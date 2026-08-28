import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
WFDASH = ROOT / "plugins" / "codex-phased-workflow" / "scripts" / "wfdash"
sys.path.insert(0, str(WFDASH))

import outbox
import server


class FakeBoard:
    def __init__(self, repo):
        self.repo = str(repo)

    def state(self):
        return {
            "repo": self.repo,
            "active": "portable",
            "plan": {
                "next": 1,
                "blocked_by": None,
                "phases": [{"n": 1, "status": " ", "title": "Build", "span": [6, 9]}],
                "header_span": [1, 5],
                "meta": {"mode": "autonomous"},
            },
            "foreman": {"title": "wf:portable:foreman"},
            "tree": {"label": "portable", "phases": []},
            "alerts": [],
            "lifecycle": [],
            "attempt": None,
            "limits": {},
        }

    def plan_source(self, slug):
        return "# Context\nMode: autonomous\n\n## Work Plan\n- [ ] **Phase 1**: Build\n  - Done: green\n"


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        outbox.TMP = Path(self.temporary.name) / "transport"
        server.ONE_SHOTS.clear()
        server.Handler.board = FakeBoard(self.repo)
        server.Handler.token = "test-token"
        server.Handler.owner = "thread-a"
        self.httpd = server.serve(0, False)
        server.Handler.cookie_port = self.httpd.server_address[1]
        self.base = f"http://127.0.0.1:{server.Handler.cookie_port}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def request(self, path, *, token=None, data=None, headers=None):
        request_headers = dict(headers or {})
        if token:
            request_headers[server.TOKEN_HEADER] = token
        body = None if data is None else json.dumps(data).encode()
        if body is not None:
            request_headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.base + path,
            headers=request_headers,
            data=body,
            method="POST" if data is not None else "GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as error:
            return error.code, dict(error.headers), error.read()

    def test_every_read_requires_token_and_one_shot_cannot_replay(self):
        status, _, _ = self.request("/api/state")
        self.assertEqual(status, 403)
        one_shot = server.new_one_shot()
        status, headers, body = self.request(f"/?k={one_shot}")
        self.assertEqual(status, 200)
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertNotIn(b"test-token", body)
        status, _, _ = self.request(f"/?k={one_shot}")
        self.assertEqual(status, 403)

    def test_write_perimeter_and_owner_stamp(self):
        status, _, _ = self.request(
            "/api/launch",
            token="test-token",
            data={"road": "unattended"},
            headers={"Origin": "https://example.invalid"},
        )
        self.assertEqual(status, 403)
        status, _, body = self.request(
            "/api/launch", token="test-token", data={"road": "unattended"}
        )
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["queued"])
        self.assertEqual(outbox.read(self.repo)[0]["owner"], "thread-a")

    def test_codex_owner_and_foreman_queue_feed_the_claude_ui_contract(self):
        status, _, body = self.request("/api/sessions", token="test-token")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["owner"]["name"], "thread-a")
        status, _, _ = self.request(
            "/api/foreman", token="test-token", data={"text": "keep the contract"}
        )
        self.assertEqual(status, 200)
        status, _, body = self.request("/api/mirror", token="test-token")
        mirror = json.loads(body)
        self.assertEqual(mirror["owner"], "thread-a")
        self.assertEqual(mirror["exchange"][0]["text"], "keep the contract")

    def test_new_workflow_uses_codex_command_dialect(self):
        board = server.Handler.board
        original = board.state
        board.state = lambda: {"active": None}
        try:
            status, _, body = self.request(
                "/api/newflow",
                token="test-token",
                data={"name": "same-ui", "scope": "adapt the harness"},
            )
        finally:
            board.state = original
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(
            payload["command"], "/write-workflow same-ui — adapt the harness"
        )
        self.assertEqual(outbox.read(self.repo)[0]["owner"], "thread-a")

    def test_server_never_spawns_or_edits_workflow(self):
        source = (WFDASH / "server.py").read_text()
        self.assertNotIn("import subprocess", source)
        self.assertNotIn("codex exec", source)
        self.assertNotIn("Popen(", source)

    def test_probe_reuses_server_and_updates_owner(self):
        server.write_registry(str(self.repo), server.Handler.cookie_port, "test-token")
        found = server.probe(str(self.repo), owner="thread-b")
        self.assertIsNotNone(found)
        self.assertEqual(found["port"], server.Handler.cookie_port)
        self.assertEqual(server.Handler.owner, "thread-b")

    def test_stale_registry_is_removed(self):
        path = server.registry_path(str(self.repo))
        outbox.private_dir(path.parent)
        path.write_text(
            json.dumps({"port": 1, "pid": 999999, "repo": str(self.repo), "token": "dead"})
        )
        self.assertIsNone(server.probe(str(self.repo)))
        self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
