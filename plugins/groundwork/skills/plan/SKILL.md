---
name: "plan"
description: Splits a job that does not fit in one PR into steps, and after approval creates a parent issue plus one sub-issue per step in the repository's tracker. Use for "plan this job", "split this into issues", or when another skill hands off a large job.
allowed-tools: Bash, Read, Grep, Glob, AskUserQuestion
argument-hint: <requirement | issue id> [--context <text or file>]
---

Turn a job into a parent issue and step sub-issues. This skill **only plans and creates issues.** Running a step is the job of `step`.

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

`workflow.bundle` must be `step-loop`, `design-first`, or `tdd-loop`. Otherwise stop and point the user to the skill that serves their bundle:

- `flight`: `/groundwork:boarding` and the stages after it
- `quick`: `/groundwork:review-and-fix`, then `/groundwork:commit-push`
- `review-only`: `/groundwork:review`

Talk to the user in `language.conversation`. Write issue text in `language.artifacts`.

Every tracker action below is an operation from `reference/config.md` "Tracker operations". Perform it as `catalog/trackers/<tracker.type>.md` says. If the tracker or its CLI is not authorized, stop and tell the user the command to run. Do not log in or switch accounts yourself.

If `docs.rules` and this skill disagree, follow `docs.rules`.

## 1. Gather context

- Read `docs.rules`, `docs.architecture` (when set) and the documents it links that the job touches, the build manifest, and the code the job touches.
- If the argument is an issue id, `read` it with its comments and use it as the parent issue instead of creating a new one.
- If `--context` is given, it comes from the caller. Carry its per-step instructions into the matching sub-issue's "Implementation notes" as written. Do not interpret or expand them.

## 2. Split

- If the job fits in one PR, make one issue with no parent and skip the sub-issues.
- Each step must build, pass `verification.commands`, and be reviewable on its own.
- Size a step so one review loop can cover it: one PR a reviewer can read in one sitting.
- When `docs.architecture` is set and the job changes structure, the first step updates `docs.architecture` and its sub-documents.
- `design-first`: the first step is always a design step that changes `docs.architecture` or adds a design note. Its done criteria include explicit user approval of the document. Every later step depends on it.
- If any `verification.commands` entry still has `verified: false`, the repository has no working code yet. Propose a first "scaffold" step whose done criteria are: every `verification.commands` entry passes, and each is flipped to `verified: true` in `GROUNDWORK.md`. When the repository has no commits, the scaffold step also makes the first commit on `branches.production` and creates `branches.integration` from it, because no work branch can start before that. Under `design-first` it comes right after the design step.
- Order steps by dependency and write each step's dependencies down.
- Do not add steps for work nobody asked for. Ask when the requirement leaves a choice open.
- When the user moves something to a later scope while answering, set it aside as a **needs-planning issue**. Only record what the user moved out. Do not add your own ideas.

## 3. Preview and get approval

Show the user the parent issue and every step: title, goal, scope (in / out), done criteria, dependencies. List the needs-planning issues too, with title and start condition. Explain the split in one or two sentences. **Create nothing before the user approves.** Apply requested changes and show the preview again.

## 4. Create the issues

1. `create` the parent issue, unless one was given.
2. `create` each sub-issue in step order with the parent, titled `<Parent short name>: <step>`. Do not number titles; the parent's Steps list holds the order, so adding or dropping a step does not rename the others.
3. `link` each sub-issue to the parent if `create` did not already do it.
4. `create` each needs-planning issue with the label `needs planning` and no parent. Do not `link` it: sub-issues are the steps that finish the parent, so a parked item would keep the parent open forever. Point back with `Split from <parent id>` in its body.
5. Report the parent link, the sub-issue ids in order, and the needs-planning issue ids.

### Parent issue body

```markdown
## Goal
<what the finished job delivers, in two or three sentences>

## Context
<why now; links to the relevant sections of docs.rules / docs.architecture>

## Steps
<ordered list; sub-issues track progress>

## Decisions
<empty at first; append decisions as they are made>
```

### Sub-issue body

```markdown
## Goal
<one or two sentences>

## Scope
- In: ...
- Out: ...

## Depends on
<issue ids, or "none">

## Implementation notes
<caller-provided instructions, or "none">

## Done when
- [ ] Verification commands in GROUNDWORK.md pass
- [ ] Review leaves no confirmed 🔴/🟠
- [ ] <step-specific criteria>
```

A design step replaces the first two boxes with `- [ ] Document review leaves no confirmed 🔴/🟠` and `- [ ] User approved the document`.

### Needs-planning issue body

When its start condition is met, run `/groundwork:plan <issue id>` on it.

```markdown
Split from <parent id>

## What
<the work, in one or two sentences>

## Why not now
<the reason the user gave>

## Start when
<the condition that makes it worth planning>

## Decisions so far
<answers already given during planning, or "none">
```
