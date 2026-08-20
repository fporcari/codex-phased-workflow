---
name: run-workflow
description: Run every remaining phase autonomously in a fresh high-quality Codex session per phase, preserving the portable .phased protocol and stopping on unresolved failures or blocked work.
---

# Run workflow

Run the remaining phases through `<PLUGIN_ROOT>/scripts/run-workflow.sh`. Each
phase and repair gets a fresh ephemeral `codex exec` session using
`gpt-5.6-sol`. The plan's effort is honored; the implementation model never
drops below Sol.

## Pre-flight gate

1. Resolve and validate the active plan:

   ```bash
   python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --resolve
   python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --validate
   ```

2. Require `Mode: autonomous`. An interactive plan must be refined first.
3. Read every phase. Reject unresolved decisions, non-measurable `Done:`, and
   destructive or externally consequential actions that cannot safely run under
   Codex `workspace-write` without an escalation.
4. Preserve the compatibility model labels in the plan. `opus` and `fable` are
   portable protocol vocabulary shared with Claude; Codex maps both, plus any
   legacy `sonnet`, to `gpt-5.6-sol`. Effort remains `low|medium|high|xhigh|max`.
5. Show the final phase list and the runtime mapping. End with the explicit
   launch gate: “Launch? On your ok the autonomous run starts over all remaining
   phases.” Do not start before that answer.

## Launch

Run in the foreground when no durable monitor is available:

```bash
bash "<PLUGIN_ROOT>/scripts/run-workflow.sh"
```

The launcher emits `EVENT:` lines and writes logs beside the active plan. Report
phase completion, the first failure, every blocked phase, and the final outcome.
Do not infer success from process exit alone: read the plan markers afterward.

## Stop conditions

- all phases are `[x]`;
- a phase remains `[!]` after one fresh repair and carries
  `> Repair attempted:`;
- a phase is `[~]` because the baseline failure cannot be attributed;
- Codex exits non-zero;
- a session returns without changing the expected durable state;
- the configured maximum phase count is reached.

Never merge, publish, deploy, delete user data, or perform another external
side effect merely because the workflow is autonomous. Those actions still need
their own explicit authority.
