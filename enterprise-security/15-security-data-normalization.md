# Security data normalization

> Chuẩn hóa dữ liệu bảo mật là đưa log từ nhiều nguồn về một schema chung, để cùng một khái niệm luôn có cùng tên, cùng kiểu, cùng nghĩa; OCSF là schema mở, trung lập vendor được xây cho mục đích này.

## Tại sao cần biết
Một tổ chức có hàng chục nguồn log, mỗi nguồn mô tả thế giới theo cách riêng. Detection, điều tra, quản lý tài sản đều cần *so sánh và nối* dữ liệu giữa các nguồn, mà không thể so những thứ không cùng ngôn ngữ. File [07-logging-and-telemetry.md](07-logging-and-telemetry.md) đặt chuẩn hóa vào đường đi của log; file này giải thích bản chất của nó.

## Khái niệm cốt lõi
- **Log khác nhau ở bốn tầng**:
  - *Tên*: tên máy là `Computer`, `DeviceName` hay `shost` tùy nguồn.
  - *Nghĩa*: `src` của firewall là máy khởi tạo kết nối; `Computer` của Windows là máy ghi log.
  - *Giá trị*: thất bại có thể là `FAILED`, `0xC000006A` hay `deny`; mỗi vendor một thang severity.
  - *Thời gian*: syslog thiếu năm và múi giờ, nguồn khác dùng UTC.
- **Parse và normalize**: *parse* tách log thô thành cặp field–giá trị theo tên của nguồn; *normalize* (map) đổi chúng sang tên, kiểu, giá trị của schema chung. Parse đúng mà map sai vẫn cho dữ liệu sai nghĩa.
- **Schema** quy định năm thứ: tên field, kiểu dữ liệu, ngữ nghĩa, tập giá trị liệt kê (enum), và cách phân loại event.
- **Vai trò ngữ nghĩa** là phần khó nhất của chuẩn hóa. Mỗi event có thể có nhiều máy và nhiều người, mỗi bên một vai:
  - *observer*: máy ghi nhận sự kiện;
  - *source* / *destination*: hai đầu của một kết nối hay một lần xác thực;
  - *actor*: chủ thể gây ra hành động;
  - *target*: đối tượng bị tác động.
- **Bài toán N × M**: N nguồn, M công dụng (rule, dashboard, điều tra, inventory). Không có schema chung, mỗi cặp phải tự hiểu nhau: N × M. Có schema chung: mỗi nguồn map một lần, mỗi công dụng viết một lần, N + M.
- **Hai kiểu schema**:
  - *Tập field dùng chung*: một kho field, event được phân loại bằng vài field nhãn; nguồn tự chọn field cần điền.
  - *Hướng class*: mỗi loại event là một class với tập attribute định nghĩa sẵn, có mức bắt buộc và enum riêng. Chặt hơn, dễ kiểm tra hơn, map tốn công hơn.
- **Bức tranh schema**: phần lớn là schema của một nền tảng (CIM của Splunk, ASIM của Sentinel, UDM của Google SecOps, ECS của Elastic). **OCSF** (Open Cybersecurity Schema Framework) là schema mở, hướng class, không thuộc nền tảng nào:
  - ra mắt năm 2022 do AWS và Splunk khởi xướng, dựa trên schema Symantec phát triển trước đó;
  - bản 1.0 năm 2023;
  - thuộc Linux Foundation từ tháng 11/2024, giấy phép Apache 2.0.
- **Cái giá của chuẩn hóa**: công sức map và bảo trì khi nguồn đổi định dạng; mất chi tiết đặc thù của nguồn; schema tiến hóa theo phiên bản.

## Cách hoạt động
```
Nguồn A ─┐                                           ┌─► rule
Nguồn B ─┼─► parse ─► normalize ─► schema chung ─────┼─► điều tra
Nguồn C ─┘   (tên      (tên, kiểu, nghĩa,            ├─► quản lý tài sản
              nguồn)    giá trị, vai trò)            └─► báo cáo
```
Sau chuẩn hóa, người dùng dữ liệu không cần biết log đến từ nguồn nào. Chỉ người viết mapping cần hiểu sâu từng nguồn.

## Ví dụ
Windows ghi event `4625` (đăng nhập thất bại) trên domain controller `DC01`, người dùng gõ sai mật khẩu từ laptop `WS-0412`. Log gốc có `Computer=DC01` và `WorkstationName=WS-0412`, hai field tên na ná nhau nhưng là hai vai khác hẳn: DC01 là *observer* và *destination*, WS-0412 là *source*. Nếu chuẩn hóa nhầm WS-0412 thành máy ghi log, mọi phân tích phía sau sẽ gán sự việc cho sai máy.

## Hiểu nhầm thường gặp
- **"Chuẩn hóa chỉ là đổi tên field"**: phần khó là giữ đúng *nghĩa* và *vai trò*, không phải tên.
- **"Đúng schema là dữ liệu tốt"**: dữ liệu có thể đúng schema mà sai nghĩa.
- **"Schema mở thay được SIEM"**: schema là mô hình dữ liệu; SIEM, data lake là nơi lưu và xử lý dữ liệu theo mô hình đó.

## Liên quan
- [07-logging-and-telemetry.md](07-logging-and-telemetry.md): chuẩn hóa trong đường đi của log.
- [14-vendor-terminology-map.md](14-vendor-terminology-map.md): schema của từng vendor.
- [16-ocsf-data-model.md](16-ocsf-data-model.md): cấu trúc của OCSF.
