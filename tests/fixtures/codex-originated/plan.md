# Context: wf/codex-originated
Parent: develop
Mode: autonomous
Channel: relayed

## Objective

Prove that Claude can continue a workflow written by Codex without encountering
Codex-specific state in the plan.

## Work Plan

- [ ] **Phase 1**: portable strong-model phase
  - Pattern reference: `new-pattern (flagged: higher risk)`
  - Files: portable.txt
  - Decisions: use fable as the portable hard-phase label
  - Details: create the portable result.
  - Done: portable.txt exists

## Suggested execution config
| Phase | Effort | Model |
|---|---|---|
| Phase 1 | xhigh | fable |

## Notes

Originated in Codex.
