# OCSF event anatomy

> Mọi bản ghi OCSF gồm cùng những nhóm field: phân loại, thời gian, kết quả, các thực thể theo vai trò, nội dung riêng của class, kết luận của control hay finding, chỉ mục thực thể (`observables`), ngữ cảnh (`enrichments`), xuất xứ (`metadata`) và phần dự phòng (`unmapped`, `raw_data`). Biết mỗi nhóm dùng để làm gì là đọc được mọi event theo một trình tự cố định.

## Tại sao cần biết
[16-ocsf-data-model.md](16-ocsf-data-model.md) mô tả khung của schema; file này mở một bản ghi cụ thể ra xem bên trong. Mỗi nhóm field trả lời một câu hỏi mà analyst, rule hay hệ thống tự động đều phải hỏi. Các phần về tài sản ([18](18-asset-inventory-and-profile.md), [19](19-building-asset-profiles-from-events.md)) dựa trực tiếp vào nhóm *thực thể*, *enrichments* và *metadata* ở đây.

## Khái niệm cốt lõi

### Phân loại
- **Field**: `category_uid`, `class_uid`, `activity_id`, `type_uid` (kèm caption `class_name`, `activity_name`, `type_name`).
- **Dùng để**: trả lời "đây là loại sự việc gì", và quyết định phần còn lại của bản ghi chứa những field nào.

### Thời gian
- **Field**: `time` (thời điểm sự việc), `start_time`/`end_time` và `count` (cho bản ghi gộp nhiều lần xảy ra), `duration`, `timezone_offset`.
- **Dùng để**: sắp xếp, dựng timeline, tính cửa sổ thời gian cho tương quan. Tất cả là epoch milliseconds UTC nên so được giữa các nguồn.

### Kết quả và mức độ
- **Field**:
  - `status_id` (`status`, `status_code`, `status_detail`): ở class hoạt động là thành công/thất bại; ở finding là trạng thái xử lý (New, In Progress, Suppressed, Resolved...);
  - `severity_id`: mức nghiêm trọng theo đánh giá của nguồn (0 Unknown, 1 Informational, 2 Low, 3 Medium, 4 High, 5 Critical, 6 Fatal).
- **Dùng để**: phân biệt một lần đăng nhập thành công với thất bại (cùng `type_uid`), và xếp mức nghiêm trọng theo một thang chung.

### Thực thể theo vai trò
Mỗi object thực thể nằm ở một *vai*, và vai quyết định nghĩa:

| Object | Vai | Dùng để |
|---|---|---|
| `device` | máy nơi sự việc được ghi nhận (observer) | biết sự việc xảy ra trên máy nào; gắn ngữ cảnh tài sản |
| `actor` | chủ thể gây ra hành động: `actor.user`, `actor.process`, `actor.session` | biết ai/cái gì làm |
| `user` | trong class IAM: tài khoản *bị* tác động (đăng nhập vào, bị đổi mật khẩu) | tách người làm với tài khoản bị làm |
| `src_endpoint`, `dst_endpoint` | nguồn và đích của kết nối, của lần xác thực | dựng quan hệ giữa các máy |

Cùng một máy có thể là `device` trong event này và `src_endpoint` trong event khác; đọc sai vai là gán sự việc cho sai máy.

### Nội dung riêng của class
- **Field**: object đặc thù: `process` và `parent_process` (Process Activity), `file` (File System Activity), `query`/`answers` (DNS Activity), `http_request` (HTTP Activity), `connection_info` và `traffic` (Network Activity), `logon_type_id`, `auth_protocol_id`, `is_mfa` (Authentication)...
- **Dùng để**: mô tả đối tượng bị tác động và chi tiết của hành động.

### Kết luận của control (profile `security_control`)
- **Field**: `action_id` (Allowed, Denied...), `disposition_id` (Allowed, Blocked, Quarantined, Isolated, Detected, Logged...), `is_alert`, `risk_level_id`, `confidence_id`, `policy`, `firewall_rule`, `malware`.
- **Dùng để**: biết control đã *làm gì* với sự việc: chặn, cách ly hay chỉ ghi nhận. Cùng một hành vi, đã bị chặn và chưa bị chặn là hai mức rủi ro khác nhau.

### Nội dung của finding
Với class thuộc category Findings (vd Detection Finding `2004`):
- `finding_info`: `uid`, `title`, `desc`, `analytic` (rule/logic sinh ra finding), `attacks` (tactic/technique ATT&CK), `related_events` (các event làm bằng chứng), `first_seen_time`/`last_seen_time`;
- `evidences`: bằng chứng có cấu trúc (process, file, kết nối...);
- `resources`: tài nguyên bị ảnh hưởng, kèm `criticality_id`;
- `confidence_id`, `risk_level_id`, `impact_id`.
- **Dùng để**: nối một kết luận về các event gốc và về kỹ thuật tấn công, phục vụ triage và điều tra.

### `observables[]`: chỉ mục thực thể
- **Là gì**: danh sách phẳng các thực thể đáng chú ý trong bản ghi, mỗi phần tử gồm `name` (đường dẫn field, vd `src_endpoint.ip`), `type_id` (1 Hostname, 2 IP Address, 3 MAC Address, 4 User Name, 5 Email Address, 6 URL String, 7 File Name, 8 Hash, 9 Process Name, 20 Endpoint, 21 User, 24 File, 25 Process...), `value`, và có thể có `reputation`.
- **Dùng để**: pivot và tra cứu mà không cần biết class. "Mọi bản ghi có IP X" là một truy vấn trên `observables`, bất kể IP nằm ở `src_endpoint`, `dst_endpoint` hay trong câu trả lời DNS. Đây cũng là chỗ đối chiếu với threat intel.

### `enrichments[]`: ngữ cảnh bổ sung
- **Là gì**: thông tin lấy từ nguồn ngoài, gắn vào một field của bản ghi. Mỗi phần tử gồm `name` (field được làm giàu), `value` (giá trị của field đó), `type` (vd `location`, `asset`), `data` (nội dung ngữ cảnh), `provider`, `created_time`.
- **Dùng để**: thêm ngữ cảnh mà nguồn log không có (vị trí địa lý của IP, thông tin tài sản, danh tiếng), *và* giữ rõ ngữ cảnh đó đến từ đâu, lúc nào, tách khỏi dữ liệu nguồn báo.

### `metadata`: xuất xứ của bản ghi
| Field | Dùng để |
|---|---|
| `version` | biết bản ghi theo phiên bản schema nào |
| `product` (tên, vendor, phiên bản) | biết nguồn nào sinh ra bản ghi; cũng cho biết máy được *cảm biến nào* nhìn thấy |
| `event_code` | giữ mã sự việc gốc (vd Windows `4625`) để đối chiếu tài liệu của nguồn |
| `original_time` | giữ chuỗi thời gian gốc trước khi chuẩn hóa |
| `uid`, `original_event_uid`, `correlation_uid` | định danh bản ghi, định danh gốc ở nguồn, khóa nối các bản ghi liên quan |
| `log_name`, `log_provider`, `log_source` | biết bản ghi đến từ kho/log nào |
| `processed_time`, `logged_time`, `modified_time` | biết bản ghi đi qua pipeline khi nào, bị sửa/enrich lúc nào |
| `tenant_uid` | tách dữ liệu của các tenant trong hệ thống nhiều khách hàng |
| `labels`, `tags` | gắn nhãn tự do để lọc |
| `profiles` | liệt kê profile mà bản ghi áp dụng |

### Phần dự phòng
- `unmapped`: field của nguồn không có chỗ trong schema. **Dùng để** không mất thông tin khi chuẩn hóa.
- `raw_data`: log gốc nguyên văn. **Dùng để** kiểm chứng và forensics, không dùng để truy vấn có cấu trúc.
- `message`: câu mô tả do nguồn viết. **Dùng để** người đọc nhanh, nhưng không nhất quán giữa các nguồn.

## Cách hoạt động
Đọc một bản ghi là đi qua các nhóm theo thứ tự câu hỏi:

| # | Câu hỏi | Nhóm field |
|---|---|---|
| 1 | Loại sự việc gì? | phân loại (`type_uid`) |
| 2 | Khi nào? | thời gian |
| 3 | Kết quả, mức độ? | `status_id`, `severity_id`; `action_id`, `disposition_id` |
| 4 | Ai làm? | `actor` (và `user` với IAM) |
| 5 | Ở đâu? | `device`, `src_endpoint` → `dst_endpoint` |
| 6 | Vào cái gì? | nội dung riêng của class, hoặc `finding_info` |
| 7 | Bối cảnh? | `enrichments`, ngữ cảnh trong `device` |
| 8 | Tin được đến đâu? | `metadata`, `raw_data` |

Các bản ghi nối với nhau thành câu chuyện qua khóa chung: cùng tiến trình (`process.uid`, `process.parent_process.uid`), cùng phiên (`actor.session.uid`), cùng máy (`device.uid`), cùng thực thể (`observables`), cùng nhóm (`metadata.correlation_uid`), hoặc do finding chỉ ra (`finding_info.related_events`).

## Ví dụ
Một alert EDR đã chuẩn hóa (rút gọn):

```json
{
  "category_uid": 2, "class_uid": 2004, "activity_id": 1, "type_uid": 200401,
  "time": 1761638400000, "severity_id": 4, "status_id": 1,
  "action_id": 2, "disposition_id": 2, "is_alert": true,
  "finding_info": {
    "uid": "det-88121", "title": "Encoded PowerShell spawned by Office",
    "attacks": [ { "technique": { "uid": "T1059.001", "name": "PowerShell" } } ],
    "related_events": [ { "uid": "evt-5521", "type_uid": 100701 } ]
  },
  "device": { "hostname": "WS-0412", "uid": "agent-7f3a", "type_id": 3 },
  "actor": { "user": { "name": "lan.nguyen" },
             "process": { "name": "winword.exe", "uid": "p-1001" } },
  "observables": [ { "name": "device.hostname", "type_id": 1, "value": "WS-0412" } ],
  "enrichments": [ { "name": "device.uid", "value": "agent-7f3a", "type": "asset",
                     "data": { "owner": "lan.nguyen", "bu": "Tài chính", "criticality": "High" } } ],
  "metadata": { "version": "1.9.0", "product": { "name": "EDR" },
                "original_time": "2025-10-28T08:00:00Z" }
}
```

1. `type_uid 200401`: Detection Finding, Create. Đây là một **alert mới**, không phải log hoạt động.
2. 08:00 UTC 28/10/2025.
3. `severity_id 4` (High); `action_id 2` Denied, `disposition_id 2` Blocked: đã bị chặn. `status_id 1`: alert chưa ai xử lý.
4. `winword.exe` dưới user `lan.nguyen`.
5. Laptop `WS-0412` (`type_id 3`).
6. "PowerShell mã hóa do Office sinh ra", ATT&CK `T1059.001`; bằng chứng gốc là event `evt-5521` (Process Launch).
7. Máy của phòng Tài chính, criticality High.
8. Nguồn là EDR, schema 1.9.0; thời gian gốc khớp `time`.

Ghép lại: *"08:00, winword.exe (lan.nguyen) trên laptop WS-0412 của phòng Tài chính (criticality High) sinh PowerShell mã hóa (T1059.001); EDR đã chặn. Alert High, chưa xử lý."*

## Câu hỏi và trả lời

**Một event OCSF trả lời các thông tin "ai, làm gì, khi nào, ở đâu, kết quả ra sao" như thế nào?**
Mỗi câu hỏi có một nhóm field cố định, và nhóm đó có mặt trong mọi class vì đến từ base event, category hoặc profile. Câu hỏi về *đối tượng* thì nằm trong object riêng của class. Bảng ở *Cách hoạt động* là bản đồ đầy đủ: loại ở `type_uid`, thời điểm ở `time`, kết quả ở `status_id`/`disposition_id`, chủ thể ở `actor`, nơi xảy ra ở `device` và `src_endpoint`/`dst_endpoint`. Một field trống nghĩa là nguồn không cung cấp hoặc mapping không điền, tức là "không biết", không phải "không xảy ra".

**Một event có thể nói về bao nhiêu máy, bao nhiêu người?**
Mỗi *vai* là một object đơn (`device`, `src_endpoint`, `dst_endpoint`, `actor`, `user`), nên một event có thể nhắc nhiều máy, nhiều người, nhưng mỗi vai chỉ một. Khi cần liệt kê nhiều thực thể cùng vai, schema dùng mảng: `resources[]` và `evidences[]` của finding. `observables[]` liệt kê mọi thực thể đáng chú ý, bất kể vai.

**Alert là class gì: activity hay finding?**
Phân biệt theo cách alert sinh ra. Một control (firewall, antivirus, IPS) phán quyết ngay trên một sự việc thì vẫn là class hoạt động của sự việc đó, cộng profile `security_control` với `disposition_id` và `is_alert`. Một hệ thống phân tích một hay nhiều event rồi đưa ra kết luận (SIEM, UEBA, phần phân tích của EDR) thì sinh class Finding, vd Detection Finding. Finding có vòng đời riêng (Create, Update, Close) và trỏ về các event làm bằng chứng.

**`time` khác `original_time`, `processed_time`, `logged_time` thế nào?**
`time` là thời điểm *sự việc* xảy ra, đã chuẩn hóa; mọi phân tích theo thời gian dùng nó. Các mốc trong `metadata` mô tả *hành trình của bản ghi*: `original_time` là chuỗi thời gian gốc chưa chuẩn hóa; `processed_time` là lúc qua hệ thống xử lý trung gian; `logged_time` là lúc tới nơi lưu cuối. Chênh lệch giữa chúng đo độ trễ của pipeline, không nói gì về sự việc.

**Làm sao biết hai event có liên quan nhau?**
Hai event liên quan khi chúng chia sẻ một khóa thực thể hoặc khóa nhóm: cùng tiến trình (`process.uid`), cùng phiên (`actor.session.uid`), cùng máy (`device.uid`), cùng thực thể trong `observables`, cùng `metadata.correlation_uid`. Liên kết tường minh nhất là `finding_info.related_events` của finding. Cùng hostname hay IP chỉ là liên quan *có thể*, vì định danh yếu có thể đổi chủ theo thời gian.

## Hiểu nhầm thường gặp
- **"`device` luôn là máy người dùng"**: `device` là nơi ghi nhận; với log firewall hay domain controller, máy người dùng nằm ở `src_endpoint`.
- **"`severity_id` cao là sự cố nghiêm trọng"**: đó là đánh giá của nguồn; ưu tiên thực còn phụ thuộc tài sản ([20-asset-context-in-security-operations.md](20-asset-context-in-security-operations.md)).
- **"Có alert là tấn công đã thành công"**: đọc `disposition_id` trước: control có thể đã chặn.
- **"`observables` và `enrichments` là một"**: `observables` chỉ ra thực thể *có trong* bản ghi; `enrichments` thêm thông tin *từ bên ngoài* về thực thể đó.

## Liên quan
- [16-ocsf-data-model.md](16-ocsf-data-model.md): dictionary, object, class, profile tạo nên các nhóm field trên.
- [15-security-data-normalization.md](15-security-data-normalization.md): vai trò ngữ nghĩa khi chuẩn hóa.
- [19-building-asset-profiles-from-events.md](19-building-asset-profiles-from-events.md): ngữ cảnh tài sản trong `device` và `enrichments`.
- [02-threats-and-attack-lifecycle.md](02-threats-and-attack-lifecycle.md): ATT&CK trong `finding_info.attacks`.
