import socket
import threading
import json
import time
from pathlib import Path


class Server:
    def __init__(self, ip='127.0.0.1', port=5000):
        self.ip = str(ip)
        self.port = int(port)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = True

        self.pending_acks = {}

        # Enable address reuse
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(f"Server socket created at {self.ip}:{self.port}")

        self.clients = []
        print(f"Initial client list: {self.clients}")

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

    def start(self):
        self.server_socket.bind((self.ip, self.port))
        print(f"Server started at {self.ip}:{self.port}")

        # Run handle_clients in a separate thread for responsiveness
        client_thread = threading.Thread(target=self.handle_clients, daemon=True)
        client_thread.start()

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
                except socket.timeout:
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

                # In Server.py's handle_clients method, add processing for ACKs
                try:
                    data_dict = json.loads(decoded)
                    if data_dict.get("type") == "ack" and data_dict.get("id"):
                        # Remove from pending acknowledgments
                        cmd_id = data_dict.get("id")
                        if cmd_id in self.pending_acks:
                            self.pending_acks.pop(cmd_id)
                            print(f"Received ACK for command {cmd_id}")
                        continue
                except json.JSONDecodeError:
                    # Not JSON, handle as before
                    pass

                if decoded.startswith("connection,"):
                    parts = decoded.split(",", 1)  # Split only at first comma
                    if len(parts) == 2:
                        new_name = parts[1]
                        print(f"New connection: {new_name} from {addr}")
                        with self.clients_lock:
                            # Store address and name together as a tuple
                            self.clients.append((addr, new_name))
                        print(f"Clients: {self.clients}")

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
                    response = json.dumps({"type": "data", "server_name": self.player_name})
                    print(f"Server -> 142: get_server_name: {response}")
                    self.server_socket.sendto(response.encode(), addr)


                # Handle disconnect message
                if decoded == "disconnect":
                    print(f"{addr} is disconnecting")
                    with self.clients_lock:
                        if addr in self.clients:
                            self.clients.remove(addr)
                            print(f"Client {addr} disconnected")
                            print(f"Clients: {[f'{client[0][0]}:{client[0][1]},{self.player_name}' for client in self.clients]}")
                    continue

            except Exception as e:
                print(f"Error: {e}")
                if not self.running:
                    break

        print("Client handler loop exited")

    def send_command(self, command, client_addr=None, require_ack=False):
        """Send a command to a specific client or broadcast to all"""
        command_id = str(time.time())  # Use timestamp as unique ID

        command_msg = json.dumps({
            "type": "command",
            "command": command,
            "id": command_id,
            "require_ack": require_ack
        })

        if require_ack:
            # Store in pending acknowledgments dict with timestamp
            self.pending_acks[command_id] = {
                "time_sent": time.time(),
                "retries": 0,
                "command": command_msg,
                "addr": client_addr
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
        """Periodically check for unacknowledged commands"""
        current_time = time.time()
        to_remove = []

        for cmd_id, data in self.pending_acks.items():
            # If command was sent more than 1 second ago
            if current_time - data["time_sent"] > 1.0:
                # Max 5 retries
                if data["retries"] < 5:
                    # Resend the command
                    if data["addr"]:
                        self.server_socket.sendto(data["command"].encode(), data["addr"])
                    else:
                        with self.clients_lock:
                            for addr in self.clients:
                                self.server_socket.sendto(data["command"].encode(), addr)

                    # Update retries and time sent
                    data["retries"] += 1
                    data["time_sent"] = current_time
                    print(f"Resending command {cmd_id}, retry #{data['retries']}")
                else:
                    # Max retries reached, consider client disconnected
                    print(f"Max retries reached for command {cmd_id}")
                    to_remove.append(cmd_id)

        # Remove expired entries
        for cmd_id in to_remove:
            self.pending_acks.pop(cmd_id)

    def game_broadcast_data(self, game_data, except_ip):
        """Broadcast game data to clients except the one specified"""
        while self.running:
            # Example game data to broadcast
            game_data = {
                "type": "game_update",
                "data": {
                    "message": "Game is running",
                }
            }
            self.send_command(json.dumps(game_data))