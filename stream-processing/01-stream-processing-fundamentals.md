# Nền tảng stream processing

> Stream processing là xử lý dữ liệu *ngay khi nó đến*, trên một dòng sự kiện không có điểm kết thúc. Batch processing thì khác: nó gom dữ liệu thành khối hữu hạn rồi mới chạy. Mọi khó khăn của stream processing đến từ ba điều: dữ liệu không bao giờ "đủ", thứ tự đến không trùng thứ tự xảy ra, và chương trình phải chạy liên tục qua lỗi, restart và thay đổi quy mô.

## Tại sao cần biết
Một engine xử lý dữ liệu realtime (đếm, cảnh báo, đồng bộ, làm giàu dữ liệu) chịu cùng một nhóm câu hỏi bất kể nghiệp vụ là gì:
- Đã xử lý tới đâu, và nếu crash thì làm lại từ đâu?
- Message có bị mất hay bị xử lý hai lần không?
- Message đến lệch thứ tự thì sao?
- "Mỗi phút" là phút theo đồng hồ máy chủ hay theo lúc sự việc xảy ra?
- Khi tải tăng gấp mười thì làm gì?

File này đặt nền về từ vựng và mô hình tư duy để các file sau đi sâu vào từng câu. Domain này dùng Apache Kafka làm nền tảng log (xem [02-kafka-log-model.md](02-kafka-log-model.md)), nhưng các khái niệm như event-time, window, state, delivery semantics là chung cho mọi hệ stream.

## Khái niệm cốt lõi

### Event (sự kiện)
- **Là gì**: một bản ghi bất biến mô tả *một việc đã xảy ra* tại một thời điểm, ví dụ "user 42 bấm nút mua lúc 10:00:58". Event thường có khoá (ai/cái gì), giá trị (chi tiết) và thời điểm xảy ra.
- **Dùng để**: làm đơn vị dữ liệu nhỏ nhất mà hệ thống truyền, lưu và xử lý. Event đã xảy ra thì không sửa được; muốn "sửa" thì phát một event mới.

### Stream (dòng sự kiện)
- **Là gì**: chuỗi event có thứ tự, kéo dài vô hạn (unbounded), luôn có event mới được nối vào cuối.
- **Dùng để**: mô hình hoá dữ liệu sinh ra liên tục: click, giao dịch, log, số đo cảm biến, thay đổi trong database (CDC, change data capture).

### Bounded và unbounded data
- **Là gì**: *bounded* là tập dữ liệu hữu hạn, biết điểm kết thúc (file log của hôm qua). *Unbounded* là tập dữ liệu không có điểm kết thúc (log đang được ghi).
- **Dùng để**: phân biệt bài toán. Với bounded data, chương trình đọc hết rồi trả kết quả đúng một lần. Với unbounded data, chương trình chỉ trả được kết quả *tạm thời* tại từng thời điểm, hoặc kết quả cho từng khoảng thời gian (window, xem [10-time-and-windows.md](10-time-and-windows.md)).

### Batch processing và stream processing
- **Batch processing**
  - **Là gì**: chạy định kỳ trên một khối dữ liệu đã gom, ví dụ mỗi đêm tính doanh thu của ngày hôm trước.
  - **Dùng để**: các bài toán chấp nhận độ trễ hàng giờ, cần nhìn toàn bộ dữ liệu một lần, và muốn kết quả tất định, dễ chạy lại.
- **Stream processing**
  - **Là gì**: một chương trình chạy liên tục, xử lý từng event (hoặc từng nhóm nhỏ) ngay khi nó đến.
  - **Dùng để**: các bài toán cần kết quả trong vài mili-giây đến vài giây: cảnh báo gian lận, cập nhật tồn kho, dashboard realtime, đồng bộ dữ liệu giữa các hệ thống.
- **Micro-batch**: dạng lai, gom event trong một khoảng ngắn (vài trăm mili-giây đến vài giây) rồi xử lý như một batch nhỏ. Hầu hết consumer Kafka thực ra chạy kiểu này, vì mỗi lần đọc nhận về một nhóm record.

### Latency và throughput
- **Latency (độ trễ)**
  - **Là gì**: thời gian từ lúc event xảy ra (hoặc được ghi vào log) tới lúc kết quả xử lý có hiệu lực ở nơi đích.
  - **Dùng để**: đo độ "realtime" của hệ thống.
- **Throughput (thông lượng)**
  - **Là gì**: số event, hoặc số byte, xử lý được trong một giây.
  - **Dùng để**: đo năng lực của hệ thống.
- Hai đại lượng này kéo nhau. Gom nhiều event vào một lần đọc hoặc ghi (batching) làm throughput tăng, vì chi phí cố định của mỗi lần gọi mạng hay ghi đĩa được chia cho nhiều event. Đổi lại, latency tăng, vì event phải chờ cho đủ batch.

### Producer, broker, consumer
- **Producer**: chương trình ghi event vào log. **Dùng để** đưa dữ liệu từ nguồn (ứng dụng, database, thiết bị) vào hệ thống stream.
- **Broker / event log**: hệ thống lưu event bền vững theo thứ tự, cho nhiều bên đọc độc lập (Kafka, Redpanda, Pulsar...). **Dùng để** tách bên ghi khỏi bên đọc: producer không cần biết ai đọc, consumer đọc theo tốc độ của mình.
- **Consumer**: chương trình đọc event từ log và xử lý. **Dùng để** biến dòng event thành kết quả: ghi DB, phát event mới, gửi cảnh báo. "Engine consumer" trong domain này là một consumer được thiết kế để chạy liên tục, chịu lỗi và scale được.

### Sink và source
- **Source**: nơi engine đọc dữ liệu vào, ở đây là topic Kafka.
- **Sink**: nơi engine ghi kết quả ra: database, một topic khác, API, object storage.
- **Dùng để**: hai khái niệm này giúp nói rõ đảm bảo đúng-sai *giữa hai đầu*. Phần lớn rủi ro mất hoặc trùng dữ liệu nằm ở sink, không nằm ở Kafka (xem [05-delivery-semantics.md](05-delivery-semantics.md)).

### Stateless và stateful processing
- **Stateless**
  - **Là gì**: kết quả xử lý một event chỉ phụ thuộc vào chính event đó: lọc, đổi định dạng, làm giàu từ một bảng tra tĩnh.
  - **Dùng để**: các bước dễ song song hoá và dễ phục hồi, vì không có gì phải nhớ.
- **Stateful**
  - **Là gì**: kết quả phụ thuộc vào các event trước đó: đếm, tổng, dedupe, phát hiện chuỗi hành vi, join hai stream.
  - **Dùng để**: mọi câu hỏi có dạng "bao nhiêu", "đã thấy chưa", "trong khoảng thời gian nào". Cái giá là engine phải lưu, sao lưu và phục hồi state (xem [11-state-and-joins.md](11-state-and-joins.md)).

### Stream-table duality
- **Là gì**: một stream có thể coi là nhật ký thay đổi của một bảng, và một bảng có thể coi là ảnh chụp trạng thái mới nhất của stream. Phát lại stream "số dư thay đổi" từ đầu sẽ được bảng "số dư hiện tại". Ngược lại, ghi mọi thay đổi của bảng ra sẽ được một stream.
- **Dùng để**: hiểu vì sao Kafka dùng được làm nơi sao lưu state (changelog topic), vì sao CDC biến database thành stream, và vì sao "replay log" là cách dựng lại bất kỳ trạng thái nào.

## Cách hoạt động

Một engine stream chạy theo vòng lặp vô hạn. Mọi phần của domain này là chi tiết của các bước trong vòng lặp đó:

```
        ┌──────────────────────────────────────────────────────────────┐
        │                                                              │
        ▼                                                              │
  [1] đọc một nhóm event từ log  ─► [2] giải mã ─► [3] xử lý (± state) ─► [4] ghi sink
        ▲                                                              │
        │                                                              ▼
        └──────────── [5] ghi nhận "đã xử lý tới đâu" (commit) ◄───────┘

  Cắt ngang mọi bước: lỗi và retry (07) · song song (08) · tốc độ (09) · thời gian (10)
                      quan sát và vận hành (13)
```

Bước [5] là điểm then chốt. Log không xoá event sau khi đọc, nên consumer phải tự nhớ vị trí đã xử lý. Khi crash, consumer đọc tiếp từ vị trí đã nhớ. Bước [5] đứng trước hay sau bước [4] quyết định event bị mất hay bị xử lý lặp (xem [05-delivery-semantics.md](05-delivery-semantics.md)).

## Ví dụ

Đếm số đơn hàng mỗi phút, hai cách làm:

| | Batch | Stream |
|---|---|---|
| Khi nào chạy | 00:05 mỗi đêm, trên file của ngày hôm trước | Liên tục |
| Đầu vào | 1,2 triệu dòng, biết chắc đã đủ | Từng đơn hàng khi nó được ghi vào topic |
| Kết quả | 1.440 dòng (một dòng mỗi phút), đúng ngay lần đầu | Một con số cho mỗi phút, phát ra vài giây sau khi phút kết thúc |
| Đơn đến trễ (điện thoại mất mạng) | Không có vấn đề, vì file đã đủ | Phải quyết định chờ bao lâu, và đơn đến sau thời hạn thì làm gì |
| Crash giữa chừng | Chạy lại job | Đọc lại từ vị trí đã commit; số đếm đang tính dở phải phục hồi được |

Cột Stream có hai vấn đề không có ở batch: dữ liệu trễ và trạng thái đang tính dở. Cả hai đều là hệ quả của unbounded data.

## Câu hỏi

**Stream processing là gì, khác batch processing ở điểm nào?**
> - **Batch processing**: chạy định kỳ trên một khối dữ liệu hữu hạn đã gom đủ.
> - **Stream processing**: chạy liên tục trên dòng event vô hạn, xử lý khi event đến.
>
> Tiêu chí phân biệt là dữ liệu đầu vào có điểm kết thúc hay không. Bounded data cho phép đợi đủ dữ liệu rồi trả kết quả đúng một lần. Unbounded data buộc chương trình phải trả kết quả từng phần và tự quyết định "đã đủ chưa". Vì vậy stream processing phải có thêm ba thứ mà batch không cần: vị trí đọc bền vững (offset, commit), cơ chế xử lý dữ liệu trễ (event-time, watermark) và state sống sót qua crash.
>
> Ranh giới: micro-batch nằm giữa hai loại. Nó vẫn là stream vì chạy liên tục trên unbounded data, chỉ gom từng nhóm nhỏ để tăng throughput.

**Khi nào một bài toán cần stream processing, khi nào batch là đủ?**
> - **Latency yêu cầu**: thời gian chấp nhận được từ lúc sự việc xảy ra tới lúc có kết quả.
>
> Quy tắc: bài toán cần stream khi giá trị của kết quả giảm nhanh theo thời gian, tức kết quả đến muộn vài phút đã mất phần lớn giá trị (cảnh báo gian lận, tồn kho, phát hiện sự cố). Bài toán chấp nhận độ trễ hàng giờ và cần nhìn toàn bộ dữ liệu một lần (báo cáo tài chính cuối ngày) thì batch đơn giản và rẻ hơn.
>
> Ranh giới: nhiều hệ thống dùng cả hai. Stream cho kết quả nhanh nhưng có thể chưa đủ dữ liệu trễ, batch chạy sau để đối soát và sửa. Thêm nữa, log Kafka giữ lại được lâu, nên cùng một code stream có thể "replay" để chạy lại như batch (xem [13-observability-and-operations.md](13-observability-and-operations.md)).

**Latency và throughput liên quan với nhau thế nào?**
> - **Latency**: thời gian một event đi hết pipeline.
> - **Throughput**: số event pipeline xử lý được mỗi giây.
> - **Batching**: gom nhiều event vào một lần đọc, ghi hoặc gọi mạng.
>
> Quy tắc: batching tăng throughput vì chia chi phí cố định của mỗi lần gọi cho nhiều event, và làm tăng latency vì event phải chờ batch đầy hoặc hết thời gian chờ. Mọi tham số "kích thước tối thiểu" và "thời gian chờ tối đa" ở producer, consumer và sink đều là nút vặn của đánh đổi này (xem [09-backpressure-and-throughput.md](09-backpressure-and-throughput.md)).
>
> Ranh giới: khi hệ thống quá tải, latency tăng vọt bất kể batching, vì event xếp hàng chờ. Lúc đó latency thực chất đo độ dài hàng đợi, tức consumer lag (xem [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md)).

**Stateful khác stateless ở đâu, và vì sao stateful khó hơn nhiều?**
> - **State**: dữ liệu engine phải nhớ giữa các event (số đếm, tập key đã thấy, window đang mở).
>
> Quy tắc: một bước là stateful nếu kết quả xử lý event này phụ thuộc vào event khác. Stateful khó hơn vì state phải (1) nằm cùng chỗ với event của cùng key, nên ràng buộc cách chia partition; (2) được sao lưu, nên crash không mất; (3) được chuyển hoặc dựng lại khi partition đổi chủ lúc rebalance; (4) nhất quán với vị trí đã commit, vì nếu không thì phục hồi xong sẽ đếm thiếu hoặc đếm hai lần.
>
> Ranh giới: tra bảng tĩnh (danh mục sản phẩm nạp sẵn vào RAM) về mặt kỹ thuật là có dữ liệu, nhưng không phải state theo nghĩa trên, vì nó không thay đổi theo stream. Nó chỉ trở thành state khi bảng tra được cập nhật bằng chính một stream khác (stream-table join, xem [11-state-and-joins.md](11-state-and-joins.md)).

**Stream-table duality nghĩa là gì, dùng vào việc gì?**
> - **Stream**: chuỗi các thay đổi theo thời gian.
> - **Table**: trạng thái mới nhất của mỗi key.
>
> Quy tắc: table là kết quả của việc áp lần lượt mọi event của stream; stream là nhật ký thay đổi của table. Có cái này thì luôn dựng lại được cái kia. Nhờ vậy (a) state của engine có thể sao lưu thành một topic (changelog) và dựng lại bằng cách đọc topic đó; (b) database có thể phát ra stream thay đổi qua CDC; (c) sửa lỗi logic xong chỉ cần replay stream là được table đúng.
>
> Ranh giới: để table dựng lại được từ stream, stream phải còn đủ lịch sử. Hoặc giữ toàn bộ, hoặc dùng log compaction để chỉ giữ giá trị mới nhất của mỗi key (xem [02-kafka-log-model.md](02-kafka-log-model.md)). Topic bị xoá theo thời gian (retention) thì mất khả năng dựng lại.

## Hiểu nhầm thường gặp
- **"Realtime nghĩa là từng event một, không có batch."** Gần như mọi consumer đều đọc và ghi theo nhóm nhỏ. "Realtime" chỉ nói về độ trễ đầu-cuối, không nói về kích thước nhóm.
- **"Kafka xử lý dữ liệu."** Kafka chỉ lưu và phân phối event. Phần xử lý là việc của consumer, hoặc của framework chạy trên consumer (Kafka Streams, Flink).
- **"Stream thì không cần lo dữ liệu đến trễ."** Ngược lại, đây là vấn đề trung tâm của stream processing. Batch tránh được nó chỉ vì đợi đủ dữ liệu rồi mới chạy.
- **"Đọc xong là message bị xoá."** Log giữ event theo chính sách retention, không phụ thuộc việc có ai đọc. Nhờ vậy nhiều consumer đọc độc lập được, và có thể replay.

## Liên quan
- [02-kafka-log-model.md](02-kafka-log-model.md): log Kafka lưu event thế nào. Đây là nền cho mọi file sau.
- [05-delivery-semantics.md](05-delivery-semantics.md): bước commit đứng ở đâu trong vòng lặp thì mất hay trùng.
- [10-time-and-windows.md](10-time-and-windows.md): xử lý dữ liệu trễ và khái niệm "mỗi phút".
- [11-state-and-joins.md](11-state-and-joins.md): lưu và phục hồi state.
