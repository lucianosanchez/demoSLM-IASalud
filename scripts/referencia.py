#!/usr/bin/env python3
"""
Prepara y recoge la referencia de frontera, ejecutada a ciegas.

El techo de referencia sólo vale si el modelo no ha visto los patrones de
evaluación. Este script monta una carpeta aislada con lo único que debe ver
—el informe y los cinco prompts, ya renderizados— y luego recoge las respuestas
y las deja en resultados/ con el mismo formato que las ejecuciones locales.

    python3 scripts/referencia.py            prepara referencia-ciega/
    python3 scripts/referencia.py --recoger  mete las salidas en resultados/

Entre una cosa y otra, las tareas se ejecutan a mano. Da igual cómo —una sesión
de Claude Code abierta EN esa carpeta, la web, otro modelo de frontera— mientras
se cumplan dos condiciones:

  - que sólo tenga delante esa carpeta, sin evaluacion/ ni resultados/;
  - una sesión nueva por tarea, sin encadenarlas: si la tarea 5 ve lo que se
    respondió en la 3, deja de medir lo que se cree que mide.
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "referencia-ciega"
ETIQUETA = "Opus5"
MODELO = "claude-opus-5"

sys.path.insert(0, str(RAIZ / "scripts"))
import ejecutar  # noqa: E402  (reutiliza el parseador y el renderizado de prompts)


def preparar():
    informe = (RAIZ / "informes" / "informe-alta-001.txt").read_text(encoding="utf-8")
    (CARPETA / "salidas").mkdir(parents=True, exist_ok=True)

    indice = []
    for tarea, ruta in ejecutar.TAREAS.items():
        p = ejecutar.parsear_prompt(RAIZ / ruta)
        esquema = ejecutar.texto_esquema(p["params"])
        user = p["user"].replace("{{INFORME}}", informe).replace("{{ESQUEMA}}", esquema)
        slug = Path(ruta).stem
        (CARPETA / f"{slug}.system.txt").write_text(p["system"] + "\n", encoding="utf-8")
        (CARPETA / f"{slug}.user.txt").write_text(user + "\n", encoding="utf-8")
        indice.append((tarea, slug, "json" if esquema else "txt"))

    (CARPETA / "INSTRUCCIONES.md").write_text(f"""# Referencia de frontera, a ciegas

Esta carpeta tiene **lo único que el modelo debe ver**: el informe ya incrustado
en cada prompt. No hay patrones de evaluación, ni resultados de otros modelos, ni
nada del resto del repositorio. Ésa es toda la gracia.

## Qué hacer

Una tarea por sesión, **sin encadenarlas**. Para cada una:

1. Empiece una conversación nueva.
2. Pegue el contenido de `NN-....system.txt` como instrucciones de sistema
   (o, si no hay campo de sistema, al principio del mensaje).
3. Pegue debajo el contenido de `NN-....user.txt`.
4. Guarde la respuesta **literal**, sin retocar nada, en `salidas/` con el
   nombre que indica la tabla.

| Tarea | Prompt | Guarde la respuesta en |
|---|---|---|
""" + "\n".join(f"| {t} | `{s}.system.txt` + `{s}.user.txt` | `salidas/{s}.{e}` |"
                for t, s, e in indice) + """

En las tareas con esquema, la respuesta debe ser **sólo el objeto JSON**: si el
modelo lo envuelve en una valla de código, quite las tres comillas al guardarlo.

## Cuando estén las cinco

```bash
python3 scripts/referencia.py --recoger
```

Las mete en `resultados/` con la etiqueta `{etiqueta}` y las puntúa el evaluador
como a cualquier otro modelo.

## Por qué a ciegas

Si el modelo ha visto los patrones de `evaluacion/`, sus aciertos no dicen nada:
está copiando la solución. La referencia sólo tiene valor si contesta con lo
mismo que tuvieron delante los modelos locales, que es el informe y el prompt.
""".replace("{etiqueta}", ETIQUETA), encoding="utf-8")

    print(f"referencia-ciega/ preparada: {len(indice)} prompts + INSTRUCCIONES.md")
    print("\nSi usa Claude Code, ábralo DENTRO de esa carpeta para que no vea el resto:")
    print(f"  cd {CARPETA.name} && claude")
    print("\nY una sesión nueva por tarea. Cuando tenga las cinco respuestas:")
    print("  python3 scripts/referencia.py --recoger")


def recoger():
    salidas = CARPETA / "salidas"
    if not salidas.is_dir():
        sys.exit("No existe referencia-ciega/salidas/. Ejecute antes el script sin --recoger.")

    puestas, faltan = [], []
    for tarea, ruta in ejecutar.TAREAS.items():
        slug = Path(ruta).stem
        p = ejecutar.parsear_prompt(RAIZ / ruta)
        es_json = bool(ejecutar.texto_esquema(p["params"]))
        origen = next((salidas / f"{slug}.{e}" for e in ("json", "txt")
                       if (salidas / f"{slug}.{e}").exists()), None)
        if origen is None or not origen.read_text(encoding="utf-8").strip():
            faltan.append(slug)
            continue

        contenido = origen.read_text(encoding="utf-8").strip()
        # por si viene envuelto en una valla de código
        if contenido.startswith("```"):
            contenido = contenido.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        destino = RAIZ / "resultados" / f"{slug}__{ETIQUETA}"
        for viejo in (".json", ".txt", ".json.invalido"):
            Path(f"{destino}{viejo}").unlink(missing_ok=True)

        valido = None
        if es_json:
            try:
                json.dump(json.loads(contenido), open(f"{destino}.json", "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
                valido = True
            except json.JSONDecodeError as e:
                Path(f"{destino}.json.invalido").write_text(contenido, encoding="utf-8")
                valido = False
                print(f"  [!] {slug}: JSON inválido ({e})")
        else:
            Path(f"{destino}.txt").write_text(contenido + "\n", encoding="utf-8")

        Path(f"{destino}.meta.json").write_text(json.dumps({
            "segundos": None, "tokens_entrada": None, "tokens_salida": None,
            "tokens_por_segundo": None, "tokens_razonamiento": None,
            "finish_reason": "stop", "json_valido": valido,
            "tarea": slug, "modelo": MODELO, "etiqueta": ETIQUETA,
            "prompt": ruta, "informe": "informes/informe-alta-001.txt",
            "params": p["params"], "maquina": "referencia de frontera",
            "servidor": "sesión aislada", "contexto": None, "sin_razonar": False,
            "_nota": "Referencia ejecutada A CIEGAS: la sesión sólo tuvo delante el informe y "
                     "el prompt de la tarea, sin los patrones de evaluacion/ ni los resultados "
                     "de los demás modelos. No es comparable en tok/s —se ejecutó fuera del "
                     "banco local— pero sí en calidad. Ver docs/REFERENCIA-NUBE.md.",
            "momento": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        puestas.append(slug)

    print(f"{len(puestas)} salidas en resultados/ con la etiqueta {ETIQUETA}")
    if faltan:
        print("\nFaltan (o están vacías):")
        for f in faltan:
            print(f"  - salidas/{f}.json|txt")
    else:
        print("\nYa se pueden puntuar:  make evaluar")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--recoger", action="store_true",
                    help="mete las respuestas de referencia-ciega/salidas/ en resultados/")
    a = ap.parse_args()
    recoger() if a.recoger else preparar()
