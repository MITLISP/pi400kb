"""Memory-mapped shared storage plus a localhost HTTP listener exposing it."""
import ctypes, json, mmap, os, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate.bin")
SIZE = 4096
HDR = 8  # first 8 bytes: little-endian length of payload

def open_substrate():
    with open(PATH, "a+b") as f:
        if os.path.getsize(PATH) < SIZE:
            f.truncate(SIZE)
    fd = os.open(PATH, os.O_RDWR)
    mm = mmap.mmap(fd, SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
    os.close(fd)
    return mm

def address_of(mm):
    buf = (ctypes.c_char * len(mm)).from_buffer(mm)
    addr = ctypes.addressof(buf)
    del buf
    return addr

def write(mm, data: bytes):
    data = data[: SIZE - HDR]
    mm[HDR:HDR + len(data)] = data
    mm[0:HDR] = len(data).to_bytes(HDR, "little")
    mm.flush()

def read(mm) -> bytes:
    n = int.from_bytes(mm[0:HDR], "little")
    return bytes(mm[HDR:HDR + n])

def make_listener(mm, lock, port=0):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            with lock: body = read(mm)
            self.send_response(200); self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers(); self.wfile.write(body)
        def do_POST(self):
            data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            with lock: write(mm, data)
            self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
