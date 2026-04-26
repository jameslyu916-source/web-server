import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 6789))

# Send a malformed HTTP request (missing HTTP version)
s.send(b'GET /index.html\r\n\r\n')

response = s.recv(1024).decode('utf-8')
print("Server response:")
print(response)

s.close()