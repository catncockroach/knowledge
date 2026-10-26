---
name: commit
description: "catncockroach - Creates git commits in this repo's house style (an all-lowercase `brief title: detail` subject, a few `- ` bullet lines, Co-Authored-By trailers only: the agent, plus the owner in cloud sessions), then pushes the branch and opens or updates its pull request without asking. Use whenever a task in this repo has changed files and is done, or the user says commit, commit đi, tạo commit, lưu thay đổi, push, tạo pr, even if they don't mention the message format. Never merges a pull request; not for rewriting history."
argument-hint: "[gợi ý nội dung commit]"
allowed-tools: Bash(git status *) Bash(git diff *) Bash(git log *) Bash(git add *) Bash(git commit *) Bash(git fetch *) Bash(git checkout *) Bash(git stash *) Bash(git push *)
---

# Commit

The owner wants finished work committed, pushed and opened as a pull request **without being asked**; never merge it, the owner merges. Commit only the changes that belong to the task, with a **brief**, **lowercase** message in exactly this shape:

```
<brief title>: <detail>

- <what changed>
- <what changed>

Co-Authored-By: <agent trailer>
Co-Authored-By: catncockroach <hai.hv04@gmail.com>   # cloud sessions only
```

## Message rules

- **Lowercase everything** you write: subject, bullets, file and folder names (`update claude.md`, not `update CLAUDE.md`). The owner wants no capitals at all. The trailers are the one exception (see below).
- **Subject**: `<brief title>: <detail>`, no trailing period.
  - `brief title` is free-form: a few words (often 1–4) naming what the commit is about, phrased however reads best. It is not a fixed scope list: `more agent's skill`, `dns notes`, `networking foundations`, `research reports` are all fine.
  - `detail` says what the commit does, in a few words (`grilling`, `add commit skill`, `fix broken links`).
- **Bullets**: 1–4 lines starting with `- `, each one concrete change, at most ~72 chars. Say *what* and, when not obvious, *why*. Skip filler like "update files".
- **Language**: English, even though notes in the repo are Vietnamese. Vietnamese proper nouns or quoted titles may stay as they are, lowercased.
- **Trailer**: copy the `Co-Authored-By:` line from the commit attribution in your system context verbatim (it names the current model, so do not hard-code it). If there is none, use `Co-Authored-By: Claude <noreply@anthropic.com>`. Keep its capitalisation, since git and GitHub parse the trailer by that exact key.
- **Owner trailer in cloud sessions**: when the commit is made in a Claude Code cloud session (check with `echo "$CLAUDE_CODE_REMOTE"`: it prints `true`), add `Co-Authored-By: catncockroach <hai.hv04@gmail.com>` on the line right after the agent trailer, so the owner is credited for commits made from the phone or web. In a local session (variable empty or unset), leave it out: the owner is already the commit author there.
- **No other trailers.** The message ends on the `Co-Authored-By:` line(s). Drop every other trailer or link the attribution suggests, such as `Claude-Session:` or a claude.ai session URL: they point to the owner's private session and do not belong in the repo history. The repo's `CLAUDE.md` sets the same rule, and the attribution text itself yields to the owner's instructions, so this rule wins.

Examples:

```
agent skills: add commit

- add .claude/skills/commit with the message format rules
- note the commit convention in claude.md

Co-Authored-By: <attribution line from your context>
Co-Authored-By: catncockroach <hai.hv04@gmail.com>
```

(cloud session: both trailers)

```
dns notes: fix ttl typo

- correct ttl explanation in 03-dns.md

Co-Authored-By: <attribution line from your context>
```

(local session: agent trailer only)

## Current state

!`git status --short || true`

Recent commits:
!`git log --oneline -5 || true`

## 1. Inspect

Run `git diff --staged` and `git diff` (plus `git status` if the state above is stale) and read what changed. For untracked files, look at their names and skim their content.

Done when you can say in one line what each changed path is about.

## 2. Pick the branch and what goes in

Before staging, make sure the commit lands on a branch whose PR can still take it. Look up the branch's PR state with the GitHub tool (list PRs whose head is this branch, any state):
- On the default branch (`main`) → create a branch first. If the session or environment names a branch to work on, use that one; otherwise `git checkout -b claude/<short-topic-slug>`.
- The branch's earlier PR is already **merged** → restart the branch from the latest default branch, keeping the working tree: `git fetch origin main && git checkout -B <branch> origin/main`. A merged PR cannot take new commits. If checkout refuses because `main` changed the same files, `git stash`, checkout, then `git stash pop` and resolve.
- The branch has an **open** PR → commit on it; the push in step 4 updates that PR.

Then pick the changes:

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
brief title: detail

- change one
- change two

Co-Authored-By: ...
Co-Authored-By: catncockroach <hai.hv04@gmail.com>   # only if $CLAUDE_CODE_REMOTE is true
EOF
```

If a hook rejects the commit, fix the cause, re-stage and make a **new** commit. Keep hooks on (no `--no-verify`) and leave earlier commits as they are (no `--amend`) unless the user asks.

Done when `git log -1 --format=%B` prints a message that follows every rule above: re-read it against them, letter case included, and check that it ends on the `Co-Authored-By:` line(s) with no other trailer: the agent line, then, in a cloud session, the owner line.

## 4. Push and open the PR

1. Push: `git push -u origin <branch>`. Only if that is rejected as non-fast-forward because the branch was restarted from `main` in step 2 (the remote holds only already-merged commits), retry with `git push -u --force-with-lease origin <branch>`. Never force-push otherwise, and never push to `main` directly.
2. PR, with whatever GitHub tool the session has (the GitHub MCP `create_pull_request`/`update_pull_request`, or `gh pr create`):
   - No PR for this branch yet → open one against `main`. If the repo has a PR template, follow its layout. Title: the commit subject (or a summary subject when several commits). Body in normal-case Vietnamese: what changed, and how it was checked (validator or `check.py` runs, recomputed numbers, links checked), in a few bullets.
   - An open PR already exists → the push updated it. If its scope grew, update the title and body to cover every commit.
   - The body carries no session links or `claude.ai/code/session` URLs, for the same reason as the trailer rule. Keep a plain `🤖 Generated with [Claude Code](https://claude.com/claude-code)` line if the attribution asks for one.
3. Do **not** merge, approve or enable auto-merge, even when the PR is green.

Done when the push succeeded and you have the PR URL.

## 5. Report

Tell the user, in Vietnamese, the short hash and subject of each commit, the PR link (new or updated), and anything you left out and why.
