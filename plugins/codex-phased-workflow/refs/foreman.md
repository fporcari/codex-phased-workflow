# Foreman protocol

The foreman is the chat that holds the user's decisions and supervises the
workflow. Worker sessions own one phase; the foreman owns scope, sequencing,
re-phasing, plan defects, and the final user-facing account.

This file defines a portable file-backed protocol. Cross-chat messaging is an
optional acceleration, never the source of truth.

## The foreman

Every active plan directory may contain `foreman.json`:

```json
{
  "workflow": "<slug>",
  "title": "wf:<slug>:foreman",
  "host": "claude|codex|unknown",
  "claimed_at": "<ISO timestamp>"
}
```

The chat creating or importing the plan writes it with its own host. A later
chat taking command updates `host` and `claimed_at` in a dedicated
`wf: take command of <slug>` commit after user approval. Never use an opaque
session id as durable state: ids do not cross products or machines.

Workers do not need to edit `foreman.json`. Their durable message is the phase
marker and its notes in `plan.md`, plus `notes.md` and logs when applicable.

## Channel floors

Use the best available channel in this order:

1. a live Codex subagent or task messaging tool when the worker and foreman are
   in the same runtime tree;
2. a product-native session message when the target is explicitly discoverable;
3. the committed `.phased/` state and `EVENT:` log lines.

Do not retry a missing cross-session tool, guess a target, or treat a failed
message as a failed phase. State the degradation once. File-backed state is the
interoperable floor and is always authoritative.

## Worker messages

When a live channel exists, send one compact event after the durable state has
been written:

- `phase-started: N — <title>`
- `phase-done: N — <title> — <Done evidence>`
- `phase-failed: N — <Issue note>`
- `phase-blocked: N — <Blocked note>`
- `repair-done: N — <Repaired note>`
- `quality-check: <finding count and stamp>`

Messages never replace plan edits or commits. If the message and plan disagree,
the plan wins.

## Plan-defect claims

A worker may discover that an immutable planning premise is false: a contract
test cannot pass as authored, a settled decision is unavailable, or `Done:`
requires an impossible state. The worker records:

```text
> Issue: plan-defect claim — <specific false premise and evidence>
> Attempted: <what established that this is the plan, not the implementation>
```

It does not rewrite the plan's intent. The foreman chooses one of two outcomes:

- `plan-defect: repair` — amend the plan in its own `wf:` commit, then authorize
  a fresh repair;
- `plan-defect: stop` — keep the failure visible and stop the run.

An unattended launcher may hold briefly for that decision. If no live return
channel exists, it must stop or follow its documented timeout rule; it never
silently invents a new requirement.

## Notes ledger

`notes.md` holds reasoning that needs to outlive a chat but does not belong in a
phase status line. Use one section per phase:

```markdown
## Phase N

- <decision, constraint, or later follow-up>
```

Do not store generic personal knowledge here. Durable cross-project lessons go
to the user's configured knowledge base after approval.

## The reporting register

Reports are written for someone who understands the intended feature but did
not watch the implementation:

- lead with outcome and current state;
- name observable behavior, not tool activity;
- distinguish verified facts, inferences, and unverified assumptions;
- cite the phase, commit, file, test, or issue that supports a claim;
- keep mechanical details in logs unless they change a decision;
- never claim searched, tested, or verified unless it happened in that session.

For a major report or close-out, a fresh read-only `report-judge` subagent may
probe whether the draft answers: what changed, what remains, what was verified,
and what the user must decide. It returns comprehension gaps only. Revise once;
do not start an editorial loop.

## Notifications

Notifications are best-effort and sparse. Notify only when the user can act:

- first phase failure in an autonomous run;
- any blocked phase;
- any plan-defect decision request;
- the final run outcome.

Routine progress belongs in the plan and log, not a push. A notification failure
never changes workflow state.

## Workflow lessons

At finalization, scan the plan and notes for a non-obvious reusable lesson.
Follow the user's global knowledge-base rules and ask before publishing a new
entry. Correct an existing entry instead of adding a near-duplicate. The
workflow archive is evidence, not a substitute for the shared knowledge base.
