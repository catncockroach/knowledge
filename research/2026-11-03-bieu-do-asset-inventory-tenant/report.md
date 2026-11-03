---
title: Biểu đồ và graph cho quản lý một asset, inventory một tenant và tổng quan MSSP trên dữ liệu OCSF 1.9.0
date: 2026-11-03
question: Các vendor security dùng những biểu đồ, graph và widget nào ở trang một asset/user và ở dashboard inventory của một tenant (hoặc MSSP nhiều tenant), mỗi biểu đồ trả lời câu hỏi vận hành gì, và nên chọn bộ biểu đồ nào cho sản phẩm quản lý tài sản SOC đa tenant trên OCSF v1.9.0?
tags: [asset-management, dashboard, data-visualization, soc, ocsf, multi-tenant]
---

# Risk trend bấm được và coverage theo nguồn là lõi biểu đồ tài sản

> **Câu hỏi:** Nên dùng biểu đồ/graph nào khi quản lý một asset, khi quản lý toàn bộ inventory của một tenant, và khi MSSP nhìn nhiều tenant; dữ liệu OCSF 1.9.0 nào nuôi từng biểu đồ? · **Ngày:** 2026-11-03 · **Phạm vi:** Microsoft Defender XDR/Exposure Management/Sentinel, Splunk ES 8.5–8.6, Elastic Security, Google SecOps, Cortex XDR/XSIAM, Exabeam, Axonius, runZero, Tenable, Wazuh, CrowdStrike, Trend Vision One; CIS CAS Control 1/8, CISA CDM AWARE, CISA OT Asset Inventory 2025, NIST SP 800-55 (2024); schema OCSF tag 1.9.0. Bố cục trang profile, hợp nhất định danh và provenance đã có ở `research/2026-11-03-asset-profile-vendor-giao-dien-soc/report.md`; báo cáo này chỉ bàn biểu đồ. · **Kiểm chứng:** 80 khẳng định đã đối chiếu nguồn, 12 đã sửa

## Tóm tắt

Ở cấp một asset, bộ biểu đồ đáng làm là **đường risk score theo thời gian có điểm bấm được để lọc ra các finding đã góp điểm**, kèm bar "nguồn đóng góp điểm", breakdown severity/MITRE dùng làm bộ lọc cho cả trang, timeline hai lớp (dải tổng quan có brush rồi bảng hoặc swim lane chi tiết), và graph quan hệ chỉ vẽ quanh asset trong 1–2 bước. Ở cấp inventory tenant, vendor hội tụ về **hàng KPI tile luôn có ngữ cảnh (delta so với kỳ trước, sparkline hoặc mục tiêu)**, phân bố dạng donut/bar mà segment nào cũng bấm ra danh sách asset đã lọc, bar "nguồn nào thấy bao nhiêu asset, còn bao nhiêu unique sau hợp nhất", biểu đồ độ phủ agent và asset mới theo ngày; còn sức khoẻ nguồn dữ liệu được tách thành dashboard riêng. Ở cấp MSSP, vendor mới dừng ở **bảng tenant × vài số đếm có hàng tổng ở trên** (Microsoft), chưa ai làm heatmap tenant × KPI. Khung lý thuyết cho cả ba cấp đến từ NIST SP 800-55 (mỗi số đo cần mục tiêu, tần suất, nguồn dữ liệu, định dạng báo cáo và ngữ cảnh hành động) và CIS CAS (công thức tỉ lệ accuracy/coverage cùng ngưỡng thời gian pass/fail cho Control 1 và 8). Biểu đồ dựa trên sự kiện lấy thẳng được từ OCSF 1.9.0; biểu đồ về trạng thái tài sản theo thời gian (đếm asset, new/stale/silent, chồng lấn nguồn, % chưa phân loại, risk tổng hợp) cần kho entity tự xây. Mức chắc chắn **cao** với các mẫu biểu đồ của Microsoft, Cortex, Google, Exabeam, Elastic, Axonius, runZero, Splunk, Tenable (docs chính thức có ảnh); **thấp** với CrowdStrike, Trend và Armis, vì docs khoá hoặc render bằng JS.

**Điểm chính**
- Risk trend là "xương sống" của trang asset/user ở Cortex, Microsoft, Exabeam, Splunk và Elastic; ba chi tiết lặp lại là điểm bấm được để lọc finding, tín hiệu khối lượng chồng lên đường (bong bóng, counter) và mốc tham chiếu (peer cùng role, ngưỡng nét đứt) [1][2][3][4].
- Drill-down từ segment sang danh sách asset lọc đúng truy vấn của segment là chuẩn chung: runZero cho bấm mọi segment trừ biểu đồ timeline, Axonius ghép base query với query của segment, Microsoft cho bấm donut để sang Devices list [5][6][7].
- KPI tile gần như không bao giờ là số trần: Tenable có "Sequential Period Comparison", Microsoft có trend 14 ngày, target score và lịch sử kèm tới **100 asset thay đổi** [8][9].
- Coverage được vẽ bằng bar xếp hạng nguồn kèm tổng unique (Axonius: **19.643** lượt thấy so với **4.787** device unique) và Venn tối đa 3 tập; không vendor nào trong mẫu dùng Sankey hay treemap [10][11].
- KPI chuẩn cho tile và trend: CIS 1.1 Accuracy = M3/M2, 1.3 Asset Discovery Coverage = M1/M6 với ngưỡng discovery **24 giờ**, 8.9 Log Aggregating = asset có log tập trung / asset có khả năng log; CDM AWARE coi phần cứng chưa gán owner là một thành phần điểm [12][13][14].
- Chưa vendor nào làm sparkline telemetry theo từng nguồn trên trang asset, cũng chưa ai có heatmap tenant × KPI cho MSSP; cả hai là cơ hội sản phẩm.

## Cấp một asset: risk trend có drill-down là xương sống, graph chỉ vẽ quanh asset

Trang một asset hay một user ở các vendor hội tụ về khoảng tám loại hình trực quan: đường risk score theo thời gian, bar hoặc bảng nguồn đóng góp điểm, breakdown theo severity và MITRE, timeline mật độ sự kiện, heatmap giờ hoạt động, prevalence graph, graph quan hệ/process/causality, và graph attack path. **Nhận định:** mỗi loại trả lời một câu hỏi khác nhau của analyst, nên điểm thiết kế quan trọng không phải là có đủ tám loại mà là mỗi loại nối được sang danh sách bằng chứng cụ thể.

### Risk trend: điểm bấm được, khối lượng chồng lên và mốc tham chiếu

Cortex XSIAM làm đầy đủ nhất. Widget **Risk Score Trend** trên Host Risk View vẽ đường điểm host, tính từ các case gắn với host; **bong bóng** trên đường cho biết số issue và insight trong ngày, bóng càng to càng nhiều issue. Bấm một ngày thì widget Cases chỉ còn những case đã góp điểm hôm đó [1]. Nút "Compare To" thêm một **đường nét đứt là điểm trung bình của các host cùng asset role** trong cùng kỳ, hover vào để xem breakdown theo endpoint; User Risk View có cơ chế y hệt [1][15]. Exabeam User Risk Trend có trục y là điểm trên thang 100, khung 1 tuần, 1 tháng, 3 tháng hoặc 1 năm; ở khung ngắn mỗi điểm là một session, ở khung dài mỗi điểm là session điểm cao nhất của tuần. Hàng counter phía trên (trong ảnh: Rules, Events, Alerts, Accounts, Assets, Zones, Score) đổi theo feed đang chọn, và bấm điểm thì mở Risk Reasons [2]. Microsoft Defender XDR dùng line "Risk Trend" có khung thời gian chỉnh được trên trang identity, kèm link sang timeline [16]. Splunk ES 8.5 vẽ intermediate findings với "time on the x-axis and the risk score on the y-axis", chọn một finding trên timeline thì dòng tương ứng ở bảng bên dưới được highlight [3]. Elastic (Stack 9.5+) có risk score history chart trong flyout entity với **đường nét đứt đánh dấu ngưỡng Low/Moderate/High/Critical**; mỗi điểm là điểm cao nhất của kỳ, bấm một điểm để xem lại điểm cũ [4].

![Exabeam User Risk Trend](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-4a912150-18a6-93cf-0ed4-0c7b6d454896.png)
*Exabeam – User Risk Trend (ảnh dữ liệu 2019): đường điểm 0–100 theo ngày, điểm đang chọn khoanh đỏ, cột Feeds bên trái, hàng counter Rules/Events/Alerts/Accounts/Assets/Zones/Score phía trên. Nguồn: [2]*

**Nhận định:** sản phẩm nên làm đủ cả ba chi tiết: (a) bấm một điểm thì lọc danh sách finding đã góp điểm ngày đó; (b) có tín hiệu khối lượng (bong bóng số finding) để phân biệt "một finding nặng" với "nhiều finding nhẹ"; (c) có mốc tham chiếu, gồm band ngưỡng mức rủi ro ngay ở MVP, rồi đường peer cùng role/loại asset ở bản sau, vì tính peer đòi hỏi kho entity đã có role ổn định.

### Nguồn đóng góp điểm và breakdown severity/MITRE đóng vai trò bộ lọc cả trang

Câu hỏi tiếp theo sau "điểm có tăng không" là "vì sao". Elastic trả lời bằng bảng **Top risk score contributors** trên tab Host risk: mỗi dòng là một alert góp điểm với timestamp, rule, severity, risk score và reason [17]. Microsoft có **Likelihood of Compromise Details**, "a bar chart that shows alert distribution across MITRE ATT&CK categories", kèm bảng alert lọc được theo status và kill chain stage; likelihood và impact là hai chỉ số tách riêng [16]. Cortex XSIAM đặt một loạt widget breakdown cạnh risk trend: **Case Breakdown** theo severity (bấm một severity thì cả trang lọc theo mức đó), **CVEs Breakdown by severity**, **MITRE ATT&CK Matrix Breakdown**, Issues & Insights gom theo tactic, và counter Failed Logins có link "View in XQL" [1].

![Elastic Top risk score contributors](https://www.elastic.co/docs/solutions/images/security-host-details-hr-tab.png)
*Elastic Security – Top risk score contributors: tab Host risk của host details liệt kê các alert góp điểm với timestamp, rule, severity, risk score và reason. Nguồn: [17]*

**Nhận định:** breakdown ở cấp asset không chỉ để xem mà là **bộ lọc tương tác**: bấm một segment thì timeline, bảng finding và graph cùng lọc theo. Với dữ liệu OCSF, nguồn đóng góp nên chia theo bốn nhóm có class riêng: alert (Detection Finding 2004), lỗ hổng (Vulnerability Finding 2002), cấu hình sai (Compliance Finding 2003) và trạng thái bảo vệ (Device Config State Change 5019); một stacked bar ngang bốn nhóm này dễ đọc hơn bảng thuần khi số finding lớn.

### Timeline hai lớp: dải tổng quan có brush, rồi bảng hoặc swim lane chi tiết

Defender XDR đặt trên tab Timeline của device **một dải thời gian nhiều tháng có chấm alert tô theo severity** và một vùng brush chọn khung (mặc định 1 tuần), bên dưới là bảng sự kiện gắn tag MITRE technique [18]. Google SecOps làm tương tự ở IP view với dải overview ngắn để brush [19]. Exabeam có **Daily Timeline** 24 giờ theo feed, gộp các sự kiện không điểm cùng loại thành một dòng ("3x Remote access") [2]. Sentinel entity page đặt timeline alert/bookmark/anomaly/activity ở cột giữa [20]. Swim lane heat map của Splunk Asset Investigator đã mô tả trong báo cáo trước.

![Defender XDR device timeline](https://learn.microsoft.com/en-us/defender-xdr/media/entity-page-device/entity-device-timeline-tab.png)
*Microsoft Defender XDR – Device timeline: dải tổng quan Oct 2023–Mar 2024 có chấm alert đỏ/cam theo severity, vùng brush một tuần, bảng sự kiện bên dưới gắn tag MITRE technique. Nguồn: [18]*

![Exabeam Daily Timeline](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-4ab92b0e-99f0-eb37-1552-67c0764bd73f.jpg)
*Exabeam – Daily Timeline: dòng thời gian 24 giờ của một user chia theo feed (mô tả theo tên ảnh và đoạn văn quanh ảnh). Nguồn: [2]*

Heatmap giờ hoạt động thuộc cùng nhóm câu hỏi "lúc nào". Cortex User Risk View có **Issues & Insights Heatmap** theo giờ, căn theo múi giờ [15]; Google SecOps User view có heatmap theo giờ với tuỳ chỉnh dịch trục x [21]; Exabeam tô lịch session theo ngày (đen: không hoạt động, xanh: bình thường, đỏ: rủi ro cao) [2]. Docs của vendor nào cũng không nói rõ lưới là đúng 7×24. **Nhận định:** timeline dạng "overview + detail" là MVP vì asset nào cũng có dữ liệu nhiều tháng; heatmap 7×24 có ích nhất cho user và server có lịch cố định, nên để sau.

### Prevalence là cách giảm nhiễu rẻ nhất, nhưng chỉ Google đặt nó làm biểu đồ trung tâm

Google SecOps Asset view vẽ **prevalence graph**: trục y là số asset trong tổ chức đã kết nối tới một domain, nên domain hiếm nằm trên cao, domain phổ biến như google.com nằm dưới và thường không cần điều tra. Vòng xám là lần kết nối đầu tiên, tam giác đỏ là alert; prevalence tính trên 7 ngày, cửa sổ mặc định của view là 2 giờ, tối đa 100 nghìn sự kiện [22][23]. IP view thêm cột prevalence theo ngày qua nhiều tháng cùng thẻ threat intel [19].

![Google SecOps prevalence graph](https://docs.cloud.google.com/chronicle/images/qs/qs-alert-asset-view.png)
*Google SecOps – Prevalence graph trong Asset view: trục y là prevalence, chấm xám là domain lần đầu hoặc lặp lại, marker đỏ là alert "Suspicious download by Office Application"; trái là timeline sự kiện, phải là Procedural Filtering, dưới là counter Low prevalence domains. Nguồn: [23]*

![Google SecOps IP view](https://docs.cloud.google.com/chronicle/images/ip-address-view.png)
*Google SecOps – IP Address view: cột prevalence theo ngày qua nhiều tháng, dải overview để brush, thẻ ET Intelligence và VT Context. Nguồn: [19]*

**Nhận định:** câu hỏi "bao nhiêu asset khác trong tenant cũng làm vậy" cắt nhiễu hiệu quả mà chỉ cần đếm số asset theo đích kết nối hoặc domain trong 7 ngày. Nó đòi hỏi tính trước trên toàn tenant, nên xếp sau MVP, nhưng nên có sớm dưới dạng cột "prevalence" trong bảng kết nối trước khi làm thành graph.

### Graph chia hai loại: graph sự kiện cho điều tra, graph cấu hình/quyền cho exposure

Loại thứ nhất dựng từ sự kiện trong một khoảng thời gian. Cortex **Causality view** hình hoá một causality instance gồm node process, event và issue; kéo, zoom được, chuột phải để thêm nhánh parent/child ("Showing Partial Causality") [24]. Elastic có **Visual event analyzer** (process tree từ một alert) và **Session view** (cây lệnh terminal Linux theo session) [25][26]. Sentinel investigation graph vẽ entity trích từ raw data và mở rộng bằng exploration query, nhưng docs thừa nhận "you end up having to switch contexts a great deal more" [27].

![Cortex causality view](https://2127116976-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FcyIgISZgANJYkmLlnwdK%2Fuploads%2Fgit-blob-91c6b9d3ae540a2997e7673fed891d68c4460ff1%2F5bdf1c27f7c20f5d7a1288504bc054d6fce895a8dbec1a4ec84a7e015793c414.gif?alt=media)
*Cortex XDR/XSIAM – Causality view: ảnh động minh hoạ chuỗi causality instance gồm node process, event và issue (mô tả theo vị trí ảnh trên trang). Nguồn: [24]*

![Elastic visual event analyzer](https://www.elastic.co/docs/solutions/images/security-visual-event-analyzer.png)
*Elastic Security – Visual event analyzer: graph process/event dựng từ một alert (mô tả theo alt text). Nguồn: [25]*

Loại thứ hai dựng từ quan hệ bền vững: thành viên nhóm, quyền, kết nối đã biết. Defender XDR **Identity Explorer** (preview, cần license Sentinel Data Lake) khởi tạo graph từ identity hiện tại; node nhóm hiện số đếm như Group (20), Subscription (2), và có scenario dựng sẵn để tìm lateral movement [16]. Axonius **Asset Graph** gom node cùng loại thành một bong bóng có số đếm (vd Devices 20.4K), chỉ cho ungroup khi nhóm dưới 500 node, mỗi loại asset là một layer bật/tắt được, và có danh sách Investigation Steps để quay lui [28][29]. Trend Vision One đổi tên graph trong profile device/account/domain/IP thành **Asset Risk Graph** từ tháng 2/2024 (chỉ đọc được qua snippet) [30]. Elastic có graph preview quanh entity trong 30 ngày (trạng thái Preview từ Stack 9.4), mở rộng ra graph tương tác lọc bằng KQL [4].

![Defender Identity Explorer](https://learn.microsoft.com/en-us/defender-xdr/media/hunting-graph-identity/hunting-graph.png)
*Microsoft Defender XDR – Identity Explorer: scenario "Entity relationship map" đặt user ở tâm, nối tới Group (20), Subscription (2), một tenant ngoài và một device; edge có icon loại quan hệ. Nguồn: [16]*

![Axonius Asset Graph](https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/AssetGraph-DeviceDetailsIndv-1.png)
*Axonius – Asset Graph: node Devices gom nhóm có bong bóng 20.4K, menu View details/Filter/Preview/Ungroup/Enforce/Segment by/Explore connections, drawer Device Details bên phải. Nguồn: [28]*

Attack path là biến thể của loại thứ hai, hướng tới exposure. Microsoft Security Exposure Management vẽ **attack path graph** từ enterprise exposure graph; hover vào node hoặc connector để biết path được dựng thế nào. Tab **Choke points** liệt kê node nơi nhiều path hội tụ, và "View blast radius" cho "visually explore the highest-risk paths from a choke point" [31].

![Exposure Management attack path](https://learn.microsoft.com/en-us/security-exposure-management/media/review-attack-paths/attack-path-graph-details.png)
*Microsoft Security Exposure Management – Attack path graph: chuỗi VM lộ ra Internet → secret → database nối bằng connector có icon, nút "View in map", panel chi tiết node bên phải. Nguồn: [31]*

![Exposure Management choke points](https://learn.microsoft.com/en-us/security-exposure-management/media/review-attack-paths/choke%20points%20and%20blast%20radius.png)
*Microsoft Security Exposure Management – Choke points: bảng node (service principal, repo, pipeline) với Risk level, Type, Critical targets, Attack paths và nút "View blast radius". Nguồn: [31]*

**Nhận định:** hai loại graph cần hai nguồn dữ liệu khác nhau. Graph sự kiện dựng được ngay từ Process Activity 1007, Authentication 3002, Network Activity 4001; graph quan hệ bền vững cần cạnh user–device, group, quyền được lưu trong kho entity, hoặc lấy từ object `graph` của OCSF khi nguồn có gửi (`resource_details.resource_relationship`, `finding_info.attack_graph`) [32]. Với một sản phẩm SOC dựng từ log, graph sự kiện quanh asset (ego-graph) đến trước; attack path chỉ khả thi khi có dữ liệu quyền và cấu hình.

### Lỗ hổng và lịch sử thuộc tính: breakdown severity và bảng thay đổi có đánh dấu

Cortex có **CVEs Breakdown by severity** như một summary chart để thấy nhu cầu vá gấp [1]; Defender có tab Discovered vulnerabilities và Inventories trên device page [18]. Splunk ES 8.6 hiện **lịch sử bản ghi asset theo ngày** (IP, MAC, OS version, User ID), ô nào thay đổi được đánh dấu "Record changed" [33], một dạng trực quan cho câu hỏi "thuộc tính này đổi khi nào".

![Defender discovered vulnerabilities](https://learn.microsoft.com/en-us/defender-xdr/media/entity-page-device/entity-device-vulnerabilities-tab.png)
*Microsoft Defender XDR – Discovered vulnerabilities: tab lỗ hổng trên device profile (mô tả theo alt text). Nguồn: [18]*

![Splunk entity record change history](https://www.splunk.com/content/dam/splunk-blogs/images/media_10d8ff50825a5063fad076c825bd8c196c696750b.png)
*Splunk ES 8.6 – Entity record change history: bảng lịch sử bản ghi asset theo ngày (IP, MAC, OS version, User ID), ô thay đổi có vạch tím "Record changed". Nguồn: [33]*

**Nhận định:** với OCSF, breakdown lỗ hổng nên là stacked bar severity × (exploit có sẵn / có bản vá) cộng histogram tuổi lỗ hổng, vì Vulnerability Finding 2002 có sẵn `is_exploit_available`, `is_fix_available`, `first_seen_time`, `cve.epss.score` [32]. Như vậy một bar trả lời luôn "vá cái nào trước".

### Chưa vendor nào vẽ telemetry theo từng nguồn trên trang asset

Trong các trang device/host đã đọc, không vendor nào có sparkline lượng log theo từng nguồn trên trang một asset. Phần gần nhất là provenance nguồn dạng danh sách (Axonius adapter connections, đã có ở báo cáo trước). Google Health Hub có line theo ngày và phát hiện bất thường khối lượng, nhưng ở cấp nguồn dữ liệu chứ không ở cấp asset [34]. **Nhận định:** đây là cơ hội rõ nhất ở cấp asset cho một sản phẩm SOC quản lý log tập trung. Một hàng sparkline 14 ngày cho mỗi nguồn (EDR, Windows Security, Sysmon, firewall, scanner) kèm "last seen" và cờ im lặng trả lời ngay câu "không có alert vì an toàn hay vì không có dữ liệu". Dữ liệu có sẵn: `count(*)` theo `metadata.product.name` hoặc `metadata.log_source` theo ngày cho asset, và `max(time)` theo nguồn [32].

### Bảng (a): bộ biểu đồ đề xuất cho trang một asset

**Nhận định:** cột "Ưu tiên" và "Người xem" là đề xuất; các cột vendor và field là dữ kiện đã dẫn ở trên. Ký hiệu dữ liệu: **E** lấy thẳng từ event OCSF; **S** cần kho entity tự xây; **E+S** event OCSF đã gắn asset_id từ kho.

| Biểu đồ | Câu hỏi vận hành | Loại chart & tương tác | Vendor tham khảo | Dữ liệu OCSF 1.9.0 / kho entity | Ưu tiên | Người xem |
|---|---|---|---|---|---|---|
| Risk score trend | Rủi ro tăng từ khi nào, có vượt ngưỡng không | Line + bong bóng số finding + band ngưỡng; bấm điểm → lọc finding ngày đó; đường peer cùng role ở bản sau | Cortex, Exabeam, Microsoft, Splunk, Elastic [1][2][16][3][4] | 2004 `risk_score`, `risk_level_id`, `time`; `device.risk_score`. Điểm vendor là "as reported by the event source" nên điểm tổng hợp và lịch sử điểm tính trong kho (S) [32] | MVP (peer: sau) | Analyst |
| Nguồn đóng góp điểm | Điểm cao do alert, CVE, cấu hình hay bảo vệ | Stacked bar ngang 4 nhóm hoặc bảng top contributors; bấm nhóm → lọc trang | Elastic, Microsoft LoC bar [17][16] | 2004 `finding_info.analytic`, `metadata.product.name`; 2002 `cve.cvss[].base_score`, `cve.epss.score`; 2003 `compliance.status_id`=3; 5019 `security_states[].state_id` (S, công thức tự định) | MVP | Analyst |
| Breakdown severity/MITRE | Đang có bao nhiêu case/alert mức nào, tactic nào | Bar/chip severity, ma trận MITRE; bấm → lọc toàn trang | Cortex, Microsoft [1][16] | 2004 `severity_id`, `status_id`, `finding_info.attacks`; 2005 `severity_id`, `priority_id`, `status_id`, `attacks` (2005 không có `finding_info`) (E+S) | MVP | Analyst |
| Timeline overview + detail | Chuyện gì xảy ra, lúc nào | Dải nhiều tháng có chấm finding + brush; bảng hoặc swim lane theo class bên dưới | Microsoft, Google, Exabeam, Sentinel [18][19][2][20] | `time`, `class_uid`, `activity_id`, `count`; 2004 `finding_info.first_seen_time`/`last_seen_time`, 2005 `finding_info_list[]` (E+S) | MVP | Analyst |
| Telemetry theo nguồn | Nguồn nào còn gửi log, nguồn nào im | Hàng sparkline 14 ngày mỗi nguồn + last seen + cờ silent; bấm → truy vấn log nguồn đó | Không vendor nào (cơ hội) | `count(*)` theo `metadata.product.name`/`log_source`, `max(time)` theo nguồn (E); trạng thái silent và ngưỡng theo nguồn (S) | MVP | Analyst, SOC lead |
| Chip coverage bảo vệ | Asset có đủ EDR, log forwarder, VM agent không | Chip trạng thái từng lớp, đỏ khi thiếu hoặc tắt | Axonius coverage status (ở cấp tenant) [35] | `agent_list[].type_id` (1 EDR, 5 Vulnerability Mgmt, 6 Log Forwarding, 7 MDM), `device.is_managed`, 5019 `security_states[].state_id` 4 Protection off, 11 Not installed (không phải `state_id` cấp class, vốn chỉ có 0–2/99) (E+S) | MVP | Analyst, SOC lead |
| Vuln breakdown | CVE nào cần vá trước | Stacked bar severity × exploit/fix; histogram tuổi; bấm → danh sách CVE | Cortex, Microsoft [1][18] | 2002 `vulnerabilities[].severity`, `cve.cvss[]`, `cve.epss`, `is_exploit_available`, `is_fix_available`, `first_seen_time`; loại `status_id`=4 Resolved (E+S) | MVP | Analyst, đội vá |
| Activity heatmap | Hoạt động bất thường giờ nào | Heatmap giờ × ngày, tô theo số event hoặc finding | Cortex, Google, Exabeam [15][21][2] | `time`, `count` của 3002, 1007, 4001 (`traffic.bytes`) lọc theo `device.uid` (E+S) | Sau | Analyst |
| Prevalence | Asset đã nói chuyện với thứ gì hiếm trong tenant | Scatter thời gian × số asset cùng kết nối; marker alert; lọc theo event type | Google [22][23] | 4001 `dst_endpoint`, domain; đếm asset_id trong 7 ngày (E+S) | Sau (cột prevalence trước) | Analyst, hunter |
| Ego-graph quan hệ | Ai đăng nhập, nói chuyện với đâu, chạy gì | Graph 1–2 hop, cửa sổ thời gian, gom node cùng loại, layer bật/tắt | Microsoft, Axonius, Elastic, Sentinel [16][28][4][27] | 3002 `user`, `dst_endpoint`, `logon_type_id`; 4001 `src_endpoint`/`dst_endpoint`, `initiator_id`; 1007 `process`; cạnh bền vững user–device lưu trong kho (E+S) | Sau | Analyst |
| Process tree / causality | Chuỗi process nào dẫn tới alert | Tree/graph từ một alert, mở rộng parent/child | Cortex, Elastic [24][25] | 1007 `process`, `actor.user` (E+S) | Sau (phụ thuộc EDR) | Analyst |
| Attack path / blast radius | Từ asset này kẻ tấn công đi tới đâu | Graph path tới critical target, choke point | Microsoft, Trend [31][30] | `finding_info.attack_graph`, `resource_details.resource_relationship` (object `graph`) khi nguồn có gửi; còn lại S | Sau | Analyst, đội exposure |
| Lịch sử thuộc tính | IP/OS/owner đổi khi nào, từ nguồn nào | Bảng theo ngày có ô đánh dấu thay đổi | Splunk ES 8.6 [33] | 5001 `device.*` + `metadata.product` + `time`; provenance và hiệu lực lưu trong kho (S) | Sau | Analyst |

### Wireframe vùng trực quan của trang asset

Phần header, tab và sidebar định danh theo wireframe của báo cáo trước; khung dưới chỉ là vùng biểu đồ.

```
┌ WS-FIN-023 · Win 11 · Criticality HIGH · Risk 72 ▲18/7d · Exposure MED ─────────────────┐
├──────────────────────────────────────────────┬──────────────────────────────────────────┤
│ RISK TREND 30d   ── điểm   ┄┄ peer cùng role │ NGUỒN ĐÓNG GÓP ĐIỂM  (bấm → lọc trang)   │
│ 100┤                                         │ Alert (2004)     ████████████ 41         │
│  75┤- - - - - - - - - - - - ngưỡng HIGH - -  │ CVE (2002)       ███████ 22              │
│  50┤        (3)●───●(5)                      │ Cấu hình (2003)  ███ 9                   │
│  25┤ ●──●──●/       \●                       │ Bảo vệ (5019)    ██ 6                    │
│    ┤┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄            │ SEVERITY  [Crit 2] [High 5] [Med 9]      │
│    └─ 10-04 ───── 10-19 ───── 11-03          │ MITRE     [TA0006 3] [TA0008 2] ...      │
│   (n) = số finding trong ngày; bấm ● → lọc   │                                          │
├──────────────────────────────────────────────┴──────────────────────────────────────────┤
│ TIMELINE 6 tháng  ·  ·    ▲  ·  ·▲▲   ·   [===== brush 7 ngày =====]                     │
│  Auth 3002     ▮▮  ▮ ▮▮▮▮      ▮▮      ▮▮▮                                               │
│  Process 1007  ▮ ▮▮▮▮▮▮▮▮  ▮▮▮▮▮▮                                                        │
│  Network 4001  ▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮                                                     │
│  Finding       ▲        ▲▲                        (bảng sự kiện chi tiết bên dưới)       │
├──────────────────────────────┬─────────────────────────────────┬────────────────────────┤
│ EGO-GRAPH 1 hop · 24h        │ TELEMETRY THEO NGUỒN 14d        │ LỖ HỔNG                │
│  (tran.b)──(WS-FIN-023)      │ EDR      ▃▄▃▄▄▃▄▄▃▄   2m   ok   │ Crit ██ 3 (1 exploit)  │
│               │    ╲         │ WinSec   ▄▄▃▄▄▄▃▄▄▄   5m   ok   │ High ██████ 8          │
│          (proc ×5) (IP ×12)  │ Sysmon   ▄▄▃▃▂▁____   3d SILENT │ >30 ngày: 6            │
│  [mở rộng] [lọc quan hệ]     │ Scanner  ·    ·       9d  trễ   │ có bản vá: 7/11        │
│                              │ BẢO VỆ  EDR ✓  Log ✓  VM ✗      │                        │
└──────────────────────────────┴─────────────────────────────────┴────────────────────────┘
```

## Cấp inventory tenant: KPI có ngữ cảnh, phân bố bấm ra danh sách, coverage theo nguồn

Dashboard inventory của các vendor dùng chung một khung: hàng KPI tile ở trên, phân bố và xu hướng ở giữa, bảng xếp hạng ở dưới, đúng bố cục Splunk khuyên (trên cùng là chỉ số chính, giữa là xu hướng hoặc phân rã theo nhóm, dưới là dữ liệu chi tiết để điều tra) [36]. Khác biệt nằm ở mức độ: docs Microsoft Defender device inventory không mô tả biểu đồ nào, chỉ có **count pill** ở đầu mỗi tab (total, critical assets, high risk, high exposure, not onboarded, newly discovered) và vài card như "Classify critical assets" [37]; Elastic Entity Analytics gần như chỉ có KPI và bảng top risk score [38]; còn runZero, Axonius, Splunk và Tenable dựng dashboard nhiều loại chart.

### Hàng KPI tile luôn kèm delta, sparkline hoặc mục tiêu

Tenable Operational Dashboard gắn vào mỗi tile (CES, Critical Detections, Assets With Critical Detections) một **"Sequential Period Comparison"** theo %, kèm nhãn "Last Data Update"; dữ liệu làm mới 24 giờ một lần, giữ 90 ngày và chỉ tính asset có license [8]. Microsoft Exposure Management Overview có 5 tile Domain initiative (Code, Endpoint, Cloud, Identity, SaaS), mỗi tile là % so với target score kèm sparkline và delta [39]. Splunk ES 8.6 mở đầu Entity Discovery Insights bằng "4,355 Discovered assets" và "6 Discovered asset types" [33].

![Tenable Operational Dashboard](https://docs.tenable.com/exposure-management/Content/Resources/Images/Local/exposure-management/dashboard-details.png)
*Tenable Exposure Management – Operational Dashboard: tile CES 533, Critical Detections 1.426, Assets With Critical Detections 103, mỗi tile kèm Sequential Period Comparison %; bảng Top 5, bar Asset Exposure Score theo category, nhãn Last Data Update. Nguồn: [8]*

![Exposure Management overview](https://learn.microsoft.com/en-us/security-exposure-management/media/get-started-exposure-management/exposure-management-overview.png)
*Microsoft Security Exposure Management – Overview: card Resolve now (Patch/Mitigate/Fix) có số recommendation, bảng Internet-exposed resources, 5 tile Domain initiatives với % so với target, sparkline và delta. Nguồn: [39]*

**Nhận định:** sáu tile đáng đặt trên cùng cho SOC đa nguồn là: asset hợp nhất, asset mới 7 ngày, asset silent, asset không có EDR, % độ phủ EDR, và % chưa phân loại criticality. Tổng asset là tile kém hành động nhất, nhưng cần có vì nó là mẫu số cho các tỉ lệ khác.

### Phân bố theo loại/OS/criticality: donut hoặc bar bấm được, và mẫu "least seen"

Splunk dùng pie "Assets by type" [33]; Microsoft dùng donut "Device exposure distribution", docs ghi rõ "Select a section in the doughnut chart to go to the Devices list page" [7]; Axonius có Field Segmentation (pie hoặc histogram theo một field) và Adapter Segmentation (theo nguồn dữ liệu) [40]. runZero có nhóm "Most and least seen graphs" theo Asset types, Operating systems, Hardware, MAC vendors, ports, Products, Protocols, Risk, Criticality, Tags, **mỗi biểu đồ lật được giữa most seen và least seen** [5]. Wazuh 4.13 (2025-09-18) thêm dashboard IT Hygiene, chủ yếu là bảng Top 5 (OS families, packages, processes) và một stacked bar Package types [41][42].

![Splunk ES 8.6 Entity discovery insights](https://www.splunk.com/content/dam/splunk-blogs/images/media_163d82c78b9192b4325e24b26e6a06e7e828a320f.png)
*Splunk ES 8.6 – Entity discovery insights: KPI 4.355 asset và 6 loại, pie Assets by type, stacked bar New assets by type theo ngày, bubble map Asset locations, các bảng Asset subnets, Ephemeral assets và Discovery sources, nút View in Entity discovery inventory. Nguồn: [33]*

![Wazuh IT Hygiene dashboard](https://documentation.wazuh.com/current/_images/system-inventory-dashboard1.png)
*Wazuh – IT Hygiene dashboard: các bảng Top 5 (OS families, packages, processes, OS, host CPUs, endpoints by memory) và stacked bar ngang Package types. Nguồn: [41]*

**Nhận định:** "least seen" lật một biểu đồ phân bố vốn ít hành động thành công cụ săn shadow IT (OS lạ, MAC vendor lạ). Phân bố cơ cấu nên đặt ở tầng giữa, dùng bar ngang khi quá 6 nhóm, và luôn hiện rõ nhóm "Unknown/chưa phân loại" chứ không gộp vào "Other".

### Coverage theo nguồn: bar xếp hạng kèm tổng unique, Venn khi tối đa 3 tập

Câu hỏi "tôi có bao nhiêu thiết bị" được Axonius trả lời bằng **Device Discovery chart**: bar ngang xếp hạng adapter theo số device thấy được (top 20), kèm "Total Devices Seen" và "Total Unique Devices: The number of total unique devices after Axonius device correlation"; bấm một hàng thì mở trang Devices lọc theo adapter [10]. Splunk có bảng "Discovery sources" (vendor/nguồn × số asset) [33], runZero có bảng "Asset sources" [5]. Chồng lấn giữa các nguồn được vẽ bằng **Query Intersection**: pie hoặc bar cho tối đa 2 query giao, Venn tròn cho tối đa 3, Venn tam giác cho tối đa 6 (chỉ cho Axonius Identities); ví dụ có sẵn là "All devices" giao "Missing EDR" [11].

![Axonius Device Discovery chart](https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/DeviceDiscoveryChart_24.png)
*Axonius – Device Discovery chart: bar ngang xếp hạng adapter theo số device thấy được (ServiceNow 1.975…), Total Devices Seen 19.643 so với Total Unique 4.787 sau correlation. Nguồn: [10]*

![Axonius Venn chart](https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/img/Dashboards/VennChartPreviewExample.png)
*Axonius – Query Intersection dạng Venn: ví dụ Venn 3 vòng cho phần chồng lấn giữa các query (mô tả theo chú thích). Nguồn: [11]*

Độ phủ agent được Axonius tách thành dashboard riêng ba phần: Scope & Compliance (vd 500/1.000 device có CrowdStrike), Coverage Status (active, inactive, missing, headless), và Coverage Health Trends Over Time để thấy "spikes, or gradual degradation in coverage health" [35]. CrowdStrike Falcon Exposure Management có một **bar màu hồng đại diện cho mọi asset unmanaged**; bấm vào để drill-down rồi lọc theo phân loại asset [43].

![Axonius Agents Deployment Status](https://files.readme.io/9d03b26ed0a366aeb853129361808f49ab95cb85c0f37a2f670fae3c123698da-image.png)
*Axonius – Agents Deployment Status: bảng agent (Zoom, CrowdStrike, IGEL) với Configuration status, Active agents, Potential issues và nút Dashboard/View issues dẫn vào Agent Coverage dashboard. Nguồn: [35]*

**Nhận định:** con số 19.643 lượt thấy so với 4.787 device unique trong ảnh Axonius cho thấy vì sao biểu đồ coverage phải hiện cả "tổng lượt thấy" lẫn "unique sau hợp nhất": trong ví dụ đó, cộng thô các nguồn thổi phồng inventory khoảng 4 lần. Venn chỉ đọc được tới 3 tập; một SOC có 5–10 nguồn nên dùng UpSet hoặc ma trận nguồn × asset, còn MVP chỉ cần danh sách "asset chỉ một nguồn thấy" cùng stacked bar 100% độ phủ EDR/log theo criticality.

### Lifecycle new/stale/silent và asset mới theo ngày

runZero có widget "Asset trends: timeline of asset counts broken out by live, recent, and a couple of other states" [5]. Splunk vẽ **stacked bar "New assets by type" theo ngày**, tô màu theo loại, và bảng "Ephemeral assets" theo loại kèm % [33]. Axonius có Query Timeline và Multi-Line Timeline cho số asset khớp một query theo thời gian [40][44]. Microsoft có pill "newly discovered" [37].

![Axonius Query Timeline](https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/TimeLineChart.png)
*Axonius – Query Timeline: line số asset khớp một query theo thời gian (mô tả theo chú thích). Nguồn: [44]*

**Nhận định:** OCSF không có trạng thái lifecycle, nên các tile và trend new/stale/silent phải đọc từ snapshot đếm theo ngày trong kho entity. Cần tách "silent" (asset còn đó nhưng một nguồn ngừng gửi) khỏi "stale" (không nguồn nào thấy), vì trường hợp đầu thường là lỗi pipeline, đúng như Google cảnh báo feed có thể hiện Active trong khi thu thập đang hỏng [34].

### Exposure và top rủi ro: gauge, trend, donut và bảng xếp hạng có sparkline

Dashboard Defender Vulnerability Management có gauge "Endpoint exposure score" 0–100, line điểm theo thời gian, bảng Top vulnerable software có sparkline số device bị lộ, bar ngang Vulnerabilities insights (tổng/exploitable/critical/zero-day), donut Device exposure distribution và progress bar Top remediation activities; docs ghi "Devices that aren't active in the last 30 days aren't factored in" [7]. Elastic có bảng User/Host/Service Risk Scores top 5, bấm tên mở flyout, bấm số alert sang Alerts hoặc Timeline [38]. Wazuh có dashboard lỗ hổng theo severity, package và OS [45].

![Defender Vulnerability Management dashboard](https://learn.microsoft.com/en-us/defender/media/defender-vulnerability-management/new-overview.png)
*Microsoft Defender Vulnerability Management – Dashboard: gauge exposure score 23/100, line điểm theo thời gian, donut Device exposure distribution, bar ngang Vulnerabilities insights, progress bar remediation, bảng top exposed devices kèm criticality. Nguồn: [7]*

![Elastic host risk scores](https://www.elastic.co/docs/solutions/images/security-host-score-data.png)
*Elastic Security – Entity Analytics, Host risk scores: bảng top host theo risk score kèm alert count (mô tả theo chú thích). Nguồn: [38]*

![Wazuh vulnerabilities dashboard](https://documentation.wazuh.com/current/_images/vulnerabilities-inventory-dashboard1.png)
*Wazuh – Vulnerabilities inventory dashboard: lỗ hổng theo severity, package và OS (mô tả theo tên ảnh và ngữ cảnh). Nguồn: [45]*

**Nhận định:** không vendor nào trong mẫu vẽ sẵn heatmap severity × criticality, dù đây là câu hỏi ưu tiên vá cốt lõi ("lỗ hổng nặng nằm trên tài sản quan trọng nào"). Một lưới 4×4 (severity × criticality), mỗi ô là số asset và bấm ra danh sách, gọn hơn cả gauge lẫn donut.

### Sức khoẻ dữ liệu được tách thành dashboard riêng

Google SecOps **Health Hub** là mẫu rõ nhất: big number Healthy/Failed/Irregular cho source và parser, line "Data Source Health Overview" theo ngày, "Total Ingested Logs", "Failing Parser by Log Type", và bảng Health Status by Data Source. "Irregular" được định nghĩa là "unusual surges or drops in data volume or a significant change in error rates", phát hiện bằng thống kê "with a 15-day lookback period" [34].

![Google SecOps Health Hub](https://docs.cloud.google.com/static/chronicle/images/health-status-by-data-source-mu.png)
*Google SecOps – Health Hub, Health status by data source: bảng trạng thái nguồn Healthy/Irregular/Failed (mô tả theo tên ảnh và ngữ cảnh). Nguồn: [34]*

**Nhận định:** dashboard inventory chỉ đáng tin khi người xem biết dữ liệu nuôi nó tươi tới đâu. Nên có một dashboard data-health riêng (nguồn × trạng thái, độ trễ ingest, khối lượng theo ngày), còn trên dashboard inventory chỉ giữ một nhãn "dữ liệu cập nhật lúc… / N nguồn đang trễ", giống nhãn "Last Data Update" của Tenable [8].

### Bảng (b): bộ biểu đồ đề xuất cho dashboard inventory tenant

**Nhận định:** cột "Ưu tiên" và "Người xem" là đề xuất.

| Biểu đồ | Câu hỏi vận hành | Loại chart & tương tác | Vendor tham khảo | Dữ liệu OCSF 1.9.0 / kho entity | Ưu tiên | Người xem |
|---|---|---|---|---|---|---|
| Hàng KPI tile | Inventory hôm nay thế nào so với kỳ trước và mục tiêu | Số lớn + delta % + sparkline 14 ngày + đích; bấm → danh sách lọc | Tenable, Microsoft, Splunk [8][39][33] | Snapshot đếm theo ngày trong kho (S) | MVP | SOC lead, khách hàng tenant |
| Asset theo lifecycle | Inventory tăng/giảm, có đột biến không | Stacked area/line live–new–stale–silent | runZero, Axonius [5][44] | Snapshot kho; đầu vào 5001, 5003, 5023 và mọi event có `device` (S) | MVP | SOC lead |
| Asset mới theo ngày | Thứ gì vừa xuất hiện | Stacked bar theo ngày tô theo loại; bấm cột → danh sách | Splunk [33] | `first_seen` hợp nhất trong kho; `device.first_seen_time` theo nguồn (S) | MVP | Analyst, SOC lead |
| Phân bố loại/OS/criticality | Cơ cấu tài sản, giá trị hiếm | Bar ngang hoặc donut ≤6 nhóm; toggle most/least seen; bấm segment → danh sách | runZero, Splunk, Microsoft, Axonius [5][33][7][40] | `device.type_id`, `os.type_id`/`os.name`, `resource_details.criticality_id` (0 Unknown = chưa phân loại), `device.groups`, `org`, `region` (E+S) | MVP (BU/site: sau) | SOC lead |
| Coverage theo nguồn | Nguồn nào thấy bao nhiêu, còn bao nhiêu unique | Bar ngang xếp hạng + tổng lượt thấy vs unique; bấm hàng → danh sách | Axonius, Splunk, runZero [10][33][5] | Tập asset_id quan sát theo `metadata.product.name` trong N ngày (S) | MVP | SOC lead |
| Chồng lấn nguồn | Asset nào chỉ một nguồn thấy (CIS 1.1 Accuracy) | Venn ≤3 tập; UpSet/ma trận khi >3; MVP là danh sách "chỉ 1 nguồn" | Axonius [11] | Như trên (S) | MVP danh sách, UpSet sau | SOC lead |
| Độ phủ EDR/agent | Bao nhiêu asset thiếu hoặc tắt bảo vệ | Stacked bar 100% active/inactive/missing theo loại/criticality + trend; bấm → danh sách thiếu | Axonius, CrowdStrike, Microsoft [35][43][37] | `agent_list[].type_id`=1, `device.is_managed`, 5019 `security_states[].state_id` 4, 11 (E+S) | MVP | SOC lead, khách hàng tenant |
| Độ phủ log (CIS 8.2/8.9) | Asset có khả năng log nào chưa được thu | Stacked bar 100%: thu tập trung / có khả năng nhưng chưa thu / không hỗ trợ; theo criticality | Không vendor nào dựng sẵn; công thức CIS [13] | Asset × nguồn log trong kho; `agent_list[].type_id`=6 (S) | MVP | SOC lead |
| Chất lượng inventory | % chưa phân loại criticality, % chưa có owner | KPI + trend có đường mục tiêu; bấm → hàng chờ phân loại | runZero Asset ownership, CDM UAH [5][14] | `resource_details.criticality_id`=0, owner rỗng (`owner` của endpoint lẫn với "last logged into") (S) | MVP | SOC lead, khách hàng tenant |
| Exposure severity × criticality | Lỗ hổng nặng nằm trên asset quan trọng nào | Heatmap 4×4, ô = số asset; bấm → danh sách | Không vendor nào; gần nhất là donut exposure Microsoft, bar Tenable [7][8] | 2002 `vulnerabilities[].severity`, `cve.cvss[].base_score`, `is_exploit_available`, nối criticality từ kho (E+S) | MVP | SOC lead, đội vá |
| Top asset/user rủi ro | Xử lý asset nào trước | Bảng top N + sparkline 14 ngày + link profile | Elastic, Microsoft, Tenable [38][7][8] | Điểm tổng hợp trong kho; đầu vào 2004 `risk_score`, 2005 `priority_id`, `user.risk_score` (S) | MVP | Analyst |
| Data freshness / health | Nguồn nào trễ, dashboard có tin được không | Dashboard riêng: big number + line theo ngày + bảng nguồn; nhãn tóm tắt trên inventory | Google Health Hub [34] | `metadata.processed_time` − `time` (hoặc `logged_time` − `time`), `max(time)` theo `metadata.product.name` (E) | MVP | SOC lead, kỹ sư dữ liệu |
| Compliance pass/fail | Cấu hình sai tập trung ở control nào | Stacked bar 100% theo control | Không đọc được mẫu cụ thể | 2003 `compliance.status_id` (1 Pass, 2 Warning, 3 Fail), `control`, `standards` (E+S) | Sau | SOC lead, khách hàng tenant |
| Patch state | Máy nào thiếu bản vá | Bar theo KB/tuổi | Wazuh (Windows KB most/least common) [41] | 5004 `kb_article_list[].install_state_id`, `severity`, `created_time` (E+S) | Sau | Đội vá |
| Bản đồ vị trí | Asset nằm ở đâu | Bubble map | Splunk, runZero [33][5] | `device.location` (`country`, `city`, `lat`, `long`) (E+S) | Sau | Khách hàng tenant |

### Wireframe dashboard inventory tenant

```
Tenant: ACME ▾    Khoảng: 30 ngày ▾    Dữ liệu cập nhật 06:40 · 2 nguồn đang trễ ⚠  [Data health →]
┌────────────┬────────────┬────────────┬────────────┬────────────┬────────────┐
│ ASSET      │ MỚI 7 NGÀY │ SILENT >7d │ KHÔNG EDR  │ PHỦ EDR    │ CHƯA CRIT  │
│ 12.480     │ +312       │ 486        │ 1.104      │ 91% đích 95│ 23% đích 10│
│ ▲2,1% ▁▂▃▅ │ ▲18%  ▃▂▅▇ │ ▲9% ⚠ ▂▃▅▆ │ ▼4%  ▆▅▄▃  │ ▃▄▄▅▅▆     │ ▇▆▆▅▄▄     │
└────────────┴────────────┴────────────┴────────────┴────────────┴────────────┘
┌ ASSET THEO LIFECYCLE 90d (stacked area) ──────┐┌ ASSET MỚI THEO NGÀY (stacked bar/loại) ────┐
│ ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ silent                      ││  ▇       ▅             ▇                   │
│ ░░░░░░░░░░░░░░░░░ stale                       ││ ▃█▂ ▃ ▂ ▃█▂ ▃  ▂ ▃ ▂ ▃ █▃                  │
│ █████████████████ live                        ││ server ■ laptop ■ IoT ■ cloud ■            │
└───────────────────────────────────────────────┘└────────────────────────────────────────────┘
┌ COVERAGE THEO NGUỒN (lượt thấy) ──────────────┐┌ ĐỘ PHỦ 100% THEO CRITICALITY ──────────────┐
│ DHCP     ████████████████ 12.010              ││        EDR              Log tập trung      │
│ EDR      ██████████████ 10.950                ││ Crit  ███████████▒ 96%  ██████████▒▒ 88%   │
│ AD       █████████████ 9.870                  ││ High  ██████████▒▒ 90%  ████████▒▒▒▒ 74%   │
│ Scanner  ██████████ 7.420                     ││ Med   █████████▒▒▒ 84%  ██████▒▒▒▒▒▒ 61%   │
│ Unique sau hợp nhất 12.480 · chỉ 1 nguồn 1.930││ Low   ███████▒▒▒▒▒ 70%  ████▒▒▒▒▒▒▒▒ 40%   │
└───────────────────────────────────────────────┘└────────────────────────────────────────────┘
┌ PHÂN BỐ [Loại|OS|Crit|Site] [most|least] ─────┐┌ EXPOSURE severity × criticality ───────────┐
│ Windows 11    ████████████ 5.210              ││            Low   Med  High  Crit           │
│ Ubuntu 22.04  █████ 1.980                     ││ CVE Crit    12    40    31     9  ← bấm ô  │
│ Unknown       ███ 1.120  (chưa nhận diện)     ││ CVE High    80   210   160    22           │
└───────────────────────────────────────────────┘└────────────────────────────────────────────┘
┌ TOP 10 ASSET/USER RỦI RO (bảng · sparkline 14d · criticality · nguồn đóng góp chính) ───────┐
```

## Cấp MSSP: vendor mới dừng ở bảng tenant × số đếm, heatmap tenant × KPI còn bỏ trống

Microsoft là vendor duy nhất trong mẫu có docs rõ cho view inventory đa tenant. Trang Tenants của Defender multitenant management hiện, cho từng tenant, "the number of devices and device types, the number of high value and high exposure devices, and the number of devices available to onboard"; đầu trang có số tenant và tổng device onboarded/discovered; bấm tên tenant thì vào device inventory của tenant đó. Trang device inventory đa tenant giữ nguyên bố cục một tenant, chỉ thêm cột Tenant name và hàng tổng "for all tenants" ở trên [46]. Microsoft Secure Score có "comparison bar chart" và "comparison trend" so với các tổ chức tương tự (ẩn danh) [47], một mẫu benchmark có thể dùng lại để xếp hạng tenant. CDM AWARE cũng khuyến khích agency so điểm của mình với "federal average score" [14].

![Defender multitenant tenant view](https://learn.microsoft.com/en-us/defender-xdr/media/mto-tenant-devices/devices-tenant-view.png)
*Microsoft Defender XDR – Multitenant management, Tenants: bảng tenant × số device, high value, high exposure và device có thể onboard. Ảnh này cũng có trong báo cáo trước, dùng lại vì không tìm được ảnh MSSP nào khác. Nguồn: [46]*

Các vendor khác chỉ cung cấp hạ tầng để MSSP tự dựng. Sentinel cho triển khai workbook ở managing tenant qua Azure Lighthouse để "create at-scale dashboards to monitor and query data across customer tenants", truy vấn chéo workspace bằng `union` và `workspace()` (nội dung đọc qua snippet) [48][49]. Wazuh coi tenant là "containers for saved objects such as index patterns, visualizations, and dashboards", tức tách dashboard, còn docs không nói tách index [50]. Azure Workbooks cho phép link từ grid, tile hay graph sang một workbook khác và truyền tham số, đúng cơ chế cần để drill-down từ hàng tenant sang dashboard tenant [51]. Không tìm được docs view tổng hợp của Google SecOps, Axonius hay Splunk cho MSSP.

**Nhận định:** mẫu Microsoft (cùng bố cục cho một tenant và nhiều tenant, thêm cột Tenant, hàng tổng ở trên, bấm hàng để vào tenant) đơn giản và nên theo. Phần còn thiếu là chuyển bảng số đếm thành **bảng tỉ lệ có tô màu theo ngưỡng**, tức heatmap tenant × KPI, vì số đếm thô không so được giữa tenant 500 asset với tenant 50.000 asset. Các ngưỡng CIS (discovery ≤24 giờ, xử lý asset trái phép ≤7 ngày, review log ≤7 ngày) cho sẵn tiêu chí pass/fail để tô từng ô [12][13]. Mọi truy vấn MSSP gom theo `metadata.tenant_uid`, trường OCSF chỉ để recommended nên pipeline phải bắt buộc điền [32].

### Bảng (c): bộ biểu đồ đề xuất cho tổng quan MSSP

**Nhận định:** cột "Ưu tiên", "Người xem" và các dòng không có vendor tham khảo là đề xuất.

| Biểu đồ | Câu hỏi vận hành | Loại chart & tương tác | Vendor tham khảo | Dữ liệu OCSF 1.9.0 / kho entity | Ưu tiên | Người xem |
|---|---|---|---|---|---|---|
| Hàng KPI toàn portfolio | Cả MSSP quản lý bao nhiêu, bao nhiêu tenant dưới ngưỡng | Tile số tenant, tổng asset, tổng critical, số tenant fail ≥1 KPI | Microsoft MTO [46] | Gộp snapshot kho theo `tenant_uid` (S) | MVP | MSSP manager |
| Ma trận tenant × KPI | Tenant nào yếu ở chỉ số nào | Bảng tỉ lệ tô màu pass/warn/fail theo ngưỡng (heatmap), sort theo cột; bấm ô → dashboard tenant đã lọc | Microsoft MTO (dạng số đếm) [46]; ngưỡng CIS [12][13] | % EDR, % log 8.9, % chưa crit, % silent theo `tenant_uid` (S); độ trễ nguồn (E) | MVP | MSSP manager, SOC lead |
| Health nguồn đa tenant | Tenant nào đang mất dữ liệu | Lưới tenant × loại nguồn, ô = Healthy/Irregular/Failed + last seen | Google Health Hub (một tenant) [34] | `max(time)`, `processed_time` − `time` theo `tenant_uid` × `metadata.product.name` (E) | MVP | MSSP manager, kỹ sư dữ liệu |
| Ranking / benchmark | Tenant đứng đâu so với phần còn lại | Bar xếp hạng một KPI + đường trung vị MSSP; bản cho khách chỉ hiện tenant đó và trung vị ẩn danh | Secure Score comparison, AWARE federal average [47][14] | Snapshot KPI theo tenant (S) | Sau | MSSP manager, khách hàng tenant |
| Trend portfolio | KPI của các tenant đi lên hay xuống | Small multiples line, mỗi tenant một ô, chung trục | Không vendor nào | Snapshot KPI theo ngày × tenant (S) | Sau | MSSP manager |
| Hàng chờ theo tenant | Việc tồn nằm ở tenant nào | Stacked bar tenant × (asset chưa phân loại, asset trái phép quá 7 ngày, nguồn hỏng) | Không vendor nào; ngưỡng CIS 1.2 [12] | Kho entity + 5019 theo `tenant_uid` (S) | Sau | MSSP manager |

### Wireframe tổng quan MSSP

```
MSSP · 38 tenant · 412.300 asset · 9 tenant fail ≥1 KPI ⚠        [Khoảng: 30 ngày ▾] [Nhóm KH ▾]
┌──────────────┬─────────┬─────────┬─────────┬──────────┬─────────┬───────────┬──────────┐
│ Tenant       │ Asset   │ Phủ EDR │ Log 8.9 │ Chưa crit│ Silent  │ Discovery │ Nguồn lỗi│
│              │         │ đích 95%│ đích 90%│ đích 10% │ đích 3% │ ≤24h      │          │
├──────────────┼─────────┼─────────┼─────────┼──────────┼─────────┼───────────┼──────────┤
│ ACME         │ 12.480  │ ▒ 91%   │ ▓ 74%   │ ▓ 23%    │ ▒ 3,9%  │ ✓ 6h      │ 2 ⚠      │
│ Beta Bank    │ 48.020  │ ░ 97%   │ ░ 93%   │ ░  6%    │ ░ 1,2%  │ ✓ 4h      │ 0        │
│ Gamma Retail │    530  │ ▓ 62%   │ ▓ 41%   │ ▓ 58%    │ ▓ 11%   │ ✗ 3 ngày  │ 4 ✗      │
│ ...          │         │         │         │          │         │           │          │
└──────────────┴─────────┴─────────┴─────────┴──────────┴─────────┴───────────┴──────────┘
  ░ đạt   ▒ cảnh báo   ▓ không đạt        bấm ô → dashboard tenant đã lọc theo KPI đó
┌ XẾP HẠNG: Phủ EDR theo tenant ───────────────┐┌ HEALTH NGUỒN: tenant × loại nguồn ─────────┐
│ Beta Bank   ███████████████ 97%              ││            EDR  AD  FW  DNS  Cloud  Scan   │
│ ACME        █████████████▌  91%              ││ ACME        ✓   ✓   ⚠   ✓    ✓     ⚠      │
│ ── trung vị MSSP 88% ──────────              ││ Gamma       ✗   ✓   ✗   ⚠    –     ✗      │
│ Gamma       █████████       62%              ││ Beta        ✓   ✓   ✓   ✓    ✓     ✓      │
└──────────────────────────────────────────────┘└────────────────────────────────────────────┘
```

## Nguyên tắc thiết kế: mỗi widget là một số đo có mục tiêu, nguồn và danh sách đích

### Năm nguyên tắc rút từ docs vendor và tiêu chuẩn

**Actionability.** NIST SP 800-55 Vol.1 (12/2024) đặc tả mỗi measure bằng *Target* ("A range or a designated upper or lower bound… final and interim targets"), *Time-based reference* (tần suất theo "rate of change that is being evaluated"), *Data source* và *Reporting format* ("such as a pie chart, line chart, bar graph, or other format"); báo cáo không kèm ngữ cảnh thì "there can be unintended consequences or indecision", nên phải nêu rủi ro số đo chỉ ra và "What prioritization, action, or decision might need to be taken" [52]. Splunk nói cùng ý: dashboard giám sát cần "quick context, key information, and indication of action", và bước đầu tiên là xác định "Your intended audience, purpose and their resulting actions" [36]. **Nhận định:** mỗi widget nên có một phiếu đặc tả gồm câu hỏi vận hành, công thức, mục tiêu, tần suất, nguồn OCSF và danh sách asset nó mở ra; widget nào không viết được dòng cuối là ứng viên vanity.

**Drill-down tới danh sách đã lọc.** runZero: "you can view any widget's distinct data points in detail by clicking the relevant table row links or buttons, or individual segments of donut, bar, or column charts" (trừ biểu đồ timeline) [5]. Axonius: "Clicking a chart segment opens the Asset Table using the view associated with that segment", với Query Intersection thì base query được ghép với query của segment [6]. Tenable có drill down mode: bấm một data point để đi xuống dữ liệu chi tiết hơn ngay trong widget [8], Splunk ES 8.6 cho "drill directly from these dashboards into Entity Discovery Inventory" [33], và Azure Workbooks truyền tham số sang workbook chi tiết với điều kiện "parameter names must be the same in both workbooks" [51]. **Nhận định:** lưu mỗi widget dưới dạng truy vấn có tên trên kho entity, để segment nào cũng sinh được URL danh sách; đây là quyết định kiến trúc chứ không phải chi tiết UI.

**KPI có ngữ cảnh, delta và mục tiêu.** Microsoft Exposure Management cho mỗi initiative một "14 day change trend graph", một target score người dùng tự đặt, và History: chọn một thời điểm để xem "percent effect on the initiative score and the reason for the change" cùng "up to the top 100 changed assets"; dữ liệu được tính lại theo device group và scope của người xem [9]. NIST Vol.2 nhấn việc giữ số đo nhất quán để thấy "long-term trends and expected ranges" và đặt mục tiêu "against industry standards and internal targets" [53]. NIST cũng cảnh báo số đếm như số lỗ hổng đã biết "depend heavily on the quality of work behind them" [52], nên số đếm thô cần đổi thành tỉ lệ hoặc chia theo criticality.

![Exposure Management initiative history](https://learn.microsoft.com/en-us/security-exposure-management/media/initiatives/initiatives-history-details.png)
*Microsoft Security Exposure Management – Initiative history: chọn một thời điểm trên trend để xem lý do điểm thay đổi và danh sách asset được thêm hoặc bớt, tức drill-down từ con số sang asset. Nguồn: [9]*

**Tránh graph hairball bằng cách khoanh phạm vi.** Cambridge Intelligence (vendor thư viện graph) khuyên "graph filtering and node and link aggregation" và bắt đầu "backwards from the job your end users need to get done", dựng view dẫn xuất thay vì vẽ toàn bộ graph [54]. Axonius làm đúng như vậy: gom node cùng loại, chỉ cho ungroup dưới 500 node, có layer theo loại asset [28]. CISA, trong hướng dẫn cho OT, khuyên vẽ sơ đồ theo nhóm tài sản (Zones and Conduits) và "Use tables or charts to show asset relationships and dependencies" [55]. **Nhận định:** chỉ vẽ ego-graph quanh một asset với độ sâu 1–2 hop, cửa sổ thời gian mặc định 24 giờ, gom IP/process cùng loại thành node đếm, lọc theo loại quan hệ; không có graph "toàn tenant" mặc định, ở cấp tenant chỉ dùng sơ đồ đã gộp theo zone/segment.

**Tách dashboard sức khoẻ dữ liệu.** Google tách Health Hub khỏi các dashboard nghiệp vụ, và cảnh báo feed có thể hiện Active dù thu thập đang hỏng [34]. NIST yêu cầu kiểm tra "integrity, accuracy, and structure of the data" trước khi phân tích, và coi dữ liệu là đáng ngờ khi nguồn chỉ nhận báo cáo từ một vài bộ phận [52]. Microsoft TVM loại device không hoạt động 30 ngày khỏi phép tính [7], một ví dụ về việc phải ghi rõ mẫu số ngay trên dashboard.

### KPI chuẩn từ CIS, CDM và NIST và cách đưa lên biểu đồ

CIS Controls Assessment Specification cho sẵn công thức và ngưỡng cho Control 1 (inventory) và 8 (audit log), CISA CDM AWARE cho công thức điểm bề mặt tấn công, NIST cho khung đặc tả. Cột "Hiển thị đề xuất" là **Nhận định**.

| Chỉ số | Công thức / ngưỡng | Nguồn | Hiển thị đề xuất |
|---|---|---|---|
| CIS 1.1 Inventory Accuracy | M3/M2 = asset có cả trong inventory và nguồn đối chiếu / asset trong nguồn đối chiếu; M4 = asset trong inventory không có ở nguồn đối chiếu | [12] | Tile % + sparkline + đích; drill-down hai danh sách lệch nhau |
| CIS 1.1 Completeness | Trang ghi "M8/M1", nhiều khả năng lỗi đánh máy của M6/M1 (asset đủ thông tin chi tiết / inventory) | [12] | Tile % "đủ thuộc tính bắt buộc" |
| CIS 1.1 độ tươi inventory | Fail nếu M8 (số tháng từ lần cập nhật cuối) > 6 tháng | [12] | Nhãn tuổi dữ liệu xanh/đỏ |
| CIS 1.2 xử lý asset trái phép | Coverage = (M2 − M4)/M2, M2 = số asset trái phép, M4 = số asset trái phép *unreachable* sau scan (trang lại ghi metric = 1 khi M4 = 0, tức định nghĩa tự mâu thuẫn); fail nếu khung thời gian xử lý doanh nghiệp đặt > 7 ngày | [12] | Tile + bar tuổi hàng chờ; ô MSSP pass/fail |
| CIS 1.3 Asset Discovery Coverage | M1/M6 = asset phát hiện / inventory; fail nếu chu kỳ discovery > 24 giờ | [12] | Tile % + trend; ô MSSP pass/fail |
| CIS 1.4 CMDB Updating Accuracy | M6/M7 = thiết bị trong DHCP log có trong CMDB / thiết bị duy nhất trong DHCP log | [12] | Tile % + danh sách thiết bị DHCP chưa có trong kho |
| CIS 1.5 passive discovery | Mạng được phủ / tổng số mạng | [12] | Bar theo subnet/site |
| CIS 8.2 Collect Audit Logs | Asset cấu hình log đúng / asset có khả năng log | [13] | Stacked bar 100% theo criticality |
| CIS 8.9 Log Aggregating | Asset được ít nhất một hệ thống thu gom phủ / asset có khả năng log | [13] | Như trên; cột chính của ma trận MSSP |
| CIS 8.10 / 8.11 | Tỉ lệ hệ thống thu gom giữ log ≥ 90 ngày; fail nếu khoảng giữa hai lần review log > 7 ngày | [13] | Ô pass/fail |
| CDM AWARE | Scaled Base CVSS × Age × Weight [Threat, Impact] × Tolerance [Grace Period]; Age tính từ ngày công bố CVE, "90 days to double score"; thành phần UAH = "hardware devices that have not been assigned ownership in a dashboard container" | [14] | Công thức mẫu cho nguồn đóng góp điểm; tile "% asset chưa gán owner" |
| NIST SP 800-55 | Mỗi measure có target, time-based reference, data source, reporting format; ví dụ "percentage of systems with up-to-date patches", "color-coded risk matrix" | [52] | Phiếu đặc tả cho mọi widget |

CISA OT Asset Inventory Guidance (8/2025, 9 cơ quan đồng ký) xếp "Asset criticality" và "Logging" vào 14 thuộc tính ưu tiên cao, và chia criticality ba mức High/Medium/Low [55]. **Nhận định:** điều đó biện minh cho việc coi "% chưa phân loại criticality" và "% asset có log" là KPI chất lượng inventory hàng đầu, ngang với tổng asset. CAS tự ghi các metric chuẩn chỉ là ví dụ, không phải danh sách đầy đủ, nên sản phẩm có thể thêm chỉ số riêng như "% asset silent".

**Nhận định về người xem** (chưa có nguồn bậc 1 bàn trực tiếp cho SOC đa tenant): analyst cần trang asset, timeline, ego-graph và bảng top rủi ro; SOC lead cần KPI có ngưỡng, trend coverage và data health; khách hàng tenant cần ít chỉ số tổng (phủ EDR/log, exposure theo criticality, xu hướng so mục tiêu), tương ứng với việc NIST Vol.2 hướng tới lãnh đạo [53]; MSSP manager cần ma trận tenant × KPI và ranking.

## Dữ liệu: biểu đồ sự kiện lấy thẳng từ OCSF, biểu đồ trạng thái cần kho entity

Tên class và field trong ba bảng đều đã đối chiếu với file JSON của `ocsf/ocsf-schema` tag 1.9.0 (commit 856d462, 2026-08-03) [32]. Các biểu đồ dựa trên sự kiện lấy trực tiếp được: timeline và heatmap dùng `time`, `class_uid`, `activity_id`, `count`; telemetry và độ trễ dùng `metadata.product`, `metadata.log_source`, `metadata.logged_time`, `metadata.processed_time`; finding dùng Detection Finding 2004 (`risk_score`, `risk_level_id`, `is_alert`), Incident Finding 2005 (`priority_id`, `status_id`), Vulnerability Finding 2002 (`cve.cvss[]`, `cve.epss`, `is_exploit_available`, `is_fix_available`), Compliance Finding 2003 (`compliance.status_id` 1 Pass, 2 Warning, 3 Fail); trạng thái bảo vệ dùng Device Config State Change 5019 (`security_states[].state_id` như 4 Protection off, 11 Not installed); graph dùng object `graph` (`nodes`, `edges`) qua `finding_info.attack_graph` và `resource_details.resource_relationship` [32].

Các biểu đồ về trạng thái tài sản theo thời gian thì OCSF không nuôi được, vì schema không có thực thể asset bền vững. Object `device` có `first_seen_time`, `last_seen_time`, `is_managed`, `risk_score`, nhưng đó là giá trị một nguồn báo trong một event; `device` không có `criticality_id` (chỉ `resource_details` có), và `risk_score` của 2004 là "as reported by the event source" nên không so được giữa nguồn [32]. **Nhận định:** kho entity phải tự giữ asset_id hợp nhất theo (`tenant_uid`, asset_id), first/last seen theo từng nguồn, lifecycle state, criticality và owner thật, điểm rủi ro tổng hợp cùng lịch sử, cạnh quan hệ bền vững, và **snapshot đếm theo ngày**. Snapshot hằng ngày là thứ dễ bị bỏ quên nhất, nhưng thiếu nó thì mọi tile delta, sparkline và trend ở cấp tenant lẫn MSSP đều không vẽ được.

## Các nguồn bất đồng ở đâu

Elastic từng là chỗ phiên bản không khớp nhất giữa các bản docs preview; docs chính thức hiện ghi risk score history chart là GA từ Stack 9.5, còn graph preview trong flyout là Preview từ Stack 9.4 [4]. Nên coi đây là tính năng mới. Google SecOps định nghĩa prevalence không thống nhất giữa các trang ("số asset tối đa gần đây" và "số asset trong 7 ngày") [22][23]; với thiết kế, định nghĩa 7 ngày là đủ dùng. Trang CIS CAS (bản cho Controls v8.1) có công thức nghi lỗi đánh máy (Completeness 1.1 = "M8/M1", Tool Compliance Ratio 1.3 = "M3/M2") và định nghĩa M4 của 1.2 không khớp với cách tính metric [12]; nên dùng theo nghĩa của measure chứ không chép nguyên ký hiệu.

Về trường phái, Microsoft device inventory và Elastic Entity Analytics chọn "danh sách hành động" (count pill, bảng top N, gần như không chart) [37][38], trong khi Splunk, runZero, Axonius và Tenable chọn "toàn cảnh" bằng nhiều chart [33][5][40][8]. Phiên bản mạnh nhất của phe danh sách là: analyst cần biết làm gì tiếp theo, và chart nào cuối cùng cũng dẫn về danh sách. **Nhận định:** hai phe không mâu thuẫn nếu chart nào cũng bấm ra danh sách; ở cấp asset, với người xem là analyst, nên nghiêng về danh sách; ở cấp tenant và MSSP, với SOC lead hoặc khách hàng, cần chart xu hướng và cơ cấu. Brief có liệt kê Sankey, treemap và Venn coverage, nhưng trong docs đã đọc không vendor nào dùng Sankey hay treemap cho inventory; coverage được làm bằng Venn/intersection hoặc bảng nguồn × số asset [11][33].

## Kết luận và hàm ý

Điểm chung của các biểu đồ có giá trị ở cả ba cấp không nằm ở loại chart mà ở ba thuộc tính: có mốc so sánh (kỳ trước, mục tiêu, peer, ngưỡng CIS), bấm được ra danh sách asset cụ thể, và hiển thị kèm độ tươi của dữ liệu. Với sản phẩm SOC đa tenant trên OCSF, khoảng trống đáng khai thác nhất lại chính là chỗ vendor CAASM/XDR yếu: họ vẽ asset như một bản ghi cấu hình, còn một SOC quản lý log thì biết từng asset đang gửi gì từ nguồn nào. Vì thế sparkline telemetry theo nguồn trên trang asset, stacked bar độ phủ log theo CIS 8.9 ở cấp tenant, và ma trận tenant × KPI tô màu theo ngưỡng ở cấp MSSP là ba biểu đồ vừa khác biệt vừa dựng được từ `metadata.product` và `metadata.tenant_uid`.

Hàm ý cho lộ trình: MVP nên gồm risk trend có drill-down, nguồn đóng góp điểm, breakdown severity/MITRE, timeline overview + detail, telemetry theo nguồn, chip bảo vệ và vuln breakdown ở cấp asset; hàng KPI có delta/đích, lifecycle, asset mới, phân bố, coverage theo nguồn, độ phủ EDR/log, chất lượng inventory, heatmap exposure × criticality, top rủi ro và data health ở cấp tenant; ma trận tenant × KPI tô màu và health nguồn đa tenant ở cấp MSSP. Graph quan hệ, prevalence, attack path, peer comparison và benchmark nên đi sau, vì chúng phụ thuộc vào kho entity đã có role, cạnh quan hệ và lịch sử ổn định. Điều kiện tiên quyết kỹ thuật cho gần như toàn bộ danh sách MVP là kho entity lưu snapshot hằng ngày và lưu mỗi widget dưới dạng truy vấn có tên.

## Chưa kiểm chứng được

- CrowdStrike host page, Threat Graph, process tree: trang tech-center redirect về trang chung, không lấy được ảnh hay mô tả biểu đồ bậc 1. Truy vấn đã thử: "CrowdStrike Falcon host management process tree OR graph explorer blog screenshot 2024".
- Trend Vision One Asset Risk Graph và các widget Risk Summary/Assets at Risk: chỉ đọc qua snippet; trang render JS hoặc redirect loop; không có ảnh.
- Cortex XSIAM Unified Asset Inventory và Tenant Navigator, Armis Centrix: không đọc được danh sách widget chính thức (render JS, docs khoá, hoặc chỉ có tài liệu marketing).
- Splunk ES 8.5 entity analysis dashboard: không tìm thấy trang mô tả biểu đồ; ảnh trên help.splunk.com render bằng JS, docs.splunk.com trả 403.
- Tenable asset relationships/attack path ở cấp biểu đồ, Tenable Lumin, runZero Goals: chưa mở chi tiết.
- View inventory đa tenant của Google SecOps, Axonius và Splunk: không tìm được docs. Giới hạn "up to 20 workspaces per query" của Sentinel chỉ thấy trên docs.azure.cn, chưa xác minh.
- Heatmap 7×24 đúng nghĩa: Cortex và Google có dạng gần nhất nhưng docs không nói rõ lưới; ảnh time-shift của Google trả 404.
- Widget "% chưa phân loại criticality" hay "chất lượng inventory" dựng sẵn: không vendor nào có; Microsoft chỉ có card "Classify critical assets".
- Giao diện CDM Agency/Federal Dashboard: không có ảnh công khai, chỉ có fact sheet 2020. Truy vấn: "CDM dashboard asset management AWARE score display".
- SANS SOC Survey 2024/2025 (con số "67% cung cấp metrics cho lãnh đạo"), Gartner outcome-driven metrics, talk "Better Security Metrics" (Blue Team Con 2022): chỉ thấy snippet hoặc nằm sau paywall.
- Phân tầng người xem analyst / SOC lead / khách hàng / MSSP manager: chưa có nguồn bậc 1 bàn trực tiếp cho dashboard asset; phần đó là suy luận.
- Chưa có nguồn mô tả vendor dựng biểu đồ trực tiếp từ OCSF (vd Security Lake + QuickSight); ánh xạ field trong ba bảng là thiết kế đề xuất.
- Sumo Logic (có trong phạm vi brief): chưa khảo sát.
- Cortex XSIAM Investigate a host/user [1][15]: lúc kiểm chứng lại (2026-11-03) trang trả HTTP 500, nên các mô tả Risk Score Trend, Compare To và widget breakdown chỉ dựa trên lần đọc của researcher cùng ngày, chưa đối chiếu lại.

## Nguồn
[1] Investigate a host — Palo Alto Networks, Cortex XSIAM docs, không rõ ngày, truy cập 2026-11-03 (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/detect-investigate-and-respond-to-threats/investigation-and-response/investigate-artifacts-and-assets/investigate-a-host
[2] Get to know a user profile — Exabeam, Advanced Analytics user guide, không rõ ngày (bậc 1). https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153664-get-to-know-a-user-profile.html
[3] Access the intermediate findings timeline to review findings in Splunk Enterprise Security — Splunk, ES 8.5, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.5/risk-based-alerting/access-the-intermediate-findings-timeline-to-review-findings-in-splunk-enterprise-security
[4] View entity details — Elastic Security docs, không rõ ngày, truy cập 2026-11-03 (bậc 1; risk score history GA từ Stack 9.5, graph preview là Preview từ 9.4). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/view-entity-details
[5] Dashboard — runZero docs, cập nhật 2026-09-17 (bậc 1). https://www.runzero.com/docs/dashboard/
[6] Chart Click-Through — Axonius, không rõ ngày (bậc 1). https://docs.axonius.com/docs/chart-click-through
[7] Defender Vulnerability Management overview page (dashboard insights) — Microsoft Learn, 2025–2026 (bậc 1). https://learn.microsoft.com/en-us/defender-vulnerability-management/tvm-dashboard-insights
[8] Dashboard Overview — Tenable Exposure Management docs, không rõ ngày; ảnh 2025 (bậc 1). https://docs.tenable.com/exposure-management/Content/analytics/dashboard-overview.htm
[9] Review security initiatives — Microsoft Learn, Microsoft Security Exposure Management, cập nhật 2026-10-09 (bậc 1). https://learn.microsoft.com/en-us/security-exposure-management/initiatives
[10] Device Discovery Chart — Axonius, không rõ ngày (bậc 1). https://docs.axonius.com/docs/device-discovery-chart
[11] Query Intersection Chart — Axonius, không rõ ngày (bậc 1). https://docs.axonius.com/docs/query-intersection-chart
[12] CIS Controls Assessment Specification for Controls v8.1 — Control 1: Inventory and Control of Enterprise Assets — Center for Internet Security, không rõ ngày (bậc 1). https://cas.docs.cisecurity.org/en/latest/source/Controls1/
[13] CIS Controls Assessment Specification for Controls v8.1 — Control 8: Audit Log Management — Center for Internet Security, không rõ ngày (bậc 1). https://cas.docs.cisecurity.org/en/latest/source/Controls8/
[14] CDM Program AWARE Scoring fact sheet — CISA, 2020-09 (bậc 1). https://www.cisa.gov/sites/default/files/2023-01/cdm-program-aware-scoring-fact-sheet-092020-508_1.pdf
[15] Investigate a user — Palo Alto Networks, Cortex XSIAM docs, không rõ ngày, truy cập 2026-11-03 (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/detect-investigate-and-respond-to-threats/investigation-and-response/investigate-artifacts-and-assets/investigate-a-user
[16] Investigate users in Microsoft Defender — Microsoft Learn, không rõ ngày, truy cập 2026-11-03 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/investigate-users
[17] View and analyze risk score data — Elastic, không rõ ngày, truy cập 2026-11-03 (bậc 1). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/view-analyze-risk-score-data
[18] Device entity page in Microsoft Defender — Microsoft Learn, không rõ ngày (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/entity-page-device
[19] Investigate an IP address — Google Cloud, Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/investigation/investigate-ipaddress
[20] Entity pages in Microsoft Sentinel — Microsoft Learn, không rõ ngày (bậc 1). https://learn.microsoft.com/en-us/azure/sentinel/entity-pages
[21] Investigate a user — Google Cloud, Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/investigation/investigate-user
[22] Investigate an asset — Google Cloud, Google SecOps docs, không rõ ngày, truy cập 2026-11-03 (bậc 1). https://docs.cloud.google.com/chronicle/docs/investigation/investigate-asset
[23] Review an alert — Google Cloud, Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/review-alert
[24] Causality view — Palo Alto Networks, Cortex XDR 5.x docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xdr-5.x/detect-investigate-and-respond-to-threats/investigate-and-respond-to-cases/investigate-issues/causality-view
[25] Visual event analyzer — Elastic, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/investigate/visual-event-analyzer
[26] Session view — Elastic, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/investigate/session-view
[27] Investigate incidents (investigation graph) — Microsoft Learn, Microsoft Sentinel, không rõ ngày (bậc 1). https://learn.microsoft.com/en-us/azure/sentinel/investigate-incidents
[28] Graph Overview (Asset Graph) — Axonius, 2024 (bậc 1). https://docs.axonius.com/docs/asset-graph-overview
[29] Exploring connections and asset relationships — Axonius, 2024 (bậc 1). https://docs.axonius.com/docs/exploring-connections-and-asset-relationships
[30] Trend Vision One February 2024 release note — Trend Micro, 2024-02 (bậc 1, chỉ đọc qua snippet tìm kiếm). https://docs.trendmicro.com/en-us/documentation/article/trend-vision-one-february-2024
[31] Review attack paths — Microsoft Learn, Microsoft Security Exposure Management, không rõ ngày, truy cập 2026-11-03 (bậc 1). https://learn.microsoft.com/en-us/security-exposure-management/review-attack-paths
[32] OCSF Schema, tag 1.9.0 (commit 856d462; các file finding, detection_finding, incident_finding, compliance_finding, vulnerability, cve, metadata, device, endpoint, device_config_state_change, security_state, graph, finding_info, dictionary) — OCSF, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/tree/1.9.0
[33] Deeper Exposure Analytics in Splunk Enterprise Security 8.6 — Splunk blog, 2026-08-04 (bậc 1). https://www.splunk.com/en_us/blog/security/deeper-exposure-analytics-in-splunk-enterprise-security-8-6.html
[34] Use the Health Hub — Google Cloud, Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/reports/data-health-monitoring-and-troubleshooting-dashboard
[35] Agent Coverage Dashboards — Axonius, không rõ ngày (bậc 1). https://docs.axonius.com/docs/agent-coverage-dashboards
[36] Dashboard Design: Getting Started With Best Practices (Part 1) — Lizzy Li, Splunk, 2022-09-01 (bậc 1 về điều vendor khuyến nghị). https://www.splunk.com/en_us/blog/tips-and-tricks/dashboard-design-getting-started-with-best-practices-part-1.html
[37] Explore devices in the device inventory — Microsoft Learn, Defender for Endpoint, 2026 (bậc 1). https://learn.microsoft.com/en-us/defender-endpoint/machines-view-overview
[38] Entity Analytics dashboard — Elastic, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/dashboards/entity-analytics-dashboard
[39] Get started with Microsoft Security Exposure Management — Microsoft Learn, cập nhật 2026-07-26 (bậc 1). https://learn.microsoft.com/en-us/security-exposure-management/get-started-exposure-management
[40] Creating Dashboards and Charts with the AI Agent (danh mục loại chart) — Axonius, không rõ ngày (bậc 1). https://docs.axonius.com/docs/creating-dashboards-and-charts-with-the-ai-agent
[41] Viewing system inventory data — Wazuh documentation (4.13+), 2025–2026 (bậc 1). https://documentation.wazuh.com/current/user-manual/capabilities/system-inventory/viewing-system-inventory-data.html
[42] Release 4.13.0 — Wazuh, 2025-09-18 (bậc 1). https://documentation.wazuh.com/current/release-notes/release-4-13-0.html
[43] Identifying and Triaging Unmanaged Assets — CrowdStrike Tech Hub, 2024-05 (bậc 1). https://www.crowdstrike.com/tech-hub/exposure-management/identifying-and-triaging-unmanaged-assets/
[44] Query Timeline Chart — Axonius, không rõ ngày (bậc 1). https://docs.axonius.com/docs/query-timeline-chart
[45] IT hygiene use case — Wazuh documentation, không rõ ngày (bậc 1). https://documentation.wazuh.com/current/getting-started/use-cases/it-hygiene.html
[46] Devices in multitenant management in Microsoft Defender XDR — Microsoft Learn, không rõ ngày (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/mto-tenant-devices
[47] Track your Microsoft Secure Score history, metrics, and trends — Microsoft Learn, không rõ ngày (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/microsoft-secure-score-history-metrics-trends
[48] Manage Microsoft Sentinel workspaces at scale — Microsoft Learn, Azure Lighthouse, không rõ ngày (bậc 1, nội dung đọc qua snippet). https://learn.microsoft.com/en-us/azure/lighthouse/how-to/manage-sentinel-workspaces
[49] Extend Microsoft Sentinel across workspaces and tenants — Microsoft Learn, không rõ ngày (bậc 1, nội dung đọc qua snippet). https://learn.microsoft.com/en-us/azure/sentinel/extend-sentinel-across-workspaces-tenants
[50] Multi-tenancy — Wazuh documentation, không rõ ngày (bậc 1). https://documentation.wazuh.com/current/user-manual/wazuh-dashboard/multi-tenancy.html
[51] Azure Workbooks link actions — Microsoft Learn, 2026-04-02 (bậc 1). https://learn.microsoft.com/en-us/azure/azure-monitor/visualize/workbooks-link-actions
[52] NIST SP 800-55 Vol. 1: Measurement Guide for Information Security — Identifying and Selecting Measures — NIST, 2024-12 (bậc 1). https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-55v1.pdf
[53] NIST SP 800-55 Vol. 2: Measurement Guide for Information Security — Developing an Information Security Measurement Program — NIST, 2024-12 (bậc 1). https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-55v2.pdf
[54] Graph visualization: fixing data hairballs — Dan Williams, Cambridge Intelligence, 2019-11-25 (bậc 2). https://cambridge-intelligence.com/how-to-fix-hairballs/
[55] Foundations for OT Cybersecurity: Asset Inventory Guidance for Owners and Operators — CISA và 8 cơ quan đồng ký, 2025-08-13 (bậc 1). https://www.cisa.gov/sites/default/files/2025-08/joint-guide-foundations-for-OT-cybersecurity-asset-inventory-guidance_508c.pdf
