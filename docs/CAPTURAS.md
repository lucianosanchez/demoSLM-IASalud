# Capturas que hay que hacer

**Son cuatro.** Todo lo demás que se proyecta —las salidas de los modelos, el
JSON, la matriz del trazador, el informe— **no es una captura de pantalla**: lo
recorta `scripts/extractos.py` de `resultados/` y la presentación lo lee como
texto (`make extractos`, que ya va incluido en `make presentacion`). Se lee mejor
en un proyector y se actualiza solo cada vez que vuelve a ejecutar la demo.

Las cuatro que quedan son las que este repositorio no puede producir: hay que
fotografiar una ventana que no es suya.

**Antes de empezar:** ponga LM Studio en tema claro, suba el tamaño de fuente
hasta que se lea desde el fondo de una sala, y use siempre la misma anchura de
ventana. Una captura ilegible en un proyector no vale nada.

Guárdelas en `presentacion/img/` en PNG, con estos nombres exactos. Si falta
alguna, la presentación compila igual y muestra un recuadro con el nombre del
fichero que falta.

| Fichero | Qué debe verse | Bloque |
|---|---|---|
| `02-lmstudio-modelos.png` | La lista de modelos de LM Studio con los tres tamaños y los GB que ocupa cada uno | 1 |
| `11-ecie-sin-resultados.png` | **La captura clave.** eCIE-Maps buscando un código inventado por el modelo: «sin resultados» | 5 |
| `13-lmstudio-velocidad.png` | Barra de estado de LM Studio con los tok/s de un modelo grande | 6 |
| `14-monitor-memoria.png` | Monitor de actividad con la memoria ocupada al cargar el 27B | 6 |

## Lo que ya no hay que capturar

Estas diapositivas se rellenan solas desde `resultados/`. Si alguna aparece como
recuadro gris en el PDF, no es que falte una foto: es que **ese modelo todavía no
se ha ejecutado**. `python3 scripts/extractos.py` le dice cuáles faltan.

| Extracto | De dónde sale |
|---|---|
| `01-informe` | La cabecera del informe de alta |
| `03-t1-3b-antecedentes` / `04-t1-27b-antecedentes` | La sección ANTECEDENTES anonimizada por cada modelo |
| `05-t2-sin-esquema` / `06-t2-con-esquema` | La tarea 2 del mismo 3B, sin contrato y con contrato |
| `07-t2-edad` | El bloque `paciente` del JSON, con `edad_anos` |
| `08a-t3-8b` / `08b-t3-27b` | Las dos reescrituras al paciente |
| `09-t3-cobertura` | Tabla de cobertura de la tarea 3, modelo a modelo, con los mensajes que se dejó cada uno |
| `10-t4-json` | El JSON de códigos CIE-10 |
| `12-t5-falsas-alarmas` | El JSON de la revisión de coherencia |
| `18-t3-trazador` | El párrafo donde la tarea 3 habla del antibiótico |
| `19-trazador-matriz` | `evaluar.py --trazador` |

El QR del repositorio tampoco es una imagen: lo genera LaTeX al compilar. Ponga
la URL en `\newcommand{\urlrepo}{...}`, al principio de
`presentacion/demo-slm-local.tex`.

## Referencia: la lista completa que espera el `.tex`

| `01-informe.png` | El informe de alta en pantalla, con la cabecera de datos personales bien visible | 1 |
| `02-lmstudio-modelos.png` | La lista de modelos descargados en LM Studio con los tres tamaños y sus GB | 3 |
| `03-t1-3b-antecedentes.png` | Sección ANTECEDENTES anonimizada por el 3B. Debe verse un epónimo destruido | 3 |
| `04-t1-27b-antecedentes.png` | La misma sección anonimizada por el 27B, con los epónimos intactos | 3 |
| `05-t2-sin-esquema.png` | Salida de la tarea 2 en el 3B **sin** structured output: JSON envuelto en texto | 3 |
| `06-t2-con-esquema.png` | La misma, **con** el esquema activado: JSON limpio | 3 |
| `07-t2-edad.png` | Primer plano del campo `edad_anos` con el valor 68 (incorrecto) | 3 |
| `08-t3-comparacion.png` | Reescritura del 8B y del 27B lado a lado | 4 |
| `10-t4-json.png` | Salida JSON de la tarea 4 en el 27B, con los códigos visibles | 5 |
| `11-ecie-sin-resultados.png` | **La captura clave.** eCIE-Maps buscando un código inventado por el modelo: «sin resultados» | 5 |
| `12-t5-falsas-alarmas.png` | Salida de la tarea 5 señalando el bisoprolol o la atorvastatina como problema | 5 |
| `13-lmstudio-velocidad.png` | Barra de estado de LM Studio con los tok/s de un modelo grande | 6 |
| `14-monitor-memoria.png` | Monitor de actividad con la memoria ocupada al cargar el 27B | 6 |
| `18-t3-trazador.png` | Qué hizo la tarea 3 con la amoxicilina-clavulánico: la transmitió tal cual, o le añadió una advertencia | 4 |
| `19-trazador-matriz.png` | Salida de `scripts/evaluar.py --trazador`: el mismo dato a través de las cinco tareas | 5 |
| `qr-repositorio.png` | Código QR de la URL del repositorio (genérelo cuando publique) | 7 |

Las filas de arriba que no aparecen en la tabla de las cuatro se sirven ahora
desde `presentacion/extractos/`; se dejan aquí por si prefiere sustituir alguna
por una captura de verdad (basta con guardar el PNG con ese nombre y devolver
`\captura` a esa diapositiva).

Las tres opcionales de abajo **no están enlazadas en el `.tex`**: si las hace,
añada la diapositiva donde le convenga.

## Opcionales, por si sobra tiempo

| Fichero | Qué debe verse |
|---|---|
| `15-t4-q8.png` | Innecesaria si su modelo grande ya va a 8 bits: en ese caso la respuesta a «¿será la cuantización?» está en la tabla de modelos |
| `16-medgemma-t4.png` | Tarea 4 con MedGemma 27B: mejora sin cambiar de tamaño |
| `17-sin-red.png` | El portátil con el wifi apagado y la demo funcionando |

La 17 es barata y contundente: apague el wifi **delante del público** antes de
lanzar la primera tarea, y déjelo apagado toda la demo.
