"""I04: oscilador de la telaraña, energía y potencia."""

import numpy as np
import pytest

from simulador.analitica import (
    a_resorte_de_t,
    amax_analitica,
    energia_resorte,
    k_desde_elongacion,
    potencia_pico,
    t_pico_analitico,
    v_resorte_de_t,
    x_de_t,
)

V0 = 28.70609691337365
M = 50.0
X = 0.40


def test_k_desde_elongacion():
    k = k_desde_elongacion(V0, X, M)
    assert k == pytest.approx(259965.0, abs=50.0)


def test_amax_y_tpico():
    k = k_desde_elongacion(V0, X, M)
    assert amax_analitica(V0, k, M) / 9.81 == pytest.approx(211.0, abs=1.0)
    assert t_pico_analitico(V0, k, M) == pytest.approx(0.021850, abs=2e-4)


def test_tpico_es_el_primer_cero_de_velocidad():
    k = k_desde_elongacion(V0, X, M)
    tp = t_pico_analitico(V0, k, M)
    assert v_resorte_de_t(tp, V0, k, M) == pytest.approx(0.0, abs=1e-9)


def test_balance_energetico():
    k = k_desde_elongacion(V0, X, M)
    assert 0.5 * k * X**2 == pytest.approx(energia_resorte(V0, X, M), rel=1e-10)


def test_edo_del_oscilador_por_diferencias_finitas():
    k = k_desde_elongacion(V0, X, M)
    t = 0.011
    h = 1e-4
    x = lambda tt: float(x_de_t(tt, V0, k, M))
    segunda = (x(t + h) - 2 * x(t) + x(t - h)) / (h * h)
    a_fd = 9.81 - (k / M) * x(t)
    assert segunda == pytest.approx(a_fd, abs=1e-2)


def test_potencia_pico_real():
    k = k_desde_elongacion(V0, X, M)
    p, tp = potencia_pico(V0, k, M)
    assert p / 1e6 == pytest.approx(1.495, abs=0.01)
    assert tp == pytest.approx(0.010935, abs=2e-4)
    # la cota F_max*v0 no es la potencia real
    assert p < k * X * V0


def test_aceleracion_maxima_en_el_pico():
    k = k_desde_elongacion(V0, X, M)
    tp = t_pico_analitico(V0, k, M)
    a = abs(a_resorte_de_t(tp, V0, k, M))
    assert a == pytest.approx(amax_analitica(V0, k, M), rel=1e-6)
