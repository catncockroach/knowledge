# Delivery semantics: at-most-once, at-least-once, exactly-once

> Delivery semantics nói một message có thể có hiệu lực bao nhiêu lần khi có lỗi. **At-most-once**: tối đa một lần, có thể mất. **At-least-once**: ít nhất một lần, có thể trùng. **Exactly-once**: đúng một lần. Phía consumer, mức đạt được chỉ là hệ quả của *thứ tự giữa xử lý và lưu vị trí*. Exactly-once của Kafka (transactions) chỉ trọn vẹn khi cả đầu vào lẫn đầu ra đều là topic Kafka.

## Tại sao cần biết
Mọi engine phải trả lời "nếu crash ngay lúc này thì sao". Câu trả lời quyết định dữ liệu có thể mất hay có thể trùng, và quyết định sink cần được thiết kế thế nào. Đây cũng là chủ đề dễ hiểu nhầm nhất: "exactly-once" thường được hiểu là một tính năng bật lên là xong, trong khi thực tế nó có phạm vi rất hẹp. Hiểu đúng phạm vi đó là điều kiện để chọn giữa transactions và sink idempotent (xem [06-idempotency-and-sinks.md](06-idempotency-and-sinks.md)).

## Khái niệm cốt lõi

### Ba mức đảm bảo
- **At-most-once**
  - **Là gì**: mỗi message có hiệu lực 0 hoặc 1 lần. Lỗi xảy ra thì message có thể mất và không được giao lại.
  - **Dùng để**: dữ liệu mà mất một ít không sao và trùng thì có hại hơn, ví dụ metric lấy mẫu, log gỡ lỗi.
- **At-least-once**
  - **Là gì**: mỗi message có hiệu lực 1 hoặc nhiều lần. Lỗi xảy ra thì message được giao lại.
  - **Dùng để**: mức mặc định của hầu hết hệ thống, vì mất dữ liệu thường tệ hơn trùng, và trùng có thể khử ở sink.
- **Exactly-once**
  - **Là gì**: mỗi message có hiệu lực đúng một lần, kể cả khi có lỗi.
  - **Dùng để**: tiền, tồn kho, số đếm phải khớp. Nó đạt được *trong một phạm vi xác định*, không phải trên mọi hệ thống mà message đi qua.

### Exactly-once delivery và exactly-once processing
- **Là gì**: *delivery* là message được giao đúng một lần qua mạng. Điều này không làm được trong hệ phân tán, vì bên gửi không phân biệt được "bên nhận chưa nhận" với "bên nhận đã nhận nhưng xác nhận bị mất". *Processing* là *hiệu ứng* của message xảy ra đúng một lần. Điều này làm được, bằng cách cho phép giao lặp nhưng làm cho lần lặp vô hại.
- **Dùng để**: hiểu rằng mọi "exactly-once" thực tế đều là at-least-once delivery cộng một cơ chế khử trùng: transaction, idempotency key, hoặc lưu vị trí cùng kết quả. Cách gọi phổ biến cho kết quả này là **effectively-once**.

### Thứ tự giữa xử lý và commit
- **Commit trước, xử lý sau** → at-most-once: crash giữa hai bước thì phần đã commit mà chưa xử lý bị bỏ qua.
- **Xử lý trước, commit sau** → at-least-once: crash giữa hai bước thì phần đã xử lý mà chưa commit được xử lý lại.
- **Xử lý và commit trong cùng một thao tác nguyên tử** → exactly-once cho phạm vi của thao tác đó.

### Điểm vỡ theo từng phía

| Phía | Gây trùng khi | Gây mất khi |
|---|---|---|
| Producer | Retry sau một lần ghi thực ra đã thành công (xác nhận bị mất) | Không retry khi ghi lỗi; `acks` thấp và leader chết trước khi bản sao kịp chép |
| Consumer | Crash hoặc rebalance giữa lúc xử lý xong và lúc commit | Commit trước khi xử lý; xử lý song song mà commit offset lớn nhất |
| Sink ngoài | Xử lý lại sau crash, ghi lần hai | Ghi lỗi nhưng vẫn commit offset |

### Idempotent producer
- **Là gì**: producer nhận một định danh (PID) từ broker, và đánh số thứ tự (sequence number) cho mỗi batch gửi vào mỗi partition. Broker nhớ sequence cuối cùng của mỗi (PID, partition). Batch có sequence đã thấy thì bị coi là trùng và bỏ qua; batch nhảy cóc sequence thì báo lỗi.
- **Dùng để**: khử trùng do retry của producer, đồng thời giữ thứ tự ghi trong partition khi có retry.
- **Giới hạn**: chỉ có hiệu lực trong *một phiên* của producer. Producer restart nhận PID mới, và message gửi lại từ phiên mới không được nhận ra là trùng. Mức mặc định (bật hay tắt) khác nhau giữa các client.

### Transaction
- **Là gì**: nhóm nhiều lần ghi vào nhiều partition, cộng với việc commit offset của consumer, thành một đơn vị nguyên tử: hoặc tất cả có hiệu lực, hoặc không cái nào có. Thành phần chính:

  | Thành phần | Là gì | Dùng để |
  |---|---|---|
  | `transactional.id` | Định danh bền vững của producer, giữ nguyên qua restart | Coordinator nhận ra cùng một producer sau restart, hoàn tất hoặc huỷ transaction dở dang của phiên trước |
  | Transaction coordinator | Broker quản lý trạng thái transaction | Ghi nhận partition tham gia, điều phối commit hoặc abort |
  | Epoch (fencing) | Số thế hệ tăng mỗi khi producer cùng `transactional.id` khởi tạo lại | Chặn instance cũ (zombie) tiếp tục ghi |
  | Commit/abort marker | Record điều khiển ghi vào mỗi partition khi transaction kết thúc | Cho consumer biết record nào thuộc transaction đã commit. Marker chiếm offset nên dãy offset có lỗ |
  | Transaction timeout | Thời gian tối đa một transaction được mở | Coordinator tự abort transaction bị bỏ dở |

### Isolation level phía consumer
- **`read_uncommitted`**: nhận mọi record, kể cả record của transaction chưa commit hoặc đã abort.
- **`read_committed`**: chỉ nhận record của transaction đã commit. Consumer chỉ đọc tới **LSO** (last stable offset): offset đầu tiên còn thuộc một transaction đang mở.
- **Dùng để**: phía đọc chọn có tham gia đảm bảo exactly-once hay không. Producer dùng transaction mà consumer đọc `read_uncommitted` thì vẫn thấy dữ liệu bị abort. Mức mặc định khác nhau giữa các client.
- **Lưu ý**: transaction bị treo không kết thúc làm LSO không tiến, khiến mọi consumer `read_committed` của partition đó dừng theo.

### Read-process-write
- **Là gì**: mẫu "đọc từ topic A, xử lý, ghi sang topic B", trong đó offset của A được commit *bên trong* transaction ghi B.
- **Dùng để**: đạt exactly-once giữa các topic. Nếu transaction commit, cả output lẫn tiến độ đọc đều có hiệu lực. Nếu abort, cả hai bị huỷ và batch được đọc lại. Rebalance xảy ra giữa transaction thì transaction phải bị abort, vì partition input có thể đã sang tay member khác.

## Cách hoạt động

### At-least-once và at-most-once trong một vòng lặp

```go
// Minh hoạ khái niệm (giả mã Go, không gắn với client cụ thể).
for {
    batch := consumer.Poll(ctx)

    // at-most-once: commit trước
    // consumer.Commit(batch.NextOffsets())

    for _, r := range batch.Records {
        process(r) // ghi sink
    }

    // at-least-once: commit sau khi mọi record trong batch đã xử lý xong
    consumer.Commit(batch.NextOffsets())
}
```

Crash xảy ra giữa `process` và `Commit`:
- Commit ở cuối thì batch được xử lý lại (trùng).
- Commit ở đầu thì phần chưa xử lý của batch bị bỏ (mất).

### Exactly-once Kafka → Kafka bằng transaction

```
begin transaction
  ├─ ghi output vào topic B (nhiều partition)
  ├─ gửi offset input của topic A vào transaction (kèm thông tin group, thế hệ)
commit transaction ──► coordinator ghi commit marker vào mọi partition liên quan
                       ──► consumer read_committed của B thấy output
                       ──► offset của A có hiệu lực
crash trước commit ──► transaction bị abort (theo timeout hoặc khi producer khởi tạo lại)
                       ──► output bị bỏ, offset A không đổi, batch được đọc lại
```

### Phạm vi của exactly-once

```
  topic A ──► [engine] ──► topic B            ✓ exactly-once (transaction bao cả output lẫn offset)
  topic A ──► [engine] ──► PostgreSQL         ✗ transaction Kafka không bao được ghi DB
  topic A ──► [engine] ──► gọi API thanh toán ✗ không rollback được hiệu ứng bên ngoài
```

Với hai dòng dưới, transaction Kafka không giúp được. Engine phải dùng at-least-once cộng sink idempotent, hoặc lưu offset trong chính transaction của DB (xem [06-idempotency-and-sinks.md](06-idempotency-and-sinks.md)).

## Ví dụ

Engine đọc `payments`, ghi số dư vào DB, commit sau mỗi batch 500 record. Batch có offset 1000–1499:

| Thời điểm crash | Mức at-least-once | Hệ quả |
|---|---|---|
| Sau khi ghi DB record 1000–1299 | Committed offset vẫn là 1000 | Restart đọc lại 1000–1499; 300 record bị cộng số dư lần hai, trừ khi sink khử trùng |
| Sau khi ghi DB đủ 500 record, trước commit | Committed offset vẫn là 1000 | Cả 500 record bị cộng lần hai |
| Sau commit 1500 | Không trùng | Đọc tiếp từ 1500 |

Nếu đổi sink sang "ghi số dư kèm offset cuối đã áp dụng cho mỗi partition, trong cùng một transaction DB", lần đọc lại sẽ thấy offset ≤ 1499 đã áp dụng và bỏ qua. Kết quả là exactly-once cho sink này.

## Câu hỏi

**At-most-once, at-least-once và exactly-once khác nhau ở đâu?**
> - **At-most-once**: có thể mất, không trùng.
> - **At-least-once**: không mất, có thể trùng.
> - **Exactly-once**: không mất, không trùng, trong một phạm vi xác định.
>
> Quy tắc: mức đảm bảo do *thứ tự giữa việc tạo hiệu ứng và việc lưu vị trí* quyết định. Lưu vị trí trước thì at-most-once. Tạo hiệu ứng trước thì at-least-once. Gói cả hai vào một thao tác nguyên tử thì exactly-once trong phạm vi thao tác đó. Mọi cơ chế cụ thể (auto commit, commit tay, transaction, lưu offset trong DB) chỉ là cách sắp xếp hai việc này.
>
> Ranh giới: mức đảm bảo của cả pipeline là mức *yếu nhất* trong các khâu. Producer không idempotent làm trùng từ đầu vào; consumer exactly-once không khử được bản trùng đó.

**Kafka có exactly-once không? Phạm vi của nó tới đâu?**
> - **Transaction Kafka**: nhóm các lần ghi và commit offset thành một đơn vị nguyên tử.
> - **`read_committed`**: consumer chỉ thấy dữ liệu của transaction đã commit.
>
> Quy tắc: exactly-once của Kafka trọn vẹn khi mọi hiệu ứng của việc xử lý đều là ghi vào Kafka: đọc topic, ghi topic, commit offset, tất cả trong một transaction, và bên đọc dùng `read_committed`. Mọi hiệu ứng ra ngoài Kafka (ghi DB, gọi API, gửi email) nằm ngoài transaction. Nếu crash, các hiệu ứng đó đã xảy ra nhưng transaction bị abort, nên chúng sẽ lặp lại khi batch được đọc lại.
>
> Ranh giới: ngay trong Kafka, đảm bảo transaction được định nghĩa từ phía producer. Consumer `seek` vào giữa một transaction không chắc đọc trọn mọi message của transaction đó. Ngoài ra, cơ chế two-phase commit để Kafka tham gia transaction với hệ thống ngoài mới chỉ ở dạng đề xuất (KIP-939), chưa phải tính năng có thể dựa vào.

**Idempotent producer chống được trùng trong trường hợp nào, không chống được trường hợp nào?**
> - **PID**: định danh broker cấp cho một phiên producer.
> - **Sequence number**: số thứ tự batch theo từng partition.
>
> Quy tắc: idempotent producer khử trùng do *retry trong cùng một phiên*. Broker nhận ra batch đã ghi qua (PID, partition, sequence) và bỏ qua bản lặp. Nó không khử được trùng giữa các phiên: producer restart nhận PID mới, và message ứng dụng gửi lại sau restart là message mới đối với broker.
>
> Ranh giới: trùng do *consumer* xử lý lại (crash trước commit) không liên quan tới idempotent producer. Engine đọc lại batch và ghi lại output là ghi mới, trừ khi việc ghi nằm trong transaction hoặc sink tự khử trùng.

**Transaction có làm chậm hệ thống không? Đánh đổi là gì?**
> - **Chu kỳ transaction**: khoảng thời gian giữa hai lần commit transaction.
>
> Quy tắc: chi phí throughput của transaction giảm khi transaction dài hơn, vì chi phí cố định của mỗi lần commit được chia cho nhiều record. Cái giá chính là *latency*: bên đọc `read_committed` chỉ thấy dữ liệu khi transaction commit, nên độ trễ đầu-cuối không nhỏ hơn chu kỳ transaction. Transaction ngắn thì trễ ít nhưng tốn throughput; transaction dài thì ngược lại, và crash phải làm lại nhiều hơn.
>
> Ranh giới: số liệu đo cụ thể phụ thuộc kích thước message, chu kỳ và phiên bản. Chỉ con số đo trên chính workload mới dùng để quyết định được. Về mặt định tính: với chu kỳ commit vài chục giây, chi phí throughput gần như không đáng kể; với chu kỳ cỡ trăm mili-giây, nó trở nên rõ rệt.

**"Effectively-once" là gì, khác exactly-once ở đâu?**
> - **Effectively-once**: at-least-once delivery cộng xử lý idempotent, nên kết quả cuối cùng như thể mỗi message có hiệu lực đúng một lần.
>
> Quy tắc: effectively-once không ngăn message bị giao lặp, nó làm cho lần lặp vô hại. Đây là cách duy nhất đạt kết quả "đúng một lần" khi sink nằm ngoài Kafka. Về kết quả, nó tương đương exactly-once; về cơ chế, nó dời trách nhiệm khử trùng từ hạ tầng sang thiết kế của sink.
>
> Ranh giới: effectively-once chỉ đúng khi *mọi* hiệu ứng đều idempotent. Ghi DB bằng upsert nhưng mỗi lần xử lý lại gửi một email thì email vẫn bị gửi lặp.

## Hiểu nhầm thường gặp
- **"Bật exactly-once là xong."** Exactly-once chỉ bao phần ghi vào Kafka. Hiệu ứng ra ngoài Kafka cần cơ chế riêng.
- **"Auto commit nghĩa là at-least-once."** Chỉ khi xử lý xong trước lần poll kế. Xử lý bất đồng bộ cộng auto commit có thể thành at-most-once.
- **"Idempotent producer làm cả pipeline idempotent."** Nó chỉ khử trùng do retry của producer trong một phiên.
- **"Dùng transaction thì consumer tự nhiên không thấy dữ liệu bị abort."** Consumer phải đọc `read_committed`, và mức mặc định khác nhau giữa các client.

## Liên quan
- [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md): commit và committed offset.
- [06-idempotency-and-sinks.md](06-idempotency-and-sinks.md): làm sink chịu được trùng khi không dùng được transaction.
- [07-errors-retry-and-dlq.md](07-errors-retry-and-dlq.md): ghi sang retry topic hoặc DLQ cũng là một lần ghi phải được xác nhận trước khi commit.
- [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md): xử lý song song mà commit sai mốc gây mất dữ liệu.
