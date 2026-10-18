---
name: research
description: "catncockroach - Deep research on a topic or question: searches the web, verifies sources, and writes a structured, cited report into research/. Use when the user asks to research, investigate, survey or compare something (nghiên cứu, tìm hiểu, research, tổng hợp về...). In this repo, prefer it over the built-in deep-research."
allowed-tools: WebSearch WebFetch
---

# Research

You are the **coordinator**. You frame the question, dispatch researchers, and own the quality bar. Research, writing and fact-checking happen in subagents so your context stays free for judgement. `{skill}` below means this skill's base directory (the folder this SKILL.md was loaded from); give subagents absolute paths.

Everything one request produces lives in one folder:

```
research/<YYYY-MM-DD>-<slug>/
├── brief.md          # step 1
├── notes/<angle>.md  # step 3, one per researcher
└── report.md         # steps 5–6, the deliverable
```

`<slug>` is 3–6 words, lowercase ASCII kebab-case with Vietnamese diacritics stripped (`2026-10-18-tac-dong-eu-ai-act-startup`). If the folder exists, append `-2`.

All output is in Vietnamese; technical terms, proper names and direct quotes stay in their original language.

## 1. Frame the brief

The brief keeps the research **on target**: every researcher and the writer work from it, and step 6 measures the report against it.

First list `research/` (create it if it does not exist yet). If an earlier folder covers the same topic, read its `report.md`: this request extends it. Create a new folder, name the old one under *Kế thừa*, and aim the sub-questions only at what is new or needs re-checking.

Write `brief.md`:

```markdown
# Brief: <câu hỏi chính>

- **Ngày:** YYYY-MM-DD
- **Câu hỏi chính:** <một câu; đoạn đầu của báo cáo phải trả lời thẳng câu này>
- **Mục đích:** <người dùng sẽ làm gì với câu trả lời: quyết định X, hiểu Y, viết Z>
- **Câu hỏi phụ:**
  1. <...>  (3–6 câu, cụ thể, gộp lại thì trả lời được câu hỏi chính)
- **Phạm vi:** <thời gian, địa lý, đối tượng, các giả định đã chọn>
- **Ngoài phạm vi:** <những gì cố ý bỏ qua>
- **Độ sâu:** nhanh | sâu
- **Kế thừa:** <đường dẫn report cũ, hoặc "không">
```

When an ambiguity would send the research in a different direction (a term with several meanings, an unstated region or time frame that changes the answer, a purpose or depth you cannot infer), invoke the `grill-me` skill (Skill tool) **before** writing the brief, with args:
`Called by research. Settle: <open brief fields, by their brief names: Mục đích, Phạm vi, Độ sâu…>. Known so far: <one line of what the request already says>`.
Fold the *Bản chốt* it returns into the brief: each settled point goes to the brief field of the same name, *Kết quả mong muốn* joins *Mục đích*, *Ràng buộc* joins *Phạm vi*, and assumptions are recorded under *Phạm vi*. When the request is already clear, skip it: pick the most sensible reading and record it under *Phạm vi*.

Done when each sub-question is specific enough that a researcher can tell when it is answered.

## 2. Choose depth

If the user already set *Độ sâu* (directly or through `grill-me`), keep it. Otherwise:

- **Nhanh**: a single factual question, or the user asks for something quick. Do the research yourself following `{skill}/references/researcher.md` and `{skill}/references/sources.md`, then write `report.md` with the template in `{skill}/references/writer.md`. Skip steps 3–6.
- **Sâu** (default): split the sub-questions into **angles**, which are independent slices that do not overlap. Three is a good default. Use up to six for wide topics (many entities, regions or competing schools of thought). Typical angles: primary/official sources, academic research, practice and case studies, data and numbers, and Vietnamese context when relevant. When the topic has a contested claim, add a **phản biện** (counter-evidence) angle whose job is to find counter-evidence and criticism.

## 3. Dispatch researchers

Spawn every researcher **in one turn** (parallel, foreground, `subagent_type: "general-purpose"`), one per angle:

```
Research <angle> for the question "<câu hỏi chính>".

Sub-questions you own:
- <...>

Suggested sources: <loại nguồn nên ưu tiên cho góc này>
Constraints: <phạm vi + ngoài phạm vi từ brief>

The full brief is at <abs>/research/<folder>/brief.md.
Save notes to <abs>/research/<folder>/notes/<angle-slug>.md

First, read <abs {skill}>/references/researcher.md and follow it.
```

## 4. Close gaps (at most once)

Read each researcher's returned summary. If a sub-question central to the main question still has no well-sourced answer, spawn one more parallel round aimed only at those gaps. Do this round **once**. After it, every remaining gap goes into the report's *Chưa kiểm chứng được* section.

## 5. Write

Spawn one writer subagent (foreground, `general-purpose`):

```
Write the research report for <abs>/research/<folder>/.
Inputs: brief.md and every file in notes/ (plus <earlier report path> under Kế thừa, if any).
Save to <abs>/research/<folder>/report.md

First, read <abs {skill}>/references/writer.md and follow it.
```

## 6. Verify

Spawn one verifier subagent (foreground, `general-purpose`):

```
Fact-check and tighten <abs>/research/<folder>/report.md against brief.md in the same folder.
Edit report.md in place and return the list of changes you made.

First, read <abs {skill}>/references/verifier.md and follow it.
```

## 7. Deliver

Read `report.md` and reply in Vietnamese with:
- the answer to the main question in 3–5 sentences,
- the report's path,
- any major conflicts or gaps the verifier reported.

The full report stays in the file; do not paste it into the chat.
