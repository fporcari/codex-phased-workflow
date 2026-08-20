---
name: write-workflow
description: Write a phased work plan from the current conversation — branch, plan directory, first commit
---

# Write Workflow

Plan a work session, then open the branch and commit the plan. The plan is the **only** deliverable.

1. **NEVER edit source code.** Read anything; write nothing outside `.phased/`.
2. **Do not implement.** The user runs `/execute-phase` afterwards.

**Shared conventions:** read `<PLUGIN_ROOT>/refs/common.md`, `<PLUGIN_ROOT>/refs/contracts.md` and `<PLUGIN_ROOT>/refs/foreman.md` once at start — core conventions, the contract layer planning authors, the take-command protocol. **The board** an interactive plan closes with is specified once in `<PLUGIN_ROOT>/refs/board.md` — read it at Step 6, not before.

## Step 1: Where are we

```bash
git branch --show-current
git rev-parse --show-toplevel
git rev-parse --verify origin/develop >/dev/null 2>&1 && echo develop || echo main
```

**On a feature branch** — read what is already there (`git log origin/<base>..HEAD --oneline`, `git diff --stat origin/<base>...HEAD`, the full diff, and `gh issue view <number>` if the branch starts with one), summarise it, then ask: *"What do you want to plan on this branch?"*

**On the base branch** — no exploration. Ask straight away: *"You are on `<branch>`. What do you want to do?"*

The user's answer is the primary input. Read code only in service of the plan.

This same fork decides the branch in Step 4 — remember which side you are on.

## Step 2: The automation fork

Before building the plan, settle how it will run. This is one explicit question, asked once, and its answer picks the plan format — never default silently to one mode.

Derive the recommendation from the work just discussed and state it in one line with its reason (there is no fixed default; the recommendation follows the task):

- **UI, declarative, or visual work — anything whose success is "I'll know it when I see it"** → recommend **interactive**.
- **Heavy refactor, project startup, mechanical migration — well-specified work with a measurable done** → recommend **autonomous**.

Ask with `Codex user-input prompt` (recommended option first, per `common.md`), two options:

- **Autonomous** — `/run-workflow` runs the whole plan unattended, one self-correcting sub-session per phase.
- **Interactive** — one chat per phase with `/execute-phase`, a human approval gate on each.

The answer routes the rest of this skill:

- **Autonomous** → read `<PLUGIN_ROOT>/refs/write-workflow-autonomous.md` and apply its stricter refinement and format on top of the steps below; the plan carries `Mode: autonomous`.
- **Interactive** → continue with this file's format; the plan carries `Mode: interactive`.

## Step 3: Build the plan

Extract from the conversation: objective, phases, files per phase, pattern references, decisions, sizing, notes.

**Pattern references.** Every `/execute-phase` runs in a fresh chat: whatever isn't in the plan gets re-discovered there, phase after phase. While the code is in front of you, find 1–2 existing examples to copy-adapt for each phase that writes non-trivial code, and record concrete paths in `Pattern:`. Library-standard work → `library-standard`; nothing comparable → `new-pattern`. From ~3 such phases up, dispatch one read-only Explore subagent per phase instead of searching serially, and reason over what they return.

**Decisions.** `/execute-phase` has a single approval gate, so every choice needing the user's judgment — naming, signatures, library, API shape, trade-offs — is settled *here*, batched into Codex user-input prompt, and recorded in `Decisions:`. A phase containing "decide later" is not ready. On a real architectural fork, give a recommendation with its trade-off; say if it is the kind of choice a judge panel would decide better, and let the user ask for one.

**Contract tests.** One more option, asked with the Decisions batch: author
the tests of EVERY phase now, while the whole design sits in one context —
into `.phased/active/<slug>/tests/phase-N/`, committed with the plan, each
phase's `Done:` opening with "the plan's tests for this phase, copied into
the test tree, pass". Recommend it on refactoring and other well-specified
work — behaviour that must survive is exactly what a test states best;
where a signature is not settled yet, author that test as a skeleton
(`wf:contract:` comment lines + red body) instead of guessing. The whole
contract — the two precisions, where the tests live, the child's read-only
rule, the integrity check at close — lives once in `contracts.md` → *Contract
tests*; writing them inside `.phased/` keeps this skill's own first rule
intact. Authoring them is plan-time work: derive each phase's tests from its
`Details:` and `Done:`, in the repo's own test style, and present them with
the plan.

**The consumer question.** When `.phased/roadmap.md` has unstarted
macro-phases — or the discussion names later work that will consume this
plan's output — ask it with the Decisions batch: *who consumes what this
workflow builds, and what will they require of it?* The answer becomes the
plan's `Must not break:` header lines, backed by skeleton contract tests
where a requirement can be stated as behaviour; "nobody yet" is written
down too. Field semantics live once in `contracts.md` → *Must not break:*.
On a roadmap carrying mini-scopes, the answer starts there, confirmed
rather than reconstructed: collect the lines of `Requires of earlier work`
from the later macros that touch this plan's output, **inherit the
contracts in transit across this macro** — produced by an earlier one,
consumed by a later one, they enter this plan's `Must not break:` too
(`contracts.md` → *Must not break:*, producer-to-consumer rule) — and take
the macro's own `Ends at:` as a planning constraint: the last phases must
land the system at that border.

**Sizing.** The boundary depends on the mode chosen in Step 2.

*Interactive plans — the boundary is **"something a human can look at exists"***. A phase ends where the user can open the thing and judge it, so phases come out **bigger** — as a consequence, not as a goal. The point is what it makes impossible: a phase cannot close on half a button, so no verification step can be a trivial "try this for me". The user's own example — customer and supplier master tables *with their UI* — is one phase here, not a model phase plus a UI phase.

*Autonomous plans — one concern, ~6-8 files, closed by a re-runnable `Done:`* (the stricter rules live in `<PLUGIN_ROOT>/refs/write-workflow-autonomous.md`).

Either way:
1. Too small to verify alone (a model half, a migration, a schema)? Merge it into the phase that makes it verifiable — a phase boundary the user cannot verify is a boundary in the wrong place.
2. **Split** — two concerns in one phase: just write more phases, no tag.
3. **`vast`** — one indivisible concern with a genuinely large surface (>~10 files). At execution a read-only fan-out maps it, so the file ceiling is lifted for it only.
4. **`ui`** — a phase whose deliverable is judged by eye: a page, a form, a dashboard. Interactive plans only (an autonomous run has nobody to approve a mockup). At execution the approval gate includes a rendered HTML mockup iterated with the user, and verification adds a browser pass plus a fidelity judge against that mockup (`contracts.md` → *Verification*). Tag it here so the executing chat knows before exploring.

The split-vs-`vast` call and the `ui` tag materially change execution — batch them into the Decisions questions. Phases always run in order, each in its own chat; there are no parallel or grouped phases.

**Verification fields.** `Done:` and `Verify:` are two audiences, and their contract lives once in `<PLUGIN_ROOT>/refs/contracts.md` → *Verification* — read it there rather than inferring it. When writing an interactive plan: give every phase a `Done:` the machine can re-run, and add `Verify:` steps only for what genuinely needs human eyes, each with its *when* (`now` / `deferred: needs Phase M`). What a browser agent could assert belongs in `Done:`, never on the human's list. On a `ui` phase the `Verify:` list is authored COMPLETE here — the checks the human will run at that phase are pre-established now, and execution may add but never drop or reword them (`contracts.md` → *Verification*, authored checks are foreman-owned).

**Run hint.** Every phase carries a `Run: <model> / <effort>` line: advice for the human who opens that chat, never something the plan enforces — the model is picked when the session starts, before any skill has read the plan. That is also why it is written down instead of only said here: the chat that needs it is opened days later, and by then this conversation is gone.

- **Effort** — start low and climb only for a reason. A phase whose `Decisions:` and `Pattern:` are settled is where high effort buys least: it gets spent re-exploring what planning already decided. `low` mechanical, `medium` the standard phase, `high` where real design judgment survives inside the phase, `xhigh` a wide multi-file surface, `max` practically never (overthinking, diminishing returns). Levels copied from an older plan rarely transfer — decide them here, for this plan.
- **Model label** — write `opus` by default and `fable` only where inventive work survives *after* the approval gate: architecture to invent, an unknown surface, or no obvious decomposition. These are portable protocol labels so the same plan runs in Claude and Codex. Codex maps both to `gpt-5.6-sol`, with the listed effort controlling depth. Never author `sonnet`; it is accepted only when resuming a legacy Claude plan.

**Present the plan**, each phase with its `Run:` line, and iterate until the user approves.

**Close the presentation with the branch line and the gate line** (`common.md` → *The gate line*):

> Branch: \<what will happen\>   (say so if you would rather have it otherwise)
> **Proceed?** On your ok, I create the branch and write `.phased/active/<slug>/plan.md`.

The branch line is pre-filled per Step 4 and flippable.

## Step 4: Open the branch

Only after approval, and before writing anything.

Derive the slug from the objective: kebab-case, strip accents, ≤50 chars, a leading issue number kept as prefix (`123-fix-login`).

**On the base branch** → `git switch -c wf/<slug>`, no question asked.

**On a feature branch** → the default is to **adopt it** as the workflow branch: `.phased/` goes there, no new branch, and `Parent:` is that branch's own base. You created that branch on purpose; nesting another inside it buys nothing. The alternative, offered in the branch line above, is `wf/<slug>` off it — take it when the workflow is a distinct chunk the user may want to merge or drop on its own; the current branch then becomes the `Parent:`.

**No worktree here.** Planning creates the branch and the plan, nothing else: the workspace belongs to execution. `/run-workflow` attaches or creates the worktree itself when the run needs one, and `/finalize-workflow` removes it — the user never manages it.

## Step 5: Write it

`.phased/active/` already occupied → stop and say so: one branch, one plan. Otherwise create `.phased/active/<slug>/` holding `plan.md`, an empty `notes.md`, and `foreman.json` — **this chat takes command of the workflow it is creating**, per `foreman.md` → *The foreman* (write the file — it rides Step 6's plan commit, no second one; this chat titles itself there too, and the closing message states it).

```
# Context: <branch-name>
Parent: <parent-branch> | Issue: #<number> (if present)
Mode: interactive
Must not break: <one line per contract owned by later work — contracts.md → *Must not break:*; omit only when no roadmap and no known consumer>

## Objective
[2-3 sentences]

## Work Plan
- [ ] **Phase 1**: <concise title>
  - Run: opus / medium
  - Pattern: `path/to/example.py:func` (or `library-standard` / `new-pattern`)
  - Files: <involved files, if known>
  - Decisions: <choices already settled — omit if none>
  - Details: <what to do concretely>
- [ ] **Phase 2**: table foo with its TH UI (model + webpage)  `ui`
  - Run: opus / low
  - Files: packages/foo/model/foo.py, packages/foo/webpages/foo.py
  - Details: table + columns + relations, then TableHandler view + form.
  - Done: end-to-end test — create a row via the form, assert it persists and reloads in the grid
  - Verify: now — the form reads well: field order, labels, nothing cramped
  - Verify: deferred: needs Phase 3 — the renamed amount column still lines up in the grid
- [ ] **Phase 3**: rename legacyAmount → amount across the web layer  `vast`
  - Run: opus / xhigh
  - Files: discovery rule — all references to `legacyAmount` under packages/foo/ and gnr/web/
  - Details: rename + deprecated alias.

## Notes
[Attention points, dependencies, breaking changes]
```

Phases run strictly in order: a phase starts only when every phase above it is `[x]`.

Write no `## Suggested execution config` table on an interactive plan: nothing reads one here, and the validator warns about it. The per-phase `Run:` line is the interactive equivalent — a suggestion in the plan body, `opus`|`fable` only, read by `/execute-phase` to scale its exploration and reported by `/resume-workflow` before the next chat is opened.

## Step 6: Commit and close

The plan is the branch's first commit — everything after it is the workflow:

```bash
git add .phased && git commit -m "wf: plan for <slug>"
```

Verify it is not empty (`git show --stat HEAD`). An empty commit means `.phased/` is excluded by a `.gitignore` — say so and stop rather than working around it; the whole chain depends on the plan being tracked.

```
Plan written to .phased/active/<slug>/plan.md (<N> phases), committed on <branch>.
This chat is the foreman, now titled `wf:<slug>:foreman` — it is the address phase chats report to.
To run it, launch /execute-phase in a new chat — this one stays the board.
Phase 1 — suggested: <model>, effort <effort>.
```

Where the title could not be set — the tool is absent — that line becomes the ask instead, per `foreman.md` → *The foreman*, take-command step 3.

The last line repeats Phase 1's `Run:` hint, because the model and the effort are chosen when that session starts — reading it afterwards is too late.

**Then draw the board**, as specified in `<PLUGIN_ROOT>/refs/board.md` — the same strip `/resume-workflow` draws, one source for both. Here every row is `[ ]` and Phase 1 is the emphasised one: the plan was just written, there is no history yet.

**Only after the commit, never during Step 3's presentation.** The plan is iterated in prose, and a board naming a branch that does not exist yet is a trap. On an autonomous plan, no board at all.

(Autonomous plans use the closing message in the autonomous reference file.)
