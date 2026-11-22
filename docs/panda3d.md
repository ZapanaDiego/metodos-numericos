# Visor Panda3D

En Linux, abre **Gwen Stacy - Simulador 3D** desde el catálogo de aplicaciones.
Para registrar esa entrada en otra cuenta o después de mover el proyecto,
ejecuta `.venv/bin/python scripts/instalar_lanzador.py` desde la raíz del
repositorio.

```bash
.venv/bin/python -m visual.app_panda3d
.venv/bin/python -m visual.app_panda3d --ventana --medir 180
.venv/bin/python -m visual.app_panda3d --captura resultados/panda_captura.png
```

## Controles

**Ir al tensado** pausa la simulación en el agarre y abre la vista lateral.
**Avanzar un paso** recorre la malla del integrador y sus fronteras de fase.
**Método de integración** selecciona Euler o RK4 para la misma EDO por fase.
Los botones **-** y **+** cambian el tamaño de paso entre 0.25 y 8 ms.
**Escenario** recorre el caso base y los dos ejemplos de contacto.

Con la reproducción en pausa, arrastra horizontalmente dentro de la escena
para girar la cámara alrededor del punto de mira de **Seguir**, **Cuerpo** o
**Torre**. La rueda cambia la distancia a ese mismo punto. **Restablecer
cámara** vuelve al encuadre inicial. Al reanudar, la vista recupera su
seguimiento habitual.

La gráfica de velocidad recorre la caída completa en segundos. **Ampliar
frenado** cambia a una ventana en milisegundos alrededor del tensado de
la corrida activa. La gráfica de fuerza está alineada por tiempo desde el
tensado de cada corrida. El marcador ámbar de altura y el error del panel
usan tiempo absoluto desde el inicio. La línea blanca de cada gráfica
marca el tiempo actual, mientras que las líneas de evento indican el
tensado o el primer cero de velocidad.

**Ver EDO** muestra la ecuación de la fase activa. En pausa, también enseña
la pendiente de Euler o las cuatro pendientes de RK4 para el paso que
empieza en la última muestra de integración alcanzada. El cálculo de las
etapas comparte la función del integrador RK4.

**Gráficas y tablas** abre el laboratorio de datos. La velocidad y la tensión
usan el mismo eje de tiempo físico desde el inicio. Se puede ampliar con la
rueda, desplazar con la barra de herramientas y filtrar la tabla al intervalo
visible. El laboratorio abre con el método, el paso y el escenario actuales.

## Datos y render

`simulador.modelo.simular()` devuelve un `Resultado` con muestras en segundos,
posición y elongación en metros, velocidad positiva hacia abajo, aceleración
positiva hacia arriba, fuerza en newtons y potencia en vatios. El frenado pasa
a fase elástica en `t_tensado_s`; `t_pico_s` es relativo a ese evento.
`tiempos_pasos_s` conserva la malla para el botón Paso. La serie que se dibuja
incluye también instantes de interés como el pico de potencia.

El visor prepara una corrida al cambiar un control. La tarea Panda3D interpola
esa corrida y los perfiles segmentarios usando un reloj de reproducción.
Las muestras y los eventos conservan su tiempo físico. El reloj mantiene
la velocidad de reproducción normal antes del tensado y pasa al 5 % al
activarse el agarre.

Al abrir o redimensionar la ventana, Panda3D actualiza la escala de la
interfaz y el visor aplica el mismo encuadre al render 3D. El panel se
mantiene a la derecha en ventanas flotantes y en mosaico.

La gravedad apunta hacia −Z en el mundo. En el personaje, +X apunta hacia la
cabeza y +Z hacia el frente. El nodo raíz representa el agarre abdominal.
La malla procedural se compone de volúmenes articulados bajo nodos de cuello,
cadera y hombros. La pose previa al tensado y el vuelo de la seda son recursos
visuales. Los giros de cabeza y piernas durante el frenado salen de los dos
osciladores de `simulador/mediciones.py`. La cámara lateral y el piso hacen
visible el orden de los eventos. Los volúmenes gráficos y la geometría
simplificada de contacto se aproximan mediante dimensiones explícitas.

## Contacto y alcance

El piso del caso base está en Z = 0. En las alternativas se coloca en +1.00 m
con las piernas elevadas inicialmente 0.50 rad, o en +0.85 m con la postura
inicial horizontal. Son experimentos paramétricos. El primer contacto
monitoreado se localiza por interpolación del cruce con el piso. En ese punto
se detiene la reproducción del escenario alternativo.

La energía incidente de un segmento suma la traslación del centro de masa
y la rotación alrededor de ese centro. Con RK4 y h = 1 ms, se estiman 0.934 kJ
para cabeza en el primer alternativo y 4.841 kJ para piernas en el segundo.
Estas cifras corresponden a corridas distintas. La geometría, las inercias y
las constantes articulares son estimadas. La absorción por el cuerpo y el piso
queda indeterminada con el modelo disponible.

## Rendimiento

El benchmark recorre el tramo de frenado con personaje, seda, medidas, gráfica
y HUD activos. En ventana a 1100×700, AMD Radeon 860M, 180 cuadros, registró
60.0 FPS y 17.1 ms en el percentil 95. La prueba de búfer sin ventana sirve
para verificar renderizado y capturas en sistemas sin acceso a pantalla.
