"""I31-I33: app de escritorio Tk con escena 3D y transporte.

La app precalcula la simulación una vez y solo interpola en el bucle de dibujo.
Los controles Entry/Scale se sincronizan con guardas de reentrada.
"""

from __future__ import annotations

import time
import tkinter as tk
from tkinter import messagebox, ttk

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from simulador.estocastico import simular_ensemble
from visual.animacion import Reproductor, VELOCIDADES
from visual.escena3d import construir_escena
from visual.parametros_vista import ParametrosVista


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Gwen Stacy — simulación numérica")
        self.root.geometry("1280x820")
        self.modelo = ParametrosVista()
        self.resultado = self.modelo.simular()
        self.rep = Reproductor(self.resultado, fps=20)
        self._guard = False
        self._dirty = False
        self._after_id = None
        self._ultimo_t = time.perf_counter()
        self.controles: dict[str, dict] = {}
        self._construir()
        self._actualizar_todo()
        self._tick()

    # ------------------------------------------------------------------ UI
    def _construir(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        panel = ttk.Frame(self.root, padding=8)
        panel.grid(row=0, column=0, sticky="ns")
        ttk.Label(panel, text="Parámetros", font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")

        fila = 1
        self._control(panel, fila, "masa_kg", "Masa (kg)", 30, 100, "{:.1f}"); fila += 1
        self._control(panel, fila, "estiramiento_m", "Estiramiento (m)", 0.01, 1.59, "{:.3f}"); fila += 1
        self._control(panel, fila, "k_n_m", "Rigidez k (N/m)", 10, 1e6, "{:.0f}"); fila += 1
        self._control(panel, fila, "longitud_m", "Longitud L (m)", 10, 100, "{:.1f}"); fila += 1
        self._control_semilla(panel, fila); fila += 1

        self.var_aire = tk.BooleanVar(value=self.modelo.aire)
        self.var_tumbling = tk.BooleanVar(value=self.modelo.tumbling)
        ttk.Checkbutton(panel, text="Aire", variable=self.var_aire, command=self._cambio_flags).grid(row=fila, column=0, sticky="w"); fila += 1
        ttk.Checkbutton(panel, text="Tumbling", variable=self.var_tumbling, command=self._cambio_flags).grid(row=fila, column=0, sticky="w"); fila += 1

        self.mode_label = ttk.Label(panel, text="modo: calibración (x)", foreground="#1f4e79")
        self.mode_label.grid(row=fila, column=0, columnspan=3, sticky="w", pady=(6, 2)); fila += 1
        self.estado_label = ttk.Label(panel, text="Listo", foreground="#1e8449")
        self.estado_label.grid(row=fila, column=0, columnspan=3, sticky="w"); fila += 1

        botones = ttk.Frame(panel)
        botones.grid(row=fila, column=0, columnspan=3, pady=6, sticky="ew")
        ttk.Button(botones, text="Ejecutar", command=self.ejecutar).grid(row=0, column=0, padx=2)
        ttk.Button(botones, text="Pausa", command=self.pausar).grid(row=0, column=1, padx=2)
        ttk.Button(botones, text="Reanudar", command=self.reanudar).grid(row=0, column=2, padx=2)
        ttk.Button(botones, text="Reiniciar", command=self.reiniciar).grid(row=0, column=3, padx=2)
        ttk.Button(botones, text="Restablecer", command=self.restablecer).grid(row=1, column=0, padx=2, pady=2)
        ttk.Button(botones, text="Nueva semilla", command=self.nueva_semilla).grid(row=1, column=1, padx=2, pady=2)
        ttk.Button(botones, text="Monte Carlo", command=self.monte_carlo).grid(row=1, column=2, padx=2, pady=2)
        fila += 1

        ttk.Label(panel, text="Velocidad").grid(row=fila, column=0, sticky="w"); fila += 1
        self.velocidad = tk.StringVar(value="1x")
        combo = ttk.Combobox(panel, textvariable=self.velocidad, values=[f"{v:g}x" for v in VELOCIDADES], state="readonly", width=10)
        combo.grid(row=fila, column=0, sticky="w")
        combo.bind("<<ComboboxSelected>>", self._cambio_velocidad); fila += 1

        ttk.Label(panel, text="Tiempo").grid(row=fila, column=0, sticky="w"); fila += 1
        self.tiempo = tk.DoubleVar(value=0.0)
        self.tiempo_scale = ttk.Scale(panel, from_=0, to=self.rep.t_total, variable=self.tiempo, command=self._seek)
        self.tiempo_scale.grid(row=fila, column=0, columnspan=3, sticky="ew"); fila += 1

        self.hud = {}
        for clave, etiqueta in [
            ("t", "t"),
            ("altura", "altura"),
            ("v", "v"),
            ("a", "a"),
            ("F", "F"),
            ("E", "E"),
            ("P", "P"),
            ("HIC", "HIC"),
        ]:
            ttk.Label(panel, text=f"{etiqueta}:", width=7).grid(row=fila, column=0, sticky="w")
            lbl = ttk.Label(panel, text="—")
            lbl.grid(row=fila, column=1, columnspan=2, sticky="w")
            self.hud[clave] = lbl
            fila += 1
        self.hud["semaforo"] = ttk.Label(panel, text="—", font=("TkDefaultFont", 10, "bold"))
        self.hud["semaforo"].grid(row=fila, column=0, columnspan=3, sticky="w")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        self.fig3d = plt.Figure(figsize=(7, 6), dpi=100)
        self.ax3d = self.fig3d.add_subplot(111, projection="3d")
        self.escena = construir_escena(self.fig3d, self.ax3d)
        self.canvas3d = FigureCanvasTkAgg(self.fig3d, master=self.notebook)
        self.canvas3d.get_tk_widget().pack(fill="both", expand=True)
        self.notebook.add(self.canvas3d.get_tk_widget(), text="3D")

        self.figplots = plt.Figure(figsize=(7, 6), dpi=100)
        self.ax_a = self.figplots.add_subplot(311)
        self.ax_v = self.figplots.add_subplot(312, sharex=self.ax_a)
        self.ax_f = self.figplots.add_subplot(313, sharex=self.ax_a)
        self.canvasplots = FigureCanvasTkAgg(self.figplots, master=self.notebook)
        self.canvasplots.get_tk_widget().pack(fill="both", expand=True)
        self.notebook.add(self.canvasplots.get_tk_widget(), text="Gráficas")
        self._lineas_t = []
        for ax, dato, color, etiqueta in [
            (self.ax_a, np.abs(self.resultado.a_m_s2) / 9.81, "#c0392b", "a (g)"),
            (self.ax_v, self.resultado.v_m_s, "#1f4e79", "v (m/s)"),
            (self.ax_f, self.resultado.fuerza_n / 1e3, "#1e8449", "F (kN)"),
        ]:
            ax.plot(self.resultado.t, dato, color=color, lw=1.2)
            ax.axvline(self.resultado.t_tensado_s, color="#d35400", ls=":", lw=1)
            linea = ax.axvline(0, color="black", lw=1)
            self._lineas_t.append(linea)
            ax.set_ylabel(etiqueta)
            ax.grid(alpha=0.3)
        self.ax_f.set_xlabel("t (s)")
        self.figplots.tight_layout()

        self.frame_mc = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_mc, text="Monte Carlo")
        self.mc_text = tk.Text(self.frame_mc, height=8, width=60)
        self.mc_text.pack(fill="x", padx=4, pady=4)
        self.mc_canvas = None

    def _control(self, parent, fila, clave, etiqueta, desde, hasta, fmt):
        ttk.Label(parent, text=etiqueta).grid(row=fila, column=0, sticky="w")
        valor = self.modelo.valores_ui()[clave]
        var_e = tk.StringVar(value=fmt.format(valor))
        var_s = tk.DoubleVar(value=float(valor))
        entry = ttk.Entry(parent, textvariable=var_e, width=11)
        entry.grid(row=fila, column=1, padx=2)
        escala = ttk.Scale(parent, from_=desde, to=hasta, variable=var_s, command=lambda v, c=clave: self._desde_scale(c, v))
        escala.grid(row=fila, column=2, sticky="ew")
        self.controles[clave] = {"entry": entry, "var_e": var_e, "var_s": var_s, "scale": escala, "fmt": fmt}
        var_e.trace_add("write", lambda *a, c=clave: self._desde_entry(c))

    def _control_semilla(self, parent, fila):
        ttk.Label(parent, text="Semilla").grid(row=fila, column=0, sticky="w")
        var = tk.StringVar(value=str(self.modelo.semilla))
        entry = ttk.Entry(parent, textvariable=var, width=11)
        entry.grid(row=fila, column=1, padx=2)
        self.controles["semilla"] = {"entry": entry, "var_e": var, "var_s": None, "scale": None, "fmt": "{}"}
        var.trace_add("write", lambda *a: self._desde_entry("semilla"))

    def _desde_entry(self, clave):
        if self._guard:
            return
        c = self.controles[clave]
        texto = c["var_e"].get().strip()
        try:
            valor = int(texto) if clave == "semilla" else float(texto)
            self.modelo.set_valor(clave, valor)
        except (ValueError, TypeError):
            c["entry"].configure(foreground="#c0392b")
            self.estado_label.configure(text="Valor inválido", foreground="#c0392b")
            return
        c["entry"].configure(foreground="black")
        self._guard = True
        try:
            if c["var_s"] is not None:
                c["var_s"].set(float(valor))
            self._marcar_cambio()
        finally:
            self._guard = False

    def _desde_scale(self, clave, valor):
        if self._guard:
            return
        c = self.controles[clave]
        valor = float(valor)
        try:
            self.modelo.set_valor(clave, valor)
        except ValueError:
            return
        self._guard = True
        try:
            c["var_e"].set(c["fmt"].format(valor))
            self._marcar_cambio()
        finally:
            self._guard = False

    def set_valor(self, clave, valor):
        """API para tests: actualiza Entry y Scale a la vez."""
        self.modelo.set_valor(clave, valor)
        c = self.controles[clave]
        self._guard = True
        try:
            c["var_e"].set(c["fmt"].format(valor))
            if c["var_s"] is not None:
                c["var_s"].set(float(valor))
        finally:
            self._guard = False
        self._marcar_cambio()

    def _marcar_cambio(self):
        self._dirty = True
        self.estado_label.configure(text="Parámetros cambiados: pulsa Ejecutar", foreground="#b7950b")
        self.mode_label.configure(text=f"modo: {self.modelo.modo}")

    def _cambio_flags(self):
        self.modelo.aire = bool(self.var_aire.get())
        self.modelo.tumbling = bool(self.var_tumbling.get())
        self._marcar_cambio()

    def _cambio_velocidad(self, _event=None):
        texto = self.velocidad.get().replace("x", "")
        self.rep.set_velocidad(float(texto))

    def _seek(self, _valor=None):
        if self._guard:
            return
        self.rep.seek(float(self.tiempo.get()))
        self._actualizar_todo()

    # -------------------------------------------------------------- acciones
    def ejecutar(self):
        try:
            resultado = self.modelo.simular()
        except Exception as exc:
            messagebox.showerror("Error de simulación", str(exc))
            return
        self.resultado = resultado
        self.rep = Reproductor(resultado, fps=20)
        self.tiempo_scale.configure(to=self.rep.t_total)
        self._reconstruir_graficas()
        self._dirty = False
        self.estado_label.configure(text="Simulación lista", foreground="#1e8449")
        self.rep.play()
        self._actualizar_todo()

    def pausar(self):
        self.rep.pause()

    def reanudar(self):
        if self.rep.t >= self.rep.t_total:
            self.rep.reiniciar()
        self.rep.play()
        self._actualizar_todo()

    def reiniciar(self):
        self.rep.reiniciar()
        self._actualizar_todo()

    def restablecer(self):
        self.modelo.restablecer()
        self.var_aire.set(self.modelo.aire)
        self.var_tumbling.set(self.modelo.tumbling)
        for clave, c in self.controles.items():
            valor = self.modelo.valores_ui()[clave]
            c["var_e"].set(c["fmt"].format(valor))
            if c["var_s"] is not None:
                c["var_s"].set(float(valor))
        self._dirty = False
        self.ejecutar()

    def nueva_semilla(self):
        self.modelo.semilla = int(np.random.default_rng().integers(0, 2**31))
        self.set_valor("semilla", self.modelo.semilla)

    def monte_carlo(self):
        try:
            e = simular_ensemble(n=500, semilla=self.modelo.semilla)
        except Exception as exc:
            messagebox.showerror("Monte Carlo", str(exc))
            return
        self.mc_text.delete("1.0", tk.END)
        st = e.estadisticas("a_max_g")
        self.mc_text.insert(
            tk.END,
            f"n=500  semilla={self.modelo.semilla}\n"
            f"a_max p5/p50/p95 = {st['p5']:.1f} / {st['p50']:.1f} / {st['p95']:.1f} g\n"
            f"HIC p50 = {np.percentile(e.hic, 50):.0f}\n"
            f"fracción HIC>700 = {e.fraccion('hic', 700.0):.1%}\n",
        )
        if self.mc_canvas is not None:
            self.mc_canvas.get_tk_widget().destroy()
        fig = plt.Figure(figsize=(6, 3), dpi=100)
        ax = fig.add_subplot(111)
        ax.hist(e.a_max_g, bins=30, color="#c0392b", alpha=0.75)
        ax.axvline(6, color="black", ls="--", label="6 g")
        ax.set_xlabel("a_max (g)")
        ax.legend()
        self.mc_canvas = FigureCanvasTkAgg(fig, master=self.frame_mc)
        self.mc_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.mc_canvas.draw()
        self.notebook.select(self.frame_mc)

    # ---------------------------------------------------------------- dibujo
    def _reconstruir_graficas(self):
        self.ax_a.clear(); self.ax_v.clear(); self.ax_f.clear()
        self._lineas_t = []
        for ax, dato, color, etiqueta in [
            (self.ax_a, np.abs(self.resultado.a_m_s2) / 9.81, "#c0392b", "a (g)"),
            (self.ax_v, self.resultado.v_m_s, "#1f4e79", "v (m/s)"),
            (self.ax_f, self.resultado.fuerza_n / 1e3, "#1e8449", "F (kN)"),
        ]:
            ax.plot(self.resultado.t, dato, color=color, lw=1.2)
            ax.axvline(self.resultado.t_tensado_s, color="#d35400", ls=":", lw=1)
            linea = ax.axvline(0, color="black", lw=1)
            self._lineas_t.append(linea)
            ax.set_ylabel(etiqueta)
            ax.grid(alpha=0.3)
        self.ax_f.set_xlabel("t (s)")
        self.figplots.tight_layout()
        self.canvasplots.draw_idle()

    def _actualizar_escena(self):
        est = self.rep.estado()
        self.escena.actualizar(est.__dict__, self.rep.trayectoria_hasta())
        self.canvas3d.draw_idle()

    def _actualizar_hud(self):
        est = self.rep.estado()
        self.hud["t"].configure(text=f"{est.t:.3f} s")
        self.hud["altura"].configure(text=f"{est.altura_torso:.2f} m")
        self.hud["v"].configure(text=f"{est.v:.2f} m/s")
        self.hud["a"].configure(text=f"{est.a_g:.1f} g")
        self.hud["F"].configure(text=f"{est.fuerza/1e3:.1f} kN")
        self.hud["E"].configure(text=f"{self.resultado.energia_j/1e3:.2f} kJ")
        self.hud["P"].configure(text=f"{est.potencia/1e6:.3f} MW")
        self.hud["HIC"].configure(text=f"{est.hic:.0f}")
        color = "#1e8449" if est.semaforo == "supervivencia" else "#c0392b"
        self.hud["semaforo"].configure(text=f"● {est.semaforo}", foreground=color)

    def _actualizar_graficas(self):
        t = self.rep.t
        for linea in self._lineas_t:
            linea.set_xdata([t, t])
        self.canvasplots.draw_idle()

    def _actualizar_todo(self):
        self._guard = True
        try:
            self.tiempo.set(self.rep.t)
        finally:
            self._guard = False
        self._actualizar_escena()
        self._actualizar_hud()
        self._actualizar_graficas()

    def _tick(self):
        ahora = time.perf_counter()
        dt = min(0.1, ahora - self._ultimo_t)
        self._ultimo_t = ahora
        if self.rep.reproduciendo:
            self.rep.avanzar(dt)
            self._actualizar_todo()
        self._after_id = self.root.after(50, self._tick)

    def cerrar(self):
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
        self.root.destroy()


def main():
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.cerrar)
    root.mainloop()


if __name__ == "__main__":
    main()
