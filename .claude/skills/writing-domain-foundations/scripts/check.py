#!/usr/bin/env python3
"""Check a domain folder: README index matches files, names are kebab-case, links resolve."""
import re
import sys
from pathlib import Path

NAME = re.compile(r"^(\d{2}-)?[a-z0-9]+(-[a-z0-9]+)*\.md$")
LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")


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
    for e in dict.fromkeys(errors):
        print("ERROR:", e)
    if not errors:
        print(f"OK: {len(files)} files, README index complete")
    return 1 if errors else 0


sys.exit(main())
