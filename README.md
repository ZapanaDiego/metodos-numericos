# La caída de Gwen Stacy: energía, potencia y latigazo

**Curso:** Métodos Numéricos
**Autor:** Diego
**Entregables:** informe técnico (este README), código documentado, app de escritorio con simulación 3D en tiempo real y diapositivas.

---

## 1. Introducción y pregunta

¿Cuánta energía recibió el cuerpo de Gwen Stacy y por qué esa energía no pudo
liberarse de forma gradual?

La respuesta corta es que **la energía no es el problema: lo es la tasa a la que
se entrega**. En el escenario de la película el cuerpo llega al tensado con
unos **15.7 kJ** de energía cinética (20.8 kJ si se ignora el aire) y debe
disiparlos en una fracción de segundo. La potencia pico real es del orden de
**1 MW** y la aceleración pico de **158.6 g** con arrastre, o **211 g** sin aire.

El proyecto reproduce la escena con tres modelos:

1. caída con arrastre cuadrático,
2. telaraña elástica lineal,
3. cuerpo articulado anclado en el torso.

El caso de validación es el análisis de la Universidad de Leicester (2021),
que con una caída de 42 m sin aire y 50 kg obtiene `v ≈ 28.7 m/s`, `x ≈ 16.7 m`,
`k ≈ 204.5 N/m` y `E ≈ 343 MPa` para un límite de 6 g. El mecanismo del
latigazo es el que Marvel confirmó en el correo de lectores de *ASM* #125.

![Caída y frenado](resultados/frame_mp4.png)

---

## 2. Modelo matemático

### 2.1 Geometría

La escena se fija con cuatro datos coherentes:

| Magnitud | Valor | Origen |
|---|---:|---|
| Altura del ancla | 43.60 m | repisa inferior de la torre |
| Longitud tensa de la seda | 42.00 m | dato de la escena |
| Estiramiento observado | 0.40 m | dato de la escena |
| Altura final del torso | 1.20 m | `43.60 − 42.00 − 0.40` |
| Masa del cuerpo | 50 kg | Emma Stone ≈ 52 kg; Leicester usa 50 |
| `Cd·A` base | 0.60 m² | caída de espaldas/plana |
| Densidad del aire | 1.20 kg/m³ | aire a ~20 °C |

La verificación geométrica es exacta:

```
43.60 − 42.00 − 0.40 = 1.20 m
```

El ancla no está en la cúspide de los 72 m: Spider-Man se ancla en una repisa
inferior. El caso de la torre completa, con 70.4 m de caída, queda como
escenario paramétrico.

**Espacio libre.** En el instante de tensado el torso está a
`43.60 − 42.00 = 1.60 m` del suelo. Cualquier estiramiento mayor que 1.60 m
hace que el torso toque el suelo antes de detenerse. Este dato es central para
la conclusión.

### 2.2 Fase 1: caída con arrastre cuadrático

```
m dv/dt = m g − ½ ρ Cd A v²,     v(0)=0,  y(0)=0
```

Con `c = ½ ρ Cd A` y `v_t = sqrt(m g / c)`:

```
v(t) = v_t tanh(g t / v_t)
y(t) = (v_t²/g) ln cosh(g t / v_t)
```

El tiempo de caída se obtiene de `y(t_f) = H`:

```
t_f = (v_t/g) arccosh(exp(g H / v_t²))
```

Para el escenario base: `t_f = 3.076 s`, `v_t = 36.91 m/s`,
`v_0 = 24.87 m/s`.

### 2.3 Fase 2: telaraña elástica

```
m ẍ = m g − k x,     x(0)=0,  ẋ(0)=v_0
ω = sqrt(k/m)
x(t) = (g/ω²)(1 − cos ωt) + (v_0/ω) sin ωt
```

La aceleración máxima y el primer instante con `ẋ = 0` son:

```
a_max = sqrt(g² + (k/m) v_0²)
t_pico = (π − atan(v_0 ω / g)) / ω
```

La energía absorbida por la seda es:

```
E = ½ m v_0² + m g x_max
```

y la rigidez en modo calibración:

```
k = m(v_0² + 2 g x_max) / x_max²
```

En modo material se fija `k` y se despeja `x_max` de la misma ecuación
energética. Los dos modos se etiquetan explícitamente en todos los experimentos.

### 2.4 Potencia

La potencia instantánea es `P(t) = k x(t) ẋ(t)`. **No** es `F_max·v_0`: la
fuerza máxima ocurre cuando `ẋ = 0` y la velocidad máxima cuando `x = 0`.
Para el escenario base, `P_pico = 0.976 MW`; para el caso sin aire, `1.495 MW`.
La cota `F_max·v_0` (2.985 MW sin aire) se reporta solo como cota superior.

### 2.5 Fase 3: cuerpo articulado anclado en el torso

El cuerpo es atrapado en el torso. La cabeza (5 kg) y las piernas (20 kg) son
segmentos unidos por el cuello (0.18 m) y la cadera (0.45 m). La carga
cuasiestática en el pico es:

```
M_cuello = m_cabeza · r_cuello · (a_t + g)
M_cadera = m_piernas · r_cadera · (a_t + g)
```

Con `a_t = 158.6 g`: `M_cuello ≈ 1.41 kN·m` y `M_cadera ≈ 14.1 kN·m`.
Con `a_t = 6 g`: `M_cuello ≈ 61.8 N·m`, dentro del rango orientativo de
tolerancia cervical (30–90 N·m) pero en su límite alto.

El torso se detiene a 1.20 m y **no** se afirma que la cabeza o las piernas
golpeen el suelo: con el anclaje en el torso y esas longitudes, es
geométricamente imposible. El latigazo se mide por el momento cervical y la
aceleración relativa, no por un impacto contra el piso.

### 2.6 Criterio HIC

```
HIC = max (t₂ − t₁) · [ (1/(t₂−t₁)) ∫ a dt ]^2.5,   t₂ − t₁ ≤ 36 ms
```

La aceleración se expresa en g. El HIC es un criterio de **cabeza**; en este
proyecto se usa como índice comparativo de la carga del torso/cabeza y se
etiqueta como tal. Con un pulso constante de 158.6 g durante 25.2 ms el HIC es
`≈8·10³`; con la forma real del pulso (triangular) baja a `≈5·10³`. El
escenario de 6 g durante 0.86 s da `HIC ≈ 3.2` en la ventana de 36 ms (el valor
de ~70 que a veces se cita usa una ventana de 0.8 s, incompatible con la
definición).

---

## 3. Solución analítica y métodos numéricos

### 3.1 Caso base con aire

| Magnitud | Valor |
|---|---:|
| `v_0` | 24.866 m/s (89.5 km/h) |
| `k` | 195 679 N/m |
| `x_max` | 0.40 m |
| `a_max` | 158.58 g |
| `F_max` | 78.27 kN (160× el peso) |
| `E` absorbida | 15.654 kJ |
| `P_pico` real | 0.9757 MW |
| `t_pico` | 25.21 ms |
| `E` implícito de la seda | 328.74 GPa |
| `ε` | 0.95 % |
| `M_cuello` | 1.41 kN·m |

### 3.2 Validación de Leicester (sin aire)

| Magnitud | Proyecto | Paper |
|---|---:|---:|
| `v_0` | 28.706 m/s | 28.7 |
| `x` | 16.80 m | 16.7 |
| `k` | 204.375 N/m | 204.5 |
| `E` | 343.35 MPa | ~343 |
| `ε` | 40.0 % | — |

La diferencia de `x` (16.80 vs 16.7) es redondeo: con 6 g exactos y balance
energético, `x = 0.4 H = 16.8 m`.

### 3.3 Escenario de supervivencia (6 g con aire)

| Magnitud | Valor |
|---|---:|
| `k` | 272.37 N/m |
| `x_max` | 12.61 m |
| `ε` | 30.0 % |
| `E` implícito | 457.4 MPa |
| `E` absorbida | 21.65 kJ |
| `F_max` | 3.43 kN |
| `M_cuello` | 61.8 N·m |
| HIC (36 ms) | 3.2 |

Este escenario **no es viable**: necesita 12.61 m de estiramiento cuando solo
hay 1.60 m hasta el suelo, y su deformación del 30 % está en el límite de rotura
de la seda dragline.

### 3.4 Métodos numéricos implementados

| Unidad | Métodos | Archivo |
|---|---|---|
| Raíces | bisección, falsa posición, punto fijo, Newton-Raphson, secante | `simulador/raices.py` |
| EDO | Euler, Heun, Taylor 2, RK4, Euler implícito, RKF45 | `simulador/edo.py` |
| Lineales | LU con pivoteo, Thomas, Jacobi, Gauss-Seidel | `simulador/lineales.py` |
| Integración | trapecio, Simpson 1/3 y 3/8, Boole, Gauss-Legendre, Romberg | `simulador/integracion.py` |
| Interpolación | Lagrange, Newton, spline cúbico, mínimos cuadrados | `simulador/interpolacion.py` |
| Errores | error absoluto/relativo, orden observado, Richardson | `simulador/errores.py` |

La app y los experimentos usan **formas cerradas** para la física y los
integradores numéricos para validar, comparar y demostrar convergencia. El
bucle de dibujo nunca integra: solo interpola una trayectoria precalculada.

---

## 4. Resultados

### 4.1 Raíces (e10)

![Raíces](resultados/e10_raices.png)

Los cinco métodos coinciden en la raíz de `x³ − 2x − 5`; bisección tarda 42
iteraciones, Newton converge en menos de 10. La misma infraestructura localiza
el instante de tensado (`t = 3.07567445 s`) y la rigidez crítica de 6 g
(`k = 204.375 N/m`). La tabla completa está en `resultados/e10_raices.csv`.

### 4.2 Convergencia (e1)

![Convergencia](resultados/e1_convergencia.png)

Los órdenes observados coinciden con los teóricos: Euler 1, Heun 2, Taylor 2,
RK4 4. La tabla completa está en `resultados/e1_tabla.csv`.

![Coste](resultados/e1_costo.png)

RK4 con paso grande supera a Euler con paso pequeño para el mismo número de
evaluaciones. RKF45 adaptativo es más barato que RK4 de paso fijo para la misma
tolerancia.

### 4.3 Rigidez (e2)

El benchmark `b0` midió 33.6 fps a 800×600 con ~200 polígonos y 7 segmentos;
como supera el umbral de 25 fps, la app usa `mplot3d` y no necesita el fallback
OpenGL.

![Rigidez](resultados/e2_rigidez.png)

El umbral teórico es `h_crit = 2/ω = 27.74 ms`. Euler explícito diverge para
`h > h_crit`; Euler implícito permanece estable para todos los pasos probados.

### 4.4 Energía, potencia y HIC (e3)

![Energía](resultados/e3_energia.png)

La energía cinética se transfiere a la seda en la fase elástica. La suma de
energías se conserva (con `β=0`) y el residuo numérico es del orden de `1e-8 J`.

![Potencia](resultados/e3_potencia.png)

La potencia pico real es `0.976 MW`, no `F_max·v_0`.

![HIC](resultados/e3_hic.png)

Con la ventana de 36 ms, un pulso de 158.6 g supera ampliamente el umbral 700.

![Cuadraturas](resultados/e3_cuadraturas.png)

Gauss-Legendre y Romberg alcanzan alta precisión con menos evaluaciones;
Simpson 1/3 es exacto para polinomios cúbicos.

### 4.5 Umbral de supervivencia (e4)

![Umbral](resultados/e4_umbral.png)

![x vs k](resultados/e4_x_vs_k.png)

![Región factible](resultados/e4_supervivencia.png)

La región factible es **vacía**:

- para `a ≤ 6 g` se necesita `k = 272.4 N/m` y `x = 12.61 m`;
- para no tocar el suelo se necesita `x ≤ 1.60 m`, es decir `k ≥ 12 694 N/m`
  y `E ≥ 21.3 GPa` (más rígida que cualquier seda real);
- la seda real (1–10 GPa) se estira entre 2.4 y 8.1 m y el torso impacta el
  suelo a 18.6–24.9 m/s.

No existe una rigidez que cumpla ambas restricciones.

### 4.6 Latigazo (e5)

![Articulado](resultados/e5_articulado.png)

![Momentos](resultados/e5_momentos.png)

El torso se detiene a 1.20 m. La cabeza y la cadera permanecen por encima del
suelo; el daño proviene de la desaceleración y del momento cervical, no de un
golpe contra el piso.

### 4.7 Orientación (e6)

![Orientación](resultados/e6_rozamiento.png)

| Orientación | `Cd·A` | `v_0` | `a_max` | HIC (pulso constante) |
|---|---:|---:|---:|---:|
| De cabeza | 0.10 | 28.00 | 200.8 g | 12 793 |
| De pie | 0.25 | 26.99 | 186.6 g | 11 056 |
| De lado | 0.40 | 26.04 | 173.8 g | 9 591 |
| Plana | 0.60 | 24.87 | 158.6 g | 7 983 |
| Espalda extendida | 0.70 | 24.31 | 151.7 g | 7 301 |
| Sin aire | — | 28.71 | 211.0 g | 14 131 |

La velocidad varía un 18 % entre los extremos, pero el HIC se amplifica ~1.9×.
El factor 1.5 del plan original solo aplica al modo de `k` fijo sobre el rango
completo; aquí se reporta el modo calibración (`x=0.4`).

### 4.8 Monte Carlo (e7)

![Monte Carlo](resultados/e7_montecarlo.png)

Con `n = 2000` y semilla 42: `a_max` mediana 158.8 g, HIC mediano 7 989,
`x` mediano 0.40 m y **100 %** de las ejecuciones con HIC > 700. El percentil 5
de `a_max` sigue muy por encima de 6 g.

### 4.9 Interfaz 3D

![Interfaz de la app](resultados/app_captura.png)

La app de escritorio usa un tema oscuro pizarra + cian, un maniquí low-poly
articulado (cabeza, cuello, torso, brazos, manos, piernas y pies), una seda
dorada que se une a la cintura y tres encuadres: **Seguir**, **Cuerpo** y
**Torre**. Cada variable tiene símbolo, unidad y un tooltip; el panel muestra
los valores derivados y el veredicto (letal/supervivencia). El benchmark `b1`
dio 37 fps a 800×600 con el maniquí completo, por lo que no fue necesario el
fallback OpenGL.

### 4.10 Sensibilidad (e8)

![Sensibilidad](resultados/e8_sensibilidad.png)

La rigidez y la altura de caída dominan el HIC; la masa y el `Cd·A` tienen un
efecto menor. El resultado cualitativo no depende de los parámetros: el
escenario es letal en todo el rango razonable.

---

## 5. Análisis de error

### 5.1 Truncamiento y redondeo

El error de truncamiento disminuye con `h` según el orden del método; el error
de redondeo crece al disminuir demasiado `h` (la clásica curva en V). Se
implementaron diferencias adelante, atrás y central; la central es `O(h²)` y
la adelante/atrás `O(h)`.

![Curva en V](resultados/e9_redondeo.png)

En la práctica el mínimo de la diferencia central aparece alrededor de
`h = 5.6·10⁻⁶`, con un error de `3.8·10⁻¹³`; por debajo de ese paso domina el
redondeo de doble precisión.

### 5.2 Orden observado

La tabla `resultados/e1_tabla.csv` incluye `h`, error, orden observado y número
de evaluaciones. Los órdenes medidos son:

| Método | Orden teórico | Orden observado |
|---|---:|---:|
| Euler | 1 | ≈1.00 |
| Heun | 2 | ≈2.00 |
| Taylor 2 | 2 | ≈2.00 |
| RK4 | 4 | ≈4.00 |
| Euler implícito | 1 | ≈1.00 |

### 5.3 Propagación Monte Carlo

El error estándar de la media decae como `σ/√n`. Con `n = 100, 400, 1600` la
razón entre errores sucesivos es ≈2, como corresponde.

### 5.4 Limitaciones

- El modelo es 1D en la fase de caída y cuasiestático en el articulado.
- La seda se modela como resorte lineal; la seda real es viscoelástica y tiene
  una deformación de rotura finita.
- El HIC se usa como índice comparativo, no como diagnóstico clínico.
- La geometría de 43.60 m es una reconstrucción de la escena, no un dato
  topográfico oficial.

---

## 6. Conclusiones

1. **La energía no mata por sí sola.** El cuerpo recibe 15.7 kJ con aire
   (20.8 kJ sin aire) y debe disiparlos en ~25 ms. La potencia pico real es
   ~1 MW.
2. **La geometría no da margen.** Con 1.60 m hasta el suelo, cualquier seda
   que evite el impacto debe ser más rígida que la seda real y aun así impone
   ≥40 g. Cualquier seda real se estira más de 1.6 m y el torso impacta.
3. **El escenario de 6 g es físicamente inviable.** Necesita 12.6 m de
   estiramiento y 30 % de deformación; no cabe en la escena.
4. **El latigazo es el mecanismo final.** Con el anclaje en el torso, el
   momento cervical alcanza ~1.4 kN·m, muy por encima del rango de tolerancia.
   La cabeza y las piernas no necesitan golpear el suelo para explicar el daño.
5. **El modelo numérico es consistente.** Leicester se reproduce, los órdenes
   de convergencia coinciden con la teoría, el sistema rígido exige métodos
   implícitos y Monte Carlo confirma que el resultado es robusto.

---

## 7. Ejecución y estructura

```bash
# entorno
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# suite completa
.venv/bin/python -m pytest -q

# regenerar figuras y tablas
.venv/bin/python -m experimentos.e1_convergencia
.venv/bin/python -m experimentos.e2_rigidez
.venv/bin/python -m experimentos.e3_energia_hic
.venv/bin/python -m experimentos.e4_umbral
.venv/bin/python -m experimentos.e5_latigazo
.venv/bin/python -m experimentos.e6_rozamiento
.venv/bin/python -m experimentos.e7_montecarlo
.venv/bin/python -m experimentos.e8_sensibilidad
.venv/bin/python -m experimentos.e9_redondeo
.venv/bin/python -m experimentos.e10_raices
.venv/bin/python -m experimentos.b1_benchmark_humanoide

# escenarios
.venv/bin/python run.py --escenario base
.venv/bin/python run.py --escenario leicester
.venv/bin/python run.py --escenario supervivencia

# app 3D y MP4
.venv/bin/python -m visual.app_tkinter
.venv/bin/python -m visual.render_mp4 --semilla 42 --salida resultados/pelicula.mp4
```

```
Proyectofinal/
├── AGENTS.md                 reglas del proyecto para agentes
├── README.md                 este informe
├── run.py                    CLI de escenarios y experimentos
├── requirements.txt
├── pyproject.toml
├── simulador/                física y métodos numéricos
├── experimentos/             e1-e8 y benchmark b0
├── visual/                   escena 3D, reproductor, MP4 y app Tk
├── tests/                    suite completa + valores golden
├── datos/referencia.csv      valores congelados
├── resultados/               figuras y tablas
└── docs/                     presentación
```

### Reproducibilidad

- Semilla fija en Monte Carlo (`numpy.random.Generator`).
- Sin estado global; cada ejecución crea su propio generador.
- `datos/referencia.csv` se verifica en cada corrida de la suite.
- Las figuras del informe se versionan; el MP4 se regenera con el comando de
  arriba.

---

## Anexo A — Modelo matemático y resolución manual

Este anexo desarrolla el modelo de la sección 2 paso a paso y muestra cómo
resolverlo **a mano con una calculadora**. No cambia la física ni los valores
golden: es la versión “papel y lápiz” de lo que ejecuta el código.

### A.1 Símbolos y unidades

| Símbolo | Significado | Unidad |
|---|---|---|
| `m` | masa total del cuerpo | kg |
| `g` | gravedad | m/s² |
| `ρ` | densidad del aire | kg/m³ |
| `Cd·A` | área de arrastre efectiva | m² |
| `c` | coeficiente de arrastre `½ρCdA` | kg/m |
| `v_t` | velocidad terminal | m/s |
| `H` | caída hasta el tensado | m |
| `L` | longitud tensa de la seda | m |
| `x` | estiramiento de la seda | m |
| `k` | rigidez de la seda | N/m |
| `ω` | frecuencia angular `sqrt(k/m)` | rad/s |
| `A` | área de la sección de la seda | m² |
| `E` | módulo de Young implícito | Pa |
| `ε` | deformación `x/L` | adimensional |
| `v₀` | velocidad al tensarse | m/s |
| `a_t` | aceleración del torso hacia arriba | m/s² |
| `M` | momento cervical o de cadera | N·m |

### A.2 Geometría y supuestos

Datos de la escena base:

```
h_ancla = 43.60 m
L       = 42.00 m
x       =  0.40 m
h_torso =  1.20 m
H       = 42.00 m
m       = 50 kg
Cd·A    = 0.60 m²
ρ       = 1.20 kg/m³
g       = 9.81 m/s²
```

La geometría se comprueba con una resta:

```
43.60 − 42.00 − 0.40 = 1.20 m
```

El **espacio libre** en el instante de tensado es:

```
h_ancla − L = 43.60 − 42.00 = 1.60 m
```

Si la seda se estira más de 1.60 m, el torso toca el suelo antes de detenerse.
Ésta es la restricción que domina todo el problema.

Supuestos:

1. La caída es vertical y comienza desde el reposo.
2. El arrastre es cuadrático y usa un `Cd·A` constante durante la caída.
3. La seda es un resorte lineal sin amortiguamiento.
4. El cuerpo se ancla en el torso; la cabeza y las piernas son segmentos.
5. No se modela un golpe de cabeza o piernas contra el suelo.

### A.3 Fase 1: caída con arrastre

#### A.3.1 Deducción

La segunda ley de Newton, tomando positivo hacia abajo:

```
m dv/dt = m g − ½ ρ Cd A v²
```

Definimos:

```
c = ½ ρ Cd A          (kg/m)
v_t = sqrt(m g / c)   (m/s)
```

Dividiendo por `m`:

```
dv/dt = g (1 − v²/v_t²)
```

Separando variables:

```
dv / (1 − v²/v_t²) = g dt
```

La integral del lado izquierdo es `v_t · artanh(v/v_t)`. Con `v(0)=0`:

```
v_t · artanh(v/v_t) = g t
v(t) = v_t tanh(g t / v_t)
```

Integrando otra vez, con `y(0)=0`:

```
y(t) = (v_t²/g) ln cosh(g t / v_t)
```

El tiempo de tensado sale de `y(t_f)=H`:

```
(v_t²/g) ln cosh(g t_f/v_t) = H
cosh(g t_f/v_t) = exp(g H / v_t²)
t_f = (v_t/g) arccosh(exp(g H / v_t²))
```

La velocidad al tensarse es `v₀ = v(t_f)`.

#### A.3.2 Resolución manual del caso base

Paso 1. Coeficiente de arrastre:

```
c = 0.5 × 1.20 × 0.60 = 0.36 kg/m
```

Paso 2. Velocidad terminal:

```
v_t = sqrt(50 × 9.81 / 0.36)
    = sqrt(1362.5)
    = 36.91 m/s
```

Paso 3. Exponente del tiempo:

```
g H / v_t² = 9.81 × 42 / 1362.5
           = 0.3024
```

Paso 4. Tiempo de tensado:

```
exp(0.3024) = 1.3532
arccosh(1.3532) = ln(1.3532 + sqrt(1.3532² − 1))
                = ln(1.3532 + 0.9115)
                = 0.8174
t_f = (36.91 / 9.81) × 0.8174
    = 3.7627 × 0.8174
    = 3.0757 s
```

Paso 5. Velocidad al tensarse:

```
v₀ = 36.91 × tanh(0.8174)
   = 36.91 × 0.6737
   = 24.866 m/s
```

#### A.3.3 Caso sin aire

Si `Cd·A = 0`, entonces `c=0`, `v_t → ∞` y las fórmulas se reducen a:

```
v(t) = g t
y(t) = ½ g t²
t_f = sqrt(2H/g)
v₀ = sqrt(2gH)
```

Para `H=42.00` y `g=9.81`:

```
t_f = sqrt(84/9.81) = 2.926 s
v₀  = sqrt(2 × 9.81 × 42) = 28.706 m/s
```

Éste es el caso que se usa para validar contra Leicester.

### A.4 Fase 2: telaraña elástica

#### A.4.1 Deducción

Con `x` medido desde el punto de tensado y positivo hacia abajo:

```
m ẍ = m g − k x
ẍ + ω² x = g,     ω = sqrt(k/m)
```

La solución general es:

```
x(t) = A cos(ωt) + B sin(ωt) + g/ω²
```

Con `x(0)=0` y `ẋ(0)=v₀`:

```
x(t) = (g/ω²)(1 − cos ωt) + (v₀/ω) sin ωt
ẋ(t) = (g/ω) sin ωt + v₀ cos ωt
```

La aceleración neta hacia arriba es `a_t = (k/m)x − g`. En el instante de
tensado vale `−g` (caída libre) y en el pico vale `+a_max`.

#### A.4.2 Estiramiento máximo y aceleración pico

En el máximo, `ẋ=0`:

```
(g/ω) sin(ωt) + v₀ cos(ωt) = 0
tan(ωt) = −v₀ω/g
```

El primer tiempo positivo es:

```
t_pico = (π − atan(v₀ω/g)) / ω
```

Sustituyendo en `x(t)` o usando energía:

```
½ k x_max² = ½ m v₀² + m g x_max
k x_max² − 2 m g x_max − m v₀² = 0
x_max = [m g + sqrt((m g)² + k m v₀²)] / k
```

La aceleración en el pico es:

```
a_max = (k/m) x_max − g
      = sqrt(g² + (k/m) v₀²)
```

Y en unidades de g:

```
a_max[g] = sqrt(1 + (v₀ω/g)²)
```

#### A.4.3 Rigidez en modo calibración

Si se conoce el estiramiento observado `x`, se despeja `k` de la energía:

```
½ k x² = ½ m v₀² + m g x
k = m (v₀² + 2 g x) / x²
```

#### A.4.4 Resolución manual del caso base

Paso 1. Rigidez:

```
k = 50 × (24.866² + 2 × 9.81 × 0.40) / 0.40²
  = 50 × (618.32 + 7.848) / 0.16
  = 195 679 N/m
```

Paso 2. Frecuencia angular:

```
ω = sqrt(195679/50) = 62.559 rad/s
```

Paso 3. Tiempo del pico:

```
v₀ω/g = 24.866 × 62.559 / 9.81 = 158.58
atan(158.58) = 1.5645 rad
t_pico = (π − 1.5645) / 62.559
       = 0.02521 s = 25.21 ms
```

Paso 4. Aceleración pico:

```
a_max = sqrt(9.81² + (195679/50) × 24.866²)
      = 1555.2 m/s²
      = 158.58 g
```

Paso 5. Fuerza pico y energía:

```
F_max = k x = 195679 × 0.40 = 78 271.6 N = 78.27 kN
E     = ½ × 50 × 24.866² + 50 × 9.81 × 0.40
      = 15 458 + 196.2 = 15 654.3 J = 15.65 kJ
```

Paso 6. Módulo implícito y deformación:

```
E_seda = k L / A = 195679 × 42 / 2.5×10⁻⁵
       = 3.2874×10¹¹ Pa = 328.74 GPa
ε = x/L = 0.40/42 = 0.009524 = 0.952 %
σ = E_seda ε = 3.131 GPa
```

El módulo de 328.74 GPa está muy por encima del rango de la seda real
(1–10 GPa), y el esfuerzo de 3.13 GPa supera su resistencia aproximada.

#### A.4.5 Potencia pico: cómo calcularla a mano

La potencia instantánea es:

```
P(t) = F(t) · ẋ(t) = k x(t) ẋ(t)
```

**No** es `F_max · v₀`: la fuerza máxima ocurre cuando `ẋ=0`, y la velocidad
máxima cuando `x=0`. Para encontrar el máximo, se deriva.

Con `z = ωt`:

```
A(z) = (g/ω)(1 − cos z) + v₀ sin z
B(z) = (g/ω) sin z + v₀ cos z
P(z) = (k/ω) A(z) B(z)
```

Derivando:

```
A'(z) = B(z)
B'(z) = (g/ω) cos z − v₀ sin z
dP/dz = (k/ω) [ B(z)² + A(z) B'(z) ]
```

El máximo cumple:

```
B(z)² + A(z) B'(z) = 0
```

Se resuelve por bisección o Newton en `z ∈ (0, ωt_pico)`. Para el caso base:

```
z ≈ 0.7895
t = z/ω = 0.01262 s = 12.62 ms
P_max = k x(t) ẋ(t) = 975 711 W = 0.976 MW
```

La cota `F_max · v₀ = 78.27 kN × 24.866 m/s = 1.947 MW` es solo una cota
superior, no la potencia real.

### A.5 Fase 3: momentos del cuerpo articulado

Con el torso como anclaje y `a_t` positivo hacia arriba:

```
M_cuello = m_cabeza · r_cuello · (a_t + g)
M_cadera = m_piernas · r_cadera · (a_t + g)
```

Para `m_cabeza=5 kg`, `r_cuello=0.18 m`, `m_piernas=20 kg`, `r_cadera=0.45 m`
y `a_t=1555.2 m/s²`:

```
M_cuello = 5 × 0.18 × (1555.2 + 9.81) = 1408.5 N·m = 1.409 kN·m
M_cadera = 20 × 0.45 × (1555.2 + 9.81) = 14 085 N·m = 14.09 kN·m
```

En caída libre `a_t = −g` y ambos momentos son cero, como debe ser.

### A.6 Elasticidad y viabilidad

Para una barra elástica:

```
k = E A / L
E = k L / A
ε = x/L
σ = E ε
```

Criterios de viabilidad de la seda:

```
1 GPa ≤ E ≤ 10 GPa
ε ≤ 0.30
x ≤ 1.60 m
```

Los tres deben cumplirse. En el caso base falla `E`; en el escenario de 6 g
falla `x`; en la seda real falla `x`. Por eso la región factible es vacía.

### A.7 Impacto contra el suelo

Si `x_max > 1.60 m`, el torso impacta antes de detenerse. El instante se
obtiene resolviendo:

```
x(t) = 1.60
```

Como `x(t)` es monótona en `[0, t_pico]`, se puede usar bisección. La
velocidad de impacto se obtiene por energía:

```
v_imp² = v₀² + 2 g (1.60) − (k/m)(1.60)²
```

Para el escenario de 6 g con aire (`k=272.37 N/m`):

```
x_max = 12.606 m > 1.60 m
t_imp = 0.06378 s = 63.78 ms
v_imp = 25.21 m/s
```

Es decir: la seda apenas alcanza a frenar antes de que el torso llegue al
suelo.

### A.8 HIC

Para una aceleración `a` en g y una ventana `Δt`:

```
HIC = Δt · (a_media)^2.5,     Δt ≤ 36 ms
```

Para un pulso rectangular constante de altura `A` y duración `T`:

```
HIC = min(T, 0.036) · A^2.5
```

Caso base con `T=25.21 ms` y `A=158.58 g`:

```
158.58² = 25 147
158.58^2.5 = 25 147 × sqrt(158.58) = 316 700
HIC = 0.02521 × 316 700 ≈ 7 983
```

Con la forma real del pulso (triangular) el valor medido por el modelo baja a
≈5 115. El escenario de 6 g durante 0.86 s tiene `HIC ≈ 3.2` en la ventana de
36 ms; el valor ~70 que a veces se cita usa una ventana de 0.8 s, incompatible
con la definición.

### A.9 Resolución manual completa: tabla de pasos

| Paso | Fórmula | Resultado base |
|---|---|---:|
| 1 | `c = ½ρCdA` | 0.36 kg/m |
| 2 | `v_t = sqrt(mg/c)` | 36.91 m/s |
| 3 | `t_f = (v_t/g) arccosh(e^{gH/v_t²})` | 3.0757 s |
| 4 | `v₀ = v_t tanh(g t_f/v_t)` | 24.866 m/s |
| 5 | `k = m(v₀²+2gx)/x²` | 195 679 N/m |
| 6 | `ω = sqrt(k/m)` | 62.559 rad/s |
| 7 | `t_pico = (π−atan(v₀ω/g))/ω` | 25.21 ms |
| 8 | `a_max = sqrt(g²+(k/m)v₀²)` | 158.58 g |
| 9 | `F_max = kx` | 78.27 kN |
| 10 | `E = ½mv₀²+mgx` | 15.65 kJ |
| 11 | `P_max = max(kxẋ)` | 0.976 MW |
| 12 | `E_seda = kL/A` | 328.74 GPa |
| 13 | `ε = x/L` | 0.952 % |
| 14 | `M_cuello = m r (a_t+g)` | 1.409 kN·m |
| 15 | `HIC` (pulso constante) | ≈7 983 |

### A.10 Leicester a mano (sin aire)

```
v₀ = sqrt(2 × 9.81 × 42) = 28.706 m/s
```

Para `a_max=6 g`, se despeja `k` de `a_max² = g² + (k/m)v₀²`:

```
36g² = g² + (k/m)v₀²
k = 35 m g² / v₀²
  = 35 × 50 × 9.81² / 28.706²
  = 204.375 N/m
```

El estiramiento sale de la energía:

```
k x² − 2 m g x − m v₀² = 0
x = 16.80 m
```

Con `v₀²=2gH`, la ecuación se simplifica a `35x²−4Hx−4H²=0`, cuya raíz
positiva es `x=0.4H=16.8 m`. Entonces:

```
E_seda = kL/A = 204.375 × 42 / 2.5×10⁻⁵ = 343.35 MPa
ε = 16.8/42 = 40.0 %
```

Éste es el caso del paper. La diferencia 16.8 vs 16.7 es redondeo.

### A.11 Escenario de 6 g con aire a mano

Primero se calcula `v₀=24.866 m/s` como en A.3.2. Luego:

```
k = 35 m g² / v₀²
  = 35 × 50 × 9.81² / 24.866²
  = 272.37 N/m
x = [mg + sqrt((mg)² + k m v₀²)] / k
  = 12.606 m
ε = 12.606/42 = 30.01 %
E_seda = 272.37 × 42 / 2.5×10⁻⁵ = 457.6 MPa
E_absorbida = ½mv₀² + mgx = 21.64 kJ
```

Aunque `E_seda` está dentro del rango permisivo, `x=12.6 m` excede el espacio
libre de 1.6 m y la deformación del 30 % está en el límite de rotura.

### A.12 Seda real: barrido manual

Con `A=2.5×10⁻⁵ m²`, `L=42 m` y `v₀=24.866 m/s`:

| `E` (GPa) | `k` (N/m) | `x` (m) | `ε` | `a_max` (g) | `v_imp` a 1.6 m (m/s) |
|---:|---:|---:|---:|---:|---:|
| 1 | 595.2 | 8.08 | 19.2 % | 8.80 | 24.88 |
| 5 | 2 976.2 | 3.39 | 8.08 % | 19.58 | 22.30 |
| 10 | 5 952.4 | 2.36 | 5.63 % | 27.67 | 18.57 |

Ninguna opción evita el suelo (`x>1.6 m`) y todas superan los 6 g. Ésa es la
demostración numérica de que el problema no se arregla eligiendo otra seda.

### A.13 Cómo se resuelve con los métodos numéricos

| Problema | Método | Archivo | Tolerancia |
|---|---|---|---|
| `t_f`: raíz de `y(t)−H` | bisección, falsa posición, secante | `simulador/raices.py` | `1e-12` |
| `t_impacto`: raíz de `x(t)−1.6` | bisección | `simulador/raices.py` | `1e-12` |
| `k` crítico de 6 g | Newton / bisección | `simulador/raices.py` | `1e-9` |
| Validar la caída | Euler, Heun, RK4, RKF45 | `simulador/edo.py` | `1e-8` |
| Rigidez del resorte | Euler implícito | `simulador/edo.py` | estable |
| Energía e impulso | trapecio, Simpson, Gauss, Romberg | `simulador/integracion.py` | `1e-10` |
| Sistema articulado | LU, Thomas, Jacobi, Gauss-Seidel | `simulador/lineales.py` | `1e-10` |
| Orientación `θ(t)` | spline cúbico | `simulador/interpolacion.py` | `1e-6` |

La forma cerrada se usa para la app y las figuras; los métodos numéricos se
usan para validar, comparar órdenes de convergencia y resolver los casos que
no tienen forma cerrada (impacto, material no lineal, Monte Carlo).

### A.14 Errores comunes al resolverlo a mano

1. **Usar `F_max·v₀` como potencia.** La fuerza máxima y la velocidad máxima
   no coinciden. Hay que maximizar `P(t)=kxẋ`.
2. **Usar 20.8 kJ con aire.** Con aire el cuerpo recibe 15.65 kJ; 20.8 kJ es
   la cota sin arrastre.
3. **Calcular `t_pico` con `atan2(v₀ω,g)`.** El primer cero de la velocidad
   es `(π−atan(v₀ω/g))/ω`.
4. **Usar una ventana de HIC de 0.86 s.** La definición exige ≤36 ms.
5. **Confundir el rango de `E` con la viabilidad.** Un módulo dentro de rango
   no basta: también deben cumplirse `ε≤30 %` y `x≤1.6 m`.
6. **Comparar `x=16.8 m` con `0.4 m`.** La comparación física es contra el
   espacio libre de 1.60 m.
7. **Decir que `a_max` no depende de la altura.** Depende de `v₀`, y `v₀`
   depende de la altura y del arrastre.
8. **Aplicar HIC al torso sin aclararlo.** HIC es un criterio de cabeza; en
   este proyecto se usa como índice comparativo.

## 8. Referencias

- Universidad de Leicester, *The physics of Gwen Stacy's fall* (2021).
- Marvel, *The Amazing Spider-Man* #125, correo de lectores (latigazo).
- Burden & Faires, *Análisis numérico* (métodos de raíces, EDO e integración).
- Chapra & Canale, *Métodos numéricos para ingenieros*.
- Datos antropométricos aproximados para los segmentos corporales.
