import socket
import cv2
import numpy as np

class NetworkCamera:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.ip, self.port))

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def is_connected(self):
        return self.sock is not None

    def get_frame(self):
        frame_size_data = self.sock.recv(4)
        if not frame_size_data:
            return None
        frame_size = int.from_bytes(frame_size_data, 'big')

        frame_data = b''
        while len(frame_data) < frame_size:
            packet = self.sock.recv(frame_size - len(frame_data))
            if not packet:
                return None
            frame_data += packet

        frame = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        return frame

#
# import cv2
#
#
# class NetworkCamera:
#     def __init__(self, url):
#         self.url = url
#         self.cap = None
#
#     def connect(self):
#         self.cap = cv2.VideoCapture(self.url)
#         if not self.cap.isOpened():
#             print("Failed to connect to network camera")
#             self.cap = None
#
#     def disconnect(self):
#         if self.cap:
#             self.cap.release()
#             self.cap = None
#
#     def is_connected(self):
#         return self.cap is not None and self.cap.isOpened()
#
#     def get_frame(self):
#         if self.is_connected():
#             ret, frame = self.cap.read()
#             if ret:
#                 return frame
#         return None
