import socket
import json


class Client:
    def __init__(self, ip='127.0.0.1', port=5000):
        self.server_ip = ip
        self.server_port = port
        self.server_address = (self.server_ip, self.server_port)
        self.client_id = 0
        # Change to SOCK_DGRAM for UDP
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connected = False

    def connect(self):
        try:
            # No actual connection in UDP, just set flag and send initial message
            self.connected = True
            print(f"Ready to communicate with server at {self.server_ip}:{self.server_port}")
            self.socket.sendto(b"Connected", self.server_address)
        except Exception as e:
            print(f"Error: {e}")
            self.disconnect()

    def send_data(self, data):
        try:
            if isinstance(data, (dict, list)):
                data = json.dumps(data)
            # Use sendto instead of sendall
            self.socket.sendto(data.encode(), self.server_address)
            print(f"Sent: {data}")
        except Exception as e:
            print(f"Error sending data: {e}")
            self.disconnect()

    def receive_data(self):
        try:
            # Use recvfrom instead of recv
            data, addr = self.socket.recvfrom(1024)
            if not data:
                print("Server closed the connection")
                self.disconnect()
                return None
            return data.decode()
        except Exception as e:
            print(f"Error receiving data: {e}")
            self.disconnect()
            return None

    def disconnect(self):
        try:
            # Send disconnect message to server
            if self.connected:
                self.socket.sendto(b"disconnect", self.server_address)
            self.socket.close()
            self.connected = False
            print("Disconnected from server")
        except Exception as e:
            print(f"Error disconnecting: {e}")

    def run(self):
        self.connect()
        while self.connected:
            data = self.receive_data()
            if data is None:
                break
            print(data)


if __name__ == "__main__":
    client = Client(ip="127.0.0.1", port=5000)
    client.run()
