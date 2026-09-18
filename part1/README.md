# Part 1 — Persistent HTTP/1.1 Calculator

## Overview

A raw TCP socket HTTP/1.1 calculator server implementing persistent connections.

No HTTP framework is used.

## Files

- `calc_server.py` — HTTP/1.1 calculator server
- `test_client.py` — raw-socket test client

## Run

Start the server:

```bash
cd part1
python3 calc_server.py 8080
```

## Usage

The server speaks HTTP/1.1 on a raw TCP socket and keeps the connection open
after each response. You can send multiple requests over the same TCP
connection without reconnecting.

### Example: two requests on one connection

Using `nc` (netcat):

```bash
printf 'GET /add?a=2&b=3 HTTP/1.1\r\nHost: localhost\r\n\r\nGET /mul?a=4&b=5 HTTP/1.1\r\nHost: localhost\r\n\r\n' | nc localhost 8080
```

Using the provided test client:

```bash
python3 test_client.py
```

The client:

1. Opens one TCP connection to `localhost:8080`.
2. Sends an HTTP/1.1 request for `/add?a=2&b=3`.
3. Reads the response.
4. Sends a second request for `/mul?a=4&b=5` on the **same** connection.
5. Reads the second response and prints both.

### Expected behavior

- Both responses come back on the same TCP connection.
- Each response has `Content-Length` and a blank line before the body.
- The server does not close the connection between requests.
- The connection closes only when the client closes it or sends
  `Connection: close`.