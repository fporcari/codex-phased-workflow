# Claude 6.28.7 parity inventory

This inventory records the comparison made on 2026-08-28 before the parity
work began:

- Codex repository: `5e48fc5`, clean working tree;
- Claude reference repository: `0b02e11`, plugin version `6.28.7`, clean
  working tree.

The Claude repository was used read-only. Evidence came from its `CHANGELOG.md`,
`plugins/wf/`, orchestration suite, dashboard suite, and documentation. The
Codex repository's existing semantic port through Claude 6.20.0 was the
adaptation baseline.

## Classification

- **P — portable protocol:** committed `.phased/` structure or semantics that
  both products must read unchanged.
- **W — workflow-neutral:** behavior independent of the host runtime.
- **X — Codex-native:** the same durable result needs Codex-specific
  orchestration, sandbox, task identity, browser, or worker launching.
- **C — Claude-specific:** no safe documented Codex equivalent; omitted or
  replaced by the nearest durable Codex behavior.

Verification keys used below:

- **P1:** `tests/test_protocol.py` — both-origin fixtures, selector agreement,
  JSON, contract block, transport, fixed Sol, clean-tree launcher behavior.
- **O1:** `tests/test_orchestration.py` — timeout/interruption, stop, phase
  budget, plan-defect repair timeout, and green apply.
- **D1:** `tests/wfdash/test_core.py`, `test_components.py` — selector-backed
  state, roadmap/check rendering, branch-resident latest closed plan.
- **D2:** `tests/wfdash/test_outbox.py` — concurrent append, atomic partition,
  deduplication, ownership, private modes, Codex namespace.
- **D3:** `tests/wfdash/test_server.py` — authenticated reads/writes, one-shot
  replay, origin perimeter, no authority, registry reuse/staleness.
- **S1:** `tests/check_doc_mass.py`, `check_optional_surface.py`, skill/plugin
  validators, JSON validation, shell syntax, and Python compilation.

## Release matrix: inherited baseline through 6.20.0

These rows account for every earlier changelog entry. “Existing” means the
behavior was already present at Codex `5e48fc5`; this parity pass re-ran its
tests and preserved it.

| Claude release | Shipped behavior | Class | Codex implementation and status | Verification |
|---|---|---:|---|---|
| 4.1.0 | Corrections from the external review of 4.0.0 | W | No separately exposed runtime feature; its resulting conventions are embodied in `refs/common.md` and the current skills. | P1, S1 |
| 5.0.0 | Command surface, plan discovery, workflow branch/workspace lifecycle | P/W | `skills/*`, `refs/common.md`, `next-phase.py --resolve/--plans`; existing Codex packaging uses plugin skills instead of Claude commands. | P1, S1 |
| 5.1.0 | Unattended run | W/X | `skills/run-workflow`, `scripts/run-workflow.sh`; ephemeral `codex exec`, fixed Sol, `workspace-write`. | P1, O1 |
| 5.2.0 | Interactive mode | P/W | `Mode: interactive`, `write-workflow`, `execute-phase`, and selector validation. | P1 |
| 5.2.1 | Adversarial-review corrections to 5.1–5.2 | W | Preserved in the current execution/repair gates; no independent protocol field. | P1, S1 |
| 5.3.0 | Per-model autonomous steering | X/C | Portable labels remain; Codex intentionally maps every label to `gpt-5.6-sol` and varies only reasoning effort. Claude model-personality steering is inapplicable. | P1 |
| 5.4.0 | Invocation discipline and scope workflow | W | `skills/scope-workflow`, edit/approval gates in planning and execution. | S1 |
| 5.5.0 | Claude rename guide and cache bust | C | Claude packaging history is not imported. Codex manifest and install guide carry the Codex plugin identity. | S1 |
| 5.6.0 | Interactive `Run:` hints and resume board | P/W | `write-workflow`, `resume-workflow`, `refs/board.md`; model labels stay portable. | P1, S1 |
| 5.6.1 | Mandatory board controls and root chip | C/W | Superseded upstream by 6.2.0. Current Codex board is the same read-only strip, with chat/tool routing outside it. | S1 |
| 5.7.0 | Working board view | W | Historical state superseded by 6.2.0; no obsolete controls ported. | S1 |
| 5.7.1 | Repairable failure distinguished from blockage | P | `[!]` versus `[~]`, `Issue:` versus `Blocked:` in selector, common doctrine, repair/resume. | P1 |
| 5.8.0 | Resume evidence and checked version claim | P/W | `WIP:` with commit evidence, plan baseline attribution, selector validation. Product version claims are documented rather than inferred. | P1 |
| 5.9.0 | Explicit gate line and no fake questions | W | `refs/common.md` question/gate conventions and skill gates. | S1 |
| 5.10.0 | Foreman owns workflow; workers report | P/X | Portable `foreman.json`, `refs/foreman.md`; Codex task/subagent messaging when explicit, disk floor otherwise. | P1 |
| 5.10.1 | Foreman title as address | P/X | Portable title and host remain in `foreman.json`; Codex task discovery is best-effort and never replaces disk. | P1 |
| 5.11.0 | Run inspector, phase events, stop-work question | W/X | `run-workflow` inspector and `EVENT:` lines; return leg uses owner-private files. | O1 |
| 5.12.0 | `ui` tag, mockup, browser pass, fresh judge | P/W/X | `contracts.md`, `execute-phase`; Codex browser/UI skill when available, human fallback, judge prompt loaded from `judges/ui-judge.md`. | S1 |
| 5.13.0 | Whole-plan context, cross-phase coherence, user-language reports | W | Execution and inspector read the full plan; `common.md`/`foreman.md` own language and register. | S1 |
| 5.14.0 | Structured closing report and comprehension probe | W/X | Reporting register and path-loaded `judges/report-judge.md`; Codex renderable file/chat fallback. | S1 |
| 5.15.0 | User chooses conversation language; persisted canon English | W | `refs/common.md`; unchanged. | S1 |
| 5.16.0 | QA checklist page and selectable review depth | W/X | `contracts.md`, `quality-check`; QA page uses `<transport>-qa.html`, rendered in Codex when possible, chat fallback otherwise. | P1, S1 |
| 5.17.0 | New-callable markers, naming map, close-phase | P/W | `naming-review.md`, `close-phase`, shared markers and one phase commit. | S1 |
| 5.17.1 | Foreman supervises but does not execute phases | W | `foreman.md`, `execute-phase`, `resume-workflow`. | S1 |
| 5.18.0 | Interactive `clarify?` routes ambiguity through foreman | P/X | Disk-first decision in `notes.md`, optional explicit Codex task message, child confirmation. | P1 |
| 6.0.0 | Claude plugin renamed to `wf` namespace | C | Claude command-prefix packaging is inapplicable. Codex exposes `codex-phased-workflow:<skill>` while keeping `.phased` unchanged. | S1 |
| 6.0.1 | Field-tested clarify reply/permissions | X/C | Codex uses explicit task tools where discoverable and file-backed decisions otherwise; no guessed Claude session permission. | P1 |
| 6.0.2 | Clarify survives dead reply via committed notes | P/W | `foreman.md` disk floor and plan/notes authority. | P1 |
| 6.0.3 | Self-titling and session lookup | X/C | Codex can title/list tasks through product tools; absent tools degrade to portable title plus disk. Claude `list_sessions` is not used. | S1 |
| 6.1.0 | Human `Verify: now` holds phase open | P/W | `[>]` plus `Testing:`, `execute-phase`, `close-phase`, `contracts.md`. | P1, D1 |
| 6.2.0 | Board becomes read-only strip | W | `refs/board.md`; textual fallback remains complete. | S1 |
| 6.2.1 | User rejection does not turn green work into `[!]` | P/W | `close-phase`, `phase-execution.md`; result closes `[x]` with `Review:` and returns to planning. | P1 |
| 6.3.0 | Rejected result re-plans untouched tail | P/W | `resume-workflow` rejected-result path; closed phase remains durable. | P1 |
| 6.4.0 | Long-phase handoff and tool-availability discipline | W/X | `phase-execution.md`; Codex checks available tools and records WIP rather than inferring absence. | S1 |
| 6.5.0 | Closed-short phase and remainder re-planning | P/W | `close-phase`, `phase-execution.md`, `resume-workflow`. | P1 |
| 6.6.0 | Interactive versus unattended repair split | P/W/X | `repair-phase` and `repair-phase-agent`; autonomous launcher permits one repair. | O1 |
| 6.7.0 | Stop-loss, help map, workflow lessons | W | `help`, execution/repair doctrine, `foreman.md` lessons. | S1 |
| 6.7.1 | Repair-in-progress is explicit | P | `Repair started:` note and resume/repair semantics. | P1 |
| 6.8.0 | Plan-authored executable/skeleton contract tests | P/W | `contracts.md`, planning, execution, doctor, close. | P1, S1 |
| 6.9.0 | Doctor coherence audit and blind retrofit | W | `doctor`; blind author now reports its `READ:` set. | S1 |
| 6.10.0 | Future-consumer `Must not break:` contract | P/W | `contracts.md`, planning, doctor, execution/finalization. | P1 |
| 6.10.1 | Unattended path receives future-consumer contract | W/X | Codex never uses Claude light mode: even `low` runs the full Sol skill and reads the same header/roadmap. | P1 |
| 6.11.0 | Rolling-wave mini-scopes and coherence judge | P/W | `write-workflow-autonomous.md`, roadmap format, itinerary/contract return shapes. | D1, S1 |
| 6.12.0 | Producer-to-consumer contracts cross intermediate macros | P/W | `contracts.md`, autonomous planning, quality/finalization coherence. | S1 |
| 6.12.1 | Session budget cannot starve resumed/repair work | W/X | `run-workflow.sh` bounds attempts separately from landed phases and checks final state before exhaustion. | O1 |
| 6.13.0 | Sonnet removed from authored palette, legacy accepted | P/X | `next-phase.py` accepts it; planning authors `opus`/`fable`; Codex still runs Sol. | P1 |
| 6.14.0 | Doctrine split by consumer | W | `refs/common.md`, `contracts.md`, `foreman.md`; direct citations only. | S1 |
| 6.15.0 | Messaging channel floors declared | X/C | `foreman.md` declares Codex task/subagent, explicit product message, then disk; Claude CLI version floors are not copied. | S1 |
| 6.16.0 | Skill doctrine closure has a 1,500-line budget | W | Ported `tests/check_doc_mass.py`; current largest closure is below the ceiling. | S1 |
| 6.17.0 | Plan-defect claim consult before repair | P/W/X | Claim notes remain portable; Codex launcher waits on `<transport>-foreman-answer`, defaulting to repair on timeout. | O1 |
| 6.18.0 | Quality check split from finalization and stamped | P/W | `quality-check`, `quality-check-agent`, `finalize-workflow`, stamp in `contracts.md`. | P1, S1 |
| 6.19.0 | Minimality prevention and detection | W | Existing contract/verifier/naming-review doctrine; path-loaded verifier keeps the check fresh. | S1 |
| 6.20.0 | Interrupted unattended run is diagnosable at resume | W/X | `resume-workflow` reads selector-derived external run/attempt logs and offers reset + relaunch; landed logs stay beside plan. | O1 |

## Release matrix: 6.21.0 through 6.28.7

| Claude release | Shipped behavior | Class | Codex implementation and status | Verification |
|---|---|---:|---|---|
| 6.21.0 | Negative contract assertions checked against every other phase at planning and after landing | W | `write-workflow-autonomous.md` adds the whole-plan sweep; `run-workflow` inspector re-checks cross-phase law after each landed phase. | O1, S1 |
| 6.22.0 | Finish in-flight phase then stop; stale request removal; `RUN_WORKFLOW_MAX_PHASES` counts landings | W/X | `run-workflow.sh` uses selector-derived stop file, removes stale controls at start, checks between sessions, validates numeric budget. | O1 |
| 6.23.0 | Third plan-defect answer `apply`, bounded by exact before→after and outcome timeout | P/W/X | `foreman.md`, `contracts.md`, `run-workflow` skill/script; `Applied:` is a known portable note. Green continues without repair; red/timeout falls through. | P1, O1 |
| 6.24.0 | Namespaced judge prompts, bounded fan-outs/return formats, fixed 16-agent panel, agent-session timeout, audited doctor blindness | W/X | Codex loads shipped files under `judges/` rather than named Claude agents; `execute-phase`, planning refs, `quality-check`, `doctor`, and bounded `agent-session.sh` implement the neutral behavior. Claude namespace resolution and preset-steering cleanup are C. | O1, S1 |
| 6.25.0 | Optional secure dashboard; authenticated reads; server proposes but never acts; checks are read-only | W/X/C | New `dashboard` skill and `scripts/wfdash/`; the Claude visual shell and portable interactions are copied intact. Claude transcript/session/todo/cost inputs are C and render explicit unavailable states. | D1–D3, S1 |
| 6.26.0 | Per-port cookie, aged one-run dedup, process-safe queue, single selector reader, hardened credential handling, tags and five-way recommendation | W/X | `server.py`, `outbox.py`, `core.py`, `index.html`; plan parsing comes only from `next-phase.py --json`. | D1–D3 |
| 6.26.1 | Authenticated registry reuse/stale cleanup; atomic dedup; private queue; latest finalized plan chosen by commit time | W/X | Owner-private Codex registry, authenticated probe/one-shot, one locked `append_if_absent`, `0600/0700`, branch-resident latest closed plan in `core.py`. | D1–D3 |
| 6.27.0 | Row-set/UI intent decisions; refusal layer; deployment-tier ordering; author-time lint; origin diff for tests/fields; valid final config row | P/W | Planning/scope refs and skills updated; close checks plan commit; contract ownership explicit; template row is `Phase N+1`. Claude light-mode prohibition is C because Codex has no light worker—`low` still loads full Sol doctrine. Claude `SendUserFile` is replaced by Codex rendering/chat fallback. | P1, S1 |
| 6.28.0 | Contract-field extractor; light-contract preflight; dashboard re-owner; per-uid transport; exact threat model | P/W/X/C | `next-phase.py --contract-block`, close gate, `server.py --probe -O`, per-uid private transport and docs. Light-contract preflight is unnecessary in Codex's always-full worker. | P1, D3, S1 |
| 6.28.1 | Autonomous `Pattern reference:` protected; shell transport `0700`; plan commit from HEAD; owner-filtered queue | P/W/X | Extractor accepts both pattern spellings, shell uses `install -d -m 700`, close searches plan addition on HEAD, outbox partitions by Codex owner. | P1, D2 |
| 6.28.2 | Repo-keyed transport; drain returns one-lock served/remaining partition; explicit liveness semantics | W/X | `next-phase.py --transport` keys checkout root; `drain_split` returns its transaction's two halves. Codex does not infer task liveness from a pid; orphan recovery uses the exact stamped thread id after user confirmation. | P1, D2 |
| 6.28.3 | Orphan recovery must not bare-drain; partition result cannot race a second read | W/X | `dashboard` prescribes exact-owner recovery; `drain_split` computes both halves under one lock. | D2, S1 |
| 6.28.4 | Queue owner strengthened beyond recycled pid; copied one-shot link explains itself | X/C | Codex uses stable `CODEX_THREAD_ID`, not a process pid/session pair; replayed page URL returns an explanatory locked page while APIs stay JSON. | D2, D3 |
| 6.28.5 | Owner identity retained from validation; dead owner does not silently become a recycled process; explicit orphan recovery | X/C | One immutable thread-id owner stamps page and queue; no pid re-resolution exists. Exact-owner drain provides explicit recovery. Codex cannot locally prove task liveness, so the user confirms orphan status. | D2, D3 |
| 6.28.6 | Owner stored atomically; legacy pid-only event recovery | X/C | A Codex owner is already one immutable string. Codex queue filenames are separate, so Claude legacy pid events are never consumed; no compatibility shim is needed. | D2 |
| 6.28.7 | Page owner and queue stamp share one validated resolution | X/C | `Handler.owner` is the single value used by `/api/state`, queue display, and every stamp. Claude `live_owner()` session-record reconciliation is inapplicable because no supported Codex local session registry exists. | D2, D3 |

## Intentional runtime divergences

1. **No live transcript, internal todo, or dollar-cost feed.** Their original
   panels remain present, but Codex has no stable plugin API for the
   Claude-local data. They show explicit unavailable states; the Foreman panel
   mirrors the durable proposal queue. Private Codex storage and unstable
   app-server schemas are not scraped.
2. **Dashboard buttons cannot wake an idle Codex task.** They queue a task-owned
   proposal. The user invokes `dashboard` again, or a live `run-workflow`
   inspector drains it. The server never gains workflow authority to hide this
   platform boundary.
3. **Owner identity is `CODEX_THREAD_ID`, not pid plus Claude session id.** It is
   ephemeral transport state, never committed. Codex provides no supported
   local liveness record, so orphan recovery is explicit and user-confirmed.
4. **No Claude light mode.** Every Codex implementation, repair, verifier, and
   review worker stays on `gpt-5.6-sol` and loads the full relevant skill even
   at low effort; the Claude-only light-contract failure mode cannot occur.
5. **Judge packaging is path-based.** Claude resolves namespaced agent manifests;
   Codex loads the shipped prompt under `judges/` into a fresh Sol subagent.
6. **Sandbox differs.** Autonomous Codex workers run `workspace-write` and never
   auto-approve escalation. External effects retain their own authority gate.

None of these differences changes the committed plan layout, marker lifecycle,
notes, model labels, contract tests, quality stamp, repair outcome, or phase
commit shape. Plans produced by either implementation remain readable and
resumable by the other without translation.
