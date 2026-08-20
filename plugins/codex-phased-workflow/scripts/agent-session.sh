#!/usr/bin/env bash
# Launch a clean Codex worker for a plugin skill at the active plan's root.
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="$(cd "$script_dir/.." && pwd)"
skill_name="${1:?usage: agent-session.sh <skill-name>}"
skill_file="$plugin_root/skills/$skill_name/SKILL.md"
selector="$script_dir/next-phase.py"

if [[ ! -f "$skill_file" ]]; then
  echo "Unknown plugin skill: $skill_name" >&2
  exit 2
fi

plan="$(python3 "$selector" --resolve)"
checkout="$(git -C "$(dirname "$plan")" rev-parse --show-toplevel)"
log_dir="$(dirname "$plan")/log"
mkdir -p "$log_dir"

prompt="Use the $skill_name skill at $skill_file on the active portable plan at $plan. Follow its read/write limits exactly and return its specified machine-readable report."
codex exec --ephemeral -C "$checkout" \
  -m "${CODEX_REVIEW_MODEL:-gpt-5.6-sol}" \
  -c model_reasoning_effort=high \
  -s workspace-write \
  "$prompt" 2>&1 | tee "$log_dir/$skill_name.txt"
