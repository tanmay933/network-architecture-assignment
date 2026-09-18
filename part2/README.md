# Part 2 — Binary File Transfer Protocol

## Overview

Part 2 implements a custom binary protocol over a persistent TCP connection.

The project contains two independent programs:

- `bserve` — binary protocol file server
- `bcurl` — binary protocol client

The protocol is defined completely in [`SPEC.md`](./SPEC.md).

## Project Structure

```text
part2/
├── bserve
├── bcurl
├── SPEC.md
├── README.md
├── hexdump.txt
└── www/
    └── index.html
```

## Protocol

Every frame contains a fixed 10-byte header:

| Field        |    Size |
| ------------ | ------: |
| Length       | 3 bytes |
| Type         |  1 byte |
| Flags        |  1 byte |
| Stream ID    | 4 bytes |
| Header Count |  1 byte |

All multi-byte integers use big-endian byte order.

### Frame Types

| Type     |  Value | Meaning             |
| -------- | -----: | ------------------- |
| REQUEST  | `0x01` | Client file request |
| RESPONSE | `0x02` | Server response     |

Unknown frame types are skipped using the declared frame length, allowing the connection to continue.

## Request

A request contains a `:path` header.

Example:

```text
:path = /index.html
```

The request uses a non-zero Stream ID and has no payload.

## Response

A successful response contains:

```text
:status = 200
content-length = <file size>
```

The payload contains the raw file bytes.

For errors:

* `400` — malformed or invalid request
* `404` — requested file does not exist

## Persistent TCP

The protocol runs directly over TCP.

The implementation handles:

* partial TCP reads
* complete frames arriving across multiple reads
* multiple frames on the same connection
* persistent connections
* unknown frame types without terminating the connection

A test confirmed that an unknown frame can be skipped and a subsequent request on the same TCP connection is still processed successfully.

## File Safety

Requested paths are resolved relative to the configured web root.

Path traversal attempts such as:

```text
/../index.html
```

are rejected with:

```text
400 Bad Request
```

## Running the Server

From `part2`:

```bash
./bserve ./www 9000
```

## Running the Client

Request an existing file:

```bash
./bcurl localhost:9000/index.html
```

Verbose mode displays the hexadecimal representation of the request and response frames:

```bash
./bcurl -v localhost:9000/index.html
```

The response body is written to standard output.

## Tested Behavior

### Existing File

```bash
./bcurl -v localhost:9000/index.html
```

Result:

```text
200
Hello from my binary protocol server!
```

### Missing File

```bash
./bcurl -v localhost:9000/missing.html
```

Result:

```text
404 Not Found
```

### Invalid Path

```bash
./bcurl -v localhost:9000/../index.html
```

Result:

```text
400 Bad Request
```

### Unknown Frame

An unknown frame type was sent before a valid request.

Result:

```text
Unknown frame skipped: YES
Second request received: YES
Response status: 200
TCP connection remained usable: YES
```

## Hexdump

The complete hexadecimal request and response for `/index.html`, with field-by-field annotations, are documented in [`hexdump.txt`](./hexdump.txt).

## Independent Implementations

`bserve` and `bcurl` implement the protocol independently.

They do not share a protocol implementation module. Both implementations use
`SPEC.md` as the protocol contract.