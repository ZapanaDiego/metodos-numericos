"""e2: rigidez numérica del resorte.

Demuestra que Euler explícito es estable solo si ``h < 2/ω`` y que Euler
implícito lo es para todo paso probado. Genera ``e2_rigidez.png`` y
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
    h_crit = 2.0 / omega
    f = lambda t, y, p=None: np.array([y[1], -(k / m) * y[0]])

    hs = np.geomspace(1e-3, 0.2, 40)
    amp_exp, amp_imp = [], []
    for h in hs:
        se = euler(f, [1.0, 0.0], (0.0, 2.0), float(h))
        si = euler_implicito(f, [1.0, 0.0], (0.0, 2.0), float(h))
        amp_exp.append(float(np.max(np.abs(se.y[:, 0]))))
        amp_imp.append(float(np.max(np.abs(si.y[:, 0]))))

    with (RESULTADOS / "e2_tabla.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["h_s", "amplitud_euler_explicito", "amplitud_euler_implicito", "h_critico_s"])
        for h, ae, ai in zip(hs, amp_exp, amp_imp, strict=True):
            writer.writerow([f"{h:.6e}", f"{ae:.6e}", f"{ai:.6e}", f"{h_crit:.6e}"])

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(hs, amp_exp, "o-", color=COLORES["rojo"], label="Euler explícito", lw=1.8, ms=3)
    ax.loglog(hs, amp_imp, "s-", color=COLORES["azul"], label="Euler implícito", lw=1.8, ms=3)
    ax.axvline(h_crit, color=COLORES["gris"], ls="--", label=f"h_crit = 2/ω = {h_crit*1e3:.1f} ms")
    ax.set_xlabel("paso h (s)")
    ax.set_ylabel("máx |x| en 2 s")
    ax.set_title("Rigidez del resorte: estabilidad de Euler")
    ax.legend()
    guardar(fig, "e2_rigidez.png")

    print(f"e2: omega={omega:.3f} rad/s, h_crit={h_crit*1e3:.2f} ms")
    print(f"  amplitud explícita en h=0.2: {amp_exp[-1]:.3e}")
    print(f"  amplitud implícita en h=0.2: {amp_imp[-1]:.3e}")


if __name__ == "__main__":
    main()
