"""Capturas reproducibles de Panda3D para la guía del README."""

from panda3d.core import Filename, loadPrcFileData

from simulador.graficas import RESULTADOS
from visual.app_panda3d import Visor


def capturar(visor, nombre):
    """Renderiza escena y panel antes de guardar la ventana."""
    visor._dibujar()
    for _ in range(2):
        visor.graphicsEngine.renderFrame()
    ruta = RESULTADOS / nombre
    if not visor.win.saveScreenshot(Filename.fromOsSpecific(str(ruta))):
        raise RuntimeError(f"No se pudo guardar {ruta}.")
    print(ruta)


def main():
    loadPrcFileData("capturas", "win-size 1100 700\nload-display p3headlessgl\naudio-library-name null")
    visor = Visor(fuera_pantalla=True)
    try:
        visor.t = 0.58 * visor.r.t_tensado_s
        capturar(visor, "panda_caida.png")

        visor._saltar_tensado()
        visor.t += 0.015
        capturar(visor, "panda_captura.png")

        visor._ampliar_frenado()
        visor.t = visor.r.t_tensado_s + visor.r.t_pico_s
        capturar(visor, "panda_velocidad_cero.png")

        visor._alternar_edo()
        visor.t = visor.r.t_tensado_s + 0.010
        capturar(visor, "panda_edo.png")
    finally:
        visor.destroy()


if __name__ == "__main__":
    main()
