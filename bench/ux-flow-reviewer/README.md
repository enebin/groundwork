# Code-based UX review benchmark

This benchmark measures `ux-flow-reviewer`, the reviewer that judges usability from the code without launching the app. It answers two questions:

1. Did a prompt change make the reviewer better or worse?
2. How does reviewing from the code compare with reviewing on the running app (`ux-persona-reviewer`)?

All runs below used Sonnet. Results were judged by hand against `answer-key.json`.

## Results

### Prompt versions (code method, 11 fixtures × 3 runs each)

| | baseline | v1 | v2 (current) |
|---|---|---|---|
| Seeded defects found | 36/39 | 36/39 | 36/39 |
| False positives | 1 | 0 | **0** |
| Findings in another reviewer's lane | 6 | 6 | **0** |
| Severity matches the rubric | 28/39 | 32/39 | **35/39** |
| Mean cost per run | $0.17 | $0.17 | $0.17 |
| Mean / p90 time per run | 20.2 s / 28.1 s | 20.9 s / 29.3 s | 21.3 s / 32.2 s |

- **v1** added a UX severity rubric, a **Pre-existing** section for problems the base already had, and **Rendered-check handoffs** for risks only the running app can confirm.
- **v2** split UX from code-quality (a bug that leaves the screen wrong is not a UX finding) and from writing (a vague label is not a UX finding), limited handoffs to UI the diff touched, and named "a primary action disabled with no visible reason" as 🟠.
- The 3 missed defects are one regression in `hc-big-refactor`, missed in every run of every version (see below).
- The rubric and the expected severities were written together, so "severity matches" measures how closely the reviewer follows the rubric, not an independent ground truth.

### Code method vs. app method

The app method ran `ux-persona-reviewer` once per affected persona, twice per fixture, on iPhone 16 simulators (iOS 18.4) driven by Claude Code's iOS Simulator tools. Each reviewer built the app itself, starting with no data.

| | Code method (v2) | App method |
|---|---|---|
| Runs | 33 | 24 |
| Seeded defects reported | 36/39 (92%) | 32/32 (100%) |
| …of which seen on the running app | — | 27/32 |
| False positives | 0 | 4 |
| Severity matches the rubric | 35/39 | 22/33 |
| Mean time per run | 21 s | 126 s (max 209 s) |
| Mean tool calls per run | 4.5 | 36.6 |
| Cost per run | $0.17 (measured) | not reported by the subagent tool |

Which method caught each defect, counting runs that reported it:

| Defect | Code (v2) | App: seen on screen | App: from code only |
|---|---|---|---|
| f1: adding water needs a hidden long press | 3/3 | 2/2 | |
| f1: progress shown by color only | 3/3 | 2/2 | |
| f1: no accessibility label or action | 3/3 | | 2/2 |
| f2: clear deletes the day with no confirmation or undo | 3/3 | 2/2 | |
| f3: empty-state hint removed | 3/3 | 2/2 | |
| f3: failed load looks like an empty day | 3/3 | 2/2 | |
| f4: confirmation dialog on every add | 3/3 | 2/2 | |
| h1: new goal not shown until relaunch | 3/3 | 4/4 | |
| h1: Continue disabled with no reason | 3/3 | 3/4 | 1/4 |
| h2: failed save is silent | 3/3 | | 2/2 |
| h2: invalid amount silently ignored | 3/3 | 2/2 | |
| h3: editing only through a hidden swipe | 3/3 | 2/2 | |
| hc: "2,000 of 2000 ml" number format regression | **0/3** | **4/4** | |
| c2: buttons break at large text sizes | 3/3 as a handoff | 2/2, confirmed | |

What this shows:

- **The code method is about 6× faster and finds failure paths.** It reported the silent save failure in every run. The app method could not trigger that failure from the UI and fell back to reading the code.
- **The app method confirms what the code method can only suspect, and catches what reading misses.** It confirmed the large-text breakage the code method handed off, observed that the 250 ml long press never fires because the context menu takes the press, and found the number-format regression in a refactor that every code run judged UI-identical (SwiftUI groups an `Int` interpolated into a `Text` literal, but not a pre-built `String`).
- **The app method misattributes pre-existing problems.** All 4 of its false positives came from `h3`, where it blamed the change for stale totals and a no-undo delete that the base version already had. With no base build to compare, it inferred the cause from the diff. The code method, which compares against the base version, classified the same problems as pre-existing in 3/3 runs.
- **A practical split:** run the code method on every change, and run the app method only on its **Rendered-check handoffs** and on refactors of display code.

Caveats: one app, one platform, and hand-judged scoring. The app method ran up to 3 simulators at once, which slows builds. In one run, a reviewer that omitted the simulator ID sent a tap to another reviewer's device; the prompt now requires the ID on every call.

## Fixtures

`fixtures.bundle` holds a small SwiftUI water-tracking app as git branches. Each fixture is one commit on top of a base.

| Fixture | Base | Change | Seeded defects |
|---|---|---|---|
| `f1-quick-add-ring` | easy | Quick-add buttons replaced by a progress ring | 3 |
| `f2-clear-today` | easy | "Clear" deletes the whole day | 1 |
| `f3-list-refactor` | easy | List simplified; empty and error states dropped | 2 (+1 optional) |
| `f4-add-confirm` | easy | Confirmation before every add | 1 |
| `c1-row-extract` | easy | Row view extracted; no UX change | 0 |
| `c2-750-button` | easy | Third quick-add button | 0 (+1 rendered risk) |
| `h1-goal-setting` | hard | Goal set at first launch and in Settings | 2 |
| `h2-custom-amount` | hard | Custom amount sheet | 2 |
| `h3-history-edit` | hard | Load history once; edit by swipe only | 1 (+1 pre-existing trap) |
| `h4-settings-cleanup` | hard | Settings copy tidy-up | 0 (+1 pre-existing trap) |
| `hc-big-refactor` | hard | Shared formatting, rows, and sorting | 1 (found by the app method) |

The easy base is one screen with one persona. The hard base has three tabs and two personas. `answer-key.json` lists every defect with its expected severity, plus the traps a careful reviewer should not report.

The answer key was wrong three times while building this benchmark. The reviewers caught two of those mistakes and the app method caught the third, so treat the key as fallible.

## Running it

Requirements: Claude Code, `jq`, and Xcode with an iOS 18.4 simulator.

Code method, headless:

```bash
for f in $(jq -r '.fixtures[].id' answer-key.json); do ./run.sh "$f" mytest-r1 & done; wait
python3 summarize.py mytest runs/mytest-scores.json
```

- `run.sh` uses this checkout's `agents/ux-flow-reviewer.md` as the system prompt, so it measures local edits. Set `AGENT_FILE=agents/v2.md` (or another snapshot) to measure a fixed version.
- Fixtures are cloned from `fixtures.bundle` on first use. Worktrees go to `~/.cache/groundwork-bench/ux-flow` (outside this repository, so its `CLAUDE.md` does not reach the reviewer).
- Scoring is manual: write `runs/<label>-scores.json` from the reports (see the existing files for the shape). Without scores, `summarize.py` still prints cost, time, and tool calls.

App method, from a Claude Code session with the iOS Simulator tools:

```bash
./app-prompt.sh h2-custom-amount "Daily water logger" <simulator-udid> mytest-app-r1
```

Dispatch `groundwork:ux-persona-reviewer` with the printed prompt, record each result in `runs/app-results.json`, then run `python3 summarize_app.py`. Uninstall the app on the simulator between runs.

## Files

| Path | Purpose |
|---|---|
| `run.sh`, `summarize.py` | Code-method runner and summary |
| `app-prompt.sh`, `summarize_app.py` | App-method assignment and summary |
| `answer-key.json` | Fixtures, seeded defects, expected severities, traps |
| `fixtures.bundle` | Fixture app as git branches |
| `agents/` | Prompt snapshots: `baseline.md`, `v1.md`, `v2.md` |
| `runs/*-scores.json`, `runs/*-metrics.json`, `runs/app-results.json` | Judged scores and per-run metrics |

Raw stream logs and screenshots stay local (`.gitignore`), because the logs contain the local session's tool and plugin inventory.
