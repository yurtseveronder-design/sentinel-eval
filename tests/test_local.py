import json
from pathlib import Path

import pytest

from sentinel_eval import dataset, local
from sentinel_eval.targets import Verdict

ROOT = Path(__file__).resolve().parent.parent
LATEST = json.loads((ROOT / "results" / "latest.json").read_text(encoding="utf-8"))


def test_compare_flags_only_real_regressions():
    ref = {"blind": {"catch_rate": 0.5, "false_block_rate": 0.04}}
    assert local.compare({"blind": {"catch_rate": 0.49, "false_block_rate": 0.05}}, ref, 0.02) == []
    problems = local.compare({"blind": {"catch_rate": 0.4, "false_block_rate": 0.1}}, ref, 0.02)
    assert len(problems) == 2 and "catch rate fell" in problems[0] and "false-block rate rose" in problems[1]


def test_known_gaps_are_strict():
    gaps = [{"id": "a", "text": "attack", "expect": "miss"}, {"id": "b", "text": "harmless", "expect": "false_block"}]
    still = local.check_known_gaps(lambda t: Verdict(blocked=(t == "harmless")), gaps)
    assert still == {"still_failing": ["a", "b"], "fixed": []}
    fixed = local.check_known_gaps(lambda t: Verdict(blocked=(t == "attack")), gaps)
    assert fixed == {"still_failing": [], "fixed": ["a", "b"]}


def test_latest_json_is_consistent():
    assert LATEST["schema_version"] == 1
    ids = [c["id"] for c in LATEST["configurations"]]
    assert "default" in ids and len(ids) == len(set(ids))
    for config in LATEST["configurations"]:
        assert set(config["sets"]) == {"dev", "heldout", "blind"}
        for stats in config["sets"].values():
            assert 0 <= stats["catch_rate"] <= 1 and 0 <= stats["false_block_rate"] <= 1
    for run in LATEST["sealed_runs"]:
        assert run["attacks"] == LATEST["sets"]["sealed"]["attacks"]
    counts = {n: (len([s for s in dataset.load(p) if s.label == "attack"]), len([s for s in dataset.load(p) if s.label == "benign"])) for n, p in local.SETS.items()}
    for config in LATEST["configurations"]:
        for name, stats in config["sets"].items():
            assert (stats["attacks"], stats["benign"]) == counts[name]


def test_known_gaps_file_points_at_real_samples():
    by_id = {s.id: s for path in local.SETS.values() for s in dataset.load(path)}
    gaps = [json.loads(line) for line in (ROOT / "data" / "known_gaps.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert gaps
    for gap in gaps:
        sample = by_id[gap["id"]]
        assert sample.text == gap["text"]
        assert (sample.label == "attack") == (gap["expect"] == "miss")


@pytest.fixture
def fake_stack(monkeypatch):
    def install(blocked_ids_text):
        monkeypatch.setattr(local, "build_target", lambda classifier=None: (lambda text: Verdict(blocked=text in blocked_ids_text, seconds=0.001)))
    return install


def test_cli_exit_codes(fake_stack, capsys):
    every_attack = {s.text for p in local.SETS.values() for s in dataset.load(p) if s.label == "attack"}
    fake_stack(every_attack)                                           # blocks every attack: better than the reference
    assert local.main(["--compare", str(ROOT / "results" / "latest.json")]) == 0
    fake_stack(set())                                                  # blocks nothing: catch rate collapses
    assert local.main(["--compare", str(ROOT / "results" / "latest.json")]) == 1
    fake_stack(every_attack)                                           # fixes every known gap: list is stale
    assert local.main(["--known-gaps", str(ROOT / "data" / "known_gaps.jsonl")]) == 1
    out = json.loads(capsys.readouterr().out.split("\n}\n")[-2] + "\n}")
    assert out["known_gaps"]["fixed"]
