"""Errores, orden observado y extrapolación de Richardson (Unidad I)."""

from __future__ import annotations

import numpy as np

EPS = np.finfo(float).eps


def error_abs(x, x_verdadero) -> float:
    return float(abs(x - x_verdadero))


def error_rel(x, x_verdadero) -> float | None:
    """Error relativo; ``None`` si el valor verdadero es indistinguible de 0."""
    if abs(x_verdadero) <= EPS * max(1.0, abs(x)):
        return None
    return float(abs(x - x_verdadero) / abs(x_verdadero))


def error_verdadero(x, x_verdadero) -> tuple[float, float | None]:
    return error_abs(x, x_verdadero), error_rel(x, x_verdadero)


def orden_observado(hs, errores) -> list[float]:
    """Orden empírico ``log(e_i/e_{i+1})/log(h_i/h_{i+1})``."""
    hs = np.asarray(hs, dtype=float)
    errores = np.asarray(errores, dtype=float)
    if hs.size != errores.size or hs.size < 2:
        raise ValueError("Se necesitan al menos dos pares (h, error).")
    ordenes = []
    for i in range(hs.size - 1):
        if errores[i] <= 0 or errores[i + 1] <= 0 or hs[i] <= 0:
            ordenes.append(float("nan"))
        else:
            ordenes.append(float(np.log(errores[i] / errores[i + 1]) / np.log(hs[i] / hs[i + 1])))
    return ordenes


def richardson(valor_h: float, valor_h2: float, p: int = 2) -> float:
    """Extrapolación de Richardson para un método de orden ``p``."""
    factor = 2**p
    return float((factor * valor_h2 - valor_h) / (factor - 1))


def error_de_redondeo(x: float) -> float:
    """Error absoluto de representar ``x`` en doble precisión."""
    return float(abs(np.float64(x) - x))


def epsilon_maquina() -> float:
    return float(EPS)


def tabla_convergencia(hs, errores) -> list[dict]:
    ordenes = orden_observado(hs, errores)
    filas = []
    for i, (h, e) in enumerate(zip(hs, errores, strict=True)):
        filas.append(
            {
                "h": float(h),
                "error": float(e),
                "orden": float(ordenes[i]) if i < len(ordenes) else float("nan"),
            }
        )
    return filas
