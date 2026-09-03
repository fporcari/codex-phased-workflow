#!/usr/bin/env python3
"""Authenticated localhost dashboard for portable Codex workflow state.

The state tick includes plan-text mtimes so the page can invalidate its own
cache without polling each full plan and roadmap body.
"""

import argparse
import atexit
import contextlib
import datetime
import http.cookies
import http.server
import json
import os
import pathlib
import secrets
import threading
import time
import urllib.parse
import urllib.request

import core
import outbox
import roadmap


MAX_BODY = 64 * 1024
WRITE_PATHS = (
    "/api/foreman",
    "/api/newflow",
    "/api/launch",
    "/api/stop",
    "/api/oneshot",
    "/api/owner",
)
DEFAULT_PORT = 8787
PORT_SPAN = 20
RUN_REQUEST_TTL = 30 * 60
TOKEN_HEADER = "X-Wfdash-Token"
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
ONE_SHOTS = set()
ONE_SHOTS_LOCK = threading.Lock()
HERE = pathlib.Path(__file__).parent

LOCKED_PAGE = """<!doctype html><meta charset="utf-8">
<title>wfdash — link already used</title>
<h1>This dashboard link has already been used.</h1>
<p>Run the dashboard skill again to mint a fresh local link.</p>"""


def cookie_name(port):
    return f"codex_wfdash_{port}_session"


def new_one_shot():
    key = secrets.token_urlsafe(24)
    with ONE_SHOTS_LOCK:
        ONE_SHOTS.add(key)
    return key


def spend_one_shot(key):
    if not key:
        return False
    with ONE_SHOTS_LOCK:
        if key not in ONE_SHOTS:
            return False
        ONE_SHOTS.remove(key)
    return True


class Handler(http.server.BaseHTTPRequestHandler):
    board = None
    token = None
    owner = None
    cookie_port = None
    grant = None
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _send(self, body, content_type="application/json; charset=utf-8", code=200):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if self.grant:
            self.send_header(
                "Set-Cookie",
                f"{cookie_name(self.cookie_port)}={self.grant}; "
                "HttpOnly; SameSite=Strict; Path=/",
            )
            self.grant = None
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, code=200):
        self._send(json.dumps(payload, ensure_ascii=False), code=code)

    def authenticated(self):
        header = self.headers.get(TOKEN_HEADER)
        if (
            header
            and header.isascii()
            and secrets.compare_digest(header, self.token)
        ):
            return True
        jar = http.cookies.SimpleCookie(self.headers.get("Cookie") or "")
        morsel = jar.get(cookie_name(self.cookie_port))
        return bool(
            morsel
            and morsel.value.isascii()
            and secrets.compare_digest(morsel.value, self.token)
        )

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        if spend_one_shot(query.get("k", [""])[0]):
            self.grant = self.token
        elif not self.authenticated():
            if parsed.path in ("/", "/index.html"):
                return self._send(LOCKED_PAGE, "text/html; charset=utf-8", 403)
            return self._json({"error": "not authenticated"}, 403)
        try:
            if parsed.path in ("/", "/index.html"):
                return self._send(
                    (HERE / "index.html").read_text(encoding="utf-8"),
                    "text/html; charset=utf-8",
                )
            if parsed.path == "/api/state":
                state = self.board.state()
                state["queue"] = self.queue_state()
                state["owner"] = Handler.owner
                return self._json(state)
            if parsed.path == "/api/log":
                return self._json(self.log(query))
            if parsed.path == "/api/plantext":
                return self._json(self.plantext(query))
            if parsed.path == "/api/roadmap":
                return self._json(self.roadmap(query))
            if parsed.path == "/api/mirror":
                return self._json(self.mirror())
            if parsed.path == "/api/sessions":
                return self._json(self.sessions())
            return self._json({"error": "not found"}, 404)
        except BrokenPipeError:
            return None
        except Exception as exc:
            return self._json({"error": f"{type(exc).__name__}: {exc}"}, 500)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                self.close_connection = True
                return self._json({"error": "body too large"}, 413)
            raw = self.rfile.read(length)
            if parsed.path not in WRITE_PATHS:
                return self._json({"error": "not found"}, 404)
            if not self.authenticated():
                return self._json({"error": "write token missing or wrong"}, 403)
            origin = self.headers.get("Origin")
            if origin and urllib.parse.urlparse(origin).hostname not in LOCAL_HOSTS:
                return self._json({"error": "origin not allowed"}, 403)
            body = json.loads(raw or b"{}")
            if parsed.path == "/api/foreman":
                return self._json(self.foreman(body))
            if parsed.path == "/api/newflow":
                return self._json(self.newflow(body))
            if parsed.path == "/api/launch":
                return self._json(self.launch(body))
            if parsed.path == "/api/stop":
                return self._json(self.stop())
            if parsed.path == "/api/oneshot":
                return self._json({"k": new_one_shot()})
            if parsed.path == "/api/owner":
                return self._json(self.set_owner(body))
            return self._json({"error": "unknown endpoint"}, 404)
        except BrokenPipeError:
            return None
        except Exception as exc:
            return self._json({"error": f"{type(exc).__name__}: {exc}"}, 500)

    def stamp(self):
        return {"owner": Handler.owner} if Handler.owner else {}

    def queue_state(self):
        events = outbox.read(self.board.repo)
        mine = [event for event in events if event.get("owner") == Handler.owner]
        unowned = [event for event in events if not event.get("owner")]
        return {"mine": mine, "unowned": unowned, "other_count": len(events) - len(mine) - len(unowned)}

    def set_owner(self, body):
        owner = body.get("owner")
        if owner is not None and (not isinstance(owner, str) or not owner.strip()):
            return {"error": "owner must be a non-empty Codex thread id"}
        Handler.owner = owner.strip() if owner else None
        return {"owner": Handler.owner}

    def foreman(self, body):
        text = (body.get("text") or "").strip()
        if not text:
            return {"error": "nothing to send"}
        state = self.board.state()
        target = ((state.get("foreman") or {}).get("title"))
        event = outbox.append(
            self.board.repo, "foreman", text=text, target=target, **self.stamp()
        )
        return {"queued": True, "target": target, "request": event}

    def newflow(self, body):
        name = (body.get("name") or "").strip()
        scope = (body.get("scope") or body.get("text") or "").strip()
        if not name:
            return {"error": "name the workflow"}
        if self.board.state().get("active"):
            return {"error": "an active plan already exists"}
        command = f"/write-workflow {name}" + (f" — {scope}" if scope else "")
        event = outbox.append(
            self.board.repo,
            "write-workflow",
            command=command,
            name=name,
            scope=scope,
            **self.stamp(),
        )
        return {"queued": True, "command": command, "request": event}

    def launch(self, body):
        state = self.board.state()
        plan = state.get("plan")
        if plan is None:
            return {"error": "no plan"}
        if plan["next"] is None:
            blocked = plan.get("blocked_by")
            return {"error": f"phase {blocked} is not closed" if blocked else "every phase is done"}
        if body.get("road") == "chat":
            return {"road": "chat", "phase": plan["next"], "command": "/execute-phase"}
        event = outbox.append_if_absent(
            self.board.repo,
            "run-workflow",
            time.time() - RUN_REQUEST_TTL,
            command="/run-workflow",
            phase=plan["next"],
            slug=state["active"],
            **self.stamp(),
        )
        if event is None:
            return {"error": "an unattended run is already queued for this task"}
        return {"queued": True, "road": "unattended", "request": event}

    def stop(self):
        event = outbox.append_if_absent(
            self.board.repo,
            "stop",
            time.time() - RUN_REQUEST_TTL,
            command="graceful-stop",
            **self.stamp(),
        )
        if event is None:
            return {"error": "a graceful stop is already queued for this task"}
        return {"queued": True, "request": event}

    def sessions(self):
        owner = {"name": Handler.owner, "thread_id": Handler.owner} if Handler.owner else None
        return {"owner": owner, "sessions": [owner] if owner else []}

    def mirror(self):
        state = self.board.state()
        target = ((state.get("foreman") or {}).get("title")) or "workflow foreman"
        events = [
            event
            for event in self.queue_state()["mine"]
            if event.get("kind") == "foreman"
        ]
        exchange = [
            {
                "role": "sent",
                "text": event.get("text", ""),
                "ts": datetime.datetime.fromtimestamp(
                    event.get("at", 0), datetime.timezone.utc
                ).isoformat(),
            }
            for event in events
        ]
        return {
            "title": target,
            "live": bool(Handler.owner),
            "owner": Handler.owner,
            "exchange": exchange,
            "state": (
                "the dashboard has no Codex task owner; copy the request instead"
                if not Handler.owner
                else "proposals wait for the owning Codex task"
            ),
        }

    def _active_entry(self):
        return core.active_plan(self.board.repo)

    def log(self, query):
        entry = self._active_entry()
        if entry is None or not entry["dir"]:
            return {"error": "no local active plan"}
        try:
            number = int(query.get("phase", ["0"])[0])
        except ValueError:
            return {"error": "phase is not a number"}
        kind = "repair" if query.get("kind", ["phase"])[0] == "repair" else "phase"
        tail = min(int(query.get("tail", ["400"])[0]), 5000)
        path = pathlib.Path(entry["dir"]) / "log" / f"{kind}-{number}.txt"
        if not path.is_file():
            return {"phase": number, "lines": [], "missing": str(path)}
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return {"phase": number, "path": str(path), "total": len(lines), "lines": lines[-tail:]}

    def plantext(self, query):
        state = self.board.state()
        slug = query.get("slug", [""])[0] or state.get("active")
        if not slug:
            return {"error": "no plan"}
        source = self.board.plan_source(slug)
        if source is None:
            return {"error": f"no plan for {slug}"}
        try:
            number = int(query.get("phase", ["0"])[0])
        except ValueError:
            return {"error": "phase is not a number"}
        entry = next((item for item in core.all_plans(self.board.repo) if item["slug"] == slug), None)
        payload = entry["payload"] if entry else None
        span = payload["header_span"] if payload and number == 0 else next(
            (phase["span"] for phase in (payload or {}).get("phases", []) if phase["n"] == number),
            None,
        )
        if span is None:
            return {"slug": slug, "phase": number, "lines": [], "missing": True}
        lines = source.splitlines()
        return {"slug": slug, "phase": number, "lines": lines[span[0] - 1:span[1]]}

    def roadmap(self, query):
        path = pathlib.Path(self.board.repo) / ".phased" / "roadmap.md"
        if not path.is_file():
            return {"lines": [], "missing": str(path)}
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        wanted = query.get("macro", [""])[0]
        if not wanted:
            return {"lines": lines}
        start = next(
            (
                index
                for index, line in enumerate(lines)
                if roadmap.MACRO_RE.match(line)
                and roadmap.MACRO_RE.match(line).group(1) == wanted
            ),
            None,
        )
        if start is None:
            return {"macro": wanted, "lines": [], "missing": True}
        end = next(
            (index for index in range(start + 1, len(lines)) if lines[index].startswith("## ")),
            len(lines),
        )
        return {"macro": wanted, "lines": lines[start:end]}


def registry_path(repo):
    return outbox.TMP / f"{outbox.key(repo)}-codex-server.json"


def write_registry(repo, port, token):
    path = registry_path(repo)
    outbox.private_dir(path.parent)
    descriptor = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump({"port": port, "pid": os.getpid(), "repo": repo, "token": token, "at": time.time()}, stream)
    atexit.register(drop_registry, repo, os.getpid())


def drop_registry(repo, pid):
    path = registry_path(repo)
    with contextlib.suppress(OSError, ValueError, KeyError):
        if json.loads(path.read_text(encoding="utf-8"))["pid"] == pid:
            os.remove(path)


def probe(repo, owner=None):
    path = registry_path(core.repo_root(repo))
    try:
        info = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    root = core.repo_root(repo)
    base = f"http://127.0.0.1:{info.get('port')}"
    headers = {TOKEN_HEADER: str(info.get("token", "")), "Content-Type": "application/json"}
    try:
        request = urllib.request.Request(f"{base}/api/state", headers=headers)
        with urllib.request.urlopen(request, timeout=2) as response:
            state = json.load(response)
        if os.path.realpath(state.get("repo", "")) != root:
            raise ValueError("another repository answered")
        if owner:
            request = urllib.request.Request(
                f"{base}/api/owner",
                headers=headers,
                data=json.dumps({"owner": owner}).encode(),
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=2):
                pass
        request = urllib.request.Request(
            f"{base}/api/oneshot", headers=headers, data=b"{}", method="POST"
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            one_shot = json.load(response)["k"]
    except (OSError, ValueError, KeyError):
        with contextlib.suppress(OSError):
            os.remove(path)
        return None
    return {"port": info["port"], "pid": info.get("pid"), "repo": root, "k": one_shot}


def serve(port, scan):
    last = port + PORT_SPAN if scan else port
    for candidate in range(port, last):
        try:
            return http.server.ThreadingHTTPServer(("127.0.0.1", candidate), Handler)
        except OSError:
            continue
    return http.server.ThreadingHTTPServer(("127.0.0.1", last), Handler)


def main():
    parser = argparse.ArgumentParser(description="Dashboard of a phased workflow.")
    parser.add_argument("-C", "--cwd", default=os.getcwd())
    parser.add_argument("-O", "--owner", default=None, help="Codex thread id that owns proposals")
    parser.add_argument("-P", "--port", type=int, default=None)
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    if args.probe:
        found = probe(args.cwd, args.owner)
        if found is None:
            print(f"no wfdash on {args.cwd}", flush=True)
            raise SystemExit(1)
        print(
            f"wfdash on http://127.0.0.1:{found['port']}/?k={found['k']}"
            f"  repo: {found['repo']}  reused, pid {found['pid']}",
            flush=True,
        )
        return
    Handler.board = core.Board(args.cwd)
    Handler.owner = args.owner
    Handler.token = secrets.token_urlsafe(24)
    server = serve(args.port or DEFAULT_PORT, args.port is None)
    Handler.cookie_port = server.server_address[1]
    write_registry(Handler.board.repo, Handler.cookie_port, Handler.token)
    print(
        f"wfdash on http://127.0.0.1:{Handler.cookie_port}/?k={new_one_shot()}"
        f"  repo: {Handler.board.repo}",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
