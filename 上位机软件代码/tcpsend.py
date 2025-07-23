import socket


class TCPClient:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.client_socket = None

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.ip, self.port))
            # self.send_ip_address()
            print(f"Connected to {self.ip}:{self.port}")  # 调试信息
        except Exception as e:
            print(f"Error connecting to {self.ip}:{self.port} - {e}")  # 调试信息

    def send_ip_address(self):
        local_ip = socket.gethostbyname(socket.gethostname())
        message = f"IP:{local_ip},PORT:{self.client_socket.getsockname()[1]}"
        print(message)
        self.send_message(message)

    def is_connected(self):
        return self.client_socket is not None

    def send_message(self, message):
        try:
            print(f"Sending message: {message}")  # 调试信息
            self.client_socket.sendall(message.encode('utf-8'))
            print("Message sent, waiting for response...")  # 调试信息
            # response = self.client_socket.recv(1024).decode('utf-8')
            # print(f"Received response: {'response'}")  # 调试信息
            return 'response'
        except Exception as e:
            print(f"Error sending message: {e}")  # 调试信息
            raise e

    def receive_data(self):
        data = self.client_socket.recv(1024).decode('utf-8')
        return data

    def close(self):
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            print("Connection closed")  # 调试信息
