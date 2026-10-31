"""File-backed mmap segment + localhost HTTP listener that reads it."""
import mmap, os, struct, threading, http.server, json

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate.bin")
SIZE = 4096
HDR = struct.Struct("<QI")  # sequence counter, payload length

def open_segment():
    fd = os.open(PATH, os.O_RDWR | os.O_CREAT)
    os.ftruncate(fd, SIZE)
    return mmap.mmap(fd, SIZE)

def write(mm, payload: bytes):
    seq, _ = HDR.unpack_from(mm, 0)
    mm[HDR.size:HDR.size + len(payload)] = payload
    HDR.pack_into(mm, 0, seq + 1, len(payload))

def read(mm):
    seq, n = HDR.unpack_from(mm, 0)
    return seq, bytes(mm[HDR.size:HDR.size + n])

def start_listener(mm, port=8765):
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            seq, data = read(mm)
            body = json.dumps({"seq": seq, "data": data.decode(errors="replace")}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(body)
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
