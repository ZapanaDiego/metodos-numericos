"""Verifica que el README referencia figuras existentes y secciones clave."""

from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
README = RAIZ / "README.md"


def test_secciones_obligatorias():
    texto = README.read_text(encoding="utf-8")
    for seccion in [
        "Introducción",
        "Modelo matemático",
        "Solución analítica",
        "Resultados",
        "Análisis de error",
        "Conclusiones",
        "Ejecución",
    ]:
        assert seccion.lower() in texto.lower(), seccion


def test_figuras_referenciadas_existen():
    texto = README.read_text(encoding="utf-8")
    rutas = re.findall(r"!\[[^\]]*\]\((resultados/[^)]+)\)", texto)
    assert rutas, "el README no referencia figuras"
    for ruta in rutas:
        assert (RAIZ / ruta).exists(), ruta


def test_no_hay_placeholders():
    texto = README.read_text(encoding="utf-8")
    for marca in ["TODO", "FIXME", "XXX"]:
        assert marca not in texto
