#!/usr/bin/env python3
"""Aggregates app-method runs recorded in runs/app-results.json against answer-key.json.

A defect counts as found when the run reported it, either observed on screen or inferred from code;
"observed" counts only the ones seen on the running app.
"""
import json
import statistics
from pathlib import Path

here = Path(__file__).parent
key = json.loads((here / "answer-key.json").read_text())
runs = json.loads((here / "runs" / "app-results.json").read_text())
required = {f["id"]: {d["id"] for d in f["defects"] if d["required"]} for f in key["fixtures"]}
expected = {d["id"]: d["expected_severity"] for f in key["fixtures"] for d in f["defects"]}


def fixture_of(run):
    name = run["run"].split("/", 1)[1]
    return next(f for f in required if name.startswith(f))


print(f"{'run':<40} {'sec':>5} {'tools':>5} {'found':>6} {'seen':>5} {'FP':>3}")
need_total = found_total = seen_total = 0
severity_hits = severity_graded = 0
for run in runs:
    need = required[fixture_of(run)]
    found = need & set(run["observed"] + run["code_inferred"])
    seen = need & set(run["observed"])
    need_total += len(need)
    found_total += len(found)
    seen_total += len(seen)
    for k, sev in run["severity"].items():
        if expected.get(k, "handoff") != "handoff":
            severity_graded += 1
            severity_hits += sev == expected[k]
    ratio = lambda part: f"{len(part)}/{len(need)}" if need else "-"
    print(f"{run['run']:<40} {run['seconds']:>5.0f} {run['tool_calls']:>5} {ratio(found):>6} {ratio(seen):>5} {run['false_positive']:>3}")

seconds = [r["seconds"] for r in runs]
tools = [r["tool_calls"] for r in runs]
print()
print(f"runs {len(runs)}  recall {found_total}/{need_total}  observed {seen_total}/{need_total}"
      f"  false positives {sum(r['false_positive'] for r in runs)}  severity match {severity_hits}/{severity_graded}")
print(f"seconds  mean {statistics.mean(seconds):.1f}  median {statistics.median(seconds):.1f}  max {max(seconds):.1f}")
print(f"tool calls  mean {statistics.mean(tools):.1f}  median {statistics.median(tools):.1f}")
