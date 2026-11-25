#!/usr/bin/python3
# hgscan.py <elf> : list the 8-byte slots of executable segments that the .50 e2k_hangguard predicate flags
# (port of cmd_is_dangerous: ALS cop 0x10 + ALES opc2 0x02 on ch 2/5, cop 0x60 + opc2 0x02 on ch 0/3), with pages.
import struct, sys
def danger(w, i, n):
    hs = w[i]; lng = ((hs >> 4) & 7) + 1; total = lng * 2
    if total > n - i: return False
    c = w[i:i + total]
    has_ss, has_cs0, has_cs1 = (hs >> 12) & 1, (hs >> 14) & 1, (hs >> 15) & 1
    mdl = (hs & 0xf) + 1; ales_mask = (hs >> 20) & 0x3f; als_mask = (hs >> 26) & 0x3f
    k = 1 + has_ss; als = [0] * 6
    for ch in range(6):
        if als_mask & (1 << ch):
            if k >= total: return False
            als[ch] = c[k]; k += 1
    k += has_cs0; fixed = k + has_cs1
    if mdl != fixed and mdl != fixed + 1: return False
    if mdl == fixed + 1:
        if k >= total: return False
        a25 = c[k]; k += 1
    else: a25 = 0x01c001c0
    k += has_cs1; half = 0; ales = [None] * 6
    for ch in range(6):
        if not ales_mask & (1 << ch): continue
        if ch == 2: ales[ch] = a25 >> 16
        elif ch == 5: ales[ch] = a25 & 0xffff
        else:
            idx = k + half // 2
            if idx >= total: return False
            ales[ch] = (c[idx] & 0xffff) if half & 1 else (c[idx] >> 16); half += 1
    for ch in range(6):
        if not als_mask & (1 << ch) or ales[ch] is None: continue
        cop = (als[ch] >> 24) & 0x7f; opc2 = (ales[ch] >> 8) & 0xff
        if cop == 0x10 and opc2 == 2 and ch in (2, 5): return True
        if cop == 0x60 and opc2 == 2 and ch in (0, 3): return True
    return False
d = open(sys.argv[1], 'rb').read()
phoff, = struct.unpack_from('<Q', d, 0x20); phes, phn = struct.unpack_from('<HH', d, 0x36)
hits = []
for p in range(phn):
    t, fl, off, va, pa, fsz = struct.unpack_from('<IIQQQQ', d, phoff + p * phes)
    if t != 1 or not fl & 1: continue
    w = struct.unpack_from('<%dI' % (fsz // 4), d, off)
    n = len(w)
    for i in range(0, n - 1, 2):
        if (w[i] >> 4) & 0 == 0 and danger(w, i, n): hits.append(va + i * 4)
print(len(hits), 'flagged slots,', len(set(h >> 12 for h in hits)), 'pages')
for h in hits[:50]: print(hex(h))
