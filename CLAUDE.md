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
skills/                          4 skills de ARCA
agents/cerebro.md                el agente que cruza el grafo con el estado en vivo
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

## Las cuatro skills, y cuándo entra cada una

| Skill | Se activa |
|---|---|
| `intelica-arca-recall` | Sola, por tema: preguntas sobre infraestructura ya documentada |
| `intelica-arca-diagnose` | Un problema activo. Consulta en vivo con las tools de `intelica-aws` |
| `intelica-arca-capture` | Por el hook PreCompact. Nunca a mano |
| `intelica-arca` | Solo con `/intelica-arca`. Cierra la conversación en un PR |

`diagnose` dejó de proponer comandos para que alguien los pegue: ahora consulta
directo. Si el servidor `intelica-aws` no está conectado, vuelve al modo viejo
y lo dice.

## El agente cerebro

Cruza las dos fuentes —el grafo documentado y el estado actual de las cuentas—
porque ninguna alcanza sola: el grafo envejece y la infraestructura no explica
sus motivos. **Cuando las dos no coinciden, eso es el hallazgo**, y se reporta
con las dos versiones.

No declara `tools` a propósito: el prefijo de las tools MCP cambia según cómo
esté conectado el servidor (vía plugin, vía conector personalizado), así que
una lista fija lo dejaría sin herramientas en la mitad de los casos. La
barrera real no es esa lista — el rol detrás tiene un `Deny` de IAM.

## Después de cambiar algo

1. `./scripts/check-version.sh`
2. Bump en **los dos** archivos de versión
3. PR, nunca merge directo
4. Recién cuando se mergea, el equipo lo recibe al actualizar el plugin
