# Data analysis (Phân tích dữ liệu)

Kiến thức cơ sở của phân tích dữ liệu: hiểu dữ liệu đo cái gì, đưa nó về trạng thái dùng được, tóm tắt và khám phá nó, rồi dùng xác suất và thống kê để rút ra kết luận đáng tin, từ mô tả tới nhân quả. Đây là nền cho data analyst, product analytics, BI, và là bước đệm trước khi học machine learning. Bộ ghi chú tập trung vào cơ chế và lý do, kèm ví dụ có số liệu tính sẵn.

## Phạm vi
- **Có:**
  - Bản chất dữ liệu và thang đo, thu thập và lấy mẫu.
  - Làm sạch và biến đổi dữ liệu (SQL/pandas ở mức khái niệm).
  - Thống kê mô tả, trực quan hoá, EDA.
  - Xác suất và phân phối, suy luận thống kê, các kiểm định thường dùng.
  - Tương quan và hồi quy (tuyến tính, logistic), thí nghiệm A/B và suy luận nhân quả.
  - Chuỗi thời gian, các kỹ thuật phân tích nghiệp vụ (funnel, cohort, phân khúc, mix effect).
  - Quy trình làm việc và truyền đạt kết quả.
- **Không:** machine learning chuyên sâu (cây quyết định, mạng nơ-ron, tuning), hạ tầng data engineering (pipeline, warehouse, streaming), hướng dẫn cú pháp chi tiết của từng công cụ hay sản phẩm BI cụ thể, thống kê Bayes chuyên sâu.
- **Đối tượng:** người biết CNTT cơ bản (biết bảng, biết chút SQL hoặc lập trình), học phân tích dữ liệu và thống kê từ gốc.

## Bản đồ tư duy

```
            Câu hỏi & quyết định ─────────────────────────────── 15 quy trình, truyền đạt
                     │
   DỮ LIỆU     01 bản chất, thang đo ── 02 thu thập, lấy mẫu, lệch
                     │
   XỬ LÝ       03 làm sạch ── 04 biến đổi, join, group by
                     │
   MÔ TẢ       05 thống kê mô tả ── 06 trực quan hoá ── 07 EDA
                     │
   SUY LUẬN    08 xác suất, phân phối ── 09 suy luận (SE, CI, p-value) ── 10 kiểm định
                     │
   MÔ HÌNH     11 tương quan, hồi quy ── 12 thí nghiệm, nhân quả ── 13 chuỗi thời gian
                     │
   ỨNG DỤNG    14 funnel, cohort, phân khúc, mix effect
```

## Các file
Đọc theo thứ tự:

| File | Nội dung |
|---|---|
| [01-data-fundamentals.md](01-data-fundamentals.md) | Đơn vị quan sát, biến, grain; bốn thang đo nominal/ordinal/interval/ratio và phép tính nào có nghĩa; tidy data; vòng đời phân tích và ba loại câu hỏi. |
| [02-data-collection-and-sampling.md](02-data-collection-and-sampling.md) | Tổng thể, mẫu, tham số; dữ liệu quan sát và thí nghiệm; các cách lấy mẫu; sai số ngẫu nhiên khác lệch, và các loại lệch chọn mẫu thường gặp. |
| [03-data-cleaning.md](03-data-cleaning.md) | Các chiều chất lượng dữ liệu, quy trình làm sạch, cơ chế thiếu MCAR/MAR/MNAR và chiến lược điền, phát hiện và xử lý ngoại lai, trùng lặp. |
| [04-data-wrangling.md](04-data-wrangling.md) | Năm phép cơ bản trên bảng, các loại join và lỗi nhân dòng, group by và window function, xoay wide/long, chuẩn hoá, log, mã hoá biến. |
| [05-descriptive-statistics.md](05-descriptive-statistics.md) | Mean/median/mode, phương sai và vì sao chia n − 1, percentile, IQR, độ lệch; chọn thống kê theo thang đo, hình dạng phân bố và câu hỏi. |
| [06-data-visualization.md](06-data-visualization.md) | Mã hoá thị giác và thứ hạng độ chính xác, chọn đồ thị theo câu hỏi, đọc histogram/boxplot, các cách vẽ gây hiểu sai, bộ tứ Anscombe. |
| [07-exploratory-data-analysis.md](07-exploratory-data-analysis.md) | Quy trình khám phá một bộ dữ liệu mới, tín hiệu đáng ngờ (bậc thang, rò rỉ dữ liệu), tách khám phá và xác nhận để không tự lừa mình. |
| [08-probability-and-distributions.md](08-probability-and-distributions.md) | Xác suất có điều kiện và Bayes, biến ngẫu nhiên, các phân phối Bernoulli/Binomial/Poisson/Normal/Log-normal, luật số lớn và định lý giới hạn trung tâm. |
| [09-statistical-inference.md](09-statistical-inference.md) | Phân phối lấy mẫu và sai số chuẩn, khoảng tin cậy, logic kiểm định và p-value, lỗi loại I/II, power, cỡ hiệu ứng, bootstrap. |
| [10-hypothesis-tests.md](10-hypothesis-tests.md) | Bảng chọn kiểm định; t-test, chi-square, ANOVA, phi tham số và permutation test với ví dụ tính tay; so sánh bội và cách hiệu chỉnh. |
| [11-correlation-and-regression.md](11-correlation-and-regression.md) | Pearson/Spearman, tương quan khác nhân quả, hồi quy OLS đơn và bội, giả định và phần dư, đọc hệ số khi có log, logistic và odds ratio, Simpson's paradox. |
| [12-experiments-and-causality.md](12-experiments-and-causality.md) | Kết quả tiềm năng và vì sao ngẫu nhiên hoá hoạt động; thiết kế và tính cỡ mẫu A/B test; peeking, SRM; DiD, DAG và các phương pháp cho dữ liệu quan sát. |
| [13-time-series-analysis.md](13-time-series-analysis.md) | Xu hướng, mùa vụ, tự tương quan, tính dừng; so sánh đúng kỳ, phân rã, phát hiện bất thường; dự báo cơ bản và cách đánh giá bằng backtesting. |
| [14-analytical-techniques.md](14-analytical-techniques.md) | Thiết kế chỉ số, funnel, cohort và retention, phân khúc RFM/clustering, Pareto, phân rã thay đổi thành hiệu ứng tỉ lệ và cơ cấu, unit economics. |
| [15-analysis-workflow-and-communication.md](15-analysis-workflow-and-communication.md) | Đặt câu hỏi từ quyết định, tái lập, chọn công cụ theo vai trò, trình bày kết luận trước kèm độ bất định, danh sách kiểm tra trước khi gửi. |

## Thuật ngữ nền
- **Grain**: mức chi tiết của một dòng dữ liệu; đổi grain là đổi câu hỏi (01, 04).
- **Population / sample**: tổng thể muốn kết luận và phần thực sự quan sát (02).
- **Bias**: sai số có hệ thống, không giảm khi tăng cỡ mẫu (02).
- **Robust statistic**: thống kê ít bị ngoại lai kéo lệch, như median, IQR (05).
- **Standard error**: độ dao động của một ước lượng giữa các mẫu (09).
- **Confidence interval**: khoảng ước lượng kèm mức tin cậy của quy trình (09).
- **p-value**: xác suất thấy dữ liệu cực đoan như vậy nếu H₀ đúng (09).
- **Effect size**: độ lớn của khác biệt hay tác động, tách biệt với ý nghĩa thống kê (09).
- **Confounder**: biến ảnh hưởng cả nguyên nhân lẫn kết quả, tạo tương quan giả (11, 12).
- **Cohort**: nhóm cùng sự kiện khởi đầu trong cùng giai đoạn, theo dõi theo "tuổi" (14).
