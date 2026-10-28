# OCSF schema

> OCSF (Open Cybersecurity Schema Framework) là schema mở, trung lập vendor để mô tả mọi sự kiện bảo mật bằng cùng một bộ class, object và field, nhờ đó log từ SIEM, EDR, firewall hay cloud được đọc theo một cách duy nhất.

## Tại sao cần biết
Mỗi nguồn log tự đặt tên field: EDR gọi máy là `ComputerName`, firewall gọi là `src`, Windows gọi là `WorkstationName`. Nếu không chuẩn hóa, mỗi rule và mỗi bước enrich phải viết lại cho từng nguồn. OCSF là một trong các schema chuẩn hóa đã nêu ở [07-logging-and-telemetry.md](07-logging-and-telemetry.md); file này đi sâu vào cấu trúc của nó vì hai file sau ([16](16-mapping-logs-to-ocsf.md), [18](18-asset-enrichment-in-ocsf.md)) map log và gắn asset profile vào đúng những chỗ được mô tả ở đây.

## Khái niệm cốt lõi

### Ba tầng phân loại: category → class → activity
- **Category**: nhóm lớn, có `category_uid`. Ví dụ: System Activity (1), Findings (2), IAM (3), Network Activity (4), Discovery (5), Application Activity (6), Remediation (7).
- **Event class**: một loại sự kiện cụ thể, có `class_uid = category_uid × 1000 + số thứ tự`. Ví dụ Process Activity `1007`, Detection Finding `2004`, Authentication `3002`, Network Activity `4001`, Device Inventory Info `5001`.
- **Activity**: hành động trong class, `activity_id`. Ví dụ Process Activity có 1 Launch, 2 Terminate, 3 Open, 4 Inject; Authentication có 1 Logon, 2 Logoff.
- **`type_uid`** = `class_uid × 100 + activity_id`, là một số duy nhất trên toàn schema. Process Launch = `100701`, Logon = `300201`.

### Attribute, object, kiểu dữ liệu
- **Attribute**: một field có tên cố định trong dictionary chung (`hostname`, `ip`, `time`). Cùng tên thì cùng nghĩa ở mọi class.
- **Object**: nhóm attribute dùng lại được, lồng nhau như JSON. Các object quan trọng cho bài toán asset:
  - `device`: máy nơi sự kiện được quan sát (host của agent EDR, máy sinh Windows log).
  - `src_endpoint`, `dst_endpoint`: hai đầu kết nối mạng, kiểu `network_endpoint`.
  - `actor`: ai/cái gì gây ra hành động (user, process, session).
  - `user`, `process`, `file`, `metadata`.
- **Requirement**: mỗi attribute là *required*, *recommended* hoặc *optional*. Base event bắt buộc có `activity_id`, `category_uid`, `class_uid`, `type_uid`, `time`, `severity_id`, `metadata`.
- **Cặp `_id` + caption**: giá trị liệt kê luôn đi đôi, ví dụ `severity_id: 4` và `severity: "High"`. Rule nên lọc trên `_id` (số ổn định), caption để người đọc. Giá trị `0` là Unknown, `99` là Other (khi đó caption giữ chuỗi gốc của nguồn).

### Profile và extension
- **Profile**: bộ attribute bổ sung "gắn thêm" vào class khi ngữ cảnh phù hợp, không cần class mới. Ví dụ:
  - `host`: thêm `device` và `actor`. Base event include sẵn profile này.
  - `security_control`: thêm `action_id`, `disposition_id`, `is_alert`, `risk_level_id`... khi một control đã chặn hoặc cảnh báo.
  - `cloud`, `container`, `osint`, `datetime`.
  - Event khai báo profile đã dùng trong `metadata.profiles`.
- **Extension**: cách thêm class, object, attribute riêng của vendor hoặc tổ chức mà không sửa schema lõi. Mỗi extension có `uid` và `name` riêng; schema chính thức có sẵn extension `linux`, `macos`, `windows`.

### Các field "hạ tầng" của event
- `metadata`: thông tin về chính bản ghi: `product` (nguồn sinh log), `version` (phiên bản OCSF, bắt buộc), `original_time`, `event_code` (vd mã Windows `4624`), `log_name`, `tenant_uid`, `uid`, `processed_time`, `modified_time` (lần cuối bị sửa hoặc enrich), `labels`, `tags`.
- `observables[]`: danh sách phẳng các thực thể đáng chú ý trong event, mỗi phần tử gồm `name` (đường dẫn field, vd `src_endpoint.ip`), `type_id` (1 Hostname, 2 IP Address, 3 MAC, 4 User Name, 8 Hash, 20 Endpoint, 21 User, 25 Process...) và `value`. Dùng để pivot, tra threat intel mà không cần biết class.
- `enrichments[]`: dữ liệu ngữ cảnh lấy từ nguồn ngoài, mỗi phần tử gồm `name` (field được làm giàu), `value` (giá trị của field đó), `type`, `data` (object tự do), `provider`, `created_time`.
- `unmapped`: object chứa các field của nguồn không có chỗ trong OCSF, để không mất dữ liệu.
- `raw_data`: log gốc nguyên văn, cho forensics và debug, không dùng để truy vấn có cấu trúc.

## Cách hoạt động

```
Event OCSF
├── phân loại     category_uid · class_uid · activity_id · type_uid
├── thời gian     time · start_time/end_time · timezone_offset
├── mức độ        severity_id · status_id
├── metadata      product · version · event_code · tenant_uid · labels
├── ngữ cảnh      device · actor · src_endpoint · dst_endpoint   ← profile host, network
├── dữ liệu class process / user / file / finding_info ...      ← attribute riêng của class
├── chỉ mục       observables[]                                  ← pivot nhanh
├── làm giàu      enrichments[]                                  ← ngữ cảnh ngoài
└── dự phòng      unmapped · raw_data
```

Người dùng schema chỉ cần biết `class_uid` để biết event có những field nào; mọi thứ khác (tên field, kiểu, enum) giống nhau giữa các nguồn.

## Ví dụ
Một sự kiện EDR "máy `WS-0412` chạy `powershell.exe`" sau khi chuẩn hóa (rút gọn):

```json
{
  "category_uid": 1, "class_uid": 1007, "activity_id": 1, "type_uid": 100701,
  "class_name": "Process Activity", "activity_name": "Launch",
  "time": 1761634800000, "severity_id": 1,
  "metadata": {
    "version": "1.9.0",
    "product": { "name": "ExampleEDR", "vendor_name": "Example" },
    "original_time": "2025-10-28T07:00:00Z",
    "tenant_uid": "acme"
  },
  "device": { "hostname": "WS-0412", "ip": "10.20.4.12", "type_id": 3, "uid": "edr-agent-7f3a" },
  "actor": { "user": { "name": "lan.nguyen", "domain": "CORP" } },
  "process": { "name": "powershell.exe", "cmd_line": "powershell -enc ...", "pid": 4120 },
  "observables": [
    { "name": "device.hostname", "type_id": 1, "value": "WS-0412" },
    { "name": "process.name", "type_id": 9, "value": "powershell.exe" }
  ]
}
```

`type_uid = 1007 × 100 + 1 = 100701`; `device.type_id = 3` là Laptop. `time` là epoch milliseconds.

## Hiểu nhầm thường gặp
- **"OCSF là một định dạng file"**: OCSF là mô hình dữ liệu; có thể lưu dưới dạng JSON, Parquet hay bảng SQL. Data lake thường dùng Parquet.
- **"Phải điền hết các field"**: một class có hàng chục attribute cấp cao và hàng trăm đường dẫn lá; thực tế chỉ điền required, phần recommended có sẵn và những gì nguồn cung cấp.
- **"`device` và `src_endpoint` là một"**: `device` là máy nơi sự kiện được ghi nhận; `src_endpoint`/`dst_endpoint` là hai đầu kết nối. Với log firewall, firewall mới là `device`, còn máy người dùng là `src_endpoint`.
- **"Field không có trong OCSF thì bỏ"**: đưa vào `unmapped` hoặc tạo extension; bỏ đi là mất bằng chứng.

## Liên quan
- [07-logging-and-telemetry.md](07-logging-and-telemetry.md): vị trí của chuẩn hóa trong đường đi của log.
- [16-mapping-logs-to-ocsf.md](16-mapping-logs-to-ocsf.md): cách map log SIEM/EDR vào các class trên.
- [18-asset-enrichment-in-ocsf.md](18-asset-enrichment-in-ocsf.md): đặt asset profile vào `device`, `enrichments`.
- [14-vendor-terminology-map.md](14-vendor-terminology-map.md): OCSF so với ECS, UDM, ASIM, CIM.
