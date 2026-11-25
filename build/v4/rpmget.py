#!/usr/bin/python3
# rpmget.py <dest root> <pkg>... : download the newest e2kv4/noarch rpm of each package from the ALT Sisyphus e2k
# mirror and unpack it into <dest root> (rpm2cpio | cpio). Mirror base in $MIRROR.
import os, re, subprocess, sys, urllib.request, urllib.parse
B = os.environ['MIRROR'].rstrip('/') + '/'
dest = os.path.abspath(sys.argv[1]); os.makedirs(dest, exist_ok=True)
idx = {}
for arch in ('e2kv4', 'noarch'):
    html = urllib.request.urlopen(B + arch + '/RPMS.classic/', timeout=120).read().decode()
    for f in set(urllib.parse.unquote(x) for x in re.findall(r'href="([^"]+\.rpm)"', html)):
        m = re.match(r'(.+)-([^-]+)-([^-]+)\.(e2kv4|noarch)\.rpm$', f)
        if m: idx.setdefault(m.group(1), []).append((arch, f))
for p in sys.argv[2:]:
    c = idx.get(p)
    if not c: print('MISSING', p); continue
    arch, f = sorted(c)[-1]
    tmp = os.path.join(dest, '.rpm'); urllib.request.urlretrieve(B + arch + '/RPMS.classic/' + urllib.parse.quote(f), tmp)
    subprocess.run('rpm2cpio %s | (cd %s && cpio -idm --quiet)' % (tmp, dest), shell=True, check=True); os.remove(tmp)
    print('ok', f)
