"""Formas cerradas de las fases de caída y de la telaraña.

Convención: ``y`` es la distancia caída hacia abajo; ``v = dy/dt`` es positiva
hacia abajo. En la fase elástica ``x`` es el estiramiento de la seda y la
aceleración neta hacia arriba es ``a = k x / m - g``; para el daño se reporta
su magnitud ``|a|``.

Todas las funciones son puras y vectorizadas.
"""

from __future__ import annotations

import numpy as np

G = 9.81


# --------------------------------------------------------------------- caída
def caida_sin_aire(altura_m: float, gravedad_m_s2: float = G) -> tuple[float, float]:
    """Tiempo y velocidad final de una caída libre desde el reposo."""
    if altura_m < 0:
        raise ValueError("La altura no puede ser negativa.")
    t = np.sqrt(2.0 * altura_m / gravedad_m_s2)
    return float(t), float(gravedad_m_s2 * t)


def velocidad_terminal(
    masa_kg: float,
    cd_area_m2: float,
    densidad_aire_kg_m3: float = 1.20,
    gravedad_m_s2: float = G,
) -> float:
    """Velocidad terminal del arrastre cuadrático."""
    if cd_area_m2 <= 0:
        return np.inf
    return float(np.sqrt(2.0 * masa_kg * gravedad_m_s2 / (densidad_aire_kg_m3 * cd_area_m2)))


def caida_con_arrastre(
    altura_m: float,
    masa_kg: float,
    cd_area_m2: float,
    densidad_aire_kg_m3: float = 1.20,
    gravedad_m_s2: float = G,
) -> tuple[float, float, float]:
    """Tiempo, velocidad final y velocidad terminal con arrastre cuadrático.

    ``m dv/dt = m g - c v²`` con ``c = ½ ρ Cd A``. Si ``Cd·A = 0`` se
    devuelve la solución sin aire con ``v_t = inf``.
    """
    if cd_area_m2 <= 0:
        t, v = caida_sin_aire(altura_m, gravedad_m_s2)
        return t, v, np.inf
    vt = velocidad_terminal(masa_kg, cd_area_m2, densidad_aire_kg_m3, gravedad_m_s2)
    exponente = gravedad_m_s2 * altura_m / (vt * vt)
    t = (vt / gravedad_m_s2) * np.arccosh(np.exp(exponente))
    v = vt * np.tanh(gravedad_m_s2 * t / vt)
    return float(t), float(v), float(vt)


def v_de_t(t, velocidad_terminal_m_s: float, gravedad_m_s2: float = G):
    """Velocidad de caída con arrastre en función del tiempo."""
    t = np.asarray(t, dtype=float)
    if not np.isfinite(velocidad_terminal_m_s):
        return gravedad_m_s2 * t
    return velocidad_terminal_m_s * np.tanh(gravedad_m_s2 * t / velocidad_terminal_m_s)


def y_de_t(t, velocidad_terminal_m_s: float, gravedad_m_s2: float = G):
    """Distancia caída con arrastre en función del tiempo."""
    t = np.asarray(t, dtype=float)
    if not np.isfinite(velocidad_terminal_m_s):
        return 0.5 * gravedad_m_s2 * t * t
    vt = velocidad_terminal_m_s
    argumento = gravedad_m_s2 * t / vt
    # log(cosh(z)) estable para z grande
    z = np.abs(argumento)
    log_cosh = z + np.log1p(np.exp(-2.0 * z)) - np.log(2.0)
    return (vt * vt / gravedad_m_s2) * log_cosh


# ------------------------------------------------------------------- resorte
def k_desde_elongacion(
    v0_m_s: float,
    x_m: float,
    masa_kg: float,
    gravedad_m_s2: float = G,
) -> float:
    """Rigidez que detiene el cuerpo tras estirar ``x`` (balance energético)."""
    if x_m <= 0:
        raise ValueError("El estiramiento debe ser positivo.")
    return float(masa_kg * (v0_m_s**2 + 2.0 * gravedad_m_s2 * x_m) / (x_m**2))


def elongacion_desde_k(
    v0_m_s: float,
    k_n_m: float,
    masa_kg: float,
    gravedad_m_s2: float = G,
) -> float:
    """Estiramiento máximo para una rigidez dada (raíz positiva de energía)."""
    if k_n_m <= 0:
        raise ValueError("k debe ser positivo.")
    # ½ k x² = ½ m v0² + m g x  ->  k x² - 2 m g x - m v0² = 0
    a = k_n_m
    b = -2.0 * masa_kg * gravedad_m_s2
    c = -masa_kg * v0_m_s**2
    discriminante = b * b - 4.0 * a * c
    return float((-b + np.sqrt(discriminante)) / (2.0 * a))


def omega(v0_m_s: float, k_n_m: float, masa_kg: float) -> float:
    """Frecuencia angular del oscilador (el argumento v0 se ignora)."""
    del v0_m_s
    return float(np.sqrt(k_n_m / masa_kg))


def x_de_t(t, v0_m_s: float, k_n_m: float, masa_kg: float, gravedad_m_s2: float = G):
    """Estiramiento de la seda en la fase elástica."""
    t = np.asarray(t, dtype=float)
    w = np.sqrt(k_n_m / masa_kg)
    return (gravedad_m_s2 / (w * w)) * (1.0 - np.cos(w * t)) + (v0_m_s / w) * np.sin(w * t)


def v_resorte_de_t(t, v0_m_s: float, k_n_m: float, masa_kg: float, gravedad_m_s2: float = G):
    """Velocidad del torso en la fase elástica (positiva hacia abajo)."""
    t = np.asarray(t, dtype=float)
    w = np.sqrt(k_n_m / masa_kg)
    return (gravedad_m_s2 / w) * np.sin(w * t) + v0_m_s * np.cos(w * t)


def a_resorte_de_t(t, v0_m_s: float, k_n_m: float, masa_kg: float, gravedad_m_s2: float = G):
    """Aceleración neta del torso; positiva hacia arriba es ``-a``."""
    t = np.asarray(t, dtype=float)
    w = np.sqrt(k_n_m / masa_kg)
    # a_down = g - (k/m) x; la magnitud de frenado es (k/m)x - g
    x = x_de_t(t, v0_m_s, k_n_m, masa_kg, gravedad_m_s2)
    return gravedad_m_s2 - (k_n_m / masa_kg) * x


def amax_analitica(
    v0_m_s: float,
    k_n_m: float,
    masa_kg: float,
    gravedad_m_s2: float = G,
) -> float:
    """Aceleración máxima (m/s²) durante el frenado."""
    return float(np.sqrt(gravedad_m_s2**2 + (k_n_m / masa_kg) * v0_m_s**2))


def amax_en_g(
    v0_m_s: float,
    k_n_m: float,
    masa_kg: float,
    gravedad_m_s2: float = G,
) -> float:
    """Aceleración máxima expresada en g."""
    return amax_analitica(v0_m_s, k_n_m, masa_kg, gravedad_m_s2) / gravedad_m_s2


def k_para_aceleracion(
    v0_m_s: float,
    masa_kg: float,
    objetivo_g: float,
    gravedad_m_s2: float = G,
) -> float:
    """Rigidez que produce una aceleración máxima objetivo (en g)."""
    # a_max² = g² + (k/m) v0²  ->  k = m (a² - g²)/v0²
    a = objetivo_g * gravedad_m_s2
    if a <= gravedad_m_s2:
        raise ValueError("El objetivo debe superar 1 g.")
    return float(masa_kg * (a * a - gravedad_m_s2**2) / (v0_m_s**2))


def t_pico_analitico(
    v0_m_s: float,
    k_n_m: float,
    masa_kg: float,
    gravedad_m_s2: float = G,
) -> float:
    """Primer instante con ``ẋ = 0`` (máximo estiramiento)."""
    w = np.sqrt(k_n_m / masa_kg)
    # ẋ = (g/w) sin(wt) + v0 cos(wt) = 0
    return float((np.pi - np.arctan(v0_m_s * w / gravedad_m_s2)) / w)


def t_pico_sin_gravedad(v0_m_s: float, k_n_m: float, masa_kg: float) -> float:
    """Caso académico sin gravedad: ``t = π/(2ω)``."""
    del v0_m_s
    return float(np.pi / (2.0 * np.sqrt(k_n_m / masa_kg)))


def energia_resorte(v0_m_s: float, x_m: float, masa_kg: float, gravedad_m_s2: float = G) -> float:
    """Energía absorbida por la seda al estirarse ``x``."""
    return float(0.5 * masa_kg * v0_m_s**2 + masa_kg * gravedad_m_s2 * x_m)


def potencia_pico(v0_m_s: float, k_n_m: float, masa_kg: float, gravedad_m_s2: float = G) -> tuple[float, float]:
    """Potencia mecánica pico real ``max(k x ẋ)`` y su instante.

    No es ``F_max·v0``: la fuerza máxima y la velocidad máxima ocurren en
    instantes distintos.
    """
    tp = t_pico_analitico(v0_m_s, k_n_m, masa_kg, gravedad_m_s2)
    t = np.linspace(0.0, tp, 20001)
    x = x_de_t(t, v0_m_s, k_n_m, masa_kg, gravedad_m_s2)
    v = v_resorte_de_t(t, v0_m_s, k_n_m, masa_kg, gravedad_m_s2)
    p = k_n_m * x * v
    i = int(np.argmax(p))
    return float(p[i]), float(t[i])


def tiempo_para_elongacion(
    x_objetivo_m: float,
    v0_m_s: float,
    k_n_m: float,
    masa_kg: float,
    gravedad_m_s2: float = G,
) -> float:
    """Primer instante en que la seda alcanza ``x_objetivo``.

    Se usa bisección sobre la forma cerrada; útil para el evento de impacto
    contra el suelo (``x = espacio_libre``).
    """
    from scipy.optimize import brentq

    if x_objetivo_m <= 0:
        return 0.0
    tp = t_pico_analitico(v0_m_s, k_n_m, masa_kg, gravedad_m_s2)
    f = lambda t: float(x_de_t(t, v0_m_s, k_n_m, masa_kg, gravedad_m_s2)) - x_objetivo_m
    if f(tp) < 0:
        # la seda nunca llega a ese estiramiento
        return float("nan")
    return float(brentq(f, 0.0, tp, xtol=1e-14, rtol=1e-14))
