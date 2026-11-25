"""Energía, potencia, impulso y criterio HIC (Unidad III / Fase 3)."""

from __future__ import annotations

import numpy as np

from .variables import G, OBJETIVO_SUPERVIVENCIA_G, UMBRAL_HIC, VENTANA_HIC_S


def energia_cinetica(masa_kg: float, v_m_s):
    return 0.5 * masa_kg * np.asarray(v_m_s) ** 2


def energia_potencial(masa_kg: float, altura_m, gravedad_m_s2: float = G):
    return masa_kg * gravedad_m_s2 * np.asarray(altura_m)


def energia_elastica(k_n_m: float, x_m):
    return 0.5 * k_n_m * np.asarray(x_m) ** 2


def trabajo_resorte(k_n_m: float, x_m: float) -> float:
    return float(0.5 * k_n_m * x_m**2)


def impulso(fuerza, t) -> float:
    """Integral de la fuerza respecto al tiempo (trapecio)."""
    f = np.asarray(fuerza, dtype=float)
    t = np.asarray(t, dtype=float)
    return float(np.trapezoid(f, t))


def potencia(fuerza, velocidad):
    return np.asarray(fuerza) * np.asarray(velocidad)


def potencia_pico(k_n_m: float, x, v) -> float:
    return float(np.max(np.abs(k_n_m * np.asarray(x) * np.asarray(v))))


def hic_pulso_rectangular(a_g: float, duracion_s: float, ventana_s: float = VENTANA_HIC_S) -> float:
    """HIC analítico de un pulso rectangular constante."""
    dt = min(duracion_s, ventana_s)
    return float(dt * a_g**2.5)


def hic(
    a_g,
    dt_s: float,
    ventana_s: float = VENTANA_HIC_S,
) -> float:
    """Head Injury Criterion con ventana máxima de 36 ms.

    ``a_g`` es la aceleración resultante en unidades de g. Se evalúan todas
    las ventanas de duración ``<= ventana_s`` sobre una malla uniforme.
    """
    a = np.asarray(a_g, dtype=float)
    if a.size == 0:
        return 0.0
    if dt_s <= 0:
        raise ValueError("dt_s debe ser positivo.")
    n = a.size
    max_pasos = max(1, min(n, int(round(ventana_s / dt_s))))
    prefijo = np.concatenate(([0.0], np.cumsum(a)))
    mejor = 0.0
    # Vectorizado por longitud de ventana: cada iteración evalúa todos los
    # inicios a la vez. O(n · max_pasos) pero sin bucles Python internos.
    for pasos in range(1, max_pasos + 1):
        medias = (prefijo[pasos:] - prefijo[:-pasos]) / pasos
        valores = (pasos * dt_s) * np.abs(medias) ** 2.5
        if valores.size:
            mejor = max(mejor, float(np.max(valores)))
    return mejor


def clasificar(a_max_g: float, hic_valor: float | None = None) -> str:
    """Semáforo simple: 6 g y HIC 700 como umbrales."""
    if a_max_g > OBJETIVO_SUPERVIVENCIA_G:
        return "letal"
    if hic_valor is not None and hic_valor > UMBRAL_HIC:
        return "letal"
    return "supervivencia"


def balance_energetico(v0_m_s: float, x_m: float, masa_kg: float, k_n_m: float, gravedad_m_s2: float = G) -> dict:
    """Comprueba que la energía inicial más la gravitatoria es la elástica."""
    inicial = 0.5 * masa_kg * v0_m_s**2
    gravitatoria = masa_kg * gravedad_m_s2 * x_m
    elastica = 0.5 * k_n_m * x_m**2
    return {
        "cinetica_inicial_j": float(inicial),
        "gravitatoria_j": float(gravitatoria),
        "elastica_j": float(elastica),
        "residuo_j": float(elastica - inicial - gravitatoria),
    }
