---
name: repair-phase-agent
description: Repair the first failed [!] phase unattended — no questions, one commit, a machine-readable outcome
---

# Repair Phase — unattended

Base skill: repair-phase. Read `<PLUGIN_ROOT>/skills/repair-phase/SKILL.md` and follow it — locating the failure, diagnosing from scratch, the fix-and-converge budget, the unconditional `phase-verifier` pass and the outcome formats all live there. This file carries only what changes when nobody is in the room.

**Launched by `/run-workflow`** (at most once per phase), or `codex exec '/wf:repair-phase-agent'`.

## What the environment changes

- **No questions at all** — not at the start, not at the verdict. The base asks the human what is wrong and waits for their ok; here there is nobody to ask, so the plan's `> Issue:`, `> Attempted:` and `> Files:` are the whole account, and `log/phase-N.txt` next to the plan is the richest source of all: it is what the failing session really did, not its summary of itself.
- **`[!]` only.** Take the **first** `[!]` phase; no `[!]` → print "No failed phases to repair." and exit. The base's other way in — a defect a human has seen on a `[>]` phase — cannot arise here: it starts with somebody watching.
- **The outcome is the exit condition**, checked by an independent evaluator: `[x]` + `> Repaired:`, or `[!]` + `> Repair attempted:`. Never a phase left in a state the plan cannot describe, and never a repair that loops — a phase already carrying `> Repair attempted:` is printed and left alone.
- **The marker is written, the title is not.** `> Repair started:` goes on the phase and gets its `wf(phase N): under repair` commit exactly as in the base — it is what tells a foreman reopened cold that this phase is being worked on. The chat title is skipped: a `codex exec` sub-session has no session tools and nothing to address (`foreman.md` → *The foreman*), so the marker names the run instead — `chat run-workflow (unattended)`.
- **Never hand back.** The base can return a phase to `[>]` for its chat to finish; there is no such chat here. A repair that cannot reach green ends `[!]` with its updated diagnosis, and the foreman gets the `blocked` line if one is reachable (`foreman.md` → *The foreman*, best-effort).
