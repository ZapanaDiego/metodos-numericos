"""Personaje femenino 3D articulado y sistema de daños para el visor Panda3D.

Respeta las coordenadas y dimensiones de contacto de ``simulador/mediciones.py``:
- Nodo raíz (``raiz``): agarre abdominal en ``(0, 0, altura)``.
- ``+X`` apunta hacia la cabeza, ``+Z`` hacia el frente ventral y ``-Z`` hacia el
  piso (caída dorsal).
- Pivote del cuello en ``x = +0.39 m`` (centro craneal ``+0.18 m``, radio dorsal ``0.10 m``).
- Pivote de caderas en ``x = -0.27 m`` (talón en ``-0.79 m``, radio dorsal ``0.08 m``).
"""
from __future__ import annotations

from math import cos, degrees, pi, radians, sin

import numpy as np
from panda3d.core import (
    LineSegs,
    NodePath,
    Quat,
    Vec3,
)

from simulador.variables import (
    BRAZO_CONTACTO_CABEZA_M,
    BRAZO_CONTACTO_PIERNAS_M,
    PIVOTE_CADERA_M,
    PIVOTE_CUELLO_M,
    UMBRAL_CUELLO_LIMITE_NM,
)
from .mallas_panda3d import (
    adjuntar_geom,
    malla_elipsoide,
    malla_grietas_piso,
    malla_loft_eje,
    malla_toroide,
    material_superficie,
)

# Paleta anatómica y de vestimenta (Gwen Stacy en caída dorsal)
PIEL = (0.85, 0.66, 0.55, 1.0)
PIEL_SOMBRA = (0.76, 0.57, 0.47, 1.0)
MEJILLA = (0.86, 0.60, 0.52, 1.0)
LABIOS = (0.72, 0.35, 0.37, 1.0)
CABELLO = (0.84, 0.68, 0.36, 1.0)
CABELLO_OSCURO = (0.64, 0.48, 0.23, 1.0)
DIADEMA = (0.08, 0.08, 0.11, 1.0)
ABRIGO = (0.14, 0.47, 0.51, 1.0)
ABRIGO_SOLAPA = (0.09, 0.34, 0.38, 1.0)
BLUSA = (0.82, 0.78, 0.72, 1.0)
CINTURON = (0.10, 0.11, 0.15, 1.0)
HEBILLA = (0.78, 0.64, 0.34, 1.0)
FALDA = (0.13, 0.13, 0.22, 1.0)
MEDIAS = (0.10, 0.10, 0.16, 1.0)
BOTA = (0.07, 0.07, 0.10, 1.0)
SUELA = (0.04, 0.04, 0.06, 1.0)
OJO_BLANCO = (0.92, 0.94, 0.96, 1.0)
OJO_IRIS = (0.18, 0.46, 0.54, 1.0)
OJO_PUPILA = (0.04, 0.04, 0.06, 1.0)
CEJA = (0.44, 0.32, 0.17, 1.0)

ROJO_DANO = (1.0, 0.22, 0.20, 0.82)
AMBAR_DANO = (1.0, 0.58, 0.20, 0.76)
CIAN_SEDA = (0.36, 0.84, 1.0, 1.0)


def inclinacion(nodo: NodePath, grados: float) -> None:
    """Rota un nodo alrededor del eje Y local (plano sagital X-Z)."""
    q = Quat()
    q.setFromAxisAngle(float(grados), Vec3(0, 1, 0))
    nodo.setQuat(q)


def _deformacion_busto(intensidad: float):
    """Esculpe un contorno pectoral femenino suave en la cara ventral (+Z)."""
    def deformar(theta, u1, u2):
        # u1 = Y (lateral), u2 = Z (ventral positivo)
        ventral = np.maximum(0.0, np.sin(theta)) ** 1.35
        lobe_l = np.exp(-((u1 - 0.072) / 0.058) ** 2)
        lobe_r = np.exp(-((u1 + 0.072) / 0.058) ** 2)
        escote = np.exp(-(u1 / 0.032) ** 2)
        dz = intensidad * ventral * (0.044 * (lobe_l + lobe_r) - 0.011 * escote)
        dy = intensidad * ventral * 0.008 * (lobe_l - lobe_r)
        return dy, dz, np.zeros_like(theta)
    return deformar


def _deformacion_caderas(intensidad: float):
    """Curva redondeada de caderas y glúteos en la zona dorsal (-Z)."""
    def deformar(theta, u1, u2):
        dorsal = np.maximum(0.0, -np.sin(theta)) ** 1.4
        lobe_l = np.exp(-((u1 - 0.070) / 0.068) ** 2)
        lobe_r = np.exp(-((u1 + 0.070) / 0.068) ** 2)
        surco = np.exp(-(u1 / 0.025) ** 2)
        dz = -intensidad * dorsal * (0.028 * (lobe_l + lobe_r) - 0.009 * surco)
        return np.zeros_like(theta), dz, np.zeros_like(theta)
    return deformar


def _deformacion_rostro(zona: str):
    """Relieve craneofacial femenino (mentón, pómulos, nariz y cuencas oculares)."""
    def deformar(theta, u1, u2):
        ventral = np.maximum(0.0, np.sin(theta))
        dz = np.zeros_like(theta)
        dy = np.zeros_like(theta)
        dx = np.zeros_like(theta)
        if zona == "menton":
            centro = np.exp(-(u1 / 0.030) ** 2)
            dz += 0.014 * (ventral ** 1.6) * centro
            dx -= 0.008 * ventral * centro
        elif zona == "boca":
            labio = np.exp(-(u1 / 0.025) ** 2)
            dz += 0.010 * (ventral ** 2.0) * labio
        elif zona == "nariz":
            puente = np.exp(-(u1 / 0.014) ** 2)
            mejillas = np.exp(-((np.abs(u1) - 0.046) / 0.025) ** 2)
            dz += (0.022 * puente + 0.008 * mejillas) * (ventral ** 1.8)
            dy += 0.004 * np.sign(u1) * mejillas * ventral
        elif zona == "ojos":
            cuencas = np.exp(-((np.abs(u1) - 0.031) / 0.018) ** 2)
            puente = np.exp(-(u1 / 0.013) ** 2)
            dz += (-0.010 * cuencas + 0.012 * puente) * (ventral ** 1.8)
        elif zona == "cejas":
            arco = np.exp(-((np.abs(u1) - 0.032) / 0.024) ** 2)
            dz += 0.006 * arco * (ventral ** 1.5)
        return dy, dz, dx
    return deformar


class PersonajeFemenino:
    """Modelo femenino 3D articulado con efectos de seda y daños en cuerpo y piso."""

    def __init__(self, render: NodePath, piso: NodePath):
        self.render = render
        self.piso = piso

        self.mat_piel = material_superficie("piel", (0.20, 0.16, 0.14, 1.0), 16.0)
        self.mat_cabello = material_superficie("cabello", (0.34, 0.28, 0.16, 1.0), 28.0)
        self.mat_tela = material_superficie("tela", (0.10, 0.12, 0.13, 1.0), 10.0)
        self.mat_cuero = material_superficie("cuero", (0.36, 0.36, 0.40, 1.0), 46.0)
        self.mat_dano = material_superficie(
            "dano", (0.25, 0.10, 0.10, 1.0), 22.0, emision=(0.75, 0.10, 0.08, 1.0)
        )
        self.mat_onda = material_superficie(
            "onda", (0.30, 0.16, 0.10, 1.0), 16.0, emision=(0.85, 0.24, 0.12, 1.0)
        )

        # Nodo raíz: agarre abdominal exactamente en (0, 0, altura)
        self.raiz = render.attachNewNode("agarre abdominal")
        self.torso = self.raiz.attachNewNode("torso")

        self._construir_tronco()
        self._construir_cabeza()
        self._construir_brazos()
        self._construir_piernas()
        self._construir_abanico_seda()
        self._construir_indicadores_dano()
        self._construir_dano_piso()

        # Exposición compatible con pruebas/atributos existentes
        self.brazos = [self.hombro_der, self.hombro_izq]

    # ----------------------------------------------------------------- tronco
    def _construir_tronco(self) -> None:
        # Perfil anatómico continuo desde pelvis (-0.28) hasta base del cuello (+0.39).
        # Cintura entallada en x = 0.0 con cara ventral tocando z ≈ 0.0 (agarre de seda).
        secciones_tronco = [
            {"pos": -0.285, "c2": -0.068, "r1": 0.138, "r2": (0.068, 0.082), "color": FALDA, "tono": 0.90},
            {"pos": -0.230, "c2": -0.072, "r1": 0.172, "r2": (0.082, 0.102), "color": FALDA, "tono": 0.96,
             "deformar": _deformacion_caderas(1.0)},
            {"pos": -0.155, "c2": -0.074, "r1": 0.166, "r2": (0.080, 0.098), "color": FALDA, "tono": 1.00,
             "deformar": _deformacion_caderas(0.65)},
            {"pos": -0.095, "c2": -0.074, "r1": 0.146, "r2": (0.076, 0.088), "color": ABRIGO, "tono": 0.95},
            {"pos": -0.030, "c2": -0.072, "r1": 0.128, "r2": (0.074, 0.082), "color": CINTURON, "tono": 0.96},
            {"pos": 0.000, "c2": -0.072, "r1": 0.125, "r2": (0.074, 0.081), "color": CINTURON, "tono": 1.02},
            {"pos": 0.030, "c2": -0.072, "r1": 0.130, "r2": (0.075, 0.082), "color": ABRIGO, "tono": 0.97},
            {"pos": 0.105, "c2": -0.072, "r1": 0.149, "r2": (0.084, 0.088), "color": ABRIGO, "tono": 1.00,
             "deformar": _deformacion_busto(0.45)},
            {"pos": 0.185, "c2": -0.070, "r1": 0.166, "r2": (0.090, 0.092), "color": ABRIGO, "tono": 1.04,
             "deformar": _deformacion_busto(1.0)},
            {"pos": 0.255, "c2": -0.068, "r1": 0.174, "r2": (0.086, 0.088), "color": ABRIGO, "tono": 1.02,
             "deformar": _deformacion_busto(0.55)},
            {"pos": 0.315, "c2": -0.062, "r1": 0.168, "r2": (0.072, 0.076), "color": ABRIGO, "tono": 0.98},
            {"pos": 0.358, "c2": -0.048, "r1": 0.105, "r2": (0.056, 0.060), "color": ABRIGO_SOLAPA, "tono": 0.95},
            {"pos": 0.390, "c2": -0.025, "r1": 0.056, "r2": (0.048, 0.050), "color": BLUSA, "tono": 0.96},
        ]
        adjuntar_geom(
            self.torso,
            malla_loft_eje("tronco", secciones_tronco, n_lados=28, color=ABRIGO, sombra_dorsal=0.14),
            self.mat_tela,
        )

        # Escote en V con blusa clara y solapas de la gabardina sobre el pecho
        secciones_escote = [
            {"pos": 0.220, "c2": 0.022, "r1": 0.014, "r2": (0.008, 0.005), "color": BLUSA},
            {"pos": 0.295, "c2": 0.018, "r1": 0.048, "r2": (0.011, 0.006), "color": BLUSA},
            {"pos": 0.355, "c2": 0.005, "r1": 0.058, "r2": (0.012, 0.006), "color": BLUSA},
        ]
        adjuntar_geom(
            self.torso,
            malla_loft_eje("escote_blusa", secciones_escote, n_lados=14, color=BLUSA, sombra_dorsal=0.04),
            self.mat_tela,
        )
        for signo in (-1.0, 1.0):
            secciones_solapa = [
                {"pos": 0.08, "c1": signo * 0.020, "c2": 0.012, "r1": 0.016, "r2": 0.009},
                {"pos": 0.20, "c1": signo * 0.045, "c2": 0.032, "r1": 0.026, "r2": 0.011},
                {"pos": 0.31, "c1": signo * 0.064, "c2": 0.016, "r1": 0.028, "r2": 0.011},
                {"pos": 0.37, "c1": signo * 0.050, "c2": -0.005, "r1": 0.022, "r2": 0.012},
            ]
            adjuntar_geom(
                self.torso,
                malla_loft_eje(f"solapa_{signo:+.0f}", secciones_solapa, n_lados=12, color=ABRIGO_SOLAPA),
                self.mat_tela,
            )

        # Hebilla del cinturón y botones de la gabardina
        hebilla = adjuntar_geom(
            self.torso, malla_elipsoide("hebilla", 0.020, 0.028, 0.008, HEBILLA, n_lon=14, n_lat=8), self.mat_cuero
        )
        hebilla.setPos(0.0, 0.0, 0.004)

        # Faldones articulados de la gabardina (ondean en caída y frenado)
        self.faldones: list[NodePath] = []
        for idx, (signo, dz_base) in enumerate(((-1.0, -0.075), (1.0, -0.075))):
            pivote = self.torso.attachNewNode(f"faldon_{idx}")
            pivote.setPos(-0.07, signo * 0.115, dz_base)
            secciones_faldon = [
                {"pos": 0.0, "c1": 0.0, "c2": 0.0, "r1": 0.048, "r2": (0.055, 0.068)},
                {"pos": -0.14, "c1": signo * 0.024, "c2": -0.006, "r1": 0.054, "r2": (0.058, 0.076)},
                {"pos": -0.28, "c1": signo * 0.042, "c2": -0.014, "r1": 0.056, "r2": (0.052, 0.074)},
                {"pos": -0.37, "c1": signo * 0.052, "c2": -0.022, "r1": 0.050, "r2": (0.036, 0.058)},
            ]
            adjuntar_geom(
                pivote,
                malla_loft_eje(f"malla_faldon_{idx}", secciones_faldon, n_lados=16, color=ABRIGO, sombra_dorsal=0.14),
                self.mat_tela,
            )
            self.faldones.append(pivote)

    # ----------------------------------------------------------------- cabeza
    def _construir_cabeza(self) -> None:
        # Pivote cervical exactamente en x = +0.39 m (simulador/mediciones.py)
        self.cabeza = self.raiz.attachNewNode("cuello")
        self.cabeza.setX(PIVOTE_CUELLO_M)
        self.craneo = self.cabeza.attachNewNode("craneo")

        # Cuello estilizado conectado suavemente desde el tronco hasta la mandíbula
        secciones_cuello = [
            {"pos": -0.028, "c2": -0.024, "r1": 0.056, "r2": 0.050, "tono": 0.90},
            {"pos": 0.015, "c2": -0.016, "r1": 0.046, "r2": 0.045, "tono": 0.96},
            {"pos": 0.058, "c2": -0.012, "r1": 0.044, "r2": 0.045, "tono": 1.00},
            {"pos": 0.095, "c2": -0.008, "r1": 0.048, "r2": 0.049, "tono": 0.98},
        ]
        adjuntar_geom(
            self.craneo,
            malla_loft_eje("cuello_malla", secciones_cuello, n_lados=20, color=PIEL, sombra_dorsal=0.12),
            self.mat_piel,
        )

        # Cabeza y rostro femenino esculpido centrado alrededor de x = +0.18 m,
        # con radio dorsal exacto <= 0.10 m para coincidir con mediciones.py.
        secciones_cabeza = [
            {"pos": 0.082, "c2": 0.036, "r1": 0.024, "r2": (0.032, 0.024), "tono": 0.95,
             "deformar": _deformacion_rostro("menton")},
            {"pos": 0.106, "c2": 0.012, "r1": 0.050, "r2": (0.072, 0.056), "tono": 0.98,
             "deformar": _deformacion_rostro("menton")},
            {"pos": 0.130, "c2": 0.002, "r1": 0.066, "r2": (0.088, 0.082), "tono": 1.00,
             "deformar": _deformacion_rostro("boca")},
            {"pos": 0.158, "c2": -0.002, "r1": 0.076, "r2": (0.092, 0.095), "tono": 1.02,
             "deformar": _deformacion_rostro("nariz")},
            {"pos": 0.185, "c2": -0.004, "r1": 0.079, "r2": (0.090, 0.096), "tono": 1.00,
             "deformar": _deformacion_rostro("ojos")},
            {"pos": 0.210, "c2": -0.004, "r1": 0.078, "r2": (0.089, 0.095), "tono": 1.00,
             "deformar": _deformacion_rostro("cejas")},
            {"pos": 0.242, "c2": -0.005, "r1": 0.072, "r2": (0.080, 0.086), "tono": 0.98},
            {"pos": 0.270, "c2": -0.008, "r1": 0.051, "r2": (0.056, 0.062), "tono": 0.95},
            {"pos": 0.286, "c2": -0.010, "r1": 0.022, "r2": (0.025, 0.028), "tono": 0.92},
        ]
        self.malla_rostro = adjuntar_geom(
            self.craneo,
            malla_loft_eje("cabeza_rostro", secciones_cabeza, n_lados=28, color=PIEL, sombra_dorsal=0.10),
            self.mat_piel,
        )

        # Rasgos faciales delicados: ojos, iris, pupilas, cejas, labios y orejas
        for signo in (-1.0, 1.0):
            # Esclerótica, iris y pupila
            ojo = adjuntar_geom(
                self.craneo, malla_elipsoide(f"ojo_{signo:+.0f}", 0.011, 0.015, 0.009, OJO_BLANCO, 14, 8), self.mat_piel
            )
            ojo.setPos(0.186, signo * 0.030, 0.081)
            iris = adjuntar_geom(
                self.craneo, malla_elipsoide(f"iris_{signo:+.0f}", 0.007, 0.008, 0.005, OJO_IRIS, 12, 8), self.mat_cuero
            )
            iris.setPos(0.186, signo * 0.030, 0.087)
            pupila = adjuntar_geom(
                self.craneo, malla_elipsoide(f"pupila_{signo:+.0f}", 0.0038, 0.0040, 0.0035, OJO_PUPILA, 10, 6), self.mat_cuero
            )
            pupila.setPos(0.186, signo * 0.030, 0.090)

            # Línea de pestañas y ceja arqueada
            pestana = adjuntar_geom(
                self.craneo, malla_elipsoide(f"pestana_{signo:+.0f}", 0.004, 0.017, 0.003, DIADEMA, 10, 6), self.mat_tela
            )
            pestana.setPos(0.194, signo * 0.031, 0.086)
            ceja = adjuntar_geom(
                self.craneo, malla_elipsoide(f"ceja_{signo:+.0f}", 0.0045, 0.022, 0.0035, CEJA, 10, 6), self.mat_cabello
            )
            ceja.setPos(0.207, signo * 0.032, 0.088)
            ceja.setR(signo * -8.0)

            # Rubor sutil en mejilla y oreja
            oreja = adjuntar_geom(
                self.craneo, malla_elipsoide(f"oreja_{signo:+.0f}", 0.022, 0.009, 0.015, PIEL_SOMBRA, 12, 8), self.mat_piel
            )
            oreja.setPos(0.174, signo * 0.079, -0.002)

        # Labios femeninos (superior e inferior)
        labio_sup = adjuntar_geom(
            self.craneo, malla_elipsoide("labio_sup", 0.0055, 0.021, 0.0055, LABIOS, 14, 8), self.mat_piel
        )
        labio_sup.setPos(0.133, 0.0, 0.093)
        labio_inf = adjuntar_geom(
            self.craneo, malla_elipsoide("labio_inf", 0.006, 0.018, 0.0055, LABIOS, 14, 8), self.mat_piel
        )
        labio_inf.setPos(0.125, 0.0, 0.091)

        # Casquete de cabello rubio envolviendo nuca, sienes y frente (sin sobresalir > 0.10 m en -Z)
        secciones_cabello = [
            {"pos": 0.115, "c2": -0.044, "r1": 0.068, "r2": (0.042, 0.052), "color": CABELLO_OSCURO, "tono": 0.92},
            {"pos": 0.155, "c2": -0.036, "r1": 0.086, "r2": (0.056, 0.064), "color": CABELLO, "tono": 0.98},
            {"pos": 0.195, "c2": -0.026, "r1": 0.090, "r2": (0.070, 0.074), "color": CABELLO, "tono": 1.02},
            {"pos": 0.235, "c2": -0.012, "r1": 0.088, "r2": (0.088, 0.086), "color": CABELLO, "tono": 1.05},
            {"pos": 0.268, "c2": -0.008, "r1": 0.074, "r2": (0.076, 0.076), "color": CABELLO, "tono": 1.02},
            {"pos": 0.292, "c2": -0.010, "r1": 0.040, "r2": (0.042, 0.044), "color": CABELLO, "tono": 0.96},
        ]
        self.malla_cabello_base = adjuntar_geom(
            self.craneo,
            malla_loft_eje("cabello_base", secciones_cabello, n_lados=24, color=CABELLO, sombra_dorsal=0.12),
            self.mat_cabello,
        )

        # Flequillo lateral suave integrado en sienes y frente (sin sobresalir como varillas)
        for signo, grosor in ((-1.0, 1.08), (1.0, 0.94)):
            sec_mechon = [
                {"pos": 0.268, "c1": signo * 0.032, "c2": 0.052, "r1": 0.028 * grosor, "r2": 0.015},
                {"pos": 0.232, "c1": signo * 0.068, "c2": 0.044, "r1": 0.025 * grosor, "r2": 0.018},
                {"pos": 0.182, "c1": signo * 0.080, "c2": 0.016, "r1": 0.020 * grosor, "r2": 0.022},
                {"pos": 0.130, "c1": signo * 0.074, "c2": -0.016, "r1": 0.016 * grosor, "r2": 0.020},
                {"pos": 0.095, "c1": signo * 0.064, "c2": -0.036, "r1": 0.009 * grosor, "r2": 0.012},
            ]
            adjuntar_geom(
                self.craneo,
                malla_loft_eje(f"mechon_cara_{signo:+.0f}", sec_mechon, n_lados=14, color=CABELLO, sombra_dorsal=0.10),
                self.mat_cabello,
            )

        # Diadema negra icónica de Gwen Stacy
        diadema = adjuntar_geom(
            self.craneo, malla_toroide("diadema", 0.085, 0.0085, eje="x", color=DIADEMA, n_u=28, n_v=8), self.mat_cuero
        )
        diadema.setPos(0.236, 0.0, -0.004)
        diadema.setScale(1.3, 1.03, 1.07)

        # Melena rubia trasera articulada en 3 tramos fluidos desde la nuca
        self.melena_tramos: list[NodePath] = []
        padre_melena = self.craneo
        longitudes_melena = (
            (0.155, -0.072, -0.145, 0.094, 0.022),
            (-0.145, 0.0, -0.140, 0.086, 0.018),
            (-0.140, 0.0, -0.125, 0.068, 0.013),
        )
        for idx, (ox, oz, largo, ancho, espesor) in enumerate(longitudes_melena):
            nodo_m = padre_melena.attachNewNode(f"melena_{idx}")
            if idx == 0:
                nodo_m.setPos(ox, 0.0, oz)
            else:
                nodo_m.setPos(ox, 0.0, 0.0)
            sec_m = [
                {"pos": 0.0, "c2": 0.0, "r1": ancho, "r2": espesor, "color": CABELLO, "tono": 0.96},
                {"pos": 0.55 * largo, "c2": -0.004, "r1": 0.96 * ancho, "r2": 0.88 * espesor, "color": CABELLO, "tono": 1.03},
                {"pos": largo, "c2": -0.006, "r1": 0.84 * ancho if idx < 2 else 0.28 * ancho,
                 "r2": 0.72 * espesor if idx < 2 else 0.28 * espesor,
                 "color": CABELLO_OSCURO if idx == 2 else CABELLO, "tono": 0.94},
            ]
            adjuntar_geom(
                nodo_m,
                malla_loft_eje(f"malla_melena_{idx}", sec_m, n_lados=18, color=CABELLO, sombra_dorsal=0.14),
                self.mat_cabello,
            )
            self.melena_tramos.append(nodo_m)
            padre_melena = nodo_m

    # ----------------------------------------------------------------- brazos
    def _construir_brazos(self) -> None:
        self.codos: list[NodePath] = []
        self.manos: list[NodePath] = []
        hombros = []
        for signo, nombre in ((-1.0, "der"), (1.0, "izq")):
            hombro = self.raiz.attachNewNode(f"hombro_{nombre}")
            hombro.setPos(0.285, signo * 0.168, -0.062)

            # Empalme redondeado del deltoides
            adjuntar_geom(
                hombro, malla_elipsoide(f"deltoides_{nombre}", 0.056, 0.054, 0.054, ABRIGO, 16, 10), self.mat_tela
            )

            # Brazo superior (manga de la gabardina) a lo largo de ±Y
            sec_brazo = [
                {"pos": 0.0, "c1": 0.0, "c2": 0.0, "r1": 0.048, "r2": 0.050, "tono": 0.96},
                {"pos": signo * 0.08, "c1": 0.0, "c2": -0.014, "r1": 0.045, "r2": 0.047, "tono": 1.00},
                {"pos": signo * 0.18, "c1": 0.003, "c2": -0.028, "r1": 0.041, "r2": 0.042, "tono": 0.98},
                {"pos": signo * 0.26, "c1": 0.005, "c2": -0.038, "r1": 0.038, "r2": 0.039, "tono": 0.95},
            ]
            adjuntar_geom(
                hombro,
                malla_loft_eje(f"brazo_{nombre}", sec_brazo, eje="y", n_lados=18, color=ABRIGO, sombra_dorsal=0.12),
                self.mat_tela,
            )

            # Pivote del codo
            codo = hombro.attachNewNode(f"codo_{nombre}")
            codo.setPos(-0.038, signo * 0.26, 0.005)
            adjuntar_geom(
                codo, malla_elipsoide(f"art_codo_{nombre}", 0.036, 0.036, 0.036, ABRIGO, 14, 8), self.mat_tela
            )

            # Antebrazo (manga con puño + muñeca de piel)
            sec_antebrazo = [
                {"pos": 0.0, "c1": 0.0, "c2": 0.0, "r1": 0.037, "r2": 0.038, "color": ABRIGO, "tono": 0.98},
                {"pos": signo * 0.12, "c1": 0.004, "c2": 0.010, "r1": 0.033, "r2": 0.034, "color": ABRIGO, "tono": 1.00},
                {"pos": signo * 0.185, "c1": 0.006, "c2": 0.015, "r1": 0.031, "r2": 0.032, "color": ABRIGO_SOLAPA, "tono": 0.95},
                {"pos": signo * 0.195, "c1": 0.006, "c2": 0.016, "r1": 0.024, "r2": 0.025, "color": PIEL, "tono": 0.96},
                {"pos": signo * 0.235, "c1": 0.007, "c2": 0.019, "r1": 0.022, "r2": 0.024, "color": PIEL, "tono": 1.00},
            ]
            adjuntar_geom(
                codo,
                malla_loft_eje(f"antebrazo_{nombre}", sec_antebrazo, eje="y", n_lados=16, color=ABRIGO, sombra_dorsal=0.10),
                self.mat_tela,
            )

            # Mano femenina moldeada (palma + bloque de dedos + pulgar)
            mano = codo.attachNewNode(f"mano_{nombre}")
            mano.setPos(0.019, signo * 0.235, 0.007)
            sec_mano = [
                {"pos": 0.0, "c1": 0.0, "c2": 0.0, "r1": 0.016, "r2": 0.028},
                {"pos": signo * 0.045, "c1": 0.002, "c2": 0.004, "r1": 0.014, "r2": 0.034},
                {"pos": signo * 0.095, "c1": 0.004, "c2": 0.006, "r1": 0.010, "r2": 0.028},
                {"pos": signo * 0.135, "c1": 0.003, "c2": 0.006, "r1": 0.006, "r2": 0.016},
            ]
            adjuntar_geom(
                mano,
                malla_loft_eje(f"palma_{nombre}", sec_mano, eje="y", n_lados=14, color=PIEL, sombra_dorsal=0.08),
                self.mat_piel,
            )
            pulgar = adjuntar_geom(
                mano, malla_elipsoide(f"pulgar_{nombre}", 0.024, 0.011, 0.009, PIEL, 10, 6), self.mat_piel
            )
            pulgar.setPos(0.032, signo * 0.035, 0.006)
            pulgar.setH(signo * 32.0)

            hombros.append(hombro)
            self.codos.append(codo)
            self.manos.append(mano)

        self.hombro_der, self.hombro_izq = hombros

    # ---------------------------------------------------------------- piernas
    def _construir_piernas(self) -> None:
        # Pivote de caderas exactamente en x = -0.27 m (simulador/mediciones.py)
        self.piernas = self.raiz.attachNewNode("caderas")
        self.piernas.setX(-PIVOTE_CADERA_M)

        self.muslos: list[NodePath] = []
        self.rodillas: list[NodePath] = []
        self.tobillos: list[NodePath] = []

        for signo, nombre in ((-1.0, "der"), (1.0, "izq")):
            lateral = signo * 0.092
            muslo = self.piernas.attachNewNode(f"muslo_{nombre}")
            muslo.setPos(0.0, lateral, -0.048)

            # Empalme de cadera oculto dentro de la pelvis/falda
            adjuntar_geom(
                muslo, malla_elipsoide(f"cadera_art_{nombre}", 0.080, 0.074, 0.074, FALDA, 16, 10), self.mat_tela
            )

            # Muslo femenino estilizado (falda arriba, medias oscuras abajo)
            sec_muslo = [
                {"pos": 0.02, "c2": -0.004, "r1": 0.076, "r2": (0.068, 0.078), "color": FALDA, "tono": 0.94},
                {"pos": -0.06, "c2": -0.002, "r1": 0.074, "r2": (0.068, 0.076), "color": FALDA, "tono": 0.98},
                {"pos": -0.10, "c2": 0.000, "r1": 0.068, "r2": (0.064, 0.068), "color": MEDIAS, "tono": 0.95},
                {"pos": -0.21, "c2": 0.004, "r1": 0.062, "r2": (0.060, 0.062), "color": MEDIAS, "tono": 1.00},
                {"pos": -0.32, "c2": 0.008, "r1": 0.052, "r2": (0.052, 0.052), "color": MEDIAS, "tono": 0.98},
                {"pos": -0.39, "c2": 0.012, "r1": 0.046, "r2": (0.048, 0.046), "color": MEDIAS, "tono": 0.96},
            ]
            adjuntar_geom(
                muslo,
                malla_loft_eje(f"malla_muslo_{nombre}", sec_muslo, n_lados=20, color=MEDIAS, sombra_dorsal=0.12),
                self.mat_tela,
            )

            # Pivote de rodilla en x_local = -0.39 m
            rodilla = muslo.attachNewNode(f"rodilla_{nombre}")
            rodilla.setPos(-0.39, -signo * 0.008, 0.012)
            adjuntar_geom(
                rodilla, malla_elipsoide(f"art_rodilla_{nombre}", 0.047, 0.046, 0.048, MEDIAS, 16, 10), self.mat_tela
            )

            # Pantorrilla con curva natural del gemelo + bota alta de cuero desde media pierna
            sec_pantorrilla = [
                {"pos": 0.0, "c2": 0.0, "r1": 0.046, "r2": (0.047, 0.046), "color": MEDIAS, "tono": 0.97},
                {"pos": -0.09, "c2": -0.006, "r1": 0.052, "r2": (0.048, 0.058), "color": MEDIAS, "tono": 1.02},
                {"pos": -0.15, "c2": -0.005, "r1": 0.050, "r2": (0.046, 0.055), "color": BOTA, "tono": 1.00},
                {"pos": -0.24, "c2": 0.004, "r1": 0.042, "r2": (0.042, 0.044), "color": BOTA, "tono": 1.02},
                {"pos": -0.33, "c2": 0.016, "r1": 0.036, "r2": (0.039, 0.038), "color": BOTA, "tono": 0.98},
                {"pos": -0.37, "c2": 0.022, "r1": 0.035, "r2": (0.040, 0.038), "color": BOTA, "tono": 0.96},
            ]
            adjuntar_geom(
                rodilla,
                malla_loft_eje(f"malla_pantorrilla_{nombre}", sec_pantorrilla, n_lados=20, color=BOTA, sombra_dorsal=0.12),
                self.mat_cuero,
            )

            # Pivote del tobillo en x_local = -0.37 (total x = -0.76 en piernas)
            tobillo = rodilla.attachNewNode(f"tobillo_{nombre}")
            tobillo.setPos(-0.37, 0.0, 0.022)

            # Bota / pie moldeado: talón centrado en x = -0.03 (total -0.79 en piernas)
            # con borde dorsal en z = -0.08 m (exacto a radio_m = 0.08 de mediciones.py)
            sec_bota = [
                {"pos": 0.015, "c2": 0.006, "r1": 0.036, "r2": (0.042, 0.044), "color": BOTA, "tono": 0.96},
                {"pos": -0.030, "c2": 0.012, "r1": 0.039, "r2": (0.068, 0.066), "color": BOTA, "tono": 1.00},
                {"pos": -0.062, "c2": 0.045, "r1": 0.038, "r2": (0.095, 0.095), "color": BOTA, "tono": 1.04},
                {"pos": -0.082, "c2": 0.072, "r1": 0.033, "r2": (0.088, 0.070), "color": SUELA, "tono": 0.95},
            ]
            adjuntar_geom(
                tobillo,
                malla_loft_eje(f"bota_{nombre}", sec_bota, n_lados=18, color=BOTA, sombra_dorsal=0.10),
                self.mat_cuero,
            )
            # Punta del pie extendiéndose hacia +Z (empeine natural femenino)
            sec_punta = [
                {"pos": 0.01, "c1": -0.048, "c2": 0.0, "r1": 0.036, "r2": 0.038},
                {"pos": 0.08, "c1": -0.056, "c2": 0.0, "r1": 0.032, "r2": 0.036},
                {"pos": 0.14, "c1": -0.058, "c2": 0.0, "r1": 0.024, "r2": 0.028},
                {"pos": 0.175, "c1": -0.055, "c2": 0.0, "r1": 0.013, "r2": 0.018},
            ]
            adjuntar_geom(
                tobillo,
                malla_loft_eje(f"punta_bota_{nombre}", sec_punta, eje="z", n_lados=16, color=BOTA, sombra_dorsal=0.08),
                self.mat_cuero,
            )

            self.muslos.append(muslo)
            self.rodillas.append(rodilla)
            self.tobillos.append(tobillo)

    # -------------------------------------------------------- abanico de seda
    def _construir_abanico_seda(self) -> None:
        self.abanico_seda = self.raiz.attachNewNode("abanico_seda")
        trazo = LineSegs()
        trazo.setThickness(2.0)
        trazo.setColor(*CIAN_SEDA)
        for x in (-0.11, -0.04, 0.04, 0.11):
            for y in (-0.135, 0.135):
                trazo.moveTo(x, y, -0.055)
                trazo.drawTo(0.0, 0.0, 0.010)
        self.abanico_seda.attachNewNode(trazo.create())
        self.abanico_seda.hide()

    # ---------------------------------------------------- daños en el cuerpo
    def _construir_indicadores_dano(self) -> None:
        """Anillos y mangas anatómicas translúcidas de estrés/trauma sobre el modelo."""
        # 1. Daño cervical (cuello): manga translúcida sobre vértebras cervicales + dos anillos
        self.dano_cuello = self.craneo.attachNewNode("dano_cuello")
        self.dano_cuello.setPos(0.038, 0.0, -0.014)
        sec_manga_cuello = [
            {"pos": -0.040, "c2": -0.004, "r1": 0.056, "r2": 0.054},
            {"pos": 0.005, "c2": 0.0, "r1": 0.052, "r2": 0.051},
            {"pos": 0.048, "c2": 0.003, "r1": 0.055, "r2": 0.055},
        ]
        adjuntar_geom(
            self.dano_cuello,
            malla_loft_eje("manga_cuello_dano", sec_manga_cuello, n_lados=20, color=(1.0, 0.18, 0.16, 0.52),
                           cerrar_inicio=False, cerrar_fin=False),
            self.mat_dano,
            transparente=True,
        )
        adjuntar_geom(
            self.dano_cuello,
            malla_toroide("anillo_cuello_1", 0.072, 0.011, eje="x", color=ROJO_DANO, n_u=28, n_v=10),
            self.mat_dano,
            transparente=True,
        )
        anillo2 = adjuntar_geom(
            self.dano_cuello,
            malla_toroide("anillo_cuello_2", 0.092, 0.007, eje="x", color=AMBAR_DANO, n_u=28, n_v=8),
            self.mat_dano,
            transparente=True,
        )
        anillo2.setX(0.022)
        self.dano_cuello.hide()

        # 2. Daño lumbar / cintura (frenado en el agarre de seda)
        self.dano_lumbar = self.torso.attachNewNode("dano_lumbar")
        self.dano_lumbar.setPos(-0.07, 0.0, -0.072)
        adjuntar_geom(
            self.dano_lumbar,
            malla_toroide("anillo_lumbar", 0.165, 0.011, eje="x", color=AMBAR_DANO, n_u=32, n_v=10),
            self.mat_dano,
            transparente=True,
        )
        self.dano_lumbar.setScale(1.0, 1.05, 0.65)
        self.dano_lumbar.hide()

        # 3. Trauma craneal occipital (exclusivo de impacto de cabeza contra el piso)
        self.dano_craneo = self.craneo.attachNewNode("dano_craneo")
        self.dano_craneo.setPos(0.185, 0.0, -0.056)
        adjuntar_geom(
            self.dano_craneo,
            malla_elipsoide("halo_craneo", 0.110, 0.096, 0.064, (1.0, 0.16, 0.14, 0.56), n_lon=20, n_lat=10),
            self.mat_dano,
            transparente=True,
        )
        anillo_cr = adjuntar_geom(
            self.dano_craneo,
            malla_toroide("anillo_craneo", 0.118, 0.012, eje="z", color=ROJO_DANO, n_u=28, n_v=10),
            self.mat_dano,
            transparente=True,
        )
        anillo_cr.setZ(-0.032)
        self.dano_craneo.hide()

        # 4. Trauma en tren inferior: rodillas, tibias y tobillos (exclusivo de impacto de piernas)
        self.dano_rodillas: list[NodePath] = []
        self.dano_tobillos: list[NodePath] = []
        for idx, (rodilla, tobillo) in enumerate(zip(self.rodillas, self.tobillos, strict=True)):
            dr = rodilla.attachNewNode(f"dano_rodilla_{idx}")
            adjuntar_geom(
                dr,
                malla_elipsoide(f"manga_rodilla_{idx}", 0.065, 0.058, 0.060, (1.0, 0.20, 0.16, 0.48), 16, 10),
                self.mat_dano,
                transparente=True,
            )
            adjuntar_geom(
                dr,
                malla_toroide(f"anillo_rodilla_{idx}", 0.076, 0.011, eje="x", color=ROJO_DANO, n_u=24, n_v=8),
                self.mat_dano,
                transparente=True,
            )
            dr.hide()
            self.dano_rodillas.append(dr)

            dt = tobillo.attachNewNode(f"dano_tobillo_{idx}")
            adjuntar_geom(
                dt,
                malla_elipsoide(f"manga_tobillo_{idx}", 0.072, 0.056, 0.072, (1.0, 0.16, 0.14, 0.54), 16, 10),
                self.mat_dano,
                transparente=True,
            )
            adjuntar_geom(
                dt,
                malla_toroide(f"anillo_tobillo_{idx}", 0.074, 0.012, eje="x", color=ROJO_DANO, n_u=24, n_v=8),
                self.mat_dano,
                transparente=True,
            )
            dt.hide()
            self.dano_tobillos.append(dt)

    # ------------------------------------------------------ daños en el piso
    def _construir_dano_piso(self) -> None:
        """Grietas radiales, ondas expansivas y astillas sobre ``self.piso``."""
        self.dano_piso = self.piso.attachNewNode("dano_piso")
        self.grieta_piso = adjuntar_geom(
            self.dano_piso,
            malla_grietas_piso("grietas_impacto", radio=0.62, n_rayos=10),
            self.mat_tela,
            transparente=True,
        )
        self.ondas_piso: list[NodePath] = []
        for idx, color in enumerate((ROJO_DANO, AMBAR_DANO)):
            onda = adjuntar_geom(
                self.dano_piso,
                malla_toroide(f"onda_piso_{idx}", 0.30, 0.016, eje="z", color=color, n_u=36, n_v=8),
                self.mat_onda,
                transparente=True,
            )
            onda.setZ(0.012)
            self.ondas_piso.append(onda)

        # Astillas / fragmentos discretos de madera que saltan al chocar
        self.astillas: list[tuple[NodePath, float, float, float]] = []
        angulos = np.linspace(0.2, 2.0 * pi - 0.15, 10)
        for i, ang in enumerate(angulos):
            vel_r = 0.75 + 0.55 * ((i * 5) % 7) / 6.0
            vel_z = 1.15 + 0.65 * ((i * 3) % 5) / 4.0
            ast = adjuntar_geom(
                self.dano_piso,
                malla_elipsoide(
                    f"astilla_{i}",
                    0.036 + 0.012 * (i % 3),
                    0.012,
                    0.008,
                    (0.28 + 0.05 * (i % 2), 0.21, 0.17, 1.0),
                    n_lon=10,
                    n_lat=6,
                ),
                self.mat_tela,
            )
            self.astillas.append((ast, float(ang), vel_r, vel_z))

        self.dano_piso.hide()

    # ------------------------------------------------------------ animación
    def actualizar(
        self,
        *,
        t: float,
        tau: float,
        altura: float,
        v_m_s: float,
        a_g: float,
        angulo_cabeza_rad: float,
        omega_cabeza_rad_s: float,
        angulo_piernas_rad: float,
        m_cuello_nm: float,
        m_cadera_nm: float,
        contacto,
        en_fin: bool,
        t_dano: float,
        piso_m: float,
        tablas_piso: list[NodePath] | None = None,
    ) -> None:
        """Actualiza pose, articulaciones secundarias y daños sin tocar la física."""
        frenado = tau >= 0.0
        self.raiz.setZ(altura)

        # 1. Orientación del tronco (idéntica a la caída dorsal original)
        inclinacion(self.raiz, -36.0 * float(np.clip(-tau / 1.3, 0.0, 1.0)))

        # 2. Abanico de seda solo visible al producirse el agarre en el abdomen
        if frenado:
            self.abanico_seda.show()
            tension_escala = float(np.clip(0.35 + tau / 0.006, 0.35, 1.0))
            self.abanico_seda.setScale(1.0, 1.0, tension_escala)
        else:
            self.abanico_seda.hide()

        # Progreso suave del desenlace post-evento (0 en caída/frenado, 0..1 en daño final)
        u = float(np.clip(t_dano / 0.55, 0.0, 1.0)) if en_fin else 0.0
        u_suave = u * u * (3.0 - 2.0 * u)
        choque_cabeza = bool(en_fin and contacto is not None and contacto.segmento == "Cabeza")
        choque_piernas = bool(en_fin and contacto is not None and contacto.segmento == "Piernas")
        latigazo_aire = bool(en_fin and contacto is None)

        # 3. Cabeza y cuello (exactamente acoplados a mediciones.py hasta self.fin)
        giro_cab_deg = degrees(angulo_cabeza_rad)
        roll_cab = 0.0
        yaw_cab = 0.0
        compresion_z = 1.0
        desp_cab_z = 0.0

        if not frenado:
            # Respiración / leve balanceo aerodinámico durante la caída
            giro_cab_deg += 3.0 * sin(3.6 * t)
            yaw_cab = 4.0 * sin(2.1 * t)
        elif choque_cabeza and u > 0.0:
            # Impacto craneal contra z = piso_m: compresión breve + rebote corto + colapso lateral
            # sin atravesar nunca el piso.
            pulso_imp = sin(min(pi, u * pi * 2.2)) * np.exp(-3.8 * u)
            rebote_deg = -11.0 * sin(min(pi, u * pi * 1.8)) * np.exp(-2.8 * u)
            giro_cab_deg = giro_cab_deg + rebote_deg
            compresion_z = 1.0 - 0.08 * pulso_imp
            desp_cab_z = 0.015 * pulso_imp
            roll_cab = 18.0 * u_suave
            yaw_cab = -14.0 * u_suave
        elif latigazo_aire and u > 0.0:
            # Pérdida súbita de tono cervical suspendida en el aire: cae inerte hacia atrás y de lado
            osc = sin(2.0 * pi * 1.9 * t_dano) * np.exp(-3.4 * t_dano)
            giro_cab_deg = giro_cab_deg + 8.0 * u_suave + 5.5 * osc
            roll_cab = 16.0 * u_suave + 4.0 * osc
            yaw_cab = 10.0 * u_suave
        elif choque_piernas and u > 0.0:
            # Sacudida secundaria al absorber el impacto del tren inferior
            sacudida = sin(2.0 * pi * 3.0 * t_dano) * np.exp(-4.2 * t_dano)
            giro_cab_deg = giro_cab_deg + 7.0 * u_suave + 6.0 * sacudida
            roll_cab = -9.0 * u_suave

        inclinacion(self.cabeza, giro_cab_deg)
        self.craneo.setHpr(yaw_cab, 0.0, roll_cab)
        self.craneo.setScale(1.0, 1.0, compresion_z)
        self.craneo.setZ(desp_cab_z)

        # Garantizar no-penetración del cráneo y del cabello base contra el piso
        if frenado and piso_m > 0.0:
            z_min_cab = min(
                self.malla_rostro.getTightBounds(self.render)[0].z,
                self.malla_cabello_base.getTightBounds(self.render)[0].z,
            )
            if z_min_cab < piso_m:
                deficit = piso_m - z_min_cab
                giro_cab_deg -= degrees(np.arcsin(float(np.clip(deficit / 0.20, 0.0, 0.92))))
                inclinacion(self.cabeza, giro_cab_deg)
                z_min_cab2 = min(
                    self.malla_rostro.getTightBounds(self.render)[0].z,
                    self.malla_cabello_base.getTightBounds(self.render)[0].z,
                )
                if z_min_cab2 < piso_m:
                    self.craneo.setZ(desp_cab_z + (piso_m - z_min_cab2))

        # 4. Melena articulada en 3 tramos respetando el plano del piso (sin atravesar tablas)
        v_norm = float(np.clip(abs(v_m_s) / 25.0, 0.0, 1.0))
        if not frenado:
            # Aire ascendente (+Z): melena ondeando detrás de los hombros hacia atrás/arriba
            ang_mundo_0 = 16.0 + 18.0 * v_norm + 6.0 * v_norm * sin(9.5 * t)
            inclinacion(self.melena_tramos[0], ang_mundo_0 - giro_cab_deg)
            inclinacion(self.melena_tramos[1], 8.0 * v_norm + 8.0 * v_norm * sin(9.5 * t - 1.3))
            inclinacion(self.melena_tramos[2], 6.0 * v_norm + 10.0 * v_norm * sin(9.5 * t - 2.6))
        else:
            if choque_cabeza:
                deseados = (-3.0 * (1.0 - u_suave), -2.0 * u_suave, -1.0 * u_suave)
            else:
                latigazo = float(np.clip(omega_cabeza_rad_s * 0.9, -15.0, 28.0))
                base_0 = float(np.clip(-28.0 - 0.8 * latigazo - 44.0 * u_suave, -82.0, -14.0))
                deseados = (base_0, max(-85.0, base_0 - 10.0 - 10.0 * u_suave), max(-88.0, base_0 - 18.0 - 16.0 * u_suave))

            # Resolver cada tramo secuencialmente para que, al tocar el piso, se tienda sobre la madera
            largos_m = (0.145, 0.140, 0.125)
            z_actual = self.melena_tramos[0].getPos(self.render).z
            ang_padre = giro_cab_deg
            for idx, (tramo, largo_m, ang_des) in enumerate(
                zip(self.melena_tramos, largos_m, deseados, strict=True)
            ):
                margen = 0.068 - 0.004 * idx
                dz_disp = max(0.0, z_actual - (piso_m + margen))
                ang_min = -degrees(np.arcsin(float(np.clip(dz_disp / largo_m, 0.0, 1.0))))
                ang_mundo = max(ang_des, ang_min)
                inclinacion(tramo, ang_mundo - ang_padre)
                z_actual += largo_m * sin(radians(ang_mundo))
                ang_padre = ang_mundo

        # 5. Faldones del abrigo acompañando la inclinación de los muslos
        giro_piernas_deg = degrees(angulo_piernas_rad)
        for idx, faldon in enumerate(self.faldones):
            signo = -1.0 if idx == 0 else 1.0
            if not frenado:
                ang_f = 14.0 * v_norm + 5.0 * v_norm * sin(8.0 * t + idx)
                faldon.setHpr(signo * 4.0, signo * ang_f, 0.0)
            else:
                carga = float(np.clip(a_g / 150.0, 0.0, 1.15))
                acompana = -0.58 * giro_piernas_deg if not choque_piernas else -0.25 * giro_piernas_deg * (1.0 - u_suave)
                inclinacion(faldon, acompana)
                faldon.setP(-signo * (6.0 * carga + 6.0 * u_suave))

        # 6. Brazos y codos (naturales, ligeramente flexionados y respetando siempre z >= piso_m)
        espacio_brazo = max(0.03, altura - 0.062 - piso_m - 0.045)
        # Alcance real hombro -> punta de dedos = 0.26 + 0.235 + 0.135 = 0.63 m
        max_bajada_hombro = degrees(np.arcsin(float(np.clip(espacio_brazo / 0.64, 0.05, 0.96))))
        for idx, (hombro, codo, signo) in enumerate(
            ((self.hombro_der, self.codos[0], -1.0), (self.hombro_izq, self.codos[1], 1.0))
        ):
            desfase = 0.7 * idx
            asim = 1.0 if idx == 0 else 0.86
            if not frenado:
                # Caída dorsal: brazos abiertos y elevados con codos suaves por la corriente de aire
                pitch = signo * (22.0 + 18.0 * v_norm + 7.0 * sin(4.8 * t + desfase))
                heading = signo * (14.0 + 6.0 * cos(3.7 * t + desfase))
                codo_p = signo * (22.0 + 8.0 * sin(5.2 * t + desfase))
                codo_h = signo * 20.0
            else:
                carga = float(np.clip((a_g + 1.0) / 140.0, 0.0, 1.20))
                if choque_cabeza and u > 0.0:
                    # Brazos caen y reposan abiertos sobre el piso (z >= piso_m)
                    bajada = min(max_bajada_hombro, 28.0 + 16.0 * u_suave)
                    pitch = -signo * bajada
                    heading = signo * (12.0 - 28.0 * u_suave * asim)
                    codo_p = signo * (0.72 * bajada * u_suave)
                    codo_h = signo * (22.0 + 14.0 * u_suave)
                elif latigazo_aire and u > 0.0:
                    # Brazos inertes suspendidos en el aire, con codos relajados (no rígidos a 90°)
                    osc = sin(2.0 * pi * 1.6 * t_dano + desfase) * np.exp(-3.0 * t_dano)
                    bajada = min(max_bajada_hombro, 34.0 * carga + (26.0 * asim) * u_suave + 6.0 * osc)
                    pitch = -signo * bajada
                    heading = -signo * (12.0 + 18.0 * u_suave * asim)
                    codo_p = signo * (14.0 * u_suave - 8.0 * carga)
                    codo_h = signo * (18.0 + 14.0 * u_suave)
                elif choque_piernas and u > 0.0:
                    # Sacudida y apoyo/caída controlada sin atravesar el piso (+0.85 m)
                    sac = sin(2.0 * pi * 2.8 * t_dano + desfase) * np.exp(-3.8 * t_dano)
                    bajada = min(max_bajada_hombro, 30.0 * carga + 16.0 * u_suave + 7.0 * sac)
                    pitch = -signo * bajada
                    heading = -signo * (10.0 + 16.0 * u_suave)
                    codo_p = signo * (0.65 * bajada * u_suave)
                    codo_h = signo * (24.0 + 10.0 * u_suave)
                else:
                    # Frenado activo: inercia arrastra brazos hacia abajo respetando el piso
                    bajada = min(max_bajada_hombro, 34.0 * carga)
                    pitch = -signo * bajada
                    heading = -signo * (8.0 + 14.0 * carga)
                    holgura_codo = max(0.0, max_bajada_hombro - bajada)
                    codo_p = -signo * min(12.0 * carga, holgura_codo) if holgura_codo > 2.0 else signo * (0.40 * bajada)
                    codo_h = signo * (22.0 - 6.0 * carga)

            hombro.setHpr(heading, pitch, 0.0)
            codo.setHpr(codo_h, codo_p, 0.0)

        # 7. Piernas, rodillas y tobillos (acoplados a mediciones.py + cinemática de daño)
        inclinacion(self.piernas, -giro_piernas_deg)

        for idx, (muslo, rodilla, tobillo, signo) in enumerate(
            zip(self.muslos, self.rodillas, self.tobillos, (-1.0, 1.0), strict=True)
        ):
            if not frenado:
                # Ligero movimiento vivo y asimétrico durante la caída libre
                flex_rod = -(8.0 + 7.0 * v_norm * (0.5 + 0.5 * sin(4.4 * t + 1.4 * idx)))
                muslo.setHpr(0.0, 0.0, 0.0)
                inclinacion(muslo, 0.0)
                inclinacion(rodilla, flex_rod)
                inclinacion(tobillo, 12.0 + 5.0 * sin(4.4 * t + idx))
            elif choque_piernas and u > 0.0:
                # Colapso realista del tren inferior contra el piso (z = piso_m) sin penetrarlo:
                # Las rodillas se doblan hacia arriba (+Z, flexión anatómica humana) y los
                # talones/botas permanecen apoyados sobre el plano del piso.
                asimetria = 1.0 if idx == 0 else 1.20
                rebote = sin(2.0 * pi * 2.6 * t_dano) * np.exp(-4.5 * t_dano)
                # Rótula sube conforme las botas se frenan contra el piso
                eleva_muslo_deg = (34.0 * asimetria + 5.0 * rebote) * u_suave
                # Ángulo total del muslo respecto a la horizontal (positivo = apunta hacia arriba +Z)
                ang_muslo_mundo = radians(eleva_muslo_deg - giro_piernas_deg)
                z_rodilla = altura - 0.048 + 0.39 * sin(ang_muslo_mundo)
                # Resolver ángulo de pantorrilla para mantener el talón apoyado sobre piso_m
                seno_panto = float(np.clip((z_rodilla - (piso_m + 0.082)) / 0.40, -0.96, 0.96))
                ang_panto_mundo = -np.arcsin(seno_panto)  # negativo = baja hacia el piso
                ang_rodilla_local_deg = degrees(ang_panto_mundo - ang_muslo_mundo)
                # Limitar a flexión anatómica humana (nunca hiperextensión hacia delante)
                ang_rodilla_local_deg = float(np.clip(ang_rodilla_local_deg, -108.0, -4.0))
                ang_tobillo_local_deg = float(np.clip(-degrees(ang_panto_mundo) - 6.0, -25.0, 55.0))

                inclinacion(muslo, eleva_muslo_deg)
                muslo.setH(signo * 7.5 * u_suave)
                inclinacion(rodilla, ang_rodilla_local_deg)
                inclinacion(tobillo, ang_tobillo_local_deg)
            elif latigazo_aire and u > 0.0:
                # Suspendida en el aire: rodillas ceden por gravedad (colgando sobre el suelo)
                osc = sin(2.0 * pi * 1.5 * t_dano + 0.5 * idx) * np.exp(-2.8 * t_dano)
                flex_rod = -(22.0 + 6.0 * idx) * u_suave - 4.0 * osc
                inclinacion(muslo, 4.0 * u_suave)
                muslo.setH(signo * 2.5 * u_suave)
                inclinacion(rodilla, flex_rod)
                inclinacion(tobillo, 18.0 * u_suave)
            elif choque_cabeza and u > 0.0:
                # Al golpear la cabeza, las piernas elevadas ceden ligeramente por gravedad
                inclinacion(muslo, -8.0 * u_suave)
                muslo.setH(signo * 2.0 * u_suave)
                inclinacion(rodilla, -16.0 * u_suave)
                inclinacion(tobillo, 10.0 * u_suave)
            else:
                # Durante el frenado antes del fin: piernas casi alineadas con el segmento físico
                inclinacion(muslo, 0.0)
                muslo.setH(0.0)
                inclinacion(rodilla, 0.0)
                inclinacion(tobillo, 6.0)

        # 8. Indicadores de daño anatómico sobre el modelo del personaje y el piso
        self._actualizar_danos(
            frenado=frenado,
            m_cuello_nm=m_cuello_nm,
            m_cadera_nm=m_cadera_nm,
            contacto=contacto,
            en_fin=en_fin,
            t_dano=t_dano,
            u=u,
            angulo_cabeza_rad=angulo_cabeza_rad,
            angulo_piernas_rad=angulo_piernas_rad,
            tablas_piso=tablas_piso,
        )

    def _actualizar_danos(
        self,
        *,
        frenado: bool,
        m_cuello_nm: float,
        m_cadera_nm: float,
        contacto,
        en_fin: bool,
        t_dano: float,
        u: float,
        angulo_cabeza_rad: float,
        angulo_piernas_rad: float,
        tablas_piso: list[NodePath] | None,
    ) -> None:
        pulso = 0.5 + 0.5 * sin(2.0 * pi * 3.8 * t_dano) if en_fin else 1.0

        # Daño cervical (cuello): activo al superar el umbral de tolerancia (90 Nm)
        intensidad_cuello = float(np.clip((m_cuello_nm - UMBRAL_CUELLO_LIMITE_NM) / 1100.0, 0.0, 1.0)) if frenado else 0.0
        if intensidad_cuello > 0.05:
            self.dano_cuello.show()
            escala_c = 0.92 + 0.24 * intensidad_cuello + (0.10 * pulso if en_fin else 0.0)
            self.dano_cuello.setScale(escala_c)
            alpha_c = float(np.clip(0.28 + 0.62 * intensidad_cuello, 0.0, 0.92))
            self.dano_cuello.setColorScale(1.0, 0.28 - 0.16 * intensidad_cuello, 0.22, alpha_c)
        else:
            self.dano_cuello.hide()

        # Daño lumbar / cintura
        intensidad_cadera = float(np.clip((m_cadera_nm - 1200.0) / 10000.0, 0.0, 1.0)) if frenado else 0.0
        if intensidad_cadera > 0.08:
            self.dano_lumbar.show()
            esc_l = 0.95 + 0.14 * intensidad_cadera + (0.06 * pulso if en_fin else 0.0)
            self.dano_lumbar.setScale(esc_l, 1.05 * esc_l, 0.68 * esc_l)
            self.dano_lumbar.setColorScale(1.0, 0.55 - 0.25 * intensidad_cadera, 0.22, 0.25 + 0.52 * intensidad_cadera)
        else:
            self.dano_lumbar.hide()

        # Daño específico de contacto craneal
        if en_fin and contacto is not None and contacto.segmento == "Cabeza":
            self.dano_craneo.show()
            esc_cr = 0.96 + 0.16 * (0.4 + 0.6 * pulso)
            self.dano_craneo.setScale(esc_cr)
            self.dano_craneo.setColorScale(1.0, 0.18, 0.15, 0.72 + 0.20 * pulso)
        else:
            self.dano_craneo.hide()

        # Daño específico de contacto de piernas (rodillas + tobillos)
        if en_fin and contacto is not None and contacto.segmento == "Piernas":
            esc_p = 0.96 + 0.22 * (0.4 + 0.6 * pulso)
            for dr, dt in zip(self.dano_rodillas, self.dano_tobillos, strict=True):
                dr.show()
                dt.show()
                dr.setScale(esc_p)
                dt.setScale(esc_p * 1.1)
                dr.setColorScale(1.0, 0.25, 0.18, 0.72 + 0.20 * pulso)
                dt.setColorScale(1.0, 0.16, 0.14, 0.80 + 0.15 * pulso)
        else:
            for dr, dt in zip(self.dano_rodillas, self.dano_tobillos, strict=True):
                dr.hide()
                dt.hide()

        # Daño sobre el modelo del piso (solo si hubo contacto)
        if en_fin and contacto is not None:
            self.dano_piso.show()
            es_piernas = contacto.segmento == "Piernas"
            if es_piernas:
                x_imp = -PIVOTE_CADERA_M - BRAZO_CONTACTO_PIERNAS_M * cos(angulo_piernas_rad)
                escala_energia = 1.25  # 4841 J
            else:
                x_imp = PIVOTE_CUELLO_M + BRAZO_CONTACTO_CABEZA_M * cos(angulo_cabeza_rad)
                escala_energia = 0.74  # 934 J
            self.dano_piso.setPos(x_imp, 0.0, 0.0)

            # Grieta crece rápidamente en los primeros 120 ms tras el golpe
            progreso_grieta = float(np.clip(0.35 + 0.65 * (u / 0.22), 0.35, 1.0)) if u > 0 else 0.75
            self.grieta_piso.setScale(escala_energia * progreso_grieta)
            self.grieta_piso.setColorScale(1.0, 1.0, 1.0, 0.94)

            # Ondas concéntricas expansivas sobre el piso
            for idx, onda in enumerate(self.ondas_piso):
                fase_onda = (u * 1.35 + 0.22 * idx) % 1.0 if u > 0 else (0.28 + 0.24 * idx)
                radio_esc = escala_energia * (0.45 + 2.4 * fase_onda)
                alpha_o = max(0.0, 0.88 * (1.0 - fase_onda))
                onda.setScale(radio_esc, radio_esc, 1.0)
                onda.setColorScale(1.0, 0.28 + 0.25 * idx, 0.18, alpha_o)

            # Astillas de madera con trayectoria parabólica sobre las tablas
            t_ast = max(0.04, t_dano)
            for ast, ang, vr, vz in self.astillas:
                r_dist = escala_energia * vr * t_ast * 0.55
                z_ast = max(0.008, vz * escala_energia * t_ast - 4.9 * t_ast * t_ast)
                ast.setPos(r_dist * cos(ang), r_dist * sin(ang), z_ast)
                ast.setHpr(degrees(ang) + 260.0 * t_ast, 180.0 * t_ast, 90.0 * t_ast)
                ast.setScale(escala_energia * 0.85)

            # Ligera vibración/hundimiento de las tablas golpeadas del piso
            if tablas_piso:
                sacudida_tabla = -0.028 * escala_energia * np.exp(-7.0 * t_dano) * cos(28.0 * t_dano)
                for idx, tabla in enumerate(tablas_piso):
                    # Las tablas centrales (índices 3 y 4) están bajo y = 0
                    peso = 1.0 if idx in (3, 4) else (0.35 if idx in (2, 5) else 0.0)
                    tabla.setZ(-0.17 + peso * sacudida_tabla)
        else:
            self.dano_piso.hide()
            if tablas_piso:
                for tabla in tablas_piso:
                    tabla.setZ(-0.17)
