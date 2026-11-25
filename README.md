# nwjs-e2k — NW.js для Эльбруса (e2k-v5)

Порт NW.js на архитектуру e2k (Эльбрус-8СВ, e2k-v5) с нативным JIT V8 для e2k. Здесь — серия патчей, сценарии
сборки и аргументы GN. Готовые сборки — в выпусках (Releases). Бинарных файлов в git нет.

## Версии
| компонент | версия | примечание |
|---|---|---|
| NW.js | 0.117.0 (nw.js тег nw-v0.117.0) | в оригинале Chromium 154.0.8037.58 — та же ветка M154 |
| Chromium | 154.0.8037.97 | исходники пакета ALT chromium 154.0.8037.97-alt1 + порт e2k |
| V8 | 15.4.80.20 | бэкенд e2k + правки V8 от NW.js (nwjs/v8 7d30a50b) |
| Node.js | 26.7.0 | nwjs/node c8241474, собран через GYP как libnode.so |


## Какой архив для какого процессора
| архив | процессоры | система |
|---|---|---|
| `…-linux-e2k.tar.xz` (e2k-v5) | Эльбрус-8СВ (он же 8С2, e2k-v5); 16С (e2k-v6) тоже исполняет | библиотеки из системы (ALT с glibc 2.35, ядро 6.1); RPATH = `$ORIGIN`, LD_LIBRARY_PATH не нужен |
| `…-linux-e2kv4.tar.xz` (e2k-v4) | Эльбрус-8С, 1С+ (e2k-v4); 8СВ и 16С тоже исполняют | всё своё: glibc 2.35 и библиотеки в `lib/`; после распаковки один раз `./setup.sh` (пишет путь к `lib/` в бинарники) |

Код v4 работает и на v5/v6, но без 128-битных операций (wasm SIMD выключен) и без плотной упаковки кода
Sparkplug/Maglev, поэтому на 8СВ лучше архив v5.

## Исправлено 2026-11-25
RPATH в пакете e2k-v5 указывал на корень перекрёстной сборки, и без LD_LIBRARY_PATH запуск падал
(`libXNVCtrl.so.0: cannot open shared object file`). Теперь RPATH = `$ORIGIN` (и `$ORIGIN/lib` у NW.js), правится на
месте `build/fixrpath.py`; архивы в выпуске заменены.

## e2k-v4 (Эльбрус-8С, 1С+)
Тот же NW.js на дереве Chromium e2k-v4 (сборка 25.11): `patches/chromium-e2kv4` (V8: модель процессора по IDR,
без 128-битных операций и плотной упаковки на v4; abseil, rust.gni, распределитель Rust), затем те же
`patches/nwjs-e2k`, затем `patches/nwjs-e2kv4` (libuv node-nw без io_uring на ядрах до 6.1; пустой
node26_malloc_impls, иначе двойное определение в libnw.so). Сборка `build/v4/xs-el4` с `XS_PROJ=nw4 XS_OUT=nw`
и `build/v4/args-nwjs-v4.gn`, libnode.so — тот же GYP. Пакет самодостаточный (`build/v4/pack-v4.py`, `setup.sh`).
Проверено на Эльбрусе-8С (glibc 2.29, ядро 5.10, Xvfb): `nw --version`, проверочное приложение с N-API-модулем,
WaveDrom Editor 3.7.0. fib(30) ≈ 155 мс.

## Как устроено
NW.js — это форк Chromium (nwjs/chromium.src), форк V8 (nwjs/v8), форк Node (nwjs/node) и код самого NW.js
(`content/nw`). Вместо форка Chromium мы берём **разность** NW.js относительно апстрима (1010 файлов,
`build/make-nw-deltas.sh` строит её из публичных репозиториев) и накладываем её на наше дерево Chromium 154 для e2k;
так же — разность V8 (50 файлов). Отклонено 7 кусков: 5 уже есть в 8037.97 или не нужны, 2 поправлены руками.

## Состав
- `patches/chromium-e2k/` — порт Chromium 154 и V8 на e2k (99 патчей, пути `chromium/...` от корня исходников ALT).
- `patches/nwjs-e2k/`:
  - `0001` — дерево Chromium под NW.js на e2k: строка CHROMIUM_RPATH ALT при закомментированных NW ldflags;
    распределитель Rust (крейты остаются как в сборке Chrome e2k, реализация на malloc glibc, потому что NW.js
    отключает PartitionAlloc вместо malloc); группа архивов и rlib при сборке разделяемых библиотек (libnw.so,
    GNU ld); libc++ `__config_site` Chromium (у NW.js пространство `__1`); кусок `FixSourceNWBin` в v8/src/api/api.cc.
  - `0002` — `content/nw`: без SwiftShader Vulkan на e2k, статический ffmpeg.
  - `0003` — `third_party/node-nw`: без lld, zstd без BMI2, OpenSSL без async (нет makecontext), js2c с libc++.
  Кроме того, `third_party/node-nw/deps/v8/include` заменяется ссылкой на `v8/include` (заголовки V8 14.x из Node
  не знают e2k и не совпадают по ABI с V8 15.4).
- `build/` — `args-nwjs.gn`, `xs-el` (XS_PROJ=nw XS_OUT=nw), `nw-node-gyp.sh` (GYP для libnode.so),
  `pack-nw.sh`, `hgscan.py` (см. ниже), дополнения обёрток clang и rustc.
- `scripts/nw.sh`, `examples/nwsmoke`.

## Сборка
1. Исходники ALT chromium 154.0.8037.97-alt1, `%autopatch -p1`, `patches/chromium-e2k`.
2. `content/nw` = nw.js `nw-v0.117.0`, `third_party/node-nw` = nwjs/node c82414748.
3. `build/make-nw-deltas.sh`, затем `git apply --reject -p2 nw-chromium.diff` в `src`, `git apply --reject -p1
   nw-v8.diff` в `src/v8`; патчи поддеревьев NW.js из `content/nw/patch/patch.cfg` (perfetto, icu, ffmpeg и
   devtools с `-p0`).
4. `patches/nwjs-e2k/*`.
5. `xs-el gen build/args-nwjs.gn` (каталог `out/nw` — так требует NW.js), `xs-el build nwjs` (≈31 тыс. шагов).
6. `nw-node-gyp.sh` в контейнере, `ninja -C out/Release node` (≈2 тыс. шагов), `ninja -C out/nw copy_node`.
7. `pack-nw.sh out/nw nwjs-...`.

Важные решения: `exclude_unwind_tables = false` (NW.js включает их исключение, из-за чего меняются флаги всех
крейтов Rust), `is_component_ffmpeg = false`, `cppgc_enable_object_section_gcinfo = false` (как в NW.js),
без Vulkan/Dawn/SwiftShader.

### e2k_hangguard
На стенде с модулем ядра e2k_hangguard (защита от ошибки «зависания» Эльбрус-8СВ) сканер страниц проверяет команду
с каждого 8-байтового слота, а не только с начала команды, и находит в libnw.so ложные совпадения внутри команд;
такая страница не исполняется (SIGILL). `build/hgscan.py` — тот же предикат на Python. Объекты с совпадениями
собраны с `-O1` через обёртку clang (список в LOG.md); осталось 6 мест в редком коде (Temporal, AV1-смешивание,
одна сортировка, хинтинг шрифтов в Rust).

## Запуск и что проверено
```sh
./nw --version            # nwjs 154.0.8037.97
./nw.sh examples/nwsmoke  # версии, Node в странице, wasm, N-API, снимок окна
```
- Окно, canvas, Node в странице (`os`, `fs`, `crypto`, `zlib`), Intl ru-RU, WebAssembly, `nw.App.manifest`,
  `nw.Window.capturePage`, N-API-модуль, собранный node-gyp на Эльбрусе. JIT: fib(30) ≈ 170 мс.
- WaveDrom Editor 3.7.0 (готовое приложение NW.js для x86): редактор и диаграммы работают.

Журнал — `LOG.md`.
