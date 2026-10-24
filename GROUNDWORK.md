---
groundwork: 1
language:
  conversation: ko
  artifacts: en
project:
  summary: "Dogfood groundwork while developing the groundwork plugin."
  stack: [markdown, bash, json]
  kind: tool
docs:
  rules: AGENTS.md
  architecture: ARCHITECTURE.md
tracker:
  type: github
  owner: enebin
  repo: groundwork
  project: 10
workflow:
  bundle: step-loop
  autoland: false
  worktree: true
branches:
  strategy: develop-release
  integration: develop
  production: main
  work_prefix: step
  merge: squash
verification:
  base: evidence
  addons: []
  commands:
    - name: Shell syntax
      run: bash -n plugins/groundwork/hooks/check-update.sh
      verified: true
    - name: JSON syntax
      run: |
        python3 - <<'PY'
        import json
        from pathlib import Path
        paths = sorted(path for path in Path('.').rglob('*.json') if not any(part in {'.git', '.groundwork'} for part in path.parts))
        for path in paths:
            with path.open() as source:
                json.load(source)
        print(f'Validated {len(paths)} JSON files')
        PY
      verified: true
  ui_paths: []
  ui_tests:
    targeted: null
    full: null
  design_source: null
  ui_coverage: null
architecture:
  bundle: none
review:
  bundle: light
  reviewers: [code-quality, dx]
  release_qa: false
  skeptic: blocking
  trigger: per-round
  personas:
    - name: Groundwork user
      goal: "Install groundwork, configure a repository, and complete a planned change through a pull request."
      kind: developer
qa:
  bundle: manual
ux:
  bundle: manual
  method: code
mode: normal
---

## Review focus: code-quality

- Check configuration reads, migrations, workflow triggers, and screen-check triggers against `plugins/groundwork/reference/config.md`.
- Verify tracker state changes and worktree paths follow configured values without repeating remote side effects.
- Require meaningful behavior tests for changed executable hooks.

## Review focus: dx

- Trace installation, onboarding, planning, implementation, and pull-request creation for the Groundwork user in both supported clients.
- Keep the English and Korean READMEs, skill help, plugin manifests, and configuration examples consistent with the actual behavior.
- Errors must name the missing prerequisite and a recovery action; never silently guess required configuration.

## Notes

- GitHub closes issues on merge: no — integration branch is not the default branch.
- Projects Item closed → Done: on (user-confirmed). Skills still close issues explicitly after a merge into develop.
- Integration branch develop was initialized from main for the develop-release workflow.
- No build pipeline, behavioral test suite, or CI workflow was found. The verified commands check syntax only.
- First scaffold task: add meaningful automated behavior checks for executable hooks and document the test command in verification.commands. Do not treat syntax checks as behavior-test coverage.
- Screen checks are not applicable: this plugin has no application screens. qa.bundle and ux.bundle are manual, and review.release_qa is the false compatibility mirror of qa.bundle.
- Architecture none adds no application-specific layering. ARCHITECTURE.md contains only the mandatory minimal-structure rules.
