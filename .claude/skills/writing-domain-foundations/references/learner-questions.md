# Learner questions

A foundations file is good when a learner can bring it any natural question about its topic and find the answer. This file says which questions to anticipate and how to answer them.

## Contents
- Question kinds
- Answer from the general rule
- Format in the file
- Examples

## Question kinds

For each file, go through these kinds and keep the questions that matter for its topic (usually 4–8 per file):

| Kind | Typical wording (Vietnamese) | What the answer must give |
|---|---|---|
| Purpose | X là gì? X dùng để làm gì? | definition + the problem it solves |
| Cardinality | Một A có thể có nhiều B không? Bao nhiêu? | the exact relation (1–1, 1–n, 0..n) and why it is designed that way |
| Location | Thông tin Y nằm ở đâu trong X? X trả lời Y bằng cách nào? | the place (field, layer, step) and how to read it |
| Distinction | A khác B thế nào? Khi nào dùng A, khi nào dùng B? | the deciding criterion, not two separate definitions |
| Order and time | Cái gì xảy ra trước? Giá trị này của lúc nào? | the sequence or the point in time it refers to |
| Design reason | Vì sao thiết kế như vậy? | the trade-off the design chose |
| Boundary | Khi nào quy tắc này không đúng? Trường hợp đặc biệt? | the exceptions and how the domain handles them |

Questions the user asked in the conversation are mandatory entries, phrased the way they asked them.

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

Keep each answer to a short paragraph. If an answer needs a long mechanism, put the mechanism in *Cách hoạt động* and answer briefly with a link to it.

## Examples

**Narrow (avoid)**
> **Một log OCSF có thể thể hiện nhiều class không?**
> Không, log đăng nhập chỉ là class Authentication.

It answers one case, and the reader still cannot tell what happens to an alert, a DNS log or a firewall log.

**General (target)**
> **Một log OCSF có thể thể hiện nhiều class không?**
> Mỗi event OCSF là đúng một bản ghi của một class: một `class_uid`, một `activity_id`, và vì `class_uid` mã hóa category nên cũng đúng một `category_uid`. Một lần đăng nhập vì thế là một event Authentication với activity Logon. Một log nguồn có nhiều khía cạnh (vừa là truy cập file vừa bị antivirus chặn) vẫn là một class; khía cạnh còn lại được thêm bằng profile (`security_control`), không bằng class thứ hai. Kết luận rút ra từ nhiều event (một alert của SIEM) là một event riêng thuộc class Finding, nối về các event gốc.

**Narrow (avoid)**
> **IP trong log firewall nằm ở đâu?**
> Ở `src_endpoint.ip`.

**General (target)**
> **Thông tin về một máy nằm ở đâu trong event?**
> Ở object thực thể theo *vai* của máy trong sự việc: máy ghi nhận ở `device`, hai đầu kết nối ở `src_endpoint` và `dst_endpoint`. Vì vậy với log firewall, firewall là `device` còn IP người dùng nằm ở `src_endpoint.ip`. Cùng một máy có thể là `device` ở event này và `src_endpoint` ở event khác.
