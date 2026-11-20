"""Utilidades de figuración compartidas por los experimentos."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "resultados"
RESULTADOS.mkdir(exist_ok=True)

COLORES = {
    "azul": "#1f4e79",
    "rojo": "#c0392b",
    "verde": "#1e8449",
    "naranja": "#d35400",
    "morado": "#7d3c98",
    "gris": "#5d6d7e",
    "dorado": "#b7950b",
}


def configurar():
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 160,
            "font.size": 10,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.autolayout": True,
        }
    )


def guardar(fig, nombre: str, cerrar: bool = True) -> Path:
    ruta = RESULTADOS / nombre
    fig.savefig(ruta, bbox_inches="tight")
    if cerrar:
        plt.close(fig)
    return ruta


def figura(nombre: str, figsize=(8, 5)):
    configurar()
    fig, ax = plt.subplots(figsize=figsize)
    fig.suptitle(nombre, fontsize=11)
    return fig, ax
