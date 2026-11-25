# Additions to the e2k cross clang wrapper (bash; the wrapper builds a `tail` array of extra flags that go after
# "$@"). The wrapper itself is the one of the e2k Chromium build: MCST clang 21.1.1 + lccopt (lcc 1.29.16 back end),
# with the e2k-rmw-fence and e2k-i65-fix pass plugins.

# node's tools/js2c.cc: MCST clang + lccopt does not finish at -O1/-O2 (>20 min); js2c runs once at build time.
case " $* " in *node_js2c/*|*node_js2c.*) tail+=(-O0);; esac

# lccopt lowers a <2 x i2> vector compare in cc::SnapContainerData::FindSnapPosition to
# __lccrt_builtin_cmp_eq_i_v2i2, which no liblccrt_s.a defines (undefined at the link of the snapshot generator).
case " $* " in *" -o obj/cc/cc/scroll_snap_data.o "*) tail+=(-fno-vectorize -fno-slp-vectorize);; esac

# Every compile has a time limit; on timeout it is retried once locally at -O1 (a hung distcc job or a source that
# lccopt cannot finish at -O2 must not stall the build for hours).
#   timeout -k 20 ${XS_CC_TIMEOUT:-900} distcc $self "$@"; rc=$?
#   [ $rc = 124 ] || [ $rc = 137 ] || exit $rc
#   exec timeout -k 20 ${XS_CC_TIMEOUT:-900} clang "$@" -O1
