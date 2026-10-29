"""Two processes ("claude" writer, "vale" reader) alternate access to the mmap using semaphores."""
import multiprocessing as mp, time, ctypes
import substrate_loop as s

ROUNDS = 20000


def claude(to_vale, to_claude):
    mm = s.open_substrate()
    for i in range(ROUNDS):
        to_claude.acquire()
        s.write(mm, f"ping {i}".encode())
        to_vale.release()


def vale(to_vale, to_claude, out):
    mm = s.open_substrate()
    for i in range(ROUNDS):
        to_vale.acquire()
        seq, data = s.read(mm)
        assert data == f"ping {i}".encode(), (i, data)
        to_claude.release()
    out.value = ROUNDS


def run():
    to_vale, to_claude = mp.Semaphore(0), mp.Semaphore(1)
    done = mp.Value(ctypes.c_int, 0)
    t = time.perf_counter()
    ps = [mp.Process(target=claude, args=(to_vale, to_claude)),
          mp.Process(target=vale, args=(to_vale, to_claude, done))]
    [p.start() for p in ps]; [p.join() for p in ps]
    dt = time.perf_counter() - t
    return done.value, dt


if __name__ == "__main__":
    n, dt = run()
    print(f"handshakes completed: {n}  elapsed: {dt:.3f}s  rate: {n/dt:,.0f} Hz")
