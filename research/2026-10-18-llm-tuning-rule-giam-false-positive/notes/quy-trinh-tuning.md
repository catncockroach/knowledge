# Quy trình tuning detection rule để giảm False Positive

Góc nghiên cứu: vòng đời detection engineering, các bước tuning trong thực tế, kỹ thuật tuning, metric "FP chấp nhận được", và ví dụ rule trước/sau tuning. Không đi sâu phần LLM và phần test/QA (researcher khác lo).

## 1. Vòng đời detection engineering và vị trí của bước tuning

### Kết luận ngắn
Các framework công khai (Palantir ADS, DDLC của Securonix/Augusto Barros, Forrester DR-DLC, Elastic DEBMM) đều mô phỏng vòng đời phát triển phần mềm: xác định use case → viết rule → test/peer review → đưa vào production → **review và tuning định kỳ** → retire. Tuning là một pha lặp, kích hoạt theo lịch hoặc theo sự kiện (quá nhiều FP, sau sự cố). Mức chắc chắn: **cao**, vì có nhiều nguồn bậc 1 độc lập và thống nhất.

### Phát hiện có nguồn
- DDLC của Securonix có 4 pha: (1) xác định use case, (2) triển khai (connector, parser, rule; test bằng attack simulation; deploy qua change control), (3) **review và tuning**: chỉnh threshold, nguồn dữ liệu, query, điều kiện alert; "This happens at regular intervals and in response to a breach or an adverse situation", (4) retire, tức gỡ content không còn phù hợp và kiểm tra không có content khác phụ thuộc. Trigger của tuning gồm review định kỳ, sau breach, FP quá nhiều, quá nhiều event. Tác giả cũng nhận xét việc test detection content còn yếu và đa số tool không hỗ trợ — [Managing Security Threats With Detection Development Life Cycle, Augusto Barros/Securonix](https://www.securonix.com/blog/managing-security-threats-with-detection-development-life-cycle/) (bậc 1 với vai trò quan điểm chuyên gia/vendor, không rõ ngày, ước khoảng 2022)
- Forrester đề xuất DR-DLC (Detection and Response Development Lifecycle) với 3 nguyên tắc: theo một vòng đời phát triển, agile, và detection-as-code — [Forrester blog](https://www.forrester.com/blogs/announcing-the-detection-and-response-development-lifecycle-dr-dlc-for-detection-engineering) (bậc 2, chỉ thấy qua snippet tìm kiếm, chưa mở trang)
- Palantir ADS framework là template văn bản bắt buộc cho mỗi detection, gồm các mục: Goal, Categorization (MITRE ATT&CK), Strategy Abstract, Technical Context, **Blind Spots and Assumptions**, **False Positives**, **Validation** (cách sinh ra một true positive, "similar to a unit test"), Priority, Response, Additional Resources. Quy trình: Draft → peer review → production. Trong mục False Positives: mỗi strategy "needs to be tested and refined to remove as many false positives as possible" trước production; nếu không đạt FP thấp thì "the alert may need to be broken down, refactored, or entirely discarded." — [ADS-Framework.md, palantir/alerting-detection-strategy-framework](https://github.com/palantir/alerting-detection-strategy-framework/blob/master/ADS-Framework.md) (bậc 1, repo push cuối 12/2021)
- Elastic DEBMM (Detection Engineering Behavior Maturity Model) đặt "Continuously Tuning and Reducing FPs" ở Tier 2, với ngưỡng: Repeatable giảm 10–25% FP rate/quý; Defined giảm >25%/quý; Managed giảm >50% qua nhiều quý; Optimized ">75%" với "automated feedback loops". Model cũng ghi rõ định nghĩa FP rate là "rate determined by ruleset feature owner", và khuyến nghị dùng exception list dùng chung, ghi lại phân tích FP cũ để không chỉnh lặp lại. Các tier khác: Tier 0 peer review (Optimized 90–100% rule), Tier 1 version control/detection-as-code, "Baseline Diagnostic Phase" (Managed: 100% rule chạy thử dạng diagnostic/beta trước production), Tier 3 false negatives, Tier 4 có mục "AI-Assisted FP Reduction" (Managed: "AI-driven suggestions result in a 30-50% reduction in FPs"). Elastic nói các ngưỡng là điểm khởi đầu, tổ chức tự điều chỉnh — [Elastic releases the Detection Engineering Behavior Maturity Model, Ayenson/DeJesus/Bousseaden](https://www.elastic.co/security-labs/elastic-releases-debmm) (bậc 1, 2024-09-06)
- Splunk ES 8.6 docs mô tả vòng đời: detection authoring → detection tuning (phân tích kết quả, loại trừ giá trị field) → throttling → risk-based alerting → detection scheduling — [Tune detections in Splunk Enterprise Security](https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.6/detections/tune-detections-in-splunk-enterprise-security) (bậc 1, docs ES 8.6, không rõ ngày)
- Google SecOps khuyến nghị re-tune mỗi rule trong tuần đầu chạy production, và coi tuning là "not a one-time task. It is an ongoing practice." — [Signal, Not Noise: Tuning Detection Rules with Exclusions and Data Tables, Google Security Community](https://security.googlecloudcommunity.com/tuesday-s-tip-of-the-week-93/tuesday-s-tip-of-the-week-signal-not-noise-tuning-detection-rules-with-exclusions-and-data-tables-8179) (bậc 2, nhân viên Google, 2026-09-01)

### Nhận định
- **Nhận định:** Có hai thời điểm tuning: (a) *pre-production*, khi rule chạy ở chế độ diagnostic/beta hoặc backtest (ADS, DEBMM "Baseline Diagnostic Phase"); (b) *post-production*, một vòng lặp liên tục dựa trên feedback của analyst. Task LLM của chủ repo nằm ở (b) nhưng có thể dùng cho cả (a).
- **Nhận định:** Ba mục "False Positives", "Blind Spots and Assumptions" và "Validation" trong ADS chính là metadata mà một hệ thống đề xuất tuning cần đọc và cập nhật: FP đã biết, điểm mù đã biết, và test case TP phải còn kích hoạt sau khi đổi rule.
- **Nhận định:** "Retire/discard" là một kết quả hợp lệ của tuning, không chỉ thêm exclusion (ADS, DDLC).

### Khoảng trống
- Không tìm được bài viết gốc "Detection Development Lifecycle" của Haider Dost (Snowflake) mà coordinator gợi ý. Truy vấn đã thử: "detection development life cycle Haider Dost", "Snowflake Detection Development Lifecycle medium Haider Dost".
- Không mở được Detection Engineering Maturity Matrix của Kyle Bailey (detectionengineering.io); chỉ có tham chiếu thứ cấp.
- Blog gốc của Palantir (blog.palantir.com) trả về 403; đã dùng file framework trên GitHub thay thế.

## 2. Quy trình tuning từng bước và vai trò (analyst vs detection engineer)

### Kết luận ngắn
Quy trình thực tế: analyst đóng alert/case với **verdict có cấu trúc + bình luận** → tổng hợp định kỳ theo rule để xếp hạng rule "ồn" (volume, tỉ lệ TP, thời gian analyst) → detection engineer mở ticket/issue, đọc sample event, tìm nguyên nhân gốc → chọn kỹ thuật tuning → sửa rule như code (PR, test TP vẫn kích hoạt, peer review) → deploy → theo dõi metric và có khả năng rollback. Analyst có thể tạo exception tạm thời có hạn; thay đổi logic rule thuộc về detection/SOC engineer. Mức chắc chắn: **cao** cho khung chung (nhiều nguồn bậc 1 khớp nhau), **trung bình** cho phân vai cụ thể (khác nhau giữa các tổ chức).

### Phát hiện có nguồn
**Bước 1 – Thu thập feedback (analyst đóng case):**
- Microsoft Sentinel bắt buộc chọn classification khi đóng incident: "True Positive – suspicious activity", "Benign Positive – suspicious but expected", "False Positive – incorrect alert logic", "False Positive – incorrect data", "Undetermined", kèm ô Comment mô tả — [Basic incident tasks… Close an incident, Microsoft Learn](https://learn.microsoft.com/en-us/azure/sentinel/incident-navigate-triage) (bậc 1, cập nhật 2026-08)
- Sentinel nêu các nguyên nhân FP thường gặp, kể cả khi rule viết đúng: hoạt động bình thường của một số user (thường là service principal) trông đáng ngờ; quét bảo mật có chủ đích từ IP đã biết; IP nội bộ không thuộc dải private nhưng lẽ ra phải loại trừ — [Handle false positives in Microsoft Sentinel](https://learn.microsoft.com/en-us/azure/sentinel/false-positives) (bậc 1, ms.date 2026-07-02)

**Bước 2 – Tổng hợp và ưu tiên rule "ồn":**
- Red Canary (2018) chấm điểm mỗi detector theo trọng số của 3 yếu tố, tính trên 28 ngày: conversion rate (tỉ lệ event của detector thành detection thật; ">10%" coi là chấp nhận được), time claimed (giờ analyst bỏ ra, trọng số 0.75; conversion trừ đi với trọng số 0.25), và event count (không đánh trọng số). Năng lực giả định: 254 giờ analyst và ~23.500 event/tuần. "The higher a detector's score, the worse it's performing." Báo cáo được gửi email hằng tuần cho team, review thủ công; mỗi detector điểm cao được mở một GitHub issue với các câu hỏi: có cải thiện được không, có quá ồn không, đã có detector khác phủ chưa, hay để nguyên — [Driving Efficacy Through Detector Tuning, Keshia LeVan (Red Canary), nay đăng lại trên Zscaler](https://www.zscaler.com/blogs/cybersecurity-best-practices/tuning-detectors) (bậc 2, 2018-05-17)
- Sentinel "Tuning insights" (preview) hiển thị cho mỗi rule trong 14 ngày: số alert trung bình mỗi incident, số incident mở/đóng theo classification TP/FP; danh sách entity "highly correlated with incidents that you closed and classified as false positive", thêm vào exclusion bằng 1 click; và top 4 entity xuất hiện nhiều nhất ("hogging the spotlight") — [Get fine-tuning recommendations for your analytics rules](https://learn.microsoft.com/en-us/azure/sentinel/detection-tuning) (bậc 1, ms.date 2026-07-02)
- Splunk ES "Tuning mode" chạy detection trên dữ liệu lịch sử, trả về danh sách giá trị field (username, hostname, command line, IP) có khả năng gây alert, kèm "Detection metrics" (phần trăm giảm noise, tổng event) cập nhật theo thời gian thực khi bật/tắt exclusion; tính năng đang ở dạng beta — [Tune detections in Splunk ES 8.6](https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.6/detections/tune-detections-in-splunk-enterprise-security) (bậc 1)

**Bước 3 – Phân tích nguyên nhân gốc:**
- Red Canary bắt đầu bằng code review logic detector (có lỗi không, đang nhắm vào hành vi gì) rồi mới chọn kỹ thuật — [Red Canary/Zscaler](https://www.zscaler.com/blogs/cybersecurity-best-practices/tuning-detectors) (bậc 2, 2018)
- Google SecOps: xem mẫu alert gần đây, tìm pattern của FP (user, IP, service account, tên resource); "Never suppress alerts blindly. Understand why they fire before tuning them out." — [Google Security Community](https://security.googlecloudcommunity.com/tuesday-s-tip-of-the-week-93/tuesday-s-tip-of-the-week-signal-not-noise-tuning-detection-rules-with-exclusions-and-data-tables-8179) (bậc 2, 2026-09-01)
- Splunk ES: xem sample event (tối đa 5 event cho mỗi related field) để xác định giá trị đó có benign hay không trước khi loại trừ — [Splunk ES 8.6 docs](https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.6/detections/tune-detections-in-splunk-enterprise-security) (bậc 1)
- Ví dụ nguyên nhân gốc "dữ liệu/chuẩn hóa": PR tuning của Elastic đổi `count_distinct(winlog.event_data.TargetUserName)` thành `count_distinct(to_lower(...))`, tức là cùng một user viết hoa/thường khác nhau từng bị đếm thành nhiều user — [elastic/detection-rules PR #6950 "[Rule Tuning] Diverse Rules"](https://github.com/elastic/detection-rules/pull/6950) (bậc 1, merge 2026-10-05)

**Bước 4–7 – Viết thay đổi, test, review, deploy (detection-as-code):**
- SigmaHQ: PR sửa FP dùng tag changelog `fix: <title> - <comment>`, có mục "Example Log Event" ("Fill this in case of false positive fixes"); PR #6417 vừa thêm filter vừa thêm regression test (file evtx + `info.yml` với `match_count: 1`, "Positive Detection Test") để chứng minh rule vẫn bắt được hành vi tấn công sau khi lọc FP — [SigmaHQ/sigma PR #6417](https://github.com/SigmaHQ/sigma/pull/6417) (bậc 1, merge 2026-10-02)
- Elastic detection-rules: mỗi thay đổi tuning là một PR có tiền tố "[Rule Tuning]" (khoảng 1.205 PR đã merge tính đến 10/2026), thường link tới issue/SDH (support case) gốc, ví dụ PR #6985 "Resolves SDH # 817" — [search PR elastic/detection-rules](https://github.com/elastic/detection-rules/pulls?q=is%3Apr+is%3Amerged+%22%5BRule+Tuning%5D%22), [PR #6985](https://github.com/elastic/detection-rules/pull/6985) (bậc 1, 2026-10)
- Securonix DDLC: deploy qua change control; tuning ưu tiên chỉnh nhỏ trước, nếu không hoàn thiện được thì chuyển sang retire — [Securonix](https://www.securonix.com/blog/managing-security-threats-with-detection-development-life-cycle/) (bậc 1/quan điểm, ~2022)
- Red Canary sau khi tách detector đã "review thủ công" để xác nhận không mất detection quan trọng nào — [Red Canary/Zscaler](https://www.zscaler.com/blogs/cybersecurity-best-practices/tuning-detectors) (bậc 2, 2018)

**Bước 8 – Giám sát sau deploy, hết hạn, rollback:**
- Automation rule tạo exception trong Sentinel mặc định "expire automatically after 24 hours", điều này "reduces the chance of false negative errors"; exception có audit trail và tự đóng incident kèm lý do — [Handle false positives in Microsoft Sentinel](https://learn.microsoft.com/en-us/azure/sentinel/false-positives) (bậc 1, 2026)
- Elastic DEBMM: version control và detection-as-code là điều kiện để review/rollback; Tier 2 yêu cầu theo dõi mức giảm FP rate theo quý — [Elastic DEBMM](https://www.elastic.co/security-labs/elastic-releases-debmm) (bậc 1, 2024-09)

**Phân vai:**
- Sentinel: automation rule (exception) "are often generated by analysts"; sửa analytics rule "typically require implementation by Security Operations Center (SOC) engineers"; dùng watchlist cho exception giúp "An analyst can add exceptions without editing the rule, which better follows SOC best practices." — [Handle false positives in Microsoft Sentinel](https://learn.microsoft.com/en-us/azure/sentinel/false-positives) (bậc 1, 2026)
- Red Canary: analyst team review báo cáo; tuning được theo dõi bằng GitHub issue (vai trò detection engineering lead) — [Red Canary/Zscaler](https://www.zscaler.com/blogs/cybersecurity-best-practices/tuning-detectors) (bậc 2, 2018)

### Nhận định
- **Nhận định:** Một quy trình tham chiếu có thể tổng hợp như sau (ghép từ các nguồn trên):
  1. *Analyst (L1/L2):* đóng alert với verdict chuẩn hóa (TP / Benign Positive / FP-logic / FP-data / Undetermined) và comment nêu lý do; khi cần, tạo exception tạm thời có hạn (vd 24h, cửa sổ bảo trì).
  2. *Tự động/DE:* báo cáo định kỳ (tuần) xếp hạng rule theo volume × (1 − precision) × thời gian xử lý.
  3. *Detection engineer:* mở ticket cho từng rule ồn, đọc sample, phân loại nguyên nhân gốc: (a) hành vi hợp lệ đặc thù môi trường (admin, service account, scanner, phần mềm nội bộ) → exception hẹp; (b) logic rule quá rộng → siết điều kiện/tách rule; (c) dữ liệu sai/parse sai/chưa chuẩn hóa → sửa parser/normalize ("FP – incorrect data"); (d) volume cao nhưng tín hiệu yếu → threshold/aggregation, suppression hoặc chuyển sang risk-based; (e) IoC kém (thuộc researcher IoC).
  4. *DE:* viết thay đổi như code (PR), thêm test TP + mẫu FP, backtest trên dữ liệu lịch sử để đo số alert giảm và TP còn lại.
  5. *Peer review/approve* → deploy (có thể qua giai đoạn diagnostic/shadow) → theo dõi metric 1–4 tuần → rollback qua version control nếu TP giảm hoặc phát sinh điểm mù.
- **Nhận định:** Phân biệt "Benign Positive" (rule bắt đúng hành vi nhưng hành vi đó được phép) với "False Positive" (rule sai logic hoặc dữ liệu sai) quyết định kỹ thuật tuning: benign positive thường dẫn tới exception theo ngữ cảnh, FP-logic dẫn tới sửa logic, FP-data dẫn tới sửa pipeline dữ liệu. Đây là input rất quan trọng cho LLM.
- **Nhận định:** Comment tự do của analyst là dữ liệu chính để hiểu nguyên nhân gốc, nhưng chất lượng của nó không đồng đều (xem khoảng trống).

### Khoảng trống
- Không tìm được taxonomy chuẩn ngành (ngoài classification của Sentinel) cho nguyên nhân gốc FP hay schema ticket tuning. Truy vấn đã thử: "detection tuning request analyst feedback loop detection engineer ticket root cause false positive categories" (extended).
- Không có số liệu công khai về chất lượng/độ chính xác của nhãn verdict do analyst gán.
- Chưa có nguồn mô tả chi tiết bước approval (ai ký duyệt, SLA) trong một SOC/MSSP cụ thể.

## 3. Các kỹ thuật tuning: khi nào dùng, ưu/nhược điểm

### Kết luận ngắn
Các kỹ thuật chính: exclusion/allowlist (một field hoặc nhiều field kết hợp, inline hoặc qua lookup/watchlist/data table), siết logic, threshold/aggregation/time window, suppression/dedup, hạ risk score/severity, tách rule, và chuyển sang risk-based alerting. Đồng thuận lớn nhất giữa các nguồn: exclusion càng hẹp (kết hợp nhiều thuộc tính) càng an toàn. Exclusion theo path/tên file dễ bị attacker lợi dụng, và exclusion có xu hướng tích tụ, hiếm khi được gỡ. Mức chắc chắn: **cao**.

### Phát hiện có nguồn
**Exclusion/allowlist:**
- Sentinel chia 2 cách: (1) automation rule, tức exception không sửa rule, áp được cho nhiều rule, có audit trail, có hạn dùng; (2) sửa query của analytics rule, cho phép biểu thức boolean phức tạp và exception theo subnet, dùng watchlist để quản lý tập trung, "the most flexible and complete false positive solution, but are more complex". Ví dụ KQL:
  - đơn giản: `| where IPAddress !in ('10.0.0.8', '192.168.12.1')`
  - kết hợp chặt hơn: `| where IPAddress != '10.0.0.8' and UserPrincipalName != 'user@microsoft.com'`, được mô tả là "more fine-grained exception … reduce the chance for false negatives". **Lưu ý:** theo logic De Morgan, biểu thức `!= A and != B` thực ra loại trừ mọi event có IP=A **hoặc** user=B, nên câu "applies only if both values appear" trong docs có vẻ mâu thuẫn với code. Muốn chỉ loại khi cả hai cùng xuất hiện thì phải viết `where not(IPAddress == '10.0.0.8' and UserPrincipalName == 'user@microsoft.com')`. Đây chính là loại lỗi exclusion quá rộng cần cảnh giác.
  - subnet: `evaluate ipv4_lookup(subnets, IPAddress, network, return_unmatched = true) | where isempty(network)`
  - watchlist: `let allowlist = (_GetWatchlist('ipallowlist') | project IPAddress); … | where IPAddress !in (allowlist)`
  — [Handle false positives in Microsoft Sentinel](https://learn.microsoft.com/en-us/azure/sentinel/false-positives) (bậc 1, 2026)
- Splunk ES phân biệt direct exclusion (một giá trị), relational exclusion (`NOT (source="logins.log" AND host="test-server")`) và multi-field: "Excluding multiple fields with specific values often provide more accurate results than completely excluding a single field." — [Splunk ES 8.6 docs](https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.6/detections/tune-detections-in-splunk-enterprise-security) (bậc 1)
- Splunk security_content: mỗi detection kết thúc bằng một macro rỗng `<tên_detection>_filter` (vd `` `windows_service_created_with_suspicious_service_path_filter` ``) để khách hàng tự thêm exclusion mà không sửa logic gốc; YAML có field `known_false_positives` ("Legitimate applications may install services with uncommon services paths.") — [windows_service_created_with_suspicious_service_path.yml, splunk/security_content](https://github.com/splunk/security_content/blob/develop/detections/endpoint/windows_service_created_with_suspicious_service_path.yml) (bậc 1, version 20, sửa 2026-05-13)
- Elastic: dùng exception khi "a rule is correctly written but fires on known-safe activity specific to your environment"; ví dụ exception `process.name is myautomatedbuild`; phương án khác: nhân bản rule, hạ risk score cho bản chỉ khớp user/process bị loại trừ. Cảnh báo: "Exceptions could result in an undetected client-side execution, or a persistence or malware threat going unnoticed." — [Tune detection rules, Elastic Security docs](https://www.elastic.co/guide/en/security/current/tuning-detection-signals.html) (bậc 1, không rõ ngày)
- Google SecOps (YARA-L): exclusion trong events section (`not $e.principal.user.email_addresses in %approved_admins.email`), allowlist động bằng data table (thêm entry mà không sửa rule) — [Google Security Community](https://security.googlecloudcommunity.com/tuesday-s-tip-of-the-week-93/tuesday-s-tip-of-the-week-signal-not-noise-tuning-detection-rules-with-exclusions-and-data-tables-8179) (bậc 2, 2026-09-01)
- Red Canary: suppression theo process MD5, parent MD5 hoặc command line, nhưng làm kém khi command line biến đổi (ngày tháng, tên file thay đổi) — [Red Canary/Zscaler](https://www.zscaler.com/blogs/cybersecurity-best-practices/tuning-detectors) (bậc 2, 2018)

**Nguy cơ exclusion quá rộng / bị lợi dụng:**
- Preprint "The Exclusion Ratchet" phân tích 8.234 revision của SigmaHQ trong 9 năm: 1.642 exclusion được thêm, 304 bị gỡ (tỉ lệ 5,4:1, ở mức từng rule là 13:1); ước lượng Kaplan-Meier cho thấy 86,7% exclusion vẫn còn sau 3 năm; việc exclusion tồn tại không phụ thuộc vào chuyện rule đó có phải là coverage duy nhất cho technique ATT&CK hay không (p = 0,49); 64,1% exclusion dạng path có thể bị thỏa mãn bởi một process không đặc quyền chỉ cần tự chọn tên file; 31% việc thu hẹp rule không thấy được qua so sánh cấu trúc. Kết luận: thu hẹp "accumulates, is rarely revisited, and is not triaged by consequence" — [The Exclusion Ratchet, Dhananjeyan & U, arXiv:2608.31062](https://arxiv.org/abs/2608.31062) (bậc 1 nhưng là preprint chưa bình duyệt, 2026-08-31)
- MITRE ATT&CK T1564.012 File/Path Exclusions: "Adversaries may attempt to hide their file-based artifacts by writing them to specific folders or file names" mà công cụ bảo mật bỏ qua, và có thể dùng discovery để tìm các exclusion đang có — [MITRE ATT&CK T1564.012](https://attack.mitre.org/techniques/T1564/012/) (bậc 1, tạo 2024-03-29, sửa 2026-05-12)
- Sentinel: exception tạm có hạn (mặc định 24h) để giảm rủi ro false negative — [Microsoft Learn](https://learn.microsoft.com/en-us/azure/sentinel/false-positives) (bậc 1)

**Siết logic / tách rule:**
- Red Canary: detector WIN-SCHEDULED-SCRIPT-EXECUTION thêm điều kiện "users" trong command line, giảm event từ hơn 2.000 xuống 80, conversion tăng lên 58%; một biến thể với "programdata" và "-iserik" đạt conversion 99,9%. Một detector khác được tách thành 2 để tự động hóa có mục tiêu: conversion do người xử lý tăng từ 4% lên 93%, do bot xử lý tăng từ 55% lên 99%; detector gốc bị deactivate nhưng không xóa vì vẫn có coverage riêng — [Red Canary/Zscaler](https://www.zscaler.com/blogs/cybersecurity-best-practices/tuning-detectors) (bậc 2, 2018)
- Palantir ADS: nếu không đạt FP thấp thì "broken down, refactored, or entirely discarded" — [ADS-Framework.md](https://github.com/palantir/alerting-detection-strategy-framework/blob/master/ADS-Framework.md) (bậc 1)

**Threshold / aggregation / time window / suppression:**
- Google SecOps: chỉnh số event và match window (vd từ 10 event/15 phút lên 20 event/15 phút, hoặc 10 event/5 phút); `match: $user over 1h` — [Google Security Community](https://security.googlecloudcommunity.com/tuesday-s-tip-of-the-week-93/tuesday-s-tip-of-the-week-signal-not-noise-tuning-detection-rules-with-exclusions-and-data-tables-8179) (bậc 2, 2026)
- Elastic PR #6985: thêm `with maxspan=1m` vào sequence và bỏ khóa `host.id` thừa — [PR #6985](https://github.com/elastic/detection-rules/pull/6985) (bậc 1, 2026-10). PR #6950: thêm `[rule.alert_suppression]` group_by `["source.ip", "winlog.computer_name"]`, duration 30 phút, `missing_fields_strategy = "doNotSuppress"` — [PR #6950](https://github.com/elastic/detection-rules/pull/6950) (bậc 1, 2026-10)
- Splunk ES: throttling, tức suppress một detection hoặc field trong một khoảng thời gian — [Splunk ES 8.6 docs](https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.6/detections/tune-detections-in-splunk-enterprise-security) (bậc 1)

**Risk-based alerting (RBA) / enrichment / đổi severity:**
- Splunk RBA: detection ghi "intermediate findings" vào risk index; "Events collected in the risk index create a single finding when they meet a specific criteria", ví dụ risk score >100 trong 24h, sự kiện từ 3 sourcetype trên một máy trong 3 ngày, hoặc nhiều tactic ATT&CK trong 7 ngày. Risk modifier điều chỉnh điểm theo asset/identity, ví dụ nhân 1,5 cho admin đặc quyền — [Analyze risk with risk-based alerting in Splunk ES 8.5](https://help.splunk.com/en/splunk-enterprise-security-8/user-guide/8.5/mission-control/analyze-risk-with-risk-based-alerting-in-splunk-enterprise-security) (bậc 1)
- Splunk tuyên bố RBA giảm alert volume 60–80% (blog) hoặc 50–90% / 30–80% (các ebook khác nhau), và một testimonial cho thấy TP rate tăng từ 40% lên 90% trong chưa tới 2 tháng — [Splunk RBA product brief/ebooks](https://www.splunk.com/en_us/pdfs/product-briefs/risk-based-alerting.pdf) (bậc 1 nhưng là **tuyên bố marketing**, chỉ thấy qua snippet tìm kiếm, các tài liệu cho số liệu lệch nhau)
- Splunk security_content: detection có `type: TTP` và `finding.entity.score: 50`, tức gán risk score cho entity, thay vì mọi detection đều sinh alert riêng — [splunk/security_content YAML](https://github.com/splunk/security_content/blob/develop/detections/endpoint/windows_service_created_with_suspicious_service_path.yml) (bậc 1)

### Nhận định
- **Nhận định:** Bảng chọn kỹ thuật theo nguyên nhân gốc:

| Nguyên nhân gốc | Kỹ thuật ưu tiên | Rủi ro chính |
|---|---|---|
| Hành vi hợp lệ, ổn định, xác định rõ (phần mềm nội bộ, scanner, service account) | Exclusion **nhiều field kết hợp** (process + parent + command line/signer + host group), quản lý bằng lookup/watchlist | Exclusion một field (chỉ tên process/path) bị attacker giả mạo (T1564.012); tích tụ không gỡ |
| Hành vi tạm thời (bảo trì, pentest) | Exception có hạn (TTL) | Quên gia hạn/gỡ |
| Logic quá rộng | Siết điều kiện, thêm corroborating condition, tách rule | Mất biến thể tấn công (false negative) |
| Volume cao, tín hiệu đơn lẻ yếu | Threshold/time window, aggregation, suppression/dedup, chuyển sang risk-based | Bỏ lỡ tấn công "low and slow" dưới ngưỡng; suppression che các lần lặp |
| Dữ liệu sai/chưa chuẩn hóa | Sửa parser/normalize (vd `to_lower`) | Ảnh hưởng tới nhiều rule khác |
| Rule không bao giờ ra TP, đã có coverage khác | Retire/deactivate | Mất coverage riêng |

- **Nhận định:** Hướng dẫn của Sentinel về exception "kết hợp" có ví dụ code mà ngữ nghĩa thực tế rộng hơn lời mô tả. Đây là minh chứng rằng ngay cả tài liệu chính thức cũng có thể viết exclusion sai; mọi đề xuất (của người hay LLM) cần backtest định lượng xem bao nhiêu event bị loại, không chỉ đọc code.

### Khoảng trống
- Chưa tìm được bài SpecterOps cụ thể về độ "giòn" (brittleness) của exclusion; truy vấn đã thử: "SpecterOps detection precision recall tuning exclusion bypass", "SpecterOps On Detection brittle detection exclusions tuning Jared Atkinson".
- Chưa có đánh giá độc lập (không phải của vendor) về hiệu quả của RBA.

## 4. "Mức FP chấp nhận được" và cách đo

### Kết luận ngắn
Không có ngưỡng chung cho toàn ngành. Mức chấp nhận được phụ thuộc vào năng lực analyst và base rate. Các metric phổ biến: precision/conversion rate (TP ÷ tổng alert) theo rule, alert volume/ngày, thời gian analyst cho mỗi rule, mức giảm FP rate theo quý (DEBMM). Mốc thực hành được nêu công khai: Red Canary coi detector có conversion >10% là "fairly reasonable". Cách tiếp cận định lượng nhất là tính FPR tối đa từ năng lực xử lý và base rate (Axelsson). Mức chắc chắn: **trung bình**, vì các con số là heuristic của từng tổ chức, còn khảo sát ngành phần lớn là số tự khai.

### Phát hiện có nguồn
- Red Canary: "We consider a detector to be fairly reasonable if it converts over 10% of the time." Đồng thời họ chủ động chấp nhận FP cao: "we'd rather cast a wide net than miss something" — [Red Canary/Zscaler](https://www.zscaler.com/blogs/cybersecurity-best-practices/tuning-detectors) (bậc 2, 2018)
- Magonia Research: FPR chấp nhận được của cả chương trình là giá trị thấp hơn trong hai "trần": (1) *trust ceiling*: chọn Bayesian detection rate mục tiêu (tỉ lệ alert là thật) rồi giải công thức Bayes của Axelsson ra FPR tối đa; (2) *capacity ceiling*: (số analyst × giờ/ngày × 60) ÷ số phút trung bình mỗi alert, trừ số TP dự kiến, rồi chia cho tổng event benign. Ví dụ: 1.000.000 event/ngày, 2 vụ xâm nhập/ngày × 10 event = 20 event độc hại; FPR 0,00001 cho 10 FP + 20 TP (~67% alert là thật); FPR 0,001 cho 1.000 FP + 20 TP (~2% là thật). Mốc tham chiếu của Axelsson: khoảng 100 FP/ngày/analyst. "Acceptable FPR isn't a vibes problem, it's a math problem." — [Determining an Acceptable False Positive Rate for Your SOC, signalblur/Magonia Research](https://www.magonia.io/research/determining-an-acceptable-false-positive-rate-for-your-soc/) (bậc 2, 2026-04-28; dựa trên paper base-rate fallacy của Axelsson, chưa mở paper gốc)
- Elastic DEBMM đo bằng **mức giảm** FP rate theo quý (10–25%, >25%, >50%, >75% tùy tier) thay vì một ngưỡng tuyệt đối, và để định nghĩa FP rate cho "ruleset feature owner" — [Elastic DEBMM](https://www.elastic.co/security-labs/elastic-releases-debmm) (bậc 1, 2024-09)
- Sentinel tuning insights dùng: số alert/incident, incident đóng theo TP/FP trong 14 ngày — [Microsoft Learn detection-tuning](https://learn.microsoft.com/en-us/azure/sentinel/detection-tuning) (bậc 1, 2026)
- Google SecOps (ví dụ minh họa): "A rule that fires 10,000 alerts daily is worse than no rule at all"; rule YARA-L ví dụ trước tuning cho 200 alert/ngày với 80% FP, sau tuning còn 5 alert/ngày với TP 95%+ — [Google Security Community](https://security.googlecloudcommunity.com/tuesday-s-tip-of-the-week-93/tuesday-s-tip-of-the-week-signal-not-noise-tuning-detection-rules-with-exclusions-and-data-tables-8179) (bậc 2, 2026-09-01; số liệu là ví dụ minh họa, không phải đo thực tế)
- Khảo sát ngành (số tự khai, **chưa xác minh trực tiếp tài liệu gốc**): Vectra 2023 State of Threat Detection (2.000 analyst) cho biết trung bình 4.484 alert/ngày, 67% không xử lý kịp, analyst ước 83% là FP — [Vectra 2023 report PDF](https://content.vectra.ai/hubfs/downloadable-assets/V_2023-State-of-Threat-Detection.pdf) (bậc 1 nhưng không trích được text từ PDF; số liệu lấy qua snippet tìm kiếm và bài thứ cấp [Security Magazine](https://securitymagazine.com/articles/99674-90-of-soc-analysts-believe-current-threat-detection-tools-are-effective)), nên cần coi là chưa xác minh.

### Nhận định
- **Nhận định:** Metric nên theo dõi theo **từng rule**: (1) alert volume/ngày; (2) precision = TP ÷ (TP + FP), có tách Benign Positive riêng; (3) tổng thời gian analyst; (4) số TP còn lại sau tuning, đo bằng backtest và test tấn công giả lập (thuộc researcher QA); (5) tuổi và số lượng exclusion của rule (từ phát hiện "Exclusion Ratchet"). Mục tiêu của tuning nên phát biểu theo dạng "giảm X% alert mà không mất TP đã biết nào", không phải một FP rate tuyệt đối.
- **Nhận định:** Trade-off precision/recall: siết rule làm tăng precision nhưng có thể giảm recall. Vì base rate tấn công rất thấp, recall chỉ đo được gián tiếp, qua test case TP, purple team và lịch sử incident, nên khi tuning cần chứng cứ "TP đã biết vẫn còn". Các rule có severity cao/coverage duy nhất cho một technique nên được chấp nhận FP cao hơn.
- **Nhận định:** Ngưỡng ">10% conversion" của Red Canary là heuristic của một MDR có đội analyst lớn, đặt năm 2018, không phải chuẩn ngành.

### Khoảng trống
- Không có benchmark chuẩn ngành công khai nào cho FP rate theo từng rule. Truy vấn đã thử: "Chuvakin acceptable false positive rate detection", "SOC survey percentage alerts false positives per day study 2023 2024".
- Không tìm được bài của Anton Chuvakin về ngưỡng FP chấp nhận được.
- Chưa đọc trực tiếp paper Axelsson (base-rate fallacy, ~2000, ngoài phạm vi năm nhưng là nền tảng lý thuyết).
- Số liệu của Cisco/Microsoft-Omdia/Devo về tỉ lệ FP chỉ thấy qua tóm tắt thứ cấp, chưa xác minh.

## 5. Ví dụ rule trước và sau tuning (nguồn công khai)

### Kết luận ngắn
Có nhiều ví dụ thật trong repo SigmaHQ và elastic/detection-rules: thêm filter hẹp nhiều điều kiện, thêm time window, thêm suppression, chuẩn hóa dữ liệu, kèm regression test chứng minh TP vẫn bắt được. Mức chắc chắn: **cao** (đọc trực tiếp diff).

### Phát hiện có nguồn
- **Quy ước SigmaHQ:** `falsepositives` là field bắt buộc, chỉ để người đọc (không ảnh hưởng logic); giá trị `Unknown` nếu chưa biết, `Unlikely` nếu không dự kiến FP; không chấp nhận các giá trị "None", "Pentest", "Red Team". Đặt tên filter: `filter_main_*` "For filters that are mandatory to the rule's logic, or if the excluded behavior or software is present by default or very common"; `filter_optional_*` "For filters that are based on behaviors or software that aren't part of the default installation" — [sigmahq-rule-convention.md](https://github.com/SigmaHQ/sigma-specification/blob/main/sigmahq/sigmahq-rule-convention.md) (bậc 1, không rõ ngày)
- **Ví dụ 1 – Sigma, filter hẹp + regression test (PR #6417, 2026-10-02):** rule "Renamed Schtasks Execution" (level high, falsepositives: Unlikely) bị FP với lệnh `openfiles /query /fo` vì chuỗi flag giống schtasks. Diff:
  ```yaml
  # Thêm
      filter_optional_cmd_openfiles:
          CommandLine|contains|all:
              - 'openfiles'
              - ' /query '
              - ' /fo'
  # Trước
  -    condition: (all of selection_cmd_* and not filter_main_cmd) or (selection_pe and not filter_main_img)
  # Sau
  +    condition: (all of selection_cmd_* and not filter_main_cmd and not filter_optional_cmd_openfiles) or (selection_pe and not filter_main_img)
  +regression_tests_path: regression_data/rules/windows/process_creation/proc_creation_win_renamed_schtasks_execution/info.yml
  ```
  Kèm file evtx TP (schtasks.exe đổi tên thành `C:\Temp\update.exe`, OriginalFileName=schtasks.exe) với `match_count: 1`. Filter dùng `contains|all` (3 điều kiện cùng lúc) chứ không lọc mọi lệnh chứa "openfiles" — [SigmaHQ/sigma PR #6417](https://github.com/SigmaHQ/sigma/pull/6417) (bậc 1, 2026-10-02)
- **Ví dụ 2 – Sigma, exclusion theo command line đầy đủ của phần mềm phổ biến:** rule "New Firewall Rule Added Via Netsh.EXE" (level medium) có `filter_optional_dropbox` khớp **toàn bộ** command line `advfirewall firewall add rule name=Dropbox dir=in action=allow "program=?:\Program Files (x86)\Dropbox\Client\Dropbox.exe" enable=yes profile=Any`; condition `all of selection_* and not 1 of filter_optional_*`; falsepositives: "Legitimate administration activity", "Software installations" — [proc_creation_win_netsh_fw_add_rule.yml, SigmaHQ](https://github.com/SigmaHQ/sigma/blob/master/rules/windows/process_creation/proc_creation_win_netsh_fw_add_rule.yml) (bậc 1, modified 2023-02-10)
- **Ví dụ 3 – Elastic EQL, exclusion kết hợp process + parent (PR #6986 "Small tuning for package manager FPs"):**
  ```
  - container.id like "?*" and not process.args == "-x"
  + container.id like "?*" and
  + not (
  +   process.args == "-x" or
  +   (process.args like "/tmp/apt-key-gpghome.*" and process.parent.args == "/usr/bin/apt-key") or
  +   (process.parent.args == "/var/lib/dpkg/info/ca-certificates.postinst" and process.args == "/usr/local/share/ca-certificates")
  + )
  ```
  — [elastic/detection-rules PR #6986](https://github.com/elastic/detection-rules/pull/6986) (bậc 1, 2026-10-08)
- **Ví dụ 4 – Elastic, time window + lọc process (PR #6985, "Resolves SDH # 817"):** `sequence by host.id, process.entity_id` → `sequence by process.entity_id with maxspan=1m` và thêm `process.name : ("wscript.exe", "cscript.exe")` — [PR #6985](https://github.com/elastic/detection-rules/pull/6985) (bậc 1, 2026-10-08)
- **Ví dụ 5 – Elastic ES|QL, chuẩn hóa dữ liệu + suppression (PR #6950):** `count_distinct(TargetUserName)` → `count_distinct(to_lower(TargetUserName))`; thêm `alert_suppression` group_by source.ip + computer_name trong 30 phút — [PR #6950](https://github.com/elastic/detection-rules/pull/6950) (bậc 1, 2026-10-05)
- **Ví dụ 6 – YARA-L (Google SecOps), minh họa:** v1 khớp `$e.target.resource.name = /.*admin.*/`, điều kiện `$access_count >= 1` (200 alert/ngày, 80% FP) → v2 thêm `not $user in %approved_admins.email`, `not $e.principal.ip in cidr %corporate_networks.cidr`, ngưỡng `$access_count >= 3`, và xuất `array_distinct` tên resource làm ngữ cảnh (5 alert/ngày, 95%+ TP) — [Google Security Community](https://security.googlecloudcommunity.com/tuesday-s-tip-of-the-week-93/tuesday-s-tip-of-the-week-signal-not-noise-tuning-detection-rules-with-exclusions-and-data-tables-8179) (bậc 2, 2026-09-01, ví dụ minh họa)
- **Ví dụ 7 – KQL (Sentinel):** thêm `| where IPAddress !in ('10.0.0.8', '192.168.12.1')` hoặc allowlist qua `_GetWatchlist('ipallowlist')` — [Microsoft Learn](https://learn.microsoft.com/en-us/azure/sentinel/false-positives) (bậc 1, 2026)
- **Ví dụ 8 – SPL (Splunk security_content):** search kết thúc bằng macro `` `windows_service_created_with_suspicious_service_path_filter` `` làm điểm chèn exclusion của khách hàng; logic gốc đã tự loại các path `*:\Windows\*`, `*:\Program File*`, `*:\Programdata\*` — [splunk/security_content](https://github.com/splunk/security_content/blob/develop/detections/endpoint/windows_service_created_with_suspicious_service_path.yml) (bậc 1, 2026-05)
- SigmaHQ có nhiều PR gom các bản sửa FP, vd #6019 và #5989 "Reduce false positives across multiple Windows rules" (2026), #5167 "Fix multiple false positives found in the wild" (2025-01) — [GitHub search SigmaHQ commits](https://github.com/SigmaHQ/sigma/pulls?q=is%3Apr+false+positive) (bậc 1)

### Nhận định
- **Nhận định:** Kho rule công khai (SigmaHQ, elastic/detection-rules, splunk/security_content) với lịch sử PR "fix FP"/"[Rule Tuning]" là nguồn dữ liệu tốt để xây bộ ví dụ few-shot hoặc bộ đánh giá (rule trước → diff → rule sau + mẫu log) cho task LLM. Riêng SigmaHQ có thêm regression test dạng evtx/JSON.
- **Nhận định:** Pattern chung của một bản tuning "tốt" trong các ví dụ trên: exclusion khớp nhiều thuộc tính cùng lúc (`contains|all`, process AND parent), gắn với phần mềm/hành vi cụ thể có tên, đặt tên filter có nghĩa, và có test TP đi kèm.
- **Nhận định:** Ví dụ Dropbox trong rule netsh dùng ký tự đại diện `?:\Program Files…\Dropbox.exe`. Dù khớp toàn bộ command line, attacker vẫn có thể đặt payload đúng path đó nếu có quyền ghi, vì vậy path-based exclusion vẫn mang rủi ro theo phát hiện của "Exclusion Ratchet".

### Khoảng trống
- Chưa có ví dụ trước/sau dạng SPL từ git history của splunk/security_content (mới có cơ chế filter macro).
- Chưa tìm ví dụ tuning riêng cho rule match IoC (thuộc researcher IoC).

## Truy vấn đã chạy
- Palantir Alerting and Detection Strategy framework (standard)
- detection engineering false positive tuning process (standard)
- Splunk risk-based alerting reduce alert volume (standard)
- detection development life cycle Haider Dost (standard)
- Microsoft Sentinel tune analytics rules false positives automation rule exclusion (standard)
- detection engineering maturity matrix Kyle Bailey (standard)
- SigmaHQ rule filter_main filter_optional falsepositives convention (standard)
- Chuvakin acceptable false positive rate detection (standard)
- SpecterOps detection precision recall tuning exclusion bypass (standard)
- Splunk RBA tuning risk rules "risk notable" false positive Haylee Mills (standard)
- attackers abuse SIEM EDR exclusions allowlist masquerading detection blind spot (standard)
- SOC survey percentage alerts false positives per day study 2023 2024 (standard)
- Florian Roth detection rule false positives filters tuning blog (standard)
- detection tuning request analyst feedback loop detection engineer ticket root cause false positive categories (extended)
- Snowflake "Detection Development Lifecycle" medium Haider Dost (standard)
- SpecterOps "On Detection" brittle detection exclusions tuning Jared Atkinson (standard)
- GitHub API: search commits/PR SigmaHQ/sigma "false positive"; search PR elastic/detection-rules "[Rule Tuning]"; đọc diff PR SigmaHQ #6417, Elastic #6985, #6986, #6950, #6960
