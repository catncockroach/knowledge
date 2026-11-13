# Vận hành & observability cho engine consumer Kafka viết bằng Go

Phạm vi: metric và alert, tracing và logging, graceful shutdown và deploy trên Kubernetes, replay/reprocess, schema evolution, testing. Client Go tham chiếu chính là franz-go (`kgo`), vì đọc được source và doc comment trực tiếp. Các nguồn franz-go dưới đây là source nhánh `master` tải về ngày 2026-11-13.

## 1. Metric cốt lõi: lag theo offset và theo thời gian, throughput, latency, rebalance, lỗi/DLQ; nên alert gì

### Kết luận ngắn
Lag tính bằng số offset (log end offset trừ committed offset) là metric phổ biến nhưng dễ đánh lừa. Nên đo thêm lag theo thời gian ("consumer chậm bao nhiêu giây"), và alert theo xu hướng (kiểu Burrow) hoặc theo SLO thời gian, không dùng ngưỡng số message cố định. Mức chắc chắn: **cao** về khái niệm và công cụ (docs, source, wiki gốc). Mức chắc chắn: **trung bình** về bộ alert cụ thể, vì phần đó là tổng hợp của agent, không có một tài liệu chuẩn nào.

### Phát hiện có nguồn
- **Lag theo offset trong Go:** `kadm.Client.Lag(ctx, groups...)` trả về lag theo từng partition của group. `CalculateGroupLagWithStartOffsets` xử lý được partition chưa có commit mà log start offset khác 0. Ví dụ: log end 30, start 10, chưa commit, thì lag đúng là 20, còn `CalculateGroupLag` báo 30 — [franz-go pkg/kadm/groups.go](https://github.com/twmb/franz-go/blob/master/pkg/kadm/groups.go) (bậc 1, source master 2026-11).
- **Plugin `kprom` của franz-go không có metric lag hay metric theo partition.** Nó chỉ có counter mức client: `connects_total`, `read/write_bytes_total`, `fetch_bytes_total{node_id,topic}`, `buffered_fetch_records_total`... Histogram (request latency, throttle) mặc định tắt và bật bằng option `Histograms` — [kprom docs](https://pkg.go.dev/github.com/twmb/franz-go/plugin/kprom) (bậc 1, không rõ ngày).
- **Metric của consumer Java** (để so sánh và đặt tên khi tự export): `records-lag-max` (lag tối đa tính bằng số record của mọi partition trong cửa sổ đo), `last-poll-seconds-ago` (có từ Kafka 2.4, theo KIP-517), `rebalance-rate-per-hour`, `rebalance-total` — [Confluent Platform Consumer Metrics](https://docs.confluent.io/platform/current/kafka/consumer-metrics.html) (bậc 1, không rõ ngày); [KIP-517](https://cwiki.apache.org/confluence/display/KAFKA/KIP-517:+Add+consumer+metrics+to+observe+user+poll+behavior) (bậc 1). Client Go không tự có các metric này, phải tự đo (xem Nhận định).
- **Burrow (LinkedIn) đánh giá lag bằng cửa sổ trượt** gồm các lần commit, mặc định 10 điểm, tức khoảng 10 phút nếu commit mỗi 60 giây. Các trạng thái:
  - **OK:** trong cửa sổ có lúc lag bằng 0.
  - **WARNING:** offset vẫn tiến nhưng lag đứng yên hoặc tăng qua mọi cặp điểm.
  - **STALLED:** consumer vẫn commit nhưng committed offset không đổi.
  - **STOPPED:** commit mới nhất cũ hơn độ dài cửa sổ.

  Lý do: tránh "the need for setting a discrete threshold for the number of messages a consumer is allowed to be behind" — [Burrow wiki: Consumer Lag Evaluation Rules](https://github.com/linkedin/Burrow/wiki/Consumer-Lag-Evaluation-Rules) (bậc 1, không rõ ngày).
- **Kafka Lag Exporter (Lightbend/seglo)** export `kafka_consumergroup_group_lag_seconds` ("estimated lag in seconds"). Nó ước lượng bằng cách nội suy trên bảng offset→timestamp, mặc định giữ 60 mẫu mỗi partition. Repo **đã archive ngày 2024-03-17** — [seglo/kafka-lag-exporter](https://github.com/seglo/kafka-lag-exporter) (bậc 1, 2024-03).
- **Lời phê bình cách nội suy** (từ một bên làm công cụ cạnh tranh, cần lưu ý thiên vị):
  - "Offset lag is completely disconnected from time."
  - Nội suy hỏng khi cold start (trả NaN), khi producer ngừng (chia cho 0), và khi throughput dao động.
  - Topic ít traffic: consumer chết trên một topic mỗi ngày một lần mà offset lag vẫn phẳng suốt một tuần.
  - Compaction hoặc retention làm lag bị báo thấp hơn thực tế.

  Cách họ đề xuất là seek tới committed offset, đọc 1 record, lấy now trừ timestamp của record, có cache TTL — [SoftwareMill, The Hidden Problem with Kafka Lag Monitoring](https://softwaremill.com/the-hidden-problem-with-kafka-lag-monitoring/) (bậc 2, 2026-01-30).
- **kminion (Redpanda)** là Prometheus exporter. Nó đọc offset của group qua Admin API (mặc định) hoặc bằng cách consume `__consumer_offsets`; cách thứ hai cho thêm số lần commit của mỗi group. Lag export theo partition hoặc theo topic. Có chế độ **end-to-end**: tự produce rồi consume vào topic riêng để đo "roundtrip" latency, ack-latency và offset-commit-latency — [redpanda-data/kminion](https://github.com/redpanda-data/kminion) (bậc 1, không rõ ngày; repo còn hoạt động, 757 commit).
- **Nguồn timestamp để tính latency end-to-end:**
  - Topic config `message.timestamp.type` mặc định là `CreateTime` (producer đặt). `LogAppendTime` thì broker ghi đè bằng đồng hồ của broker — [KIP-32](https://cwiki.apache.org/confluence/display/KAFKA/KIP-32+-+Add+timestamps+to+Kafka+message) (bậc 1).
  - `message.timestamp.after.max.ms` giới hạn timestamp tương lai và chỉ áp dụng với CreateTime — [Kafka topic configs](https://kafka.apache.org/37/configuration/topic-level-configs/) (bậc 1).
  - Default của `log.message.timestamp.after.max.ms` có hai con số khác nhau: 3600000 ms trong KIP-32 và 86400000 ms trong tài liệu AWS MSK — [AWS MSK config](https://docs.aws.amazon.com/es_es/msk/latest/developerguide/msk-configuration-express-read-write.html) (bậc 1). Cần kiểm tra theo version đang dùng.

### Nhận định
- **Định nghĩa cho người mới:**
  - *Log end offset (LEO)*: offset kế tiếp sẽ được ghi vào partition.
  - *Committed offset*: vị trí group đã lưu, là record kế tiếp cần đọc.
  - *Offset lag* = LEO − committed.
  - *Time lag* ≈ now − timestamp của record tại committed offset.
  - *Processing latency* = thời gian xử lý một record hoặc một batch trong engine.
  - *End-to-end latency* = thời điểm sink ghi xong − timestamp của record.
- **Bộ metric engine Go nên tự export** (Prometheus hoặc OTel), vì client Go không có sẵn:
  1. `consumer_lag_records{topic,partition}` và `consumer_lag_seconds{topic,partition}`, đo từ bên ngoài (kminion, Burrow, hoặc job dùng `kadm.Lag`) chứ không đo trong chính consumer. Lý do: consumer chết thì không còn ai báo lag.
  2. Throughput: `records_consumed_total`, `records_processed_total{outcome=ok|retry|dlq|skip}`, bytes.
  3. Histogram `process_duration_seconds` (từng record hoặc từng batch) và `e2e_latency_seconds` (now − record.Timestamp, ghi ở sink).
  4. `rebalances_total`, `partitions_assigned` (gauge), thời gian trong callback revoke/assign. Đếm trong `OnPartitionsAssigned/Revoked/Lost`.
  5. `commit_errors_total`, `commit_duration_seconds`.
  6. `dlq_records_total`, `poison_records_total`, `deserialize_errors_total`.
  7. Thời gian từ lần poll cuối, tương đương `last-poll-seconds-ago`, để phát hiện vòng poll bị treo.
- **Alert gợi ý** (agent tổng hợp):
  - **Page:** time lag vượt SLO (vd >5 phút) kéo dài N phút. Burrow-STOPPED hoặc STALLED, tức group không commit hoặc offset đứng yên. Không có thành viên nào trong group (`partitions_assigned` tổng bằng 0).
  - **Ticket hoặc cảnh báo:** lag tăng đều trong 15–30 phút (kiểu Burrow-WARNING), tỉ lệ DLQ vượt ngưỡng hoặc tăng đột biến, rebalance/giờ cao bất thường (dấu hiệu crashloop hoặc vượt `max.poll`/session timeout), commit lỗi liên tục, p99 e2e latency vượt SLO.
  - **Không nên** alert trên offset lag tuyệt đối dùng chung một ngưỡng cho nhiều topic, vì 10k message có thể là 1 giây hoặc 1 ngày tuỳ throughput.
- Với topic ít traffic, chỉ dùng được time lag đọc trực tiếp timestamp của record, hoặc heartbeat/end-to-end probe kiểu kminion. Nội suy không dùng được.

### Khoảng trống
- Không lấy được trang tài liệu Apache gốc liệt kê metric consumer (`kafka.apache.org/documentation` chỉ trả trang redirect). Đã dùng tài liệu Confluent Platform thay thế.
- Không tìm được công thức nội suy chính xác của Kafka Lag Exporter từ nguồn của chính tác giả (bài blog Lightbend trả 404).
- Không có benchmark về chi phí broker của cách "đọc 1 record tại committed offset" khi có hàng nghìn partition.

## 2. Distributed tracing qua Kafka header (OpenTelemetry) và structured logging

### Kết luận ngắn
Theo OTel, producer tiêm "creation context" vào header của message. Phía consumer tạo span `receive` (CLIENT) và `process` (CONSUMER). Mặc định nên **link** span process tới creation context thay vì làm con (parent-child), nhất là khi xử lý theo batch. Convention vẫn ở trạng thái **Development**. Trong Go, `kotel` của franz-go lo phần inject/extract header, còn span process do code người dùng tự tạo. Mức chắc chắn: **cao** (spec và docs gốc).

### Phát hiện có nguồn
- **Span kind theo thao tác:**
  - `create`: PRODUCER.
  - `send`: PRODUCER nếu context của nó là creation context, ngược lại CLIENT.
  - `receive`: CLIENT.
  - `process`: CONSUMER.
  - `settle` (ack/commit): CLIENT.

  Nguồn: [OTel Semantic conventions for messaging spans](https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/) (bậc 1, không rõ ngày, trạng thái Development).
- **Creation context:** "A producer SHOULD attach a message creation context to each message."
- **Link hay parent-child:** link là mặc định, vì nó là "the only option to correlate producer and consumer(s) in batch scenarios" (một span chỉ có một parent). Dùng creation context làm parent của "Process" khi đã có span bao ngoài thì "NOT RECOMMENDED".
- **Chuyển phiên bản convention:** instrumentation ở v1.24.0 trở về trước không nên tự đổi version convention. Opt-in qua `OTEL_SEMCONV_STABILITY_OPT_IN=messaging` hoặc `messaging/dup` (phát cả hai) — cùng nguồn trên.
- **Attribute riêng cho Kafka:** `messaging.system.name="kafka"`, `kafka.cluster.id`, `kafka.message.key`, `kafka.offset`, `kafka.message.tombstone`. Batch dùng `messaging.batch.message_count`. Ví dụ tên span: `send T`, `poll T`, `process T`, `commit T`. Spec không quy định tên header hay cách mã hoá header — [OTel Kafka semantic conventions](https://opentelemetry.io/docs/specs/semconv/messaging/kafka/) (bậc 1, không rõ ngày, Development).
- **`kotel` (franz-go):**
  - `RecordCarrier` inject/extract trace vào header của `kgo.Record`. Propagator lấy từ `TracerPropagator(...)` hoặc global propagator.
  - Span publish chạy từ `OnProduceRecordBuffered` tới `OnProduceRecordUnbuffered`. Span receive chạy từ `OnFetchRecordBuffered` tới `OnFetchRecordUnbuffered`.
  - Span process tạo bằng `Tracer.WithProcessSpan(r)`, trả về `(ctx, span)`. "The user's application code is responsible for ending the span."
  - `LinkSpans()` cho span phía consumer link tới parent thay vì làm con.
  - Có thêm meter: `messaging.kafka.fetch_records.count`, `produce_bytes.count`...

  Nguồn: [kotel docs](https://pkg.go.dev/github.com/twmb/franz-go/plugin/kotel) (bậc 1, không rõ ngày).
- **Structured logging:** `kslog` là plugin bọc `slog.Logger` thành `kgo.Logger`: `kgo.WithLogger(kslog.New(slog.Default()))` — [kslog docs](https://pkg.go.dev/github.com/twmb/franz-go/plugin/kslog) (bậc 1, không rõ ngày).

### Nhận định
- **Mẫu dùng trong engine:** bật `kotel` (gồm `LinkSpans()`). Với mỗi record, gọi `ctx, span := tracer.WithProcessSpan(r)`, truyền `ctx` xuống tầng decode → process → sink. Sink produce ra topic khác bằng `cl.Produce(ctx, ...)` để trace nối tiếp. Lỗi thì `span.RecordError`, gán `error.type`, rồi `span.End()`.
- **Log của mỗi record nên có các field cố định:** `topic`, `partition`, `offset`, `key` (hoặc hash của key nếu nhạy cảm), `trace_id`, `group`, `generation`. Đây là "toạ độ" để replay chính xác một message lỗi. Không log payload ở mức info.
- **Sampling:** với >100k msg/s, tạo span cho từng record rất tốn. Nên sample theo tỉ lệ (head sampling) hoặc chỉ giữ span lỗi (tail sampling ở collector). Metric vẫn đếm đủ 100%.
- Convention còn ở Development nên tên attribute có thể đổi. Nên ghim version semconv của thư viện instrumentation.

### Khoảng trống
- Không kiểm chứng được kotel đang phát semconv version nào (tên attribute cũ `messaging.kafka.*` hay mới `kafka.*`). Cần đọc source kotel.
- Chưa có số liệu chi phí CPU khi tracing từng record ở throughput cao.

## 3. Graceful shutdown trong Go, deploy không downtime trên Kubernetes, tránh mất hoặc trùng khi rollout

### Kết luận ngắn
Trình tự đúng gồm 5 bước:
1. Bắt SIGTERM bằng `signal.NotifyContext`.
2. Ngừng poll.
3. Xử lý xong (drain) các record đã nhận.
4. Commit đồng bộ.
5. Rời group bằng `Close()`. Lệnh này gửi LeaveGroup, trừ khi dùng static membership.

Tất cả phải xong trong `terminationGracePeriodSeconds` (mặc định 30 giây, tính cả preStop). Với at-least-once thì rollout gần như không mất dữ liệu nhưng **luôn có thể trùng**, nên sink phải idempotent. Mức chắc chắn: **cao** (doc của franz-go và Kubernetes).

### Phát hiện có nguồn
- **`Close()`:** "leaves any group and closes all connections and goroutines. This function waits for the group to be left." Nếu đã override `OnPartitionsRevoked` thì "you must manually commit offsets before closing the client." Nếu dùng `BlockRebalanceOnPoll` mà đã poll, `Close` sẽ treo trừ khi gọi `AllowRebalance` trước, hoặc dùng `CloseAllowingRebalance()` — [franz-go pkg/kgo/client.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/client.go) (bậc 1, source 2026-11).
- **`LeaveGroupContext(ctx)`:**
  - Với group classic, nếu đang rebalance thì nó chờ join/sync xong để có thể commit lần cuối trong `OnPartitionsRevoked`.
  - Với group KIP-848, leave là heartbeat cuối với `MemberEpoch -1`; có `InstanceID` thì epoch là `-2` (rời tạm, partition vẫn được giữ tới session timeout).
  - Leave không đánh thức một `PollFetches` đang chờ, nên phải cancel context của vòng poll.
  - Không được gọi LeaveGroup hay Close đồng bộ từ trong callback `OnPartitions*`, vì sẽ deadlock.

  Nguồn: [franz-go pkg/kgo/consumer_group.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/consumer_group.go) (bậc 1, 2026-11).
- **Mặc định của franz-go:**
  - Autocommit mỗi 5 giây.
  - `OnPartitionsRevoked` mặc định là "a blocking commit of all non-dirty offsets (where 'dirty' is the most recent poll)".
  - `defaultRevoke` "commits the last fetched offsets and waits for the commit to finish".
  - Session timeout mặc định 45 giây.

  Nguồn: [franz-go pkg/kgo/config.go](https://github.com/twmb/franz-go/blob/master/pkg/kgo/config.go) (bậc 1, 2026-11).
- **Rủi ro của autocommit:** với autocommit mặc định, record poll ở lần trước được coi là đã xong khi poll lần kế tiếp. Nếu xử lý bất đồng bộ (worker pool), offset có thể được commit trước khi record xử lý xong, và crash lúc đó thì **mất dữ liệu**. Hai cách tránh:
  - `AutoCommitMarks()` + `MarkCommitRecords(...)`: chỉ commit record đã đánh dấu.
  - `DisableAutoCommit()` + commit tay, kèm một `OnPartitionsRevoked` tự viết có commit chặn.

  Doc nêu ví dụ: thiếu commit lúc revoke thì member B xử lý lại offset 4–29, và member A còn có thể "rewind member B's commit" — config.go (bậc 1).
- **`BlockRebalanceOnPoll()`:** chặn rebalance từ lúc poll tới lúc `AllowRebalance()`, để không commit vào partition mình không còn sở hữu. Đánh đổi: xử lý lâu thì member bị đá khỏi group vì vượt rebalance timeout. Doc khuyên dùng `PollRecords` để giới hạn số record mỗi lần — config.go (bậc 1).
- **Static membership (`InstanceID`):** khi close thì "does NOT send a leave group request", để restart với cùng ID mà không gây rebalance. Doc khuyên tăng session timeout (mặc định 45 giây) cho đủ thời gian restart. Muốn rời hẳn thì phải dùng lệnh admin. Ngoại lệ: group classic dùng cooperative balancer, nếu vừa bị revoke partition rồi close thì client vẫn gửi leave — config.go (bậc 1).
- **Kubernetes:**
  - Khi xoá pod, kubelet chạy preStop hook (nếu có), rồi gửi SIGTERM tới PID 1. Hết grace period thì gửi KILL.
  - "The default terminationGracePeriodSeconds setting is 30 seconds."
  - Nếu preStop vẫn chạy khi hết grace period thì chỉ được gia hạn một lần 2 giây; preStop cần lâu hơn thì phải tăng `terminationGracePeriodSeconds`.
  - Runtime có thể gửi `STOPSIGNAL` của image thay cho TERM.

  Nguồn: [Kubernetes Pod Lifecycle — Termination of Pods](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination) (bậc 1, docs hiện hành 2026-11).

### Nhận định
- **Khung shutdown cho Go** (minh hoạ, chưa chạy thử):

```go
ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
defer stop()
cl, _ := kgo.NewClient(
    kgo.ConsumerGroup("engine"), kgo.ConsumeTopics("events"),
    kgo.DisableAutoCommit(),
    kgo.OnPartitionsRevoked(func(ctx context.Context, cl *kgo.Client, _ map[string][]int32) {
        drainInFlight()                        // chờ worker của các partition bị thu hồi xong
        _ = cl.CommitMarkedOffsets(ctx)        // commit chặn
    }),
)
for {
    fs := cl.PollRecords(ctx, 500)            // ctx bị cancel khi có SIGTERM -> thoát
    if ctx.Err() != nil { break }
    process(fs)                                // xử lý xong mới MarkCommitRecords
}
drainInFlight()
shCtx, cancel := context.WithTimeout(context.Background(), 20*time.Second) // < grace period
defer cancel()
_ = cl.CommitMarkedOffsets(shCtx)
cl.Close()                                     // gửi LeaveGroup -> rebalance ngay, không chờ session timeout
```

  `CommitMarkedOffsets` là tên hàm agent nhớ, chưa kiểm chứng trong lần đọc này (xem Khoảng trống).
- **Ngân sách thời gian:** `terminationGracePeriodSeconds` ≥ (thời gian drain tối đa) + (commit) + (leave) + dự phòng. Engine có batch hoặc sink chậm nên đặt 60–120 giây và giới hạn thời gian drain bằng context.
- **Rollout:**
  - Dùng `RollingUpdate` với `maxSurge` nhỏ để tránh nhiều đợt rebalance dồn dập.
  - Dùng cooperative-sticky (classic) hoặc protocol KIP-848 để mỗi pod rời chỉ làm dịch chuyển partition của nó, thay vì dừng cả group.
  - Static membership (StatefulSet, `InstanceID` = tên pod) giảm rebalance khi restart nhanh. Đổi lại, partition của pod đó bị dừng tới khi pod quay lại hoặc hết session timeout, nên lag tăng tạm thời.
- **Readiness probe** gần như vô nghĩa với consumer, vì không nhận traffic qua Service. Liveness nên dựa trên "vòng poll còn chạy" (thời gian từ lần poll cuối), không dựa trên HTTP 200 thuần.
- **Không thể tránh trùng hoàn toàn** khi chỉ có at-least-once: crash giữa lúc ghi sink và lúc commit vẫn gây trùng. Giải pháp là sink idempotent hoặc EOS (xem góc delivery semantics).

### Khoảng trống
- Chưa kiểm chứng tên chính xác các hàm `CommitMarkedOffsets` / `CommitUncommittedOffsets` trong source lần này (chỉ xác nhận được `AutoCommitMarks` và `MarkCommitRecords` qua doc).
- Chưa có nguồn bậc 1–2 đo thời gian rebalance khi rolling update có và không có static membership/KIP-848.

## 4. Replay/reprocess: reset offset theo timestamp, xử lý lại sang topic mới, tiered storage (KIP-405), backfill

### Kết luận ngắn
Có hai cách replay:
- **Cách 1, reset offset:** dùng `kafka-consumer-groups.sh --reset-offsets` (`--to-datetime`, `--by-duration`, `--to-earliest`...), và group phải không còn member active. Trong Go có thể tự seek theo timestamp.
- **Cách 2, consumer group mới:** chạy song song với group cũ, ghi sang topic hoặc bảng mới (blue/green), so sánh rồi cắt chuyển.

Tiered storage cho phép giữ dữ liệu lâu hơn để replay, nhưng đọc dữ liệu đã đẩy sang tầng remote chậm hơn và có giới hạn riêng. Nó không hỗ trợ topic compacted. Mức chắc chắn: **cao** về công cụ và giới hạn, **trung bình** về trạng thái các bản sửa lỗi (đã lên kế hoạch cho 4.2).

### Phát hiện có nguồn
- `kafka-consumer-groups.sh --reset-offsets` có hai chế độ: `--dry-run` (mặc định, chỉ lên kế hoạch) và `--execute`. Đề xuất cải tiến nằm ở [KIP-1359](https://cwiki.apache.org/confluence/spaces/KAFKA/pages/430409229/KIP-1359+Improve+usability+of+resetting+group+offsets) (bậc 1, đang là đề xuất). Công cụ gốc ra đời từ [KIP-122](https://kafka-options-explorer.conduktor.io/kip/122/) (bậc 3, chỉ dùng để lần nguồn).
- `--to-datetime` reset về offset sớm nhất sau mốc thời gian (định dạng `yyyy-MM-ddTHH:mm:ss.xxx`). `--by-duration` lùi theo khoảng ISO-8601 (vd `PT0H30M0S`). Phải dừng consumer trước ("has no active members") — [Conduktor CLI tutorial](https://www.conduktor.io/kafka/kafka-consumer-group-management-cli-tutorial) (bậc 2, không rõ ngày).
- **Tiered storage (KIP-405):**
  - Tầng remote (vd S3, HDFS) chứa các segment đã đóng. Kafka không kèm implementation remote storage.
  - Bật theo topic bằng `remote.storage.enable` (mặc định false). `local.retention.ms/bytes` quyết định dữ liệu nằm trên đĩa local bao lâu; `retention.ms/bytes` áp cho cả tầng remote.
  - Dữ liệu cũ thường được đọc cho backfill hoặc phục hồi.
  - Giới hạn: "No support for compacted topics"; segment thiếu producer snapshot (topic tạo trước 2.8.0) không được hỗ trợ.

  Nguồn: [Apache Kafka 4.2 docs — Tiered Storage](https://kafka.apache.org/42/operations/tiered-storage/) (bậc 1, docs 4.2).
- **Bẫy phía consumer khi đọc từ tầng remote:**
  - "each fetch request can only handle a single remote storage partition" (KAFKA-14915), nên latency là tổng latency từng partition.
  - Pool `remote.log.reader.threads` cạn thì "additional reads return empty data".
  - Dữ liệu remote có thể vượt `fetch.max.bytes`, nguy cơ OOM; bộ nhớ bị chặn trên ở mức `fetch.max.bytes + max.partition.fetch.bytes`. Cách giảm: đặt `max.message.bytes <= fetch.max.bytes` và tăng `remote.fetch.max.wait.ms`.
  - Các bản sửa lên kế hoạch cho Kafka 4.2.0.

  Nguồn: [Red Hat Developer, The hidden pitfalls of Kafka tiered storage](https://developers.redhat.com/articles/2025/08/21/hidden-pitfalls-kafka-tiered-storage) (bậc 2, 2025-08-21).
- **Consumer đọc thẳng từ remote storage** (bỏ qua broker) vẫn đang là đề xuất: KIP-1254 "Under Discussion", phụ thuộc KIP-1248 phía broker — [KIP-1254](https://cwiki.apache.org/confluence/display/KAFKA/KIP-1254:+Kafka+Consumer+Support+for+Remote+Tiered+Storage+Fetch) (bậc 1, đề xuất).

### Nhận định
- **Thiết kế cho phép replay ngay từ đầu:**
  1. Xử lý idempotent theo khoá tự nhiên hoặc (topic, partition, offset), để xử lý lại không làm hỏng sink.
  2. Logic phụ thuộc thời gian dùng **event time** trong payload hoặc timestamp của record, không dùng `time.Now()`.
  3. Có một "chế độ replay" khởi động với group ID riêng và điểm bắt đầu theo timestamp. Trong franz-go có thể dùng `kgo.ConsumeResetOffset(kgo.NewOffset().AfterMilli(ts))` cho group mới (agent nhớ API này, chưa kiểm chứng trong lần đọc này), hoặc dùng `kadm` để tìm offset theo timestamp (ListOffsetsAfterMilli).
- **So sánh hai cách:**
  - **Reset offset của group đang chạy:** đơn giản, nhưng phải dừng engine và ghi đè lên sink đang phục vụ.
  - **Group mới ghi sang topic/bảng mới (backfill song song):** an toàn hơn, so sánh được trước khi cắt chuyển. Tốn gấp đôi tài nguyên, và phải giới hạn tốc độ để không giành băng thông broker với luồng realtime (dùng quota hoặc giới hạn trong engine).
- Backfill qua tiered storage nên chạy với ít partition song song mỗi lần fetch và theo dõi riêng latency fetch. Topic compacted (state, changelog) không tier được nên giữ toàn bộ trên đĩa local.
- DLQ nên có công cụ "redrive": đọc DLQ và produce lại vào topic gốc hoặc topic retry. DLQ chỉ có ích khi đi kèm cách xử lý lại.

### Khoảng trống
- Chưa xác nhận bản sửa KAFKA-14915 thực sự đã có trong Kafka 4.2.0 hay chưa. Nguồn mới chỉ nói là "planned".
- Chưa kiểm chứng tên chính xác của API franz-go cho seek theo timestamp (`NewOffset().AfterMilli`, `kadm.ListOffsetsAfterMilli`).

## 5. Schema evolution: Schema Registry, Avro/Protobuf/JSON Schema, chế độ tương thích, wire format, thư viện Go

### Kết luận ngắn
Wire format chuẩn của Confluent: 1 byte magic `0`, 4 byte schema ID (big-endian), rồi tới message index (chỉ Protobuf), rồi tới dữ liệu. Chế độ tương thích mặc định là BACKWARD (nâng cấp consumer trước). Với Protobuf, Confluent khuyên BACKWARD_TRANSITIVE. Trong Go:
- `franz-go/pkg/sr`: client registry và Serde cho wire format. Mang theo codec Avro/Protobuf/JSON riêng, vd `hamba/avro`.
- `confluent-kafka-go/schemaregistry/serde`: đầy đủ serde (avrov2, protobuf, jsonschema) nhưng cần cgo vì dựa trên librdkafka.

Mức chắc chắn: **cao** (docs gốc).

### Phát hiện có nguồn
- **Wire format:** byte 0 = version/magic `0`, byte 1–4 = schema ID "big-endian", tiếp theo là message index cho Protobuf (zigzag, có tiền tố độ dài; message top-level đầu tiên mã hoá thành một số `0`), sau đó là dữ liệu.
- **Từ Confluent Platform 8.1.1** có tuỳ chọn đặt **schema GUID 16 byte vào header** (`__key_schema_id` / `__value_schema_id`), payload chỉ còn dữ liệu. Bật bằng `value.schema.id.serializer=...HeaderSchemaIdSerializer`. Deserializer đọc header trước, không có thì đọc tiền tố payload. Lưu ý: đổi cách này cho **key** có thể làm thay đổi partitioning.

  Nguồn: [Confluent docs, Formats, Serializers, and Deserializers](https://docs.confluent.io/platform/current/schema-registry/fundamentals/serdes-develop/index.html) (bậc 1, docs CP 8.x, 2026).
- **Các chế độ tương thích:**
  - BACKWARD: consumer dùng schema X đọc được dữ liệu X và X-1. FORWARD: dữ liệu X đọc được bởi consumer X và X-1. FULL = cả hai.
  - Các bản `_TRANSITIVE` áp với **mọi** version cũ, không chỉ X-1. NONE: tắt kiểm tra.
  - "The Confluent Schema Registry default compatibility type is `BACKWARD`, not `BACKWARD_TRANSITIVE`."
  - Thứ tự nâng cấp: BACKWARD thì "upgrade all consumers before you start producing new events". FORWARD thì producer trước. FULL thì thứ tự nào cũng được.
  - Thêm hoặc xoá field có default là "fully compatible".
  - Protobuf: "best practice for Protobuf is to use BACKWARD_TRANSITIVE, as adding new message types is not forward compatible."

  Nguồn: [Confluent docs, Schema Evolution and Compatibility](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) (bậc 1, docs CP 8.x).
- **`franz-go/pkg/sr` (v1.8.0):** client Schema Registry và `Serde` "encodes and decodes values according to the schema registry wire format". `ConfluentHeader` "starts with 0, then big endian uint32 of the ID, then index (only protobuf)". Gói này **không** tự khám phá schema hay tự giải mã kiểu ("does not provide schema auto-discovery and type auto-decoding"). Có `CheckCompatibility` và API đọc/ghi mức compatibility; hỗ trợ kiểu Avro, Protobuf, JSON — [sr docs](https://pkg.go.dev/github.com/twmb/franz-go/pkg/sr) (bậc 1, v1.8.0).
- **`confluent-kafka-go`:** "Production applications should serialize with Schema Registry". Có serializer JSON Schema, Avro, Protobuf. Thư viện dựa trên librdkafka nên "CGO_ENABLED must NOT be set to 0" — [confluent-kafka-go README](https://github.com/confluentinc/confluent-kafka-go) (bậc 1, không rõ ngày). Gói `schemaregistry/serde/avrov2` có trên pkg.go.dev ([link](https://pkg.go.dev/github.com/confluentinc/confluent-kafka-go/v2/schemaregistry/serde/avrov2), bậc 1).
- **`hamba/avro/v2`:** codec Avro thuần Go, hỗ trợ union và TextMarshaler — [pkg.go.dev](https://pkg.go.dev/github.com/hamba/avro/v2) (bậc 1, không rõ ngày).

### Nhận định
- **Định nghĩa cho người mới:**
  - *Schema* = hợp đồng cấu trúc message.
  - *Subject* = "tên" chứa các version schema, thường là `<topic>-value`.
  - *Compatibility check* = registry từ chối đăng ký schema mới nếu phá hợp đồng.
- **Gợi ý chọn định dạng:**
  - Protobuf hợp với team Go (codegen tốt, `protoc-gen-go`).
  - Avro hợp hệ sinh thái Kafka/JVM/Flink và kiểu dữ liệu động.
  - JSON Schema dễ debug nhưng tốn băng thông và parse chậm hơn.
- **Engine nên có:**
  1. Bước decode tách riêng, có cache theo schema ID (ID → decoder).
  2. Lỗi decode hoặc ID không xác định thì đưa record vào DLQ kèm header ghi lý do. Không làm crash vòng poll.
  3. Đăng ký schema ở CI/CD (producer), không tự đăng ký lúc runtime (auto-register).
  4. Đặt mức compatibility cho từng subject (BACKWARD_TRANSITIVE nếu cần replay từ đầu topic).
  5. Theo dõi header schema ID kiểu mới (CP 8.1.1+) nếu producer trong hệ thống dùng nó.
- Chọn `franz-go/pkg/sr` + codec riêng thì giữ được Go thuần (không cgo, build tĩnh dễ). Chọn serde của confluent-kafka-go thì có sẵn nhiều tính năng (data contracts...) nhưng kéo theo cgo/librdkafka.

### Khoảng trống
- Chưa kiểm chứng `franz-go/pkg/sr` đã hỗ trợ header schema GUID mới của CP 8.1.1 hay chưa.
- Không có benchmark tốc độ decode Avro/Protobuf/JSON trong Go từ nguồn độc lập.
- Không kiểm tra được hỗ trợ data contracts/CSFLE trong serde Go của Confluent (README không nhắc tới).

## 6. Testing: integration test với testcontainers/kfake, chaos testing

### Kết luận ngắn
Nên dùng ba tầng test:
1. Unit test logic xử lý với record giả (không cần Kafka).
2. Integration test nhanh bằng **kfake**: broker giả trong process, hỗ trợ consumer group classic và KIP-848, tiêm lỗi được bằng `Fault`/`ControlKey`.
3. Integration test "thật" bằng **testcontainers-go** (Kafka KRaft trong Docker).

Chaos test (mạng chậm hoặc đứt bằng Toxiproxy, pod bị kill khi rollout) dùng để kiểm chứng không mất hoặc trùng dữ liệu. Mức chắc chắn: **cao** về công cụ, **thấp–trung bình** về quy trình chaos cụ thể cho Kafka (chủ yếu là nhận định).

### Phát hiện có nguồn
- **kfake:** "a fake Kafka broker for testing".
  - Hỗ trợ group classic, KIP-848 và share group; có handler cho transaction.
  - Khởi tạo bằng `kfake.NewCluster(kfake.NumBrokers(n), kfake.SeedTopics(p, "t"))`. Có `DataDir` để lưu xuống đĩa, `MaxVersions` để giả lập Kafka cũ.
  - Tiêm lỗi: `ControlKey(key, fn)` / `Control(fn)` chặn từng loại request, chạy một lần trừ khi gọi `KeepControl`. `Fault(...)` tiêm mã lỗi theo topic/group/partition/node, có `Hits/Wait/Remove`.
  - Có `VirtualNetwork` để chạy với `testing/synctest`.
  - Module ở pseudo-version `v0.0.0-...`, chưa có tag ổn định.

  Nguồn: [kfake docs](https://pkg.go.dev/github.com/twmb/franz-go/pkg/kfake) (bậc 1, không rõ ngày).
- **testcontainers-go module kafka:** `kafka.Run(ctx, "confluentinc/confluent-local:7.5.0", kafka.WithClusterID("test-cluster"))`, lấy địa chỉ bằng `Brokers(ctx)`. KRaft cần tối thiểu `confluent-local:7.4.0`. Từ v0.45.0 có `WithTLS()`. Tài liệu chỉ nói tới image `confluentinc/confluent-local`; image khác thì tự kiểm tra tương thích KRaft — [Testcontainers for Go, Kafka module](https://golang.testcontainers.org/modules/kafka/) (bậc 1, không rõ ngày).
- **Toxiproxy (Shopify):** TCP proxy "for simulating network conditions", điều khiển qua HTTP API (cổng 8474). Có các toxic `latency`, `bandwidth`, `timeout`, `reset_peer`, `slicer`, và có client Go — [Shopify/toxiproxy](https://github.com/Shopify/toxiproxy) (bậc 1, không rõ ngày).

### Nhận định
- **Các kịch bản test bắt buộc cho engine:**
  1. *Kill giữa chừng:* dừng engine sau khi xử lý xong nhưng trước khi commit, khởi động lại, rồi kiểm tra không thiếu record nào (chấp nhận trùng; nếu có idempotency thì kết quả sink không đổi).
  2. *Rebalance khi đang xử lý:* thêm hoặc bớt consumer trong lúc chạy và kiểm tra commit không "rewind". Dùng kfake hoặc testcontainers với 2–3 client.
  3. *Poison message:* payload không decode được thì đi vào DLQ, không chặn partition.
  4. *Lỗi broker tạm thời:* dùng kfake `Fault` trả `NOT_COORDINATOR` hoặc `REBALANCE_IN_PROGRESS` khi commit, kiểm tra retry.
  5. *Mạng chậm:* dùng Toxiproxy thêm latency hoặc cắt kết nối và quan sát lag, timeout, rebalance.
  6. *Shutdown:* gửi SIGTERM và đo thời gian drain so với grace period.
- **Khi nào dùng công cụ nào:**
  - kfake: test nhanh, chạy trong CI không cần Docker, tiêm lỗi chính xác.
  - testcontainers: kiểm tra hành vi broker thật (version, config, độ trễ thật). Chạy chậm hơn và cần Docker.
- Với Toxiproxy và Kafka cần cấu hình advertised listener trỏ qua proxy, nếu không client sẽ nối thẳng tới broker và bỏ qua proxy. Đây là hiểu biết chung, trang Toxiproxy không nói tới.
- **Chaos ở mức Kubernetes** (kill pod ngẫu nhiên, rolling update liên tục) kết hợp một job "đối soát" (đếm record vào và ra theo key) là cách thực tế nhất để chứng minh delivery semantics.

### Khoảng trống
- Không tìm nguồn về công cụ chaos Kubernetes cụ thể (Chaos Mesh, Litmus) cho Kafka consumer, do giới hạn số lượt gọi tool.
- Chưa kiểm chứng testcontainers-go có module hay hướng dẫn cho image `apache/kafka` chính thức.
- Caveat về advertised listener của Toxiproxy với Kafka chưa có nguồn.

## Truy vấn đã chạy
- kafka lag exporter "estimate consumer group lag in time" interpolation (standard)
- kafka consumer metrics records-lag-max rebalance-rate-per-hour last-poll-seconds-ago documentation (standard)
- kafka tiered storage documentation consumer fetch remote log limitations 4.0 (standard)
- kafka-consumer-groups.sh --reset-offsets --to-datetime --by-duration --dry-run --execute (standard)
- kafka topic config message.timestamp.type CreateTime LogAppendTime message.timestamp.after.max.ms (standard)
- Trang đã fetch trực tiếp: OTel messaging spans và Kafka semconv; Burrow wiki; seglo/kafka-lag-exporter; kminion; kprom; kotel; kfake; kslog; sr; hamba/avro; testcontainers-go kafka; Confluent serdes và schema-evolution; Kubernetes pod-lifecycle; Kafka 4.2 tiered storage; Red Hat tiered storage pitfalls; SoftwareMill lag; confluent-kafka-go README; Toxiproxy; source franz-go (`kgo/client.go`, `kgo/config.go`, `kgo/consumer_group.go`, `kadm/groups.go`) nhánh master ngày 2026-11-13.
