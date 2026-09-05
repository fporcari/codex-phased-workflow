"""Host-neutral ownership and durable worker-outcome checks."""
import argparse
import fcntl
import importlib.util
import os
from pathlib import Path
import subprocess
import sys


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def lock(path, command):
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise RuntimeError('writer-already-active')
    os.set_inheritable(fd, True)
    os.environ['PHASED_RUN_LOCK_PID'] = str(os.getpid())
    os.execvp(command[0], command)


def record(plan, before, log, name):
    plan = Path(plan).resolve()
    root = Path(git(plan.parent, 'rev-parse', '--show-toplevel'))
    head = git(root, 'rev-parse', 'HEAD')
    if head == before:
        raise RuntimeError('missing-outcome-commit')
    if subprocess.call(['git', '-C', str(root), 'merge-base', '--is-ancestor', before, head]):
        raise RuntimeError('worker-rewrote-history')
    if git(root, 'status', '--porcelain'):
        raise RuntimeError('dirty-worker-outcome')
    relative = str(plan.relative_to(root))
    previous = git(root, 'show', before + ':' + relative)
    current = git(root, 'show', head + ':' + relative)
    spec = importlib.util.spec_from_file_location('wf_reader', Path(__file__).with_name('next-phase.py'))
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    old_phases = reader.parse_lines(previous.splitlines())[0]
    new_phases = reader.parse_lines(current.splitlines())[0]
    if not old_phases or [p.number for p in old_phases] != [p.number for p in new_phases]:
        raise RuntimeError('worker-changed-phase-boundaries')
    changes = [(old.status, new.status) for old, new in zip(old_phases, new_phases)
               if old.status != new.status]
    allowed = {(' ', 'x'), (' ', '!'), (' ', '~'), (' ', '>'),
               ('>', 'x'), ('>', '!'), ('>', '~'), ('!', 'x'), ('x', '!')}
    if previous == current or len(changes) > 1 or any(pair not in allowed for pair in changes):
        raise RuntimeError('invalid-worker-transition')
    if Path(name).name != name:
        raise RuntimeError('invalid-log-name')
    target = plan.parent / 'log' / name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(Path(log).read_bytes())
    git(root, 'add', '--', str(target.relative_to(root)))
    git(root, 'commit', '--amend', '--no-edit', '-q')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    own = commands.add_parser('lock')
    own.add_argument('path')
    own.add_argument('command', nargs=argparse.REMAINDER)
    outcome = commands.add_parser('record')
    for field in ('plan', 'before', 'log', 'name'):
        outcome.add_argument(field)
    args = parser.parse_args()
    try:
        if args.action == 'lock':
            lock(args.path, args.command)
        else:
            record(args.plan, args.before, args.log, args.name)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print('EVENT: runtime-error:%s' % error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
