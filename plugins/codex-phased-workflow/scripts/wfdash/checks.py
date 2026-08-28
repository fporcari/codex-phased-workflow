"""The `Verify:` steps of a phase, read from the plan.

Nothing is recorded here. The gate a `Verify: now` step names is the human's
ok in the conversation, and the panel only has to show what the plan already
carries — the QA page's own checkboxes are client-side for the same reason
(`refs/contracts.md`). A tick persisted where no skill reads it was a second
source of truth for that gate.
"""

import hashlib
import re

# `now — <step>` or `deferred: needs Phase 5 — <step>`.
WHEN_RE = re.compile(r'^(now|deferred:[^—–]*?)\s*[—–]\s*(.*)$', re.I)


def phase_checks(phase):
    """The checks of a phase, one per row.

    The `> Verify:` notes written by execution win over the `- Verify:` fields
    written by planning: execution carries the authored steps into its own
    notes, so where the notes exist that list is the complete one.
    """
    notes = [n['text'] for n in (phase.get('notes') or ()) if n['kind'] == 'Verify']
    steps = notes or [v['text'] for v in (phase.get('verify') or ())]
    out = []
    for step in steps:
        m = WHEN_RE.match(step)
        when, text = (m.group(1).strip(), m.group(2).strip()) if m else (None, step)
        ident = f"{phase['n']}:{hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]}"
        out.append({'id': ident, 'text': text, 'when': when})
    return out
