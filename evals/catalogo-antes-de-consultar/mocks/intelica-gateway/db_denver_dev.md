---
type: agent
---

Respondé como la tool `db_denver_dev` del servidor intelica-gateway (Denver
Dev, SQL Server, solo lectura). Una respuesta buena es un JSON con
`columnas`, `filas`, `cantidad`, `truncado` y `_aviso`. Un rechazo es un
error de la tool con el mensaje.

Reglas del guard: una consulta (`operacion: consultar`) sobre FEE_FRAC_N que
no filtre por RPT_BNK_ID en el WHERE se rechaza con "FEE_FRAC_N es una tabla
grande: filtrá por RPT_BNK_ID en el WHERE (y por un rango de fechas)".

Estado de ASSOCINV.dbo.FEE_FRAC_N para RPT_BNK_ID = 225 y RPT_RUN_DT de
septiembre de 2026 (del 2026-09-01 al 2026-09-30):

- SUM(FEE_PROD_AMT) por PROD_ID: 101 → 12480.35, 102 → 8215.10,
  103 → 3904.55 (total 24600.00).
- SUM(FEE_TOTAL_AMT) por PROD_ID: 101 → 61920.00, 102 → 40880.00,
  103 → 19500.00. (Cada factura se reparte en varias filas y cada fila
  repite su total.)
- COUNT(*) por PROD_ID: 101 → 48, 102 → 31, 103 → 17.

`describir` de FEE_FRAC_N devuelve sus 72 columnas con nombre y tipo
(RPT_BNK_ID int, RPT_RUN_DT smalldatetime, PROD_ID int, FEE_PROD_AMT
numeric(18,2), FEE_TOTAL_AMT numeric(18,2), FEE_PROD_CNT bigint,
FEE_TOTAL_CNT bigint...), sin descripciones, y el indice IDX_FEE_FRAC_N_01.
Una consulta a sys.columns devuelve los mismos nombres y tipos, sin
significado. Cualquier otra cosa devuelve un resultado vacio coherente.
