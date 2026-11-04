"""Memory-mapped shared storage plus a localhost HTTP listener that reads it."""
import mmap, os, struct, threading, time, json
from http.server import BaseHTTPRequestHandler, HTTPServer

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate.mmap")
SIZE = 4096
HDR = struct.Struct("<QQ")  # seq counter, payload length
PORT = 8765

def open_substrate():
    fd = os.open(PATH, os.O_RDWR | os.O_CREAT)
    os.ftruncate(fd, SIZE)
    m = mmap.mmap(fd, SIZE)
    os.close(fd)
    return m

def write(m, data: bytes):
    seq, _ = HDR.unpack_from(m, 0)
    m[HDR.size:HDR.size + len(data)] = data
    HDR.pack_into(m, 0, seq + 1, len(data))

def read(m):
    seq, n = HDR.unpack_from(m, 0)
    return seq, bytes(m[HDR.size:HDR.size + n])

def address(m):
    import ctypes
    return hex(ctypes.addressof(ctypes.c_char.from_buffer(m)))

def serve(m, port=PORT):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            seq, data = read(m)
            body = json.dumps({"seq": seq, "data": data.decode(errors="replace")}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(body)
        def log_message(self, *a): pass
    srv = HTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

def baseline_rate(m, n=50000):
    """Measured write+read round-trip rate on this mapping (Hz)."""
    t = time.perf_counter()
    for i in range(n):
        write(m, b"x"); read(m)
    return n / (time.perf_counter() - t)
