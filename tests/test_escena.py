"""Tests de la escena 3D y del cuerpo articulado."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from simulador.modelo import simular
from simulador.parametros import Escena
from visual.animacion import Reproductor
from visual.cuerpo3d import CuerpoHumano
from visual.escena3d import ANCLA_Z, ALTURA_TORRE, construir_escena
from visual.estilo import PALETA, aplicar_estilo_3d, configurar_matplotlib

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


def _escena():
    r = simular(Escena.pelicula(), n_caida=400, n_resorte=400)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    return r, fig, ax, construir_escena(fig, ax, r)


def test_escena_estatica_y_ancla():
    r, fig, ax, escena = _escena()
    assert escena.cuerpo.contar_artistas() >= 20
    assert abs(ANCLA_Z - 43.60) < 1e-12
    assert ALTURA_TORRE == 72.0
    assert escena.estaticos["suelo"] is not None
    assert escena.vista == "seguir"
    plt.close(fig)


def test_actualizar_no_crea_artistas():
    r, fig, ax, escena = _escena()
    n0 = escena.contar_artistas()
    rep = Reproductor(r)
    for t in np.linspace(0, r.t[-1], 10):
        escena.actualizar(rep.estado(float(t)).__dict__, rep.trayectoria_hasta(float(t)))
    assert escena.contar_artistas() == n0
    plt.close(fig)


def test_render_estatico(tmp_path):
    r, fig, ax, escena = _escena()
    rep = Reproductor(r)
    escena.actualizar(rep.estado(r.t_tensado_s).__dict__, rep.trayectoria_hasta(r.t_tensado_s))
    salida = tmp_path / "frame.png"
    fig.savefig(salida)
    assert salida.exists() and salida.stat().st_size > 0
    plt.close(fig)


def test_cuerpo_pose_y_suelo():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    cuerpo = CuerpoHumano(ax, t_tensado_s=3.0)
    estado = {"altura_torso": 1.2, "a_g": 158.6, "fase": 1, "t": 3.004}
    j = cuerpo.esqueleto(estado)
    for clave, punto in j.items():
        assert np.all(np.isfinite(punto)), clave
    assert j["cabeza"][2] > j["pecho"][2] > j["pelvis"][2]
    assert j["pie_der"][2] >= -0.01
    assert j["pie_izq"][2] >= -0.01
    cintura = cuerpo.punto_cintura(estado)
    assert cintura[2] == pytest.approx(1.2)
    plt.close(fig)


def test_cuerpo_actualiza_sin_nan():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    cuerpo = CuerpoHumano(ax, t_tensado_s=1.0)
    for t in np.linspace(0, 1.1, 8):
        cuerpo.actualizar({"altura_torso": 1.2, "a_g": 10 + 100 * t, "fase": 1, "t": t})
    plt.close(fig)


def test_reproductor_seek_y_estado():
    r, fig, ax, _ = _escena()
    rep = Reproductor(r)
    e = rep.seek(r.t_tensado_s)
    assert e.t == pytest.approx(r.t_tensado_s)
    assert e.altura_torso == pytest.approx(1.60, abs=0.05)
    plt.close(fig)


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


def test_paleta_y_estilo_3d():
    configurar_matplotlib()
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    aplicar_estilo_3d(fig, ax)
    assert PALETA["fondo"].startswith("#")
    assert fig.get_facecolor()[:3] == pytest.approx(
        tuple(int(PALETA["fondo"][i : i + 2], 16) / 255 for i in (1, 3, 5)), abs=1e-6
    )
    plt.close(fig)
