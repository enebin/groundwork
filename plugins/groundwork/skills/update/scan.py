"""Sort plugin changes and managed rule blocks for one repository, without network access.

  scan.py <repository root>   JSON report for the update skill
  scan.py --sources           JSON map of rule block id to source hash, for stamping markers
  scan.py --notes <version>   Markdown release notes for one version
"""
import hashlib
import json
from pathlib import Path
import re
import sys

PLUGIN = Path(__file__).resolve().parents[2]
SECTIONS = ["New features", "Bug fixes", "Upgrading"]
EMPTY = {"", "null", "~", "{}", "[]", '""', "''"}
BLOCK = re.compile(r"<!-- groundwork:begin ([\w.-]+)(?: source=([0-9a-f]+))? -->\n?(.*?)<!-- groundwork:end \1 -->", re.S)
SOURCE_HEADING = re.compile(r"^#+ (Rules|Contract) to write\s*$")


def version_key(version):
    return tuple(int(part) for part in version.split("."))


def load_changes():
    return json.loads((PLUGIN / "CHANGES.json").read_text())["releases"]


def frontmatter(text):
    """Map each dotted key path to whether it holds a value. Enough YAML for presence checks."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    has_value = {}
    stack = []
    block_indent = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        indent = len(line) - len(line.lstrip())
        if block_indent is not None:
            if not line.strip() or indent > block_indent:
                continue
            block_indent = None
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if stack:
                has_value[stack[-1][1]] = True
            continue
        match = re.match(r"([\w.-]+):\s*(.*)$", stripped)
        if not match:
            continue
        while stack and stack[-1][0] >= indent:
            stack.pop()
        path = ".".join([entry[1] for entry in stack[-1:]] + [match.group(1)])
        value = re.sub(r"\s+#.*$", "", match.group(2)).strip()
        has_value[path] = value not in EMPTY
        if value[:1] in {"|", ">"}:
            block_indent = indent
        if value not in EMPTY:
            for parent in [entry[1] for entry in stack]:
                has_value[parent] = True
        stack.append((indent, path))
    return has_value


def scalar(text, key):
    match = re.search(rf"^{re.escape(key)}:\s*([^\s#]+)", text, re.M)
    return match.group(1).strip("\"'") if match else None


def nested_scalar(text, parent, key):
    match = re.search(rf"^{parent}:\s*\n((?:[ \t]+.*\n?)*)", text, re.M)
    if not match:
        return None
    return scalar("\n".join(line.strip() for line in match.group(1).splitlines()), key)


def recorded_addons(text):
    match = re.search(r"<!-- groundwork:begin addons -->(.*?)<!-- groundwork:end addons -->", text, re.S)
    if not match:
        return set()
    names = set()
    for row in match.group(1).splitlines():
        cells = [cell.strip().strip("`") for cell in row.strip().strip("|").split("|")]
        if row.strip().startswith("|") and cells[0] and cells[0] != "Skill" and not set(cells[0]) <= set("-: "):
            names.add(cells[0])
    return names


def fenced_source(text):
    lines = text.split("\n")
    for start, line in enumerate(lines):
        if not SOURCE_HEADING.match(line):
            continue
        for open_at in range(start + 1, len(lines)):
            fence = re.match(r"^(`{3,})markdown\s*$", lines[open_at])
            if fence:
                body = []
                for inner in lines[open_at + 1:]:
                    if inner.rstrip() == fence.group(1):
                        return "\n".join(body)
                    body.append(inner)
            if lines[open_at].startswith("#"):
                return None
    return None


def section(text, name):
    match = re.search(rf"^## {re.escape(name)}(?: \(add-on\))?\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else None


def source_bodies():
    texts = {
        "implementation": (PLUGIN / "reference/implementation.md").read_text(),
    }
    for path in sorted((PLUGIN / "catalog/architecture").glob("*.md")):
        texts[path.stem] = path.read_text()
    verification = (PLUGIN / "catalog/verification.md").read_text()
    for name in re.findall(r"^## ([\w-]+)(?: \(add-on\))?\s*$", verification, re.M):
        texts.setdefault(name, section(verification, name))
    bodies = {block_id: fenced_source(text or "") for block_id, text in texts.items()}
    return {block_id: body for block_id, body in bodies.items() if body is not None}


def source_hash(body):
    return hashlib.sha256(body.encode()).hexdigest()[:12]


def sources():
    return {block_id: source_hash(body) for block_id, body in source_bodies().items()}


def item_group(item, has_value, addons):
    kind = item["kind"]
    if kind == "auto":
        return "comes_automatically"
    if "addons" in item:
        return "already_in_place" if set(item["addons"]) <= addons else "can_attach"
    key = item.get("key")
    if kind == "migrate":
        if key is None:
            return "needs_migration"
        if "values" in item:
            return "needs_migration" if item.get("current") in item["values"] else "already_in_place"
        return "already_in_place" if has_value.get(key) else "needs_migration"
    return "already_in_place" if key and has_value.get(key) else "can_attach"


def block_report(root, config, bodies):
    blocks = []
    for doc_key, default in (("rules", "AGENTS.md"), ("architecture", "ARCHITECTURE.md")):
        name = nested_scalar(config, "docs", doc_key) or default
        path = root / name
        if not path.is_file():
            continue
        for match in BLOCK.finditer(path.read_text()):
            block_id, stamped, text = match.groups()
            body = bodies.get(block_id)
            current = source_hash(body) if body is not None else None
            if current is None:
                status = "unknown"
            elif stamped is None:
                status = "unstamped-same" if text.strip() == body.strip() else "unstamped"
            else:
                status = "same" if stamped == current else "changed"
            blocks.append({"file": name, "id": block_id, "status": status, "source": current})
    return blocks


def scan(root):
    config_path = root / "GROUNDWORK.md"
    if not config_path.is_file():
        return {"status": "not-set-up"}
    config = config_path.read_text()
    installed = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())["version"]
    releases = load_changes()
    known = max((release["version"] for release in releases), key=version_key)
    target = min(installed, known, key=version_key)
    set_up_with = scalar(config, "plugin_version")
    report = {
        "installed": installed,
        "latest_known": known,
        "target": target,
        "set_up_with": set_up_with,
        "schema": scalar(config, "groundwork"),
    }
    if set_up_with and version_key(set_up_with) > version_key(installed):
        return {**report, "status": "plugin-older-than-setup"}

    has_value = frontmatter(config)
    addons = recorded_addons(config)
    items = []
    for release in sorted(releases, key=lambda release: version_key(release["version"])):
        version = version_key(release["version"])
        if set_up_with and version <= version_key(set_up_with):
            continue
        if version > version_key(target):
            continue
        for item in release["items"]:
            if "values" in item:
                item = {**item, "current": scalar_path(config, item["key"])}
            items.append({
                "version": release["version"],
                "section": item["section"],
                "group": item_group(item, has_value, addons),
                "text": item["text"],
                **{field: item[field] for field in ("key", "addons") if field in item},
            })
    blocks = block_report(root, config, source_bodies())
    choices = sum(item["group"] in {"needs_migration", "can_attach"} for item in items)
    stale_blocks = any(block["status"] not in {"same", "unknown"} for block in blocks)
    up_to_date = set_up_with == target and not stale_blocks
    return {
        **report,
        "status": "up-to-date" if up_to_date else "ok",
        "choices": choices,
        "items": items,
        "blocks": blocks,
    }


def scalar_path(config, dotted):
    parts = dotted.split(".")
    if len(parts) == 1:
        return scalar(config, parts[0])
    return nested_scalar(config, parts[0], parts[1])


def notes(version):
    release = next((release for release in load_changes() if release["version"] == version), None)
    if release is None:
        raise SystemExit(f"{version} is not in CHANGES.json")
    lines = [f"## {version}"]
    sections = SECTIONS + sorted({item["section"] for item in release["items"]} - set(SECTIONS))
    for name in sections:
        bullets = [item["text"] for item in release["items"] if item["section"] == name]
        if bullets:
            lines += ["", f"### {name}", ""] + [f"- {text}" for text in bullets]
    return "\n".join(lines) + "\n"


def main(argv):
    if argv[:1] == ["--sources"]:
        print(json.dumps(sources(), indent=2))
    elif argv[:1] == ["--notes"] and len(argv) == 2:
        print(notes(argv[1]), end="")
    elif len(argv) == 1:
        print(json.dumps(scan(Path(argv[0]).resolve()), indent=2, ensure_ascii=False))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
