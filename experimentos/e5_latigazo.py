"""e5: latigazo del cuerpo anclado en el torso."""

from __future__ import annotations

import csv

import numpy as np
from matplotlib import pyplot as plt

from simulador.articulado import momentos, perfil_momentos, posiciones
from simulador.graficas import COLORES, RESULTADOS, configurar, guardar
from simulador.modelo import simular
from simulador.parametros import Escena


def main() -> None:
    configurar()
    r = simular(Escena.pelicula())
    cuerpo = r.escena.cuerpo
    t, mc, mh = perfil_momentos(r, cuerpo)
    cabeza, torso, cadera = posiciones(r.altura_torso_m, cuerpo)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(r.t, torso, color=COLORES["azul"], label="torso")
    ax.plot(r.t, cabeza, color=COLORES["rojo"], label="cabeza")
    ax.plot(r.t, cadera, color=COLORES["verde"], label="cadera")
    ax.axhline(0, color="black", lw=1, label="suelo")
    ax.axvline(r.t_tensado_s, color=COLORES["naranja"], ls=":", label="tensado")
    ax.set_xlabel("t (s)")
    ax.set_ylabel("altura sobre el suelo (m)")
    ax.set_title("El torso se detiene a 1.20 m; los segmentos no tocan el suelo")
    ax.legend(fontsize=8)
    ax.set_ylim(bottom=-0.2)
    guardar(fig, "e5_articulado.png")

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(t, mc / 1e3, color=COLORES["rojo"], label="momento cervical")
    ax.plot(t, mh / 1e3, color=COLORES["azul"], label="momento de cadera")
    ax.axhspan(0.030, 0.090, color=COLORES["verde"], alpha=0.18, label="tolerancia cervical 30-90 N·m")
    ax.set_xlabel("t (s)")
    ax.set_ylabel("momento (kN·m)")
    ax.set_title("Momentos inerciales durante el frenado")
    ax.legend(fontsize=8)
    guardar(fig, "e5_momentos.png")

    m_pico = momentos(r.a_max_m_s2, cuerpo)
    with (RESULTADOS / "e5_tabla.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["cantidad", "valor"])
        writer.writerow(["a_pico_g", r.a_max_g])
        writer.writerow(["momento_cuello_kn_m", m_pico.cuello_kn_m])
        writer.writerow(["momento_cadera_kn_m", m_pico.cadera_n_m / 1e3])
        writer.writerow(["altura_min_torso_m", float(np.min(torso))])
        writer.writerow(["altura_min_cabeza_m", float(np.min(cabeza))])
        writer.writerow(["altura_min_cadera_m", float(np.min(cadera))])

    print(f"e5: M_cuello={m_pico.cuello_kn_m:.3f} kN·m, M_cadera={m_pico.cadera_n_m/1e3:.2f} kN·m")


if __name__ == "__main__":
    main()
