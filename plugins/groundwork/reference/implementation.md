# Default implementation rules

Tests are part of implementation, not an onboarding choice. Onboarding always writes the block below into `docs.rules` (normally `AGENTS.md`), inside a managed `implementation` block, in `language.artifacts`. It also discovers build/test commands and UI paths as described in the onboarding skill. Existing stronger repository rules stay in force.

## Rules to write

```markdown
### Implementation and tests

- A type that holds or transitions state is not merged without tests. Test each input for the normal path, the ignored case, the failure case, and a completion that arrives late. Pure logic (formatters, resolvers, parsers) is tested the same way. Display-only views are exempt.
- Write each test as Given / When / Then. Name tests in plain language that states the behavior.
- Do not hard-code the same literal across several assertions. Define it once as a test constant or helper.
- Unit tests never reach a real backend, network service, or production data. Replace I/O at its boundary with a test double.
- Do not wait with sleeps. Await async calls directly, or poll for the expected state with a bounded wait helper.
- Write meaningful tests with behavior changes and regression tests for bug fixes. During implementation, run the affected tests. Before declaring work done, run every `verification.commands` entry and the required UI suite. Follow the effective groundwork mode for targeted versus full UI runs; no mode removes required tests or screenshot inspection.
- Every changed screen has a UI test that attaches a screenshot. UI work is done only when the implementer has opened those screenshots and checked them. Checks no test can make go into the UI coverage ledger with the reason. A check may go to "Why QA must look" only when no UI test can make it, after considering all three ways: asserting a value (sizes, frames, visibility, text), launching with a different condition (dark appearance, largest text size, locale, an empty or error state), and attaching a screenshot that the implementer opens. The reason must say why each of the three fails. What remains is human judgment: whether wording reads naturally, whether a flow feels easy, how an animation feels.
- Run each UI test once per build. Record the result path with the commit and dirty state it was built from, so later checks on the same build reuse it.
- Keep compiler and type-checker warnings at zero. A new warning is a failure.
- If any verification could not run (missing tool, no simulator), say which one and why in the work result. Report it as unverified. Never report it as passed.
```

## Automatic setup

Keep the `verification` keys: they are execution settings used by the skills, not a user-facing verification step. New repositories use `verification.base: evidence`, or `test-first` for `tdd-loop`. When the repository has CI running the full test suite, use `ci-gate`; for `tdd-loop` also write the test-first rules. The baseline implementation rules always apply.

Use `catalog/verification.md` as the source for CI gate, test-first, and add-on rule blocks. Detect applicable add-ons from that catalog's “Recommended when” conditions and show them in the final preview, without a separate bundle question. A design-fidelity check needs a readable design source; do not enable it merely because the project has screens. Include existing add-ons on re-runs. The user may change these details in the final preview or later in `GROUNDWORK.md`.

For existing configurations, retain `verification.base` and add-ons unless the user changes them. Even a legacy `basic` configuration receives these default implementation rules when onboarding runs again. Show any resulting rule change in the final preview; do not remove stronger existing requirements.
