# Vendor terminology map

> Cùng một khái niệm, mỗi nền tảng gọi một tên khác nhau; bảng map giúp đọc tài liệu và dữ liệu từ nhiều hệ mà không nhầm.

## Tại sao cần biết
"Event" trong QRadar không phải "event" của NIST, "notable" của Splunk là alert, "incident" của Sentinel khác "offense" của QRadar. Khi làm việc với nhiều hệ, hoặc thiết kế công cụ chạy trên dữ liệu từ nhiều hệ, cần một bảng dịch.

## Khái niệm cốt lõi

Bảng map (dựa trên tài liệu chính thức của các vendor; ô có `?` là chưa xác minh bằng docs):

| Khái niệm chung | Splunk ES (7.x) | Microsoft Sentinel | Elastic Security | Google SecOps | IBM QRadar |
|---|---|---|---|---|---|
| Schema chuẩn hóa | CIM | ASIM | ECS | UDM | DSM parse thành event/flow |
| Rule | Correlation search (SPL); risk rule (RBA) | Analytics rule (KQL), nay là custom detections | Detection rule (query, threshold, EQL, ES\|QL, indicator match, new terms, ML) | Rule YARA-L | Custom rule (CRE): event, flow, offense rule |
| Đầu ra của rule | Notable event; risk notable | Alert | Alert | Detection / alert | Event được rule đánh dấu → Offense |
| Đơn vị điều tra | Notable / Incident Review | Incident | Case (?) | Case | Offense |
| Mức quan trọng | Urgency, risk score | Severity | Severity, risk score | Severity, priority | Magnitude (0–10) |
| Tự động hóa | Adaptive response | Automation rule + playbook (Logic Apps) | Rule actions (?) | SOAR playbook, case playbook | Thường nối SOAR ngoài |
| Nhãn khi đóng | Disposition (?) | True Positive / Benign Positive / False Positive (logic) / False Positive (data) / Undetermined | ? | ? | Đánh dấu false positive |
| Cơ chế exception | Lookup/allowlist | Automation rule exception (có hạn), watchlist, sửa query | Rule exception, shared exception list | Alert suppression, sửa rule | Tuning rule/building block (?) |

Các hệ khác: TheHive (case management mã nguồn mở) tiếp nhận *alert* từ ngoài, rồi tạo/gộp thành *case* chia task và gắn *observable*; không có engine rule.

### Quy tắc đọc chéo
- Tên của bước "đơn vị điều tra" quyết định cách đếm khối lượng: số alert ≠ số incident/case/offense.
- Cùng chữ "event" có thể là log thô (QRadar) hoặc mọi quan sát (NIST).
- Vendor đang đổi thuật ngữ theo phiên bản (ví dụ Sentinel chuyển sang Defender portal và custom detections; Splunk ES 8.x có thể đổi "notable"); luôn kiểm tra phiên bản.

## Cách hoạt động
Khi xử lý dữ liệu đa vendor, chuẩn hóa về một **từ vựng trung gian** (alert, case, verdict, entity, severity) trước, rồi map ngược khi hành động ngược lại vào từng hệ.

## Ví dụ
Đếm "bao nhiêu sự cố tuần này": Sentinel đếm *incident*, Splunk đếm *notable* (có thể nhiều notable cho một vấn đề), QRadar đếm *offense*. So sánh trực tiếp ba con số này mà không quy về cùng đơn vị là sai.

## Hiểu nhầm thường gặp
- **"Mọi SIEM đều có Benign Positive"**: không phải hệ nào cũng tách nhãn này.
- **"Bảng này đúng mãi"**: thuật ngữ và sản phẩm thay đổi nhanh; dùng làm điểm khởi đầu, kiểm tra lại docs.

## Liên quan
- [08-siem.md](08-siem.md): khái niệm chung của SIEM.
- [09-detection-engineering.md](09-detection-engineering.md): TP/BTP/FP và tuning.
- Nguồn trích dẫn chi tiết cho bảng này: [../research/2026-10-18-llm-tuning-rule-giam-false-positive/notes/domain-kien-truc-soc.md](../research/2026-10-18-llm-tuning-rule-giam-false-positive/notes/domain-kien-truc-soc.md) (mục 5).
