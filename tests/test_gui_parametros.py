"""I31: modelo de parámetros de la vista y sincronización lógica."""

import pytest

from visual.parametros_vista import ParametrosVista


def test_valores_iniciales_y_escena():
    p = ParametrosVista()
    e = p.escena()
    assert e.h_ancla_m == pytest.approx(43.60)
    assert e.caida_m == pytest.approx(42.0)
    assert e.altura_torso_m == pytest.approx(1.20)
    assert e.telarana.estiramiento_m == pytest.approx(0.40)
    e.validar_geometria()


def test_cambio_de_masa_y_modo():
    p = ParametrosVista()
    p.set_valor("masa_kg", 62.5)
    assert p.masa_kg == 62.5
    p.set_valor("k_n_m", 300000)
    assert p.modo == "material"
    p.set_valor("estiramiento_m", 0.5)
    assert p.modo == "calibracion"


def test_valor_invalido_no_propaga():
    p = ParametrosVista()
    with pytest.raises(ValueError):
        p.set_valor("masa_kg", -1)
    with pytest.raises(ValueError):
        p.set_valor("semilla", -5)
    assert p.masa_kg == 50.0


def test_restablecer():
    p = ParametrosVista()
    p.set_valor("masa_kg", 70)
    p.set_valor("k_n_m", 500000)
    p.restablecer()
    assert p.masa_kg == 50.0
    assert p.modo == "calibracion"
    assert p.k_efectiva() == pytest.approx(195739, rel=1e-3)


def test_aire_y_tumbling():
    p = ParametrosVista()
    assert p.cd_area_efectiva() == pytest.approx(0.6)
    p.aire = False
    assert p.cd_area_efectiva() == 0.0
    p.aire = True
    p.tumbling = True
    p.semilla = 7
    assert 0.4 <= p.cd_area_efectiva() <= 0.8


def test_simular_y_k_efectiva():
    p = ParametrosVista()
    r = p.simular()
    assert r.a_max_g == pytest.approx(158.6, abs=0.5)
    assert p.k_efectiva() == pytest.approx(r.k_n_m, rel=1e-3)
