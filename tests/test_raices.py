"""I07: métodos de raíces y sus aplicaciones al problema."""

import math

import pytest

from simulador.analitica import caida_con_arrastre, caida_sin_aire
from simulador.raices import (
    biseccion,
    falsa_posicion,
    k_critico_supervivencia,
    newton_raphson,
    punto_fijo,
    secante,
    t_impacto_suelo,
    t_tensado_numerico,
)


def f(x):
    return x**3 - 2 * x - 5


def df(x):
    return 3 * x**2 - 2


RAIZ = 2.0945514815423265


def test_cinco_metodos_coinciden():
    metodos = [
        biseccion(f, 1, 3, tol=1e-12),
        falsa_posicion(f, 1, 3, tol=1e-12),
        newton_raphson(f, df, 2.0, tol=1e-12),
        secante(f, 1.0, 3.0, tol=1e-12),
        punto_fijo(lambda x: (2 * x + 5) ** (1 / 3), 2.0, tol=1e-12),
    ]
    for raiz, _, _ in metodos:
        assert raiz == pytest.approx(RAIZ, abs=1e-8)


def test_iteraciones():
    _, it_bis, _ = biseccion(f, 1, 3, tol=1e-10)
    _, it_new, _ = newton_raphson(f, df, 2.0, tol=1e-10)
    assert it_bis == pytest.approx(math.log2(2 / 1e-10), abs=2)
    assert it_new < 10


def test_punto_fijo_divergente():
    with pytest.raises(RuntimeError):
        punto_fijo(lambda x: (x**3 - 5) / 2, 2.0)


def test_k_critico_supervivencia():
    _, v0 = caida_sin_aire(42.0)
    k, _, _ = k_critico_supervivencia(v0, 50.0, 6.0)
    assert k == pytest.approx(204.375, abs=0.1)


def test_newton_para_el_k_critico():
    from simulador.analitica import amax_en_g

    _, v0 = caida_sin_aire(42.0)
    f = lambda k: amax_en_g(v0, k, 50.0) - 6.0
    raiz, it, _ = newton_raphson(f, None, 300.0, tol=1e-10)
    assert raiz == pytest.approx(204.375, abs=1e-4)
    assert it < 10


def test_instante_de_tensado():
    t, it, _ = t_tensado_numerico(42.0, 50.0, 0.6)
    t_an, _, _ = caida_con_arrastre(42.0, 50.0, 0.6)
    assert t == pytest.approx(t_an, rel=1e-10)
    assert it > 0


def test_instante_de_impacto_contra_el_suelo():
    _, v0, _ = caida_con_arrastre(42.0, 50.0, 0.6)
    from simulador.analitica import k_para_aceleracion

    k = k_para_aceleracion(v0, 50.0, 6.0)
    t, _, _ = t_impacto_suelo(v0, k, 50.0, 1.60)
    assert 0 < t < 1.0
