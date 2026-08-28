# wfdash for Codex

`wfdash` is a localhost view of the portable `.phased/` record. It composes the
JSON produced by `next-phase.py` with roadmap state, `wf:` commits, committed
worker logs, and the current launcher's owner-private external log.

The HTML/CSS shell is copied from the Claude 6.28.7 dashboard. Codex-specific
changes are confined to command wording, task ownership, proposal transport,
and unavailable host telemetry.

The server is deliberately unprivileged:

- it binds only to `127.0.0.1`;
- every request requires a per-process token;
- a single-use URL exchanges its key for an `HttpOnly`, `SameSite=Strict`
  cookie;
- writes reject non-local origins and bodies over 64 KiB;
- registry and queue files are mode `0600` inside a mode `0700` directory;
- it never spawns Codex, edits the plan, sends task messages, or persists
  verification ticks.

Buttons append proposals to a Codex-specific JSONL outbox. `CODEX_THREAD_ID`
stamps ownership, and drains partition atomically so one task cannot consume
another task's request. Ownerless proposals require explicit adoption.

The server registry and outbox use `-codex-` names. They cannot collide with or
be consumed by the Claude dashboard even when both products watch the same
checkout.

## Run by hand

```bash
python3 server.py -C /path/to/repository -O "$CODEX_THREAD_ID"
python3 server.py --probe -C /path/to/repository -O "$CODEX_THREAD_ID"
python3 outbox.py -C /path/to/repository --drain --owner "$CODEX_THREAD_ID"
```

Use the `/dashboard` skill in normal operation: it owns server reuse, browser
opening, and the proposal gate.

## Intentional product boundary

Claude's dashboard can inspect local Claude transcript JSONL, todo files,
session records, and model-specific token prices. Codex provides no stable
plugin API for those feeds. This port does not scrape private Codex storage or
bind to unstable app-server schemas. The corresponding panels remain in their
original positions and show an explicit unavailable state; the Foreman panel
mirrors the Codex proposal queue. Plan, lifecycle, verification, alerts, logs,
and safe proposal behavior remain available.
