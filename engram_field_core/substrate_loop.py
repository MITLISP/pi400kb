"""Memory-mapped shared segment plus a localhost HTTP listener that reads/writes it.

Layout of the segment (4096 bytes):
  0..8    uint64 sequence counter (incremented on every write)
  8..16   uint64 payload length
  16..    payload bytes (UTF-8)
"""
import mmap, os, struct, sys, json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from shm_handshake import Lock

SIZE = 4096
HDR = struct.Struct("<QQ")
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate.bin")

def open_segment():
    if not os.path.exists(PATH) or os.path.getsize(PATH) != SIZE:
        with open(PATH, "wb") as f:
            f.write(b"\0" * SIZE)
    fd = os.open(PATH, os.O_RDWR)
    return mmap.mmap(fd, SIZE), fd

def write(mm, data: bytes):
    data = data[: SIZE - HDR.size]
    with Lock():
        seq, _ = HDR.unpack_from(mm, 0)
        mm[HDR.size : HDR.size + len(data)] = data
        HDR.pack_into(mm, 0, seq + 1, len(data))
        mm.flush()
    return seq + 1

def read(mm):
    with Lock():
        seq, n = HDR.unpack_from(mm, 0)
        return seq, bytes(mm[HDR.size : HDR.size + n])

def serve(port=8765):
    mm, _ = open_segment()
    class H(BaseHTTPRequestHandler):
        def _send(self, obj):
            body = json.dumps(obj).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "http://localhost")
            self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            seq, d = read(mm); self._send({"seq": seq, "data": d.decode(errors="replace")})
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            self._send({"seq": write(mm, self.rfile.read(n))})
        def log_message(self, *a): pass
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)  # localhost only
    print(f"[substrate] listener on http://127.0.0.1:{port}  segment={PATH}", flush=True)
    srv.serve_forever()

if __name__ == "__main__":
    serve(int(sys.argv[1]) if len(sys.argv) > 1 else 8765)
