# Schema và serialization

> Kafka chỉ lưu byte. Việc biến event thành byte (**serialize**) và ngược lại (**deserialize**) là của producer và consumer, theo một **schema** mô tả cấu trúc dữ liệu. **Schema registry** lưu các phiên bản schema và gán ID cho chúng. Mỗi record mang ID của schema đã dùng để ghi nó. **Compatibility mode** quy định schema mới được phép khác schema cũ tới đâu, và qua đó quyết định producer hay consumer phải nâng cấp trước.

## Tại sao cần biết
Producer và consumer được deploy độc lập, vào những thời điểm khác nhau, và log giữ dữ liệu cũ hàng ngày hoặc hàng tuần. Vì vậy consumer luôn phải đọc được cả dữ liệu ghi theo schema cũ lẫn schema mới. Thêm một trường bắt buộc, đổi kiểu một trường hay đổi tên một trường có thể làm mọi consumer cũ lỗi giải mã đồng loạt. Tầng decode cũng là nơi sinh ra loại poison message phổ biến nhất (xem [07-errors-retry-and-dlq.md](07-errors-retry-and-dlq.md)).

## Khái niệm cốt lõi

### Serialization format
| Định dạng | Là gì | Đặc điểm |
|---|---|---|
| JSON | Văn bản, tự mô tả bằng tên trường | Dễ đọc, không cần schema để giải mã; tốn byte và CPU; kiểu dữ liệu lỏng (số, ngày tháng) |
| Avro | Nhị phân, cần schema để giải mã; dữ liệu không chứa tên trường | Gọn; quy tắc tiến hoá schema rõ ràng (trường có giá trị mặc định); phổ biến trong hệ sinh thái JVM |
| Protobuf | Nhị phân, trường đánh số; code được sinh từ file `.proto` | Gọn, nhanh; trường định danh bằng số nên đổi tên an toàn; phổ biến với Go |
| JSON Schema | JSON kèm một schema để kiểm tra | Giữ tính dễ đọc của JSON, thêm kiểm tra cấu trúc |

- **Dùng để**: chọn đánh đổi giữa dễ đọc, kích thước, tốc độ và mức kiểm soát khi tiến hoá.

### Schema
- **Là gì**: bản mô tả cấu trúc của event: có những trường nào, kiểu gì, trường nào bắt buộc, giá trị mặc định là gì.
- **Dùng để**: một hợp đồng giữa producer và consumer. Có schema thì dữ liệu sai cấu trúc bị phát hiện ngay lúc ghi, thay vì làm lỗi hàng loạt consumer về sau.

### Schema registry
- **Là gì**: dịch vụ lưu các phiên bản schema, gán cho mỗi schema một ID duy nhất, và kiểm tra tính tương thích khi có phiên bản mới.
- **Subject**: tên nhóm các phiên bản của một schema, thường theo topic (ví dụ `orders-value`). Kiểm tra tương thích được thực hiện trong một subject.
- **Dùng để**: tách schema khỏi dữ liệu. Record chỉ mang ID (vài byte) thay vì cả schema; consumer tra ID để lấy đúng schema đã dùng khi ghi.

### Wire format
- **Là gì**: cách đóng gói byte của value khi dùng schema registry theo quy ước phổ biến:

  ```
  byte 0      : magic byte = 0
  byte 1..4   : schema ID, số nguyên 4 byte big-endian
  (Protobuf)  : chỉ số message trong file .proto
  phần còn lại: dữ liệu đã serialize
  ```

- **Dùng để**: consumer đọc 5 byte đầu là biết phải giải mã bằng schema nào. Một biến thể khác đặt định danh schema vào header của record thay vì tiền tố của value, để value giữ nguyên dạng thuần.

### Compatibility mode
| Mode | Là gì | Ai nâng cấp trước |
|---|---|---|
| BACKWARD | Consumer dùng schema mới đọc được dữ liệu ghi bằng schema *ngay trước đó* | Consumer trước, rồi mới tới producer |
| FORWARD | Consumer dùng schema cũ đọc được dữ liệu ghi bằng schema mới | Producer trước |
| FULL | Cả BACKWARD lẫn FORWARD | Thứ tự nào cũng được |
| *_TRANSITIVE | Như trên, nhưng với *mọi* phiên bản cũ chứ không chỉ phiên bản ngay trước | Theo mode gốc |
| NONE | Không kiểm tra | Tự chịu trách nhiệm |

- **Dùng để**: registry từ chối đăng ký schema mới vi phạm mode, nên lỗi được bắt lúc deploy thay vì lúc chạy. Mode mặc định phổ biến là BACKWARD.
- Mode không transitive chỉ so với phiên bản ngay trước. Consumer phải đọc lại dữ liệu từ đầu topic (replay) sẽ gặp mọi phiên bản cũ, nên chỉ mode transitive mới đảm bảo đọc được tất cả.

### Thay đổi an toàn và không an toàn (khái quát)
- **Thường an toàn**: thêm trường tuỳ chọn có giá trị mặc định; xoá trường tuỳ chọn (tuỳ mode); với Protobuf, đổi tên trường mà giữ số hiệu.
- **Thường không an toàn**: thêm trường bắt buộc không có mặc định; đổi kiểu trường; dùng lại số hiệu đã xoá (Protobuf); đổi tên trường (Avro, JSON).
- Quy tắc chi tiết khác nhau theo định dạng và mode, nên registry là nơi quyết định cuối cùng.

## Cách hoạt động

```
producer:  event ──► serializer: tra/đăng ký schema ──► [0][schema ID][dữ liệu] ──► topic
                                    │
                               schema registry  (subject: orders-value; v1 → ID 41, v2 → ID 58)
                                    │
consumer:  [0][58][dữ liệu] ──► đọc ID 58 ──► cache decoder theo ID (tra registry lần đầu)
                                          ──► giải mã thành struct
                                          ──► ID lạ / giải mã lỗi ──► DLQ (poison), không làm vòng poll crash
```

Tầng decode của engine thường làm ba việc:
1. **Cache decoder theo schema ID**, vì tra registry cho mỗi record là quá đắt.
2. **Coi record không giải mã được là poison**: đưa vào DLQ kèm lý do, rồi đi tiếp (xem [07-errors-retry-and-dlq.md](07-errors-retry-and-dlq.md)).
3. **Tách giải mã khỏi vòng poll** khi throughput cao, vì giải mã tốn CPU và cấp phát bộ nhớ (xem [09-backpressure-and-throughput.md](09-backpressure-and-throughput.md)).

## Ví dụ

Subject `orders-value` ở mode BACKWARD. Phiên bản 1 có các trường `id`, `amount`. Phiên bản 2 thêm `currency` với mặc định `"VND"`.

| Tình huống | Kết quả |
|---|---|
| Consumer v2 đọc record ghi bằng v1 | Đọc được, `currency` nhận mặc định `"VND"` |
| Consumer v1 đọc record ghi bằng v2 | Tuỳ định dạng: Avro bỏ qua trường lạ khi giải mã bằng schema của consumer; nhưng mode BACKWARD *không đảm bảo* điều này |
| Đăng ký v3 thêm `customer_id` bắt buộc, không mặc định | Registry từ chối: consumer v3 không đọc được record v2 (thiếu trường) |

Thứ tự deploy an toàn ở BACKWARD: nâng cấp mọi consumer lên v2 trước, rồi mới cho producer ghi v2.

## Câu hỏi

**Schema registry dùng để làm gì?**
> - **Schema**: hợp đồng cấu trúc giữa producer và consumer.
> - **Schema ID**: định danh một phiên bản schema, gắn vào mỗi record.
>
> Quy tắc: registry tách schema khỏi dữ liệu và kiểm tra hợp đồng tại thời điểm thay đổi. Record chỉ mang ID, consumer tra ID để giải mã bằng đúng schema đã dùng khi ghi. Schema mới vi phạm compatibility mode bị từ chối ngay lúc đăng ký, nên thay đổi phá vỡ không lọt được vào topic.
>
> Ranh giới: registry chỉ bảo vệ khi mọi producer đều đi qua nó. Producer ghi thẳng byte (bỏ qua serializer) vẫn có thể đưa dữ liệu sai vào topic. Consumer phải xử lý trường hợp đó như poison message.

**Compatibility mode BACKWARD và FORWARD khác nhau thế nào? Ai phải nâng cấp trước?**
> - **BACKWARD**: schema mới đọc được dữ liệu cũ.
> - **FORWARD**: schema cũ đọc được dữ liệu mới.
>
> Quy tắc: mode xác định *bên nào được phép đi trước*. Ở BACKWARD, consumer mới đọc được dữ liệu cũ, nên nâng cấp consumer trước, rồi tới producer. Ở FORWARD, consumer cũ đọc được dữ liệu mới, nên producer đi trước. FULL cho phép thứ tự bất kỳ, đổi lại tập thay đổi được phép hẹp hơn.
>
> Ranh giới: các mode không transitive chỉ đảm bảo với phiên bản *ngay trước*. Engine cần replay từ đầu topic, hoặc topic giữ dữ liệu lâu qua nhiều phiên bản, cần mode transitive.

**Vì sao record không giải mã được thường được đưa vào DLQ thay vì retry?**
> - **Poison message**: record lỗi vĩnh viễn, xử lý lại bao nhiêu lần cũng lỗi.
>
> Quy tắc: lỗi giải mã là lỗi của *dữ liệu*, không phải của môi trường, nên retry không thay đổi kết quả. Engine đưa record vào DLQ kèm schema ID và lý do, rồi đi tiếp, để một record hỏng không chặn partition.
>
> Ranh giới: có một ngoại lệ là registry tạm thời không truy cập được. Lúc đó lỗi tra schema là lỗi tạm thời, không phải poison, và phải được retry. Phân biệt "ID không tồn tại" với "không gọi được registry" là việc của tầng decode.

**JSON, Avro và Protobuf nên chọn theo tiêu chí nào?**
> - **JSON**: văn bản tự mô tả.
> - **Avro, Protobuf**: nhị phân, cần schema.
>
> Tiêu chí: JSON hợp khi con người cần đọc trực tiếp, lưu lượng thấp, và nhiều bên không chung công cụ. Avro và Protobuf hợp khi throughput cao (gọn hơn, giải mã nhanh hơn) và cần quy tắc tiến hoá chặt. Giữa hai loại nhị phân, khác biệt chính là hệ sinh thái và cách định danh trường: Avro gắn chặt với hệ JVM và các framework stream; Protobuf có code sinh tốt cho nhiều ngôn ngữ (trong đó có Go), và định danh trường bằng số nên đổi tên an toàn.
>
> Ranh giới: JSON vẫn dùng được với schema registry (JSON Schema) khi cần kiểm tra cấu trúc mà vẫn giữ dạng văn bản.

## Hiểu nhầm thường gặp
- **"Kafka kiểm tra cấu trúc dữ liệu."** Kafka chỉ thấy byte. Kiểm tra là việc của serializer và registry.
- **"Thêm trường thì luôn an toàn."** Thêm trường bắt buộc không có mặc định phá BACKWARD.
- **"BACKWARD nghĩa là mọi consumer cũ vẫn chạy."** BACKWARD đảm bảo consumer *mới* đọc được dữ liệu cũ, không đảm bảo consumer *cũ* đọc được dữ liệu mới.
- **"Lỗi tra registry là poison."** Nếu do registry không truy cập được thì đó là lỗi tạm thời.

## Liên quan
- [02-kafka-log-model.md](02-kafka-log-model.md): value và header của record.
- [07-errors-retry-and-dlq.md](07-errors-retry-and-dlq.md): poison message và DLQ.
- [09-backpressure-and-throughput.md](09-backpressure-and-throughput.md): chi phí giải mã ở throughput cao.
- [13-observability-and-operations.md](13-observability-and-operations.md): replay đòi đọc được mọi phiên bản schema cũ.
