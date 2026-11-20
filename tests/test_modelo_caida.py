"""I06: modelo de caída, evento de tensado y simulación completa."""

import numpy as np
import pytest

from simulador.analitica import caida_con_arrastre, caida_sin_aire
from simulador.modelo import detectar_evento, simular, simular_caida_numerica
from simulador.parametros import Escena


@pytest.mark.parametrize("escena", [Escena.pelicula(), Escena.sin_aire()])
def test_evento_numerico_coincide_con_analitica(escena):
    t_num, v_num, _, _ = simular_caida_numerica(escena, dt=1e-4)
    if escena.cuerpo.cd_area_m2 > 0:
        t_an, v_an, _ = caida_con_arrastre(
            escena.caida_m,
            escena.cuerpo.masa_kg,
            escena.cuerpo.cd_area_m2,
            escena.cuerpo.densidad_aire_kg_m3,
        )
    else:
        t_an, v_an = caida_sin_aire(escena.caida_m)
    assert t_num == pytest.approx(t_an, rel=1e-8)
    assert v_num == pytest.approx(v_an, rel=1e-8)


def test_detectar_evento_entre_pasos():
    f = lambda t: t - 0.123456789
    raices = detectar_evento(f, (0.0, 1.0), n=101)
    assert len(raices) == 1
    assert raices[0] == pytest.approx(0.123456789, abs=1e-12)


def test_simulacion_base_con_aire():
    r = simular(Escena.pelicula())
    assert r.v0_m_s == pytest.approx(24.87, abs=0.01)
    assert r.k_n_m == pytest.approx(195739.0, rel=1e-3)
    assert r.x_max_m == pytest.approx(0.40, rel=1e-12)
    assert r.a_max_g == pytest.approx(158.62, abs=0.05)
    assert r.f_max_n / 1e3 == pytest.approx(78.30, abs=0.05)
    assert r.energia_j / 1e3 == pytest.approx(15.659, abs=0.01)
    assert r.p_max_w / 1e6 == pytest.approx(0.976, abs=0.01)
    assert r.t_pico_s * 1e3 == pytest.approx(25.206, abs=0.05)
    assert r.deformacion == pytest.approx(0.4 / 42.0, rel=1e-12)
    assert r.modulo_seda_pa / 1e9 == pytest.approx(328.74, rel=1e-3)
    assert np.isnan(r.t_impacto_s)  # el torso no toca el suelo
    assert np.min(r.altura_torso_m) == pytest.approx(1.20, abs=0.01)


def test_simulacion_sin_aire():
    r = simular(Escena.sin_aire())
    assert r.v0_m_s == pytest.approx(28.7061, rel=1e-4)
    assert r.a_max_g == pytest.approx(211.0, abs=0.1)
    assert r.k_n_m == pytest.approx(259965.0, rel=1e-5)
    assert r.energia_j / 1e3 == pytest.approx(20.797, abs=0.01)


def test_modo_material_supervivencia():
    r = simular(Escena.supervivencia())
    assert r.a_max_g == pytest.approx(6.0, abs=0.05)
    assert r.x_max_m == pytest.approx(12.61, abs=0.05)
    assert r.deformacion == pytest.approx(0.30, abs=2e-3)
    assert r.modulo_seda_pa / 1e6 == pytest.approx(457.4, abs=2)
    assert np.isfinite(r.t_impacto_s)
    assert r.t_impacto_s < r.t_pico_s


def test_conservacion_de_energia_en_el_resorte():
    r = simular(Escena.pelicula())
    # en el pico toda la energía es elástica (más gravedad)
    assert 0.5 * r.k_n_m * r.x_max_m**2 == pytest.approx(r.energia_j, rel=1e-9)
