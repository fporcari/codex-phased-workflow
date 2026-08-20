# Context: wf/claude-originated
Parent: main | Issue: #101
Mode: autonomous

## Objective

Prove that Codex can continue a workflow written by Claude without converting
its protocol or model labels.

## Work Plan

- [x] **Phase 1**: establish the shared state
  - Pattern reference: `library-standard`
  - Files: shared.txt
  - Decisions: keep the portable marker vocabulary
  - Details: create the initial state.
  - Done: shared.txt exists
  > Done: shared.txt exists
  > Files: shared.txt
- [ ] **Phase 2**: continue from Codex
  - Pattern reference: `library-standard`
  - Files: codex.txt
  - Decisions: preserve the opus compatibility label
  - Details: create the continuation marker.
  - Done: codex.txt exists

## Suggested execution config
| Phase | Effort | Model |
|---|---|---|
| Phase 1 | medium | opus |
| Phase 2 | high | opus |

## Notes

Originated in Claude Code.
