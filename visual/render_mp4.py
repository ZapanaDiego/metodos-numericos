"""Exporta la simulación a MP4 con ffmpeg.

Uso:
    .venv/bin/python -m visual.render_mp4 --semilla 42 --salida resultados/pelicula.mp4
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FFMpegWriter

from simulador.modelo import simular
from simulador.parametros import Escena
from visual.animacion import Reproductor
from visual.escena3d import construir_escena


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--semilla", type=int, default=42)
    parser.add_argument("--salida", type=Path, default=Path("resultados/pelicula.mp4"))
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--ancho", type=int, default=640)
    args = parser.parse_args(argv)

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    r = simular(Escena.pelicula(), n_caida=700, n_resorte=700)
    rep = Reproductor(r, fps=args.fps)

    fig = plt.figure(figsize=(args.ancho / 100, args.ancho * 0.85 / 100), dpi=100)
    ax = fig.add_subplot(111, projection="3d")
    escena = construir_escena(fig, ax)
    hud = fig.text(0.02, 0.95, "", fontsize=9, family="monospace", va="top")
    fig.suptitle("Caída de Gwen Stacy — simulación numérica", fontsize=11)

    # caída a velocidad normal y frenado en cámara ultra lenta
    t_frenado = np.linspace(r.t_tensado_s, r.t[-1], 55)
    t_caida = np.linspace(0.0, r.t_tensado_s, 75)
    tiempos = np.concatenate([t_caida, t_frenado])

    writer = FFMpegWriter(fps=args.fps, codec="libx264", bitrate=2000)
    with writer.saving(fig, str(args.salida), dpi=100):
        for t in tiempos:
            est = rep.estado(float(t))
            escena.actualizar(est.__dict__, rep.trayectoria_hasta(float(t)))
            hud.set_text(
                f"t={est.t:6.3f}s  y={est.altura_torso:5.2f}m  v={est.v:6.2f}m/s\n"
                f"a={est.a_g:6.1f}g  F={est.fuerza/1e3:6.1f}kN  HIC={est.hic:7.0f}  {est.semaforo}"
            )
            ax.view_init(elev=10, azim=-70 + 5 * np.sin(2 * np.pi * t / max(r.t[-1], 1e-9)))
            writer.grab_frame()

    plt.close(fig)
    print(f"MP4 escrito en {args.salida} ({args.salida.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
