# Phase execution — shared core

Loaded by `/execute-phase` (interactive) and `/execute-phase-agent`
(unattended). The two modes differ by *where decisions get made* — live in
the chat, or pre-made in the plan — never by these mechanics. A rule that
changes here changes for both; that is the point (the `Never commit`
leftover of 4.1.0 is what happens when siblings carry their own copies).

## Select the phase

```bash
python3 "<PLUGIN_ROOT>/scripts/next-phase.py"
```

Act on `recommendation:` — `next: N` → take it; `done` → exit suggesting
`/finalize-workflow`; `blocked: ...` → report the reason and stop;
`resume-candidate: N` and `attention: ...` → mode-specific, see the calling
skill. Script unavailable → apply the semantics in `refs/common.md`.

Mark the selected phase `[>]` with `> In execution since <ISO timestamp>`.

## Implement

Read the phase's `Pattern:` example first — it is the model to copy-adapt —
then its `Files:`. Write the code the phase describes, and nothing else.
Never invent framework APIs. ONE phase per invocation; no out-of-scope
refactoring.

**New callables: minimal, and marked.** Introduce only the methods and
functions the phase's `Done:` requires, and give every one of them the
end-of-line marker on its definition line — `# wf:phase-N:new`, in the
file's own comment token — per `refs/contracts.md` → *New-method markers and
minimality*. The name you choose is a proposal: the naming review
(`refs/naming-review.md`) is where a human accepts or rewords it —
`/close-phase` in interactive runs, `/finalize-workflow` in autonomous
ones — so never spend a question on a name here.

**The plan is context, not just a queue.** Before the first edit, skim the
whole plan once — every phase, not only yours. The `> Done:`/`> Files:`
notes of completed phases say what already exists: reuse it, never
duplicate it. The pending phases say where the work is heading: a
micro-choice this phase leaves open (a name, where a helper lives, a data
shape) is decided in favour of the phases that come after, and a choice
that would force a successor to undo or work around it is the wrong choice
even when it is locally cheaper. Where the plan carries contract tests, the
pending phases' `tests/phase-M/` are the sharpest statement of where the
work is heading — read the ones this phase's choices could touch. The
plan's `Must not break:` header and, on a programme, the roadmap's
remaining macro-phases are successors of the same rank (`refs/contracts.md` →
*Must not break:*): a choice that breaks one is wrong at the same price. Scope is
unchanged: knowing Phase 5 exists never means implementing a piece of it
here.

**Contract tests, where the plan carries them** (`refs/contracts.md` →
*Contract tests*): copy `tests/phase-N/` verbatim into the repo's test tree
before implementing — red is the starting state, green is part of `Done:`.
A skeleton's body is yours to write; everything else is read-only here, and
a test that cannot pass as written goes up, never under the knife —
`clarify?` in interactive mode, `[!]` naming the test in unattended mode,
per the single source.

## Record the outcome

The `[x]` path has a skill of its own: in interactive runs `/close-phase`
performs this section and the two that follow (naming review included);
`/execute-phase-agent` performs them inline, markers left in place. The
`[!]` and `[~]` outcomes are always recorded directly by the executing
skill — failure never routes through `/close-phase`.

```
- [x] **Phase N**: title
  > Done: brief description
  > Files: path/a.py, path/b.py, ...
  > Review: judgment-level findings flagged for the quality check (omit if none)
```

```
- [!] **Phase N**: title
  > Issue: root symptom and current diagnosis
  > Attempted: 1) <fix tried> → <error signature>  2) <fix tried> → <error signature>
  > Files: path/a.py, path/b.py, ...
```

```
- [~] **Phase N**: title
  > Blocked: <what blocks it — e.g. a pre-existing red baseline nobody owns>
```

**Always list ALL touched files in `> Files:`** — later baseline checks
attribute regressions by them, and `/repair-phase` diffs against them.
`> Attempted:` is mandatory on `[!]`: it is the input of `/repair-phase`,
which must not repeat those attempts.

## The phase commit

One commit, at the end, the phase's code and its own plan status update
together — so the next phase starts from a clean tree:

```bash
git add -A && git commit -q -m "wf(phase N): <title>"
```

A phase closing `[!]` commits too, as `wf(phase N): FAILED — <title>`, and
leaves the failing code **in place**: repair has to see it.

A choice the phase made that the plan did not settle — why this way, what was
rejected — goes into `notes.md` under a `## Phase N` heading before the
commit, per `refs/foreman.md` → *The foreman* (per-phase rationale): finalize
reads the file, not the memory of a chat that no longer exists.

## Notify the foreman

After the phase commit, send the workflow's foreman chat one message with the
outcome — done, FAILED, or blocked — in the exact format and by the exact
mechanics of `refs/foreman.md` → *Sending to the foreman*. Read that section
when you reach this step, not at start — it is the only part of the foreman
layer an executing session needs. Best-effort: no
`foreman.json`, no messaging tool, delivery refused → skip in silence. The
notification never fails a phase and is never worth a retry loop.

## WIP checkpoints

A phase big enough to die halfway must leave evidence along the way. Two
triggers, one mechanic:

- **Coherent sub-result** — the phase reaches something demonstrable (the
  schema exists, the logic passes its test) with substantial work still
  ahead: checkpoint it, without asking. In practice this concerns
  interactive phases, sized to "something a human can look at"; an
  autonomous phase rarely lives long enough to need one.
- **Context running out** — the same mechanic, forced: checkpoint what
  exists and exit; the next invocation resumes from a clean tree.

Commit and note travel together — never one without the other, so the
note's `commit:` always points at code that exists:

```bash
git add -A && git commit -q -m "wf(phase N): partial — <sub-result>"
```

Keep the phase `[>]` and write (or replace) the structured `> WIP:` note.
**This is the single source of its format** — the skills cite it, they
never restate it:

```
> WIP: done: <demonstrable so far> | missing: <what remains of Done:> | next: <first concrete action> | commit: <short hash>
```

Each key earns its place at resume time: `done:` is what a fresh session
must not redo, `missing:` is what remains of the phase's own `Done:`,
`next:` is where it starts, `commit:` is the hash it diffs from instead of
trusting the story. Free prose is what made resume unreliable: a fresh
session reading vague prose reinterprets, and reinterpretation is how work
gets redone or contradicted.

## Handing a defect to repair

A defect found mid-phase is not the phase chat's to chase. Debugging is the
most context-hungry thing a phase does, and the chat holding the phase is the
one place where that context is expensive: it is carrying the objective, the
approval, the files and everything decided so far. So the defect goes to a
chat that exists only for it and is thrown away after.

The phase chat's part is two moves and no diagnosis:

1. **Checkpoint** — `partial` commit and `> WIP:` note, as above. The repair
   works on committed code, never on top of edits nobody recorded.
2. **Stand down** and say so: the working tree belongs to the repair chat
   until it hands back. Two chats editing one tree is the failure mode the
   whole protocol is shaped to avoid, and a phase chat that keeps tinkering
   "meanwhile" is that failure.

The rest belongs to `/repair-phase` in the new chat: it asks the human what is
wrong — their account, not the phase chat's diagnosis — records it as
`> Issue:`, marks the phase `[!]` on their confirmation for as long as the
repair lasts, and hands the phase back `[>]` with a `> Repaired:` note when
the human says it is fixed. **One chat is one attempt**: a repair that eats a
whole context without a green signal is not a bug but a plan problem, and it
goes to the foreman as `blocked` rather than to a second repair.

## When the phase outgrows its chat

A phase that does not fit in one context was sized wrong — the plan's own
doctrine, applied to itself. So the first question is not *how do I carry
this over* but **is there a seam here**, and the answer decides between two
mechanics:

- **There is a coherent, demonstrable sub-result, and what exists is
  green** → **close short**, the cleaner of the two. Nothing half-cooked has
  to survive a chat boundary: the phase ends properly, the tree is clean,
  the markers are reviewed, and the plan grows a phase for the remainder.
- **The work is mid-air** — a refactor half applied, a schema with nothing
  using it yet — → **hand over**. There is no honest `Done:` to write, so
  the `> WIP:` checkpoint above is the only truthful record.

**Closing short**, in order:

1. **Rewrite the phase's `Done:` to the sub-result actually reached**, and
   its `Files:` to what actually landed, with the user's ok. Mid-phase the
   child is the only writer of the plan, so it makes this edit itself — on
   its own phase, never on the others. A narrowed `Done:` is not a lowered
   bar: it is the plan being corrected to match what was really built, which
   is the precondition for `[x]` to keep meaning what it says.
2. **Close through `/close-phase`** like any other phase: naming review,
   `Done:` gate re-run — it passes now, honestly — `[x]`, ONE phase commit.
3. **Tell the foreman it closed short**, naming what remains in one line, so
   the plan grows the phases that carry it. What remains also goes to
   `notes.md` under the phase's `## Phase N`: a remainder that lives only in
   a message dies with the message.

The remainder is re-planned by the foreman, never appended by the child:
sizing the work is the job the whole protocol gives that chat, and the phase
that just overran is evidence about the sizing, not only about itself.

**Resuming a `[>]` phase** — the calling skill decides *whether* to take
it over; this is *how*: read the `> WIP:` note, run
`git log --oneline` over the phase's `partial` commits and
`git diff <commit>..HEAD`, and continue from `next:` toward the phase's
own `Done:`. What `done:` claims and the diff confirms is not redone.

**Look for the chat that had it, before reading the tree as an orphan.** A
phase chat titles itself `wf:<slug>:phase-N — <title>`, so it is findable in
`list_sessions` like the foreman is (`foreman.md` → *The foreman*, including
the rule that a tool you have not loaded is not a tool that is absent). Alive
→ one message: *hand over — commit anything uncommitted, tell me what is not
on disk, and stop working on this phase.* Its answer is a **supplement**: the
`> WIP:` note and the diff stay the authority, and a contradiction is settled
by the tree. Unreachable, or silent for ~3 minutes → carry on with the disk,
exactly as if it had never existed.

That message is what makes an uncommitted tree safe. Two chats on one working
tree are not a handover problem, they are two writers: the arriving one must
be able to say *stop*, rather than discover the traces afterwards.

A `[>]` phase with no `> WIP:` note and no `partial` commit carries no
evidence — and if its chat is gone too, reset it to `[ ]` with
`> Execution interrupted, phase available for retry` rather than guessing
what a dead session did. Uncommitted changes with nothing to explain them are
never guessed at either: report them and ask.

Checkpoints are not phase commits: `/finalize-workflow` squashes them with
everything else, and red-baseline attribution keeps matching against the
`> Files:` of *completed* phases, which a `[>]` phase does not yet have.

## Awaiting the human's checks

Interactive mode only — an unattended phase has nobody to hand a check to.
**When verification leaves the human at least one `Verify: now` step, the
code is finished but the phase is not.** It is committed and left `[>]`, so
nothing closes on a result nobody has looked at yet.

The mechanic is the checkpoint above — a `partial` commit — plus the note
that says what it waits for. **This is the single source of its format** —
the skills cite it, they never restate it:

```
> Testing: awaiting the human's `Verify: now` checks | commit: <short hash>
```

**Three ways out of the gate**, and only the middle one is more work here:
the checks pass → close; something is off and this phase can fix it →
ordinary work on the open phase, commit, present again; the result is wrong
at the root → the `Done:` passed, so the phase closes `[x]` carrying the
verdict as `> Review:`, the foreman gets the `result rejected` line, and the
phases that have not run are re-planned through `/resume-workflow`.
**Never `[!]` on a person's judgment** — `common.md` → *Failure and repair
notes* has both reasons: it aims an automatic repair at green code, and the
work itself is usually sound.

**Nothing is closed and nobody is told before the person has answered.** The
`[x]`, the phase commit and the foreman message all belong on the far side of
this gate: a phase reported done while its checks are still unrun is the
failure the gate exists to prevent.

The checks themselves stay in their own `> Verify: now` notes: one syntax,
not two. `next-phase.py` reports such a phase as `blocked:` — only the human
clears it, so an unattended run stops and says so instead of resuming a
phase with nothing left to implement. What the checks turn up is ordinary
work on the still-open phase: commit it the same way, replace the note. The
human's ok is what runs `/close-phase`, and closing drops the note.
