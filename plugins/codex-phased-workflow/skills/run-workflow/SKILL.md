---
name: run-workflow
description: Run every remaining phase autonomously in a fresh high-quality Codex session per phase, preserving the portable .phased protocol and stopping on unresolved failures or blocked work.
---

# Run workflow

Run the remaining phases through `<PLUGIN_ROOT>/scripts/run-workflow.sh`. Each
phase and repair gets a fresh ephemeral `codex exec` session using
the selected Sol/Astra model, Codex `workspace-write`, and the plan's effort. This chat is the
inspector: it owns the live `EVENT:` stream, dashboard requests, plan-defect
return leg, and graceful stop. The launcher owns worker processes and durable
logs; neither surface changes the portable `.phased/` state machine.

`RUN_WORKFLOW_MAX_ATTEMPTS=N` caps worker launches in this invocation, including
repair and provider fallback. Zero launches none. `RUN_WORKFLOW_MAX_PHASES=N`
limits completed phases; it does not bound repair cost. At the attempt boundary,
stop with durable state; relaunch needs remaining authority. Existing Repair
attempted notes still prevent another automatic repair. There is no portable
currency or soft-budget enforcement; report unknown usage as unavailable.

## Pre-flight gate

1. Resolve and validate the active plan:

   ```bash
   python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --resolve
   python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --validate
   ```

2. Require `Mode: autonomous`. An interactive plan must be refined first.
3. Read every phase. Reject unresolved decisions, non-measurable `Done:`, and
   destructive or externally consequential actions that cannot safely run under
   Codex `workspace-write` without an escalation.
4. Preserve the compatibility model labels in the plan. `opus` and `fable` are
   portable protocol vocabulary shared with Claude; Codex maps `opus` and
   legacy `sonnet` to `gpt-5.6-sol`, and `fable` to `gpt-6-astra`. Effort remains `low|medium|high|xhigh|max`.
5. Read `## Suggested execution config`: every row is `Phase <N>`, and its
   effort is one of `low|medium|high|xhigh|max`. The selector validates the
   table; the launcher reads it by column position. There is no environment
   override for the implementation model.
6. Show the final phase list and the runtime mapping. End with the explicit
   launch gate: “Launch? On your ok the autonomous run starts over all remaining
   phases.” Do not start before that answer.

## Launch

Resolve the transport prefix and keep the complete inspector log outside the
repository. Run it in a durable terminal/session so this chat can keep serving
the stream:

```bash
T=$(python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --transport)
install -d -m 700 "$(dirname "$T")"
bash "<PLUGIN_ROOT>/scripts/run-workflow.sh" 2>&1 | tee "$T-run.log"
```

The launcher writes the complete worker attempt outside the tree while it is
running. Once that attempt lands its one outcome commit, the launcher copies the
log to `log/phase-N.txt` or `log/repair-N.txt` beside the plan and amends that
same commit; the tree stays clean and the durable record remains portable.

## Monitor and return legs

Follow `EVENT:` lines, the process result, and the plan marker together. Report
each `phase-done`, `phase-repaired`, `phase-applied`, first failure, blocked
phase, and final `run-end`. After every landed phase, inspect the changed phase
against the plan: its negative assertions must not contradict another phase's
`Decisions:` or `Done:`, including golden files and round trips. A newly exposed
contradiction is a plan defect, not an implementation success to wave through.

When `EVENT: phase-needs-foreman:N` appears, relay the recorded claim to the
foreman/user. Before asking, inspect the claim against the exact code and
contract it names; attach claim, evidence, and your verdict to one question.
Then write one answer to `$T-foreman-answer`:

- `plan-defect: repair` — recommended when inspection does not confirm the
  claim; fresh eyes test implementability;
- `plan-defect: apply` — only for an explicit before-text → after-text edit,
  recommended when inspection confirms the one-line correction;
- `plan-defect: stop` — end the autonomous run and return planning authority.

The launcher also accepts the bare verbs and normalizes case. Invalid answers
leave it holding. There is no default deadline: the decision remains the
human's whenever they arrive. A graceful stop request during the hold ends the
run. Only an explicitly configured `RUN_WORKFLOW_CONSULT_TIMEOUT` falls through
to fresh repair.

On apply, the launcher emits `phase-apply-wait` and holds the workspace. Apply
only the declared edit to both contract copies, re-run the phase's literal
`Done:`, and follow `refs/foreman.md` → *Plan-defect claims*. Write `green` or
`red` to `$T-apply-outcome` before the deadline. Red, timeout, or an edit that
expands into a rewrite falls through to fresh repair.

The optional dashboard queues proposals rather than starting work. While this
skill owns the run, drain only requests stamped for this Codex task:

```bash
python3 "<PLUGIN_ROOT>/scripts/wfdash/outbox.py" -C "$PWD" --drain --owner "${CODEX_THREAD_ID:-}"
```

Collapse duplicate `run-workflow` intents, ignore an intent for a run already
active, and serve a `stop` by creating `$T-stop-request`. Requests stamped for
another task remain queued. An ownerless request is shown explicitly and needs
the current user's confirmation before this chat serves it.

For a deliberate graceful stop, create `$T-stop-request`. The launcher checks
between sessions, never kills a worker mid-write, and ends with
`EVENT: run-end:stopped-by-request`. `RUN_WORKFLOW_MAX_PHASES=N` likewise counts
landed phases, not attempts, and stops at the next clean boundary.

## Stop conditions

- all phases are `[x]`;
- a phase remains `[!]` after one fresh repair and carries
  `> Repair attempted:`;
- a phase is `[~]` because the baseline failure cannot be attributed;
- Codex exits non-zero;
- a session returns without changing the expected durable state;
- the configured maximum phase count is reached.

Timeouts are numeric seconds: `RUN_WORKFLOW_SESSION_TIMEOUT` defaults to 3600
and `RUN_WORKFLOW_APPLY_TIMEOUT` to 900.
`RUN_WORKFLOW_CONSULT_TIMEOUT` is unset by default; set it explicitly only when
an unattended handoff to repair is preferable to an open human decision. One
failed repair, no durable progress, invalid state, or the session budget ends
the run.

When every phase is `[x]`, point to `/quality-check`, then
`/finalize-workflow`. What the user's QA check and pre-commit review turn up is
fixed by the foreman as QA fixes and a final touch on a decided design, never
appended as a phase per finding (`/quality-check` → *QA fixes*, *The final touch*).

Never merge, publish, deploy, delete user data, or perform another external
side effect merely because the workflow is autonomous. Those actions still need
their own explicit authority.
