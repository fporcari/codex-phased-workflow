# wfdash

`wfdash` is an optional local view of a phased workflow. The normal textual
`resume-workflow` report remains complete; the dashboard is not required to run,
repair, close, or move a plan between Claude and Codex.

Invoke `dashboard` in a Codex task attached to the repository. The skill reuses
the repository's live server when one exists, otherwise starts it in a local
terminal, then opens the one-shot URL in Codex's browser panel.

## What it shows

- the same visual shell, navigation, hierarchy, phase panes, plan renderer,
  creation dialog, and proposal controls as the Claude dashboard;
- the roadmap, local and branch-resident plans, and the latest closed plan;
- a conditional **Done** tab for finalized workflows not declared by the
  current roadmap; closed macros in the current roadmap stay in **Plan**;
- every phase marker, portable tag, run hint, note, and human `Verify:` step;
- the selector's exact five-way recommendation;
- `wf:` lifecycle commits, durable worker logs, and an interrupted launcher's
  external log;
- failed, blocked, stale-running, and ownerless-request alerts.

Selecting a phase opens its verbatim plan block. Verification rows are a read
of the plan, not a second checklist: nothing the browser ticks can close a
phase.

Plan and roadmap text are cached for reading stability, then invalidated when
their own filesystem mtime changes. The existing text stays visible until the
replacement fetch lands; branch-only plan text has no local mtime and retains
the stable one-fetch behavior.

## Proposal buttons

The server has no workflow authority. The original dashboard controls append
proposals to an owner-private Codex outbox:

- **Command for phase** returns `execute-phase` as text for a fresh task;
- **Ask for an unattended run** proposes `run-workflow`, whose skill still owns preflight,
  authorization, model, sandbox, monitor, and plan-defect handling;
- **Create workflow** proposes `write-workflow` with the entered name and scope;
- **Foreman** writes to the owning task's durable proposal queue.

`CODEX_THREAD_ID` stamps the proposal for the task that opened or most recently
reused the page. A task drains only its own entries. Ownerless entries are
visible but need explicit adoption, and another task's entries remain queued.

A localhost page cannot wake an idle Codex task through a supported plugin API.
After pressing a button, invoke `dashboard` again to serve the proposal, unless
a live `run-workflow` inspector is already draining the queue. This is a
declared handoff, not a silent failure.

## Security boundary

The server binds to `127.0.0.1`. Every request, including reads, requires a
per-process token. A URL key authenticates one load and becomes an `HttpOnly`,
`SameSite=Strict` cookie; open another pane by invoking `dashboard` again, not
by copying a spent link. Writes reject foreign origins and bodies over 64 KiB.

Registry and queue files are mode `0600` in a mode `0700` per-user transport
directory. This keeps out other machines, browser origins, and UNIX users. It
does not protect against another process running as the same user, which can
already read that user's repository and local files.

## Codex-native limits

Claude's dashboard reads Claude-specific transcript JSONL, session records,
todo files, and model price tables. Codex exposes no stable plugin API for
equivalent task transcripts, internal todos, or priced token usage. This port
does not scrape private Codex storage or depend on unstable app-server schemas.
The original Active, Off plan, Foreman, todo, and cost surfaces remain in the
same layout: unavailable telemetry renders as `—` or an explicit empty state,
while Foreman proposals use the owner-scoped Codex queue instead of a Claude
transcript channel.

The nearest stable Codex equivalent is the durable view above: plan and roadmap
state, commits, notes, verification, worker logs, active launcher events, and a
task-owned proposal queue. Those are also the facts another product or machine
can resume.
