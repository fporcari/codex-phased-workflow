---
name: issue
description: Analyze a GitHub issue and recommend one fresh task or a phased workflow — analysis and handoff only
---

# GitHub issue analysis

**Language rule:** All written content must be in English; the conversation follows the user's own configuration (`<PLUGIN_ROOT>/refs/common.md` → *Language*).

**IMPORTANT: This command is for ANALYSIS ONLY. Do NOT edit source code, implement anything, or create a task. Hand over a one-task prompt or direct the user to `/write-workflow`.**

## Step 1: Fetch issue

```
gh issue view <issue-number> --json title,body,labels,state,comments --jq '{title,body,labels: [.labels[].name],state,comments: [.comments[].body]}'
```

## Step 2: Analyze

1. **Understand the issue**: problem, expected behavior, reproduction steps
2. **Explore the codebase** to identify relevant files, components, and existing tests
3. **Assess scope — one task or a workflow?** A workflow pays only when one
   of three holds: the work does not fit one context; an intermediate result
   changes what comes next and needs a human gate; or the user needs
   unattended execution with checkpoints and repair. A fix whose decisions
   the issue already settles and whose diff can be understood in one sitting
   meets none: recommend one fresh Codex task with a complete prompt,
   <Sol for decided work or Astra for engineering> / `high`, and no workflow. Recon and a re-runnable `Done:`
   remain necessary on either road.

## Step 3: Present and hand off

Present to the user a summary of:
- What the issue is about
- Which files/components are involved
- Estimated complexity, the one-task/workflow verdict, and why

Then close flat, with no question — this command cannot create the plan or
task itself, so asking *"shall I go ahead?"* promises something it cannot do:

- **One task** → *"Next step: one fresh Codex task, no workflow — here is its
  prompt."* Give a self-contained prompt with the repository, starting state,
  <Sol for decided work or Astra for engineering> / `high` hint, objective, settled decisions, verified files and
  copy-adapt patterns, constraints, contract tests first,
  exact lint/test commands, re-runnable Done criteria, and the deliverable.
  Stop for an unlisted decision or after two attempts leave Done red. Do not
  imply authority to merge or publish. A user who still wants a plan invokes
  `/write-workflow` explicitly.
- **Workflow** → *"Next step: launch `/write-workflow` to create the work plan
  (in this task or a new one — the analysis stays readable here)."*

## Additional Context

- Issue number: the number named in the user's invocation
- Full request: the user's invocation text
