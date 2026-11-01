"""mmap-backed shared segment. Layout: 8-byte counter | 4-byte length | payload."""
import mmap, os, struct, ctypes

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "substrate.bin")
SIZE = 4096
HDR = struct.Struct("<QI")

def open_substrate():
    fd = os.open(PATH, os.O_RDWR | os.O_CREAT, 0o600)
    os.ftruncate(fd, SIZE)
    mm = mmap.mmap(fd, SIZE)
    os.close(fd)
    return mm

def address(mm):
    return ctypes.addressof(ctypes.c_char.from_buffer(mm))

def write(mm, data: bytes):
    n, _ = HDR.unpack_from(mm, 0)
    mm[HDR.size:HDR.size + len(data)] = data
    HDR.pack_into(mm, 0, n + 1, len(data))

def read(mm):
    n, ln = HDR.unpack_from(mm, 0)
    return n, bytes(mm[HDR.size:HDR.size + ln])
