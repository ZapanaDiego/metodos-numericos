"""Comparación de las dos EDO y sus eventos con la referencia."""
import numpy as np
import pytest

from simulador.modelo import simular
from simulador.parametros import Computo, Escena


@pytest.mark.parametrize("escena", [Escena.pelicula(), Escena.sin_aire()])
def test_convergencia_en_la_escena(escena):
    referencia = simular(escena)
    for metodo in ("euler", "rk4"):
        gruesa, fina = [simular(escena, computo=Computo(h, metodo)) for h in (0.004, 0.002)]
        assert fina.k_n_m == referencia.k_n_m
        assert np.all(np.diff(fina.t) > 0)
        assert abs(fina.x_max_m - referencia.x_max_m) < abs(gruesa.x_max_m - referencia.x_max_m)
        evento = np.searchsorted(fina.t, fina.t_tensado_s)
        assert fina.altura_torso_m[evento] == pytest.approx(escena.h_ancla_m - escena.caida_m)
        assert fina.fuerza_n[evento] == pytest.approx(0)
    assert fina.t_pico_s == pytest.approx(referencia.t_pico_s, rel=1e-4)
    assert fina.energia_j == pytest.approx(referencia.energia_j, rel=1e-4)


def test_rechaza_paso_que_no_resuelve_el_frenado():
    with pytest.raises(ValueError, match="período"):
        simular(Escena.pelicula(), computo=Computo(0.1, "euler"))


def test_balance_y_primer_contacto_en_escenario_alternativo():
    from simulador.mediciones import energias, primer_contacto, segmentos

    resultado = simular(Escena.pelicula(), computo=Computo(0.001, "rk4"))
    balance = energias(resultado)
    assert np.max(balance["seda_j"]) == pytest.approx(resultado.energia_j)
    assert np.max(np.abs(balance["residuo_j"])) < 0.01
    assert primer_contacto(segmentos(resultado)) is None
    choque = primer_contacto(segmentos(resultado, 0.85))
    assert choque.tiempo_s > resultado.t_tensado_s
    assert choque.rapidez_normal_m_s > 0
    assert choque.energia_incidente_j > 0
    assert choque.segmento == "Piernas"
    cabeza = primer_contacto(segmentos(resultado, 1.0, piernas_rad=-0.5))
    assert cabeza.segmento == "Cabeza"
    assert cabeza.energia_incidente_j > 0
