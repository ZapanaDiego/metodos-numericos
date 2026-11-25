"""Fuente única de inicialización de todas las variables del proyecto.

Centraliza los parámetros físicos, geométricos, anatómicos, numéricos y las
constantes derivadas de las EDO del escenario base para que el resto de los
módulos de ``simulador/``, ``visual/`` y ``experimentos/`` los instancien desde
un único lugar.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# ---------------------------------------------------------------------------
# 1. Variables fisicas y geométricas primarias (Escenario base congelado)
# ---------------------------------------------------------------------------
MASA_KG: float = 50.0  # m: masa total del cuerpo (kg)
GRAVEDAD_M_S2: float = 9.81  # g: aceleración de la gravedad (m/s²)
G: float = GRAVEDAD_M_S2  # alias corto usado en fórmulas
DENSIDAD_AIRE_KG_M3: float = 1.20  # ρ: densidad del aire (kg/m³)
CD_AREA_M2: float = 0.60  # Cd·A: área de arrastre efectiva en caída dorsal (m²)

H_ANCLA_M: float = 43.60  # h_ancla: altura del punto de anclaje de la seda (m)
CAIDA_M: float = 42.00  # H: distancia de caída libre hasta el tensado (m)
LONGITUD_SEDA_M: float = 42.00  # L: longitud natural de la seda sin estirar (m)
AREA_SEDA_M2: float = 2.5e-5  # A_seda: área transversal de la hebra (25 mm² = 2.5e-5 m²)
ESTIRAMIENTO_CAL_M: float = 0.40  # x_cal: estiramiento de calibración en la escena (m)

ALTURA_TORSO_FINAL_M: float = round(H_ANCLA_M - LONGITUD_SEDA_M - ESTIRAMIENTO_CAL_M, 12)  # 1.20 m
ESPACIO_LIBRE_M: float = round(H_ANCLA_M - LONGITUD_SEDA_M, 12)  # 1.60 m
CAIDA_TORRE_M: float = 70.40  # caída desde la cúspide de la torre (m)

# ---------------------------------------------------------------------------
# 2. Constantes exactas de las EDO (Fase 1: caída y Fase 2: frenado elástico)
# ---------------------------------------------------------------------------
# c = ½ ρ Cd A (kg/m) -> F_aire = c v²
C_ARRASTRE_KG_M: float = 0.5 * DENSIDAD_AIRE_KG_M3 * CD_AREA_M2  # 0.36 kg/m

# coef = c / m (m⁻¹) -> EDO 1: v' = g - coef · v²
COEF_CAIDA_M_INV: float = C_ARRASTRE_KG_M / MASA_KG  # 0.0072 m⁻¹

# v_t = sqrt(g / coef) = sqrt(2 m g / (ρ Cd A)) (m/s)
VELOCIDAD_TERMINAL_M_S: float = float(
    np.sqrt(2.0 * MASA_KG * GRAVEDAD_M_S2 / (DENSIDAD_AIRE_KG_M3 * CD_AREA_M2))
)  # 36.91205765058349 m/s

# Estado exacto en el evento de tensado y(t_f) = H = 42.00 m
_EXPONENTE_CAIDA: float = GRAVEDAD_M_S2 * CAIDA_M / (VELOCIDAD_TERMINAL_M_S * VELOCIDAD_TERMINAL_M_S)
T_TENSADO_REF_S: float = float(
    (VELOCIDAD_TERMINAL_M_S / GRAVEDAD_M_S2) * np.arccosh(np.exp(_EXPONENTE_CAIDA))
)
V0_REF_M_S: float = float(
    VELOCIDAD_TERMINAL_M_S * np.tanh(GRAVEDAD_M_S2 * T_TENSADO_REF_S / VELOCIDAD_TERMINAL_M_S)
)  # 24.865757761168984 m/s

# k = m (v0² + 2 g x_cal) / x_cal² (N/m)
K_CALIBRADA_N_M: float = float(
    MASA_KG * (V0_REF_M_S**2 + 2.0 * GRAVEDAD_M_S2 * ESTIRAMIENTO_CAL_M) / (ESTIRAMIENTO_CAL_M**2)
)  # 195678.991731443 N/m

# ω² = k / m (s⁻²) -> EDO 2: v' = g - ω² x
OMEGA2_S_INV2: float = float(K_CALIBRADA_N_M / MASA_KG)  # 3913.57983462886 s⁻²

# ω = sqrt(k / m) (rad/s) y período elástico T = 2π / ω (s)
OMEGA_RAD_S: float = float(np.sqrt(OMEGA2_S_INV2))  # 62.55861119485358 rad/s
PERIODO_ELASTICO_S: float = float(2.0 * np.pi / OMEGA_RAD_S)  # 0.10043677671419184 s

# ---------------------------------------------------------------------------
# 3. Propiedades del material, umbrales biomecánicos y segmentos anatómicos
# ---------------------------------------------------------------------------
DEFORMACION_ROTURA: float = 0.30  # ε_rotura = 30 %
RANGO_SEDA_PA: tuple[float, float] = (1e9, 10e9)  # seda dragline real (1–10 GPa)
RANGO_PERMISIVO_PA: tuple[float, float] = (100e6, 10e9)

OBJETIVO_SUPERVIVENCIA_G: float = 6.0  # umbral de desaceleración tolerable (g)
UMBRAL_HIC: float = 700.0  # criterio de daño craneal HIC-36
VENTANA_HIC_S: float = 0.036  # ventana máxima de HIC (36 ms)
UMBRAL_CUELLO_SEGURO_NM: float = 30.0
UMBRAL_CUELLO_LIMITE_NM: float = 90.0

# Masas y brazos cuasiestáticos de cabeza y piernas
MASA_CABEZA_KG: float = 5.0
MASA_PIERNAS_KG: float = 20.0
R_CUELLO_M: float = 0.18
R_CADERA_M: float = 0.45

# Parámetros de los dos osciladores sagitales y geometría de contacto (mediciones.py y visor 3D)
PIVOTE_CUELLO_M: float = 0.39
BRAZO_CONTACTO_CABEZA_M: float = 0.18
RADIO_CABEZA_M: float = 0.10
INERCIA_CABEZA_KG_M2: float = 0.22
RIGIDEZ_CUELLO_NM_RAD: float = 45.0
AMORTIGUAMIENTO_CUELLO_NM_S_RAD: float = 1.2
REPOSO_CABEZA_RAD: float = 0.0

PIVOTE_CADERA_M: float = 0.27
BRAZO_CONTACTO_PIERNAS_M: float = 0.79
RADIO_PIERNAS_M: float = 0.08
INERCIA_PIERNAS_KG_M2: float = 5.0
RIGIDEZ_CADERA_NM_RAD: float = 120.0
AMORTIGUAMIENTO_CADERA_NM_S_RAD: float = 5.0
REPOSO_PIERNAS_RAD: float = 0.0

# ---------------------------------------------------------------------------
# 4. Cómputo numérico, pasos de integración h, Monte Carlo y escenarios
# ---------------------------------------------------------------------------
PASO_BASE_S: float = 0.001  # h = 1 ms: paso base del visor Panda3D y del CSV e11
PASO_COMPUTO_DEFAULT_S: float = 1e-4  # dt_s = 0.1 ms por defecto en Computo
PASOS_VISOR_MS: tuple[float, ...] = (0.25, 0.5, 1, 2, 4, 8)
INDICE_PASO_BASE_VISOR: int = 2  # índice correspondiente a 1 ms en PASOS_VISOR_MS
PASOS_CONVERGENCIA_S: tuple[float, ...] = (0.008, 0.004, 0.002, 0.001, 0.0005)
METODO_DEFAULT: str = "rk4"
SEMILLA_DEFAULT: int = 42

# Escenarios de piso en el visor Panda3D: (altura_piso_m, postura_piernas_rad)
ESCENARIOS_PISO: tuple[tuple[float, float], ...] = (
    (0.0, 0.0),
    (1.00, -0.50),
    (0.85, 0.0),
)

# Geometría de la torre en la escena 3D
ALTURA_TORRE_M: float = 72.0
LADO_TORRE_M: float = 18.0

# Parámetros de muestreo estocástico / Monte Carlo y vista de parámetros
K_MEDIA_MC_N_M: float = 195739.0
MASA_SD_MC_KG: float = 3.0
CAIDA_SD_MC_M: float = 0.5
K_SIGMA_LOG_MC: float = 0.08
CD_AREA_MIN_MC_M2: float = 0.40
CD_AREA_MAX_MC_M2: float = 0.80


@dataclass(frozen=True)
class VariablesModelo:
    """Contenedor inmutable con las variables principales de las EDO y geometría."""

    m: float = MASA_KG
    g: float = GRAVEDAD_M_S2
    rho: float = DENSIDAD_AIRE_KG_M3
    cd_area: float = CD_AREA_M2
    c: float = C_ARRASTRE_KG_M
    coef: float = COEF_CAIDA_M_INV
    v_t: float = VELOCIDAD_TERMINAL_M_S
    h_ancla: float = H_ANCLA_M
    H: float = CAIDA_M
    L: float = LONGITUD_SEDA_M
    area_seda: float = AREA_SEDA_M2
    x_cal: float = ESTIRAMIENTO_CAL_M
    altura_torso_final: float = ALTURA_TORSO_FINAL_M
    espacio_libre: float = ESPACIO_LIBRE_M
    t_tensado_ref: float = T_TENSADO_REF_S
    v0_ref: float = V0_REF_M_S
    k: float = K_CALIBRADA_N_M
    omega2: float = OMEGA2_S_INV2
    omega: float = OMEGA_RAD_S
    periodo_elastico: float = PERIODO_ELASTICO_S
    h: float = PASO_BASE_S


VARIABLES_BASE = VariablesModelo()
