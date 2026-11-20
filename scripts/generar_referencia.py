"""Genera ``datos/referencia.csv`` a partir de los modelos congelados."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from simulador.modelo import simular
from simulador.parametros import Escena
from simulador.validacion import escenario_leicester

SALIDA = RAIZ / "datos" / "referencia.csv"


def main():
    base = simular(Escena.pelicula())
    sin = simular(Escena.sin_aire())
    sup = simular(Escena.supervivencia())
    leic = escenario_leicester()
    filas = [
        ("base", "v0_m_s", base.v0_m_s, 1e-6),
        ("base", "k_n_m", base.k_n_m, 1e-6),
        ("base", "x_m", base.x_max_m, 1e-12),
        ("base", "a_max_g", base.a_max_g, 1e-5),
        ("base", "f_max_n", base.f_max_n, 1e-5),
        ("base", "energia_j", base.energia_j, 1e-6),
        ("base", "p_max_w", base.p_max_w, 1e-5),
        ("base", "t_pico_s", base.t_pico_s, 1e-6),
        ("base", "modulo_pa", base.modulo_seda_pa, 1e-5),
        ("base", "deformacion", base.deformacion, 1e-6),
        ("base", "m_cuello_n_m", base.momentos().cuello_n_m, 1e-5),
        ("base", "hic", base.hic, 1e-3),
        ("sin_aire", "v0_m_s", sin.v0_m_s, 1e-9),
        ("sin_aire", "k_n_m", sin.k_n_m, 1e-6),
        ("sin_aire", "a_max_g", sin.a_max_g, 1e-6),
        ("sin_aire", "energia_j", sin.energia_j, 1e-9),
        ("sin_aire", "p_max_w", sin.p_max_w, 1e-5),
        ("sin_aire", "t_pico_s", sin.t_pico_s, 1e-9),
        ("sin_aire", "modulo_pa", sin.modulo_seda_pa, 1e-6),
        ("leicester", "v0_m_s", leic.v0_m_s, 1e-9),
        ("leicester", "k_n_m", leic.k_n_m, 1e-9),
        ("leicester", "x_m", leic.x_m, 1e-9),
        ("leicester", "modulo_pa", leic.modulo_pa, 1e-9),
        ("supervivencia", "k_n_m", sup.k_n_m, 1e-6),
        ("supervivencia", "x_m", sup.x_max_m, 1e-6),
        ("supervivencia", "a_max_g", sup.a_max_g, 1e-6),
        ("supervivencia", "deformacion", sup.deformacion, 1e-6),
        ("supervivencia", "modulo_pa", sup.modulo_seda_pa, 1e-6),
        ("supervivencia", "energia_j", sup.energia_j, 1e-6),
    ]
    with SALIDA.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["caso", "magnitud", "valor", "rtol"])
        for caso, magnitud, valor, rtol in filas:
            writer.writerow([caso, magnitud, f"{valor:.15g}", f"{rtol:.1e}"])
    print(f"escrito {SALIDA} con {len(filas)} valores")


if __name__ == "__main__":
    main()
