# Intelica ARCA

**ARCA** — Automated Retrieval & Context Architecture. Plugin de Claude
Code/Desktop que es la capa de conocimiento de infraestructura de
Intelica, particionada en tres dominios (`aws`, `database`, `windows`)
sobre un solo grafo: consulta lo ya documentado antes de responder, y
convierte conversaciones largas en documentacion persistida como Pull
Request en `ITL-ORG-INFRA/intelica-brain-ia`.

```
skills/
├── intelica-arca-capture/     (automatico, lo dispara el hook PreCompact)
├── intelica-arca/             (invocado al cerrar — "/intelica-arca")
├── intelica-arca-recall/      (consulta lo ya documentado — se auto-activa por tema)
└── intelica-arca-diagnose/    (troubleshooting en vivo — se auto-activa por tema)
```

## Los cuatro momentos

**Capturar** (`intelica-arca-capture`, automatico): justo antes de que
Claude Code compacte el contexto, guarda lo relevante de la conversacion en
staging local (`~/.intelica-arca/sessions/<session_id>/`). Corre solo,
disparado por el hook — no se invoca a mano.

Por que en ese momento: la compactacion resume la conversacion para poder
seguir trabajando, no para documentar. Conserva el objetivo y el estado, y
descarta los identificadores exactos y el razonamiento de las decisiones —
justo lo que vale guardar. La captura corre mientras todo eso todavia esta
en contexto.

**Cerrar** (`intelica-arca`, invocado): consolida los fragmentos de esa
sesion, resuelve contradicciones, redacta los `.md` finales con su fragmento
de grafo, y los sube como un solo PR. Todo en un pase. Si la conversacion
fue corta y nunca se compacto, extrae directo de la conversacion viva.

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
(repo separado: `ddvloayza/intelica-brain-mcp`) — lo necesita. `intelica-arca`
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
(por ejemplo `ddvloayza/intelica-brain-plugin`).

## El hook de captura

El hook viene **incluido en el plugin** (`hooks/hooks.json`) y se registra
solo al instalarlo — no hay que tocar `settings.json`. Usa
`${CLAUDE_PLUGIN_ROOT}` para resolver su propia ruta, asi que no se rompe si
moves el repo de lugar.

Si por algun motivo no queres la captura automatica, deshabilita el plugin o
quita ese archivo: `/intelica-arca` sigue funcionando igual, solo que al no
encontrar fragmentos extrae de la conversacion viva. Se pierde el detalle de
las conversaciones largas ya compactadas, que es justo lo que el hook salva.

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

Los fragmentos de captura viven en `~/.intelica-arca/sessions/<session_id>/`
como `001.json`, `002.json`, etc. **Nunca se borran** y **nunca van a
GitHub**: son material de trabajo, no conocimiento. Si un PR sale mal o
queres re-curar con otro criterio, el crudo sigue ahi.

Para moverlos a otra ruta: `export INTELICA_ARCA_STAGING=/otra/ruta`.
