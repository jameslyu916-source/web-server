import socket

# Config server host and port
HOST = '127.0.0.1'
PORT = 6789

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server is running on http://{HOST}:{PORT} ...")
    print("Press Ctrl+C to stop the server")

    try:
        while True:
            connection_socket, client_address = server_socket.accept()
            print(f"\n--- Got connection from {client_address} ---")

            # Receive request
            request = connection_socket.recv(1024).decode('utf-8')
            if not request:
                connection_socket.close()
                continue

            # Parse the first line of the request
            # The first line format: GET /index.html HTTP/1.1
            request_lines = request.split('\n')
            first_line = request_lines[0].strip()
            print(f"Request line: {first_line}")

            # Split the method, path, and HTTP version
            parts = first_line.split()
            if len(parts) != 3:
                print("Invalid request format")
                connection_socket.close()
                continue

            method = parts[0]
            path = parts[1]
            http_version = parts[2]

            print(f"Method: {method}")
            print(f"Requested path: {path}")
            print(f"HTTP version: {http_version}")

            # Convert the path to a filename
            # If the request is for the root path /, return index.html
            if path == '/':
                filename = 'test_files/index.html'
            else:
                # Remove the leading / to get the filename
                filename = 'test_files' + path

            print(f"Looking for file: {filename}")

            # Don't return content yet, implement in the next version
            connection_socket.close()
            print("--- Connection closed ---")

    except KeyboardInterrupt:
        print("\nServer is shutting down...")
        server_socket.close()

if __name__ == "__main__":
    main()