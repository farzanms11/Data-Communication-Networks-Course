"""End-to-end tests using only loopback HTTP servers (no Internet)."""
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import threading
import time
import unittest

MODULE_FILE = Path(__file__).resolve().parents[1] / 'final-project' / 'proxy_server.py'
spec = importlib.util.spec_from_file_location('proxy_server', MODULE_FILE)
proxy_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy_module)
ProxyServer = proxy_module.ProxyServer


class OriginHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *_):
        pass
    def do_GET(self):
        with self.server.count_lock:
            self.server.counts[self.path] = self.server.counts.get(self.path, 0) + 1
        if self.path == '/large':
            body = b'\x00\xff' + b'A' * 150000 + b'\x02end'
        elif self.path == '/cache':
            body = b'fresh-response'
        else:
            body = b'uncached'
        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', str(len(body)))
        if self.path == '/cache':
            self.send_header('Cache-Control', 'public, max-age=45')
        if self.path == '/private':
            self.send_header('Cache-Control', 'private, max-age=60')
        self.end_headers()
        self.wfile.write(body)
    def do_POST(self):
        size = int(self.headers.get('Content-Length','0'))
        body = self.rfile.read(size)
        self.send_response(200)
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class ProxyIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.origin = ThreadingHTTPServer(('127.0.0.1',0),OriginHandler)
        cls.origin.counts = {}
        cls.origin.count_lock = threading.Lock()
        cls.origin_worker = threading.Thread(target=cls.origin.serve_forever,daemon=True)
        cls.origin_worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.origin.shutdown()
        cls.origin.server_close()
        cls.origin_worker.join(timeout=2)

    def setUp(self):
        self.proxy = ProxyServer(port=0)
        self.proxy.log_callback = lambda *_: None
        self.proxy.start()

    def tearDown(self):
        self.proxy.stop()

    def request(self,path,method='GET',body=b'',extra_headers=None):
        host=f'127.0.0.1:{self.origin.server_address[1]}'
        lines=[f'{method} http://{host}{path} HTTP/1.1',f'Host: {host}','Connection: close']
        for k,v in (extra_headers or {}).items():lines.append(f'{k}: {v}')
        if body:lines.append(f'Content-Length: {len(body)}')
        request=('\r\n'.join(lines)+'\r\n\r\n').encode('ascii')+body
        with socket.create_connection(('127.0.0.1',self.proxy.port),timeout=5) as s:
            s.settimeout(10)
            s.sendall(request)
            pieces=[]
            while True:
                p=s.recv(65536)
                if not p:break
                pieces.append(p)
        return b''.join(pieces)

    def test_large_binary_response_is_complete(self):
        response = self.request('/large')
        self.assertIn(b'HTTP/1.1 200',response.split(b'\r\n',1)[0])
        self.assertEqual(response.split(b'\r\n\r\n',1)[1],b'\x00\xff'+b'A'*150000+b'\x02end')

    def test_explicit_public_response_is_cached(self):
        with self.origin.count_lock:
            before=self.origin.counts.get('/cache',0)
        first=self.request('/cache')
        second=self.request('/cache')
        self.assertEqual(first,second)
        self.assertEqual(self.proxy.cache_hits,1)
        with self.origin.count_lock:
            self.assertEqual(self.origin.counts.get('/cache',0),before+1)

    def test_cache_is_cleared(self):
        self.request('/cache')
        self.proxy.clear_cache()
        self.assertEqual(self.proxy.cache,{})

    def test_private_response_is_not_cached(self):
        self.request('/private');self.request('/private')
        self.assertEqual(self.proxy.cache_hits,0)

    def test_blocklist_and_error_response(self):
        self.proxy.blocked_urls={'/large'}
        response=self.request('/large')
        self.assertIn(b'403 Forbidden',response)
        self.assertEqual(self.proxy.blocked_count,1)

    def test_post_body_forwarded_without_corruption(self):
        body=b'hello' * 5000 + b'\x00\xff'
        response=self.request('/echo','POST',body)
        self.assertIn(b'200',response.split(b'\r\n',1)[0])
        self.assertEqual(response.split(b'\r\n\r\n',1)[1],body)

    def test_https_connect_is_explicitly_rejected(self):
        response=self.request('/','CONNECT')
        self.assertIn(b'501 Not Implemented',response)

    def test_malformed_scheme_is_rejected(self):
        host='127.0.0.1:80'
        payload=b'GET https://'+host.encode()+b'/ HTTP/1.1\r\nHost: '+host.encode()+b'\r\n\r\n'
        with socket.create_connection(('127.0.0.1',self.proxy.port),timeout=5) as s:
            s.sendall(payload)
            response=s.recv(4096)
        self.assertIn(b'400 Bad Request',response)

    def test_server_can_stop_and_restart(self):
        port=self.proxy.port
        self.proxy.stop()
        self.proxy.port=port
        self.assertTrue(self.proxy.start())
        self.assertFalse(self.proxy.start())


if __name__=='__main__':
    unittest.main()
