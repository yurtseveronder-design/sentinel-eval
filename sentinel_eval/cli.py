import argparse
import json
import os
import sys
from pathlib import Path

from . import dataset, metrics, report, targets


def run(samples, target):
    return [(s, target.check(s.text)) for s in samples]


def regression(m, baseline, tolerance):
    problems = []
    if m["catch_rate"] is not None and baseline.get("catch_rate") is not None \
            and m["catch_rate"] < baseline["catch_rate"] - tolerance:
        problems.append(f"catch rate fell: {m['catch_rate']} < baseline {baseline['catch_rate']}")
    if m["false_block_rate"] is not None and baseline.get("false_block_rate") is not None \
            and m["false_block_rate"] > baseline["false_block_rate"] + tolerance:
        problems.append(f"false-block rate rose: {m['false_block_rate']} > baseline {baseline['false_block_rate']}")
    return problems


def main(argv=None):
    p = argparse.ArgumentParser(prog="sentinel-eval")
    p.add_argument("--target", choices=["scan", "gateway"], default="scan")
    p.add_argument("--url", help="default: SENTINEL_URL (scan) or UI_URL (gateway)")
    p.add_argument("--api-key", help="default: SENTINEL_API_KEY / UI_API_KEY")
    p.add_argument("--dataset", default=str(dataset.DEFAULT_DATASET))
    p.add_argument("--out", default="reports", help="directory for report.json / report.md")
    p.add_argument("--baseline", help="baseline.json to compare against")
    p.add_argument("--tolerance", type=float, default=0.02)
    p.add_argument("--write-baseline", help="write current metrics to this file")
    p.add_argument("--max-errors", type=int, default=0)
    args = p.parse_args(argv)

    if args.target == "scan":
        url = args.url or os.getenv("SENTINEL_URL", "http://127.0.0.1:8000")
        key = args.api_key or os.getenv("SENTINEL_API_KEY", "test-api-key")
        target = targets.ScanTarget(url, key)
    else:
        url = args.url or os.getenv("UI_URL", "http://127.0.0.1:8200")
        key = args.api_key or os.getenv("UI_API_KEY", "ui-test-key")
        target = targets.GatewayTarget(url, key)

    m = metrics.compute(run(dataset.load(args.dataset), target))
    baseline = json.loads(Path(args.baseline).read_text()) if args.baseline and Path(args.baseline).exists() else None
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{target.name}.json").write_text(json.dumps(m, indent=2))
    text = report.markdown(f"{target.name} / {Path(args.dataset).stem}", m, baseline)
    (out / f"{target.name}.md").write_text(text)
    print(text)
    if args.write_baseline:
        Path(args.write_baseline).write_text(json.dumps(
            {k: m[k] for k in ("catch_rate", "false_block_rate")}, indent=2) + "\n")

    failed = []
    if m["errors"] > args.max_errors:
        failed.append(f"{m['errors']} requests failed (service unreachable or auth error)")
    if baseline:
        failed += regression(m, baseline, args.tolerance)
    for line in failed:
        print("FAIL:", line, file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
