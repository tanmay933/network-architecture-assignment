# Binary File Transfer Protocol Specification

## 1. Overview

This document defines a small binary protocol used by `bserve` and `bcurl`
to request and transfer files over a persistent TCP connection.

The protocol provides basic file retrieval functionality:

- The client requests a file path.
- The server returns the file contents.
- The server returns `404` when the file does not exist.
- The server returns `400` when the request frame is malformed.
- TCP connections are persistent.
- Unknown frame types are skipped without closing the connection.

There is no dependency on HTTP.

All multi-byte integers use **network byte order (big-endian)**.

---

## 2. Frame Format

Every frame begins with a fixed 10-byte header.

| Offset | Size | Field | Description |
|---|---:|---|---|
| 0 | 3 bytes | Length | Unsigned 24-bit payload length |
| 3 | 1 byte | Type | Frame type |
| 4 | 1 byte | Flags | Frame flags |
| 5 | 4 bytes | Stream ID | Unsigned 32-bit stream identifier |
| 9 | 1 byte | Header Count | Number of encoded headers |
| 10 | variable | Headers | Encoded header fields |
| ... | variable | Payload | Frame payload |

The `Length` field counts every byte after the fixed 10-byte header,
including encoded headers and payload.

The maximum value representable by the 3-byte length field is:

```text
16,777,215 bytes
```

A frame whose declared length exceeds this value cannot be represented and is
invalid.

Implementations also impose a practical maximum frame size of 16 MiB.

---

## 3. Frame Types

| Type     |           Value | Meaning                        |
| -------- | --------------: | ------------------------------ |
| REQUEST  |          `0x01` | Client requests a file         |
| RESPONSE |          `0x02` | Server returns a file or error |
| Unknown  | Any other value | Receiver skips the frame       |

An unknown frame type does not cause the TCP connection to close.

The receiver uses the declared frame length to consume and skip the complete
unknown frame.

---

## 4. Flags

The current protocol defines no flags.

Normal frames use:

```text
Flags = 0x00
```

Receivers ignore unknown flag bits so that future protocol extensions do not
break existing implementations.

---

## 5. Stream ID

The Stream ID identifies a request/response pair.

The client starts with:

```text
Stream ID = 1
```

Each new request uses the next positive Stream ID.

The server copies the request Stream ID into the corresponding response.

The Stream ID is encoded as an unsigned 32-bit big-endian integer.

The value `0` is reserved and MUST NOT be used for normal request/response
frames.

---

## 6. Header Encoding

The fixed header contains a one-byte Header Count.

Each encoded header has this format:

|    Size | Field        |
| ------: | ------------ |
|  1 byte | Header Name  |
| 2 bytes | Value Length |
| N bytes | Header Value |

The Header Name byte is an index into the following static table:

|  Index | Header Name      |
| -----: | ---------------- |
| `0x01` | `:path`          |
| `0x02` | `:status`        |
| `0x03` | `content-type`   |
| `0x04` | `content-length` |
| `0x05` | `server`         |
| `0x06` | `error`          |
| `0x07` | `host`           |
| `0x08` | `file-name`      |
| `0x09` | `request-id`     |
| `0x0A` | `connection`     |

A Header Name value of:

```text
0xFF
```

means that the header name is encoded literally.

For a literal name:

```text
1 byte   = 0xFF
1 byte   = name length
N bytes  = header name
2 bytes  = value length
N bytes  = value
```

Header values are UTF-8 encoded.

The maximum header value length is 65,535 bytes.

The maximum number of headers in one frame is 255.

---

## 7. REQUEST Frame

A REQUEST frame has:

```text
Type = 0x01
```

The request must contain a `:path` header.

Example:

```text
:path = /index.html
```

The request payload is empty.

The path MUST:

* begin with `/`
* use UTF-8 encoding
* identify a file relative to the server's configured web root
* not escape the configured web root

Absolute filesystem paths are not permitted.

Path traversal using components such as:

```text
../
```

must be rejected.

---

## 8. RESPONSE Frame

A RESPONSE frame has:

```text
Type = 0x02
```

The response contains a `:status` header.

### Successful response

For an existing file:

```text
:status = 200
content-length = <file size>
```

The frame payload contains the raw file bytes.

### Missing file

For a file that does not exist:

```text
:status = 404
error = Not Found
```

The payload is empty.

### Malformed request

For a malformed frame or invalid request:

```text
:status = 400
error = Bad Request
```

The payload is empty.

---

## 9. TCP Connection Behaviour

The protocol runs directly over TCP.

TCP is a byte stream, therefore a single frame may be received in multiple
`recv()` calls.

Implementations MUST continue receiving until the complete frame has been
assembled.

Multiple frames may also arrive in a single `recv()` call.

Implementations MUST process every complete frame in the received byte stream.

The connection remains open after successfully processing a request.

The server closes the connection only when:

* the client closes the connection;
* an unrecoverable TCP error occurs; or
* a malformed frame makes continued parsing unsafe.

---

## 10. Unknown Frame Handling

If a receiver encounters an unknown frame type, it MUST:

1. Read the fixed header.
2. Read the declared frame length.
3. Consume the complete frame.
4. Ignore its contents.
5. Continue processing the next frame.

For example:

```text
REQUEST
UNKNOWN FRAME
REQUEST
```

must result in both REQUEST frames being processed.

The UNKNOWN FRAME must not terminate the TCP connection.

---

## 11. Malformed Frames

A frame is malformed when, for example:

* the frame header is incomplete;
* the declared frame length is invalid;
* the frame is truncated;
* a header field is truncated;
* a header value exceeds the allowed length;
* the Header Count cannot be decoded safely;
* a REQUEST does not contain `:path`;
* the path is invalid;
* a required response field cannot be encoded.

A malformed request results in:

```text
:status = 400
error = Bad Request
```

The server may close the connection after sending the `400` response if the
stream can no longer be safely synchronized.

---

## 12. File Server Command

The server is started with:

```bash
./bserve ./www 9000
```

The first argument is the web root.

The second argument is the TCP port.

For example:

```text
./www/index.html
```

is requested using:

```text
/index.html
```

The server must never allow a requested path to escape the configured web
root.

---

## 13. Client Command

The client is invoked using:

```bash
./bcurl -v localhost:9000/index.html
```

The client:

1. Opens one TCP connection.
2. Sends a REQUEST frame.
3. Reads the RESPONSE frame.
4. Writes the response body to standard output.
5. Keeps the connection available for additional requests.
6. With `-v`, displays the hexadecimal representation of transmitted and
   received frames.
7. Exits with a non-zero status for `4xx` or `5xx` responses.

---

## 14. Error Exit Status

The client exits with:

```text
0
```

for a successful `200` response.

The client exits with a non-zero status for:

```text
400
404
5xx
```

responses.

---

## 15. Field Width Design

The protocol uses a 3-byte length field rather than HTTP/2's 24-bit
length field by explicitly adopting the same 24-bit width.

The Type and Flags fields are one byte each, matching HTTP/2's one-byte
frame type and flags fields.

The Stream ID uses 4 bytes so that the protocol can represent stream
identifiers directly without requiring additional frame formats.

The one-byte Header Count limits a frame to at most 255 encoded headers.

These widths keep the fixed header small while providing sufficient range for
the file-transfer requirements of this assignment.

---

## 16. Example Request

A request for:

```text
/index.html
```

contains:

```text
Type       = 0x01
Flags      = 0x00
Stream ID  = 0x00000001
Header     = :path
Value      = /index.html
Payload    = empty
```

The exact hexadecimal representation is documented in `hexdump.txt`.

---

## 17. Example Response

For an existing `index.html`:

```text
Type       = 0x02
Flags      = 0x00
Stream ID  = 0x00000001
Headers:
    :status        = 200
    content-length = <length>
Payload:
    raw file bytes
```

The exact hexadecimal representation is documented in `hexdump.txt`.

---

## 18. Independent Implementations

`bserve` and `bcurl` are separate implementations.

Neither implementation depends on a shared protocol implementation file.

Both programs implement the protocol directly from this specification.

The specification therefore acts as the contract between the two programs.