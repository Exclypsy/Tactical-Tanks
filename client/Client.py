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

        self.server_name = None
        self.server_color = "blue"  # Default server color
        self.assigned_color = None
        self.client_id = None

        self.current_map = None

        self.latest_player_list = []

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
        self.socket.settimeout(0.5)

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

                    # Handle the "players:" fallback response HERE instead of in get_players_list
                    if decoded.startswith("players:"):
                        try:
                            players_data = decoded[8:]  # Remove "players:" prefix
                            if players_data:
                                player_list = json.loads(players_data)
                                print(f"Fallback player list received in listener: {[p[1] for p in player_list]}")
                                # Cache it immediately
                                self.latest_player_list = player_list
                                # Notify lobby immediately
                                current_view = self.window.current_view
                                if hasattr(current_view, 'on_instant_player_update'):
                                    arcade.schedule_once(lambda dt: current_view.on_instant_player_update(), 0)
                            continue
                        except json.JSONDecodeError as e:
                            print(f"Error parsing fallback player list: {e}")
                            continue

                    # Process JSON messages
                    try:
                        message = json.loads(decoded)
                        message_get = message.get("type")

                        # Handle command messages
                        if message_get == "command":
                            print(f"Received command: {message.get('command')}")
                            self.handle_command(message)

                        elif message_get == "heartbeat_ack":
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
                            print(
                                f"Connection accepted. Name: {self.player_name}, Color: {self.assigned_color}, ID: {self.client_id}")

                        elif message_get == "server_name":
                            print(f"Received server data: {message}")
                            try:
                                self.server_name = message.get("server_name")
                                self.server_color = message.get("server_color", "blue")
                                print(f"Server name: {self.server_name}, Server color: {self.server_color}")
                            except Exception as e:
                                print("Error getting server name:", e)

                        elif message_get == "tank_state":
                            with self.tank_updates_lock:
                                print(f"Client received tank state: {message}")
                                self.pending_tank_updates.append(message)

                        # Handle real-time player list updates
                        elif message_get == "player_list_update":
                            print("Received instant player list update")
                            self.latest_player_list = message.get("players", [])
                            print(f"Client cached player list: {[p[1] for p in self.latest_player_list]}")

                            # Notify current view immediately if it's a lobby
                            current_view = self.window.current_view
                            if hasattr(current_view, 'on_instant_player_update'):
                                arcade.schedule_once(lambda dt: current_view.on_instant_player_update(), 0)

                        continue

                    except json.JSONDecodeError:
                        # Not JSON and not players: format, treat as regular message
                        print(f"Received unknown message: {decoded}")

                except UnicodeDecodeError:
                    print("Received binary data")

            except socket.timeout:
                if time.time() - self.last_heartbeat_sent > self.heartbeat_interval:
                    self.send_heartbeat()
                continue

            except Exception as e:
                print(f"Listener error: {e}")
                if self.running and self.connected:
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
            self.socket.settimeout(2.0)  # Increased timeout

            # Get response directly
            try:
                data, addr = self.socket.recvfrom(1024)
                decoded = data.decode()
                print(f"Received response for command: {decoded}")
                return decoded
            except socket.timeout:
                print("Response timeout for command")
                return None
            except Exception as recv_error:
                print(f"Error receiving response: {recv_error}")
                return None
            finally:
                # Restore original timeout
                if self.connected:
                    self.socket.settimeout(current_timeout)

        except Exception as e:
            print(f"Error in command_send_receive: {e}")
            return None

    def get_players_list(self):
        """Simplified fallback method - just send request, response handled in listener"""
        try:
            print("Requesting fallback player list...")
            self.socket.sendto(b"get_players", self.server_address)

            # Wait a short time for the response to be processed by the listener
            import time
            time.sleep(0.2)

            # Return cached data if available
            cached_list = self.get_latest_player_list()
            if cached_list:
                print(f"Using cached data from fallback: {[p[1] for p in cached_list]}")
                return cached_list

            print("No fallback response received")
            return []

        except Exception as e:
            print(f"Error requesting fallback player list: {e}")
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
                print(f"Sent ACK for command: {command}")

            if command == "map_selected":
                map_name = command_data.get("map_name")
                if map_name:
                    self.current_map = map_name
                    print(f"Received selected map: {self.current_map}")
                else:
                    print("ERROR: Received map_selected command without map_name")

            elif command == "server_disconnect":
                print("Server is disconnecting, returning to main menu...")
                arcade.schedule_once(lambda dt: self._return_to_main_menu(), 0)

            elif command == "game_start":
                print("Game is starting!")
                self.color_assignments = command_data.get("color_assignments", {})
                self.spawn_assignments = command_data.get("spawn_assignments", {})
                arcade.schedule_once(lambda dt: self._start_game(), 0)

    def _return_to_main_menu(self):
        """Return to main menu (called from main thread)"""
        try:
            print("Returning to main menu due to server disconnect")

            # Clean up current view if needed
            current_view = self.window.current_view

            # Unschedule specific functions instead of unschedule_all
            functions_to_unschedule = []

            if hasattr(current_view, 'update_player_list'):
                functions_to_unschedule.append(current_view.update_player_list)

            if hasattr(current_view, 'check_game_start'):
                functions_to_unschedule.append(current_view.check_game_start)

            if hasattr(current_view, 'send_tank_update'):
                functions_to_unschedule.append(current_view.send_tank_update)

            if hasattr(current_view, 'process_queued_tank_updates'):
                functions_to_unschedule.append(current_view.process_queued_tank_updates)

            if hasattr(current_view, '_delayed_camera_setup'):
                functions_to_unschedule.append(current_view._delayed_camera_setup)

            # Unschedule each function individually
            for func in functions_to_unschedule:
                try:
                    arcade.unschedule(func)
                    print(f"Unscheduled {func.__name__}")
                except:
                    pass  # Function might not be scheduled

            # Disable UI manager if present
            if hasattr(current_view, 'manager'):
                try:
                    current_view.manager.disable()
                    current_view.manager.clear()
                    print("Disabled and cleared UI manager")
                except:
                    pass

            # Disconnect from server
            self.disconnect()

            # Return to main menu
            from MainMenu import Mainview
            from SettingsWindow import toggle_fullscreen, settings

            if settings.get("fullscreen", True):
                toggle_fullscreen(self.window)

            self.window.show_view(Mainview(self.window))
            print("Successfully returned to main menu")

        except Exception as e:
            print(f"Error returning to main menu: {e}")
            import traceback
            traceback.print_exc()

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

    def get_latest_player_list(self):
        """Get the most recent player list from real-time updates"""
        return getattr(self, 'latest_player_list', [])
