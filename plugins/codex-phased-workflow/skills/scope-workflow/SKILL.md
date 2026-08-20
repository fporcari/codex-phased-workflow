---
name: scope-workflow
description: Settle the decisions a phased plan needs, before the plan exists — one question at a time, down the decision tree
---

# Scope Workflow

Interrogate the user about the scope named in the invocation until every decision `write-workflow` will
need is settled. Relentless, one question at a time, and **nothing is built here**:
this skill produces understanding, never code, never a branch, never a plan file.

It exists because `/write-workflow` settles decisions by *reading the conversation*.
When the conversation was vague there is nothing to read, and the plan comes out with
"decide later" phases — which that skill's own rules forbid. This is where the
conversation stops being vague.

**Shared conventions:** read `<PLUGIN_ROOT>/refs/common.md` once at start —
language and Codex user-input prompt style.

## Step 1: Pre-flight

```bash
python3 "<PLUGIN_ROOT>/scripts/next-phase.py" --resolve
```

A plan already resolves → say so and stop: scoping is for work that has no plan yet.
Point at `/resume-workflow` to see where that one stands, or `/execute-phase` to carry
it forward. One branch, one plan.

## Step 2: Establish the ground

**A fact is looked up, never asked.** What exists today, where it lives, who calls it,
what the issue says — you find it yourself with Grep, Read, `git log`,
`gh issue view`. Asking the user something the filesystem could answer spends their
attention on your legwork.

From ~3 areas to survey, dispatch one read-only Explore subagent per area instead of
searching serially, and reason over what they return.

Report the ground in a few lines, with concrete paths, so a wrong premise gets
corrected before it costs a whole branch of questions.

**Done when** every factual premise behind the coming questions is either verified in
the codebase or flagged as unverifiable.

## Step 3: Map the decision tree

Every question here exists to fill a field of the plan. Know which one before you ask:

| Field | What the question settles |
|---|---|
| `Mode:` | interactive or autonomous — **ask this first** |
| `Decisions:` | naming, signatures, library, API shape, trade-offs |
| `Pattern:` | which existing example each non-trivial phase copy-adapts |
| `Files:` | the surface each phase touches, or its discovery rule |
| `Done:` | what "finished" means, re-runnably |

**The mode fork leads** because it reshapes everything below it: interactive phases
close where a human can look at something, autonomous ones close on one concern with a
re-runnable `Done:`. The same work splits into different phases under the two. Derive
a recommendation from the work itself — *"I'll know it when I see it"* (UI, visual,
declarative) → interactive; measurable (refactor, migration, well-specified startup) →
autonomous — and put it as the recommended answer.

Order the rest by **what they unlock**: a decision that changes the shape of the ones
below it comes first. Decisions that cannot affect each other are siblings, and their
order is free.

A decision belongs to the user when either answer leads to materially different work.
Everything else is yours — make it, say you made it, move on.

**Done when** you can name the first question and say which later ones its answer
would change.

## Step 4: The loop

One question per turn. Asking several at once is bewildering, and it destroys the
tree: you cannot branch on an answer you asked for in parallel.

Each question carries **your recommended answer and its reason in one line** — the
user often just confirms, which is the point — and, when the answer reshapes what
follows, **what it unlocks**: *"if you answer X, the next question about the index
falls away"*.

Use `Codex user-input prompt` with the recommendation first per `common.md`. An answer that
opens ground you had not mapped sends you back to Step 3 for that subtree: the tree
grows during the interrogation, it is not fixed up front. An answer that contradicts
the ground from Step 2 stops the loop — re-verify the fact before building a branch on
it.

**Done when** every branch is **decided**, or **deferred in the plan's own
vocabulary** — a check that only makes sense later is a `Verify: deferred: needs Phase
M`, not a vague "we'll decide later". A branch with no field and no phase to land in is
not settled.

## Step 5: Hand over

Present it in the shape `/write-workflow` reads, and **wait for the user to
confirm the shared understanding**:

```
Mode: <interactive|autonomous> — <reason, half a line>

Settled:
- <decision> → <choice> (<reason>)                   [Decisions:]
- pattern for <work> → `path/to/example.py:func`     [Pattern:]
- <phase> is finished when <re-runnable criterion>   [Done:]

Deferred:
- <check> → Verify: deferred: needs Phase <M>

Facts it rests on:
- <fact> (<path>)
```

Close the block with the gate line (`common.md` → *The gate line*): *"**Confirm?**
On your ok we are done here: launch `/write-workflow` in this chat, it reads the
decisions from here."*

Not confirmed → keep going on the parts they push back on. Nothing else happens
here: no branch, no file, no code.
