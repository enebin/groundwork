# Review bundles

Token cost levels are relative estimates within this step, not measurements.

Onboarding shows these bundles as one choice. It writes the bundle id to `review.bundle`, the reviewer list to `review.reviewers`, and the skeptic policy to `review.skeptic`. After onboarding, `review.reviewers` is the source of truth; the user may add or drop reviewers by hand.

These reviewers read code and run on every change. `ux` judges end-user experience from the code: it traces each `user` persona's tasks through screens and state without launching the app. `dx` does the same for `developer` personas through a library API, an HTTP or RPC API, or a command-line tool. The agents that exercise the running app (`ui-qa`, `ux-persona-reviewer`) are not part of any bundle: their automatic trigger is chosen separately in step 7, from `catalog/qa.md`. Screens are checked on every change by UI tests instead.

| Bundle | Reviewers | Skeptic |
|---|---|---|
| `app` | architecture, code-quality, ux | blocking |
| `sdk` | architecture, code-quality, dx | blocking |
| `service` | architecture, code-quality, security, dx | blocking |
| `product` | architecture, code-quality, security, writing, ux (+ dx when it exposes a public API) | all |
| `light` | code-quality | blocking |

`architecture` is dropped from any bundle when `architecture.bundle` is `none`, because the reviewer has no standard to judge against.

Skeptic policy:
- `blocking`: the skeptic pass verifies only 🔴/🟠 findings, the ones that block done. 🟡 and nits go to the log unverified. Cheaper, and nothing that blocks is acted on without a second look.
- `all`: the skeptic pass verifies every non-nit finding. Costs more; worth it when 🟡 findings are also acted on (security, user-facing copy).

Every bundle uses the same severity scale and the same done rule from `reference/config.md`.

## app

Summary: For an application with screens. Code is reviewed for structure, correctness, and whether each persona can finish its tasks; screens are covered by UI tests on every change.

Reviewers: architecture, code-quality, ux. Skeptic: blocking.

Pros:
- Usability problems that show in the code (extra steps, missing states, dead ends) are caught on every change, without launching the app.

Cons:
- Visual polish and on-screen readability are not judged per change; that follows the separate QA policy or is left to a human.

Token cost: Medium — three code-reading reviewers each round.

Recommended when: `project.kind` is `app`.

## sdk

Summary: For a library other developers build on. Adds a DX reviewer who traces developer tasks through the public API: call sites, customization reach, compatibility, docs.

Reviewers: architecture, code-quality, dx. Skeptic: blocking.

Pros:
- Catches public API mistakes while they are still cheap to change.

Cons:
- DX judgment can be subjective; findings need concrete user scenarios to survive the skeptic pass.

Token cost: Medium — three code-reading reviewers each round.

Recommended when: `project.kind` is `library`.

## service

Summary: For a backend whose users are other programs: an HTTP or RPC API, a worker, or a CLI. No screens, so no `ux`; a DX reviewer traces client developers' tasks through the API instead.

Reviewers: architecture, code-quality, security, dx. Skeptic: blocking.

Pros:
- Status codes, error shapes, pagination, retries, and schema drift are checked on every change, alongside authorization.

Cons:
- No end-user review; add `ux` by hand if the service also renders pages.

Token cost: Medium — four code-reading reviewers each round.

Recommended when: `project.kind` is `service` with no screens of its own.

## product

Summary: For a product with real users and real data. Adds security and user-facing writing review, and verifies every non-nit finding.

Reviewers: architecture, code-quality, security, writing, ux, and dx when the product also exposes a public API. Skeptic: all.

Pros:
- Authorization, data isolation, personal data, and copy accuracy are checked on every change.

Cons:
- The most expensive bundle; writing review often has nothing to do and reports not applicable.

Token cost: High — five code-reading reviewers each round, and the skeptic pass verifies every non-nit finding.

Recommended when: the product handles accounts, payments, organizations, or personal data.

## light

Summary: One code-quality reviewer. Nothing else.

Reviewers: code-quality. Skeptic: blocking.

Pros:
- Fast and cheap; fits the `quick` workflow.

Cons:
- One reviewer means one blind spot; structure and security problems pass silently.

Token cost: Low — one code reviewer and a skeptic pass on blocking findings only.

Recommended when: scripts, tools, prototypes, or solo projects where speed matters more than coverage. For a command-line tool other people run, add `dx`.

## QA is configured separately

The QA strength and execution-cost guidance are in `catalog/qa.md`, onboarding step 7. Do not ask for release QA or overall mode as review-specific settings. Automated testing is mandatory implementation work from `reference/implementation.md`.

## Follow-up questions

Onboarding asks only the questions the chosen bundles trigger.

### Personas (when `ux` or `dx` is in `review.reviewers`)

Ask: "Who uses this? Name each kind of user and the main thing they come to do." Ask about end users when `ux` is selected, and about developers who build on the code (app developers importing the library, API clients, CLI users) when `dx` is selected.

Write each answer to `review.personas` as `name`, `goal`, and `kind` (`user` or `developer`). `ux` traces every `user` persona's tasks through the code on each change, and `dx` every `developer` persona's; when the QA policy calls for persona checks, one `ux-persona-reviewer` per selected `user` persona also checks the running app. When a persona has several tasks, write them under `## Persona: <name>` in the `GROUNDWORK.md` body. Suggest one or two personas from `project.summary`; let the user edit them.

### Review trigger (only for `flight` and `quick`)

`step-loop`, `design-first`, and `tdd-loop` always review every round (`review.trigger: per-round`). `review-only` always reviews on request (`on-request`). Only `flight` and `quick` ask:

Ask: "Should review run every time an implementation is finished, or only when you ask?"

- `per-implementation`: `flight` runs review in `takeoff` before pushing; `quick` runs `review-and-fix` after each implementation. Default.
- `on-request`: review runs only when the user calls `review` or `review-and-fix`.

## Overall effort

`eco / normal / sport` applies to implementation verification, review, and applicable QA together. It is presented with the whole onboarding route, not as a code-review option. The exact preset rules and per-run override behavior are in Modes in `reference/config.md`. The default is normal; a user can pick an effort for each run without configuring every detail.
