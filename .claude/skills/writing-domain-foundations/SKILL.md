---
name: writing-domain-foundations
description: "catncockroach - Writes the foundational, core knowledge of a field as a domain folder at the repo root: several English-named .md files (Vietnamese content) plus a README.md that overviews the domain and explains what each file covers. Use when the user wants to learn or relearn the basics of a field, or asks for kiến thức cơ sở / cốt lõi / nền tảng của một ngành or domain (viết kiến thức nền tảng, học lại cơ bản, xây domain mới), even if they don't say 'skill'. Not for time-bound investigations: those go to the research skill."
---

# Writing domain foundations

You write the stable, core knowledge of a field so the repo owner can learn or relearn it from first principles. One request produces one **domain folder** at the repo root:

```
<domain>/
├── README.md              # overview + index of every file
├── 01-<topic>.md          # one concept cluster per file
├── 02-<topic>.md
└── ...
```

- `<domain>` and file names are lowercase English kebab-case (`internet/`, `01-physical-layer.md`). The numeric prefix gives the reading order.
- Content is Vietnamese; technical terms, protocol names and acronyms stay in English.
- Foundations are stable knowledge. Explain mechanisms and the reasons behind them, and leave out versions, vendors and news that age quickly.

## 1. Frame the domain

First list the repo root: if `<domain>/` exists, read its README and extend it instead of overwriting.

Settle three things: the domain name, the **scope** (which sub-fields are in, which are out) and the reader's starting level (default: IT-literate, new to this field). If any of these would change the file list, invoke `grill-me` in Called mode: `Called by writing-domain-foundations. Settle: <open points>. Known so far: <one line>`. If the request is clear, choose the most sensible reading and record it in the README.

Done when you can state the scope in two sentences.

## 2. Outline

Design the file list as a learning path: each file depends only on earlier ones. Split by concept cluster, not by length, and aim for 6–15 files (fewer for a narrow field). Show the user the list (file name + one-line meaning) and adapt it if they react. For a layered or staged field, make one file per layer or stage.

Done when every file has a name, a one-line purpose, and no two files overlap.

## 3. Write the files

Write each file with the template in [references/file-template.md](references/file-template.md). Rules:

- Teach the "why" and the mechanism, then the vocabulary. A reader should be able to rebuild the idea, not just recite it.
- Use concrete examples (a real packet, a real command, a worked number) in preference to abstract definitions.
- Cross-link related files with relative links. Link to concepts a file relies on that live in earlier files.
- Add a diagram (ASCII or a Mermaid block) where structure or flow matters.
- Check facts you are not certain of (numbers, port values, header fields, dates) with WebSearch/WebFetch before writing them. Prefer standards (RFCs, IEEE, ISO) and official docs. If you cannot verify a figure, leave it out.
- Keep each file focused: readable in one sitting.

Done when every file in the outline exists and follows the template.

## 4. Write the README

Use the template in [references/readme-template.md](references/readme-template.md). Every file must appear in the index with a one-line meaning that says what the reader learns there, not just its title.

## 5. Validate

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check.py <domain>
```

It checks that every `.md` file is listed in the README and vice versa, that file names are English kebab-case, and that relative links resolve. Fix every error and re-run until it exits 0.

## 6. Deliver

Tell the user in Vietnamese: the domain folder, the file list with meanings, and any facts you left out because you could not verify them. Then commit, push and open the PR with the `commit` skill, and include the PR link.
