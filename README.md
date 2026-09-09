# Modelos de lenguaje pequeños en local: qué se pierde y qué se gana

Material de la demostración presentada en **IAS 2026**
(<https://asturiasias.github.io/ias2026/>) por Luciano Sánchez.

**Cinco tareas clínicas de dificultad creciente sobre un mismo informe de alta,
en tres tamaños de modelo, ejecutadas en local y sin conexión a la red.**

### 👉 [Ver los resultados](RESULTADOS.md) · [el informe de alta](informes/informe-alta-001.txt) · [los prompts](prompts/) · [la presentación en PDF](presentacion/demo-slm-local.pdf)

El informe es **sintético**: ningún dato corresponde a una persona real. Por eso
se puede publicar entero, y por eso se pudo ejecutar la referencia en la nube.

---
El mensaje de la demostración cabe en dos frases:

> Las tareas 1–3 consisten en extraer y reformular información **que ya está en
> el texto**. Las tareas 4–5 exigen conocimiento **que tiene que estar dentro de
> los pesos**. Los parámetros gastan memoria, y el tamaño importa muchísimo en
> unas tareas y casi nada en otras.

Todo lo que hay aquí se ejecuta en un portátil con LM Studio y Python 3 de
sistema. **No hay dependencias que instalar.**

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

Un solo comando hace **todo** y en el orden correcto —las ejecuciones, la tabla
y el PDF—:

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

**¿Y si su máquina es más modesta?** El contexto y la cuantización se eligen al
cargar el modelo en LM Studio, no aquí. En 32 GB —un Mac de memoria unificada o
un PC con NVIDIA— cabe el mismo 27B **a 4 bits** con 16k de contexto: unos 20 GB.
Lo único que se pasa por la API es el presupuesto de salida:

```bash
make todo MAX_TOKENS=16384
```

Si no cabe en la ventana del modelo, el script lo recorta y lo dice. La tabla
comparativa está en [`docs/MODELOS.md`](docs/MODELOS.md).

Si su modelo grande razona, gastará muchos más tokens de los que devuelve y la
tanda puede irse a varias horas.

Por partes, si prefiere ir viendo:

| Paso | Comando | Qué hace |
|---|---|---|
| 1 | `make demo` | Las 5 tareas en los 3 modelos, y puntúa |
| 2 | `make tabla` | `presentacion/tabla-resultados.tex` — **necesita el paso 1 hecho**, porque lee todo `resultados/` |
| 3 | `make presentacion` | Compila el PDF, que incorpora esa tabla |

Ese orden importa: la tabla resume lo que haya en `resultados/` en ese momento, y
el PDF incorpora la tabla que exista al compilar.

`make evaluar` y `make trazador` se pueden repetir cuando quiera: no vuelven a
llamar a ningún modelo, sólo releen `resultados/`.

El PDF compila **aunque no haya nada todavía**: cada hueco aparece como un
recuadro con el nombre del fichero que falta, y el `make` le enumera cuáles son.

Las diapositivas que enseñan salidas de los modelos no llevan capturas de
pantalla: leen el texto recortado de `resultados/` por `make extractos`, así que
se rellenan solas al ejecutar la demo. Capturas de verdad hacen falta cuatro, las
que este repositorio no puede producir —la ventana de LM Studio, su barra de
velocidad, el monitor de memoria y el «sin resultados» de eCIE-Maps—: están en
[`docs/CAPTURAS.md`](docs/CAPTURAS.md). El QR lo genera LaTeX; sólo hay que poner
la URL en `\newcommand{\urlrepo}{...}` al principio del `.tex`.

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

## Hardware: las dos reglas

```bash
make hardware
python3 scripts/hardware.py --params 70 --ancho-banda 100
```

**Memoria.** En cuantización de 4 bits, ~0,6 GB por cada mil millones de
parámetros, más el contexto. 8B ≈ 5 GB · 27B ≈ 17 GB · 70B ≈ 42 GB. A 8 bits,
el doble. Y la caché KV sin cuantizar cuesta unos 7 GB en un 27B con 32k de
contexto: no es un detalle, es la diferencia entre caber en un portátil o no.

Y el corolario que ahorra dinero: **antes de comprar memoria para meter un modelo
más grande, gaste la que ya tiene en servir mejor uno mediano.** Un 120B a 4 bits
ocupa 87 GB, va a 3–5 tok/s y responde peor que un 27B a 8 bits con contexto
amplio, que ocupa 36 GB y va a 9–14.

**Velocidad.** Generar un token obliga a leer todos los pesos, así que

```
tokens/s = ancho de banda de la memoria (GB/s) / tamaño del modelo (GB)
```

En la práctica se alcanza entre el 50 % y el 80 % de ese techo. De ahí sale la
conclusión que más dinero ahorra: **un servidor con 512 GB de RAM y sin GPU carga
un modelo de 70B y lo ejecuta a 1–2 tokens por segundo.** Mucha RAM y rápido no
son lo mismo.

Y la concurrencia: un portátil sirve a una persona; 200 usuarios simultáneos
exigen procesar por lotes, y procesar por lotes exige GPU. El coste no escala con
lo listo que sea el modelo, sino con cuánta gente lo usa a la vez.

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

Un modelo local elimina las preguntas del art. 23 —encargado del tratamiento,
subencargados, ubicación de los datos, transferencias—. **No elimina** el resto.
Cumplir es más fácil; no es automático.

---

## Avisos

**La propuesta de codificación CIE-10 de `evaluacion/gold-04-cie10.json` no es un
patrón certificado.** Es una propuesta razonada que debe validar un técnico de
documentación clínica antes de proyectar ninguna cifra en público. Los códigos
marcados con confianza media o baja son precisamente los discutibles, y esa
discusión es material de charla.

**Las métricas de las tareas 3 y 5 son heurísticas** para comparar modelos entre
sí sobre un único informe. No son una validación clínica ni un estudio.

**Las tres incoherencias de la tarea 5 están plantadas a propósito.** Dígalo en
voz alta antes de ejecutarla.

---

## Licencia

El informe sintético, los prompts, los patrones de evaluación y los scripts se
publican para que cualquier asistente pueda reproducir la demostración en su
propio hardware. Los modelos son de sus respectivos autores y cada uno tiene su
propia licencia: revísela antes de cualquier uso que no sea esta demostración.

---

## Los resultados

Las salidas de los tres modelos sobre este informe, tarea por tarea, están en
[**RESULTADOS.md**](RESULTADOS.md) y en [`resultados/`](resultados/), con el
`.meta.json` de cada ejecución: modelo, parámetros, tiempos y tokens.
