#!/usr/bin/env bash
# Run a portable .phased workflow with one fresh Codex session per attempt.
set -uo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="$(cd "$script_dir/.." && pwd)"
selector="$script_dir/next-phase.py"
phase_model="gpt-5.6-sol"
session_timeout="${RUN_WORKFLOW_SESSION_TIMEOUT:-3600}"
consult_timeout="${RUN_WORKFLOW_CONSULT_TIMEOUT:-}"
apply_timeout="${RUN_WORKFLOW_APPLY_TIMEOUT:-900}"

numeric_or_exit() {
  local name="$1"
  local value="$2"
  if [[ ! "$value" =~ ^[0-9]+$ ]]; then
    echo "EVENT: run-end:invalid-$name:$value"
    exit 2
  fi
}

numeric_or_exit session-timeout "$session_timeout"
if [[ -n "$consult_timeout" ]]; then
  numeric_or_exit consult-timeout "$consult_timeout"
fi
numeric_or_exit apply-timeout "$apply_timeout"

plan="$(python3 "$selector" --resolve)" || exit 2
checkout="$(git -C "$(dirname "$plan")" rev-parse --show-toplevel)" || exit 2
plan_dir="$(dirname "$plan")"
mode="$(awk -F': *' '/^Mode:/ {print tolower($2); exit}' "$plan")"
if [[ "$mode" != "autonomous" ]]; then
  echo "EVENT: run-end:preflight:mode=${mode:-missing}"
  exit 2
fi
python3 "$selector" --validate "$plan" || exit 2

transport="$(python3 "$selector" --transport "$plan")" || exit 2
install -d -m 700 "$(dirname "$transport")"
stop_request="$transport-stop-request"
consult_answer="$transport-foreman-answer"
apply_outcome="$transport-apply-outcome"
rm -f "$stop_request" "$consult_answer" "$apply_outcome"

phase_count() {
  local marker="$1"
  grep -cE "^- \\[$marker\\] \\*\\*Phase" "$plan" 2>/dev/null || true
}

unfinished_count() {
  grep -cE '^- \\[[ !~>]\\] \\*\\*Phase' "$plan" 2>/dev/null || true
}

recommendation() {
  python3 "$selector" "$plan" |
    awk -F'recommendation: ' '/^recommendation: / {print $2}'
}

phase_effort() {
  local number="$1"
  local effort
  effort="$(awk -F'|' -v number="$number" '
    /^## Suggested execution config/ {table=1; next}
    table && /^## / {table=0}
    table && $2 ~ "^[[:space:]]*Phase[[:space:]]+" number "[[:space:]]*$" {
      value=$3
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
      print tolower(value)
      exit
    }
  ' "$plan")"
  if [[ -z "$effort" ]]; then
    effort="$(awk -v number="$number" '
      $0 ~ "^- \\[.\\] \\*\\*Phase " number "\\*\\*:" {inside=1; next}
      inside && /^- \\[.\\] \\*\\*Phase / {exit}
      inside && /Run:/ {
        line=$0
        sub(/^.*Run:[[:space:]]*/, "", line)
        n=split(line, parts, /[[:space:]]*\\/[[:space:]]*/)
        if (n > 1) {
          gsub(/[^a-z]/, "", parts[n])
          print parts[n]
          exit
        }
      }
    ' "$plan")"
  fi
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
    inside && /^- \\[.\\] \\*\\*Phase / {exit}
    inside {
      line=$0
      sub(/^[[:space:]]*/, "", line)
      if (index(line, "> " note ":") == 1) found=1
    }
    END {exit found ? 0 : 1}
  ' "$plan"
}

phase_has_claim() {
  local number="$1"
  awk -v number="$number" '
    $0 ~ "^- \\[!\\] \\*\\*Phase " number "\\*\\*:" {inside=1; next}
    inside && /^- \\[.\\] \\*\\*Phase / {exit}
    inside && /plan-defect claim/ {found=1}
    END {exit found ? 0 : 1}
  ' "$plan"
}

wait_for_file() {
  local path="$1"
  local limit="$2"
  local elapsed=0
  while (( elapsed < limit )); do
    if [[ -s "$path" ]]; then
      head -1 "$path"
      rm -f "$path"
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  return 1
}

consult_result=""
wait_for_consult() {
  local path="$1"
  local limit="$2"
  local stop_path="$3"
  local number="$4"
  local elapsed=0
  local answer
  consult_result=""
  while true; do
    if [[ -s "$path" ]]; then
      answer="$(head -1 "$path" | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')"
      rm -f "$path"
      answer="${answer#plan-defect:}"
      case "$answer" in
        stop|repair|apply)
          consult_result="$answer"
          return 0
          ;;
        *)
          echo "EVENT: consult-answer-invalid:$number:${answer:-empty}"
          ;;
      esac
    fi
    if [[ -f "$stop_path" ]]; then
      rm -f "$stop_path"
      consult_result="stop-request"
      return 0
    fi
    if [[ -n "$limit" ]] && (( elapsed >= limit )); then
      return 1
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
}

run_codex() {
  local prompt="$1"
  local effort="$2"
  local log_file="$3"
  local worker_pid
  local watchdog_pid=""
  local status

  : >"$log_file"
  chmod 600 "$log_file"
  codex exec --ephemeral -C "$checkout" \
    -m "$phase_model" \
    -c "model_reasoning_effort=$effort" \
    -s workspace-write \
    "$prompt" >"$log_file" 2>&1 &
  worker_pid=$!

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
  return "$status"
}

record_session_log() {
  local external_log="$1"
  local internal_name="$2"
  local before_head="$3"
  local after_head
  local relative

  after_head="$(git -C "$checkout" rev-parse HEAD 2>/dev/null)" || return
  [[ "$after_head" != "$before_head" && -s "$external_log" ]] || return
  mkdir -p "$plan_dir/log"
  cp "$external_log" "$plan_dir/log/$internal_name"
  relative="${plan_dir#"$checkout"/}/log/$internal_name"
  git -C "$checkout" add -- "$relative"
  git -C "$checkout" commit --amend --no-edit -q
}

run_phase() {
  local number="$1"
  local effort
  local prompt
  local log_file
  effort="$(phase_effort "$number")"
  log_file="$transport-phase-$number.log"
  prompt="Use the execute-phase-agent skill from $plugin_root/skills/execute-phase-agent/SKILL.md. Execute exactly Phase $number of the active portable plan at $plan. Preserve the .phased protocol exactly. Finish with exactly one durable outcome: the phase becomes [x] with Done and Files notes and one phase commit; it becomes [!] with Issue and Attempted notes and one failure commit; an attributable earlier regression reopens its owning phase as [!]; or an unattributable red baseline marks Phase $number [~] with a Blocked note. Demonstrate Done with tests and lint actually run. Do not start another phase."
  echo "EVENT: phase-started:$number:model=$phase_model:effort=$effort"
  run_codex "$prompt" "$effort" "$log_file"
}

run_repair() {
  local number="$1"
  local prompt
  local log_file
  log_file="$transport-repair-$number.log"
  prompt="Use the repair-phase-agent skill from $plugin_root/skills/repair-phase-agent/SKILL.md. Repair exactly the first [!] phase in the active portable plan at $plan. Preserve the .phased protocol. Finish with [x] plus a Repaired note and one repair outcome commit, or keep [!] and add Repair attempted. Do not touch another phase."
  echo "EVENT: repair-started:$number:model=$phase_model:effort=max"
  run_codex "$prompt" max "$log_file"
}

initial_done="$(phase_count x)"
initial_unfinished="$(unfinished_count)"
session_limit=$((initial_unfinished * 2 + 2))
max_landings=2147483647
if [[ -n "${RUN_WORKFLOW_MAX_PHASES:-}" ]]; then
  numeric_or_exit max-phases "$RUN_WORKFLOW_MAX_PHASES"
  max_landings="$RUN_WORKFLOW_MAX_PHASES"
fi

sessions=0
landed=0
while true; do
  if (( landed >= max_landings )); then
    echo "EVENT: run-end:phase-budget:$landed/$max_landings"
    exit 0
  fi
  if [[ -f "$stop_request" ]]; then
    rm -f "$stop_request"
    echo "EVENT: run-end:stopped-by-request:$landed/$initial_unfinished"
    exit 0
  fi

  state="$(recommendation)" || exit 2
  if (( sessions >= session_limit )) && [[ "$state" != "done" ]]; then
    echo "EVENT: run-end:session-budget-exhausted:$sessions/$session_limit"
    exit 1
  fi
  case "$state" in
    done)
      echo "EVENT: run-end:done:$(phase_count x) phases complete"
      exit 0
      ;;
    next:\ *)
      number="${state#next: }"
      number="${number%% *}"
      before_done="$(phase_count x)"
      before_head="$(git -C "$checkout" rev-parse HEAD)"
      run_phase "$number"
      exit_code=$?
      sessions=$((sessions + 1))
      record_session_log "$transport-phase-$number.log" "phase-$number.txt" "$before_head"
      if (( exit_code != 0 )); then
        echo "EVENT: run-end:codex-exit-$exit_code:phase=$number"
        exit "$exit_code"
      fi
      after_done="$(phase_count x)"
      if (( after_done > before_done )); then
        landed=$((landed + 1))
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
      ;;
    attention:\ *)
      number="$(printf '%s\n' "$state" | sed -E 's/^attention: ([0-9]+).*/\1/')"
      if phase_has_note "$number" "Repair attempted"; then
        echo "EVENT: run-end:repair-exhausted:phase=$number"
        exit 1
      fi

      if phase_has_claim "$number"; then
        echo "EVENT: phase-needs-foreman:$number"
        if wait_for_consult "$consult_answer" "$consult_timeout" \
            "$stop_request" "$number"; then
          answer="$consult_result"
        else
          answer=""
        fi
        case "$answer" in
          stop)
            echo "EVENT: run-end:plan-defect-stop:phase=$number"
            exit 1
            ;;
          stop-request)
            echo "EVENT: run-end:stopped-by-request:$landed/$initial_unfinished"
            exit 0
            ;;
          apply)
            echo "EVENT: phase-apply-wait:$number"
            outcome="$(wait_for_file "$apply_outcome" "$apply_timeout" || true)"
            if [[ "$outcome" == "green" ]] &&
               grep -qE "^- \\[x\\] \\*\\*Phase $number\\*\\*:" "$plan"; then
              landed=$((landed + 1))
              echo "EVENT: phase-applied:$number"
              continue
            fi
            echo "EVENT: phase-apply-fell-through:$number"
            ;;
          repair|"")
            ;;
        esac
      fi

      before_done="$(phase_count x)"
      before_head="$(git -C "$checkout" rev-parse HEAD)"
      run_repair "$number"
      exit_code=$?
      sessions=$((sessions + 1))
      record_session_log "$transport-repair-$number.log" "repair-$number.txt" "$before_head"
      if (( exit_code != 0 )); then
        echo "EVENT: run-end:codex-repair-exit-$exit_code:phase=$number"
        exit "$exit_code"
      fi
      after_done="$(phase_count x)"
      if (( after_done > before_done )); then
        landed=$((landed + 1))
        echo "EVENT: phase-repaired:$number"
      fi
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
