import socket
import threading
import json


class Server:
    def __init__(self, ip='127.0.0.1', port=5000):
        self.ip = str(ip)
        self.port = int(port)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = True

        # Enable address reuse
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(f"Server socket created at {self.ip}:{self.port}")

        self.clients = []
        print(f"Initial client list: {self.clients}")

        self.clients_lock = threading.Lock()

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
                    if addr not in self.clients:
                        print(f"Connection from {addr}")
                        self.clients.append(addr)
                        print(f"Clients: {self.clients}")

                # Process the received data
                try:
                    decoded = data.decode()
                    print(f"Received from {addr}: {decoded}")
                except UnicodeDecodeError:
                    print(f"Received non-text data from {addr}")
                    continue

                # Handle get_players command
                if decoded == "get_players":
                    print(f"Sending player list to {addr}")
                    with self.clients_lock:
                        client_addresses = [f"{client[0]}:{client[1]}" for client in self.clients]
                    response = json.dumps({"type": "clients", "clients": client_addresses})
                    self.server_socket.sendto(response.encode(), addr)
                    continue

                # Handle disconnect message
                if decoded == "disconnect":
                    print(f"{addr} is disconnecting")
                    with self.clients_lock:
                        if addr in self.clients:
                            self.clients.remove(addr)
                            print(f"Client {addr} disconnected")
                            print(f"Clients: {[f'{client[0]}:{client[1]}' for client in self.clients]}")
                    continue

            except Exception as e:
                print(f"Error: {e}")
                if not self.running:
                    break

        print("Client handler loop exited")

    def send_command(self, command, client_addr=None):
        """Send a command to a specific client or broadcast to all"""
        command_msg = json.dumps({"type": "command", "command": command})
        if client_addr:
            try:
                self.server_socket.sendto(command_msg.encode(), client_addr)
                print(f"Command '{command}' -> {client_addr}")
            except Exception as e:
                print(f"Error sending command to {client_addr}: {e}")
        else:
            with self.clients_lock:
                for addr in self.clients:
                    try:
                        self.server_socket.sendto(command_msg.encode(), addr)
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
