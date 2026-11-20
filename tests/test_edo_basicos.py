"""I08/I09: orden de los integradores, RKF45 y estabilidad implícita."""

import numpy as np
import pytest

from simulador.edo import euler, euler_implicito, heun, integrar, rk4, rkf45, taylor2


def f_lineal(t, y, params=None):
    return -2.0 * y


def exacta(t):
    return np.exp(-2.0 * t)


def error(metodo, h):
    sol = integrar(f_lineal, [1.0], (0.0, 1.0), h, metodo=metodo)
    return abs(float(sol.y_final) - exacta(1.0))


@pytest.mark.parametrize("metodo,orden", [("euler", 1.0), ("heun", 2.0), ("rk4", 4.0), ("taylor2", 2.0)])
def test_orden_observado(metodo, orden):
    e1 = error(metodo, 0.1)
    e2 = error(metodo, 0.05)
    e3 = error(metodo, 0.025)
    o1 = np.log2(e1 / e2)
    o2 = np.log2(e2 / e3)
    assert o1 == pytest.approx(orden, abs=0.2)
    assert o2 == pytest.approx(orden, abs=0.2)


def test_rkf45_mas_barato_que_rk4():
    sol = rkf45(f_lineal, [1.0], (0.0, 5.0), 0.1, rtol=1e-8, atol=1e-11)
    assert abs(float(sol.y_final) - exacta(5.0)) < 1e-6
    ref = rk4(f_lineal, [1.0], (0.0, 5.0), 1e-3)
    assert sol.n_evals < ref.n_evals
    assert sol.h_hist is not None and len(sol.h_hist) > 0


def test_euler_implicito_estable_en_resorte_rigido():
    omega2 = 259965.0 / 50.0
    f = lambda t, y, p=None: np.array([y[1], -omega2 * y[0]])
    h = 0.1
    explicito = euler(f, [1.0, 0.0], (0.0, 5.0), h)
    implicito = euler_implicito(f, [1.0, 0.0], (0.0, 5.0), h)
    assert np.max(np.abs(explicito.y)) > 1e3  # diverge
    assert np.all(np.isfinite(implicito.y))
    assert np.max(np.abs(implicito.y)) < 20.0  # transitorio acotado, sin crecer
    assert abs(implicito.y[-1, 0]) < abs(implicito.y[0, 0])


def test_rkf45_sin_paso_negativo():
    sol = rkf45(f_lineal, [1.0], (0.0, 1.0), 0.5, rtol=1e-10)
    assert np.all(np.diff(sol.t) > 0)
