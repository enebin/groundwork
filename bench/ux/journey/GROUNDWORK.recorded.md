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
  personas:
    - name: "Studio team lead"
      goal: "Set up a shared space for a small team, then add the first project and teammates."
      kind: user
qa:
  bundle: manual
ux:
  bundle: manual
  method: code
  journey: manual
mode: normal
---

## UI QA notes

- Launch: Node 18 or later, no dependencies. `PORT=<port> DATA_DIR=<data> PUBLIC_URL=http://<host>:<port> npm start`. Give each session its own port, `DATA_DIR`, and host name (for example `s1.localhost`), because cookies are shared across ports.
- Inbox: `http://<host>:<port>/dev/inbox?to=<address>` shows only that address's mail.
- Reset: `DATA_DIR=<data> npm run reset`. The server rereads data on every request.
- Checkpoint: `DATA_DIR=<data> npm run checkpoint:save -- <name>`; to restore into another session, copy `<data>/checkpoints/<name>.json` into the new session's `DATA_DIR/checkpoints/` and run `checkpoint:restore`. Sign the new browser context in with `/dev/login?email=<address>` as setup; never show this route to participants.
- Success checks: read `<data>/db.json`.

## Journey: New workspace
- Persona: Studio team lead
- Devices: desktop 1440×900
- Start: http://<host>:<port>/ — signed out, new browser context, empty data
- Precondition: none
- Scenario: You run a five-person design studio. A friend said Taskfold helps small teams share their work. Find out what it does, create an account, and set up a space for your team.
- Test access: Use the address journey-<run>@example.test. Your inbox is at http://<host>:<port>/dev/inbox?to=journey-<run>@example.test.
- Reset: DATA_DIR=<data> npm run reset, plus a new browser context
- Milestones:
  1. Understands what the product does and finds where to sign up
  2. Creates an account
  3. Confirms the email address
  4. Signs in and creates and names an organization
- Success: db.json holds an organization whose owner is the session's address.
- Code map: server.js landing → signupForm, /signup → /verify → signinForm, /signin → orgForm, /onboarding/org → dashboard

## Journey: First project
- Continues from: New workspace
- Start: the dashboard, signed in
- Scenario: Yesterday you created an account and set up a space for your studio. Now set up the first project for a client, so the team can start using it.
- Milestones:
  1. Finds where to start a new project
  2. Creates and names it, and sees it in the team's space
- Success: The organization has exactly one project with a non-empty name.
- Code map: server.js dashboard (⋯ menu) → projectForm, /app/projects/new

## Journey: Invite a teammate
- Continues from: New workspace
- Start: the dashboard, signed in
- Scenario: Yesterday you set up your studio's space. Your colleague Sam should be able to work in it with you. Get Sam added.
- Test access: Sam's address is sam-<run>@example.test. You cannot read Sam's email.
- Milestones:
  1. Finds where people are added
  2. Sends Sam an invitation
  3. Knows whether the invitation went out
- Success: db.json has an unaccepted invitation for Sam's address in the owner's organization.
- Code map: server.js dashboard → members → inviteForm, /app/invite

## Notes

- No automated UI tests yet.
