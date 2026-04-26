import socket
import os

# Config server host and port
HOST = '127.0.0.1'
PORT = 6789
# Static files root directory
STATIC_DIR = 'test_files'

def get_content_type(filename):
    """Get the corresponding Content-Type based on the file extension"""
    ext = os.path.splitext(filename)[1].lower()
    content_types = {
        '.html': 'text/html; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.js': 'application/javascript; charset=utf-8',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.ico': 'image/x-icon',
        '.txt': 'text/plain; charset=utf-8'
    }
    return content_types.get(ext, 'application/octet-stream')

def handle_request(connection_socket):
    """Handle a single client request"""
    try:
        # Receive request data (increase buffer to 4096 to accommodate larger requests)
        request = connection_socket.recv(4096).decode('utf-8', errors='ignore')
        if not request:
            return

        # Parse request line
        request_lines = request.split('\n')
        first_line = request_lines[0].strip()
        print(f"\nRequest line: {first_line}")

        # Validate request line format
        parts = first_line.split()
        if len(parts) != 3:
            response = (
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                "Content-Length: 12\r\n"
                "\r\n"
                "Bad Request"
            )
            connection_socket.send(response.encode('utf-8'))
            return

        method, path, http_version = parts

        # Only support GET method
        if method != 'GET':
            response = (
                f"{http_version} 405 Method Not Allowed\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                "Allow: GET\r\n"
                "Content-Length: 17\r\n"
                "\r\n"
                "Method Not Allowed"
            )
            connection_socket.send(response.encode('utf-8'))
            print(f"Error: {method} method not supported")
            return

        # Determine the file path based on the requested path
        if path == '/':
            file_path = os.path.join(STATIC_DIR, 'index.html')
        else:
            # Prevent directory traversal by normalizing the path and ensuring it stays within STATIC_DIR
            file_path = os.path.join(STATIC_DIR, path.lstrip('/'))
            # Check if the resolved file path is still within the STATIC_DIR
            if not os.path.abspath(file_path).startswith(os.path.abspath(STATIC_DIR)):
                file_path = os.path.join(STATIC_DIR, '404.html')

        print(f"Looking for file: {file_path}")

        # Read the file content and send response
        try:
            # Read file content in binary mode to support all file types
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Construct successful response
            content_type = get_content_type(file_path)
            response_headers = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {len(file_content)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            )
            # First send headers, then send file content
            connection_socket.send(response_headers.encode('utf-8'))
            connection_socket.send(file_content)
            print(f"Success: Sent {len(file_content)} bytes, Content-Type: {content_type}")

        except FileNotFoundError:
            # 404 Not Found response
            error_msg = f"File not found: {file_path}"
            print(f"Error: {error_msg}")
            response = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(error_msg)}\r\n"
                "\r\n"
                f"{error_msg}"
            )
            connection_socket.send(response.encode('utf-8'))

        except Exception as e:
            # Other server errors
            error_msg = f"Server error: {str(e)}"
            print(f"Error: {error_msg}")
            response = (
                "HTTP/1.1 500 Internal Server Error\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(error_msg)}\r\n"
                "\r\n"
                f"{error_msg}"
            )
            connection_socket.send(response.encode('utf-8'))

    finally:
        # Close the connection socket after handling the request
        connection_socket.close()
        print("--- Connection closed ---")

def main():
    """Main function for the server"""
    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Set port reuse option to avoid "Address already in use" error on restart
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind address and port
    server_socket.bind((HOST, PORT))
    # Start listening (maximum pending connections: 5)
    server_socket.listen(5)
    
    print(f"=== Static File Server Running ===")
    print(f"Address: http://{HOST}:{PORT}")
    print(f"Static files dir: {os.path.abspath(STATIC_DIR)}")
    print("Press Ctrl+C to stop the server\n")

    try:
        # Continuously accept and handle client connections
        while True:
            connection_socket, client_address = server_socket.accept()
            print(f"--- Got connection from {client_address} ---")
            # Handle client request
            handle_request(connection_socket)

    except KeyboardInterrupt:
        print("\n--- Server is shutting down ---")
    finally:
        # Close the server socket
        server_socket.close()

if __name__ == "__main__":
    # Ensure static files directory exists
    if not os.path.exists(STATIC_DIR):
        os.makedirs(STATIC_DIR)
        print(f"Created static files directory: {STATIC_DIR}")
    main()