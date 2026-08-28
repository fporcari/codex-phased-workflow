---
name: execute-phase
description: Execute the next phase from the active work plan
---

# Execute Phase

Execute the next uncompleted phase. **This is the heart of interactive mode**, not a lesser `/run-workflow`: ONE approval gate up front (plan + all questions batched), then execution — and a real doubt is asked **live, in this chat**, because here there is somebody who can answer. One class of doubt is routed first: an ambiguity in the *plan itself* goes to the foreman (`foreman.md` → *The foreman*, `clarify?`) before it reaches the user — the plan's author answers it better — and the user here confirms what the foreman decided.

Two kinds of interruption, and only one is legitimate: a question that needs a **decision** — ask it, take the answer, resume. Asking the user to **try something trivial** mid-phase is not a question, it is the symptom of a phase that was cut too small; the cure is sizing, and manual checks belong in `Verify:` at the end. Execution stays on `gpt-5.6-sol`; the plan's portable `opus`/`fable` label changes guidance, never lowers model quality.

**The phase's `Run: <model> / <effort>` line** is the plan's advice for this session, decided during planning. Neither value can be changed from inside the session, so read it rather than reconsider it:

- **Effort** governs how wide you look before the gate — the scale is in Step 3. Missing line → treat as `high`.
- **`fable`** is the portable label for a phase that kept inventive work of its own. On Codex it still runs on Sol, normally with `xhigh` or `max` effort. Read this file as a contract on the *output* — the approval gate, one phase, one commit, the outcome format — not as a procedure to re-derive. The settled `Decisions:` are input.

**Shared conventions:** read `<PLUGIN_ROOT>/refs/common.md`, `<PLUGIN_ROOT>/refs/contracts.md` and `<PLUGIN_ROOT>/refs/foreman.md` once at start — core conventions, the contract layer (Done:/Verify:, contract tests), the foreman protocol this skill routes clarify? through. **Shared mechanics:** `<PLUGIN_ROOT>/refs/phase-execution.md` — selection, implementation discipline, outcome formats, the phase commit; `/execute-phase-agent` is this same skill with the gate replaced by unattended constraints.

## Step 1: Find the plan and the phase

```bash
python3 "<PLUGIN_ROOT>/scripts/next-phase.py"
```

No active plan → stop and say so: `/write-workflow` creates one, `/import-workflow` adapts an older one. The plan lives on the workflow branch, so being on the wrong branch is the usual reason it is missing — check `git branch --show-current` before concluding there is no work. If the plan lives in another checkout (or the user means a different workflow), resolve via `--plans` and anchor every command to that plan's root — `common.md` → *Plan location*.

Act on `recommendation:` — `next: N` → proceed; `resume-candidate: N` → ask whether to take over a phase another chat left `[>]` — on yes, resume per the shared core (`refs/phase-execution.md` → *WIP checkpoints*): the `> WIP:` note and its `commit:` are the evidence, the diff decides what is already done; `attention: ...` → surface the `[!]`/`[~]` phases, they block what follows; `done` → suggest `/quality-check`, then `/finalize-workflow`; `blocked: ...` → report and stop — except a `blocked:` naming a phase that awaits the human's checks, which is this skill's own gate coming back: present those checks and, on the user's ok, close the phase through `close-phase` (`refs/phase-execution.md` → *Awaiting the human's checks*).

Mark the phase `[>]` with `> In execution since <ISO timestamp>`.

**Title this chat** `wf:<slug>:phase-N — <phase title>`, with `set_session_title` on `session_id: "self"` (`foreman.md` → *The foreman*). Best-effort, like everything on that channel: no tool, no title, no consequence — nothing addresses a phase chat, the title is there so the session list reads as a workflow.

## Step 2: `vast` phases only — read-only fan-out

Skip unless the phase is tagged `vast`. Partition its `Files:` list (or run its
discovery rule) into at most four slices and dispatch one read-only Explore
subagent per slice. Each returns only one line per site as
`<path>:<line> — <change> — <pattern>`, or exactly `NO SITES`. Build the Step 3
gate from those lines instead of reading the whole surface yourself. `NO SITES`
for a path the plan names is a plan ambiguity routed as `clarify?`, not an empty
success. **This fan-out writes nothing.**

## Step 3: The approval gate (the only planned interruption)

Read the phase's `Pattern:` example first — don't re-explore what planning already recorded.

**Scale the exploration to the phase's `Run:` effort** (missing → `high`): `low` only the listed `Files:`; `medium` + their immediate references; `high` up to 2 read-only Explore subagents and the surrounding package; `xhigh`/`max` up to 3 plus a cross-package consistency pass. Same scale as `/execute-phase-agent` Step 2 — what differs is only that here it ends in a question instead of a decision.

**The gate carries a compatibility line.** Before presenting, read the
pending phases — their `Files:`, `Details:`, and contract tests where the
plan carries them (`contracts.md` → *Contract tests*) — plus the plan's
`Must not break:` header and, when `.phased/roadmap.md` exists, its
remaining macro-phases (`contracts.md` → *Must not break:*): premises of the
same rank. State in ONE line what this phase's approach leaves standing for
them: the data shape a later phase builds on, the file a later `Files:`
names, the behaviour a later test asserts. A conflict found here is a plan ambiguity: it goes up as `clarify?`
(below) before any approval is asked — approving an approach nobody checked
against the plan's own future is how a phase betrays it.

**Plan ambiguities go up before the gate.** An open question about the plan itself — what the objective means, what `Done:` covers, a `Files:`/`Pattern:` that doesn't match the code — is not the user's first: send it to the foreman per `foreman.md` → *The foreman* (`clarify?` — precondition, reply paths, one-round cap and timeout all live there) and fold the answer into the gate as a settled decision, presented for confirmation. What the foreman sent back as the user's (`ask-user`), what it never answered, and every question outside that scope — local technical choices, the approval itself — joins the batch as today.

Present in ONE message: what the phase will do, the files to create/modify/delete with their key changes, and **every open question batched** (anything `Decisions:`/`Details:` leave unsettled). Then ONE Codex user-input prompt carrying approval plus those questions.

**`ui` phases — the mockup gate.** Before asking for approval, build a
throwaway **static HTML mockup** of what the phase will produce — look and
layout only, plausible fake data, no framework — and show it with Codex's file
or browser panel. This gate may
loop: mockup → feedback → mockup, as long as it takes — aesthetics is all
decision, and this is the one interruption that is legitimate by design. A
text description of a UI is never a substitute: the stated purpose of the
tag is judging the *look*. The authored `Verify:` checks stay as planned —
the mockup loop refines the look, never the checklist: a check that no
longer fits goes through the foreman (`contracts.md` → *Verification*, authored
checks are foreman-owned). Approval of the phase IS approval of the mockup:
save the approved version as `.phased/active/<slug>/mockups/phase-N.html` —
the phase's visual contract (`contracts.md` → *Verification*), the reference
for Step 5's judge, committed with the phase.

**No file may be edited before approval. After approval, run to completion.**

## Step 4: Execute

Implement only this phase. When a coherent, demonstrable sub-result lands and substantial work remains, checkpoint it per the shared core (*WIP checkpoints*) — the cost is a `partial` commit the squash will drop, the payoff is that a dying session loses minutes, not the phase. If something the plan doesn't cover comes up and a wrong default would be costly, ask ONE batched question and record the answer in Notes; otherwise take the conservative option and note it. Same routing mid-phase as at the gate: a blocker that is a plan ambiguity goes to the foreman first (`clarify?`, per `foreman.md` → *The foreman*), and the ONE question to the user then presents the foreman's decision for confirmation — a rejection travels back up once, per the protocol.

**The stop-loss.** Struggle is itself a routing signal, per the same section of `foreman.md`: the second failed attempt at one obstacle, or an exchange with the user that has turned from deciding into diagnosing why the approach does not work, stops the work — checkpoint (*WIP checkpoints*), then the suspected presupposition goes up as a `clarify?`; never a third attempt, never another diagnostic message here. The answer decides between the two known exits: a defect leaves the chat (`refs/phase-execution.md` → *Handing a defect to repair*), a wrong plan follows the rejection road.

**When an answer changes the plan itself** — a phase reshaped, a decision reversed, scope moved — the plan edit gets committed as usual, and the foreman chat is told: one `plan changed at phase N` message per the protocol in `foreman.md` → *The foreman*, best-effort. The father must not discover a deviation at finalize.

## Step 5: Verify

- Phases with contract tests start from them: copied verbatim and green per the shared core (`refs/phase-execution.md` → *Implement*); edits to their contract only ever arrive as a foreman `clarify:` decision.
- Testable logic → write/update tests in the repo's existing style, run the suite. A failure that doesn't touch this phase's `Files:` is probably pre-existing: check before absorbing it, and tell the user instead. Fix and re-run, ONE retry; still red → `[!]`.
- Purely UI/declarative → what a browser agent can assert still belongs to the machine: the `ui-test` skill (Skill tool), where installed, drives a real browser (the flow works, the record persists, the grid reloads). Run it, or say why you didn't — and when it is not installed, apply the declared fallback in `<PLUGIN_ROOT>/refs/contracts.md` → *Verification*: those checks go to the human as `Verify: now` steps, said out loud. **Login-gated target → the human performs the login, always** — first establish whether there is one, then hand over (`contracts.md` → *Verification*).
- `ui`-tagged → the browser pass above takes `mockups/phase-N.html` as its reference and must return **screenshots of the key states** (saved next to the mockup). Load `<PLUGIN_ROOT>/judges/ui-judge.md` and give that shipped prompt to ONE fresh read-only Codex subagent, with the mockup path, screenshot paths, and a one-line phase brief. Never invoke a bare judge name: Codex packages these as prompt files, not discoverable named agents. Findings: **MECHANICAL** (element missing or plainly wrong vs the mockup) → fix now, re-run the check; **JUDGMENT** (a deviation that may be legitimate, an aesthetic call) → record as `> Review:`, never block. No browser surface available → the judge is skipped too; say so and hand the comparison to the human as a `Verify: now` step with both paths.
- `vast` → optionally re-run the read-only fan-out to confirm no site was missed, then test as usual.

What is left after that — aesthetics, "is this interaction right?", UX ambiguity — is the human's, and only that. Record it as `> Verify:` notes, each with its *when*, **starting from the phase's own authored `Verify:` fields** and adding what execution surfaced, per `<PLUGIN_ROOT>/refs/contracts.md` → *Verification*: `now` steps go in the phase summary, `deferred: needs Phase M` steps are **also appended to `verify.md`** in the plan directory, under a `## Phase N` heading, so `/quality-check` can present them as one QA pass. Never use `Verify:` to offload a check the tests could have made.

## Step 6: Hand over for testing, then close

**A `Verify: now` step left to the human holds the phase open.** Step 5's split already decided this: what an agent could assert, an agent asserted; what remains is what only you can judge. Closing before you have judged it books a result nobody has looked at — and on a `ui` phase whose browser pass could not run, that is the whole result. So, when at least one `now` check is yours:

1. Commit the work and write the `> Testing:` note, per the shared core (`refs/phase-execution.md` → *Awaiting the human's checks*). The phase stays `[>]`.
2. Present the checks — each with what to do and what should happen — and **stop there**. No `close-phase`, no foreman message: nothing has closed.
3. What the checks turn up is ordinary work on the open phase: fix, commit the same way, present again — unless the verdict is that the phase is wrong at the root, which is not this phase's to repair and never `[!]`: the shared core's third exit applies (`common.md` → *Failure and repair notes*).
4. The user's ok is the trigger for the close below. A new chat resuming here gets the same gate back from `next-phase.py`, as `blocked:` (Step 1).

**Nothing left for the human** — the suite covered it — closes straight away, as before.

A phase that reached its `Done:` closes through the `close-phase` skill (Skill tool): naming review of the methods this phase marked (`contracts.md` → *New-method markers and minimality* — accept-all is one keypress), the Done gate re-run, the `[x]` record with the Step 5 `> Verify:` notes, the ONE phase commit, the foreman message and the desktop notification — all per the shared cores it cites. Hand it the outcome material (touched files, `> Review:`/`> Verify:` notes); do not restate its mechanics here. Its closing line names the next step; add beside it what it does not carry — what was done, test results, the manual checks left to the user.

A phase ending `[!]` or `[~]` never routes through `close-phase`: record and commit it directly, exactly as the shared core (`refs/phase-execution.md`) specifies, and send the foreman message per `foreman.md` → *The foreman*, best-effort.

## Handing over

A long phase outlives its chat. **Ask first whether it has a seam**, because a phase that does not fit one context was sized wrong and there are two answers to that, not one (`refs/phase-execution.md` → *When the phase outgrows its chat*): a coherent green sub-result **closes short** — the phase ends properly and the foreman grows a phase for the remainder — while work in mid-air hands over. Closing short is the cleaner one; propose it whenever the seam is there.

The handover itself is a move the user can call at any time — *"pass the baton"*, no reason needed — not only a reaction to a full context. Offer it too, since the user strongly dislikes compaction: when the phase isn't done and the context is filling (or it already compacted once), *"⚠️ The context is filling up. Close this phase on what is done, or hand over to a new chat?"*

Handing over is three things, in order:

1. **Checkpoint** exactly as the shared core (`refs/phase-execution.md` → *WIP checkpoints*) specifies — `partial` commit and structured `> WIP:` note together, never one without the other.
2. **Write down what four keys cannot hold**: decisions taken and why, roads tried that do not work, what the next chat must not redo — into `notes.md` under the phase's `## Phase N` heading (`foreman.md` → *The foreman*, per-phase rationale), committed with the checkpoint. This is the part that dies with the chat if nobody writes it.
3. **Stop.** Say to open a new chat on `/wf:execute-phase`, and touch nothing further: from here the working tree belongs to whoever picks the phase up.

The arriving chat finds the phase `[>]`, and may reach back to this one while it is alive — the shared core's *Resuming a `[>]` phase* says how, and answering that message is the last thing this chat does.

## Rules

- NEVER edit before the Step 3 approval; the `vast` fan-out never bypasses it
- ONE phase per invocation; no out-of-scope refactoring
- After approval, no further questions except the Step 4 blocker policy
- ONE phase commit per phase, at Step 6 — WIP checkpoints (shared core) are `partial` commits, not phase commits
- If the session dies with the plan still writable and NO checkpoint exists, reset `[>]` to `[ ]` with `> Execution interrupted, phase available for retry` — and commit that reset as `wf: reset phase N` (the plan is tracked). With a checkpoint, leave `[>]` and its `> WIP:` note in place: they are the handoff
