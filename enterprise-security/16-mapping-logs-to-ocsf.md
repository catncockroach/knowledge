# Mapping logs to OCSF

> Map log là biến một bản ghi thô của SIEM, EDR hay firewall thành một event OCSF: chọn đúng class và activity, đưa từng field về đúng attribute, chuẩn hóa giá trị liệt kê và thời gian, giữ lại phần không map được.

## Tại sao cần biết
Rule, dashboard và bước enrich asset chỉ đúng khi mapping đúng. Hai lỗi mapping hay gặp là đặt nhầm máy vào `device` thay vì `src_endpoint` và để nguyên giá trị chuỗi của nguồn thay vì chuyển sang `_id`. Khi đó tra asset profile sai máy, còn rule lọc theo `status_id` bỏ sót event. File này nối [15-ocsf-schema.md](15-ocsf-schema.md) (cấu trúc đích) với [18-asset-enrichment-in-ocsf.md](18-asset-enrichment-in-ocsf.md) (làm giàu sau khi map).

## Khái niệm cốt lõi
- **Parse** và **map** là hai bước khác nhau:
  - *Parse*: tách log thô (syslog, CEF, JSON, XML của Windows) thành cặp field–giá trị theo tên của nguồn.
  - *Map*: đổi tên, đổi kiểu, đổi giá trị các field đó sang attribute OCSF.
- **Mapping theo nguồn và loại event**: một nguồn sinh nhiều loại event, mỗi loại thuộc một class. Khóa chọn class thường là mã sự kiện (`EventID` của Windows, `event_type` của EDR, `action` của firewall).
- **Ba vai trò máy trong event**:
  - `device`: máy *ghi nhận* sự kiện (host cài agent EDR, máy sinh Windows log, chính firewall).
  - `src_endpoint` / `dst_endpoint`: máy *nguồn* và *đích* của kết nối hay của phiên đăng nhập.
  - `actor`: chủ thể gây ra hành động (user, process).
- **Chuẩn hóa giá trị**: chuỗi của nguồn (`"FAILED"`, `"blocked"`, `"high"`) phải đổi sang `status_id`, `action_id`, `severity_id`; caption có thể giữ chuỗi gốc khi `_id = 99` (Other).
- **Chuẩn hóa thời gian**: `time` là epoch milliseconds UTC; chuỗi thời gian gốc giữ ở `metadata.original_time`. Thời điểm pipeline xử lý ghi vào `metadata.processed_time`.
- **Giữ dấu vết**: `metadata.event_code` (mã sự kiện gốc), `metadata.original_event_uid` (ID gốc), `metadata.product` (sản phẩm nguồn), `unmapped`, `raw_data`.
- **Alert khác event**: alert của EDR hay notable/offense của SIEM là *finding*, map vào category Findings (vd Detection Finding `2004`), không phải vào class hoạt động.

## Cách hoạt động

```
Log thô ──► Parse (tách field theo nguồn)
        ──► Chọn class + activity (theo mã event)
        ──► Map field ──► device / actor / src_endpoint / dst_endpoint / class fields
        ──► Chuẩn hóa enum (_id), thời gian (ms UTC), kiểu (IP, số)
        ──► Điền metadata (product, version, event_code, tenant_uid)
        ──► Sinh observables[] từ các field quan trọng
        ──► Field thừa → unmapped · log gốc → raw_data
        ──► Enrich (asset, identity, geo, threat intel) ──► Lưu
```

### Bảng chọn class cho nguồn SIEM/EDR điển hình

| Log nguồn | Class OCSF | `class_uid` | `activity_id` |
|---|---|---|---|
| EDR process create, Sysmon Event ID 1, Windows 4688 | Process Activity | 1007 | 1 Launch |
| Windows 4624 / 4625 (đăng nhập thành công / thất bại) | Authentication | 3002 | 1 Logon, `status_id` 1 / 2 |
| Firewall allow/deny, NetFlow | Network Activity | 4001 | 6 Traffic, 1 Open, 5 Refuse... |
| DNS query log | DNS Activity | 4003 | 1 Query |
| EDR alert, SIEM notable/offense | Detection Finding | 2004 | 1 Create, 2 Update, 3 Close |
| Danh sách máy từ EDR console, MDM | Device Inventory Info | 5001 | 2 Collect |
| Kết quả quét lỗ hổng | Vulnerability Finding | 2002 | 1 Create |

## Ví dụ
Windows Security log `4625` (đăng nhập thất bại) do domain controller `DC01` ghi, người đăng nhập từ máy `WS-0412`:

```
EventID=4625  Computer=DC01.corp.local  TargetUserName=lan.nguyen  TargetDomainName=CORP
LogonType=3  IpAddress=10.20.4.12  WorkstationName=WS-0412  AuthenticationPackageName=NTLM
```

| Field nguồn | Attribute OCSF | Ghi chú |
|---|---|---|
| `EventID=4625` | `class_uid 3002`, `activity_id 1`, `status_id 2` (Failure), `metadata.event_code "4625"` | 4624 cũng là Logon, chỉ khác `status_id 1` |
| `Computer` | `device.hostname = "DC01.corp.local"` và `dst_endpoint.hostname` | DC là máy ghi log và là đích xác thực |
| `TargetUserName`, `TargetDomainName` | `user.name`, `user.domain` | Tài khoản bị thử đăng nhập |
| `LogonType=3` | `logon_type_id 3` (Network) | Enum OCSF trùng giá trị Windows |
| `IpAddress`, `WorkstationName` | `src_endpoint.ip`, `src_endpoint.hostname` | Máy người dùng là *nguồn*, không phải `device` |
| `AuthenticationPackageName=NTLM` | `auth_protocol_id 1` (NTLM) | |
| Các field còn lại (`SubStatus`, `LogonProcessName`) | `status_detail` hoặc `unmapped` | |

Kết quả: `type_uid = 300201`. Ở bước enrich, cả `device` (DC01) và `src_endpoint` (WS-0412) đều cần tra asset profile, và chúng là hai máy khác nhau.

## Hiểu nhầm thường gặp
- **"`device` luôn là máy người dùng"**: `device` là nơi sự kiện được ghi. Với log DC, firewall hay proxy, máy người dùng nằm ở `src_endpoint`.
- **"Giữ nguyên chuỗi severity của vendor là đủ"**: mỗi vendor có thang riêng; phải quy về `severity_id` 0–6 và 99, nếu không rule ưu tiên theo mức độ sẽ sai.
- **"Một nguồn ứng với một class"**: EDR sinh process, file, network, registry, alert..., mỗi loại một class; mapping phải rẽ nhánh theo mã event.
- **"Map xong là xong"**: schema nguồn đổi theo phiên bản agent; cần giám sát tỷ lệ field rơi vào `unmapped` và tỷ lệ event `class_uid` không xác định để phát hiện parser hỏng.

## Liên quan
- [15-ocsf-schema.md](15-ocsf-schema.md): class, object, profile mà mapping nhắm tới.
- [17-asset-inventory-and-profile.md](17-asset-inventory-and-profile.md): dữ liệu asset sẽ được gắn vào event sau khi map.
- [18-asset-enrichment-in-ocsf.md](18-asset-enrichment-in-ocsf.md): bước enrich trong pipeline trên.
- [08-siem.md](08-siem.md): rule chạy trên event đã chuẩn hóa.
