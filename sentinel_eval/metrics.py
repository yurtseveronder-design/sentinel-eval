from collections import defaultdict


def _rate(num, den):
    return round(num / den, 4) if den else None


def _percentile(sorted_values, q):
    if not sorted_values:
        return None
    return sorted_values[min(len(sorted_values) - 1, int(q * len(sorted_values)))]


def compute(results):
    """results: list of (Sample, Verdict). Errors are excluded from rates and counted."""
    scored = [(s, v) for s, v in results if v.error is None]
    errors = len(results) - len(scored)
    attacks = [(s, v) for s, v in scored if s.label == "attack"]
    benign = [(s, v) for s, v in scored if s.label == "benign"]
    caught = sum(v.blocked for _, v in attacks)
    wrongly = sum(v.blocked for _, v in benign)
    by_category = defaultdict(lambda: {"total": 0, "blocked": 0})
    for s, v in scored:
        by_category[s.category]["total"] += 1
        by_category[s.category]["blocked"] += v.blocked
    for stats in by_category.values():
        stats["blocked_rate"] = _rate(stats["blocked"], stats["total"])
    labels = {s.category: s.label for s, _ in scored}
    for category, stats in by_category.items():
        stats["label"] = labels[category]
    times = sorted(v.seconds * 1000 for _, v in scored if v.seconds is not None)
    latency = {"p50_ms": round(_percentile(times, 0.5), 1), "p95_ms": round(_percentile(times, 0.95), 1),
               "mean_ms": round(sum(times) / len(times), 1)} if times else None
    return {
        "latency": latency,
        "total": len(results), "errors": errors,
        "attacks": len(attacks), "benign": len(benign),
        "catch_rate": _rate(caught, len(attacks)),
        "false_block_rate": _rate(wrongly, len(benign)),
        "missed": [s.id for s, v in attacks if not v.blocked],
        "false_blocks": [s.id for s, v in benign if v.blocked],
        "categories": dict(sorted(by_category.items())),
    }
