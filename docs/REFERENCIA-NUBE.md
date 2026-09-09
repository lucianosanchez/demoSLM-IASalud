# El techo de referencia: un modelo grande en la nube


> ## Aviso sobre la referencia incluida en `resultados/`
>
> El repositorio trae una columna `Opus5` ya rellenada. **No es una medición
> ciega**: esas salidas se produjeron en la misma sesión de trabajo en la que se
> revisaron los patrones de `evaluacion/`, de modo que el modelo los había visto.
> Sirven para enseñar el techo de lo que cada tarea admite —que la 4 y la 5
> tienen solución, y cuál es—, no para comparar con los modelos locales, que se
> ejecutaron a ciegas.
>
> Si necesita una referencia con valor comparativo, repita el protocolo de abajo
> en una sesión limpia y sustituya los ficheros `*__Opus5.*`.


## Qué es y por qué se puede hacer

Un modelo de frontera ejecutando las mismas cinco tareas sobre el mismo informe
marca el **techo absoluto**: lo mejor que hoy se puede obtener de un modelo de
lenguaje en estas tareas, sin restricción de tamaño ni de hardware.

Se puede hacer **porque el informe es sintético, y sólo por eso**. Ninguno de los
datos corresponde a una persona real, de modo que enviarlo a un servicio externo
no es un tratamiento de datos personales. Ese es, exactamente, el motivo por el
que el repositorio empieza con un informe generado y no con uno real anonimizado.

Dicho de otra manera: la columna de referencia existe gracias a la misma decisión
de diseño que hace que la demostración sea conforme al Decreto 98/2025. Conviene
señalarlo en voz alta, porque refuerza el argumento en lugar de contradecirlo.

## Qué aporta a la charla

Tres cosas, en orden de valor:

1. **Cierra la objeción del tamaño.** Si un modelo de frontera también falla en la
   tarea 4 —y falla, aunque menos—, la conclusión deja de ser «hace falta un
   modelo mayor» y pasa a ser «hace falta recuperación sobre la tabla». Eso es
   mucho más difícil de rebatir que cualquier argumento sobre parámetros.
2. **Separa lo que es cuestión de tamaño de lo que no.** En las tareas 1 a 3 la
   referencia estará por encima del 27B, pero por poco: es la confirmación de que
   ahí el tamaño rinde poco. En la 4 y la 5 la distancia será mayor, y aun así
   insuficiente para el umbral de uso real.
3. **Da una cifra de coste de oportunidad.** Es lo que se renuncia a tener por
   procesar en local. Ponerle número es más honesto que decir que no se pierde
   nada.

## Cómo se ejecuta

**Antes de la charla, nunca en directo.** La demostración se hace con la red
apagada y esa coreografía no debe romperse. La referencia se ejecuta días antes y
se proyecta como captura.

1. Abrir la interfaz web del modelo de frontera que se quiera usar como techo.
2. Para cada tarea, pegar el prompt de sistema y el mensaje de `prompts/` con el
   informe incrustado — son exactamente los mismos que se usan en local, y eso es
   parte del control experimental.
3. Chat nuevo para cada tarea, igual que en LM Studio.
4. Guardar la salida en `resultados/` con la etiqueta `referencia`, respetando la
   convención de nombres: `01-anonimizacion__referencia.txt`,
   `02-extraccion__referencia.json`, etc. Así `scripts/evaluar.py` la puntúa junto
   con las demás sin ninguna modificación.
5. Crear a mano el `.meta.json` correspondiente, con al menos:

```json
{"tarea": "04-codificacion-cie10", "etiqueta": "referencia",
 "modelo": "[nombre y versión exactos]",
 "tokens_por_segundo": null, "segundos": null,
 "momento": "2026-01-01T00:00:00",
 "nota": "ejecutado en la interfaz web, sobre informe sintético"}
```

## Precauciones

- **Anote el nombre y la versión exactos del modelo y la fecha.** Los modelos de
  frontera cambian sin aviso y una cifra sin versión no es reproducible ni por
  usted.
- **No compare tokens por segundo.** La velocidad de un servicio en la nube
  depende de la carga, del lote en que le haya tocado y del hardware del
  proveedor. Comparar esa cifra con la de un portátil no significa nada. Deje el
  campo a `null`.
- **Es una sola ejecución sobre un solo informe.** Vale como referencia
  cualitativa, no como medición.
- **La salida estructurada puede no ser equivalente.** Si la interfaz web no
  permite imponer el esquema JSON, la comparación de la tarea 2 y de la 4 no es
  estrictamente pareja. Anótelo.
- **No presente la referencia como una opción disponible.** Es el techo teórico.
  Con un informe real no se puede usar, y ése es el punto de partida de toda la
  charla.

## Tabla para rellenar

| Tarea | Métrica principal | 3B | 8B | 27B | Referencia (nube) | Umbral |
|---|---|---|---|---|---|---|
| 1 Anonimización | recall / falsos positivos | | | | | 100 % / 0 |
| 2 Extracción | F1 medicación / alucinaciones | | | | | 0,95 / 0 |
| 3 Reescritura | cobertura crítica / cifras | | | | | 13/13 / 0 |
| 4 Codificación | código completo / inexistentes | | | | | 0,90 / 0 |
| 5 Razonamiento | detectadas / falsas alarmas | | | | | 3/3 / 0 |

Modelo de referencia: ______________________ Versión: __________ Fecha: __________

## La frase de la diapositiva

> La columna de la derecha es el techo. No está disponible para un informe real,
> porque para obtenerla hay que enviar el documento. Y aun teniéndola, la tarea 4
> sigue sin llegar al umbral.
