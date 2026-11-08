"""Memory-mapped shared storage plus a localhost-only HTTP listener over it."""
import mmap, os, struct, threading, ctypes
from http.server import BaseHTTPRequestHandler, HTTPServer

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate.mmap")
SIZE = 4096
HDR = struct.Struct("<QI")  # sequence counter, payload length

class Substrate:
    def __init__(self, path=PATH, size=SIZE):
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        os.ftruncate(fd, size)
        self.mm = mmap.mmap(fd, size)
        os.close(fd)
        self.addr = ctypes.addressof(ctypes.c_char.from_buffer(self.mm))
        self.size = size
    def write(self, data: bytes):
        data = data[: self.size - HDR.size]
        seq, _ = HDR.unpack_from(self.mm, 0)
        self.mm[HDR.size:HDR.size + len(data)] = data
        HDR.pack_into(self.mm, 0, seq + 1, len(data))
    def read(self):
        seq, n = HDR.unpack_from(self.mm, 0)
        return seq, bytes(self.mm[HDR.size:HDR.size + n])

def make_handler(sub):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            seq, data = sub.read()
            self.send_response(200); self.end_headers()
            self.wfile.write(f"seq={seq} data={data.decode(errors='replace')}\n".encode())
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            sub.write(self.rfile.read(n))
            self.send_response(204); self.end_headers()
        def log_message(self, *a): pass
    return H

def start_listener(sub, port=0):
    srv = HTTPServer(("127.0.0.1", port), make_handler(sub))  # loopback only
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
