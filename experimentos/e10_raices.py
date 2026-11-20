"""e10: tabla de convergencia de los cinco métodos de raíces."""

from __future__ import annotations

import csv

import numpy as np
from matplotlib import pyplot as plt

from simulador.graficas import COLORES, RESULTADOS, configurar, guardar
from simulador.raices import (
    biseccion,
    falsa_posicion,
    newton_raphson,
    punto_fijo,
    secante,
    t_tensado_numerico,
    k_critico_supervivencia,
)


def f(x):
    return x**3 - 2 * x - 5


def df(x):
    return 3 * x**2 - 2


def main():
    configurar()
    metodos = [
        ("Bisección", lambda: biseccion(f, 1, 3, tol=1e-12)),
        ("Falsa posición", lambda: falsa_posicion(f, 1, 3, tol=1e-12)),
        ("Newton", lambda: newton_raphson(f, df, 2.0, tol=1e-12)),
        ("Secante", lambda: secante(f, 1.0, 3.0, tol=1e-12)),
        ("Punto fijo", lambda: punto_fijo(lambda x: (2 * x + 5) ** (1 / 3), 2.0, tol=1e-12)),
    ]
    fig, ax = plt.subplots(figsize=(8, 5))
    filas = []
    for (nombre, ejecutar), color in zip(metodos, COLORES.values(), strict=False):
        raiz, it, hist = ejecutar()
        errores = [h[2] for h in hist]
        ax.semilogy(range(1, len(errores) + 1), errores, "o-", label=f"{nombre} ({it} it)", color=color, ms=3, lw=1.2)
        for (i, x, e) in hist:
            filas.append((nombre, i, x, e))
    ax.set_xlabel("iteración")
    ax.set_ylabel("error estimado")
    ax.set_title("Convergencia de los cinco métodos de raíces")
    ax.legend(fontsize=8)
    guardar(fig, "e10_raices.png")

    t_t, it_t, _ = t_tensado_numerico(42.0, 50.0, 0.6)
    k6, it_k, _ = k_critico_supervivencia(28.70609691337365, 50.0, 6.0)
    with (RESULTADOS / "e10_raices.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["metodo", "iteracion", "raiz", "error"])
        for fila in filas:
            writer.writerow([fila[0], fila[1], f"{fila[2]:.12g}", f"{fila[3]:.3e}"])
        writer.writerow(["aplicacion_t_tensado", it_t, f"{t_t:.12g}", ""])
        writer.writerow(["aplicacion_k_6g", it_k, f"{k6:.12g}", ""])
    print(f"e10: t_tensado={t_t:.9f} s ({it_t} it), k(6g)={k6:.4f} N/m ({it_k} it)")


if __name__ == "__main__":
    main()
