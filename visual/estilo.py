"""Paleta y tema visual del proyecto (modo oscuro pizarra + cian)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import matplotlib

PALETA = {
    "fondo": "#0b0f14",
    "superficie": "#121821",
    "tarjeta": "#1a2230",
    "borde": "#263241",
    "texto": "#e6edf3",
    "suave": "#8b98a9",
    "cian": "#4cc9f0",
    "cian_claro": "#7adcf5",
    "alerta": "#ff5c5c",
    "exito": "#3ddc97",
    "seda": "#f5c542",
    "naranja": "#ff9f43",
    "morado": "#b388ff",
    "azul": "#5aa9ff",
}

CUERPO = {
    "piel": "#e3b49a",
    "pelo": "#e8c15a",
    "abrigo": "#d7e0ea",
    "abrigo_sombra": "#b8c4d1",
    "pantalon": "#3a4b5f",
    "zapato": "#161d27",
    "seda": PALETA["seda"],
    "sombra": "#000000",
}

FUENTE = "Inter"


def configurar_matplotlib() -> None:
    """rcParams oscuros para todas las figuras y el MP4."""
    matplotlib.rcParams.update(
        {
            "figure.facecolor": PALETA["fondo"],
            "savefig.facecolor": PALETA["fondo"],
            "axes.facecolor": PALETA["superficie"],
            "axes.edgecolor": PALETA["borde"],
            "axes.labelcolor": PALETA["texto"],
            "axes.titlecolor": PALETA["texto"],
            "text.color": PALETA["texto"],
            "xtick.color": PALETA["suave"],
            "ytick.color": PALETA["suave"],
            "grid.color": PALETA["borde"],
            "grid.alpha": 0.35,
            "legend.facecolor": PALETA["tarjeta"],
            "legend.edgecolor": PALETA["borde"],
            "legend.labelcolor": PALETA["texto"],
            "figure.titlesize": 12,
            "font.size": 9,
        }
    )


def aplicar_estilo_3d(fig, ax) -> None:
    """Fondo oscuro, paneles transparentes y ejes legibles en 3D."""
    fig.patch.set_facecolor(PALETA["fondo"])
    ax.set_facecolor(PALETA["fondo"])
    for eje in (ax.xaxis, ax.yaxis, ax.zaxis):
        eje.set_pane_color((0.04, 0.06, 0.09, 0.0))
        eje.line.set_color(PALETA["borde"])
        eje.label.set_color(PALETA["suave"])
    ax.tick_params(colors=PALETA["suave"], labelsize=8)
    ax.grid(True, color=PALETA["borde"], alpha=0.25)


def aplicar_tema_tk(root: tk.Tk) -> None:
    """Tema ttk plano y oscuro, sin depender del tema nativo."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    root.configure(bg=PALETA["fondo"])
    style.configure(
        ".",
        background=PALETA["fondo"],
        foreground=PALETA["texto"],
        fieldbackground=PALETA["superficie"],
        bordercolor=PALETA["borde"],
        focuscolor=PALETA["cian"],
        font=(FUENTE, 9),
    )
    style.configure("TFrame", background=PALETA["fondo"])
    style.configure("Card.TFrame", background=PALETA["tarjeta"])
    style.configure("TLabel", background=PALETA["fondo"], foreground=PALETA["texto"])
    style.configure("Card.TLabel", background=PALETA["tarjeta"], foreground=PALETA["texto"])
    style.configure("Muted.TLabel", foreground=PALETA["suave"])
    style.configure("CardMuted.TLabel", background=PALETA["tarjeta"], foreground=PALETA["suave"])
    style.configure("Title.TLabel", font=(FUENTE, 20, "bold"), foreground=PALETA["texto"])
    style.configure("Subtitle.TLabel", font=(FUENTE, 10), foreground=PALETA["suave"])
    style.configure("Section.TLabel", font=(FUENTE, 9, "bold"), foreground=PALETA["cian"])
    style.configure("Metric.TLabel", font=(FUENTE, 12, "bold"), foreground=PALETA["texto"])
    style.configure("Accent.TLabel", foreground=PALETA["cian"])
    style.configure("Alert.TLabel", foreground=PALETA["alerta"])
    style.configure("Ok.TLabel", foreground=PALETA["exito"])
    style.configure("TButton", background=PALETA["tarjeta"], foreground=PALETA["texto"], padding=(10, 6), borderwidth=0)
    style.map("TButton", background=[("active", PALETA["superficie"])], foreground=[("disabled", PALETA["suave"])])
    style.configure("Accent.TButton", background=PALETA["cian"], foreground="#06121a", padding=(10, 6), borderwidth=0)
    style.map("Accent.TButton", background=[("active", PALETA["cian_claro"])])
    style.configure("TEntry", fieldbackground=PALETA["superficie"], foreground=PALETA["texto"], insertcolor=PALETA["texto"], bordercolor=PALETA["borde"], padding=4)
    style.configure("TScale", background=PALETA["fondo"], troughcolor=PALETA["superficie"], bordercolor=PALETA["borde"], sliderlength=14)
    style.configure("TCheckbutton", background=PALETA["fondo"], foreground=PALETA["texto"])
    style.map("TCheckbutton", background=[("active", PALETA["fondo"])])
    style.configure("TNotebook", background=PALETA["fondo"], borderwidth=0)
    style.configure("TNotebook.Tab", background=PALETA["tarjeta"], foreground=PALETA["suave"], padding=(14, 7), borderwidth=0)
    style.map("TNotebook.Tab", background=[("selected", PALETA["superficie"])], foreground=[("selected", PALETA["cian"])])
    style.configure("TCombobox", fieldbackground=PALETA["superficie"], background=PALETA["tarjeta"], foreground=PALETA["texto"], arrowcolor=PALETA["suave"])
    style.map("TCombobox", fieldbackground=[("readonly", PALETA["superficie"])], foreground=[("readonly", PALETA["texto"])])
    style.configure("TLabelframe", background=PALETA["fondo"], foreground=PALETA["texto"], bordercolor=PALETA["borde"])
    style.configure("TLabelframe.Label", background=PALETA["fondo"], foreground=PALETA["cian"])
    style.configure("Vertical.TScrollbar", background=PALETA["tarjeta"], troughcolor=PALETA["fondo"], bordercolor=PALETA["borde"], arrowcolor=PALETA["suave"])


class ToolTip:
    """Tooltip simple para explicar cada variable sin recargar el panel."""

    def __init__(self, widget, texto: str, retardo: int = 350):
        self.widget = widget
        self.texto = texto
        self.retardo = retardo
        self._after = None
        self._ventana = None
        widget.bind("<Enter>", self._programar, add="+")
        widget.bind("<Leave>", self._ocultar, add="+")
        widget.bind("<ButtonPress>", self._ocultar, add="+")

    def _programar(self, _event=None):
        self._cancelar()
        self._after = self.widget.after(self.retardo, self._mostrar)

    def _cancelar(self):
        if self._after is not None:
            self.widget.after_cancel(self._after)
            self._after = None

    def _mostrar(self):
        if self._ventana is not None:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._ventana = tk.Toplevel(self.widget)
        self._ventana.wm_overrideredirect(True)
        self._ventana.configure(bg=PALETA["borde"])
        etiqueta = tk.Label(
            self._ventana,
            text=self.texto,
            justify="left",
            bg=PALETA["tarjeta"],
            fg=PALETA["texto"],
            padx=8,
            pady=5,
            wraplength=280,
            font=(FUENTE, 8),
        )
        etiqueta.pack(padx=1, pady=1)
        self._ventana.wm_geometry(f"+{x}+{y}")

    def _ocultar(self, _event=None):
        self._cancelar()
        if self._ventana is not None:
            self._ventana.destroy()
            self._ventana = None
