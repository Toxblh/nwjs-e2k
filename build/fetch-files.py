#!/usr/bin/python3
# fetch-files.py <raw diff (git diff --raw --abbrev=40)> <outdir> : fetch both sides of every changed file over HTTP
# a/ = upstream Chromium tag (googlesource ?format=TEXT), b/ = NW.js fork commit (raw.githubusercontent.com).
import base64, concurrent.futures, os, sys, urllib.request, urllib.parse
raw, out = sys.argv[1], sys.argv[2]
UP = 'https://raw.githubusercontent.com/chromium/chromium/%s/%%s' % os.environ.get('UPTAG', '154.0.8037.58')
NW = 'https://raw.githubusercontent.com/nwjs/chromium.src/%s/%%s' % os.environ.get('NWSHA', '9fd7cb96a1a60c107768b38e6bb4632b3a3ab5dd')
jobs = []
for l in open(raw):
    meta, path = l.rstrip('\n').split('\t', 1)
    m = meta.split()
    if m[2].strip('0'): jobs.append(('a', path, m[0][1:]))
    if m[3].strip('0'): jobs.append(('b', path, m[1]))
def get(j):
    side, path, mode = j
    dst = os.path.join(out, side, path)
    if os.path.exists(dst): return None
    q = urllib.parse.quote(path)
    for t in range(5):
        try:
            d = urllib.request.urlopen((UP if side == 'a' else NW) % q, timeout=60).read()
            pass
            break
        except Exception as e: err = e
    else: return '%s %s %s' % (side, path, err)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if mode == '120000': os.symlink(d.decode(), dst)
    else:
        open(dst, 'wb').write(d)
        if mode == '100755': os.chmod(dst, 0o755)
    return None
with concurrent.futures.ThreadPoolExecutor(8) as ex:
    errs = [e for e in ex.map(get, jobs) if e]
print('files', len(jobs), 'errors', len(errs)); print('\n'.join(errs[:20]))
