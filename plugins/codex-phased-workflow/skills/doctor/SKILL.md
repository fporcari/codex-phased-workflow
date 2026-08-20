---
name: doctor
description: Diagnose the active workflow against its own plan — do the pending phases' premises still hold on what actually landed, were the contract tests honoured, and where a plan has none, retro-fit them blind and verify the completed phases against the plan's own promises. Use when phases feel incompatible with each other, after upgrading the plugin on a mid-flight workflow, or before resuming work that has been sitting.
---

# Doctor

A checkup of the workflow against its own plan. `/resume-workflow` reports
where the work *stands*; this skill asks whether the work is still *coherent*
with where the plan says it is going — and, on plans that predate contract
tests, retro-fits the tests and lets them deliver the verdict. Episodic and
deliberately heavier than a status query: run it when something smells, not
on every visit.

**Read-only on source code.** The only files this skill may write live in the
plan directory — `.phased/active/<slug>/tests/` and `notes.md` — each write
committed as its own `wf:` commit. A finding is reported, never fixed here:
the remedies belong to `/resume-workflow` (re-planning) and `/repair-phase`
(a machine-red `Done:`), and a completed phase is **never reopened** — a red
retro-test on a `[x]` phase is the *result rejected* family (`common.md` →
*Failure and repair notes*), not a `[!]`.

**Shared conventions:** read `<PLUGIN_ROOT>/refs/common.md` and
`<PLUGIN_ROOT>/refs/contracts.md` once at start — language, plan
directory, the contract-tests contract. The reporting register lives in
`refs/foreman.md`; read that section at the findings step.

## Step 1: Find the plan, read it whole

```bash
python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --resolve
git log -1 --diff-filter=A --format=%H -- <plan path>
```

No active plan → stop and say so (`--plans` first, per `common.md` → *Plan
location*). The second command gives `BASE`. Read the whole plan — every
phase, every note: the diagnosis is exactly the cross-reading a phase chat
cannot afford.

## Step 2: Coherence audit (cheap, no agents)

For each **pending** phase, check its premises against the state the `[x]`
commits actually left (`git log --oneline "$BASE"..HEAD`, `git show --stat`,
targeted greps):

- a file its `Files:` names that was renamed, moved, or deleted;
- a data shape, signature, or behaviour its `Details:` builds on that came
  out different;
- a `Pattern:` example that a completed phase refactored away.

Each mismatch is a finding: *which pending phase, which premise, what the
tree says instead*. This is the retrospective counterpart of
`/run-workflow`'s per-phase coherence look — done once, over the whole plan.

On a programme (`.phased/roadmap.md` exists) the audit widens: the plan's
`Must not break:` header and the roadmap's remaining macro-phases are
premises of the same rank (`contracts.md` → *Must not break:*) — check the
landed work against them too.

## Step 3: Contract-test integrity (where the plan carries them)

Per `contracts.md` → *Contract tests*: for each `[x]` phase with
`tests/phase-N/`, check the in-tree copies against the plan copies —
executable tests byte-identical; skeletons with names and every
`wf:contract:` line surviving verbatim, no red body left — then re-run them.
A divergence with no foreman decision in `notes.md`, or a test gone red, is
a finding. Pending phases: their plan copies exist and are red by
construction — nothing to run yet.

## Step 4: Blind retro-fit (where the plan has no contract tests)

Findings from Steps 2–3 in hand, ask ONE Codex user-input prompt: retro-fit and
verify (recommended when incoherence is suspected — this is where the
verdict stops being inference), audit-only report, or stop. On yes, two
agents with two different blindfolds:

1. **The blind author** — a fresh subagent given ONLY the plan's phase texts
   (`Details:`, `Done:`, `Decisions:`) and ONE pre-existing test file as a
   style example (pick it at `BASE`: `git show "$BASE:<path>"` — never a file
   a phase touched), and told to read nothing else: not the diffs, not the
   `Files:`, not the code the phases wrote. Blindness is the point — a test
   written from the code ratifies the code's own deviations; written from
   the plan, it embodies the promise. It authors `tests/phase-N/` for every
   phase, at the two precisions of `contracts.md` → *Contract tests*:
   executable where the plan fixes the signatures, `wf:contract:` skeletons
   where it does not.
2. **The sighted verifier** — a second subagent, on the `[x]` phases only,
   in plan order: fills each skeleton's body against the real code,
   implementing exactly what the `wf:contract:` lines state, and runs the
   phase's tests (`python3 -m pytest` pointed at the plan directory). Green →
   the phase honoured the plan. Red → an incoherence finding: the plan
   promised one thing, the code does another — report it, with the failing
   assertion as the evidence. Never fix, never touch source, never reopen
   the `[x]`.

Pending phases get authorship only: their tests stay red by construction and
become the gate of their own phase, exactly as on a plan born with them.

**A consumer measured late** is the same machinery pointed backwards: when a
later macro-phase's requirements are known — measured during its planning,
or stated by the user in this chat — hand them to the blind author as
`wf:contract:` skeletons against the component that must serve them
(`contracts.md` → *Must not break:*), and let the sighted verifier run them
against what the earlier macro actually built. The reds enumerate exactly
which requirements the landed shape cannot carry — "the decision must be
revisited" becomes a measured list, which is what the remedy phases are
then written from.

Commit the authored tests and the filled bodies together, ONE commit:
`wf: doctor — contract tests retro-fitted (<n> phases, <m> red)`.

## Step 5: Report and persist

Findings, in the reporting register (`foreman.md`), one verdict line first —
coherent or not, and the single fact that matters — then one line per
finding, classified:

- **RECORD** — the plan's bookkeeping is wrong (a `> Files:` note diverging
  from its commit): `/resume-workflow` territory.
- **COHERENCE** — a pending premise broken, or a red retro-test on a `[x]`
  phase: re-planning territory — remedy phases in the tail, via
  `/resume-workflow` in the foreman chat.
- **INTEGRITY** — a contract test edited outside the foreman road: name the
  edit; the decision on it is the foreman's.

Append the same findings to `notes.md` under a `## Doctor <ISO date>`
heading, committed (`wf: doctor — findings`): the chat dies, the file is
what `/resume-workflow` and finalize read. Healthy plan → say so in one
line and stop; no commit, no note.

Close with the next step, always: `/resume-workflow` in the foreman chat for
re-planning, `/repair-phase` only for a genuinely machine-red `Done:`,
nothing when healthy.
