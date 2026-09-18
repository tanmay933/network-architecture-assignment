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