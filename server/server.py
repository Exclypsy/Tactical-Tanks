import socket
import threading
import json

clients = []
clients_lock = threading.Lock()

def broadcast_client_list():
    # Prepare and broadcast the list of all connected clients
    with clients_lock:
        client_addresses = [str(client.getpeername()) for client in clients]
        message = json.dumps({"type": "clients", "clients": client_addresses})
        for client in clients:
            try:
                client.sendall(message.encode())
            except Exception as e:
                print(f"Error sending to client: {e}")

def handle_client(client_socket, addr):
    print(f"Connection from {addr}")
    with clients_lock:
        clients.append(client_socket)
    broadcast_client_list()
    print([str(client.getpeername()) for client in clients])
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            decoded = data.decode()
            print(f"Received from {addr}: {decoded}")
            response = json.dumps({"type": "echo", "message": decoded})
            client_socket.sendall(response.encode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        with clients_lock:
            if client_socket in clients:
                clients.remove(client_socket)
        client_socket.close()
        print(f"Client {addr} disconnected")
        print([str(client.getpeername()) for client in clients])
        broadcast_client_list()

def start_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((ip, port))
    server_socket.listen(5)
    print(f"Server started at {ip}:{port}")
    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()

if __name__ == "__main__":
    start_server("127.0.0.1", 5000)
