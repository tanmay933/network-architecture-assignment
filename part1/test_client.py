#!/usr/bin/env python3

import socket


HOST = "127.0.0.1"
PORT = 8080


def read_response(sock):
    data = b""

    while b"\r\n\r\n" not in data:
        chunk = sock.recv(4096)

        if not chunk:
            return None

        data += chunk

    header_end = data.find(b"\r\n\r\n")
    headers = data[:header_end].decode("iso-8859-1")
    body_start = header_end + 4

    content_length = 0

    for line in headers.split("\r\n")[1:]:
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())

    while len(data) - body_start < content_length:
        chunk = sock.recv(4096)

        if not chunk:
            break

        data += chunk

    body = data[body_start:body_start + content_length]

    return headers, body.decode("utf-8", errors="replace")


def send_request(sock, request):
    print(">>>", request.split("\r\n")[0])

    sock.sendall(request.encode("ascii"))

    result = read_response(sock)

    if result is None:
        print("No response")
        return

    headers, body = result

    print(headers.split("\r\n")[0])
    print(body, end="")
    print("-" * 40)


# One persistent TCP connection
with socket.create_connection((HOST, PORT)) as sock:

    send_request(
        sock,
        "GET /add?a=2&b=3 HTTP/1.1\r\nHost: localhost\r\n\r\n"
    )

    send_request(
        sock,
        "GET /sub?a=10&b=4 HTTP/1.1\r\nHost: localhost\r\n\r\n"
    )

    send_request(
        sock,
        "GET /mul?a=6&b=7 HTTP/1.1\r\nHost: localhost\r\n\r\n"
    )

    send_request(
        sock,
        "GET /div?a=9&b=3 HTTP/1.1\r\nHost: localhost\r\n\r\n"
    )

    send_request(
        sock,
        "GET /div?a=1&b=0 HTTP/1.1\r\nHost: localhost\r\n\r\n"
    )

    send_request(
        sock,
        "GET /add?a=x&b=3 HTTP/1.1\r\nHost: localhost\r\n\r\n"
    )

    send_request(
        sock,
        "GET /pow?a=2&b=8 HTTP/1.1\r\nHost: localhost\r\n\r\n"
    )

    send_request(
        sock,
        "POST /add HTTP/1.1\r\nHost: localhost\r\n\r\n"
    )

    print("Connection still open after 8 requests.")


# Missing Host must return 400
with socket.create_connection((HOST, PORT)) as sock:

    send_request(
        sock,
        "GET /add?a=2&b=3 HTTP/1.1\r\n\r\n"
    )