#!/usr/bin/python3
# seedfix.py <out dir> <seed dir> <reference out dir> : for every Rust step of <out dir> whose .rsp.rust or
# .rustflags.json differs from the seed's (as recorded from <reference out dir>) only in link-only arguments
# (-l<lib>, -L, -Clink-arg) - which do not change an rlib - point the seed entry at the new hashes.
import hashlib, json, os, sys
out, seed, refdir = sys.argv[1], sys.argv[2], sys.argv[3]
man = json.load(open(os.path.join(seed, 'manifest.json')))
orig = json.load(open(os.path.join(os.path.dirname(os.path.abspath(seed)), 'e2k-rel3', 'manifest.json')))['steps']  # the reference seed
def sha(p):
    try: return hashlib.sha256(open(p, 'rb').read()).hexdigest()
    except OSError: return None
def link(t): return t.startswith('-l') or t.startswith('-L') or 'link-arg' in t
def norm_rsp(p): return [t for t in open(p).read().split() if not link(t)]
def norm_json(p):
    def walk(x):
        if isinstance(x, list): return [walk(y) for y in x if not (isinstance(y, str) and link(y))]
        if isinstance(x, dict): return {k: walk(v) for k, v in x.items()}
        return x
    return walk(json.load(open(p)))
fixed = other = 0
for stem, st in man['steps'].items():
    for key, ext, norm in (('rsp', '.rsp.rust', norm_rsp), ('json', '.rustflags.json', norm_json)):
        p = os.path.join(out, stem + ext)
        if not os.path.exists(p): continue
        h = sha(p)
        if h == st[key]: continue
        ref = os.path.join(refdir, stem + ext)
        if os.path.exists(ref) and stem in orig and sha(ref) == orig[stem][key] and norm(ref) == norm(p):
            st[key] = h; fixed += 1; print('fixed', key, stem); continue
        other += 1; print('differs', key, stem)
json.dump(man, open(os.path.join(seed, 'manifest.json.new'), 'w'))
os.replace(os.path.join(seed, 'manifest.json.new'), os.path.join(seed, 'manifest.json'))
print('fixed', fixed, 'still different', other)
