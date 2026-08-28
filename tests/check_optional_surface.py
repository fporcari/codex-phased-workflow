#!/usr/bin/env python3
"""Guard that wfdash remains optional and never becomes workflow authority."""

import os
import re
import sys


SURFACE_RE = re.compile(r"/dashboard|wfdash|optional live dashboard", re.I)
FALLBACK_RE = re.compile(
    r"optional|fallback|without|no dashboard|textual|plain list|proposal|never acts|not a precondition",
    re.I,
)
PRECONDITION_RE = re.compile(
    r"dashboard[^.\n]*\b(then continue|then proceed|before continuing|must be open|is required|wait for)"
    r"|\b(requires?|needs?|only after) the dashboard",
    re.I,
)
WINDOW = 8


def violations(roots):
    findings = []
    for root in roots:
        for directory, _, names in sorted(os.walk(root)):
            for name in sorted(names):
                if not name.endswith(".md"):
                    continue
                path = os.path.join(directory, name)
                lines = open(path, encoding="utf-8").read().splitlines()
                dashboard_skill = f"{os.sep}dashboard{os.sep}" in path
                for index, line in enumerate(lines):
                    if PRECONDITION_RE.search(line):
                        findings.append(
                            f"{path}:{index + 1}: makes dashboard a precondition: {line.strip()}"
                        )
                    if dashboard_skill or not SURFACE_RE.search(line):
                        continue
                    nearby = lines[max(0, index - WINDOW): index + WINDOW + 1]
                    if not any(FALLBACK_RE.search(candidate) for candidate in nearby):
                        findings.append(
                            f"{path}:{index + 1}: dashboard mention has no optional/fallback clause"
                        )
    return findings


if __name__ == "__main__":
    found = violations(sys.argv[1:])
    if found:
        print("\n".join(found))
    raise SystemExit(1 if found else 0)
