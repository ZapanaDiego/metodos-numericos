"""I03: caída libre y caída con arrastre cuadrático."""

import numpy as np
import pytest

from simulador.analitica import (
    caida_con_arrastre,
    caida_sin_aire,
    v_de_t,
    y_de_t,
)


def test_caida_sin_aire():
    t, v = caida_sin_aire(42.0)
    assert v == pytest.approx(28.70609691337365, rel=1e-12)
    assert t == pytest.approx(np.sqrt(2 * 42.0 / 9.81), rel=1e-12)


def test_caida_con_arrastre():
    t, v, vt = caida_con_arrastre(42.0, 50.0, 0.6)
    assert vt == pytest.approx(36.91, abs=0.1)
    assert v == pytest.approx(24.87, abs=0.01)
    assert t == pytest.approx(3.0757, abs=0.01)


def test_reconstruccion_de_la_altura():
    t, v, vt = caida_con_arrastre(42.0, 50.0, 0.6)
    assert y_de_t(t, vt) == pytest.approx(42.0, rel=1e-10)
    assert v_de_t(t, vt) == pytest.approx(v, rel=1e-12)


def test_monotonia_y_limite_terminal():
    t, _, vt = caida_con_arrastre(42.0, 50.0, 0.6)
    ts = np.linspace(0, 5 * t, 5000)
    ys = y_de_t(ts, vt)
    vs = v_de_t(ts, vt)
    assert np.all(np.diff(ys) > 0)
    assert np.all(np.diff(vs) >= -1e-12)
    assert v_de_t(200.0, vt) == pytest.approx(vt, rel=1e-12)


def test_sin_aire_es_limite():
    t, v, vt = caida_con_arrastre(42.0, 50.0, 0.0)
    assert not np.isfinite(vt)
    assert v == pytest.approx(28.70609691337365, rel=1e-12)
    assert y_de_t(t, vt) == pytest.approx(42.0, rel=1e-10)
