"""The tree of the work, from the roadmap down to the phase.

The hierarchy is roadmap -> macro-phase -> phase. `.phased/roadmap.md`
carries the macro-phases as `## Macro-phase N — <title>` headings, each with
its `Mini-scope` and its `Ends at`, and each one is a plan.md of its own. A
repo with no roadmap.md has the active plan as its root.

The state of a macro-phase comes from WHERE its plan directory sits — `done/`
closed, `active/` in progress, neither one not started — never from a
judgment this tool makes. Same rule for the phase icons: they are derived
from the phase marker and its notes, which the plugin has already written.

This module does not read plans: it receives them already read. That way
`core` imports `roadmap` and not the other way round.
"""

import pathlib
import re

MACRO_RE = re.compile(r'^##\s+Macro-?phase\s+(\d+)\s*[—–:-]\s*(.*)$', re.I)
MACRO_FIELD_RE = re.compile(r'^\s*[-*]\s*\**(Mini-scope|Ends at)\**\s*:\s*(.*)$', re.I)
TITLE_RE = re.compile(r'^#\s+(.*)$')
# `macro2-replica-convergence` -> macro-phase 2. It is the only link between a
# macro-phase and its plan: no field of a plan names its macro-phase.
SLUG_MACRO_RE = re.compile(r'^macro-?(\d+)\b', re.I)

# The phase marker icons. `✓!` and the person are the two cases where the
# marker alone does not say enough: a closed phase carrying a `> Review:`, and
# a running one awaiting the human checks.
MARKER_ICONS = {
    ' ': ('○', ''),
    'x': ('✓', 'x'),
    '!': ('✕', 'e'),
    '~': ('⊘', ''),
    '>': ('◐', 'r'),
}
MACRO_ICONS = {'done': ('✓', 'x'), 'active': ('◐', 'r'), 'none': ('○', '')}


def read_roadmap(repo):
    """The macro-phases of `.phased/roadmap.md`. None when the file is absent."""
    f = pathlib.Path(repo) / '.phased' / 'roadmap.md'
    if not f.is_file():
        return None
    title, macros = None, []
    current = None
    for line in f.read_text(errors='replace').splitlines():
        m = MACRO_RE.match(line)
        if m:
            current = {'n': int(m.group(1)), 'title': m.group(2).strip(),
                       'mini_scope': None, 'ends_at': None}
            macros.append(current)
            continue
        m = TITLE_RE.match(line)
        if m and title is None:
            title = m.group(1).strip()
            continue
        if current is None:
            continue
        m = MACRO_FIELD_RE.match(line)
        if m:
            key = 'mini_scope' if m.group(1).lower() == 'mini-scope' else 'ends_at'
            current[key] = m.group(2).strip()
    return {'title': title or 'roadmap', 'macros': macros}


def phase_icon(phase, agents=()):
    """The icon of a phase, from its own facts: marker, notes, active agents."""
    kinds = {n['kind'] for n in phase.get('notes') or ()}
    status = phase['status']
    if status == 'x' and 'Review' in kinds:
        icon, cls = '✓!', 'x'
    elif status == '>' and 'Testing' in kinds:
        icon, cls = '👤', 'h'
    else:
        icon, cls = MARKER_ICONS.get(status, (status, ''))
    warn = any(a.get('errors') and a.get('active') for a in agents)
    return {'icon': icon, 'cls': cls, 'warn': warn}


def macro_of(slug):
    m = SLUG_MACRO_RE.match(slug or '')
    return int(m.group(1)) if m else None


def build_tree(roadmap, plans, active_slug):
    """The tree the page draws.

    `plans` is a list of `{'slug','dir','state','phases'}` — the plans already
    read. A plan whose slug names no macro-phase does not vanish: it lands at
    the foot of the tree as a node of its own, because losing it is worse than
    seeing it with no parent.
    """
    used = set()
    nodes = []
    if roadmap:
        for macro in roadmap['macros']:
            match = next((p for p in plans if macro_of(p['slug']) == macro['n']), None)
            state = match['state'] if match else 'none'
            if match:
                used.add(match['slug'])
            icon, cls = MACRO_ICONS[state]
            nodes.append({
                'kind': 'macro', 'n': macro['n'], 'title': macro['title'],
                'mini_scope': macro['mini_scope'], 'ends_at': macro['ends_at'],
                'state': state, 'icon': icon, 'cls': cls,
                'slug': match['slug'] if match else None,
                'branch': (match or {}).get('branch'),
                'phases': _phases(match, active_slug)})
    for plan in plans:
        if plan['slug'] in used:
            continue
        icon, cls = MACRO_ICONS[plan['state']]
        nodes.append({
            'kind': 'plan', 'n': None, 'title': plan['slug'],
            'mini_scope': None, 'ends_at': None,
            'state': plan['state'], 'icon': icon, 'cls': cls,
            'slug': plan['slug'], 'branch': plan.get('branch'),
            'phases': _phases(plan, active_slug)})
    if roadmap:
        return {'label': roadmap['title'], 'roadmap': True, 'nodes': nodes}
    # No roadmap: the root is the active plan, as before.
    root = next((n for n in nodes if n['slug'] == active_slug), None)
    return {'label': active_slug or 'no plan', 'roadmap': False,
            'nodes': [], 'phases': root['phases'] if root else []}


def _phases(plan, active_slug):
    if not plan:
        return []
    mine = plan['slug'] == active_slug
    out = []
    for ph in plan['phases']:
        # The notes travel for another plan's phases too: they are what one
        # reads when coming back to review closed work.
        out.append({'n': ph['n'], 'status': ph['status'], 'title': ph['title'],
                    'tags': ph.get('tags') or [],
                    'run': ph['run'], 'mine': mine, 'notes': ph.get('notes') or [],
                    'icon': ph.get('icon'), 'cls': ph.get('cls'),
                    'warn': ph.get('warn', False)})
    return out
