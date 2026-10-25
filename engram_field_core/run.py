import urllib.request
import substrate_loop as s, shm_handshake as h

mm = s.open_substrate()
s.write(mm, b"init")
print(f"[substrate] file={s.PATH} size={s.SIZE} base_vaddr={hex(s.addr(mm))}")
srv = s.start_listener(mm)
port = srv.server_address[1]
print(f"[listener]  http://127.0.0.1:{port}")
urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}", b"from-browser", method="POST"))
print("[listener]  GET ->", urllib.request.urlopen(f"http://127.0.0.1:{port}").read().decode().strip())
hz, last, mm2 = h.measure()
print(f"[handshake] baseline round-trip rate: {hz:,.0f} Hz (claude<->peer, 2 semaphores)")
print(f"[handshake] final state: seq={last[0]} data={last[1]!r}")
