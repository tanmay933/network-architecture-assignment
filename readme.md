# Network Architecture Assignment — Build a Calculator That Stays on the Line

**Author: Tanmay Mittal**

![Java](https://img.shields.io/badge/Java-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TCP](https://img.shields.io/badge/TCP-005571?style=for-the-badge)
![HTTP/1.1](https://img.shields.io/badge/HTTP%2F1.1-005571?style=for-the-badge)
![Networking](https://img.shields.io/badge/Computer%20Networking-6A1B9A?style=for-the-badge)
![Sockets](https://img.shields.io/badge/Socket%20Programming-2E7D32?style=for-the-badge)
![Binary Protocol](https://img.shields.io/badge/Binary%20Protocol-C62828?style=for-the-badge)
![Network Architecture](https://img.shields.io/badge/Network%20Architecture-1565C0?style=for-the-badge)

## Overview

This project implements two TCP-based network applications to demonstrate reliable message framing, persistent connections, and protocol design:

* **Part 1:** A persistent HTTP/1.1 calculator server using raw TCP sockets.
* **Part 2:** A custom binary protocol with an independent server (`bserve`) and client (`bcurl`).

The implementation focuses on correctly handling TCP streams, message boundaries, request/response framing, validation, and multiple requests over a single connection.

---

## Part 1 — HTTP/1.1 Calculator

A raw TCP server implementing a minimal HTTP/1.1 interface for arithmetic operations.

### Features

* TCP socket-based HTTP server
* HTTP/1.1 request parsing
* Persistent connections
* Multiple requests over the same TCP connection
* `Content-Length` based message framing
* Required HTTP status handling
* Arithmetic expression evaluation
* Request validation

### Running the server

```bash
cd part1
python3 calc_server.py 8080
```

The server listens on:

```text
localhost:8080
```

### Testing

Use the provided test client:

```bash
python3 test_client.py
```

The implementation demonstrates persistent HTTP communication rather than creating a new TCP connection for every request.

---

# Part 2 — Custom Binary Protocol

Part 2 implements a custom framed binary protocol over TCP.

It consists of:

```text
bserve  → Binary protocol server
bcurl   → Binary protocol client
SPEC.md → Protocol specification
```

### Protocol structure

Each frame contains a fixed **10-byte header** followed by the frame payload.

The protocol uses:

* Length field
* Frame type
* Flags
* Stream ID
* Header count
* Big-endian integer encoding

The protocol supports persistent TCP connections and multiple frames on the same connection.

### Supported request

A request contains a `:path` header identifying the requested resource.

Example:

```text
:path = /index.html
```

The server reads the requested file from the configured web root and returns an appropriate response.

### Running the server

From `part2/`:

```bash
./bserve ./www 9000
```

Expected output:

```text
bserve listening on port 9000
```

### Running the client

In another terminal:

```bash
cd part2
./bcurl -v localhost:9000/index.html
```

Example response:

```text
Hello from my binary protocol server!
```

The `-v` option displays the request and response frames as hexadecimal dumps.

---

## HTTP vs Binary Protocol

| Feature       | Part 1           | Part 2                 |
| ------------- | ---------------- | ---------------------- |
| Transport     | TCP              | TCP                    |
| Protocol      | HTTP/1.1         | Custom binary protocol |
| Framing       | `Content-Length` | Binary length field    |
| Header format | Text             | Binary                 |
| Connection    | Persistent       | Persistent             |
| Client        | Test client      | `bcurl`                |
| Server        | `calc_server.py` | `bserve`               |

---

## Error Handling

The implementations handle malformed and invalid requests according to their respective protocols.

Part 1 includes handling for cases such as:

* Missing `Host`
* Invalid arithmetic expressions
* Unsupported HTTP methods
* Unknown routes

Part 2 includes handling for:

* Invalid frames
* Invalid request headers
* Missing/invalid `:path`
* Missing files
* Unsupported frame types
* Path traversal attempts

Unknown frame types are skipped without terminating the connection.

---

## TCP Stream Handling

A key objective of this assignment is understanding that **TCP is a byte stream, not a message protocol**.

The implementation therefore does not assume that a single `recv()`/`read()` call corresponds to one complete protocol frame.

Part 2 handles:

* Partial reads
* Complete frame reconstruction
* Multiple frames on one connection
* Persistent communication

---

## Protocol Specification

The complete binary protocol definition is documented in:

```text
part2/SPEC.md
```

It describes the frame format, fields, request/response structure, and protocol behavior.

---

## Hexdump

An annotated request/response hexdump is provided in:

```text
part2/hexdump.txt
```

It demonstrates the actual bytes exchanged between `bcurl` and `bserve`, including the frame header, stream ID, headers, status, and response body.

---

## Project Structure

```text
network-architecture-assignment/
│
├── part1/
│   ├── calc_server.py
│   ├── test_client.py
│   └── README.md
│
├── part2/
│   ├── bserve
│   ├── bcurl
│   ├── SPEC.md
│   ├── hexdump.txt
│   └── www/
│       └── index.html
│
└── README.md
```

---

## Author

**Tanmay Mittal**