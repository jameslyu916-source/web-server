import socket

# Config server host and port
HOST = '127.0.0.1'
PORT = 6789

def main():
    # 1. Creating a TCP socket
    # AF_INET using IPv4，SOCK_STREAM using TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # 2. Binding address and port
    # This line is to prevent the error of port already in use (Address already in use)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    
    # 3. Start listening for connections
    server_socket.listen(5)
    print(f"Server is running on http://{HOST}:{PORT} ...")
    print("Press Ctrl+C to stop the server")

    try:
        while True:
            # 4. Wait for a browser connection
            # accept() will block until a browser connects
            connection_socket, client_address = server_socket.accept()
            print(f"\n--- Got connection from {client_address} ---")

            # 5. Receive the message sent by the browser
            # Receive up to 1024 bytes at a time
            request = connection_socket.recv(1024).decode('utf-8')
            print("--- Request received ---")
            print(request)  # Print the request content to see what was received

            # 6. For now, don't return any actual content, just close the connection
            # In the next version, I'll implement the response logic
            connection_socket.close()
            print("--- Connection closed ---")

    except KeyboardInterrupt:
        print("\nServer is shutting down...")
        server_socket.close()

if __name__ == "__main__":
    main()