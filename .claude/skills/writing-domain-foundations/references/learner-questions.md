# Learner questions

A foundations file is good when a learner can bring it any natural question about its topic and find the answer. This file says which questions to anticipate and how to answer them.

## Contents
- Question kinds
- Answer from the general rule
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

## Answer from the general rule

A learner's question is usually one instance of a wider question. Answer the wider one, so the next instance is answered too:

1. **General rule**: one sentence that holds for every case in the class. This is the answer the reader should remember.
2. **Applied to the case asked**: show how the rule answers the specific question.
3. **Boundary**: what looks like an exception and how the rule still holds, or what people confuse it with.

Test: if the reader changed the example in the question (another class, another protocol, another field), would the answer still tell them what happens? If not, it is not general enough.

## Format in the file

In the *Câu hỏi và trả lời* section of each topic file:

```markdown
**<Câu hỏi, viết như người học hỏi>?**
<Quy tắc tổng quát, một câu.> <Áp vào trường hợp được hỏi.> <Ranh giới hoặc điểm hay nhầm.>
```

Keep each answer to a short paragraph. A distinction along several dimensions may carry a small comparison table inside the answer. If an answer needs a long mechanism, put the mechanism in *Cách hoạt động* and answer briefly with a link to it.

## Examples

These show the *shape* of a good answer. Never copy them into a file as content: derive each answer from the topic's own sources, which usually say more than the example does.

**Narrow (avoid)**
> **Một log OCSF có thể thể hiện nhiều class không?**
> Không, log đăng nhập chỉ là class Authentication.

It answers one case, and the reader still cannot tell what happens to an alert, a DNS log or a firewall log.

**General (target)**
> **Một log OCSF có thể thể hiện nhiều class không?**
> Một event OCSF có ba trục độc lập: đúng *một* class (nên đúng một `activity_id`, một `type_uid`, một category), *0..n* profile, *0..n* extension. Một lần đăng nhập là một event Authentication. Sự việc có khía cạnh thứ hai (file bị antivirus chặn) vẫn là một class, khía cạnh kia đi vào profile `security_control`. Ranh giới: một bản ghi nguồn gói nhiều sự việc thì tách thành nhiều event; kết luận rút ra từ nhiều event là một event mới thuộc class Finding. Alert không nhất thiết là Finding: alert của control tại chỗ là event hoạt động áp `security_control` với `is_alert`.

It answers the whole family (how many classes, profiles, extensions; what happens to multi-faceted logs, batches and alerts), and every claim traces to the spec.

**Narrow (avoid)**
> **IP trong log firewall nằm ở đâu?**
> Ở `src_endpoint.ip`.

**General (target)**
> **Thông tin về một máy nằm ở đâu trong event?**
> Ở object thực thể theo *vai* của máy trong sự việc: máy ghi nhận ở `device`, hai đầu kết nối ở `src_endpoint` và `dst_endpoint`. Vì vậy với log firewall, firewall là `device` còn IP người dùng nằm ở `src_endpoint.ip`. Cùng một máy có thể là `device` ở event này và `src_endpoint` ở event khác.
