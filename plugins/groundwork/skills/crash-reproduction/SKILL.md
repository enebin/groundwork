---
name: crash-reproduction
description: Reconstruct the environment of a reported software crash, analyze the actual failing point, and attempt a faithful reproduction. Use when a crash log, stack trace, incident report, or suspected timing-related crash needs investigation; do not use for ordinary non-crashing bugs.
---

# Crash Reproduction

Find a realistic path from a user action to the reported crash. Keep facts, hypotheses, and experimental changes separate. A reproduction is valid only when it reaches the same failure through actions and states the product can naturally encounter.

Read `reference/config.md` under the plugin root (two directories above this skill), the repository's `GROUNDWORK.md`, and its rules. Talk in `language.conversation`; write saved files in `language.artifacts`. This skill investigates and reports; it does not fix the crash. When the user wants a fix afterward, hand the report to `step`.

## 1. Match the reported environment

Collect the available crash log, incident context, source revision, and build artifacts. Reconstruct as much of the following as the evidence supports:

- app and SDK versions, commit or release revision, build configuration, and compiler/toolchain
- device or hardware model, OS version, architecture, and locale when relevant
- dependency versions, feature flags, server/environment, account state, persisted data, and permissions
- the user action sequence, navigation state, foreground/background state, network conditions, and relevant timing

Symbolicate the crash before drawing source-level conclusions. Verify that binary UUIDs match the dSYM or equivalent symbols. If symbols, the exact revision, or another important input is missing, label the gap explicitly. Do not silently substitute the current environment and call it equivalent.

A latent crash found by reading code has no log to symbolicate. Mark the crash log `MISSING`, and target the oldest supported OS and the shipped revision that contains the suspect code.

Prefer an isolated branch, worktree, simulator, or disposable test state when changing revisions or configuration. Do not overwrite the user's current work. Never expose secrets from logs or configuration in the report.

End this stage with a short environment table or list using these labels:

- `MATCHED`: supported by an artifact or direct observation
- `ASSUMED`: plausible but not verified
- `MISSING`: required evidence is unavailable
- `DIFFERENT`: the available test environment cannot match the report

## 2. Analyze the crash point

Start from the exception or signal, the crashed thread, and its fully symbolicated frames. Locate the first frame owned by the product, then trace the execution path and state transitions that lead to it. Inspect nearby lifecycle, concurrency, ownership, collection indexing, and callback behavior only when the evidence points there.

For each hypothesis, record:

- the evidence from the crash log and source
- the required preconditions
- the user-visible action sequence that could create those preconditions
- an observation that would confirm it
- an observation that would disprove it

Rank hypotheses by evidence. Do not present a guessed root cause as fact. Distinguish the crash site, where the process stopped, from the root cause, which may have occurred earlier.

### Name the exact subject

Use the concrete names shown by source code and artifacts whenever they are available:

- Name the exact type, property or variable, function, file and line, thread or queue, and event involved in the failure.
- When multiple instances share a type, identify the instance by its owner and role, such as `ConversationViewModel.messageTask` rather than "the task."
- State the observed ownership or lifecycle relationship instead of saying only that an object was "internal" or "already gone."
- Do not use invented placeholders such as "object X," `SomeType`, "some manager," "an internal object," or "a component" in the final explanation.
- If an exact name cannot be recovered, do not invent one. State what is unknown and why, then identify the strongest available evidence, such as an unsymbolicated frame number, memory address, binary image, or source expression.

For example, prefer "`ConversationViewModel.messageTask` completed after `ConversationViewController.deinit` and its closure accessed the released controller" over "an internal object accessed object X after it was released."

## 3. Attempt a faithful reproduction

First try the reported environment and natural user flow without diagnostic behavior changes. Repeat enough times to observe whether the failure is deterministic or intermittent, and record attempts and outcomes. If about 10 attempts produce no crash, stop widening timing. First confirm with logs that each required precondition actually held, such as screen state, data shape, and scroll position. A missing precondition is a more common cause than a window that is too short.

When the suspected failure window is too short to observe reliably, widen time without inventing a new state:

- Prefer controllable real-world conditions such as network throttling, animation controls, background/foreground transitions, or debugger scheduling when they preserve the suspected sequence.
- A local diagnostic delay may be inserted at the boundary under investigation. For example, if the suspected window is between hiding a typing indicator and showing a message, preserve those two events and increase only the interval between them from milliseconds to a visible `N` seconds.
- Try a small set of explicit delay values and compare against an unchanged control run. Record the exact location and duration of every delay.
- Confirm with logs or signposts that the delayed run still produces the hypothesized events once each, in the original order, with only the gap widened. A delay that misses the real event path or re-triggers itself makes both runs fail to crash for the wrong reason.
- Keep diagnostic timing changes local and clearly identified. Do not ship them or commit them to a working branch. Before removing them, save the diagnostic patch, probe logs, and crash reports in a fresh `.groundwork/notes/crash-YYYYMMDD-HHMMSS/` so the reproduction can be repeated. Create a self-ignoring `.gitignore` containing `*` inside `.groundwork/notes/` if absent. Remove only changes made by this investigation, and only when doing so cannot overwrite unrelated work.

Instrumentation may observe state through logs, breakpoints, signposts, thread diagnostics, or sanitizers. It must not manufacture the failure.

### Choose an experiment that matches the suspected mechanism

Select the strongest evidence-backed mechanism, then read only its reference. Read another reference only when the evidence supports a separate hypothesis.

- For access after an object lifetime ends, dangling pointers, or use-after-free, read [references/memory-lifetime.md](references/memory-lifetime.md).
- For data races or unsafe cross-thread access, read [references/concurrency.md](references/concurrency.md).
- For callbacks, observers, timers, or tasks arriving after lifecycle changes, read [references/lifecycle-callbacks.md](references/lifecycle-callbacks.md).
- For invalid indices or collection and UI snapshot mismatches, read [references/collection-state.md](references/collection-state.md).
- For reentrancy, duplicate completion, retry, or repeated actions, read [references/reentrancy.md](references/reentrancy.md).
- For persisted data or version migration failures, read [references/persistence-migration.md](references/persistence-migration.md).
- For memory pressure, resource exhaustion, or operating-system termination, read [references/resource-pressure.md](references/resource-pressure.md).
- For malformed or extreme values from a server, server settings, push payload, or other external input, read [references/external-input.md](references/external-input.md).

### Invalid reproduction methods

Do not add `fatalError`, forced unwraps, out-of-bounds access, invalid casts, deliberate use-after-free, or similar code whose purpose is to crash. Do not directly call otherwise unreachable internals, fabricate impossible callbacks or events (a value a real external system can send is not impossible; see the external-input reference), corrupt state, bypass product validation, or perform actions a real user or real system event cannot cause.

A unit test, extracted-code reproducer, or sanitizer run may call internal code directly when each call matches a path the product can reach. Show that path in the report.

Do not count a crash as reproduced merely because it stops on the same line. Match the exception or signal, relevant stack shape, required state, and user-observable sequence closely enough to support the same mechanism.

## Report the result

Return a concise report with:

1. Environment match, including all `ASSUMED`, `MISSING`, and `DIFFERENT` items
2. Crash point and the strongest evidence-backed causal path, using exact symbol and type names
3. Ranked hypotheses and their confidence
4. Reproduction steps, diagnostic timing changes, attempt count, and success rate
5. Verdict: `REPRODUCED`, `PARTIALLY REPRODUCED`, or `NOT REPRODUCED`
6. The smallest next experiment if uncertainty remains
7. The absolute path of the saved diagnostic files, when any were saved

`REPRODUCED` means the realistic path matches the reported failure mechanism. `PARTIALLY REPRODUCED` means a related failure or state was reached but important evidence differs. This includes the same mechanism hit only in isolation, such as a unit test or extracted code; say "isolated" in the verdict. `NOT REPRODUCED` is a valid result; report the evidence gap instead of forcing a crash or claiming a fix.
