"""I16: elasticidad y viabilidad de la seda."""

import pytest

from simulador.elasticidad import (
    E_a_k,
    Viabilidad,
    deformacion,
    dentro_de_rango,
    dentro_de_rango_dragline,
    energia_especifica,
    esfuerzo,
    k_a_E,
)
from simulador.modelo import simular
from simulador.parametros import Escena


def test_escenario_a_modulo_imposible():
    r = simular(Escena.pelicula())
    assert r.modulo_seda_pa / 1e9 == pytest.approx(328.7, rel=1e-3)
    assert not dentro_de_rango(r.modulo_seda_pa)
    assert not dentro_de_rango_dragline(r.modulo_seda_pa)


def test_ida_y_vuelta():
    E = 5e9
    L, A = 42.0, 2.5e-5
    k = E_a_k(E, L, A)
    assert k_a_E(k, L, A) == pytest.approx(E, rel=1e-12)
    k2 = 195739.0
    assert E_a_k(k_a_E(k2, L, A), L, A) == pytest.approx(k2, rel=1e-12)


def test_deformaciones():
    assert deformacion(0.4, 42.0) == pytest.approx(0.4 / 42.0, rel=1e-12)
    r = simular(Escena.supervivencia())
    assert r.deformacion == pytest.approx(0.30, abs=2e-3)


def test_esfuerzo_y_energia_especifica():
    assert esfuerzo(5e9, 0.01) == pytest.approx(5e7)
    assert energia_especifica(5e9, 0.01) == pytest.approx(2.5e5)


def test_viabilidad_escenario_supervivencia():
    r = simular(Escena.supervivencia())
    v = Viabilidad(
        modulo_pa=r.modulo_seda_pa,
        deformacion=r.deformacion,
        espacio_libre_m=r.escena.espacio_libre_m,
        estiramiento_m=r.x_max_m,
    )
    assert not v.viable
    assert "espacio libre" in v.motivo


def test_viabilidad_seda_real():
    v = Viabilidad(
        modulo_pa=5e9,
        deformacion=5.43 / 42.0,
        espacio_libre_m=1.6,
        estiramiento_m=5.43,
    )
    assert not v.viable
    assert "espacio libre" in v.motivo
