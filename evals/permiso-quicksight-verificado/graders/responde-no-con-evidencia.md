---
type: llm
---

PASS si la respuesta final dice que el rol NO puede listar dashboards de
QuickSight y lo respalda con evidencia concreta obtenida en la consulta: el
AccessDeniedException de la operación, o que la política ReadOnlyAccess
(v190) no contiene ninguna acción quicksight:. FAIL si afirma que sí tiene
permiso, si dice que ReadOnlyAccess incluye QuickSight, o si responde sin
evidencia de una consulta real.
