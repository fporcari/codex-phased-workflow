# Naming review — shared core

The procedure that turns `wf:phase-N:new` markers into final names. Loaded
by `/close-phase` (scope: one phase's touched files) and by
`/quality-check` (scope: every file the workflow touched). The marker
contract itself — format, minimality, which mode strips when — is
`refs/contracts.md` → *New-method markers and minimality*; the skills cite
these two files, they never restate them.

The review exists for one reason: agent-chosen names are the part of a diff
users most often want to reword, and renaming after the merge costs a
commit per name. Here it costs one answer — and for a user who trusts the
proposals, one keypress.

## Collect

```bash
grep -rn "wf:phase-[0-9]*:new" <scope files>
```

Scope is the caller's: the phase's `Files:` list for `/close-phase`, the
union of every completed phase's `> Files:` for `/quality-check`. No
hits → say so in one line and stop; the review has nothing to do.

## The map

Build ONE table — the map the user reviews:

| # | Proposed name | Kind | Necessity | File | Phase |
|---|---|---|---|---|---|

**Kind** is `free` (renameable) or `framework` (the name is API — dispatch
by prefix or suffix, a hook the framework matches literally; state which
part, if any, is free). Detecting it is the caller's context: the phase's
`Pattern:` reference and the file's own conventions say which name shapes
are magic — never guess a framework rule the code does not show.

**Necessity** is the minimality contract (`refs/contracts.md` → *New-method
markers and minimality*) applied to each entry, now that every new callable
sits in one view — the vantage point no single phase had. Read each one
against its phase's objective and `Done:`: required → the column stays
empty; a helper with a single caller that could be inlined, a speculative
abstraction, a parameter nothing passes, a duplicate of something an
earlier phase already built, an accessor for an attribute the language
already exposes as public, a wrapper that only delegates (the named
anti-patterns of the contract) → `⚠` with the reason, stated in half a
line.
The flags sit in the map, ABOVE the question: the accept-all user has seen
them before pressing enter.

Present the map in ONE message, then ONE `Codex user-input prompt`:

- **Accept all (Recommended)** — every proposed name stands and the review
  reduces to stripping the markers. This is the default for a reason: a
  user who trusts the names presses enter once and pays nothing more —
  `⚠` flags included: seen and waved through is a decision too.
- **Review one by one** — per-method questions follow, batched up to 4 per
  `Codex user-input prompt`: one question per method, options *Keep `<name>`*
  (Recommended) / *Rename* — the new name arrives through the free-text
  "Other" answer. A `⚠`-flagged method carries a third option,
  *Inline/remove*, with the flag's reason as its description — recommended
  in place of *Keep* when the code is plainly dead. `framework` names are
  keep-only in phrasing: the fixed part is stated, and a rename applies to
  the free part alone.

## Apply

For each rename: the definition AND every call site.

```bash
grep -rn "\b<old_name>\b" .
```

The grep runs over the repository, not just the scope — a caller outside
the phase's files is exactly the one a scoped search misses, and a rename
that misses one caller is worse than no rename. Then strip every marker in
scope, renamed or not.

An *Inline/remove* decision is applied like a rename, with the same care:
the callable's body moves to its caller (or goes, when nothing calls it),
its tests follow, and no other behaviour changes.

Renames or removals happened → re-run the narrowest green signal the caller
already uses (tests + lint scoped to the touched files) before anything
commits. Marker stripping alone changes no behaviour: no re-run needed.

## Sweep

The exit check, always — the fast path included:

```bash
grep -rn "wf:phase-[0-9]*:new" <scope files>
```

Empty → done. Anything left is fixed before the caller commits: a marker
that survives consolidation is noise shipped to the parent branch.
