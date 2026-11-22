"""Reproductor de la simulación: transporte, velocidades y cámara lenta."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

VELOCIDADES = (1.0, 0.5, 0.25, 0.1, 0.05)


@dataclass(frozen=True)
class Estado:
    t: float
    altura_torso: float
    v: float
    a_g: float
    fuerza: float
    potencia: float
    fase: int
    x: float
    hic: float
    semaforo: str


class Reproductor:
    """Reproduce un ``Resultado`` precalculado; nunca integra en el bucle."""

    def __init__(self, resultado, fps: int = 60):
        self.resultado = resultado
        self.fps = fps
        self.t_total = float(resultado.t[-1])
        self.t = 0.0
        self.reproduciendo = False
        self._velocidad = 1.0
        alturas = np.asarray(resultado.altura_torso_m, dtype=float)
        self._cached_trayectoria = np.column_stack([np.zeros_like(alturas), np.zeros_like(alturas), alturas])

    @property
    def velocidad(self) -> float:
        return self._velocidad

    def set_velocidad(self, v: float) -> None:
        if v > 1.0 or v <= 0:
            raise ValueError("La velocidad debe estar en (0, 1].")
        if v not in VELOCIDADES:
            # se permite cualquier valor válido, pero se documentan los presets
            pass
        self._velocidad = float(v)

    @property
    def velocidad_efectiva(self) -> float:
        # cámara lenta cinematográfica suave en la ventana de frenado
        t_t = self.resultado.t_tensado_s
        if self.t < t_t - 0.25:
            return self._velocidad
        v_min = min(self._velocidad, 0.05)
        if self.t <= t_t:
            prog = (self.t - (t_t - 0.25)) / 0.25
            factor = 0.5 * (1.0 + np.cos(np.pi * prog))
            return float(v_min + (self._velocidad - v_min) * factor)
        return v_min

    def estado(self, t: float | None = None) -> Estado:
        t = self.t if t is None else float(np.clip(t, 0.0, self.t_total))
        r = self.resultado
        altura = float(np.interp(t, r.t, r.altura_torso_m))
        v = float(np.interp(t, r.t, r.v_m_s))
        a_g = float(np.interp(t, r.t, np.abs(r.a_m_s2) / r.escena.gravedad_m_s2))
        f = float(np.interp(t, r.t, r.fuerza_n))
        p = float(np.interp(t, r.t, r.potencia_w))
        fase = int(round(float(np.interp(t, r.t, r.fase))))
        x = max(0.0, r.escena.h_ancla_m - r.escena.telarana.longitud_m - altura)
        return Estado(t, altura, v, a_g, f, p, fase, x, r.hic, r.semaforo)

    def play(self) -> None:
        self.reproduciendo = True

    def pause(self) -> None:
        self.reproduciendo = False

    def reiniciar(self) -> None:
        self.pause()
        self.t = 0.0

    def seek(self, t: float) -> Estado:
        self.t = float(np.clip(t, 0.0, self.t_total))
        return self.estado()

    def avanzar(self, dt_real: float) -> Estado:
        if self.reproduciendo:
            self.t += dt_real * self.velocidad_efectiva
            if self.t >= self.t_total:
                self.t = self.t_total
                self.reproduciendo = False
        return self.estado()

    def trayectoria_hasta(self, t: float | None = None) -> np.ndarray:
        t = self.t if t is None else float(np.clip(t, 0.0, self.t_total))
        idx = int(np.searchsorted(self.resultado.t, t, side="right"))
        return self._cached_trayectoria[:idx]
