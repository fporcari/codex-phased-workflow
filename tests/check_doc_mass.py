"""Doc-mass budget: every skill's closure stays under a declared ceiling.

A skill's closure is its SKILL.md plus every ref file it names — the doctrine
a session must ingest before doing any work. The 6.14.0 split exists because
that mass had grown past what a session reliably follows; this check turns
the arms race into a measured quantity, so growth pays its budget at merge
time instead of degrading sessions in the field.

Usage: check_doc_mass.py <skills_dir> <refs_dir>
Emits one stdout line per violation; exits 0 always (the harness asserts on
output, same contract as the other check_*.py guards). Pass --report to
emit the closure table instead.
"""
import os
import re
import sys

# Ceiling in closure lines. Current worst case (close-phase) is ~1400;
# the ceiling grants headroom for honest growth but fails the next monolith.
CEILING = 1500


def closure(skill_path, refs_dir, violations):
    # Direct citations only: the refs the SKILL.md itself names are what the
    # skill can cause a session to ingest. A ref pointing at a section of
    # another ref is a lazy pointer, not an ingest instruction — and the
    # layout map in common.md would otherwise pull every ref into every
    # skill, flattening the very split this check protects.
    text = open(skill_path).read()
    lines = text.count("\n")
    seen = set()
    # A refs/-prefixed citation of a missing file is a broken reference; a
    # bare name that matches no ref (plan.md, notes.md, verify.md) is plan
    # vocabulary, not a citation, and is ignored.
    for name in re.findall(r"refs/([a-z-]+\.md)", text):
        if not os.path.exists(os.path.join(refs_dir, name)):
            violations.append(f"{skill_path}: cites refs/{name}, which does not exist")
    for name in re.findall(r"\b([a-z][a-z-]*\.md)\b", text):
        ref_path = os.path.join(refs_dir, name)
        if name in seen or not os.path.exists(ref_path):
            continue
        seen.add(name)
        lines += open(ref_path).read().count("\n")
    return lines, sorted(seen)


def main():
    args = [a for a in sys.argv[1:] if a != "--report"]
    report = "--report" in sys.argv
    skills_dir, refs_dir = args
    rows = []
    violations = []
    for skill in sorted(os.listdir(skills_dir)):
        path = os.path.join(skills_dir, skill, "SKILL.md")
        if not os.path.exists(path):
            continue
        lines, refs = closure(path, refs_dir, violations)
        rows.append((lines, skill, refs))
        if lines > CEILING:
            violations.append(
                f"{path}: closure {lines} lines exceeds the {CEILING}-line "
                f"budget (refs: {', '.join(refs) or 'none'})")
    if report:
        table = [f"{lines:5d}  {skill}  ({', '.join(refs) or 'no refs'})"
                 for lines, skill, refs in sorted(rows, reverse=True)]
        sys.stdout.write("\n".join(table) + "\n")
    elif violations:
        sys.stdout.write("\n".join(violations) + "\n")


if __name__ == "__main__":
    main()
