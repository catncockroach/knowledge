# Security fundamentals

> An ninh thông tin là quản lý rủi ro: bảo vệ tính bí mật, toàn vẹn và sẵn sàng của tài sản bằng nhiều lớp biện pháp, chứ không phải ngăn chặn tuyệt đối.

## Tại sao cần biết
Mọi công cụ về sau (SIEM, EDR, SOC...) chỉ là biện pháp để giảm một loại rủi ro cụ thể. Nắm được từ vựng gốc giúp biết mỗi công cụ bảo vệ cái gì và không bảo vệ cái gì.

## Khái niệm cốt lõi

### Bộ ba CIA
| Thuộc tính | Nghĩa | Bị phá khi | Biện pháp điển hình |
|---|---|---|---|
| **Confidentiality** (bí mật) | Chỉ người được phép mới đọc được | Rò rỉ dữ liệu | Mã hóa, phân quyền |
| **Integrity** (toàn vẹn) | Dữ liệu không bị sửa trái phép | Ransomware sửa file, sửa DB | Hash, chữ ký, kiểm soát thay đổi |
| **Availability** (sẵn sàng) | Dịch vụ dùng được khi cần | DDoS, ransomware khóa hệ thống | Dự phòng, backup, chống DDoS |

### Từ vựng rủi ro
- **Asset**: thứ có giá trị cần bảo vệ (dữ liệu, hệ thống, danh tính, uy tín).
- **Threat**: tác nhân hoặc sự kiện có thể gây hại (nhóm tội phạm, insider, lỗi cấu hình).
- **Vulnerability**: điểm yếu mà threat có thể khai thác.
- **Risk** ≈ khả năng xảy ra × tác động. Rủi ro không bằng 0; mục tiêu là đưa về mức chấp nhận được.
- **Control**: biện pháp giảm rủi ro. Phân loại theo chức năng: *preventive* (ngăn), *detective* (phát hiện), *corrective* (khắc phục), *deterrent* (răn đe); và theo bản chất: kỹ thuật, quản trị (chính sách, quy trình), vật lý.
- **Xử lý rủi ro**: giảm (mitigate), tránh (avoid), chuyển giao (transfer, ví dụ bảo hiểm), chấp nhận (accept).

### Nguyên tắc thiết kế
- **Defense in depth**: nhiều lớp biện pháp độc lập để một lớp hỏng không làm sập tất cả.
- **Least privilege**: chỉ cấp quyền tối thiểu cần để làm việc.
- **Separation of duties**: không để một người nắm trọn một quy trình nhạy cảm.
- **Zero Trust** (NIST SP 800-207): không tin mặc định vì vị trí mạng; mỗi yêu cầu truy cập được xác thực và cấp quyền theo ngữ cảnh. Đây là hướng thiết kế, không phải sản phẩm.
- **Assume breach**: thiết kế như thể kẻ tấn công đã vào được, nên cần phát hiện và ứng phó, không chỉ phòng ngừa.

### Prevent – Detect – Respond
Không biện pháp phòng ngừa nào hoàn hảo, nên một chương trình an ninh cân bằng ba việc: ngăn, phát hiện nhanh, ứng phó và phục hồi. Phần lớn nội dung "security operations" (SIEM, SOC, IR) thuộc hai vế sau.

## Cách hoạt động
```
Threat ──khai thác──► Vulnerability ──ảnh hưởng──► Asset ──► Impact
                          ▲                          ▲
                      Control giảm khả năng       Control giảm tác động
```
Quản lý rủi ro là vòng lặp: xác định tài sản → đánh giá rủi ro → chọn control → vận hành → đo lại.

## Ví dụ
Server chứa dữ liệu khách hàng (asset) có lỗ hổng chưa vá (vulnerability); nhóm ransomware (threat) khai thác. Control: vá lỗi (preventive), EDR cảnh báo mã hóa hàng loạt (detective), backup offline (corrective). Nếu chi phí vá toàn hệ thống quá lớn, tổ chức có thể chấp nhận rủi ro với hệ thống ít quan trọng và có ghi nhận.

## Hiểu nhầm thường gặp
- **"Mua đủ công cụ là an toàn"**: công cụ cần con người, quy trình và dữ liệu tốt đi kèm.
- **"Security chỉ là việc của team security"**: phần lớn control (vá, phân quyền, cấu hình) do team vận hành và dev thực hiện.
- **"An toàn tuyệt đối là mục tiêu"**: mục tiêu là rủi ro chấp nhận được với chi phí hợp lý.

## Liên quan
- [02-threats-and-attack-lifecycle.md](02-threats-and-attack-lifecycle.md): threat cụ thể trông như thế nào.
- [03-frameworks-and-governance.md](03-frameworks-and-governance.md): cách tổ chức hóa quản lý rủi ro.
- [../internet/10-network-security.md](../internet/10-network-security.md): nền tảng mật mã, TLS, firewall ở mức mạng.
