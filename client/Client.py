import socket
import json
import threading
import time
from pathlib import Path

import arcade


class Client:
    def __init__(self, ip='127.0.0.1', port=5000, window=None):
        self.listener_thread = None
        self.window = window
        self.server_ip = ip
        self.server_port = port
        self.server_address = (self.server_ip, int(self.server_port))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connected = False
        self.running = False

        self.server_name = None

        self.pending_tank_updates = []
        self.tank_updates_lock = threading.Lock()

        # Heartbeat
        self.last_heartbeat_sent = 0
        self.heartbeat_interval = 3.0  # Send heartbeat every 3 seconds

        # Load settings
        project_root = Path(__file__).resolve().parent.parent
        SETTINGS_FILE = project_root / ".config" / "settings.json"
        settings = {}
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, "r") as file:
                    settings = json.load(file)
        except json.JSONDecodeError:
            print("️Nastal problém pri načítaní settings.json – používa sa prázdne nastavenie.")
            settings = {}

        self.player_name = settings.get("player_name")
        self.color_assignments = {}
        self.assigned_color = None
        self.client_id = None

    def connect(self):
        try:
            # Create a new socket for each connection
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Now send the connection message
            message = f"connection,{self.player_name}"
            self.socket.sendto(message.encode('utf-8'), self.server_address)
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
                        message_get = message.get("type")
                        # Handle command messages
                        if message_get == "command":
                            print(f"Received command: {message.get('command')}")
                            self.handle_command(message)
                        elif message_get == "heartbeat_ack":
                            # Connection is alive, nothing to do
                            continue
                        elif message_get == "name_assignment":
                            assigned_name = message.get("assigned_name")
                            if assigned_name:
                                print(f"Server assigned name: {assigned_name}")
                                self.player_name = assigned_name
                        elif message_get == "connection_accepted":
                            self.client_id = message.get("client_id")
                            self.assigned_color = message.get("assigned_color")
                            assigned_name = message.get("assigned_name")
                            if assigned_name:
                                self.player_name = assigned_name
                            print(f"Connection accepted. Name: {self.player_name}, Color: {self.assigned_color}, ID: {self.client_id}")
                        elif message_get == "server_name":
                            print(f"Received data: {message.get('server_name')}")
                            try:
                                self.server_name = message.get("server_name")
                            except Exception as e:
                                print("Error getting server name:", e)

                        elif message_get == "tank_state":
                            with self.tank_updates_lock:
                                print(f"Client -> 95: Client received tank state: {message}")
                                self.pending_tank_updates.append(message)
                            continue



                    except json.JSONDecodeError:
                        # Not JSON, treat as regular message
                        print(f"Received non-JSON message: {decoded}")
                except UnicodeDecodeError:
                    print("Received binary data")

            except socket.timeout:
                if time.time() - self.last_heartbeat_sent > self.heartbeat_interval:
                    self.send_heartbeat()
                continue
            except Exception as e:
                print(f"Listener error: {e}")
                if self.running and self.connected:
                    # Only try to recover if still running
                    print("Error in listener thread, will continue...")
                else:
                    break

        print("Listener thread exiting")

    def send_heartbeat(self):
        """Send periodic heartbeat to maintain connection"""
        current_time = time.time()
        if not self.connected or self.socket is None:
            return

        if current_time - self.last_heartbeat_sent > self.heartbeat_interval:
            try:
                heartbeat_msg = json.dumps({"type": "heartbeat", "timestamp": current_time})
                self.socket.sendto(heartbeat_msg.encode(), self.server_address)
                self.last_heartbeat_sent = current_time
            except Exception as e:
                print(f"Error sending heartbeat: {e}")

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
                    ipPort, player_name = client_str.split(",")
                    ip, port_str = ipPort.split(":")
                    client_tuples.append(((ip, int(port_str)), player_name))
                return client_tuples
            elif data["type"] == "command":
                self.handle_command(data)
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

    def handle_command(self, command_data):
        """Process json commands from the server"""
        if isinstance(command_data, dict):
            command = command_data.get("command")
            cmd_id = command_data.get("id")
            require_ack = command_data.get("require_ack", False)

            # Send acknowledgment if required
            if require_ack and cmd_id:
                ack_msg = json.dumps({"type": "ack", "id": cmd_id})
                self.socket.sendto(ack_msg.encode(), self.server_address)

            if command == "game_start":
                print("Game is starting!")
                # Store the color assignments for use in GameView
                self.color_assignments = command_data.get("color_assignments", {})
                arcade.schedule_once(lambda dt: self._start_game(), 0)

    def _start_game(self):
        """Transition to GameView (called from main thread)"""
        from client.game import GameView

        # Safely unschedule update_player_list if necessary
        try:
            if hasattr(self.window.current_view, "update_player_list"):
                arcade.unschedule(self.window.current_view.update_player_list)
        except Exception as e:
            print(f"Error unscheduling player list updates: {e}")

        # Show game view with color assignments
        self.window.show_view(GameView(
            self.window,
            self,
            True,
            self.color_assignments,
            getattr(self, 'spawn_assignments', {})
        ))

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