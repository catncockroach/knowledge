# Phân tích chuỗi thời gian

> Chuỗi thời gian là các quan sát của cùng một đại lượng theo thứ tự thời gian; vì các điểm gần nhau phụ thuộc lẫn nhau, cần tách xu hướng, mùa vụ và nhiễu trước khi so sánh, phát hiện bất thường hay dự báo.

## Tại sao cần biết

Phần lớn chỉ số nghiệp vụ là chuỗi thời gian: doanh thu ngày, người dùng hoạt động, số ticket hỗ trợ. Câu hỏi "hôm nay có bất thường không" hay "tháng này tăng thật hay chỉ do mùa" không trả lời được bằng các kiểm định ở [10-hypothesis-tests.md](10-hypothesis-tests.md), vì chúng giả định quan sát độc lập, còn doanh thu hôm nay rất giống hôm qua. Bỏ qua cấu trúc thời gian dẫn tới so sánh sai kỳ, tương quan giả giữa hai chuỗi cùng tăng, và dự báo bỏ quên mùa vụ.

## Khái niệm cốt lõi

### Các thành phần
- **Xu hướng (trend)**: hướng đi dài hạn (tăng trưởng người dùng).
- **Mùa vụ (seasonality)**: mẫu lặp với chu kỳ cố định và biết trước: theo giờ trong ngày, ngày trong tuần, tháng trong năm, dịp Tết.
- **Chu kỳ (cycle)**: dao động không có chu kỳ cố định (chu kỳ kinh tế).
- **Phần dư / nhiễu (residual)**: phần còn lại sau khi tách các thành phần trên.

Hai dạng ghép:
- **Cộng (additive)**: Y = Trend + Season + Residual, khi biên độ mùa vụ không đổi theo mức.
- **Nhân (multiplicative)**: Y = Trend × Season × Residual, khi biên độ mùa vụ lớn dần theo mức (mùa cao điểm tăng 30% dù quy mô là bao nhiêu). Lấy log biến dạng nhân thành dạng cộng.

### Tự tương quan (autocorrelation)
Tương quan của chuỗi với chính nó lệch k bước (lag k). Chuỗi ngày có mùa vụ tuần sẽ có tự tương quan cao ở lag 7, 14, … Đồ thị ACF (autocorrelation function) giúp nhận ra chu kỳ.

### Tính dừng (stationarity)
Chuỗi dừng có mean, variance và cấu trúc tự tương quan không đổi theo thời gian. Nhiều mô hình cổ điển cần dữ liệu dừng; cách thường dùng là **lấy sai phân** (Yₜ − Yₜ₋₁ cho xu hướng, Yₜ − Yₜ₋₇ cho mùa vụ tuần).

### Làm mượt
- **Trung bình trượt (moving average)**: trung bình của k điểm gần nhất. Trung bình trượt 7 ngày triệt tiêu mùa vụ tuần.
- **Làm mượt hàm mũ (exponential smoothing)**: trung bình có trọng số giảm dần theo độ cũ; Holt-Winters mở rộng cho xu hướng và mùa vụ.

## Cách hoạt động

### So sánh đúng kỳ
- **WoW (week-over-week)** cùng thứ: so Chủ nhật này với Chủ nhật trước, không so Chủ nhật với thứ Bảy.
- **YoY (year-over-year)**: so với cùng kỳ năm trước, loại bỏ mùa vụ năm. Cẩn thận với lễ di động: Tết âm lịch rơi vào tháng 1 hoặc tháng 2 dương lịch tuỳ năm, nên so tháng 1 với tháng 1 có thể là so "có Tết" với "không có Tết". Hãy căn theo số ngày trước/sau Tết.
- **Hiệu ứng lịch**: số ngày trong tháng, số ngày cuối tuần, ngày lương.

### Phân rã (decomposition)

```
Chuỗi gốc  ─►  Trend (trung bình trượt dài hoặc STL)
           ─►  Seasonal (trung bình phần chênh theo vị trí trong chu kỳ)
           ─►  Residual = gốc − trend − seasonal   ← tìm bất thường ở đây
```

**STL** (Seasonal-Trend decomposition using Loess) là phương pháp phổ biến, bền với ngoại lai và cho phép mùa vụ thay đổi chậm.

### Phát hiện bất thường
Bất thường là điểm lệch xa **so với kỳ vọng**, không phải so với mean toàn chuỗi. Cách đơn giản và hiệu quả: dự báo giá trị kỳ vọng (ví dụ cùng thứ tuần trước × xu hướng), rồi đánh dấu khi phần dư vượt k lần độ lệch điển hình của phần dư (dùng MAD cho bền vững, [05-descriptive-statistics.md](05-descriptive-statistics.md)).

### Dự báo cơ bản
Bắt đầu từ mô hình đơn giản, vì chúng là mốc so sánh khó vượt hơn người ta nghĩ:
- **Naive**: ngày mai = hôm nay.
- **Seasonal naive**: thứ Hai tới = thứ Hai này.
- **Drift / trung bình**: kéo dài xu hướng hoặc lấy trung bình lịch sử.
- **Exponential smoothing (ETS), ARIMA**: mô hình thống kê cổ điển cho xu hướng, mùa vụ, tự tương quan.
- Mô hình có biến ngoài (khuyến mãi, ngày lễ, thời tiết) khi các yếu tố đó biết trước.

**Đánh giá dự báo**:
- Chỉ số: **MAE** (sai số tuyệt đối trung bình, cùng đơn vị), **MAPE** (sai số phần trăm, vô nghĩa khi giá trị thật gần 0), **RMSE** (phạt nặng sai số lớn).
- **Backtesting**: luôn tách theo thời gian (huấn luyện trên quá khứ, kiểm tra trên giai đoạn sau). Xáo trộn ngẫu nhiên như dữ liệu thường sẽ cho mô hình "nhìn thấy tương lai".
- Báo **khoảng dự báo**, không chỉ một con số: độ bất định tăng theo tầm xa dự báo.

## Ví dụ

Số đơn mỗi ngày trong 2 tuần (thứ Hai → Chủ nhật):

| | T2 | T3 | T4 | T5 | T6 | T7 | CN |
|---|---|---|---|---|---|---|---|
| Tuần 1 | 120 | 115 | 118 | 122 | 140 | 190 | 210 |
| Tuần 2 | 126 | 121 | 124 | 128 | 147 | 199 | 220 |

- "Chủ nhật tăng 10,6% so với hôm qua" (220 vs 199): đúng số học nhưng vô nghĩa, vì Chủ nhật luôn cao hơn thứ Bảy.
- So đúng kỳ, Chủ nhật tuần 2 vs Chủ nhật tuần 1: **+4,8%**. Tổng tuần 2 so với tuần 1: +4,9%. Hai con số khớp → tăng trưởng đều, không có gì bất thường ở Chủ nhật.
- Trung bình trượt 7 ngày đi từ 145,0 lên 152,1: đường mượt, cho thấy xu hướng mà không bị răng cưa thứ Bảy, Chủ nhật.
- Dự báo 4 ngày đầu tuần 3, giả sử giá trị thật là 130, 124, 127, 131:
  - Naive (lấy giá trị hôm trước, ngày đầu dùng 220): MAE ≈ **25,8** đơn.
  - Seasonal naive (lấy cùng thứ tuần trước): MAE ≈ **3,3** đơn.
  - Chỉ cần tôn trọng mùa vụ tuần, sai số đã giảm gần 8 lần.

## Hiểu nhầm thường gặp

- **"Hai chuỗi cùng tăng có tương quan cao nên liên quan."** Mọi chuỗi có xu hướng đều tương quan với nhau. Kiểm tra trên sai phân hoặc phần dư sau khi tách xu hướng.
- **"So với hôm qua là cách theo dõi nhanh nhất."** Mùa vụ ngày trong tuần làm so sánh liền kề nhiễu. Dùng cùng kỳ hoặc trung bình trượt.
- **"Mô hình phức tạp dự báo tốt hơn."** Mô hình đơn giản theo mùa vụ thường là mốc khó vượt; luôn so với nó trước khi dùng mô hình phức tạp.
- **"Kiểm định t trên hai giai đoạn trước/sau là đủ."** Quan sát theo thời gian không độc lập và có xu hướng sẵn; so sánh trước/sau lẫn lộn tác động với xu hướng. Dùng nhóm đối chứng (DiD, [12-experiments-and-causality.md](12-experiments-and-causality.md)) hoặc mô hình chuỗi thời gian.

## Liên quan
- [04-data-wrangling.md](04-data-wrangling.md): window function cho trung bình trượt và LAG.
- [08-probability-and-distributions.md](08-probability-and-distributions.md): giả định độc lập bị vi phạm thế nào.
- [11-correlation-and-regression.md](11-correlation-and-regression.md): tương quan giả giữa các chuỗi có xu hướng.
- [14-analytical-techniques.md](14-analytical-techniques.md): cohort là cách nhìn thời gian theo "tuổi" của khách hàng.
