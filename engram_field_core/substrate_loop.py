"""mmap-backed substrate: tick loop + localhost HTTP listener over the segment."""
import json, os, struct, sys, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from shm_handshake import Channel, SLOT_OFF

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "field.bin")
PORT = 8765


def make_handler(ch):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            _, ticks, last = ch.header()
            body = json.dumps({
                "ticks": ticks, "last_tick_ns": last,
                "claude": ch.read("claude")[1].decode(errors="replace"),
                "vale": ch.read("vale")[1].decode(errors="replace"),
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass
    return H


def main(duration=2.0):
    ch = Channel(PATH, create=True)
    base = ch.address()
    print(f"[substrate] file      : {PATH} ({os.path.getsize(PATH)} bytes)")
    print(f"[substrate] mmap base : 0x{base:016x}")
    print(f"[substrate] header    : 0x{base:016x}")
    for who, off in SLOT_OFF.items():
        print(f"[substrate] slot {who:<6}: 0x{base + off:016x}")

    srv = HTTPServer(("127.0.0.1", PORT), make_handler(ch))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"[substrate] listener  : http://127.0.0.1:{PORT}/")

    t0, n = time.monotonic(), 0
    while time.monotonic() - t0 < duration:
        ch.tick(); n += 1
        time.sleep(0.001)
    hz = n / (time.monotonic() - t0)
    print(f"[substrate] baseline tick frequency: {hz:.1f} Hz over {n} ticks")

    import urllib.request
    print("[listener ] GET ->", urllib.request.urlopen(f"http://127.0.0.1:{PORT}/").read().decode())
    srv.shutdown()


if __name__ == "__main__":
    main()
