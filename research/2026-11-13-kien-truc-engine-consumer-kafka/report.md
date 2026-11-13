---
title: Kiến trúc engine consumer Kafka xử lý dữ liệu realtime bằng Go
date: 2026-11-13
question: Một engine consumer Kafka xử lý dữ liệu realtime (tự viết bằng Go, quy mô vừa đến lớn) nên có kiến trúc ra sao, gồm những mảng kỹ thuật nào, và khi gặp bài toán cụ thể thì chọn kỹ thuật/kiến trúc nào (kể cả khi nào nên dùng framework thay vì tự viết)?
tags: [kafka, consumer, golang, franz-go, stream-processing, kien-truc]
---

# Engine consumer Kafka bằng Go: at-least-once, offset tracker, sink idempotent

> **Câu hỏi:** Engine consumer Kafka tự viết bằng Go nên có kiến trúc nào, gồm những mảng kỹ thuật nào, và chọn kỹ thuật ra sao cho từng loại bài toán? · **Ngày:** 2026-11-13 · **Phạm vi:** Apache Kafka 3.x–4.x (KRaft, KIP-848), tương thích Redpanda khi liên quan; Go là ngôn ngữ chính, framework JVM chỉ để so sánh; chạy trên Kubernetes; quy mô từ 10k đến hơn 500k msg/s. Không bàn tuning broker. · **Kế thừa:** không

## Tóm tắt

Một engine consumer Kafka viết bằng Go nên là một pipeline bốn tầng (nhận → giải mã → xử lý → ghi sink), bọc trong một runtime lo offset, rebalance, retry/DLQ, metric và shutdown. Engine nên mặc định chạy **at-least-once** và làm cho sink **idempotent**, vì exactly-once của Kafka chỉ trọn vẹn khi cả đầu vào lẫn đầu ra đều là topic Kafka. Độ song song đến từ một goroutine cho mỗi partition, hoặc từ worker pool băm theo key khi mỗi message tốn I/O. Khi đã xử lý lệch thứ tự trong một partition, engine bắt buộc phải có một **offset tracker** chỉ commit tới mốc liên tục cao nhất. Về client, franz-go là nền mặc định hợp lý nhất ở thời điểm 11/2026: Go thuần, có transactions, cooperative-sticky, KIP-848 và share group. Nên dùng nó cùng static membership trên StatefulSet. Phần stateless và state theo key đơn giản (đếm, dedupe, profile thực thể) tự viết trong Go là khả thi. Window theo event-time, watermark, join stream-stream, state lớn cần checkpoint, hay EOS có state thì nên giao cho Flink hoặc Kafka Streams. Các khuyến nghị kiến trúc có độ chắc cao, vì docs chính thức, source client và case study của Uber, Cloudflare, Grab, Segment khớp nhau. Con số hiệu năng thì yếu: không có benchmark độc lập nào cho client Go ở mức trên 500k msg/s. **Mục 11 gom mọi thứ thành bản đồ quyết định theo đặc điểm bài toán.**

**Điểm chính**
- Ba mức delivery chỉ phản ánh thứ tự giữa "xử lý" và "commit". EOS chỉ áp dụng trong vòng Kafka→Kafka; sink ngoài phải dùng idempotency hoặc lưu offset trong cùng transaction DB [1][2][3].
- Offset chỉ là một con số cho mỗi partition, nên xử lý song song trong partition buộc phải commit tới mốc liên tục cao nhất. Uber, Confluent Parallel Consumer và các pipeline Go đều làm vậy. Commit "offset mới nhất đã xong" là lỗi mất dữ liệu đã xảy ra trong thực tế [4][5][6].
- franz-go mặc định dùng cooperative-sticky và autocommit at-least-once. KIP-848 GA từ Kafka 4.0, nhưng franz-go khuyên chỉ bật khi broker từ 4.3 trở lên [7][8].
- "Exactly-once" ở các case thực tế (Segment, OpenMeter) đều là at-least-once cộng dedupe theo key, không dùng Kafka transactions [9][10].
- Với consumer, scale theo lag (KEDA) hoặc giữ số pod cố định bằng số partition (Grab) đều tốt hơn HPA theo CPU. Trần scale là số partition [11][12][13].
- Nên chuyển sang framework khi cần window event-time, join, state lớn có checkpoint, hoặc EOS có state. Go chưa có thư viện trưởng thành cho các phần này; goka chỉ có state table theo key [14][15].

## Mục lục

1. **Kafka nhìn từ phía consumer**: topic, partition, offset, consumer group, rebalance, lag.
2. **Kiến trúc tham khảo**: sơ đồ bốn tầng cộng runtime, đối chiếu với Uber, Cloudflare, Grab, Segment, Netflix.
3. **Delivery semantics và offset**: ba mức đảm bảo, cách commit, transactions/EOS, sink idempotent.
4. **Lỗi, retry và DLQ**: phân loại lỗi, retry tại chỗ, retry topic, DLQ, outbox/inbox.
5. **Song song và backpressure**: bốn mô hình song song, offset tracker, pause/resume.
6. **Consumer group, rebalance và scale**: eager, cooperative, static membership, KIP-848, autoscale theo lag.
7. **Throughput**: các nút vặn fetch, nén, GC của Go.
8. **Stateful processing**: window, join, event-time, watermark, state store, tự làm trong Go khó tới đâu.
9. **Vận hành**: metric, tracing, shutdown, replay, schema, testing.
10. **Hệ sinh thái Go và framework**: so sánh client, thư viện Go, Kafka Streams và Flink khác nhau ở đâu.
11. **Bản đồ quyết định**: đặc điểm bài toán → kỹ thuật, bảng quyết định thiết kế kèm đánh đổi, khi nào rời Go sang framework, anti-pattern.

## 1. Kafka nhìn từ phía consumer: mọi khó khăn nằm ở khoảng cách giữa "đã xử lý" và "đã commit"

Kafka lưu dữ liệu theo **topic**. Mỗi topic chia thành nhiều **partition**, và mỗi partition là một log chỉ ghi nối thêm. Thứ tự chỉ được đảm bảo *trong một partition*, không phải trên cả topic. Producer băm key của message để chọn partition, nên mọi message cùng key rơi vào cùng partition, *miễn là số partition không đổi*. Tăng số partition về sau sẽ phá thứ tự theo key, vì message cùng key có thể nằm ở partition khác trước và sau khi tăng [16].

Mỗi record trong partition có một số thứ tự gọi là **offset**. Consumer đọc tuần tự và định kỳ lưu lại vị trí đã đọc, gọi là *commit offset*. Javadoc của Kafka nói rõ: "The committed offset should always be the offset of the next message that your application will read". Vì vậy xử lý xong record offset N thì phải commit N+1; hàm `CommitRecords` của franz-go tự cộng 1 [3][17]. Javadoc cũng phân biệt *position* ("the offset of the next record that will be given out") với *committed position* ("the last offset that has been stored securely") [3]. Khi consumer khởi động lại, hoặc khi partition chuyển sang member khác, việc đọc tiếp bắt đầu từ committed position chứ không phải position.

Nhiều instance cùng `group.id` tạo thành một **consumer group** và chia nhau các partition. Mỗi partition chỉ thuộc tối đa một member tại một thời điểm. Vì vậy số consumer song song hữu ích tối đa bằng số partition; consumer thừa "will have to sit idle" [11][18]. Khi member vào hoặc ra, group chạy **rebalance** để chia lại partition [19]. **Lag** là số record còn tồn, bằng log end offset (offset kế tiếp sẽ được ghi) trừ committed offset.

**Nhận định:** gần như mọi bài toán trùng hoặc mất dữ liệu đều xoay quanh khoảng cách giữa "đã xử lý tới đâu" và "đã commit tới đâu" tại lúc crash hoặc rebalance. Commit sớm hơn tiến độ xử lý thì mất dữ liệu. Commit muộn hơn thì trùng. Các mục sau đều là những cách quản lý khoảng cách này.

| Thuật ngữ | Nghĩa | Vì sao engine quan tâm |
|---|---|---|
| Partition | Log con của topic, đơn vị thứ tự và đơn vị song song | Trần số consumer; cố định từ đầu vì đổi về sau phá thứ tự theo key |
| Offset / committed offset | Số thứ tự record; vị trí đã lưu = record kế tiếp cần đọc | Commit N+1 sau khi xong N; commit sai gây mất hoặc trùng |
| Consumer group | Các instance chia nhau partition | Đơn vị scale ngang |
| Rebalance | Chia lại partition khi member đổi | Nguồn trùng lặp chính; thời gian dừng xử lý |
| Lag (offset / thời gian) | Số record còn tồn; độ trễ tính bằng giây | Tín hiệu autoscale và alert |
| Key / partitioner | Hàm băm chọn partition từ key | Quyết định thứ tự theo entity và co-partitioning khi join |

## 2. Kiến trúc tham khảo: bốn tầng xử lý bọc trong một runtime lo offset và lỗi

Các công ty tự viết consumer engine đều đi tới cùng một cách tách tầng. Cloudflare có thư viện Go nội bộ Messagebus-Client bọc Sarama, cấu hình "có chính kiến", tự xoay vòng chứng chỉ mTLS và có sẵn metric. Trên đó họ dựng một connector framework, cấu hình pipeline bằng ba biến `READER`, `TRANSFORMATIONS`, `WRITER` [20]. Mỗi pod của Grab Coban gồm **Trigger** (kết nối nguồn), **Runtime** (điều phối) và **Pipeline plugin** do người dùng viết; quy mô gần **400 tỉ event mỗi tuần** [12]. OpenMeter viết consumer Go cho billing theo chuỗi: poll → lọc event hỏng sang DLQ → dedupe trong batch → dedupe qua Redis → insert ClickHouse → ghi key vào Redis → commit offset [10]. Uber uForwarder dùng cùng mô hình, nhưng tầng xử lý nằm ở service khác: proxy fetch từ Kafka, đẩy từng message qua gRPC, rồi chỉ commit khi an toàn [4].

**Nhận định:** từ các case trên có thể rút ra kiến trúc tham khảo dưới đây. Mỗi khối được giải thích ngay sau sơ đồ, và các mục 3–9 đi sâu vào từng khối.

```text
                    +----------------------------- Engine instance (1 pod) ------------------------------+
                    |                                                                                    |
 Kafka topic        |  [1] SOURCE           [2] DECODE           [3] PROCESS            [4] SINK         |
 partition P0..Pn ->|  franz-go client  ->  cache theo        ->  handler theo      ->  ghi theo batch   |-> DB / topic / API
                    |  poll, pause/resume   schema ID             partition / key       idempotent       |
                    |  callback rebalance   validate              state store           (upsert, dedupe) |
                    |         ^             lỗi decode -> DLQ     (tuỳ chọn)                  |          |
                    |         |                                                               |          |
                    |         +----------- [5] OFFSET TRACKER theo partition <------- ack ----+          |
                    |                      commit tới mốc liên tục cao nhất                              |
                    |                                                                                    |
                    |  [6] RUNTIME: phân loại lỗi + router retry/DLQ | metric | tracing qua header       |
                    |               health check theo tiến độ | graceful shutdown | trần in-flight       |
                    +------------------------------------------------------------------------------------+
                               | lỗi tạm thời                                  | lỗi không xử lý được
                               v                                               v
                    retry topic tầng 1 -> tầng 2 -> ... ----------------->  DLQ topic -> công cụ redrive

 Bên ngoài engine:  lag exporter (kminion / Burrow / kadm.Lag) -> Prometheus -> alert + KEDA autoscale
                    Schema Registry | changelog topic compacted (nếu stateful) | StatefulSet + PVC
```

**Source** là client Kafka. Nó poll record, tham gia consumer group, nhận callback khi partition được giao hoặc bị thu hồi, và có thể tạm dừng fetch từng partition. **Decode** tách payload theo wire format của Schema Registry, cache decoder theo schema ID, và đẩy record hỏng sang DLQ thay vì làm vòng poll crash. **Process** là logic nghiệp vụ, chạy theo partition hoặc theo key; nếu có state thì giữ state store cục bộ cho mỗi partition. **Sink** ghi kết quả theo batch, và phải idempotent để chịu được việc xử lý lại. **Offset tracker** ghi nhận record nào đã xong, rồi chỉ commit tới mốc liên tục cao nhất. **Runtime** là phần "khung" mà mọi pipeline dùng chung. Đây chính là thứ Cloudflare đóng gói thành thư viện, để service mới có sẵn metric và health check [20][21].

Bảng sau tóm tắt cơ chế đáng học và lỗi đã gặp ở từng case.

| Công ty | Mô hình | Cơ chế đáng học | Lỗi hoặc bài học |
|---|---|---|---|
| Uber uForwarder | Push proxy qua gRPC, hơn **1.000** service | Out-of-order commit tracker; phát hiện head-of-line (HOL) khi tracker dùng **>90%** và phần chưa commit **<2%**; delay bằng pause riêng partition | Thiết kế cũ dừng cả fetcher để chờ delay, nên retry topic chỉ được 1 partition [4] |
| Uber (2018) | Retry topic theo tầng + DLQ | Mỗi tầng delay dài hơn; DLQ có list/purge/merge | Retry topic làm mất thứ tự so với traffic sống [22] |
| Cloudflare | SDK Go bọc Sarama; connector Reader/Transform/Writer | Health check theo *tiến độ* commit; fast lane/slow lane; song song trong partition | Liveness chỉ kiểm tra kết nối nên bỏ sót consumer kẹt; state theo partition không dọn khi revoke gây restart dây chuyền [21][23] |
| Grab Coban | Plugin Go trên Kubernetes | Số pod cố định = số partition, cộng VPA | HPA theo CPU gây tải lệch, giảm được **~45%** tài nguyên khi bỏ [12] |
| Segment | Worker Go + RocksDB dedupe | Topic output là nguồn sự thật; input chỉ ack sau khi RocksDB đã persist | Không có bước nguyên tử chung, nên phải đối chiếu lại khi khởi động [9] |
| OpenMeter | Consumer Go thay Kafka Connect | Mọi bước idempotent nên fail thì làm lại cả batch | Một event hỏng làm fail cả batch sink trong Kafka Connect [10] |
| LinkedIn Brooklin | Pipeline di chuyển dữ liệu | Tự pause partition lỗi, checkpoint theo partition | Flush đồng bộ của producer có thể làm đứng pipeline vài phút [24] |
| Netflix | Keystone / Data Mesh trên Flink | Mỗi job một cluster Flink, checkpoint lên S3, control plane khai báo | Stateful nặng thì không tự viết [25][26] |

Còn một lựa chọn kiến trúc lớn là **pull** (mỗi service tự chạy consumer) hay **push proxy** (một tầng trung tâm đọc Kafka rồi đẩy tới service). Wix chọn proxy vì chi phí đọc: đọc chiếm khoảng **40%** hoá đơn Confluent Cloud, ghi chỉ khoảng **10%**, do nhiều consumer group đọc cùng topic. Proxy đọc mỗi topic đúng một lần, và bài viết đặt mục tiêu giảm 30% chi phí Kafka [27]. Phía ngược lại, Kai Waehner cho rằng proxy chỉ đáng làm ở quy mô cực lớn và khi có platform team. Ở quy mô nhỏ đến vừa, proxy "adds unnecessary complexity, overhead, and risk", nên bắt đầu bằng consumer pull và thêm song song kiểu Parallel Consumer khi gọi DB/HTTP chậm [28]. **Nhận định:** với quy mô 10k–500k msg/s và một vài team, nên chọn SDK pull dùng chung; push proxy chỉ đáng bàn khi hàng trăm service cùng đọc và chi phí đọc trở thành vấn đề.

## 3. Delivery semantics: mặc định at-least-once, exactly-once chỉ trọn vẹn khi Kafka→Kafka

### Ba mức đảm bảo thực chất là thứ tự giữa xử lý và lưu vị trí

**At-most-once** nghĩa là message được giao tối đa một lần; nếu có lỗi thì có thể mất và không giao lại. **At-least-once** nghĩa là message được giao một hoặc nhiều lần. **Exactly-once** nghĩa là mỗi message có hiệu lực đúng một lần [1]. Phía consumer, ba mức này chỉ là hệ quả của thứ tự hai việc. Lưu vị trí rồi mới xử lý thì được at-most-once, vì crash giữa chừng sẽ bỏ qua phần chưa xử lý. Xử lý rồi mới lưu vị trí thì được at-least-once, vì crash giữa chừng sẽ xử lý lại [1]. Javadoc mô tả đúng cửa sổ trùng này: lỗi xảy ra "after the insert into the database but before the commit", nên consumer thay thế xử lý lại batch cuối [3]. Phía producer, retry sau một lần ghi thực ra đã thành công sẽ tạo bản trùng trong log, nên at-least-once là mặc định [1].

Exactly-once có giới hạn rõ ràng ngay từ người thiết kế. Theo Narkhede, "exactly-once semantics is guaranteed within the scope of Kafka Streams' internal processing only". Gọi RPC tới store ngoài thì "The resulting side effects would not be guaranteed exactly once". Tua lại offset thì không thể "rollback the associated state in an external system" [2]. KIP-98 còn nói đảm bảo transaction là "from the point of view of the producer": consumer không chắc đọc trọn mọi message của một transaction đã commit, ví dụ khi seek vào giữa transaction [29]. Gunnar Morling diễn đạt gọn: không thể có exactly-once *delivery*, nhưng có thể có exactly-once *processing* nếu lưu idempotency key nguyên tử cùng kết quả xử lý [30]. **Nhận định:** bảng dưới gom các điểm vỡ theo từng phía.

| Phía | Gây trùng khi | Gây mất khi | Cách chữa |
|---|---|---|---|
| Producer | Retry sau khi ghi thật ra đã thành công | Tắt retry | Idempotent producer (bật mặc định ở Java từ Kafka 3.0) [31] |
| Consumer | Crash hoặc rebalance giữa lúc xử lý xong và lúc commit | Commit trước khi xử lý; xử lý song song mà commit offset lớn nhất | Commit sau xử lý; offset tracker (mục 5) |
| Sink ngoài | Xử lý lại sau crash | Ghi lỗi mà vẫn commit | Sink idempotent hoặc lưu offset trong transaction DB |

**Nhận định:** mặc định thiết kế nên là "at-least-once cộng sink idempotent", hay còn gọi là effectively-once. Transaction Kafka chỉ đáng dùng khi output là topic Kafka.

### Commit offset: autocommit chỉ an toàn khi xử lý xong trước lần poll kế tiếp

Với Java, `enable.auto.commit=true` commit theo chu kỳ `auto.commit.interval.ms`, nhưng có điều kiện: "you must consume all data returned from each call to poll(Duration) before any subsequent calls". Nếu không, committed offset có thể vượt tiến độ xử lý và gây "missing records" [3]. librdkafka (nền của confluent-kafka-go) có thêm một tầng nữa. `enable.auto.offset.store` mặc định `true`, tức offset được "store" ngay khi message *được giao* cho ứng dụng, chưa chắc đã xử lý xong. Docs khuyên ứng dụng xử lý lâu nên đặt `enable.auto.offset.store=false` và gọi `offsets_store()` *sau* khi xử lý [32].

franz-go bật autocommit mặc định, chu kỳ 5 giây. Nó chỉ commit những gì đã poll ở lần *trước*: "This one-poll lag is INTENTIONAL and is what makes default autocommit at-least-once" [7][17]. Ngoài chế độ mặc định, franz-go còn ba chế độ khác, tóm tắt ở bảng dưới.

| Chế độ franz-go | Đảm bảo | Dùng khi |
|---|---|---|
| Autocommit mặc định | At-least-once nếu xử lý đồng bộ trong vòng poll; "likely some duplicate processing during rebalances" | Consumer đơn giản, xử lý xong trước lần poll kế |
| `GreedyAutoCommit` | Commit mọi thứ đã poll; "may result in message loss if your application crashes" | Metric/log chấp nhận mất |
| `AutoCommitMarks` + `MarkCommitRecords` | "a halfway point between autocommitting and manually committing": chỉ autocommit record đã đánh dấu; không cho rewind | Xử lý tách khỏi vòng poll, đánh dấu sau khi xong |
| `DisableAutoCommit` + commit tay | Tự quyết định thời điểm | Lưu offset ngoài Kafka, EOS tự làm |

Nguồn của bảng: [7][17].

Rebalance là nguồn trùng lặp chính. Docs của franz-go nêu một kịch bản cụ thể. Member A đã commit offset 4 nhưng xử lý tới 30, rồi partition chuyển sang B. Nếu A không commit trong `OnPartitionsRevoked` thì B bắt đầu từ 4 và xử lý lại 4–29. Tệ hơn, A có thể commit 30 *sau* khi B đã commit 50, tức "rewind" commit của B [7]. franz-go quản lý group độc lập với việc poll, nên "A rebalance may occur at any moment". Option `BlockRebalanceOnPoll` chặn rebalance từ lúc poll tới khi gọi `AllowRebalance`. Đổi lại, member có thể bị đá khỏi group nếu chờ quá rebalance timeout [7]. Callback `OnPartitionsRevoked` (còn kịp commit) và `OnPartitionsLost` (đã mất partition, không được commit nữa) phải xử lý khác nhau [7]. Về đồng bộ hay bất đồng bộ: `commitSync` chặn tới khi xong và ném lỗi khi partition không còn thuộc consumer, còn `commitAsync` giữ đúng thứ tự gửi nhưng lỗi chỉ được báo qua callback hoặc bị bỏ qua [3]. **Nhận định:** mẫu phổ biến là commit bất đồng bộ hoặc theo chu kỳ trong luồng chính để giữ throughput, và commit đồng bộ ở các ranh giới (revoke, shutdown) để chắc chắn.

Đoạn mã dưới minh hoạ at-least-once với xử lý tuần tự trong partition. Đây là minh hoạ chưa biên dịch và chưa chạy. Các option lấy từ source franz-go v1.22.3; riêng tên `CommitMarkedOffsets` chưa được đối chiếu.

```go
// Minh hoạ, chưa biên dịch/chạy.
cl, err := kgo.NewClient(
    kgo.SeedBrokers(brokers...),
    kgo.ConsumerGroup("engine"),
    kgo.ConsumeTopics("events"),
    kgo.AutoCommitMarks(),                        // chỉ autocommit record đã Mark
    kgo.FetchIsolationLevel(kgo.ReadCommitted()), // franz-go mặc định ReadUncommitted
    kgo.InstanceID(os.Getenv("POD_NAME")),        // static membership (mục 6)
    kgo.OnPartitionsRevoked(func(ctx context.Context, cl *kgo.Client, revoked map[string][]int32) {
        waitWorkers(revoked)            // chờ phần đang xử lý của các partition bị thu hồi
        _ = cl.CommitMarkedOffsets(ctx) // commit chặn trước khi partition sang member khác
    }),
)
if err != nil { log.Fatal(err) }
for {
    fs := cl.PollRecords(ctx, 1000)
    if ctx.Err() != nil { break }
    fs.EachRecord(func(r *kgo.Record) {
        if err := handle(ctx, r); err != nil {
            routeFailure(ctx, r, err) // retry topic/DLQ, phải nhận ack trước khi Mark (mục 4)
        }
        cl.MarkCommitRecords(r) // tuần tự trong partition nên offset luôn liên tục
    })
}
```

### Idempotent producer và transactions: EOS cho read-process-write giữa các topic

**Idempotent producer** chống trùng do retry. Mỗi producer nhận một PID, và broker theo dõi sequence number theo từng partition. Write có sequence nhỏ hơn mong đợi bị coi là trùng và bỏ qua; lớn hơn thì là mất message (lỗi fatal). Đảm bảo này chỉ có "within a single producer session" [29]. Producer Java bật `enable.idempotence=true` và `acks=all` mặc định từ Kafka 3.0 (KIP-679) [31]. librdkafka, và do đó confluent-kafka-go, vẫn mặc định **false** [32].

**Transaction** dùng một `transactional.id` bền qua restart. Coordinator đảm bảo "Exactly one active producer with a given TransactionalId", và fencing bằng epoch, tức instance cũ (zombie) bị chặn ghi. `transaction.timeout.ms` mặc định 60.000 ms [29]. Consumer đặt `read_committed` thì chỉ nhận record của transaction đã commit, đọc tới Last Stable Offset (LSO). Transaction marker chiếm offset nhưng không được trả về, nên **dãy offset có lỗ hổng** [3]. Mặc định isolation khác nhau giữa các client: Java dùng `read_uncommitted`, librdkafka dùng `read_committed`, franz-go dùng `ReadUncommitted` [29][32][7]. KIP-447 (Kafka 2.6, broker từ 2.5) cho một producer phục vụ nhiều input partition qua `sendOffsetsToTransaction(offsets, groupMetadata)`, kèm generation và member ID để fence ngay khi sai [33]. KIP-890 ở Kafka 4.0 chặn "hanging transaction", loại lỗi làm LSO không tiến và khiến consumer `read_committed` kẹt. Nó được điều khiển bằng feature flag `transaction.version=2` [34][35]. KIP-939 cho phép tham gia two-phase commit với hệ thống ngoài, nhưng trạng thái phát hành chưa rõ (xem *Chưa kiểm chứng được*) [36].

Chi phí transaction không lớn nếu transaction đủ dài. Với message 1 KB và transaction 100 ms, throughput producer giảm **3%** so với producer at-least-once có thứ tự. Kafka Streams EOS với commit interval 100 ms giảm **15–30%**, còn với commit 30 s thì không đo được overhead. Các số này đo năm 2017 [2]. Cái giá thật là độ trễ: downstream chỉ thấy dữ liệu khi transaction commit. Confluent Cloud for Apache Flink commit transaction khoảng mỗi phút, nên consumer `read_committed` thấy độ trễ tới khoảng 1 phút. Chạy at-least-once thì độ trễ end-to-end dưới 100 ms [37].

Trong Go, franz-go có `GroupTransactSession`, "abstracts away the proper way to begin and end a transaction when consuming in a group, modifying records, and producing (EOS)". Khi có rebalance trước lúc kết thúc transaction, nó chọn *abort* thay vì chặn rebalance. `End` chỉ commit nếu được yêu cầu commit, group chưa rebalance, và commit offset thành công [38]. franz-go luôn đặt `RequireStable` khi đọc offset (KIP-447), và "strongly recommended" dùng broker từ 2.5 trở lên [39]. Đoạn mã dưới là minh hoạ chưa chạy; tên `kgo.TransactionalID` và `kgo.TryCommit` lấy theo example `transactions/eos` của franz-go và chưa đối chiếu.

```go
// Minh hoạ EOS Kafka→Kafka, chưa biên dịch/chạy.
sess, err := kgo.NewGroupTransactSession(
    kgo.SeedBrokers(brokers...),
    kgo.TransactionalID("enricher-"+podName),
    kgo.ConsumerGroup("enricher"),
    kgo.ConsumeTopics("raw"),
    kgo.FetchIsolationLevel(kgo.ReadCommitted()),
)
for {
    fs := sess.PollFetches(ctx)
    if err := sess.Begin(); err != nil { return err }
    fs.EachRecord(func(r *kgo.Record) { sess.Produce(ctx, enrich(r), nil) })
    committed, err := sess.End(ctx, kgo.TryCommit)
    // committed == false: transaction bị abort (vd vì rebalance), batch này sẽ được đọc lại
    _ = committed; _ = err
}
```

### Sink idempotent: offset theo partition là idempotency key tự nhiên

Khi sink nằm ngoài Kafka, engine phải tự làm cho việc ghi lặp lại vô hại. Morling phân tích các loại khoá. UUIDv4 buộc phải nhớ mọi key đã thấy. UUIDv7/ULID có timestamp nên biết được key nào "quá cũ". Khoá đơn điệu tăng thì chỉ cần lưu key lớn nhất, và mọi key bằng hoặc nhỏ hơn là trùng. **Offset Kafka theo partition chính là khoá đơn điệu tự nhiên:** lưu offset mới nhất của mỗi partition trong sink, bỏ mọi record có offset nhỏ hơn hoặc bằng, tốn không gian hằng số [30]. Javadoc mô tả cách làm triệt để hơn: tắt auto commit, lưu offset cùng kết quả trong sink, rồi khi được gán partition thì `seek` tới offset đã lưu; làm vậy có thể "fully atomic and give 'exactly once' semantics" [3]. Các thao tác tự nhiên idempotent gồm upsert và update có điều kiện theo version. Còn bảng inbox với unique constraint trên (consumer, event ID), insert cùng transaction với cập nhật nghiệp vụ, là cách chung cho nghiệp vụ không upsert được [40].

**Nhận định:** bảng chọn kỹ thuật theo loại sink:

| Sink | Delivery đạt được | Cách commit | Kỹ thuật ở sink |
|---|---|---|---|
| Metric/log, chấp nhận mất ít | at-most hoặc at-least | Autocommit mặc định | Ghi thẳng |
| DB nghiệp vụ | at-least-once, kết quả như exactly-once | Mark sau khi xử lý, commit đồng bộ khi revoke | Upsert theo khoá nghiệp vụ, version check, hoặc inbox |
| DB cần exactly-once thật | exactly-once cho sink đó | Lưu (topic, partition, offset) trong cùng transaction DB, seek khi được gán | Bảng offset trong DB |
| Topic Kafka khác | exactly-once | Transaction (`GroupTransactSession`) | Downstream đọc `read_committed` |
| HTTP/API bên thứ ba | at-least-once | Sau khi nhận 2xx | Gửi idempotency key `topic/partition/offset` hoặc event ID; API không hỗ trợ key thì trùng là không tránh được |

## 4. Lỗi, retry và DLQ: phân loại lỗi trước, chọn đường retry theo yêu cầu thứ tự

Retry ngay trong consumer chặn tiến độ, vì "Without a success response, the Kafka consumer will not commit a new offset". Message lỗi bị đọc lại mãi, còn message mới phải chờ [22]. Uber giải quyết bằng một chuỗi **retry topic**, mỗi tầng có consumer group riêng. Handler lỗi thì publish message sang retry topic kế tiếp, trả về thành công và commit offset gốc. Tầng cuối là **dead letter queue (DLQ)**, tức topic chứa message không xử lý được. Mỗi tầng có độ trễ tăng dần, và tác giả gọi chúng là "delayed processing queues": handler chạy "at least after the configured timeout but possibly later". DLQ cần hỗ trợ list, purge và merge (đẩy lại vào retry topic đầu tiên). Đánh đổi lớn nhất: retry topic tách message khỏi luồng chính nên **mất thứ tự**, và consumer phải idempotent [22].

Confluent mô tả bốn pattern, trải từ ưu tiên thứ tự tới ưu tiên liveness [41]. Pattern 1 là *stop on error*: dừng tới khi có người can thiệp, hợp với luồng phải đúng thứ tự như CDC. Pattern 2 là *DLQ không retry*, dành cho event hỏng định dạng. Pattern 3 là *retry topic cộng ứng dụng retry riêng*, chấp nhận mất thứ tự. Pattern 4 là *giữ thứ tự bằng redirect topic*. Ứng dụng chính nhớ các item đang có event nằm trong retry, và event mới của cùng item cũng chuyển sang retry. Khi retry thành công, ứng dụng retry phát tombstone để ứng dụng chính bỏ item khỏi danh sách. Ví dụ tồn kho cho thấy vì sao thứ tự quan trọng: xử lý "giảm" trước "tăng" có thể gây đặt hàng sai.

Uber uForwarder giải quyết delay theo cách hợp với engine Go. `DelayProcessManager` chỉ kiểm tra message chưa xử lý đầu tiên của mỗi partition, **pause riêng partition** còn trong thời gian delay, giữ message đã poll trong RAM, và resume khi hết delay. Nhờ vậy retry topic dùng được nhiều partition [4]. Uber cũng tự phát hiện HOL blocking: khi tracker dùng trên 90% và phần chưa commit dưới 2%, tức "a small amount of messages blocking the majority of messages", thì offset kẹt bị huỷ, đẩy sang DLQ và đánh dấu đã commit [4]. Kafka core không có retry hay DLQ cho consumer thường; Kafka Streams mới có DLQ tích hợp từ 4.2 (KIP-1034) [42][43]. Engine Go phải tự làm phần này, hoặc dùng middleware Retry và Poison Queue của Watermill [44].

Khi engine vừa cập nhật DB vừa phải phát event mới, có hai pattern bổ trợ. **Outbox** ghi event vào bảng outbox cùng transaction với dữ liệu, rồi một relay (vd Debezium) đẩy lên Kafka. Debezium đặt `id` của bảng outbox vào header để "remove duplicate messages", và dùng aggregate ID làm key [45]. **Inbox** là bảng dedupe ở phía đọc như đã nói ở mục 3. Outbox chỉ cho at-least-once, vì relay có thể publish rồi crash trước khi đánh dấu [40].

**Nhận định:** engine nên có một bộ *phân loại lỗi* trước khi chọn đường đi, và mỗi đường có đánh đổi riêng:

| Loại lỗi | Ví dụ | Đường đi | Ghi chú |
|---|---|---|---|
| Poison / không thể xử lý | Deserialize lỗi, schema sai, vi phạm validate | Thẳng DLQ, kèm header: topic/partition/offset gốc, lý do, số lần thử, timestamp | Không retry; có công cụ redrive |
| Lỗi tạm thời | Timeout DB/API, 5xx, throttling | Retry tại chỗ vài lần (backoff + jitter), rồi retry topic (không chặn) hoặc pause partition (chặn, giữ thứ tự) | Chọn theo yêu cầu thứ tự |
| Downstream sập toàn bộ | DB chết, mọi message đều lỗi | Circuit breaker: pause consume, không đổ hàng loạt vào retry/DLQ | Chưa có nguồn bậc 1 cho mẫu này |

**Nhận định:** yêu cầu thứ tự quyết định đường retry. Cần thứ tự tuyệt đối theo partition (CDC, sổ cái) thì dùng stop-on-error hoặc retry chặn vô hạn kèm alert. Cần thứ tự theo key thì dùng pattern 4 của Confluent, hoặc worker theo key giữ record lỗi trong hàng đợi của key đó. Không cần thứ tự thì dùng retry topic kiểu Uber cộng DLQ. Ghi sang retry/DLQ rồi commit offset gốc là một "dual write" Kafka→Kafka. Vì vậy produce sang DLQ phải nhận ack *trước* khi mark offset gốc, hoặc đặt cả hai trong một transaction. Mỗi khi chờ delay, dùng pause partition thay cho `time.Sleep`, để vòng poll không bị chặn quá rebalance timeout.

## 5. Song song và backpressure: song song vượt số partition thì bắt buộc có offset tracker

### Bốn mô hình song song, đánh đổi giữa độ song song và thứ tự

franz-go "avoiding channels and goroutines where not necessary": client không tự sinh goroutine xử lý, nên mô hình song song là việc của ứng dụng [46]. Confluent Parallel Consumer định nghĩa ba mức chia nhỏ đơn vị công việc từ partition xuống key hoặc message [16]. Ở mức *partition*, "At most only one message from any given input partition will be in flight". Ở mức *key*, thứ tự được giữ theo key trong partition. Ở mức *unordered*, mọi message xử lý tự do [5]. Kafka 4.2 thêm mô hình thứ tư do broker quản lý: **share group** (KIP-932). Ở đó "many consumers can share a single partition, records are individually acknowledged, and unacknowledged records are automatically redelivered". Share group "production-ready" từ 4.2.0 (2026-02-17), và franz-go hỗ trợ từ v1.21.0 qua option `ShareGroup` [47][48].

| Mô hình | Thứ tự | Song song tối đa | Commit offset | Hợp khi |
|---|---|---|---|---|
| 1 goroutine/partition | Theo partition | = số partition được giao | Đơn giản: commit offset cuối đã xử lý | Xử lý nhanh, CPU-bound, cần thứ tự chặt |
| Worker pool băm theo key | Theo key | N worker, có thể lớn hơn nhiều so với số partition | Cần offset tracker, commit tới mốc liên tục | Mỗi message gọi I/O chậm, cần thứ tự theo entity |
| Pool không thứ tự | Không | Tuỳ ý | Như trên; crash thì replay nhiều hơn | Job độc lập: notification, enrich |
| Share group (KIP-932) | Không | Nhiều consumer trên một partition | Broker theo dõi ack từng record | Hàng đợi công việc; cần Kafka ≥ 4.2 |

Nguồn của bảng: [5][16][47]. Theo biểu đồ của Confluent, chế độ key tiến gần hiệu năng unordered khi số key tăng [16]. **Nhận định:** nói ngược lại, ít key hoặc *hot key* (một key chiếm phần lớn traffic) sẽ biến worker giữ key đó thành nút cổ chai, dù pool lớn đến đâu. Cloudflare cho thấy lợi ích của song song trong partition với tác vụ I/O-bound. Họ consume theo batch và cho mỗi message một goroutine, nâng throughput từ khoảng **10 lên hơn 120 scan/s**, tức hơn 10 lần, mà không thêm phần cứng; đổi lại, crash giữa batch thì phải làm lại nhiều hơn [23].

**Nhận định:** với mô hình một goroutine cho mỗi partition, cách rẻ nhất là xử lý cả slice record của partition trong một goroutine, thay vì gửi từng record qua channel. Minh hoạ dưới chưa chạy, và giả định tên trường `p.Records` của `FetchTopicPartition`.

```go
// Minh hoạ, chưa biên dịch/chạy. Mỗi partition một goroutine, giữ thứ tự theo partition.
fs := cl.PollRecords(ctx, 10000)
var wg sync.WaitGroup
fs.EachPartition(func(p kgo.FetchTopicPartition) {
    wg.Add(1)
    go func() {
        defer wg.Done()
        writeWithRetry(ctx, p.Records)    // bulk insert idempotent; lỗi cuối cùng → DLQ, không bỏ qua
        cl.MarkCommitRecords(p.Records...) // chỉ mark khi cả slice đã có kết cục
    }()
})
wg.Wait() // đơn giản, nhưng một partition chậm kéo chậm cả lượt poll
```

### Offset tracker: chỉ commit tới mốc liên tục cao nhất

Offset là *một con số cho mỗi partition*, nên nó không diễn đạt được trạng thái "đã xong 10 và 12 nhưng chưa xong 11". Khi xử lý song song trong partition, chỉ được commit tới **mốc liên tục cao nhất** (low watermark). Ví dụ 10, 11, 12 đang chạy, 10 và 12 đã xong: commit 11, nghĩa là "mọi offset nhỏ hơn 11 đã xong". Nếu crash, 11 và 12 sẽ chạy lại, nên sink vẫn phải idempotent. Parallel Consumer làm đúng như vậy: chỉ commit "offsets for messages which have been successfully processed", "in order ... regardless of concurrency level or retries". Các offset đã xong nằm *sau* mốc được mã hoá (run-length hoặc BitSet) vào commit metadata, giới hạn **4 KB mỗi partition**. Khi map chạm 75% giới hạn thì nó ngừng nhận record mới, tức là backpressure [5]. Uber uForwarder có out-of-order commit tracker cùng nguyên lý [4]. Pipeline Go giữ thứ tự theo session mà InfoQ mô tả cũng có commit loop chỉ tiến tới offset hoàn thành liên tục cao nhất. Nhóm này ghi nhận lỗi thật: commit "offset mới nhất đã xong" làm mất message chưa xong khi crash [6]. Lưu ý thêm: franz-go `CommitRecords` lấy offset lớn nhất của mỗi partition [17], nên gọi nó với record vừa xong mà không qua tracker sẽ ngầm bỏ qua record chưa xong.

Minh hoạ tracker dưới chưa chạy. Nó lưu *record đã giao* theo thứ tự poll thay vì tính `offset+1`, vì transaction marker và compaction tạo lỗ hổng trong dãy offset [3].

```go
// Minh hoạ, chưa biên dịch/chạy. Một tracker cho mỗi partition được giao.
type tracker struct {
    mu      sync.Mutex
    pending []*kgo.Record          // record đã giao cho worker, theo thứ tự poll
    done    map[*kgo.Record]bool
}
func (t *tracker) dispatched(r *kgo.Record) { t.mu.Lock(); t.pending = append(t.pending, r); t.mu.Unlock() }
func (t *tracker) finished(r *kgo.Record)   { t.mu.Lock(); t.done[r] = true; t.mu.Unlock() }
func (t *tracker) inFlight() int            { t.mu.Lock(); defer t.mu.Unlock(); return len(t.pending) }

// advance trả record cuối của đoạn liên tục đã xong (nil nếu chưa tiến); đem record này đi MarkCommitRecords.
func (t *tracker) advance() *kgo.Record {
    t.mu.Lock(); defer t.mu.Unlock()
    var last *kgo.Record
    for len(t.pending) > 0 && t.done[t.pending[0]] {
        last = t.pending[0]
        delete(t.done, last)
        t.pending = t.pending[1:]
    }
    return last
}
```

Dispatcher cho worker pool theo key cũng chỉ vài dòng. Channel có giới hạn chính là backpressure thô:

```go
// Minh hoạ, chưa chạy. N worker, mỗi worker một channel có buffer giới hạn.
fs.EachRecord(func(r *kgo.Record) {
    trackers[tp(r)].dispatched(r)
    h := fnv.New32a(); h.Write(r.Key)
    workers[h.Sum32()%uint32(len(workers))] <- r // đầy thì block vòng poll
})
// worker: handle(r) → trackers[tp(r)].finished(r); vòng commit định kỳ gọi advance() rồi MarkCommitRecords
```

**Nhận định:** tracker phải đi kèm một trần số record "in flight" cho mỗi partition, giống ngưỡng 75% của Parallel Consumer. Không có trần thì một record kẹt làm khoảng chưa commit phình vô hạn. Khi một offset kẹt quá lâu, cần cơ chế như uForwarder: timeout theo từng offset, đẩy sang DLQ hoặc slow lane, rồi coi như xong. InfoQ ghi nhận rằng detector "partition kẹt" dựa trên số in-flight luôn khác rỗng sẽ báo sai dưới tải liên tục, và họ phải đổi sang timeout theo từng offset [6]. Chưa thấy thư viện Go phổ biến nào làm sẵn phần tracker như Parallel Consumer (Java), nên phần này phải tự viết.

### Backpressure: ba tầng, tinh dần từ channel tới pause partition

**Backpressure** là cơ chế để consumer không đọc nhanh hơn khả năng xử lý. Tầng thô nhất là channel có giới hạn như trên. Nó đơn giản, nhưng chặn *mọi* partition, kể cả partition đi tới sink nhanh. Tầng thứ hai là `PauseFetchPartitions`/`ResumeFetchPartitions` của franz-go. Hàm này ngừng fetch partition cụ thể ("Paused partitions persist until resumed") trong khi vòng poll vẫn chạy và member vẫn ở trong group [49]. Tầng thứ ba là giới hạn bộ nhớ fetch của client. `MaxConcurrentFetches` mặc định không giới hạn, và "paired with FetchMaxBytes, can upper bound the maximum amount of memory". Client chỉ coi một fetch là xong khi ứng dụng đã poll hết dữ liệu của nó, nên xử lý chậm tự làm chậm fetch [7].

```go
// Minh hoạ, chưa chạy. Pause partition khi hàng đợi của nó vượt ngưỡng cao, resume khi tụt dưới ngưỡng thấp.
switch n := trackers[tp].inFlight(); {
case n > highWater:
    cl.PauseFetchPartitions(map[string][]int32{topic: {part}})
case n < lowWater:
    cl.ResumeFetchPartitions(map[string][]int32{topic: {part}})
}
```

Rủi ro chính của backpressure là chặn vòng poll quá lâu thì bị đá khỏi group. Với client Java và librdkafka, giới hạn là `max.poll.interval.ms`, mặc định **5 phút** [50][32]. franz-go chạy heartbeat ở nền, nên rủi ro chỉ xuất hiện khi bật `BlockRebalanceOnPoll` và xử lý lâu hơn `RebalanceTimeout` (mặc định 60 giây) [7]. Pipeline session-ordered của InfoQ và uForwarder đều dùng pause theo partition khi channel đầy, rồi resume khi tải giảm. InfoQ ghi nhận một hệ quả: pause theo partition ảnh hưởng chéo tới các session khác cùng partition [6][4]. **Nhận định:** pause partition là cách đúng khi sink chậm cục bộ (một shard DB nóng). Còn khi sink chết hẳn thì dùng circuit breaker (mục 4).

## 6. Consumer group và scale: cooperative-sticky cộng static membership, KIP-848 khi broker đủ mới

Rebalance có ba thế hệ, khác nhau ở mức "dừng thế giới":

| Giao thức | Cách chạy | Ai dừng | Trạng thái |
|---|---|---|---|
| Classic eager | Mọi member trả hết partition, leader chia lại | Cả group: "a complete halt" | Cũ |
| Classic cooperative (KIP-429) | Hai vòng rebalance liên tiếp; chỉ thu hồi partition phải chuyển | Chỉ partition bị chuyển, nhưng vẫn qua barrier đồng bộ toàn group | Kafka 2.4+; mặc định của franz-go |
| KIP-848 (`group.protocol=consumer`) | Broker tính phân công, gửi lệnh revoke/assign qua heartbeat; không có barrier toàn group | "Only consumers losing a partition pause on that partition" | GA từ Kafka 4.0, opt-in; dự kiến mặc định ở 5.0 |

Nguồn của bảng: [51][19][8][7].

Nâng cấp từ eager lên cooperative cần hai lần rolling bounce: lần đầu khai cả hai assignor, lần sau bỏ assignor cũ. Ở cooperative, `onPartitionsRevoked` chỉ được gọi trên tập partition bị chuyển, và có thể không được gọi, nên không dùng nó để phát hiện rebalance [19]. franz-go mặc định dùng cooperative-sticky. Nếu một member chỉ hỗ trợ eager tham gia, cả group bị hạ xuống eager, mọi partition bị thu hồi và đọc lại từ committed offset; docs viết "It is not recommended to downgrade once a group is cooperative" [7].

**Static membership** (KIP-345, `group.instance.id`) giải quyết một vấn đề khác: restart nhanh. Static member đã biết khi quay lại sẽ nhận lại phân công cũ "without doing any rebalance". Nó không gửi leave group khi offline, và chỉ bị loại khi offline quá session timeout. Động lực chính là ứng dụng stateful, nơi "one of the biggest performance bottleneck is the state shuffling" [52]. Trong franz-go đó là option `InstanceID`. Docs "strongly recommended" tăng session timeout (mặc định 45 giây) cho đủ thời gian restart. Nhược điểm: phải tự quản lý ID, và rebalance chậm hơn khi client chết thật [7].

KIP-848 chuyển heartbeat, session timeout và assignor sang cấu hình broker. Nó không hỗ trợ assignor phía client, nhưng nâng cấp online được bằng rolling restart [8]. Mức hỗ trợ ở các client Go khác nhau. franz-go thêm `ServerSideBalancer()` ở v1.22.0, nhưng docs viết: "It is recommended to use this only if you are on Kafka 4.3+. Before that, it is possible to receive a STALE_MEMBER_EPOCH error during an offset commit … that the client cannot handle itself" [7][48]. confluent-kafka-go tuyên bố KIP-848 "production-ready" từ v2.12.0, vẫn opt-in [53]. Sarama mới có API `ConsumerGroupDescribe`; membership theo KIP-848 thì chưa có (issue #3818, mở 2026-09-30) [54][55]. Chưa có benchmark công khai nào đo thời gian rebalance của KIP-848; Confluent chỉ nói "significantly faster" [51].

**Nhận định:** cấu hình mặc định hợp lý cho engine Go mới là franz-go với cooperative-sticky, cộng static membership (`InstanceID` bằng tên pod của StatefulSet, ví dụ `consumer-3`), và session timeout lớn hơn thời gian restart pod. Chỉ bật KIP-848 khi broker từ 4.3 trở lên. Với engine stateful, static membership quan trọng hơn cả cooperative, vì nó tránh phải dựng lại state mỗi lần restart.

**Số partition** phải tính cho mức scale tối đa ngay từ đầu. Cloudflare rút ra bài học: khi sự cố "không thể chỉ thêm consumer để tăng tốc", vì một partition chỉ có một consumer trong group [20]. Mặt khác, tăng partition về sau phá thứ tự theo key [16]. **Nhận định:** nên đặt số partition không nhỏ hơn số instance tối đa nhân số goroutine theo partition mỗi instance, hoặc dùng worker pool theo key để tách độ song song khỏi số partition.

**Autoscale theo lag.** KEDA Kafka scaler tính số replica xấp xỉ `ceil(tổng lag / lagThreshold)`; `lagThreshold` mặc định 10. Số replica bị chặn trên bởi số partition, trừ khi bật `allowIdleConsumers`. Option `excludePersistentLag` bỏ qua partition kẹt, còn `ensureEvenDistributionOfPartitions` chỉ cho số replica chia hết số partition [11]. Có hai bẫy được docs nêu: khi chưa có offset commit thì lag âm, và với `minReplicaCount: 0` thì KEDA có thể scale về 0 rồi không lên lại được [11]. trivago dùng `lagThreshold: 100`, `cooldownPeriod: 300` s, scale về 0, và giảm từ khoảng **50 xuống 1–2 replica-giờ mỗi ngày** ở mỗi region. Họ gặp ba bẫy: group không hoạt động quá 2 tuần bị xoá theo policy; CPU và RAM "stay flat when sinks are blocked on I/O"; và sink khởi động chậm có rủi ro phục vụ dữ liệu cũ [13]. Grab bỏ HPA theo CPU/memory vì tải lệch giữa các pod, chuyển sang số pod cố định bằng số partition cộng VPA, và giảm khoảng **45%** tài nguyên so với mức requested [12].

**Nhận định:** bẫy lớn nhất của autoscale là vòng phản hồi rebalance. Lag tăng thì KEDA scale up, mỗi lần scale là một lần rebalance, rebalance làm dừng xử lý nên lag tăng thêm. Giảm thiểu bằng cooperative-sticky hoặc KIP-848, cộng `cooldownPeriod` và cửa sổ ổn định scale-down dài. Static membership không giúp được ở đây, vì scale thật sự thêm hoặc bớt member. Ngoài ra, lag theo offset không phản ánh độ trễ: 10.000 message lag trên topic 100k msg/s chỉ là 0,1 giây, nhưng trên topic 100 msg/s là 100 giây. Muốn scale theo SLA thì nên xuất metric lag theo giây (mục 9) và dùng scaler Prometheus.

## 7. Throughput: nút cổ chai thường là sink và allocation, không phải Kafka

Các nút vặn phía consumer gồm kích thước và thời gian chờ của mỗi fetch, số record mỗi lần poll, và nén ở producer. franz-go có vài mặc định khác Java mà người mới dễ bỏ sót. Cột "Gợi ý" không có trích dẫn là **nhận định** của người viết.

| Config (Java) | Mặc định Kafka 4.2 | franz-go | Ý nghĩa | Gợi ý |
|---|---|---|---|---|
| `fetch.min.bytes` | 1 | `FetchMinBytes` = 1 | Broker chờ đủ bấy nhiêu byte mới trả | Khoảng 100.000 nếu ưu tiên throughput [18] |
| `fetch.max.wait.ms` | 500 | `FetchMaxWait` = **5 s** | Chờ tối đa nếu chưa đủ byte | Đặt rõ trong franz-go |
| `max.partition.fetch.bytes` | 1 MiB | `FetchMaxPartitionBytes` = 1 MiB | Trần mỗi partition mỗi fetch | Tăng khi throughput rất lớn |
| `fetch.max.bytes` | 50 MiB | `FetchMaxBytes` = 50 MiB; có thể buffer tới số broker × giá trị này | Trần mỗi fetch | Giới hạn kèm `MaxConcurrentFetches` để vừa `GOMEMLIMIT` |
| `max.poll.records` | 500 | `PollRecords(ctx, n)` | Số record mỗi lần poll | 500–10.000 tuỳ kích thước batch sink |
| Nén (producer) | — | — | Nén theo batch | `lz4` "recommended for performance"; `batch.size` 100.000–200.000, `linger.ms` 10–100 [18] |

Nguồn của bảng: [50][7][18]. Hai giới hạn `fetch.max.bytes` và `max.partition.fetch.bytes` không tuyệt đối: batch đầu tiên quá cỡ vẫn được trả để consumer tiến được [50]. Docs franz-go "strongly recommended" đặt `FetchMaxBytes` khi dữ liệu nén tốt, để việc giải nén không ăn hết RAM [7].

Riêng với Go, chi phí GC phụ thuộc chủ yếu vào *tốc độ cấp phát*: "doubling GOGC will double heap memory overheads and roughly halve GC CPU cost", và cách giảm chi phí là "have the GC manage fewer values to begin with". `GOMEMLIMIT` dành cho triển khai trong container có bộ nhớ cố định, nên chừa thêm 5–10% headroom. Giới hạn này là "soft" để tránh thrashing [56].

**Nhận định:** ở mức 10k–100k msg/s, vài pod với cấu hình mặc định thường là đủ, và nút cổ chai gần như luôn là sink. Tune theo thứ tự: ghi sink theo batch (bulk insert hoặc pipeline); dùng `PollRecords` với n khoảng 500–5.000; nếu latency cho phép thì tăng `FetchMinBytes` lên khoảng 100 KB và đặt `FetchMaxWait` 100–500 ms. Ở mức trên 500k msg/s cho cả cụm, các việc chính là: có đủ partition (thường hàng trăm) để chia cho nhiều pod; tăng `FetchMaxPartitionBytes` lên vài MiB nhưng giữ tổng bộ nhớ fetch dưới `GOMEMLIMIT`; bật lz4 hoặc zstd cùng batch lớn ở producer; **không decode trong vòng poll** mà đẩy decode sang worker; giảm allocation (dùng lại buffer bằng `sync.Pool`, decode vào struct có sẵn, xử lý theo slice thay vì từng record qua channel); và commit theo chu kỳ, không commit đồng bộ từng message. Theo dõi số object cấp phát mỗi message bằng pprof `-alloc_objects`; chỉ số này quan trọng hơn số byte. Mọi khuyến nghị ở mức trên 500k msg/s đều chưa có benchmark độc lập cho client Go để kiểm chứng.

## 8. Stateful processing: state theo key tự viết được, window theo event-time nên giao framework

"Stateful" nghĩa là kết quả xử lý một message phụ thuộc vào các message trước đó: đếm, tổng, dedupe, join. Kafka Streams diễn đạt mối quan hệ cơ bản là "a stream can be viewed as a table, and a table can be viewed as a stream" [57]. Bảng là trạng thái mới nhất của mỗi key; stream là chuỗi thay đổi của bảng.

### Bốn loại window và hai nhóm join

**Window** gom các record cùng key theo khoảng thời gian: "Windowing lets you control how to group records that have the same key" [57].

| Window | Định nghĩa | Ví dụ bài toán |
|---|---|---|
| Tumbling | Kích thước bằng bước nhảy, không chồng lên nhau; mỗi record thuộc đúng một window | Số đơn hàng mỗi 5 phút |
| Hopping | Kích thước cố định, bước nhảy nhỏ hơn kích thước, chồng lên nhau; một record thuộc nhiều window | Trung bình 5 phút gần nhất, cập nhật mỗi phút (mỗi event ghi vào 5 window) |
| Sliding (Kafka Streams) | Hai record chung window nếu timestamp cách nhau không quá kích thước; căn theo record, không theo epoch | Hai sự kiện của cùng user cách nhau ≤ 10 giây |
| Session | Các đoạn hoạt động ngăn cách bởi khoảng nghỉ (inactivity gap); kích thước thay đổi theo dữ liệu | Phiên duyệt web, kết thúc khi im lặng 30 phút |

Nguồn của định nghĩa: [58][59][60]. Ví dụ bài toán trong bảng là minh hoạ của người viết. Cần lưu ý thuật ngữ: Akidau và Flink gọi "sliding window" cho loại có độ dài và chu kỳ cố định, tức tương đương *hopping* của Kafka Streams [61][59].

**Join** chia làm hai nhóm. Join *stream-stream* luôn phải có window, vì nếu không thì join store sẽ tăng vô hạn. Join *stream-table* không cần window, nhưng đòi **co-partitioning**: hai topic phải cùng số partition, và mọi producer dùng cùng partitioner [58]. Kafka Streams kiểm tra số partition lúc chạy nhưng **không kiểm tra được** chiến lược partition [58]. Đây là một bẫy thật trong Go: Sarama mặc định băm bằng fnv, còn Java client và Kafka Streams dùng murmur2. Wiki goka viết rằng nếu không đặt hasher murmur2 thì "keys won't be sent to the expected partitions" [62].

### Event-time, stream-time, watermark và dữ liệu trễ

**Event time** là "the time at which events actually occurred". **Processing time** là "the time at which events are observed in the system". Độ lệch giữa hai loại thường "a highly variable function", nên window theo processing time sẽ xếp sai một phần dữ liệu [61]. Muốn trả lời câu hỏi theo thời gian thực của sự kiện thì phải dùng event-time, và cần một "đồng hồ dữ liệu". Kafka Streams dùng **stream-time**: một thời gian "data-driven", chỉ tiến khi có record mới. Window nhận record tới khi `stream_time >= window_end + grace_period` [57]. **Grace period** "controls how long Kafka Streams will wait for out-of-order data records"; record đến sau đó bị bỏ [57]. Từ Kafka 3.x phải chọn grace tường minh, ví dụ `ofSizeWithNoGrace` nghĩa là grace bằng 0 [63]. Flink dùng **watermark**: "A Watermark(t) declares that event time has reached time t in that stream". Operator nhiều input lấy *min* của các input, nên một partition không có dữ liệu (idle) giữ watermark đứng yên; muốn tránh thì dùng `withIdleness` [64][65]. Allowed lateness mặc định của Flink là 0. Dữ liệu bị bỏ có thể lấy ra qua side output [59].

**Nhận định:** một ví dụ cụ thể. Đếm click mỗi phút bằng tumbling window, grace 30 giây. Một click xảy ra lúc 10:00:58 trên điện thoại mất mạng, tới Kafka lúc 10:01:20. Theo processing-time, nó bị đếm vào phút 10:01, sai. Theo event-time, nó thuộc window [10:00, 10:01). Window này đóng khi stream-time đạt 10:01:30, nên click về lúc stream-time là 10:01:20 vẫn được tính. Nếu nó về khi stream-time đã là 10:01:45 thì quá hạn, và nên được đẩy sang một topic "late" có metric đếm, thay vì bỏ âm thầm.

**Nhận định:** với engine Go tự viết, cách đơn giản và đủ dùng là bắt chước stream-time: mỗi partition giữ `maxSeenTs`, rồi đóng window khi `maxSeenTs` vượt cuối window cộng grace. Chỉ cần watermark kiểu Flink (lấy min qua nhiều nguồn) khi một operator gom dữ liệu từ nhiều partition hoặc topic. Partition thưa event giữ stream-time đứng yên, nên cần thêm timer theo wall-clock nếu kết quả phải ra đúng giờ. Minh hoạ dưới chưa chạy, và giữ state trong RAM, nên crash là mất. Chính điểm này dẫn sang phần state store.

```go
// Minh hoạ, chưa biên dịch/chạy. Tumbling window đếm theo key, một instance cho mỗi partition.
type windowAgg struct {
    size, grace time.Duration
    streamTime  time.Time                      // event-time lớn nhất đã thấy ở partition này
    open        map[time.Time]map[string]int64 // windowStart → key → count
}
func (w *windowAgg) add(key string, ts time.Time) (late bool) {
    if ts.After(w.streamTime) { w.streamTime = ts }
    start := ts.Truncate(w.size)
    if !w.streamTime.Before(start.Add(w.size + w.grace)) { return true } // quá grace → topic "late"
    if w.open[start] == nil { w.open[start] = map[string]int64{} }
    w.open[start][key]++
    return false
}
func (w *windowAgg) closeReady(emit func(start time.Time, counts map[string]int64)) {
    for start, counts := range w.open {
        if !w.streamTime.Before(start.Add(w.size + w.grace)) { emit(start, counts); delete(w.open, start) }
    }
}
```

### State store: cục bộ theo partition, sao lưu bằng changelog topic

Thiết kế chuẩn của Kafka Streams, Samza và goka giống nhau. State nằm **cục bộ** theo từng partition, trong một store nhúng (embedded KV store). Mỗi store có một **changelog topic** để ghi lại mọi cập nhật, và topic này bật log compaction để chỉ giữ giá trị mới nhất của mỗi key. Khi crash hoặc rebalance, instance mới dựng lại state "by replaying the corresponding changelog topics prior to resuming the processing" [66]. **Standby replica** là bản sao state đầy đủ trên instance khác, giúp có sẵn một instance đã "đuổi kịp" khi cần chuyển [66]. Thời gian phục hồi là vấn đề thật: KIP-441 ghi rằng "some task can get hung up for hours while it rebuilds its state stores". Giải pháp của nó là cấp warmup replica trên instance đích trước khi chuyển quyền sở hữu, với `acceptable.recovery.lag` mặc định 10.000 offset [67]. Ở Kafka Streams 4.3, EOS vẫn xoá state khi crash và restore lại toàn bộ từ changelog. KIP-892 (transactional state store) đang nhắm bỏ bước này [68][69].

Local và remote state có khoảng cách lớn. LinkedIn/Samza xử lý **1,1 triệu request/giây** trên một máy với RocksDB cục bộ. Đọc từ xa (Espresso, 3 node SSD) thì "less than 10,000 requests per second", tức "A 100X difference". Phép đo remote dùng I/O đồng bộ, không batching, năm 2016 [70]. Flink tiếp cận bằng checkpoint kiểu Chandy-Lamport, với barrier "never overtake records", và savepoint để nâng cấp chương trình mà không mất state [71]. Flink 2.0 còn đưa state chính lên remote storage (disaggregated state) [72].

Với Go có ba store nhúng. **Pebble** "inspired by LevelDB/RocksDB", là store mặc định của CockroachDB từ v20.2, "considered stable and production ready". Nó có range deletion và checkpoint, nhưng không có transaction [73]. **BadgerDB** là KV pure Go, theo thiết kế LSM cộng value log, có transaction và TTL [74]. goka mặc định dùng LevelDB [14]. **Nhận định:** Pebble là mặc định hợp lý cho state cục bộ trong Go. Nó không cần cgo, đã chạy production ở quy mô lớn, và có range deletion để xoá cả dải window hết hạn nếu key được thiết kế dạng `key|windowStart`. Store ngoài (Redis, ScyllaDB) hợp khi state phải đọc chung giữa nhiều service, không co-partition được, tải vừa phải, hoặc cần scale nhanh mà không replay state. Cái giá là độ trễ mạng mỗi event và việc offset Kafka không cùng transaction với ghi DB.

### Tự làm trong Go: đủ cho state theo key, quá sức cho window và join phức tạp

goka "extends the concept of Kafka consumer groups by binding a state table to them and persisting them in Kafka". Các thành phần gồm Emitter, Processor, Group table (KV chia theo partition, topic phải compacted) và View (cache chỉ đọc của cả bảng). goka đảm bảo at-least-once và dùng Sarama làm client [14]. README, overview và wiki của goka không nhắc tới window, event-time, grace hay EOS [14][62]. GKES của AWS dựng trên franz-go, có EOS và local state store, nhưng tự nhận "not an all-in-one, do-everything black box"; StateStore "left without comprehensive implementations", và bản mới nhất là từ 2022 [75].

**Nhận định:** các mảnh phải tự viết cho một stateful engine trên franz-go, xếp theo độ khó:

| Mảnh | Việc phải làm | Độ khó |
|---|---|---|
| Task theo partition | Mỗi partition một goroutine, một store (thư mục Pebble riêng hoặc prefix), một partition changelog cùng chỉ số | Thấp |
| Đường ghi | Cập nhật store → gửi changelog → commit input sau khi changelog được ack; EOS thì gói changelog, output và offset vào một transaction | Trung bình |
| Checkpoint cục bộ | Ghi "offset changelog đã áp" vào chính store, cùng batch với dữ liệu, để restart chỉ replay phần thiếu | Trung bình |
| Restore khi được giao partition | Đọc changelog từ checkpoint tới cuối bằng consumer riêng ngoài group, ghi batch vào store, pause input trong lúc đó | Trung bình |
| Window store | Key `key|windowStart`, stream-time theo partition, đóng theo grace, tombstone khi hết hạn | Cao, nhất là session window vì event trễ có thể gộp hai session |
| Timer/punctuator | Theo stream-time và theo wall-clock | Trung bình |
| Join | Stream-table: nạp topic bảng vào store cục bộ; stream-stream: hai window store | Cao |
| Standby/warmup | Instance khác tail changelog sẵn | Cao |
| Gắn với rebalance | Revoke: flush store, chốt checkpoint, commit; assign: restore | Trung bình, dễ sai |

**Nhận định:** các bẫy chính gồm: đổi số partition input làm hỏng ánh xạ key và changelog; lệch hash (fnv và murmur2) phá co-partitioning một cách âm thầm; restore lâu khi pod mới không có đĩa cũ; crash giữa lúc ghi store và ghi changelog làm store "đi trước" changelog (lý do Kafka Streams xoá state khi crash ở EOS); changelog không có tombstone thì phình mãi; và đổi schema của state không có công cụ như savepoint của Flink. **Nhận định:** trên Kubernetes, engine stateful nên chạy bằng StatefulSet có PVC cộng static membership, để pod khởi động lại gặp đúng partition và đĩa cũ, chỉ cần replay phần changelog còn thiếu. Cách này tương đương host affinity của Samza [70]. Segment cho thấy state đơn giản tự viết được ở quy mô lớn: worker Go cộng RocksDB dedupe với cửa sổ **4 tuần**, khoảng **60 tỉ key** (1,5 TB), phát hiện khoảng 0,6% event trùng [9].

## 9. Vận hành: đo lag theo thời gian, shutdown có kỷ luật, thiết kế để replay

### Metric: lag theo offset dễ đánh lừa, cần lag theo thời gian và alert theo xu hướng

Lag theo offset bằng log end offset trừ committed offset. Lag theo thời gian xấp xỉ bằng now trừ timestamp của record tại committed offset. Độ trễ end-to-end bằng lúc sink ghi xong trừ timestamp của record. Client Go không tự có metric lag. Plugin `kprom` của franz-go chỉ có counter mức client (byte, kết nối, fetch theo topic), không có lag hay metric theo partition [76]. Lag lấy được qua `kadm.Client.Lag`. Hàm `CalculateGroupLagWithStartOffsets` tính đúng cho partition chưa có commit mà log start offset khác 0: log end 30, start 10, chưa commit thì lag đúng là 20, không phải 30 [77]. Consumer Java có sẵn `records-lag-max`, `last-poll-seconds-ago` và `rebalance-rate-per-hour`; có thể dùng các tên này khi tự export metric [78][79].

Burrow của LinkedIn đánh giá lag bằng một cửa sổ trượt gồm các lần commit, mặc định 10 điểm. Trạng thái OK nghĩa là trong cửa sổ có lúc lag bằng 0. WARNING nghĩa là offset vẫn tiến nhưng lag không giảm. STALLED nghĩa là consumer vẫn commit nhưng offset không đổi. STOPPED nghĩa là commit mới nhất cũ hơn cửa sổ. Mục đích là tránh "the need for setting a discrete threshold" [80]. Kafka Lag Exporter từng export lag theo giây bằng nội suy, nhưng repo đã archive ngày 2024-03-17 [81]. SoftwareMill (một bên làm công cụ cạnh tranh) chỉ ra rằng nội suy hỏng khi cold start, khi producer ngừng, và trên topic ít traffic: consumer có thể chết trên một topic mỗi ngày một lần mà offset lag vẫn phẳng cả tuần. Cách họ đề xuất là đọc record tại committed offset rồi lấy now trừ timestamp [82]. kminion của Redpanda export lag theo partition, và có chế độ end-to-end tự produce rồi consume để đo roundtrip latency [83]. Timestamp của record mặc định là `CreateTime` do producer đặt; topic dùng `LogAppendTime` thì broker ghi đè bằng đồng hồ của broker [84].

**Nhận định:** bộ metric engine nên tự export:

| Nhóm | Metric | Ghi chú |
|---|---|---|
| Lag | `consumer_lag_records`, `consumer_lag_seconds` theo topic/partition | Đo từ bên ngoài (kminion, Burrow, job dùng `kadm.Lag`), vì consumer chết thì không còn ai báo |
| Throughput | `records_processed_total{outcome=ok|retry|dlq|skip}`, byte | Tỉ lệ outcome là tín hiệu chất lượng dữ liệu |
| Latency | Histogram `process_duration_seconds`, `e2e_latency_seconds` | e2e đo ở sink |
| Group | `rebalances_total`, `partitions_assigned`, thời gian trong callback | Đếm trong `OnPartitionsAssigned/Revoked/Lost` |
| Commit | `commit_errors_total`, `commit_duration_seconds` | |
| Lỗi | `dlq_records_total`, `deserialize_errors_total` | |
| Sống còn | Giây kể từ lần poll cuối | Tương đương `last-poll-seconds-ago`; dùng cho liveness |

**Nhận định:** nên page khi lag theo giây vượt SLO kéo dài, khi Burrow báo STOPPED hoặc STALLED, hoặc khi group không còn member nào. Nên mở ticket khi lag tăng đều 15–30 phút, tỉ lệ DLQ tăng đột biến, rebalance mỗi giờ cao bất thường (dấu hiệu crashloop), hoặc commit lỗi liên tục. Không nên alert trên offset lag tuyệt đối với cùng một ngưỡng cho mọi topic.

### Tracing qua header: link span thay vì parent-child

OpenTelemetry quy định producer "SHOULD attach a message creation context to each message", tức tiêm trace context vào header. Phía consumer có span `receive` (CLIENT) và `process` (CONSUMER). Mặc định nên **link** span process tới creation context thay vì làm con, vì link là "the only option to correlate producer and consumer(s) in batch scenarios" [85]. Convention có attribute riêng cho Kafka như `kafka.offset` và `kafka.message.key`, nhưng vẫn ở trạng thái **Development** [86]. Trong Go, `kotel` của franz-go lo inject/extract header. Span process tạo bằng `Tracer.WithProcessSpan(r)`, và "The user's application code is responsible for ending the span"; option `LinkSpans()` cho span consumer link tới span producer [87]. `kslog` bọc `slog.Logger` thành logger của client [88]. **Nhận định:** mỗi dòng log về record nên có `topic`, `partition`, `offset`, `key` (hoặc hash), `trace_id`. Đây là "toạ độ" để replay chính xác một message lỗi. Trên 100k msg/s, tạo span cho từng record rất tốn, nên sample theo tỉ lệ hoặc chỉ giữ span lỗi ở collector, còn metric vẫn đếm đủ 100%.

### Graceful shutdown và deploy: drain, commit, rồi mới rời group

Khi xoá pod, Kubernetes chạy preStop hook (nếu có), gửi SIGTERM, rồi gửi KILL khi hết grace period. "The default terminationGracePeriodSeconds setting is 30 seconds" [89]. `Close()` của franz-go "leaves any group and closes all connections and goroutines". Nếu đã override `OnPartitionsRevoked` thì "you must manually commit offsets before closing the client" [90]. Rời group không đánh thức một `PollFetches` đang chờ, nên phải cancel context của vòng poll. Không được gọi `Close` hay `LeaveGroup` đồng bộ từ trong callback `OnPartitions*`, vì sẽ deadlock [17]. Static member khi close "does NOT send a leave group request" [7]. Trình tự đúng gồm năm bước: bắt SIGTERM, ngừng poll, drain các record đã nhận, commit đồng bộ, rồi `Close()`. Tất cả phải xong trong grace period.

```go
// Minh hoạ, chưa biên dịch/chạy; tên CommitMarkedOffsets chưa đối chiếu.
ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
defer stop()
// ... vòng poll dùng ctx, thoát khi ctx.Err() != nil ...
drainInFlight()                                                         // chờ worker xong, có giới hạn thời gian
shCtx, cancel := context.WithTimeout(context.Background(), 20*time.Second) // < terminationGracePeriodSeconds
defer cancel()
_ = cl.CommitMarkedOffsets(shCtx)
cl.Close() // không static: gửi LeaveGroup để rebalance ngay; static: giữ partition tới session timeout
```

Cloudflare cho thấy health check chỉ kiểm tra kết nối broker sẽ bỏ sót consumer bị kẹt. Sau rebalance, một consumer có thể chờ mãi một partition không còn sở hữu. Health check mới của họ fail khi committed offset không đổi từ lần check trước trong khi vẫn còn message. Nhưng khi rollout, replica giữ committed offset cũ của partition đã mất lại báo unhealthy sai, gây restart, gây thêm rebalance, thành **lỗi dây chuyền**. Họ sửa bằng cách xoá partition khỏi map khi bị revoke [21]. **Nhận định:** đặt `terminationGracePeriodSeconds` không nhỏ hơn thời gian drain tối đa cộng thời gian commit, leave và một khoảng dự phòng; engine có batch hoặc sink chậm nên dùng 60–120 giây. Readiness probe gần như vô nghĩa với consumer. Liveness nên dựa trên tiến độ (thời gian từ lần poll cuối, commit có tiến hay không). Với at-least-once, rollout gần như không mất dữ liệu nhưng **luôn có thể trùng**.

### Replay và reprocess: thiết kế cho phép chạy lại ngay từ đầu

Có hai cách replay. Cách thứ nhất là reset offset của group bằng `kafka-consumer-groups.sh --reset-offsets` (`--to-datetime`, `--by-duration`, mặc định `--dry-run`, cần `--execute`); group phải không còn member nào đang chạy [91]. Cách thứ hai là chạy group mới song song, ghi sang topic hoặc bảng mới, so sánh rồi mới cắt chuyển. **Tiered storage** (KIP-405) cho phép giữ dữ liệu lâu hơn trên object storage để replay. Nó bật theo topic bằng `remote.storage.enable` và "No support for compacted topics" [92]. Đọc từ tầng remote có bẫy: mỗi fetch request chỉ xử lý một partition remote, và pool thread đọc cạn thì "additional reads return empty data"; các bản sửa được lên kế hoạch cho 4.2.0 [93]. Đọc thẳng từ remote storage, bỏ qua broker, vẫn là đề xuất (KIP-1254) [94]. **Nhận định:** muốn replay an toàn thì phải chuẩn bị từ lúc thiết kế: xử lý idempotent theo khoá tự nhiên hoặc (topic, partition, offset); logic phụ thuộc thời gian dùng event-time trong payload chứ không dùng `time.Now()`; có một "chế độ replay" khởi động với group ID riêng và điểm bắt đầu theo timestamp; và giới hạn tốc độ backfill để không giành băng thông của luồng realtime. DLQ chỉ có ích khi có công cụ redrive đi kèm.

### Schema evolution: wire format 5 byte và chế độ BACKWARD mặc định

Wire format của Confluent Schema Registry gồm byte magic `0`, 4 byte schema ID big-endian, rồi message index (chỉ với Protobuf), rồi dữ liệu. Từ Confluent Platform 8.1.1 có tuỳ chọn đặt schema GUID vào header thay vì tiền tố payload [95]. Chế độ tương thích mặc định là **BACKWARD** (consumer dùng schema mới đọc được dữ liệu cũ), nên phải "upgrade all consumers before you start producing new events". Với Protobuf, docs khuyên BACKWARD_TRANSITIVE [96]. Trong Go, `franz-go/pkg/sr` làm client registry và Serde cho wire format, nhưng "does not provide schema auto-discovery and type auto-decoding", nên phải đi kèm codec như `hamba/avro` [97][98]. confluent-kafka-go có serde đầy đủ nhưng kéo theo cgo [99]. **Nhận định:** tầng decode nên cache decoder theo schema ID, đẩy record có ID lạ hoặc decode lỗi sang DLQ, và đăng ký schema ở CI/CD thay vì auto-register lúc runtime. Nếu cần replay từ đầu topic thì dùng `_TRANSITIVE`.

### Testing: kfake cho CI, testcontainers cho broker thật, Toxiproxy cho mạng xấu

`kfake` là "a fake Kafka broker for testing" chạy ngay trong process. Nó hỗ trợ group classic, KIP-848, share group và transaction, và tiêm lỗi được theo request (`ControlKey`) hoặc theo mã lỗi (`Fault`). Module vẫn ở pseudo-version, chưa có tag ổn định [100]. testcontainers-go chạy Kafka KRaft thật trong Docker [101]. Toxiproxy là TCP proxy để giả lập latency, băng thông thấp, timeout và reset kết nối [102]. **Nhận định:** các kịch bản bắt buộc phải test gồm: kill engine sau khi xử lý nhưng trước khi commit, rồi kiểm tra không thiếu record; thêm/bớt consumer giữa chừng và kiểm tra commit không bị rewind; poison message đi vào DLQ mà không chặn partition; lỗi commit tạm thời như `REBALANCE_IN_PROGRESS` (dùng `Fault` của kfake); mạng chậm (Toxiproxy); và SIGTERM, đo thời gian drain so với grace period. Một job đối soát đếm record vào và ra theo key là cách thực tế nhất để chứng minh delivery semantics.

## 10. Hệ sinh thái Go: franz-go làm nền, thư viện Go chỉ phủ phần stateless và state theo key

### So sánh bốn client Go (11/2026)

| Client | Bản mới nhất | cgo | Transactions/EOS | Cooperative | KIP-848 | Share group | Bảo trì | Khi chọn |
|---|---|---|---|---|---|---|---|---|
| franz-go | v1.22.3 (2026-11-09) | Không | Có (`GroupTransactSession`) | Mặc định | Có, khuyên broker 4.3+ | Có (v1.21.0+) | Rất tích cực, gần như một maintainer | Mặc định cho engine mới |
| confluent-kafka-go | v2.16.1 (2026-10-27) | Có (librdkafka) | Có | Qua cấu hình | Production-ready từ v2.12.0, opt-in | Chưa xác minh | Chậm hơn | Tổ chức đã chuẩn hoá librdkafka, cần hỗ trợ Confluent |
| IBM/sarama | v1.61.1 (2026-09-27) | Không | Producer transaction | Có (v1.60.1+) | Chưa có membership | — | Tích cực | Codebase sẵn có, goka, watermill |
| segmentio/kafka-go | v0.4.51 (2026-04-23) | Không | Không | Không | Không | — | Gần như ngừng | Không nên cho dự án mới |

Nguồn của bảng: [103][46][7][104][53][99][105][106][55][107][108][109]. Một số điểm cần nói thêm. franz-go tự mô tả "Feature complete client (Kafka >= 0.8.0 through v4.4+)" [46]. Theo số liệu của Kafma, trong 90 ngày tới 25/9/2026 franz-go có 386 commit, nhưng một tài khoản xử lý toàn bộ các lần merge, tức có rủi ro "bus factor" [109]. Redpanda Connect dùng franz-go làm client chính [110]. confluent-kafka-go đòi "`CGO_ENABLED` must NOT be set to `0`". Bản build sẵn không có Kerberos/GSSAPI, và build trên máy glibc mới rồi chạy trên máy glibc cũ có thể lỗi [99]. kafka-go chỉ "currently tested with Kafka versions 0.10.1.0 to 2.7.1" [108]. Về hiệu năng, README franz-go chỉ nói định tính "consistently among the fastest and most cpu and memory efficient Kafka clients in Go" [46]. Kafma kết luận "There is no reliable general winner" [109]. **Nhận định:** franz-go cho engine trên Kubernetes lợi thế kép: build tĩnh không cgo (image distroless, cross-compile dễ), và là client Go duy nhất có đủ EOS, KIP-848 lẫn share group. Rủi ro chính là phụ thuộc vào một maintainer.

### Thư viện stream trong Go: không có tương đương đầy đủ của Kafka Streams

| Thư viện | Là gì | Mạnh ở | Thiếu | Client bên dưới |
|---|---|---|---|---|
| goka v1.1.18 (2026-11-11) | Thư viện stateful: state table theo group, lưu trên topic compacted, View để truy vấn | State theo key, phục hồi khi rebalance | Window, event-time, join dựng sẵn, EOS (suy từ docs không nhắc tới) | Sarama |
| Redpanda Connect v4.118.0 / Bento | Pipeline cấu hình YAML + Bloblang | Ingest/transform/route stateless, nhiều connector, CDC | State bền ("no disk-persisted state") | franz-go |
| Watermill v1.5.x | Khung ứng dụng event-driven, router + middleware | Retry, Poison Queue, Deduplicator, Circuit Breaker có sẵn | Không phải engine stream stateful | Sarama |
| GKES (AWS) | Event source trên franz-go, có EOS, state store | Ý tưởng hay | Bản cuối từ 2022, StateStore chưa hoàn chỉnh | franz-go |
| go-streams v0.13.0 | Thư viện stream nhẹ, có window | Đơn giản | State không lưu trên Kafka | — |

Nguồn của bảng: [14][111][112][113][114][115][116][44][117][75][118]. Input Kafka của Redpanda Connect chỉ commit một offset khi mọi message có offset nhỏ hơn đã giao xong. Nó cho tối đa `checkpoint_limit` (mặc định 1024) message song song mỗi partition trước khi backpressure, và commit mỗi 5 giây. Tức là nó có sẵn đúng offset tracker ở mục 5 [114]. Redpanda mua Benthos năm 2024, và WarpStream fork thành Bento "100% MIT licensed" [119][115]. **Nhận định:** goka và watermill-kafka đều dựa trên Sarama, nên thừa hưởng việc chưa có KIP-848.

### Khi nào chuyển sang Flink, Kafka Streams, Spark hay streaming database

Khác biệt cốt lõi giữa Kafka Streams và Flink là mô hình triển khai. Kafka Streams là thư viện nhúng ("code you ship"), còn Flink là runtime cụm ("infrastructure you operate"). Khi cả hai cùng làm được, "you choose on operations and team, not capability" [15]. Kafka Streams có song song bị chặn bởi số partition, chỉ đọc/ghi Kafka, và phục hồi state bằng replay changelog. Flink tách song song khỏi partition, kết nối DB và object storage, phục hồi từ checkpoint trên storage bền, nhưng thường cần đội platform riêng. ksqlDB thì "effectively maintenance-mode" [15]. KafkaSink của Flink đạt exactly-once bằng two-phase commit gắn với checkpoint [120]. Đổi lại, độ trễ cỡ chu kỳ commit, khoảng 1 phút trên Confluent Cloud [37]. Spark 4.1 có Real-Time Mode với độ trễ vài mili-giây cho workload stateless [121]. RisingWave (vendor) định vị là database streaming tương thích PostgreSQL, duy trì materialized view tăng dần và phục vụ truy vấn trực tiếp [122].

Bảng tiêu chí rời Go tự viết được đặt ở mục 11, cùng với bản đồ quyết định. Các nguồn chỉ đưa tiêu chí định tính, không ai đưa ngưỡng kiểu "state trên X GB thì dùng Flink" [15]. **Nhận định:** mô hình lai thường hợp lý: consumer Go lo ingest, decode, enrich stateless và sink idempotent; phần analytics stateful (window, join) giao cho Flink hoặc streaming SQL; cả hai cùng đọc Kafka. Netflix đi theo hướng nền tảng: Keystone chạy mỗi job trên một cluster Flink riêng để cô lập, checkpoint lên S3, và Data Mesh dùng Kafka làm tầng vận chuyển giữa các processor Flink nối tiếp nhau [25][26].

## 11. Bản đồ quyết định: từ đặc điểm bài toán tới kỹ thuật và kiến trúc

**Nhận định:** các bảng trong mục này là tổng hợp của người viết từ những phát hiện có nguồn ở mục 2–10. Không có nguồn nào đưa ra nguyên bảng. Cột "case" chỉ nơi kỹ thuật đã được dùng thật. Tiêu chí chi tiết để rời Go tự viết sang Flink, Kafka Streams hay streaming SQL nằm ở mục con thứ ba.

### Đặc điểm bài toán → kỹ thuật nên chọn

| Đặc điểm bài toán | Kỹ thuật / kiến trúc nên chọn | Case | Đánh đổi chính |
|---|---|---|---|
| Stateless, CPU-bound nhanh, cần thứ tự theo partition | Một goroutine/partition, xử lý theo slice, commit sau batch; scale bằng partition + pod | Grab | Song song bị trần bởi số partition |
| Stateless, mỗi message gọi I/O chậm, không cần thứ tự | Song song trong partition + offset tracker + trần in-flight; hoặc share group nếu Kafka ≥ 4.2 | Cloudflare (10x), Uber tracker | Crash thì replay nhiều hơn; sink phải idempotent |
| Cần thứ tự theo entity (user, order, session) | Key = entity ở producer; hash key → worker cố định; retry tại chỗ có backoff + jitter, không dùng retry topic | InfoQ session pipeline | Một key lỗi lâu chặn key đó; hot key thành nút cổ chai |
| Cần thứ tự tuyệt đối (CDC, sổ cái) | Stop-on-error, retry chặn vô hạn + alert | Confluent pattern 1 | Mất liveness khi có poison message |
| Không cần thứ tự, lỗi tạm thời phổ biến | Retry topic theo tầng delay + DLQ + redrive; delay bằng pause partition | Uber 2018, uForwarder | Nhiều topic, mất thứ tự |
| Thời gian xử lý rất không đều (ms đến giờ) | Fast lane/slow lane (group riêng); phát hiện HOL → slow lane hoặc DLQ | Cloudflare, uForwarder | Thêm topic và logic định tuyến |
| Sink ngoài Kafka cần kết quả "exactly-once" | At-least-once + upsert/idempotency key; hoặc lưu offset trong transaction DB và seek khi được giao | OpenMeter, Segment | Ca biên cần đối soát; chi phí store dedupe |
| Kafka → Kafka (enrich, filter, route) không được trùng | Transactions (`GroupTransactSession`), downstream `read_committed` | — | Độ trễ bằng chu kỳ transaction; vài % throughput |
| Gọi API bên thứ ba | At-least-once + idempotency key `topic/partition/offset`; circuit breaker khi API sập | — | API không hỗ trợ key thì trùng không tránh được |
| Dedupe hoặc aggregate theo key, cửa sổ dài | State cục bộ Pebble/RocksDB theo partition + changelog + StatefulSet/PVC | Segment | Restore lâu nếu mất đĩa |
| Window event-time, join, session, state lớn | Flink / Kafka Streams / streaming SQL | Netflix | Thêm hệ thống, JVM |
| Latency rất thấp (<100 ms), chấp nhận trùng | At-least-once, `fetch.min.bytes` nhỏ, `FetchMaxWait` ngắn, không transaction | Confluent Cloud Flink (at-least-once <100 ms) | Phải chịu trùng |
| Throughput rất cao (>500k msg/s) | Nhiều partition; batch lớn + nén lz4/zstd; decode ngoài vòng poll; giảm allocation; `GOMEMLIMIT` | — | Chưa có benchmark Go độc lập để kiểm chứng |
| Tải dao động mạnh theo giờ | KEDA theo lag (tốt hơn: lag theo giây), cooldown dài, cooperative/KIP-848 | trivago | Mỗi lần scale là một lần rebalance |
| Nhiều team cùng đọc, chi phí đọc lớn | SDK chung có chính kiến; quy mô cực lớn mới tính push proxy gRPC | Cloudflare, Grab, Wix, Uber | Proxy thêm hop, thêm hạ tầng |
| Pipeline di chuyển dữ liệu nhiều nguồn/đích | Redpanda Connect/Bento, hoặc connector framework tự viết; cô lập lỗi theo partition | Cloudflare, Brooklin | Kém linh hoạt cho logic phức tạp |

### Bảng quyết định thiết kế: lựa chọn mặc định và khi nào đổi

| Quyết định | Các lựa chọn | Mặc định đề xuất | Đổi khi | Đánh đổi |
|---|---|---|---|---|
| Client | franz-go, confluent-kafka-go, sarama, kafka-go | franz-go | Tổ chức đã chuẩn hoá librdkafka → confluent-kafka-go | cgo và build; KIP-848; một maintainer |
| Delivery | at-most, at-least, exactly-once | At-least-once + sink idempotent | Kafka→Kafka không được trùng → transactions | Độ trễ và độ phức tạp của EOS |
| Commit | Autocommit, mark + autocommit, tay | `AutoCommitMarks` + `MarkCommitRecords`, commit đồng bộ khi revoke và shutdown | Lưu offset ngoài Kafka → `DisableAutoCommit` | Commit thưa thì replay nhiều hơn |
| Mô hình song song | Partition, key, unordered, share group | Goroutine/partition | I/O chậm → key hoặc unordered + tracker | Thứ tự giảm, rủi ro HOL |
| Backpressure | Channel có giới hạn, pause partition, trần bộ nhớ fetch | Cả ba: channel + pause theo ngưỡng + `MaxConcurrentFetches`/`FetchMaxBytes` | — | Độ phức tạp của engine |
| Rebalance | Eager, cooperative-sticky, KIP-848 | Cooperative-sticky | Broker ≥ 4.3 → KIP-848 | Bản client và broker |
| Membership | Dynamic, static | Static (`InstanceID` = tên pod) | Scale động liên tục → cân nhắc dynamic | Partition đứng yên tới session timeout khi pod chết thật |
| Số partition | — | Tính theo mức scale tối đa từ đầu | — | Tăng về sau phá thứ tự theo key |
| Autoscale | HPA CPU, KEDA lag, cố định + VPA | KEDA theo lag hoặc số pod cố định bằng số partition | Tải ổn định → cố định | Rebalance khi scale |
| Retry | Tại chỗ, retry topic, stop-on-error | Tại chỗ vài lần, rồi theo yêu cầu thứ tự | — | Thứ tự hay liveness |
| State store | Không, cục bộ (Pebble), ngoài (Redis) | Pebble + changelog nếu có state | Chia sẻ state giữa service → Redis/Scylla | Restore và độ trễ mạng |
| Thời gian | Processing-time, event-time | Event-time + stream-time + grace | Chỉ đo thông lượng hệ thống → processing-time | Phải xử lý late data |
| Định dạng | Avro, Protobuf, JSON Schema | Protobuf cho team Go | Hệ JVM/Flink → Avro | Codegen và tương thích |
| Lag metric | Offset, thời gian | Cả hai, đo bên ngoài, alert theo xu hướng | — | Thêm exporter |
| Liveness | Kết nối, tiến độ | Tiến độ (poll gần nhất, commit tiến) | — | Phải dọn state khi revoke để tránh báo sai |

### Khi nào rời Go tự viết sang framework

Tín hiệu nào trong bảng dưới xuất hiện thì nên cân nhắc rời Go tự viết. Bảng xếp theo mức độ quan trọng.

| Tín hiệu từ bài toán | Hướng chọn | Lý do |
|---|---|---|
| Chỉ stateless, hoặc state theo key không window | Giữ Go (franz-go + Pebble/Redis, hoặc goka) | Rẻ nhất về vận hành: một Deployment bình thường |
| Cần window event-time, watermark, late data, session window, join stream-stream | Kafka Streams (đội chấp nhận JVM, chỉ Kafka→Kafka) hoặc Flink | Tự viết là dựng lại một phần Kafka Streams |
| Cần EOS có state Kafka→Kafka | Kafka Streams/Flink; franz-go làm được nhưng phải tự gắn state vào transaction | Kafka Streams vẫn xoá state khi crash ở EOS, tự làm còn khó hơn |
| State lớn (hàng trăm GB), cần checkpoint incremental, savepoint để nâng cấp logic | Flink (2.x có disaggregated state) | Không có công cụ tương đương trong Go |
| Nhiều nguồn/đích (DB, object storage, CDC) | Flink; Redpanda Connect nếu stateless | Connector có sẵn |
| Logic diễn đạt được bằng SQL, cần truy vấn kết quả trực tiếp | Flink SQL hoặc streaming database | Đội analyst tự viết được |
| Đã có hạ tầng Spark/Databricks | Spark Structured Streaming | Tận dụng hạ tầng |

### Mười anti-pattern đã xảy ra thật

| Anti-pattern | Hậu quả | Case |
|---|---|---|
| Liveness check chỉ kiểm tra kết nối broker | Bỏ sót consumer kẹt | Cloudflare [21] |
| Giữ state theo partition mà không dọn khi revoke | Báo unhealthy sai, restart dây chuyền | Cloudflare [21] |
| Commit offset "mới nhất đã xong" khi xử lý song song | Mất dữ liệu khi crash | InfoQ [6] |
| Worker pool phẳng cho bài toán cần thứ tự | Một session retry chặn session khác | InfoQ [6] |
| Autoscale consumer bằng HPA theo CPU | Tải lệch, lãng phí | Grab [12] |
| Không lên kế hoạch partition trước khi launch | Không scale được khi sự cố | Cloudflare [20] |
| Dừng cả fetcher để chờ delay retry | Retry topic chỉ dùng được 1 partition | Uber [4] |
| Batch sink không validate trước | Một event hỏng làm fail cả batch | OpenMeter [10] |
| Abstraction giấu cấu hình quan trọng | Partition skew | Cloudflare [20] |
| Dựng push proxy khi chưa đủ quy mô | Thêm phức tạp, độ trễ, rủi ro | Kai Waehner [28] |

## Các nguồn bất đồng ở đâu

**Hỗ trợ KIP-848 ở client Go.** Kafma viết rằng franz-go chưa có KIP-848, còn README và source franz-go nói đã hỗ trợ qua `ServerSideBalancer` từ v1.22.0 [109][46][48]. Nên tin source, vì đó là nguồn gốc và mới hơn. Một điểm lệch tinh tế hơn: Kafka GA KIP-848 từ 4.0 và confluent-kafka-go gọi nó "production-ready" từ v2.12.0, nhưng franz-go khuyên chỉ dùng trên broker từ 4.3, vì lỗi `STALE_MEMBER_EPOCH` khi commit mà client không tự xử lý được [123][53][7]. Hai lời khuyên không mâu thuẫn về sự thật mà khác về client. Với franz-go, nên theo khuyến nghị của chính franz-go.

**Default của `log.message.timestamp.after.max.ms`.** Notes ghi nhận hai con số: 3.600.000 ms (1 giờ) theo KIP-32, và 86.400.000 ms (1 ngày) theo tài liệu AWS MSK [84][124]. Topic config `message.timestamp.after.max.ms` chỉ áp dụng với CreateTime [125]. Độ lệch có thể do khác phiên bản Kafka hoặc do MSK đặt mặc định riêng. Chưa xác định được bên nào đúng cho bản đang dùng, nên phải kiểm tra trên chính cluster. Giá trị này quan trọng khi tính lag theo thời gian từ timestamp của record.

**Kích hoạt KIP-890.** Docs Kafka 4.0 vừa nói KIP-890 "automatically enabled on the server since Apache Kafka 4.0", vừa nói cluster nâng cấp phải đặt `transaction.version=2` [35]. Cách hiểu hợp lý nhất: cluster mới bật sẵn, còn cluster nâng cấp chỉ bật khi finalize feature. Vẫn nên kiểm tra rõ trên cluster.

**"Sliding window".** Kafka Streams dùng "sliding" cho window căn theo record, còn Akidau và Flink dùng "sliding" cho loại mà Kafka Streams gọi là hopping [58][61][59]. Không ai sai; chỉ cần ghi rõ đang dùng thuật ngữ của hệ nào.

**Proxy hay thư viện.** Uber và Wix cho thấy push proxy giải được giới hạn song song theo partition và giảm chi phí đọc [4][27]. Kai Waehner cho rằng ở quy mô nhỏ đến vừa, proxy là phức tạp thừa [28]. Hai bên khớp nhau khi xét quy mô: Uber có hơn 1.000 service, Wix hơn 4.000. Với brief này, lập luận của Waehner áp dụng. Riêng con số 30% của Wix, phần bài đọc được trình bày như mức tiết kiệm kỳ vọng; mức đạt thực tế chỉ thấy qua tiêu đề bài [27].

**Benchmark client Go.** Một benchmark năm 2022 cho rằng kafka-go nhanh nhất tổng thể, nhưng nó không gồm franz-go và chỉ đo ghi bất đồng bộ [126]. Các tuyên bố kiểu "nhanh hơn N lần" từng có trong README franz-go đã bị gỡ khỏi bản hiện tại [46]. Không nên tin số nào trong số này để chọn client; các tiêu chí tính năng và bảo trì đáng tin hơn.

**Tên config DLQ của Kafka Streams.** KIP-1034 và upgrade guide 4.2 dùng hai tên khác nhau (`errors.dead.letter.queue.topic.name` và `errors.deadletterqueue.topic.name`) [42][43]. Upgrade guide gắn với bản phát hành nên đáng tin hơn, nhưng cần kiểm tra lại nếu dùng Kafka Streams.

## Kết luận và hàm ý

Điều rút ra quan trọng nhất là phần "engine" của một consumer Kafka chủ yếu *không* nằm ở logic nghiệp vụ, mà ở việc quản lý khoảng cách giữa tiến độ xử lý và tiến độ commit trong mọi tình huống: song song, lỗi, rebalance, shutdown, replay. Gần như mọi case thực tế đều hội tụ về ba cơ chế: offset tracker commit theo mốc liên tục, pause/resume theo partition, và phân loại lỗi tạm thời với poison message. Cùng với đó là một quy ước ngầm: "exactly-once" với sink ngoài thực chất là at-least-once cộng idempotency. Vì vậy thứ nên viết đầu tiên là runtime dùng chung (tracker, router lỗi, metric, health check theo tiến độ, shutdown), chứ không phải pipeline đầu tiên. Pipeline nào ra đời sau cũng sẽ dùng lại runtime này, giống cách Cloudflare và Grab đóng gói thành SDK.

Với mục đích của brief, khi gặp một bài toán cụ thể, nên trả lời theo thứ tự ba câu hỏi ở mục 11. Thứ nhất, sink là gì: nó quyết định mức delivery và kỹ thuật idempotency. Thứ hai, cần thứ tự theo gì: nó quyết định mô hình song song và đường retry. Thứ ba, có cần state theo thời gian hay không: nó quyết định ở lại Go hay chuyển sang framework. Ranh giới tự viết khá rõ: stateless và state theo key là vùng an toàn của Go với franz-go cộng Pebble. Window event-time, join và EOS có state là nơi chi phí tự viết tăng vọt, và Flink hoặc Kafka Streams đã giải sẵn. Con số hiệu năng cho Go ở mức trên 500k msg/s vẫn là điểm mù; cách duy nhất để có số là tự benchmark bằng `examples/bench` của franz-go trên workload thật trước khi chốt kiến trúc [46].

## Chưa kiểm chứng được

- **Không có benchmark độc lập, có công bố phương pháp, cho client Go ở mức trên 500k msg/s.** Các con số tìm được đều là lead chưa mở hoặc đã cũ: gist cũ so sánh confluent-kafka-go và Sarama, issue Sarama #2540 về producer, bài Medium "5.7 Billion Event Backlog" (trả 403), câu "10x-20x faster" trên một bản fork franz-go. Bindplane nói chuyển sang franz-go tăng throughput 35%, nhưng mới thấy qua snippet. Truy vấn đã thử: "franz-go benchmark throughput consumer msg/s", "franz-go vs confluent-kafka-go vs sarama consume benchmark MB/s", "Go Kafka consumer GC pressure allocations high throughput million messages per second", "engineering blog Go Kafka consumer millions events per second franz-go migration", "franz-go sarama kafka-go benchmark throughput comparison".
- **Một số tên API franz-go trong các đoạn mã chưa đối chiếu với source:** `CommitMarkedOffsets`, `CommitUncommittedOffsets`, `kgo.TransactionalID`, `kgo.TryCommit`, `kgo.NewOffset().AfterMilli`, `kadm` `ListOffsetsAfterMilli`, và trường `Records` của `FetchTopicPartition`. Các tên đã thấy trong source hoặc docs gồm `AutoCommitMarks`, `MarkCommitRecords`, `CommitRecords`, `BlockRebalanceOnPoll`, `PauseFetchPartitions`/`ResumeFetchPartitions`, `InstanceID`, `ServerSideBalancer`, `ShareGroup`, `GroupTransactSession`. Mọi đoạn mã trong báo cáo đều là minh hoạ chưa biên dịch và chưa chạy. Tên API transaction của confluent-kafka-go (`InitTransactions`, `SendOffsetsToTransaction`) cũng chưa đọc trên pkg.go.dev.
- **Trạng thái phát hành KIP-939 (2PC với hệ thống ngoài).** Release plan 4.1.0 liệt kê KIP này ở trạng thái "Accepted", nhưng thông báo phát hành 4.1.0 không nhắc tới. Một nguồn bậc 3 ghi "full implementation unconfirmed" [127][128][129]. Truy vấn đã thử: "KIP-939 two-phase commit Kafka transactions external database", "Apache Kafka 4.1 release KIP-939 2PC preview".
- **goka không có window và EOS:** đây là suy luận từ việc README, overview và wiki không nhắc tới, cộng với việc goka tự ghi at-least-once. Chưa có tuyên bố tường minh từ docs [14]. Cũng chưa đọc đoạn gốc về `WaitForReady` và việc chặn xử lý trong lúc recovery.
- **Default mâu thuẫn của `log.message.timestamp.after.max.ms`:** 3.600.000 ms (KIP-32) và 86.400.000 ms (AWS MSK). Chưa tìm được trang config của bản Kafka 4.x để chốt. Truy vấn đã thử: "kafka topic config message.timestamp.type CreateTime LogAppendTime message.timestamp.after.max.ms".
- Chưa có thư viện Go trưởng thành nào được kiểm chứng là làm offset tracker kiểu Parallel Consumer, ngoài input Kafka của Redpanda Connect (vốn là ứng dụng, không phải thư viện). Truy vấn đã thử: "Confluent Parallel Consumer ordering key partition unordered".
- Không có benchmark công khai về thời gian rebalance của eager, cooperative và KIP-848 ở group lớn, cũng như về tác động rebalance khi KEDA scale. Truy vấn đã thử: "KIP-848 next generation consumer rebalance protocol Kafka 4.0 GA", "KEDA Kafka autoscaling rebalance storm pitfalls consumer lag".
- Chưa xác nhận bản sửa KAFKA-14915 (đọc tiered storage nhiều partition) đã có trong Kafka 4.2.0 hay chưa; nguồn mới chỉ nói "planned".
- Chưa kiểm chứng `kotel` phát semconv phiên bản nào; `franz-go/pkg/sr` đã hỗ trợ header schema GUID của CP 8.1.1 hay chưa; confluent-kafka-go đã hỗ trợ share consumer (KIP-932) hay chưa.
- Nội dung bài của Grab về GOMAXPROCS trên Kubernetes chỉ thấy qua snippet tìm kiếm nên không đưa vào báo cáo.
- Không có ngưỡng định lượng đáng tin để quyết định chuyển sang Flink (state bao nhiêu GB, bao nhiêu join); các nguồn chỉ đưa tiêu chí định tính, nhiều nguồn có lợi ích thương mại. Các phát hiện về Spark 4.1 RTM và RisingWave chỉ đọc qua snippet.
- Không có số liệu về mức out-of-orderness điển hình để chọn grace period, và không có benchmark độc lập giữa Pebble, RocksDB và Badger cho workload stream processing.

## Nguồn

[1] Kafka Message Delivery Guarantees — Confluent Documentation, không rõ ngày (bậc 1). https://docs.confluent.io/kafka/design/delivery-semantics.html
[2] Exactly-Once Semantics Are Possible: Here's How Kafka Does It — Neha Narkhede / Confluent, 2017-06-30, cập nhật 2025-03 (bậc 1). https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/
[3] KafkaConsumer Javadoc 3.9 — Apache Kafka, bản 3.9, không rõ ngày (bậc 1). https://kafka.apache.org/39/javadoc/org/apache/kafka/clients/consumer/KafkaConsumer.html
[4] Introducing uForwarder: The Consumer Proxy for Kafka Async Queuing — Uber Engineering, 2026-02-05 (bậc 1). https://www.uber.com/en-NG/blog/introducing-ufowarder
[5] confluentinc/parallel-consumer README — Confluent, đọc 2026-11 (bậc 1). https://github.com/confluentinc/parallel-consumer
[6] Building a Session-Ordered Kafka Pipeline in Go — InfoQ, 2026-10-07 (bậc 2). https://www.infoq.com/articles/apache-kafka-golang-session-ordered-pipeline
[7] franz-go pkg/kgo/config.go — twmb, nhánh master (v1.22.3), đọc 2026-11-13 (bậc 1). https://github.com/twmb/franz-go/blob/master/pkg/kgo/config.go
[8] Consumer Rebalance Protocol (Kafka 4.2 docs) — Apache Kafka, 2026 (bậc 1). https://kafka.apache.org/42/operations/consumer-rebalance-protocol/
[9] Delivering billions of messages exactly once — Segment / Twilio, 2017-06-29 (bậc 1). https://www.twilio.com/en-us/blog/insights/exactly-once-delivery/
[10] Building a Consistent Kafka Consumer — OpenMeter, 2023-10-18 (bậc 1). https://openmeter.io/blog/consistent-kafka-consumer
[11] Apache Kafka scaler (KEDA docs v2.18) — KEDA, không rõ ngày (bậc 1). https://keda.sh/docs/2.18/scalers/apache-kafka/
[12] Optimally scaling Kafka consumer applications — Grab Engineering, 2020-10-13 (bậc 1). https://engineering.grab.com/optimally-scaling-kafka-consumer-applications
[13] From Always-On to On-Demand: Scaling Kafka Sinks with KEDA — trivago tech blog, 2026-02-18 (bậc 2). https://tech.trivago.com/post/2026-02-18-from-always-on-to-on-demand-scaling-kafka-sinks-with-keda
[14] lovoo/goka README — lovoo, đọc 2026-11-13 (bậc 1). https://github.com/lovoo/goka
[15] Kafka Streams vs Flink vs ksqlDB: Honest Guide — Stéphane Derosiaux / Conduktor, cập nhật 2026-10-20 (bậc 2). https://www.conduktor.io/kafka-streams/vs-flink
[16] Introducing the Confluent Parallel Consumer — Antony Stubbs / Confluent, 2020-12-15 (bậc 1, vendor). https://www.confluent.io/blog/introducing-confluent-parallel-message-processing-client/
[17] franz-go pkg/kgo/consumer_group.go — twmb, nhánh master (v1.22.3), đọc 2026-11-13 (bậc 1). https://github.com/twmb/franz-go/blob/master/pkg/kgo/consumer_group.go
[18] Optimize Confluent Cloud Clients for Throughput — Confluent Documentation, không rõ ngày (bậc 1, vendor). https://docs.confluent.io/cloud/current/client-apps/optimizing/throughput.html
[19] KIP-429: Kafka Consumer Incremental Rebalance Protocol — Apache Kafka wiki, accepted 2.4.0 (bậc 1). https://cwiki.apache.org/confluence/display/KAFKA/KIP-429%3A+Kafka+Consumer+Incremental+Rebalance+Protocol
[20] Using Apache Kafka to process 1 trillion inter-service messages — Cloudflare blog, 2022-07-19 (bậc 1). https://blog.cloudflare.com/using-apache-kafka-to-process-1-trillion-messages/
[21] Intelligent, automatic restarts for unhealthy Kafka consumers — Cloudflare blog, 2023-01-24 (bậc 1). https://blog.cloudflare.com/intelligent-automatic-restarts-for-unhealthy-kafka-consumers/
[22] Building Reliable Reprocessing and Dead Letter Queues with Apache Kafka — Ning Xia / Uber Engineering, 2018-02-16 (bậc 1). https://www.uber.com/blog/reliable-reprocessing/
[23] Scaling Security Insights: how we achieved a 10x increase in global scanning capacity — Cloudflare blog, 2026-06-12 (bậc 1). https://blog.cloudflare.com/scaling-security-scans
[24] Open sourcing Brooklin: Near real-time data streaming at scale — LinkedIn Engineering, 2019-07-16 (bậc 1). https://www.linkedin.com/blog/engineering/open-source/brooklin-open-source
[25] Netflix Keystone Real-Time Stream Processing Platform — InfoQ, 2018-09-30 (bậc 2, tóm tắt blog Netflix). https://www.infoq.com/news/2018/09/Netflix-Keystone-Real-Time-Proc
[26] Netflix Data Mesh — InfoQ, 2022-08 (bậc 2). https://www.infoq.com/news/2022/08/netflix-data-mesh/
[27] From Bottleneck to Breakthrough: How Wix Cut Kafka Costs by 30% with a Push-Based Consumer Proxy — Wix Engineering, 2025-02-26 (bậc 1). https://wix.engineering/post/from-bottleneck-to-breakthrough-how-wix-cut-kafka-costs-by-30-with-a-push-based-consumer-proxy
[28] Scaling Kafka Consumers: Proxy vs. Client Library for High-Throughput Architectures — Kai Waehner, 2025-09-30 (bậc 2). https://www.kai-waehner.de/?p=8276
[29] KIP-98: Exactly Once Delivery and Transactional Messaging — Apache Kafka wiki, adopted 0.11.0 (bậc 1). https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging
[30] On Idempotency Keys — Gunnar Morling, 2025-11-25 (bậc 2). https://www.morling.dev/blog/on-idempotency-keys/
[31] KIP-679: Producer will enable the strongest delivery guarantee by default — Apache Kafka wiki, Kafka 3.0 (bậc 1). https://cwiki.apache.org/confluence/spaces/KAFKA/pages/165221843/KIP-679+Producer+will+enable+the+strongest+delivery+guarantee+by+default
[32] librdkafka CONFIGURATION.md — Confluent, nhánh master, đọc 2026-11 (bậc 1). https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md
[33] KIP-447: Producer scalability for exactly once semantics — Apache Kafka wiki, adopted 2.6.0 (bậc 1). https://cwiki.apache.org/confluence/display/KAFKA/KIP-447%3A+Producer+scalability+for+exactly+once+semantics
[34] KIP-890: Transactions Server-Side Defense — Apache Kafka wiki, cập nhật 2025-02-13 (bậc 1). https://cwiki.apache.org/confluence/display/KAFKA/KIP-890%3A+Transactions+Server-Side+Defense
[35] Transaction Protocol (Kafka 4.0 docs) — Apache Kafka, 2025 (bậc 1). https://kafka.apache.org/40/operations/transaction-protocol/
[36] KIP-939: Support Participation in 2PC — Apache Kafka wiki, không rõ ngày (bậc 1, đọc qua tóm tắt tìm kiếm). https://cwiki.apache.org/confluence/display/KAFKA/KIP-939:+Support+Participation+in+2PC
[37] Delivery Guarantees and Latency in Confluent Cloud for Apache Flink — Confluent Documentation, đọc 2026-11-13 (bậc 1). https://docs.confluent.io/cloud/current/flink/concepts/delivery-guarantees.html
[38] franz-go pkg/kgo/txn.go — twmb, nhánh master, đọc 2026-11-13 (bậc 1). https://github.com/twmb/franz-go/blob/master/pkg/kgo/txn.go
[39] franz-go docs/transactions.md — twmb, không rõ ngày, đọc 2026-11-13 (bậc 1). https://github.com/twmb/franz-go/blob/master/docs/transactions.md
[40] Transactional Outbox Pattern: Database to Kafka — Conduktor, không rõ ngày (bậc 2–3, mô tả pattern). https://conduktor.io/blog/transactional-outbox-pattern-database-kafka
[41] Error Handling Patterns for Apache Kafka Applications — Gerardo Villeda / Confluent, 2021-05-21 (bậc 2). https://www.confluent.io/blog/error-handling-patterns-in-kafka/
[42] KIP-1034: Dead letter queue in Kafka Streams — Apache Kafka wiki, không rõ ngày (bậc 1, qua tìm kiếm). https://cwiki.apache.org/confluence/display/KAFKA/KIP-1034%3A+Dead+letter+queue+in+Kafka+Streams
[43] Kafka Streams Upgrade Guide (Kafka 4.2) — Apache Kafka, 2026 (bậc 1, qua tìm kiếm). https://kafka.apache.org/42/streams/upgrade-guide/
[44] Watermill docs: Middlewares — ThreeDotsLabs, đọc 2026-11-13 (bậc 1). https://watermill.io/docs/middlewares/
[45] Outbox Event Router — Debezium Documentation (stable), đọc 2026-11 (bậc 1). https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html
[46] franz-go README — twmb, đọc 2026-11-13 (bậc 1). https://github.com/twmb/franz-go
[47] Apache Kafka 4.2.0 Release Announcement — Apache Kafka, 2026-02-17 (bậc 1). https://kafka.apache.org/blog/2026/02/17/apache-kafka-4.2.0-release-announcement/
[48] franz-go CHANGELOG.md — twmb, đọc 2026-11-13 (bậc 1). https://raw.githubusercontent.com/twmb/franz-go/master/CHANGELOG.md
[49] franz-go pkg/kgo/consumer.go — twmb, nhánh master, đọc 2026-11-13 (bậc 1). https://github.com/twmb/franz-go/blob/master/pkg/kgo/consumer.go
[50] Consumer Configs (Kafka 4.2 docs) — Apache Kafka, 2026 (bậc 1). https://kafka.apache.org/42/configuration/consumer-configs/
[51] Introducing KIP-848: The Next Generation of the Consumer Rebalance Protocol — Confluent blog, 2025-06-03 (bậc 1, vendor). https://www.confluent.io/blog/kip-848-consumer-rebalance-protocol/
[52] KIP-345: Introduce static membership protocol to reduce consumer rebalances — Apache Kafka wiki, Kafka 2.3 (bậc 1). https://cwiki.apache.org/confluence/display/KAFKA/KIP-345%3A+Introduce+static+membership+protocol+to+reduce+consumer+rebalances
[53] confluent-kafka-go CHANGELOG — Confluent, đọc 2026-11-13 (bậc 1). https://github.com/confluentinc/confluent-kafka-go/blob/master/CHANGELOG.md
[54] IBM/sarama PR #3748: ConsumerGroupDescribe — GitHub, 2026 (bậc 1). https://github.com/IBM/sarama/pull/3748
[55] IBM/sarama issue #3818: KIP-848 consumer group membership — GitHub, 2026-09-30 (bậc 1). https://github.com/IBM/sarama/issues/3818
[56] A Guide to the Go Garbage Collector — The Go Authors, không rõ ngày (bậc 1). https://tip.golang.org/doc/gc-guide
[57] Kafka Streams Core Concepts 4.3 — Apache Kafka, 2026 (bậc 1). https://kafka.apache.org/43/streams/core-concepts/
[58] Streams DSL (Kafka Streams 4.3 developer guide) — Apache Kafka, 2026 (bậc 1). https://kafka.apache.org/43/streams/developer-guide/dsl-api/
[59] Windows (Flink 2.3 docs) — Apache Flink, 2026 (bậc 1). https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/
[60] Streaming 102: The world beyond batch — Tyler Akidau / O'Reilly, 2016-01-20 (bậc 2). https://www.oreilly.com/radar/the-world-beyond-batch-streaming-102/
[61] Streaming 101: The world beyond batch — Tyler Akidau / O'Reilly, 2015-08-05 (bậc 2). https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/
[62] goka wiki: Tips — lovoo, không rõ ngày (bậc 1). https://github.com/lovoo/goka/wiki/Tips
[63] TimeWindows Javadoc 3.5.2 — Apache Kafka, không rõ ngày (bậc 1). https://kafka.apache.org/35/javadoc/org/apache/kafka/streams/kstream/TimeWindows.html
[64] Timely Stream Processing (Flink 2.3 docs) — Apache Flink, 2026 (bậc 1). https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time/
[65] Generating Watermarks (Flink 2.3 docs) — Apache Flink, 2026 (bậc 1). https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/event-time/generating_watermarks/
[66] Kafka Streams Architecture 4.3 — Apache Kafka, 2026 (bậc 1). https://kafka.apache.org/43/streams/architecture/
[67] KIP-441: Smooth Scaling Out for Kafka Streams — Apache Kafka wiki, không rõ ngày (bậc 1). https://cwiki.apache.org/confluence/display/KAFKA/KIP-441%3A+Smooth+Scaling+Out+for+Kafka+Streams
[68] Kafka Streams Upgrade Guide 4.3 — Apache Kafka, 2026 (bậc 1). https://kafka.apache.org/43/streams/upgrade-guide/
[69] KIP-892: Transactional Semantics for StateStores — Apache Kafka wiki, không rõ ngày (bậc 1). https://cwiki.apache.org/confluence/display/KAFKA/KIP-892:+Transactional+Semantics+for+StateStores
[70] Stream Processing Hard Problems Part II: Data Access — LinkedIn Engineering, 2016-08-22 (bậc 1). https://www.linkedin.com/blog/engineering/archive/stream-processing-hard-problems-part-ii-data-access
[71] Stateful Stream Processing (Flink 2.3 docs) — Apache Flink, 2026 (bậc 1). https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/stateful-stream-processing/
[72] Disaggregated State Management in Apache Flink 2.0 — PVLDB vol. 18, 2025 (bậc 1). https://www.vldb.org/pvldb/vol18/p4846-mei.pdf
[73] cockroachdb/pebble — Cockroach Labs, đọc 2026 (bậc 1). https://github.com/cockroachdb/pebble
[74] dgraph-io/badger — Dgraph, đọc 2026 (bậc 1). https://github.com/dgraph-io/badger
[75] Package streams (aws/go-kafka-event-source) v1.0.6 — pkg.go.dev, 2022-11-02 (bậc 1). https://pkg.go.dev/github.com/aws/go-kafka-event-source/streams
[76] Package kprom — franz-go plugin, pkg.go.dev, không rõ ngày (bậc 1). https://pkg.go.dev/github.com/twmb/franz-go/plugin/kprom
[77] franz-go pkg/kadm/groups.go — twmb, nhánh master, đọc 2026-11-13 (bậc 1). https://github.com/twmb/franz-go/blob/master/pkg/kadm/groups.go
[78] Consumer Metrics — Confluent Platform Documentation, không rõ ngày (bậc 1). https://docs.confluent.io/platform/current/kafka/consumer-metrics.html
[79] KIP-517: Add consumer metrics to observe user poll behavior — Apache Kafka wiki, Kafka 2.4 (bậc 1). https://cwiki.apache.org/confluence/display/KAFKA/KIP-517:+Add+consumer+metrics+to+observe+user+poll+behavior
[80] Burrow wiki: Consumer Lag Evaluation Rules — LinkedIn, không rõ ngày (bậc 1). https://github.com/linkedin/Burrow/wiki/Consumer-Lag-Evaluation-Rules
[81] seglo/kafka-lag-exporter — GitHub, archive 2024-03-17 (bậc 1). https://github.com/seglo/kafka-lag-exporter
[82] The Hidden Problem with Kafka Lag Monitoring — SoftwareMill, 2026-01-30 (bậc 2, bên làm công cụ cạnh tranh). https://softwaremill.com/the-hidden-problem-with-kafka-lag-monitoring/
[83] redpanda-data/kminion — Redpanda, không rõ ngày (bậc 1). https://github.com/redpanda-data/kminion
[84] KIP-32: Add timestamps to Kafka message — Apache Kafka wiki, không rõ ngày (bậc 1). https://cwiki.apache.org/confluence/display/KAFKA/KIP-32+-+Add+timestamps+to+Kafka+message
[85] Semantic conventions for messaging spans — OpenTelemetry, trạng thái Development, không rõ ngày (bậc 1). https://opentelemetry.io/docs/specs/semconv/messaging/messaging-spans/
[86] Semantic conventions for Kafka — OpenTelemetry, trạng thái Development, không rõ ngày (bậc 1). https://opentelemetry.io/docs/specs/semconv/messaging/kafka/
[87] Package kotel — franz-go plugin, pkg.go.dev, không rõ ngày (bậc 1). https://pkg.go.dev/github.com/twmb/franz-go/plugin/kotel
[88] Package kslog — franz-go plugin, pkg.go.dev, không rõ ngày (bậc 1). https://pkg.go.dev/github.com/twmb/franz-go/plugin/kslog
[89] Pod Lifecycle: Termination of Pods — Kubernetes Documentation, đọc 2026-11 (bậc 1). https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination
[90] franz-go pkg/kgo/client.go — twmb, nhánh master, đọc 2026-11-13 (bậc 1). https://github.com/twmb/franz-go/blob/master/pkg/kgo/client.go
[91] Kafka Consumer Group Management CLI Tutorial — Conduktor, không rõ ngày (bậc 2). https://www.conduktor.io/kafka/kafka-consumer-group-management-cli-tutorial
[92] Tiered Storage (Kafka 4.2 docs) — Apache Kafka, 2026 (bậc 1). https://kafka.apache.org/42/operations/tiered-storage/
[93] The hidden pitfalls of Kafka tiered storage — Red Hat Developer, 2025-08-21 (bậc 2). https://developers.redhat.com/articles/2025/08/21/hidden-pitfalls-kafka-tiered-storage
[94] KIP-1254: Kafka Consumer Support for Remote Tiered Storage Fetch — Apache Kafka wiki, Under Discussion, không rõ ngày (bậc 1). https://cwiki.apache.org/confluence/display/KAFKA/KIP-1254:+Kafka+Consumer+Support+for+Remote+Tiered+Storage+Fetch
[95] Formats, Serializers, and Deserializers — Confluent Platform 8.x Documentation, 2026 (bậc 1). https://docs.confluent.io/platform/current/schema-registry/fundamentals/serdes-develop/index.html
[96] Schema Evolution and Compatibility — Confluent Platform 8.x Documentation, không rõ ngày (bậc 1). https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html
[97] Package sr (v1.8.0) — franz-go, pkg.go.dev, không rõ ngày (bậc 1). https://pkg.go.dev/github.com/twmb/franz-go/pkg/sr
[98] Package avro/v2 (hamba) — pkg.go.dev, không rõ ngày (bậc 1). https://pkg.go.dev/github.com/hamba/avro/v2
[99] confluent-kafka-go README — Confluent, đọc 2026-11-13 (bậc 1). https://github.com/confluentinc/confluent-kafka-go/blob/master/README.md
[100] Package kfake — franz-go, pkg.go.dev, pseudo-version, không rõ ngày (bậc 1). https://pkg.go.dev/github.com/twmb/franz-go/pkg/kfake
[101] Testcontainers for Go: Kafka module — Testcontainers, không rõ ngày (bậc 1). https://golang.testcontainers.org/modules/kafka/
[102] Shopify/toxiproxy — Shopify, không rõ ngày (bậc 1). https://github.com/Shopify/toxiproxy
[103] franz-go @latest (v1.22.3) — Go module proxy, 2026-11-09 (bậc 1). https://proxy.golang.org/github.com/twmb/franz-go/@latest
[104] confluent-kafka-go/v2 @latest (v2.16.1) — Go module proxy, 2026-10-27 (bậc 1). https://proxy.golang.org/github.com/confluentinc/confluent-kafka-go/v2/@latest
[105] IBM/sarama @latest (v1.61.1) — Go module proxy, 2026-09-27 (bậc 1). https://proxy.golang.org/github.com/!i!b!m/sarama/@latest
[106] IBM/sarama README — IBM, đọc 2026-11-13 (bậc 1). https://github.com/IBM/sarama/blob/main/README.md
[107] segmentio/kafka-go @latest (v0.4.51) — Go module proxy, 2026-04-23 (bậc 1). https://proxy.golang.org/github.com/segmentio/kafka-go/@latest
[108] segmentio/kafka-go README — Segment, đọc 2026-11-13 (bậc 1). https://github.com/segmentio/kafka-go/blob/main/README.md
[109] Kafka Go Clients: franz-go vs kafka-go vs Sarama — Kafma, 2026-09-26 (bậc 2–3, một nguồn). https://kafma.app/blog/kafka-golang-clients
[110] go.mod của redpanda-data/connect v4.118.0 — Go module proxy, 2026-11-13 (bậc 1). https://proxy.golang.org/github.com/redpanda-data/connect/v4/@v/v4.118.0.mod
[111] Package goka v1.1.18 — pkg.go.dev, 2026-11-11 (bậc 1). https://pkg.go.dev/github.com/lovoo/goka
[112] go.mod của goka v1.1.18 — Go module proxy, 2026-11-11 (bậc 1). https://proxy.golang.org/github.com/lovoo/goka/@v/v1.1.18.mod
[113] Redpanda Connect README — Redpanda, đọc 2026-11-13 (bậc 1). https://github.com/redpanda-data/connect/blob/main/README.md
[114] kafka_franz input — Redpanda Connect docs, đọc 2026-11-13 (bậc 1). https://docs.redpanda.com/redpanda-connect/components/inputs/kafka_franz/
[115] Announcing Bento, the open source fork of the project formerly known as Benthos — WarpStream, 2024 (bậc 1, bên liên quan). https://www.warpstream.com/blog/announcing-bento-the-open-source-fork-of-the-project-formerly-known-as-benthos
[116] Watermill README — ThreeDotsLabs, đọc 2026-11-13 (bậc 1). https://github.com/ThreeDotsLabs/watermill/blob/master/README.md
[117] go.mod của watermill-kafka v3.1.4 — Go module proxy, 2026-07-29 (bậc 1). https://proxy.golang.org/github.com/!three!dots!labs/watermill-kafka/v3/@v/v3.1.4.mod
[118] reugn/go-streams — GitHub, v0.13.0 2025-05-10 (bậc 1). https://github.com/reugn/go-streams
[119] Redpanda Acquires Benthos — Redpanda press release, 2024-05-30 (bậc 1). https://redpanda.com/press/redpanda-acquires-benthos
[120] An Overview of End-to-End Exactly-Once Processing in Apache Flink (with Apache Kafka, too!) — Apache Flink blog, 2018-02-28 (bậc 1, qua tìm kiếm). https://flink.apache.org/2018/02/28/an-overview-of-end-to-end-exactly-once-processing-in-apache-flink-with-apache-kafka-too/
[121] Spark Structured Streaming — Apache Spark, không rõ ngày (bậc 1, qua tìm kiếm). https://spark.apache.org/streaming/
[122] When to use RisingWave — RisingWave Documentation, không rõ ngày (bậc 1 nhưng là vendor, qua tìm kiếm). https://docs.risingwave.com/faq/faq-when-to-use-risingwave
[123] Apache Kafka 4.0.0 Release Announcement — Apache Kafka, 2025-03-18 (bậc 1). https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/
[124] Amazon MSK Express broker read/write configurations — AWS Documentation, không rõ ngày (bậc 1). https://docs.aws.amazon.com/es_es/msk/latest/developerguide/msk-configuration-express-read-write.html
[125] Topic-Level Configs (Kafka 3.7 docs) — Apache Kafka, không rõ ngày (bậc 1). https://kafka.apache.org/37/configuration/topic-level-configs/
[126] Go社区主流Kafka客户端简要对比 — Tony Bai, 2022-03-28 (bậc 2, qua tìm kiếm). https://tonybai.com/2022/03/28/the-comparison-of-the-go-community-leading-kakfa-clients/
[127] Release Plan 4.1.0 — Apache Kafka wiki, 2025 (bậc 1, qua tìm kiếm). https://cwiki.apache.org/confluence/display/KAFKA/Release+Plan+4.1.0
[128] Apache Kafka 4.1.0 Release Announcement — Apache Kafka, 2025-09-04 (bậc 1). https://kafka.apache.org/blog/2025/09/04/apache-kafka-4.1.0-release-announcement/
[129] KIP-939 trên Kafka Options Explorer — Conduktor, không rõ ngày (bậc 3, chỉ dùng làm manh mối). https://kafka-options-explorer.conduktor.io/kip/939/
