# Threat intelligence

> Threat intelligence (CTI) là thông tin về kẻ tấn công, công cụ và hành vi của chúng, đã được phân tích để hỗ trợ quyết định phòng thủ.

## Tại sao cần biết
CTI cho phép phòng thủ chủ động và đặt cảnh báo vào ngữ cảnh. Nhưng nếu dùng thiếu chọn lọc, IoC cũ và kém chất lượng là một nguồn false positive đáng kể.

## Khái niệm cốt lõi

- **Dữ liệu ≠ thông tin ≠ intelligence**: feed IP thô là dữ liệu; được phân tích, đặt trong bối cảnh và gắn hành động mới là intelligence.
- **Ba cấp**:
  | Cấp | Câu hỏi | Người dùng | Ví dụ |
  |---|---|---|---|
  | Strategic | Ai nhắm vào ngành chúng ta, vì sao? | Lãnh đạo | Báo cáo xu hướng, nhóm APT trong ngành |
  | Operational | Chiến dịch nào đang diễn ra? | Quản lý SOC, IR | Mô tả chiến dịch, TTP |
  | Tactical / technical | Dấu vết cụ thể là gì? | SOC, hệ thống tự động | IoC: IP, domain, hash, URL |
- **IoC vs TTP**: theo Pyramid of Pain (file 02), IoC rẻ để attacker đổi, TTP đắt. CTI tốt ưu tiên TTP.
- **Nguồn**: open source (OSINT), feed thương mại, chia sẻ theo ngành (ISAC), vendor (báo cáo threat research), nội bộ (từ sự cố của chính mình).
- **TIP** (Threat Intelligence Platform): thu thập, khử trùng lặp, chấm điểm, quản lý vòng đời IoC và đẩy xuống các hệ thống (SIEM, EDR, firewall).
- **Chuẩn trao đổi**: STIX (mô hình dữ liệu), TAXII (giao thức vận chuyển).
- **Chất lượng indicator**: độ tin cậy nguồn, tuổi, ngữ cảnh, thời hạn (TTL). IoC hết hạn và IoC nhầm (CDN, IP dùng chung, domain hợp pháp bị lạm dụng) gây FP.
- **Threat hunting**: tìm chủ động dấu hiệu tấn công chưa bị rule phát hiện, xuất phát từ giả thuyết (thường lấy từ CTI hoặc ATT&CK).

## Cách hoạt động
```
Nguồn CTI ─► TIP (chuẩn hóa, chấm điểm, hết hạn)
              ├─► SIEM: indicator-match rule, enrich alert
              ├─► EDR/Firewall: chặn
              └─► Analyst: ngữ cảnh khi điều tra
Sự cố nội bộ ─► CTI mới ─► quay lại TIP
```
Vòng phản hồi: khi điều tra phát hiện một IoC là sai (ví dụ IP của CDN hợp pháp), cần gỡ hoặc hạ điểm trong TIP để không gây FP lặp lại.

## Ví dụ
Sentinel cho analyst đánh dấu một IP/domain/hash trong incident là IoC ("Add to TI"), và hiển thị insight như "IP address remote connections with TI match". Elastic có loại rule *Indicator match* so khớp field của event với index threat intel và làm giàu alert bằng metadata của indicator.

## Hiểu nhầm thường gặp
- **"Nhiều feed hơn thì tốt hơn"**: nhiều feed kém chất lượng chỉ tăng nhiễu.
- **"IoC khớp nghĩa là bị xâm nhập"**: có thể chỉ là truy cập thoáng qua, hoặc indicator sai; cần ngữ cảnh.
- **CTI chỉ là danh sách IoC**: phần giá trị cao nhất là hiểu hành vi (TTP) và bối cảnh.

## Liên quan
- [02-threats-and-attack-lifecycle.md](02-threats-and-attack-lifecycle.md): IoC, IoA, TTP, Pyramid of Pain.
- [08-siem.md](08-siem.md): nơi IoC được so khớp.
- [09-detection-engineering.md](09-detection-engineering.md): chuyển CTI thành rule.
