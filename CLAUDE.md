# intelica-brain-plugin

El plugin de Claude Code de Intelica: las skills de ARCA, el agente `cerebro`,
el hook de captura, y la declaración de los dos servidores MCP.

**Este repo es también el marketplace del que instala el equipo.** Cada push a
`main` cambia lo que la gente recibe al actualizar. Por eso el código de los
servidores vive aparte, en `ITL-ORG-INFRA/intelica-arca-mcp`.

```
.claude-plugin/plugin.json       metadatos y version
.claude-plugin/marketplace.json  lo que lee el cliente para ofrecer actualizaciones
.mcp.json                        los dos servidores MCP que el plugin declara
skills/                          7 skills: cerebro es la puerta, smith se multiplica, las 5 de ARCA el resto
agents/cerebro.md                el agente que cruza el grafo con el estado en vivo
agents/smith.md                  una copia de smith: investiga un frente de un problema
evals/                           casos de `claude plugin eval` para medir a cerebro y a smith
hooks/                           PreCompact, que dispara la captura
```

## La versión vive en DOS archivos

`plugin.json` es el que uno recuerda tocar. **`marketplace.json` es el que el
cliente lee** para decidir si ofrece actualizar. Si se desincronizan, el
cambio existe en `main` y nadie lo recibe: el botón "Actualizar" queda gris y
no hay ningún error que lo explique.

Antes de publicar cualquier versión:

```bash
./scripts/check-version.sh
```

Esto ya pasó tres veces. El fallo es silencioso: la única señal es que no
pasa nada.

## Reglas de trabajo

**Nunca hagas merge de un PR.** Todo cambio va como Pull Request; el merge es
una decisión humana en GitHub.

**No ejecutes nada contra AWS.** Si un paso lo necesita, dejá el script listo
para que lo corra Diego.

**Seguí el idioma de cada archivo.** Los `SKILL.md` están en inglés; el agente
`cerebro` y los documentos del repo de conocimiento, en castellano técnico sin
adornos. No unifiques por gusto.

**Una skill se escribe para que se dispare bien.** El campo `description` del
frontmatter es lo que decide si se activa: tiene que decir *cuándo* usarla y
*cuándo no*, con los términos que alguien usaría al pedirlo. Un `description`
que solo describe qué hace la skill se dispara mal.

## Las skills, y cuándo entra cada una

| Skill | Se activa |
|---|---|
| `cerebro` | **Sola, por tema**: cualquier pregunta que necesite consultar las cuentas o el grafo. Es la voz con la que se responde |
| `intelica-arca-recall` | Sola, por tema: preguntas sobre infraestructura ya documentada |
| `intelica-arca-diagnose` | Un problema activo. Consulta en vivo con las tools de `intelica-aws` |
| `intelica-arca-finops` | Sola, por tema: costos, licencias, quién usa qué. Recetas y facturación ya verificada |
| `intelica-arca-capture` | Por el hook PreCompact. Nunca a mano |
| `intelica-arca` | Solo con `/intelica-arca`. Cierra la conversación en un PR |
| `smith` | Sola, por tema: un problema que se parte en frentes independientes (barrer una cuenta buscando ahorro, auditar varias cuentas, un diagnóstico con varias hipótesis). También con `/smith` |

`diagnose` dejó de proponer comandos para que alguien los pegue: ahora consulta
directo. Si el servidor `intelica-aws` no está conectado, vuelve al modo viejo
y lo dice.

`cerebro` y `recall` se solapan a propósito en la zona documental: las dos
empiezan por el grafo. La diferencia es el alcance — `cerebro` sigue hacia el
estado actual y responde con identidad; `recall` se queda en lo documentado.
Si en la práctica se pisan de forma molesta, la que hay que acotar es
`recall`, no `cerebro`.

## El agente cerebro

Cruza las dos fuentes —el grafo documentado y el estado actual de las cuentas—
porque ninguna alcanza sola: el grafo envejece y la infraestructura no explica
sus motivos. **Cuando las dos no coinciden, eso es el hallazgo**, y se reporta
con las dos versiones.

No declara `tools` a propósito: el prefijo de las tools MCP cambia según cómo
esté conectado el servidor (vía plugin, vía conector personalizado), así que
una lista fija lo dejaría sin herramientas en la mitad de los casos. La
barrera real no es esa lista — el rol detrás tiene un `Deny` de IAM.

Corre con `opus` y tiene `memory: user`: un directorio propio en
`~/.claude/agent-memory/intelica-arca-cerebro/` por persona, para lo que aprende operando
las tools. Lo que le sirve al equipo sigue yendo al grafo. Precarga
`intelica-arca-recall` (el manual del grafo) e `intelica-arca-finops`; no
precarga `diagnose`, que repite su propio método y le sumaría unos 1.300
tokens a cada arranque. En un plugin se ignoran `permissionMode`, `hooks`,
`mcpServers` e `initialPrompt`: no los agregues ahí.

**Antes y después de tocar su prompt, corré los evals** (`evals/README.md`,
requiere Claude Code 2.1.269+). Cada error verificable de cerebro es un caso
nuevo.

## Smith: la skill que se multiplica y el agente que es cada copia

Smith es un patrón, no un especialista: **partir, multiplicar, consolidar.**
Un subagente no puede lanzar otros, así que se multiplica la sesión
principal:

- **La skill `smith`** parte el problema en frentes que no se pisan (por
  cuenta, por rubro de costos, por hipótesis, por cluster), junta una sola
  vez lo que todos necesitan —la factura, la lista de cuentas, la hora del
  incidente—, lanza una copia por frente en el mismo mensaje y consolida:
  una fila por recurso, las contradicciones a la vista, la cobertura de cada
  frente, y la pregunta de por dónde seguir. Para profundizar, retoma con
  `SendMessage` la copia que encontró el hallazgo.
- **El agente `smith`** es cada copia. Recibe un mandato (problema, frente,
  alcance, contexto ya obtenido), se queda en su frente, y devuelve
  hallazgos con un formato fijo para que se puedan juntar. No escribe su
  memoria cuando es copia: varias se pisarían. Devuelve "Para memoria:" y
  guarda la skill.

Hereda de cerebro el modelo, `memory: user`
(`~/.claude/agent-memory/intelica-arca-smith/`), la ausencia de `tools` y las
reglas de solo lectura. Precarga `intelica-arca-recall` e
`intelica-arca-finops`; `diagnose` la carga cuando el frente es un problema
activo, para no sumarle esos tokens a cada copia.

**Lo de costos no vive en smith.** El método (precio unitario de la
factura, medido contra estimado, Terraform si hay tags de IaC) y el
catálogo de chequeos están en `intelica-arca-finops`, sección "Savings
sweep". Los chequeos deterministas son cuatro tools de `intelica-aws`
(`finops_red`, `finops_almacenamiento`, `finops_computo`, `finops_logs`),
una por frente; mientras no estén desplegadas, las copias usan las recetas
de `aws_api` de esa misma sección.

Lo que sabe de las tools está escrito como límite verificado (sin
`StartQuery`, `sort_by` sobre fechas, claves no ASCII). Si un límite cambia
en `intelica-arca-mcp`, se corrige ahí también.

## Después de cambiar algo

1. `./scripts/check-version.sh`
2. Bump en **los dos** archivos de versión
3. PR, nunca merge directo
4. Recién cuando se mergea, el equipo lo recibe al actualizar el plugin
