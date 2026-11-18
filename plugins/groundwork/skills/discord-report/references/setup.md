# Discord connection

Requirements: Python 3, Git, and a Discord bot that is a member of the server the user selected.

## Bot and permissions

Create an application and its bot in the [Discord Developer Portal](https://discord.com/developers/applications), or reuse the bot of the Discord channel plugin. Invite it to the server with an OAuth2 URL that has the `bot` scope and these permissions:

| Permission | Why |
|---|---|
| View Channels | Read the report channel and its threads |
| Send Messages | Post the starter message |
| Create Public Threads | Open a thread for each report |
| Send Messages in Threads | Post the report and answers |
| Manage Threads | Delete a waiting thread when its work finishes |
| Manage Channels | Create the report channel during setup |

Manage Channels is needed only for setup. The user can remove it afterwards. If the server overrides permissions per channel, give the bot the same permissions on the report channel.

## Token

The helper looks for the token in this order:

1. `~/.config/discord-report/token`, holding the token alone. Use this for Codex or without the Discord channel plugin.
2. `DISCORD_BOT_TOKEN=<token>` in `~/.claude/channels/discord/.env`, the file the Discord channel plugin writes. Unlike that plugin, the helper does not read the shell variable.

Both are machine-local files outside the repository. Use restrictive permissions, such as directory mode `700` and file mode `600`. Have the user enter the token locally. Never request it in chat, shell history, an issue, or a tracked file.

## Checks

`python3 <skill-directory>/post.py --check` calls `GET /users/@me` and `GET /users/@me/guilds`. It prints the bot name and its servers. Once `DISCORD_INFO.md` exists, it also prints the saved channel and whether its server matches `guild_id`. It never posts.

If the token is missing or rejected (`401`), explain which file to fix and stop. A `403 Missing Permissions` or `Missing Access` means the bot lacks a permission above, or cannot see the channel.

API references: [Get Current User Guilds](https://discord.com/developers/docs/resources/user#get-current-user-guilds), [Create Guild Channel](https://discord.com/developers/docs/resources/guild#create-guild-channel), [Create Message](https://discord.com/developers/docs/resources/message#create-message), [Start Thread from Message](https://discord.com/developers/docs/resources/channel#start-thread-from-message), [Delete Channel](https://discord.com/developers/docs/resources/channel#deleteclose-channel).
