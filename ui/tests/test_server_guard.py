"""Request guards on the launcher: Host check (DNS rebinding) and POST origin/type checks (CSRF).

Starts a throwaway server on an ephemeral loopback port inside the test process. No request
here reaches Docker: allowed POSTs use an unknown action (rejected by the whitelist) or
/api/stop with no job running.
"""
from __future__ import annotations

import http.client
import importlib.util
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "redkeep_ui_server", Path(__file__).resolve().parents[1] / "server.py")
assert _spec and _spec.loader
server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server)


@pytest.fixture(scope="module")
def port():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield httpd.server_address[1]
    httpd.shutdown()
    httpd.server_close()


def _req(port, method, path, headers=None, body=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    h = {"Host": f"127.0.0.1:{port}"}
    h.update(headers or {})
    c.request(method, path, body=body, headers=h)
    r = c.getresponse()
    data = r.read()
    c.close()
    return r.status, (json.loads(data) if data[:1] in (b"{", b"[") else data)


JSON = {"Content-Type": "application/json"}
BAD_ACTION = json.dumps({"action": "not-a-real-action"})


def test_get_with_local_host_is_served(port):
    status, body = _req(port, "GET", "/api/job")
    assert status == 200 and body["status"] in {"idle", "running", "done"}


@pytest.mark.parametrize("host", ["evil.example", "evil.example:{port}", "127.0.0.1:1", ""])
def test_get_with_foreign_host_is_refused(port, host):
    status, _ = _req(port, "GET", "/api/job", {"Host": host.format(port=port)})
    assert status == 403


def test_localhost_name_is_accepted(port):
    status, _ = _req(port, "GET", "/api/job", {"Host": f"localhost:{port}"})
    assert status == 200


def test_post_without_json_type_is_refused(port):
    # What a cross-site form or no-cors fetch can send without a preflight.
    status, body = _req(port, "POST", "/api/exec", {"Content-Type": "text/plain"}, BAD_ACTION)
    assert status == 403 and "Content-Type" in body["error"]


def test_post_from_foreign_origin_is_refused(port):
    status, body = _req(port, "POST", "/api/exec",
                        {**JSON, "Origin": "http://evil.example"}, BAD_ACTION)
    assert status == 403 and "cross-origin" in body["error"]


def test_post_from_other_local_port_is_refused(port):
    status, _ = _req(port, "POST", "/api/exec",
                     {**JSON, "Origin": "http://127.0.0.1:3000"}, BAD_ACTION)
    assert status == 403


@pytest.mark.parametrize("site", ["cross-site", "same-site"])
def test_post_marked_cross_site_is_refused(port, site):
    status, _ = _req(port, "POST", "/api/exec", {**JSON, "Sec-Fetch-Site": site}, BAD_ACTION)
    assert status == 403


def test_post_from_own_page_passes_the_guard(port):
    # Same origin + JSON reaches the whitelist, which rejects the unknown action (400, not 403).
    headers = {**JSON, "Origin": f"http://127.0.0.1:{port}", "Sec-Fetch-Site": "same-origin"}
    status, body = _req(port, "POST", "/api/exec", headers, BAD_ACTION)
    assert status == 400 and "unknown action" in body["error"]


def test_post_from_local_script_passes_the_guard(port):
    # No Origin / Sec-Fetch-Site, as curl or a local script would send.
    status, body = _req(port, "POST", "/api/stop", JSON, "{}")
    assert status == 200 and body["ok"] is False


def test_oversized_body_is_refused(port):
    status, _ = _req(port, "POST", "/api/exec", JSON, "x" * (server.MAX_BODY + 1))
    assert status == 413
