# codex

OpenAI Codex CLI. Reaches the GPT models the signed-in account allows.

Verified with: codex-cli 0.146.0, 2026-11-01.

## Detect

`codex --version` succeeds.

## Models

`codex debug models` prints the account's model catalog as JSON. Use the entries whose `visibility` is `list`; each has a `slug` (the id) and a `description`, so choose by description. A model outside this list, including the one in the user's own Codex config, may be rejected for the account.

## Run

From the repository root, with a timeout of at least 10 minutes:

```bash
codex exec -s read-only --ignore-user-config --ephemeral -m <model id> -o <output file> \
  "Read <prompt file> and follow it. Reply only with the findings and coverage limits, in the output format it gives."
```

- Output: the `-o` file, created with `mktemp`. Delete it after reading.
- Commands: read-only. The `read-only` sandbox blocks file writes at the operating-system level, so the model may run read-only commands such as `git log` and `git show`. Never use `workspace-write`, `danger-full-access`, or `--add-dir`, which makes a directory writable.
- `--ignore-user-config` keeps the user's MCP servers, default model, and other personal settings out of the run.
- Files it can read: any path the user can read, including the plugin root.

## Failures

| What happened | Recovery |
|---|---|
| `codex` not found | Install the Codex CLI, or remove the key from `review.external` |
| Signed out or not authorized | Run `codex login` |
| `model_not_found` or "not supported" | Pick a `list` model from `codex debug models` |
| Rate limit or timeout | Retry later |
| Network or sandbox error | Run the review where the CLI can reach OpenAI, for example with network allowed for this command |

The run failed when the exit code is non-zero, or when the output file is missing or empty. Error lines go to stderr.
