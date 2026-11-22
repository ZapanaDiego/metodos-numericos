"""Maniquí low-poly articulado para la escena 3D.

El cuerpo se construye una sola vez como un conjunto de mallas (cápsulas y
elipsoides). En cada frame solo se recalculan los vértices; no se crean
artistas nuevos.

Convención: ``z`` es la altura sobre el suelo. El origen del cuerpo está en la
pelvis, ``altura_torso`` es la cintura (punto de anclaje de la seda) y el torso
se dibuja por encima.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from matplotlib.colors import to_rgb
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from .estilo import CUERPO


def _rot_x(v, angulo: float):
    c, s = np.cos(angulo), np.sin(angulo)
    return np.array([v[0], c * v[1] - s * v[2], s * v[1] + c * v[2]])


def _base_perpendicular(axis: np.ndarray) -> np.ndarray:
    aux = np.array([0.0, 0.0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    return aux


class MallaCapsula:
    """Cápsula/cono truncado orientado entre dos puntos con sombreado vectorizado."""

    def __init__(self, ax, color: str, n_lados: int = 8, alpha: float = 1.0, luz=(0.35, -0.55, 0.75)):
        self.ax = ax
        self.n = n_lados
        self.color = np.array(to_rgb(color))
        self.alpha = float(alpha)
        self.luz = np.asarray(luz, dtype=float) / np.linalg.norm(luz)
        self.collection = Poly3DCollection(
            [],
            facecolor=color,
            edgecolor=(1.0, 1.0, 1.0, 0.09),
            linewidths=0.16,
            alpha=alpha,
        )
        self.collection.set_zsort("average")
        ax.add_collection3d(self.collection)

        angulos = np.linspace(0, 2 * np.pi, self.n, endpoint=False)
        self._circulo = np.column_stack([np.cos(angulos), np.sin(angulos)])
        self._anillos = np.array([0.0, 0.35, 0.7, 1.0])
        quad_indices = []
        for k in range(len(self._anillos) - 1):
            for i in range(self.n):
                j = (i + 1) % self.n
                quad_indices.append([k * self.n + i, k * self.n + j, (k + 1) * self.n + j, (k + 1) * self.n + i])
        self._quad_indices = np.array(quad_indices)
        self._cap_col = np.array([list(self.color) + [self.alpha], list(self.color) + [self.alpha]])

    def actualizar(self, p0, p1, r0: float, r1: float):
        p0 = np.asarray(p0, dtype=float)
        p1 = np.asarray(p1, dtype=float)
        eje = p1 - p0
        largo = float(np.linalg.norm(eje))
        if largo < 1e-9:
            self.collection.set_verts([[p0, p0 + [1e-4, 0, 0], p0 + [0, 1e-4, 0]]])
            return
        u = eje / largo
        v = np.cross(u, _base_perpendicular(u))
        v_norm = np.linalg.norm(v)
        if v_norm < 1e-9:
            v = np.cross(u, np.array([1.0, 0.0, 0.0]))
            v_norm = np.linalg.norm(v)
        v /= v_norm
        w = np.cross(u, v)

        radios = r0 + self._anillos * (r1 - r0)
        centros = p0[None, :] + self._anillos[:, None] * eje[None, :]
        radial = self._circulo[:, 0, None] * v[None, :] + self._circulo[:, 1, None] * w[None, :]
        verts = centros[:, None, :] + radios[:, None, None] * radial[None, :, :]
        all_verts = verts.reshape(-1, 3)

        quads = all_verts[self._quad_indices]
        v1 = quads[:, 1] - quads[:, 0]
        v2 = quads[:, 3] - quads[:, 0]
        normals = np.cross(v1, v2)
        normas = np.linalg.norm(normals, axis=1, keepdims=True)
        normals /= np.maximum(normas, 1e-12)
        intensidades = 0.58 + 0.42 * np.abs(np.dot(normals, self.luz))
        colores_quads = np.column_stack([
            np.clip(self.color[None, :] * intensidades[:, None], 0, 1),
            np.full(len(intensidades), self.alpha),
        ])

        cap0 = np.vstack([p0, all_verts[:self.n][::-1]])
        cap1 = np.vstack([p1, all_verts[-self.n:]])
        caras = list(quads) + [cap0, cap1]
        colores = np.vstack([colores_quads, self._cap_col])
        self.collection.set_verts(caras)
        self.collection.set_facecolors(colores)


class MallaElipsoide:
    """Elipsoide de resolución media para cabeza, pelo y manos."""

    def __init__(self, ax, color: str, n_meridianos: int = 12, n_paralelos: int = 7, alpha: float = 1.0, phi_max: float = np.pi):
        self.ax = ax
        self.color = np.array(to_rgb(color))
        self.alpha = float(alpha)
        self.n_mer = n_meridianos
        self.n_par = n_paralelos
        self.phi_max = phi_max
        theta = np.linspace(0, 2 * np.pi, n_meridianos, endpoint=False)
        phi = np.linspace(0.0, phi_max, n_paralelos + 1)
        unit = []
        for p in phi:
            unit.append(np.column_stack([np.sin(p) * np.cos(theta), np.sin(p) * np.sin(theta), np.full_like(theta, np.cos(p))]))
        self._unit_stacked = np.concatenate(unit, axis=0)

        quad_indices = []
        for k in range(n_paralelos):
            for i in range(n_meridianos):
                j = (i + 1) % n_meridianos
                quad_indices.append([k * n_meridianos + i, k * n_meridianos + j, (k + 1) * n_meridianos + j, (k + 1) * n_meridianos + i])
        self._quad_indices = np.array(quad_indices)
        self._facecolor = self.color.tolist() + [self.alpha]

        self.collection = Poly3DCollection(
            [],
            facecolor=color,
            edgecolor=(1.0, 1.0, 1.0, 0.09),
            linewidths=0.16,
            alpha=alpha,
        )
        self.collection.set_zsort("average")
        ax.add_collection3d(self.collection)

    def actualizar(self, centro, radios):
        centro = np.asarray(centro, dtype=float)
        radios = np.asarray(radios, dtype=float)
        all_verts = self._unit_stacked * radios[None, :] + centro[None, :]
        caras = all_verts[self._quad_indices]
        self.collection.set_verts(caras)
        self.collection.set_facecolors(self._facecolor)


class CuerpoHumano:
    """Cuerpo articulado de 15+ partes, actualizado por pose."""

    def __init__(self, ax, t_tensado_s: float = 0.0):
        self.ax = ax
        self.t_tensado = float(t_tensado_s)
        self.partes = {
            "cabeza": MallaElipsoide(ax, CUERPO["piel"], 12, 7),
            "pelo": MallaElipsoide(ax, CUERPO["pelo"], 12, 7, phi_max=0.58 * np.pi),
            "cuello": MallaCapsula(ax, CUERPO["piel"], 8),
            "torax": MallaCapsula(ax, CUERPO["abrigo"], 10),
            "abdomen": MallaCapsula(ax, CUERPO["abrigo"], 10),
            "pelvis": MallaCapsula(ax, CUERPO["pantalon"], 8),
            "abrigo_cola": MallaCapsula(ax, CUERPO["abrigo_sombra"], 8, alpha=0.85),
            "brazo_izq": MallaCapsula(ax, CUERPO["abrigo"], 8),
            "brazo_der": MallaCapsula(ax, CUERPO["abrigo"], 8),
            "antebrazo_izq": MallaCapsula(ax, CUERPO["piel"], 7),
            "antebrazo_der": MallaCapsula(ax, CUERPO["piel"], 7),
            "mano_izq": MallaElipsoide(ax, CUERPO["piel"], 8, 5),
            "mano_der": MallaElipsoide(ax, CUERPO["piel"], 8, 5),
            "muslo_izq": MallaCapsula(ax, CUERPO["pantalon"], 8),
            "muslo_der": MallaCapsula(ax, CUERPO["pantalon"], 8),
            "pantorrilla_izq": MallaCapsula(ax, CUERPO["pantalon"], 7),
            "pantorrilla_der": MallaCapsula(ax, CUERPO["pantalon"], 7),
            "pie_izq": MallaCapsula(ax, CUERPO["zapato"], 6),
            "pie_der": MallaCapsula(ax, CUERPO["zapato"], 6),
            "coleta": MallaCapsula(ax, CUERPO["pelo"], 6),
        }
        (self.ojo_izq,) = ax.plot([0], [0], [0], "o", color="#1b1b1b", ms=2.2)
        (self.ojo_der,) = ax.plot([0], [0], [0], "o", color="#1b1b1b", ms=2.2)

    # --------------------------------------------------------------- pose
    def esqueleto(self, estado: dict) -> dict:
        h = float(estado.get("altura_torso", 1.2))
        a_g = float(estado.get("a_g", 1.0))
        fase = int(estado.get("fase", 0))
        t = float(estado.get("t", 0.0))
        v = float(estado.get("v", 0.0))
        w = float(np.clip((a_g - 1.0) / 120.0, 0.0, 1.4))

        if fase == 1:
            osc = 0.0
            if t >= self.t_tensado:
                tau = t - self.t_tensado
                osc = float(np.sin(2 * np.pi * tau / 0.07) * np.exp(-tau / 0.055))
            cuello = -0.55 * w + 0.28 * osc
            hombro = 1.05 * w + 0.22 * osc
            cadera = -0.32 * w - 0.18 * osc
            rodilla = 0.55 * w + 0.20 * osc
        else:
            v_norm = float(np.clip(v / 25.0, 0.0, 1.0))
            cuello = 0.03 * v_norm * np.sin(2 * np.pi * t * 3.2)
            hombro = 0.08 * v_norm * np.sin(2 * np.pi * t * 4.0)
            cadera = 0.04 * v_norm * np.cos(2 * np.pi * t * 3.0)
            rodilla = 0.06 * v_norm * np.sin(2 * np.pi * t * 3.5)

        origen = np.array([0.0, 0.0, h - 0.34])
        pelvis = origen
        abdomen = origen + np.array([0.0, 0.0, 0.18])
        pecho = origen + np.array([0.0, 0.0, 0.42])
        base_cuello = origen + np.array([0.0, 0.0, 0.60])
        cabeza = base_cuello + np.array([0.0, 0.0, 0.18])
        # cuello: la cabeza bascula sobre la base
        cabeza = base_cuello + _rot_x(np.array([0.0, 0.0, 0.18]), cuello)

        j = {
            "origen": origen,
            "pelvis": pelvis,
            "abdomen": abdomen,
            "pecho": pecho,
            "base_cuello": base_cuello,
            "cabeza": cabeza,
        }
        for lado, signo in (("der", 1.0), ("izq", -1.0)):
            hombro_p = pecho + np.array([0.24 * signo, 0.0, 0.02])
            codo_off = _rot_x(np.array([0.035 * signo, 0.0, -0.28]), hombro)
            muneca_off = _rot_x(np.array([0.015 * signo, 0.0, -0.24]), hombro * 0.92)
            codo = hombro_p + codo_off
            muneca = codo + muneca_off
            mano = muneca + _rot_x(np.array([0.0, 0.0, -0.055]), hombro)
            j[f"hombro_{lado}"] = hombro_p
            j[f"codo_{lado}"] = codo
            j[f"muneca_{lado}"] = muneca
            j[f"mano_{lado}"] = mano

            cadera_p = pelvis + np.array([0.11 * signo, 0.0, 0.0])
            rodilla_p = cadera_p + _rot_x(np.array([0.005 * signo, 0.0, -0.42]), cadera)
            tobillo_p = rodilla_p + _rot_x(np.array([0.0, 0.0, -0.38]), cadera + rodilla)
            pie_p = tobillo_p + _rot_x(np.array([0.0, 0.14, -0.04]), cadera + rodilla)
            j[f"cadera_{lado}"] = cadera_p
            j[f"rodilla_{lado}"] = rodilla_p
            j[f"tobillo_{lado}"] = tobillo_p
            j[f"pie_{lado}"] = pie_p
        return j

    # ------------------------------------------------------------ dibujo
    def actualizar(self, estado: dict):
        j = self.esqueleto(estado)
        self.partes["cabeza"].actualizar(j["cabeza"], [0.100, 0.110, 0.128])
        self.partes["pelo"].actualizar(j["cabeza"] + np.array([0.0, -0.01, 0.035]), [0.112, 0.122, 0.118])
        self.partes["cuello"].actualizar(j["base_cuello"], j["cabeza"] - np.array([0.0, 0.0, 0.09]), 0.050, 0.048)
        self.partes["torax"].actualizar(j["abdomen"], j["pecho"], 0.16, 0.195)
        self.partes["abdomen"].actualizar(j["pelvis"], j["abdomen"], 0.155, 0.16)
        self.partes["pelvis"].actualizar(j["pelvis"] - np.array([0.0, 0.0, 0.08]), j["pelvis"] + np.array([0.0, 0.0, 0.10]), 0.145, 0.155)

        v_norm = float(np.clip(float(estado.get("v", 0.0)) / 25.0, 0.0, 1.0))
        fase = int(estado.get("fase", 0))
        t = float(estado.get("t", 0.0))
        if fase == 0:
            dy_coleta = 0.16 + 0.02 * v_norm * np.sin(2 * np.pi * t * 6.0)
            dz_coleta = -0.28 + 0.10 * v_norm + 0.02 * v_norm * np.cos(2 * np.pi * t * 7.0)
            dy_abrigo = 0.18 + 0.02 * v_norm * np.sin(2 * np.pi * t * 5.0)
            dz_abrigo = -0.24 + 0.06 * v_norm + 0.02 * v_norm * np.sin(2 * np.pi * t * 5.5)
        else:
            a_g = float(estado.get("a_g", 1.0))
            w = float(np.clip((a_g - 1.0) / 120.0, 0.0, 1.4))
            tau = max(0.0, t - self.t_tensado)
            osc = float(np.sin(2 * np.pi * tau / 0.07) * np.exp(-tau / 0.055))
            dy_coleta = 0.16 + 0.04 * w - 0.02 * osc
            dz_coleta = -0.28 - 0.05 * w + 0.03 * osc
            dy_abrigo = 0.18 + 0.03 * w
            dz_abrigo = -0.24 - 0.04 * w + 0.02 * osc

        self.partes["abrigo_cola"].actualizar(
            j["pelvis"] + np.array([0.0, 0.13, 0.08]),
            j["pelvis"] + np.array([0.0, dy_abrigo, dz_abrigo]),
            0.10,
            0.07,
        )
        for lado in ("izq", "der"):
            self.partes[f"brazo_{lado}"].actualizar(j[f"hombro_{lado}"], j[f"codo_{lado}"], 0.065, 0.055)
            self.partes[f"antebrazo_{lado}"].actualizar(j[f"codo_{lado}"], j[f"muneca_{lado}"], 0.050, 0.038)
            self.partes[f"mano_{lado}"].actualizar(j[f"mano_{lado}"], [0.055, 0.045, 0.075])
            self.partes[f"muslo_{lado}"].actualizar(j[f"cadera_{lado}"], j[f"rodilla_{lado}"], 0.095, 0.075)
            self.partes[f"pantorrilla_{lado}"].actualizar(j[f"rodilla_{lado}"], j[f"tobillo_{lado}"], 0.070, 0.050)
            self.partes[f"pie_{lado}"].actualizar(j[f"tobillo_{lado}"], j[f"pie_{lado}"], 0.065, 0.045)
        # coleta detrás de la cabeza (y positiva = espalda)
        self.partes["coleta"].actualizar(j["cabeza"] + np.array([0.0, 0.10, 0.02]), j["cabeza"] + np.array([0.0, dy_coleta, dz_coleta]), 0.045, 0.020)
        # ojos en la cara (el frente es y negativo)
        frente = j["cabeza"] + np.array([0.0, -0.098, 0.015])
        self.ojo_izq.set_data_3d([frente[0] - 0.035], [frente[1]], [frente[2] + 0.018])
        self.ojo_der.set_data_3d([frente[0] + 0.035], [frente[1]], [frente[2] + 0.018])

    def punto_cintura(self, estado: dict):
        return np.array([0.18, 0.08, float(estado.get("altura_torso", 1.2))])

    def contar_artistas(self) -> int:
        return len(self.partes) + 2
