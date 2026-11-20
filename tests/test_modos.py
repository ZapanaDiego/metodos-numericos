"""I17: modos calibración (x fijo) y material (k fijo)."""

import pytest

from simulador.modelo import simular
from simulador.parametros import Cuerpo, Escena, Telarana


def test_calibracion_recupera_x():
    e = Escena.pelicula()
    r = simular(e)
    assert r.x_max_m == pytest.approx(0.40, rel=1e-12)
    assert r.k_n_m == pytest.approx(195679.0, rel=1e-4)


def test_material_con_k_conocido():
    e = Escena(
        h_ancla_m=43.60,
        caida_m=42.0,
        altura_torso_m=1.20,
        cuerpo=Cuerpo(cd_area_m2=0.6),
        telarana=Telarana(estiramiento_m=None, k_n_m=260000.0),
        modo="material",
    )
    r = simular(e)
    assert r.k_n_m == pytest.approx(260000.0, rel=1e-12)
    assert r.x_max_m == pytest.approx(0.3467, abs=1e-3)


def test_monotonia_material():
    xs = []
    for k in (100000.0, 200000.0, 300000.0, 400000.0):
        e = Escena(
            cuerpo=Cuerpo(cd_area_m2=0.6),
            telarana=Telarana(estiramiento_m=None, k_n_m=k),
            modo="material",
        )
        xs.append(simular(e).x_max_m)
    assert all(xs[i] > xs[i + 1] for i in range(len(xs) - 1))


def test_v0_no_cambia_k_en_material():
    base = Escena(
        cuerpo=Cuerpo(cd_area_m2=0.6),
        telarana=Telarana(estiramiento_m=None, k_n_m=260000.0),
        modo="material",
    )
    otra = Escena(
        caida_m=50.0,
        cuerpo=Cuerpo(cd_area_m2=0.6),
        telarana=Telarana(estiramiento_m=None, k_n_m=260000.0),
        modo="material",
    )
    assert simular(base).k_n_m == simular(otra).k_n_m
    cal1 = Escena.pelicula()
    cal2 = Escena.pelicula().con(caida_m=50.0)
    assert simular(cal1).k_n_m != simular(cal2).k_n_m
