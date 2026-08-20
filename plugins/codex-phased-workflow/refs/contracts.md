# The contract layer — what a phase owes and to whom

The verification and contract sections of the shared conventions, split out
so that only their consumers pay for them: planning (`/write-workflow`),
execution (`/execute-phase`, `/execute-phase-agent`), the close
(`/close-phase`), the audit (`/doctor`) and the consolidation
(`/quality-check`, `/finalize-workflow`) read this file; the purely operational skills do not.
Core conventions stay in `refs/common.md`; the chat hierarchy and messaging
in `refs/foreman.md`.

## Verification: `Done:` and `Verify:`

Two fields, two audiences. **This section is the single source of the
contract** — the skills cite it, they never restate it.

- **`Done:`** — the machine's exit condition: tests, lint, build, a named
  output. Re-runnable verbatim by whoever reads the plan next. It stays
  machine-checkable in both modes; `/execute-phase-agent` re-runs it before
  closing a phase.
- **`Verify:`** — steps a *person* performs, each with the result they should
  see. Never a substitute for a weak `Done:`: a phase whose tests could have
  covered it does not get to push the work onto the human.

**Every `Verify:` step carries a *when*:**

- `now` — check it at the end of this phase; it makes sense on its own.
- `deferred: needs Phase M` — it only makes sense in a wider context, so it is
  **dated, not skipped**.

A `now` step also **gates the close in interactive mode**: the phase commits
its work and stays `[>]` until the human has run those checks — the mechanic
is in `refs/phase-execution.md` → *Awaiting the human's checks*. Autonomous
mode has nobody to wait for and closes as before.

```
  > Verify: now — open /foo, save a row, it reappears in the grid after reload
  > Verify: deferred: needs Phase 5 — the invoice total matches the order once
    the pricing phase lands
```

**One contract, two origins.** A `Verify:` step is either **authored in the
plan** (a field on the phase, written by `/write-workflow`) or **surfaced at
execution**. The executing skill carries the authored ones into its
end-of-phase `> Verify:` notes exactly like its own — deferred ones into
`verify.md` — so the QA pass reads ONE list and an authored check can never
fall between the two syntaxes.

**Split by who can check it.** What an agent can assert never reaches the human
list: the flow works, the record persists, the grid reloads — that is what a
browser-driving skill (`ui-test` where installed; it ships separately, not with
this plugin) exercises. **No such skill available → declare it, and hand
exactly those checks to the human as `Verify: now` steps** — a named fallback,
never a silent skip. The human list otherwise carries only what needs human
judgment: aesthetics, "is this interaction right?", UX ambiguity.
Without this split the list fills with automatable work and stops being read.

**Browser verification and logins.** Before driving any browser check,
establish whether the target is login-gated — always, as the first step. When
it is, the login is performed by the **human operator** in the visible browser
window, every time: the executing agent never types, logs, or persists
credentials, whatever impersonation convention the project offers (those
conventions belong to the browser-driving skill, never to this plugin). One
login per session usually suffices — the cookie persists across iterations.

**The mockup is the visual contract** of a `ui`-tagged phase: approved at the
phase's gate, saved as `mockups/phase-N.html` in the plan directory, committed
with the phase. The browser pass screenshots the real page next to it, and a
fresh-context judge (the `ui-judge` agent) compares the two — because the
author of a UI is the worst judge of its own fidelity. What the judge flags as
a human call lands in `> Review:`; what remains for human eyes (taste beyond
the mockup) stays on the `Verify:` list.

**Deferred steps accumulate in `verify.md`** in the plan directory, appended per
phase, and `/quality-check` presents the file as one QA pass at the end
instead of scattering checks the user cannot yet perform.

**The QA pass is delivered as a QA page** where the session can render a file
to the user (SendUserFile on the desktop): a manual test plan written outside
the repo (`${TMPDIR:-/tmp}/phased-workflow/<slug>-qa.html` — a file in the
tree would dirty it), one checkbox per check, grouped by phase, each item
naming the action to exercise and the result the user should see — the
reporting register (`refs/foreman.md`) applies. A deferred step whose phase has since landed is
marked as now due. The checkboxes are the user's own tracking while they work
through the list — purely client-side, nothing reports back to the session:
the presenting skill still asks its one question about the outcome afterwards.
It is a work sheet, not a closing report, so the report-judge gate does not
apply to it. Without a way to render the page (CLI, headless), degrade
declared: the same list in chat, grouped by phase.

The mechanism is **thick in interactive mode and thin in autonomous, never
absent**: an autonomous project startup still wants human eyes on the result.

**Authored checks are foreman-owned.** After the plan commit, the contract
fields — `Done:`, the authored `Verify:` steps, the contract tests where the
plan carries them — belong to the plan's author, never to the phase executing
them. On a `ui` phase the authored `Verify:` list is written COMPLETE at
planning time: the checks the human will run at that phase are pre-established
in the plan, not improvised at the gate — the mockup loop refines the look,
never the checklist. The executing chat may ADD surfaced steps — an addition
strengthens the contract — but never drops or rewords an authored one on its
own: a check that no longer fits is a plan ambiguity, routed through the
foreman (`clarify?`), whose reply carries the edit. The sanctioned protocols
that already reshape the contract — closed short, a rejected result — keep
working as written: both report to the foreman by construction.

`verify.md` and `review.md` are siblings, not duplicates: `review.md` says
*"here is what I noticed and will not decide for you"* — the user reads and
judges; `verify.md` says *"here is what you must exercise"* — the user does.

## The quality-check stamp

The fact that the quality work ran, on disk where the closing skill can read
it. **This section is the single source of the stamp** — the two skills cite
it, they never restate it. `/quality-check` appends it to `plan.md` under a
`## Quality check` heading (created on first use, one line per run — the
last line governs) and commits it alone as `wf: quality check — <depth>`:

```
> Quality check: <ISO timestamp> — commit <short HEAD hash> — review <extended|light|panel|none|agent>, QA <done|declined|none>, findings <N confirmed, M dismissed | none>
```

The stamp records outcomes, never grants: a declined QA and a `none` review
are stamped too — facts, not omissions. The `commit` hash is HEAD at stamp
time; `/finalize-workflow` gates on the stamp and treats commits landed
after the stamp's own commit as staleness — the check saw a tree that no
longer exists. Missing or stale, finalize asks ONE question: run
`/quality-check` first (recommended), or close without it with the price
stated. It never runs the quality work itself.

## Contract tests — the executable contract

An option `/write-workflow` puts to the user: the tests of EVERY phase are
authored at planning time, while the whole design sits in one context, and
committed with the plan under `.phased/active/<slug>/tests/phase-N/`. Each
such phase's `Done:` opens with them. **This section is the single source of
the contract** — the skills cite it, they never restate it.

What the tests buy is bindingness: a later phase's premise stops being prose
an executor may skim and becomes a red test the phase cannot close over.
Recommended where the work is refactoring or otherwise well-specified —
behaviour that must survive is exactly what a test states best; on
exploratory work prefer skeletons (below) over guessed signatures.

**Each test is authored at one of two precisions**, chosen per test by how
settled the surface is:

- **Executable** — the design already fixes the signatures (a refactor: they
  exist today). Real, runnable test code. Read-only for the child in its
  entirety.
- **Skeleton** — the behaviour is decided, the bindings are not. A named test
  whose contract is stated in comment lines carrying the `wf:contract:`
  marker, with a red body (`pytest.fail("phase N pending")` or the repo
  equivalent):

  ```python
  def test_invoice_total_survives_rename():
      # wf:contract: renaming legacyAmount -> amount keeps invoice.total()
      # wf:contract: equal to the sum of its lines after reload
      pytest.fail("phase 3 pending")
  ```

  The child replaces the red body with a real implementation of exactly what
  the `wf:contract:` lines state; the test name and those lines are
  read-only. Red by construction either way: no phase closes over an
  unimplemented contract, and no signature gets guessed at planning.

The rules, in both execution modes:

- **The phase copies its own tests verbatim** from `tests/phase-N/` into the
  repo's test tree at phase start, and implements until they are green. The
  copy — and a skeleton's body — is the phase's work; the contract is not.
- **The contract is read-only for the child.** A test that cannot pass as
  written — a wrong premise, an assertion the design outgrew — is a plan
  ambiguity, never a local fix: interactive phases route it as `clarify?`
  (`refs/foreman.md` → *The foreman*), and the foreman's reply carries the exact test edit as
  before-text → after-text, applied verbatim by the child and committed as
  `wf: clarify phase N — <one line>`. Unattended phases have nobody to ask
  mid-phase: the phase closes `[!]` with `> Issue: plan-defect claim — <the
  test, the premise it believes wrong, and the exact edit it thinks the plan
  needs>` — the words `plan-defect claim` verbatim, they are what the
  launcher's consult gate greps for (`refs/foreman.md` → *Plan-defect
  claims*). A **claim, never a verdict**: the first field run made it twice
  and was wrong twice — the "impossible" contract was implementable
  in-dialect both times, and the repair found the better design. The claim
  is judged upstream — the foreman through the gate, or fresh repair eyes on
  its timeout — and in no case by editing the contract.
- **The close verifies the copy.** `/close-phase`'s Done gate (and the
  phase-verifier, where it runs) checks the in-tree copy against the plan
  copy: executable tests byte-identical; skeletons with their test names and
  every `wf:contract:` line surviving verbatim and no red body left. Any
  divergence must be covered by a foreman decision recorded in `notes.md`
  under the phase's `## Phase N` — a silent one blocks the close.

A plan without the option keeps today's behaviour: tests are written by each
phase, and the cross-phase direction is prose
(`refs/phase-execution.md` → *The plan is context*).

## Must not break: — contracts owned by the future

A plan header field, one line per constraint, recording what this workflow
must leave intact — including, on a programme split into macro-phases, what
a LATER macro-phase will require of the work built here. **This section is
the single source of the contract** — the skills cite it, they never
restate it.

The field exists because hindsight flows forward and constraints do not:
each macro is planned by its own `/write-workflow` after the previous one
landed, and nothing else carries a future consumer's requirements backwards.
The failure it answers is documented (issue #15): a data shape chosen
correctly for one macro's own scope could not carry what a macro planned
much later measured it needs — nothing destroyed, but the cost landed on
the wrong side of the programme.

- **Written by `/write-workflow` — the consumer question.** When
  `.phased/roadmap.md` has unstarted macro-phases (or the discussion names
  later work that will consume this plan's output), planning asks: *who
  consumes what this workflow builds, and what will they require of it?*
  The answer lands here; genuinely unknown is written as `Must not break:
  unknown — consumers not yet measured`, because an EMPTY field on a macro
  whose output another one consumes is itself a finding.
- **Backed by skeletons where it can be.** A future consumer's requirement
  is "behaviour decided, bindings unknown" by definition — the exact case
  `wf:contract:` skeletons exist for (*Contract tests* above). A constraint
  statable as behaviour is written as a skeleton in the plan's `tests/`,
  owned by the future macro but red against this one's work.
- **A contract lives from producer to consumer, across everything between.**
  The dependency structure of a programme is a graph, not a chain: Macro 5
  may require what Macro 2 builds, with other macros in between. The
  constraint therefore binds more than its producer — every macro between
  the one that builds the thing and the one that consumes it inherits the
  line into its own `Must not break:`, because what is **in transit** must
  not be lost by a leg it merely crosses. The tour version: you saw the
  Uffizi on the Italy leg in order to compare them with the Prado on the
  Spain leg — no leg in between may lose that luggage.
- **Read at execution.** `/execute-phase`'s compatibility line and the
  shared core's plan-is-context skim treat these lines — and, where a
  roadmap exists, its remaining macro-phases — as premises of the same rank
  as a pending phase's: a choice that breaks one goes up as `clarify?`
  before any approval.
- **Checked at the close of the macro.** `/quality-check`'s roadmap
  check compares what was built against this field and the roadmap's
  remaining macro-phases, and reports every shape a later macro would have
  to undo — the last cheap moment to act, since the next macro is planned
  against this commit.
- **Audited by `/doctor`, retroactively too.** A consumer measured late can
  be handed to the doctor as contract skeletons against the component that
  must serve it: the reds enumerate exactly which requirements the landed
  shape cannot carry.

## New-method markers and minimality

Two disciplines on every method or function a phase CREATES. They hold in
both execution modes; **this section is the single source of the contract**
(the review procedure lives in `refs/naming-review.md` — skills cite these
two, they never restate them).

**Minimality.** A phase introduces only the callables its objective and
`Done:` criterion require. A helper "for later", a speculative abstraction,
a second code path nothing exercises — that is scope the plan did not buy,
and the phase verifier reports it. When in doubt, inline the code: a future
phase can extract the helper the day two callers exist.

Minimality covers **surface and prose alike** — the named anti-patterns,
so no check has to re-derive them: accessor methods (setters/getters) for
attributes the language already exposes as public; wrapper methods that
only delegate; comments that narrate the line below them; docstrings that
restate the signature; defensive guards for states the code cannot reach.
Each is verbosity the plan did not buy. The measure of comment density is
the repo's own, never a general taste: match the surrounding files.

**The marker.** Every new method or function carries, on its definition
line, an end-of-line comment in the file's own comment token:

```python
def calc_totals(self):  # wf:phase-3:new
```

The name is a *proposal*: agent-chosen names are the part of a diff users
most often want to reword, so each one stays findable until a human has
ruled on it. Names that ARE framework API (dispatch by prefix or suffix, a
hook the framework matches literally) carry the marker too — they appear in
the review as fixed names, where only the free part, if any, can change.

The marker is scaffolding, like the `wf(phase N)` commits — it never
reaches the parent branch:

- **interactive runs** — `/close-phase` runs the naming review at the end
  of each phase; accepted or renamed, the markers die with the phase commit.
- **autonomous runs** — nobody can answer a naming question mid-run, so
  markers accumulate in the phase commits and `/quality-check` runs ONE
  naming review for the whole workflow before consolidating.

The sweep is blocking either way: before a phase commit closes the review,
and again before the workflow consolidates, a grep for `wf:phase-` over the
touched files must come back empty.
