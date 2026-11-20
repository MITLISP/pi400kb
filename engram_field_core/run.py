import os, sys, ctypes, time, json, subprocess, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import substrate_loop as s, shm_handshake as h

mm, _ = s.open_segment()
addr = ctypes.addressof(ctypes.c_char.from_buffer(mm))
print(f"[init] segment {s.PATH} size={s.SIZE} mapped at 0x{addr:x} (pid {os.getpid()}, virtual, per-process)")
seq, last, hz, dt = h.handshake()
print(f"[handshake] 2 processes, final seq={seq}, last='{last}', {dt:.3f}s -> {hz:,.0f} round-trips/s")
p = subprocess.Popen([sys.executable, s.__file__, "8765"], stdout=subprocess.PIPE, text=True)
print(p.stdout.readline().strip())
req = urllib.request.Request("http://127.0.0.1:8765", data=b"hello from listener", method="POST")
print("[listener] POST ->", urllib.request.urlopen(req).read().decode())
print("[listener] GET  ->", urllib.request.urlopen("http://127.0.0.1:8765").read().decode())
p.terminate()
