"""Interpolación: Lagrange, Newton, spline cúbico y mínimos cuadrados."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from scipy.interpolate import CubicSpline


def lagrange(xn, yn) -> Callable[[float | np.ndarray], float | np.ndarray]:
    xn = np.asarray(xn, dtype=float)
    yn = np.asarray(yn, dtype=float)

    def evaluar(x):
        x = np.asarray(x, dtype=float)
        total = np.zeros_like(x, dtype=float)
        for i in range(xn.size):
            base = np.ones_like(x, dtype=float)
            for j in range(xn.size):
                if j != i:
                    base *= (x - xn[j]) / (xn[i] - xn[j])
            total += yn[i] * base
        return total

    return evaluar


def diferencias_divididas(xn, yn) -> np.ndarray:
    xn = np.asarray(xn, dtype=float)
    yn = np.asarray(yn, dtype=float)
    n = xn.size
    tabla = np.zeros((n, n))
    tabla[:, 0] = yn
    for j in range(1, n):
        for i in range(n - j):
            tabla[i, j] = (tabla[i + 1, j - 1] - tabla[i, j - 1]) / (xn[i + j] - xn[i])
    return tabla[0, :]


def newton(xn, yn) -> tuple[np.ndarray, Callable[[float | np.ndarray], float | np.ndarray]]:
    xn = np.asarray(xn, dtype=float)
    coef = diferencias_divididas(xn, yn)

    def evaluar(x):
        x = np.asarray(x, dtype=float)
        total = np.full_like(x, coef[-1], dtype=float)
        for k in range(len(coef) - 2, -1, -1):
            total = coef[k] + (x - xn[k]) * total
        return total

    return coef, evaluar


def spline_cubico(xn, yn) -> CubicSpline:
    """Spline cúbico not-a-knot: reproduce exactamente polinomios cúbicos."""
    return CubicSpline(np.asarray(xn, dtype=float), np.asarray(yn, dtype=float), bc_type="not-a-knot")


def spline_cubico_natural(xn, yn) -> CubicSpline:
    """Spline natural (segunda derivada nula en los extremos).

    No reproduce un cúbico exacto cerca de los bordes; se conserva para
    comparar el efecto de la condición de frontera.
    """
    return CubicSpline(np.asarray(xn, dtype=float), np.asarray(yn, dtype=float), bc_type="natural")


def minimos_cuadrados(x, y, grado: int = 1):
    coef = np.polyfit(np.asarray(x, dtype=float), np.asarray(y, dtype=float), grado)
    return coef, lambda xx: np.polyval(coef, xx)


def error_maximo(f, xn, yn) -> float:
    xn = np.asarray(xn, dtype=float)
    yn = np.asarray(yn, dtype=float)
    return float(np.max(np.abs(np.asarray(f(xn)) - yn)))
