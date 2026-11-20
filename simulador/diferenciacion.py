"""Diferenciación numérica: adelante, atrás, central y segunda derivada."""

from __future__ import annotations

from collections.abc import Callable


def adelante(f: Callable[[float], float], x: float, h: float) -> float:
    return float((f(x + h) - f(x)) / h)


def atras(f: Callable[[float], float], x: float, h: float) -> float:
    return float((f(x) - f(x - h)) / h)


def central(f: Callable[[float], float], x: float, h: float) -> float:
    return float((f(x + h) - f(x - h)) / (2.0 * h))


def segunda_derivada(f: Callable[[float], float], x: float, h: float) -> float:
    return float((f(x + h) - 2.0 * f(x) + f(x - h)) / (h * h))


def error_adelante(f, df_exacta, x, h) -> float:
    return abs(adelante(f, x, h) - df_exacta(x))


def error_atras(f, df_exacta, x, h) -> float:
    return abs(atras(f, x, h) - df_exacta(x))


def error_central(f, df_exacta, x, h) -> float:
    return abs(central(f, x, h) - df_exacta(x))


def error_segunda(f, d2_exacta, x, h) -> float:
    return abs(segunda_derivada(f, x, h) - d2_exacta(x))
