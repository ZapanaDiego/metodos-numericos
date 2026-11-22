"""Cuerpo articulado: momentos cervical y de cadera, y pose para la escena.

El anclaje está en el torso. La cabeza y las piernas son segmentos unidos por
el cuello y la cadera. No se modela el golpe contra el suelo: el torso se
detiene a 1.20 m y los segmentos permanecen por encima del piso.

Los momentos son la estimación cuasiestática de la carga inercial:
``M = m_segmento · r · (a_t + g)`` con ``a_t`` la aceleración del torso hacia
arriba (positiva). En caída libre ``a_t = -g`` y el momento es cero.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .parametros import Cuerpo, G


@dataclass(frozen=True)
class Momentos:
    cuello_n_m: float
    cadera_n_m: float
    a_t_m_s2: float

    @property
    def cuello_kn_m(self) -> float:
        return self.cuello_n_m / 1e3


def momento_cuello(
    a_t_m_s2: float,
    cuerpo: Cuerpo,
    gravedad_m_s2: float = G,
) -> float:
    return float(cuerpo.masa_cabeza_kg * cuerpo.r_cuello_m * (a_t_m_s2 + gravedad_m_s2))


def momento_cadera(
    a_t_m_s2: float,
    cuerpo: Cuerpo,
    gravedad_m_s2: float = G,
) -> float:
    return float(cuerpo.masa_piernas_kg * cuerpo.r_cadera_m * (a_t_m_s2 + gravedad_m_s2))


def momentos(a_t_m_s2: float, cuerpo: Cuerpo, gravedad_m_s2: float = G) -> Momentos:
    return Momentos(
        cuello_n_m=momento_cuello(a_t_m_s2, cuerpo, gravedad_m_s2),
        cadera_n_m=momento_cadera(a_t_m_s2, cuerpo, gravedad_m_s2),
        a_t_m_s2=float(a_t_m_s2),
    )


def posiciones(
    altura_torso_m,
    cuerpo: Cuerpo,
    angulo_cuello_rad=0.0,
    angulo_cadera_rad=0.0,
):
    """Devuelve ``(cabeza, torso, cadera)`` como alturas sobre el suelo.

    ``angulo_cuello`` y ``angulo_cadera`` son pequeños giros respecto de la
    vertical; se usan para la animación, no para el cálculo de momentos.
    """
    h = np.asarray(altura_torso_m, dtype=float)
    cabeza = h + cuerpo.r_cuello_m * np.cos(np.asarray(angulo_cuello_rad))
    cadera = h - cuerpo.r_cadera_m * np.cos(np.asarray(angulo_cadera_rad))
    return cabeza, h, cadera


def perfil_momentos(resultado, cuerpo: Cuerpo, gravedad_m_s2: float = G):
    """Momentos a lo largo de la fase elástica, con ``a_t`` del modelo."""
    fase = resultado.fase == 1
    a_t = resultado.a_m_s2[fase]
    m_cuello = cuerpo.masa_cabeza_kg * cuerpo.r_cuello_m * (a_t + gravedad_m_s2)
    m_cadera = cuerpo.masa_piernas_kg * cuerpo.r_cadera_m * (a_t + gravedad_m_s2)
    return resultado.t[fase], m_cuello, m_cadera


def clasificar_momento(m_cuello_n_m: float) -> str:
    """Umbral orientativo de tolerancia cervical: 30-90 N·m."""
    if m_cuello_n_m <= 30.0:
        return "seguro"
    if m_cuello_n_m <= 90.0:
        return "limite"
    return "letal"
