import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = next(path for path in (ROOT / 'plugins').iterdir()
              if (path / 'scripts/next-phase.py').exists())


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


reader = module('reader', PLUGIN / 'scripts/next-phase.py')
roadmap = module('roadmap', PLUGIN / 'scripts/wfdash/roadmap.py')


class ReaderRegressions(unittest.TestCase):
    def test_nested_decisions_survive_handoff(self):
        text = ('## Work Plan\n- [ ] **Phase 1**: work\n'
                '  - Decisions:\n    - Preserve keys\n      - Including legacy keys\n'
                '  - Done: checks pass\n  > Issue: runtime only\n')
        lines = text.splitlines()
        phases, _, bounds = reader.parse_lines(lines)
        self.assertEqual(reader.contract_block(lines, phases, bounds, 1), lines[2:6])

    def test_examples_are_not_executable(self):
        text = ('## Example\n- [ ] **Phase 99**: example\n'
                '## Work Plan\n- [ ] **Phase 1**: real\n'
                '## Notes\n- [ ] **Phase 98**: example\n')
        phases, _, _ = reader.parse_lines(text.splitlines())
        self.assertEqual([p.number for p in phases], [1])

    def test_legacy_headingless_plan_remains_readable(self):
        phases, _, _ = reader.parse_lines(['- [ ] **Phase 1**: old plan'])
        self.assertEqual(len(phases), 1)

    def test_conflicting_mode_is_rejected(self):
        text = 'Parent: main\nMode: interactive\nMode: autonomous\n## Work Plan\n- [ ] **Phase 1**: work\n'
        phases, meta, _ = reader.parse_lines(text.splitlines())
        self.assertEqual(meta['mode'], 'interactive')
        errors = reader.validate(Path('plan.md'), phases, text)
        self.assertTrue(any(level == 'error' and 'duplicate Mode' in message
                            for _, level, message in errors))

    def test_authored_roadmap_and_legacy_headings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.phased'
            path.mkdir()
            (path / 'roadmap.md').write_text(
                '# Roadmap\n## Macro 1 (current): first\n- Objective: usable API\n'
                '- Ends at: compatible endpoint\n## Macro 2: second\n'
                '## Macro-phase 3 — legacy\n- Mini-scope: old style\n')
            macros = roadmap.read_roadmap(directory)['macros']
        self.assertEqual([m['n'] for m in macros], [1, 2, 3])
        self.assertEqual(macros[0]['mini_scope'], 'usable API')
        self.assertEqual(macros[0]['ends_at'], 'compatible endpoint')
        self.assertEqual(macros[2]['mini_scope'], 'old style')


if __name__ == '__main__':
    unittest.main()
