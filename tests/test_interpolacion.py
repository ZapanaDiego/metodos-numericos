"""I23: interpolación y splines."""

import numpy as np
import pytest

from simulador.interpolacion import (
    lagrange,
    minimos_cuadrados,
    newton,
    spline_cubico,
    spline_cubico_natural,
)


def test_spline_reproduce_cubico():
    x = np.linspace(0, 2, 8)
    y = 2 * x**3 - x + 1
    s = spline_cubico(x, y)
    xx = np.linspace(0, 2, 200)
    assert np.max(np.abs(s(xx) - (2 * xx**3 - xx + 1))) < 1e-10


def test_lagrange_y_newton_coinciden():
    x = np.linspace(-1, 1, 7)
    y = np.cos(x)
    l = lagrange(x, y)
    _, n = newton(x, y)
    xx = np.linspace(-1, 1, 50)
    assert np.allclose(l(xx), n(xx), rtol=1e-12, atol=1e-12)


def test_spline_theta_fino():
    t = np.arange(0, 0.1, 1e-3)
    theta = np.sin(2 * np.pi * 5 * t)
    s = spline_cubico(t, theta)
    tt = np.arange(0, 0.1, 1e-4)
    assert np.max(np.abs(s(tt) - np.sin(2 * np.pi * 5 * tt))) < 1e-6


def test_minimos_cuadrados_recupera_tendencia():
    rng = np.random.default_rng(3)
    x = np.linspace(0, 10, 100)
    y = 2 * x + 1 + rng.normal(0, 0.1, x.size)
    coef, f = minimos_cuadrados(x, y, 1)
    assert coef[0] == pytest.approx(2.0, abs=0.05)
    assert coef[1] == pytest.approx(1.0, abs=0.2)


def test_runge_lagrange_oscila_y_spline_no():
    x = np.linspace(-1, 1, 11)
    y = 1 / (1 + 25 * x**2)
    l = lagrange(x, y)
    s = spline_cubico_natural(x, y)
    xx = np.linspace(-1, 1, 1000)
    exacto = 1 / (1 + 25 * xx**2)
    assert np.max(np.abs(l(xx) - exacto)) > np.max(np.abs(s(xx) - exacto))
    assert np.max(np.abs(s(xx) - exacto)) < 0.2
