---
type: agent
---

Respondé como la tool `get_file_contents` del servidor intelica-brain-mcp:
`{"path": "<ruta>", "content": "<el archivo>"}`. Solo existen los archivos
de abajo; cualquier otra ruta devuelve
`{"error": "Not Found: el archivo pedido no existe en ITL-ORG-INFRA/intelica-brain-ia."}`.

`database/catalogo/INDEX.md`:

    # Catalogo de bases de datos
    ## denver
    ### ASSOCINV — La base origen del ETL de fees de Visa y Mastercard.
    | Objeto | Tipo | Filas | Para que | Acotar por | Tags |
    |---|---|---|---|---|---|
    | [dbo.MAR_FEE_DATA](denver/ASSOCINV/MAR_FEE_DATA.md) | tabla | 715 mil | Tasa de aprobacion actual y minima, diferencia y fee aplicado por banco, BIN, segmento y mes; su proposito de negocio no esta documentado (hipotesis: la tabla final de la carga de reportes MAR de Visa). | | MAR, approval rate, BIN, sin documentar |

`database/catalogo/denver/ASSOCINV/MAR_FEE_DATA.md` (el cuerpo de la ficha):

    ## Para que sirve
    Su proposito de negocio no esta documentado todavia. Ninguna conversacion
    curada la nombra; lo que sigue sale de describir en Denver Dev.
    Por las columnas, cada fila asocia un archivo (FILE_PATH), un mes
    (MONTH_ID), un banco, un BIN y un segmento con una tasa de aprobacion
    actual, una minima, su diferencia y un fee aplicado.
    Hipotesis, sin verificar: es la tabla final de la carga de reportes
    Minimum Approval Rate (MAR) de Visa que describe el instructivo
    INS-CORP-FEE-06. Ese instructivo no nombra ninguna tabla ni proc.
    ## Quien la escribe y cuando
    No documentado. No se identifico que proc o ejecutable la llena.
    ## Diferencias entre entornos
    No documentadas. Solo se verifico que existe en Dev.
