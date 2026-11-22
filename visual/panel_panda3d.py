"""Panel y gráficas en coordenadas de diseño de 1100 × 700."""
import numpy as np
from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import CardMaker, LineSegs, TextNode

ANCHO, ALTO = 1100, 700
ESCENA = (18, 86, 604, 595)
CIAN = (0.36, 0.84, 1, 1)
BLANCO = (0.91, 0.95, 0.99, 1)
AMBAR = (1, 0.69, 0.44, 1)
MUTED = (0.66, 0.73, 0.82, 1)
SUPERFICIE = (0.07, 0.10, 0.15, 1)
TARJETA = (0.10, 0.14, 0.20, 1)
ACTIVO = (0.12, 0.32, 0.41, 1)


def rectangulo(padre, x, y, w, h, color):
    tarjeta = CardMaker("fondo")
    tarjeta.setFrame(x, x + w, -y - h, -y)
    nodo = padre.attachNewNode(tarjeta.generate())
    nodo.setColor(*color)
    return nodo


def texto(padre, x, y, contenido="", tam=14, color=BLANCO, mutable=False):
    return OnscreenText(parent=padre, pos=(x, -y), text=contenido, scale=tam,
                        align=TextNode.ALeft, fg=color, mayChange=mutable)


def boton(padre, x, y, w, h, nombre, accion):
    return DirectButton(parent=padre, pos=(x + w / 2, 0, -y - h / 2),
                        frameSize=(-w / 2, w / 2, -h / 2, h / 2),
                        frameColor=TARJETA, relief=DGG.FLAT, pressEffect=False,
                        text=nombre, text_pos=(0, -4), text_scale=13, text_fg=BLANCO,
                        command=accion)


def trazo(padre, puntos, color, grosor=1):
    linea = LineSegs()
    linea.setColor(*color)
    linea.setThickness(grosor)
    for i, (x, y) in enumerate(puntos):
        if i:
            linea.drawTo(x, 0, -y)
        else:
            linea.moveTo(x, 0, -y)
    return padre.attachNewNode(linea.create())


class Grafica:
    """Abscisas en tiempo físico y cursor ligado a la corrida activa."""

    def __init__(self, padre, x, y):
        self.raiz = padre.attachNewNode("gráfica")
        self.raiz.setPos(x, 0, -y)
        rectangulo(self.raiz, 0, 0, 438, 125, TARJETA)
        self.datos = self.raiz.attachNewNode("ejes y series")
        self.cursor = trazo(self.raiz, [(0, 29), (0, 94)], BLANCO)
        self.limites = (0, 1)

    def configurar(self, titulo, unidad_t, series, limites, eventos, nota):
        for nodo in self.datos.getChildren():
            nodo.removeNode()
        self.limites = limites
        a, b = limites
        vmax = max(0, *(float(np.max(y)) for _, y, _ in series))
        vmin = min(0, *(float(np.min(y)) for _, y, _ in series))
        if vmax <= vmin:
            vmax = vmin + 1

        def px(t):
            return 45 + 375 * (t - a) / (b - a)

        def py(v):
            return 94 - 65 * (v - vmin) / (vmax - vmin)

        texto(self.datos, 12, 18, titulo, 14)
        texto(self.datos, 269, 18, nota, 11, MUTED)
        for v in np.unique([vmin, 0, vmax]):
            y = py(v)
            texto(self.datos, 8, y + 4, f"{v:.2g}", 11, MUTED)
            trazo(self.datos, [(45, y), (420, y)], (0.23, 0.29, 0.38, 1))
        for fraccion in (0, 0.25, 0.5, 0.75, 1):
            t = a + (b - a) * fraccion
            texto(self.datos, px(t) - 8, 110, f"{t:.3g}", 11, MUTED)
        texto(self.datos, 11, 115, unidad_t, 10, MUTED)
        for t, color in eventos:
            if a <= t <= b:
                trazo(self.datos, [(px(t), 29), (px(t), 94)], color)
        for t, y, color in series:
            if len(t) > 1:
                trazo(self.datos, zip(px(t), py(y)), color, 2)

    def actualizar(self, t):
        a, b = self.limites
        if a <= t <= b:
            self.cursor.show()
            self.cursor.setX(45 + 375 * (t - a) / (b - a))
        else:
            self.cursor.hide()
