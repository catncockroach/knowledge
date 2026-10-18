# Frameworks and governance

> Framework và tiêu chuẩn biến "làm an ninh" thành một chương trình có cấu trúc, đo được và kiểm toán được.

## Tại sao cần biết
Ở doanh nghiệp, quyết định bảo mật được đặt trong khung quản trị, tuân thủ và ngân sách. Biết các khung chuẩn giúp hiểu vì sao tổ chức có policy, audit, risk register, và dùng chung ngôn ngữ với lãnh đạo và kiểm toán viên.

## Khái niệm cốt lõi

### Các framework chính
| Framework | Bản chất | Dùng để |
|---|---|---|
| **NIST CSF 2.0** (2024) | Khung tự nguyện, 6 Function: Govern, Identify, Protect, Detect, Respond, Recover | Định hình chương trình, đo mức trưởng thành, giao tiếp với lãnh đạo |
| **ISO/IEC 27001** | Tiêu chuẩn cho hệ thống quản lý an ninh thông tin (ISMS), có thể được chứng nhận | Chứng nhận với khách hàng, đối tác |
| **CIS Critical Security Controls** | Danh sách biện pháp cụ thể, ưu tiên theo hiệu quả | Hướng dẫn thực thi kỹ thuật |
| **NIST SP 800-53** | Danh mục control chi tiết (gốc cho khu vực công Mỹ) | Chọn control cụ thể |
| **MITRE ATT&CK** | Mô hình hành vi kẻ tấn công | Đánh giá độ phủ phát hiện (xem file 02) |
| **PCI DSS, HIPAA, GDPR** | Quy định theo ngành/khu vực | Tuân thủ bắt buộc khi xử lý dữ liệu tương ứng |

Chú ý: framework (CSF, CIS) khuyến nghị; standard (ISO 27001) cho phép chứng nhận; regulation (GDPR, PCI DSS) bắt buộc trong phạm vi áp dụng.

### Quản trị và rủi ro
- **Governance**: ai quyết định và chịu trách nhiệm (CISO, hội đồng rủi ro).
- **Policy → Standard → Procedure/Guideline**: chính sách (what/why, cấp cao) → tiêu chuẩn (yêu cầu cụ thể) → quy trình (how).
- **Risk register**: danh sách rủi ro kèm chủ sở hữu, mức độ, cách xử lý.
- **Risk assessment**: định tính (cao/vừa/thấp) hoặc định lượng (tiền).
- **Compliance vs security**: tuân thủ là mức tối thiểu được kiểm tra, không bảo đảm an toàn thực tế.
- **Three lines of defense**: vận hành sở hữu rủi ro; bộ phận giám sát rủi ro/tuân thủ; kiểm toán nội bộ độc lập.

### Vai trò
**CISO** (lãnh đạo an ninh), security architect, GRC (Governance, Risk, Compliance), SOC, security engineer, auditor.

## Cách hoạt động
Chu trình quản trị điển hình (Plan–Do–Check–Act):
1. Xác định phạm vi, tài sản, yêu cầu pháp lý.
2. Đánh giá rủi ro, chọn control từ framework.
3. Triển khai và vận hành control.
4. Đo lường, kiểm toán, rà soát.
5. Cải tiến, lặp lại.

NIST CSF 2.0 làm rõ rằng Detect, Respond, Recover là phần xử lý sự cố, còn Govern, Identify, Protect là chuẩn bị. Đây là cầu nối sang SOC và incident response (file 11, 12).

## Ví dụ
Công ty bán SaaS cho khách ngân hàng: dùng ISO 27001 làm khung ISMS để khách tin cậy, dùng CIS Controls làm checklist kỹ thuật, dùng ATT&CK để xem rule SIEM đã phủ những technique nào, và chịu thêm yêu cầu của quy định tài chính địa phương.

## Hiểu nhầm thường gặp
- **"Đạt chứng nhận = an toàn"**: chứng nhận xác nhận quy trình tồn tại và được thực hiện, không loại trừ sự cố.
- **"Chọn một framework duy nhất"**: thực tế kết hợp, mỗi framework phục vụ một mục đích.

## Liên quan
- [01-security-fundamentals.md](01-security-fundamentals.md): khái niệm rủi ro và control.
- [12-incident-response.md](12-incident-response.md): Detect/Respond/Recover chi tiết.
