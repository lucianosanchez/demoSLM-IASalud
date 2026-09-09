#!/usr/bin/env python3
"""
Ejecuta una de las cinco tareas contra un modelo servido por LM Studio.

Sin dependencias: sólo biblioteca estándar. LM Studio expone una API compatible
con OpenAI en http://localhost:1234/v1 cuando se activa el servidor local
(pestaña "Developer" -> "Start Server", o `lms server start` desde la CLI).

Uso:
    python3 scripts/ejecutar.py --listar-modelos
    python3 scripts/ejecutar.py --tarea 2 --modelo qwen3-8b
    python3 scripts/ejecutar.py --tarea 4 --modelo gemma-3-27b-it --etiqueta 27B
    python3 scripts/ejecutar.py --todas --modelo qwen3-4b-instruct-2507

Las salidas se guardan en resultados/ con un fichero .meta.json que incluye
tokens/s medidos, que es el dato que sostiene la parte de hardware de la charla.
"""

import argparse, json, os, re, shutil, socket, subprocess, sys, time, urllib.request, urllib.error
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TAREAS = {
    "1": "prompts/01-anonimizacion.md",
    "2": "prompts/02-extraccion.md",
    "3": "prompts/03-reescritura.md",
    "4": "prompts/04-codificacion-cie10.md",
    "5": "prompts/05-razonamiento-clinico.md",
}

def texto_esquema(params) -> str:
    """El esquema JSON, formateado para incrustarlo en el propio prompt.

    Mandar el esquema sólo como `response_format` no basta. Esa vía es una
    gramática que restringe la generación, pero el modelo no la LEE: si además
    no lo tiene en el texto, no sabe qué se le está pidiendo. Un modelo que
    razona antes de responder se inventa entonces una estructura propia —el
    razonamiento va en texto libre, donde la gramática no rige— y, al escribir,
    la gramática le obliga a rellenar claves que nunca preparó. El resultado es
    un JSON impecable con datos inventados.

    Se lee del mismo fichero que se envía como contrato, para que no haya dos
    versiones del esquema que se puedan desincronizar.
    """
    ruta = params.get("structured_output", "no")
    if not ruta or ruta == "no":
        return ""
    d = json.loads((RAIZ / ruta).read_text(encoding="utf-8"))
    return esqueleto(d.get("schema", d), d.get("schema", d))


def _tipo(nodo):
    """Los tipos de un campo, en una sola pieza: number|null, o el enum."""
    if "enum" in nodo:
        return " | ".join(json.dumps(v, ensure_ascii=False) for v in nodo["enum"])
    tipos = nodo.get("type", "string")
    return " | ".join(tipos) if isinstance(tipos, list) else tipos


def esqueleto(nodo, raiz, sangria=0):
    """El esquema como la FORMA del objeto, no como especificación formal.

    El JSON Schema completo son ~1.900 tokens de `type`, `required`,
    `additionalProperties` y descripciones. Un modelo que razona se pone a
    deliberar sobre cada palabra de eso: medido, el de 8B pasó de 2.200 tokens
    de razonamiento a 34.302, se quedó sin presupuesto y devolvió una respuesta
    vacía tras once minutos. Con la forma escueta ve lo mismo que necesita
    —claves, tipos, valores admitidos— en la cuarta parte de espacio.

    El contrato duro sigue siendo el JSON Schema, que se envía aparte como
    `response_format`; esto es sólo lo que el modelo LEE.
    """
    if "$ref" in nodo:
        nombre = nodo["$ref"].rsplit("/", 1)[-1]
        nodo = raiz.get("$defs", {}).get(nombre, {})

    pad, pad2 = "  " * sangria, "  " * (sangria + 1)
    tipos = nodo.get("type")

    if tipos == "object" or "properties" in nodo:
        lineas = []
        props = list(nodo.get("properties", {}).items())
        for i, (clave, hijo) in enumerate(props):
            coma = "," if i < len(props) - 1 else ""
            valor = esqueleto(hijo, raiz, sangria + 1)
            desc = (hijo.get("description") or "").strip()
            nota = f"   // {desc}" if desc and "\n" not in valor else ""
            lineas.append(f'{pad2}"{clave}": {valor}{coma}{nota}')
        return "{\n" + "\n".join(lineas) + f"\n{pad}}}"

    if tipos == "array":
        return "[ " + esqueleto(nodo.get("items", {}), raiz, sangria) + " ]"

    return _tipo(nodo)


def parsear_prompt(ruta: Path) -> dict:
    """Extrae las secciones ## PARAMS, ## SYSTEM y ## USER de un fichero de prompt."""
    texto = ruta.read_text(encoding="utf-8")
    secciones, actual = {}, None
    for linea in texto.splitlines():
        m = re.match(r"^##\s+([A-ZÁÉÍÓÚÑ ]+)\s*$", linea)
        if m:
            actual = m.group(1).strip()
            secciones[actual] = []
        elif actual:
            secciones[actual].append(linea)
    for k in secciones:
        secciones[k] = "\n".join(secciones[k]).strip()

    params = {}
    for linea in secciones.get("PARAMS", "").splitlines():
        if ":" in linea:
            k, v = linea.split(":", 1)
            params[k.strip()] = v.strip()

    return {
        "params": params,
        "system": secciones.get("SYSTEM", ""),
        "user": secciones.get("USER", ""),
        "notas": secciones.get("NOTAS PARA EL PONENTE", ""),
    }


def listar_modelos(base_url: str) -> list:
    try:
        with urllib.request.urlopen(f"{base_url}/models", timeout=10) as r:
            return [m["id"] for m in json.load(r).get("data", [])]
    except urllib.error.URLError as e:
        sys.exit(
            f"No se puede contactar con LM Studio en {base_url} ({e}).\n"
            "Abre LM Studio -> pestaña Developer -> Start Server, o ejecuta `lms server start`."
        )


def llamar(base_url, modelo, system, user, params, timeout, sin_razonar=False):
    cuerpo = {
        "model": modelo,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": float(params.get("temperature", 0)),
        "top_p": float(params.get("top_p", 1)),
        "max_tokens": int(params.get("max_tokens", 2048)),
        "stream": False,
    }
    if "repeat_penalty" in params:
        cuerpo["repeat_penalty"] = float(params["repeat_penalty"])

    # Desactivar el bloque de pensamiento, por las dos vías que existen:
    #   - `chat_template_kwargs`, que es lo que declaran las plantillas de chat,
    #     pero que LM Studio ignora (medido: el 8B siguió razonando igual);
    #   - la marca `/no_think` al final del mensaje, que interpreta el propio
    #     modelo —Qwen3 la define en su plantilla— y por tanto no depende del
    #     motor.
    # Si aun así razona, se avisa al terminar: hay que desactivarlo en el preset.
    if sin_razonar:
        cuerpo["chat_template_kwargs"] = {"enable_thinking": False}
        cuerpo["messages"][-1]["content"] += "\n\n/no_think"

    esquema_ruta = params.get("structured_output", "no")
    if esquema_ruta and esquema_ruta != "no":
        esquema = json.loads((RAIZ / esquema_ruta).read_text(encoding="utf-8"))
        cuerpo["response_format"] = {"type": "json_schema", "json_schema": esquema}

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            respuesta = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Error HTTP {e.code} de LM Studio:\n{e.read().decode('utf-8', 'replace')[:2000]}")
    except urllib.error.URLError as e:
        sys.exit(f"No hay respuesta de LM Studio: {e}")
    segundos = time.perf_counter() - t0

    uso = respuesta.get("usage", {}) or {}
    salida_tok = uso.get("completion_tokens")
    mensaje = respuesta["choices"][0]["message"]

    # Los modelos de razonamiento devuelven el pensamiento en un campo aparte y
    # dejan `content` vacío mientras piensan. Si se agota max_tokens antes de
    # que terminen, `content` llega vacío y la ejecución no vale para nada: hay
    # que verlo en el momento, no tres días después al montar las diapositivas.
    razonamiento = next((mensaje[k] for k in ("reasoning_content", "reasoning")
                         if mensaje.get(k)), None)
    detalles = uso.get("completion_tokens_details") or {}

    return {
        "contenido": mensaje.get("content") or "",
        "razonamiento": razonamiento,
        "tokens_razonamiento": detalles.get("reasoning_tokens"),
        "segundos": round(segundos, 2),
        "tokens_entrada": uso.get("prompt_tokens"),
        "tokens_salida": salida_tok,
        "tokens_por_segundo": round(salida_tok / segundos, 1) if salida_tok and segundos else None,
        "finish_reason": respuesta["choices"][0].get("finish_reason"),
    }


def cargar_modelo(modelo, contexto, base_url):
    """Carga el modelo en LM Studio con la ventana pedida, vía CLI `lms`.

    La ventana NO se puede fijar desde la API: se fija al cargar. Sin esto, el
    modelo se queda con el valor por defecto del preset —8192 es lo habitual— y
    todo lo demás da igual, porque el prompt y la respuesta tienen que caber ahí.
    """
    if not shutil.which("lms"):
        print(f"  [AVISO] no encuentro `lms`; cargue el modelo a mano:\n"
              f"          lms load {modelo} -c {contexto} --gpu max -y")
        return

    # Comprobar que el modelo existe ANTES de descargar nada: `lms load -y` con
    # una clave que no coincide carga «el primero que se le parezca», y el
    # unload previo se habría llevado por delante lo que hubiera cargado.
    disponibles = listar_modelos(base_url)
    if modelo not in disponibles:
        print(f"  [AVISO] el servidor no publica «{modelo}». No se toca nada.\n"
              f"          Hay: {', '.join(disponibles[:6])}")
        return

    _, maxima = ventana(base_url, modelo)
    if maxima and contexto > maxima:
        print(f"  [AVISO] {modelo} admite {maxima} tokens como mucho, no {contexto}.")
        contexto = maxima

    print(f"  cargando {modelo} con contexto {contexto} ...", end="", flush=True)
    subprocess.run(["lms", "unload", "--all"], capture_output=True, text=True)
    r = subprocess.run(["lms", "load", modelo, "-c", str(contexto), "--gpu", "max", "-y"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(" ERROR\n  " + (r.stderr or r.stdout).strip()[:400])
        return
    real = ventana(base_url, modelo, refrescar=True)[0]
    print(f" listo ({real} tokens)" if real else " listo")


_VENTANA = {}


def ventana(base_url, modelo, refrescar=False):
    """(cargada, máxima) del modelo según LM Studio; (None, None) si no lo dice.

    La ventana con la que está CARGADO el modelo es el techo real: el prompt y
    la respuesta tienen que caber juntos ahí, y no se puede cambiar desde la
    API —se fija al cargar el modelo—. La máxima es hasta dónde admite ese
    modelo, y no siempre coinciden: pedir más al cargar no da error, LM Studio
    recorta en silencio. La API compatible con OpenAI no publica ninguna de las
    dos; la REST propia de LM Studio sí.
    """
    if refrescar:
        _VENTANA.pop(modelo, None)
    if modelo not in _VENTANA:
        _VENTANA[modelo] = (None, None)
        try:
            raiz = base_url.rsplit("/v1", 1)[0]
            with urllib.request.urlopen(f"{raiz}/api/v0/models", timeout=5) as r:
                for m in json.load(r).get("data", []):
                    if m.get("id") == modelo:
                        _VENTANA[modelo] = (m.get("loaded_context_length"),
                                            m.get("max_context_length"))
        except Exception:
            pass
    return _VENTANA[modelo]


def presupuesto(system, user, params, base_url, modelo):
    """El max_tokens que cabe de verdad, avisando cuando no es el pedido.

    Si el prompt y la respuesta no caben juntos en la ventana, LM Studio corta
    al llegar al final: la respuesta sale a medias, o vacía si el modelo estaba
    razonando. Vale más recortar y decirlo que gastar veinte minutos en una
    ejecución que se va a truncar.
    """
    tope = int(params.get("max_tokens") or 0)
    cargada, maxima = ventana(base_url, modelo)
    hueco = cargada or maxima
    if not hueco:
        return tope

    prompt_tok = (len(system) + len(user)) // 3      # ~3 caracteres por token
    cabe = (hueco - prompt_tok) // 512 * 512
    if tope <= cabe:
        return tope

    print(f"    [ventana de {hueco} tokens] el prompt ocupa ~{prompt_tok}, así que el "
          f"presupuesto de salida baja de {tope} a {cabe}.")
    if maxima and hueco < maxima:
        print(f"    {modelo} admite hasta {maxima}: recárguelo con más contexto "
              f"(lms load {modelo} -c {maxima}) si quiere el presupuesto entero.")
    return max(512, cabe)


def ejecutar_tarea(tarea, modelo, informe_ruta, base_url, etiqueta, timeout, max_tokens=None,
                   sin_razonar=False):
    ruta = TAREAS[tarea]
    prompt = parsear_prompt(RAIZ / ruta)
    informe = (RAIZ / informe_ruta).read_text(encoding="utf-8")
    esquema = texto_esquema(prompt["params"])
    if esquema and "{{ESQUEMA}}" not in prompt["user"] + prompt["system"]:
        print(f"  [AVISO] {ruta} usa structured_output pero no incrusta {{{{ESQUEMA}}}} en el "
              "texto.\n          El modelo no verá el esquema: sólo lo sufrirá.")
    user = prompt["user"].replace("{{INFORME}}", informe).replace("{{ESQUEMA}}", esquema)
    prompt["system"] = prompt["system"].replace("{{ESQUEMA}}", esquema)

    # --max-tokens manda sobre el valor del prompt, y queda registrado en el
    # .meta.json como el parámetro que realmente se usó.
    if max_tokens:
        prompt["params"]["max_tokens"] = str(max_tokens)

    print(f"  tarea {tarea} · {modelo} ...", flush=True)
    prompt["params"]["max_tokens"] = str(
        presupuesto(prompt["system"], user, prompt["params"], base_url, modelo))
    r = llamar(base_url, modelo, prompt["system"], user, prompt["params"], timeout, sin_razonar)
    print(f" {r['segundos']} s · {r['tokens_por_segundo'] or '?'} tok/s")

    if sin_razonar and r["tokens_razonamiento"]:
        print(f"    [AVISO] se pidió sin razonamiento y ha gastado {r['tokens_razonamiento']} "
              f"tokens pensando.\n"
              f"            Ni `enable_thinking` ni `/no_think` le han hecho efecto: este modelo "
              f"sólo\n"
              f"            deja de razonar desde su preset en LM Studio.")

    tope = int(prompt["params"].get("max_tokens") or 0)
    if not r["contenido"].strip():
        print(f"    [SALIDA VACÍA] el modelo ha consumido {r['tokens_salida']} tokens y no ha "
              f"devuelto texto.")
        if r["razonamiento"] or r["tokens_razonamiento"]:
            cargada = ventana(base_url, modelo)[0]
            margen = (cargada - (r["tokens_entrada"] or 0)) if cargada else None
            print(f"    Se le han ido pensando: {r['tokens_razonamiento'] or r['tokens_salida']} "
                  f"tokens de razonamiento y nada de respuesta.")
            if margen and tope >= margen - 1024:
                # el presupuesto ya era todo lo que cabía: subirlo es imposible
                print(f"    Y NO se puede subir el presupuesto: con una ventana de {cargada} y un "
                      f"prompt de\n"
                      f"    {r['tokens_entrada']} tokens, {tope} era ya todo lo que cabía. El "
                      f"modelo razona sin converger.\n"
                      f"    Salidas reales: acortar el prompt, desactivar el razonamiento en "
                      f"LM Studio,\n"
                      f"    o hacer esta tarea con un modelo que la resuelva sin deliberar tanto.")
            else:
                print(f"    Suba max_tokens por encima de {tope}, o desactive el razonamiento "
                      f"en LM Studio.")
        else:
            print("    Revise en LM Studio que el modelo esté cargado y que el prompt de sistema "
                  "del preset no esté interfiriendo.")
    elif r["finish_reason"] == "length":
        print(f"    [AVISO] salida cortada por max_tokens ({tope}). "
              "Está incompleta y no es puntuable: suba max_tokens en el prompt.")

    nombre_tarea = Path(ruta).stem
    etiqueta_final = etiqueta or modelo
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", etiqueta_final)
    destino = RAIZ / "resultados" / f"{nombre_tarea}__{slug}"

    # Una salida previa con otra extensión (porque el prompt tenía o dejó de
    # tener esquema) confundiría a evaluar.py, que prueba .json antes que .txt.
    for obsoleto in (".json", ".txt", ".json.invalido", ".razonamiento.txt"):
        Path(f"{destino}{obsoleto}").unlink(missing_ok=True)

    es_json = prompt["params"].get("structured_output", "no") not in ("no", "", None)
    contenido = r["contenido"]
    if es_json:
        try:
            Path(f"{destino}.json").write_text(
                json.dumps(json.loads(contenido), ensure_ascii=False, indent=2), encoding="utf-8")
            r["json_valido"] = True
        except json.JSONDecodeError as e:
            Path(f"{destino}.json.invalido").write_text(contenido, encoding="utf-8")
            r["json_valido"] = False
            r["error_json"] = str(e)
            print(f"    ¡JSON inválido! guardado en {destino}.json.invalido")
    else:
        Path(f"{destino}.txt").write_text(contenido, encoding="utf-8")

    Path(f"{destino}.razonamiento.txt").unlink(missing_ok=True)
    if r["razonamiento"]:
        Path(f"{destino}.razonamiento.txt").write_text(r["razonamiento"], encoding="utf-8")

    meta = {k: v for k, v in r.items() if k not in ("contenido", "razonamiento")}
    meta.update({"tarea": nombre_tarea, "modelo": modelo, "etiqueta": etiqueta_final,
                 "prompt": ruta,
                 "informe": informe_ruta, "params": prompt["params"],
                 # dónde se midió: los tok/s sólo significan algo junto a la
                 # máquina que los produjo, y el servidor de LM Studio puede
                 # no ser el equipo desde el que se lanza la demo.
                 "maquina": socket.gethostname(), "servidor": base_url,
                 "contexto": ventana(base_url, modelo)[0], "sin_razonar": sin_razonar,
                 "momento": time.strftime("%Y-%m-%dT%H:%M:%S")})
    Path(f"{destino}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main():
    # El terminal puede no estar en UTF-8 (una sesión SSH con LANG=C, por
    # ejemplo) y entonces los avisos salen con interrogantes en vez de acentos.
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    p = argparse.ArgumentParser(description="Ejecuta las tareas de la demo contra LM Studio")
    p.add_argument("--tarea", choices=list(TAREAS))
    p.add_argument("--todas", action="store_true", help="ejecuta las cinco tareas seguidas")
    p.add_argument("--tareas", help="varias tareas en una sola carga del modelo, separadas por "
                                    "comas: --tareas 2,4,5")
    p.add_argument("--modelo", help="id del modelo tal como lo publica LM Studio")
    p.add_argument("--etiqueta", help="nombre corto para los ficheros de salida, p. ej. 3B / 8B / 27B")
    p.add_argument("--informe", default="informes/informe-alta-001.txt")
    p.add_argument("--max-tokens", type=int,
                   help="presupuesto de salida para TODAS las tareas de esta ejecución; "
                        "manda sobre el max_tokens de cada prompt. Un modelo de razonamiento "
                        "necesita mucho: lo que no gaste, no lo cobra")
    p.add_argument("--context-length", type=int,
                   help="ventana con la que CARGAR el modelo antes de empezar (vía `lms load`). "
                        "Es el techo real: el prompt y la respuesta caben ahí o no caben")
    p.add_argument("--sin-razonar", action="store_true",
                   help="pide al modelo que no genere bloque de pensamiento. Para pruebas "
                        "rápidas: un modelo de razonamiento tarda diez veces más")
    p.add_argument("--url", default=os.environ.get("LMSTUDIO_URL", "http://localhost:1234/v1"))
    # 16.384 tokens a 10 tok/s son 27 minutos: con un modelo de razonamiento en
    # una máquina modesta, media hora de timeout se queda corta.
    p.add_argument("--timeout", type=int, default=5400,
                   help="segundos por llamada (por defecto 90 min); súbelo en servidores sin GPU")
    p.add_argument("--listar-modelos", action="store_true")
    a = p.parse_args()

    if a.listar_modelos:
        for m in listar_modelos(a.url):
            print(m)
        return
    if not a.modelo:
        p.error("hace falta --modelo (usa --listar-modelos para ver los cargados)")
    if not (a.tarea or a.todas or a.tareas):
        p.error("hace falta --tarea N, --tareas N,M o --todas")
    if a.tareas:
        a.tareas = [t.strip() for t in a.tareas.split(",") if t.strip()]
        malas = [t for t in a.tareas if t not in TAREAS]
        if malas:
            p.error(f"tareas desconocidas: {', '.join(malas)}")

    (RAIZ / "resultados").mkdir(exist_ok=True)
    tareas = a.tareas or (list(TAREAS) if a.todas else [a.tarea])
    print(f"modelo: {a.modelo}   informe: {a.informe}"
          + (f"   contexto: {a.context_length}" if a.context_length else "")
          + (f"   max_tokens: {a.max_tokens}" if a.max_tokens else "")
          + ("   sin razonamiento" if a.sin_razonar else ""))

    if a.context_length:
        cargar_modelo(a.modelo, a.context_length, a.url)

    metas = [ejecutar_tarea(t, a.modelo, a.informe, a.url, a.etiqueta, a.timeout, a.max_tokens,
                            a.sin_razonar)
             for t in tareas]

    vel = [m["tokens_por_segundo"] for m in metas if m.get("tokens_por_segundo")]
    if vel:
        print(f"\nvelocidad media: {sum(vel)/len(vel):.1f} tok/s  "
              f"(mín {min(vel)}, máx {max(vel)})")
    print("resultados en resultados/")


if __name__ == "__main__":
    main()
