---
name: naming-branches
description: "catncockroach - Picks a meaningful git branch name (`type/short-english-slug`, lowercase kebab-case, describing the work) whenever a branch is about to be created or checked out. Use when about to create a branch: use automatically before `git checkout -b`, `git switch -c`, `git branch NAME` or creating a branch through the GitHub tool, and when the user says đặt tên branch, tạo branch, checkout branch mới, even if they don't mention naming rules. Not for renaming a branch the harness or user already designated."
allowed-tools: Bash(git branch *) Bash(git checkout *) Bash(git switch *) Bash(git status *)
---

# Naming branches

A branch name should tell the owner, at a glance in a PR list, what the work is about. Auto-generated names such as `ccr-bd656127-kw0065` or `branch-1` say nothing.

## 0. Respect a designated branch

If the task, the user or the session setup names the branch to work on (for example "Develop on branch `ccr-...`"), **use that exact name**. Do not rename it, and do not push to a different one. This skill only applies when you are the one choosing a new name.

## 1. Name format

```
<type>/<slug>
```

- All **lowercase**, words joined by `-`, only `a-z`, `0-9`, `-` and the one `/`.
- **English**, even though the notes are Vietnamese (ASCII-safe, no diacritics).
- `slug`: 2–5 words naming the *subject*, not the action's date or the tool. Keep the whole name ≤ 50 chars.

| type | for | example |
|---|---|---|
| `research` | a new `research/<date>-<slug>/` run | `research/cve-response-sandbox` |
| `notes` | a domain folder or notes (`writing-domain-foundations`) | `notes/internet-foundations` |
| `skill` | creating or changing a `.claude/skills/` skill | `skill/naming-branches` |
| `fix` | correcting content, broken links, typos | `fix/broken-links-networking` |
| `docs` | CLAUDE.md, README files, repo conventions | `docs/claude-md-branch-rules` |
| `chore` | anything else (moves, cleanup) | `chore/reorganize-research` |

## 2. Choose the slug

1. State the work in one sentence, then keep the nouns that identify it (`cve response research` → `cve-response`).
2. Drop filler: `update`, `new`, `stuff`, `changes`, `wip`, `test`, and the date (git history has it).
3. Reuse the folder or skill name when the work is about one (`skill/commit`, `notes/internet`).
4. One branch = one purpose. If the slug needs "and", the work likely belongs in two branches.

## 3. Create it

1. `git status` and `git branch -a`: confirm the working tree is clean enough and the name is unused. If it exists, add a distinguishing word (`research/cve-response-poc`), not a number.
2. Branch from the up-to-date default branch unless the user says otherwise: `git fetch origin main && git switch -c <name> origin/main`.

Done when the branch exists, its name matches `^(research|notes|skill|fix|docs|chore)/[a-z0-9]+(-[a-z0-9]+)*$`, and you have told the user the name in one line.
