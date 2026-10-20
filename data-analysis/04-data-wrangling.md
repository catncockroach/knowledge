# Biến đổi và kết hợp dữ liệu (data wrangling)

> Wrangling là đưa dữ liệu sạch về đúng hình dạng cho câu hỏi: lọc, tạo biến mới, kết hợp nhiều bảng, gộp nhóm, xoay bảng; và biến đổi thang của biến khi phân tích cần.

## Tại sao cần biết

Dữ liệu hiếm khi nằm sẵn trong một bảng đúng grain. Câu "doanh thu trung bình mỗi khách theo kênh đăng ký" cần ghép bảng đơn hàng với bảng khách hàng, gộp đơn theo khách, rồi gộp khách theo kênh. Mỗi bước đổi grain là một chỗ có thể đếm trùng hoặc đếm sót. Nắm các phép biến đổi cơ bản giúp bạn diễn đạt mọi câu hỏi bằng vài thao tác ghép lại, dù dùng SQL, pandas hay công cụ nào.

## Khái niệm cốt lõi

### Năm phép cơ bản trên một bảng
Hầu hết thư viện (SQL, pandas, dplyr) có cùng bộ phép:

| Phép | Ý nghĩa | SQL | pandas |
|---|---|---|---|
| Chọn cột | giữ biến cần | `SELECT a, b` | `df[["a","b"]]` |
| Lọc dòng | giữ quan sát thoả điều kiện | `WHERE` | `df[df.x > 0]` / `query` |
| Tạo biến | tính cột mới từ cột cũ | `SELECT x*2 AS y` | `assign(y=...)` |
| Sắp xếp | đổi thứ tự | `ORDER BY` | `sort_values` |
| Gộp nhóm | tóm tắt mỗi nhóm thành một dòng | `GROUP BY` + `SUM/AVG/COUNT` | `groupby().agg()` |

### Join: kết hợp hai bảng theo khoá
- **Inner join**: chỉ giữ dòng có khoá ở cả hai bảng.
- **Left join**: giữ mọi dòng bảng trái; bảng phải không khớp thì điền NULL.
- **Full outer join**: giữ mọi dòng của cả hai.
- **Anti join**: dòng bảng trái **không** có ở bảng phải (khách chưa từng mua). SQL: `LEFT JOIN ... WHERE right.key IS NULL` hoặc `NOT EXISTS`.

**Quan hệ khoá (cardinality)** quyết định số dòng sau join:
- 1–1: số dòng giữ nguyên.
- 1–n: bảng bên "1" bị nhân lên theo số dòng khớp bên "n".
- n–n: nhân chéo trong mỗi khoá, gần như luôn là lỗi.

### Gộp nhóm và grain
`GROUP BY customer_id` đổi grain từ "đơn hàng" sang "khách hàng". Mọi cột trong kết quả phải là khoá nhóm hoặc một hàm gộp. Hàm gộp phổ biến: `COUNT`, `COUNT(DISTINCT)`, `SUM`, `AVG`, `MIN`, `MAX`, percentile.

### Window function: tính toán theo nhóm mà không gộp dòng
Window giữ nguyên số dòng nhưng nhìn sang các dòng cùng nhóm:
- Xếp hạng: `ROW_NUMBER()`, `RANK()`.
- Dòng trước/sau: `LAG()`, `LEAD()` (khoảng cách giữa hai lần mua).
- Luỹ kế, trượt: `SUM(...) OVER (ORDER BY ... ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` cho trung bình trượt 7 ngày.

### Xoay bảng: wide ↔ long
- **Long (tidy)**: mỗi dòng một (đơn vị, biến, giá trị). `pivot_longer` / `melt`.
- **Wide**: mỗi giá trị của một biến thành một cột. `pivot_wider` / `pivot` / `pivot_table`.

Phân tích và vẽ đồ thị cần long; báo cáo cho người đọc hay cần wide.

### Biến đổi biến (feature transformation)
- **Chuẩn hoá (standardization)**: z = (x − mean)/sd, đưa biến về mean 0, sd 1. Dùng khi so sánh biến khác đơn vị, hoặc cho thuật toán nhạy với thang đo.
- **Min-max scaling**: (x − min)/(max − min) về [0, 1]. Nhạy với ngoại lai.
- **Biến đổi log**: log(x) hoặc log(1 + x) cho biến lệch phải (doanh thu, thu nhập, lượt xem). Biến tích thành tổng, làm phân bố cân hơn, và hiệu số trên thang log đọc như tỉ lệ phần trăm.
- **Chia khoảng (binning)**: biến liên tục thành nhóm (tuổi → 18–24, 25–34…). Dễ đọc nhưng mất thông tin; ranh giới chọn tuỳ tiện có thể đổi kết luận.
- **Mã hoá biến định tính**: **one-hot** (mỗi giá trị một cột 0/1) cho nominal; mã số thứ tự cho ordinal. Gán số 1, 2, 3 cho nominal sẽ tạo ra thứ tự giả.
- **Trích từ thời gian**: giờ, thứ, tuần, tháng, ngày lễ, "số ngày kể từ lần mua trước".

## Cách hoạt động

### Diễn đạt câu hỏi thành chuỗi phép
"Doanh thu trung bình mỗi khách theo kênh đăng ký, chỉ tính khách đăng ký năm 2026":

```
customers ──filter(signup_year = 2026)──┐
                                        ├─ left join on customer_id ─► group by customer_id ─► group by channel
orders ────group by customer_id: SUM ───┘   (khách không mua → 0)       (doanh thu/khách)     AVG(doanh thu/khách)
```

```sql
WITH rev AS (
  SELECT customer_id, SUM(amount) AS revenue
  FROM orders
  GROUP BY customer_id
)
SELECT c.signup_channel,
       COUNT(*)                         AS customers,
       AVG(COALESCE(r.revenue, 0))      AS avg_revenue_per_customer
FROM customers c
LEFT JOIN rev r ON r.customer_id = c.customer_id
WHERE c.signup_year = 2026
GROUP BY c.signup_channel;
```

Hai quyết định ẩn trong đoạn này đều thay đổi kết quả:
- **Gộp orders về grain khách trước khi join**, tránh nhân dòng.
- **Left join + COALESCE 0**: khách không mua được tính là doanh thu 0. Dùng inner join thì chỉ còn khách đã mua, và con số trả lời một câu hỏi khác ("doanh thu trung bình mỗi *khách đã mua*").

## Ví dụ

Lỗi fan-out khi join 1–n. Bảng `customers` có 2 khách, mỗi khách một dòng ngân sách marketing:

| customer_id | acquisition_cost |
|---|---|
| C1 | 100 |
| C2 | 100 |

Bảng `orders`: C1 có 3 đơn, C2 có 1 đơn. Join rồi `SUM(acquisition_cost)` cho 100 × 3 + 100 × 1 = **400**, trong khi chi phí thật là **200**. Cột của bảng bên "1" bị lặp theo số đơn. Cách sửa: gộp từng bảng về cùng grain trước khi join, hoặc chỉ cộng các cột thuộc bảng bên "n".

Kiểm tra nhanh sau mỗi join: so số dòng trước và sau, và so tổng một cột quen thuộc (tổng doanh thu) với con số đã biết.

## Hiểu nhầm thường gặp

- **"Left join không làm tăng số dòng."** Left join giữ mọi dòng trái, nhưng nếu khoá bên phải không duy nhất thì dòng trái vẫn bị nhân.
- **"COUNT(*) sau join = số khách."** Sau join 1–n, `COUNT(*)` đếm dòng ở grain chi tiết hơn; cần `COUNT(DISTINCT customer_id)`.
- **"Trung bình của trung bình = trung bình chung."** Trung bình của tỉ lệ chuyển đổi các ngày khác trung bình tính trên tổng (tổng chuyển đổi / tổng lượt), trừ khi mọi ngày cùng cỡ. Gộp tử số và mẫu số riêng rồi mới chia.
- **"Chuẩn hoá làm phân bố thành chuẩn."** z-score chỉ dời và co giãn; hình dạng (lệch, đuôi dài) giữ nguyên. Muốn đổi hình dạng thì cần biến đổi phi tuyến như log.

## Liên quan
- [01-data-fundamentals.md](01-data-fundamentals.md): grain, tidy data, thang đo quyết định cách mã hoá.
- [03-data-cleaning.md](03-data-cleaning.md): làm sạch trước khi biến đổi; xử lý NULL sau left join.
- [05-descriptive-statistics.md](05-descriptive-statistics.md): các hàm gộp chính là thống kê mô tả.
- [13-time-series-analysis.md](13-time-series-analysis.md): window function cho trung bình trượt, so sánh kỳ trước.
