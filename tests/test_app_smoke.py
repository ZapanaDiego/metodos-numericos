"""Smoke test de la app Tk (se salta sin DISPLAY)."""

import os

import pytest

pytestmark = [pytest.mark.gui, pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="sin DISPLAY")]


def test_app_arranca_y_sincroniza():
    tk = pytest.importorskip("tkinter")
    from visual.app_tkinter import App

    root = tk.Tk()
    root.withdraw()
    try:
        app = App(root)
        app.set_valor("masa_kg", 62.5)
        assert float(app.controles["masa_kg"]["var_e"].get()) == pytest.approx(62.5)
        assert float(app.controles["masa_kg"]["var_s"].get()) == pytest.approx(62.5)
        app.ejecutar()
        app.rep.seek(app.resultado.t_tensado_s)
        app._actualizar_todo()
        assert app.resultado.a_max_g > 0
    finally:
        app.cerrar()
