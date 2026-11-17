# Deployment strategies

> Chiến lược deploy là cách thay phiên bản đang chạy bằng phiên bản mới: thay tất cả một lúc, thay dần từng phần, dựng một môi trường song song rồi chuyển traffic, hay cho một nhóm nhỏ người dùng thử trước. Mỗi cách đánh đổi giữa thời gian downtime, chi phí tài nguyên, tốc độ rollback và phạm vi ảnh hưởng khi bản mới có lỗi.

## Tại sao cần biết
Pipeline CI/CD ([08-ci-cd.md](08-ci-cd.md)) tạo ra artifact đã test, nhưng test không bắt được hết lỗi. Có những lỗi chỉ lộ ra với traffic và dữ liệu thật. Chiến lược deploy quyết định khi bản mới có lỗi thì bao nhiêu người dùng bị ảnh hưởng và mất bao lâu để quay lại. Đây là lớp an toàn cho phép deploy thường xuyên ([01-devops-culture.md](01-devops-culture.md)), và ảnh hưởng trực tiếp đến hai chỉ số DORA: change fail rate và failed deployment recovery time.

## Khái niệm cốt lõi

### Deploy và release
- **Deploy** — **Là gì:** đưa phiên bản code mới lên hạ tầng và cho nó chạy.
- **Release** — **Là gì:** cho người dùng thực sự dùng tính năng mới.
- **Dùng để (tách hai việc):** deploy thường xuyên mà không bật tính năng ngay. Code mới có thể nằm trên production nhiều ngày ở trạng thái tắt, tới khi kinh doanh quyết định bật.

### Recreate
- **Là gì:** dừng toàn bộ phiên bản cũ rồi chạy phiên bản mới.
- **Dùng để:** trường hợp hai phiên bản *không được* chạy cùng lúc (vd schema thay đổi không tương thích, license chỉ cho một bản). Có downtime.

### Rolling update
- **Là gì:** thay dần từng nhóm instance cũ bằng instance mới. Mỗi nhóm mới phải sẵn sàng (qua health check/readiness) thì mới thay tiếp nhóm sau. Đây là mặc định của Deployment trong Kubernetes ([05-kubernetes.md](05-kubernetes.md)).
- **Dùng để:** không downtime, gần như không tốn thêm tài nguyên. Đổi lại là trong lúc rollout, hai phiên bản cùng phục vụ traffic, và rollback cũng là một lần rolling update ngược lại nên không tức thì.

### Blue-green
- **Là gì:** chạy hai môi trường giống hệt nhau. **Blue** đang phục vụ, **green** được deploy bản mới và kiểm tra. Khi green ổn thì chuyển *toàn bộ* traffic sang green (đổi target của load balancer hoặc selector của Service). Blue được giữ lại để quay về.
- **Dùng để:** chuyển và rollback gần như tức thì (chỉ là đổi con trỏ traffic), kiểm tra bản mới trên hạ tầng thật trước khi người dùng thấy. Đổi lại là tốn gấp đôi tài nguyên trong lúc chuyển, và mọi người dùng chuyển sang bản mới cùng một lúc.

### Canary
- **Là gì:** đưa một phần nhỏ traffic (vd 1%, rồi 5%, 25%, 100%) sang bản mới, so sánh metric của canary với bản cũ (tỷ lệ lỗi, latency) ở mỗi bước rồi mới tăng tiếp. Tên lấy từ chim hoàng yến mà thợ mỏ mang xuống hầm để phát hiện khí độc sớm.
- **Dùng để:** giới hạn phạm vi ảnh hưởng (blast radius) khi bản mới có lỗi: lỗi chỉ chạm 1% người dùng, và được phát hiện bằng dữ liệu thật.
- **Progressive delivery** — **Là gì:** tự động hoá canary. Công cụ (Argo Rollouts, Flagger) tự tăng traffic theo bước, tự đọc metric, và tự rollback khi vượt ngưỡng.

### Shadow (mirroring)
- **Là gì:** sao chép traffic thật gửi tới bản mới, nhưng bỏ đi phản hồi của bản mới. Người dùng chỉ nhận phản hồi từ bản cũ.
- **Dùng để:** thử hiệu năng và độ đúng của bản mới với tải thật mà không có rủi ro cho người dùng. Phải cẩn thận với request có tác dụng phụ (ghi database, gửi email, trừ tiền).

### Feature flag
- **Là gì:** điều kiện trong code (`if flags.enabled("new-checkout", user)`) mà giá trị được đổi lúc chạy, không cần deploy lại.
- **Dùng để:** tách release khỏi deploy, bật dần theo nhóm người dùng, tắt ngay một tính năng lỗi (kill switch), merge code chưa xong vào `main` mà vẫn giấu nó đi (hỗ trợ trunk-based development).
- **A/B testing** — **Là gì:** chia người dùng thành nhóm thấy hai biến thể để đo biến thể nào tốt hơn về *kinh doanh* (tỷ lệ chuyển đổi). Khác canary, vốn đo sức khoẻ *kỹ thuật* của bản mới.

### Rollback và roll forward
- **Rollback** — **Là gì:** quay lại phiên bản trước đã biết là chạy tốt. **Dùng để:** khôi phục nhanh khi chưa biết nguyên nhân lỗi.
- **Roll forward** — **Là gì:** sửa lỗi rồi deploy một phiên bản mới hơn. **Dùng để:** khi rollback không còn khả thi (dữ liệu đã đổi theo cách bản cũ không đọc được) hoặc khi bản sửa nhỏ, chắc chắn và pipeline đủ nhanh.

### Migration database: expand and contract
- **Là gì:** cách đổi schema thành nhiều bước, mỗi bước đều tương thích với cả phiên bản code trước lẫn phiên bản sau (còn gọi là *parallel change*):
  1. **Expand**: thêm cấu trúc mới (cột, bảng) nhưng chưa xoá cái cũ. Code cũ vẫn chạy.
  2. **Migrate**: deploy code ghi vào cả cũ lẫn mới, chép dữ liệu cũ sang (backfill), rồi chuyển sang đọc từ cấu trúc mới.
  3. **Contract**: khi không còn code nào dùng cấu trúc cũ thì xoá nó đi.
- **Dùng để:** đổi schema mà không downtime, và vẫn rollback được code ở mỗi bước.

### Graceful shutdown và connection draining
- **Là gì:** khi một instance sắp bị thay, nó ngừng nhận request mới (bị rút khỏi load balancer), xử lý nốt các request đang chạy, rồi mới thoát. Kubernetes gửi `SIGTERM` và chờ một khoảng (mặc định 30 giây, `terminationGracePeriodSeconds`) rồi mới `SIGKILL`.
- **Dùng để:** không làm rơi request đang dở trong lúc deploy. Thiếu bước này thì rolling update "không downtime" vẫn trả lỗi 5xx cho một số người dùng.

## Cách hoạt động
So sánh các chiến lược, giả sử chạy 4 instance:

```
 Recreate     v1 v1 v1 v1 → (không có gì: downtime) → v2 v2 v2 v2

 Rolling      v1 v1 v1 v1 → v2 v1 v1 v1 → v2 v2 v1 v1 → v2 v2 v2 v1 → v2 v2 v2 v2
              (mỗi bước chờ instance mới Ready mới đi tiếp)

 Blue-green   LB → [blue: v1 ×4]     [green: v2 ×4] đang kiểm tra
              LB →  blue: v1 ×4  ──► [green: v2 ×4]    (đổi một lần 100%, giữ blue để quay về)

 Canary       traffic: v1 99% / v2 1% → 90/10 → 50/50 → 0/100
              mỗi bước: so error rate, latency của v2 với v1 → đạt thì tăng tiếp, xấu thì về 0%
```

| | Downtime | Tài nguyên thêm | Tốc độ rollback | Phạm vi ảnh hưởng khi lỗi | Hai phiên bản chạy cùng lúc |
|---|---|---|---|---|---|
| Recreate | Có | Không | Chậm (deploy lại) | 100% | Không |
| Rolling | Không | Ít (`maxSurge`) | Trung bình | Tăng dần tới 100% | Có |
| Blue-green | Không | Gấp đôi lúc chuyển | Tức thì | 100% ngay khi chuyển | Không (chỉ một bên nhận traffic) |
| Canary | Không | Ít | Nhanh | Nhỏ, có kiểm soát | Có |

## Ví dụ
Đổi tên cột `users.fullname` thành `users.display_name` mà không downtime, theo expand and contract:

| Bước | Thay đổi | Code đang chạy | Rollback code được không? |
|---|---|---|---|
| 1. Expand | `ALTER TABLE users ADD COLUMN display_name text` | v1 (chỉ biết `fullname`) | Được, v1 bỏ qua cột mới |
| 2. Ghi kép | Deploy v2: ghi cả hai cột, vẫn đọc `fullname` | v2 | Được, về v1 |
| 3. Backfill | `UPDATE users SET display_name = fullname WHERE display_name IS NULL` (chạy theo lô) | v2 | Được |
| 4. Đổi chỗ đọc | Deploy v3: đọc `display_name`, vẫn ghi cả hai | v3 | Được, về v2 |
| 5. Ngừng ghi cũ | Deploy v4: chỉ dùng `display_name` | v4 | Được, về v3 (`fullname` cũ còn đó, chỉ thiếu dữ liệu mới) |
| 6. Contract | `ALTER TABLE users DROP COLUMN fullname` | v4 | Từ đây không còn về bản trước v4 được |

Làm một lần `RENAME COLUMN` thì nhanh, nhưng trong lúc rolling update, các instance v1 còn chạy sẽ lỗi ngay vì không thấy cột `fullname`.

## Câu hỏi

**Rolling, blue-green và canary khác nhau ở đâu, chọn thế nào?**
> - **Rolling**: thay dần từng instance.
> - **Blue-green**: hai môi trường đầy đủ, chuyển traffic một lần.
> - **Canary**: chuyển dần *traffic* theo tỷ lệ, có kiểm tra metric ở từng bước.
>
> Các chiến lược khác nhau ở *đơn vị chuyển* (instance hay traffic), *tốc độ chuyển* (từng phần hay một lần) và *cách quyết định đi tiếp* (health check hay so sánh metric). Tiêu chí chọn: cần rollback tức thì và chịu được gấp đôi tài nguyên thì chọn blue-green; cần giới hạn số người dùng bị ảnh hưởng và có metric đủ tốt để so sánh thì chọn canary; muốn đơn giản, ít tài nguyên, chấp nhận rollback mất vài phút thì chọn rolling.
>
> Ranh giới: rolling và canary đều làm hai phiên bản phục vụ cùng lúc, nên API và schema phải tương thích ngược. Blue-green tránh được việc này ở tầng code nhưng không tránh được ở database dùng chung.

**Canary quyết định "đi tiếp" hay "quay lại" dựa vào đâu?**
> - **Canary analysis**: so sánh metric của nhóm canary với nhóm đang chạy bản cũ (baseline) trong cùng khoảng thời gian.
> - **SLI**: chỉ số đo chất lượng dịch vụ như tỷ lệ lỗi, latency ([11-sre-and-incident-management.md](11-sre-and-incident-management.md)).
>
> Quyết định dựa trên *so sánh tương đối* giữa canary và baseline cùng lúc, không dựa trên một ngưỡng tuyệt đối. So cùng lúc thì loại được ảnh hưởng của giờ cao điểm hay sự cố hạ tầng chung. Metric thường dùng là tỷ lệ lỗi 5xx, latency p99, và cả metric kinh doanh (số đơn đặt thành công). Mỗi bước giữ đủ lâu và đủ traffic để khác biệt có ý nghĩa thống kê.
>
> Ranh giới: lỗi chỉ xuất hiện với một nhóm hiếm (một loại thiết bị, một quốc gia) có thể không lộ ra ở 1% traffic. Lỗi dữ liệu chậm (ghi sai mà vài giờ sau mới bị phát hiện) thì canary ngắn không bắt được.

**Feature flag dùng để làm gì, có khác canary không?**
> - **Feature flag**: công tắc lúc chạy, bật tắt từng tính năng mà không deploy lại.
> - **Canary**: chuyển một phần traffic sang *phiên bản* mới.
>
> Tiêu chí phân biệt là đơn vị kiểm soát: canary kiểm soát theo *phiên bản artifact* (cả bản mới), feature flag kiểm soát theo *từng tính năng* bên trong cùng một artifact. Vì vậy flag tách được release khỏi deploy, tắt được một tính năng lỗi mà không động tới các thay đổi khác, và bật được theo nhóm người dùng (nhân viên nội bộ trước, rồi 10% khách hàng). Hai thứ thường dùng cùng nhau.
>
> Ranh giới: flag là nợ kỹ thuật. Flag cũ không được dọn làm code đầy nhánh `if` và tổ hợp trạng thái không ai test. Mỗi flag release nên có ngày gỡ.

**Bản mới đã chạy migration database, rollback thế nào?**
> - **Migration**: thay đổi schema hoặc dữ liệu đi kèm một phiên bản code.
> - **Tương thích ngược (backward compatible)**: schema mới vẫn chạy được với code cũ.
>
> Code rollback được, còn dữ liệu và schema thường không quay lại được. Vì vậy quy tắc là: mỗi migration phải tương thích với cả phiên bản code trước nó, và mỗi bước phá vỡ (xoá cột, đổi kiểu) được tách ra làm sau, khi không còn code nào dùng tới (expand and contract). Làm vậy thì rollback code luôn an toàn, vì schema hiện tại vẫn chạy được với bản cũ.
>
> Ranh giới: migration "down" (đảo migration) hiếm khi cứu được production, vì dữ liệu ghi theo schema mới trong lúc đó có thể mất khi đảo. Coi migration là chỉ đi tiến, và chỉ có bước contract là điểm không quay lại.

**Khi nào nên rollback, khi nào nên roll forward?**
> - **Rollback**: quay về bản trước đã biết là tốt.
> - **Roll forward**: deploy một bản mới có sửa lỗi.
>
> Mặc định ưu tiên khôi phục trước, tìm nguyên nhân sau: chưa rõ lỗi do đâu thì rollback, vì bản trước đã được chứng minh trên production. Roll forward hợp lý khi rollback không an toàn (đã có thay đổi dữ liệu mà bản cũ không hiểu), hoặc khi lỗi đã rõ, bản sửa nhỏ và pipeline đủ nhanh để bản sửa lên trong vài phút.
>
> Ranh giới: "sửa nóng ngay trên production" bằng cách bỏ qua pipeline không phải roll forward. Đó là đánh cược thêm một thay đổi chưa test vào một hệ thống đang có sự cố.

## Hiểu nhầm thường gặp
- **"Rolling update là không downtime."** Chỉ đúng khi readiness probe chính xác, app xử lý `SIGTERM` để dừng gọn, và hai phiên bản tương thích với nhau.
- **"Blue-green giải quyết luôn chuyện database."** Hai môi trường thường dùng chung một database. Schema vẫn phải tương thích với cả blue lẫn green.
- **"Canary 1% thì an toàn tuyệt đối."** 1% của một triệu người dùng là mười nghìn người. Canary giảm blast radius chứ không xoá nó. Request làm thay đổi dữ liệu vẫn để lại hậu quả.
- **"Feature flag chỉ là `if` trong code."** Flag cần hệ thống quản lý: ai đổi, đổi lúc nào, giá trị theo nhóm người dùng, và có lịch gỡ.

## Liên quan
- [05-kubernetes.md](05-kubernetes.md): Deployment, rolling update, probe, rollout undo.
- [08-ci-cd.md](08-ci-cd.md): bước deploy cuối của pipeline.
- [10-monitoring-and-observability.md](10-monitoring-and-observability.md): metric dùng để quyết định canary.
- [../backend/10-databases.md](../backend/10-databases.md): schema, transaction, lock, những thứ ảnh hưởng tới migration.
