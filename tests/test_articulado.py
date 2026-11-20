"""I20: momentos del cuerpo articulado anclado en el torso."""

import numpy as np
import pytest

from simulador.articulado import (
    clasificar_momento,
    momento_cadera,
    momento_cuello,
    momentos,
    perfil_momentos,
    posiciones,
)
from simulador.modelo import simular
from simulador.parametros import Cuerpo, Escena

CUERPO = Cuerpo()


def test_momento_cuello_en_el_pico():
    m = momento_cuello(158.624 * 9.81, CUERPO)
    assert m / 1e3 == pytest.approx(1.409, abs=0.01)
    m2 = momento_cuello(211.0 * 9.81, CUERPO)
    assert m2 / 1e3 == pytest.approx(1.872, abs=0.02)


def test_momento_escala_linealmente():
    a = 100.0
    m1 = momento_cuello(a, CUERPO)
    m2 = momento_cuello(2 * a, CUERPO)
    # el término +g introduce una constante, pero la diferencia es lineal
    assert (m2 - m1) == pytest.approx(m1 - momento_cuello(0.0, CUERPO))


def test_momentos_en_6g():
    a6 = 6 * 9.81
    m = momento_cuello(a6, CUERPO)
    assert m == pytest.approx(61.8, abs=0.5)
    assert clasificar_momento(m) == "limite"


def test_momento_cadera():
    assert momento_cadera(0.0, CUERPO) == pytest.approx(20 * 0.45 * 9.81)


def test_perfil_y_posiciones_no_tocan_suelo():
    r = simular(Escena.pelicula())
    t, mc, mh = perfil_momentos(r, CUERPO)
    assert len(t) == len(mc) == len(mh)
    assert np.max(mc) / 1e3 == pytest.approx(1.41, abs=0.02)
    cabeza, torso, cadera = posiciones(r.altura_torso_m, CUERPO)
    assert np.min(cabeza) > 1.2
    assert np.min(cadera) > 0.7
    assert np.min(torso) == pytest.approx(1.20, abs=0.01)
