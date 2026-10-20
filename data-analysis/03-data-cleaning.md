# Làm sạch dữ liệu

> Làm sạch là đưa dữ liệu thô về trạng thái mà mỗi giá trị đúng nghĩa của nó: đúng kiểu, đúng đơn vị, không trùng, không giả; và xử lý giá trị thiếu và ngoại lai một cách có lý do.

## Tại sao cần biết

Dữ liệu thật luôn bẩn: form cho nhập tự do, hệ thống ghi log hai lần khi retry, đơn vị đổi giữa chừng, người dùng điền ngày sinh 1900-01-01 cho nhanh. Mọi thống kê tính trên dữ liệu bẩn đều sai một cách lặng lẽ, vì công thức không báo lỗi. Làm sạch thường chiếm phần lớn thời gian của một dự án phân tích, và quan trọng hơn: mỗi quyết định làm sạch (xoá dòng nào, điền gì vào chỗ trống) **là một giả định** ảnh hưởng tới kết luận.

## Khái niệm cốt lõi

### Các chiều chất lượng dữ liệu
- **Đầy đủ (completeness)**: có thiếu giá trị, thiếu dòng không.
- **Hợp lệ (validity)**: giá trị có nằm trong miền cho phép (tuổi 0–120, email đúng định dạng).
- **Chính xác (accuracy)**: giá trị có khớp thực tế (địa chỉ có đúng không).
- **Nhất quán (consistency)**: cùng một sự thật có cùng giá trị ở mọi nơi ("HCM", "TP.HCM", "Ho Chi Minh").
- **Duy nhất (uniqueness)**: không có bản ghi trùng.
- **Kịp thời (timeliness)**: dữ liệu có cập nhật đủ cho câu hỏi.

### Cơ chế thiếu dữ liệu (Rubin, 1976)
Cách xử lý giá trị thiếu phụ thuộc vào **vì sao** nó thiếu:
- **MCAR (Missing Completely At Random)**: việc thiếu không liên quan đến bất cứ biến nào. Ví dụ: một phần log mất do lỗi server ngẫu nhiên. Bỏ các dòng thiếu chỉ làm mất mẫu, không gây lệch.
- **MAR (Missing At Random)**: việc thiếu phụ thuộc vào biến **đã quan sát** được. Ví dụ: khách dùng app hay bỏ trống thu nhập hơn khách dùng web. Có thể hiệu chỉnh nhờ biến kênh.
- **MNAR (Missing Not At Random)**: việc thiếu phụ thuộc vào **chính giá trị bị thiếu**. Ví dụ: người thu nhập cao hay giấu thu nhập. Không hiệu chỉnh được chỉ từ dữ liệu, cần giả định hoặc thu thêm.

Không kiểm định được dữ liệu là MAR hay MNAR chỉ từ dữ liệu: đó là lập luận về quy trình sinh dữ liệu.

### Ngoại lai (outlier)
Giá trị khác xa phần còn lại. Có ba nguồn gốc, cần xử lý khác nhau:
1. **Lỗi**: nhập thừa số 0, đơn vị sai (gram ghi thành kg). → Sửa hoặc xoá.
2. **Giá trị thật nhưng thuộc quần thể khác**: tài khoản test nội bộ, đơn hàng của đại lý sỉ lẫn vào khách lẻ. → Tách ra, phân tích riêng.
3. **Giá trị thật, hiếm, cùng quần thể**: một khách mua rất lớn. → Giữ lại; dùng thống kê bền vững (median, IQR) hoặc biến đổi log thay vì xoá.

## Cách hoạt động

### Quy trình làm sạch

```
1. Profile      → đếm dòng, kiểu, % thiếu, số giá trị khác nhau, min/max mỗi cột
2. Kiểu & định dạng → ép kiểu, chuẩn hoá ngày giờ/múi giờ, đơn vị, mã hoá ký tự
3. Chuẩn hoá giá trị → gộp biến thể ("HCM" = "TP.HCM"), trim khoảng trắng, chữ hoa/thường
4. Trùng lặp    → xác định khoá, loại bản sao chính xác và gần đúng
5. Hợp lệ       → kiểm tra miền giá trị và ràng buộc chéo (ngày giao ≥ ngày đặt)
6. Thiếu        → xác định cơ chế, chọn chiến lược
7. Ngoại lai    → phát hiện, phân loại nguồn gốc, quyết định
8. Ghi lại      → mọi quy tắc đã áp dụng, số dòng bị ảnh hưởng ở mỗi bước
```

Bước 8 là bắt buộc: làm sạch phải tái lập được, tức là viết bằng code (SQL, script) chứ không sửa tay trong file.

### Chiến lược cho giá trị thiếu
| Chiến lược | Khi nào dùng | Rủi ro |
|---|---|---|
| Bỏ dòng (listwise deletion) | Ít thiếu, MCAR | Mất mẫu; lệch nếu không MCAR |
| Điền hằng (0, "unknown") | Thiếu có nghĩa ("không có giảm giá" = 0) | Sai nếu thiếu không có nghĩa là 0 |
| Điền mean/median | Nhanh, ít thiếu | Làm giảm phương sai giả tạo, làm yếu tương quan |
| Điền theo nhóm | MAR theo một biến nhóm | Vẫn giảm phương sai |
| Mô hình (hồi quy, KNN, multiple imputation) | MAR, thiếu nhiều | Phức tạp hơn; multiple imputation giữ được độ bất định |
| Thêm cờ `is_missing` | Thiếu bản thân mang thông tin | Thêm một biến |

Quy tắc thực hành: luôn báo cáo tỉ lệ thiếu, và kiểm tra xem kết luận có đổi không khi đổi chiến lược (sensitivity analysis).

### Phát hiện ngoại lai
- **Quy tắc IQR (Tukey)**: ngoại lai nếu < Q1 − 1,5·IQR hoặc > Q3 + 1,5·IQR, với IQR = Q3 − Q1. Bền vững vì dựa trên quartile.
- **z-score**: z = (x − x̄)/s, đánh dấu |z| > 3. Nhạy với chính ngoại lai (ngoại lai kéo mean và s lên, có thể tự che mình).
- **Quy tắc nghiệp vụ**: tốt nhất khi có, ví dụ "đơn hàng > 50 triệu là sỉ".

### Trùng lặp
- **Trùng chính xác**: mọi cột giống nhau, thường do ghi hai lần. Loại theo khoá.
- **Trùng gần đúng**: "Nguyễn Văn A, 0901..." và "Nguyen Van A, +84901...". Cần chuẩn hoá trước rồi so khớp mờ (fuzzy matching). Đây là bài toán **entity resolution**.
- Trước khi xoá, phải định nghĩa "cùng một bản ghi" theo grain: hai đơn cùng khách cùng số tiền cùng ngày có thể là hai đơn thật.

## Ví dụ

Cột giá trị đơn hàng (nghìn đồng) của 10 đơn: 120, 150, 150, 180, 200, 220, 250, 300, 350, 2000.

- Q1 = 157,5; Q3 = 287,5; IQR = 130; ngưỡng trên = 287,5 + 1,5 × 130 = 482,5. Đơn 2000 bị đánh dấu.
- z-score của 2000: mean = 392, s = 569,5 → z ≈ 2,82 < 3. **Quy tắc z không bắt được**, vì chính đơn 2000 đã kéo mean và s lên. Đây là lý do quy tắc IQR được ưa hơn với mẫu nhỏ.
- Kiểm tra nguồn gốc: đơn 2000 thuộc tài khoản đại lý → quần thể khác, tách ra. Sau khi tách: mean từ 392 xuống 213,3; median từ 210 xuống 200. Median gần như không đổi, mean đổi gần một nửa: mean nhạy với ngoại lai, median thì không.

## Hiểu nhầm thường gặp

- **"Ngoại lai là dữ liệu xấu, cứ xoá."** Nhiều khi ngoại lai là thông tin quan trọng nhất (gian lận, khách VIP, sự cố). Phải hỏi vì sao nó lệch trước khi quyết định.
- **"Điền mean là trung tính."** Điền mean làm phân bố nhọn hơn, phương sai nhỏ hơn, tương quan yếu đi, và khoảng tin cậy hẹp giả tạo.
- **"NULL và 0 là một."** NULL là "không biết", 0 là "biết, và bằng không". `AVG` trong SQL bỏ qua NULL nhưng tính 0, nên kết quả khác nhau.
- **"Làm sạch xong một lần là xong."** Dữ liệu chảy liên tục; quy tắc làm sạch phải chạy lại được và có kiểm tra tự động (data tests) để bắt lỗi mới.

## Liên quan
- [02-data-collection-and-sampling.md](02-data-collection-and-sampling.md): thiếu dữ liệu không ngẫu nhiên là một dạng lệch chọn mẫu.
- [04-data-wrangling.md](04-data-wrangling.md): bước tiếp theo, biến đổi và kết hợp bảng.
- [05-descriptive-statistics.md](05-descriptive-statistics.md): quartile, IQR và thống kê bền vững.
