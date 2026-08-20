---
name: finalize-workflow
description: Close the workflow — quality-check gate, durable lessons, plan archive, consolidation into one clean commit
---

# Finalize Workflow

Close the workflow: check the quality gate, carry the lessons out, archive the plan, and turn the working tree into one clean commit with the closing proposal. The quality work itself — QA pass, naming review, scope coherence, pre-commit review — is `/quality-check`'s, run before this skill and attested by its stamp. **Never edit source code here** — this skill touches `.phased/` and git history only.

**Shared conventions:** read `<PLUGIN_ROOT>/refs/common.md` and `<PLUGIN_ROOT>/refs/foreman.md` once at start — core conventions, the reporting register and foreman messaging. The stamp this skill gates on is defined in `<PLUGIN_ROOT>/refs/contracts.md` → *The quality-check stamp*.

## Step 1: Find the plan and the base

```bash
python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --resolve
git branch --show-current
git worktree list --porcelain
```

Set `IN_WORKTREE` from whether the cwd is in the worktree list. No active plan → stop; the plan lives on the workflow branch, so check `git branch --show-current` before concluding there is nothing to finalize — and check `--plans` first: the workflow may live in another checkout (`common.md` → *Plan location*). When it does, every git command below runs `git -C <plan root>` and every path is anchored there; the consolidation itself (Step 5) must happen on the plan's branch, never on the cwd's.

Read the plan for `Parent:`, the issue number and the phase states. **Resolve the parent ref**: `origin/<parent>` if `git rev-parse --verify` finds it, otherwise the local `<parent>`.

Then resolve the two things every step below depends on:

```bash
BASE=$(git log -1 --diff-filter=A --format=%H -- <plan path>)   # the commit that ADDED the plan
git rev-list --count "$BASE"^..<parent>                         # 0 => BASE is the branch point
```

`BASE` is the workflow's base: everything after it belongs to this run, everything before it does not. That second command tells you which shape you are in — **dedicated branch** (the plan commit *is* the branch point: the branch is the workflow) or **adopted branch** (the branch already carried commits, which must survive untouched). Step 5 differs between the two; nothing else does.

All phases `[x]` → proceed. Otherwise report the incomplete ones (warn specifically that a `[>]` may be a dead session) and ask whether to finalize anyway (default: no).

## Step 2: The quality gate

Grep the plan for the stamp — the last `> Quality check:` line under `## Quality check` (`contracts.md` → *The quality-check stamp*):

- **No stamp** → the quality work has not run. Ask ONE `Codex user-input prompt`: **Run `/quality-check` first** (Recommended — this close would otherwise carry no QA pass, no naming review, no whole-diff review) / **Close without it** (its price stated in the option: nobody has seen the whole diff at once, and any `wf:phase-N:new` markers ride into the parent). On the first option, stop here and say to run `/quality-check`, then `/finalize-workflow` again. On the second, proceed — and say so again in the close-out, in one line.
- **Stamp present but stale** — commits landed after the stamp's own commit (compare the stamp's `commit <hash>` against `git log <hash>..HEAD`, the stamp commit itself excluded) → same question, phrased as stale: the check saw a tree that no longer exists.
- **Stamp current** → proceed, quoting it in one line (review depth, QA answer, findings).

The tree must be clean either way. If `git status --short` shows anything, report it and ask whether to include it before going on; do not sweep it in silently.

## Step 3: Capture durable lessons

**This step is mandatory and runs before anything is archived or removed.** `.phased/` never reaches the parent, and the workflow branch is deletable at Step 5 — so this is the only path by which anything learned during the run outlives it. Skipping it silently is how the loop stops learning across runs.

Scan the plan and its `notes.md` for: `> Repaired:` notes (a root cause *plus why earlier attempts missed it* — the highest-value kind, it encodes a trap); the per-phase `## Phase N` rationale entries the executing chats left there (`foreman.md` → *The foreman*) — that file is how the run's reasoning outlives its executor chats; `new-pattern` phases that landed cleanly (now there IS a reference); `> Review:` findings that revealed a convention rather than a one-off; and pattern references that proved **wrong**.

One bar: **would this have saved a future session real work, in a way the repo and git history don't already say?** Framework quirks, non-obvious API behaviour, "we do it like X here" → yes. Bugs specific to this diff, anything visible by opening the file → no.

Nothing clears the bar → say so explicitly, in one line, naming what you scanned. Something does → propose it via Codex user-input prompt with a draft title and a two-line summary, and on approval write it wherever this project keeps durable know-how, following whatever your global rules say about that. Prefer correcting an existing entry over adding a near-duplicate. Never publish without approval.

## Step 4: Archive the plan

The run is over and its lessons are out. Move the plan directory into the archive and commit it on the workflow branch:

```bash
git mv .phased/active/<slug> .phased/done/<slug>
git commit -q -m "wf: archive plan for <slug>"
```

It stays on this branch — logs, notes and phase history included — and never reaches the parent. If `.phased/roadmap.md` exists, leave it in place: the next macro-phase is written against it.

## Step 5: Close out

Build the commit message from the objective, the completed phases, the actual diff (`git log --oneline "$BASE"..HEAD`, `git diff --stat "$BASE"..HEAD`) and the issue (`fixes #N`):

```
<type>: <concise summary>

<detailed description, grouped logically>

[Fixes #N]
```

Present it, then ask ONE `Codex user-input prompt` — choosing a path approves the message as shown, so say right above the question that edits to the message are welcome before choosing:

- **Pull request** (Recommended) — clean branch off the parent, squash, PR to `<parent-branch>`
- **Merge into parent** — squash straight onto `<parent-branch>` and push
- **Commit only** — leave the branch as it is, decide later

One gate, not two: approving the commit message separately was a second round-trip that bought nothing.

**Merge into parent** → from the main repo (`git worktree list --porcelain | head -1 | sed 's/worktree //'`): switch to the parent, pull, then

```bash
git merge --squash <workflow-branch>
git rm -r -f .phased
git commit    # the message approved above
git push
```

On an **adopted branch** there is nothing to squash onto the parent — the workflow is consolidated in place:

```bash
git tag "wf-archive/<slug>" HEAD     # keep the per-phase history reachable
git reset --soft "$BASE"^
git rm -r -f .phased
git commit                           # the message approved above
```

The commits that preceded `BASE` stay exactly as they were; the branch then reaches the parent by the ordinary merge or PR.

**Say the trade-off out loud before doing it.** Consolidating in place drops the per-phase commits and the archived plan from the branch — unlike the dedicated-branch path, no separate branch is left holding them. The tag is what keeps them reachable (`git log wf-archive/<slug>`), and Step 3 is what carries the lessons out regardless. Delete the tag once the work is merged and the history is no longer wanted.

**Pull request** → branch off the **parent**, not off the workflow branch, so the PR carries one commit and no `.phased/`:

```bash
git switch <parent> && git pull
git switch -c <type>/<slug>
git merge --squash <workflow-branch>
git rm -r -f .phased
git commit
git push -u origin <type>/<slug>
```

Then: *"Branch pushed. Launch `/pull-request` to open the PR to `<parent>`."*

**Commit only** → nothing else happens; the workflow branch holds everything.

Whichever path ran: send the foreman the closing `workflow finalized` message per `foreman.md` → *The foreman* — best-effort, phrased per the reporting register. `list_sessions` excludes the current session, so when this chat IS the foreman the title lookup finds nothing and the skip is automatic. A close that ran without a quality stamp says so here too, in one line.

After the first two, offer to delete the workflow branch and its worktree (default: yes) — `git worktree remove .claude/worktrees/<slug>` + `git branch -D <workflow-branch>`. **Unless `.phased/roadmap.md` still lists unstarted macro-phases:** then keep the branch, say why, and remind the user *"The roadmap has further macro-phases. Next step: a new chat and `/write-workflow` to detail the next one — with the hindsight of the one just committed."* If `IN_WORKTREE`, remind the user that the worktree itself is plain git: `git worktree list` shows the stale ones, `git worktree remove <path>` clears them.

## Rules

- **NO source code editing** — the quality work, its findings and the one naming-review exception live in `/quality-check`
- Show what will happen before any git operation; be especially careful with resets
- Never delete the workflow branch before Step 3 has run: it is the only thing carrying the run's lessons out
