# State và join

> **State** là dữ liệu engine phải nhớ giữa các event: số đếm, window đang mở, tập key đã thấy, bảng tra cứu. Thiết kế chuẩn đặt state **cục bộ theo partition** trong một store nhúng, và sao lưu nó bằng một **changelog topic** compacted. Khi partition đổi chủ, state được dựng lại bằng cách đọc changelog. **Join** là trường hợp đặc biệt của stateful processing. Nó đòi dữ liệu cần ghép nằm cùng chỗ, tức hai topic phải **co-partitioned**.

## Tại sao cần biết
Stateless engine crash thì chỉ cần đọc lại vài record. Stateful engine crash thì còn phải trả lời: state đang ở đâu, nó khớp với offset nào, dựng lại mất bao lâu. State sai lệch với offset là nguồn đếm sai khó phát hiện: phục hồi xong, số đếm có thể thiếu hoặc thừa đúng phần nằm giữa hai mốc. Thời gian dựng lại state quyết định một lần rebalance mất vài giây hay hàng giờ. Đây là phần mà tự làm tốn công nhất, và là ranh giới thực tế giữa "tự viết được" và "nên dùng framework" (xem [14-engine-architecture-and-frameworks.md](14-engine-architecture-and-frameworks.md)).

## Khái niệm cốt lõi

### Task theo partition
- **Là gì**: đơn vị xử lý gắn cố định với một partition input (hoặc một nhóm partition cùng chỉ số của nhiều topic). Mỗi task có state riêng, không chia sẻ với task khác.
- **Dùng để**: vì mọi event của một key nằm trong một partition (xem [02-kafka-log-model.md](02-kafka-log-model.md)), state của key đó chỉ cần nằm ở task của partition đó. Không có hai luồng cùng sửa một state, nên không cần khoá giữa các task. Khi partition đổi chủ, state của nó di chuyển theo.

### Store cục bộ (embedded store)
- **Là gì**: một key-value store chạy ngay trong process của engine, lưu trên đĩa cục bộ. Loại phổ biến dùng cấu trúc LSM tree (RocksDB, Pebble, LevelDB, BadgerDB).
- **Dùng để**: đọc ghi state với độ trễ của bộ nhớ hoặc đĩa cục bộ, không qua mạng. Khoảng cách với đọc từ xa rất lớn. Một phép đo công khai cho thấy store cục bộ xử lý nhiều hơn khoảng 100 lần so với gọi database từ xa bằng I/O đồng bộ không batching.
- Một store hỗ trợ **xoá theo dải** (range deletion) tiện cho window: khoá dạng `key|windowStart` cho phép xoá cả dải window hết hạn bằng một thao tác.

### Store bên ngoài (remote store)
- **Là gì**: state đặt trong một hệ thống riêng (Redis, Cassandra, ScyllaDB, database quan hệ), truy cập qua mạng.
- **Dùng để**: state cần đọc chung giữa nhiều service; dữ liệu không co-partition được; muốn thêm bớt instance mà không phải chuyển state.
- **Đánh đổi**: độ trễ mạng cho mỗi event (giảm được bằng batching hoặc pipeline), thêm một hệ thống phải vận hành, và offset Kafka không cùng transaction với ghi state. Khi đó phải dùng ghi idempotent hoặc lưu offset trong chính store (xem [06-idempotency-and-sinks.md](06-idempotency-and-sinks.md)).

### Changelog topic
- **Là gì**: topic ghi lại mọi cập nhật của một store, theo khoá của store, bật compaction để chỉ giữ giá trị mới nhất của mỗi khoá. Changelog có cùng số partition với input, và partition changelog *i* là bản sao lưu của state của task *i*.
- **Dùng để**: sao lưu state lên Kafka. Đọc changelog từ đầu sẽ được đúng state mới nhất (stream-table duality, xem [01-stream-processing-fundamentals.md](01-stream-processing-fundamentals.md)). Khoá hết hạn (window cũ) được xoá bằng tombstone, nếu không changelog phình mãi.

### Checkpoint cục bộ
- **Là gì**: ghi "offset changelog đã áp dụng vào store" ngay trong store, cùng một batch với dữ liệu.
- **Dùng để**: khi khởi động lại trên đúng đĩa cũ, engine chỉ cần đọc phần changelog sau checkpoint thay vì đọc lại từ đầu.

### Restore
- **Là gì**: quá trình dựng lại state của một partition vừa được giao: đọc changelog từ checkpoint (hoặc từ đầu) tới cuối, ghi vào store, xong mới bắt đầu xử lý input.
- **Dùng để**: tiếp quản partition sau crash hoặc rebalance. Thời gian restore xấp xỉ bằng kích thước changelog chia cho tốc độ đọc và ghi vào store, và đó là khoảng thời gian partition không được xử lý. Với state lớn, nó có thể kéo dài hàng giờ.

### Standby và warmup replica
- **Standby replica**: một instance khác liên tục đọc changelog để giữ sẵn bản sao state. **Dùng để** khi partition chuyển sang instance đó, nó gần như không phải restore.
- **Warmup replica**: bản sao được dựng tạm trên instance đích *trước* khi chuyển quyền sở hữu partition. Quyền chỉ chuyển khi bản sao đã theo kịp tới một ngưỡng lag chấp nhận được. **Dùng để** scale out mà không có một khoảng dài partition đứng chờ restore.

### Giữ partition và đĩa đi cùng nhau
- **Là gì**: instance khởi động lại nhận lại đúng partition cũ (static membership, sticky assignment, xem [04-rebalancing-and-scaling.md](04-rebalancing-and-scaling.md)) và gắn lại đúng đĩa cũ (ổ đĩa bền gắn theo danh tính instance).
- **Dùng để**: restart chỉ cần đọc phần changelog còn thiếu sau checkpoint. Thiếu một trong hai thì mỗi lần restart là một lần restore đầy đủ.

### Checkpoint toàn cục và savepoint
- **Checkpoint phân tán** (cách của Flink): định kỳ chèn một "barrier" vào dòng dữ liệu tại nguồn. Barrier không bao giờ vượt record. Khi mọi operator nhận barrier, chúng chụp state của mình lên storage bền; snapshot cùng vị trí đọc của nguồn tạo thành một điểm nhất quán toàn cục. Đây là biến thể của thuật toán Chandy-Lamport. Phục hồi là nạp snapshot và đọc lại nguồn từ vị trí đã ghi. **Dùng để** có state nhất quán với vị trí đọc mà không cần changelog topic cho từng store.
- **Savepoint**: checkpoint được tạo thủ công và giữ lại. **Dùng để** dừng chương trình, nâng cấp logic hoặc thay đổi độ song song, rồi chạy tiếp từ đúng state đó.

### Nhất quán giữa state, changelog và offset
- **Là gì**: ba thứ phải khớp nhau: state trong store, những gì đã ghi vào changelog, và committed offset của input.
- **Dùng để**: hiểu nguồn gốc của số đếm sai sau phục hồi. Ở at-least-once, engine cập nhật store, ghi changelog, rồi commit input. Crash trước khi commit thì input được đọc lại và cộng lần hai vào state, trừ khi thao tác trên state là idempotent. Ở exactly-once, ghi changelog, ghi output và commit offset nằm trong một transaction Kafka. Nhưng store cục bộ không thuộc transaction đó, nên crash giữa chừng có thể để store "đi trước" changelog. Cách an toàn nhất, và cũng là cách của một số framework, là xoá store cục bộ rồi dựng lại toàn bộ từ changelog sau crash.

### Co-partitioning
- **Là gì**: hai topic là co-partitioned khi chúng có cùng số partition, dùng cùng khoá, và mọi producer dùng *cùng một hàm băm*. Khi đó một khoá luôn nằm ở partition cùng chỉ số trong cả hai topic.
- **Dùng để**: cho phép join và aggregate trên nhiều topic mà không cần chuyển dữ liệu qua mạng. Task *i* chỉ cần đọc partition *i* của cả hai topic.
- Framework kiểm tra được *số partition* nhưng không kiểm tra được *hàm băm*. Một producer dùng hàm băm khác (fnv thay vì murmur2) phá co-partitioning mà không có lỗi nào được báo.
- **Repartition**: khi hai topic không co-partitioned, hoặc phải join theo một khoá khác, engine ghi lại một bên sang topic trung gian với khoá mới và số partition khớp, rồi mới join.

### Các loại join

| Join | Là gì | Cần window | Cần co-partitioning |
|---|---|---|---|
| Stream-stream | Ghép event của hai stream có cùng khoá xảy ra gần nhau | Có, bắt buộc, vì nếu không state phải giữ mọi event mãi mãi | Có |
| Stream-table | Ghép mỗi event với giá trị *hiện tại* của khoá đó trong một bảng (dựng từ topic compacted) | Không | Có |
| Stream-global table | Mỗi instance giữ *toàn bộ* bảng, nên event ở partition nào cũng tra được | Không | Không |
| Table-table, foreign-key | Ghép hai bảng; foreign-key join theo một trường không phải khoá | Không | Table-table thì có; foreign-key thì framework tự repartition |

- **Dùng để**: chọn đúng loại theo câu hỏi. "Đơn hàng có thanh toán trong vòng 1 giờ không" là stream-stream có window 1 giờ. "Làm giàu click bằng hồ sơ user hiện tại" là stream-table. "Tra quốc gia từ mã quốc gia" (bảng nhỏ) là global table.

## Cách hoạt động

```
              input topic (P0..P3)                   changelog topic (P0..P3, compacted)
                    │                                          ▲
  task P2 ──────────┼──────────────────────────────────────────┼─────────────
   1. đọc record   ─┘                                          │
   2. đọc/ghi store cục bộ (state của P2)                      │
   3. ghi cập nhật vào changelog P2 ───────────────────────────┘
   4. ghi output
   5. commit offset input (sau khi changelog đã được xác nhận;
      hoặc 3 + 4 + 5 trong một transaction)

  khi được giao P2 ở instance khác:
   a. mở store (đĩa cũ nếu có), đọc checkpoint (offset changelog đã áp dụng)
   b. pause input P2, đọc changelog P2 từ checkpoint → cuối, ghi batch vào store
   c. resume input P2 từ committed offset
```

Những mảnh phải có khi tự xây một engine stateful, xếp theo độ khó tăng dần:

| Mảnh | Việc phải làm |
|---|---|
| Task theo partition | Mỗi partition một luồng, một store (thư mục riêng hoặc prefix riêng), một partition changelog cùng chỉ số |
| Đường ghi | Store → changelog → commit input, đúng thứ tự, hoặc gói trong transaction |
| Checkpoint cục bộ | Ghi offset changelog đã áp dụng cùng batch với dữ liệu |
| Restore | Consumer riêng, ngoài group, đọc changelog; pause input trong lúc restore |
| Gắn với rebalance | Khi bị thu hồi: flush store, chốt checkpoint, commit. Khi được giao: restore |
| Window store | Khoá `key|windowStart`, stream-time theo partition, đóng theo grace, tombstone khi hết hạn |
| Timer | Theo stream-time và theo đồng hồ thật |
| Join | Stream-table: nạp topic bảng vào store. Stream-stream: hai window store |
| Standby / warmup | Instance khác đọc sẵn changelog |

## Ví dụ

Dedupe event theo `event_id` trong cửa sổ 7 ngày, topic 32 partition, khoảng 2 tỉ key mỗi tuần, mỗi key cộng metadata khoảng 40 byte:

| Đại lượng | Ước lượng |
|---|---|
| State tổng | 2 × 10⁹ × 40 B ≈ 80 GB |
| State mỗi partition | 80 / 32 ≈ 2,5 GB |
| Restore một partition từ đầu changelog, đọc và ghi 50 MB/s | ≈ 50 giây |
| Restore cả 32 partition trên một instance mới, tuần tự | ≈ 27 phút |

Cùng một state, nhưng instance khởi động lại *với đĩa cũ* chỉ phải đọc phần changelog sau checkpoint, tức vài giây. Khoảng cách giữa 27 phút và vài giây là lý do partition và đĩa phải đi cùng nhau.

## Câu hỏi

**State nên đặt cục bộ hay ở một store bên ngoài?**
> - **Store cục bộ**: key-value store chạy trong process, trên đĩa cục bộ, mỗi partition một phần.
> - **Store bên ngoài**: hệ thống riêng, truy cập qua mạng.
>
> Tiêu chí: store cục bộ thắng về độ trễ và throughput (không qua mạng, không tranh chấp), nhưng gắn chặt với partition, nên phải changelog, restore và co-partitioning. Store bên ngoài thắng khi state cần dùng chung giữa nhiều service, khi dữ liệu không co-partition được, hoặc khi muốn thay đổi số instance mà không phải chuyển state; cái giá là độ trễ mạng cho mỗi event và khó giữ nhất quán với offset.
>
> Ranh giới: ở tải vừa phải, hoặc khi gom thao tác theo batch, độ trễ của store bên ngoài thường chấp nhận được. Khoảng cách hàng trăm lần chỉ rõ khi mỗi event gọi một lần đồng bộ.

**Changelog topic là gì, và state được phục hồi thế nào khi partition đổi chủ?**
> - **Changelog topic**: topic compacted ghi mọi cập nhật của store.
> - **Restore**: đọc changelog để dựng lại store.
>
> Quy tắc: state cục bộ được sao lưu bằng cách ghi mọi cập nhật vào một partition changelog cùng chỉ số. Instance mới nhận partition sẽ đọc partition changelog đó tới cuối rồi mới xử lý input. Compaction giữ changelog ở kích thước "một bản mới nhất cho mỗi khoá", nên đọc hết changelog là được state mới nhất.
>
> Ranh giới: thời gian restore tỉ lệ với kích thước state, và partition không được xử lý trong thời gian đó. Ba cách rút ngắn: checkpoint cộng đĩa cũ (chỉ đọc phần thiếu), standby hoặc warmup replica (bản sao có sẵn), và tăng số partition để chia nhỏ state.

**Vì sao số đếm có thể sai sau khi engine stateful phục hồi?**
> - **Nhất quán state–offset**: state phải phản ánh đúng các record trước committed offset, không thiếu, không thừa.
>
> Quy tắc: state, changelog và committed offset được ghi ở ba thời điểm khác nhau. Crash giữa các thời điểm đó làm chúng lệch nhau. State đi trước offset thì record được đọc lại và áp dụng hai lần (đếm thừa). Offset đi trước state thì record bị bỏ qua (đếm thiếu). At-least-once cho trường hợp đầu, nên thao tác trên state phải idempotent; exactly-once đòi gói changelog, output và offset vào một transaction, và dựng lại store từ changelog sau crash.
>
> Ranh giới: thao tác ghi đè (lưu trạng thái mới nhất của khoá) tự nhiên chịu được áp dụng lặp. Thao tác cộng dồn (đếm, tổng) thì không, và chính chúng là nơi lệch nhất quán lộ ra.

**Co-partitioning là gì, và vì sao join cần nó?**
> - **Co-partitioning**: cùng số partition, cùng khoá, cùng hàm băm ở mọi producer.
> - **Repartition**: ghi lại dữ liệu với khoá hoặc số partition mới để đạt co-partitioning.
>
> Quy tắc: join và aggregate theo khoá chỉ chạy cục bộ được khi mọi dữ liệu của một khoá, từ mọi topic tham gia, nằm ở cùng một task. Co-partitioning đảm bảo điều đó: khoá K ở partition *i* của topic A thì cũng ở partition *i* của topic B. Thiếu nó thì engine phải repartition trước khi join.
>
> Ranh giới: hai topic cùng số partition nhưng producer dùng hai hàm băm khác nhau vẫn *không* co-partitioned, và không có cơ chế nào tự phát hiện điều đó. Join kiểu global table không cần co-partitioning, vì mỗi instance giữ toàn bộ bảng, nhưng chỉ hợp với bảng đủ nhỏ.

**Stream-stream join khác stream-table join ở đâu?**
> - **Stream-stream join**: ghép event của hai stream xảy ra gần nhau về thời gian.
> - **Stream-table join**: ghép event với giá trị hiện tại của một bảng.
>
> Tiêu chí: hỏi "hai sự việc có xảy ra cùng nhau không" thì dùng stream-stream. Nó bắt buộc có window, vì engine phải giữ event của cả hai phía để chờ bên kia, và window giới hạn thời gian chờ đó. Hỏi "sự việc này gắn với trạng thái nào lúc nó xảy ra" thì dùng stream-table. Không cần window, vì bảng chỉ giữ giá trị mới nhất mỗi khoá.
>
> Ranh giới: stream-table join dùng giá trị bảng *tại lúc engine xử lý event*, không nhất thiết là giá trị tại event time. Khi replay dữ liệu cũ, event cũ có thể được ghép với giá trị bảng mới, trừ khi engine xử lý hai topic theo thứ tự timestamp.

**Tự viết một engine stateful khó ở những phần nào?**
> - **Window store, restore, standby, nhất quán state–offset**: các mảnh mà framework stream cung cấp sẵn.
>
> Quy tắc: độ khó tăng theo mức state *gắn với thời gian* và *gắn với rebalance*. State theo khoá đơn giản (đếm, dedupe, hồ sơ thực thể) chỉ cần task theo partition, store cục bộ, changelog và restore, nên tự viết được. Window theo event time (đặc biệt session window), join stream-stream, standby và warmup, nhất quán exactly-once giữa state và offset, cùng việc nâng cấp logic mà giữ nguyên state, là những phần tốn công và dễ sai nhất.
>
> Ranh giới: các bẫy thường gặp khi tự làm gồm đổi số partition input làm hỏng ánh xạ state, lệch hàm băm phá co-partitioning, changelog không có tombstone thì phình mãi, và đổi cấu trúc state mà không có công cụ chuyển đổi.

## Hiểu nhầm thường gặp
- **"State nằm trong RAM là đủ."** Crash hoặc rebalance là mất. State phải có bản sao bền (changelog hoặc checkpoint).
- **"Hai topic cùng số partition là co-partitioned."** Còn phải cùng khoá và cùng hàm băm.
- **"Có changelog thì phục hồi tức thì."** Restore tỉ lệ với kích thước state; không có đĩa cũ hay standby thì có thể mất hàng giờ.
- **"Exactly-once tự động bao cả store cục bộ."** Store cục bộ không thuộc transaction Kafka; tính nhất quán đạt được bằng cách dựng lại store từ changelog.

## Liên quan
- [02-kafka-log-model.md](02-kafka-log-model.md): compaction, tombstone và hàm băm của partitioner.
- [04-rebalancing-and-scaling.md](04-rebalancing-and-scaling.md): static membership giữ partition ở yên với state.
- [10-time-and-windows.md](10-time-and-windows.md): window là state có thời hạn.
- [14-engine-architecture-and-frameworks.md](14-engine-architecture-and-frameworks.md): khi nào state là lý do chọn framework.
