"""Error y coste de Euler y RK4 en la caída y el frenado."""
import csv

import matplotlib.pyplot as plt
import numpy as np

from simulador.graficas import COLORES, RESULTADOS, configurar, guardar
from simulador.mediciones import energias
from simulador.modelo import simular
from simulador.parametros import Computo, Escena
from simulador.variables import METODO_DEFAULT, PASO_BASE_S, PASOS_CONVERGENCIA_S

MAGNITUDES = ("t_tensado_s", "v0_m_s", "t_pico_s", "x_max_m", "f_max_n", "p_max_w", "energia_j")
PASOS = PASOS_CONVERGENCIA_S


def perfiles():
    """Exporta la corrida del visor y destaca el primer cero de velocidad."""
    r = simular(Escena.pelicula(), computo=Computo(PASO_BASE_S, METODO_DEFAULT))
    tau = 1000 * (r.t - r.t_tensado_s)
    x = r.elongacion_m
    tension = r.k_n_m * x
    potencia = tension * r.v_m_s
    balance = energias(r)
    columnas = {"tiempo_s": r.t, "desde_tensado_ms": tau, "fase": r.fase,
                "altura_m": r.altura_torso_m, "velocidad_m_s": r.v_m_s,
                "aceleracion_m_s2": r.a_m_s2, "elongacion_m": x, "tension_n": tension,
                "potencia_seda_w": potencia, **balance}
    with (RESULTADOS / "e11_perfiles.csv").open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo, lineterminator="\n")
        escritor.writerow(columnas)
        escritor.writerows(zip(*columnas.values(), strict=True))

    azul, rojo = COLORES["azul"], COLORES["rojo"]
    evento = COLORES["dorado"]
    frenado = tau >= -4
    t_cero = 1000 * r.t_pico_s
    fig, (caida, velocidad, fuerza) = plt.subplots(
        3, 1, figsize=(9.4, 7.7), height_ratios=(1, 1.16, 1.16),
    )
    caida.set_title("Caída completa", loc="left", weight="bold")
    caida.plot(r.t, r.v_m_s, color=azul, lw=2.4)
    caida.axvline(r.t_tensado_s, color=evento, ls="--", lw=1.4)
    caida.scatter(r.t_tensado_s, r.v0_m_s, color=evento, zorder=4)
    caida.annotate(f"Tensado: {r.v0_m_s:.3f} m/s", (r.t_tensado_s, r.v0_m_s),
                   xytext=(2.2, 12), arrowprops={"arrowstyle": "->", "color": evento})
    caida.set(xlabel="Tiempo desde el inicio (s)", ylabel="Velocidad (m/s)",
              xlim=(0, r.t[-1] + 0.06))

    velocidad.set_title("Frenado ampliado", loc="left", weight="bold")
    velocidad.plot(tau[frenado], r.v_m_s[frenado], color=azul, lw=2.4)
    velocidad.axhline(0, color=COLORES["gris"], lw=0.9)
    velocidad.scatter(t_cero, 0, color=azul, zorder=4)
    velocidad.annotate(f"v = 0 a los {t_cero:.2f} ms", (t_cero, 0),
                       xytext=(10, 5), arrowprops={"arrowstyle": "->", "color": azul})
    velocidad.set(ylabel="Velocidad (m/s)")

    fuerza.set_title("Tensión en el mismo intervalo", loc="left", weight="bold")
    f_max_kn = r.f_max_n / 1000
    fuerza.plot(tau[frenado], tension[frenado] / 1000, color=rojo, lw=2.4)
    fuerza.scatter(t_cero, f_max_kn, color=rojo, zorder=4)
    fuerza.annotate(f"Tensión máxima: {f_max_kn:.2f} kN", (t_cero, f_max_kn),
                    xytext=(10, 33), arrowprops={"arrowstyle": "->", "color": rojo})
    fuerza.set(xlabel="Tiempo desde el tensado (ms)", ylabel="Tensión (kN)",
               ylim=(-4, 89))
    for ax in (velocidad, fuerza):
        ax.set_xlim(-4, tau[-1] + 1.3)
        ax.axvline(0, color=evento, ls="--", lw=1.4)
        ax.axvline(t_cero, color=COLORES["gris"], ls=":", lw=1.4)

    guardar(fig, "e11_velocidad_tension.png")


def barrer():
    """Compara las mismas EDO y los mismos parámetros en ambos escenarios."""
    filas = []
    for caso, escena in (("base", Escena.pelicula()), ("sin_aire", Escena.sin_aire())):
        ref = simular(escena)
        for metodo in ("euler", "rk4"):
            previos = {}
            for h in PASOS:
                dato = simular(escena, computo=Computo(h, metodo))
                for nombre in MAGNITUDES:
                    valor, referencia = getattr(dato, nombre), getattr(ref, nombre)
                    error = abs(valor - referencia)
                    previo = previos.get(nombre, 0)
                    filas.append(dict(caso=caso, metodo=metodo, paso_s=h, evaluaciones=dato.evaluaciones,
                                      magnitud=nombre, valor=valor, referencia=referencia, error=error,
                                      error_porcentual=100 * error / abs(referencia) if referencia else "",
                                      orden=np.log2(previo / error) if error and previo else ""))
                    previos[nombre] = error
    return filas


def main():
    configurar()
    perfiles()
    filas = barrer()
    with (RESULTADOS / "e11_caida.csv").open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=filas[0].keys(), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(filas)
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    for metodo in ("euler", "rk4"):
        datos = [f for f in filas if f["caso"] == "base" and f["metodo"] == metodo
                 and f["magnitud"] == "x_max_m"]
        errores = [f["error"] for f in datos]
        axs[0].loglog(PASOS, errores, "o-", label=metodo.upper())
        axs[1].loglog([f["evaluaciones"] for f in datos], errores, "o-", label=metodo.upper())
    for ax, etiqueta in zip(axs, ("Paso h (s)", "Evaluaciones de la EDO"), strict=True):
        ax.set(xlabel=etiqueta, ylabel="Error absoluto en elongación (m)")
        ax.legend()
    fig.tight_layout()
    guardar(fig, "e11_caida.png")


if __name__ == "__main__":
    main()
