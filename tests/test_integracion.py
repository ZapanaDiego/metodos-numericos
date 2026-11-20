"""I13: cuadraturas de Newton-Cotes, Gauss y Romberg."""

import numpy as np
import pytest

from simulador.integracion import (
    boole,
    gauss_legendre,
    romberg,
    simpson_13,
    simpson_38,
    trapecio,
)


def test_x_cubo_exacto_en_simpson():
    f = lambda x: x**3
    for regla in (simpson_13, simpson_38):
        n = 6 if regla is simpson_13 else 6
        assert regla(f, 0.0, 2.0, n) == pytest.approx(4.0, rel=1e-12)
    assert boole(f, 0.0, 2.0, 8) == pytest.approx(4.0, rel=1e-12)


def test_trapecio_error_conocido():
    f = lambda x: x**3
    # trapecio con n=2: 1*(0 + 1 + 4) = 5, exacto 4
    assert trapecio(f, 0.0, 2.0, 2) == pytest.approx(5.0)
    assert abs(trapecio(f, 0.0, 2.0, 4) - 4.0) == pytest.approx(0.25)


def test_orden_trapecio_y_simpson():
    f = np.sin
    exacto = 2.0
    e_t = [abs(trapecio(f, 0, np.pi, n) - exacto) for n in (10, 20, 40)]
    e_s = [abs(simpson_13(f, 0, np.pi, n) - exacto) for n in (10, 20, 40)]
    assert np.log2(e_t[0] / e_t[1]) == pytest.approx(2.0, abs=0.1)
    assert np.log2(e_s[0] / e_s[1]) == pytest.approx(4.0, abs=0.2)


def test_gauss_exacto_hasta_grado_2n_menos_1():
    for n in (3, 5):
        for grado in (2 * n - 1,):
            f = lambda x, g=grado: x**g
            exacto = (2.0 ** (grado + 1)) / (grado + 1)
            assert gauss_legendre(f, 0.0, 2.0, n) == pytest.approx(exacto, rel=1e-12)


def test_romberg_converge_mas_rapido_que_trapecio():
    f = np.sin
    r = romberg(f, 0.0, np.pi, tol=1e-12)
    assert r.valor == pytest.approx(2.0, abs=1e-12)
    assert r.n_evals <= 260
    assert r.iteraciones >= 2
