import socket
import time
import json

client_id = 0

def connect_to_server(ip, port, client_socket):
    global client_id
    try:
        client_socket.connect((ip, port))
        print(f"Connected to server at {ip}:{port}")
        client_socket.sendall(b"Connected")
    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()

def send_data(client_socket, data):
    try:
        client_socket.sendall(data.encode())
        print(f"Sent: {data}")
    except Exception as e:
        print(f"Error sending data: {e}")
        client_socket.close()

def receive_data(client_socket):
    try:
        data = client_socket.recv(1024)
        if not data:
            print("Server closed the connection")
            client_socket.close()
            return None
        return data.decode()
    except Exception as e:
        print(f"Error receiving data: {e}")
        client_socket.close()
        return None
def disconnect(client_socket):
    try:
        client_socket.close()
        print("Disconnected from server")
    except Exception as e:
        print(f"Error disconnecting: {e}")

if __name__ == "__main__":
    ip = "127.0.0.1"
    port = 5000
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    connect_to_server(ip, port, client_socket)
    # print all server messages
    while True:
        data = receive_data(client_socket)
        if data is None:
            break
        print(data)

    # Do not close the socket here if you want to keep the connection open
    print("Client is still connected and ready for more messages.")
    # You can now continue to send/receive more data as needed
