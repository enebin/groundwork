# Architecture

<!-- groundwork:begin minimal-structure -->
## Minimal structure

These rules apply to every part of the codebase. The sections after this one add rules for the chosen architecture.

- Do not add abstraction for a future that has not arrived. No use-case layer, no DI container, no coordinator or router object, no plugin registry, unless a current caller needs it. When the same logic has genuinely repeated, or a test cannot be written without a seam, extract then.
- Put a protocol (interface) only at two kinds of boundary: an external system (backend, database, third-party SDK), and I/O that tests must replace (time, randomness, file system, network). Do not put one in front of a type that has a single implementation and no test reason.
- No global mutable registries and no singleton configuration. Pass values down explicitly or through the framework's scoped mechanism (for example SwiftUI Environment or React context).
- Inject dependencies through the constructor (or function parameters). Assemble concrete dependencies at one composition root, at the edge of the app.
- Do not create generation, epoch, or token counters to check whether a result is still valid. Use identity that already exists: the task or request that produced the result, the resource reference, or the current case of the state. Cancellation is cooperative, so a cancelled job's completion can still arrive: check right before writing state, not only when starting.
- Report misuse through visible state and logs, not by crashing. A missing dependency renders an error or placeholder state and logs a fault-level message. Do not use assertion or fatal-error calls to signal a configuration mistake.
- When a change needs a different structure, update this document first, then the code. The document is the single source for structure; working rules live in the rules document.
<!-- groundwork:end minimal-structure -->
