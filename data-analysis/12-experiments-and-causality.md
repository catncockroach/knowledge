# Thí nghiệm, A/B test và suy luận nhân quả

> Muốn biết "làm X thì Y đổi bao nhiêu" phải so sánh với cái sẽ xảy ra nếu không làm X; thí nghiệm ngẫu nhiên tạo ra phép so sánh đó một cách sạch nhất, còn với dữ liệu quan sát thì cần thiết kế và giả định để tiến gần tới nó.

## Tại sao cần biết

Các quyết định đáng giá nhất đều là câu hỏi nhân quả: đổi giá có tăng doanh thu không, tính năng mới có giữ chân khách không. Dữ liệu quan sát đầy confounder ([11-correlation-and-regression.md](11-correlation-and-regression.md)): khách dùng tính năng mới vốn đã tích cực hơn. A/B test là công cụ chuẩn của sản phẩm số, nhưng nó có nhiều cách hỏng khó thấy: dừng sớm khi thấy kết quả đẹp, phân chia lệch, đo quá nhiều chỉ số.

## Khái niệm cốt lõi

### Khung kết quả tiềm năng (potential outcomes)
Mỗi đơn vị i có hai kết quả tiềm năng: Yᵢ(1) nếu được can thiệp, Yᵢ(0) nếu không. Tác động với đơn vị đó là Yᵢ(1) − Yᵢ(0), nhưng ta **chỉ quan sát được một trong hai**: đó là "vấn đề cơ bản của suy luận nhân quả".
- **ATE (Average Treatment Effect)**: E[Y(1) − Y(0)] trên toàn tổng thể.
- So sánh ngây thơ (người dùng tính năng vs không dùng) = ATE + **lệch chọn**, vì hai nhóm khác nhau ngay cả khi không có can thiệp.

### Vì sao ngẫu nhiên hoá hoạt động
Gán can thiệp bằng tung đồng xu thì việc được can thiệp **độc lập** với mọi đặc điểm của đơn vị, cả đặc điểm đo được lẫn không đo được. Trung bình, hai nhóm giống nhau ở mọi mặt trừ can thiệp, nên chênh lệch kết quả là ước lượng không lệch của ATE.

### Thành phần của một A/B test
- **Đơn vị ngẫu nhiên hoá**: người dùng, phiên, cửa hàng. Phải khớp với đơn vị phân tích, và tránh "nhiễm chéo" (một người thấy cả A và B).
- **Chỉ số chính (primary metric)**: một chỉ số chọn trước, gắn với mục tiêu (tỉ lệ chuyển đổi, doanh thu/người).
- **Chỉ số bảo vệ (guardrail metrics)**: những thứ không được xấu đi (tốc độ tải, tỉ lệ hoàn tiền, khiếu nại).
- **MDE (Minimum Detectable Effect)**: hiệu ứng nhỏ nhất đáng phát hiện, quyết định cỡ mẫu.
- **Thời lượng**: đủ cỡ mẫu và phủ trọn chu kỳ tuần (hành vi thứ Hai khác Chủ nhật).

### Tính cỡ mẫu
Với hai tỉ lệ p₁ (đối chứng) và p₂ (kỳ vọng), α = 0,05 hai phía, power 80%:

n mỗi nhóm ≈ (z₀,₉₇₅ + z₀,₈)² · [p₁(1 − p₁) + p₂(1 − p₂)] / (p₂ − p₁)², với z₀,₉₇₅ ≈ 1,96 và z₀,₈ ≈ 0,84.

Cỡ mẫu tỉ lệ nghịch với **bình phương** MDE: muốn phát hiện hiệu ứng nhỏ bằng một nửa thì cần mẫu gấp bốn.

## Cách hoạt động

### Quy trình

```
1. Giả thuyết + chỉ số chính + guardrail + MDE   (viết ra TRƯỚC)
2. Tính cỡ mẫu và thời lượng
3. Kiểm tra A/A hoặc kiểm tra hạ tầng chia nhóm
4. Chạy; theo dõi SRM và guardrail, KHÔNG quyết định theo p-value giữa chừng
5. Đến đủ cỡ mẫu → phân tích chỉ số chính (CI của hiệu số)
6. Phân nhóm, chỉ số phụ → coi là khám phá
7. Quyết định + ghi lại (cả thử nghiệm thất bại)
```

### Các lỗi phổ biến
- **Peeking (nhìn trộm)**: xem p-value hằng ngày và dừng khi p < 0,05 làm tỉ lệ dương tính giả tăng xa hơn 5% nhiều. Hoặc cố định cỡ mẫu trước, hoặc dùng phương pháp thiết kế cho theo dõi liên tục (sequential testing, always-valid p-values).
- **Sample Ratio Mismatch (SRM)**: thiết kế chia 50/50 mà thực tế ra 50,8/49,2 trên mẫu lớn là dấu hiệu lỗi (bot bị lọc khác nhau, redirect làm mất người dùng một nhánh). Kiểm định chi-square tỉ lệ chia; nếu có SRM thì không tin kết quả.
- **Hiệu ứng mới lạ (novelty effect)**: người dùng tò mò bấm thử giao diện mới vài ngày đầu. Xem hiệu ứng theo thời gian.
- **Nhiễu chéo giữa đơn vị (interference)**: trong chợ hai phía (người mua/người bán, tài xế/khách), can thiệp lên nhóm B lấy bớt nguồn cung của nhóm A. Cần ngẫu nhiên hoá theo cụm (vùng, thời gian).
- **So sánh bội**: 20 chỉ số × 5 phân nhóm = 100 kiểm định ([10-hypothesis-tests.md](10-hypothesis-tests.md)).

### Khi không thể thí nghiệm: suy luận nhân quả từ dữ liệu quan sát
- **Kiểm soát bằng hồi quy / matching / propensity score**: so sánh các đơn vị giống nhau ở những biến confounder **đã đo**. Giả định mạnh: không còn confounder nào chưa đo.
- **Difference-in-differences (DiD)**: so sánh *thay đổi* trước–sau của nhóm bị tác động với *thay đổi* của nhóm không bị tác động. Giả định: nếu không có can thiệp, hai nhóm sẽ đi song song (parallel trends).
- **Regression discontinuity**: can thiệp được gán theo ngưỡng (điểm ≥ 700 được duyệt vay); so sánh người ngay trên và ngay dưới ngưỡng.
- **Instrumental variables**: dùng một biến chỉ ảnh hưởng tới Y thông qua X.
- **Sơ đồ nhân quả (DAG)**: vẽ giả định về quan hệ nhân quả giữa các biến, từ đó biết phải kiểm soát biến nào (confounder) và **không** được kiểm soát biến nào (mediator, collider).

```
         Mùa vụ (confounder)
          ↙          ↘
  Quảng cáo ─────────► Doanh thu        kiểm soát Mùa vụ: đúng
          ↘          ↗
       Lượt truy cập (mediator)          kiểm soát Lượt truy cập: xoá mất tác động cần đo
```

## Ví dụ

**Thiết kế**: tỉ lệ chuyển đổi hiện tại 5%, muốn phát hiện mức tăng lên 6% (MDE +1 điểm, +20% tương đối).
n mỗi nhóm ≈ (1,96 + 0,84)² × (0,05 × 0,95 + 0,06 × 0,94) / 0,01² ≈ **8.155** người. Nếu mỗi ngày có 1.200 người vào trang, chia đôi mỗi nhánh 600/ngày → khoảng 14 ngày, tròn 2 tuần, phủ đủ chu kỳ tuần.

**Phân tích** (giả sử dừng sớm hơn, mỗi nhóm 10.000 người): A có 500 chuyển đổi (5,0%), B có 560 (5,6%).
- Tỉ lệ gộp 5,3%; SE của hiệu số ≈ √(0,053 × 0,947 × (1/10.000 + 1/10.000)) ≈ 0,0032.
- z ≈ 0,006 / 0,0032 ≈ **1,89**, p ≈ **0,058**.
- CI 95% của hiệu số ≈ 0,6 ± 0,62 điểm, tức khoảng [−0,02; +1,22] điểm.

Đọc đúng: dữ liệu phù hợp với cả "không có hiệu ứng" lẫn "tăng hơn 1 điểm". Không kết luận "B không tác dụng", cũng không triển khai vì "gần có ý nghĩa". Hoặc chạy tiếp tới cỡ mẫu đã định trước, hoặc quyết định dựa trên chi phí của việc sai mỗi chiều.

## Hiểu nhầm thường gặp

- **"A/B test cho biết tác động với từng người."** Nó cho tác động **trung bình**. Phân tích theo phân nhóm (heterogeneous effects) cần cỡ mẫu lớn hơn nhiều và dễ dính so sánh bội.
- **"Chạy đến khi có ý nghĩa thống kê."** Đây chính là peeking: với đủ thời gian, gần như chắc chắn sẽ có lúc p < 0,05 dù không có hiệu ứng.
- **"Kiểm soát đủ biến thì dữ liệu quan sát tương đương thí nghiệm."** Chỉ khi không còn confounder nào chưa đo, điều không bao giờ kiểm chứng được từ dữ liệu.
- **"Không có ý nghĩa thống kê = thất bại."** Một thử nghiệm có power đủ mà không thấy hiệu ứng là thông tin có giá trị: nó loại bỏ một ý tưởng tốn kém.

## Liên quan
- [09-statistical-inference.md](09-statistical-inference.md): power, MDE, khoảng tin cậy.
- [10-hypothesis-tests.md](10-hypothesis-tests.md): z-test tỉ lệ, chi-square cho SRM, so sánh bội.
- [11-correlation-and-regression.md](11-correlation-and-regression.md): confounder và Simpson's paradox.
- [14-analytical-techniques.md](14-analytical-techniques.md): funnel và cohort là nơi chọn chỉ số cho thí nghiệm.
