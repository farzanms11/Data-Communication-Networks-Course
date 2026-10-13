# HTTP Proxy Server

**Final Project · Data Communication Networks**  
**Farzan Aghaei · Sharif University of Technology**

A multithreaded HTTP forward proxy implemented in Python with a Tkinter desktop interface. The server accepts plain HTTP requests from a local browser or client, forwards them to the destination server, and relays the response to the client.

## Implementation

- **HTTP forwarding:** supports `GET`, `HEAD`, `POST`, `PUT`, `PATCH`, and `DELETE` with `Content-Length` request bodies; transfers complete binary and large responses.
- **Concurrent connections:** uses a listener thread and separate worker threads for client requests.
- **URL filtering:** blocks requests matching case-insensitive URL-substring rules loaded from a text file and returns HTTP 403.
- **Response caching:** stores eligible public HTTP 200 GET responses in memory, using the origin's `Cache-Control: public, max-age=...` directive. Cached responses expire and are limited to 2 MiB each.
- **Desktop interface:** controls proxy start/stop and port selection, shows request, blocked-request and cache-hit counters, and provides blocklist/cache controls and request logs.
- **Traceroute diagnostics:** runs the operating system's `tracert` (Windows) or `traceroute` (Linux/macOS), if available.

## Requirements and execution

Python 3.9 or newer with Tkinter. The application has no third-party Python dependencies.

From the repository root:

```bash
python final-project/proxy_server.py
```

Start the proxy in the application (default port `8080`). For Firefox, navigate to **Settings → General → Network Settings → Settings**, choose **Manual proxy configuration**, and set the **HTTP proxy** to `127.0.0.1` with port `8080`. Do not configure an HTTPS proxy for this application.

Alternatively, test with an HTTP URL:

```bash
curl --proxy http://127.0.0.1:8080 http://example.com/
```

Select **Load Blocked URLs** to load [`blocked_urls.txt`](blocked_urls.txt); the rules are not loaded automatically. **Clear Blocked URLs** and **Clear Cache** clear the respective in-memory state.

## Tests

Run from the repository root:

```bash
python -m unittest discover -s tests -v
```

The tests use a local HTTP server to check request forwarding, large and binary responses, POST bodies, public/private caching behavior, URL blocking, unsupported requests, and proxy restart.

## Scope

The server binds to `127.0.0.1` and is intended for local HTTP experiments. HTTPS `CONNECT` tunnelling and chunked request bodies are not supported. Cached data and active blocklist rules are not retained between application sessions.

The project report is available as [`Project_Report.pdf`](Project_Report.pdf).
