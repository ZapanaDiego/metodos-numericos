"""I14: energía, potencia, impulso, HIC y clasificación."""

import numpy as np
import pytest

from simulador.energia import (
    balance_energetico,
    clasificar,
    energia_cinetica,
    hic,
    hic_pulso_rectangular,
    impulso,
    potencia_pico,
    trabajo_resorte,
)
from simulador.modelo import simular
from simulador.parametros import Escena


def test_energia_base():
    r = simular(Escena.pelicula())
    assert r.energia_j / 1e3 == pytest.approx(15.659, abs=0.01)
    assert r.energia_j == pytest.approx(
        0.5 * 50 * r.v0_m_s**2 + 50 * 9.81 * r.x_max_m, rel=1e-10
    )


def test_potencia_pico_real():
    r = simular(Escena.pelicula())
    assert r.p_max_w / 1e6 == pytest.approx(0.976, abs=0.01)
    assert potencia_pico(r.k_n_m, r.x_max_m, r.v0_m_s) <= r.k_n_m * r.x_max_m * r.v0_m_s


def test_trabajo_numerico_vs_analitico():
    r = simular(Escena.pelicula())
    assert trabajo_resorte(r.k_n_m, r.x_max_m) == pytest.approx(
        0.5 * r.k_n_m * r.x_max_m**2, rel=1e-12
    )


def test_balance_energetico_residuo_cero():
    r = simular(Escena.pelicula())
    b = balance_energetico(r.v0_m_s, r.x_max_m, 50.0, r.k_n_m)
    assert b["residuo_j"] == pytest.approx(0.0, abs=1e-8)


def test_hic_pulso_rectangular():
    assert hic_pulso_rectangular(10.0, 0.02) == pytest.approx(0.02 * 10**2.5)
    # una duración mayor que 36 ms se recorta
    assert hic_pulso_rectangular(10.0, 0.08) == pytest.approx(0.036 * 10**2.5)


def test_hic_numerico_y_ventana():
    dt = 1e-4
    a = np.full(int(0.02 / dt), 10.0)
    assert hic(a, dt) == pytest.approx(0.02 * 10**2.5, rel=1e-3)
    a_largo = np.full(int(0.2 / dt), 10.0)
    assert hic(a_largo, dt) == pytest.approx(0.036 * 10**2.5, rel=1e-3)


def test_clasificar():
    assert clasificar(211.0) == "letal"
    assert clasificar(6.0) == "supervivencia"
    assert clasificar(6.0, hic_valor=3.2) == "supervivencia"
    assert clasificar(6.0, hic_valor=800.0) == "letal"


def test_energia_cinetica_e_impulso():
    assert energia_cinetica(50, [0, 10]) == pytest.approx([0.0, 2500.0])
    t = np.linspace(0, 1, 101)
    f = np.ones_like(t)
    assert impulso(f, t) == pytest.approx(1.0)
