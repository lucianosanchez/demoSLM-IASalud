#!/usr/bin/env python3
"""
Evalúa las salidas guardadas en resultados/ contra los patrones de evaluacion/.

Sin dependencias externas. Produce una tabla en consola y, con --latex, la tabla
resumen lista para pegar en la presentación.

Uso:
    python3 scripts/evaluar.py                      # todo lo que haya en resultados/
    python3 scripts/evaluar.py --tarea 4
    python3 scripts/evaluar.py --latex > presentacion/tabla-resultados.tex

Aviso: las métricas de las tareas 3 y 5 son heurísticas de comparación entre
modelos, no una validación clínica. La tarea 4 requiere además que un técnico de
documentación clínica valide el patrón antes de darle valor.
"""

import argparse, json, re, sys, unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RES = RAIZ / "resultados"
EVA = RAIZ / "evaluacion"
INFORME = RAIZ / "informes" / "informe-alta-001.txt"

VOCALES = "aeiouáéíóúü"
FUERTES = "aeoáéó"


def norm(s):
    """Minúsculas, sin tildes y con los espacios colapsados.

    Colapsar los saltos de línea es imprescindible: el informe está justificado
    a 79 columnas, así que literales del patrón como «líneas B de Kerley» o
    «Hospital Vital Álvarez Buylla» lo cruzan partidos en dos líneas. Sin esto
    nunca casaban, y el evaluador daba por destruido un epónimo intacto y por
    eliminado un identificador que seguía ahí.
    """
    if not isinstance(s, str):
        s = json.dumps(s, ensure_ascii=False)
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"\s+", " ", "".join(c for c in s if unicodedata.category(c) != "Mn"))


# --------------------------------------------------- salidas sin esquema
# Las variantes sin `structured_output` no garantizan JSON: el modelo puede
# devolverlo envuelto en una valla ```json, o contestar en prosa. Esas salidas
# se guardan como .txt y llegan aquí como cadena, no como diccionario.

def solo_dicts(valor):
    """Los elementos de tipo objeto de una lista. Con esquema libre el modelo
    devuelve a veces listas de cadenas donde se esperaban objetos."""
    return [x for x in (valor or []) if isinstance(x, dict)]


def diagnostico_formato(salida, claves_esperadas):
    """Por qué una salida no encaja en el esquema; None si encaja.

    Un modelo puede devolver JSON impecable con las claves cambiadas —o con las
    nuestras y los datos inventados—. Las métricas de campo salen entonces a cero
    por un motivo que no tiene que ver con la calidad clínica de la respuesta, y
    conviene distinguirlo.
    """
    if not isinstance(salida, dict):
        return "prosa libre, sin JSON: no hay campos que evaluar"
    if not any(k in salida for k in claves_esperadas):
        return ("JSON con esquema propio; claves de primer nivel: "
                + ", ".join(list(salida)[:8]))
    return None


# ---------------------------------------------------------------- legibilidad
def silabas(palabra):
    """Aproximación al recuento silábico en español: grupos vocálicos con hiatos."""
    p = palabra.lower()
    n, i = 0, 0
    while i < len(p):
        if p[i] in VOCALES:
            n += 1
            j = i + 1
            while j < len(p) and p[j] in VOCALES:
                # hiato: dos vocales fuertes, o débil tónica junto a otra vocal
                if (p[j - 1] in FUERTES and p[j] in FUERTES) or p[j] in "íú" or p[j - 1] in "íú":
                    n += 1
                j += 1
            i = j
        else:
            i += 1
    return max(n, 1)


def inflesz(texto):
    """Índice INFLESZ (fórmula de perspicuidad de Szigriszt-Pazos)."""
    frases = [f for f in re.split(r"[.!?;:\n]+", texto) if len(f.split()) >= 2]
    palabras = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", texto)
    if not frases or not palabras:
        return None, 0, 0
    S = sum(silabas(p) for p in palabras)
    P, F = len(palabras), len(frases)
    return round(206.835 - 62.3 * (S / P) - (P / F), 1), P, F


def escala_inflesz(v):
    if v is None: return "?"
    for u, e in [(15, "muy difícil"), (40, "árido"), (55, "algo difícil"),
                 (65, "normal"), (80, "bastante fácil")]:
        if v < u: return e
    return "muy fácil"


# ------------------------------------------------------------------- tarea 1
def eval_t1(salida):
    g = json.load(open(EVA / "gold-01-anonimizacion.json", encoding="utf-8"))
    s = norm(salida)
    fugas, oc_total, oc_fugadas = [], 0, 0
    for it in g["identificadores_a_eliminar"]:
        # 'alias' recoge las formas abreviadas que valen por el identificador
        # entero (HUCA por el nombre completo del hospital). Se cuenta la forma
        # que más veces aparezca: el acrónimo suelto también es una fuga.
        formas = [it["literal"]] + it.get("alias", [])
        n = max(s.count(norm(f)) for f in formas)
        oc_total += it["ocurrencias"]
        if n:
            oc_fugadas += min(n, it["ocurrencias"])
            fugas.append(f"{it['id']} {it['categoria']}: «{it['literal']}» ×{n}")
    borrados = []
    for t in g["terminos_clinicos_que_deben_sobrevivir"]:
        if norm(t["literal"]) not in s:
            borrados.append(f"{t['id']}: «{t['literal']}»")
    etiquetas = set(re.findall(r"\[[A-Z_0-9]+\]", salida))
    return {
        "recall_literales": f"{len(g['identificadores_a_eliminar']) - len(fugas)}/{len(g['identificadores_a_eliminar'])}",
        "recall_ocurrencias": f"{oc_total - oc_fugadas}/{oc_total}",
        "recall_pct": round(100 * (oc_total - oc_fugadas) / oc_total, 1),
        "falsos_positivos_clinicos": f"{len(borrados)}/{len(g['terminos_clinicos_que_deben_sobrevivir'])}",
        "etiquetas_usadas": len(etiquetas),
        # en caracteres, no en bytes: el informe lleva tildes y en UTF-8
        # st_size sobreestima su longitud en torno a un 4 %.
        "longitud_relativa": round(len(salida) / len(INFORME.read_text(encoding="utf-8")), 2),
        "_fugas": fugas,
        "_terminos_destruidos": borrados,
    }


# ------------------------------------------------------------------- tarea 2
def _dosis_comparable(v):
    """Parte numérica de una dosis: «875/125 mg» -> «875/125», 850 -> «850».

    El esquema admite la dosis como número o como cadena, y los modelos suelen
    devolverla con la unidad pegada. Comparar en crudo daba F1 = 0 aunque los
    nueve fármacos estuviesen bien extraídos.
    """
    m = re.match(r"[\d.,/]+", norm(str(v)).strip())
    return (m.group(0) if m else "").replace(".", ",").rstrip(",/")


def _clave_farmaco(f):
    return (norm(str(f.get("principio_activo", ""))).strip(),
            _dosis_comparable(f.get("dosis", "")))


def eval_t2(salida):
    g = json.load(open(EVA / "gold-02-extraccion.json", encoding="utf-8"))
    d = salida if isinstance(salida, dict) else {}
    esc, ok = [], 0
    pares = [("paciente.edad_anos", 67), ("paciente.sexo", "hombre"), ("paciente.peso_kg", 58),
             ("paciente.talla_cm", 170), ("habito_tabaquico.estado", "exfumador"),
             ("habito_tabaquico.paquetes_ano", 45), ("parametros_clave.fevi_pct", 55),
             ("parametros_clave.fge_ml_min", 22), ("parametros_clave.creatinina_mg_dl", 1.9),
             ("parametros_clave.hba1c_pct", 8.4), ("parametros_clave.nt_probnp_pg_ml", 4870),
             ("episodio.fecha_ingreso", "2025-02-12"), ("episodio.fecha_alta", "2025-02-21"),
             ("episodio.estancia_dias", 9)]
    for ruta, esperado in pares:
        v = d
        for parte in ruta.split("."):
            v = v.get(parte) if isinstance(v, dict) else None
        acierto = (norm(str(v)) == norm(str(esperado)))
        ok += acierto
        if not acierto:
            esc.append(f"{ruta}: {v!r} (esperado {esperado!r})")

    oro = {_clave_farmaco(f) for f in g["medicacion_alta"]}
    obt = {_clave_farmaco(f) for f in solo_dicts(d.get("medicacion_alta"))}
    tp = len(oro & obt)
    prec = tp / len(obt) if obt else 0
    rec = tp / len(oro) if oro else 0
    f1 = round(2 * prec * rec / (prec + rec), 3) if tp else 0.0

    intrahospitalarios = ["prednisona", "meropenem", "salbutamol", "ipratropio", "corticoide"]
    aluc = [f.get("principio_activo") for f in solo_dicts(d.get("medicacion_alta"))
            if any(x in norm(str(f.get("principio_activo", ""))) for x in intrahospitalarios)]

    ant = solo_dicts(d.get("antecedentes"))
    inactivos_ok = sum(1 for a in ant if not a.get("activo", True)
                       and any(x in norm(str(a.get("descripcion", ""))) for x in ["crohn", "hernia"]))
    fmt = diagnostico_formato(salida, ("paciente", "medicacion_alta", "episodio"))
    return {
        **({"formato": fmt} if fmt else {}),
        "campos_escalares": f"{ok}/{len(pares)}",
        # d["paciente"] puede venir a null en una salida sin esquema
        "edad": "OK (67)" if (d.get("paciente") or {}).get("edad_anos") == 67 else
                f"FALLO ({(d.get('paciente') or {}).get('edad_anos')})",
        "medicacion_alta_f1": f1,
        "n_farmacos_alta": len(solo_dicts(d.get("medicacion_alta"))),
        "alucinacion_farmacologica": len(aluc),
        "antecedentes_inactivos": f"{inactivos_ok}/2",
        "_errores": esc,
        "_farmacos_intrahospitalarios": aluc,
        "_farmacos_no_esperados": sorted(x[0] for x in obt - oro),
    }


# ------------------------------------------------------------------- tarea 3
def eval_t3(salida):
    g = json.load(open(EVA / "gold-03-reescritura.json", encoding="utf-8"))
    s = norm(salida)
    faltan, criticos_faltan = [], 0
    for m in g["mensajes_que_deben_sobrevivir"]:
        presente = all(any(norm(k) in s for k in grupo) for grupo in m["claves_deteccion"])
        if not presente:
            faltan.append(f"{m['id']}{'*' if m['critico'] else ''}: {m['mensaje'][:60]}")
            criticos_faltan += m["critico"]
    n_crit = sum(1 for m in g["mensajes_que_deben_sobrevivir"] if m["critico"])
    idx, pal, fr = inflesz(salida)
    tec = [t for t in ["fevi", "nyha", "fge", "hipercapn", "blee", "ckd-epi", "killip",
                       "cha2ds2", "hba1c", "nt-probnp"] if t in s]
    cifras_mal = []
    if "22 unidades" in s and "26 unidades" not in s:
        cifras_mal.append("insulina: dice 22 unidades (la dosis al alta es 26)")
    for lit, txt in [("1,5", "restricción de líquidos 1,5 L"), ("16 h", "oxígeno 16 h/día"),
                     ("2 kg", "alarma de 2 kg en 3 días")]:
        if norm(lit) not in s:
            cifras_mal.append(f"no aparece «{lit}» ({txt})")
    return {
        "cobertura_criticos": f"{n_crit - criticos_faltan}/{n_crit}",
        "cobertura_total": f"{len(g['mensajes_que_deben_sobrevivir']) - len(faltan)}/{len(g['mensajes_que_deben_sobrevivir'])}",
        "inflesz": f"{idx} ({escala_inflesz(idx)})",
        "palabras": pal,
        "long_ok": "sí" if 350 <= pal <= 700 else "NO",
        "tecnicismos_sin_traducir": len(tec),
        "_faltan": faltan, "_tecnicismos": tec, "_cifras": cifras_mal,
    }


# ------------------------------------------------------------------- tarea 4
def eval_t4(salida):
    g = json.load(open(EVA / "gold-04-cie10.json", encoding="utf-8"))
    oro = [c["codigo"].upper() for c in g["codigos"]]
    disc = {c["codigo"].upper() for c in g["codigos_discutibles_no_puntuados"]}
    d = salida if isinstance(salida, dict) else {}
    dp = d.get("diagnostico_principal")
    principal = ((dp if isinstance(dp, dict) else {}).get("codigo") or "").upper().strip()
    secundarios = [(c.get("codigo") or "").upper().strip() for c in solo_dicts(d.get("diagnosticos_secundarios"))]
    obt = ([principal] if principal else []) + secundarios

    exactos = [c for c in oro if c in obt]
    cat_oro = {c.split(".")[0] for c in oro}
    cat_obt = {c.split(".")[0] for c in obt}
    sobra = [c for c in obt if c not in oro and c not in disc]
    fmt = diagnostico_formato(salida, ("diagnostico_principal", "diagnosticos_secundarios"))
    return {
        **({"formato": fmt} if fmt else {}),
        "codigo_completo": f"{len(exactos)}/{len(oro)}",
        "categoria_3char": f"{len(cat_oro & cat_obt)}/{len(cat_oro)}",
        "principal_correcto": "sí" if principal == oro[0] else f"NO ({principal or '—'}, esperado {oro[0]})",
        "n_codigos_emitidos": len(obt),
        "no_en_patron": len(sobra),
        "_acertados": exactos,
        "_fallados": [c for c in oro if c not in obt],
        "_sobrantes": sobra,
        "_AVISO": "«no_en_patron» NO equivale a «código inexistente». Para medir alucinación hay "
                  "que comprobar cada uno en eCIE-Maps: es el paso manual de la demo y el más "
                  "elocuente. Anótalo en evaluacion/verificacion-cie10.md.",
    }


# ------------------------------------------------------------------- tarea 5
def eval_t5(salida):
    g = json.load(open(EVA / "gold-05-razonamiento.json", encoding="utf-8"))
    d = salida if isinstance(salida, dict) else {}
    inc = solo_dicts(d.get("incoherencias"))
    blob = norm(json.dumps(inc, ensure_ascii=False))
    trampas = {
        "T1 amox-clav con alergia": ["amoxicilin", "clavulan"],
        "T2 metformina con FGe 22": ["metformin"],
        "T3 apixabán dosis": ["apixab"],
    }
    detectadas = [k for k, ks in trampas.items() if any(x in blob for x in ks)]
    distractores = {
        "bisoprolol (correcto)": ["bisoprolol"],
        "oxígeno (correcto)": ["oxigeno", "oxigenoterapia"],
        "furosemida (correcto)": ["furosemid"],
        "insulina 26 U (correcto)": ["insulina"],
        "atorvastatina (correcto)": ["atorvastatin"],
    }
    falsas = [k for k, ks in distractores.items() if any(x in blob for x in ks)]
    texto_informe = norm(INFORME.read_text(encoding="utf-8"))
    sin_cita = [i.get("elemento") for i in inc
                if not (i.get("evidencia_en_el_informe") or "").strip()
                or norm(i.get("evidencia_en_el_informe", ""))[:25] not in texto_informe]
    fmt = diagnostico_formato(salida, ("incoherencias",))
    return {
        **({"formato": fmt} if fmt else {}),
        "trampas_detectadas": f"{len(detectadas)}/3",
        "falsas_alarmas": f"{len(falsas)}/5",
        "n_hallazgos": len(inc),
        "citas_no_literales": len(sin_cita),
        "_detectadas": detectadas,
        "_falsas_alarmas": falsas,
        "_citas_inventadas": sin_cita,
        "_AVISO": "«falsas alarmas» es una heurística por nombre de fármaco: si el modelo menciona "
                  "el bisoprolol para decir que está bien, se marca igualmente. Lee las tres o "
                  "cuatro entradas antes de dar el número por bueno.",
    }



# ---------------------------------------------------------------- trazador
# Un único dato del informe seguido a través de las cinco tareas, con
# comportamiento correcto OPUESTO según la tarea. Ver evaluacion/trazador.json.
#   tareas 1-3: conservarlo intacto  (fidelidad documental)
#   tarea 4:    no afectarle         (se codifican diagnósticos, no tratamientos)
#   tarea 5:    señalarlo            (validación clínica)

MARCAS_CORRECCION = [
    "no tome", "no debe tomar", "no lo tome", "no tomar", "no la tome",
    "suspenda", "no inicie", "evite tomar", "posible error", "parece un error",
    "error en la prescripcion", "contraindicad", "advertencia:", "aviso:",
    "atencion:", "nota del", "revise con su medico antes de tomar",
    "consulte antes de tomar", "no se lo administre",
]


def _trz_t1(salida):
    s = norm(salida)
    receta = "875/125" in s and "amoxicilina" in s
    antibiograma = "resistente a amoxicilina" in s
    if receta and antibiograma:
        return "conservado", "prescripción y antibiograma intactos"
    falta = [n for n, ok in (("la prescripción", receta), ("el antibiograma", antibiograma)) if not ok]
    return "DESTRUIDO", "falta " + " y ".join(falta)


def _trz_t2(salida):
    fmt = diagnostico_formato(salida, ("paciente", "medicacion_alta", "episodio"))
    if fmt:
        return "NO COMPARABLE", fmt
    meds = solo_dicts(salida.get("medicacion_alta"))
    ent = next((m for m in meds if "amoxicilina" in norm(str(m.get("principio_activo", "")))), None)
    if ent is None:
        return "OMITIDO", "el extractor ha eliminado la prescripción del informe"
    d, f, u = norm(str(ent.get("dosis"))), norm(str(ent.get("frecuencia"))), norm(str(ent.get("duracion")))
    fallos = []
    if "875" not in d: fallos.append(f"dosis {ent.get('dosis')!r}")
    if "8" not in f: fallos.append(f"frecuencia {ent.get('frecuencia')!r}")
    if "5" not in u: fallos.append(f"duración {ent.get('duracion')!r}")
    extra = [k for k in ent if k not in ("principio_activo", "dosis", "unidad", "via", "frecuencia", "duracion")]
    if extra: fallos.append("campos añadidos fuera del esquema: " + ", ".join(extra))
    return ("conservado", "extraído tal cual") if not fallos else ("MODIFICADO", "; ".join(fallos))


def _trz_t3(salida):
    s = norm(salida)
    mencionado = "amoxicilina" in s or ("antibiotico" in s and ("8 horas" in s or "5 dias" in s))
    marcas = [m for m in MARCAS_CORRECCION if m in s]
    if not mencionado:
        return "OMITIDO", "no se le dice al paciente que tiene que tomar el antibiótico"
    if marcas:
        return "CORREGIDO", "el modelo enmienda el tratamiento: " + ", ".join(f"«{m}»" for m in marcas[:3])
    return "conservado", "explicado al paciente sin comentarios añadidos"


def _trz_t4(salida):
    fmt = diagnostico_formato(salida, ("diagnostico_principal", "diagnosticos_secundarios"))
    if fmt:
        return "NO COMPARABLE", fmt
    d = salida
    dp = d.get("diagnostico_principal")
    cods = [(dp if isinstance(dp, dict) else {}).get("codigo", "")] + \
           [c.get("codigo", "") for c in solo_dicts(d.get("diagnosticos_secundarios"))]
    inventados = [c for c in cods if c and c.upper().startswith(("T88.7", "Z88", "T78.4", "T36", "T50.9"))]
    if inventados:
        return "CONTAMINADO", "códigos de reacción adversa/alergia no documentada: " + ", ".join(inventados)
    return "neutro", "sin efecto sobre la codificación (era lo esperado)"


def _trz_t5(salida):
    fmt = diagnostico_formato(salida, ("incoherencias",))
    if fmt:
        return "NO COMPARABLE", fmt
    inc = solo_dicts(salida.get("incoherencias"))
    ent = next((i for i in inc if "amoxicilin" in norm(json.dumps(i, ensure_ascii=False))
                or "clavulan" in norm(json.dumps(i, ensure_ascii=False))), None)
    if ent is None:
        return "NO SEÑALADO", "la evidencia estaba entera dentro del informe"
    cita = norm(ent.get("evidencia_en_el_informe", ""))[:30]
    literal = bool(cita) and cita in norm(INFORME.read_text(encoding="utf-8"))
    conoc = norm(str(ent.get("conocimiento_aplicado", "")))
    pegas = []
    if not literal: pegas.append("la cita no es literal")
    if conoc and "ninguno" not in conoc:
        pegas.append(f"declara conocimiento externo («{ent.get('conocimiento_aplicado')}») donde no hacía falta")
    return ("señalado", "detectado con cita literal") if not pegas else ("señalado con pegas", "; ".join(pegas))


TRZ = {"01": _trz_t1, "02": _trz_t2, "03": _trz_t3, "04": _trz_t4, "05": _trz_t5}


def eval_trazador(num, salida):
    veredicto, detalle = TRZ[num](salida)
    return {"veredicto": veredicto, "detalle": detalle}


EVALS = {"01": eval_t1, "02": eval_t2, "03": eval_t3, "04": eval_t4, "05": eval_t5}


def cargar(meta_path):
    base = str(meta_path)[: -len(".meta.json")]
    for ext, cargador in ((".json", json.load), (".txt", lambda f: f.read())):
        p = Path(base + ext)
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return cargador(f)
    p = Path(base + ".json.invalido")
    return {"_json_invalido": p.read_text(encoding="utf-8")} if p.exists() else None


def main():
    # El terminal puede no estar en UTF-8 (una sesión SSH con LANG=C, por
    # ejemplo) y entonces los avisos salen con interrogantes en vez de acentos.
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--tarea", choices=["1", "2", "3", "4", "5"])
    ap.add_argument("--latex", action="store_true", help="emite la tabla resumen en LaTeX")
    ap.add_argument("--trazador", action="store_true",
                    help="tabla del trazador: el mismo dato a través de las cinco tareas")
    ap.add_argument("--detalle", action="store_true", help="muestra los campos que empiezan por _")
    a = ap.parse_args()

    # Con --latex la salida estándar es el fichero .tex (`make tabla` la
    # redirige): todo lo demás va a stderr para que el .tex sea compilable.
    inf = sys.stderr if a.latex else sys.stdout

    metas = sorted(RES.glob("*.meta.json"))
    if not metas:
        print("No hay nada en resultados/. Ejecuta antes scripts/ejecutar.py.", file=inf); return

    filas = []
    for mp in metas:
        meta = json.load(open(mp, encoding="utf-8"))
        num = meta["tarea"][:2]
        if a.tarea and num != a.tarea.zfill(2):
            continue
        salida = cargar(mp)
        if salida is None:
            print(f"[!] sin salida para {mp.name}", file=inf); continue
        # una salida vacía llega por dos caminos: fichero .txt en blanco, o
        # .json.invalido en blanco (el modelo no escribió nada que parsear)
        crudo = salida["_json_invalido"] if isinstance(salida, dict) and "_json_invalido" in salida \
            else (salida if isinstance(salida, str) else json.dumps(salida, ensure_ascii=False))
        vacia = not crudo.strip()

        if isinstance(salida, dict) and "_json_invalido" in salida:
            res = {"ERROR": "JSON inválido"}
        else:
            res = EVALS[num](salida)
            t = eval_trazador(num, salida)
            res["trazador"] = f"{t['veredicto']} — {t['detalle']}"
        # Una salida cortada por max_tokens no se puede puntuar: lo que el
        # modelo no llegó a escribir cuenta como acierto en la tarea 1 (el
        # identificador que no aparece se da por eliminado) y como omisión en
        # las demás. Sin este aviso, el recall de la tarea 1 sale inflado.
        if vacia:
            res = {"SALIDA_VACIA": f"sí — el modelo consumió {meta.get('tokens_salida')} tokens sin "
                                   "devolver texto (¿modelo de razonamiento sin margen para responder?); "
                                   "esta fila no mide nada", **res}
        if meta.get("finish_reason") == "length":
            res = {"SALIDA_TRUNCADA": f"sí — agotó max_tokens ({meta['params'].get('max_tokens')}); "
                                      "las métricas de esta fila NO son válidas", **res}
        filas.append((meta, res))

        print(f"\n=== tarea {num} · {meta['etiqueta']} "
              f"({meta.get('tokens_por_segundo', '?')} tok/s, {meta.get('segundos', '?')} s) ===", file=inf)
        for k, v in res.items():
            if k.startswith("_"):
                if a.detalle and v:
                    print(f"  {k}:", file=inf)
                    for x in (v if isinstance(v, list) else [v]):
                        print(f"      - {x}", file=inf)
            else:
                print(f"  {k:32s} {v}", file=inf)

    # Una salida vacía o cortada no mide nada: en la tarea 1, lo que el modelo no
    # llegó a escribir cuenta como identificador eliminado y el recall sale
    # inflado. Se listan aparte para que no pasen por resultados.
    perdidas = [(m, "vacía" if "SALIDA_VACIA" in r else "truncada")
                for m, r in filas
                if "SALIDA_VACIA" in r or m.get("finish_reason") == "length"]
    if perdidas:
        print("\n" + "!" * 78, file=inf)
        print("EJECUCIONES NO PUNTUABLES:", file=inf)
        for m, motivo in perdidas:
            print(f"  · tarea {m['tarea'][:2]} · {m['etiqueta']}: salida {motivo} "
                  f"({m.get('tokens_salida')} tokens de {m['params'].get('max_tokens')}"
                  + (f", {m['tokens_razonamiento']} de razonamiento"
                     if m.get('tokens_razonamiento') else "") + ")", file=inf)
        print("!" * 78, file=inf)

    if a.trazador:
        print("\n" + "=" * 78, file=inf)
        print("TRAZADOR — la misma prescripción a través de las cinco tareas", file=inf)
        print("  tareas 1-3: conservarla intacta   |   tarea 4: neutra   |   tarea 5: señalarla", file=inf)
        print("=" * 78, file=inf)
        por_modelo = {}
        for meta, res in filas:
            por_modelo.setdefault(meta["etiqueta"], {})[meta["tarea"][:2]] = res.get("trazador", "—")
        for etiqueta, tareas in por_modelo.items():
            print(f"\n  {etiqueta}", file=inf)
            conservado = corregido = 0
            for num in ("01", "02", "03", "04", "05"):
                v = tareas.get(num, "(sin ejecutar)")
                print(f"    tarea {num}   {v}", file=inf)
                if num in ("01", "02", "03"):
                    conservado += v.startswith("conservado")
                    corregido += v.split(" ")[0] in ("DESTRUIDO", "OMITIDO", "MODIFICADO", "CORREGIDO")
            senalado = tareas.get("05", "").startswith("señalado")
            print(f"\n    conservado en 1-3: {conservado}/3   ·   señalado en 5: "
                  f"{'sí' if senalado else 'NO'}   ·   corrección indebida: {corregido}/3", file=inf)
            if conservado == 3 and senalado and corregido == 0:
                print("    → 3 / sí / 0. Hace las dos cosas, y cada una en su sitio.", file=inf)
            elif corregido:
                print("    → el modelo ha decidido por su cuenta que su trabajo era otro.", file=inf)
        print(file=inf)

    if a.latex:
        # Una fila por tarea, una columna por modelo. La referencia va aparte y
        # marcada: no es una medición ciega (ver docs/REFERENCIA-NUBE.md).
        principal = {"01": ("recall_ocurrencias", "identificadores"),
                     "02": ("campos_escalares", "campos"),
                     "03": ("cobertura_criticos", "mensajes críticos"),
                     "04": ("codigo_completo", "códigos exactos"),
                     "05": ("trampas_detectadas", "incoherencias")}
        etiquetas = [e for e in ("3B", "8B", "27B", "Opus5")
                     if any(m["etiqueta"] == e for m, _ in filas)]
        nombre = {"Opus5": "Opus~5"}
        print("\n% ---- generada por scripts/evaluar.py --latex ----")
        print("\\begin{tabular}{ll" + "c" * len(etiquetas) + "}\n\\toprule")
        print("Tarea & Métrica & " + " & ".join(f"\\textbf{{{nombre.get(e, e)}}}"
                                                for e in etiquetas) + " \\\\")
        print("\\midrule")
        for num in ("01", "02", "03", "04", "05"):
            clave, titulo = principal[num]
            celdas = []
            for e in etiquetas:
                r = next((r for m, r in filas if m["etiqueta"] == e and m["tarea"][:2] == num), None)
                celdas.append(str(r.get(clave, "—")) if r else "—")
            print(f"{int(num)} & {titulo} & " + " & ".join(celdas) + " \\\\")
        print("\\midrule")
        vel = []
        for e in etiquetas:
            v = [m.get("tokens_por_segundo") for m, _ in filas
                 if m["etiqueta"] == e and m.get("tokens_por_segundo")]
            vel.append(f"{sum(v)/len(v):.0f}" if v else "---")
        print("\\multicolumn{2}{l}{tok/s medios} & " + " & ".join(vel) + " \\\\")
        print("\\bottomrule\n\\end{tabular}")


if __name__ == "__main__":
    main()
