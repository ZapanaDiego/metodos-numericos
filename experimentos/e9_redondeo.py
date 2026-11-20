"""e9: curva en V del error de truncamiento y redondeo."""

from __future__ import annotations

import csv

import numpy as np
from matplotlib import pyplot as plt

from simulador.diferenciacion import central
from simulador.errores import epsilon_maquina
from simulador.graficas import COLORES, RESULTADOS, configurar, guardar


def main() -> None:
    configurar()
    f = np.sin
    df = np.cos
    x = 1.0
    exacto = df(x)
    hs = np.logspace(-1, -16, 61)
    errores = [abs(central(f, x, float(h)) - exacto) for h in hs]
    i = int(np.argmin(errores))
    with (RESULTADOS / "e9_redondeo.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["h", "error_central", "eps_maquina"])
        for h, e in zip(hs, errores, strict=True):
            writer.writerow([f"{h:.3e}", f"{e:.6e}", f"{epsilon_maquina():.3e}"])

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(hs, errores, "o-", color=COLORES["azul"], ms=3, lw=1.2, label="error de la diferencia central")
    ax.axvline(hs[i], color=COLORES["rojo"], ls="--", label=f"mínimo en h={hs[i]:.1e}")
    ax.axhline(epsilon_maquina(), color=COLORES["gris"], ls=":", label="eps de máquina")
    ax.set_xlabel("h")
    ax.set_ylabel("error absoluto")
    ax.set_title("Curva en V: truncamiento (izquierda) vs redondeo (derecha)")
    ax.legend(fontsize=8)
    guardar(fig, "e9_redondeo.png")
    print(f"e9: mínimo en h={hs[i]:.3e}, error={errores[i]:.3e}")


if __name__ == "__main__":
    main()
