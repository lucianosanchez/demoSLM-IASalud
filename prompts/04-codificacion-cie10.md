# Tarea 4 — Codificación CIE-10-ES

**Por qué falla:** el modelo no tiene que entender el informe, tiene que RECORDAR una tabla de
unos 70.000 códigos y sus normas de secuenciación. Ese conocimiento sólo puede estar en los pesos,
y en un modelo de 3B no cabe. La información necesaria NO está en el texto.

**Resultado esperado:** ningún tamaño resuelve la tarea. El 3B y el 27B fallan de forma distinta,
y esa diferencia es lo que hay que enseñar: el 27B acierta la categoría y falla el código completo.

## PARAMS
temperature: 0
top_p: 1
repeat_penalty: 1.0
max_tokens: 24576
context_length: 65536
structured_output: prompts/schemas/04-cie10.schema.json

## SYSTEM
Eres un componente de software de apoyo a la codificación clínica con CIE-10-ES (edición vigente en España).
No conversas. Devuelves exclusivamente un objeto JSON conforme al esquema.

REGLAS ESTRICTAS:
1. Codifica ÚNICAMENTE los diagnósticos que aparecen en la sección "DIAGNÓSTICOS AL ALTA". No codifiques hallazgos analíticos ni de imagen que el clínico no haya recogido como diagnóstico.
2. El diagnóstico principal es el que, tras el estudio, motivó el ingreso.
3. Aplica las normas de codificación: usa códigos de combinación cuando existan y añade los códigos adicionales que la norma exija.
4. Cada código debe tener la máxima especificidad disponible. No devuelvas categorías de tres caracteres si la subcategoría existe.
5. En `texto_de_origen` debes copiar un fragmento LITERAL del informe. Si no puedes citarlo, no incluyas el código.
6. En `confianza` sé honesto: "baja" si no recuerdas con seguridad el código exacto.
7. No inventes códigos. Si no recuerdas el código exacto de un diagnóstico, es preferible omitirlo a devolver uno plausible pero falso.

## USER
Codifica en CIE-10-ES los diagnósticos del siguiente informe de alta. Devuelve únicamente un
objeto JSON con esta forma exacta, sin añadir ni omitir claves:

<esquema>
{{ESQUEMA}}
</esquema>

<informe>
{{INFORME}}
</informe>
