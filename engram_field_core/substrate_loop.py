"""Memory-mapped shared segment plus a localhost-only HTTP listener that exposes it read-only."""
import mmap, os, struct, threading, http.server

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate.bin")
SIZE = 4096
HEADER = struct.Struct("<QI")  # sequence counter, payload length


def open_substrate():
    with open(PATH, "a+b") as f:
        f.truncate(SIZE)
    f = open(PATH, "r+b")
    return mmap.mmap(f.fileno(), SIZE)


def write(mm, payload: bytes):
    seq, _ = HEADER.unpack_from(mm, 0)
    mm[HEADER.size:HEADER.size + len(payload)] = payload
    HEADER.pack_into(mm, 0, seq + 1, len(payload))


def read(mm):
    seq, n = HEADER.unpack_from(mm, 0)
    return seq, bytes(mm[HEADER.size:HEADER.size + n])


def start_listener(mm, port=8765):
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            seq, data = read(mm)
            body = f"seq={seq} payload={data.decode(errors='replace')}\n".encode()
            self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body)
        def log_message(self, *a): pass
    srv = http.server.HTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
