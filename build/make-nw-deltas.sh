#!/bin/sh
# make-nw-deltas.sh <workdir> : NW.js 0.117.0 changes relative to upstream, as diffs to apply to the e2k tree.
#  - Chromium: upstream 154.0.8037.58 -> nwjs/chromium.src 9fd7cb96 (only the changed files are fetched over HTTP;
#    the list comes from a blob-less shallow fetch of both commits), applied with `git apply --reject -p2`.
#  - V8: v8 671f7c27 (DEPS of 154.0.8037.58) -> nwjs/v8 7d30a50b, applied in src/v8 with -p1.
set -e
W=$1; mkdir -p $W && cd $W
git init -q cr && cd cr
git fetch -q --filter=blob:none --depth=1 https://github.com/nwjs/chromium.src.git 9fd7cb96a1a60c107768b38e6bb4632b3a3ab5dd && git tag -f nw FETCH_HEAD
git fetch -q --filter=blob:none --depth=1 https://chromium.googlesource.com/chromium/src.git refs/tags/154.0.8037.58 && git tag -f up FETCH_HEAD
git diff --no-renames --raw --abbrev=40 up nw > ../nw-raw.txt; cd ..
python3 "$(dirname "$0")/fetch-files.py" nw-raw.txt ff     # rerun until "errors 0" (rate limits)
(cd ff && git diff --no-index --binary a b > ../nw-chromium.diff) || true
git init -q v8 && cd v8
git fetch -q --depth=1 https://github.com/nwjs/v8.git 7d30a50b1e2bfd55dc960f4455123a18f80b0f2f && git tag nw FETCH_HEAD
git fetch -q --depth=1 https://github.com/v8/v8.git 671f7c27ac0403ceb8074a8dfbcc02cdd7369c3f && git tag up FETCH_HEAD
git diff --binary up nw > ../nw-v8.diff
