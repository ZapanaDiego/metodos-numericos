"""Validación externa contra el análisis de la Universidad de Leicester.

El paper modela una caída de 42 m sin aire, masa 50 kg y calcula la rigidez
necesaria para que la desaceleración máxima sea 6 g. Sus valores redondeados
son: v ≈ 28.7 m/s, x ≈ 16.7 m, k ≈ 204.5 N/m y E ≈ 343 MPa.

La diferencia entre 16.7 y 16.80 es de redondeo: con 6 g exactos y el balance
energético, ``x = 0.4 H``.
"""

from __future__ import annotations

from dataclasses import dataclass

from .analitica import caida_sin_aire, elongacion_desde_k, k_para_aceleracion
from .variables import (
    AREA_SEDA_M2,
    CAIDA_M,
    G,
    LONGITUD_SEDA_M,
    MASA_KG,
    OBJETIVO_SUPERVIVENCIA_G,
)


@dataclass(frozen=True)
class ResultadoLeicester:
    v0_m_s: float
    k_n_m: float
    x_m: float
    modulo_pa: float
    deformacion: float

    @property
    def modulo_mpa(self) -> float:
        return self.modulo_pa / 1e6


def escenario_leicester(
    altura_m: float = CAIDA_M,
    masa_kg: float = MASA_KG,
    objetivo_g: float = OBJETIVO_SUPERVIVENCIA_G,
    area_m2: float = AREA_SEDA_M2,
    longitud_m: float = LONGITUD_SEDA_M,
    gravedad_m_s2: float = G,
) -> ResultadoLeicester:
    """Reproduce el caso de Leicester con formas cerradas."""
    _, v0 = caida_sin_aire(altura_m, gravedad_m_s2)
    k = k_para_aceleracion(v0, masa_kg, objetivo_g, gravedad_m_s2)
    x = elongacion_desde_k(v0, k, masa_kg, gravedad_m_s2)
    modulo = k * longitud_m / area_m2
    return ResultadoLeicester(
        v0_m_s=v0,
        k_n_m=k,
        x_m=x,
        modulo_pa=modulo,
        deformacion=x / longitud_m,
    )
