---
name: dashboard
description: Open or resume the local wfdash view for portable phased-workflow state, and serve proposals queued for this Codex task.
---

# Dashboard

Open the optional local view of the current repository's phased workflows. The
page reads portable plan state and proposes actions; this skill remains the
authority boundary. A browser click never starts a worker or edits `.phased/`.

Read `<PLUGIN_ROOT>/refs/board.md` → *Optional live dashboard* once at start.

## 1. Identify the repository and owner

Resolve the git root. `CODEX_THREAD_ID` is the ephemeral owner of proposals
from this page. It never enters `.phased/`:

```bash
ROOT=$(git rev-parse --show-toplevel)
OWNER=${CODEX_THREAD_ID:-}
```

No owner means a read-only page whose proposals are deliberately ownerless.
Say so. Ownerless requests are never auto-adopted by another task.

## 2. Serve pending proposals

Before opening or refreshing the page, inspect the queue. With an owner, drain
only that owner's entries; without one, read but do not drain:

```bash
python3 "<PLUGIN_ROOT>/scripts/wfdash/outbox.py" -C "$ROOT" --drain --owner "$OWNER"
```

Show the drained proposals and ask for confirmation before serving any that
changes workflow state. Collapse duplicates. Route confirmed requests through
their owning skill:

- `run-workflow` → `/run-workflow`, including its preflight and launch gate;
- `stop` → if this task owns a live autonomous inspector, create the active
  plan's `<transport>-stop-request`; otherwise report that no owned run can be
  stopped here;
- `write-workflow` → `/write-workflow` with the queued description;
- `foreman` → treat the text as a message to the current foreman task when it
  is this task; otherwise use an explicit Codex task message only when the
  destination is discoverable, with committed plan state still authoritative.

Requests stamped for another task remain queued. An ownerless request is shown
separately and requires explicit adoption (`--include-unowned`) before drain.
If the user confirms that a stamped owner task is gone, recover only that
orphan with `--drain --owner <the exact owner value on the event>`; never use a
bare drain, which would consume every task's queue.

Codex has no supported way for a localhost page to wake an idle task. A click
therefore becomes visible when the user invokes `/dashboard` again or while a
live `/run-workflow` inspector is already draining the queue. State this once,
not as an error.

## 3. Reuse or start one server

Probe the owner-private registry first:

```bash
python3 "<PLUGIN_ROOT>/scripts/wfdash/server.py" --probe -C "$ROOT" -O "$OWNER"
```

A successful probe returns a fresh one-shot URL and re-owns proposals to this
task. Open that URL in Codex's browser panel.

If none answers, start the server in a persistent local terminal session — not
as a detached repository process — and read its first line for the one-shot
URL:

```bash
python3 "<PLUGIN_ROOT>/scripts/wfdash/server.py" -C "$ROOT" -O "$OWNER"
```

Open the reported `http://127.0.0.1:<port>/?k=<one-shot>` in the Codex browser
panel. Do not expose or repeat the registry token. The URL key is single-use;
run the probe again for another browser.

## Surface and limits

The page shows roadmap/plan hierarchy, phase markers, `Verify:` steps, notes,
workflow commits, alerts, durable logs, and the active launcher's external log.
All buttons queue proposals for this skill or `/run-workflow` to serve.

Keep the shipped Claude dashboard composition intact. Codex adaptations belong
in its command strings and data adapter, not in its layout, CSS, hierarchy, or
portable interactions.

Codex does not expose a stable plugin API for task transcripts, internal todos,
or priced token usage. Their panels remain visible with an explicit unavailable
state; Foreman uses the owner-scoped proposal queue rather than a transcript.
Never scrape Codex private storage or depend on app-server internals to fill
them.
