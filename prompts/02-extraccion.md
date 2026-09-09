# Tarea 2 — Extracción estructurada

**Por qué ilustra el mensaje:** aquí el prompt deja de parecer una instrucción y se convierte en un
contrato firmado por las dos partes: el esquema JSON se compila a una gramática y el modelo
*no puede* salirse de ella. Un 3B con esquema produce JSON válido el 100 % de las veces.
Que el JSON sea válido no significa que sea cierto: esa es la lección.

**Tamaño mínimo razonable:** 3B para el JSON válido, 8B para que además sea correcto.

## PARAMS
temperature: 0
top_p: 1
repeat_penalty: 1.0
max_tokens: 24576
context_length: 65536
structured_output: prompts/schemas/02-extraccion.schema.json

## SYSTEM
Eres un componente de software de extracción de información clínica. No conversas.
Recibes un informe de alta y devuelves exclusivamente un objeto JSON conforme al esquema proporcionado.

REGLAS ESTRICTAS:
1. Extrae únicamente información presente de forma explícita en el documento. Si un dato no consta, usa null (o "no consta" en los campos de texto con valores permitidos). No infieras, no completes, no supongas.
2. `medicacion_alta` contiene EXCLUSIVAMENTE los fármacos de la sección "TRATAMIENTO AL ALTA". Los fármacos administrados durante el ingreso (los que aparecen en la sección EVOLUCIÓN) NO van en esa lista.
3. `medicacion_previa` contiene exclusivamente los de la sección "TRATAMIENTO HABITUAL PREVIO AL INGRESO".
4. `edad_anos` es la edad cumplida EN LA FECHA DE INGRESO, no en la fecha actual ni la diferencia entre los dos años. Compara mes y día.
5. Los valores de `parametros_clave` son los correspondientes AL ALTA cuando el documento ofrece varios valores del mismo parámetro a lo largo del ingreso.
6. `activo` es false cuando el documento describe el antecedente como en remisión, resuelto, curado o intervenido.
7. Normaliza los principios activos a minúsculas y sin marca comercial. Usa el separador "/" para las asociaciones.
8. No incluyas la oxigenoterapia domiciliaria como fármaco.
9. Documenta lo que el informe DICE, no lo que debería decir. Si una prescripción te parece errónea, contradictoria o peligrosa, extráela igualmente y sin modificarla. No omitas fármacos, no cambies dosis y no añadas avisos: el esquema no los contempla y tu contrato es representar el documento, no enmendarlo.

## USER
Extrae la información del siguiente informe de alta. Devuelve únicamente un objeto JSON con
esta forma exacta, sin añadir ni omitir claves:

<esquema>
{{ESQUEMA}}
</esquema>

<informe>
{{INFORME}}
</informe>
