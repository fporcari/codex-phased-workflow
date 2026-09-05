from pathlib import Path
import json
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
    def test_parity_inventory_accounts_for_every_baseline_release(self) -> None:
        expected = set(
            (FIXTURES / "claude-6.35.0-releases.txt").read_text().splitlines()
        )
        inventory = (ROOT / "docs" / "PARITY.md").read_text()
        actual = set(re.findall(r"^\| (\d+\.\d+\.\d+) \|", inventory, re.MULTILINE))
        self.assertEqual(actual, expected)

    def test_selector_json_is_the_single_machine_reader(self) -> None:
        plan = FIXTURES / "claude-originated" / "plan.md"
        result = run_selector(SELECTOR, "--json", str(plan))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["next"], 2)
        self.assertEqual(payload["recommendation"], "next: 2")
        self.assertEqual(payload["meta"]["mode"], "autonomous")
        self.assertIsNone(payload["meta"].get("channel"))
        self.assertEqual(payload["phases"][1]["run"], None)
        self.assertEqual(payload["phases"][1]["blocked_by"], [])

    def test_contract_block_keeps_foreman_owned_fields_only(self) -> None:
        plan_text = textwrap.dedent("""\
            # Context: wf/contract
            Parent: main
            Mode: autonomous

            ## Work Plan
            - [>] **Phase 1**: contract
              - Pattern reference: `library-standard`
              - Files: one.py,
                two.py
              - Decisions: keep the public shape
              - Verify: now — inspect it
              - Done: tests pass
              > In execution since: 2026-08-28T08:00:00+02:00
              > Issue: runtime note
        """)
        result = subprocess.run(
            ["python3", str(SELECTOR), "--contract-block", "1", "-"],
            input=plan_text,
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Pattern reference:", result.stdout)
        self.assertIn("  two.py", result.stdout)
        self.assertIn("Verify: now", result.stdout)
        self.assertNotIn("In execution since", result.stdout)
        self.assertNotIn("Issue:", result.stdout)

    def test_applied_note_is_a_known_portable_outcome(self) -> None:
        plan = (FIXTURES / "codex-originated" / "plan.md").read_text()
        plan = plan.replace(
            "  - Pattern reference:",
            "  > Applied: plan-defect edit — exact declared change\n"
            "  - Pattern reference:",
            1,
        )
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as stream:
            stream.write(plan)
            path = Path(stream.name)
        self.addCleanup(path.unlink)
        result = run_selector(SELECTOR, "--validate", str(path))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("unknown note field 'Applied'", result.stdout)

    def test_channel_and_batches_are_portable_and_validated(self) -> None:
        plan = (FIXTURES / "codex-originated" / "plan.md").read_text()
        plan = plan.replace(
            "  - Pattern reference:",
            "  > Batches: 1 parser | 2 renderer\n  - Pattern reference:",
            1,
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "plan.md"
            path.write_text(plan)
            result = run_selector(SELECTOR, "--validate", str(path))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("unknown note field", result.stdout)
            payload = json.loads(run_selector(SELECTOR, "--json", str(path)).stdout)
            self.assertEqual(payload["meta"]["channel"], "relayed")

            path.write_text(plan.replace("Channel: relayed", "Channel: in-chat"))
            result = run_selector(SELECTOR, "--validate", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn("Mode: autonomous with Channel: in-chat", result.stdout)

            path.write_text(plan.replace("Channel: relayed", "Chanel: relayed"))
            result = run_selector(SELECTOR, "--validate", str(path))
            self.assertEqual(result.returncode, 1)
            self.assertIn('field is "Channel:"', result.stdout)

            path.write_text(plan.replace(
                "> Batches: 1 parser | 2 renderer",
                "> Batches: parser | 3 renderer",
            ))
            result = run_selector(SELECTOR, "--validate", str(path))
            self.assertEqual(result.returncode, 0)
            self.assertIn('body is not "1 <label> | 2 <label> | ..."', result.stdout)

    def test_transport_is_stable_and_repo_keyed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            prefixes = []
            for name in ("one", "two"):
                repository = temporary / name
                plan_directory = repository / ".phased" / "active" / "same-slug"
                plan_directory.mkdir(parents=True)
                plan = plan_directory / "plan.md"
                shutil.copy(FIXTURES / "codex-originated" / "plan.md", plan)
                first = run_selector(SELECTOR, "--transport", str(plan))
                second = run_selector(SELECTOR, "--transport", str(plan))
                self.assertEqual(first.returncode, 0, first.stderr)
                self.assertEqual(first.stdout, second.stdout)
                prefixes.append(first.stdout.strip())
            self.assertNotEqual(prefixes[0], prefixes[1])
            self.assertEqual(Path(prefixes[0]).parent.name, f"phased-workflow-{os.getuid()}")

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

    def test_quality_stamp_round_trips_old_and_final_touch_outcomes(self) -> None:
        legacy = (
            "2026-09-03T10:00:00Z — commit abc1234 — review extended, "
            "QA done, findings 2 confirmed, 1 dismissed"
        )
        current = (
            "2026-09-04T10:00:00Z — commit def5678 — review extended, "
            "QA done, findings 2 confirmed, 1 dismissed, final touch 2 corrections"
        )
        configured = os.environ.get("CLAUDE_PHASED_WORKFLOW_SELECTOR")
        reference = Path(configured) if configured else DEFAULT_REFERENCE
        selectors = [SELECTOR] + ([reference] if reference.exists() else [])
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "plan.md"
            for fixture in sorted(FIXTURES.glob("*/plan.md")):
                for stamps in ((legacy,), (current,), (legacy, current)):
                    path.write_text(
                        fixture.read_text() + "\n## Quality check\n"
                        + "\n".join(f"> Quality check: {stamp}" for stamp in stamps)
                        + "\n"
                    )
                    for selector in selectors:
                        with self.subTest(origin=fixture.parent.name, stamps=stamps, selector=selector):
                            validation = run_selector(selector, "--validate", str(path))
                            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
                            result = run_selector(selector, "--json", str(path))
                            self.assertEqual(result.returncode, 0, result.stderr)
                            payload = json.loads(result.stdout)
                            self.assertEqual(payload["meta"]["quality_check"], stamps[-1])
                            original = json.loads(run_selector(selector, "--json", str(fixture)).stdout)
                            self.assertEqual(payload["phases"], original["phases"])
                            self.assertEqual(payload["next"], original["next"])

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

    def test_autonomous_launcher_maps_fable_to_astra_and_advances_state(self) -> None:
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
                assert "gpt-6-astra" in arguments
                assert "model_reasoning_effort=xhigh" in arguments
                assert "-s" in arguments and "workspace-write" in arguments
                assert "--approve-for-me" not in arguments
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
                print(f"phase {number} committed")
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
            self.assertTrue((plan_directory / "log" / "phase-1.txt").is_file())
            self.assertEqual(
                subprocess.run(
                    ["git", "-C", str(repository), "status", "--porcelain"],
                    check=True,
                    text=True,
                    capture_output=True,
                ).stdout,
                "",
            )

    def test_launcher_refuses_an_interactive_plan_before_spawning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = Path(temporary_directory) / "repo"
            plan_directory = repository / ".phased" / "active" / "interactive"
            plan_directory.mkdir(parents=True)
            plan = (FIXTURES / "codex-originated" / "plan.md").read_text()
            (plan_directory / "plan.md").write_text(
                plan.replace("Mode: autonomous", "Mode: interactive")
            )
            subprocess.run(["git", "init", "-q", "-b", "wf/interactive", str(repository)], check=True)
            launcher = PLUGIN / "scripts" / "run-workflow.sh"
            result = subprocess.run(
                ["bash", str(launcher)],
                cwd=repository,
                env=os.environ.copy(),
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("EVENT: run-end:preflight:mode=interactive", result.stdout)

    def test_worker_launchers_never_auto_approve_escalations(self) -> None:
        for script_name in ("run-workflow.sh", "agent-session.sh"):
            with self.subTest(script=script_name):
                script = (PLUGIN / "scripts" / script_name).read_text()
                self.assertIn("-s workspace-write", script)
                self.assertNotIn("--approve-for-me", script)

    def test_all_direct_worker_entry_points_document_sol_default(self) -> None:
        for skill_name in (
            "execute-phase-agent",
            "repair-phase-agent",
            "quality-check-agent",
        ):
            with self.subTest(skill=skill_name):
                skill = (PLUGIN / "skills" / skill_name / "SKILL.md").read_text()
                self.assertIn("gpt-5.6-sol", skill)
                self.assertIn("agent-session.sh", skill)

    def test_codex_judges_are_loaded_from_shipped_prompt_paths(self) -> None:
        consumers = {
            "execute-phase": "ui-judge.md",
            "execute-phase-agent": "phase-verifier.md",
            "repair-phase": "phase-verifier.md",
            "quality-check": "report-judge.md",
        }
        for skill_name, prompt in consumers.items():
            with self.subTest(skill=skill_name):
                self.assertTrue((PLUGIN / "judges" / prompt).is_file())
                body = (PLUGIN / "skills" / skill_name / "SKILL.md").read_text()
                self.assertIn(f"<PLUGIN_ROOT>/judges/{prompt}", body)

    def test_codex_doctrine_has_no_claude_session_or_worktree_commands(self) -> None:
        body = "\n".join(
            path.read_text()
            for root in (PLUGIN / "skills", PLUGIN / "refs")
            for path in root.rglob("*.md")
        )
        for forbidden in (
            "list_sessions",
            "SendUserFile",
            "SendMessage",
            "ListAgents",
            ".claude/worktrees",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, body)

    def test_recent_claude_doctrine_is_present_with_codex_adaptations(self) -> None:
        common = (PLUGIN / "refs" / "common.md").read_text()
        contracts = (PLUGIN / "refs" / "contracts.md").read_text()
        execution = (PLUGIN / "refs" / "phase-execution.md").read_text()
        foreman = (PLUGIN / "refs" / "foreman.md").read_text()
        write = (PLUGIN / "skills" / "write-workflow" / "SKILL.md").read_text()
        repair = (PLUGIN / "skills" / "repair-phase" / "SKILL.md").read_text()
        quality = (PLUGIN / "skills" / "quality-check" / "SKILL.md").read_text()
        run = (PLUGIN / "skills" / "run-workflow" / "SKILL.md").read_text()

        self.assertIn("Channel: in-chat", contracts)
        self.assertIn("Routing a decision", execution)
        self.assertIn("Planned batches", execution)
        self.assertIn("partial — batch M/K", execution)
        self.assertIn("decision boundaries", write)
        self.assertIn("after the mode answer", write)
        self.assertIn("exactly ONE **phase commit**", common)
        self.assertIn("Satisfying it has a cost bound", repair)
        self.assertIn("Plan-defect confirmed", repair)
        self.assertIn("Collect QA and naming findings without editing", quality)
        self.assertIn("gpt-5.6-sol", foreman)
        self.assertIn("high reasoning", foreman)
        self.assertIn("no default deadline", run)
        self.assertIn("task's workspace", write)


if __name__ == "__main__":
    unittest.main()
