#!/bin/sh
# pack-nw.sh <out dir> <name> : (inside the xs container) runtime files of an NW.js Linux build for e2k, stripped,
# into /tmp/<name>.tar.zst
set -e
O=$1; N=$2; S=/opt/mcst/lcc-1.29.16.e2k-v5.8c2.linux-6.1/binutils/bin/e2k-linux-strip
D=/tmp/pack-$N; rm -rf $D; mkdir -p $D/$N/lib; cd $O
for f in nw chrome_crashpad_handler icudtl.dat v8_context_snapshot.bin snapshot_blob.bin resources.pak nw_100_percent.pak \
  nw_200_percent.pak locales credits.html; do [ -e $f ] && cp -a $f $D/$N/; done
for f in libnw.so libnode.so libEGL.so libGLESv2.so libvulkan.so.1; do [ -e lib/$f ] && cp -a lib/$f $D/$N/lib/; done
rm -f $D/$N/locales/*.info
for f in nw chrome_crashpad_handler lib/libnw.so lib/libnode.so lib/libEGL.so lib/libGLESv2.so lib/libvulkan.so.1; do
  [ -f $D/$N/$f ] && $S --strip-unneeded $D/$N/$f; done
cd $D && tar cf - $N | zstd -q -T16 -12 -o /tmp/$N.tar.zst -f; ls -la /tmp/$N.tar.zst; du -sh $D/$N; rm -rf $D
