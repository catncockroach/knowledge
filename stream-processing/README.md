# Stream processing

Stream processing là xử lý dữ liệu ngay khi nó đến, trên một dòng sự kiện không có điểm kết thúc. Đây là nền tảng của mọi engine xử lý dữ liệu realtime: đồng bộ dữ liệu, cảnh báo, đếm và tổng hợp theo thời gian, làm giàu sự kiện. Bộ ghi chú này lấy Apache Kafka làm nền tảng log và nhìn từ góc độ người xây **engine consumer**: đọc từ Kafka, xử lý, ghi ra sink, và chạy liên tục qua lỗi, rebalance, deploy và thay đổi quy mô. Nguồn gốc là research [2026-11-13-kien-truc-engine-consumer-kafka](../research/2026-11-13-kien-truc-engine-consumer-kafka/report.md). Phần ghi chú này chỉ giữ kiến thức ổn định; phiên bản cụ thể, so sánh client và số liệu benchmark nằm ở report đó.

## Phạm vi
- **Có:** mô hình log của Kafka (topic, partition, offset, compaction); consumer group, commit, lag; rebalance và scale; delivery semantics và transaction; idempotency và thiết kế sink; xử lý lỗi, retry và DLQ; song song, thứ tự và offset tracker; backpressure và throughput; event time, watermark, window; state, changelog và join; schema và serialization; quan sát, shutdown, replay; kiến trúc tham khảo của một engine và tiêu chí phân biệt các loại framework. Ví dụ code viết bằng Go, dạng minh hoạ khái niệm, không gắn với client cụ thể.
- **Không:** vận hành và tuning broker (sizing cluster, replication); so sánh Kafka với message broker khác; so sánh phiên bản cụ thể của client và framework; hướng dẫn cấu hình triển khai.
- **Đối tượng:** người biết lập trình backend (xem [../backend/](../backend/README.md), nhất là concurrency), mới với stream processing và Kafka.

## Bản đồ tư duy

```
                      01 nền tảng stream ──► 02 mô hình log Kafka
                                                    │
                    ┌───────────────────────────────┼────────────────────────────────┐
                    ▼                               ▼                                ▼
          Tiến độ & group                  Đúng - sai                      Thời gian & state
     03 group, offset, lag         05 delivery semantics                10 event time, window
     04 rebalance, scale     ──►   06 idempotency, sink          ──►    11 state, changelog, join
                                   07 lỗi, retry, DLQ                   12 schema, serialization
                    │                               │                                │
                    └──────────────► Hiệu năng ◄────┘                                │
                               08 song song, thứ tự                                  │
                               09 backpressure, throughput                           │
                                            │                                        │
                                            ▼                                        ▼
                               13 quan sát, vận hành  ──────►  14 kiến trúc engine và framework
```

## Các file
Đọc theo thứ tự:

| File | Nội dung |
|---|---|
| [01-stream-processing-fundamentals.md](01-stream-processing-fundamentals.md) | Stream khác batch ở đâu: event, bounded và unbounded, latency và throughput, stateless và stateful, stream-table duality, vòng lặp đọc → xử lý → ghi → commit. |
| [02-kafka-log-model.md](02-kafka-log-model.md) | Kafka lưu event thế nào: topic, partition là đơn vị thứ tự và song song, record, offset và các mốc của log, partitioner, retention và compaction. |
| [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md) | Consumer group chia partition thế nào, position khác committed offset, các cách commit, `auto.offset.reset`, lag theo offset và theo thời gian, heartbeat và các timeout. |
| [04-rebalancing-and-scaling.md](04-rebalancing-and-scaling.md) | Rebalance xảy ra khi nào và vì sao sinh bản trùng; eager, cooperative và giao thức do broker điều khiển; static membership; partition là trần scale; autoscale theo lag và vòng phản hồi của nó. |
| [05-delivery-semantics.md](05-delivery-semantics.md) | At-most/at-least/exactly-once là hệ quả của thứ tự xử lý và commit; idempotent producer, transaction, `read_committed`; vì sao exactly-once chỉ trọn vẹn khi Kafka → Kafka. |
| [06-idempotency-and-sinks.md](06-idempotency-and-sinks.md) | Làm sink chịu được ghi lặp: upsert, cập nhật theo version, idempotency key, offset theo partition làm key, lưu offset trong transaction của sink, inbox, dual write và outbox. |
| [07-errors-retry-and-dlq.md](07-errors-retry-and-dlq.md) | Phân loại lỗi; retry tại chỗ, retry topic, DLQ, stop on error, giữ thứ tự theo key khi retry; head-of-line blocking; circuit breaker khi downstream sập. |
| [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md) | Song song theo partition, theo key, không thứ tự, share group; offset tracker commit tới mốc liên tục; trần in-flight; hot key. |
| [09-backpressure-and-throughput.md](09-backpressure-and-throughput.md) | Ba tầng backpressure (hàng đợi giới hạn, pause/resume, trần bộ nhớ fetch); các nút vặn fetch; nén và batching; nút cổ chai thường nằm ở sink; chi phí cấp phát và GC; định luật Little. |
| [10-time-and-windows.md](10-time-and-windows.md) | Event time, ingestion time, processing time; stream-time và watermark; grace period và late data; tumbling, hopping, sliding, session window; phát kết quả liên tục hay khi đóng. |
| [11-state-and-joins.md](11-state-and-joins.md) | State theo partition trong store cục bộ hay bên ngoài; changelog, checkpoint, restore, standby; nhất quán state–offset; co-partitioning; các loại join. |
| [12-schema-and-serialization.md](12-schema-and-serialization.md) | JSON, Avro, Protobuf; schema registry, wire format, compatibility mode và thứ tự nâng cấp; lỗi giải mã là poison message. |
| [13-observability-and-operations.md](13-observability-and-operations.md) | Các đại lượng cần đo; đo lag từ bên ngoài và đánh giá theo xu hướng; tracing qua header; graceful shutdown; health check theo tiến độ; replay; kiểm thử. |
| [14-engine-architecture-and-frameworks.md](14-engine-architecture-and-frameworks.md) | Kiến trúc tham khảo bốn tầng cộng runtime; pull và push proxy; các loại công cụ từ client tới streaming SQL; bản đồ từ đặc điểm bài toán tới kỹ thuật; lỗi thiết kế thường gặp. |

## Thuật ngữ nền
- **Partition**: log con của topic; đơn vị thứ tự và đơn vị song song (xem 02).
- **Offset / committed offset**: vị trí của record trong partition / vị trí đã lưu mà consumer đọc tiếp từ đó (xem 02, 03).
- **Consumer group**: các consumer chia nhau partition, mỗi partition thuộc một member (xem 03).
- **Rebalance**: chia lại partition khi member thay đổi (xem 04).
- **Lag**: khoảng cách giữa cuối log và committed offset, tính bằng record hoặc bằng giây (xem 03, 13).
- **At-least-once / effectively-once**: không mất, có thể trùng / trùng nhưng vô hại nhờ sink idempotent (xem 05, 06).
- **DLQ**: topic chứa record không xử lý được (xem 07).
- **Offset tracker**: bộ tính mốc commit liên tục khi xử lý song song (xem 08).
- **Event time / watermark**: lúc sự việc xảy ra / đồng hồ dữ liệu quyết định khi nào đóng window (xem 10).
- **Changelog**: topic compacted sao lưu state của engine (xem 11).
