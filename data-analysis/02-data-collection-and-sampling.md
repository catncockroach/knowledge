# Thu thập dữ liệu và lấy mẫu

> Ta hầu như không bao giờ quan sát toàn bộ tổng thể, chỉ một mẫu; cách mẫu được tạo ra quyết định kết luận từ mẫu có suy rộng được cho tổng thể hay không.

## Tại sao cần biết

Thống kê suy luận ([09-statistical-inference.md](09-statistical-inference.md)) trả lời được câu "sai số do ngẫu nhiên lớn cỡ nào", nhưng **không** sửa được sai số do cách thu thập. Một khảo sát 100.000 người trả lời tự nguyện có thể sai hơn một khảo sát 1.000 người chọn ngẫu nhiên. Hiểu nguồn dữ liệu là bước đầu tiên của việc đánh giá mọi con số.

## Khái niệm cốt lõi

### Tổng thể, mẫu, tham số, thống kê
- **Tổng thể (population)**: toàn bộ đối tượng ta muốn kết luận (mọi khách hàng đang hoạt động).
- **Khung mẫu (sampling frame)**: danh sách thực tế ta chọn mẫu từ đó (danh sách email trong CRM). Khung khác tổng thể thì đã có lệch trước khi chọn.
- **Mẫu (sample)**: phần được quan sát.
- **Tham số (parameter)**: con số thật của tổng thể, thường không biết (tỉ lệ thật khách hài lòng, ký hiệu p, μ).
- **Thống kê (statistic)**: con số tính trên mẫu để ước lượng tham số (p̂, x̄).

### Dữ liệu quan sát và dữ liệu thí nghiệm
- **Quan sát (observational)**: ghi lại cái đã xảy ra, không can thiệp (log, giao dịch). Rẻ, nhiều, nhưng dễ có **biến gây nhiễu (confounder)**.
- **Thí nghiệm (experimental)**: ta gán can thiệp ngẫu nhiên (A/B test). Đắt hơn nhưng cho phép kết luận nhân quả (xem [12-experiments-and-causality.md](12-experiments-and-causality.md)).

### Nguồn dữ liệu thường gặp
- **Hệ thống giao dịch**: database của ứng dụng; chính xác về nghiệp vụ nhưng thiết kế cho vận hành, không cho phân tích.
- **Event / log**: hành vi người dùng; khối lượng lớn, dễ mất sự kiện (ad blocker, mất mạng), dễ trùng.
- **Khảo sát**: đo được thái độ, ý định; chịu lệch trả lời và lệch người tham gia.
- **Dữ liệu bên thứ ba / công khai**: cần đọc kỹ định nghĩa và phương pháp của bên cung cấp.

### Các phương pháp lấy mẫu xác suất
Mỗi đơn vị có xác suất được chọn biết trước và khác 0:
- **Ngẫu nhiên đơn giản (simple random)**: mọi tập con cùng cỡ có xác suất như nhau.
- **Phân tầng (stratified)**: chia tổng thể thành các tầng (miền Bắc/Trung/Nam), lấy ngẫu nhiên trong từng tầng. Đảm bảo nhóm nhỏ có đủ đại diện và thường giảm sai số.
- **Cụm (cluster)**: chọn ngẫu nhiên vài cụm (vài cửa hàng) rồi lấy hết hoặc lấy mẫu trong cụm. Rẻ khi đi thực địa nhưng sai số lớn hơn nếu các cụm khác nhau nhiều.
- **Hệ thống (systematic)**: lấy mỗi đơn vị thứ k trong danh sách. Nguy hiểm nếu danh sách có chu kỳ trùng k.

Lấy mẫu **phi xác suất** (tiện lợi, tự nguyện, quả cầu tuyết) nhanh và rẻ, nhưng không có cơ sở để tính sai số suy rộng.

## Cách hoạt động

### Sai số = ngẫu nhiên + hệ thống

```
Ước lượng − Giá trị thật = Sai số ngẫu nhiên (sampling error) + Lệch (bias)
                            └ giảm khi mẫu lớn hơn            └ KHÔNG giảm khi mẫu lớn hơn
```

Tăng cỡ mẫu chỉ thu hẹp phần ngẫu nhiên (tỉ lệ với 1/√n, xem [09-statistical-inference.md](09-statistical-inference.md)). Lệch chỉ sửa được bằng thiết kế thu thập tốt hơn hoặc hiệu chỉnh (gán trọng số).

### Các loại lệch quan trọng
- **Lệch chọn mẫu (selection bias)**: cơ chế đưa đơn vị vào dữ liệu có liên quan đến biến cần đo. Khảo sát hài lòng chỉ gửi cho khách còn hoạt động thì bỏ sót người đã rời đi.
- **Lệch sống sót (survivorship bias)**: chỉ thấy đối tượng "sống sót" qua một bộ lọc. Phân tích "đặc điểm của startup thành công" mà không nhìn startup thất bại.
- **Lệch không phản hồi (non-response bias)**: người trả lời khác người không trả lời. Người rất hài lòng hoặc rất bực mình hay trả lời hơn.
- **Lệch đo lường (measurement bias)**: công cụ đo sai có hệ thống: câu hỏi dẫn dắt, cảm biến lệch, tracking chỉ chạy trên một số trình duyệt.
- **Lệch tự chọn (self-selection)**: đối tượng tự quyết định có tham gia "can thiệp" không. Khách dùng tính năng mới thường là khách tích cực sẵn, nên so họ với người không dùng sẽ phóng đại hiệu quả tính năng.

### Cỡ mẫu cần bao nhiêu
Với một tỉ lệ, sai số biên ở độ tin cậy 95% xấp xỉ 1,96·√(p(1−p)/n). Trường hợp xấu nhất p = 0,5:
- n = 400 → sai số ≈ ±4,9 điểm phần trăm.
- n = 1.000 → ≈ ±3,1 điểm.
- n = 10.000 → ≈ ±1,0 điểm.

Muốn sai số giảm một nửa phải tăng mẫu gấp bốn. Đáng chú ý: khi tổng thể lớn hơn mẫu nhiều, sai số **gần như không phụ thuộc cỡ tổng thể**. 1.000 người chọn ngẫu nhiên cho độ chính xác gần như nhau dù tổng thể là 100.000 hay 100 triệu.

## Ví dụ

Một ứng dụng muốn biết tỉ lệ người dùng sẵn sàng trả phí:
- **Cách A:** popup trong app, 20.000 người trả lời, 38% nói có.
- **Cách B:** chọn ngẫu nhiên 1.000 tài khoản từ toàn bộ người dùng đăng ký, liên hệ và theo đuổi đến khi 800 người trả lời, 21% nói có.

Cách A có sai số ngẫu nhiên nhỏ (±0,7 điểm) nhưng chỉ chạm người đang mở app, tức người dùng tích cực, và người tự nguyện bấm trả lời. Cách B có sai số ngẫu nhiên lớn hơn (±2,8 điểm) nhưng khung mẫu đúng tổng thể và tỉ lệ phản hồi cao. Con số đáng tin hơn để lập kế hoạch doanh thu là của cách B, và chênh lệch 38% với 21% chính là độ lớn của lệch chọn mẫu.

## Hiểu nhầm thường gặp

- **"Big data không cần lấy mẫu, nên không có lệch."** Dữ liệu log là "toàn bộ người đã dùng sản phẩm", không phải toàn bộ khách tiềm năng. Lệch nằm ở khung, không ở cỡ.
- **"Mẫu phải chiếm vài phần trăm tổng thể mới đại diện."** Độ chính xác phụ thuộc vào n tuyệt đối và cách chọn, không phải tỉ lệ n/N (trừ khi n chiếm phần lớn N).
- **"Ngẫu nhiên nghĩa là tùy tiện."** Ngẫu nhiên trong thống kê là có quy trình xác suất rõ ràng (sinh số ngẫu nhiên), không phải "chọn ai cũng được".

## Liên quan
- [01-data-fundamentals.md](01-data-fundamentals.md): đơn vị quan sát và tổng thể là gì.
- [03-data-cleaning.md](03-data-cleaning.md): giá trị thiếu cũng là một dạng lệch chọn mẫu.
- [09-statistical-inference.md](09-statistical-inference.md): tính sai số ngẫu nhiên và khoảng tin cậy.
- [12-experiments-and-causality.md](12-experiments-and-causality.md): ngẫu nhiên hoá để loại confounder.
