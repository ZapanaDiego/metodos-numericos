"""Cuadraturas de Newton-Cotes, Gauss-Legendre y Romberg (Unidad III)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.polynomial.legendre import leggauss


def trapecio(f: Callable[[float], float], a: float, b: float, n: int = 100) -> float:
    if n < 1:
        raise ValueError("n debe ser >= 1")
    x = np.linspace(a, b, n + 1)
    y = np.array([f(xi) for xi in x])
    return float(np.trapezoid(y, x))


def simpson_13(f, a: float, b: float, n: int = 100) -> float:
    """Simpson 1/3; ``n`` es el número de subintervalos (debe ser par)."""
    if n < 2 or n % 2:
        raise ValueError("Simpson 1/3 requiere n par >= 2")
    x = np.linspace(a, b, n + 1)
    y = np.array([f(xi) for xi in x])
    h = (b - a) / n
    return float(h / 3.0 * (y[0] + 4.0 * y[1:-1:2].sum() + 2.0 * y[2:-1:2].sum() + y[-1]))


def simpson_38(f, a: float, b: float, n: int = 99) -> float:
    """Simpson 3/8; ``n`` debe ser múltiplo de 3."""
    if n < 3 or n % 3:
        raise ValueError("Simpson 3/8 requiere n múltiplo de 3")
    x = np.linspace(a, b, n + 1)
    y = np.array([f(xi) for xi in x])
    h = (b - a) / n
    s = y[0] + y[-1]
    s += 3.0 * y[1:-1:3].sum()
    s += 3.0 * y[2:-1:3].sum()
    s += 2.0 * y[3:-1:3].sum()
    return float(3.0 * h / 8.0 * s)


def boole(f, a: float, b: float, n: int = 100) -> float:
    """Regla de Boole; ``n`` debe ser múltiplo de 4."""
    if n < 4 or n % 4:
        raise ValueError("Boole requiere n múltiplo de 4")
    x = np.linspace(a, b, n + 1)
    y = np.array([f(xi) for xi in x])
    h = (b - a) / n
    s = 7.0 * (y[0] + y[-1])
    s += 32.0 * y[1:-1:4].sum()
    s += 12.0 * y[2:-1:4].sum()
    s += 32.0 * y[3:-1:4].sum()
    s += 14.0 * y[4:-1:4].sum()
    return float(2.0 * h / 45.0 * s)


def gauss_legendre(f, a: float, b: float, n: int = 5) -> float:
    """Cuadratura de Gauss-Legendre de ``n`` nodos (exacta hasta grado 2n−1)."""
    if n < 1:
        raise ValueError("n debe ser >= 1")
    nodos, pesos = leggauss(n)
    x = 0.5 * (b - a) * nodos + 0.5 * (b + a)
    return float(0.5 * (b - a) * np.sum(pesos * np.array([f(xi) for xi in x])))


@dataclass
class ResultadoRomberg:
    valor: float
    tabla: np.ndarray
    n_evals: int
    iteraciones: int
    error_estimado: float


def romberg(
    f,
    a: float,
    b: float,
    tol: float = 1e-10,
    max_iter: int = 8,
) -> ResultadoRomberg:
    """Integración de Romberg con criterio de parada en la última diferencia."""
    tabla = np.full((max_iter, max_iter), np.nan)
    cache: dict[float, float] = {}

    def T(h: float) -> float:
        if h not in cache:
            n = int(round((b - a) / h))
            cache[h] = trapecio(f, a, b, n)
        return cache[h]

    R = np.empty((max_iter, max_iter))
    R[:] = np.nan
    R[0, 0] = T(b - a)
    n_evals = 2
    error = float("inf")
    it = 1
    for k in range(1, max_iter):
        R[k, 0] = T((b - a) / (2**k))
        n_evals += 2**k
        for j in range(1, k + 1):
            R[k, j] = R[k, j - 1] + (R[k, j - 1] - R[k - 1, j - 1]) / (4**j - 1)
        error = abs(R[k, k] - R[k - 1, k - 1])
        it = k + 1
        if error <= tol:
            break
    return ResultadoRomberg(
        valor=float(R[it - 1, it - 1]),
        tabla=R[:it, :it],
        n_evals=n_evals,
        iteraciones=it,
        error_estimado=float(error),
    )


def costo(regla: str, n: int) -> int:
    """Número de evaluaciones de una regla compuesta."""
    regla = regla.lower()
    if regla == "trapecio":
        return n + 1
    if regla == "simpson13":
        return n + 1
    if regla == "simpson38":
        return n + 1
    if regla == "boole":
        return n + 1
    if regla == "gauss":
        return n
    raise ValueError(f"Regla desconocida: {regla}")
