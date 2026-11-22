"""Visor de escritorio del laboratorio de Euler y Runge–Kutta."""
from __future__ import annotations

import argparse
import subprocess
import sys
from math import cos, sin
from time import perf_counter

import numpy as np
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight, DirectionalLight, Filename, LineSegs, Point3, Quat,
    Vec3, loadPrcFileData,
)

from simulador.mediciones import energias, primer_contacto, segmentos
from simulador.modelo import inspeccionar_paso, simular
from simulador.parametros import Computo, Escena
from .animacion import avanzar_reloj
from .panel_panda3d import (
    ACTIVO, ALTO, AMBAR, ANCHO, BLANCO, CIAN, ESCENA, MUTED, SUPERFICIE,
    TARJETA, Grafica, boton, rectangulo, texto,
)

PASOS_MS = (0.25, 0.5, 1, 2, 4, 8)
PISOS = ((0.0, 0.0), (1.00, -0.50), (0.85, 0.0))


def linea(padre, puntos, color, grosor=2):
    trazo = LineSegs()
    trazo.setThickness(grosor)
    trazo.setColor(*color)
    trazo.moveTo(*puntos[0])
    for punto in puntos[1:]:
        trazo.drawTo(*punto)
    return padre.attachNewNode(trazo.create(dynamic=True))


def inclinacion(nodo, grados):
    q = Quat()
    q.setFromAxisAngle(grados, Vec3(0, 1, 0))
    nodo.setQuat(q)


class Visor(ShowBase):
    """La tarea gráfica lee estados precalculados e interpola por tiempo físico."""

    def __init__(self, fuera_pantalla=False):
        super().__init__(windowType="offscreen" if fuera_pantalla else "onscreen")
        if self.win is None:
            raise RuntimeError("Panda3D no pudo abrir una superficie gráfica.")
        self.disableMouse()
        self.setBackgroundColor(0.025, 0.04, 0.06)
        self.camLens.setNearFar(0.05, 160)
        self.region_3d = self.cam.node().getDisplayRegion(0)
        ambiente = AmbientLight("ambiente")
        ambiente.setColor((0.53, 0.59, 0.69, 1))
        self.render.setLight(self.render.attachNewNode(ambiente))
        luz = DirectionalLight("luz lateral")
        luz.setColor((0.88, 0.80, 0.73, 1))
        foco = self.render.attachNewNode(luz)
        foco.setHpr(25, -48, 0)
        self.render.setLight(foco)
        self.esfera = self.loader.loadModel("models/misc/sphere")
        self.caja = self.loader.loadModel("models/box")
        self.esfera.setTextureOff(1)
        self.caja.setTextureOff(1)
        self.escena = Escena.pelicula()
        self.referencia = simular(self.escena)
        self.vista = "seguir"
        self.indice_h = 2
        self.metodo = "rk4"
        self.indice_piso = 0
        self.piso_m = 0.0
        self.t = 0.0
        self.play = False
        self.zoom_grafica = False
        self.ver_edo = False
        self.giro = 0.0
        self.distancia = 1.0
        self.arrastre_x = None
        self.ultimo_cuadro = perf_counter()
        self._crear_torre()
        self._crear_cuerpo()
        self._crear_panel()
        self._ajustar_ventana(self.win)
        self._calcular()
        self.taskMgr.add(self._cuadro, "reproducción")

    def _volumen(self, modelo, padre, posicion, escala, color):
        pieza = modelo.copyTo(padre)
        pieza.setPos(*posicion)
        pieza.setScale(*escala)
        pieza.setColor(*color)
        return pieza

    def _crear_torre(self):
        self.piso = self.render.attachNewNode("piso")
        for i in range(8):
            self._volumen(self.caja, self.piso, (-4, i - 4, -0.17), (8, 0.96, 0.16),
                          (0.20 + i % 2 * 0.035, 0.17, 0.15, 1))
        acero = (0.19, 0.24, 0.29, 1)
        for x, y in ((-4, 3), (4, 3), (-4, -5), (4, -5)):
            self._volumen(self.caja, self.render, (x, y, 0), (0.24, 0.24, 44), acero)
        for z in range(0, 44, 3):
            self._volumen(self.caja, self.render, (-4, 3, z), (8, 0.2, 0.19), acero)
            linea(self.render, [(-2.5, 0, z), (-2.16, 0, z)], CIAN, 1)
        linea(self.render, [(-2.5, 0, 0), (-2.5, 0, 43.6)], CIAN, 1)
        self._volumen(self.esfera, self.render, (0, 0, self.escena.h_ancla_m),
                      (0.16, 0.16, 0.16), CIAN)
        self.seda = self.render.attachNewNode("seda")
        self.origen_seda = Point3(0, 0, self.escena.h_ancla_m)
        self.guia = self.render.attachNewNode("mediciones")

    def _crear_cuerpo(self):
        # Eje X hacia la cabeza y Z hacia el frente del personaje.
        self.cuerpo = self.render.attachNewNode("agarre abdominal")
        self.fantasma = self._volumen(self.esfera, self.render, (0, 0, 0),
                                      (0.10, 0.10, 0.10), AMBAR)
        abrigo = (0.17, 0.54, 0.57, 1)
        piel = (0.79, 0.55, 0.39, 1)
        oscuro = (0.13, 0.12, 0.23, 1)
        cabello = (0.47, 0.28, 0.14, 1)

        def pieza(padre, centro, escala, color):
            return self._volumen(self.esfera, padre, centro, escala, color)

        pieza(self.cuerpo, (0.10, 0, -0.09), (0.32, 0.22, 0.13), abrigo)
        pieza(self.cuerpo, (-0.19, 0, -0.09), (0.20, 0.19, 0.12), oscuro)
        self.cabeza = self.cuerpo.attachNewNode("cuello")
        self.cabeza.setX(0.39)
        pieza(self.cabeza, (0.035, 0, -0.015), (0.07, 0.06, 0.066), piel)
        pieza(self.cabeza, (0.18, 0, 0), (0.10, 0.085, 0.095), piel)
        pieza(self.cabeza, (0.19, 0, -0.043), (0.13, 0.106, 0.075), cabello)
        self.piernas = self.cuerpo.attachNewNode("caderas")
        self.piernas.setX(-0.27)
        self.brazos = []
        for signo in (-1, 1):
            brazo = self.cuerpo.attachNewNode("hombro")
            brazo.setPos(0.25, signo * 0.18, -0.08)
            pieza(brazo, (-0.06, signo * 0.13, 0), (0.09, 0.16, 0.065), abrigo)
            pieza(brazo, (0.003, signo * 0.31, 0.035), (0.08, 0.13, 0.047), abrigo)
            pieza(brazo, (0.05, signo * 0.43, 0.04), (0.06, 0.045, 0.026), piel)
            self.brazos.append(brazo)
            lateral = signo * 0.105
            pieza(self.piernas, (-0.21, lateral, -0.01), (0.25, 0.10, 0.088), oscuro)
            pieza(self.piernas, (-0.58, lateral, -0.035), (0.23, 0.068, 0.065), oscuro)
            pieza(self.piernas, (-0.79, lateral, 0.00), (0.075, 0.067, 0.08), oscuro)
        for x in (-0.14, 0, 0.14):
            for y in (-0.16, 0.16):
                linea(self.cuerpo, [(x, y, -0.015), (0, 0, 0)], CIAN, 1)

    def _crear_panel(self):
        self.panel = self.pixel2d.attachNewNode("laboratorio")
        rectangulo(self.panel, 18, 15, 586, 62, SUPERFICIE)
        rectangulo(self.panel, 18, 604, 586, 82, SUPERFICIE)
        rectangulo(self.panel, 620, 15, 462, 671, SUPERFICIE)
        texto(self.panel, 32, 43, "Caída y frenado", 23)
        texto(self.panel, 32, 65, "Laboratorio de Euler y Runge-Kutta", 13, MUTED)
        self.ayuda_camara = texto(self.panel, 335, 65, tam=12, color=MUTED, mutable=True)
        self.fase_texto = texto(self.panel, 32, 676, tam=13, color=MUTED, mutable=True)

        self.b_reproducir = boton(self.panel, 30, 615, 112, 31, "Reproducir", self._alternar)
        boton(self.panel, 150, 615, 70, 31, "Inicio", self._inicio)
        boton(self.panel, 228, 615, 131, 31, "Avanzar un paso", self._paso)
        boton(self.panel, 367, 615, 105, 31, "Ir al tensado", self._saltar_tensado)
        self.b_vista = boton(self.panel, 480, 615, 114, 31, "Vista: Seguir", self._cambiar_vista)
        self.b_restablecer = boton(self.panel, 450, 652, 144, 26, "Restablecer cámara",
                                   self._restablecer_camara)

        texto(self.panel, 632, 49, "Método de integración", 15)
        self.botones_metodo = {
            metodo: boton(self.panel, 838 + 111 * i, 28, 105, 30, etiqueta,
                          lambda m=metodo: self._metodo(m))
            for i, (metodo, etiqueta) in enumerate((("euler", "Euler"), ("rk4", "RK4")))
        }
        texto(self.panel, 632, 85, "Paso de integración h", 14, MUTED)
        boton(self.panel, 815, 64, 31, 28, "-", lambda: self._cambiar_h(-1))
        self.paso_texto = texto(self.panel, 855, 84, tam=14, mutable=True)
        boton(self.panel, 927, 64, 31, 28, "+", lambda: self._cambiar_h(1))
        boton(self.panel, 972, 64, 94, 28, "Escenario", self._alternar_piso)

        etiquetas = (
            "Altura z", "Velocidad vertical v", "Aceleración vertical a",
            "Tensión F", "Elongación x", "Energía en seda E",
            "Potencia P", "Error de altura",
        )
        self.lecturas = []
        for i, etiqueta in enumerate(etiquetas):
            fila, columna = divmod(i, 2)
            x, y = 632 + 222 * columna, 107 + 43 * fila
            rectangulo(self.panel, x, y, 216, 39, TARJETA)
            texto(self.panel, x + 9, y + 14, etiqueta, 11, MUTED)
            self.lecturas.append(texto(self.panel, x + 9, y + 33, tam=16, mutable=True))

        self.modo_grafico = self.panel.attachNewNode("gráficas")
        self.grafica_v = Grafica(self.modo_grafico, 632, 336)
        self.grafica_f = Grafica(self.modo_grafico, 632, 469)
        self.b_zoom = boton(self.modo_grafico, 920, 300, 150, 27, "Ampliar frenado",
                            self._ampliar_frenado)
        self.modo_edo = self.panel.attachNewNode("ecuaciones")
        rectangulo(self.modo_edo, 632, 336, 438, 258, TARJETA)
        self.ecuacion = texto(self.modo_edo, 644, 364, tam=15, mutable=True)
        self.etapas = texto(self.modo_edo, 644, 433, tam=14, mutable=True)
        self.modo_edo.hide()
        self.b_edo = boton(self.panel, 632, 300, 107, 27, "Ver EDO", self._alternar_edo)
        boton(self.panel, 746, 300, 166, 27, "Gráficas y tablas", self._abrir_laboratorio)
        self.leyenda = texto(self.modo_grafico, 897, 290, tam=11, color=MUTED, mutable=True)
        self.estado = texto(self.panel, 632, 623, tam=12, color=MUTED, mutable=True)

        for tecla, accion in (("space", self._alternar), ("home", self._inicio),
                              ("arrow_right", self._paso), ("escape", self.userExit),
                              ("mouse1", self._iniciar_arrastre), ("mouse1-up", self._soltar_arrastre),
                              ("wheel_up", lambda: self._acercar(0.88)),
                              ("wheel_down", lambda: self._acercar(1 / 0.88))):
            self.accept(tecla, accion)

    def windowEvent(self, ventana):
        """Conserva el ciclo de ventana de Panda3D y reajusta el área 3D."""
        super().windowEvent(ventana)
        if ventana == self.win and hasattr(self, "panel"):
            self._ajustar_ventana(ventana)

    def _ajustar_ventana(self, ventana):
        # Usa las dimensiones de pixel2d, que ShowBase acaba de actualizar.
        w, h = ventana.getSbsLeftXSize(), ventana.getSbsLeftYSize()
        if w <= 0 or h <= 0:
            return
        escala = min(w / ANCHO, h / ALTO)
        ox, oy = (w - ANCHO * escala) / 2, (h - ALTO * escala) / 2
        self.panel.setPos(ox, 0, -oy)
        self.panel.setScale(escala)
        x0, y0, x1, y1 = ESCENA
        self.region_3d.setDimensions((ox + x0 * escala) / w, (ox + x1 * escala) / w,
                                     1 - (oy + y1 * escala) / h, 1 - (oy + y0 * escala) / h)
        self.camLens.setAspectRatio((x1 - x0) / (y1 - y0))
        self.camLens.setFov(54)

    def _raton_en_visor(self):
        if not self.play and self.mouseWatcherNode and self.mouseWatcherNode.hasMouse():
            x, y = self.mouseWatcherNode.getMouse()
            region = self.region_3d
            if (region.getLeft() < (x + 1) / 2 < region.getRight()
                    and region.getBottom() < (y + 1) / 2 < region.getTop()):
                return x
        return None

    def _iniciar_arrastre(self):
        self.arrastre_x = self._raton_en_visor()

    def _soltar_arrastre(self):
        self.arrastre_x = None

    def _acercar(self, factor):
        if self._raton_en_visor() is not None:
            self.distancia = float(np.clip(self.distancia * factor, 0.38, 2.2))
            self._aplicar_camara()

    def _restablecer_camara(self):
        self.giro = 0.0
        self.distancia = 1.0
        self.arrastre_x = None
        self._aplicar_camara()

    def _aplicar_camara(self):
        altura = self.cuerpo.getZ()
        if self.vista == "torre":
            objetivo, offset = Point3(0, 0, 22), Vec3(9, -60, 2)
        elif self.vista == "cuerpo":
            objetivo = Point3(0, 0, max(self.piso_m + 0.52, altura) - 0.10)
            offset = Vec3(0.1, -3.65, 0.32)
        else:
            objetivo, offset = Point3(0, 0, altura + 0.17), Vec3(2.2, -4, 0.48)
        c, s = cos(self.giro), sin(self.giro)
        lateral = Vec3(c * offset.x - s * offset.y, s * offset.x + c * offset.y, offset.z)
        self.camera.setPos(objetivo + lateral * self.distancia)
        self.camera.lookAt(objetivo)

    def _ampliar_frenado(self):
        self.zoom_grafica = not self.zoom_grafica
        self.b_zoom["text"] = "Ver caída completa" if self.zoom_grafica else "Ampliar frenado"
        self._configurar_graficas()
        self._dibujar()

    def _alternar_edo(self):
        self.ver_edo = not self.ver_edo
        self.b_edo["text"] = "Ver gráficas" if self.ver_edo else "Ver EDO"
        if self.ver_edo:
            self.modo_grafico.hide()
            self.modo_edo.show()
        else:
            self.modo_edo.hide()
            self.modo_grafico.show()
        self._dibujar()

    def _abrir_laboratorio(self):
        _, postura = PISOS[self.indice_piso]
        subprocess.Popen([
            sys.executable, "-m", "visual.laboratorio_datos",
            "--metodo", self.r.metodo, "--paso", str(self.r.paso_s),
            "--piso", str(self.piso_m), "--postura", str(postura),
            "--instante", str(self.t),
        ])

    def _configurar_graficas(self):
        base = self.r.t_tensado_s if self.zoom_grafica else 0.0
        inicio_v = max(0.0, min(base, self.referencia.t_tensado_s) - 0.004)
        inicio_zoom = (inicio_v - base) * 1000 if self.zoom_grafica else 0.0
        escala = 1000 if self.zoom_grafica else 1
        series_v, series_f = [], []
        for r, color in ((self.referencia, AMBAR), (self.r, CIAN)):
            fin = self.fin if r is self.r else r.t[-1]
            # Agrega los extremos de la ventana por interpolación.
            inicio = min(inicio_v, fin)
            t = np.unique(np.r_[inicio, r.t[(r.t > inicio) & (r.t < fin)], fin])
            series_v.append(((t - base) * escala, np.interp(t, r.t, r.v_m_s), color))
            t = np.unique(np.r_[r.t_tensado_s, r.t[(r.t > r.t_tensado_s) & (r.t < fin)], fin])
            series_f.append(((t - r.t_tensado_s) * 1000,
                             np.interp(t, r.t, r.elongacion_m) * r.k_n_m / 1000, color))
        pico = self.r.t_pico_s
        fin_v = max((max(self.fin, self.referencia.t[-1]) - base) * escala, 1e-6)
        self.grafica_v.configurar(
            "Velocidad vertical v (m/s)", "ms" if self.zoom_grafica else "s",
            series_v, (inicio_zoom, fin_v),
            [((self.r.t_tensado_s - base) * escala, AMBAR),
             ((self.r.t_tensado_s + pico - base) * escala, MUTED)],
            "Marcas: tensado y v = 0")
        self.grafica_f.configurar("Tensión F (kN)", "ms",
                                 series_f, (0, max(t[-1] for t, _, _ in series_f)), [(pico * 1000, MUTED)], "Desde el tensado")

    def _calcular(self):
        self.r = simular(self.escena, computo=Computo(PASOS_MS[self.indice_h] / 1000, self.metodo))
        self.balance = energias(self.r)
        self.piso_m, postura = PISOS[self.indice_piso]
        self.segmentos = segmentos(self.r, self.piso_m, piernas_rad=postura)
        self.elongacion = self.r.elongacion_m
        self.contacto = primer_contacto(self.segmentos)
        self.fin = self.contacto.tiempo_s if self.contacto else self.r.t[-1]
        self.piso.setZ(self.piso_m)
        self.paso_texto.setText(f"{self.r.paso_s * 1000:g} ms")
        for metodo, control in self.botones_metodo.items():
            control["frameColor"] = ACTIVO if metodo == self.metodo else TARJETA
        self.leyenda.setText(f"{self.metodo.upper()}: cian  /  exacta: ámbar")
        self._configurar_graficas()
        self._dibujar()

    def _alternar(self):
        if self.t >= self.fin:
            self.t = 0.0
        self.play = not self.play
        if self.play:
            self._restablecer_camara()
        self._dibujar()

    def _inicio(self):
        self.t = 0.0
        self.play = False
        self._dibujar()

    def _paso(self):
        self.play = False
        tiempos = self.r.tiempos_pasos_s
        i = np.searchsorted(tiempos, self.t, side="right")
        self.t = min(self.fin, float(tiempos[min(i, len(tiempos) - 1)]))
        self._dibujar()

    def _saltar_tensado(self):
        self.play = False
        self.t = min(self.fin, self.r.t_tensado_s)
        self.vista = "cuerpo"
        self._restablecer_camara()
        self._dibujar()

    def _metodo(self, metodo):
        if metodo != self.metodo:
            self.metodo = metodo
            self.t, self.play = 0.0, False
            self._calcular()

    def _cambiar_h(self, delta):
        self.indice_h = int(np.clip(self.indice_h + delta, 0, len(PASOS_MS) - 1))
        self._inicio()
        self._calcular()

    def _alternar_piso(self):
        self.indice_piso = (self.indice_piso + 1) % len(PISOS)
        self._inicio()
        self._calcular()

    def _cambiar_vista(self):
        vistas = ("seguir", "cuerpo", "torre")
        self.vista = vistas[(vistas.index(self.vista) + 1) % len(vistas)]
        self._restablecer_camara()
        self._dibujar()

    def _cuadro(self, tarea):
        ahora = perf_counter()
        dt = min(0.05, ahora - self.ultimo_cuadro)
        self.ultimo_cuadro = ahora
        if self.play:
            self.t = min(self.fin, avanzar_reloj(self.t, dt, self.r.t_tensado_s))
            self.play = self.t < self.fin
            self._dibujar()
        elif self.arrastre_x is not None:
            x = self._raton_en_visor()
            if x is None:
                self._soltar_arrastre()
            else:
                self.giro += 3 * (x - self.arrastre_x)
                self.arrastre_x = x
                self._aplicar_camara()
        return tarea.cont

    def _dibujar(self):
        r = self.r
        t = self.t
        altura = float(np.interp(t, r.t, r.altura_torso_m))
        altura_ref = float(np.interp(t, self.referencia.t, self.referencia.altura_torso_m))
        tau = t - r.t_tensado_s
        frenado = tau >= 0
        self.cuerpo.setZ(altura)
        self.fantasma.setPos(0, 0.31, altura_ref)
        inclinacion(self.cuerpo, -36 * float(np.clip(-tau / 1.3, 0, 1)))
        for nombre, nodo, signo in (("Cabeza", self.cabeza, 1), ("Piernas", self.piernas, -1)):
            perfil = self.segmentos[nombre]
            giro = np.interp(t, perfil.t, perfil.angulo_rad)
            inclinacion(nodo, signo * float(np.degrees(giro)))
        for i, brazo in enumerate(self.brazos):
            brazo.setR((-1)**i * (10*np.sin(4*t) if not frenado else min(45, 1600*tau)))
        self.seda.node().removeAllChildren()
        inicio = max(0.0, r.t_tensado_s - 0.52)
        if t >= inicio:
            fraccion = float(np.clip((t - inicio) / (r.t_tensado_s - inicio), 0, 1))
            extremo = self.origen_seda + (self.cuerpo.getPos() - self.origen_seda) * fraccion
            linea(self.seda, [self.origen_seda, extremo], CIAN if frenado else BLANCO, 3 if frenado else 1)
        self._aplicar_camara()
        self._medir(t, tau, altura, altura_ref)

    def _medir(self, t, tau, altura, altura_ref):
        r = self.r
        valor = lambda serie: float(np.interp(t, r.t, serie))
        frenado = tau >= 0
        fuerza = r.k_n_m * valor(self.elongacion) if frenado else 0.0
        potencia = fuerza * valor(r.v_m_s)
        self.guia.node().removeAllChildren()
        if fuerza > 0:
            escala = min(1, fuerza / r.f_max_n)
            punta = altura + 0.19 + 0.58 * escala
            linea(self.guia, [(0.15, -0.22, altura), (0.15, -0.22, punta)], AMBAR, 3)
            linea(self.guia, [(0.09, -0.22, punta - 0.10), (0.15, -0.22, punta),
                              (0.21, -0.22, punta - 0.10)], AMBAR, 3)
            nivel = r.escena.h_ancla_m - r.escena.caida_m
            linea(self.guia, [(1.05, 0, altura), (1.05, 0, nivel)], CIAN)
        self.grafica_v.actualizar(tau * 1000 if self.zoom_grafica else t)
        self.grafica_f.actualizar(tau * 1000)
        error = abs(altura - altura_ref)
        porcentaje = f"{100 * error / abs(altura_ref):.3g} %" if altura_ref else "n/a"
        v = valor(r.v_m_s)
        sentido = "sube" if v < -0.0005 else "baja" if v > 0.0005 else ""
        rapidez_texto = f"{v:+.3f}" if round(v, 3) else "0.000"
        potencia_mw = potencia / 1e6
        potencia_texto = f"{potencia_mw:+.3f}" if round(potencia_mw, 3) else "0.000"
        valores = (f"{altura:.3f} m", f"{rapidez_texto} m/s  {sentido}".strip(),
                   f"{valor(r.a_m_s2) / r.escena.gravedad_m_s2:+.2f} g",
                   f"{fuerza / 1000:.2f} kN", f"{valor(self.elongacion):.4f} m",
                   f"{valor(self.balance['seda_j']) / 1000:.3f} kJ",
                   f"{potencia_texto} MW", f"{error:.3g} m  ({porcentaje})")
        for lectura, dato in zip(self.lecturas, valores, strict=True):
            lectura.setText(dato)
        self.b_reproducir["text"] = "Pausar" if self.play else "Reproducir"
        self.b_vista["text"] = f"Vista: {self.vista.capitalize()}"
        self.b_restablecer["state"] = "disabled" if self.play else "normal"
        fase = "Frenado" if frenado else "Caída"
        modo = "En curso" if self.play else "En pausa"
        self.ayuda_camara.setText("" if self.play else "Arrastra para girar / rueda para acercar")
        self.fase_texto.setText(f"{fase}  |  t = {t:.4f} s  |  {modo}")
        if self.ver_edo:
            self._mostrar_edo(frenado)
        mensaje = ("Caso base" if self.piso_m == 0 else
                   f"Piso +{self.piso_m:.2f} m  |  postura de piernas {PISOS[self.indice_piso][1]:g} rad")
        if frenado:
            carga = valor(r.a_m_s2) + r.escena.gravedad_m_s2
            cuerpo = r.escena.cuerpo
            cabeza, piernas = (float(np.interp(t, p.t, p.energia_cinetica_j))
                               for p in self.segmentos.values())
            mensaje += (f"\nCuello {cuerpo.masa_cabeza_kg * cuerpo.r_cuello_m * carga:.0f} Nm"
                        f"   |   cadera {cuerpo.masa_piernas_kg * cuerpo.r_cadera_m * carga:.0f} Nm"
                        f"\nCabeza {cabeza:.0f} J   |   piernas {piernas:.0f} J  (cinética)")
        if self.contacto and t >= self.fin:
            mensaje += (f"\nPrimer contacto: {self.contacto.segmento.lower()}"
                        f"   |   {self.contacto.energia_incidente_j:.0f} J incidentes")
        self.estado.setText(mensaje)


    def _mostrar_edo(self, frenado):
        r = self.r
        if frenado:
            formula = "x' = v     v' = g - (k/m)x"
        else:
            formula = "y' = v     v' = g - [rho Cd A / (2m)] v^2"
        self.ecuacion.setText(f"{formula}\nMisma EDO para Euler y RK4.\n"
                              "v positiva hacia abajo; a del panel hacia arriba.")
        if self.play:
            self.etapas.setText("Pausa para inspeccionar las pendientes del paso.")
            return
        tiempos = r.tiempos_pasos_s
        i = np.searchsorted(tiempos, self.t, side="right") - 1
        if self.t >= self.fin or i >= len(tiempos) - 1:
            self.etapas.setText("Fin de la corrida.")
            return
        pendientes = inspeccionar_paso(r, i)
        filas = [f"Paso nominal desde t = {tiempos[i]:.6f} s",
                 "Pendiente       posición (m/s)    velocidad (m/s^2)"]
        filas.extend(f"k{j}                      {v:+.4g}                  {a:+.4g}"
                     for j, (v, a) in enumerate(pendientes, 1))
        if r.metodo == "euler":
            filas.append("Incremento = h k1")
        else:
            filas.append("Incremento = h (k1 + 2 k2 + 2 k3 + k4) / 6")
        if tiempos[i + 1] == r.t_tensado_s:
            filas.append("La frontera de tensado se localiza por interpolación.")
        self.etapas.setText("\n".join(filas))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--medir", type=int, default=0, metavar="CUADROS")
    parser.add_argument("--captura")
    parser.add_argument("--ventana", action="store_true", help="mide con ventana visible")
    args = parser.parse_args()
    loadPrcFileData("laboratorio", (
        f"win-size {ANCHO} {ALTO}\n"
        "window-title Gwen Stacy - Simulador 3D\n"
        "x-wm-class gwen-stacy-3d\nx-wm-class-name gwen-stacy-3d\n"
        "sync-video false\naudio-library-name null"
    ))
    medir_o_capturar = bool(args.medir or args.captura)
    fuera = medir_o_capturar and not args.ventana
    if fuera:
        loadPrcFileData("medición", "load-display p3headlessgl")
    app = Visor(fuera)
    try:
        if not medir_o_capturar:
            app.run()
            return
        app.vista = "cuerpo"
        app.t = app.r.t_tensado_s + 0.012
        app._dibujar()
        for _ in range(4):
            app.graphicsEngine.renderFrame()
        tiempos = []
        if args.medir:
            for i in range(args.medir):
                inicio = perf_counter()
                app.t = app.r.t_tensado_s - 0.05 + 0.075 * i / args.medir
                app._dibujar()
                app.eventMgr.doEvents()
                app.graphicsEngine.renderFrame()
                app.graphicsEngine.syncFrame()
                tiempos.append(perf_counter() - inicio)
            ancho, alto = app.win.getXSize(), app.win.getYSize()
            print(f"{app.win.getGsg().getDriverRenderer()}  |  {ancho}×{alto}  |  "
                  f"{1 / np.mean(tiempos):.1f} FPS  |  p95 {1000 * np.percentile(tiempos, 95):.1f} ms")
        if args.captura:
            app.t = app.r.t_tensado_s + 0.015
            app._dibujar()
            app.graphicsEngine.renderFrame()
            app.win.saveScreenshot(Filename.fromOsSpecific(args.captura))
    finally:
        app.destroy()


if __name__ == "__main__":
    main()
