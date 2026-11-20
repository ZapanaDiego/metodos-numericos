# AGENTS.md — Proyecto Gwen Stacy (Métodos Numéricos)

Este archivo es la fuente de verdad para cualquier agente que trabaje en el
repositorio. Si una decisión de este documento cambia, se actualiza aquí y se
avisa en el commit correspondiente.

## 1. Objetivo

Simular la caída de Gwen Stacy y responder: **¿cuánta energía recibe el cuerpo y
por qué no puede liberarse gradualmente?** El entregable es un informe técnico
(README), código documentado, una app de escritorio con simulación 3D en tiempo
real y diapositivas de sustentación.

## 2. Escenario base congelado

- Caída con arrastre cuadrático, `Cd·A = 0.6 m²`, `m = 50 kg`.
- `H = 42.00 m` de caída hasta el tensado; `L = 42.00 m`; `x_max = 0.40 m`.
- Ancla a `43.60 m`; torso final a `1.20 m`: `43.60 - 42.00 - 0.40 = 1.20`.
- El cuerpo es atrapado **en el torso**. No se afirma que cabeza o piernas
  golpeen el suelo: el daño se evalúa por aceleración del torso y momento
  cervical/cadera.
- Escenario Leicester (validación): sin aire, `H = 42`, `m = 50`, objetivo 6 g.
- Escenario de supervivencia con aire: `k = 272.37 N/m`, `x = 12.61 m`,
  `E = 457.6 MPa`, `ε = 30.0 %` (no es factible por el espacio libre de 1.60 m).

Valores golden (ver `datos/referencia.csv`):

| Magnitud | Base con aire | Leicester sin aire |
|---|---:|---:|
| `v` al tensarse | 24.866 m/s | 28.7061 m/s |
| `k` | 195 679 N/m | 259 965 N/m |
| `a_pico` | 158.575 g | 211.00 g |
| `F_pico` | 78.272 kN | 103.99 kN |
| Energía absorbida | 15.654 kJ | 20.797 kJ |
| `P_pico` real (`k·x·v`) | 0.9757 MW | 1.495 MW |
| `t_pico` (primer `ẋ=0`) | 25.206 ms | 21.850 ms |
| `E` implícito de la seda | 328.74 GPa | 436.74 GPa |

Fórmulas obligatorias:

- `v(t) = v_t tanh(g t / v_t)`, `y(t) = (v_t²/g) ln cosh(g t / v_t)`.
- `k = m(v₀² + 2 g x)/x²` (modo calibración).
- `a_max = sqrt(g² + (k/m) v₀²)`.
- `t_pico = (π - atan(v₀ω/g))/ω`, **no** `atan2(v₀ω, g)/ω`.
- `P(t) = k x(t) ẋ(t)`, **no** `F_max·v₀`.
- `M_cuello = m_cabeza · r · (a_t + g)`.
- OU: `dω = -λ ω dt + σ√(2λ) dW` ⇒ varianza estacionaria `σ²`.
- HIC: aceleración en g, ventana máxima 36 ms, o se etiqueta como índice
  equivalente. No usar una ventana de 0.8 s.

## 3. Entorno y comandos

```bash
.venv/bin/python -m pytest -m fast -q        # cada iteración
.venv/bin/python -m pytest -q                # al cerrar fase
.venv/bin/python -m experimentos.e1_convergencia
.venv/bin/python -m visual.app_tkinter
```

- Python 3.14.10; numpy 2.5.5, scipy 1.18.1, matplotlib 3.11.2, pytest 9.2.0.
- Tests de matplotlib siempre con backend `Agg` (lo fija `conftest.py`).
- Tests de GUI se saltan si no hay `DISPLAY`.
- No se avanza con la suite en rojo. Si un valor golden se mueve fuera de
  tolerancia, se detiene y se consulta.

## 4. Arquitectura

```
simulador/     física, métodos numéricos y modelos
experimentos/  scripts que generan figuras y CSV
visual/        escena 3D, reproductor, MP4 y app Tk
tests/         una suite por iteración + valores golden
datos/         referencia.csv con los valores congelados
resultados/    figuras y tablas versionadas (no MP4)
docs/          presentación
```

- `simulador.modelo.simular()` es la única fuente de verdad para la app, los
  experimentos y Monte Carlo. El bucle de dibujo **no** integra.
- Los integradores viven en `simulador/edo.py` y comparten firma.
- Monte Carlo se vectoriza sobre `N` desde el principio; no bucles por muestra.
- Sin RNG global: `numpy.random.Generator` creado por ejecución.
- Dataclasses con unidades en el nombre (`masa_kg`, `longitud_m`).

## 5. Convenciones visuales

- Tema oscuro pizarra + cian (`visual/estilo.py`): fondo `#0b0f14`, superficie
  `#121821`, tarjeta `#1a2230`, acento `#4cc9f0`, alerta `#ff5c5c`.
- El cuerpo es un maniquí low-poly procedural (`visual/cuerpo3d.py`), no un
  stick figure. La seda se une a la cintura, no al cuello.
- Tres vistas: `seguir` (cámara que acompaña), `cuerpo` (detalle fijo) y
  `torre` (contexto completo).
- La física no cambia por motivos visuales. Cualquier cambio de pose es solo
  presentación.
- `b1` mide el rendimiento del maniquí; `app_captura.png` es la captura de
  referencia de la interfaz.

## 6. Convenciones

- Commits: `I07 raices: 5 metodos + tabla de convergencia`.
- Docstrings y comentarios en español; nombres de API en español.
- Cada iteración deja test, figura o CSV en `resultados/`.
- Las figuras citadas por el README se versionan; solo `*.mp4` y archivos
  pesados van a `.gitignore`.
- No se introducen dependencias nuevas sin justificarlas aquí.

## 7. Reglas de parada

1. Leicester no reproduce dentro de tolerancia.
2. El benchmark 3D no alcanza 25 fps y no hay fallback aceptado.
3. Un supuesto físico del plan resulta falso (se consulta antes de seguir).
4. La suite completa falla y no se identifica la causa en la iteración.
