"""e3: energía, potencia, HIC y coste de las cuadraturas."""

from __future__ import annotations

import csv

import numpy as np
from matplotlib import pyplot as plt

from simulador.energia import energia_cinetica, energia_elastica, energia_potencial, hic
from simulador.graficas import COLORES, RESULTADOS, configurar, guardar
from simulador.integracion import (
    boole,
    gauss_legendre,
    romberg,
    simpson_13,
    simpson_38,
    trapecio,
)
from simulador.modelo import simular
from simulador.parametros import Escena


def main() -> None:
    configurar()
    r = simular(Escena.pelicula())
    m = r.escena.cuerpo.masa_kg
    g = r.escena.gravedad_m_s2
    t = r.t
    v = r.v_m_s
    altura = r.altura_torso_m
    x = np.maximum(r.escena.h_ancla_m - r.escena.telarana.longitud_m - altura, 0.0)

    ec = energia_cinetica(m, v) / 1e3
    ep = energia_potencial(m, altura, g) / 1e3
    ee = energia_elastica(r.k_n_m, x) / 1e3
    total = ec + ep + ee

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(t, ec, color=COLORES["rojo"], label="cinética")
    ax.plot(t, ep, color=COLORES["azul"], label="potencial")
    ax.plot(t, ee, color=COLORES["verde"], label="elástica")
    ax.plot(t, total, color=COLORES["gris"], ls="--", label="total")
    ax.axvline(r.t_tensado_s, color=COLORES["naranja"], ls=":", label="tensado")
    ax.set_xlabel("t (s)")
    ax.set_ylabel("energía (kJ)")
    ax.set_title("Balance energético de la caída y el frenado")
    ax.legend(fontsize=8)
    guardar(fig, "e3_energia.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(t, r.potencia_w / 1e6, color=COLORES["morado"], label="P(t) = F·v")
    i = int(np.argmax(r.potencia_w))
    ax.plot(t[i], r.potencia_w[i] / 1e6, "o", color=COLORES["rojo"], label=f"pico {r.potencia_w[i]/1e6:.3f} MW")
    ax.set_xlabel("t (s)")
    ax.set_ylabel("potencia (MW)")
    ax.set_title("Potencia instantánea entregada al cuerpo")
    ax.legend()
    guardar(fig, "e3_potencia.png")

    duraciones = np.linspace(0.005, 0.12, 100)
    valores = [0.036 * 158.62**2.5 if d >= 0.036 else d * 158.62**2.5 for d in duraciones]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(duraciones * 1e3, valores, color=COLORES["rojo"], label="pulso constante 158.6 g")
    ax.axhline(700, color=COLORES["gris"], ls="--", label="umbral HIC 700")
    ax.set_xlabel("duración del pulso (ms)")
    ax.set_ylabel("HIC")
    ax.set_title("HIC frente a la duración (ventana máxima 36 ms)")
    ax.legend()
    guardar(fig, "e3_hic.png")

    reglas = [
        ("Trapecio", lambda f, a, b, n: trapecio(f, a, b, n)),
        ("Simpson 1/3", lambda f, a, b, n: simpson_13(f, a, b, n)),
        ("Simpson 3/8", lambda f, a, b, n: simpson_38(f, a, b, n)),
        ("Boole", lambda f, a, b, n: boole(f, a, b, n)),
        ("Gauss n", lambda f, a, b, n: gauss_legendre(f, a, b, n)),
    ]
    f = np.sin
    exacto = 2.0
    fig, ax = plt.subplots(figsize=(8, 5))
    filas = []
    for nombre, regla in reglas:
        ns = [4, 8, 16, 32, 64, 128]
        if nombre == "Simpson 3/8":
            ns = [6, 12, 24, 48, 96]
        if nombre == "Boole":
            ns = [8, 16, 32, 64, 128]
        if nombre == "Gauss n":
            ns = [1, 2, 3, 4, 5, 6, 8, 10, 12]
        errs, costos = [], []
        for n in ns:
            try:
                valor = regla(f, 0.0, np.pi, n)
            except ValueError:
                continue
            errs.append(abs(valor - exacto))
            costos.append(n if nombre != "Gauss n" else n)
        ax.loglog(costos, errs, "o-", label=nombre, lw=1.6, ms=3)
        for n, e in zip(ns, errs, strict=False):
            filas.append({"regla": nombre, "n": n, "error": f"{e:.6e}"})

    rb = romberg(f, 0.0, np.pi, tol=1e-12)
    ax.loglog([rb.n_evals], [abs(rb.valor - exacto) + 1e-16], "*", color=COLORES["rojo"], ms=12, label="Romberg")
    ax.set_xlabel("evaluaciones de f")
    ax.set_ylabel("error absoluto")
    ax.set_title("Cuadraturas: error frente a evaluaciones")
    ax.legend(fontsize=8)
    guardar(fig, "e3_cuadraturas.png")

    with (RESULTADOS / "e3_tabla.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["cantidad", "valor"])
        writer.writerow(["energia_kJ", r.energia_j / 1e3])
        writer.writerow(["potencia_pico_MW", r.p_max_w / 1e6])
        writer.writerow(["tiempo_pico_ms", r.t_pico_s * 1e3])
        writer.writerow(["a_max_g", r.a_max_g])
        for fila in filas:
            writer.writerow([f"{fila['regla']} n={fila['n']}", fila["error"]])

    print(f"e3: E={r.energia_j/1e3:.3f} kJ, Pmax={r.p_max_w/1e6:.3f} MW")


if __name__ == "__main__":
    main()
