---
name: pull-request
description: Create a Pull Request after thorough review as a meticulous maintainer
---

# Pull Request Review & Creation

Review the branch as the maintainer who has to approve it, then open the PR — or block it. All written output (title, body, review report) in English; the conversation follows the user's own configuration (`<PLUGIN_ROOT>/refs/common.md` → *Language*).

## Step 1: Base branch and issue

Resolve the PR target with `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`.
Use the repository default unless the user explicitly chose another target.
The plan's Parent is its workflow integration boundary, not automatically the
PR base. Verify the chosen remote ref before reviewing the delivery diff.

Issue number: use the number named in the user's invocation, otherwise the leading number of the branch name (`123-fix-login` → 123); none → proceed without one.

**If the current branch IS `<base>`**, the changes aren't on a feature branch yet: `git fetch origin <base>` → `git stash` → `git pull` → `git stash pop` (conflicts → STOP and report). Read the diff, derive a branch name of the form `type/short-description` in kebab-case (`fix/`, `feat/`, `refactor/`, `docs/`, `style/`, `chore/`; ≤50 chars; describe what the change does, not which files it touches), present it with a proposed commit message, and only after approval `git checkout -b` + `git add -A` + `git commit`.

## Step 2: Sync and read the diff

```bash
git fetch origin <base>
git log HEAD..origin/<base> --oneline
```

New commits on the base → ask before `git merge origin/<base>` (recommended: yes); conflicts → STOP and report how to resolve.

Then read `git diff --name-only origin/<base>...HEAD` and the full `git diff origin/<base>...HEAD`, plus `gh issue view <number>` if there is one.

## Step 3: Review

**3.1 — Independent pass.** Reuse traceable quality-check evidence from notes.md
for the reviewed revision. Review changes since that revision and affected
consumers; unchanged covered code does not need a duplicate full pass. Missing
evidence or new requirements require review of the uncovered scope. Preserve
unresolved findings and check the delivery requirements below every time.

**3.2 — Maintainer checks** (what only this workflow knows):

- **Issue coherence** — every change relevant to the linked issue; flag drive-by changes and scope creep.
- **Conventions** — the code follows the project's (framework APIs verified against source, style of the surrounding code).
- **Over-engineering**, one line per finding as `file:line — tag — what to cut, what replaces it`:
  - `delete:` dead code, unused flexibility, speculative features
  - `stdlib:` hand-rolled code the standard library already ships
  - `native:` code or dependency doing what the framework already does
  - `yagni:` abstraction with one implementation, config nobody sets, layer with one caller
  - `shrink:` same logic, fewer lines — show the shorter form
- **Leftovers** — TODO/FIXME, `console.log`, `print`, `debugger`.
- **Comments in English** — every comment **added or modified by this PR**. Pre-existing non-English comments on untouched lines are not a blocker.
- **Security** — no hardcoded credentials; error handling and input validation where the diff touches a trust boundary. If it touches auth, permissions or input parsing, recommend `/security-review` before merging.

## Step 4: Decide

**Problems found → do NOT create the PR.** Report:

```
## PR Review Failed

### Problems Found:
1. **[Category]**: description
   - File: `path/to/file.py:123`
   - Detail: ...

### Required Actions:
- [ ] Fix problem 1

Once problems are resolved, run `/pull-request` again
```

**Clean → create it:**

```bash
git push -u origin HEAD
gh pr create --base <base> --title "[DESCRIPTIVE TITLE]" --body "$(cat <<'EOF'
## Summary
- [Main change]
- [Bullet 2]

## Linked Issue
Closes #ISSUE_NUMBER (if present)

## Test plan
- [ ] Manual tests executed
- [ ] Automated tests pass
- [ ] Expected behavior verified

EOF
)"
```

Then show the PR link.

Blocking a problematic PR is the correct outcome — better than letting subpar code through.
