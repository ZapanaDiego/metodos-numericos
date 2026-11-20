"""I02: parámetros, presets y validación geométrica."""

import pytest

from simulador.parametros import Computo, Cuerpo, Escena, Telarana


def test_escena_por_defecto():
    e = Escena.pelicula()
    assert e.h_ancla_m == pytest.approx(43.60)
    assert e.telarana.longitud_m == pytest.approx(42.0)
    assert e.telarana.estiramiento_m == pytest.approx(0.40)
    assert e.altura_torso_m == pytest.approx(1.20)
    assert e.espacio_libre_m == pytest.approx(1.60)
    e.validar_geometria()


def test_geometria_inconsistente():
    with pytest.raises(ValueError, match="Geometría inconsistente"):
        Escena(telarana=Telarana(longitud_m=30.0)).validar_geometria()


def test_presets_validos():
    for escena in (Escena.pelicula(), Escena.sin_aire(), Escena.torre_completa()):
        escena.validar_geometria()
    s = Escena.supervivencia()
    assert s.modo == "material"
    assert s.telarana.k_n_m == pytest.approx(272.37, rel=1e-3)


def test_validaciones_de_entrada():
    with pytest.raises(ValueError):
        Cuerpo(masa_kg=0)
    with pytest.raises(ValueError):
        Telarana(longitud_m=-1)
    with pytest.raises(ValueError):
        Escena(modo="otro")
    with pytest.raises(ValueError):
        Computo(dt_s=0)


def test_computo():
    c = Computo()
    assert c.dt_s == 1e-4
    assert c.semilla == 42
