import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from sentinel_eval import cli, dataset, metrics, report, targets


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.headers.get("X-API-Key") != "k":
            return self._send(401, {"detail": "bad key"})
        blocked = "ignore" in body["prompt"].lower()
        if self.path == "/v1/scan":
            return self._send(200, {"action": "BLOCK" if blocked else "ALLOW", "risk_score": 0.9 if blocked else 0.0})
        return self._send(400 if blocked else 200, {})

    def _send(self, code, payload):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture()
def server():
    s = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_port}"
    s.shutdown()


def test_dataset_is_valid_and_balanced():
    samples = dataset.load()
    labels = {s.label for s in samples}
    assert labels == {"attack", "benign"}
    assert sum(s.label == "attack" for s in samples) >= 40
    assert sum(s.label == "benign" for s in samples) >= 40


def test_dataset_rejects_bad_label(tmp_path):
    f = tmp_path / "d.jsonl"
    f.write_text('{"id":"a","label":"nope","category":"c","text":"t"}\n')
    with pytest.raises(ValueError):
        dataset.load(f)


@pytest.mark.parametrize("cls,key", [(targets.ScanTarget, "k"), (targets.GatewayTarget, "k")])
def test_targets_read_verdicts(server, cls, key):
    t = cls(server, key)
    assert t.check("please ignore this").blocked is True
    assert t.check("hello").blocked is False


def test_target_reports_auth_error(server):
    v = targets.ScanTarget(server, "wrong").check("hello")
    assert v.error and not v.blocked


def test_unreachable_target_is_an_error():
    assert targets.ScanTarget("http://127.0.0.1:1", "k", timeout=1).check("x").error


def test_metrics_rates_and_errors():
    S = dataset.Sample
    results = [
        (S("1", "attack", "a", "x"), targets.Verdict(True)),
        (S("2", "attack", "a", "x"), targets.Verdict(False)),
        (S("3", "benign", "b", "x"), targets.Verdict(True)),
        (S("4", "benign", "b", "x"), targets.Verdict(False)),
        (S("5", "benign", "b", "x"), targets.Verdict(False, error="boom")),
    ]
    m = metrics.compute(results)
    assert (m["catch_rate"], m["false_block_rate"], m["errors"]) == (0.5, 0.5, 1)
    assert m["missed"] == ["2"] and m["false_blocks"] == ["3"]
    assert "50.0%" in report.markdown("t", m)


def test_cli_passes_then_detects_regression(server, tmp_path):
    base = tmp_path / "baseline.json"
    args = ["--url", server, "--api-key", "k", "--out", str(tmp_path / "r")]
    assert cli.main(args + ["--write-baseline", str(base)]) == 0
    base.write_text(json.dumps({"catch_rate": 1.0, "false_block_rate": 0.0}))
    # stub only blocks prompts containing "ignore", so catch rate < 1.0 -> regression
    assert cli.main(args + ["--baseline", str(base)]) == 1


def test_cli_fails_on_unreachable(tmp_path):
    assert cli.main(["--url", "http://127.0.0.1:1", "--out", str(tmp_path)]) == 1
