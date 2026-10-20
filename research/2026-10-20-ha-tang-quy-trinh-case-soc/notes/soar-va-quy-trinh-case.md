# SOAR, vòng đời case và quy trình SOC/MDR (câu hỏi phụ 3 + xu hướng AI SOC)

> **Lưu ý phương pháp (quan trọng cho writer/verifier):** trong phiên này `WebFetch` và `curl` tới hầu hết các domain (learn.microsoft.com, docs.cloud.google.com, arxiv.org, usenix.org, expel.com, redcanary.com, elastic.co, docs.expel.io...) bị proxy chặn (CONNECT 403, kiểm tra lúc 2026-10-20). Mọi phát hiện dưới đây lấy từ đoạn trích mà công cụ `WebSearch` trả về kèm URL nguồn, **chưa mở trang gốc để đọc đoạn văn đầy đủ**. Vì vậy mức chắc chắn được hạ một bậc so với bình thường; verifier nên mở lại các URL bậc 1 trước khi dùng con số trong report.

## 1. Playbook/automation chạy ở điểm nào trong vòng đời case

### Kết luận ngắn
Các nền tảng lớn đều có ba nhóm điểm kích hoạt: (a) lúc alert/case được tạo hoặc nạp vào (ingestion), (b) khi case/incident được cập nhật (đổi status, owner, severity, thêm alert, thêm comment/tag), (c) chạy thủ công/ad-hoc từ case, cộng thêm (d) chạy theo lịch ở một số sản phẩm. Ngoài ra có tầng "tiền xử lý" chạy *trước khi* case tồn tại (drop/dedup/link). Mức chắc chắn: **trung bình–cao** (docs vendor, nhưng chỉ đọc qua đoạn trích).

### Phát hiện có nguồn
- **Microsoft Sentinel** có 3 loại trigger cho automation rule: *When incident is created* (incident từ analytics rule, tạo thủ công, ingest từ Defender XDR; hoặc incident tạo trong Defender portal nếu đã onboard), *When incident is updated* (đổi status, owner, severity, thêm alert, thêm comment/tag/tactic; có toán tử Changed / Changed from / Changed to), và *When alert is created* (chỉ với alert từ Scheduled/NRT analytics rule, điều kiện chỉ lọc được theo tên analytic rule; trong Defender portal chỉ áp cho alert Sentinel) — [Create and use Microsoft Sentinel automation rules](https://learn.microsoft.com/en-in/azUre/sentinel/create-manage-use-automation-rules) (bậc 1, không rõ ngày cập nhật, đọc qua đoạn trích 2026-10)
- Microsoft khuyến nghị dùng trigger theo incident cho hầu hết trường hợp vì incident là "case file" có thể sửa, giữ status hiện tại và làm giàu bằng comment/tag/bookmark; automation rule có thể gọi playbook (Logic Apps) cho tác vụ phức tạp — cùng nguồn trên (bậc 1)
- **Google SecOps SOAR**: trigger của playbook đặt khi tạo playbook, áp ở mức alert khi ingest: All, Alert Type (khớp field Rule Generator), Product Name, Tag Name, Alert Trigger Value, Custom Trigger, Custom List, Network Name — [Use triggers in playbooks](https://docs.cloud.google.com/chronicle/docs/soar/respond/working-with-playbooks/using-triggers-in-playbooks) (bậc 1, không rõ ngày)
- Google SecOps: mỗi alert gắn tối đa 10 playbook, **chỉ 1 playbook gắn tự động qua ingestion trigger**, 9 playbook còn lại gắn thủ công; khách có tính năng Reaction Triggers / Cases playbook được tới 30; priority 1–3 (mặc định 2); mỗi playbook chạy lại tối đa 10 lần mỗi case/alert (30 nếu có tính năng trên). Gắn thủ công qua tab Playbooks của alert trong case — [Attach playbooks to alerts or cases](https://docs.cloud.google.com/chronicle/docs/soar/respond/working-with-playbooks/attach-playbooks-to-alerts-cases) (bậc 1, không rõ ngày)
- **Splunk SOAR**: playbook chạy theo *label* của container ("Operates on"); mọi event có label (vd Events, Email). Để định tuyến theo use case, cộng đồng gợi ý mỗi use case một automation account gắn label riêng, hoặc một playbook "landing" làm enrichment chung rồi đổi label/gọi playbook con (đây là câu trả lời cộng đồng, không phải docs chính thức) — [View or edit playbook settings in Splunk SOAR](https://help.splunk.com/en/splunk-soar/soar-cloud/build-playbooks/manage-playbooks-and-playbook-settings/view-or-edit-playbook-settings-in-splunk-soar) (bậc 1); [Splunk Community: playbook trigger based on labels](https://community.splunk.com/t5/Splunk-SOAR/How-to-create-Playbook-trigger-based-on-different-labels/m-p/596479) (bậc 3, 2022)
- Splunk SOAR chạy theo lịch: template của Recorded Future dùng Timer app để tạo container và gắn label định kỳ, từ đó kích playbook hunting theo lịch — [Recorded Future playbook template](https://support.recordedfuture.com/hc/article_attachments/19636461585683) (bậc 2, không rõ ngày)
- **Cortex XSOAR pre-process rules** chạy *sau* ingestion/classification/mapping nhưng *trước* khi tạo incident; hành động: Drop (không tạo incident), Link and close (ghi vào bảng Linked Incidents của incident có sẵn rồi đóng incident mới — đây là cách dedup), Drop and update (ghi vào bảng Dropped Duplicate Incidents + War Room entry của incident có sẵn); rule chạy từ trên xuống, mỗi incident chỉ áp một rule — [Pre-process rules (XSOAR 8 SaaS)](https://cortex-docs.paloaltonetworks.com/cortex-xsoar-8-saas/configure-cortex-xsoar/incident-configuration/pre-process-rules) (bậc 1); [Rule actions for pre-process rules (6.13)](https://cortex-docs.paloaltonetworks.com/xsoar-6-administrator-guide/6.13/learn-about-cortex-xsoar/customize-and-configure-cortex-xsoar/incidents/pre-process-rules/rule-actions-for-pre-process-rules) (bậc 1)

### Nhận định
- **Nhận định:** có hai "tầng" tự động hóa cần phân biệt khi lấy dữ liệu cho tuning: tầng *trước case* (pre-process / suppression / dedup — không tạo case, hoặc tạo rồi đóng ngay và link) và tầng *trong case* (playbook/automation rule chạy khi tạo/cập nhật). Alert bị drop ở tầng trước có thể không bao giờ có nhãn.
- **Nhận định:** Sentinel chỉ cho lọc automation rule mức alert theo tên analytic rule → các auto-close theo điều kiện entity/thời gian thường viết ở mức incident, nên nhãn auto-close nằm ở incident chứ không ở alert.

### Khoảng trống
- Chưa xác nhận trực tiếp docs Splunk SOAR/ES 8 về trigger "container created/updated" chính thức; chưa có docs trigger theo lịch của Sentinel (thường làm bằng Logic Apps recurrence — chưa có nguồn).
- Chưa đọc docs XSOAR về playbook mặc định chạy khi tạo incident theo incident type (truy vấn đã thử không trả kết quả).

## 2. Những việc thường được tự động hóa

### Kết luận ngắn
Các việc phổ biến: enrichment (TI, entity, user risk), phân loại/gán severity, gán owner, dedup/link, đóng tự động hoạt động đã biết là benign với nhãn đóng kèm theo, containment có điều kiện (isolate host theo verdict), thông báo/escalation, đồng bộ ticket hai chiều. Mức chắc chắn: **trung bình** (nhiều nguồn docs + blog, không có khảo sát định lượng về tần suất từng loại).

### Phát hiện có nguồn
- Sentinel: tạo "exception" bằng automation rule **đóng ngay incident vừa tạo, ghi lý do đóng và comment** (thủ tục này chỉ hỗ trợ ở Azure portal; với Defender portal phải tạo rule từ đầu) — [Handle false positives in Microsoft Sentinel](https://docs.azure.cn/en-us/sentinel/false-positives) (bậc 1, không rõ ngày)
- Khi tạo automation rule từ một incident, Sentinel điền sẵn action Change Status → Closed với classification **"Benign Positive – Suspicious but expected"**, có thể xóa/đổi — [Tech Community forum: Defender–Sentinel sync](https://techcommunity.microsoft.com/discussions/microsoftsentinel/defender-sentinel-sync/3239352/replies/3581023) (bậc 3, không rõ ngày; cần đối chiếu docs)
- Blog bên thứ ba khuyên auto-close với classification "False Positive" hoặc "Benign Positive – Confirmed Benign Activity" kèm comment vì metric của Sentinel dựa vào classification — [OneUptime: Sentinel automation rules auto-assign and auto-close](https://oneuptime.com/blog/post/2026-02-16-how-to-create-microsoft-sentinel-automation-rules-to-auto-assign-and-auto-close-incidents/view) (bậc 3, 2026-02)
- Google SecOps: output AI (risk score, verdict như True Positive) dùng làm điều kiện rẽ nhánh playbook, vd tự isolate host nếu verdict Malicious, chỉ flag để review nếu Suspicious — [Respond to alerts and cases](https://docs.cloud.google.com/chronicle/docs/secops/respond-cases) (bậc 1, không rõ ngày)
- Một bài lab (tiếng Nhật) dựng playbook Google SecOps tự đóng case khi Triage agent ra verdict False Positive với High Confidence — [G-gen: Google SecOps AI agent alert automation](https://blog.g-gen.co.jp/entry/google-secops-ai-agent-alert-automation) (bậc 2–3, không rõ ngày)
- Expel: bot Josie triage event từ thiết bị của khách trước; chỉ tạo "Expel Alert" khi cần analyst xem; hoạt động đã biết benign bị auto-ignore → một alert vendor có thể không có Expel Alert tương ứng trong Workbench — [How Expel alerts work](https://docs.expel.io/workbench-reference/alerts/how-expel-alerts-work) (bậc 1, không rõ ngày)
- Expel Ruxie: agent rapid triage "never auto-closes or resolves an alert"; agent blocked-malware gửi khuyến nghị và mọi khuyến nghị cần analyst Expel duyệt trước khi đóng; nhưng brochure Ruxie lại viết Ruxie có thể "confidently auto-close benign alerts" (mâu thuẫn trong tài liệu chính vendor) — [New Ruxie AI power-up: blocked malware triage agent](https://expel.com/blog/new-ruxie-ai-power-up-blocked-malware-triage-agent-clears-the-noise/) (bậc 1 về tuyên bố của vendor, ~2025–2026); [Expel Ruxie AI Workbench brochure](https://expel.com/wp-content/uploads/2026/06/Expel-Ruxie-AI-Workbench-062226.pdf) (marketing, 2026-06)
- Arctic Wolf: báo cáo 2025 nói **71% alert được nạp bị suppress** như hoạt động expected/benign dựa trên context khách và TI; Aurora giảm 330 nghìn tỷ observation xuống ~8,6 triệu alert — [Arctic Wolf Security Operations Report 2025 (PDF)](https://cuebid.se/wp-content/uploads/2025/09/Arctic-Wolf-Security-Operations-Report-2025.pdf) (bậc 1 về số liệu nội bộ vendor, 2025)
- eSentire tuyên bố "99.97% false positive reduction" nhờ automated event suppression — [eSentire press release (pr.com)](https://www.pr.com/press-release/756826) (**marketing**, không rõ ngày)
- Red Canary: khách có thể "authorize" user/endpoint/sensor group để hoạt động tương tự không bị gắn vào threat nữa; analyst đánh dấu FP thì kích hoạt Detection Engineering review lỗi logic — [Red Canary docs: Resolve threats](https://docs.redcanary.com/docs/resolve-threats) (bậc 1, không rõ ngày)
- Đồng bộ ticket: tích hợp ServiceNow Security Incident Response ↔ Sentinel là hai chiều; khi SIR incident đóng thì status Sentinel incident được cập nhật và comment đóng được ghi ngược; có cấu hình "incident classification and closing reason" (classification mặc định dùng khi đóng ở Sentinel); trải nghiệm Azure portal của Sentinel bị deprecate kéo dài tới 03/2027, khuyến nghị chuyển sang tích hợp Defender portal — [ServiceNow docs: Automate incident updates and closures by SIR incident status](https://www.servicenow.com/docs/r/Hl2CblJbxzWNxnQLivjlGg/594rNOqIY0WOJfPelELzEQ) (bậc 1, không rõ ngày)
- App ServiceNow store của bên thứ ba đồng bộ Status, Severity, Owner, comment/work note, entity và alert hai chiều — [ServiceNow Store app](https://store.servicenow.com/store/app/8feeab2e1b646a50a85b16db234bcb2c) (bậc 2, không rõ ngày)

### Nhận định
- **Nhận định:** "auto-close" gần như luôn ghi kèm một classification *do người cấu hình rule chọn sẵn* (vd Benign Positive mặc định ở Sentinel). Nhãn này phản ánh *chính sách* chứ không phải phán đoán từng case → cần tách riêng khi huấn luyện/đánh giá tuning (đã gợi ý trong câu hỏi phụ 4).
- **Nhận định:** với MSSP/MDR, phần lớn "lọc" xảy ra trước khi có case (suppression/auto-ignore 71% ở Arctic Wolf, Josie ở Expel). Nếu pipeline tuning chỉ nhìn case thì bỏ sót phần này; ngược lại các suppression này chính là "tuning" đã làm.
- **Nhận định:** khi đồng bộ ServiceNow/Jira, nhãn đóng có thể bị ánh xạ về một classification mặc định → nhãn ở SIEM có thể là sản phẩm của mapping, không phải lựa chọn của analyst.

### Khoảng trống
- Không có khảo sát định lượng cho biết bao nhiêu % SOC tự động hóa từng loại tác vụ (enrichment vs containment...). SANS 2025 có dữ liệu nhưng không mở được PDF.
- Chưa có bảng ánh xạ close code ServiceNow ↔ classification Sentinel cụ thể; Jira chưa tìm.

## 3. Tỷ lệ case/alert được đóng tự động

### Kết luận ngắn
Không có con số độc lập, đã công bố phương pháp, về tỷ lệ case đóng tự động. Các con số hiện có là của vendor/MDR, đo những thứ khác nhau (suppress trước case, triage tự động, auto-close Tier-1) và dao động 10%–95%. Mức chắc chắn: **cao** về việc "không có số chuẩn"; **thấp** về giá trị cụ thể.

### Phát hiện có nguồn
- Arctic Wolf 2025: 71% alert bị suppress (expected/benign); Alpha AI (triage tự động) xử lý **10% alert**, bỏ được >860.000 lượt review thủ công; mean time to ticket giảm 37% trong hai năm — [Arctic Wolf Security Operations Report 2025](https://cuebid.se/wp-content/uploads/2025/09/Arctic-Wolf-Security-Operations-Report-2025.pdf) (bậc 1 về số liệu tự báo cáo, 2025); [SecurityBrief AU](https://securitybrief.com.au/story/cybersecurity-alerts-surge-after-hours-as-threats-evolve-says-report) (bậc 2, 2025). Hai con số đo hai thứ khác nhau, không cộng được.
- Arctic Wolf 2025: 51% alert ngoài giờ hành chính; tỉ lệ cuối tuần 15% (press release) vs 17% (SecurityBrief) — [Arctic Wolf press release](https://arcticwolf.com/resources/press-releases/arctic-wolf-2025-security-operations-report-reveals-threat-landscape-acceleration-majority-of-security-alerts-now-occur-outside-working-hours/) (bậc 1, 2025); mâu thuẫn với [SecurityBrief AU](https://securitybrief.com.au/story/cybersecurity-alerts-surge-after-hours-as-threats-evolve-says-report) (bậc 2, 2025)
- Red Canary Threat Detection Report 2026: 419 triệu investigative lead → 8,5 triệu event có thể độc hại → **110.000 threat được xác nhận** (~0,026% lead thành threat); >97% threat được phát hiện bởi máy nhưng người vẫn xác nhận threat trước khi báo khách — [Red Canary TDR methodology](https://redcanary.com/threat-detection-report/methodology/) (bậc 1 về số liệu tự báo cáo, 2026)
- Red Canary tuyên bố "99.6% customer-validated true positive rate" cho AI agent (press release 2025-06) — [Red Canary expands AI innovations](https://redcanary.com/news/red-canary-expands-ai-innovations/) (**marketing**, 2025-06)
- Expel: Annual Threat Report 2026 phân tích >1.000.000 alert trong SOC năm 2025; 75,6% detection năm 2025 là Expel-written/enhanced; trang Workbench tuyên bố "99.9% reduction in investigative leads"; MTTR (remediate) 14 phút cho incident high/critical tự động hoàn toàn — [Expel 2026 Annual Threat Report blog](https://expel.com/blog/expels-2026-annual-threat-report-is-live/) (bậc 1, 2026); [Expel Workbench](https://expel.com/workbench-operations-platform/) (**marketing**); [Expel: automation metrics](https://expel.com/cyberspeak/what-are-some-cybersecurity-metrics-examples-for-measuring-automation-impact/) (bậc 2, không rõ ngày). Không tìm được % alert auto-close của Expel.
- Torq: trang HyperSOC tuyên bố tự remediate **95% case Tier-1**, cùng trang lại có tiêu đề "Close 90% of Tier-1 Tickets", case study ghi 82% case được tự động — [Torq HyperSOC](https://torq.io/hypersoc) (**marketing**, không rõ ngày); [BusinessWire 2025-04](https://www.businesswire.com/news/home/20250416564362/en) (marketing, 2025-04)
- Microsoft phishing triage agent: Microsoft nói ~90% email người dùng báo cáo là FP và agent được thiết kế để tag và tự dismiss chúng — [Redmond Mag 2025-08](https://redmondmag.com/articles/2025/08/06/microsoft-rolls-out-phishing-triage-agent-in-security-copilot-public-preview.aspx) (bậc 2, 2025-08; con số gốc từ Microsoft, **marketing**)
- Microsoft SOC nội bộ: incident không giải quyết được bằng automation thì escalate theo tầng; ~96% được Tier 1–2 xử lý, ~4% escalate — [Microsoft: How we manage incidents at Microsoft](https://www.microsoft.com/en-au/business/experiences/how-we-manage-incidents-at-microsoft) (bậc 1 về chính tổ chức, 2023-07)

### Nhận định
- **Nhận định:** con số "% tự động đóng" phụ thuộc mẫu số (raw event, alert, lead, case Tier-1). So sánh giữa vendor là vô nghĩa nếu không rõ mẫu số; report nên trình bày như dải tuyên bố, không phải benchmark.
- **Nhận định:** với dữ liệu tuning, tỷ lệ TP thật ở mức lead/alert rất thấp (Red Canary ~0,03% lead → threat), nên nhãn FP/benign chiếm áp đảo; phần lớn nhãn đó do tự động/suppression gán chứ không do người.

### Khoảng trống
- Không lấy được số từ SANS SOC Survey 2024/2025 về tỷ lệ đóng tự động (PDF bị chặn). Truy vấn: "SANS SOC survey 2025 automation metrics", "SANS 2024 SOC survey metrics MTTD MTTR".
- Không có nguồn độc lập (học thuật) đo tỷ lệ auto-close thực tế.

## 4. Vòng đời case, SLA và metric (MTTA/MTTD/MTTR, dwell time)

### Kết luận ngắn
Vòng đời case thường: tạo (New) → đang xử lý (Active/In progress, có owner) → đóng kèm *lý do đóng* + *root cause/classification* + comment. Metric thời gian phổ biến là MTTD/MTTA/MTTR nhưng phần lớn SOC vẫn đo thủ công. Dwell time toàn cầu (Mandiant) 11 ngày (M-Trends 2025) → 14 ngày (M-Trends 2026). Mức chắc chắn: **trung bình**.

### Phát hiện có nguồn
- Google SecOps: đóng case phải chọn **Reason** rồi mới chọn **Root Cause**, kèm comment; admin có thể thêm root cause/tham số tùy chỉnh. API `caseCloseDefinitions` liệt kê reason: MALICIOUS, NOT_MALICIOUS, MAINTENANCE, INCONCLUSIVE (+ UNSPECIFIED); trang enum SOAR cũ (cập nhật 2025-07) chỉ có unspecified/not malicious/malicious/maintenance, không có inconclusive — [Resolve and close cases](https://docs.cloud.google.com/chronicle/docs/soar/investigate/working-with-cases/how-to-close-cases) (bậc 1); [REST caseCloseDefinitions](https://docs.cloud.google.com/chronicle/docs/reference/rest/v1/projects.locations.instances.caseCloseDefinitions) (bậc 1); mâu thuẫn với [Shared.Types/Reason](https://docs.cloud.google.cn/chronicle/docs/reference/rest/Shared.Types/Reason) (bậc 1, 2025-07)
- Defender Experts for XDR (dịch vụ MDR của Microsoft): incident được phân loại False Positive hoặc Informational, Expected Activity thì Status được đặt Resolved — [Managed detection and response (Defender XDR)](https://learn.microsoft.com/en-ca/defender-xdr/managed-detection-and-response-xdr) (bậc 1, không rõ ngày)
- Defender XDR AIR (automated investigation): evidence có verdict Malicious / Suspicious / Unknown / No threats found; Defender for Office 365 có trạng thái investigation "No Threats Found" — [Details and results of an automated investigation](https://learn.microsoft.com/el-gr/defender-xdr/m365d-autoir-results) (bậc 1); [AIR view investigation results (MDO)](https://learn.microsoft.com/en-us/defender-office-365/air-view-investigation-results) (bậc 1). Không tìm thấy docs ánh xạ "No threats found" sang Classification của incident.
- Sentinel ↔ Defender for Cloud Apps: một case đóng "Benign Positive" ở Sentinel hiện thành "True Positive" ở MDA vì các portal dùng bộ resolution khác nhau — [Tech Community forum](https://techcommunity.microsoft.com/discussions/microsoftsentinel/defender-sentinel-sync/3239352/replies/3581023) (bậc 3, không rõ ngày)
- SANS 2025 SOC Survey (theo bản Elastic host và tóm tắt vendor): **69% SOC vẫn báo cáo metric thủ công hoặc phần lớn thủ công**; ~42% dùng AI/ML "out of the box" không tùy biến (một tóm tắt khác ghi 40%); 24/7 được ghi 82% hoặc 79% tùy nguồn — [SANS 2025 SOC Survey PDF (Elastic)](https://www.elastic.co/pdf/sans-soc-survey-2025.pdf) (bậc 1, 2025; chỉ đọc qua đoạn trích); [Swimlane summary](https://swimlane.com/blog/global-soc-survey-insights/) (bậc 2, vendor, 2025)
- SANS 2023 (qua Trend Micro): trong nhóm đo giá trị SOC bằng MTTD/MTTR, 84% báo giảm chi phí xử lý sự cố xuống ≤50% — [Trend Micro JP expert view 2024-04](https://trendmicro.com/ja_jp/jp-security/24/d/expertview-20240430-01.html) (bậc 2, 2024-04; chưa đối chiếu bản gốc)
- Expel đo latency alert ở **p95** thay vì median để không che đuôi chậm — [Expel blog: Performance SOC metrics part 1](https://expel.com/blog/performance-metrics-measuring-soc-efficiency/) (bậc 1 về thực hành của tổ chức, không rõ ngày)
- Microsoft SOC: tầng triage có ~15 phút để phản hồi, rồi chuyển sang tầng investigation — [Microsoft: How we manage incidents](https://www.microsoft.com/en-au/business/experiences/how-we-manage-incidents-at-microsoft) (bậc 1, 2023-07)
- Dwell time: M-Trends 2025 — median toàn cầu 11 ngày (tăng từ 10); 26 ngày khi bên ngoài báo, 5 ngày khi kẻ tấn công báo (ransomware), 10 ngày khi tự phát hiện. M-Trends 2026 — tăng lên 14 ngày — [M-Trends 2025](https://cloud.google.com/blog/topics/threat-intelligence/m-trends-2025/) (bậc 1, 2025-04); [M-Trends 2026](https://cloud.google.com/blog/topics/threat-intelligence/m-trends-2026) (bậc 1, 2026)

### Nhận định
- **Nhận định:** "close reason" của Google (Malicious/Not malicious/Maintenance/Inconclusive) và classification của Sentinel (TP/BP/FP/Undetermined) không ánh xạ 1-1 vào nhị phân TP/FP; "Maintenance" và "Benign Positive" là lớp riêng mà tuning nên xử lý khác FP thuần.
- **Nhận định:** vì 69% SOC đo metric thủ công, timestamp MTTA/MTTR trong case có thể không đáng tin để dùng làm tín hiệu phụ.

### Khoảng trống
- Không có bảng SLA chuẩn ngành theo severity (các con số kiểu "Tier 1 escalation 15–25%" chỉ thấy ở blog vendor không nguồn — không dùng).
- Chưa lấy được docs trạng thái incident của Sentinel (New/Active/Closed) do không mở được Learn; report cũ có thể đã có.

## 5. Tiering L1→L2→L3 và escalation

### Kết luận ngắn
Mô hình 3 tầng (L1 triage, L2 điều tra/xác thực, L3 hunting/forensics/IR) vẫn là mặc định; dữ liệu của Microsoft cho thấy ~96% incident xử lý ở L1–L2. Phê phán (handoff mất context, hàng đợi tuần tự) và xu hướng "làm phẳng" tầng nhờ AI chủ yếu đến từ vendor. Mức chắc chắn: **trung bình**.

### Phát hiện có nguồn
- Phân tầng theo độ phức tạp/kinh nghiệm; lý do chính là chi phí — phần lớn alert là FP/thấp nên dùng người junior lọc trước; SOC nhỏ hay gộp L1 và L2 — [Intezer: SOC tiers explained](https://intezer.com/guides/ai-soc/soc-tiers-explained) (bậc 2, vendor, không rõ ngày)
- Phê phán: tiêu chí escalate chủ quan, context mất khi handoff, backlog L1 làm chậm threat thật — [Prophet Security: SOC tiers are out](https://prophetsecurity.ai/blog/soc-tiers-are-out-how-ai-is-flattening-soc-tier-1-2-3) (bậc 2, vendor có lợi ích); [Fluency: Rethinking the SOC three-tier model](https://blogs.fluencysecurity.com/rethinking-the-soc-three-tier-model/) (bậc 2–3)
- Microsoft SOC: L1 triage là tập con tinh gọn của quy trình L2; ~4% incident escalate khỏi L1–L2 — [Lessons learned from the Microsoft SOC, part 1](https://www.microsoft.com/security/blog/2019/02/21/lessons-learned-from-the-microsoft-soc-part-1-organization/) (bậc 1, 2019-02); [How we manage incidents at Microsoft](https://www.microsoft.com/en-au/business/experiences/how-we-manage-incidents-at-microsoft) (bậc 1, 2023-07)
- Học thuật: Kokulu et al. (CCS 2019) — 18 phỏng vấn bán cấu trúc với analyst và manager SOC; phát hiện bất đồng nội tại giữa manager và analyst (về metric, công cụ, tự động hóa) có thể đe dọa hiệu quả SOC — [Matched and Mismatched SOCs](https://adamdoupe.com/publications/matched-and-mismatched-socs-ccs2019.md) (bậc 1, 2019)
- Alahmadi, Axon, Martinovic (USENIX Security 2022): khảo sát 20 + phỏng vấn 21 practitioner; phần lớn "false positive" theo cảm nhận thực ra là **benign trigger** (alarm đúng do hoạt động hợp lệ); validate alarm tẻ nhạt dẫn đến burnout; đề xuất alarm cần Reliable, Explainable, Analytical, Contextual, Transferable — [99% False Positives](https://www.usenix.org/conference/usenixsecurity22/presentation/alahmadi) (bậc 1, 2022-08)
- Tines Voice of the SOC 2023 (900 người): 63% burnout, 9/10 đội có tự động hóa một phần, 93% tin tự động hóa thêm sẽ cải thiện work-life balance, 55% có khả năng nghỉ việc năm tới — [Dark Reading về Tines report](https://www.darkreading.com/cybersecurity-operations/tines-report-finds-more-than-half-of-security-professionals-likely-to-switch-jobs-next-year) (bậc 2, 2023; khảo sát do vendor tài trợ)

### Nhận định
- **Nhận định:** nhãn đóng do L1 (nhiều và nhanh) và nhãn do L2/L3 (ít, kỹ) có chất lượng khác nhau; nếu dữ liệu case lưu người đóng/tầng, nên dùng làm trọng số. Phát hiện "benign trigger" của Alahmadi củng cố việc tách BP khỏi FP.

### Khoảng trống
- Không có nghiên cứu thực nghiệm so sánh SOC có tầng và không tầng.

## 6. Quy trình MSSP/MDR với khách hàng (ai đóng, ai gắn nhãn, feedback)

### Kết luận ngắn
Mẫu chung: MDR lọc/triage phía mình (đa số tự động), chỉ đẩy "incident/threat" đã được người xác nhận cho khách; khách phản hồi bằng cách xác nhận hoạt động là hợp lệ/authorize, và phản hồi đó được biến thành suppression/exclusion hoặc chuyển cho đội detection engineering. Nhãn vì thế có hai nguồn (MDR analyst và khách) không phải lúc nào cũng khớp. Mức chắc chắn: **trung bình–thấp** (ít docs công khai về workflow chi tiết).

### Phát hiện có nguồn
- Red Canary: khách đánh dấu FP → Detection Engineering review lỗi logic; khách authorize user/endpoint/sensor group → hoạt động tương tự không bị gắn vào threat nữa; con người xác nhận mọi threat trước khi báo khách — [Red Canary docs: Resolve threats](https://docs.redcanary.com/docs/resolve-threats) (bậc 1); [Red Canary TDR methodology](https://redcanary.com/threat-detection-report/methodology/) (bậc 1, 2026)
- Expel: Josie lọc event; chỉ alert cần người mới vào Workbench; Ruxie khuyến nghị, analyst Expel duyệt trước khi đóng — [How Expel alerts work](https://docs.expel.io/workbench-reference/alerts/how-expel-alerts-work) (bậc 1); [Expel blog Ruxie blocked malware agent](https://expel.com/blog/new-ruxie-ai-power-up-blocked-malware-triage-agent-clears-the-noise/) (bậc 1 về tuyên bố)
- Arctic Wolf: suppress dựa trên "customer context" (71% alert) và metric "mean time to ticket" — ticket là đơn vị giao cho khách — [Arctic Wolf SOR 2025](https://cuebid.se/wp-content/uploads/2025/09/Arctic-Wolf-Security-Operations-Report-2025.pdf) (bậc 1, 2025)
- Case study At-Bay MDR: analyst isolate server vì alert credential dumping, gọi điện khách, khách xác nhận là dev được giao chuyển credential → restore, đóng FP trong ~15 phút — [At-Bay case study](https://www.at-bay.com/case-studies/mdr-quickly-resolved-false-positive-credential-alert/) (bậc 2, marketing)
- Defender Experts for XDR: Microsoft đặt classification (FP / Informational, Expected Activity) và chuyển Status Resolved trên incident của khách — [Managed detection and response (Defender XDR)](https://learn.microsoft.com/en-ca/defender-xdr/managed-detection-and-response-xdr) (bậc 1)
- D3 Smart SOAR mô tả đồng bộ hai chiều classification với Sentinel cho MSSP qua trigger workflow — [D3: bi-directional sync with Sentinel for MSSPs](https://d3security.com/blog/bi-directional-sync-microsoft-sentinel-smart-soar-for-mssps/) (bậc 2, vendor)

### Nhận định
- **Nhận định:** ở MSSP/MDR, "verdict" khách nhìn thấy thường là của nhà cung cấp; còn phản hồi của khách ("hợp lệ, đã authorize") là tín hiệu BP mạnh nhất cho tuning theo khách (per-tenant exclusion), nhưng thường nằm trong comment/ticket tự do chứ không trong field cấu trúc.
- **Nhận định:** có hai vòng tuning khác nhau: per-customer (allowlist/suppression) và global (sửa logic detection) — Red Canary tách rõ hai luồng này; pipeline LLM tuning nên phân loại đầu ra theo hai luồng.

### Khoảng trống
- Không tìm được docs công khai của eSentire/Huntress/Arctic Wolf mô tả ai đóng case và field lưu phản hồi khách. Truy vấn đã thử: "MDR provider customer feedback loop false positive close investigation...".

## 7. AI SOC / agentic triage: ai đặt verdict, verdict nào được ghi

### Kết luận ngắn
Các agent triage (Google TIN, Microsoft phishing triage agent, Dropzone, Prophet, Elastic nội bộ, Expel Ruxie, Red Canary) đều ghi một **verdict riêng của AI** (thường kèm confidence và giải thích) tách khỏi trạng thái review của người; phần lớn để người duyệt/override, một số cho phép playbook tự đóng hoặc tự containment dựa trên verdict đó. Từ vựng verdict không thống nhất (TP/FP, Malicious/Suspicious/Benign/Inconclusive, "Recommended Benign"...). Mức chắc chắn: **trung bình** (docs vendor + một RCT preprint).

### Phát hiện có nguồn
- **Google SecOps Triage and Investigation Agent (TIN)**: xác định alert là true hay false positive; panel tóm tắt ghi **disposition**, **confidence level** và **explanation** — [Use Triage and Investigation Agent](https://docs.cloud.google.com/chronicle/docs/secops/triage-agent) (bậc 1, không rõ ngày). Verdict có thể làm điều kiện playbook (Malicious → isolate, Suspicious → review) — [Respond to alerts and cases](https://docs.cloud.google.com/chronicle/docs/secops/respond-cases) (bậc 1). Google tuyên bố agent đã điều tra >5 triệu alert, giảm 30 phút thủ công xuống 60 giây — [TechInformed](https://techinformed.com/googles-soc-agent-cuts-alert-review-from-30-minutes-to-60-seconds/) (bậc 2, ~2026-06, số **marketing** của Google)
- Google 3P Context Agent làm giàu entity, có thể bổ sung verdict và confidence tổng thể; tool run hiện trên timeline điều tra và Case Wall — [Investigate alerts with the 3P Context Agent](https://docs.cloud.google.com/chronicle/docs/investigation/context-agent-investigation) (bậc 1)
- **Microsoft Security Copilot Phishing Triage Agent** (Defender): phân loại mỗi email người dùng báo cáo là threat thật hay false positive, kèm giải thích ngôn ngữ tự nhiên; analyst có thể override và gửi feedback bằng ngôn ngữ tự nhiên; mặc định "hơi bi quan" — [Phishing triage agent (Microsoft Learn)](https://learn.microsoft.com/en-us/defender-xdr/phishing-triage-agent) (bậc 1); [Redmond Mag 2025-08](https://redmondmag.com/articles/2025/08/06/microsoft-rolls-out-phishing-triage-agent-in-security-copilot-public-preview.aspx) (bậc 2). Demo: agent gắn nhầm email HR toàn công ty là phishing; feedback sửa chỉ áp cho agent của người đó — cùng nguồn Redmond Mag / [The Register 2025-03](https://www.theregister.com/2025/03/24/microsoft_security_copilot_agents/) (bậc 2)
- RCT (preprint arXiv 2511.13860, 2025-11): analyst có agent hỗ trợ đạt tới **6,5× số TP mỗi phút analyst** và **độ chính xác verdict tăng 77%** so với nhóm đối chứng; analyst không có xu hướng "đóng dấu" verdict malicious của agent — [Randomized Controlled Trials for Phishing Triage Agent](https://arxiv.org/html/2511.13860v1) (bậc 1 preprint, 2025-11; tác giả liên quan Microsoft — chưa xác nhận do không mở được)
- **Dropzone**: mỗi investigation kết thúc với một trong 4 kết luận AI — **Malicious, Suspicious, Benign, Inconclusive** — và một *review state* cho biết người đã review chưa; sau kết luận có thể dismiss FP, thông báo, escalate hoặc contain — [Dropzone docs: Investigations](https://docs.dropzone.ai/dropzone-101/terms-and-defs/investigations) (bậc 1); [Dropzone product](https://dropzone.ai/product) (marketing). Dropzone tuyên bố 99,9% accuracy (**marketing**).
- **Prophet Security**: mỗi investigation kết luận true positive / false positive / inconclusive kèm bằng chứng; đội SOC feedback và Prophet dùng cho lần sau — [AWS Marketplace: Prophet](https://aws.amazon.com/marketplace/pp/prodview-xy555gpzgrrvq) (bậc 2, vendor listing); một guide bên thứ ba mô tả nhãn "Recommended Benign / Likely Benign / Recommended Malicious" để người review — [Decryption Digest](https://www.decryptiondigest.com/blog/autonomous-ai-soc-analyst-agents-dropzone-radiant-prophet) (bậc 3, cần đối chiếu); Prophet tự báo >98% accuracy (**marketing**)
- **Elastic (SOC nội bộ)**: accuracy verdict của AI triage tăng ~60% → 92% không đổi model, nhờ thêm context: investigation guide của rule, user risk từ Workday, **closure reason của các case 30 ngày trước trên cùng rule**, và vòng feedback cho agent thấy lần trước sai ở rule đó; tóm tắt AI dài sai 40% nên analyst bỏ đọc; analyst đóng phần lớn alert bằng một click trong Slack; bản mô tả là Elastic 9.5.1 — [Inside Elastic's agentic SOC](https://www.elastic.co/security-labs/blog/alert-triage-agentic-soc-self-correcting-agents) (bậc 1 về thực hành tổ chức, 2026)
- Red Canary: >97% threat do máy phát hiện, nhưng người xác nhận trước khi báo khách — [Red Canary TDR methodology](https://redcanary.com/threat-detection-report/methodology/) (bậc 1, 2026)
- Expel: rapid triage agent "never auto-closes"; mọi khuyến nghị blocked-malware phải được analyst duyệt — [Expel blog](https://expel.com/blog/new-ruxie-ai-power-up-blocked-malware-triage-agent-clears-the-noise/) (bậc 1 về tuyên bố)
- Torq: escalate hành động nhạy cảm cho analyst xác nhận, nên "autonomous" không hoàn toàn không người — [Torq HyperSOC](https://torq.io/hypersoc) (marketing)

### Nhận định
- **Nhận định:** với AI SOC, mỗi case/alert có thể mang **hai (hoặc ba) nhãn**: verdict AI (+confidence), quyết định của người (accept/override) và lý do đóng cuối cùng. Pipeline tuning nên lưu cả ba; cặp "AI nói FP, người override thành TP" là dữ liệu quý nhất, và case AI tự đóng mà không người review cần đánh dấu là nhãn máy (rủi ro vòng lặp tự củng cố nếu dùng để tuning rule).
- **Nhận định:** cách Elastic đưa closure reason 30 ngày của cùng rule vào context là bằng chứng thực tế rằng nhãn đóng case có thể truy ngược theo rule và dùng được — liên quan trực tiếp tới thiết kế ở report cũ.
- **Nhận định:** từ vựng verdict khác nhau (TP/FP vs Malicious/Benign/Inconclusive) → cần một bảng chuẩn hóa nhãn khi gộp nguồn.

### Khoảng trống
- Không xác nhận được agent triage của Microsoft ghi verdict vào field Classification của incident hay vào field riêng của agent; không xác nhận được danh sách đầy đủ giá trị verdict/confidence của Google TIN (không mở được trang).
- Không có đánh giá độc lập (ngoài RCT của chính Microsoft) về tỷ lệ sai của các agent triage.

## Truy vấn đã chạy
- Microsoft Sentinel automation rules triggers incident created updated alert created (standard)
- SANS SOC survey 2025 automation metrics (standard)
- Expel alerts automatically closed percentage SOC metrics (standard)
- Microsoft Security Copilot phishing triage agent verdict false positive (standard)
- Google SecOps triage agent verdict alert investigation Gemini (standard)
- Kokulu "Matched and Mismatched SOCs" findings (standard)
- Red Canary detections false positive rate threats per customer automation exclusion (standard)
- Google SecOps SOAR playbook trigger types alert attached playbook (standard)
- Alahmadi "99% False Positives" USENIX Security 2022 SOC practitioners (standard)
- Defender phishing triage agent classifies incident "false positive" resolves incident classification (standard)
- Tines Voice of the SOC 2023 report findings alerts analysts (standard)
- Splunk SOAR playbook trigger container created event label automation (standard)
- Expel annual threat report alerts to incidents funnel percentage automation resolved (extended)
- Arctic Wolf security operations report alerts escalated to customers ticket triage percent (standard)
- Dropzone AI SOC analyst verdict benign malicious autonomous investigation human review (standard)
- Sentinel incident close classification true positive benign positive false positive automation rule close incident (standard)
- SANS 2024 SOC survey metrics MTTD MTTR tracked percentage tier analysts (standard)
- Google SecOps close case reason malicious not malicious maintenance inconclusive root cause (standard)
- Sentinel ServiceNow bidirectional incident sync close status classification (standard)
- M-Trends 2025 median dwell time days (standard)
- Mandiant M-Trends 2025 global median dwell time 11 days (standard)
- MDR provider customer feedback loop false positive close investigation customer "not malicious" eSentire Huntress workflow (standard)
- Prophet Security AI SOC analyst disposition human review verdict feedback (standard)
- SOC tier 1 tier 2 tier 3 escalation tiered model criticism tierless SOC (standard)
- Defender XDR automated investigation incident resolved automatically "no threats found" classification status (standard)
- Cortex XSOAR pre-process rules drop dedup link incident playbook runs on incident creation (standard)
- Google SecOps Triage agent documentation verdict confidence "true positive" "false positive" alert (standard)
- Elastic security labs alert triage agentic SOC self-correcting agents closure reasons (standard)
- Torq HyperSOC percentage cases auto-remediated Tier-1 autonomous claim (standard)
- Expel Ruxie automation percentage alerts triaged by bots before analyst (standard)
- Microsoft SOC lessons learned tier 1 tier 2 96 percent incidents remediated (standard)
- (WebFetch tới learn.microsoft.com, docs.expel.io, elastic.co, arxiv.org — thất bại do proxy chặn; thử raw.githubusercontent.com/MicrosoftDocs/azure-docs — 404 đường dẫn)
