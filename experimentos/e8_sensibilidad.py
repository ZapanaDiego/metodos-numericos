"""e8: sensibilidad (diagrama de tornado) de a_max y HIC."""

from __future__ import annotations

import csv

import numpy as np
from matplotlib import pyplot as plt

from simulador.analitica import (
    amax_en_g,
    caida_con_arrastre,
    k_desde_elongacion,
    t_pico_analitico,
)
from simulador.graficas import COLORES, RESULTADOS, configurar, guardar


def _modelo(m, cd, H, k_escala):
    _, v0, _ = caida_con_arrastre(H, m, cd)
    k = k_desde_elongacion(v0, 0.40, m) * k_escala
    a = amax_en_g(v0, k, m)
    hic = t_pico_analitico(v0, k, m) * a**2.5
    return a, hic


def main() -> None:
    configurar()
    base = dict(m=50.0, cd=0.60, H=42.0, k_escala=1.0)
    a0, hic0 = _modelo(**base)
    parametros = [
        ("masa", "m", 0.10),
        ("Cd·A", "cd", 0.10),
        ("altura de caída", "H", 0.10),
        ("rigidez k", "k_escala", 0.20),
    ]
    filas = []
    nombres, bajos, altos = [], [], []
    for etiqueta, clave, delta in parametros:
        resultados = []
        for factor in (1 - delta, 1 + delta):
            p = dict(base)
            p[clave] = p[clave] * factor
            a, hic = _modelo(**p)
            resultados.append(hic - hic0)
        nombres.append(etiqueta)
        bajos.append(resultados[0])
        altos.append(resultados[1])
        filas.append((etiqueta, resultados[0], resultados[1]))

    orden = np.argsort(np.abs(np.array(altos) - np.array(bajos)))
    nombres = [nombres[i] for i in orden]
    bajos = [bajos[i] for i in orden]
    altos = [altos[i] for i in orden]

    fig, ax = plt.subplots(figsize=(8, 4.8))
    y = np.arange(len(nombres))
    ax.barh(y, bajos, color=COLORES["azul"], alpha=0.8, label="-10 % / -20 %")
    ax.barh(y, altos, color=COLORES["rojo"], alpha=0.8, label="+10 % / +20 %")
    ax.set_yticks(y)
    ax.set_yticklabels(nombres)
    ax.axvline(0, color="black", lw=1)
    ax.set_xlabel("cambio en HIC respecto al caso base")
    ax.set_title(f"Tornado de sensibilidad (HIC base = {hic0:.0f})")
    ax.legend()
    guardar(fig, "e8_sensibilidad.png")

    with (RESULTADOS / "e8_tabla.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["parametro", "delta_hic_bajo", "delta_hic_alto"])
        writer.writerows(filas)

    print(f"e8: a_max base={a0:.1f} g, HIC base={hic0:.0f}")
    for n, b, a in zip(nombres, bajos, altos, strict=True):
        print(f"  {n:18s} ΔHIC = [{b:+.0f}, {a:+.0f}]")


if __name__ == "__main__":
    main()
