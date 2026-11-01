# Learner questions

A foundations file is good when a learner can bring it any natural question about its topic and find the answer. This file says which questions to anticipate and how to answer them.

## Contents
- Question kinds
- Answer: concepts first, then the general rule
- Format in the file
- Examples

## Question kinds

For each file, go through these kinds and keep the questions that matter for its topic (at least 4 per file; the owner's own questions are added on top and never dropped to stay under a count):

| Kind | Typical wording (Vietnamese) | What the answer must give |
|---|---|---|
| Purpose | X là gì? X dùng để làm gì? | definition + the problem it solves |
| Cardinality | Một A có thể có nhiều B không? Bao nhiêu? | the exact relation (1–1, 1–n, 0..n) and why it is designed that way |
| Location | Thông tin Y nằm ở đâu trong X? X trả lời Y bằng cách nào? | the place (field, layer, step) and how to read it |
| Distinction | A khác B thế nào? Khi nào dùng A, khi nào dùng B? | the deciding criterion, not two separate definitions |
| Order and time | Cái gì xảy ra trước? Giá trị này của lúc nào? | the sequence or the point in time it refers to |
| Design reason | Vì sao thiết kế như vậy? | the trade-off the design chose |
| Boundary | Khi nào quy tắc này không đúng? Trường hợp đặc biệt? | the exceptions and how the domain handles them |

Questions the user asked in the conversation are mandatory entries. Keep their meaning and wording; only fix spelling and abbreviations ("1 log ocsf" → "Một log OCSF").

## Answer: concepts first, then the general rule

A learner's question names concepts, and the answer only lands if the reader knows them. A learner's question is also usually one instance of a wider question: answer the wider one, so the next instance is answered too. Each answer has these parts, in this order:

1. **Concepts**: briefly explain every concept the question names, plus any term the answer relies on that an entry-level reader may not know. One or two sentences each: what it is and what it is for. If the file defines it in depth elsewhere, keep this short and link there instead of repeating.
2. **General rule**: one sentence that holds for every case in the class. This is the answer the reader should remember.
3. **Applied to the case asked**: show how the rule answers the specific question, with the reason behind it.
4. **Boundary**: what looks like an exception and how the rule still holds, or what people confuse it with.

Test: if the reader changed the example in the question (another class, another protocol, another field), would the answer still tell them what happens? If not, it is not general enough. Second test: could a reader who skipped the rest of the file follow the answer? If a term in it is unexplained, add it to the concepts part.

## Format in the file

In the *Câu hỏi và trả lời* section of each topic file, the question stands alone on its own bold line. The answer starts on the **next line**, never on the same line as the question (not `**Câu hỏi?** trả lời`, not `1. **Câu hỏi?** trả lời`), and the whole answer is a blockquote.

```markdown
**<Câu hỏi, viết như người học hỏi>?**
> - **<Khái niệm A>**: <là gì, dùng để làm gì.>
> - **<Khái niệm B>**: <là gì, dùng để làm gì.>
>
> <Quy tắc tổng quát, một câu.> <Áp vào trường hợp được hỏi, kèm lý do.>
>
> <Ranh giới hoặc điểm hay nhầm.>

**<Câu hỏi tiếp theo>?**
> ...
```

- Every line of the answer starts with `>`; a blank line inside the answer is a bare `>`. Leave one empty line between an answer and the next question.
- A question about a single concept ("X là gì?") puts its definition in the concepts part and spends the rest on purpose, mechanism in one or two sentences, and boundary.
- Tables, short lists and short code snippets may sit inside the blockquote (prefix each line with `> `) when they make a distinction or mechanism clearer.
- Aim for an answer a reader can learn from without re-reading the file, usually 4–12 lines. If it needs a long mechanism, put the mechanism in *Cách hoạt động* and summarise it with a link.
- A question asking the reader to do something (write a query, implement an algorithm) still gets an answer: the approach plus a short solution.

## Examples

These show the *shape* of a good answer. Never copy them into a file as content: derive each answer from the topic's own sources, which usually say more than the example does.

**Narrow and inline (avoid)**

```markdown
**Một log OCSF có thể thể hiện nhiều class không?** Không, log đăng nhập chỉ là class Authentication.
```

It answers one case, the reader still cannot tell what happens to an alert, a DNS log or a firewall log, "class" is never explained, and the answer sits on the question's line.

**General, concepts first (target)**

```markdown
**Một log OCSF có thể thể hiện nhiều class không?**
> - **Class**: khuôn mẫu cho một loại sự việc (Authentication, Network Activity, Detection Finding...), quy định event có những field nào. Dùng để mọi nguồn log mô tả cùng loại sự việc theo cùng một cấu trúc.
> - **Profile**: một nhóm field dùng chung, gắn thêm vào class khi sự việc có khía cạnh đó (vd `security_control` cho phán quyết của control bảo mật).
> - **Extension**: phần mở rộng schema do tổ chức hay vendor định nghĩa thêm class hoặc field.
>
> Một event OCSF có ba trục độc lập: đúng *một* class (nên đúng một `activity_id`, một `type_uid`, một category), *0..n* profile, *0..n* extension. Một lần đăng nhập là một event Authentication. Sự việc có khía cạnh thứ hai (file bị antivirus chặn) vẫn là một class, khía cạnh kia đi vào profile `security_control`.
>
> Ranh giới: một bản ghi nguồn gói nhiều sự việc thì tách thành nhiều event; kết luận rút ra từ nhiều event là một event mới thuộc class Finding. Alert không nhất thiết là Finding: alert của control tại chỗ là event hoạt động áp `security_control` với `is_alert`.
```

It explains the three terms the answer depends on, answers the whole family (how many classes, profiles, extensions; what happens to multi-faceted logs, batches and alerts), and every claim traces to the spec.

**Narrow (avoid)**

```markdown
**IP trong log firewall nằm ở đâu?**
> Ở `src_endpoint.ip`.
```

**General (target)**

```markdown
**Thông tin về một máy nằm ở đâu trong event?**
> - **Object thực thể**: nhóm field mô tả một đối tượng (máy, người dùng, tiến trình), tái sử dụng ở nhiều class.
> - **Vai**: vị trí của đối tượng trong sự việc: nơi ghi nhận, nguồn, đích.
>
> Thông tin về máy nằm ở object thực thể theo *vai* của máy trong sự việc: máy ghi nhận ở `device`, hai đầu kết nối ở `src_endpoint` và `dst_endpoint`. Vì vậy với log firewall, firewall là `device` còn IP người dùng nằm ở `src_endpoint.ip`.
>
> Ranh giới: cùng một máy có thể là `device` ở event này và `src_endpoint` ở event khác.
```
