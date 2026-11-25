# Física
La caída usa desplazamiento y velocidad positivos hacia abajo. Resultado.a_m_s2 es positiva hacia arriba. Comparar Euler y RK4 con el mismo k y con el estado de cada método al tensarse. Los eventos y mediciones pertenecen al modelo. Usar datos/referencia.csv para la regresión.

Estado. Euler y RK4 comparten el contrato Resultado. mediciones.py documenta
los dos osciladores y la localización del contacto. Validación en
tests/test_caida_euler_rk4.py.

Variables centralizadas (V1–V4). `simulador/variables.py` es la única fuente de
inicialización de las variables físicas, geométricas, anatómicas, constantes
de las EDO (`c`, `coef`, `v_t`, `k`, `omega2`, `omega`) y pasos `h`. Los demás
módulos de `simulador/`, `visual/` y `experimentos/` las instancian desde allí.
Validación en `tests/test_variables.py`.
