"""Portable workflow state for the Codex dashboard.

The selector is the only plan parser. This module composes its JSON with git,
roadmap, durable logs, and the owner-private launcher transport.
"""

import datetime
import json
import os
import pathlib
import subprocess

import checks
import roadmap


HERE = pathlib.Path(__file__).resolve().parent
SELECTOR = HERE.parent / "next-phase.py"


def run(command, cwd, stdin=None, check=True):
    result = subprocess.run(
        command,
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return result.stdout


def git(repo, *args):
    return run(["git", *args], repo)


def repo_root(repo):
    return os.path.realpath(git(repo, "rev-parse", "--show-toplevel").strip())


def selection(repo, plan=None, text=None):
    command = ["python3", str(SELECTOR), "--json"]
    if text is not None:
        command.append("-")
    elif plan is not None:
        command.append(str(plan))
    return json.loads(run(command, repo, stdin=text))


def _decorate(payload):
    for phase in payload["phases"]:
        phase.update(roadmap.phase_icon(phase))
        phase["checks"] = checks.phase_checks(phase)
    return payload


def _local_plans(repo):
    root = pathlib.Path(repo) / ".phased"
    entries = []
    for state in ("active", "done"):
        for plan in sorted((root / state).glob("*/plan.md")):
            payload = _decorate(selection(repo, plan=plan))
            relative = os.path.relpath(plan, repo)
            updated = run(
                ["git", "log", "-1", "--format=%ct", "--", relative],
                repo,
                check=False,
            ).strip()
            entries.append(
                {
                    "slug": plan.parent.name,
                    "dir": str(plan.parent),
                    "path": str(plan),
                    "state": "active" if state == "active" else "done",
                    "phases": payload["phases"],
                    "payload": payload,
                    "branch": None,
                    "updated": int(updated) if updated.isdigit() else 0,
                }
            )
    return entries


def _reachable_active_plans(repo, known):
    entries = []
    output = run(["python3", str(SELECTOR), "--plans"], repo, check=False)
    for line in output.splitlines():
        parts = line.split("|")
        if len(parts) % 2:
            continue
        row = dict(zip(parts[::2], parts[1::2]))
        location = row.get("plan")
        if not location or location in known:
            continue
        checkout = row.get("worktree")
        branch = row.get("branch")
        if checkout and checkout != "-":
            payload = _decorate(selection(repo, plan=location))
            directory = str(pathlib.Path(location).parent)
        else:
            prefix = f"{branch}:"
            if not branch or not location.startswith(prefix):
                continue
            plan_path = location[len(prefix):]
            source = git(repo, "show", f"{branch}:{plan_path}")
            payload = _decorate(selection(repo, text=source))
            directory = None
        slug = pathlib.PurePosixPath(payload["path"]).parent.name
        if payload["path"] == "-":
            slug = pathlib.PurePosixPath(location.split(":", 1)[-1]).parent.name
        updated = run(
            ["git", "log", "-1", "--format=%ct", branch or "HEAD"],
            repo,
            check=False,
        ).strip()
        entries.append(
            {
                "slug": slug,
                "dir": directory,
                "path": location,
                "state": "active",
                "phases": payload["phases"],
                "payload": payload,
                "branch": branch,
                "updated": int(updated) if updated.isdigit() else 0,
            }
        )
    return entries


def _branch_done_plans(repo):
    entries = []
    current = git(repo, "branch", "--show-current").strip()
    branches = run(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads/wf/"],
        repo,
        check=False,
    ).splitlines()
    for branch in branches:
        if branch == current:
            continue
        names = run(
            ["git", "ls-tree", "-r", "--name-only", branch, ".phased/done/"],
            repo,
            check=False,
        ).splitlines()
        for name in names:
            if not name.endswith("/plan.md"):
                continue
            source = git(repo, "show", f"{branch}:{name}")
            payload = _decorate(selection(repo, text=source))
            updated = run(
                ["git", "log", "-1", "--format=%ct", branch, "--", name],
                repo,
                check=False,
            ).strip()
            entries.append(
                {
                    "slug": pathlib.PurePosixPath(name).parent.name,
                    "dir": None,
                    "path": f"{branch}:{name}",
                    "state": "done",
                    "phases": payload["phases"],
                    "payload": payload,
                    "branch": branch,
                    "updated": int(updated) if updated.isdigit() else 0,
                }
            )
    return entries


def all_plans(repo):
    local = _local_plans(repo)
    known = {entry["path"] for entry in local}
    return local + _reachable_active_plans(repo, known) + _branch_done_plans(repo)


def active_plan(repo):
    plans = [entry for entry in all_plans(repo) if entry["state"] == "active"]
    here = os.path.realpath(repo)
    local = [
        entry
        for entry in plans
        if entry["dir"] and os.path.realpath(entry["dir"]).startswith(here + os.sep)
    ]
    return local[0] if len(local) == 1 else None


def latest_finished(plans):
    done = [entry for entry in plans if entry["state"] == "done"]
    return max(done, key=lambda entry: entry.get("updated", 0), default=None)


def _foreman(entry):
    if not entry or not entry["dir"]:
        return None
    path = pathlib.Path(entry["dir"]) / "foreman.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _age_hours(value):
    if not value:
        return None
    try:
        stamp = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    now = datetime.datetime.now(stamp.tzinfo) if stamp.tzinfo else datetime.datetime.now()
    return (now - stamp).total_seconds() / 3600


def alerts(entry):
    if entry is None:
        return [{"level": "info", "text": "No single local active plan."}]
    found = []
    for phase in entry["phases"]:
        if phase["status"] == "!":
            found.append({"level": "error", "text": f"Phase {phase['n']} failed."})
        elif phase["status"] == "~":
            found.append({"level": "error", "text": f"Phase {phase['n']} is blocked."})
        elif phase["status"] == ">" and (_age_hours(phase.get("since")) or 0) > 2:
            found.append({"level": "warning", "text": f"Phase {phase['n']} has run for over two hours."})
    return found


def lifecycle(repo):
    raw = git(
        repo,
        "log",
        "--date=iso-strict",
        "--format=%H%x1f%ad%x1f%s",
        "--grep=^wf",
        "-n",
        "100",
    )
    rows = []
    for line in raw.splitlines():
        fields = line.split("\x1f", 2)
        if len(fields) == 3:
            rows.append({"commit": fields[0], "at": fields[1], "subject": fields[2]})
    return rows


def _plan_commit(repo, slug):
    return run(
        [
            "git",
            "log",
            "-1",
            "--format=%h",
            "--all",
            "-E",
            f"--grep=^wf: plan for {slug}$",
        ],
        repo,
        check=False,
    ).strip() or None


def workflow_lifecycle(repo, entry):
    payload = entry["payload"]
    phases = payload["phases"]
    proofs = {
        "planned": _plan_commit(repo, entry["slug"]),
        "executing": (
            f"{len(phases)}/{len(phases)} phases closed"
            if phases and all(phase["status"] == "x" for phase in phases)
            else None
        ),
        "quality": payload.get("meta", {}).get("quality_check"),
        "finalized": entry["path"] if entry["state"] == "done" else None,
    }
    labels = (
        ("planned", "plan"),
        ("executing", "exec"),
        ("quality", "quality"),
        ("finalized", "final"),
    )
    reached = False
    result = []
    for key, label in labels:
        proof = proofs[key]
        if proof:
            state = "done"
        elif reached:
            state = "todo"
        else:
            state = "now"
            reached = True
        result.append({"key": key, "label": label, "state": state, "proof": proof})
    return result


def plan_view(repo, entry):
    if entry is None:
        return None
    payload = dict(entry["payload"])
    phases = payload["phases"]
    meta = payload.get("meta", {})
    payload.update(
        {
            "slug": entry["slug"],
            "dir": entry["dir"] or entry["path"],
            "done": sum(phase["status"] == "x" for phase in phases),
            "total": len(phases),
            "mode": meta.get("mode"),
            "parent": meta.get("parent"),
            "quality": meta.get("quality_check"),
            "foreman": _foreman(entry),
            "median_ratio": None,
            "lifecycle": workflow_lifecycle(repo, entry),
        }
    )
    return payload


def transport_prefix(repo, entry):
    if entry is None or not entry["path"] or ":" in entry["path"]:
        return None
    result = run(
        ["python3", str(SELECTOR), "--transport", entry["path"]],
        repo,
        check=False,
    ).strip()
    return result or None


def attempt(repo, entry, tail=120):
    prefix = transport_prefix(repo, entry)
    if prefix is None:
        return None
    path = pathlib.Path(prefix + "-run.log")
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return {"path": str(path), "mtime": path.stat().st_mtime, "lines": lines[-tail:]}


class Board:
    def __init__(self, repo):
        self.repo = repo_root(repo)

    def state(self):
        plans = all_plans(self.repo)
        active = active_plan(self.repo)
        finished = latest_finished(plans)
        display = active or finished
        active_slug = active["slug"] if active else None
        display_slug = display["slug"] if display else None
        tree = roadmap.build_tree(
            roadmap.read_roadmap(self.repo), plans, display_slug
        )
        plan = plan_view(self.repo, active)
        finished_plan = plan_view(self.repo, finished) if active is None else None
        alerts_found = alerts(active)
        alerts_found.append(
            {
                "level": "info",
                "text": (
                    "Codex does not expose stable task transcripts, todo lists, "
                    "token usage, or cost telemetry to local plugins."
                ),
            }
        )
        return {
            "generated": datetime.datetime.now().timestamp(),
            "repo": self.repo,
            "active": active_slug,
            "display": display_slug,
            "display_state": display["state"] if display else None,
            "plan": plan,
            "finished": finished_plan,
            "foreman": _foreman(active),
            "tree": tree,
            "chats": [],
            "groups": {"by_phase": {}, "off_plan": []},
            "alerts": alerts_found,
            "totals": {
                "agents": 0,
                "active": 0,
                "turns": 0,
                "output": 0,
                "reread": 0,
                "usd": 0.0,
                "unpriced": [],
                "available": False,
            },
            "lifecycle": lifecycle(self.repo),
            "attempt": attempt(self.repo, active),
            "limits": {
                "transcripts": False,
                "todos": False,
                "cost": False,
                "reason": "Codex exposes no stable plugin API for these feeds.",
            },
        }

    def plan_source(self, slug):
        for entry in all_plans(self.repo):
            if entry["slug"] != slug:
                continue
            if entry["dir"]:
                return pathlib.Path(entry["path"]).read_text(
                    encoding="utf-8", errors="replace"
                )
            branch, path = entry["path"].split(":", 1)
            return git(self.repo, "show", f"{branch}:{path}")
        return None
