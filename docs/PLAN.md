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
