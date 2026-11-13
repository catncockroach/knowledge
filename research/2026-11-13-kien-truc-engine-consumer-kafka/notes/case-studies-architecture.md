# Kiến trúc tham khảo & case study engine consumer Kafka

## Câu hỏi phụ 6a: Các công ty thực tế tổ chức engine consumer ra sao (tách tầng, push vs pull, thứ tự, scale, lỗi), bài học và lỗi thường gặp

### Kết luận ngắn
Có hai họ kiến trúc lặp lại ở các công ty lớn: (1) **thư viện client "có chính kiến" (opinionated SDK) bọc client Kafka**, mỗi service tự kéo (pull) dữ liệu: Cloudflare (Go, bọc Sarama), Grab Coban (Go, plugin Trigger/Runtime/Pipeline), Wix Greyhound (Scala/Java); và (2) **consumer proxy đẩy (push) qua gRPC**, một tầng trung tâm đọc Kafka rồi đẩy từng message tới service: Uber uForwarder (>1.000 service), Wix (giảm ~30% chi phí Kafka). Bài toán stateful/analytics nặng thì các công ty dùng nền tảng stream processing có sẵn (Netflix Keystone/Data Mesh trên Flink), không tự viết. Mức chắc chắn: **cao** cho mô tả kiến trúc (phần lớn từ blog gốc của công ty, bậc 1); **trung bình** cho số liệu quy mô (nhiều con số chỉ có trong blog của chính công ty, khác năm).

### Phát hiện có nguồn

**Uber — uForwarder (consumer proxy, push qua gRPC)**
- Uber chạy Kafka ở mức "trillions of messages and multiple petabytes of data per day"; uForwarder là cách chính để service đọc Kafka cho use case pub-sub, hơn 1.000 consumer service đã onboard; đội máy tăng từ "two digits of servers" lên nhiều cluster "hundreds, eventually thousands" server — [Introducing uForwarder: The Consumer Proxy for Kafka Async Queuing](https://www.uber.com/en-NG/blog/introducing-ufowarder) (bậc 1, 2026-02-05)
- Cơ chế: proxy fetch từ Kafka, đẩy **từng message riêng lẻ** tới endpoint gRPC của consumer, gom mã trạng thái gRPC, và **chỉ commit offset khi an toàn**. Mục đích: giấu việc quản lý consumer Kafka khỏi service owner và giải quyết "impedance mismatch of Kafka partitions for message queuing use cases" (song song bị giới hạn bởi số partition) — cùng nguồn
- Thành phần: **Controller** (chạy rebalance, đặt workload lên worker) và **Worker** (các fetcher thread poll Kafka và dispatch). Placement "sticky", chỉ đổi khi vi phạm kích thước hoặc liveness check fail; sizing thích ứng theo CPU/memory/network; scale-up dùng cửa sổ thời gian ngắn, scale-down dùng cửa sổ dài để giảm lag do thiếu tài nguyên và giảm message trùng do placement churn — cùng nguồn
- **Out-of-order commit tracker**: ghi trạng thái commit từng offset theo partition, cho phép xử lý song song nhiều message trong một partition mà vẫn chỉ commit phần đã xong liên tục — cùng nguồn
- **Phát hiện head-of-line (HOL) blocking**: hai điều kiện — tracker dùng >90% (`UTILIZATION_THRESHOLD`) và tỉ lệ chưa commit <2% (`UNCOMMITTED_PERCENTAGE_THRESHOLD`), tức "a small amount of messages blocking the majority of messages". Xử lý: đánh dấu offset CANCELED → huỷ gRPC đang bay và các retry tương lai → đẩy message vào DLQ → đánh dấu COMMITTED — cùng nguồn
- Giới hạn của DLQ: không bắt được message hỏng "trên đường" trước khi tới handler, vd payload vượt giới hạn mặc định 4MB của gRPC server, instance đích chết, interceptor từ chối request — cùng nguồn
- **Delay/retry**: thiết kế cũ cho fetcher thread dừng hẳn tới khi hết delay → buộc retry topic chỉ có **1 partition**. Thiết kế mới: `DelayProcessManager` chỉ kiểm tra message chưa xử lý đầu tiên của mỗi partition, **pause riêng partition còn trong thời gian delay**, buffer message đã poll trong RAM, resume khi đủ delay → retry topic dùng nhiều partition được. Delay là tối thiểu ("at-least"), không chính xác — cùng nguồn
- **Context-aware routing**: producer gắn context (vd prod/non-prod, zone) vào Kafka header, proxy chép sang gRPC header để load balancer định tuyến; thay cho cách tạo topic con cho từng subset — cùng nguồn
- Bài học Uber nêu: đẩy rebalance sang proxy khiến consumer service trở thành **stateless**; áp lực chi phí phần cứng đưa utilization lên ưu tiên. Hướng tiếp: rewind offset về latest trong khi một "side consumer" đuổi lag — cùng nguồn
- InfoQ đưa tin việc mở mã nguồn uForwarder (Apache 2.0) — [uber uforwarder kafka push proxy](https://www.infoq.com/news/2026/02/uber-uforwarder-kafka-push-proxy) (bậc 2, 2026-02)

**Uber — retry topic & DLQ (2018)**
- Khi handler fail một số lần, consumer publish message sang **retry topic đầu tiên**, trả success và commit offset để không chặn batch; mỗi tầng retry fail thì đẩy tiếp sang tầng sau với delay dài hơn; hết chuỗi thì vào **dead letter topic**. Tác giả gọi đây là "delayed processing queues"; delay là best-effort: "handler invocation will occur at least after the configured timeout but possibly later" — [Building Reliable Reprocessing and Dead Letter Queues with Apache Kafka](https://www.uber.com/US/en/blog/reliable-reprocessing/) (bậc 1, 2018-02-16)
- DLQ cần hỗ trợ list, purge, merge (merge = publish lại vào retry topic đầu tiên). Lỗi tạm thời (mạng chập chờn) thì retry; lỗi code (null pointer) có thể đi thẳng DLQ — cùng nguồn
- Mỗi luồng downstream có consumer path + retry/DLQ riêng, để lỗi một dependency không bắt retry các dependency đã thành công — cùng nguồn
- Đánh đổi: retry topic tách message khỏi luồng chính → xử lý **mất thứ tự** so với traffic sống; at-least-once đòi consumer idempotent; nhiều loại event → nhiều topic phải quản lý — cùng nguồn

**Wix — Greyhound SDK rồi push proxy**
- Wix có hơn 4.000 microservice/serverless function; hoá đơn Confluent Cloud: ~10% ghi, ~40% đọc, 40–50% capacity (CKU). Đọc đắt gấp ~4 lần ghi → trung bình mỗi byte được đọc ~4 lần vì nhiều consumer group trên cùng topic. Giải pháp: proxy đọc mỗi topic **một lần** rồi đẩy tới client qua gRPC; vì mọi service đã dùng Greyhound nên thay đổi chủ yếu nằm trong thư viện (Greyhound expose endpoint gRPC). Tiêu đề bài: giảm 30% chi phí Kafka — [From Bottleneck to Breakthrough: How Wix Cut Kafka Costs by 30% with a Push-Based Consumer Proxy](https://wix.engineering/post/from-bottleneck-to-breakthrough-how-wix-cut-kafka-costs-by-30-with-a-push-based-consumer-proxy) (bậc 1, 2025-02-26). Lưu ý: phần đã đọc được trình bày 30% như mức tiết kiệm kỳ vọng; con số đạt thực tế chỉ xác nhận qua tiêu đề và qua Kai Waehner (bậc 2).

**Kai Waehner — proxy vs client library**
- So sánh: proxy (Uber, Wix) → ít Kafka client hơn, giảm tải broker, retry/DLQ tập trung, tránh HOL theo từng service; đổi lại phải xây và vận hành hạ tầng mới, thêm latency, khó chẩn đoán lỗi. Client library kiểu Confluent Parallel Consumer → dễ áp dụng, giảm HOL mà không cần hạ tầng mới, hợp cho việc gọi DB/HTTP chậm; đổi lại code phức tạp hơn, cần hiểu async/concurrency. Khuyến nghị: proxy chỉ cho quy mô cực lớn có platform team; với quy mô nhỏ–vừa proxy "adds unnecessary complexity, overhead, and risk"; bắt đầu bằng pull consumer native — [Scaling Kafka Consumers: Proxy vs. Client Library for High-Throughput Architectures](https://www.kai-waehner.de/?p=8276) (bậc 2, 2025-09-30)

**Cloudflare — thư viện Go bọc Sarama, connector framework, health check theo tiến độ**
- 14 cluster Kafka, ~330 node, dùng từ 2014; >1 nghìn tỉ message trong 8 năm cho giao tiếp liên service. Thư viện Go nội bộ **Messagebus-Client** bọc Shopify Sarama với cấu hình có chính kiến, tự xoay vòng chứng chỉ mTLS, expose metric mặc định (consumed/errors). Đã tới bản thứ 5 — [Using Apache Kafka to process 1 trillion inter-service messages](https://blog.cloudflare.com/using-apache-kafka-to-process-1-trillion-messages/) (bậc 1, 2022-07-19)
- Lỗi thực tế: lớp abstraction giấu chi tiết Kafka, một misconfiguration gây **partition skew** làm chậm xử lý realtime; sau đó sửa thư viện để khó cấu hình sai hơn — cùng nguồn
- **Connector framework** kiểu Kafka Connect: pipeline cấu hình bằng biến môi trường `READER`, `TRANSFORMATIONS`, `WRITER`; thêm reader/writer/transformation bằng cách implement interface và đăng ký; sinh service từ cookiecutter template (đây chính là tách tầng ingest → transform → sink) — cùng nguồn
- Schema: Protobuf (thay JSON) với registry dạng repo, Prototool phát hiện breaking change; **một proto message/topic** → nhiều topic, lãng phí compute cho topic ít traffic — cùng nguồn
- Thêm topic trong YAML tự tạo alert lag cao + dashboard Grafana — cùng nguồn
- Bài học: một partition chỉ có một consumer trong group nên khi sự cố **không thể chỉ thêm consumer để tăng tốc**; phải ước lượng throughput và số partition trước khi lên production — cùng nguồn
- **Consumer "khoẻ" nhưng đứng yên**: liveness check chỉ kiểm tra kết nối broker bỏ sót consumer bị kẹt; sau rebalance, consumer không xác nhận rebalance có thể chờ mãi một partition không còn sở hữu (deadlock, phải restart tay). Health check mới dựa trên **tiến độ**: fail nếu committed offset không đổi kể từ lần check trước trong khi còn message (committed ≠ latest). Lỗi khi rollout: replica giữ committed offset cũ của partition đã mất sau rebalance → báo unhealthy sai → restart → thêm rebalance → **lỗi dây chuyền**; sửa bằng cách xoá partition khỏi map khi bị revoke (dùng `session.Context().Done()` của Sarama) — [Intelligent, automatic restarts for unhealthy Kafka consumers](https://blog.cloudflare.com/intelligent-automatic-restarts-for-unhealthy-kafka-consumers/) (bậc 1, 2023-01-24)
- **HOL blocking & fast/slow lane**: các "checker" là microservice Go; một partition một consumer active trong group, message chậm (phút–giờ, vd account rất nhiều asset) chặn cả partition. Giải pháp: tách mỗi checker thành **slow lane** và **fast lane** (consumer group riêng); fast lane gặp message chậm thì bỏ qua sang slow lane. Thêm **song song trong partition**: consume theo batch, mỗi message một goroutine; đánh đổi: crash giữa batch thì làm lại nhiều hơn, tốn RAM hơn chút. Kết quả: từ ~10 lên >120 scan/s (mục tiêu 100), tăng >10x không thêm phần cứng. Ví dụ lag: 30 partition thì 15 partition bị lag vì load balancer chia traffic sang hai endpoint API ở Portland và Amsterdam — [Scaling Security Insights: how we achieved a 10x increase in global scanning capacity](https://blog.cloudflare.com/scaling-security-scans) (bậc 1, 2026-06-12)

**Grab — Coban (Go, plugin, Kubernetes)**
- Pipeline xử lý là các pod consumer Kafka trên Kubernetes, kiến trúc plugin Go; mỗi pod gồm **Trigger** (kết nối nguồn), **Runtime** (điều phối pod) và **Pipeline plugin** do người dùng viết (logic domain); ghi kết quả ra RDBMS hoặc topic Kafka khác. Quy mô gần 400 tỉ event/tuần — [Optimally scaling Kafka consumer applications](https://engineering.grab.com/optimally-scaling-kafka-consumer-applications) (bậc 1, 2020-10-13)
- Bài học scale: HPA theo CPU/memory gây over-provision theo đỉnh và **tải không đều giữa pod** dù partition đều; chuyển sang **số pod cố định = số partition** (lấy từ Kafka API lúc deploy) + VPA → giảm ~45% tài nguyên sử dụng so với requested. VPA phản ứng chậm với tải đột biến. Tách pipeline critical (On-Demand node) và non-critical (Spot), dùng priority class và pod "noop" dự phòng — cùng nguồn
- Search snippet (chưa mở trang gốc): Grab viết rằng không đặt GOMAXPROCS thì Go runtime tưởng dùng được toàn bộ CPU của node, hại hiệu năng trên Kubernetes; worker goroutine song song giảm lag đáng kể — [performance bottlenecks go apps](https://engineering.grab.com/performance-bottlenecks-go-apps) (bậc 1, không rõ ngày; **chưa xác minh nội dung bằng WebFetch**)

**Segment — dedupe "exactly-once" bằng Go + RocksDB**
- Worker Go đọc topic input (partition theo `messageId` để cùng ID luôn về cùng worker), tra RocksDB nhúng trên EBS (thay cụm Memcached), chỉ publish message mới ra topic output. Cửa sổ dedupe 4 tuần (giới hạn theo dung lượng, page on-call nếu co dưới 24h); ~0,6% event trùng trong 4 tuần; 200 tỉ message qua hệ thống trong ~3 tháng; ~60 tỉ key, 1,5 TB key trên đĩa; tra cứu bằng batched `MultiGet`, bloom filter giúp key mới khỏi đọc SSTable — [Delivering billions of messages exactly once](https://www.twilio.com/en-us/blog/insights/exactly-once-delivery/) (bậc 1, 2017-06-29)
- Không có bước atomic chung cho RocksDB + topic output + ack input; **topic output là nguồn sự thật/WAL**, input chỉ ack sau khi RocksDB đã persist key; khởi động lại thì đối chiếu topic output để sửa RocksDB. Disk gắn lại được sang instance mới nếu giữ nguyên partition ID — cùng nguồn

**OpenMeter — consumer Go tự viết cho billing**
- Bỏ Kafka Connect sink ClickHouse vì một event lỗi làm fail cả batch, khó quản lý plugin, thiếu metric/log. Consumer Go: poll từ offset đã commit → lọc event không hợp lệ (vào DLQ) → dedupe trong batch (RAM) → dedupe qua Redis → insert ClickHouse → ghi key vào Redis → commit offset. Fail bước nào thì xử lý lại cả batch, an toàn vì các bước idempotent; vẫn còn ca hiếm (cả Kafka commit lẫn ghi Redis cùng fail) cần đối soát tay. Key message = idempotency key nên nhất quán chỉ cần giữ trong từng partition — [Building a Consistent Kafka Consumer](https://openmeter.io/blog/consistent-kafka-consumer) (bậc 1, 2023-10-18)

**InfoQ — pipeline Go giữ thứ tự theo session**
- Kiến trúc 2 cấp: `SessionWorker` (consistent hashing theo session ID) → goroutine per-session tạo theo nhu cầu, tự huỷ khi idle, xử lý tuần tự từng message. Retry tại chỗ với exponential backoff + jitter để message sau không vượt message lỗi; poison pill → DLQ. Commit loop chỉ tiến tới **offset hoàn thành liên tục cao nhất**; gap vĩnh viễn thì timeout và bỏ qua (đánh đổi availability). Backpressure: channel dispatch đầy → pause partition, monitor resume khi tải giảm, record đã kéo về được buffer và xả trước. Rebalance: đánh dấu revoking, chờ in-flight (check mỗi 50 ms), commit watermark cuối — [Building a Session-Ordered Kafka Pipeline in Go](https://www.infoq.com/articles/apache-kafka-golang-session-ordered-pipeline) (bậc 2, 2026-10-07)
- Số liệu: benchmark tổng hợp 14.027 msg/s (10 partition, p99 185 ms, 0 vi phạm thứ tự); load test 48.805 msg/s (mục tiêu 50k), p99 2.843 ms do quota API Gateway; production >40 triệu message, 460 vào DLQ (~0,002%) — cùng nguồn
- Lỗi đã gặp: worker pool phẳng khiến một session đang retry chặn session khác; goroutine retry riêng + queue RAM phức tạp, rủi ro RAM không giới hạn; commit offset "mới nhất đã xong" làm mất message chưa xong khi crash; detector "partition kẹt" dựa trên in-flight luôn khác rỗng báo sai dưới tải liên tục → đổi sang timeout theo từng offset; pause theo partition gây ảnh hưởng chéo giữa các session — cùng nguồn

**LinkedIn — Brooklin**
- Brooklin chạy từ 2016, "thousands of data streams and over 2 trillion messages per day"; thay Kafka MirrorMaker, giảm cụm mirroring từ hàng trăm xuống khoảng một chục. **Phát hiện lỗi theo từng partition, tự pause partition lỗi**, tự resume sau khoảng cấu hình được, các partition/pipeline khác chạy bình thường. Chế độ "flushless-produce" checkpoint tiến độ **theo partition** thay vì theo pipeline, tránh lời gọi flush đồng bộ của producer có thể làm đứng pipeline vài phút. Có REST endpoint chẩn đoán lag và lỗi theo partition — [Open sourcing Brooklin: Near real-time data streaming at scale](https://www.linkedin.com/blog/engineering/open-source/brooklin-open-source) (bậc 1, 2019-07-16)
- Một talk Current 2026 nêu >7 nghìn tỉ message/ngày trên 50+ cluster (chỉ thấy qua kết quả search, chưa mở) — [Building Reliable CDC and Kafka Mirroring Pipelines at Trillion-Message Scale](https://current.confluent.io/post-conference-videos-26/building-reliable-cdc-and-kafka-mirroring-pipelines-at-trillionmessage-scale-ldn26) (bậc 2, 2026; **chưa xác minh**)

**Netflix — Keystone & Data Mesh (dùng Flink, không tự viết)**
- Keystone: data pipeline + "Stream Processing as a Service" trên Flink; **mỗi job một cluster Flink riêng** để cô lập, chỉ chia sẻ ZooKeeper và S3 (checkpoint). Routing hỗ trợ at-least-once tuỳ chỉnh được (đánh đổi latency vs đảm bảo). Control plane khai báo goal state lưu ở RDS, tự hồi phục bằng reconciliation; backfill/rewind job qua UI. Nguyên tắc: "failure as a first-class citizen", cho đánh đổi tuỳ chỉnh được. Năm 2016: 36 cluster Kafka, >700 tỉ message/ngày — [Netflix Keystone Real-Time Stream Processing Platform](https://www.infoq.com/news/2018/09/Netflix-Keystone-Real-Time-Proc) (bậc 2, 2018-09-30, tóm tắt blog Netflix)
- Data Mesh: control plane (Controller) + data plane (pipeline); Kafka là tầng vận chuyển giữa các processor Flink nối tiếp nhau; sink processor ghi ra Iceberg/Elasticsearch/Kafka; có Processor SDK. Talk 2025 nêu >20.000 job Flink và hàng nghìn topic — [netflix data mesh](https://www.infoq.com/news/2022/08/netflix-data-mesh/) (bậc 2, 2022-08); con số 20.000 job từ [DSS Virtual 2025 talk](https://streamnative.io/videos/dss-virtual-2025-building-the-next-generation-of-real-time-data-pipelines-data-mesh-and-streaming-sql-at-netflix) (bậc 2, 2025, chỉ thấy qua snippet)

### Nhận định
- **Nhận định:** Cách tách tầng chung nhất là **Source/Trigger (fetch + quản lý partition) → Decode/validate → Process (plugin/handler do người dùng viết) → Sink/Writer**, bọc bởi một **Runtime** lo offset, retry/DLQ, metric, health check, shutdown. Cloudflare (`READER`/`TRANSFORMATIONS`/`WRITER`) và Grab (Trigger/Runtime/Pipeline) gần như trùng nhau; uForwarder là cùng mô hình nhưng tầng Process nằm ở service khác qua gRPC.
- **Nhận định:** Ba cơ chế xuất hiện lặp lại ở gần như mọi engine tự viết: (a) **offset tracker cho commit không theo thứ tự** (commit tới offset liên tục cao nhất) — Uber, InfoQ session pipeline; (b) **pause/resume theo partition** cho backpressure, delay và lỗi — Uber DelayProcessManager, Brooklin, InfoQ; (c) **tách lỗi tạm thời vs poison pill**, poison đi DLQ, có công cụ replay DLQ — Uber, OpenMeter, InfoQ.
- **Nhận định:** Lỗi thường gặp được ghi nhận: health check chỉ kiểm tra kết nối (Cloudflare); state theo partition không dọn khi rebalance gây lỗi dây chuyền (Cloudflare); commit offset "mới nhất xong" thay vì "liên tục cao nhất" (InfoQ); worker pool phẳng gây HOL chéo key (InfoQ); HPA theo CPU cho consumer (Grab); abstraction giấu cấu hình gây partition skew (Cloudflare); thiếu kế hoạch partition trước khi launch (Cloudflare); retry topic một partition do dừng cả fetcher (Uber thiết kế cũ); một event lỗi làm fail cả batch sink (OpenMeter).
- **Nhận định:** Exactly-once "thực tế" ở các case đều là **at-least-once + dedupe/idempotency** (Segment RocksDB, OpenMeter Redis + ClickHouse), không phải Kafka transactions, vì sink nằm ngoài Kafka.

### Khoảng trống
- Chưa tìm được bài gốc của Shopify, Zalando, Agoda về kiến trúc consumer engine (Agoda chỉ có bài về load balancing partitioner/assignor và failover consumer giữa cluster — [How We Solve Load Balancing Challenges in Apache Kafka](https://medium.com/agoda-engineering/how-we-solve-load-balancing-challenges-in-apache-kafka-8cd88fdad02b), chưa mở). Truy vấn đã thử: "Agoda Kafka consumer parallel processing engineering blog".
- Không có số throughput msg/s cụ thể của uForwarder hay của một consumer Go đơn lẻ ở quy mô >500k msg/s trong các bài đã đọc; các con số đều là tổng/ngày hoặc /tuần.
- Bài Netflix gốc (Tech Blog) không mở được trực tiếp; dùng bản tóm tắt InfoQ.
- Phần cuối bài Wix (ordering/ack/offset của proxy, kết quả thực tế) bị cắt khi đọc.
- Nội dung bài Grab về GOMAXPROCS chỉ thấy qua snippet search.

## Câu hỏi phụ 6b: Bản đồ quyết định "đặc điểm bài toán → kỹ thuật/kiến trúc", và anti-pattern

### Kết luận ngắn
Có thể tổng hợp một bảng quyết định khá chắc từ các case: xử lý stateless + I/O chậm → song song trong partition với offset tracker (hoặc theo key nếu cần thứ tự); cần thứ tự theo entity → hash theo key vào worker/goroutine cố định, retry tại chỗ; cần "exactly-once" với sink ngoài → at-least-once + idempotent/dedupe theo key; message chậm/không đều → fast/slow lane; nhiều team, nhiều consumer group → SDK chung, quy mô cực lớn mới tính push proxy; stateful nặng (window/join) → Flink/nền tảng có sẵn. Mức chắc chắn: **trung bình** — các hàng của bảng là suy luận tổng hợp từ các case bậc 1, không có nguồn nào đưa ra nguyên bảng.

### Phát hiện có nguồn
- Proxy chỉ đáng khi quy mô cực lớn và có platform team; quy mô nhỏ–vừa nên bắt đầu bằng pull consumer native, thêm parallel-consumer khi gọi DB/HTTP chậm — [Kai Waehner](https://www.kai-waehner.de/?p=8276) (bậc 2, 2025-09-30)
- Song song trong partition (batch + goroutine/message) tăng >10x throughput cho tác vụ I/O-bound; message chậm cần lane riêng — [Cloudflare Scaling Security Insights](https://blog.cloudflare.com/scaling-security-scans) (bậc 1, 2026-06-12)
- Out-of-order commit + phát hiện HOL + DLQ cho message queuing nhiều service — [Uber uForwarder](https://www.uber.com/en-NG/blog/introducing-ufowarder) (bậc 1, 2026-02-05)
- Thứ tự theo session với song song giữa session: hash theo key → goroutine per-key, retry tại chỗ, commit theo watermark liên tục — [InfoQ session-ordered pipeline](https://www.infoq.com/articles/apache-kafka-golang-session-ordered-pipeline) (bậc 2, 2026-10-07)
- Retry topic/DLQ phá thứ tự so với traffic sống, chỉ hợp khi thứ tự không quan trọng — [Uber reliable reprocessing](https://www.uber.com/US/en/blog/reliable-reprocessing/) (bậc 1, 2018-02-16)
- Dedupe theo key với state cục bộ (RocksDB) cho cửa sổ dài và số key lớn — [Segment](https://www.twilio.com/en-us/blog/insights/exactly-once-delivery/) (bậc 1, 2017-06-29); dedupe qua Redis + batch insert idempotent cho sink OLAP — [OpenMeter](https://openmeter.io/blog/consistent-kafka-consumer) (bậc 1, 2023-10-18)
- Số pod cố định = số partition + VPA tốt hơn HPA theo CPU cho consumer — [Grab](https://engineering.grab.com/optimally-scaling-kafka-consumer-applications) (bậc 1, 2020-10-13)
- Stateful/analytics nhiều job, nhiều team → nền tảng Flink có cô lập job, checkpoint S3, control plane khai báo — [Netflix Keystone (InfoQ)](https://www.infoq.com/news/2018/09/Netflix-Keystone-Real-Time-Proc) (bậc 2, 2018-09-30)
- Cô lập lỗi theo partition (pause partition lỗi, checkpoint theo partition) cho pipeline di chuyển dữ liệu — [Brooklin](https://www.linkedin.com/blog/engineering/open-source/brooklin-open-source) (bậc 1, 2019-07-16)

### Nhận định
Bảng quyết định đề xuất (tổng hợp của agent từ các case trên):

| Đặc điểm bài toán | Kỹ thuật / kiến trúc gợi ý | Case tham chiếu | Đánh đổi chính |
|---|---|---|---|
| Stateless, xử lý nhanh CPU-bound, không cần thứ tự | Một goroutine/partition, batch, commit sau batch; scale bằng thêm partition + pod | Grab (pod = partition) | Song song bị trần bởi số partition |
| Stateless, I/O chậm (gọi DB/API), không cần thứ tự | Song song trong partition (worker pool/goroutine per message) + **offset tracker commit liên tục cao nhất** + giới hạn in-flight | Cloudflare (10x), Uber tracker | Crash → xử lý lại nhiều hơn; cần idempotent |
| Cần thứ tự theo entity (user/order/session) | Producer đặt key = entity; consumer hash key → worker/goroutine cố định; retry **tại chỗ** (backoff + jitter), không dùng retry topic | InfoQ session pipeline | Một key lỗi lâu chặn key đó; pause partition ảnh hưởng chéo |
| Không cần thứ tự, lỗi tạm thời phổ biến | Retry topic theo tầng delay + DLQ + công cụ list/purge/merge; delay bằng pause theo partition | Uber 2018, uForwarder | Nhiều topic; mất thứ tự |
| Message thời gian xử lý rất không đều (ms vs giờ) | Fast lane / slow lane (consumer group riêng), phát hiện HOL → đẩy DLQ/slow lane | Cloudflare, uForwarder | Thêm topic/group, logic định tuyến |
| Cần "exactly-once" với sink ngoài Kafka (DB, OLAP) | At-least-once + idempotency key = message key; dedupe (Redis hoặc RocksDB cục bộ); validate trước khi batch insert, event lỗi vào DLQ | OpenMeter, Segment | Còn ca biên cần đối soát; chi phí store dedupe |
| Kafka → Kafka (read-process-write) | Kafka transactions/EOS là lựa chọn (xem góc delivery semantics); hoặc topic output làm nguồn sự thật + dedupe | Segment (output topic là WAL) | Latency cao hơn với transactions |
| Stateful nặng: window, join, aggregation dài | Dùng Flink/Kafka Streams/nền tảng có sẵn; tự viết chỉ khi state đơn giản (dedupe/KV) với store cục bộ + khôi phục | Netflix Keystone/Data Mesh; Segment (state đơn giản tự viết) | Vận hành thêm hệ thống; JVM |
| Nhiều team/service cùng đọc, chi phí đọc lớn | SDK chung có chính kiến (metric, mTLS, health check mặc định); quy mô cực lớn mới tính push proxy gRPC | Cloudflare, Grab, Wix, Uber | Proxy: thêm hop latency, hạ tầng mới |
| Pipeline di chuyển dữ liệu nhiều nguồn/đích | Connector framework (Reader/Transform/Writer cấu hình được), cô lập lỗi theo partition | Cloudflare connectors, Brooklin | Ít linh hoạt cho logic phức tạp |

Anti-pattern rút ra (mỗi cái có case đã gặp, xem phần 6a):
1. Liveness check chỉ kiểm tra kết nối broker → bỏ sót consumer kẹt (Cloudflare).
2. Giữ state theo partition mà không dọn khi revoke → báo sai, restart dây chuyền (Cloudflare).
3. Commit offset của message "mới nhất xong" khi xử lý song song → mất dữ liệu khi crash (InfoQ).
4. Worker pool phẳng cho bài toán cần thứ tự → HOL chéo key (InfoQ).
5. Autoscale consumer bằng HPA theo CPU → tải lệch, lãng phí (Grab).
6. Không lên kế hoạch partition trước khi launch → không scale được khi sự cố (Cloudflare).
7. Dừng cả fetcher để chờ delay retry → retry topic chỉ 1 partition (Uber thiết kế cũ).
8. Batch sink không validate trước → một event hỏng làm fail cả batch (OpenMeter).
9. Abstraction giấu cấu hình quan trọng → partition skew (Cloudflare).
10. Dựng push proxy khi chưa đủ quy mô → thêm phức tạp, latency, rủi ro (Kai Waehner).

### Khoảng trống
- Không có nguồn nào đưa ra số liệu ngưỡng định lượng (vd "trên X msg/s thì nên chuyển proxy/Flink"); bảng trên là suy luận định tính.
- Chưa có case Go ở quy mô >500k msg/s cho một consumer group đơn lẻ với số liệu chi tiết (latency, CPU/msg).
- Phần Kafka transactions/EOS read-process-write thuộc góc delivery semantics; ở đây không có case study cụ thể nào dùng nó trong Go.

## Truy vấn đã chạy
- Uber uForwarder Kafka consumer proxy (standard)
- Uber reliable reprocessing Kafka dead letter queue (standard)
- Cloudflare blog Kafka consumers Go scale (standard)
- Netflix Keystone real-time stream processing platform architecture (standard)
- Cloudflare "Scaling Security Insights" Kafka consumer throughput (standard)
- Grab Coban Kafka consumer platform Go (standard)
- Segment engineering Kafka Go consumer deduplication exactly-once (standard)
- Agoda Kafka consumer parallel processing engineering blog (standard)
- Netflix data mesh Kafka Flink processors architecture blog (standard)
- Wix Greyhound Kafka consumer platform (standard)
- Netflix tech blog Keystone real-time stream processing platform 2018 (standard)
- LinkedIn Kafka consumer Brooklin trillions messages architecture (standard)
