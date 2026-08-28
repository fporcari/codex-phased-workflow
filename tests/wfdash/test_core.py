import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
WFDASH = ROOT / "plugins" / "codex-phased-workflow" / "scripts" / "wfdash"
FIXTURE = ROOT / "tests" / "fixtures" / "claude-originated" / "plan.md"
sys.path.insert(0, str(WFDASH))

import core


class CoreTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        self.plan_dir = self.repo / ".phased" / "active" / "portable"
        self.plan_dir.mkdir(parents=True)
        shutil.copy(FIXTURE, self.plan_dir / "plan.md")
        (self.plan_dir / "foreman.json").write_text(
            json.dumps(
                {
                    "workflow": "portable",
                    "title": "wf:portable:foreman",
                    "host": "codex",
                    "claimed_at": "2026-08-28T08:00:00+02:00",
                }
            )
        )
        subprocess.run(["git", "init", "-q", "-b", "wf/portable", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Dashboard Test"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "dashboard@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "wf: plan for portable"], check=True)

    def tearDown(self):
        self.temporary.cleanup()

    def test_state_uses_selector_payload_and_portable_foreman(self):
        state = core.Board(self.repo).state()
        self.assertEqual(state["active"], "portable")
        self.assertEqual(state["plan"]["next"], 2)
        self.assertEqual(state["plan"]["slug"], "portable")
        self.assertEqual(state["plan"]["done"], 1)
        self.assertEqual(state["plan"]["total"], 2)
        self.assertEqual(len(state["plan"]["lifecycle"]), 4)
        self.assertEqual(state["foreman"]["host"], "codex")
        self.assertEqual(state["tree"]["label"], "portable")
        self.assertEqual(state["groups"], {"by_phase": {}, "off_plan": []})
        self.assertFalse(state["totals"]["available"])
        self.assertFalse(state["limits"]["transcripts"])
        self.assertEqual(state["plan"]["phases"][1]["checks"], [])

    def test_plan_source_and_lifecycle_are_durable(self):
        board = core.Board(self.repo)
        self.assertIn("Phase 2", board.plan_source("portable"))
        self.assertEqual(board.state()["lifecycle"][0]["subject"], "wf: plan for portable")

    def test_latest_finished_plan_is_read_from_its_workflow_branch(self):
        subprocess.run(["git", "-C", str(self.repo), "branch", "main"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "switch", "-qc", "wf/finished"], check=True)
        target = self.repo / ".phased" / "done" / "portable"
        target.parent.mkdir(parents=True)
        (self.repo / ".phased" / "active" / "portable").rename(target)
        plan = target / "plan.md"
        plan.write_text(plan.read_text().replace("- [ ] **Phase 2**:", "- [x] **Phase 2**:", 1))
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "wf: archive portable"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "switch", "-q", "main"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "rm", "-qr", ".phased"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "parent without workflow state"], check=True)
        state = core.Board(self.repo).state()
        self.assertIsNone(state["active"])
        self.assertEqual(state["display"], "portable")
        self.assertEqual(state["display_state"], "done")
        self.assertIsNone(state["plan"])
        self.assertIsNone(state["finished"]["next"])
        self.assertEqual(state["finished"]["slug"], "portable")


if __name__ == "__main__":
    unittest.main()
