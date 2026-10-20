# Nền tảng về dữ liệu

> Dữ liệu là các phép đo được ghi lại về đối tượng; trước khi phân tích phải biết mỗi cột đo cái gì, ở thang đo nào và bảng được tổ chức ra sao, vì điều đó quyết định phép tính nào có nghĩa.

## Tại sao cần biết

Phần lớn lỗi phân tích không nằm ở công thức mà ở chỗ hiểu sai dữ liệu: lấy trung bình của mã tỉnh, cộng tỉ lệ phần trăm của các nhóm khác cỡ, đếm một khách hàng hai lần vì bảng có một dòng cho mỗi đơn hàng. Mọi kỹ thuật ở các file sau (làm sạch, thống kê, kiểm định, hồi quy) đều giả định bạn đã trả lời được ba câu: **một dòng là gì**, **một cột đo gì**, và **cột đó thuộc thang đo nào**.

## Khái niệm cốt lõi

### Đơn vị quan sát, biến, giá trị
- **Đơn vị quan sát (observational unit)**: thực thể mà ta đo: một khách hàng, một đơn hàng, một lượt truy cập, một ngày.
- **Biến (variable)**: một thuộc tính được đo trên mỗi đơn vị: tuổi, giá trị đơn, kênh truy cập.
- **Giá trị (value)**: kết quả đo của một biến trên một đơn vị.
- **Độ hạt (granularity / grain)**: mức chi tiết của một dòng. "Một dòng = một đơn hàng" khác "một dòng = một sản phẩm trong đơn hàng". Đổi grain là đổi câu hỏi có thể trả lời.

### Kiểu biến
- **Định tính (categorical)**: giá trị là nhãn.
  - **Danh nghĩa (nominal)**: không có thứ tự (kênh: web, app, cửa hàng).
  - **Thứ bậc (ordinal)**: có thứ tự nhưng khoảng cách không đều (mức hài lòng 1–5, hạng thành viên).
- **Định lượng (numerical)**: giá trị là số đo được.
  - **Rời rạc (discrete)**: đếm được (số sản phẩm trong giỏ).
  - **Liên tục (continuous)**: lấy giá trị bất kỳ trong khoảng (thời gian tải trang).

### Bốn thang đo của Stevens
Stevens (1946) phân thang đo theo những phép toán còn có nghĩa:

| Thang đo | Ví dụ | Phép toán có nghĩa | Thống kê trung tâm phù hợp |
|---|---|---|---|
| Nominal | Kênh, tỉnh, màu | =, ≠, đếm | Mode |
| Ordinal | Điểm hài lòng 1–5 | thêm <, > | Median, percentile |
| Interval | Nhiệt độ °C, năm | thêm +, − (khoảng cách đều, không có 0 tuyệt đối) | Mean |
| Ratio | Doanh thu, thời gian, cân nặng | thêm ×, ÷ (có 0 tuyệt đối) | Mean, hệ số biến thiên, tỉ lệ "gấp đôi" |

Hệ quả: "20 °C nóng gấp đôi 10 °C" là sai vì °C là interval (0 °C không phải "không có nhiệt"). "Doanh thu tháng này gấp đôi tháng trước" thì đúng vì doanh thu là ratio. Mã số (mã bưu chính, mã khách hàng) trông như số nhưng là nominal.

### Dữ liệu có cấu trúc và phi cấu trúc
- **Có cấu trúc (structured)**: bảng có schema cố định (database, CSV).
- **Bán cấu trúc (semi-structured)**: có khoá/tên trường nhưng linh hoạt (JSON, log có trường).
- **Phi cấu trúc (unstructured)**: văn bản tự do, ảnh, âm thanh. Muốn phân tích thống kê thì phải trích ra biến trước.

### Tidy data
Wickham (2014) định nghĩa một bảng **tidy** khi:
1. Mỗi biến là một cột.
2. Mỗi quan sát là một dòng.
3. Mỗi loại đơn vị quan sát là một bảng.

Hầu hết công cụ (SQL `GROUP BY`, pandas, thư viện vẽ đồ thị) giả định dữ liệu tidy. Bảng báo cáo kiểu Excel (mỗi tháng một cột) là dạng "wide", tiện đọc nhưng không tidy. Cách chuyển qua lại nằm ở [04-data-wrangling.md](04-data-wrangling.md).

### Metadata và data dictionary
**Data dictionary** ghi cho mỗi cột: tên, ý nghĩa, đơn vị, kiểu, miền giá trị, nguồn, cách tính. Không có nó thì không biết `revenue` đã trừ hoàn tiền chưa, hay `created_at` theo múi giờ nào.

## Cách hoạt động

### Quy trình phân tích dữ liệu
Các khung quy trình (CRISP-DM, hay chuỗi ask → prepare → process → analyze → share) cùng một mạch:

```
Câu hỏi nghiệp vụ ──► Dữ liệu cần gì ──► Thu thập ──► Làm sạch & biến đổi
        ▲                                                   │
        │                                                   ▼
 Quyết định / hành động ◄── Truyền đạt ◄── Mô hình/kiểm định ◄── Khám phá (EDA)
```

Mũi tên quay lại là cố ý: khám phá thường làm lộ ra câu hỏi tốt hơn câu hỏi ban đầu. Phân tích là vòng lặp, không phải dây chuyền.

### Ba loại câu hỏi
- **Mô tả (descriptive)**: chuyện gì đã xảy ra? Doanh thu quý 3 bao nhiêu?
- **Suy luận / chẩn đoán (inferential / diagnostic)**: khác biệt có thật hay do ngẫu nhiên, vì sao xảy ra? Tỉ lệ chuyển đổi tăng có ý nghĩa không?
- **Dự đoán và nhân quả (predictive / causal)**: sẽ xảy ra gì, và nếu ta làm X thì Y đổi thế nào?

Loại câu hỏi quyết định công cụ: mô tả cần tổng hợp và đồ thị; suy luận cần xác suất và kiểm định; nhân quả cần thiết kế thí nghiệm hoặc giả định mạnh (xem [12-experiments-and-causality.md](12-experiments-and-causality.md)).

## Ví dụ

Bảng đơn hàng của một shop:

| order_id | customer_id | channel | rating | amount_k | created_at |
|---|---|---|---|---|---|
| 1001 | C07 | app | 4 | 250 | 2026-03-02 09:15 |
| 1002 | C07 | web | 5 | 180 | 2026-03-05 20:41 |
| 1003 | C12 | store | 3 | 1200 | 2026-03-05 11:02 |

- Grain: một dòng = một đơn hàng. Câu hỏi "bao nhiêu khách?" phải đếm `DISTINCT customer_id` (2), không phải số dòng (3).
- `order_id`, `customer_id`: nominal dù là chuỗi số. Trung bình của chúng vô nghĩa.
- `channel`: nominal, tóm tắt bằng đếm/tỉ lệ.
- `rating`: ordinal. Báo median và phân bố (bao nhiêu % chấm 4–5) an toàn hơn mean 4,0.
- `amount_k`: ratio, nghìn đồng. Mean, tổng, tỉ số đều có nghĩa.
- `created_at`: thời điểm, cần biết múi giờ. Từ đó trích được biến mới: giờ trong ngày, thứ trong tuần.

## Hiểu nhầm thường gặp

- **"Cột là số thì tính trung bình được."** Mã số là nominal; điểm 1–5 là ordinal, khoảng cách giữa 1→2 và 4→5 không chắc bằng nhau. Mean của ordinal hay được dùng trong thực tế nhưng phải hiểu đó là xấp xỉ.
- **"Số dòng = số đối tượng."** Chỉ đúng khi grain trùng với đối tượng bạn đếm. Join sai grain làm nhân bản dòng (xem [04-data-wrangling.md](04-data-wrangling.md)).
- **"Nhiều dữ liệu hơn thì kết luận đúng hơn."** Dữ liệu lớn nhưng lệch (chỉ khách dùng app) vẫn cho kết luận sai về toàn bộ khách. Chất lượng lấy mẫu quan trọng hơn cỡ (xem [02-data-collection-and-sampling.md](02-data-collection-and-sampling.md)).

## Liên quan
- [02-data-collection-and-sampling.md](02-data-collection-and-sampling.md): dữ liệu đến từ đâu và lệch như thế nào.
- [04-data-wrangling.md](04-data-wrangling.md): chuyển bảng về dạng tidy, đổi grain bằng join và group by.
- [05-descriptive-statistics.md](05-descriptive-statistics.md): chọn thống kê tóm tắt theo thang đo.
