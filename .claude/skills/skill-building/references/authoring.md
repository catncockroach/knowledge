# Authoring rules

From Anthropic's *Skill authoring best practices* (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), plus lessons from this repo.

## Contents
- Concise is key
- Degrees of freedom
- Descriptions
- Progressive disclosure
- Workflows, checklists, feedback loops
- Templates and examples
- Wording
- Scripts
- Anti-patterns
- Final checklist

## Concise is key

Claude is already very smart. Add only what it does not know: the repo's conventions, the reasons behind a choice, the gotchas no config file reveals. Challenge every paragraph: does it change behaviour compared with what Claude would do anyway? If not, delete the whole sentence rather than trimming it. A shorter skill is easier to keep correct.

## Degrees of freedom

Match specificity to how fragile the task is:

| Freedom | Form | Use when |
|---|---|---|
| High | Prose heuristics | Many valid approaches; the decision depends on context (reviews, research, writing) |
| Medium | Pseudocode, a template with parameters | A preferred pattern exists, but variation is fine |
| Low | An exact script, "run exactly this" | The task is fragile, consistency is critical, or the order is fixed (migrations, releases) |

Narrow bridge with cliffs on both sides → guardrails. Open field → give a direction and trust Claude.

## Descriptions

The description is the only part Claude sees before choosing a skill, often from 100+ candidates.
- **Third person**: "Builds reports from…", not "I can…" or "You can…".
- **What, then when**: the capability, then "Use when…" listing the distinct situations and the keywords users actually type. In this repo that means Vietnamese and English.
- One trigger per distinct case. Synonyms for the same case add tokens without adding reach.
- Front-load the key use case, because truncation cuts from the end.
- Make it slightly pushy ("…even if they don't say 'X'"), since skills tend to under-trigger.
- In this repo, start with `catncockroach - `.

## Progressive disclosure

Rank the material by how often a run needs it:
1. **SKILL.md steps**: what every run does, in order.
2. **SKILL.md reference**: short rules consulted during those steps.
3. **references/*.md**: material only some runs need. Link it from SKILL.md with the condition for reading it ("For tracked changes, read …").

Rules:
- Every reference file is linked directly from SKILL.md. Keep references **one level deep**: Claude may only skim files reached through another file.
- A reference file over 100 lines opens with a *Contents* list.
- Name files after their content (`form-validation.md`, not `doc2.md`). Organise by domain so a run loads only its own branch.
- Exception: a file written as a subagent's whole prompt (like `research/references/researcher.md`) may point to a shared sibling. The subagent reads it fully as its first step.

## Workflows, checklists, feedback loops

- Break a complex job into numbered steps. Each ends on a **completion criterion** ("Done when every sub-question has an answer or a stated gap"). A vague bound invites stopping too early. A demanding bound drives thoroughness.
- For long workflows, give a checklist that Claude copies into its reply and ticks off.
- **Feedback loop**: run the validator, fix, repeat until it passes. The validator can be a script or a checklist file. This is the single biggest quality lever.
- **Plan, validate, execute** for batch or destructive work: write the plan to a file, validate it, then apply it.
- For decision points, use a conditional workflow ("Creating new? → A. Editing? → B").

## Templates and examples

- Give an output template when the format matters. Say whether it is strict ("use exactly") or a default ("adapt as needed").
- When style matters, show 2–3 input→output examples. They convey style better than adjectives.

## Wording

- Use the imperative voice. Explain *why* a rule exists instead of stacking MUST/NEVER. Claude generalises from reasons, and all-caps is a sign the reasoning is missing.
- Use one term per concept throughout (always "field", never "field/box/element").
- State the positive target. A prohibition puts the unwanted behaviour into context. Keep a prohibition only as a hard guardrail, and pair it with what to do instead.
- **Leading words**: a single well-known word (*brief*, *tight*, *on target*), repeated, anchors behaviour more cheaply than a sentence of explanation.
- Leave out time-sensitive statements ("before August 2025…"). Put superseded material in an *Old patterns* section if it must stay.

## Scripts

- Make the intent clear: "Run `scripts/x.py`" (execute) or "See `scripts/x.py` for the algorithm" (read).
- **Solve, don't punt**: handle errors in the script, and print specific, actionable messages ("Field 'x' not found. Available: a, b").
- No voodoo constants: comment why each value is what it is.
- List dependencies and how to install them, and use forward-slash paths.
- Bundle a script whenever test runs show Claude writing the same helper code again and again.
- Refer to MCP tools by their fully qualified name (`mcp__server__tool` in Claude Code).

## Anti-patterns

- Offering many alternatives ("use A, or B, or C…"). Give one default plus one escape hatch.
- Explaining what Claude already knows (what a PDF is, how git works).
- Deep reference chains, or a dump of reference material inside SKILL.md.
- A description that says what the skill is but not when to use it.
- Overfitting to the test prompts. Fixes should generalise.

## Final checklist

**Core**
- [ ] The description says what the skill does and when to use it, with real trigger words, in third person, starting with `catncockroach - `
- [ ] SKILL.md body is under 500 lines, with the critical rules near the top
- [ ] Every step has a completion criterion
- [ ] Reference files are one level deep, linked with the condition for reading them, and have a contents list if over 100 lines
- [ ] Terminology is consistent, nothing is time-sensitive, examples are concrete

**Scripts (if any)**
- [ ] Errors are handled with specific messages, constants are justified, dependencies are listed
- [ ] Each script is marked as run or read, and is pre-approved via `allowed-tools` if it runs every time

**Testing**
- [ ] `scripts/validate.py` exits 0
- [ ] At least 2–3 realistic prompts were run by fresh subagents and their outputs reviewed
- [ ] Should-trigger and near-miss prompts were checked against the description
