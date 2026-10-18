# Threats and attack lifecycle

> Một cuộc tấn công thường đi qua nhiều giai đoạn; mô tả hành vi theo các mô hình chung (Kill Chain, MITRE ATT&CK) cho phép phát hiện và trao đổi bằng cùng một ngôn ngữ.

## Tại sao cần biết
Phát hiện hiệu quả cần biết kẻ tấn công làm gì ở từng bước. ATT&CK và các khái niệm IoC/IoA/TTP là từ vựng nền của detection, threat intelligence và incident response.

## Khái niệm cốt lõi

### Tác nhân đe dọa
| Loại | Động cơ | Ví dụ |
|---|---|---|
| Tội phạm có tổ chức | Tiền | Ransomware, BEC, đánh cắp thẻ |
| Nhà nước (APT) | Gián điệp, phá hoại | Đánh cắp tài sản trí tuệ |
| Hacktivist | Chính trị, tuyên truyền | DDoS, deface |
| Insider | Bất mãn, lợi ích, sơ suất | Nhân viên tải dữ liệu mang đi |
| Opportunistic | Quét hàng loạt lỗ hổng | Botnet quét cổng mở |

### Cyber Kill Chain (Lockheed Martin, 7 bước)
Reconnaissance → Weaponization → Delivery → Exploitation → Installation → Command & Control → Actions on Objectives. Giá trị: cắt chuỗi ở bất kỳ bước nào cũng làm hỏng cuộc tấn công.

### MITRE ATT&CK
Cơ sở tri thức về hành vi kẻ tấn công dựa trên quan sát thực tế.
- **Tactic** = *why* (mục tiêu ở bước đó). Enterprise matrix có 14 tactic: Reconnaissance, Resource Development, Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection, Command and Control, Exfiltration, Impact.
- **Technique** = *how* (cách đạt mục tiêu), có ID dạng `T1059`; **sub-technique** chi tiết hơn (`T1059.001` PowerShell).
- **Procedure** = cách triển khai cụ thể của một nhóm hay công cụ.
- **TTP** = Tactics, Techniques, Procedures: "chữ ký hành vi" của kẻ tấn công.

### Indicator
- **IoC** (Indicator of Compromise): dấu vết tĩnh cho thấy đã bị xâm nhập (hash file, IP, domain, URL). Mang tính *phản ứng*.
- **IoA** (Indicator of Attack): chuỗi hành vi cho thấy tấn công đang diễn ra, ví dụ Word sinh PowerShell rồi đọc bộ nhớ chứa credential.
- **Pyramid of Pain** (David Bianco): xếp indicator theo mức kẻ tấn công "đau" khi bị chặn. Từ dễ đổi đến khó đổi: hash → IP → domain → network/host artifact → tool → TTP. Phát hiện theo TTP khó bị né nhất.

### Các kiểu tấn công phổ biến
Phishing / BEC (lừa người dùng), khai thác lỗ hổng, đánh cắp và lạm dụng credential, ransomware, tấn công chuỗi cung ứng, DDoS, lạm dụng cấu hình sai trên cloud, insider threat.

## Cách hoạt động
Ví dụ một chuỗi điển hình, ghi theo tactic:

```
Initial Access (phishing) → Execution (macro → PowerShell)
  → Persistence (scheduled task) → Credential Access (dump LSASS)
  → Lateral Movement (RDP/SMB) → Exfiltration / Impact (mã hóa dữ liệu)
```
Mỗi mũi tên là một cơ hội phát hiện; càng sớm, thiệt hại càng nhỏ.

## Ví dụ
Rule phát hiện "tiến trình Office sinh `powershell.exe` với tham số mã hóa base64" bám vào *Execution* (T1059.001): đây là IoA, bền hơn nhiều so với chặn hash của một file macro cụ thể (IoC).

## Hiểu nhầm thường gặp
- **"IoC nhiều là bảo vệ tốt"**: IoC hết hạn nhanh vì attacker đổi IP/domain dễ; chúng có giá trị với sự cố đã biết, ít với kẻ tấn công mới.
- **"ATT&CK là danh sách phải phủ 100%"**: nó là bản đồ để đánh giá độ phủ phát hiện, không phải checklist hoàn thành.
- **"Kill Chain là tuyến tính"**: kẻ tấn công lặp bước, quay lại, đi song song.

## Liên quan
- [09-detection-engineering.md](09-detection-engineering.md): chuyển TTP thành rule.
- [10-threat-intelligence.md](10-threat-intelligence.md): cách thu thập và dùng IoC/TTP.
- [01-security-fundamentals.md](01-security-fundamentals.md): threat, vulnerability, risk.
