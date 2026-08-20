#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
plugin="$repo_root/plugins/codex-phased-workflow"

bash -n "$plugin/scripts/agent-session.sh" "$plugin/scripts/run-workflow.sh"
python3 -m py_compile "$plugin/scripts/next-phase.py" "$repo_root/tests/test_protocol.py"
python3 -m unittest discover -s "$repo_root/tests" -p 'test_*.py' -v
python3 -m json.tool "$plugin/.codex-plugin/plugin.json" >/dev/null
python3 -m json.tool "$repo_root/.agents/plugins/marketplace.json" >/dev/null

skill_validator="$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py"
if [[ -f "$skill_validator" ]]; then
  for skill in "$plugin"/skills/*; do
    python3 "$skill_validator" "$skill"
  done
fi

plugin_validator="$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py"
if [[ -f "$plugin_validator" ]]; then
  python3 "$plugin_validator" "$plugin"
fi
