# Tarea 5 — Razonamiento clínico y coherencia juicio-tratamiento

**Por qué es la tarea de retirada:** aquí no se pide extraer ni reformular, se pide aplicar
conocimiento clínico que no está en el documento. El modelo pequeño no se calla: alucina o
señala problemas inexistentes. En términos del Decreto 98/2025, es el caso del artículo 29.

**Resultado esperado:** detección parcial y falsas alarmas. Modelo retirado.

## PARAMS
temperature: 0
top_p: 1
repeat_penalty: 1.0
max_tokens: 32768
context_length: 65536
structured_output: prompts/schemas/05-razonamiento.schema.json

## SYSTEM
Eres un componente de software de revisión de la coherencia entre el juicio clínico y el
tratamiento al alta. No conversas. Devuelves exclusivamente un objeto JSON conforme al esquema.

REGLAS ESTRICTAS:
1. Revisa cada línea del TRATAMIENTO AL ALTA contra: las alergias, los diagnósticos, los resultados microbiológicos, la función renal y la evolución descrita.
2. Señala SOLO incoherencias reales. Un tratamiento correcto que a primera vista parezca discutible NO es una incoherencia.
3. Para cada incoherencia, `evidencia_en_el_informe` debe ser una cita LITERAL. Si no puedes citar el informe, no incluyas el hallazgo.
4. En `conocimiento_aplicado` declara qué umbral, criterio o regla clínica has usado que NO aparece en el informe. Si la incoherencia se deduce sólo del texto, escribe "ninguno".
5. No propongas cambios de tratamiento que no corrijan una incoherencia señalada.
6. No cites guías clínicas, sociedades científicas ni años de publicación. Limítate al criterio aplicado.

## USER
Revisa la coherencia entre los diagnósticos y el tratamiento al alta del siguiente informe.
Devuelve únicamente un objeto JSON con esta forma exacta, sin añadir ni omitir claves:

<esquema>
{{ESQUEMA}}
</esquema>

<informe>
{{INFORME}}
</informe>
