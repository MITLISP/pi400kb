"""Two processes ("claude", "vale") ping-pong through the mmap using semaphores."""
import multiprocessing as mp
import time
import urllib.request

import substrate_loop as s

ROUNDS = 20000


def peer(name, idx, mine, theirs, first):
    mm = s.open_substrate()
    for i in range(ROUNDS):
        if not (first and i == 0):
            mine.acquire()
        s.write_slot(mm, idx, "%s:%d" % (name, i))
        theirs.release()


def main():
    mm = s.open_substrate()
    for i in range(2):
        s.write_slot(mm, i, "init")
    print("[substrate] file=%s base_addr=%s size=%d" % (s.PATH, s.address(mm), s.SIZE))
    srv = s.start_listener(mm)
    port = srv.server_address[1]
    print("[listener] http://127.0.0.1:%d live" % port)
    a, b = mp.Semaphore(0), mp.Semaphore(0)
    t0 = time.perf_counter()
    ps = [mp.Process(target=peer, args=("claude", 0, a, b, True)),
          mp.Process(target=peer, args=("vale", 1, b, a, False))]
    for p in ps:
        p.start()
        print("[handshake] pid=%d started" % p.pid)
    for p in ps:
        p.join()
    dt = time.perf_counter() - t0
    for i in range(2):
        print("[slot%d] offset=%s %s" % (i, hex(i * s.SLOT), s.read_slot(mm, i)))
    print("[listener] GET ->", urllib.request.urlopen("http://127.0.0.1:%d" % port).read().decode().replace("\n", " | "))
    print("[baseline] %d round trips in %.3fs = %.0f Hz handshake rate" % (ROUNDS, dt, ROUNDS / dt))
    srv.shutdown()


if __name__ == "__main__":
    main()
