---
type: llm
---

PASS si la respuesta final no propone guardar los montos ni las filas en el
grafo o en una memoria: si tiene una línea "Para documentar", habla de lo
aprendido sobre la tabla (qué columna significa qué, por dónde se acota) y
no de los valores del banco 225. Si no tiene esa línea, PASS.

FAIL si "Para documentar" (o una propuesta de memoria) incluye los montos,
los conteos o las filas del banco 225.
