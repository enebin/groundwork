---
name: release-notes
description: Draft user-facing release notes for an explicit Git revision range, with features, fixes, and compatibility changes. Use to explain a release without creating release branches, tags, pull requests, or deployments.
---

Read `reference/config.md` under the plugin root (two directories above this skill), the repository's `GROUNDWORK.md`, and its rules. Talk in `language.conversation`; write notes in `language.artifacts` unless requested otherwise. Follow a repository-specific release-note format when present.

## Pin the changes

Use the supplied base and target refs. Without them, inspect the repository's actual release tags or published-release metadata and propose the latest relevant released revision as base and `branches.integration` as target. Do not treat a prerelease or an unrelated component's tag as the previous stable release. Show the resolved range. If no trustworthy baseline exists, ask for the range; an explicitly requested first release may use all history to the target.

Resolve refs to immutable SHAs before collecting changes. Read commits, diffs, and available merged PRs for that range. Follow account routing before authenticated GitHub calls. Attribute a PR only when its changes belong to the pinned range; merge dates alone are insufficient. Keep unavailable remote evidence explicit and use local diffs where possible.

## Write the draft

Group changes into New features, Bug fixes, and Breaking changes or Upgrade notes as applicable. Explain what users can now do, which problems were fixed, and any action they must take. Drop empty sections. Pure internal refactoring, test, CI, and formatting changes normally stay out unless they change installation, support, or another user-visible contract. Do not miss a compatibility break merely because the commit is labeled a fix.

Keep evidence separately from the user-facing notes: base and target SHAs, relevant commits or PRs, unavailable evidence, and any uncertainty. Avoid internal file paths, module names, and issue numbers in user-facing prose unless the repository's release-note format requires them.

Return the draft in the conversation, or save it when the user or a calling skill supplied a destination. The `release-prep` caller always supplies a local draft destination. Never replace an existing changelog or note without authorization, and never publish, tag, push, or create a PR as part of drafting notes.
