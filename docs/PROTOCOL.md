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
    foreman.json
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

Known durable note fields are `Done`, `Files`, `Issue`, `Attempted`, `Repaired`,
`Repair attempted`, `Repair started`, `Review`, `Blocked`, `WIP`, `Testing`,
`In execution since`, `Verify`, and `Verified`.

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
4. `foreman.json` may update its `host`; opaque session ids are never portable.
5. A live cross-session message is advisory. The committed plan is authoritative.

Protocol changes require fixtures for both origins and must remain readable by
the previous released implementation unless the release explicitly declares a
breaking compatibility version.
