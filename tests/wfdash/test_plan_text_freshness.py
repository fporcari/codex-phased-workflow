import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
WFDASH = ROOT / "plugins" / "codex-phased-workflow" / "scripts" / "wfdash"
sys.path.insert(0, str(WFDASH))

import core


PLAN = """# Context: wf/myplan
Mode: autonomous

## Work Plan
- [ ] **Phase 1**: one
  - Done: a
"""


class PlanTextFreshnessTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        phased = self.repo / ".phased"
        phased.mkdir(parents=True)
        (phased / "roadmap.md").write_text("# Roadmap\n\n## Macro-phase 1 — one\n")
        for state, slug in (("active", "myplan"), ("done", "oldplan")):
            directory = phased / state / slug
            directory.mkdir(parents=True)
            (directory / "plan.md").write_text(PLAN)
        subprocess.run(["git", "init", "-q", "-b", "wf/myplan", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Dashboard Test"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "dashboard@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "wf: plan for myplan"], check=True)

    def tearDown(self):
        self.temporary.cleanup()

    def test_rewrite_moves_only_its_stamp_and_state_publishes_it(self):
        before = core.text_stamps(self.repo)
        self.assertEqual(sorted(before["plans"]), ["myplan", "oldplan"])
        self.assertIsNotNone(before["roadmap"])

        active = self.repo / ".phased" / "active" / "myplan" / "plan.md"
        active.write_text(PLAN.replace("one", "ONE REWRITTEN"))
        os.utime(active, (before["plans"]["myplan"] + 10,) * 2)

        after = core.text_stamps(self.repo)
        self.assertNotEqual(after["plans"]["myplan"], before["plans"]["myplan"])
        self.assertEqual(after["plans"]["oldplan"], before["plans"]["oldplan"])
        self.assertEqual(after["roadmap"], before["roadmap"])
        self.assertEqual(core.Board(self.repo).state()["stamps"], after)

    def test_page_invalidates_both_text_readers_by_stamp(self):
        page = (WFDASH / "index.html").read_text()
        self.assertNotIn("if(planText[key]!==undefined)return;", page)
        self.assertIn("planStamp[key]===stamp", page)
        for reader in ("loadRoadmap", "loadPlanText"):
            body = page.split(f"async function {reader}(", 1)[1].split("\n}", 1)[0]
            self.assertIn("loadText(", body)


if __name__ == "__main__":
    unittest.main()
