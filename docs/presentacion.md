# Presentación — La caída de Gwen Stacy

**Duración objetivo:** 12–15 min + 3 min de demo.
**Regla:** cada lámina responde una de las cinco preguntas de la rúbrica.

---

## Lámina 1 — Título (20 s)

- La caída de Gwen Stacy.
- Pregunta: ¿cuánta energía recibió y por qué no pudo liberarse gradualmente?
- Métodos Numéricos · Proyecto final.

## Lámina 2 — El problema (60 s)

- La escena: 42 m de caída, ancla a 43.6 m, 0.4 m de estiramiento.
- La tesis: la energía total es finita; lo que mata es la **tasa**.
- Dos números que se repiten: 15.7 kJ y ~25 ms.

## Lámina 3 — Geometría y datos (60 s)

- `h_ancla − L − x = h_torso`: 43.60 − 42.00 − 0.40 = 1.20 m.
- 50 kg, `Cd·A = 0.6 m²`, aire ρ = 1.2 kg/m³.
- El espacio libre hasta el suelo es 1.60 m: el dato que decide todo.
- Fuente de validación: Leicester (2021).

## Lámina 4 — Modelo (90 s)

- Fase 1: `m dv/dt = mg − ½ρCdA v²` → `v(t) = v_t tanh(g t/v_t)`.
- Fase 2: `m ẍ = mg − kx` → `x(t)`, `a_max`, `t_pico`.
- Fase 3: cuerpo anclado en el torso; `M_cuello = m r (a_t + g)`.
- Tres ecuaciones, tres formas de validar.

## Lámina 5 — Solución analítica (60 s)

- `v_0 = 24.87 m/s` con aire; 28.71 m/s sin aire.
- `k = 195 739 N/m`; `x_max = 0.40 m`.
- `a_max = 158.6 g` con aire; 211 g sin aire.
- `P_pico = 0.976 MW` (no `F_max·v_0`).

## Lámina 6 — Validación Leicester (60 s)

- Reproducimos: `v = 28.706`, `x = 16.80`, `k = 204.375`, `E = 343 MPa`.
- El paper redondea `x` a 16.7; con 6 g exactos, `x = 0.4H`.
- Si Leicester no reproduce, no se avanza: es el gate del proyecto.

## Lámina 7 — Métodos numéricos (90 s)

- Raíces: bisección, falsa posición, punto fijo, Newton, secante (I07).
- EDO: Euler, Heun, Taylor 2, RK4, Euler implícito, RKF45 (I08–I09).
- Integración: Newton-Cotes, Gauss, Romberg (I13).
- Lineales: LU, Thomas, Jacobi, Gauss-Seidel (I19).
- Interpolación: Lagrange, Newton, spline, mínimos cuadrados (I23).

## Lámina 8 — Convergencia y rigidez (60 s)

- Figura e1: órdenes 1, 2, 4.
- Figura e2: `h_crit = 27.74 ms`; Euler explícito diverge, implícito no.
- Mensaje: el método importa tanto como la ecuación.

## Lámina 9 — Energía y potencia (60 s)

- Figura e3: cinética → elástica; conservación.
- `E = 15.66 kJ`; `P_pico = 0.976 MW`.
- HIC ~8·10³ con la ventana de 36 ms.

## Lámina 10 — La región factible es vacía (90 s)

- Para 6 g: `k = 272.4 N/m`, `x = 12.61 m`, `ε = 30 %`.
- Para no tocar el suelo: `x ≤ 1.60 m` → `E ≥ 21.3 GPa`, `a ≈ 40 g`.
- Seda real (1–10 GPa): se estira 3.8–12.6 m e impacta a 18.6–24.9 m/s.
- **No hay intersección.** Ésta es la conclusión del proyecto.

## Lámina 11 — Latigazo (60 s)

- Figura e5: torso a 1.20 m; cabeza y cadera por encima del suelo.
- `M_cuello = 1.41 kN·m` (20–60× el umbral).
- El daño es inercial; no hace falta golpear el piso.

## Lámina 12 — Monte Carlo y sensibilidad (45 s)

- e7: 100 % de las corridas con HIC > 700; p5 de `a_max` ≫ 6 g.
- e8: `k` y la altura dominan; el resultado es robusto.

## Lámina 13 — Conclusiones (60 s)

1. La energía no es el problema; la potencia y la aceleración sí.
2. Ninguna seda real cabe en 1.6 m sin impacto o sin ≥40 g.
3. El escenario de 6 g es geométricamente inviable.
4. El latigazo cervical es el mecanismo final.
5. El modelo reproduce Leicester y los órdenes numéricos.

## Lámina 14 — Demo (3 min)

- App: ejecutar, pausar, reiniciar, cambiar masa/estiramiento/k/longitud/semilla.
- Cámara lenta automática en el frenado.
- HUD: `t`, `y`, `v`, `a/g`, `F`, `E`, `P`, `HIC`, semáforo.
- Monte Carlo en vivo.

## Lámina 15 — Preguntas (30 s)

- Limitaciones: modelo 1D, seda lineal, HIC comparativo.
- Trabajo futuro: viscoelasticidad, modelo 3D del cuerpo, más orientaciones.
