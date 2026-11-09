import json, urllib.request, time
import substrate_loop as s, shm_handshake as h

mm = s.open_segment()
print(f"[init] segment file: {s.PATH} size={s.SIZE}")
print(f"[init] mapped virtual address (this process): {s.address(mm)}")
srv = s.serve(mm)
port = srv.server_address[1]
print(f"[listener] http://127.0.0.1:{port} live")
n, dt, last = h.run()
print(f"[handshake] {n} semaphore-synchronised round trips in {dt:.3f}s; last={last}")
print(f"[baseline] round-trip rate: {n/dt:,.0f} Hz (mean period {dt/n*1e6:.1f} us)")
mm2 = s.open_segment()
print("[listener] GET ->", json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/").read()))
srv.shutdown()
