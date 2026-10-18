# Writer

Synthesise the notes into a report that answers the brief's main question. The brief is the yardstick: anything in the notes that does not help answer the main question or a sub-question stays out, however interesting it is.

Read `sources.md` (in this folder) for the citation rules.

## Steps

1. Read `brief.md`, every file in `notes/`, and the earlier report if *Kế thừa* names one. Where the new notes and the earlier report disagree, the new notes win, and the report must stand on its own.
2. Decide the **answer** first: one or two sentences that reply to the main question directly. Then plan headings that lead the reader to it.
3. Write `report.md` with the template below and save it.

## Template

```markdown
---
title: <tiêu đề>
date: YYYY-MM-DD
question: <câu hỏi chính>
tags: [<3–6 tag, chữ thường, tiếng Việt không dấu hoặc thuật ngữ gốc>]
---

# <Tiêu đề: 4–10 từ, nói lên phát hiện chính, không chỉ tên chủ đề>

> **Câu hỏi:** <...> · **Ngày:** YYYY-MM-DD · **Phạm vi:** <...>

## Tóm tắt

<Một đoạn 4–8 câu. Câu đầu trả lời thẳng câu hỏi chính, rồi mở rộng ra ý nghĩa, bối cảnh và mức độ chắc chắn. Người đọc dừng ở đây vẫn nắm được kết luận.>

**Điểm chính**
- <3–6 ý, mỗi ý một dòng, có trích dẫn [n]>

## <Heading dẫn đường cho câu hỏi phụ / chủ đề 1>
<...>

## <...>  (3–6 mục nội dung tổng cộng)

## Các nguồn bất đồng ở đâu
<chỉ viết khi có mâu thuẫn đáng kể: ai nói gì, vì sao lệch, nên tin bên nào và vì sao>

## Kết luận và hàm ý
<1–2 đoạn: điều rút ra mới, hàm ý cho mục đích trong brief. Không tóm tắt lại.>

## Chưa kiểm chứng được
- <khoảng trống, và các truy vấn đã thử>

## Nguồn
[1] Tiêu đề — Tác giả/Nhà phát hành, ngày (bậc N). URL
```

## Writing rules

- **Signpost headings**: a reader who skims only the headings should still get the argument.

  | Tốt | Kém |
  |---|---|
  | "Ngủ dưới 6 tiếng làm giảm 20–30% hiệu suất nhận thức" | "Ảnh hưởng của giấc ngủ" |
  | "Châu Âu phạt theo doanh thu, Mỹ phạt theo vụ việc" | "So sánh quy định" |

- Write dense, flowing prose. Each paragraph advances the argument instead of listing facts. **Bold** the key numbers and facts so they are easy to scan. Use bullets only in *Điểm chính*, *Chưa kiểm chứng được* and *Nguồn*.
- Use a table when comparing 3 or more subjects on 2 or more criteria.
- Interpret what the data means: put numbers in context (compared with what, measured when, on what sample).
- Take a position when the evidence is enough. State the uncertainty plainly where it is not. Present the strongest version of the opposing view.
- Cite at the important points: every number, every quote, every claim a reader would want to check. A claim in the notes without a URL does not go into the report.
- Every inference starts with **Nhận định:**.
- Fit length to the question: a deep question gets a long report, a narrow one gets a short report. Focused beats exhaustive.
- Renumber the citations in order of first appearance, and merge duplicate sources.
