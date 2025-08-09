import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
from datetime import datetime
import platform
import ctypes

# HTTP Proxy Server Core
class ProxyServer:
    def __init__(self, port=8080):
        self.port = port  # Listening port for proxy
        self.running = False  # Server state flag
        self.server_socket = None  # Server socket
        self.cache = {}  # Cache storage
        self.blocked_urls = set()  # URLs to block
        self.lock = threading.Lock()  # Thread synchronization lock
        self.log_callback = None  # Logging callback function
        self.request_count = 0  # Total requests count
        self.blocked_count = 0  # Blocked requests count
        self.cache_hits = 0  # Cache hits count
    
    def log(self, message, tag="info"):
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{time}] {message}"
        
        if self.log_callback:
            self.log_callback(log_message, tag)
        
        print(log_message)
    
    def start(self):
        if self.running:
            return False
        self.running = True
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('localhost', self.port))
        self.server_socket.listen(8)
        
        self.log(f"Proxy server started on port {self.port}", "success")
        threading.Thread(target=self.accept_connections).start()
        return True
    
    def stop(self):
        if not self.running:
            return
        
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        self.log("Proxy server stopped")
    
    def accept_connections(self):
        while self.running:
            try:
                (client_socket, addr) = self.server_socket.accept()
                self.request_count += 1
                threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
                
            except OSError:
                break
    
    def parse_request(self, request):
        lines = request.split('\r\n')
        method, url, http_version = lines[0].split()
        
        headers = {}
        for line in lines[1:]:
            if not line:
                break
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key] = value
        
        return method, url, http_version, headers
    
    def handle_client(self, client_socket, addr):
        try:
            request = client_socket.recv(8192).decode()
            if not request:
                return
            
            # Parse HTTP request
            method, url, http_version, headers = self.parse_request(request)
            
            # Extract host
            host = headers.get('Host', '')
            if not host:
                return
            
            self.log(f"Request #{self.request_count}: {method} {url} from {addr[0]}", "request")
            
            # Check if URL is blocked
            if self.is_blocked(url):
                self.blocked_count += 1
                self.log(f"Blocked URL: {url}", "blocked")
                response = (
                    "HTTP/1.1 403 Forbidden\r\n"
                    "Content-Type: text/html\r\n\r\n"
                    "<html><body style='background: #1e1e2e; color: #cdd6f4; font-family: sans-serif; padding: 40px; text-align: center;'>"
                    "<h1 style='color: #f38ba8;'>403 Forbidden</h1>"
                    "<p style='font-size: 1.2em;'>This URL has been blocked by the proxy server.</p>"
                    "</body></html>"
                )
                client_socket.sendall(response.encode())
                return
            
            # Check cache
            cached_response = self.get_cached_url(url)
            if cached_response:
                self.cache_hits += 1
                self.log(f"Serving from cache: {url}", "cache")
                client_socket.sendall(cached_response)
                return
            
            # Forward request to destination server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.connect((host, 80))
                server_socket.sendall(request.encode())
                response = b""
                while True:
                    response = server_socket.recv(32768)
                    client_socket.sendall(response)
                    break
            
            # Cache the response
            if method == "GET" and (response.startswith(b"HTTP/1.1 200") or response.startswith(b"HTTP/1.1 304")):
                if url not in self.cache:
                    self.cache[url] = response
                    self.log(f"Cached: {url}", "cache")
        
        except Exception as e:
            self.log(f"Error: {str(e)}", "error")
        
        finally:
            client_socket.close()
    
    def is_blocked(self, url):
        with self.lock:
            return any(blocked_url in url for blocked_url in self.blocked_urls)
    
    def load_blocked_urls(self, filename):
        with open(filename) as f:
            with self.lock:
                self.blocked_urls = {line.strip() for line in f if line.strip()}
        self.log(f"Loaded {len(self.blocked_urls)} blocked URLs", "success")
        return
    
    def clear_blocked_urls(self):
        with self.lock:
            self.blocked_urls.clear()
        self.log("Cleared blocked URLs")
    
    def get_cached_url(self, url):
        with self.lock:
            return self.cache.get(url)
    
    def clear_cache(self):
        print(self.cache)
        with self.lock:
            self.cache.clear()
        self.log("Cache cleared")
    
    def run_traceroute(self, host):
        # Determine the correct command for the OS
        if platform.system().lower() == "windows":
            command = ['tracert', '-d', '-h', '5', host]
        else:
            command = ['traceroute', '-m', '5', host]
        
        result = subprocess.run(command, capture_output=True, text=True).stdout
        return result

# HTTP Proxy Server GUI
class ProxyGUI:
    def __init__(self):
        self.proxy = ProxyServer()
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
        self.log(message, tag)
    
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
        result = self.proxy.run_traceroute(host)
        messagebox.showinfo("Success", "Traceroute Completed!")
        
        # Display in log
        self.log(f"{result}", "system")
    
    def set_icon(self):
        myAppID = 'arbitrary string'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myAppID)
        self.root.iconbitmap("F:\\term6\data_network\project\\python\proxy.ico")

if __name__ == "__main__":
    proxy = ProxyGUI()
    proxy.root.mainloop()