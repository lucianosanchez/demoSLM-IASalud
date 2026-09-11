# Modelos de lenguaje pequeños en local: qué se pierde y qué se gana

Material de la demostración presentada en **IAS 2026**
(<https://asturiasias.github.io/ias2026/>) por Luciano Sánchez.

**Cinco tareas clínicas de dificultad creciente sobre un mismo informe de alta,
en tres tamaños de modelo, ejecutadas en local y sin conexión a la red.**

### 👉 [Ver los resultados](RESULTADOS.md) · [el informe de alta](informes/informe-alta-001.txt) · [los prompts](prompts/) · [la presentación en PDF](presentacion/demo-slm-local.pdf)

El informe es **sintético**: ningún dato corresponde a una persona real. Por eso
se puede publicar entero, y por eso se pudo ejecutar la referencia en la nube.

---

## Las cinco tareas

| # | Tarea | Qué exige de verdad | Tamaño mínimo |
|---|---|---|---|
| 1 | Anonimización / seudonimización | Reconocer entidades | 3B |
| 2 | Extracción estructurada | Leer y ordenar | 3B–8B |
| 3 | Reescritura para el paciente | Reformular sin perder nada | 8B–27B |
| 4 | Codificación CIE-10-ES | **Recordar una tabla de 70.000 códigos** | ninguno basta |
| 5 | Razonamiento clínico | **Aplicar conocimiento ausente del texto** | ninguno basta |

La tarea 1 es la única en la que un modelo local no es una preferencia sino la
única opción posible: para anonimizar un texto hay que enviarlo sin anonimizar.

### El trazador

El informe lleva **una prescripción al alta contradicha por sus propias pruebas**:
amoxicilina-clavulánico en un paciente con alergia documentada a betalactámicos y
con un antibiograma que informa resistencia a ese mismo antibiótico.

Ese único dato se sigue a través de las cinco tareas, y **su comportamiento
correcto es opuesto según la tarea**:

| Tarea | Qué debe hacer con él | Porque mide |
|---|---|---|
| 1 Anonimización | conservarlo intacto | fidelidad documental |
| 2 Extracción | extraerlo tal cual | fidelidad documental |
| 3 Reescritura | contárselo al paciente sin comentarios | fidelidad documental |
| 4 Codificación | no le afecta | se codifican diagnósticos, no tratamientos |
| 5 Razonamiento | **señalarlo** | validación clínica |

Un modelo que en la tarea 3 escriba «no tome este antibiótico, usted es alérgico»
tiene razón **y ha incumplido el contrato**. Ésa es la diferencia entre
transformar un texto y validarlo, y es medible:

```bash
make trazador
```

Toda la evidencia necesaria está dentro del informe, así que cuando la tarea 5
no lo detecta no vale la excusa de que el modelo no sabe medicina. Definición
completa en [`evaluacion/trazador.json`](evaluacion/trazador.json).

---

## Puesta en marcha

### 1. LM Studio

Instale [LM Studio](https://lmstudio.ai), descargue los tres modelos indicados en
[`docs/MODELOS.md`](docs/MODELOS.md) —la mejor cuantización que le quepa— y arranque el
servidor local:

```bash
lms server start
lms ls
```

O, en la interfaz: pestaña *Developer* → *Start Server*.

### 2. Comprobar la conexión

```bash
make comprobar
```

Debe listar los modelos cargados. Los identificadores que devuelve son los que
hay que pasar en `--modelo`.

### 3. Ejecutarla entera y compilar la charla

Generar las ejecuciones, la tabla
y el PDF:

```bash
make todo
```

Con sus propios modelos:

```bash
make todo MODELO_3B=<el suyo> MODELO_8B=<el suyo> MODELO_27B=<el suyo>
```

Son 15 ejecuciones (3 modelos × 5 tareas). Cargue los modelos **de uno en
uno**: si LM Studio mantiene los tres en memoria, los tokens/s que mida no serán
los reales.

En 32 GB —un Mac de memoria unificada o
un PC con NVIDIA— cabe el mismo 27B **a 4 bits** con 16k de contexto: unos 20 GB.
Lo único que se pasa por la API es el presupuesto de salida:

```bash
make todo MAX_TOKENS=16384
```

Si no cabe en la ventana del modelo, el script lo recorta y lo dice. La tabla
comparativa está en [`docs/MODELOS.md`](docs/MODELOS.md).

Si su modelo grande razona, gastará muchos más tokens de los que devuelve y la
tanda puede irse a varias horas.


---

## Qué hay en cada sitio

```
informes/       El informe de alta sintético
prompts/        Los cinco prompts, con sus parámetros y notas para el ponente
  schemas/      Los esquemas JSON que convierten el prompt en un contrato
evaluacion/     Los patrones de oro, el trazador, la rúbrica y la verificación CIE-10
scripts/        ejecutar.py, evaluar.py, hardware.py — sin dependencias
resultados/     Salidas de los modelos y sus .meta.json (trazabilidad)
presentacion/   La charla en Beamer
  extractos/    El texto que se proyecta, recortado de resultados/ (generado)
  img/          Las cuatro capturas de pantalla que hay que hacer a mano
docs/           MODELOS.md, REFERENCIA-NUBE.md, CAPTURAS.md
```

---

## Hardware: 

```bash
make hardware
python3 scripts/hardware.py --params 70 --ancho-banda 100
```

**Memoria.** En cuantización de 4 bits, ~0,6 GB por cada mil millones de
parámetros, más el contexto. 8B ≈ 5 GB · 27B ≈ 17 GB · 70B ≈ 42 GB. A 8 bits,
el doble. Y la caché KV sin cuantizar cuesta unos 7 GB en un 27B con 32k de
contexto.

**Velocidad.** Generar un token obliga a leer todos los pesos, así que

```
tokens/s = ancho de banda de la memoria (GB/s) / tamaño del modelo (GB)
```

En la práctica se alcanza entre el 50 % y el 80 % de ese techo. 

---

## Marco normativo

La demostración está construida para ser conforme al **Decreto 98/2025** del
Principado de Asturias:

- El informe es **sintético**: ningún dato corresponde a una persona real.
- Cada ejecución deja un `.meta.json` con modelo, parámetros, tiempos y tokens
  (art. 17.3.a, registro automático de eventos).
- La rúbrica fija umbrales explícitos por debajo de los cuales el sistema no se
  despliega (art. 3.h, supervisión humana; art. 12, verificación previa).
- La tarea 5 termina en retirada del modelo (art. 29).

Al usarse un modelo local, el art. 23 (encargado del tratamiento,
subencargados, ubicación de los datos, transferencias) se cumple. 

---
