# groundwork

Decide once how a repository works, then let the agent run it that way.

`/groundwork:onboarding` asks seven questions: language, issue tracker, workflow, branches, verification, architecture, and review. Each answer is a **bundle**: a named set of rules and skills that work together, shown with its pros and cons and a recommended option for your repository. Your answers go into `GROUNDWORK.md`, and the chosen rules go into your own `AGENTS.md` and `ARCHITECTURE.md`. Every other groundwork skill reads that file, so the same plugin behaves correctly in every repository.

It is built for starting a new project. An existing repository gets the same questions, with recommendations taken from what it already has.

Works in Claude Code and Codex. Both tools share one set of skills; only the manifests differ.

## Install

Claude Code:

```
/plugin marketplace add enebin/groundwork
/plugin install groundwork@groundwork
```

Then, in the repository you want to set up:

```
/groundwork:onboarding
```

Optional: install [skeptic-review](https://github.com/enebin/skeptic-review) to have review findings verified before you see them. Without it, reviews report `SkepticReview: OFF`.

## What onboarding asks

| Step | Decides | Choices | Default for a new project |
|---|---|---|---|
| 1 | Language | conversation / artifacts | yours / English (fewer tokens) |
| 2 | Issue tracker | local files, GitHub Projects, Linear, Jira | local files |
| 3 | Workflow | step-loop, design-first, tdd-loop, flight, quick, review-only | step-loop |
| 4 | Branches | develop + release, main only | develop + release |
| 5 | Verification | evidence, ci-gate, test-first, basic; add-ons design-fidelity, api-contract, isolated-e2e, visual-regression | evidence |
| 6 | Architecture | unidirectional, mvvm, layered-service, layered-web, none | depends on the stack |
| 7 | Review | app, sdk, product, light | depends on the kind of project |
| 8 | Anything else | free text | nothing |

Before the first question you see this whole table filled in for your repository, and can take every recommendation at once. Try not to: what you pick here tends to stay.

Every bundle, with its pros, cons, and the exact rules it writes, is in [`plugins/groundwork/catalog/`](plugins/groundwork/catalog/).

## Skills

| Skill | Use |
|---|---|
| `onboarding` | Set up or change `GROUNDWORK.md` |
| `plan` | Split a job into a parent issue and step issues |
| `step` | Run one step: implement, then verify → review → fix until no confirmed 🔴/🟠 remains |
| `boarding`, `door-closing`, `taxiing`, `takeoff`, `landing`, `rejoin` | The flight workflow, one issue at a time |
| `release`, `autoland` | Cut a release; merge automatically once CI passes |
| `review-and-fix`, `commit-push` | The quick workflow |
| `review` | Run the chosen reviewers in parallel and merge their findings |
| `ux-review` | Usability review, one agent per persona |
| `ui-qa` | Check the running UI against the task and the design source |

Reviewer agents: `architecture-reviewer`, `code-quality-reviewer`, `security-reviewer`, `writing-reviewer`, `dx-reviewer`, `ux-persona-reviewer`, `ui-qa`. Each has a general checklist in the plugin and reads repository-specific checks from `## Review focus: <reviewer>` in `GROUNDWORK.md`.

## GROUNDWORK.md

The contract is in [`plugins/groundwork/reference/config.md`](plugins/groundwork/reference/config.md). Keys are only ever added, never renamed or removed. When the shape must change, the schema version goes up and onboarding migrates the file.

Commit `GROUNDWORK.md` and the docs it writes. Teammates then only install the plugin; they do not need to run onboarding.

## License

MIT
