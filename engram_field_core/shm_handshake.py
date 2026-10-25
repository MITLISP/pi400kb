"""Two-party handshake over the substrate using named POSIX semaphores (via multiprocessing)."""
import multiprocessing as mp, time
import substrate_loop as s


def peer(name, my_turn, other_turn, rounds):
    mm = s.open_substrate()
    for _ in range(rounds):
        my_turn.acquire()
        seq, data = s.read(mm)
        s.write(mm, f"{name}:{seq}".encode())
        other_turn.release()


def measure(rounds=20000):
    claude_turn, vale_turn = mp.Semaphore(1), mp.Semaphore(0)
    p = mp.Process(target=peer, args=("vale", vale_turn, claude_turn, rounds))
    p.start()
    mm = s.open_substrate()
    t0 = time.perf_counter()
    for _ in range(rounds):
        claude_turn.acquire()
        seq, _ = s.read(mm)
        s.write(mm, f"claude:{seq}".encode())
        vale_turn.release()
    p.join()
    dt = time.perf_counter() - t0
    return rounds / dt, s.read(mm), mm
