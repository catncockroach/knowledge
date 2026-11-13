# Consumer group và offset

> Một **consumer** đọc record bằng một vòng lặp poll. Nhiều consumer cùng `group.id` tạo thành một **consumer group** và chia nhau các partition. Mỗi partition chỉ thuộc một member tại một thời điểm. Tiến độ của group được lưu dưới dạng **committed offset** cho mỗi partition, và khoảng cách từ đó tới cuối log là **lag**.

## Tại sao cần biết
Hai câu hỏi nền nhất của một engine consumer là "chia việc cho nhiều instance thế nào" và "crash thì đọc lại từ đâu". Consumer group trả lời câu thứ nhất, committed offset trả lời câu thứ hai. Gần như mọi chuyện mất hay trùng dữ liệu đều quy về khoảng cách giữa "đã xử lý tới đâu" và "đã commit tới đâu" tại lúc crash hoặc lúc partition đổi chủ. File này giải thích các khái niệm đó; cách partition được chia lại nằm ở [04-rebalancing-and-scaling.md](04-rebalancing-and-scaling.md), còn thứ tự giữa xử lý và commit nằm ở [05-delivery-semantics.md](05-delivery-semantics.md).

## Khái niệm cốt lõi

### Consumer và vòng poll
- **Là gì**: consumer là client chủ động *kéo* (pull) dữ liệu. Nó lặp đi lặp lại thao tác `poll`: gửi fetch request tới broker, nhận về một nhóm record, xử lý, rồi poll tiếp.
- **Dùng để**: consumer tự quyết định tốc độ đọc. Đọc chậm thì record nằm chờ trong log, không làm broker quá tải. Đây là nền của backpressure (xem [09-backpressure-and-throughput.md](09-backpressure-and-throughput.md)).

### Consumer group
- **Là gì**: tập các consumer cùng một `group.id`. Partition của các topic mà group đăng ký được chia cho các member, mỗi partition thuộc đúng một member.
- **Dùng để**: scale ngang. Thêm instance thì việc được chia nhỏ ra. Các group khác nhau đọc cùng topic độc lập, mỗi group có tiến độ riêng. Nhờ vậy một topic phục vụ được nhiều ứng dụng.

### Group coordinator
- **Là gì**: một broker được chọn để quản lý một group. Nó theo dõi member nào còn sống, điều phối việc chia partition, và lưu committed offset của group.
- **Dùng để**: một điểm quyết định chung cho cả group, nhờ đó hai member không cùng giữ một partition.

### Assignment
- **Là gì**: kết quả chia partition: member nào giữ partition nào.
- **Dùng để**: mỗi member biết mình phải đọc gì. Khi assignment đổi (member vào hoặc ra), group chạy rebalance (xem [04-rebalancing-and-scaling.md](04-rebalancing-and-scaling.md)). Ứng dụng nhận callback khi được *giao* (assigned) hoặc bị *thu hồi* (revoked) partition, và đó là chỗ nó khởi tạo hoặc dọn state của partition.

### Position và committed offset
- **Position**
  - **Là gì**: offset của record kế tiếp mà client sẽ trả về cho ứng dụng. Nó nằm trong bộ nhớ của consumer và tăng mỗi lần poll.
  - **Dùng để**: client biết fetch tiếp từ đâu trong lúc đang chạy.
- **Committed offset**
  - **Là gì**: vị trí đã được lưu bền vững cho (group, topic, partition), nằm trong topic nội bộ `__consumer_offsets`. Theo quy ước, đây là offset của *record kế tiếp cần đọc*: xử lý xong record offset N thì commit N+1.
  - **Dùng để**: phục hồi. Khi consumer khởi động lại, hoặc khi partition chuyển sang member khác, việc đọc bắt đầu từ committed offset, *không phải* từ position.
- Khoảng cách giữa position, phần đã xử lý xong và committed offset chính là vùng có thể bị mất hoặc xử lý lặp.

### Commit
- **Là gì**: thao tác gửi committed offset lên coordinator. Có ba cách:

  | Cách | Là gì | Dùng để / rủi ro |
  |---|---|---|
  | Auto commit | Client tự commit định kỳ những gì đã trả về cho ứng dụng | Đơn giản. Chỉ đúng nếu ứng dụng xử lý xong mọi record của một lần poll trước lần poll kế. Xử lý bất đồng bộ thì commit có thể vượt tiến độ thật, gây mất |
  | Commit đồng bộ | Gọi commit và chờ kết quả | Chắc chắn đã lưu. Tốn một round-trip mỗi lần, nên thường dùng ở ranh giới: khi bị thu hồi partition, khi shutdown |
  | Commit bất đồng bộ | Gửi commit, không chờ, lỗi báo qua callback | Không chặn vòng xử lý. Một lần commit lỗi có thể được lần sau bù lại |

- Một số client có thêm chế độ trung gian: ứng dụng *đánh dấu* (mark) record đã xử lý xong, và client chỉ tự commit phần đã đánh dấu. Chế độ này tách việc "xử lý xong" khỏi việc "poll".

### Điểm bắt đầu khi chưa có commit (`auto.offset.reset`)
- **Là gì**: quy tắc chọn vị trí đọc khi group chưa có committed offset cho partition, hoặc offset đã lưu không còn hợp lệ (dữ liệu đã bị xoá theo retention). Ba giá trị: `earliest` (đọc từ đầu log), `latest` (chỉ đọc record mới đến), `none` (báo lỗi).
- **Dùng để**: quyết định group mới thấy dữ liệu cũ hay không. Chọn `latest` cho group mới thì bỏ qua mọi thứ đã có trong topic. Chọn `earliest` thì xử lý lại toàn bộ.

### Lag
- **Lag theo offset**
  - **Là gì**: log end offset trừ committed offset của một partition, tức số record còn tồn chưa xử lý.
  - **Dùng để**: đo hàng đợi đang dài bao nhiêu.
- **Lag theo thời gian**
  - **Là gì**: hiện tại trừ timestamp của record nằm ở committed offset, tức consumer đang chậm bao nhiêu giây so với dữ liệu.
  - **Dùng để**: đo độ trễ theo cảm nhận của người dùng. Cùng 10.000 record lag là 0,1 giây trên topic 100.000 msg/s, nhưng là 100 giây trên topic 100 msg/s (xem [13-observability-and-operations.md](13-observability-and-operations.md)).

### Liveness: heartbeat và các timeout
- **Heartbeat / session timeout**: consumer gửi heartbeat định kỳ; coordinator không nhận được heartbeat trong *session timeout* thì coi member đã chết và chia lại partition của nó. **Dùng để** phát hiện instance chết.
- **Poll interval tối đa** (`max.poll.interval.ms` ở client Java): khoảng thời gian tối đa giữa hai lần poll. Quá ngưỡng này thì client tự rời group. **Dùng để** phát hiện instance còn sống nhưng bị kẹt trong xử lý. Hệ quả: xử lý quá lâu trong vòng poll sẽ làm partition bị chia lại dù instance vẫn chạy.
- Mỗi client cài đặt heartbeat khác nhau. Có client gửi heartbeat ở luồng nền, độc lập với poll; có client gắn heartbeat vào poll. Vì vậy cùng một code xử lý chậm có thể bị đá khỏi group ở client này mà không bị ở client khác.

## Cách hoạt động

Group `billing` đọc topic có 4 partition, chạy 2 instance:

```
            topic orders: P0  P1  P2  P3
                           │   │   │   │
  group "billing":   A ◄───┴───┘   │   │      A giữ P0, P1
                     B ◄───────────┴───┘      B giữ P2, P3
  group "analytics": C ◄── P0 P1 P2 P3         group khác, tiến độ riêng

  __consumer_offsets:  (billing, orders, P0) = 1520
                       (billing, orders, P1) = 980   ...
                       (analytics, orders, P0) = 1610 ...
```

Vòng đời một partition ở member A:

```
được giao P0 ──► đọc committed offset (1520) ──► poll từ 1520 ──► xử lý ──► commit ──► poll ...
                                                                           │
bị thu hồi P0 ◄── (rebalance) ── commit lần cuối nếu còn kịp ◄──────────────┘
```

Nếu A crash sau khi xử lý tới 1600 nhưng mới commit 1520, member nhận P0 sẽ đọc lại từ 1520. Các record 1520–1599 được xử lý lần thứ hai.

## Ví dụ

Tính lag cho partition P0, tại thời điểm 10:05:00:

| Mốc | Giá trị |
|---|---|
| Log end offset | 50.000 |
| Committed offset của group | 47.000 |
| Timestamp của record tại offset 47.000 | 10:04:10 |
| Tốc độ ghi vào P0 | 200 msg/s |

- Lag theo offset: 50.000 − 47.000 = **3.000 record**.
- Lag theo thời gian: 10:05:00 − 10:04:10 = **50 giây**.
- Nếu consumer xử lý 300 msg/s, hàng đợi giảm 100 msg/s, nên mất khoảng 30 giây để bắt kịp. Nếu nó chỉ xử lý 150 msg/s, lag tăng 50 msg/s và không bao giờ bắt kịp.

## Câu hỏi

**Consumer group dùng để làm gì?**
> - **Consumer group**: tập consumer cùng `group.id`, chia nhau partition.
> - **Assignment**: bảng partition nào thuộc member nào.
>
> Quy tắc: trong một group, mỗi partition thuộc đúng một member, nên các member chia việc mà không trùng nhau. Giữa các group thì hoàn toàn độc lập: mỗi group có committed offset riêng và đọc toàn bộ topic. Vì vậy group vừa là đơn vị scale ngang (thêm member để chia việc) vừa là đơn vị cô lập ứng dụng (mỗi ứng dụng một group).
>
> Ranh giới: muốn hai ứng dụng *cùng* nhận mọi message thì cho chúng hai group khác nhau. Muốn chúng *chia* message thì cho chung một group. Nhầm hai trường hợp này là lỗi cấu hình phổ biến.

**Một partition có thể được nhiều consumer trong cùng group đọc không? Có bao nhiêu consumer là hữu ích?**
> - **Member**: một consumer trong group.
>
> Quy tắc: trong mô hình consumer group, một partition chỉ thuộc tối đa một member tại một thời điểm. Một member có thể giữ nhiều partition. Vì vậy số member xử lý song song hữu ích tối đa bằng tổng số partition; member thừa sẽ ngồi chờ, chỉ có ích để thay thế khi member khác chết.
>
> Ranh giới: giới hạn này nằm ở *đơn vị chia việc giữa các instance*, không chặn được song song *bên trong* một member. Một member có thể xử lý các record của cùng partition bằng nhiều goroutine (xem [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md)). Ngoài ra, Kafka có thêm mô hình share group, nơi nhiều consumer cùng đọc một partition và ack từng record, nhưng đó là ngữ nghĩa hàng đợi, không phải consumer group.

**Position khác committed offset ở đâu? Restart thì đọc lại từ cái nào?**
> - **Position**: offset record kế tiếp client sẽ trả về, nằm trong bộ nhớ.
> - **Committed offset**: vị trí đã lưu bền vững trên broker.
>
> Quy tắc: position chỉ sống trong một phiên chạy; committed offset là thứ duy nhất sống qua crash, restart và việc partition đổi chủ. Vì vậy mọi lần bắt đầu đọc một partition (khởi động, được giao partition) đều bắt đầu từ committed offset. Phần giữa committed offset và position sẽ được đọc lại.
>
> Ranh giới: nếu chưa có committed offset, hoặc offset đã lưu nhỏ hơn log start offset (dữ liệu đã bị xoá), điểm bắt đầu do `auto.offset.reset` quyết định. Ứng dụng cũng có thể chủ động `seek` tới vị trí nó tự lưu ở nơi khác (xem [06-idempotency-and-sinks.md](06-idempotency-and-sinks.md)).

**Vì sao xử lý xong record offset N thì commit N+1?**
> - **Committed offset**: theo quy ước của Kafka là "offset của record kế tiếp cần đọc".
>
> Quy tắc: committed offset là một *vị trí bắt đầu*, không phải "record cuối cùng đã xong". Commit N+1 nghĩa là mọi record có offset nhỏ hơn N+1 đã được xử lý. Nếu commit N thì sau khi restart record N bị xử lý lại; nếu commit N+2 thì record N+1 bị bỏ qua.
>
> Ranh giới: nhiều client có hàm commit nhận chính record vừa xử lý và tự cộng 1. Khi xử lý song song, "record vừa xử lý xong" không phải là mốc an toàn, vì các record trước nó có thể chưa xong (xem [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md)).

**Lag theo offset và lag theo thời gian khác nhau thế nào, dùng cái nào?**
> - **Lag theo offset**: số record còn tồn.
> - **Lag theo thời gian**: consumer chậm bao nhiêu giây so với dữ liệu.
>
> Tiêu chí: lag theo offset đo *khối lượng* việc còn lại, nên hợp để ước lượng cần bao nhiêu năng lực xử lý. Lag theo thời gian đo *độ trễ* mà người dùng thấy, nên hợp để so với yêu cầu latency. Cùng một số offset lag có ý nghĩa rất khác nhau giữa topic nhiều traffic và topic ít traffic, nên một ngưỡng offset lag dùng chung cho mọi topic không phản ánh đúng mức nghiêm trọng.
>
> Ranh giới: lag bằng 0 chưa chắc consumer khoẻ. Topic không có dữ liệu mới thì lag luôn bằng 0, kể cả khi consumer đã chết. Ngược lại, lag ổn định ở một mức khác 0 có thể là bình thường (consumer xử lý theo batch). Cách đánh giá lag theo xu hướng nằm ở [13-observability-and-operations.md](13-observability-and-operations.md).

**Vì sao instance vẫn chạy mà partition lại bị chia sang member khác?**
> - **Session timeout**: thời gian không có heartbeat thì coordinator coi member đã chết.
> - **Poll interval tối đa**: thời gian tối đa giữa hai lần poll.
>
> Quy tắc: group coi một member là sống chỉ khi nó vừa gửi heartbeat đều, vừa poll đủ thường xuyên. Xử lý một lô record lâu hơn poll interval tối đa (gọi API chậm, retry bằng `sleep`, chờ sink sập) làm member bị loại. Partition của nó được chia cho member khác và đọc lại từ committed offset, trong khi member cũ có thể vẫn đang xử lý chính những record đó. Kết quả là xử lý trùng.
>
> Ranh giới: cách client gửi heartbeat ảnh hưởng tới hành vi này. Client gửi heartbeat ở luồng nền chỉ gặp vấn đề khi ứng dụng chặn rebalance trong lúc xử lý lâu. Cách tránh chung là không chặn vòng poll: chờ bằng cách tạm dừng fetch partition (pause) thay vì `sleep` (xem [09-backpressure-and-throughput.md](09-backpressure-and-throughput.md)).

## Hiểu nhầm thường gặp
- **"Kafka biết message nào đã được xử lý."** Kafka chỉ biết một con số cho mỗi partition: committed offset. Nó không theo dõi từng message.
- **"Auto commit nghĩa là at-least-once."** Chỉ đúng khi ứng dụng xử lý xong record trước lần poll kế. Đẩy record sang goroutine khác rồi poll tiếp thì auto commit có thể commit phần chưa xử lý, gây mất.
- **"Thêm instance là xử lý nhanh hơn."** Vượt quá số partition thì instance thêm vào chỉ ngồi chờ.
- **"Lag bằng 0 là ổn."** Lag bằng 0 trên topic không có dữ liệu mới không nói gì về sức khoẻ consumer.

## Liên quan
- [02-kafka-log-model.md](02-kafka-log-model.md): partition, offset và các mốc của log.
- [04-rebalancing-and-scaling.md](04-rebalancing-and-scaling.md): assignment thay đổi thế nào khi member vào hoặc ra.
- [05-delivery-semantics.md](05-delivery-semantics.md): thứ tự giữa xử lý và commit quyết định mất hay trùng.
- [13-observability-and-operations.md](13-observability-and-operations.md): đo lag và phát hiện consumer kẹt.
