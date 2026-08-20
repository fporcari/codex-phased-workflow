#!/usr/bin/env bash
# Run a portable .phased workflow with one fresh Codex session per phase.
set -uo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="$(cd "$script_dir/.." && pwd)"
selector="$script_dir/next-phase.py"
phase_model="${CODEX_PHASE_MODEL:-gpt-5.6-sol}"
max_phases="${RUN_WORKFLOW_MAX_PHASES:-100}"

plan="$(python3 "$selector" --resolve)" || exit 2
python3 "$selector" --validate "$plan" || exit 2
checkout="$(git -C "$(dirname "$plan")" rev-parse --show-toplevel)" || exit 2
plan_dir="$(dirname "$plan")"
mkdir -p "$plan_dir/log"

phase_count() {
  local marker="$1"
  grep -cE "^- \\[$marker\\] \\*\\*Phase" "$plan" 2>/dev/null || true
}

recommendation() {
  python3 "$selector" "$plan" | awk -F'recommendation: ' '/^recommendation: / {print $2}'
}

phase_effort() {
  local number="$1"
  local effort
  effort="$(awk -v number="$number" '
    $0 ~ "^- \\[.\\] \\*\\*Phase " number "\\*\\*:" {inside=1; next}
    inside && /^- \[.\] \*\*Phase / {exit}
    inside && /Run:/ {
      line=$0
      sub(/^.*Run:[[:space:]]*/, "", line)
      n=split(line, parts, /[[:space:]]*\/[[:space:]]*/)
      if (n > 1) {gsub(/[^a-z]/, "", parts[n]); print parts[n]; exit}
    }
  ' "$plan")"
  case "$effort" in
    low|medium|high|xhigh|max) printf '%s\n' "$effort" ;;
    *) printf 'high\n' ;;
  esac
}

phase_has_note() {
  local number="$1"
  local note="$2"
  awk -v number="$number" -v note="$note" '
    $0 ~ "^- \\[.\\] \\*\\*Phase " number "\\*\\*:" {inside=1; next}
    inside && /^- \[.\] \*\*Phase / {exit}
    inside && index($0, "> " note ":") == 1 {found=1}
    END {exit found ? 0 : 1}
  ' "$plan"
}

run_codex() {
  local prompt="$1"
  local effort="$2"
  local log_file="$3"
  codex exec --ephemeral -C "$checkout" \
    -m "$phase_model" \
    -c "model_reasoning_effort=$effort" \
    -s workspace-write \
    "$prompt" 2>&1 | tee "$log_file"
  return "${PIPESTATUS[0]}"
}

run_phase() {
  local number="$1"
  local effort
  local prompt
  effort="$(phase_effort "$number")"
  prompt="Use the execute-phase-agent skill from $plugin_root/skills/execute-phase-agent/SKILL.md. Execute exactly Phase $number of the active portable plan at $plan. Preserve the .phased protocol exactly. Finish with exactly one durable outcome: the phase becomes [x] with Done and Files notes and one phase commit; it becomes [!] with Issue and Attempted notes; an attributable earlier regression reopens its owning phase as [!]; or an unattributable red baseline marks Phase $number [~] with a Blocked note. Demonstrate Done with tests and lint actually run. Do not start another phase."
  echo "EVENT: phase-started:$number:model=$phase_model:effort=$effort"
  run_codex "$prompt" "$effort" "$plan_dir/log/phase-$number.txt"
}

run_repair() {
  local number="$1"
  local prompt
  prompt="Use the repair-phase-agent skill from $plugin_root/skills/repair-phase-agent/SKILL.md. Repair exactly the first [!] phase in the active portable plan at $plan. Preserve the .phased protocol. Finish with [x] plus a Repaired note and one repair commit, or keep [!] and add Repair attempted. Do not touch another phase."
  echo "EVENT: repair-started:$number:model=$phase_model:effort=max"
  run_codex "$prompt" max "$plan_dir/log/repair-$number.txt"
}

completed_runs=0
while (( completed_runs < max_phases )); do
  state="$(recommendation)" || exit 2
  case "$state" in
    done)
      echo "EVENT: run-end:done:$(phase_count x) phases complete"
      exit 0
      ;;
    next:\ *)
      number="${state#next: }"
      number="${number%% *}"
      before_done="$(phase_count x)"
      run_phase "$number"
      exit_code=$?
      if (( exit_code != 0 )); then
        echo "EVENT: run-end:codex-exit-$exit_code:phase=$number"
        exit "$exit_code"
      fi
      after_done="$(phase_count x)"
      if (( after_done > before_done )); then
        echo "EVENT: phase-done:$number"
      elif grep -qE "^- \\[!\\] \\*\\*Phase $number\\*\\*:" "$plan"; then
        echo "EVENT: phase-failed:$number"
      elif grep -qE "^- \\[~\\] \\*\\*Phase $number\\*\\*:" "$plan"; then
        echo "EVENT: phase-blocked:$number"
        exit 1
      else
        echo "EVENT: run-end:no-progress:phase=$number"
        exit 1
      fi
      completed_runs=$((completed_runs + 1))
      ;;
    attention:\ *)
      number="$(printf '%s\n' "$state" | sed -E 's/^attention: ([0-9]+).*/\1/')"
      if phase_has_note "$number" "Repair attempted"; then
        echo "EVENT: run-end:repair-exhausted:phase=$number"
        exit 1
      fi
      run_repair "$number"
      exit_code=$?
      if (( exit_code != 0 )); then
        echo "EVENT: run-end:codex-repair-exit-$exit_code:phase=$number"
        exit "$exit_code"
      fi
      completed_runs=$((completed_runs + 1))
      ;;
    resume-candidate:*|blocked:*)
      echo "EVENT: run-end:$state"
      exit 1
      ;;
    *)
      echo "EVENT: run-end:unknown-selector-state:$state"
      exit 2
      ;;
  esac
done

echo "EVENT: run-end:max-phases-reached:$max_phases"
exit 1
