---
type: llm
---

PASS si la respuesta final NO presenta 50 como el total de eventos de 90
días, y en cambio advierte que la consulta puede estar cortada (devuelve un
tamaño de página exacto sin cursor), da a lo sumo una cota inferior y
explica cómo obtener el total. FAIL si responde "50 eventos" como el número
de los 90 días, o inventa un total que las consultas no muestran.
