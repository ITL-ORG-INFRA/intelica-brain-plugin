---
name: intelica-arca-capture
description: "Extracts what matters from a stretch of conversation into a staging fragment: facts, decisions and typed entities with exact identifiers — AWS resources, database servers and instances, Windows servers and patch reviews — because compaction summarizes for continuity and drops precisely those identifiers. Used by the subagents /intelica-arca launches over the tramo-NNN.md stretches the PreCompact hook saved — NOT invoked by the user, and never activates on conversation topic. Covers all three knowledge domains: aws, database, windows. Writes to the session's folder under ~/.intelica-arca/sessions/ via scripts/write_capture.py. Staging only: nothing reaches GitHub here — that is intelica-arca's job at the end of the chat."
user-invocable: false
---

# Intelica ARCA Capture

Turns a stretch of conversation into a staging fragment. The user doesn't
invoke it.

Why it exists: compaction produces a summary optimized for Claude to keep
working, not for documentation. It keeps the goal and current state but
drops exact identifiers, edge cases and the reasoning behind decisions —
which is exactly the material worth documenting. So the `PreCompact` hook
copies the stretch about to be summarized to
`~/.intelica-arca/sessions/<session_id>/tramo-NNN.md`, without stopping
the compaction, and `/intelica-arca` extracts each one at the end of the
chat with this method.

The hook used to stop the compaction (exit 2) and ask Claude to run this
skill. That message reaches the user, not Claude, so it never ran, and the
compaction went through on the retry. That's why the hook now saves the
stretch itself: copying needs no judgment, extracting does, and at the end
of the chat there is room for it.

## Extracting a saved tramo

The mandate gives you the tramo's path, the session id and the tramo
number. The tramo is a plain transcript: `[usuario]`, `[claude]`,
`[tool <name>]` with its input and `[resultado]` with its output, both
truncated. Read it in full before writing — a fact near the end often
corrects one near the start.

Write with `--tramo <n>`: the fragment takes the tramo's number, so the
facts keep the conversation's order even though the tramos are extracted
in parallel. **Always write a fragment for a tramo**, even if it's only a
`summary` saying it had nothing to document: the fragment is what marks
the tramo as done, and without it `/intelica-arca` keeps relaunching it.

## What to extract

Only what would be worth reading in six months. Not the whole
conversation.

- **`summary`** — one or two sentences: what this stretch of the
  conversation was about.
- **`facts`** — the concrete findings. Include corrections explicitly: if
  something asserted earlier turned out to be wrong, write it as
  `"DISCARDED: <claim> — <why>"`. That's what lets the consolidation know
  what didn't survive.
- **`entities`** — typed, per the vocabulary below. This is the part that
  matters most and the part that's lost if deferred.
- **`relations`** — how those entities connect.
- **`accounts`** — the AWS accounts involved.
- **`open_questions`** — what was left unresolved.
- **`catalogo`** — what was learned that *describes* a database object:
  what a table is for, what a column means, which column or index to filter
  by, which proc writes it, what it joins with, a gotcha that cost time. One
  item per object: `{"objeto": "ASSOCINV.dbo.FEE_FRAC_N", "perfil":
  "denver", "tipo": "tabla", "hechos": ["..."]}`. `objeto` is
  `<BASE>.<schema>.<name>` as the engine writes it (`MSTRAFB*` for the
  per-client template); `tipo` is `tabla`, `vista`, `proc`, `funcion`, or
  `base` with `objeto` set to the database name. It ends up in that object's
  card in `database/catalogo/`, which is what gets read before the next
  query. Corrections go in as `"DISCARDED: <claim> — <why>"`, like facts.
  **Never rows**: no values from a query result, no amounts, no client data
  — a card describes the table, not its contents. And nothing the database
  already says on its own (the full column list, types, indexes): only what
  someone had to work out.
- **`reports`** — HTML reports generated so far with the Intelica template
  (saved under `salidas/<date>/`): `{"path": "<absolute path>", "about":
  "<one line: what it shows>"}`. The absolute path, exactly as written to
  disk. After compaction this is the only place the path survives, and
  `/intelica-arca` uploads each report from it at the end of the chat.

Skip greetings, tool output that led nowhere and repeated content. Don't
worry about overlap with other tramos: the consolidation deduplicates
entities and relations, and resolves facts by order.

## Entities: use the real IDs

Use the exact identifier, never a description. `i-0abc123`, not "the
Denver instance". `sg-04aac9e78d6520b80`, not "the SQL security group".

This is the whole point: those IDs already exist in the knowledge graph
from the AWS inventory (or from an earlier database/Windows document).
Matching them exactly means this conversation attaches to the **same
node** instead of creating an island. A paraphrase creates a duplicate
that nothing can join.

Types available: `Account`, `Resource` (with `resource_type`), `Finding`,
`Decision`, `Incident`, `Project`, `DatabaseServer` (with `engine`),
`Database`, `DatabaseObject` (with `object_type`: `table`, `view`,
`procedure`, `function`; id `<BASE>.<schema>.<name>`), `WindowsServer`,
`PatchReview`. There is no `Person` type — don't model who did or said
something.

On an `Incident`, `date` is when it **started**, not when it was noticed.
If the conversation says something had been failing since a date before
anyone reported it, that earlier date is the one to capture — the gap
between the two is usually part of what matters.

## Write the fragment

```bash
python3 scripts/write_capture.py --session <session_id> --tramo <n> <<'EOF'
{
  "summary": "...",
  "accounts": ["Portal-Prod"],
  "facts": ["...", "DISCARDED: ... — ..."],
  "entities": [
    {"type": "Resource", "id": "i-0abc123", "resource_type": "ec2_instance", "region": "eu-south-2"},
    {"type": "Decision", "id": "some-kebab-slug", "title": "..."}
  ],
  "relations": [
    {"from": "i-0abc123", "type": "BELONGS_TO", "to": "Portal-Prod"}
  ],
  "open_questions": ["..."],
  "catalogo": [
    {"objeto": "ASSOCINV.dbo.FEE_FRAC_N", "perfil": "denver", "tipo": "tabla",
     "hechos": ["FEE_PROD_AMT is the allocated amount; FEE_TOTAL_AMT repeats the whole invoice on every row"]}
  ],
  "reports": [
    {"path": "/Users/.../salidas/2026-10-02/plan-continuidad-caida-eu-south-2.html", "about": "..."}
  ]
}
EOF
```

The script handles the deterministic parts — which session directory, the
sequence number, the timestamp. Don't compute those.

## Rules

- **Never** writes to GitHub, never opens a PR, never calls the MCP. This
  is staging only.
- Never asks the user anything — it runs inside a subagent, and nobody is
  there to answer.
- Only output: the script's line confirming the fragment was written.
- A tramo with nothing worth documenting still gets a fragment with just
  its `summary` (see above). A generated report always goes in `reports`.
