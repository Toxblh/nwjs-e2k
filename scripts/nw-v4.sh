#!/bin/sh
# Запуск NW.js для e2k-v4: без песочницы, программная отрисовка. Сначала один раз ./setup.sh.
# Использование: ./nw.sh <каталог приложения | app.nw> [ключи]
D=$(cd "$(dirname "$0")" && pwd)
exec "$D/nw" --no-sandbox ${NW_GPU:---disable-gpu} "$@"
