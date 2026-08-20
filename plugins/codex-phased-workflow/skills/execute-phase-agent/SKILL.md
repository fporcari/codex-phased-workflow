---
name: execute-phase-agent
description: Execute the next phase unattended — no questions, baseline attribution, convergence loop, one commit per phase
---

# Execute Phase — Agent

Execute ONE phase of the active plan unattended: implement, test, record the outcome, commit, exit.

**Base skill: execute-phase** — the same work with nobody to answer a question. This variant states only the unattended constraints; the mechanics shared by both modes (phase selection, implementation discipline, outcome formats, the phase commit, the WIP checkpoints) live in `<PLUGIN_ROOT>/refs/phase-execution.md` and are not restated here.

**Usage:** `codex exec '/execute-phase-agent'` — or `/run-workflow` for the whole plan.

**Non-negotiables:**
- **No questions.** Never Codex user-input prompt — there is nobody here who can answer. Decide, and document the decision in the plan.
- **Output is a log.** Nobody reads this session live; every word of narration is token spend with no reader. Silence between tool calls — one short line only on a load-bearing finding, a change of direction, or a blocker — and a closing report of the ✓/⚠ line plus at most three sentences. Never restate the plan or the phase text.
- **The outcome in the plan is the exit condition**, not bookkeeping — under `/run-workflow` an independent evaluator re-checks it every turn.
- One phase, one commit at the end, everything written in English — per the shared core.

**Shared conventions:** `<PLUGIN_ROOT>/refs/common.md` and `<PLUGIN_ROOT>/refs/contracts.md`. The foreman layer is NOT read at start: only its message formats matter here, at the notify step, per the shared core.

## Step 0: Read the plan

Resolve the active plan (`python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --resolve`, see `common.md`; from outside the plan's root, `--plans` + `git -C` per `common.md` → *Plan location*) and read it. No `[ ]` phases left → print "All phases completed. Run /quality-check, then /finalize-workflow." and exit.

## Step 0.2: Baseline check (before any edit)

Run the project's green signal — test suite + linter (pytest/flake8 projects: `python -m pytest tests/ -q`, `flake8`). Green → proceed. No signal configured → note it and proceed.

**Red → the failure is not yours.** Do not fix it, do not start the phase. Attribute it against the `> Files:` notes of the `[x]` phases:

*Case A — an earlier phase owns those files.* It was closed `[x]` wrongly. Reopen it and exit without touching your phase:

```
- [!] **Phase M**: title
  > Issue: regression detected at the baseline check of Phase N: <failure signature>. Closed [x] but broke <file>, which its own Done criterion did not cover.
  > Attempted: (none — reopened by a later phase's baseline check, not by a failed fix loop)
  > Files: <the culprit phase's original Files: list, preserved>
```

Keep its `> Done:`/`> Repaired:` history — the repair session needs it.

*Case B — nobody owns it* (pre-dates the run). Mark your phase `[~]` with a `> Blocked:` note naming the failure signature, and exit.

Ambiguous attribution → prefer Case B. A wrong reopen burns the culprit's only repair on the wrong bug.

## Step 0.4: Restore point

`HEAD` is the restore point: every earlier phase committed its own work, so the tree is clean when you start. A **dirty tree means something is wrong** — a previous session died mid-phase, or someone edited by hand. Do not commit it as if it were yours: report what is uncommitted, mark your phase `[~]` with a `> Blocked:` note naming the stray files, and exit.

## Step 1: Select the phase

Per the shared core. The mode-specific outcomes, decided here instead of asked: `resume-candidate: N` → resume it if `wip: yes`, else take it over if older than 2h, else exit reporting it busy; `attention: ...` → mark the pending phase `[~] Blocked` and exit.

## Step 2: Implement

Per the shared core, scaling exploration to the **Effort** column of the execution config table (missing table → `high`): `low` only the listed files; `medium` + immediate references; `high` up to 2 Explore subagents and the surrounding package; `xhigh`/`max` up to 3 plus a cross-package consistency pass.

## Step 3: Write tests

Phases with contract tests start from them: copy `tests/phase-N/` verbatim and make them green — a skeleton's body is yours, the rest is read-only, and a test that cannot pass as written closes the phase `[!]` with `> Issue: plan-defect claim — …` (`contracts.md` → *Contract tests*: the exact wording, and why it is a claim the launcher routes upstream, never your verdict); never edit a contract into passing. The same claim format applies when the blocker is the plan itself — a `Done:` premise that turns out false, a pre-made decision that cannot be implemented. Then test the phase's remaining logic following the repo's existing test patterns. Purely UI/declarative phases with no testable logic → skip.

## Step 4: Convergence loop

Green signal = test suite + linter scoped to the touched files. Both must pass.

- **Green** → Step 5.
- **Failure** → up to **3 fix attempts**. Each: find the root cause before patching (grep the callers — one fix in the shared function beats a patch in the failing path), fix, re-run.
- **No-progress detector**: identical failure signature twice in a row → stop early.
- **Revert, don't stack**: an attempt that leaves the signal worse gets undone (`git checkout -- <files it touched>` returns to `HEAD`, the Step 0.4 restore point) before re-diagnosing. Patch-on-patch also poisons what `/repair-phase` receives.
- **Budget exhausted or stuck** → `[!]` with the shared core's notes. Leave the failing code **in place** — repair needs to see it.

## Step 5: Verify and gate

**The Done gate always runs.** Re-check the phase's `Done:` field literally, criterion by criterion — run the named test, the named lint, verify the named output. "Tests pass" is not enough if `Done:` says more. An unmet criterion is a failure: back to Step 4 if attempts remain, else `[!]` naming it in `> Issue:`. This is a contract check against a criterion you did not write — not a re-read of your own work.

**An independent verifier runs only where it earns its keep**: the phase's `Pattern:` is `new-pattern`, or the phase is marked `sonnet` (legacy plans only — sonnet left the palette). Otherwise skip it — you already check your own work as you go, and a second review pass on a well-specified phase mostly re-litigates settled decisions.

When it does run: ONE `phase-verifier` subagent (Codex subagent; fallback: a general-purpose subagent told to stay read-only), given the phase objective and `Done:`, its `Pattern:` example, **only this phase's touched files**, and — where the plan carries them — the phase's contract-test paths, plan copy and in-tree copy. Findings: **MECHANICAL** (real bug, wrong API, divergence from the pattern) → fix, re-run the signal, same 3-attempt budget. **JUDGMENT** (design trade-off, human call) → do not fix; record as `> Review:`. Never blocks `[x]`.

## Step 6: Record, commit, stop

Record the outcome and make the phase commit exactly as the shared core specifies. The `wf:phase-N:new` markers on new callables stay in place — nobody here can answer a naming question; `/quality-check` runs the whole-workflow naming review (`contracts.md` → *New-method markers and minimality*). **Thin `Verify:` pass — thin, never absent** (`<PLUGIN_ROOT>/refs/contracts.md` → *Verification*): the phase's authored `Verify:` fields, plus anything only human eyes can judge, become `> Verify:` notes with their *when*; deferred ones are appended to `verify.md` under a `## Phase N` heading. No browser skill runs here, and `Verify:` never carries what the tests already cover — most phases end with none. A `ui`-tagged phase reaching this skill lost its mockup gate and browser pass by construction (the tag belongs to interactive plans): note it, and hand the visual check to the human as a `Verify: now` step.

Then the shared core's *Notify the foreman* — one outcome message, best-effort, no retry: in a `-p` sub-session the messaging tool may simply not exist, and that is the silent-skip case, not a failure.

Print `✓ Phase N completed: <title>` or `⚠ Phase N has issues: <reason>` and stop.
