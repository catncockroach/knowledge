# Quan sát và vận hành

> Vận hành một engine consumer xoay quanh ba câu hỏi: nó có **đang tiến** không, nó **chậm bao nhiêu** so với dữ liệu, và có **tắt, deploy, chạy lại** được mà không mất dữ liệu không. Chỉ số trung tâm là **lag**, đo cả theo offset lẫn theo thời gian, đo từ *bên ngoài* engine, và đánh giá theo *xu hướng* thay vì theo một ngưỡng cố định. **Graceful shutdown** là một trình tự có thứ tự: ngừng nhận, xử lý hết phần đang dở, commit, rồi mới rời group. **Replay** chỉ an toàn khi engine được thiết kế cho nó từ đầu.

## Tại sao cần biết
Consumer hỏng thường không báo lỗi gì. Nó vẫn chạy, vẫn kết nối broker, chỉ là không tiến. Health check chỉ kiểm tra kết nối sẽ không thấy. Một ngưỡng lag cố định sẽ báo động giả trên topic nhiều traffic và bỏ sót trên topic ít traffic. Mỗi lần deploy đều là một lần các partition đổi chủ, và tắt sai thứ tự sẽ sinh bản trùng hoặc mất. Cuối cùng, sửa một lỗi logic thường có nghĩa là xử lý lại dữ liệu cũ. Engine không được thiết kế để replay sẽ cho kết quả khác nhau mỗi lần chạy lại.

## Khái niệm cốt lõi

### Các đại lượng cốt lõi
| Đại lượng | Là gì | Dùng để |
|---|---|---|
| Lag theo offset | Log end offset − committed offset, theo partition | Khối lượng việc còn tồn |
| Lag theo thời gian | Hiện tại − timestamp của record ở committed offset | Engine chậm bao nhiêu giây so với dữ liệu; so trực tiếp với yêu cầu latency |
| Độ trễ xử lý | Thời gian xử lý một record hoặc một batch | Tìm khâu chậm |
| Độ trễ đầu-cuối | Thời điểm sink ghi xong − timestamp của record | Độ "realtime" thật mà người dùng thấy |
| Throughput theo kết cục | Số record mỗi giây theo kết cục: thành công, retry, DLQ, bỏ qua | Tỉ lệ kết cục là tín hiệu chất lượng dữ liệu |
| Số lần rebalance | Đếm trong các callback giao và thu hồi partition | Rebalance dày bất thường là dấu hiệu instance restart liên tục |
| Lỗi commit | Số lần commit lỗi và thời gian commit | Commit lỗi kéo dài nghĩa là tiến độ không được lưu |
| Thời gian từ lần poll cuối | Bao lâu rồi vòng poll chưa chạy | Tín hiệu sống còn của chính engine |

### Đo lag từ bên ngoài
- **Là gì**: một thành phần độc lập với engine định kỳ đọc committed offset của group và log end offset của partition, rồi tính lag.
- **Dùng để**: engine đã chết hoặc bị treo thì không còn tự báo lag được. Chỉ phép đo từ bên ngoài mới thấy được tình huống đó. Nhiều client không tự xuất metric lag, nên phép đo bên ngoài thường là bắt buộc chứ không phải bổ sung.

### Đánh giá lag theo xu hướng
- **Là gì**: thay vì so lag với một ngưỡng cố định, xét một cửa sổ các lần commit gần nhất và phân loại:

  | Trạng thái | Điều kiện |
  |---|---|
  | OK | Trong cửa sổ có lúc lag về 0, hoặc lag đang giảm |
  | WARNING | Offset vẫn tiến nhưng lag không giảm |
  | STALLED | Consumer vẫn commit, nhưng committed offset không đổi |
  | STOPPED | Lần commit mới nhất đã cũ hơn cửa sổ |

- **Dùng để**: phát hiện consumer kẹt và consumer không theo kịp mà không cần chọn ngưỡng riêng cho từng topic.

### Cách tính lag theo thời gian
- **Nội suy**: suy thời gian từ tốc độ ghi gần đây và lag theo offset. Rẻ, nhưng sai khi producer ngừng ghi, khi topic ít traffic, và lúc mới khởi động. Một consumer có thể đã chết trên một topic mỗi ngày chỉ có một record, mà lag nội suy vẫn phẳng cả tuần.
- **Đọc record tại committed offset**: lấy timestamp của chính record đó và trừ khỏi hiện tại. Đắt hơn (một lần đọc thêm), nhưng phản ánh đúng.

### Tracing qua header
- **Là gì**: producer đặt *trace context* (định danh trace, định danh span) vào header của record. Consumer đọc header đó để nối span xử lý của mình với span tạo ra record.
- **Link thay vì quan hệ cha–con**: một batch chứa record từ nhiều trace khác nhau, nên span xử lý batch không thể là con của tất cả. Quy ước tracing cho messaging dùng *link*: span xử lý trỏ tới các span tạo record.
- **Dùng để**: lần theo một event qua nhiều service. Ở throughput rất cao, tạo span cho mọi record rất tốn, nên thường lấy mẫu theo tỉ lệ, trong khi metric vẫn đếm đủ.

### Toạ độ của record trong log
- **Là gì**: mỗi dòng log liên quan tới một record mang `topic`, `partition`, `offset`, `key` (hoặc hash của key) và `trace_id`.
- **Dùng để**: từ một dòng log lỗi có thể tìm lại đúng record trong Kafka để xem, replay hoặc đưa vào DLQ.

### Graceful shutdown
- **Là gì**: trình tự tắt có thứ tự để không mất và giảm trùng:
  1. Nhận tín hiệu dừng (SIGTERM).
  2. Ngừng poll record mới.
  3. Chờ xử lý xong phần đang dở, có giới hạn thời gian.
  4. Commit đồng bộ.
  5. Đóng client: rời group (member thường) hoặc giữ chỗ (static member).
- **Dùng để**: partition chuyển sang member khác với committed offset sát với tiến độ thật.
- **Thời hạn**: nền tảng chạy container chỉ chờ một khoảng thời gian cố định sau SIGTERM (Kubernetes mặc định 30 giây) rồi mới giết hẳn process. Toàn bộ trình tự phải xong trong thời hạn đó. Phần dở dang khi bị giết hẳn sẽ được xử lý lại.
- Member thường rời group thì rebalance chạy ngay. Static member không rời group, nên partition của nó đứng yên cho tới khi nó quay lại hoặc hết session timeout (xem [04-rebalancing-and-scaling.md](04-rebalancing-and-scaling.md)).

### Health check theo tiến độ
- **Là gì**: kiểm tra sống còn dựa trên việc engine có đang *tiến* không (vòng poll gần đây có chạy không, committed offset có tăng khi còn lag không), thay vì chỉ kiểm tra kết nối.
- **Dùng để**: phát hiện consumer kẹt mà vẫn kết nối broker bình thường.
- **Bẫy**: nếu engine giữ trạng thái tiến độ của partition đã bị thu hồi, nó sẽ thấy "partition này không tiến" và tự báo không khoẻ. Báo sai gây restart, restart gây rebalance, rebalance lại thu hồi partition của instance khác, và lỗi lan dây chuyền. Trạng thái theo partition phải được dọn ngay khi partition bị thu hồi.

### Replay và reprocess
- **Là gì**: xử lý lại dữ liệu đã có trong log, sau khi sửa lỗi logic hoặc để dựng một kết quả mới. Có hai cách:
  - **Reset offset của group** về một thời điểm hoặc một vị trí. Công cụ quản trị chỉ cho reset khi group không còn member đang chạy.
  - **Chạy một group mới song song**, ghi sang đích mới, so sánh với kết quả cũ, rồi mới chuyển sang dùng đích mới.
- **Dùng để**: sửa kết quả mà không cần dữ liệu nguồn ngoài Kafka.
- **Giới hạn**: chỉ replay được những gì còn trong retention. Tiered storage (đẩy dữ liệu cũ sang object storage) kéo dài cửa sổ replay, nhưng không áp dụng được cho topic compacted, và đọc từ tầng lưu trữ xa có thông lượng khác với đọc từ đĩa broker.
- **Điều kiện để replay cho kết quả đúng**: sink idempotent (xem [06-idempotency-and-sinks.md](06-idempotency-and-sinks.md)); logic theo thời gian dùng event time trong dữ liệu chứ không dùng đồng hồ máy (xem [10-time-and-windows.md](10-time-and-windows.md)); đọc được mọi phiên bản schema cũ (xem [12-schema-and-serialization.md](12-schema-and-serialization.md)); và có giới hạn tốc độ để luồng replay không giành tài nguyên của luồng realtime.

### Kiểm thử
| Công cụ | Là gì | Dùng để |
|---|---|---|
| Broker giả trong process | Một broker giả lập chạy ngay trong test, tiêm được lỗi theo request | Test nhanh trong CI các nhánh lỗi: commit lỗi, rebalance giữa chừng |
| Broker thật trong container | Broker Kafka chạy trong Docker cho test tích hợp | Kiểm tra hành vi thật của giao thức |
| Proxy gây lỗi mạng | TCP proxy chèn độ trễ, giới hạn băng thông, cắt kết nối | Kiểm tra hành vi khi mạng xấu |

- Các kịch bản chứng minh delivery semantics: giết engine sau khi xử lý mà trước khi commit, rồi kiểm tra không thiếu record; thêm và bớt instance giữa chừng, rồi kiểm tra committed offset không lùi; poison message vào DLQ mà không chặn partition; gửi SIGTERM và đo thời gian drain so với thời hạn. Một job đối soát đếm record vào và ra theo khoá là bằng chứng thực tế nhất.

## Cách hoạt động

Trình tự shutdown, minh hoạ bằng Go không gắn với client cụ thể:

```go
// Minh hoạ khái niệm.
ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
defer stop()

runPollLoop(ctx)          // thoát khi ctx bị huỷ: (2) ngừng poll

drainCtx, cancel := context.WithTimeout(context.Background(), 20*time.Second) // < thời hạn của nền tảng
defer cancel()
waitInFlight(drainCtx)    // (3) chờ worker xử lý xong phần đang dở
commitSync(drainCtx)      // (4) commit mốc an toàn (xem 08: offset tracker)
client.Close()            // (5) rời group, hoặc giữ chỗ nếu là static member
```

Các thành phần quan sát xung quanh engine:

```
                engine ──► metric: throughput theo kết cục, độ trễ, rebalance, lỗi commit, giây từ lần poll cuối
                   │  └──► log có toạ độ (topic, partition, offset, key, trace_id)
                   │  └──► span xử lý, link tới span tạo record (trace context trong header)
                   ▼
  bộ đo lag bên ngoài (đọc committed offset + log end offset; đọc record ở committed offset để tính lag theo giây)
                   │
                   ▼
  đánh giá theo xu hướng (OK / WARNING / STALLED / STOPPED) ──► cảnh báo, autoscale
```

## Ví dụ

Hai topic, cùng một ngưỡng lag cố định 10.000 record:

| Topic | Traffic | Lag theo offset | Lag theo thời gian | Ngưỡng cố định báo gì |
|---|---|---|---|---|
| `clicks` | 100.000 msg/s | 20.000 | 0,2 giây | Báo động, dù hoàn toàn bình thường |
| `refunds` | 1 msg/phút | 8 | 8 phút | Im lặng, dù consumer đã chết từ 8 phút trước |

Lag theo thời gian và đánh giá theo xu hướng (STOPPED với `refunds`) cho câu trả lời đúng ở cả hai dòng.

## Câu hỏi

**Đo sức khoẻ của consumer bằng những chỉ số nào?**
> - **Lag theo thời gian**: engine chậm bao nhiêu giây so với dữ liệu.
> - **Tiến độ commit**: committed offset có tăng không.
> - **Tỉ lệ kết cục**: phần record thành công, retry, vào DLQ.
>
> Quy tắc: một consumer khoẻ khi nó *đang tiến* và *đủ nhanh*. "Đang tiến" đo bằng tiến độ commit và thời gian từ lần poll cuối. "Đủ nhanh" đo bằng lag theo thời gian so với yêu cầu latency. Tỉ lệ kết cục đo chất lượng: engine tiến nhanh nhưng đẩy phần lớn record vào DLQ thì vẫn hỏng.
>
> Ranh giới: lag phải được đo từ bên ngoài engine, vì engine chết thì không tự báo được gì. Lag bằng 0 trên topic không có dữ liệu mới không chứng minh consumer còn sống.

**Vì sao không nên cảnh báo bằng một ngưỡng lag offset cố định cho mọi topic?**
> - **Lag theo offset**: số record còn tồn.
> - **Đánh giá theo xu hướng**: xét lag thay đổi thế nào qua một cửa sổ commit.
>
> Quy tắc: cùng một số record lag có nghĩa rất khác nhau tuỳ traffic. 20.000 record là 0,2 giây trên topic nhiều traffic nhưng có thể là hàng giờ trên topic ít traffic. Vì vậy cảnh báo hữu ích dựa trên lag theo *thời gian* so với yêu cầu, và trên *xu hướng* (lag không giảm, offset không tiến, commit đã dừng), không dựa trên một con số offset chung.
>
> Ranh giới: lag theo thời gian tính bằng nội suy sai trên topic ít traffic và khi producer ngừng ghi. Đọc timestamp của record ở committed offset cho kết quả đúng ở các trường hợp đó.

**Tắt consumer thế nào cho đúng? Deploy có làm mất hay trùng dữ liệu không?**
> - **Graceful shutdown**: ngừng nhận, xử lý hết phần dở, commit, rồi rời group.
> - **Thời hạn tắt**: thời gian nền tảng chờ sau SIGTERM trước khi giết hẳn process.
>
> Quy tắc: trình tự đúng là ngừng poll → chờ phần đang xử lý (có giới hạn) → commit đồng bộ → đóng client, và tất cả phải nằm trong thời hạn tắt. Làm đúng thì partition chuyển đi với committed offset sát tiến độ thật. Với at-least-once, deploy không làm mất dữ liệu nhưng *luôn có thể* sinh bản trùng: phần xử lý sau lần commit cuối, hoặc phần dở khi bị giết hẳn, sẽ được xử lý lại.
>
> Ranh giới: commit trong callback rồi đóng client đồng bộ ngay *bên trong* callback rebalance có thể gây deadlock ở một số client, nên việc đóng thường được thực hiện từ luồng chính sau khi vòng poll đã thoát.

**Health check cho consumer nên kiểm tra gì?**
> - **Liveness**: process còn hoạt động đúng không; sai thì bị restart.
> - **Health check theo tiến độ**: kiểm tra engine có đang tiến không.
>
> Quy tắc: health check của consumer phải đo *tiến độ*, vì lỗi phổ biến nhất là kẹt mà vẫn kết nối broker bình thường. Tín hiệu hợp lý gồm thời gian từ lần poll cuối, và committed offset có tăng khi vẫn còn lag không. Readiness (sẵn sàng nhận traffic) gần như không có nghĩa với consumer, vì consumer không nhận request từ load balancer.
>
> Ranh giới: health check theo tiến độ phải chỉ xét partition đang được giao. Giữ trạng thái của partition đã bị thu hồi sẽ gây báo sai, kéo theo restart và rebalance dây chuyền.

**Muốn xử lý lại dữ liệu cũ thì làm thế nào, và cần chuẩn bị gì?**
> - **Reset offset**: đưa committed offset của group về một mốc cũ.
> - **Group song song**: chạy một group mới đọc lại từ mốc cũ, ghi sang đích mới.
>
> Quy tắc: replay cho kết quả đúng khi xử lý là *tất định* và *idempotent*: sink chịu được ghi lặp, logic theo thời gian dùng event time trong dữ liệu, và mọi phiên bản schema cũ đều đọc được. Reset offset nhanh nhưng ghi đè lên kết quả hiện tại và đòi dừng group. Group song song an toàn hơn vì so sánh được trước khi chuyển, đổi lại tốn gấp đôi tài nguyên trong thời gian chạy.
>
> Ranh giới: chỉ replay được dữ liệu còn trong retention. Logic gọi đồng hồ máy hoặc gọi dịch vụ ngoài có trạng thái thay đổi theo thời gian sẽ cho kết quả khác lần chạy đầu, kể cả khi code không đổi.

## Hiểu nhầm thường gặp
- **"Consumer kết nối được broker là khoẻ."** Lỗi phổ biến nhất là kẹt mà vẫn kết nối.
- **"Engine tự báo lag là đủ."** Engine chết thì không báo được gì; lag phải đo từ bên ngoài.
- **"Rollout cẩn thận thì không có bản trùng."** Với at-least-once, mỗi lần partition đổi chủ đều có thể có bản trùng.
- **"Replay chỉ là reset offset."** Replay cho kết quả đúng chỉ khi engine idempotent, dùng event time và đọc được schema cũ.

## Liên quan
- [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md): lag và committed offset.
- [04-rebalancing-and-scaling.md](04-rebalancing-and-scaling.md): static membership khi tắt và khởi động lại.
- [06-idempotency-and-sinks.md](06-idempotency-and-sinks.md): điều kiện để replay an toàn.
- [10-time-and-windows.md](10-time-and-windows.md): event time và tính tất định khi chạy lại.
