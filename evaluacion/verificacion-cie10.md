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

| Código | Lo emitió | ¿Existe en CIE-10-ES? | ¿Aplica a este caso? | Veredicto |
|---|---|---|---|---|
| `B96.2` | 27B | | | |
| `E11.31` | 27B | | | |
| `E11.9` | 3B | | | |
| `F17.9` | 3B | | | |
| `H36.0` | 27B | | | |
| `I10` | 3B, 8B, 27B | | | |
| `I12.0` | 3B | | | |
| `I48.0` | 8B | | | |
| `I48.2` | 27B | | | |
| `I48.9` | 3B | | | |
| `I50.21` | 8B | | | |
| `I50.23` | 27B | | | |
| `I50.31` | 3B | | | |
| `J41.9` | 3B | | | |
| `J44.0` | 8B | | | |
| `J44.9` | 3B, 27B | | | |
| `J96.0` | 8B | | | |
| `J96.21` | 27B | | | |
| `K50.2` | 8B | | | |
| `K50.9` | 3B | | | |
| `N18.5` | 8B | | | |
| `Z87.890` | 8B | | | |

**Veredicto:** `correcto alternativo` / `existe pero no aplica` / `NO EXISTE`.

Los 22 códigos de arriba son los que emitieron los modelos y no están ni en el
patrón ni entre los discutibles. La tabla la genera
`python3 scripts/evaluar.py --tarea 4 --detalle` en el campo `_sobrantes`.

**Para la captura de la charla** (`11-ecie-sin-resultados.png`) busque primero
los que tienen pinta de subcategoría inventada o de código no facturable, que
son donde es más probable el «sin resultados»: `J41.9`, `I48.9`, `F17.9`,
`K50.9`, `E11.9`, `J96.0`, `B96.2`, `I48.2`. Con uno que no exista basta: la
diapositiva necesita **una** captura del buscador vacío.

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
