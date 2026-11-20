"""e7: Monte Carlo del escenario base."""

from __future__ import annotations

import csv

import numpy as np
from matplotlib import pyplot as plt

from simulador.estocastico import simular_ensemble
from simulador.graficas import COLORES, RESULTADOS, configurar, guardar


def main() -> None:
    configurar()
    e = simular_ensemble(n=2000, semilla=42)
    campos = [
        ("a_max_g", "aceleración pico (g)", COLORES["rojo"]),
        ("hic", "HIC (pulso constante)", COLORES["morado"]),
        ("x_max_m", "estiramiento máximo (m)", COLORES["verde"]),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, (campo, etiqueta, color) in zip(axes, campos, strict=True):
        v = getattr(e, campo)
        ax.hist(v, bins=40, color=color, alpha=0.75, edgecolor="white")
        st = e.estadisticas(campo)
        for p, ls in [(st["p5"], ":"), (st["p50"], "-"), (st["p95"], ":")]:
            ax.axvline(p, color="black", ls=ls, lw=1)
        ax.set_title(etiqueta, fontsize=9)
        ax.set_yticks([])
    fig.suptitle("Monte Carlo (n=2000): percentiles p5/p50/p95", fontsize=11)
    guardar(fig, "e7_montecarlo.png")

    filas = []
    for campo, etiqueta, _ in campos:
        st = e.estadisticas(campo)
        for clave, valor in st.items():
            filas.append((f"{campo}.{clave}", valor))
    filas.append(("fraccion_hic_mayor_700", e.fraccion("hic", 700.0)))
    filas.append(("fraccion_a_mayor_6g", e.fraccion("a_max_g", 6.0)))
    with (RESULTADOS / "e7_tabla.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["cantidad", "valor"])
        writer.writerows(filas)

    print(f"e7: a_max p50={np.percentile(e.a_max_g, 50):.1f} g")
    print(f"    HIC p50={np.percentile(e.hic, 50):.0f}, fracción HIC>700={e.fraccion('hic', 700.0):.3f}")
    print(f"    x p50={np.percentile(e.x_max_m, 50):.2f} m")


if __name__ == "__main__":
    main()
