# Thống kê mô tả

> Thống kê mô tả nén một cột nhiều giá trị thành vài con số về vị trí, độ phân tán và hình dạng; chọn đúng con số theo thang đo và hình dạng phân bố là kỹ năng nền của mọi phân tích.

## Tại sao cần biết

Không ai đọc được 1 triệu đơn hàng, nhưng ai cũng đọc được "trung vị 210 nghìn, 75% đơn dưới 290 nghìn". Mỗi con số tóm tắt bỏ đi một phần thông tin, và chọn sai con số thì bức tranh bị bóp méo. "Thu nhập trung bình" của một nhóm có vài tỉ phú nói rất ít về người điển hình. Các file sau dùng lại những khái niệm ở đây: phương sai là nền của kiểm định ([09-statistical-inference.md](09-statistical-inference.md)), quartile là nền của boxplot ([06-data-visualization.md](06-data-visualization.md)).

## Khái niệm cốt lõi

### Đo vị trí trung tâm
- **Mean (trung bình cộng)**: x̄ = Σxᵢ / n. Dùng hết thông tin, có tính chất toán học tốt, nhưng **nhạy với ngoại lai**.
- **Median (trung vị)**: giá trị đứng giữa khi sắp xếp; n chẵn thì lấy trung bình hai giá trị giữa. **Bền vững (robust)**: một giá trị cực đoan không kéo nó đi xa.
- **Mode (yếu vị)**: giá trị xuất hiện nhiều nhất. Dùng được cả cho nominal.
- **Trimmed mean**: bỏ k% hai đầu rồi lấy mean, nằm giữa mean và median.
- **Weighted mean**: Σwᵢxᵢ / Σwᵢ, dùng khi các quan sát có trọng số khác nhau (giá trung bình theo số lượng bán).

### Đo độ phân tán
- **Range**: max − min. Chỉ dựa vào hai giá trị cực đoan.
- **Phương sai (variance)**: trung bình bình phương độ lệch khỏi mean. Phương sai mẫu chia cho **n − 1** (hiệu chỉnh Bessel), vì độ lệch được đo quanh x̄, vốn "gần" dữ liệu hơn μ thật, nên chia n sẽ ước lượng thấp có hệ thống.
  s² = Σ(xᵢ − x̄)² / (n − 1)
- **Độ lệch chuẩn (standard deviation)**: s = √s², cùng đơn vị với dữ liệu.
- **Percentile / quartile**: percentile thứ p là giá trị mà p% dữ liệu nhỏ hơn hoặc bằng. Q1 = P25, Q2 = median, Q3 = P75. Có nhiều quy tắc nội suy khác nhau, nên các công cụ có thể cho kết quả hơi khác với mẫu nhỏ.
- **IQR**: Q3 − Q1, độ rộng của 50% dữ liệu ở giữa. Bền vững.
- **MAD (median absolute deviation)**: median của |xᵢ − median|. Bền vững nhất.
- **Hệ số biến thiên (CV)**: s / x̄, so sánh độ phân tán giữa các biến khác thang. Chỉ có nghĩa với dữ liệu ratio.

### Đo hình dạng
- **Độ lệch (skewness)**: lệch phải (đuôi dài bên phải, mean > median) phổ biến với doanh thu, thời gian chờ, thu nhập; lệch trái hiếm hơn (điểm bài thi dễ).
- **Độ nhọn (kurtosis)**: mức "nặng đuôi". Đuôi nặng nghĩa là giá trị cực đoan xuất hiện thường hơn phân phối chuẩn.
- **Đa đỉnh (multimodal)**: nhiều đỉnh thường báo hiệu nhiều nhóm trộn lẫn (khách lẻ và khách sỉ). Một con số tóm tắt duy nhất sẽ che mất điều đó.

### Biến định tính
Tóm tắt bằng **bảng tần số**: đếm (count) và tỉ lệ (proportion) mỗi nhóm. Hai biến định tính thì dùng **bảng chéo (contingency table)**, kiểm định ở [10-hypothesis-tests.md](10-hypothesis-tests.md).

### Quan hệ hai biến định lượng
- **Hiệp phương sai (covariance)**: Σ(xᵢ − x̄)(yᵢ − ȳ)/(n − 1). Dấu cho chiều quan hệ, độ lớn phụ thuộc đơn vị.
- **Hệ số tương quan Pearson r**: covariance chia cho sₓ·s_y, nằm trong [−1, 1], đo **quan hệ tuyến tính**.
- **Spearman ρ**: Pearson trên thứ hạng, đo quan hệ **đơn điệu**, bền với ngoại lai.

Chi tiết và cạm bẫy ở [11-correlation-and-regression.md](11-correlation-and-regression.md).

## Cách hoạt động

### Chọn thống kê theo tình huống

```
Biến định tính? ── có ──► count, proportion, mode
      │ không
      ▼
Phân bố gần đối xứng, không ngoại lai lớn? ── có ──► mean ± sd
      │ không (lệch, đuôi dài, có ngoại lai)
      ▼
median, IQR (hoặc percentile P10/P50/P90), cân nhắc biến đổi log
```

Với số liệu nghiệp vụ, báo cáo nhiều percentile thường hữu ích hơn một con số: "P50 thời gian phản hồi 120 ms, P95 là 800 ms, P99 là 2,3 s" cho biết trải nghiệm của người bình thường lẫn người chịu thiệt nhất.

### Năm số tóm tắt (five-number summary)
min, Q1, median, Q3, max: chính là các mốc vẽ boxplot.

## Ví dụ

Giá trị 10 đơn hàng (nghìn đồng): 120, 150, 150, 180, 200, 220, 250, 300, 350, 2000.

| Thống kê | Có đơn 2000 | Bỏ đơn 2000 |
|---|---|---|
| Mean | 392 | 213,3 |
| Median | 210 | 200 |
| Mode | 150 | 150 |
| Độ lệch chuẩn s | 569,5 | 75,5 |
| Q1 / Q3 (nội suy inclusive) | 157,5 / 287,5 | |
| IQR | 130 | |

Đọc bảng:
- Mean (392) lớn hơn 9/10 giá trị, nên không đại diện cho "đơn điển hình". Mean > median rõ rệt là dấu hiệu lệch phải.
- Một giá trị làm s tăng gần 8 lần (75,5 → 569,5), trong khi median chỉ đổi 10. Đây là ý nghĩa cụ thể của "bền vững".
- Nhưng nếu câu hỏi là **tổng doanh thu** thì mean mới đúng (tổng = mean × n), và đơn 2000 chiếm hơn một nửa doanh thu. Chọn thống kê theo câu hỏi, không theo thói quen.

## Hiểu nhầm thường gặp

- **"Median luôn tốt hơn mean."** Median bỏ qua độ lớn của đuôi. Khi quyết định dựa trên tổng (ngân sách, doanh thu, tải hệ thống), mean là thứ cần.
- **"Khoảng mean ± 2sd chứa 95% dữ liệu."** Chỉ đúng gần đúng khi phân bố gần chuẩn. Với dữ liệu lệch như ví dụ trên, mean − 2s là số âm, vô nghĩa với giá trị đơn hàng.
- **"Độ lệch chuẩn nhỏ nghĩa là dữ liệu tốt."** Độ lệch chuẩn đo độ phân tán, không đo chất lượng; dữ liệu bị điền mean hàng loạt có sd nhỏ giả tạo.
- **"Trung bình của percentile = percentile của tổng."** P95 của từng server không cộng hay lấy trung bình được thành P95 của cả hệ thống; phải tính lại từ dữ liệu gốc hoặc từ histogram gộp.

## Liên quan
- [01-data-fundamentals.md](01-data-fundamentals.md): thang đo quyết định thống kê nào có nghĩa.
- [03-data-cleaning.md](03-data-cleaning.md): IQR và z-score để phát hiện ngoại lai.
- [06-data-visualization.md](06-data-visualization.md): histogram và boxplot cho thấy cái mà con số tóm tắt che đi.
- [08-probability-and-distributions.md](08-probability-and-distributions.md): mean và variance của một phân phối.
