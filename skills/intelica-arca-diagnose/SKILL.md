---
name: intelica-arca-diagnose
description: "Guides live troubleshooting of an active AWS problem — connectivity between two resources, permission denials, timeouts, unexpected access. Checks the knowledge graph first (find_entity/traverse/find_documents) to see if the answer is already known; if not, proposes the specific read-only AWS CLI command that would answer it, explains what it returns, and waits — never runs it. Parses whatever output gets pasted back and continues from there, chaining more proposed commands if needed. Never proposes a mutating command. Does not persist anything itself: whatever gets found here is picked up naturally by intelica-arca-capture like any other conversation. Triggers on describing a live problem to diagnose, not on informational lookups (that's intelica-arca-recall's job)."
---

# Intelica ARCA Diagnose

Helps troubleshoot something that's actually broken right now, by proposing
the exact command to run next — never running it yourself.

## When to use

The user describes an active problem, not a lookup: "can't connect from X to
Y", "getting access denied", "this times out", "why is this exposed". If
it's more "what do we already know about X" than "help me figure out why X
is broken", that's `intelica-arca-recall`'s job instead.

## Step 1 — Check what's already known

Before proposing anything, look at the graph: `find_entity` on the
resources involved, `traverse` their relevant relationships. Often the
answer is already there — a security group's rules, what VPC something is
in, what role it assumes.

The knowledge base is partitioned by domain (`aws`, `database`,
`windows`), so start from the domain the problem is actually in — a
`DatabaseServer` or a `WindowsServer` involved in the problem means
checking `database`/`windows` knowledge too, not just AWS. This doesn't
change what this skill does: it's still AWS-CLI-first troubleshooting: a
`RUNS_ON` hop from a `DatabaseServer` to its underlying `Resource` or
`WindowsServer` is often what tells you which AWS command actually
applies.

If that fully answers it, answer directly and stop. Don't propose a command
for something you can already see in the graph.

## Step 2 — Recognize the problem type and propose a command

If the graph doesn't have enough, pick the closest pattern below, or improvise
one in the same spirit for a problem type that isn't listed. Always:

- Propose **one command at a time** — read-only only (`describe-*`,
  `get-*`, `list-*`, `simulate-*`). **Never** a command that creates,
  modifies, or deletes anything.
- Say what it returns and why that answers the question, in plain terms.
- Wait for the output to be pasted back. Don't assume the result.

**Connectivity between two resources** (A can't reach B):

```bash
aws ec2 describe-instances --instance-ids <id> \
  --query 'Reservations[].Instances[].[InstanceId,VpcId,SubnetId,SecurityGroups]'
```
Gives the VPC, subnet and security groups on each side — usually enough to
see if they're even in a position to talk. Follow with:

```bash
aws ec2 describe-security-groups --group-ids <sg-id>
```
The actual rules: protocol, ports, and what's allowed in/out. If both sides
check out and it still doesn't connect, the next places to check are route
tables (`describe-route-tables`) and NACLs (`describe-network-acls`) — a
security group can be wide open and a route table can still be why nothing
gets there.

**Permission denied**:

```bash
aws sts get-caller-identity
```
Confirms which identity is actually being used — half of these turn out to
be the wrong role or an assumed-role mismatch, not a missing permission.

```bash
aws iam simulate-principal-policy --policy-source-arn <role-arn> --action-names <action>
```
Tells you directly whether that identity's policies allow the action, which
is more reliable than reading policy JSON by eye.

**Something unexpectedly public** (bucket, RDS, security group open to
0.0.0.0/0): the relevant describe call for that resource type, same pattern
— propose it, explain what to look for in the output.

## Step 3 — Parse the output, keep going if needed

Read what got pasted, answer what it clarifies, and if that opens a new
question, go back to Step 2 with the next command. Don't try to guess two
steps ahead — one command, one answer, then decide the next one.

## Referencing what you find

Use the real IDs as they appear in the output — `i-0abc123`, `sg-0xyz`, not
a description. These match the same IDs already in the knowledge graph from
the AWS inventory, which is what lets this conversation's findings attach to
the same nodes later instead of creating duplicates.

## Rules

- Never runs a command — only proposes it and waits.
- Never proposes anything that creates, modifies, or deletes an AWS
  resource. If the actual fix requires a mutating command, propose that
  too, but say plainly that it's a change, not a diagnostic — same as any
  other change the user runs themselves and decides on.
- Doesn't persist anything, ever. No `push_knowledge`, no PR. Whatever gets
  found here becomes knowledge the normal way, through
  `intelica-arca-capture` and `/intelica-arca`, same as any other
  conversation.
- If the graph already answers the question, don't propose a command just
  to be thorough.
