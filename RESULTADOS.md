# Resultados

Todo lo que hay aquí lo genera `make todo`: son las salidas literales de los
modelos sobre el mismo informe, con los mismos prompts.

## De un vistazo

| Tarea | Métrica | 3B | 8B | 27B | Opus5 |
|---|---|---|---|---|---|
| 1 Anonimización | identificadores detectados (de 46) | 30/46 | 33/46 | 46/46 | 46/46 |
| 2 Extracción estructurada | campos correctos (de 14) | 13/14 | 14/14 | 14/14 | 14/14 |
| 3 Reescritura para el paciente | mensajes críticos (de 13) | 11/13 | 12/13 | 13/13 | 13/13 |
| 4 Codificación CIE-10-ES | códigos exactos (de 16) | 1/16 | 2/16 | 5/16 | 16/16 |
| 5 Revisión de coherencia | incoherencias detectadas (de 3) | 1/3 | 2/3 | 3/3 | 3/3 |
| | **tok/s medios** | 80 | 60 | 22 | — |

> La columna **Opus5** es un techo de referencia y **no es una medición ciega**:
> se produjo con los patrones de evaluación a la vista. Dice qué admite cada
> tarea, no cuánto separa a un modelo de otro. Ver
> [`docs/REFERENCIA-NUBE.md`](docs/REFERENCIA-NUBE.md).

## Las salidas, una por una

Cada celda enlaza con lo que el modelo devolvió, tal cual.

| Tarea | 3B | 8B | 27B | Opus5 |
|---|---|---|---|---|
| 1 Anonimización | [ver](resultados/01-anonimizacion__3B.txt) | [ver](resultados/01-anonimizacion__8B.txt) · [razonamiento](resultados/01-anonimizacion__8B.razonamiento.txt) | [ver](resultados/01-anonimizacion__27B.txt) · [razonamiento](resultados/01-anonimizacion__27B.razonamiento.txt) | [ver](resultados/01-anonimizacion__Opus5.txt) |
| 2 Extracción estructurada | [ver](resultados/02-extraccion__3B.json) | [ver](resultados/02-extraccion__8B.json) · [razonamiento](resultados/02-extraccion__8B.razonamiento.txt) | [ver](resultados/02-extraccion__27B.json) · [razonamiento](resultados/02-extraccion__27B.razonamiento.txt) | [ver](resultados/02-extraccion__Opus5.json) |
| 3 Reescritura para el paciente | [ver](resultados/03-reescritura__3B.txt) | [ver](resultados/03-reescritura__8B.txt) · [razonamiento](resultados/03-reescritura__8B.razonamiento.txt) | [ver](resultados/03-reescritura__27B.txt) · [razonamiento](resultados/03-reescritura__27B.razonamiento.txt) | [ver](resultados/03-reescritura__Opus5.txt) |
| 4 Codificación CIE-10-ES | [ver](resultados/04-codificacion-cie10__3B.json) | [ver](resultados/04-codificacion-cie10__8B.json) · [razonamiento](resultados/04-codificacion-cie10__8B.razonamiento.txt) | [ver](resultados/04-codificacion-cie10__27B.json) · [razonamiento](resultados/04-codificacion-cie10__27B.razonamiento.txt) | [ver](resultados/04-codificacion-cie10__Opus5.json) |
| 5 Revisión de coherencia | [ver](resultados/05-razonamiento-clinico__3B.json) | [ver](resultados/05-razonamiento-clinico__8B.json) · [razonamiento](resultados/05-razonamiento-clinico__8B.razonamiento.txt) | [ver](resultados/05-razonamiento-clinico__27B.json) · [razonamiento](resultados/05-razonamiento-clinico__27B.razonamiento.txt) | [ver](resultados/05-razonamiento-clinico__Opus5.json) |

## Cómo se leen estas cifras

Los patrones de oro con los que se puntúa están en [`evaluacion/`](evaluacion/),
con la justificación de cada elemento. La rúbrica y los umbrales de uso real,
en [`evaluacion/rubrica.md`](evaluacion/rubrica.md).

Para reproducirlo con sus propios modelos:

```bash
make todo MODELO_3B=<el suyo> MODELO_8B=<el suyo> MODELO_27B=<el suyo>
```
