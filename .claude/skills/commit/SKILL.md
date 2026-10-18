---
name: commit
description: "catncockroach - Creates git commits in this repo's house style: a brief, all-lowercase `scope: detail` subject, a few `- ` bullet lines describing the change, and a Co-Authored-By trailer for the agent. Use whenever you are about to run git commit in this repo: the user says commit, commit đi, tạo commit, lưu thay đổi, or a task ends with committing, even if they don't mention the message format. Not for push, pull requests, or rewriting history."
argument-hint: "[gợi ý nội dung commit]"
allowed-tools: Bash(git status *) Bash(git diff *) Bash(git log *) Bash(git add *) Bash(git commit *)
---

# Commit

Commit only what the user asked to commit, with a **brief**, **lowercase** message in exactly this shape:

```
<scope>: <detail>

- <what changed>
- <what changed>

Co-Authored-By: <agent trailer>
```

## Message rules

- **Lowercase everything** you write: subject, bullets, file and folder names (`update claude.md`, not `update CLAUDE.md`). The owner wants no capitals at all. The trailer is the one exception (see below).
- **Subject**: `<scope>: <detail>`, at most ~50 chars, imperative, no trailing period.
  - `scope` is the brief title: the area touched, usually a top-level folder or a skill name (`skill`, `research`, `internet`, `readme`, `repo`). Several areas → the one that matters most, or `repo`.
  - `detail` says what the commit does, in a few words (`add commit skill`, `fix broken links in dns notes`).
- **Bullets**: 1–4 lines starting with `- `, each one concrete change, at most ~72 chars. Say *what* and, when not obvious, *why*. Skip filler like "update files".
- **Language**: English, even though notes in the repo are Vietnamese. Vietnamese proper nouns or quoted titles may stay as they are, lowercased.
- **Trailer**: copy the `Co-Authored-By:` line from the commit attribution in your system context verbatim (it names the current model, so do not hard-code it). If there is none, use `Co-Authored-By: Claude <noreply@anthropic.com>`. Keep its capitalisation, since git and GitHub parse the trailer by that exact key.

Examples:

```
skill: add commit skill

- add .claude/skills/commit with the message format rules
- note the commit convention in claude.md

Co-Authored-By: <attribution line from your context>
```

```
internet: fix typos in dns notes

- correct ttl explanation in 03-dns.md

Co-Authored-By: <attribution line from your context>
```

## Current state

!`git status --short || true`

Recent commits:
!`git log --oneline -5 || true`

## 1. Inspect

Run `git diff --staged` and `git diff` (plus `git status` if the state above is stale) and read what changed. For untracked files, look at their names and skim their content.

Done when you can say in one line what each changed path is about.

## 2. Pick what goes in

- Something already staged → commit exactly the staged set and leave the rest alone. If the staged set holds changes outside what the user asked for, ask before committing them.
- Nothing staged → stage the changes that belong to what the user asked for, by path (`git add <path>...`). Use `git add -A` only when every change belongs.
- Changes that cover clearly separate topics → one commit per topic, in a sensible order, each with its own message. This holds even for "commit hết": everything gets committed, just split. Splitting also keeps each message brief.
- Changes outside the request → leave them unstaged, name them at the end, and offer to commit them separately.
- Never stage secrets (`.env`, keys, tokens, credentials). Skip them, warn the user, and suggest `.gitignore`. Do not print their values while inspecting.

Done when `git diff --staged --stat` shows exactly the set for this commit.

## 3. Write and commit

Write the message by the rules above, then commit through a heredoc so the layout survives:

```bash
git commit -F - <<'EOF'
scope: detail

- change one
- change two

Co-Authored-By: ...
EOF
```

If a hook rejects the commit, fix the cause, re-stage and make a **new** commit. Keep hooks on (no `--no-verify`) and leave earlier commits as they are (no `--amend`) unless the user asks.

Done when `git log -1 --format=%B` prints a message that follows every rule above: re-read it against them, letter case included.

## 4. Report

Tell the user, in Vietnamese, the short hash and subject of each commit, plus anything you left out and why. Do not push.
