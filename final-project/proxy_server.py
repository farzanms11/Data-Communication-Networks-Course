"""Local HTTP forward proxy with a Tkinter monitoring interface.

The server deliberately binds to 127.0.0.1 and supports plain HTTP traffic;
HTTPS CONNECT tunnelling is outside the scope of the course implementation.
"""

import queue
import re
import shutil
import socket
import subprocess
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from urllib.parse import urlsplit, urlunsplit
import platform


class ProxyServer:
    """Threaded local HTTP proxy, URL blocklist, bounded response cache."""

    MAX_HEADERS = 65536
    MAX_BODY = 8 * 1024 * 1024
    MAX_CACHE = 2 * 1024 * 1024
    SOCKET_TIMEOUT = 10

    def __init__(self, port=8080):
        self.port = port
        self.running = False
        self.server_socket = None
        self.listener_thread = None
        self.cache = {}  # request URL -> (expiry_timestamp, complete raw response)
        self.blocked_urls = set()
        self.lock = threading.Lock()
        self.log_callback = None
        self.request_count = 0
        self.blocked_count = 0
        self.cache_hits = 0

    def log(self, message, tag="info"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        if self.log_callback:
            self.log_callback(formatted, tag)
        print(formatted)

    def start(self):
        if self.running:
            return False
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            listener.bind(("127.0.0.1", self.port))
            listener.listen(16)
            listener.settimeout(0.3)
        except Exception:
            listener.close()
            raise
        self.server_socket = listener
        self.port = listener.getsockname()[1]  # Allow port 0 for integration tests.
        self.running = True
        self.listener_thread = threading.Thread(target=self.accept_connections, daemon=True)
        self.listener_thread.start()
        self.log(f"Listening on 127.0.0.1:{self.port}", "success")
        return True

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        if self.listener_thread and self.listener_thread != threading.current_thread():
            self.listener_thread.join(timeout=1.0)
        self.log("Proxy stopped")

    def accept_connections(self):
        listener = self.server_socket
        while self.running:
            try:
                client, addr = listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with self.lock:
                self.request_count += 1
                request_number = self.request_count
            threading.Thread(
                target=self.handle_client, args=(client, addr, request_number), daemon=True
            ).start()

    @staticmethod
    def parse_request(header_bytes):
        lines = header_bytes.decode("iso-8859-1").split("\r\n")
        tokens = lines[0].split()
        if len(tokens) != 3 or not tokens[2].startswith("HTTP/"):
            raise ValueError("Malformed HTTP request line")
        method, target, version = tokens
        headers = {}
        for line in lines[1:]:
            if not line:
                break
            if ":" not in line:
                raise ValueError("Malformed HTTP header")
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()
        return method.upper(), target, version, headers

    @staticmethod
    def send_error(client, status, reason, message):
        body = (message + "\n").encode("utf-8")
        response = (
            f"HTTP/1.1 {status} {reason}\r\nContent-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n"
        ).encode("ascii") + body
        try:
            client.sendall(response)
        except OSError:
            pass

    def _read_request(self, client):
        data = bytearray()
        while b"\r\n\r\n" not in data:
            part = client.recv(8192)
            if not part:
                raise ValueError("Connection closed before request headers")
            data.extend(part)
            if len(data) > self.MAX_HEADERS:
                raise ValueError("Request headers too large")
        head, initial_body = bytes(data).split(b"\r\n\r\n", 1)
        method, target, version, headers = self.parse_request(head)
        if "transfer-encoding" in headers:
            raise NotImplementedError("Chunked request bodies are not supported")
        try:
            body_length = int(headers.get("content-length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid Content-Length") from exc
        if body_length < 0 or body_length > self.MAX_BODY or len(initial_body) > body_length:
            raise ValueError("Invalid or excessive request body")
        body = bytearray(initial_body)
        while len(body) < body_length:
            chunk = client.recv(min(8192, body_length - len(body)))
            if not chunk:
                raise ValueError("Incomplete request body")
            body.extend(chunk)
        return method, target, version, headers, bytes(body)

    @staticmethod
    def _destination(target, headers):
        parsed = urlsplit(target)
        if parsed.scheme:
            if parsed.scheme.lower() != "http" or not parsed.hostname or parsed.username:
                raise ValueError("Only plain HTTP URLs are supported")
        else:
            host = headers.get("host", "")
            if not host or not target.startswith("/"):
                raise ValueError("Missing Host header or invalid request target")
            parsed = urlsplit("http://" + host + target)
        try:
            port = parsed.port or 80
        except ValueError as exc:
            raise ValueError("Invalid destination port") from exc
        if not 1 <= port <= 65535:
            raise ValueError("Invalid destination port")
        path = urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
        host_port = parsed.netloc
        canonical_url = urlunsplit(("http", host_port, parsed.path or "/", parsed.query, ""))
        return parsed.hostname, port, path, canonical_url, host_port

    def is_blocked(self, url):
        with self.lock:
            rules = tuple(self.blocked_urls)
        lowered = url.lower()
        return any(rule.lower() in lowered for rule in rules)

    def load_blocked_urls(self, filename):
        with open(filename, encoding="utf-8") as file:
            rules = {line.strip() for line in file if line.strip() and not line.lstrip().startswith("#")}
        with self.lock:
            self.blocked_urls = rules
        self.log(f"Loaded {len(rules)} blocked URL rules", "success")

    def clear_blocked_urls(self):
        with self.lock:
            self.blocked_urls.clear()
        self.log("Cleared blocked URL rules")

    def get_cached_url(self, url):
        with self.lock:
            entry = self.cache.get(url)
            if not entry:
                return None
            if entry[0] <= time.monotonic():
                del self.cache[url]
                return None
            return entry[1]

    def clear_cache(self):
        with self.lock:
            self.cache.clear()
        self.log("Cache cleared")

    @staticmethod
    def _cache_duration(header_bytes):
        """Cache only explicitly public HTTP 200 responses with a max-age value."""
        header_lines = header_bytes.decode("iso-8859-1", errors="replace").split("\r\n")
        if not header_lines[0].startswith(("HTTP/1.0 200", "HTTP/1.1 200")):
            return 0
        headers = {}
        for header in header_lines[1:]:
            if ":" in header:
                key, value = header.split(":", 1)
                headers[key.strip().lower()] = value.strip().lower()
        control = headers.get("cache-control", "")
        if "set-cookie" in headers or "vary" in headers or any(x in control for x in ("no-store", "private", "no-cache")):
            return 0
        if "public" not in control:
            return 0
        match = re.search(r"(?:^|,)\s*max-age\s*=\s*(\d+)", control)
        return min(int(match.group(1)), 3600) if match else 0

    def handle_client(self, client_socket, addr, request_number=0):
        sent_upstream_bytes = False
        try:
            client_socket.settimeout(self.SOCKET_TIMEOUT)
            method, target, version, headers, body = self._read_request(client_socket)
            if method == "CONNECT":
                self.send_error(client_socket, 501, "Not Implemented", "HTTPS CONNECT tunnelling is not supported")
                return
            if method not in {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"}:
                self.send_error(client_socket, 405, "Method Not Allowed", "Unsupported HTTP method")
                return
            hostname, port, path, url, authority = self._destination(target, headers)
            self.log(f"Request #{request_number}: {method} {url} from {addr[0]}", "request")
            if self.is_blocked(url):
                with self.lock:
                    self.blocked_count += 1
                self.send_error(client_socket, 403, "Forbidden", "Blocked by the local proxy URL filter")
                self.log(f"Blocked: {url}", "blocked")
                return
            cache_allowed = (method == "GET" and "authorization" not in headers
                             and "cookie" not in headers and "range" not in headers
                             and "no-cache" not in headers.get("cache-control", "").lower()
                             and "no-store" not in headers.get("cache-control", "").lower()
                             and "max-age=0" not in headers.get("cache-control", "").lower()
                             and "no-cache" not in headers.get("pragma", "").lower()
                             and not any(k.startswith("if-") for k in headers))
            if cache_allowed:
                cached = self.get_cached_url(url)
                if cached is not None:
                    with self.lock:
                        self.cache_hits += 1
                    client_socket.sendall(cached)
                    self.log(f"Cache hit: {url}", "cache")
                    return
            forward_headers = {k: v for k, v in headers.items()
                               if k not in {"proxy-connection", "connection", "keep-alive"}}
            forward_headers["host"] = authority
            forward_headers["connection"] = "close"
            head = (f"{method} {path} HTTP/1.1\r\n" +
                    "".join(f"{key}: {value}\r\n" for key, value in forward_headers.items()) +
                    "\r\n").encode("iso-8859-1")
            with socket.create_connection((hostname, port), timeout=self.SOCKET_TIMEOUT) as upstream:
                upstream.settimeout(self.SOCKET_TIMEOUT)
                upstream.sendall(head + body)
                header_buffer = bytearray()
                response_chunks = []
                cache_size = 0
                cache_duration = 0
                response_started = False
                while True:
                    chunk = upstream.recv(65536)
                    if not chunk:
                        break
                    if not response_started:
                        header_buffer.extend(chunk)
                        if len(header_buffer) > self.MAX_HEADERS:
                            raise ValueError("Upstream response headers too large")
                        if b"\r\n\r\n" not in header_buffer:
                            continue
                        chunk = bytes(header_buffer)
                        header_section = chunk.split(b"\r\n\r\n", 1)[0]
                        cache_duration = self._cache_duration(header_section)
                        response_started = True
                    client_socket.sendall(chunk)
                    sent_upstream_bytes = True
                    if cache_allowed and cache_duration and cache_size + len(chunk) <= self.MAX_CACHE:
                        response_chunks.append(chunk)
                        cache_size += len(chunk)
                    else:
                        cache_duration = 0
                        response_chunks.clear()
                if not response_started:
                    raise OSError("Upstream did not send a complete HTTP response")
            if cache_allowed and cache_duration and response_chunks:
                with self.lock:
                    self.cache[url] = (time.monotonic() + cache_duration, b"".join(response_chunks))
                self.log(f"Cached: {url}", "cache")
        except NotImplementedError as exc:
            self.send_error(client_socket, 501, "Not Implemented", str(exc))
            self.log(f"Unsupported request: {exc}", "error")
        except ValueError as exc:
            if not sent_upstream_bytes:
                self.send_error(client_socket, 400, "Bad Request", str(exc))
            self.log(f"Bad request: {exc}", "error")
        except (OSError, TimeoutError) as exc:
            if not sent_upstream_bytes:
                self.send_error(client_socket, 502, "Bad Gateway", "The upstream server could not be reached")
            self.log(f"Upstream/network error: {exc}", "error")
        finally:
            client_socket.close()

    def run_traceroute(self, host):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]{0,252}", host):
            return "Invalid hostname or IPv4 address."
        windows = platform.system().lower() == "windows"
        executable = "tracert" if windows else "traceroute"
        if not shutil.which(executable):
            return f"{executable} is not installed or is not in PATH."
        command = ([executable, "-d", "-h", "5", host] if windows
                   else [executable, "-n", "-m", "5", host])
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=20)
            return (result.stdout + "\n" + result.stderr).strip() or "No traceroute output."
        except subprocess.TimeoutExpired:
            return "Traceroute timed out after 20 seconds."


# HTTP Proxy Server GUI
class ProxyGUI:
    def __init__(self):
        self.proxy = ProxyServer()
        self._log_queue = queue.Queue()
        self.proxy.log_callback = self.log_message
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("HTTP Proxy Server")
        self.root.geometry("960x640")
        self.root.configure(bg="#1e1e2e")
        self.root.minsize(900, 600)
        
        # Configure styling
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        self.configure_styles()
        
        # Create widgets
        self.create_widgets()
        
        # Set app icon
        self.set_icon()
        
        # Set initial status color to red (disconnected)
        self.update_status_color()
        self.root.after(80, self._flush_log_queue)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def configure_styles(self):
        # Configure colors
        bg_color = "#1e1e2e"
        fg_color = "#cdd6f4"
        
        self.style.configure(".", background=bg_color, foreground=fg_color, font=("Inter", 10))
        self.style.configure("TFrame", background=bg_color)
        self.style.configure("TLabel", background=bg_color, foreground=fg_color)
        self.style.configure("TButton", background="#45475a", foreground=fg_color, borderwidth=1, focuscolor="#89b4fa", padding=6)
        self.style.map("TButton", background=[("active", "#5c5e7e"), ("pressed", "#313244")], foreground=[("active", fg_color)])
        self.style.configure("TEntry", fieldbackground="#313244", foreground=fg_color, insertcolor=fg_color, padding=5)
        self.style.configure("TCombobox", fieldbackground="#313244", foreground=fg_color)
        self.style.configure("TNotebook", background=bg_color, borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#313244", foreground=fg_color, padding=[10, 5], font=("Inter", 10, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", bg_color), ("active", "#45475a")], foreground=[("selected", "#89b4fa")])
        self.style.configure("Vertical.TScrollbar", background="#45475a", arrowcolor=fg_color)
        
        # Configure tags for log text
        self.log_tags = {
            "info": {"foreground": "#89b4fa"},
            "error": {"foreground": "#f38ba8"},
            "success": {"foreground": "#a6e3a1"},
            "request": {"foreground": "#cba6f7"},
            "cache": {"foreground": "#f9e2af"},
            "blocked": {"foreground": "#f38ba8"},
            "system": {"foreground": "#a6e3a1"}
        }
    
    def create_widgets(self):
        # Create header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        # Title
        title_label = ttk.Label(header_frame, text="HTTP Proxy Server", font=("Inter", 18, "bold"),foreground="#89b4fa")
        title_label.pack(side=tk.LEFT)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Control Tab
        control_tab = ttk.Frame(notebook)
        notebook.add(control_tab, text="⚙️ Control Panel")
        
        # Proxy Control Frame
        control_frame = ttk.LabelFrame(control_tab, text="Proxy Server Control", padding=15)
        control_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Port configuration
        port_frame = ttk.Frame(control_frame)
        port_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(port_frame, text="Proxy Port:").pack(side=tk.LEFT, padx=15)
        self.port_var = tk.StringVar(value="8080")
        port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=10, font=("Inter", 10))
        port_entry.pack(side=tk.LEFT, padx=15)
        
        # Buttons frame
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Proxy", command=self.start_proxy)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = ttk.Button(button_frame, text="Stop Proxy", command=self.stop_proxy, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Load Blocked URLs", command=self.load_blocked_urls).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Blocked URLs", command=self.clear_blocked_urls).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Cache", command=self.clear_cache).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Status: Not running")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Inter", 10, "bold"))
        self.status_label.pack(side=tk.LEFT)
        
        stats_frame = ttk.Frame(status_frame)
        stats_frame.pack(side=tk.RIGHT)
        
        ttk.Label(stats_frame, text="Requests:").pack(side=tk.LEFT, padx=(10, 2))
        self.request_count_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.request_count_var, foreground="#cba6f7").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(stats_frame, text="Blocked:").pack(side=tk.LEFT, padx=2)
        self.blocked_count_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.blocked_count_var, foreground="#f38ba8").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(stats_frame, text="Cache Hits:").pack(side=tk.LEFT, padx=2)
        self.cache_hits_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.cache_hits_var, foreground="#f9e2af").pack(side=tk.LEFT)
        
        # Traceroute Frame
        traceroute_frame = ttk.LabelFrame(control_tab, text="Traceroute Utility", padding=15)
        traceroute_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        ttk.Label(traceroute_frame, text="Host to trace:").pack(side=tk.LEFT, padx=(0, 10))
        self.trace_add = tk.StringVar(value="httpforever.com")
        trace_entry = ttk.Entry(traceroute_frame, textvariable=self.trace_add, width=30)
        trace_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Button(traceroute_frame, text="Run Traceroute", command=self.run_traceroute).pack(side=tk.LEFT)
        
        # Log Tab
        log_tab = ttk.Frame(notebook)
        notebook.add(log_tab, text="📝 Activity Log")
        
        # Log display
        log_frame = ttk.Frame(log_tab)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4",
                                                  font=("Consolas", 10),padx=10,pady=10,wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for log messages
        for tag, config in self.log_tags.items():
            self.log_text.tag_config(tag, **config)
        
        # Add welcome message
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, "HTTP Proxy Server - Activity Log\n", "system")
        self.log_text.insert(tk.END, "="*80 + "\n", "system")
        self.log_text.insert(tk.END, "• Click 'Start Proxy' to start the proxy\n", "info")
        self.log_text.insert(tk.END, "• Use the traceroute tool to diagnose network paths\n", "info")
        self.log_text.config(state=tk.DISABLED)
        
        # Create footer
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        ttk.Label(footer_frame, text="HTTP Proxy Server", foreground="#6c7086",font=("Inter", 9)).pack(side=tk.LEFT)
        ttk.Label(footer_frame, text="Status: Ready", foreground="#a6e3a1",font=("Inter", 9)).pack(side=tk.RIGHT)
    
    def update_status_color(self):
        if self.proxy.running:
            self.status_label.configure(foreground="#a6e3a1")  # Green when connected
        else:
            self.status_label.configure(foreground="#f38ba8")  # Red when disconnected
    
    def log(self, message, tag="info"):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
        
        # Update statistics
        self.request_count_var.set(str(self.proxy.request_count))
        self.blocked_count_var.set(str(self.proxy.blocked_count))
        self.cache_hits_var.set(str(self.proxy.cache_hits))
    
    def log_message(self, message, tag="info"):
        # Worker threads must not call Tkinter directly.
        self._log_queue.put((message, tag))

    def _flush_log_queue(self):
        try:
            while True:
                message, tag = self._log_queue.get_nowait()
                self.log(message, tag)
        except queue.Empty:
            pass
        self.root.after(80, self._flush_log_queue)

    def _on_close(self):
        self.proxy.stop()
        self.root.destroy()
    
    def start_proxy(self):
        try:
            port = int(self.port_var.get())
            if not (1024 <= port <= 65535):
                raise ValueError("Port must be between 1024 and 65535")
            
            self.proxy.port = port
            if self.proxy.start():
                self.status_var.set(f"Status: Running on port {port}")
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                self.log(f"Proxy started on port {port}", "success")
                self.update_status_color()
        except Exception as e:
            self.log(f"Failed to start proxy: {str(e)}", "error")
            messagebox.showerror("Error", f"Failed to start proxy:\n{str(e)}")
    
    def stop_proxy(self):
        self.proxy.stop()
        self.status_var.set("Status: Not running")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log("Proxy server stopped")
        self.update_status_color()
    
    def load_blocked_urls(self):
        filename = filedialog.askopenfilename(title="Select blocked URLs file", filetypes=[("Text files", "*.txt"),
                                                                                           ("All files", "*.*")])
        if filename:
            self.proxy.load_blocked_urls(filename)
            self.log(f"Loaded {len(self.proxy.blocked_urls)} blocked URLs", "success")
            self.log("Blocked URLs:")
            for i in self.proxy.blocked_urls:
                self.log(f"{i}")
            messagebox.showinfo("Success", f"Loaded {len(self.proxy.blocked_urls)} blocked URLs")
    
    def clear_blocked_urls(self):
        self.proxy.clear_blocked_urls()
        self.log("Cleared blocked URLs")
        messagebox.showinfo("Success", "Blocked URLs cleared!")
    
    def clear_cache(self):
        self.proxy.clear_cache()
        self.log("Cache cleared")
        messagebox.showinfo("Success", "Cache cleared!")
    
    def run_traceroute(self):
        host = self.trace_add.get().strip()
        if not host:
            messagebox.showwarning("Warning", "Please enter a hostname!!!")
            return
        
        self.log(f"Running traceroute to {host} ...")
        def worker():
            result = self.proxy.run_traceroute(host)
            self.log_message(result, "system")
        threading.Thread(target=worker, daemon=True).start()
    
    def set_icon(self):
        # Icon is optional and supported by Tk on Windows.
        icon = Path(__file__).resolve().parent / "proxy.ico"
        if platform.system().lower() == "windows" and icon.exists():
            try:
                self.root.iconbitmap(str(icon))
            except tk.TclError:
                pass


if __name__ == "__main__":
    proxy = ProxyGUI()
    proxy.root.mainloop()