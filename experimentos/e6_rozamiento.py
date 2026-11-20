"""e6: efecto de la orientación y del arrastre."""

from __future__ import annotations

import csv

import numpy as np
from matplotlib import pyplot as plt

from simulador.analitica import (
    amax_en_g,
    caida_con_arrastre,
    caida_sin_aire,
    energia_resorte,
    k_desde_elongacion,
    t_pico_analitico,
)
from simulador.graficas import COLORES, RESULTADOS, configurar, guardar


def main() -> None:
    configurar()
    m, H, x = 50.0, 42.0, 0.40
    orientaciones = [
        ("De cabeza", 0.10),
        ("De pie", 0.25),
        ("De lado", 0.40),
        ("Plana", 0.60),
        ("Espalda extendida", 0.70),
    ]
    filas = []
    nombres, v0s, amaxs, hics, energias = [], [], [], [], []
    for nombre, cd in orientaciones:
        _, v0, _ = caida_con_arrastre(H, m, cd)
        k = k_desde_elongacion(v0, x, m)
        a = amax_en_g(v0, k, m)
        tp = t_pico_analitico(v0, k, m)
        hic = tp * a**2.5
        E = energia_resorte(v0, x, m)
        filas.append((nombre, cd, v0, k, a, hic, E))
        nombres.append(nombre)
        v0s.append(v0)
        amaxs.append(a)
        hics.append(hic)
        energias.append(E)

    _, v0_sin = caida_sin_aire(H)
    k_sin = k_desde_elongacion(v0_sin, x, m)
    a_sin = amax_en_g(v0_sin, k_sin, m)
    filas.append(("Sin aire", 0.0, v0_sin, k_sin, a_sin, t_pico_analitico(v0_sin, k_sin, m) * a_sin**2.5, energia_resorte(v0_sin, x, m)))

    with (RESULTADOS / "e6_tabla.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["orientacion", "cd_area_m2", "v0_m_s", "k_n_m", "a_max_g", "hic_constante", "energia_j"])
        for fila in filas:
            writer.writerow([fila[0], f"{fila[1]:.2f}", f"{fila[2]:.3f}", f"{fila[3]:.1f}", f"{fila[4]:.2f}", f"{fila[5]:.1f}", f"{fila[6]:.1f}"])

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(range(len(nombres)), v0s, "o-", color=COLORES["azul"], label="v al tensarse")
    ax1.set_xticks(range(len(nombres)))
    ax1.set_xticklabels(nombres, rotation=20, ha="right", fontsize=8)
    ax1.set_ylabel("v0 (m/s)", color=COLORES["azul"])
    ax2 = ax1.twinx()
    ax2.plot(range(len(nombres)), hics, "s--", color=COLORES["rojo"], label="HIC constante")
    ax2.set_ylabel("HIC (pulso constante)", color=COLORES["rojo"])
    ax1.set_title("Orientación: la velocidad varía poco, el HIC se amplifica")
    guardar(fig, "e6_rozamiento.png")

    print("e6: orientación -> v0, a_max, HIC")
    for fila in filas:
        print(f"  {fila[0]:18s} v={fila[2]:6.2f} m/s  a={fila[4]:6.1f} g  HIC={fila[5]:9.0f}")


if __name__ == "__main__":
    main()
