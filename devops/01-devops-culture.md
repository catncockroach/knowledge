# DevOps culture

> DevOps là cách tổ chức công việc phần mềm để đội phát triển (Dev) và đội vận hành (Ops) cùng chịu trách nhiệm đưa thay đổi lên production nhanh, thường xuyên và an toàn, dựa trên văn hoá chung, tự động hoá và đo lường.

## Tại sao cần biết
Trước DevOps, nhiều công ty chia đôi trách nhiệm. Dev được đánh giá theo số tính năng làm ra, nên muốn thay đổi nhiều. Ops được đánh giá theo độ ổn định của hệ thống, nên muốn thay đổi ít. Code được "ném qua tường" (throw over the wall) cho Ops deploy, thường theo đợt lớn vài tháng một lần. Đợt càng lớn thì càng nhiều thứ hỏng cùng lúc, và khi hỏng thì hai bên đổ lỗi cho nhau.

DevOps sinh ra để gỡ mâu thuẫn đó. Mọi công cụ ở các file sau (container, Kubernetes, Terraform, CI/CD, monitoring) đều phục vụ cùng một mục tiêu: làm cho mỗi thay đổi **nhỏ, tự động, đo được và đảo ngược được**. Hiểu mục tiêu này thì mới biết công cụ nào giải quyết vấn đề gì.

## Khái niệm cốt lõi

### DevOps
- **Là gì:** một tập hợp văn hoá, cách làm và công cụ giúp rút ngắn đường đi từ lúc commit code đến lúc code chạy ổn định trên production, đồng thời giữ được độ tin cậy. DevOps không phải một công cụ hay một sản phẩm.
- **Dùng để:** cho phép tổ chức release thường xuyên mà không đánh đổi sự ổn định. Phát hiện lỗi sớm, sửa nhanh, và học từ lỗi.

### Kỹ sư DevOps (DevOps engineer)
- **Là gì:** chức danh phổ biến trên thị trường cho người xây và vận hành hạ tầng, pipeline CI/CD, công cụ tự động hoá và hệ thống monitoring để các đội phát triển tự deploy được.
- **Dùng để:** cung cấp "đường ray" (tooling, platform) cho Dev. Theo đúng tinh thần DevOps, Ops không làm thay Dev mà giúp Dev tự làm.

### CALMS
- **Là gì:** khung năm trụ cột để mô tả một tổ chức làm DevOps: **C**ulture (văn hoá chia sẻ trách nhiệm, không đổ lỗi), **A**utomation (tự động hoá build, test, deploy, hạ tầng), **L**ean (luồng công việc nhỏ, giảm lãng phí và chờ đợi), **M**easurement (đo mọi thứ: tốc độ deploy, tỷ lệ lỗi, thời gian khôi phục), **S**haring (chia sẻ kiến thức, công cụ, bài học giữa các đội).
- **Dùng để:** tự đánh giá xem một tổ chức đã làm DevOps thật hay mới chỉ mua công cụ. Có công cụ (A) mà thiếu văn hoá (C) và đo lường (M) thì vẫn chưa phải DevOps.

### The Three Ways
- **Là gì:** ba nguyên tắc nền trong *The DevOps Handbook* và *The Phoenix Project*:
  1. **Flow**: tối ưu luồng chảy từ Dev sang Ops sang khách hàng. Làm từng mẻ nhỏ, giới hạn việc dở dang, không đẩy lỗi xuống công đoạn sau.
  2. **Feedback**: tạo vòng phản hồi nhanh từ phải về trái (production về Dev), để phát hiện và sửa lỗi ngay gần nơi nó sinh ra.
  3. **Continual learning and experimentation**: tạo văn hoá dám thử nghiệm, học từ thất bại và biến cải tiến thành thói quen.
- **Dùng để:** định hướng khi chọn cách làm. Một thay đổi tốt là thay đổi làm luồng nhanh hơn, phản hồi sớm hơn, hoặc giúp tổ chức học nhanh hơn.

### DORA metrics
- **Là gì:** bộ chỉ số đo hiệu năng giao phần mềm (software delivery performance), do nhóm nghiên cứu DORA (DevOps Research and Assessment) xây dựng từ khảo sát hằng năm. Bộ hiện tại có năm chỉ số, chia hai nhóm:

| Nhóm | Chỉ số | Đo gì |
|---|---|---|
| Throughput (thông lượng) | **Change lead time** | Thời gian từ lúc commit vào version control đến lúc chạy trên production |
| | **Deployment frequency** | Bao lâu deploy một lần |
| | **Failed deployment recovery time** | Mất bao lâu để khôi phục sau một lần deploy hỏng |
| Instability (bất ổn) | **Change fail rate** | Tỷ lệ deploy phải can thiệp ngay sau đó (rollback, hotfix) |
| | **Deployment rework rate** | Tỷ lệ deploy không có kế hoạch, sinh ra do sự cố production |

- **Dùng để:** đo kết quả thay vì đo hoạt động. Nghiên cứu của DORA cho thấy tốc độ và độ ổn định không đối nghịch nhau: các đội tốt nhất vừa deploy nhiều vừa ít hỏng.
- Bộ gốc ban đầu có bốn chỉ số (lead time, deployment frequency, change failure rate, time to restore service). Các tài liệu cũ vẫn thường gọi là "4 key metrics".

### SRE và Platform Engineering
- **SRE (Site Reliability Engineering)** — **Là gì:** cách Google tổ chức vận hành: giao việc vận hành cho kỹ sư phần mềm và dùng phần mềm để giải bài toán vận hành. **Dùng để:** quản lý độ tin cậy bằng con số (SLO, error budget), giới hạn việc thủ công (toil). Chi tiết ở [11-sre-and-incident-management.md](11-sre-and-incident-management.md).
- **Platform Engineering** — **Là gì:** một đội xây nền tảng nội bộ (Internal Developer Platform, IDP) dùng chung: template service, pipeline, môi trường, cổng self-service. **Dùng để:** giảm tải nhận thức cho các đội sản phẩm. Họ chỉ cần bấm hoặc khai báo, không phải tự hiểu mọi chi tiết của Kubernetes hay Terraform.

## Cách hoạt động

### Vòng lặp DevOps
Vòng lặp vô hạn (infinity loop) mô tả công việc liên tục, không có điểm "xong":

```
        ┌──── Dev ────┐          ┌──── Ops ────┐
   Plan → Code → Build → Test → Release → Deploy → Operate → Monitor
     ▲                                                          │
     └──────────────────── feedback ────────────────────────────┘
```

| Giai đoạn | Việc chính | File liên quan |
|---|---|---|
| Plan, Code | Viết code, review, quản lý version | [../backend/13-git-and-version-control.md](../backend/13-git-and-version-control.md) |
| Build, Test | Build artifact, chạy test tự động | [08-ci-cd.md](08-ci-cd.md) |
| Release, Deploy | Đưa artifact lên môi trường, chọn chiến lược | [09-deployment-strategies.md](09-deployment-strategies.md) |
| Operate | Chạy trên hạ tầng (server, container, cloud) | [04](04-containers-and-docker.md) → [07](07-terraform-and-iac.md) |
| Monitor | Quan sát, cảnh báo, xử lý sự cố | [10](10-monitoring-and-observability.md), [11](11-sre-and-incident-management.md) |

### Vì sao mẻ nhỏ an toàn hơn mẻ lớn
Một release gồm 200 thay đổi sau ba tháng: nếu hỏng thì phải dò lỗi trong 200 thay đổi, rollback cũng mất cả 200 thay đổi, và người viết code đã quên chi tiết. Một deploy gồm 1–2 thay đổi: nếu hỏng thì biết ngay thủ phạm, rollback chỉ mất một thay đổi nhỏ, người viết vẫn nhớ code. Rủi ro của mỗi lần deploy giảm, nên deploy được thường xuyên hơn. Đây là lý do DevOps đẩy mạnh tự động hoá: deploy thủ công thì tốn công, nên người ta dồn lại thành mẻ lớn.

## Ví dụ
Một đội đo DORA metrics trong một tháng:
- Có 40 lần deploy lên production, tức khoảng 2 lần mỗi ngày làm việc: **deployment frequency** cao.
- Trung vị thời gian từ commit đến production là 3 giờ: **change lead time**.
- Có 4 lần deploy phải rollback hoặc hotfix: **change fail rate** = 4 / 40 = **10%**.
- Trung bình mất 25 phút để khôi phục mỗi lần hỏng: **failed deployment recovery time**.

Muốn cải thiện thì đội nhìn vào chỗ tắc. Lead time 3 giờ mà 2 giờ là chờ người duyệt thủ công: tự động hoá kiểm tra để giảm thời gian chờ. Change fail rate cao: thêm test, dùng canary.

## Câu hỏi

**DevOps là một vai trò, một công cụ hay một văn hoá?**
> - **Vai trò**: chức danh trong tổ chức (DevOps engineer).
> - **Công cụ**: phần mềm cụ thể (Jenkins, Docker, Terraform...).
> - **Văn hoá**: cách mọi người làm việc với nhau, chia trách nhiệm và đo kết quả.
>
> DevOps trước hết là văn hoá và cách làm: Dev và Ops cùng chịu trách nhiệm từ lúc viết code đến lúc vận hành, dựa trên tự động hoá và đo lường (CALMS). Công cụ là phương tiện để làm cách đó rẻ hơn. Chức danh "DevOps engineer" là cách thị trường gọi người xây các phương tiện ấy.
>
> Ranh giới: một công ty mua Kubernetes và Jenkins nhưng vẫn để Ops deploy hộ ba tháng một lần thì chưa làm DevOps. Ngược lại, một đội nhỏ deploy bằng script đơn giản, mỗi ngày nhiều lần, có monitoring và cùng trực sự cố thì đang làm DevOps.

**DevOps giải quyết mâu thuẫn gì giữa Dev và Ops?**
> - **Dev**: đội viết tính năng, được đánh giá theo tốc độ ra tính năng.
> - **Ops**: đội vận hành hệ thống, được đánh giá theo độ ổn định.
>
> Khi hai đội có mục tiêu đối nghịch (thay đổi nhiều và thay đổi ít), mỗi bên tối ưu phần của mình và ma sát dồn vào khâu bàn giao. DevOps gỡ mâu thuẫn bằng cách cho hai bên chung một mục tiêu (giao giá trị nhanh *và* ổn định, đo bằng DORA metrics), và làm cho thay đổi đủ nhỏ, đủ tự động để tốc độ không còn đe doạ sự ổn định.
>
> Ranh giới: DevOps không xoá Ops. Việc vận hành vẫn còn, chỉ được tự động hoá và chia sẻ trách nhiệm ("you build it, you run it").

**Đo một đội làm DevOps tốt hay không bằng gì?**
> - **DORA metrics**: năm chỉ số giao phần mềm, gồm ba chỉ số thông lượng (change lead time, deployment frequency, failed deployment recovery time) và hai chỉ số bất ổn (change fail rate, deployment rework rate).
>
> Đo kết quả của cả hệ thống, không đo hoạt động của từng người: đo tốc độ đưa thay đổi lên production và độ ổn định của chúng, không đo số dòng code hay số ticket. Hai nhóm phải xem cùng lúc: deploy nhiều mà hay hỏng thì chưa tốt, ít hỏng vì gần như không deploy cũng chưa tốt.
>
> Ranh giới: chỉ số trở thành mục tiêu thì dễ bị "chơi" (định luật Goodhart). Ví dụ chia nhỏ deploy vô nghĩa để tăng deployment frequency. DORA metrics dùng để tìm chỗ tắc, không dùng để xếp hạng cá nhân.

**DevOps, SRE và Platform Engineering khác nhau ở đâu?**
> - **DevOps**: triết lý và tập cách làm chung (văn hoá, tự động hoá, đo lường).
> - **SRE**: một cách hiện thực cụ thể, tập trung vào độ tin cậy, quản lý bằng SLO và error budget.
> - **Platform Engineering**: một cách tổ chức đội, xây nền tảng nội bộ self-service cho các đội khác dùng.
>
> Tiêu chí phân biệt là câu hỏi mỗi thứ trả lời. DevOps trả lời "nên làm việc theo nguyên tắc nào", SRE trả lời "đo và giữ độ tin cậy thế nào", Platform Engineering trả lời "làm sao để hàng chục đội cùng dùng chung hạ tầng mà không phải ai cũng thành chuyên gia". Ba thứ bổ sung cho nhau, không loại trừ nhau. Một công ty có thể vừa có đội platform, vừa có SRE, và cả hai đều làm theo nguyên tắc DevOps.
>
> Ranh giới: tên đội ở mỗi công ty khác nhau. Một đội tên "DevOps" có thể đang làm việc của platform team. Nhìn vào việc họ làm, đừng nhìn vào tên đội.

**Vì sao deploy thường xuyên lại an toàn hơn deploy ít?**
> - **Batch size**: số thay đổi gộp trong một lần deploy.
>
> Rủi ro và chi phí sửa lỗi tăng theo batch size: mẻ càng lớn thì càng khó tìm thay đổi gây lỗi, rollback càng mất nhiều, và người sửa càng xa thời điểm viết code. Deploy thường xuyên buộc mỗi mẻ phải nhỏ, nên mỗi lần hỏng chỉ ảnh hưởng ít và sửa nhanh. Việc deploy cũng được luyện nhiều nên quy trình được tự động hoá và ít sai.
>
> Ranh giới: deploy thường xuyên chỉ an toàn khi có test tự động, monitoring và cách rollback nhanh. Deploy nhiều mà không có lưới an toàn thì chỉ là hỏng nhiều hơn.

## Hiểu nhầm thường gặp
- **"DevOps là một đội riêng."** Một đội DevOps đứng giữa Dev và Ops dễ trở thành bức tường thứ ba. Mục tiêu là xoá vách ngăn, không phải thêm một vách ngăn.
- **"Cài CI/CD là xong DevOps."** Pipeline chỉ là phần Automation trong CALMS. Thiếu đo lường và văn hoá không đổ lỗi thì pipeline chỉ giúp deploy lỗi nhanh hơn.
- **"Tốc độ và ổn định phải đánh đổi."** Dữ liệu DORA cho thấy hai thứ đi cùng nhau: thay đổi nhỏ và tự động thì vừa nhanh vừa ổn.
- **"DevOps thay thế Agile."** Agile tối ưu cách làm ra phần mềm. DevOps nối dài tối ưu đó sang khâu giao và vận hành. Xem [../backend/15-sdlc-agile-scrum.md](../backend/15-sdlc-agile-scrum.md).

## Liên quan
- [../backend/15-sdlc-agile-scrum.md](../backend/15-sdlc-agile-scrum.md): SDLC và Agile, tiền thân về mặt quy trình của DevOps.
- [08-ci-cd.md](08-ci-cd.md): hiện thực phần Automation và Flow.
- [11-sre-and-incident-management.md](11-sre-and-incident-management.md): SRE, cách hiện thực DevOps tập trung vào độ tin cậy.
