# High availability and disaster recovery

> High availability (HA) là thiết kế để hệ thống tiếp tục phục vụ khi một thành phần hỏng, bằng cách có bản dự phòng và tự chuyển sang nó. Disaster recovery (DR) là khả năng khôi phục khi sự cố lớn vượt quá sức chịu của HA (mất cả một region, dữ liệu bị xoá hay bị mã hoá tống tiền), đo bằng hai chỉ số RPO và RTO.

## Tại sao cần biết
Mọi thứ đều sẽ hỏng: disk, máy, AZ, cả region, và cả con người khi gõ nhầm lệnh xoá. Câu hỏi không phải "có hỏng không" mà là "hỏng thì người dùng có thấy không, và mất bao nhiêu dữ liệu". HA và DR biến SLO ([11-sre-and-incident-management.md](11-sre-and-incident-management.md)) thành kiến trúc cụ thể. Các khối xây dựng đã có ở các file trước: load balancer và health check ([03](03-networking-for-ops.md)), nhiều AZ ([06](06-cloud-fundamentals.md)), Deployment và HPA ([05](05-kubernetes.md)), IaC để dựng lại hạ tầng ([07](07-terraform-and-iac.md)).

## Khái niệm cốt lõi

### Availability và single point of failure
- **Availability** — **Là gì:** tỷ lệ thời gian (hoặc request) mà hệ thống phục vụ đúng. Thường nói theo "số 9": 99,9% ("ba số 9"), 99,99% ("bốn số 9"). Bảng quy đổi ra phút downtime ở [11-sre-and-incident-management.md](11-sre-and-incident-management.md#ví-dụ).
- **Single point of failure (SPOF)** — **Là gì:** thành phần mà nếu nó hỏng thì cả hệ thống ngừng. **Dùng để (cần tìm ra):** mỗi SPOF là giới hạn trên của availability. Một database duy nhất, một NAT gateway duy nhất, một người duy nhất biết cách deploy đều là SPOF.

### Redundancy và failover
- **Redundancy** — **Là gì:** có nhiều bản của cùng một thành phần. **Dùng để:** một bản hỏng thì còn bản khác.
  - **Active-active**: mọi bản cùng phục vụ traffic. Một bản hỏng thì các bản còn lại gánh thêm. Không mất thời gian chuyển, nhưng phải có đủ dư công suất (vd 3 bản chạy ở mức 66% thì mất một bản, hai bản còn lại phải gánh 100%).
  - **Active-passive (standby)**: một bản phục vụ, bản kia chờ. Hỏng thì chuyển sang bản chờ. Đơn giản hơn (nhất là với database ghi), nhưng mất thời gian chuyển và tốn tài nguyên cho bản ngồi chờ.
- **Failover** — **Là gì:** quá trình phát hiện thành phần chính hỏng và chuyển vai trò sang bản dự phòng. Cần ba thứ: **phát hiện** (health check, heartbeat), **quyết định** (ai được nâng lên, tránh việc có hai bản cùng nghĩ mình là chính, gọi là *split-brain*), và **chuyển hướng** (đổi DNS, đổi target của load balancer, đổi địa chỉ IP).

### Availability của chuỗi phụ thuộc
- Thành phần **nối tiếp** (request phải đi qua tất cả): availability bằng **tích** các availability. Ba thành phần 99,9% nối tiếp: 0,999³ ≈ 99,7%.
- Thành phần **song song** (chỉ cần một bản sống): availability bằng `1 − (1 − a)^n`. Hai bản 99% song song: 1 − 0,01² = 99,99%.
- Hệ quả: thêm phụ thuộc cứng làm availability *giảm*, thêm bản dự phòng độc lập làm availability *tăng*. Giả định "độc lập" rất quan trọng: hai bản cùng AZ, cùng phiên bản lỗi, hay cùng một file config sai sẽ hỏng cùng lúc.

### Scale dọc, scale ngang, autoscaling
- **Vertical scaling (scale up)** — **Là gì:** tăng cấu hình một máy (thêm CPU, RAM). **Dùng để:** đơn giản, không phải sửa ứng dụng. Có trần phần cứng, thường phải restart, và vẫn là một máy, tức vẫn là SPOF.
- **Horizontal scaling (scale out)** — **Là gì:** thêm máy chạy song song phía sau load balancer. **Dùng để:** tăng sức chịu gần như không giới hạn và có luôn redundancy. Đòi hỏi ứng dụng **stateless**: trạng thái (session, file) nằm ở database hay cache dùng chung, không nằm trong RAM hay disk của từng instance.
- **Autoscaling** — **Là gì:** tự thêm hoặc bớt instance theo một metric so với mục tiêu. Có nhiều tầng: Pod (HPA trong Kubernetes), node (Cluster Autoscaler, Karpenter), VM (Auto Scaling Group). **Dùng để:** theo kịp tải mà không phải trả tiền cho công suất thừa lúc vắng. HPA tính số replica cần có theo tỷ lệ: `desired = ceil(current × giá_trị_hiện_tại / giá_trị_mục_tiêu)`.

### Chống lan sự cố
- **Timeout** — **Là gì:** giới hạn thời gian chờ một lời gọi. **Dùng để:** service chậm phía sau không giữ tài nguyên của service gọi vô thời hạn.
- **Retry với exponential backoff và jitter** — **Là gì:** thử lại sau khoảng chờ tăng dần (1 s, 2 s, 4 s...) cộng thêm một độ lệch ngẫu nhiên. **Dùng để:** vượt qua lỗi tạm thời mà không làm hàng nghìn client thử lại *cùng lúc* (thundering herd). Chỉ retry thao tác idempotent.
- **Circuit breaker** — **Là gì:** khi tỷ lệ lỗi tới một phụ thuộc vượt ngưỡng thì "ngắt mạch": trả lỗi ngay, không gọi nữa trong một khoảng, sau đó thử lại vài lời gọi. **Dùng để:** để phụ thuộc đang hỏng có thời gian hồi phục, và để service gọi không bị kéo sập theo.
- **Graceful degradation** — **Là gì:** khi một phần hỏng thì vẫn phục vụ phần còn lại ở mức giảm (ẩn phần gợi ý sản phẩm nhưng vẫn cho thanh toán). **Load shedding** — **Là gì:** chủ động từ chối bớt request khi quá tải. **Dùng để:** phục vụ tốt *một phần* người dùng thay vì phục vụ tệ *tất cả*.

### Replication
- **Là gì:** sao chép dữ liệu từ bản chính sang các bản phụ (replica).
  - **Synchronous**: bản chính chỉ báo ghi thành công khi replica đã nhận. Không mất dữ liệu khi failover, nhưng tăng latency của mỗi lần ghi.
  - **Asynchronous**: bản chính báo thành công ngay, replica nhận sau. Nhanh, nhưng failover có thể mất các thay đổi chưa kịp chép (replication lag).
- **Dùng để:** HA cho database (failover sang replica), chia tải đọc (read replica).

### Backup
- **Là gì:** bản sao dữ liệu tại một thời điểm, lưu tách biệt khỏi hệ thống đang chạy, giữ theo lịch (giữ 7 bản hằng ngày, 4 bản hằng tuần...).
- **Dùng để:** khôi phục về một thời điểm trước khi dữ liệu bị hỏng, bị xoá nhầm hay bị mã hoá tống tiền. **Replication không phải backup:** lệnh `DELETE` nhầm được chép sang replica ngay lập tức.
- **Quy tắc 3-2-1**: ít nhất 3 bản dữ liệu, trên 2 loại phương tiện khác nhau, 1 bản để ở nơi khác (khác region, khác tài khoản). Ngày nay hay thêm yêu cầu một bản **immutable** (không ai, kể cả admin, xoá được trước hạn) để chống ransomware.
- **Point-in-time recovery (PITR)** — **Là gì:** khôi phục về một thời điểm bất kỳ nhờ có backup đầy đủ cộng log giao dịch liên tục (WAL, binlog).

### RPO và RTO
- **RPO (Recovery Point Objective)** — **Là gì:** lượng dữ liệu tối đa được phép mất, đo bằng thời gian. RPO 1 giờ nghĩa là chấp nhận mất tối đa 1 giờ dữ liệu gần nhất. **Dùng để:** quyết định tần suất backup và kiểu replication.
- **RTO (Recovery Time Objective)** — **Là gì:** thời gian tối đa từ lúc sự cố tới lúc dịch vụ chạy lại. **Dùng để:** quyết định chiến lược DR, tức chuẩn bị sẵn bao nhiêu hạ tầng.

```
   lần backup cuối              sự cố                     dịch vụ chạy lại
        │◄────── RPO ──────────►│◄──────── RTO ──────────────►│
   dữ liệu trong khoảng này      thời gian người dùng
   có thể bị mất                 không dùng được dịch vụ
```

### Chiến lược DR
Theo mức chuẩn bị sẵn ở nơi dự phòng (thường là một region khác), từ rẻ tới đắt:

| Chiến lược | Ở nơi dự phòng có gì | RPO / RTO điển hình | Chi phí |
|---|---|---|---|
| **Backup and restore** | Chỉ có backup. Hạ tầng dựng lại bằng IaC khi cần | Giờ / giờ tới ngày | Thấp nhất |
| **Pilot light** | Dữ liệu được replicate liên tục, hạ tầng lõi tối thiểu, app chưa chạy | Phút / hàng chục phút tới giờ | Thấp |
| **Warm standby** | Bản thu nhỏ của toàn hệ thống đang chạy, khi cần thì scale lên | Giây tới phút / phút | Trung bình |
| **Multi-site active-active** | Hệ thống đầy đủ chạy và phục vụ traffic ở nhiều nơi | Gần 0 / gần 0 | Cao nhất |

## Cách hoạt động
Failover của một database có primary và standby:

```
  bình thường:  app ──► [endpoint db] ──► primary (AZ a) ══sync══► standby (AZ b)

  primary hỏng:
   1. Health check / heartbeat báo primary không trả lời trong N giây
   2. Bộ điều phối xác nhận primary thật sự chết (tránh split-brain)
   3. Nâng standby lên làm primary mới
   4. Trỏ endpoint (DNS hoặc proxy) sang primary mới
   5. App kết nối lại: có vài chục giây lỗi kết nối → cần retry
   6. Dựng standby mới từ primary mới để có lại redundancy
```

Bước 5 cho thấy HA vẫn có một khoảng gián đoạn ngắn, nên ứng dụng phải biết retry. Bước 6 thường bị quên: sau failover, hệ thống tạm thời không còn dự phòng, một sự cố nữa là sập.

## Ví dụ
Một hệ thống thương mại điện tử đặt yêu cầu và chọn cách làm:

| Thành phần | Yêu cầu | Cách đạt |
|---|---|---|
| Web/API | Chịu được mất một AZ | 3 replica trải trên 3 AZ, sau load balancer, HPA theo CPU và latency |
| Database đơn hàng | RPO ≈ 0 trong region, RTO < 2 phút | Primary + standby đồng bộ ở AZ khác, failover tự động |
| Mất cả region | RPO 15 phút, RTO 1 giờ | Pilot light: replicate bất đồng bộ sang region thứ hai, hạ tầng dựng lại bằng Terraform |
| Xoá nhầm hoặc ransomware | Khôi phục được về trước sự cố tới 35 ngày | Backup hằng ngày + PITR, bản copy immutable ở tài khoản khác |
| Kiểm chứng | Biết chắc kế hoạch chạy được | Diễn tập khôi phục mỗi quý, đo RPO/RTO thật |

Availability của đường đi chính: load balancer (99,99%) × API trên 3 AZ (gần 100%) × database HA (99,95%) ≈ 99,94%. Database là mắt xích yếu nhất, nên muốn tăng availability thì đầu tư vào database trước.

## Câu hỏi

**"Bốn số 9" (99,99%) nghĩa là bao nhiêu phút downtime?**
> - **Availability**: tỷ lệ thời gian dịch vụ hoạt động đúng.
> - **Cửa sổ đo**: khoảng thời gian tính availability (tháng, quý, năm).
>
> Downtime cho phép = `(1 − availability) × độ dài cửa sổ`. Với 99,99%: một năm 525.600 phút × 0,0001 ≈ **52,6 phút/năm**, một tháng 30 ngày 43.200 phút × 0,0001 ≈ **4,3 phút/tháng**. Mỗi số 9 thêm vào chia downtime cho 10: ba số 9 là khoảng 8,8 giờ/năm, năm số 9 là khoảng 5,3 phút/năm.
>
> Ranh giới: 4,3 phút một tháng là ít hơn thời gian một người kịp nhận alert và mở laptop. Bốn số 9 trở lên đòi hỏi failover *tự động*, không thể dựa vào con người. Con số cũng phụ thuộc cách đo: theo thời gian hay theo request, có tính bảo trì có kế hoạch hay không.

**Redundancy và failover hoạt động thế nào?**
> - **Redundancy**: có nhiều bản của cùng một thành phần.
> - **Failover**: phát hiện bản chính hỏng, quyết định bản thay thế, chuyển traffic sang.
> - **Split-brain**: hai bản cùng nghĩ mình là bản chính và cùng nhận ghi, làm dữ liệu lệch nhau.
>
> Redundancy chỉ có ích khi đi kèm failover hoạt động được: phải phát hiện được hỏng (health check), chuyển được traffic (load balancer, DNS, endpoint), và với thành phần có trạng thái thì phải đảm bảo chỉ một bản được ghi. Thành phần stateless (web/API) thì dễ: active-active sau load balancer, load balancer tự bỏ bản hỏng. Thành phần stateful (database) thì khó hơn: cần replication, cơ chế bầu bản chính, và chấp nhận một khoảng gián đoạn ngắn.
>
> Ranh giới: redundancy không độc lập thì vô ích. Hai bản cùng AZ, cùng nguồn điện, hay cùng một bản deploy lỗi sẽ hỏng cùng lúc. Failover không bao giờ được diễn tập thì thường không chạy đúng khi cần.

**Vì sao thêm phụ thuộc làm hệ thống kém sẵn sàng hơn?**
> - **Phụ thuộc nối tiếp**: request cần *mọi* thành phần đều hoạt động.
> - **Phụ thuộc song song**: chỉ cần *một* trong các bản hoạt động.
>
> Availability của chuỗi nối tiếp là tích các availability, nên luôn thấp hơn thành phần yếu nhất. 10 phụ thuộc 99,9% nối tiếp chỉ còn khoảng 99%. Vì vậy cần giảm phụ thuộc *cứng* trên đường đi chính, biến phụ thuộc không thiết yếu thành phụ thuộc mềm (có timeout, có fallback, có thể bỏ qua), và đặt redundancy độc lập ở mắt xích yếu.
>
> Ranh giới: công thức tích giả định các lỗi độc lập. Trên thực tế các thành phần hay hỏng *cùng nhau* (chung mạng, chung DNS, cùng một bản config), nên con số thật thường tệ hơn công thức.

**Autoscaling scale theo gì?**
> - **Autoscaling**: tự đổi số instance theo metric so với mục tiêu.
> - **Metric dẫn dắt (leading) và metric trễ (lagging)**: metric báo tải *sắp* tăng, và metric chỉ thay đổi *sau khi* đã quá tải.
>
> Scale theo metric tỷ lệ thuận với tải và phản ánh đúng nút cổ chai của service: CPU cho service nặng tính toán, số request/giây hoặc số request đang xử lý cho API, độ dài hàng đợi (consumer lag) cho worker. Autoscaler tính số instance bằng tỷ lệ giữa giá trị hiện tại và giá trị mục tiêu. Ví dụ 4 Pod ở 90% CPU, mục tiêu 60%: cần ceil(4 × 90/60) = 6 Pod.
>
> Ranh giới: autoscaling có độ trễ (thu metric, tạo Pod, kéo image, khởi động app, có khi phải tạo node mới), nên không cứu được đợt tăng tải đột ngột trong vài giây. Trường hợp đó cần dư công suất sẵn hoặc scale trước theo lịch. Scale ngang cũng không giúp gì khi nút cổ chai là database dùng chung.

**RPO khác RTO thế nào?**
> - **RPO**: lượng dữ liệu tối đa được phép mất, tính ngược từ lúc sự cố.
> - **RTO**: thời gian tối đa được phép ngừng dịch vụ, tính xuôi từ lúc sự cố.
>
> RPO nhìn *về quá khứ* (mất bao nhiêu dữ liệu), RTO nhìn *về tương lai* (bao lâu thì chạy lại). Hai chỉ số được quyết định bởi những thứ khác nhau: RPO bởi tần suất backup và kiểu replication (backup mỗi đêm thì RPO tới 24 giờ, replication đồng bộ thì RPO gần 0), RTO bởi lượng hạ tầng chuẩn bị sẵn và mức tự động hoá của việc khôi phục.
>
> Ranh giới: RPO và RTO thấp đều tốn kém, và mỗi hệ thống con cần một mức khác nhau. Dữ liệu thanh toán cần RPO gần 0, còn log phân tích có thể chấp nhận mất một ngày. Đặt cùng một mục tiêu cho mọi thứ là lãng phí.

**Backup, replication và DR khác nhau ra sao?**
> - **Backup**: bản sao tại một thời điểm, lưu tách biệt.
> - **Replication**: sao chép liên tục sang bản khác.
> - **DR**: kế hoạch và năng lực khôi phục cả hệ thống sau thảm hoạ.
>
> Mỗi thứ chống một loại sự cố khác nhau. Replication chống *hỏng phần cứng* (mất một máy hay một AZ) nhưng chép luôn cả lỗi logic. Backup chống *hỏng dữ liệu* (xoá nhầm, bug ghi sai, ransomware) nhờ quay được về quá khứ. DR là cả quy trình (con người, IaC, runbook, thứ tự khôi phục) dùng backup và replication để dựng lại dịch vụ khi mất cả region.
>
> Ranh giới: backup chưa từng được thử khôi phục thì không chắc đã là backup. Lỗi hay gặp là backup thiếu một phần, không giải mã được vì mất khoá, hay khôi phục mất 3 ngày trong khi RTO là 4 giờ. Diễn tập khôi phục định kỳ là cách duy nhất để biết.

## Hiểu nhầm thường gặp
- **"Chạy trên Kubernetes là có HA."** Kubernetes restart Pod hỏng, nhưng 1 replica, mọi Pod cùng một node, hay database chỉ có một bản thì vẫn là SPOF.
- **"Có replica rồi không cần backup."** Replica chép nguyên văn cả lệnh xoá nhầm lẫn dữ liệu bị mã hoá.
- **"Retry là luôn tốt."** Retry không có backoff, jitter và giới hạn sẽ nhân tải lên một service đang yếu và làm nó sập hẳn (retry storm).
- **"DR là tài liệu."** Kế hoạch DR không được diễn tập chỉ là giả thuyết. Chaos engineering và game day là cách chủ động gây lỗi có kiểm soát để kiểm chứng.

## Liên quan
- [11-sre-and-incident-management.md](11-sre-and-incident-management.md): SLO quyết định mức HA cần đạt.
- [06-cloud-fundamentals.md](06-cloud-fundamentals.md): region, AZ, storage, nền của HA trên cloud.
- [05-kubernetes.md](05-kubernetes.md): replica, probe, HPA.
- [../backend/10-databases.md](../backend/10-databases.md): transaction và nhất quán dữ liệu, những thứ ảnh hưởng tới replication.
