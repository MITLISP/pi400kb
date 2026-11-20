"""Cross-process lock (fcntl advisory lock on a sidecar file) and a ping-pong
handshake between two processes over the shared segment.

Note: Python's stdlib has no named POSIX semaphore; an exclusive flock serves the
same mutual-exclusion role. Writers are serialized, not truly simultaneous --
concurrent unsynchronized writes to the same bytes would corrupt the data.
"""
import fcntl, os, time, struct, multiprocessing as mp

LOCK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate.lock")

class Lock:
    def __enter__(self):
        self.fd = os.open(LOCK_PATH, os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(self.fd, fcntl.LOCK_EX); return self
    def __exit__(self, *a):
        fcntl.flock(self.fd, fcntl.LOCK_UN); os.close(self.fd)

def _peer(name, parity, rounds):
    import substrate_loop as s
    mm, _ = s.open_segment()
    done = 0
    while done < rounds:
        seq, _ = s.read(mm)
        if seq % 2 == parity:
            s.write(mm, f"{name}:{seq}".encode()); done += 1

def handshake(rounds=2000):
    import substrate_loop as s
    mm, _ = s.open_segment()
    with Lock():
        mm[:16] = b"\0" * 16
    t = time.perf_counter()
    a = mp.Process(target=_peer, args=("A", 0, rounds))
    b = mp.Process(target=_peer, args=("B", 1, rounds))
    a.start(); b.start(); a.join(); b.join()
    dt = time.perf_counter() - t
    seq, last = s.read(mm)
    return seq, last.decode(), rounds / dt, dt
