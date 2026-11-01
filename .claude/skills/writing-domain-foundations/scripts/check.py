#!/usr/bin/env python3
"""Check a domain folder: README index matches files, names are kebab-case, links resolve.

Also warns (exit code unaffected) when a topic file lacks the Q&A section or its
answers are not blockquotes on the lines below the question.
"""
import re
import sys
from pathlib import Path

NAME = re.compile(r"^(\d{2}-)?[a-z0-9]+(-[a-z0-9]+)*\.md$")
QA = "## Câu hỏi"
LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")
QUESTION = re.compile(r"^(\d+\.\s+)?\*\*(.+?)\*\*(.*)$")


def qa_format_issues(text: str) -> list[str]:
    """Each question stands on its own bold line; its '>' blockquote answer starts on a later line."""
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if re.match(rf"^{QA}\s*$", l))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    issues = []
    for i in range(start + 1, end):
        m = QUESTION.match(lines[i])
        if not m:
            continue
        q = m.group(2).strip()
        if m.group(3).strip():
            issues.append(f"answer to '{q}' is on the question's line (move it to the next line, as '>')")
            continue
        nxt = next((lines[j] for j in range(i + 1, end) if lines[j].strip()), "")
        if not nxt.startswith(">"):
            issues.append(f"'{q}' has no '>' blockquote answer")
    return issues


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check.py <domain-dir>")
        return 2
    root = Path(sys.argv[1])
    readme = root / "README.md"
    if not readme.is_file():
        print(f"ERROR: {readme} not found")
        return 1
    errors = []
    files = sorted(p for p in root.glob("*.md") if p.name != "README.md")
    if not files:
        errors.append("no topic files besides README.md")
    text = readme.read_text(encoding="utf-8")
    linked = {
        Path(m).name
        for m in LINK.findall(text)
        if m.endswith(".md") and (readme.parent / m).resolve().parent == root.resolve()
    }
    for p in files:
        if not NAME.match(p.name):
            errors.append(f"{p.name}: not English kebab-case (optionally NN- prefix)")
        if p.name not in linked:
            errors.append(f"{p.name}: not linked from README.md")
    for name in linked - {p.name for p in files}:
        errors.append(f"README.md links {name} but the file does not exist")
    for p in [readme, *files]:
        for target in LINK.findall(p.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+:", target):
                continue
            if not (p.parent / target).exists():
                errors.append(f"{p.name}: broken link {target}")
    # Warn only: older domains predate the Q&A rule, and fixing them is a separate request.
    warnings = []
    for p in files:
        text = p.read_text(encoding="utf-8")
        if not re.search(rf"^{QA}\s*$", text, re.M):
            warnings.append(f"{p.name}: no '{QA}' section")
            continue
        warnings += [f"{p.name}: {w}" for w in qa_format_issues(text)]
    for e in dict.fromkeys(errors):
        print("ERROR:", e)
    for w in warnings:
        print("WARN:", w)
    if not errors:
        print(f"OK: {len(files)} files, README index complete")
    return 1 if errors else 0


sys.exit(main())
