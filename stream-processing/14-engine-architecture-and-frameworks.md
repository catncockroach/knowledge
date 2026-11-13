# Kiến trúc engine và các loại framework

> Một engine consumer gồm bốn tầng xử lý (**source → decode → process → sink**), bọc trong một **runtime** dùng chung lo offset, rebalance, lỗi, backpressure, metric và shutdown. Phần lớn độ khó nằm ở runtime chứ không ở logic nghiệp vụ. Các công cụ xử lý stream khác nhau ở chỗ chúng làm sẵn bao nhiêu phần của kiến trúc này: **client** (chỉ đọc ghi), **thư viện stream nhúng**, **runtime cụm**, **công cụ pipeline cấu hình**, **streaming SQL**. Đặc điểm của bài toán (sink là gì, cần thứ tự theo gì, có state theo thời gian không) quyết định cần bao nhiêu trong số đó.

## Tại sao cần biết
Các file trước mô tả từng cơ chế riêng lẻ. File này ghép chúng thành một bức tranh: mỗi cơ chế nằm ở đâu trong engine, và khi gặp một bài toán mới thì đi từ đặc điểm của nó tới những cơ chế cần dùng. Nó cũng giải thích ranh giới giữa "tự viết trên client" và "dùng framework" bằng tiêu chí, để quyết định đó dựa trên bài toán chứ không dựa trên thói quen.

## Khái niệm cốt lõi

### Bốn tầng xử lý
| Tầng | Là gì | Dùng để | Chi tiết ở |
|---|---|---|---|
| Source | Client Kafka: poll, tham gia group, nhận callback giao/thu hồi partition, pause/resume | Đưa record vào engine và giữ quan hệ với group | [03](03-consumer-groups-and-offsets.md), [04](04-rebalancing-and-scaling.md) |
| Decode | Tách wire format, tra và cache schema theo ID, kiểm tra hợp lệ | Biến byte thành dữ liệu có cấu trúc; chặn poison message sớm | [12](12-schema-and-serialization.md) |
| Process | Logic nghiệp vụ, chạy theo partition hoặc theo key; có thể kèm state | Tạo kết quả | [08](08-parallelism-and-ordering.md), [10](10-time-and-windows.md), [11](11-state-and-joins.md) |
| Sink | Ghi kết quả theo batch, idempotent | Đưa kết quả ra ngoài và chịu được ghi lặp | [06](06-idempotency-and-sinks.md), [09](09-backpressure-and-throughput.md) |

### Runtime dùng chung
- **Là gì**: phần khung mà mọi pipeline dùng lại, không chứa logic nghiệp vụ. Gồm offset tracker theo partition, bộ phân loại lỗi và định tuyến retry/DLQ, trần in-flight và pause theo ngưỡng, xử lý callback rebalance, metric, tracing qua header, health check theo tiến độ, và trình tự shutdown.
- **Dùng để**: giải quyết một lần các vấn đề mà mọi engine đều gặp. Thực tế, các tổ chức tự viết consumer ở quy mô lớn thường đóng gói phần này thành một SDK nội bộ. Service mới viết phần process, còn mọi thứ khác có sẵn.

### Mô hình connector (reader → transform → writer)
- **Là gì**: pipeline được cấu hình bằng cách ghép một nguồn, một chuỗi biến đổi và một đích có sẵn, thay vì viết code cho từng pipeline.
- **Dùng để**: các pipeline *di chuyển dữ liệu* (sao chép, lọc, đổi định dạng, định tuyến) mà logic đơn giản và lặp lại nhiều lần.

### Pull và push proxy
- **Pull**
  - **Là gì**: mỗi service tự chạy consumer và tự đọc Kafka.
  - **Dùng để**: mô hình mặc định; đơn giản, ít hạ tầng.
- **Push proxy**
  - **Là gì**: một tầng trung tâm đọc Kafka một lần rồi *đẩy* từng message tới service qua RPC (gRPC, HTTP), đồng thời tự quản lý offset và retry.
  - **Dùng để**: khi hàng trăm service cùng đọc. Proxy đọc mỗi topic một lần thay vì mỗi service một lần (giảm chi phí đọc), và tách song song khỏi số partition vì nó có thể đẩy song song nhiều message của cùng partition.
- **Đánh đổi**: proxy thêm một chặng mạng, thêm một hệ thống phải vận hành và một điểm lỗi chung. Ở quy mô nhỏ đến vừa, độ phức tạp đó thường không đáng.

### Các loại công cụ xử lý stream
| Loại | Là gì | Làm sẵn | Không làm sẵn |
|---|---|---|---|
| Client Kafka | Thư viện đọc ghi, tham gia group, transaction | Giao thức, group, commit, có thể có transaction | Gần như toàn bộ runtime: tracker, retry/DLQ, state, window |
| Thư viện ứng dụng sự kiện | Router và middleware trên client | Retry, poison queue, dedupe, circuit breaker | State bền, window |
| Thư viện stream có state theo key | Gắn một bảng state theo partition vào consumer group, sao lưu bằng topic compacted | State theo key, restore khi rebalance | Window theo event time, join phức tạp |
| Công cụ pipeline cấu hình | Pipeline mô tả bằng file cấu hình, nhiều connector có sẵn | Ingest, biến đổi, định tuyến, offset tracker | State bền |
| Thư viện stream nhúng (kiểu Kafka Streams) | Chạy *trong* ứng dụng; đọc và ghi Kafka | Window, join, state store, changelog, exactly-once Kafka→Kafka | Nguồn và đích ngoài Kafka; song song vượt số partition |
| Runtime cụm (kiểu Flink) | Một cụm riêng chạy job, checkpoint lên storage bền | Window, join, state lớn, checkpoint, savepoint, nhiều connector, song song không phụ thuộc partition | Không chạy như một ứng dụng thường; cần vận hành cụm |
| Streaming SQL / database | Viết truy vấn SQL; hệ thống duy trì kết quả (materialized view) tăng dần và cho truy vấn trực tiếp | Mọi thứ diễn đạt được bằng SQL | Logic không diễn đạt được bằng SQL |
| Engine micro-batch | Chạy truy vấn trên các lô nhỏ liên tiếp | Tận dụng hạ tầng batch sẵn có | Độ trễ phụ thuộc kích thước lô |

- **Khác biệt cốt lõi giữa thư viện nhúng và runtime cụm** là mô hình triển khai. Thư viện nhúng là *code được ship cùng ứng dụng*, chạy như mọi service. Runtime cụm là *hạ tầng phải vận hành*. Khi cả hai đều làm được bài toán, lựa chọn nằm ở vận hành và đội ngũ chứ không ở năng lực.

## Cách hoạt động

Sơ đồ tham khảo của một engine instance:

```
                 +------------------------------- engine instance --------------------------------+
                 |                                                                                |
 Kafka topic     |  [1] SOURCE          [2] DECODE          [3] PROCESS           [4] SINK        |
 P0..Pn  ──────► |  poll, pause/resume ► cache theo     ►   theo partition   ►   ghi theo batch  | ──► DB / topic / API
                 |  callback rebalance   schema ID           hoặc theo key        idempotent      |
                 |        ▲              lỗi → DLQ           state (tuỳ chọn)          │          |
                 |        │                                                          │ ack      |
                 |        └──────── [5] OFFSET TRACKER (mốc liên tục) ◄──────────────┘          |
                 |                                                                                |
                 |  [6] RUNTIME: phân loại lỗi, retry/DLQ · trần in-flight · metric · tracing     |
                 |               health check theo tiến độ · graceful shutdown                    |
                 +--------------------------------------------------------------------------------+
                        │ lỗi tạm thời                                   │ lỗi vĩnh viễn
                        ▼                                                ▼
                 retry topic (nhiều tầng) ─────────────────────────►  DLQ ──► công cụ redrive

 Bên ngoài: bộ đo lag (theo offset và theo giây) → cảnh báo, autoscale · schema registry ·
            changelog topic compacted (nếu có state) · đĩa bền gắn theo danh tính instance (nếu có state)
```

Đi từ bài toán tới kỹ thuật bằng ba câu hỏi, theo thứ tự:
1. **Sink là gì?** Quyết định mức delivery và cách khử trùng ([05](05-delivery-semantics.md), [06](06-idempotency-and-sinks.md)).
2. **Cần thứ tự theo gì?** Quyết định mô hình song song và đường retry ([07](07-errors-retry-and-dlq.md), [08](08-parallelism-and-ordering.md)).
3. **Có state gắn với thời gian không?** Quyết định mức công cụ cần dùng ([10](10-time-and-windows.md), [11](11-state-and-joins.md)).

## Ví dụ

Bản đồ từ đặc điểm bài toán tới kỹ thuật phù hợp:

| Đặc điểm bài toán | Kỹ thuật phù hợp | Đánh đổi |
|---|---|---|
| Stateless, xử lý nhanh, cần thứ tự theo partition | Một luồng mỗi partition, xử lý theo lô, commit sau lô | Song song bị chặn bởi số partition |
| Stateless, mỗi record chờ I/O lâu, không cần thứ tự | Song song trong partition, offset tracker, trần in-flight; hoặc share group | Crash thì xử lý lại nhiều hơn; sink phải idempotent |
| Cần thứ tự theo thực thể (user, đơn hàng) | Key = định danh thực thể; băm key vào worker cố định; retry tại chỗ | Một key lỗi lâu chặn key đó; hot key thành nút cổ chai |
| Cần thứ tự tuyệt đối (CDC, sổ cái) | Dừng khi lỗi, retry chặn kèm cảnh báo | Mất liveness khi có poison message |
| Không cần thứ tự, lỗi tạm thời phổ biến | Retry topic nhiều tầng, DLQ, redrive; trễ bằng pause partition | Nhiều topic; mất thứ tự |
| Thời gian xử lý rất không đều | Tách fast lane và slow lane; timeout theo record | Thêm topic và logic định tuyến |
| Sink ngoài Kafka phải "đúng một lần" | At-least-once cộng upsert hoặc idempotency key; hoặc lưu offset trong transaction của sink | Cần đối soát các ca biên |
| Kafka → Kafka không được trùng | Transaction, bên đọc `read_committed` | Độ trễ không nhỏ hơn chu kỳ transaction |
| Dedupe hoặc aggregate theo key, không window | Store cục bộ theo partition, changelog, đĩa bền | Restore lâu khi mất đĩa |
| Window theo event time, join, session, state lớn | Thư viện stream nhúng hoặc runtime cụm | Thêm hệ thống hoặc thêm runtime |
| Logic diễn đạt được bằng SQL, cần truy vấn kết quả trực tiếp | Streaming SQL / database | Giới hạn trong những gì SQL diễn đạt được |
| Di chuyển dữ liệu giữa nhiều nguồn và đích, logic đơn giản | Công cụ pipeline cấu hình, hoặc mô hình connector | Kém linh hoạt cho logic phức tạp |
| Tải dao động mạnh theo giờ | Autoscale theo lag (tốt nhất là lag theo giây), cooldown dài, rebalance rẻ | Mỗi lần scale là một lần rebalance |
| Hàng trăm service cùng đọc, chi phí đọc lớn | Push proxy trung tâm | Thêm chặng, thêm hạ tầng |

Lỗi thiết kế thường gặp, đã được ghi nhận trong vận hành thực tế:

| Lỗi | Hậu quả |
|---|---|
| Health check chỉ kiểm tra kết nối broker | Không phát hiện consumer kẹt |
| Giữ trạng thái của partition đã bị thu hồi | Báo không khoẻ sai, restart và rebalance dây chuyền |
| Commit offset của record vừa xong khi xử lý song song | Mất dữ liệu khi crash |
| Worker pool không theo key cho bài toán cần thứ tự | Retry của một thực thể chặn hoặc đảo thứ tự thực thể khác |
| Autoscale consumer theo CPU | Không theo kịp tải I/O-bound, chia tải lệch |
| Không tính trước số partition | Không scale được lúc sự cố cần bắt kịp |
| Dừng cả consumer để chờ trễ retry | Retry topic chỉ chạy được một partition tại một thời điểm |
| Sink theo batch không kiểm tra dữ liệu trước | Một record hỏng làm lỗi cả batch |

## Câu hỏi

**Một engine consumer gồm những thành phần nào?**
> - **Bốn tầng xử lý**: source, decode, process, sink.
> - **Runtime**: phần khung dùng chung cho mọi pipeline.
>
> Quy tắc: bốn tầng xử lý mô tả *dữ liệu đi qua đâu*. Runtime mô tả *engine sống sót thế nào*: offset tracker, phân loại lỗi và retry/DLQ, backpressure, xử lý rebalance, metric, tracing, health check, shutdown. Logic nghiệp vụ chỉ nằm ở tầng process. Mọi thứ còn lại là runtime, và đó là nơi tập trung phần lớn độ khó và lỗi.
>
> Ranh giới: engine stateful có thêm store cục bộ, changelog, restore và checkpoint. Chúng thuộc runtime nhưng phức tạp tới mức thường là lý do chọn framework (xem [11-state-and-joins.md](11-state-and-joins.md)).

**Pull consumer và push proxy khác nhau ở đâu, khi nào cần proxy?**
> - **Pull consumer**: mỗi service tự đọc Kafka.
> - **Push proxy**: tầng trung tâm đọc Kafka rồi đẩy message tới service qua RPC.
>
> Tiêu chí: proxy giải hai vấn đề chỉ xuất hiện ở quy mô lớn. Một là chi phí đọc khi rất nhiều group cùng đọc một topic. Hai là service muốn song song vượt số partition mà không tự viết offset tracker. Đổi lại, nó thêm một chặng mạng, một hệ thống phải vận hành và một điểm lỗi chung. Khi số service và số team nhỏ, pull consumer với một SDK dùng chung đạt phần lớn lợi ích mà không có các chi phí đó.
>
> Ranh giới: proxy không loại bỏ được các vấn đề cốt lõi. Nó chỉ dời chúng vào proxy: offset tracker, retry, DLQ vẫn phải có, chỉ là ở một chỗ.

**Thư viện stream nhúng và runtime cụm khác nhau ở đâu?**
> - **Thư viện stream nhúng**: chạy trong ứng dụng, đọc và ghi Kafka.
> - **Runtime cụm**: cụm riêng chạy job, checkpoint lên storage bền.
>
> Tiêu chí phân biệt là *mô hình triển khai* và *phạm vi nguồn đích*. Thư viện nhúng triển khai như một service bình thường, chỉ làm việc với Kafka, song song bị chặn bởi số partition, và phục hồi state bằng cách đọc lại changelog. Runtime cụm cần vận hành riêng, nhưng kết nối được nhiều loại nguồn và đích, tách song song khỏi partition, và phục hồi state lớn từ checkpoint. Khi cả hai đều làm được, lựa chọn nằm ở khả năng vận hành và đội ngũ.
>
> Ranh giới: exactly-once của cả hai đều dựa trên cơ chế commit theo chu kỳ, nên đều có độ trễ không nhỏ hơn chu kỳ đó khi bên đọc dùng `read_committed`.

**Khi nào tự viết engine trên client là phù hợp, khi nào nên dùng framework?**
> - **Tự viết trên client**: dùng client Kafka và tự xây runtime.
> - **Framework**: công cụ làm sẵn một phần runtime.
>
> Quy tắc: chi phí tự viết tăng theo mức state *gắn với thời gian*. Stateless, hoặc state theo key không window (đếm, dedupe, hồ sơ thực thể), là vùng tự viết được: runtime cần có là tracker, retry/DLQ, metric, shutdown, cộng store cục bộ và changelog nếu có state. Khi bài toán cần window theo event time, watermark, session window, join stream-stream, state lớn cần checkpoint và nâng cấp logic mà giữ state, hoặc exactly-once có state, tự viết nghĩa là dựng lại phần lớn một framework, và đó là lúc framework rẻ hơn.
>
> Ranh giới: hai hướng thường được ghép. Engine tự viết lo ingest, decode, làm giàu stateless và sink idempotent; phần phân tích có window và join giao cho framework hoặc streaming SQL; cả hai cùng đọc Kafka.

**Gặp một bài toán realtime mới thì bắt đầu phân tích từ đâu?**
> - **Sink**: nơi kết quả có hiệu lực.
> - **Đơn vị thứ tự**: mức thứ tự nhỏ nhất bài toán cần giữ.
> - **State theo thời gian**: kết quả phụ thuộc vào event khác trong một khoảng thời gian.
>
> Quy tắc: ba câu hỏi theo thứ tự này quyết định phần lớn kiến trúc. (1) Sink là gì quyết định mức delivery và cách khử trùng. (2) Cần thứ tự theo gì quyết định mô hình song song và đường retry. (3) Có state theo thời gian không quyết định tự viết hay dùng framework. Throughput và latency mục tiêu sau đó quyết định số partition, cấu hình batch và mức song song.
>
> Ranh giới: thứ tự này giả định yêu cầu nghiệp vụ đã rõ. Nếu chưa rõ dữ liệu đến trễ bao lâu, hoặc trùng có hại tới mức nào, cần đo hoặc hỏi trước. Đó là những thông số mà mọi lựa chọn phía sau phụ thuộc vào.

## Hiểu nhầm thường gặp
- **"Phần khó của engine là logic nghiệp vụ."** Phần khó là runtime: offset, lỗi, rebalance, shutdown, state.
- **"Framework thì không cần hiểu các cơ chế bên dưới."** Framework làm sẵn cơ chế, nhưng các đánh đổi (exactly-once tốn độ trễ, restore tốn thời gian, partition chặn song song) vẫn còn nguyên.
- **"Push proxy luôn tốt hơn vì tập trung."** Nó chỉ có lợi ở quy mô rất lớn; ở quy mô vừa nó thêm phức tạp và một điểm lỗi chung.
- **"Chọn công cụ trước, rồi mới phân tích bài toán."** Đặc điểm bài toán (sink, thứ tự, state) quyết định công cụ, không phải ngược lại.

## Liên quan
- [05-delivery-semantics.md](05-delivery-semantics.md) và [06-idempotency-and-sinks.md](06-idempotency-and-sinks.md): câu hỏi thứ nhất (sink).
- [07-errors-retry-and-dlq.md](07-errors-retry-and-dlq.md) và [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md): câu hỏi thứ hai (thứ tự).
- [10-time-and-windows.md](10-time-and-windows.md) và [11-state-and-joins.md](11-state-and-joins.md): câu hỏi thứ ba (state theo thời gian).
- [13-observability-and-operations.md](13-observability-and-operations.md): runtime trong vận hành.
