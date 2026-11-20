"""Verifica todos los valores golden contra los modelos actuales."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from simulador.modelo import simular
from simulador.parametros import Escena
from simulador.validacion import escenario_leicester

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "datos" / "referencia.csv"


def _actuales():
    base = simular(Escena.pelicula())
    sin = simular(Escena.sin_aire())
    sup = simular(Escena.supervivencia())
    leic = escenario_leicester()
    return {
        ("base", "v0_m_s"): base.v0_m_s,
        ("base", "k_n_m"): base.k_n_m,
        ("base", "x_m"): base.x_max_m,
        ("base", "a_max_g"): base.a_max_g,
        ("base", "f_max_n"): base.f_max_n,
        ("base", "energia_j"): base.energia_j,
        ("base", "p_max_w"): base.p_max_w,
        ("base", "t_pico_s"): base.t_pico_s,
        ("base", "modulo_pa"): base.modulo_seda_pa,
        ("base", "deformacion"): base.deformacion,
        ("base", "m_cuello_n_m"): base.momentos().cuello_n_m,
        ("base", "hic"): base.hic,
        ("sin_aire", "v0_m_s"): sin.v0_m_s,
        ("sin_aire", "k_n_m"): sin.k_n_m,
        ("sin_aire", "a_max_g"): sin.a_max_g,
        ("sin_aire", "energia_j"): sin.energia_j,
        ("sin_aire", "p_max_w"): sin.p_max_w,
        ("sin_aire", "t_pico_s"): sin.t_pico_s,
        ("sin_aire", "modulo_pa"): sin.modulo_seda_pa,
        ("leicester", "v0_m_s"): leic.v0_m_s,
        ("leicester", "k_n_m"): leic.k_n_m,
        ("leicester", "x_m"): leic.x_m,
        ("leicester", "modulo_pa"): leic.modulo_pa,
        ("supervivencia", "k_n_m"): sup.k_n_m,
        ("supervivencia", "x_m"): sup.x_max_m,
        ("supervivencia", "a_max_g"): sup.a_max_g,
        ("supervivencia", "deformacion"): sup.deformacion,
        ("supervivencia", "modulo_pa"): sup.modulo_seda_pa,
        ("supervivencia", "energia_j"): sup.energia_j,
    }


def test_referencia_completa():
    if not CSV.exists():
        pytest.skip("falta datos/referencia.csv; ejecuta scripts/generar_referencia.py")
    actuales = _actuales()
    with CSV.open(encoding="utf-8") as fh:
        for fila in csv.DictReader(fh):
            clave = (fila["caso"], fila["magnitud"])
            assert clave in actuales, f"clave desconocida en CSV: {clave}"
            esperado = float(fila["valor"])
            rtol = float(fila["rtol"])
            assert actuales[clave] == pytest.approx(esperado, rel=rtol), clave


def test_ficheros_requeridos():
    for nombre in ["README.md", "AGENTS.md", "requirements.txt", "pyproject.toml"]:
        assert (RAIZ / nombre).exists(), nombre
