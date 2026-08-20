#!/usr/bin/env python3
"""Compute the next eligible phase from a phased work plan.

Deterministic implementation of the phase-selection semantics used by
the phased-workflow skills (/execute-phase, /execute-phase-agent). The canonical
description of the semantics lives in
<PLUGIN_ROOT>/refs/common.md ("Phase selection").

Statuses: [ ] pending, [>] in execution, [x] done, [!] issue, [~] blocked.
Tags (backticked at end of the phase line): vast.

Rules:
- [x] phases are complete; every other status counts as "not complete".
- Phases run strictly in order: a pending phase is blocked while any
  preceding phase is not [x].
- [>] phases are reported as resume candidates only when no pending
  phase is eligible.

Output: a "phases:" table plus one final "recommendation:" line:
  recommendation: next: 3               execute Phase 3
  recommendation: resume-candidate: 2 (age: 3.4h, wip: yes)
  recommendation: blocked: phase 2 ... awaiting the human's checks
  recommendation: attention: 5[!]       user must resolve before going on
  recommendation: done                  all phases [x]
  recommendation: blocked: <reason>     pending phases exist, none eligible

--validate checks the plan structure instead of selecting a phase: one
"<path>:<line>: error|warning: <message>" per finding, then a final
"validate: N error(s), M warning(s)". Exit 0 when clean or warnings only,
1 on validation errors, 2 when the plan is unreadable or unresolvable.

--plans lists every workflow plan reachable from this repo — the current
root's, every linked worktree's, and every wf/* branch with no worktree
(read without checkout) — one pipe-separated line per plan:
  plan|<path or branch:path>|branch|<name>|worktree|<path or ->
      |phases|<done>/<total>|state|<clean|running|failed|blocked>
"""

import argparse
import pathlib
import re
import subprocess
import sys
from datetime import datetime

PHASE_RE = re.compile(r'^- \[([ x!~>])\] \*\*Phase (\d+)\*\*:\s*(.*)$')
TAG_RE = re.compile(r'`(vast)`')
EXEC_RE = re.compile(r'In execution since\s+(\S+)')
WIP_COMMIT_RE = re.compile(r'commit:\s*([0-9a-f]{7,40})\b')


class Phase:
    def __init__(self, status, number, rest):
        self.status = status
        self.number = int(number)
        self.tags = TAG_RE.findall(rest)
        self.title = TAG_RE.sub('', rest).strip()
        self.since = None
        self.wip = False
        self.wip_commit = None
        self.testing = False

    @property
    def age_hours(self):
        if not self.since:
            return None
        try:
            ts = datetime.fromisoformat(self.since.replace('Z', '+00:00'))
        except ValueError:
            return None
        now = datetime.now(ts.tzinfo) if ts.tzinfo else datetime.now()
        return (now - ts).total_seconds() / 3600


def parse_lines(lines):
    phases = []
    for line in lines:
        m = PHASE_RE.match(line.rstrip())
        if m:
            phases.append(Phase(*m.groups()))
        elif phases and line.lstrip().startswith('>'):
            m = EXEC_RE.search(line)
            if m:
                phases[-1].since = m.group(1)
            if 'WIP:' in line:
                phases[-1].wip = True
                cm = WIP_COMMIT_RE.search(line)
                if cm:
                    phases[-1].wip_commit = cm.group(1)
            if 'Testing:' in line:
                phases[-1].testing = True
    return phases


def parse(path):
    with open(path, encoding='utf-8') as f:
        return parse_lines(f)


def wip_desc(p):
    """Human line for a [>] phase's WIP evidence — commit ref included,
    because the resume session diffs from it instead of trusting prose."""
    if not p.wip:
        return 'wip: no'
    if p.wip_commit:
        return f'wip: yes, wip-commit: {p.wip_commit}'
    return 'wip: yes (no commit ref)'


def blockers(phases, i):
    """Numbers of preceding phases that block phases[i]."""
    return [q.number for q in phases[:i] if q.status != 'x']


def repo_root():
    try:
        return subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return '.'


def resolve_plan_path():
    """Locate the active plan at <git root>/.phased/active/*/plan.md.

    Exactly one is expected: one branch, one plan, no discovery. Returns
    (path, error) with error None on success.
    """
    active = pathlib.Path(repo_root()) / '.phased' / 'active'
    found = sorted(active.glob('*/plan.md'))
    if not found:
        return None, (f'no active plan under {active} — run /write-workflow, '
                      'or /import-workflow on an older plan')
    if len(found) > 1:
        names = ', '.join(p.parent.name for p in found)
        return None, (f'several active plans under {active} ({names}); '
                      'exactly one is expected')
    return str(found[0]), None


# --- plan location (--plans) ------------------------------------------------
# Every workflow plan reachable from this repo: the current root's active
# plan(s), every linked worktree's, and every wf/* branch that has no worktree,
# read WITHOUT checking it out. One line per plan, pipe-separated, so a skill
# can disambiguate when several workflows exist.

def _git(args, cwd=None):
    try:
        return subprocess.run(['git'] + args, capture_output=True, text=True,
                              check=True, cwd=cwd).stdout
    except (subprocess.CalledProcessError, OSError):
        return ''


def worktree_map():
    """branch -> checkout path, from `git worktree list --porcelain`."""
    result, path = {}, None
    for line in _git(['worktree', 'list', '--porcelain']).splitlines():
        if line.startswith('worktree '):
            path = line[len('worktree '):]
        elif line.startswith('branch refs/heads/') and path:
            result[line[len('branch refs/heads/'):]] = path
    return result


def plan_state(phases):
    for status, state in (('!', 'failed'), ('~', 'blocked'), ('>', 'running')):
        if any(p.status == status for p in phases):
            return state
    return 'clean'


def list_plans():
    """[(location, branch, checkout-or-None, phases)] for every plan found."""
    rows, root = [], repo_root()
    checkouts = worktree_map()
    for branch, path in checkouts.items():
        for plan in sorted(pathlib.Path(path).glob('.phased/active/*/plan.md')):
            rows.append((str(plan), branch, path, parse(plan)))
    for line in _git(['for-each-ref', '--format=%(refname:short)',
                      'refs/heads/wf/'], cwd=root).splitlines():
        if line in checkouts:
            continue
        names = _git(['ls-tree', '-r', '--name-only', line,
                      '.phased/active/'], cwd=root).splitlines()
        for name in names:
            if not name.endswith('/plan.md'):
                continue
            text = _git(['show', f'{line}:{name}'], cwd=root)
            if text:
                rows.append((f'{line}:{name}', line, None,
                             parse_lines(text.splitlines())))
    return rows


def print_plans():
    for location, branch, checkout, phases in list_plans():
        done = sum(1 for p in phases if p.status == 'x')
        print(f'plan|{location}|branch|{branch}'
              f'|worktree|{checkout or "-"}'
              f'|phases|{done}/{len(phases)}'
              f'|state|{plan_state(phases)}')


def describe(phases, i):
    p = phases[i]
    parts = [f'  {p.number} [{p.status}] {p.title}']
    if p.tags:
        parts.append(' '.join(f'`{t}`' for t in p.tags))
    if p.status == '>':
        age = p.age_hours
        age_s = f'{age:.1f}h' if age is not None else 'unknown'
        parts.append(f'(since: {p.since or "?"}, age: {age_s}, '
                     f'{wip_desc(p)})')
    if p.status == ' ':
        blocked_by = blockers(phases, i)
        parts.append(f'[blocked by: {",".join(map(str, blocked_by))}]'
                     if blocked_by else '[eligible]')
    return ' '.join(parts)


def recommend(phases):
    for i, p in enumerate(phases):
        if p.status == ' ' and not blockers(phases, i):
            return f'next: {p.number}'
    # A [>] phase carrying '> Testing:' is not unfinished work: its code is
    # complete and committed, and only the human's own checks can clear it.
    # Reported as blocked so an unattended run stops and says why, instead of
    # resuming a phase there is nothing left to implement in.
    testing = [p for p in phases if p.status == '>' and p.testing]
    if testing:
        p = testing[0]
        return (f'blocked: phase {p.number} is complete and awaiting the '
                f"human's checks — /wf:close-phase once they pass")
    candidates = [p for p in phases if p.status == '>']
    if candidates:
        p = candidates[0]
        age = p.age_hours
        age_s = f'{age:.1f}h' if age is not None else 'unknown'
        return (f'resume-candidate: {p.number} '
                f'(age: {age_s}, {wip_desc(p)})')
    stuck = [p for p in phases if p.status in '!~']
    if stuck and any(p.status == ' ' for p in phases):
        nums = ' '.join(f'{p.number}[{p.status}]' for p in stuck)
        return f'attention: {nums}'
    if all(p.status == 'x' for p in phases):
        return 'done'
    if stuck:
        nums = ' '.join(f'{p.number}[{p.status}]' for p in stuck)
        return f'attention: {nums}'
    return 'blocked: pending phases exist but none is eligible'


# --- plan validation (--validate) -------------------------------------------
# The validator shares PHASE_RE / TAG_RE / parse() with the selector on
# purpose: a validator that disagreed with the selector about what a phase is
# would be worse than none. Two severities: errors block the run (exit 1),
# warnings never do (exit 0). Anything with a plausible false positive is a
# warning by construction — rejecting a legitimate plan is worse than the
# silent defaults the gate replaces.

KNOWN_NOTE_FIELDS = (
    'Done', 'Files', 'Issue', 'Attempted', 'Repaired', 'Repair attempted',
    'Repair started',
    'Review', 'Blocked', 'WIP', 'Testing', 'In execution since', 'Verify',
    'Verified',
)
EFFORTS = ('low', 'medium', 'high', 'xhigh', 'max')
MODELS = ('fable', 'sonnet', 'opus')
CONFIG_HEADING = 'Suggested execution config'
# Known limitation: NOTE_RE cannot distinguish a new note field from a
# wrapped continuation line of a previous note that happens to begin
# "Capitalised:" — such a line draws the unknown-field warning. Accepted by
# design: it is a warning, and a warning never blocks.
NOTE_RE = re.compile(r'^\s*> ([A-Z][A-Za-z ]*):')
CHECKBOX_RE = re.compile(r'^- \[')
BACKTICK_RE = re.compile(r'`([^`]+)`')
MODE_RE = re.compile(r'^Mode:\s*(\S+)\s*$')
MODES = ('autonomous', 'interactive')


def _is_separator(cells):
    body = [c for c in cells if c]
    return bool(body) and all(re.fullmatch(r':?-+:?', c) for c in body)


def _taglike(tok):
    """A backticked token that reads like an attempted tag but is not one.

    Narrow on purpose: a phase title routinely carries backticked prose
    (`next-phase.py --validate`), and flagging that would make the validator
    cry wolf. Only `parallel`/`group`/`vast` prefixes and `word:number` shapes
    qualify — which also makes the retired `parallel:N` / `group:N` tags on
    a pre-5.0 plan surface as warnings instead of being silently ignored.
    """
    return bool(re.match(r'(parallel|group|vast)', tok)
                or re.match(r'[a-z]+:\d+$', tok))


def validate(path, phases, text):
    """Return a list of (lineno, severity, message) for the plan at path."""
    findings = []

    def add(lineno, severity, msg):
        findings.append((lineno, severity, msg))

    lines = text.splitlines()
    has_parent = False
    mode_value = None
    mode_lineno = None
    heading = None
    phase_linenos = {}
    in_work_plan = False
    work_plan_lineno = None
    config_lineno = None
    config_header = None        # (lineno, cells)
    config_rows = []            # [(lineno, cells)]

    for idx, line in enumerate(lines, 1):
        if line.startswith('Parent:'):
            has_parent = True
        if line.startswith('Mode:'):
            mm = MODE_RE.match(line)
            if mm:
                if mode_value is None:
                    mode_value = mm.group(1).lower()
                    mode_lineno = idx
            else:
                # "Mode: autonomous (fast lane)" must not silently read as
                # "no header" and degrade to the interactive default — the
                # same threat the unknown-value error below exists for.
                add(idx, 'error',
                    'malformed Mode: line "%s" — expected exactly '
                    '"Mode: <value>"' % line.strip())

        if line.startswith('## '):
            heading = line[3:].strip()
            in_work_plan = (heading == 'Work Plan')
            if heading == 'Work Plan' and work_plan_lineno is None:
                work_plan_lineno = idx
            if heading == CONFIG_HEADING and config_lineno is None:
                config_lineno = idx
            continue

        if CHECKBOX_RE.match(line):
            if in_work_plan:
                if not PHASE_RE.match(line):
                    add(idx, 'error',
                        '"%s" in ## Work Plan is not a valid phase line '
                        '(expected "- [ |x|!|~|>] **Phase N**: title")'
                        % line.strip())
            else:
                add(idx, 'warning',
                    'checkbox bullet outside ## Work Plan reads like a phase '
                    'but is not one: "%s"' % line.strip())

        m = PHASE_RE.match(line)
        if m:
            phase_linenos.setdefault(int(m.group(2)), idx)
            for tok in BACKTICK_RE.findall(m.group(3)):
                if TAG_RE.fullmatch('`%s`' % tok):
                    continue
                if _taglike(tok):
                    add(idx, 'warning',
                        'backticked token `%s` on the phase line looks like a '
                        'malformed or retired tag (valid: vast)' % tok)

        if in_work_plan:
            nm = NOTE_RE.match(line)
            if nm and nm.group(1).strip() not in KNOWN_NOTE_FIELDS:
                add(idx, 'warning',
                    'unknown note field "> %s:" (known: %s)'
                    % (nm.group(1).strip(), ', '.join(KNOWN_NOTE_FIELDS)))

        if heading == CONFIG_HEADING and line.startswith('|'):
            cells = [c.strip() for c in line.split('|')]
            if _is_separator(cells):
                continue
            if config_header is None:
                config_header = (idx, cells)
            else:
                config_rows.append((idx, cells))

    if work_plan_lineno is None:
        add(1, 'error', 'no "## Work Plan" section')
    if not has_parent:
        add(1, 'error', 'no "Parent:" line')

    in_exec = [p for p in phases if p.status == '>']
    if len(in_exec) > 1:
        add(work_plan_lineno or 1, 'warning',
            'several phases in execution ([>]): %s — one chat, one phase; '
            'the extras are likely dead sessions to reset'
            % ', '.join(str(p.number) for p in in_exec))
    for p in in_exec:
        ln = phase_linenos.get(p.number, work_plan_lineno or 1)
        if not p.since:
            add(ln, 'warning',
                'phase %d is [>] with no "> In execution since" note — '
                'its age cannot be reported' % p.number)
        if p.wip and not p.wip_commit:
            add(ln, 'warning',
                'phase %d has a "> WIP:" note with no commit: ref — resume '
                'will trust prose instead of a diff (format: done: ... | '
                'missing: ... | next: ... | commit: <hash>)' % p.number)

    if not phases:
        add(work_plan_lineno or 1, 'error', 'no phases in ## Work Plan')
    else:
        numbers = [p.number for p in phases]
        dups = sorted({n for n in numbers if numbers.count(n) > 1})
        if dups:
            add(work_plan_lineno or 1, 'error',
                'duplicate phase number(s): %s'
                % ', '.join(map(str, dups)))
        elif numbers != list(range(1, len(numbers) + 1)):
            add(work_plan_lineno or 1, 'error',
                'phase numbers must be contiguous ascending from 1, found %s'
                % numbers)

    mode_autonomous = mode_value == 'autonomous'
    mode_interactive = mode_value == 'interactive'
    if mode_value is not None and mode_value not in MODES:
        add(mode_lineno, 'error',
            "Mode: '%s' is not one of: %s"
            % (mode_value, ', '.join(MODES)))

    table_present = config_header is not None
    if mode_autonomous and not table_present:
        add(config_lineno or 1, 'error',
            'Mode: autonomous requires a "## Suggested execution config" table')
    if mode_interactive and table_present:
        add(config_lineno or 1, 'warning',
            'Mode: interactive plan carries a "## Suggested execution config" '
            'table, which nothing reads on an interactive plan — a half-'
            'converted plan')

    if table_present:
        hln, hcells = config_header
        got = hcells[1:4] if len(hcells) >= 4 else hcells[1:]
        if got != ['Phase', 'Effort', 'Model']:
            add(hln, 'error',
                'config table header must be "| Phase | Effort | Model |" in '
                'that order, found %s' % got)
        else:
            phase_nums = {p.number for p in phases}
            rowed = set()
            for rln, cells in config_rows:
                if len(cells) < 4:
                    add(rln, 'error',
                        'config table row has too few columns')
                    continue
                pm = re.match(r'^Phase (\d+)$', cells[1])
                if not pm:
                    add(rln, 'error',
                        'config table row is not "| Phase N | ... |": "%s"'
                        % cells[1])
                    continue
                num = int(pm.group(1))
                rowed.add(num)
                if num not in phase_nums:
                    add(rln, 'error',
                        'config table row references Phase %d, which has no '
                        'phase in ## Work Plan' % num)
                if cells[2].lower() not in EFFORTS:
                    add(rln, 'error',
                        'Phase %d Effort "%s" is not one of %s'
                        % (num, cells[2], '|'.join(EFFORTS)))
                if cells[3].lower() not in MODELS:
                    add(rln, 'error',
                        'Phase %d Model "%s" is not one of %s'
                        % (num, cells[3], '|'.join(MODELS)))
            for p in phases:
                if p.number not in rowed:
                    add(work_plan_lineno or 1, 'error',
                        'Phase %d has no row in the execution config table'
                        % p.number)

    return findings


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('plan', nargs='?', default=None,
                    help='path to the plan file (default: the active plan '
                         'under <git root>/.phased/active/)')
    ap.add_argument('--resolve', action='store_true',
                    help='print the active plan path and exit')
    ap.add_argument('--plans', action='store_true',
                    help='list every plan reachable from this repo (current '
                         'root, linked worktrees, wf/* branches read without '
                         'checkout), one pipe-separated line per plan')
    ap.add_argument('--validate', action='store_true',
                    help='validate the plan structure and exit '
                         '(0 clean/warnings, 1 errors, 2 unreadable)')
    args = ap.parse_args()
    if args.plans:
        print_plans()
        return 0
    path = args.plan
    if path is None:
        path, err = resolve_plan_path()
        if err:
            print(f'error: {err}')
            return 2 if args.validate else 1
    if args.resolve:
        print(path)
        return 0
    if args.validate:
        try:
            text = pathlib.Path(path).read_text(encoding='utf-8')
            phases = parse(path)
        except OSError as e:
            print(f'error: cannot read {path}: {e}')
            return 2
        findings = validate(path, phases, text)
        findings.sort(key=lambda f: (f[0], 0 if f[1] == 'error' else 1))
        for lineno, sev, msg in findings:
            print(f'{path}:{lineno}: {sev}: {msg}')
        n_err = sum(1 for f in findings if f[1] == 'error')
        n_warn = len(findings) - n_err
        print(f'validate: {n_err} error(s), {n_warn} warning(s)')
        return 1 if n_err else 0
    try:
        phases = parse(path)
    except OSError as e:
        print(f'error: cannot read {path}: {e}')
        return 1
    if not phases:
        print(f'error: no phases found in {path}')
        return 1
    print('phases:')
    for i in range(len(phases)):
        print(describe(phases, i))
    print(f'recommendation: {recommend(phases)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
