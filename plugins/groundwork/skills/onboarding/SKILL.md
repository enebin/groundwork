---
name: onboarding
description: Sets up groundwork for the current repository. Walks the user through language, issue tracker, workflow, branches, verification, architecture, and review as pre-packaged bundles with a recommended choice each time, then writes GROUNDWORK.md and the chosen rules into the repository docs. Use when starting a new project, adopting groundwork in an existing repository, or changing earlier choices.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, AskUserQuestion
argument-hint: "[--recommended]"
---

Set up groundwork for this repository. The main audience is someone starting a new project; an existing repository gets the same questions with recommendations taken from what is already there.

`reference/config.md` under the plugin root defines `GROUNDWORK.md`. The catalog under `catalog/` holds every bundle, its pros and cons, and the text to write when it is chosen. Read `reference/config.md` first. Read a catalog file when its step comes up, not all at the start: the catalog is long, and loading it all up front costs tokens on every later turn. The plugin root is two directories above this skill's directory.

Talk to the user in the language they are using. This skill writes nothing until the user approves the final preview. Plan mode: gather everything read-only, write the plan, and continue after approval.

## Asking

Every question follows these rules.

- Put the recommended option first, mark it "(Recommended)", and give one line on why it is recommended **for this repository**.
- Before each choice, show the step's bundles as one table with exactly these columns: `Bundle | Pros | Cons | Token cost`. The recommended bundle is the first row and is marked "(Recommended)". Each cell holds the bundle's single strongest point in about twelve words or fewer, not a list; give the full lists only when the user asks. A step whose choice does not change token use (such as branches) may drop the Token cost column. Token cost is the catalog's relative level (Low / Medium / High / Very high), compared within this step; say once that it is an estimate, not a measurement. Keep the rules inside a bundle folded; show them only when the user asks.
- Use `AskUserQuestion` when available, with the same three items (pros, cons, token cost) in each option's `preview`. It allows four options; when a step has more, show the full catalog table as text first, then offer the recommended option, the two most relevant alternatives, and let the user name any other bundle through "Other". Without `AskUserQuestion` (for example in Codex), ask in plain text with numbered options.
- Never invent a bundle, rule, or pro/con that the catalog does not contain.

## 1. Scan the repository

Read-only. Record what you find; it decides the recommendations.

- Files: build manifests (`Package.swift`, `*.xcodeproj`, `project.yml`, `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `build.gradle*`, ...), CI workflows, `AGENTS.md`, `CLAUDE.md`, an architecture document, a design reference.
- Git: remotes, branches (`develop`?), whether there are any commits.
- Existing agent setup: `.claude/skills`, `.claude/agents`, `.claude/commands`, `.agents/skills`, `.codex/`. Note each item that overlaps a groundwork skill or agent.
- Existing `GROUNDWORK.md`: if present, this is a re-run. Its values become the recommendations, and the user only changes what they want. If its `groundwork` version is older than `reference/config.md`, migrate it as part of this run and say what changed.

Tell the user in two or three lines what you found. For an empty repository, say plainly that it is empty and that the recommendations will come from the next answer.

## 2. What are you building?

Ask the user to describe the project in one or two sentences, including the language or framework if decided. Example answers: "An iOS habit tracker in SwiftUI", "A reservation web service with FastAPI and React", "A Swift chat UI library".

This is the only question without a recommended option, because it asks for a fact. For an existing repository, propose a summary from the scan and ask the user to confirm or correct it.

Derive `project.summary`, `project.stack`, and `project.kind` (`app`, `library`, `service`, `tool`) from the answer.

## 3. Show the whole route

Before the first choice, show every step at once with the recommendation already filled in for this repository:

| Step | Decides | Recommended |
|---|---|---|
| 1 | Language | conversation: <current> / artifacts: English |
| 2 | Issue tracker | <recommendation> |
| 3 | Workflow | <recommendation> |
| 4 | Branches | <recommendation> |
| 5 | Verification | <base> + <add-ons> |
| 6 | Architecture | <recommendation> |
| 7 | Review | <recommendation>, mode `normal` |
| 8 | Anything else | none |

Then offer two choices: "Decide one by one (Recommended)" and "Use all recommendations". Say this with them, in the user's language:

> "Use all recommendations" picks the recommended option at every step and jumps to the final review. Still, I suggest going through each step and thinking about it yourself. What you choose here becomes the way this repository works. You can change it later, but people rarely change something once it is set. The recommendations are guesses from what I could see, and I do not know your situation.

With `--recommended`, show the table and the warning, then go straight to step 8.

## 4. The steps

### Step 1 — Language

- Conversation language: the language the user is using now (Recommended).
- Artifact language (commits, issues, code comments, work logs): English (Recommended). Tell the user that the same content in English usually takes fewer tokens than in many other languages, and agents reread these artifacts on every task, so the saving adds up.

Reassure the user: this setting only affects stored artifacts. Conversation with the agent and every groundwork message stay in their language, and the product's own user-facing text is not affected.

### Step 2 — Issue tracker

Options: local files (Recommended for a new project: no setup, start now; can move to a real tracker later), GitHub Projects, Linear, Jira. For an existing repository whose skills or history show a tracker in use, recommend that tracker instead.

Then follow the "Setup" section of `catalog/trackers/<type>.md`: detect, ask its sub-questions (each with a recommendation), and verify access with one read-only call. Creating anything remote (a GitHub repository, a project, labels) is an outward action: confirm it separately right before doing it. When a permission is missing, tell the user the command to run themselves; never switch or log in accounts on their behalf.

### Step 3 — Workflow

Bundles from `catalog/workflows.md`. Recommended: `step-loop` for a new project; for an existing repository, the bundle matching the skills it already uses.

Then, unless the bundle skips it (see the catalog), ask the autoland follow-up: "Merge automatically once CI passes?" — No (Recommended), with the catalog's reason.

### Step 4 — Branches

- `develop-release` (Recommended for a new project): work lands on `develop`; releases go through `release/x.y.z` into `main`.
- `main-only`. Recommended instead when an existing repository has no `develop` branch.

Then the merge style: recommend what the repository's merged PRs already use; `squash` for a new project.

### Step 5 — Verification

Base bundle and add-ons from `catalog/verification.md`. Recommend the base the catalog marks for this kind of project, and pre-select each add-on whose "Recommended when" matches the scan and the step 2 answer.

Verification commands:

- Existing repository: show the detected commands as a table (purpose, command) with their sources (CI, rules doc, manifest). "Use as found (Recommended)" or "Edit". Mark them `verified: true` only after running each once successfully; if a command cannot run here, keep `verified: false` and say why.
- Empty repository: propose the stack's usual build and test commands, marked `verified: false`. When a command names a device, simulator, or runtime, pick one that exists on this machine (for example from `xcrun simctl list devices available`), preferring one available on the newest installed runtime so the command needs no OS pin. Explain that the first `plan` will propose a scaffold step that makes them pass.

Also confirm `ui_paths` (paths whose changes need UI tests with screenshots) and, when `design-fidelity` is on, `design_source`.

### Step 6 — Architecture

Bundles from `catalog/architecture/`, filtered to the project's stack. `minimal-structure` is part of every bundle and is not asked separately.

- An existing architecture document: "Follow the existing document (Recommended)". Name the bundle it resembles, if any, and do not overwrite it.
- Otherwise: the bundle the catalog marks for this stack (Recommended), the other stack-matching bundles, and `none`.

Show the comparison table first. When the user picks or asks about a bundle, show its flow, example, and failure modes.

### Step 7 — Review

Bundles from `catalog/review.md`. Recommend by `project.kind`: `app` for apps, `sdk` for libraries, `service` for backends and APIs without screens, `product` for products with screens plus sign-in, personal data, or several user roles (add `dx` when it also exposes a public API), `light` for tools (add `dx` for a command-line tool other people run). Drop `architecture` when step 6 chose `none`, and say why.

Ask only the follow-ups the chosen bundle triggers (see the catalog), each with a recommendation:

- Release QA, when the project has screens: off (Recommended) or on, from the Release QA section of `catalog/review.md`, in the same table. Warn plainly that it has very high token and time cost (10 to 20 minutes per screen per agent in testing). Only when on: the design source, if not set in step 5.
- `ux` or `dx` in the bundle, or release QA on: personas, each with a `kind` (`user` for `ux` and release QA, `developer` for `dx`). Recommend one persona per selected reviewer, drawn from the step 2 answer; the user can add more.
- Flight or quick workflow: review trigger.
- Mode: `normal` (Recommended), from the Modes section of `catalog/review.md`, shown in the same Bundle | Pros | Cons | Token cost table. Say that it can be overridden per run with `--mode`, so the default should fit everyday work.
- Skeptic policy: the bundle's default (Recommended). Mention that Skeptic Review is a separate plugin; if it is not installed, reviews report `SkepticReview: OFF`.

For an existing repository with its own reviewers or review rules, draft a `## Review focus: <key>` section for each chosen reviewer from them, show the drafts, and ask "Use the drafts (Recommended)" or "Edit".

### Step 8 — Anything else

Always ask, even after "Use all recommendations":

> Is there anything this repository should follow that has not come up? For example a commit message format, "ask before adding a third-party dependency", "never touch this folder", or something a reviewer must always check.

Options: "Nothing (Recommended) — you can add more any time by running onboarding again" and free text.

Place each item the user gives, and show where it goes:

| The item | Goes to |
|---|---|
| Changes an earlier choice | That config value |
| A working rule | The rules document (`docs.rules`) |
| A reviewer's standard | That reviewer's `## Review focus: <key>` |
| Something groundwork cannot do | Nowhere. Say plainly that it cannot be done, and suggest an alternative if there is one. Do not write a rule that nothing will enforce. |

## 5. Final review

Mandatory, also after "Use all recommendations". Show every file to create or change with what goes into it:

- `GROUNDWORK.md` — the full frontmatter and body.
- `docs.rules` (create `AGENTS.md` if absent) — the "Rules to write" block of each chosen verification bundle and add-on, and step 8 rules.
- `docs.architecture` (create `ARCHITECTURE.md` if absent) — the `minimal-structure` rules first, then the chosen bundle's "Contract to write" (none for `none`). When following an existing document, add only the `minimal-structure` block.
- `CLAUDE.md` — a one-line pointer to `AGENTS.md`, only if `CLAUDE.md` does not exist.
- `verification.ui_coverage` (`docs/ui-coverage.md`) — the ledger's header row only, when the project has screens. The implementing skills fill it as screens are built.
- Local tracker setup from `catalog/trackers/local.md` (a self-ignoring `.gitignore` inside the issue directory, so no tracked file changes), when the tracker is local.

Wrap every block groundwork writes into an existing document in `<!-- groundwork:begin <id> -->` and `<!-- groundwork:end <id> -->`, so a re-run replaces exactly that block and leaves the user's text alone. Never edit text outside these markers.

For an existing repository, list each repository-local skill, agent, or command that overlaps a groundwork one and ask separately whether to remove them: "Remove (Recommended) — two copies with the same name drift apart, and the repository copy wins over the plugin". Removing files is destructive: show the exact paths and get an explicit yes.

Write only after approval. Apply requested changes and show the preview again.

## 6. Finish

- Report what was written, in a short list.
- Say what to run next: `/groundwork:plan` for step-loop, design-first, or tdd-loop; `/groundwork:boarding <issue>` for flight; `/groundwork:review-and-fix` for quick; `/groundwork:review` for review-only.
- Offer to commit the changes. Commit only if the user says yes.
