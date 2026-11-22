"""e2: rigidez numérica del resorte.

Compara el crecimiento de energía con Euler explícito y el amortiguamiento
numérico con Euler implícito en un oscilador conservativo. Genera ``e2_rigidez.png`` y
``e2_tabla.csv``.
"""

from __future__ import annotations

import csv

import numpy as np
from matplotlib import pyplot as plt

from simulador.edo import euler, euler_implicito
from simulador.graficas import COLORES, RESULTADOS, configurar, guardar


def main() -> None:
    configurar()
    k = 259965.0
    m = 50.0
    omega = np.sqrt(k / m)
    f = lambda t, y, p=None: np.array([y[1], -(k / m) * y[0]])

    hs = np.geomspace(1e-3, 0.2, 40)
    amp_exp, amp_imp = [], []
    for h in hs:
        se = euler(f, [1.0, 0.0], (0.0, 2.0), float(h))
        si = euler_implicito(f, [1.0, 0.0], (0.0, 2.0), float(h))
        amp_exp.append(float(se.y[-1, 0]**2 + (se.y[-1, 1]/omega)**2))
        amp_imp.append(float(si.y[-1, 0]**2 + (si.y[-1, 1]/omega)**2))

    with (RESULTADOS / "e2_tabla.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["h_s", "energia_relativa_explicito", "energia_relativa_implicito"])
        for h, ae, ai in zip(hs, amp_exp, amp_imp, strict=True):
            writer.writerow([f"{h:.6e}", f"{ae:.6e}", f"{ai:.6e}"])

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(hs, amp_exp, "o-", color=COLORES["rojo"], label="Euler explícito", lw=1.8, ms=3)
    ax.loglog(hs, amp_imp, "s-", color=COLORES["azul"], label="Euler implícito", lw=1.8, ms=3)
    ax.axhline(1, color="gray", ls="--", label="energía exacta")
    ax.set_xlabel("paso h (s)")
    ax.set_ylabel("E(2 s) / E(0)")
    ax.set_title("Rigidez del resorte: estabilidad de Euler")
    ax.legend()
    guardar(fig, "e2_rigidez.png")

    print(f"e2: omega={omega:.3f} rad/s")
    print(f"  energía relativa explícita en h=0.2: {amp_exp[-1]:.3e}")
    print(f"  energía relativa implícita en h=0.2: {amp_imp[-1]:.3e}")


if __name__ == "__main__":
    main()
