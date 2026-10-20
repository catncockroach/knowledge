# Xác suất và phân phối

> Xác suất là ngôn ngữ để mô tả bất định; phân phối xác suất là mô hình cho biết một biến ngẫu nhiên nhận giá trị nào với khả năng bao nhiêu, và là nền móng để suy luận từ mẫu ra tổng thể.

## Tại sao cần biết

Mọi câu hỏi "khác biệt này có thật không" đều thực chất là câu hỏi "nếu không có khác biệt thật, khả năng thấy dữ liệu như thế này là bao nhiêu". Trả lời được nó cần mô hình xác suất cho dữ liệu. Ngoài ra, nhận ra dữ liệu của mình trông giống phân phối nào (đếm sự kiện? thời gian chờ? tổng của nhiều yếu tố nhỏ?) giúp chọn đúng thống kê, đúng kiểm định, và nhận ra khi nào giả định bị vi phạm.

## Khái niệm cốt lõi

### Quy tắc xác suất cơ bản
- **Không gian mẫu (sample space)**: tập mọi kết quả có thể. **Biến cố (event)**: một tập con.
- 0 ≤ P(A) ≤ 1; P(không A) = 1 − P(A).
- **Cộng**: P(A ∪ B) = P(A) + P(B) − P(A ∩ B).
- **Xác suất có điều kiện**: P(A | B) = P(A ∩ B) / P(B), tức xác suất A khi đã biết B xảy ra.
- **Độc lập**: P(A ∩ B) = P(A)·P(B), tương đương P(A | B) = P(A).
- **Định lý Bayes**: P(A | B) = P(B | A)·P(A) / P(B). Cho phép "lật" điều kiện: từ P(dương tính | bệnh) suy ra P(bệnh | dương tính).

### Biến ngẫu nhiên
- **Rời rạc**: mô tả bằng hàm xác suất (PMF) P(X = k).
- **Liên tục**: mô tả bằng hàm mật độ (PDF); xác suất là diện tích dưới đường cong trên một khoảng, còn P(X = một giá trị đúng) = 0.
- **Hàm phân phối tích luỹ (CDF)**: F(x) = P(X ≤ x), dùng được cho cả hai loại.
- **Kỳ vọng (expected value)** E[X]: trung bình dài hạn. **Phương sai** Var(X) = E[(X − E[X])²].
- Tính chất hữu ích: E[aX + b] = aE[X] + b; Var(aX + b) = a²Var(X); với X, Y độc lập, Var(X + Y) = Var(X) + Var(Y).

### Các phân phối hay gặp

| Phân phối | Mô tả hiện tượng | Tham số | Mean | Variance |
|---|---|---|---|---|
| Bernoulli | một lần thử có/không (mua hay không) | p | p | p(1−p) |
| Binomial | số lần "có" trong n lần thử độc lập | n, p | np | np(1−p) |
| Poisson | số sự kiện trong một khoảng, sự kiện độc lập, tốc độ ổn định (số đơn mỗi phút) | λ | λ | λ |
| Uniform | mọi giá trị trong [a, b] như nhau | a, b | (a+b)/2 | (b−a)²/12 |
| Exponential | thời gian chờ đến sự kiện tiếp theo trong quá trình Poisson | λ | 1/λ | 1/λ² |
| Normal (Gauss) | tổng của nhiều yếu tố nhỏ độc lập (sai số đo, chiều cao) | μ, σ | μ | σ² |
| Log-normal | tích của nhiều yếu tố nhỏ; biến dương lệch phải (thu nhập, giá trị đơn) | μ, σ của log | | |

Dấu hiệu nhận diện nhanh: dữ liệu đếm với variance ≈ mean gợi ý Poisson; variance lớn hơn mean nhiều (**overdispersion**) gợi ý có sự không đồng nhất giữa các đơn vị. Biến dương, lệch phải, mà log của nó trông đối xứng gợi ý log-normal.

### Phân phối chuẩn và quy tắc 68–95–99,7
Với phân phối chuẩn, khoảng μ ± 1σ chứa khoảng 68%, ± 2σ khoảng 95% (chính xác là ± 1,96σ), ± 3σ khoảng 99,7% xác suất. Biến đổi z = (x − μ)/σ đưa mọi phân phối chuẩn về **chuẩn tắc** (mean 0, sd 1).

## Cách hoạt động

### Luật số lớn (Law of Large Numbers)
Trung bình mẫu x̄ tiến dần về kỳ vọng μ khi n tăng. Đây là cơ sở để "ước lượng từ mẫu" có nghĩa. Luật số lớn nói về dài hạn: nó **không** nói rằng sau chuỗi 5 lần sấp thì lần sau dễ ngửa hơn (ngụy biện con bạc).

### Định lý giới hạn trung tâm (Central Limit Theorem)
Với n quan sát độc lập cùng phân phối có phương sai hữu hạn σ², **phân phối của trung bình mẫu** x̄ xấp xỉ chuẩn với mean μ và độ lệch chuẩn σ/√n khi n đủ lớn, **bất kể phân phối gốc** trông thế nào.

```
Dữ liệu gốc (lệch phải)        Phân phối của x̄ khi lấy mẫu n lần lặp lại
█                                      ▁▃▆█▆▃▁
██                                    (gần chuẩn, hẹp hơn σ/√n)
████▄▂▁▁▁▁▁▁
```

Đây là lý do kiểm định dựa trên phân phối chuẩn và t dùng được cho trung bình của dữ liệu không chuẩn. "Đủ lớn" phụ thuộc độ lệch của dữ liệu gốc: quy tắc ngón tay cái n ≥ 30 thường ổn với dữ liệu lệch vừa, nhưng dữ liệu đuôi rất nặng (doanh thu có vài khách cực lớn) có thể cần hàng nghìn quan sát.

## Ví dụ

### Bayes: xét nghiệm dương tính
Một bệnh có tỉ lệ mắc 1%. Xét nghiệm có độ nhạy 99% (người bệnh → dương tính) và độ đặc hiệu 95% (người khoẻ → âm tính). Một người dương tính, xác suất họ thật sự bệnh?

Xét 10.000 người:
- 100 người bệnh → 99 dương tính.
- 9.900 người khoẻ → 5% × 9.900 = 495 dương tính giả.
- P(bệnh | dương tính) = 99 / (99 + 495) ≈ **16,7%**.

Dù xét nghiệm "chính xác 99%", phần lớn người dương tính lại không bệnh, vì bệnh hiếm. Cùng logic này áp dụng cho hệ thống cảnh báo gian lận, phát hiện bất thường: khi sự kiện thật hiếm, cảnh báo giả chiếm đa số.

### Binomial và Poisson
- Tỉ lệ một email bị mở là 10%. Gửi 10 email, xác suất **không** email nào được mở: 0,9¹⁰ ≈ 0,349.
- Trung bình 3 đơn/phút (Poisson λ = 3): P(0 đơn) ≈ 0,050; P(3 đơn) ≈ 0,224; P(≥ 6 đơn) ≈ 1 − (0,050 + 0,149 + 0,224 + 0,224 + 0,168 + 0,101) ≈ 0,084. Một phút có 6 đơn trở lên xảy ra khoảng 8% số phút, không phải bất thường.

## Hiểu nhầm thường gặp

- **"P(A | B) = P(B | A)."** Đây là lỗi đảo điều kiện (ví dụ xét nghiệm ở trên). P(dương tính | bệnh) = 99% nhưng P(bệnh | dương tính) ≈ 17%.
- **"CLT nói dữ liệu sẽ thành phân phối chuẩn khi có nhiều."** CLT nói về phân phối của **trung bình mẫu**, không phải của dữ liệu. Một triệu đơn hàng vẫn lệch phải như cũ.
- **"Dữ liệu thật thường tuân theo phân phối chuẩn."** Nhiều biến nghiệp vụ lệch phải, đuôi nặng, bị chặn ở 0. Phân phối chuẩn là mô hình hữu ích cho sai số và trung bình, không phải mặc định cho mọi biến.
- **"Độc lập và loại trừ nhau là một."** Hai biến cố loại trừ (không thể cùng xảy ra) có xác suất khác 0 thì **không** độc lập: biết A xảy ra thì chắc chắn B không xảy ra.

## Liên quan
- [05-descriptive-statistics.md](05-descriptive-statistics.md): mean và variance của mẫu so với của phân phối.
- [09-statistical-inference.md](09-statistical-inference.md): dùng CLT để xây khoảng tin cậy và kiểm định.
- [13-time-series-analysis.md](13-time-series-analysis.md): khi quan sát không độc lập theo thời gian.
