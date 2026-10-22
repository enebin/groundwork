# Repository instructions

<!-- groundwork:begin project-rules -->
## Repository rules

- Read `/Users/kai.lee/.claude/claude.md` and apply all global rules, including repository-path Git identity and GitHub CLI account routing before commits, pushes, and authenticated GitHub CLI calls.
- Never add a `codex/` prefix to branch names. Use the work prefix configured in `GROUNDWORK.md`.
- Explain work to the user in clear, concise Korean at a middle-school reading level.
- Read `GROUNDWORK.md` before using groundwork workflows.
<!-- groundwork:end project-rules -->

<!-- groundwork:begin implementation -->
### Implementation and tests

- A type that holds or transitions state is not merged without tests. Test each input for the normal path, the ignored case, the failure case, and a completion that arrives late. Pure logic (formatters, resolvers, parsers) is tested the same way. Display-only views are exempt.
- Write each test as Given / When / Then. Name tests in plain language that states the behavior.
- Do not hard-code the same literal across several assertions. Define it once as a test constant or helper.
- Unit tests never reach a real backend, network service, or production data. Replace I/O at its boundary with a test double.
- Do not wait with sleeps. Await async calls directly, or poll for the expected state with a bounded wait helper.
- Write meaningful tests with behavior changes and regression tests for bug fixes. During implementation, run the affected tests. Before declaring work done, run every `verification.commands` entry and the required UI suite. Follow the effective groundwork mode for targeted versus full UI runs; no mode removes required tests or screenshot inspection.
- Every changed screen has a UI test that attaches a screenshot. UI work is done only when the implementer has opened those screenshots and checked them. Checks no test can make go into the UI coverage ledger with the reason. A check may go to "Why QA must look" only when no UI test can make it, after considering all three ways: asserting a value (sizes, frames, visibility, text), launching with a different condition (dark appearance, largest text size, locale, an empty or error state), and attaching a screenshot that the implementer opens. The reason must say why each of the three fails. A missing test hook is not a reason: when a check needs one (a launch argument, an injectable clock or store), add it in debug or test builds only, then write the test. Only a rule in this document that forbids the hook lets the check go, and the reason names that rule. What remains is human judgment: whether wording reads naturally, whether a flow feels easy, how an animation feels.
- Run each UI test once per build. Record the result path with the commit and dirty state it was built from, so later checks on the same build reuse it.
- Keep compiler and type-checker warnings at zero. A new warning is a failure.
- If any verification could not run (missing tool, no simulator), say which one and why in the work result. Report it as unverified. Never report it as passed.
<!-- groundwork:end implementation -->
