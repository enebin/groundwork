---
name: onboarding
description: Sets up groundwork for the current repository. Walks the user through language, issue tracker, workflow, deployment strategy, architecture, review, and screen checks (UX and QA) as pre-packaged bundles with a recommended choice each time, then writes GROUNDWORK.md and the chosen rules into the repository docs. Use when starting a new project, adopting groundwork in an existing repository, or changing earlier choices.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, AskUserQuestion
argument-hint: "[--recommended]"
---

Set up groundwork for this repository. The main audience is someone starting a new project; an existing repository gets the same questions with recommendations taken from what is already there.

`reference/config.md` under the plugin root defines `GROUNDWORK.md`. The catalog under `catalog/` holds every bundle, its pros and cons, and the text to write when it is chosen. Read `reference/config.md` first. Read a catalog file when its step comes up, not all at the start: the catalog is long, and loading it all up front costs tokens on every later turn. The plugin root is two directories above this skill's directory.

Talk to the user in the language they are using. This skill writes nothing until the user approves the final preview. Plan mode: gather everything read-only, write the plan, and continue after approval.

## Asking

Every question follows these rules.

- Put the recommended option first, mark it "(Recommended)", and give one line on why it is recommended **for this repository**.
- Before each choice, show the step's bundles as one table with exactly these columns: `Bundle | Pros | Cons | Token cost`. The recommended bundle is the first row and is marked "(Recommended)". Each cell holds the bundle's single strongest point in about twelve words or fewer, not a list; give the full lists only when the user asks. A step whose choice does not change token use (such as deployment strategy) may drop the Token cost column. Token cost is the catalog's relative level (Low / Medium / High / Very high), compared within this step; say once that it is an estimate, not a measurement. Keep the rules inside a bundle folded; show them only when the user asks.
- Use `AskUserQuestion` when available, with the same three items (pros, cons, token cost) in each option's `preview`. It allows four options; when a step has more, show the full catalog table as text first, then offer the recommended option, the two most relevant alternatives, and let the user name any other bundle through "Other". In Codex, use `request_user_input` when this turn lists it (Plan mode, or Default mode with the `default_mode_request_user_input` feature on). It takes two or three options per question and adds "Other" by itself: offer the recommended option and the one or two most relevant others, with the pros, cons, and token cost in each option's description, and let the user name any other bundle through "Other". Without either tool, show the table as information, then ask one plain-text question that names the recommendation and asks the user to accept it or name another bundle from the table. Codex's Default mode forbids writing a multiple-choice question as a message, so do not format the choices as a numbered list. Approvals are not choices: in Codex, ask to create anything remote, to remove files, or to write the final preview as one plain-text question, never with `request_user_input`.
- Never invent a bundle, rule, or pro/con that the catalog does not contain.
- Group related, independent questions in one interaction, up to the question tool's supported limit; with plain text, ask them together. Select a bundle first when it determines which follow-ups apply, then collect only those follow-ups as a group. Do not ask again for facts the user has already supplied. Keep approval questions separate from preference questions.
- Show each question once. When using a question tool, put comparisons and shared context in the preceding message, and the question and answer options in the tool only. Do not repeat them in commentary or a final message while awaiting the answer. After an answer, briefly acknowledge the choices and move to the next unanswered group; do not send a separate recap-only turn.

## 1. Scan the repository

Read-only. Record what you find; it decides the recommendations.

- Files: build manifests (`Package.swift`, `*.xcodeproj`, `project.yml`, `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `build.gradle*`, ...), CI workflows, `AGENTS.md`, `CLAUDE.md`, an architecture document, a design reference.
- Git: remotes, branches (`develop`?), whether there are any commits.
- Existing agent setup: `.claude/skills`, `.claude/agents`, `.claude/commands`, `.agents/skills`, `.codex/`. Note each item that overlaps a groundwork skill or agent.
- Existing `GROUNDWORK.md`: if present, this is a re-run. If the user only wants what a newer plugin version added, suggest `/groundwork:update` instead: it asks only about the changes. Its values become the recommendations, and the user only changes what they want. If its `groundwork` version is older than `reference/config.md`, migrate it as part of this run and say what changed. A `workflow.bundle: flight` becomes `step-loop` with `workflow.worktree: true`, which keeps one worktree per issue; say so, and set `review.trigger` to `per-round`, as every step workflow uses.

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
| 4 | Deployment strategy | <recommendation> |
| 5 | Architecture | <recommendation> |
| 6 | Review | <recommendation> |
| 7 | Screen checks (UX, QA) | <recommendation, or not applicable> |
| 8 | Anything else | none |

Below the route, show the overall effort setting: `eco / normal (Recommended) / sport`. Explain it as one control for implementation verification, review, and screen checks together, like a reasoning-effort setting, with `--mode` available per run. It does not select a model. For screen checks it is the scope: eco and normal check only the screens a change may affect, and sport checks every screen. Reuse an existing `mode` on re-runs. Explain the trade-offs from Modes in `reference/config.md`; offer a different default without making it a ninth numbered step.

Tests are always part of implementation. Tell the user that build/test commands and applicable checks will be detected automatically and included in the final preview.

Then offer two choices: "Decide one by one (Recommended)" and "Use all recommendations". Say this with them, in the user's language:

> "Use all recommendations" picks the recommended option at every step and jumps to the final review. Still, I suggest going through each step and thinking about it yourself. What you choose here becomes the way this repository works. You can change it later, but people rarely change something once it is set. The recommendations are guesses from what I could see, and I do not know your situation.

With `--recommended`, show the table and the warning, apply the recommendations (including the screen-check compatibility mappings and overall mode), then go straight to step 8. In either recommendation shortcut, still perform automatic implementation setup and collect any missing launch, design-source, or persona facts required by the selected policies before the final preview; never invent them.

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

After the workflow choice, ask its applicable autoland and worktree follow-ups together in one interaction (see the catalog). Autoland: "Merge automatically once CI passes?" — No (Recommended), with the catalog's reason. Worktree, for `step-loop`, `design-first`, and `tdd-loop`: "Work on each issue in its own worktree?" — Yes (Recommended), with the catalog's reason. Skip follow-ups the chosen bundle does not use.

### Step 4 — Deployment strategy

- `develop-release` (Recommended for a new project): work lands on `develop`; releases go through `release/x.y.z` into `main`.
- `main-only`. Recommended instead when an existing repository has no `develop` branch.

Ask the deployment strategy and merge style together in one interaction. For the merge style, recommend what the repository's merged PRs already use; `squash` for a new project.

### Step 5 — Architecture

Bundles from `catalog/architecture/`, filtered to the project's stack. `minimal-structure` is part of every bundle and is not asked separately.

- An existing architecture document: "Follow the existing document (Recommended)". Name the bundle it resembles, if any, and do not overwrite it.
- Otherwise: the bundle the catalog marks for this stack (Recommended), the other stack-matching bundles, and `none`.

Show the comparison table first. When the user picks or asks about a bundle, show its flow, example, and failure modes.

### Step 6 — Review

Bundles from `catalog/review.md`. Recommend by `project.kind`: `app` for apps, `sdk` for libraries, `service` for backends and APIs without screens, `product` for products with screens plus sign-in, personal data, or several user roles (add `dx` when it also exposes a public API), `light` for tools (add `dx` for a command-line tool other people run). Drop `architecture` when step 5 chose `none`, and say why.

Ask only the follow-ups the chosen bundle triggers (see the catalog), each with a recommendation:

- `dx` in the bundle: developer personas (`kind: developer`). Recommend one, drawn from the step 2 answer; the user can add more. End-user personas come in step 7.
- Quick workflow: review trigger.

Do not ask the Skeptic policy. Write the bundle's default, or keep an existing `review.skeptic` on re-runs, and show it in the final preview. Mention that Skeptic Review is a separate plugin; if it is not installed, reviews report `SkepticReview: OFF`.

For an existing repository with its own reviewers or review rules, draft a `## Review focus: <key>` section for each chosen reviewer from them, show the drafts, and ask "Use the drafts (Recommended)" or "Edit".

### Step 7 — Screen checks

Read `catalog/screen-checks.md`. For projects without screens, show not applicable and write the catalog's defaults without asking an irrelevant question.

First show the cost guidance: checks on the running app can take long and use many tokens. Then show the frequency table and the UX method table, and ask in one interaction:

- UX frequency: every PR (`continuous`, Recommended), before release only (`release`), or manual.
- UX method: from the code (`code`, Recommended) or on the simulator or browser (`app`).
- QA frequency: manual (Recommended), before release only, or every PR.

Do not ask a separate scope question; scope follows the overall mode shown with the route. Existing `ux` and `qa` values are the recommendations on re-runs. When either mapping is absent, migrate it as Screen checks compatibility in `reference/config.md` specifies: remove `ux` from `review.reviewers` and show the mapping in the final preview. When the old file ran UX both from the code and on the running app, ask the UX method even in a recommendation shortcut, and name the on-app check that stops if the user keeps `code`.

Collect the catalog's applicable end-user-persona, launch, and design-source follow-ups. Keep these separate from code review. Set `review.release_qa` to the compatibility mirror, not as a second choice.

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

## Automatic implementation setup

Do this without a verification-bundle question. Read `reference/implementation.md` and detect the implementation settings it describes. Tests are mandatory in every workflow and mode.

Verification commands:

- Existing repository: detect build and test commands from CI, rules, and manifests, and show their sources in the final preview. Mark a command `verified: true` only after it runs successfully; otherwise keep false and explain why.
- Empty repository: propose the stack's usual build/test commands as `verified: false`. For a command naming a device or runtime, use one actually available on this machine, preferring the newest installed runtime. The first scaffold step must make these commands pass.
- Detect `verification.ui_paths`, targeted/full UI commands, and applicable add-ons. Retain existing settings on re-runs. Missing required commands remain an explicit scaffold task, not evidence of a pass.
- If design-fidelity applies, collect a readable design source even when QA is manual. Keep it disabled if the source is unavailable and mark exact design matching unverified. Never silently remove a previously required design check; report the missing source as blocked and show it in the final preview.
- Preserve legacy `verification.base` values and supplemental rules on re-runs. The default implementation block is written regardless of that value. Explain this rule upgrade in the preview.

## 5. Final review

Mandatory, also after "Use all recommendations". Show a summary the user can read in a minute, not raw file contents:

- One table of every choice: the step, what was chosen, and one line on what it means day to day. Include values the user did not pick directly, such as the overall `mode` and the Skeptic policy.
- The detected verification commands, each with its source and whether it ran, plus anything blocked or unverified.
- Each file to create or change, with one line on what it will hold. Name each rule block by its purpose, not its text.
- Everything the steps above say to show in the final preview, such as migrations and replaced blocks.

Show a file's full contents only when the user asks.

Files to write:

- `GROUNDWORK.md` — the full frontmatter and body, with `plugin_version` set to the installed plugin version (`.claude-plugin/plugin.json` under the plugin root), including automatic implementation settings, the `ux` and `qa` screen checks, and the overall `mode`.
- `docs.rules` (create `AGENTS.md` if absent) — the mandatory block from `reference/implementation.md`, supplemental CI/test-first/add-on rules, and step 8 rules. For an existing managed evidence/basic block, show its replacement with the mandatory implementation block so contradictory run policies do not remain. Preserve CI gates and test-first requirements. Do not duplicate the old evidence block inside a new supplemental block.
- `docs.architecture` (create `ARCHITECTURE.md` if absent) — the `minimal-structure` rules first, then the chosen bundle's "Contract to write" (none for `none`). When following an existing document, add only the `minimal-structure` block.
- `CLAUDE.md` — a one-line pointer to `AGENTS.md`, only if `CLAUDE.md` does not exist.
- `verification.ui_coverage` (`docs/ui-coverage.md`) — the ledger's header row only, when the project has screens. The implementing skills fill it as screens are built.
- Local tracker setup from `catalog/trackers/local.md` (a self-ignoring `.gitignore` inside the issue directory, so no tracked file changes), when the tracker is local.

Wrap every block groundwork writes into an existing document in `<!-- groundwork:begin <id> -->` and `<!-- groundwork:end <id> -->`, so a re-run replaces exactly that block and leaves the user's text alone. Never edit text outside these markers.

For an existing repository, list each repository-local skill, agent, or command that overlaps a groundwork one and ask separately whether to remove them: "Remove (Recommended) — two copies with the same name drift apart, and the repository copy wins over the plugin". Removing files is destructive: show the exact paths and get an explicit yes.

Write only after approval. Apply requested changes and show the preview again.

## 6. Finish

- When every approved file was written, open the message with this banner in a `text` code block, copied exactly, so the end of setup is easy to spot. If a write failed or was declined, skip the banner, name each file that is missing, and say to run onboarding again.

  ```text
  ▄▀▀▀▀ █▀▀▀▀ ▀▀█▀▀ █   █ █▀▀▀▄
  ▀▄▄▄  █▄▄▄    █   █   █ █▄▄▄▀
      █ █       █   █   █ █
  ▀▀▀▀  ▀▀▀▀▀   ▀    ▀▀▀  ▀

  █▀▀▀▄ ▄▀▀▀▄ █▄  █ █▀▀▀▀ █
  █   █ █   █ █ ▀▄█ █▄▄▄  █
  █   █ █   █ █   █ █     ▀
  ▀▀▀▀   ▀▀▀  ▀   ▀ ▀▀▀▀▀ ▀
  ```

- Report what was written, in a short list.
- Say what to run next: `/groundwork:plan` for step-loop, design-first, or tdd-loop; `/groundwork:review-and-fix` for quick; `/groundwork:review` for review-only.
- Offer to commit the changes. Commit only if the user says yes.
- After successful setup, read `catalog/addons.md` and show its optional list under a heading equivalent to "You might also find these useful" in `language.conversation`. Include what each feature does and when it is useful. Keep this outside the eight numbered steps and the final configuration approval. Always allow the user to finish here and return with `/groundwork:addons`; accepting all recommendations never enables an add-on. Skeptic Review is part of the base review setup, not an entry in this list. When the user selects an item, follow `skills/addons/SKILL.md` with that selection instead of asking them to choose it again.
