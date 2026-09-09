#!/usr/bin/env python3
"""
Calculadora de memoria y velocidad para modelos locales.

Dos reglas, y con ellas se responde a casi todo lo que se pregunta en un comité
de compras:

  1. MEMORIA. Un modelo cuantizado a b bits ocupa aproximadamente
     parámetros × b / 8 bytes. En Q4_K_M el peso efectivo ronda los 4,8 bits,
     de donde sale la regla de bolsillo: ~0,6 GB por cada mil millones de
     parámetros. A eso se le suma la caché KV del contexto.

  2. VELOCIDAD. Generar un token exige leer TODOS los pesos del modelo desde la
     memoria. Por tanto el techo de generación es
         tokens/s = ancho de banda (GB/s) / tamaño del modelo (GB)
     Es un límite de ancho de banda, no de potencia de cálculo. En la práctica
     se alcanza entre el 50 % y el 80 % de ese techo.

  El prefill (leer el prompt) sí está limitado por cálculo, y por eso una CPU
  con mucha RAM tarda tanto en "leer" un informe largo aunque luego escriba.

Uso:
    python3 scripts/hardware.py --tabla
    python3 scripts/hardware.py --params 27 --ancho-banda 400
    python3 scripts/hardware.py --params 70 --ancho-banda 100 --contexto 32768
"""

import argparse

BITS = {"Q4_K_M": 4.8, "Q5_K_M": 5.7, "Q6_K": 6.6, "Q8_0": 8.5, "FP16": 16.0}

NIVELES = [
    # etiqueta, memoria útil GB, ancho de banda GB/s, params que caben (B), techo clínico
    ("a) Móvil / tableta",             6,   50,   3, "Anonimización, plantillas, dictado"),
    ("b) Portátil sin GPU",           32,   80,   8, "Extracción estructurada por lotes, no interactiva"),
    ("c) Portátil Apple Silicon",     48,  300,  27, "Lo anterior + reescritura para el paciente"),
    ("d) Servidor sin GPU, mucha RAM", 512, 100,  70, "Casi nada interactivo. Sólo procesos nocturnos"),
    ("e) Servidor con 1 GPU",         48, 1000,  32, "Codificación asistida, servicio a pocos usuarios"),
    ("f) Servidor multi-GPU",        160, 6700, 120, "Servicio hospitalario concurrente con batching"),
]

NOTAS_NIVELES = {
    "d": "Aunque el servidor alcance 300 GB/s reales (EPYC de 12 canales), el 70B sigue dando "
         "4-6 tok/s. El problema no se arregla comprando más RAM: se arregla comprando ancho de banda.",
    "f": "6700 GB/s es el ancho de banda AGREGADO de dos GPU de gama de centro de datos. Con "
         "batching, el rendimiento TOTAL se multiplica por el tamaño del lote aunque la velocidad "
         "por usuario se mantenga: leer los pesos una vez sirve para todas las peticiones del lote. "
         "Por eso la concurrencia exige GPU y la calidad no.",
}


def memoria_gb(params_b, cuant="Q4_K_M"):
    return params_b * BITS[cuant] / 8


def kv_cache_gb(params_b, contexto, bytes_por_elem=2):
    """Estimación de caché KV para arquitecturas con atención agrupada (GQA).

        KV/token = 2 (K y V) x capas x cabezas_kv x dim_cabeza x bytes

    Con los valores típicos de los modelos abiertos actuales (8 cabezas KV,
    dimensión 128) y capas ~= 10 x raíz(parámetros), queda en capas x 4 KB por
    token. Contrastado: 8B -> 0,9 GB a 8k (real ~1,1); 70B -> 2,8 GB (real ~2,6).

    Aquí se calcula SIN cuantizar (2 bytes por elemento), que es como conviene
    servirla: cuantizar la caché la reduce a la mitad y cuesta precisión justo en
    lo que miden estas tareas —cifras y seguimiento de instrucciones largas—.
    Con contexto amplio no es un detalle: un 27B a 32k son 7 GB sólo de caché."""
    capas = max(24, round(10 * params_b ** 0.5))
    return capas * 8 * 128 * 2 * contexto * bytes_por_elem / 1e9


def velocidad(mem_gb, ancho_banda):
    techo = ancho_banda / mem_gb
    return techo, techo * 0.5, techo * 0.8


def linea(params_b, ancho_banda, contexto=8192, cuant="Q4_K_M"):
    m = memoria_gb(params_b, cuant)
    kv = kv_cache_gb(params_b, contexto)
    total = m + kv
    techo, lo, hi = velocidad(total, ancho_banda)
    return m, kv, total, techo, lo, hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", type=float, help="miles de millones de parámetros, p. ej. 27")
    ap.add_argument("--ancho-banda", type=float, help="GB/s de la memoria donde vive el modelo")
    ap.add_argument("--contexto", type=int, default=8192)
    ap.add_argument("--cuant", default="Q4_K_M", choices=list(BITS))
    ap.add_argument("--tabla", action="store_true", help="imprime la tabla de niveles de la charla")
    ap.add_argument("--latex", action="store_true")
    a = ap.parse_args()

    if a.tabla or not (a.params and a.ancho_banda):
        filas = []
        for etiqueta, mem, bw, p, techo_clinico in NIVELES:
            m, kv, total, t, lo, hi = linea(p, bw, a.contexto, a.cuant)
            cabe = "sí" if total <= mem else "NO"
            filas.append((etiqueta, mem, bw, p, total, t, lo, hi, cabe, techo_clinico))

        if a.latex:
            print("\\begin{tabular}{lrrrrl}\n\\toprule")
            print("Nivel & Mem. & GB/s & Modelo & Ocupa & tok/s reales \\\\\n\\midrule")
            for e, mem, bw, p, total, t, lo, hi, cabe, tc in filas:
                print(f"{e} & {mem:.0f}\\,GB & {bw:.0f} & {p:.0f}B & {total:.0f}\\,GB & {lo:.0f}--{hi:.0f} \\\\")
            print("\\bottomrule\n\\end{tabular}")
        else:
            print(f"\nCuantización {a.cuant} ({BITS[a.cuant]} bits/parámetro), contexto {a.contexto}\n")
            print(f"{'Nivel':32s} {'Mem':>6s} {'GB/s':>6s} {'Modelo':>7s} {'Ocupa':>7s} {'techo':>7s} {'reales':>10s}  {'cabe':>4s}")
            print("-" * 100)
            for e, mem, bw, p, total, t, lo, hi, cabe, tc in filas:
                print(f"{e:32s} {mem:5.0f}G {bw:6.0f} {p:6.0f}B {total:6.1f}G {t:6.1f} "
                      f"{lo:4.0f}-{hi:<5.0f} {cabe:>4s}   {tc}")
            print("\n'reales' = 50-80 % del techo teórico. El techo es ancho de banda / tamaño del modelo.")
            print("Fíjese en la fila d: 512 GB de RAM y aun así 1-2 tok/s. Mucha RAM no es rápido.")
            print("Y antes de subir de modelo, compare con subir los bits del que ya tiene:")
            print("  hardware.py --params 27  --cuant Q8_0   --contexto 32768   ->  36 GB, 9-14 tok/s")
            print("  hardware.py --params 120 --cuant Q4_K_M --contexto 32768   ->  87 GB,  3-5 tok/s")
            for k, v in NOTAS_NIVELES.items():
                print(f"\n  [{k}] {v}")
            print()
        return

    m, kv, total, t, lo, hi = linea(a.params, a.ancho_banda, a.contexto, a.cuant)
    print(f"\nModelo de {a.params:g}B en {a.cuant}, contexto {a.contexto}")
    print(f"  pesos          {m:6.1f} GB")
    print(f"  caché KV       {kv:6.1f} GB  (estimación)")
    print(f"  memoria total  {total:6.1f} GB")
    print(f"\nCon {a.ancho_banda:g} GB/s de ancho de banda:")
    print(f"  techo teórico  {t:6.1f} tok/s")
    print(f"  realista       {lo:6.1f} - {hi:.1f} tok/s")
    lectura = 4  # palabras/s de lectura humana cómoda ~ 4 tok/s en español
    print(f"\n  {'por encima' if lo > lectura else 'POR DEBAJO'} de la velocidad de lectura humana (~{lectura} tok/s)")
    if lo < 2:
        print("  → esto no es un sistema interactivo. Es un proceso por lotes nocturno.")


if __name__ == "__main__":
    main()
