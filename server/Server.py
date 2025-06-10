import socket
import threading
import json
import time
import random
from pathlib import Path


import arcade

import traceback


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


        path = project_root / ".config" / "maps"
        arcade.resources.add_resource_handle("maps", str(path.resolve()))

        self.all_maps = []
        for map_file in path.glob("*.json"):
            if map_file.is_file():
                self.all_maps.append(map_file.stem)




        self.available_colors = ["blue", "red", "yellow", "green"]
        self.player_colors = {}
        self.clients_lock = threading.Lock()
        self.color_assignment_lock = threading.Lock()
        self.next_client_id = 0
        self.available_client_ids = set()  # Track available IDs for reuse
        self.max_client_ids = 4  # Maximum number of spawn positions

        self.server_color = None

        self.picked_map = None

    def start(self):
        if not self.server_color:
            self.server_color = self.assign_server_color()
            print(f"Server assigned itself color: {self.server_color}")

        self.server_socket.bind((self.ip, self.port))
        print(f"Server started at {self.ip}:{self.port}")

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

    def assign_server_color(self):
        """Assign a random color to the server itself - called only once"""
        with self.color_assignment_lock:
            print(f"Available colors before server assignment: {self.available_colors}")
            if not self.available_colors:
                print("ERROR: No colors available for server!")
                return "blue"  # Emergency fallback

            # Server picks a random color
            server_color = random.choice(self.available_colors)
            self.available_colors.remove(server_color)
            print(f"Server took color {server_color}, remaining: {self.available_colors}")

            # Store server's color with consistent key
            server_name = getattr(self, 'player_name', 'host')
            self.player_colors[server_name] = server_color

            return server_color

    def assign_color_to_player(self, player_id):
        """Assign a random unique color to a client player - thread safe"""
        with self.color_assignment_lock:
            # Check if player already has a color
            if player_id in self.player_colors:
                return self.player_colors[player_id]

            print(f"Available colors for client {player_id}: {self.available_colors}")

            # Ensure server color is not available for clients
            server_name = getattr(self, 'player_name', 'host')
            if self.server_color and self.server_color in self.available_colors:
                print(f"WARNING: Server color {self.server_color} found in available colors, removing it")
                self.available_colors.remove(self.server_color)

            if not self.available_colors:
                print(f"ERROR: No colors available for player {player_id}")
                # Instead of defaulting to blue (server might have it), assign a unique fallback
                used_colors = set(self.player_colors.values())
                all_colors = ["blue", "red", "yellow", "green"]
                for fallback_color in all_colors:
                    if fallback_color not in used_colors:
                        print(f"Using fallback color {fallback_color} for player {player_id}")
                        self.player_colors[player_id] = fallback_color
                        return fallback_color

                # Ultimate fallback - this shouldn't happen with 4 colors and max 4 players
                print(f"CRITICAL: All colors exhausted, assigning 'blue' to {player_id}")
                return "blue"

            # Client gets a random color from remaining colors
            color = random.choice(self.available_colors)
            self.available_colors.remove(color)
            self.player_colors[player_id] = color
            print(f"Assigned random color {color} to player {player_id}, remaining: {self.available_colors}")
            return color

    def release_player_color(self, player_id):
        """Return a player's color to the available pool when they disconnect - thread safe"""
        with self.color_assignment_lock:
            if player_id in self.player_colors:
                color = self.player_colors[player_id]

                # Don't release server's own color
                server_name = getattr(self, 'player_name', 'host')
                if player_id != server_name:
                    self.available_colors.append(color)
                    print(f"Released color {color} from player {player_id}")

                del self.player_colors[player_id]
    def run_command_checks(self):
        """Run periodic checks for unacknowledged commands"""
        while self.running:
            self.check_unacknowledged_commands()
            time.sleep(0.5)  # Check every half second

    def get_server_ip(self):
        return self.ip, self.port

    def get_players_list(self):
        """Return a list of connected players in the same format as clients expect"""
        with self.clients_lock:
            client_tuples = []

            # First add server/host entry
            server_name = getattr(self, 'player_name', 'Host')
            server_color = getattr(self, 'server_color', 'blue')
            server_display = f"{server_name} ({server_color}) (host)"
            client_tuples.append(((self.ip, self.port), server_display))

            # Then add connected clients
            for client in self.clients:
                client_addr = client['addr']
                client_name = client['name']
                client_color = client['color']
                client_display = f"{client_name} ({client_color})"
                client_tuples.append((client_addr, client_display))

            print(f"Server returning player list: {[p[1] for p in client_tuples]}")
            return client_tuples

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
                    # Handle timeouts - check for disconnected clients
                    current_time = time.time()
                    with self.clients_lock:
                        to_remove = []
                        for client in self.clients:
                            client_addr = client['addr']
                            if client_addr not in self.client_last_seen or current_time - self.client_last_seen[client_addr] > self.client_timeout:
                                to_remove.append(client)

                        for client in to_remove:
                            self.release_player_color(client['name'])
                            self.clients.remove(client)
                            print(f"Client {client['addr']} ({client['name']}) timed out")

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
                        if client['addr'] == addr:
                            client_found = True
                            break

                if not client_found:
                    print(f"New connection from {addr}")


                # Process the received data
                try:
                    decoded = data.decode()
                    # print(f"Received from {addr}: {decoded}")
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
                    parts = decoded.split(",", 1)
                    if len(parts) == 2:
                        base_name = parts[1]

                    validation_result = self.validate_connection_request(base_name, addr)

                    if validation_result["accepted"]:
                        unique_name = self.get_unique_player_name(base_name)
                        assigned_color = self.assign_color_to_player(unique_name)
                        client_id = self.assign_client_id()

                        client_data = {
                            'addr': addr,
                            'name': unique_name,
                            'color': assigned_color,
                            'client_id': client_id
                        }

                        with self.clients_lock:
                            self.clients.append(client_data)

                        print(f"Connection accepted: {base_name} -> {unique_name} ({assigned_color}) ID:{client_id}")

                        # Send connection confirmation
                        connection_response = json.dumps({
                            "type": "connection_accepted",
                            "assigned_name": unique_name,
                            "assigned_color": assigned_color,
                            "client_id": client_id
                        })
                        # Send connection acceptance
                        connection_response = json.dumps({
                            "type": "connection_accepted",
                            "assigned_name": unique_name,
                            "assigned_color": assigned_color,
                            "client_id": client_id
                        })
                        self.server_socket.sendto(connection_response.encode(), addr)

                        # Broadcast to clients
                        self.broadcast_player_list_update()

                        # Update server's own lobby view
                        if hasattr(self, 'lobby_update_callback') and self.lobby_update_callback:
                            arcade.schedule_once(lambda dt: self.lobby_update_callback(), 0)
                    else:
                        # Send connection rejection
                        rejection_response = json.dumps({
                            "type": "connection_rejected",
                            "reason": validation_result["reason"]
                        })
                        self.server_socket.sendto(rejection_response.encode(), addr)
                        print(f"Connection rejected for {addr}: {validation_result['reason']}")

                # Handle get_players command
                elif decoded == "get_players":
                    print(f"Client {addr} requesting player list (fallback)")
                    try:
                        player_list = self.get_players_list()
                        # Convert tuples to lists for JSON
                        serializable_players = []
                        for player_tuple in player_list:
                            addr_data, display_name = player_tuple
                            if isinstance(addr_data, tuple):
                                addr_list = list(addr_data)
                            else:
                                addr_list = addr_data
                            serializable_players.append([addr_list, display_name])

                        players_json = json.dumps(serializable_players)
                        response_msg = f"players:{players_json}"
                        self.server_socket.sendto(response_msg.encode(), addr)
                        print(f"Sent fallback player list to {addr}")
                    except Exception as e:
                        print(f"Error sending player list to {addr}: {e}")


                elif decoded == "get_server_name":
                    print(f"Sending server name to {addr}")
                    server_name = getattr(self, 'player_name', 'host')
                    server_color = getattr(self, 'server_color', 'blue')
                    response = json.dumps({
                        "type": "server_name",
                        "server_name": server_name,
                        "server_color": server_color
                    })
                    print(f"Server -> get_server_name: {response}")
                    self.server_socket.sendto(response.encode(), addr)


                # Handle disconnect message
                elif decoded == "disconnect":
                    print(f"{addr} is disconnecting")

                    in_game = hasattr(self, 'picked_map') and self.picked_map is not None

                    if in_game:
                        try:
                            self.handle_client_disconnect_in_game(addr)
                        except Exception as e:
                            print(f"Error handling game disconnect for {addr}: {e}")
                            with self.clients_lock:
                                self.clients = [c for c in self.clients if c['addr'] != addr]
                    else:
                        # During lobby: remove and instantly update
                        with self.clients_lock:
                            for client in self.clients[:]:
                                if client['addr'] == addr:
                                    self.release_player_color(client['name'])
                                    self.release_client_id(client['client_id'])
                                    self.clients.remove(client)
                                    print(f"Client {addr} ({client['name']}) disconnected from lobby")
                                    break

                        # Broadcast to clients
                        self.broadcast_player_list_update()

                        # FIX: Also update server's own lobby view
                        if hasattr(self, 'lobby_update_callback') and self.lobby_update_callback:
                            arcade.schedule_once(lambda dt: self.lobby_update_callback(), 0)

                    # Remove from last_seen
                    if addr in self.client_last_seen:
                        del self.client_last_seen[addr]

                    # Update timeout handling to also release client IDs:
            except socket.timeout:
                # Handle timeouts - check for disconnected clients
                current_time = time.time()
                with self.clients_lock:
                    to_remove = []
                    for client in self.clients:
                        client_addr = client['addr']
                        if client_addr not in self.client_last_seen or current_time - self.client_last_seen[
                            client_addr] > self.client_timeout:
                            to_remove.append(client)

                    for client in to_remove:
                        client_addr = client['addr']

                        # Check if we're in game - if so, handle as game disconnect
                        in_game = hasattr(self, 'picked_map') and self.picked_map is not None

                        if in_game:
                            # Handle as game disconnect (this will broadcast to other clients)
                            self.handle_client_disconnect_in_game(client_addr)
                        else:
                            # Handle as lobby disconnect and release client ID
                            self.release_player_color(client['name'])
                            self.release_client_id(client['client_id'])
                            self.clients.remove(client)
                            print(f"Client {client['addr']} ({client['name']}) timed out in lobby")

                            # Broadcast to clients
                            self.broadcast_player_list_update()

                            # FIX: Also update server's own lobby view
                            if hasattr(self, 'lobby_update_callback') and self.lobby_update_callback:
                                arcade.schedule_once(lambda dt: self.lobby_update_callback(), 0)

                        # Remove from last_seen
                        if client_addr in self.client_last_seen:
                            del self.client_last_seen[client_addr]

                continue
            except Exception as e:
                print(f"Error handling client data: {e}")
                traceback.print_exc()

        print("Client handler loop exited")

    def validate_connection_request(self, player_name, client_addr):
        """Validate incoming connection request"""

        # Check if server is full (max 4 players including server)
        with self.clients_lock:
            if len(self.clients) >= 3:  # 3 clients + 1 server = 4 total
                return {
                    "accepted": False,
                    "reason": "Server is full (maximum 4 players)"
                }

        # Check if we're already in game
        if hasattr(self, 'picked_map') and self.picked_map is not None:
            return {
                "accepted": False,
                "reason": "Game already in progress"
            }

        # Check for empty player name
        if not player_name or player_name.strip() == "":
            return {
                "accepted": False,
                "reason": "Invalid player name"
            }

        # Check if client is already connected (reconnection attempt)
        with self.clients_lock:
            for client in self.clients:
                if client['addr'] == client_addr:
                    return {
                        "accepted": False,
                        "reason": "Already connected from this address"
                    }

        # All validation passed
        return {
            "accepted": True,
            "reason": None
        }

    def get_unique_player_name(self, base_name):
        """Generate a unique player name by appending numbers if necessary"""
        with self.clients_lock:
            # Get all existing names including server
            existing_names = [client['name'] for client in self.clients]

            # Also check server name to avoid conflicts
            server_name = getattr(self, 'player_name', 'host')
            if server_name:
                existing_names.append(server_name)

        if base_name not in existing_names:
            return base_name

        # If the name is in use, try appending numbers
        counter = 1
        while True:
            new_name = f"{base_name}{counter}"
            if new_name not in existing_names:
                return new_name
            counter += 1

    def debug_color_assignments(self):
        """Debug method to check current color assignments"""
        with self.color_assignment_lock:
            print(f"=== COLOR ASSIGNMENT DEBUG ===")
            print(f"Server color: {self.server_color}")
            print(f"Available colors: {self.available_colors}")
            print(f"Player colors: {self.player_colors}")

            # Check for duplicates
            all_assigned_colors = list(self.player_colors.values())
            if len(all_assigned_colors) != len(set(all_assigned_colors)):
                print("ERROR: Duplicate colors detected!")
                for color in set(all_assigned_colors):
                    players_with_color = [k for k, v in self.player_colors.items() if v == color]
                    if len(players_with_color) > 1:
                        print(f"  Color {color} assigned to: {players_with_color}")
            else:
                print("✓ No duplicate colors detected")
            print(f"==============================")

    def send_command(self, command, client_addr=None, require_ack=False, max_retries=10, retry_interval=1.0):
        command_id = str(time.time())

        if command == "map_selected":
            if not self.picked_map:
                print("ERROR: No map selected to broadcast")
                return

            command_data = {
                "type": "command",
                "command": "map_selected",
                "map_name": self.picked_map,
                "id": command_id,
                "require_ack": require_ack
            }
            command_msg = json.dumps(command_data)
            print(f"Broadcasting selected map: {self.picked_map}")


        elif command == "game_start":
            # Use already assigned colors including server color
            color_assignments = {}
            spawn_assignments = {}

            # First add server's color assignment
            server_name = getattr(self, 'player_name', 'host')
            color_assignments[server_name] = self.server_color
            spawn_assignments[server_name] = 0  # Server always gets spawn position 0

            with self.clients_lock:
                # Then add client color assignments
                for client in self.clients:
                    client_name = client['name']
                    color_assignments[client_name] = client['color']
                    spawn_assignments[client_name] = client['client_id']

            command_data = {
                "type": "command",
                "command": "game_start",
                "color_assignments": color_assignments,
                "spawn_assignments": spawn_assignments,
                "id": command_id,
                "require_ack": require_ack
            }
            command_msg = json.dumps(command_data)
            print(f"Game start color assignments: {color_assignments}")  # Debug output
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
                if isinstance(client_addr, dict):
                    actual_addr = client_addr['addr']
                else:
                    actual_addr = client_addr[0] if isinstance(client_addr, tuple) and isinstance(client_addr[0], tuple) else client_addr

                self.server_socket.sendto(command_msg.encode(), actual_addr)
                print(f"Command '{command}' -> {client_addr}")
            except Exception as e:
                print(f"Error sending command to {client_addr}: {e}")
        else:
            with self.clients_lock:
                for client in self.clients:
                    try:
                        actual_addr = client['addr']
                        self.server_socket.sendto(command_msg.encode(), actual_addr)
                    except Exception as e:
                        print(f"Error sending command to {client}: {e}")
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

            if "game_start" in data.get("command", ""):
                max_retries = 30
                retry_interval = 0.3

            if current_time - data["time_sent"] > retry_interval:
                if data["retries"] < max_retries:
                    if data["addr"]:
                        self.server_socket.sendto(data["command"].encode(), data["addr"])
                    else:
                        # Fix: Use dictionary keys instead of indices
                        with self.clients_lock:
                            for client in self.clients:
                                try:
                                    self.server_socket.sendto(data["command"].encode(), client['addr'])
                                except Exception as e:
                                    print(f"Error resending command to {client['name']}: {e}")

                    data["retries"] += 1
                    data["time_sent"] = current_time
                    print(f"Resending command {cmd_id}, retry #{data['retries']}")
                else:
                    print(f"Max retries reached for command {cmd_id}")
                    to_remove.append(cmd_id)

        for cmd_id in to_remove:
            self.pending_acks.pop(cmd_id)

    def game_broadcast_data(self, game_data, except_ip=None):
        """Broadcast game data to all clients except the one specified"""
        if not self.running:
            return

        if isinstance(game_data, (dict, list)):
            data_json = json.dumps(game_data)
        else:
            data_json = game_data

        with self.clients_lock:
            clients_copy = self.clients[:]

        for client in clients_copy:
            try:
                client_addr = client['addr']

                # Skip if this is the excluded client
                if except_ip and client_addr == except_ip:
                    continue

                # Skip if client is marked as disconnected
                if client.get('status') == 'disconnected':
                    continue

                # Set timeout to prevent hanging
                self.server_socket.settimeout(0.1)
                self.server_socket.sendto(data_json.encode(), client_addr)
                # print(f"Sent game data to {client['name']} at {client_addr}")

            except socket.timeout:
                print(f"Timeout sending to {client.get('name', 'unknown')} at {client_addr}")
                with self.clients_lock:
                    for c in self.clients:
                        if c['addr'] == client_addr:
                            c['status'] = 'disconnected'
                            break
            except Exception as e:
                print(f"Error broadcasting game data to {client.get('name', 'unknown')}: {e}")
                with self.clients_lock:
                    for c in self.clients:
                        if c['addr'] == client_addr:
                            c['status'] = 'disconnected'
                            break
            finally:
                try:
                    self.server_socket.settimeout(0.5)
                except:
                    pass

    def broadcast_selected_map(self):
        """Pick a random map and broadcast it to all connected clients with ACK requirement"""
        if not self.all_maps:
            print("ERROR: No maps available to select")
            return

        # Pick the map
        self.picked_map = random.choice(self.all_maps)
        print(f"Selected map: {self.picked_map}")

        # MAP DEBUG
        # self.picked_map = "stones"

        self.send_command("map_selected", require_ack=True)

    def send_server_disconnect(self, notify_clients=True):
        """Send disconnect command to all clients before shutting down"""
        if notify_clients and self.clients:
            print("Notifying all clients of server disconnect...")
            self.send_command("server_disconnect", require_ack=True, retry_interval=0.3, max_retries=10)

            # Wait for acknowledgments with timeout
            max_wait_time = 3.0
            start_time = time.time()

            while (time.time() - start_time) < max_wait_time and self.pending_acks:
                server_disconnect_pending = any(
                    "server_disconnect" in data.get("command", "")
                    for data in self.pending_acks.values()
                )
                if not server_disconnect_pending:
                    break
                time.sleep(0.1)

            print("All clients notified of server disconnect")

        # Now proceed with shutdown
        self.shutdown()

    def handle_client_disconnect_in_game(self, client_addr):
        """Handle client disconnect during game - mark as dead and notify all players"""
        with self.clients_lock:
            disconnected_client = None
            for client in self.clients[:]:
                if client['addr'] == client_addr:
                    disconnected_client = client
                    break

            if disconnected_client:
                player_name = disconnected_client['name']

                # Don't remove from clients list during game, just mark as disconnected
                disconnected_client['status'] = 'disconnected'
                print(f"Player {player_name} disconnected during game - marking as dead")

                # Instead of broadcasting directly from networking thread,
                # schedule the broadcast to happen from main thread
                if hasattr(self, 'window') and self.window and hasattr(self.window, 'current_view'):
                    current_view = self.window.current_view
                    if hasattr(current_view, 'handle_player_disconnect'):
                        # Schedule on main thread to avoid socket contention
                        arcade.schedule_once(
                            lambda dt, name=player_name: current_view.handle_player_disconnect(name),
                            0
                        )
                        print(f"Scheduled player disconnect handling for {player_name}")
                    else:
                        # Fallback: try to handle it directly in game view
                        if hasattr(current_view, 'process_tank_update'):
                            disconnect_message = {
                                "type": "player_disconnected",
                                "player_id": player_name
                            }
                            arcade.schedule_once(
                                lambda dt, data=disconnect_message: current_view.process_tank_update(data),
                                0
                            )
                            print(f"Scheduled tank kill for {player_name} on server's game view")

                print(f"Disconnection handling complete for {player_name}")

    def assign_client_id(self):
        """Assign a client ID, reusing available ones first"""
        with self.clients_lock:
            # First try to reuse an available ID
            if self.available_client_ids:
                client_id = min(self.available_client_ids)  # Get the smallest available ID
                self.available_client_ids.remove(client_id)
                print(f"Reusing client ID: {client_id}")
                return client_id

            # If no available IDs and we haven't reached the maximum, create a new one
            if self.next_client_id < self.max_client_ids:
                client_id = self.next_client_id
                self.next_client_id += 1
                print(f"Assigned new client ID: {client_id}")
                return client_id

            # If we've reached maximum clients, find the lowest available ID to reuse
            # This shouldn't happen in normal operation but provides a fallback
            all_used_ids = {client['client_id'] for client in self.clients}
            for i in range(self.max_client_ids):
                if i not in all_used_ids:
                    print(f"Fallback: Assigned client ID: {i}")
                    return i

            # Ultimate fallback - return 0 (this means server is full)
            print("WARNING: Server is full, reusing ID 0")
            return 0

    def release_client_id(self, client_id):
        """Release a client ID back to the available pool"""
        if client_id is not None and 0 <= client_id < self.max_client_ids:
            self.available_client_ids.add(client_id)
            print(f"Released client ID {client_id} for reuse")

    def broadcast_player_list_update(self):
        """Instantly broadcast updated player list to all clients"""
        if not self.running:
            return

        try:
            # Get current player list in the correct format
            player_list = self.get_players_list()

            # Convert tuples to lists for JSON serialization
            serializable_players = []
            for player_tuple in player_list:
                # Convert tuple (addr, display_name) to list [addr, display_name]
                addr, display_name = player_tuple
                # Convert addr tuple to list as well
                if isinstance(addr, tuple):
                    addr_list = list(addr)
                else:
                    addr_list = addr
                serializable_players.append([addr_list, display_name])

            # Create player list update message
            update_message = {
                "type": "player_list_update",
                "players": serializable_players
            }

            # Broadcast to all clients instantly
            message_json = json.dumps(update_message)
            with self.clients_lock:
                for client in self.clients:
                    try:
                        self.server_socket.sendto(message_json.encode(), client['addr'])
                        print(f"Sent instant update to {client['name']}: {message_json[:100]}...")
                    except Exception as e:
                        print(f"Error broadcasting to {client['name']}: {e}")

            print(f"Broadcasted instant player list to {len(self.clients)} clients")

        except Exception as e:
            print(f"Error broadcasting player list: {e}")
            import traceback
            traceback.print_exc()

def _extract_player_info(self, player_text):
        """Extract player information from display text"""
        import re

        # Extract color using regex - look for (color) pattern
        color_match = re.search(r'\((\w+)\)(?:\s*\([^)]*\))?', player_text)
        if color_match:
            color = color_match.group(1).lower()
            # Remove all parenthetical parts to get clean name
            clean_name = re.sub(r'\s*\([^)]*\)', '', player_text).strip()
            # Check if it's a host
            is_host = "(host)" in player_text.lower()
            return clean_name, color, is_host
        else:
            # Fallback
            clean_name = re.sub(r'\s*\([^)]*\)', '', player_text).strip()
            return clean_name, "blue", False

