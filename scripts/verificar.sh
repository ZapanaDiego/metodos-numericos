#!/usr/bin/env bash
# Verificación completa: regenera figuras y tablas, y corre la suite.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== limpieza de resultados =="
rm -f resultados/*.png resultados/*.csv

echo "== experimentos =="
for e in e1_convergencia e2_rigidez e3_energia_hic e4_umbral e5_latigazo \
         e6_rozamiento e7_montecarlo e8_sensibilidad e9_redondeo e10_raices; do
  .venv/bin/python -m experimentos."$e"
done

echo "== referencia =="
.venv/bin/python scripts/generar_referencia.py

echo "== MP4 y frame =="
.venv/bin/python -m visual.render_mp4 --semilla 42 --salida resultados/pelicula.mp4
ffmpeg -y -v error -ss 2.0 -i resultados/pelicula.mp4 -frames:v 1 resultados/frame_mp4.png

echo "== pytest =="
.venv/bin/python -m pytest -q

echo "== benchmark 3D =="
.venv/bin/python -m experimentos.b0_benchmark3d

echo "OK: todo regenerado y en verde"
