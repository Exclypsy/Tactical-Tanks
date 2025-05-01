import socket
import json
import threading
import arcade


class Client:
    def __init__(self, ip='127.0.0.1', port=5000, window=None):
        self.listener_thread = None
        self.window = window
        self.server_ip = ip
        self.server_port = port
        self.server_address = (self.server_ip, int(self.server_port))
        self.client_id = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connected = False

    def connect(self):
        # ... existing connection code ...
        self.connected = True
        # Start a background thread to listen for server messages
        self.listener_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
        self.listener_thread.start()

    def listen_for_commands(self):
        while self.connected:
            try:
                data = self.receive_data()
                # receive_data already processes commands, so nothing else needed here
            except Exception as e:
                print(f"Listener error: {e}")
                break

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
    def command_send_receive(self,command):
        """ Sends a command to the server
            Returns server response: String format
        """
        self.socket.sendto(command, self.server_address)

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

        return data

    def get_players_list(self):
        try:
            # Check if socket is valid
            if not self.check_socket_connection():
                print("Socket is invalid or closed, reconnecting...")
                # Create a new socket
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.connect()

            data = self.command_send_receive(b"get_players")

            # Check if data is already a list (when return was empty)
            if isinstance(data, list):
                return data

            # Try to parse JSON data
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
            data, addr = self.socket.recvfrom(1024)

            if not data:
                print("Server closed the connection")
                self.disconnect()
                return None

            decoded = data.decode()

            # Process JSON messages
            try:
                message = json.loads(decoded)

                # Handle command messages
                if message.get("type") == "command":
                    self.handle_command(message.get("command"))
                    return None  # Commands are handled internally
            except json.JSONDecodeError:
                # Not JSON, treat as regular message
                pass

            return decoded
        except socket.timeout:
            print("Socket timed out waiting for data")
            return None
        except Exception as e:
            print(f"Error receiving data: {e}")
            self.disconnect()
            return None

    def handle_command(self, command):
        """Process commands from the server"""
        print(f"Received command: {command}")

        # Implement command handlers here
        if command == "game_start":
            print("Game is starting!")
            from Lobby import LobbyView
            arcade.unschedule(LobbyView.update_player_list(self,None))
            # change to GameView
            from client.game import GameView
            self.window.show_view(GameView(self.window, self, True))

        elif command == "player_update":
            # Handle player update
            pass
        # Add more command handlers as needed

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
