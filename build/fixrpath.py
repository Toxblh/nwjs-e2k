#!/usr/bin/python3
# fixrpath.py <elf> <new rpath> : rewrite DT_RPATH/DT_RUNPATH in place (the new string must not be longer than the
# old one; the rest is NUL-padded). The cross build leaves the sysroot paths (/e2k/lib64:...) there; the packages
# need $ORIGIN (or $ORIGIN/lib) so that no LD_LIBRARY_PATH is required.
import struct, sys, os
f, new = sys.argv[1], sys.argv[2].encode()
d = bytearray(open(f, 'rb').read())
shoff, = struct.unpack_from('<Q', d, 0x28); shentsize, shnum, shstrndx = struct.unpack_from('<HHH', d, 0x3a)
secs = [struct.unpack_from('<IIQQQQIIQQ', d, shoff + i * shentsize) for i in range(shnum)]
dyn = [s for s in secs if s[1] == 6][0]          # SHT_DYNAMIC
strtab = secs[dyn[6]]                            # sh_link -> .dynstr
done = 0
for i in range(dyn[5] // 16):
    tag, val = struct.unpack_from('<qQ', d, dyn[4] + i * 16)
    if tag in (15, 29):                          # DT_RPATH, DT_RUNPATH
        o = strtab[4] + val; e = d.index(b'\0', o); old = bytes(d[o:e])
        if len(new) > len(old): sys.exit('new rpath longer than the old one')
        d[o:e] = new + b'\0' * (len(old) - len(new)); done += 1
        print('%s: %s -> %s' % (os.path.basename(f), old.decode()[:60], new.decode()))
if not done: print('%s: no RPATH' % os.path.basename(f))
open(f + '.tmp', 'wb').write(d); os.chmod(f + '.tmp', os.stat(f).st_mode); os.replace(f + '.tmp', f)
