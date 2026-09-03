---
name: quality-check
description: Quality check of the finished workflow — QA pass with the user, naming review, scope coherence, pre-commit review at chosen depth; stamps the plan for /finalize-workflow
---

# Quality Check

The quality half of closing a workflow: verify the plan is complete, put the QA checks in the user's hands, review the whole diff at the depth the user chooses, and stamp the plan with the outcome. `/finalize-workflow` reads the stamp and does the rest — lessons, archive, consolidation. **Never edit source code here** — findings get reported and delegated. Two declared exceptions: the bounded QA correction below and Step 3's naming review.

**Usage:** `/quality-check` — or `/quality-check light|extended|panel|none` to pre-answer Step 5's depth question (the argument is the user's call made early; everything else still runs).

**Shared conventions:** read `<PLUGIN_ROOT>/refs/common.md`, `<PLUGIN_ROOT>/refs/contracts.md` and `<PLUGIN_ROOT>/refs/foreman.md` once at start — core conventions, the contract layer (verify.md, markers, the stamp, Must not break:), the reporting register.

## Step 1: Find the plan and the base

```bash
python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --resolve
git branch --show-current
git worktree list --porcelain
```

No active plan → stop; the plan lives on the workflow branch, so check `git branch --show-current` before concluding there is nothing to check — and check `--plans` first: the workflow may live in another checkout (`common.md` → *Plan location*). When it does, every git command below runs `git -C <plan root>` and every path is anchored there.

Read the plan for `Parent:` and the phase states. **Resolve the parent ref**: `origin/<parent>` if `git rev-parse --verify` finds it, otherwise the local `<parent>`. Then:

```bash
BASE=$(git log -1 --diff-filter=A --format=%H -- <plan path>)   # the commit that ADDED the plan
```

`BASE` is the workflow's base: everything after it belongs to this run, everything before it does not. Consolidation shape (dedicated vs adopted branch) is `/finalize-workflow`'s concern, not this skill's.

## Step 2: Verify completion, and put the QA in the user's hands

All phases `[x]` → proceed. Otherwise report the incomplete ones (warn specifically that a `[>]` may be a dead session) and ask whether to check anyway (default: no).

**Present the QA pass.** Collect every `Verify:` step from the plan — authored fields and `> Verify:` notes alike — *and* the whole of `verify.md` if it exists (the deferred checks the executing skill dated to a later phase — `<PLUGIN_ROOT>/refs/contracts.md` → *Verification*). Deliver them as the **QA page** defined there: ONE checklist, grouped by phase, each check with the action to exercise and the result the user should see; a deferred step whose phase has since landed is now due. Phrase every item per `foreman.md` → *The reporting register*: the reader knows what the feature should do, not how the phases built it. Then ask whether they have been done — not as a blocker, but never silently skipped either: if the user says no, say plainly that the stamp will record those checks as declined. **Keep the answer**: whether a human exercises the result is one of the inputs Step 5's recommendation reads, and it lands in the stamp.

`verify.md` is the sibling of `review.md`, not a duplicate: this list is what the user must *exercise*, `review.md` is what they must *judge*. Present both.

**QA fixes.** A defect the user reports while exercising the list is fixed in
this task when it is a correction and not a design — the second foreman
exception (`foreman.md`). The boundary is whether the user's sentence is the
whole decision: a wrong term, label, field rule or default, or a missing
catalog entry qualifies. No new table, column, migration, engine change,
surface, or callable; touch only files earlier phases touched plus catalogs
that serve them, such as localization or CSS.

Apply the correction, run the suite and lint on the touched files, and make one
`wf: qa fix — <one line>` commit per QA round. Record each under `## QA fixes`
in `notes.md` as *what the user saw → what changed*. Beyond that boundary — a
decision the user has not supplied, a test nobody wrote, or a surface nobody
built — the correction is a phase appended through `/resume-workflow`; say
which road it took and why.

## Step 3: Naming review

Autonomous runs accumulate `wf:phase-N:new` markers on the callables the phases created — nobody could answer a naming question mid-run (`contracts.md` → *New-method markers and minimality*). Collect them over the union of every phase's `> Files:` (`grep -rn "wf:phase-[0-9]*:new" <files>`); none → skip in one line. Found → run `<PLUGIN_ROOT>/refs/naming-review.md` for the whole workflow: ONE map, accept-all as the recommended fast path, renames applied with their call sites, markers stripped, the narrow signal re-run when anything was renamed. Commit the result on the workflow branch:

```bash
git add -A && git commit -q -m "wf: method naming review"
```

**This is the one step of the quality check that edits source, by design** — the edits are the user's naming decisions plus marker removal, and the commit lands before the reviews so what gets reviewed is what will ship. The ref's sweep is blocking: a marker that survives here reaches the parent branch.

## Step 4: Review the scope

No staging heuristics and no guessing: the workflow is exactly
`git log --oneline "$BASE"..HEAD` — the plan commit plus, per phase, one phase
commit and any partial commits that preceded it. Group the log by the
`wf(phase N):` prefix, name each phase's partials, then show
`git diff --stat "$BASE"..HEAD`.

The tree must be clean. If `git status --short` shows anything, a phase closed without committing or someone edited by hand — report it and ask whether it belongs to the workflow before going on; do not sweep it in silently.

**On a programme (`.phased/roadmap.md` exists): the roadmap check.** Compare
what this macro actually built — the diff above, read against the plan's
`Must not break:` lines — with the remaining macro-phases' mini-scopes:
every shape a later macro would have to undo or work around is a finding
(`contracts.md` → *Must not break:*). Where the roadmap declares an `Ends at:`
for this macro, compare it with the state actually delivered — a leg about
to close in Puglia is caught at the close of the leg, not at the departure
of the next. Contracts in transit across this macro — produced by an
earlier one, consumed by a later one — are checked the same way: lost
luggage is a finding. This is the last cheap moment to act — the next macro is
planned against this commit. Findings feed Step 5's
review as explicit focus points and the stamp; deep measurement
(retro-fitted contract tests against the landed code) belongs to `/doctor`,
not here.

## Step 5: Pre-commit review

**When the plan lives in another checkout (its own worktree), or the cwd is outside the plan's root**, do not review in-session: silently run the shipped verify agent in a clean sub-session at the plan's root —

```bash
bash "<PLUGIN_ROOT>/scripts/agent-session.sh" quality-check-agent
```

— and read its report (stdout, teed to the plan's `log/quality-check-agent.txt`). Its prompt ships in the plugin, not composed here: that is what keeps the review independent. Treat its FINDINGS exactly like the in-session review's below, and its VERIFY-NOTES as Step 2's `> Verify:` collection. The agent never touches history; every decision stays here, with the user.

**Otherwise** (the plan is in this root, no worktree of its own), the review runs in-session via the built-in `code-review` skill (Skill tool) — never with `--fix` — and its depth is the user's call, not a guess (an argument on the invocation IS that call, already made). Ask ONE `Codex user-input prompt` — **Extended** / **Light** / **None** — and compute the recommended option from what this check already knows:

- **The QA pass exercises the deliverable** (Step 2's checks cover what the workflow built, and the user does them — a human eye lands on the result) → recommend **Light**. Every phase was already verified in isolation — in interactive runs by the user as each diff landed — so what nobody has seen is the diff as a whole. Light hunts exactly that residue and nothing else: effort `low`, scoped to **cross-phase issues only** — one phase breaking another's assumption, helpers duplicated by sessions unaware of each other, naming or pattern drift between phases.
- **Nothing a human will exercise** (internal work with no QA check on the deliverable, or the user declined the QA pass) → recommend **Extended**: this review is the only eye on the work. Whole diff, effort `medium` — `high` when the plan is `Mode: autonomous`.
- **`> Review:` notes on any phase, or a `## Run inspection` section in `notes.md`** → recommend **Extended** regardless (nobody read that code as it landed), effort `high`. Whatever the user picks, those notes are never dropped: Extended and Light take each one as an explicit focus point that must come out confirmed or explicitly dismissed; **None** presents them raw, for the user to judge alone.
- **None** is always on offer, its price stated in the option itself: nobody — the user included — has seen the whole diff at once, and the stamp will say so.

Extended also hunts cross-phase issues — Light's whole scope is a subset of Extended's.

**Large autonomous diffs:** add a fourth option, **Panel**, and recommend it in
place of Extended. Run four read-only dimensions in parallel — correctness,
cross-phase coherence, pattern conformance, test coverage — each returning
`MECHANICAL:`/`JUDGMENT:` findings, most severe first, or exactly
`NO FINDINGS`. Rank the union and take the four most severe; for each, run
three read-only skeptics in parallel, each returning exactly
`REFUTED: <why>` or `STANDS: <diff line proving it>`. Keep a finding on two of
three `STANDS`. Present findings beyond the fourth as unverified rather than
silently dropping them. The panel is 4 + 12 = **16 agents, fixed by
construction**, and never edits source.

The worktree path above is exempt from the question: the agent's prompt ships fixed in the plugin, and that is what keeps its review independent.

Findings → present them per `foreman.md` → *The reporting register*: the short
form (verdict line, one line per finding, its consequence for the user), passed
through the comprehension probe in `<PLUGIN_ROOT>/judges/report-judge.md` by
ONE fresh read-only Codex subagent. Never invoke a bare judge name: Codex
packages these as prompt files, not discoverable named agents. **Skip the probe
when the review returns no findings**: a clean verdict line has nothing to
misread. Deliver it as the register's report page where the session can render
one. Then ONE question — *"The pre-commit review found N problems. Fix them
first, or shall I stamp the check as it stands?"* (recommended: fix first) — on
the degraded chat-only path with the register's detail option folded in
(*Expand the details before deciding*), never as a second question. Fixing is
delegated, not done here; then re-run `/quality-check`.

This is the only whole-diff review on the "Merge into parent" and "Commit only" close-out paths — `/pull-request` adds a maintainer-grade one only on the PR path.

## Step 6: Stamp the plan

Record the outcome as the stamp `/finalize-workflow` reads (`contracts.md` → *The quality-check stamp*): append to `plan.md`, under a `## Quality check` heading (created on first use, one line appended per run — the last line governs):

```
> Quality check: <ISO timestamp> — commit <short HEAD hash> — review <extended|light|panel|none|agent>, QA <done|declined|none>, findings <N confirmed, M dismissed | none>
```

The hash is HEAD at stamp time — it is what lets finalize detect a stale check when commits land after it. Commit the stamp alone:

```bash
git add .phased && git commit -q -m "wf: quality check — <review depth>"
```

Close with the stamp line repeated in chat and the next step: *"Quality check stamped. Next: `/finalize-workflow` to consolidate and close the branch."*

## Rules

- **NO source code editing** — report findings and delegate fixes. The two exceptions, each in its own `wf:` commit, are Step 2's bounded QA corrections and Step 3's user-approved naming review
- A finding never blocks the stamp: the user decides to fix first or stamp as-is, and the stamp records what was found either way
- The stamp is written even when every answer was "no" — a declined QA and a `none` review are facts finalize must see, not omissions
