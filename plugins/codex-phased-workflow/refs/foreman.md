# Foreman protocol

On `Channel: relayed`, the foreman is the task that holds the user's decisions
and supervises the workflow. Worker tasks own one phase; the foreman owns scope,
sequencing, re-phasing, plan defects, and the final user-facing account. On
`Channel: in-chat` the role is co-located with execution and this file is not a
relay to create or load.

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

The foreman commands; it does not execute phases. Two exceptions are intended:
launching `/run-workflow`, which supervises external workers, and QA fixes
with their final touch after every phase is `[x]` (`/quality-check` → *QA
fixes*, *The final touch*). The user's check and review findings are corrected
here when no decision is open. With the human at the gate and no phase left to
command, a phase per finding starts a loop rather than buying isolation.

The foreman's model is a written hint like a phase's `Run:` line. For Codex,
suggest `gpt-5.6-sol` for coordination or `gpt-6-astra` for material replanning, with high reasoning: its work is judgment, user-facing
prose, consults, QA fixes, and the final touch. Nothing enforces the hint.

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

It does not rewrite the plan's intent. When the claim includes the exact
contract edit as before-text → after-text, the foreman chooses one of three
outcomes:

- `plan-defect: repair` — authorize a fresh repair with independent eyes;
- `plan-defect: apply` — apply exactly the declared edit to both contract
  copies, re-run the phase's `Done:`, and report the result;
- `plan-defect: stop` — keep the failure visible and stop the run.

The apply road is deliberately narrow. While the launcher holds the workspace,
the supervising run applies the declared before→after edit to the plan copy and
the in-tree copy, keeping them byte-identical. Green `Done:` flips the phase to
`[x]`, retains the `> Issue:` for the record, adds
`> Applied: plan-defect edit — <one line>`, and commits
`wf: plan defect phase N — applied — <one line>`. Red, a missing exact edit, a
rewrite that grows beyond the declaration, or the apply deadline expiring
restores the touched files, records a red outcome, and proceeds to fresh repair.

The unattended launcher holds for the decision with no default deadline. The
foreman first checks the claim against the code it names and puts one question
to the user with claim, evidence, and its own verdict. No reply leaves the run
holding; a stop request during the hold ends it. Only an explicitly configured
`RUN_WORKFLOW_CONSULT_TIMEOUT` hands the claim to repair without advice.
Answers are `plan-defect: repair`, `plan-defect: apply`, or `plan-defect: stop`
(the launcher also accepts the bare verb, case-insensitively). Invalid answers
leave the gate open.

On `apply`, the supervisor changes exactly the declared before-text →
after-text pair in both contract copies, re-runs `Done:`, and reports the
outcome. A missing exact edit, red result, expired explicit apply timeout, or
an edit that grows into a rewrite restores the touched files and proceeds to
fresh repair. A granted stop leaves the tree free for the foreman to clarify
with the user and amend both plan and contract tests in a separate `wf:` commit
before relaunching.

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

For a major report or close-out, load `<PLUGIN_ROOT>/judges/report-judge.md` and
give that shipped prompt to a fresh read-only Codex subagent. It probes whether
the draft answers: what changed, what remains, what was verified, and what the
user must decide. It returns comprehension gaps only. Revise once; do not start
an editorial loop or invoke a bare judge name.

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
