"""Regresiones de cámara anclada y de lecturas enlazadas a la malla."""
import numpy as np
import pytest

from simulador.modelo import inspeccionar_paso, simular
from simulador.parametros import Computo, Escena


@pytest.mark.parametrize("metodo", ["euler", "rk4"])
def test_pendientes_reproducen_el_paso_del_integrador(metodo):
    resultado = simular(Escena.pelicula(), computo=Computo(0.001, metodo))
    t = resultado.tiempos_pasos_s
    i = np.searchsorted(t, resultado.t_tensado_s)
    for paso in (2, i + 1):
        pendientes = inspeccionar_paso(resultado, paso)
        pesos = np.array([1]) if metodo == "euler" else np.array([1, 2, 2, 1]) / 6
        ind = np.searchsorted(resultado.t, t[paso:paso + 2])
        incremento = np.diff(np.c_[-resultado.altura_torso_m[ind], resultado.v_m_s[ind]], axis=0)[0]
        np.testing.assert_allclose(resultado.paso_s * (pesos @ pendientes), incremento, atol=1e-12)


@pytest.fixture
def visor_panda():
    pytest.importorskip("panda3d")
    from panda3d.core import loadPrcFileData
    from visual.app_panda3d import Visor

    loadPrcFileData("test", "load-display p3headlessgl\naudio-library-name null")
    app = Visor(True)
    try:
        yield app
    finally:
        app.destroy()


@pytest.mark.gui
def test_camara_y_graficas_en_pausa(monkeypatch, visor_panda):
    from panda3d.core import Vec3

    app = visor_panda
    app._saltar_tensado()
    t = app.t
    lecturas = [dato.getText() for dato in app.lecturas]
    cursores = (app.grafica_v.cursor.getX(), app.grafica_f.cursor.getX())
    for _ in range(3):
        antes = app.camera.getPos()
        frente = app.camera.getQuat().xform(Vec3(0, 1, 0))
        raton = iter([0.0, 0.15])
        monkeypatch.setattr(app, "_raton_en_visor", lambda: next(raton))
        app._iniciar_arrastre()
        app._cuadro(app.taskMgr.getTasksNamed("reproducción")[0])
        monkeypatch.setattr(app, "_raton_en_visor", lambda: 0.15)
        app._acercar(0.8)
        despues = app.camera.getPos()
        giro = app.camera.getQuat().xform(Vec3(0, 1, 0))
        assert (despues - antes).length() > 0.03
        objetivo = np.linalg.lstsq(np.array([frente, -giro]).T,
                                    np.array(despues - antes), rcond=None)[0]
        np.testing.assert_allclose(antes + frente * objetivo[0],
                                   despues + giro * objetivo[1], atol=2e-5)
        assert app.t == t
        assert [dato.getText() for dato in app.lecturas] == lecturas
        assert (app.grafica_v.cursor.getX(), app.grafica_f.cursor.getX()) == cursores
        app._cambiar_vista()

    app._ampliar_frenado()
    app._paso()
    assert app.t > t
    assert app.grafica_f.cursor.getX() > cursores[1]
    assert app.lecturas[1].getText() != lecturas[1]
    app._alternar_edo()
    assert "k4" in app.etapas.getText()
    app._metodo("euler")
    assert "Incremento = h k1" in app.etapas.getText()


@pytest.mark.gui
def test_evento_de_ventana_reescala_panel_y_render(monkeypatch, visor_panda):
    from direct.showbase.ShowBase import ShowBase
    from panda3d.core import Point3
    from types import SimpleNamespace
    from visual.panel_panda3d import ESCENA

    app = visor_panda
    llamados = []

    def evento_base(self, ventana):
        w, h = ventana.getSbsLeftXSize(), ventana.getSbsLeftYSize()
        llamados.append((w, h))
        self.pixel2d.setScale(2 / w, 1, 2 / h)
        self.camLens.setAspectRatio(w / h)

    monkeypatch.setattr(ShowBase, "windowEvent", evento_base)
    for w, h in ((1100, 700), (900, 600), (700, 820), (1400, 800), (1100, 700)):
        ventana = SimpleNamespace(getSbsLeftXSize=lambda: w, getSbsLeftYSize=lambda: h)
        with monkeypatch.context() as cambios:
            cambios.setattr(app, "win", ventana)
            app.messenger.send("window-event", [ventana])

        assert llamados[-1] == (w, h)
        x0, y0, x1, y1 = ESCENA
        region = app.region_3d
        izquierda = app.render2d.getRelativePoint(app.panel, Point3(x0, 0, -y0))
        derecha = app.render2d.getRelativePoint(app.panel, Point3(x1, 0, -y1))
        assert (izquierda.x + 1) / 2 == pytest.approx(region.getLeft(), abs=1e-6)
        assert (izquierda.z + 1) / 2 == pytest.approx(region.getTop(), abs=1e-6)
        assert (derecha.x + 1) / 2 == pytest.approx(region.getRight(), abs=1e-6)
        assert (derecha.z + 1) / 2 == pytest.approx(region.getBottom(), abs=1e-6)
        assert app.camLens.getAspectRatio() == pytest.approx((x1 - x0) / (y1 - y0))
        panel = app.render2d.getRelativePoint(app.panel, Point3(1082, 0, -686))
        assert -1 < panel.x < 1 and -1 < panel.z < 1


def test_mallas_procedurales_normales_y_triangulos():
    pytest.importorskip("panda3d")
    from panda3d.core import GeomVertexReader
    from visual.mallas_panda3d import (
        malla_elipsoide, malla_grietas_piso, malla_loft_eje, malla_toroide,
    )

    mallas = [
        malla_loft_eje("tubo", [{"pos": 0.0, "r1": 0.1, "r2": 0.1}, {"pos": 0.5, "r1": 0.15, "r2": 0.12}], n_lados=20),
        malla_elipsoide("esf", 0.1, 0.08, 0.09, (0.8, 0.6, 0.5, 1.0)),
        malla_toroide("toro", 0.12, 0.015),
        malla_grietas_piso("grietas", radio=0.5),
    ]
    for nodo in mallas:
        assert nodo.getNumGeoms() == 1
        geom = nodo.getGeom(0)
        vdata = geom.getVertexData()
        assert vdata.getNumRows() > 10
        assert geom.getPrimitive(0).getNumPrimitives() > 10
        rv = GeomVertexReader(vdata, "vertex")
        rn = GeomVertexReader(vdata, "normal")
        while not rv.isAtEnd():
            v = rv.getData3f()
            n = rn.getData3f()
            assert np.all(np.isfinite([v.x, v.y, v.z]))
            assert np.isclose(n.length(), 1.0, atol=1e-4)


@pytest.mark.gui
def test_animacion_personaje_y_danos_conservan_sincronizacion(visor_panda):
    from visual.app_panda3d import DURACION_DANO_S

    app = visor_panda
    p = app.personaje

    # Caída libre: abanico de seda y daños ocultos
    app._inicio()
    app.t = 1.0
    app._dibujar()
    assert p.abanico_seda.isHidden()
    assert p.dano_cuello.isHidden()
    assert p.dano_piso.isHidden()

    # Frenado activo: abanico y estrés cervical visibles, piso intacto
    app.t = app.r.t_tensado_s + 0.015
    app._dibujar()
    assert not p.abanico_seda.isHidden()
    assert not p.dano_cuello.isHidden()
    assert p.dano_piso.isHidden()

    poses_finales = {}
    for escenario in (0, 1, 2):
        app.indice_piso = escenario
        app._calcular()
        app.t = app.fin
        app.t_dano = 0.0
        app._dibujar()
        lecturas_fin = [dato.getText() for dato in app.lecturas]
        cursores_fin = (app.grafica_v.cursor.getX(), app.grafica_f.cursor.getX())
        altura_fin = app.cuerpo.getZ()

        # Reproducir el sub-reloj visual de daño sin mover t ni lecturas ni cursores
        app.play = True
        app.ultimo_cuadro -= 0.04
        for _ in range(16):
            app.ultimo_cuadro -= 0.045
            app._cuadro(app.taskMgr.getTasksNamed("reproducción")[0])
        assert app.t == pytest.approx(app.fin)
        assert app.t_dano == pytest.approx(DURACION_DANO_S)
        assert not app.play
        assert [dato.getText() for dato in app.lecturas] == lecturas_fin
        assert (app.grafica_v.cursor.getX(), app.grafica_f.cursor.getX()) == cursores_fin
        assert app.cuerpo.getZ() == pytest.approx(altura_fin)

        poses_finales[escenario] = (
            p.cabeza.getQuat(),
            p.craneo.getHpr(),
            p.rodillas[0].getQuat(),
            p.muslos[0].getQuat(),
        )

        if escenario == 0:
            # Caso base: sin contacto con el piso -> daño cervical en el aire, piso intacto
            assert not p.dano_cuello.isHidden()
            assert p.dano_piso.isHidden()
            assert p.dano_craneo.isHidden()
            assert p.dano_rodillas[0].isHidden()
        elif escenario == 1:
            # Contacto cabeza: daño craneal + piso fracturado, rodillas sin marca y sin atravesar piso
            assert not p.dano_craneo.isHidden()
            assert not p.dano_piso.isHidden()
            assert p.dano_rodillas[0].isHidden()
            assert p.malla_rostro.getTightBounds(app.render)[0].z >= app.piso_m - 0.02
            assert p.malla_cabello_base.getTightBounds(app.render)[0].z >= app.piso_m - 0.02
            assert p.manos[0].getTightBounds(app.render)[0].z >= app.piso_m - 0.02
        else:
            # Contacto piernas: daño en rodillas/tobillos + piso fracturado, cráneo sin marca
            assert not p.dano_rodillas[0].isHidden()
            assert not p.dano_tobillos[0].isHidden()
            assert not p.dano_piso.isHidden()
            assert p.dano_craneo.isHidden()
            # Botas, manos y melena no atraviesan el piso (+0.85 m)
            assert p.tobillos[0].getPos(app.render).z >= app.piso_m - 0.02
            assert p.manos[0].getTightBounds(app.render)[0].z >= app.piso_m - 0.02
            assert p.melena_tramos[-1].getTightBounds(app.render)[0].z >= app.piso_m - 0.025

    # Las 3 animaciones de desenlace producen poses distintas
    assert poses_finales[0] != poses_finales[1]
    assert poses_finales[1] != poses_finales[2]
    assert poses_finales[0] != poses_finales[2]
