# Detection engineering

> Detection engineering là kỹ nghệ biến hiểu biết về hành vi tấn công thành rule phát hiện, rồi kiểm thử, triển khai và liên tục tuning chúng.

## Tại sao cần biết
Chất lượng phát hiện không đến từ việc có SIEM mà từ chất lượng rule. Vấn đề lớn nhất của SOC, quá nhiều alert sai, được giải bằng chính kỷ luật này.

## Khái niệm cốt lõi

### Vòng đời rule
Ý tưởng (từ TTP, threat intel, sự cố) → viết rule → kiểm thử (dữ liệu mẫu, mô phỏng tấn công) → triển khai → vận hành & đo → tuning hoặc retire.

### Rule tốt gồm
Mô tả giả thuyết ("hành vi nào là xấu và vì sao"), logic, nguồn log cần có, mapping sang ATT&CK, mức severity, hướng dẫn triage, và các false positive đã biết.

### Sigma
Định dạng rule mở, độc lập với SIEM (YAML), có công cụ chuyển sang KQL, SPL, v.v. Giúp chia sẻ và tái sử dụng rule giữa các nền tảng.

### Detection-as-code
Rule là file trong git: review, test tự động, CI/CD triển khai, lịch sử thay đổi. Ví dụ repo `elastic/detection-rules` quản lý rule dạng TOML kèm bộ test và validate schema.

### Content của vendor và rule tùy biến
Vendor phát hành **prebuilt rule** dùng chung cho mọi khách. Khách có thể dùng nguyên, thêm *exception*, hoặc nhân bản thành *custom rule* tự duy trì (lúc đó không nhận cập nhật từ vendor). Cách đóng gói tốt: `rule_id` ổn định, có version, exception list/watchlist tách khỏi rule.

### Độ chính xác của phát hiện
|  | Có tấn công thật | Không có tấn công |
|---|---|---|
| **Rule bắn** | True Positive (TP) | False Positive (FP) |
| **Rule im** | False Negative (FN) | True Negative |

- **Benign True Positive (BTP)**: logic đúng, hành vi có thật nhưng hợp lệ (admin chạy script, pentest đã duyệt).
- **FN** nguy hiểm nhất và không có alert nào để gán nhãn, nên vô hình với dữ liệu về FP. Giảm FP quá tay có thể tăng FN.
- **Precision** = TP / (TP + FP); **recall** = TP / (TP + FN).

### Tuning
Giảm FP mà không mất phát hiện thật. Công cụ theo mức xâm lấn tăng dần:
1. **Exception / allowlist hẹp** (một entity, một đường dẫn, có hạn dùng) cho BTP.
2. **Watchlist** dùng chung nhiều rule, sửa không cần đụng rule.
3. **Sửa logic** (thêm điều kiện, đổi ngưỡng, đổi severity).
4. **Sửa parser / nguồn dữ liệu** khi FP đến từ lỗi chuẩn hóa.
5. **Retire** rule không còn giá trị.

Nguyên tắc: đề xuất tuning phải nêu *phạm vi* (một khách/môi trường hay rule gốc dùng chung), giữ exception hẹp và có chủ sở hữu, và đo lại sau thay đổi.

## Cách hoạt động
```
Alert ─► Analyst gán verdict (TP / BTP / FP-logic / FP-data)
   ─► gom mẫu FP lặp lại ─► chọn kiểu tuning ─► review ─► triển khai ─► đo lại
```
Microsoft Sentinel tách sẵn các nhãn "False Positive – incorrect alert logic" và "False Positive – incorrect data", nên có thể định tuyến thẳng sang sửa rule hay sửa parser.

## Ví dụ
Rule bắn mỗi đêm vì job backup của `svc-backup` chạy `powershell -enc`. Đây là BTP lặp lại: thêm exception giới hạn theo (tài khoản `svc-backup`, host backup, đường dẫn script), đặt ngày hết hạn để rà soát lại, thay vì tắt rule hay nới điều kiện cho mọi người.

## Hiểu nhầm thường gặp
- **"Mục tiêu là FP bằng 0"**: đánh đổi với recall; chấp nhận một mức nhiễu.
- **"FP luôn là lỗi rule"**: có thể do dữ liệu (parse), hoặc hành vi hợp lệ (BTP).
- **Tuning bằng cách nới cho cả hệ thống** vì một mẫu cục bộ: tạo điểm mù mới.

## Liên quan
- [02-threats-and-attack-lifecycle.md](02-threats-and-attack-lifecycle.md): nguồn ý tưởng rule (TTP).
- [08-siem.md](08-siem.md): nơi rule chạy.
- [11-soc-organization.md](11-soc-organization.md): ai tạo nhãn, ai sửa rule.
- Nghiên cứu chuyên sâu về dùng LLM để tuning: [../research/2026-10-18-llm-tuning-rule-giam-false-positive/report.md](../research/2026-10-18-llm-tuning-rule-giam-false-positive/report.md).
