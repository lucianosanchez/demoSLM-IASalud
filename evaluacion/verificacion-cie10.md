# Verificación manual de los códigos CIE-10

Este fichero se rellena a mano. Es el paso que no se puede automatizar y el que
sostiene el argumento central de la tarea 4.

## Parte 1 — Validación del patrón

Antes de la charla, un técnico de documentación clínica debe revisar los 16
códigos de `gold-04-cie10.json`.

| # | Código propuesto | ¿Correcto? | Corrección | Comentario del codificador |
|---|---|---|---|---|
| 1 | I13.0 | | | ¿Se aplica la norma de combinación HTA + cardiopatía + ERC? |
| 2 | I50.33 | | | ¿Crónica agudizada o sólo crónica? |
| 3 | N18.4 | | | |
| 4 | J44.1 | | | ¿J44.0 estaría mal, siendo la infección urinaria? |
| 5 | J96.22 | | | |
| 6 | N39.0 | | | |
| 7 | B96.20 | | | |
| 8 | Z16.12 | | | |
| 9 | E11.22 | | | |
| 10 | E11.319 | | | ¿Sin gravedad especificada? |
| 11 | I48.21 | | | |
| 12 | K50.00 | | | ¿Se codifica una enfermedad en remisión sin tratamiento? |
| 13 | Z87.891 | | | |
| 14 | Z99.81 | | | |
| 15 | Z79.01 | | | |
| 16 | Z79.4 | | | |

**Secuenciación:** ¿cuál es el diagnóstico principal y por qué? _______________

**Si el codificador discrepa en dos o más códigos, dígalo en la charla.** Que dos
profesionales codifiquen distinto el mismo informe es información valiosa sobre
qué significa «acierto» cuando se lo exigimos a una máquina.

## Parte 2 — Códigos emitidos por los modelos

Para cada código que aparezca en `_sobrantes` de `evaluar.py --tarea 4 --detalle`,
búsquelo en <https://eciemaps.sanidad.gob.es/> y anote el resultado.

| Modelo | Código emitido | ¿Existe en CIE-10-ES? | ¿Aplica a este caso? | Veredicto |
|---|---|---|---|---|
| 3B | | | | |
| 3B | | | | |
| 3B | | | | |
| 8B | | | | |
| 8B | | | | |
| 8B | | | | |
| 27B | | | | |
| 27B | | | | |
| 27B | | | | |

**Veredicto:** `correcto alternativo` / `existe pero no aplica` / `NO EXISTE`.

Sólo la última categoría es alucinación en sentido estricto, y es la única cifra
que debe proyectar como tal. Es tentador contar los otros dos casos como fallo:
no lo haga, porque alguien del público sabrá distinguirlos y perderá usted la
credibilidad de toda la charla por dos décimas de una tabla.

### Resumen para la diapositiva

| Modelo | Códigos emitidos | Correctos | Existen pero no aplican | **No existen** |
|---|---|---|---|---|
| 3B | | | | |
| 8B | | | | |
| 27B | | | | |
