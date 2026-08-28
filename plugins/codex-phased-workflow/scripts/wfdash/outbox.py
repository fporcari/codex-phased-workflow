#!/usr/bin/env python3
"""Owner-scoped dashboard proposals outside the working tree."""

import argparse
import contextlib
import fcntl
import hashlib
import itertools
import json
import os
import pathlib
import threading
import time


TMP = (pathlib.Path(os.environ.get("TMPDIR") or "/tmp")
       / f"phased-workflow-{os.getuid()}")
_SERIAL = itertools.count()
_locks = {}
_locks_guard = threading.Lock()


def private_dir(directory):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        os.chmod(directory, 0o700)


def _thread_lock(path):
    with _locks_guard:
        return _locks.setdefault(str(path), threading.RLock())


@contextlib.contextmanager
def _locked(path, exclusive):
    private_dir(path.parent)
    with _thread_lock(path):
        descriptor = os.open(
            path.with_name(path.name + ".lock"), os.O_CREAT | os.O_RDWR, 0o600
        )
        try:
            fcntl.flock(
                descriptor, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            )
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)


def key(repo):
    root = os.path.realpath(os.path.expanduser(repo))
    digest = hashlib.sha1(root.encode()).hexdigest()[:12]
    return f"{pathlib.Path(root).name}-{digest}"


def path(repo):
    return TMP / f"{key(repo)}-codex-outbox.jsonl"


def _append_line(queue, event):
    descriptor = os.open(queue, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
    with contextlib.suppress(OSError):
        os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")


def _entries(queue):
    try:
        raw = queue.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    entries = []
    for line in raw.splitlines():
        try:
            entries.append(json.loads(line))
        except ValueError:
            continue
    return entries


def append(repo, kind, owner=None, **fields):
    event = dict(fields, kind=kind, at=time.time())
    if owner:
        event["owner"] = owner
    queue = path(repo)
    with _locked(queue, exclusive=True):
        _append_line(queue, event)
    return event


def append_if_absent(repo, kind, fresh_after, owner=None, **fields):
    queue = path(repo)
    with _locked(queue, exclusive=True):
        if any(
            event.get("kind") == kind
            and event.get("owner") == owner
            and event.get("at", 0) > fresh_after
            for event in _entries(queue)
        ):
            return None
        event = dict(fields, kind=kind, at=time.time())
        if owner:
            event["owner"] = owner
        _append_line(queue, event)
    return event


def read(repo):
    queue = path(repo)
    try:
        with _locked(queue, exclusive=False):
            return _entries(queue)
    except OSError:
        return _entries(queue)


def _serve(event, owner, include_unowned):
    stamped = event.get("owner")
    if owner is None:
        return True
    if stamped is None:
        return include_unowned
    return stamped == owner


def drain_split(repo, owner=None, include_unowned=False):
    queue = path(repo)
    aside = queue.with_name(
        f"{queue.name}.draining-{os.getpid()}-{next(_SERIAL)}"
    )
    with _locked(queue, exclusive=True):
        try:
            os.rename(queue, aside)
        except OSError:
            return {"served": [], "remaining": []}
        events = _entries(aside)
        served = [
            event for event in events if _serve(event, owner, include_unowned)
        ]
        remaining = [event for event in events if event not in served]
        for event in remaining:
            _append_line(queue, event)
    with contextlib.suppress(OSError):
        os.remove(aside)
    return {"served": served, "remaining": remaining}


def main():
    parser = argparse.ArgumentParser(description="Dashboard requests for a Codex task.")
    parser.add_argument("-C", "--cwd", default=os.getcwd())
    parser.add_argument("--drain", action="store_true")
    parser.add_argument("--owner", default=None)
    parser.add_argument("--include-unowned", action="store_true")
    args = parser.parse_args()
    if args.drain:
        owner = args.owner if args.owner is not None else None
        payload = drain_split(args.cwd, owner, args.include_unowned)
    else:
        payload = {"pending": read(args.cwd)}
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
