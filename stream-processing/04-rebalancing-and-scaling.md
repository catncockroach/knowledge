# Rebalance và scale consumer

> **Rebalance** là quá trình group chia lại partition khi member vào, ra hoặc chết. Trong lúc rebalance, các partition đang chuyển chủ ngừng được xử lý, và phần đã xử lý mà chưa commit sẽ được xử lý lại. Ba thế hệ giao thức (eager, cooperative, do broker điều khiển) khác nhau ở *phần nào của group phải dừng*. **Static membership** cho phép một instance restart mà không gây rebalance. Scale consumer bị chặn trên bởi số partition, và mỗi lần scale lại gây một lần rebalance.

## Tại sao cần biết
Rebalance là nguồn trùng lặp và gián đoạn lớn nhất của một engine consumer trong vận hành bình thường. Mỗi lần deploy, mỗi lần pod restart, mỗi lần autoscale đều có thể gây rebalance. Với engine stateful, rebalance còn kéo theo việc chuyển hoặc dựng lại state, có thể mất từ vài giây tới hàng giờ. Hiểu rebalance thì mới biết vì sao rollout lại sinh bản trùng, vì sao autoscale có thể tự làm lag tăng thêm, và vì sao số partition phải được tính trước.

## Khái niệm cốt lõi

### Rebalance
- **Là gì**: quá trình group tính lại assignment khi tập member thay đổi (member mới vào, member rời đi, member bị coi là chết) hoặc khi tập partition thay đổi (thêm partition, topic mới khớp pattern đăng ký).
- **Dùng để**: giữ bất biến "mỗi partition thuộc đúng một member" khi group thay đổi.

### Generation / epoch
- **Là gì**: số thế hệ của group, tăng sau mỗi lần rebalance. Mỗi member biết mình thuộc thế hệ nào.
- **Dùng để**: chặn *zombie*, tức member cũ chưa biết mình đã mất partition. Commit kèm thế hệ cũ bị coordinator từ chối, nên member cũ không ghi đè được tiến độ của member mới.

### Assignor
- **Là gì**: thuật toán chia partition cho member. Các loại cơ bản: *range* (chia dải liên tiếp theo từng topic), *round-robin* (rải lần lượt), *sticky* (giữ assignment cũ nhiều nhất có thể), *cooperative-sticky* (sticky và cho phép rebalance từng phần).
- **Dùng để**: quyết định rebalance di chuyển bao nhiêu partition. Sticky giảm số partition phải đổi chủ, nên giảm việc đọc lại và chuyển state.

### Callback revoked và lost
- **Revoked**
  - **Là gì**: thông báo "partition này sắp được chuyển đi", gọi khi member *vẫn còn* quyền với partition.
  - **Dùng để**: chờ phần đang xử lý xong, commit đồng bộ, flush và đóng state của partition trước khi member khác nhận.
- **Lost**
  - **Là gì**: thông báo "partition này đã mất", gọi khi member bị loại khỏi group (quá session timeout).
  - **Dùng để**: dọn tài nguyên. Lúc này member *không được* commit nữa, vì partition có thể đã thuộc người khác.
- Không xử lý hai trường hợp khác nhau là nguồn lỗi phổ biến. Commit trong lost có thể ghi đè tiến độ của member mới; không commit trong revoked thì member mới đọc lại nhiều hơn cần thiết.

### Ba thế hệ giao thức rebalance

| Giao thức | Cách chạy | Phần nào dừng |
|---|---|---|
| Eager | Mọi member trả hết partition, một member leader tính assignment mới, rồi mọi member nhận lại | Cả group dừng hoàn toàn ("stop the world") |
| Cooperative (incremental) | Hai vòng: vòng đầu chỉ thu hồi các partition phải chuyển, vòng sau giao chúng cho member mới; partition không đổi chủ vẫn được xử lý | Chỉ partition phải chuyển, nhưng mọi member vẫn qua một điểm đồng bộ chung |
| Do broker điều khiển (KIP-848) | Broker tự tính assignment, gửi lệnh thu hồi và giao qua heartbeat cho từng member; không có điểm đồng bộ toàn group | Chỉ member được yêu cầu thu hồi partition mới dừng, và chỉ dừng ở các partition đó |

- **Dùng để**: hiểu chi phí của mỗi lần rebalance. Với eager, mọi thay đổi nhỏ (một pod restart) đều dừng cả group. Với cooperative và KIP-848, chi phí tỉ lệ với số partition thực sự phải chuyển.
- Ở giao thức do broker điều khiển, cấu hình heartbeat, session timeout và assignor chuyển sang phía broker. Client phải hỗ trợ giao thức mới và chủ động bật; mức hỗ trợ khác nhau giữa các client và giữa các bản broker.

### Static membership
- **Là gì**: mỗi member khai báo một định danh cố định (`group.instance.id`), ví dụ tên pod. Member static khi tắt không gửi yêu cầu rời group. Nếu nó quay lại trong session timeout với cùng định danh, nó nhận lại đúng assignment cũ mà không gây rebalance.
- **Dùng để**: restart nhanh (deploy, pod khởi động lại) mà không xáo trộn group. Lợi ích lớn nhất ở engine stateful, vì partition quay về đúng instance có sẵn state trên đĩa.
- **Đánh đổi**: khi instance chết thật, partition của nó đứng yên cho tới hết session timeout. Session timeout càng dài để chịu được restart thì thời gian chết này càng dài. Định danh cũng phải được quản lý để hai instance không trùng nhau.

### Trần scale: số partition
- **Là gì**: trong consumer group, số member làm việc song song tối đa bằng số partition (xem [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md)).
- **Dùng để**: tính năng lực tối đa. Khi đã chạm trần, thêm instance không giúp gì nữa. Còn tăng partition thì phá ánh xạ key → partition (xem [02-kafka-log-model.md](02-kafka-log-model.md)). Vì vậy số partition của topic có key là quyết định cho mức scale tối đa dự kiến, không phải mức hiện tại.

### Autoscale theo lag
- **Là gì**: điều chỉnh số instance theo lag thay vì theo CPU hay RAM. Công thức phổ biến là số replica ≈ trần(tổng lag / ngưỡng lag mỗi replica), chặn trên bởi số partition.
- **Dùng để**: theo kịp tải dao động theo giờ. Lag phản ánh đúng việc còn tồn, trong khi CPU không phản ánh được: consumer chủ yếu chờ I/O (gọi DB, API) có CPU gần như phẳng dù đang tụt lại phía sau.
- **Vòng phản hồi rebalance**: lag tăng thì scale up; mỗi lần thêm hoặc bớt member là một lần rebalance; rebalance làm dừng xử lý, nên lag tăng thêm và có thể kích hoạt lần scale tiếp theo. Các yếu tố làm vòng này dịu đi: giao thức cooperative hoặc do broker điều khiển (rebalance rẻ), thời gian chờ giữa hai lần scale (cooldown), và cửa sổ ổn định dài trước khi scale down. Static membership không giúp được ở đây, vì scale là thật sự thêm hoặc bớt member.

### Số instance cố định
- **Là gì**: chạy số instance bằng số partition (hoặc một ước số của nó), chỉ chỉnh tài nguyên của từng instance theo chiều dọc.
- **Dùng để**: tránh hoàn toàn rebalance do scale và chia tải đều. Phù hợp khi tải ổn định, hoặc khi chi phí rebalance (state lớn) cao hơn chi phí để instance chạy không tải lúc thấp điểm.

## Cách hoạt động

Group có member A (P0, P1, P2) và B (P3, P4, P5); member C vào.

```
Eager:
  A, B trả hết ──► [cả group dừng] ──► leader tính: A{P0,P1} B{P3,P4} C{P2,P5} ──► mọi member nhận lại
  P0..P5 đều ngừng xử lý trong lúc này

Cooperative (2 vòng):
  vòng 1: A vẫn chạy P0,P1, chỉ trả P2 ; B vẫn chạy P3,P4, chỉ trả P5
  vòng 2: C nhận P2, P5
  chỉ P2, P5 ngừng xử lý

Do broker điều khiển:
  broker gửi qua heartbeat: "A thu hồi P2", "B thu hồi P5"
  A, B xác nhận từng phần ──► broker gửi "C nhận P2, P5"
  không có điểm đồng bộ chung; A, B không phải chờ nhau
```

Static membership khi pod B restart:

```
B tắt (không gửi leave) ──► P3, P4, P5 đứng yên, chưa chia cho ai
B quay lại với cùng instance id trong session timeout ──► nhận lại P3, P4, P5 ──► không có rebalance
B không quay lại kịp ──► hết session timeout ──► rebalance, P3..P5 chia cho A, C
```

## Ví dụ

Topic có 24 partition, mỗi instance xử lý ổn định khoảng 3.000 msg/s, tải từ 15.000 msg/s (đêm) tới 60.000 msg/s (cao điểm):

| Phương án | Số instance | Ghi chú |
|---|---|---|
| Cố định theo cao điểm | 20 (≥ 60.000 / 3.000) | Không có rebalance do scale; ban đêm phần lớn chạy không tải |
| Autoscale theo lag | 5 đến 20 | Tiết kiệm tài nguyên; mỗi lần đổi số instance là một lần rebalance |
| Muốn chịu được 100.000 msg/s | Cần ≥ 34 instance | Vượt trần 24 partition: hoặc tăng partition (phá thứ tự theo key), hoặc tăng song song bên trong mỗi instance (xem [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md)) |

Dòng cuối cho thấy vì sao số partition được tính theo mức tối đa dự kiến ngay từ lúc tạo topic.

## Câu hỏi

**Rebalance là gì, khi nào xảy ra?**
> - **Rebalance**: quá trình chia lại partition giữa các member của group.
> - **Assignment**: bảng partition nào thuộc member nào.
>
> Quy tắc: mọi thay đổi trong tập member hoặc tập partition của group đều gây rebalance. Cụ thể: member mới vào (scale up, pod mới khi deploy), member rời đi (scale down, shutdown), member bị coi là chết (mất heartbeat quá session timeout, hoặc không poll trong poll interval tối đa), và partition được thêm vào topic.
>
> Ranh giới: với static membership, member tắt rồi quay lại kịp trong session timeout không gây rebalance. Đổi lại, member chết thật cũng chỉ được phát hiện sau session timeout.

**Vì sao rebalance gây xử lý trùng?**
> - **Committed offset**: vị trí member mới bắt đầu đọc khi nhận partition.
> - **Callback revoked**: cơ hội cuối để member cũ commit.
>
> Quy tắc: member mới luôn bắt đầu từ committed offset. Mọi record member cũ đã xử lý mà chưa kịp commit sẽ được xử lý lại. Lượng trùng bằng khoảng cách giữa tiến độ xử lý và tiến độ commit tại lúc partition đổi chủ. Commit đồng bộ trong callback revoked thu hẹp khoảng này; bị loại khỏi group (lost) thì không thu hẹp được.
>
> Ranh giới: có một lỗi ngược lại, nguy hiểm hơn. Member cũ commit *sau khi* member mới đã tiến xa hơn sẽ làm committed offset lùi lại (rewind). Cơ chế generation hoặc epoch tồn tại để coordinator từ chối các commit muộn như vậy.

**Eager, cooperative và giao thức do broker điều khiển khác nhau ở đâu?**
> - **Eager**: mọi member trả hết partition rồi nhận lại.
> - **Cooperative**: chỉ thu hồi partition phải chuyển, qua hai vòng.
> - **Do broker điều khiển (KIP-848)**: broker tính assignment và điều khiển từng member qua heartbeat.
>
> Tiêu chí phân biệt là *phạm vi dừng*. Eager dừng cả group. Cooperative chỉ dừng partition phải chuyển, nhưng mọi member vẫn qua một điểm đồng bộ chung, nên một member chậm làm cả group chờ. Giao thức do broker điều khiển bỏ điểm đồng bộ chung, nên mỗi member chỉ dừng đúng phần được yêu cầu.
>
> Ranh giới: một group chỉ chạy cooperative khi mọi member hỗ trợ nó. Một member chỉ biết eager tham gia vào là kéo cả group về eager. Giao thức mới cũng cần đồng thời broker và client hỗ trợ; client không đủ điều kiện có thể âm thầm quay về giao thức cũ, nên phải xác nhận giao thức thực tế của group trên broker.

**Static membership giải quyết vấn đề gì, và có cái giá gì?**
> - **Static membership**: member mang định danh cố định, tắt không rời group.
> - **Session timeout**: thời gian group chờ trước khi coi member là chết.
>
> Quy tắc: static membership đổi *tốc độ phát hiện instance chết* lấy *sự ổn định khi restart*. Restart trong session timeout không gây rebalance, nên partition và state ở yên. Cái giá: instance chết thật thì partition của nó đứng yên cho tới hết session timeout, và lag của các partition đó tăng trong thời gian này.
>
> Ranh giới: static membership không giúp gì khi scale, vì scale thật sự thêm hoặc bớt member. Nó cũng đòi định danh duy nhất. Hai instance trùng định danh sẽ thay nhau đá nhau ra khỏi group.

**Vì sao autoscale consumer theo CPU thường không hiệu quả, và autoscale theo lag có bẫy gì?**
> - **Lag**: số record, hoặc số giây, consumer còn chậm so với log.
> - **Vòng phản hồi rebalance**: scale gây rebalance, rebalance làm lag tăng.
>
> Quy tắc: tín hiệu scale phải đo đúng việc còn tồn. CPU chỉ phản ánh tải khi xử lý là CPU-bound. Consumer chủ yếu chờ DB hay API có CPU thấp trong khi lag tăng, nên scale theo CPU vừa không scale kịp vừa chia tải lệch. Lag đo trực tiếp hàng đợi, nhưng có hai bẫy: (1) mỗi lần scale là một lần rebalance, có thể tự kích thích thêm lần scale nữa; (2) số replica bị chặn trên bởi số partition.
>
> Ranh giới: lag theo offset không cùng đơn vị giữa các topic có traffic khác nhau. Một ngưỡng tính bằng giây (lag theo thời gian) phản ánh yêu cầu latency sát hơn. Group chưa từng commit thì lag có thể được báo sai (âm hoặc bằng 0), dẫn tới scale về 0 rồi không lên lại được.

**Nên chọn bao nhiêu partition cho một topic?**
> - **Trần song song**: số member làm việc trong group không vượt số partition.
>
> Quy tắc: số partition xác định độ song song tối đa giữa các instance, và với topic có key thì về sau không đổi được mà không phá thứ tự. Vì vậy nó được tính từ mức tải tối đa dự kiến: số partition ≥ số instance tối đa × số luồng xử lý theo partition trong mỗi instance. Partition quá ít thì chạm trần scale khi sự cố cần bắt kịp nhanh. Partition quá nhiều thì tăng chi phí cho broker, tăng thời gian rebalance, và mỗi partition nhận ít dữ liệu nên batch nhỏ.
>
> Ranh giới: song song bên trong một instance (worker pool theo key) tách được độ song song xử lý khỏi số partition. Khi đó số partition chỉ cần đủ để chia tải giữa các instance (xem [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md)).

## Hiểu nhầm thường gặp
- **"Rebalance chỉ xảy ra khi có sự cố."** Mỗi lần deploy, mỗi lần scale và mỗi lần pod restart đều có thể gây rebalance.
- **"Cooperative nghĩa là không dừng xử lý."** Partition phải chuyển vẫn dừng, và vẫn có một điểm đồng bộ toàn group.
- **"Static membership làm group phục hồi nhanh hơn."** Nó làm *restart* nhanh hơn, nhưng làm việc phát hiện *instance chết thật* chậm hơn.
- **"Callback revoked luôn được gọi trước khi mất partition."** Khi bị loại vì quá timeout, member nhận lost chứ không nhận revoked, và không được commit nữa.

## Liên quan
- [03-consumer-groups-and-offsets.md](03-consumer-groups-and-offsets.md): group, assignment, heartbeat và các timeout.
- [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md): song song bên trong instance để vượt trần partition.
- [11-state-and-joins.md](11-state-and-joins.md): rebalance kéo theo chuyển và dựng lại state.
- [13-observability-and-operations.md](13-observability-and-operations.md): đo lag, shutdown và rollout.
