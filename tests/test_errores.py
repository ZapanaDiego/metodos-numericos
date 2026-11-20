"""I10: errores, diferencias finitas y Richardson."""

import numpy as np
import pytest

from simulador.diferenciacion import adelante, atras, central, segunda_derivada
from simulador.errores import (
    epsilon_maquina,
    error_abs,
    error_rel,
    orden_observado,
    richardson,
)
from simulador.integracion import trapecio


def test_errores_basicos():
    assert error_abs(1.0, 1.1) == pytest.approx(0.1)
    assert error_rel(1.0, 2.0) == pytest.approx(0.5)
    assert error_rel(0.0, 0.0) is None
    assert epsilon_maquina() == pytest.approx(2.22e-16, rel=1e-2)


def test_orden_observado_un_paso():
    assert orden_observado([0.1, 0.05], [0.01, 0.0025])[0] == pytest.approx(2.0)


def test_richardson_mejora_el_orden():
    f = np.exp
    exacto = np.e - 1
    h = 0.1
    t1 = trapecio(f, 0.0, 1.0, int(1 / h))
    t2 = trapecio(f, 0.0, 1.0, int(2 / h))
    r = richardson(t1, t2, p=2)
    assert abs(t2 - exacto) < abs(t1 - exacto)
    assert abs(r - exacto) < abs(t2 - exacto)
    assert abs(r - exacto) < 1e-4


def test_diferencias_finitas_orden():
    x = 0.7
    hs = [0.1, 0.05, 0.025]
    f = np.exp
    e_adelante = [abs(adelante(f, x, h) - f(x)) for h in hs]
    e_central = [abs(central(f, x, h) - f(x)) for h in hs]
    o_adelante = orden_observado(hs, e_adelante)
    o_central = orden_observado(hs, e_central)
    assert o_adelante[0] == pytest.approx(1.0, abs=0.15)
    assert o_central[0] == pytest.approx(2.0, abs=0.15)
    assert atras(f, x, 1e-5) == pytest.approx(f(x), rel=1e-4)


def test_segunda_derivada():
    f = np.sin
    assert segunda_derivada(f, 0.3, 1e-4) == pytest.approx(-np.sin(0.3), abs=1e-6)
