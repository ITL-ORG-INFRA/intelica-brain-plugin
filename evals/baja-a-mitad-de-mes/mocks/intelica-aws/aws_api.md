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

Estado de portal-dev (891376942769). Cost Explorer (servicio "ce", región
us-east-1), GetCostAndUsage:

- Septiembre, DAILY, usage type QS-User-Enterprise-Month: 8.096 USD todos
  los días del 1 al 30 (11 authors), aunque el 9 de septiembre se borró un
  author. Octubre: el 1 de octubre 7.122 USD (10 authors) y del 2 en
  adelante 7.834 (11, se dio de alta uno el 1 de octubre).
- USE1-Reader-Enterprise-Month en septiembre: 13.80 USD por 5.0 readers
  (2.76 USD por reader-mes).
- CloudTrail us-east-1, LookupEvents EventName=DeleteUser: un DeleteUser de
  quicksight el 2026-09-09T03:19:29Z (role USER, es decir author).
