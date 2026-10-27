# Taskfold

Shared tasks for small teams of 2 to 20: studios, agencies, and small startups. A team signs up, creates an organization, invites its members, and keeps its projects in one place.

## Running locally

Requires Node 18 or later. There are no dependencies.

```bash
PORT=4310 DATA_DIR=./data npm start
```

Data lives in `DATA_DIR/db.json`. Each server needs its own `DATA_DIR`. Set `PUBLIC_URL` when the app is reached at another address, so links in emails point there.

- `npm run reset` deletes all data.
- `npm run checkpoint:save -- <name>` and `npm run checkpoint:restore -- <name>` copy the data file to and from `DATA_DIR/checkpoints/`. The server reads the file on every request, so a restore takes effect at once.

## Development helpers

These routes exist only for local testing:

- `/dev/inbox` shows every email the app sent. `/dev/inbox?to=<address>` shows only one recipient's messages.
- `/dev/login?email=<address>` signs in as an existing user without a password.
