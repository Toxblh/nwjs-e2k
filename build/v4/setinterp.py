#!/usr/bin/env python3
# setinterp.py <elf> <dir with ld-linux.so.2 and the libraries>
# Writes <dir>/ld-linux.so.2 into PT_INTERP and <dir> into the reserved absolute RPATH entry, in place (the build
# reserves ~180 bytes for each; no patchelf needed). Run again after moving the directory.
import os, struct, sys
f, d = sys.argv[1], os.path.abspath(sys.argv[2])
interp = (d + "/ld-linux.so.2").encode()
data = bytearray(open(f, "rb").read())
assert data[:4] == b"\x7fELF" and data[4] == 2, "not an ELF64 file"
phoff, = struct.unpack_from("<Q", data, 32); phentsize, phnum = struct.unpack_from("<HH", data, 54)
for i in range(phnum):
    o = phoff + i * phentsize
    if struct.unpack_from("<I", data, o)[0] == 3:
        off, = struct.unpack_from("<Q", data, o + 8); size, = struct.unpack_from("<Q", data, o + 32)
        if len(interp) + 1 > size: sys.exit("path too long for PT_INTERP: %d > %d" % (len(interp), size - 1))
        data[off:off + size] = interp + b"\0" * (size - len(interp))
        break
else:
    sys.exit("no PT_INTERP")
# the RPATH reserve: an absolute entry after "$ORIGIN/...:" (at build time /opt/<name>/LIB + '/' * 160)
k = data.find(b"LIB" + b"/" * 100)
if k >= 0:
    s = data.rindex(b":", 0, k) + 1; e = data.index(b"\0", s); room = e - s
    if len(d) <= room:
        data[s:e] = d.encode() + b"/" * (room - len(d))   # trailing slashes keep the length; "dir////" is the same dir
    else:
        print("note: directory path longer than the RPATH reserve (%d), only the $ORIGIN entry is used" % room)
open(f + ".tmp", "wb").write(data); os.chmod(f + ".tmp", os.stat(f).st_mode); os.replace(f + ".tmp", f)
print("interpreter ->", interp.decode())
