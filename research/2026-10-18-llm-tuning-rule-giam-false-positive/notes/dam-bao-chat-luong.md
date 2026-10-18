# Đảm bảo chất lượng khi tuning rule

Phạm vi góc này: các cơ chế kiểm chứng và bảo đảm khi sửa rule để giảm FP (không lặp lại các bước tuning, không đi sâu phần LLM).

## 1. Khi tuning cần đảm bảo những gì

### Kết luận ngắn
Có 6 yêu cầu được nhắc lặp lại trong tài liệu: (a) không mất TP / không tạo điểm mù, (b) rule vẫn bền trước biến thể của kỹ thuật tấn công và giữ được coverage ATT&CK, (c) exclusion không thành chỗ trốn cho attacker, (d) có truy vết ai sửa gì, vì sao, (e) đáp ứng yêu cầu giám sát của các chuẩn tuân thủ, (f) không làm query hỏng hay chậm. Mức chắc chắn **cao** cho (a)–(d), vì có nguồn bậc 1 (MITRE, Microsoft, CTID) và sự cố công khai. Mức **trung bình** cho (e), vì chỉ đọc được bản diễn giải thứ cấp chứ chưa đọc văn bản chuẩn gốc. Mức **thấp–trung bình** cho (f), vì ít nguồn chuyên về hiệu năng.

### Phát hiện có nguồn

**(a) Exclusion tạo ra điểm mù, nên chỉ dùng sau khi đã rõ nguyên nhân gốc**
- Microsoft viết thẳng: "Creating an exclusion or an allow indicator creates a protection gap. Use these techniques only after you determine the root cause of the issue." Tài liệu xếp exclusion/indicator ở bước cuối ("only if necessary"), sau khi đã phân loại alert, suppress alert cho entity đã biết, xem lại hành động remediation và gửi file cho Microsoft phân tích. — [Overview of exclusions and indicators in Microsoft Defender for Endpoint](https://learn.microsoft.com/en-us/defender-endpoint/navigate-defender-endpoint-antivirus-exclusions) (bậc 1, ms.date 2026-07-02)
- Cùng tài liệu: một process exclusion trên bất kỳ hệ điều hành nào "prevents network protection from inspecting traffic or enforcing rules for that specific process". Trên Linux, "global exclusions" tắt cả alert antivirus lẫn alert EDR. Hai ví dụ này cho thấy phạm vi của một exclusion thường rộng hơn người tạo nó tưởng. — [như trên](https://learn.microsoft.com/en-us/defender-endpoint/navigate-defender-endpoint-antivirus-exclusions) (bậc 1, 2026-07)
- CTID định nghĩa một analytic **chính xác** (accurate) là analytic có ít FP **và** ít FN, còn analytic **bền** (robust) là analytic vẫn chính xác khi attacker đổi cách thực hiện kỹ thuật. Analytic gắn với công cụ hay artifact cụ thể thì dễ bị né. Từ đó suy ra tuning chỉ nhằm giảm FP mà làm tăng FN là đi ngược mục tiêu. — [Summiting the Pyramid: Bring the Pain](https://ctid.mitre.org/blog/2024/12/16/summiting-the-pyramid-bring-the-pain/) (bậc 1, 2024-12-16); [trang dự án](https://ctid.mitre.org/projects/summiting-the-pyramid) (bậc 1)

**(b) Coverage ATT&CK**
- Elastic detection-rules kiểm tra trường MITRE ATT&CK của rule với file `attack-v13.1.0.json.gz` ngay khi load rule. Nhờ đó tag technique không thể sai hoặc lỗi thời. — [Internals of the detection-rules Repo](https://dac-reference.readthedocs.io/en/latest/internals_of_the_detection_rules_repo.html) (bậc 1, docs DaC của Elastic, không rõ ngày)
- Sách "Practical Threat Detection Engineering" (Packt, 2023) chia hai loại coverage. Coverage "độ trung thực thấp" là việc map rule lên ma trận ATT&CK. Coverage "độ trung thực cao" đo bằng validation, detection drift và volatility. — [Packt: chapter 15 summary](https://subscription-non-live.prod.packtpub.com/book/security/9781801076715/15/ch15lvl1sec76/summary) (bậc 2, 2023; mới đọc phần tóm tắt chương)

**(c) Attacker lợi dụng exclusion**
- MITRE ATT&CK T1564.012 (Hide Artifacts: File/Path Exclusions) mô tả việc attacker đặt payload vào thư mục hoặc tên file mà công cụ bảo mật bỏ qua. Exclusion đó có thể là mặc định hoặc do admin thêm vì hiệu năng. Attacker có thể dò để tìm và xác minh exclusion. Ví dụ thực tế: APT38 thêm exclusion Defender cho `C:\Windows\System32`; Turla đặt file cài LunarWeb vào thư mục bị loại khỏi quét; ransomware "The Gentlemen" dùng PowerShell tự thêm mình vào exclusion list của EDR. Mitigation M1049: "Review and audit file and folder exclusions, and limit them to what is required". Detection DET0051: giám sát việc tạo/sửa file trong thư mục bị loại trừ và đối chiếu với execution hoặc parent process bất thường. — [MITRE ATT&CK T1564.012](https://attack.mitre.org/techniques/T1564/012/) (bậc 1, tạo 2024-03-29, sửa 2026-05-12, ATT&CK v20)
- Tháng 1/2022, có báo cáo rằng mọi user local trên Windows 10 21H1/21H2 đọc được exclusion list của Defender bằng `reg query`. Exclusion đặt qua Group Policy cũng đọc được và có thể áp lên nhiều máy. BleepingComputer thử nghiệm: mẫu Conti bị Defender chặn khi chạy ở vị trí thường, nhưng khi chạy từ thư mục được exclude thì "no warning", và mẫu đã mã hóa được máy. — [Microsoft Defender weakness lets hackers bypass malware detection](https://www.bleepingcomputer.com/news/security/microsoft-defender-weakness-lets-hackers-bypass-malware-detection/amp/) (bậc 2, Ionut Ilascu, 2022-01-13)
- SafeBreach cảnh báo allowlist chỉ dựa trên tên process là không đủ, vì attacker đổi tên dễ dàng. — [SafeBreach: Dark side of EDR](https://www.safebreach.com/blog/dark-side-of-edr-offensive-tool/) (bậc 2, 2024-04-19; thông tin lấy từ snippet tìm kiếm, chưa mở trang)
- Beazley Security quan sát thấy attacker dùng WDAC policy tùy chỉnh để allowlist bộ công cụ của mình và chặn agent EDR. — [Disabling EDR with WDAC](https://labs.beazley.security/articles/disabling-edr-with-wdac) (bậc 2, 2025-03-06; theo snippet, chưa mở trang)

**(d) Truy vết / audit trail**
- Trong pipeline Detection-as-Code của NVISO cho Sentinel, mỗi giá trị filter-out (watchlist CSV trong `filters/`) được thêm qua pull request. Cột `Tags` dùng để ghi ticket id. Pipeline build ước tính tác động bằng cách đếm số incident/alert trong 30 ngày có chứa giá trị mới. Sau đó "a fellow detection engineer reviews and approves or rejects the changes". Bản thân pipeline không có audit log riêng: lịch sử Git (PR, commit "Merged PR <n>") đóng vai trò audit trail. NVISO còn để chế độ validation là "Optional", nên pipeline lỗi vẫn không chặn merge. — [NVISO: Practicing Detection-as-Code – Tuning – Part 8](https://blog.nviso.eu/2025/11/25/detection-engineering-practicing-detection-as-code-tuning-part-8/) (bậc 2, 2025-11-25)
- Phần Monitoring (Part 7) của cùng series có check "Detection tampering": "Monitor and report when any detections from our repository that are disabled or deleted", tức là phát hiện rule bị tắt hoặc xóa bởi người ngoài danh sách được phép, dựa trên audit log. — [NVISO Part 7 – Monitoring](https://blog.nviso.eu/2025/10/07/detection-engineering-practicing-detection-as-code-monitoring-part-7/) (bậc 2, 2025-10-07)
- Elastic dùng `version.lock.json` để lưu sha256, số version và loại của từng rule; rule bị loại bỏ ghi trong `deprecated_rules.json`. — [Internals of the detection-rules Repo](https://dac-reference.readthedocs.io/en/latest/internals_of_the_detection_rules_repo.html) (bậc 1)

**(e) Tuân thủ** (tất cả đều là nguồn thứ cấp, chưa đọc văn bản gốc)
- PCI DSS v4.0: Req 10.4.1.1 yêu cầu dùng cơ chế tự động để review audit log (SIEM được chấp nhận). Req 10.7.2 yêu cầu phát hiện và cảnh báo khi các hệ thống kiểm soát an ninh trọng yếu bị lỗi, kể cả IDS, FIM, anti-malware và chính SIEM. Cả hai bắt buộc từ 31/3/2025. — [Motadata: PCI DSS Requirement 10](https://www.motadata.com/blog/pci-dss-requirement-10) (bậc 3, vendor), [Steampipe/Powerpipe benchmark 10.4.1.1](https://hub.powerpipe.io/mods/turbot/steampipe-mod-aws-compliance/controls/benchmark.pci_dss_v40_requirement_10_4_1_1) (bậc 2), [Microsoft Entra: PCI requirement 10](https://learn.microsoft.com/en-sg/Entra/standards/pci-requirement-10) (bậc 1 về hướng dẫn map, không phải chuẩn gốc)
- ISO/IEC 27001:2022 Annex A 8.16 "Monitoring activities" (control mới của bản 2022) yêu cầu giám sát mạng, hệ thống và ứng dụng để tìm hành vi bất thường. Checklist audit thứ cấp coi log tuning của SOC và hồ sơ thay đổi correlation rule của SIEM là bằng chứng. Hệ thống có "unmanageable volume of false positives" dẫn đến alert fatigue sẽ bị đánh fail. — [HighTable: ISO 27001 8.16 audit checklist](https://hightable.io/iso-27001-annex-a-8-16-audit-checklist) (bậc 3), [Advisera: control 8.16](https://advisera.com/iso27001/control-8-16-monitoring-activities/) (bậc 2)
- SOC 2: CC8.1 (change management) thường lấy bằng chứng từ yêu cầu approve PR, cấu hình CI/CD và hồ sơ deploy có phê duyệt. CC7.x (monitoring) lấy bằng chứng từ alert và dashboard SIEM. Các nguồn thứ cấp map CC7.1/CC7.2 không nhất quán. — [Presencis: SOC 2 CC8.1](https://presencis.com/regulations/soc-2/article-CC8-1/) (bậc 3)

**(f) Hiệu năng / tính đúng của query**
- Microsoft Learn (theo kết quả tìm kiếm) nói deployment qua Sentinel Repositories "doesn't validate the content except to confirm it's in the correct JSON format". Lỗi KQL vì vậy lọt qua nếu không có bước kiểm tra riêng. — [Microsoft Learn: Deploy custom content from your repository](https://learn.microsoft.com/he-il/azure/sentinel/ci-cd-custom-content) (bậc 1, theo snippet, chưa mở trang)
- Tim Groothuis chạy query trên ADX emulator với dữ liệu mẫu và bắt được lỗi dùng sai `mv-expand`, loại lỗi mà lint JSON/YAML bỏ qua. — [Improving automated Sentinel detection validation](https://medium.com/@TimGroothuis/improving-automated-sentinel-detection-validation-02f91a9f4a21) (bậc 2/3, theo snippet)
- NVISO tránh xóa rồi upload lại cả watchlist khi sync filter. Lý do: SLA ingest 5 phút có thể khiến rule chạy trong lúc không có dữ liệu filter, tức là một khoảng FP hoặc điểm mù tạm thời do chính quy trình deploy gây ra. — [NVISO Part 8](https://blog.nviso.eu/2025/11/25/detection-engineering-practicing-detection-as-code-tuning-part-8/) (bậc 2, 2025-11)

### Nhận định
- Một exclusion có ba tầng rủi ro: (1) nó che luôn TP thật nằm trong phạm vi exclusion; (2) attacker có thể đọc được nó (registry, file config, rule public) rồi cố tình rơi vào phạm vi đó; (3) nó rộng hơn dự định, ví dụ process exclusion tắt luôn cả network protection. Vì vậy một đề xuất exclusion tốt nên neo vào thuộc tính khó giả mạo (hash, chữ ký, đường dẫn đầy đủ kết hợp parent process, hoặc entity cụ thể như host/user) thay vì tên process hay wildcard path.
- Với đầu ra của LLM, các yêu cầu (a)–(d) có thể đổi thành checklist máy kiểm được: đề xuất có dùng wildcard hay tên process trần không, có thu hẹp tag ATT&CK không, có kèm ticket/lý do không, có hạn dùng không.

### Khoảng trống
- Chưa đọc văn bản gốc PCI DSS v4.0.1, ISO/IEC 27002:2022 §8.16 và AICPA TSC: cả ba đều cần tài khoản hoặc trả phí. Chưa tìm thấy chuẩn nào yêu cầu cụ thể "quy trình tuning rule". Các chuẩn chỉ yêu cầu giám sát tự động, quản lý thay đổi và phát hiện khi control bị lỗi.
- Thiếu nguồn bậc 1 đo tác động hiệu năng của exclusion hay watchlist lớn lên query SIEM.

## 2. Đảm bảo bằng cách nào

### Kết luận ngắn
Ngành đã hội tụ về một chuỗi kiểm chứng nhiều lớp. Lớp tĩnh gồm schema, lint và query parse. Lớp động gồm test dương (rule phải bắt được mẫu tấn công) và test âm (rule không được kêu trên log sạch), sau đó là backtest trên dữ liệu lịch sử để đếm alert trước/sau. Lớp con người là peer review qua PR. Khi chạy thật thì có giai đoạn chạy "câm" (shadow/preview/silent), và sau deploy thì giám sát fire-rate, health và tampering. Mức chắc chắn **cao** cho các lớp này, vì có repo mã nguồn và docs chính thức. Mức **trung bình** cho shadow/canary, vì chủ yếu là khuyến nghị chứ chưa có tiêu chuẩn chung.

### Phát hiện có nguồn

**Detection-as-code: lint, schema và query validation trong CI**
- SigmaHQ chạy GitHub Actions trên mọi push/PR. Workflow `sigma-test.yml` gồm yaml-lint, test logsource, `test_rules.py`, `sigma check --fail-on-error --fail-on-issues --validation-config tests/sigma_cli_conf.yml` và kiểm tra trùng ID. — [SigmaHQ sigma-test.yml](https://github.com/SigmaHQ/sigma/blob/master/.github/workflows/sigma-test.yml) (bậc 1, source code, đọc ngày 2026-10-18)
- Elastic detection-rules: `make test` hoặc `python -m detection_rules test` chạy unit test cho toàn bộ rule; `validate-rule`/`validate-all` kiểm tra schema (Marshmallow dataclass). Query KQL/EQL được parse thành AST và đối chiếu trường với schema ECS, integration và endpoint. ES|QL không có parser local nên cần remote validation trên stack thật. — [Internals of the detection-rules Repo](https://dac-reference.readthedocs.io/en/latest/internals_of_the_detection_rules_repo.html) (bậc 1)
- Theo tài liệu của Elastic, các trường `exceptions_list`, `actions` và `response_actions` viết inline chỉ được kiểm tra rất sơ sài, nên lỗi định dạng thường chỉ lộ ra khi Kibana từ chối import. Đây là chỗ cần tự viết thêm test. — [như trên](https://dac-reference.readthedocs.io/en/latest/internals_of_the_detection_rules_repo.html) (bậc 1)
- Sentinel: kho community Azure-Sentinel kiểm tra cú pháp KQL và schema detection (frequency, trigger, connector ID) ở bước PR. Northwave tự viết framework unittest để test analytics rule từ Terraform plan, vì "no public solution available". Một thread Tech Community (2026-07) nhắc hai điểm: workspace non-prod có thể bị drift schema so với prod, và việc đổi `id` rule trong PR có thể sinh rule trùng. — [Northwave: Testing Sentinel Analytic Rules at Scale](https://northwave-cybersecurity.com/threat-intel-research/soc-testing-microsoft-sentinel-analytic-rules-at-scale) (bậc 2), [Tech Community thread](https://techcommunity.microsoft.com/discussions/microsoft-security/custom-detection-rules-as-code-in-sentinel-repositories-what-your-pipeline-owns-/4536196/replies/4539309) (bậc 3); các ý này lấy từ snippet tìm kiếm
- Panther: unit test được viết ngay trong YAML của detection và chạy bằng Panther Analysis Tool (PAT) trong CI (có hướng dẫn cho CircleCI và GitHub Actions). `pantherlog` dùng để validate schema log và chạy unit test. — [Panther: CI/CD for Panther Content](https://docs.panther.com/panther-developer-workflows/ci-cd) (bậc 1, theo snippet)

**Test dương và test âm bằng dữ liệu log (regression)**
- SigmaHQ regression testing: rule có status `test` hoặc `stable` **bắt buộc** trỏ tới một `info.yml` chứa test case. Mỗi test case đi kèm mẫu event thật (EVTX hoặc JSON/NDJSON) và `match_count` kỳ vọng. Runner `tests/regression_tests_runner.py` chạy trên mọi push/PR và fail nếu số match không đúng. — [SigmaHQ regression_data/README.md](https://github.com/SigmaHQ/sigma/blob/master/regression_data/README.md) (bậc 1, đọc 2026-10-18)
- SigmaHQ "Goodlog Tests": `goodlog-tests.yml` chạy toàn bộ rule Windows trên các baseline log sạch Win7, Win10 và Win11 (Nextron `evtx-baseline` v0.8.5, công cụ `evtx-sigma-checker`). Match nào ngoài danh sách `known-FPs.csv` (khoảng 86 dòng) sẽ bị báo. Đây là cơ chế chặn rule gây FP ngay từ CI, và danh sách FP đã biết cũng được version hóa trong repo. — [SigmaHQ goodlog-tests.yml](https://github.com/SigmaHQ/sigma/blob/master/.github/workflows/goodlog-tests.yml), [known-FPs.csv](https://github.com/SigmaHQ/sigma/blob/master/.github/workflows/known-FPs.csv) (bậc 1, đọc 2026-10-18)
- Splunk security_content + attack_data: attack_data là bộ dataset tấn công đã curate, dùng để test content. `contentctl` build và test bằng cách replay dữ liệu, rồi báo cáo kết quả. Nếu có Enterprise Security, nó chạy thêm integration test cho risk action và message. — [Splunk Lantern: Improving your security detection development processes](https://lantern.splunk.com/Security_Use_Cases/Threat_Hunting/Improving_your_security_detection_development_processes) (bậc 1, theo snippet), [splunk/attack_data](https://github.com/splunk/attack_data) (bậc 1)
- Bài học từ Splunk (2020-12-04): cách test mỗi detection bằng cách dựng Attack Range (môi trường lab thật trên AWS) cho mỗi PR đã thất bại. Mỗi file test mất hơn 30 phút, hàng đợi hơn 10 job phải chờ khoảng 16 giờ. Chạy nightly thì đụng giới hạn 5 giờ của CircleCI (một lần chạy chỉ test được 10 detection rồi timeout), và test lỗi bỏ lại tài nguyên AWS mồ côi. Họ chuyển sang tách việc sinh dữ liệu tấn công thành repo attack_data rồi replay. — [CI/CD Detection Engineering: Failing, Part 3](https://www.splunk.com/en_us/blog/security/ci-cd-detection-engineering-failing-part-3.html) (bậc 1, José Enrique Hernandez, 2020-12-04)
- Elastic dùng Red Team Automation (`rta/`) để giả lập kỹ thuật tấn công; `rule-mapping.yaml` map rule với RTA tương ứng. — [Internals of the detection-rules Repo](https://dac-reference.readthedocs.io/en/latest/internals_of_the_detection_rules_repo.html) (bậc 1)
- Một hướng dẫn CI/CD cho Sigma (bậc 3) khuyên mỗi rule phải có fixture dương (event phải match) và fixture âm (event không được match), thiếu một trong hai thì CI fail. — [decryptiondigest: Sigma rules CI/CD](https://www.decryptiondigest.com/blog/sigma-rules-cicd-pipeline-siem-deployment) (bậc 3, theo snippet)

**Giả lập tấn công: Atomic Red Team, Stratus Red Team, purple team, BAS**
- Stratus Red Team (Datadog) được mô tả là "Atomic Red Team™ for the cloud". Đây là binary Go giả lập từng kỹ thuật tấn công trên AWS, Azure, GCP, Entra ID và Kubernetes, có map ATT&CK. Mỗi kỹ thuật đi qua các pha warmup, detonate và cleanup. — [DataDog/stratus-red-team](https://github.com/DataDog/stratus-red-team) (bậc 1)
- Theo các nguồn cộng đồng: Atomic Red Team gồm các test nhỏ, mỗi test map một technique, chạy được riêng lẻ. Vòng purple team thường là chạy atomic, kiểm tra SIEM, tune, rồi chạy lại. Kết quả được ghi vào VECTR để coverage thành con số theo dõi được. — kết quả tìm kiếm tổng hợp, chủ yếu bậc 3 (vd [redfoxsec: purple team exercises](https://www.redfoxsec.com/blog/purple-team-exercises-how-to-run-them-and-what-youll-learn-about-your-defences)); chưa đọc docs gốc của Atomic Red Team
- Có một dự án mã nguồn mở tên "sigma-regression-testing" map rule Sigma với test Atomic Red Team và sinh báo cáo pass/fail (talk tại BlueTeamCon 2026). — [BlueTeamCon 2026 schedule](https://blueteamcon2026.sched.com/event/2P73O) (bậc 3, chưa xem repo)

**Backtest / replay trên dữ liệu lịch sử, preview, shadow**
- Elastic khuyên dùng rule preview trên khoảng 7–14 ngày dữ liệu lịch sử trước khi bật rule: kiểm tra TP mong đợi, FP rõ ràng và "missing detections". Nếu có hoạt động hợp lệ thì "refine the query or plan to add exceptions before enabling the rule". Elastic cũng khuyên test trong một Kibana space riêng để manual run không ảnh hưởng alert production. Lưu ý: manual run tạo alert và action thật, nên phải snooze action trước. — [Elastic: Validate and test rules](https://www.elastic.co/docs/solutions/security/detect-and-alert/validate-and-test-rules) (bậc 1, không rõ ngày)
- NVISO ước tính tác động khi build PR: đếm số incident/alert trong 30 ngày gần nhất có chứa entity sắp được filter. Đây là dạng backtest đơn giản cho exclusion. — [NVISO Part 8](https://blog.nviso.eu/2025/11/25/detection-engineering-practicing-detection-as-code-tuning-part-8/) (bậc 2, 2025-11)
- Datadog Cloud SIEM có "Historical Jobs" để chạy rule trên log lịch sử. Grab xây hệ thống backtest rule trên Spark, nói rằng nhờ đó không còn cần shadow mode khi onboard rule (bối cảnh là rule chống gian lận, không phải SIEM). — [Grab: Automatic rule backtesting](https://engineering.grab.com/automatic-rule-backtesting) (bậc 2, theo snippet)
- Một bài kỹ thuật đề xuất "diff backtest": so kết quả query cũ với query mới để bắt các thay đổi vô ý, chẳng hạn AND bị đổi thành OR. — [Blake Hensley: Automation for Threat Detection Quality Assurance](https://medium.com/@BlakeHensleyy/automation-for-threat-detection-quality-assurance-4a7d9acbcc4e) (bậc 3, theo snippet)
- Giới hạn của backtest: dữ liệu lịch sử chỉ chứa những gì đã được điều tra và gắn nhãn, nên nó đánh giá thấp những gì đã bỏ sót. Số alert thấp không chứng minh rule chính xác. — [Brandon Lyons: The Detection Engineering Baseline Part 3](https://brandontlyons.substack.com/p/the-detection-engineering-baseline-394) (bậc 2/3, theo snippet)
- Chế độ "Silent" ở Stellar Cyber: rule vẫn chạy và đếm số lần lẽ ra đã kích hoạt trong 7 ngày nhưng không gửi alert. Đây là một dạng shadow deploy có sẵn trong sản phẩm. — [Stellar Cyber: Detection Management System](https://docs.stellarcyber.ai/6.6.x/Configure/Detection-Management-System.htm) (bậc 1, theo snippet)

**Peer review và approval**
- NVISO: PR do một detection engineer khác review rồi approve hoặc reject. — [NVISO Part 8](https://blog.nviso.eu/2025/11/25/detection-engineering-practicing-detection-as-code-tuning-part-8/) (bậc 2)
- SOC 2 CC8.1 lấy bằng chứng từ yêu cầu approve PR và hồ sơ deploy (xem mục 1e).

**Giám sát sau deploy**
- NVISO Part 7 có 4 check: trigger rate (trung bình, độ lệch chuẩn trong 30 ngày), tần suất xuất hiện của entity, tampering (rule bị tắt hoặc xóa) và health (tỉ lệ lỗi theo ngày/tháng, rule bị tự động tắt sau nhiều lần lỗi). Ngưỡng mặc định là 20 lỗi/tháng và 70 lỗi/ngày. Kết quả được tạo thành work item trên Azure DevOps. — [NVISO Part 7](https://blog.nviso.eu/2025/10/07/detection-engineering-practicing-detection-as-code-monitoring-part-7/) (bậc 2, 2025-10-07)
- "Detection decay" (rule im lặng): rule vẫn parse đúng, tham chiếu trường hợp lệ, nhưng trả về 0 match vì trường bị đổi tên, để trống hoặc đổi nghĩa sau khi parser hay log source thay đổi. Cách xử lý được đề xuất là lập baseline fire-rate cho từng rule và cảnh báo khi rate sập về 0. Checklist của Hunters lưu ý rule im lặng thường không ai để ý, vì KPI chỉ nhìn vào alert ồn. — [SOC Prime: Detection Validation and Decay](https://socprime.com/?p=52931) (bậc 2/3, vendor), [Hunters: Detection Engineering Checklist](https://www.hunters.security/hubfs/2025%20Research%20Paper/Detection%20Engineering%20Checklist%20for%20SOC%20Teams%20%20(3).pdf?hsLang=en) (bậc 2/3, 2025); theo snippet

**Exclusion có hạn dùng / review định kỳ**
- MITRE M1049 yêu cầu "review and audit" exclusion và giới hạn ở mức tối thiểu cần thiết. — [T1564.012](https://attack.mitre.org/techniques/T1564/012/) (bậc 1)
- Repo SigmaHQ giữ `known-FPs.csv` trong Git, nên mọi thay đổi danh sách FP đều đi qua review. — [known-FPs.csv](https://github.com/SigmaHQ/sigma/blob/master/.github/workflows/known-FPs.csv) (bậc 1)

### Nhận định
- Nếu đóng vai "cổng chất lượng" cho một đề xuất tuning (dù do người hay LLM viết), đây là chuỗi khả thi nhất: (1) lint, schema và parse query; (2) test dương: rule mới vẫn match mọi mẫu TP/attack đã lưu (regression_data, attack_data, các alert TP lịch sử); (3) test âm: rule mới không match các FP đã gán nhãn, và không kêu trên baseline sạch; (4) diff backtest N ngày: số alert trước/sau, liệt kê từng alert bị loại để người review nhìn thấy, và đánh dấu riêng alert nào đã từng là TP; (5) review PR có ticket và lý do; (6) chạy câm hoặc preview vài ngày; (7) theo dõi fire-rate và health, kèm ngày hết hạn cho exclusion.
- Bài học từ Splunk 2020: replay dataset có sẵn rẻ và nhanh hơn nhiều so với dựng lab tấn công cho mỗi PR. Lab hay BAS nên để chạy định kỳ chứ không gắn vào từng thay đổi.
- Trường hợp riêng của rule IoC: test dương có thể là "IoC còn hiệu lực trong feed vẫn match", còn test âm dùng warninglist (phần này do researcher IoC lo).

### Khoảng trống
- Chưa tìm thấy nguồn bậc 1 mô tả cụ thể canary deploy cho detection rule (bật cho một phần tenant hay host trước). Khái niệm này có trong thực tế MSSP/vendor nhưng không có docs công khai.
- Chưa đọc docs gốc của Atomic Red Team, Caldera hay BAS (AttackIQ, SafeBreach); phần purple team chủ yếu dựa trên nguồn cộng đồng.
- Chưa tìm thấy cơ chế "hạn dùng exclusion" có sẵn trong sản phẩm SIEM lớn kèm nguồn bậc 1. NVISO dùng Tags/ticket nhưng không có trường expiry.

## 3. Công cụ, khung và metric chất lượng detection

### Kết luận ngắn
Các bộ công cụ mở chính là SigmaHQ (sigma-cli/pySigma + regression_data + goodlog), Elastic detection-rules (unit test, schema, RTA), Splunk security_content + contentctl + attack_data, Azure-Sentinel (KQL validation khi PR), Panther PAT/pantherlog, Stratus Red Team và Atomic Red Team. Về metric, chưa có chuẩn chung cho "detection validation rate"; coverage ATT&CK là metric phổ biến nhất nhưng bị coi là "độ trung thực thấp". Mức chắc chắn: **cao** cho công cụ, **trung bình–thấp** cho metric.

### Phát hiện có nguồn
- Bảng tóm tắt công cụ (nguồn đã dẫn ở mục 2):
  - SigmaHQ: `sigma check`, regression test (EVTX/JSON, `match_count`), goodlog test trên baseline Win7/10/11 cùng `known-FPs.csv`.
  - Elastic detection-rules: `make test`, `validate-rule`/`validate-all`, parse KQL/EQL theo schema ECS, kiểm tra ATT&CK, `version.lock.json`, RTA.
  - Splunk: security_content, contentctl (build/test/replay), attack_data (Git LFS, hơn 9 GB), Attack Range.
  - Sentinel: Repositories chỉ kiểm tra JSON; kho community có KQL validation; các team tự xây test (Northwave, ADX emulator).
  - Panther: unit test trong YAML, PAT, pantherlog.
  - Stratus Red Team cho cloud; Atomic Red Team cho endpoint.
- CTID Summiting the Pyramid chấm điểm độ bền của analytic theo các mức của Pyramid of Pain. Bản cập nhật 2024-12-16 bổ sung network. Roadmap CTID 2026 vẫn giữ STP là một trong 6 hướng, tập trung vào "detection robustness". — [CTID: Summiting the Pyramid](https://ctid.mitre.org/projects/summiting-the-pyramid), [CTID roadmap](https://ctid.mitre.org/roadmap/) (bậc 1)
- Metric "độ trung thực cao": validation, detection drift, volatility. — [Packt: Practical Threat Detection Engineering ch.15](https://subscription-non-live.prod.packtpub.com/book/security/9781801076715/15/ch15lvl1sec76/summary) (bậc 2, 2023)
- Metric vận hành từ NVISO: trigger rate, số entity, health failure rate, tampering. — [NVISO Part 7](https://blog.nviso.eu/2025/10/07/detection-engineering-practicing-detection-as-code-monitoring-part-7/) (bậc 2)
- Một số nguồn cảnh báo điểm maturity cao không cho biết SOC phát hiện được technique nào, nên cần đi kèm coverage technique đã được kiểm chứng. — [Anvilogic: Detection Coverage Maturity](https://anvilogic.com/detection-coverage-maturity) và các bài tổng hợp (bậc 3, theo snippet)

### Nhận định
- Với task tuning, metric hữu ích nhất là các số đo theo từng thay đổi: (i) số alert giảm được và tỉ lệ FP giảm; (ii) số TP lịch sử, mẫu attack và test regression còn match (mục tiêu 100%); (iii) mức thu hẹp coverage ATT&CK (mục tiêu 0); (iv) fire-rate sau deploy so với baseline. Metric toàn cục kiểu "coverage %" ít giá trị để đánh giá một đề xuất cụ thể.

### Khoảng trống
- Không tìm thấy định nghĩa chuẩn cho "detection validation rate" hay "detection efficacy".
- Chưa kiểm tra chi tiết các nền tảng thương mại về detection validation (CardinalOps, AttackIQ, SafeBreach, Anvilogic) ngoài mức tuyên bố marketing.

## 4. Sự cố và bài học khi tuning hay giám sát làm mất phát hiện

### Kết luận ngắn
Có bằng chứng công khai rằng exclusion bị khai thác: APT38, Turla và ransomware "The Gentlemen" theo MITRE; Conti chạy được từ thư mục được exclude theo thử nghiệm của BleepingComputer 2022. Cũng có trường hợp điểm mù giám sát kéo dài vì một thành phần hỏng mà không ai biết (Equifax). Chưa tìm thấy postmortem công khai trong khoảng 2018–2026 mô tả đích danh "rule bị tắt vì quá ồn, rồi bỏ lỡ tấn công". Mức chắc chắn: **cao** cho nhóm exclusion bị lợi dụng, **trung bình** cho Equifax (số liệu giữa các nguồn lệch nhau), **thấp** cho nhóm rule bị tắt vì ồn.

### Phát hiện có nguồn
- Exclusion bị khai thác: APT38 (exclude `C:\Windows\System32`), Turla (LunarWeb trong thư mục bị loại khỏi quét), The Gentlemen (tự thêm vào exclusion list của EDR). — [MITRE T1564.012](https://attack.mitre.org/techniques/T1564/012/) (bậc 1, 2026-05)
- Exclusion list đọc được và bị lợi dụng: Conti chạy từ thư mục được exclude, mã hóa máy mà không có cảnh báo; vấn đề có thể đã tồn tại khoảng 8 năm. — [BleepingComputer 2022-01-13](https://www.bleepingcomputer.com/news/security/microsoft-defender-weakness-lets-hackers-bypass-malware-detection/amp/) (bậc 2)
- Equifax (vụ xâm nhập 2017, báo cáo năm 2018): thiết bị giám sát traffic của hệ thống ACIS ngừng hoạt động vì chứng chỉ hết hạn. Báo cáo House Oversight nói thiết bị đó đã "inactive for 19 months", còn bài báo dẫn GAO nói khoảng 10 tháng. Cuộc tấn công kéo dài 76 ngày. Khi chứng chỉ được gia hạn ngày 29/7/2017, traffic đáng ngờ lộ ra ngay. — [House Oversight: Equifax Report (2018-12)](https://oversight.house.gov/wp-content/uploads/2018/12/Equifax-Report.pdf) (bậc 1, theo snippet), [TechTarget về báo cáo GAO](https://www.techtarget.com/cybersecurity/news/252454340/Equifax-breach-report-highlights-multiple-security-failures) (bậc 2); hai nguồn lệch nhau 10 tháng và 19 tháng
- SolarWinds: hướng dẫn cũ khuyên exclude toàn bộ thư mục cài đặt Orion khỏi antivirus. Sau SUNBURST, cộng đồng (Thwack, ISC2) đặt câu hỏi liệu allowlist này có che hoạt động độc hại không. Hướng dẫn hiện tại nói exclusion là tùy chọn và nên đánh giá file trước khi exclude. Không có tuyên bố chính thức nào nối exclusion với việc SUNBURST không bị phát hiện. — [SolarWinds Success Center](https://support.solarwinds.com/SuccessCenter/s/article/Files-and-directories-to-exclude-from-antivirus-scanning-for-Orion-Platform-products) (bậc 1), [ISC2 community](https://community.isc2.org/t5/Threats/Solarwinds-supply-chain-attack-still-a-good-idea-to-whitelist/m-p/41766) (bậc 3)

### Nhận định
- Equifax không phải lỗi tuning rule. Nó là ví dụ điển hình cho "silent failure": control giám sát hỏng mà không ai biết. PCI DSS 10.7.2 về sau yêu cầu đúng điều này, tức là phát hiện khi control an ninh trọng yếu bị lỗi. Vì vậy giám sát health và fire-rate sau tuning nên coi là bắt buộc.

### Khoảng trống
- Chưa tìm thấy postmortem công khai (2018–2026) về việc rule SIEM bị tắt hoặc suppress vì ồn rồi bỏ lỡ tấn công. Ví dụ nổi tiếng nhất là Target 2013 (alert FireEye bị bỏ qua), nhưng nó nằm ngoài khoảng thời gian và chưa được kiểm chứng trong lần này. Các truy vấn đã thử không nhắm trực tiếp vào chủ đề này; nên tìm thêm "alert fatigue breach postmortem", "suppressed alert missed intrusion".

## Truy vấn đã chạy
- Elastic detection-rules unit tests rule validation repository (standard)
- Splunk security_content attack_data detection testing CI (standard)
- detection rule exclusion abused attacker allowlisted path bypass EDR (standard)
- PCI DSS 4.0 requirement 10.4.1.1 automated audit log review (standard)
- Splunk contentctl test attack_data replay detection testing (standard)
- Panther detection unit tests pantherlog test rules CI (standard)
- sigma-cli check rules regression test SigmaHQ evtx test pipeline (standard)
- Microsoft Sentinel repositories CI/CD analytics rules validation KQL test (standard)
- detection engineering backtest new rule historical data compare alert volume before deploy (extended)
- silent detection rule monitoring "rule health" detection engineering stopped firing (standard)
- Center for Threat-Informed Defense Summiting the Pyramid robust detection analytics (standard)
- NVISO "Practicing Detection-as-Code" Tuning Part 8 (standard)
- Atomic Red Team detection validation coverage purple team test detections continuously (standard)
- Microsoft Defender exclusions readable attackers enumerate exclusion list 2022 (standard)
- SolarWinds Orion recommended antivirus exclusions folders SUNBURST lesson (standard)
- ISO 27001:2022 Annex A 8.16 monitoring activities false positives tuning guidance ISO 27002 (standard)
- SOC 2 CC7.2 CC8.1 change management detection rules SIEM evidence (standard)
- "10.4.1.1" "automated mechanisms are used to perform audit log reviews" "10.7.2" (standard)
- Equifax breach expired certificate traffic inspection 19 months GAO report (standard)
- detection engineering metrics detection coverage validation rate ATT&CK "detection efficacy" maturity (standard)
- Sigma rule regression data "regression_data" SigmaHQ tests evtx match_count (standard)
- Đọc trực tiếp qua GitHub API/raw: SigmaHQ `regression_data/README.md`, `.github/workflows/sigma-test.yml`, `goodlog-tests.yml`, `known-FPs.csv`, thư mục `tests/`
