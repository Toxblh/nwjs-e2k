#!/bin/bash
# nw-node-gyp.sh (inside the xs container, tree at /usr/src/chromium): generate out/Release/build.ninja for NW.js's
# libnode.so (GYP, as the NW.js buildbot does), for e2k: target/host arch e2k (build tools run under qemu like GN's),
# compiler = the e2k wrapper /x/bin/clang (via third_party/llvm-build/Release+Asserts/bin), sysroot /e2k.
set -e
cd /usr/src/chromium
mkdir -p third_party/llvm-build/Release+Asserts/bin
ln -sf /x/bin/clang third_party/llvm-build/Release+Asserts/bin/clang
ln -sf /x/bin/clang++ third_party/llvm-build/Release+Asserts/bin/clang++
export GYP_DEFINES="target_arch=e2k host_arch=e2k building_nw=1 clang=1 nwjs_sdk=0 disable_nacl=1 buildtype=Official sysroot=/e2k icu_use_data_file_flag=1 ${NW_GYP_EXTRA}"
export GYP_GENERATORS=ninja GYP_CHROMIUM_NO_ACTION=0 GYP_GENERATOR_FLAGS=output_dir=out
python3 third_party/node-nw/tools/gyp/gyp_main.py --depth=. -I third_party/node-nw/common.gypi -D build_type=Release third_party/node-nw/node.gyp
ls -la out/Release/build.ninja
