import json, urllib.request
import substrate_loop as s, shm_handshake as h
if __name__ == "__main__":
    mm, seq, data, hz = h.measure()
    srv = s.make_listener(mm)
    port = srv.server_address[1]
    resp = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/"))
    addr = __import__("ctypes").addressof(__import__("ctypes").c_char.from_buffer(mm))
    print(f"[substrate] file={s.PATH} size={s.SIZE}")
    print(f"[substrate] mapped virtual address=0x{addr:x}")
    print(f"[listener]  http://127.0.0.1:{port}/ -> {resp}")
    print(f"[handshake] writes={seq} last={data.decode()} (expected {2*h.ROUNDS})")
    print(f"[baseline]  alternating write handoff rate = {hz:,.0f} Hz")
    assert seq == 2 * h.ROUNDS and resp["seq"] == seq
    print("[ok] shared-memory handshake verified")
    del addr
