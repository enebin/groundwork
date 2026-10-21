<p align="center">
  <img src="assets/hero.svg" alt="groundwork — choose how your repository works, once. A plugin for Claude Code and Codex." width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-2F6B5A"></a>
  <img alt="Claude Code plugin" src="https://img.shields.io/badge/Claude%20Code-plugin-D97757">
  <img alt="Codex plugin" src="https://img.shields.io/badge/Codex-plugin-1F1E1B">
  <img alt="Version 0.1.0" src="https://img.shields.io/badge/version-0.1.0-6E6C66">
</p>

**groundwork** is a Claude Code and Codex plugin that sets up how an AI coding agent works in your repository — issue tracking, workflow, deployment strategy, architecture, AI code review, and rendered QA — and then runs that workflow for you.

`/groundwork:onboarding` asks eight questions. Each answer is a **bundle**: a named set of rules and skills that work together, shown with its pros, cons, token cost, and a recommended option for your repository. Your answers go into `GROUNDWORK.md`. Mandatory implementation and test rules go into your own `AGENTS.md`, alongside the chosen rules; architecture goes into `ARCHITECTURE.md`. Every other groundwork skill reads that file, so the same plugin behaves correctly in every repository.

It is built for starting a new project. An existing repository gets the same questions, with recommendations taken from what it already has.

Before the first question, onboarding shows the whole route with a recommendation for every step:

<p align="center">
  <img src="assets/overview.svg" alt="Onboarding in an empty repository: every step with its recommended bundle, before the first question." width="100%">
</p>

At each step, it compares every bundle by pros, cons, and token cost:

<p align="center">
  <img src="assets/choices.svg" alt="Onboarding step 3 of 8: workflow bundles compared by pros, cons, and token cost, with the recommended bundle first." width="100%">
</p>

## How it works

<p align="center">
  <img src="assets/how-it-works.svg" alt="Onboarding writes GROUNDWORK.md, AGENTS.md, and ARCHITECTURE.md; every groundwork skill and reviewer agent follows them." width="100%">
</p>

Both tools share one set of skills; only the manifests differ.

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
| 3 | Workflow | step-loop, design-first, tdd-loop, quick, review-only; worktree per issue | step-loop, no worktree |
| 4 | Deployment strategy | develop + release, main only; merge style | develop + release |
| 5 | Architecture | unidirectional, mvvm, layered-service, layered-web, none | depends on the stack |
| 6 | Review | app, sdk, service, product, light; Skeptic policy | depends on the kind of project |
| 7 | QA | manual, release, continuous | manual |
| 8 | Anything else | free text | nothing |

Before the first question you see this whole table filled in for your repository, and can take every recommendation at once. Try not to: what you pick here tends to stay.

Tests are part of implementation, not an onboarding choice. Onboarding detects build/test commands and applicable checks, previews them, and writes the [default implementation rules](plugins/groundwork/reference/implementation.md) into `AGENTS.md`.

`eco / normal / sport` is a separate overall effort preset, defaulting to `normal`. Like a reasoning-effort setting, it adjusts verification breadth, review repetition, and applicable QA scope together; it does not select a model. Override it per run with `--mode`. Users can edit individual settings later. The QA bundle still decides when rendered QA runs.

Every bundle, with its pros, cons, and the exact rules it writes, is in [`plugins/groundwork/catalog/`](plugins/groundwork/catalog/).

## Skills

| Skill | Use |
|---|---|
| `onboarding` | Set up or change `GROUNDWORK.md` |
| `plan` | Split a job into a parent issue and step issues |
| `step` | Run one step: implement, then verify → review → fix until no confirmed 🔴/🟠 remains |
| `takeoff` | Rebase, push, and open the PR for a finished step |
| `landing`, `rejoin` | Clean up after a merge; move a branch out of its worktree |
| `release`, `autoland` | Cut a release; merge automatically once CI passes |
| `review-and-fix`, `commit-push` | The quick workflow |
| `review` | Run the chosen reviewers in parallel and merge their findings |
| `ux-review` | Usability review for selected end-user personas, under the QA policy or on request |
| `ui-qa` | Check the running app for uncovered UI checks, under the QA policy or on request |

Code reviewers, run on every change: `architecture-reviewer`, `code-quality-reviewer`, `security-reviewer`, `writing-reviewer`, `dx-reviewer`, and `ux-flow-reviewer`. The last two trace personas' tasks through the code without launching anything: `ux-flow-reviewer` for end users of an app (extra steps, missing states, dead ends), `dx-reviewer` for developers building on a library, an HTTP or RPC API, or a CLI. Each has a general checklist in the plugin and reads repository-specific checks from `## Review focus: <reviewer>` in `GROUNDWORK.md`.

Screens are checked on every change by UI tests that attach screenshots, which the implementer opens and inspects. Separate rendered QA is configured in [the QA step](plugins/groundwork/catalog/qa.md): only on request (`manual`, the default), before releases (`release`), or also after each implementation (`continuous`). The UI coverage ledger (`docs/ui-coverage.md`) lists what tests cannot check.

Web tools can often locate page elements directly. iOS simulators and Android emulators may take longer because of builds, installation, startup, and the available UI tools. Screenshot-based web QA can also be slow. Actual time and token usage depend on coverage, personas, tools, and retries; there is no promised platform multiplier.

Review fixes go to the `fixer` agent. It starts from a fresh context, fixes the confirmed findings, and re-runs their tests, so after implementation the step's own context grows only by short reports.

## GROUNDWORK.md

The contract is in [`plugins/groundwork/reference/config.md`](plugins/groundwork/reference/config.md). Keys are only ever added, never renamed or removed. When the shape must change, the schema version goes up and onboarding migrates the file.

Commit `GROUNDWORK.md` and the docs it writes. Teammates then only install the plugin; they do not need to run onboarding.

## License

MIT
