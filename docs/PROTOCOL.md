# Portable `.phased/` protocol

This document is the compatibility contract between `claude-phased-workflow`
and `codex-phased-workflow`.

## Stable surface

The stable surface is committed repository state, not a host application's
session API:

```text
.phased/
  roadmap.md
  active/<slug>/
    plan.md
    notes.md
    foreman.json           # Channel: relayed and legacy plans only
    verify.md
    mockups/
    tests/
    log/
  done/<slug>/
```

`plan.md` uses these phase markers:

| Marker | Meaning |
|---|---|
| `[ ]` | pending |
| `[>]` | in progress or awaiting human verification |
| `[x]` | completed |
| `[!]` | failed and repairable |
| `[~]` | blocked by an unattributable baseline or external constraint |

Known durable note fields are `Done`, `Files`, `Issue`, `Attempted`, `Applied`, `Repaired`,
`Repair attempted`, `Repair started`, `Review`, `Blocked`, `WIP`, `Testing`,
`In execution since`, `Verify`, `Verified`, and `Batches`.

`Mode:` and `Channel:` are orthogonal plan headers. `Mode:` remains
`interactive|autonomous`; optional `Channel:` is `in-chat|relayed` and decides
where questions, outcomes, and re-planning travel. A missing `Channel:` keeps
legacy relayed behavior. `Mode: autonomous` with `Channel: in-chat` is invalid.

`> Batches: 1 <label> | 2 <label> | …` is an optional planned subdivision of
one phase. Each batch may land as
`wf(phase N): partial — batch M/K <label>` without a `WIP:` note or handover.
The phase still owes one `Done:` and one final `wf(phase N): <title>` commit.

After the plan commit, a phase may change its marker and append durable `>`
notes. The foreman owns `Done:`, authored `Verify:`, `Pattern:`/`Pattern
reference:`, `Files:`, `Decisions:`, and plan-authored contract tests. A
sanctioned change is recorded in `notes.md`; close compares those fields and
tests with both the current copies and the plan commit.

## Quality closure

When every phase is `[x]`, corrections on decisions already taken stay in the
quality-check task: user-reported QA fixes and one final touch for review
findings. Size alone does not make a correction a phase. Open design decisions
or surfaces the plan never built go to planning together, as one phase once
the decisions are settled.

The final touch lands as `wf: final touch — <N> corrections`; its
finding → fix → files table is preserved under `## Final touch` in `notes.md`.
The re-check is Light/low on touched files and their human verification items,
not another Extended/Panel pass over the branch. Finalization reads both
`## QA fixes` and `## Final touch` for lessons.

The latest `> Quality check:` line under `## Quality check` remains the stamp.
Claude 6.35.0 adds the trailing `final touch <N corrections | none>` outcome;
older stamps remain readable, with the missing outcome unrecorded rather than
implicitly zero. The canonical stamp lives in `refs/contracts.md`. The
selector preserves the whole stamp without interpreting its outcome fields.

## Runtime mapping

Plans keep the Claude-era model labels because deployed Claude versions already
understand them:

| Portable label | Codex runtime | Meaning |
|---|---|---|
| `opus` | `gpt-5.6-sol` | default strong implementation |
| `fable` | `gpt-5.6-sol` | inventive work; retain or raise effort |
| `sonnet` | `gpt-5.6-sol` | accepted only for legacy plans |

Effort remains `low`, `medium`, `high`, `xhigh`, or `max` and maps directly to
Codex `model_reasoning_effort`.

## Handoff rules

1. Commit or cleanly record the current phase before switching hosts.
2. The receiving host runs `resume-workflow` and validates the plan.
3. Never translate markers, rename note fields, or rewrite model labels merely
   because the runtime changed.
4. On relayed and legacy plans, `foreman.json` may update its `host`; opaque
   session ids are never portable. In-chat plans do not create the file.
5. A live cross-session message is advisory. The committed plan is authoritative.

## Runtime transport

Stop requests, plan-defect answers, apply outcomes, active attempt logs, and
dashboard proposals stay outside the repository. `next-phase.py --transport`
returns an owner-private prefix under
`${TMPDIR:-/tmp}/phased-workflow-<uid>/`, keyed by both workflow slug and
repository root. Two checkouts carrying the same slug therefore cannot consume
each other's signals. These files accelerate one runtime and are not part of
the cross-product protocol.

Protocol changes require fixtures for both origins and must remain readable by
the previous released implementation unless the release explicitly declares a
breaking compatibility version.
