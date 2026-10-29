import ctypes, urllib.request
import substrate_loop as s, shm_handshake as h

mm = s.open_substrate()
addr = ctypes.addressof(ctypes.c_char.from_buffer(mm))
print(f"[substrate] file={s.PATH} size={s.SIZE} mapped_va=0x{addr:x}")
srv = s.start_listener(mm)
print("[listener] http://127.0.0.1:8765 (localhost only, read-only)")
n, dt = h.run()
print(f"[handshake] {n} semaphore round-trips in {dt:.3f}s -> baseline {n/dt:,.0f} Hz")
print("[listener check]", urllib.request.urlopen("http://127.0.0.1:8765").read().decode().strip())
del addr
srv.shutdown()
