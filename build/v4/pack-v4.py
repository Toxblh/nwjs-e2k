#!/usr/bin/python3
# pack-v4.py electron|nw <out dir> <name> : e2k-v4 package: the app files (stripped), lib/ = NEEDED closure from the
# v4 sysroot (glibc 2.35 included; the 8C hosts run glibc 2.29) + GTK3 and libnotify (dlopen'ed) + NSS modules,
# lib/ld-linux.so.2, setinterp.py and setup.sh (binds PT_INTERP / RPATH to this directory). -> /tmp/xs-tmp/<name>
import os, shutil, subprocess, sys
kind, out, name = sys.argv[1:4]
ROOT = os.path.expanduser('~/v4/root2'); BIN = os.path.expanduser('~/e2k-x86/mcst/lcc-1.29.16.e2k-v5.8c2.linux-6.1/binutils/bin/')
D = '/tmp/xs-tmp/' + name; shutil.rmtree(D, ignore_errors=True); os.makedirs(D + '/lib')
if kind == 'electron':
    files = ['electron', 'chrome_crashpad_handler', 'libEGL.so', 'libGLESv2.so', 'libvulkan.so.1', 'icudtl.dat', 'snapshot_blob.bin',
             'v8_context_snapshot.bin', 'resources.pak', 'chrome_100_percent.pak', 'chrome_200_percent.pak', 'resources', 'locales']
    exes = ['electron', 'chrome_crashpad_handler']; libdir = D + '/lib'
else:
    files = ['nw', 'chrome_crashpad_handler', 'icudtl.dat', 'v8_context_snapshot.bin', 'snapshot_blob.bin', 'resources.pak',
             'nw_100_percent.pak', 'nw_200_percent.pak', 'locales', 'lib/libnw.so', 'lib/libnode.so', 'lib/libEGL.so',
             'lib/libGLESv2.so', 'lib/libvulkan.so.1']
    exes = ['nw', 'chrome_crashpad_handler']; libdir = D + '/lib'
for f in files:
    s = os.path.join(out, f)
    if not os.path.exists(s): continue
    (shutil.copytree if os.path.isdir(s) else shutil.copy2)(s, os.path.join(D, f))
for root, ds, fs in os.walk(D + '/locales'):
    for f in fs:
        if f.endswith('.info'): os.remove(os.path.join(root, f))
elfs = [os.path.join(D, f) for f in files if not f.endswith(('.pak', '.dat', '.bin')) and os.path.isfile(os.path.join(D, f))]
for e in elfs: subprocess.run([BIN + 'e2k-linux-strip', '--strip-unneeded', e], check=True)
extra = [ROOT + '/usr/lib64/libgtk-3.so.0', ROOT + '/usr/lib64/libnotify.so.4']
nss = ['libsoftokn3.so', 'libfreebl3.so', 'libfreeblpriv3.so', 'libnssdbm3.so', 'libnssckbi.so']
for n in nss:
    for d in ('usr/lib64', 'usr/lib64/nss', 'lib64'):
        p = os.path.join(ROOT, d, n)
        if os.path.exists(p): extra.append(p); break
seeds = elfs + [p for p in extra if os.path.exists(p)]
r = subprocess.run(['python3', os.path.expanduser('~/v4/closure.py'), ROOT] + seeds, capture_output=True, text=True)
own = set(os.path.basename(e) for e in elfs)
libs = {}
for l in r.stdout.splitlines():
    n, p = l.split(' ', 1)
    if n not in own: libs[n] = p
for p in seeds[len(elfs):]: libs[os.path.basename(p)] = os.path.realpath(p)
for g in ('ld-linux.so.2', 'libc.so.6', 'libm.so.6', 'libpthread.so.0', 'libdl.so.2', 'librt.so.1', 'libresolv.so.2',
          'libutil.so.1', 'libnss_files.so.2', 'libnss_dns.so.2', 'libgcc_s.so.1'):
    for d in ('lib64', 'usr/lib64'):
        p = os.path.join(ROOT, d, g)
        if os.path.exists(p): libs[g] = os.path.realpath(p); break
for n, p in libs.items(): shutil.copy2(p, os.path.join(libdir, n))
print('MISSING', r.stderr.strip().replace('\n', ' ') or '-')
shutil.copy2(os.path.expanduser('~/elnw/bin/setinterp.py'), libdir + '/setinterp.py')
with open(D + '/setup.sh', 'w') as f:
    f.write('#!/bin/sh\n# setup.sh: bind %s to the glibc and libraries in lib/ of this directory (PT_INTERP and the absolute\n'
            '# RPATH entry are written in place). Run after unpacking and after every move of the directory.\n'
            'D=$(cd "$(dirname "$0")" && pwd)\n' % ' and '.join(exes) +
            ''.join('python3 "$D/lib/setinterp.py" "$D/%s" "$D/lib" || exit 1\n' % e for e in exes))
os.chmod(D + '/setup.sh', 0o755)
print(len(libs), 'libs;', subprocess.run(['du', '-sh', D], capture_output=True, text=True).stdout.split()[0])
