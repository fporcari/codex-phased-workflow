---
name: resume-workflow
description: Locate the active phased workflow and report where it stands, then name the skill that takes it forward. The entry point of the phased-workflow plugin, and the only skill in it the agent may reach on its own. Use when the user asks where the work stands, what the next phase is, whether a workflow is running, why a phase is stuck or failed, how to resume after an interrupted session, or mentions `.phased/` or a `wf/` branch.
---

# Resume Workflow

Supervision and resume view of the work plan. **Read-only on source code** — the only files this command may modify are the plan, `notes.md` and `foreman.json`; plan and notes only on an approved edit; each edit gets its own `wf:` commit.

A healthy workflow is a valid reason to run this: when nothing is broken it early-exits with the state report and nothing to resume.

**Shared conventions:** read `<PLUGIN_ROOT>/refs/common.md` once at start. Read
`<PLUGIN_ROOT>/refs/foreman.md` at Step 1b only after the plan proves relayed or
legacy; an in-chat workflow has no relay to take command of.

## The map

Every other skill in this plugin is **user-invoked**: only the user typing its name reaches it. Naming the right one is part of this skill's job — in Step 3's *Next step*, and whenever the user asks what to run.

| Skill | Reach for it when |
|---|---|
| `/scope-workflow` | the work is still vague — settle the decisions before planning |
| `/write-workflow` | there is no plan yet, and the work was just discussed |
| `/import-workflow` | a plan or handoff document already exists outside `.phased/` |
| `/issue` | the work starts from a GitHub issue (analysis only) |
| `/execute-phase` | run the next phase with an approval gate — a new task on relayed/legacy, this conversation on in-chat |
| `/run-workflow` | run every remaining phase unattended (`Mode: autonomous` plans) |
| `/repair-phase` | a phase is `[!]` and needs fresh eyes |
| `/doctor` | the work and the plan may have drifted apart — coherence audit, contract-test integrity, blind retro-fit of missing tests |
| `/quality-check` | every phase is `[x]` — QA pass, naming review, whole-diff review; stamps the plan |
| `/finalize-workflow` | quality check stamped — lessons, archive, consolidate into one commit |
| `/dashboard` | optional authenticated local plan/roadmap/log view; this textual report remains the complete fallback |
| `/pull-request` | the branch is ready to open a PR |

## Step 1: Find the plan and the base

```bash
python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --resolve
python3 "<PLUGIN_ROOT>/scripts/next-phase.py"
git log -1 --diff-filter=A --format=%H -- <plan path>
```

No active plan → stop: `/write-workflow` creates one, `/import-workflow` adapts an older one. Since the plan lives on the workflow branch, check `git branch --show-current` before concluding there is no work — and check `--plans` first: the workflow may live in another checkout or on a branch with no checkout at all (`common.md` → *Plan location*); anchor every command to the plan's root with `git -C`.

The third command gives `BASE`, the commit that added the plan. Everything after it is this workflow; everything before it is not — on an adopted branch that distinction is the whole point.

## Step 1b: The foreman

On `Channel: in-chat` there is no relay and nothing to take command of. The
plan's decisions belong to the user in this conversation; skip to Step 2 and
report the channel.

On relayed and legacy plans, read `.phased/active/<slug>/foreman.json` (protocol, file format and
take-command mechanics live once in `foreman.md` → *The foreman*):

- **Absent** → **assume command, without asking**: the normal state of every
  workflow that predates the protocol, and a workflow being resumed wants a
  foreman. Take command per `foreman.md` — write the file, ONE `wf: foreman —
  takes command` commit, title this chat.
- **Present, and no other Codex task bears the title** (use the available task
  listing tool; without one, report liveness as unknown) → the
  title is unclaimed: either it is this very chat (fine) or the old foreman
  is dead or renamed. Either way, claim it — same take-command step, which is
  **idempotent by content** (`foreman.md`): the file already carries this
  exact title, so nothing is rewritten and no commit is made; at most, the
  chat re-applies the title to itself — the call returns the one it
  replaced, which is also how a chat learns it had drifted off it.
- **Present, another task bears the title** → do not depose on a status
  query. Report it (Step 3 gets a *Foreman* line: who, since when).
  Offer the takeover through the Step 3 Codex user-input prompt only when something
  actually needs action here, or the user says they want this chat in
  charge. On yes: depose per `foreman.md` — best-effort farewell message and
  retitle of the old session — then take command (its own commit). The old
  chat may be long dead; nothing in this step is allowed to block on it.

## Step 2: Attribute the work

Each completed phase committed its own work, so attribution is **exact — never infer it**:

```bash
git log --oneline "$BASE"..HEAD
git show --stat <phase commit>
```

For each `[x]` phase, compare its commit's files against its own `> Files:` note. For each pending phase, there is simply no commit yet.

Then look at `git status --short`. **A clean tree is the normal state.** Uncommitted changes are legitimate only while a phase is `[>]` — anything else is a finding, not context: a session that died before committing, or hand edits nobody recorded.

Two distinct kinds of drift, and they mean different things:

1. **Unlisted files** — inside a phase's commit but absent from its `> Files:`. The work landed but the record is wrong, which silently breaks later baseline attribution and `/repair-phase`.
2. **Uncommitted leftovers** — in the tree, in no commit, with no `[>]` phase to explain them.

Flag a phase as **oversized** when its commit spans more than ~10 files, covers unrelated areas (model + UI + tests for different features), or is too large to review as one commit. **Exception:** a `vast` phase is intentionally whole — that size is by design, never propose re-phasing it for size alone. For a pending phase the same judgment is a projection from its `Files:`, not a measurement; say which one you are making.
For a phase carrying `> Batches:`, apply that judgment to each batch's partial
commit, not the phase total: an oversized batch is a finding; a large phase
made of reviewable batches is not.

## Step 3: Report

1. **Plan state** — every phase with its marker. For `[>]`, show the timestamp and flag anything older than 2h: *"running for over 2 hours — the previous chat may have ended"* — unless it carries a `> Testing:` note, which means it is waiting for the user's checks (`contracts.md` → *Verification*). Read `log/phase-N.txt` and `log/repair-N.txt` beside the plan when present. Also resolve `T=$(python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --transport)` and inspect `$T-run.log`, `$T-phase-N.log`, or `$T-repair-N.log` when a worker was interrupted before its outcome commit; those external files are diagnostic only, while committed plan state is authoritative. A `[!]` phase carrying `> Repair started:` is under repair, not immediately available for a second repair. Judge staleness from the timestamp, log, process state when locally observable, and the user's account — never from a product-specific session id. Close with one **Channel** line: on in-chat say the work continues here and name no foreman; on relayed/legacy name the foreman host and live message channel. The committed plan remains authoritative.
2. **Workflow commits** — `git log --oneline $BASE..HEAD`, one line per phase, with the files each touched.
3. **Coverage** — per `[x]` phase: does its commit match its `> Files:`? Per pending phase: still to do.
4. **Drift** — the two kinds above, kept apart.
5. **Oversized phases** — for each, what its commit already contains, what remains, and a proposed split into sub-phases.
6. **Next step** — continue (`/execute-phase` or `/run-workflow`), repair (`/repair-phase` on a `[!]`), re-phase, add phases for work that surfaced (Step 4 — the answer when a phase passed and is still wrong), finalize, clean up drift — or, when what smells is incoherence between the landed work and the pending phases' premises rather than record drift, `/doctor` for the verdict instead of the suspicion. When it is `/execute-phase`, quote the next phase's `Run: <model> / <effort>` hint alongside it (older plan without one → `opus` / `high`). When it is a fresh successor foreman task, quote `gpt-5.6-sol` / `high` from `foreman.md`. These settings are chosen when the task opens, so the hint is useful only beforehand.

**The board.** On a `Mode: interactive` plan, render points 1 and 6 as the strip specified in `<PLUGIN_ROOT>/refs/board.md` — read it there rather than inferring the shape; it is the single source, shared with `/write-workflow`. Points 3, 4 and 5 stay prose in the reply: they are judgments, and a strip argues badly. On an autonomous plan, no board at all. No `visualize` server → the same rows as a plain list, per the ref.

**Healthy plan → stop here.** No `[!]`/`[~]`, no stale `[>]`, no drift: the report ends with the next step and nothing to resume — no questions asked.

Something needs action → propose it via Codex user-input prompt: reset a stale `[>]` to `[ ]`, apply a re-phasing, or hand the `[!]` to `/repair-phase` — the last one only when no live repair holds it (point 1). A stale `[>]` that point 1 traced to a killed unattended run gets the reset and the relaunch as **one option** — the reset alone would leave the user without the path back.

## Step 4: Apply approved plan edits (only if approved)

- **Stale `[>]` reset** — back to `[ ]` with `> Execution interrupted, phase available for retry`.
- **Re-phasing** — replace the oversized phase with the split sub-phases, marking the completed ones `[x]` and leaving the rest `[ ]`.
- **A phase for the remainder of one closed short** — announced by the relayed message or said at the in-chat gate. The phase that overran is evidence the sizing was wrong, and sizing belongs to whoever owns the plan. Write what remains from the record in `notes.md`.
- **Re-planning after a rejected result** — the answer to *"this phase passed and is still wrong"*, and the case the `phase N closed, result rejected` message announces. It is not only an append: the phases that have not run were written for the design just rejected, so they are re-planned too — rewritten where they no longer fit, dropped where they no longer apply — while the closed phase keeps its `[x]` and its `> Review:` verdict. A phase whose `Done:` went green cannot be repaired into a different design: `/repair-phase` only takes a `[!]`, and its job is to make a `Done:` green again, not to reopen a decomposition. What the plan needs is one or more **new phases**, written from the user's own account of the problem (the user's own account of it, here in this chat).

  **In the tail, never in the middle**, even when the work logically belongs at Phase 2. Phase numbers must be contiguous ascending from 1, so an insertion renumbers everything after it — while the commits already made say `wf(phase 3)`, `wf(phase 4)` with the old numbers, and the correspondence between the plan and the history breaks silently. Execution order stays the numeric order; the new phase's text says what it remedies.

  **A closed phase is not reopened.** Its `[x]` and its `> Files:` are the record of what happened and stay as they are; what it lacks becomes new work with its own phase and its own commit. Write the new phases to the same bar as `/write-workflow` — `Files:`, `Details:`, a re-runnable `Done:`, a `Pattern:` where the code is non-trivial, and a `Run:` line — and present them for approval before writing.

- **After a quality check** — accept only what `/quality-check` → *The final
  touch* sends here: unresolved design or a surface the plan never built, such
  as a table, page, or migration. Settle the remaining decisions before
  authoring ONE phase for all such findings together, to the same bar above.
  Corrections on a decided design stay in the final touch; never create a
  phase per review finding or reopen a closed phase.

- **Actualising an older plan** — a plan written before a format existed keeps running on defaults, and defaults are invisible. Offer to write them down, on pending phases only (a `[x]` phase is a record of what happened; leave it alone): the `Mode:` header when absent, and on an interactive plan the per-phase `Run: <model> / <effort>` line. Decide each one with `/write-workflow`'s own criteria — that skill is the single source, do not restate them here — and present the values before writing them.

  **Fill in defaults, never gaps.** A missing `Run:` is a default made explicit (`opus` / `high`), which is why proposing it is legitimate. A missing `Done:`, `Pattern:` or `Decisions:` is something its author never settled: report it and stop there, exactly as `/import-workflow` Step 3 does. Inventing a plausible `Done:` makes an open question look closed, and nobody checks it twice.

The plan is a tracked file, so each edit needs its own commit — it belongs to no phase:

```bash
git add .phased && git commit -q -m "wf: <what changed>"
```

Leaving it uncommitted would break the clean-tree invariant the next phase's baseline check relies on.

After any such commit, send the foreman one `plan changed` message on relayed,
best-effort. On in-chat, report it to the user here. The plan commit is the
authoritative record on both roads.
