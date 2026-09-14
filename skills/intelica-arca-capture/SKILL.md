---
name: intelica-arca-capture
description: "Captures what matters from the conversation so far into local staging, right before Claude Code compacts the context. Triggered by the PreCompact hook — NOT invoked by the user, and never activates on conversation topic. Extracts facts, decisions and typed entities (with exact identifiers — AWS resources, database servers and instances, Windows servers and patch reviews) while the full detail is still in context, because compaction summarizes for continuity and drops precisely those identifiers. Covers all three knowledge domains: aws, database, windows. Writes to ~/.intelica-arca/sessions/<session_id>/ via scripts/write_capture.py. Staging only: nothing reaches GitHub here — that is intelica-arca's job at the end of the chat."
user-invocable: false
---

# Intelica ARCA Capture

Saves the conversation's substance to local staging **before** compaction
degrades it. Runs automatically, triggered by the `PreCompact` hook — the
user doesn't invoke it.

Why the timing matters: compaction produces a summary optimized for Claude
to keep working, not for documentation. It keeps the goal and current state
but drops exact identifiers, edge cases and the reasoning behind decisions
— which is exactly the material worth documenting. This runs while all of
that is still in context.

## Input from the hook

The hook passes the `session_id`. It's required — without it the fragment
can't be filed under the right conversation. If it isn't in the hook
message, say so and skip; don't guess one.

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

Skip greetings, tool output that led nowhere, repeated content, and
anything already captured in an earlier fragment of this same session.

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
`Database`, `WindowsServer`, `PatchReview`. There is no `Person` type —
don't model who did or said something.

On an `Incident`, `date` is when it **started**, not when it was noticed.
If the conversation says something had been failing since a date before
anyone reported it, that earlier date is the one to capture — the gap
between the two is usually part of what matters.

## Write the fragment

```bash
python3 scripts/write_capture.py --session <session_id> <<'EOF'
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
  "open_questions": ["..."]
}
EOF
```

The script handles the deterministic parts — which session directory, the
sequence number, the timestamp. Don't compute those.

## Rules

- **Never** writes to GitHub, never opens a PR, never calls the MCP. This
  is staging only.
- Never asks the user anything — compaction is about to happen and there's
  no room for a round trip.
- Only output: one line confirming the fragment was written. Keep it
  short; the user didn't ask for this, it fired on its own.
- If the extraction has nothing worth saving (a short exchange with no
  findings), say so and write nothing. An empty fragment is noise.
