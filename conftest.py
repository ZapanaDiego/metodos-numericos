"""Configuración global de pytest.

Fija el backend de matplotlib antes de que ningún test importe pyplot y
proporciona un fixture para saltar pruebas de GUI sin display.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def hay_display() -> bool:
    return bool(os.environ.get("DISPLAY"))


@pytest.fixture
def rng():
    """Generador reproducible para tests estocásticos."""
    import numpy as np

    return np.random.default_rng(20261119)


def pytest_collection_modifyitems(items):
    """Selecciona como rápidas las pruebas sin marca de GUI o carga lenta."""
    for item in items:
        if not any(item.get_closest_marker(nombre) for nombre in ("slow", "gui")):
            item.add_marker(pytest.mark.fast)
