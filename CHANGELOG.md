# Changelog

## 0.19.0 - 2026-10-10

- **Agente nuevo, `smith`**: recorre una cuenta por vez buscando ahorro. Arranca
  por la factura del último mes (una llamada a Cost Explorer agrupada por
  servicio y usage type) y revisa en el orden que pone la plata. Cada hallazgo
  sale con el costo actual, el ahorro con lo medido separado de lo estimado,
  la evidencia con IDs, el cambio con su rollback y su ventana, y los riesgos.
- El precio unitario se calcula con la factura: 295,52 USD / 6.692 GB =
  0,0442 USD/GB para el NAT de portal-prod en septiembre. La tabla pública no
  trae ni la región ni el descuento.
- Si el recurso tiene tags de módulo o el nombre de IaC, el cambio va por
  Terraform y el comando de CLI queda como prueba previa.
- Seis evals nuevos con el tag `smith`: `s3-por-nat`, `medido-vs-estimado`,
  `flow-logs-con-consumidor`, `terraform-drift`, `precio-de-la-factura` y
  `no-escribe-smith`. Los tres primeros salen del análisis del endpoint de S3
  de portal-prod del 2026-10-10.

## 0.18.4 - 2026-10-10

- `intelica-arca-finops`: **quién se factura, usuario por usuario**, con
  `GetCostAndUsageWithResources` agrupado por `RESOURCE_ID`: devuelve el ARN
  de cada usuario de QuickSight facturado en los últimos 14 días. Es la
  receta con la que cerebro encontró que a `hildebrando.nunez` no se le cobra
  en portal-dev.
- El usuario de un `RegisterUser` está en `requestParameters` y
  `responseElements`, no en `serviceEventDetails` (eso es solo para
  `DeleteUser`). La 0.18.1 decía lo mismo para los dos; lo corrigió cerebro
  al verificarlo en cuatro eventos.
- Los usage types de Pro: `USE1-Author-Pro-Enterprise-Month` y
  `USE1-Amazon-Q-QS-Fee`. Un solo usuario Pro dispara el cargo de US$250 de
  la cuenta (junio de 2026 en portal-dev).

## 0.18.3 - 2026-10-10

- `intelica-arca-finops`: el costo de Cost Explorer se informa una sola vez.
  Desde intelica-arca-mcp #29 el `_costo` de una respuesta de `ce` ya trae
  los US$0,01; la skill decía sumarlos a mano, y con el servidor nuevo eso
  los contaba dos veces. Ahora: si la respuesta lo trae, se usa; si no, se
  suma.

## 0.18.2 - 2026-10-10

- **El `session_id` lo pone Claude Code**: `intelica-arca` y
  `intelica-arca-capture` usan `${CLAUDE_SESSION_ID}`, que se sustituye al
  cargar el skill. Antes el cierre tenía que encontrar el id en la
  conversación, y después de dos compactaciones el mensaje del hook que lo
  traía ya estaba resumido: con un id equivocado, `consolidate.py` devuelve
  `fragment_count: 0` sin error y se pierde todo lo capturado.
- Estaba escrito desde el 2026-10-04 para la 0.17.0, pero se subió a la rama
  del PR #1 después de que se mergeara y nunca llegó a `main`.

## 0.18.1 - 2026-10-09

Ajustes de la prueba a mano de la 0.18.0 contra las cuentas reales:

- **Si no pudo consultar la cuenta, la respuesta empieza por eso**, no por un
  "sí": con el MCP sin autenticar, cerebro abrió con un "sí" sacado del
  template.
- **El código no es la cuenta**: un template dice lo que debería haber, y los
  tests y fixtures usan datos inventados. Había tomado un fixture de
  `test_quicksight.py` como estado de las cuentas.
- **A la memoria va solo lo verificado**: había guardado ese fixture y que un
  `DeleteUser` no trae el usuario, que es falso.
- `intelica-arca-finops`: el usuario de un `DeleteUser` está en el JSON del
  evento aunque `Resources` venga vacío; cómo contar usuarios facturados con
  `UsageQuantity`; las altas se prorratean por hora; `Active: false` no sirve
  ni para elegir por dónde empezar.

## 0.18.0 - 2026-10-09

- **cerebro corre con `opus`** y tiene memoria propia (`memory: user`, en
  `~/.claude/agent-memory/intelica-arca-cerebro/`): guarda lo que aprende operando las
  tools —cómo se comporta un servicio, un hueco de permisos, un error suyo—
  y lo lee al empezar. El conocimiento del equipo sigue yendo al grafo; al
  final de una investigación propone qué documentar con una línea
  "Para documentar:".
- Precarga `intelica-arca-recall` y la nueva `intelica-arca-finops`, y tiene
  `maxTurns: 80`.
- **Nueva skill `intelica-arca-finops`**: Cost Explorer (cada llamada cuesta
  US$0,01), los usage types de QuickSight y lo que se cobra por cada uno, y
  la receta para saber quién usa una licencia cruzando `ListUsers` con
  CloudTrail. Incluye lo verificado en la factura: un usuario dado de alta a
  mitad de mes se cobra desde ese día, uno borrado a mitad de mes se cobra el
  mes completo.
- cerebro conoce `quicksight_inventory`, desconfía de una lista que vuelve
  con un tamaño de página exacto sin cursor, y verifica un permiso leyendo
  la política en vez de suponerlo (`ReadOnlyAccess` no incluye QuickSight).
- **`evals/`**: cinco casos de `claude plugin eval` sacados de errores y
  hallazgos reales, con respuestas de AWS simuladas. Requiere Claude Code
  2.1.269+.

## 0.17.0 - 2026-10-04

- **Los reportes HTML van a S3**, a `reportes/` del bucket de artefactos de
  ARCA. En el repo queda el `.md`, con `reporte: <key>` en el frontmatter:
  es lo que se indexa, y lo único por lo que se encuentra el reporte.
- `build_push_args.py` acepta `report_file` por tema: valida que el HTML
  exista, deriva la key de la misma fecha y slug que el `.md`, y la devuelve
  en `reports` aparte de `files`.
- `intelica-arca` sube cada reporte antes del PR con `upload_report` y el
  `curl` que devuelve: el HTML va del disco a S3 sin pasar por el modelo,
  que antes lo tenía que reescribir entero (5k a 40k tokens por reporte).
- `intelica-arca-capture` guarda la ruta de los reportes generados, que la
  compactación pierde. `consolidate.py` los junta por ruta.
- `intelica-arca-recall` menciona el reporte y da el link con
  `get_report_url` solo si lo piden; nunca lee el HTML para responder.
- Requiere las tools `upload_report` y `get_report_url` de
  `intelica-arca-mcp`, y el permiso de `add-reports-bucket-permission.sh`.

## 0.13.0 - 2026-09-01

- **Conocimiento particionado por dominio**: `aws`, `database`, `windows`.
  Mismo repo y mismo grafo — las relaciones cruzadas entre dominios (una
  base de datos que corre en una EC2, un servidor Windows que tambien es
  una instancia AWS) siguen existiendo, solo cambia como se organizan los
  documentos y el indice.
- `KNOWLEDGE_MODEL.md` (en `intelica-brain-ia`) suma la propiedad `domain`
  y los tipos `DatabaseServer`, `Database`, `WindowsServer`, `PatchReview`,
  mas las relaciones `HOSTS_DATABASE`, `RUNS_ON`, `REVIEWED_IN`, `SAME_AS`.
- `build_push_args.py` valida `domain` (nuevo campo requerido) y escribe
  en `inbox/<domain>/...` — `aws` mantiene la subcarpeta por cuenta
  existente, `database`/`windows` empiezan planos.
- `intelica-arca` clasifica el dominio de cada tema antes de redactar
  (paso nuevo), separando en varios documentos si la conversacion mezcla
  dominios.
- `intelica-arca-recall` y `intelica-arca-diagnose` amplian sus
  descripciones y ejemplos a los tres dominios, y `recall` rutea primero
  al `INDEX.md` del dominio en vez de siempre ir a la raiz.

## 0.12.0 - 2026-08-20

- **`KNOWLEDGE_MODEL.md` se mudó a `intelica-brain-ia`**, a la raíz del repo
  de conocimiento. Describe qué entidades y relaciones son válidas **en la
  base**, así que va junto a lo que describe.
- **La razón concreta:** `get_file_contents` solo puede leer el repo que
  apunta `GITHUB_TARGET_REPO`, o sea `intelica-brain-ia`. Mientras el modelo
  vivió en este repo era **estructuralmente inalcanzable**. Se vio en vivo:
  el skill decía "leé KNOWLEDGE_MODEL.md", el modelo lo buscó en el único
  repo que la tool ve, y se comió un 404 de la API de GitHub.
- Ahora además va con frontmatter, así que `build_index.py` lo indexa y queda
  encontrable desde `INDEX.md` como cualquier otro documento.
- Verificado que los ejemplos YAML del propio modelo **no** se cuelan al
  grafo: `build_graph.py` solo lee el bloque de frontmatter del principio, no
  los bloques de código. Cero entidades de ejemplo en `graph.json`.
- El vocabulario sigue **inline** en el `SKILL.md` (0.11.0) — eso es lo que
  hace que funcione sin ir a buscar nada. El archivo es la fuente para
  personas y para CI; el inline es la copia operativa.

## 0.11.0 - 2026-08-10

- **El vocabulario del modelo ahora está inline en el `SKILL.md`.**
  `KNOWLEDGE_MODEL.md` se mencionaba por nombre pero nunca con una ruta, y
  vive en la raíz del repo del plugin — instalado queda en
  `~/.claude/plugins/cache/.../KNOWLEDGE_MODEL.md`. O sea que **nadie lo
  leía**: los tipos funcionaban solo porque estaban repetidos inline en
  `intelica-arca-capture`. Ahora los tipos de entidad, sus campos
  requeridos y los tipos de relación están en el skill que sí se carga.
- **`Incident.date` es cuándo EMPEZÓ el incidente**, no cuándo se detectó
  ni cuándo se documentó. Quedó dicho en los dos skills y en el modelo.
  Pasó de verdad: el incidente de agotamiento de IPs de pods de EKS se
  registró con la fecha en que alguien lo reportó (`2026-08-04`), mientras
  el propio documento decía que venía fallando desde el `2026-07-31` sin
  que nada alertara. Esos cuatro días de detección tardía se perdían del
  grafo, y el índice ordenaba y contestaba "cuándo pasó" con la fecha
  equivocada.
- `build_push_args.py` avisa —sin bloquear, porque `date` es opcional en el
  modelo— cuando un `Incident` viene sin fecha. No se puede validar que sea
  la de inicio y no la de detección: eso es criterio, y por eso está dicho
  en el skill.

## 0.10.0 - 2026-08-10

- **`build_push_args.py` ahora genera los archivos en vez de que el LLM
  escriba YAML a mano**, y valida entidades y relaciones contra
  `KNOWLEDGE_MODEL.md` antes de generar nada. Recibe datos estructurados
  (título, resumen, tags, cuerpo, entidades, relaciones) y devuelve el
  `.md` y su `.graph.yaml` listos, con la referencia cruzada
  `graph:`/`documents:` coherente en ambos sentidos por construcción.
- **Cierra un agujero que estaba activo:** el vocabulario del modelo no se
  chequeaba en ningún punto de la cadena. `build_graph.py` en CI solo
  rechaza entidades sin `id` y relaciones incompletas, así que un tipo
  inventado (`SecurityGroup` en vez de `Resource` con
  `resource_type: security_group`) pasaba el PR, pasaba CI y aterrizaba en
  `graph.json`, donde ninguna consulta posterior lo encontraba jamás.
- Detecta: tipos de entidad y de relación inexistentes, campos requeridos
  faltantes, `Person` (excluida a propósito por privacidad), `Document` y
  `DOCUMENTED_IN` declarados a mano cuando se derivan solos, `resource_type`
  que no es snake_case, e IPs usadas como ID. Si algo falla no genera nada
  y sale con código 1, así que un borrador roto no se puede pushear.
- Avisa sin bloquear cuando una relación apunta a una entidad declarada en
  otro documento — eso es legítimo y común.
- Descarta `seen_in` solo, que antes era un paso manual que se podía olvidar.
- Corrige una regla que había quedado engañosa: los `.graph.yaml` **sí**
  van a GitHub; lo que nunca sale de la máquina son los fragmentos de
  staging (`~/.intelica-arca/sessions/<id>/NNN.json`).

## 0.9.0 - 2026-08-09

- **Los `.md` curados ahora llevan `summary` en el frontmatter**, y los
  `tags` pasan a incluir las formas alternativas de preguntar (un
  documento sobre picos de `CPU` también lleva `rendimiento`,
  `saturacion`, `lentitud`). Eso es lo único que hay al elegir un
  documento desde `INDEX.md`: acá no hay búsqueda semántica, así que un
  documento que no se encuentra por su resumen es un documento que no
  existe.
- Es el lugar donde una persona puede codificar el vocabulario propio del
  equipo — algo que ningún mecanismo de recuperación infiere solo.
- `intelica-arca-recall` ahora busca contra el resumen y los tags, no
  solo contra el título, y se le dice explícitamente que la recuperación
  es léxica: si no calza, asumir que no está en vez de forzar un match
  débil.
- Del lado de `intelica-brain-ia` (repo aparte): `build_index.py` separa
  conversaciones de inventario y arregla el parser de frontmatter, que no
  leía ninguno de los dos estilos de lista YAML del repo — los tags nunca
  habían llegado al índice.

## 0.8.0 - 2026-08-08

- **Los `.md` generados vuelven a escribirse en español.** El merge del PR
  es el único gate humano de todo el sistema y lo hace gente que lee
  español: no tiene sentido poner fricción justo ahí.
- **El "~31% menos tokens" que justificaba el inglés (0.2.0) era falso.**
  Estaba afirmado como "medido" en tres archivos sin ningún artefacto de
  medición detrás. Medido de verdad sobre un documento real del repo
  (`2026-07-25-analisis-metricas-denver-prd-90-dias.md`, con `tiktoken
  o200k_base` como proxy): el ahorro real es **9.6%**, no 31%.
- La razón de la brecha: estos `.md` son densos en identificadores
  (`itl-0003-portal-prd-ec2-denver-02`, `dbo.vw_active_session_history`,
  `period=3600`) que tokenizan idéntico en los dos idiomas y nunca se
  traducen. Solo cambia la prosa alrededor, que es la minoría del archivo.
  Una comparación de prosa genérica sí daría algo cercano al 30%; sobre
  estos documentos, no.
- Los `SKILL.md` siguen en inglés: los lee Claude, no son un entregable
  que revise una persona, así que ahí el ahorro no le cuesta fricción a
  nadie.
- Los identificadores literales se siguen sin traducir, como siempre.

## 0.7.0 - 2026-08-08

- **Ya no hace falta configurar `INTELICA_MCP_TOKEN` a mano.** El servidor
  `intelica-brain-mcp` ahora anuncia su propio authorization server OAuth
  (`token-issuer`), asi que "Conectar" en la pantalla de Conectores lleva
  al login de FinOps directamente — sin token que copiar ni pegar, y sin
  variables de entorno que configurar en cada maquina. `.mcp.json` se
  simplifico para reflejar esto: ya no declara un header de auth estatico.
- Cada persona sigue autenticando con su propia cuenta de FinOps, no con
  una credencial compartida entre el equipo.
- El camino anterior (generar un token en `/generate-token` y pegarlo a
  mano) sigue existiendo para usos fuera de Claude Desktop/Code, pero deja
  de ser lo que usa este plugin.

## 0.6.0 - 2026-08-04

- **Nuevo `intelica-arca-diagnose`.** El "Provider" tipo recetario que
  habíamos diseñado en la arquitectura de ARCA v2 (reconoce el tipo de
  problema, propone el comando de solo lectura, la persona lo corre y
  pega la salida) nunca se había escrito como skill. Se auto-activa con
  problemas activos ("no puedo conectar A con B", "access denied") —
  distinto de `intelica-arca-recall`, que es para preguntas informativas
  sobre lo ya documentado.
- No tiene su propio camino de persistencia: lo que descubre durante el
  diagnóstico lo captura `intelica-arca-capture` igual que cualquier otra
  conversación. Esto simplifica el diseño original, que asumía que el
  Provider necesitaba parsear y subir el resultado por su cuenta.
- Primero consulta el grafo (mismas tools que `recall`) antes de proponer
  nada — no sugiere un comando para algo que ya se puede ver ahí.
- Nunca propone un comando que cree, modifique o borre un recurso de AWS.

## 0.5.1 - 2026-08-04

- **El hook ahora viene incluido en el plugin** (`hooks/hooks.json`), asi que
  se registra solo al instalarlo. Antes habia que pegar un bloque en
  `settings.json` con una ruta absoluta al script — fragil (se rompe si el
  repo cambia de lugar) y facil de saltearse. Usa `${CLAUDE_PLUGIN_ROOT}`,
  que resuelve la ruta del plugin en runtime.
- `intelica-arca-capture` declara `user-invocable: false`. No cambia el
  comportamiento — Claude ya lo podia invocar y el usuario no lo veia en el
  menu `/` — pero deja la intencion explicita en el frontmatter en vez de
  depender de un efecto lateral no documentado.
- Documentado un limite verificado: un hook **no puede invocar un skill**.
  Solo manda el mensaje a Claude por stderr al salir con codigo 2, y Claude
  decide invocarlo. La captura no es deterministica como un cron.

## 0.5.0 - 2026-08-04

Rediseño del lado de curacion en tres momentos, reemplazando el pipeline de
un solo pase.

- **Nuevo `intelica-arca-capture`** (automatico, disparado por el hook
  `PreCompact`): guarda lo relevante de la conversacion en staging local
  antes de que la compactacion lo degrade. La compactacion nativa resume
  para poder seguir trabajando, y en el proceso descarta los identificadores
  exactos y el razonamiento de las decisiones — justo lo que vale
  documentar. Nuevo `hooks/precompact-capture.sh`, que hay que configurar a
  mano en `settings.json` (ver README).
- **`intelica-arca` reescrito**: ahora consolida los fragimentos de la sesion
  y persiste el PR en un solo pase. Si la conversacion nunca se compacto,
  extrae directo de la conversacion viva.
- **Retirados** `intelica-compression`, `intelica-markdown`,
  `intelica-kb-storage` e `intelica-arca-fast`. Todos asumian un solo pase
  sobre la conversacion completa, premisa que el staging local reemplaza.
- **Los documentos curados ahora emiten fragmento de grafo.** Antes
  `intelica-markdown` emitia `entities` como lista plana de strings, que
  `build_graph.py` ignora por no tener tipo — el resultado era que las
  conversaciones llegaban al `INDEX.md` pero no al grafo. Los tipos
  `Decision` e `Incident` del esquema no tenian quien los produjera.
- **El trabajo pesado pasa a Python.** `write_capture.py` (secuencia,
  directorio de sesion, timestamp) y `consolidate.py` (dedup de entidades
  por ID acumulando propiedades, dedup de relaciones, agrupado por cuenta).
  El LLM queda solo con lo que necesita criterio: que extraer, y como
  resolver contradicciones entre fragmentos. Una sesion larga puede dejar
  300+ entidades — deduplicarlas leyendolas todas seria caro e
  inconsistente.
- Revierte a proposito la decision de "contexto en proceso efimero": el
  staging local persiste. El motivo es distinto al original — no es guardar
  borradores a medio hacer, es no perder detalle en la compactacion.

## 0.4.0 - 2026-08-02

- Renombrado a **Intelica ARCA** (Automated Retrieval & Context
  Architecture). Cambia el `name` del plugin (`intelica-brain` →
  `intelica-arca`), asi que hay que **desinstalar y reinstalar** — no
  alcanza con actualizar.
- Los 3 skills invocables se renombran: `/intelica-brain` →
  `/intelica-arca`, `/intelica-brain-fast` → `/intelica-arca-fast`,
  `/intelica-brain-recall` → `/intelica-arca-recall`. Los 3 internos
  (`intelica-compression`, `intelica-markdown`, `intelica-kb-storage`) no
  cambian: nunca se invocan directo y ya tenian nombre neutro.
- **Fix**: los skills mandaban `enviado_por` a `push_knowledge`, un
  parametro que el servidor ya no acepta — habrian fallado en la proxima
  corrida. La autoria ahora la resuelve el servidor desde el token
  personal autenticado, lo que ademas la vuelve verificable en vez de
  autodeclarada por el caller.
- `intelica-arca-recall` reescrito para el grafo de conocimiento: elige
  entre el grafo (`find_entity`/`traverse`/`find_documents`) para
  preguntas sobre un recurso concreto, y los documentos para las
  narrativas. Su `description` ahora cubre preguntas de conectividad e
  inventario, no solo incidentes y decisiones.
- Nuevo `KNOWLEDGE_MODEL.md`: esquema fijo y curado de entidades y
  relaciones que alimentan el grafo.
- Metadata del plugin completada (`displayName`, `keywords`, `category`,
  `homepage`, `repository`, `license`) — es lo que se muestra al
  instalarlo. Los plugins de Claude Code no soportan icono ni imagen.


## 0.3.0 - 2026-07-27

- Added `intelica-arca-recall`: read-only skill that checks
  `INDEX.md`/existing `.md` files in `intelica-brain-ia` (via the new
  `get_file_contents` tool on `intelica-brain-mcp`) before answering,
  instead of answering from scratch. Unlike the other skills, this one
  can trigger on relevant conversation topic, not only explicit
  invocation. Opens at most 2 files per question.
- `intelica-brain-mcp` gained a 5th tool, `get_file_contents(path, ref)`
  — read-only, no path restriction (reads carry no supply-chain risk,
  unlike writes).
- `intelica-brain-ia` gained an auto-generated `INDEX.md`, rebuilt by a
  GitHub Actions workflow on every push to `main` (see that repo).

## 0.2.0 - 2026-07-26

- Added `intelica-arca-fast`: single-pass version with no intermediate
  questions or preview — extracts, drafts, and pushes in one go, without
  invoking the other 3 skills.
- Added `scripts/build_push_args.py` (bundled in `intelica-arca-fast`):
  computes branch name, file paths, and the random suffix
  deterministically instead of having the model reason them out — real
  date, real randomness, no extra tokens spent on it.
- Trimmed all `SKILL.md` instructions ~58% (531 → 225 lines across the 4
  original skills), per Anthropic's Skill authoring best practices
  (concise instructions, progressive disclosure).
- Extracted `intelica-compression`'s 17-field schema into a separate
  `schema.md` reference file — only read when the exact format is
  needed, not on every invocation.
- Made compression output fields optional (omit if not applicable)
  instead of forcing empty `[]` on all 17 fields per topic — cuts output
  tokens on every run.
- Translated all `SKILL.md` instructions and the content the pipeline
  generates (titles, summaries, sections, PR title/body, commit
  messages) to English — measured ~31% fewer tokens for equivalent
  content. Literal identifiers (IDs, ARNs, resource names, `account`
  values) are never translated.
- Added `ARCHITECTURE.md` documenting both pipelines, key design
  decisions, and shared conventions.

## 0.1.0 - 2026-07-25

- First version: `intelica-arca` (orchestrator) plus the 3 decoupled
  pipeline skills — `intelica-compression`, `intelica-markdown`,
  `intelica-kb-storage`.
- Bundled `.mcp.json` registering `intelica-brain-mcp` on install, using
  `${INTELICA_MCP_URL}`/`${INTELICA_MCP_TOKEN}` env var references (never
  a hardcoded token in the repo).
- Pipeline: compress the conversation → draft `.md` files for RAG →
  persist as a single Pull Request in `ddvloayza/intelica-brain-ia` via
  `intelica-brain-mcp`'s `push_knowledge` tool. No merge tool, by design
  — merging always stays a human, manual step in GitHub.
