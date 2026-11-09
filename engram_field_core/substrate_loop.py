"""File-backed mmap segment + localhost HTTP listener that exposes it read-only."""
import mmap, os, struct, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate.mmap")
SIZE = 4096
HDR = struct.Struct("<QI")  # sequence counter, payload length

def open_segment():
    with open(PATH, "a+b") as f:
        f.truncate(SIZE)
    fd = os.open(PATH, os.O_RDWR)
    return mmap.mmap(fd, SIZE)

def write(mm, payload: bytes, seq: int):
    payload = payload[: SIZE - HDR.size]
    mm[HDR.size : HDR.size + len(payload)] = payload
    mm[: HDR.size] = HDR.pack(seq, len(payload))

def read(mm):
    seq, n = HDR.unpack(mm[: HDR.size])
    return seq, bytes(mm[HDR.size : HDR.size + n])

def address(mm):
    import ctypes
    return hex(ctypes.addressof(ctypes.c_char.from_buffer(mm)))

def serve(mm, port=0):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            seq, data = read(mm)
            body = json.dumps({"seq": seq, "payload": data.decode(errors="replace")}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self, *a): pass
    srv = HTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
