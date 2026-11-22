"""Escena 3D oscura de la torre, el cuerpo articulado y la telaraña."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from .cuerpo3d import CuerpoHumano
from .estilo import CUERPO, PALETA, aplicar_estilo_3d

ANCLA_Z = 43.60
ALTURA_TORRE = 72.0
LADO_TORRE = 18.0


def _cara(ax, puntos, color, alpha=0.5, borde=None, lw=0.5):
    colleccion = Poly3DCollection(
        [puntos],
        facecolor=color,
        edgecolor=borde or PALETA["borde"],
        linewidths=lw,
        alpha=alpha,
    )
    ax.add_collection3d(colleccion)
    return colleccion


def construir_torre(ax) -> dict:
    """Torre estilizada con ventanales, reloj y ancla sobre fondo oscuro."""
    L = LADO_TORRE
    H = ALTURA_TORRE
    suelo = _cara(ax, [(-L, -L, 0), (L, -L, 0), (L, L, 0), (-L, L, 0)], "#111821", 0.95, PALETA["borde"], 0.8)
    paredes = []
    for x0, y0, x1, y1 in [(-L, -L, L, -L), (L, -L, L, L), (L, L, -L, L), (-L, L, -L, -L)]:
        paredes.append(
            _cara(
                ax,
                [(x0, y0, 0), (x1, y1, 0), (x1, y1, H), (x0, y0, H)],
                "#1b2635",
                0.22,
                "#31465c",
                0.8,
            )
        )
        # aristas verticales iluminadas
        ax.plot([x0, x0], [y0, y0], [0, H], color=PALETA["cian"], alpha=0.18, lw=0.8)

    ventanas = []
    for z0 in (10, 25, 40, 55):
        for x0 in (-L + 2, -6, 6):
            ventanas.append(
                _cara(
                    ax,
                    [(x0, -L + 0.15, z0), (x0 + 4, -L + 0.15, z0), (x0 + 4, -L + 0.15, z0 + 7), (x0, -L + 0.15, z0 + 7)],
                    PALETA["cian"],
                    0.10,
                    PALETA["cian"],
                    0.4,
                )
            )
    # reloj
    theta = np.linspace(0, 2 * np.pi, 48)
    reloj_pts = [(7.5 * np.cos(t), -L + 0.25, 60 + 7.5 * np.sin(t)) for t in theta]
    reloj = _cara(ax, reloj_pts, PALETA["seda"], 0.92, "#f9e79f", 1.0)
    (aguja_hora,) = ax.plot([0, 0], [-L + 0.4, -L + 0.4], [60, 66], color=PALETA["texto"], lw=2.0)
    (aguja_min,) = ax.plot([0, 3.2], [-L + 0.4, -L + 0.4], [60, 60], color=PALETA["texto"], lw=1.5)
    # ancla y halo
    (ancla,) = ax.plot([0], [0], [ANCLA_Z], "o", color=PALETA["alerta"], ms=8, markeredgecolor="#ffd1d1")
    (halo,) = ax.plot([0, 0], [0, 0], [ANCLA_Z - 0.6, ANCLA_Z + 0.6], color=PALETA["alerta"], alpha=0.35, lw=1.0)
    # rejilla
    rejilla = []
    for v in np.linspace(-L, L, 13):
        (ln,) = ax.plot([v, v], [-L, L], [0.02, 0.02], color=PALETA["borde"], lw=0.45, alpha=0.75)
        rejilla.append(ln)
        (ln,) = ax.plot([-L, L], [v, v], [0.02, 0.02], color=PALETA["borde"], lw=0.45, alpha=0.75)
        rejilla.append(ln)
    return {
        "suelo": suelo,
        "paredes": paredes,
        "ventanas": ventanas,
        "reloj": reloj,
        "aguja_hora": aguja_hora,
        "aguja_min": aguja_min,
        "ancla": ancla,
        "halo": halo,
        "rejilla": rejilla,
    }


_U_BEZIER = np.linspace(0.0, 1.0, 32)
_B0 = (1.0 - _U_BEZIER)[:, None] ** 3
_B1 = 3.0 * (1.0 - _U_BEZIER)[:, None] ** 2 * _U_BEZIER[:, None]
_B2 = 3.0 * (1.0 - _U_BEZIER)[:, None] * _U_BEZIER[:, None] ** 2
_B3 = _U_BEZIER[:, None] ** 3
_SIN_PI_U = np.sin(np.pi * _U_BEZIER)
_ANG_SOMBRA = np.linspace(0.0, 2 * np.pi, 32)
_COS_SOMBRA = np.cos(_ANG_SOMBRA)
_SIN_SOMBRA = 0.52 * np.sin(_ANG_SOMBRA)
_ZEROS_SOMBRA = np.full_like(_ANG_SOMBRA, 0.008)


@dataclass
class Escena3D:
    fig: object
    ax: object
    resultado: object | None
    estaticos: dict
    cuerpo: CuerpoHumano
    web: object | None = None
    estela: object | None = None
    sombra: object | None = None
    marcador: object | None = None
    etiqueta_ancla: object | None = None
    vista: str = "cuerpo"
    n_artistas: int = 0

    def aplicar_vista(self, modo: str, altura: float = 1.2) -> None:
        """Tres encuadres: cuerpo (detalle), torre (contexto) y seguir."""
        modo = modo.lower()
        self.vista = modo
        torre = modo == "torre"
        for clave in ("paredes", "ventanas", "reloj", "aguja_hora", "aguja_min", "suelo", "rejilla"):
            artista = self.estaticos.get(clave)
            if artista is None:
                continue
            if isinstance(artista, list):
                for a in artista:
                    a.set_visible(torre)
            else:
                artista.set_visible(torre)
        self.etiqueta_ancla.set_visible(not torre)
        if self.estela is not None:
            self.estela.set_visible(torre)
        if torre:
            self.ax.set_axis_on()
            self.ax.grid(True, color=PALETA["borde"], alpha=0.25)
        else:
            self.ax.set_axis_off()
        if modo == "torre":
            self.ax.set_xlim(-LADO_TORRE, LADO_TORRE)
            self.ax.set_ylim(-LADO_TORRE, LADO_TORRE)
            self.ax.set_zlim(0, ALTURA_TORRE + 2)
            self.ax.set_box_aspect((1, 1, 2.8))
            self.ax.view_init(elev=10, azim=-68)
        elif modo == "seguir":
            z0 = max(0.0, altura - 0.95)
            z1 = z0 + (2.2 if altura < 2.2 else 1.9)
            self.ax.set_xlim(-1.0, 1.0)
            self.ax.set_ylim(-1.0, 1.0)
            self.ax.set_zlim(z0, z1)
            self.ax.set_box_aspect((1, 1, 1.2))
            self.ax.view_init(elev=6, azim=-72)
        else:
            self.ax.set_xlim(-1.3, 1.3)
            self.ax.set_ylim(-1.3, 1.3)
            self.ax.set_zlim(0, 2.7)
            self.ax.set_box_aspect((1, 1, 1.35))
            self.ax.view_init(elev=6, azim=-72)

    def actualizar(self, estado: dict, trayectoria: np.ndarray | None = None) -> None:
        h = float(np.clip(estado.get("altura_torso", 1.2), -0.5, ALTURA_TORRE))
        fase = int(estado.get("fase", 0))
        t = float(estado.get("t", 0.0))
        self.cuerpo.actualizar(estado)
        if self.vista == "seguir":
            z0 = max(0.0, h - 0.95)
            z1 = z0 + (2.2 if h < 2.2 else 1.9)
            self.ax.set_zlim(z0, z1)
        cintura = self.cuerpo.punto_cintura(estado)

        # Seda: curva de Bézier desde el ancla hasta el costado de la cintura.
        ancla = np.array([0.0, 0.0, ANCLA_Z])
        if fase == 1:
            control1 = np.array([0.04, 0.03, ANCLA_Z * 0.62])
            control2 = np.array([0.12, 0.05, h + 0.55])
        else:
            control1 = np.array([0.28, 0.10, ANCLA_Z * 0.70])
            control2 = np.array([0.42, 0.18, h + 1.8])
        bezier = (
            _B0 * ancla
            + _B1 * control1
            + _B2 * control2
            + _B3 * cintura
        )
        if fase == 1 and self.resultado is not None:
            tau = max(0.0, t - self.resultado.t_tensado_s)
            vib = 0.040 * np.sin(2 * np.pi * tau / 0.035) * np.exp(-tau / 0.08)
            bezier[:, 0] += vib * _SIN_PI_U
        self.web.set_data_3d(bezier[:, 0], bezier[:, 1], bezier[:, 2])
        self.web.set_color(PALETA["seda"])
        self.web.set_linewidth(2.6 if fase == 1 else 1.6)
        self.web.set_alpha(0.98 if fase == 1 else 0.60)

        # Sombra elíptica en el suelo.
        r = 0.58 * max(0.12, 1.0 - h / 65.0)
        sombra = np.column_stack([r * _COS_SOMBRA, r * _SIN_SOMBRA, _ZEROS_SOMBRA])
        self.sombra.set_verts([sombra])
        self.sombra.set_facecolor("#000000")
        self.sombra.set_alpha(0.42)

        # Estela y marcador de la cintura.
        if trayectoria is not None:
            self.estela.set_data_3d(trayectoria[:, 0], trayectoria[:, 1], trayectoria[:, 2])
        self.marcador.set_data_3d([cintura[0]], [cintura[1]], [cintura[2]])

    def contar_artistas(self) -> int:
        return len(self.ax.lines) + len(self.ax.collections)


def centrar_vista(ax) -> None:
    ax.view_init(elev=10, azim=-68)
    ax.set_xlim(-LADO_TORRE, LADO_TORRE)
    ax.set_ylim(-LADO_TORRE, LADO_TORRE)
    ax.set_zlim(0, ALTURA_TORRE + 2)


def construir_escena(fig, ax, resultado=None) -> Escena3D:
    aplicar_estilo_3d(fig, ax)
    estaticos = construir_torre(ax)
    cuerpo = CuerpoHumano(ax, t_tensado_s=getattr(resultado, "t_tensado_s", 0.0))
    (web,) = ax.plot([0, 0], [0, 0], [ANCLA_Z, ANCLA_Z], color=PALETA["seda"], lw=1.6, ls="-")
    (estela,) = ax.plot([0], [0], [ANCLA_Z], color=PALETA["naranja"], lw=1.1, alpha=0.40, ls=":")
    (marcador,) = ax.plot([0], [0], [1.2], "o", color=PALETA["cian"], ms=4, alpha=0.8)
    sombra = Poly3DCollection(
        [],
        facecolor="#000000",
        edgecolor=(0.30, 0.78, 0.94, 0.30),
        linewidths=0.8,
        alpha=0.45,
    )
    ax.add_collection3d(sombra)
    centrar_vista(ax)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("altura (m)")
    etiqueta = ax.text2D(
        0.02,
        0.94,
        "ancla 43.60 m  ↑\nseda de 42.00 m",
        transform=ax.transAxes,
        color=PALETA["seda"],
        fontsize=8,
        va="top",
    )
    n = len(ax.lines) + len(ax.collections)
    escena = Escena3D(
        fig=fig,
        ax=ax,
        resultado=resultado,
        estaticos=estaticos,
        cuerpo=cuerpo,
        web=web,
        estela=estela,
        sombra=sombra,
        marcador=marcador,
        etiqueta_ancla=etiqueta,
        n_artistas=n,
    )
    escena.aplicar_vista("seguir", 1.2)
    return escena
