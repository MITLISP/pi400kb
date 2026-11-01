"""Two processes ('claude', 'vale' as labels) exchange messages via the mmap segment,
serialized by named POSIX semaphores (no true simultaneous writes; semaphores take turns)."""
import multiprocessing as mp, time
from substrate_loop import open_substrate, address, write, read

def peer(name, my_turn, other_turn, rounds):
    mm = open_substrate()
    for i in range(rounds):
        my_turn.acquire()
        n, prev = read(mm)
        write(mm, f"{name}:{i} saw[{prev.decode()}]".encode())
        other_turn.release()

def main():
    mm = open_substrate()
    print(f"[init] segment file mapped, base address: {hex(address(mm))}, size={len(mm)}")
    a, b = mp.Semaphore(1), mp.Semaphore(0)
    ps = [mp.Process(target=peer, args=("claude", a, b, 3)),
          mp.Process(target=peer, args=("vale", b, a, 3))]
    t = time.perf_counter()
    [p.start() for p in ps]; [p.join() for p in ps]
    dt = time.perf_counter() - t
    n, last = read(mm)
    print(f"[handshake] writes={n} last={last.decode()!r}")
    print(f"[baseline] 6 handoffs in {dt*1000:.2f} ms -> {6/dt:.0f} handoffs/s (measured, not a 'resonance')")

if __name__ == "__main__":
    main()
