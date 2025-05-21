import socket
import threading
import json
import time
from pathlib import Path

import arcade


class Server:
    def __init__(self, ip='127.0.0.1', port=5000, window=None):
        self.ip = str(ip)
        self.port = int(port)
        self.window = window
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = True

        self.pending_acks = {}

        # Enable address reuse
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(f"Server socket created at {self.ip}:{self.port}")

        self.clients = []
        self.client_last_seen = {}  # Track when each client was last seen
        self.client_timeout = 15.0  # Seconds before considering a client disconnected

        self.clients_lock = threading.Lock()

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

        self.available_colors = ["blue", "red", "yellow", "green"]
        self.player_colors = {}

    def start(self):
        self.server_socket.bind((self.ip, self.port))
        print(f"Server started at {self.ip}:{self.port}")

        # Run handle_clients in a separate thread for responsiveness
        client_thread = threading.Thread(target=self.handle_clients, daemon=True)
        client_thread.start()

        # Schedule regular checks for unacknowledged commands
        check_interval = 0.5  # Check every half second
        self.check_commands_thread = threading.Thread(
            target=self.run_command_checks,
            daemon=True
        )
        self.check_commands_thread.start()

        try:
            # Keep main thread alive until shutdown
            while self.running:
                try:
                    # Wait for KeyboardInterrupt to shutdown
                    threading.Event().wait(1)
                except KeyboardInterrupt:
                    print("Server shutting down.")
                    self.shutdown()
        finally:
            self.server_socket.close()

    def assign_color_to_player(self, player_id):
        """Assign a unique color to a player"""
        if player_id in self.player_colors:
            return self.player_colors[player_id]

        if not self.available_colors:
            # If we run out of colors, reuse one (shouldn't happen with 4 player limit)
            return "blue"

        color = self.available_colors.pop(0)  # Take first available color
        self.player_colors[player_id] = color
        return color

    def release_player_color(self, player_id):
        """Return a player's color to the available pool when they disconnect"""
        if player_id in self.player_colors:
            color = self.player_colors[player_id]
            self.available_colors.append(color)
            del self.player_colors[player_id]

    def run_command_checks(self):
        """Run periodic checks for unacknowledged commands"""
        while self.running:
            self.check_unacknowledged_commands()
            time.sleep(0.5)  # Check every half second

    def get_server_ip(self):
        return self.ip, self.port

    def get_players_list(self):
        """Return a list of connected players"""
        with self.clients_lock:
            return list(self.clients)

    def handle_clients(self):
        # Set a timeout, so we can check the running flag periodically
        self.server_socket.settimeout(0.5)
        while self.running:
            try:
                try:
                    data, addr = self.server_socket.recvfrom(1024)

                    # Update last seen timestamp for this client
                    self.client_last_seen[addr] = time.time()
                except socket.timeout:
                    current_time = time.time()
                    with self.clients_lock:
                        to_remove = []
                        for client in self.clients:
                            client_addr = client[0]
                            if client_addr not in self.client_last_seen or current_time - self.client_last_seen[client_addr] > self.client_timeout:
                                to_remove.append(client)

                        # Only remove truly timed-out clients
                        for client in to_remove:
                            self.clients.remove(client)
                            print(f"Client {client[0]} timed out after {self.client_timeout} seconds")

                    continue
                except OSError as e:
                    if not self.running:
                        print("Socket closed during shutdown")
                        break
                    else:
                        print(f"Socket error: {e}")
                        continue

                # Check if this is a new client
                with self.clients_lock:
                    client_found = False
                    for client in self.clients:
                        if client[0] == addr:
                            client_found = True
                            break
                    if not client_found:
                        print(f"New connection from {addr}")


                # Process the received data
                try:
                    decoded = data.decode()
                    print(f"Received from {addr}: {decoded}")
                except UnicodeDecodeError:
                    print(f"Received non-text data from {addr}")
                    continue

                try:
                    data_dict = json.loads(decoded)
                    if data_dict.get("type") == "ack" and data_dict.get("id"):
                        # Remove from pending acknowledgments
                        cmd_id = data_dict.get("id")
                        if cmd_id in self.pending_acks:
                            self.pending_acks.pop(cmd_id)
                            print(f"Received ACK for command {cmd_id}")
                        continue

                    if data_dict.get("type") == "tank_state":
                        # Broadcast this tank state to all other clients
                        self.game_broadcast_data(data_dict, except_ip=addr)

                        if hasattr(self, 'window') and self.window:
                            view = self.window.current_view
                            if hasattr(view, 'process_tank_update'):
                                arcade.schedule_once(lambda dt, data=data_dict: view.process_tank_update(data), 0)
                        continue
                except json.JSONDecodeError:
                    # Not JSON, handle as before
                    pass

                if decoded.startswith("connection,"):
                    parts = decoded.split(",", 1)  # Split only at first comma
                    if len(parts) == 2:
                        base_name = parts[1]
                        # Check if name exists and generate a unique name
                        unique_name = self.get_unique_player_name(base_name)
                        print(f"New connection: {base_name} (assigned: {unique_name}) from {addr}")

                        with self.clients_lock:
                            # Store address and name together as a tuple
                            self.clients.append((addr, unique_name))

                        print(f"Clients: {self.clients}")

                        # Notify client of their assigned name if it was changed
                        if base_name != unique_name:
                            name_assignment = json.dumps({
                                "type": "name_assignment",
                                "assigned_name": unique_name
                            })
                            self.server_socket.sendto(name_assignment.encode(), addr)

                # Handle get_players command
                if decoded == "get_players":
                    print(f"Sending player list to {addr}")
                    with self.clients_lock:
                        # Use each client's own name instead of server's name
                        client_addresses = [f"{client[0][0]}:{client[0][1]},{client[1]}" for client in self.clients]
                        print(f"Server>120: {client_addresses}")
                        response = json.dumps({"type": "clients", "clients": client_addresses})
                        self.server_socket.sendto(response.encode(), addr)


                elif decoded == "get_server_name":
                    print(f"Sending server name to {addr}")
                    response = json.dumps({"type": "server_name", "server_name": self.player_name})
                    print(f"Server -> 142: get_server_name: {response}")
                    self.server_socket.sendto(response.encode(), addr)


                # Handle disconnect message
                if decoded == "disconnect":
                    print(f"{addr} is disconnecting")
                    with self.clients_lock:
                        # Find the client by address
                        for client in self.clients:
                            if client[0] == addr:
                                self.clients.remove(client)
                                # Also remove from last_seen
                                if addr in self.client_last_seen:
                                    del self.client_last_seen[addr]
                                print(f"Client {addr} disconnected")
                                break
                    continue

            except Exception as e:
                print(f"Error: {e}")
                if not self.running:
                    break

        print("Client handler loop exited")

    def get_unique_player_name(self, base_name):
        """Generate a unique player name by appending numbers if necessary"""
        # Check if the name is already in use
        with self.clients_lock:
            existing_names = [client[1] for client in self.clients]

        # If the base name is not in use, we can use it
        if base_name not in existing_names:
            return base_name

        # If the name is in use, try appending numbers
        counter = 1
        while True:
            new_name = f"{base_name}{counter}"
            if new_name not in existing_names:
                return new_name
            counter += 1

    def send_command(self, command, client_addr=None, require_ack=False, max_retries=10, retry_interval=1.0):
        command_id = str(time.time())  # Use timestamp as unique ID

        # Convert string commands to JSON format
        if command == "game_start":
            # Create a color assignment for all connected players
            color_assignments = {}
            with self.clients_lock:
                for client in self.clients:
                    client_id = client[1]  # The player name/ID
                    color = self.assign_color_to_player(client_id)
                    color_assignments[client_id] = color

            command_data = {
                "type": "command",
                "command": "game_start",
                "color_assignments": color_assignments,
                "id": command_id,
                "require_ack": require_ack
            }
            command_msg = json.dumps(command_data)
        else:
            command_msg = json.dumps({
                "type": "command",
                "command": command,
                "id": command_id,
                "require_ack": require_ack
            })

        if require_ack:
            self.pending_acks[command_id] = {
                "time_sent": time.time(),
                "retries": 0,
                "command": command_msg,
                "addr": client_addr,
                "max_retries": max_retries if command != "game_start" else 20,  # More retries for game_start
                "retry_interval": retry_interval if command != "game_start" else 0.5  # Faster retries for game_start
            }

        if client_addr:
            try:
                # Extract the actual socket address (the first element of the tuple)
                actual_addr = client_addr[0] if isinstance(client_addr, tuple) and isinstance(client_addr[0],
                                                                                              tuple) else client_addr
                self.server_socket.sendto(command_msg.encode(), actual_addr)
                print(f"Command '{command}' -> {client_addr}")
            except Exception as e:
                print(f"Error sending command to {client_addr}: {e}")
        else:
            with self.clients_lock:
                for addr in self.clients:
                    try:
                        # Extract the socket address from the client tuple
                        actual_addr = addr[0]  # This should be the (ip, port) tuple
                        self.server_socket.sendto(command_msg.encode(), actual_addr)
                    except Exception as e:
                        print(f"Error sending command to {addr}: {e}")
            print(f"Command '{command}' broadcast to all clients")

    def shutdown(self):
        print("Shutting down server...")
        self.running = False
        # Unblock the recvfrom call with a quick message to self
        try:
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.sendto(b"", (self.ip, self.port))
            temp_socket.close()
        except Exception:
            pass
        if self.server_socket:
            self.server_socket.close()
        print("Server shutdown complete")

    def check_unacknowledged_commands(self):
        """Run periodic checks for unacknowledged commands with improved reliability"""
        current_time = time.time()
        to_remove = []

        for cmd_id, data in self.pending_acks.items():
            retry_interval = data.get("retry_interval", 1.0)
            max_retries = data.get("max_retries", 5)

            # For game_start commands, use more aggressive retries and longer timeout
            if "game_start" in data.get("command", ""):
                max_retries = 30  # Much more retries for game_start
                retry_interval = 0.3  # Quicker retries for critical commands

            # If command was sent more than retry_interval seconds ago
            if current_time - data["time_sent"] > retry_interval:
                # Check against max_retries
                if data["retries"] < max_retries:
                    # For targeted commands, send only to the target
                    if data["addr"]:
                        self.server_socket.sendto(data["command"].encode(), data["addr"])
                    # For broadcast commands like game_start, send to all clients
                    else:
                        with self.clients_lock:
                            for client in self.clients:
                                self.server_socket.sendto(data["command"].encode(), client[0])

                    # Update retries and time sent
                    data["retries"] += 1
                    data["time_sent"] = current_time
                    print(f"Resending command {cmd_id}, retry #{data['retries']}")
                else:
                    # Max retries reached
                    print(f"Max retries reached for command {cmd_id}")
                    to_remove.append(cmd_id)

        # Remove expired entries
        for cmd_id in to_remove:
            self.pending_acks.pop(cmd_id)

    def game_broadcast_data(self, game_data, except_ip=None):
        """Broadcast game data to all clients except the one specified"""
        if not self.running:
            return

        # Convert to string if it's a dict or list
        if isinstance(game_data, (dict, list)):
            data_json = json.dumps(game_data)
        else:
            data_json = game_data

        print(f"Broadcasting game data: {data_json} (except: {except_ip})")

        with self.clients_lock:
            for client in self.clients:
                try:
                    client_addr = client[0]  # The first element is the address tuple
                    # Skip the client that sent this data if specified
                    if except_ip and client_addr == except_ip:
                        continue

                    self.server_socket.sendto(data_json.encode(), client_addr)
                    print(f"Sent game data to {client[1]} at {client_addr}")
                except Exception as e:
                    print(f"Error broadcasting game data to {client}: {e}")