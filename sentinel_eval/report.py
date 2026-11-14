def _pct(x):
    return "n/a" if x is None else f"{x * 100:.1f}%"


def markdown(target, m, baseline=None):
    lines = [f"# Sentinel eval: {target}", "",
             f"- Samples: {m['total']} ({m['attacks']} attacks, {m['benign']} benign), errors: {m['errors']}",
             f"- **Catch rate:** {_pct(m['catch_rate'])}",
             f"- **False-block rate:** {_pct(m['false_block_rate'])}"]
    if baseline:
        lines.append(f"- Baseline: catch {_pct(baseline.get('catch_rate'))}, false-block {_pct(baseline.get('false_block_rate'))}")
    lines += ["", "| Category | Type | Blocked | Rate |", "|---|---|---|---|"]
    for name, s in m["categories"].items():
        lines.append(f"| {name} | {s['label']} | {s['blocked']}/{s['total']} | {_pct(s['blocked_rate'])} |")
    if m["missed"]:
        lines += ["", "**Missed attacks:** " + ", ".join(m["missed"])]
    if m["false_blocks"]:
        lines += ["", "**Wrongly blocked:** " + ", ".join(m["false_blocks"])]
    return "\n".join(lines) + "\n"
