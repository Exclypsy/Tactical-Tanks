import socket
import json
import time

class Client:
    def __init__(self, ip='127.0.0.1', port=5000):
        self.server_ip = ip
        self.server_port = port
        self.server_address = (self.server_ip, int(self.server_port))
        self.client_id = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connected = False

    def connect(self):
        try:
            self.socket.sendto(b"connection", self.server_address)
            print(f"{time.time()} Tarying connection -> {self.server_ip}:{self.server_port}")
        except Exception as e:
            print(e)
        else:
            self.connected = True
            print(f"Connected -> {self.server_ip}:{self.server_port}")

    def get_server_ip(self):
        return self.server_ip + ":" + str(self.server_port)

    def get_players(self):
        try:
            # Send request to the server
            self.socket.sendto(b"get_players", self.server_address)

            # Set a timeout to avoid hanging indefinitely
            self.socket.settimeout(1.0)

            # Get response
            data = self.receive_data()
            print(f"Received data: {data}")
            # Reset timeout to blocking mode
            self.socket.settimeout(None)

            if data is None:
                return []

            data = json.loads(data)
            if data["type"] == "clients":
                return data["clients"]
            else:
                print(f"Unexpected response type: {data.get('type', 'unknown')}")
                return []
        except json.JSONDecodeError:
            print("Error decoding JSON response")
            return []
        except KeyError as e:
            print(f"Missing expected key in response: {e}")
            return []
        except Exception as e:
            print(f"Error getting player list: {e}")
            return []
    def send_data(self, data):
        try:
            if isinstance(data, (dict, list)):
                data = json.dumps(data)
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
