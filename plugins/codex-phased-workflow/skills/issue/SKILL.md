---
name: issue
description: Load and analyze a GitHub issue — analysis only, the work plan is created via /write-workflow
---

# GitHub issue analysis

**Language rule:** All written content must be in English; the conversation follows the user's own configuration (`<PLUGIN_ROOT>/refs/common.md` → *Language*).

**IMPORTANT: This command is for ANALYSIS ONLY. Do NOT edit source code or implement anything. Use `/write-workflow` to create the work plan.**

## Step 1: Fetch issue

```
gh issue view <issue-number> --json title,body,labels,state,comments --jq '{title,body,labels: [.labels[].name],state,comments: [.comments[].body]}'
```

## Step 2: Analyze

1. **Understand the issue**: problem, expected behavior, reproduction steps
2. **Explore the codebase** to identify relevant files, components, and existing tests
3. **Assess scope**: is this a quick fix or a multi-phase task?

## Step 3: Present and hand off

Present to the user a summary of:
- What the issue is about
- Which files/components are involved
- Estimated complexity

Then close flat, with no question — this command cannot create the plan itself, so asking *"shall I go ahead?"* promises something it cannot do:

*"Next step: launch `/write-workflow` to create the work plan (in this chat or a new one — the analysis stays readable here)."*

## Additional Context

- Issue number: the number named in the user's invocation
- Full request: the user's invocation text
