# Arquitectura de Intelica ARCA (plugin)

Documento para quien mantenga este repo a futuro (vos, o yo en otra
sesión) — no lo lee Claude al correr un skill, solo lo que cada `SKILL.md`
referencia explícitamente.

## Qué es esto

**ARCA** — Automated Retrieval & Context Architecture. La capa de
conocimiento de infraestructura de Intelica, como plugin de Claude
Code/Desktop. Particionada en tres dominios — `aws`, `database`,
`windows` — sobre un solo repo y un solo grafo, porque las relaciones
cruzadas entre dominios (una base de datos que corre en una EC2, un
servidor Windows que tambien es una instancia AWS) son parte del valor.
Dos lados: consultar lo ya documentado antes de responder, y convertir
conversaciones en documentación persistida como PR en
`ITL-ORG-INFRA/intelica-brain-ia`.

No incluye el servidor MCP — eso vive en `ddvloayza/intelica-brain-mcp`
(Lambda + Function URL). Este plugin son los Skills que usan sus tools.

## Los tres momentos

```
DURANTE la conversación                    (automático)
  contexto se llena
       ↓
  hook PreCompact frena la compactación (exit 2)
       ↓
  intelica-arca-capture extrae y escribe:
       ~/.intelica-arca/sessions/<session_id>/001.json
       ↓
  compactación nativa sigue su curso
       ↓
  se repite → 002.json, 003.json...


AL CERRAR                                  (/intelica-arca)
  consolidate.py: merge + dedup de los NNN.json
       ↓
  el skill resuelve contradicciones y redacta
       ↓
  build_push_args.py: fecha, slug, rama, rutas
       ↓
  push_knowledge → PR
       ↓
  vos mergeás  ← único gate humano


AL PREGUNTAR (informativo)                 (intelica-arca-recall)
  find_entity / traverse / find_documents   → grafo
  get_file_contents                         → documentos


AL DIAGNOSTICAR (problema activo)          (intelica-arca-diagnose)
  primero mira el grafo (igual que recall)
       ↓
  si no alcanza: propone UN comando de solo lectura, explica que devuelve
       ↓
  espera que le pegues la salida — nunca lo ejecuta el
       ↓
  parsea, responde, y si hace falta propone el siguiente
       ↓
  no persiste nada — lo que se encontro lo agarra capture, como cualquier
  otra conversacion
```

## Por qué la captura corre en la compactación

La compactación nativa de Claude Code genera un resumen **optimizado para
que Claude siga trabajando**, no para documentar: conserva el objetivo,
las decisiones clave y el estado actual, pero pierde los identificadores
exactos, los casos borde y el razonamiento detrás de cada decisión — justo
el material que vale documentar.

Se evaluó capturar ese resumen nativo en vez de extraer aparte, y se
descartó por dos motivos verificados: está optimizado para otra cosa
(pierde lo que necesitamos), y su formato en la transcripción es interno e
inestable entre versiones de Claude Code, así que parsearlo se rompería
solo.

## Por qué el hook no extrae, solo frena

Un hook de Claude Code es un comando de shell — no puede razonar sobre la
conversación. Lo que sí puede es elegir el momento y devolverle el control
a Claude, que todavía tiene el contexto completo: con exit code 2 frena la
compactación y le muestra un mensaje. El hook decide *cuándo*; el skill
hace *qué*.

El hook se registra solo al instalar el plugin, via `hooks/hooks.json` con
`${CLAUDE_PLUGIN_ROOT}` — no hace falta editar `settings.json`, y la ruta no
depende de donde este clonado el repo.

Un limite a tener presente: un hook **no puede invocar un skill**. Solo le
manda el mensaje a Claude por stderr, y Claude decide invocarlo. La captura
no es deterministica como un cron: depende de que Claude actue sobre ese
mensaje.

`hooks/precompact-capture.sh` deja un archivo `.capturing` como marca para
no frenar dos veces la misma compactación — sin eso, hook y skill se
bloquearían mutuamente en loop. Y si no puede leer el `session_id`, sale
con 0 en vez de frenar: perder una captura es molesto, dejar la sesión
trabada es peor.

## Por qué Python y no el LLM

El corte no es por "cuántos skills" sino por **qué es determinista y qué
necesita criterio**.

| Tarea | Dónde |
|---|---|
| Numerar fragmentos, resolver el directorio de sesión, timestamps | `write_capture.py` |
| Deduplicar entidades por ID acumulando propiedades | `consolidate.py` |
| Deduplicar relaciones, agrupar por cuenta | `consolidate.py` |
| Fecha real, slugs, nombre de rama, sufijo random, rutas | `build_push_args.py` |
| Validar entidades y relaciones contra `KNOWLEDGE_MODEL.md` | `build_push_args.py` |
| Serializar el `.md` y el `.graph.yaml`, y aparearlos | `build_push_args.py` |
| Decidir qué importa de la conversación | skill (criterio) |
| Resolver contradicciones entre fragmentos | skill (criterio) |
| Redactar la narrativa, el resumen y los tags | skill (criterio) |

Sobre las dos filas de validación y serialización: la regla no es "el LLM
escribe y después alguien revisa", es que **el LLM no escribe YAML**. Pasa
datos estructurados y el script emite los archivos. Un YAML mal indentado,
una referencia `graph:`/`documents:` que no coincide, o un `.graph.yaml`
en otro directorio que su `.md` dejan de ser errores posibles en vez de
errores que hay que cazar.

La validación estaba genuinamente ausente: `build_graph.py` en CI solo
rechaza entidades sin `id` y relaciones incompletas, nunca el vocabulario.
Un `type: SecurityGroup` en lugar de `Resource` + `resource_type` pasaba
el PR, pasaba CI, y quedaba en `graph.json` como un nodo que
`find_entity(entity_type="security_group")` no encuentra nunca. El error
es silencioso y solo se manifiesta como "el grafo no sabe eso".

El caso que lo justifica: una sesión larga puede dejar 8 fragmentos con 40
entidades cada uno. Deduplicar 320 leyéndolas todas es caro y el LLM lo
hace inconsistente. Python lo hace exacto y gratis.

Lo que **no** se puede scriptear: si un fragmento afirma algo que otro
después descartó, decidir cuál sobrevive y cómo se narra. Por eso
`consolidate.py` devuelve cada hecho con su número de fragmento en vez de
intentar resolverlo — el orden es la evidencia, la decisión es del skill.

## Por qué 4 skills y no más

Los skills se cargan por *progressive disclosure*: solo `name` +
`description` está siempre en contexto (~100 tokens cada uno); el
`SKILL.md` completo se carga al dispararse. Entonces partir en más skills
solo conviene si **no siempre corren juntos** — si son una secuencia fija,
los cargás todos igual y pagás las descripciones extra sin ganar nada.

- `capture` y `arca` tienen disparadores distintos (uno automático mitad de
  conversación, otro invocado al final) → separados, obligatoriamente.
- Consolidar y persistir siempre van juntos → un solo skill.
- `recall` (consulta lo ya documentado) y `diagnose` (ayuda con un problema
  activo, proponiendo comandos) responden a la misma señal superficial
  ("pregunta sobre AWS") pero con intención distinta — uno es informativo,
  el otro es troubleshooting en vivo con turnos de ida y vuelta. Fusionarlos
  diluye la identidad de `recall` ("consultar antes de responder") con algo
  que no siempre corre junto: la mitad de las preguntas de `recall` nunca
  necesitan proponer un comando.
- `diagnose` no necesita su propio camino de persistencia — lo que
  descubre lo captura `capture` igual que cualquier conversación, porque
  ese mecanismo ya es genérico. Esto simplificó el diseño original del
  "Provider" (Fase 5 de ARCA v2), que asumía que el propio Provider tenía
  que parsear y subir el resultado — ya no hace falta, esa parte quedó
  cubierta por `capture`/`arca`.

## Por qué los `.md` están en español y los `SKILL.md` en inglés

Son dos audiencias distintas, y por eso la regla no es la misma.

Los `.md` generados **los revisa y mergea una persona**, y ese merge es el
único gate de todo el sistema. El equipo habla español, así que el
documento se escribe en español: no tiene sentido poner fricción justo en
el paso que más importa que se haga con atención.

El ahorro de tokens del inglés no lo compensa. Medido sobre un documento
real del repo (`2026-07-25-analisis-metricas-denver-prd-90-dias.md`, con
`tiktoken o200k_base` como proxy — no es el tokenizador de Claude): el
inglés ahorra **9.6%**, no el ~31% que afirmaban antes estos documentos
sin ningún respaldo. La diferencia se aplasta porque estos `.md` son
densos en identificadores (`itl-0003-portal-prd-ec2-denver-02`,
`dbo.vw_active_session_history`, `period=3600`), que tokenizan idéntico
en los dos idiomas y nunca se traducen. Solo cambia la prosa que los
rodea, y es la minoría del archivo.

Los `SKILL.md` sí siguen en inglés: son instrucciones que lee Claude, no
un entregable que lea alguien del equipo, así que ahí el ahorro no compra
fricción de nadie.

Los identificadores literales (IDs, ARNs, nombres de recursos, valores de
`account`) nunca se traducen, en ningún caso — son claves de retrieval
exacto.

## Convenciones

- Rama: `docs/brain-{fecha-real}-{identificador}-{sufijo}`.
- Ruta: `inbox/{domain}/{account}/{fecha}-{slug}.md` (+ su `.graph.yaml`
  hermano). El conocimiento esta particionado en tres dominios (`aws`,
  `database`, `windows`); `{account}` solo aplica en `aws` (sigue la
  convencion existente de una subcarpeta por cuenta) — `database` y
  `windows` van directo a `inbox/{domain}/...` salvo que el tema declare
  una cuenta igual.
- Remitente del PR: lo resuelve el servidor desde el token personal
  autenticado — no es un parámetro que mande el skill, y nunca se pide
  email ni dato personal. (Antes era el valor fijo
  `enviado_intelicaBrain`; se cambió para que la autoría quede atada a
  quien autenticó de verdad, en vez de ser autodeclarada por el caller.)
- Los fragmentos de staging **nunca** se borran y **nunca** van a GitHub.
- Nunca hay tool de merge — el merge queda siempre a revisión humana.

## Estructura del repo

```
intelica-brain-plugin/
├── .claude-plugin/
│   ├── plugin.json         # manifest del plugin
│   └── marketplace.json    # se instala apuntando a este mismo repo
├── .mcp.json               # registra intelica-brain-mcp al instalar
├── hooks/
│   ├── hooks.json              # registra el hook al instalar el plugin
│   └── precompact-capture.sh   # dispara la captura
├── skills/
│   ├── intelica-arca-capture/  # automático: conversación -> staging local
│   │   └── scripts/write_capture.py
│   ├── intelica-arca/          # invocado: staging -> .md + .graph.yaml -> PR
│   │   └── scripts/
│   │       ├── consolidate.py
│   │       └── build_push_args.py
│   ├── intelica-arca-recall/   # consulta: grafo + documentos
│   └── intelica-arca-diagnose/ # troubleshooting: propone comandos, nunca los corre
└── README.md               # instalación y configuración para el equipo
```

`KNOWLEDGE_MODEL.md` ya no está acá: vive en la raíz de `intelica-brain-ia`.
Describe qué entidades y relaciones son válidas **en la base de conocimiento**,
así que va junto a lo que describe — y es el único repo que
`get_file_contents` alcanza, así que desde ahí se puede consultar en vivo.
Mientras estuvo en este repo era estructuralmente inalcanzable: el skill
decía "leé KNOWLEDGE_MODEL.md", el modelo lo buscaba en el único repo que
la tool ve, y se comía un 404.

## Historial de decisiones relevantes

- Se descartó OAuth completo (Cognito) para el servidor MCP: Cognito no
  soporta registro dinámico de clientes (RFC7591), que el cliente OAuth de
  Claude Code exige. Se optó por tokens personales emitidos desde la
  plataforma FinOps en vez de bearer compartido — sin la complejidad de
  construir un Authorization Server propio. Después el bearer compartido se
  eliminó del todo.
- Se descartó fusionar `intelica-compression` + `intelica-markdown` cuando
  el objetivo era "ir más rápido", por single-responsibility. Ese pipeline
  terminó retirado igual en 0.5.0, pero por otro motivo: asumía un solo
  pase sobre la conversación completa, y el staging local por compactación
  reemplaza esa premisa.
- Se revirtió a propósito la decisión de "contexto en proceso 100%
  efímero". El problema original era no guardar borradores de curación a
  medio hacer; el problema del staging es distinto — no perder detalle en
  la compactación. Misma mecánica, motivo distinto.
- Los fragmentos de grafo de documentos generados van en un archivo
  hermano `.graph.yaml`, no en el frontmatter: medido sobre el inventario
  real de AWS, el frontmatter llegaba al 85% del archivo (500+ entidades
  por cuenta), lo que hacía que cada lectura gastara tokens en datos que
  solo le sirven al grafo. Medido de nuevo sobre el repo entero: 848 KB de
  `.graph.yaml` contra 360 KB de documentos, o sea el 70% de cada archivo si
  fuera inline. Ver `KNOWLEDGE_MODEL.md` en `intelica-brain-ia`.
