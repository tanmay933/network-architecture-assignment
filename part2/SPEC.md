# Binary File Transfer Protocol Specification

## 1. Overview

This protocol transfers files over a persistent TCP connection. It has two
independent programs:

- `bserve` — server that serves files below a configured root directory.
- `bcurl` — client that requests files.

The specification is the only protocol contract shared by the implementations.
All multi-byte integers use big-endian byte order.

## 2. Frame Format

Every frame starts with a fixed 10-byte header:

| Field | Size | Meaning |
|---|---:|---|
| Length | 3 bytes | Bytes following this fixed header |
| Type | 1 byte | Frame type |
| Flags | 1 byte | Protocol flags |
| Stream ID | 4 bytes | Unsigned stream identifier |
| Header Count | 1 byte | Number of encoded headers |

`Length` includes the encoded headers and payload, but not the 10-byte fixed
header. Its maximum value is `0xFFFFFF` (16,777,215).

Frame types:

| Type | Value | Meaning |
|---|---:|---|
| REQUEST | `0x01` | Client file request |
| RESPONSE | `0x02` | Server response |

An unknown frame type MUST be skipped completely and processing MUST continue
with the next frame.

## 3. Flags and Streams

The current protocol defines no flags; normal frames use `Flags = 0x00`.
Unknown flag bits are ignored.

Stream ID `0` is reserved. The client starts at stream ID `1` and uses a new
positive ID for each request. The server copies the request stream ID into the
response.

## 4. Header Encoding

Each header is encoded as:

```text
1 byte   header-name index
2 bytes  value length
N bytes  UTF-8 value
```

Static header names are:

| Index | Name |
|---|---|
| `0x01` | `:path` |
| `0x02` | `:status` |
| `0x03` | `content-type` |
| `0x04` | `content-length` |
| `0x05` | `server` |
| `0x06` | `error` |
| `0x07` | `host` |
| `0x08` | `file-name` |
| `0x09` | `request-id` |
| `0x0A` | `connection` |

`0xFF` means a literal name. It is followed by one byte for name length, the
name bytes, two bytes for value length, and the UTF-8 value.

Header Count is one byte (maximum 255). A header value is at most 65,535 bytes.

## 5. REQUEST

A REQUEST has `Type = 0x01`, no payload, and exactly one `:path` header.

Example:

```text
:path = /index.html
```

The path MUST begin with `/`, is interpreted relative to the configured web
root, and MUST NOT escape that root. Absolute filesystem paths and traversal
such as `/../index.html` are invalid.

## 6. RESPONSE

A successful response has `Type = 0x02` and contains the request's Stream ID.

For an existing file:

```text
:status = 200
content-length = <file size>
```

The payload is the raw file bytes.

For a missing file:

```text
:status = 404
error = Not Found
```

For a malformed or invalid request:

```text
:status = 400
error = Bad Request
```

The 400 and 404 responses have empty payloads.

## 7. TCP and Error Handling

TCP is a byte stream. Implementations MUST handle:

- a frame split across multiple reads;
- multiple frames received in one read;
- multiple frames on one persistent connection.

The server keeps the connection open after successfully processing a request.

A malformed frame is one that cannot be safely decoded, such as a truncated
header/body, invalid header encoding, invalid request structure, missing
`:path`, invalid path, or an oversized value. Such a request receives
`400 Bad Request`. If synchronization cannot safely continue, the connection
may then be closed.

For an unknown frame type, the receiver MUST read the complete declared frame
body, discard it without decoding its headers, and continue. Thus:

```text
REQUEST → UNKNOWN → REQUEST
```

must allow both REQUEST frames to be processed.

## 8. Server and Client

Start the server with:

```bash
./bserve ./www 9000
```

A request for `/index.html` maps to `./www/index.html`. The server MUST prevent
the resolved path from escaping `./www`.

Run the client with:

```bash
./bcurl -v localhost:9000/index.html
```

The client opens one TCP connection, sends the binary request, reads the
response, writes a successful body to stdout, and does not open a second
connection. With `-v`, it prints hexadecimal frame data. It exits non-zero
for `4xx` or `5xx` responses.

## 9. Field-Width Design

The fixed header is deliberately similar to HTTP/2:

- **Length:** 3 bytes, matching HTTP/2's 24-bit length field.
- **Type:** 1 byte.
- **Flags:** 1 byte.
- **Stream ID:** 4 bytes.
- **Header Count:** 1 byte.

HTTP/2 uses a 31-bit stream identifier; this protocol uses the full 32-bit
field for simpler encoding while retaining a compact fixed header.

## 10. Example

A request for `/index.html` is:

```text
Type = REQUEST
Flags = 0
Stream ID = 1
:path = /index.html
Payload = empty
```

A successful response is:

```text
Type = RESPONSE
Flags = 0
Stream ID = 1
:status = 200
content-length = <file size>
Payload = raw file bytes
```

A complete annotated request and response are provided in `hexdump.txt`.