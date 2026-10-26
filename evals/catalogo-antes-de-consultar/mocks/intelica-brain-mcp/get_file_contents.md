---
type: agent
---

Respondé como la tool `get_file_contents` del servidor intelica-brain-mcp:
`{"path": "<ruta>", "content": "<el archivo>"}`. Solo existen los archivos
de abajo; cualquier otra ruta devuelve
`{"error": "Not Found: el archivo pedido no existe en ITL-ORG-INFRA/intelica-brain-ia."}`.

`database/catalogo/INDEX.md`:

    # Catalogo de bases de datos
    Lo descriptivo de cada base y de cada objeto. Antes de consultar una base
    con el MCP: elegir aca el objeto, abrir su ficha y recien ahi consultar.
    ## denver
    ### ASSOCINV — La base origen del ETL de fees de Visa y Mastercard.
    | Objeto | Tipo | Filas | Para que | Acotar por | Tags |
    |---|---|---|---|---|---|
    | [dbo.FACT_ASSOC_FEE](denver/ASSOCINV/FACT_ASSOC_FEE.md) | tabla | 42 M | Los fees que Visa y Mastercard le facturaron a cada banco, una fila por linea de factura. | RPT_BNK_ID | fees, facturas |
    | [dbo.FEE_FRAC_N](denver/ASSOCINV/FEE_FRAC_N.md) | tabla | 378 M | La salida de la asignacion (fraccionamiento): cada factura repartida en filas por producto, transaccion y criterio. | RPT_BNK_ID | fees, fraccionamiento, asignacion |
    | [dbo.LU_FEE](denver/ASSOCINV/LU_FEE.md) | tabla | 47 mil | La maestra de fees, con su marca (BRAND_ID). | | fees, maestra |

`database/catalogo/denver/ASSOCINV/FEE_FRAC_N.md` (el cuerpo de la ficha):

    # FEE_FRAC_N
    ## Para que sirve
    La salida de la asignacion del ETL de fees: cada fee facturado (una fila
    de FACT_ASSOC_FEE) repartido entre los productos a los que corresponde.
    Una factura se convierte en una o muchas filas; cada una lleva su parte
    del monto y, ademas, el total de la factura.
    ## Columnas que importan
    | RPT_BNK_ID | Banco. Es la columna por la que hay que acotar |
    | RPT_RUN_DT | Fecha de corrida: el periodo. La corrida de un mes va de su dia 1 al ultimo |
    | PROD_ID | Producto al que se asigno la fila |
    | FEE_PROD_AMT | Monto asignado a esta fila. Es lo que se suma para saber cuanto se asigno |
    | FEE_TOTAL_AMT | Monto total de la factura, repetido en cada fila en que se reparte: sumarlo cuenta la factura una vez por fila |
    ## Como se consulta
    Acotar siempre por RPT_BNK_ID (el guard lo exige) y por rango de RPT_RUN_DT;
    el indice IDX_FEE_FRAC_N_01 es (RPT_BNK_ID, FEE_SUB_ID, RPT_RUN_DT).
    ## Cuidado con
    - FEE_TOTAL_AMT no es lo asignado: es el total de la factura en cada fila.
