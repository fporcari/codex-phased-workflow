import concurrent.futures
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "plugins" / "codex-phased-workflow" / "scripts" / "wfdash" / "outbox.py"


def load_outbox():
    spec = importlib.util.spec_from_file_location("codex_wfdash_outbox", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OutboxTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.outbox = load_outbox()
        self.outbox.TMP = Path(self.temporary.name) / "transport"
        self.repo = str(Path(self.temporary.name) / "repo")

    def tearDown(self):
        self.temporary.cleanup()

    def test_owner_partition_survives_atomic_drain(self):
        self.outbox.append(self.repo, "run-workflow", owner="thread-a", value=1)
        self.outbox.append(self.repo, "stop", owner="thread-b", value=2)
        self.outbox.append(self.repo, "newflow", value=3)
        result = self.outbox.drain_split(self.repo, "thread-a")
        self.assertEqual([event["value"] for event in result["served"]], [1])
        self.assertEqual([event["value"] for event in result["remaining"]], [2, 3])
        adopted = self.outbox.drain_split(self.repo, "thread-a", include_unowned=True)
        self.assertEqual([event["value"] for event in adopted["served"]], [3])
        self.assertEqual([event["value"] for event in adopted["remaining"]], [2])

    def test_concurrent_writers_do_not_lose_events(self):
        def write(number):
            self.outbox.append(self.repo, "event", owner=f"thread-{number % 3}", number=number)

        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            list(executor.map(write, range(120)))
        events = self.outbox.read(self.repo)
        self.assertEqual({event["number"] for event in events}, set(range(120)))
        self.assertEqual(len(events), 120)

    def test_duplicate_guard_is_one_locked_operation(self):
        def request(_):
            return self.outbox.append_if_absent(
                self.repo, "run-workflow", 0, owner="thread-a"
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(request, range(30)))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(len(self.outbox.read(self.repo)), 1)

    def test_transport_is_private_and_codex_namespaced(self):
        self.outbox.append(self.repo, "event", owner="thread-a")
        queue = self.outbox.path(self.repo)
        self.assertIn("-codex-outbox", queue.name)
        self.assertEqual(os.stat(queue.parent).st_mode & 0o777, 0o700)
        self.assertEqual(os.stat(queue).st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
