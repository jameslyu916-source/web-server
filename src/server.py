import socket
import os
import threading
import datetime
import time

# Server configuration
HOST = '0.0.0.0'  # Allow connections from other hosts
PORT = 6789
STATIC_DIR = 'test_files'
LOG_FILE = 'server.log'

def get_content_type(filename):
    """Return correct Content-Type based on file extension"""
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

def get_http_time(timestamp=None):
    """Convert timestamp to HTTP date format (RFC 1123)"""
    if timestamp is None:
        timestamp = time.time()
    return datetime.datetime.utcfromtimestamp(timestamp).strftime('%a, %d %b %Y %H:%M:%S GMT')

def parse_http_headers(request):
    """Parse all HTTP request headers into a dictionary"""
    headers = {}
    lines = request.split('\n')
    # Skip request line (first line)
    for line in lines[1:]:
        line = line.strip()
        if not line:
            break
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip().lower()] = value.strip()
    return headers

def log_request(client_ip, method, path, status_code):
    """Write request log to server.log"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"{timestamp} | {client_ip} | {method} | {path} | {status_code}\n"
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_line)

def handle_client_connection(connection_socket, client_address):
    """Handle a single client connection (supports keep-alive)"""
    client_ip = client_address[0]
    keep_alive = True
    
    while keep_alive:
        try:
            # Set timeout for keep-alive connections (5 seconds)
            connection_socket.settimeout(5.0)
            request = connection_socket.recv(4096).decode('utf-8', errors='ignore')
            
            if not request:
                break
            
            # Parse request line and headers
            request_lines = request.split('\n')
            first_line = request_lines[0].strip()
            headers = parse_http_headers(request)
            
            print(f"\n[{client_ip}] Request: {first_line}")
            
            # Validate request line format
            parts = first_line.split()
            if len(parts) != 3:
                status_code = 400
                response_body = b"Bad Request"
                response_headers = (
                    "HTTP/1.1 400 Bad Request\r\n"
                    "Content-Type: text/plain; charset=utf-8\r\n"
                    f"Content-Length: {len(response_body)}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                )
                connection_socket.send(response_headers.encode('utf-8') + response_body)
                log_request(client_ip, parts[0] if len(parts)>=1 else "UNKNOWN", parts[1] if len(parts)>=2 else "/", status_code)
                break
            
            method, path, http_version = parts
            
            # Check for forbidden files (403 Forbidden)
            if path.startswith('/.') or path.endswith('.log'):
                status_code = 403
                response_body = b"Forbidden"
                response_headers = (
                    f"{http_version} 403 Forbidden\r\n"
                    "Content-Type: text/plain; charset=utf-8\r\n"
                    f"Content-Length: {len(response_body)}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                )
                connection_socket.send(response_headers.encode('utf-8') + response_body)
                log_request(client_ip, method, path, status_code)
                break
            
            # Resolve file path
            if path == '/':
                file_path = os.path.join(STATIC_DIR, 'index.html')
            else:
                file_path = os.path.join(STATIC_DIR, path.lstrip('/'))
            
            # Prevent directory traversal attack
            if not os.path.abspath(file_path).startswith(os.path.abspath(STATIC_DIR)):
                status_code = 403
                response_body = b"Forbidden"
                response_headers = (
                    f"{http_version} 403 Forbidden\r\n"
                    "Content-Type: text/plain; charset=utf-8\r\n"
                    f"Content-Length: {len(response_body)}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                )
                connection_socket.send(response_headers.encode('utf-8') + response_body)
                log_request(client_ip, method, path, status_code)
                break
            
            # Check if file exists
            if not os.path.isfile(file_path):
                status_code = 404
                response_body = b"File Not Found"
                response_headers = (
                    f"{http_version} 404 Not Found\r\n"
                    "Content-Type: text/plain; charset=utf-8\r\n"
                    f"Content-Length: {len(response_body)}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                )
                connection_socket.send(response_headers.encode('utf-8') + response_body)
                log_request(client_ip, method, path, status_code)
                break
            
            # Get file modification time
            file_mtime = os.path.getmtime(file_path)
            file_mtime_http = get_http_time(file_mtime)
            
            # Check If-Modified-Since header (304 Not Modified)
            if 'if-modified-since' in headers:
                try:
                    client_mtime = time.mktime(time.strptime(headers['if-modified-since'], '%a, %d %b %Y %H:%M:%S GMT'))
                    # Allow 1 second tolerance for clock differences
                    if file_mtime <= client_mtime + 1:
                        status_code = 304
                        response_headers = (
                            f"{http_version} 304 Not Modified\r\n"
                            f"Last-Modified: {file_mtime_http}\r\n"
                            "Connection: keep-alive\r\n"
                            "\r\n"
                        )
                        connection_socket.send(response_headers.encode('utf-8'))
                        log_request(client_ip, method, path, status_code)
                        # Check connection header for keep-alive
                        keep_alive = headers.get('connection', '').lower() == 'keep-alive'
                        continue
                except ValueError:
                    # Ignore invalid If-Modified-Since format
                    pass
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Prepare response headers
            content_type = get_content_type(file_path)
            status_code = 200
            
            response_headers = [
                f"{http_version} 200 OK",
                f"Content-Type: {content_type}",
                f"Content-Length: {len(file_content)}",
                f"Last-Modified: {file_mtime_http}"
            ]
            
            # Handle Connection header
            if headers.get('connection', '').lower() == 'keep-alive':
                response_headers.append("Connection: keep-alive")
                keep_alive = True
            else:
                response_headers.append("Connection: close")
                keep_alive = False
            
            # Join headers and add empty line
            response_headers_str = '\r\n'.join(response_headers) + '\r\n\r\n'
            
            # Send response
            connection_socket.send(response_headers_str.encode('utf-8'))
            
            # Only send body for GET requests (not HEAD)
            if method == 'GET':
                connection_socket.send(file_content)
            
            print(f"[{client_ip}] Response: {status_code} {len(file_content)} bytes")
            log_request(client_ip, method, path, status_code)
            
        except socket.timeout:
            # Keep-alive timeout, close connection
            print(f"[{client_ip}] Keep-alive timeout")
            break
        except Exception as e:
            print(f"[{client_ip}] Error handling request: {str(e)}")
            break
    
    connection_socket.close()
    print(f"[{client_ip}] Connection closed")

def main():
    """Main server function"""
    # Create log file if it doesn't exist
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write("Timestamp | Client IP | Method | Path | Status Code\n")
            f.write("-" * 70 + "\n")
    
    # Ensure static directory exists
    if not os.path.exists(STATIC_DIR):
        os.makedirs(STATIC_DIR)
        print(f"Created static directory: {STATIC_DIR}")
    
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)  # Increase backlog for multi-threaded
    
    print(f"=== Multi-threaded Web Server Started ===")
    print(f"Listening on: http://{HOST}:{PORT}")
    print(f"Static files: {os.path.abspath(STATIC_DIR)}")
    print(f"Log file: {os.path.abspath(LOG_FILE)}")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        while True:
            connection_socket, client_address = server_socket.accept()
            print(f"New connection from {client_address}")
            
            # Start a new thread for each client connection
            client_thread = threading.Thread(
                target=handle_client_connection,
                args=(connection_socket, client_address),
                daemon=True
            )
            client_thread.start()
            
            print(f"Active threads: {threading.active_count() - 1}")
    
    except KeyboardInterrupt:
        print("\n--- Server shutting down ---")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()