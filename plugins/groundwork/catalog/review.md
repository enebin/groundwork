# Review bundles

Token cost levels are relative estimates within this step, not measurements.

Onboarding shows these bundles as one choice. It writes the bundle id to `review.bundle`, the reviewer list to `review.reviewers`, and the skeptic policy to `review.skeptic`. After onboarding, `review.reviewers` is the source of truth; the user may add or drop reviewers by hand.

| Bundle | Reviewers | Skeptic |
|---|---|---|
| `app` | architecture, code-quality, ux, ui-qa | blocking |
| `sdk` | architecture, code-quality, dx, ui-qa (when the library has UI) | blocking |
| `product` | architecture, code-quality, security, writing, ux | all |
| `light` | code-quality | blocking |

`architecture` is dropped from any bundle when `architecture.bundle` is `none`, because the reviewer has no standard to judge against.

Skeptic policy:
- `blocking`: the skeptic pass verifies only 🔴/🟠 findings, the ones that block done. 🟡 and nits go to the log unverified. Cheaper, and nothing that blocks is acted on without a second look.
- `all`: the skeptic pass verifies every non-nit finding. Costs more; worth it when 🟡 findings are also acted on (security, user-facing copy).

Every bundle uses the same severity scale and the same done rule from `reference/config.md`.

## app

Summary: For an application with screens. Code is reviewed for structure and correctness; the running app is reviewed by UX personas and by UI QA against the design source.

Reviewers: architecture, code-quality, ux, ui-qa. Skeptic: blocking.

Pros:
- Covers both what the code says and what the user sees; a clean diff cannot hide a broken screen.
- Persona reviewers catch flows that work but are hard to find or recover from.
- UI QA compares against the design source with screenshots as evidence.

Cons:
- UX and UI QA need a runnable app, sample data, and a simulator or browser; setup is a real cost.
- UI checks are slow; running them on every round adds minutes.
- Persona reviews are expert judgment, not real-user research.

Token cost: High — four reviewers each round; `ux` runs one agent per persona and, with `ui-qa`, drives the running app and inspects screenshots.

Recommended when: `project.kind` is `app` and it has a UI.

## sdk

Summary: For a library other developers build on. Adds a DX reviewer who reads the change as a library user would: naming, customization reach, compatibility, docs.

Reviewers: architecture, code-quality, dx, and ui-qa when the library ships UI. Skeptic: blocking.

Pros:
- Catches public API mistakes before they ship, when they are still cheap to change.
- Checks compatibility and deprecation, which code-quality review does not focus on.
- Works with the `api-contract` verification add-on.

Cons:
- DX judgment can be subjective; findings need concrete user scenarios to hold up in the skeptic pass.
- UI QA needs a demo or host app to render the library's views.

Token cost: Medium — three code-reading reviewers, plus `ui-qa` when the library ships UI.

Recommended when: `project.kind` is `library`.

## product

Summary: For a product with real users and real data. Adds security and user-facing writing review, and verifies every non-nit finding.

Reviewers: architecture, code-quality, security, writing, ux. Skeptic: all.

Pros:
- Security review looks at authorization, data isolation, personal data, and untrusted input on every change.
- Writing review keeps copy consistent with behavior and terminology.
- Verifying 🟡 too means fewer false positives reach the fix list.

Cons:
- The most expensive bundle: five first-pass reviewers plus a wider skeptic pass.
- Writing review has nothing to do on changes without user-facing text and reports not applicable.
- No `ui-qa`; add it by hand if pixel accuracy also matters.

Token cost: Very high — five reviewers with one `ux` agent per persona, and the skeptic pass verifies every non-nit finding.

Recommended when: the product handles accounts, payments, organizations, or personal data.

## light

Summary: One code-quality reviewer. Nothing else.

Reviewers: code-quality. Skeptic: blocking.

Pros:
- Fast and cheap; fits the `quick` workflow.
- Still independent of the author, so obvious bugs are caught.

Cons:
- No structure, security, or UI review; those problems pass silently.
- One reviewer means one blind spot.

Token cost: Low — one code reviewer and a skeptic pass on blocking findings only.

Recommended when: scripts, tools, prototypes, or solo projects where speed matters more than coverage.

## Follow-up questions

Onboarding asks only the questions the chosen bundles trigger.

### Personas (when `ux` is in `review.reviewers`)

Triggered by: `app`, `product`.

Ask: "Who uses this product? Name each kind of user and the main thing they come to do."

Write each answer to `review.personas` as `name` and `goal`. One `ux-persona-reviewer` runs per persona. When a persona has several tasks, write them under `## Persona: <name>` in the `GROUNDWORK.md` body. Suggest one or two personas from `project.summary`; let the user edit them.

### Design source (when `ui-qa` is in `review.reviewers`)

Triggered by: `app`, and `sdk` when the library has UI.

Ask: "Where is the design the UI should match? A design tool link, a folder of specs, or none."

Write it to `verification.design_source` (or `null`). When it is `null`, UI QA checks against the task's requirements and platform conventions only and says so in its report. Also ask how to launch the app for QA (scheme or command, sample data, launch flags) and write it under `## UI QA notes`.

### Library UI (for `sdk`)

Ask: "Does the library ship views or screens?" If no, drop `ui-qa` from `review.reviewers` and skip the design source question.

### Review trigger (only for `flight` and `quick`)

`step-loop`, `design-first`, and `tdd-loop` always review every round (`review.trigger: per-round`). `review-only` always reviews on request (`on-request`). Only `flight` and `quick` ask:

Ask: "Should review run every time an implementation is finished, or only when you ask?"

- `per-implementation`: `flight` runs review in `takeoff` before pushing; `quick` runs `review-and-fix` after each implementation. Default.
- `on-request`: review runs only when the user calls `review` or `review-and-fix`.
