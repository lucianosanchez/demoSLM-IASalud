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

| Código | Lo emitió | Veredicto | Por qué |
|---|---|---|---|
| `B96.2` | 27B | no facturable | categoría; exige 5.º carácter (B96.20/.21/.29) |
| `E11.31` | 27B | no facturable | exige 5.º carácter (E11.311/E11.319) |
| `E11.9` | 3B | no aplica | DM2 sin complicaciones; el paciente las tiene |
| `F17.9` | 3B | no facturable | la serie facturable es F17.2xx |
| `H36.0` | 27B | **NO EXISTE** | excluido en CIE-10-ES: la retinopatía diabética va en E11.3- |
| `I10` | 3B, 8B, 27B | no aplica | la norma de combinación obliga a I13.0 |
| `I12.0` | 3B | no aplica | hay insuficiencia cardíaca: I13.0 |
| `I48.0` | 8B | no aplica | paroxística; el informe dice permanente (I48.21) |
| `I48.2` | 27B | no facturable | exige 5.º carácter (I48.20/I48.21) |
| `I48.9` | 3B | no facturable | exige 5.º carácter (I48.91/I48.92) |
| `I50.21` | 8B | no aplica | sistólica aguda; aquí es diastólica crónica agudizada |
| `I50.23` | 27B | no aplica | sistólica crónica agudizada; aquí diastólica (I50.33) |
| `I50.31` | 3B | no aplica | diastólica aguda; aquí crónica agudizada (I50.33) |
| `J41.9` | 3B | **NO EXISTE** | la categoría J41 sólo tiene .0, .1 y .8 |
| `J44.0` | 8B | no aplica | EPOC con infección respiratoria baja; aquí es urinaria |
| `J44.9` | 3B, 27B | no aplica | sin exacerbación; el informe la documenta (J44.1) |
| `J96.0` | 8B | no facturable | exige 5.º carácter (J96.00/.01/.02) |
| `J96.21` | 27B | no aplica | con hipoxia; el informe dice hipercapnia (J96.22) |
| `K50.2` | 8B | **NO EXISTE** | la categoría K50 sólo tiene .0, .1, .8 y .9 |
| `K50.9` | 3B | no facturable | exige 5.º carácter (K50.90...) |
| `N18.5` | 8B | no aplica | estadio 5; el informe documenta estadio 4 |
| `Z87.890` | 8B | no aplica | historia de otras condiciones; nicotina es Z87.891 |

**Fuente y alcance.** Verificado contra ICD-10-CM, que es la clasificación de la
que deriva CIE-10-ES, consultando las tablas publicadas (septiembre de 2026).
**Falta el paso oficial**: comprobarlos en eCIE-Maps, porque la edición española
puede diferir en algún código y es la que rige aquí. Los tres marcados como
`NO EXISTE` son los que hay que buscar primero para la captura de la charla.

Tres categorías, y las tres importan por motivos distintos:

- **NO EXISTE** — el modelo se lo inventó. Es alucinación en sentido estricto.
- **no facturable** — el código existe como categoría pero no es válido para
  codificar: le falta el último carácter. En el CMBD es igual de inservible.
- **no aplica** — existe y es válido, pero no describe a este paciente.

### Recuento

| Modelo | Fuera del patrón | NO EXISTE | No facturable | Existe, no aplica |
|---|---|---|---|---|
| 3B | 9 | **1** (`J41.9`) | 3 | 5 |
| 8B | 8 | **1** (`K50.2`) | 1 | 6 |
| 27B | 8 | **1** (`H36.0`) | 3 | 4 |
| Opus 5 | 0 | 0 | 0 | 0 |

**Los tres modelos locales inventaron exactamente un código cada uno.** Ninguno
de los tres se repite entre modelos, y los tres tienen aspecto impecable.

### Resumen para la diapositiva

| Modelo | Códigos emitidos | Correctos | Existen pero no aplican | **No existen** |
|---|---|---|---|---|
| 3B | | | | |
| 8B | | | | |
| 27B | | | | |
