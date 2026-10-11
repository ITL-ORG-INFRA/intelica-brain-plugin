---
type: llm
---

PASS si la respuesta final, antes de recomendar sacar la copia de CloudWatch
(fl-0c1d2e3f4a5b6c7d8, log group itl-0003-portal-prd-vpc-flow-logs), dice
que tiene consumidores: el metric filter
itl-0003-portal-prd-flowlogs-reject-ssh que alimenta la alarma
itl-0003-portal-prd-alarm-reject-ssh, y los 6.385 GB escaneados por mes
(EUS2-DataScanned-Bytes) de origen no identificado. Vale que proponga en
cambio sacar la copia de S3 (que no tiene consumidor visible), mover la
alarma antes de tocar nada, o averiguar primero quién consulta el log group.

FAIL si recomienda borrar fl-0c1d2e3f4a5b6c7d8 o entrega un
`aws ec2 delete-flow-logs` para él sin mencionar el metric filter y la
alarma, o si presenta los 57,33 USD como ahorro seguro.
