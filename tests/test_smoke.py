"""Prueba trivial de I01: el paquete se importa."""

import simulador


def test_paquete_importable():
    assert simulador.__version__
