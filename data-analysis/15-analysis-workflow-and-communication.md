# Quy trình phân tích và truyền đạt kết quả

> Một phân tích chỉ có giá trị khi trả lời đúng câu hỏi, tái lập được, và được trình bày để người ra quyết định hiểu và hành động; file này ghép các kỹ thuật ở các file trước thành một quy trình làm việc hoàn chỉnh.

## Tại sao cần biết

Phân tích đúng kỹ thuật vẫn có thể vô ích: trả lời một câu hỏi không ai hỏi, ra con số không ai tái lập được khi số liệu thay đổi, hay một slide 20 đồ thị mà người đọc không biết phải làm gì. Phần lớn giá trị nằm ở hai đầu: **đặt câu hỏi** và **truyền đạt**. Phần giữa ([03-data-cleaning.md](03-data-cleaning.md) đến [14-analytical-techniques.md](14-analytical-techniques.md)) là kỹ thuật.

## Khái niệm cốt lõi

### Đặt câu hỏi đúng
- Bắt đầu từ **quyết định**: "Câu trả lời này sẽ làm ai thay đổi việc gì?" Nếu không có quyết định nào phụ thuộc vào nó, cân nhắc không làm.
- Chuyển yêu cầu mơ hồ thành câu hỏi đo được: "khách có thích tính năng mới không" → "người dùng tính năng X có retention tuần 4 khác người không dùng bao nhiêu, sau khi tính đến mức hoạt động ban đầu".
- Xác định **loại câu hỏi** (mô tả, suy luận, nhân quả, dự đoán, xem [01-data-fundamentals.md](01-data-fundamentals.md)), vì nó quyết định phương pháp và mức độ chắc chắn có thể đạt.
- Viết ra **giả thuyết** và **kết quả nào sẽ thay đổi quyết định** trước khi xem dữ liệu, để tránh tìm lý do hợp lý hoá sau.

### Tái lập (reproducibility)
- **Mọi bước bằng code**: truy vấn, làm sạch, biến đổi, đồ thị. Không sửa tay trong bảng tính rồi quên.
- **Quản lý phiên bản** code phân tích như code phần mềm.
- **Ghi lại phiên bản dữ liệu**: ngày trích, bộ lọc, nguồn. Dữ liệu nguồn thay đổi thì kết quả thay đổi; phải biết vì sao.
- **Notebook** tiện để khám phá nhưng dễ chạy các ô lệch thứ tự; trước khi chia sẻ, chạy lại từ đầu đến cuối.
- **Kiểm tra dữ liệu tự động**: khoá duy nhất, không NULL ở cột bắt buộc, tổng khớp nguồn tham chiếu.

### Bộ công cụ (theo vai trò, không theo sản phẩm)
| Vai trò | Công cụ điển hình |
|---|---|
| Truy vấn, gộp dữ liệu lớn | SQL trên database/data warehouse |
| Phân tích linh hoạt, thống kê, mô hình | Python (pandas, thư viện thống kê), R |
| Khám phá nhanh, mô hình nhỏ, chia sẻ với người không lập trình | Bảng tính |
| Theo dõi chỉ số định kỳ | Công cụ BI / dashboard |
| Tái lập, cộng tác | Git, notebook, môi trường được khai báo |

Nguyên tắc: đẩy việc gộp nặng xuống SQL gần dữ liệu; kéo kết quả đã gộp lên Python/R cho thống kê và đồ thị.

### Truyền đạt
- **Kết luận trước** (nguyên tắc kim tự tháp): câu đầu tiên là câu trả lời và khuyến nghị, sau đó mới là bằng chứng, cuối cùng là phương pháp.
- **"So what"**: mỗi con số đi kèm ý nghĩa của nó. "Retention tuần 4 tăng 3 điểm" → "tương đương khoảng 1.200 khách giữ lại thêm mỗi tháng".
- **Nói rõ độ chắc chắn**: khoảng tin cậy hoặc khoảng dự báo, những gì phân tích *không* chứng minh được (tương quan hay nhân quả), giả định quan trọng.
- **Một đồ thị, một thông điệp** ([06-data-visualization.md](06-data-visualization.md)); tiêu đề đồ thị là kết luận.
- **Theo người đọc**: lãnh đạo cần quyết định và rủi ro; đội kỹ thuật cần phương pháp và giới hạn; đưa chi tiết vào phụ lục.

## Cách hoạt động

### Quy trình đầu–cuối

```
Câu hỏi & quyết định ─► Giả thuyết + tiêu chí ─► Dữ liệu: nguồn, grain, lệch (01, 02)
                                                        │
  ┌─────────────────────────────────────────────────────┘
  ▼
Làm sạch (03) ─► Biến đổi (04) ─► EDA (05–07) ─► Suy luận / mô hình (08–13)
                                                        │
  ┌─────────────────────────────────────────────────────┘
  ▼
Kiểm tra độ vững: đổi giả định, đổi khoảng thời gian, đổi định nghĩa → kết luận có giữ?
  ▼
Truyền đạt: kết luận → bằng chứng → giới hạn → khuyến nghị ─► Quyết định ─► (đo lại)
```

### Danh sách kiểm tra trước khi gửi kết quả
- [ ] Con số tổng khớp một nguồn tham chiếu độc lập.
- [ ] Grain và mẫu số đúng; join không nhân dòng.
- [ ] Đã xem phân bố, không chỉ trung bình; đã xem có ngoại lai chi phối không.
- [ ] Đã kiểm tra Simpson / mix effect theo các chiều quan trọng.
- [ ] Đã phân biệt khám phá và xác nhận; đã tính đến so sánh bội.
- [ ] Đã nêu rõ tương quan hay nhân quả, và vì sao.
- [ ] Có độ bất định (CI) cho các con số chính.
- [ ] Người khác chạy lại được từ code.
- [ ] Câu đầu tiên trả lời câu hỏi ban đầu.

### Đạo đức và quyền riêng tư
- Chỉ dùng dữ liệu cá nhân trong phạm vi được phép; tổng hợp hoặc ẩn danh hoá khi chia sẻ.
- Nhóm nhỏ có thể làm lộ danh tính dù đã bỏ tên (một khách hàng duy nhất ở một quận).
- Cẩn trọng khi phân tích theo thuộc tính nhạy cảm; kết quả có thể bị dùng để phân biệt đối xử.

## Ví dụ

Một bản tóm tắt phân tích tốt, gửi cho trưởng sản phẩm:

> **Nên giữ trang thanh toán mới.** Thí nghiệm 2 tuần, mỗi nhóm khoảng 8.200 người, tỉ lệ trả tiền tăng từ 5,0% lên 5,9% (+0,9 điểm, CI 95%: +0,2 đến +1,6). Với lưu lượng hiện tại, mức tăng tương đương khoảng 300 đơn mỗi tháng. Không chỉ số bảo vệ nào xấu đi (thời gian tải, tỉ lệ hoàn tiền). Giới hạn: hiệu ứng mạnh hơn trên mobile nhưng phân nhóm này chưa đủ mẫu để chắc chắn; đề xuất theo dõi tiếp 4 tuần sau khi triển khai. Chi tiết phương pháp ở phụ lục.

Đoạn này có câu trả lời ở câu đầu, cỡ hiệu ứng kèm độ bất định, quy đổi sang tác động nghiệp vụ, kiểm tra guardrail, nêu giới hạn và bước tiếp theo. Không có con số nào thiếu đơn vị hay thiếu mẫu số.

## Hiểu nhầm thường gặp

- **"Phân tích càng nhiều đồ thị càng thuyết phục."** Nhiều đồ thị làm loãng thông điệp; người đọc phải tự tìm kết luận.
- **"Nêu giới hạn làm kết quả yếu đi."** Nêu giới hạn làm kết quả đáng tin hơn, và bảo vệ người ra quyết định khỏi tin quá mức.
- **"Dashboard thay thế phân tích."** Dashboard trả lời "cái gì"; câu hỏi "vì sao" và "nên làm gì" vẫn cần phân tích có chủ đích.
- **"Kết quả không như mong đợi thì phân tích hỏng."** Kết quả bất ngờ cần kiểm tra kỹ hơn, nhưng không phải bị loại bỏ. Chỉ báo cáo kết quả "đẹp" là lệch công bố (publication bias) ở quy mô tổ chức.

## Liên quan
- [01-data-fundamentals.md](01-data-fundamentals.md): loại câu hỏi và vòng đời phân tích.
- [06-data-visualization.md](06-data-visualization.md): đồ thị giải thích.
- [07-exploratory-data-analysis.md](07-exploratory-data-analysis.md): tách khám phá và xác nhận.
- [12-experiments-and-causality.md](12-experiments-and-causality.md): khi nào được nói "gây ra".
- [14-analytical-techniques.md](14-analytical-techniques.md): các khung câu hỏi nghiệp vụ.
