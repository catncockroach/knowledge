# Delivery semantics & quản lý offset

Phạm vi: at-most/at-least/exactly-once; chiến lược commit offset; idempotency phía sink; Kafka transactions/EOS (KIP-98, KIP-447, KIP-890, KIP-939); retry, retry topic, DLQ, poison message, outbox/inbox; hướng dẫn cụ thể cho Go (franz-go, confluent-kafka-go).

Khái niệm nền (giải thích từ đầu, để writer dùng lại):
- **Offset**: số thứ tự của một record trong một partition. Consumer group lưu "committed offset" cho mỗi partition, tức offset của record *tiếp theo* sẽ đọc khi khởi động lại hoặc khi partition chuyển sang member khác. Javadoc: "The committed offset should always be the offset of the next message that your application will read." — [KafkaConsumer Javadoc 3.9](https://kafka.apache.org/39/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html) (bậc 1, Kafka 3.9). Vì vậy commit cho record offset N phải là N+1; franz-go `CommitRecords` tự cộng 1 (`r.Offset + 1, // need to advice to next offset`) — [franz-go source consumer_group.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/consumer_group.go) (bậc 1, master v1.22.3, xem 2026-11).
- **Position** vs **committed position**: "The position of the consumer gives the offset of the next record that will be given out"; "The committed position is the last offset that has been stored securely" — [KafkaConsumer Javadoc](https://kafka.apache.org/39/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html) (bậc 1).
- **Rebalance**: khi member vào/ra group, partition được chia lại; member mới nhận partition sẽ bắt đầu từ committed offset. Mọi bài toán trùng/mất dữ liệu đều xoay quanh khoảng cách giữa "đã xử lý tới đâu" và "đã commit tới đâu" tại thời điểm crash/rebalance.

## 1. At-most-once / at-least-once / exactly-once thực sự đảm bảo gì, và vỡ ở đâu

### Kết luận ngắn
Ba mức chỉ là hệ quả của *thứ tự* giữa "xử lý" và "lưu vị trí" (phía consumer) cộng với retry (phía producer). Mặc định thực tế của Kafka là at-least-once; exactly-once chỉ có thật trong vòng read-process-write Kafka→Kafka bằng transaction, còn với sink ngoài (DB, HTTP) thì phải tự làm bằng idempotency hoặc lưu offset cùng kết quả. Mức chắc chắn: cao (docs chính thức, KIP, bài của tác giả EOS thống nhất).

### Phát hiện có nguồn
- Định nghĩa: "At most once: Messages are delivered once, and if there is a system failure, messages may be lost and are not redelivered." / "At least once: This means messages are delivered one or more times." / "Exactly once: ... each message is delivered once and only once." — [Kafka Message Delivery Guarantees, Confluent docs](https://docs.confluent.io/kafka/design/delivery-semantics.html) (bậc 1, không rõ ngày, nội dung bám Kafka design doc).
- Phía consumer: lưu vị trí rồi mới xử lý ⇒ at-most-once ("a consumer reads a set of messages, saves its position in the log, and then processes the messages"); xử lý rồi mới lưu vị trí ⇒ at-least-once ("reads a set of messages, processes the messages, and then saves its position") — [Confluent docs delivery semantics](https://docs.confluent.io/kafka/design/delivery-semantics.html) (bậc 1).
- Phía producer: at-least-once là mặc định vì retry sau khi ghi thật ra đã thành công sẽ tạo bản trùng; at-most-once làm bằng tắt retry phía producer và commit offset trước khi xử lý — [Confluent docs delivery semantics](https://docs.confluent.io/kafka/design/delivery-semantics.html) (bậc 1).
- Với hệ thống ngoài: "it can be challenging to coordinate the data the consumer is receiving and the consumer's position"; cách thường làm là two-phase commit hoặc lưu vị trí cùng chỗ với dữ liệu — [Confluent docs delivery semantics](https://docs.confluent.io/kafka/design/delivery-semantics.html) (bậc 1). Javadoc mô tả cách lưu offset ngoài Kafka: đặt `enable.auto.commit=false`, lưu offset của mỗi record cùng kết quả, khi khởi động/được gán partition thì `seek` tới offset đã lưu; làm vậy có thể "fully atomic and give 'exactly once' semantics" — [KafkaConsumer Javadoc](https://kafka.apache.org/39/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html) (bậc 1).
- Duplicate window điển hình: lỗi "after the insert into the database but before the commit" ⇒ consumer thay thế xử lý lại batch cuối — [KafkaConsumer Javadoc, Manual Offset Control](https://kafka.apache.org/39/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html) (bậc 1).
- Giới hạn EOS (Narkhede/Wang, tác giả tính năng): "exactly-once semantics is guaranteed within the scope of Kafka Streams' internal processing only"; gọi RPC tới store ngoài hay client tự đọc/ghi topic thì "The resulting side effects would not be guaranteed exactly once"; khi tua lại offset thì không thể "rollback the associated state in an external system, leading to incorrect results when the state update is not idempotent"; "Exactly-once processing is an end-to-end guarantee" — [Exactly-Once Semantics Are Possible: Here's How Kafka Does It, Confluent blog](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/) (bậc 1 — bài của chính người thiết kế, 2017-06-30, cập nhật 2025-03).
- Logic không tất định (phụ thuộc dịch vụ ngoài) chỉ được đảm bảo output nằm trong tập output hợp lệ, không phải một kết quả cố định — cùng nguồn trên (bậc 1).
- Giới hạn phía consumer của transaction: KIP-98 nói đảm bảo là "from the point of view of the producer"; "we cannot guarantee that all the messages of a committed transaction will be consumed all together" (lý do: compaction, xoá segment cũ, seek vào giữa transaction, consumer không đọc hết các partition tham gia) — [KIP-98](https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging) (bậc 1, adopted 0.11.0).
- Quan điểm chuyên gia: "not possible to guarantee exactly-once delivery of messages", nhưng exactly-once *processing* làm được bằng cách lưu idempotency key nguyên tử cùng kết quả xử lý — [On Idempotency Keys, Gunnar Morling](https://www.morling.dev/blog/on-idempotency-keys/) (bậc 2, 2025-11-25).

### Nhận định
- Bảng "vỡ ở đâu" để writer dùng:
  - *Producer side*: retry ⇒ trùng trong log (sửa bằng idempotent producer, xem mục 3); tắt retry ⇒ mất.
  - *Consumer side*: commit trước xử lý ⇒ mất khi crash; commit sau xử lý ⇒ trùng khi crash/rebalance giữa xử lý và commit; xử lý song song không đúng thứ tự mà commit offset cao nhất ⇒ mất (mục 2).
  - *Sink side*: Kafka transaction không bao được DB/HTTP ⇒ phải idempotent sink hoặc lưu offset trong cùng transaction DB.
- Kết luận thực dụng cho engine Go: mặc định thiết kế "at-least-once + sink idempotent" (effectively-once). Chỉ dùng transaction Kafka khi output là topic Kafka.

### Khoảng trống
- Không lấy được trang design doc gốc trên kafka.apache.org (URL redirect/404); dùng bản Confluent docs có nội dung tương đương. Truy vấn đã thử: fetch `kafka.apache.org/documentation/#semantics`, `kafka.apache.org/40/documentation/design.html`.
- Không truy được nguyên văn Kleppmann (DDIA) về end-to-end argument; chỉ có nguồn thứ cấp.

## 2. Chiến lược commit offset

### Kết luận ngắn
Auto commit chỉ là at-least-once khi mọi record của lần poll trước đã xử lý xong trước lần poll kế tiếp; với xử lý bất đồng bộ/song song phải chuyển sang commit thủ công (hoặc "mark/store rồi auto commit") và chỉ commit offset liên tục cao nhất đã xong. Rebalance là nguồn trùng chính, xử lý bằng commit trong callback revoke hoặc chặn rebalance khi đang xử lý. Mức chắc chắn: cao cho cơ chế (docs + source code client); trung bình cho phần tracking offset liên tục trong Go (chưa có nguồn Go chính thức, dựa trên Confluent Parallel Consumer).

### Phát hiện có nguồn
**Auto commit**
- Java: `enable.auto.commit=true` commit theo `auto.commit.interval.ms`; cảnh báo "you must consume all data returned from each call to poll(Duration) before any subsequent calls", nếu không committed offset có thể vượt vị trí đã xử lý ⇒ "missing records" — [KafkaConsumer Javadoc](https://kafka.apache.org/39/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html) (bậc 1).
- librdkafka (nền của confluent-kafka-go): `enable.auto.commit` mặc định `true`, `auto.commit.interval.ms` mặc định 5000; `enable.auto.offset.store` mặc định `true` = "Automatically store offset of last message provided to application" (tức offset được "store" ngay khi message *được giao* cho app, chưa chắc đã xử lý). Ghi chú ở `max.poll.interval.ms`: "It is recommended to set `enable.auto.offset.store=false` for long-time processing applications and then explicitly store offsets (using offsets_store()) *after* message processing, to make sure offsets are not auto-committed prior to processing has finished." — [librdkafka CONFIGURATION.md](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md) (bậc 1, master, xem 2026-11).
- franz-go: autocommit mặc định bật, `AutoCommitInterval` mặc định 5s — [franz-go config.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/config.go) (bậc 1). Chế độ mặc định chỉ commit những gì đã poll ở lần *trước*: comment source: "This one-poll lag is INTENTIONAL and is what makes default autocommit at-least-once: defaultRevoke commits head, so a revoke between poll N and N+1 commits none of poll N's records and the new owner re-reads them." — [franz-go consumer_group.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/consumer_group.go) (bậc 1).
- franz-go `GreedyAutoCommit`: commit mọi thứ đã poll, "may result in message loss if your application crashes" — [franz-go config.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/config.go) (bậc 1).
- franz-go `AutoCommitMarks` + `MarkCommitRecords`: "basically a halfway point between autocommitting and manually committing" — chỉ autocommit các record đã được đánh dấu; `MarkCommitRecords` "does not allow rewinds"; `CommitMarkedOffsets` cho commit đồng bộ các offset đã mark, khuyến nghị vòng poll → xử lý → mark → commit — [franz-go config.go / consumer_group.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/config.go) (bậc 1).

**Sync vs async**
- Java `commitSync` chặn tới khi thành công, lỗi không phục hồi được, hoặc hết timeout (`default.api.timeout.ms`); ném `CommitFailedException` khi partition không còn thuộc consumer, `RebalanceInProgressException` khi đang rebalance — [KafkaConsumer Javadoc](https://kafka.apache.org/39/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html) (bậc 1).
- Java `commitAsync`: "Any errors encountered are either passed to the callback (if provided) or discarded"; "Offsets committed through multiple calls to this API are guaranteed to be sent in the same order as the invocations"; callbacks gọi theo cùng thứ tự; commitAsync trước đó hoàn tất trước khi `commitSync` sau trả về. Javadoc không nói commitAsync có tự retry — cùng nguồn (bậc 1).
- franz-go `CommitRecords`: "If you do not want to wait for this function to complete before continuing processing records, you can call this function in a goroutine"; khi nhiều record cùng partition nó lấy epoch/offset lớn nhất — [franz-go consumer_group.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/consumer_group.go) (bậc 1).

**Rebalance & crash**
- franz-go `DisableAutoCommit` doc mô tả chính xác kịch bản trùng: member A commit offset 4, đã xử lý tới 30; partition chuyển sang B; nếu A không commit trong `OnPartitionsRevoked` thì B bắt đầu từ 4 ⇒ xử lý lại 4–29; tệ hơn, A có thể commit 30 *sau* khi B đã commit 50, "rewind" commit của B ⇒ trùng thêm 30–49 nếu rebalance tiếp. "not using it just means double processing, which for most workloads is fine since a simple group consumer is not EOS / transactional, only at-least-once" — [franz-go config.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/config.go) (bậc 1).
- franz-go mặc định quản lý group độc lập với việc poll: "A rebalance may occur at any moment. If you poll records, and then a rebalance happens, and then you commit, you may be committing to partitions you no longer own. This will result in duplicates." `BlockRebalanceOnPoll` + `AllowRebalance` chặn rebalance từ lúc poll tới khi gọi AllowRebalance, đánh đổi: "you put your group member at risk of waiting so long that the group member is kicked from the group because it exceeded the rebalance timeout"; Sarama mặc định chặn rebalance; có `OnPartitionsCallbackBlocked` làm tín hiệu "hurry up" — [franz-go config.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/config.go) (bậc 1).
- Java Javadoc (lưu offset ngoài Kafka): dùng `ConsumerRebalanceListener` — "when partitions are taken from a consumer the consumer will want to commit its offset for those partitions"; khi được gán thì tra offset đã lưu và seek — [KafkaConsumer Javadoc](https://kafka.apache.org/39/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html) (bậc 1).
- franz-go có `OnPartitionsRevoked` (rebalance bình thường, còn kịp commit) và `OnPartitionsLost` (mất partition do bị đá khỏi group, không commit được nữa); cả hai không được gọi `Close`/`LeaveGroup` đồng bộ bên trong — [franz-go config.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/config.go) (bậc 1).

**Commit khi xử lý song song, không đúng thứ tự (tracking contiguous offsets)**
- Confluent Parallel Consumer: chỉ commit "offsets for messages which have been successfully processed", "in order ... regardless of concurrency level or retries"; ba chế độ thứ tự: PARTITION ("At most only one message from any given input partition will be in flight"), KEY ("ensures process ordering by key (per partition)"), UNORDERED — [confluentinc/parallel-consumer README](https://github.com/confluentinc/parallel-consumer) (bậc 1, xem 2026-11).
- Cơ chế: commit "highest committable offset" (offset liên tục cao nhất đã xong); các offset đã xong *vượt* mốc đó được mã hoá (run-length hoặc BitSet, chọn cái nhỏ hơn, có thể nén zstd), base64, nhét vào commit metadata. Giới hạn "hardcoded limit of 4096 bytes (4 kb) per partition"; vượt thì bỏ map (mất lợi ích giảm replay); khi đạt 75% giới hạn thì ngừng nhận record mới (backpressure) — [parallel-consumer README, mục Offset Map/FAQ](https://github.com/confluentinc/parallel-consumer) (bậc 1).
- Sau failure/rebalance (chế độ KEY): "the system will not replay messages already marked as successful", nhưng "message replay may cause duplicates in external systems which is unavoidable" — cùng nguồn (bậc 1).

### Nhận định
- Không dùng auto commit "thuần" khi tách poll khỏi xử lý bằng goroutine/worker pool: offset có thể được commit trước khi worker xong ⇒ mất dữ liệu. Với confluent-kafka-go: `enable.auto.offset.store=false` + `StoreOffsets`/`StoreMessage` sau khi xử lý xong (giữ auto commit nền). Với franz-go: `AutoCommitMarks` + `MarkCommitRecords` sau khi xử lý xong, hoặc `DisableAutoCommit` + `CommitRecords`/`CommitUncommittedOffsets`.
- Với worker pool xử lý không đúng thứ tự trong một partition: KHÔNG được mark/commit record có offset lớn nhất vừa xong (franz-go `CommitRecords` lấy max ⇒ ngầm bỏ qua record chưa xong). Cần một "offset tracker" per partition: tập offset đã xong + con trỏ `committable` = offset liên tục cao nhất + 1; chỉ commit `committable`. Cần chặn số record "in flight" (giống ngưỡng 75% của Parallel Consumer) để một record kẹt không làm khoảng chưa commit phình vô hạn. Đây là suy luận từ thiết kế Parallel Consumer, chưa có thư viện Go chính thức được kiểm chứng.
- Dù tracker tốt đến đâu, crash vẫn có replay các offset sau mốc liên tục ⇒ sink vẫn phải idempotent.
- Commit đồng bộ khi revoke/shutdown, async (hoặc theo chu kỳ) trong luồng chính là mẫu phổ biến: async cho throughput, sync ở các điểm ranh giới để chắc chắn.

### Khoảng trống
- Chưa kiểm chứng thư viện Go nào triển khai contiguous-offset tracking + metadata encoding như Parallel Consumer (chưa search riêng, hết ngân sách tool call).
- Chưa xác minh hành vi commit/revoke cụ thể dưới protocol KIP-848 (thuộc góc concurrency/rebalance); chỉ có ghi chú franz-go rằng KIP-848 có thể chuyển partition "in under 200ms" (xem mục 3).
- Javadoc không nói rõ `commitAsync` có retry hay không.

## 3. Idempotency phía sink, idempotent producer, transactions/EOS và giới hạn

### Kết luận ngắn
Idempotent producer chống trùng do retry trong một session producer, theo từng partition; transaction (với `transactional.id`) cho ghi nguyên tử nhiều partition + commit offset trong cùng transaction, là nền của EOS read-process-write Kafka→Kafka. KIP-447 (2.5) cho phép một producer phục vụ nhiều input partition qua `sendOffsetsToTransaction(offsets, groupMetadata)`; KIP-890 (4.0) chặn "hanging/zombie transaction". Sink ngoài thì EOS không áp dụng: dùng upsert/dedup key/lưu offset trong transaction DB, hoặc chờ KIP-939 (2PC, trạng thái phát hành chưa xác nhận). Mức chắc chắn: cao cho KIP-98/447/890; thấp cho trạng thái phát hành KIP-939.

### Phát hiện có nguồn
**Idempotent producer**
- Mỗi producer được gán PID khi khởi tạo; broker theo dõi sequence number theo từng topic-partition, chỉ nhận write có sequence đúng bằng last+1; nhỏ hơn = trùng (bỏ qua), lớn hơn = mất message (fatal). "we can only guarantee idempotent production within a single producer session"; không có `transactional.id` thì restart nhận "a fresh PID" — [KIP-98](https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging) (bậc 1, 0.11.0).
- KIP-679: từ Kafka 3.0, producer Java mặc định `enable.idempotence=true`, `acks=all` (trước là false / acks=1); bug khiến mặc định không áp dụng ở 3.0.0 và 3.1.0, sửa ở 3.0.1, 3.1.1, 3.2.0 (KAFKA-13598) — [KIP-679](https://cwiki.apache.org/confluence/spaces/KAFKA/pages/165221843/KIP-679+Producer+will+enable+the+strongest+delivery+guarantee+by+default) (bậc 1); chi tiết bug qua kết quả search tổng hợp từ release note 3.2.0 trên mail-archive (bậc 2, chưa mở trực tiếp).
- librdkafka/confluent-kafka-go: `enable.idempotence` mặc định **false**; bật thì tự đặt `max.in.flight.requests.per.connection=5` (phải ≤5), `retries=INT32_MAX`, `acks=all` — [librdkafka CONFIGURATION.md](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md) (bậc 1, master 2026-11).
- Overhead: idempotence "negligible impact"; transaction với message 1 KB, transaction 100 ms: throughput producer giảm 3% so với producer at-least-once có thứ tự (acks=all, max.in.flight=1), ~20% so với cấu hình mặc định lúc đó; Kafka Streams EOS với commit interval 100 ms giảm 15–30% tuỳ cỡ message, commit 30 s thì không đo được overhead với message ≥1 KB — [Confluent blog EOS, Narkhede](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/) (bậc 1 về tuyên bố, số đo năm 2017).

**Transactions & read_committed**
- `transactional.id` giữ trạng thái qua restart; coordinator đảm bảo "Exactly one active producer with a given TransactionalId", fencing bằng tăng epoch ⇒ instance cũ (zombie) "is fenced off"; `transaction.timeout.ms` mặc định 60000, không vượt `max.transaction.timeout.ms` broker (mặc định 900000) — [KIP-98](https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging) (bậc 1).
- `read_committed` chỉ trả non-transactional hoặc transactional đã commit; đọc tới Last Stable Offset (LSO) = offset của message đầu tiên thuộc transaction còn mở; transaction marker chiếm offset nhưng không trả về ⇒ offset có "gap" — [KafkaConsumer Javadoc](https://kafka.apache.org/39/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html) (bậc 1); lag ở chế độ này tính theo LSO thay vì high watermark — [KIP-98](https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging) (bậc 1).
- Mặc định isolation khác nhau giữa client: Java mặc định `read_uncommitted` (KIP-98); librdkafka mặc định `read_committed` ([CONFIGURATION.md](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md), bậc 1); franz-go mặc định `ReadUncommitted`, đổi bằng `FetchIsolationLevel(kgo.ReadCommitted())` ([franz-go config.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/config.go), bậc 1).

**KIP-447 (Kafka 2.6 adopted; broker ≥2.5)**
- Vấn đề: trước KIP-447 phải tạo "a separate producer for every input partition" (như Kafka Streams cũ), tốn bộ nhớ/thread/kết nối khi nhiều partition. Giải pháp: `sendOffsetsToTransaction(offsets, ConsumerGroupMetadata)` mang generation ID, member ID, group instance ID; broker kiểm tra, sai thì "the client will be fenced immediately"; thêm lỗi `PENDING_TRANSACTION` để OffsetFetch chờ transaction treo. Offset phải lưu ở group coordinator Kafka; consumer không auto-commit hay commit thủ công riêng. Trạng thái "Adopted (2.6.0)"; client non-Streams sẽ lỗi nếu broker <2.5 — [KIP-447](https://cwiki.apache.org/confluence/display/KAFKA/KIP-447%3A+Producer+scalability+for+exactly+once+semantics) (bậc 1).
- franz-go luôn đặt `RequireStable=true` khi OffsetFetch (KIP-447), `RequireStableFetchOffsets()` giờ là no-op; "Any broker that supports KIP-848 necessarily supports KIP-447"; ghi chú KIP-848 "heartbeat-driven reassignment can move partitions in under 200ms" làm vấn đề commit marker chưa lan truyền nguy hiểm hơn nếu không có RequireStable — [franz-go docs/transactions.md](https://github.com/twmb/franz-go/blob/master/docs/transactions.md) và [config.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/config.go) (bậc 1, master 2026-11).

**KIP-890 (Transactions Server-Side Defense, Kafka 4.0)**
- Vấn đề: "hanging transactions" — LSO không tiến, chặn log cleaning cho compacted topic và làm consumer read_committed kẹt; nguyên nhân: message trễ của transaction đã abort, EndTxn marker trễ, client lỗi ghi trước khi add partition vào transaction. Giải pháp: tăng producer epoch sau mỗi commit/abort; add partition ngầm ở produce request đầu tiên; với client cũ, broker xác minh transaction đang mở trước khi ghi — [KIP-890](https://cwiki.apache.org/confluence/display/KAFKA/KIP-890%3A+Transactions+Server-Side+Defense) (bậc 1, cập nhật 2025-02-13).
- Docs Kafka 4.0: "Starting from Apache Kafka 4.0, Transactions Server Side Defense (KIP-890) brings a strengthened transactional protocol"; điều khiển bằng feature flag `transaction.version` (=2 để bật); "The producer clients do not need to be restarted"; "A producer will not upgrade mid-transaction, but on the start of the next transaction" — [Kafka 4.0 Transaction Protocol](https://kafka.apache.org/40/operations/transaction-protocol/) (bậc 1). Docs vừa nói "automatically enabled on the server since Apache Kafka 4.0" vừa nói phải đặt `transaction.version=2` cho cluster nâng cấp ⇒ hiểu là bật khi finalize nâng cấp 4.0 (upgrade guide, qua search) — chưa hoàn toàn rõ.

**KIP-939 (2PC với hệ thống ngoài)**
- Cho broker/producer tham gia two-phase commit do bên ngoài điều phối: thêm pha `PrepareTransaction` trước `EndTransaction`, API `initTransactions(keepPreparedTxn=true)`, `prepareTransaction()`, `completeTransaction(PreparedTxnState)`, bỏ transaction timeout cho transaction 2PC — [KIP-939](https://cwiki.apache.org/confluence/display/KAFKA/KIP-939:+Support+Participation+in+2PC) (bậc 1, qua tóm tắt search) và [Conduktor KIP explorer](https://kafka-options-explorer.conduktor.io/kip/939/) (bậc 3, "Accepted", nhắm 4.1, "full implementation unconfirmed").
- Release plan 4.1.0 liệt kê KIP-939 trạng thái "Accepted"; thông báo phát hành 4.1.0 không nhắc KIP-939 (có KIP-1050 "Consistent error handling for Transactions") — [Release Plan 4.1.0](https://cwiki.apache.org/confluence/display/KAFKA/Release+Plan+4.1.0) (bậc 1, qua search), [Apache Kafka 4.1.0 Release Announcement](https://kafka.apache.org/blog/2025/09/04/apache-kafka-4.1.0-release-announcement/) (bậc 1, 2025-09-04).

**EOS trong Go (franz-go)**
- franz-go gộp consumer + producer trong một client; `GroupTransactSession` "abstracts away the proper way to begin and end a transaction when consuming in a group, modifying records, and producing (EOS)". Khi rebalance xảy ra trước khi kết thúc transaction, nó chọn *abort* thay vì chặn rebalance; `End(ctx, commit)` "committing if commit is true, if the group did not rebalance since the transaction began, and if committing offsets is successful. If any of these conditions are false, this aborts"; lỗi trả về không retry được. Không gọi `End` đồng bộ trong `OnPartitionsRevoked/Lost` (deadlock) — [franz-go txn.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/txn.go) (bậc 1).
- Biện pháp an toàn thêm: heartbeat thành công ngay trước commit; mặc định transaction timeout < session timeout; nếu broker <2.5 thì ngủ 500 ms sau commit (heuristic, "strongly recommended to use a 2.5+ cluster") — [franz-go docs/transactions.md](https://github.com/twmb/franz-go/blob/master/docs/transactions.md) (bậc 1). README liệt kê hỗ trợ KIP-98 và KIP-447 — [franz-go README](https://github.com/twmb/franz-go) (bậc 1).

**Idempotency phía sink (sink ngoài)**
- Idempotency key: UUIDv4 buộc nhớ mọi key đã thấy (hoặc hết hạn key và chấp nhận rủi ro trùng); UUIDv7/ULID có timestamp để nhận biết key "quá cũ"; khoá đơn điệu tăng chỉ cần lưu key lớn nhất — "same or a lower" key coi là trùng; **offset Kafka theo partition là khoá đơn điệu tự nhiên**: lưu offset mới nhất mỗi partition, bỏ mọi record ≤ offset đó; tốn không gian hằng số — [On Idempotency Keys, Morling](https://www.morling.dev/blog/on-idempotency-keys/) (bậc 2, 2025-11-25).
- Thao tác tự nhiên idempotent: upsert, update có điều kiện (`UPDATE ... WHERE version = expected_version`) — tổng hợp từ [Conduktor: Transactional Outbox](https://conduktor.io/blog/transactional-outbox-pattern-database-kafka) (bậc 2/3, không rõ ngày).

### Nhận định
- Bản đồ chọn kỹ thuật theo sink:
  - Kafka→Kafka: transaction (franz-go `GroupTransactSession`, confluent-kafka-go transactional producer + `SendOffsetsToTransaction`) + consumer downstream `read_committed`. Đánh đổi: latency tăng theo chu kỳ commit transaction (downstream chỉ thấy dữ liệu khi commit), throughput giảm vài % tới vài chục % nếu transaction quá ngắn.
  - Kafka→DB quan hệ: lưu offset (topic, partition, offset) trong bảng của chính DB, cùng transaction với dữ liệu; khi được gán partition thì đọc offset từ DB và seek (franz-go: `AdjustFetchOffsetsFn` hoặc `OnPartitionsAssigned` + `SetOffsets`; confluent-kafka-go: `Assign` với offset). Đây là exactly-once thật cho sink đó. Hoặc đơn giản hơn: upsert theo khoá nghiệp vụ + commit Kafka sau.
  - Kafka→HTTP/API ngoài: chỉ at-least-once + idempotency key gửi kèm (vd `topic-partition-offset` hoặc event ID); nếu API không hỗ trợ key thì trùng là không tránh được.
- Bật idempotent producer rõ ràng khi dùng confluent-kafka-go (mặc định false), và đặt isolation level rõ ràng khi dùng franz-go (mặc định read_uncommitted) — hai client Go có mặc định ngược nhau với Java ở hai điểm này.
- KIP-890 giảm rủi ro chứ không thay đổi API; với cluster 4.x nên đảm bảo `transaction.version=2` đã bật.

### Khoảng trống
- Chưa xác nhận KIP-939 đã ship ở bản nào (4.1/4.2) và trạng thái preview hay GA; truy vấn: "KIP-939 two-phase commit...", "Apache Kafka 4.1 release KIP-939 2PC preview".
- Chưa đọc trực tiếp API transaction của confluent-kafka-go (`InitTransactions`, `SendOffsetsToTransaction`, `CommitTransaction`) trên pkg.go.dev; tên API dựa trên kiến thức chung, writer nên ghi là cần kiểm tra.
- Chưa có số đo overhead EOS mới (sau 2017) hoặc riêng cho franz-go.

## 4. Retry, retry topic không chặn, DLQ, poison message, outbox/inbox

### Kết luận ngắn
Retry tại chỗ (blocking) giữ thứ tự nhưng chặn cả partition; retry topic (non-blocking) giữ luồng chính chạy nhưng phá thứ tự; DLQ là điểm cuối để cô lập poison message. Nếu cần thứ tự theo key, phải "đi theo" key đang retry (mọi event mới của key đó cũng vào đường retry). Outbox giải dual-write ở phía ghi, inbox/dedup table giải trùng ở phía đọc. Mức chắc chắn: cao (Uber, Confluent, Debezium là nguồn gốc của các pattern).

### Phát hiện có nguồn
- Uber (Ning Xia, Insurance Engineering, 2018-02-16): retry trong consumer chặn tiến độ vì "Without a success response, the Kafka consumer will not commit a new offset" ⇒ message lỗi bị đọc lại mãi, message mới phải chờ; khó lấy metadata retry. Thiết kế: chuỗi retry topic, mỗi tầng một nhóm consumer riêng; handler lỗi thì publish sang retry topic kế tiếp, trả true và commit offset gốc; tầng cuối là dead letter topic. Mỗi tầng có độ trễ tăng dần (leaky bucket) — "not so much retry queues as they are delayed processing queues"; "handler invocation will occur at least after the configured timeout but possibly later". DLQ hỗ trợ list, purge, merge (re-publish vào retry topic đầu tiên, tách khỏi traffic live). Đánh đổi: phải chịu xử lý không đúng thứ tự, consumer phải idempotent; nhiều topic tăng chi phí quản lý — [Building Reliable Reprocessing and Dead Letter Queues with Apache Kafka, Uber](https://www.uber.com/blog/reliable-reprocessing/) (bậc 1, 2018-02-16).
- Confluent (Gerardo Villeda, 2021-05-21) – 4 pattern: (1) Stop on error — dừng tới khi có người can thiệp, hợp với luồng phải đúng thứ tự như CDC; (2) DLQ — event không xử lý được (vd malformed) vào topic lỗi, không retry; (3) Retry topic + ứng dụng retry riêng — "Events are not guaranteed to be processed in the same sequence received in the source topic"; (4) Giữ thứ tự bằng redirect topic — ứng dụng chính nhớ (in-memory) các item đang có event trong retry, event mới cùng item cũng chuyển sang retry; ứng dụng retry thành công thì phát tombstone vào redirect topic để ứng dụng chính xoá khỏi store; khôi phục store bằng replay redirect topic; ví dụ tồn kho: giảm trước tăng có thể gây đặt hàng sai — [Error Handling Patterns for Apache Kafka Applications, Confluent blog](https://www.confluent.io/blog/error-handling-patterns-in-kafka/) (bậc 2, 2021-05-21).
- Parallel Consumer: lỗi được bắt, log và đưa record vào hàng đợi để retry sau, có delay/backoff tuỳ chỉnh; "messages will continue to be retried forever as long as an exception continues to be thrown" (chưa có terminal error); muốn bỏ qua thì không ném exception; ở chế độ PARTITION record lỗi "will block progress", KEY/UNORDERED thì không — [parallel-consumer README](https://github.com/confluentinc/parallel-consumer) (bậc 1).
- Kafka Streams có DLQ tích hợp từ Kafka 4.2 (KIP-1034); mặc định không gửi DLQ; topic DLQ không tự tạo; tên config giữa KIP và upgrade guide lệch nhau (`errors.dead.letter.queue.topic.name` vs `errors.deadletterqueue.topic.name`) — [KIP-1034](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1034%3A+Dead+letter+queue+in+Kafka+Streams) (bậc 1, qua search), [Kafka 4.2 Streams upgrade guide](https://kafka.apache.org/42/streams/upgrade-guide/) (bậc 1, qua search). Chỉ để tham chiếu: Kafka core không có retry/DLQ cho consumer thường; client Go phải tự làm.
- Outbox (Debezium Outbox Event Router): bảng outbox mặc định `id` (uuid), `aggregatetype`, `aggregateid`, `type`, `payload` (jsonb); `id` được đặt vào header `id` của event, "You can use this ID, for example, to remove duplicate messages"; aggregate ID làm message key — [Debezium Outbox Event Router docs](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) (bậc 1, stable, xem 2026-11).
- Outbox chỉ cho at-least-once (relay có thể publish rồi crash trước khi đánh dấu ⇒ publish lại); inbox: consumer insert (consumer name, event ID) vào bảng có unique constraint trong cùng transaction với cập nhật nghiệp vụ, trùng khoá = đã xử lý — [Conduktor: Transactional Outbox](https://conduktor.io/blog/transactional-outbox-pattern-database-kafka) (bậc 2/3, không rõ ngày; cần xem như mô tả pattern, không phải bằng chứng).

### Nhận định
- Phân loại lỗi trước khi chọn đường đi (để engine Go có một "error classifier"):
  - *Poison/không thể xử lý* (deserialize lỗi, schema sai, vi phạm validate): không retry, đi thẳng DLQ kèm header lỗi (topic/partition/offset gốc, lý do, số lần thử, timestamp).
  - *Lỗi tạm thời* (timeout DB/API, 5xx, throttling): retry tại chỗ vài lần với backoff ngắn; nếu vẫn lỗi thì sang retry topic (non-blocking) hoặc pause partition (blocking, giữ thứ tự).
  - *Lỗi hệ thống downstream sập toàn bộ*: không nên đẩy hàng loạt vào retry/DLQ; nên pause consume (circuit breaker) — vì mọi message đều sẽ lỗi. (Suy luận; chưa có nguồn bậc 1 cụ thể.)
- Ma trận thứ tự vs liveness:
  - Cần thứ tự tuyệt đối theo partition (CDC, ledger): stop-on-error / blocking retry vô hạn + alert.
  - Cần thứ tự theo key: pattern 4 của Confluent (chặn key đang retry), hoặc worker pool theo key giữ record lỗi trong hàng của key đó.
  - Không cần thứ tự: retry topic kiểu Uber + DLQ.
- Retry topic trong Go: delay thực hiện bằng cách đọc timestamp/header "not-before", nếu chưa tới hạn thì pause partition retry đó (franz-go `PauseFetchPartitions`/`ResumeFetchPartitions`) thay vì `time.Sleep` chặn vòng poll quá `max.poll.interval`/rebalance timeout. (Suy luận; tên API franz-go chưa đối chiếu trong lần research này.)
- Ghi sang retry/DLQ rồi commit offset gốc là một "dual write" Kafka→Kafka: muốn không mất/không trùng thì produce sang DLQ phải thành công (đợi ack) *trước* khi mark/commit offset gốc; hoặc đặt cả hai trong transaction.
- Outbox hữu ích khi engine consumer vừa cập nhật DB vừa phải phát event mới; inbox/dedup table là cách hiện thực "sink idempotent" chung cho mọi loại nghiệp vụ không có upsert tự nhiên.

### Khoảng trống
- Chưa tìm được hướng dẫn chính thức về retry topic/DLQ dành cho Go (Watermill, Redpanda Connect có cơ chế poison queue nhưng thuộc góc hệ sinh thái Go, chưa kiểm chứng).
- Chưa có số liệu thực tế về tỷ lệ message vào DLQ hay chi phí vận hành retry topic.

## Gợi ý Go tổng hợp (cho writer)

### Kết luận ngắn
franz-go cung cấp đủ "núm vặn" cho cả ba mức (autocommit mặc định at-least-once, `AutoCommitMarks`, commit thủ công, `BlockRebalanceOnPoll`, `GroupTransactSession` cho EOS); confluent-kafka-go dùng mô hình librdkafka "store offset rồi auto commit". Mức chắc chắn: cao cho các API đã trích từ source/docs; trung bình cho các đoạn mã phác hoạ (chưa chạy).

### Phát hiện có nguồn
- franz-go option liên quan: `DisableAutoCommit`, `AutoCommitInterval` (mặc định 5s), `AutoCommitMarks`, `GreedyAutoCommit`, `BlockRebalanceOnPoll`/`AllowRebalance`, `OnPartitionsRevoked`, `OnPartitionsLost`, `OnPartitionsCallbackBlocked`, `AdjustFetchOffsetsFn`, `FetchIsolationLevel(ReadCommitted())`, `InstanceID` (static membership; khi đóng không gửi LeaveGroup) — [franz-go config.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/config.go) (bậc 1, v1.22.3 trên master, 2026-11).
- `PollFetches` doc: "If you are group consuming, a rebalance can happen under the hood while you process the returned fetches. This can result in duplicate work, and you may accidentally commit to partitions that you no longer own." — [franz-go consumer.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/consumer.go) (bậc 1).
- confluent-kafka-go: test chính thức đặt `"enable.auto.offset.store": false, // permit StoreOffsets()` rồi gọi `StoreOffsets`/`StoreMessage` — [confluent-kafka-go consumer_test.go (fork mirror)](https://github-redirect.dependabot.com/SourceFellows/confluent-kafka-go/blob/9d526f99762c5a3a3923794563bc43b785f56686/kafka/consumer_test.go) (bậc 3 vì là mirror; cơ chế được librdkafka docs xác nhận, bậc 1).

### Nhận định
- Phác hoạ at-least-once với worker và mark (franz-go), để writer dùng làm ví dụ (chưa chạy thử):
  ```go
  cl, _ := kgo.NewClient(
      kgo.SeedBrokers(brokers...),
      kgo.ConsumerGroup("engine"),
      kgo.ConsumeTopics("events"),
      kgo.AutoCommitMarks(),                 // chỉ commit record đã Mark
      kgo.FetchIsolationLevel(kgo.ReadCommitted()),
      kgo.OnPartitionsRevoked(func(ctx context.Context, cl *kgo.Client, _ map[string][]int32) {
          // đợi worker của các partition bị thu hồi xong (drain), rồi commit đồng bộ
          _ = cl.CommitMarkedOffsets(ctx)
      }),
  )
  for {
      fs := cl.PollFetches(ctx)
      fs.EachRecord(func(r *kgo.Record) {
          if err := process(r); err != nil { sendToRetryOrDLQ(r, err) } // phải ack trước khi mark
          cl.MarkCommitRecords(r) // xử lý tuần tự trong partition nên offset liên tục
      })
  }
  ```
  Khi xử lý song song trong partition, thay `MarkCommitRecords(r)` bằng một offset tracker chỉ mark offset liên tục cao nhất.
- Phác hoạ EOS Kafka→Kafka: `sess, _ := kgo.NewGroupTransactSession(kgo.TransactionalID(id), kgo.ConsumerGroup(g), kgo.FetchIsolationLevel(kgo.ReadCommitted()), ...)`; vòng: `PollFetches` → `sess.Begin()` → produce kết quả → `committed, err := sess.End(ctx, kgo.TryCommit)`; nếu `committed == false` thì dữ liệu sẽ được đọc lại (abort do rebalance). Tên hằng `kgo.TryCommit`/`TransactionalID` theo ví dụ `examples/transactions/eos` của franz-go — writer nên đối chiếu lại.
- Bảng chọn nhanh:
  | Bài toán | Delivery | Commit | Sink |
  |---|---|---|---|
  | Metrics/log, mất ít chấp nhận được, cần latency thấp | at-most hoặc at-least | autocommit mặc định | ghi thẳng |
  | Cập nhật DB nghiệp vụ | at-least-once | mark/store sau xử lý, commit sync khi revoke | upsert / version check / inbox |
  | Kafka→Kafka (enrich, filter, route) cần không trùng | exactly-once | trong transaction (`sendOffsetsToTransaction` / `GroupTransactSession`) | topic, downstream `read_committed` |
  | Ghi DB cần exactly-once thật | exactly-once (cho sink đó) | lưu offset trong DB cùng transaction, seek khi assign | DB |
  | Gọi HTTP bên thứ ba | at-least-once | sau khi nhận 2xx | idempotency key `topic/partition/offset` hoặc event ID |

### Khoảng trống
- Các đoạn mã chưa được biên dịch/chạy; tên `kgo.TryCommit`, `kgo.TransactionalID`, `PauseFetchPartitions` chưa đối chiếu trong lần research này.

## Truy vấn đã chạy
- WebFetch kafka.apache.org/documentation/#semantics (redirect, thất bại)
- WebFetch kafka.apache.org/40/documentation/design.html (404)
- WebFetch KIP-447, KIP-890, KIP-98 trên cwiki
- KIP-890 transactions server-side defense released Kafka 4.0 transaction version 2 (standard)
- KIP-939 two-phase commit Kafka transactions external database (standard)
- WebFetch kafka.apache.org/40/operations/transaction-protocol/
- WebFetch kafka-options-explorer.conduktor.io/kip/939/
- kafka documentation design "message delivery semantics" at most once at least once (standard)
- WebFetch docs.confluent.io/kafka/design/delivery-semantics.html
- KIP-679 producer enable.idempotence default true acks=all Kafka 3.0 (standard)
- Uber reliable reprocessing kafka retry topics dead letter queue (standard)
- WebFetch uber.com/blog/reliable-reprocessing/
- WebFetch confluent.io/blog/error-handling-patterns-in-kafka/
- WebFetch pkg.go.dev franz-go kgo (bị cắt) → tải source franz-go (config.go, consumer.go, consumer_group.go, txn.go, docs/transactions.md, README, CHANGELOG) từ GitHub raw
- WebFetch KafkaConsumer Javadoc 3.9 (2 lần, offset 0 và 100000)
- WebFetch github.com/confluentinc/parallel-consumer (2 lần)
- WebFetch Confluent blog EOS (Narkhede) (3 lần, gồm 1 URL redirect)
- confluent-kafka-go enable.auto.offset.store false StoreOffsets at-least-once (standard)
- transactional outbox pattern Debezium Kafka inbox idempotent consumer (standard)
- Tải librdkafka CONFIGURATION.md
- Apache Kafka 4.1 release KIP-939 2PC preview (standard)
- WebFetch Debezium outbox-event-router docs
- WebFetch Kafka 4.1.0 release announcement
- KIP-1034 dead letter queue Kafka Streams release (standard)
- Kleppmann exactly-once end-to-end argument idempotence request ID designing data-intensive applications (standard)
- WebFetch morling.dev/blog/on-idempotency-keys/
