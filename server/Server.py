import socket
import threading
import json


class Server:
    def __init__(self, ip='127.0.0.1', port=5000):
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"Server socket created at {self.ip}:{self.port}")
        # Store client addresses instead of sockets (server is also a client)
        self.clients = [str(self.ip) + ":" + str(self.port)]
        print(f"Initial client list: {self.clients}")
        self.clients_lock = threading.Lock()

    def start(self):
        self.server_socket.bind((self.ip, self.port))
        # No listen() or accept() calls in UDP
        print(f"Server started at {self.ip}:{self.port}")
        try:
            # Single thread handles all clients in UDP
            self.handle_clients()
        except KeyboardInterrupt:
            print("Server shutting down.")
        finally:
            self.server_socket.close()

    def broadcast_client_list(self):
        with self.clients_lock:
            client_addresses = [f"{addr[0]}:{addr[1]}" for addr in self.clients]
            message = json.dumps({"type": "clients", "clients": client_addresses})
            for client_addr in self.clients:
                try:
                    self.server_socket.sendto(message.encode(), client_addr)
                except Exception as e:
                    print(f"Error sending to client {client_addr}: {e}")

    def handle_clients(self):
        while True:
            try:
                # Use recvfrom to get data and client address
                data, addr = self.server_socket.recvfrom(1024)

                # Check if this is a new client
                if addr not in self.clients:
                    print(f"Connection from {addr}")
                    with self.clients_lock:
                        self.clients.append(addr)
                    self.broadcast_client_list()
                    print(f"Clients: {[f'{client[0]}:{client[1]}' for client in self.clients]}")

                decoded = data.decode()
                print(f"Received from {addr}: {decoded}")

                # Handle get_players command. returns list of players
                if decoded == "get_players":
                    print(f"Sending player list to {addr}")
                    with self.clients_lock:
                        players = [f"{client[0]}:{client[1]}" for client in self.clients]
                    response = json.dumps({"type": "clients", "clients": players})
                    self.server_socket.sendto(response.encode(), addr)
                    continue

                # Handle disconnect message
                if decoded == "disconnect":
                    with self.clients_lock:
                        if addr in self.clients:
                            self.clients.remove(addr)
                    print(f"Client {addr} disconnected")
                    print(f"Clients: {[f'{client[0]}:{client[1]}' for client in self.clients]}")
                    self.broadcast_client_list()
                    continue

                # Echo response
                response = json.dumps({"type": "echo", "message": decoded})
                self.server_socket.sendto(response.encode(), addr)

            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    server = Server(ip="127.0.0.1", port=5000)
    server.start()
