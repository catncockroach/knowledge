---
name: grill-me
description: "catncockroach - Interviews the user in rounds through the question tool (pick an option or type a free answer) to pin down the problem they actually need solved: goal, context, scope, constraints, what done looks like. Use when the user says grill me / hỏi lại tôi / làm rõ giúp tôi, when a request is too vague to act on without guessing, or when another skill (such as research) needs open points settled with the user before it starts. Not for quizzing or testing the user's knowledge."
argument-hint: "[vấn đề cần làm rõ]"
---

# Grill me

You interview the user until the problem is **pinned down**: nothing important left to guess. The *decisions* are the user's; *facts* are your job. Never ask what you can look up in the repo, the environment or the conversation.

## Mode

Read the arguments and the conversation, then pick a mode:

- **Called**: another skill invoked you and named the points it needs settled (for example research's purpose, scope and depth). Ask only about those points. Add another point only when a named one cannot be settled without it. Use at most 2 rounds; close whatever is still open after that with your best assumption. Skip the confirmation round. Show the *Bản chốt* in one message, then the caller continues its own steps in the same conversation, using the *Bản chốt* under its own field names.
- **Standalone**: the user asked to be grilled, or typed `/grill-me <vấn đề>`. Be **relentless** about **material** decisions, the ones that change what gets built, researched or written. Keep going round after round until no material decision is open, then confirm. Details that would not change the direction (file names, tags, wording) are not worth a question: close them with a sensible default under *Giả định*.

## 1. Map the problem

Before asking anything, draft privately what you already know and what is open. Work through the branches that matter for this problem; skip the ones that clearly do not:

| Branch | What it settles |
|---|---|
| **Vấn đề thật** | The need behind the request: why now, what goes wrong if nothing is done |
| **Kết quả** | What "done" looks like: deliverable, format, who will use it |
| **Bối cảnh** | Current state, what was already tried, what the user already knows |
| **Phạm vi** | What is in and what is deliberately out |
| **Ràng buộc** | Time, budget, tools, language, level of depth or rigour |
| **Ưu tiên** | What wins when two goals conflict (speed vs depth, breadth vs focus) |

Each open point is a node. Node A is a **prerequisite** of node B when A's answer would change B's options: for example, the format of the deliverable cannot be settled before the goal is. The **frontier** is every open node whose prerequisites are already settled, meaning the questions you can ask *now* without guessing at answers you have not heard.

## 2. Ask a round

Ask the whole frontier in one round, through the question tool, following *Asking* below. Then wait for the answers.

Write a short line above the call: what you already understood and why these questions matter. Long material (a draft outline, a list of candidate topics) belongs in your message or a file. The question only asks about it.

## 3. Between rounds

Fold the answers into the map:
- Each settled node pushes the frontier outward.
- An "Other" answer, or a choice with a note, is a partial answer: settle what is clear and put what it opened on the next frontier.
- If an answer contradicts a decision settled earlier, reopen that node and ask about it again in the next round, stating the conflict. Never silently overwrite a settled decision.
- When a node needs a fact, look it up yourself (read files, search). Ask the rest of the frontier meanwhile, since only nodes downstream of that fact need to wait.

Recompute the frontier and ask the next round. If the user says "đủ rồi", "làm luôn" or similar, stop at once: close every open node with your best assumption, and mark it as an assumption.

Done when the frontier is empty (Standalone), or when the caller's points are settled (Called).

## 4. Bản chốt

Write the outcome in Vietnamese:

```markdown
## Bản chốt: <vấn đề, một dòng>

- **Vấn đề thật:** <...>
- **Kết quả mong muốn:** <deliverable, format, thế nào là xong>
- **Bối cảnh:** <...>
- **Phạm vi:** <...> · **Ngoài phạm vi:** <...>
- **Ràng buộc:** <...>
- **Ưu tiên khi đánh đổi:** <...>
- **Đã chốt:** <câu hỏi → câu trả lời, mỗi dòng một quyết định>
- **Giả định / còn để ngỏ:** <điều chưa hỏi hoặc user bỏ qua, kèm giả định đang dùng>
```

Leave out the lines that do not apply. The *Bản chốt* stays in the chat; save it to a file only if the user asks (a calling skill saves it in its own files).

**Standalone**: ask one last question through the question tool: "Bản chốt này đúng chưa?", with the options "Đúng, chốt (Recommended)" and "Cần sửa vài điểm". "Other" lets the user type corrections. Treat the problem as settled only once the user confirms; until then, do not start solving it. **Called**: show the *Bản chốt* and let the caller continue.

## Asking

**Question tool first.** Use `AskUserQuestion` in Claude Code. On another host, use whatever structured question or choice tool it lists. The user should answer by clicking, not by reading a wall of text.

- Each call holds 1–4 questions. A bigger frontier goes out as consecutive calls in the same round, most decisive questions first. Aim for at most about 6 questions per round, and push the less decisive ones to the next round.
- Each question has a short `header` (≤ 12 chars) and 2–4 mutually exclusive options. Each option's `description` states its consequence.
- Options are your concrete best guesses at what the user means, drawn from the context, never vague placeholders. Put the one you recommend first, with a label ending in "(Recommended)". With `multiSelect`, mark every option you recommend. When the context is too thin to have a real preference, recommend the most common reading and say so in its description. The tool adds "Other" for free text, so do not add one yourself.
- Use `multiSelect` only when the options genuinely combine (which constraints apply, which sub-topics to cover).
- Use `preview` only on options the user must compare as concrete artefacts side by side: outlines, sample formats, a draft structure.
- Write the context line, the questions and the options in Vietnamese, with technical terms in English. Each question asks one thing.

**Text fallback.** Ask in plain text only when no question tool is available, or when the answer cannot be listed as options (a file path, a description of a process). Still number the questions and give a recommendation:

```
❓ **Q1 – <tiêu đề>**: <câu hỏi, kèm các lựa chọn nếu có>
➡️ Đề xuất: <đáp án khuyến nghị>
```
