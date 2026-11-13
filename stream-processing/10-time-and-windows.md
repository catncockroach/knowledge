# Thời gian và window

> Một event có ít nhất hai thời điểm: lúc nó **xảy ra** (event time) và lúc engine **thấy** nó (processing time). Hai thời điểm này lệch nhau một khoảng không cố định, nên event đến lệch thứ tự. **Window** gom event theo khoảng thời gian. Muốn window theo event time, engine cần một "đồng hồ dữ liệu" (**stream-time** hoặc **watermark**) để biết khi nào một khoảng đã đủ dữ liệu, cộng một **grace period** để chờ event trễ. Event đến sau grace là **late data** và phải có cách xử lý riêng.

## Tại sao cần biết
"Số đơn hàng mỗi phút" nghe đơn giản, nhưng phút nào? Một đơn đặt lúc 10:00:58 trên điện thoại mất mạng, tới Kafka lúc 10:01:20, thuộc phút 10:00 hay 10:01? Khi nào thì được phép công bố con số của phút 10:00, nếu vẫn có thể còn đơn trễ đang trên đường? Mọi bài toán đếm, tổng, phát hiện chuỗi hành vi theo thời gian đều phải trả lời những câu này. Đây cũng là phần khó tự viết nhất trong một engine, và là lý do chính để chọn một framework stream (xem [14-engine-architecture-and-frameworks.md](14-engine-architecture-and-frameworks.md)).

## Khái niệm cốt lõi

### Ba loại thời gian
| Loại | Là gì | Dùng để |
|---|---|---|
| Event time | Thời điểm sự việc thật sự xảy ra, thường ghi trong payload | Trả lời câu hỏi về thế giới thật ("bao nhiêu đơn đặt trong phút 10:00") |
| Ingestion time | Thời điểm event vào hệ thống, ví dụ timestamp `LogAppendTime` do broker ghi | Một mốc ổn định, do hệ thống tự gán, khi nguồn không ghi event time |
| Processing time | Thời điểm engine xử lý event, tức đồng hồ của máy chạy engine | Đo hoạt động của chính hệ thống ("engine xử lý bao nhiêu record mỗi phút") |

- **Độ lệch giữa event time và processing time** không cố định: lúc vài mili-giây, lúc vài phút (mất mạng, hàng đợi ứ, replay dữ liệu cũ). Vì vậy window theo processing time sẽ xếp một phần event vào sai khoảng, và kết quả thay đổi mỗi lần chạy lại.

### Out-of-order data
- **Là gì**: event đến engine không theo thứ tự event time. Event của 10:00:58 có thể đến sau event của 10:01:05.
- **Dùng để**: gọi tên hệ quả tất yếu của độ lệch trên. Thứ tự trong partition là thứ tự *ghi*, không phải thứ tự *xảy ra*.

### Stream-time
- **Là gì**: đồng hồ do dữ liệu dẫn dắt. Nó bằng event time lớn nhất đã thấy (thường tính theo partition hoặc theo task), và chỉ tiến khi có record mới.
- **Dùng để**: quyết định window nào đã đóng mà không phụ thuộc đồng hồ máy. Chạy lại cùng dữ liệu sẽ cho cùng kết quả.
- **Hạn chế**: partition thưa event thì stream-time đứng yên, và window không đóng cho tới khi có event mới. Kết quả cần ra đúng giờ thì phải có thêm timer theo đồng hồ thật, với đánh đổi về độ đúng.

### Watermark
- **Là gì**: một khẳng định đi kèm dòng dữ liệu: "event time đã đạt tới t", tức (theo ước tính) sẽ không còn event nào có event time ≤ t. Một cách tính phổ biến: watermark = event time lớn nhất đã thấy trừ độ trễ cho phép.
- **Dùng để**: cho các operator biết khi nào được đóng window và phát kết quả.
- *Perfect watermark* (biết chắc không còn event trễ) chỉ có khi biết hết nguồn. Thực tế dùng *heuristic watermark*, có lúc sai, nên vẫn có late data.
- Với operator nhận dữ liệu từ nhiều partition hoặc nhiều nguồn, watermark của nó là **giá trị nhỏ nhất** trong các input. Một input không có dữ liệu (idle) giữ watermark đứng yên, nên phải được đánh dấu idle để không chặn cả operator.

### Grace period và allowed lateness
- **Là gì**: khoảng thời gian, tính bằng event time hoặc stream-time, mà window vẫn nhận event sau khi đã qua mốc kết thúc của nó. Window `[10:00, 10:01)` với grace 30 giây chỉ thật sự đóng khi stream-time đạt 10:01:30.
- **Dùng để**: đánh đổi giữa *độ đúng* (chờ lâu thì đón được nhiều event trễ) và *độ trễ của kết quả* (chờ lâu thì kết quả ra chậm) cùng *lượng state* (window mở lâu thì giữ nhiều state).

### Late data
- **Là gì**: event đến sau khi window của nó đã đóng (quá grace).
- **Dùng để**: gọi tên phần dữ liệu engine phải có chính sách riêng. Có ba lựa chọn: bỏ (và đếm bằng metric), đẩy ra một luồng riêng (side output, topic "late") để xử lý hoặc đối soát sau, hoặc phát một bản sửa cho kết quả đã công bố.

### Bốn loại window

| Window | Là gì | Một event thuộc mấy window | Ví dụ bài toán |
|---|---|---|---|
| Tumbling | Kích thước cố định, nối tiếp nhau, không chồng lấn | Đúng 1 | Số đơn hàng mỗi 5 phút |
| Hopping | Kích thước cố định, bước nhảy nhỏ hơn kích thước, chồng lấn | Kích thước / bước nhảy | Trung bình 5 phút gần nhất, cập nhật mỗi phút (mỗi event thuộc 5 window) |
| Sliding (nghĩa của Kafka Streams) | Hai event chung window nếu event time cách nhau không quá kích thước; window căn theo event, không theo mốc cố định | Phụ thuộc dữ liệu | Hai giao dịch của cùng thẻ cách nhau ≤ 10 giây |
| Session | Các đoạn hoạt động ngăn cách bởi khoảng nghỉ (inactivity gap); kích thước thay đổi theo dữ liệu, tính riêng cho từng key | Đúng 1, nhưng window có thể gộp lại | Phiên duyệt web, kết thúc khi im lặng 30 phút |

- **Lưu ý thuật ngữ**: trong mô hình Dataflow và trong Flink, "sliding window" là window có kích thước và chu kỳ cố định, tức chính là *hopping* của Kafka Streams. Khi đọc tài liệu cần xác định đang dùng thuật ngữ của hệ nào.
- Window luôn tính *theo key*. Window không theo key thì mọi event dồn vào một chỗ, song song chỉ còn 1.
- Session window khó nhất: một event trễ rơi vào khoảng nghỉ giữa hai session có thể **gộp** hai session thành một, nên engine phải xoá hai kết quả cũ và tạo một kết quả mới.

### Phát kết quả: liên tục hay khi window đóng
- **Phát liên tục**: mỗi event cập nhật window thì phát một bản kết quả mới. Kết quả có sớm, nhưng sink phải hiểu "bản sau ghi đè bản trước" (upsert theo khoá window).
- **Phát khi đóng**: chỉ phát một lần khi window đóng (qua grace). Mỗi window có đúng một kết quả, nhưng độ trễ bằng kích thước window cộng grace.
- Mô hình Dataflow gói các lựa chọn này vào bốn câu hỏi: *what* (tính gì), *where* (window nào), *when* (khi nào phát, theo watermark và trigger), *how* (các bản kết quả liên tiếp liên hệ với nhau thế nào: thay thế, cộng dồn, hay rút lại bản cũ).

## Cách hoạt động

Đếm click mỗi phút, tumbling 1 phút, grace 30 giây, theo stream-time:

```
event (event time)        đến lúc (stream-time trước → sau)   window       hành động
click A 10:00:20          10:00:20                             [10:00,10:01) +1
click B 10:00:58 (trễ)    sau C: stream-time = 10:01:20        [10:00,10:01) +1 (chưa quá 10:01:30)
click C 10:01:20          10:01:20                             [10:01,10:02) +1
click D 10:01:35          10:01:35                             [10:01,10:02) +1
                          stream-time ≥ 10:01:30 ⇒ đóng [10:00,10:01), phát count = 2
click E 10:00:45 (rất trễ) stream-time = 10:01:35              [10:00,10:01) đã đóng ⇒ late data
```

Một bản cài đặt tối giản tumbling window theo stream-time, state trong RAM:

```go
// Minh hoạ khái niệm. Một windowAgg cho mỗi partition. State trong RAM nên crash là mất
// (xem 11-state-and-joins.md về lưu và phục hồi state).
type windowAgg struct {
    size, grace time.Duration
    streamTime  time.Time                      // event time lớn nhất đã thấy
    open        map[time.Time]map[string]int64 // windowStart → key → count
}

func (w *windowAgg) Add(key string, ts time.Time) (late bool) {
    if ts.After(w.streamTime) {
        w.streamTime = ts
    }
    start := ts.Truncate(w.size)
    if !w.streamTime.Before(start.Add(w.size + w.grace)) {
        return true // window đã đóng: late data
    }
    if w.open[start] == nil {
        w.open[start] = map[string]int64{}
    }
    w.open[start][key]++
    return false
}

func (w *windowAgg) CloseReady(emit func(start time.Time, counts map[string]int64)) {
    for start, counts := range w.open {
        if !w.streamTime.Before(start.Add(w.size + w.grace)) {
            emit(start, counts)
            delete(w.open, start)
        }
    }
}
```

## Ví dụ

Cùng một dòng click, ba cách đếm "click mỗi phút" cho phút 10:00:

| Cách | Kết quả cho [10:00, 10:01) | Vấn đề |
|---|---|---|
| Processing time | Chỉ A | B (xảy ra 10:00:58, đến 10:01:20) bị đếm vào phút 10:01; chạy lại sẽ ra kết quả khác |
| Event time, grace 0 | Chỉ A | Window đóng ngay khi stream-time qua 10:01, nên B thành late data |
| Event time, grace 30 s | A, B | Kết quả ra lúc stream-time đạt 10:01:30; E (đến khi stream-time 10:01:35) vẫn là late data |

Không có cấu hình nào đón được *mọi* event trễ mà vẫn ra kết quả. Chọn grace là chọn chấp nhận bao nhiêu late data để đổi lấy kết quả nhanh hơn bao nhiêu, và kích thước của late data đo được qua metric.

## Câu hỏi

**Event time và processing time khác nhau thế nào, khi nào dùng loại nào?**
> - **Event time**: lúc sự việc xảy ra.
> - **Processing time**: lúc engine xử lý event.
>
> Tiêu chí: câu hỏi về *thế giới thật* (bao nhiêu đơn đặt, bao nhiêu lần đăng nhập trong khoảng nào) cần event time. Câu hỏi về *chính hệ thống* (engine xử lý nhanh tới đâu, hàng đợi dài bao nhiêu) dùng processing time. Event time cho kết quả tất định khi chạy lại; processing time thì không, vì đồng hồ lúc chạy lại đã khác.
>
> Ranh giới: event time chỉ tốt bằng đồng hồ của nguồn. Thiết bị có đồng hồ sai đưa event vào sai window, và broker có thể từ chối record có timestamp lệch quá xa. Vì vậy event time thường được lấy từ payload, kèm kiểm tra hợp lệ.

**Watermark là gì, và stream-time khác watermark ở đâu?**
> - **Stream-time**: event time lớn nhất đã thấy, tiến theo dữ liệu.
> - **Watermark**: khẳng định "event time đã đạt t, không còn (hoặc gần như không còn) event nào ≤ t".
>
> Quy tắc: cả hai đều là "đồng hồ dữ liệu" để quyết định khi nào đóng window, và đều tiến theo dữ liệu chứ không theo đồng hồ máy. Khác biệt nằm ở chỗ gộp nhiều input. Stream-time thường tính theo một partition và lấy giá trị lớn nhất. Watermark được truyền qua các operator, và khi một operator nhận nhiều input thì lấy giá trị *nhỏ nhất*, để không đóng window khi một input còn chậm.
>
> Ranh giới: lấy nhỏ nhất nghĩa là một input không có dữ liệu sẽ giữ watermark đứng yên vô hạn. Input idle phải được phát hiện và loại khỏi phép tính, nếu không window không bao giờ đóng.

**Grace period nên đặt bao nhiêu? Event đến quá grace thì sao?**
> - **Grace period**: thời gian window còn nhận event sau mốc kết thúc.
> - **Late data**: event đến sau khi window đã đóng.
>
> Quy tắc: grace là đánh đổi ba chiều. Grace dài thì đón được nhiều event trễ hơn, nhưng kết quả ra chậm hơn và nhiều window mở cùng lúc hơn (nhiều state hơn). Mức hợp lý chỉ biết được bằng cách đo phân bố độ trễ (processing time − event time) trên dữ liệu thật, rồi chọn mức phủ phần lớn phân bố đó. Event quá grace không được tính vào window, và cần một chính sách tường minh: bỏ có đếm, đẩy ra luồng late, hoặc phát bản sửa.
>
> Ranh giới: bỏ late data một cách âm thầm làm không biết grace đang đặt sai. Metric đếm late data là cách duy nhất để thấy điều đó.

**Tumbling, hopping, sliding và session window khác nhau thế nào?**
> - **Tumbling**: kích thước cố định, không chồng lấn.
> - **Hopping**: kích thước cố định, chồng lấn theo bước nhảy.
> - **Sliding** (Kafka Streams): căn theo event, nhóm event cách nhau không quá kích thước.
> - **Session**: kích thước theo dữ liệu, ngăn cách bằng khoảng nghỉ.
>
> Tiêu chí: câu hỏi "trong mỗi khoảng cố định" dùng tumbling. "Trong N phút gần nhất, cập nhật đều đặn" dùng hopping. "Hai sự kiện cách nhau không quá X" dùng sliding hoặc join có window. "Một đợt hoạt động liên tục" dùng session. Chi phí tăng theo thứ tự: hopping nhân state và số lần ghi theo tỉ lệ kích thước/bước nhảy; session phải xử lý việc gộp window khi có event trễ.
>
> Ranh giới: tên gọi không thống nhất giữa các hệ. "Sliding" của Dataflow và Flink là "hopping" của Kafka Streams.

**Nên phát kết quả window liên tục hay chỉ khi window đóng?**
> - **Phát liên tục**: mỗi cập nhật phát một bản kết quả mới.
> - **Phát khi đóng**: một kết quả duy nhất khi window qua grace.
>
> Quy tắc: lựa chọn phụ thuộc vào việc sink và người dùng xử lý được kết quả tạm hay không. Dashboard và sink chịu upsert theo khoá window thì phát liên tục, cho kết quả nhanh. Sink chỉ nhận một bản cuối (gửi cảnh báo, ghi sổ, tính tiền) thì phát khi đóng, chấp nhận độ trễ bằng kích thước window cộng grace.
>
> Ranh giới: phát khi đóng không loại bỏ late data. Event quá grace vẫn có thể đến, và hoặc bị bỏ, hoặc phải phát thêm một bản sửa.

## Hiểu nhầm thường gặp
- **"Thứ tự trong partition là thứ tự xảy ra."** Đó là thứ tự ghi. Event có thể được ghi muộn hơn nhiều so với lúc xảy ra.
- **"Window theo đồng hồ máy là đủ."** Kết quả phụ thuộc lúc chạy, không lặp lại được khi replay.
- **"Watermark đảm bảo không còn event trễ."** Watermark thực tế là heuristic; late data vẫn có.
- **"Grace càng lớn càng tốt."** Grace lớn làm kết quả chậm và state lớn.

## Liên quan
- [02-kafka-log-model.md](02-kafka-log-model.md): timestamp của record (`CreateTime`, `LogAppendTime`).
- [11-state-and-joins.md](11-state-and-joins.md): window là state; lưu, phục hồi và join có window.
- [13-observability-and-operations.md](13-observability-and-operations.md): replay và vì sao logic dùng event time chứ không dùng đồng hồ máy.
- [14-engine-architecture-and-frameworks.md](14-engine-architecture-and-frameworks.md): khi nào window event-time là lý do chọn framework.
