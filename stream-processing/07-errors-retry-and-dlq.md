# Lỗi, retry và dead letter queue

> Khi xử lý một record lỗi, engine phải chọn giữa **giữ thứ tự** (dừng lại chờ record đó) và **giữ tiến độ** (đẩy record lỗi sang đường khác và đi tiếp). Lựa chọn đúng phụ thuộc *loại lỗi* và *yêu cầu thứ tự*. Lỗi vĩnh viễn (poison message) đi thẳng vào **dead letter queue (DLQ)**. Lỗi tạm thời được **retry**: tại chỗ (chặn), qua **retry topic** (không chặn, mất thứ tự), hoặc bằng cách tạm dừng partition. Downstream sập toàn bộ thì cần **circuit breaker**.

## Tại sao cần biết
Một partition chỉ có một committed offset. Nếu record 1000 không xử lý được, engine không thể commit 1001 mà không coi 1000 là "đã xong". Retry tại chỗ mãi mãi thì cả partition đứng. Bỏ qua thì mất dữ liệu. Đẩy đi chỗ khác thì phá thứ tự. Không có lựa chọn nào đúng cho mọi bài toán, nên engine phải *phân loại* lỗi trước rồi mới chọn đường đi. File này mô tả các đường đi đó và đánh đổi của từng đường.

## Khái niệm cốt lõi

### Phân loại lỗi
| Loại | Là gì | Ví dụ | Retry có ích không |
|---|---|---|---|
| Poison message (lỗi vĩnh viễn) | Record mà xử lý bao nhiêu lần cũng lỗi | Không giải mã được, schema sai, vi phạm ràng buộc nghiệp vụ | Không |
| Lỗi tạm thời (transient) | Lỗi do môi trường, có thể tự hết | Timeout, 5xx, throttling, deadlock DB | Có |
| Lỗi hệ thống (downstream sập) | Mọi record đều lỗi vì nơi đích không dùng được | DB chết, API bên thứ ba sập | Có, nhưng không phải theo từng record |

- **Dùng để**: quyết định đường đi. Retry poison message là lãng phí và chặn tiến độ. Đẩy lỗi hệ thống vào DLQ thì DLQ đầy hàng loạt record hoàn toàn hợp lệ.

### Retry tại chỗ (in-place retry)
- **Là gì**: thử lại ngay trong luồng xử lý, vài lần, với khoảng chờ tăng dần (**exponential backoff**) cộng một phần ngẫu nhiên (**jitter**) để các instance không thử lại cùng một lúc.
- **Dùng để**: vượt qua lỗi tạm thời ngắn (vài trăm mili-giây đến vài giây) mà vẫn giữ thứ tự.
- **Rủi ro**: chờ trong vòng poll quá lâu thì member bị loại khỏi group (xem [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md)). Chờ lâu được thực hiện bằng cách tạm dừng fetch partition (pause) thay vì `sleep`.

### Retry topic
- **Là gì**: một hoặc nhiều topic phụ, mỗi topic có consumer riêng. Xử lý lỗi thì engine ghi record sang retry topic, coi record gốc là "đã xong" và commit tiếp. Consumer của retry topic xử lý lại sau một khoảng trễ. Nhiều tầng retry, mỗi tầng trễ dài hơn, gọi là *delayed processing queue*: record được xử lý *ít nhất* sau khoảng trễ đã cấu hình, có thể muộn hơn.
- **Dùng để**: không chặn luồng chính khi có lỗi tạm thời kéo dài.
- **Đánh đổi**: record lỗi tách khỏi luồng chính, nên **mất thứ tự** so với các record đến sau nó. Consumer phải idempotent, vì một record có thể đi qua nhiều tầng.

### Dead letter queue (DLQ)
- **Là gì**: topic chứa record không xử lý được, sau khi đã hết số lần retry hoặc khi lỗi là vĩnh viễn. Record vào DLQ kèm header mô tả: topic, partition, offset gốc, lý do lỗi, số lần đã thử, thời điểm.
- **Dùng để**: cô lập record hỏng để partition đi tiếp, giữ bằng chứng để điều tra, và cho phép **redrive** (đẩy lại vào luồng xử lý sau khi sửa lỗi).
- DLQ chỉ có giá trị khi đi kèm công cụ xem, xoá và redrive. Không có những công cụ đó thì nó chỉ là nơi dữ liệu mất đi một cách có trật tự.

### Stop on error
- **Là gì**: dừng xử lý partition (hoặc cả engine) khi gặp lỗi không vượt qua được, cho tới khi có người can thiệp.
- **Dùng để**: luồng mà thứ tự là tuyệt đối, như CDC, sổ cái, replication. Ở đó bỏ qua một record làm sai mọi thứ phía sau.
- **Đánh đổi**: mất *liveness*. Một poison message làm đứng cả partition.

### Giữ thứ tự theo key khi retry
- **Là gì**: khi một record của key K vào đường retry, engine nhớ "K đang có record chờ retry", và mọi record mới của K cũng đi theo đường retry, sau record đang chờ. Retry thành công thì xoá đánh dấu của K.
- **Dùng để**: vừa không chặn cả partition, vừa giữ thứ tự *theo key*. Cái giá là state phụ (tập key đang chờ) và logic định tuyến phức tạp hơn.
- Ví dụ vì sao thứ tự quan trọng: với tồn kho, xử lý "giảm 5" trước "tăng 10" của cùng một mặt hàng có thể làm tồn kho âm tạm thời và kích hoạt đặt hàng sai.

### Head-of-line (HOL) blocking
- **Là gì**: một record chậm hoặc kẹt ở đầu hàng làm mọi record sau nó không commit được, kể cả khi chúng đã xử lý xong.
- **Dùng để**: gọi tên vấn đề mà mọi engine xử lý song song đều gặp (xem [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md)). Cách xử lý chung là đặt **timeout theo từng record**: quá hạn thì đẩy record đó sang DLQ hoặc sang một *slow lane* (consumer group riêng cho việc chậm), rồi coi như đã xong.

### Circuit breaker
- **Là gì**: cơ chế đếm lỗi liên tiếp khi gọi downstream. Vượt ngưỡng thì "ngắt mạch": ngừng gọi một thời gian, rồi thử lại từng chút.
- **Dùng để**: khi downstream sập toàn bộ, tạm dừng consume (pause mọi partition) thay vì đẩy hàng loạt record hợp lệ vào retry hay DLQ. Lag tăng nhưng dữ liệu vẫn nằm an toàn trong log, chờ downstream hồi phục.

## Cách hoạt động

```
record ──► xử lý ──► OK ──────────────────────────────────────────► mark đã xong
              │
              └─ lỗi ──► phân loại
                          │
                          ├─ poison ─────────────────────────────► DLQ (kèm header) ──► mark đã xong
                          │
                          ├─ tạm thời ──► retry tại chỗ (backoff + jitter, vài lần)
                          │                 ├─ OK ──► mark đã xong
                          │                 └─ vẫn lỗi ──► theo yêu cầu thứ tự:
                          │                       ├─ thứ tự tuyệt đối ──► dừng partition, alert
                          │                       ├─ thứ tự theo key  ──► đường retry theo key
                          │                       └─ không cần thứ tự ──► retry topic tầng 1 → 2 → … → DLQ
                          │
                          └─ downstream sập ──► circuit breaker: pause consume, chờ hồi phục
```

"Mark đã xong" sau khi ghi sang DLQ hoặc retry topic chỉ được thực hiện khi broker đã xác nhận lần ghi đó. Nếu commit offset gốc trước và ghi DLQ thất bại, record bị mất (xem phần dual write ở [06-idempotency-and-sinks.md](06-idempotency-and-sinks.md)).

Trễ ở retry topic được thực hiện bằng cách đọc record, so thời điểm hiện tại với thời điểm được phép xử lý, và nếu chưa tới thì **pause riêng partition đó** cho tới hạn. Không dùng `sleep` cả luồng. Dừng cả consumer để chờ một partition thì các partition khác của retry topic cũng không chạy được.

## Ví dụ

Header của một record trong DLQ:

| Header | Giá trị |
|---|---|
| `dlq.original.topic` | `payments` |
| `dlq.original.partition` | `7` |
| `dlq.original.offset` | `1834120` |
| `dlq.error.class` | `poison` |
| `dlq.error.message` | `unknown schema id 4182` |
| `dlq.attempts` | `1` |
| `dlq.failed.at` | `2030-03-02T10:01:22Z` |

Từ ba header đầu có thể tìm lại đúng record gốc trong log. Sau khi đăng ký schema 4182, công cụ redrive đọc DLQ và đẩy các record có `error.class = poison` và lỗi này quay lại luồng xử lý.

## Câu hỏi

**Dead letter queue là gì, dùng để làm gì?**
> - **DLQ**: topic chứa record không xử lý được, kèm thông tin về record gốc và lỗi.
> - **Redrive**: đẩy record từ DLQ quay lại luồng xử lý.
>
> Quy tắc: DLQ tồn tại để một record hỏng không chặn cả partition (vì một partition chỉ có một committed offset) mà vẫn không mất record đó. Engine ghi record vào DLQ, chờ broker xác nhận, rồi coi record gốc là đã xong và đi tiếp. Record trong DLQ được giữ để điều tra và redrive.
>
> Ranh giới: DLQ không thay được retry. Record lỗi tạm thời vào thẳng DLQ là đẩy việc cho con người một cách không cần thiết. DLQ cũng phá thứ tự: khi redrive, record cũ quay lại *sau* các record mới hơn của cùng key.

**Retry tại chỗ và retry topic khác nhau ở đâu? Khi nào dùng cái nào?**
> - **Retry tại chỗ**: thử lại ngay trong luồng chính, chặn các record sau.
> - **Retry topic**: chuyển record lỗi sang topic khác để xử lý sau, không chặn luồng chính.
>
> Tiêu chí phân biệt là *thứ tự hay tiến độ quan trọng hơn*. Retry tại chỗ giữ thứ tự nhưng chặn partition trong lúc chờ, nên hợp với lỗi ngắn. Retry topic giữ tiến độ nhưng record lỗi sẽ được xử lý sau các record đến sau nó, nên chỉ hợp khi không cần thứ tự giữa các record.
>
> Ranh giới: hai cách thường được ghép. Retry tại chỗ vài lần cho lỗi rất ngắn, rồi mới chuyển sang retry topic hoặc DLQ. Nếu cần thứ tự theo key mà vẫn không muốn chặn cả partition, cần đường retry theo key: mọi record mới của key đang lỗi cũng đi theo đường retry.

**Yêu cầu thứ tự ảnh hưởng tới cách xử lý lỗi thế nào?**
> - **Thứ tự tuyệt đối theo partition**: mọi record phải áp dụng đúng thứ tự log.
> - **Thứ tự theo key**: chỉ record cùng key mới phải đúng thứ tự.
> - **Liveness**: hệ thống tiếp tục tiến được.
>
> Quy tắc: thứ tự càng chặt thì càng ít đường thoát khi gặp lỗi. Thứ tự tuyệt đối thì chỉ còn chặn và chờ (stop on error, retry vô hạn kèm alert), tức hy sinh liveness. Thứ tự theo key thì chặn được ở mức key: tách key đang lỗi, các key khác đi tiếp. Không cần thứ tự thì dùng được retry topic và DLQ tự do.
>
> Ranh giới: "thứ tự theo key" chỉ có nghĩa khi producer đã đặt key đúng (định danh thực thể). Key ngẫu nhiên hoặc rỗng thì không có thứ tự theo key nào để giữ.

**Vì sao không nên đẩy record vào DLQ khi database đích bị sập?**
> - **Lỗi hệ thống**: mọi record đều lỗi vì nơi đích không dùng được.
> - **Circuit breaker**: ngừng gọi downstream khi lỗi liên tiếp vượt ngưỡng.
>
> Quy tắc: DLQ dành cho record *có vấn đề*, không dành cho *môi trường có vấn đề*. Khi downstream sập, mọi record đều hợp lệ. Đẩy chúng vào DLQ biến một sự cố ngắn thành một đợt redrive lớn, và phá thứ tự của toàn bộ dữ liệu trong thời gian sự cố. Cách đúng là tạm dừng consume: dữ liệu vẫn nằm trong log, lag tăng, và engine đi tiếp từ đúng chỗ khi downstream hồi phục.
>
> Ranh giới: tạm dừng lâu hơn retention của topic thì dữ liệu bắt đầu bị xoá trước khi kịp xử lý. Lag theo thời gian so với retention là chỉ số cho biết còn bao nhiêu thời gian.

**Head-of-line blocking là gì, xử lý thế nào?**
> - **HOL blocking**: một record kẹt ở đầu làm các record sau không commit được.
>
> Quy tắc: vì committed offset là một mốc liên tục, record chưa xong nhỏ nhất của một partition quyết định mốc commit, bất kể bao nhiêu record sau nó đã xong. Một record kẹt vô hạn thì mốc commit đứng yên vô hạn. Cách xử lý chung là timeout theo từng record: quá hạn thì record đó được chuyển sang DLQ hoặc slow lane và coi như đã xong, để mốc commit tiến tiếp.
>
> Ranh giới: phát hiện "partition kẹt" bằng điều kiện "số record đang xử lý luôn khác 0" sẽ báo sai dưới tải liên tục, vì lúc nào cũng có record đang chạy. Điều kiện đúng là *tuổi* của record chưa xong cũ nhất vượt ngưỡng.

## Hiểu nhầm thường gặp
- **"Retry vài lần rồi vào DLQ là đủ cho mọi lỗi."** Lỗi hệ thống cần circuit breaker; lỗi vĩnh viễn không cần retry.
- **"Retry topic giữ thứ tự."** Retry topic tách record khỏi luồng chính, nên thứ tự với các record sau bị mất.
- **"Chờ retry bằng `sleep` trong consumer là được."** Chờ quá lâu thì member bị loại khỏi group; chờ cả luồng thì mọi partition khác cũng đứng.
- **"Ghi vào DLQ là xong."** Chỉ xong khi broker xác nhận lần ghi trước lúc commit offset gốc. Không thì record mất.

## Liên quan
- [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md): poll interval tối đa và việc bị loại khỏi group.
- [06-idempotency-and-sinks.md](06-idempotency-and-sinks.md): ghi DLQ rồi commit là một dual write.
- [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md): offset tracker và head-of-line blocking khi xử lý song song.
- [09-backpressure-and-throughput.md](09-backpressure-and-throughput.md): pause/resume partition.
