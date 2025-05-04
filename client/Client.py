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
        self.running = False

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
            return False
        else:
            self.connected = True
            self.running = True
            print(f"Connected -> {self.server_ip}:{self.server_port}")

            # Start a background thread to listen for server messages
            self.listener_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
            self.listener_thread.start()
            return True

    def listen_for_commands(self):
        """Continuously listen for server commands in the background"""
        print("Starting listener thread")
        self.socket.settimeout(0.5)  # Short timeout to check running flag

        while self.running and self.connected:
            try:
                data, addr = self.socket.recvfrom(1024)

                if not data:
                    print("Server closed the connection")
                    self.disconnect()
                    break

                # Process the data
                try:
                    decoded = data.decode()
                    # Process JSON messages
                    try:
                        message = json.loads(decoded)
                        # Handle command messages
                        if message.get("type") == "command":
                            print(f"Received command: {message.get('command')}")
                            self.handle_command(message.get("command"))
                    except json.JSONDecodeError:
                        # Not JSON, treat as regular message
                        print(f"Received non-JSON message: {decoded}")
                except UnicodeDecodeError:
                    print("Received binary data")

            except socket.timeout:
                # Just loop and check running flag
                continue
            except Exception as e:
                print(f"Listener error: {e}")
                if self.running and self.connected:
                    # Only try to recover if still running
                    print("Error in listener thread, will continue...")
                else:
                    break

        print("Listener thread exiting")

    def get_server_ip(self):
        """Return server IP address as Tuple"""
        return self.server_ip, self.server_port

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

    def command_send_receive(self, command):
        """ Sends a command to the server
            Returns server response: String format
        """
        if not self.connected:
            print("Not connected")
            return None

        try:
            # Save current timeout
            current_timeout = self.socket.gettimeout()

            self.socket.sendto(command, self.server_address)

            # Set a timeout to avoid hanging indefinitely
            self.socket.settimeout(1.0)

            # Get response directly (don't use receive_data which is now used by listener)
            try:
                data, addr = self.socket.recvfrom(1024)
                decoded = data.decode()
                print(f"Received data: {decoded}")
            except socket.timeout:
                print("Response timeout")
                decoded = None

            # Restore original timeout
            if self.connected:
                self.socket.settimeout(current_timeout)

            return decoded
        except Exception as e:
            print(f"Error in command_send_receive: {e}")
            return None

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

            # Handle no data case
            if not data:
                return []

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
            if not self.connected:
                print("Not connected, can't send data")
                return

            if isinstance(data, (dict, list)):
                data = json.dumps(data)
            self.socket.sendto(data.encode(), self.server_address)
            print(f"Sent: {data}")
        except Exception as e:
            print(f"Error sending data: {e}")
            self.disconnect()

    def handle_command(self, command):
        """Process commands from the server"""
        print(f"Processing command: {command}")

        # Implement command handlers here
        if command == "game_start":
            print("Game is starting!")
            # Use arcade.schedule_once to safely transition to GameView from the main thread
            arcade.schedule_once(lambda dt: self._start_game(), 0)

        elif command == "player_update":
            # Handle player update
            pass
        # Add more command handlers as needed

    def _start_game(self):
        """Transition to GameView (called from main thread)"""
        from client.game import GameView
        # Safely unschedule update_player_list if necessary
        try:
            if hasattr(self.window.current_view, "update_player_list"):
                arcade.unschedule(self.window.current_view.update_player_list)
        except Exception as e:
            print(f"Error unscheduling player list updates: {e}")
        # Show game view
        self.window.show_view(GameView(self.window, self, True))

    def disconnect(self):
        try:
            self.running = False  # Signal listener thread to stop

            if self.connected:
                try:
                    self.socket.sendto(b"disconnect", self.server_address)
                except Exception:
                    pass  # Ignore errors when trying to send disconnect

                self.socket.close()
                self.socket = None  # Set to None after closing
                self.connected = False
                print("Disconnected from server")

            # Wait for listener thread to exit (with timeout)
            if self.listener_thread and self.listener_thread.is_alive():
                self.listener_thread.join(timeout=2.0)

        except Exception as e:
            print(f"Error disconnecting: {e}")

    def game_send_my_state(self, data):
        """Send the player's state to the server"""
        if not self.connected:
            print("Not connected, can't send game state")
            return

        print(f"Sending player state: {data}")

        # Send the player state to the server
        self.send_data(data)