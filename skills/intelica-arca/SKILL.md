---
name: intelica-arca
description: "Closes out a conversation: consolidates everything intelica-arca-capture staged locally during it, drafts the final .md documents plus their graph fragments, and pushes them as a single Pull Request to ITL-ORG-INFRA/intelica-brain-ia via intelica-brain-mcp — all in one pass. Invoke with '/intelica-arca' (add '--full' to review the drafts before pushing). Works whether the conversation was long (several capture fragments) or short (none — it extracts from the live conversation instead). Covers three knowledge domains — aws, database, windows — and classifies which one each document belongs to before drafting. Does NOT activate on conversation topic, only on explicit invocation. Never merges the PR: that stays a human step in GitHub."
---

# Intelica ARCA

Turns a finished conversation into documented knowledge, in one pass:
consolidate → draft → push. Only output is the PR link, unless `--full`.

Never merges. The PR is the human gate, and there is no merge tool by
design.

## Step 1 — Consolidate the staged fragments

Get the `session_id` for this conversation, then:

```bash
python3 scripts/consolidate.py --session <session_id>
```

The script deduplicates entities by ID (merging their properties),
deduplicates relations, and returns every fact tagged with the fragment it
came from. Don't do that merging by hand — a long session can stage 300+
entities and the script does it exactly, for free.

**`fragment_count: 0`** means the conversation never compacted, so nothing
was staged. That's normal for a short chat: extract directly from the
conversation you're in, using the same shape the script would have
returned, and continue.

## Step 2 — Resolve what the script can't

This is the part that needs judgment, and it's why the facts come with
sequence numbers.

**Contradictions.** A higher sequence came later in the conversation. A
fact marked `DISCARDED:` overrides what it discards — the final document
must reflect the conclusion, not the abandoned hypothesis. Don't document
both as if they were equally true.

**Grouping.** One `.md` per coherent topic. Several unrelated topics in one
conversation → several files. Don't split a single topic across files, and
don't merge two unrelated ones to save effort.

**Relevance.** `seen_in` tells you whether an entity showed up once in
passing or recurred across the conversation. Recurring ones are usually the
subject; one-offs are usually context.

## Step 2.5 — Classify each topic's domain

The knowledge base is partitioned into three domains: `aws`, `database`,
`windows`. Every document needs exactly one before it can be drafted —
it decides which `inbox/<domain>/...` folder it lands in.

- One topic, one clear domain → tag it and move on.
- A conversation that mixes domains (e.g. an AWS EC2 discussion that
  turns into a SQL Server tuning discussion) → split into one document
  per domain, per the grouping rule in Step 2. Don't force a mixed topic
  into a single domain just to avoid a second file.
- Genuinely ambiguous → ask the user once, before drafting, with the
  three domains as the options. Don't guess and don't draft first and
  reclassify later.

## Step 3 — Draft the documents

Write the prose in **Spanish**. A human reviews and merges this document,
that merge is the only gate in the whole system, and the team reads
Spanish — don't add friction to the step that most needs care. Writing it
in English was measured to save only 9.6% of tokens on a real document
from the repo, because these files are dense in identifiers that tokenize
the same either way.

Never translate literal identifiers (IDs, ARNs, resource names, `account`
values): those are exact retrieval keys.

**Don't write any YAML.** Step 4's script generates both files — the
frontmatter, the graph fragment, and the cross-reference between them.
Your job here is the content: the prose, and the structured values below.

`summary` and `tags` are what the whole document lookup path runs on, so
they're worth real attention — they land in `INDEX.md`, and that index is
all anyone has when deciding whether to open this file. There is no
semantic search here: a document nobody can find from its summary is a
document that doesn't exist.

- **`summary`** — what question this document answers, in the words
  someone would use six months from now. Not "analysis of Denver Prd" but
  "why Denver Prd peaks at 20:00 and why the backup jobs turned out not to
  explain it". One line, no line breaks (it goes in a table cell).
- **`tags`** — include the **alternate ways people would phrase it**, not
  just the literal terms in the document. A document about `CPU` peaks
  should also carry `rendimiento`, `saturacion`, `lentitud` if that's how
  someone might ask. This is the one place where a human can encode the
  team's own vocabulary, which no retrieval mechanism can infer on its own.

- **`body`** — what the situation was, what was found, what was decided,
  and what remains open. Markdown, no frontmatter. Write what someone
  would need six months from now, not a transcript.
- **`entities` / `relations`** — the consolidated ones, minus anything
  belonging to a different topic's file. `seen_in` gets dropped
  automatically — leave it in if it's there.

  Entity types, and their required fields beyond `id`:
  `Account` · `Resource` (needs `resource_type`) · `Finding` (needs
  `finding_type`) · `Decision` (needs `title`) · `Incident` · `Project` ·
  `DatabaseServer` (needs `engine`) · `Database` · `WindowsServer` ·
  `PatchReview` (needs `date`).
  There is no `Person` type — who did or said something is not modelled,
  by design. `Document` and `DOCUMENTED_IN` are derived, never declared.

  Relations: `BELONGS_TO` · `HAS_SECURITY_GROUP` · `IN_VPC` · `IN_SUBNET` ·
  `ASSUMES_ROLE` · `ENCRYPTED_BY` · `ATTACHED_TO` · `REGISTERED_ON` ·
  `AFFECTS` · `MITIGATED_BY` · `RELATED_TO` · `HOSTS_DATABASE` ·
  `RUNS_ON` (a `DatabaseServer` on a `Resource` or `WindowsServer` — this
  is what connects the `database` domain to `aws` or `windows`) ·
  `REVIEWED_IN` · `SAME_AS` (a `WindowsServer` that is also an EC2
  `Resource` — the two entities stay separate, linked by this relation).

  **On `Incident`, `date` is when the incident STARTED** — not when it was
  detected, not when you're writing this. Those can be weeks apart, and
  the index sorts and answers "when did this happen" from this field, so
  confusing them makes a correct answer cite a wrong date. It already
  happened once: an EKS pod-IP exhaustion incident was recorded as
  `2026-08-04`, the day someone reported it, while the document itself
  said the oldest pod had been failing since `2026-07-31` with nothing
  alerting — four days of silence that were part of the finding, lost
  from the graph. If the start is unknown, use the earliest date the
  evidence supports and say in the prose that it's approximate.

## Step 4 — Generate and push

One script validates the drafts, writes both files per topic, and computes
the deterministic parts (real date, slugs, branch name, paths):

```bash
python3 scripts/build_push_args.py <<'EOF'
[{
  "title": "...", "domain": "aws", "account": "...", "category_raw": "...",
  "summary": "...", "tags": ["..."], "body": "<markdown prose>",
  "entities": [{"type": "Resource", "id": "i-0abc", "resource_type": "ec2_instance"}],
  "relations": [{"from": "i-0abc", "type": "BELONGS_TO", "to": "Portal-Prod"}],
  "commit_message": "docs: ..."
}]
EOF
```

`domain` is required (`aws`, `database`, or `windows` — from Step 2.5) and
decides the folder: `inbox/aws/<account>/...` keeps the existing
per-account layout, `inbox/database/...` and `inbox/windows/...` are flat
unless the topic also carries an `account`. `account` itself stays
required only for `domain: aws`.

**If it exits non-zero, nothing was generated.** It prints one line per
problem: an entity type that isn't in the model, a missing
`resource_type`, an IP used as an ID, a relation type that doesn't exist.
Fix the draft and run it again — don't work around it by assembling the
files yourself, and don't push anything. That check is the only thing in
the entire chain that catches an invented type: CI won't, and a bad node
that reaches `graph.json` is simply unreachable by every later query.

Warnings (`AVISO`) don't block. A relation pointing at an entity declared
in another document is normal and expected.

Then call `push_knowledge` with `base_branch: "main"` and the script's
`new_branch_name` / `files`, unchanged.

Don't pass a sender. The server derives it from the authenticated personal
token — it isn't a parameter. Never ask the user for an email or any other
personal data.

With `--full`: show the drafted files and wait for confirmation before
pushing. Without it: push silently and report only the PR link.

If `intelica-brain-mcp` isn't loaded: write the files locally, say so, and
don't block.

## Rules

- Never merges the PR, in any mode.
- The staged fragments are **never deleted** — if the PR comes out wrong or
  you want to re-curate differently, the raw material is still there.
- The staging fragments (`~/.intelica-arca/sessions/<id>/NNN.json`) never
  go to GitHub — staging is working material, not knowledge. The
  `.graph.yaml` files the script generates are a different thing entirely
  and do get pushed, alongside their `.md`.
- Never hand-assemble the files or bypass the script when it reports an
  error. An invalid type reaches `graph.json` silently and nothing
  downstream will catch it.
- Doesn't accept credentials pasted in chat for any action.
- Only activates on explicit `/intelica-arca` invocation.
