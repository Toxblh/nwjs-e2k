#!/bin/sh
# run-xvfb.sh :N : Xvfb (e2kv4 build of ALT xorg-xvfb with its own glibc 2.35 in lib/) on a host without X.
# Xvfb runs xkbcomp from /usr/bin: in a private mount namespace /usr/bin is replaced by a symlink farm that points to
# a second bind of the original /usr/bin, plus an xkbcomp wrapper.
D=$(cd "$(dirname "$0")" && pwd); N=${1:-:93}; T=/tmp/elnw
printf '#!/bin/sh\nexec %s/lib/ld-linux.so.2 --library-path %s/lib %s/bin/xkbcomp "$@"\n' $D $D $D > $D/bin/xkbcomp.sh; chmod +x $D/bin/xkbcomp.sh
rm -rf $T/usrbin; mkdir -p $T/usrbin $T/origbin
for f in /usr/bin/*; do ln -s $T/origbin/$(basename $f) $T/usrbin/; done; rm -f $T/usrbin/xkbcomp; ln -s $D/bin/xkbcomp.sh $T/usrbin/xkbcomp
exec unshare -rm sh -c "mount --bind /usr/bin $T/origbin && mount --bind $T/usrbin /usr/bin && exec $D/lib/ld-linux.so.2 --library-path $D/lib $D/bin/Xvfb $N -screen 0 1600x1000x24 -nolisten tcp -ac -xkbdir $D/share/X11/xkb"
