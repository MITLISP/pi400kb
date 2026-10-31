"""Two-process ping-pong over the mmap segment, synchronized by semaphores."""
import multiprocessing as mp, time, urllib.request
import substrate_loop as s

def peer(name, mm_ready, my_turn, other_turn, n):
    mm = s.open_segment()
    for i in range(n):
        my_turn.acquire()
        seq, data = s.read(mm)
        s.write(mm, f"{name}:{i}".encode())
        other_turn.release()

def main(n=20000):
    mm = s.open_segment(); s.write(mm, b"init")
    srv = s.start_listener(mm)
    a, b = mp.Semaphore(1), mp.Semaphore(0)
    ps = [mp.Process(target=peer, args=("claude", None, a, b, n)),
          mp.Process(target=peer, args=("peer-b", None, b, a, n))]
    t0 = time.perf_counter()
    for p in ps: p.start()
    for p in ps: p.join()
    dt = time.perf_counter() - t0
    seq, data = s.read(mm)
    http = urllib.request.urlopen("http://127.0.0.1:8765/").read().decode()
    print(f"mmap file      : {s.PATH} ({s.SIZE} bytes)")
    print(f"mmap base addr : {hex(__import__('ctypes').addressof(__import__('ctypes').c_char.from_buffer(mm)))}")
    print(f"writes         : {seq} (expected {2*n+1})")
    print(f"last payload   : {data!r}")
    print(f"listener reply : {http}")
    print(f"baseline rate  : {2*n/dt:,.0f} handoffs/s ({dt:.2f}s)")

if __name__ == "__main__":
    main()
