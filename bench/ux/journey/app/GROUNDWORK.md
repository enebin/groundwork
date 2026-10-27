---
groundwork: 1
language:
  conversation: en
  artifacts: en
project:
  summary: "Taskfold: a web app where small teams share projects and tasks"
  stack: [javascript, node, web]
  kind: app
docs:
  rules: AGENTS.md
  architecture: ARCHITECTURE.md
tracker:
  type: local
  path: .groundwork/issues
  shared: false
  keep: true
workflow:
  bundle: quick
  autoland: false
  worktree: false
branches:
  strategy: main-only
  integration: main
  production: main
  work_prefix: step
  merge: squash
verification:
  base: evidence
  addons: []
  commands:
    - name: Start
      run: "node --check server.js"
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
  reviewers: [code-quality]
  release_qa: false
  skeptic: blocking
  trigger: on-request
  personas: []
qa:
  bundle: manual
ux:
  bundle: manual
  method: code
mode: normal
---

## Notes

- No automated UI tests yet.
