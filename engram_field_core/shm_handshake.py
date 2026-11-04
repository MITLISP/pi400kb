"""Two processes (labelled claude / vale) alternate access to the mmap using POSIX semaphores."""
import multiprocessing as mp, urllib.request
import substrate_loop as s

def worker(name, my_sem, other_sem, rounds):
    m = s.open_substrate()
    for i in range(rounds):
        my_sem.acquire()
        seq, data = s.read(m)
        s.write(m, f"{name}:{i} (saw {data.decode() or 'empty'})".encode())
        print(f"[{name}] wrote seq={seq+1}", flush=True)
        other_sem.release()

def main():
    m = s.open_substrate()
    s.write(m, b"")
    print(f"mmap file : {s.PATH}\nmapped at : {s.address(m)} ({s.SIZE} bytes)")
    srv = s.serve(m)
    print(f"listener  : http://127.0.0.1:{s.PORT}")
    a, b = mp.Semaphore(1), mp.Semaphore(0)
    ps = [mp.Process(target=worker, args=("claude", a, b, 3)),
          mp.Process(target=worker, args=("vale", b, a, 3))]
    [p.start() for p in ps]; [p.join() for p in ps]
    print("listener read:", urllib.request.urlopen(f"http://127.0.0.1:{s.PORT}").read().decode())
    print(f"baseline write+read rate: {s.baseline_rate(m):,.0f} Hz")
    srv.shutdown()

if __name__ == "__main__":
    main()
