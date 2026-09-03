from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugins" / "codex-phased-workflow"
LAUNCHER = PLUGIN / "scripts" / "run-workflow.sh"
SELECTOR = PLUGIN / "scripts" / "next-phase.py"
FIXTURE = ROOT / "tests" / "fixtures" / "codex-originated" / "plan.md"


class OrchestrationTest(unittest.TestCase):
    def repository(self, plan_text=None):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        repo = root / "repo"
        plan_dir = repo / ".phased" / "active" / "portable"
        bin_dir = root / "bin"
        plan_dir.mkdir(parents=True)
        bin_dir.mkdir()
        (plan_dir / "plan.md").write_text(plan_text or FIXTURE.read_text())
        subprocess.run(["git", "init", "-q", "-b", "wf/portable", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Orchestration Test"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "orchestration@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "wf: plan for portable"], check=True)
        return temporary, repo, plan_dir, bin_dir

    def environment(self, bin_dir, **values):
        environment = os.environ.copy()
        environment["PATH"] = f"{bin_dir}:{environment['PATH']}"
        environment.update(values)
        return environment

    def write_mock(self, bin_dir, source):
        mock = bin_dir / "codex"
        mock.write_text(textwrap.dedent(source))
        mock.chmod(0o755)

    def test_worker_timeout_ends_as_interruption_without_dirtying_plan(self):
        temporary, repo, _, bin_dir = self.repository()
        self.addCleanup(temporary.cleanup)
        self.write_mock(
            bin_dir,
            """\
            #!/usr/bin/env python3
            import time
            time.sleep(30)
            """,
        )
        result = subprocess.run(
            ["bash", str(LAUNCHER)],
            cwd=repo,
            env=self.environment(bin_dir, RUN_WORKFLOW_SESSION_TIMEOUT="1"),
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("EVENT: run-end:codex-exit-", result.stdout)
        self.assertEqual(
            subprocess.run(
                ["git", "-C", str(repo), "status", "--porcelain"],
                text=True,
                capture_output=True,
                check=True,
            ).stdout,
            "",
        )

    def test_plan_defect_timeout_falls_through_to_one_fresh_repair(self):
        temporary, repo, plan_dir, bin_dir = self.repository()
        self.addCleanup(temporary.cleanup)
        self.write_mock(
            bin_dir,
            """\
            #!/usr/bin/env python3
            from pathlib import Path
            import subprocess
            import sys

            args = sys.argv[1:]
            assert "gpt-5.6-sol" in args
            checkout = Path(args[args.index("-C") + 1])
            prompt = args[-1]
            plan = next((checkout / ".phased" / "active").glob("*/plan.md"))
            text = plan.read_text()
            if "Repair exactly" in prompt:
                text = text.replace("- [!] **Phase 1**:", "- [x] **Phase 1**:", 1)
                text = text.replace("> Attempted: mock evidence", "> Attempted: mock evidence\\n  > Repaired: fresh repair proved the contract", 1)
                subject = "wf(phase 1): repaired"
            else:
                text = text.replace("- [ ] **Phase 1**:", "- [!] **Phase 1**:", 1)
                text = text.replace("  - Pattern reference:", "  > Issue: plan-defect claim — before-text -> after-text\\n  > Attempted: mock evidence\\n  - Pattern reference:", 1)
                subject = "wf(phase 1): failed"
            plan.write_text(text)
            subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
            subprocess.run(["git", "-C", str(checkout), "commit", "-qm", subject], check=True)
            print(subject)
            """,
        )
        result = subprocess.run(
            ["bash", str(LAUNCHER)],
            cwd=repo,
            env=self.environment(bin_dir, RUN_WORKFLOW_CONSULT_TIMEOUT="0"),
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )
        prefix = subprocess.run(
            ["python3", str(SELECTOR), "--transport", str(plan_dir / "plan.md")],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        phase_log = Path(prefix + "-phase-1.log")
        evidence = phase_log.read_text() if phase_log.is_file() else "no phase log"
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr + evidence)
        self.assertIn("EVENT: phase-needs-foreman:1", result.stdout)
        self.assertIn("EVENT: phase-repaired:1", result.stdout)
        self.assertIn("Repaired: fresh repair", (plan_dir / "plan.md").read_text())
        self.assertTrue((plan_dir / "log" / "repair-1.txt").is_file())

    def test_plan_defect_wait_has_no_default_deadline_and_honours_stop(self):
        plan = FIXTURE.read_text().replace(
            "- [ ] **Phase 1**:",
            "- [!] **Phase 1**:",
            1,
        ).replace(
            "  - Pattern reference:",
            "  > Issue: plan-defect claim — exact premise is wrong\n"
            "  > Attempted: mock evidence\n"
            "  - Pattern reference:",
            1,
        )
        temporary, repo, plan_dir, bin_dir = self.repository(plan)
        self.addCleanup(temporary.cleanup)
        prefix = subprocess.run(
            ["python3", str(SELECTOR), "--transport", str(plan_dir / "plan.md")],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        process = subprocess.Popen(
            ["bash", str(LAUNCHER)],
            cwd=repo,
            env=self.environment(bin_dir),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        lines = []
        for line in process.stdout:
            lines.append(line)
            if "EVENT: phase-needs-foreman:1" in line:
                Path(prefix + "-foreman-answer").write_text("not-a-verdict\n")
            elif "EVENT: consult-answer-invalid:1:not-a-verdict" in line:
                Path(prefix + "-stop-request").write_text("stop while consulting\n")
        process.stdout.close()
        status = process.wait(timeout=10)
        output = "".join(lines)
        self.assertEqual(status, 0, output)
        self.assertIn("EVENT: consult-answer-invalid:1:not-a-verdict", output)
        self.assertIn("EVENT: run-end:stopped-by-request:0/", output)
        self.assertIn("- [!] **Phase 1**", (plan_dir / "plan.md").read_text())
        self.assertFalse((plan_dir / "log" / "repair-1.txt").exists())
        self.assertNotIn('RUN_WORKFLOW_CONSULT_TIMEOUT:-600', LAUNCHER.read_text())

    def test_stale_stop_is_removed_and_phase_budget_counts_landings(self):
        plan = FIXTURE.read_text()
        plan = plan.replace(
            "## Suggested execution config",
            "- [ ] **Phase 2**: second portable phase\n"
            "  - Pattern reference: `library-standard`\n"
            "  - Files: second.txt\n"
            "  - Details: create it.\n"
            "  - Done: second.txt exists\n\n"
            "## Suggested execution config",
        ).replace("| Phase 1 | xhigh | fable |", "| Phase 1 | xhigh | fable |\n| Phase 2 | medium | opus |")
        temporary, repo, plan_dir, bin_dir = self.repository(plan)
        self.addCleanup(temporary.cleanup)
        self.write_mock(
            bin_dir,
            """\
            #!/usr/bin/env python3
            from pathlib import Path
            import re
            import subprocess
            import sys

            args = sys.argv[1:]
            checkout = Path(args[args.index("-C") + 1])
            number = re.search(r"Phase (\\d+)", args[-1]).group(1)
            plan = next((checkout / ".phased" / "active").glob("*/plan.md"))
            plan.write_text(plan.read_text().replace(f"- [ ] **Phase {number}**:", f"- [x] **Phase {number}**:", 1))
            subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
            subprocess.run(["git", "-C", str(checkout), "commit", "-qm", f"wf(phase {number}): landed"], check=True)
            """,
        )
        prefix = subprocess.run(
            ["python3", str(SELECTOR), "--transport", str(plan_dir / "plan.md")],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        stale = Path(prefix + "-stop-request")
        stale.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        stale.write_text("stale")
        result = subprocess.run(
            ["bash", str(LAUNCHER)],
            cwd=repo,
            env=self.environment(bin_dir, RUN_WORKFLOW_MAX_PHASES="1"),
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("EVENT: phase-done:1", result.stdout)
        self.assertIn("EVENT: run-end:phase-budget:1/1", result.stdout)
        text = (plan_dir / "plan.md").read_text()
        self.assertIn("- [x] **Phase 1**", text)
        self.assertIn("- [ ] **Phase 2**", text)

    def test_declared_plan_defect_can_be_applied_without_repair_session(self):
        temporary, repo, plan_dir, bin_dir = self.repository()
        self.addCleanup(temporary.cleanup)
        self.write_mock(
            bin_dir,
            """\
            #!/usr/bin/env python3
            from pathlib import Path
            import subprocess
            import sys

            args = sys.argv[1:]
            checkout = Path(args[args.index("-C") + 1])
            prompt = args[-1]
            if "Repair exactly" in prompt:
                raise SystemExit("repair must not launch on green apply")
            plan = next((checkout / ".phased" / "active").glob("*/plan.md"))
            text = plan.read_text().replace("- [ ] **Phase 1**:", "- [!] **Phase 1**:", 1)
            text = text.replace("  - Pattern reference:", "  > Issue: plan-defect claim — before-text -> after-text\\n  > Attempted: mock evidence\\n  - Pattern reference:", 1)
            plan.write_text(text)
            subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
            subprocess.run(["git", "-C", str(checkout), "commit", "-qm", "wf(phase 1): failed"], check=True)
            print("claim committed")
            """,
        )
        prefix = subprocess.run(
            ["python3", str(SELECTOR), "--transport", str(plan_dir / "plan.md")],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        process = subprocess.Popen(
            ["bash", str(LAUNCHER)],
            cwd=repo,
            env=self.environment(
                bin_dir,
                RUN_WORKFLOW_CONSULT_TIMEOUT="5",
                RUN_WORKFLOW_APPLY_TIMEOUT="5",
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        lines = []
        for line in process.stdout:
            lines.append(line)
            if "EVENT: phase-needs-foreman:1" in line:
                Path(prefix + "-foreman-answer").write_text("PLAN-DEFECT: APPLY\n")
            elif "EVENT: phase-apply-wait:1" in line:
                plan_path = plan_dir / "plan.md"
                text = plan_path.read_text().replace("- [!] **Phase 1**:", "- [x] **Phase 1**:", 1)
                text = text.replace(
                    "  > Attempted: mock evidence",
                    "  > Attempted: mock evidence\n  > Applied: plan-defect edit — declared one-line edit",
                    1,
                )
                plan_path.write_text(text)
                subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
                subprocess.run(
                    ["git", "-C", str(repo), "commit", "-qm", "wf: plan defect phase 1 — applied — declared edit"],
                    check=True,
                )
                Path(prefix + "-apply-outcome").write_text("green\n")
        process.stdout.close()
        status = process.wait(timeout=10)
        output = "".join(lines)
        self.assertEqual(status, 0, output)
        self.assertIn("EVENT: phase-applied:1", output)
        self.assertIn("EVENT: run-end:done", output)
        self.assertIn("> Applied: plan-defect edit", (plan_dir / "plan.md").read_text())
        self.assertFalse((plan_dir / "log" / "repair-1.txt").exists())

    def test_graceful_stop_finishes_in_flight_phase_before_stopping(self):
        plan = FIXTURE.read_text().replace(
            "## Suggested execution config",
            "- [ ] **Phase 2**: must remain pending\n"
            "  - Pattern reference: `library-standard`\n"
            "  - Files: second.txt\n"
            "  - Details: create it.\n"
            "  - Done: second.txt exists\n\n"
            "## Suggested execution config",
        ).replace(
            "| Phase 1 | xhigh | fable |",
            "| Phase 1 | xhigh | fable |\n| Phase 2 | medium | opus |",
        )
        temporary, repo, plan_dir, bin_dir = self.repository(plan)
        self.addCleanup(temporary.cleanup)
        self.write_mock(
            bin_dir,
            """\
            #!/usr/bin/env python3
            from pathlib import Path
            import re
            import subprocess
            import sys
            import time

            args = sys.argv[1:]
            checkout = Path(args[args.index("-C") + 1])
            number = re.search(r"Phase (\\d+)", args[-1]).group(1)
            time.sleep(1)
            plan = next((checkout / ".phased" / "active").glob("*/plan.md"))
            plan.write_text(plan.read_text().replace(f"- [ ] **Phase {number}**:", f"- [x] **Phase {number}**:", 1))
            subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
            subprocess.run(["git", "-C", str(checkout), "commit", "-qm", f"wf(phase {number}): landed"], check=True)
            print(f"phase {number} landed")
            """,
        )
        prefix = subprocess.run(
            ["python3", str(SELECTOR), "--transport", str(plan_dir / "plan.md")],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        process = subprocess.Popen(
            ["bash", str(LAUNCHER)],
            cwd=repo,
            env=self.environment(bin_dir),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        lines = []
        for line in process.stdout:
            lines.append(line)
            if "EVENT: phase-started:1" in line:
                Path(prefix + "-stop-request").write_text("stop after this phase\n")
        process.stdout.close()
        status = process.wait(timeout=10)
        output = "".join(lines)
        self.assertEqual(status, 0, output)
        self.assertIn("EVENT: phase-done:1", output)
        self.assertIn("EVENT: run-end:stopped-by-request:1/", output)
        text = (plan_dir / "plan.md").read_text()
        self.assertIn("- [x] **Phase 1**", text)
        self.assertIn("- [ ] **Phase 2**", text)


if __name__ == "__main__":
    unittest.main()
