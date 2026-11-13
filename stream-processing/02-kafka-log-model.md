# Mô hình log của Kafka

> Kafka lưu event trong các **log chỉ ghi nối thêm**. Mỗi topic chia thành nhiều **partition**, mỗi partition là một log riêng. Mỗi record trong partition có một số thứ tự gọi là **offset**. Thứ tự chỉ được đảm bảo *trong một partition*, và key của record quyết định nó rơi vào partition nào.

## Tại sao cần biết
Mọi quyết định thiết kế phía consumer đều quy về mô hình này: song song được bao nhiêu, thứ tự giữ được theo cái gì, phục hồi từ đâu, state đặt ở đâu. Nhiều lỗi khó tìm (mất thứ tự sau khi tăng partition, join sai do lệch hàm băm, khoảng trống trong dãy offset) chỉ hiểu được khi nắm rõ cách Kafka đặt và đánh số record. File này chỉ mô tả log từ góc nhìn người viết consumer. Phần vận hành broker nằm ngoài phạm vi.

## Khái niệm cốt lõi

### Topic
- **Là gì**: một tên logic cho một dòng event cùng loại, ví dụ `orders`, `clicks`.
- **Dùng để**: phân loại dữ liệu. Producer ghi vào topic, consumer đăng ký đọc topic. Mỗi topic có cấu hình riêng về số partition, retention và compaction.

### Partition
- **Là gì**: một phần của topic. Mỗi partition là một log có thứ tự, chỉ ghi nối vào cuối, và nằm trên một broker leader cùng các bản sao.
- **Dùng để**: vừa là **đơn vị thứ tự** (record trong một partition giữ đúng thứ tự ghi), vừa là **đơn vị song song** (các partition được đọc độc lập, bởi các consumer khác nhau). Số partition là trần của số consumer xử lý song song trong một group (xem [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md)).

### Record (message)
- **Là gì**: một event được lưu trong partition, gồm:

  | Thành phần | Là gì | Dùng để |
  |---|---|---|
  | Key | Mảng byte, có thể rỗng | Chọn partition; gom mọi event của cùng một thực thể (user, đơn hàng) vào cùng partition; khoá cho compaction |
  | Value | Mảng byte, nội dung event | Dữ liệu nghiệp vụ. Kafka không hiểu nội dung, việc giải mã là của consumer (xem [12-schema-and-serialization.md](12-schema-and-serialization.md)) |
  | Headers | Danh sách cặp tên–giá trị byte | Metadata đi kèm mà không chạm vào value: trace context, schema ID, lý do vào DLQ |
  | Timestamp | Mili-giây epoch | Thời điểm producer tạo record (`CreateTime`) hoặc lúc broker ghi (`LogAppendTime`), tuỳ cấu hình topic |
  | Offset | Số nguyên 64 bit do broker gán | Vị trí của record trong partition |

### Offset
- **Là gì**: số thứ tự tăng dần, do broker gán cho mỗi record khi ghi vào một partition. Offset chỉ có nghĩa trong một partition: offset 100 của partition 0 và offset 100 của partition 1 không liên quan gì đến nhau.
- **Dùng để**: định vị record. Bộ ba (topic, partition, offset) xác định duy nhất một record. Consumer lưu offset để biết đọc tiếp từ đâu, và bộ ba này cũng là "toạ độ" để replay hay truy vết một message.
- **Lưu ý**: offset tăng dần nhưng **không nhất thiết liên tục**. Compaction xoá record cũ, và transaction marker chiếm offset mà không trả về cho ứng dụng, nên dãy offset ứng dụng nhìn thấy có thể có lỗ (xem [05-delivery-semantics.md](05-delivery-semantics.md)).

### Các mốc offset của một partition
- **Log start offset**: offset nhỏ nhất còn được giữ. Nó tăng dần khi dữ liệu cũ bị xoá theo retention.
- **Log end offset (LEO)**: offset sẽ được gán cho record *kế tiếp*, tức bằng offset cuối cộng 1.
- **High watermark**: offset tới đó mọi bản sao đồng bộ đã có dữ liệu. Consumer chỉ đọc được tới mốc này, nhờ vậy không đọc phải dữ liệu có thể mất khi leader đổi.
- **Dùng để**: tính lag (khoảng cách giữa log end và vị trí consumer, xem [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md)), và biết offset đã lưu còn hợp lệ không. Offset đã commit nhỏ hơn log start offset nghĩa là dữ liệu đã bị xoá trước khi kịp đọc.

### Partitioner
- **Là gì**: hàm phía producer chọn partition cho record. Record có key thì partition = hash(key) mod số partition. Record không có key thì producer tự rải đều, thường theo kiểu "dính" một partition cho một batch rồi chuyển sang partition khác.
- **Dùng để**: đảm bảo mọi record cùng key vào cùng partition, nên giữ được thứ tự theo key và đặt được state theo key cục bộ.
- **Lưu ý**: hàm băm phải giống nhau ở mọi producer cùng ghi vào một topic. Client Java dùng murmur2; một số client khác mặc định dùng hàm khác (fnv, crc32). Trộn hai loại producer sẽ đưa cùng một key vào hai partition khác nhau mà không ai báo lỗi.

### Retention
- **Là gì**: chính sách xoá dữ liệu cũ theo thời gian (giữ 7 ngày) hoặc theo dung lượng.
- **Dùng để**: giới hạn ổ đĩa, đồng thời quyết định *cửa sổ replay*: chỉ đọc lại được những gì còn trong retention. Consumer dừng lâu hơn retention sẽ mất dữ liệu chưa đọc.

### Log compaction
- **Là gì**: chính sách dọn dẹp giữ lại *ít nhất record mới nhất của mỗi key* và xoá các bản cũ hơn của cùng key. Record có value rỗng (**tombstone**) nghĩa là "xoá key này", và chính tombstone cũng bị dọn sau một thời gian.
- **Dùng để**: biến topic thành một bảng (stream-table duality, xem [01-stream-processing-fundamentals.md](01-stream-processing-fundamentals.md)). Đọc topic compacted từ đầu sẽ được trạng thái mới nhất của mọi key, nên đây là cách lưu changelog của state store và các bảng tra cứu (xem [11-state-and-joins.md](11-state-and-joins.md)).

### Replication
- **Là gì**: mỗi partition có một leader và các follower sao chép dữ liệu. Tập bản sao đang theo kịp leader gọi là ISR (in-sync replicas).
- **Dùng để**: chịu lỗi broker. Từ phía consumer chỉ cần biết hai điều: record chỉ đọc được khi đã nằm dưới high watermark, và producer chọn mức xác nhận `acks` (chờ leader, hay chờ mọi bản sao đồng bộ) để đánh đổi giữa độ bền và độ trễ.

## Cách hoạt động

Topic `orders` có 3 partition, key là `user_id`:

```
producer: hash("u1") mod 3 = 0   hash("u2") mod 3 = 2   hash("u7") mod 3 = 0

partition 0:  [0:u1 tạo] [1:u7 tạo] [2:u1 thanh toán] [3:u1 huỷ] ...  ─► ghi nối vào cuối
partition 1:  [0:u5 tạo] [1:u9 tạo] ...
partition 2:  [0:u2 tạo] [1:u2 thanh toán] ...
               ▲                                   ▲            ▲
          log start offset                  high watermark   log end offset
```

- Mọi event của `u1` nằm ở partition 0, theo đúng thứ tự tạo → thanh toán → huỷ.
- Không có thứ tự nào giữa `u1` (partition 0) và `u2` (partition 2). Consumer có thể xử lý `u2 thanh toán` trước `u1 tạo`.
- Consumer đọc partition 0 lưu "đã xử lý tới offset 2", nên lần sau đọc từ offset 3.

Nếu tăng topic lên 4 partition, `hash("u1") mod 4` có thể ra một partition khác. Từ đó event mới của `u1` vào partition mới, trong khi event cũ vẫn nằm ở partition 0. Hai partition đọc độc lập, nên thứ tự của `u1` không còn được đảm bảo ở giai đoạn chuyển tiếp.

## Ví dụ

Topic compacted `user-profile`, key là `user_id`:

```
trước compaction:  [0: u1 → {city: HN}] [1: u2 → {city: SG}] [2: u1 → {city: DN}] [3: u2 → null]
sau compaction:    [2: u1 → {city: DN}] [3: u2 → null]       (tombstone của u2 bị dọn sau một thời gian)
```

Consumer mới đọc từ đầu nhận được trạng thái "u1 ở Đà Nẵng, u2 đã bị xoá". Offset 0 và 1 không còn nữa, nên dãy offset nó thấy bắt đầu từ 2.

## Câu hỏi

**Partition là gì, và vì sao Kafka chia topic thành nhiều partition?**
> - **Topic**: tên logic của một dòng event.
> - **Partition**: một log có thứ tự là một phần của topic.
>
> Quy tắc: partition vừa là đơn vị thứ tự, vừa là đơn vị song song. Thiết kế này đánh đổi thứ tự toàn cục lấy khả năng scale. Một log duy nhất giữ được thứ tự tuyệt đối nhưng chỉ một máy ghi và một consumer đọc được. Chia thành N partition cho phép N máy cùng ghi và N consumer cùng đọc, đổi lại thứ tự chỉ còn trong từng partition.
>
> Ranh giới: muốn giữ thứ tự cho một thực thể thì đặt key là định danh thực thể đó. Mọi event của nó vào cùng partition, nên "thứ tự theo key" là mức thứ tự thực tế mà Kafka cho được.

**Một topic có thể có bao nhiêu partition, và đổi số partition về sau có sao không?**
> - **Partitioner**: hàm `hash(key) mod N` chọn partition.
>
> Quy tắc: một topic có từ 1 tới rất nhiều partition. Số partition tăng được nhưng không giảm được. Tăng N làm thay đổi kết quả `hash(key) mod N`, nên key cũ có thể chuyển sang partition mới. Hệ quả: (1) thứ tự theo key bị phá trong giai đoạn chuyển tiếp; (2) state đặt theo partition (xem [11-state-and-joins.md](11-state-and-joins.md)) không còn khớp với dữ liệu; (3) hai topic dùng để join không còn cùng số partition.
>
> Ranh giới: topic không có key (rải đều) thì tăng partition không gây vấn đề thứ tự, vì vốn không có thứ tự theo key để giữ. Vì vậy với topic có key, số partition là quyết định được tính cho mức scale tối đa ngay từ đầu.

**Kafka đảm bảo thứ tự ở mức nào?**
> - **Thứ tự**: consumer nhận record đúng theo thứ tự chúng được ghi.
>
> Quy tắc: Kafka đảm bảo thứ tự *trong một partition* và không đảm bảo gì giữa các partition. Với producer, thứ tự ghi trong một partition được giữ, kể cả khi retry, nếu bật idempotent producer (xem [05-delivery-semantics.md](05-delivery-semantics.md)). Không bật thì retry có thể đảo thứ tự hai batch.
>
> Ranh giới: thứ tự lưu trong log không có nghĩa là thứ tự xử lý. Nếu consumer xử lý song song các record của cùng một partition thì nó tự phá thứ tự đó, và phải chủ động giữ lại theo key nếu cần (xem [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md)).

**Offset là gì? Offset có luôn liên tục không?**
> - **Offset**: số thứ tự broker gán cho record trong một partition.
>
> Quy tắc: offset tăng dần trong một partition và là vị trí duy nhất của record trong partition đó. Nó không nhất thiết liên tục: compaction xoá record cũ, transaction marker chiếm offset mà không trả về cho ứng dụng. Vì vậy code consumer không được giả định "record kế tiếp là offset + 1". Nó chỉ được dựa vào thứ tự record mà client trả về.
>
> Ranh giới: committed offset theo quy ước là offset của record *kế tiếp* cần đọc, tức bằng offset đã xử lý cộng 1. Đây là quy ước về vị trí, không phải giả định rằng record kế tiếp thật sự có offset đó (xem [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md)).

**Retention và compaction khác nhau thế nào? Khi nào dùng loại nào?**
> - **Retention**: xoá theo thời gian hoặc dung lượng, bất kể key.
> - **Compaction**: giữ bản mới nhất của mỗi key, xoá các bản cũ hơn.
>
> Tiêu chí phân biệt: topic là *dòng sự kiện* (mỗi event có giá trị riêng, ví dụ các click) thì dùng retention. Topic là *trạng thái của thực thể* (chỉ bản mới nhất có ý nghĩa, ví dụ hồ sơ user, changelog của state store) thì dùng compaction. Một topic có thể bật cả hai: vừa compact, vừa xoá key quá cũ.
>
> Ranh giới: compaction không chạy tức thì, nên đọc topic compacted vẫn có thể gặp nhiều bản của cùng một key. Consumer phải coi bản sau ghi đè bản trước, không được giả định mỗi key xuất hiện một lần.

**Timestamp của record là thời điểm nào?**
> - **CreateTime**: thời điểm producer đặt khi tạo record.
> - **LogAppendTime**: thời điểm broker ghi record vào log, ghi đè giá trị của producer.
>
> Quy tắc: timestamp của record mang nghĩa nào là do cấu hình topic quyết định. Với `CreateTime`, nó gần với thời điểm sự việc xảy ra nhưng phụ thuộc đồng hồ và cách producer đặt. Với `LogAppendTime`, nó là thời điểm vào hệ thống (ingestion time). Bài toán cần thời điểm thật của sự việc thì thường lấy timestamp ghi trong payload, vì đó là nơi nguồn ghi đúng nghĩa nghiệp vụ (xem [10-time-and-windows.md](10-time-and-windows.md)).
>
> Ranh giới: broker có thể từ chối record có `CreateTime` lệch quá xa so với đồng hồ broker, theo một ngưỡng cấu hình được. Giá trị mặc định của ngưỡng khác nhau giữa các bản và các nhà cung cấp, nên phải kiểm tra trên chính cluster đang dùng.

## Hiểu nhầm thường gặp
- **"Topic có thứ tự."** Chỉ partition có thứ tự. Topic nhiều partition không có thứ tự toàn cục.
- **"Thêm partition lúc nào cũng an toàn."** Nó phá ánh xạ key → partition, nên ảnh hưởng tới thứ tự theo key và state.
- **"Offset kế tiếp luôn là offset hiện tại + 1."** Compaction và transaction để lại lỗ trong dãy offset.
- **"Compaction nghĩa là mỗi key chỉ có một record."** Compaction chỉ đảm bảo *giữ ít nhất* bản mới nhất, và chạy trễ. Phần đầu log chưa được dọn vẫn có nhiều bản.

## Liên quan
- [01-stream-processing-fundamentals.md](01-stream-processing-fundamentals.md): stream-table duality, nền của compaction.
- [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md): consumer dùng offset và partition thế nào.
- [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md): giữ thứ tự theo key khi xử lý song song.
- [11-state-and-joins.md](11-state-and-joins.md): changelog compacted và co-partitioning.
