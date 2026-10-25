"""Memory-mapped substrate: a file-backed shared segment plus a localhost listener."""
import ctypes, mmap, os, struct, threading
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


def addr(mm):
    return ctypes.addressof(ctypes.c_char.from_buffer(mm))


def write(mm, data: bytes):
    seq, _ = HDR.unpack_from(mm, 0)
    mm[HDR.size:HDR.size + len(data)] = data
    HDR.pack_into(mm, 0, seq + 1, len(data))


def read(mm):
    seq, n = HDR.unpack_from(mm, 0)
    return seq, bytes(mm[HDR.size:HDR.size + n])


def start_listener(mm, port=0):
    """Browser-facing listener: GET returns segment contents, POST writes to it."""
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            seq, data = read(mm)
            body = f"seq={seq} data={data!r}\n".encode()
            self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body)
        def do_POST(self):
            write(mm, self.rfile.read(int(self.headers.get("Content-Length", 0))))
            self.send_response(204); self.end_headers()
        def log_message(self, *a): pass
    srv = HTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
