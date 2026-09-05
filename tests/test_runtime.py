import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = next(path for path in (ROOT / 'plugins').iterdir()
              if (path / 'scripts/runtime.py').exists())
RUNTIME = PLUGIN / 'scripts/runtime.py'


class RuntimeTest(unittest.TestCase):
    def test_duplicate_owner_is_rejected_and_exit_releases_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            ready = Path(directory) / 'ready'
            prefix = [sys.executable, str(RUNTIME), 'lock', directory + '/lock']
            command = prefix + [sys.executable, '-c',
                                'from pathlib import Path; import time; '
                                'Path(%r).touch(); time.sleep(30)' % str(ready)]
            child = subprocess.Popen(command)
            try:
                deadline = time.monotonic() + 5
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertTrue(ready.exists())
                second = subprocess.run(prefix + ['true'], capture_output=True, text=True)
                self.assertNotEqual(second.returncode, 0)
                self.assertIn('writer-already-active', second.stderr)
            finally:
                child.terminate()
                child.wait(timeout=5)
            self.assertEqual(subprocess.run(prefix + ['true']).returncode, 0)

    def test_only_committed_clean_outcomes_can_archive_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'repo'
            root.mkdir()
            env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')

            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], env=env, text=True).strip()
            git('init', '-q')
            git('config', 'user.name', 'Fixture')
            git('config', 'user.email', 'fixture@example.test')
            plan = root / 'plan.md'
            plan.write_text('## Work Plan\n- [ ] **Phase 1**: result\n- [ ] **Phase 2**: tail\n')
            git('add', '.')
            git('commit', '-qm', 'plan')
            before = git('rev-parse', 'HEAD')
            log = Path(directory) / 'worker.log'
            log.write_text('completed output\n')
            command = [sys.executable, str(RUNTIME), 'record', str(plan), before, str(log), 'phase.txt']
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertIn('missing-outcome-commit', result.stderr)
            plan.write_text('## Work Plan\n- [x] **Phase 1**: result\n- [ ] **Phase 2**: tail\n')
            git('add', '.')
            git('commit', '-qm', 'outcome')
            dirty = root / 'leftover'
            dirty.touch()
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertIn('dirty-worker-outcome', result.stderr)
            dirty.unlink()
            correct = plan.read_text()
            plan.write_text(correct.replace('- [ ]', '- [x]'))
            git('add', '.')
            git('commit', '--amend', '--no-edit', '-q')
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertIn('invalid-worker-transition', result.stderr)
            plan.write_text(correct)
            git('add', '.')
            git('commit', '--amend', '--no-edit', '-q')
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(git('status', '--porcelain'), '')
            self.assertEqual(git('show', 'HEAD:log/phase.txt'), 'completed output')
            self.assertEqual(git('rev-list', '--count', 'HEAD'), '2')


if __name__ == '__main__':
    unittest.main()
