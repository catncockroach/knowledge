# Tương quan và hồi quy

> Tương quan đo hai biến cùng biến thiên mạnh đến đâu; hồi quy mô hình hoá biến kết quả theo một hay nhiều biến giải thích, cho phép ước lượng "Y đổi bao nhiêu khi X đổi một đơn vị, giữ các biến khác cố định", nhưng không tự động cho kết luận nhân quả.

## Tại sao cần biết

Hầu hết câu hỏi phân tích có dạng "cái gì đi kèm với cái gì, và mạnh đến đâu": giá có liên quan đến lượng bán không, khách có thời gian dùng app cao có ít rời bỏ không. Hồi quy là công cụ đa năng nhất của phân tích: t-test và ANOVA ([10-hypothesis-tests.md](10-hypothesis-tests.md)) là trường hợp đặc biệt của nó, và nó cho phép **kiểm soát** biến gây nhiễu. Đồng thời đây là nơi dễ kết luận sai nhất, vì tương quan rất dễ bị đọc thành nhân quả.

## Khái niệm cốt lõi

### Tương quan
- **Pearson r**: đo quan hệ **tuyến tính**, trong [−1, 1]. r = 0 không có nghĩa là không liên quan: quan hệ hình chữ U có r ≈ 0.
- **Spearman ρ**: tương quan trên thứ hạng, đo quan hệ **đơn điệu**, bền với ngoại lai.
- **r²**: tỉ lệ phương sai của Y "được giải thích" bởi quan hệ tuyến tính với X.
- Một ngoại lai có thể tạo ra hoặc xoá đi tương quan mạnh (bộ tứ Anscombe, [06-data-visualization.md](06-data-visualization.md)). Luôn nhìn scatter plot.

### Tương quan không phải nhân quả
X và Y tương quan có thể vì:
1. X gây ra Y.
2. Y gây ra X (**nhân quả ngược**).
3. Z gây ra cả hai (**confounder**): doanh số kem và số vụ đuối nước cùng tăng vì trời nóng.
4. Chọn mẫu tạo ra quan hệ (**collider bias**): chỉ xét người đã được tuyển, hai tiêu chí tuyển có thể trông như tương quan âm.
5. Ngẫu nhiên, đặc biệt khi đã thử nhiều cặp biến.

### Hồi quy tuyến tính đơn
Mô hình: Y = β₀ + β₁X + ε.
- **OLS (Ordinary Least Squares)**: chọn β₀, β₁ làm nhỏ nhất tổng bình phương phần dư Σ(yᵢ − ŷᵢ)².
- Công thức: β̂₁ = Σ(xᵢ − x̄)(yᵢ − ȳ) / Σ(xᵢ − x̄)², β̂₀ = ȳ − β̂₁x̄.
- **Diễn giải**: β₁ là mức thay đổi trung bình của Y khi X tăng 1 đơn vị.
- **R²** = 1 − SS_residual / SS_total: tỉ lệ phương sai Y mà mô hình giải thích. R² cao không có nghĩa mô hình đúng, R² thấp không có nghĩa hệ số vô dụng.
- Mỗi hệ số có SE, khoảng tin cậy và p-value (H₀: β = 0).

### Hồi quy bội (multiple regression)
Y = β₀ + β₁X₁ + β₂X₂ + … + ε.
- β₁ giờ là tác động của X₁ **khi giữ X₂, … cố định**. Đây là cách "kiểm soát" confounder **đã đo được**.
- **Biến giả (dummy)**: biến định tính k mức → k − 1 cột 0/1, một mức làm mốc (baseline). Hệ số là chênh lệch so với mốc.
- **Tương tác (interaction)**: thêm X₁·X₂ khi tác động của X₁ phụ thuộc vào X₂ (giảm giá hiệu quả hơn với khách mới).
- **Đa cộng tuyến (multicollinearity)**: các X tương quan mạnh với nhau → hệ số không ổn định, SE lớn, dù dự đoán vẫn có thể tốt.

### Giả định của hồi quy tuyến tính (OLS)
- **Tuyến tính**: E[Y] là hàm tuyến tính của các X (có thể sau biến đổi).
- **Độc lập** của phần dư (vi phạm với dữ liệu thời gian, dữ liệu theo cụm).
- **Phương sai đều (homoscedasticity)**: độ phân tán phần dư không đổi theo X. Vi phạm → SE sai; dùng robust SE.
- **Phần dư xấp xỉ chuẩn**: chủ yếu quan trọng cho khoảng tin cậy với mẫu nhỏ.

Kiểm tra bằng **đồ thị phần dư theo giá trị dự đoán**: thấy hình phễu (phương sai tăng) hoặc đường cong (sai dạng hàm) là có vấn đề.

### Biến đổi log và cách đọc hệ số
| Mô hình | Diễn giải β₁ (xấp xỉ, với β₁ nhỏ) |
|---|---|
| Y ~ X | X +1 đơn vị → Y + β₁ đơn vị |
| log(Y) ~ X | X +1 đơn vị → Y thay đổi khoảng 100·β₁ % |
| Y ~ log(X) | X +1% → Y thay đổi khoảng β₁/100 đơn vị |
| log(Y) ~ log(X) | X +1% → Y thay đổi khoảng β₁ % (độ co giãn) |

### Hồi quy logistic
Khi Y là có/không (mua, rời bỏ): mô hình log-odds, log(p / (1 − p)) = β₀ + β₁X.
- e^β₁ là **odds ratio**: X tăng 1 đơn vị thì odds nhân với e^β₁.
- Ví dụ β₁ = 0,4 → odds ratio ≈ 1,49, tức odds tăng khoảng 49%. Odds không phải xác suất: với p nhỏ hai cái gần nhau, với p lớn thì khác xa.

## Cách hoạt động

### Simpson's paradox: khi kiểm soát đổi chiều kết luận
Dữ liệu điều trị sỏi thận (Charig và cộng sự, 1986), tỉ lệ thành công:

| | Sỏi nhỏ | Sỏi lớn | Tổng |
|---|---|---|---|
| Phương pháp A | 81/87 = **93,1%** | 192/263 = **73,0%** | 273/350 = 78,0% |
| Phương pháp B | 234/270 = 86,7% | 55/80 = 68,8% | 289/350 = **82,6%** |

A tốt hơn ở **từng nhóm**, nhưng B tốt hơn ở **tổng**. Lý do: A được dùng chủ yếu cho ca khó (sỏi lớn), vốn có tỉ lệ thành công thấp hơn. Kích thước sỏi là confounder, ảnh hưởng cả việc chọn phương pháp lẫn kết quả. Hồi quy bội có biến "kích thước sỏi" cho kết luận theo từng nhóm. Nhưng việc nên gộp hay tách **không** do số liệu quyết định: phải lập luận về cơ chế nhân quả (xem [12-experiments-and-causality.md](12-experiments-and-causality.md)).

## Ví dụ

Chi phí quảng cáo (triệu đồng/tuần) và doanh thu (triệu đồng/tuần) trong 6 tuần:

| X (quảng cáo) | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Y (doanh thu) | 3,1 | 4,9 | 7,2 | 8,8 | 11,1 | 12,9 |

- x̄ = 3,5; ȳ = 8,0; β̂₁ ≈ **1,98**; β̂₀ ≈ **1,08**; R² ≈ 0,998.
- Đọc: mỗi triệu quảng cáo thêm đi kèm khoảng 1,98 triệu doanh thu; khi không quảng cáo, mô hình ngoại suy doanh thu ≈ 1,08 triệu (điểm X = 0 nằm ngoài dữ liệu, nên con số này không đáng tin).
- Dự đoán X = 7: ≈ 14,9 triệu. Đây là **ngoại suy** ra ngoài khoảng đã quan sát; quan hệ có thể bão hoà.
- Cảnh báo nhân quả: nếu shop tăng quảng cáo vào những tuần vốn đã đông khách (cuối tháng, mùa lễ), một phần β̂₁ là hiệu ứng mùa vụ chứ không phải của quảng cáo. Muốn biết tác động thật cần thí nghiệm hoặc kiểm soát mùa vụ.

## Hiểu nhầm thường gặp

- **"R² cao nghĩa là mô hình tốt."** Hai chuỗi thời gian cùng có xu hướng tăng cho R² rất cao mà không liên quan gì (spurious regression). Đánh giá mô hình bằng phần dư, bằng dữ liệu ngoài mẫu, và bằng lập luận.
- **"Thêm càng nhiều biến kiểm soát càng tốt."** Kiểm soát một biến **trung gian** (nằm trên đường X → M → Y) xoá mất chính tác động cần đo; kiểm soát một **collider** tạo ra quan hệ giả.
- **"Hệ số có ý nghĩa thống kê thì quan trọng."** Hệ số có thể khác 0 rõ ràng nhưng nhỏ đến mức không đáng quan tâm. Đọc độ lớn và khoảng tin cậy.
- **"Hồi quy dự đoán tốt thì hệ số có nghĩa nhân quả."** Dự đoán và giải thích nhân quả là hai mục tiêu khác nhau; một biến dự đoán tốt có thể chỉ là dấu hiệu chứ không phải nguyên nhân.

## Liên quan
- [05-descriptive-statistics.md](05-descriptive-statistics.md): covariance và tương quan.
- [09-statistical-inference.md](09-statistical-inference.md): SE, CI và p-value cho hệ số.
- [12-experiments-and-causality.md](12-experiments-and-causality.md): khi nào hệ số có thể đọc như tác động nhân quả.
- [13-time-series-analysis.md](13-time-series-analysis.md): hồi quy trên dữ liệu thời gian và tương quan giả.
