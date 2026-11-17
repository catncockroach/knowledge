# SRE and incident management

> Site Reliability Engineering (SRE) là cách quản lý độ tin cậy bằng con số: định nghĩa "đủ tốt" bằng SLO, cho phép một lượng lỗi có kiểm soát (error budget) để cân bằng giữa tốc độ ra tính năng và sự ổn định, giới hạn việc vận hành thủ công (toil), và xử lý sự cố theo một quy trình có vai trò rõ ràng, sau đó học từ sự cố qua postmortem không đổ lỗi.

## Tại sao cần biết
"Hệ thống phải luôn chạy" là một mục tiêu không đo được và không đạt được. Thiếu con số chung thì Dev và Ops lại cãi nhau như thời trước DevOps ([01-devops-culture.md](01-devops-culture.md)): bao nhiêu lỗi là chấp nhận được, khi nào phải dừng tính năng để lo ổn định. SRE biến câu hỏi đó thành con số đo từ metric ([10-monitoring-and-observability.md](10-monitoring-and-observability.md)). Và vì sự cố chắc chắn sẽ xảy ra, cách xử lý nó (nhanh, bình tĩnh, có học) quyết định chỉ số failed deployment recovery time của DORA.

## Khái niệm cốt lõi

### SLI, SLO, SLA
- **SLI (Service Level Indicator)** — **Là gì:** một chỉ số đo chất lượng dịch vụ từ góc người dùng, thường viết dạng tỷ lệ *sự kiện tốt / tổng sự kiện*. Ví dụ: tỷ lệ request trả về không lỗi, tỷ lệ request nhanh hơn 300 ms. **Dùng để:** có một con số khách quan để biết người dùng đang được phục vụ tốt tới đâu.
- **SLO (Service Level Objective)** — **Là gì:** mục tiêu cho một SLI trong một khoảng thời gian. Ví dụ: 99,9% request thành công trong 30 ngày trượt. **Dùng để:** định nghĩa "đủ tin cậy" là gì. Đây là mục tiêu nội bộ, do đội sản phẩm và đội kỹ thuật cùng chốt.
- **SLA (Service Level Agreement)** — **Là gì:** cam kết trong *hợp đồng* với khách hàng, kèm hậu quả khi vi phạm (hoàn tiền, credit). **Dùng để:** ràng buộc pháp lý và thương mại. SLA thường lỏng hơn SLO để có khoảng an toàn.

```
 SLI   "tỷ lệ request thành công"           ← đo được, là con số thực tế
 SLO   "SLI ≥ 99,9% trong 30 ngày"          ← mục tiêu nội bộ
 SLA   "≥ 99,5%/tháng, nếu không hoàn 10%"  ← hợp đồng, lỏng hơn SLO
```

### Error budget
- **Là gì:** lượng "không tin cậy" được phép, bằng `1 − SLO`. SLO 99,9% thì error budget là 0,1% số request (hoặc thời gian) trong cửa sổ đo.
- **Dùng để:** chuyển cuộc tranh luận "nhanh hay ổn" thành một quy tắc. Còn budget thì cứ deploy, thử nghiệm. Hết budget thì ưu tiên độ tin cậy: tạm dừng tính năng rủi ro, tập trung sửa nguyên nhân gây lỗi.
- **Error budget policy** — **Là gì:** văn bản các bên đã đồng ý từ trước, nói rõ làm gì khi budget sắp hết hoặc đã hết. **Dùng để:** quyết định không phụ thuộc vào cảm tính lúc căng thẳng.
- **Burn rate** — **Là gì:** tốc độ tiêu budget so với mức "vừa đủ hết đúng lúc cửa sổ kết thúc". Burn rate 1 thì hết đúng lúc cửa sổ kết thúc, burn rate 14,4 trong 1 giờ thì tiêu 2% budget của 30 ngày (14,4 × 1 / 720). **Dùng để:** alert theo SLO. Gọi người khi budget bị đốt nhanh, không gọi vì từng lần lỗi lẻ tẻ.

### Toil
- **Là gì:** việc vận hành mang tính *thủ công, lặp lại, tự động hoá được, phản ứng theo sự việc (không theo kế hoạch), không để lại giá trị lâu dài*, và *tăng tuyến tính theo quy mô* của service. Ví dụ: restart tay một service mỗi khi đầy bộ nhớ, tạo tài khoản bằng tay theo ticket, chạy tay cùng một bộ lệnh mỗi lần deploy.
- **Dùng để (nhận diện):** biết việc nào cần tự động hoá. Google đặt mục tiêu giữ toil dưới 50% thời gian của mỗi SRE, nửa còn lại cho việc kỹ thuật làm giảm toil hoặc tăng độ tin cậy.
- Không phải việc vận hành nào cũng là toil. Họp thiết kế, review kiến trúc, viết postmortem là *overhead*, không phải toil.

### On-call
- **Là gì:** lịch trực, trong đó một người (hoặc một cặp primary/secondary) nhận alert và phản hồi trong một thời gian quy định.
- **Dùng để:** đảm bảo luôn có người xử lý sự cố. Trực tốt cần: alert ít mà đúng, runbook đầy đủ, quyền đủ để xử lý, luân phiên công bằng, và thời gian nghỉ bù.
- **Runbook** — **Là gì:** tài liệu từng bước cho một alert hay một loại sự cố: kiểm tra gì, chạy lệnh gì, khi nào gọi thêm người. **Dùng để:** người trực xử lý được kể cả khi không phải tác giả của service. Runbook nào toàn là lệnh lặp lại là ứng viên để tự động hoá.

### Incident
- **Là gì:** sự kiện ngoài kế hoạch làm giảm (hoặc đe doạ làm giảm) chất lượng dịch vụ, đủ nghiêm trọng để cần phản ứng có tổ chức.
- **Severity (SEV)** — **Là gì:** mức nghiêm trọng, thường từ SEV1 (sự cố lớn, nhiều người dùng bị ảnh hưởng, mất tiền hoặc mất dữ liệu) tới SEV3–4 (ảnh hưởng nhỏ, có cách đi vòng). **Dùng để:** quyết định huy động bao nhiêu người, có thông báo ra ngoài không, phản ứng nhanh tới mức nào. Định nghĩa cụ thể do mỗi tổ chức tự đặt.
- **Vai trò khi xử lý sự cố lớn:**

| Vai trò | Là gì / Dùng để |
|---|---|
| **Incident Commander (IC)** | Điều phối chung, giữ bức tranh tổng, ra quyết định, giao việc. *Không* tự tay gỡ lỗi |
| **Ops / technical lead** | Người trực tiếp điều tra và thực hiện thay đổi trên hệ thống |
| **Communications lead** | Cập nhật định kỳ cho các bên liên quan, khách hàng, trang status |
| **Scribe** | Ghi lại timeline: ai làm gì, lúc nào, thấy gì. Là nguyên liệu cho postmortem |

### Postmortem
- **Là gì:** tài liệu viết sau sự cố: tác động, timeline, nguyên nhân gốc và các yếu tố góp phần, cái gì làm tốt, cái gì làm chưa tốt, và **action item** có người chịu trách nhiệm và hạn chót.
- **Blameless** — **Là gì:** viết với giả định mọi người đã hành động hợp lý theo thông tin họ có lúc đó. Tìm lỗ hổng của *hệ thống và quy trình*, không tìm người để phạt. **Dùng để:** mọi người dám kể đúng sự thật. Đổ lỗi thì người ta giấu thông tin, và lần sau sự cố lặp lại.

### MTTD, MTTR
- **MTTD (Mean Time To Detect)**: trung bình thời gian từ lúc sự cố bắt đầu tới lúc được phát hiện.
- **MTTR (Mean Time To Restore / Recover)**: trung bình thời gian từ lúc phát hiện tới lúc dịch vụ trở lại bình thường. Chữ "R" được dùng theo nhiều nghĩa (repair, respond, resolve), nên khi dùng phải định nghĩa rõ.

## Cách hoạt động
Vòng đời một incident:

```
 Detect ──► Triage ──► Mitigate ──► Resolve ──► Postmortem ──► Action items
   │          │            │            │             │               │
 alert,     xác định     cầm máu:     sửa tận gốc,  blameless,     làm thật,
 người      severity,    rollback,    xác nhận      timeline,      theo dõi tới
 dùng báo   mở kênh,     tắt flag,    hết tác động  nguyên nhân    khi xong
            gán IC       chuyển region,
                         thêm máy
```

Nguyên tắc quan trọng nhất: **mitigate trước, tìm root cause sau**. Mục tiêu lúc có sự cố là làm người dùng hết bị ảnh hưởng nhanh nhất. Rollback bản deploy gần nhất hoặc tắt feature flag thường làm được việc này trong vài phút, *trước khi* biết chính xác dòng code nào sai. Tìm nguyên nhân gốc thuộc giai đoạn resolve và postmortem.

## Ví dụ
Tính error budget cho SLO "99,9% request thành công trong 30 ngày":

- Theo thời gian: 30 ngày = 43.200 phút. Budget = 0,1% × 43.200 = **43,2 phút** lỗi hoàn toàn mỗi 30 ngày.
- Theo request: tháng này có 50 triệu request. Budget = 0,1% × 50.000.000 = **50.000 request lỗi**.

Hôm qua một bản deploy hỏng làm 20.000 request lỗi trong 15 phút: đã tiêu 40% budget của cả tháng chỉ trong một lần. Theo error budget policy, đội dừng các deploy rủi ro, thêm canary cho đường thanh toán, và viết postmortem.

Bảng quy đổi availability ra thời gian downtime tối đa:

| Availability | Mỗi năm (365 ngày) | Mỗi 30 ngày |
|---|---|---|
| 99% | 3,65 ngày | 7,2 giờ |
| 99,9% | 8,76 giờ | 43,2 phút |
| 99,95% | 4,38 giờ | 21,6 phút |
| 99,99% | 52,6 phút | 4,32 phút |
| 99,999% | 5,26 phút | 25,9 giây |

## Câu hỏi

**SLI, SLO và SLA khác nhau thế nào?**
> - **SLI**: chỉ số đo được (tỷ lệ request tốt).
> - **SLO**: mục tiêu nội bộ cho SLI trong một cửa sổ thời gian.
> - **SLA**: cam kết hợp đồng với khách hàng, có hậu quả khi vi phạm.
>
> Ba khái niệm xếp theo tầng: SLI là *thứ đo*, SLO là *mục tiêu* đặt trên thứ đo đó, SLA là *lời hứa có ràng buộc* thường dựa trên cùng SLI nhưng lỏng hơn SLO. Thứ tự này để đội phản ứng khi SLO bị đe doạ, từ lâu trước khi SLA bị vi phạm và phải trả tiền.
>
> Ranh giới: không phải service nào cũng có SLA (service nội bộ thường không có), nhưng service quan trọng nào cũng nên có SLO. SLI nên đo càng gần người dùng càng tốt (ở load balancer hoặc ở client), không đo ở chỗ người dùng không cảm nhận được (CPU của một máy).

**Error budget là gì và dùng để làm gì?**
> - **Error budget**: `1 − SLO`, lượng lỗi được phép trong cửa sổ đo.
> - **Error budget policy**: thoả thuận trước về việc phải làm khi budget cạn.
>
> Error budget biến độ tin cậy thành tài nguyên có thể *tiêu*: còn budget thì được chấp nhận rủi ro (deploy, thử nghiệm), hết budget thì phải ưu tiên ổn định. Vì vậy Dev và Ops không còn tranh luận cảm tính "có nên deploy không" mà nhìn cùng một con số. Budget còn là cơ sở cho alert: gọi người khi burn rate cao, tức budget đang bị đốt nhanh.
>
> Ranh giới: budget chỉ có ý nghĩa khi policy được tôn trọng thật. Hết budget mà vẫn đẩy tính năng như thường thì SLO chỉ là con số trang trí. Sự cố do phụ thuộc bên ngoài (cloud sập) vẫn tiêu budget, vì người dùng vẫn bị ảnh hưởng.

**Vì sao không đặt SLO 100%?**
> - **Availability**: tỷ lệ thời gian hoặc request mà dịch vụ hoạt động đúng.
>
> Mỗi số 9 thêm vào làm chi phí tăng mạnh, trong khi người dùng gần như không cảm nhận được sự khác biệt, vì mạng, điện thoại và ISP của họ còn kém tin cậy hơn thế. 100% còn có nghĩa là budget bằng 0: không được deploy, không được thử nghiệm, vì mọi thay đổi đều có rủi ro. SLO nên đặt ở mức *người dùng hài lòng*, không đặt ở mức cao nhất có thể.
>
> Ranh giới: một số thành phần cần độ tin cậy cao hơn hẳn phần còn lại (hệ thống thanh toán, xác thực) và có SLO riêng chặt hơn. Một service không thể có SLO cao hơn các phụ thuộc cứng của nó, trừ khi có cơ chế dự phòng.

**Toil là gì, vì sao phải giới hạn?**
> - **Toil**: việc vận hành thủ công, lặp lại, tự động hoá được, phản ứng theo sự việc, không để lại giá trị lâu dài, tăng theo quy mô.
>
> Toil tăng tuyến tính theo quy mô: service lớn gấp đôi thì toil gấp đôi. Không giới hạn thì đội vận hành dần chỉ còn làm toil, không còn thời gian để cải thiện gì. Vì vậy SRE đặt trần (Google dùng mức dưới 50%) và dùng nửa thời gian còn lại để tự động hoá, xoá bớt toil.
>
> Ranh giới: việc thủ công làm một lần (dựng một thứ mới), hay việc cần phán đoán của con người (thiết kế, review), không phải toil. Tự động hoá một việc hiếm khi xảy ra có thể tốn hơn làm tay. Hãy cân nhắc tần suất và rủi ro sai sót.

**Một incident được xử lý theo các bước nào?**
> - **Mitigate**: làm dịch vụ hết ảnh hưởng tới người dùng (cầm máu).
> - **Resolve**: sửa nguyên nhân để sự cố không quay lại.
> - **Incident Commander**: người điều phối, không tự tay sửa.
>
> Thứ tự là phát hiện → phân loại (severity, gán IC, mở kênh liên lạc) → **giảm tác động trước** → sửa tận gốc → postmortem. Ưu tiên giảm tác động vì mỗi phút người dùng bị lỗi là thiệt hại thật, trong khi tìm nguyên nhân gốc có thể mất hàng giờ. Rollback, tắt flag, chuyển traffic sang region khác, hay thêm máy đều là mitigate. Tách vai IC khỏi người sửa vì người đang tập trung gỡ lỗi không đồng thời nhìn được bức tranh tổng và lo liên lạc.
>
> Ranh giới: với sự cố nhỏ, một người có thể kiêm mọi vai. Quy trình đầy đủ dành cho sự cố lớn, kéo dài hoặc nhiều đội cùng tham gia. Khai báo incident sớm rồi hạ mức nếu không nghiêm trọng thì tốt hơn khai báo muộn.

**Thế nào là postmortem blameless, vì sao không đổ lỗi?**
> - **Postmortem**: tài liệu phân tích sau sự cố, kèm action item.
> - **Blameless**: tập trung vào hệ thống và quy trình, không quy lỗi cho cá nhân.
>
> Lỗi của con người là triệu chứng của một hệ thống *cho phép* lỗi đó xảy ra. Câu hỏi đúng không phải "ai gõ sai lệnh" mà "vì sao một lệnh gõ sai lại xoá được production, và vì sao không ai phát hiện sớm". Không đổ lỗi thì người trong cuộc mới kể đủ chi tiết, và action item mới sửa được lỗ hổng thật (thêm bước xác nhận, hạn chế quyền, tự động hoá).
>
> Ranh giới: blameless không có nghĩa là không ai chịu trách nhiệm. Action item vẫn có người phụ trách và hạn chót. Postmortem mà action item không bao giờ được làm thì sự cố sẽ lặp lại.

## Hiểu nhầm thường gặp
- **"SLO càng cao càng tốt."** SLO quá cao làm đóng băng việc phát triển và tốn chi phí vô ích. SLO đúng là mức làm người dùng hài lòng.
- **"MTTR thấp là nhờ sửa bug nhanh."** MTTR thấp chủ yếu nhờ mitigate nhanh (rollback, flag), không nhờ tìm ra bug nhanh.
- **"On-call là việc của Ops."** Theo tinh thần "you build it, you run it", đội viết service cũng tham gia trực. Như vậy họ có động lực làm service dễ vận hành và alert có ý nghĩa.
- **"Không có sự cố nghĩa là làm tốt."** Không có sự cố trong khi SLO còn dư nhiều có thể là dấu hiệu đang quá thận trọng, deploy quá ít.

## Liên quan
- [10-monitoring-and-observability.md](10-monitoring-and-observability.md): metric để đo SLI và alert theo burn rate.
- [09-deployment-strategies.md](09-deployment-strategies.md): rollback và feature flag là công cụ mitigate.
- [12-high-availability-and-dr.md](12-high-availability-and-dr.md): kiến trúc đạt SLO và khôi phục sau thảm hoạ.
- [../enterprise-security/12-incident-response.md](../enterprise-security/12-incident-response.md): ứng phó sự cố bảo mật, có quy trình tương tự nhưng mục tiêu khác.
