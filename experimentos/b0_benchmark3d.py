"""b0: benchmark de mplot3d antes de construir la escena.

Mide fps de un redibujado completo con ~200 polígonos y 7 segmentos. Si no
alcanza 25 fps a 800x600, la app usa el renderizador por proyección propia.
"""

from __future__ import annotations

import time

import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def escena(ax):
    rng = np.random.default_rng(0)
    polys = []
    for _ in range(200):
        c = rng.uniform([-10, -10, 0], [10, 10, 60])
        d = rng.uniform(0.5, 3.0, 3)
        x0, y0, z0 = c
        dx, dy, dz = d
        polys.append(
            [
                (x0, y0, z0),
                (x0 + dx, y0, z0),
                (x0 + dx, y0 + dy, z0),
                (x0, y0 + dy, z0),
                (x0, y0, z0 + dz),
                (x0 + dx, y0, z0 + dz),
                (x0 + dx, y0 + dy, z0 + dz),
                (x0, y0 + dy, z0 + dz),
            ]
        )
    caras = []
    for p in polys:
        caras.extend(
            [
                [p[0], p[1], p[2], p[3]],
                [p[4], p[5], p[6], p[7]],
                [p[0], p[1], p[5], p[4]],
                [p[2], p[3], p[7], p[6]],
                [p[1], p[2], p[6], p[5]],
                [p[3], p[0], p[4], p[7]],
            ]
        )
    col = Poly3DCollection(caras, facecolor="#7f8c8d", edgecolor="#2c3e50", alpha=0.5)
    ax.add_collection3d(col)
    lineas = []
    for i in range(7):
        (ln,) = ax.plot([0, 1], [0, 1], [0, i], color="red", lw=2)
        lineas.append(ln)
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.set_zlim(0, 70)
    return col, lineas


def medir(ancho, alto, frames=20):
    fig = plt.figure(figsize=(ancho / 100, alto / 100), dpi=100)
    ax = fig.add_subplot(111, projection="3d")
    col, lineas = escena(ax)
    fig.canvas.draw()
    t0 = time.perf_counter()
    for k in range(frames):
        for i, ln in enumerate(lineas):
            ln.set_data_3d([0, 1], [0, 1], [k * 0.1, i + k * 0.1])
        col.set_alpha(0.4 + 0.01 * (k % 10))
        fig.canvas.draw()
    dt = time.perf_counter() - t0
    plt.close(fig)
    return frames / dt


def main():
    print("b0: benchmark mplot3d (redibujado completo)")
    for ancho, alto in [(640, 480), (800, 600), (1024, 768)]:
        fps = medir(ancho, alto, frames=12)
        print(f"  {ancho}x{alto}: {fps:.1f} fps")
    print("  criterio: >= 25 fps a 800x600 usa mplot3d")


if __name__ == "__main__":
    main()
