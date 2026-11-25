"""Parámetros físicos y geometría de la escena.

Todas las magnitudes llevan unidades en el nombre para evitar ambigüedades.
La escena base reproduce el escenario de la película con arrastre cuadrático:

    h_ancla - L - x_max = altura del torso
    43.60 - 42.00 - 0.40 = 1.20 m

Los presets son inmutables; cualquier cambio se hace construyendo una escena
nueva con ``dataclasses.replace``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .variables import (
    ALTURA_TORSO_FINAL_M,
    AREA_SEDA_M2,
    CAIDA_M,
    CAIDA_TORRE_M,
    CD_AREA_M2,
    DEFORMACION_ROTURA,
    DENSIDAD_AIRE_KG_M3,
    ESTIRAMIENTO_CAL_M,
    G,
    H_ANCLA_M,
    LONGITUD_SEDA_M,
    MASA_CABEZA_KG,
    MASA_KG,
    MASA_PIERNAS_KG,
    METODO_DEFAULT,
    OBJETIVO_SUPERVIVENCIA_G,
    PASO_BASE_S,
    PASO_COMPUTO_DEFAULT_S,
    R_CADERA_M,
    R_CUELLO_M,
    SEMILLA_DEFAULT,
)


@dataclass(frozen=True)
class Cuerpo:
    """Cuerpo rígido aproximado y sus segmentos para el latigazo."""

    masa_kg: float = MASA_KG
    cd_area_m2: float = CD_AREA_M2
    densidad_aire_kg_m3: float = DENSIDAD_AIRE_KG_M3
    masa_cabeza_kg: float = MASA_CABEZA_KG
    masa_piernas_kg: float = MASA_PIERNAS_KG
    r_cuello_m: float = R_CUELLO_M
    r_cadera_m: float = R_CADERA_M

    def __post_init__(self) -> None:
        if self.masa_kg <= 0:
            raise ValueError("La masa del cuerpo debe ser positiva.")
        if self.cd_area_m2 < 0:
            raise ValueError("Cd·A no puede ser negativo.")
        if self.densidad_aire_kg_m3 <= 0:
            raise ValueError("La densidad del aire debe ser positiva.")


@dataclass(frozen=True)
class Telarana:
    """Telaraña elástica lineal.

    En modo calibración se fija ``estiramiento_m`` y se despeja ``k_n_m``.
    En modo material se fija ``k_n_m`` (o ``modulo_pa``) y se despeja el
    estiramiento.
    """

    longitud_m: float = LONGITUD_SEDA_M
    area_m2: float = AREA_SEDA_M2
    estiramiento_m: float | None = ESTIRAMIENTO_CAL_M
    k_n_m: float | None = None
    modulo_pa: float | None = None
    deformacion_rotura: float = DEFORMACION_ROTURA

    def __post_init__(self) -> None:
        if self.longitud_m <= 0:
            raise ValueError("La longitud de la telaraña debe ser positiva.")
        if self.area_m2 <= 0:
            raise ValueError("El área de la seda debe ser positiva.")
        if self.estiramiento_m is not None and self.estiramiento_m <= 0:
            raise ValueError("El estiramiento debe ser positivo.")
        if self.k_n_m is not None and self.k_n_m <= 0:
            raise ValueError("k debe ser positivo.")
        if self.modulo_pa is not None and self.modulo_pa <= 0:
            raise ValueError("El módulo de elasticidad debe ser positivo.")

    @property
    def k_material_n_m(self) -> float | None:
        """Rigidez implícita por el material, si se conoce."""
        if self.k_n_m is not None:
            return self.k_n_m
        if self.modulo_pa is not None:
            return self.modulo_pa * self.area_m2 / self.longitud_m
        return None


@dataclass(frozen=True)
class Escena:
    """Geometría, cuerpo y telaraña de una simulación."""

    h_ancla_m: float = H_ANCLA_M
    caida_m: float = CAIDA_M
    altura_torso_m: float = ALTURA_TORSO_FINAL_M
    cuerpo: Cuerpo = field(default_factory=Cuerpo)
    telarana: Telarana = field(default_factory=Telarana)
    modo: str = "calibracion"
    gravedad_m_s2: float = G

    def __post_init__(self) -> None:
        if self.h_ancla_m <= 0 or self.caida_m <= 0:
            raise ValueError("Las alturas deben ser positivas.")
        if self.altura_torso_m < 0:
            raise ValueError("La altura del torso no puede ser negativa.")
        if self.modo not in {"calibracion", "material"}:
            raise ValueError("modo debe ser 'calibracion' o 'material'.")
        if self.modo == "material" and self.telarana.k_material_n_m is None:
            raise ValueError(
                "En modo material hay que fijar Telarana.k_n_m o modulo_pa."
            )
        if self.modo == "calibracion" and self.telarana.estiramiento_m is None:
            raise ValueError("En modo calibración hay que fijar estiramiento_m.")

    # ------------------------------------------------------------------ presets
    @classmethod
    def pelicula(cls) -> "Escena":
        """Escenario base: caída con aire y 0.40 m de estiramiento."""
        return cls()

    @classmethod
    def sin_aire(cls) -> "Escena":
        """Escenario de validación de Leicester: sin arrastre."""
        return cls(cuerpo=replace(Cuerpo(), cd_area_m2=0.0))

    @classmethod
    def torre_completa(cls) -> "Escena":
        """Caso paramétrico: caída desde la cúspide (70.4 m)."""
        return cls(caida_m=CAIDA_TORRE_M)

    @classmethod
    def supervivencia(cls, objetivo_g: float = OBJETIVO_SUPERVIVENCIA_G) -> "Escena":
        """Escenario hipotético de 6 g con la misma caída y arrastre.

        La rigidez se obtiene de ``a_max(k) = objetivo_g·g`` y luego el
        estiramiento se resuelve por energía en modo material.
        """
        from .analitica import caida_con_arrastre, k_para_aceleracion

        base = cls()
        _, v0, _ = caida_con_arrastre(
            base.caida_m,
            base.cuerpo.masa_kg,
            base.cuerpo.cd_area_m2,
            base.cuerpo.densidad_aire_kg_m3,
            base.gravedad_m_s2,
        )
        k = k_para_aceleracion(v0, base.cuerpo.masa_kg, objetivo_g, base.gravedad_m_s2)
        tel = replace(base.telarana, estiramiento_m=None, k_n_m=k)
        return replace(base, telarana=tel, modo="material")

    # --------------------------------------------------------------- validación
    def validar_geometria(self, tol: float = 1e-6) -> None:
        """Comprueba ``h_ancla - L - x = h_torso`` en modo calibración."""
        x = self.telarana.estiramiento_m
        if x is None:
            return
        residuo = self.h_ancla_m - self.telarana.longitud_m - x - self.altura_torso_m
        if abs(residuo) > tol:
            raise ValueError(
                "Geometría inconsistente: "
                f"h_ancla - L - x - h_torso = {residuo:.6f} m "
                f"(h_ancla={self.h_ancla_m}, L={self.telarana.longitud_m}, "
                f"x={x}, h_torso={self.altura_torso_m})."
            )

    @property
    def espacio_libre_m(self) -> float:
        """Distancia del torso al suelo en el instante de tensado."""
        return self.h_ancla_m - self.telarana.longitud_m

    def con(self, **cambios) -> "Escena":
        """Devuelve una copia con campos reemplazados."""
        return replace(self, **cambios)


@dataclass(frozen=True)
class Computo:
    """Parámetros de la integración numérica."""

    dt_s: float = PASO_COMPUTO_DEFAULT_S
    metodo: str = METODO_DEFAULT
    semilla: int = SEMILLA_DEFAULT

    def __post_init__(self) -> None:
        if self.dt_s <= 0:
            raise ValueError("dt debe ser positivo.")
        if not 0 <= self.semilla < 2**32:
            raise ValueError("La semilla debe estar en [0, 2**32).")


CUERPO_BASE = Cuerpo()
TELARANA_BASE = Telarana()
ESCENA_BASE = Escena.pelicula()
COMPUTO_VISOR_BASE = Computo(dt_s=PASO_BASE_S, metodo=METODO_DEFAULT)
