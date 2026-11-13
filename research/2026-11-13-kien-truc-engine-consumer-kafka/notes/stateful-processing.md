# Stateful stream processing: window, thời gian, state store và cách dựng trong Go

Ghi chú của góc "stateful processing" (câu hỏi phụ 3 trong brief). Kafka Streams và Flink chỉ dùng làm thiết kế tham khảo; trọng tâm là cái gì phải tự làm khi viết engine bằng Go.

## 1. Window, aggregation, join: là gì, khi nào cần

### Kết luận ngắn
Có bốn loại window chuẩn: tumbling, hopping, sliding và session. Join chia làm hai nhóm. Join stream-stream luôn phải có window, vì nếu không thì state phình vô hạn. Join stream-table không cần window nhưng bắt buộc co-partitioning. Mức chắc chắn: **cao**, vì định nghĩa khớp nhau giữa docs Kafka Streams 4.3, Flink 2.3 và Akidau.

### Phát hiện có nguồn
- **Tumbling:** "A tumbling window is a hopping window whose window size is equal to its advance interval." Các window không chồng lên nhau, nên mỗi record thuộc đúng một window. Ví dụ: window 5 phút. — [Kafka Streams DSL API 4.3](https://kafka.apache.org/43/streams/developer-guide/dsl-api/) (bậc 1, 2026)
- **Hopping:** window có kích thước cố định, chồng lên nhau, được định nghĩa bằng size và advance, nên một record thuộc nhiều window. Ví dụ size 5 phút, advance 1 phút. Cận dưới inclusive, cận trên exclusive, căn theo epoch. Với size 5000ms và advance 3000ms ta có `[0;5000),[3000;8000),...`. — [Kafka Streams DSL API 4.3](https://kafka.apache.org/43/streams/developer-guide/dsl-api/) (bậc 1, 2026)
- **Sliding (Kafka Streams):** dùng cho `JoinWindows` và `SlidingWindows`. Hai record chung một window nếu timestamp của chúng cách nhau không quá window size. Window căn theo timestamp của record chứ không theo epoch, và cả hai cận đều inclusive. Ví dụ: `SlidingWindows.ofTimeDifferenceAndGrace(10 min, 30 min)`. — [Kafka Streams DSL API 4.3](https://kafka.apache.org/43/streams/developer-guide/dsl-api/) (bậc 1, 2026)
- Lưu ý thuật ngữ: Akidau và Flink gọi "sliding window" là loại có "a fixed length and a fixed period", tức tương đương *hopping* của Kafka Streams. — [Streaming 101, Tyler Akidau](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/) (bậc 2, 2015-08-05); Flink ghi "elements are assigned to multiple windows" — [Flink Windows 2.3](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/) (bậc 1, 2026)
- **Session:** gồm các đoạn hoạt động, ngăn cách nhau bằng một khoảng nghỉ (inactivity gap). Sự kiện nằm trong gap được gộp vào session hiện có, sự kiện ngoài gap mở session mới. Session theo từng key và có kích thước thay đổi, ví dụ `SessionWindows.ofInactivityGapWithNoGrace(5 min)`. — [Kafka Streams DSL API 4.3](https://kafka.apache.org/43/streams/developer-guide/dsl-api/) (bậc 1, 2026). Flink "merges windows together if they are closer to each other than the defined gap" — [Flink Windows 2.3](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/) (bậc 1, 2026). Akidau: "the location and sizes of the windows are a direct consequence of the input data themselves" — [Streaming 102](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-102/) (bậc 2, 2016-01-20)
- Window được tính theo từng key: "Windowing lets you control how to group records that have the same key." — [Kafka Streams Core Concepts 4.3](https://kafka.apache.org/43/streams/core-concepts/) (bậc 1, 2026). Ở Flink, nếu không `keyBy` thì `windowAll` chạy "by a single task", tức parallelism bằng 1. — [Flink Windows 2.3](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/) (bậc 1, 2026)
- **Các loại join trong Kafka Streams:**

  | Join | Có window không |
  |---|---|
  | KStream-KStream | có (bắt buộc) |
  | KStream-KTable, KStream-GlobalKTable, KTable-KTable, KTable-KTable foreign-key | không |
  | KTable-GlobalKTable | không hỗ trợ |

  KStream-KStream luôn có window, vì nếu không thì join store sẽ tăng vô hạn. Kết quả left/outer cho record không khớp được phát ra sau khi grace period hết. API cũ `JoinWindows.of(...).grace(...)` có thể phát kết quả left/outer sớm, gây kết quả giả (spurious). — [Kafka Streams DSL API 4.3](https://kafka.apache.org/43/streams/developer-guide/dsl-api/) (bậc 1, 2026)
- **Emit final results:** `suppress(Suppressed.untilWindowCloses(unbounded()))` không phát gì cho tới khi window đóng, rồi phát kết quả cuối đúng một lần. Ví dụ trong docs: user U có 10 event trong khoảng 09:00–10:00, grace 10 phút, thì downstream nhận đúng một record giá trị 10 lúc 10:10. Buffer của suppress không giữ header. — [Kafka Streams DSL API 4.3](https://kafka.apache.org/43/streams/developer-guide/dsl-api/) (bậc 1, 2026)
- Mô hình "4 câu hỏi" của Dataflow: *What* (phép biến đổi), *Where* (window), *When* (watermark và trigger) và *How* (accumulation). Có ba accumulation mode là discarding, accumulating, và accumulating & retracting ("also produces independent retractions for the previous pane(s)"). — [Streaming 102](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-102/) (bậc 2, 2016-01-20)

### Nhận định
- **Nhận định:** bảng chọn nhanh (ví dụ do agent đặt ra):
  - "Số đơn hàng mỗi 5 phút" dùng tumbling.
  - "Trung bình 5 phút gần nhất, cập nhật mỗi phút" dùng hopping (5m/1m). Lưu ý mỗi event ghi vào 5 window, nên state và số lần ghi tăng 5 lần.
  - "Phát hiện 2 sự kiện của cùng user cách nhau ≤ 10 giây" dùng sliding hoặc join window.
  - "Phiên duyệt web của user, kết thúc khi im lặng 30 phút" dùng session.
  - "Enrich click bằng hồ sơ user" dùng stream-table join, với bảng user là KTable hoặc changelog compacted.
  - "Khớp đơn hàng với thanh toán đến trong vòng 1 giờ" dùng stream-stream join có window 1 giờ.
- **Nhận định:** session window khó tự viết nhất, vì một event đến trễ có thể nối hai session đang tách rời thành một (merge), nên phải xoá hai bản ghi cũ và ghi một bản mới vào store. Hopping với tỷ lệ size/advance lớn thì tốn state, nên cân nhắc pre-aggregate theo các "slice" nhỏ rồi gộp lại.
- **Nhận định:** cần quyết định từ đầu là phát kết quả liên tục (mỗi event một bản cập nhật, sink phải chịu được upsert) hay chỉ phát khi window đóng (giống suppress, độ trễ bằng window cộng grace).

### Khoảng trống
- Chưa đọc được phần mô tả `emitStrategy(ON_WINDOW_CLOSE)` (KIP-825) trong docs. Trang DSL quá dài và đoạn đã đọc không có nó.

## 2. Event-time vs processing-time, watermark, dữ liệu trễ hoặc sai thứ tự

### Kết luận ngắn
Muốn trả lời câu hỏi theo thời gian thực của sự kiện thì phải dùng event-time. Khi đó cần một "đồng hồ dữ liệu", là stream-time ở Kafka Streams hoặc watermark ở Flink, cộng một ngưỡng chịu trễ (grace hay allowed lateness). Quá ngưỡng thì record bị bỏ hoặc đẩy ra side output. Mức chắc chắn: **cao**.

### Phát hiện có nguồn
- Định nghĩa: "Event time, which is the time at which events actually occurred", còn "Processing time, which is the time at which events are observed in the system". Độ lệch giữa hai loại "is not only non-zero, but often a highly variable function". Nếu window theo processing time thì "some of your event time data are going to end up in the wrong processing time windows". — [Streaming 101, Akidau](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/) (bậc 2, 2015-08-05)
- Kafka Streams phân biệt ba loại thời gian: event time, processing time và ingestion time ("stored in a topic partition by a Kafka broker"). Timestamp được gán qua interface `TimestampExtractor`. — [Kafka Streams Core Concepts 4.3](https://kafka.apache.org/43/streams/core-concepts/) (bậc 1, 2026)
- **Stream-time (Kafka Streams):** là "data-driven time", chỉ tiến lên khi có record mới đến processor. Lateness được tính bằng `stream_time - record_timestamp`. Window vẫn nhận record cho tới khi `stream_time >= window_end + grace_period`. — [Kafka Streams Core Concepts 4.3](https://kafka.apache.org/43/streams/core-concepts/) (bậc 1, 2026); [Windows Javadoc 3.1](https://kafka.apache.org/31/javadoc/org/apache/kafka/streams/kstream/Windows.html) (bậc 1)
- **Grace period:** "controls how long Kafka Streams will wait for out-of-order data records for a given window. If a record arrives after the grace period of a window has passed, the record is discarded." Ví dụ: window 09:00–10:00 với grace 10 phút nhận record trễ tới 10:10. — [Core Concepts 4.3](https://kafka.apache.org/43/streams/core-concepts/), [DSL API 4.3](https://kafka.apache.org/43/streams/developer-guide/dsl-api/) (bậc 1, 2026)
- Giá trị mặc định đã đổi theo phiên bản. Ở Kafka 2.1 grace mặc định là 24 giờ, nay đã deprecated. Từ 3.x phải chọn tường minh: `ofSizeWithNoGrace` nghĩa là grace bằng 0, nên mọi record đến sau khi window kết thúc đều bị bỏ. — [TimeWindows Javadoc 3.5.2](https://kafka.apache.org/35/javadoc/org/apache/kafka/streams/kstream/TimeWindows.html), [Windows Javadoc 2.1](https://kafka.apache.org/21/javadoc/org/apache/kafka/streams/kstream/Windows.html) (bậc 1)
- **Watermark (Flink):** "A Watermark(t) declares that event time has reached time t in that stream", tức không còn phần tử nào có timestamp ≤ t. Với operator nhiều input, "current event time is the minimum of its input streams' event times". — [Flink Timely Stream Processing 2.3](https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time/) (bậc 1, 2026)
- `forBoundedOutOfOrderness(d)` tính watermark bằng timestamp lớn nhất đã thấy trừ đi d. Một input không có event (idle) giữ watermark đứng yên vì watermark lấy min, nên cần `withIdleness(Duration.ofMinutes(1))`. Watermark được sinh "inside the Kafka consumer, per Kafka partition" rồi mới merge. Watermark alignment tạm dừng đọc những partition chạy quá xa phía trước. — [Flink Generating Watermarks 2.3](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/event-time/generating_watermarks/) (bậc 1, 2026)
- **Allowed lateness (Flink):** mặc định bằng 0, tức "elements that arrive behind the watermark will be dropped". Record trễ trong ngưỡng gây "late firings", và kết quả đó phải coi là bản cập nhật. Có thể lấy dữ liệu bị bỏ qua side output (`getSideOutput(lateOutputTag)`). State của window bị xoá khi watermark vượt `window_end + allowed_lateness`. — [Flink Windows 2.3](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/) (bậc 1, 2026)
- Akidau chia watermark làm hai loại. *Perfect* nghĩa là "there is no such thing as late data". *Heuristic* thì "may sometimes be wrong, which will lead to late data". Allowed lateness là "placing a bound on how late any given record may be", và quá giới hạn thì "all state for the window is discarded". Trigger có ba kiểu: early (kết quả tạm), on-time (khi watermark qua cuối window) và late. — [Streaming 102](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-102/) (bậc 2, 2016-01-20)

### Nhận định
- **Nhận định:** với engine Go tự viết, cách đơn giản và đủ dùng là bắt chước stream-time của Kafka Streams: mỗi partition (task) giữ `maxSeenTs`, rồi đóng window khi `maxSeenTs - grace ≥ window_end`. Chỉ cần watermark kiểu Flink (lấy min qua nhiều nguồn) khi một operator gom dữ liệu từ nhiều partition hoặc topic, ví dụ join hai topic. Lúc đó phải xử lý partition idle, nếu không window sẽ không bao giờ đóng.
- **Nhận định:** stream-time "đứng yên khi không có dữ liệu". Partition thưa event có thể giữ window mở rất lâu. Nếu cần đóng đúng giờ, phải có thêm timer theo wall-clock (giống punctuator `WALL_CLOCK_TIME` của Kafka Streams), và chấp nhận đánh đổi về tính đúng.
- **Nhận định:** đừng âm thầm bỏ record trễ. Hãy đẩy chúng ra một topic "late" (tương đương side output) và đếm bằng metric, để biết nên tăng grace hay không.
- **Nhận định:** timestamp nên lấy từ payload (thời điểm sinh event). Timestamp của Kafka record chỉ dùng được nếu producer set đúng `CreateTime`. Nếu topic dùng `LogAppendTime` thì đó là ingestion time.

### Khoảng trống
- Không có số liệu thực nghiệm về mức out-of-orderness điển hình, để chọn grace bao nhiêu. Việc này phụ thuộc workload và cần đo trên dữ liệu thật.

## 3. State store: cục bộ nhúng hay bên ngoài; co-partitioning; changelog, checkpoint, phục hồi, standby

### Kết luận ngắn
Thiết kế chuẩn (Kafka Streams, Samza, goka) như sau: state đặt **cục bộ** theo từng partition, trong một store nhúng (RocksDB, Pebble, LevelDB, Badger), và được sao lưu bằng **changelog topic compacted**. Khi crash hoặc rebalance, state được phục hồi bằng cách replay changelog. Standby replica giúp rút ngắn thời gian phục hồi. Store bên ngoài như Redis hay Cassandra đơn giản hơn khi scale, nhưng chậm hơn khoảng 100 lần trong số đo của LinkedIn. Mức chắc chắn: **cao** cho kiến trúc, **trung bình** cho con số hiệu năng (một nguồn, năm 2016, I/O đồng bộ).

### Phát hiện có nguồn
- **Task và partition:** "Kafka Streams creates a fixed number of tasks based on the input stream partitions". "The assignment of partitions to tasks never changes so that each task is a fixed unit of parallelism". Các thread "no shared state". — [Kafka Streams Architecture 4.3](https://kafka.apache.org/43/streams/architecture/) (bậc 1, 2026)
- **Changelog:** mỗi store "maintains a replicated changelog Kafka topic in which it tracks any state updates", và "Log compaction is enabled on the changelog topics so that old data can be purged safely". Khi phục hồi, state được dựng lại "by replaying the corresponding changelog topics prior to resuming the processing". — [Kafka Streams Architecture 4.3](https://kafka.apache.org/43/streams/architecture/) (bậc 1, 2026)
- **Standby replica:** là bản sao đầy đủ của state trên instance khác. "Standby tasks will increase the likelihood that a caught-up instance exists". Khi chuyển task, Streams ưu tiên gán vào instance đã có standby. — [Kafka Streams Architecture 4.3](https://kafka.apache.org/43/streams/architecture/) (bậc 1, 2026)
- **Thời gian phục hồi là vấn đề thật:** KIP-441 ghi task phải "catch it up to the head of its changelog before beginning to process", và "some task can get hung up for hours while it rebuilds its state stores". Giải pháp là cấp thêm replica "khởi động ấm" (warmup) trên instance đích trước khi chuyển quyền sở hữu, với `acceptable.recovery.lag` mặc định 10.000 offset, `max.warmup.replicas` mặc định 2 và `probing.rebalance.interval.ms` mặc định 10 phút. — [KIP-441](https://cwiki.apache.org/confluence/display/KAFKA/KIP-441%3A+Smooth+Scaling+Out+for+Kafka+Streams) (bậc 1, không rõ ngày)
- **Co-partitioning:** join kiểu equi đòi hai topic có cùng số partition và mọi producer dùng cùng partitioner. Streams kiểm tra số partition lúc chạy và ném `TopologyBuilderException` nếu lệch, nhưng **không kiểm tra được** chiến lược partition. Join với GlobalKTable và foreign-key join không cần co-partitioning. Cách sửa là repartition phía có ít partition hơn, và với stream-table thì repartition stream. — [Kafka Streams DSL API 4.3](https://kafka.apache.org/43/streams/developer-guide/dsl-api/) (bậc 1, 2026)
- Bẫy hash trong Go: Sarama mặc định dùng hash **fnv**, trong khi Java client và Kafka Streams dùng **murmur2**. Wiki của goka viết rằng khi chạy chung với client khác mà không set hasher murmur2 thì "keys won't be sent to the expected partitions". — [goka wiki Tips](https://github.com/lovoo/goka/wiki/Tips) (bậc 1, không rõ ngày)
- **Local và remote, số liệu:** LinkedIn/Samza xử lý được 1,1 triệu request/giây trên một máy SSD với RocksDB cục bộ, trong khi đọc Espresso từ xa (3 node SSD) đạt "less than 10,000 requests per second", tức "A 100X difference". Tác giả lưu ý phép đo remote dùng I/O đồng bộ, không batching. Remote vẫn ổn khi tải dưới khoảng 10k req/s. Samza dùng host affinity (chạy lại trên đúng host cũ) để không phải reseed state, vì reseed "will cause a large pause". — [LinkedIn: Stream Processing Hard Problems Part II](https://www.linkedin.com/blog/engineering/archive/stream-processing-hard-problems-part-ii-data-access) (bậc 1, 2016-08-22)
- Nhược điểm của local state: gắn chặt vào vòng đời instance, compaction chạy trên cùng node gây jitter. — [RisingWave blog](https://www.risingwave.com/blog/sub-100ms-stream-processing-s3-cloud-native) (bậc 2, ý kiến của vendor bán giải pháp state trên S3, không rõ ngày)
- **Checkpoint kiểu Flink:** dựa trên Chandy-Lamport. Barrier "never overtake records". Operator nhiều input phải căn barrier (alignment). Unaligned checkpoint cho barrier vượt qua dữ liệu in-flight, và dữ liệu đó trở thành một phần của state. Bỏ alignment thì thành at-least-once ("On a restore, these records will occur as duplicates"). Savepoint được kích hoạt thủ công, dùng để nâng cấp chương trình mà không mất state. Keyed state được phân phối lại theo đơn vị **key group**, số key group bằng max parallelism. Backend là heap hoặc RocksDB. — [Flink Stateful Stream Processing 2.3](https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/stateful-stream-processing/) (bậc 1, 2026)
- **EOS và state cục bộ:** ở Kafka Streams 4.3, "EOS crash behavior is unchanged in 4.3: state stores are still wiped and fully restored from the changelog". KIP-1035 (lưu changelog offset bên trong từng store) đã có ở 4.3 và là tiền đề cho KIP-892 (transactional state store, bỏ bước restore toàn bộ). 4.3.0 có rò rỉ bộ nhớ native trong tầng RocksDB, nên dùng 4.3.1. — [Kafka Streams Upgrade Guide 4.3](https://kafka.apache.org/43/streams/upgrade-guide/) (bậc 1, 2026). KIP-844 đã bị loại để thay bằng KIP-892 — [KIP-892](https://cwiki.apache.org/confluence/display/KAFKA/KIP-892:+Transactional+Semantics+for+StateStores) (bậc 1)
- **Các store nhúng trong Go:**
  - Pebble là "LevelDB/RocksDB inspired key-value store focused on performance and internal usage by CockroachDB", mặc định trong CockroachDB từ v20.2, "considered stable and production ready". Nó không có column family, transaction, universal compaction. Có batch (indexed), snapshot, iterator có bound/prefix, range deletion và checkpoint. — [cockroachdb/pebble](https://github.com/cockroachdb/pebble) (bậc 1, 2026)
  - BadgerDB là KV pure Go, theo thiết kế LSM cộng value log (WiscKey), giảm write amplification. Có transaction ACID SSI và TTL. Dùng trong Dgraph và Jaeger. — [dgraph-io/badger](https://github.com/dgraph-io/badger) (bậc 1, 2026)
  - goka mặc định dùng LevelDB, ngoài ra có in-memory và Redis. — [lovoo/goka](https://github.com/lovoo/goka) (bậc 1)

### Nhận định
- **Nhận định:** với Go, Pebble là lựa chọn mặc định hợp lý cho state cục bộ. Nó pure Go (không cần cgo như RocksDB), đã chạy production ở quy mô lớn, và có range deletion. Range deletion hữu ích để xoá cả dải window đã hết hạn bằng một thao tác, nếu key được thiết kế là `key|windowStart`. TTL của Badger tiện cho state hết hạn, nhưng value log cần GC riêng. Chọn RocksDB qua cgo chỉ khi cần đúng tính năng của nó.
- **Nhận định:** store bên ngoài (Redis, ScyllaDB hoặc Cassandra) hợp khi: (a) state phải đọc chung giữa nhiều service; (b) không muốn hoặc không thể co-partition; (c) tải vừa phải (khoảng 10k thao tác/giây trở xuống, hoặc cao hơn nếu batch hoặc pipeline); (d) cần scale instance nhanh mà không phải replay state. Cái giá: độ trễ mạng mỗi event, thêm một hệ thống phải vận hành, và exactly-once khó hơn vì offset Kafka và ghi DB không cùng một transaction. Khi đó phải dùng ghi idempotent hoặc lưu offset vào chính DB.
- **Nhận định:** trên Kubernetes, nên chạy engine stateful bằng StatefulSet với PVC và static membership hoặc sticky assignment. Mục đích là pod khởi động lại gặp lại đúng partition và đĩa cũ, chỉ cần replay phần changelog còn thiếu. Cách này tương đương host affinity của Samza.
- **Nhận định:** thời gian restore xấp xỉ bằng kích thước changelog chia cho tốc độ đọc và ghi vào store. Muốn giảm thì giữ changelog compacted gọn (xoá bằng tombstone khi window hết hạn), tăng số partition để chia nhỏ state, dùng standby hoặc warmup, và khi restore thì ghi theo batch lớn, tắt WAL.

### Khoảng trống
- Chưa tìm được benchmark độc lập so sánh Pebble, RocksDB và Badger cho workload stream processing (nhiều ghi nhỏ, xoá theo dải).
- Chưa có nguồn bậc 1 về số liệu thực tế của Redis hay ScyllaDB làm state store cho stream processing (độ trễ p99, thông lượng có pipeline).
- Phiên bản Kafka phát hành KIP-441 không ghi trên trang KIP. Theo hiểu biết của agent là 2.6, nhưng chưa xác minh.

## 4. Kafka Streams và Flink làm thế nào (tham khảo), và tự làm trong Go khó tới đâu

### Kết luận ngắn
goka cho sẵn phần "state table theo consumer group, có changelog, phục hồi khi rebalance, có view và lookup", nhưng **không có** window, event-time, grace, suppress, stream-stream join có window hay EOS. Các phần này phải tự viết, cùng với chiến lược restore nhanh (standby/warmup). Thư viện Go khác (GKES, kstream) hoặc chưa đầy đủ, hoặc ít được kiểm chứng. Mức chắc chắn: **trung bình–cao**. Việc goka thiếu window là suy ra từ docs không nhắc tới, không phải một tuyên bố tường minh.

### Phát hiện có nguồn
- **goka:** "extends the concept of Kafka consumer groups by binding a state table to them and persisting them in Kafka". Các thành phần: Emitter, Processor, Group table (partitioned KV, "belongs to a single processor group", topic phải bật log compaction), View ("persistent cache of a group table", chỉ đọc). Store cục bộ mặc định LevelDB. Khi instance chết, "the remaining instances will take over the group table partitions of the failed instance recovering them from Kafka". Bảo đảm at-least-once. Client bên dưới là Sarama (IBM). Repo có khoảng 2,6k sao. — [lovoo/goka](https://github.com/lovoo/goka) (bậc 1, 2026-11); [goka overview](https://lovoo.github.io/goka/docs/guide/02_overview) (bậc 1)
- Processor của goka đọc "a set of co-partitioned topics (topics with the same number of partitions and the same key range)". Phiên bản xem được trên pkg.go.dev là v1.1.18, ngày 2026-11-11. — [pkg.go.dev goka](https://pkg.go.dev/github.com/lovoo/goka) (bậc 1, 2026-11-11)
- Lưu ý vận hành goka: tạo table topic với số partition bằng input. Tắt auto topic creation. Không có compaction thì Kafka sẽ xoá nội dung table theo retention. Kill processor thay vì dừng sạch "may cause a long time to rebalance". Nếu đọc nhiều hơn ghi nhiều thì nên bọc store bằng LRU cache. Phải set Kafka version cho Sarama. — [goka wiki Tips](https://github.com/lovoo/goka/wiki/Tips) (bậc 1, không rõ ngày)
- Callback update của goka chạy cho từng message khi recovery, nên callback nặng làm recovery chậm. Xử lý input bị chặn cho tới khi table phục hồi xong. — tổng hợp từ docs goka qua kết quả search ([pkg.go.dev goka](https://pkg.go.dev/github.com/lovoo/goka)). Đây là manh mối bậc 3, chưa đọc tận đoạn gốc.
- **GKES (aws/go-kafka-event-source):** dựng trên franz-go (kgo). Có EOS qua transaction, local state store, incremental rebalancing, changelog (`ChangeLogEntry`), "Interjections" giống punctuator, và xử lý async theo key. Tự nhận "not an all-in-one, do-everything black box". StateStore "left without comprehensive implementations". Không nhắc tới window hay join. Bản xem được là v1.0.6, ngày 2022-11-02. — [pkg.go.dev GKES](https://pkg.go.dev/github.com/aws/go-kafka-event-source/streams) (bậc 1, 2022-11-02)
- **franz-go GroupTransactSession:** helper cho EOS consume-process-produce. Nó "sets its internal state to abort whenever necessary (specifically, when a group rebalance happens)". Khuyến nghị mạnh dùng broker 2.5+ (KIP-447, `RequireStable`). Trên broker cũ hơn có "a very small risk of duplicates". — [franz-go docs/transactions.md](https://github.com/twmb/franz-go/blob/master/docs/transactions.md) (bậc 1, không rõ ngày). Bản franz-go xem được là v1.22.3, ngày 2026-11-09 — [pkg.go.dev kgo](https://pkg.go.dev/github.com/twmb/franz-go/pkg/kgo) (bậc 1)
- **Kafka Streams đang chuyển rebalance lên broker:** KIP-1071 (Streams Rebalance Protocol) ra early access ở 4.1. Ở 4.2, "General Availability for the core functionality" và bật mặc định trên cluster mới, bật bằng `group.protocol=streams`. Giới hạn: không có static membership, chỉ có sticky assignor (không có warmup task, không có rack-aware), không có regex, chỉ migrate offline. `num.standby.replicas` cấu hình phía broker. — [Streams Rebalance Protocol 4.2](https://kafka.apache.org/42/streams/developer-guide/streams-rebalance-protocol/) (bậc 1, 2026); [Upgrade Guide 4.3](https://kafka.apache.org/43/streams/upgrade-guide/) (bậc 1, 2026)
- Thư viện Go khác: gmbyapa/kstream (port Kafka Streams, cần librdkafka) và StreamForge (tự quảng cáo có window, chưa kiểm chứng). — chỉ thấy qua kết quả search ([gmbyapa/kstream](https://github.com/gmbyapa/kstream), [streamforge](https://pkg.go.dev/github.com/ilya-shevelev/streamforge)). Bậc 3, chưa đọc kỹ.

### Nhận định
- **Nhận định:** các mảnh phải tự viết khi làm stateful engine trong Go trên franz-go hoặc goka:
  1. **Task theo partition.** Mỗi partition có một goroutine, một store (thư mục Pebble riêng, hoặc một DB chung với prefix là partition) và một partition changelog tương ứng (changelog có cùng số partition với input).
  2. **Đường ghi.** Cập nhật store, gửi bản ghi changelog, rồi commit offset input. Nếu at-least-once thì commit sau khi changelog được ack. Nếu EOS thì gói produce changelog, produce output và commit offset vào một transaction (`GroupTransactSession`).
  3. **Checkpoint cục bộ.** Ghi "offset changelog đã áp vào store" vào chính store, cùng batch với dữ liệu (ý tưởng của KIP-1035). Khi khởi động chỉ cần replay từ offset đó.
  4. **Restore khi được gán partition.** Đọc changelog từ checkpoint tới high watermark bằng một consumer riêng không thuộc group, ghi batch vào store, xong rồi mới xử lý input. Trong lúc đó partition input nên được pause.
  5. **Window store.** Key có dạng `key|windowStart`, stream-time theo partition, đóng window theo grace, phát kết quả (liên tục hoặc khi đóng), xoá window hết hạn ở cả store lẫn changelog (tombstone).
  6. **Timer/punctuator** theo stream-time và theo wall-clock.
  7. **Join.** Stream-table: đọc topic bảng vào store cục bộ (co-partitioned), hoặc dùng "global table" replicate toàn bộ. Stream-stream: hai window store, mỗi bên giữ record trong khoảng join window cộng grace.
  8. **Standby/warmup (tuỳ chọn).** Instance khác cũng tail changelog để sẵn sàng nhận partition.
  9. **Gắn với rebalance.** Callback revoke phải flush store, chốt checkpoint và commit. Callback assign phải restore. Dùng cooperative-sticky hoặc KIP-848 để giảm số lần di chuyển partition.
- **Nhận định:** các bẫy chính:
  - (a) Đổi số partition input làm hỏng ánh xạ key → partition và changelog. Nên xem số partition là bất biến, hoặc phải migrate bằng cách dựng lại state.
  - (b) Lệch hash (fnv của Sarama với murmur2) làm hỏng co-partitioning một cách âm thầm.
  - (c) Restore lâu sau rebalance hoặc khi scale. Đây là vấn đề KIP-441 sinh ra để giải quyết. Trên K8s, pod mới không có đĩa cũ thì phải replay toàn bộ.
  - (d) Crash giữa lúc ghi store và ghi changelog làm store cục bộ "đi trước" changelog. Đó là lý do Kafka Streams xoá state khi crash ở chế độ EOS. Tự làm thì phải chọn: chấp nhận at-least-once (replay changelog đè lên, chỉ an toàn khi cập nhật idempotent), hoặc chỉ áp vào store sau khi transaction commit.
  - (e) Changelog không compacted hoặc không có tombstone thì phình mãi.
  - (f) Đổi schema hay logic của state (state migration) không có công cụ như savepoint của Flink. Phải version hoá format value, hoặc chạy app mới với changelog mới và reprocess.
- **Nhận định:** khi nào nên dùng framework thay vì tự viết: nhiều phép join hoặc window chồng nhau, cần exactly-once end-to-end có state, state lớn (hàng trăm GB trở lên) cần checkpoint incremental lên object storage, hoặc cần savepoint để nâng cấp logic. Khi đó Flink hoặc Kafka Streams đã giải sẵn hàng chục năm bug. Với aggregation theo key đơn giản (đếm, dedup, profile theo entity) thì goka hoặc tự viết trên franz-go cộng Pebble là khả thi.

### Khoảng trống
- Chưa xác nhận trực tiếp từ docs goka rằng goka **không** có window hay EOS. Kết luận này dựa trên việc README, overview và wiki không nhắc tới, và client là Sarama (goka tự ghi at-least-once).
- Chưa có postmortem hay case study công khai về engine stateful tự viết bằng Go, để có số liệu thời gian restore thực tế.
- Chưa đọc đoạn docs gốc của goka về `WaitForReady` và hành vi chặn xử lý trong lúc recovery.

## 5. Giải thích từ đầu, kèm ví dụ cụ thể (cho người mới)

### Kết luận ngắn
Phần này tổng hợp để writer dùng. Mọi sự thật đã có nguồn ở các mục 1–4. Ví dụ là minh hoạ do agent đặt ra. Mức chắc chắn: **cao** về khái niệm.

### Phát hiện có nguồn
- "Stream" và "table" là hai mặt của một thứ: "a stream can be viewed as a table, and a table can be viewed as a stream", và "A stream is thus a table in disguise". — [Kafka Streams Core Concepts 4.3](https://kafka.apache.org/43/streams/core-concepts/) (bậc 1, 2026)
- Định nghĩa streaming system: "a type of data processing engine that is designed with infinite data sets in mind". — [Streaming 101](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/) (bậc 2, 2015)

### Nhận định
- **Nhận định, ví dụ 1 (event-time và grace):** đếm click mỗi 1 phút bằng tumbling window. Một click xảy ra lúc 10:00:58 trên điện thoại mất mạng, tới Kafka lúc 10:01:20.
  - Theo processing-time, nó bị đếm vào phút 10:01. Sai.
  - Theo event-time, nó thuộc phút 10:00. Với grace 30 giây, window [10:00, 10:01) đóng khi stream-time ≥ 10:01:30. Click về lúc stream-time là 10:01:20 nên vẫn được tính.
  - Nếu nó về lúc stream-time là 10:01:45 thì đã quá hạn, bị bỏ hoặc đẩy sang topic late.
- **Nhận định, ví dụ 2 (vì sao state phải theo partition):** đếm số đơn theo `user_id`. Nếu đơn của user 42 lúc vào partition 3, lúc vào partition 7, thì hai instance mỗi bên giữ một nửa con số. Vì vậy key phải quyết định partition, và mọi topic cần join theo key đó phải chia partition giống hệt nhau (co-partitioning).
- **Nhận định, ví dụ 3 (changelog):** instance A giữ count của partition 3 trong Pebble. Mỗi lần count đổi, A ghi `user42 → 17` vào topic `app-counts-changelog` partition 3. Topic này compacted, chỉ giữ giá trị mới nhất của mỗi key. A chết, B nhận partition 3, đọc changelog partition 3 từ đầu (hoặc từ checkpoint) để dựng lại Pebble, rồi mới đọc tiếp input. Changelog càng lớn thì B càng mất lâu mới chạy được. Đó là lý do có standby: instance C luôn đọc sẵn changelog này.
- **Nhận định, ví dụ 4 (stream-table join):** topic `clicks` (key `user_id`) join với topic compacted `users` (key `user_id`, hồ sơ). Engine giữ `users` partition 3 trong store cục bộ. Click của user 42 vào partition 3, tra store, gắn hồ sơ rồi xuất ra. Nếu `users` có 8 partition còn `clicks` có 12 thì phải repartition `clicks`, hoặc nạp toàn bộ `users` vào mọi instance (global table) nếu bảng đủ nhỏ.
- **Nhận định, ví dụ 5 (session):** gap 30 phút. User có event lúc 10:00, 10:10 và 11:00, tạo thành hai session [10:00–10:10] và [11:00]. Event trễ có timestamp 10:35 đến, cách 10:10 dưới 30 phút và cách 11:00 dưới 30 phút, nên hai session gộp thành [10:00–11:00]. Store phải xoá hai bản cũ và ghi một bản mới.

### Khoảng trống
- Không có.

## Truy vấn đã chạy
- kafka streams core concepts stream-time grace period (standard, giới hạn kafka.apache.org)
- goka processor rebalance recovery slow state table (standard)
- KIP-1071 streams rebalance protocol Kafka 4.1 (standard)
- stream processing state local RocksDB vs remote Redis latency tradeoff (standard)
- KIP-892 transactional state stores Kafka Streams EOS wipe state (standard)
- golang kafka stream processing library windowing state store changelog (standard)
- Fetch trực tiếp: Kafka Streams 4.3 core-concepts, architecture, dsl-api, upgrade-guide; Kafka 4.2 streams-rebalance-protocol; KIP-441; Flink 2.3 time, stateful-stream-processing, windows, generating_watermarks; Akidau Streaming 101/102; goka README, wiki Tips, overview, pkg.go.dev; Pebble, Badger README; franz-go transactions.md; GKES pkg.go.dev; LinkedIn "Stream Processing Hard Problems Part II"
