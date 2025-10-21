import socket

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 8080  

STATUS_MESSAGES = {
    200: "OK",
    304: "Not Modified",
    403: "Forbidden",
    404: "Not Found",
    505: "HTTP Version Not Supported",
}

def build_response(status_code, body=b"", content_type="text/plain"):
    reason = STATUS_MESSAGES[status_code]
    headers = [
        f"HTTP/1.1 {status_code} {reason}",
        f"Content-Length: {len(body)}",
        f"Content-Type: {content_type}",
        "Connection: close",
        "",
        ""
    ]
    return "\r\n".join(headers).encode() + body

def handle_client(client):
    try:
        request = client.recv(1024).decode()
        if not request:
            return

        # Parse request line: "GET /file.html HTTP/1.1"
        request_line = request.split("\r\n")[0]
        method, path, _ = request_line.split()

        if method != "GET":
            response = build_response(405, b"Method Not Allowed")
            client.sendall(response)
            return


        if path == "/":
            path = "/index.html"
        file_path = os.path.join(WEB_ROOT, path.lstrip("/"))

        if not os.path.exists(file_path):
            response = build_response(404, b"Not Found")
        elif not os.path.isfile(file_path):
            response = build_response(403, b"Forbidden")
        else:
            with open(file_path, "rb") as f:
                content = f.read()
            response = build_response(200, content, "text/html")

        client.sendall(response)
    except Exception as e:
        error_msg = f"Internal Server Error: {e}".encode()
        client.sendall(build_response(500, error_msg))
    finally:
        client.close()

def run():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"Serving on http://{HOST}:{PORT}")
        while True:
            client, addr = s.accept()
            handle_client(client)

if __name__ == "__main__":
    run()
