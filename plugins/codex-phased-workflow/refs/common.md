# Shared conventions — phased-workflow skills

Single source of truth for the core blocks every phased-workflow skill needs.
Skills point here instead of restating them. The doctrine is split by
consumer, so a session pays only for the layers its skill actually uses:

- `refs/common.md` (this file) — language, questions, the gate line, the plan
  directory and its location, the workflow branch, phase selection, failure
  and repair notes. Everyone reads it.
- `refs/contracts.md` — `Done:`/`Verify:`, contract tests, `Must not break:`,
  new-method markers. Planning, execution, close, doctor, quality check, finalize.
- `refs/foreman.md` — chat hierarchy and messaging, the wf-lessons ledger,
  the reporting register, notifications. The skills that supervise or report.

## Plugin root

`<PLUGIN_ROOT>` is a placeholder, not an environment variable. Resolve it from
the loaded skill path: it is the plugin directory containing `skills/`, `refs/`,
and `scripts/`. Replace the placeholder with that absolute path before running a
command. Never assume `CLAUDE_PLUGIN_ROOT` or another host-specific variable.

## Portable protocol

The committed `.phased/` tree is the interoperability boundary. Claude and
Codex must preserve the same directory layout, marker vocabulary, note fields,
branch shape, and phase commits. Runtime details never enter the protocol.

The model words `opus`, `fable`, and legacy `sonnet` are portable compatibility
labels, not commands to Codex. Codex maps all code-writing labels to
`gpt-5.6-sol`; `fable` means to retain or raise the listed reasoning effort.
Codex-authored plans keep these labels so Claude can resume them unchanged.

## Language

All written content (plans, phase notes, code, comments, commits, PRs,
issues) in English: the artifacts outlive the chat that produced them, and
what reads them next is usually another session.

**The conversation is in the user's language, never in one this plugin
picks.** Follow their own configuration — global instructions, output style,
or simply the language they are writing in. Every wording quoted below and in
the skills (gate lines, question options, closing messages, board labels) is
the English **canon of what to say**, not the language to say it in.

## Codex user-input prompt style

Use Codex's user-input tool for every structured question when it is available.
Otherwise ask one compact plain-language question. When a sensible
default exists, put the recommended option FIRST and append
"(Recommended)" to its label (the tool has no default-answer parameter).
For multiple-choice lists, one option per line, checkbox style.

## The gate line

A skill that stops to wait for the user must say so — an implicit wait
reads as hesitation, and only someone who knows the flow by heart guesses
that a reply is expected. Every presentation that ends in a wait closes
with ONE line, plain text, **never inside a code fence** (fenced text
reads as log output, not as a question addressed to the user):

> **Proceed?** On your ok, \<exactly what happens next\>.

The verb can change (*Confirm?* / *Launch?*), the shape cannot: a bold
one-word question, then what the ok unlocks. Multi-way choices go through
`Codex user-input prompt` instead (style above); the gate line is for the binary
"go" that unblocks the skill.

## Plan directory

Every workflow keeps its plan and its working notes in `.phased/`, at the
git repository root:

```
.phased/
  roadmap.md              # megaplans only — spans macro-phases
  active/<slug>/          # exactly one at a time
    plan.md               # the work plan
    notes.md              # free-form annotations + per-phase rationale
                          #   (## Phase N headings — see refs/foreman.md)
    foreman.json          # which chat commands it — Channel: relayed only
    verify.md             # human checks a phase deferred to a wider context
                          #   (see refs/contracts.md)
    mockups/phase-N.html  # ui-tagged phases — the approved visual contract
                          #   (refs/contracts.md; written by /execute-phase)
    tests/phase-N/        # contract tests authored at plan time — the
                          #   executable contract (refs/contracts.md)
    log/phase-N.txt       # stdout of each /run-workflow sub-session, committed
  done/<slug>/            # moved here by /finalize-workflow
```

The active plan is `<git root>/.phased/active/*/plan.md`, resolved by:

```bash
python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --resolve
```

`active/` holds exactly ONE plan directory — one branch, one plan, no
discovery. No match means there is no workflow in this repository: run
`/write-workflow`, or `/import-workflow` on an older plan. Several matches
are an anomaly to report to the user, never to guess at.

`.phased/` is committed on the workflow branch and never reaches the parent:
`/finalize-workflow` drops it from the squashed commit.

## Plan location — operating from anywhere

`--resolve` answers for the repository you are standing in. When it fails, or
the user means a different workflow, list every reachable plan instead:

```bash
python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --plans
```

One pipe-separated line per plan: location (a filesystem path, or
`branch:path` for a `wf/*` branch with no checkout), branch, checkout path
(`-` when none), phase counts, state. Several plans → ask the user which one,
never guess.

Once a plan outside the current root is chosen, anchor every command to ITS
root: `git -C <plan root>` for every git invocation, and every path (the plan
file, `log/`, `.phased/`) resolved against that root, never against the cwd.
A plan whose branch has no checkout cannot be operated on directly. Codex task
creation chooses the checkout or worktree before the skill starts; the plugin
never creates a nested host-specific worktree. Attach the branch to a Codex
task first, then operate from that task's root.

## Workflow branch

Every plan gets a branch, so that everything belonging to the run is
identifiable without heuristics.

- `/write-workflow` either creates `wf/<slug>` or adopts the branch you are
  already on (its own rules decide); either way `Parent:` in the plan records
  where the work goes back to.
- The plan is committed first, as `wf: plan for <slug>`.
- Each completed phase produces exactly ONE **phase commit**,
  `wf(phase N): <title>`, including the plan's own status update. Any number
  of `wf(phase N): partial — <sub-result>` commits may precede it — a
  checkpoint or a planned batch (`refs/phase-execution.md`) — and none of them
  closes anything: the phase commit is the one that carries `[x]`. A phase
  closing `[!]` commits too, as `wf(phase N): FAILED — <title>`: repair needs
  to see the failing code, and it needs to start from a clean tree.

**The base of the workflow is the commit that added the plan**, not the
branch point:

```bash
git log -1 --diff-filter=A --format=%H -- .phased/active/<slug>/plan.md
```

On a dedicated `wf/` branch the two coincide. On an adopted branch that
already carried commits, only this marker separates the workflow from the
work that preceded it, and `/finalize-workflow` consolidates from here.

**The plan is a tracked file**, so any skill that edits it dirties the tree.
Edits made outside a phase — a `/resume-workflow` re-phasing, a
`/repair-phase` note, hand annotations in `notes.md` — get their own
`wf: <what changed>` commit. Otherwise the "clean tree at phase start"
invariant that `/execute-phase-agent` relies on is false.

## Phase selection

The next eligible phase is computed deterministically by:

```bash
python3 "<PLUGIN_ROOT>/scripts/next-phase.py"
```

Called with no argument it resolves the active plan itself; pass a path to
point it at a specific one.

It prints a status table for all phases plus one `recommendation:` line
(`next: N` / `resume-candidate: N` / `attention: ...` / `done` /
`blocked: ...`). The semantics it implements — also the manual fallback if
the script is unavailable — are:

- `[x]` done → skip; `[!]` issue / `[~]` blocked → skip (the user must
  resolve them); like any non-completed phase, they block what follows.
- Phases run strictly in order: a `[ ]` phase is blocked while ANY
  preceding phase is not `[x]`.
- `[>]` phases are resume candidates only when nothing else is eligible;
  the script reports their age and whether a `> WIP:` note exists — what
  to do with that is the calling skill's decision.

## Failure and repair notes

**`[!]` is a machine verdict, never a human one.** A phase is `[!]` when its
`Done:` came back red and the bounded attempts are exhausted — that is what
`/repair-phase` reads, and its whole job is to make a `Done:` green again.

What the marker asserts is that **something is demonstrably broken**: a red
signal, or a defect that reproduces. A person is often the one who *saw* it,
and mid-phase it is `/repair-phase` that writes it down and marks the phase
`[!]` with their confirmation, for as long as the repair lasts — that is not a
human verdict, it is a human pointing at a machine-checkable fact. The verdict
a person cannot make is the other one, below: a phase whose result they judge
wrong with everything green.
**A person judging the result wrong is a different thing**, including when
they say the phase is broken: if the `Done:` passed, the machine has nothing
to repair. Marking it `[!]` sends the next session — or an unattended run,
which repairs without asking — at code whose tests are already green, to fix
a disagreement no test states.

So a rejected result never moves the marker. Its `Done:` passed, so the phase
is `[x]` — closed, and closed carrying a problem: the verdict stays on it as
`> Review:`, rejected options included, so nobody proposes them again. A phase
that already carries `> Issue:` / `> Attempted:` keeps them: they are the
record of what its own tests went through, not a claim about the design.

What changes is the **decomposition**, and not only by addition: the phases
that have not run yet were written for the design just rejected, so
`/resume-workflow` re-plans them — rewriting what no longer fits, adding what
is missing — from the person's own account of what went wrong. It owns that
edit and its commit.

`phase N closed short` is the same family: a phase that outgrew its chat
(`refs/phase-execution.md` → *When the phase outgrows its chat*) closes on
the sub-result it reached, and the remainder needs a phase the child does not
write — sizing belongs to the plan's author, not to the phase running, and a
phase that overran is evidence about the sizing.

**The foreman is told, in one line** — `phase N closed, result rejected`,
above. It is the one report that is not routine: the plan it authored is
about to change, and it holds the reasons the plan was shaped that way. It
answers as it answers any message, with the delta (`refs/board.md` → *When it
is drawn*): a rejection is the moment a board is most tempting and least
useful — the shape is about to change, so drawing the old one costs tokens to
show a position nobody will act on. The re-planning itself is a conversation,
and it happens where the person is. A rejection is also a ledger moment
(`refs/foreman.md` → *Skill lessons — the wf-lessons ledger*): the design conversation let a bad
idea through, and where it did is a lesson about the skill, not only about
this plan.

Note fields the autonomous chain writes on phases, and what consumes them:

- `> Issue:` — root symptom and current diagnosis; written by `/execute-phase-agent`
  when a phase exits `[!]`.
- `> Attempted:` — numbered list of fixes tried, each with its error
  signature. Mandatory on `[!]`: it is the input of `/repair-phase`, which
  must NOT repeat those attempts.
- `> Repair started: <ISO timestamp> — chat <title>` — written by
  `/repair-phase` the moment it takes the phase under repair, committed with
  that transition, and removed by the edit that records the outcome. It is
  what separates a phase somebody is repairing right now from one left
  broken: `[!]` alone does not say, so a foreman reading the plan cold would
  send a second repair into the same working tree. A marker whose chat is
  gone is stale, and a stale one means the repair can be taken up again.
- `> Repaired:` — on a phase turned `[x]` by `/repair-phase`: the actual
  root cause and why the previous attempts missed it.
- `> Repair attempted: <ISO timestamp> — <diagnosis>` — appended by
  `/repair-phase` when the repair fails. It is the idempotent marker:
  `/run-workflow` launches at most ONE repair per phase and stops for
  human review when this note exists. Deleting the note grants another
  repair round after manual intervention.
- `> Review:` — judgment-level findings from the per-phase independent
  verification, flagged for the human at the quality check; they never block `[x]`.
- `> Verify:` — one manual check left to the human, carrying its *when*
  (`now` / `deferred: needs Phase M`); written by the executing skill —
  thick in `/execute-phase`, thin in `/execute-phase-agent` — deferred
  ones copied into `verify.md`, all of them collected by
  `/quality-check`. Semantics in `refs/contracts.md` → *Verification*.
- `> Verified:` — optional record of the verification evidence a phase ran
  (which test, which check, what confirmed the `Done:`).

`/repair-phase` always targets the FIRST `[!]` phase in the plan.

## Autonomous permission scope

The Codex `workspace-write` boundary without automatic escalation, and the convention
for writing phases around it, live in
`<PLUGIN_ROOT>/refs/auto-mode-scope.md` — read it only when deciding
whether a phase can run unattended (`/run-workflow` pre-flight,
`/write-workflow` on the autonomous branch).
