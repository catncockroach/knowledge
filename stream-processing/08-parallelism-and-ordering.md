# Song song và thứ tự

> Một engine có thể xử lý song song ở ba mức: **theo partition** (giữ thứ tự partition), **theo key** (giữ thứ tự từng key), hoặc **không thứ tự**. Ngoài ra Kafka có **share group**, nơi broker chia từng record cho nhiều consumer theo kiểu hàng đợi. Song song càng mịn thì throughput càng cao nhưng thứ tự càng yếu. Một khi các record trong cùng partition có thể xong lệch thứ tự, engine bắt buộc phải có **offset tracker**: chỉ commit tới mốc liên tục cao nhất mà mọi record trước đó đều đã xong.

## Tại sao cần biết
Số partition chặn trên số instance làm việc song song (xem [04-rebalancing-and-scaling.md](04-rebalancing-and-scaling.md)). Khi mỗi record tốn thời gian chờ I/O (gọi DB, gọi API), một luồng cho mỗi partition để CPU ngồi không phần lớn thời gian, và cách duy nhất để nhanh hơn mà không thêm partition là xử lý nhiều record của cùng partition cùng lúc. Việc này đụng ngay vào hai bất biến: thứ tự, và "committed offset là một con số". Lỗi kinh điển là commit offset của record *vừa xong* thay vì mốc an toàn, và nó gây mất dữ liệu khi crash.

## Khái niệm cốt lõi

### Bốn mô hình song song

| Mô hình | Là gì | Thứ tự giữ được | Song song tối đa | Phù hợp khi |
|---|---|---|---|---|
| Theo partition | Mỗi partition một luồng xử lý tuần tự | Theo partition | Bằng số partition được giao | Xử lý nhanh, CPU-bound, cần thứ tự chặt |
| Theo key | Băm key vào N worker cố định; mỗi worker xử lý tuần tự | Theo key | N worker, có thể lớn hơn nhiều so với số partition | Mỗi record tốn I/O, cần thứ tự theo thực thể |
| Không thứ tự | Mọi record vào một pool chung | Không | Tuỳ ý | Các việc độc lập: gửi thông báo, làm giàu dữ liệu |
| Share group | Broker giao từng record cho nhiều consumer cùng đọc một partition; consumer ack từng record; record không được ack thì được giao lại | Không | Nhiều consumer trên một partition | Hàng đợi công việc |

- **Dùng để**: chọn đúng mức song song theo yêu cầu thứ tự của bài toán. Ba mô hình đầu nằm trong ứng dụng; share group nằm ở broker và thay đổi chính ngữ nghĩa đọc (từ log sang hàng đợi).

### Offset tracker
- **Là gì**: bộ ghi nhận, cho mỗi partition, record nào đã được giao cho worker và record nào đã xong. Nó tính **mốc liên tục cao nhất** (low watermark): vị trí ngay sau đoạn dài nhất tính từ đầu mà mọi record đều đã xong. Chỉ mốc này được commit.
- **Dùng để**: giữ đúng nghĩa của committed offset ("mọi thứ trước vị trí này đã xong") khi record xong lệch thứ tự. Crash thì các record sau mốc được xử lý lại, kể cả những record đã xong, nên sink vẫn phải idempotent (xem [06-idempotency-and-sinks.md](06-idempotency-and-sinks.md)).
- Một số thư viện lưu thêm danh sách "đã xong sau mốc" vào metadata của commit (dung lượng giới hạn), để giảm lượng xử lý lại sau crash.

### Trần in-flight
- **Là gì**: giới hạn số record đã giao mà chưa xong, cho mỗi partition hoặc cho toàn instance.
- **Dùng để**: chặn khoảng chưa commit phình vô hạn khi một record kẹt (head-of-line blocking, xem [07-errors-retry-and-dlq.md](07-errors-retry-and-dlq.md)), và làm tín hiệu backpressure: chạm trần thì ngừng nhận record mới cho partition đó (xem [09-backpressure-and-throughput.md](09-backpressure-and-throughput.md)).

### Hot key
- **Là gì**: một key chiếm phần lớn traffic, ví dụ một khách hàng doanh nghiệp lớn, hoặc key rỗng mặc định.
- **Dùng để**: giải thích vì sao song song theo key có trần riêng. Mọi record của một key đi vào cùng một worker, nên worker đó thành nút cổ chai dù pool lớn đến đâu. Song song theo key tiến gần hiệu năng của không-thứ-tự khi số key lớn và phân bố đều, và kém đi rõ rệt khi có hot key.

### Fast lane / slow lane
- **Là gì**: tách record thành hai luồng (hai consumer group hoặc hai topic) theo thời gian xử lý dự kiến hoặc thực tế.
- **Dùng để**: khi thời gian xử lý rất không đều (từ mili-giây tới hàng phút), record chậm không làm chậm record nhanh.

## Cách hoạt động

### Vì sao commit "record vừa xong" gây mất dữ liệu

```
partition 3, ba record đang xử lý song song:   10   11   12
thời điểm t1: 10 xong, 12 xong, 11 còn chạy

commit "record vừa xong" (12)  → committed = 13  → crash → đọc lại từ 13 → record 11 MẤT
commit mốc liên tục             → committed = 11  → crash → đọc lại từ 11 → 11, 12 chạy lại (trùng, không mất)
```

### Offset tracker tối giản

Tracker giữ record theo *thứ tự đã giao*, không tính `offset + 1`, vì dãy offset có thể có lỗ do compaction và transaction marker (xem [02-kafka-log-model.md](02-kafka-log-model.md)).

```go
// Minh hoạ khái niệm, không gắn với client cụ thể. Một tracker cho mỗi partition.
type Record struct{ Partition int32; Offset int64; Key []byte }

type tracker struct {
    mu      sync.Mutex
    pending []*Record          // record đã giao cho worker, theo đúng thứ tự poll
    done    map[*Record]bool   // record đã xử lý xong
}

func (t *tracker) Dispatched(r *Record) { t.mu.Lock(); t.pending = append(t.pending, r); t.mu.Unlock() }
func (t *tracker) Finished(r *Record)   { t.mu.Lock(); t.done[r] = true; t.mu.Unlock() }
func (t *tracker) InFlight() int        { t.mu.Lock(); defer t.mu.Unlock(); return len(t.pending) }

// Advance bỏ khỏi đầu hàng mọi record đã xong liên tiếp, trả về record cuối của đoạn đó.
// Committed offset an toàn = offset của record trả về + 1. Trả về nil nếu đầu hàng chưa xong.
func (t *tracker) Advance() *Record {
    t.mu.Lock(); defer t.mu.Unlock()
    var last *Record
    for len(t.pending) > 0 && t.done[t.pending[0]] {
        last = t.pending[0]
        delete(t.done, last)
        t.pending = t.pending[1:]
    }
    return last
}
```

### Song song theo key

```go
// Minh hoạ: N worker, mỗi worker một channel có giới hạn. Cùng key luôn vào cùng worker.
for _, r := range batch {
    trackers[r.Partition].Dispatched(r)
    h := fnv.New32a()
    h.Write(r.Key)
    workers[h.Sum32()%uint32(len(workers))] <- r   // channel đầy thì vòng poll bị chặn: backpressure thô
}
// Worker: process(r); trackers[r.Partition].Finished(r)
// Vòng commit định kỳ: với mỗi partition, last := Advance(); nếu last != nil thì commit last.Offset+1
```

Cùng key luôn vào cùng worker và worker xử lý tuần tự, nên thứ tự theo key được giữ. Các key khác nhau chạy song song, kể cả khi nằm cùng partition.

## Ví dụ

Mỗi record gọi một API mất trung bình 50 ms; topic có 12 partition; engine chạy 3 instance:

| Mô hình | Song song | Throughput lý thuyết |
|---|---|---|
| Theo partition | 12 luồng (mỗi instance 4) | 12 × (1000 / 50) = 240 msg/s |
| Theo key, 64 worker mỗi instance | 192 luồng | ≈ 192 × 20 = 3.840 msg/s, nếu key đủ nhiều và phân bố đều |
| Theo key, có hot key chiếm 30% traffic | 192 luồng, nhưng 30% traffic dồn vào một worker | Worker đó chỉ chạy được 20 msg/s, nên toàn hệ thống bị chặn ở khoảng 20 / 0,3 ≈ 67 msg/s |

Dòng cuối cho thấy song song theo key không vượt được giới hạn của key nóng nhất. Hot key phải xử lý riêng: tách key, hoặc chấp nhận bỏ thứ tự cho key đó.

## Câu hỏi

**Có những cách nào xử lý song song trong một consumer, và chúng đánh đổi gì?**
> - **Theo partition**: một luồng mỗi partition.
> - **Theo key**: băm key vào worker cố định.
> - **Không thứ tự**: pool chung.
> - **Share group**: broker giao từng record cho nhiều consumer.
>
> Quy tắc: đơn vị song song càng mịn thì throughput càng cao và thứ tự càng yếu. Theo partition giữ thứ tự partition, nhưng song song bị chặn bởi số partition. Theo key giữ thứ tự từng key, nhưng bị chặn bởi key nóng nhất. Không thứ tự thì không giới hạn song song nhưng không giữ thứ tự nào. Bài toán quyết định đơn vị thứ tự tối thiểu cần giữ, và đơn vị đó là đơn vị song song mịn nhất được phép dùng.
>
> Ranh giới: từ mức theo key trở đi, record trong cùng partition xong lệch thứ tự, nên bắt buộc có offset tracker. Share group thì khác: broker theo dõi ack từng record, nên ứng dụng không cần tracker, nhưng cũng không có thứ tự.

**Offset tracker là gì, vì sao cần?**
> - **Committed offset**: một con số cho mỗi partition, nghĩa là "mọi record trước đây đã xong".
> - **Mốc liên tục cao nhất**: vị trí ngay sau đoạn dài nhất tính từ đầu mà mọi record đều đã xong.
>
> Quy tắc: một con số không diễn đạt được trạng thái "đã xong 10 và 12 nhưng chưa xong 11". Vì vậy khi record có thể xong lệch thứ tự, chỉ mốc liên tục cao nhất mới được commit. Offset tracker là bộ phận tính mốc đó. Commit bất kỳ vị trí nào cao hơn sẽ làm mất các record chưa xong nằm phía trước khi có crash.
>
> Ranh giới: tracker không loại bỏ được việc xử lý lại. Các record đã xong nằm *sau* mốc vẫn chạy lại sau crash, nên sink vẫn phải idempotent. Một record kẹt mãi làm mốc đứng yên, nên tracker luôn đi cùng trần in-flight và timeout theo từng record.

**Muốn xử lý nhanh hơn mà không tăng số partition thì làm thế nào?**
> - **Trần partition**: số instance làm việc song song tối đa bằng số partition.
> - **Song song bên trong instance**: nhiều luồng xử lý record của cùng partition.
>
> Quy tắc: số partition giới hạn song song *giữa các instance*, không giới hạn song song *bên trong một instance*. Khi việc xử lý chủ yếu là chờ I/O, tăng song song bên trong (theo key hoặc không thứ tự, cộng offset tracker) tăng throughput mà không cần thêm partition hay instance.
>
> Ranh giới: nếu việc xử lý là CPU-bound, song song bên trong instance bị chặn bởi số nhân CPU. Khi đó tăng thêm luồng không giúp gì, chỉ còn cách thêm instance, tức là cần thêm partition.

**Xử lý song song thì thứ tự còn được giữ không?**
> - **Thứ tự theo key**: mọi record cùng key được xử lý theo thứ tự log.
>
> Quy tắc: thứ tự giữ được tới đúng mức mà mô hình song song đảm bảo, không hơn. Song song theo key giữ thứ tự từng key vì mọi record cùng key đi qua một worker tuần tự. Pool không thứ tự thì không giữ được gì.
>
> Ranh giới: retry cũng phá thứ tự. Một worker theo key chuyển record lỗi sang retry topic rồi xử lý record tiếp theo của cùng key là đã đảo thứ tự. Giữ thứ tự theo key khi có lỗi đòi worker giữ record lỗi trong hàng của key đó, hoặc đưa mọi record sau của key đó theo đường retry (xem [07-errors-retry-and-dlq.md](07-errors-retry-and-dlq.md)).

**Share group khác consumer group ở đâu?**
> - **Consumer group**: mỗi partition thuộc một member; tiến độ là một offset mỗi partition.
> - **Share group**: nhiều consumer cùng đọc một partition; broker giao từng record và theo dõi ack từng record.
>
> Tiêu chí phân biệt là ngữ nghĩa *log* hay *hàng đợi*. Consumer group đọc log theo thứ tự, và ứng dụng tự quản lý tiến độ. Share group biến topic thành hàng đợi công việc: không có thứ tự, record không được ack trong thời hạn thì được giao lại cho consumer khác, và song song không bị chặn bởi số partition.
>
> Ranh giới: share group không thay được consumer group cho bài toán cần thứ tự, cần state theo partition, hay cần exactly-once qua transaction. Nó cũng là tính năng mới, đòi broker và client đều hỗ trợ.

## Hiểu nhầm thường gặp
- **"Song song theo key thì không giới hạn throughput."** Bị chặn bởi key nóng nhất.
- **"Commit offset của record vừa xong là được."** Chỉ đúng khi record xong theo thứ tự. Song song thì phải commit mốc liên tục.
- **"Có tracker thì không cần sink idempotent."** Record đã xong sau mốc vẫn chạy lại sau crash.
- **"Tính record kế tiếp bằng offset + 1."** Dãy offset có lỗ; tracker phải dựa trên thứ tự record client trả về.

## Liên quan
- [02-kafka-log-model.md](02-kafka-log-model.md): thứ tự trong partition và lỗ trong dãy offset.
- [04-rebalancing-and-scaling.md](04-rebalancing-and-scaling.md): trần partition khi scale giữa các instance.
- [07-errors-retry-and-dlq.md](07-errors-retry-and-dlq.md): head-of-line blocking và giữ thứ tự khi retry.
- [09-backpressure-and-throughput.md](09-backpressure-and-throughput.md): trần in-flight và pause partition.
