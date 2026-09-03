---
name: close-phase
description: Close the phase whose work is finished — naming review, Done gate, plan update, one phase commit, and routed outcome. Invoke at the end of an interactive phase, when the user says the phase is done, or on an in-progress phase whose interrupted session left complete but unclosed.
---

# Close Phase

Turn finished work into a closed phase: naming review, Done gate, `[x]`
record, ONE phase commit, routed outcome. **The happy path only** — a
phase that fails closes `[!]` where it failed, inside the executing skill;
this skill never writes `[!]` or `[~]`.

Three ways in, one mechanic:

- **From `/execute-phase`** — its closing step is this skill.
- **Model-invoked** — the conversation's phase work is done and verified;
  closing is not a question, so nothing asks permission to *start* (the
  naming review carries its own question, and the commit is the phase
  commit the flow already owes).
- **Manual** — `/close-phase` on a `[>]` phase whose work a dead session
  finished but never closed; before this skill, the only honest move was
  resetting completed work to `[ ]`.

**Shared conventions:** read `<PLUGIN_ROOT>/refs/common.md` and
`<PLUGIN_ROOT>/refs/contracts.md` once at start — core conventions
plus the contract layer this close verifies (Done gate, contract-test
integrity, markers). The relay's message formats are reached at the notify
step through the shared core, not read at start.
**Shared mechanics:** `<PLUGIN_ROOT>/refs/phase-execution.md`
(outcome format, the phase commit, notify) and
`<PLUGIN_ROOT>/refs/naming-review.md` (the naming review) — cited,
never restated.

## Step 1: Identify the phase

Invoked from the executing conversation, the phase is the one just
executed — no lookup needed, and the caller's outcome material (touched
files, `> Review:`/`> Verify:` notes) travels with the invocation.

Invoked standalone, resolve the plan first
(`python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --resolve`; from
outside the plan's root, `--plans` + `git -C` per `common.md` → *Plan
location*). The phase to close is the `[>]` one; none → nothing to close,
say so and stop.

**A standalone close gates on evidence.** This session did not write the
work, so the work must speak: read the phase's `> WIP:` note, diff from its
`commit:` (`git diff <commit>..HEAD`), and check what exists against the
phase's `Done:`. No note, no `partial` commit, or a diff that does not
reach `Done:` → this is a resume-or-reset case
(`refs/phase-execution.md` → *Resuming a `[>]` phase*), not a close —
say so and stop. Closing unverified work would forge the one guarantee
`[x]` gives the plan's next reader.

## Step 2: The Done gate

Re-check the phase's `Done:` literally, criterion by criterion — run the
named tests, the named lint, verify the named output. An unmet criterion
blocks the close: report it and stop, leaving the phase `[>]`. In the
`/execute-phase` flow this re-runs checks that just passed — cheap, and it
is what makes `[x]` a contract instead of a claim.

**Contract tests gate the close too.** Where the plan carries
`tests/phase-N/` for this phase (`contracts.md` → *Contract tests*), check the
in-tree copies against the plan copies AND the plan copies against the commit
that added the plan (`git diff <plan-commit> HEAD -- <plan-dir>/tests/phase-N/`
empty). Executable tests are byte-identical; skeletons keep their names and
every `wf:contract:` line verbatim, with no red body left. A divergence not covered by a decision in
`notes.md` under `## Phase N` blocks the close exactly like a red
criterion — the contract was edited by the wrong writer, and closing over
it would launder the edit into `[x]`. The gate reads the record, never the
route it arrived by.

**The contract fields have the same gate.** Markers and `>` notes move during
execution; `Done:`, authored `Verify:`, `Pattern:`/`Pattern reference:`,
`Files:`, and `Decisions:` do not. Resolve the plan path as `PLAN`, find its
addition on this branch only, and compare the selector's normalized block:

```bash
PC=$(git log -1 --diff-filter=A --format=%H HEAD -- "$PLAN")
diff <(git show "$PC:$PLAN" | python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --contract-block N -) \
     <(python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --contract-block N "$PLAN")
```

An empty `PC`, or a diff without a covering decision in `notes.md`
under `## Phase N`, blocks the close. Never search `--all`: a reused slug on
another branch is not this plan's origin.

**Two ways a criterion goes unmet, and only one of them is a refusal.**
Something the phase built is red — a failing test, a lint error — and the
close stops, full stop: that is repair territory, never absorbed here. But a
criterion covering work the phase never got to, with everything it *did*
build green, is the **closed short** case (`<PLUGIN_ROOT>/refs/phase-execution.md`
→ *When the phase outgrows its chat*): say which criteria are unreached,
propose the `Done:` narrowed to the sub-result that exists, and close on the
user's ok. The `closed short` outcome and re-planning take the configured
route: the foreman on relayed, the user at this gate on in-chat.

## Step 3: Naming review

Run `<PLUGIN_ROOT>/refs/naming-review.md` scoped to this phase's
touched files. The fast path is one keypress: accept all → markers
stripped, nothing else changes. Renames re-run the narrow signal per the
ref before anything commits.

## Step 4: Record, commit, notify

A phase held open for the human's checks carries a `> Testing:` note (`<PLUGIN_ROOT>/refs/phase-execution.md` → *Awaiting the human's checks*): drop it here — `[x]` and the note contradict each other, and the checks it was waiting for are recorded as `> Verify:` like every other.

**Closing a phase whose result the person rejected** is this same close with a different report: record the `> Review:` verdict and route the `result rejected` outcome per the shared core, because what follows is re-planning, not the next phase. On relayed the next step is `/resume-workflow` in the foreman task; on in-chat it happens with the user at this gate.

Exactly as `refs/phase-execution.md` specifies — *Record the outcome*, *The
phase commit*, *Notify the foreman*: the `[x]` entry with `> Done:`,
`> Files:` (ALL touched files), the `> Review:`/`> Verify:` notes handed
over by the caller; ONE phase commit `wf(phase N): <title>` carrying code,
naming-review edits and plan update together, whatever partial commits
preceded it; then the relayed message when applicable. A choice the review made worth remembering (a rename and why)
goes to `notes.md` under the phase's `## Phase N` heading before the
commit.

```bash
osascript -e 'display notification "Phase N closed: <title>" with title "Codex — <repo>/<branch>" sound name "Glass"'
```

Close with the next step, always: the next phase with its `Run:` hint
quoted, or `/quality-check` (then `/finalize-workflow`) when this was the last.
On relayed, the next phase starts in a new task; on in-chat, `/execute-phase`
runs again in this conversation. The user must never
need to know the flow by heart to keep moving.

## Rules

- Happy path only: never write `[!]` or `[~]`, and never absorb a criterion that is *red* — a criterion merely **unreached**, with what exists green, is the closed-short case above, and it is closed by narrowing the `Done:` with the user, never by ignoring it
- ONE phase commit — naming-review edits never get their own; planned batches
  land as partial commits before it, never as a second close
- A standalone close without evidence of completed work is a refusal, not a favour
- The naming-review sweep (grep for `wf:phase-` over the touched files, empty) runs before the commit, even on the accept-all path
