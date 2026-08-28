# Installation

## Requirements

- Codex CLI and the Codex app signed into the same account.
- Git available on `PATH`.
- A recent Codex build with plugin marketplace support.

## Install from GitHub

```bash
codex plugin marketplace add fporcari/codex-phased-workflow
codex plugin add codex-phased-workflow@codex-phased-workflow
```

Restart the Codex app. Then ask Codex:

```text
Use resume-workflow and tell me whether this repository has an active phased plan.
```

If no plan exists, start with `write-workflow` after discussing the work. For a
decision-heavy idea, use `scope-workflow` first.

The optional local dashboard needs no additional package. Invoke `dashboard`
inside a repository to open it in Codex's browser panel. The textual workflow
remains the fallback and the dashboard is never required; see
[wfdash](wfdash.md) for its proposal and security boundaries.

## Verify the installation

```bash
codex plugin list
codex plugin marketplace list
```

Both lists should contain `codex-phased-workflow`.

## Update

Refresh the marketplace snapshot, then reinstall the plugin:

```bash
codex plugin marketplace upgrade codex-phased-workflow
codex plugin remove codex-phased-workflow@codex-phased-workflow
codex plugin add codex-phased-workflow@codex-phased-workflow
```

Restart Codex after updating.

## Continue work from Claude Code

Open the same repository and branch in Codex. Do not convert `.phased/` or edit
its model labels. Invoke `resume-workflow`; it validates the existing plan and
names the next safe skill.

The reverse handoff is identical: commit or durably record the current phase,
open the same branch in Claude Code, and run its `resume-workflow` command.

## Uninstall

```bash
codex plugin remove codex-phased-workflow@codex-phased-workflow
```

Uninstalling the plugin does not touch any repository's committed `.phased/`
state.
