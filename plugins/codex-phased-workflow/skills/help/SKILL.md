---
name: help
description: The map of the wf commands — where the work stands decides which command comes next, plus one line per command. Pure orientation, reads no state, changes nothing.
---

# Help — the map of the plugin

A router, not a manual: from where the user says they are, name the command
that takes the work forward. This skill reads no state and runs nothing — the
state of a real workflow is `/resume-workflow`'s to report, in a fresh
chat. Answer in the user's language, adapted to what they asked; the routes
and the table below are the canon of what to say, not a page to paste.

## Where are you?

- **No workflow yet — an idea, an issue, a discussion.** Talk the work
  through in a chat, then `/write-workflow` recommends a self-contained
  brief for one task when no context limit, intermediate decision gate, or
  unattended checkpoint/repair need justifies a workflow. Otherwise it creates
  a branch, a plan and its first commit. Decisions still open →
  `/scope-workflow` first, one question at a time. Starting from a GitHub
  issue → `/issue` for the analysis. A plan or handoff that already
  exists → `/import-workflow`.
- **A plan exists, building interactively.** `/execute-phase` gives one
  approval gate up front, then execution; `Channel: relayed` and legacy plans
  use one fresh task per phase, while `Channel: in-chat` keeps every phase and
  gate in this conversation.
- **A plan exists, run it unattended.** `/run-workflow` from the foreman
  chat: one sub-session per phase, one automatic repair on failure, stop
  conditions. The `-agent` variants (`/execute-phase-agent`,
  `/repair-phase-agent`, `/quality-check-agent`) are its workers —
  launchable by hand, but nobody has to.
- **Something is demonstrably broken** — a red `Done:`, a defect that
  reproduces → `/repair-phase` in a chat of its own; the phase chat
  checkpoints and stands down until the repair hands back.
- **The work is done but it was the wrong thing** — everything green, result
  rejected: the phase closes `[x]` carrying the verdict and the remaining work
  is re-planned on the configured route — foreman on relayed, this gate on
  in-chat.
- **A phase is struggling** — presuppositions in doubt, the conversation
  circling on why it does not work: that is the stop-loss; route the doubt per
  `Channel:` and land on one of the two cases above.
- **Lost, or resuming after days** — `/resume-workflow` in a fresh chat:
  it needs the branch, nothing else, and it names the next command.
- **Want a live local view** — `/dashboard` opens the optional authenticated
  plan/roadmap/log view and serves proposals queued for this Codex task. The
  textual `/resume-workflow` report remains the complete fallback; the page
  is never required to continue.
- **The phases feel incompatible with each other** — or the plan predates
  contract tests and you want the verdict instead of the suspicion →
  `/doctor`: coherence audit, contract-test integrity, and a blind
  retro-fit of the missing tests, verified phase by phase.
- **Every phase is `[x]`** — `/quality-check` first: the QA pass of the
  deferred human checks, the naming review, the whole-diff review at the
  depth you choose. Corrections on a decided design are QA fixes and one final
  touch in this task, followed by a scoped, risk-appropriate re-check; new surfaces or unresolved
  design go to one grouped phase, never one per finding. Then `/finalize-workflow`:
  lessons, archive, one consolidated commit on the parent — then PR, merge,
  or leave it.

## The commands, one line each

| Command | What it does |
|---|---|
| `/scope-workflow` | settle the open decisions before the plan exists, one question at a time |
| `/issue` | load and analyze a GitHub issue — analysis only |
| `/write-workflow` | turn the conversation into a one-task brief or branch + plan + first commit |
| `/import-workflow` | adopt an existing plan or handoff document into `.phased/` |
| `/execute-phase` | execute the next phase interactively — one gate, then run to completion |
| `/close-phase` | close a finished phase: naming review, Done gate, `[x]`, one commit |
| `/repair-phase` | fresh-eyes repair in its own chat; you say what is wrong and when it is fixed |
| `/run-workflow` | run all remaining phases unattended, one sub-session per phase |
| `/execute-phase-agent` | one phase, unattended — `/run-workflow`'s worker |
| `/repair-phase-agent` | repair the first `[!]` phase, unattended |
| `/resume-workflow` | where the work stands, and which command takes it forward |
| `/dashboard` | optional authenticated local state view and task-owned proposal queue |
| `/doctor` | is the work still coherent with the plan — audit, test integrity, blind retro-fit |
| `/quality-check` | QA, naming, whole-diff review, one correction batch and scoped verification — stamps the plan |
| `/quality-check-agent` | the read-only quality verification, in a clean sub-session |
| `/finalize-workflow` | quality gate, lessons, archive, consolidate into one commit |
| `/pull-request` | open the PR after a maintainer-grade review |
| `/help` | this map |

Close with one line: the full narrative is the plugin's README; for the
state of an actual workflow, open a fresh chat on `/resume-workflow`.
