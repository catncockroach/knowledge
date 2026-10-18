# SIEM

> SIEM là hệ thống tập trung log từ nhiều nguồn, chạy rule tương quan để sinh alert, và là nơi analyst tìm kiếm, điều tra.

## Tại sao cần biết
SIEM là trung tâm của security operations: nơi telemetry biến thành alert và case. Mọi khái niệm về rule, tuning, false positive đều xoay quanh nó.

## Khái niệm cốt lõi

- **SIEM** = SIM (quản lý log) + SEM (quản lý sự kiện thời gian thực). Chức năng: thu thập, chuẩn hóa, lưu, tìm kiếm, tương quan, cảnh báo, dashboard, báo cáo tuân thủ.
- **Detection / correlation rule**: truy vấn hoặc logic chạy định kỳ hoặc real-time trên event, khớp thì sinh alert. Ngôn ngữ phụ thuộc vendor: KQL (Sentinel), SPL (Splunk), YARA-L (Google SecOps), EQL / KQL / ES|QL (Elastic).
- **Các kiểu rule**: khớp đơn giản (signature), ngưỡng (threshold), chuỗi sự kiện (correlation, sequence), so khớp indicator với threat intel, "giá trị mới chưa từng thấy" (new terms), bất thường bằng ML/UEBA.
- **UEBA** (User & Entity Behavior Analytics): mô hình hóa hành vi bình thường của user/thiết bị và cảnh báo khi lệch.
- **Risk-based alerting (RBA)** (Splunk): rule không bắn alert ngay mà cộng điểm rủi ro vào một *risk object* (user, host); chỉ cảnh báo khi điểm vượt ngưỡng. Mục đích: giảm số alert bằng cách chỉ báo khi có đủ bằng chứng. Hiệu quả phụ thuộc việc curate, không tự động.
- **Alert → Case**: alert liên quan được gom thành *incident/case/offense* theo entity và cửa sổ thời gian. Đơn vị điều tra là case, không phải alert đơn lẻ.
- **Severity** (mức nghiêm trọng của rule) khác **priority** (thứ tự xử lý, có tính độ quan trọng tài sản).
- **Sản phẩm**: Splunk Enterprise Security, Microsoft Sentinel, Elastic Security, Google SecOps, IBM QRadar, và nhiều nền tảng khác. Ranh giới giữa SIEM, SOAR và UEBA đang mờ dần vì các nền tảng gộp cả ba.

## Cách hoạt động
```
Log đã chuẩn hóa ─► Rule engine ─► Alert ─► Gom thành Case
        ▲                              │
        └── threat intel, UEBA ────────┘      ─► Analyst điều tra ─► Verdict
```
Khi analyst đóng case, nhãn kết quả (xem file 09) quay lại để tuning rule: đây là vòng phản hồi trung tâm của vận hành SIEM.

## Ví dụ
Rule KQL kiểu Sentinel (giản lược): cảnh báo khi một tài khoản thất bại đăng nhập trên nhiều ứng dụng rồi thành công ngay sau đó.

```
SigninLogs
| where ResultType != 0                       // thất bại
| summarize fails=count() by UserPrincipalName, IPAddress, bin(TimeGenerated, 10m)
| where fails > 10
```
Rule này sẽ bắn nhầm với một scanner nội bộ hay một service account lỗi mật khẩu: phải tuning bằng exception hoặc watchlist.

## Hiểu nhầm thường gặp
- **"SIEM tự phát hiện mọi thứ"**: SIEM chỉ chạy những gì được viết và dữ liệu nó có; chất lượng rule và log quyết định hiệu quả.
- **"SIEM là kho log"**: kho log thuần không tạo giá trị an ninh nếu không có detection và quy trình xử lý.
- **Nhầm alert với incident**: một incident có thể gồm nhiều alert.

## Liên quan
- [07-logging-and-telemetry.md](07-logging-and-telemetry.md): đầu vào của SIEM.
- [09-detection-engineering.md](09-detection-engineering.md): cách viết, quản lý và tuning rule.
- [13-soar-xdr-and-automation.md](13-soar-xdr-and-automation.md): tự động hóa sau alert.
- [14-vendor-terminology-map.md](14-vendor-terminology-map.md): bảng map thuật ngữ giữa các vendor.
