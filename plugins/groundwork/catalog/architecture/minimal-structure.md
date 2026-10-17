# Minimal structure

Token cost levels are relative estimates within this step, not measurements.

Every architecture bundle includes this principle set. Onboarding writes it to `docs.architecture` before the bundle's own contract. It is not a choice on its own; with `architecture.bundle: none` nothing is written.

Summary: Build only the structure today's code needs. Put seams only where something outside the code, or a test, forces one. Change the architecture document before changing the structure.

Pros:
- Less code to read and fewer layers to trace through when debugging.
- Every abstraction in the code has a current caller, so none of it is dead weight.
- No hidden global state, which keeps concurrency and tests simple.
- The document always describes the code, because structure changes start there.

Cons:
- When a second case does arrive, someone must extract the abstraction then; that refactor is real work.
- People used to a full layered template (use cases, DI container, coordinators) can read the code as unfinished.
- Requires discipline in review: "we might need it" is a common and persuasive argument.

Token cost: Low — fewer layers means less code touched per change and less for the reviewer to read.

Recommended when: included in every architecture bundle; not chosen on its own.

## Rules to write

```markdown
## Minimal structure

These rules apply to every part of the codebase. The sections after this one add rules for the chosen architecture.

- Do not add abstraction for a future that has not arrived. No use-case layer, no DI container, no coordinator or router object, no plugin registry, unless a current caller needs it. When the same logic has genuinely repeated, or a test cannot be written without a seam, extract then.
- Put a protocol (interface) only at two kinds of boundary: an external system (backend, database, third-party SDK), and I/O that tests must replace (time, randomness, file system, network). Do not put one in front of a type that has a single implementation and no test reason.
- No global mutable registries and no singleton configuration. Pass values down explicitly or through the framework's scoped mechanism (for example SwiftUI Environment or React context).
- Inject dependencies through the constructor (or function parameters). Assemble concrete dependencies at one composition root, at the edge of the app.
- Do not create generation, epoch, or token counters to check whether a result is still valid. Use identity that already exists: the task or request that produced the result, the resource reference, or the current case of the state. Cancellation is cooperative, so a cancelled job's completion can still arrive: check right before writing state, not only when starting.
- Report misuse through visible state and logs, not by crashing. A missing dependency renders an error or placeholder state and logs a fault-level message. Do not use assertion or fatal-error calls to signal a configuration mistake.
- When a change needs a different structure, update this document first, then the code. The document is the single source for structure; working rules live in the rules document.
```

## Review checklist

The architecture reviewer flags, in changed code only:

- A new protocol, layer, registry, or generic wrapper without a second implementation or a test that needs it.
- A new global or static mutable value, or a shared singleton for configuration.
- A dependency pulled from a global locator instead of passed in.
- A counter or token added only to detect stale results.
- A crash used to report misuse (`fatalError`, `assert`, `panic`, `throw` at startup for missing config) where a visible error state would work.
- A structural change with no matching change to the architecture document.
