#!/usr/bin/env python3
"""Aggregates cost and effort metrics, and recall/precision from a judged scores file.

Usage: summarize.py <label-prefix> [scores.json]
Also writes runs/<label-prefix>-metrics.json from the raw logs, and reads it when the logs are absent.
scores.json maps "<label>/<fixture>" to {"found": {key id: reported severity}, "false_positive": n, "out_of_lane": n}.
A severity matches when it equals the key's expected_severity; "handoff" keys are excluded from the severity rate.
"""
import json
import re
import statistics
import sys
from pathlib import Path

here = Path(__file__).parent
prefix = sys.argv[1]
scores = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else {}
key = json.loads((here / "answer-key.json").read_text())
required = {f["id"]: {d["id"] for d in f["defects"] if d["required"]} for f in key["fixtures"]}
expected = {d["id"]: d["expected_severity"] for f in key["fixtures"] for d in f["defects"]}


def severity_hits(found):
    graded = [k for k in found if expected.get(k, "handoff") != "handoff"]
    return sum(found[k] == expected[k] for k in graded), len(graded)

rows = []
for run_dir in sorted(p for p in (here / "runs").iterdir() if p.name.startswith(prefix)):
    for log in sorted(run_dir.glob("*.jsonl")):
        events = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
        result = next((e for e in events if e.get("type") == "result"), None)
        if result is None:
            rows.append({"run": f"{run_dir.name}/{log.stem}", "error": "no result"})
            continue
        tools = [
            c["name"]
            for e in events if e.get("type") == "assistant"
            for c in e["message"]["content"] if c.get("type") == "tool_use"
        ]
        usage = result["usage"]
        report = result.get("result", "")
        rows.append({
            "run": f"{run_dir.name}/{log.stem}",
            "fixture": log.stem,
            "cost": result["total_cost_usd"],
            "seconds": result["duration_ms"] / 1000,
            "api_seconds": result["duration_api_ms"] / 1000,
            "tool_calls": len(tools),
            "input_tokens": usage["input_tokens"] + usage["cache_creation_input_tokens"] + usage["cache_read_input_tokens"],
            "output_tokens": usage["output_tokens"],
            "findings": {s: len(re.findall(rf"^### {s}", report, re.M)) for s in "🔴🟠🟡"},
        })

# Raw logs are not committed, so a fresh checkout falls back to the metrics saved by the last local run.
metrics_file = here / "runs" / f"{prefix}-metrics.json"
if rows:
    metrics_file.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
elif metrics_file.exists():
    rows = json.loads(metrics_file.read_text())

print(f"{'run':<40} {'cost':>6} {'sec':>5} {'api':>5} {'tools':>5} {'in_tok':>7} {'out':>5}  🔴🟠🟡  recall  FP")
for r in rows:
    if "error" in r:
        print(f"{r['run']:<40} {r['error']}")
        continue
    s = scores.get(r["run"])
    need = required[r["fixture"]]
    recall = "-" if s is None or not need else f"{len(need & set(s['found']))}/{len(need)}"
    fp = "-" if s is None else str(s["false_positive"])
    f = r["findings"]
    print(f"{r['run']:<40} {r['cost']:>6.3f} {r['seconds']:>5.0f} {r['api_seconds']:>5.0f} {r['tool_calls']:>5} {r['input_tokens']:>7} {r['output_tokens']:>5}  {f['🔴']} {f['🟠']} {f['🟡']}   {recall:>5}  {fp:>2}")

ok = [r for r in rows if "error" not in r]


def spread(values):
    values = sorted(values)
    p90 = values[min(len(values) - 1, round(0.9 * (len(values) - 1)))]
    return f"mean {statistics.mean(values):>9.2f}  median {statistics.median(values):>9.2f}  p90 {p90:>9.2f}  max {values[-1]:>9.2f}  total {sum(values):>9.2f}"


if ok:
    print()
    for metric in ("cost", "seconds", "api_seconds", "tool_calls", "input_tokens", "output_tokens"):
        print(f"{metric:<14} {spread([r[metric] for r in ok])}")

    print()
    print(f"{'fixture':<26} {'runs':>4} {'cost':>6} {'med_sec':>7} {'recall':>7} {'FP':>4} {'sev_ok':>7}")
    for fixture in dict.fromkeys(r["fixture"] for r in ok):
        group = [r for r in ok if r["fixture"] == fixture]
        judged = [scores[r["run"]] for r in group if r["run"] in scores]
        need = required[fixture]
        recall = "-"
        if judged and need:
            recall = f"{sum(len(need & set(j['found'])) for j in judged) / (len(need) * len(judged)):.0%}"
        fp = str(sum(j["false_positive"] for j in judged)) if judged else "-"
        hits = [severity_hits(j["found"]) for j in judged]
        sev = f"{sum(h for h, _ in hits)}/{sum(n for _, n in hits)}" if any(n for _, n in hits) else "-"
        print(f"{fixture:<26} {len(group):>4} {statistics.mean(r['cost'] for r in group):>6.3f} "
              f"{statistics.median(r['seconds'] for r in group):>7.1f} {recall:>7} {fp:>4} {sev:>7}")

    judged_all = [scores[r["run"]] for r in ok if r["run"] in scores]
    if judged_all:
        need_total = sum(len(required[r["fixture"]]) for r in ok if r["run"] in scores)
        found_total = sum(len(required[r["fixture"]] & set(scores[r["run"]]["found"])) for r in ok if r["run"] in scores)
        hits = [severity_hits(j["found"]) for j in judged_all]
        print()
        print(f"TOTAL recall {found_total}/{need_total}  false positives {sum(j['false_positive'] for j in judged_all)}"
              f"  out-of-lane {sum(j['out_of_lane'] for j in judged_all)}"
              f"  severity match {sum(h for h, _ in hits)}/{sum(n for _, n in hits)}")
