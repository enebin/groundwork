---
groundwork: 1

language:
  conversation: ko
  artifacts: en

project:
  summary: "Temporary config for testing groundwork's own push and cleanup skills"
  stack: [markdown]
  kind: tool

docs:
  rules: README.md
  architecture: README.md

tracker:
  type: local
  path: .groundwork/issues
  shared: false

workflow:
  bundle: step-loop
  autoland: false
  worktree: true

branches:
  strategy: main-only
  integration: gwtest/develop
  production: main
  work_prefix: gwtest/step
  merge: squash

verification:
  base: evidence
  addons: []
  commands:
    - name: Whitespace
      run: "git diff --check gwtest/develop"
      verified: true
  ui_paths: []
  ui_tests:
    targeted: "true"
    full: "true"
  design_source: null
  ui_coverage: null

architecture:
  bundle: none

review:
  bundle: light
  reviewers: [code-quality]
  release_qa: false
  skeptic: blocking
  trigger: per-round
  personas: []

mode: eco
---

Temporary. Exists only on gwtest/ branches and is deleted with them.
