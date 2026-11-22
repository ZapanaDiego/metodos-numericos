"""CLI del proyecto: escenarios, experimentos y estado de los entregables."""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path

from simulador.modelo import simular
from simulador.parametros import Escena

RAIZ = Path(__file__).resolve().parent
EXPERIMENTOS = {
    "e1": "experimentos.e1_convergencia",
    "e2": "experimentos.e2_rigidez",
    "e3": "experimentos.e3_energia_hic",
    "e4": "experimentos.e4_umbral",
    "e5": "experimentos.e5_latigazo",
    "e6": "experimentos.e6_rozamiento",
    "e7": "experimentos.e7_montecarlo",
    "e8": "experimentos.e8_sensibilidad",
    "e9": "experimentos.e9_redondeo",
    "e10": "experimentos.e10_raices",
    "e11": "experimentos.e11_caida",
    "b0": "experimentos.b0_benchmark3d",
    "b1": "experimentos.b1_benchmark_humanoide",
}
ESCENARIOS = {
    "base": Escena.pelicula,
    "leicester": Escena.sin_aire,
    "supervivencia": Escena.supervivencia,
    "torre": Escena.torre_completa,
}


def _resumen(escena: Escena):
    r = simular(escena)
    m = r.momentos()
    print(f"escenario: {escena.modo}  Cd·A={escena.cuerpo.cd_area_m2:.2f}  L={escena.telarana.longitud_m:.1f}")
    print(f"  v0={r.v0_m_s:.3f} m/s  k={r.k_n_m:.1f} N/m  x={r.x_max_m:.3f} m")
    print(f"  a_max={r.a_max_g:.2f} g  F_max={r.f_max_n/1e3:.2f} kN  E={r.energia_j/1e3:.2f} kJ")
    print(f"  P_max={r.p_max_w/1e6:.3f} MW  t_pico={r.t_pico_s*1e3:.2f} ms  HIC={r.hic:.0f}")
    print(f"  seda E={r.modulo_seda_pa/1e9:.2f} GPa  eps={r.deformacion*100:.2f} %  M_cuello={m.cuello_kn_m:.3f} kN·m")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Simulación de la caída de Gwen Stacy")
    parser.add_argument("--escenario", choices=ESCENARIOS, default="base")
    parser.add_argument("--experimento", choices=EXPERIMENTOS)
    parser.add_argument("--todo", action="store_true", help="muestra el estado de los entregables")
    args = parser.parse_args(argv)

    if args.experimento:
        modulo = importlib.import_module(EXPERIMENTOS[args.experimento])
        modulo.main()
        return
    if args.todo:
        print("Entregables:")
        print(f"  README.md: {'ok' if (RAIZ/'README.md').exists() else 'falta'}")
        print(f"  AGENTS.md: {'ok' if (RAIZ/'AGENTS.md').exists() else 'falta'}")
        print(f"  datos/referencia.csv: {'ok' if (RAIZ/'datos/referencia.csv').exists() else 'falta'}")
        print("  experimentos:")
        for clave in EXPERIMENTOS:
            print(f"    {clave}: {EXPERIMENTOS[clave]}")
        print("  app: visual.app_tkinter")
        print("  laboratorio: visual.app_panda3d")
        print("  mp4: visual.render_mp4")
        print("  tests: .venv/bin/python -m pytest -q")
        return
    _resumen(ESCENARIOS[args.escenario]())


if __name__ == "__main__":
    main()
