# copilot

GitHub Copilot CLI. Reaches models from several vendors (Claude, GPT, Gemini, Grok, and others) through one GitHub sign-in.

Verified with: GitHub Copilot CLI 1.0.109, 2026-11-12.

## Detect

`copilot --version` succeeds.

## Models

`copilot help config` lists the model ids under `model:`, one quoted id per line. The list has ids only, no descriptions, so choose by name: a higher version number is newer, and `flash`, `mini`, `fast`, and `haiku` mark smaller, faster models.

## Run

From the repository root, with a timeout of at least 10 minutes:

```bash
copilot -p "Read <prompt file> and follow it. Reply only in the output format it gives, plus any coverage limits." \
  --model <model id> -s --available-tools view grep glob --add-dir <plugin root>
```

- Output: stdout. It may start with a line announcing what it will read; drop anything before the first result in the prompt's output format, coverage limit, or "No findings".
- Commands: none. `--available-tools` hides every tool except the read-only `view`, `grep`, and `glob`, including shell, file writes, web access, and MCP servers. Do not add tools; even a git-only shell allowance is not read-only, because options such as `git diff --output=<file>` write files.
- Files it can read: the repository, the system temporary directory, and the plugin root (`--add-dir`).

## Failures

| What happened | Recovery |
|---|---|
| `copilot` not found | Install the GitHub Copilot CLI, or remove the key from `review.external` |
| Signed out or not authorized | Run `copilot login` |
| Unknown model | Pick an id from `copilot help config` |
| Rate limit or timeout | Retry later |
| Network or sandbox error | Run the review where the CLI can reach GitHub, for example with network allowed for this command |

A non-zero exit code means the run failed.
