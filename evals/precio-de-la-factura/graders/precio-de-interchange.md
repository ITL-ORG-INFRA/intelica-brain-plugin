---
type: llm
---

PASS si la respuesta final calcula el precio por GB con la factura de
interchange-prod —78,71 USD / 1.874 GB = 0,042 USD/GB— y da un ahorro de
alrededor de 50 USD por mes (entre 49 y 52) en procesamiento del NAT. Vale
que aclare que las horas del NAT (63,60 USD) no cambian.

FAIL si usa un precio de lista de AWS (0,045, 0,048, 0,052 u otro), si usa
el 0,0442 USD/GB de portal-prod, o si el ahorro de procesamiento queda fuera
de 49 a 52 USD por mes.
