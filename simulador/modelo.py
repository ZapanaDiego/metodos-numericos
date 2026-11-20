"""Modelo determinista de la caída y del frenado.

``simular`` usa las formas cerradas para producir las trayectorias que consumen
la app, los experimentos y Monte Carlo. ``simular_caida_numerica`` integra la
fase de caída con RK4 y localiza el evento de tensado con un spline cúbico
Hermite, para la validación de I06.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.interpolate import CubicHermiteSpline
from scipy.optimize import brentq

from .analitica import (
    a_resorte_de_t,
    amax_analitica,
    caida_con_arrastre,
    caida_sin_aire,
    elongacion_desde_k,
    energia_resorte,
    k_desde_elongacion,
    t_pico_analitico,
    tiempo_para_elongacion,
    v_de_t,
    v_resorte_de_t,
    x_de_t,
    y_de_t,
)
from .parametros import Escena

G = 9.81


@dataclass
class Resultado:
    """Trayectorias y escalares de una simulación."""

    escena: Escena
    t: np.ndarray
    altura_torso_m: np.ndarray
    v_m_s: np.ndarray
    a_m_s2: np.ndarray
    fuerza_n: np.ndarray
    potencia_w: np.ndarray
    fase: np.ndarray
    t_tensado_s: float
    t_pico_s: float
    v0_m_s: float
    k_n_m: float
    x_max_m: float
    a_max_m_s2: float
    f_max_n: float
    p_max_w: float
    energia_j: float
    modulo_seda_pa: float
    deformacion: float
    t_impacto_s: float = float("nan")
    a_max_g: float = 0.0
    resumen_extra: dict = field(default_factory=dict)

    @property
    def altura_inicial_m(self) -> float:
        return float(self.altura_torso_m[0])

    @property
    def recorre_suelo(self) -> bool:
        return np.any(self.altura_torso_m <= 0.0)

    @property
    def semaforo(self) -> str:
        return "supervivencia" if self.a_max_g <= 6.0 else "letal"

    def momentos(self):
        """Momentos cervical y de cadera en el pico de aceleración."""
        from .articulado import momentos

        return momentos(self.a_max_m_s2, self.escena.cuerpo, self.escena.gravedad_m_s2)

    @property
    def hic(self) -> float:
        """HIC equivalente sobre la fase de frenado (pulso real muestreado)."""
        from .energia import hic

        mascara = self.fase == 1
        a = np.abs(self.a_m_s2[mascara]) / self.escena.gravedad_m_s2
        if a.size < 2:
            return 0.0
        dt = float(np.median(np.diff(self.t[mascara])))
        return hic(a, dt)


def _perfil_caida(escena: Escena, n: int = 4000):
    m = escena.cuerpo.masa_kg
    cd = escena.cuerpo.cd_area_m2
    rho = escena.cuerpo.densidad_aire_kg_m3
    g = escena.gravedad_m_s2
    if cd > 0:
        tf, v0, vt = caida_con_arrastre(escena.caida_m, m, cd, rho, g)
    else:
        tf, v0 = caida_sin_aire(escena.caida_m, g)
        vt = np.inf
    t1 = np.linspace(0.0, tf, n)
    y1 = y_de_t(t1, vt, g)
    v1 = v_de_t(t1, vt, g)
    if cd > 0:
        a1 = g - 0.5 * rho * cd * v1 * v1 / m
        f1 = 0.5 * rho * cd * v1 * v1
        p1 = f1 * v1
    else:
        a1 = np.full_like(t1, g)
        f1 = np.zeros_like(t1)
        p1 = np.zeros_like(t1)
    return tf, v0, vt, t1, y1, v1, a1, f1, p1


def simular(escena: Escena, n_caida: int = 4000, n_resorte: int = 4000) -> Resultado:
    """Simula la escena completa y devuelve arrays listos para graficar."""
    escena.validar_geometria()
    m = escena.cuerpo.masa_kg
    g = escena.gravedad_m_s2
    tf, v0, vt, t1, y1, v1, a1, f1, p1 = _perfil_caida(escena, n_caida)

    if escena.modo == "calibracion":
        x_max = float(escena.telarana.estiramiento_m)  # type: ignore[arg-type]
        k = k_desde_elongacion(v0, x_max, m, g)
    else:
        k = float(escena.telarana.k_material_n_m)  # type: ignore[arg-type]
        x_max = elongacion_desde_k(v0, k, m, g)

    tp = t_pico_analitico(v0, k, m, g)
    t2 = np.linspace(0.0, 1.25 * tp, n_resorte)
    x2 = x_de_t(t2, v0, k, m, g)
    v2 = v_resorte_de_t(t2, v0, k, m, g)
    a2 = (k / m) * x2 - g  # positiva hacia arriba
    f2 = k * x2
    p2 = f2 * v2

    t = np.concatenate([t1, tf + t2[1:]])
    y = np.concatenate([y1, escena.caida_m + x2[1:]])
    v = np.concatenate([v1, v2[1:]])
    # Convención única: aceleración positiva hacia arriba. En caída libre es
    # -g; en el frenado es kx/m - g.
    a = np.concatenate([-a1, a2[1:]])
    f = np.concatenate([f1, f2[1:]])
    p = np.concatenate([p1, p2[1:]])
    fase = np.concatenate([np.zeros_like(t1, dtype=int), np.ones_like(t2[1:], dtype=int)])
    altura = escena.h_ancla_m - y

    a_max = amax_analitica(v0, k, m, g)
    espacio = escena.espacio_libre_m
    if x_max > espacio:
        t_imp = tiempo_para_elongacion(espacio, v0, k, m, g)
    else:
        t_imp = float("nan")

    energia = energia_resorte(v0, x_max, m, g)
    modulo = k * escena.telarana.longitud_m / escena.telarana.area_m2
    resumen_extra = {
        "vt_m_s": float(vt),
        "t_caida_s": float(tf),
        "fuerza_peso_n": float(m * g),
        "relacion_fuerza_peso": float(k * x_max / (m * g)),
        "potencia_cota_w": float(k * x_max * v0),
        "tiempo_total_s": float(t[-1]),
    }
    return Resultado(
        escena=escena,
        t=t,
        altura_torso_m=altura,
        v_m_s=v,
        a_m_s2=a,
        fuerza_n=f,
        potencia_w=p,
        fase=fase,
        t_tensado_s=float(tf),
        t_pico_s=float(tp),
        v0_m_s=float(v0),
        k_n_m=float(k),
        x_max_m=float(x_max),
        a_max_m_s2=float(a_max),
        f_max_n=float(k * x_max),
        p_max_w=float(np.max(p)),
        energia_j=float(energia),
        modulo_seda_pa=float(modulo),
        deformacion=float(x_max / escena.telarana.longitud_m),
        t_impacto_s=float(t_imp),
        a_max_g=float(a_max / g),
        resumen_extra=resumen_extra,
    )


# --------------------------------------------------------------- I06: evento
def detectar_evento(
    g_func,
    t_span: tuple[float, float],
    n: int = 20000,
) -> list[float]:
    """Localiza todos los ceros de ``g_func(t)`` en el intervalo.

    Se detecta por cambio de signo y se refina con ``brentq`` (xtol 1e-14).
    No se pierde un cruce que caiga entre dos muestras.
    """
    t0, tf = t_span
    ts = np.linspace(t0, tf, n)
    vals = np.asarray([g_func(t) for t in ts], dtype=float)
    raices = []
    for i in range(len(ts) - 1):
        if vals[i] == 0:
            raices.append(float(ts[i]))
        elif vals[i] * vals[i + 1] < 0:
            raices.append(
                float(brentq(g_func, ts[i], ts[i + 1], xtol=1e-14, rtol=1e-14))
            )
    if vals[-1] == 0:
        raices.append(float(ts[-1]))
    return raices


def _f_caida(t, estado, params):
    y, v = estado
    g, coef = params
    return np.array([v, g - coef * v * v])


def simular_caida_numerica(
    escena: Escena,
    dt: float = 1e-4,
) -> tuple[float, float, np.ndarray, np.ndarray]:
    """Integra la caída con RK4 y devuelve ``(t_tensado, v_tensado, t, y)``.

    El evento ``y = H`` se localiza sobre un spline cúbico Hermite construido
    con las posiciones y velocidades de la malla, no por el paso bruto.
    """
    from .edo import rk4

    m = escena.cuerpo.masa_kg
    cd = escena.cuerpo.cd_area_m2
    rho = escena.cuerpo.densidad_aire_kg_m3
    g = escena.gravedad_m_s2
    coef = 0.5 * rho * cd / m
    tf_aprox = np.sqrt(2 * escena.caida_m / g) * 1.2
    sol = rk4(_f_caida, [0.0, 0.0], (0.0, tf_aprox), dt, (g, coef))
    t, y = sol.t, sol.y[:, 0]
    v = sol.y[:, 1]
    spline = CubicHermiteSpline(t, y, v)
    f_evento = lambda tt: float(spline(tt)) - escena.caida_m
    idx = np.where(y >= escena.caida_m)[0]
    if len(idx) == 0:
        raise RuntimeError("La caída numérica no alcanzó la altura de tensado.")
    i = int(idx[0])
    t_evento = brentq(f_evento, t[max(0, i - 1)], t[i], xtol=1e-14, rtol=1e-14)
    v_evento = float(spline.derivative()(t_evento))
    return float(t_evento), v_evento, t, y
