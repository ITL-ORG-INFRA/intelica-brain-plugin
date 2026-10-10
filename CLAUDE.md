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
skills/                          6 skills: cerebro es la puerta, las 5 de ARCA el resto
agents/cerebro.md                el agente que cruza el grafo con el estado en vivo
evals/                           casos de `claude plugin eval` para medir a cerebro
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

## Después de cambiar algo

1. `./scripts/check-version.sh`
2. Bump en **los dos** archivos de versión
3. PR, nunca merge directo
4. Recién cuando se mergea, el equipo lo recibe al actualizar el plugin
