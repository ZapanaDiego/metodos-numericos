"""Escena 3D de la torre, el cuerpo y la telaraña (mplot3d).

La escena se construye una sola vez y se actualiza con ``actualizar``. El
número de artistas no crece entre frames. Unidades: metros; ``z`` es la altura
sobre el suelo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from mpl_toolkits.mplot3d.art3d import Line3D, Poly3DCollection

ANCLA_Z = 43.60
ALTURA_TORRE = 72.0
LADO_TORRE = 18.0
ALTURA_TORSO_FINAL = 1.20


def _cara(ax, puntos, color, alpha=0.5, borde="#2c3e50", lw=0.5):
    colleccion = Poly3DCollection([puntos], facecolor=color, edgecolor=borde, linewidths=lw, alpha=alpha)
    ax.add_collection3d(colleccion)
    return colleccion


def construir_torre(ax) -> dict:
    """Torre estilizada, suelo, reloj y ancla. Devuelve colecciones estáticas."""
    L = LADO_TORRE
    H = ALTURA_TORRE
    # suelo
    suelo = _cara(ax, [(-L, -L, 0), (L, -L, 0), (L, L, 0), (-L, L, 0)], "#d5d8dc", 0.9)
    # cuatro paredes (sin techo para ver el interior)
    paredes = []
    for x0, y0, x1, y1 in [(-L, -L, L, -L), (L, -L, L, L), (L, L, -L, L), (-L, L, -L, -L)]:
        paredes.append(
            _cara(
                ax,
                [(x0, y0, 0), (x1, y1, 0), (x1, y1, H), (x0, y0, H)],
                "#aeb6bf",
                0.18,
            )
        )
    # ventanales como paneles semitransparentes en dos paredes
    ventanas = []
    for z0 in (12, 28, 44, 58):
        ventanas.append(
            _cara(ax, [(-L, -L + 0.2, z0), (L, -L + 0.2, z0), (L, -L + 0.2, z0 + 8), (-L, -L + 0.2, z0 + 8)], "#5dade2", 0.20, "#85c1e9")
        )
    # esfera del reloj (círculo en el plano y=0)
    theta = np.linspace(0, 2 * np.pi, 40)
    reloj_pts = [(8 * np.cos(t), -L + 0.3, 60 + 8 * np.sin(t)) for t in theta]
    reloj = _cara(ax, reloj_pts, "#f7dc6f", 0.85, "#b7950b", 1.0)
    # agujas
    (aguja_hora,) = ax.plot([0, 0], [-L + 0.4, -L + 0.4], [60, 66], color="#1c2833", lw=2)
    (aguja_min,) = ax.plot([0, 3], [-L + 0.4, -L + 0.4], [60, 60], color="#1c2833", lw=1.5)
    # ancla
    (ancla,) = ax.plot([0], [0], [ANCLA_Z], "o", color="#c0392b", ms=7)
    # rejilla del suelo
    rejilla = []
    for v in np.linspace(-L, L, 9):
        (ln,) = ax.plot([v, v], [-L, L], [0.02, 0.02], color="#95a5a6", lw=0.5)
        rejilla.append(ln)
        (ln,) = ax.plot([-L, L], [v, v], [0.02, 0.02], color="#95a5a6", lw=0.5)
        rejilla.append(ln)
    return {
        "suelo": suelo,
        "paredes": paredes,
        "ventanas": ventanas,
        "reloj": reloj,
        "aguja_hora": aguja_hora,
        "aguja_min": aguja_min,
        "ancla": ancla,
        "rejilla": rejilla,
    }


@dataclass
class Escena3D:
    fig: object
    ax: object
    estaticos: dict
    segmentos: list = field(default_factory=list)
    web: object | None = None
    estela: object | None = None
    puntos: dict = field(default_factory=dict)
    n_artistas: int = 0

    def actualizar(self, estado: dict, trayectoria: np.ndarray | None = None) -> None:
        """Actualiza el cuerpo y la seda sin crear artistas nuevos."""
        h = float(np.clip(estado["altura_torso"], -0.5, ALTURA_TORRE))
        # pequeña inclinación durante el frenado para visualizar el latigazo
        a_g = float(estado.get("a_g", 1.0))
        fase = int(estado.get("fase", 0))
        sway = 0.0
        if fase == 1:
            sway = np.clip((a_g - 1.0) / 300.0, 0.0, 0.25)
        # siete segmentos: cabeza, cuello, torso, pelvis, brazo izq., brazo der., piernas
        pts = np.array(
            [
                [0.0, 0.0, h + 1.05],  # coronilla
                [0.0, 0.0, h + 0.78],  # cuello
                [0.0, 0.0, h + 0.42],  # hombros
                [0.0, 0.0, h],  # torso
                [0.0, 0.0, h - 0.35],  # pelvis
                [0.35 + sway, 0.0, h + 0.05],  # mano derecha
                [-0.35 + sway, 0.0, h + 0.05],  # mano izquierda
                [0.0, 0.0, h - 0.85],  # rodillas
                [0.0, 0.0, h - 1.15],  # pies
            ]
        )
        segmentos = [
            (pts[0], pts[1]),
            (pts[1], pts[2]),
            (pts[2], pts[3]),
            (pts[3], pts[4]),
            (pts[2], pts[5]),
            (pts[2], pts[6]),
            (pts[4], pts[8]),
        ]
        for linea, (p0, p1) in zip(self.segmentos, segmentos, strict=True):
            linea.set_data_3d([p0[0], p1[0]], [p0[1], p1[1]], [p0[2], p1[2]])
        # seda: ancla -> torso
        self.web.set_data_3d([0.0, 0.0], [0.0, 0.0], [ANCLA_Z, h + 0.42])
        self.web.set_linestyle("-" if fase == 1 else ":")
        self.web.set_linewidth(2.0 if fase == 1 else 1.0)
        # cabeza como marcador
        self.puntos["cabeza"].set_data_3d([0.0], [0.0], [h + 1.05])
        if trayectoria is not None and self.estela is not None:
            self.estela.set_data_3d(trayectoria[:, 0], trayectoria[:, 1], trayectoria[:, 2])

    def contar_artistas(self) -> int:
        return len(self.ax.lines) + len(self.ax.collections)


def construir_escena(fig, ax) -> Escena3D:
    estaticos = construir_torre(ax)
    segmentos = []
    for _ in range(7):
        (ln,) = ax.plot([0, 0], [0, 0], [0, 0], color="#c0392b", lw=3, solid_capstyle="round")
        segmentos.append(ln)
    (web,) = ax.plot([0, 0], [0, 0], [ANCLA_Z, ANCLA_Z], color="#f1c40f", lw=1.0, ls=":")
    (estela,) = ax.plot([0], [0], [ANCLA_Z], color="#e67e22", lw=1.0, alpha=0.6)
    (cabeza,) = ax.plot([0], [0], [ANCLA_Z], "o", color="#c0392b", ms=7)
    ax.set_xlim(-LADO_TORRE, LADO_TORRE)
    ax.set_ylim(-LADO_TORRE, LADO_TORRE)
    ax.set_zlim(0, ALTURA_TORRE + 2)
    ax.set_box_aspect((1, 1, 2.8))
    ax.view_init(elev=10, azim=-70)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("altura (m)")
    n = len(ax.lines) + len(ax.collections)
    return Escena3D(
        fig=fig,
        ax=ax,
        estaticos=estaticos,
        segmentos=segmentos,
        web=web,
        estela=estela,
        puntos={"cabeza": cabeza},
        n_artistas=n,
    )
