# Hệ sinh thái Go & so sánh framework cho engine consumer Kafka

Ghi chú nền cho người mới (để writer dùng khi giải thích):
- **Kafka client** là thư viện nói giao thức Kafka (fetch, produce, commit offset, tham gia consumer group). Mọi engine Go đều đứng trên một client.
- **cgo** là cơ chế để Go gọi code C. Client dùng cgo (confluent-kafka-go bọc librdkafka viết bằng C) thì build cần trình biên dịch C, phụ thuộc libc (glibc/musl), khó cross-compile và khó build binary tĩnh "chỉ một file".
- **KIP-848** là giao thức consumer group thế hệ mới: broker tự tính việc chia partition (server-side assignment), rebalance theo từng phần, không còn "stop-the-world". **Cooperative-sticky** (KIP-429) là cách rebalance theo từng phần trên giao thức cũ (classic), do client tính.
- **Transactions/EOS** (KIP-98): producer ghi nhiều record và commit offset của consumer trong một giao dịch nguyên tử, nền tảng cho exactly-once kiểu read-process-write.
- **Stream-processing framework** (goka, Kafka Streams, Flink) lo thêm phần *state* (bảng, window, join), phục hồi state khi crash/rebalance; còn client chỉ lo đọc/ghi.

## 1. So sánh client Go: franz-go, confluent-kafka-go, sarama, segmentio/kafka-go (tình trạng 11/2026)

### Kết luận ngắn
franz-go là lựa chọn mặc định hợp lý nhất cho engine mới viết bằng Go thuần: đủ tính năng nhất (transactions/EOS, cooperative-sticky, KIP-848, KIP-932 share group, admin `kadm`), hoạt động phát triển mạnh, phát hành liên tục đến 11/2026. confluent-kafka-go là lựa chọn thứ hai khi cần đồng bộ hành vi với hệ client Confluent/librdkafka và chấp nhận cgo; sarama còn bảo trì tốt nhưng chưa hỗ trợ KIP-848 phía consumer; segmentio/kafka-go gần như ngừng phát triển, không nên chọn cho dự án mới. Mức chắc chắn: **cao** về tính năng/phiên bản (lấy từ Go module proxy và README chính chủ); **thấp** về hiệu năng tương đối (không có benchmark độc lập gần đây).

### Phát hiện có nguồn

**Phiên bản mới nhất (tra trực tiếp Go module proxy, ngày 2026-11-13):**
- franz-go `v1.22.3` (2026-11-09); `pkg/kadm` `v1.20.0` (2026-11-09) — [proxy.golang.org franz-go @latest](https://proxy.golang.org/github.com/twmb/franz-go/@latest) (bậc 1, 2026-11-09)
- confluent-kafka-go `v2.16.1` (2026-10-27) — [proxy.golang.org confluent-kafka-go/v2 @latest](https://proxy.golang.org/github.com/confluentinc/confluent-kafka-go/v2/@latest) (bậc 1, 2026-10-27)
- IBM/sarama `v1.61.1` (2026-09-27) — [proxy.golang.org sarama @latest](https://proxy.golang.org/github.com/!i!b!m/sarama/@latest) (bậc 1, 2026-09-27)
- segmentio/kafka-go `v0.4.51` (2026-04-23), vẫn ở 0.x — [proxy.golang.org kafka-go @latest](https://proxy.golang.org/github.com/segmentio/kafka-go/@latest) (bậc 1, 2026-04-23)

**franz-go (twmb), Go thuần, không cgo:**
- Tự mô tả "Feature complete client (Kafka >= 0.8.0 through v4.4+)"; có "Idempotent & transactional producers", group consumer với balancer eager (roundrobin, range, sticky) và "cooperative (cooperative-sticky)", "server-side balancing (KIP-848)", "Share group (queue) consumers (KIP-932)", admin package `kadm` — [franz-go README](https://github.com/twmb/franz-go/blob/master/README.md) (bậc 1, đọc 2026-11-13)
- Bảng KIP trong README: KIP-848 "Supported (`ServerSideBalancer` group opt)"; KIP-345 static membership, KIP-429 incremental rebalance, KIP-881 rack-aware assignment, KIP-98 EOS đều "Supported"; KIP-932 share groups (Kafka 4.1) "Supported (via `ShareGroup`)"; đã hỗ trợ cả các KIP của Kafka 4.2 (KIP-1206, KIP-1222, KIP-1226) — [franz-go README](https://github.com/twmb/franz-go/blob/master/README.md) (bậc 1, đọc 2026-11-13)
- Về hiệu năng, README chỉ nói định tính: "consistently among the fastest and most cpu and memory efficient Kafka clients in Go"; "Highly performant by avoiding channels and goroutines where not necessary"; có thư mục `examples/bench/compare` để tự so với client khác — [franz-go README](https://github.com/twmb/franz-go/blob/master/README.md) (bậc 1, tự công bố)
- Hoạt động: tính đến 25/9/2026, 386 commit và 103 PR merge trong 90 ngày, thời gian merge trung vị 2,1 giờ, nhưng **một tài khoản xử lý toàn bộ các lần merge** (rủi ro "bus factor") — [Kafka Go Clients: franz-go vs kafka-go vs Sarama, Kafma](https://kafma.app/blog/kafka-golang-clients) (bậc 2–3, nhóm Kafma, 2026-09-26)
- franz-go được chính Redpanda Connect dùng làm client chính (`twmb/franz-go v1.22.2`, kèm `kadm`, `kfake`, `sr` cho Schema Registry) — [go.mod của redpanda-data/connect v4.118.0](https://proxy.golang.org/github.com/redpanda-data/connect/v4/@v/v4.118.0.mod) (bậc 1, 2026-11-13)

**confluent-kafka-go (bọc librdkafka bằng cgo):**
- "a lightweight wrapper around librdkafka, a finely tuned C client"; độ tin cậy đến từ việc dùng chung một lõi C với các client Confluent khác — [confluent-kafka-go README](https://github.com/confluentinc/confluent-kafka-go/blob/master/README.md) (bậc 1, đọc 2026-11-13)
- **Hệ quả cgo:** "`CGO_ENABLED` must NOT be set to `0`"; có sẵn librdkafka build tĩnh cho macOS x64/arm64, Linux glibc x64/arm64, Linux musl amd64/arm64 (Alpine, phải build với `-tags musl`), Windows amd64 (không có gói hỗ trợ chính thức); bản build sẵn **không có GSSAPI/Kerberos** (muốn có phải cài librdkafka riêng và build `-tags dynamic`); build trên máy glibc mới rồi chạy trên máy glibc cũ có thể lỗi phiên bản glibc, static link không giải quyết được vì `getaddrinfo` vẫn cần thư viện động — [confluent-kafka-go README](https://github.com/confluentinc/confluent-kafka-go/blob/master/README.md) (bậc 1, đọc 2026-11-13)
- README hiện yêu cầu "Go 1.26.10+ (or 1.27.3+) and librdkafka 2.16.0+"; API khuyến nghị là function-based, API channel-based chuyển vào `examples/legacy` — [confluent-kafka-go README](https://github.com/confluentinc/confluent-kafka-go/blob/master/README.md) (bậc 1, đọc 2026-11-13)
- KIP-848: v2.10.0 thêm KIP-848 vào DescribeConsumerGroups/AlterConfigs; **v2.12.0 tuyên bố "production-ready"** nhưng vẫn opt-in, `group.protocol` mặc định `classic`. v2.16.0 thêm `SerializingProducer`/`DeserializingConsumer` thử nghiệm ("experimental and subject to change or removal") — [confluent-kafka-go CHANGELOG](https://github.com/confluentinc/confluent-kafka-go/blob/master/CHANGELOG.md) (bậc 1, đọc 2026-11-13)
- Có AdminClient đầy đủ, transactional producer, cooperative-sticky qua `partition.assignment.strategy`, Schema Registry client tích hợp sẵn — [Kafma](https://kafma.app/blog/kafka-golang-clients) (bậc 2–3, 2026-09-26) và [CHANGELOG](https://github.com/confluentinc/confluent-kafka-go/blob/master/CHANGELOG.md) (bậc 1)
- Hoạt động (25/9/2026): 55 commit, 29 PR merge/90 ngày, merge trung vị 4,2 ngày, 74 PR mở với tuổi trung vị 2,4 năm — [Kafma](https://kafma.app/blog/kafka-golang-clients) (bậc 2–3, 2026-09-26)

**IBM/sarama (Go thuần, client lâu đời nhất):**
- Chính sách tương thích: "we support the two latest stable releases of Kafka and Go, and we provide a two month grace period for older releases" — [sarama README](https://github.com/IBM/sarama/blob/main/README.md) (bậc 1, đọc 2026-11-13)
- Có producer transactions; v1.60.1 thêm cooperative-sticky, v1.61.0 thêm incremental cooperative rebalancing (KIP-429) — [Kafma](https://kafma.app/blog/kafka-golang-clients) (bậc 2–3, 2026-09-26)
- KIP-848: chỉ mới có API `ConsumerGroupDescribe` (PR #3748, vào v1.61.0); **membership theo KIP-848 chưa có**, issue #3818 mở ngày 30/9/2026 đề nghị bổ sung để "avoid stop-the-world" — [IBM/sarama PR #3748](https://github.com/IBM/sarama/pull/3748), [IBM/sarama issue #3818](https://github.com/IBM/sarama/issues/3818) (bậc 1, 2026)
- Hoạt động (25/9/2026): 86 commit, 74 PR merge/90 ngày, merge trung vị 1,3 ngày, một tài khoản xử lý 98% merge — [Kafma](https://kafma.app/blog/kafka-golang-clients) (bậc 2–3, 2026-09-26)
- Lời chê từ phía kafka-go (quan điểm của đối thủ, cần đọc có phê phán): sarama "poorly documented, the API exposes low level concepts of the Kafka protocol", truyền giá trị bằng pointer gây nhiều cấp phát bộ nhớ và GC — [segmentio/kafka-go README](https://github.com/segmentio/kafka-go/blob/main/README.md) (bậc 1, không rõ ngày đoạn này)
- sarama là nền của goka và watermill-kafka (xem mục 2).

**segmentio/kafka-go (Go thuần):**
- README: "currently tested with Kafka versions 0.10.1.0 to 2.7.1"; yêu cầu Go 1.15+; không nhắc transactions; `ReadMessage` tự commit offset khi dùng consumer group, có `CommitInterval` để commit định kỳ — [segmentio/kafka-go README](https://github.com/segmentio/kafka-go/blob/main/README.md) (bậc 1, đọc 2026-11-13)
- Không có transactional producer/consume-transform-produce, không có KIP-848, không có assignor cooperative-sticky, không có AdminClient riêng; tính đến 25/9/2026 "no default-branch commits or merged PRs in 90 days", 83 PR mở với tuổi trung vị 2,6 năm — [Kafma](https://kafma.app/blog/kafka-golang-clients) (bậc 2–3, 2026-09-26)
- Confluent từng ghi kafka-go "not compliant for consumer applications" và khuyên dùng confluent-kafka-go (trang có thể cũ, khoảng 15 tháng) — [Client Deprecation in Confluent Cloud](https://docs.confluent.io/cloud/current/client-apps/deprecate-how-to.html) (bậc 1 nhưng là bên có lợi ích, không rõ ngày; chỉ thấy qua snippet tìm kiếm, chưa mở trang)

**Bối cảnh broker (để hiểu vì sao KIP-848 quan trọng):**
- Từ Kafka 4.0 (phát hành 2025-03-18), KIP-848 GA; bật mặc định phía broker, consumer phải opt-in `group.protocol=consumer`; chuyển nhóm từ Classic sang Consumer không downtime; không hỗ trợ client-side assignor; Kafka Streams có lộ trình riêng (KIP-1071); dự kiến Kafka 5.0 mới đổi mặc định — [Apache Kafka 4.0.0 Release Announcement](https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/) và [Kafka docs: Consumer Rebalance Protocol](https://kafka.apache.org/40/operations/consumer-rebalance-protocol/) (bậc 1, 2025-03; qua snippet tìm kiếm)
- franz-go đòi Kafka 4.0+ cho KIP-848 (opt-in `ServerSideBalancer()`); confluent-kafka-go GA từ v2.12.0, Kafka 4.0+, opt-in — [Kafma](https://kafma.app/blog/kafka-golang-clients) (bậc 2–3, 2026-09-26)

**Hiệu năng:**
- Không có benchmark độc lập, gần đây, so sánh cùng điều kiện. Kafma: "There is no reliable general winner", throughput phụ thuộc kích thước message, batching, nén, acks, giới hạn broker, cách commit — [Kafma](https://kafma.app/blog/kafka-golang-clients) (bậc 2–3, 2026-09-26)
- Benchmark độc lập 2022 (i7-9700, chỉ đo ghi bất đồng bộ): sarama ít cấp phát bộ nhớ hơn, kafka-go nhanh nhất tổng thể; **không gồm franz-go**, phương pháp hẹp — [Go社区主流Kafka客户端简要对比, Tony Bai](https://tonybai.com/2022/03/28/the-comparison-of-the-go-community-leading-kakfa-clients/) (bậc 2, 2022-03; chỉ qua snippet, cũ)
- Issue sarama #2540: bật nén tăng throughput đáng kể, công cụ bench của franz-go cho thấy hiệu ứng tương tự — [IBM/sarama issue #2540](https://github.com/IBM/sarama/issues/2540) (bậc 3, qua snippet)

### Nhận định
- **Nhận định:** với engine mới chạy trên Kubernetes, franz-go cho lợi thế kép: build tĩnh không cgo (image distroless/scratch, cross-compile dễ) và là client Go duy nhất hỗ trợ đầy đủ cả EOS, KIP-848 lẫn share group. Rủi ro chính là phụ thuộc gần như một maintainer.
- **Nhận định:** chọn confluent-kafka-go khi tổ chức đã chuẩn hoá trên librdkafka (cùng cấu hình/hành vi với client Python/C#), cần hỗ trợ thương mại từ Confluent, hoặc cần serializer Schema Registry có sẵn; trả giá bằng build cgo, không có Kerberos trong bản build sẵn, debug xuyên lớp Go/C khó hơn, cấu hình dạng chuỗi kiểu librdkafka.
- **Nhận định:** sarama hợp khi đã có codebase hoặc dùng goka/watermill; nhưng khi cần KIP-848 thì hiện chưa dùng được.
- **Nhận định:** không nên chọn segmentio/kafka-go cho engine mới ở quy mô vừa–lớn: không transactions, không cooperative/KIP-848 (rebalance stop-the-world khi scale), gần như không có hoạt động merge năm 2026.

### Khoảng trống
- Không tìm được benchmark độc lập, công bố phương pháp, năm 2025–2026 so sánh cả bốn client ở >500k msg/s. Một kết quả tìm kiếm nói README franz-go từng ghi "2.5x faster at producing than sarama, 1.5x faster at consuming", nhưng README hiện tại (đọc 2026-11-13) không còn câu đó, nên không dùng làm bằng chứng. Truy vấn đã thử: "franz-go sarama kafka-go benchmark throughput comparison".
- Không xác minh được trực tiếp trên GitHub (API GitHub bị chặn trong phiên này) số sao, issue mở; số liệu hoạt động lấy từ Kafma (bậc 2–3, một nguồn).
- Chưa xác minh confluent-kafka-go có hỗ trợ share consumer (KIP-932) hay chưa: CHANGELOG không nhắc.

## 2. Thư viện/khung xử lý stream trong Go: goka, Redpanda Connect (Benthos), Watermill, khác

### Kết luận ngắn
Go không có tương đương đầy đủ của Kafka Streams/Flink. goka là thư viện stateful duy nhất còn bảo trì (state table theo key lưu trên Kafka compacted topic, at-least-once, không có window/join dựng sẵn). Redpanda Connect (trước là Benthos) là công cụ pipeline cấu hình YAML, mạnh cho ingest/transform/route stateless. Watermill là khung ứng dụng event-driven (router + middleware retry/poison queue), không phải engine stream stateful. Các thư viện khác (go-streams, GKES của AWS, gstream) nhỏ hoặc gần như ngừng. Mức chắc chắn: **cao** (README và go.mod chính chủ).

### Phát hiện có nguồn

**goka (lovoo):**
- "a compact yet powerful distributed stream processing library for Apache Kafka written in Go"; thành phần: Emitter (ghi key-value vào Kafka), Processor (tập callback biến đổi state), Group table ("the state of a processor group", lưu trong Kafka, chia theo partition), View ("local caches of a complete group table", đọc-only, phục vụ gRPC/HTTP) — [goka README](https://github.com/lovoo/goka/blob/master/README.md) (bậc 1, đọc 2026-11-13)
- Storage cục bộ cắm được: "By default, the local storage uses LevelDB, but in-memory map and Redis-based storage are also available"; table topic phải bật log compaction; ngữ nghĩa "at-least-once"; khi instance hỏng, state và workload được chia lại cho instance khác; README không nhắc window hay join — [goka README](https://github.com/lovoo/goka/blob/master/README.md) (bậc 1)
- Dùng sarama làm client ("relies on Sarama"); go.mod của v1.1.18 phụ thuộc `IBM/sarama v1.46.3` và `syndtr/goleveldb v1.0.0` — [goka README](https://github.com/lovoo/goka/blob/master/README.md), [go.mod goka v1.1.18](https://proxy.golang.org/github.com/lovoo/goka/@v/v1.1.18.mod) (bậc 1)
- Bản mới nhất `v1.1.18` phát hành 2026-11-11 (vẫn được bảo trì) — [proxy.golang.org goka @latest](https://proxy.golang.org/github.com/lovoo/goka/@latest) (bậc 1, 2026-11-11)

**Redpanda Connect (trước là Benthos) và nhánh Bento:**
- "a stream processor that moves data between a wide range of sources and sinks", có processor để enrich/transform/filter, có connector CDC cho Postgres, MySQL, MongoDB, Oracle, MSSQL; ngôn ngữ mapping Bloblang — [Redpanda Connect README](https://github.com/redpanda-data/connect/blob/main/README.md) (bậc 1, đọc 2026-11-13)
- Ngữ nghĩa: "processes and acknowledges messages using an in-process transaction model with no disk-persisted state"; với nguồn và đích at-least-once thì đảm bảo at-least-once kể cả khi crash; tự mô tả "stateless and horizontally scalable"; có hai gói API: "Apache V2" và "Enterprise" — [Redpanda Connect README](https://github.com/redpanda-data/connect/blob/main/README.md) (bậc 1)
- Input Kafka: `kafka_franz` (dựa trên franz-go) đã deprecated từ 4.68.0, thay bằng input `redpanda`; offset chỉ commit khi mọi message có offset nhỏ hơn đã giao xong (`checkpoint_limit` mặc định 1024 message song song mỗi partition trước khi backpressure), commit mỗi `commit_period` 5s và luôn commit khi shutdown; batching giữ thứ tự partition; hỗ trợ static membership qua `instance_id`; `read_committed` để đọc record giao dịch đã commit — [Redpanda Connect docs: kafka_franz input](https://docs.redpanda.com/redpanda-connect/components/inputs/kafka_franz/) (bậc 1, đọc 2026-11-13)
- Bản mới nhất `v4.118.0` (2026-11-13); lõi tách thành module `redpanda-data/benthos/v4` `v4.84.0` (2026-10-22) — [proxy.golang.org connect/v4](https://proxy.golang.org/github.com/redpanda-data/connect/v4/@latest), [proxy.golang.org benthos/v4](https://proxy.golang.org/github.com/redpanda-data/benthos/v4/@latest) (bậc 1)
- Redpanda mua Benthos tháng 5/2024 và đổi tên thành Redpanda Connect; Redpanda nói lõi engine vẫn MIT — [Redpanda Acquires Benthos (press)](https://redpanda.com/press/redpanda-acquires-benthos) (bậc 1, 2024-05-30); [TechCrunch](https://techcrunch.com/2024/05/30/redpanda-acquires-benthos-to-expand-its-end-to-end-streaming-data-platform/) (bậc 2, 2024-05-30)
- WarpStream fork thành **Bento**, "100% MIT licensed" như Benthos trước đây, sau một thay đổi giấy phép từ phía Redpanda (chi tiết thay đổi chưa đọc được) — [Announcing Bento, WarpStream](https://www.warpstream.com/blog/announcing-bento-the-open-source-fork-of-the-project-formerly-known-as-benthos) (bậc 1 nhưng là bên liên quan, 2024); Bento `v1.22.0` phát hành 2026-10-09 — [proxy.golang.org bento](https://proxy.golang.org/github.com/warpstreamlabs/bento/@latest) (bậc 1)

**Watermill (ThreeDotsLabs):**
- "a Go library for working efficiently with message streams"; định vị cho ứng dụng event-driven (event sourcing, RPC over messages, saga, CQRS); hỗ trợ nhiều Pub/Sub: Kafka, AMQP, SNS/SQS, Google Pub/Sub, NATS JetStream, Redis Streams, SQL, ...; "Watermill v1.0.0 has been released and is production-ready", API ổn định theo semver — [Watermill README](https://github.com/ThreeDotsLabs/watermill/blob/master/README.md) (bậc 1, đọc 2026-11-13)
- Middleware dựng sẵn: Retry (exponential backoff), Poison Queue (đẩy message lỗi sang topic riêng), Throttle, Deduplicator (theo hash trong cửa sổ thời gian), Circuit Breaker, Timeout, Recoverer (bắt panic), Instant Ack (ack trước khi xử lý, đổi đảm bảo lấy throughput và "may break message ordering"), Duplicator (chạy handler hai lần để kiểm tra idempotency) — [Watermill docs: Middlewares](https://watermill.io/docs/middlewares/) (bậc 1, đọc 2026-11-13)
- watermill-kafka v3.1.4 (2026-07-29) dùng `IBM/sarama v1.50.1`; watermill core v1.5.3 (2026-08-25) — [go.mod watermill-kafka v3.1.4](https://proxy.golang.org/github.com/!three!dots!labs/watermill-kafka/v3/@v/v3.1.4.mod), [proxy.golang.org watermill](https://proxy.golang.org/github.com/!three!dots!labs/watermill/@latest) (bậc 1)

**Thư viện khác:**
- AWS go-kafka-event-source (GKES): quảng cáo EOS, local state store, incremental rebalancing, "used by AWS for internal workloads"; nhưng bản mới nhất `v1.0.0-beta` từ 2022-10-07 — [proxy.golang.org GKES](https://proxy.golang.org/github.com/aws/go-kafka-event-source/@latest) (bậc 1, 2022-10); mô tả tính năng qua snippet [GitHub GKES](https://github.com/ssorren/go-kafka-event-source) (bậc 3)
- reugn/go-streams: thư viện stream nhẹ, có window, có connector Kafka nhưng state không lưu trên Kafka; `v0.13.0` (2025-05-10) — [GitHub go-streams](https://github.com/reugn/go-streams), [proxy.golang.org go-streams](https://proxy.golang.org/github.com/reugn/go-streams/@latest) (bậc 1)
- gstream (KStream/KTable kiểu Kafka Streams cho Go): chỉ `v0.1.0` (2022-12-21) — [proxy.golang.org gstream](https://proxy.golang.org/github.com/!kum!kee!hyun/gstream/@latest) (bậc 1)
- Arroyo (Rust) nằm ngoài phạm vi Go; không khảo sát.

### Nhận định
- **Nhận định:** bản đồ chọn trong Go: (a) pipeline stateless, nhiều nguồn/đích, cần ra nhanh → Redpanda Connect/Bento (YAML + Bloblang, plugin Go khi cần); (b) dịch vụ nghiệp vụ event-driven cần retry/DLQ/dedup có sẵn, chịu được at-least-once → Watermill; (c) state theo key đơn giản (đếm, profile, trạng thái thực thể), cần view phục vụ truy vấn → goka; (d) cần window event-time, join stream-stream, watermark, EOS end-to-end → Go không có thư viện trưởng thành, hoặc tự viết trên franz-go (tốn công lớn) hoặc chuyển sang Flink/Kafka Streams/streaming SQL.
- **Nhận định:** goka và watermill-kafka đều kéo theo sarama, nên thừa hưởng việc chưa có KIP-848. Redpanda Connect dùng franz-go nên đi cùng hướng client mạnh nhất.
- **Nhận định:** Redpanda Connect có phần "Enterprise" và lịch sử tranh cãi giấy phép; nếu muốn MIT thuần thì Bento là lựa chọn, nhưng cần cân nhắc khác biệt tính năng đang lớn dần giữa hai nhánh.

### Khoảng trống
- Chưa xác minh chính xác thay đổi giấy phép nào của Redpanda dẫn đến fork Bento và connector nào thuộc diện enterprise.
- Không có số liệu throughput độc lập cho goka, Redpanda Connect, Watermill.
- Chưa rõ goka có hỗ trợ franz-go hay kế hoạch KIP-848 (go.mod chỉ có sarama).

## 3. Khi nào chuyển sang Flink, Kafka Streams, Spark Structured Streaming hay dịch vụ managed / streaming SQL

### Kết luận ngắn
Giữ consumer Go tự viết khi xử lý stateless hoặc state nhỏ theo key, sink có thể làm idempotent, và đội mạnh Go. Chuyển sang framework khi cần window theo event-time + watermark, join stream-stream, state lớn cần checkpoint/phục hồi, hoặc exactly-once end-to-end: Kafka Streams nếu chấp nhận JVM và chỉ Kafka→Kafka; Flink nếu nhiều nguồn/đích, state rất lớn, cần SQL và có đội vận hành (hoặc dùng managed như Confluent Cloud Flink); streaming database (RisingWave/Materialize) nếu logic diễn đạt được bằng SQL và cần materialized view truy vấn được; Spark chỉ hợp khi đã có hạ tầng Spark/Databricks. Mức chắc chắn: **trung bình**, vì tiêu chí chủ yếu là định tính, nhiều nguồn có lợi ích thương mại.

### Phát hiện có nguồn

**Kafka Streams vs Flink (tiêu chí):**
- Khác biệt chính là mô hình triển khai: Kafka Streams là thư viện nhúng trong ứng dụng ("code you ship"), Flink là runtime cụm ("infrastructure you operate"); khi cả hai làm được, "you choose on operations and team, not capability" — [Kafka Streams vs Flink vs ksqlDB: Honest Guide, Stéphane Derosiaux / Conduktor](https://www.conduktor.io/kafka-streams/vs-flink) (bậc 2, nhà cung cấp tool, cập nhật 2026-10-20)
- Kafka Streams: song song bị giới hạn bởi số partition của sub-topology bận nhất; chỉ đọc/ghi Kafka; phục hồi state bằng replay changelog topic nên đội ứng dụng chịu thời gian restore và bộ nhớ RocksDB; `num.standby.replicas` mặc định 0. Flink: song song tách khỏi partition, kết nối DB/file/object storage, phục hồi từ checkpoint trên storage bền, thống nhất batch và stream; thường cần đội platform riêng. ksqlDB "effectively maintenance-mode", dự án SQL mới nên xét Flink SQL trước — [Conduktor](https://www.conduktor.io/kafka-streams/vs-flink) (bậc 2, 2026-10-20)
- Kafka Streams chưa dùng giao thức KIP-848 của consumer; có lộ trình riêng KIP-1071 — [Kafka docs: Consumer Rebalance Protocol](https://kafka.apache.org/40/operations/consumer-rebalance-protocol/) (bậc 1, qua snippet)
- Vận hành Flink production gồm sizing cụm, tuning checkpoint, cấu hình state backend, nâng cấp job giữ tương thích state, on-call cho hệ phân tán; logic stateless có thể chỉ cần Kafka consumer viết logic trực tiếp — tổng hợp từ [Conduktor glossary](https://www.conduktor.io/glossary/kafka-streams-vs-apache-flink) và các blog khác (bậc 2–3, qua snippet)

**Flink: state và exactly-once:**
- Flink 2.0 đưa "disaggregated state": remote storage là nơi lưu state chính, store ForSt (LSM dựa trên RocksDB); chỉ disaggregate khi dùng API state bất đồng bộ (State V2) — [Disaggregated State Management in Apache Flink 2.0, PVLDB vol 18](https://www.vldb.org/pvldb/vol18/p4846-mei.pdf) (bậc 1, 2025); [Flink 2.0 release notes](https://apache.googlesource.com/flink/+show/master/docs/content/release-notes/flink-2.0.md) (bậc 1, 2025; qua snippet)
- KafkaSink exactly-once dùng two-phase commit gắn với checkpoint, cần `DeliveryGuarantee.EXACTLY_ONCE` và transactional ID prefix; transaction timeout phải lớn hơn checkpoint interval cộng thời gian downtime tối đa của Flink — [Flink: End-to-End Exactly-Once with Kafka](https://flink.apache.org/2018/02/28/an-overview-of-end-to-end-exactly-once-processing-in-apache-flink-with-apache-kafka-too/) (bậc 1, 2018; nguyên lý vẫn đúng, qua snippet)

**Managed: Confluent Cloud for Apache Flink:**
- Mặc định exactly-once end-to-end, dựa trên checkpoint + Kafka transactions; Flink commit transaction "approximately every minute", nên consumer `read_committed` thấy độ trễ tới khoảng 1 phút mỗi statement (trung bình ~30 giây mỗi hop trong pipeline nhiều statement); dùng at-least-once với `read_uncommitted` thì "end-to-end latency below 100 ms" nhưng có thể thấy trùng — [Delivery Guarantees and Latency in Confluent Cloud for Apache Flink](https://docs.confluent.io/cloud/current/flink/concepts/delivery-guarantees.html) (bậc 1, đọc 2026-11-13)

**Spark Structured Streaming:**
- Spark 4.1 thêm Real-Time Mode (RTM): pipelined/streaming shuffle, độ trễ mili-giây một chữ số cho workload stateless — [Spark Structured Streaming page](https://spark.apache.org/streaming/) (bậc 1, qua snippet); [Introducing Apache Spark 4.1, Databricks](https://www.databricks.com/blog/introducing-apache-sparkr-41) (bậc 1 nhà phát triển chính, 2025–2026, qua snippet)
- Giới hạn ở 4.1: chỉ query stateless hoặc một stage, viết bằng Scala, output mode Update; RTM là at-least-once còn micro-batch mới cho exactly-once — [Spark 4.1 Release Highlights, sparkingscala.com](https://sparkingscala.com/latest/2026/03/17/spark-4-1-release-highlights/) (bậc 2–3, 2026-03, qua snippet)

**Streaming database / streaming SQL (RisingWave, Materialize):**
- RisingWave: database streaming tương thích PostgreSQL, ingest từ Kafka và duy trì materialized view tăng dần; không phải deploy job hay quản lý topology worker; có thể phục vụ point lookup trực tiếp từ view (Flink SQL cần sink ra DB ngoài); benchmark Nexmark do chính hãng báo: thắng Flink 22/27 query — [RisingWave docs: When to use RisingWave](https://docs.risingwave.com/faq/faq-when-to-use-risingwave), [RisingWave vs Flink feature comparison](https://docs.risingwave.com/faq/rw-flink-feature-comparison) (bậc 1 nhưng là vendor; tuyên bố, không phải bằng chứng độc lập; qua snippet)
- Flink vẫn được ưu tiên khi cần logic lập trình (DataStream API), operator tùy biến ngoài SQL — [When to Use Flink vs a Streaming Database, RisingWave](https://risingwave.com/blog/when-to-use-flink-vs-streaming-database/) (bậc 2–3, vendor, qua snippet)

### Nhận định
- **Nhận định — tiêu chí chuyển khỏi Go tự viết (gợi ý cho bảng quyết định):**
  1. *Độ phức tạp state:* chỉ state theo key, không window → Go (map + Pebble/Redis, hoặc goka). Window event-time, watermark, late data, join stream-stream, session window → framework. Viết đúng watermark + checkpoint + phục hồi state khi rebalance trong Go là tự xây lại một phần Kafka Streams.
  2. *Exactly-once:* nếu sink là DB có thể upsert/idempotent → at-least-once + idempotent sink trong Go là đủ. Nếu cần EOS Kafka→Kafka có state → franz-go có transaction (tự làm được nhưng phải tự gắn state vào transaction), còn Kafka Streams/Flink làm sẵn. Lưu ý EOS kiểu Flink đổi lấy độ trễ cỡ checkpoint interval (Confluent Cloud: ~1 phút).
  3. *Kỹ năng đội:* đội Go thuần, không muốn vận hành JVM → tránh Kafka Streams (bắt buộc JVM). Đội SQL/analyst viết logic → Flink SQL hoặc streaming DB.
  4. *Chi phí vận hành:* Flink tự host cần đội platform; managed (Confluent Cloud Flink, các dịch vụ Flink managed khác) chuyển chi phí thành tiền dịch vụ. Consumer Go là một Deployment Kubernetes bình thường, rẻ nhất về vận hành khi logic đơn giản.
  5. *Nguồn/đích:* chỉ Kafka→Kafka → Kafka Streams đủ; nhiều nguồn/đích (DB, object storage, CDC) → Flink, hoặc Redpanda Connect nếu stateless.
  6. *Cần truy vấn kết quả:* materialized view truy vấn trực tiếp → streaming DB (RisingWave/Materialize) thay vì Flink + DB phục vụ.
- **Nhận định:** mô hình lai thường gặp và hợp lý: consumer Go làm ingest/decode/enrich stateless và sink idempotent; phần analytics stateful (window, join) giao cho Flink/streaming SQL, cả hai cùng đọc Kafka.

### Khoảng trống
- Không có ngưỡng định lượng đáng tin (vd "state > X GB thì dùng Flink"); các nguồn chỉ đưa tiêu chí định tính.
- Chưa có nguồn độc lập về chi phí (USD) Confluent Cloud Flink vs tự vận hành Flink vs consumer Go.
- Chưa khảo sát Materialize trực tiếp; thông tin streaming DB chủ yếu từ RisingWave (vendor).
- Nhiều phát hiện ở mục này chỉ đọc qua snippet tìm kiếm (Flink 2.0 notes, Spark 4.1, RisingWave), chưa mở trang gốc; writer nên ghi rõ mức độ.

## Truy vấn đã chạy
- Go module proxy `@latest` cho franz-go, kadm, confluent-kafka-go/v2, sarama, kafka-go, goka, redpanda connect/v4, watermill, watermill-kafka/v3, go-kafka-event-source, go-streams, bento, benthos/v4, gstream (tra trực tiếp)
- go.mod của watermill-kafka v3.1.4, goka v1.1.18, connect v4.118.0 (tra trực tiếp)
- IBM sarama KIP-848 consumer group protocol support (extended)
- segmentio kafka-go maintenance status 2026 (extended)
- franz-go sarama kafka-go benchmark throughput comparison (extended)
- Redpanda acquires Benthos Redpanda Connect license WarpStream Bento fork (standard)
- Go stream processing library Kafka stateful windowing 2025 alternative goka (extended)
- when to use Flink vs Kafka Streams vs plain consumer decision criteria (extended)
- Apache Flink 2.0 disaggregated state ForSt release Kafka exactly-once (standard)
- Spark Structured Streaming real-time mode latency Spark 4.1 (extended)
- RisingWave vs Flink streaming SQL Kafka materialized views when to use (standard)
- Apache Kafka 4.0 release KIP-848 consumer rebalance protocol generally available group.protocol=consumer (standard)
