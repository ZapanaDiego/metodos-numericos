"""Proceso de orientación y Monte Carlo vectorizado (Fase 6).

La orientación se modela con un proceso de Ornstein-Uhlenbeck para la
velocidad angular. El área proyectada ``Cd·A`` oscila con ``cos²θ``. El
ensemble se evalúa de forma vectorizada: no hay un bucle por muestra.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

G = 9.81


def ou_proceso(
    n: int,
    dt_s: float,
    lam: float,
    sigma: float,
    rng: np.random.Generator,
    x0: float = 0.0,
) -> np.ndarray:
    """Euler-Maruyama para ``dω = -λ ω dt + σ√(2λ) dW``."""
    x = np.empty(n + 1)
    x[0] = x0
    ruido = rng.standard_normal(n)
    factor = sigma * np.sqrt(2.0 * lam * dt_s)
    for i in range(n):
        x[i + 1] = x[i] - lam * x[i] * dt_s + factor * ruido[i]
    return x


def cd_area(theta, minimo: float = 0.10, maximo: float = 0.70):
    """Área proyectada ``Cd·A(θ) = min + (max-min) cos²θ``."""
    theta = np.asarray(theta, dtype=float)
    return minimo + (maximo - minimo) * np.cos(theta) ** 2


def muestrear_parametros(
    n: int,
    rng: np.random.Generator,
    masa_media: float = 50.0,
    masa_sd: float = 3.0,
    caida_media: float = 42.0,
    caida_sd: float = 0.5,
    k_media: float = 195739.0,
    k_sigma_log: float = 0.08,
    cd_area_min: float = 0.40,
    cd_area_max: float = 0.80,
) -> dict[str, np.ndarray]:
    masa = np.clip(rng.normal(masa_media, masa_sd, n), 40.0, 65.0)
    caida = np.clip(rng.normal(caida_media, caida_sd, n), 40.0, 45.0)
    k = np.exp(rng.normal(np.log(k_media), k_sigma_log, n))
    cd = rng.uniform(cd_area_min, cd_area_max, n)
    return {"masa_kg": masa, "caida_m": caida, "k_n_m": k, "cd_area_m2": cd}


def _v0_vectorizado(altura, masa, cd, rho=1.20, g=G):
    vt = np.sqrt(2.0 * masa * g / (rho * cd))
    t = (vt / g) * np.arccosh(np.exp(g * altura / (vt * vt)))
    return vt * np.tanh(g * t / vt)


def _x_desde_k_vectorizado(v0, k, masa, g=G):
    a = k
    b = -2.0 * masa * g
    c = -masa * v0**2
    return (-b + np.sqrt(b * b - 4 * a * c)) / (2 * a)


@dataclass
class Ensemble:
    masa_kg: np.ndarray
    caida_m: np.ndarray
    k_n_m: np.ndarray
    cd_area_m2: np.ndarray
    v0_m_s: np.ndarray
    x_max_m: np.ndarray
    a_max_g: np.ndarray
    energia_j: np.ndarray
    t_pico_s: np.ndarray
    hic: np.ndarray
    momento_cuello_n_m: np.ndarray

    def estadisticas(self, campo: str) -> dict:
        v = np.asarray(getattr(self, campo), dtype=float)
        return {
            "media": float(np.mean(v)),
            "desviacion": float(np.std(v, ddof=1)),
            "error_estandar": float(np.std(v, ddof=1) / np.sqrt(v.size)),
            "p5": float(np.percentile(v, 5)),
            "p50": float(np.percentile(v, 50)),
            "p95": float(np.percentile(v, 95)),
            "min": float(np.min(v)),
            "max": float(np.max(v)),
        }

    def fraccion(self, campo: str, umbral: float) -> float:
        v = np.asarray(getattr(self, campo), dtype=float)
        return float(np.mean(v > umbral))


def simular_ensemble(
    n: int = 2000,
    semilla: int = 42,
    escena_base=None,
) -> Ensemble:
    """Monte Carlo vectorizado del escenario base."""
    from .parametros import Escena

    if n < 1:
        raise ValueError("n debe ser positivo.")
    escena = escena_base or Escena.pelicula()
    rng = np.random.default_rng(semilla)
    p = muestrear_parametros(n, rng)
    masa = p["masa_kg"]
    caida = p["caida_m"]
    k = p["k_n_m"]
    cd = p["cd_area_m2"]
    g = escena.gravedad_m_s2
    v0 = _v0_vectorizado(caida, masa, cd, escena.cuerpo.densidad_aire_kg_m3, g)
    x = _x_desde_k_vectorizado(v0, k, masa, g)
    a = np.sqrt(g * g + (k / masa) * v0 * v0)
    a_g = a / g
    w = np.sqrt(k / masa)
    tp = (np.pi - np.arctan(v0 * w / g)) / w
    energia = 0.5 * masa * v0**2 + masa * g * x
    # HIC equivalente con pulso constante de duración t_pico
    hic = tp * a_g**2.5
    m_cuello = 5.0 * 0.18 * (a + g)
    return Ensemble(
        masa_kg=masa,
        caida_m=caida,
        k_n_m=k,
        cd_area_m2=cd,
        v0_m_s=v0,
        x_max_m=x,
        a_max_g=a_g,
        energia_j=energia,
        t_pico_s=tp,
        hic=hic,
        momento_cuello_n_m=m_cuello,
    )
