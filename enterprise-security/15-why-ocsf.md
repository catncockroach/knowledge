# Why OCSF

> Chuẩn hóa log về một schema chung biến hàng chục định dạng log khác nhau thành một ngôn ngữ duy nhất; OCSF là schema mở, trung lập vendor, mô tả sự kiện theo class có kiểu chặt, nên dữ liệu viết một lần dùng được cho mọi công cụ và mọi mục đích phân tích.

## Tại sao cần biết
Ở [07-logging-and-telemetry.md](07-logging-and-telemetry.md), chuẩn hóa chỉ là một bước trong pipeline. Thực ra, chất lượng của mọi thứ phía sau đều do nó quyết định: rule, dashboard, điều tra, enrich, quản lý tài sản, cả ML và LLM. File này trả lời hai câu: vì sao phải chuẩn hóa, và vì sao chọn OCSF thay vì schema của một vendor. Các file 16–22 đi tiếp từ cấu trúc schema đến ứng dụng.

## Khái niệm cốt lõi

### Vấn đề: cùng một sự thật, mười cách viết
Cùng khái niệm "tên máy", mỗi nguồn ghi một kiểu:

| Nguồn | Field chứa tên máy |
|---|---|
| Windows Security log | `Computer`, `WorkstationName` |
| Một EDR | `ComputerName` hoặc `DeviceName` |
| Firewall syslog/CEF | `shost`, `dhost`, hoặc chỉ có IP |
| Cloud audit | ID của instance, không có hostname |

Khác nhau không chỉ ở tên field:
- **Ngữ nghĩa**: `src` của firewall là máy nguồn kết nối; `Computer` của Windows là máy ghi log.
- **Giá trị**: thang severity, chuỗi kết quả (`FAILED`, `0xC000006A`, `deny`) mỗi nơi một kiểu.
- **Thời gian**: syslog không có năm và múi giờ, Windows dùng UTC, có nguồn dùng giờ địa phương.
- **Cấu trúc**: có nguồn phẳng, có nguồn lồng nhiều tầng.

### Bài toán N × M
Có N nguồn log và M thứ cần dùng log: rule, dashboard, hunting, báo cáo tuân thủ, quản lý tài sản, model ML. Không có schema chung thì mỗi cặp nguồn–công dụng phải tự hiểu định dạng của nhau, tức N × M chỗ phải viết và bảo trì. Có schema chung, mỗi nguồn chỉ map **một lần** (N mapping), mỗi công dụng chỉ viết **một lần** trên schema (M), tổng còn N + M.

```
Không chuẩn hóa                      Có schema chung
EDR ──┬─► rule                       EDR ──┐            ┌─► rule
FW  ──┼─► dashboard                  FW  ──┼─► OCSF ────┼─► dashboard
AD  ──┼─► asset inventory            AD  ──┤            ├─► asset inventory
VPN ──┴─► ML                         VPN ──┘            └─► ML
(mỗi mũi tên là một parser riêng)    (map 1 lần / viết 1 lần)
```

### Một schema tốt cho bạn những gì
- **Tên chung**: một khái niệm, một tên (`device.hostname`).
- **Kiểu chung**: IP là IP, thời gian là epoch milliseconds UTC.
- **Ngữ nghĩa chung**: `device` luôn là nơi ghi nhận, `src_endpoint` luôn là nguồn.
- **Giá trị liệt kê chung**: `status_id 2` luôn là Failure, bất kể nguồn viết thế nào.
- **Phân loại chung**: mọi event thuộc đúng một class, biết class là biết event có những field nào.

### Vì sao là OCSF
- **Mở và trung lập vendor**: OCSF ra mắt năm 2022 do AWS và Splunk khởi xướng, dựa trên schema mà Symantec (nay thuộc Broadcom) phát triển trước đó, có nhiều vendor bảo mật cùng tham gia. Bản 1.0 phát hành năm 2023. Từ tháng 11/2024 dự án thuộc Linux Foundation. Mã nguồn schema theo giấy phép Apache 2.0.
- **Mô hình class có kiểu chặt**: mỗi loại sự kiện là một class với attribute được định nghĩa sẵn, có mức required/recommended và enum. Các schema dạng "tập field dùng chung" phân loại event bằng vài field nhãn và để nguồn tự chọn field cần điền.
- **Không gắn với một công cụ**: CIM của Splunk, ASIM của Sentinel, UDM của Google SecOps sinh ra để phục vụ nền tảng của chính vendor đó. OCSF không thuộc nền tảng nào, nên cùng một dữ liệu dùng được trong SIEM, data lake, công cụ tự viết.
- **Mở rộng có quy tắc**: profile thêm ngữ cảnh mà không cần class mới; extension cho phép thêm field riêng mà không phá schema lõi.
- **Có phiên bản**: schema đánh số theo SemVer; mỗi event ghi `metadata.version` để biết nó theo bản nào.
- **Bao cả finding và inventory**: ngoài event hoạt động, OCSF có class cho alert/finding và cho inventory (máy, phần mềm, user). Nhờ vậy log sự kiện, alert và dữ liệu tài sản cùng nằm trong một schema, điều kiện tiên quyết để làm quản lý tài sản từ log ([20-asset-profiling-from-ocsf-logs.md](20-asset-profiling-from-ocsf-logs.md)).

### Lợi ích khi mọi nguồn đã về OCSF
1. **Viết rule một lần**: rule "đăng nhập thất bại hàng loạt" lọc `class_uid = 3002 AND status_id = 2` là chạy được cho AD, VPN, SSO.
2. **Tương quan chéo nguồn**: nối event EDR, firewall, AD bằng cùng khóa (`device.uid`, `user.name`, `src_endpoint.ip`) mà không cần bảng dịch.
3. **Đọc event theo một quy trình cố định**, không cần biết nguồn ([17-reading-an-ocsf-event.md](17-reading-an-ocsf-event.md)).
4. **Enrich một lần tại điểm chung**: gắn asset profile vào `device` thì mọi nguồn đều được hưởng ([21-asset-enrichment-in-ocsf.md](21-asset-enrichment-in-ocsf.md)).
5. **Phân tích lấy thực thể làm trung tâm**: vì máy, user, process luôn nằm ở cùng object, có thể gom mọi event theo một máy hay một user để dựng profile, baseline, timeline ([22-asset-data-use-cases.md](22-asset-data-use-cases.md)).
6. **Đo được chất lượng dữ liệu**: thiếu field required, enum sai, tỷ lệ `unmapped` đều đếm được theo từng nguồn.
7. **Đổi công cụ không phải làm lại dữ liệu**: chuyển SIEM hay thêm data lake vẫn giữ nguyên lớp dữ liệu.
8. **Đầu vào ổn định cho ML/LLM**: feature và prompt dựa trên field cố định, không phải học lại theo từng nguồn.

### Cái giá phải trả
- **Công sức mapping**: mỗi nguồn và mỗi loại event cần mapping riêng, phải bảo trì khi nguồn đổi định dạng.
- **Mất độ chi tiết**: field đặc thù của nguồn không có chỗ thì rơi vào `unmapped`, khó truy vấn hơn.
- **Schema còn tiến hóa**: class và field mới được thêm theo phiên bản; pipeline phải theo kịp.
- **Hỗ trợ không đồng đều**: sản phẩm "hỗ trợ OCSF" có thể chỉ xuất một phần class hoặc điền ít field; cần kiểm tra thực tế.

## Cách hoạt động
Chuẩn hóa là một lớp nằm giữa nguồn và công dụng:

```
Tầng nguồn       EDR · SIEM · firewall · AD/IdP · cloud · MDM · scanner
                     │ parse + map (18)
Tầng dữ liệu     Event OCSF (16) ──► đọc hiểu (17)
                     │ enrich bằng asset profile (19, 21)
                     │ ◄── profile được dựng lại từ chính event OCSF (20)
Tầng ứng dụng    detection · triage · hunting · IR · quản lý tài sản · tuân thủ (22)
```

## Ví dụ
Câu hỏi: "Trong 24 giờ qua, máy `WS-0412` có những lần đăng nhập thất bại nào?"

- **Không chuẩn hóa**: viết ba truy vấn. Windows: `EventID=4625 AND WorkstationName=WS-0412`. VPN: `action=auth-fail AND client_name=ws-0412`. SSO: `outcome.result=FAILURE AND client.device=WS-0412`. Thêm nguồn thứ tư thì viết truy vấn thứ tư.
- **Đã về OCSF**: một truy vấn cho mọi nguồn:

```sql
SELECT time, metadata.product.name, user.name, src_endpoint.ip
FROM ocsf_events
WHERE class_uid = 3002 AND status_id = 2
  AND (src_endpoint.hostname = 'WS-0412' OR device.hostname = 'WS-0412')
  AND time > now() - interval '24' hour
```

## Hiểu nhầm thường gặp
- **"Dùng OCSF thì không cần biết log gốc"**: người viết mapping vẫn phải hiểu sâu từng nguồn; OCSF chỉ giúp người *dùng* dữ liệu không phải biết.
- **"OCSF thay thế SIEM"**: OCSF là mô hình dữ liệu; SIEM, data lake là nơi lưu và xử lý dữ liệu theo mô hình đó.
- **"Chuẩn hóa xong là dữ liệu tốt"**: map sai vai trò máy, enum sai hay thiếu thời gian vẫn cho dữ liệu "đúng schema nhưng sai nghĩa".
- **"Schema nào cũng như nhau"**: khác biệt nằm ở tính trung lập, độ chặt của kiểu, và phạm vi (có bao cả finding, inventory hay không).

## Liên quan
- [07-logging-and-telemetry.md](07-logging-and-telemetry.md): vị trí của chuẩn hóa trong đường đi của log.
- [14-vendor-terminology-map.md](14-vendor-terminology-map.md): schema của từng vendor.
- [16-ocsf-schema.md](16-ocsf-schema.md): cấu trúc chi tiết của OCSF.
- [22-asset-data-use-cases.md](22-asset-data-use-cases.md): dữ liệu sạch được dùng vào việc gì.
