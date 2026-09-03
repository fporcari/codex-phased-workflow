from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
WFDASH = ROOT / "plugins" / "codex-phased-workflow" / "scripts" / "wfdash"
sys.path.insert(0, str(WFDASH))

import roadmap


class DoneTabTest(unittest.TestCase):
    def test_only_finalized_workflows_outside_the_current_roadmap_are_archived(self):
        current = {
            "title": "current",
            "macros": [
                {"n": 1, "title": "Collection", "mini_scope": None, "ends_at": None},
                {"n": 2, "title": "Replica", "mini_scope": None, "ends_at": None},
            ],
        }
        plans = [
            {"slug": "macro1-collection", "state": "done", "phases": [], "branch": None},
            {"slug": "macro2-replica", "state": "active", "phases": [], "branch": None},
            {"slug": "old-parser", "state": "done", "phases": [], "branch": None},
            {"slug": "old-ui", "state": "done", "phases": [], "branch": None},
            {"slug": "orphan-active", "state": "active", "phases": [], "branch": None},
        ]

        tree = roadmap.build_tree(current, plans, "macro2-replica")
        archived = {
            node["slug"]
            for node in tree["nodes"]
            if node["kind"] == "plan" and node["state"] == "done"
        }
        kept = {node["slug"] for node in tree["nodes"] if node["slug"] not in archived}

        self.assertEqual(archived, {"old-parser", "old-ui"})
        self.assertIn("macro1-collection", kept)
        self.assertIn("macro2-replica", kept)
        self.assertIn("orphan-active", kept)

    def test_page_uses_the_same_partition_and_falls_back_from_empty_done(self):
        page = (WFDASH / "index.html").read_text()
        self.assertIn("'done','Done'", page)
        self.assertIn("n.kind==='plan'&&n.state==='done'", page)
        self.assertIn("archived(n)===arch", page)
        self.assertIn("if(level==='done'&&!archivedNodes().length)level='plan';", page)


if __name__ == "__main__":
    unittest.main()
