"""App de escritorio: escena 3D, parámetros explicados y tema oscuro."""

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
from visual.estilo import FUENTE, PALETA, ToolTip, aplicar_estilo_3d, aplicar_tema_tk, configurar_matplotlib
from visual.parametros_vista import ParametrosVista


class MarcoDesplazable(tk.Frame):
    """Contenedor vertical con scroll para el sidebar."""

    def __init__(self, master, **kwargs):
        super().__init__(master, bg=PALETA["fondo"], **kwargs)
        self.canvas = tk.Canvas(self, bg=PALETA["fondo"], highlightthickness=0, bd=0)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.interior = tk.Frame(self.canvas, bg=PALETA["fondo"])
        self._window = self.canvas.create_window((0, 0), window=self.interior, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")
        self.interior.bind("<Configure>", self._al_cambiar)
        self.canvas.bind("<Configure>", self._al_redimensionar)
        self.canvas.bind_all("<MouseWheel>", self._rueda)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-2, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(2, "units"))

    def _al_cambiar(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _al_redimensionar(self, event):
        self.canvas.itemconfigure(self._window, width=event.width)

    def _rueda(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Gwen Stacy — caída, energía y latigazo")
        self.root.geometry("1380x960")
        self.root.minsize(1160, 820)
        aplicar_tema_tk(root)
        configurar_matplotlib()

        self.modelo = ParametrosVista()
        self.resultado = self.modelo.simular()
        self.rep = Reproductor(self.resultado, fps=60)
        self._guard = False
        self._dirty = False
        self._after_id = None
        self._ultimo_t = time.perf_counter()
        self.controles: dict[str, dict] = {}
        self._lineas_t = []
        self.vista = tk.StringVar(value="Seguir")

        self._construir()
        self._actualizar_derivados()
        self._actualizar_todo()
        self._tick()

    # --------------------------------------------------------------- estructura
    def _construir(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._cabecera()
        cuerpo = tk.Frame(self.root, bg=PALETA["fondo"])
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 6))
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        self.sidebar = MarcoDesplazable(cuerpo, width=330)
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        self.sidebar.interior.configure(width=320)
        self._panel_parametros(self.sidebar.interior)

        self.notebook = ttk.Notebook(cuerpo)
        self.notebook.grid(row=0, column=1, sticky="nsew")
        self._pestana_3d()
        self._pestana_graficas()
        self._pestana_modelo()
        self._pestana_monte_carlo()
        self.notebook.bind("<<NotebookTabChanged>>", self._al_cambiar_pestana)

        self._pie()

    def _al_cambiar_pestana(self, _event=None):
        try:
            tab = self.notebook.index("current")
        except Exception:
            tab = 0
        if tab == 0:
            self._actualizar_escena()
        elif tab == 1:
            self._actualizar_graficas()

    def _cabecera(self):
        barra = tk.Frame(self.root, bg=PALETA["fondo"], height=74)
        barra.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))
        barra.columnconfigure(1, weight=1)
        tk.Label(
            barra,
            text="GWEN STACY",
            bg=PALETA["fondo"],
            fg=PALETA["texto"],
            font=(FUENTE, 20, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            barra,
            text="Caída, energía y latigazo · Métodos Numéricos",
            bg=PALETA["fondo"],
            fg=PALETA["suave"],
            font=(FUENTE, 10),
            anchor="w",
        ).grid(row=1, column=0, sticky="w")
        self.badge_escenario = tk.Label(
            barra,
            text="ESCENARIO BASE · CON AIRE",
            bg=PALETA["tarjeta"],
            fg=PALETA["cian"],
            font=(FUENTE, 8, "bold"),
            padx=10,
            pady=5,
        )
        self.badge_escenario.grid(row=0, column=1, sticky="e", padx=6)
        self.mode_label = tk.Label(
            barra,
            text="modo: calibración (x)",
            bg=PALETA["fondo"],
            fg=PALETA["suave"],
            font=(FUENTE, 8),
        )
        self.mode_label.grid(row=1, column=1, sticky="e", padx=6)

    # --------------------------------------------------------------- sidebar
    def _seccion(self, parent, texto: str):
        tk.Label(
            parent,
            text=texto.upper(),
            bg=PALETA["fondo"],
            fg=PALETA["cian"],
            font=(FUENTE, 8, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(12, 4))

    def _panel_parametros(self, parent):
        self._seccion(parent, "Cuerpo")
        self._control(parent, "masa_kg", "Masa", "m", "kg", 30, 100, "{:.1f}", "Masa total del cuerpo. Más masa aumenta la energía y la fuerza necesaria para detenerlo.")
        self._control(parent, "cd_area_m2", "Área de arrastre", "Cd·A", "m²", 0.05, 1.2, "{:.2f}", "Área de arrastre efectiva. Depende de la postura: de cabeza ~0.1 m², plana ~0.6 m².")

        self._seccion(parent, "Telaraña")
        self._control(parent, "estiramiento_m", "Estiramiento", "x", "m", 0.01, 1.59, "{:.3f}", "Cuánto se estira la seda desde el tensado hasta detener el torso. Si supera 1.60 m, el torso toca el suelo.")
        self._control(parent, "k_n_m", "Rigidez", "k", "N/m", 10, 500000, "{:.0f}", "Resistencia de la seda: fuerza por metro de estiramiento. Se relaciona con el material como k = E·A/L.")
        self._control(parent, "longitud_m", "Longitud tensa", "L", "m", 10, 100, "{:.1f}", "Longitud de la seda cuando se tensa. Define la altura del tirón y el espacio libre hasta el suelo.")

        self._seccion(parent, "Ambiente")
        self.var_aire = tk.BooleanVar(value=self.modelo.aire)
        self.var_tumbling = tk.BooleanVar(value=self.modelo.tumbling)
        self._check(parent, "Aire (arrastre cuadrático)", self.var_aire, "Activa la resistencia del aire. Sin aire, la velocidad al tensarse sube de 24.9 a 28.7 m/s.")
        self._check(parent, "Tumbling (orientación variable)", self.var_tumbling, "Hace variar el área de arrastre con la orientación. La semilla decide el muestreo.")

        self._seccion(parent, "Simulación")
        fila = tk.Frame(parent, bg=PALETA["fondo"])
        fila.pack(fill="x", pady=2)
        tk.Label(fila, text="Semilla", bg=PALETA["fondo"], fg=PALETA["texto"], font=(FUENTE, 9)).pack(side="left")
        self.var_semilla = tk.StringVar(value=str(self.modelo.semilla))
        self.entry_semilla = ttk.Entry(fila, textvariable=self.var_semilla, width=11)
        self.entry_semilla.pack(side="left", padx=6)
        ToolTip(self.entry_semilla, "Fija el muestreo aleatorio del tumbling y de Monte Carlo. Misma semilla, misma simulación.")
        self.var_semilla.trace_add("write", lambda *a: self._desde_entry("semilla"))
        self.controles["semilla"] = {"entry": self.entry_semilla, "var_e": self.var_semilla, "var_s": None, "scale": None, "fmt": "{}"}
        ttk.Button(fila, text="Nueva", command=self.nueva_semilla).pack(side="left")

        self._tarjeta_derivados(parent)
        self._tarjeta_diagnostico(parent)

    def _control(self, parent, clave, nombre, simbolo, unidad, desde, hasta, fmt, ayuda):
        marco = tk.Frame(parent, bg=PALETA["tarjeta"], padx=8, pady=6)
        marco.pack(fill="x", pady=3)
        marco.columnconfigure(0, weight=1)
        titulo = tk.Label(
            marco,
            text=f"{nombre}  {simbolo}  ({unidad})",
            bg=PALETA["tarjeta"],
            fg=PALETA["texto"],
            font=(FUENTE, 9),
            anchor="w",
        )
        titulo.grid(row=0, column=0, sticky="w")
        ayuda_lbl = tk.Label(marco, text="?", bg=PALETA["tarjeta"], fg=PALETA["cian"], font=(FUENTE, 9, "bold"), cursor="hand2")
        ayuda_lbl.grid(row=0, column=1, sticky="e")
        ToolTip(ayuda_lbl, ayuda)
        ToolTip(titulo, ayuda)

        valor = self.modelo.valores_ui()[clave]
        var_e = tk.StringVar(value=fmt.format(valor))
        var_s = tk.DoubleVar(value=float(valor))
        entry = ttk.Entry(marco, textvariable=var_e, width=10)
        entry.grid(row=1, column=0, sticky="w", padx=(0, 6), pady=(3, 0))
        escala = ttk.Scale(marco, from_=desde, to=hasta, variable=var_s, command=lambda v, c=clave: self._desde_scale(c, v))
        escala.grid(row=1, column=1, sticky="ew", pady=(3, 0))
        marco.columnconfigure(1, weight=1)
        self.controles[clave] = {"entry": entry, "var_e": var_e, "var_s": var_s, "scale": escala, "fmt": fmt, "titulo": titulo}
        var_e.trace_add("write", lambda *a, c=clave: self._desde_entry(c))

    def _check(self, parent, texto, variable, ayuda):
        cb = ttk.Checkbutton(parent, text=texto, variable=variable, command=self._cambio_flags)
        cb.pack(anchor="w", pady=2)
        ToolTip(cb, ayuda)

    def _tarjeta_derivados(self, parent):
        self._seccion(parent, "Valores derivados")
        marco = tk.Frame(parent, bg=PALETA["tarjeta"], padx=10, pady=8)
        marco.pack(fill="x", pady=3)
        self.derivados = {}
        claves = [
            ("v0", "Velocidad al tensarse"),
            ("k", "Rigidez k"),
            ("x", "Estiramiento x"),
            ("a", "Aceleración pico"),
            ("F", "Fuerza pico"),
            ("E", "Energía absorbida"),
            ("seda", "Módulo implícito"),
            ("eps", "Deformación"),
            ("M", "Momento cervical"),
            ("HIC", "HIC"),
        ]
        for i, (clave, etiqueta) in enumerate(claves):
            tk.Label(marco, text=etiqueta, bg=PALETA["tarjeta"], fg=PALETA["suave"], font=(FUENTE, 8), anchor="w").grid(row=i, column=0, sticky="w", pady=1)
            lbl = tk.Label(marco, text="—", bg=PALETA["tarjeta"], fg=PALETA["texto"], font=(FUENTE, 9, "bold"), anchor="e")
            lbl.grid(row=i, column=1, sticky="e", pady=1)
            self.derivados[clave] = lbl
        self.badge_k = tk.Label(marco, text="", bg=PALETA["tarjeta"], fg=PALETA["cian"], font=(FUENTE, 8))
        self.badge_k.grid(row=len(claves), column=0, columnspan=2, sticky="w", pady=(4, 0))

    def _tarjeta_diagnostico(self, parent):
        self._seccion(parent, "Diagnóstico")
        marco = tk.Frame(parent, bg=PALETA["tarjeta"], padx=10, pady=10)
        marco.pack(fill="x", pady=3)
        self.veredicto = tk.Label(marco, text="—", bg=PALETA["tarjeta"], fg=PALETA["alerta"], font=(FUENTE, 13, "bold"), anchor="w")
        self.veredicto.pack(fill="x")
        self.diagnostico = tk.Label(
            marco,
            text="",
            bg=PALETA["tarjeta"],
            fg=PALETA["suave"],
            font=(FUENTE, 8),
            justify="left",
            wraplength=285,
            anchor="w",
        )
        self.diagnostico.pack(fill="x", pady=(4, 0))

    # ------------------------------------------------------------- pestañas
    def _pestana_3d(self):
        marco = tk.Frame(self.notebook, bg=PALETA["fondo"])
        self.notebook.add(marco, text="3D")
        barra = tk.Frame(marco, bg=PALETA["fondo"])
        barra.pack(fill="x", padx=8, pady=4)
        tk.Label(barra, text="Vista", bg=PALETA["fondo"], fg=PALETA["suave"], font=(FUENTE, 9)).pack(side="left")
        self.selector_vista = ttk.Combobox(barra, values=["Seguir", "Cuerpo", "Torre"], state="readonly", width=10)
        self.selector_vista.set("Seguir")
        self.selector_vista.pack(side="left", padx=6)
        self.selector_vista.bind("<<ComboboxSelected>>", self._cambio_vista)
        ttk.Button(barra, text="Centrar", command=self.centrar_vista).pack(side="left", padx=4)
        tk.Label(barra, text="arrastra para orbitar · rueda para zoom", bg=PALETA["fondo"], fg=PALETA["suave"], font=(FUENTE, 8)).pack(side="right")

        self.fig3d = plt.Figure(figsize=(7, 6.5), dpi=100)
        self.fig3d.patch.set_facecolor(PALETA["fondo"])
        self.ax3d = self.fig3d.add_subplot(111, projection="3d")
        self.escena = construir_escena(self.fig3d, self.ax3d, self.resultado)
        self.canvas3d = FigureCanvasTkAgg(self.fig3d, master=marco)
        self.canvas3d.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=4)

        overlay = tk.Frame(
            self.canvas3d.get_tk_widget(),
            bg=PALETA["tarjeta"],
            padx=10,
            pady=8,
            highlightbackground=PALETA["borde"],
            highlightthickness=1,
        )
        overlay.place(relx=0.985, rely=0.025, anchor="ne")
        tk.Label(overlay, text="RESUMEN", bg=PALETA["tarjeta"], fg=PALETA["cian"], font=(FUENTE, 7, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        self.overlay = {}
        for i, (clave, etiqueta) in enumerate(
            [("a", "a_pico"), ("E", "energía"), ("seda", "E seda"), ("veredicto", "veredicto")],
            start=1,
        ):
            tk.Label(overlay, text=etiqueta, bg=PALETA["tarjeta"], fg=PALETA["suave"], font=(FUENTE, 8)).grid(row=i, column=0, sticky="w", padx=(0, 10))
            lbl = tk.Label(overlay, text="—", bg=PALETA["tarjeta"], fg=PALETA["texto"], font=(FUENTE, 9, "bold"))
            lbl.grid(row=i, column=1, sticky="e")
            self.overlay[clave] = lbl

    def _pestana_graficas(self):
        marco = tk.Frame(self.notebook, bg=PALETA["fondo"])
        self.notebook.add(marco, text="Gráficas")
        self.figplots = plt.Figure(figsize=(7, 6.5), dpi=100)
        self.figplots.patch.set_facecolor(PALETA["fondo"])
        self.ax_a = self.figplots.add_subplot(311)
        self.ax_v = self.figplots.add_subplot(312, sharex=self.ax_a)
        self.ax_f = self.figplots.add_subplot(313, sharex=self.ax_a)
        self.canvasplots = FigureCanvasTkAgg(self.figplots, master=marco)
        self.canvasplots.get_tk_widget().pack(fill="both", expand=True)
        self._reconstruir_graficas()

    def _pestana_modelo(self):
        marco = tk.Frame(self.notebook, bg=PALETA["fondo"])
        self.notebook.add(marco, text="Modelo")
        texto = tk.Text(
            marco,
            bg=PALETA["superficie"],
            fg=PALETA["texto"],
            insertbackground=PALETA["texto"],
            relief="flat",
            padx=16,
            pady=12,
            wrap="word",
            font=("DejaVu Sans Mono", 9),
        )
        scroll = ttk.Scrollbar(marco, orient="vertical", command=texto.yview)
        texto.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        texto.pack(side="left", fill="both", expand=True)
        texto.insert(
            "1.0",
            """ECUACIONES DEL MODELO

Caída con arrastre
    m dv/dt = m g − ½ ρ Cd A v²
    v(t) = v_t tanh(g t / v_t)
    y(t) = (v_t²/g) ln cosh(g t / v_t)

Telaraña elástica
    m ẍ = m g − k x
    x(t) = (g/ω²)(1 − cos ωt) + (v₀/ω) sin ωt
    a_pico = sqrt(g² + (k/m) v₀²)
    t_pico = (π − atan(v₀ω/g)) / ω
    k = m(v₀² + 2 g x) / x²

Cuerpo articulado
    M_cuello = m_cabeza · r_cuello · (a_t + g)
    M_cadera = m_piernas · r_cadera · (a_t + g)

GLOSARIO

m          masa total del cuerpo (kg)
Cd·A       área de arrastre efectiva (m²)
L          longitud tensa de la seda (m)
x          estiramiento máximo de la seda (m)
k          rigidez de la seda (N/m); k = E·A/L
E          módulo de Young implícito de la seda (Pa)
ε          deformación de la seda, x/L
v₀         velocidad del torso al tensarse (m/s)
a_pico     aceleración máxima de frenado (g)
F_pico     fuerza máxima de la seda (kN)
P          potencia instantánea, P(t) = k x(t) ẋ(t)
HIC        índice de daño craneal equivalente, ventana ≤ 36 ms

SUPUESTOS

· El cuerpo es atrapado en el torso; no se modela un golpe de la cabeza
  o las piernas contra el suelo.
· La seda es un resorte lineal; la seda real es viscoelástica.
· El modelo es 1D en la caída y cuasiestático en el articulado.
· El HIC se usa como índice comparativo, no como diagnóstico clínico.

LECTURA RÁPIDA

1. La energía no es el problema: la potencia y la aceleración sí.
2. Para 6 g la seda debería estirarse 12.6 m, pero solo hay 1.6 m.
3. Para no tocar el suelo haría falta E ≥ 21.3 GPa y aun así ~40 g.
4. El latigazo cervical es el mecanismo final.
""",
        )
        texto.configure(state="disabled")

    def _pestana_monte_carlo(self):
        marco = tk.Frame(self.notebook, bg=PALETA["fondo"])
        self.notebook.add(marco, text="Monte Carlo")
        self.mc_text = tk.Text(
            marco,
            height=7,
            bg=PALETA["superficie"],
            fg=PALETA["texto"],
            relief="flat",
            padx=10,
            pady=8,
            font=("DejaVu Sans Mono", 9),
        )
        self.mc_text.pack(fill="x", padx=6, pady=6)
        self.mc_text.insert("1.0", "Pulsa «Monte Carlo» para lanzar 500 simulaciones con la semilla actual.\n")
        self.mc_text.configure(state="disabled")
        self.mc_canvas = None

    # ------------------------------------------------------------------ pie
    def _pie(self):
        pie = tk.Frame(self.root, bg=PALETA["superficie"], padx=12, pady=8)
        pie.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))
        pie.columnconfigure(8, weight=1)
        ttk.Button(pie, text="▶  Ejecutar", style="Accent.TButton", command=self.ejecutar).grid(row=0, column=0, padx=2)
        ttk.Button(pie, text="⏸  Pausa", command=self.pausar).grid(row=0, column=1, padx=2)
        ttk.Button(pie, text="▶▶ Reanudar", command=self.reanudar).grid(row=0, column=2, padx=2)
        ttk.Button(pie, text="↺ Reiniciar", command=self.reiniciar).grid(row=0, column=3, padx=2)
        ttk.Button(pie, text="Restablecer", command=self.restablecer).grid(row=0, column=4, padx=2)
        ttk.Button(pie, text="Monte Carlo", command=self.monte_carlo).grid(row=0, column=5, padx=2)

        self.var_velocidad = tk.StringVar(value="1x")
        combo = ttk.Combobox(pie, textvariable=self.var_velocidad, values=[f"{v:g}x" for v in VELOCIDADES], state="readonly", width=5)
        combo.grid(row=0, column=6, sticky="w", padx=(10, 4))
        combo.bind("<<ComboboxSelected>>", self._cambio_velocidad)

        self.tiempo = tk.DoubleVar(value=0.0)
        self.tiempo_scale = ttk.Scale(pie, from_=0, to=self.rep.t_total, variable=self.tiempo, command=self._seek)
        self.tiempo_scale.grid(row=0, column=7, sticky="ew", padx=6)
        pie.columnconfigure(7, weight=1)
        self.lbl_tiempo = tk.Label(pie, text="0.000 s", bg=PALETA["superficie"], fg=PALETA["suave"], font=(FUENTE, 9))
        self.lbl_tiempo.grid(row=0, column=8, padx=4)

        chips = tk.Frame(pie, bg=PALETA["superficie"])
        chips.grid(row=1, column=0, columnspan=9, sticky="ew", pady=(7, 0))
        self.hud = {}
        definiciones = [
            ("t", "t", "s"),
            ("y", "Altura y", "m"),
            ("v", "Velocidad v", "m/s"),
            ("a", "Aceleración a", "g"),
            ("F", "Fuerza F", "kN"),
            ("E", "Energía E", "kJ"),
            ("P", "Potencia P", "MW"),
            ("HIC", "HIC", ""),
        ]
        for i, (clave, etiqueta, unidad) in enumerate(definiciones):
            marco = tk.Frame(chips, bg=PALETA["tarjeta"], padx=7, pady=3)
            marco.grid(row=0, column=i, padx=2, sticky="w")
            tk.Label(marco, text=etiqueta, bg=PALETA["tarjeta"], fg=PALETA["suave"], font=(FUENTE, 7)).pack(anchor="w")
            lbl = tk.Label(marco, text="—", bg=PALETA["tarjeta"], fg=PALETA["texto"], font=(FUENTE, 9, "bold"))
            lbl.pack(anchor="w")
            self.hud[clave] = (lbl, unidad)
        self.hud_semaforo = tk.Label(chips, text="—", bg=PALETA["superficie"], fg=PALETA["alerta"], font=(FUENTE, 10, "bold"))
        self.hud_semaforo.grid(row=0, column=len(definiciones), padx=8)
        self.estado_label = tk.Label(chips, text="Listo", bg=PALETA["superficie"], fg=PALETA["exito"], font=(FUENTE, 8), anchor="e")
        self.estado_label.grid(row=0, column=len(definiciones) + 1, sticky="e", padx=6)
        chips.columnconfigure(len(definiciones) + 1, weight=1)

    # ------------------------------------------------------------- controles
    def _desde_entry(self, clave):
        if self._guard:
            return
        c = self.controles[clave]
        texto = c["var_e"].get().strip()
        try:
            valor = int(texto) if clave == "semilla" else float(texto)
            self.modelo.set_valor(clave, valor)
        except (ValueError, TypeError):
            c["entry"].configure(foreground=PALETA["alerta"])
            self.estado_label.configure(text="Valor inválido", fg=PALETA["alerta"])
            return
        c["entry"].configure(foreground=PALETA["texto"])
        self._guard = True
        try:
            if c["var_s"] is not None:
                c["var_s"].set(float(valor))
        finally:
            self._guard = False
        self._marcar_cambio()

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
        finally:
            self._guard = False
        self._marcar_cambio()

    def set_valor(self, clave, valor):
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
        self.estado_label.configure(text="Parámetros cambiados: pulsa Ejecutar", fg=PALETA["seda"])
        self.mode_label.configure(text=f"modo: {'calibración (x)' if self.modelo.modo == 'calibracion' else 'material (k)'}")
        if self.modelo.modo == "calibracion":
            self._sincronizar_k()

    def _sincronizar_k(self):
        try:
            k = self.modelo.k_efectiva()
        except Exception:
            return
        c = self.controles.get("k_n_m")
        if c is None:
            return
        self._guard = True
        try:
            c["var_e"].set(c["fmt"].format(k))
            c["var_s"].set(float(k))
        finally:
            self._guard = False

    def _cambio_flags(self):
        self.modelo.aire = bool(self.var_aire.get())
        self.modelo.tumbling = bool(self.var_tumbling.get())
        self._marcar_cambio()

    def _cambio_velocidad(self, _event=None):
        self.rep.set_velocidad(float(self.var_velocidad.get().replace("x", "")))

    def _cambio_vista(self, _event=None):
        modo = self.selector_vista.get().lower()
        self.vista.set(self.selector_vista.get())
        self.escena.aplicar_vista(modo, self.rep.estado().altura_torso)
        self.canvas3d.draw_idle()

    def centrar_vista(self):
        self.escena.aplicar_vista(self.selector_vista.get().lower(), self.rep.estado().altura_torso)
        self.canvas3d.draw_idle()

    def _seek(self, _valor=None):
        if self._guard:
            return
        self.rep.seek(float(self.tiempo.get()))
        self._actualizar_todo()

    # --------------------------------------------------------------- acciones
    def ejecutar(self):
        try:
            resultado = self.modelo.simular()
        except Exception as exc:
            messagebox.showerror("Error de simulación", str(exc))
            return
        self.resultado = resultado
        self.rep = Reproductor(resultado, fps=60)
        self.tiempo_scale.configure(to=self.rep.t_total)
        self._reconstruir_escena()
        self._reconstruir_graficas()
        self._dirty = False
        self.estado_label.configure(text="Simulación lista", fg=PALETA["exito"])
        self.rep.play()
        self._actualizar_derivados()
        self._actualizar_todo()

    def pausar(self):
        self.rep.pause()
        self.estado_label.configure(text="Pausa", fg=PALETA["suave"])

    def reanudar(self):
        if self.rep.t >= self.rep.t_total:
            self.rep.reiniciar()
        self.rep.play()
        self.estado_label.configure(text="Reproduciendo", fg=PALETA["exito"])

    def reiniciar(self):
        self.rep.reiniciar()
        self._actualizar_todo()

    def restablecer(self):
        self.modelo.restablecer()
        self.var_aire.set(self.modelo.aire)
        self.var_tumbling.set(self.modelo.tumbling)
        self.var_semilla.set(str(self.modelo.semilla))
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
        self.mc_text.configure(state="normal")
        self.mc_text.delete("1.0", tk.END)
        st = e.estadisticas("a_max_g")
        self.mc_text.insert(
            tk.END,
            f"n=500  semilla={self.modelo.semilla}\n"
            f"a_max p5/p50/p95 = {st['p5']:.1f} / {st['p50']:.1f} / {st['p95']:.1f} g\n"
            f"HIC p50 = {np.percentile(e.hic, 50):.0f}\n"
            f"fracción HIC>700 = {e.fraccion('hic', 700.0):.1%}\n",
        )
        self.mc_text.configure(state="disabled")
        if self.mc_canvas is not None:
            self.mc_canvas.get_tk_widget().destroy()
        fig = plt.Figure(figsize=(6, 3.2), dpi=100)
        fig.patch.set_facecolor(PALETA["fondo"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(PALETA["superficie"])
        ax.hist(e.a_max_g, bins=30, color=PALETA["alerta"], alpha=0.8, edgecolor=PALETA["fondo"])
        ax.axvline(6, color=PALETA["texto"], ls="--", label="6 g")
        ax.set_xlabel("a_max (g)", color=PALETA["texto"])
        ax.set_ylabel("frecuencia", color=PALETA["texto"])
        ax.tick_params(colors=PALETA["suave"])
        ax.grid(alpha=0.2, color=PALETA["borde"])
        ax.legend(facecolor=PALETA["tarjeta"], edgecolor=PALETA["borde"], labelcolor=PALETA["texto"])
        self.mc_canvas = FigureCanvasTkAgg(fig, master=self.mc_text.master)
        self.mc_canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
        self.mc_canvas.draw()
        self.notebook.select(self.mc_text.master)

    # ---------------------------------------------------------------- dibujo
    def _reconstruir_escena(self):
        self.ax3d.clear()
        aplicar_estilo_3d(self.fig3d, self.ax3d)
        self.escena = construir_escena(self.fig3d, self.ax3d, self.resultado)
        self.escena.aplicar_vista(self.selector_vista.get().lower(), self.rep.estado().altura_torso)
        self.canvas3d.draw_idle()

    def _reconstruir_graficas(self):
        self.ax_a.clear(); self.ax_v.clear(); self.ax_f.clear()
        self._lineas_t = []
        datos = [
            (self.ax_a, np.abs(self.resultado.a_m_s2) / self.resultado.escena.gravedad_m_s2, PALETA["alerta"], "Aceleración a (g)"),
            (self.ax_v, self.resultado.v_m_s, PALETA["azul"], "Velocidad v (m/s)"),
            (self.ax_f, self.resultado.fuerza_n / 1e3, PALETA["exito"], "Fuerza F (kN)"),
        ]
        for ax, dato, color, etiqueta in datos:
            ax.set_facecolor(PALETA["superficie"])
            ax.plot(self.resultado.t, dato, color=color, lw=1.5)
            ax.axvline(self.resultado.t_tensado_s, color=PALETA["seda"], ls=":", lw=1.2)
            linea = ax.axvline(0, color=PALETA["texto"], lw=1)
            self._lineas_t.append(linea)
            ax.set_ylabel(etiqueta, color=PALETA["texto"])
            ax.tick_params(colors=PALETA["suave"], labelsize=8)
            ax.grid(alpha=0.25, color=PALETA["borde"])
            for spine in ax.spines.values():
                spine.set_color(PALETA["borde"])
        self.ax_f.set_xlabel("t (s)", color=PALETA["texto"])
        self.figplots.tight_layout()
        self.canvasplots.draw_idle()

    def _actualizar_escena(self):
        est = self.rep.estado()
        self.escena.actualizar(est.__dict__, self.rep.trayectoria_hasta())
        self.canvas3d.draw_idle()

    def _actualizar_hud(self):
        est = self.rep.estado()
        valores = {
            "t": f"{est.t:.3f}",
            "y": f"{est.altura_torso:.2f}",
            "v": f"{est.v:.2f}",
            "a": f"{est.a_g:.1f}",
            "F": f"{est.fuerza/1e3:.1f}",
            "E": f"{self.resultado.energia_j/1e3:.2f}",
            "P": f"{est.potencia/1e6:.3f}",
            "HIC": f"{est.hic:.0f}",
        }
        for clave, valor in valores.items():
            lbl, unidad = self.hud[clave]
            lbl.configure(text=f"{valor} {unidad}".strip())
        color = PALETA["exito"] if est.semaforo == "supervivencia" else PALETA["alerta"]
        self.hud_semaforo.configure(text=f"● {est.semaforo.upper()}", fg=color)
        self.lbl_tiempo.configure(text=f"{est.t:.3f} s")
        self.estado_label.configure(
            text=f"{'Frenado' if est.fase else 'Caída'} · a={est.a_g:.1f} g",
            fg=PALETA["seda"] if est.fase else PALETA["suave"],
        )

    def _actualizar_derivados(self):
        r = self.resultado
        m = r.momentos()
        self.derivados["v0"].configure(text=f"{r.v0_m_s:.2f} m/s")
        self.derivados["k"].configure(text=f"{r.k_n_m:,.0f} N/m")
        self.derivados["x"].configure(text=f"{r.x_max_m:.3f} m")
        self.derivados["a"].configure(text=f"{r.a_max_g:.1f} g")
        self.derivados["F"].configure(text=f"{r.f_max_n/1e3:.1f} kN")
        self.derivados["E"].configure(text=f"{r.energia_j/1e3:.2f} kJ")
        self.derivados["seda"].configure(text=f"{r.modulo_seda_pa/1e9:.1f} GPa")
        self.derivados["eps"].configure(text=f"{r.deformacion*100:.2f} %")
        self.derivados["M"].configure(text=f"{m.cuello_kn_m:.2f} kN·m")
        self.derivados["HIC"].configure(text=f"{r.hic:.0f}")
        if self.modelo.modo == "calibracion":
            self.badge_k.configure(text="k calculado a partir de x y v₀")
        else:
            self.badge_k.configure(text="x calculado a partir de k y v₀")
        letal = r.a_max_g > 6.0
        self.veredicto.configure(
            text="LETAL" if letal else "SUPERVIVENCIA",
            fg=PALETA["alerta"] if letal else PALETA["exito"],
        )
        self.overlay["a"].configure(text=f"{r.a_max_g:.1f} g", fg=PALETA["alerta"] if letal else PALETA["exito"])
        self.overlay["E"].configure(text=f"{r.energia_j/1e3:.1f} kJ")
        self.overlay["seda"].configure(text=f"{r.modulo_seda_pa/1e9:.0f} GPa")
        self.overlay["veredicto"].configure(text="LETAL" if letal else "OK", fg=PALETA["alerta"] if letal else PALETA["exito"])
        self.diagnostico.configure(
            text=(
                f"{r.a_max_g:.1f} g > 6 g. La seda se estira {r.x_max_m:.2f} m "
                f"y solo hay {r.escena.espacio_libre_m:.2f} m hasta el suelo.\n"
                f"Módulo implícito {r.modulo_seda_pa/1e9:.1f} GPa "
                f"(seda real: 1–10 GPa)."
            )
        )

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

        try:
            tab = self.notebook.index("current")
        except Exception:
            tab = 0

        if tab == 0:
            self._actualizar_escena()
        elif tab == 1:
            self._actualizar_graficas()

        self._actualizar_hud()
        self.mode_label.configure(text=f"modo: {'calibración (x)' if self.modelo.modo == 'calibracion' else 'material (k)'}")

    def _tick(self):
        ahora = time.perf_counter()
        dt = min(0.1, ahora - self._ultimo_t)
        self._ultimo_t = ahora
        if self.rep.reproduciendo:
            self.rep.avanzar(dt)
            self._actualizar_todo()
        t_proc = time.perf_counter() - ahora
        ms_espera = max(2, int((1.0 / 60.0 - t_proc) * 1000))
        self._after_id = self.root.after(ms_espera, self._tick)

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
