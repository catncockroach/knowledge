# Suy luận thống kê

> Suy luận thống kê đi từ mẫu ra tổng thể và đo luôn độ bất định của bước đi đó: ước lượng kèm sai số chuẩn và khoảng tin cậy, kiểm định giả thuyết bằng p-value, và cân nhắc lỗi loại I, loại II.

## Tại sao cần biết

Mẫu khác nhau cho con số khác nhau. Lấy hai mẫu 500 khách từ cùng một tổng thể, tỉ lệ hài lòng có thể là 42% và 46% mà tổng thể không hề đổi. Suy luận thống kê trả lời câu "con số này dao động bao nhiêu chỉ do ngẫu nhiên lấy mẫu", và từ đó tách tín hiệu khỏi nhiễu. Nó **không** xử lý lệch do thu thập ([02-data-collection-and-sampling.md](02-data-collection-and-sampling.md)); nó giả định mẫu được chọn đúng cách.

## Khái niệm cốt lõi

### Phân phối lấy mẫu và sai số chuẩn
- **Phân phối lấy mẫu (sampling distribution)**: phân phối của một thống kê (x̄, p̂) nếu ta lặp lại việc lấy mẫu vô số lần. Ta chỉ có một mẫu, nhưng lý thuyết (CLT, xem [08-probability-and-distributions.md](08-probability-and-distributions.md)) cho biết hình dạng của nó.
- **Sai số chuẩn (standard error, SE)**: độ lệch chuẩn của phân phối lấy mẫu, tức độ dao động của ước lượng.
  - Trung bình: SE = s / √n.
  - Tỉ lệ: SE = √(p̂(1 − p̂) / n).
- Phân biệt: **sd** đo độ phân tán của **dữ liệu**; **SE** đo độ dao động của **ước lượng**. SE giảm theo √n, còn sd thì không.

### Khoảng tin cậy (confidence interval)
Khoảng 95% có dạng: ước lượng ± hệ số tới hạn × SE (hệ số ≈ 1,96 với phân phối chuẩn; dùng phân phối t khi ước lượng σ bằng s với mẫu nhỏ).

Ý nghĩa chính xác: nếu lặp lại quy trình lấy mẫu và xây khoảng nhiều lần, khoảng **95% số khoảng** tạo ra sẽ chứa tham số thật. Một khoảng cụ thể thì hoặc chứa, hoặc không chứa; "95%" là tính chất của **quy trình**.

### Logic kiểm định giả thuyết
1. **Giả thuyết không (H₀)**: không có hiệu ứng/khác biệt (μ_A = μ_B).
2. **Giả thuyết đối (H₁)**: có khác biệt (μ_A ≠ μ_B, hoặc một phía μ_B > μ_A).
3. **Thống kê kiểm định**: đo khoảng cách giữa dữ liệu và H₀, theo đơn vị SE, ví dụ z = (ước lượng − giá trị theo H₀) / SE.
4. **p-value**: xác suất, **giả sử H₀ đúng**, quan sát được thống kê cực đoan bằng hoặc hơn giá trị thấy được.
5. **Quyết định**: nếu p < α (thường 0,05) thì bác bỏ H₀; nếu không thì "chưa đủ bằng chứng để bác bỏ", không phải "chứng minh H₀ đúng".

### Hai loại lỗi và power

| | H₀ thật sự đúng | H₀ thật sự sai |
|---|---|---|
| Bác bỏ H₀ | **Lỗi loại I** (dương tính giả), xác suất α | Đúng; xác suất = **power** = 1 − β |
| Không bác bỏ | Đúng | **Lỗi loại II** (âm tính giả), xác suất β |

- **α** do ta chọn trước (0,05).
- **Power** phụ thuộc: cỡ hiệu ứng thật (lớn → dễ phát hiện), cỡ mẫu (lớn → dễ), độ nhiễu (lớn → khó), và α. Quy ước thường nhắm power 80%.
- Thiết kế nghiên cứu = chọn n đủ lớn để power đạt mức mong muốn với **hiệu ứng nhỏ nhất đáng quan tâm** (tính ở [12-experiments-and-causality.md](12-experiments-and-causality.md)).

### Cỡ hiệu ứng (effect size)
p-value cho biết "có chắc là khác 0 không", không cho biết "khác bao nhiêu". Luôn báo kèm cỡ hiệu ứng:
- Hiệu số tuyệt đối (+0,6 điểm phần trăm) và tương đối (+12%).
- Chuẩn hoá: **Cohen's d** = (x̄₁ − x̄₂) / s_pooled, giúp so sánh giữa các nghiên cứu.
- Kèm khoảng tin cậy của hiệu ứng: cách trình bày đầy đủ nhất.

### Bootstrap
Khi không có công thức SE (median, tỉ số phức tạp), lấy mẫu **có hoàn lại** từ chính dữ liệu n phần tử, tính thống kê, lặp vài nghìn lần; phân phối của các giá trị thu được xấp xỉ phân phối lấy mẫu. Khoảng 95% bootstrap đơn giản nhất là percentile 2,5 và 97,5 của các giá trị đó.

## Cách hoạt động

```
Tổng thể (μ chưa biết)
     │ lấy mẫu ngẫu nhiên n
     ▼
Mẫu → x̄, s ──► SE = s/√n ──► CI: x̄ ± 1,96·SE         (ước lượng)
                       └───► z = (x̄ − μ₀)/SE → p-value (kiểm định H₀: μ = μ₀)
```

Khoảng tin cậy và kiểm định hai phía ở cùng mức α là hai mặt của một đồng xu: khoảng 95% **không chứa** μ₀ đúng khi kiểm định H₀: μ = μ₀ cho p < 0,05.

### Có ý nghĩa thống kê khác có ý nghĩa thực tế
Với n rất lớn, chênh lệch nhỏ đến mức vô nghĩa cũng cho p < 0,001. Với n nhỏ, chênh lệch lớn và quan trọng có thể cho p = 0,2. Quyết định nên dựa vào khoảng tin cậy của hiệu ứng so với ngưỡng có ý nghĩa nghiệp vụ.

## Ví dụ

**Ước lượng trung bình**: khảo sát n = 100 khách, thời gian dùng app trung bình 52 phút/tuần, s = 10. SE = 10/√100 = 1. CI 95% ≈ 52 ± 1,96 = **[50,0; 54,0]** phút.

**Ước lượng tỉ lệ**: 500 khách, 42% hài lòng. SE = √(0,42 × 0,58 / 500) ≈ 0,022. CI 95% ≈ 42% ± 4,3 = **[37,7%; 46,3%]**. Hai mẫu cho 42% và 46% hoàn toàn có thể đến từ cùng một tổng thể.

**Kiểm định**: năm ngoái thời gian dùng trung bình là 50 phút. H₀: μ = 50. z = (52 − 50)/1 = 2 → p hai phía ≈ 0,046. Bác bỏ H₀ ở α = 0,05, nhưng sát ngưỡng; CI [50,0; 54,0] cho thấy mức tăng thật có thể chỉ quanh 0 phút đến 4 phút.

## Hiểu nhầm thường gặp

- **"p-value là xác suất H₀ đúng."** p-value tính **giả sử** H₀ đúng; nó là P(dữ liệu cực đoan như vậy | H₀), không phải P(H₀ | dữ liệu). Muốn cái sau cần phương pháp Bayes với prior.
- **"p = 0,06 nghĩa là không có hiệu ứng."** Nghĩa là bằng chứng chưa đủ mạnh theo ngưỡng đã chọn. Xem khoảng tin cậy: nó có thể chứa cả hiệu ứng lớn.
- **"Khoảng 95% này chứa μ với xác suất 95%."** Trong khung tần suất, "95%" thuộc về quy trình, không thuộc về một khoảng cụ thể. (Khoảng tin cậy Bayes, credible interval, mới có cách hiểu đó.)
- **"Hai khoảng tin cậy chồng nhau thì khác biệt không có ý nghĩa."** Hai khoảng 95% có thể chồng một phần trong khi hiệu số vẫn có ý nghĩa ở mức 5%. Phải tính khoảng tin cậy cho **hiệu số**.

## Liên quan
- [08-probability-and-distributions.md](08-probability-and-distributions.md): CLT và phân phối chuẩn là nền của SE và CI.
- [10-hypothesis-tests.md](10-hypothesis-tests.md): các kiểm định cụ thể và cách chọn.
- [12-experiments-and-causality.md](12-experiments-and-causality.md): tính cỡ mẫu theo power cho A/B test.
