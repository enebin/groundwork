# Review bundles

Token cost levels are relative estimates within this step, not measurements.

Onboarding shows these bundles as one choice. It writes the bundle id to `review.bundle`, the reviewer list to `review.reviewers`, and the skeptic policy to `review.skeptic`. After onboarding, `review.reviewers` is the source of truth; the user may add or drop reviewers by hand.

These reviewers read code and run on every change. The agents that exercise the running app (`ui-qa`, `ux`) are not part of any bundle: they run only in release QA, which is a separate opt-in choice below. Screens are checked on every change by UI tests instead.

| Bundle | Reviewers | Skeptic |
|---|---|---|
| `app` | architecture, code-quality | blocking |
| `sdk` | architecture, code-quality, dx | blocking |
| `product` | architecture, code-quality, security, writing | all |
| `light` | code-quality | blocking |

`architecture` is dropped from any bundle when `architecture.bundle` is `none`, because the reviewer has no standard to judge against.

Skeptic policy:
- `blocking`: the skeptic pass verifies only 🔴/🟠 findings, the ones that block done. 🟡 and nits go to the log unverified. Cheaper, and nothing that blocks is acted on without a second look.
- `all`: the skeptic pass verifies every non-nit finding. Costs more; worth it when 🟡 findings are also acted on (security, user-facing copy).

Every bundle uses the same severity scale and the same done rule from `reference/config.md`.

## app

Summary: For an application with screens. Code is reviewed for structure and correctness; screens are covered by UI tests on every change.

Reviewers: architecture, code-quality. Skeptic: blocking.

Pros:
- Two independent angles on every change at a modest cost.

Cons:
- Nobody judges usability or visual polish per change; that waits for release QA or a human.

Token cost: Medium — two code-reading reviewers each round.

Recommended when: `project.kind` is `app`.

## sdk

Summary: For a library other developers build on. Adds a DX reviewer who reads the change as a library user would: naming, customization reach, compatibility, docs.

Reviewers: architecture, code-quality, dx. Skeptic: blocking.

Pros:
- Catches public API mistakes while they are still cheap to change.

Cons:
- DX judgment can be subjective; findings need concrete user scenarios to survive the skeptic pass.

Token cost: Medium — three code-reading reviewers each round.

Recommended when: `project.kind` is `library`.

## product

Summary: For a product with real users and real data. Adds security and user-facing writing review, and verifies every non-nit finding.

Reviewers: architecture, code-quality, security, writing. Skeptic: all.

Pros:
- Authorization, data isolation, personal data, and copy accuracy are checked on every change.

Cons:
- The most expensive bundle; writing review often has nothing to do and reports not applicable.

Token cost: High — four reviewers each round, and the skeptic pass verifies every non-nit finding.

Recommended when: the product handles accounts, payments, organizations, or personal data.

## light

Summary: One code-quality reviewer. Nothing else.

Reviewers: code-quality. Skeptic: blocking.

Pros:
- Fast and cheap; fits the `quick` workflow.

Cons:
- One reviewer means one blind spot; structure and security problems pass silently.

Token cost: Low — one code reviewer and a skeptic pass on blocking findings only.

Recommended when: scripts, tools, prototypes, or solo projects where speed matters more than coverage.

## Release QA

Asked separately when the project has screens. Writes `review.release_qa`.

Summary: before a release, agents launch the app and check what UI tests cannot: the rows of the UI coverage ledger with no automated test, and, when personas are set, how easily each persona completes its tasks.

### off (Recommended)

Pros: no agent drives the running app; screens are covered by UI tests and the implementer's look at their screenshots.
Cons: what tests cannot assert (visual polish, readability at large text, usability) is left to a human; the ledger lists exactly what to look at.
Token cost: Low — nothing runs.

### on

Pros: an independent agent looks at every uncovered check and every persona task before each release.
Cons: very slow. A single screen took 10 to 20 minutes per agent in testing, and every persona adds one more agent.
Token cost: Very high — agents drive a simulator or browser step by step and read many screenshots.

When on, onboarding also asks for personas and the design source.

## Follow-up questions

Onboarding asks only the questions the chosen bundles trigger.

### Personas (when release QA is on)

Ask: "Who uses this product? Name each kind of user and the main thing they come to do."

Write each answer to `review.personas` as `name` and `goal`. In release QA, one `ux-persona-reviewer` runs per persona. When a persona has several tasks, write them under `## Persona: <name>` in the `GROUNDWORK.md` body. Suggest one or two personas from `project.summary`; let the user edit them.

### Design source (when release QA is on, or the `design-fidelity` add-on is chosen)

Ask: "Where is the design the UI should match? A design tool link, a folder of specs, or none."

Write it to `verification.design_source` (or `null`). When it is `null`, release QA checks against requirements and platform conventions only and says so in its report. Also ask how to launch the app for QA (scheme or command, sample data, launch flags) and write it under `## UI QA notes`.

### Review trigger (only for `flight` and `quick`)

`step-loop`, `design-first`, and `tdd-loop` always review every round (`review.trigger: per-round`). `review-only` always reviews on request (`on-request`). Only `flight` and `quick` ask:

Ask: "Should review run every time an implementation is finished, or only when you ask?"

- `per-implementation`: `flight` runs review in `takeoff` before pushing; `quick` runs `review-and-fix` after each implementation. Default.
- `on-request`: review runs only when the user calls `review` or `review-and-fix`.

## Modes

Asked for every bundle. A mode sets how hard the review loop works, never which model runs it. Overridable per run with `--mode`. The exact rules are in Modes in `reference/config.md`.

### eco

Summary: one review round; fixes are checked by tests only.
Pros: the cheapest loop that still reviews every change once.
Cons: a fix can introduce a problem no reviewer sees.
Token cost: Low — one review pass per step.
Recommended when: small fixes, experiments, or work far from a release.

### normal

Summary: up to three rounds; only reviewers with blocking findings look again.
Pros: fixes are re-reviewed by the reviewer who raised the problem, without paying for the rest.
Cons: a fix for one reviewer's finding is not re-checked by the others.
Token cost: Medium — usually one full round plus a narrow second round.
Recommended when: everyday work. Default.

### sport

Summary: up to three rounds with every reviewer each time, and the full test suite every round.
Pros: every fix is seen by every reviewer and every test.
Cons: slowest and most expensive; repeats checks that already passed.
Token cost: High — every round costs as much as the first.
Recommended when: shared components or themes change, payments, authentication, or the step before a release.
