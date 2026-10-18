# Incident response

> Incident response (IR) là quy trình có tổ chức để phát hiện, kiềm chế, loại bỏ sự cố an ninh, phục hồi và rút kinh nghiệm.

## Tại sao cần biết
Không phải mọi cảnh báo là sự cố; không phải mọi sự cố đều ngăn được. Chất lượng ứng phó quyết định thiệt hại, và là nơi alert trở thành hành động.

## Khái niệm cốt lõi

### Phân biệt thuật ngữ
- **Event**: bất kỳ điều gì quan sát được (NIST: "any observable occurrence").
- **Alert**: kết quả khớp của rule, cần được xem xét.
- **Incident**: theo định nghĩa của NIST CSF 1.1, là một cybersecurity event đã được xác định là có tác động đến tổ chức và cần ứng phó, phục hồi.
- **Triage**: phân loại nhanh alert: thật hay giả, mức ưu tiên, cần escalate không.

### Vòng đời IR
- **Mô hình cổ điển (NIST SP 800-61 Rev.2, 2012)**: Preparation → Detection & Analysis → Containment, Eradication & Recovery → Post-Incident Activity.
- **NIST SP 800-61 Rev.3 (2025)** thay Rev.2 và gắn IR vào 6 Function của CSF 2.0: Govern, Identify, Protect là chuẩn bị; **Detect, Respond, Recover** là xử lý sự cố; hoạt động sau sự cố đóng góp vào cải tiến. Tổ chức không bắt buộc dùng mô hình này.

### Các bước thực tế
1. **Chuẩn bị**: kế hoạch IR, vai trò, công cụ, liên lạc, diễn tập.
2. **Phát hiện & phân tích**: xác nhận, xác định phạm vi và mức độ, lưu bằng chứng.
3. **Kiềm chế (containment)**: ngăn lan rộng (cô lập máy, khóa tài khoản, chặn IOC), ngắn hạn rồi dài hạn.
4. **Loại bỏ (eradication)**: xóa mã độc, đóng đường vào, vá lỗ hổng.
5. **Phục hồi (recovery)**: khôi phục hệ thống từ nguồn tin cậy, giám sát chặt.
6. **Rút kinh nghiệm**: họp post-incident, cập nhật rule, quy trình, đào tạo.

### Chính sách và tài liệu
- **Playbook**: hướng dẫn xử lý theo loại sự cố (phishing, ransomware): vai trò, điểm quyết định, escalation.
- **Runbook**: các bước cụ thể cho một tác vụ kỹ thuật (cô lập máy trong EDR). Cách dùng hai từ này không thống nhất giữa các nguồn.
- **Case management**: ghi lại timeline, bằng chứng, hành động, quyết định (ví dụ TheHive, hoặc module có trong SIEM/SOAR).
- **Digital forensics**: thu thập và bảo toàn bằng chứng (memory, disk, log) theo nguyên tắc chain of custody.
- **Thông báo**: pháp lý/khách hàng/cơ quan quản lý theo yêu cầu tuân thủ.

## Cách hoạt động
```
Alert ─► triage ─► incident? ─yes─► contain ─► eradicate ─► recover
                      │no                                       │
                  đóng + verdict                         post-incident review
                                                         └► cải tiến rule, control
```

## Ví dụ
EDR báo ransomware trên một laptop: L1 xác nhận → cô lập laptop khỏi mạng (containment) → L2 tìm thấy tài khoản bị đánh cắp và lan sang file server → khóa tài khoản, cô lập server → phục hồi từ backup bất biến → post-incident: thêm rule phát hiện mã hóa hàng loạt, bật MFA cho tài khoản đó.

## Hiểu nhầm thường gặp
- **"Xóa mã độc là xong"**: nếu không tìm ra đường vào và tài khoản bị lộ, kẻ tấn công quay lại.
- **"Tắt máy ngay để an toàn"**: tắt có thể xóa bằng chứng trong RAM; kiềm chế bằng cô lập mạng thường tốt hơn.
- **"Bỏ qua bước rút kinh nghiệm"**: đây là nơi sự cố biến thành cải tiến.

## Liên quan
- [11-soc-organization.md](11-soc-organization.md): ai thực hiện các bước.
- [13-soar-xdr-and-automation.md](13-soar-xdr-and-automation.md): tự động hóa các bước lặp lại.
- [03-frameworks-and-governance.md](03-frameworks-and-governance.md): CSF 2.0 và vị trí của IR.
