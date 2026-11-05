"""Memory-mapped substrate: a file-backed shared segment plus a localhost HTTP listener."""
import mmap, os, struct, threading, json
from http.server import BaseHTTPRequestHandler, HTTPServer

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate.bin")
SIZE = 4096
HDR = struct.Struct("<QI")  # sequence counter, payload length

def open_substrate():
    fd = os.open(PATH, os.O_RDWR | os.O_CREAT)
    os.ftruncate(fd, SIZE)
    mm = mmap.mmap(fd, SIZE)
    os.close(fd)
    return mm

def write(mm, payload: bytes):
    seq, _ = HDR.unpack_from(mm, 0)
    mm[HDR.size:HDR.size + len(payload)] = payload
    HDR.pack_into(mm, 0, seq + 1, len(payload))

def read(mm):
    seq, n = HDR.unpack_from(mm, 0)
    return seq, bytes(mm[HDR.size:HDR.size + n])

def make_listener(mm, port=0):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            seq, data = read(mm)
            body = json.dumps({"seq": seq, "data": data.decode(errors="replace")}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body)
        def log_message(self, *a): pass
    srv = HTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
