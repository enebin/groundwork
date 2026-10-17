---
name: "release"
description: Cuts a release/<version> branch from the integration branch and opens a release PR into the production branch, with release notes and pre-release checks. Use for "release <version>" when `branches.strategy` is develop-release.
allowed-tools: Bash, Read, Grep, Glob, AskUserQuestion
argument-hint: <version, e.g. 1.4.0>
---

Collect what has merged into the integration branch since the last release, cut `release/<version>`, and open a PR into the production branch.

## 0. Read the config

Read `reference/config.md` under the plugin root (two directories above this skill's directory), then `GROUNDWORK.md` at the repository root as it says. Stop if the file is missing or a key this skill needs is missing.

`branches.strategy` must be `develop-release`. With `main-only` there is nothing to release from; tell the user and stop.

Talk to the user in `language.conversation`. Write the PR title and release notes in `language.artifacts`.

In plan mode, do not refuse. Inspect with read-only tools, write the concrete plan (version, release notes, checks, commands), and ask for approval. After approval, carry it out as planned.

If `docs.rules` and this skill disagree, follow `docs.rules`.

## 1. Preflight

1. **Version.** The argument is required and must match `^\d+\.\d+\.\d+$`. Otherwise ask the user to call `/groundwork:release <x.y.z>` and stop.
2. **GitHub CLI.** Run `gh auth status`. If it is not authenticated or lacks permission, stop and tell the user to run `gh auth login` themselves. Never run `gh auth login` or `gh auth switch`.
3. **Clean tree.** If `git status --porcelain` is not empty, tell the user and stop, so unrelated changes cannot ride along.
4. **Fetch.** `git fetch origin <branches.production> <branches.integration> --tags`.
5. **Anything to release?** If `git rev-list --count origin/<branches.production>..origin/<branches.integration>` is 0, say there is nothing to release and stop.
6. **Open release branches.** If `git branch -a --list '*release/*'` shows another release branch, tell the user and ask whether to continue.
7. **Duplicate version.** If a tag `v<version>` or `<version>`, or a branch `release/<version>`, already exists, tell the user and stop.

## 2. Collect changes

Use merged PRs as the source of the notes; commit prefixes are only a hint.

```bash
# When the last release PR merged into the production branch
gh pr list --state merged --base <branches.production> --search "release in:title" --limit 1 \
  --json mergedAt,title,number

# PRs merged into the integration branch since then
gh pr list --state merged --base <branches.integration> --search "merged:>=<last release mergedAt>" \
  --json number,title,body,mergedAt
```

If there is no earlier release PR, use every PR in `origin/<branches.production>..origin/<branches.integration>`.

Sort each PR by what it means to users:

- New capability → **New features**
- Fixes something users ran into → **Bug fixes**
- Refactors and performance work that users notice go in whichever fits better. Otherwise leave them out.
- Docs, chores, style, tests, CI, and build changes → leave out.

## 3. Release notes

```markdown
## <version>

### New features

- <what users can now do>

### Bug fixes

- <the problem users had, now fixed>
```

- Write from the user's point of view.
- Leave out implementation details, internal module names, file paths, and issue and PR numbers.
- Drop an empty section.
- Split one PR into several bullets when it delivers several user-facing changes.
- If `docs.rules` defines a release-note format, follow it instead.

## 4. Pre-release checks

Static checks only. Do not try to simulate production or run load tests; passing tests and builds are CI's job.

1. **Destructive migrations.** List migration files changed in `origin/<branches.production>..origin/<branches.integration>` (paths with `migration` or `migrate` in them, or the migration directory `docs.rules` names). Flag any that drop a table, column, constraint, or index; rename a table or column; change a column type; or add `NOT NULL` without a default. If `docs.rules` defines a migration policy such as expand-contract, check against it.
2. **Deploy configuration.** Flag changes to deploy and runtime configuration: CI/CD workflows, container and infrastructure files, and example environment files. A missing environment variable can break the release.
3. **Repository checks.** Apply the checks under `## Release checks` in `GROUNDWORK.md` and any release rules in `docs.rules`.

Print one line per check with ✅ or ⚠️ and, for ⚠️, the file and the pattern found.

## 5. Confirm

Show the version, the release notes, and the check results, and ask with AskUserQuestion:

- Proceed as is
- Edit the notes (the user rewrites them)
- Stop

If any check shows ⚠️, proceed only if the user explicitly chooses to. To change the version, the user calls the skill again; do not guess a new one.

## 6. Branch and push

```bash
git checkout -b release/<version> origin/<branches.integration>
git push -u origin release/<version>
```

## 7. Open the PR

```bash
gh pr create --base <branches.production> --head release/<version> \
  --title "Release <version>" --body "<notes from step 5>"
```

Show the PR URL and stop.

## Rules

- No `--no-verify`, force-push, or other destructive git commands.
- Never push to `branches.production` directly. It changes only through the PR.
- Check that no issue numbers, PR numbers, or internal module names leak into the notes.
- If `gh` or git fails, report the root cause and stop. Do not work around it or retry blindly.
