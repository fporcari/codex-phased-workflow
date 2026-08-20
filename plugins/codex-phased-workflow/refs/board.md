# The board — the plan, at a glance

One strip: a row per phase, its marker as the plan has it, the next phase
picked out. **Nothing on it is clickable.** It answers one question — where
does the work stand — and the answer is read, not operated.

It was a working view once: per-phase status pickers the user drove, a remarks
box on every card, a button that exported them as one prompt. That shape was
built when the chats could not talk to each other and a widget was the only
place to put a remark. They talk now (`foreman.md` → *The foreman*), so a
remark goes where remarks go — into the conversation, which keeps them,
carries them upward and can be argued with. Controls that die with the
message they were drawn in cannot compete with that.

## When it is drawn, and when it is not

- **`Mode: interactive` only.** On an autonomous plan, render nothing: the report
  stays text. There the next step is `/run-workflow`, a single launcher that owns
  every remaining phase.
- **Only where the `visualize` MCP server is available.** Absent → the same rows as
  a plain list. Declare the fallback, never fail silently; same rule as `ui-test`
  in `/execute-phase`.
- **Judgments stay prose.** Coverage, drift, oversizing, why a phase failed — those
  go in the reply where they can be read. A strip shows a position well and argues a
  finding badly.
- **Never on an incoming message**, whatever it carries. A foreman told that a phase
  closed — or that its result was rejected and the plan needs re-planning — answers
  with the delta (`foreman.md` → *The foreman*). The board is drawn when the **person**
  asks where the work stands, and after a re-planning is committed, once. Drawing it
  because the shape is *about to* change shows a position nobody will act on.

## The shape

- **One header line**: `done N / M`, the branch, the mode.
- **One row per phase**, in order: the marker (`[ ]` `[>]` `[x]` `[!]` `[~]`) as an
  icon, `Phase N: <title>`, and nothing else. A `[>]` row carries its age; a `[>]`
  waiting on the human's checks says so instead (`refs/phase-execution.md` →
  *Awaiting the human's checks*). An `[x]` whose result was rejected is marked as
  closed-with-a-problem, muted — its work stands, its design did not.
- **The next phase is the only emphasis** — the first unfinished row, with its
  `Run: <model> / <effort>` hint beside it, since both are chosen when that chat
  opens and reading them afterwards is too late.
- **The launch command appears once, under the strip, as text**: `/wf:execute-phase`.
  It takes no argument — the phase comes from the plan and the chat titles itself.

## Why nothing is clickable

`sendPrompt` is a widget's only channel and it writes into the chat you are in, so
a run button would run the phase in the supervision chat — the one place the
protocol says must not execute. A refresh button could only re-run the whole skill
and print a second report below: a recomputation dressed as an update. And a
`spawn_task` chip does open a session of its own, but its UI decides how — including
a *new worktree* for a plan that already has a branch and a checkout, with no
parameter to prevent it.

The strip is an accurate snapshot of the moment it was asked for. Ask again and a
new one is drawn.
