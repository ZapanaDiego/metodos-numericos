"""Tests de la escena 3D y del reproductor."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from simulador.modelo import simular
from simulador.parametros import Escena
from visual.animacion import Reproductor
from visual.escena3d import ANCLA_Z, ALTURA_TORRE, construir_escena

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


def test_escena_estatica_y_ancla():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    escena = construir_escena(fig, ax)
    assert len(escena.segmentos) == 7
    assert abs(ANCLA_Z - 43.60) < 1e-12
    assert ALTURA_TORRE == 72.0
    assert escena.estaticos["suelo"] is not None
    plt.close(fig)


def test_actualizar_no_crea_artistas():
    r = simular(Escena.pelicula(), n_caida=500, n_resorte=500)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    escena = construir_escena(fig, ax)
    n0 = escena.contar_artistas()
    rep = Reproductor(r)
    for t in np.linspace(0, r.t[-1], 10):
        est = rep.estado(float(t))
        escena.actualizar(est.__dict__, rep.trayectoria_hasta(float(t)))
    assert escena.contar_artistas() == n0
    plt.close(fig)


def test_render_estatico(tmp_path):
    r = simular(Escena.pelicula(), n_caida=300, n_resorte=300)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    escena = construir_escena(fig, ax)
    rep = Reproductor(r)
    escena.actualizar(rep.estado(r.t_tensado_s).__dict__, rep.trayectoria_hasta(r.t_tensado_s))
    salida = tmp_path / "frame.png"
    fig.savefig(salida)
    assert salida.exists() and salida.stat().st_size > 0
    plt.close(fig)


def test_reproductor_seek_y_estado():
    r = simular(Escena.pelicula())
    rep = Reproductor(r)
    e = rep.seek(r.t_tensado_s)
    assert e.t == pytest.approx(r.t_tensado_s)
    assert e.altura_torso == pytest.approx(1.60, abs=0.05)


def test_velocidad_y_reinicio():
    r = simular(Escena.pelicula())
    rep = Reproductor(r)
    with pytest.raises(ValueError):
        rep.set_velocidad(2.0)
    rep.set_velocidad(0.1)
    rep.play()
    for _ in range(10):
        rep.avanzar(0.1)
    assert rep.t > 0
    t_antes = rep.t
    rep.reiniciar()
    assert rep.t == 0.0
    assert t_antes > 0


def test_camara_lenta_automatica():
    r = simular(Escena.pelicula())
    rep = Reproductor(r)
    rep.seek(r.t_tensado_s)
    assert rep.velocidad_efectiva <= 0.05
