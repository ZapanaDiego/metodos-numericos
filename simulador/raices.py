"""Métodos de búsqueda de raíces de la Unidad I.

Todos devuelven ``(raiz, iteraciones, historial)``. El historial es una lista
de tuplas ``(iteracion, aproximacion, error)``.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def _error_abs(fx: float) -> float:
    return abs(fx)


def biseccion(
    f: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-10,
    max_iter: int = 200,
) -> tuple[float, int, list[tuple[int, float, float]]]:
    fa, fb = f(a), f(b)
    if fa == 0:
        return a, 0, [(0, a, 0.0)]
    if fb == 0:
        return b, 0, [(0, b, 0.0)]
    if fa * fb > 0:
        raise ValueError("biseccion requiere f(a)·f(b) < 0")
    historial: list[tuple[int, float, float]] = []
    for i in range(1, max_iter + 1):
        c = 0.5 * (a + b)
        fc = f(c)
        err = 0.5 * abs(b - a)
        historial.append((i, c, err))
        if err <= tol or abs(fc) <= tol:
            return c, i, historial
        if fa * fc < 0:
            b, fb = c, fc
        else:
            a, fa = c, fc
    return 0.5 * (a + b), max_iter, historial


def falsa_posicion(
    f: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-10,
    max_iter: int = 200,
) -> tuple[float, int, list[tuple[int, float, float]]]:
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("falsa_posicion requiere f(a)·f(b) < 0")
    historial = []
    c = a
    for i in range(1, max_iter + 1):
        c = (a * fb - b * fa) / (fb - fa)
        fc = f(c)
        err = abs(b - a)
        historial.append((i, c, err))
        if abs(fc) <= tol or err <= tol:
            return c, i, historial
        if fa * fc < 0:
            b, fb = c, fc
        else:
            a, fa = c, fc
    return c, max_iter, historial


def punto_fijo(
    g: Callable[[float], float],
    x0: float,
    tol: float = 1e-10,
    max_iter: int = 200,
) -> tuple[float, int, list[tuple[int, float, float]]]:
    historial = []
    x = x0
    for i in range(1, max_iter + 1):
        try:
            x_new = g(x)
        except (OverflowError, ZeroDivisionError) as exc:
            raise RuntimeError(
                "punto_fijo divergió; revise el reordenamiento"
            ) from exc
        if not np.isfinite(x_new):
            raise RuntimeError("punto_fijo divergió; revise el reordenamiento")
        err = abs(x_new - x)
        historial.append((i, x_new, err))
        if err <= tol:
            return x_new, i, historial
        x = x_new
    raise RuntimeError("punto_fijo no convergió; revise el reordenamiento")


def newton_raphson(
    f: Callable[[float], float],
    df: Callable[[float], float] | None,
    x0: float,
    tol: float = 1e-10,
    max_iter: int = 100,
) -> tuple[float, int, list[tuple[int, float, float]]]:
    historial = []
    x = x0
    for i in range(1, max_iter + 1):
        fx = f(x)
        if df is None:
            h = 1e-7 * max(1.0, abs(x))
            d = (f(x + h) - f(x - h)) / (2.0 * h)
        else:
            d = df(x)
        if d == 0:
            raise ZeroDivisionError("Derivada nula en Newton-Raphson")
        x_new = x - fx / d
        err = abs(x_new - x)
        historial.append((i, x_new, err))
        if err <= tol or abs(f(x_new)) <= tol:
            return x_new, i, historial
        x = x_new
    return x, max_iter, historial


def secante(
    f: Callable[[float], float],
    x0: float,
    x1: float,
    tol: float = 1e-10,
    max_iter: int = 100,
) -> tuple[float, int, list[tuple[int, float, float]]]:
    f0, f1 = f(x0), f(x1)
    historial = []
    for i in range(1, max_iter + 1):
        if f1 == f0:
            raise ZeroDivisionError("Secante con f(x1) = f(x0)")
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        f2 = f(x2)
        err = abs(x2 - x1)
        historial.append((i, x2, err))
        if err <= tol or abs(f2) <= tol:
            return x2, i, historial
        x0, f0 = x1, f1
        x1, f1 = x2, f2
    return x1, max_iter, historial


def t_tensado_numerico(
    altura_m: float,
    masa_kg: float,
    cd_area_m2: float,
    densidad_aire_kg_m3: float = 1.20,
    gravedad_m_s2: float = 9.81,
    tol: float = 1e-12,
) -> tuple[float, int, list[tuple[int, float, float]]]:
    """Raíz de ``y(t) - H`` para la caída con arrastre."""
    from .analitica import caida_con_arrastre, y_de_t

    t_f, _, vt = caida_con_arrastre(
        altura_m, masa_kg, cd_area_m2, densidad_aire_kg_m3, gravedad_m_s2
    )
    return biseccion(
        lambda t: float(y_de_t(t, vt, gravedad_m_s2)) - altura_m,
        0.0,
        t_f * 1.01,
        tol=tol,
    )


def k_critico_supervivencia(
    v0_m_s: float,
    masa_kg: float,
    objetivo_g: float = 6.0,
    gravedad_m_s2: float = 9.81,
    tol: float = 1e-9,
) -> tuple[float, int, list[tuple[int, float, float]]]:
    """Raíz de ``a_max(k) - objetivo_g·g``."""
    from .analitica import amax_analitica

    objetivo = objetivo_g * gravedad_m_s2
    return biseccion(
        lambda k: amax_analitica(v0_m_s, k, masa_kg, gravedad_m_s2) - objetivo,
        1e-3,
        1e7,
        tol=tol,
    )


def t_impacto_suelo(
    v0_m_s: float,
    k_n_m: float,
    masa_kg: float,
    espacio_libre_m: float,
    gravedad_m_s2: float = 9.81,
    tol: float = 1e-12,
) -> tuple[float, int, list[tuple[int, float, float]]]:
    """Primer instante en que ``x(t) = espacio_libre`` (contacto con el suelo)."""
    from .analitica import t_pico_analitico, x_de_t

    tp = t_pico_analitico(v0_m_s, k_n_m, masa_kg, gravedad_m_s2)
    f = lambda t: float(x_de_t(t, v0_m_s, k_n_m, masa_kg, gravedad_m_s2)) - espacio_libre_m
    if f(tp) < 0:
        raise ValueError("La seda no alcanza el espacio libre antes de detenerse.")
    return biseccion(f, 0.0, tp, tol=tol)


def orden_convergencia(
    errores: list[float],
) -> float:
    """Estima el orden observado a partir de tres errores consecutivos."""
    if len(errores) < 3:
        return float("nan")
    e = np.asarray(errores[-4:], dtype=float)
    e = e[e > 0]
    if len(e) < 3:
        return float("nan")
    return float(np.log(e[-1] / e[-2]) / np.log(e[-2] / e[-3]))
