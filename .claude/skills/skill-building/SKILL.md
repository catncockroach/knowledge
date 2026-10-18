---
name: skill-building
description: "catncockroach - Builds a new skill or improves an existing one in this repo's .claude/skills/, following Anthropic's official skill docs: captures intent, designs the layout and frontmatter, writes SKILL.md and its reference files, validates, and test-runs it. Use when the user asks to create, write, add, fix or improve a skill (tạo skill, viết skill, sửa skill), or to turn a workflow from the conversation into a skill."
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/validate.py *)
---

# Skill building

You turn a repeatable task into a **skill**: a folder that teaches a future Claude instance how to do it. That instance has no memory of this conversation, so the skill must carry everything it needs, and nothing it already knows.

Two references back this workflow; read each when its step comes up:
- [references/frontmatter.md](references/frontmatter.md): every frontmatter field, substitutions, `!` injection, `context: fork`, limits.
- [references/authoring.md](references/authoring.md): writing rules from the official best-practices guide, plus the final checklist.

Copy this checklist into your reply and tick it off as you go:

```
- [ ] 1. Intent captured
- [ ] 2. Overlap checked
- [ ] 3. Design agreed
- [ ] 4. Files written
- [ ] 5. Validator green
- [ ] 6. Test-run observed
- [ ] 7. Delivered
```

## 1. Capture intent

Mine the conversation first: if the user says "turn this into a skill", the steps, tools, corrections and output formats are already in the history. Then fill the gaps:

- **Job**: what the skill makes Claude do, and what "done" looks like.
- **Triggers**: the phrases and situations that should fire it, in the words the user actually types (Vietnamese and English), and near-misses that should *not*.
- **Output**: files, their location and format, or a reply.
- **Invocation**: should Claude fire it on its own (model-invoked), or only when the user types `/name` (user-invoked, `disable-model-invocation: true`)? Pick user-invoked for anything with side effects the user wants to time, such as commits, deploys or sending messages.
- **Degrees of freedom**: open field (heuristics, high freedom) or narrow bridge (exact script, low freedom)? See *authoring.md*.

Ask the user (AskUserQuestion, one round) only for what you cannot infer. Done when you can write the description from your answers.

## 2. Check overlap

List `.claude/skills/` and re-read the skill listing in your context. If an existing repo skill covers most of the job, extend it instead of adding a near-duplicate. If a built-in skill competes (as `deep-research` does with `research`), the description says "In this repo, prefer it over <built-in>", and `CLAUDE.md` gets a line saying the same.

## 3. Design

Decide and show the user in a few lines:

- **name**: kebab-case, ≤ 64 chars, no `anthropic`/`claude`. Prefer gerund form (`skill-building`, `processing-pdfs`). The folder name equals `name`.
- **description**: third person, what it does and then when to use it, starting with the repo prefix `catncockroach - `. Put the key use case first and keep it under 1,024 chars. Make it slightly **pushy**, since Claude tends to under-trigger skills.
- **Other frontmatter**: only the fields the job needs (see *frontmatter.md*). Common ones: `allowed-tools` for tools the skill runs every time, `argument-hint` for `/name <arg>` skills, and `context: fork` when the job is self-contained and should not see the chat.
- **Layout**: `SKILL.md` holds the steps every run needs. Push reference that only some branches need into `references/<topic>.md`, one level deep and linked from `SKILL.md`. Deterministic, fragile operations become `scripts/` that Claude *runs*. Output templates go in `assets/` or inline.

```
<name>/
├── SKILL.md          # steps + pointers (< 500 lines; aim far lower)
├── references/*.md   # read on demand
├── scripts/*         # executed, not read
└── assets/*          # templates/files used in output
```

## 4. Write

Follow *authoring.md*. In this repo:
- Instructions are in English. User-facing output templates (reports, notes) are in Vietnamese, with technical terms kept in English. `research` is the model.
- Every step ends on a **completion criterion** ("Done when..."), checkable where possible.
- Paths inside the skill use `${CLAUDE_SKILL_DIR}` or are relative to `SKILL.md`. Subagents get absolute paths.
- Put the most important instructions near the top. After compaction, only the start of a skill survives.

## 5. Validate

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validate.py .claude/skills/<name>
```

It checks the frontmatter (it must parse, plus name rules, the `catncockroach - ` prefix, length limits and unknown keys), body length, broken file links, nested references, and a contents section in long reference files. Fix every **ERROR**. Fix each **WARN** or justify it. Re-run until it exits 0.

## 6. Test-run

The writer of a skill is the worst judge of it (Claude A writes, Claude B tests). Do both checks:

1. **Behaviour.** Write 2–3 realistic prompts, the way the user would actually type them. Spawn one `general-purpose` subagent per prompt, in parallel: `Read <abs path>/SKILL.md and follow it to handle this request: "<prompt>". Save outputs under <scratchpad>/skill-test/<name>/<n>/. Report the steps you took and where the skill was unclear.` Read the outputs and the reports. Look for skipped steps, wrong files, and reference files that were never opened or opened every time.
2. **Triggering.** Write 5 should-trigger and 5 near-miss should-not-trigger prompts. Judge each one against the description as it would sit among the other skills. Sharpen the description wherever a prompt would go the wrong way.

Fix what you observed. Generalise each fix instead of patching it for one prompt, then re-validate. For rigorous evals (baselines, benchmarks, an automated description-optimisation loop), offer the built-in `anthropic-skills:skill-creator`.

Done when every test prompt produced the expected output without you intervening.

## 7. Deliver

- Update `CLAUDE.md` if the skill sets a repo-wide convention or overrides a built-in.
- Tell the user in Vietnamese: what the skill does, how to call it (`/name ...` or the trigger phrases), the files created, and what the test-run showed.
- Edits to an existing skill take effect immediately. A new top-level skills directory needs `/reload-skills` or a new session.
