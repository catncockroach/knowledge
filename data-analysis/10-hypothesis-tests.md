# Các kiểm định thống kê thường dùng

> Mỗi kiểm định là cùng một logic (H₀, thống kê, p-value) áp cho một kiểu dữ liệu và câu hỏi cụ thể; chọn kiểm định theo loại biến kết quả, số nhóm, mẫu độc lập hay ghép cặp, và giả định nào chấp nhận được.

## Tại sao cần biết

Dùng sai kiểm định cho p-value sai: t-test độc lập trên dữ liệu ghép cặp làm mất power; chi-square trên tỉ lệ đã tính sẵn thay vì số đếm cho kết quả vô nghĩa; chạy 20 kiểm định rồi báo cái nhỏ nhất thì gần như chắc chắn tìm ra "phát hiện". File này nối logic chung ở [09-statistical-inference.md](09-statistical-inference.md) với tình huống cụ thể.

## Khái niệm cốt lõi

### Bảng chọn kiểm định

| Biến kết quả | So sánh | Độc lập / ghép cặp | Tham số (giả định phân phối) | Phi tham số / thay thế |
|---|---|---|---|---|
| Định lượng | 1 nhóm với một giá trị | — | One-sample t-test | Wilcoxon signed-rank |
| Định lượng | 2 nhóm | Độc lập | Welch t-test | Mann-Whitney U, permutation test |
| Định lượng | 2 điều kiện, cùng đối tượng | Ghép cặp | Paired t-test | Wilcoxon signed-rank |
| Định lượng | ≥ 3 nhóm | Độc lập | One-way ANOVA (Welch ANOVA) | Kruskal-Wallis |
| Tỉ lệ (có/không) | 2 nhóm | Độc lập | Two-proportion z-test | Fisher exact (mẫu nhỏ) |
| Định tính × định tính | bảng chéo | Độc lập | Chi-square test of independence | Fisher exact |
| Định tính | phân bố so với kỳ vọng | — | Chi-square goodness-of-fit | |

### t-test
- So sánh trung bình, thống kê t = hiệu số / SE của hiệu số.
- **Welch t-test** không giả định hai nhóm cùng phương sai; nên là mặc định thay cho Student t-test.
- Giả định: quan sát độc lập; trung bình mỗi nhóm xấp xỉ chuẩn (đúng với mẫu đủ lớn nhờ CLT, hoặc dữ liệu gần chuẩn với mẫu nhỏ).
- **Paired t-test** thực chất là one-sample t-test trên hiệu số từng cặp; nó loại bỏ khác biệt giữa các đối tượng, nên power cao hơn nhiều khi dữ liệu thật sự ghép cặp (trước/sau trên cùng người dùng).

### Chi-square test of independence
- Dữ liệu: bảng chéo **số đếm** (không phải phần trăm).
- Số kỳ vọng mỗi ô nếu độc lập: E = (tổng dòng × tổng cột) / tổng chung.
- χ² = Σ (O − E)² / E, bậc tự do (số dòng − 1)(số cột − 1).
- Quy tắc thường dùng: số kỳ vọng mỗi ô nên ≥ 5; nếu không thì dùng Fisher exact.

### ANOVA
- Kiểm định H₀: mọi nhóm cùng mean, bằng cách so phương sai **giữa** các nhóm với phương sai **trong** nhóm (thống kê F).
- Bác bỏ H₀ chỉ cho biết "có ít nhất một nhóm khác"; cần kiểm định hậu nghiệm (post-hoc, ví dụ Tukey HSD) để biết nhóm nào.

### Kiểm định phi tham số
- Dựa trên thứ hạng hoặc hoán vị, ít giả định về hình dạng phân phối.
- **Mann-Whitney U** kiểm tra xem giá trị ở một nhóm có xu hướng lớn hơn nhóm kia không; nó **không** đơn thuần là "kiểm định median" trừ khi hai phân phối cùng hình dạng.
- **Permutation test**: dưới H₀ nhãn nhóm không quan trọng; xáo trộn nhãn nhiều lần, tính lại hiệu số, p-value = tỉ lệ lần xáo trộn cho hiệu số cực đoan bằng hoặc hơn quan sát thật. Trực quan, dùng được cho bất kỳ thống kê nào.

### So sánh bội (multiple comparisons)
Chạy m kiểm định độc lập ở α = 0,05 khi H₀ đều đúng, xác suất có **ít nhất một** dương tính giả là 1 − 0,95^m. Với m = 20: 1 − 0,95²⁰ ≈ **64%**.
- **Bonferroni**: dùng ngưỡng α/m cho từng kiểm định. Kiểm soát xác suất có bất kỳ dương tính giả nào (FWER), khá bảo thủ.
- **Benjamini-Hochberg**: kiểm soát **tỉ lệ phát hiện sai (FDR)**, tức tỉ lệ dương tính giả trong số các kết quả được báo là có ý nghĩa. Ít mất power hơn khi m lớn.
- Thực hành tốt nhất: chọn trước một **chỉ số chính (primary metric)** và một kiểm định chính; các phân tích khác coi là khám phá.

## Cách hoạt động

```
Biến kết quả là gì?
├─ có/không hoặc nhóm ──► bảng đếm ──► 2×2: z-test tỉ lệ / chi-square / Fisher
│                                      r×c: chi-square / Fisher
└─ định lượng
     ├─ cùng đối tượng đo 2 lần? ── có ──► paired t / Wilcoxon signed-rank
     └─ không
          ├─ 2 nhóm ──► Welch t (lệch mạnh, mẫu nhỏ: Mann-Whitney hoặc permutation)
          └─ ≥3 nhóm ─► ANOVA + post-hoc (hoặc Kruskal-Wallis)
```

## Ví dụ

### Welch t-test: thời gian tải trang
Phiên bản cũ (A) và mới (B), mỗi bên 8 lần đo (giây):
- A: 2,1; 2,4; 1,9; 2,6; 2,2; 2,5; 2,3; 2,0 → mean 2,25, variance 0,060.
- B: 1,8; 1,9; 2,0; 1,7; 2,1; 1,6; 1,9; 2,0 → mean 1,875, variance 0,028.
- SE của hiệu số = √(0,060/8 + 0,028/8) ≈ 0,105.
- t = (2,25 − 1,875) / 0,105 ≈ **3,58**, bậc tự do Welch ≈ 12,4, p hai phía ≈ **0,004**.
- Kết luận: B nhanh hơn khoảng 0,375 giây, khác biệt khó xảy ra do ngẫu nhiên. Cỡ hiệu ứng mới là thứ quyết định có đáng triển khai không.

### Chi-square: thiết bị và mua hàng
| | Mua | Không mua | Tổng |
|---|---|---|---|
| Mobile | 90 | 110 | 200 |
| Desktop | 60 | 140 | 200 |
| Tổng | 150 | 250 | 400 |

- Số kỳ vọng nếu độc lập: 75 / 125 ở mỗi dòng.
- χ² = (90−75)²/75 + (110−125)²/125 + (60−75)²/75 + (140−125)²/125 = 3 + 1,8 + 3 + 1,8 = **9,6**, bậc tự do 1, p ≈ **0,002**.
- Tỉ lệ mua: mobile 45%, desktop 30%. Có liên hệ giữa thiết bị và mua hàng; nhưng đây là dữ liệu quan sát, nên chưa nói được là thiết bị *gây ra* khác biệt (xem [12-experiments-and-causality.md](12-experiments-and-causality.md)).

## Hiểu nhầm thường gặp

- **"Phải kiểm tra phân phối chuẩn của dữ liệu trước khi dùng t-test."** Với mẫu vừa và lớn, điều cần là trung bình xấp xỉ chuẩn (CLT); kiểm định chuẩn (Shapiro-Wilk) với n lớn gần như luôn bác bỏ vì độ lệch nhỏ không quan trọng. Lo hơn về ngoại lai cực đoan và tính độc lập.
- **"Phi tham số luôn an toàn hơn."** Chúng trả lời câu hỏi hơi khác (thứ hạng, không phải trung bình), và khi câu hỏi nghiệp vụ là về tổng/trung bình (doanh thu) thì kiểm định trung bình mới đúng câu hỏi.
- **"Kiểm định nhiều phân nhóm, báo nhóm có p < 0,05."** Đó là p-hacking. Hiệu chỉnh so sánh bội, hoặc coi là giả thuyết cần xác nhận.
- **"Tính chi-square trên phần trăm."** χ² phụ thuộc cỡ mẫu; phải dùng số đếm thật.

## Liên quan
- [09-statistical-inference.md](09-statistical-inference.md): logic chung của p-value, lỗi loại I/II, cỡ hiệu ứng.
- [11-correlation-and-regression.md](11-correlation-and-regression.md): hồi quy tổng quát hoá t-test và ANOVA, cho phép kiểm soát biến khác.
- [12-experiments-and-causality.md](12-experiments-and-causality.md): kiểm định trong A/B test, peeking và so sánh bội theo thời gian.
