"""Two processes ("claude", "vale") alternate read/write on the segment using semaphores."""
import multiprocessing as mp, time, ctypes
import substrate_loop as s

ROUNDS = 20000

def party(name, mine, theirs, first):
    mm = s.open_substrate()
    for i in range(ROUNDS):
        mine.acquire()
        s.write(mm, f"{name}:{i}".encode())
        theirs.release()

def measure():
    mm = s.open_substrate()
    s.HDR.pack_into(mm, 0, 0, 0)
    a, b = mp.Semaphore(1), mp.Semaphore(0)
    p1 = mp.Process(target=party, args=("claude", a, b, True))
    p2 = mp.Process(target=party, args=("vale", b, a, False))
    t = time.perf_counter(); p1.start(); p2.start(); p1.join(); p2.join()
    dt = time.perf_counter() - t
    seq, data = s.read(mm)
    return mm, seq, data, (2 * ROUNDS) / dt
