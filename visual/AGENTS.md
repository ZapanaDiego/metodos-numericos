# Planos de las 14 capturas
1–2. Cámara de seguimiento, brazos abiertos y caída dorsal en tres cuartos.
3–4. La punta de la seda se aproxima por el interior de la torre.
5. El abanico de seda se une al abdomen.
6. Perfil dorsal, dirección de tensión casi vertical.
7–9. Cámara baja con el piso visible. La proximidad de la cabeza motiva el escenario alternativo. El contacto de pies queda indeterminado.
10–13. El abdomen elevado y los segmentos rezagados guían la pose de retorno.
14. Vista de torre para comparar ancla, tensado y suelo.
El visor interpola un Resultado por tiempo físico. Los tiempos cinematográficos y los ángulos de pose son estimados.

Estado. app_panda3d.py implementa el visor con Panda3D 1.10.16 y un personaje
procedural. El mapa de datos y el benchmark en ventana están en
docs/panda3d.md.

Panel del laboratorio. panel_panda3d.py conserva las coordenadas de diseño en
1100 × 700. El DisplayRegion 3D se ajusta a la misma escala. Las gráficas
comparten el reloj con la escena. En pausa, el arrastre rota alrededor del
punto de mira de cada vista y la rueda cambia su distancia. Evidencia en
resultados/panda_captura.png y tests/test_panel_panda3d.py.

El evento de ventana llama primero a ShowBase.windowEvent para actualizar
pixel2d. Después se recalcula el encuadre del DisplayRegion con el tamaño
efectivo. El catálogo de Linux usa scripts/instalar_lanzador.py.

laboratorio_datos.py abre la corrida activa en una ventana independiente.
Comparte el eje temporal entre gráficas y filtra las muestras por intervalo.
animacion.avanzar_reloj aplica cámara lenta desde el evento de tensado.

Personaje 3D y daños (A1–A6). `mallas_panda3d.py` construye geometría orgánica
suavizada (`V3n3c4`) y `personaje_panda3d.py` arma la figura femenina articulada
(cabeza/rostro, melena de 3 tramos, codos, rodillas y tobillos) respetando los
pivotes y radios de `simulador/mediciones.py`. Al llegar a `self.fin`, el reloj
físico `self.t` y todas las lecturas/gráficas quedan fijos mientras `self.t_dano`
reproduce el desenlace de daño según `self.contacto` (latigazo cervical en aire,
impacto craneal o colapso de piernas con grietas, ondas y astillas sobre `piso`).
Evidencia en `resultados/panda_captura.png` y `tests/test_panel_panda3d.py`.
