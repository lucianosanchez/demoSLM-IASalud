.PHONY: all ver limpiar limpiar-todo

all: demo-slm-local.pdf

demo-slm-local.pdf: demo-slm-local.tex $(wildcard img/*.png) $(wildcard *.tex) $(wildcard extractos/*.txt)
	latexmk -pdf -interaction=nonstopmode -halt-on-error demo-slm-local.tex
	@echo ""
	@echo "Capturas que faltan (aparecen como recuadro en el PDF):"
	@grep -oE '\\captura(\[[^]]*\])?\{[^}]*\.png\}' demo-slm-local.tex \
	  | sed -E 's/.*\{([^}]*\.png)\}/img\/\1/' | sort -u | while read f; do \
	  [ -f "$$f" ] || echo "  - $$f"; done

ver: demo-slm-local.pdf
	open demo-slm-local.pdf

limpiar:
	latexmk -c

limpiar-todo:
	latexmk -C
