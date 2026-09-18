#!/usr/bin/env python3

import socket
import sys
from urllib.parse import urlsplit, parse_qs


HOST = "0.0.0.0"
PORT = 8080

MAX_HEADER_BYTES = 8192
MAX_CONTENT_LENGTH = 1024


def make_response(status_code, body):
    reason = {
        200: "OK",
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
    }[status_code]

    body_bytes = body.encode("utf-8")

    response = (
        f"HTTP/1.1 {status_code} {reason}\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        f"Content-Type: text/plain\r\n"
        f"Connection: keep-alive\r\n"
        f"\r\n"
    ).encode("ascii") + body_bytes

    return response


def parse_request(data):
    header_end = data.find(b"\r\n\r\n")

    if header_end == -1:
        if len(data) > MAX_HEADER_BYTES:
            return None, data, "too_large"
        return None, data, "incomplete"

    header_block = data[:header_end]
    remaining = data[header_end + 4:]

    if len(header_block) > MAX_HEADER_BYTES:
        return None, remaining, "too_large"

    try:
        text = header_block.decode("iso-8859-1")
    except UnicodeDecodeError:
        return None, remaining, "bad"

    lines = text.split("\r\n")

    if not lines or len(lines) == 0:
        return None, remaining, "bad"

    request_line = lines[0].split(" ")

    if len(request_line) != 3:
        return None, remaining, "bad"

    method, target, version = request_line

    if version != "HTTP/1.1":
        return None, remaining, "bad"

    headers = {}

    for line in lines[1:]:
        if ":" not in line:
            return None, remaining, "bad"

        name, value = line.split(":", 1)
        name = name.strip().lower()
        value = value.strip()

        if not name:
            return None, remaining, "bad"

        if name in headers:
            headers[name] += ", " + value
        else:
            headers[name] = value

    if "host" not in headers:
        return None, remaining, "bad"

    if "transfer-encoding" in headers:
        return None, remaining, "bad"

    content_length = 0

    if "content-length" in headers:
        value = headers["content-length"]

        try:
            content_length = int(value)
        except ValueError:
            return None, remaining, "bad"

        if content_length < 0 or content_length > MAX_CONTENT_LENGTH:
            return None, remaining, "bad"

    if len(remaining) < content_length:
        return None, data, "incomplete"

    body = remaining[:content_length]
    leftover = remaining[content_length:]

    return {
        "method": method,
        "target": target,
        "version": version,
        "headers": headers,
        "body": body,
    }, leftover, "ok"


def calculate(method, target):
    if method != "GET":
        return 405, "Method Not Allowed\n"

    parsed = urlsplit(target)

    path = parsed.path
    query = parse_qs(parsed.query, keep_blank_values=True)

    if path not in ("/add", "/sub", "/mul", "/div"):
        return 404, "Not Found\n"

    if "a" not in query or "b" not in query:
        return 400, "Bad Request\n"

    if len(query["a"]) != 1 or len(query["b"]) != 1:
        return 400, "Bad Request\n"

    a_text = query["a"][0]
    b_text = query["b"][0]

    try:
        a = int(a_text)
        b = int(b_text)
    except (ValueError, OverflowError):
        return 400, "Bad Request\n"

    if path == "/add":
        result = a + b

    elif path == "/sub":
        result = a - b

    elif path == "/mul":
        result = a * b

    else:
        if b == 0:
            return 400, "Bad Request\n"

        if a % b != 0:
            return 200, f"{a / b}\n"

        result = a // b

    return 200, f"{result}\n"


def handle_client(conn):
    buffer = b""

    while True:
        try:
            request, buffer, status = parse_request(buffer)

            if status == "incomplete":
                chunk = conn.recv(4096)

                if not chunk:
                    break

                buffer += chunk
                continue

            if status != "ok":
                conn.sendall(make_response(400, "Bad Request\n"))
                break

            status_code, body = calculate(
                request["method"],
                request["target"]
            )

            conn.sendall(make_response(status_code, body))

        except (ConnectionResetError, BrokenPipeError):
            break


def main():
    global PORT

    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))
    server.listen(10)

    print(f"Calculator server listening on port {PORT}")

    while True:
        conn, address = server.accept()

        print(f"Connection from {address}")

        try:
            handle_client(conn)
        finally:
            conn.close()


if __name__ == "__main__":
    main()
