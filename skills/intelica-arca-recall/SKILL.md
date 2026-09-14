---
name: intelica-arca-recall
description: "Checks Intelica's infrastructure knowledge base (ITL-ORG-INFRA/intelica-brain-ia, via intelica-brain-mcp) before answering from scratch. Covers three domains. AWS: resources and their config (instances, security groups and their rules, VPCs, subnets, RDS, S3, IAM roles, KMS keys), connectivity questions ('can A reach B', 'what opens port X', 'who uses this security group'), the accounts Portal-Prod, Portal-Dev, Interchange-Prod, Interchange-Dev, Analytics-Prod, Analytics-Dev, Intelica-Network or Audit. Databases: engines and instances (SQL Server, Postgres, MySQL, Oracle), which server hosts which database, connectivity to a database, connection strings or drivers. Windows: servers and their roles (domain controllers, file servers, app servers), patch/update cycles, pending reboots, OS versions. Also past incidents, architecture decisions, or 'did we handle this before' in any of the three. Two paths: the knowledge graph (find_entity/traverse/find_documents) for questions about a specific resource, and a domain's INDEX.md plus get_file_contents for narrative ones. Unlike the other skills here, this one CAN trigger on relevant conversation topic, not only on explicit invocation (also invokable with '/intelica-arca-recall'). If nothing relevant is found, say so and answer normally — never fabricate a source."
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
  is rds-portal-prd").
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

## Step A — Graph

1. `find_entity(name=<what the user named>)` — accepts an exact ID
   (`i-0abc`, `sg-0xyz`, `Portal-Prod`, `sqlprd-01`, `WSRV-DC-01`) or part
   of a name (`denver`). Narrow with `entity_type` when the question
   implies one — AWS: `ec2_instance`, `security_group`, `vpc`,
   `rds_instance`, `iam_role`; database: `DatabaseServer`, `Database`;
   windows: `WindowsServer`, `PatchReview`.
2. `traverse(entity_id=<the id>, relationship_type=<optional>)` — mind
   the direction, they answer different questions:
   - **outgoing** `HAS_SECURITY_GROUP` from an instance → its SGs.
   - **incoming** `HAS_SECURITY_GROUP` into an SG → who uses it.
   - **outgoing** `RUNS_ON` from a `DatabaseServer` → the EC2 or
     `WindowsServer` it runs on — this is the hop that crosses from
     `database` into `aws`/`windows`.
   - **outgoing** `HOSTS_DATABASE` from a `DatabaseServer` → the
     `Database`s it hosts.
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
`security.md`. `database` and `windows` don't have an equivalent generated
inventory yet — everything there is narrative, via the index.

## Answer, citing the source

Say which document the answer came from, so the user can open it for the
full context. If the sources didn't actually cover the question, say so
rather than stretching them.

## Rules

- Read-only: never `create_branch`, `create_or_update_file`,
  `create_pull_request`, or `push_knowledge` from this skill.
- At most 2 documents per question — that's the token budget this whole
  design is built around. Graph calls are cheap and don't count.
- Never invent a citation. Empty result → say so plainly.
