---
name: pull-request
description: Create a Pull Request after thorough review as a meticulous maintainer
---

# Pull Request Review & Creation

Review the branch as the maintainer who has to approve it, then open the PR — or block it. All written output (title, body, review report) in English; the conversation follows the user's own configuration (`<PLUGIN_ROOT>/refs/common.md` → *Language*).

## Step 1: Base branch and issue

Default base: the `Parent:` line of the active plan if there is one (`python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --resolve`; from outside the plan's root, `--plans` + `git -C` per `common.md` → *Plan location*), else `develop` when `git rev-parse --verify origin/develop` succeeds, else `main`. Ask the user via Codex user-input prompt with that default first and "(Recommended)", verify the chosen branch exists (`git ls-remote --heads origin <base>`), and use it as `<base>` throughout.

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

**3.1 — Delegated pass.** Run the built-in `code-review` skill (Skill tool) on the branch diff at effort `medium` (`high` for large or risky diffs). Its confirmed findings feed Step 4.

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
