"""Ventana de análisis de la corrida abierta desde el visor Panda3D."""
from __future__ import annotations

import argparse
import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.ticker import EngFormatter

from simulador.mediciones import energias, primer_contacto, segmentos
from simulador.modelo import simular
from simulador.parametros import Computo, Escena


def series_corrida(r, fin):
    """Muestras hasta el final observable, incluyendo el instante de contacto."""
    t = np.r_[r.t[r.t < fin], fin]
    valor = lambda serie: np.interp(t, r.t, serie)
    elongacion = valor(r.elongacion_m)
    velocidad = valor(r.v_m_s)
    tension = r.k_n_m * elongacion
    balance = energias(r)
    return {
        "t": t, "Altura (m)": valor(r.altura_torso_m), "Velocidad (m/s)": velocidad,
        "Tensión (kN)": tension / 1000,
        "Aceleración (g)": valor(r.a_m_s2) / r.escena.gravedad_m_s2,
        "Elongación (m)": elongacion, "Energía en seda (kJ)": tension * elongacion / 2000,
        "Potencia de la seda (MW)": tension * velocidad / 1e6,
        "Energía cinética (kJ)": valor(balance["cinetica_j"]) / 1000,
        "Pérdida por arrastre (kJ)": valor(balance["aire_j"]) / 1000,
    }


class Laboratorio:
    def __init__(self, root, resultado, referencia, contacto, instante):
        self.r = resultado
        self.fin = float(contacto.tiempo_s if contacto else resultado.t[-1])
        self.datos = series_corrida(resultado, self.fin)
        self.ref = series_corrida(referencia, min(self.fin, referencia.t[-1]) if contacto else referencia.t[-1])
        self.instante = float(np.clip(instante, 0, self.fin))
        self.eventos = [("Tensado", resultado.t_tensado_s),
                        ("Primera detención", resultado.t_tensado_s + resultado.t_pico_s)]
        if contacto:
            self.eventos.append((f"Contacto: {contacto.segmento.lower()}", self.fin))
        self.eventos = [(nombre, t) for nombre, t in self.eventos if t <= self.fin]

        root.title("Gwen Stacy - Gráficas y tablas")
        root.geometry("1190x820")
        root.minsize(820, 610)
        cabecera = ttk.Frame(root, padding=(12, 9))
        cabecera.pack(fill="x")
        etiqueta = f"{resultado.metodo.upper()}  |  h = {1000 * resultado.paso_s:g} ms"
        if contacto:
            etiqueta += f"  |  {contacto.energia_incidente_j / 1000:.3f} kJ incidentes"
        ttk.Label(cabecera, text=etiqueta).pack(side="left")
        self.pestanas = ttk.Notebook(root)
        self.pestanas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        graficas, tablas = ttk.Frame(self.pestanas), ttk.Frame(self.pestanas)
        self.pestanas.add(graficas, text="Gráficas")
        self.pestanas.add(tablas, text="Tablas")

        controles = ttk.Frame(graficas, padding=(8, 5))
        controles.pack(fill="x")
        ttk.Button(controles, text="Caída completa", command=self._completa).pack(side="left")
        ttk.Button(controles, text="Frenado", command=self._frenado).pack(side="left", padx=4)
        ttk.Label(controles, text="Tercera gráfica").pack(side="left", padx=(16, 5))
        self.variable = ttk.Combobox(controles, state="readonly", width=25,
                                     values=tuple(self.datos)[4:] + ("Altura (m)",))
        self.variable.set("Energía en seda (kJ)")
        self.variable.bind("<<ComboboxSelected>>", self._cambiar_variable)
        self.variable.pack(side="left")
        ttk.Label(controles, text="Rueda: zoom  |  Arrastrar con Desplazar  |  Clic: cursor").pack(
            side="right", padx=5)

        fig = Figure(figsize=(10, 6), layout="constrained")
        self.ejes = fig.subplots(3, 1, sharex=True)
        self.canvas = FigureCanvasTkAgg(fig, master=graficas)
        self.barra = NavigationToolbar2Tk(self.canvas, graficas, pack_toolbar=False)
        self.barra.pack(fill="x")
        self.lectura_cursor = ttk.Label(graficas, padding=(8, 4))
        self.lectura_cursor.pack(fill="x", side="bottom")
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.mpl_connect("scroll_event", self._zoom)
        self.canvas.mpl_connect("button_press_event", self._seleccionar)
        self._dibujar_eje(self.ejes[0], "Velocidad (m/s)")
        self._dibujar_eje(self.ejes[1], "Tensión (kN)")
        self._cambiar_variable()
        self._completa()
        self._cursor(self.instante)
        self.barra.update()
        self.barra.push_current()

        resumen = ttk.Frame(tablas, padding=(8, 7))
        resumen.pack(fill="x")
        for nombre, t in self.eventos:
            ttk.Label(resumen, text=f"{nombre}   {t:.6f} s").pack(side="left", padx=(0, 15))
        ttk.Button(resumen, text="Mostrar intervalo visible", command=self._filtrar).pack(side="right")
        ttk.Button(resumen, text="Todas las muestras", command=self._llenar_tabla).pack(side="right", padx=6)
        cuerpo = ttk.Frame(tablas)
        cuerpo.pack(fill="both", expand=True)
        columnas = ("Tiempo (s)", "Desde tensado (ms)", *tuple(self.datos)[1:])
        self.tabla = ttk.Treeview(cuerpo, columns=columnas, show="headings")
        self.tabla.grid(row=0, column=0, sticky="nsew")
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.rowconfigure(0, weight=1)
        vertical = ttk.Scrollbar(cuerpo, orient="vertical", command=self.tabla.yview)
        horizontal = ttk.Scrollbar(cuerpo, orient="horizontal", command=self.tabla.xview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.tabla.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        for columna in columnas:
            self.tabla.heading(columna, text=columna)
            self.tabla.column(columna, width=max(105, 7 * len(columna) + 12), stretch=False, anchor="e")
        self.tabla.tag_configure("par", background="#edf4f7", foreground="#141e2a")
        self.tabla.bind("<Double-1>", self._fila_a_cursor)
        self._llenar_tabla()

    def _dibujar_eje(self, eje, nombre):
        eje.plot(self.ref["t"], self.ref[nombre], "--", color="#b36b21", label="Analítica")
        eje.plot(self.datos["t"], self.datos[nombre], color="#057499", lw=1.7, label=self.r.metodo.upper())
        for evento, tiempo in self.eventos:
            eje.axvline(tiempo, color="#687785", ls=":", lw=1, label=evento)
        eje._cursor_corrida = eje.axvline(self.instante, color="#141e2a", lw=1)
        eje.set_ylabel(nombre)
        eje.grid(alpha=0.2)
        if eje is self.ejes[0]:
            eje.legend(loc="upper left", ncols=3, fontsize=8)

    def _cambiar_variable(self, _evento=None):
        eje = self.ejes[2]
        limites = self.ejes[0].get_xlim()
        eje.clear()
        self._dibujar_eje(eje, self.variable.get())
        eje.set_xlabel("Tiempo físico (s)")
        eje.xaxis.set_major_formatter(EngFormatter(unit="s", places=3, useOffset=True))
        self.ejes[0].set_xlim(*limites)
        self.canvas.draw_idle()

    def _completa(self):
        self.ejes[0].set_xlim(0, max(self.fin, self.ref["t"][-1]))
        self.canvas.draw_idle()

    def _frenado(self):
        inicio = self.r.t_tensado_s
        self.ejes[0].set_xlim(max(0, inicio - 0.004), self.fin)
        self.canvas.draw_idle()

    def _zoom(self, evento):
        if evento.inaxes not in self.ejes or evento.xdata is None or evento.step == 0:
            return
        a, b = evento.inaxes.get_xlim()
        factor = 0.78 if evento.step > 0 else 1 / 0.78
        if (b - a) * factor < 1e-6:
            return
        t = evento.xdata
        self.barra.push_current()
        self.ejes[0].set_xlim(t + (a - t) * factor, t + (b - t) * factor)
        self.barra.push_current()
        self.canvas.draw_idle()

    def _seleccionar(self, evento):
        if (evento.button == 1 and evento.inaxes in self.ejes
                and evento.xdata is not None and not self.barra.mode):
            self._cursor(evento.xdata)

    def _cursor(self, tiempo):
        self.instante = float(np.clip(tiempo, 0, self.fin))
        for eje in self.ejes:
            eje._cursor_corrida.set_xdata([self.instante] * 2)
        v = np.interp(self.instante, self.datos["t"], self.datos["Velocidad (m/s)"])
        f = np.interp(self.instante, self.datos["t"], self.datos["Tensión (kN)"])
        tau = 1000 * (self.instante - self.r.t_tensado_s)
        self.lectura_cursor.configure(
            text=f"t = {self.instante:.6f} s  |  Desde el tensado {tau:+.3f} ms  |  "
                 f"Velocidad {v:.4f} m/s  |  Tensión {f:.4f} kN"
        )
        self.canvas.draw_idle()

    def _llenar_tabla(self, limites=None):
        self.tabla.delete(*self.tabla.get_children())
        t = self.datos["t"]
        muestras = np.arange(len(t)) if limites is None else np.flatnonzero((t >= limites[0]) & (t <= limites[1]))
        columnas = tuple(self.datos.values())[1:]
        for i in muestras:
            fila = (f"{t[i]:.6f}", f"{1000 * (t[i] - self.r.t_tensado_s):.3f}",
                    *(f"{col[i]:.6g}" for col in columnas))
            self.tabla.insert("", "end", iid=str(i), values=fila, tags=("par",) if i % 2 == 0 else ())

    def _filtrar(self):
        self._llenar_tabla(self.ejes[0].get_xlim())

    def _fila_a_cursor(self, evento):
        fila = self.tabla.identify_row(evento.y)
        if fila:
            self._cursor(self.datos["t"][int(fila)])
            self.pestanas.select(0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metodo", choices=("euler", "rk4"), default="rk4")
    parser.add_argument("--paso", type=float, default=0.001)
    parser.add_argument("--piso", type=float, default=0)
    parser.add_argument("--postura", type=float, default=0)
    parser.add_argument("--instante", type=float, default=0)
    args = parser.parse_args()
    escena = Escena.pelicula()
    resultado = simular(escena, computo=Computo(args.paso, args.metodo))
    referencia = simular(escena)
    contacto = primer_contacto(segmentos(resultado, args.piso, piernas_rad=args.postura))
    root = tk.Tk()
    Laboratorio(root, resultado, referencia, contacto, args.instante)
    root.mainloop()


if __name__ == "__main__":
    main()
