<p align="center">
  <img src="assets/hero.svg" alt="groundwork — choose how your repository works, once. A plugin for Claude Code and Codex." width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-2F6B5A"></a>
  <img alt="Claude Code plugin" src="https://img.shields.io/badge/Claude%20Code-plugin-D97757">
  <img alt="Codex plugin" src="https://img.shields.io/badge/Codex-plugin-1F1E1B">
  <img alt="Version 0.3.0" src="https://img.shields.io/badge/version-0.3.0-6E6C66">
</p>

<p align="center"><b>Set it up once. Then just say what to build.</b></p>

<p align="center">
  <a href="#install">Install</a> &ensp;·&ensp;
  <a href="#your-first-feature">Your first feature</a> &ensp;·&ensp;
  <a href="#what-you-can-ask-for">What you can ask for</a> &ensp;·&ensp;
  <a href="README.ko.md">한국어</a> &ensp;·&ensp;
  <a href="README.zh-CN.md">简体中文</a>
</p>

<br>

**groundwork** is a Claude Code and Codex plugin that decides, once, how AI coding agents work in your repository: issue tracking, workflow, branches and releases, architecture, code review, and UI checks. After that, you ask for a feature in plain words, and the agent files the issue, implements, tests, reviews, and fixes it the way you chose. It stops only where a person should decide.

There are no commands to learn. Every skill can be started in plain words, in any language.

## Install

Claude Code:

```
/plugin marketplace add enebin/groundwork
/plugin install groundwork@groundwork
```

Then, in the repository you want to set up, say:

```text
Set up groundwork for this repo.
```

Onboarding asks eight questions, recommends an answer for each, and saves your choices to `GROUNDWORK.md`. Every other skill reads that file.

groundwork checks GitHub for a new release at most once a day and tells you once per release. To update, run `claude plugin update groundwork@groundwork` and restart Claude Code.

Optional: install [skeptic-review](https://github.com/enebin/skeptic-review) to double-check review findings before they reach you.

## Your first feature

```text
Add a sign-in screen.
```

That one sentence is the whole request. With the default setup, groundwork then:

1. Files an issue for the request and creates a branch in its own worktree.
2. Implements it, with tests written alongside.
3. Runs your build and tests, then the reviewers you chose, in parallel.
4. Fixes what the reviewers confirm, and repeats until no serious finding is left.
5. Checks the changed screens when your setup asks for it.
6. Reports what it did and offers a commit.

When you are happy with it:

```text
Push it and open a PR.
```

groundwork rebases, verifies again, pushes, and opens the PR. With auto-merge on, it also waits for CI, merges, and cleans up the branch.

A job too large for one PR is split into steps first; you approve the plan, and each step then runs the same way.

### Where it stops for you

groundwork never decides these on its own:

- **Approving a plan** for a job split into several steps.
- **Approving a design document**, in the design-first workflow.
- **Pushing and opening a PR.** It waits until you ask in so many words.
- **Merging**, unless you turned on auto-merge.
- **Releasing.** A release starts only when you ask, and scheduled release prep waits for your Yes before publishing.

## What you can ask for

These are examples; any wording that means the same works.

| You say | What runs |
|---|---|
| "Add dark mode." / "Fix the crash on the settings screen." | `step`: issue → implement → test → review → fix |
| "This is big. Split it into issues." | `plan`, then `step` for each part |
| "Push it and open a PR." | `takeoff`, then `autoland` if auto-merge is on |
| "The PR is merged. Clean up." | `landing` |
| "Review my changes." | `review` |
| "Can new users get through sign-up?" | `ux-journey` on the running app |
| "Check the settings screen on the app." | `ui-qa` |
| "Prepare release 1.2.0." | `release` |
| "Summarize this week." | `weekly-summary` |
| "I'm stopping here. Leave a note for next time." | `handoff` |

You can still type a skill by name, such as `/groundwork:step`, when you want to be exact.

## Set it up once

Before the first question, onboarding shows every step and its recommended setup at a glance:

<p align="center">
  <img src="assets/overview.svg" alt="Onboarding in an empty repository: every step with its recommended bundle, before the first question." width="100%">
</p>

Each choice is a **bundle**: rules and skills that work together, shown with pros, cons, and token cost.

<p align="center">
  <img src="assets/choices.svg" alt="Onboarding step 3 of 8: workflow bundles compared by pros, cons, and token cost, with the recommended bundle first." width="100%">
</p>

| Step | Category | Options | New project default |
|---|---|---|---|
| 1 | Language | conversation / artifacts | your language / English (saves tokens) |
| 2 | Issue tracker | local files, GitHub Projects, Linear, Jira | local files |
| 3 | Workflow | step-loop, design-first, tdd-loop, quick, review-only; worktree per issue | step-loop, worktree per issue |
| 4 | Release strategy | develop + release, main only; merge style | develop + release |
| 5 | Architecture | unidirectional, mvvm, layered-service, layered-web, none | recommended based on stack |
| 6 | Review | app, sdk, service, product, light | recommended based on project type |
| 7 | Screen checks | UX and QA: every PR, before release, or manual | UX: every PR, from the code. QA: manual |
| 8 | Custom rules | free text | none |

It works best on a fresh `git init`, such as a side project, a hackathon prototype, or an assignment due tomorrow, so you start with rules, reviews, and QA in place. On an existing repository it asks the same questions and recommends answers from your code.

Commit `GROUNDWORK.md` and the docs onboarding writes. Teammates only need to install the plugin to work under the same rules. To change a choice later, say so; to pick up new features after a plugin update, say "update groundwork".

<p align="center">
  <img src="assets/how-it-works.svg" alt="Onboarding writes GROUNDWORK.md, AGENTS.md, and ARCHITECTURE.md; every groundwork skill and reviewer agent follows them." width="100%">
</p>

## What runs behind a request

- **Tests are part of implementation**, not an option. Onboarding finds your build and test commands and writes the [implementation rules](plugins/groundwork/reference/implementation.md) into `AGENTS.md`.
- **Reviewers** for architecture, code quality, security, writing, and developer experience run in parallel on each change. Confirmed findings go to a `fixer` agent in a fresh context, so your conversation receives only a short summary.
- **Screen checks** test whether each user persona can finish its tasks, from the code or on the running app, and check the rendered UI against requirements. See [screen checks](plugins/groundwork/catalog/screen-checks.md) and how the [UX checks compare](plugins/groundwork/reference/ux-checks.md). In a [benchmark](bench/ux/flow-reviewer/README.md), the code-based UX review found 36 of 39 seeded defects at about a tenth of the app-based review's cost.
- **Thoroughness** is one preset, `eco`, `normal` (default), or `sport`, that sets verification depth, review rounds, and screen-check scope together. Say "use sport mode for this one" to change it for a single request.

A review does not replace your own judgment, and checks on the running app can take a long time and many tokens.

## Optional add-ons

Nothing here runs until you ask. Say "show me the groundwork add-ons" to browse them.

| Add-on | What it does |
|---|---|
| `slack-report` | Sends work changes and test results to Slack |
| `handoff` | Saves what is done, what is left, and where to start next |
| `weekly-summary` | Summarizes a week's commits, PRs, and issues |
| `release-notes` | Turns a range of commits into user-facing release notes |
| `ux-journey` | Has a first-time user walk a whole journey on the running app and reports where they get stuck |
| `release-prep` | Prepares and verifies releases on a schedule, then asks for final approval |

Setup details for each are in the [add-on catalog](plugins/groundwork/catalog/addons.md).

<details>
<summary><b>All skills</b></summary>

| Skill | Description |
|---|---|
| `onboarding` | Initialize or update `GROUNDWORK.md` |
| `update` | After a plugin update, apply migrations and pick new features from the release notes |
| `addons` | Browse optional features and continue their setup or one-off use |
| `plan` | Break a large task into a parent issue and smaller step issues |
| `step` | Run a single step: implement, then loop through verify → review → fix until no confirmed 🔴/🟠 issues remain |
| `takeoff` | Rebase, push, and open the PR for a finished step |
| `landing`, `rejoin` | Clean up after a merge, or move a branch out of its worktree |
| `release`, `autoland` | Cut a release, and merge once CI passes |
| `review-and-fix`, `commit-push` | The quick workflow |
| `review` | Run the selected reviewers in parallel and combine their findings |
| `ux-review` | Usability review from chosen user personas, from the code or on the app |
| `ui-qa` | Launch the app to check UI behavior automated tests can't cover |
| `slack-report`, `handoff`, `weekly-summary`, `release-notes`, `release-prep`, `ux-journey` | Optional add-ons; see above |

</details>

## GROUNDWORK.md

The full specification is in [`plugins/groundwork/reference/config.md`](plugins/groundwork/reference/config.md). Keys are only ever added, never renamed or removed. When the structure must change, the schema version is bumped and onboarding migrates your file.

## License

MIT
