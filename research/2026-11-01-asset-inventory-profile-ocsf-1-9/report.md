---
title: Asset inventory và asset profile từ log OCSF 1.9.0
date: 2026-11-01
question: Với log bảo mật đã chuẩn hóa theo OCSF 1.9.0, nên dựng asset inventory và asset profile theo phương pháp nào để phục vụ detection và triage?
tags: [asset-inventory, asset-profile, ocsf, microsoft, entity-resolution]
---

# Asset inventory từ OCSF là một engine entity resolution

> **Câu hỏi:** Dựng asset inventory và asset profile từ log OCSF 1.9.0 thế nào? · **Ngày:** 2026-11-01 · **Tác giả:** @Hai · **Phạm vi:** OCSF 1.9.0, docs Microsoft Learn hiện hành; device và account trước. · **Kế thừa:** [research/2026-10-29-asset-profile-tu-event-chuan-hoa](../2026-10-29-asset-profile-tu-event-chuan-hoa/report.md) · **Kiểm chứng:** đối chiếu với schema OCSF v1.9.0 chính thức và docs Microsoft, 3 chỗ đã sửa (xem [notes/doi-chieu-kiem-chung.md](notes/doi-chieu-kiem-chung.md))

## Mục lục

1. **Tóm tắt**: mục tiêu, phạm vi, kết luận chính.
2. **Khung khái niệm: Microsoft định nghĩa entity thế nào**: entity, asset và evidence, strong/weak identifier, merge.
3. **Microsoft triển khai inventory và profile thế nào**: DeviceInfo, device discovery, dedup, critical asset, Exposure Graph, UEBA.
4. **Kiến thức cơ bản OCSF: từ cấu trúc đến cách khai thác**: khái niệm nền tảng, giải phẫu một event, quy ước đọc dữ liệu, tám phương pháp khai thác.
5. **Nguồn asset trong OCSF 1.9.0**: lớp và trường dùng được, observable type\_id, criticality\_id, phần deprecated.
6. **Mô hình dữ liệu đề xuất**: năm bảng và tương đương bên Microsoft.
7. **Từ entity đến asset**: ba điều kiện để promote, phân loại toàn bộ entity, vai trò của evidence.
8. **Pipeline từ log OCSF đến inventory**: sáu bước từ extract đến lifecycle.
9. **Asset profile**: thông tin theo từng loại asset (device, account, group, cloud) và class OCSF nguồn.
10. **Bẫy thường gặp**: IP, onboard lại, clone VM, tài khoản built-in, parser không đều.
11. **Phục vụ detection và lộ trình MVP**: cách dùng cho triage, rule, ưu tiên hóa và các bước triển khai.
12. **Đối chiếu với báo cáo trước**: điểm khớp, điểm mới, điểm đã sửa.
13. **Chưa kiểm chứng được**
14. **Nguồn tham khảo**

## Tóm tắt

Asset inventory nên được dựng như một **engine entity resolution** chạy trên log OCSF 1.9.0: trích identifier từ mọi event, gộp theo strong identifier, rồi suy ra profile (role, criticality, baseline hành vi) để phục vụ detection và triage.

- **Mô hình tham chiếu:** Microsoft chia entity thành asset (thứ được bảo vệ) và evidence (thứ xuất hiện trong sự kiện), gộp entity bằng strong/weak identifier, và tách trạng thái thiết bị (DeviceInfo) khỏi hành vi (UEBA).
- **Nguồn dữ liệu:** lớp Discovery (5001, 5003, 5020, 5023, Live Evidence Info 5040) là nguồn khai báo; object `device`, `src/dst_endpoint`, `user`, `actor` trong activity events là nguồn quan sát; mảng `observables` là lối tắt để trích entity.
- **Criticality:** OCSF 1.9.0 thêm enum `criticality_id` 4 mức (Low → Very High), trùng thang criticality của Microsoft, nên dùng làm enum cho cột criticality của inventory. Lưu ý: trong 1.9.0 enum này chỉ được gắn vào object `resource_details`; `device` và `user` không có trường criticality, nên criticality phải do inventory tự suy ra hoặc khai báo, không đọc được từ event.
- **Phạm vi:** asset dạng device và account trước; cloud resource và ứng dụng để giai đoạn sau.

## Khung khái niệm: Microsoft định nghĩa entity thế nào

Microsoft coi entity là đơn vị dữ liệu được nhận diện xuyên suốt analytics, điều tra và hunting, và định danh nó bằng tổ hợp identifier mạnh hoặc yếu. Ba khái niệm dưới đây nên mượn nguyên vẹn.

| Khái niệm | Microsoft định nghĩa | Microsoft triển khai | Áp dụng cho inventory OCSF |
| --- | --- | --- | --- |
| Entity | Phần tử dữ liệu trong alert được nhận diện và phân loại (user account, host, mailbox, IP, file, cloud app, process, URL…) ([Sentinel entities](https://learn.microsoft.com/en-in/azure/sentinel/entities)) | Entity mapping trong analytics rule: map cột kết quả truy vấn vào entity type qua identifier; mỗi type có schema riêng ([entities reference](https://learn.microsoft.com/azure/sentinel/entities-reference)) | Mỗi object OCSF (`device`, `user`, `*_endpoint`) là một ứng viên entity |
| Asset vs evidence | Defender portal chia entity thành hai nhóm: Assets và Other entities (evidence) | Asset (device, user, mailbox, cloud resource) có trang entity, inventory, criticality; evidence chỉ gắn vào alert/incident | Inventory chỉ chứa asset; file, process, IP, URL là thuộc tính hành vi gắn vào asset |
| Strong / weak identifier | Strong đủ để định danh duy nhất; weak chỉ định danh được khi kết hợp với identifier khác | Bảng identifier theo từng entity type (xem dưới); tối đa 3 identifier cho một entity mapping | Bảng `asset_identifier` có cột `strength` |
| Merge | Hai entity nhận ra là một qua identifier thì được gộp; entity chỉ có weak identifier (ví dụ username không domain) thì không gộp được và đứng riêng | Gộp tự động khi nguồn dùng strong identifier chung; đồng bộ Entra ID tạo thư mục thống nhất giúp gộp account | Resolve chỉ dựa trên strong ID; weak ID đi qua bảng binding theo thời gian |

**Strong identifier của Microsoft cho các entity liên quan** ([entities reference](https://learn.microsoft.com/azure/sentinel/entities-reference)):

| Entity | Strong identifier | Weak identifier | Tương đương OCSF 1.9.0 |
| --- | --- | --- | --- |
| Host | HostName + NTDomain · HostName + DnsDomain · NetBiosName + NTDomain · NetBiosName + DnsDomain · AzureID · OMSAgentID · IoTDevice | HostName · NetBiosName (không domain) | `device.uid`, `uid_alt`, `os_machine_uuid`, `hw_info.uuid`, `instance_uid`; `hostname` + `domain` |
| Account | Name + UPNSuffix · AadUserId · Sid (không phải built-in) · Sid + Host · Name + NTDomain (+ Host nếu là local) · Name + DnsDomain · PUID · ObjectGuid | Name | `user.uid` (SID/GUID), `user.name` + `domain`, `email_addr`/UPN, `account.uid` |
| IP | IP public: Address · IP private: Address + AddressScope | IP private đứng một mình | `ip` + `network_scope_id`/`subnet`; chỉ là thuộc tính, không phải asset |
| Process | Host + ProcessId + CreationTimeUtc (+ CommandLine/ImageFile/FileHash) | ProcessId + CreationTimeUtc không có Host | `process.uid`, `pid` + `created_time` + device; là evidence |

Điểm then chốt: SID của tài khoản built-in chỉ thành strong khi đi kèm Host, và Name + NTDomain của tài khoản local cũng cần Host. Microsoft còn loại hẳn khỏi alert các account chỉ định danh bằng Name khi tên là một trong 11 tên chung: ADMIN, ADMINISTRATOR, SYSTEM, ROOT, ANONYMOUS, AUTHENTICATED USER, NETWORK, NULL, LOCAL SYSTEM, LOCALSYSTEM, NETWORK SERVICE. Inventory nên áp dụng cùng danh sách chặn này.

## Microsoft triển khai inventory và profile thế nào

Microsoft không có một "asset inventory" duy nhất mà tách thành sáu thành phần: trạng thái thiết bị, phát hiện thiết bị chưa quản lý, khử trùng lặp, phân loại criticality, đồ thị quan hệ và baseline hành vi. Inventory OCSF nên có đủ sáu chức năng này.

| Thành phần | Microsoft định nghĩa | Cách triển khai | Bài học cho inventory OCSF |
| --- | --- | --- | --- |
| [DeviceInfo](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-deviceinfo-table) (trạng thái thiết bị) | Bảng chứa thông tin thiết bị: OS, user đang hoạt động, tên máy, `DeviceCategory` (Endpoint, Network device, IoT, Unknown), `DeviceType`, `OnboardingStatus`, `SensorHealthState`, `ExposureLevel` | Bảng "updated continuously, and all updates contain the full current device data"; trạng thái hiện tại lấy bằng `arg_max(IngestionTime, *) by DeviceId`; ID cũ của cùng thiết bị nằm ở `MergedDeviceIds`, ID mới nhất ở `MergedToDeviceId` | Lưu snapshot append-only, suy ra current state bằng latest-wins theo `asset_id` |
| [Device discovery](https://learn.microsoft.com/en-us/defender-endpoint/device-discovery) (thiết bị chưa quản lý) | Khả năng tìm thiết bị unmanaged trong mạng doanh nghiệp, không cần thêm appliance | Basic: endpoint đã onboard thụ động trích thông tin từ lưu lượng mạng nó thấy, không tạo traffic. Standard (mặc định): thêm truy vấn multicast và dò chủ động, mỗi thiết bị thường dò không quá 3 tuần một lần, dưới 50 KB mỗi lần; chỉ dò thiết bị chưa onboard; chỉ liệt kê thiết bị trên mạng được xác định là mạng doanh nghiệp | Dùng `src/dst_endpoint` trong log OCSF như "basic discovery": asset được tạo từ quan sát thụ động, gắn cờ unmanaged |
| Transient devices | Cột `IsTransient` của DeviceInfo: thiết bị "classified as short-lived or transient based on the frequency of appearance of the device on the network"; Defender for IoT gọi là thiết bị "detected for only a short time" ([IoT inventory](https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/device-inventory)) | Được đánh dấu riêng; một blog bên thứ ba cho biết chúng được ẩn khỏi inventory mặc định ([tips](https://www.51sec.org/2025/05/14/microsoft-defender-tips-tricks/), bậc 3) | Trạng thái `transient` cho asset chỉ có weak ID hoặc hiếm khi xuất hiện |
| Dedup thiết bị | Bản ghi trùng phát sinh khi discovery quét trúng thiết bị đã onboard hoặc vừa offboard; mỗi lần onboard sinh một chữ ký mới dù cùng máy | Tùy chọn "Hide potential duplicate device records" ẩn bản ghi trùng khỏi Device Inventory, MDVM và API, giữ bản chính xác nhất ([advanced features](https://learn.microsoft.com/en-us/defender-endpoint/advanced-features)). Defender for IoT gộp thiết bị cùng zone có tổ hợp đặc tính giống nhau (ví dụ cùng IP và MAC); cùng MAC khác IP thì không gộp ([IoT inventory](https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/device-inventory)) | Rule merge rõ ràng, ưu tiên ID phần cứng; bản ghi thua cuộc được đánh dấu `merged_into`, không xóa |
| [Critical asset management](https://learn.microsoft.com/en-us/security-exposure-management/critical-asset-management) | 4 mức criticality: low, medium, high, very high; very high = tài sản trọng yếu của doanh nghiệp | Catalog phân loại định sẵn cho device, identity, cloud resource, tự gắn nhãn; cho phép tạo rule tùy chỉnh và chỉnh mức thủ công ([classify](https://learn.microsoft.com/en-us/security-exposure-management/classify-critical-assets)). Ví dụ: vCenter được nhận ra nhờ fingerprint của device discovery cộng network connection events ([blog, bản chép lại](https://app-pack.telkomuniversity.ac.id/?p=447888)); docs chính thức xếp ESXi/vCenter ở mức High ([predefined classifications](https://learn.microsoft.com/en-us/security-exposure-management/predefined-classification-rules-and-levels)) | Criticality = rule suy từ role + override thủ công; dùng enum `criticality_id` của OCSF |
| [Exposure Graph](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-exposuregraphnodes-table) | `ExposureGraphNodes` chứa entity của tổ chức (device, identity, group, cloud asset) cùng thuộc tính; `ExposureGraphEdges` chứa quan hệ | Mỗi node có `NodeId`, `NodeLabel`, `Categories`, `NodeProperties` (JSON: criticality, exposedToInternet, vulnerableToRCE…) và `EntityIds` = tất cả identifier đã biết; dữ liệu từ MDE, MDI, Defender for Cloud, Entra ID và connector bên thứ ba ([query](https://learn.microsoft.com/en-us/security-exposure-management/query-enterprise-exposure-graph)) | Mô hình node + `asset_identifier` + `asset_relationship` tương đương; thuộc tính linh hoạt để trong JSON |
| [UEBA](https://learn.microsoft.com/azure/sentinel/ueba-reference) (baseline hành vi) | Baseline của mỗi entity dựng từ lịch sử của chính nó, của peer group và của toàn tổ chức ([anomalies](https://learn.microsoft.com/azure/sentinel/anomalies-reference)) | `IdentityInfo`: hồ sơ identity đồng bộ từ Entra ID và AD (qua MDI). `BehaviorAnalytics`: event được làm giàu (UsersInsights, DevicesInsights, ActivityInsights), mỗi activity có lookback riêng. `UserPeerAnalytics`: top 20 peer theo nhóm bảo mật, mailing list. Điểm `InvestigationPriority` 0–10 ([UEBA](https://learn.microsoft.com/en-us/azure/sentinel/identify-threats-with-entity-behavior-analytics)) | Baseline theo 3 tầng: asset, peer (cùng role/OU), toàn tổ chức; mỗi đặc trưng có cửa sổ lookback riêng |

Điểm khác biệt cần lưu ý: Microsoft có agent và thư mục danh tính riêng (MDE, Entra ID) nên luôn có strong ID. Inventory dựng trên log đa nguồn không có lợi thế này, vì vậy bước resolve qua weak ID là phần khó nhất và phải tự làm.

**Danh sách entity type của Microsoft Sentinel** (20 loại, theo [entity types reference](https://learn.microsoft.com/azure/sentinel/entities-reference); nhóm theo cách Defender chia asset / evidence):

- **Asset (thứ được bảo vệ)**
  - Host: máy tính, server, VM
  - Account: tài khoản người dùng hoặc dịch vụ
  - Security group: nhóm bảo mật trong AD / Entra ID
  - Mailbox: hộp thư
  - IoT device: thiết bị IoT
  - Azure resource: tài nguyên cloud
  - Cloud application: ứng dụng SaaS / cloud
- **Evidence (thứ xuất hiện trong sự kiện)**
  - IP: địa chỉ IP
  - URL: đường dẫn web
  - DNS resolution: bản ghi phân giải tên miền
  - Process: tiến trình
  - File: tệp
  - File hash: giá trị băm của tệp
  - Registry key: khóa registry
  - Registry value: giá trị registry
  - Malware: mã độc được phát hiện
- **Email**
  - Mail message: một thư cụ thể
  - Mail cluster: nhóm thư giống nhau
  - Submission mail: thư người dùng báo cáo
- **Khác**
  - Sentinel entities: danh sách entity đi kèm alert

## Kiến thức cơ bản OCSF: từ cấu trúc đến cách khai thác

OCSF là schema chuẩn hóa sự kiện bảo mật, độc lập với định dạng lưu trữ và quy trình ETL; mỗi log gốc được map vào đúng một event class. Nắm cấu trúc schema cho phép viết extractor dựa trên schema thay vì dò từng nguồn log ([Understanding OCSF](https://github.com/ocsf/ocsf-docs/blob/main/overview/understanding-ocsf.md)).

### Năm khái niệm nền tảng

| Khái niệm | Định nghĩa | Ví dụ |
| --- | --- | --- |
| Data type, attribute, array | Kiểu scalar dựng trên kiểu nguyên thủy; attribute là tên định danh cho một kiểu dữ liệu có thể validate; mọi attribute nằm trong attribute dictionary. Object là tập attribute liên quan, thường đại diện một entity, có thể lồng object khác | `timestamp_t`, `ip_t`, `mac_t`; object `process`, `device`, `user`, `file` |
| Event class | Tập attribute từ dictionary mô tả ngữ nghĩa một loại sự kiện; mỗi event là một instance; mọi class kế thừa Base Event | Process Activity (1007), Authentication (3002), Network Activity (4001) |
| Category | Nhóm class theo domain; mỗi class thuộc đúng một category | 1 System Activity, 2 Findings, 3 IAM, 4 Network Activity, 5 Discovery, 6 Application Activity, 7 Remediation, 8 Unmanned Systems |
| Profile | Lớp attribute phủ lên class và object, độc lập với category; event khai báo profile đã áp dụng, nhờ đó lọc được xuyên class | `host` (device, actor), `cloud`, `security_control`, `container`, `datetime` |
| Extension | Mở rộng schema mà không sửa core; có UID riêng để tránh trùng ID | `win` (Windows), `linux`, `macos`; extension của vendor |

### Giải phẫu một event

*(Bản gốc có sơ đồ "giải phẫu một event OCSF · 8 nhóm thuộc tính"; sơ đồ không có trong bản lưu này.)*

Phần tô đậm trong sơ đồ là nơi chứa entity cần cho inventory; observables là bản tóm tắt của chúng, unmapped là nơi cần kiểm tra khi một trường tưởng như bị thiếu.

### Quy ước đọc dữ liệu

- **Hậu tố tên:** `_id` là enum số nguyên (0 = Unknown, 99 = Other); khi là Other, attribute "anh em" cùng tên bỏ hậu tố phải chứa nhãn gốc (`severity_id` / `severity`). `_uid` là định danh duy nhất trong schema hoặc của entity; `_uuid` là định danh toàn cục; `_name` là nhãn; `_time` là mili giây Unix; `_dt` là chuỗi RFC 3339; số nhiều hoặc `_list` là mảng.
- **Mức yêu cầu:** Required luôn có (thiếu thì đặt Unknown), Recommended nên có nhưng không bị validate, Optional tùy nguồn. Mức yêu cầu thuộc về attribute trong từng class, không phải bản thân attribute.
- **Constraint:** `at_least_one` và `just_one` trên các attribute Recommended. Ví dụ Device (kế thừa ràng buộc của `endpoint`) chỉ cần một trong ip, uid, name, hostname, instance_uid, interface_uid, interface_name, nên không được giả định `device.uid` luôn có.
- **Nhóm attribute:** Classification (phân loại, bắt buộc), Occurrence (thời gian), Primary (ngữ nghĩa chính của class), Context (làm giàu).
- **Associations:** class khai báo thuộc tính nào đi với thuộc tính nào. Trong Authentication, `actor.user` gắn với `src_endpoint`, còn `user` (đích) gắn với `dst_endpoint`.
- **Thời gian:** `time` là thời điểm đã chuẩn hóa và hiệu chỉnh lệch đồng hồ; `metadata.original_time` là chuỗi gốc; `logged_time`, `processed_time`, `modified_time` thuộc pipeline; `timezone_offset` tính bằng phút.
- **Phiên bản:** semver; phiên bản minor chỉ bổ sung và giữ tương thích ngược trong cùng major, vì vậy dữ liệu 1.x cũ vẫn đọc được bằng schema 1.9.0.

### Phương pháp khai thác, từ cơ bản đến nâng cao

1. **Lọc theo phân loại, không theo event ID của vendor.** Dùng `class_uid`, `activity_id`, `type_uid` (số nguyên) để lọc, dùng caption để hiển thị. Ví dụ `type_uid = 300201` là Authentication: Logon.
2. **Điều hướng theo đường dẫn object.** `actor` là bên khởi tạo hành động (`actor.user`, `actor.process`); các object khác là đối tượng bị tác động. Cùng một kiểu object xuất hiện ở nhiều đường dẫn (`device`, `src_endpoint`, `dst_endpoint`), nên extractor phải xử lý tất cả.
3. **Dùng `observables` để pivot và trích entity nhanh.** Mỗi phần tử có `name` (đường dẫn đầy đủ), `type_id`, `value`; observable kiểu object chỉ có `name`, không có `value`.
4. **Đọc `metadata` trước khi tin dữ liệu.** `version` cho biết schema, `product` và `log_source` cho biết nguồn, `profiles` cho biết attribute nào có thể có. Lọc theo profile cho phép lấy mọi event có `device` bất kể class.
5. **Kiểm tra `unmapped` và `raw_data`.** Trước khi kết luận một nguồn không có trường nào đó, xem nó có nằm trong `unmapped` không; đây cũng là thước đo chất lượng parser.
6. **Dùng associations để ghép user với endpoint.** Đây là nguồn tự nhiên cho bảng binding user ↔ máy và IP ↔ máy.
7. **Sinh extractor từ schema.** Tải schema đã biên dịch (export JSON từ schema browser hoặc repo), duyệt mọi class để liệt kê mọi đường dẫn có kiểu `device`, `user`, `network_endpoint`, `process`…, rồi chạy extractor theo danh sách này. Cần giới hạn độ sâu: toàn bộ cây đường dẫn của OCSF 1.9.0 vượt 100.000 ([Axiom](https://axiom.co/docs/use-cases/ocsf)); Tenzir được cho là chỉ giữ đệ quy một cấp cho object như `process.parent_process` (chưa kiểm chứng, link changelog nay trả 404).
8. **Đo coverage và validate.** Đo tỷ lệ điền theo nguồn × class × đường dẫn, ưu tiên trường Required và Recommended; chạy validator (schema server hoặc [ocsf-toolkit](https://pkg.go.dev/github.com/ocsf/ocsf-toolkit)) trên mẫu dữ liệu.

Ví dụ truy vấn theo phân loại, áp dụng cho mọi nguồn đã chuẩn hóa:

```sql
-- Logon thành công theo user và máy nguồn
SELECT "user.name", "src_endpoint.hostname", count(*) AS n
FROM ocsf
WHERE class_uid = 3002 AND activity_id = 1 AND status_id = 1
GROUP BY 1, 2;
```

## Nguồn asset trong OCSF 1.9.0

OCSF 1.9.0 (phát hành 3/8/2026) cung cấp asset qua bốn nguồn, xếp theo độ tin cậy giảm dần: lớp Discovery (khai báo), activity events (quan sát), mảng `observables` (lối tắt) và Findings (rủi ro).

| Mục tiêu | Lớp / trường OCSF 1.9.0 | Ghi chú |
| --- | --- | --- |
| Device, khai báo | Device Inventory Info (5001), Software Inventory Info (5020), Cloud Resources Inventory Info (5023), Live Evidence Info (5040) | 5001 có `activity_id` 1 = Log (thụ động), 2 = Collect (thu thập chủ động) |
| Device, quan sát | `device` trên mọi event (host profile ở base\_event), `src_endpoint` / `dst_endpoint`, `network_interfaces[]` | Phần tử đầu của `network_interfaces` là thông tin mạng của chính event |
| Strong ID của device | `device.uid` (ví dụ Windows TargetSID, EC2 ARN), `uid_alt` (ví dụ AD DN), `os_machine_uuid`, `hw_info.uuid`, `instance_uid`, `boot_uid`, MAC | Device object chỉ bắt buộc có ít nhất một trong ip, uid, name, hostname, instance\_uid, interface\_uid, interface\_name, nên nhiều bản ghi chỉ có IP |
| Thuộc tính device | `type_id`, `os`, `hw_info.cpu_info_list` (1.9), `peripheral_devices` (1.9), `is_managed`, `is_shared`, `is_trusted`, `is_backed_up`, `first_seen_time`, `last_seen_time`, `vendor_name`, `model`, `mac_vendor` (1.8) | Không có trường criticality trên `device` |
| Account, khai báo | User Inventory Info (5003), User Management (3007, mới ở 1.9), Group Management (3006, `users[]`), Role Management (3008, mới ở 1.9) |  |
| Account, quan sát | Authentication (3002), Authorize Session (3003), `actor.user`, `user` | `user.type_id` có giá trị Service (1.6); object `account` có `is_disabled`, `is_locked` (1.8) |
| Dịch vụ / vai trò mạng | `initiator_id` trong Network Activity (1.9), `network_interface.open_ports` (1.6), `network_endpoint.network_scope_id` (1.6) | `initiator_id` cho biết bên nào khởi tạo kết nối, thay `is_src_dst_assignment_known` |
| Cấu hình, tuân thủ | Compliance Finding (2003), OS Patch State (5004) |  |
| Rủi ro | Detection Finding (2004), Vulnerability Finding (2002) |  |
| Lifecycle | Device Power State Activity (1011, mới ở 1.9), `first/last_seen_time` |  |
| Provenance | `metadata.reporter`, `source`, `log_source`, `original_event_uid` (1.7) | Căn cứ xếp ưu tiên nguồn khi mâu thuẫn |

**Observable type\_id hữu ích:** 1 Hostname, 2 IP, 3 MAC, 4 User Name, 20 Endpoint, 21 User, 47 `device.uid` (1.6), 48 `network_endpoint.uid` (1.7), 49/50 `iam_role.name`/`uid` (1.9). Từ 1.7, object observable có `event_uid` và `type_uid` để truy ngược về event gốc. Nếu parser có sinh mảng `observables`, việc trích entity chỉ còn là lọc theo `type_id`.

**Criticality:** 1.9.0 thêm `criticality_id` với Low (1), Medium (2), High (3), Very High (4), cùng Unknown (0) và Other (99), đi cặp với `criticality`. Thang này trùng thang của Microsoft Exposure Management. Trong 1.9.0, attribute này chỉ được gắn vào object `resource_details` (tài nguyên cloud); `device`, `user`, `endpoint` không có nó. Vì vậy inventory chỉ mượn *enum* cho cột `criticality_id` của mình; giá trị phải do rule suy ra hoặc khai báo thủ công, không đọc được từ event.

**Các lớp, trường đã deprecated** (vẫn có thể xuất hiện nếu parser viết theo mapping cũ, extractor nên đọc cả hai):

| Cũ | Từ phiên bản | Thay bằng |
| --- | --- | --- |
| Process / Service / User Session / User Query và các query class khác | 1.5 | Live Evidence Info |
| Device Config State (5002) | 1.5 | Compliance Finding |
| Account Change (3001), User Access Management (3005) | 1.9 | User Management (3007) |
| `user_result` | 1.9 | `updated_user` |
| `group_management.user` | 1.9 | `users[]` |
| `actor.app_name`, `actor.app_uid` | 1.9 | `actor.application` |
| `is_src_dst_assignment_known` | 1.9 | `initiator_id` |
| `device_hw_info.cpu_*` | 1.9 | `cpu_info_list[*]` |

Nguồn: [OCSF CHANGELOG](https://github.com/ocsf/ocsf-schema/blob/main/CHANGELOG.md), [release 1.9.0](https://github.com/ocsf/ocsf-schema/releases), [Device object](https://docs.tenzir.com/reference/ocsf/1-5-0/objects/device), [Device Inventory Info](https://docs.tenzir.com/reference/ocsf/1-3-0/classes/inventory_info); đối chiếu lại với repo `ocsf-schema` tag v1.9.0.

## Mô hình dữ liệu đề xuất

Năm bảng, tách identity khỏi state và state khỏi hành vi, theo đúng cách Microsoft tách `EntityIds` / `DeviceInfo` / `BehaviorAnalytics`.

| Bảng | Vai trò | Cột chính | Tương đương Microsoft |
| --- | --- | --- | --- |
| `asset` | Thực thể chuẩn, một dòng mỗi asset | `asset_id` (UUID nội bộ), `asset_type` (device, user, service\_account, cloud\_resource), `state` (active, stale, retired, transient, merged), `merged_into`, `first_seen`, `last_seen` | `NodeId` / `DeviceId` |
| `asset_identifier` | Mọi identifier của asset, có thời hạn | `asset_id`, `id_type` (device\_uid, os\_machine\_uuid, sid, upn, fqdn, netbios+domain, mac, ip…), `value`, `strength` (strong/weak), `valid_from`, `valid_to`, `source`, `confidence` | `EntityIds`, strong/weak identifier |
| `asset_observation` | Snapshot append-only từ từng nguồn | `asset_id`, `source`, `class_uid`, `time`, `attrs` (JSON) | Các bản cập nhật của `DeviceInfo` |
| `asset_relationship` | Quan hệ giữa các asset | `src_asset`, `rel_type` (logged\_on, admin\_of, talks\_to, member\_of, owns), `dst_asset`, `count`, `first_seen`, `last_seen` | `ExposureGraphEdges` |
| `asset_profile` | Kết quả suy luận, có phiên bản | `asset_id`, `version`, `role`, `criticality_id`, `criticality_source` (rule/manual), `baseline` (JSON theo cửa sổ), `computed_at` | `NodeProperties`, `BehaviorAnalytics` |

Hai nguyên tắc:

- **`asset_id` là ID nội bộ, không bao giờ là hostname hay IP.** IP đổi theo DHCP, hostname bị dùng lại, cài lại OS làm đổi `device.uid`.
- **Không xóa khi merge.** Bản ghi thua chuyển sang `state = merged` với `merged_into`, để truy vết và tách lại nếu merge sai.

## Từ entity đến asset

Engine xác định entity trước, rồi chỉ đẩy lên asset những entity thỏa đồng thời ba điều kiện. Entity còn lại không bị bỏ: chúng dùng để resolve asset, dựng quan hệ và tính baseline. Phần này tương ứng bước 1–3 của pipeline.

*(Bản gốc có sơ đồ "entity → asset · 3 điều kiện, 4 kết cục"; sơ đồ không có trong bản lưu này.)*

**Ba điều kiện promote:**

1. **Thuộc kiểu có thể là asset:** Host/device, Account, Security group, Mailbox, IoT device, cloud resource (bảng dưới).
2. **Thuộc phạm vi tổ chức:** nằm trong dải mạng nội bộ, thuộc domain/tenant của công ty, hoặc có trong nguồn khai báo (AD, CMDB). Server Internet, account của domain ngoài, SaaS bên thứ ba là external dù có strong ID. Microsoft cũng chỉ đưa vào inventory thiết bị trên mạng được xác định là mạng doanh nghiệp.
3. **Định danh đủ:** có strong ID, hoặc weak ID gắn được vào strong ID qua binding theo thời gian. Chưa đủ thì giữ ở trạng thái candidate (`transient`), promote khi sau này gặp strong ID, tương tự transient devices của Microsoft.

**Phân loại toàn bộ entity type của Microsoft Sentinel** ([entities reference](https://learn.microsoft.com/azure/sentinel/entities-reference)):

| Entity | Nhóm | Strong identifier | Tương đương OCSF |
| --- | --- | --- | --- |
| Host | Asset | HostName/NetBiosName + NTDomain/DnsDomain, AzureID, OMSAgentID, IoTDevice | `device` |
| Account | Asset | Name + UPNSuffix, AadUserId, Sid, Sid + Host, Name + NTDomain, Name + DnsDomain, PUID, ObjectGuid | `user`, `account` |
| Security group | Asset | DistinguishedName, SID, ObjectGuid | `group` |
| Mailbox | Asset | MailboxPrimaryAddress | `user.email_addr`, `email` |
| IoT device | Asset | IoTHub + DeviceId | `device` (`type_id` = IOT) |
| Azure resource | Asset | ResourceId | `resource_details`, `cloud` |
| Cloud application | Asset nếu là ứng dụng nội bộ, evidence nếu là SaaS ngoài | AppId hoặc Name (có/không InstanceName) | `application` |
| IP | Evidence (thuộc tính của asset) | Address (public); Address + AddressScope (private) | `ip`, `network_endpoint` |
| URL | Evidence | Url (tuyệt đối) | `url` |
| DNS resolution | Evidence | DomainName + DnsServerIp + HostIpAddress | DNS Activity (4003) |
| Process | Evidence | Host + ProcessId + CreationTimeUtc (+ CommandLine / ImageFile / FileHash) | `process` |
| File | Evidence | Name + Directory, Name + FileHash | `file` |
| File hash | Evidence | Algorithm + Value | `fingerprint` |
| Registry key / value | Evidence | Hive + Key / Key + Name | `win/reg_key`, `reg_value` |
| Malware | Evidence | Name + Category | `malware` |
| Mail message, Mail cluster, Submission mail | Evidence (email) | NetworkMessageId + Recipient; Query + Source; SubmissionId + NetworkMessageId + Recipient + Submitter | `email` |

**Vai trò của evidence entity:**

| Vai trò | Ví dụ |
| --- | --- |
| Hỗ trợ resolve asset | IP + thời gian → binding về device; DNS resolution (hostname ↔ IP) gán weak ID cho đúng host; Process luôn gắn Host nên neo được event vào device |
| Đặc trưng profile | Process, file hash, URL, domain DNS, port làm baseline; registry cho cơ chế persistence quen thuộc |
| Dựng quan hệ | Account logon Host, Account thuộc Security group, Host kết nối Host → `asset_relationship`, nguồn cho role, peer group, criticality |

Evidence cũng cần identity ổn định nhưng nhẹ hơn: Process cần Host + PID + thời điểm tạo để không đếm trùng, File cần hash để biết binary lần đầu xuất hiện trên asset. Evidence không cần lifecycle, merge hay criticality. Microsoft gọi entity nằm bên trong entity khác (Host trong Account, Account và ParentProcess trong Process) là internal entities; chúng không dùng làm identifier trong entity mapping nhưng là nguồn dựng quan hệ.

## Pipeline từ log OCSF đến inventory

Bước Resolve quyết định chất lượng toàn bộ inventory: chỉ strong identifier được phép gộp asset, weak identifier phải đi qua bảng binding có thời hạn.

*(Bản gốc có sơ đồ "pipeline từ log OCSF đến inventory · 6 bước"; nội dung sáu bước liệt kê ngay dưới.)*

1. **Extract:** từ mỗi event lấy `device`, `src_endpoint`, `dst_endpoint`, `user`, `actor.user`, `observables`; gắn nhãn vai trò (chủ thể hay đối tác) và `metadata` của nguồn.
2. **Normalize:** đưa hostname về chữ thường, tách FQDN thành host + domain, chuẩn hóa MAC, SID, UPN; phân loại IP theo `network_scope_id` hoặc dải nội bộ; bỏ giá trị rác.
3. **Resolve:** strong ID trùng thì merge vào asset có sẵn. Chỉ có weak ID thì tra bảng binding `(ip, thời gian) → asset`, dựng từ event có cả IP lẫn strong ID (heartbeat EDR, DHCP, 3002 có hostname). Không resolve được thì tạo asset `transient`, giống transient devices của Microsoft.
4. **Aggregate:** ghi snapshot vào `asset_observation`, suy current state theo latest-wins như `arg_max` trên DeviceInfo; khi mâu thuẫn, ưu tiên Discovery > EDR > network.
5. **Derive:** role, `criticality_id`, baseline (xem phần Asset profile).
6. **Lifecycle:** active → stale (quá N ngày không thấy) → retired; merge sai thì tách lại nhờ `merged_into`.

## Asset profile

Profile trả lời ba câu hỏi: *nó là gì, bình thường nó làm gì, quan trọng đến đâu*. Nội dung khác nhau theo loại asset; phần tĩnh tương đương `DeviceInfo` / `IdentityInfo`, phần hành vi tương đương `BehaviorAnalytics` của Microsoft.

### Device (host)

| Thông tin | Lấy từ OCSF |
| --- | --- |
| Cấu hình: OS/build, phần cứng, interface (MAC/IP), agent, managed hay không | Device Inventory Info 5001, object `device` trên mọi event |
| Phần mềm cài đặt, bản vá còn thiếu | Software Inventory Info 5020, OS Patch State 5004 |
| Dịch vụ cung cấp: port lắng nghe, giao thức nhận vào | Network Activity 4001 (`initiator_id`, `open_ports`), SMB 4006, RDP 4005, HTTP 4002, Live Evidence Info |
| Ai dùng máy: user, loại logon, account đặc quyền | Authentication 3002 (`user`, `dst_endpoint`, `logon_type`) |
| Process thường chạy: cặp cha → con, binary hiếm, module nạp | Process Activity 1007, Module Activity 1005 |
| Persistence quen thuộc: scheduled task, service, registry | Scheduled Job Activity 1006, Windows Service / Registry Activity (Windows extension) |
| Mạng thường gặp: peer, port đích, domain DNS, lưu lượng ra Internet | Network Activity 4001, DNS Activity 4003 |
| Nhịp hoạt động: giờ hoạt động, bật/tắt máy | `time` của mọi event, Device Power State Activity (1.9) |
| Rủi ro: lỗ hổng, cảnh báo, vi phạm cấu hình | Vulnerability Finding 2002, Detection Finding 2004, Compliance Finding 2003 |

Khác nhau theo role (role suy từ hành vi, cần thấy liên tục, ví dụ ≥ 7 ngày):

- **Workstation:** 1–2 user tương tác, giờ hành chính, process văn phòng và trình duyệt, chủ yếu kết nối ra ngoài.
- **Server:** port lắng nghe ổn định, chạy bằng service account, hiếm logon tương tác (chỉ admin), hoạt động 24/7; process mới là tín hiệu mạnh.
- **Domain Controller:** nhận Kerberos 88 và LDAP 389/636 từ rất nhiều host (bên kia là bên khởi tạo theo `initiator_id`), khối lượng 3002 lớn; criticality mặc định Very High.
- **Jump host / admin workstation:** nhiều account đặc quyền logon, dùng RDP, PsExec, MMC.
- **Unmanaged device:** chỉ có góc nhìn mạng, lấy từ 4001/4003 của máy khác (nằm ở `dst_endpoint`): IP/MAC, `mac_vendor`, port bị kết nối tới, ai nói chuyện với nó.

### Account

| Thông tin | Lấy từ OCSF |
| --- | --- |
| Định danh: SID/UID, UPN, domain, loại account, phòng ban, disabled/locked, MFA | User Inventory Info 5003, User Management 3007, object `user` (`has_mfa`) và `account` (`is_disabled`, `is_locked`) |
| Nhóm và đặc quyền | Group Management 3006 (`users[]`), Authorize Session 3003 |
| Máy dùng, nguồn đăng nhập (IP, VPN), giao thức xác thực | Authentication 3002 (`src_endpoint`, `auth_protocol_id`), Tunnel Activity 4014 |
| Tỷ lệ logon thất bại | Authentication 3002 (`status_id`) |
| Process chạy dưới account | Process Activity 1007 (`actor.user`) |
| Nhịp giờ hoạt động | `time` của 3002, 1007 |

Khác nhau theo loại:

- **Người dùng thường:** ít máy, logon tương tác, giờ hành chính, ứng dụng đa dạng.
- **Service account:** `user.type_id` = Service hoặc chỉ logon non-interactive; máy cố định, process cố định, 24/7. Một lần logon tương tác đã là bất thường.
- **Admin:** logon vào nhiều server, dùng công cụ quản trị, đúng ra xuất phát từ jump host.

### Security group

| Thông tin | Lấy từ OCSF |
| --- | --- |
| Thành viên, nhóm lồng nhau, tần suất thay đổi | Group Management 3006 |
| Mức đặc quyền (nhóm admin hay không) | Tên / SID nhóm + quyền cấp trong Authorize Session 3003 |

Profile của group chủ yếu dùng để suy ra đặc quyền và peer group cho account.

### Cloud resource (nếu trong phạm vi)

| Thông tin | Lấy từ OCSF |
| --- | --- |
| Cấu hình, vùng, mức phơi ra Internet, criticality khai báo | Cloud Resources Inventory Info 5023 (`resource_details`, có `criticality_id`) |
| Ai gọi API nào lên tài nguyên | API Activity 6003 |

### Chung cho mọi asset

- **Quan hệ:** user ↔ máy, account ↔ group, máy ↔ máy (`asset_relationship`).
- **Criticality:** `criticality_id` 1–4, suy từ role, cho phép override thủ công.
- **Baseline ba tầng như UEBA:** so với lịch sử chính asset, với peer cùng role / OU, với toàn tổ chức; mỗi đặc trưng có lookback riêng, ví dụ 30 ngày cho process, 14 ngày cho logon.

## Bẫy thường gặp

| Bẫy | Biểu hiện | Cách xử lý |
| --- | --- | --- |
| IP không phải identity | NAT, VPN, DHCP, proxy làm một IP ứng với nhiều host; chính `PublicIP` trong DeviceInfo có thể là IP của NAT hoặc proxy | IP chỉ resolve qua bảng binding `(ip, khoảng thời gian) → asset` |
| Onboard lại sinh bản ghi mới | Mỗi lần onboard tạo chữ ký mới dù cùng máy; máy wipe rồi giao người khác thì đổi tên nhưng giữ ID ([Q&A](https://learn.microsoft.com/en-au/answers/questions/1660445/how-to-remove-duplicate-devices-in-denfender-and-i), bậc 3) | Merge theo `os_machine_uuid` / `hw_info.uuid` / MAC cộng tính liên tục thời gian |
| Clone VM / golden image | Trùng `device.uid` hoặc machine SID | Tách bằng `instance_uid`, MAC, `boot_uid` |
| Tài khoản built-in | Administrator, SYSTEM tồn tại trên mọi máy | Chỉ định danh kèm Host, như quy tắc Sid + Host của Microsoft |
| Hostname không chuẩn | FQDN, NetBIOS, chữ hoa/thường lẫn lộn | Chuẩn hóa chữ thường, tách FQDN thành host + domain, lưu cả hai dạng làm identifier |
| Giá trị rác | `localhost`, `-`, `0.0.0.0`, `WORKGROUP`, `127.0.0.1` | Danh sách chặn trước bước resolve |
| Parser không đều | Nguồn này có `device.uid`, nguồn kia chỉ có IP; trường deprecated lẫn trường mới | Đo coverage identifier theo từng nguồn; kết quả quyết định độ tin cậy của inventory |
| Mạng không thuộc doanh nghiệp | Laptop kết nối mạng nhà, quán cà phê sinh peer lạ | Microsoft chỉ đưa vào inventory thiết bị trên mạng xác định là mạng doanh nghiệp; nên giới hạn tạo asset unmanaged theo dải mạng nội bộ |

## Phục vụ detection và lộ trình MVP

Microsoft dùng criticality để tạo attack path dẫn tới tài sản trọng yếu, tinh chỉnh exposure score và risk score, hỗ trợ triage incident theo ngữ cảnh và ưu tiên khuyến nghị bảo mật ([blog, bản chép lại](https://app-pack.telkomuniversity.ac.id/?p=447888)). UEBA không tự sinh incident mà làm giàu incident bằng insight và điểm ưu tiên. Inventory OCSF nên phục vụ detection theo ba cách tương tự:

- **Enrichment lúc triage:** join finding theo `asset_id` để lấy role, criticality, owner và baseline, rồi đưa vào ngữ cảnh của bước triage (LLM).
- **Rule nhận biết asset:** process hoặc user lần đầu xuất hiện trên server critical; workstation bỗng lắng nghe cổng dịch vụ; account người dùng logon vào DC.
- **Ưu tiên hóa:** risk = severity × hệ số theo `criticality_id`.

**Lộ trình MVP:**

1. Khảo sát dữ liệu: `metadata.version` và `metadata.profiles` theo nguồn; các `class_uid` thực có; coverage của `device.uid`, `os_machine_uuid`, `initiator_id`, observable type\_id 47; parser có sinh `observables` không.
2. Validate mẫu dữ liệu bằng [ocsf-toolkit](https://pkg.go.dev/github.com/ocsf/ocsf-toolkit) để phát hiện trường sai kiểu hoặc thiếu.
3. Dựng `asset` + `asset_identifier` cho device và account, chỉ dùng strong identifier.
4. Thêm bảng binding IP → asset theo thời gian; tạo asset unmanaged ở trạng thái transient.
5. Thêm lifecycle (active, stale, retired) và thuộc tính static.
6. Thêm role inference và criticality (rule + override, enum `criticality_id`).
7. Thêm baseline hành vi ba tầng, rồi tích hợp vào triage.

**Câu hỏi mở:** ngưỡng ngày cho stale/retired; danh sách dải mạng nội bộ; nguồn nào có quyền ghi đè thuộc tính khi mâu thuẫn.

## Đối chiếu với báo cáo trước

Báo cáo [2026-10-29](../2026-10-29-asset-profile-tu-event-chuan-hoa/report.md) trả lời "vendor làm thế nào" (Microsoft, Splunk, Google SecOps); báo cáo này trả lời "làm thế nào trên OCSF", nên hai báo cáo bổ sung cho nhau.

- **Khớp:** khung bốn bước (thu quan sát → nhận diện, gộp → hồ sơ khai báo, quan sát, hành vi → gắn ngược vào alert); IP chỉ có nghĩa kèm khoảng thời gian; trạng thái hiện tại là bản ghi mới nhất chưa bị gộp (`MergedToDeviceId`); critical asset 4 mức suy ra bằng luật; UEBA ba tầng baseline; chỉ theo dõi mạng doanh nghiệp.
- **Mới so với báo cáo trước:** mô hình strong/weak identifier của Sentinel làm luật gộp; tách asset và evidence; bản đồ đầy đủ nguồn asset trong OCSF 1.9.0 (class, observable type\_id, phần deprecated); mô hình năm bảng; ba điều kiện promote; pipeline sáu bước; profile theo từng loại asset; lộ trình MVP.
- **Đã sửa theo báo cáo trước và schema:** báo cáo trước nêu đúng rằng `device` không có trường criticality; bản nháp báo cáo này ngầm coi `criticality_id` là thuộc tính của asset trong OCSF, đã sửa lại thành "chỉ mượn enum".
- **Lưu ý khi dùng:** thứ tự ưu tiên nguồn (Discovery > EDR > network) và danh sách identifier mạnh cho OCSF là *đề xuất thiết kế* của báo cáo này, không phải quy định của OCSF; báo cáo trước đã chỉ ra OCSF không quy định gộp, interval hay thứ tự ưu tiên định danh. Báo cáo này không bàn Splunk và Google SecOps; xem báo cáo trước cho hai hướng đó (association có first/last seen, entity có interval).

## Chưa kiểm chứng được

- Tenzir v5.19.0 chỉ giữ đệ quy một cấp cho object OCSF như `process.parent_process`: link changelog cũ chuyển hướng tới trang trả 404.
- Ví dụ vCenter được nhận ra nhờ fingerprint device discovery cộng network connection events: nguồn là trang chép lại blog Microsoft, chưa tìm được bài gốc.
- Defender portal chia entity thành "Assets" và "Other entities": chưa mở trang Defender tương ứng.
- Transient device bị ẩn khỏi inventory mặc định: chỉ có nguồn bậc 3 (blog 51sec); docs chính thức chỉ định nghĩa cột `IsTransient`.
- Chi tiết kiểm chứng từng khẳng định: [notes/doi-chieu-kiem-chung.md](notes/doi-chieu-kiem-chung.md).

## Nguồn tham khảo

**Microsoft**

- [Microsoft Sentinel entity types reference](https://learn.microsoft.com/azure/sentinel/entities-reference)
- [Entities in Microsoft Sentinel](https://learn.microsoft.com/en-in/azure/sentinel/entities)
- [DeviceInfo table](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-deviceinfo-table)
- [Device discovery overview](https://learn.microsoft.com/en-us/defender-endpoint/device-discovery)
- [Defender device inventory](https://learn.microsoft.com/en-us/defender-endpoint/machines-view-overview)
- [Configure advanced features (duplicate devices)](https://learn.microsoft.com/en-us/defender-endpoint/advanced-features)
- [Defender for IoT device inventory](https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/device-inventory)
- [Critical asset management](https://learn.microsoft.com/en-us/security-exposure-management/critical-asset-management)
- [Classify critical assets](https://learn.microsoft.com/en-us/security-exposure-management/classify-critical-assets)
- [Predefined classifications for critical assets](https://learn.microsoft.com/en-us/security-exposure-management/predefined-classification-rules-and-levels)
- [Critical asset protection (blog, bản chép lại)](https://app-pack.telkomuniversity.ac.id/?p=447888)
- [ExposureGraphNodes table](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-exposuregraphnodes-table)
- [Query the enterprise exposure graph](https://learn.microsoft.com/en-us/security-exposure-management/query-enterprise-exposure-graph)
- [UEBA in Microsoft Sentinel](https://learn.microsoft.com/en-us/azure/sentinel/identify-threats-with-entity-behavior-analytics)
- [UEBA reference](https://learn.microsoft.com/azure/sentinel/ueba-reference)
- [Anomalies reference](https://learn.microsoft.com/azure/sentinel/anomalies-reference)
- [Microsoft Q&A: remove duplicate devices in Defender](https://learn.microsoft.com/en-au/answers/questions/1660445/how-to-remove-duplicate-devices-in-denfender-and-i) (bậc 3)
- [Microsoft Defender tips and tricks (51sec)](https://www.51sec.org/2025/05/14/microsoft-defender-tips-tricks/) (bậc 3)

**OCSF**

- [OCSF schema repo, tag v1.9.0](https://github.com/ocsf/ocsf-schema/tree/v1.9.0)
- [OCSF schema CHANGELOG](https://github.com/ocsf/ocsf-schema/blob/main/CHANGELOG.md)
- [OCSF schema releases (1.9.0)](https://github.com/ocsf/ocsf-schema/releases)
- [OCSF Device object](https://docs.tenzir.com/reference/ocsf/1-5-0/objects/device)
- [OCSF event classes](https://docs.tenzir.com/reference/ocsf/1-7-0/classes)
- [Device Inventory Info (5001)](https://docs.tenzir.com/reference/ocsf/1-3-0/classes/inventory_info)
- [Observable object](https://docs.tenzir.com/reference/ocsf/1-4-0/objects/observable)
- [OCSF observables (Splunk)](https://help.splunk.com/en/data-management/process-data-at-the-edge/use-edge-processors-for-splunk-cloud-platform/process-data-using-pipelines/convert-data-to-ocsf-format-using-an-edge-processor/ocsf-data-conversion-process)
- [OCSF Toolkit](https://pkg.go.dev/github.com/ocsf/ocsf-toolkit)
- [Understanding the Open Cybersecurity Schema Framework](https://github.com/ocsf/ocsf-docs/blob/main/overview/understanding-ocsf.md)
- [OCSF security data in Axiom (độ lớn cây đường dẫn 1.9.0)](https://axiom.co/docs/use-cases/ocsf)
- [Tenzir v5.19.0 (đệ quy một cấp cho object OCSF)](https://docs.tenzir.com/changelog/node/v5-19-0) (link nay trả 404)
