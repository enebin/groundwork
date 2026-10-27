# Slack connection

Requirements: Python 3, Git, and a Slack app bot installed in the workspace the user selected. GitHub CLI is optional for PR links and status; follow the repository's account-routing rules before using it.

Create or reuse a Slack app in that workspace. The bot needs `chat:write`, `channels:manage` to create repository channels, and `channels:write.invites` to invite the owner. `chat:write.public` allows posting to existing public channels without joining first; otherwise invite the bot to the chosen channel. Private channels require an invitation and their corresponding conversation permissions. Use a public repository channel by default; do not silently change a workspace's privacy policy.

Keep the bot token in `~/.config/slack-report/token` and the owner's member ID in `~/.config/slack-report/user_id`. These are machine-local files outside the repository; use restrictive permissions such as directory mode `700` and file mode `600`. Have the user enter the token locally; never request it in chat, shell history, an issue, or a tracked settings file. The member ID is optional; without it the helper warns that the user must join a new channel manually.

Run `python3 <skill-directory>/post.py --check`. It reads the configured token internally and calls `auth.test`, printing only `team`, `team_id`, and `user`. Confirm that workspace with the user during setup, then store the confirmed `team_id` as `workspace_id` in `SLACK_INFO.md`. Every post checks the match before creating or updating anything. If credentials are missing or rejected, explain the missing prerequisite and stop without changing connections.

If the workspace uses a custom channel name, save it in `SLACK_INFO.md`. Channel creation and invitations are part of the reporting setup the user chooses. No message is sent by `--check` or the hook installer.

API references: [auth.test](https://docs.slack.dev/reference/methods/auth.test), [chat.postMessage](https://docs.slack.dev/reference/methods/chat.postMessage), [conversations.create](https://docs.slack.dev/reference/methods/conversations.create), [conversations.invite](https://docs.slack.dev/reference/methods/conversations.invite).
