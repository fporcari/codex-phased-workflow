# Auto-mode permission scope

Read by the two skills that decide whether a phase can run unattended:
`/run-workflow` (pre-flight) and `/write-workflow` on the autonomous branch
(`write-workflow-autonomous.md`). No other skill needs it.

Sub-sessions launch with `codex exec --sandbox workspace-write` and no automatic
escalation approval. This plugin ships no hooks or exec-policy overrides. An
operation outside the sandbox stops the worker. The list below is the convention for autonomous phase
design, not a claim that the plugin can enforce every boundary.

Under that mode, routine local operations in project scope (git
status/log/diff/show, edits in the working directory, and targeted tests) are
in scope. These categories must be left out of autonomous phases unless the
user separately authorizes them:

- any push, merge, release, or pull-request mutation;
- any new dependency. Existing manifest-driven bootstrap is allowed only when
  the plan names it and the user approved the autonomous run;
- destructive cleanup, history rewriting, or overwriting unrelated files;
- production deploys, database migrations against shared environments, SSH,
  or infrastructure mutations;
- downloading and executing unreviewed code;
- self-modification of agent configuration;
- secrets, data exfiltration, public repository creation, or writing to
  external systems.
