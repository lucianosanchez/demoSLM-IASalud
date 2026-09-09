# Modelos que descargar

> **Verifique los nombres exactos en el buscador de LM Studio antes de la charla.**
> El catálogo cambia de un mes para otro: aparecen versiones nuevas, se renombran
> repositorios y se retiran cuantizaciones. Lo que no cambia son los tres tamaños
> y el papel de cada uno en la demostración.

## Los tres modelos de la demo

La demo necesita **tres tamaños del mismo orden de calidad**, no tres modelos
cualesquiera. Si mezcla familias, el público atribuirá las diferencias al
fabricante y no al tamaño, que es lo que se quiere enseñar. Por eso la
recomendación principal es usar los tres tamaños de **una sola familia**.

Las etiquetas **3B / 8B / 27B** son papeles, no cifras exactas: el pequeño, el
mediano y el mayor que le quepa. Reprodúzcala con los suyos y pase los
identificadores que le dé `lms ls`:

```bash
make demo MODELO_3B=<el suyo> MODELO_8B=<el suyo> MODELO_27B=<el suyo>
```

### Los tres de esta charla (familia Qwen, misma casa)

| Etiqueta | Identificador en LM Studio | Params | Bits | Ocupa | Papel en la demo |
|---|---|---|---|---|---|
| **3B** | `qwen3-4b-instruct-2507` | 4B | ~4 | 2,4 GB | El suelo. Hace la 1 y la 2, se cae en la 3 |
| **8B** | `qwen3-8b` | 8B | ~5 | 5,0 GB | El punto dulce. Hace 1, 2 y casi la 3 |
| **27B** | `qwen3.8-27b` | 27B | **8** | 30,0 GB | El techo local. Hace 1, 2 y 3. Sigue fallando 4 y 5 |

Los tres son de la misma familia, con el mismo tokenizador y el mismo estilo de
instrucción, así que la variable dominante es el número de parámetros, que es
exactamente la variable de la charla.

**El grande va a 8 bits y los otros dos a 4. Dígalo en voz alta.** No es un
descuido: un 27B a 8 bits es lo mejor que cabe hoy en una máquina de 128 GB
—un Mac Studio, una DGX Spark—, y es el techo real de «modelo local» para quien
esté escuchando. La asimetría **juega a favor del modelo grande**, y por eso
refuerza el argumento en lugar de debilitarlo: aun dándole la mejor versión
posible de sí mismo, el 27B **sigue fallando las tareas 4 y 5**. Si alguien
pregunta si los fallos son culpa de la cuantización, la respuesta ya está en la
tabla: el que falla es el que no está cuantizado agresivamente.

Lo que sí conviene no mezclar son los ajustes de muestreo (temperature, top_p,
repeat penalty y contexto), que deben ser idénticos en los tres. Ésos sí
cambiarían la comparación.

Tiene el efecto de los 8 bits medido en la propia charla: 30 GB que hay que leer
de memoria por cada token, el doble que en Q4. Es la mitad de velocidad, y sale
en los tok/s del bloque 6:

```bash
python3 scripts/hardware.py --params 27 --ancho-banda 546 --cuant Q8_0 --contexto 12288
```

### Opción alternativa: mezcla de familias

Si el 27B no le cabe o va demasiado lento, ésta es la combinación más habitual:

| Etiqueta | Modelo | Cuantización | Ocupa | Notas |
|---|---|---|---|---|
| **3B** | Llama-3.2-3B-Instruct | Q4_K_M | ~2,0 GB | El más pequeño que aún es usable en español |
| **3-4B** | gemma-3-4b-it | Q4_K_M | ~2,6 GB | Mejor español que Llama 3.2 3B |
| **8B** | Meta-Llama-3.1-8B-Instruct | Q4_K_M | ~4,9 GB | El caballo de batalla clásico |
| **9B** | NVIDIA-Nemotron-Nano-9B-v2 | Q4_K_M | ~5,7 GB | Buen extractor estructurado |
| **24B** | Mistral-Small-3.2-24B-Instruct | Q4_K_M | ~14,3 GB | Muy buen español, cabe en 24 GB |
| **27B** | gemma-3-27b-it | Q4_K_M | ~16,5 GB | El de referencia para la tarea 3 |

### Track opcional: dominio frente a tamaño

Si tiene tiempo para un séptimo bloque, añada **MedGemma 27B (texto)**, la
variante de Gemma preentrenada con corpus médico. Sirve para separar dos cosas
que el público confunde:

- Más parámetros → más conocimiento memorizado en general.
- Preentrenamiento de dominio → más conocimiento memorizado **de esa** materia,
  con el mismo número de parámetros.

En las tareas 4 y 5, MedGemma sube respecto a Gemma-3-27B; en la 1 y la 2 no se
nota nada, porque ahí no hace falta conocimiento. Además está orientado al
inglés, así que en español pierde parte de la ventaja: eso, dicho en una charla
en España, vale por sí solo.

## Descarga

Con la interfaz: pestaña **Discover** (lupa), busque el nombre, elija la
cuantización (ver más abajo) y descargue.

Con la CLI de LM Studio:

```bash
lms server start
lms ls
```

`lms ls` le da los identificadores exactos que necesita para `--modelo`.

## Qué cuantización usar

La regla es sencilla: **la mejor que le quepa, y dicha en voz alta.**

- **Q8_0** (~8,5 bits) casi no pierde calidad y ocupa el doble que Q4. Es lo que
  se usa aquí para el modelo grande, porque en 128 GB cabe de sobra.
- **Q4_K_M** (~4,8 bits) es el equilibrio estándar: pérdida pequeña y medible, y
  la mitad de memoria. Es lo razonable para el pequeño y el mediano, y lo que
  usará casi todo el que reproduzca la demo en un portátil.
- **Q3 o inferior** degrada de forma visible justo en lo que mide la demo:
  seguimiento de instrucciones y precisión numérica. No lo use.

Anote la cuantización de cada modelo junto a sus tok/s. Sin ese dato, los tok/s
no significan nada: la velocidad depende de los **gigabytes** que hay que leer
por token, no de los parámetros.

## El error de compra: un modelo más grande, peor servido

La pregunta que sale siempre es «¿y si compro más máquina y meto un modelo más
grande?». La respuesta, medida en este mismo montaje, es que **no compensa**:

| Montaje | Ocupa | tok/s reales | Calidad observada |
|---|---|---|---|
| 27B a **8 bits**, contexto 32k, caché KV sin cuantizar | 36 GB | 9–14 | La referencia local |
| 120B a **4 bits**, contexto 32k | 87 GB | 3–5 | **Peor**, pese al triple de parámetros |

Un modelo de 120B cuantizado a 4 bits pierde varios puntos de capacidad, y esa
pérdida se come la ventaja de tener más parámetros. Frente a un 27B servido bien
—pesos a 8 bits, contexto amplio y la caché KV **sin** cuantizar—, el grande
ocupa el doble de memoria, va tres veces más lento y contesta peor. Lo mismo
ocurre con los demás pesos pesados que se puedan cargar en local: si sólo caben
cuantizados de forma agresiva, no son competitivos.

De ahí la recomendación práctica para el público:

> **Antes de comprar más memoria para meter un modelo mayor, gaste la que tiene
> en servir mejor uno mediano.** Suba los bits de los pesos antes que los
> parámetros, y no cuantice la caché KV.

Las cuentas se pueden rehacer en directo con cualquier configuración:

```bash
python3 scripts/hardware.py --params 27  --cuant Q8_0   --contexto 32768 --ancho-banda 546
python3 scripts/hardware.py --params 120 --cuant Q4_K_M --contexto 32768 --ancho-banda 546
```

## Las dos configuraciones

La demo se ha medido en una máquina de 128 GB de memoria unificada, pero el
escalón que se llevará el público es otro. Conviene tener las dos cifras:

| | Máquina de la charla | Lo que tendrá el público |
|---|---|---|
| Hardware | 128 GB unificada (Mac Studio, DGX Spark) | **32 GB**: Mac unificada, o PC con NVIDIA |
| Modelo grande | 27B a **8 bits** | el mismo 27B a **4 bits** |
| Contexto | 65.536 | 16.384 |
| Pesos + caché KV | 28,7 + 14,0 = **43 GB** | 16,2 + 3,5 = **20 GB** |
| Razonamiento | todo el margen que quiera | cabe, pero justo |

La primera responde a «¿hasta dónde se llega sin límite de hardware local?». La
segunda **funciona**, y es la que hay que citar en la charla: el mismo modelo a
4 bits con 16k de contexto ocupa unos 20 GB y deja sitio al sistema.

Lo que cambia entre las dos no es sólo la precisión de los pesos, es el **margen
para razonar**, y eso se nota justo en las tareas 4 y 5. No es un defecto del
montaje: es el resultado, y merece decirse.

Ni el contexto ni la cuantización se fijan desde este repositorio: se eligen al
cargar el modelo en LM Studio. Lo único que se pasa por la API es el presupuesto
de salida, y para eso está `MAX_TOKENS`:

```bash
make todo MAX_TOKENS=16384
```

### Nota para los Mac

En memoria unificada, macOS no deja que la GPU use toda la RAM: reserva una parte
para el sistema. Por eso la segunda columna se queda en 16k de contexto y no
apura los 23 GB que costaría el de 32k. Si su Mac admite más, cárguelo con más
contexto; si LM Studio se queja o el sistema empieza a paginar, baje el contexto
antes que la cuantización.

## Configuración común en LM Studio

Para que la comparación entre tamaños signifique algo, los tres modelos deben
correr con los mismos ajustes de muestreo (la cuantización puede diferir; ver
arriba):

| Ajuste | Valor | Por qué |
|---|---|---|
| Temperature | **0** | Reproducibilidad. Sin esto, la demo no se puede repetir. |
| Top P | 1 | Idem |
| Repeat penalty | 1.0 | Penalizar repeticiones altera listas y dosis |
| Context Length | **65536** (o 16384 en 32 GB) | Se fija al CARGAR el modelo. Con 8192 no cabe un modelo que razone |
| Max tokens | el del prompt, o `MAX_TOKENS=` | Es un techo, no una reserva: un modelo que no razona termina mucho antes |
| Caché KV | **sin cuantizar** | Cuantizarla ahorra memoria y cuesta precisión justo donde duele: cifras y seguimiento de instrucciones largas |
| GPU offload | máximo que quepa | En Apple Silicon, todo |
| Structured Output | según la tarea | Sólo tareas 2, 4 y 5 |
| Flash Attention | activado | Reduce la memoria de la caché KV |

Con temperature 0 la demo es determinista: la misma pregunta da la misma
respuesta. Es un requisito de la charla, no una manía: si el 27B acierta un
código CIE-10 por azar delante de la sala, pierde usted el argumento.

## El presupuesto de tokens

Los modelos de razonamiento —`qwen3.8-27b` lo es— **consumen muchísimos más
tokens de los que devuelven**: piensan primero, en un bloque que no forma parte
de la respuesta, y sólo después escriben. Con los presupuestos habituales de una
demo (2.000–3.000 tokens) se quedan sin sitio antes de contestar y devuelven una
respuesta **vacía**, no una respuesta corta.

Por eso los prompts de este repositorio llevan presupuestos amplios:

| Tarea | max_tokens (perfil `techo`) | Respuesta útil observada | El resto es para pensar |
|---|---|---|---|
| 1 Anonimización | 32.768 | ~3.600 (devuelve el documento entero) | sí |
| 2 Extracción | 24.576 | ~1.900 | sí |
| 3 Reescritura | 24.576 | ~1.900 | sí |
| 4 Codificación | 24.576 | ~2.200 | sí |
| 5 Razonamiento | 32.768 | ~3.000 | sí, y es la que más piensa |

Con la ventana en 65536 hay sitio para el prompt (hasta ~4.900 tokens) más el
presupuesto completo de salida. En 32 GB, con 16.384 de ventana, el presupuesto
que cabe ronda los 11.000: `ejecutar.py` lo calcula y lo recorta solo.

**Es un techo, no una reserva.** Un modelo que no razona termina en cuanto acaba
la respuesta y no gasta nada de más; sólo cambia que ya no se corta. Y si una
ejecución vuelve a agotar el techo, `scripts/ejecutar.py` lo dice en el momento
y `scripts/evaluar.py` marca esa fila como no puntuable.

### Cómo subirlo

**Para una tanda**, sin tocar ningún fichero:

```bash
make todo MAX_TOKENS=32768
```

Vale igual en `make demo` o `make demo-27b`, y por debajo es la
opción `--max-tokens` de `scripts/ejecutar.py`, que manda sobre el valor del
prompt y queda registrada en el `.meta.json` de cada ejecución.

**Para dejarlo fijo**, el valor vive en la línea `max_tokens:` del bloque
`## PARAMS` de cada prompt. Los cinco de golpe:

```bash
python3 - <<'EOF'
import re, pathlib
NUEVO = 32768
for f in pathlib.Path("prompts").glob("*.md"):
    t = f.read_text(encoding="utf-8")
    f.write_text(re.sub(r"^max_tokens: \d+$", f"max_tokens: {NUEVO}", t, count=1, flags=re.M), encoding="utf-8")
    print(f)
EOF
```

### Y la ventana, que va aparejada

El presupuesto de salida no se puede subir por encima de lo que quede libre en
la ventana del modelo: el prompt y la respuesta comparten ese espacio. Con un
prompt de ~4.900 tokens y una ventana de 8192 no hay presupuesto que valga.

`ejecutar.py` lo comprueba antes de lanzar cada tarea y, si no cabe, recorta y
lo dice:

```
[ventana de 40960 tokens] el prompt ocupa ~4900, así que el presupuesto de
salida baja de 32768 a 36352.
```

La ventana se fija **al cargar el modelo**, no desde aquí:

```bash
lms load qwen3.8-27b -c 65536 --gpu max -y
```

Y recuerde el coste: la caché KV sin cuantizar de un 27B son ~7 GB a 32k y
~14 GB a 64k.

## Advertencia sobre la salida estructurada

Las tareas 2, 4 y 5 usan `response_format: json_schema`. LM Studio lo traduce a
una gramática que restringe la generación token a token. Tres cosas que conviene
saber antes de subirse al estrado:

1. **Funciona incluso en modelos de 3B.** Es la mejor demostración de que el
   prompt es un contrato ejecutable y no una conversación.
2. **Ralentiza la generación** entre un 10 % y un 30 %. Si compara tok/s entre
   tareas, compare tareas con el mismo régimen.
3. **Algunos motores se atascan** con esquemas que usan `$ref`, `$defs` o
   `pattern`. Si le ocurre, edite el esquema de `prompts/schemas/`: sustituya
   cada `$ref` por la definición que hay en `$defs`, y como último recurso quite
   el `pattern` del código CIE-10 —perderá la garantía de que el código tenga
   forma de código, que es parte del argumento de la tarea 4, así que déjelo
   anotado si lo hace—.
