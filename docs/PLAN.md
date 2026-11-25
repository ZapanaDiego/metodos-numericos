# Laboratorio de Euler y Runge–Kutta

Cada fila se cierra con pruebas o un artefacto reproducible. Las decisiones físicas del escenario base están en el AGENTS.md raíz.

| Iteración | Entrega | Evidencia prevista |
|---|---|---|
| 01 | Contexto por área | Línea base de 112 pruebas aprobadas y una GUI omitida sin pantalla |
| 02 | Estabilidad de Euler | e2 |
| 03 | Caída numérica | Prueba de convergencia |
| 04 | Evento de tensado | Error temporal |
| 05 | Frenado | Primer cero de velocidad |
| 06 | Coste y error | e11 |
| 07 | Contrato de datos | simular |
| 08 | Ventana Panda3D | Prueba de render |
| 09 | Torre y reloj | Escala métrica |
| 10 | Personaje dorsal | Captura lateral |
| 11 | Seda y cámaras | Tres vistas |
| 12 | Controles | Comparación por paso |
| 13 | Balance energético | Residuo en julios |
| 14 | Momentos | Perfil articular |
| 15 | Dinámica segmentaria | Energía cinética |
| 16 | Contacto | Primer evento localizado |
| 17 | Absorción | Alcance documentado |
| 18 | Rendimiento | FPS y percentil 95 |
| 19 | Sustentación | README, láminas y suite |

## Estado de cierre

Las iteraciones 01–07 se verifican con e2, e11 y test_caida_euler_rk4.py.
La captura y el manual de Panda3D cubren 08–12 y 18. Las iteraciones 13–16
se verifican con el balance y los casos base, cabeza y piernas. En 17 se
publica energía incidente porque la absorción corporal es indeterminada.
La entrega 19 enlaza el laboratorio desde el README y la sustentación.

## Revisión de interfaz del laboratorio

| Iteración | Entrega verificada |
|---|---|
| 01 | Región 3D separada del panel, revisada a 1100 × 700 y 900 × 600 |
| 02 | Controles agrupados, método activo y tamaño de paso visible |
| 03 | Giro y acercamiento anclados en pausa para las tres cámaras |
| 04 | Lecturas con etiquetas, unidades y precisión del error |
| 05 | Velocidad de la caída y ampliación alrededor del tensado |
| 06 | Tensión con ejes y cursores sincronizados |
| 07 | EDO activa, pendiente de Euler y cuatro pendientes de RK4 |
| 08 | Captura, manual, pruebas de regresión y benchmark de 60.0 FPS |

## Mejora visual del personaje 3D y daños (Panda3D)

| Iteración | Entrega verificada |
|---|---|
| A1 | Motor de mallas suaves `V3n3c4` (`visual/mallas_panda3d.py`), materiales e iluminación de 3 puntos |
| A2 | Personaje femenino 3D anatómico articulado (`visual/personaje_panda3d.py`): rostro, cabello, gabardina y botas |
| A3 | Caída dorsal aerodinámica, abanico de seda sincronizado al tensado y frenado con inercia secundaria |
| A4 | Sistema de daños en cuerpo y piso con sub-reloj `t_dano` sin alterar `t`, lecturas ni cursores |
| A5 | Tres desenlaces diferenciados: latigazo cervical en aire, trauma craneal (+1.00 m) y colapso de piernas (+0.85 m) |
| A6 | Pruebas de geometría y sincronización, captura `resultados/panda_captura.png` y 411.7 FPS (p95 3.4 ms) |

## Centralización de variables del modelo

| Iteración | Entrega verificada |
|---|---|
| V1 | Módulo único `simulador/variables.py` con variables primarias, constantes de las EDO y contenedor `VARIABLES_BASE` |
| V2 | Instanciación en `simulador/` (`parametros`, `analitica`, `modelo`, `mediciones`, `articulado`, `elasticidad`, `energia`, `raices`, `validacion`, `estocastico`) |
| V3 | Instanciación en `visual/` (`app_panda3d`, `personaje_panda3d`, `laboratorio_datos`, `parametros_vista`, `escena3d`) y `experimentos/e11_caida.py` |
| V4 | Suite completa y `tests/test_variables.py` en verde sin alterar valores golden de `datos/referencia.csv` |
