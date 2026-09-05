#!/usr/bin/env bash
# Launch a bounded Codex worker for a plugin skill at the active plan's root.
set -uo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="$(cd "$script_dir/.." && pwd)"
skill_name="${1:?usage: agent-session.sh <skill-name>}"
skill_file="$plugin_root/skills/$skill_name/SKILL.md"
selector="$script_dir/next-phase.py"
session_timeout="${CODEX_AGENT_SESSION_TIMEOUT:-3600}"
model="gpt-5.6-sol"
if (( $# > 1 )); then
  if [[ $# != 3 || "$2" != "--model" ]]; then
    echo "usage: agent-session.sh <skill-name> [--model gpt-5.6-sol|gpt-6-astra]" >&2
    exit 2
  fi
  model="$3"
fi
case "$model" in
  gpt-5.6-sol|gpt-6-astra) ;;
  *) echo "Unsupported worker model: $model" >&2; exit 2 ;;
esac


if [[ ! -f "$skill_file" ]]; then
  echo "Unknown plugin skill: $skill_name" >&2
  exit 2
fi
if [[ ! "$session_timeout" =~ ^[0-9]+$ ]]; then
  echo "Invalid CODEX_AGENT_SESSION_TIMEOUT: $session_timeout" >&2
  exit 2
fi

plan="$(python3 "$selector" --resolve)" || exit 2
checkout="$(git -C "$(dirname "$plan")" rev-parse --show-toplevel)" || exit 2
transport="$(python3 "$selector" --transport "$plan")" || exit 2
if [[ "${PHASED_RUN_LOCK_PID:-}" != "$$" ]]; then
  exec python3 "$script_dir/runtime.py" lock "$transport-writer.lock" bash "$0" "$@"
fi
install -d -m 700 "$(dirname "$transport")"
log_file="$transport-$skill_name.log"
: >"$log_file"
chmod 600 "$log_file"

prompt="Use the $skill_name skill at $skill_file on the active portable plan at $plan. Follow its read/write limits exactly and return its specified machine-readable report."
codex exec --ephemeral -C "$checkout" \
  -m "$model" \
  -c model_reasoning_effort=high \
  -s workspace-write \
  "$prompt" >"$log_file" 2>&1 &
worker_pid=$!

watchdog_pid=""
if (( session_timeout > 0 )); then
  (
    elapsed=0
    while (( elapsed < session_timeout )); do
      sleep 1
      kill -0 "$worker_pid" 2>/dev/null || exit 0
      elapsed=$((elapsed + 1))
    done
    kill -TERM "$worker_pid" 2>/dev/null || true
    sleep 5
    kill -KILL "$worker_pid" 2>/dev/null || true
  ) &
  watchdog_pid=$!
fi

wait "$worker_pid"
status=$?
if [[ -n "$watchdog_pid" ]]; then
  kill "$watchdog_pid" 2>/dev/null || true
  wait "$watchdog_pid" 2>/dev/null || true
fi
sed -n '1,$p' "$log_file"
exit "$status"
