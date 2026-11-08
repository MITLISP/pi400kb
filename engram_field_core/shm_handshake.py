"""Two-party read/write handshake over the mmap, using OS semaphores."""
import multiprocessing as mp, time, urllib.request
from substrate_loop import Substrate, start_listener

def party(name, n, my_turn, other_turn):
    sub = Substrate()
    for i in range(n):
        my_turn.acquire()
        if name == "claude":
            sub.write(f"ping {i}".encode())
        else:
            seq, data = sub.read()
            sub.write(b"ack " + data)
        other_turn.release()

if __name__ == "__main__":
    sub = Substrate()
    srv = start_listener(sub)
    port = srv.server_address[1]
    N = 20000
    a, b = mp.Semaphore(1), mp.Semaphore(0)   # claude goes first
    ps = [mp.Process(target=party, args=("claude", N, a, b)),
          mp.Process(target=party, args=("vale", N, b, a))]
    t0 = time.perf_counter()
    for p in ps: p.start()
    for p in ps: p.join()
    dt = time.perf_counter() - t0
    seq, data = sub.read()
    print(f"[mmap] file-backed, base virtual address {hex(sub.addr)}, size {sub.size}")
    print(f"[listener] http://127.0.0.1:{port} (loopback only)")
    print(f"[handshake] {N} round trips, final seq={seq}, last payload={data!r}")
    print(f"[baseline] {N/dt:,.0f} round trips/s ({N/dt/1000:.1f} kHz) — measured handshake rate")
    print("[listener check]", urllib.request.urlopen(f"http://127.0.0.1:{port}/").read().decode().strip())
    srv.shutdown()
