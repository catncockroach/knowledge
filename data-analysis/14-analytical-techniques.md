# Các kỹ thuật phân tích nghiệp vụ

> Một nhóm kỹ thuật lặp lại trong hầu hết phân tích sản phẩm và kinh doanh: thiết kế chỉ số, funnel, cohort và retention, phân khúc, Pareto, và phân rã một thay đổi thành các phần đóng góp để tìm nguyên nhân.

## Tại sao cần biết

Thống kê cho ta công cụ; các kỹ thuật này cho ta **khung câu hỏi** thường gặp: khách rơi rụng ở đâu, khách mới có giữ chân tốt hơn khách cũ không, nhóm nào mang lại phần lớn doanh thu, chỉ số giảm vì đâu. Chúng chủ yếu dựng từ group by, join và window ([04-data-wrangling.md](04-data-wrangling.md)), cộng với tư duy về grain và mẫu số.

## Khái niệm cốt lõi

### Thiết kế chỉ số (metrics)
- **Định nghĩa chính xác**: tử số, mẫu số, cửa sổ thời gian, đơn vị, bộ lọc. "Người dùng hoạt động" là ai: mở app, hay thực hiện một hành động có giá trị? Trong 1 ngày, 7 ngày hay 28 ngày?
- **Chỉ số tỉ lệ (ratio metric)**: luôn kiểm tra tử số và mẫu số riêng. Tỉ lệ chuyển đổi tăng có thể chỉ vì mẫu số giảm (lượng truy cập chất lượng thấp biến mất).
- **Leading vs lagging**: doanh thu là chỉ số trễ; hoạt động tuần đầu của khách mới là chỉ số sớm dự báo giữ chân.
- **North star metric** và **cây chỉ số**: một chỉ số tổng phản ánh giá trị cho khách, được phân rã thành các nhánh mà từng đội tác động được (doanh thu = số khách × tần suất mua × giá trị đơn).
- **Định luật Goodhart**: khi một chỉ số trở thành mục tiêu, nó không còn là chỉ số tốt. Luôn đi kèm chỉ số bảo vệ.

### Funnel (phễu)
Chuỗi bước người dùng đi qua (truy cập → xem sản phẩm → thêm giỏ → thanh toán → trả tiền). Đo tỉ lệ qua mỗi bước và tỉ lệ toàn phễu.
- Cần định nghĩa: các bước phải theo **thứ tự** hay chỉ cần xảy ra? Trong **cửa sổ** thời gian bao lâu? Đơn vị là người hay phiên?
- Bước có tỉ lệ rơi lớn nhất về tuyệt đối thường là nơi đáng đầu tư, nhưng phải so với chuẩn của chính bước đó.

### Cohort và retention
**Cohort** là nhóm đơn vị cùng trải qua một sự kiện khởi đầu trong cùng giai đoạn (khách đăng ký trong tháng 1). **Phân tích cohort** theo dõi mỗi nhóm theo "tuổi" (số tháng kể từ khi đăng ký) thay vì theo lịch.
- Tách được **hiệu ứng tuổi** (khách rời dần theo thời gian) khỏi **hiệu ứng nhóm** (khách tháng 3 tốt hơn vì sản phẩm đã cải thiện) và khỏi **tăng trưởng** (tổng số người dùng tăng che giấu việc giữ chân kém).
- **Retention tháng k** = số người của cohort còn hoạt động ở tháng k / cỡ cohort.
- **Đường retention** đi ngang ở một mức > 0 nghĩa là có nhóm khách trung thành; tiến về 0 nghĩa là sản phẩm chưa giữ chân được ai.

### Phân khúc (segmentation)
- **Theo quy tắc**: kênh, vùng, thiết bị, gói dịch vụ.
- **RFM**: xếp khách theo **Recency** (mua gần đây cỡ nào), **Frequency** (mua bao nhiêu lần), **Monetary** (chi bao nhiêu), mỗi chiều chia thành điểm (thường theo quintile), ghép lại thành nhóm (khách tốt nhất, khách sắp mất, khách mới).
- **Phân cụm (clustering)**, ví dụ k-means trên các biến đã chuẩn hoá: tìm nhóm tự nhiên trong dữ liệu. Kết quả phụ thuộc biến chọn và cách chuẩn hoá; nhóm chỉ có giá trị khi diễn giải được và dẫn đến hành động khác nhau.

### Pareto và phân tích ABC
Nhiều đại lượng nghiệp vụ tập trung: một phần nhỏ khách/sản phẩm chiếm phần lớn doanh thu (thường gọi "80/20", con số thật mỗi nơi một khác). Sắp xếp giảm dần, vẽ đường **tỉ lệ luỹ kế**; nhóm A là phần tạo ra khoảng 80% đầu, B và C là phần còn lại. Dùng để ưu tiên chăm sóc khách, quản lý tồn kho.

### Phân rã thay đổi: hiệu ứng tỉ lệ và hiệu ứng cơ cấu
Một chỉ số tổng hợp (giá trị đơn trung bình, tỉ lệ chuyển đổi chung) thay đổi vì hai lý do:
- **Hiệu ứng tỉ lệ (rate effect)**: chỉ số **trong** từng nhóm thay đổi.
- **Hiệu ứng cơ cấu (mix effect)**: **tỉ trọng** các nhóm thay đổi.

Đây là cùng cơ chế với Simpson's paradox ([11-correlation-and-regression.md](11-correlation-and-regression.md)). Khi chỉ số tổng thay đổi, luôn hỏi: các nhóm thay đổi, hay cơ cấu thay đổi?

### Unit economics
- **CAC (Customer Acquisition Cost)**: chi phí thu hút / số khách mới.
- **LTV (Lifetime Value)**: tổng lợi nhuận gộp kỳ vọng từ một khách trong suốt vòng đời; thường ước lượng từ đường retention theo cohort.
- So LTV với CAC, và **thời gian hoàn vốn (payback period)**, theo từng kênh, không chỉ trung bình chung.

## Cách hoạt động

### Truy nguyên khi chỉ số đổi bất thường
```
1. Có thật không?    → lỗi dữ liệu/tracking? (xem 07: bậc thang, phiên bản, nguồn)
2. Bao giờ?          → đột ngột (sự kiện) hay dần dần (xu hướng)?
3. Tử hay mẫu?       → tách tử số, mẫu số của chỉ số tỉ lệ
4. Ở đâu?            → drill-down theo từng chiều: kênh, nền tảng, vùng, phiên bản, cohort
5. Rate hay mix?     → phân rã thay đổi thành hai phần
6. Vì sao?           → đối chiếu lịch phát hành, marketing, đối thủ, mùa vụ, sự cố
```

## Ví dụ

### Funnel
| Bước | Người | Qua bước | Từ đầu |
|---|---|---|---|
| Truy cập | 10.000 | | 100% |
| Xem sản phẩm | 6.000 | 60% | 60% |
| Thêm giỏ | 1.800 | 30% | 18% |
| Bắt đầu thanh toán | 900 | 50% | 9% |
| Trả tiền | 720 | 80% | 7,2% |

Bước xem sản phẩm → thêm giỏ mất 4.200 người, nhiều nhất về tuyệt đối. Nhưng bước thanh toán → trả tiền (mất 20%) có thể là lỗi kỹ thuật sửa rẻ hơn: xem chi tiết lý do bỏ ở từng bước.

### Cohort retention (% còn hoạt động)
| Cohort | Cỡ | Tháng 0 | Tháng 1 | Tháng 2 | Tháng 3 |
|---|---|---|---|---|---|
| 2026-01 | 1.000 | 100% | 40% | 28% | 25% |
| 2026-02 | 1.200 | 100% | 45% | 33% | |
| 2026-03 | 1.500 | 100% | 52% | | |

Đọc theo **cột** (cùng tuổi): retention tháng 1 tăng từ 40% → 45% → 52%, tức các cohort mới giữ chân tốt hơn. Đọc theo **dòng**: cohort 01 đi ngang quanh 25% từ tháng 2, có một lõi khách trung thành. Một đồ thị "tổng người dùng hoạt động" theo lịch sẽ trộn cả ba hiệu ứng lại và không thấy được điều này.

### Hiệu ứng cơ cấu
| | Tháng 1: đơn | Giá trị đơn TB | Tháng 2: đơn | Giá trị đơn TB |
|---|---|---|---|---|
| App | 1.000 | 200 | 1.500 | 200 |
| Web | 1.000 | 300 | 500 | 300 |
| **Chung** | 2.000 | **250** | 2.000 | **225** |

Giá trị đơn trung bình chung giảm 10%, nhưng **không kênh nào** giảm giá trị đơn. Toàn bộ thay đổi là hiệu ứng cơ cấu: tỉ trọng app (giá trị đơn thấp) tăng từ 50% lên 75%. Hành động đúng là hỏi vì sao cơ cấu kênh thay đổi, không phải đi tìm lý do giá trị đơn "giảm".

## Hiểu nhầm thường gặp

- **"Tổng người dùng tăng nghĩa là sản phẩm giữ chân tốt."** Thu hút mạnh có thể che retention kém. Nhìn theo cohort.
- **"Phân khúc càng nhỏ càng sâu sắc."** Phân khúc nhỏ thì nhiễu lớn và dễ dính so sánh bội ([10-hypothesis-tests.md](10-hypothesis-tests.md)). Mỗi phân khúc cần đủ cỡ và một lý do hành động.
- **"LTV trung bình > CAC trung bình nên kinh doanh tốt."** Trung bình che các kênh lỗ; và LTV ước lượng từ vài tháng đầu ngoại suy rất bất định.
- **"Chỉ số giảm thì có ai đó làm sai."** Mix effect, mùa vụ và lỗi đo lường giải thích nhiều biến động trước khi cần tìm "thủ phạm".

## Liên quan
- [04-data-wrangling.md](04-data-wrangling.md): group by, join, window để dựng funnel và cohort.
- [07-exploratory-data-analysis.md](07-exploratory-data-analysis.md): kiểm tra lỗi dữ liệu trước khi truy nguyên.
- [11-correlation-and-regression.md](11-correlation-and-regression.md): Simpson's paradox, cùng cơ chế với mix effect.
- [12-experiments-and-causality.md](12-experiments-and-causality.md): chỉ số chính và guardrail cho thí nghiệm.
- [13-time-series-analysis.md](13-time-series-analysis.md): so sánh đúng kỳ khi theo dõi chỉ số.
