---
name: repair-phase
description: Repair a broken phase with fresh eyes, in a chat of its own
---

# Repair Phase

Fresh-eyes repair, in a chat that exists only for it. **The previous session's diagnosis may itself be the problem — question it, don't continue it**, and debugging is the most context-hungry thing a phase does, which is why it happens here and not in the chat that holds the phase.

**Two ways in**, and they differ only at the ends:

- **A phase left `[!]`** — its `Done:` came back red and its own chat gave up. The repair closes it: `[x]` + `> Repaired:`.
- **A phase still `[>]`, with a defect you have seen** — the phase is not finished, its chat has stood down (`refs/phase-execution.md` → *Handing a defect to repair*), and the repair **hands it back**: the phase returns `[>]` and you resume in the chat that owns it.

**Non-negotiables:** no questions between the start and the verdict — that is what keeps this cheap for you; ONE commit at the end; one phase per invocation; everything written in English; and always a machine-readable outcome, never a phase left in a state the plan cannot describe.

`/wf:repair-phase-agent` is this same repair with the human replaced by a contract: unattended, `[!]` only, closing on its own.

## Step 1: Ask what is wrong

**Always ask, even when the answer seems to be on file.** The plan's `> Issue:`, the other chat's account, a transcript you can read — all of it is a *previous diagnosis*, and this chat exists because those are suspect. Your account of the symptom is the specification; everything else is evidence about it.

One question, plain: what goes wrong, what you expected instead, and — where it can be said — how to make it happen. Nothing else is asked until the verdict.

## Step 2: Locate the phase, and put it under repair

Resolve the active plan (`python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --resolve`, see `common.md`; from outside the plan's root, `--plans` + `git -C` per `common.md` → *Plan location*).

- **First `[!]` phase** → that is the one, and it is already marked. Read its `> Issue:`, `> Attempted:` and `> Files:`.
- **No `[!]`, one `[>]`** → the mid-phase case. Write what you said as `> Issue:` and **ask to confirm the phase goes `[!]` while under repair** — one Codex user-input prompt, because it is a real state change: while it holds, nothing else in the plan may start, and any chat that looks at the plan sees why. On confirmation, commit that edit alone.
- **Neither** → nothing to repair here: say so and stop.
- It already has `> Repair attempted:` → say "Repair already attempted for Phase N — the next look is yours" and stop. Never loop repairs.

**Title this chat** `wf:<slug>:repair-N — <phase title>`, with `set_session_title` on `session_id: "self"` (`foreman.md` → *The foreman*). **Not** the phase chat's own `wf:<slug>:phase-N` title: that one is an address, the one the hand-back below sends to, and a second session bearing it would make this chat the addressee of its own outcome. Best-effort, like everything on that channel — no tool, no title, no consequence.

**Then write the marker and commit it**, on the phase:

```
  > Repair started: <ISO timestamp> — chat wf:<slug>:repair-N
```

`[!]` on its own does not say whether anybody is on the phase, so a foreman reopened cold reads it as broken-and-available and can send a second repair into this working tree — two chats, one tree. The note is on disk and committed, which is the part a message to the foreman cannot promise (`common.md` → *Failure and repair notes*). In the `[>]` case it rides the same commit as the `[!]` transition; in the `[!]` case it is a commit of its own — `wf(phase N): under repair`.

**Hard rule: never repeat an attempt listed in `> Attempted:`.** If your diagnosis leads to essentially one of those fixes, the diagnosis is wrong — dig deeper.

Under `/run-workflow` there is one more source, and it is the richest: `log/phase-N.txt` next to the plan holds the failing session's actual transcript. The `> Attempted:` notes are that session's summary of itself — the log is what it really did.

**The tree is yours while this runs.** The phase's own chat has stopped (that is the precondition, not a courtesy): two chats editing one working tree is the failure mode the whole protocol is shaped to avoid.

## Step 3: Diagnose from scratch

1. Re-read the phase objective, `Details:`, `Done:` and its `Pattern:` example.
2. **An `> Issue:` carrying `plan-defect claim` is itself the thing under test.** The child judged the plan unimplementable, and that judgment reached you unverified — in the first field run both such claims dissolved under fresh eyes (the contract was implementable in-dialect both times). Your first job is trying to satisfy the contract AS WRITTEN; the contract stays read-only either way (`refs/contracts.md` → *Contract tests*). Only a claim that survives your own attempt ends the repair `[!]` with `> Repair attempted: plan-defect confirmed — <what you tried, why the contract truly cannot hold>` — the foreman fixes plan and tests from there, never you.
3. Reproduce the failure and confirm the recorded error signature still holds.
4. **Establish whose failure it is.** The failed phase committed its own work as `wf(phase N): FAILED — <title>`, so its boundaries are exact: `git show --stat HEAD` is everything it changed, and `HEAD^` is the tree before it started. Re-run the green signal at `HEAD^` — a failure that reproduces there is **not this phase's**. Don't patch it here: keep the phase `[!]` with a `> Repair attempted:` note naming the real culprit, so the human fixes the right thing.

   `HEAD` is that commit only if nothing landed after it, which is the normal case (a `[!]` phase stops the run). Otherwise find it by message rather than assuming: `git log --format='%H %s' | grep "phase N"`.
5. Root-cause first: grep the callers of the touched functions, compare against the pattern reference, and ask whether the previous fixes aimed at a symptom.
6. Scale exploration to the phase's Effort as in `/execute-phase-agent` Step 2.

## Step 4: Fix and converge

Same rules as `/execute-phase-agent` Step 4: green signal = test suite + linter on the touched files; up to **3 fix attempts** with the no-progress detector; then re-check every item of `Done:` literally.

Then load `<PLUGIN_ROOT>/judges/phase-verifier.md` and give that shipped prompt
to ONE fresh read-only Codex subagent scoped to this phase's files. Never invoke
a bare judge name: Codex packages these as prompt files, not discoverable named
agents. MECHANICAL findings are fixed within the same budget; JUDGMENT is
recorded as `> Review:`. Unlike a normal phase, this runs **unconditionally**:
the code already failed once and was patched under a bounded budget, which is
the case where a fresh independent pass reliably pays.

## Step 5: The verdict is yours

Show what it turned out to be, what changed, and which signal is green that was red — then **stop and ask**. You decide it is repaired; a repair that grades itself is the thing this chat was opened to avoid.

On your ok, record the outcome for the way in:

- **Came in `[!]`** → the phase closes: `[x]` + `> Repaired:`, as below.
- **Came in `[>]`** → the phase **goes back to `[>]`** carrying `> Repaired:` and its existing `> WIP:` note, and this task sends the outcome to the phase task (`wf:<slug>:phase-N`, resolved through the available Codex task-listing tool — `foreman.md` → *The foreman*, including the rule that a tool you have not loaded is not a tool that is absent) and tells you to carry on there. It does not touch anything else: the phase is not finished, and finishing it is that task's job.

**One chat is one attempt.** If the repair eats this whole context without a green signal, the problem is not a bug: leave `[!]` + `> Repair attempted:`, send the foreman the `blocked` line (`foreman.md` → *The foreman*), and say plainly that this belongs in a re-planning conversation, not in another repair.

## The outcome formats

**Repaired:**
```
- [x] **Phase N**: title
  > Done: brief description
  > Repaired: <the actual root cause, and why the previous attempts missed it>
  > Files: <complete list — previous session's plus yours>
  > Review: judgment-level findings flagged for the quality check (omit if none)
```

**Still failing** — keep `[!]` and the existing `> Issue:` / `> Attempted:` / `> Files:` notes (extend `> Attempted:` with yours), and append:
```
  > Repair attempted: <ISO timestamp> — <updated diagnosis: what you ruled out, what the human should look at first>
```

**The `> Repair started:` marker goes, whatever the outcome** — it described a repair in progress, and the outcome supersedes it: remove it in the same edit that records the result, on a phase handed back `[>]` too. A marker left behind describes a chat that no longer exists.

Either way, commit — the plan is tracked, and leaving the tree dirty would block the next phase's baseline:

```bash
git add -A && git commit -q -m "wf(phase N): repaired — <root cause>"
```

or, on a failed repair, `wf(phase N): repair attempted — <diagnosis>`.

Print `✓ Phase N repaired: <root cause>` or `✗ Phase N repair failed: <reason> — human review required`, then stop. A phase handed back `[>]` prints the same first line plus where to go: *"back to the phase chat — it has the verdict."*
