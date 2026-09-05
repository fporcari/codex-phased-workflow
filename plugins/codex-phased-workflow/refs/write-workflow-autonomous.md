# Write Workflow — Autonomous addendum

Loaded by `/write-workflow` when its automation fork (Step 2) selects autonomous. Everything in the main skill still applies; this adds a stricter refinement and format, because the plan must pass the launcher's pre-flight without a single question.

The fork already asked whether the plan targets autonomous execution — do not ask again. If the refinement below reveals the task does not fit, the *Honesty check* is the way back.

## Per-phase refinement

1. **Pattern reference.** For non-trivial code, find 1–2 existing examples and propose them: *"For Phase X I follow the pattern of `path/to/example.py:func`. Confirm?"* No clean candidate → ask the user; still nothing → propose 2–3 based on the phase description; still nothing → the phase is `new-pattern (flagged: higher risk)` and the user is told it is riskier autonomously. Library-standard work needs no reference.
2. **Scope safety.** Sub-sessions run in Codex `workspace-write` without automatic escalation approval; the autonomous boundary is listed in `<PLUGIN_ROOT>/refs/auto-mode-scope.md`. A phase needing something outside it must surface the action and offer: stop before it, drop it, or run that phase interactively. Never silently rewrite a phase to hide it.
3. **Pre-make every external decision** (library, naming, signature, API shape, trade-offs) and record it in `Decisions:`.
4. **Bound the scope**: concrete paths in `Files:`, or an explicit discovery rule.
5. **Measurable `Done:`.** It is the literal exit condition of the executor's loop — `/execute-phase-agent` re-runs each criterion verbatim before closing the phase. Write re-runnable checks ("pytest tests/test_foo.py::test_bar passes", "flake8 zero errors on the Files: set"), not prose.
6. **`Verify:` only where human eyes are genuinely needed** — the mechanism is thin in this mode and most phases carry none, but it is never absent (contract: `<PLUGIN_ROOT>/refs/contracts.md` → *Verification*); each step carries its *when* (`now` / `deferred: needs Phase M`).
7. **Contract tests carry even more weight here** — nobody watches an unattended run, so where the option (main skill, Step 3) chose them, every phase's `Done:` opens with its plan tests and a test the phase cannot pass unchanged closes it `[!]` (`contracts.md` → *Contract tests*). The option is asked once, in the main skill — do not re-ask.
8. **Sweep negative assertions across phase boundaries.** After authoring the
   contract tests, collect every forbidden substring and rejected shape, then
   check it against every other phase's `Decisions:` and `Done:` — including
   golden files and round trips. Resolve any prohibition that another phase's
   required output can force before presenting the plan.

## Honesty check

If the refinement reveals the task doesn't fit autonomous execution, say so instead of forcing it — flip the fork (Step 2 of `/write-workflow`) back to interactive rather than bending the plan to a mode it resists. Red flags: the work *is* the exploration; decisions that only implementation can settle; visual/UX output needing human judgment per iteration; heavy dependence on external state; tests requiring human setup; success meaning "the user will recognise it when they see it".

The user picks autonomous when the task suits it, so friction usually means a misunderstanding, not a stubborn user. Stop and ask:

> *"Wait — this plan resists being made autonomous. Reason: <concrete reason>. It is probably one of two things: (a) I misunderstood something — let's clear it up; (b) the task really does suit interactive better — shall I go on with a normal interactive plan? Which is it?"*

**Not a rejection:** phases unspecifiable only because they depend on *earlier phases' outcomes* — that plan is too ambitious for one wave, so split it into macro-phases.

## Macro-phases (rolling wave)

Use macro-phases when outcomes must inform later planning or integration needs
an accepted checkpoint. Detail only the next ready macro; keep later scopes in
`.phased/roadmap.md`, which survives archival of the current plan.

**Scope every macro.** Verify factual premises in the code; batch unresolved
product decisions once. Each mini-scope records the itinerary and contracts below.
Later detail is deferred, not its consumer requirements.

```
# Roadmap
## Macro 1 (current): <title> — detailed in active/<slug>/plan.md
## Macro 2: <title>
- Objective: <2 lines>
- Starts from: <the state it assumes standing when it begins>
- Ends at: <the state it leaves the system in — the border, never the locally convenient stop>
- Delivers: <what lands, and who consumes it>
- Consumes: <what it takes, and from which macro>
- Requires of earlier work: <what it will demand of output built before it — the seeds of their Must not break:>
- Open decisions: <what must be settled when this macro is planned — recorded, not resolved now>
```

Collect later macros' Requires of earlier work into this macro's Must not break,
including contracts in transit. Ends at and Starts from must describe compatible
states; a locally convenient stopping point is not sufficient.

**One seam review.** For a multi-macro plan, a fresh read-only reviewer checks
mini-scopes against the itinerary and contract graph: each Ends at matches the
next Starts from; every Consumes has a producer; every Delivers has a consumer or
is the final result; Requires of earlier work survives every intermediate macro.
Consolidate gaps, correct the split once and verify the changed seams. Do not
turn this into another implementation phase or a repeated whole-plan review.

Keeping the roadmap out of `plan.md` also means the launcher cannot mistake its blocks for phase lines: the separation is structural (no `[ ]` markers here), not a matter of formatting.

The cycle: `/run-workflow` → `/quality-check` → `/finalize-workflow` (bounded, review-sized diff) → **human checkpoint** → new chat, `/write-workflow` details the next macro with hindsight — **starting from its mini-scope**: the `Open decisions` are its scoping agenda, the later macros' `Requires` become its `Must not break:`, and its `Ends at:` is a planning constraint — the last phases must land the system there. Deliberately manual: that boundary is where human judgment pays most. Independent macros can run in separate worktrees with separate PRs.

## Plan format

`vast` is the only tag; every phase is tested alone, in order.

```
# Context: <branch-name>
Parent: <parent-branch> | Issue: #<number> (if present)
Mode: autonomous
Channel: relayed
Must not break: <one line per contract owned by later work — contracts.md → *Must not break:*; omit only when no roadmap and no known consumer>

## Objective
[2-3 sentences]

## Work Plan
- [ ] **Phase 1**: <concise title>
  - Pattern reference: `path/to/example.py:func` (or `library-standard`, or `new-pattern (flagged: higher risk)`)
  - Files: <concrete paths — no "TBD">
  - Decisions: <pre-made choices>
  - Details: <step-by-step>
  - Done: <measurable criterion>

[... more phases ...]

## Notes
[Attention points, dependencies, breaking changes, scope deviations recorded during refinement]

## Suggested execution config
| Phase | Effort | Model |
|-------|--------|-------|
| Phase 1 | ... | ... |
```

Keep the column order exactly as above — `/run-workflow` reads Effort and Model
**by column position**. The Phase cell is only `Phase <number>`; a parenthetical
there is rejected by `next-phase.py --validate`.

- **Effort**: passed to Codex as `model_reasoning_effort`. Start low and climb only for a reason: `low` mechanical, `medium` standard well-specified work, `high` for surviving design judgment, `xhigh` for wide multi-file consistency, `max` for the hardest repair or architecture. Effort and model are separate decisions.
- **Model label**: write `opus` by default and `fable` for genuinely hard architecture, debugging, or novel design. These values preserve Claude interoperability; Codex maps `opus` to Sol and `fable` to Astra, retaining the effort column for depth. Accept `sonnet` from legacy plans but never author it.

## Closing message

Report the plan path, delivery-phase count, branch and checks. Each phase carries
pattern, scope, decisions and measurable Done; one diagnosed local correction
and one fresh repair are bounded. Point to run-workflow, then quality-check for
one consolidated correction batch. Do not add a mandatory review phase.
