---
name: quality-check
description: Quality check of the finished workflow — QA pass with the user, naming review, scope coherence, pre-commit review at chosen depth; stamps the plan for /finalize-workflow
---

# Quality Check

Collect the finished workflow's evidence, diagnose the complete finding set, apply
one approved correction batch, and verify it once. Finalize reads the quality
stamp; a stamp is a record, not permission to hide a residual defect.

**Usage:** `/quality-check light|extended|panel|none`; an explicit depth already
answers the depth question. Read `<PLUGIN_ROOT>/refs/contracts.md`,
`<PLUGIN_ROOT>/refs/foreman.md` and `<PLUGIN_ROOT>/refs/execution-policy.md`.
Use the reporting register for user-facing findings.

## Step 1: Resolve scope and previous evidence

Resolve the active plan with `python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --resolve`.
If necessary use `--plans` to locate its checkout; run every Git command there.
Read the plan, notes.md, verify.md and review.md when present. Resolve:

```bash
BASE=$(git log -1 --diff-filter=A --format=%H -- <plan path>)
REVIEW_HEAD=$(git rev-parse HEAD)
git status --short
git diff --stat "$BASE".."$REVIEW_HEAD"
```

An absent/ambiguous base or unrelated dirty work must be resolved before review.
All phases must be `[x]` for close-out; an incomplete run can be assessed when
requested, but the report must name the missing acceptance.

A `## Final touch` heading is not proof of coverage. Read its recorded reviewed
revision, correction revision, scope, checks and remaining findings. Reuse only
traceable evidence covering the current scope. After a completed correction,
resume at its pending verification, not at a fresh whole-diff review. New code,
new phases, changed contracts or changed dependencies need a delta review and
related integration checks. Missing revision evidence means coverage is unknown.

## Step 2: Collect QA and naming findings without editing

Present the QA page defined in contracts.md as one checklist from authored and recorded `Verify:` items and verify.md,
grouped by observable result. Ask whether the human checks were exercised; retain
`done`, `declined` or `none` honestly. Review.md contains judgments, not substitutes
for exercising behavior. Collect defects and reproduction steps into the same
finding set used below; do not run a separate QA-fix commit cycle.

Collect `wf:phase-N:new` markers across the recorded files. Build the naming map
using `<PLUGIN_ROOT>/refs/naming-review.md`, but defer its edits and marker removal to
Step 5. Gather naming decisions once. A remaining marker is a reported blocker.
An urgent correction needed to exercise QA can be made when already authorized;
record its exact revision and finish collecting evidence before the final batch.

## Step 3: Review the complete scope once

Review `BASE..REVIEW_HEAD` for acceptance, behavior, contracts and integration.
Include every `> Review:` note, Run inspection finding and roadmap seam; each
receives a confirmed/dismissed/deferred outcome. Check produced and consumed
contracts in transit, including constraints crossing intermediate macros. Compare
the roadmap Ends at: with the delivered state in this roadmap check.

Ask once for review depth when none was specified.
Recommend Light only when informative phase checks and exercised human QA already
cover implementation; it focuses on integration. Recommend Extended for unreviewed
implementation, declined QA, uncertain contracts or high consequence changes.
Explicit None remains possible and is recorded as omitted review. It does not
waive acceptance checks or turn an unchecked result into a clean review.
Panel is one strong reviewer plus at most one specialist for a distinct material
risk. Do not dispatch a fixed panel or decide findings by majority vote.

Use a fresh read-only reviewer with the actual diff, acceptance and dependencies.
For another checkout use `<PLUGIN_ROOT>/scripts/agent-session.sh quality-check-agent`;
its default is an independent integration/acceptance pass. For a resumed delta
check use a fresh read-only reviewer given the exact revision range and affected
consumers; do not relaunch the whole-diff agent. Checkout location never changes
quality requirements. Keep author and reviewer separate for non-trivial code.
Report judging is optional and justified only by a material comprehension risk.
When needed, load `<PLUGIN_ROOT>/judges/report-judge.md` into a fresh read-only
`gpt-5.6-sol` reviewer.

## Step 4: Consolidate and diagnose before correction

An engineer checks all findings against the real code and contracts, groups shared
root causes and prepares ONE table:

| Finding and evidence | Root cause | Fix and affected consumers | Verification | Outcome |
|---|---|---|---|---|

Require a reproduction, violated acceptance/contract or concrete code evidence
for a defect. Label preferences and new requirements separately. Include naming,
QA and reviewer findings together. Determine whether one fix addresses several
symptoms; inspect callers before proposing edits. Resolve open product decisions
with the user in one batch. Present one reviewable correction proposal and obtain
approval unless the current authorization already covers it.

Do not append a phase for each defect. Existing-scope corrections stay here;
only a genuine new requirement or unresolved decision can lead to one grouped
follow-up through `/resume-workflow`. Report its effect on close-out explicitly.

## Step 5: One final touch and one focused verification

Apply the approved table, including renames/callers and marker removal. Run the
narrow relevant checks after each edit, then integration checks justified by the
combined change. Commit once as `wf: final touch — <N> corrections` when commits
are authorized. Preserve any user instruction forbidding commits.

Record under `## Final touch` in notes.md: reviewed revision, correction revision
(or pending commit), table, checks actually run, covered dependencies and residual
findings. This existing notes section is the durable correction ledger; no new
mandatory plan field is introduced.

One fresh read-only reviewer verifies that the corrections resolve the recorded
causes and do not break affected consumers. Review the correction delta plus its
dependencies, with effort appropriate to risk. Re-exercise affected human checks.
Do not restart Extended/Panel over unchanged scope. A residual defect stops a
clean close-out: report the evidence and failed premise, then propose a bounded
engineering intervention or an explicit risk decision. No automatic phase growth,
no concealed second repair loop, no invented clean verdict.

## Step 6: Stamp the actual result

Append the existing compatible stamp under `## Quality check` in plan.md:

```
> Quality check: <ISO timestamp> — commit <short HEAD hash> — review <extended|light|panel|none|agent>, QA <done|declined|none>, findings <N confirmed, M dismissed | none>, final touch <N corrections | none>
```

Record unresolved findings and any explicit risk acceptance in notes.md, linked to
the stamp revision. A diagnostic stamp with residual findings is not a clean gate;
finalize must read their disposition. Never automatically recommend consolidation
while required acceptance fails. When authorized, commit the stamp and ledger
alone as `wf: quality check — <review depth>`. Repeat the outcome in chat and name
the next action justified by it.
