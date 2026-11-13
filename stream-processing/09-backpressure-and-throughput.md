# Backpressure và throughput

> **Backpressure** là cơ chế để engine không nhận dữ liệu nhanh hơn khả năng xử lý. Nhờ consumer *kéo* dữ liệu, backpressure trong Kafka chỉ cần làm một việc: đọc chậm lại. Engine thực hiện việc đó ở ba tầng: hàng đợi có giới hạn, tạm dừng fetch từng partition, và giới hạn bộ nhớ fetch của client. **Throughput** của một consumer được quyết định bởi khâu chậm nhất, thường là sink và chi phí xử lý từng record, ít khi là Kafka.

## Tại sao cần biết
Engine không có backpressure thì khi sink chậm, record tích trong bộ nhớ cho tới khi hết RAM, hoặc vòng poll bị chặn lâu tới mức member bị loại khỏi group. Engine có backpressure nhưng sai tầng thì một partition chậm làm đứng mọi partition khác. Ở chiều tối ưu, biết các nút vặn của fetch, batch, nén và cấp phát bộ nhớ thì mới biết vì sao cùng một code chạy 10.000 msg/s ở cấu hình này mà chỉ 2.000 msg/s ở cấu hình khác, và vì sao nút cổ chai thường không nằm ở chỗ người ta tìm đầu tiên.

## Khái niệm cốt lõi

### Backpressure
- **Là gì**: tín hiệu chảy *ngược* từ khâu sau về khâu trước: "chậm lại, tôi chưa xử lý kịp".
- **Dùng để**: giữ lượng dữ liệu đang nằm trong engine ở mức có giới hạn, bất kể tốc độ đầu vào. Với Kafka, dữ liệu chưa đọc vẫn nằm an toàn trong log, nên đọc chậm lại không làm mất gì; nó chỉ làm lag tăng.

### Ba tầng backpressure

| Tầng | Là gì | Dùng để | Hạn chế |
|---|---|---|---|
| Hàng đợi có giới hạn | Channel hoặc queue có dung lượng cố định giữa vòng poll và worker | Vòng poll tự chặn khi hàng đầy | Chặn *mọi* partition, kể cả partition đi tới phần sink đang nhanh |
| Tạm dừng fetch từng partition (pause/resume) | Ra lệnh client ngừng fetch một partition cụ thể trong khi vòng poll vẫn chạy và member vẫn ở trong group | Chậm lại có chọn lọc: chỉ partition đang ứ | Phải tự theo dõi ngưỡng cho từng partition |
| Giới hạn bộ nhớ fetch | Giới hạn số fetch đồng thời và số byte mỗi fetch của client | Đặt trần bộ nhớ dữ liệu đã fetch mà chưa xử lý | Chỉ là trần tổng, không phân biệt partition |

- Ngưỡng pause/resume thường có hai mức (**high water / low water**): vượt mức cao thì pause, tụt dưới mức thấp mới resume, để partition không bật tắt liên tục.

### Rủi ro chặn vòng poll
- **Là gì**: nếu backpressure được thực hiện bằng cách *không gọi poll*, member có thể vượt quá poll interval tối đa và bị loại khỏi group (xem [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md)).
- **Dùng để**: hiểu vì sao pause partition an toàn hơn chặn vòng poll. Pause giữ vòng poll chạy (và giữ heartbeat với những client gắn heartbeat vào poll), chỉ dừng việc nhận dữ liệu mới.

### Nút vặn của fetch

Các tham số dưới dùng tên của client Java; client khác có tên và giá trị mặc định riêng, có khi khác đáng kể (ví dụ thời gian chờ tối đa của fetch).

| Tham số | Là gì | Tác động |
|---|---|---|
| `fetch.min.bytes` | Broker chờ đủ bấy nhiêu byte mới trả kết quả | Tăng thì mỗi fetch mang nhiều dữ liệu hơn (throughput cao, ít request), nhưng record có thể chờ lâu hơn |
| `fetch.max.wait.ms` | Thời gian broker chờ tối đa khi chưa đủ `fetch.min.bytes` | Trần độ trễ do fetch thêm vào khi traffic thấp |
| `max.partition.fetch.bytes` | Trần byte mỗi partition trong một fetch | Tăng khi một partition có throughput rất lớn |
| `fetch.max.bytes` | Trần byte của cả một fetch | Cùng với số fetch đồng thời, quyết định bộ nhớ đệm tối đa |
| `max.poll.records` | Số record tối đa một lần poll trả về | Kích thước mỗi lô giao cho ứng dụng; ảnh hưởng thời gian giữa hai lần poll |

- Hai trần về byte không tuyệt đối: batch đầu tiên quá cỡ vẫn được trả, để consumer luôn tiến được.
- Dữ liệu được nén theo batch. Trần byte tính trên dữ liệu *đã nén*, nên sau giải nén, bộ nhớ dùng thực tế có thể lớn hơn nhiều lần.

### Nén và batching ở producer
- **Là gì**: producer gom record vào batch theo partition (kích thước batch, thời gian chờ gom) và nén cả batch (gzip, snappy, lz4, zstd).
- **Dùng để**: giảm số request và số byte qua mạng, tăng throughput ở cả hai đầu. Consumer nhận nguyên batch đã nén và giải nén ở phía mình. Vì vậy batch nhỏ ở producer làm consumer cũng kém hiệu quả.

### Batching ở sink
- **Là gì**: ghi nhiều record trong một lần: bulk insert, pipeline lệnh, gom request.
- **Dùng để**: giảm chi phí cố định (round-trip mạng, transaction, fsync) trên mỗi record. Đây thường là thay đổi tăng throughput nhiều nhất, vì sink thường là khâu chậm nhất.

### Chi phí cấp phát bộ nhớ và GC
- **Là gì**: với ngôn ngữ có garbage collector (Go, Java), mỗi record được giải mã thành nhiều object nhỏ. GC tốn CPU tỉ lệ với *tốc độ cấp phát* và số object còn sống.
- **Dùng để**: hiểu vì sao ở throughput cao, số object cấp phát cho mỗi record quan trọng hơn số byte. Trong Go, tăng gấp đôi `GOGC` làm phần bộ nhớ dư cho heap tăng gấp đôi và chi phí CPU của GC giảm khoảng một nửa. `GOMEMLIMIT` đặt một trần *mềm* cho bộ nhớ, dành cho chương trình chạy trong container có giới hạn RAM. Cách bền vững nhất vẫn là cho GC ít object phải quản lý hơn: dùng lại buffer, giải mã vào struct có sẵn, xử lý theo slice thay vì gửi từng record qua channel.

### Định luật Little
- **Là gì**: số việc đang nằm trong hệ thống = tốc độ đến × thời gian mỗi việc nằm trong hệ thống (L = λ × W).
- **Dùng để**: ước lượng nhanh. Muốn 5.000 msg/s với mỗi record mất 40 ms (gồm chờ I/O) thì cần khoảng 5.000 × 0,04 = 200 record đang xử lý đồng thời. Con số này cho biết cần bao nhiêu song song (xem [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md)) và trần in-flight tối thiểu là bao nhiêu.

## Cách hoạt động

```
  broker ──fetch──► [bộ đệm của client]  ──poll──► [hàng đợi giới hạn] ──► worker ──► sink
                    trần: fetch.max.bytes          dung lượng N              │
                          × số fetch đồng thời          ▲                     │
                                                        │ đầy: poll chặn      │ chậm
                    ◄──── pause(P3) ─── hàng của P3 > high water ◄────────────┘
                    ◄──── resume(P3) ── hàng của P3 < low water
```

Chuỗi phản ứng khi sink của partition P3 chậm:
1. Record của P3 tích trong hàng của nó, số in-flight của P3 tăng.
2. Vượt high water thì P3 bị pause; client ngừng fetch P3, các partition khác vẫn chạy bình thường.
3. Lag của P3 tăng, dữ liệu của P3 nằm chờ trong log.
4. Sink hồi phục, hàng của P3 cạn dưới low water, P3 được resume.

Nếu chỉ dùng hàng đợi chung có giới hạn, ở bước 2 cả vòng poll sẽ chặn, và mọi partition đều dừng theo P3.

## Ví dụ

Engine ghi vào database, mỗi lần insert một dòng mất 2 ms (gần như toàn bộ là round-trip mạng):

| Cách ghi | Thời gian cho 1.000 record | Throughput tối đa của một luồng |
|---|---|---|
| Từng dòng một | 1.000 × 2 ms = 2 s | 500 msg/s |
| Bulk insert 500 dòng, mỗi lần 10 ms | 2 × 10 ms = 20 ms | ≈ 50.000 msg/s |

Đổi cấu hình fetch hay tăng số partition không cứu được trường hợp đầu, vì nút cổ chai nằm ở sink. Ngược lại, khi đã bulk insert, kích thước lô poll (`max.poll.records`) bắt đầu có ý nghĩa, vì nó quyết định có đủ record để gom thành một lô ghi hay không.

## Câu hỏi

**Backpressure là gì, và Kafka hỗ trợ nó thế nào?**
> - **Backpressure**: tín hiệu từ khâu sau báo khâu trước chậm lại.
> - **Pull**: consumer chủ động kéo dữ liệu, broker không đẩy.
>
> Quy tắc: trong mô hình pull, backpressure chỉ là "kéo chậm lại", và dữ liệu chưa kéo vẫn an toàn trong log. Vì vậy Kafka không cần giao thức backpressure riêng. Engine chỉ cần giới hạn lượng dữ liệu đang giữ (hàng đợi có giới hạn, trần bộ nhớ fetch) và dừng nhận dữ liệu mới có chọn lọc (pause partition).
>
> Ranh giới: "kéo chậm lại" không được làm bằng cách ngừng gọi poll quá lâu, vì member sẽ bị coi là kẹt và bị loại khỏi group. Pause partition giữ vòng poll chạy mà không nhận thêm dữ liệu.

**Pause partition khác chặn bằng hàng đợi đầy ở đâu?**
> - **Hàng đợi có giới hạn**: chỗ chứa cố định giữa vòng poll và worker.
> - **Pause/resume**: dừng hoặc tiếp tục fetch một partition cụ thể.
>
> Tiêu chí phân biệt là *phạm vi chặn*. Hàng đợi chung đầy chặn cả vòng poll, nên mọi partition dừng. Pause chỉ dừng partition đang ứ, các partition khác vẫn chạy. Pause phù hợp khi chậm là *cục bộ* (một shard DB nóng, một khách hàng có traffic lớn). Hàng đợi chung đủ dùng khi mọi partition đi tới cùng một sink và chậm cùng lúc.
>
> Ranh giới: khi sink chết hẳn, pause theo ngưỡng từng partition sẽ lần lượt pause tất cả. Lúc đó circuit breaker (pause mọi partition một lần, thử lại theo chu kỳ) mô tả trạng thái rõ ràng hơn (xem [07-errors-retry-and-dlq.md](07-errors-retry-and-dlq.md)).

**Nút cổ chai throughput của consumer thường nằm ở đâu?**
> - **Nút cổ chai**: khâu chậm nhất, quyết định throughput của cả chuỗi.
>
> Quy tắc: throughput của một pipeline bằng throughput của khâu chậm nhất. Theo thứ tự hay gặp: (1) sink ghi từng record, vì chi phí round-trip lặp lại cho mỗi record; (2) mỗi record chờ I/O tuần tự, vì không đủ song song; (3) chi phí giải mã và cấp phát bộ nhớ ở throughput rất cao; (4) cấu hình fetch, thường chỉ thành vấn đề sau khi ba khâu trên đã được giải quyết.
>
> Ranh giới: đo trước khi chỉnh. Lag tăng trong khi CPU thấp nghĩa là engine đang chờ (sink hoặc thiếu song song). CPU cao với phần lớn thời gian trong GC nghĩa là vấn đề nằm ở cấp phát bộ nhớ.

**Vì sao có đánh đổi giữa throughput và latency khi chỉnh fetch?**
> - **`fetch.min.bytes`**: số byte tối thiểu broker gom trước khi trả.
> - **`fetch.max.wait.ms`**: thời gian chờ tối đa.
>
> Quy tắc: mỗi fetch có chi phí cố định, nên fetch lớn và ít thì throughput cao. Nhưng để có fetch lớn, broker phải chờ dữ liệu tích đủ, nên record chờ lâu hơn. Hai tham số này định nghĩa cuộc chờ đó: gom tới khi đủ số byte tối thiểu, hoặc tới khi hết thời gian chờ tối đa. Traffic cao thì byte đủ rất nhanh và gần như không phải chờ. Traffic thấp thì thời gian chờ tối đa thành độ trễ thêm vào.
>
> Ranh giới: giá trị mặc định của thời gian chờ tối đa khác nhau giữa các client, có client mặc định vài giây. Topic ít traffic với một client như vậy có thể trễ vài giây mỗi fetch mà không có lỗi gì.

**Vì sao số object cấp phát cho mỗi record quan trọng ở throughput cao?**
> - **GC**: bộ thu gom bộ nhớ tự động.
> - **Tốc độ cấp phát**: số object, hoặc số byte, cấp phát mỗi giây.
>
> Quy tắc: chi phí CPU của GC tỉ lệ với tốc độ cấp phát và số object phải theo dõi. Ở 100.000 msg/s, mỗi record cấp phát 20 object nhỏ là 2 triệu object mỗi giây cho GC. Giảm số object (dùng lại buffer, giải mã vào struct có sẵn, xử lý theo slice) giảm chi phí GC trực tiếp hơn là giảm số byte.
>
> Ranh giới: chỉnh `GOGC` hay `GOMEMLIMIT` đổi bộ nhớ lấy CPU, không giảm được lượng việc. `GOMEMLIMIT` là trần mềm: khi dữ liệu thật sự vượt trần, GC chạy liên tục (thrashing). Vì vậy giới hạn bộ nhớ fetch của client phải nằm dưới trần này.

## Hiểu nhầm thường gặp
- **"Consumer chậm thì tăng `max.poll.records`."** Nếu sink ghi từng record thì lô lớn hơn chỉ làm mỗi vòng poll lâu hơn, không làm nhanh hơn.
- **"Backpressure làm mất dữ liệu."** Với Kafka, dữ liệu chưa đọc vẫn nằm trong log; backpressure chỉ làm tăng lag.
- **"Trần `fetch.max.bytes` là trần bộ nhớ."** Nó tính trên dữ liệu đã nén, cho mỗi fetch; bộ nhớ thật còn phụ thuộc số fetch đồng thời và tỉ lệ nén.
- **"Throughput thấp là do Kafka."** Nút cổ chai thường là sink và chi phí xử lý từng record.

## Liên quan
- [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md): poll interval tối đa.
- [07-errors-retry-and-dlq.md](07-errors-retry-and-dlq.md): circuit breaker khi downstream sập.
- [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md): trần in-flight và số luồng cần thiết.
- [13-observability-and-operations.md](13-observability-and-operations.md): đo lag và latency để tìm nút cổ chai.
