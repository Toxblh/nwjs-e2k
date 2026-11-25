# Additions to the e2k-v4 clang wrapper (the v4 one already has -march=elbrus-v4, the scroll_snap_data fix and the
# per-compile timeout). The app executables get a long placeholder PT_INTERP and an RPATH reserve, so that
# setinterp.py can bind them to the glibc + libraries shipped in lib/ of the package (8C hosts run glibc 2.29).
case " $* " in *" -o ./electron "*|*" -o ./chrome_crashpad_handler "*|*" -o ./nw "*)
  case " $* " in *" -c "*) ;; *)
    P=/opt/e2k-app/lib$(printf '/%.0s' $(seq 160))
    tail+=("-Wl,--dynamic-linker=$P/ld-linux.so.2" "-Wl,-rpath=\$ORIGIN:\$ORIGIN/lib:/opt/e2k-app/LIB$(printf '/%.0s' $(seq 160))");;
  esac;;
esac
case " $* " in *node_js2c/*|*node_js2c.*) tail+=(-O0 -D__OPTIMIZE_SIZE__=1);; esac
