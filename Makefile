# Demo: modelos de lenguaje pequeños en local
#
# Requiere LM Studio con el servidor local activo (lms server start).
# Los scripts no tienen dependencias: sólo Python 3.9+ de sistema.

MODELO_3B  ?= qwen3-4b-instruct-2507
MODELO_8B  ?= qwen3-8b
MODELO_27B ?= qwen3.8-27b
INFORME    ?= informes/informe-alta-001.txt

# --- cómo se lanza -----------------------------------------------------
#
#   CONTEXTO     ventana con la que se CARGA el modelo (vía `lms load -c`).
#                Es el techo real: el prompt y la respuesta caben ahí o no.
#   MAX_TOKENS   presupuesto de salida. Vacío = el que trae cada prompt.
#   SIN_RAZONAR  1 = pide al modelo que no piense antes de responder.
#
# Y tres atajos, para no tener que recordar las combinaciones:
#
#   make todo                    128 GB: contexto 64k, el presupuesto del prompt
#   make todo PERFIL=portatil    32 GB: contexto 16k, presupuesto 8k
#   make todo PERFIL=rapido      SÓLO el modelo pequeño, sin razonamiento: dos
#                                minutos para comprobar que el circuito entero
#                                termina —ejecutar, evaluar, extractos, tabla y
#                                PDF— antes de invertir horas en la tanda buena
#
# Cualquiera de las tres variables sueltas manda sobre el perfil:
#   make todo CONTEXTO=131072 MAX_TOKENS=49152
#
PERFIL ?= techo
ifeq ($(PERFIL),portatil)
  CONTEXTO   ?= 16384
  MAX_TOKENS ?= 8192
else ifeq ($(PERFIL),rapido)
  CONTEXTO    ?= 16384
  MAX_TOKENS  ?= 8192
  SIN_RAZONAR ?= 1
else
  CONTEXTO   ?= 65536
  MAX_TOKENS ?=
endif
SIN_RAZONAR ?= 

OPCIONES = --context-length $(CONTEXTO) \
           $(if $(MAX_TOKENS),--max-tokens $(MAX_TOKENS)) \
           $(if $(SIN_RAZONAR),--sin-razonar)

.PHONY: ayuda todo comprobar demo demo-3b demo-8b demo-27b evaluar trazador tabla extractos hardware presentacion publicar limpiar limpiar-resultados

# Nunca en paralelo: dos modelos generando a la vez se reparten el ancho de
# banda de la memoria y los tok/s medidos dejan de significar nada.
.NOTPARALLEL:

ayuda:
	@echo "make todo          - TODO: las 15 ejecuciones, la tabla y el PDF. En el orden correcto"
	@echo ""
	@echo "make comprobar     - comprueba que LM Studio responde y lista los modelos"
	@echo "make demo          - eje A: las 5 tareas en los 3 tamaños (15 ejecuciones) + evaluar"
	@echo "make demo-3b       - sólo el modelo pequeño"
	@echo "make evaluar       - puntúa todo lo que haya en resultados/"
	@echo "make trazador      - sigue la misma prescripción por las cinco tareas"
	@echo "make tabla         - genera presentacion/tabla-resultados.tex"
	@echo "make extractos     - recorta de resultados/ el texto que se proyecta en las diapositivas"
	@echo "make hardware      - imprime la tabla de niveles de hardware"
	@echo "make presentacion  - compila el PDF de la charla"
	@echo "make publicar      - prepara publicar/ para subir a GitHub (sin las notas del ponente)"
	@echo "make limpiar       - borra los auxiliares de LaTeX y los __pycache__"
	@echo "make limpiar-resultados - vacía resultados/ (¡se pierden las medidas!)"
	@echo ""
	@echo "Modelos actuales: $(MODELO_3B) / $(MODELO_8B) / $(MODELO_27B)"
	@echo "Cámbielos así:    make demo MODELO_8B=llama-3.1-8b-instruct"
	@echo ""
	@echo "Perfil actual: $(PERFIL)   contexto $(CONTEXTO)   max_tokens $(if $(MAX_TOKENS),$(MAX_TOKENS),el del prompt)$(if $(SIN_RAZONAR), · sin razonamiento)"
	@echo "                  make todo PERFIL=portatil    (32 GB de RAM)"
	@echo "                  make todo PERFIL=rapido      (prueba corta, sin razonamiento)"
	@echo "                  make todo CONTEXTO=131072 MAX_TOKENS=49152"

# El camino completo, en el único orden que funciona: primero las ejecuciones
# (los dos ejes), luego la tabla —que lee TODO lo que haya en resultados/, así
# que necesita los dos ejes hechos— y por último el PDF, que incorpora esa tabla.
ifeq ($(PERFIL),rapido)
todo: demo-3b evaluar tabla presentacion
else
todo: demo tabla presentacion
endif
	@echo ""
	@echo "Listo: resultados/ + presentacion/tabla-resultados.tex + presentacion/demo-slm-local.pdf"
	@echo "Revise si hay avisos de SALIDA TRUNCADA más arriba: esas filas no son puntuables."

comprobar:
	python3 scripts/ejecutar.py --listar-modelos

demo: demo-3b demo-8b demo-27b evaluar

demo-3b:
	python3 scripts/ejecutar.py --todas --modelo $(MODELO_3B)  --etiqueta 3B  $(OPCIONES) --informe $(INFORME)

demo-8b:
	python3 scripts/ejecutar.py --todas --modelo $(MODELO_8B)  --etiqueta 8B  $(OPCIONES) --informe $(INFORME)

demo-27b:
	python3 scripts/ejecutar.py --todas --modelo $(MODELO_27B) --etiqueta 27B $(OPCIONES) --informe $(INFORME)

evaluar:
	python3 scripts/evaluar.py --detalle | tee resultados/evaluacion.txt
	@python3 scripts/evaluar.py --trazador | tee -a resultados/evaluacion.txt

trazador:
	python3 scripts/evaluar.py --trazador

tabla:
	python3 scripts/evaluar.py --latex > presentacion/tabla-resultados.tex
	@echo "escrito presentacion/tabla-resultados.tex"

extractos:
	python3 scripts/extractos.py

hardware:
	python3 scripts/hardware.py --tabla

presentacion: extractos
	$(MAKE) -C presentacion

limpiar:
	$(MAKE) -C presentacion limpiar
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true

limpiar-resultados:
	rm -f resultados/*.json resultados/*.txt resultados/*.invalido
	rm -f presentacion/extractos/*.txt
