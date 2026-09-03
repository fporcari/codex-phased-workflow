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

Split when more than ~8-10 phases would be needed, or a phase can only be written concretely after an earlier one lands, or the combined diff would be too large for one quality-check review.

Detail ONLY the first macro as the Work Plan (5-8 phases). The rest go in `.phased/roadmap.md` — a file of its own, one level above `active/`, because the roadmap has to outlive the macro currently being worked: when `/finalize-workflow` moves `active/<slug>/` into `done/`, the roadmap stays where the next `/write-workflow` will look for it.

**The split is scoped, not just listed.** The moment the split is proposed
is the only moment the whole programme sits in one context, and a macro
reduced to a one-line bullet is how a future consumer's requirements die
(issue #15). So every macro — not only the first — gets a **mini-scope**, at
`/scope-workflow`'s bar but produced here, automated: ground facts come from
the codebase (one read-only Explore subagent per area from ~3 up, at most four
running at once; each returns verified paths and explicitly unverified
premises — a fact is looked up, never asked), and the decisions that belong to the user are
batched into ONE Codex user-input prompt round — never one interview per macro. The
format, one block per macro:

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

*Delivers* names the forward half of the contract — what lands and who
consumes it — and *Requires of earlier work* the backward half: when a later
`/write-workflow` details a macro, it collects from the LATER macros'
`Requires` lines everything that touches what this macro builds, and those
become its `Must not break:` header (`contracts.md` → *Must not break:*) —
confirmed from the roadmap, not reconstructed from memory.
`Starts from:`/`Ends at:` are the **itinerary**: plan a European tour as
Italy, France, Spain, and the Italy leg must not end in Puglia — internally
perfect, and stranded at the wrong border.

**The coherence judge.** Before the split is presented, ONE fresh-context
subagent (Codex subagent; read-only; fallback: a general-purpose subagent told
to stay read-only) gets the mini-scopes ALONE — not the conversation — and
returns one `ITINERARY: <macro N -> macro N+1> — <gap>` per broken seam, one
`CONTRACT: <edge> — <loss>` per broken edge, or exactly `COHERENT`. It checks:

1. **The itinerary first**: the `Ends at:` of every macro ≡ the
   `Starts from:` of the next. A gap here blocks the presentation — it is
   the split itself that is wrong.
2. **The contract graph**: every `Consumes` is delivered by an earlier
   macro; every `Delivers` has a consumer or is the final deliverable;
   every `Requires of earlier work` names output some earlier macro
   actually builds; no two macros contradict each other's semantics (a
   stack kept parallel by one macro and assumed cut over by another).
   The edges hop: a `Requires` may point several legs back, and every
   macro the edge crosses inherits the constraint — what is in transit
   must not be lost by a leg it merely crosses (`contracts.md` →
   *Must not break:*, producer-to-consumer rule). Flag any intermediate
   macro whose scope plausibly destroys what crosses it.

Findings → fix the mini-scopes, re-judge ONCE, then present the split.
Fresh eyes by design: the author of a split is the worst judge of its own
seams.

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

- [ ] **Phase N+1**: Coherence review and auto-fix (final, mandatory)
  - Pattern reference: same as Phases 1..N (cross-check against them)
  - Files: only the files written by Phases 1..N (collect them from their `Files:` fields). Never touch a pre-existing file they did not modify.
  - Decisions:
    - Auto-fix directly: tool-fixable lint (ruff/prettier/eslint/black), unused imports, formatting, trivially mechanical fixes. Re-run the tests after each non-tooling fix; if one breaks a test, roll back that fix and flag it instead.
    - Never auto-fix: logic errors, design divergences from the pattern reference, missing edge cases, anything architectural. Those go to `review.md` only.
  - Details: convergence loop (max 3 cycles) of linter scoped to the file set → auto-fix → linter → test suite; stop early if a cycle makes no progress. Then write `.phased/active/<slug>/review.md` with three sections: **Auto-fixed** (file, what, tool), **Flagged for human** (file, description, suggested action), **Final state** (linter output, suite result, files reviewed).
  - Done: `review.md` exists in the plan directory with the three sections, linter zero errors on the file set, full suite green.

## Notes
[Attention points, dependencies, breaking changes, scope deviations recorded during refinement]

## Suggested execution config
| Phase | Effort | Model |
|-------|--------|-------|
| Phase 1 | ... | ... |
| Phase N+1 | xhigh | opus |
```

Keep the column order exactly as above — `/run-workflow` reads Effort and Model
**by column position**. The Phase cell is only `Phase <number>`; a parenthetical
there is rejected by `next-phase.py --validate`.

- **Effort**: passed to Codex as `model_reasoning_effort`. Start low and climb only for a reason: `low` mechanical, `medium` standard well-specified work, `high` for surviving design judgment, `xhigh` for wide multi-file consistency, `max` for the hardest repair or architecture. The model remains `gpt-5.6-sol` at every level.
- **Model label**: write `opus` by default and `fable` for genuinely hard architecture, debugging, or novel design. These values preserve Claude interoperability; Codex maps both to Sol and uses the effort column for depth. Accept `sonnet` from legacy plans but never author it. The final review is `opus` at `xhigh`.

## Closing message

```
Autonomous-ready plan written to .phased/active/<slug>/plan.md (<N> phases + final review), committed on <branch>.
Every phase carries: pattern reference, files, pre-made decisions, a measurable done criterion.
Each phase runs a self-correcting loop (3 test+lint attempts, independent review, gate on the Done); a failed phase gets ONE automatic fresh-eyes repair before it stops for you.
The final review fixes the trivial slips and flags the rest in .phased/active/<slug>/review.md.
To run it: /run-workflow (it will pass the pre-flight check with no questions).
```
