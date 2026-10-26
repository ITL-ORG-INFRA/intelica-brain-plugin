---
type: llm
---

PASS si la respuesta final da por producto el monto **asignado** del banco
225 en septiembre de 2026: 12480.35 (PROD_ID 101), 8215.10 (102) y 3904.55
(103), o su total 24600.00, y dice que sale de sumar FEE_PROD_AMT de
ASSOCINV.dbo.FEE_FRAC_N. Suma, sin ser obligatorio, que cite la ficha del
catálogo (database/catalogo/denver/ASSOCINV/FEE_FRAC_N.md) o explique que
FEE_TOTAL_AMT repite el total de la factura en cada fila.

FAIL si presenta como monto asignado las sumas de FEE_TOTAL_AMT (61920.00,
40880.00, 19500.00, o su total 122300.00), si da números que no salen de
la base, o si dice no poder responder sin haber consultado.
