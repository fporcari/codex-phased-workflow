import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = next(path for path in (ROOT / 'plugins').iterdir()
              if (path / 'scripts/runtime.py').exists())
HOST = 'claude' if PLUGIN.name == 'wf' else 'codex'


class LauncherBudgetTest(unittest.TestCase):
    def test_budget_includes_repairs_and_zero_starts_nothing(self):
        for limit, fail, expected in ((0, False, 0), (1, False, 1), (1, True, 1)):
            with self.subTest(limit=limit, fail=fail), tempfile.TemporaryDirectory() as directory:
                work = Path(directory)
                repo = work / 'repo'
                plan_dir = repo / '.phased/active/example'
                plan_dir.mkdir(parents=True)
                plan = plan_dir / 'plan.md'
                plan.write_text('Parent: main\nMode: autonomous\n## Work Plan\n'
                                '- [ ] **Phase 1**: first\n  - Done: check\n'
                                '- [ ] **Phase 2**: second\n  - Done: check\n'
                                '## Suggested execution config\n| Phase | Effort | Model |\n'
                                '|---|---|---|\n| Phase 1 | low | opus |\n| Phase 2 | low | opus |\n')
                for args in [('init', '-q'), ('config', 'user.name', 'Fixture'),
                             ('config', 'user.email', 'fixture@example.test'),
                             ('add', '.'), ('commit', '-qm', 'plan')]:
                    subprocess.run(['git', *args], cwd=repo, check=True)
                binary = work / HOST
                binary.write_text(textwrap.dedent('''\
                    #!/usr/bin/env python3
                    import os
                    from pathlib import Path
                    import subprocess
                    import sys
                    if '--version' in sys.argv:
                        print('2.1.211 (fixture)')
                        sys.exit(0)
                    count = Path(os.environ['MOCK_COUNT'])
                    count.write_text(count.read_text() + 'call\\n' if count.exists() else 'call\\n')
                    plan = next(Path.cwd().glob('.phased/active/*/plan.md'))
                    marker = '!' if os.environ['MOCK_FAIL'] == '1' else 'x'
                    body = plan.read_text().replace('- [ ]', '- [' + marker + ']', 1)
                    if marker == '!':
                        notes = '  > Issue: fixture failure\\n  > Attempted: one fix\\n  - Done:'
                        body = body.replace('  - Done:', notes, 1)
                    plan.write_text(body)
                    subprocess.run(['git', 'add', '.'], check=True)
                    subprocess.run(['git', 'commit', '-qm', 'outcome'], check=True)
                    print('durable outcome')
                '''))
                binary.chmod(0o755)
                count = work / 'count'
                env = dict(os.environ, PATH=str(work) + os.pathsep + os.environ['PATH'],
                           RUN_WORKFLOW_MAX_ATTEMPTS=str(limit), MOCK_FAIL=str(int(fail)),
                           MOCK_COUNT=str(count), TMPDIR=str(work / 'transport'),
                           RUN_WORKFLOW_SESSION_TIMEOUT='0')
                result = subprocess.run(['bash', str(PLUGIN / 'scripts/run-workflow.sh')],
                                        cwd=repo, env=env, capture_output=True, text=True, timeout=20)
                calls = len(count.read_text().splitlines()) if count.exists() else 0
                self.assertEqual(calls, expected, result.stdout + result.stderr)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(subprocess.check_output(['git', 'status', '--porcelain'],
                                                         cwd=repo, text=True), '')
                self.assertEqual(plan.read_text().count('- [x]'), 1 if limit and not fail else 0)


if __name__ == '__main__':
    unittest.main()
