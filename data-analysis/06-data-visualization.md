# Trực quan hoá dữ liệu

> Đồ thị biến số liệu thành vị trí, độ dài, màu sắc để mắt người nhận ra mẫu hình, ngoại lai và so sánh nhanh hơn đọc bảng; chọn đúng loại đồ thị theo câu hỏi và tránh các cách vẽ gây hiểu sai.

## Tại sao cần biết

Thống kê tóm tắt có thể giống hệt nhau trong khi dữ liệu khác hẳn nhau. Bộ tứ Anscombe (1973) gồm bốn tập dữ liệu có cùng mean, cùng phương sai của x và y, cùng hệ số tương quan (≈ 0,82) và cùng đường hồi quy (y ≈ 3 + 0,5x), nhưng khi vẽ lên thì một tập tuyến tính, một tập cong, một tập có một ngoại lai kéo lệch đường, một tập gần như là một cột thẳng đứng. **Luôn vẽ trước khi tin con số.** Đồ thị là công cụ chính của khám phá ([07-exploratory-data-analysis.md](07-exploratory-data-analysis.md)) và của truyền đạt kết quả ([15-analysis-workflow-and-communication.md](15-analysis-workflow-and-communication.md)).

## Khái niệm cốt lõi

### Mã hoá thị giác (visual encoding)
Mỗi đồ thị ánh xạ biến sang **kênh thị giác**: vị trí x/y, độ dài, góc, diện tích, màu (sắc độ, độ đậm), hình dạng. Nghiên cứu của Cleveland & McGill (1984) cho thấy con người so sánh định lượng chính xác nhất bằng **vị trí trên một trục chung**, rồi đến độ dài, sau đó mới tới góc, diện tích, và kém nhất là thể tích, độ đậm màu. Hệ quả thực hành:
- So sánh giá trị → dùng vị trí/độ dài (bar chart, dot plot), hạn chế pie chart và bubble.
- Màu sắc dùng để **phân nhóm** (hue cho nominal) hoặc **thứ bậc** (một dải đậm-nhạt cho ordinal/định lượng), không để đọc giá trị chính xác.

### Chọn đồ thị theo câu hỏi

| Câu hỏi | Đồ thị phù hợp |
|---|---|
| Phân bố của một biến định lượng | Histogram, density, boxplot, violin, ECDF |
| So sánh giá trị giữa các nhóm | Bar chart (bắt đầu từ 0), dot plot |
| So sánh phân bố giữa các nhóm | Boxplot cạnh nhau, histogram chồng/facet |
| Quan hệ hai biến định lượng | Scatter plot (+ đường xu hướng) |
| Thay đổi theo thời gian | Line chart |
| Thành phần của tổng thể | Stacked bar, (pie chỉ khi ≤ 3–4 phần, khác nhau rõ) |
| Hai biến định tính | Heatmap bảng chéo, mosaic |
| Nhiều biến cùng lúc | Small multiples (facet), scatter matrix, heatmap tương quan |

### Đọc histogram và boxplot
- **Histogram**: chia trục thành các bin, chiều cao là số quan sát. Hình dạng phụ thuộc độ rộng bin; thử vài độ rộng trước khi kết luận về số đỉnh.
- **Boxplot**: hộp từ Q1 đến Q3, vạch giữa là median, "râu" kéo tới giá trị xa nhất còn trong 1,5·IQR, điểm ngoài râu là ngoại lai tiềm năng (quy tắc Tukey). Boxplot che mất đa đỉnh: hai nhóm tách hẳn nhau vẫn có thể cho một hộp trông bình thường.

```
Boxplot giá trị đơn hàng (nghìn đồng):

   120  157.5  210   287.5   350               2000
    |-----[======|======]-----|                 o
   min    Q1   median   Q3   râu trên         ngoại lai
```

### Small multiples
Thay vì nhồi 10 đường vào một đồ thị, vẽ 10 đồ thị nhỏ cùng trục, mỗi đồ thị một nhóm. Mắt so sánh hình dạng giữa các ô rất nhanh, miễn là **trục giống nhau**.

## Cách hoạt động

### Quy trình vẽ một đồ thị giải thích
1. **Viết câu kết luận trước**: "Doanh thu app vượt web từ tháng 6."
2. **Chọn đồ thị** làm cho kết luận đó hiện ra ngay: line chart hai đường.
3. **Loại bỏ nhiễu**: bỏ lưới dày, bỏ 3D, bỏ màu không mang thông tin.
4. **Nhấn mạnh**: tô màu đường chính, xám các đường phụ, ghi chú trực tiếp lên đồ thị thay vì bắt người đọc dò legend.
5. **Tiêu đề là kết luận**, không phải mô tả ("App vượt web từ tháng 6" thay vì "Doanh thu theo kênh").
6. **Ghi rõ đơn vị, nguồn, khoảng thời gian**, và kích thước mẫu nếu có.

Đồ thị khám phá thì ngược lại: vẽ nhanh, nhiều, không cần đẹp; mục tiêu là cho chính mình thấy.

### Các cách vẽ gây hiểu sai
- **Trục bar không bắt đầu từ 0**: bar mã hoá bằng độ dài, cắt trục làm chênh 2% trông như gấp đôi. Line chart thì được cắt trục, vì nó mã hoá bằng vị trí và độ dốc.
- **Hai trục y (dual axis)**: chọn thang cho hai trục tuỳ ý thì vẽ ra được bất kỳ "tương quan" nào.
- **Diện tích/thể tích cho một chiều số liệu**: biểu tượng to gấp đôi cả chiều cao lẫn chiều rộng thì diện tích gấp bốn.
- **Bỏ mẫu số**: bản đồ "số ca" theo tỉnh thường chỉ là bản đồ dân số. Dùng tỉ lệ trên 100.000 dân.
- **Chọn khoảng thời gian có lợi**: cắt đúng điểm đáy để xu hướng trông như tăng mạnh.
- **Overplotting**: scatter hàng triệu điểm thành một vệt đen. Dùng độ trong suốt, lấy mẫu, hoặc hexbin/heatmap 2D.

## Ví dụ

Tỉ lệ chuyển đổi hai phiên bản trang: A = 5,0%, B = 5,6%.
- Bar chart với trục y từ 4,8% đến 5,7%: bar B cao gấp khoảng bốn lần bar A. Người xem nghĩ B "tốt hơn gấp bốn".
- Bar chart từ 0%: hai bar gần bằng nhau, chênh 12% tương đối. Đúng với dữ liệu.
- Tốt hơn nữa: dot plot hai điểm kèm **khoảng tin cậy** 95% cho mỗi tỉ lệ. Nếu hai khoảng chồng nhiều lên nhau, người đọc thấy ngay chênh lệch chưa chắc chắn (tính ở [12-experiments-and-causality.md](12-experiments-and-causality.md)).

## Hiểu nhầm thường gặp

- **"Pie chart luôn sai."** Pie ổn cho 2–3 phần khác nhau rõ, khi thông điệp là "phần lớn". Nó kém khi cần so sánh nhiều phần gần bằng nhau.
- **"Đồ thị càng nhiều thông tin càng tốt."** Một đồ thị giải thích nên trả lời một câu hỏi. Nhiều câu hỏi thì vẽ nhiều đồ thị.
- **"Màu cầu vồng cho dải số liệu là trực quan."** Dải cầu vồng không tăng đều về độ sáng, tạo ranh giới giả và khó đọc với người mù màu. Dùng dải một màu đậm dần (sequential) hoặc hai màu quanh một điểm giữa (diverging).
- **"Đường xu hướng trên scatter chứng minh quan hệ."** Đường fit luôn vẽ được; xem độ phân tán quanh nó và khoảng tin cậy trước khi kết luận.

## Liên quan
- [05-descriptive-statistics.md](05-descriptive-statistics.md): quartile, IQR là nền của boxplot.
- [07-exploratory-data-analysis.md](07-exploratory-data-analysis.md): dùng đồ thị để khám phá có hệ thống.
- [11-correlation-and-regression.md](11-correlation-and-regression.md): scatter plot và bộ tứ Anscombe.
- [15-analysis-workflow-and-communication.md](15-analysis-workflow-and-communication.md): trình bày đồ thị cho người ra quyết định.
