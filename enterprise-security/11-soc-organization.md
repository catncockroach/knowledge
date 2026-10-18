# SOC organization

> SOC (Security Operations Center) là đội ngũ, quy trình và công nghệ làm việc giám sát, phát hiện và ứng phó sự cố an ninh liên tục.

## Tại sao cần biết
Công cụ chỉ có tác dụng qua con người và quy trình vận hành. Biết ai làm gì, ai tạo nhãn, ai sửa rule giúp hiểu vì sao hệ thống alert vận hành như hiện tại và đâu là điểm nghẽn.

## Khái niệm cốt lõi

### Ba trụ cột: People – Process – Technology
SOC cần nhân sự (24/7 hay giờ hành chính), quy trình (triage, escalation, IR) và công nghệ (SIEM, EDR, SOAR, TIP, case management).

### Mô hình tier
| Tier | Vai trò | Việc chính | Kinh nghiệm điển hình |
|---|---|---|---|
| **L1** | Triage analyst | Theo dõi hàng đợi alert, triage ban đầu, đóng FP hoặc escalate, theo playbook | 0–2 năm |
| **L2** | Incident responder | Điều tra sâu, tương quan log, tìm root cause, containment | 2–5 năm |
| **L3** | Senior / hunter | Threat hunting, detection engineering, reverse malware, phân tích CTI | 5 năm trở lên |

Mô hình thay thế (pod-based, platform + automation) đang được áp dụng, nhưng tier vẫn là ngôn ngữ phổ biến.

### Các vai trò chuyên biệt
- **Detection engineer**: viết, kiểm thử, tuning rule mà SOC dùng (khác threat hunter, người săn theo giả thuyết).
- **Threat intel analyst**, **forensics / IR specialist**, **SOC manager**, **SOC engineer** (duy trì nền tảng SIEM/SOAR, kết nối log).

### Mô hình triển khai
| Mô hình | Đặc điểm |
|---|---|
| **In-house** | Tự xây và vận hành; kiểm soát cao, chi phí và gánh nhân sự lớn |
| **MSSP** (Managed Security Service Provider) | Giám sát thiết bị/SIEM của khách; thường thông báo cho khách xử lý |
| **MDR** (Managed Detection & Response) | Dịch vụ SOC từ xa dùng công nghệ chọn sẵn; tự điều tra và phản ứng/ngăn chặn trong phạm vi đã thỏa thuận (theo định nghĩa của Gartner) |
| **Hybrid** | Phối hợp: in-house cho khu vực nhạy cảm, thuê ngoài ca đêm hoặc mảng chuyên biệt |

Ranh giới MSSP/MDR chồng lấn ngày càng nhiều.

### Multi-tenant
MSSP/MDR vận hành cho nhiều khách. Mô hình điển hình trên Sentinel: mỗi khách một workspace, quản lý tập trung từ tenant của nhà cung cấp. Hệ quả cho tuning: sửa rule gốc ảnh hưởng mọi khách, còn exception chỉ ảnh hưởng một khách.

### Metric
- **MTTD** (mean time to detect), **MTTR** (mean time to respond/resolve): không có công thức chuẩn thống nhất, mỗi tổ chức định nghĩa riêng.
- Tỷ lệ TP/FP, số alert mỗi analyst, thời gian triage, độ phủ ATT&CK.

### Alert fatigue
Khối lượng alert vượt khả năng xử lý, trong đó nhiều alert là nhiễu, khiến analyst bỏ sót alert thật hoặc kiệt sức. Các khảo sát công bố con số rất khác nhau: tỷ lệ FP do analyst tự ước tính từ khoảng 46% đến 83%, và một phần lớn alert không được điều tra kịp. Đây là số tự đánh giá hoặc do vendor tài trợ, nên coi là chỉ báo về cỡ vấn đề, không phải thước đo chính xác.

## Cách hoạt động
```
Alert ─► L1 triage ─┬─► đóng (FP/BTP, ghi verdict)
                    └─► escalate ─► L2 điều tra ─► L3 / IR (nếu nặng)
verdict ─► detection engineer ─► tuning rule ─► ít nhiễu hơn
```
Chất lượng nhãn do L1/L2 tạo ra quyết định chất lượng tuning về sau.

## Ví dụ
Một MDR phục vụ 50 khách: cùng một mẫu FP (backup agent chạy PowerShell) xuất hiện ở 30 khách → tín hiệu nên sửa rule gốc. Mẫu chỉ ở một khách có script riêng → exception cục bộ.

## Hiểu nhầm thường gặp
- **"Thuê MDR là xong"**: khách vẫn phải chịu trách nhiệm về cấu hình, quyền phản ứng và quyết định kinh doanh.
- **"Nhiều analyst hơn giải quyết alert fatigue"**: gốc rễ thường ở chất lượng rule và dữ liệu.

## Liên quan
- [09-detection-engineering.md](09-detection-engineering.md): vòng phản hồi từ nhãn đến tuning.
- [12-incident-response.md](12-incident-response.md): quy trình ứng phó mà SOC thực hiện.
- Nền domain đầy đủ hơn kèm nguồn: [../research/2026-10-18-llm-tuning-rule-giam-false-positive/notes/domain-kien-truc-soc.md](../research/2026-10-18-llm-tuning-rule-giam-false-positive/notes/domain-kien-truc-soc.md).
