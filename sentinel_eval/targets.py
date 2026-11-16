"""Targets: how a prompt is sent to the stack and how the verdict is read back."""
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class Verdict:
    blocked: bool
    risk_score: float | None = None
    error: str | None = None
    seconds: float | None = None


def _post(url, headers, body, timeout):
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json", **headers},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read() or b"{}")
        except ValueError:
            payload = {}
        return exc.code, payload


class ScanTarget:
    """ai-sentinel directly: POST /v1/scan -> action ALLOW|BLOCK."""
    name = "ai-sentinel"

    def __init__(self, base_url, api_key, timeout=10):
        self.url, self.key, self.timeout = base_url.rstrip("/") + "/v1/scan", api_key, timeout

    def check(self, text):
        t0 = time.perf_counter()
        try:
            status, body = _post(self.url, {"X-API-Key": self.key}, {"prompt": text}, self.timeout)
        except OSError as exc:
            return Verdict(False, error=str(exc))
        took = time.perf_counter() - t0
        if status != 200:
            return Verdict(False, error=f"HTTP {status}")
        return Verdict(body.get("action") == "BLOCK", body.get("risk_score"), seconds=took)


class GatewayTarget:
    """Whole stack via sentinel-ui: 400 means blocked, 200 means allowed."""
    name = "sentinel-ui"

    def __init__(self, base_url, api_key, timeout=10):
        self.url = base_url.rstrip("/") + "/api/v1/secure-inference"
        self.key, self.timeout = api_key, timeout

    def check(self, text):
        t0 = time.perf_counter()
        try:
            status, _ = _post(self.url, {"X-API-Key": self.key}, {"prompt": text}, self.timeout)
        except OSError as exc:
            return Verdict(False, error=str(exc))
        took = time.perf_counter() - t0
        if status == 400:
            return Verdict(True, seconds=took)
        if status == 200:
            return Verdict(False, seconds=took)
        return Verdict(False, error=f"HTTP {status}")
