"""Series de energía y extensión articulada de la trayectoria del torso."""
from dataclasses import dataclass

import numpy as np
from scipy.integrate import cumulative_trapezoid

from .edo import integrar
from .variables import (
    AMORTIGUAMIENTO_CADERA_NM_S_RAD,
    AMORTIGUAMIENTO_CUELLO_NM_S_RAD,
    BRAZO_CONTACTO_CABEZA_M,
    BRAZO_CONTACTO_PIERNAS_M,
    INERCIA_CABEZA_KG_M2,
    INERCIA_PIERNAS_KG_M2,
    PIVOTE_CADERA_M,
    PIVOTE_CUELLO_M,
    RADIO_CABEZA_M,
    RADIO_PIERNAS_M,
    REPOSO_CABEZA_RAD,
    REPOSO_PIERNAS_RAD,
    RIGIDEZ_CADERA_NM_RAD,
    RIGIDEZ_CUELLO_NM_RAD,
)


@dataclass(frozen=True)
class Contacto:
    segmento: str
    tiempo_s: float
    rapidez_normal_m_s: float
    energia_incidente_j: float


def energias(resultado):
    """Balance del modelo puntual con la convención de trabajo sobre el cuerpo."""
    r = resultado
    m = r.escena.cuerpo.masa_kg
    g = r.escena.gravedad_m_s2
    caida = r.t < r.t_tensado_s
    coef = 0.5 * r.escena.cuerpo.densidad_aire_kg_m3 * r.escena.cuerpo.cd_area_m2
    tiempos = np.r_[r.t[caida], r.t_tensado_s]
    velocidades = np.r_[r.v_m_s[caida], r.v0_m_s]
    disipacion = cumulative_trapezoid(coef * velocidades**3, tiempos, initial=0)
    aire = np.interp(r.t, tiempos, disipacion)
    cinetica = 0.5 * m * r.v_m_s**2
    resorte = 0.5 * r.k_n_m * r.elongacion_m**2
    gravedad = m * g * (r.altura_inicial_m - r.altura_torso_m)
    return dict(cinetica_j=cinetica, seda_j=resorte, aire_j=aire,
                gravedad_j=gravedad, residuo_j=cinetica + resorte + aire - gravedad)


@dataclass(frozen=True)
class Segmento:
    nombre: str
    masa_kg: float
    pivote_m: float
    brazo_cm_m: float
    brazo_contacto_m: float
    radio_m: float
    inercia_kg_m2: float
    rigidez_nm_rad: float
    amortiguamiento_nm_s_rad: float
    reposo_rad: float


@dataclass(frozen=True)
class PerfilSegmento:
    t: np.ndarray
    angulo_rad: np.ndarray
    altura_contacto_m: np.ndarray
    rapidez_normal_m_s: np.ndarray
    energia_cinetica_j: np.ndarray
    disipacion_j: np.ndarray
    contacto: Contacto | None


def segmentos(resultado, piso_m=0.0, *, piernas_rad=REPOSO_PIERNAS_RAD):
    """Dos osciladores en el plano sagital forzados por el torso prescrito.

    La posición dorsal es horizontal durante el frenado. El modelo termina
    en el primer contacto y su acoplamiento con el torso es unidireccional.
    """
    r = resultado
    cuerpo = r.escena.cuerpo
    g = r.escena.gravedad_m_s2
    segmentos = (
        Segmento("Cabeza", cuerpo.masa_cabeza_kg, PIVOTE_CUELLO_M, cuerpo.r_cuello_m,
                 BRAZO_CONTACTO_CABEZA_M, RADIO_CABEZA_M, INERCIA_CABEZA_KG_M2,
                 RIGIDEZ_CUELLO_NM_RAD, AMORTIGUAMIENTO_CUELLO_NM_S_RAD, REPOSO_CABEZA_RAD),
        Segmento("Piernas", cuerpo.masa_piernas_kg, PIVOTE_CADERA_M, cuerpo.r_cadera_m,
                 BRAZO_CONTACTO_PIERNAS_M, RADIO_PIERNAS_M, INERCIA_PIERNAS_KG_M2,
                 RIGIDEZ_CADERA_NM_RAD, AMORTIGUAMIENTO_CADERA_NM_S_RAD, piernas_rad),
    )
    t0 = r.t_tensado_s
    duracion = r.t[-1] - t0
    despues = r.t >= t0
    t_acel = r.t[despues] - t0
    a_t = r.a_m_s2[despues]
    if t_acel[0] > 0.0:
        t_acel = np.r_[0., t_acel]
        a_t = np.r_[-g, a_t]
    perfiles = {}
    for s in segmentos:
        def derivada(t, estado, _):
            angulo, omega = estado
            aceleracion = np.interp(t, t_acel, a_t)
            torque = s.masa_kg * s.brazo_cm_m * (aceleracion + g) * np.cos(angulo)
            return np.array([omega, (torque - s.rigidez_nm_rad * (angulo - s.reposo_rad)
                                    - s.amortiguamiento_nm_s_rad * omega) / s.inercia_kg_m2])

        sol = integrar(derivada, [s.reposo_rad, 0.], (0., duracion),
                       r.paso_s or 0.0005, metodo=r.metodo if r.paso_s else "rk4")
        distintos = np.r_[True, np.diff(sol.t) > 0]
        tiempo = t0 + sol.t[distintos]
        angulo, omega = sol.y[distintos].T
        altura = np.interp(tiempo, r.t, r.altura_torso_m)
        velocidad = np.interp(tiempo, r.t, r.v_m_s)
        espacio = altura - s.radio_m - s.brazo_contacto_m * np.sin(angulo) - piso_m
        normal = velocidad + s.brazo_contacto_m * omega * np.cos(angulo)
        v_horizontal = s.brazo_cm_m * omega * np.sin(angulo)
        v_vertical = velocidad + s.brazo_cm_m * omega * np.cos(angulo)
        energia = 0.5 * s.masa_kg * (v_horizontal**2 + v_vertical**2)
        energia += 0.5 * (s.inercia_kg_m2 - s.masa_kg * s.brazo_cm_m**2) * omega**2
        disipacion = cumulative_trapezoid(s.amortiguamiento_nm_s_rad * omega**2, tiempo, initial=0)
        cruces = np.flatnonzero((espacio[:-1] > 0) & (espacio[1:] <= 0))
        contacto = None
        if len(cruces):
            i = cruces[0]
            fraccion = espacio[i] / (espacio[i] - espacio[i + 1])
            instante = tiempo[i] + fraccion * (tiempo[i + 1] - tiempo[i])
            contacto = Contacto(s.nombre, instante, float(np.interp(instante, tiempo, normal)),
                                float(np.interp(instante, tiempo, energia)))
        perfiles[s.nombre] = PerfilSegmento(tiempo, angulo, espacio, normal, energia, disipacion, contacto)
    return perfiles


def primer_contacto(perfiles):
    """Devuelve solo el primer evento de la trayectoria prescrita."""
    return min((p.contacto for p in perfiles.values() if p.contacto),
               key=lambda contacto: contacto.tiempo_s, default=None)
