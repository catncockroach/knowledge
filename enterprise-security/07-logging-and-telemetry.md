# Logging and telemetry

> Phát hiện chỉ giỏi bằng dữ liệu nó nhìn thấy: log phải đủ nguồn, đủ chi tiết, được chuẩn hóa về một schema chung và lưu đủ lâu.

## Tại sao cần biết
Mọi rule trong SIEM chạy trên dữ liệu đã chuẩn hóa. Một cảnh báo sai có thể do logic rule, cũng có thể do lỗi thu thập hoặc parse. Hiểu đường đi của log giúp chẩn đoán đúng chỗ.

## Khái niệm cốt lõi

- **Event / log**: bản ghi về một việc đã xảy ra. NIST định nghĩa event là "any observable occurrence". Ví dụ: một dòng đăng nhập thất bại, một tiến trình khởi tạo.
- **Telemetry**: dòng dữ liệu quan sát liên tục từ hệ thống (log, metric, flow, trace).
- **Nguồn log điển hình**:
  | Nhóm | Ví dụ |
  |---|---|
  | Endpoint | Windows Event Log, Sysmon, EDR, auditd (Linux) |
  | Danh tính | Active Directory, Entra ID, Okta |
  | Mạng | Firewall, proxy, DNS, NetFlow, NDR |
  | Cloud / SaaS | AWS CloudTrail, Azure Activity, Microsoft 365 audit |
  | Ứng dụng | Web server, database, ứng dụng nghiệp vụ |
  | Bảo mật | EDR alert, email gateway, vulnerability scanner |
- **Thu thập**: *agent* trên máy, *syslog* (UDP/TCP 514), *API pull*, *event streaming*, cloud-native export.
- **Parse và chuẩn hóa**: tách log thô thành field có tên và kiểu, rồi map về schema chung để rule không cần biết định dạng từng nguồn.
- **Các schema**: **OCSF** (mở, trung lập vendor), **ECS** (Elastic), **UDM** (Google SecOps), **ASIM** (Microsoft Sentinel), **CIM** (Splunk). Cùng một khái niệm, tên field khác nhau.
- **Enrichment**: bổ sung ngữ cảnh: GeoIP, thông tin tài sản/chủ sở hữu, threat intel, danh tính.
- **Retention và tầng lưu trữ**: *hot* (tìm nhanh, đắt) → *warm/cold* (rẻ, chậm) → *archive*. Thời hạn lưu chịu ảnh hưởng của quy định tuân thủ.
- **Security data lake**: lưu log rẻ trong object storage, tách lưu trữ khỏi công cụ phân tích (ví dụ Amazon Security Lake dùng OCSF).
- **Chất lượng log**: đồng bộ thời gian (NTP, múi giờ), không rơi log, đủ độ chi tiết (bật audit policy), bảo vệ tính toàn vẹn của log.

## Cách hoạt động
```
Nguồn ─(agent/syslog/API)─► Collector ─► Parse ─► Chuẩn hóa (schema)
   ─► Enrich ─► Lưu (index / data lake) ─► Detection / Search
```

## Ví dụ
Một dòng log Windows `4625` (đăng nhập thất bại) được parse thành các field chuẩn: `user`, `src_ip`, `result=failure`, `logon_type`. Nhờ vậy cùng một rule "nhiều lần đăng nhập thất bại" áp được cho Windows, VPN và Okta, dù log gốc khác nhau.

## Hiểu nhầm thường gặp
- **"Thu càng nhiều log càng tốt"**: chi phí lưu và nhiễu tăng; chọn nguồn theo use case phát hiện.
- **"Không có alert nghĩa là không có tấn công"**: có thể do log không về hoặc parse hỏng; cần giám sát sức khỏe nguồn log.
- **Lệch giờ giữa các nguồn** làm tương quan sai thứ tự sự kiện.

## Liên quan
- [08-siem.md](08-siem.md): nơi tập trung và phân tích log.
- [15-ocsf-schema.md](15-ocsf-schema.md) → [18-asset-enrichment-in-ocsf.md](18-asset-enrichment-in-ocsf.md): đi sâu vào chuẩn hóa OCSF và enrich asset.
- [../internet/08-dns-and-dhcp.md](../internet/08-dns-and-dhcp.md): DNS log là nguồn telemetry mạng giá trị.
