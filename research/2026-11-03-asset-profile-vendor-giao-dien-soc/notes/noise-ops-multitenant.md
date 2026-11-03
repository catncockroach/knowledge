# Dùng asset context để giảm nhiễu, vận hành SOC và đa tenant MSSP

## 1. Asset/identity context giảm nhiễu và tăng chất lượng ưu tiên alert thế nào

### Kết luận ngắn
Mọi vendor lớn đều đưa criticality/priority của asset và identity vào công thức ưu tiên: Splunk ES (ma trận urgency = severity × priority, risk factor nhân/cộng điểm), Elastic (trọng số criticality 0,5–2 cộng vào entity risk score), Google SecOps (context-aware analytics chấm điểm và lọc ngay lúc detection chạy), Microsoft (criticality 4 mức là một input của AI incident prioritization). Mức chắc chắn về **cơ chế: cao** (docs chính thức). Mức chắc chắn về **hiệu quả định lượng: thấp–trung bình**, vì mọi con số giảm alert tìm được đều do vendor công bố, không có benchmark độc lập.

### Phát hiện có nguồn
**Splunk ES: urgency và RBA**
- Urgency của notable event là tổ hợp của severity của correlation search và priority của asset/identity liên quan. Nếu cả asset lẫn identity đều có priority thì lấy giá trị cao hơn. Severity informational luôn cho urgency informational. Asset priority unknown/low thì severity high chỉ ra urgency medium. Asset priority critical thì severity high hoặc critical đều ra urgency critical. Bảng urgency là một lookup sửa được (Configure > Content > Content Management > Urgency Levels). — [How urgency is assigned to notable events in Splunk ES 7.2](https://help.splunk.com/en/splunk-enterprise-security-7/user-guide/7.2/incident-review/how-urgency-is-assigned-to-notable-events-in-splunk-enterprise-security) (bậc 1, 2023–2024)
- Risk factor (risk modifier) điều chỉnh điểm của từng risk event. Các phép cộng luôn chạy trước các phép nhân. Ví dụ của docs: base 5, cộng 5 và 6 được 16, nhân 2 hai lần ra 64. Risk factor mặc định cho đích critical là "if the dest_priority field value is 'critical', the risk factor is multiplied by 1.5". Ví dụ thứ hai: user nằm trong watchlist và asset priority critical thì nhân 1,2. Nhiều điều kiện trong một factor được ghép bằng AND. Mọi factor có sẵn đều hiện trong editor nhưng mặc định tắt. Cần capability `edit_risk_factor`. — [Create risk factors to adjust risk scores in Splunk ES 8.1](https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.1/risk-based-alerting/create-risk-factors-to-adjust-risk-scores-in-splunk-enterprise-security) (bậc 1, 2025); [ES 7.3.2 Createriskfactors](https://docs.splunk.com/Documentation/ES/7.3.2/RBA/Createriskfactors) (bậc 1)
- RBA chỉ sinh risk notable khi risk object vượt ngưỡng. Threshold có thể gắn với criticality của asset hoặc identity. Splunk tự nhận RBA chưa được curate thì "can generate as many notables as traditional alerting" và tạo notable trùng lặp. Các khuyến nghị gồm: dedup, ưu tiên threat object hơn risk object trong risk incident rule, rút ngắn cửa sổ (24h xuống 12h), tinh chỉnh cho các hoạt động dự đoán được như cài tool mới. — [Managing risk using RBA in Splunk ES 7.3 – best practices](https://help.splunk.com/en/splunk-enterprise-security-7/risk-based-alerting/7.3/best-practices/managing-risk-using-risk-based-alerting-in-splunk-enterprise-security) (bậc 1, 2024)
- **Con số vendor công bố (chưa kiểm chứng độc lập, và lệch nhau giữa các tài liệu):**
  - Blog ES 6.4 nói khách hàng giảm 60–80% khối lượng alert.
  - "The Splunk Guide to RBA" ghi giảm 30–80%, với chú thích con số lấy từ một testimonial duy nhất.
  - RBA FAQ và Alert Fidelity Accelerator ghi giảm 50–90%.
  - Case study một ngân hàng Fortune 100: giảm 65% alert, fidelity tăng khoảng 2 lần.
  - Johnson Matthey: fidelity +30%, thời gian xử lý case −83%.
  - Blog Splunk: true positive rate của một khách hàng tăng từ dưới 10% lên trên 30%.

  Nguồn: [Better detections… ES 6.4](https://splunk.com/en_us/blog/security/better-detections-and-cloud-coverage-with-splunk-enterprise-security-6-4.html) (bậc 1 – marketing, không rõ ngày); [Splunk Guide to RBA (PDF)](https://www.splunk.com/en_us/pdfs/gated/ebooks/the-splunk-guide-to-risk-based-alerting.pdf) (bậc 1 – marketing); [Johnson Matthey CS](https://splunk.com/content/dam/splunk2/en_us/pdfs/customer-success-stories/johnson-matthey.pdf) (bậc 1 – marketing); [Risk-Based Alerting: The New Frontier for SIEM](https://www.splunk.com/en_us/blog/security/risk-based-alerting-the-new-frontier-for-siem) (bậc 1 – marketing). Các con số này lấy từ snippet tìm kiếm. File PDF Fortune 100 (`fortune100-finservices-CS.pdf`) trả về 404 khi mở, nên con số 65% chưa xác minh được tận nơi.

**Elastic Security: asset criticality trong entity risk score**
- Score gốc lấy từ alert Open và Acknowledged trong 30 ngày (mặc định), xử lý tối đa 10.000 alert mỗi entity, tính lại mỗi giờ, giữ lịch sử từng lần tính. Chỉ entity có trong entity store mới được chấm điểm. Trọng số mặc định theo mức criticality: Low 0,5, Medium 1, High 1,5, Extreme 2 ("subject to change"). Phần đóng góp nằm trong một category riêng là "Asset Criticality", ngoài các category Alerts và Watchlist (category Privileged User có ở 9.0–9.3, bị bỏ từ 9.4). Ví dụ: Alerts 36,16 cộng Asset Criticality 16,95 ra 53,11 (Moderate). Không gán criticality thì score bằng đúng điểm Alerts. Các mức: Unknown <20, Low 20–40, Moderate 40–70, High 70–90, Critical >90. Docs không công bố công thức quy trọng số ra điểm. — [Entity risk scoring – Elastic Docs](https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/entity-risk-scoring) (bậc 1, bản hiện hành 2026)
- Sửa criticality của từng entity thì score được tính lại ngay. Import file hàng loạt thì phải chờ lần chấm điểm theo giờ kế tiếp. — [Asset criticality – Elastic Docs](https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/asset-criticality) (bậc 1); [8.13 asset criticality](https://www.elastic.co/guide/en/security/8.13/asset-criticality.html) (bậc 1, 2024)

**Google SecOps: context-aware analytics**
- Mục tiêu là đưa context vào sớm: "Making relevant context available for heuristic-driven contextual risk scoring of detections at detection execution time". Context dùng cho "detection filtering, heuristic alert prioritization, triage, and investigation", và giúp "filter out entire clusters of threats that may be expected or represent little or no danger to the enterprise". Nguồn context: EDR, firewall/proxy, kết quả scan lỗ hổng, CMDB, IAM (quyền tài khoản, dữ liệu asset đang chứa), IOC, Azure AD (ngày nghỉ việc, chức danh). Ví dụ dùng: brute-force vào tài khoản có quyền admin; asset chứa dữ liệu quan trọng có kết nối ra ngoài; lọc bỏ sandbox/dev network không có dữ liệu nhạy cảm. Entity context có khoảng hiệu lực (validity interval). Event chỉ join được với context khi timestamp của event nằm trong khoảng đó. Entity context không dùng được làm pivot của sliding window. — [Overview of context-aware analytics – Google SecOps](https://docs.cloud.google.com/chronicle/docs/detection/context-aware-analytics) (bậc 1, 2025–2026)
- Rule có thể tính risk score trong phần `outcome`. Entity risk score được lưu tách khỏi entity context, nên rule dùng cả hai cần hai biến event riêng (docs có ví dụ ngưỡng 100). — [Specify entity risk score in rules](https://docs.cloud.google.com/chronicle/docs/detection/yara-l-entity-risk-score) (bậc 1)

**Microsoft Defender XDR / Exposure Management**
- Critical asset management tự nhận diện và phân loại asset quan trọng: có classification định sẵn cho device, identity, cloud resource, và cho tạo classification tuỳ biến. Có 4 mức criticality, cấu hình ở Settings > Microsoft XDR > Rules > Critical asset management. Asset khớp classification có thể bị loại nếu không đạt ngưỡng của tổ chức (ví dụ một DC không business-critical). — [Critical asset management – Microsoft Learn](https://learn.microsoft.com/en-us/security-exposure-management/critical-asset-management) (bậc 1, 2025–2026)
- AI-powered incident prioritization (công bố 01/2026) dùng asset criticality làm một input, cùng với kỹ thuật ATT&CK, loại và độ hiếm của alert, và các threat nổi bật. Microsoft không công bố trọng số. — [Introducing AI-powered incident prioritization in Microsoft Defender](https://techcommunity.microsoft.com/blog/microsoftthreatprotectionblog/introducing-ai-powered-incident-prioritization-in-microsoft-defender/4483834) (bậc 1 – blog vendor, 2026-01); [Redmondmag](https://redmondmag.com/articles/2026/01/09/new-microsoft-machine-learning-tools.aspx) (bậc 2, 2026-01-09)

**Suppression/allow-list theo asset class**
- Trang detection strategy (mirror của MITRE ATT&CK DET0867 "Detection of vulnerability scanning") khuyến nghị tách scan được phép khỏi nguồn lạ bằng dải IP scanner được duyệt, lịch scan và change record, và tương quan hoạt động scan với asset criticality thay vì chỉ cảnh báo theo khối lượng. — [DET0867 Detection of vulnerability scanning (mirror)](https://security.glexia.com/learn/attack/detections/DET0867-detection-of-vulnerability-scanning) (bậc 3, chưa mở được bản gốc trên attack.mitre.org)
- Thực tế ở Rapid7 InsightIDR: người dùng phản ánh không allow-list được scanner engine của InsightVM, phải tự động đóng investigation theo source IP, và chính họ thấy cách này mong manh. — [Allow InsightVM – Exclude From Alerts (Rapid7 Discuss)](https://discuss.rapid7.com/t/allow-insightvm-exclude-from-alerts/6403) (bậc 3, forum, chỉ làm minh hoạ)

### Nhận định
- Vendor dùng criticality theo ba mẫu: (a) **ma trận** severity × priority (Splunk urgency), (b) **hệ số nhân/cộng** vào risk event hoặc entity score (Splunk risk factor ×1,5 cho đích critical; Elastic trọng số 0,5–2), (c) **feature cho model hoặc rule** (Microsoft AI prioritization, Google outcome score). Với sản phẩm trên OCSF, mẫu (a) và (b) minh bạch và dễ giải thích cho analyst. Nên cho mỗi tenant tự sửa ma trận và hệ số.
- Suppression theo asset class (scanner, jump host, DC, build server) nên là **tag/role** trên asset profile, được rule tham chiếu, kèm lý do, người duyệt và hạn review. Không nên là exception cứng theo IP, nhất là khi IP động hoặc trùng giữa các tenant.
- Con số giảm 30–90% alert là tuyên bố marketing. Báo cáo cuối không nên dùng chúng làm benchmark.

### Khoảng trống
- Không tìm được nghiên cứu độc lập hay paper SANS nào đo hiệu quả giảm nhiễu nhờ asset context. Truy vấn đã thử: "risk-based alerting case study alert reduction percent", "detection engineering asset context suppress…".
- Chưa tìm được hướng dẫn practitioner cụ thể về tuning theo tier admin (DC, jump host).
- Chưa mở được PDF Fortune 100 (404).

## 2. Vận hành: coverage/health log source theo asset, KPI chất lượng inventory, profile trong triage

### Kết luận ngắn
Vendor giám sát "asset im lặng" bằng ba cách: rule hoặc alert "không có event trong N phút" (Google SecOps silent-host monitoring), bảng health của connector cùng workbook phát hiện bất thường (Sentinel), và cột "sensor health" trong device inventory (Defender). CIS Controls cho sẵn công thức KPI coverage và inventory có thể áp dụng ngay. Mức chắc chắn: **cao** cho cơ chế và KPI CIS, **thấp** cho nội dung hướng dẫn của CISA/ASD (chưa đọc được bản PDF).

### Phát hiện có nguồn
- **Google SecOps silent-host monitoring (SHM):**
  - Cách 1: gắn ingestion label (vd `ingestion_source` = `host.name` qua processor Copy Field của Bindplane), rồi đặt alert Cloud Monitoring theo metric "Chronicle Collector > Ingestion > Total Ingestion Log Count" khi tốc độ xuống dưới ngưỡng. Ngưỡng thấp bắt được collector chết, ngưỡng cao bắt được khoảng trống log ở upstream. Nhược điểm: phải cấu hình ngoài SecOps và bị giới hạn số ingestion label.
  - Cách 2: dashboard đếm số silent host theo ngày, trễ tới 6 giờ, không alert được.

  Nguồn: [Silent-host monitoring – Google SecOps](https://docs.cloud.google.com/chronicle/docs/ingestion/silent-host-monitoring) (bậc 1, 2025–2026)
- Theo snippet của trang ingestion health: rule YARA-L mẫu theo hostname quét cửa sổ 20 phút, đệm 1.500 giây cho độ trễ index, và alert khi host không có event trong 10 phút gần nhất nhưng vẫn có trong 20 phút. Health Hub cho trạng thái theo feed, data source, log type. Metric absence alert ví dụ 60 phút. — [Check data ingestion health – Google SecOps](https://docs.cloud.google.com/chronicle/docs/ingestion/ingestion-overview) (bậc 1). Chi tiết rule lấy từ snippet tìm kiếm, chưa đọc nguyên văn trên trang.
- **Microsoft Sentinel:**
  - Workbook "Data collection health monitoring" có 3 tab: Overview (volume, EPS, thời điểm nhận log cuối), Data collection anomalies (bất thường theo table và data source, dùng `series_decompose_anomalies()`), và Agent info.
  - Bảng `SentinelHealth` chỉ hỗ trợ một số connector (AWS CloudTrail/S3, Dynamics 365, Office 365, MDE, TI-TAXII, TI Platforms, các connector dựa trên Codeless Connector Framework).
  - Cách ghi sự kiện: đổi trạng thái success↔failure được ghi ngay. Trạng thái ổn định được ghi mỗi giờ một lần. Lỗi tạm thời (throttling) chỉ ghi khi kéo dài quá 60 phút. Mỗi connector, mỗi workspace có một failure summary theo giờ.

  Nguồn: [Monitor the health of your data connectors – Microsoft Learn](https://learn.microsoft.com/en-us/azure/sentinel/monitor-data-connector-health) (bậc 1, ms.date 2026-07-02)
- **Defender XDR device inventory** cho lọc theo Sensor health state, Antivirus status, First seen, Exclusion state, Managed by, Criticality level. Đây là các trường cốt lõi để biết asset nào "thiếu EDR" hoặc "đã ngừng báo cáo". — [Devices in multitenant management – Microsoft Learn](https://learn.microsoft.com/en-us/defender-xdr/mto-tenant-devices) (bậc 1, ms.date 2024-03-15, cập nhật 2026-09)
- **CIS Control 8.2 (Collect Audit Logs, IG1):** M1 = số asset có khả năng ghi log; M2 = số asset được cấu hình log đúng quy trình; M3 = số asset cấu hình sai. Metric Coverage = **M2/M1**. — [CIS Controls Assessment Specification – 8.2](https://controls-assessment-specification.readthedocs.io/en/latest/control-8/control-8.2.html) (bậc 1)
- **CIS Control 1.1:** inventory phải "accurate, detailed, and up-to-date" và được review "bi-annually, or more frequently". Các measure:
  - M2 = số thiết bị phát hiện được qua discovery; M3 = số thiết bị có ở cả inventory lẫn discovery.
  - M4 = có trong inventory nhưng không phát hiện được, tức asset có thể đã stale.
  - M5 = phát hiện được nhưng không có trong inventory, tức asset unauthorized hoặc unknown.
  - M6, M7 = số bản ghi đủ hoặc thiếu thông tin chi tiết.
  - M8 = số tháng từ lần cập nhật cuối. Quá 6 tháng thì điểm bằng 0.
  - Accuracy = M3/M2. Công thức Completeness in trong spec là M8/M1, có vẻ là lỗi của spec (lẽ ra là M6/M1).

  Nguồn: [CIS Controls Assessment Specification – 1.1](https://controls-assessment-specification.readthedocs.io/en/latest/control-1/control-1.1.html) (bậc 1)
- **CISA/ASD "Best practices for event logging and threat detection"** (21/08/2024): ASD's ACSC chủ trì, đồng tác giả gồm CISA, FBI, NSA, NCSC-UK, CCCS, NCSC-NZ, CERT NZ, NISC, JPCERT/CC, NIS, NCSC-Korea, CSA Singapore, AIVD, MIVD. Tài liệu đặt baseline thực hành logging. — [CISA resource page](https://cisa.gov/resources-tools/resources/best-practices-event-logging-and-threat-detection) (bậc 1, 2024-08-21). Theo các tóm tắt thứ cấp, tài liệu có 4 trụ: chính sách logging, thu thập và tương quan tập trung, lưu trữ an toàn và toàn vẹn, chiến lược phát hiện. — [Canadian Centre for Cyber Security](https://www.cyber.gc.ca/en/news-events/best-practices-event-logging-and-threat-detection) (bậc 1–2, 2024)
- **NIST SP 800-92r1 (ipd, 11/10/2023)** "Cybersecurity Log Management Planning Guide" thay SP 800-92, có dạng playbook lập kế hoạch. Comment đóng 29/11/2023. Trang CSRC vẫn ghi "addressing public comments", chưa thấy bản final. — [CSRC SP 800-92r1 ipd](https://csrc.nist.gov/pubs/sp/800/92/r1/ipd) (bậc 1, 2023-10-11)

### Nhận định
- Bộ KPI tối thiểu cho chức năng asset của SOC đa tenant, tính theo từng tenant:
  - Logging coverage % = M2/M1 (CIS 8.2), tách theo loại log: EDR, auth, network, cloud.
  - Unknown/unauthorized assets = M5.
  - Stale assets = M4, hoặc last_seen quá N ngày.
  - Completeness % = M6/M1.
  - Inventory freshness = M8 hoặc độ trễ đồng bộ nguồn.
  - Số silent host theo cửa sổ 10, 20, 60 phút.
- Asset profile nên có khối "Telemetry health": danh sách nguồn log hoặc log type đã thấy cho asset (map OCSF class hoặc `metadata.product`), last event time cho từng nguồn, trạng thái expected/observed, và badge "silent". Profile chỉ có ích khi phân biệt được "không có alert" với "không có dữ liệu".

### Khoảng trống
- Chưa đọc được PDF CISA/ASD (cyber.gov.au trả 503 hoặc ngắt kết nối, link trên cisa.gov trả HTML). Vì vậy chưa trích được câu cụ thể về ưu tiên log source theo critical asset.
- Chưa đọc nội dung nhóm task INV của NIST SP 800-92r1.
- Chưa tìm được tài liệu "asset coverage" của Splunk (Lantern, ES) và tài liệu playbook triage dùng asset profile (SANS).

## 3. Đa tenant / MSSP

### Kết luận ngắn
Có hai mô hình: (1) **instance hoặc tenant riêng cho từng khách, cộng một lớp tổng hợp** (Defender XDR multitenant management, Cortex XSIAM parent/child, Wazuh cluster riêng cộng cross-cluster search); (2) **một instance chung, tách bằng nhãn hoặc domain** (Google SecOps Data RBAC theo namespace, QRadar domain, Wazuh agent group cộng document-level security). Chỉ QRadar có tài liệu rõ về việc IP trùng: dùng khoá (domain, IP). Mức chắc chắn: **trung bình–cao** cho cơ chế tách dữ liệu, **thấp** cho cách mỗi vendor cấu hình criticality và tag riêng theo tenant.

### Phát hiện có nguồn
- **IBM QRadar domains:**
  - Lý do cần domain: "Log sources that have the same IP address cause problems with correlation, reporting, searching, and asset profiling." Gán từng log source vào domain riêng. Event collector, flow collector, data gateway có thể gán cùng domain. Search có thể thêm cột domain. Tình huống nêu trong docs: sáp nhập công ty, MSSP onboard khách mới. — [Overlapping IP addresses – IBM QRadar](https://www.ibm.com/docs/SSKMKU/com.ibm.qradar.doc/c_domain_example_ip_separation.html) (bậc 1, không rõ ngày)
  - Domain giúp quản lý dải IP trùng trên hạ tầng QRadar dùng chung. — [Domain segmentation – IBM](https://www.ibm.com/docs/en/SSKMKU/com.ibm.qradar.doc/c_domain_segmentation.html) (bậc 1)
  - QRadar định danh thực thể bằng tổ hợp "IP address and domain" thay vì chỉ IP. — [QRadar domains and multi-tenancy – IBM Community (Holly Wright)](https://community.ibm.com/community/user/blogs/holly-wright/2020/04/24/qradar-domains-and-multi-tenancy) (bậc 2, 2020)
  - Asset do scanner có domain phát hiện được tự gán vào domain của scanner. Mỗi asset mang domain ID. Security profile giới hạn được theo domain (flows, events, assets, offenses). User không phải admin mà không được gán domain thì không thấy gì. — [Domain definition and tagging – IBM](https://www.ibm.com/docs/en/SSKMKU/com.ibm.qradar.doc/c_domain_defining.html) (bậc 1). Câu về scanner và asset lấy từ snippet tìm kiếm; câu "each asset is assigned to a domain; assets can have overlapping IP addresses" lấy từ [IBM QRadar for MSPs (slide 2015)](https://www.slideshare.net/slideshow/ibm-q-radar-for-msps/48961730) (bậc 2, 2015, có thể đã cũ)
- **Google SecOps Data RBAC:**
  - Một scope gồm allow label và (tuỳ chọn) deny label; deny được ưu tiên. Các label cùng loại ghép bằng OR, khác loại ghép bằng AND. Label gán lúc ingest gồm namespace (tuỳ chọn), ingestion metadata (tuỳ chọn), log type (bắt buộc). — [Data RBAC overview – Google SecOps](https://docs.cloud.google.com/chronicle/docs/administration/datarbac-overview) (bậc 1, 2025–2026)
  - Bật Data RBAC trước khi gán scope cho rule thì mọi rule cũ nhận global scope. Dashboard của user có nhiều scope hiển thị dữ liệu gộp của mọi scope được phép (tức một dạng view tổng hợp kiểu MSSP). — [Impact of data RBAC on features](https://docs.cloud.google.com/chronicle/docs/administration/datarbac-impact) (bậc 1); [Configure data RBAC for Dashboards](https://docs.cloud.google.com/chronicle/docs/administration/configure-datarbac-dashboards) (bậc 1)
  - Mẫu practitioner: mỗi tenant một scope allow-list namespace, dùng chung một slug cho namespace, scope và SOAR environment. "Multi-tenancy" ở đây là một bộ quy ước, không phải tính năng của nền tảng. Có báo cáo rằng Ingestion API mới không điền `ingestion_kv_labels`, nên scope theo ingestion label có thể không khớp gì (chưa kiểm chứng). — [Multi-tenancy on a single Google SecOps, part 3](https://security.googlecloudcommunity.com/google-security-operations-2/multi-tenancy-on-a-single-google-secops-part-3-who-sees-what-and-where-the-alert-lands-7899) (bậc 2–3, community)
- **Microsoft Defender XDR multitenant management:**
  - Trang Tenants liệt kê từng tenant: số device và loại device, số device high value và high exposure, số device có thể onboard. Đầu trang có tổng toàn bộ tenant: high risk, high exposure, internet facing, can be onboarded, newly discovered, high value.
  - Device inventory gộp giống của MDE, thêm cột **Tenant name**, nhưng không có tab network, IoT, uncategorized. Lọc được theo tenant, risk, criticality, sensor health, AV status, tags, first seen, internet facing, group, exclusion state, managed by.
  - Thao tác ngay trên danh sách gồm sửa tag, exclusion, report inaccuracy. Bấm vào tên tenant thì chuyển sang inventory của tenant đó trong portal để làm các thao tác đầy đủ.

  Nguồn: [Devices in multitenant management – Microsoft Learn](https://learn.microsoft.com/en-us/defender-xdr/mto-tenant-devices) (bậc 1, ms.date 2024-03-15)
- **Cortex XSIAM:** child tenant là instance riêng, lưu dữ liệu riêng, được ghép cặp với parent. Có hai mô hình license: central (parent cấp endpoint hoặc GB cho child, child tự ghép cặp) và customer-owned (ghép cặp thủ công, admin của child phải duyệt). Trang Tenant Management của parent hiển thị trạng thái ghép cặp và lần đồng bộ cuối. — [MSSP multi-tenant – Cortex XSIAM docs](https://cortex-docs.paloaltonetworks.com/cortex-xsiam/configure-cortex-xsiam/multi-tenant/what-is-cortex-xsiam-multi-tenant/mssp-multi-tenant) (bậc 1); [What is Cortex XSIAM multi-tenant](https://cortex-docs.paloaltonetworks.com/cortex-xsiam/configure-cortex-xsiam/multi-tenant/what-is-cortex-xsiam-multi-tenant) (bậc 1). Câu "parent xem được alert của mọi child" lấy từ snippet tìm kiếm.
- **Wazuh:** Security plugin của indexer quản lý users, roles, role mappings, action groups và tenants. Tenant dùng để cô lập saved object như dashboard và index pattern. — [Wazuh dashboard multi-tenancy](https://documentation.wazuh.com/current/user-manual/wazuh-dashboard/multi-tenancy.html) (bậc 1); [Wazuh indexer security (5.0-rc)](https://documentation.wazuh.com/5.0-rc/user-manual/wazuh-indexer/security.html) (bậc 1). Mẫu practitioner: mỗi khách một agent group hoặc label, rồi lọc bằng document-level security trên index alert. Hoặc mỗi khách một cụm indexer và manager, cộng một indexer/dashboard trung tâm dùng cross-cluster search. Có báo cáo rằng view Overview và Vulnerabilities không tôn trọng bộ lọc theo group. — [Wazuh mailing list – Multi Tenancy for MSSP](https://groups.google.com/g/wazuh/c/-141kWNG2Yc) (bậc 3)
- **Splunk ES:** framework Asset & Identity lưu dữ liệu ở dạng lookup CSV, merge thành 4 lookup. Từ ES 6.0 hỗ trợ custom field. Không tìm thấy tài liệu chính thức về chế độ đa tenant hay trường tenant. — [Format an asset or identity list as a lookup – Splunk ES](https://docs.splunk.com/Documentation/ES/latest/User/AssetandIdentityLookupReference) (bậc 1)

### Nhận định
- Với IP private trùng giữa các tenant, khoá định danh asset bắt buộc phải có tenant (và tuỳ trường hợp cả network zone hoặc VPC): `(tenant_id, network_zone, ip)`, giống tổ hợp (domain, IP) của QRadar. Mọi bước enrichment trên OCSF (`device.ip`, `src_endpoint.ip`) phải tra cứu trong phạm vi tenant của event, không bao giờ tra toàn cục.
- View tổng hợp cho MSSP nên theo mẫu Defender MTO: trang tenant list với các chỉ số chuẩn hoá (high value, high exposure, can-onboard, newly discovered, sensor unhealthy), cộng inventory gộp có cột tenant, và drill-down vào profile của tenant. Thao tác ghi (tag, exclusion) nên ghi audit theo tenant.
- Criticality và tag nên là cấu hình riêng mỗi tenant (ma trận urgency, risk factor, classification rule), có thể kế thừa từ một template của MSSP. Không vendor nào tìm được có tài liệu rõ về cơ chế template/kế thừa này: đây là khoảng trống, cũng là cơ hội thiết kế.

### Khoảng trống
- Chưa xác minh XSIAM parent có xem được asset inventory của child hay không, và có đồng bộ content (rule, policy) từ parent xuống không.
- Chưa tìm hiểu Elastic Spaces (asset criticality và entity store có tách theo space không) và Sentinel/Azure Lighthouse (cross-workspace asset view).
- Chưa có tài liệu nào về criticality hoặc tag riêng theo tenant ở vendor nào.

## Hình minh hoạ giao diện

| vendor | màn hình | mô tả | image URL | trang nguồn | đã kiểm tra |
|---|---|---|---|---|---|
| Microsoft Defender XDR | Multitenant – Tenants list (Devices) | Danh sách tenant, số device và loại, high value, high exposure, can onboard; tổng toàn bộ tenant ở đầu trang | https://learn.microsoft.com/en-us/defender-xdr/media/mto-tenant-devices/devices-tenant-view.png | https://learn.microsoft.com/en-us/defender-xdr/mto-tenant-devices | 200, image/png (2026-11-03) |
| Microsoft Defender XDR | Multitenant – Device inventory gộp | Inventory gộp mọi tenant, có cột Tenant name, lọc theo risk, criticality, sensor health | https://learn.microsoft.com/en-us/defender-xdr/media/mto-tenant-devices/devices-device-inventory.png | https://learn.microsoft.com/en-us/defender-xdr/mto-tenant-devices | 200, image/png (2026-11-03) |
| Microsoft Sentinel | Data collection health workbook – Overview | Volume, EPS, thời điểm nhận log cuối theo nguồn | https://learn.microsoft.com/en-us/azure/sentinel/media/monitor-data-connector-health/data-health-workbook-1.png | https://learn.microsoft.com/en-us/azure/sentinel/monitor-data-connector-health | 200, image/png (2026-11-03) |
| Microsoft Sentinel | Data collection health workbook – Anomalies | Bất thường thu thập theo table và data source | https://learn.microsoft.com/en-us/azure/sentinel/media/monitor-data-connector-health/data-health-workbook-2.png | https://learn.microsoft.com/en-us/azure/sentinel/monitor-data-connector-health | 200, image/png (2026-11-03) |
| Microsoft Sentinel | Data collection health workbook – Agent info | Thông tin và trạng thái agent gửi log | https://learn.microsoft.com/en-us/azure/sentinel/media/monitor-data-connector-health/data-health-workbook-3.png | https://learn.microsoft.com/en-us/azure/sentinel/monitor-data-connector-health | 200, image/png (2026-11-03) |

Ghi chú: ảnh `devices-choose-device.png` (Defender MTO) trả về `text/html` nên bị loại. Trang silent-host monitoring của Google SecOps không có ảnh. Chưa tìm được ảnh chính thức về QRadar domain hay XSIAM tenant management.

## Truy vấn đã chạy
- Splunk risk-based alerting reduce alert volume risk modifier asset priority risk incident rule (standard)
- Elastic Security asset criticality risk score multiplier modifier (standard)
- QRadar domain segmentation overlapping IP addresses domain-aware asset model (standard)
- risk-based alerting case study alert reduction percent Splunk RBA customer (standard)
- Google SecOps "silent" hosts log ingestion monitoring asset stopped sending logs (standard)
- CISA "Best practices for event logging and threat detection" asset inventory log sources priority (standard)
- Google SecOps context-aware analytics entity context priority risk score detection rule (standard)
- Microsoft Defender XDR asset criticality incident prioritization critical assets incident queue (standard)
- Splunk Enterprise Security asset and identity framework priority urgency matrix notable event (standard)
- Splunk ES risk factor editor multiply risk score asset priority critical risk factor (standard)
- Google SecOps data RBAC scopes labels namespace multi-tenant MSSP (standard)
- Microsoft Defender multitenant management device inventory across tenants MSSP (standard)
- Cortex XSIAM multi-tenant managed security parent child tenant asset inventory (standard)
- Wazuh multi-tenancy agent groups indexer security roles tenants MSSP (standard)
- Microsoft Sentinel data connector health monitoring SentinelHealth table workspace manager multiple workspaces MSSP Lighthouse (standard)
- QRadar domain-aware assets network hierarchy per domain asset profile domain (standard)
- NIST SP 800-92r1 log management planning inventory log sources draft 2023 (standard)
- CIS Controls v8.1 safeguard 8.2 collect audit logs 1.1 detailed enterprise asset inventory 1.2 unauthorized assets (standard)
- detection engineering asset context suppress vulnerability scanner false positives allowlist domain controllers jump hosts tuning blog (standard)
- Splunk Enterprise Security multi-tenant MSSP assets identities per tenant lookup "tenant" field (standard)
