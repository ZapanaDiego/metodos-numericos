"""I22/I24: proceso de Ornstein-Uhlenbeck y Monte Carlo vectorizado."""

import time

import numpy as np
import pytest

from simulador.estocastico import (
    cd_area,
    muestrear_parametros,
    ou_proceso,
    simular_ensemble,
)


def test_ou_reproducible():
    r1 = ou_proceso(1000, 1e-3, lam=1.0, sigma=0.5, rng=np.random.default_rng(7))
    r2 = ou_proceso(1000, 1e-3, lam=1.0, sigma=0.5, rng=np.random.default_rng(7))
    r3 = ou_proceso(1000, 1e-3, lam=1.0, sigma=0.5, rng=np.random.default_rng(8))
    assert np.array_equal(r1, r2)
    assert not np.array_equal(r1, r3)


def test_ou_varianza_estacionaria():
    r = ou_proceso(200000, 1e-3, lam=1.0, sigma=0.5, rng=np.random.default_rng(1))
    assert np.var(r[10000:]) == pytest.approx(0.25, abs=0.02)


def test_ou_sin_ruido_decae():
    r = ou_proceso(5000, 1e-3, lam=1.0, sigma=0.0, rng=np.random.default_rng(1), x0=1.0)
    t = np.arange(r.size) * 1e-3
    assert np.allclose(r, np.exp(-t), rtol=1e-2, atol=1e-3)


def test_cd_area_acotado():
    theta = np.linspace(-10, 10, 1000)
    cd = cd_area(theta)
    assert np.all(cd >= 0.1 - 1e-12)
    assert np.all(cd <= 0.7 + 1e-12)


def test_muestreo_reproducible():
    a = muestrear_parametros(100, np.random.default_rng(3))
    b = muestrear_parametros(100, np.random.default_rng(3))
    for clave in a:
        assert np.array_equal(a[clave], b[clave])


def test_montecarlo_reproducible_y_percentiles():
    e1 = simular_ensemble(n=200, semilla=42)
    e2 = simular_ensemble(n=200, semilla=42)
    assert np.array_equal(e1.a_max_g, e2.a_max_g)
    st = e1.estadisticas("a_max_g")
    assert st["p5"] <= st["p50"] <= st["p95"]
    assert st["error_estandar"] > 0
    assert e1.fraccion("hic", 700.0) > 0.95


def test_error_estandar_decrece_como_raiz_de_n():
    errores = []
    for n in (100, 400, 1600):
        e = simular_ensemble(n=n, semilla=5)
        errores.append(e.estadisticas("a_max_g")["error_estandar"])
    assert errores[0] / errores[1] == pytest.approx(2.0, rel=0.3)
    assert errores[1] / errores[2] == pytest.approx(2.0, rel=0.3)


def test_montecarlo_2000_rapido():
    t0 = time.perf_counter()
    e = simular_ensemble(n=2000, semilla=1)
    dt = time.perf_counter() - t0
    assert dt < 30.0
    assert e.a_max_g.shape == (2000,)
