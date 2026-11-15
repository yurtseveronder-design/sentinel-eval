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


def html(target, m, baseline=None):
    """Self-contained HTML dashboard (no external assets, no JavaScript)."""
    from html import escape

    def bar(rate, good_high):
        if rate is None:
            return "<em>n/a</em>"
        w = round(rate * 100, 1)
        colour = "#2e7d32" if good_high else "#c62828"
        return (f'<div class="bar"><div style="width:{w}%;background:{colour}"></div></div>'
                f'<span>{w}%</span>')

    rows = "".join(
        f"<tr><td>{escape(n)}</td><td>{escape(s['label'])}</td><td>{s['blocked']}/{s['total']}</td>"
        f"<td>{bar(s['blocked_rate'], s['label'] == 'attack')}</td></tr>"
        for n, s in m["categories"].items())
    base = ""
    if baseline:
        base = (f"<p class=muted>Baseline: catch {_pct(baseline.get('catch_rate'))}, "
                f"false-block {_pct(baseline.get('false_block_rate'))}</p>")
    missed = ("<h2>Missed attacks</h2><p>" + ", ".join(map(escape, m["missed"])) + "</p>") if m["missed"] else ""
    fps = ("<h2>Wrongly blocked</h2><p>" + ", ".join(map(escape, m["false_blocks"])) + "</p>") if m["false_blocks"] else ""
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>Sentinel eval: {escape(target)}</title>
<style>body{{font:15px system-ui;max-width:880px;margin:2rem auto;padding:0 1rem;color:#1b1b1b}}
.cards{{display:flex;gap:1rem;flex-wrap:wrap}}.card{{flex:1;min-width:180px;border:1px solid #ddd;border-radius:8px;padding:1rem}}
.card b{{display:block;font-size:2rem}}table{{width:100%;border-collapse:collapse;margin-top:1rem}}
td,th{{text-align:left;padding:.4rem;border-bottom:1px solid #eee}}.bar{{display:inline-block;width:60%;height:10px;background:#eee;margin-right:.5rem}}
.bar div{{height:10px}}.muted{{color:#666}}</style>
<h1>Sentinel eval: {escape(target)}</h1>
<div class="cards">
<div class="card"><b>{_pct(m['catch_rate'])}</b>attacks caught</div>
<div class="card"><b>{_pct(m['false_block_rate'])}</b>benign wrongly blocked</div>
<div class="card"><b>{m['total']}</b>samples ({m['attacks']} attacks, {m['benign']} benign, {m['errors']} errors)</div></div>
{base}<table><tr><th>Category</th><th>Type</th><th>Blocked</th><th>Rate</th></tr>{rows}</table>{missed}{fps}</html>
"""
