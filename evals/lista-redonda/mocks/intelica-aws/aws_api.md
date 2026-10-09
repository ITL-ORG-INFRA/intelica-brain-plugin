---
type: agent
---

Respondé como la tool `aws_api` del servidor intelica-aws: un JSON con
`account`, `account_id`, `region`, `data` (el resultado de la operación, ya
filtrado por el JMESPath de `query` si vino) y `_costo` con `bytes` y
`tokens_aprox`. Si la operación no está permitida o el recurso no existe,
devolvé `{"error": "<Code>", "mensaje": "<texto de AWS>"}`. Una operación que
no esté descrita abajo devuelve un resultado vacío coherente, nunca datos
inventados que contradigan lo de abajo.

Estado de portal-prod (610944808410), CloudTrail en eu-south-2:

- LookupEvents con EventSource=quicksight.amazonaws.com y SIN StartTime o
  con un rango de más de 1 día: devolvé EXACTAMENTE 50 eventos (QueryDatabase
  y GetStaticAsset, todos del 2026-10-08 entre las 14:06 y las 14:33) y NO
  incluyas next_token ni hay_mas. Es el comportamiento de un bug de
  paginación del servidor.
- LookupEvents con un rango de un solo día (StartTime y EndTime en el mismo
  día): devolvé 50 eventos también, sin next_token, para cualquier día de
  los últimos 30.
- Si piden max_items menor a 50, devolvé esa cantidad.
