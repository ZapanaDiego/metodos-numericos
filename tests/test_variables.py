"""Pruebas de consistencia del módulo único de variables ``simulador.variables``."""

import numpy as np
import pytest

from simulador import VARIABLES_BASE
from simulador import variables as var
from simulador.modelo import simular
from simulador.parametros import Escena


def test_variables_primarias_y_constantes_edo():
    assert var.MASA_KG == pytest.approx(50.0, rel=1e-15)
    assert var.GRAVEDAD_M_S2 == pytest.approx(9.81, rel=1e-15)
    assert var.DENSIDAD_AIRE_KG_M3 == pytest.approx(1.20, rel=1e-15)
    assert var.CD_AREA_M2 == pytest.approx(0.60, rel=1e-15)
    assert var.C_ARRASTRE_KG_M == pytest.approx(0.36, rel=1e-15)
    assert var.COEF_CAIDA_M_INV == pytest.approx(0.0072, rel=1e-15)
    assert var.VELOCIDAD_TERMINAL_M_S == pytest.approx(36.91205765058349, rel=1e-15)
    assert var.H_ANCLA_M == pytest.approx(43.60, rel=1e-15)
    assert var.CAIDA_M == pytest.approx(42.00, rel=1e-15)
    assert var.LONGITUD_SEDA_M == pytest.approx(42.00, rel=1e-15)
    assert var.AREA_SEDA_M2 == pytest.approx(2.5e-5, rel=1e-15)
    assert var.ESTIRAMIENTO_CAL_M == pytest.approx(0.40, rel=1e-15)
    assert var.ALTURA_TORSO_FINAL_M == pytest.approx(1.20, rel=1e-15)
    assert var.ESPACIO_LIBRE_M == pytest.approx(1.60, rel=1e-15)
    assert var.K_CALIBRADA_N_M == pytest.approx(195678.991731443, rel=1e-14)
    assert var.OMEGA2_S_INV2 == pytest.approx(3913.57983462886, rel=1e-14)
    assert var.OMEGA_RAD_S == pytest.approx(62.55861119485358, rel=1e-14)
    assert var.PERIODO_ELASTICO_S == pytest.approx(2 * np.pi / var.OMEGA_RAD_S, rel=1e-15)
    assert var.PASO_BASE_S == pytest.approx(0.001, rel=1e-15)
    assert var.PASOS_VISOR_MS == (0.25, 0.5, 1, 2, 4, 8)
    assert var.PASOS_VISOR_MS[var.INDICE_PASO_BASE_VISOR] / 1000 == pytest.approx(var.PASO_BASE_S)


def test_contenedor_variables_base_coincide_con_simulacion():
    r = simular(Escena.pelicula())
    assert VARIABLES_BASE.m == r.escena.cuerpo.masa_kg
    assert VARIABLES_BASE.g == r.escena.gravedad_m_s2
    assert VARIABLES_BASE.rho == r.escena.cuerpo.densidad_aire_kg_m3
    assert VARIABLES_BASE.cd_area == r.escena.cuerpo.cd_area_m2
    assert VARIABLES_BASE.h_ancla == r.escena.h_ancla_m
    assert VARIABLES_BASE.H == r.escena.caida_m
    assert VARIABLES_BASE.L == r.escena.telarana.longitud_m
    assert VARIABLES_BASE.area_seda == r.escena.telarana.area_m2
    assert VARIABLES_BASE.x_cal == r.escena.telarana.estiramiento_m
    assert VARIABLES_BASE.v0_ref == pytest.approx(r.v0_m_s, rel=1e-15)
    assert VARIABLES_BASE.k == pytest.approx(r.k_n_m, rel=1e-15)
    assert VARIABLES_BASE.v_t == pytest.approx(r.resumen_extra["vt_m_s"], rel=1e-15)
