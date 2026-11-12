#!/usr/bin/env node
const { spawnSync } = require("node:child_process");
const { parseArgs } = require("node:util");

const MARKETPLACE = "enebin/groundwork";
const PLUGIN = "groundwork@groundwork";

const CLIENTS = [
  {
    name: "Claude Code",
    bin: "claude",
    install: [
      ["plugin", "marketplace", "add", MARKETPLACE],
      ["plugin", "install", PLUGIN],
    ],
    update: [
      ["plugin", "marketplace", "update", "groundwork"],
      ["plugin", "update", PLUGIN],
    ],
    list: ["plugin", "list", "--json"],
    installedIds: (list) => list.map((plugin) => plugin.id),
    after: "Restart Claude Code to load it.",
  },
  {
    name: "Codex",
    bin: "codex",
    install: [
      ["plugin", "marketplace", "add", MARKETPLACE],
      ["plugin", "add", PLUGIN],
    ],
    // Codex has no plugin update command; re-adding installs the version in the refreshed marketplace.
    update: [
      ["plugin", "marketplace", "upgrade", "groundwork"],
      ["plugin", "add", PLUGIN],
    ],
    // Scoped to one marketplace so an unrelated broken marketplace does not fail the listing.
    list: ["plugin", "list", "-m", "groundwork", "--json"],
    installedIds: (list) => list.installed.map((plugin) => plugin.pluginId),
    after: "Start a new Codex session to load it.",
  },
];

const USAGE = `Usage: npx @enebin/groundwork@latest [install|update] [--target claude|codex]

  install   Add the groundwork plugin to Claude Code and Codex (default)
  update    Update the groundwork plugin where it is installed
  --target  Only use this client; by default every client found on PATH is used

Example: npx @enebin/groundwork@latest update --target codex`;

function isInstalled(bin) {
  const result = spawnSync(bin, ["--version"], { stdio: "ignore", shell: process.platform === "win32" });
  return !result.error && result.status === 0;
}

function hasGroundwork(client) {
  const result = spawnSync(client.bin, client.list, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "inherit"],
    shell: process.platform === "win32",
  });
  if (result.error || result.status !== 0) return null;
  try {
    return client.installedIds(JSON.parse(result.stdout)).includes(PLUGIN);
  } catch {
    return null;
  }
}

function run(client, args) {
  console.log(`$ ${client.bin} ${args.join(" ")}`);
  const result = spawnSync(client.bin, args, { stdio: "inherit", shell: process.platform === "win32" });
  return !result.error && result.status === 0;
}

function usageError(message) {
  console.error(`${message}\n\n${USAGE}`);
  return 2;
}

function main(argv) {
  let parsed;
  try {
    parsed = parseArgs({
      args: argv,
      allowPositionals: true,
      options: { target: { type: "string" }, help: { type: "boolean", short: "h" } },
    });
  } catch (error) {
    return usageError(error.message);
  }
  const { values, positionals } = parsed;
  if (values.help) {
    console.log(USAGE);
    return 0;
  }
  const target = values.target ?? null;
  if (target !== null && !CLIENTS.some((client) => client.bin === target)) {
    return usageError(`--target must be claude or codex, got: ${target}`);
  }
  const command = positionals[0] ?? "install";
  if ((command !== "install" && command !== "update") || positionals.length > 1) {
    return usageError(`Unknown argument: ${positionals.find((arg) => arg !== "install" && arg !== "update") ?? positionals[1]}`);
  }

  const candidates = CLIENTS.filter((client) => !target || client.bin === target);
  const found = candidates.filter((client) => isInstalled(client.bin));
  if (found.length === 0) {
    console.error(
      target
        ? `\`${target}\` was not found on PATH. Install ${candidates[0].name}, then run this again.`
        : "Neither `claude` (Claude Code) nor `codex` (Codex) was found on PATH. Install one of them, then run this again."
    );
    return 1;
  }

  const failed = [];
  const skipped = [];
  for (const client of found) {
    console.log(`\n${client.name}`);
    if (command === "update") {
      const present = hasGroundwork(client);
      if (present === null) {
        console.error(
          `Could not read the plugin list from \`${client.bin} ${client.list.join(" ")}\`; trying the update anyway.`
        );
      } else if (!present) {
        console.log(`groundwork is not installed for ${client.name}; skipped.`);
        skipped.push(client.name);
        continue;
      }
    }
    if (client[command].every((args) => run(client, args))) {
      console.log(`groundwork ${command === "install" ? "installed" : "updated"} for ${client.name}. ${client.after}`);
    } else {
      failed.push(client.name);
    }
  }

  if (failed.length > 0) {
    console.error(`\nFailed for ${failed.join(" and ")}. The output above shows the command that failed and why.`);
    return 1;
  }
  if (skipped.length === found.length) {
    console.error("\ngroundwork is not installed for any client. Run `npx @enebin/groundwork@latest install` to add it.");
    return 1;
  }
  if (skipped.length > 0) {
    console.log(`\nTo add groundwork to ${skipped.join(" and ")}, run \`npx @enebin/groundwork@latest install\`.`);
  }
  console.log(
    command === "install"
      ? '\nNext, in the repository you want to set up, say: "Set up groundwork for this repo."'
      : '\nNext, in each repository you set up, say: "update groundwork".'
  );
  return 0;
}

process.exitCode = main(process.argv.slice(2));
