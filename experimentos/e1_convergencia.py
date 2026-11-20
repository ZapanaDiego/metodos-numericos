"""e1: convergencia de los integradores y coste computacional.

Genera ``resultados/e1_convergencia.png``, ``e1_tabla.csv`` y
``e1_costo.png``. La EDO de prueba es ``y' = -2y``, ``y(0)=1``, con solución
exacta ``e^{-2t}``.
"""

from __future__ import annotations

import csv

import numpy as np
from matplotlib import pyplot as plt

from simulador.edo import integrar, rkf45
from simulador.graficas import COLORES, RESULTADOS, configurar, guardar
from simulador.errores import orden_observado


def f(t, y, params=None):
    return -2.0 * y


def exacta(t):
    return np.exp(-2.0 * t)


def main() -> None:
    configurar()
    metodos = {
        "Euler": ("euler", COLORES["rojo"]),
        "Heun": ("heun", COLORES["naranja"]),
        "Taylor 2": ("taylor2", COLORES["dorado"]),
        "RK4": ("rk4", COLORES["azul"]),
        "Euler implícito": ("euler_implicito", COLORES["morado"]),
    }
    hs = np.array([0.2, 0.1, 0.05, 0.025, 0.0125, 0.00625])
    filas = []
    datos = {}
    for nombre, (metodo, color) in metodos.items():
        errores = []
        evaluaciones = []
        for h in hs:
            sol = integrar(f, [1.0], (0.0, 1.0), float(h), metodo=metodo)
            errores.append(abs(float(sol.y_final) - exacta(1.0)))
            evaluaciones.append(sol.n_evals)
        ordenes = orden_observado(hs, errores)
        datos[nombre] = (hs, errores, evaluaciones, color)
        for i, h in enumerate(hs):
            filas.append(
                {
                    "metodo": nombre,
                    "h": f"{h:.6g}",
                    "error": f"{errores[i]:.6e}",
                    "orden": f"{ordenes[i]:.3f}" if i < len(ordenes) else "",
                    "evaluaciones": evaluaciones[i],
                }
            )

    # RKF45: error frente a evaluaciones para varias tolerancias
    tolerancias = [1e-4, 1e-5, 1e-6, 1e-7, 1e-8, 1e-10]
    rkf_pts = []
    for tol in tolerancias:
        sol = rkf45(f, [1.0], (0.0, 1.0), 0.1, rtol=tol, atol=tol * 1e-3)
        err = abs(float(sol.y_final) - exacta(1.0))
        rkf_pts.append((sol.n_evals, err, tol))
        filas.append(
            {
                "metodo": "RKF45",
                "h": "adaptativo",
                "error": f"{err:.6e}",
                "orden": "",
                "evaluaciones": sol.n_evals,
            }
        )

    with (RESULTADOS / "e1_tabla.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["metodo", "h", "error", "orden", "evaluaciones"])
        writer.writeheader()
        writer.writerows(filas)

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for nombre, (h, err, _, color) in datos.items():
        ax.loglog(h, err, "o-", color=color, label=nombre, lw=1.8, ms=4)
    hh = np.array([hs.min(), hs.max()])
    referencia = datos["Euler"][1][0]
    for pendiente, color in [(1, "#999999"), (2, "#bbbbbb"), (4, "#dddddd")]:
        ax.loglog(hh, referencia * (hh / hh[0]) ** pendiente, "--", color=color, lw=1)
    ax.set_xlabel("paso h (s)")
    ax.set_ylabel("error absoluto en t=1")
    ax.set_title("Convergencia: y' = -2y, y(0)=1")
    ax.legend(fontsize=8, ncol=2)
    guardar(fig, "e1_convergencia.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    for nombre, (_, err, ev, color) in datos.items():
        ax.loglog(ev, err, "o-", color=color, label=nombre, lw=1.8, ms=4)
    ax.loglog([p[0] for p in rkf_pts], [p[1] for p in rkf_pts], "s--", color=COLORES["verde"], label="RKF45 (adaptativo)")
    ax.set_xlabel("evaluaciones de f")
    ax.set_ylabel("error absoluto")
    ax.set_title("Coste computacional: error frente a evaluaciones")
    ax.legend(fontsize=8)
    guardar(fig, "e1_costo.png")

    print("e1: escritos e1_convergencia.png, e1_tabla.csv, e1_costo.png")
    for nombre, (_, err, _, _) in datos.items():
        print(f"  {nombre:16s} error(h=0.00625) = {err[-1]:.3e}")


if __name__ == "__main__":
    main()
