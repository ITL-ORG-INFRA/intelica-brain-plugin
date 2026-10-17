# Intelica ARCA

**ARCA** — Automated Retrieval & Context Architecture. Plugin de Claude
Code/Desktop que es la capa de conocimiento de infraestructura de
Intelica, particionada en tres dominios (`aws`, `database`, `windows`)
sobre un solo grafo: consulta lo ya documentado antes de responder, y
convierte conversaciones largas en documentacion persistida como Pull
Request en `ITL-ORG-INFRA/intelica-brain-ia`.

```
skills/
├── intelica-arca-capture/     (el metodo de extraccion que usa /intelica-arca sobre cada tramo)
├── intelica-arca/             (invocado al cerrar — "/intelica-arca")
├── intelica-arca-recall/      (consulta lo ya documentado — se auto-activa por tema)
├── intelica-arca-diagnose/    (troubleshooting en vivo — se auto-activa por tema)
├── intelica-arca-finops/      (costos, licencias y barrido de ahorro — se auto-activa por tema)
├── smith/                     (parte un problema en frentes y lanza una copia por frente — por tema o "/smith")
├── seraph/                    (revisión de seguridad por frentes, ordenada por exposición — por tema o "/seraph")
├── intelica-arca-seguridad/   (el método de seraph: escala de exposición y recetas por frente)
└── cerebro/                   (la voz con la que se responde — se auto-activa por tema)
agents/cerebro.md              (subagente para investigaciones largas)
agents/smith.md                (subagente: cada copia de smith, un frente)
agents/seraph.md               (subagente: cada copia de seraph, un frente de seguridad)
evals/                         (casos para medir a cerebro, smith y seraph con `claude plugin eval`)
```

## Los cuatro momentos

**Guardar** (hook `PreCompact`, automatico): justo antes de que Claude
Code compacte el contexto, copia el tramo que se va a resumir a
`~/.intelica-arca/sessions/<session_id>/tramo-NNN.md`, como texto legible.
No frena la compactacion ni le pide nada a Claude.

Por que en ese momento: la compactacion resume la conversacion para poder
seguir trabajando, no para documentar. Conserva el objetivo y el estado, y
descarta los identificadores exactos y el razonamiento de las decisiones —
justo lo que vale guardar.

**Cerrar** (`intelica-arca`, invocado): lanza un subagente por tramo, que
lo extrae a un fragmento con el metodo de `intelica-arca-capture`; consolida
los fragmentos, resuelve contradicciones, redacta los `.md` finales con su
fragmento de grafo, y los sube como un solo PR. Lo que vino despues de la
ultima compactacion lo extrae de la conversacion viva. Si una compactacion
quedo sin tramo (una conversacion de antes de 0.22.0, o un hook que fallo),
lo recupera del transcript.

**Consultar** (`intelica-arca-recall`): usa el grafo de conocimiento
(`find_entity`, `traverse`, `find_documents`) para preguntas sobre recursos
concretos — que security groups tiene una instancia, quien usa un SG, que
hay en una VPC — y los documentos para preguntas narrativas.

El esquema de entidades y relaciones vive en
[`KNOWLEDGE_MODEL.md`](https://github.com/ITL-ORG-INFRA/intelica-brain-ia/blob/main/KNOWLEDGE_MODEL.md)
del repo de conocimiento, no acá: describe qué es válido **en la base**, así
que va junto a lo que describe. Además es el único repo que `get_file_contents`
alcanza, así que desde ahí se puede leer en vivo — cuando estaba en este repo
era inalcanzable, y cualquier intento de consultarlo terminaba en un 404.

El vocabulario está igual **inline** en el `SKILL.md` de `intelica-arca`, que
es lo que hace que funcione sin ir a buscar nada.

**Diagnosticar** (`intelica-arca-diagnose`): distinto de consultar — es
para un problema activo, no una pregunta informativa ("no puedo conectar A
con B", "me tira access denied"). Primero mira el grafo por si ya está la
respuesta; si no, propone el comando exacto de AWS CLI a correr —
**siempre de solo lectura, nunca lo ejecuta el** — explica qué va a
devolver, y espera que le pegues la salida para seguir. No persiste nada
por su cuenta: lo que se descubre ahí lo captura `intelica-arca-capture`
como cualquier otra conversación.

El merge del PR siempre queda a revision humana — no existe tool de merge,
a proposito.

## Que es Python y que es criterio

El trabajo pesado no lo hace el LLM. Deduplicar 300 entidades por ID,
calcular fechas, slugs y nombres de rama, y numerar los fragmentos son
tareas deterministas: las hacen scripts (`scripts/` de cada skill), exactas
y sin costo de tokens. El LLM solo decide **que importa** de la
conversacion y **resuelve las contradicciones** al consolidar — que es lo
que no se puede scriptear.

## Requisito: el servidor MCP

Este plugin **no reemplaza** el servidor MCP `intelica-brain-mcp`
(repo separado: `ITL-ORG-INFRA/intelica-arca-mcp`) — lo necesita. `intelica-arca`
usa `push_knowledge` para persistir en GitHub, y `intelica-arca-recall` usa
`find_entity` / `traverse` / `find_documents` / `get_file_contents` para
consultar.

El plugin ya trae su propio `.mcp.json` (en la raiz de este repo), asi que
instalar el plugin **registra el servidor automaticamente** — no hace
falta que cada proyecto tenga su propio `.mcp.json` por separado.

**No hace falta configurar ninguna variable de entorno.** El servidor
anuncia su propio authorization server OAuth (`token-issuer`), asi que al
instalar el plugin y apretar "Conectar" en la pantalla de Conectores,
Claude te lleva al login de FinOps que ya usas para todo lo demas — con
esa sesion alcanza, no hay token que copiar ni pegar. Cada persona
autentica con su propia cuenta de FinOps, no con una credencial compartida.

Si por algun motivo preferis un token personal fijo en vez del login (por
ejemplo para automatizar algo fuera de Claude Desktop/Code), todavia podes
generarlo a mano en `/generate-token` del portal de FinOps y pegarlo en el
header `Authorization: Bearer <token>` de tu propio cliente MCP — pero ya
no es el camino que usa este plugin.

### Plan Team: puede necesitar habilitacion del owner

En workspaces de Claude Team/Enterprise, agregar un conector MCP remoto
nuevo suele estar deshabilitado hasta que un admin/owner del workspace
habilita "Custom Connectors" a nivel organizacion (Settings → Connectors).
Si el instalador te aparece bloqueado, pedile eso al owner antes de seguir
— no es un problema de esta configuracion.

## Instalar el plugin

Una vez que este contenido este pusheado a un repo de GitHub:

```
/plugin marketplace add <owner>/<nombre-del-repo>
/plugin install intelica-arca@intelica-arca-marketplace
```

Reemplaza `<owner>/<nombre-del-repo>` por el repo real donde vive esto
(por ejemplo `ITL-ORG-INFRA/intelica-brain-plugin`).

## El hook de captura

El hook viene **incluido en el plugin** (`hooks/hooks.json`) y se registra
solo al instalarlo — no hay que tocar `settings.json`. Usa
`${CLAUDE_PLUGIN_ROOT}` para resolver su propia ruta, asi que no se rompe si
moves el repo de lugar.

Si por algun motivo no queres el hook, deshabilita el plugin o quita ese
archivo: `/intelica-arca` sigue funcionando igual, porque recupera los tramos
del transcript de la sesion (`~/.claude/projects/*/<session_id>.jsonl`)
cortando en cada compactacion. El hook existe para no depender de que ese
archivo siga ahi y con el mismo formato.

## Uso

Al cerrar una conversacion que valga documentar:

```
/intelica-arca
```

o, para revisar los archivos antes de que se suban:

```
/intelica-arca --full
```

No se activa por el tema de la conversacion — solo con esas invocaciones.
`intelica-arca-recall` si puede activarse solo cuando preguntas algo que
podria estar ya documentado.

## Staging local

En `~/.intelica-arca/sessions/<session_id>/` viven los tramos
(`tramo-001.md`, ...), su indice `tramos.json` con el rango de lineas del
transcript de cada uno, y los fragmentos extraidos (`001.json`, ...): el
fragmento de un tramo lleva su mismo numero. **Nunca se borran** y **nunca
van a GitHub**: son material de trabajo, no conocimiento — un tramo es la
conversacion cruda, con la salida de las tools. Si un PR sale mal o queres
re-curar con otro criterio, el crudo sigue ahi.

Para moverlos a otra ruta: `export INTELICA_ARCA_STAGING=/otra/ruta`.
