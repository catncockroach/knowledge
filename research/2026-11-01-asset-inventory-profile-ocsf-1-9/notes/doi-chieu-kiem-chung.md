# Đối chiếu và kiểm chứng

Ngày kiểm: 2026-11-01. Báo cáo gốc do chủ repo viết; ghi chú này ghi lại từng khẳng định đã đối chiếu, với nguồn nào, và kết quả.

## Nguồn dùng để kiểm

- **Schema OCSF chính thức:** clone `github.com/ocsf/ocsf-schema` tại tag `v1.9.0` (commit `856d462`, 2026-08-03), đọc trực tiếp `dictionary.json`, `objects/`, `events/`, `profiles/`, `CHANGELOG.md` (bậc 1).
- **Microsoft Sentinel entity types reference**, cập nhật 2026-06-28 (bậc 1). https://learn.microsoft.com/en-us/azure/sentinel/entities-reference
- **DeviceInfo table**, cập nhật 2026-08-10 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-deviceinfo-table
- **Defender for IoT device inventory**, cập nhật 2026-08-07 (bậc 1). https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/device-inventory
- **Axiom, OCSF security data** (bậc 2). https://axiom.co/docs/use-cases/ocsf
- **Báo cáo kế thừa** `research/2026-10-29-asset-profile-tu-event-chuan-hoa/report.md` cho các ý về critical asset, UEBA, MergedToDeviceId.

## Khớp với nguồn

| Khẳng định | Kết quả kiểm |
|---|---|
| OCSF 1.9.0 phát hành 3/8/2026 | Khớp: CHANGELOG "[v1.9.0] - Aug 3rd, 2026", tag cùng ngày |
| Category 1–8, gồm 8 Unmanned Systems | Khớp `categories.json` |
| Class 5001, 5003, 5004, 5020, 5023, Live Evidence Info (5040), 3002, 3003, 3006, 3007, 3008, 4001–4006, 4014, 1005–1007, 2002–2004, 6003 | Khớp tên và UID |
| 3007 User Management, 3008 Role Management, Device Power State Activity (1011) mới ở 1.9 | Khớp CHANGELOG 1.9.0 (#1603, #1624) |
| 5001 có activity 1 Log, 2 Collect | Khớp (kế thừa từ class `discovery`) |
| Account Change 3001, User Access Management 3005 deprecated từ 1.9 thay bằng 3007 | Khớp |
| Device Config State 5002 deprecated từ 1.5; các class Query deprecated từ 1.5 thay bằng Live Evidence Info | Khớp |
| `user_result` → `updated_user`; `group_management.user` → `users`; `actor.app_name/app_uid` → `application`; `is_src_dst_assignment_known` → `initiator_id`; `device_hw_info.cpu_*` → `cpu_info_list[*]` (đều từ 1.9.0) | Khớp `@deprecated` trong schema |
| `initiator_id`, `cpu_info_list`, `peripheral_devices` mới ở 1.9; `mac_vendor`, `account.is_disabled/is_locked` ở 1.8; `observable.event_uid/type_uid`, `metadata.original_event_uid` ở 1.7; `open_ports`, `network_scope_id`, `user.type_id` Service ở 1.6 | Khớp CHANGELOG theo đúng phiên bản |
| Observable type_id 1 Hostname, 2 IP, 3 MAC, 4 User Name, 20 Endpoint, 21 User, 47 `device.uid` (1.6), 48 `network_endpoint.uid` (1.7), 49/50 `iam_role.name/uid` (1.9) | Khớp |
| `device` kế thừa `endpoint`, ràng buộc `at_least_one` gồm ip, uid, name, hostname, instance_uid, interface_uid, interface_name | Khớp `objects/endpoint.json` |
| Phần tử đầu của `network_interfaces` là thông tin mạng của chính event | Khớp mô tả trong `dictionary.json` |
| Authentication: `actor.user` gắn `src_endpoint`, `user` gắn `dst_endpoint` | Khớp `associations` của class 3002 |
| Profile `host` gồm `device`, `actor` | Khớp `profiles/host.json` |
| `criticality_id` mới ở 1.9.0: Unknown 0, Low 1, Medium 2, High 3, Very High 4, Other 99, đi cặp `criticality` | Khớp (#1693) |
| Sentinel: tối đa 3 identifier mỗi entity mapping; bảng strong/weak của Host, Account, IP, Process, Security group, Mailbox, IoT device, Cloud application, DNS, File, Registry, Malware, Mail | Khớp nguyên văn |
| Sentinel loại khỏi alert account chỉ có Name khi tên là ADMIN, ADMINISTRATOR, SYSTEM, ROOT, NETWORK SERVICE… | Khớp; danh sách đầy đủ có 11 tên |
| Sentinel có 20 entity type | Khớp danh sách schema |
| DeviceInfo: `DeviceCategory` (Endpoint, Network device, IoT, Unknown); `PublicIP` có thể là IP của NAT hoặc proxy | Khớp |
| Defender for IoT gộp thiết bị cùng zone có tổ hợp đặc tính giống nhau (cùng IP và MAC); cùng MAC khác IP thì không gộp | Khớp nguyên văn |
| Cây đường dẫn đầy đủ của OCSF 1.9.0 vượt 100.000 | Khớp Axiom: "the full closure of OCSF 1.9.0 runs to over 100,000 paths" |

## Không khớp, đã sửa trong báo cáo

| Khẳng định gốc | Thực tế | Sửa |
|---|---|---|
| "OCSF 1.9.0 đã có `criticality_id` … nên dùng làm enum chính thức" (ngầm hiểu là thuộc tính của asset) | Trong 1.9.0, `criticality_id` chỉ được gắn vào object `resource_details`; `device`, `user`, `endpoint` **không** có trường này. Báo cáo kế thừa đã nêu đúng điểm này | Ghi rõ: dùng enum `criticality_id` trong bảng `asset_profile` là lựa chọn thiết kế, không đọc được criticality từ `device` |
| DeviceInfo: "thiết bị gửi báo cáo đầy đủ mỗi giờ và mỗi khi có thay đổi so với heartbeat trước"; truy vấn `arg_max(Timestamp, *)` | Trang hiện hành chỉ ghi "The DeviceInfo table is updated continuously, and all updates contain the full current device data"; truy vấn mẫu dùng `arg_max(IngestionTime, *) by DeviceId` | Thay bằng câu của docs hiện hành |
| Transient devices dẫn blog 51sec: "thiết bị chưa thấy đủ lâu để thu thập đủ thông tin", "ẩn khỏi inventory" | Nguồn chính thức: cột `IsTransient` của DeviceInfo, "classified as short-lived or transient based on the frequency of appearance of the device on the network"; Defender for IoT: "detected for only a short time" | Dùng định nghĩa chính thức; ý "ẩn khỏi inventory" giữ lại, ghi là nguồn bậc 3 |

## Chưa kiểm chứng được

- Tenzir v5.19.0 giữ đệ quy một cấp cho object như `process.parent_process`: link `docs.tenzir.com/changelog/node/v5-19-0` chuyển hướng sang `tenzir.com/...` và trả 404.
- Ví dụ vCenter được nhận ra nhờ fingerprint device discovery cộng network connection events: nguồn là trang `app-pack.telkomuniversity.ac.id` chép lại blog, không phải trang gốc của Microsoft. Báo cáo kế thừa có nguồn chính thức cho việc ESXi/vCenter được xếp High (Predefined classifications).
- Defender portal chia entity thành "Assets" và "Other entities": chưa mở trang Defender tương ứng.
