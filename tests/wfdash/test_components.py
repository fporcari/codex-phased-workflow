import hashlib
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
WFDASH = ROOT / "plugins" / "codex-phased-workflow" / "scripts" / "wfdash"
sys.path.insert(0, str(WFDASH))

import checks
import roadmap


class ComponentsTest(unittest.TestCase):
    def test_execution_verify_notes_replace_authored_fields(self):
        phase = {
            "n": 5,
            "notes": [
                {"kind": "Verify", "text": "now — a tick survives reload"},
                {"kind": "Review", "text": "inspect the heading"},
            ],
            "verify": [{"text": "now — an authored fallback"}],
        }
        result = checks.phase_checks(phase)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["when"], "now")
        self.assertEqual(result[0]["text"], "a tick survives reload")
        self.assertTrue(result[0]["id"].startswith("5:"))

    def test_icons_derive_from_marker_and_durable_notes(self):
        rejected = {"status": "x", "notes": [{"kind": "Review", "text": "wrong"}]}
        testing = {"status": ">", "notes": [{"kind": "Testing", "text": "human"}]}
        self.assertEqual(roadmap.phase_icon(rejected)["icon"], "✓!")
        self.assertEqual(roadmap.phase_icon(testing)["icon"], "👤")
        self.assertEqual(roadmap.phase_icon({"status": "!", "notes": []})["icon"], "✕")

    def test_page_renders_tags_and_all_selector_recommendations_generically(self):
        page = (WFDASH / "index.html").read_text()
        self.assertIn("(f.tags||[])", page)
        self.assertIn("p.recommendation", page)
        self.assertIn("resume-candidate:", page)
        self.assertNotIn("__WFDASH_TOKEN__", page)
        self.assertNotIn("/wf:", page)

    def test_page_keeps_the_claude_visual_shell(self):
        page = (WFDASH / "index.html").read_text()
        style = page.split("<style>", 1)[1].split("</style>", 1)[0]
        shell = page.split("<script>", 1)[0]
        self.assertEqual(
            hashlib.sha256(style.encode()).hexdigest(),
            "cf5ba851381b30ea219891ec79029e8b5dfacdb9a0014f5792ac012186a6f068",
        )
        self.assertEqual(
            hashlib.sha256(shell.encode()).hexdigest(),
            "5cca68630ddeb4bda37cb3c4d50aa27f1151f3936f7d093d674b60a19d28395e",
        )


if __name__ == "__main__":
    unittest.main()
