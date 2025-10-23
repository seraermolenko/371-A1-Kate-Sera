import socket
import os 
import time
from email.utils import formatdate, parsedate_to_datetime

# testing
# 200 
# curl -i http://127.0.0.1:8080/test.html

# 304
# (to check last mod date of test and sjut if needed): stat -f "%Sm" -t "%a, %d %b %Y %H:%M:%S GMT" test.html
# ensure you disable cache (in devtools network for chrome) and also Empty Cache and Hard Reload (press n hold reload)
# curl -i http://127.0.0.1:8080/test.html --header "If-Modified-Since: Wed, 22 Oct 2025 16:00:00 GMT"

# 403
# u gotta create a secret file and change its permisions cuz git wont let me push w it (chmod 000 teehee.txt)
# I just added a dummy teehee file with 644 so that I could push (chmod 644 teehee.txt)
# curl -i http://127.0.0.1:8080/teehee.txt

# 404 
# curl -i http://127.0.0.1:8080/doesnotexist.html
# 505 
# curl -1 "http://127.0.0.1:8080/test.html?v=2"

HOST = "127.0.0.1" 
PORT = 8080  
WEB_ROOT = "."  

STATUS_MESSAGES = {
    200: "OK",
    304: "Not Modified",
    403: "Forbidden",
    404: "Not Found",
    505: "HTTP Version Not Supported",
}

def build_response(code, body=b"", content_type="text/plain"):
    reason = STATUS_MESSAGES[code]
    headers = [
        f"HTTP/1.1 {code} {reason}",
        f"Content-Length: {len(body)}",
        f"Date: {formatdate(time.time(), usegmt=True)}",
        f"Content-Type: {content_type}",
        "Cache-Control: no-cache", 
        "Connection: close",
        "",
        ""
    ]
    return "\r\n".join(headers).encode() + body

def handle_client(connection):

    # Data is in binary ("socket communication is binary") so we gotta decode, and "receives up to 1024 bytes of data from the client"
    # Decode converts it to UTF-8
    request = connection.recv(1024).decode()
    if not request:
        return

    # Parsing GET /file HTTP/x.x
    request_line = request.split("\r\n")[0]
    parts = request_line.split(" ")
    if len(parts) != 3:
        return
    method, path, version = parts

    if path == "/": # for when running python script it takes u to http without the test file/if going thru browser, the curl commands above r chillin w/o this tho
        path = "/test.html"

    if "?v=2" in path:
        version = "HTTP/2.0"

    if version != "HTTP/1.1":
        connection.sendall(build_response(505, b" Error 505: HTTP Version Not Supported"))
        return

    file_path = os.path.join(WEB_ROOT, path.lstrip("/"))

    if not os.path.exists(file_path):
        connection.sendall(build_response(404, b"Error 404: Not Found"))
        return

    if not os.access(file_path, os.R_OK):
        connection.sendall(build_response(403, b"Error 403: Forbidden"))
        return

    headers = request.split("\r\n")[1:]
    print("headers:")
    print(headers)
    if_mod_since_header = None
    for h in headers:
        if h.lower().startswith("if-modified-since:"):
            if_mod_since_header = h.split(":", 1)[1].strip()
            break
    print("if_mod_since_header:")
    print(if_mod_since_header)

    last_modified = os.path.getmtime(file_path)

    print("last_modified:")
    print(last_modified)

    if if_mod_since_header:
        if_mod_since_dt = parsedate_to_datetime(if_mod_since_header)

        if if_mod_since_dt >= parsedate_to_datetime(formatdate(last_modified, usegmt=True)):
            connection.sendall(build_response(304))
            return


    with open(file_path, "rb") as f: # read binary (rb)
        content = f.read()
    connection.sendall(build_response(200, content, "text/html"))


    connection.close()

def run():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # server socket
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"Serving on http://{HOST}:{PORT}")


        while True: # server always running
            client, _ = s.accept() # connection socket (for each time a clinet connects and is closed in handle lclient pwhen they are done)

            # connection socket bettwen client and server
            handle_client(client)

if __name__ == "__main__":
    run()