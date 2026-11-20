"""Modelo de la vista de parámetros, independiente de Tk.

Sirve para probar la lógica de edición y sincronización sin abrir ventanas.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

from simulador.modelo import Resultado, simular
from simulador.parametros import Computo, Cuerpo, Escena, Telarana


@dataclass
class ParametrosVista:
    masa_kg: float = 50.0
    estiramiento_m: float = 0.40
    k_n_m: float = 195739.0
    longitud_m: float = 42.0
    semilla: int = 42
    aire: bool = True
    tumbling: bool = False
    modo: str = "calibracion"
    computo: Computo = field(default_factory=Computo)

    RANGOS = {
        "masa_kg": (30.0, 100.0),
        "estiramiento_m": (0.01, 1.59),
        "k_n_m": (10.0, 1e6),
        "longitud_m": (10.0, 100.0),
        "semilla": (0, 2**32 - 1),
    }

    def set_valor(self, clave: str, valor) -> None:
        if clave == "semilla":
            valor = int(valor)
        else:
            valor = float(valor)
            if not np.isfinite(valor):
                raise ValueError("El valor debe ser finito.")
        if clave in self.RANGOS:
            lo, hi = self.RANGOS[clave]
            if not (lo <= valor <= hi):
                raise ValueError(f"{clave} debe estar en [{lo}, {hi}].")
        if clave == "estiramiento_m":
            self.modo = "calibracion"
        elif clave == "k_n_m":
            self.modo = "material"
        setattr(self, clave, valor)

    def restablecer(self) -> None:
        self.masa_kg = 50.0
        self.estiramiento_m = 0.40
        self.k_n_m = 195739.0
        self.longitud_m = 42.0
        self.semilla = 42
        self.aire = True
        self.tumbling = False
        self.modo = "calibracion"

    def cd_area_efectiva(self) -> float:
        if not self.aire:
            return 0.0
        if not self.tumbling:
            return 0.6
        # proxy determinista: el tumbling muestrea un Cd·A efectivo
        return float(0.6 + 0.15 * np.sin(self.semilla % 997))

    def escena(self) -> Escena:
        L = float(self.longitud_m)
        h_ancla = L + 1.60
        if self.modo == "calibracion":
            x = float(self.estiramiento_m)
            h_torso = h_ancla - L - x
            tel = Telarana(longitud_m=L, estiramiento_m=x, k_n_m=None)
        else:
            h_torso = 1.20
            tel = Telarana(longitud_m=L, estiramiento_m=None, k_n_m=float(self.k_n_m))
        cuerpo = Cuerpo(masa_kg=float(self.masa_kg), cd_area_m2=self.cd_area_efectiva())
        return Escena(
            h_ancla_m=h_ancla,
            caida_m=L,
            altura_torso_m=h_torso,
            cuerpo=cuerpo,
            telarana=tel,
            modo=self.modo,
            gravedad_m_s2=9.81,
        )

    def simular(self) -> Resultado:
        return simular(self.escena(), n_caida=3000, n_resorte=3000)

    def k_efectiva(self) -> float:
        from simulador.analitica import caida_con_arrastre, caida_sin_aire, k_desde_elongacion

        e = self.escena()
        if e.cuerpo.cd_area_m2 > 0:
            _, v0, _ = caida_con_arrastre(
                e.caida_m, e.cuerpo.masa_kg, e.cuerpo.cd_area_m2, e.cuerpo.densidad_aire_kg_m3
            )
        else:
            _, v0 = caida_sin_aire(e.caida_m)
        return k_desde_elongacion(v0, self.estiramiento_m, self.masa_kg)

    def valores_ui(self) -> dict:
        return {
            "masa_kg": self.masa_kg,
            "estiramiento_m": self.estiramiento_m,
            "k_n_m": self.k_efectiva() if self.modo == "calibracion" else self.k_n_m,
            "longitud_m": self.longitud_m,
            "semilla": self.semilla,
        }
