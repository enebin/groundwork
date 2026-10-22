# Review bundles

Token cost levels are relative estimates within this step, not measurements.

Onboarding shows these bundles as one choice. It writes the bundle id to `review.bundle`, the reviewer list to `review.reviewers`, and the skeptic policy to `review.skeptic`. After onboarding, `review.reviewers` is the source of truth; the user may add or drop reviewers by hand.

These reviewers read code and run on every change. `dx` judges developer experience from the code: it traces each `developer` persona's tasks through a library API, an HTTP or RPC API, or a command-line tool. End-user UX is not part of any bundle: whether it runs from the code (`ux-flow-reviewer`) or on the running app (`ux-persona-reviewer`), and how often, is chosen in step 7 with QA, from `catalog/screen-checks.md`. When step 7 picks code-based UX on every PR, the `ux` reviewer joins these reviewers in every round. Screens are checked on every change by UI tests.

| Bundle | Reviewers | Skeptic |
|---|---|---|
| `app` | architecture, code-quality | blocking |
| `sdk` | architecture, code-quality, dx | blocking |
| `service` | architecture, code-quality, security, dx | blocking |
| `product` | architecture, code-quality, security, writing (+ dx when it exposes a public API) | all |
| `light` | code-quality | blocking |

`architecture` is dropped from any bundle when `architecture.bundle` is `none`, because the reviewer has no standard to judge against.

Skeptic policy:
- `blocking`: the skeptic pass verifies only 🔴/🟠 findings, the ones that block done. 🟡 and nits go to the log unverified. Cheaper, and nothing that blocks is acted on without a second look.
- `all`: the skeptic pass verifies every non-nit finding. Costs more; worth it when 🟡 findings are also acted on (security, user-facing copy).

Every bundle uses the same severity scale and the same done rule from `reference/config.md`.

## app

Summary: For an application with screens. Code is reviewed for structure and correctness; screens are covered by UI tests on every change, and usability follows the screen checks in step 7.

Reviewers: architecture, code-quality. Skeptic: blocking.

Pros:
- Structure and correctness are checked on every change at a low cost.

Cons:
- Usability and visual polish are not judged here; they follow the screen checks or are left to a human.

Token cost: Medium — two code-reading reviewers each round.

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
- No end-user review; if the service also renders pages, turn on UX in the screen checks.

Token cost: Medium — four code-reading reviewers each round.

Recommended when: `project.kind` is `service` with no screens of its own.

## product

Summary: For a product with real users and real data. Adds security and user-facing writing review, and verifies every non-nit finding.

Reviewers: architecture, code-quality, security, writing, and dx when the product also exposes a public API. Skeptic: all.

Pros:
- Authorization, data isolation, personal data, and copy accuracy are checked on every change.

Cons:
- The most expensive bundle; writing review often has nothing to do and reports not applicable.

Token cost: High — four code-reading reviewers each round, and the skeptic pass verifies every non-nit finding.

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

## Screen checks are configured separately

UX, QA, and their execution-cost guidance are in `catalog/screen-checks.md`, onboarding step 7. Do not ask for UX, release QA, or overall mode as review-specific settings. Automated testing is mandatory implementation work from `reference/implementation.md`.

## Follow-up questions

Onboarding asks only the questions the chosen bundles trigger.

### Developer personas (when `dx` is in `review.reviewers`)

Ask: "Who builds on this? Name each kind of developer and the main thing they come to do." Examples: app developers importing the library, API clients, CLI users.

Write each answer to `review.personas` as `name`, `goal`, and `kind: developer`. `dx` traces every `developer` persona's tasks through the code on each change. When a persona has several tasks, write them under `## Persona: <name>` in the `GROUNDWORK.md` body. Suggest one or two personas from `project.summary`; let the user edit them. End-user personas (`kind: user`) are collected in step 7.

### Review trigger (only for `quick`)

`step-loop`, `design-first`, and `tdd-loop` always review every round (`review.trigger: per-round`). `review-only` always reviews on request (`on-request`). Only `quick` asks:

Ask: "Should review run every time an implementation is finished, or only when you ask?"

- `per-implementation`: `quick` runs `review-and-fix` after each implementation. Default.
- `on-request`: review runs only when the user calls `review` or `review-and-fix`.

## Overall effort

`eco / normal / sport` applies to implementation verification, review, and screen checks together. It is presented with the whole onboarding route, not as a code-review option. The exact preset rules and per-run override behavior are in Modes in `reference/config.md`. The default is normal; a user can pick an effort for each run without configuring every detail.
