import socket
import json

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
            # Create a new socket for each connection
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Set socket option to reuse address
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Now send the connection message
            self.socket.sendto(b"connection", self.server_address)
            print(f"Trying connection -> {self.server_ip}:{self.server_port}")
        except Exception as e:
            print(e)
        else:
            self.connected = True
            print(f"Connected -> {self.server_ip}:{self.server_port}")

    def get_server_ip(self):
        return str(self.server_ip + ":" + str(self.server_port))

    def check_socket_connection(self):
        if not self.connected or self.socket is None:
            return False
        try:
            # Try a non-destructive operation on the socket
            self.socket.getsockname()

            # Optional: Test if we can send data
            try:
                # Send a harmless zero-byte packet
                self.socket.sendto(b"", self.server_address)
            except OSError:
                self.connected = False
                return False

            return True
        except OSError:
            self.connected = False
            return False

    def get_players(self):
        try:
            # Check if socket is valid
            if not self.check_socket_connection():
                print("Socket is invalid or closed, reconnecting...")
                # Create a new socket
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.connect()

            # Send request to the server
            self.socket.sendto(b"get_players", self.server_address)

            # Set a timeout to avoid hanging indefinitely
            self.socket.settimeout(1.0)

            # Get response
            data = self.receive_data()
            print(f"Received data: {data}")

            # Only reset timeout if socket is still valid
            if self.connected:
                self.socket.settimeout(None)

            if data is None:
                return []

            data = json.loads(data)
            if data["type"] == "clients":
                # Convert strings like "127.0.0.1:5000" back to tuples
                client_tuples = []
                for client_str in data["clients"]:
                    ip, port_str = client_str.split(":")
                    client_tuples.append((ip, int(port_str)))
                return client_tuples

            else:
                print(f"Unexpected response type: {data.get('type', 'unknown')}")
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
        except socket.timeout:
            # For timeouts, just return None without disconnecting
            print("Socket timed out waiting for data")
            return None
        except Exception as e:
            print(f"Error receiving data: {e}")
            self.disconnect()
            return None

    def disconnect(self):
        try:
            if self.connected:
                self.socket.sendto(b"disconnect", self.server_address)
                self.socket.close()
                self.socket = None  # Set to None after closing
                self.connected = False
                print("Disconnected from server")
        except Exception as e:
            print(f"Error disconnecting: {e}")
