---
name: import-workflow
description: Import an existing plan or a handoff document into a .phased/ workflow
---

# Import Workflow

Turn an existing plan or a handoff document into a `.phased/` workflow. This is an **adapter, not a planner**: it maps what the source already says onto the plan format and reports what is missing. It never invents phases, and it never writes source code.

**Shared conventions:** read `<PLUGIN_ROOT>/refs/common.md` once at start. Read
`<PLUGIN_ROOT>/refs/foreman.md` only at Step 4 after Step 3 settles relayed or a
legacy plan; an in-chat import creates no relay.

Typical sources: a pre-4.0 `.claude/MEMORY.md`, a parallel `memory_<name>.md` from the same era, or a free-form handoff written by a previous session or another person.

## Step 1: Find the source

If the user's invocation names a path, use it. Otherwise look, in order, for `.claude/MEMORY.md`, `.claude/memory_*.md`, then any handoff-looking markdown the user points at. Several candidates → ask one structured question. Nothing → stop: *"Nothing to import here. `write-workflow` writes a new plan."*

`.phased/active/` already occupied → stop. One branch, one plan.

## Step 2: Classify the source

One question decides Step 4: **does the source contain phases already marked `[x]`?** Getting it wrong is the one way this skill can destroy work, so do not eyeball the markers — ask the parser that already reads them:

```bash
python3 "<PLUGIN_ROOT>/scripts/next-phase.py" <source>
```

It prints one line per phase with its state, and it works unchanged on a pre-4.0 `MEMORY.md` — the phase-line format did not change. It also fails loudly if the source is not a parsable plan, which is worth knowing before touching anything.

- **No `[x]` in the table** (and always, for a handoff document, which has no phases at all) → *fresh import*. The work has not started.
- **Any `[x]`** → *mid-run import*. The work already exists in the tree and in old-style commits.

The script erroring out (an unparsable source, a handoff) is not a classification — read the source yourself and treat it as a fresh import. Genuinely ambiguous markers → mid-run, which is the conservative side: it never rewrites history.

Then read the whole source, for the mapping in Step 3.

## Step 3: Map onto the plan format

Produce the plan in the `/write-workflow` format — same `Pattern:` / `Files:` / `Decisions:` / `Details:` / `Done:` fields, same phase markers.

**Preserve, do not rewrite.** Phase states (`[x]`, `[!]`, `[~]`, `[>]`) and every note the source carries — `> Done:`, `> Files:`, `> Issue:`, `> Attempted:`, `> Repaired:`, `> Review:`, `> Verify:` — come across verbatim. They are the record of what happened; re-deriving them would be inventing history. A `## Roadmap` section in the source moves to `.phased/roadmap.md`, and a `## Suggested execution config` table comes across as-is.

A handoff document has no phases yet: derive them from what it describes, and say plainly that you did — this is the one case where the import is also an act of planning, and the user should review it as such.

**Then report the gaps, don't fill them.** Check every remaining `[ ]` phase against the autonomous-ready bar (`/run-workflow` pre-flight): concrete and verifiable, bounded scope, measurable `Done:`, decisions pre-made, `Pattern:` cited for non-trivial code. Present what is missing, per phase:

```
Phase 3 — no measurable Done: ("works fine" cannot be checked)
Phase 5 — no Pattern:, and the code is not trivial
```

Inventing a plausible `Done:` for a phase whose author never wrote one is worse than leaving the gap visible: it looks settled and nobody checks it again. Offer to refine them now, one at a time, or to import as-is and leave `/write-workflow` to it.

**Then settle how it will run** — use `/write-workflow` Step 2's mode and
channel fork. Keep headers the source already carries. When a source has no
`Channel:`, it is a legacy plan whose behaviour must not change silently: ask
before adding the field. Autonomous always implies relayed. The gap report
still applies; the headers never hide an autonomous-readiness gap.

## Step 4: Land it

Show the plan and close with the gate line (`common.md` → *The gate line*): *"**Proceed?** On your ok, I create or adopt the branch and commit the plan."* Then, depending on Step 2:

**Fresh import** → same branch rules as `/write-workflow` Step 4 (*Open the branch*): on a base branch, `git switch -c wf/<slug>`; on a feature branch, adopt it by default, with `wf/<slug>` off it as the alternative.

**Mid-run import** → **adopt the current branch, no question, no rebase, no reset.** The completed phases correspond to work already in this tree and to commits already made; a fresh branch would strand them. Say so explicitly: *"Imported in place on `<branch>`: the phases already `[x]` match work that is already here, so no new branch and no history rewrite."*

This is safe because the workflow's base is the plan commit, not the branch point (see `common.md`): the old commits land before it and therefore outside the workflow, so `/finalize-workflow` consolidates only what comes after and leaves them for the user to deal with — which is the honest outcome, since nothing can retroactively tell which of them belonged to which phase.

Then write and commit:

```bash
mkdir -p .phased/active/<slug>
# plan.md + empty notes.md (+ foreman.json on relayed/legacy only)
git add .phased && git commit -m "wf: import plan for <slug>"
```

On relayed and legacy plans, importing is taking command: write `foreman.json`
alongside the plan per `foreman.md`; it rides the import commit. On in-chat,
write no `foreman.json` and apply no foreman title — the work continues here.

Verify the commit is not empty (`git show --stat HEAD`).

**Leave the source file alone.** Deleting it is the user's call, and on a mid-run import it may still be what other tooling is reading. Say where it is and that it is now superseded.

## Step 5: Close

```
Imported into .phased/active/<slug>/plan.md (<N> phases: <x> done, <y> to do), committed on <branch>.
relayed/legacy → this task is the foreman, now titled `wf:<slug>:foreman`; continue with /execute-phase in a new task.
in-chat → no relay and no foreman; continue with /execute-phase here.
Source left at <path> — superseded, delete it whenever you like.
<gaps, if any>
```

On the relayed road, where the title could not be set, that line becomes the
ask per `foreman.md`.
