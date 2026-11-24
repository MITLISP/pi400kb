"""Two processes read/write the same mmap, serialized by a shared semaphore."""
import multiprocessing as mp, os, time, urllib.request
import substrate_loop as sl

ROUNDS = 2000

def peer(name, sem, ready, q):
    mm = sl.open_substrate()
    q.put((name, os.getpid(), hex(sl.address_of(mm))))
    ready.wait()
    t0 = time.perf_counter()
    for i in range(ROUNDS):
        with sem:
            prev = sl.read(mm)
            sl.write(mm, f"{name}:{i}|prev={prev[:24].decode(errors='replace')}".encode())
    q.put((name, "done", time.perf_counter() - t0))
    mm.close()

if __name__ == "__main__":
    sem, ready, q = mp.BoundedSemaphore(1), mp.Event(), mp.Queue()
    mm = sl.open_substrate()
    sl.write(mm, b"init")
    print(f"[init] substrate file: {sl.PATH} ({sl.SIZE} bytes)")
    print(f"[init] runtime pid={os.getpid()} mmap vaddr={hex(sl.address_of(mm))}")
    srv = sl.make_listener(mm, sem)
    port = srv.server_address[1]
    print(f"[listener] http://127.0.0.1:{port}/ (GET reads, POST writes)")

    procs = [mp.Process(target=peer, args=(n, sem, ready, q)) for n in ("claude", "vale")]
    for p in procs: p.start()
    for _ in procs:
        n, pid, addr = q.get(); print(f"[peer] {n} pid={pid} mmap vaddr={addr} (same file, own address space)")
    ready.set()
    times = {}
    for _ in procs:
        n, _, dt = q.get(); times[n] = dt
    for p in procs: p.join()

    with sem: final = sl.read(mm)
    print(f"[verify] final record: {final.decode()}")
    req = urllib.request.Request(f"http://127.0.0.1:{port}/", data=b"browser-probe", method="POST")
    urllib.request.urlopen(req).read()
    got = urllib.request.urlopen(f"http://127.0.0.1:{port}/").read()
    print(f"[verify] listener round-trip: {'OK' if got == b'browser-probe' else 'FAIL'} ({got!r})")
    total = 2 * ROUNDS
    wall = max(times.values())
    print(f"[measure] {total} locked read+write ops in {wall*1000:.1f} ms -> {total/wall:,.0f} ops/s")
    srv.shutdown(); mm.close()
