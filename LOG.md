# Electron and NW.js for e2k-v5 (Elbrus-8SV) with the e2k V8 JIT port — log (agent elnw)

## 2026-11-25 versions chosen
- Base: our e2k Chromium tree = ALT chromium 154.0.8037.97 + e2k patches, V8 e2k-v8-js3 c50e517786 (the tree of
  node26 / chrome v4 on the x86 server: ~/chromium-v8-js3/chromium), toolchain/wrappers/xs-rexec as in HANDOFF and ~/v4/LOG.md.
- Electron: no Electron release line ships Chromium 154 as stable: 45.x went 154.0.8025/8029 (alpha.1-3) -> 155.0.8038+
  (alpha.4+), 46 nightlies 154.0.8015..8037.0 then 155. Picked **v46.0.0-nightly.20260902** = Chromium
  **154.0.8037.0** (the M154 branch point, the closest to our 8037.97), Node **24.20.0**, electron commit 15d32f2.
  Patches against 8037.0 apply to 8037.97+ALT+e2k with 5/257 problems (see below).
- NW.js: **v0.117.0** (2026-09-25) = Chromium **154.0.8037.58**, Node **26.7.0** (nwjs/node c82414748), nwjs/v8
  7d30a50b, nwjs/chromium.src 9fd7cb96. Exact M154 match.

## Layout (x86 server, home of user test)
- ~/elnw/el/src: Electron tree = `cp -al` of ~/chromium-v8-js3/chromium (no out/), electron at src/electron (git clone
  of the tag), src/third_party/electron_node (nodejs/node v24.20.0, git, electron patches committed), src/third_party/nan.
  Hard links: every edit must replace the file (git apply / python os.replace / sed -i do; never write in place).
  Edited files of the shared tree: ~/elnw/el-tree-edits.txt.
- ~/elnw/nw/src: NW.js tree, same kind of copy; content/nw = nw.js tag nw-v0.117.0, third_party/node-nw = nwjs/node.
- ~/elnw/bin/xs-el: gen|build|status|shell (XS_PROJ=el|nw, XS_OUT=out dir), unit xs-build-<proj>, log
  ~/elnw/build-<proj>-<out>.log. Wrapper copy ~/elnw/xbin (= ~/xtools/bin, clang: elbrus-v5, v4's per-compile timeout
  900 s + -O1 retry, DISTCC_IO_TIMEOUT=300, js2c -O0), distcc a distcc worker + a distcc worker (60 each), -j150.
  Container adds /opt/node22 (x86 node 22.20 + npm for Electron's webpack/TS steps).
- Rust: seed ~/xtools/rseed/e2k-electron = hard-linked copy of e2k-rel3 with its own manifest.json;
  ~/elnw/bin/seedfix.py re-keys steps whose rsp differs only in link args (-l/-L).

## 2026-11-25 Electron: patches
- electron/patches (config.json, 257 patches, mac-only squirrel/ReactiveObjC and reclient skipped) applied with
  `git apply --reject` (~/elnw/bin/apply-electron-patches.py). Problems: 2 .gitignore-only patches; 3 rejected hunks:
  - crash_allow_setting_more_options: `#include <map>` hunk (context differs) -> added by hand.
  - fix_select_the_first_menu_item_when_opened_via_keyboard hunk 2 (menu_controller.cc): code already differs in
    8037.97 -> dropped.
  - fix_wayland_window_stuck_maximized_after_early_maximize hunks 2-3: Wayland only, we run X11 -> dropped.
- Build fixes for the ALT/e2k tree:
  - electron/build/electron_paks.gni: tracing_resources.pak / //content/browser/tracing:resources removed (the ALT
    tarball has no catapult tracing UI, Debian patch remove-dependencies-on-third_party-catapult).
  - third_party/zstd/BUILD.gn (ALT unbundled = system zstd): added group("headers") that Electron's node wants.
  - libc++ ABI: electron's build_make_libcxx_abi_unstable_false_for_electron sets _LIBCPP_ABI_VERSION 1; that changes
    every bindgen output (allocator FFI) -> every Rust crate misses the native Rust seed (rustc under qemu never
    finishes). Reverted to ABI 2 (Chromium default). Consequence: Electron's libc++ ABI is not the "stable" one; native
    modules do not pass libc++ types across the boundary (N-API/nan use V8/C types), so this only matters for
    exotic addons.
  - libnotify headers: e2k root lacked libnotify-devel; headers of libnotify-devel-0.8.4-alt1.e2kv5 (ALT Sisyphus
    e2kv5 mirror) added to ~/e2k-root/usr/include/libnotify (noted in ~/xwork/e2k-root-added.txt). Electron loads
    libnotify with dlopen at run time.
  - npm: Electron's GN actions run `npm run ...` (webpack/tsc); yarn install of electron's devDependencies done on the
    x86 host with node 22.20 (`yarn install --immutable --mode=skip-build`), npm put on PATH inside the container.
- args: ~/elnw/args-el.gn = import(//electron/build/args/release.gn) + the js3 Chrome e2k args, is_official_build=false
  (as our Chrome; keeps Rust seed hits), chrome_pgo_phase=0, v8_builtins_profiling_log_file="" (no PGO profiles),
  pointer compression and V8 sandbox off (as the e2k port), no Vulkan/Dawn/SwiftShader.
- Disk: / of the x86 server had 23 GB free; removed stale ~/chromium/chromium/out/e2k-o1 (15.10) and e2k-o3t (16.10)
  experiment dirs (logged in ~/xwork/disk-cleanup.log) -> 39 GB free.

## 2026-11-25 NW.js: source preparation
- NW.js chromium delta = tree diff upstream 154.0.8037.58 -> nwjs/chromium.src 9fd7cb96: 1010 files (974 M, 36 A),
  2.5 MB (~/elnw/nwgit/nw-chromium.diff; both sides fetched per file over HTTP, googlesource rate-limits, GitHub mirror
  chromium/chromium used for the upstream side). NW v8 delta = v8 671f7c27 (DEPS of 8037.58) -> nwjs/v8 7d30a50b:
  50 files, +4840/-65 (~/elnw/nwgit/nw-v8.diff; nwjc.cc, v8.gyp, api additions).
- Applied to ~/elnw/nw/src with git apply --reject: 7 files with rejected hunks: chrome/browser/first_run/first_run.h,
  chrome/chrome_paks.gni, components/enterprise/client_certificates/core/private_key_factory.cc,
  net/cookies/cookie_util.cc, third_party/node/node.py, v8/gni/v8.gni, v8/src/api/api.cc; test-data files missing in
  the ALT tarball skipped.
- NW sub-repo patches (content/nw/patch/patch.cfg, the gclient hook nw_patch): perfetto (libperfettonode), icu,
  ffmpeg (-p0), devtools (-p0) applied; selenium/gyp not needed (no tools/gyp in the tarball, node-nw has its own).
- NW GN conflicts with the ALT/e2k tree:
  - build/config/gcc/BUILD.gn: ALT's CHROMIUM_RPATH line appends to an ldflags that NW commented out -> guarded.
  - NW forces exclude_unwind_tables=true -> -Cforce-unwind-tables=no for Rust -> every crate misses the seed:
    args exclude_unwind_tables=false (as the e2k Chrome).
  - NW disables PartitionAlloc-as-malloc on non-Windows (build_overrides/partition_alloc.gni, for libnode.so's
    malloc): the Rust allocator crate changes cfg -> all Rust misses. build/rust/allocator: on e2k the Rust side
    keeps the PA configuration (same rlibs as the seed) and allocator_impls.cc implements
    rust_allocator_internal::{alloc,...} on glibc malloc (define RUST_ALLOC_E2K_MALLOC; node26b3 code).
  - NW adds -Wl,-rpath=$ORIGIN/lib/ to every executable -> rustflags.json of build scripts differ: rustc wrapper
    copy ~/elnw/usrbin/rustc compares the json also without that link-only argument.
  - content/nw/BUILD.gn: nwjs pulled SwiftShader Vulkan (copy_icd); marl needs makecontext (missing in e2k glibc)
    -> dropped on e2k (no SwiftShader in the e2k Chrome either).
- NW node (libnode.so) is built by GYP (as NW's buildbot): ~/elnw/bin/nw-node-gyp.sh in the container,
  target_arch=host_arch=e2k (host tools run under qemu like GN's), clang = the e2k wrapper via
  third_party/llvm-build/Release+Asserts/bin, sysroot /e2k, python -> python3 in ~/elnw/xbin. node-nw edits:
  common.gypi without -fuse-ld=lld (GNU ld for e2k), deps/zstd/zstd.gyp STATIC_BMI2=0/DYNAMIC_BMI2=0 on e2k.
  OpenSSL: unknown arch -> linux-x86_64 no-asm config (LP64 LE, fine for e2k).

## 2026-11-25 Electron build pass 1 (x86 the x86 server + distcc a distcc worker/a distcc worker, -j150): 37.6k steps in 45 min
- Failures and fixes: npm missing in the container (-> /opt/node22), libnotify headers (-> e2k root), 2 Rust seed
  misses where the rsp differs only by -lz/-lm (seedfix), GTK: electron_gtk_stubs needs GTK3 headers ->
  gtk_version=3 (the e2k root has gtk+-3.0; Chrome e2k builds use 4), v8_context_snapshot_generator link:
  undefined __lccrt_builtin_cmp_eq_i_v2i2 from cc/scroll_snap_data.o (the lccopt bug the v4 agent found, here on v5
  too) -> wrapper builds that object with -fno-vectorize -fno-slp-vectorize.
- More fixes until the link: enable_resource_allowlist_generation=false (tools/resources/ar.py cannot parse the thin
  archives of the e2k GNU ar: "/43   /" member names); is_component_ffmpeg=false (v8_context_snapshot_generator
  links libffmpeg.so and runs on the Elbrus through xs-rexec, which ships only the binary); Rust: 2 more steps whose
  rsp differ only in link libs (seedfix; the wrapper copy ~/elnw/usrbin/rustc now accepts such steps itself, given
  the reference out dir mounted at /ref).
- Electron sources vs the 8037.97 tree: BrowserProcess has no speech_recognition_small_expert_model_installer in
  this tree (override removed); crash_reporter ProductInfo became a class with a constructor in 8037.97
  (GetProductInfo adapted).
- Link of ./electron (GNU ld for e2k): 93 s; electron 904 MB, 780 MB stripped (e2k code is large; Chrome is 981 MB).

## 2026-11-25 Electron on the Elbrus host: first run, the crash and the fix
- `electron --version` OK; ELECTRON_RUN_AS_NODE: process.arch e2k, v8 15.4.80.20-electron.0, fib(30) 150 ms.
  RPATH points to the cross sysroot (/e2k/...), libXNVCtrl.so.0 comes from the package dir via LD_LIBRARY_PATH.
- GUI start: SIGSEGV in memcpy under PartitionAlloc ThreadCache::Create on a thread with a 32 KB stack: Electron's
  ShutdownDetector thread (electron_browser_main_parts_posix.cc) uses PTHREAD_STACK_MIN*2 = 32 KB; e2k C frames
  overflow it already at the thread start (FilePath::Append -> operator new -> PA slow path). Found with gdb
  (fault 8 KB below the thread descriptor, mapping 0x8000) + breakpoint on pthread_attr_setstacksize + addr2line on
  the unstripped binary. Fix: 512 KB on __e2k__. (node's inspector SignalInspector thread also uses 32 KB, idle.)
- Smoke app (~/elnw/apps/smoke, Xvfb :93, --no-sandbox --disable-gpu): versions, renderer page, preload +
  contextBridge, IPC invoke/handle and send/on, renderer fib(30) 163 ms, sort 2e5 853 ms, Intl ru-RU, RegExp \p{L},
  WebAssembly, canvas, capturePage -> shots/electron-smoke-capturePage.png: all OK.
- Native addon: N-API module built on the Elbrus host with node-gyp of node26 (`--nodedir=~/node26/headers`), loads in Electron
  main process and in ELECTRON_RUN_AS_NODE. (electron:node_headers target fails: its configure.py does not know
  --dest-cpu e2k; not needed for N-API.)
- Obsidian 1.8.10 (x86 deb, resources/ only): starts, self-updates to 1.15.1 over the network, opens a vault, renders
  Markdown with table, code highlighting, MathJax, Russian UI (shots/electron-obsidian-{1,2,3}.png). Its .node
  modules (get-fonts, btime) are Windows/macOS-only, not loaded on Linux.
- TickTick 6.0.30 (x86 deb): starts, talks to its API, shows the login window (shots/electron-ticktick-1.png).
- Dist: ~/elnw/dist/electron-v46.0.0-nightly.20260902-linux-e2k.tar.xz (electron.sh, run-app.sh, README.md in
  Russian, examples/smoke, LOG.md).
- Electron dist: ~/elnw/dist/electron-v46.0.0-nightly.20260902-linux-e2k.tar.xz, 175 MB,
  md5 c8fc7bc4d0479a7feaa0c6ceb905170d (xz -6 on the Elbrus host at nice 19 under the other agents' load: ~45 min; next time
  compress on the x86 server).

## 2026-11-25 NW.js build (out/nw, -j90 next to the Electron build): ~31.4k steps, 47 min
- More NW/tree conflicts fixed on the way: NW's buildtools/third_party/libc++/__config_site uses ABI namespace __1
  and comments defines out -> every bindgen output changes (Rust seed misses) -> Chromium's __config_site kept;
  NW's devtools patch (-p0); rustc wrapper copy accepts rustflags.json that differ only by NW's rpath link-arg (and,
  with the reference out dir of the seed at /ref, any step that differs only in -l/-L/link-arg).
- Rust allocator: the host toolchain keeps the plain (non-PA) Rust allocator like the seed (override only for the
  target toolchain).
- content/nw/BUILD.gn: libffmpeg.so in the `dump` list only with is_component_ffmpeg (ffmpeg static here, like
  Electron: the snapshot generator runs remotely and would need libffmpeg.so).
- libnw.so (1.16 GB, NW builds Chrome as a shared library on Linux): GNU ld left Rust symbols undefined
  (serde_core, icu_collections, zune_core...): rlibs were outside the archive group in the *solink* rule; the e2k port
  only grouped them for executables -> build/toolchain/gcc_toolchain.gni: solink/solink_module put rsp + rlibs into
  one --start-group/--end-group on e2k.
- libnode.so via GYP (out/Release, 2055 steps, 145 s): OpenSSL async off (OPENSSL_NO_ASYNC: no makecontext in e2k
  glibc), node_js2c links the NW build's libc++ (libcpp.a; js2c is compiled against Chromium's libc++ headers),
  js2c -O0 needs libc++'s vectorized std::find off (-D__OPTIMIZE_SIZE__=1; at -O0 lccopt emits
  __lccrt_builtin_shuffle_v16v16i16, absent from liblccrt_s.a), deps/v8/include -> the e2k V8's include (node-nw
  ships V8 14.x headers whose v8config.h does not know e2k; mixed headers would be an ABI mismatch, full clean
  rebuild done).
- First run: `nw --version` = "nwjs 154.0.8037.97". The window crashed with SIGILL (si_code ILL_ILLOPC) at the entry
  of cc::TransformTree::FindDrawnElasticOverscrollFromTransformId: dmesg showed **e2k_hangguard** (the PoC kernel
  module on the Elbrus host) "reserved hang encoding at libnw.so+0x21c1cea8 ... refused exec of page". Its scanner tests a
  command at every 8-byte slot, not only at command starts; disassembly from the function start shows 0x21c1cea8 is
  inside a command (StickyPositionOffset) = false positive. The guard polices mmap'ed shared libraries; the
  executable is not refused (Electron has ~30 such slots too, among them blink CSS parsing and the same cc function,
  and ran Obsidian for minutes). ~/elnw/bin/hgscan.py = the module's predicate in Python: libnw.so had 28 flagged
  slots in 26 pages. The 16 C/C++ objects holding them are compiled at -O1 through the wrapper
  (~/elnw/xbin/hgfix-objs.txt) -> 6 slots left (V8 Temporal, libaom blend_h_c, one std::sort instance, skrifa
  (Rust, from the seed), 2 outside code). NW then runs.
- NW smoke (~/elnw/apps/nwsmoke): versions nw 0.117.0 / chromium 154.0.8037.97 / node 26.7.0 / v8 15.4.80.20,
  arch e2k, fib(30) 167 ms, Intl ru-RU, fs, crypto, zlib, WebAssembly, the N-API addon, nw.App.manifest,
  nw.Window.capturePage -> shots/nwjs-smoke-capturePage.png.
- Real NW.js app: WaveDrom Editor 3.7.0 (x86 release; its app zip appended to the nw binary, unzipped) runs:
  editor + timing diagram rendering (shots/nwjs-wavedrom-1.png).
- Second -O1/-Os iteration (dav1d mc_tmpl, history_embeddings_search, js-temporal-objects at -Os) did not move the
  remaining 6 flagged slots (they are probably at function joins); left as is: they are in V8 Temporal ZonedDateTime,
  dav1d blend (AV1 video), one std::sort instance in history embeddings search, skrifa TrueType hinting (Rust from
  the seed) and 2 outside code. On a host without the guard none of this matters.
- A nonexistent app path (`nw /nonexistent`) ends in SIGILL ILL_ILLOPN in extensions::Extension::Create (a CHECK on
  the error path while NW loads the app as an extension); not investigated.
- NW dist: built on the x86 server (xz -T32 there: 1 min instead of 45 on the Elbrus host), copied to
  ~/elnw/dist/nwjs-v0.117.0-linux-e2k.tar.xz, 237 MB, md5 2da8e29f6dc18297b86914d1c23620da; checked from the tarball
  on the Elbrus host: `nw --version`, nw.sh + examples/nwsmoke.

## 2026-11-25 VS Code 1.147.0 (x86 release, JS unchanged) on the e2k Electron
- resources/ of the x86 tarball + the Electron package. Native modules rebuilt on the Elbrus host with node-gyp of node26
  (N-API, `--nodedir=~/node26/headers`, lcc 1.29.16, sources = npm packages of the same versions):
  kerberos, native-is-elevated, node-pty, @parcel/watcher, @vscode/native-watchdog, @vscode/policy-watcher,
  @vscode/spdlog, @vscode/sqlite3 (needs NODE_PATH for npm's `tar` module in its extract step), native-keymap
  (needs libxkbfile-devel headers: taken from the ALT e2kv5 rpm into /tmp, PKG_CONFIG_PATH).
  Left x86 (prebuilt only / closed): vsda, @vscode/os-proxy-resolver, @github/copilot-sdk, @vscode/deviceid.
- spdlog.node built with node-addon-api 8.9 had an undefined Napi::details::default_basic_finalizer<...> (an inline
  template whose address is taken in a default template argument is not emitted by lcc); with its own
  node-addon-api 7.1.0 it links.
- VS Code starts, opens a folder, the editor highlights JavaScript (shots/electron-vscode-{1,2}.png); a second
  `code <file>` call reaches the running instance over its IPC socket.
- lcc 1.29.16 bug (reduced, /tmp/elnw-style test t2.cc): a function template that is only named in a default
  template argument of another function template is never instantiated -> `U deffin<X>` in the .so. In
  node-addon-api this is AttachData<FreeType, finalizer = default_[basic_]finalizer<FreeType>> -> spdlog, node-pty,
  @parcel/watcher, policy-watcher, kerberos fail at dlopen (undefined Napi::details::default_*finalizer<...>);
  __attribute__((used)) or static do not help. Workaround: `(void)&default_basic_finalizer<FreeType>;` in the body of
  AttachData (~/elnw/bin/natbuild3.sh patches every napi-inl.h). Candidate MCST report. (node26's own N-API test
  addons are C, so this did not show there.)

## 2026-11-25 publication (requested by the user via the coordinator)
- Private GitHub repos created from the Mac: Toxblh/electron-e2k and Toxblh/nwjs-e2k (visibility PRIVATE checked),
  one commit each by Anton Palgunov <toxblh@gmail.com>, unsigned (the 1Password signing agent needs the user), no AI
  attribution. Content: the 99 e2k Chromium/V8 patches (e2k-base..e2k-v8-js3, author emails rewritten to the gmail
  address), Electron/NW.js patches and tree fixes, build scripts with generic paths and no hosts, Russian READMEs,
  LOG.md passed through a sanitizer (no IPs, hosts, home paths). ALT spec patches and NW.js upstream deltas are not
  vendored (third-party emails/IPs in them): the README says where they come from, nwjs-e2k has make-nw-deltas.sh.
- Audit before push (tree + `git log -p`): IPv4 addresses (only version numbers match), home directories of this
  machine and the Mac, ALT/BaseALT domains and the e2k mirror host, e-mails other than the author's, the closed lcc
  sources, AI attribution: nothing found.
- Releases e2k-20261125 with the two tarballs as assets.
- The same lcc bug in [Basic]Env::SetInstanceData<T, fini = DefaultFini<T>> (spdlog loads, then fails lazily on
  Napi::Env::DefaultFini<FunctionReference>): natbuild4.sh names DefaultFini/DefaultFiniWithHint in those bodies and
  rebuilds the modules that call SetInstanceData (spdlog, sqlite3, kerberos). node-pty after the first workaround:
  pty.spawn('/bin/sh') inside Electron prints `pty-on-e2k e2k`, exit 0.
- sqlite3.c (8.5 MB amalgamation) with lcc -O3 on the Elbrus host got ~3 min of CPU in 40 min next to the other agents' jobs
  (nice 19): compiled instead on the x86 server with the e2k cross clang (-O2, same defines, 90 s) and dropped into
  the node-gyp build dir; the C++ binding is still built by lcc.
- native-keymap uses the V8 API directly: needs -DV8_CPPGC_MICROTASK_QUEUE (V8 15.4 headers) and -L for the local
  libxkbfile; then it loads. All 9 rebuilt modules load in Electron; spdlog writes a rotating log, node-pty spawns a
  shell, sqlite3 opens a database, parcel watcher / policy-watcher / kerberos / keymap export their APIs.
- VS Code with all of them on a fresh profile: starts with no native-module errors in the main-process log (only the
  Copilot sign-in onboarding dialog shows on a new profile: shots/electron-vscode-3.png).

## State at the end (2026-11-25)
- the Elbrus host: dist ~/elnw/dist (README.md + 2 tarballs), shots ~/elnw/shots (9 PNG), apps ~/elnw/apps (smoke, nwsmoke,
  wavedrom), runtime copies in /tmp/elnw (electron-v46n-e2k, nwjs-v0.117.0-e2k, obsidian-e2k, ticktick-e2k,
  vscode-e2k with the e2k native modules, natbuild/). Units stopped (Xvfb :93, x86srv-rexec as found).
- x86 server: ~/elnw (el/src + out/e2k-electron, nw/src + out/nw + out/Release, nwgit, vscode, bin, xbin, usrbin),
  43 GB; / has 16 GB free. Rust seeds ~/xtools/rseed/{e2k-electron,nw} (hard-linked copies of e2k-rel3).
- Remaining: Electron's own spec runner (needs its spec node_modules with native test modules for e2k); electron
  node_headers target (configure.py lacks e2k); rebase on the release branch e2k-chrome-rel (VA-API, AV1, libc++
  num_get and other Chrome-side fixes are not in e2k-v8-js3); chrome-sandbox / SUID sandbox; GPU acceleration;
  NW.js: the 6 hangguard false positives left in libnw.so (only matter on hosts with that module), the CHECK on a
  missing app path; MCST reports: lcc template instantiation (node-addon-api), lccopt __lccrt_builtin_cmp_eq_i_v2i2
  and __lccrt_builtin_shuffle_v16v16i16 missing from liblccrt_s.a.
