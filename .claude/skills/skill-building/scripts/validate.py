#!/usr/bin/env python3
"""Validate a skill folder against the official Claude skill rules and this repo's conventions.

Usage: python3 validate.py <skill-dir> [<skill-dir> ...]
Exit code 0 when no ERROR was found, 1 otherwise. WARN lines need a fix or a reason.
"""
import re
import sys
from pathlib import Path

# Repo convention: every repo skill's description starts with this prefix.
DESC_PREFIX = "catncockroach - "

# Limits from the official docs (platform.claude.com best practices + code.claude.com/docs/en/skills).
NAME_MAX = 64
DESC_MAX = 1024          # portable limit; Claude Code's listing truncates at 1,536 incl. when_to_use
LISTING_MAX = 1536
BODY_MAX_LINES = 500
REF_TOC_LINES = 100      # reference files longer than this need a contents list
RESERVED = ("anthropic", "claude")

KNOWN_KEYS = {
    "name", "description", "when_to_use", "argument-hint", "arguments",
    "disable-model-invocation", "user-invocable", "allowed-tools", "disallowed-tools",
    "model", "effort", "context", "agent", "background", "hooks", "paths", "shell",
    "metadata", "license", "compatibility",
}

results = []


def report(level, path, msg):
    results.append(level)
    print(f"{level:5} {path}: {msg}")


def parse_frontmatter(text):
    """Return (dict, body, error). Uses PyYAML when present, else a flat key: value parser."""
    if not text.startswith("---\n"):
        return None, text, "frontmatter must start with '---' on line 1"
    end = text.find("\n---", 4)
    if end == -1:
        return None, text, "frontmatter has no closing '---'"
    raw = text[4:end]
    body = text[end + 4:].lstrip("\n")
    try:
        import yaml
        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            return None, body, "frontmatter is not a YAML mapping"
        return data, body, None
    except ImportError:
        # Fallback: flat `key: value` lines only (enough for name/description checks).
        data = {}
        for line in raw.splitlines():
            m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
            if m:
                data[m.group(1)] = m.group(2).strip().strip('"').strip("'")
        return data, body, None
    except Exception as e:  # yaml.YAMLError and friends
        return None, body, f"YAML does not parse ({e}); Claude Code would load the skill with NO fields"


def check_links(md_path, text, skill_dir, is_skill_md):
    """Check relative markdown links resolve; flag nested references from non-SKILL.md files."""
    # Links inside code are examples/templates, not real references.
    text = re.sub(r"^\s*(`{3,}|~{3,}).*?^\s*\1", "", text, flags=re.S | re.M)
    text = re.sub(r"`[^`\n]*`", "", text)
    for target in re.findall(r"\]\(([^)\s]+)\)", text):
        if re.match(r"^[a-z]+:", target) or target.startswith("#"):
            continue
        target_path = (md_path.parent / target.split("#")[0]).resolve()
        if not target_path.exists():
            report("ERROR", md_path, f"broken link -> {target}")
        elif not is_skill_md and target_path.suffix == ".md" and skill_dir in target_path.parents:
            report("WARN", md_path, f"nested reference -> {target} (keep references one level deep from SKILL.md)")


def validate(skill_dir):
    skill_dir = skill_dir.resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        report("ERROR", skill_dir, "no SKILL.md")
        return
    text = skill_md.read_text(encoding="utf-8")
    fm, body, err = parse_frontmatter(text)
    if err:
        report("ERROR", skill_md, err)
        return

    # name
    name = str(fm.get("name", skill_dir.name))
    if not re.fullmatch(r"[a-z0-9-]+", name):
        report("ERROR", skill_md, f"name '{name}' must be lowercase letters, digits, hyphens")
    if len(name) > NAME_MAX:
        report("ERROR", skill_md, f"name is {len(name)} chars (max {NAME_MAX})")
    if any(r in name.lower() for r in RESERVED):
        report("ERROR", skill_md, f"name '{name}' contains a reserved word {RESERVED}")
    if name != skill_dir.name:
        report("WARN", skill_md, f"name '{name}' differs from folder '{skill_dir.name}'")

    # description
    desc = fm.get("description")
    if not desc or not str(desc).strip():
        report("ERROR", skill_md, "description is missing or empty")
    else:
        desc = str(desc)
        if not desc.startswith(DESC_PREFIX):
            report("ERROR", skill_md, f"description must start with '{DESC_PREFIX}'")
        if len(desc) > DESC_MAX:
            report("ERROR", skill_md, f"description is {len(desc)} chars (max {DESC_MAX})")
        if re.search(r"<[A-Za-z/][^>]*>", desc):
            report("ERROR", skill_md, "description contains an XML/HTML tag")
        if re.match(r"^(I|You)\b", desc[len(DESC_PREFIX):] if desc.startswith(DESC_PREFIX) else desc):
            report("WARN", skill_md, "description should be third person ('Builds…', not 'I/You…')")
        if "use when" not in desc.lower() and "use for" not in desc.lower():
            report("WARN", skill_md, "description should say when to use it ('Use when …')")
        combined = len(desc) + len(str(fm.get("when_to_use", "")))
        if combined > LISTING_MAX:
            report("WARN", skill_md, f"description + when_to_use is {combined} chars; listing truncates at {LISTING_MAX}")

    # keys
    for key in fm:
        if key not in KNOWN_KEYS:
            report("WARN", skill_md, f"unknown frontmatter key '{key}' (Claude Code ignores it silently)")

    # body
    n = len(body.splitlines())
    if n > BODY_MAX_LINES:
        report("ERROR", skill_md, f"body is {n} lines (keep under {BODY_MAX_LINES}; move reference out)")
    check_links(skill_md, body, skill_dir, is_skill_md=True)

    # every file in the skill
    for f in sorted(skill_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix in {".md", ".py", ".sh", ".txt", ".json", ".yaml", ".yml"}:
            content = f.read_text(encoding="utf-8", errors="replace")
            if re.search(r"\b[\w.-]+\\[\w.-]+\.(md|py|sh|json)\b", content):
                report("WARN", f, "Windows-style backslash path; use forward slashes")
        if f.suffix == ".md" and f != skill_md:
            content = f.read_text(encoding="utf-8")
            check_links(f, content, skill_dir, is_skill_md=False)
            lines = content.splitlines()
            if len(lines) > REF_TOC_LINES and not re.search(r"^#+\s*(Contents|Mục lục)", content, re.M | re.I):
                report("WARN", f, f"{len(lines)} lines without a '## Contents' section")
            if f.name not in body and str(f.relative_to(skill_dir)) not in body:
                report("WARN", f, "not mentioned in SKILL.md (orphan, or only reachable through another file)")


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(2)
    for arg in sys.argv[1:]:
        validate(Path(arg))
    errors = results.count("ERROR")
    warns = results.count("WARN")
    print(f"\n{'OK' if errors == 0 else 'FAIL'}: {errors} error(s), {warns} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
