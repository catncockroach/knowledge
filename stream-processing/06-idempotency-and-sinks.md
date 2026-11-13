# Idempotency và sink

> Một thao tác là **idempotent** khi thực hiện nhiều lần cho cùng kết quả như thực hiện một lần. Khi sink nằm ngoài Kafka, transaction của Kafka không bao được việc ghi, nên engine at-least-once chỉ cho kết quả đúng nếu sink chịu được ghi lặp. Có ba cách chính: thao tác tự nhiên idempotent (upsert, cập nhật có điều kiện), khử trùng bằng **idempotency key**, và **lưu offset cùng kết quả** trong một transaction của sink.

## Tại sao cần biết
At-least-once là mức mặc định thực tế của hầu hết engine (xem [05-delivery-semantics.md](05-delivery-semantics.md)). Mỗi lần crash, rebalance hay rollout đều sinh ra một ít record được xử lý lại. Nếu sink không chịu được việc đó, số dư bị cộng hai lần, email gửi hai lần, đơn hàng tạo hai lần. Phần lớn các hệ thống tự gọi là "exactly-once" thực chất là at-least-once cộng một sink idempotent. Vì vậy thiết kế sink là nơi quyết định đúng-sai của kết quả cuối, không phải cấu hình Kafka.

## Khái niệm cốt lõi

### Idempotency
- **Là gì**: tính chất của một thao tác: áp dụng lần thứ hai, thứ ba không thay đổi gì so với lần đầu. `SET balance = 100` là idempotent; `SET balance = balance + 10` thì không.
- **Dùng để**: biến việc giao lặp (không tránh được) thành vô hại.

### Thao tác tự nhiên idempotent
- **Upsert theo khoá nghiệp vụ**
  - **Là gì**: ghi "trạng thái của thực thể X là Y", có rồi thì ghi đè, chưa có thì tạo.
  - **Dùng để**: event mang *trạng thái đầy đủ* (hồ sơ user, trạng thái đơn hàng). Ghi lặp chỉ ghi đè cùng giá trị.
- **Cập nhật có điều kiện theo version**
  - **Là gì**: chỉ ghi nếu version của event lớn hơn version đang lưu: `UPDATE ... WHERE version < :v`.
  - **Dùng để**: vừa khử trùng, vừa chống bản cũ ghi đè bản mới khi event đến lệch thứ tự.
- **Thao tác cộng dồn** (tăng số đếm, trừ tồn kho, cộng tiền) *không* tự nhiên idempotent. Nó cần một trong hai cơ chế dưới.

### Idempotency key
- **Là gì**: một định danh duy nhất của event (event ID do nguồn sinh, hoặc toạ độ `topic/partition/offset`). Sink nhớ các key đã áp dụng và bỏ qua key đã thấy.
- **Dùng để**: khử trùng cho thao tác không tự nhiên idempotent.
- Chi phí nhớ key phụ thuộc loại key:

  | Loại key | Phải nhớ gì để khử trùng |
  |---|---|
  | Ngẫu nhiên (UUID ngẫu nhiên) | Mọi key đã thấy, hoặc mọi key trong một cửa sổ thời gian đã chọn |
  | Có thời gian bên trong (UUID có timestamp, ULID) | Key trong một cửa sổ; key cũ hơn cửa sổ được coi là trùng hoặc quá hạn |
  | Đơn điệu tăng theo một nguồn | Chỉ cần key lớn nhất; mọi key nhỏ hơn hoặc bằng là trùng |

- **Offset theo partition là key đơn điệu tự nhiên**: trong một partition, offset luôn tăng. Sink chỉ cần lưu "offset lớn nhất đã áp dụng" cho mỗi partition, và bỏ mọi record có offset nhỏ hơn hoặc bằng. Chi phí là hằng số.

### Lưu offset trong sink
- **Là gì**: tắt việc commit offset lên Kafka (hoặc chỉ dùng nó để quan sát), ghi kết quả *và* offset `(topic, partition, offset)` vào sink trong cùng một transaction. Khi được giao partition, consumer đọc offset từ sink rồi `seek` tới đó.
- **Dùng để**: đạt exactly-once cho một sink có transaction (database quan hệ). Kết quả và tiến độ luôn khớp vì chúng được ghi nguyên tử cùng nhau.
- **Đánh đổi**: offset không còn nằm ở Kafka, nên công cụ đo lag và reset offset của Kafka không thấy tiến độ thật, trừ khi engine vẫn commit lên Kafka để quan sát.

### Bảng inbox (dedupe phía đọc)
- **Là gì**: bảng có ràng buộc duy nhất trên (consumer, event ID). Engine insert vào bảng này *trong cùng transaction* với cập nhật nghiệp vụ. Insert lỗi do trùng nghĩa là event đã xử lý.
- **Dùng để**: khử trùng tổng quát cho nghiệp vụ không upsert được, khi event có ID ổn định.

### Dual write và outbox
- **Dual write**
  - **Là gì**: ghi vào hai hệ thống (database và Kafka) bằng hai thao tác độc lập.
  - **Vấn đề**: không có thao tác nguyên tử chung. Crash giữa hai bước để lại một bên có dữ liệu còn bên kia không.
- **Outbox**
  - **Là gì**: ghi event cần phát vào một bảng outbox *cùng transaction* với dữ liệu nghiệp vụ. Một tiến trình relay (thường đọc qua CDC) đẩy bảng outbox lên Kafka.
  - **Dùng để**: phát event từ DB lên Kafka mà không mất. Relay có thể publish rồi crash trước khi đánh dấu xong, nên outbox cho at-least-once. Bên đọc vẫn cần khử trùng, thường bằng ID của dòng outbox đặt trong header.
- Ghi sang retry topic hay DLQ rồi commit offset gốc cũng là một dual write Kafka → Kafka. Produce phải được broker xác nhận *trước* khi commit offset gốc, hoặc cả hai nằm trong một transaction (xem [07-errors-retry-and-dlq.md](07-errors-retry-and-dlq.md)).

### Sink là API bên ngoài
- **Là gì**: gọi một dịch vụ HTTP/gRPC không thuộc quyền kiểm soát của engine.
- Nếu API nhận idempotency key (header, trường request), engine gửi key ổn định (event ID hoặc `topic/partition/offset`) và API tự khử trùng. Nếu API không hỗ trợ, gọi lặp là không tránh được dưới at-least-once. Chỉ còn cách chấp nhận, hoặc đặt một lớp trung gian có lưu trạng thái để nhớ đã gọi chưa.

## Cách hoạt động

### Lưu offset cùng kết quả trong DB

```sql
-- Một transaction cho mỗi batch của một partition
BEGIN;
  UPDATE accounts SET balance = balance + :amount WHERE id = :acc;   -- cho từng record
  ...
  INSERT INTO consumer_offsets(topic, part, next_offset) VALUES ('payments', 3, 1500)
    ON CONFLICT (topic, part) DO UPDATE SET next_offset = EXCLUDED.next_offset;
COMMIT;
```

```
khi được giao partition 3:
  next := SELECT next_offset FROM consumer_offsets WHERE topic='payments' AND part=3
  consumer.Seek(partition 3, next)
```

Crash trước `COMMIT` thì cả cập nhật số dư lẫn offset đều không có hiệu lực, và batch được đọc lại. Crash sau `COMMIT` thì offset mới đã lưu, nên batch không bị đọc lại.

### Khử trùng bằng offset lớn nhất

```go
// Minh hoạ: sink giữ offset lớn nhất đã áp dụng cho mỗi partition.
func (s *Sink) Apply(tx Tx, r Record) error {
    last := tx.LastOffset(r.Topic, r.Partition)   // đọc trong cùng transaction
    if r.Offset <= last {
        return nil                                  // đã áp dụng: bỏ qua
    }
    if err := tx.ApplyBusiness(r); err != nil {
        return err
    }
    return tx.SetLastOffset(r.Topic, r.Partition, r.Offset)
}
```

Cách này đúng khi mọi record của một partition đi qua sink theo đúng thứ tự offset. Nếu xử lý song song lệch thứ tự trong một partition, "offset lớn nhất" không còn là mốc khử trùng an toàn, và phải dùng key theo từng record.

## Ví dụ

Chọn kỹ thuật theo loại sink:

| Sink | Kỹ thuật | Kết quả đạt được |
|---|---|---|
| Kho metric, chấp nhận sai số nhỏ | Ghi thẳng | At-least-once, số liệu có thể lệch nhẹ khi có sự cố |
| Bảng trạng thái thực thể (hồ sơ, trạng thái đơn) | Upsert theo khoá, hoặc cập nhật có điều kiện theo version | Kết quả như exactly-once |
| Sổ cái, số dư (cộng dồn) | Offset lưu trong cùng transaction DB, hoặc bảng inbox | Exactly-once cho sink đó |
| Topic Kafka khác | Transaction Kafka, bên đọc `read_committed` (xem [05-delivery-semantics.md](05-delivery-semantics.md)) | Exactly-once |
| API thanh toán có idempotency key | Gửi `topic/partition/offset` hoặc event ID làm key | Kết quả như exactly-once |
| API gửi SMS không có key | Không khử được | At-least-once: có thể gửi lặp |

## Câu hỏi

**Idempotent là gì, và vì sao sink cần idempotent?**
> - **Idempotent**: làm nhiều lần cho kết quả như làm một lần.
> - **At-least-once**: message có thể được xử lý lại sau lỗi.
>
> Quy tắc: kết quả cuối cùng chỉ đúng khi *mức đảm bảo của engine* cộng với *khả năng chịu lặp của sink* đủ bù cho nhau. Engine at-least-once (mức mặc định thực tế) luôn sinh ra một ít bản lặp mỗi khi crash, rebalance hay rollout, nên sink phải idempotent thì kết quả mới đúng.
>
> Ranh giới: sink không idempotent vẫn chấp nhận được khi bản lặp vô hại về nghiệp vụ, ví dụ ghi log, ghi metric chấp nhận sai số. Đó là lựa chọn có ý thức, không phải mặc định.

**Có những cách nào làm sink idempotent? Khi nào dùng cách nào?**
> - **Upsert / cập nhật có điều kiện**: ghi trạng thái thay vì ghi thay đổi.
> - **Idempotency key**: nhớ event đã áp dụng.
> - **Lưu offset trong sink**: ghi tiến độ cùng kết quả, nguyên tử.
>
> Tiêu chí: nếu event mang *trạng thái đầy đủ* thì upsert là đủ và rẻ nhất. Nếu event mang *thay đổi* (cộng, trừ, tạo mới) thì cần nhớ đã áp dụng hay chưa. Khi đó, sink có transaction và mỗi partition đi theo thứ tự thì lưu offset theo partition (chi phí hằng số). Event có ID ổn định và phải khử trùng giữa nhiều nguồn thì dùng bảng inbox theo ID.
>
> Ranh giới: idempotency key chỉ khử được trùng *do engine xử lý lại*. Nếu nguồn đã phát hai event khác ID cho cùng một việc (producer gửi lại sau restart), cả hai đều hợp lệ đối với sink. Khử loại trùng này cần khoá nghiệp vụ, không phải ID kỹ thuật.

**Vì sao offset theo partition dùng được làm idempotency key?**
> - **Offset**: số thứ tự tăng dần của record trong một partition.
> - **Key đơn điệu**: key luôn tăng, nên chỉ cần nhớ giá trị lớn nhất.
>
> Quy tắc: trong một partition, offset tăng nghiêm ngặt và mỗi record có đúng một offset. Vì vậy cặp (topic, partition) cộng "offset lớn nhất đã áp dụng" mô tả đầy đủ những gì sink đã thấy từ partition đó: record có offset nhỏ hơn hoặc bằng là trùng. Chi phí là một dòng cho mỗi partition, bất kể có bao nhiêu record.
>
> Ranh giới: cách này giả định record của một partition được áp dụng theo đúng thứ tự offset. Xử lý song song lệch thứ tự trong partition phá giả định đó. Ngoài ra, offset chỉ định danh *bản ghi trong log*: cùng một event được ghi vào log hai lần (do producer) có hai offset khác nhau.

**Dual write là gì, và outbox giải quyết nó thế nào?**
> - **Dual write**: ghi vào hai hệ thống bằng hai thao tác độc lập.
> - **Outbox**: ghi event vào bảng của DB trong cùng transaction với dữ liệu, rồi relay đẩy lên Kafka.
>
> Quy tắc: hai thao tác ghi vào hai hệ thống không thể nguyên tử nếu không có transaction chung, nên crash giữa chừng luôn có thể để lại một bên lệch. Outbox biến hai lần ghi thành *một* lần ghi nguyên tử (cùng DB), và đẩy phần phát lên Kafka thành một bước at-least-once có thể lặp lại an toàn.
>
> Ranh giới: outbox không cho exactly-once ở phía Kafka. Relay có thể phát một dòng outbox hai lần, nên bên đọc vẫn phải khử trùng, thường theo ID của dòng outbox.

**Sink là API bên thứ ba thì đạt được đảm bảo nào?**
> - **Idempotency key ở API**: API nhận một key và tự bỏ qua request lặp có cùng key.
>
> Quy tắc: engine không kiểm soát được hiệu ứng bên ngoài, nên đảm bảo cuối cùng phụ thuộc vào API. Nếu API hỗ trợ idempotency key, engine gửi một key ổn định cho mỗi event, và kết quả như exactly-once. Nếu không, gọi lặp là không tránh được: engine at-least-once có thể gọi hai lần; engine at-most-once có thể bỏ sót lần gọi.
>
> Ranh giới: key phải ổn định qua mọi lần xử lý lại, nên được rút ra từ event (ID, toạ độ offset), không được sinh ngẫu nhiên lúc gọi.

## Hiểu nhầm thường gặp
- **"Đã dùng transaction Kafka thì DB cũng exactly-once."** Ghi DB nằm ngoài transaction Kafka.
- **"Upsert giải quyết mọi trùng lặp."** Upsert chỉ đúng khi event mang trạng thái đầy đủ. Event mang thay đổi cộng dồn thì upsert vô nghĩa.
- **"Event ID duy nhất là đủ khử mọi trùng."** Nó khử được trùng do xử lý lại, không khử được trùng do nguồn phát hai event khác nhau cho cùng một việc.
- **"Lưu offset trong DB thì không cần quan tâm committed offset của Kafka."** Công cụ đo lag và vận hành nhìn committed offset của Kafka; không commit lên đó thì mất khả năng quan sát.

## Liên quan
- [05-delivery-semantics.md](05-delivery-semantics.md): phạm vi exactly-once của Kafka và vì sao at-least-once là mặc định.
- [07-errors-retry-and-dlq.md](07-errors-retry-and-dlq.md): ghi sang retry/DLQ là một dual write.
- [08-parallelism-and-ordering.md](08-parallelism-and-ordering.md): xử lý lệch thứ tự ảnh hưởng tới khử trùng theo offset.
- [13-observability-and-operations.md](13-observability-and-operations.md): replay chỉ an toàn khi sink idempotent.
