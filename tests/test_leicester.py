"""I05: validación externa contra el paper de Leicester (2021)."""

import pytest

from simulador.validacion import escenario_leicester


def test_leicester():
    r = escenario_leicester()
    assert r.v0_m_s == pytest.approx(28.7, rel=1e-3)
    assert r.x_m == pytest.approx(16.7, rel=1e-2)
    assert r.k_n_m == pytest.approx(204.5, rel=1e-2)
    assert 100e6 <= r.modulo_pa <= 10e9
    assert r.modulo_mpa == pytest.approx(343.35, rel=1e-3)
    assert r.deformacion == pytest.approx(0.40, abs=1e-3)


def test_relacion_x_igual_a_cuatro_decimas_de_h():
    r = escenario_leicester()
    assert r.x_m == pytest.approx(0.4 * 42.0, rel=1e-12)
