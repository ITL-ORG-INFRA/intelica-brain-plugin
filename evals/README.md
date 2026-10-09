# Evals de cerebro

Cinco casos sacados de situaciones reales, cada uno con una respuesta que se
puede verificar. Miden si cerebro mejora o empeora con un cambio en su prompt,
su modelo o sus skills, en vez de juzgarlo a ojo.

| Caso | Qué prueba | De dónde salió |
|---|---|---|
| `permiso-quicksight-verificado` | Afirma un permiso solo después de verificarlo | Se dijo que `ReadOnlyAccess` incluía QuickSight sin leer la política; no incluye nada |
| `baja-a-mitad-de-mes` | Sabe que una baja de QuickSight a mitad de mes no ahorra ese mes | La factura de portal-dev de septiembre (2026-10-08) |
| `lista-redonda` | No toma como total una lista que vuelve con un tamaño de página exacto | El bug de paginación de `aws_api` devolvía 50 eventos de CloudTrail sin avisar |
| `usuario-sin-uso` | Mide el uso de una licencia con CloudTrail, no con el campo `Active` | Los clientes de portal-prod figuran `Active: false` y usan QuickSight a diario |
| `no-escribe` | Ante un pedido de cambio, entrega el comando y no lo ejecuta | El diseño de solo lectura |

## Correrlos

Requiere Claude Code **2.1.269 o posterior** (`claude --version`).

```bash
claude plugin eval
claude plugin eval --ablation with-without
```

`--ablation with-without` corre también sin el plugin y muestra la diferencia:
es lo que dice si cerebro aporta algo respecto del modelo solo. El resultado
queda en `evals/results/<fecha>/` (`report.html` y `aggregate-result.json`).

**Cuesta uso real.** Cada caso corre 3 veces por defecto, con el modelo del
agente (`opus`), y los graders `llm` consultan a un juez 3 veces más.

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
  resume lo que hizo cerebro. No está documentado si `tool_used` ve las
  llamadas que hace un subagente, por eso ningún caso depende de eso.
- El agente tiene `memory: user`: si el directorio de memoria persiste entre
  corridas, una corrida puede influir en la siguiente.

## Agregar un caso

Cada vez que cerebro se equivoque en algo que se pueda verificar, ese error es
un caso nuevo: `prompt.md` con la pregunta, `mocks/intelica-aws/aws_api.md`
con el estado de la cuenta que la responde, y al menos un grader en
`graders/`.
