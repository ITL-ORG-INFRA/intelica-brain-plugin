---
name: intelica-arca-recall
description: "Checks Intelica's infrastructure knowledge base (intelica-brain-ia, via intelica-brain-mcp) before answering from scratch. AWS: resources and their config (instances, security groups and rules, VPCs, subnets, RDS, S3, IAM roles, KMS keys), connectivity ('can A reach B', 'what opens port X', 'who uses this SG'), the Portal, Interchange, Analytics, Intelica-Network and Audit accounts. Databases: engines and servers, which database lives where, connectivity, and the catalog of tables, columns and procs (what a table is for, how to filter it). Windows: servers and their roles (domain controllers, file and app servers), patch cycles, pending reboots, OS versions. Also past incidents, architecture decisions, or 'did we handle this before'. The graph (find_entity/traverse/find_documents) for a specific resource; a domain's INDEX.md plus get_file_contents for narrative ones. It triggers on topic, not only via '/intelica-arca-recall'. If nothing is found, say so and answer normally — never fabricate a source."
---

# Intelica ARCA Recall

Checks the knowledge base before answering, instead of answering from
scratch. Read-only — never writes, never opens a PR.

## When to use

The question plausibly relates to Intelica's infrastructure or its
history, in any of the three domains this covers:

- **aws** — a specific resource, an account, connectivity between two
  things ("what security groups does denver-02 have", "is this bucket
  public", "what's in Portal-Prod's VPC").
- **database** — a database engine or instance, connectivity to a
  database, which server hosts which database ("what SQL Server hosts
  portal_core", "can the app reach the Postgres instance", "what version
  is rds-portal-prd"). And what's **inside** a database: what a table,
  view or proc is for, what a column means, how to filter a big table, who
  writes it — that's the catalog, see "Database objects" below.
- **windows** — a Windows server, its role, patch/update state ("what's
  the role of WSRV-DC-01", "when was the last patch review", "is there a
  pending reboot on the file server").

Plus, in any domain: an incident, an architecture decision, or "did we
already deal with this?". Skip it for generic questions unrelated to
Intelica.

## Pick a domain, then a path

Figure out the domain first — `aws`, `database`, or `windows` — from what
the question names. It's what tells Step B which `INDEX.md` to open. Not
obvious? Fall back to the root `INDEX.md` (see Step B).

Then two ways in. Choose by the shape of the question — don't run both.

**Graph path** — the question is about a *specific resource* or how
resources relate: "what security groups does X have", "what opens port
3389 on Y", "who uses this SG", "what's in this VPC", "which RDS are
publicly accessible". Go to Step A.

**Document path** — the question is *narrative*: "why did we decide X",
"what happened with that incident", "how did we solve this before". Go
to Step B.

Unsure, or the graph came back empty? Fall back to the document path.

## Database objects: the catalog first

A question about a table, view, procedure or column — or any question
that's about to be answered by querying a database with a `db_*` tool —
goes to the catalog before anything else. It holds what the database can't
say on its own: what the object is for, which column to filter by and why,
who writes it, what it joins with, what already cost time.

1. `get_file_contents(path="database/catalogo/INDEX.md")` — one row per
   object, grouped by profile (`denver`...) and database: what it's for and
   what to filter by. Read it whole; it's built to fit.
2. Open the card(s) that match, **at most 2**, with the path the index
   links (`database/catalogo/<perfil>/<BASE>/<OBJETO>.md`). A per-client
   database (`MSTRAFBXGRPEU`, `MSTRAFBNEDBZA`...) is documented once, under
   `MSTRAFB/`.
3. Answer from the card, citing its path. If the question needs live data,
   the card is what makes the first query right: the column that means
   what's being asked, the filter the guard requires, the index it uses.

The card is not live: `filas_aprox` has its `medido_en` date, and the
structure can change. When the live database disagrees with the card,
that's a finding — say so with both versions. No card for the object →
say the catalog doesn't cover it yet and fall back to the database index
below (and to `describir` live, if a `db_*` tool is connected).

## Step A — Graph

1. `find_entity(name=<what the user named>)` — accepts an exact ID
   (`i-0abc`, `sg-0xyz`, `Portal-Prod`, `sqlprd-01`, `WSRV-DC-01`) or part
   of a name (`denver`). Narrow with `entity_type` when the question
   implies one — AWS: `ec2_instance`, `security_group`, `vpc`,
   `rds_instance`, `iam_role`; database: `DatabaseServer`, `Database`,
   `DatabaseObject`; windows: `WindowsServer`, `PatchReview`.
2. `traverse(entity_id=<the id>, relationship_type=<optional>)` — mind
   the direction, they answer different questions:
   - **outgoing** `HAS_SECURITY_GROUP` from an instance → its SGs.
   - **incoming** `HAS_SECURITY_GROUP` into an SG → who uses it.
   - **outgoing** `RUNS_ON` from a `DatabaseServer` → the EC2 or
     `WindowsServer` it runs on — this is the hop that crosses from
     `database` into `aws`/`windows`.
   - **outgoing** `HOSTS_DATABASE` from a `DatabaseServer` → the
     `Database`s it hosts.
   - **incoming** `IN_DATABASE` into a `Database` → its catalogued
     objects. **Incoming** `WRITES` into a table → the procs that load it;
     outgoing from a proc → what it writes. `REFERENCES` → how two objects
     join.
   - **outgoing** `SAME_AS` from a `WindowsServer` → the matching AWS
     `Resource`, when the server is also an EC2 instance.
   - Others: `IN_VPC`, `IN_SUBNET`, `BELONGS_TO`, `ENCRYPTED_BY`,
     `ATTACHED_TO`, `REGISTERED_ON`, `ASSUMES_ROLE`, `REVIEWED_IN`.
   - Several hops → chain calls, feeding each result into the next.
3. The graph holds structured facts, not prose. For the actual **rules**
   of a security group, or any narrative detail, get the source with
   `find_documents(entity_id=...)` and read it with `get_file_contents`.

## Step B — Documents

1. `get_file_contents(path="<domain>/INDEX.md")` — go straight to the
   domain's own index (`aws/INDEX.md`, `database/INDEX.md`,
   `windows/INDEX.md`) once you know it. Domain not obvious from the
   question? Start from the root `INDEX.md` instead — it's a short router
   that links to the three, use it to figure out which one applies. If
   the fetch fails (MCP not loaded, or nothing merged yet), say so
   briefly and answer normally — don't block.
2. Go to the **Conversaciones** section — that's where narrative
   knowledge lives. Match against the **summary and tags**, not just the
   title: tags deliberately carry alternate phrasings, so a question
   about "rendimiento" may well be answered by a document titled around
   "picos de CPU". Pick **at most 2**.
3. `get_file_contents(path=<candidate>)` for each pick.

Nothing plausible → say the knowledge base doesn't cover this yet and
answer from your own knowledge. Don't force a match. Retrieval here is
lexical, not semantic: if the summary and tags don't line up with the
question, assume it isn't there rather than stretching a weak match.

For AWS inventory, the per-account documents are predictable, so you can
go straight to one without the index: `aws/aws-inventory/<Account>/`
holds `overview.md`, `compute.md` (instances plus the full catalog of
security group rules), `network.md`, `data.md`, `workloads.md`,
`security.md`. `database` has the catalog instead (see "Database objects"
above); `windows` has only the narrative, via the index.

## Answer, citing the source

Say which document the answer came from, so the user can open it for the
full context. If the sources didn't actually cover the question, say so
rather than stretching them.

A document whose frontmatter has `reporte: reportes/...html` has an HTML
report in S3 — the visual version made with the Intelica template. Mention
it in one line. Only when the user wants to see it, call
`get_report_url(path=<that value>)` and give them the link (it expires in
an hour). Never fetch the HTML to answer: the `.md` already has the
content, and the report costs ten times the tokens for the same facts.

## Rules

- Read-only: never `create_branch`, `create_or_update_file`,
  `create_pull_request`, `push_knowledge`, or `upload_report` from this
  skill.
- At most 2 documents per question — that's the token budget this whole
  design is built around. Graph calls are cheap and don't count, and
  neither do the indexes (`INDEX.md`, `database/catalogo/INDEX.md`).
- Never invent a citation. Empty result → say so plainly.
