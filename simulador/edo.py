"""Integradores numéricos de EDO (Unidades II y IV).

Todos los métodos comparten la firma ``integrar(f, y0, t_span, h, params=None,
metodo=...)`` y devuelven una :class:`SolucionEDO`. El campo ``n_evals`` cuenta
evaluaciones de ``f`` y ``h_hist`` guarda los pasos aceptados por RKF45.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

Funcion = Callable[[float, np.ndarray, object], np.ndarray]


@dataclass
class SolucionEDO:
    t: np.ndarray
    y: np.ndarray
    n_evals: int = 0
    h_hist: np.ndarray | None = None

    def __iter__(self):
        yield self.t
        yield self.y

    @property
    def y_final(self):
        return self.y[-1]


def _preparar(y0, t_span, h):
    y0 = np.atleast_1d(np.asarray(y0, dtype=float))
    t0, tf = float(t_span[0]), float(t_span[1])
    if tf <= t0:
        raise ValueError("t_span debe ser creciente.")
    if h <= 0:
        raise ValueError("El paso h debe ser positivo.")
    n = int(np.ceil((tf - t0) / h))
    return y0, t0, tf, h, n


def _forma(y: np.ndarray):
    return y[:, 0] if y.shape[1] == 1 else y


def _guardar(y: np.ndarray):
    return y.copy()


def integrar(
    f: Funcion,
    y0,
    t_span,
    h: float,
    params=None,
    metodo: str = "rk4",
    **kwargs,
) -> SolucionEDO:
    """Integra ``y' = f(t, y, params)`` con el método pedido."""
    metodo = metodo.lower()
    if metodo == "euler":
        return euler(f, y0, t_span, h, params, **kwargs)
    if metodo == "heun":
        return heun(f, y0, t_span, h, params, **kwargs)
    if metodo == "rk4":
        return rk4(f, y0, t_span, h, params, **kwargs)
    if metodo == "taylor2":
        return taylor2(f, y0, t_span, h, params, df=kwargs.pop("df", None), **kwargs)
    if metodo in {"euler_implicito", "euler_implícito"}:
        return euler_implicito(f, y0, t_span, h, params, **kwargs)
    if metodo == "rkf45":
        return rkf45(f, y0, t_span, h, params, **kwargs)
    raise ValueError(f"Método desconocido: {metodo}")


class _Contador:
    def __init__(self, f: Funcion, params):
        self.f = f
        self.params = params
        self.n = 0

    def __call__(self, t, y):
        self.n += 1
        return np.asarray(self.f(t, y, self.params), dtype=float)


def euler(f, y0, t_span, h, params=None) -> SolucionEDO:
    y0, t0, tf, h, n = _preparar(y0, t_span, h)
    fc = _Contador(f, params)
    t = np.empty(n + 1)
    y = np.empty((n + 1, y0.size))
    t[0], y[0] = t0, y0
    for i in range(n):
        paso = min(h, tf - t[i])
        y[i + 1] = y[i] + paso * fc(t[i], y[i])
        t[i + 1] = t[i] + paso
    return SolucionEDO(t, _forma(y), fc.n)


def heun(f, y0, t_span, h, params=None) -> SolucionEDO:
    y0, t0, tf, h, n = _preparar(y0, t_span, h)
    fc = _Contador(f, params)
    t = np.empty(n + 1)
    y = np.empty((n + 1, y0.size))
    t[0], y[0] = t0, y0
    for i in range(n):
        paso = min(h, tf - t[i])
        k1 = fc(t[i], y[i])
        k2 = fc(t[i] + paso, y[i] + paso * k1)
        y[i + 1] = y[i] + 0.5 * paso * (k1 + k2)
        t[i + 1] = t[i] + paso
    return SolucionEDO(t, _forma(y), fc.n)


def etapas_rk4(f, t, y, h):
    """Pendientes de las cuatro etapas del paso clásico de Runge–Kutta."""
    k1 = f(t, y)
    k2 = f(t + h / 2, y + h / 2 * k1)
    k3 = f(t + h / 2, y + h / 2 * k2)
    k4 = f(t + h, y + h * k3)
    return k1, k2, k3, k4


def rk4(f, y0, t_span, h, params=None) -> SolucionEDO:
    y0, t0, tf, h, n = _preparar(y0, t_span, h)
    fc = _Contador(f, params)
    t = np.empty(n + 1)
    y = np.empty((n + 1, y0.size))
    t[0], y[0] = t0, y0
    for i in range(n):
        paso = min(h, tf - t[i])
        ti, yi = t[i], y[i]
        k1, k2, k3, k4 = etapas_rk4(fc, ti, yi, paso)
        y[i + 1] = yi + (paso / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        t[i + 1] = ti + paso
    return SolucionEDO(t, _forma(y), fc.n)


def taylor2(f, y0, t_span, h, params=None, df=None) -> SolucionEDO:
    """Taylor de orden 2: ``y + h f + h²/2 (f_t + J f)``.

    ``df`` se acepta por compatibilidad, pero las derivadas se calculan por
    diferencias finitas sobre ``f`` para no exigir una segunda implementación.
    """
    del df
    y0, t0, tf, h, n = _preparar(y0, t_span, h)
    fc = _Contador(f, params)

    t = np.empty(n + 1)
    y = np.empty((n + 1, y0.size))
    t[0], y[0] = t0, y0
    eps = 1e-6
    for i in range(n):
        paso = min(h, tf - t[i])
        ti, yi = t[i], y[i]
        fv = fc(ti, yi)
        # Jacobiano J = df/dy y derivada temporal f_t
        J = np.empty((y0.size, y0.size))
        for j in range(y0.size):
            dy = np.zeros_like(yi)
            dy[j] = eps
            J[:, j] = (fc(ti, yi + dy) - fc(ti, yi - dy)) / (2 * eps)
        ft = (fc(ti + eps, yi) - fc(ti - eps, yi)) / (2 * eps)
        y[i + 1] = yi + paso * fv + 0.5 * paso * paso * (ft + J @ fv)
        t[i + 1] = ti + paso
    return SolucionEDO(t, _forma(y), fc.n)


def euler_implicito(f, y0, t_span, h, params=None, tol=1e-12, max_iter=50) -> SolucionEDO:
    """Euler implícito con Newton y Jacobiano numérico."""
    y0, t0, tf, h, n = _preparar(y0, t_span, h)
    fc = _Contador(f, params)
    t = np.empty(n + 1)
    y = np.empty((n + 1, y0.size))
    t[0], y[0] = t0, y0
    for i in range(n):
        paso = min(h, tf - t[i])
        tn, yi = t[i] + paso, y[i]
        yn = yi.copy()
        for _ in range(max_iter):
            F = fc(tn, yn) * paso + yi - yn
            if np.linalg.norm(F) <= tol * max(1.0, np.linalg.norm(yn)):
                break
            # Jacobiano numérico de F respecto a yn
            eps = 1e-7
            J = np.empty((yn.size, yn.size))
            for j in range(yn.size):
                dy = np.zeros_like(yn)
                dy[j] = eps
                J[:, j] = (fc(tn, yn + dy) * paso + yi - (yn + dy) - F) / eps
            try:
                delta = np.linalg.solve(J, -F)
            except np.linalg.LinAlgError as exc:
                raise RuntimeError("Jacobiano singular en Euler implícito") from exc
            yn = yn + delta
        else:
            raise RuntimeError("Euler implícito no convergió")
        y[i + 1] = yn
        t[i + 1] = tn
    return SolucionEDO(t, _forma(y), fc.n)


# Coeficientes clásicos de Runge-Kutta-Fehlberg 4(5)
_C = np.array([0.0, 0.25, 0.375, 12 / 13, 1.0, 0.5])
_A = np.array(
    [
        [0, 0, 0, 0, 0],
        [1 / 4, 0, 0, 0, 0],
        [3 / 32, 9 / 32, 0, 0, 0],
        [1932 / 2197, -7200 / 2197, 7296 / 2197, 0, 0],
        [439 / 216, -8, 3680 / 513, -845 / 4104, 0],
        [-8 / 27, 2, -3544 / 2565, 1859 / 4104, -11 / 40],
    ]
)
_B4 = np.array([25 / 216, 0, 1408 / 2565, 2197 / 4104, -1 / 5, 0])
_B5 = np.array([16 / 135, 0, 6656 / 12825, 28561 / 56430, -9 / 50, 2 / 55])


def rkf45(
    f,
    y0,
    t_span,
    h: float,
    params=None,
    rtol: float = 1e-8,
    atol: float = 1e-10,
    h_min: float = 1e-12,
    max_iter: int = 200000,
) -> SolucionEDO:
    """Runge-Kutta-Fehlberg 4(5) con control de paso adaptativo."""
    y = np.atleast_1d(np.asarray(y0, dtype=float))
    t0, tf = float(t_span[0]), float(t_span[1])
    if h <= 0:
        raise ValueError("h debe ser positivo.")
    fc = _Contador(f, params)
    ts, ys, hs = [t0], [y.copy()], []
    t = t0
    h_actual = h
    for _ in range(max_iter):
        if t >= tf:
            break
        h_actual = min(h_actual, tf - t)
        k = np.empty((6, y.size))
        for s in range(6):
            y_s = y + h_actual * sum(_A[s, j] * k[j] for j in range(s))
            k[s] = fc(t + _C[s] * h_actual, y_s)
        y4 = y + h_actual * (_B4 @ k)
        y5 = y + h_actual * (_B5 @ k)
        escala = atol + rtol * np.maximum(np.abs(y), np.abs(y5))
        err = np.linalg.norm((y5 - y4) / escala) / np.sqrt(y.size)
        if err == 0:
            factor = 5.0
        else:
            factor = 0.9 * err ** (-0.2)
            factor = min(5.0, max(0.2, factor))
        if err <= 1.0:
            t += h_actual
            y = y5
            ts.append(t)
            ys.append(y.copy())
            hs.append(h_actual)
        h_actual *= factor
        if h_actual < h_min:
            raise RuntimeError("RKF45 alcanzó h_min sin cumplir tolerancia")
    t_arr = np.asarray(ts)
    y_arr = np.asarray(ys)
    return SolucionEDO(t_arr, _forma(y_arr), fc.n, np.asarray(hs))
