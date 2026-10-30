"""File-backed mmap substrate plus a localhost HTTP listener that reads it."""
import ctypes
import mmap
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate.bin")
SIZE = 4096
SLOT = 256  # byte 0..7 sequence counter, rest payload


def open_substrate():
    fd = os.open(PATH, os.O_RDWR | os.O_CREAT)
    os.ftruncate(fd, SIZE)
    mm = mmap.mmap(fd, SIZE)
    os.close(fd)
    return mm


def address(mm):
    return hex(ctypes.addressof(ctypes.c_char.from_buffer(mm)))


def write_slot(mm, idx, text):
    off = idx * SLOT
    seq = int.from_bytes(mm[off:off + 8], "little") + 1
    data = text.encode()[:SLOT - 9]
    mm[off + 8:off + SLOT] = data.ljust(SLOT - 8, b"\0")
    mm[off:off + 8] = seq.to_bytes(8, "little")
    return seq


def read_slot(mm, idx):
    off = idx * SLOT
    seq = int.from_bytes(mm[off:off + 8], "little")
    return seq, bytes(mm[off + 8:off + SLOT]).rstrip(b"\0").decode(errors="replace")


def start_listener(mm, port=0):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            body = "\n".join("slot%d seq=%d %r" % ((i,) + read_slot(mm, i)) for i in range(2)).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
