# SDLC, Agile and Scrum

> Quy trình phát triển phần mềm (SDLC) mô tả các giai đoạn đưa một ý tưởng thành phần mềm chạy được và duy trì nó. Agile là triết lý phát triển theo vòng lặp ngắn, đón nhận thay đổi; Scrum là framework phổ biến nhất để thực hành Agile.

## Tại sao cần biết
Lập trình viên không code một mình: bạn nhận việc qua backlog, ước lượng, báo cáo trong daily, demo trong review. Yêu cầu entry level: biết các khái niệm về quy trình phát triển phần mềm, đặc biệt Agile, Scrum. Interview hay hỏi: Waterfall vs Agile, các vai trò và sự kiện trong Scrum, sprint là gì, user story, Definition of Done, CI/CD.

## Khái niệm cốt lõi

### Các giai đoạn SDLC
```
Planning → Requirements → Design → Implementation → Testing → Deployment → Maintenance
   ▲                                                                           │
   └───────────────────────────── phản hồi, yêu cầu mới ──────────────────────┘
```
| Giai đoạn | Việc chính | Sản phẩm |
|---|---|---|
| Planning | Mục tiêu, phạm vi, nguồn lực, rủi ro | Kế hoạch dự án |
| Requirements | Thu thập, phân tích yêu cầu chức năng và phi chức năng | Tài liệu yêu cầu (SRS), user story |
| Design | Kiến trúc, thiết kế DB, API, giao diện | Tài liệu giải pháp, thiết kế chi tiết |
| Implementation | Viết code, code review, unit test | Mã nguồn |
| Testing | Integration, system, UAT, performance, security test | Báo cáo test, danh sách bug |
| Deployment | Triển khai lên môi trường production | Bản phát hành |
| Maintenance | Sửa lỗi, cải tiến, vận hành, giám sát | Bản vá, phiên bản mới |

Môi trường điển hình: **dev** (phát triển) → **test/QA** → **staging** (giống production nhất) → **production** (người dùng thật).

### Các mô hình phát triển
| Mô hình | Cách làm | Hợp với | Hạn chế |
|---|---|---|---|
| **Waterfall** (thác nước) | Các giai đoạn tuần tự, xong hẳn giai đoạn này mới sang giai đoạn sau | Yêu cầu rõ, ổn định, ràng buộc pháp lý | Thay đổi muộn rất tốn kém; khách hàng thấy sản phẩm rất muộn |
| **V-Model** | Waterfall với mỗi giai đoạn phát triển có giai đoạn kiểm thử tương ứng | Hệ thống đòi hỏi kiểm định cao | Cứng nhắc như Waterfall |
| **Iterative / Incremental** | Làm theo nhiều vòng, mỗi vòng thêm một phần | Dự án lớn, yêu cầu dần rõ | Cần quản lý phạm vi tốt |
| **Agile** | Vòng lặp ngắn, giao phần mềm chạy được thường xuyên, thích ứng thay đổi | Yêu cầu thay đổi, cần phản hồi nhanh | Cần khách hàng tham gia, team tự quản |

### Agile
**Tuyên ngôn Agile** (Agile Manifesto, 2001) gồm bốn giá trị:
1. **Cá nhân và sự tương tác** hơn quy trình và công cụ.
2. **Phần mềm chạy được** hơn tài liệu đầy đủ.
3. **Cộng tác với khách hàng** hơn đàm phán hợp đồng.
4. **Phản hồi với thay đổi** hơn bám theo kế hoạch.

Vế bên phải vẫn có giá trị, nhưng vế bên trái được coi trọng hơn. Kèm theo là 12 nguyên tắc, nổi bật: giao phần mềm chạy được sớm và liên tục; chào đón thay đổi yêu cầu kể cả ở giai đoạn muộn; nghiệp vụ và lập trình viên làm việc cùng nhau hằng ngày; đo tiến độ bằng phần mềm chạy được; nhịp làm việc bền vững; đơn giản là tối đa hóa lượng công việc không cần làm; team tự tổ chức; định kỳ nhìn lại để cải tiến.

Agile là **triết lý**; các framework cụ thể gồm Scrum, Kanban, XP (Extreme Programming: pair programming, TDD, CI), SAFe (Agile cho tổ chức lớn).

### Scrum
Framework nhẹ để team giải quyết vấn đề phức tạp theo vòng lặp cố định gọi là **Sprint**. Dựa trên ba trụ cột: **minh bạch** (transparency), **thanh tra** (inspection), **thích nghi** (adaptation).

**Ba vai trò (Scrum Team)**
| Vai trò | Trách nhiệm |
|---|---|
| **Product Owner (PO)** | Tối đa hóa giá trị sản phẩm; quản lý và sắp xếp ưu tiên Product Backlog; quyết định làm gì trước |
| **Scrum Master (SM)** | Giúp team hiểu và áp dụng Scrum, gỡ trở ngại, điều phối sự kiện; là người phục vụ (servant leader), không phải sếp giao việc |
| **Developers** | Những người tạo ra Increment (dev, tester, designer…); tự tổ chức để quyết định *làm thế nào* |

**Năm sự kiện**
| Sự kiện | Mục đích | Thời lượng tối đa (sprint 1 tháng; sprint ngắn hơn thường ngắn hơn) |
|---|---|---|
| **Sprint** | Vòng lặp chứa mọi sự kiện khác, tạo ra Increment | Cố định, tối đa 1 tháng (thường 1–2 tuần) |
| **Sprint Planning** | Chọn việc từ Product Backlog, đặt Sprint Goal, lập kế hoạch | 8 giờ |
| **Daily Scrum** | Team đồng bộ tiến độ hướng tới Sprint Goal, phát hiện trở ngại | 15 phút, mỗi ngày |
| **Sprint Review** | Trình bày kết quả cho stakeholder, nhận phản hồi, cập nhật backlog | 4 giờ |
| **Sprint Retrospective** | Team nhìn lại cách làm việc, chọn cải tiến cho sprint sau | 3 giờ |

Daily Scrum thường xoay quanh ba câu: hôm qua tôi làm gì cho Sprint Goal, hôm nay làm gì, có gì cản trở. Đây không phải buổi báo cáo cho quản lý và không giải quyết chi tiết vấn đề (để sau buổi họp).

**Ba artifact và cam kết đi kèm**
| Artifact | Nội dung | Cam kết |
|---|---|---|
| **Product Backlog** | Danh sách có thứ tự mọi thứ cần làm cho sản phẩm | **Product Goal** |
| **Sprint Backlog** | Các mục được chọn cho sprint + kế hoạch thực hiện | **Sprint Goal** |
| **Increment** | Phần sản phẩm hoàn chỉnh, có thể dùng được, tạo ra trong sprint | **Definition of Done** |

**Backlog refinement** (grooming): hoạt động liên tục để làm rõ, chia nhỏ, ước lượng các mục backlog trước khi đưa vào sprint.

### User story, estimation và các khái niệm đi kèm
- **User story**: yêu cầu viết từ góc nhìn người dùng: *"Là một khách hàng, tôi muốn lưu giỏ hàng, để có thể mua tiếp vào lần sau."* Story tốt theo **INVEST**: Independent, Negotiable, Valuable, Estimable, Small, Testable.
- **Epic**: story lớn được chia thành nhiều story. **Task**: việc kỹ thuật để hoàn thành story.
- **Acceptance criteria**: điều kiện để **một story cụ thể** được chấp nhận, hay viết dạng Given–When–Then.
- **Definition of Done (DoD)**: tiêu chí chất lượng chung cho **mọi** story: code review xong, unit test pass, coverage đạt, tài liệu cập nhật, deploy staging thành công.
- **Story point**: đơn vị ước lượng **tương đối** độ lớn (khối lượng, độ phức tạp, rủi ro), thường theo dãy kiểu Fibonacci (1, 2, 3, 5, 8, 13). **Planning poker**: mọi người ra số cùng lúc rồi thảo luận chênh lệch.
- **Velocity**: tổng story point team hoàn thành mỗi sprint, dùng để dự báo; không dùng để so sánh giữa các team.
- **Burndown chart**: lượng việc còn lại theo thời gian trong sprint.

### Kanban
- Trực quan hóa công việc trên bảng các cột (To Do → In Progress → Review → Done).
- **Giới hạn WIP** (work in progress) mỗi cột để tránh làm dở dang quá nhiều việc, lộ ra điểm nghẽn.
- Luồng liên tục, không có sprint cố định; đo **lead time** (từ khi yêu cầu tới khi xong) và **cycle time** (từ khi bắt đầu làm tới khi xong).
- Hợp với team vận hành, hỗ trợ, nơi việc đến không đoán trước. Nhiều team kết hợp (Scrumban).

| | Scrum | Kanban |
|---|---|---|
| Nhịp | Sprint cố định | Liên tục |
| Vai trò | PO, SM, Developers | Không bắt buộc |
| Thay đổi giữa chừng | Hạn chế trong sprint | Bất cứ lúc nào |
| Đo lường | Velocity | Lead/cycle time |

### DevOps và CI/CD
- **DevOps**: văn hóa và thực hành gắn kết phát triển (Dev) và vận hành (Ops) để phát hành nhanh, ổn định.
- **Continuous Integration (CI)**: mỗi thay đổi được merge thường xuyên và tự động build, lint, test.
- **Continuous Delivery**: mọi bản build qua CI đều sẵn sàng deploy, deploy production bằng một thao tác. **Continuous Deployment**: tự động deploy production luôn khi pipeline xanh.
- Pipeline ví dụ: `push → build → lint → unit test → build Docker image → quét lỗ hổng → deploy staging → integration test → (duyệt) → deploy production`.
- Chiến lược deploy giảm rủi ro: **rolling update**, **blue-green**, **canary** (đưa phiên bản mới cho một phần nhỏ người dùng trước), feature flag.

## Cách hoạt động
Một sprint 2 tuần điển hình từ góc nhìn developer:
1. **Ngày 1 – Sprint Planning**: PO trình bày các mục ưu tiên cao; team hỏi rõ acceptance criteria, ước lượng, chọn lượng việc vừa sức (dựa trên velocity), đặt Sprint Goal, chia story thành task.
2. **Hằng ngày**: nhận task trên bảng, tạo branch, code, unit test, mở merge request, review cho đồng đội; Daily Scrum 15 phút; báo ngay trở ngại.
3. **Giữa sprint**: tham gia refinement cho các story của sprint sau.
4. **Story "Done"** khi đạt DoD: merge, CI xanh, deploy staging, tester xác nhận.
5. **Ngày cuối – Sprint Review**: demo tính năng chạy thật cho stakeholder, nhận phản hồi.
6. **Retrospective**: điều gì tốt, điều gì chưa tốt, chọn 1–2 cải tiến cụ thể cho sprint sau.

## Ví dụ
User story kèm acceptance criteria:
```
Story: Là người dùng đã đăng nhập, tôi muốn đổi mật khẩu để bảo vệ tài khoản.

Acceptance criteria:
- Given tôi nhập đúng mật khẩu hiện tại và mật khẩu mới hợp lệ,
  When tôi bấm "Đổi mật khẩu",
  Then mật khẩu được cập nhật và các phiên đăng nhập khác bị đăng xuất.
- Given mật khẩu hiện tại sai, When tôi gửi, Then hiển thị lỗi và không thay đổi gì.
- Mật khẩu mới tối thiểu 8 ký tự, khác mật khẩu cũ.

Task: API PUT /me/password; hash bcrypt; thu hồi session; unit test; cập nhật tài liệu API.
Estimate: 3 story points.
```

## Hiểu nhầm thường gặp
- **"Agile là không cần tài liệu, không cần kế hoạch"**: Agile vẫn lập kế hoạch và viết tài liệu, chỉ là vừa đủ và thường xuyên cập nhật.
- **"Scrum Master là quản lý dự án"**: SM là người hỗ trợ quy trình, không giao việc hay chấm điểm người khác.
- **"Daily Scrum là họp báo cáo"**: nó là buổi đồng bộ của Developers để đạt Sprint Goal.
- **"Story point = số giờ"**: story point là ước lượng tương đối, không quy đổi cố định ra giờ.
- **"Acceptance criteria và Definition of Done là một"**: AC riêng cho từng story; DoD chung cho mọi story.

## Câu hỏi và trả lời

**Các giai đoạn của SDLC?**
> - **SDLC (Software Development Life Cycle)**: chuỗi giai đoạn một phần mềm đi qua từ ý tưởng tới vận hành, giúp làm việc có kế hoạch và kiểm soát chất lượng.
>
> Các giai đoạn thường gặp, mỗi giai đoạn trả lời một câu hỏi:
> 1. **Lập kế hoạch**: có nên làm không, phạm vi, nguồn lực, rủi ro?
> 2. **Phân tích yêu cầu**: hệ thống phải làm gì (chức năng) và tốt tới đâu (hiệu năng, bảo mật)?
> 3. **Thiết kế**: làm thế nào: kiến trúc, dữ liệu, API?
> 4. **Phát triển**: viết code theo thiết kế.
> 5. **Kiểm thử**: có đúng yêu cầu không, có lỗi không?
> 6. **Triển khai**: đưa tới người dùng.
> 7. **Vận hành và bảo trì**: theo dõi, sửa lỗi, cải tiến.
>
> Ranh giới: các mô hình (Waterfall, Agile) không khác nhau ở *giai đoạn* mà ở *cách đi qua* chúng: Waterfall đi một lượt tuần tự; Agile đi lặp lại cả chu trình trong mỗi vòng ngắn. Tên và số giai đoạn khác nhau tùy tài liệu.

**Waterfall vs Agile? Khi nào dùng Waterfall?**
> - **Waterfall**: mô hình tuần tự: làm xong và chốt từng giai đoạn của SDLC rồi mới sang giai đoạn sau, người dùng thấy sản phẩm ở cuối.
> - **Agile**: nhóm phương pháp phát triển *lặp và tăng dần*: chia việc thành vòng ngắn, mỗi vòng giao một phần chạy được, lấy phản hồi để điều chỉnh.
>
> Tiêu chí chọn là *độ chắc chắn của yêu cầu và chi phí thay đổi*. Waterfall giả định yêu cầu biết rõ từ đầu và ít đổi: lập kế hoạch, dự toán, hợp đồng dễ, nhưng phát hiện sai muộn thì sửa rất đắt. Agile giả định yêu cầu sẽ thay đổi và học dần: phản hồi sớm, giảm rủi ro làm sai sản phẩm, nhưng khó cam kết trước phạm vi và ngày hoàn thành cố định.
>
> Waterfall hợp khi: yêu cầu ổn định và đặc tả rõ (dự án theo hợp đồng giá cố định, hệ thống theo quy định pháp lý), thay đổi về sau cực kỳ đắt (phần cứng, hệ thống nhúng an toàn), hoặc cần phê duyệt hồ sơ theo từng giai đoạn. Ranh giới: thực tế nhiều tổ chức dùng lai, vd khung kế hoạch tổng theo giai đoạn nhưng phát triển bên trong theo sprint.

**Bốn giá trị của Agile Manifesto?**
> - **Agile Manifesto**: tuyên ngôn năm 2001 của 17 người làm phần mềm, nêu bốn giá trị và mười hai nguyên tắc làm nền cho các phương pháp Agile.
>
> Bốn giá trị, mỗi giá trị so sánh hai thứ đều có ích nhưng ưu tiên vế trái:
> 1. **Cá nhân và sự tương tác** hơn quy trình và công cụ.
> 2. **Phần mềm chạy được** hơn tài liệu đầy đủ.
> 3. **Cộng tác với khách hàng** hơn đàm phán hợp đồng.
> 4. **Phản hồi với thay đổi** hơn làm theo kế hoạch.
>
> Ý chung: phần mềm là việc khám phá, nên ưu tiên những thứ giúp học nhanh và điều chỉnh nhanh. Ranh giới: tuyên ngôn nói rõ "vế phải vẫn có giá trị"; Agile không có nghĩa là không tài liệu, không kế hoạch, mà là không để chúng cản việc giao giá trị.

**Ba vai trò, năm sự kiện, ba artifact của Scrum?**
> - **Scrum**: framework Agile tổ chức công việc thành các vòng có độ dài cố định gọi là **Sprint**, dựa trên ba trụ cột minh bạch, kiểm tra, thích ứng.
>
> Theo Scrum Guide (bản 2020 gọi vai trò là *accountabilities*):
> - **Ba vai trò**: **Product Owner** chịu trách nhiệm tối đa hóa giá trị sản phẩm, quản lý và sắp xếp Product Backlog; **Scrum Master** giúp team hiểu và áp dụng Scrum, gỡ trở ngại; **Developers** là những người làm ra Increment mỗi sprint (không chỉ lập trình viên).
> - **Năm sự kiện**: **Sprint** (vỏ chứa mọi sự kiện khác); **Sprint Planning** (chọn việc và đặt Sprint Goal); **Daily Scrum** (15 phút mỗi ngày, Developers kiểm tra tiến độ tới Sprint Goal); **Sprint Review** (trình bày kết quả cho stakeholder, điều chỉnh backlog); **Sprint Retrospective** (team cải tiến cách làm việc).
> - **Ba artifact**, mỗi cái gắn một cam kết: **Product Backlog** (cam kết: Product Goal); **Sprint Backlog** (cam kết: Sprint Goal); **Increment** (cam kết: Definition of Done).
>
> Ranh giới: Backlog Refinement là hoạt động liên tục, không phải sự kiện chính thức. Scrum Master không phải quản lý dự án hay sếp của team.

**Sprint dài bao lâu? Có được thay đổi phạm vi trong sprint không?**
> - **Sprint**: khoảng thời gian cố định (timebox) trong đó team tạo ra một Increment có giá trị.
> - **Sprint Goal**: mục tiêu duy nhất của sprint, lý do sprint tồn tại. **Sprint Backlog**: Sprint Goal cộng các việc được chọn và kế hoạch thực hiện.
>
> Sprint tối đa một tháng, thường 1–2 tuần; độ dài giữ cố định để tạo nhịp đều. Quy tắc về thay đổi: *Sprint Goal không đổi*, không thay đổi nào được đe dọa nó, và chất lượng không giảm; còn *Sprint Backlog có thể được điều chỉnh* (thêm, bớt, làm rõ việc) khi team hiểu thêm, thông qua thương lượng với Product Owner. Việc mới phát sinh lớn thường đưa vào Product Backlog cho sprint sau.
>
> Ranh giới: nếu Sprint Goal trở nên vô nghĩa (đổi hướng kinh doanh), chỉ Product Owner có quyền hủy sprint, rồi bắt đầu Sprint Planning mới. Sprint ngắn cho phản hồi nhanh và giảm rủi ro nhưng tốn tỷ lệ thời gian cho các sự kiện nhiều hơn.

**Definition of Done khác acceptance criteria?**
> - **Definition of Done (DoD)**: tiêu chuẩn chất lượng *chung cho mọi* hạng mục để được coi là xong, vd code đã review, có unit test, CI xanh, đã deploy lên staging, tài liệu API cập nhật.
> - **Acceptance criteria (AC)**: điều kiện *riêng của một* user story để được chấp nhận về mặt nghiệp vụ, vd "nhập sai mật khẩu 5 lần thì khóa tài khoản 15 phút".
>
> Tiêu chí phân biệt là *phạm vi áp dụng*: DoD áp cho mọi việc và nói về *chất lượng*; AC áp cho một story và nói về *hành vi mong đợi*. Một story chỉ xong khi đạt *cả hai*: đúng hành vi (AC) và đúng chuẩn chất lượng (DoD).
>
> Ranh giới: DoD là cam kết gắn với Increment trong Scrum, team có thể nâng dần theo thời gian. AC thường viết dạng Given/When/Then để chuyển thành test tự động.

**Story point, velocity là gì?**
> - **User story**: mô tả yêu cầu từ góc nhìn người dùng: "Là <ai>, tôi muốn <gì>, để <lợi ích>".
> - **Story point**: đơn vị *tương đối* ước lượng độ lớn của một story, gộp khối lượng, độ phức tạp và độ không chắc chắn; thường dùng dãy gần Fibonacci (1, 2, 3, 5, 8, 13).
> - **Velocity**: tổng story point team hoàn thành (đạt DoD) trong một sprint.
>
> Story point ước lượng *so sánh* ("story này lớn gấp đôi story kia") thay vì đoán giờ, vì con người so sánh tương đối tốt hơn đoán tuyệt đối, và nó không phụ thuộc ai làm. Velocity trung bình vài sprint gần nhất giúp team dự báo làm được bao nhiêu trong sprint tới và bao lâu thì xong một khối backlog. Dãy Fibonacci giãn dần thể hiện việc càng lớn càng khó ước lượng chính xác; story quá lớn (13 trở lên) nên tách nhỏ.
>
> Ranh giới: story point của team này không so được với team khác, và velocity là công cụ lập kế hoạch của team, không phải chỉ số năng suất để đánh giá; dùng nó làm KPI sẽ dẫn tới thổi phồng điểm. Story point không có trong Scrum Guide, đây là thực hành phổ biến đi kèm.

**Scrum vs Kanban?**
> - **Scrum**: framework làm việc theo sprint cố định, có vai trò, sự kiện, artifact quy định rõ.
> - **Kanban**: phương pháp quản lý *dòng chảy* công việc: trực quan hóa việc trên bảng theo cột trạng thái, *giới hạn số việc đang làm* (WIP limit) ở mỗi cột, kéo việc mới khi có chỗ.
>
> Tiêu chí phân biệt là *nhịp làm việc*: Scrum chia thời gian thành sprint, cam kết một nhóm việc cho mỗi sprint, đo bằng velocity; Kanban chảy liên tục, không có sprint, việc nào xong thì giao, đo bằng *lead time*/*cycle time* (thời gian một việc đi qua hệ thống) và throughput. Scrum hợp với phát triển sản phẩm cần mục tiêu theo chu kỳ; Kanban hợp với việc đến liên tục, khó lên kế hoạch trước (vận hành, hỗ trợ, sửa lỗi).
>
> Ranh giới: Kanban không quy định vai trò hay cuộc họp nào; bảng có cột "To do / Doing / Done" mà không có WIP limit chưa phải Kanban. Nhiều team dùng lai (Scrumban): sprint của Scrum với bảng và WIP limit của Kanban.

**CI/CD là gì? Một pipeline gồm những bước nào?**
> - **CI (Continuous Integration)**: mọi người tích hợp code vào nhánh chính thường xuyên (ít nhất mỗi ngày), mỗi lần đều được build và test tự động.
> - **CD**: **Continuous Delivery** (mọi thay đổi qua CI luôn ở trạng thái *sẵn sàng* deploy, deploy production bằng một thao tác) hoặc **Continuous Deployment** (deploy production *tự động* không cần người bấm).
> - **Pipeline**: chuỗi bước tự động chạy mỗi khi có thay đổi.
>
> Mục tiêu chung: phát hiện lỗi sớm khi thay đổi còn nhỏ, và biến việc phát hành thành việc thường ngày, ít rủi ro. Pipeline tiêu biểu: **checkout** code → **build** (`go build`) → **kiểm tra tĩnh** (`go vet`, linter, format) → **unit test** (kèm `-race`, coverage) → **quét bảo mật** (dependency, secret) → **đóng gói** (build Docker image, gắn tag theo commit) → **integration test** → **deploy staging** → kiểm tra (smoke test) → **deploy production** (thủ công hoặc tự động, có thể theo canary/rolling) → theo dõi và sẵn sàng rollback.
>
> Ranh giới: CI không phải là "có server chạy Jenkins"; nhánh sống hàng tuần mới merge thì vẫn không có CI dù pipeline đẹp. Pipeline chậm hoặc test chập chờn làm mọi người bỏ qua nó, nên giữ nhanh và tin cậy.

## Liên quan
- [02-backend-architecture.md](02-backend-architecture.md): tài liệu giải pháp ở giai đoạn Design; Docker, k8s khi deploy.
- [11-unit-testing.md](11-unit-testing.md): test trong DoD và CI.
- [13-git-and-version-control.md](13-git-and-version-control.md): branching và merge request trong quy trình.
