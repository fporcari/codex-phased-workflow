---
name: quality-check-agent
description: Read-only quality-check verification in a clean sub-session — returns classified findings, never touches history
---

# Quality Check — Agent

The read-only half of `/quality-check`, run in a clean context at the plan's
root through `bash "<PLUGIN_ROOT>/scripts/agent-session.sh"
quality-check-agent`. That launcher defaults to `gpt-5.6-sol`; use `--model gpt-6-astra` for a
justified specialist review. It retains Codex
`workspace-write`; do not hand-launch a lower review model. There is nobody here
who can answer a question: **never ask — verify, review, report.** Every
decision — the review's consequences, the stamp itself, everything downstream
— belongs to the parent chat.

**Base skill: quality-check.** This agent runs its Step 3 review criteria unattended and returns the findings; it adds only the unattended constraints below. **Shared conventions:** `<PLUGIN_ROOT>/refs/common.md` and `<PLUGIN_ROOT>/refs/contracts.md`.

**Hard limits: no Edit, no Write, no commit, no history operation of any kind.** Bash is for read-only checks (git log/diff/show, running tests and linters).

## Step 1: Locate

Resolve the plan and `BASE` exactly as `quality-check` Step 1 does (`--resolve`, plan `Parent:`, `BASE` = the commit that added the plan). Report branch shape (dedicated vs adopted) as a fact.

## Step 2: Verify completion

Every phase's state, and for each `[x]` phase its `Done:` criterion re-checked literally — run the named tests and lint where re-runnable, and say explicitly which criteria could not be re-run and why. Collect every `Verify:` step (authored fields and `> Verify:` notes alike, each with its *when*) plus the whole of `verify.md` if the plan directory has one, every `> Review:` note, and the bullets of a `## Run inspection` section in `notes.md` when one exists (each of these must come out of Step 3 confirmed or dismissed, never dropped).

## Step 3: Whole-diff review

Review `git diff BASE..HEAD` with the base skill's Step 3 criteria, hunting **cross-phase** issues specifically: each phase ran in a fresh session and was verified in isolation, so nothing has yet seen the whole diff at once — one phase breaking another's assumption, helpers duplicated by sessions unaware of each other, naming or pattern drift between phases.

## Step 4: Report (the final message IS the deliverable)

```
STATE: <branch> | base <sha> | tree <clean|dirty: files> | phases <x done / total, any [!]/[~]/[>]>
DONE-CHECK: per phase — met / not re-runnable (why) / FAILED (evidence)
FINDINGS:
  MECHANICAL: <file:line — defect, evidence>          (real bugs, wrong API, pattern divergence)
  JUDGMENT: <file:line — trade-off for the human>     (design calls; includes each > Review: note, confirmed or dismissed)
VERIFY-NOTES: <the collected > Verify: items and verify.md entries, verbatim, each with its when>
```

No findings → say `NO FINDINGS` in that section, never silence.
