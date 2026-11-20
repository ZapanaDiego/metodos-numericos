"""Elasticidad de la seda: rigidez, módulo, deformación y viabilidad."""

from __future__ import annotations

from dataclasses import dataclass

# Rangos citados en la literatura para seda de araña (dragline):
# módulo ~1-10 GPa, deformación de rotura ~20-35 %.
RANGO_SEDA_PA = (1e9, 10e9)
RANGO_PERMISIVO_PA = (100e6, 10e9)


def k_a_E(k_n_m: float, longitud_m: float, area_m2: float) -> float:
    """Módulo de Young implícito por la rigidez de una barra."""
    return float(k_n_m * longitud_m / area_m2)


def E_a_k(modulo_pa: float, longitud_m: float, area_m2: float) -> float:
    return float(modulo_pa * area_m2 / longitud_m)


def deformacion(x_m: float, longitud_m: float) -> float:
    return float(x_m / longitud_m)


def esfuerzo(modulo_pa: float, deformacion: float) -> float:
    return float(modulo_pa * deformacion)


def energia_especifica(modulo_pa: float, deformacion: float) -> float:
    """Energía elástica por unidad de volumen."""
    return float(0.5 * modulo_pa * deformacion**2)


def dentro_de_rango(
    modulo_pa: float,
    rango: tuple[float, float] = RANGO_PERMISIVO_PA,
) -> bool:
    return bool(rango[0] <= modulo_pa <= rango[1])


def dentro_de_rango_dragline(modulo_pa: float) -> bool:
    return dentro_de_rango(modulo_pa, RANGO_SEDA_PA)


@dataclass(frozen=True)
class Viabilidad:
    modulo_pa: float
    deformacion: float
    espacio_libre_m: float
    estiramiento_m: float

    @property
    def modulo_ok(self) -> bool:
        return dentro_de_rango_dragline(self.modulo_pa)

    @property
    def deformacion_ok(self) -> bool:
        return self.deformacion <= 0.30

    @property
    def espacio_ok(self) -> bool:
        return self.estiramiento_m <= self.espacio_libre_m

    @property
    def viable(self) -> bool:
        return self.modulo_ok and self.deformacion_ok and self.espacio_ok

    @property
    def motivo(self) -> str:
        fallos = []
        if not self.modulo_ok:
            fallos.append("módulo fuera del rango de la seda dragline (1-10 GPa)")
        if not self.deformacion_ok:
            fallos.append("deformación por encima del 30 % de rotura")
        if not self.espacio_ok:
            fallos.append("se estira más que el espacio libre hasta el suelo")
        return "viable" if not fallos else "; ".join(fallos)
