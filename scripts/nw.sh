#!/bin/sh
# Запуск NW.js для e2k: без песочницы (chrome-sandbox не собран), программная отрисовка.
# Использование: ./nw.sh <каталог приложения | app.nw> [ключи]
D=$(cd "$(dirname "$0")" && pwd)
export LD_LIBRARY_PATH="$D/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$D/nw" --no-sandbox ${NW_GPU:---disable-gpu} "$@"
