#!/usr/bin/env python3
"""
Recorta de resultados/ los fragmentos que se proyectan en las diapositivas.

La charla va cerrada en transparencias, y las diapositivas que enseñan una
salida de un modelo no la llevan como captura de pantalla: la leen de
presentacion/extractos/, que genera este script. Tres ventajas sobre fotografiar
la pantalla:

  - se lee en un proyector (es texto vectorial, no un PNG ampliado);
  - se actualiza solo al volver a ejecutar la demo, sin rehacer nada;
  - el recorte está decidido aquí, en un sitio, y no escondido en el .tex.

Lo que sigue haciendo falta en PNG es lo que no produce este repositorio: la
ventana de LM Studio, el monitor de memoria y el «sin resultados» de eCIE-Maps.
Ver docs/CAPTURAS.md.

Uso:
    python3 scripts/extractos.py        (o: make extractos)
"""

import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RES = RAIZ / "resultados"
DESTINO = RAIZ / "presentacion" / "extractos"
INFORME = RAIZ / "informes" / "informe-alta-001.txt"

ANCHO = 96      # columnas; más allá, listings parte la línea y se lee peor
ALTO = 18       # líneas que caben en una diapositiva con holgura

# `listings` sólo sabe pintar los caracteres declarados en el `literate` de
# presentacion/demo-slm-local.tex; con cualquier otro, la compilación falla con
# «Invalid UTF-8 byte sequence». Aquí se sustituyen los que produce el propio
# evaluador y se avisa de los que no estén contemplados en ninguno de los dos
# sitios, para que el fallo salte al generar y no al compilar la charla.
SUSTITUCIONES = {"→": "->", "✓": "[ok]", "✗": "[x]", "×": "x", "…": "...",
                 "–": "-", "\u00a0": " ", "\u2019": "'", "“": '"', "”": '"'}
SEGUROS = set("áéíóúüñÁÉÍÓÚÜÑ«»·—ºª°²³µ¿¡")


def leer(ruta):
    return ruta.read_text(encoding="utf-8") if ruta.exists() else None


def primeras(texto, n=ALTO):
    return "\n".join(texto.splitlines()[:n])


def desde_hasta(texto, desde, hasta=None, n=ALTO):
    """Fragmento que empieza en la línea que contiene `desde`.

    Se busca por contenido y no por número de línea porque cada modelo devuelve
    el documento con una maquetación distinta.
    """
    lineas = texto.splitlines()
    ini = next((i for i, l in enumerate(lineas) if desde.lower() in l.lower()), None)
    if ini is None:
        return None
    fin = len(lineas)
    if hasta:
        fin = next((j for j in range(ini + 1, len(lineas))
                    if hasta.lower() in lineas[j].lower()), fin)
    return "\n".join(lineas[ini:min(fin, ini + n)])


def parrafo_con(texto, *terminos, n=6):
    """El párrafo donde el modelo habla de algo. Para el trazador."""
    for bloque in re.split(r"\n\s*\n", texto):
        if all(t.lower() in bloque.lower() for t in terminos):
            return "\n".join(bloque.strip().splitlines()[:n])
    return None


ORDEN = ["3B", "8B", "27B"]


def comparacion_tarea3():
    """La tabla de la tarea 3, modelo a modelo, medida y no escrita a mano.

    Es la diapositiva «Los dos textos se leen bien»: los tres textos se leen
    igual de bien y lo que los separa es lo que se han dejado por el camino. Los
    números salen del evaluador, así que no pueden desincronizarse de los
    resultados.
    """
    sys.path.insert(0, str(RAIZ / "scripts"))
    import evaluar

    medidas = {}
    for meta in RES.glob("03-reescritura__*.meta.json"):
        m = json.loads(meta.read_text(encoding="utf-8"))
        salida = evaluar.cargar(meta)
        if salida:
            medidas[m["etiqueta"]] = evaluar.EVALS["03"](salida)
    if not medidas:
        return None

    etiquetas = [e for e in ORDEN if e in medidas] + sorted(set(medidas) - set(ORDEN))
    filas = [("mensajes críticos", "cobertura_criticos"),
             ("mensajes (de 15)", "cobertura_total"),
             ("legibilidad INFLESZ", "inflesz"),
             ("palabras", "palabras"),
             ("tecnicismos sin traducir", "tecnicismos_sin_traducir")]

    ancho = max(11, *(len(e) for e in etiquetas))
    lineas = [" " * 26 + "".join(f"{e:>{ancho}}" for e in etiquetas)]
    for titulo, clave in filas:
        valores = "".join(f"{str(medidas[e].get(clave, '—')).split(' ')[0]:>{ancho}}"
                          for e in etiquetas)
        lineas.append(f"{titulo:26s}{valores}")

    for e in etiquetas:
        perdidos = medidas[e].get("_faltan") or []
        cifras = medidas[e].get("_cifras") or []
        if perdidos:
            lineas.append("")
            lineas.append(f"lo que se dejó {e}:")
            lineas += [f"  - {x.split(':')[0]}: {x.split(':', 1)[1].strip()[:52]}" for x in perdidos]
        if cifras:
            lineas.append(f"  cifras alteradas: {'; '.join(cifras)}")
    return "\n".join(lineas)


def salida_del_evaluador(*args):
    r = subprocess.run([sys.executable, str(RAIZ / "scripts" / "evaluar.py"), *args],
                       capture_output=True, text=True, cwd=RAIZ)
    return r.stdout.strip() or None


def recorta_ancho(texto):
    """Corta las líneas larguísimas para que no se plieguen tres veces."""
    return "\n".join(l if len(l) <= ANCHO else l[:ANCHO - 3] + "..."
                     for l in texto.splitlines())


def apto_para_latex(texto, nombre, avisos):
    for malo, bueno in SUSTITUCIONES.items():
        texto = texto.replace(malo, bueno)
    raros = {c for c in texto if ord(c) > 127 and c not in SEGUROS}
    if raros:
        avisos.append(f"{nombre}: caracteres que LaTeX no sabrá pintar: "
                      + " ".join(f"«{c}» (U+{ord(c):04X})" for c in sorted(raros)))
    return texto


# --------------------------------------------------------------- las recetas
# (nombre del extracto, de dónde sale). El nombre es el que cita el .tex con
# \salida{...}; coincide con el número de la captura que sustituye.

def recetas():
    r = []

    inf = leer(INFORME)
    r.append(("01-informe", desde_hasta(inf, "DATOS DEL PACIENTE", "MOTIVO DE INGRESO", 16)))

    # tarea 1: la misma sección de ANTECEDENTES en dos tamaños
    for etiqueta, nombre in (("3B", "03-t1-3b-antecedentes"), ("27B", "04-t1-27b-antecedentes")):
        t = leer(RES / f"01-anonimizacion__{etiqueta}.txt")
        r.append((nombre, desde_hasta(t, "ANTECEDENTES", "TRATAMIENTO", 13) if t else None))

    # tarea 2: la salida con contrato
    t = leer(RES / "02-extraccion__3B.json")
    r.append(("06-t2-con-esquema", primeras(t, 15) if t else None))
    r.append(("07-t2-edad", desde_hasta(t, '"paciente"', '"alergias"', 7) if t else None))

    # tarea 3: dos reescrituras, y qué hizo cada una con el trazador
    for etiqueta, nombre in (("8B", "08a-t3-8b"), ("27B", "08b-t3-27b")):
        t = leer(RES / f"03-reescritura__{etiqueta}.txt")
        r.append((nombre, primeras(t, 16) if t else None))
    t = leer(RES / "03-reescritura__27B.txt") or leer(RES / "03-reescritura__3B.txt")
    r.append(("18-t3-trazador", parrafo_con(t, "amoxicilina") if t else None))
    r.append(("09-t3-cobertura", comparacion_tarea3()))

    # tareas 4 y 5, en el modelo grande si ya se ha ejecutado
    t = leer(RES / "04-codificacion-cie10__27B.json") or leer(RES / "04-codificacion-cie10__3B.json")
    r.append(("10-t4-json", primeras(t, 17) if t else None))
    t = leer(RES / "05-razonamiento-clinico__27B.json") or leer(RES / "05-razonamiento-clinico__3B.json")
    r.append(("12-t5-falsas-alarmas", primeras(t, 17) if t else None))

    r.append(("19-trazador-matriz", salida_del_evaluador("--trazador")))
    return r


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    hechos, faltan, avisos = [], [], []
    for nombre, texto in recetas():
        destino = DESTINO / f"{nombre}.txt"
        if texto:
            texto = apto_para_latex(recorta_ancho(texto), nombre, avisos)
            destino.write_text(texto + "\n", encoding="utf-8")
            hechos.append(nombre)
        else:
            # sin fichero de origen no se escribe nada: la diapositiva enseña
            # su recuadro de hueco, igual que con una captura que falta.
            destino.unlink(missing_ok=True)
            faltan.append(nombre)

    print(f"{len(hechos)} extractos en presentacion/extractos/")
    if avisos:
        print("\nAvisos:")
        for a in avisos:
            print(f"  ! {a}")
    if faltan:
        print("\nSin datos todavía (la diapositiva mostrará el hueco):")
        for n in faltan:
            print(f"  - {n}")
        print("\nSe rellenan solos en cuanto ejecute los modelos que faltan (make todo).")


if __name__ == "__main__":
    main()
