# Phân tích khám phá (EDA)

> EDA là giai đoạn nhìn vào dữ liệu một cách có hệ thống, bằng thống kê mô tả và đồ thị, để hiểu cấu trúc, phát hiện lỗi và hình thành giả thuyết, trước khi kiểm định hay mô hình hoá.

## Tại sao cần biết

Tukey (1977) tách phân tích dữ liệu thành hai việc: **khám phá** (exploratory) để tìm xem dữ liệu nói gì, và **xác nhận** (confirmatory) để kiểm tra một giả thuyết đã nêu. Bỏ qua khám phá thì kiểm định chạy trên dữ liệu chưa hiểu: không biết có ngoại lai, có nhóm trộn lẫn, có lỗi tracking. Ngược lại, nếu dùng chính dữ liệu khám phá để "xác nhận" giả thuyết vừa tìm ra từ nó thì kết quả tự nhiên trông có ý nghĩa: đó là **lỗi dùng dữ liệu hai lần**. EDA nằm giữa làm sạch ([03-data-cleaning.md](03-data-cleaning.md)) và suy luận ([09-statistical-inference.md](09-statistical-inference.md)).

## Khái niệm cốt lõi

- **Univariate**: xem từng biến riêng lẻ (phân bố, thiếu, ngoại lai).
- **Bivariate**: quan hệ giữa hai biến, đặc biệt giữa mỗi biến và biến mục tiêu (outcome).
- **Multivariate**: quan hệ có điều kiện: quan hệ X–Y có giữ nguyên khi tách theo nhóm Z không.
- **Giả thuyết (hypothesis)**: đầu ra của EDA không phải kết luận, mà là danh sách giả thuyết đáng kiểm tra và các vấn đề dữ liệu cần sửa.
- **Sanity check**: so con số với một nguồn đã biết (tổng doanh thu khớp báo cáo tài chính?) để phát hiện lỗi pipeline.

## Cách hoạt động

### Danh sách việc khi gặp một bộ dữ liệu mới

```
1. Hình dạng      số dòng, số cột, grain, khoá có duy nhất không
2. Từng cột       kiểu, % thiếu, số giá trị khác nhau, min/max, top giá trị
3. Phân bố        histogram/boxplot cho biến số; bar tần số cho biến định tính
4. Thời gian      vẽ số dòng theo ngày: có khoảng trống, bậc thang, đột biến?
5. Quan hệ        scatter/boxplot từng biến theo biến mục tiêu; ma trận tương quan
6. Phân nhóm      lặp lại bước 3–5 theo các nhóm quan trọng (kênh, vùng, thiết bị)
7. Đối chiếu      so tổng/đếm với nguồn tham chiếu
8. Ghi chép       vấn đề dữ liệu + giả thuyết + câu hỏi cho người nắm nghiệp vụ
```

### Các tín hiệu đáng ngờ
- **Bậc thang trên đồ thị theo thời gian**: số sự kiện nhảy lên/xuống đột ngột một ngày → thường là thay đổi tracking hoặc pipeline, không phải hành vi người dùng.
- **Giá trị "tròn" quá nhiều**: tuổi = 30, ngày sinh 01-01 → giá trị mặc định hoặc điền ẩu.
- **Đỉnh ở một giá trị cụ thể**: thời gian phiên đúng 30 phút → timeout của hệ thống.
- **Tương quan gần 1 giữa biến đầu vào và kết quả**: có thể là **rò rỉ dữ liệu (data leakage)**, tức biến được tính *sau* hoặc *từ* kết quả.
- **Phân bố đa đỉnh**: nhiều quần thể trộn lẫn, cần tách.

### Tránh tự lừa mình
- **Tách dữ liệu**: dùng một phần (hoặc một khoảng thời gian) để khám phá, phần còn lại để xác nhận giả thuyết.
- **Ghi lại số lần thử**: đã xem 40 phân nhóm rồi tìm ra 2 nhóm "khác biệt có ý nghĩa" thì đó là kết quả kỳ vọng do ngẫu nhiên (vấn đề so sánh bội, xem [10-hypothesis-tests.md](10-hypothesis-tests.md)).
- **Phân biệt "thấy" và "biết"**: viết kết quả EDA dưới dạng "gợi ý rằng…", "cần kiểm tra…".

## Ví dụ

Dữ liệu: 6 tháng đơn hàng của một shop, câu hỏi mở "vì sao doanh thu tháng 5 giảm?".

1. **Theo ngày**: số đơn giảm đột ngột từ ngày 12/5 và giữ ở mức thấp. Không phải giảm dần → nghi một sự kiện cụ thể.
2. **Phân nhóm theo kênh**: web và store không đổi; chỉ app giảm, và giảm gần 100% trên Android.
3. **Phân nhóm theo phiên bản app**: đơn từ phiên bản phát hành ngày 12/5 gần như bằng 0.
4. **Đối chiếu**: hệ thống thanh toán vẫn ghi nhận giao dịch Android bình thường → đơn hàng vẫn có, chỉ **sự kiện tracking** bị mất ở phiên bản mới.

Kết luận của EDA: "doanh thu giảm" là lỗi đo lường, không phải hành vi khách. Không cần kiểm định nào; nhưng nếu bỏ qua EDA và chạy thẳng một mô hình dự báo, mô hình sẽ học một "xu hướng giảm" không có thật.

## Hiểu nhầm thường gặp

- **"EDA là vẽ thật nhiều đồ thị đẹp."** EDA là đặt câu hỏi và kiểm tra. Đồ thị nhanh, xấu nhưng trả lời được câu hỏi giá trị hơn dashboard đẹp.
- **"Thấy khác biệt trong EDA là đã có phát hiện."** Khác biệt tìm được khi lục lọi nhiều phân nhóm cần được xác nhận trên dữ liệu mới hoặc bằng thí nghiệm.
- **"EDA chỉ làm một lần ở đầu dự án."** Mỗi khi kết quả bất ngờ, quay lại EDA trên phần dữ liệu liên quan.

## Liên quan
- [03-data-cleaning.md](03-data-cleaning.md): EDA phát hiện vấn đề, làm sạch xử lý chúng.
- [05-descriptive-statistics.md](05-descriptive-statistics.md) và [06-data-visualization.md](06-data-visualization.md): bộ công cụ chính của EDA.
- [10-hypothesis-tests.md](10-hypothesis-tests.md): kiểm định giả thuyết mà EDA đưa ra, và vấn đề so sánh bội.
- [11-correlation-and-regression.md](11-correlation-and-regression.md): Simpson's paradox khi phân tích có điều kiện.
