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

G = 9.81


@dataclass(frozen=True)
class Cuerpo:
    """Cuerpo rígido aproximado y sus segmentos para el latigazo."""

    masa_kg: float = 50.0
    cd_area_m2: float = 0.6
    densidad_aire_kg_m3: float = 1.20
    masa_cabeza_kg: float = 5.0
    masa_piernas_kg: float = 20.0
    r_cuello_m: float = 0.18
    r_cadera_m: float = 0.45

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

    longitud_m: float = 42.0
    area_m2: float = 2.5e-5
    estiramiento_m: float | None = 0.40
    k_n_m: float | None = None
    modulo_pa: float | None = None
    deformacion_rotura: float = 0.30

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

    h_ancla_m: float = 43.60
    caida_m: float = 42.00
    altura_torso_m: float = 1.20
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
        return cls(caida_m=70.40)

    @classmethod
    def supervivencia(cls, objetivo_g: float = 6.0) -> "Escena":
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

    dt_s: float = 1e-4
    metodo: str = "rk4"
    semilla: int = 42

    def __post_init__(self) -> None:
        if self.dt_s <= 0:
            raise ValueError("dt debe ser positivo.")
        if not 0 <= self.semilla < 2**32:
            raise ValueError("La semilla debe estar en [0, 2**32).")
