# Evals de cerebro y de smith

Casos sacados de situaciones reales, cada uno con una respuesta que se puede
verificar. Miden si un agente mejora o empeora con un cambio en su prompt,
su modelo o sus skills, en vez de juzgarlo a ojo. Cada caso lleva en `tags`
el agente que mide.

## cerebro

| Caso | Qué prueba | De dónde salió |
|---|---|---|
| `permiso-quicksight-verificado` | Afirma un permiso solo después de verificarlo | Se dijo que `ReadOnlyAccess` incluía QuickSight sin leer la política; no incluye nada |
| `baja-a-mitad-de-mes` | Sabe que una baja de QuickSight a mitad de mes no ahorra ese mes | La factura de portal-dev de septiembre (2026-10-08) |
| `lista-redonda` | No toma como total una lista que vuelve con un tamaño de página exacto | El bug de paginación de `aws_api` devolvía 50 eventos de CloudTrail sin avisar |
| `usuario-sin-uso` | Mide el uso de una licencia con CloudTrail, no con el campo `Active` | Los clientes de portal-prod figuran `Active: false` y usan QuickSight a diario |
| `no-escribe` | Ante un pedido de cambio, entrega el comando y no lo ejecuta | El diseño de solo lectura |

## smith

| Caso | Qué prueba | De dónde salió |
|---|---|---|
| `barrido-con-cuadro` | Ante un pedido abierto de ahorro, la skill smith se multiplica en los cuatro frentes y consolida **un solo** cuadro con accionables (11 hallazgos plantados, RDS y ECR limpios), y pregunta por cuál empezar | El diseño de smith como patrón de multiplicación |
| `diagnostico-en-frentes` | En un diagnóstico (portal-api no conecta a su RDS), se multiplica por hipótesis, encuentra el `RevokeSecurityGroupIngress` con su evidencia, descarta las otras capas y entrega el arreglo sin aplicarlo | Que el patrón sirva para algo que no es costos |
| `s3-por-nat` | Encuentra la tabla de rutas sin el endpoint de S3, verifica con flow logs que el tráfico es S3 y entrega `modify-vpc-endpoint` sin ejecutarlo | Los backups de DENVER en portal-prod (2026-10-10) |
| `medido-vs-estimado` | No presenta el ahorro de cruce de AZ como medido: el cargo regional es de toda la cuenta | El mismo análisis: NAT 161–262 USD medido, entre AZ 67–109 estimado |
| `flow-logs-con-consumidor` | No recomienda sacar la copia de CloudWatch sin ver antes el metric filter, la alarma y quién escanea el log group | Los flow logs duplicados de portal-prod |
| `terraform-drift` | Con tags de Terraform, el cambio de gp2 a gp3 va por el módulo y no por CLI | Un cambio por CLI lo revierte el próximo `apply` |
| `precio-de-la-factura` | Calcula el precio por GB con la factura de esa cuenta, no con la tabla pública ni con el 0,0442 de portal-prod que el prompt trae de ejemplo | La regla del precio unitario |
| `no-escribe-smith` | Ante un pedido de aplicar un ahorro, entrega el comando con su rollback y no lo ejecuta | El caso `no-escribe` de cerebro, con un cambio de red |

`s3-por-nat`, `medido-vs-estimado` y `no-escribe-smith` comparten el estado
de portal-prod en su `aws_api.md`: los tres archivos son iguales y se
corrigen juntos.

Los dos casos de multiplicación arrancan en la sesión principal y no con
"Usá el subagente": la que se multiplica es la skill. Por eso su
`allowed_tools` incluye `Skill`, `Agent`, `SendMessage` y `aws_api` (la
sesión principal pide la factura una vez). Los nombres de las tools MCP en
`allowed_tools` son los que tienen en una sesión con el plugin instalado;
no está verificado que el eval las nombre igual.

Los mocks no incluyen las tools `finops_*`: los evals miden el camino con
`aws_api`. Cuando estén desplegadas, cada caso de costos necesita además un
mock `fixed` con la salida de su tool.

## Correrlos

Requiere Claude Code **2.1.269 o posterior** (`claude --version`).

```bash
claude plugin eval
claude plugin eval --ablation with-without
```

Solo los de un agente: `claude plugin eval --tag smith` (o `--tag cerebro`).
Un caso: `--case s3-por-nat`.

`--ablation with-without` corre también sin el plugin y muestra la diferencia:
es lo que dice si el agente aporta algo respecto del modelo solo. El resultado
queda en `evals/results/<fecha>/` (`report.html` y `aggregate-result.json`).

**Cuesta uso real.** Cada caso corre 3 veces por defecto, con el modelo del
agente (`opus` en los dos), y los graders `llm` consultan a un juez 3 veces más.

## Cómo funcionan las respuestas de AWS

Los servidores MCP **no se conectan** durante un eval: cada tool responde desde
un archivo en `mocks/`. `list_accounts` y las tools del grafo tienen una
respuesta fija común a todos los casos (`evals/mocks/`). `aws_api` es
`type: agent`: un modelo responde siguiendo la descripción del estado de la
cuenta que tiene cada caso en `<caso>/mocks/intelica-aws/aws_api.md`, porque una
sola tool cubre cientos de operaciones distintas.

Lo que no se pudo verificar sin correrlo, y conviene revisar en la primera
corrida:

- El nombre de la carpeta de cada servidor en `mocks/` es la clave del
  `.mcp.json` (`intelica-aws`, `intelica-brain-mcp`); la documentación no lo
  dice explícito.
- Los graders miran la respuesta final de la sesión principal, que es la que
  resume lo que hizo el agente. No está documentado si `tool_used` ve las
  llamadas que hace un subagente, por eso ningún caso depende de eso.
- Los dos agentes tienen `memory: user`: si el directorio de memoria
  persiste entre corridas, una corrida puede influir en la siguiente.

## Agregar un caso

Cada vez que un agente se equivoque en algo que se pueda verificar, ese
error es un caso nuevo: `prompt.md` con la pregunta, `mocks/intelica-aws/aws_api.md`
con el estado de la cuenta que la responde, y al menos un grader en
`graders/`.
