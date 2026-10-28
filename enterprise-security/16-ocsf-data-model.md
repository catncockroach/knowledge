# OCSF data model

> OCSF mô tả mọi bản ghi bảo mật bằng một cây phân loại (category → class → activity) cùng các object dùng chung; nhờ vậy, mọi event dù đến từ nguồn nào cũng được hiểu bằng cùng một cách đọc.

## Tại sao cần biết
Biết cấu trúc của schema là biết mỗi thông tin nằm ở đâu: máy, người, hành động, kết quả, ngữ cảnh. Đây là nền để hiểu cách một event được diễn giải, cách tài sản xuất hiện trong log ([17-asset-management.md](17-asset-management.md)) và cách ngữ cảnh được gắn vào event ([18-asset-context-and-enrichment.md](18-asset-context-and-enrichment.md)).

## Khái niệm cốt lõi
- **Category → class → activity**:
  - *Category* là nhóm lớn: System Activity (1), Findings (2), IAM (3), Network Activity (4), Discovery (5), Application Activity (6), Remediation (7).
  - *Class* là một loại sự kiện, `class_uid = category_uid × 1000 + n`. Ví dụ Process Activity `1007`, Detection Finding `2004`, Authentication `3002`, Network Activity `4001`, Device Inventory Info `5001`.
  - *Activity* là hành động trong class (`activity_id`). Ví dụ Process Activity có Launch, Terminate, Inject; Authentication có Logon, Logoff.
  - **`type_uid = class_uid × 100 + activity_id`** định danh duy nhất "loại + hành động" trên toàn schema, vd Logon = `300201`.
- **Ba kiểu bản ghi**:
  - *Activity*: một việc đã xảy ra (process chạy, đăng nhập, kết nối mạng).
  - *Finding*: một kết luận về việc đã xảy ra (alert, lỗ hổng, vi phạm tuân thủ).
  - *Discovery/inventory*: trạng thái của một thứ tại một thời điểm (máy, phần mềm, user). OCSF chứa cả ba kiểu, nên log, alert và dữ liệu tài sản cùng nằm trong một mô hình.
- **Attribute và object**: attribute là field có tên cố định trong một dictionary chung, cùng tên thì cùng nghĩa ở mọi class. Object là nhóm attribute lồng nhau dùng lại được. Các object quan trọng:
  - `device`: máy nơi sự kiện được ghi nhận (observer);
  - `src_endpoint`, `dst_endpoint`: nguồn và đích;
  - `actor`: chủ thể (user, process, session);
  - `user`, `process`, `file`, `metadata`.
- **Requirement và enum**: attribute có mức required, recommended, optional. Giá trị liệt kê đi theo cặp `_id` + caption (`severity_id 4` / `High`); `0` là Unknown, `99` là Other.
- **Profile và extension**: *profile* gắn thêm một nhóm attribute vào class khi ngữ cảnh phù hợp (`host` thêm `device` và `actor`; `security_control` thêm hành động và kết luận của control). *Extension* thêm class, object, attribute riêng mà không sửa schema lõi.
- **Các field bao quanh nội dung**:
  - `metadata`: xuất xứ của bản ghi (sản phẩm nguồn, phiên bản schema, mã event gốc, thời gian gốc);
  - `observables[]`: danh sách phẳng các thực thể đáng chú ý (IP, hostname, hash, user) để pivot;
  - `enrichments[]`: ngữ cảnh lấy từ nguồn ngoài;
  - `unmapped`: field của nguồn không có chỗ trong schema;
  - `raw_data`: log gốc nguyên văn.

## Cách hoạt động
Mỗi event trả lời cùng một bộ câu hỏi, và mỗi câu có chỗ cố định trong schema:

| Câu hỏi | Nơi trả lời |
|---|---|
| Loại gì? | `class_uid`, `activity_id` → `type_uid` |
| Khi nào? | `time` (epoch milliseconds, UTC) |
| Kết quả? | `status_id`; với control: `action_id`, `disposition_id`; `severity_id` |
| Ai? | `actor` (với IAM thêm `user` là tài khoản bị tác động) |
| Ở đâu? | `device` (observer), `src_endpoint` → `dst_endpoint` |
| Vào cái gì? | object riêng của class: `process`, `file`, `dns_query`, `finding_info`... |
| Bối cảnh? | `enrichments`, thuộc tính tổ chức trong `device` |
| Tin được không? | `metadata`, `raw_data` |

Đọc lần lượt các câu trên cho ra một câu mô tả hoàn chỉnh về event. Các event nối với nhau thành câu chuyện qua khóa chung: cùng process (`process.uid`), cùng phiên (`session.uid`), cùng máy (`device.uid`), hoặc liên kết do finding chỉ ra (`finding_info.related_events`).

## Ví dụ
Một alert EDR đã chuẩn hóa, các field chính:

```
type_uid=200401 (Detection Finding: Create)  time=2025-10-28 08:00 UTC
severity_id=4 (High)  disposition_id=2 (Blocked)  status_id=1 (New)
actor.process.name=winword.exe  actor.user.name=lan.nguyen
device.hostname=WS-0412  device.type_id=3 (Laptop)
finding_info.title="Encoded PowerShell spawned by Office"  attacks=T1059.001
```

Đọc theo bảng: *"08:00, winword.exe của user lan.nguyen trên laptop WS-0412 sinh PowerShell mã hóa (T1059.001), EDR đã chặn; alert mức High, chưa xử lý."* Người đọc không cần biết đó là EDR của hãng nào.

## Hiểu nhầm thường gặp
- **"OCSF là một định dạng file"**: OCSF là mô hình dữ liệu; có thể biểu diễn bằng JSON, Parquet hay bảng.
- **"`device` và `src_endpoint` là một"**: `device` là nơi ghi nhận; với log firewall, firewall là `device`, máy người dùng là `src_endpoint`.
- **"`status_id` nghĩa như nhau ở mọi class"**: ở activity là thành công/thất bại; ở finding là trạng thái xử lý.
- **"Phải điền hết field"**: mỗi class có rất nhiều attribute; bản ghi chỉ điền phần bắt buộc và phần nguồn cung cấp.

## Liên quan
- [15-security-data-normalization.md](15-security-data-normalization.md): vì sao cần schema chung.
- [02-threats-and-attack-lifecycle.md](02-threats-and-attack-lifecycle.md): ATT&CK technique trong finding.
- [17-asset-management.md](17-asset-management.md): tài sản xuất hiện trong event ra sao.
