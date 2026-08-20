from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "codex-phased-workflow"
SELECTOR = PLUGIN / "scripts" / "next-phase.py"
FIXTURES = ROOT / "tests" / "fixtures"
DEFAULT_REFERENCE = Path.home() / "Development" / "claude-phased-workflow-repo" / "plugins" / "wf" / "scripts" / "next-phase.py"


def run_selector(selector: Path, *arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(selector), *arguments],
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )


class ProtocolCompatibilityTest(unittest.TestCase):
    def test_both_origins_validate(self) -> None:
        for fixture in sorted(FIXTURES.glob("*/plan.md")):
            with self.subTest(fixture=fixture.parent.name):
                result = run_selector(SELECTOR, "--validate", str(fixture))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_expected_continuations(self) -> None:
        claude_plan = FIXTURES / "claude-originated" / "plan.md"
        codex_plan = FIXTURES / "codex-originated" / "plan.md"
        self.assertIn("recommendation: next: 2", run_selector(SELECTOR, str(claude_plan)).stdout)
        self.assertIn("recommendation: next: 1", run_selector(SELECTOR, str(codex_plan)).stdout)

    def test_claude_reference_selector_agrees_when_available(self) -> None:
        configured = os.environ.get("CLAUDE_PHASED_WORKFLOW_SELECTOR")
        reference = Path(configured) if configured else DEFAULT_REFERENCE
        if not reference.exists():
            self.skipTest("Claude reference selector is not available")
        for fixture in sorted(FIXTURES.glob("*/plan.md")):
            with self.subTest(fixture=fixture.parent.name):
                expected = run_selector(reference, str(fixture))
                actual = run_selector(SELECTOR, str(fixture))
                self.assertEqual(actual.returncode, expected.returncode)
                self.assertEqual(actual.stdout, expected.stdout)

    def test_autonomous_launcher_uses_sol_and_advances_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            repository = temporary / "repo"
            plan_directory = repository / ".phased" / "active" / "portable"
            binary_directory = temporary / "bin"
            plan_directory.mkdir(parents=True)
            binary_directory.mkdir()
            shutil.copy(FIXTURES / "codex-originated" / "plan.md", plan_directory / "plan.md")

            subprocess.run(["git", "init", "-q", "-b", "wf/portable", str(repository)], check=True)
            subprocess.run(["git", "-C", str(repository), "config", "user.name", "Protocol Test"], check=True)
            subprocess.run(["git", "-C", str(repository), "config", "user.email", "protocol@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repository), "commit", "-qm", "wf: plan"], check=True)

            mock_codex = binary_directory / "codex"
            mock_codex.write_text(textwrap.dedent("""\
                #!/usr/bin/env python3
                from pathlib import Path
                import re
                import subprocess
                import sys

                arguments = sys.argv[1:]
                assert "gpt-5.6-sol" in arguments
                checkout = Path(arguments[arguments.index("-C") + 1])
                prompt = arguments[-1]
                number = re.search(r"Phase (\\d+)", prompt).group(1)
                plan = next((checkout / ".phased" / "active").glob("*/plan.md"))
                text = plan.read_text()
                text = text.replace(
                    f"- [ ] **Phase {number}**:",
                    f"- [x] **Phase {number}**:",
                    1,
                )
                plan.write_text(text)
                subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
                subprocess.run(
                    ["git", "-C", str(checkout), "commit", "-qm", f"wf(phase {number}): mock"],
                    check=True,
                )
            """))
            mock_codex.chmod(0o755)

            environment = os.environ.copy()
            environment["PATH"] = f"{binary_directory}:{environment['PATH']}"
            launcher = PLUGIN / "scripts" / "run-workflow.sh"
            result = subprocess.run(
                ["bash", str(launcher)],
                cwd=repository,
                env=environment,
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("EVENT: run-end:done", result.stdout)
            self.assertIn("- [x] **Phase 1**", (plan_directory / "plan.md").read_text())


if __name__ == "__main__":
    unittest.main()
