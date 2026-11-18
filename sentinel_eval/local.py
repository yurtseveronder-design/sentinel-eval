"""Re-evaluate the stack in-process, with machine-readable output. Built so an AI agent (or a script) can
change a rule or swap a model and get one JSON answer, no running server needed.

    sentinel-eval-local                                   # default stack on dev, held-out, blind -> JSON
    sentinel-eval-local --classifier protectai/deberta-v3-base-prompt-injection-v2
    sentinel-eval-local --sealed /private/sealed.jsonl    # adds the sealed set (aggregate numbers only)
    sentinel-eval-local --compare results/latest.json --config default     # exit 1 on regression
    sentinel-eval-local --known-gaps data/known_gaps.jsonl                 # exit 1 if a known gap was fixed (update the list)

Needs ai-sentinel and sentinel-semantic installed (the classifier also needs the sentinel-semantic [classifier] extra).
Exit codes: 0 ok, 1 regression or stale known-gap list, 2 usage/setup error.
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from . import dataset, metrics
from .targets import Verdict

DATA = Path(__file__).resolve().parent.parent / "data"
SETS = {"dev": DATA / "prompts.jsonl", "heldout": DATA / "heldout.jsonl", "blind": DATA / "blind.jsonl"}


def build_target(classifier=None):
    """The in-process stack: rule shield, then the semantic router; either layer can block."""
    from ai_sentinel.core.shield import SecurityShield
    from sentinel_semantic.router import SemanticRouter

    if classifier:
        os.environ["SEMANTIC_CLASSIFIER_MODEL"] = classifier
    else:
        os.environ.pop("SEMANTIC_CLASSIFIER_MODEL", None)
    shield, router = SecurityShield(block_threshold=0.7), SemanticRouter(engine="keyword")

    def check(text):
        started = time.perf_counter()
        verdict = shield.inspect(prompt=text)
        route = router.route(text)
        blocked = verdict.action == "BLOCK" or route.guardrail_profile == "maximum_security_block"
        return Verdict(blocked=blocked, risk_score=float(verdict.risk_score), seconds=time.perf_counter() - started)

    return check


def score(check, samples):
    m = metrics.compute([(s, check(s.text)) for s in samples])
    return {"attacks": m["attacks"], "benign": m["benign"], "catch_rate": m["catch_rate"],
            "false_block_rate": m["false_block_rate"], "latency_ms": m["latency"], "missed": m["missed"]}


def compare(measured, reference, tolerance):
    """Both are {set: {catch_rate, false_block_rate}}. Returns a list of regression messages."""
    problems = []
    for name, ref in reference.items():
        now = measured.get(name)
        if now is None:
            continue
        if now["catch_rate"] is not None and ref.get("catch_rate") is not None and now["catch_rate"] < ref["catch_rate"] - tolerance:
            problems.append(f"{name}: catch rate fell {ref['catch_rate']} -> {now['catch_rate']}")
        if now["false_block_rate"] is not None and ref.get("false_block_rate") is not None and now["false_block_rate"] > ref["false_block_rate"] + tolerance:
            problems.append(f"{name}: false-block rate rose {ref['false_block_rate']} -> {now['false_block_rate']}")
    return problems


def check_known_gaps(check, gaps):
    """Each gap is {id, text, expect: 'miss' | 'false_block'}. A gap that no longer fails is 'fixed' (strict, like xfail)."""
    fixed, still = [], []
    for gap in gaps:
        blocked = check(gap["text"]).blocked
        failing = (not blocked) if gap["expect"] == "miss" else blocked
        (still if failing else fixed).append(gap["id"])
    return {"still_failing": still, "fixed": fixed}


def main(argv=None):
    p = argparse.ArgumentParser(prog="sentinel-eval-local", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--classifier", help="Hugging Face model id to enable as the semantic classifier")
    p.add_argument("--sealed", help="path to the private sealed set; only aggregate numbers are printed")
    p.add_argument("--compare", help="results/latest.json to compare against")
    p.add_argument("--config", default="default", help="configuration id inside --compare (default: default)")
    p.add_argument("--tolerance", type=float, default=0.02)
    p.add_argument("--known-gaps", help="data/known_gaps.jsonl")
    p.add_argument("--out", help="also write the JSON here")
    args = p.parse_args(argv)

    try:
        check = build_target(args.classifier)
    except ImportError as exc:
        print(f"error: {exc}. Install ai-sentinel and sentinel-semantic first.", file=sys.stderr)
        return 2

    sets = {name: score(check, dataset.load(path)) for name, path in SETS.items()}
    if args.sealed:
        raw = Path(args.sealed).read_bytes()
        sealed = score(check, dataset.load(args.sealed))
        sealed.pop("missed")                      # never reveal which sealed prompts were missed
        sealed["sha256"] = hashlib.sha256(raw).hexdigest()
        sets["sealed"] = sealed
    report = {"configuration": args.classifier or "default", "sets": sets}

    exit_code = 0
    if args.compare:
        data = json.loads(Path(args.compare).read_text(encoding="utf-8"))
        configs = {c["id"]: c for c in data["configurations"]}
        if args.config not in configs:
            print(f"error: configuration '{args.config}' not in {args.compare}", file=sys.stderr)
            return 2
        report["regressions"] = compare(sets, configs[args.config]["sets"], args.tolerance)
        exit_code = 1 if report["regressions"] else 0
    if args.known_gaps:
        gaps = [json.loads(line) for line in Path(args.known_gaps).read_text(encoding="utf-8").splitlines() if line.strip()]
        report["known_gaps"] = check_known_gaps(check, gaps)
        if report["known_gaps"]["fixed"]:
            exit_code = 1
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
