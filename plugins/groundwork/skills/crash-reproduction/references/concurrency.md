# Concurrency Failures

Use this guide when the evidence points to a data race or unsafe cross-thread access.

- Find two real operations that touch the same state, such as receiving a streamed update while cancelling, refreshing while pagination completes, or entering the background while a callback updates UI.
- Repeat those operations through accepted UI and system events. Widen one existing scheduling boundary with a breakpoint or delay instead of invoking a method from an impossible queue.
- Use Thread Sanitizer or equivalent race diagnostics where available. Treat a sanitizer-only finding as supporting evidence until the conflicting accesses and state match the report.
