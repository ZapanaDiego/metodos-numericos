"""b1: benchmark del maniquí low-poly y la escena oscura."""

from __future__ import annotations

import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from simulador.modelo import simular
from simulador.parametros import Escena
from visual.animacion import Reproductor
from visual.escena3d import construir_escena


def medir(ancho: int, alto: int, frames: int = 12) -> float:
    r = simular(Escena.pelicula(), n_caida=400, n_resorte=400)
    fig = plt.figure(figsize=(ancho / 100, alto / 100), dpi=100)
    ax = fig.add_subplot(111, projection="3d")
    escena = construir_escena(fig, ax, r)
    rep = Reproductor(r)
    tiempos = np.linspace(0, r.t[-1], frames)
    fig.canvas.draw()
    t0 = time.perf_counter()
    for t in tiempos:
        est = rep.estado(float(t))
        escena.actualizar(est.__dict__, rep.trayectoria_hasta(float(t)))
        fig.canvas.draw()
    dt = time.perf_counter() - t0
    plt.close(fig)
    return frames / dt


def main():
    print("b1: benchmark del maniquí low-poly")
    for ancho, alto in [(640, 480), (800, 600), (1024, 768)]:
        fps = medir(ancho, alto)
        print(f"  {ancho}x{alto}: {fps:.1f} fps")
    print("  criterio de la app: >= 20 fps a 800x600; si no, LOD o Canvas")


if __name__ == "__main__":
    main()
