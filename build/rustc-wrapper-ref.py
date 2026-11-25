# Addition to the seed-based rustc wrapper of the e2k cross build (rustc itself runs only natively on an Elbrus;
# the cross build takes every Rust step from a "seed" = outputs of a native build of the e2k Chrome, keyed by the
# sha256 of the step's .rsp.rust/.rustflags.json and inputs). Electron and NW.js differ from that build only in
# link-only arguments of some steps (-l/-L, -Clink-arg rpath); this accepts such a step when the reference out dir
# of the seed (mounted at /ref) has it with exactly the seed's hash and it equals ours without the link-only args.
REF = '/ref'
def _link(t): return t.startswith('-l') or t.startswith('-L') or 'link-arg' in t
def _norm_rsp(p): return [t for t in open(p).read().split() if not _link(t)]
def _norm_json(p):
    def w(x):
        if isinstance(x, list): return [w(y) for y in x if not (isinstance(y, str) and _link(y))]
        if isinstance(x, dict): return {k: w(v) for k, v in x.items()}
        return x
    return w(json.load(open(p)))
def _same(ext, key, norm):
    p = stem + ext
    if sha(p) == st[key]: return True
    r = os.path.join(REF, stem + ext)
    try: return os.path.exists(r) and sha(r) == st[key] and norm(r) == norm(p)
    except Exception: return False
if not _same('.rsp.rust', 'rsp', _norm_rsp): real('rsp differs')
if not _same('.rustflags.json', 'json', _norm_json): real('rustflags differ')
