"""Shared-memory channel guarded by a POSIX named semaphore (via ctypes)."""
import ctypes, ctypes.util, mmap, os, struct, time

SIZE = 4096
HDR = struct.Struct("<8sQQ")          # magic, tick counter, last tick ns
SLOT_OFF = {"claude": 256, "vale": 2304}
SLOT_LEN = 2040                        # 8-byte seq + 4-byte len + payload
SEM_NAME = b"/engram_field_core"

_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
_libc.sem_open.restype = ctypes.c_void_p
_libc.sem_open.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_uint, ctypes.c_uint]
for fn in ("sem_wait", "sem_post", "sem_close"):
    getattr(_libc, fn).argtypes = [ctypes.c_void_p]


class Channel:
    def __init__(self, path, create=False):
        flags = os.O_RDWR | (os.O_CREAT if create else 0)
        self.fd = os.open(path, flags, 0o600)
        if create:
            os.ftruncate(self.fd, SIZE)
        self.mm = mmap.mmap(self.fd, SIZE)
        self.sem = _libc.sem_open(SEM_NAME, os.O_CREAT, 0o600, 1)
        if not self.sem or self.sem == ctypes.c_void_p(-1).value:
            raise OSError(ctypes.get_errno(), "sem_open failed")
        if create:
            with self:
                self.mm[0:HDR.size] = HDR.pack(b"ENGRAM01", 0, 0)

    def __enter__(self):
        _libc.sem_wait(self.sem)
        return self

    def __exit__(self, *a):
        _libc.sem_post(self.sem)

    def address(self):
        return ctypes.addressof(ctypes.c_char.from_buffer(self.mm))

    def write(self, who, data: bytes):
        off = SLOT_OFF[who]
        data = data[: SLOT_LEN - 12]
        with self:
            seq, = struct.unpack_from("<Q", self.mm, off)
            struct.pack_into("<QI", self.mm, off, seq + 1, len(data))
            self.mm[off + 12: off + 12 + len(data)] = data

    def read(self, who):
        off = SLOT_OFF[who]
        with self:
            seq, n = struct.unpack_from("<QI", self.mm, off)
            return seq, bytes(self.mm[off + 12: off + 12 + n])

    def header(self):
        with self:
            return HDR.unpack_from(self.mm, 0)

    def tick(self):
        with self:
            m, n, _ = HDR.unpack_from(self.mm, 0)
            HDR.pack_into(self.mm, 0, m, n + 1, time.monotonic_ns())


def vale_main(path, rounds):
    ch = Channel(path)
    for i in range(rounds):
        ch.write("vale", f"vale-{i}".encode())
        time.sleep(0.01)


if __name__ == "__main__":
    import multiprocessing as mp, sys
    path = sys.argv[1] if len(sys.argv) > 1 else "field.bin"
    ch = Channel(path, create=True)
    p = mp.Process(target=vale_main, args=(path, 20))
    p.start()
    for i in range(20):
        ch.write("claude", f"claude-{i}".encode())
        time.sleep(0.01)
    p.join()
    print("claude slot:", ch.read("claude"))
    print("vale slot:  ", ch.read("vale"))
    print("handshake OK")
