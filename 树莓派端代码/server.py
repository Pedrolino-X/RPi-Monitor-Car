
import socket
import threading
import time
import os
import RPi.GPIO as GPIO
import cv2
import struct
import random
from gyro import get_gyro_data

# --- Motor Control ---
STBY = 27
PWMA = 13
AIN1 = 19
AIN2 = 26
PWMB = 16
BIN1 = 20
BIN2 = 21
hz = 500
speed = 0

def setup_motors():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PWMA, GPIO.OUT)
    GPIO.setup(AIN1, GPIO.OUT)
    GPIO.setup(AIN2, GPIO.OUT)
    GPIO.setup(PWMB, GPIO.OUT)
    GPIO.setup(BIN1, GPIO.OUT)
    GPIO.setup(BIN2, GPIO.OUT)
    GPIO.setup(STBY, GPIO.OUT)
    global pwma, pwmb
    pwma = GPIO.PWM(PWMA, hz)
    pwmb = GPIO.PWM(PWMB, hz)
    pwma.start(speed)
    pwmb.start(speed)
    GPIO.output(STBY, True)

def move_forward():
    GPIO.output(AIN1, False)
    GPIO.output(AIN2, True)
    pwma.ChangeDutyCycle(85)
    GPIO.output(BIN1, False)
    GPIO.output(BIN2, True)
    pwmb.ChangeDutyCycle(80)

def move_backward():
    GPIO.output(AIN1, True)
    GPIO.output(AIN2, False)
    pwma.ChangeDutyCycle(85)
    GPIO.output(BIN1, True)
    GPIO.output(BIN2, False)
    pwmb.ChangeDutyCycle(80)

def turn_left():
    GPIO.output(AIN1, False)
    GPIO.output(AIN2, True)
    pwma.ChangeDutyCycle(85)
    GPIO.output(BIN1, True)
    GPIO.output(BIN2, False)
    pwmb.ChangeDutyCycle(80)

def turn_right():
    GPIO.output(AIN1, True)
    GPIO.output(AIN2, False)
    pwma.ChangeDutyCycle(85)
    GPIO.output(BIN1, False)
    GPIO.output(BIN2, True)
    pwmb.ChangeDutyCycle(80)

def stop_movement():
    pwma.ChangeDutyCycle(0)
    pwmb.ChangeDutyCycle(0)

# --- Servo Control ---
servoA_pin = 17
servoB_pin = 22

def setup_servos():
    GPIO.setup(servoA_pin, GPIO.OUT, initial=False)
    GPIO.setup(servoB_pin, GPIO.OUT, initial=False)
    global sA, sB
    sA = GPIO.PWM(servoA_pin, 50)
    sB = GPIO.PWM(servoB_pin, 50)
    sA.start(0)
    sB.start(0)

def set_servo_angle(servo, angle):
    duty_cycle = 2.5 + angle / 180.0 * 10
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.1)
    servo.ChangeDutyCycle(0)



# --- Camera ---
class VideoStreamer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.lock = threading.Lock()
        self.camera = cv2.VideoCapture(0)

    def start(self):
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Video streamer listening on {self.host}:{self.port}")
        accept_thread = threading.Thread(target=self.accept_clients)
        accept_thread.daemon = True
        accept_thread.start()

    def accept_clients(self):
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"Video client connected from {address}")
            with self.lock:
                self.clients.append(client_socket)
            stream_thread = threading.Thread(target=self.stream_video, args=(client_socket,))
            stream_thread.daemon = True
            stream_thread.start()

    def stream_video(self, client_socket):
        try:
            while True:
                ret, frame = self.camera.read()
                if not ret:
                    break
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                _, encoded_frame = cv2.imencode('.jpg', frame)
                frame_data = encoded_frame.tobytes()
                frame_size = struct.pack("!L", len(frame_data))
                client_socket.sendall(frame_size + frame_data)
                time.sleep(0.03) # Limit frame rate
        except (BrokenPipeError, ConnectionResetError):
            print("Video client disconnected.")
        finally:
            with self.lock:
                self.clients.remove(client_socket)
            client_socket.close()

    def capture_photo(self, path):
        ret, frame = self.camera.read()
        if ret:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            cv2.imwrite(path, frame)
            print(f"Photo saved to {path}")

# --- Main Server ---
class CommandServer:
    def __init__(self, host, port, video_streamer):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.lock = threading.Lock()
        self.video_streamer = video_streamer
        self.photo_dir = os.path.expanduser("~/Desktop/Camera_Photos")
        if not os.path.exists(self.photo_dir):
            os.makedirs(self.photo_dir)

    def handle_client(self, client_socket, address):
        print(f"Command client connected from {address}")
        with self.lock:
            self.clients.append(client_socket)

        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                print(f"Received command from {address}: {data}")
                self.process_command(data)
        except ConnectionResetError:
            print(f"Command client from {address} reset.")
        finally:
            with self.lock:
                self.clients.remove(client_socket)
            client_socket.close()
            print(f"Command client from {address} closed.")

    def process_command(self, command):
        if command == 'w':
            move_forward()
        elif command == 's':
            move_backward()
        elif command == 'a':
            turn_left()
        elif command == 'd':
            turn_right()
        elif command in ('wc', 'sc', 'ac', 'dc', 'stop'):
            stop_movement()
        elif command == 'p':
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            photo_path = os.path.join(self.photo_dir, f"capture_{timestamp}.jpg")
            self.video_streamer.capture_photo(photo_path)
        elif command.startswith("IP:"):
            print(f"Client IP info: {command}")
        elif command.startswith("servoA:"):
            try:
                parts = command.split(',')
                angleA_str = parts[0].split(':')[1]
                angleB_str = parts[1].split(':')[1]
                angleA = int(angleA_str)
                angleB = int(angleB_str)
                print(f"Setting servoA to {angleA}, servoB to {angleB}")
                set_servo_angle(sA, angleA)
                set_servo_angle(sB, angleB)
            except (IndexError, ValueError) as e:
                print(f"Invalid servo command format. Error: {e}")

    def broadcast_gyro_data(self):
        while True:
            if self.clients:
                data_str = get_gyro_data()
                with self.lock:
                    for client in self.clients:
                        try:
                            client.sendall(data_str.encode('utf-8'))
                        except:
                            pass
            time.sleep(0.4)

    def start(self):
        setup_motors()
        setup_servos()
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Command server listening on {self.host}:{self.port}")

        gyro_thread = threading.Thread(target=self.broadcast_gyro_data)
        gyro_thread.daemon = True
        gyro_thread.start()

        while True:
            client_socket, address = self.server_socket.accept()
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket, address))
            client_handler.daemon = True
            client_handler.start()

if __name__ == "__main__":
    def cleanup():
        print("\nCleaning up and shutting down...")
        stop_movement()
        if 'video_streamer' in locals() and video_streamer.server_socket:
            video_streamer.server_socket.close()
        if 'command_server' in locals() and command_server.server_socket:
            command_server.server_socket.close()
        if 'video_streamer' in locals() and video_streamer.camera:
            video_streamer.camera.release()
        GPIO.cleanup()
        print("Cleanup complete. Exiting.")

    try:
        video_streamer = VideoStreamer('0.0.0.0', 8081)
        video_streamer.start()

        command_server = CommandServer('0.0.0.0', 8082, video_streamer)
        command_server.start()

    except KeyboardInterrupt:
        pass
    finally:
        cleanup()