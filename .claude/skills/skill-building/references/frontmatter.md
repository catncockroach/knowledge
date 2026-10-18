# Skill mechanics reference (Claude Code)

Condensed from the official docs. Last checked against them on 2026-10-18. If a field behaves differently from what is described here, re-fetch the source and update this file.
- https://code.claude.com/docs/en/skills
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

## Contents
- Locations and precedence
- Frontmatter fields
- Limits
- String substitutions
- Dynamic context injection
- Running in a subagent (`context: fork`)
- Content lifecycle
- Troubleshooting

## Locations and precedence

| Scope | Path |
|---|---|
| Personal (all projects) | `~/.claude/skills/<name>/SKILL.md` |
| Project (this repo) | `.claude/skills/<name>/SKILL.md` |
| Nested | `<subdir>/.claude/skills/<name>/SKILL.md`, loaded once Claude touches files in `<subdir>` |
| Plugin | `<plugin>/skills/<name>/SKILL.md`, invoked as `/plugin:name` |

- When names collide: enterprise beats personal, and personal beats project. A skill beats a `.claude/commands/` file with the same name.
- Never name a folder `synced`. The prefix `anthropic-skills:` is reserved.
- Edits to existing skills apply live. A new top-level skills directory needs `/reload-skills`.

## Frontmatter fields

The opening `---` must be line 1. Claude Code silently ignores unknown keys. Malformed YAML loads the skill with **no** fields, so the description cannot match anything, and the problem is visible only with `claude --debug`.

| Field | Default | Meaning |
|---|---|---|
| `name` | folder name | `/` command name. Lowercase letters, digits and hyphens. ≤ 64 chars. Must not contain `anthropic` or `claude`. |
| `description` | first body line | What it does and when to use it. Third person. This is what Claude matches against. |
| `when_to_use` | none | Extra trigger text appended to `description`. Shares the listing cap. |
| `argument-hint` | none | Autocomplete hint, e.g. `[topic]`. |
| `arguments` | none | Named positional args for `$name` substitution (space-separated string or YAML list). |
| `disable-model-invocation` | `false` | `true` makes the skill user-invoked only. The description leaves Claude's context, and subagents and scheduled tasks cannot preload it. |
| `user-invocable` | `true` | `false` hides it from the `/` menu. Claude can still invoke it. |
| `allowed-tools` | none | Tools **pre-approved** (no prompt) during the invoking turn. Space- or comma-separated, or a YAML list. Does not restrict tools. Deny/ask rules still win. The grant clears on the user's next message. For session-wide approval, use `permissions.allow` in `.claude/settings.json`. |
| `disallowed-tools` | none | Tools removed while the skill is active. |
| `model` | session | Model for this turn (`/model` values or `inherit`). |
| `effort` | session | `low`, `medium`, `high`, `xhigh` or `max`. |
| `context` | none | `fork` runs the skill in a subagent. |
| `agent` | `general-purpose` | Subagent type for a fork: `Explore`, `Plan`, `general-purpose` or a custom agent. |
| `background` | `true` | For a fork, `false` waits for the result in the same turn. |
| `hooks` | none | Hooks registered when the skill is invoked, kept for the session. |
| `paths` | none | Globs that limit automatic activation to matching files. |
| `shell` | `bash` | Shell for `!` blocks (`bash` or `powershell`). |
| `metadata` | none | Free-form map for your own tooling. |
| `license`, `compatibility` | none | Accepted, not acted on. `compatibility` ≤ 500 chars. |

**Portability.** claude.ai uploads and the Skills API accept only `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools`. Any other key is a hard error there. Repo-only skills may use the full table.

`allowed-tools` examples:
```yaml
allowed-tools: WebSearch WebFetch
allowed-tools: Bash(git add *) Bash(git commit *)
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/run.sh *)
```

## Limits

- `name`: ≤ 64 chars.
- `description`: ≤ 1,024 chars (the portable limit). In Claude Code's listing, `description` + `when_to_use` is truncated at 1,536 chars.
- The whole skill listing has a budget of about 1% of the context window. When it overflows, Claude Code drops the descriptions of the least-used skills first, so put the trigger words first.
- `SKILL.md` body: under 500 lines.
- Reference files over 100 lines: open with a contents list.

## String substitutions

| Placeholder | Expands to |
|---|---|
| `$ARGUMENTS` | Full argument string. If no placeholder is present, Claude Code appends `ARGUMENTS: <value>`. |
| `$0`, `$1`, … / `$ARGUMENTS[N]` | Positional argument (0-based, shell-style quoting). |
| `$name` | A named argument from `arguments:`. |
| `${CLAUDE_SKILL_DIR}` | Folder containing `SKILL.md`. Use it for stable paths. |
| `${CLAUDE_PROJECT_DIR}` | Project root. |
| `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}` | Session id, effort level. |

Escape a literal dollar sign as `\$`. Values are inserted literally and are not re-expanded.

## Dynamic context injection

`` !`command` `` (at line start or after whitespace) runs **before** Claude sees the skill, and its output replaces the placeholder. For multi-line commands, use a fenced block opened with ` ```! `.
- Any non-zero exit aborts the whole invocation (exit 1 from grep/diff-style commands is tolerated). Append `|| true` when failure is acceptable.
- The command must be permitted. Pre-approve it in `allowed-tools`, or the invocation aborts.
- It runs in the session's current directory. Use `${CLAUDE_SKILL_DIR}` for paths inside the skill.

```markdown
## Current changes
!`git diff HEAD || true`
```

## Running in a subagent (`context: fork`)

- The skill body becomes the subagent's prompt. The subagent **does not see the conversation**, so the skill must be self-contained and must contain a task. A guideline-only skill makes a useless fork.
- Runs in the background by default, with a narrower background tool set. Set `background: false` if it needs other tools or the result is needed right away.
- Edits made by a background fork are outside `/rewind` checkpoints.

Alternative: keep the skill inline and have it spawn subagents with the Agent tool (as `research` does). This gives you more control over prompts and parallelism.

## Content lifecycle

- Always in context: the name and description of every model-invoked skill.
- The body loads on invocation and stays in the conversation. Claude does not re-read the file, so phrase rules to cover the whole task ("after every edit").
- After compaction, only the first ~5,000 tokens of each invoked skill are re-attached (25,000 tokens in total). Put critical rules at the top.
- A rule that must hold *every* time belongs in a hook (the `hooks` frontmatter or settings), not in prose.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Never triggers | Add the words users actually type to the description. Check the YAML parses (`claude --debug`, `claude plugin validate .claude/skills`). |
| Triggers too often | Make the description more specific, or set `disable-model-invocation: true`. |
| Followed at first, then forgotten | Make the rule task-wide; move hard rules to hooks; re-invoke after compaction. |
| Description cut short | Fewer or shorter descriptions. Run `/doctor` or `/skill-doctor`, or raise `skillListingBudgetFraction`. |
| Missing from the `/` menu | The name contains forbidden characters (`<`, `>`, control/zero-width/bidi chars). |
