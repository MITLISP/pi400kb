"""Two-process handshake over the mmap segment, synchronised with OS semaphores."""
import multiprocessing as mp, time
import substrate_loop as s

def writer(n, to_reader, to_writer):
    mm = s.open_segment()
    for i in range(1, n + 1):
        to_writer.acquire()                      # wait until reader consumed previous
        s.write(mm, f"claude->vale #{i}".encode(), i)
        to_reader.release()

def reader(n, to_reader, to_writer, out):
    mm = s.open_segment()
    for _ in range(n):
        to_reader.acquire()
        seq, data = s.read(mm)
        out.put((seq, data.decode()))
        to_writer.release()

def run(n=20000):
    to_reader, to_writer = mp.Semaphore(0), mp.Semaphore(1)
    out = mp.Queue()
    w = mp.Process(target=writer, args=(n, to_reader, to_writer))
    r = mp.Process(target=reader, args=(n, to_reader, to_writer, out))
    t = time.perf_counter(); r.start(); w.start()
    last = None
    for _ in range(n): last = out.get()
    w.join(); r.join()
    dt = time.perf_counter() - t
    return n, dt, last
