"""e4: umbral de supervivencia y región factible.

Con la caída base (con aire) se barre ``k`` y se calcula ``a_max`` y el
estiramiento. La conclusión es que la región ``a <= 6 g`` y ``x <= espacio
libre`` es vacía: no hay rigidez posible que salve a Gwen en esta geometría.
"""

from __future__ import annotations

import csv

import numpy as np
from matplotlib import pyplot as plt

from simulador.analitica import (
    amax_en_g,
    caida_con_arrastre,
    elongacion_desde_k,
    k_para_aceleracion,
)
from simulador.elasticidad import E_a_k, k_a_E
from simulador.graficas import COLORES, RESULTADOS, configurar, guardar
from simulador.parametros import Escena


def main() -> None:
    configurar()
    escena = Escena.pelicula()
    m = escena.cuerpo.masa_kg
    g = escena.gravedad_m_s2
    _, v0, _ = caida_con_arrastre(
        escena.caida_m,
        m,
        escena.cuerpo.cd_area_m2,
        escena.cuerpo.densidad_aire_kg_m3,
        g,
    )
    _, v0_sin, _ = caida_con_arrastre(escena.caida_m, m, 0.0, 1.2, g)
    k6 = k_para_aceleracion(v0, m, 6.0, g)
    x6 = elongacion_desde_k(v0, k6, m, g)
    k6_sin = k_para_aceleracion(v0_sin, m, 6.0, g)
    x6_sin = elongacion_desde_k(v0_sin, k6_sin, m, g)
    espacio = escena.espacio_libre_m

    ks = np.geomspace(10.0, 5e5, 400)
    x = np.array([elongacion_desde_k(v0, float(k), m, g) for k in ks])
    a = np.array([amax_en_g(v0, float(k), m, g) for k in ks])
    E = np.array([E_a_k(float(k), escena.telarana.longitud_m, escena.telarana.area_m2) for k in ks])

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(ks, a, color=COLORES["azul"], label="a_max(k)")
    ax.axhline(6.0, color=COLORES["rojo"], ls="--", label="6 g")
    ax.axvline(k6, color=COLORES["naranja"], ls=":", label=f"k = {k6:.1f} N/m")
    ax.set_xlabel("k (N/m)")
    ax.set_ylabel("a_max (g)")
    ax.set_title("Aceleración pico frente a la rigidez (con aire)")
    ax.legend()
    guardar(fig, "e4_umbral.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(ks, x, color=COLORES["verde"], label="x_max(k)")
    ax.axhline(espacio, color=COLORES["rojo"], ls="--", label=f"espacio libre = {espacio:.2f} m")
    ax.axvline(k6, color=COLORES["naranja"], ls=":", label=f"k(6 g) = {k6:.1f}")
    ax.set_xlabel("k (N/m)")
    ax.set_ylabel("estiramiento máximo (m)")
    ax.set_title("Estiramiento frente a la rigidez")
    ax.legend()
    guardar(fig, "e4_x_vs_k.png")

    # Región factible en el plano (k, x): a<=6g y x<=espacio
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.loglog(ks, x, color=COLORES["azul"], lw=2, label="x_max(k) con aire")
    ax.axhline(espacio, color=COLORES["rojo"], ls="--", label="suelo: x = 1.60 m")
    ax.axvline(k6, color=COLORES["naranja"], ls=":", label=f"k(6 g) = {k6:.1f}")
    ax.fill_between(ks, 0.01, np.minimum(x, espacio), where=(a <= 6), color=COLORES["verde"], alpha=0.18, label="a<=6g")
    ax.fill_between(ks, 0.01, np.minimum(x, espacio), where=(x <= espacio), color=COLORES["azul"], alpha=0.10, label="x<=espacio")
    # banda de seda real: E en [1,10] GPa
    for Emin, Emax, alpha in [(1e9, 10e9, 0.12)]:
        kmin = E_a_k(Emin, escena.telarana.longitud_m, escena.telarana.area_m2)
        kmax = E_a_k(Emax, escena.telarana.longitud_m, escena.telarana.area_m2)
        ax.axvspan(kmin, kmax, color=COLORES["morado"], alpha=alpha, label="seda real (1-10 GPa)")
    ax.set_xlabel("k (N/m)")
    ax.set_ylabel("x (m)")
    ax.set_ylim(0.01, 1e3)
    ax.set_title("Región factible: no hay intersección")
    ax.legend(fontsize=8, loc="upper right")
    ax.text(
        0.02,
        0.03,
        "La zona verde (6 g) exige x = 12.6 m;\nla zona azul (suelo) exige x <= 1.6 m.\nIntersección vacía.",
        transform=ax.transAxes,
        fontsize=8,
        bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
    )
    guardar(fig, "e4_supervivencia.png")

    filas = [
        ("v0_con_aire_m_s", v0),
        ("k_6g_con_aire_n_m", k6),
        ("x_6g_con_aire_m", x6),
        ("deformacion_6g_con_aire", x6 / escena.telarana.longitud_m),
        ("E_seda_6g_con_aire_pa", k6 * escena.telarana.longitud_m / escena.telarana.area_m2),
        ("k_6g_sin_aire_n_m", k6_sin),
        ("x_6g_sin_aire_m", x6_sin),
        ("espacio_libre_m", espacio),
        ("k_minimo_para_no_tocar_suelo_n_m", 12693.5),
        ("E_minimo_para_no_tocar_suelo_pa", k_a_E(12693.5, escena.telarana.longitud_m, escena.telarana.area_m2)),
    ]
    with (RESULTADOS / "e4_tabla.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["cantidad", "valor"])
        writer.writerows(filas)

    print(f"e4: k(6g)={k6:.2f} N/m, x={x6:.2f} m, espacio={espacio:.2f} m")
    print(f"    k mínimo para no tocar suelo={12693.5:.1f} N/m, E={k_a_E(12693.5, 42.0, 2.5e-5)/1e9:.2f} GPa")
    print("    región factible: VACÍA")


if __name__ == "__main__":
    main()
