---
title: Asset profile, giao diện asset/user profile và biểu đồ inventory của các vendor security, bài học cho SOC đa tenant trên OCSF 1.9.0
date: 2026-11-03
question: Trong các nền tảng SIEM/XDR/CAASM, asset profile và user profile được xây dựng thế nào, giao diện thể hiện thông tin và tác vụ gì, nên dùng biểu đồ nào ở cấp một asset, inventory tenant và MSSP, và nên thiết kế quản lý tài sản + asset profile cho tenant SOC (dữ liệu OCSF v1.9.0) ra sao?
tags: [asset-management, entity-resolution, dashboard, soc, ocsf, multi-tenant]
---

# Hồ sơ asset hợp nhất có provenance, khoá theo tenant, biểu đồ bấm được

> **Câu hỏi:** Vendor dựng asset/user profile, giao diện profile và biểu đồ (một asset, inventory tenant, MSSP) thế nào, và nên thiết kế quản lý tài sản + asset profile cho SOC đa tenant trên OCSF 1.9.0 ra sao? · **Ngày:** 2026-11-03 · **Phạm vi:** Splunk ES, Google SecOps, Elastic Security, IBM QRadar, Rapid7 InsightIDR, Sumo Logic, Microsoft Defender XDR/Sentinel/Exposure Management, Cortex XSIAM, Trend Vision One, CrowdStrike Falcon, Axonius, Tenable, runZero, Exabeam, Wazuh, Graylog; CIS CAS Control 1/8, CISA CDM AWARE, CISA OT Asset Inventory 2025, NIST SP 800-55 (2024); schema OCSF tag 1.9.0; docs chính thức 2023–2026. · **Kiểm chứng:** khoảng 220 khẳng định đã đối chiếu nguồn (≈ 140 ở phần profile, gồm ≈ 60 tên class/field/enum OCSF đối chiếu schema tag 1.9.0; ≈ 80 ở phần biểu đồ), 21 đã sửa

## Tóm tắt

Các vendor đang hội tụ về cùng một mô hình: **một hồ sơ hợp nhất cho mỗi asset hoặc identity, dựng từ nhiều nguồn quan sát**, mỗi giá trị biết nguồn nào báo và thấy lần cuối khi nào, cộng thêm ba trục điểm tách nhau: criticality do người hoặc rule gán, risk từ alert, exposure từ lỗ hổng và cấu hình. Họ khác nhau chủ yếu ở cách hợp nhất (gộp khi trùng bất kỳ khoá nào, khoá có thứ tự ưu tiên, hay nhóm primary/alias gỡ được), và ở chỗ UI xoay quanh "hồ sơ bền vững" (Microsoft, Elastic, Sumo, Axonius, Tenable) hay "trang điều tra theo thời gian" (Google, Splunk, Exabeam). Ngữ cảnh tài sản được dùng để giảm nhiễu qua ba cơ chế có tài liệu rõ: ma trận severity × priority, hệ số nhân/cộng vào risk score, và đổi baseline theo vai trò hoặc nhóm tài sản. Các con số giảm 30–80% alert đều là tuyên bố của vendor, không có đo lường độc lập. Đa tenant chỉ có QRadar (khoá domain + IP), Splunk (zone + IP) và runZero (site) mô tả rõ cách xử lý IP private trùng nhau. OCSF 1.9.0 cung cấp đủ dữ liệu quan sát (class Inventory, Activity, Finding và `metadata.tenant_uid`), nhưng không có thực thể asset bền vững, và `criticality_id` chỉ nằm trên `resource_details`. Vì vậy sản phẩm cần một kho entity riêng theo tenant cùng một extension OCSF nhỏ. Về trực quan, trang một asset xoay quanh **đường risk score có điểm bấm được để lọc ra các finding đã góp điểm**, dashboard inventory tenant xoay quanh **hàng KPI tile luôn có delta hoặc mục tiêu và các phân bố bấm ra danh sách asset đã lọc**, còn ở cấp MSSP vendor mới có bảng tenant × vài số đếm; biểu đồ dựa trên event lấy thẳng được từ OCSF, biểu đồ trạng thái tài sản theo thời gian thì cần kho entity. Mức chắc chắn về cơ chế là cao (phần lớn từ docs bậc 1). Về hiệu quả giảm nhiễu thì thấp, và về các vendor có docs khoá (CrowdStrike, SentinelOne, Armis, Securonix) cũng thấp.

**Điểm chính**
- Hợp nhất an toàn nhất là khoá có thứ tự ưu tiên, kèm khoá chặn (hai agent ID khác nhau thì không bao giờ gộp), cửa sổ thời gian cho IP, và nhóm primary/alias có unlink và giải thích được [1][2][3][4].
- Criticality hội tụ về **3–4 mức**: gán bằng classifier hoặc rule, khi nhiều rule cùng khớp thì mức cao nhất thắng, ghi đè thủ công có ô ghi lý do, tài sản dưới ngưỡng tự phân loại vào hàng chờ duyệt [5][6][7].
- UI chuẩn de facto: header (định danh, risk, criticality, tag, action) → tab → sidebar thuộc tính và thẻ KPI có "View all". CAASM thêm provenance theo từng trường, UEBA thêm risk trend kèm lý do điểm [8][9][10].
- Giảm nhiễu: Splunk có sẵn risk factor nhân **×1,5** cho đích critical (mặc định tắt), Elastic nhân trọng số **0,5–2** theo criticality, Cortex đẩy alert nhỏ trên asset quan trọng lên. Mức giảm alert 30–80% của Splunk RBA chỉ là tuyên bố vendor [11][12][13][14].
- Đa tenant: mọi khoá entity phải chứa tenant. `metadata.tenant_uid` của OCSF chỉ là *recommended*, nên pipeline phải bắt buộc điền nó [15][16][17].
- OCSF 1.9.0 thiếu thực thể asset bền vững, provenance, lifecycle, coverage theo nguồn, cùng `criticality_id`/`tags` trên `device`. Các bên dùng OCSF (DataBee, AWS, Tenzir) đều tự xây kho entity riêng [18][19][20].
- Risk trend là "xương sống" của trang asset/user ở Cortex, Microsoft, Exabeam, Splunk và Elastic; ba chi tiết lặp lại là điểm bấm được để lọc finding, tín hiệu khối lượng chồng lên đường (bong bóng, counter) và mốc tham chiếu (peer cùng role, ngưỡng nét đứt) [21][10][22][23].
- Drill-down từ segment sang danh sách asset lọc đúng truy vấn của segment là chuẩn chung: runZero cho bấm mọi segment trừ biểu đồ timeline, Axonius ghép base query với query của segment, Microsoft cho bấm donut để sang Devices list [24][25][26].
- Coverage được vẽ bằng bar xếp hạng nguồn kèm tổng unique (Axonius: **19.643** lượt thấy so với **4.787** device unique) và Venn tối đa 3 tập; không vendor nào trong mẫu dùng Sankey hay treemap [27][28].
- Chưa vendor nào làm sparkline telemetry theo từng nguồn trên trang asset, cũng chưa ai có heatmap tenant × KPI cho MSSP; cả hai là cơ hội sản phẩm.

## Vendor hội tụ về "một hồ sơ, nhiều nguồn quan sát" nhưng hợp nhất theo ba kiểu khác nhau

### Từ bảng ngữ cảnh do admin nạp sang inventory tự khám phá từ telemetry

Thế hệ cũ dựa vào bảng ngữ cảnh do admin nạp vào. Splunk ES Asset & Identity poll lookup từ CMDB, AD, LDAP rồi merge các list [29]. Sumo Logic import metadata entity bằng CSV [30]. Elastic import asset criticality bằng CSV [31]. Hướng 2025–2026 là tự khám phá từ dữ liệu đã có. **Splunk Exposure Analytics** (RSAC 2026) khám phá liên tục workstation, server, cloud asset và IoT [32]. Nó tách nguồn "streaming" (DHCP, VPN, EDR: cái gì đang chạy, quan hệ IP–host–user tại một thời điểm) khỏi nguồn "batch" (CMDB, scanner: làm giàu metadata), và dùng source prioritization để giải xung đột [33]. Elastic entity store đối soát entity từ log, IdP, alert và kho asset ngoài, theo từng space [34]. Microsoft Defender dùng chính endpoint đã onboard làm cảm biến khám phá thiết bị unmanaged. Chế độ Standard quét chủ động mỗi thiết bị **không quá một lần mỗi ba tuần**, dưới **50 KB** mỗi lần [35]. Cortex XSIAM "collects, normalizes, and aggregates data from multiple sensors to create a single, holistic profile for each asset" [36]. **Nhận định:** sản phẩm của chủ repo đã có sẵn log OCSF của tenant, nên ở vị trí giống Splunk Exposure Analytics và Elastic: dựng inventory từ telemetry, coi CMDB/IdP chỉ là một nguồn có thứ hạng, không phải nguồn sự thật duy nhất.

| Vendor | Nguồn dựng profile | Khoá định danh / cách hợp nhất | IP động, vòng đời | Criticality | Điểm rủi ro |
|---|---|---|---|---|---|
| Splunk ES | Lookup CMDB/AD/LDAP; Exposure Analytics: CMDB, EDR, DHCP, VPN, scanner [29][33] | Gộp khi trùng bất kỳ `ip`/`dns`/`mac`/`nt_host`; list hạng cao thắng khi xung đột [29] | Lịch sử discovery theo thời điểm [33]; đẩy entity thấy trong **30 ngày**, mỗi **15 phút** [37] | `priority` vào urgency [38] | Entity risk score từ risk event 7 ngày [39] |
| Google SecOps | Log, DHCP, EDR, AD/Workday/Okta, entity context [40][41] | Aliasing DHCP/EDR; ưu tiên alias asset hostname > mac > asset_id > ip [42] | Alias theo thời gian; context có validity interval [43] | Context do admin nạp (entity data, data tables) [44] | max finding + 0,2 × tổng còn lại, chuẩn hoá 1–1000 [42] |
| Elastic Security | Log, IdP, alert, kho asset ngoài [34] | EUID `host.id` > `host.name` > `host.hostname`; resolution group primary/alias [34][3] | Snapshot lịch sử hằng ngày [34] | 4 mức low → extreme [31] | 0–100, nhân 0,5–2 theo criticality, tính lại mỗi giờ [12] |
| IBM QRadar | Flow hai chiều, scanner VA, identity event [45] | Đối soát MAC/NetBIOS/DNS/IP; blocklist dữ liệu "nhảy" [46] | MAC gắn ≥ 3 IP trong 2 giờ → blocklist; retention threshold [46][47] | Không rõ | Không rõ |
| Rapid7 InsightIDR | Event source, agent, network sensor, DHCP [48] | Attribution IP → asset theo thời gian; primary user = user logon nhiều nhất trong tuần [48] | Theo DHCP | Không rõ | Không rõ |
| Sumo Logic | Entity tạo khi signal bắn lần đầu; import CSV [30] | Theo giá trị field entity | Không rõ | Biểu thức severity (`severity+2`) [49] | Activity score = tổng severity trong 2 tuần [49] |
| Microsoft Defender XDR | Agent MDE, network discovery, MDI, Entra, cloud [50][35] | Nhiều account gộp thành một identity có primary account [51] | Tag internet-facing tự bỏ sau **48 giờ** [52] | 4 mức: classifier, custom rule, thủ công [5] | Risk (alert) tách khỏi exposure [8]; identity 0–100 có decay [51] |
| Cortex XSIAM | Nhiều sensor, Workday, AD [36][13] | Gộp điểm theo đúng hostname/username [13] | Active 0–3 → Not Seen 3–5 → Lost 5–7 ngày → ẩn [36] | Asset Roles tự phân loại [53] | Tổng điểm case/alert, thường 10–100 [13] |
| Trend Vision One | Các nguồn đã kết nối [7] | Không rõ | Không rõ | 3 mức từ profile tag, đánh giá hằng ngày [7] | Tính lại mỗi 4 giờ trên 30 ngày [54] |
| CrowdStrike Falcon | Sensor khám phá unmanaged, ServiceNow [6] | Không rõ (docs khoá) | Managed / Unmanaged / Unsupported | Critical/High/Noncritical/Unassigned + lý do [6] | Không rõ |
| Tenable EM | Sensor Tenable và connector bên thứ ba [1] | External ID → MAC → tổ hợp Name/FQDN/IP; UUID khác nhau không bao giờ gộp [1] | Không rõ | ACR 1–10 [55] | AES 0–1000 [55] |
| runZero | Scan, integration [2] | MAC → IP (cửa sổ 3 ngày) → hostname, chỉ trong cùng site [2][56] | Offline nếu vắng ở lần scan gần nhất [56] | Không rõ | Outlier score 0–5 [56] |
| Axonius | Adapter (EDR, AD, CMDB, cloud…) [9] | Tự gộp; có Explain Correlation / Non-Correlation [4] | Không rõ | Tag có ngày hết hạn [9] | Không rõ |
| Exabeam | LDAP, log, CSV zone [57] | Host-to-IP mapping, trễ tới 2 giờ [58] | Theo session | Label executive/privileged, asset group [10][57] | anchor × anomaly factor; notable ≥ 90 [10][59] |
| Wazuh | Agent (Syscollector) [60] | Agent ID, một nguồn | Không rõ | Không có | Không có |

### Ba kiểu hợp nhất thực thể, và kiểu nhóm primary/alias gỡ được là an toàn nhất

Kiểu thứ nhất là **gộp khi trùng bất kỳ khoá nào**. Splunk A&I coi hai dòng là cùng asset khi một trong `ip`, `dns`, `mac`, `nt_host` trùng nhau [29]. Cách này dễ gộp nhầm, nên Splunk phải cho tắt merge toàn cục khi file nguồn có khoá trùng mà không làm sạch được [61]. Kiểu thứ hai là **khoá có thứ tự ưu tiên**. Tenable thử lần lượt External Identifier → MAC → Name+FQDN+IP → … → Name, và đặt hai ràng buộc cứng: "Assets with different Tenable UUIDs will never be merged" và "Assets must belong to the same class to be merged" [1]. runZero khớp MAC → IP trong **cửa sổ 3 ngày** → hostname, và chỉ ghép trong cùng một site [2][56]. Elastic chỉ tạo entity khi đủ dữ liệu để sinh EUID ổn định. User từ các IdP khác nhau có namespace riêng, còn user từ EDR được coi là "medium-confidence local user" gắn với host [34]. Kiểu thứ ba là **nhóm resolution gỡ được**. Elastic (GA 9.4) giữ bản ghi gốc, gom chúng vào một group có primary entity (ưu tiên entity từ IdP) và các alias trỏ về qua `resolved_to`. Tự động resolve chỉ dựa vào email, link thủ công làm qua CSV hoặc flyout, còn bulk unlink chỉ có qua API [3]. Microsoft gộp nhiều account (AD, Entra, SaaS) thành một identity có primary account và cho analyst link thêm bằng tay [51]. Axonius có nút **Unlink Device** trên header profile [9].

IP động được xử lý bằng chỉ mục theo thời gian. Google lấy liên kết hostname–MAC–IP từ DHCP ACK/OFFER/RELEASE, và lấy liên kết product ID–hostname từ EDR [40]. Rapid7 "model the relationship between IP addresses and assets over time" và tự nhận đây là "best-effort algorithm that is not guaranteed to be accurate" [48]. QRadar đi theo hướng phòng thủ: dữ liệu có hành vi đáng ngờ từ hai lần trở lên trong **2 giờ** (ví dụ một MAC gắn với **≥ 3 IP**) bị đưa vào blocklist và không được áp vào asset DB, và có allowlist cho dữ liệu hợp lệ [46]. QRadar cũng cảnh báo hiện tượng "asset growth deviation", khi asset mới sinh nhanh hơn tốc độ dọn hoặc một asset tích tụ quá nhiều identity [47]. Axonius cho thấy "confidence" ngầm định khi giải thích vì sao hai bản ghi *không* được ghép. Mỗi identifier ra một trong các kết quả: Contradiction, Missing Values, hoặc khớp nhưng không đủ (giá trị yếu, placeholder, quá ngắn, bị loại khi chuẩn hoá) [4].

![Tenable Asset Cluster Logic hiển thị tiêu chí và giá trị đã khiến các nguồn được ghép](https://docs.tenable.com/exposure-management/Content/Resources/Images/Local/exposure-management/asset-cluster-logic.png)
*Tenable – Asset Cluster Logic: tiêu chí khớp (hostname, IP, MAC) và giá trị cụ thể đã kích hoạt mỗi lần ghép một tài sản đa nguồn. Nguồn: [55]*

![Axonius Explain Correlation hiển thị chuỗi ghép giữa hai adapter qua bản ghi trung gian](https://files.readme.io/5c066413acf4f063e0f6de1bd5b0bdeb1b864017af5625e8c4c7d45eeb1e0dc0-image.png)
*Axonius – Explain Correlation: chuỗi từng bước nối hai adapter, có thể đi qua bản ghi trung gian, mỗi bước ghi ngày khớp. Nguồn: [4]*

### Provenance theo trường và ưu tiên nguồn quyết định giá trị hiển thị

CAASM là nhóm làm phần này kỹ nhất. Tenable dùng "a fixed priority order to determine which value appears in the unified view": nguồn native đứng trước, rồi đến connector bên thứ ba theo thứ tự kết nối. Thứ tự này xem được qua "Show information order" và chỉnh được ở Settings > Information Order Configuration [1][55]. Axonius chia field thành Aggregated (gộp từ mọi adapter), Preferred (giá trị đại diện, ví dụ preferred OS), Specific (chỉ thuộc một adapter) và Common. Mỗi hàng trong bảng field có cột adapter đã cung cấp, và mở rộng ra được giá trị của từng nguồn kèm raw JSON [9]. Splunk Exposure Analytics giải xung đột kiểu "nguồn có IP mới nhất" và "nguồn có owner tin cậy" bằng source prioritization, có field aging rule để xoá giá trị cũ [33][16]. Cả Splunk lẫn Elastic đều cảnh báo dữ liệu ngữ cảnh cũ. Splunk nói chế độ trộn có thể gộp dữ liệu discovery với A&I cũ hoặc sai [37]. Elastic yêu cầu clear entity store khi đổi chuẩn hoá `host.name`/`user.name` [34]. **Nhận định:** đây là lý do nên tách thuộc tính *quan sát* (dựng lại được từ log) khỏi thuộc tính *do người gán* (criticality, owner, tag, ghi chú), để rebuild không làm mất công sức của analyst.

![Tenable Information order: thứ tự ưu tiên nguồn khi lấy giá trị thuộc tính](https://docs.tenable.com/exposure-management/Content/Resources/Images/Local/exposure-management/property-merge-order.png)
*Tenable – Information order: thứ tự nguồn được dùng để chọn giá trị hiển thị cho từng thuộc tính của tài sản hợp nhất. Nguồn: [55]*

![Axonius tooltip liệt kê các adapter connection đã cung cấp một trường](https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/AdapterConnectionsHover.png)
*Axonius – Provenance theo trường: hover trên một trường để thấy những adapter connection nào đã báo giá trị đó. Nguồn: [9]*

### Vòng đời dùng ngưỡng last seen khác nhau theo loại tài sản

Cortex dùng ngưỡng ngắn: **Active 0–3 ngày → Not Seen 3–5 → Lost 5–7**, sau 7 ngày bị ẩn khỏi bảng [36]. Splunk đẩy vào A&I các entity thấy trong **30 ngày**, ngưỡng chỉnh được, và báo Fail khi nguồn discovery vượt health window **1 ngày** [37][62]. DataBee (kho entity trên OCSF) cho virtual asset age-out sau **7 ngày**, còn user, thiết bị vật lý, application và cloud resource sau **1 năm** [20]. runZero đánh dấu offline khi tài sản vắng mặt ở lần scan gần nhất [56]. Microsoft lưu ý "the device profile doesn't consider all cyber evidence when determining the 'Last Seen' timeframe" [52]. **Nhận định:** ngưỡng phải tuỳ theo lớp tài sản (container/VM tự scale khác laptop, khác DC), và "last seen" phải tính theo từng nguồn chứ không chỉ một giá trị tổng.

## Criticality hội tụ về 3–4 mức, gán bằng rule, ghi đè có lý do và hàng chờ duyệt

Thang mức khá giống nhau giữa các vendor: Microsoft Very High/High/Medium/Low [5], Elastic low/medium/high/extreme_impact [31], CrowdStrike Critical/High/Noncritical/Unassigned [6], Trend High/Medium/Low [7], Tenable ACR 1–10 [55]. Microsoft có cơ chế gán hoàn chỉnh nhất. Gồm ba lớp: classifier định sẵn (domain controller, file server, database có dữ liệu nhạy cảm, Privileged Role Administrator, tài nguyên Azure/AWS/GCP), custom query bằng query builder Boolean có preview tài sản bị ảnh hưởng, và gán thủ công. Khi nhiều rule cùng khớp, "the rule with the highest criticality level takes precedence". Asset hết khớp rule thì tự về mức của rule kế tiếp. Tài sản khớp classifier nhưng chưa đạt ngưỡng tự phân loại vào hàng chờ **Pending Approval** [5][63]. Microsoft khuyến nghị dùng rule rộng thay vì gán tay từng máy, và cảnh báo attack path "might not be fully representative" nếu critical asset chưa được định nghĩa đủ [5][64]. CrowdStrike có ô "Reason for assignment" (tuỳ chọn, tối đa 300 ký tự) và có link "Create rule using these asset filters" để biến một bộ lọc thành rule [6]. Trend ghi rõ nguồn của mức criticality (system hay Custom), cho phép sửa hàng loạt và quay về mức hệ thống bất kỳ lúc nào [7]. Cortex Asset Roles tự phân loại theo hành vi (Domain Controller, Administrator, Executive User, Honey user), cho ghi đè và import CSV. Role được dùng làm baseline cho analytics, để so sánh peer, và làm tag family để lọc alert [53].

Ba trục được giữ tách nhau. Microsoft: "Exposure level relates to how much the device is complying with security recommendations, while risk level is calculated based on ... active alerts" [8]. Identity risk của Microsoft tách *likelihood* (alert theo chặng kill chain) khỏi *impact* (criticality, Global Admin, vai trò PIM), có decay, và có action "Confirm safe" [51]. Trend nói "Two assets with the same risk events and different criticality levels are not assigned the same risk scores" [7].

![Microsoft Exposure Management: tạo custom critical asset classification bằng query builder](https://learn.microsoft.com/en-us/security-exposure-management/media/classify-critical-assets/create-critical-asset-classification.png)
*Microsoft Security Exposure Management – Tạo critical asset classification: query builder với điều kiện Boolean theo device/identity/cloud resource để định nghĩa rule criticality. Nguồn: [5]*

![Microsoft Exposure Management: trang Critical asset management với các classification](https://learn.microsoft.com/en-us/security-exposure-management/media/classify-critical-assets/critical-asset-management-window.png)
*Microsoft Security Exposure Management – Critical asset management: danh sách classification định sẵn và custom, số asset khớp, bật/tắt và mức criticality từng rule. Nguồn: [5]*

![CrowdStrike Falcon: hộp thoại Assign asset criticality](https://www.crowdstrike.com/wp-content/uploads/2024/05/femiatua8.png)
*CrowdStrike Falcon – Assign asset criticality: chọn Critical/High/Noncritical/Unassigned, ô "Reason for assignment (optional)" (0/300) và link "Create rule using these asset filters". Nguồn: [6]*

## Giao diện profile: header bền vững cộng tab điều tra theo thời gian

### Asset/device profile: khung header → tab → sidebar + thẻ KPI

Microsoft đã chuẩn hoá một khung dùng chung cho device, identity và IP. **Header** gồm tên, các chỉ báo risk severity, criticality, device value, tag (từ MDE, MDI hoặc người dùng) và response actions. **Dãy tab** gồm Overview, Incidents and alerts, Timeline, Security recommendations, Inventories, Discovered vulnerabilities, Missing KBs, Sentinel events… **Overview** có sidebar thu gọn được (VM details, Cloud resource details, Hardware, Directory data) và lưới thẻ: Active alerts trong **180 ngày** cùng Risk level, Exposure level, Logged on users trong **30 ngày**, Device health [8]. Timeline mặc định 30 ngày, export tối đa 7 ngày ra CSV, có nút "Hunt for related events". Từ 01/2025 timeline gộp cả activity của Sentinel [8]. Action có cả Set criticality, Manage tags và **Report device inaccuracy**, tức analyst phản hồi được khi phân loại sai [8][52]. Sentinel trên Azure portal dùng bố cục 3 cột (info, timeline, insights) và có Watchlist insights [65]. Sentinel trên Azure portal ngừng hỗ trợ sau 31/03/2027 [65].

Bảng dưới so các khối thông tin trên asset profile. ✓ là có trong docs, "—" là không thấy trong nguồn đã đọc (không có nghĩa là sản phẩm không có).

| Vendor | Header: risk/criticality/tag | Thuộc tính + first/last seen | Provenance nguồn | Alert/case liên quan | Timeline | Phần mềm/lỗ hổng | User liên quan | Quan hệ/graph | Notes/audit | Hành động |
|---|---|---|---|---|---|---|---|---|---|---|
| Defender XDR [8] | ✓ | ✓ | onboarding/discovery | ✓ 180 ngày | ✓ | ✓ | ✓ logged-on | attack path | — | ✓ isolate, live response… |
| Elastic [23] | ✓ (9.4+) | ✓ observed attributes | resolution | top 10 alert | qua Timeline | vuln (host) | — | graph 30 ngày | — | Add to case |
| Sumo Logic [30] | ✓ | metadata, inventory | — | signal/insight | ✓ 3 ngày | — | related entities | — | ✓ notes + audit log | suppress, create insight |
| Google SecOps [66] | — | IP/MAC theo thời gian, first seen | — | ✓ | ✓ prevalence | — | — | domain prevalence | — | lọc procedural |
| Splunk ES [67] | asset description | ✓ | — | notable | swim lane heat map | — | — | graph (8.5) | — | Create notable |
| Axonius [9] | tag | ✓ | ✓ theo trường | — | snapshot theo ngày | CIS | — | Asset Graph | ✓ notes | ticket, enforce, unlink |
| Tenable [55] | ACR/AES | ✓ | ✓ cluster logic | findings | exposure signals 7 ngày | ✓ | accounts/users | relationships, attack path | — | export, AI summary |
| Cortex XSIAM [68] | score + delta | ✓ panel | — | cases | risk trend | CVE | — | — | — | actions, star |
| Trend Vision One [54] | ✓ hover card | ✓ | — | risk event | — | local apps | ✓ kèm risk | asset risk graph | — | exception, response |
| Exabeam [58] | điểm session | ✓ top user | — | badge alert | ✓ smart timeline | — | ✓ | — | — | create incident |
| Rapid7 [69] | — | local accounts | — | related alerts | — | vuln (InsightVM) | primary asset | lateral movement | — | download PDF |

![Microsoft Defender XDR device page, tab Overview](https://learn.microsoft.com/en-us/defender-xdr/media/entity-page-device/entity-device-overview-tab.png)
*Microsoft Defender XDR – Device entity page, tab Overview: header có risk "High", "Criticality: None", tag, nút Device value/Set criticality; sidebar VM details (domain, OS, health, IP, first/last seen); thẻ Active alerts/Risk level, Exposure level, Logged on users. Nguồn: [8]*

![Microsoft Sentinel entity page bố cục 3 cột](https://learn.microsoft.com/en-us/azure/sentinel/media/entity-pages/entity-page-sentinel.png)
*Microsoft Sentinel – Entity page (Azure portal): thông tin định danh bên trái, timeline alert/bookmark/anomaly/activity ở giữa, insights bên phải. Nguồn: [65]*

Elastic gom profile vào một **flyout** trượt từ phải, có thể mở từ bảng alert, trang Entity analytics hoặc trang Users/Hosts. Các section xếp dọc, thu gọn được: header (gán criticality ngay tại chỗ, từ 9.4), Entity summary do AI viết (9.3), Risk score kèm history từng lần tính (bấm một điểm để xem Contexts/Alerts của lần tính đó, 9.5), Behavioral anomalies ánh xạ MITRE, graph 30 ngày, Resolution, Insights (vuln, misconfig), Observed attributes. Từ 9.5 có thêm nút Take action → Add to case [23]. Docs Elastic không có ảnh flyout 9.4+. Ảnh dưới là trang Host details kiểu cũ [70].

![Elastic Security trang Host details](https://www.elastic.co/docs/solutions/images/security-hosts-detail-pg.png)
*Elastic Security – Host details (UI cổ điển): summary gồm host ID, first/last seen, IP, OS, host risk score; alert metrics theo severity/rule/status; các data table lọc theo host. Nguồn: [70]*

Sumo Logic là vendor duy nhất trong nhóm SIEM đặt **Notes** và **Audit Log** ngay trên entity, kèm slider suppression, tags, criticality, indicators, metadata, network blocks, inventory. Khu chính có tab Activity, Enrichments, Timeline 3 ngày, Related Entities, Automations, cùng danh sách signal có checkbox để Create Insight thủ công [30].

![Sumo Logic Cloud SIEM Entity Details của một host](https://www.sumologic.com/help/img/cse/entity-details-new-host.png)
*Sumo Logic Cloud SIEM – Entity Details (host): cột trái là suppression, tags, criticality, indicators, metadata, inventory, notes, audit log; khu chính là timeline, related entities và danh sách signal để tạo insight. Nguồn: [30]*

Google SecOps Asset view là trang điều tra theo thời gian. Bạn tìm theo hostname, IP hoặc MAC cùng một timestamp, cửa sổ mặc định 2 giờ. Trung tâm trang là prevalence graph: domain hiếm nổi lên trên, vòng xám là kết nối lần đầu, tam giác đỏ là alert. Bên cạnh là các khối insight: Forwarded alerts, Newly registered domains (≤ 30 ngày), Domains new to the enterprise, Low prevalence domains (≤ 10). Prevalence tính trên 7 ngày [66].

![Google SecOps Asset view: các khối Asset insight](https://docs.cloud.google.com/static/chronicle/images/asset-insight-blocks.png)
*Google SecOps – Asset view, Asset insight blocks: các khối forwarded alerts, newly registered domains, domains new to enterprise, low prevalence đặt cạnh timeline của asset. Nguồn: [66]*

Splunk ES Asset Investigator xếp chồng các swim lane, mỗi lane là một heat map mật độ sự kiện gắn với một data model (authentication, malware, notable…). Phía trên là asset description để xác nhận đúng máy, phía dưới là Event Panel với Go to Search và Create Notable Event [67]. ES 8.5 thêm Entity analysis dashboard với các tab health, activity, risk, network associations cùng graph explorer [71]. Không tìm được ảnh UI 8.x công khai. Ảnh duy nhất là ngữ cảnh A&I trong blog năm 2020.

![Splunk ES ngữ cảnh asset từ framework Asset & Identity (ảnh 2020)](https://www.splunk.com/content/dam/splunk-blogs/images/media_1740d4f15dc5d96133b8142263a74f0bca47d8bb1.webp)
*Splunk ES – Ngữ cảnh asset A&I (ảnh cũ, trước ES 8.x): asset titan.thirstyberner.com kèm city San Francisco, category Active Directory/Windows, bunit IT, IP 10.1.1.10. Nguồn: [29]*

Axonius và Tenable (CAASM) đặt **bảng thuộc tính hợp nhất có provenance** vào trung tâm. Axonius có header gồm tên và 2 trường phụ, thanh action Tag/Add Custom Field/Create Ticket/Enforce/Unlink. Pane trái là "mục lục nguồn" (Adapter Connections, Tags có ngày hết hạn, Custom Data). Vùng chính là bảng field–value–sources. Các tab khác gồm CIS, Enforcement Runs, Tickets, Notes, Asset Investigation (thay đổi theo thời gian), Asset Graph [9]. Tenable có header gồm tên, asset class, số đếm theo exposure category và nút Summarize bằng AI, sau đó là Key Properties (Owner, Location, Last Observed, ACR, AES) và một dãy tab dài: Connectors Details kèm raw data, Weaknesses, Findings, Software, Relationships, Attack Paths, Exposure Signals [55].

![Axonius Asset Profile drawer mở từ bảng Assets](https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/img/asset_profile/AssetProfileDraweronAssetsPage.png)
*Axonius – Asset Profile drawer: mở từ bảng Assets, gồm header và thanh hành động, pane trái liệt kê nguồn và tag, bảng trường hợp nhất ở giữa. Nguồn: [9]*

![Tenable Exposure Management trang Asset Details](https://docs.tenable.com/exposure-management/Content/Resources/Images/Local/exposure-management/asset-details.png)
*Tenable Exposure Management – Asset Details: header với asset class và số đếm theo exposure category, Key Properties và dãy tab dữ liệu. Nguồn: [55]*

Exabeam (UEBA) bố trí profile theo chiều dọc và xoay quanh rủi ro theo thời gian. Asset Directory Information (IP, labels, first/last seen, **Top User**, badge số alert bên thứ ba) → Asset Risk Trend → Risk Reasons (hiện icon các user rủi ro cao đã tương tác) → Asset Timeline. Exabeam lưu ý timeline chỉ cập nhật sau khi đã xử lý host-to-IP mapping, nên có thể trễ tới **2 giờ** [58].

![Exabeam Asset Directory Information](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-75d91051-bd0e-eada-5417-7f45601f4e11.jpg)
*Exabeam – Asset page, Asset Directory Information: IP, labels, first/last seen, top user, badge alert bên thứ ba và điểm sequence gần nhất. Nguồn: [58]*

Wazuh là inventory một nguồn. Module Syscollector của agent thu phần cứng, OS, package, process, service, port, user, group và browser extension, đưa vào trang IT Hygiene. Không có hợp nhất đa nguồn hay provenance [60].

![Wazuh IT Hygiene dashboard inventory endpoint](https://documentation.wazuh.com/current/_images/inventory-data-dashboard1.png)
*Wazuh – IT Hygiene / Inventory data: dashboard inventory của endpoint lấy từ Syscollector (phần cứng, OS, package, port, process). Nguồn: [60]*

Các vendor không có ảnh công khai được mô tả bằng lời dưới đây. **Cortex XSIAM Host Risk View** (cần ITDR add-on): header gồm định danh, risk score và mức thay đổi trong kỳ. Tiếp theo là hàng widget highlight bấm được (Case Breakdown theo severity, CVEs Breakdown, MITRE ATT&CK Overview). Tab Risk Assessment có đường Risk Score Trend với bong bóng số issue theo ngày và chế độ "Compare To" theo asset role, trong đó đường đứt nét là trung bình của peer. Bảng Cases có cột Status giải thích vì sao điểm đổi. Tab Activities gồm Failed Logins và Login Attempts. Star để đưa host vào watchlist [68]. **Trend Vision One device profile**: hover card trên tên hiện score, criticality và significant profile tags. Các tab gồm Risk Assessment (score 30 ngày, risk indicators kèm rule giảm thiểu), Asset Risk Graph (bấm mũi tên xem first/last time kết nối), Local Apps, Users (kèm risk score từng người), Asset Profile (Manage Tags, Modify Criticality) [54]. **Rapid7 InsightIDR Asset Details**: Local Accounts từ Insight Agent, lateral movement graph, bản đồ Ingress Locations [69]. **IBM QRadar**: tab Assets hiển thị lỗ hổng, port, ứng dụng và lịch sử, còn Asset Profile có Vulnerabilities pane. Docs IBM chặn truy cập trực tiếp nên không có mô tả bố cục [45].

**Nhận định:** hai kiểu UI bổ sung cho nhau. "Hồ sơ bền vững" (Microsoft, Elastic, Sumo, Axonius, Tenable) trả lời câu hỏi *tài sản này là gì, ai biết về nó, quan trọng đến đâu, thiếu gì*. "Trang điều tra theo thời gian" (Google, Splunk, Exabeam) trả lời *nó đang làm gì bất thường*. Asset profile cho SOC cần header bền vững cộng tab timeline/prevalence. Các chi tiết đáng chép: mọi thẻ có "View all…" và có link mở query gốc; điểm số phải có lý do (cột Status của Cortex, "factors influencing priority" của Microsoft); có nút báo sai.

### Danh sách inventory và thao tác hàng loạt

Defender device inventory có các tab theo loại (Computers & mobile, Network devices, IoT/OT, Uncategorized) và các "count pills": total, critical assets, high risk, high exposure, not onboarded, newly discovered. Bộ lọc dùng cho vận hành gồm Onboarding status = "Can be onboarded", Managed by = Unknown, Sensor health = Inactive/Misconfigured [50]. Sumo Entities có bộ lọc theo activity score, criticality, sensor zone, suppressed, tags. Nút Import Metadata (CSV) và checkbox cho phép Change Tags/Suppression/Criticality hàng loạt. Criticality còn quản lý được bằng Terraform [30][49]. Axonius thêm cột Adapter Connections dạng icon nguồn, nhìn vào là biết thiết bị đang thiếu nguồn nào [72].

![Sumo Logic Cloud SIEM trang Entities](https://www.sumologic.com/help/img/cse/entities-page-2.png)
*Sumo Logic Cloud SIEM – Entities list: bộ lọc, nút Import Metadata, checkbox sửa hàng loạt, các cột activity score, signal severity total, suppressed lists và criticality. Nguồn: [30]*

### User/identity profile: danh tính hợp nhất, heat map hoạt động và điểm có giải thích

User profile có cùng khung với device page, cộng ba phần riêng. Phần thứ nhất là **danh tính hợp nhất**. Tab "Observed in organization" của Defender liệt kê Accounts (đánh dấu primary, cho link tay), Devices, Locations, Groups. Timeline gộp 8 bảng (AlertInfo, IdentityLogonEvents, EntraIdSignInEvents…) và khử trùng: khi một sign-in có ở cả Entra lẫn cloud app thì ưu tiên bản ghi Entra [51]. Google gộp `dennis` và `dennis@altostrat.com` thành một user [41]. Phần thứ hai là **nhịp hoạt động**. Google User view có gradient heat map 7 ngày × 24 giờ UTC để phát hiện hoạt động lúc 3 giờ sáng, nút nhảy tới First/Last Seen, và tab Assets liệt kê thiết bị của user trong khoảng thời gian [41]. Exabeam có Data Insights (top 5 workstation, zone, quốc gia, giờ hoạt động) và Smart Timeline theo session [10]. Phần thứ ba là **rủi ro có giải thích**. Exabeam ghi cho mỗi risk reason: model confidence, tag MITRE và công thức "the anchor score multiplied by the anomaly factor" [10]. Defender tách likelihood khỏi impact và hiển thị percentile so với toàn tổ chức [51]. Header của Defender có các action lên tài khoản: disable, revoke sessions, force password change, mark as compromised. Panel Protection gồm MFA status và last password change [51].

![Google SecOps User view đánh số 1–7](https://docs.cloud.google.com/chronicle/images/user-view-numbered.png)
*Google SecOps – User view: (1) user info từ AD/Workday/Okta, (2) chọn tuần và nhảy First/Last Seen, (3) time shift, (4) heat map theo giờ, (5) user alerts, (6) tab Timeline/Assets, (7) tuỳ chỉnh cột. Nguồn: [41]*

![Microsoft Defender XDR Identity page tab Overview](https://learn.microsoft.com/en-us/defender-xdr/media/investigate-users/identity-page.png)
*Microsoft Defender XDR – Identity page, tab Overview: header có UPN, trạng thái, action "Mark as compromised"; panel Entity details chia Protection (MFA, last password change) và User threat (insider risk, blast radius, UEBA anomalies, risk score); thẻ incidents và thiết bị logon tương tác. Nguồn: [51]*

![Microsoft Defender XDR Identity page tab Observed in organization](https://learn.microsoft.com/en-us/defender-xdr/media/investigate-users/identity-observed-in-organization.png)
*Microsoft Defender XDR – Identity page, Observed in organization: các account đã hợp nhất (đánh dấu primary), devices, locations và groups của một identity. Nguồn: [51]*

![Exabeam User General Information](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-cb33dad9-918f-2707-97ac-cedb4c8433a2.png)
*Exabeam – User profile, General Information: title, department, manager, top peer group, labels (executive, privileged), first/last seen và risk score session gần nhất. Nguồn: [10]*

![Exabeam Risk Reasons](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-7bd36e84-66b7-6a0c-8c35-10f1f457dc6f.png)
*Exabeam – Risk Reasons: danh sách sự kiện góp điểm vào session, kèm model confidence và tag MITRE ATT&CK. Nguồn: [10]*

Cortex XSIAM User Risk View có panel phải hiện title, department, primary location, endpoint, last activity và tags. Ngoài ra có working hours và heatmap Issues & Insights [73]. Rapid7 User Details hiện số lỗ hổng đang mở trên từng asset của user, tag Primary Asset, Search Related Logs (mặc định 1 giờ qua), Related Alerts có toggle Include Actor, và nút Download PDF [69]. Rapid7 xác định primary user bằng số lần đăng nhập trong tuần [48], còn OCSF định nghĩa `endpoint.owner` là người "owns the endpoint **or was last logged into it**" [74]. **Nhận định:** "owner" (ai chịu trách nhiệm, lấy từ CMDB/HR) và "top/last user" (ai đang dùng, suy ra từ authentication) phải là hai trường khác nhau trên profile.

## Ngữ cảnh tài sản giảm nhiễu bằng ma trận, hệ số và đổi baseline; số liệu hiệu quả chỉ là tuyên bố vendor

Có ba cơ chế có tài liệu rõ. Cơ chế thứ nhất là **ma trận**. Urgency của notable trong Splunk ES là tổ hợp severity × priority của asset/identity, lấy giá trị priority cao hơn nếu cả hai cùng có. Asset priority unknown/low thì severity high chỉ ra urgency medium. Asset critical thì severity high đã ra urgency critical. Bảng ma trận là một lookup sửa được [38]. Cơ chế thứ hai là **hệ số**. Risk factor của Splunk chạy các phép cộng trước rồi mới đến phép nhân, có factor dựng sẵn "if the dest_priority field value is 'critical', the risk factor is multiplied by **1.5**", nhưng mọi factor có sẵn đều "turned off" cho tới khi bật [11]. Docs còn nêu ví dụ tự cấu hình: user trong watchlist cộng asset critical thì nhân **1,2** [75]. Elastic nhân trọng số **Low 0,5 / Medium 1 / High 1,5 / Extreme 2** ("subject to change") và tách phần đóng góp thành category "Asset Criticality". Ví dụ trong docs: Alerts 36,16 cộng Asset Criticality 16,95 ra **53,11 (Moderate)** [12]. Sumo dùng biểu thức như `severity+2` [49]. Graylog tính event risk từ severity, priority của rule và priority của asset, và **không có asset liên kết thì không tính event risk score** [76]. Cơ chế thứ ba là **đưa ngữ cảnh vào lúc phát hiện, hoặc đổi baseline**. Google context-aware analytics đưa context vào "at detection execution time" để lọc "entire clusters of threats that may be expected", ví dụ sandbox/dev network không có dữ liệu nhạy cảm. Context có validity interval, và event chỉ join được khi timestamp nằm trong khoảng hiệu lực [43]. Exabeam mô hình asset group (vd cụm Exchange cân bằng tải) như một thực thể để "reduces the amount of false positives", phân loại server/workstation theo OS hoặc OU [57], và chấm cao hơn khi non-executive truy cập workstation của executive hoặc khi service account đăng nhập interactive [77]. Peer group của Exabeam khởi đầu từ thuộc tính AD, nhưng blog năm 2016 cho biết mỗi thuộc tính chỉ phủ **50–90%** user, nên họ dùng peer động có degree of membership [78]. Cortex SmartScore: "a critical alert on an asset with a low risk score might be given a lower overall SmartScore, while minor alerts on highly critical assets might be elevated" [13]. Microsoft đưa asset criticality vào priority score 0–100 của incident (đỏ > 85, cam 15–85, xám < 15) cùng với các yếu tố khác, hiển thị "factors influencing the priority score", nhưng không công bố trọng số [79][80].

Không vendor nào công bố trọng số criticality trong công thức ML, và cũng không có nghiên cứu độc lập nào đo hiệu quả. Các con số của Splunk là **tuyên bố vendor** và lệch nhau giữa các tài liệu: blog ES 6.4 nói giảm **60–80%** khối lượng alert (trang này nay trả 404, con số chỉ còn đối chiếu được qua trích đoạn search) [81]. "The Splunk Guide to RBA" ghi **30–80%**, với chú thích con số lấy từ một testimonial [14]. Case study Johnson Matthey ghi fidelity +30% và thời gian xử lý case −83% [82]. Một blog nói true positive rate của một khách hàng tăng từ dưới 10% lên trên 30% [83]. Chính Splunk cũng thừa nhận RBA chưa được curate "can generate as many notables as traditional alerting", và khuyên dedup, rút cửa sổ từ 24h xuống 12h, tinh chỉnh các hoạt động dự đoán được [84].

![Elastic Security: bảng alert nhóm theo asset criticality](https://www.elastic.co/docs/solutions/images/security-group-by-asset-criticality.png)
*Elastic Security – Alerts group by asset criticality: bảng alert được nhóm theo mức criticality của host/user để triage theo giá trị tài sản. Nguồn: [85]*

![Microsoft Defender XDR incident queue với priority score](https://learn.microsoft.com/en-us/defender-xdr/media/incidents-queue/incidents-page.png)
*Microsoft Defender XDR – Incident queue: hàng đợi incident có cột priority score 0–100, trong đó asset criticality là một yếu tố đầu vào. Nguồn: [79]*

Suppression có một bài học ngược. "Accept Session" của Exabeam whitelist vĩnh viễn hành vi cho user/asset, không hoàn tác được, và chính Exabeam khuyên tune rule thay vì accept [10]. Tag của Axonius thì có ngày hết hạn [9]. **Nhận định:** cơ chế (b) chỉ xếp hạng lại, còn cơ chế (c) giảm nhiễu từ gốc. Sản phẩm nên có cả hai, và suppression theo lớp tài sản (scanner, jump host, build server) phải dựa trên role/tag của profile, có lý do, người duyệt, hạn và audit, không phải exception cứng theo IP.

## Vận hành, phòng thủ và đa tenant: phân biệt "không có alert" với "không có dữ liệu", và khoá phải chứa tenant

### Coverage, health và gap query

Có ba cách giám sát "asset im lặng". Cách thứ nhất là rule hoặc metric absence. Google SecOps silent-host monitoring gắn ingestion label theo `host.name` rồi đặt alert Cloud Monitoring khi log count xuống dưới ngưỡng. Phương án dashboard trễ tới **6 giờ** và không alert được [86]. Theo trích đoạn, rule YARA-L mẫu báo khi host vắng event trong 10 phút gần nhất nhưng vẫn có event trong 20 phút [87]. Cách thứ hai là bảng health của connector: workbook "Data collection health monitoring" của Sentinel có tab Overview (volume, EPS, last log), Anomalies (`series_decompose_anomalies()`) và Agent info, nhưng bảng `SentinelHealth` chỉ hỗ trợ một số connector [88]. Cách thứ ba là cột sensor health trong inventory: Defender lọc theo Sensor health, Managed by, Antivirus status [50][89]. CAASM biến coverage thành **gap query** trên bản ghi đã hợp nhất. Axonius có `OS = Windows AND CrowdStrike Agent ID does not exist`, biến thể "agent có nhưng CrowdStrike last seen > 30 ngày trong khi AD thấy trong 7 ngày", rồi chuyển kết quả sang Enforcement Center (deploy agent, báo owner, mở ticket) với lịch chạy liên tục [72]. CIS cung cấp KPI dùng được ngay: Safeguard 8.2 có Coverage = M2/M1 (asset được cấu hình log đúng / asset có khả năng log) [90]. Safeguard 1.1 có Accuracy = M3/M2, M4 = có trong inventory mà discovery không thấy (stale), M5 = discovery thấy mà không có trong inventory (unknown), và review "bi-annually, or more frequently" [91].

![Axonius gap query: thiết bị CrowdStrike lâu không check-in](https://images.contentstack.io/v3/assets/blt309b1de7d109902d/blt3f5b277a70d3e42e/6839c6eb116bcf82b521d22f/AX_DetectGaps_EP_Blog_Product01_1600x900_%281%29.png)
*Axonius – Gap query: truy vấn thiết bị có agent CrowdStrike nhưng lâu không check-in trong khi nguồn khác vẫn thấy thiết bị. Nguồn: [72]*

![Microsoft Sentinel Data collection health workbook, tab Overview](https://learn.microsoft.com/en-us/azure/sentinel/media/monitor-data-connector-health/data-health-workbook-1.png)
*Microsoft Sentinel – Data collection health workbook, Overview: volume, EPS và thời điểm nhận log cuối theo từng nguồn. Nguồn: [88]*

### Exposure và attack path lấy critical asset làm đích

Microsoft định nghĩa attack path là "end-to-end paths that attackers can create to get from an entry point ... to critical assets". Họ có choke point, blast radius và cách nhóm path theo target criticality [64]. Trang Security recommendations đếm số "exposed critical assets" cho mỗi khuyến nghị [5]. CrowdStrike dùng ma trận Asset criticality × Exploit status để ưu tiên lỗ hổng, cộng các widget Managed/Unmanaged/Unsupported và Internet-exposed. Workflow Falcon Fusion tự gợi ý cài sensor và mở ticket ServiceNow cho tài sản unmanaged có confidence High [6].

![CrowdStrike Falcon Exposure Management dashboard](https://www.crowdstrike.com/wp-content/uploads/2024/05/femiatua7.png)
*CrowdStrike Falcon – Exposure Management overview: bộ lọc criticality/host group/tag; Assets overview Managed 1K / Unmanaged 5.9K / Unsupported 305; internet-exposed assets; ma trận criticality × exploit status; Venn network exploitability. Nguồn: [6]*

### Đa tenant: hai mô hình, và chỉ ba vendor mô tả rõ cách xử lý IP trùng

Mô hình thứ nhất là instance riêng cho mỗi khách cộng một lớp tổng hợp. Defender XDR multitenant management có trang Tenants (mỗi tenant: số device, số high value, high exposure, can-onboard, cùng tổng toàn bộ ở đầu trang) và một device inventory gộp có cột **Tenant name**. Thao tác sửa tag, exclusion làm ngay trên danh sách. Muốn thao tác đầy đủ thì bấm vào tên tenant để sang portal của tenant đó [89]. Cortex XSIAM có parent/child, mỗi child là một instance lưu dữ liệu riêng [92]. Mô hình thứ hai là một instance chung, tách bằng nhãn. Google Data RBAC dùng scope gồm allow/deny label (namespace, ingestion label, log type), và deny thắng [93]. Bật Data RBAC thì Risk Analytics chỉ còn cho user có global scope [42], và rule cũ nhận global scope [94]. Practitioner gọi multi-tenancy ở Google là "một bộ quy ước", không phải tính năng [95]. Về IP trùng: QRadar nói thẳng "Log sources that have the same IP address cause problems with correlation, reporting, searching, and asset profiling", nên gán log source vào domain và mỗi asset mang domain ID [15][96]. Thực thể được định danh bằng cặp (IP, domain) [97]. Splunk ghép `cim_entity_zone` với `ip` làm khoá duy nhất cho IP inventory, cho phép khai cùng một subnet ở nhiều zone. Với asset/user inventory thì không tách theo zone mà chỉ giữ zone thấy gần nhất [16]. Khi bật zone ở A&I cổ điển, `ip` và `nt_host` không bị merge xuyên zone [98]. runZero chỉ correlate trong cùng site [56]. Elastic đặt mọi index entity, risk và criticality theo `<space-id>` [34][12]. Wazuh tách saved object theo tenant của dashboard [99]. Không vendor nào có tài liệu về cấu hình criticality hoặc tag riêng mỗi tenant kế thừa từ template của MSSP. Splunk A&I cũng không có trường tenant chính thức [100].

![Microsoft Defender XDR multitenant: danh sách tenant](https://learn.microsoft.com/en-us/defender-xdr/media/mto-tenant-devices/devices-tenant-view.png)
*Microsoft Defender XDR – Multitenant management, Tenants list: mỗi tenant có số device và loại, high value, high exposure, can-onboard; tổng toàn bộ tenant ở đầu trang. Nguồn: [89]*

![Microsoft Defender XDR multitenant: device inventory gộp](https://learn.microsoft.com/en-us/defender-xdr/media/mto-tenant-devices/devices-device-inventory.png)
*Microsoft Defender XDR – Multitenant device inventory: inventory gộp mọi tenant có cột Tenant name, lọc theo risk, criticality, sensor health. Nguồn: [89]*

## OCSF 1.9.0 đủ dữ liệu quan sát nhưng không có thực thể asset bền vững

Tag `1.9.0` (commit `856d462`, 2026-08-03; từ 1.3.0 tag không còn tiền tố `v`) cung cấp ba nhóm vật liệu [101]. Nhóm thứ nhất là **dữ liệu khai báo** trong category Discovery, có `activity_id` 1 = Log (thụ động) và 2 = Collect (chủ động) [102]. Gồm Device Inventory Info **5001** ("collecting device information from a CMDB or running a network sweep") [103], User Inventory Info **5003** [104], Software Inventory Info **5020** (`sbom`, `package`) [105], Cloud Resources Inventory Info **5023** (thêm ở 1.4.0, nhắc rõ nguồn CMDB, CAASM, API cloud/SaaS) [106], Device Config State Change **5019** (`security_states`, hợp để phát hiện EDR bị tắt) [107], và OS Patch State **5004** [108]. Nhóm thứ hai là **dữ liệu quan sát** từ các class Activity: Authentication **3002** (`user`, `dst_endpoint`, `logon_type_id`, `is_remote`, `is_mfa`) cho quan hệ user–host [109]; Network Activity **4001**, ở 1.9.0 có thêm `initiator_id` để biết phía nào khởi tạo [110]; profile `host` gắn `device`/`actor` vào event [111]. Nhóm thứ ba là **finding**: Vulnerability Finding 2002, Compliance Finding 2003, Detection Finding 2004 với `resources[]` [112]. Ở 1.9.0 còn có thêm User Management 3007, thay `account_change` và `user_access` [113].

Về field định danh, `endpoint` yêu cầu `at_least_one` của `ip`, `uid`, `name`, `hostname`, `instance_uid`, `interface_uid`, `interface_name` [74]. `device` bổ sung `uid` (vd EC2 ARN, SID), `uid_alt` (AD DN), `os_machine_uuid`, `boot_uid` (đổi sau mỗi lần reboot), `imei`/`udid`, `first_seen_time`/`last_seen_time`, `type_id` (req), `groups`, `org`, `network_interfaces[]`, `is_managed`/`is_compliant`, và `risk_level_id`/`risk_score` (dictionary mô tả `risk_score` là "as reported by the event source") [18]. `device_hw_info` có `serial_number` và `uuid` SMBIOS [114]. `agent` có `uid` (sensor ID/aid), và `type_id` 1 EDR … 6 Log Forwarding … 7 MDM [115]. `network_interface.namespace` được mô tả là hữu ích khi "similar entities exist that you need to keep separate" [116]. `user` có `uid` (SID/DN/ARN), `uid_alt`, `email_addr`, `domain`, `type_id` (User/Admin/System/Service), `has_mfa`, `risk_level_id` [117]. `ldap_person` có `employee_uid`, `department`, `job_title`, `manager`, `cost_center`, `hire_time`, `leave_time` [118].

Khoảng trống quan trọng nhất là OCSF không có chỗ cho "giá trị nghiệp vụ" của `device`. `device` và `endpoint` **không có** `criticality`, `tags` hay `labels` [18]. `criticality_id` (0 Unknown, 1 Low, 2 Medium, 3 High, **4 Very High**, 99 Other) mới được thêm ở 1.9.0 và chỉ nằm trên `resource_details`; ngoài ra chỉ `application` và `databucket` có `criticality` dạng chuỗi tự do. `resource_details` cũng có sẵn `tags`, `labels`, `owner`, `namespace`, và từ 1.9.0 có thêm hai field `device`/`user` lồng bên trong [19][119]. PR #1693 (Splunk, merge 2026-07-28) thêm chúng với lý do "the criticality of any of the resources populated (in particular `device`)" [120]. `metadata.tenant_uid` chỉ là *recommended*. Field này ra đời từ issue #833 năm 2023, với ví dụ "an MSSP collecting EDR data from a product, for a particular customer" [17][121]. Đừng nhầm nó với tenant phía IdP/SaaS nguồn (`idp.tenant_uid`). OCSF có ba điểm gắn ngữ cảnh hợp chuẩn: `enrichments[]` (name, value, type, provider, `data` json) [122], `observables[]` [123], và `metadata.extensions` [17]. Các bên dùng OCSF đều tự xây kho entity. DataBee "generates a unique ID for each device and user" và gán ID đó vào event, có ưu tiên nguồn ("reduce metadata thrashing"), tuỳ chọn "Allow Merge on IP", owner gợi ý từ authentication 7 ngày, và "OCSF Activity Inclusion List" để chọn class nào đi vào entity resolution [20]. AWS Security Hub giữ resource inventory riêng và chỉ dùng OCSF cho finding [124]. Bảng nguồn native của Security Lake vẫn ghi `metadata.version` 1.1.0 [125]. Tenzir tra lookup inventory rồi ghi vào `enrichments[]` hoặc thẳng vào `src_endpoint` [126]. Trước 1.4.0, tài sản cloud chỉ map "crudely" được vào các class Discovery [127].

## Khuyến nghị thiết kế quản lý tài sản và asset profile đa tenant trên OCSF 1.9.0

**Nhận định:** toàn bộ mục này là đề xuất thiết kế suy ra từ các bằng chứng ở trên, không phải thực tiễn đã được kiểm chứng ở một sản phẩm cụ thể. Vendor tham khảo được ghi cho từng điểm để truy lại.

### Mô hình thực thể và khoá hợp nhất theo tenant

**Nhận định:** dùng bốn lớp dữ liệu. (1) **Observation**: mỗi lần một nguồn thấy một identifier, lưu `(tenant_uid, source = metadata.product.name + log_name, identifier type, value, first_seen, last_seen)`, dựng lại được từ log. (2) **Source record**: bản ghi asset theo từng nguồn (từ 5001/5003/5023 hoặc gom từ Activity), giữ `device.uid` của nguồn làm "source identifier", không dùng làm khoá toàn cục [18]. (3) **Resolved entity**: `asset_uid` và `identity_uid` nội bộ (không có trong OCSF 1.9.0; xem phần extension), mỗi entity là một resolution group có primary record và các alias, theo mẫu Elastic [3]. (4) **Curated attributes**: criticality, owner, tag, role, ghi chú, override. Lớp này lưu riêng và không bao giờ bị rebuild ghi đè. Mọi khoá đều mở đầu bằng `tenant_uid`. Khoá hợp nhất cho device xếp từ mạnh đến yếu:

| Hạng | Khoá (luôn kèm `tenant_uid`) | Trường OCSF 1.9.0 | Ghi chú |
|---|---|---|---|
| 1 | Agent ID theo sản phẩm | `device.agent_list[].uid` + `vendor_name`, `type_id` | Khoá chặn: hai agent cùng sản phẩm có ID khác nhau thì không bao giờ gộp (Tenable UUID) [1] |
| 2 | Cloud instance ID / ARN | `device.instance_uid`, `device.uid` (ARN), `cloud.account.uid`, `resource_details.uid` | Ổn định với VM/cloud |
| 3 | Machine/hardware ID | `device.os_machine_uuid`, `hw_info.uuid`, `hw_info.serial_number`, `imei`/`udid` | Loại placeholder ("To be filled by O.E.M.") như Axonius [4] |
| 4 | MAC | `device.mac`, `network_interfaces[].mac` | Loại MAC ngẫu nhiên/ảo; chặn MAC gắn ≥ N IP trong 2 giờ (QRadar) [46] |
| 5 | Hostname/FQDN + domain | `device.hostname`, `name`, `domain` | Không phân biệt hoa thường, chuẩn hoá FQDN (Tenable) |
| 6 | IP trong (zone, cửa sổ thời gian) | `device.ip`, `src_endpoint.ip`, `network_interface.namespace` | Chỉ là bằng chứng có thời hạn, cửa sổ ngắn (runZero 3 ngày) [2]; không tự gộp chỉ vì trùng IP |

**Nhận định:** với identity, dùng thứ tự `user.uid` (SID/ObjectID/ARN) → `ldap_person.employee_uid` → `email_addr` → `uid_alt` → `name`+`domain`. Có namespace theo IdP như Elastic, nên cùng username ở Okta và AD không tự gộp nếu thiếu bằng chứng mạnh. Account local thấy từ EDR được coi là "medium confidence", gắn với host [34][20]. Thứ tự alias của Google (`windows_sid` > email > userid > employee_id) là một tham chiếu khác [42]. Chỉ gộp tự động khi khớp hạng 1–3, hoặc khớp hạng 4–5 mà không có mâu thuẫn ở hạng cao hơn. Mọi trường hợp còn lại đưa vào hàng chờ "đề xuất gộp", có nút Explain kiểu Axonius (Match / Contradiction / Missing / Weak) [4].

### Provenance và ưu tiên nguồn theo trường

**Nhận định:** giá trị hiển thị của mỗi trường lấy từ bảng ưu tiên nguồn **theo trường, theo tenant**, theo mẫu Tenable Information Order và Axonius Preferred [55][9]. UI luôn cho mở ra xem giá trị của từng nguồn kèm last seen. Bảng mặc định gợi ý: hostname, OS, agent lấy EDR > MDM > scanner > CMDB. IP và MAC lấy nguồn streaming mới nhất (EDR, DHCP, VPN) trước nguồn batch, đúng như Splunk mô tả [33]. Owner, business unit, environment lấy CMDB > IdP/HR > suy luận từ authentication (top 3 user trong 7 ngày như DataBee) [20]. Criticality theo thứ tự override thủ công > rule > classifier. Mỗi trường có field aging: giá trị không được nguồn nào xác nhận lại trong N ngày thì hết hiệu lực [16].

### Vòng đời

**Nhận định:** dùng các trạng thái `candidate` (mới thấy, chưa đủ khoá mạnh) → `active` → `not_seen` → `stale` → `retired`/`archived`, với ngưỡng tuỳ lớp tài sản. VM/container tự scale dùng ngưỡng ngắn kiểu Cortex 3/5/7 ngày [36]. Endpoint và server dùng 7/30 ngày. User và thiết bị vật lý archive sau 1 năm như DataBee [20]. Thêm hai cờ nội bộ độc lập với trạng thái: `managed` (có agent EDR, suy từ `device.agent_list[].type_id = 1`; OCSF cũng có `device.is_managed` do nguồn báo) và `telemetry_gap` (asset active theo nguồn này nhưng im lặng ở nguồn kỳ vọng khác). Dùng CIS 1.1 để đo inventory: M4 là stale, M5 là unknown [91].

### Criticality, role và tag

**Nhận định:** dùng thang 5 giá trị khớp `resource_details.criticality_id` của OCSF 1.9.0 (Unknown, Low, Medium, High, Very High) để xuất ra chuẩn mà không phải dịch [19], và giữ tách khỏi risk score tính toán. Gán qua ba lớp theo mẫu Microsoft: classifier dựng sẵn (DC, Exchange, DB, jump host, máy có tài khoản privileged, cloud prod), rule dạng query builder trên các trường profile có preview, và override thủ công bắt buộc có lý do và hạn review (CrowdStrike chỉ để ô lý do tuỳ chọn, nên đây là mức chặt hơn) [5][6]. Khi nhiều rule cùng khớp thì mức cao nhất thắng. Tài sản dưới ngưỡng tự phân loại vào hàng Pending Approval, và luôn có nút revert về mức hệ thống [5][7]. **Role** (vulnerability scanner, DC, jump host, build server, honey user, service account) là một tag family riêng, dùng làm điều kiện cho detection, suppression và baseline, theo mẫu Cortex Asset Roles [53]. Tag thủ công có ngày hết hạn [9]. Mỗi tenant có bộ rule riêng, khởi tạo từ template của MSSP và có thể override. Không vendor nào có tài liệu về cơ chế này, nên đây là chỗ để sản phẩm tạo khác biệt.

### Các khối thông tin trên asset profile

**Nhận định:** bảng dưới gộp các khối lặp lại ở ≥ 3 vendor và các khối khác biệt đáng học, kèm nguồn OCSF 1.9.0 để dựng từng khối.

| Khối thông tin | Nội dung | Vendor tham khảo | Nguồn OCSF 1.9.0 (class / field) |
|---|---|---|---|
| Header định danh | Tên hiển thị (preferred), loại/class, tenant, lifecycle, criticality (kèm nguồn: rule/override), risk level + delta, exposure, coverage badge, tag/role, action | Defender, Elastic flyout, Axonius, Tenable | `device.name`/`hostname`, `device.type_id`, `metadata.tenant_uid`; criticality xuất qua `resource_details.criticality_id`; risk là giá trị tính nội bộ |
| Định danh và thuộc tính | IP/MAC theo khoảng thời gian, OS, phần cứng, domain, cloud account/region, first/last seen tổng | Defender sidebar, Google asset info, Cortex core/main | 5001 `device.*`: `ip`, `mac`, `network_interfaces[]`, `os.*`, `hw_info.*`, `domain`, `instance_uid`, `os_machine_uuid`, `first_seen_time`/`last_seen_time`; 5023 `cloud`, `region` |
| Nguồn và provenance | Danh sách nguồn đã thấy asset, ID theo nguồn, last seen theo nguồn, giá trị từng nguồn cho từng trường, giải thích ghép | Axonius Adapter Connections, Tenable Connectors/Cluster Logic | `metadata.product.name`/`vendor_name`, `metadata.log_name`, `device.uid` theo nguồn, `agent_list[]` |
| Telemetry health / coverage | Log type kỳ vọng và quan sát được (EDR, auth, network, DNS, cloud), last event theo nguồn, badge "silent", trạng thái agent | MDE sensor health, Sentinel health workbook, Google SHM | `max(time)` theo (`metadata.product`, `class_uid`); `agent_list[].type_id`; 5019 `security_states`; `device.is_managed` |
| Rủi ro và lý do | Risk trend 30 ngày, đóng góp theo category (alert, criticality, watchlist), top finding góp điểm, so peer/role | Elastic risk history, Cortex trend + peer, Exabeam risk reasons | 2004 Detection Finding `risk_score`, `finding_info`, `resources[]`; điểm là dữ liệu nội bộ |
| Alert và case | Alert/incident mở và đã đóng theo severity, link sang case | Defender, Elastic, Sumo | 2004, Incident Finding 2005, `resources[]`/`device` |
| Phần mềm, lỗ hổng, cấu hình | Software/package, CVE (CVSS, EPSS, exploit), patch, compliance check | Defender Inventories/Vulnerabilities, Tenable, Wazuh | 5020 `sbom`/`package`; 2002 `vulnerabilities[].cve`; 2003 `compliance`; 5004 `kb_article_list` |
| User liên quan | Owner (CMDB) tách khỏi top/last user (auth), logon interactive/remote 30 ngày | Defender Logged on users, Exabeam Top User, Rapid7 Primary Asset | 3002 `user`, `dst_endpoint`/`device`, `logon_type_id`, `is_remote`; `actor.user` trong Process Activity; tránh dùng `device.owner` làm owner |
| Mạng và quan hệ | Cổng/dịch vụ, peer nội bộ, domain hiếm/mới, internet-facing, graph host–user–host | Google prevalence, Trend Asset Risk Graph, Rapid7 lateral movement, Tenable Relationships | 4001 `src_endpoint`/`dst_endpoint`, `initiator_id`; `network_interface.open_ports`; `network_endpoint.network_scope_id` |
| Timeline | Swim lane/heat map theo nhóm class, lọc theo nguồn, mở query gốc | Splunk swim lane, Defender timeline, Sumo | Mọi class Activity có `device`/`src_endpoint`, nhóm theo `category_uid` |
| Ghi chú, tag, audit | Ghi chú analyst, lịch sử đổi criticality/tag/merge (ai, khi nào, lý do) | Sumo Notes + Audit Log, Axonius Notes | Không có trong OCSF: dữ liệu nội bộ; có thể phát Entity Management 3004 khi thay đổi |
| Hành động | Set criticality, tag, suppress có hạn, merge/unlink, tạo case, hunt, report inaccuracy | Defender response actions, Axonius Enforce/Unlink, Elastic Take action | Không có trong OCSF |

### Các khối thông tin trên user profile

| Khối thông tin | Nội dung | Vendor tham khảo | Nguồn OCSF 1.9.0 (class / field) |
|---|---|---|---|
| Header | Tên, UPN, title/department, loại (user/admin/service), enabled/locked, criticality, risk, tag | Defender Identity, Exabeam | `user.name`, `display_name`, `full_name`, `type_id`; `account.is_disabled`/`is_locked`; `ldap_person.job_title`/`department`; criticality và tag cần extension (xem dưới) |
| Danh tính hợp nhất | Các account liên kết (primary, nguồn, IdP), alias, giải thích liên kết | Defender Observed in organization, Google aliasing, Elastic resolution | 5003 `user.uid`, `uid_alt`, `email_addr`, `domain`, `account.uid`; 3007 User Management |
| Tổ chức và HR | Manager, cost center, office, hire/leave time, peer group hàng đầu | Exabeam (manager, top peer group), Cortex | `ldap_person.manager`, `cost_center`, `office_location`, `hire_time`, `leave_time`; `user.org` |
| Bảo vệ và đặc quyền | MFA, nhóm, vai trò, quyền | Defender Protection, Tenable Entitlements | `user.has_mfa`, `user.groups[]`, `group.privileges`; 3007 `iam_roles`, `privileges` |
| Nhịp hoạt động | Heat map 7×24, giờ làm việc, vị trí/quốc gia, VPN | Google heat map, Exabeam Data Insights, Rapid7 Ingress Locations | 3002 `time`, `src_endpoint.location`, `is_remote`, `is_mfa` |
| Thiết bị đã dùng | Host logon gần đây, primary asset | Defender, Google tab Assets, Rapid7 | 3002 `dst_endpoint`/`device` |
| Rủi ro và lý do | Likelihood (alert) và impact (criticality, đặc quyền), lý do điểm | Defender risk score, Exabeam risk reasons | 2004 `resources[]`/`actor.user`; điểm nội bộ |
| Hành động | Disable, revoke session, buộc đổi mật khẩu, watchlist, confirm safe | Defender Identity actions | Không có trong OCSF |

### Wireframe đề xuất cho asset profile

```
+--------------------------------------------------------------------------------+
| Tenant: [ACME v]   Assets > WS-FIN-023                       [Report inaccuracy]|
| [laptop] WS-FIN-023.acme.local   Windows 11 23H2   State: ACTIVE  Managed: yes  |
| Criticality: HIGH (rule "finance-pci", 2026-10-02)   Risk: 72 (+18/7d)  Exp: Med|
| Coverage: EDR ok | Auth ok | DNS ok | Sysmon SILENT 3d (!)                      |
| Tags: finance  pci  role:none        [Set criticality][Tag][Suppress..][Case][..]|
+--------------------------------------------------------------------------------+
| Overview | Alerts & cases | Timeline | Users | Network | Software & vulns |      |
| Sources & provenance | Relationships | Notes & audit                            |
+------------------------------+-------------------------------------------------+
| IDENTIFIERS (preferred)      | RISK TREND 30d   __/\__/^^\_   [why? 3 reasons] |
| asset_uid  ast-7f3a...       | Alerts open: 2 High, 5 Med        [View all ->] |
| hostname   WS-FIN-023  [3src]|-------------------------------------------------|
| IP  10.20.4.17 (DHCP, 2h ago)| TELEMETRY HEALTH                                |
|     10.20.4.9  (until 10-31) |  CrowdStrike EDR   last 2m    ok                |
| MAC 3c:52:..:19              |  Windows Security  last 5m    ok                |
| OS  Windows 11 23H2   [EDR]  |  Sysmon            last 3d    SILENT            |
| Owner (CMDB)  nguyen.a       |-------------------------------------------------|
| Top user (auth 7d) tran.b    | USERS 30d: tran.b (41 logon), svc-backup (RDP!) |
| First seen 2025-02-11        |-------------------------------------------------|
| Last seen  2026-11-03 09:12  | VULNS: 3 critical (1 exploited)   [View all ->] |
| Lifecycle  active            | NETWORK: 2 new domains, 1 rare domain (7d)      |
| Source records (3)  [explain]| SUPPRESSIONS: none active                       |
+------------------------------+-------------------------------------------------+
```

### Tác vụ hệ thống và workflow

**Nhận định:** đây là bộ tác vụ tối thiểu, ghép từ các tác vụ các vendor đã có, cộng phần duyệt mà các vendor còn thiếu.

| Tác vụ | Mô tả đề xuất | Vendor tham khảo |
|---|---|---|
| Khai báo nguồn context | Connector CMDB/IdP/cloud/scanner theo tenant, có lịch đồng bộ, thứ hạng ưu tiên theo trường, chọn class OCSF nào đi vào resolution | Splunk A&I/Exposure Analytics, DataBee Inclusion List [29][20] |
| Import CSV | Import asset, criticality, role, link identity. Kiểm tra từng dòng, chạy thử (dry-run), báo dòng lỗi, ghi audit | Elastic, Sumo [31][30] |
| Rule phân loại | Query builder trên trường profile, có preview số asset bị ảnh hưởng, mức cao nhất thắng, bật/tắt từng rule, tạo rule từ bộ lọc đang xem | Microsoft, CrowdStrike [5][6] |
| Merge / unmerge | Hàng chờ đề xuất gộp kèm Explain; gộp hay tách bằng tay đều ghi audit; unlink hàng loạt có trên cả UI, không chỉ API | Elastic, Axonius, Tenable [3][4] |
| Duyệt thay đổi | Pending Approval cho tài sản dưới ngưỡng tự phân loại, override criticality ở mức Very High, suppression theo role; người duyệt phải khác người đề xuất | Microsoft Pending Approval [5] |
| Vệ sinh dữ liệu | Rule chặn dữ liệu bẩn (MAC nhiều IP, Wi-Fi công cộng, placeholder), allowlist, cảnh báo "asset growth deviation" | QRadar [46][47] |
| Coverage gap query | Truy vấn lưu sẵn, chạy theo lịch, ví dụ: server Very High không có EDR; có EDR nhưng EDR last seen > 7 ngày trong khi auth vẫn thấy; asset active không có log auth; asset có trong CMDB mà telemetry 30 ngày không thấy (M4); telemetry thấy mà không có trong CMDB (M5) | Axonius, CIS 1.1/8.2 [72][91][90] |
| Tính lại và health | Nút "tính lại risk ngay", health của từng nguồn context theo last seen (Fail khi vượt cửa sổ) | Elastic, Splunk diagnostics [31][62] |
| Review định kỳ | Hàng việc review criticality và role, ưu tiên asset "Unassigned" và rule hết hạn | Microsoft, CrowdStrike [64][6] |
| API/IaC | API cho mọi thao tác ghi, có thể quản lý rule bằng Terraform | Sumo, Elastic [49][34] |

Workflow triage dùng profile: analyst mở alert và thấy ngay criticality, role, owner và coverage của asset trong flyout. Profile bổ sung prevalence và "lần đầu thấy" để đánh giá mức bất thường. Analyst đánh dấu là hành vi kỳ vọng thì tạo suppression gắn role, có hạn và vào hàng duyệt, không whitelist vĩnh viễn kiểu Exabeam [10].

### Profile nuôi giảm nhiễu như thế nào

**Nhận định:** cách triển khai theo thứ tự. (1) **Enrich lúc ingest/detection**: resolve `device`, `src_endpoint`, `dst_endpoint`, `user`, `actor.user` của mỗi event OCSF về `asset_uid`/`identity_uid` của **cùng tenant**, rồi gắn criticality, role, owner, environment vào `enrichments[]` (`type` = `"asset_context"`, `provider` = tên hệ thống) [122][126]. Lấy theo validity interval tại thời điểm event, giống Google [43]. (2) **Ma trận urgency severity × criticality** theo mẫu Splunk, mỗi tenant sửa được [38]. (3) **Risk modifier minh bạch**: nhân theo criticality (gợi ý khởi điểm như Elastic: 0,5/1/1,5/2, hoặc ×1,5 cho đích critical như Splunk), cộng cho watchlist hoặc privileged. Hiển thị phần đóng góp theo category trên alert và trên profile [12][11]. (4) **Suppression theo lớp tài sản**: rule detection tham chiếu `role:vuln-scanner`, `role:jump-host`, `env:dev` thay vì IP, có lịch (cửa sổ scan), hạn và audit. (5) **Baseline theo role/asset group** để giảm nhiễu từ gốc (Exabeam asset group, Cortex role baseline) [57][53]. (6) **Đo lường bằng dữ liệu của chính hệ thống, không dựa vào số vendor**: tỉ lệ alert có asset resolve được (Graylog cho thấy không có asset thì không có risk) [76], số alert mỗi tenant trước và sau, tỉ lệ true positive theo mức criticality, và số suppression hết hạn chưa review.

### Đa tenant

**Nhận định:** (1) Pipeline **ghi đè** `metadata.tenant_uid` theo kênh ingest (collector hoặc API key của tenant), không tin giá trị nguồn gửi lên. Không nhầm nó với `idp.tenant_uid` hay `cloud.account.uid` [17][121]. (2) Khoá IP có dạng `(tenant_uid, network_zone, ip, khoảng thời gian)`. Zone lấy từ subnet directory của tenant, hoặc từ `network_interface.namespace`/`resource_details.namespace`, theo mẫu Splunk zone và QRadar domain [16][15][116]. Mọi lookup enrichment phải chạy trong phạm vi tenant của event, không bao giờ tra toàn cục. (3) Cấu hình (ma trận urgency, risk factor, classifier, role, ngưỡng lifecycle, thứ hạng nguồn) tách theo tenant, kế thừa từ template MSSP, có hiển thị "khác template ở đâu". (4) View MSSP theo mẫu Defender MTO: danh sách tenant với các chỉ số chuẩn hoá (asset Very High, unmanaged, silent, stale, coverage %, newly discovered), inventory gộp có cột tenant, và drill-down sang profile của tenant [89]. (5) Risk score và entity graph không được trộn giữa các tenant. Google phải giới hạn Risk Analytics cho global scope khi bật RBAC, cho thấy điểm thực thể khó tách phạm vi về sau, nên tách từ đầu [42]. (6) Thao tác ghi từ view MSSP vẫn ghi audit theo tenant.

### Khoảng trống OCSF cần extension

**Nhận định:** đặt các trường còn thiếu vào một extension OCSF riêng của SOC (đăng ký qua `metadata.extensions`), không đưa vào `unmapped` [17][101]. Mọi trường trong bảng dưới là **extension đề xuất**, không tồn tại trên các object này trong schema 1.9.0 (đã đối chiếu `objects/*.json` và `dictionary.json` tại tag 1.9.0). Ba trường `criticality_id`, `tags`, `labels` đã có trong dictionary nên extension chỉ cần gắn chúng vào object mới, giữ nguyên enum; các trường còn lại là tên mới.

| Trường (extension đề xuất) | Gắn vào | Có trong dictionary 1.9.0? | Ghi chú |
|---|---|---|---|
| `asset_uid` / `identity_uid` | `device`, `endpoint` / `user` | Không | ID entity đã resolve của kho asset, khác `device.uid` của nguồn |
| `criticality_id` (+ `criticality`) | `device`, `user` | Có (hiện chỉ trên `resource_details`) | Cùng enum 0–4, 99 [19] |
| `tags`, `labels` | `device`, `user` | Có (hiện trên `account`, `resource_details`, `metadata`…) | Tag/role của profile |
| `asset_role[]` | `device`, `user` | Không | Vd `vuln-scanner`, `jump-host`, `service-account` |
| `environment`, `business_unit` | `device` | Không | prod/stage/dev; BU từ CMDB |
| `last_logon_user` | `device` | Không | Tách khỏi `owner`, vì định nghĩa `endpoint.owner` đang gộp hai nghĩa [74] |
| `lifecycle_state` | `device`, `user` | Không | candidate/active/not_seen/stale/retired |
| `coverage[]` | `device` | Không | Nguồn, log type, last_seen, expected |
| `resolution_confidence` | `device`, `user` | Không | Độ tin cậy của việc gắn event vào entity |

Trong lúc chưa có extension, dùng hai đường hợp chuẩn: gắn `enrichments[]` cho event Activity, và gắn `resources[]` (`resource_details` có `criticality_id`, `tags`, `labels`, `owner`, `namespace`, lồng `device`/`user`) cho Finding [19]. Có thể xuất ngược kho asset thành event Device Inventory Info 5001 / User Inventory Info 5003 với `metadata.product` là hệ thống asset của SOC, để consumer OCSF khác dùng chung [103][104]. Lịch sử thuộc tính và trạng thái thực thể theo thời gian nằm ngoài phạm vi OCSF (OCSF chỉ có `updated_*` trong một event), nên phải lưu trong kho entity [101].

## Biểu đồ ở ba cấp: risk trend bấm được cho asset, KPI có ngữ cảnh cho tenant, ma trận cho MSSP

Mục này đi sâu vào phần trực quan: biểu đồ, graph và widget nào nên có ở trang một asset, ở dashboard inventory của một tenant và ở tổng quan MSSP, mỗi cái trả lời câu hỏi vận hành gì, lấy dữ liệu OCSF 1.9.0 nào. Bố cục header/tab/sidebar của trang profile đã bàn ở mục giao diện profile phía trên.

### Cấp một asset: risk trend có drill-down là xương sống, graph chỉ vẽ quanh asset

Trang một asset hay một user ở các vendor hội tụ về khoảng tám loại hình trực quan: đường risk score theo thời gian, bar hoặc bảng nguồn đóng góp điểm, breakdown theo severity và MITRE, timeline mật độ sự kiện, heatmap giờ hoạt động, prevalence graph, graph quan hệ/process/causality, và graph attack path. **Nhận định:** mỗi loại trả lời một câu hỏi khác nhau của analyst, nên điểm thiết kế quan trọng không phải là có đủ tám loại mà là mỗi loại nối được sang danh sách bằng chứng cụ thể.

#### Risk trend: điểm bấm được, khối lượng chồng lên và mốc tham chiếu

Cortex XSIAM làm đầy đủ nhất. Widget **Risk Score Trend** trên Host Risk View vẽ đường điểm host, tính từ các case gắn với host; **bong bóng** trên đường cho biết số issue và insight trong ngày, bóng càng to càng nhiều issue. Bấm một ngày thì widget Cases chỉ còn những case đã góp điểm hôm đó [21]. Nút "Compare To" thêm một **đường nét đứt là điểm trung bình của các host cùng asset role** trong cùng kỳ, hover vào để xem breakdown theo endpoint; User Risk View có cơ chế y hệt [21][128]. Exabeam User Risk Trend có trục y là điểm trên thang 100, khung 1 tuần, 1 tháng, 3 tháng hoặc 1 năm; ở khung ngắn mỗi điểm là một session, ở khung dài mỗi điểm là session điểm cao nhất của tuần. Hàng counter phía trên (trong ảnh: Rules, Events, Alerts, Accounts, Assets, Zones, Score) đổi theo feed đang chọn, và bấm điểm thì mở Risk Reasons [10]. Microsoft Defender XDR dùng line "Risk Trend" có khung thời gian chỉnh được trên trang identity, kèm link sang timeline [51]. Splunk ES 8.5 vẽ intermediate findings với "time on the x-axis and the risk score on the y-axis", chọn một finding trên timeline thì dòng tương ứng ở bảng bên dưới được highlight [22]. Elastic (Stack 9.5+) có risk score history chart trong flyout entity với **đường nét đứt đánh dấu ngưỡng Low/Moderate/High/Critical**; mỗi điểm là điểm cao nhất của kỳ, bấm một điểm để xem lại điểm cũ [23].

![Exabeam User Risk Trend](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-4a912150-18a6-93cf-0ed4-0c7b6d454896.png)
*Exabeam – User Risk Trend (ảnh dữ liệu 2019): đường điểm 0–100 theo ngày, điểm đang chọn khoanh đỏ, cột Feeds bên trái, hàng counter Rules/Events/Alerts/Accounts/Assets/Zones/Score phía trên. Nguồn: [10]*

**Nhận định:** sản phẩm nên làm đủ cả ba chi tiết: (a) bấm một điểm thì lọc danh sách finding đã góp điểm ngày đó; (b) có tín hiệu khối lượng (bong bóng số finding) để phân biệt "một finding nặng" với "nhiều finding nhẹ"; (c) có mốc tham chiếu, gồm band ngưỡng mức rủi ro ngay ở MVP, rồi đường peer cùng role/loại asset ở bản sau, vì tính peer đòi hỏi kho entity đã có role ổn định.

#### Nguồn đóng góp điểm và breakdown severity/MITRE đóng vai trò bộ lọc cả trang

Câu hỏi tiếp theo sau "điểm có tăng không" là "vì sao". Elastic trả lời bằng bảng **Top risk score contributors** trên tab Host risk: mỗi dòng là một alert góp điểm với timestamp, rule, severity, risk score và reason [85]. Microsoft có **Likelihood of Compromise Details**, "a bar chart that shows alert distribution across MITRE ATT&CK categories", kèm bảng alert lọc được theo status và kill chain stage; likelihood và impact là hai chỉ số tách riêng [51]. Cortex XSIAM đặt một loạt widget breakdown cạnh risk trend: **Case Breakdown** theo severity (bấm một severity thì cả trang lọc theo mức đó), **CVEs Breakdown by severity**, **MITRE ATT&CK Matrix Breakdown**, Issues & Insights gom theo tactic, và counter Failed Logins có link "View in XQL" [21].

![Elastic Top risk score contributors](https://www.elastic.co/docs/solutions/images/security-host-details-hr-tab.png)
*Elastic Security – Top risk score contributors: tab Host risk của host details liệt kê các alert góp điểm với timestamp, rule, severity, risk score và reason. Nguồn: [85]*

**Nhận định:** breakdown ở cấp asset không chỉ để xem mà là **bộ lọc tương tác**: bấm một segment thì timeline, bảng finding và graph cùng lọc theo. Với dữ liệu OCSF, nguồn đóng góp nên chia theo bốn nhóm có class riêng: alert (Detection Finding 2004), lỗ hổng (Vulnerability Finding 2002), cấu hình sai (Compliance Finding 2003) và trạng thái bảo vệ (Device Config State Change 5019); một stacked bar ngang bốn nhóm này dễ đọc hơn bảng thuần khi số finding lớn.

#### Timeline hai lớp: dải tổng quan có brush, rồi bảng hoặc swim lane chi tiết

Defender XDR đặt trên tab Timeline của device **một dải thời gian nhiều tháng có chấm alert tô theo severity** và một vùng brush chọn khung (mặc định 1 tuần), bên dưới là bảng sự kiện gắn tag MITRE technique [8]. Google SecOps làm tương tự ở IP view với dải overview ngắn để brush [129]. Exabeam có **Daily Timeline** 24 giờ theo feed, gộp các sự kiện không điểm cùng loại thành một dòng ("3x Remote access") [10]. Sentinel entity page đặt timeline alert/bookmark/anomaly/activity ở cột giữa [65]. Swim lane heat map của Splunk Asset Investigator đã mô tả ở mục giao diện profile phía trên.

![Defender XDR device timeline](https://learn.microsoft.com/en-us/defender-xdr/media/entity-page-device/entity-device-timeline-tab.png)
*Microsoft Defender XDR – Device timeline: dải tổng quan Oct 2023–Mar 2024 có chấm alert đỏ/cam theo severity, vùng brush một tuần, bảng sự kiện bên dưới gắn tag MITRE technique. Nguồn: [8]*

![Exabeam Daily Timeline](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-4ab92b0e-99f0-eb37-1552-67c0764bd73f.jpg)
*Exabeam – Daily Timeline: dòng thời gian 24 giờ của một user chia theo feed (mô tả theo tên ảnh và đoạn văn quanh ảnh). Nguồn: [10]*

Heatmap giờ hoạt động thuộc cùng nhóm câu hỏi "lúc nào". Cortex User Risk View có **Issues & Insights Heatmap** theo giờ, căn theo múi giờ [128]; Google SecOps User view có heatmap theo giờ với tuỳ chỉnh dịch trục x [41]; Exabeam tô lịch session theo ngày (đen: không hoạt động, xanh: bình thường, đỏ: rủi ro cao) [10]. Docs của vendor nào cũng không nói rõ lưới là đúng 7×24. **Nhận định:** timeline dạng "overview + detail" là MVP vì asset nào cũng có dữ liệu nhiều tháng; heatmap 7×24 có ích nhất cho user và server có lịch cố định, nên để sau.

#### Prevalence là cách giảm nhiễu rẻ nhất, nhưng chỉ Google đặt nó làm biểu đồ trung tâm

Google SecOps Asset view vẽ **prevalence graph**: trục y là số asset trong tổ chức đã kết nối tới một domain, nên domain hiếm nằm trên cao, domain phổ biến như google.com nằm dưới và thường không cần điều tra. Vòng xám là lần kết nối đầu tiên, tam giác đỏ là alert; prevalence tính trên 7 ngày, cửa sổ mặc định của view là 2 giờ, tối đa 100 nghìn sự kiện [66][130]. IP view thêm cột prevalence theo ngày qua nhiều tháng cùng thẻ threat intel [129].

![Google SecOps prevalence graph](https://docs.cloud.google.com/chronicle/images/qs/qs-alert-asset-view.png)
*Google SecOps – Prevalence graph trong Asset view: trục y là prevalence, chấm xám là domain lần đầu hoặc lặp lại, marker đỏ là alert "Suspicious download by Office Application"; trái là timeline sự kiện, phải là Procedural Filtering, dưới là counter Low prevalence domains. Nguồn: [130]*

![Google SecOps IP view](https://docs.cloud.google.com/chronicle/images/ip-address-view.png)
*Google SecOps – IP Address view: cột prevalence theo ngày qua nhiều tháng, dải overview để brush, thẻ ET Intelligence và VT Context. Nguồn: [129]*

**Nhận định:** câu hỏi "bao nhiêu asset khác trong tenant cũng làm vậy" cắt nhiễu hiệu quả mà chỉ cần đếm số asset theo đích kết nối hoặc domain trong 7 ngày. Nó đòi hỏi tính trước trên toàn tenant, nên xếp sau MVP, nhưng nên có sớm dưới dạng cột "prevalence" trong bảng kết nối trước khi làm thành graph.

#### Graph chia hai loại: graph sự kiện cho điều tra, graph cấu hình/quyền cho exposure

Loại thứ nhất dựng từ sự kiện trong một khoảng thời gian. Cortex **Causality view** hình hoá một causality instance gồm node process, event và issue; kéo, zoom được, chuột phải để thêm nhánh parent/child ("Showing Partial Causality") [131]. Elastic có **Visual event analyzer** (process tree từ một alert) và **Session view** (cây lệnh terminal Linux theo session) [132][133]. Sentinel investigation graph vẽ entity trích từ raw data và mở rộng bằng exploration query, nhưng docs thừa nhận "you end up having to switch contexts a great deal more" [134].

![Cortex causality view](https://2127116976-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FcyIgISZgANJYkmLlnwdK%2Fuploads%2Fgit-blob-91c6b9d3ae540a2997e7673fed891d68c4460ff1%2F5bdf1c27f7c20f5d7a1288504bc054d6fce895a8dbec1a4ec84a7e015793c414.gif?alt=media)
*Cortex XDR/XSIAM – Causality view: ảnh động minh hoạ chuỗi causality instance gồm node process, event và issue (mô tả theo vị trí ảnh trên trang). Nguồn: [131]*

![Elastic visual event analyzer](https://www.elastic.co/docs/solutions/images/security-visual-event-analyzer.png)
*Elastic Security – Visual event analyzer: graph process/event dựng từ một alert (mô tả theo alt text). Nguồn: [132]*

Loại thứ hai dựng từ quan hệ bền vững: thành viên nhóm, quyền, kết nối đã biết. Defender XDR **Identity Explorer** (preview, cần license Sentinel Data Lake) khởi tạo graph từ identity hiện tại; node nhóm hiện số đếm như Group (20), Subscription (2), và có scenario dựng sẵn để tìm lateral movement [51]. Axonius **Asset Graph** gom node cùng loại thành một bong bóng có số đếm (vd Devices 20.4K), chỉ cho ungroup khi nhóm dưới 500 node, mỗi loại asset là một layer bật/tắt được, và có danh sách Investigation Steps để quay lui [135][136]. Trend Vision One đổi tên graph trong profile device/account/domain/IP thành **Asset Risk Graph** từ tháng 2/2024 (chỉ đọc được qua snippet) [137]. Elastic có graph preview quanh entity trong 30 ngày (trạng thái Preview từ Stack 9.4), mở rộng ra graph tương tác lọc bằng KQL [23].

![Defender Identity Explorer](https://learn.microsoft.com/en-us/defender-xdr/media/hunting-graph-identity/hunting-graph.png)
*Microsoft Defender XDR – Identity Explorer: scenario "Entity relationship map" đặt user ở tâm, nối tới Group (20), Subscription (2), một tenant ngoài và một device; edge có icon loại quan hệ. Nguồn: [51]*

![Axonius Asset Graph](https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/AssetGraph-DeviceDetailsIndv-1.png)
*Axonius – Asset Graph: node Devices gom nhóm có bong bóng 20.4K, menu View details/Filter/Preview/Ungroup/Enforce/Segment by/Explore connections, drawer Device Details bên phải. Nguồn: [135]*

Attack path là biến thể của loại thứ hai, hướng tới exposure. Microsoft Security Exposure Management vẽ **attack path graph** từ enterprise exposure graph; hover vào node hoặc connector để biết path được dựng thế nào. Tab **Choke points** liệt kê node nơi nhiều path hội tụ, và "View blast radius" cho "visually explore the highest-risk paths from a choke point" [138].

![Exposure Management attack path](https://learn.microsoft.com/en-us/security-exposure-management/media/review-attack-paths/attack-path-graph-details.png)
*Microsoft Security Exposure Management – Attack path graph: chuỗi VM lộ ra Internet → secret → database nối bằng connector có icon, nút "View in map", panel chi tiết node bên phải. Nguồn: [138]*

![Exposure Management choke points](https://learn.microsoft.com/en-us/security-exposure-management/media/review-attack-paths/choke%20points%20and%20blast%20radius.png)
*Microsoft Security Exposure Management – Choke points: bảng node (service principal, repo, pipeline) với Risk level, Type, Critical targets, Attack paths và nút "View blast radius". Nguồn: [138]*

**Nhận định:** hai loại graph cần hai nguồn dữ liệu khác nhau. Graph sự kiện dựng được ngay từ Process Activity 1007, Authentication 3002, Network Activity 4001; graph quan hệ bền vững cần cạnh user–device, group, quyền được lưu trong kho entity, hoặc lấy từ object `graph` của OCSF khi nguồn có gửi (`resource_details.resource_relationship`, `finding_info.attack_graph`) [139]. Với một sản phẩm SOC dựng từ log, graph sự kiện quanh asset (ego-graph) đến trước; attack path chỉ khả thi khi có dữ liệu quyền và cấu hình.

#### Lỗ hổng và lịch sử thuộc tính: breakdown severity và bảng thay đổi có đánh dấu

Cortex có **CVEs Breakdown by severity** như một summary chart để thấy nhu cầu vá gấp [21]; Defender có tab Discovered vulnerabilities và Inventories trên device page [8]. Splunk ES 8.6 hiện **lịch sử bản ghi asset theo ngày** (IP, MAC, OS version, User ID), ô nào thay đổi được đánh dấu "Record changed" [140], một dạng trực quan cho câu hỏi "thuộc tính này đổi khi nào".

![Defender discovered vulnerabilities](https://learn.microsoft.com/en-us/defender-xdr/media/entity-page-device/entity-device-vulnerabilities-tab.png)
*Microsoft Defender XDR – Discovered vulnerabilities: tab lỗ hổng trên device profile (mô tả theo alt text). Nguồn: [8]*

![Splunk entity record change history](https://www.splunk.com/content/dam/splunk-blogs/images/media_10d8ff50825a5063fad076c825bd8c196c696750b.png)
*Splunk ES 8.6 – Entity record change history: bảng lịch sử bản ghi asset theo ngày (IP, MAC, OS version, User ID), ô thay đổi có vạch tím "Record changed". Nguồn: [140]*

**Nhận định:** với OCSF, breakdown lỗ hổng nên là stacked bar severity × (exploit có sẵn / có bản vá) cộng histogram tuổi lỗ hổng, vì Vulnerability Finding 2002 có sẵn `is_exploit_available`, `is_fix_available`, `first_seen_time`, `cve.epss.score` [139]. Như vậy một bar trả lời luôn "vá cái nào trước".

#### Chưa vendor nào vẽ telemetry theo từng nguồn trên trang asset

Trong các trang device/host đã đọc, không vendor nào có sparkline lượng log theo từng nguồn trên trang một asset. Phần gần nhất là provenance nguồn dạng danh sách (Axonius adapter connections, ở mục giao diện profile phía trên). Google Health Hub có line theo ngày và phát hiện bất thường khối lượng, nhưng ở cấp nguồn dữ liệu chứ không ở cấp asset [141]. **Nhận định:** đây là cơ hội rõ nhất ở cấp asset cho một sản phẩm SOC quản lý log tập trung. Một hàng sparkline 14 ngày cho mỗi nguồn (EDR, Windows Security, Sysmon, firewall, scanner) kèm "last seen" và cờ im lặng trả lời ngay câu "không có alert vì an toàn hay vì không có dữ liệu". Dữ liệu có sẵn: `count(*)` theo `metadata.product.name` hoặc `metadata.log_source` theo ngày cho asset, và `max(time)` theo nguồn [139].

#### Bảng (a): bộ biểu đồ đề xuất cho trang một asset

**Nhận định:** cột "Ưu tiên" và "Người xem" là đề xuất; các cột vendor và field là dữ kiện đã dẫn ở trên. Ký hiệu dữ liệu: **E** lấy thẳng từ event OCSF; **S** cần kho entity tự xây; **E+S** event OCSF đã gắn asset_id từ kho.

| Biểu đồ | Câu hỏi vận hành | Loại chart & tương tác | Vendor tham khảo | Dữ liệu OCSF 1.9.0 / kho entity | Ưu tiên | Người xem |
|---|---|---|---|---|---|---|
| Risk score trend | Rủi ro tăng từ khi nào, có vượt ngưỡng không | Line + bong bóng số finding + band ngưỡng; bấm điểm → lọc finding ngày đó; đường peer cùng role ở bản sau | Cortex, Exabeam, Microsoft, Splunk, Elastic [21][10][51][22][23] | 2004 `risk_score`, `risk_level_id`, `time`; `device.risk_score`. Điểm vendor là "as reported by the event source" nên điểm tổng hợp và lịch sử điểm tính trong kho (S) [139] | MVP (peer: sau) | Analyst |
| Nguồn đóng góp điểm | Điểm cao do alert, CVE, cấu hình hay bảo vệ | Stacked bar ngang 4 nhóm hoặc bảng top contributors; bấm nhóm → lọc trang | Elastic, Microsoft LoC bar [85][51] | 2004 `finding_info.analytic`, `metadata.product.name`; 2002 `cve.cvss[].base_score`, `cve.epss.score`; 2003 `compliance.status_id`=3; 5019 `security_states[].state_id` (S, công thức tự định) | MVP | Analyst |
| Breakdown severity/MITRE | Đang có bao nhiêu case/alert mức nào, tactic nào | Bar/chip severity, ma trận MITRE; bấm → lọc toàn trang | Cortex, Microsoft [21][51] | 2004 `severity_id`, `status_id`, `finding_info.attacks`; 2005 `severity_id`, `priority_id`, `status_id`, `attacks` (2005 không có `finding_info`) (E+S) | MVP | Analyst |
| Timeline overview + detail | Chuyện gì xảy ra, lúc nào | Dải nhiều tháng có chấm finding + brush; bảng hoặc swim lane theo class bên dưới | Microsoft, Google, Exabeam, Sentinel [8][129][10][65] | `time`, `class_uid`, `activity_id`, `count`; 2004 `finding_info.first_seen_time`/`last_seen_time`, 2005 `finding_info_list[]` (E+S) | MVP | Analyst |
| Telemetry theo nguồn | Nguồn nào còn gửi log, nguồn nào im | Hàng sparkline 14 ngày mỗi nguồn + last seen + cờ silent; bấm → truy vấn log nguồn đó | Không vendor nào (cơ hội) | `count(*)` theo `metadata.product.name`/`log_source`, `max(time)` theo nguồn (E); trạng thái silent và ngưỡng theo nguồn (S) | MVP | Analyst, SOC lead |
| Chip coverage bảo vệ | Asset có đủ EDR, log forwarder, VM agent không | Chip trạng thái từng lớp, đỏ khi thiếu hoặc tắt | Axonius coverage status (ở cấp tenant) [142] | `agent_list[].type_id` (1 EDR, 5 Vulnerability Mgmt, 6 Log Forwarding, 7 MDM), `device.is_managed`, 5019 `security_states[].state_id` 4 Protection off, 11 Not installed (không phải `state_id` cấp class, vốn chỉ có 0–2/99) (E+S) | MVP | Analyst, SOC lead |
| Vuln breakdown | CVE nào cần vá trước | Stacked bar severity × exploit/fix; histogram tuổi; bấm → danh sách CVE | Cortex, Microsoft [21][8] | 2002 `vulnerabilities[].severity`, `cve.cvss[]`, `cve.epss`, `is_exploit_available`, `is_fix_available`, `first_seen_time`; loại `status_id`=4 Resolved (E+S) | MVP | Analyst, đội vá |
| Activity heatmap | Hoạt động bất thường giờ nào | Heatmap giờ × ngày, tô theo số event hoặc finding | Cortex, Google, Exabeam [128][41][10] | `time`, `count` của 3002, 1007, 4001 (`traffic.bytes`) lọc theo `device.uid` (E+S) | Sau | Analyst |
| Prevalence | Asset đã nói chuyện với thứ gì hiếm trong tenant | Scatter thời gian × số asset cùng kết nối; marker alert; lọc theo event type | Google [66][130] | 4001 `dst_endpoint`, domain; đếm asset_id trong 7 ngày (E+S) | Sau (cột prevalence trước) | Analyst, hunter |
| Ego-graph quan hệ | Ai đăng nhập, nói chuyện với đâu, chạy gì | Graph 1–2 hop, cửa sổ thời gian, gom node cùng loại, layer bật/tắt | Microsoft, Axonius, Elastic, Sentinel [51][135][23][134] | 3002 `user`, `dst_endpoint`, `logon_type_id`; 4001 `src_endpoint`/`dst_endpoint`, `initiator_id`; 1007 `process`; cạnh bền vững user–device lưu trong kho (E+S) | Sau | Analyst |
| Process tree / causality | Chuỗi process nào dẫn tới alert | Tree/graph từ một alert, mở rộng parent/child | Cortex, Elastic [131][132] | 1007 `process`, `actor.user` (E+S) | Sau (phụ thuộc EDR) | Analyst |
| Attack path / blast radius | Từ asset này kẻ tấn công đi tới đâu | Graph path tới critical target, choke point | Microsoft, Trend [138][137] | `finding_info.attack_graph`, `resource_details.resource_relationship` (object `graph`) khi nguồn có gửi; còn lại S | Sau | Analyst, đội exposure |
| Lịch sử thuộc tính | IP/OS/owner đổi khi nào, từ nguồn nào | Bảng theo ngày có ô đánh dấu thay đổi | Splunk ES 8.6 [140] | 5001 `device.*` + `metadata.product` + `time`; provenance và hiệu lực lưu trong kho (S) | Sau | Analyst |

#### Wireframe vùng trực quan của trang asset

Phần header, tab và sidebar định danh theo wireframe ở mục khuyến nghị thiết kế phía trên; khung dưới chỉ là vùng biểu đồ.

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

### Cấp inventory tenant: KPI có ngữ cảnh, phân bố bấm ra danh sách, coverage theo nguồn

Dashboard inventory của các vendor dùng chung một khung: hàng KPI tile ở trên, phân bố và xu hướng ở giữa, bảng xếp hạng ở dưới, đúng bố cục Splunk khuyên (trên cùng là chỉ số chính, giữa là xu hướng hoặc phân rã theo nhóm, dưới là dữ liệu chi tiết để điều tra) [143]. Khác biệt nằm ở mức độ: docs Microsoft Defender device inventory không mô tả biểu đồ nào, chỉ có **count pill** ở đầu mỗi tab (total, critical assets, high risk, high exposure, not onboarded, newly discovered) và vài card như "Classify critical assets" [50]; Elastic Entity Analytics gần như chỉ có KPI và bảng top risk score [144]; còn runZero, Axonius, Splunk và Tenable dựng dashboard nhiều loại chart.

#### Hàng KPI tile luôn kèm delta, sparkline hoặc mục tiêu

Tenable Operational Dashboard gắn vào mỗi tile (CES, Critical Detections, Assets With Critical Detections) một **"Sequential Period Comparison"** theo %, kèm nhãn "Last Data Update"; dữ liệu làm mới 24 giờ một lần, giữ 90 ngày và chỉ tính asset có license [145]. Microsoft Exposure Management Overview có 5 tile Domain initiative (Code, Endpoint, Cloud, Identity, SaaS), mỗi tile là % so với target score kèm sparkline và delta [146]. Splunk ES 8.6 mở đầu Entity Discovery Insights bằng "4,355 Discovered assets" và "6 Discovered asset types" [140].

![Tenable Operational Dashboard](https://docs.tenable.com/exposure-management/Content/Resources/Images/Local/exposure-management/dashboard-details.png)
*Tenable Exposure Management – Operational Dashboard: tile CES 533, Critical Detections 1.426, Assets With Critical Detections 103, mỗi tile kèm Sequential Period Comparison %; bảng Top 5, bar Asset Exposure Score theo category, nhãn Last Data Update. Nguồn: [145]*

![Exposure Management overview](https://learn.microsoft.com/en-us/security-exposure-management/media/get-started-exposure-management/exposure-management-overview.png)
*Microsoft Security Exposure Management – Overview: card Resolve now (Patch/Mitigate/Fix) có số recommendation, bảng Internet-exposed resources, 5 tile Domain initiatives với % so với target, sparkline và delta. Nguồn: [146]*

**Nhận định:** sáu tile đáng đặt trên cùng cho SOC đa nguồn là: asset hợp nhất, asset mới 7 ngày, asset silent, asset không có EDR, % độ phủ EDR, và % chưa phân loại criticality. Tổng asset là tile kém hành động nhất, nhưng cần có vì nó là mẫu số cho các tỉ lệ khác.

#### Phân bố theo loại/OS/criticality: donut hoặc bar bấm được, và mẫu "least seen"

Splunk dùng pie "Assets by type" [140]; Microsoft dùng donut "Device exposure distribution", docs ghi rõ "Select a section in the doughnut chart to go to the Devices list page" [26]; Axonius có Field Segmentation (pie hoặc histogram theo một field) và Adapter Segmentation (theo nguồn dữ liệu) [147]. runZero có nhóm "Most and least seen graphs" theo Asset types, Operating systems, Hardware, MAC vendors, ports, Products, Protocols, Risk, Criticality, Tags, **mỗi biểu đồ lật được giữa most seen và least seen** [24]. Wazuh 4.13 (2025-09-18) thêm dashboard IT Hygiene, chủ yếu là bảng Top 5 (OS families, packages, processes) và một stacked bar Package types [148][149].

![Splunk ES 8.6 Entity discovery insights](https://www.splunk.com/content/dam/splunk-blogs/images/media_163d82c78b9192b4325e24b26e6a06e7e828a320f.png)
*Splunk ES 8.6 – Entity discovery insights: KPI 4.355 asset và 6 loại, pie Assets by type, stacked bar New assets by type theo ngày, bubble map Asset locations, các bảng Asset subnets, Ephemeral assets và Discovery sources, nút View in Entity discovery inventory. Nguồn: [140]*

![Wazuh IT Hygiene dashboard](https://documentation.wazuh.com/current/_images/system-inventory-dashboard1.png)
*Wazuh – IT Hygiene dashboard: các bảng Top 5 (OS families, packages, processes, OS, host CPUs, endpoints by memory) và stacked bar ngang Package types. Nguồn: [148]*

**Nhận định:** "least seen" lật một biểu đồ phân bố vốn ít hành động thành công cụ săn shadow IT (OS lạ, MAC vendor lạ). Phân bố cơ cấu nên đặt ở tầng giữa, dùng bar ngang khi quá 6 nhóm, và luôn hiện rõ nhóm "Unknown/chưa phân loại" chứ không gộp vào "Other".

#### Coverage theo nguồn: bar xếp hạng kèm tổng unique, Venn khi tối đa 3 tập

Câu hỏi "tôi có bao nhiêu thiết bị" được Axonius trả lời bằng **Device Discovery chart**: bar ngang xếp hạng adapter theo số device thấy được (top 20), kèm "Total Devices Seen" và "Total Unique Devices: The number of total unique devices after Axonius device correlation"; bấm một hàng thì mở trang Devices lọc theo adapter [27]. Splunk có bảng "Discovery sources" (vendor/nguồn × số asset) [140], runZero có bảng "Asset sources" [24]. Chồng lấn giữa các nguồn được vẽ bằng **Query Intersection**: pie hoặc bar cho tối đa 2 query giao, Venn tròn cho tối đa 3, Venn tam giác cho tối đa 6 (chỉ cho Axonius Identities); ví dụ có sẵn là "All devices" giao "Missing EDR" [28].

![Axonius Device Discovery chart](https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/DeviceDiscoveryChart_24.png)
*Axonius – Device Discovery chart: bar ngang xếp hạng adapter theo số device thấy được (ServiceNow 1.975…), Total Devices Seen 19.643 so với Total Unique 4.787 sau correlation. Nguồn: [27]*

![Axonius Venn chart](https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/img/Dashboards/VennChartPreviewExample.png)
*Axonius – Query Intersection dạng Venn: ví dụ Venn 3 vòng cho phần chồng lấn giữa các query (mô tả theo chú thích). Nguồn: [28]*

Độ phủ agent được Axonius tách thành dashboard riêng ba phần: Scope & Compliance (vd 500/1.000 device có CrowdStrike), Coverage Status (active, inactive, missing, headless), và Coverage Health Trends Over Time để thấy "spikes, or gradual degradation in coverage health" [142]. CrowdStrike Falcon Exposure Management có một **bar màu hồng đại diện cho mọi asset unmanaged**; bấm vào để drill-down rồi lọc theo phân loại asset [6].

![Axonius Agents Deployment Status](https://files.readme.io/9d03b26ed0a366aeb853129361808f49ab95cb85c0f37a2f670fae3c123698da-image.png)
*Axonius – Agents Deployment Status: bảng agent (Zoom, CrowdStrike, IGEL) với Configuration status, Active agents, Potential issues và nút Dashboard/View issues dẫn vào Agent Coverage dashboard. Nguồn: [142]*

**Nhận định:** con số 19.643 lượt thấy so với 4.787 device unique trong ảnh Axonius cho thấy vì sao biểu đồ coverage phải hiện cả "tổng lượt thấy" lẫn "unique sau hợp nhất": trong ví dụ đó, cộng thô các nguồn thổi phồng inventory khoảng 4 lần. Venn chỉ đọc được tới 3 tập; một SOC có 5–10 nguồn nên dùng UpSet hoặc ma trận nguồn × asset, còn MVP chỉ cần danh sách "asset chỉ một nguồn thấy" cùng stacked bar 100% độ phủ EDR/log theo criticality.

#### Lifecycle new/stale/silent và asset mới theo ngày

runZero có widget "Asset trends: timeline of asset counts broken out by live, recent, and a couple of other states" [24]. Splunk vẽ **stacked bar "New assets by type" theo ngày**, tô màu theo loại, và bảng "Ephemeral assets" theo loại kèm % [140]. Axonius có Query Timeline và Multi-Line Timeline cho số asset khớp một query theo thời gian [147][150]. Microsoft có pill "newly discovered" [50].

![Axonius Query Timeline](https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/TimeLineChart.png)
*Axonius – Query Timeline: line số asset khớp một query theo thời gian (mô tả theo chú thích). Nguồn: [150]*

**Nhận định:** OCSF không có trạng thái lifecycle, nên các tile và trend new/stale/silent phải đọc từ snapshot đếm theo ngày trong kho entity. Cần tách "silent" (asset còn đó nhưng một nguồn ngừng gửi) khỏi "stale" (không nguồn nào thấy), vì trường hợp đầu thường là lỗi pipeline, đúng như Google cảnh báo feed có thể hiện Active trong khi thu thập đang hỏng [141].

#### Exposure và top rủi ro: gauge, trend, donut và bảng xếp hạng có sparkline

Dashboard Defender Vulnerability Management có gauge "Endpoint exposure score" 0–100, line điểm theo thời gian, bảng Top vulnerable software có sparkline số device bị lộ, bar ngang Vulnerabilities insights (tổng/exploitable/critical/zero-day), donut Device exposure distribution và progress bar Top remediation activities; docs ghi "Devices that aren't active in the last 30 days aren't factored in" [26]. Elastic có bảng User/Host/Service Risk Scores top 5, bấm tên mở flyout, bấm số alert sang Alerts hoặc Timeline [144]. Wazuh có dashboard lỗ hổng theo severity, package và OS [60].

![Defender Vulnerability Management dashboard](https://learn.microsoft.com/en-us/defender/media/defender-vulnerability-management/new-overview.png)
*Microsoft Defender Vulnerability Management – Dashboard: gauge exposure score 23/100, line điểm theo thời gian, donut Device exposure distribution, bar ngang Vulnerabilities insights, progress bar remediation, bảng top exposed devices kèm criticality. Nguồn: [26]*

![Elastic host risk scores](https://www.elastic.co/docs/solutions/images/security-host-score-data.png)
*Elastic Security – Entity Analytics, Host risk scores: bảng top host theo risk score kèm alert count (mô tả theo chú thích). Nguồn: [144]*

![Wazuh vulnerabilities dashboard](https://documentation.wazuh.com/current/_images/vulnerabilities-inventory-dashboard1.png)
*Wazuh – Vulnerabilities inventory dashboard: lỗ hổng theo severity, package và OS (mô tả theo tên ảnh và ngữ cảnh). Nguồn: [60]*

**Nhận định:** không vendor nào trong mẫu vẽ sẵn heatmap severity × criticality, dù đây là câu hỏi ưu tiên vá cốt lõi ("lỗ hổng nặng nằm trên tài sản quan trọng nào"). Một lưới 4×4 (severity × criticality), mỗi ô là số asset và bấm ra danh sách, gọn hơn cả gauge lẫn donut.

#### Sức khoẻ dữ liệu được tách thành dashboard riêng

Google SecOps **Health Hub** là mẫu rõ nhất: big number Healthy/Failed/Irregular cho source và parser, line "Data Source Health Overview" theo ngày, "Total Ingested Logs", "Failing Parser by Log Type", và bảng Health Status by Data Source. "Irregular" được định nghĩa là "unusual surges or drops in data volume or a significant change in error rates", phát hiện bằng thống kê "with a 15-day lookback period" [141].

![Google SecOps Health Hub](https://docs.cloud.google.com/static/chronicle/images/health-status-by-data-source-mu.png)
*Google SecOps – Health Hub, Health status by data source: bảng trạng thái nguồn Healthy/Irregular/Failed (mô tả theo tên ảnh và ngữ cảnh). Nguồn: [141]*

**Nhận định:** dashboard inventory chỉ đáng tin khi người xem biết dữ liệu nuôi nó tươi tới đâu. Nên có một dashboard data-health riêng (nguồn × trạng thái, độ trễ ingest, khối lượng theo ngày), còn trên dashboard inventory chỉ giữ một nhãn "dữ liệu cập nhật lúc… / N nguồn đang trễ", giống nhãn "Last Data Update" của Tenable [145].

#### Bảng (b): bộ biểu đồ đề xuất cho dashboard inventory tenant

**Nhận định:** cột "Ưu tiên" và "Người xem" là đề xuất.

| Biểu đồ | Câu hỏi vận hành | Loại chart & tương tác | Vendor tham khảo | Dữ liệu OCSF 1.9.0 / kho entity | Ưu tiên | Người xem |
|---|---|---|---|---|---|---|
| Hàng KPI tile | Inventory hôm nay thế nào so với kỳ trước và mục tiêu | Số lớn + delta % + sparkline 14 ngày + đích; bấm → danh sách lọc | Tenable, Microsoft, Splunk [145][146][140] | Snapshot đếm theo ngày trong kho (S) | MVP | SOC lead, khách hàng tenant |
| Asset theo lifecycle | Inventory tăng/giảm, có đột biến không | Stacked area/line live–new–stale–silent | runZero, Axonius [24][150] | Snapshot kho; đầu vào 5001, 5003, 5023 và mọi event có `device` (S) | MVP | SOC lead |
| Asset mới theo ngày | Thứ gì vừa xuất hiện | Stacked bar theo ngày tô theo loại; bấm cột → danh sách | Splunk [140] | `first_seen` hợp nhất trong kho; `device.first_seen_time` theo nguồn (S) | MVP | Analyst, SOC lead |
| Phân bố loại/OS/criticality | Cơ cấu tài sản, giá trị hiếm | Bar ngang hoặc donut ≤6 nhóm; toggle most/least seen; bấm segment → danh sách | runZero, Splunk, Microsoft, Axonius [24][140][26][147] | `device.type_id`, `os.type_id`/`os.name`, `resource_details.criticality_id` (0 Unknown = chưa phân loại), `device.groups`, `org`, `region` (E+S) | MVP (BU/site: sau) | SOC lead |
| Coverage theo nguồn | Nguồn nào thấy bao nhiêu, còn bao nhiêu unique | Bar ngang xếp hạng + tổng lượt thấy vs unique; bấm hàng → danh sách | Axonius, Splunk, runZero [27][140][24] | Tập asset_id quan sát theo `metadata.product.name` trong N ngày (S) | MVP | SOC lead |
| Chồng lấn nguồn | Asset nào chỉ một nguồn thấy (CIS 1.1 Accuracy) | Venn ≤3 tập; UpSet/ma trận khi >3; MVP là danh sách "chỉ 1 nguồn" | Axonius [28] | Như trên (S) | MVP danh sách, UpSet sau | SOC lead |
| Độ phủ EDR/agent | Bao nhiêu asset thiếu hoặc tắt bảo vệ | Stacked bar 100% active/inactive/missing theo loại/criticality + trend; bấm → danh sách thiếu | Axonius, CrowdStrike, Microsoft [142][6][50] | `agent_list[].type_id`=1, `device.is_managed`, 5019 `security_states[].state_id` 4, 11 (E+S) | MVP | SOC lead, khách hàng tenant |
| Độ phủ log (CIS 8.2/8.9) | Asset có khả năng log nào chưa được thu | Stacked bar 100%: thu tập trung / có khả năng nhưng chưa thu / không hỗ trợ; theo criticality | Không vendor nào dựng sẵn; công thức CIS [151] | Asset × nguồn log trong kho; `agent_list[].type_id`=6 (S) | MVP | SOC lead |
| Chất lượng inventory | % chưa phân loại criticality, % chưa có owner | KPI + trend có đường mục tiêu; bấm → hàng chờ phân loại | runZero Asset ownership, CDM UAH [24][152] | `resource_details.criticality_id`=0, owner rỗng (`owner` của endpoint lẫn với "last logged into") (S) | MVP | SOC lead, khách hàng tenant |
| Exposure severity × criticality | Lỗ hổng nặng nằm trên asset quan trọng nào | Heatmap 4×4, ô = số asset; bấm → danh sách | Không vendor nào; gần nhất là donut exposure Microsoft, bar Tenable [26][145] | 2002 `vulnerabilities[].severity`, `cve.cvss[].base_score`, `is_exploit_available`, nối criticality từ kho (E+S) | MVP | SOC lead, đội vá |
| Top asset/user rủi ro | Xử lý asset nào trước | Bảng top N + sparkline 14 ngày + link profile | Elastic, Microsoft, Tenable [144][26][145] | Điểm tổng hợp trong kho; đầu vào 2004 `risk_score`, 2005 `priority_id`, `user.risk_score` (S) | MVP | Analyst |
| Data freshness / health | Nguồn nào trễ, dashboard có tin được không | Dashboard riêng: big number + line theo ngày + bảng nguồn; nhãn tóm tắt trên inventory | Google Health Hub [141] | `metadata.processed_time` − `time` (hoặc `logged_time` − `time`), `max(time)` theo `metadata.product.name` (E) | MVP | SOC lead, kỹ sư dữ liệu |
| Compliance pass/fail | Cấu hình sai tập trung ở control nào | Stacked bar 100% theo control | Không đọc được mẫu cụ thể | 2003 `compliance.status_id` (1 Pass, 2 Warning, 3 Fail), `control`, `standards` (E+S) | Sau | SOC lead, khách hàng tenant |
| Patch state | Máy nào thiếu bản vá | Bar theo KB/tuổi | Wazuh (Windows KB most/least common) [148] | 5004 `kb_article_list[].install_state_id`, `severity`, `created_time` (E+S) | Sau | Đội vá |
| Bản đồ vị trí | Asset nằm ở đâu | Bubble map | Splunk, runZero [140][24] | `device.location` (`country`, `city`, `lat`, `long`) (E+S) | Sau | Khách hàng tenant |

#### Wireframe dashboard inventory tenant

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

### Cấp MSSP: vendor mới dừng ở bảng tenant × số đếm, heatmap tenant × KPI còn bỏ trống

Microsoft là vendor duy nhất trong mẫu có docs rõ cho view inventory đa tenant. Trang Tenants của Defender multitenant management hiện, cho từng tenant, "the number of devices and device types, the number of high value and high exposure devices, and the number of devices available to onboard"; đầu trang có số tenant và tổng device onboarded/discovered; bấm tên tenant thì vào device inventory của tenant đó. Trang device inventory đa tenant giữ nguyên bố cục một tenant, chỉ thêm cột Tenant name và hàng tổng "for all tenants" ở trên [89]. Microsoft Secure Score có "comparison bar chart" và "comparison trend" so với các tổ chức tương tự (ẩn danh) [153], một mẫu benchmark có thể dùng lại để xếp hạng tenant. CDM AWARE cũng khuyến khích agency so điểm của mình với "federal average score" [152].

Ảnh trang Tenants này đã đặt ở mục vận hành và đa tenant phía trên [89].

Các vendor khác chỉ cung cấp hạ tầng để MSSP tự dựng. Sentinel cho triển khai workbook ở managing tenant qua Azure Lighthouse để "create at-scale dashboards to monitor and query data across customer tenants", truy vấn chéo workspace bằng `union` và `workspace()` (nội dung đọc qua snippet) [154][155]. Wazuh coi tenant là "containers for saved objects such as index patterns, visualizations, and dashboards", tức tách dashboard, còn docs không nói tách index [99]. Azure Workbooks cho phép link từ grid, tile hay graph sang một workbook khác và truyền tham số, đúng cơ chế cần để drill-down từ hàng tenant sang dashboard tenant [156]. Không tìm được docs view tổng hợp của Google SecOps, Axonius hay Splunk cho MSSP.

**Nhận định:** mẫu Microsoft (cùng bố cục cho một tenant và nhiều tenant, thêm cột Tenant, hàng tổng ở trên, bấm hàng để vào tenant) đơn giản và nên theo. Phần còn thiếu là chuyển bảng số đếm thành **bảng tỉ lệ có tô màu theo ngưỡng**, tức heatmap tenant × KPI, vì số đếm thô không so được giữa tenant 500 asset với tenant 50.000 asset. Các ngưỡng CIS (discovery ≤24 giờ, xử lý asset trái phép ≤7 ngày, review log ≤7 ngày) cho sẵn tiêu chí pass/fail để tô từng ô [157][151]. Mọi truy vấn MSSP gom theo `metadata.tenant_uid`, trường OCSF chỉ để recommended nên pipeline phải bắt buộc điền [139].

#### Bảng (c): bộ biểu đồ đề xuất cho tổng quan MSSP

**Nhận định:** cột "Ưu tiên", "Người xem" và các dòng không có vendor tham khảo là đề xuất.

| Biểu đồ | Câu hỏi vận hành | Loại chart & tương tác | Vendor tham khảo | Dữ liệu OCSF 1.9.0 / kho entity | Ưu tiên | Người xem |
|---|---|---|---|---|---|---|
| Hàng KPI toàn portfolio | Cả MSSP quản lý bao nhiêu, bao nhiêu tenant dưới ngưỡng | Tile số tenant, tổng asset, tổng critical, số tenant fail ≥1 KPI | Microsoft MTO [89] | Gộp snapshot kho theo `tenant_uid` (S) | MVP | MSSP manager |
| Ma trận tenant × KPI | Tenant nào yếu ở chỉ số nào | Bảng tỉ lệ tô màu pass/warn/fail theo ngưỡng (heatmap), sort theo cột; bấm ô → dashboard tenant đã lọc | Microsoft MTO (dạng số đếm) [89]; ngưỡng CIS [157][151] | % EDR, % log 8.9, % chưa crit, % silent theo `tenant_uid` (S); độ trễ nguồn (E) | MVP | MSSP manager, SOC lead |
| Health nguồn đa tenant | Tenant nào đang mất dữ liệu | Lưới tenant × loại nguồn, ô = Healthy/Irregular/Failed + last seen | Google Health Hub (một tenant) [141] | `max(time)`, `processed_time` − `time` theo `tenant_uid` × `metadata.product.name` (E) | MVP | MSSP manager, kỹ sư dữ liệu |
| Ranking / benchmark | Tenant đứng đâu so với phần còn lại | Bar xếp hạng một KPI + đường trung vị MSSP; bản cho khách chỉ hiện tenant đó và trung vị ẩn danh | Secure Score comparison, AWARE federal average [153][152] | Snapshot KPI theo tenant (S) | Sau | MSSP manager, khách hàng tenant |
| Trend portfolio | KPI của các tenant đi lên hay xuống | Small multiples line, mỗi tenant một ô, chung trục | Không vendor nào | Snapshot KPI theo ngày × tenant (S) | Sau | MSSP manager |
| Hàng chờ theo tenant | Việc tồn nằm ở tenant nào | Stacked bar tenant × (asset chưa phân loại, asset trái phép quá 7 ngày, nguồn hỏng) | Không vendor nào; ngưỡng CIS 1.2 [157] | Kho entity + 5019 theo `tenant_uid` (S) | Sau | MSSP manager |

#### Wireframe tổng quan MSSP

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

### Nguyên tắc thiết kế: mỗi widget là một số đo có mục tiêu, nguồn và danh sách đích

#### Năm nguyên tắc rút từ docs vendor và tiêu chuẩn

**Actionability.** NIST SP 800-55 Vol.1 (12/2024) đặc tả mỗi measure bằng *Target* ("A range or a designated upper or lower bound… final and interim targets"), *Time-based reference* (tần suất theo "rate of change that is being evaluated"), *Data source* và *Reporting format* ("such as a pie chart, line chart, bar graph, or other format"); báo cáo không kèm ngữ cảnh thì "there can be unintended consequences or indecision", nên phải nêu rủi ro số đo chỉ ra và "What prioritization, action, or decision might need to be taken" [158]. Splunk nói cùng ý: dashboard giám sát cần "quick context, key information, and indication of action", và bước đầu tiên là xác định "Your intended audience, purpose and their resulting actions" [143]. **Nhận định:** mỗi widget nên có một phiếu đặc tả gồm câu hỏi vận hành, công thức, mục tiêu, tần suất, nguồn OCSF và danh sách asset nó mở ra; widget nào không viết được dòng cuối là ứng viên vanity.

**Drill-down tới danh sách đã lọc.** runZero: "you can view any widget's distinct data points in detail by clicking the relevant table row links or buttons, or individual segments of donut, bar, or column charts" (trừ biểu đồ timeline) [24]. Axonius: "Clicking a chart segment opens the Asset Table using the view associated with that segment", với Query Intersection thì base query được ghép với query của segment [25]. Tenable có drill down mode: bấm một data point để đi xuống dữ liệu chi tiết hơn ngay trong widget [145], Splunk ES 8.6 cho "drill directly from these dashboards into Entity Discovery Inventory" [140], và Azure Workbooks truyền tham số sang workbook chi tiết với điều kiện "parameter names must be the same in both workbooks" [156]. **Nhận định:** lưu mỗi widget dưới dạng truy vấn có tên trên kho entity, để segment nào cũng sinh được URL danh sách; đây là quyết định kiến trúc chứ không phải chi tiết UI.

**KPI có ngữ cảnh, delta và mục tiêu.** Microsoft Exposure Management cho mỗi initiative một "14 day change trend graph", một target score người dùng tự đặt, và History: chọn một thời điểm để xem "percent effect on the initiative score and the reason for the change" cùng "up to the top 100 changed assets"; dữ liệu được tính lại theo device group và scope của người xem [159]. NIST Vol.2 nhấn việc giữ số đo nhất quán để thấy "long-term trends and expected ranges" và đặt mục tiêu "against industry standards and internal targets" [160]. NIST cũng cảnh báo số đếm như số lỗ hổng đã biết "depend heavily on the quality of work behind them" [158], nên số đếm thô cần đổi thành tỉ lệ hoặc chia theo criticality.

![Exposure Management initiative history](https://learn.microsoft.com/en-us/security-exposure-management/media/initiatives/initiatives-history-details.png)
*Microsoft Security Exposure Management – Initiative history: chọn một thời điểm trên trend để xem lý do điểm thay đổi và danh sách asset được thêm hoặc bớt, tức drill-down từ con số sang asset. Nguồn: [159]*

**Tránh graph hairball bằng cách khoanh phạm vi.** Cambridge Intelligence (vendor thư viện graph) khuyên "graph filtering and node and link aggregation" và bắt đầu "backwards from the job your end users need to get done", dựng view dẫn xuất thay vì vẽ toàn bộ graph [161]. Axonius làm đúng như vậy: gom node cùng loại, chỉ cho ungroup dưới 500 node, có layer theo loại asset [135]. CISA, trong hướng dẫn cho OT, khuyên vẽ sơ đồ theo nhóm tài sản (Zones and Conduits) và "Use tables or charts to show asset relationships and dependencies" [162]. **Nhận định:** chỉ vẽ ego-graph quanh một asset với độ sâu 1–2 hop, cửa sổ thời gian mặc định 24 giờ, gom IP/process cùng loại thành node đếm, lọc theo loại quan hệ; không có graph "toàn tenant" mặc định, ở cấp tenant chỉ dùng sơ đồ đã gộp theo zone/segment.

**Tách dashboard sức khoẻ dữ liệu.** Google tách Health Hub khỏi các dashboard nghiệp vụ, và cảnh báo feed có thể hiện Active dù thu thập đang hỏng [141]. NIST yêu cầu kiểm tra "integrity, accuracy, and structure of the data" trước khi phân tích, và coi dữ liệu là đáng ngờ khi nguồn chỉ nhận báo cáo từ một vài bộ phận [158]. Microsoft TVM loại device không hoạt động 30 ngày khỏi phép tính [26], một ví dụ về việc phải ghi rõ mẫu số ngay trên dashboard.

#### KPI chuẩn từ CIS, CDM và NIST và cách đưa lên biểu đồ

CIS Controls Assessment Specification cho sẵn công thức và ngưỡng cho Control 1 (inventory) và 8 (audit log), CISA CDM AWARE cho công thức điểm bề mặt tấn công, NIST cho khung đặc tả. Cột "Hiển thị đề xuất" là **Nhận định**.

| Chỉ số | Công thức / ngưỡng | Nguồn | Hiển thị đề xuất |
|---|---|---|---|
| CIS 1.1 Inventory Accuracy | M3/M2 = asset có cả trong inventory và nguồn đối chiếu / asset trong nguồn đối chiếu; M4 = asset trong inventory không có ở nguồn đối chiếu | [157] | Tile % + sparkline + đích; drill-down hai danh sách lệch nhau |
| CIS 1.1 Completeness | Trang ghi "M8/M1", nhiều khả năng lỗi đánh máy của M6/M1 (asset đủ thông tin chi tiết / inventory) | [157] | Tile % "đủ thuộc tính bắt buộc" |
| CIS 1.1 độ tươi inventory | Fail nếu M8 (số tháng từ lần cập nhật cuối) > 6 tháng | [157] | Nhãn tuổi dữ liệu xanh/đỏ |
| CIS 1.2 xử lý asset trái phép | Coverage = (M2 − M4)/M2, M2 = số asset trái phép, M4 = số asset trái phép *unreachable* sau scan (trang lại ghi metric = 1 khi M4 = 0, tức định nghĩa tự mâu thuẫn); fail nếu khung thời gian xử lý doanh nghiệp đặt > 7 ngày | [157] | Tile + bar tuổi hàng chờ; ô MSSP pass/fail |
| CIS 1.3 Asset Discovery Coverage | M1/M6 = asset phát hiện / inventory; fail nếu chu kỳ discovery > 24 giờ | [157] | Tile % + trend; ô MSSP pass/fail |
| CIS 1.4 CMDB Updating Accuracy | M6/M7 = thiết bị trong DHCP log có trong CMDB / thiết bị duy nhất trong DHCP log | [157] | Tile % + danh sách thiết bị DHCP chưa có trong kho |
| CIS 1.5 passive discovery | Mạng được phủ / tổng số mạng | [157] | Bar theo subnet/site |
| CIS 8.2 Collect Audit Logs | Asset cấu hình log đúng / asset có khả năng log | [151] | Stacked bar 100% theo criticality |
| CIS 8.9 Log Aggregating | Asset được ít nhất một hệ thống thu gom phủ / asset có khả năng log | [151] | Như trên; cột chính của ma trận MSSP |
| CIS 8.10 / 8.11 | Tỉ lệ hệ thống thu gom giữ log ≥ 90 ngày; fail nếu khoảng giữa hai lần review log > 7 ngày | [151] | Ô pass/fail |
| CDM AWARE | Scaled Base CVSS × Age × Weight [Threat, Impact] × Tolerance [Grace Period]; Age tính từ ngày công bố CVE, "90 days to double score"; thành phần UAH = "hardware devices that have not been assigned ownership in a dashboard container" | [152] | Công thức mẫu cho nguồn đóng góp điểm; tile "% asset chưa gán owner" |
| NIST SP 800-55 | Mỗi measure có target, time-based reference, data source, reporting format; ví dụ "percentage of systems with up-to-date patches", "color-coded risk matrix" | [158] | Phiếu đặc tả cho mọi widget |

CISA OT Asset Inventory Guidance (8/2025, 9 cơ quan đồng ký) xếp "Asset criticality" và "Logging" vào 14 thuộc tính ưu tiên cao, và chia criticality ba mức High/Medium/Low [162]. **Nhận định:** điều đó biện minh cho việc coi "% chưa phân loại criticality" và "% asset có log" là KPI chất lượng inventory hàng đầu, ngang với tổng asset. CAS tự ghi các metric chuẩn chỉ là ví dụ, không phải danh sách đầy đủ, nên sản phẩm có thể thêm chỉ số riêng như "% asset silent".

**Nhận định về người xem** (chưa có nguồn bậc 1 bàn trực tiếp cho SOC đa tenant): analyst cần trang asset, timeline, ego-graph và bảng top rủi ro; SOC lead cần KPI có ngưỡng, trend coverage và data health; khách hàng tenant cần ít chỉ số tổng (phủ EDR/log, exposure theo criticality, xu hướng so mục tiêu), tương ứng với việc NIST Vol.2 hướng tới lãnh đạo [160]; MSSP manager cần ma trận tenant × KPI và ranking.

### Dữ liệu: biểu đồ sự kiện lấy thẳng từ OCSF, biểu đồ trạng thái cần kho entity

Tên class và field trong ba bảng đều đã đối chiếu với file JSON của `ocsf/ocsf-schema` tag 1.9.0 (commit 856d462, 2026-08-03) [139]. Các biểu đồ dựa trên sự kiện lấy trực tiếp được: timeline và heatmap dùng `time`, `class_uid`, `activity_id`, `count`; telemetry và độ trễ dùng `metadata.product`, `metadata.log_source`, `metadata.logged_time`, `metadata.processed_time`; finding dùng Detection Finding 2004 (`risk_score`, `risk_level_id`, `is_alert`), Incident Finding 2005 (`priority_id`, `status_id`), Vulnerability Finding 2002 (`cve.cvss[]`, `cve.epss`, `is_exploit_available`, `is_fix_available`), Compliance Finding 2003 (`compliance.status_id` 1 Pass, 2 Warning, 3 Fail); trạng thái bảo vệ dùng Device Config State Change 5019 (`security_states[].state_id` như 4 Protection off, 11 Not installed); graph dùng object `graph` (`nodes`, `edges`) qua `finding_info.attack_graph` và `resource_details.resource_relationship` [139].

Các biểu đồ về trạng thái tài sản theo thời gian thì OCSF không nuôi được, vì schema không có thực thể asset bền vững. Object `device` có `first_seen_time`, `last_seen_time`, `is_managed`, `risk_score`, nhưng đó là giá trị một nguồn báo trong một event; `device` không có `criticality_id` (chỉ `resource_details` có), và `risk_score` của 2004 là "as reported by the event source" nên không so được giữa nguồn [139]. **Nhận định:** kho entity phải tự giữ asset_id hợp nhất theo (`tenant_uid`, asset_id), first/last seen theo từng nguồn, lifecycle state, criticality và owner thật, điểm rủi ro tổng hợp cùng lịch sử, cạnh quan hệ bền vững, và **snapshot đếm theo ngày**. Snapshot hằng ngày là thứ dễ bị bỏ quên nhất, nhưng thiếu nó thì mọi tile delta, sparkline và trend ở cấp tenant lẫn MSSP đều không vẽ được.

## Các nguồn bất đồng ở đâu

Ba điểm lệch đáng chú ý, cộng một mâu thuẫn khái niệm. Thứ nhất, Tenable tự mâu thuẫn về connector nào thắng khi không có dữ liệu native: trang Deduplication nói ưu tiên "by the order they were connected" [1], còn FAQ nói connector xử lý thành công đầu tiên làm nguồn chính, và trang FAQ còn sót ghi chú nội bộ "[SME REVIEW]" [163]. Nên tin trang chính hơn, nhưng bài học là thứ tự ưu tiên phải hiện rõ và chỉnh được, như chính Tenable làm với Information Order. Thứ hai, Tenable nói AES kết hợp VPR với ACR [164], trong khi trang scoring cloud nói ACR không ảnh hưởng AES [165]. Có lẽ khác nhau theo loại tài sản. Cả hai chỉ đọc qua trích đoạn nên chưa phân xử được. Thứ ba, các con số giảm alert của Splunk RBA lệch nhau giữa các tài liệu: 60–80% trong blog ES 6.4 [81], 30–80% trong ebook RBA (ghi chú là từ một testimonial) [14]. Không con số nào có phương pháp đo công bố, nên không dùng được làm benchmark. Về khái niệm, OCSF gộp "chủ sở hữu" với "người đăng nhập gần nhất" vào `endpoint.owner` [74], còn các vendor tách hai khái niệm này (Exabeam Top User, Rapid7 primary user theo số lần logon, DataBee owner gợi ý) [58][48][20]. Nên theo cách của vendor.

Elastic từng là chỗ phiên bản không khớp nhất giữa các bản docs preview; docs chính thức hiện ghi risk score history chart là GA từ Stack 9.5, còn graph preview trong flyout là Preview từ Stack 9.4 [23]. Nên coi đây là tính năng mới. Google SecOps định nghĩa prevalence không thống nhất giữa các trang ("số asset tối đa gần đây" và "số asset trong 7 ngày") [66][130]; với thiết kế, định nghĩa 7 ngày là đủ dùng. Trang CIS CAS (bản cho Controls v8.1) có công thức nghi lỗi đánh máy (Completeness 1.1 = "M8/M1", Tool Compliance Ratio 1.3 = "M3/M2") và định nghĩa M4 của 1.2 không khớp với cách tính metric [157]; nên dùng theo nghĩa của measure chứ không chép nguyên ký hiệu.

Về trường phái, Microsoft device inventory và Elastic Entity Analytics chọn "danh sách hành động" (count pill, bảng top N, gần như không chart) [50][144], trong khi Splunk, runZero, Axonius và Tenable chọn "toàn cảnh" bằng nhiều chart [140][24][147][145]. Phiên bản mạnh nhất của phe danh sách là: analyst cần biết làm gì tiếp theo, và chart nào cuối cùng cũng dẫn về danh sách. **Nhận định:** hai phe không mâu thuẫn nếu chart nào cũng bấm ra danh sách; ở cấp asset, với người xem là analyst, nên nghiêng về danh sách; ở cấp tenant và MSSP, với SOC lead hoặc khách hàng, cần chart xu hướng và cơ cấu. Brief có liệt kê Sankey, treemap và Venn coverage, nhưng trong docs đã đọc không vendor nào dùng Sankey hay treemap cho inventory; coverage được làm bằng Venn/intersection hoặc bảng nguồn × số asset [28][140].

## Kết luận và hàm ý

Phát hiện quan trọng nhất là giá trị của một asset profile cho SOC không nằm ở số trường, mà ở ba thuộc tính ít được quảng cáo. Một là **hợp nhất gỡ được và giải thích được** (Elastic resolution group, Axonius Explain, Tenable Cluster Logic). Hai là **provenance và last seen theo từng nguồn**, thứ biến profile thành công cụ coverage. Ba là **ngữ cảnh do người gán được tách khỏi dữ liệu dựng lại từ log**, để hệ thống rebuild được mà không mất công sức của analyst. Ngữ cảnh tài sản giúp giảm nhiễu, nhưng bằng chứng chỉ xác nhận *cơ chế*, chưa xác nhận *mức độ*. Vì vậy sản phẩm nên đo hiệu quả bằng dữ liệu tenant của chính nó ngay từ đầu.

Với mục đích của chủ repo, OCSF 1.9.0 là lớp vận chuyển đủ tốt cho dữ liệu quan sát, nhưng không thay được kho entity. Ba quyết định nên chốt sớm vì khó sửa về sau: khoá entity luôn mở đầu bằng `tenant_uid` cộng zone cho IP; thang criticality khớp `criticality_id` (1–4) của OCSF; và một extension nhỏ cho `asset_uid`, criticality, tag và role trên `device`/`user`. Khoảng trống chung của mọi vendor (cấu hình criticality theo tenant kế thừa template MSSP, quy trình duyệt cho sửa tay, suppression có hạn) cũng là chỗ sản phẩm có thể làm tốt hơn hiện trạng.

Về trực quan, điểm chung của các biểu đồ có giá trị ở cả ba cấp không nằm ở loại chart mà ở ba thuộc tính: có mốc so sánh (kỳ trước, mục tiêu, peer, ngưỡng CIS), bấm được ra danh sách asset cụ thể, và hiển thị kèm độ tươi của dữ liệu. Với sản phẩm SOC đa tenant trên OCSF, khoảng trống đáng khai thác nhất lại chính là chỗ vendor CAASM/XDR yếu: họ vẽ asset như một bản ghi cấu hình, còn một SOC quản lý log thì biết từng asset đang gửi gì từ nguồn nào. Vì thế sparkline telemetry theo nguồn trên trang asset, stacked bar độ phủ log theo CIS 8.9 ở cấp tenant, và ma trận tenant × KPI tô màu theo ngưỡng ở cấp MSSP là ba biểu đồ vừa khác biệt vừa dựng được từ `metadata.product` và `metadata.tenant_uid`.

Hàm ý cho lộ trình: MVP nên gồm risk trend có drill-down, nguồn đóng góp điểm, breakdown severity/MITRE, timeline overview + detail, telemetry theo nguồn, chip bảo vệ và vuln breakdown ở cấp asset; hàng KPI có delta/đích, lifecycle, asset mới, phân bố, coverage theo nguồn, độ phủ EDR/log, chất lượng inventory, heatmap exposure × criticality, top rủi ro và data health ở cấp tenant; ma trận tenant × KPI tô màu và health nguồn đa tenant ở cấp MSSP. Graph quan hệ, prevalence, attack path, peer comparison và benchmark nên đi sau, vì chúng phụ thuộc vào kho entity đã có role, cạnh quan hệ và lịch sử ổn định. Điều kiện tiên quyết kỹ thuật cho gần như toàn bộ danh sách MVP là kho entity lưu snapshot hằng ngày và lưu mỗi widget dưới dạng truy vấn có tên.

## Chưa kiểm chứng được

- Thuật toán merge chi tiết của Splunk A&I khi hai dòng chỉ trùng MAC mà khác IP, cùng giao diện cấu hình thứ hạng nguồn của Splunk Exposure Analytics: docs 8.x không mô tả, và một số trang chỉ đọc được qua tóm tắt search.
- IBM QRadar: docs IBM trả 403 với curl, WebFetch chỉ cho bản tóm tắt. Chưa có danh sách tab của asset profile, giá trị retention mặc định, hay ảnh UI.
- Rapid7 InsightIDR: chưa có thông tin về gộp agent ID với hostname, asset criticality hay tag, và không có ảnh.
- CrowdStrike Falcon host page và Identity Protection user page, SentinelOne Unified Asset Inventory, Armis device profile: docs cần đăng nhập hoặc chỉ có marketing. Các trang SentinelOne trả 429. Truy vấn đã thử: "CrowdStrike Falcon Identity Protection user profile risk score entity page screenshot", "SentinelOne Singularity asset inventory XDR unified asset view", "Armis Centrix device profile page".
- Securonix: host `legacy-documentation.securonix.com` bị chặn trong session, chỉ có snippet về peer group.
- Không có ảnh công khai cho Cortex XSIAM Host/User Risk View (Fluid Topics trả 500) và Trend Vision One device profile. Không có ảnh flyout Elastic 9.4+. Ảnh Elastic host details và ảnh Splunk có thể thuộc UI cũ.
- Thuật toán dedup của MDE giữa thiết bị discovered và onboarded: chưa thấy docs.
- Trọng số criticality trong Microsoft AI prioritization, Cortex SmartScore, Trend risk score: không vendor nào công bố.
- Hiệu quả giảm nhiễu đo độc lập: không tìm được nghiên cứu hay paper SANS. Truy vấn đã thử: "risk-based alerting case study alert reduction percent", "detection engineering asset context suppress vulnerability scanner false positives allowlist". PDF case study Fortune 100 của Splunk trả 404. Hướng dẫn MITRE DET0867 chỉ đọc được qua bản mirror bậc 3 nên không dùng.
- Cơ chế criticality hoặc tag riêng theo tenant kế thừa template MSSP: không vendor nào có tài liệu. Chưa xác minh XSIAM parent có xem asset inventory của child hay không. Chưa tìm hiểu Sentinel/Azure Lighthouse cho cross-workspace asset view.
- Nội dung PDF CISA/ASD "Best practices for event logging and threat detection" (2024-08-21) chưa đọc được (cyber.gov.au trả 503) [166]. Nhóm task INV của NIST SP 800-92r1 (bản ipd 2023) cũng chưa đọc.
- OCSF: chưa đối chiếu enum `device.type_id` sau khi compile trên schema.ocsf.io/1.9.0, chưa xem extension `windows`/`linux`/`macos`. Các PR đang mở #1750 (physical_site) và #1724 (agent trust-base inventory) mới chỉ biết tiêu đề.
- Blog Splunk ES 6.4 [81] trả 404 khi kiểm chứng lại (2026-11-03); con số 60–80% chỉ còn thấy qua trích đoạn search.
- Giá trị điểm cụ thể Exabeam cộng cho executive hay service account, và implementation peer group hiện tại (blog nguồn từ 2016).
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
- Sumo Logic: chưa khảo sát phần biểu đồ inventory.
- Cortex XSIAM Investigate a host/user [21][128]: lúc kiểm chứng lại (2026-11-03) trang trả HTTP 500, nên các mô tả Risk Score Trend, Compare To và widget breakdown chỉ dựa trên lần đọc của researcher cùng ngày, chưa đối chiếu lại.

## Nguồn

[1] Asset Deduplication in Tenable Exposure Management — Tenable Docs, © 2026 (bậc 1). https://docs.tenable.com/exposure-management/Content/getting-started/asset-deduping.htm
[2] Inbound integrations — runZero Docs, không rõ ngày (bậc 1). https://help.runzero.com/docs/integrations-inbound/
[3] Entity resolution — Elastic Docs (Stack 9.4+), không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/entity-resolution
[4] Exploring Asset Correlation — Axonius Docs, 2026-10-14 (bậc 1). https://docs.axonius.com/docs/correlation-explainability
[5] Review and classify critical assets — Microsoft Learn (Security Exposure Management), cập nhật 2026-10 (bậc 1). https://learn.microsoft.com/en-us/security-exposure-management/classify-critical-assets
[6] Exposure Management – Identifying and Triaging Unmanaged Assets — CrowdStrike Tech Hub, 2024-05-02 (bậc 1). https://www.crowdstrike.com/tech-hub/exposure-management/identifying-and-triaging-unmanaged-assets/
[7] Asset criticality — Trend Vision One Docs, không rõ ngày (bậc 1). https://docs.trendmicro.com/en-us/documentation/article/trend-vision-one-asset-criticality
[8] Device entity page in Microsoft Defender — Microsoft Learn, cập nhật 2026-09 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/entity-page-device
[9] Asset Profile View — Axonius Docs, 2026-10-14 (bậc 1). https://docs.axonius.com/docs/asset-profile-page
[10] Get to Know a User Profile — Exabeam Docs (Advanced Analytics), © 2026 (bậc 1). https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153664-get-to-know-a-user-profile.html
[11] Adjusting risk using risk factors in Splunk Enterprise Security (ES 8.4) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.4/risk-based-alerting/adjusting-risk-using-risk-factors-in-splunk-enterprise-security
[12] Entity risk scoring — Elastic Docs, bản hiện hành 2026 (bậc 1). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/entity-risk-scoring
[13] Manage Risk Scores (Cortex Cloud) — Palo Alto Networks Docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-cloud-runtime-security/asset-managment/manage-asset-scores.md
[14] The Splunk Guide to Risk-Based Alerting (ebook) — Splunk (marketing), không rõ ngày (bậc 1). https://www.splunk.com/en_us/pdfs/gated/ebooks/the-splunk-guide-to-risk-based-alerting.pdf
[15] Overlapping IP addresses (domain example) — IBM QRadar Docs, không rõ ngày (bậc 1). https://www.ibm.com/docs/SSKMKU/com.ibm.qradar.doc/c_domain_example_ip_separation.html
[16] Entity zones in Exposure Analytics (ES 8.7) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.7/exposure-analytics/entity-zones-in-exposure-analytics
[17] OCSF schema 1.9.0 – objects/metadata.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/metadata.json
[18] OCSF schema 1.9.0 – objects/device.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/device.json
[19] OCSF schema 1.9.0 – objects/resource_details.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/resource_details.json
[20] Asset and Entity Resolution — DataBee Docs, không rõ ngày (bậc 1 về điều vendor mô tả). https://docs.databee.buzz/docs/entity-resolution
[21] Investigate a host — Palo Alto Networks, Cortex XSIAM docs, không rõ ngày, truy cập 2026-11-03 (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/detect-investigate-and-respond-to-threats/investigation-and-response/investigate-artifacts-and-assets/investigate-a-host
[22] Access the intermediate findings timeline to review findings in Splunk Enterprise Security — Splunk, ES 8.5, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.5/risk-based-alerting/access-the-intermediate-findings-timeline-to-review-findings-in-splunk-enterprise-security
[23] View entity details — Elastic Security docs, không rõ ngày, truy cập 2026-11-03 (bậc 1; risk score history GA từ Stack 9.5, graph preview là Preview từ 9.4). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/view-entity-details
[24] Dashboard — runZero docs, cập nhật 2026-09-17 (bậc 1). https://www.runzero.com/docs/dashboard/
[25] Chart Click-Through — Axonius, không rõ ngày (bậc 1). https://docs.axonius.com/docs/chart-click-through
[26] Defender Vulnerability Management overview page (dashboard insights) — Microsoft Learn, 2025–2026 (bậc 1). https://learn.microsoft.com/en-us/defender-vulnerability-management/tvm-dashboard-insights
[27] Device Discovery Chart — Axonius, không rõ ngày (bậc 1). https://docs.axonius.com/docs/device-discovery-chart
[28] Query Intersection Chart — Axonius, không rõ ngày (bậc 1). https://docs.axonius.com/docs/query-intersection-chart
[29] Asset & Identity for Splunk Enterprise Security Part 1: Contextualizing Systems — Splunk (blog vendor), 2020-03-27 (bậc 1). https://www.splunk.com/en_us/blog/security/asset-identity-for-splunk-enterprise-security-part-1-contextualizing-systems.html
[30] View and Manage Entities — Sumo Logic Cloud SIEM Docs, không rõ ngày (bậc 1). https://www.sumologic.com/help/docs/cse/records-signals-entities-insights/view-manage-entities/
[31] Asset criticality — Elastic Docs, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/asset-criticality
[32] Introducing Exposure Analytics in Splunk Enterprise Security — Splunk (blog vendor), 2026-04-23 (bậc 1). https://www.splunk.com/en_us/blog/security/introducing-exposure-analytics-in-splunk-enterprise-security.html
[33] From Static A&I to Continuous Entity Discovery (Using Exposure Analytics in Splunk ES) — Splunk (blog vendor), 2026-06-12 (bậc 1). https://www.splunk.com/en_us/blog/security/using-exposure-analytics-in-splunk-es.html
[34] Entity store — Elastic Docs (Stack 9.4+), không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/entity-store
[35] Device discovery overview — Microsoft Learn, cập nhật 2026-04 (bậc 1). https://learn.microsoft.com/en-us/defender-endpoint/device-discovery
[36] Asset inventory overview (Cortex XSIAM) — Palo Alto Networks Docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/detect-investigate-and-respond-to-threats/asset-management/asset-inventory-overview.md
[37] Populate Splunk ES asset and identity lookups with entity discovery data (ES 8.8) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.8/exposure-analytics/populate-splunk-es-asset-and-identity-ai-lookups-with-entity-discovery-data
[38] How urgency is assigned to notable events in Splunk Enterprise Security (ES 7.2) — Splunk, 2023–2024 (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-7/user-guide/7.2/incident-review/how-urgency-is-assigned-to-notable-events-in-splunk-enterprise-security
[39] Review risk-based findings in Splunk Enterprise Security (ES 8.3) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.3/risk-based-alerting/review-risk-based-findings-in-splunk-enterprise-security
[40] Configure aliasing — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/event-processing/aliasing-overview
[41] Investigate users — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/investigation/investigate-user
[42] Risk Analytics overview — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/detection/risk-analytics-overview
[43] Overview of context-aware analytics — Google SecOps docs, 2025–2026 (bậc 1). https://docs.cloud.google.com/chronicle/docs/detection/context-aware-analytics
[44] Data enrichment and aliasing overview — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/event-processing/overview-of-aliasing-and-enrichment
[45] Asset profiles (QRadar 7.5) — IBM Docs, không rõ ngày (bậc 1; chỉ đọc qua bản tóm tắt). https://www.ibm.com/docs/en/qsip/7.5?topic=management-asset-profiles
[46] Asset reconciliation exclusion rules — IBM QRadar Docs, không rõ ngày (bậc 1). https://www.ibm.com/docs/en/SSKMKU/com.ibm.qradar.doc/c_qradar_ug_asset_recon_rules.html
[47] Prevention of asset growth deviations — IBM QRadar Docs, không rõ ngày (bậc 1). https://www.ibm.com/docs/en/SSKMKU/com.ibm.qradar.doc/c_qradar_adm_prevent_asset_grwth_deviat.html
[48] User Attribution — Rapid7 InsightIDR Docs, không rõ ngày (bậc 1). https://docs.rapid7.com/insightidr/user-attribution/
[49] Entity criticality — Sumo Logic Cloud SIEM Docs, không rõ ngày (bậc 1). https://www.sumologic.com/help/docs/cse/records-signals-entities-insights/entity-criticality/
[50] Explore devices in the device inventory — Microsoft Learn, cập nhật 2026-07 (bậc 1). https://learn.microsoft.com/en-us/defender-endpoint/machines-view-overview
[51] Investigate Identities — Microsoft Learn, cập nhật 2026-10 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/investigate-users
[52] Investigate devices in the Microsoft Defender for Endpoint devices list — Microsoft Learn, cập nhật 2026-07 (bậc 1). https://learn.microsoft.com/en-us/defender-endpoint/investigate-machines
[53] Asset Roles (Cortex XSIAM) — Palo Alto Networks Docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/detect-investigate-and-respond-to-threats/asset-management/asset-configurations/asset-roles.md
[54] Device profile — Trend Vision One Docs, không rõ ngày (bậc 1). https://docs.trendmicro.com/en-us/documentation/article/trend-vision-one-device-profile
[55] Asset Details (Tenable Exposure Management) — Tenable Docs, © 2026 (bậc 1). https://docs.tenable.com/exposure-management/Content/inventory/asset-details.htm
[56] Understanding assets — runZero Docs, không rõ ngày (bậc 1). https://help.runzero.com/docs/understanding-assets/
[57] What are Assets & Networks — Exabeam Docs (Advanced Analytics admin guide), © 2026 (bậc 1). https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/administration-guide/set-up-authentication-and-access-control/what-are-assets---networks-.html
[58] Get Started with the Asset Page — Exabeam Docs (Advanced Analytics), © 2026 (bậc 1). https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153684-get-started-with-the-asset-page.html
[59] Entity Analytics — Exabeam Docs (Advanced Analytics), © 2026 (bậc 1; đọc qua trích đoạn search). https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153683-entity-analytics.html
[60] IT hygiene — Wazuh documentation (current, ≈4.14), không rõ ngày (bậc 1). https://documentation.wazuh.com/current/getting-started/use-cases/it-hygiene.html
[61] Turn off merge for assets and identities in Splunk Enterprise Security (ES 8.4) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.4/asset-and-identity-management/turn-off-merge-for-assets-and-identities-in-splunk-enterprise-security
[62] Exposure Analytics diagnostics (ES 8.6) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.6/exposure-analytics/exposure-analytics-diagnostics
[63] Critical asset management overview — Microsoft Learn (Security Exposure Management), cập nhật 2026-10 (bậc 1). https://learn.microsoft.com/en-us/security-exposure-management/critical-asset-management
[64] Work with attack paths — Microsoft Learn (Security Exposure Management), cập nhật 2026-10 (bậc 1). https://learn.microsoft.com/en-us/security-exposure-management/work-attack-paths-overview
[65] Entity pages in Microsoft Sentinel — Microsoft Learn, cập nhật 2026-05 (bậc 1). https://learn.microsoft.com/en-us/azure/sentinel/entity-pages
[66] Investigate assets — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/investigation/investigate-asset
[67] Asset and identity investigator dashboards (ES 8.7) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/user-guide/8.7/analytics/asset-and-identity-investigator-dashboards
[68] Investigate a host (Cortex XSIAM) — Palo Alto Networks Docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/detect-investigate-and-respond-to-threats/investigation-and-response/investigate-artifacts-and-assets/investigate-a-host.md
[69] Users and Accounts — Rapid7 InsightIDR Docs, không rõ ngày (bậc 1). https://docs.rapid7.com/insightidr/users-and-accounts-on-your-domain/
[70] Hosts page — Elastic Docs, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/explore/hosts-page
[71] Entity analysis dashboard (ES 8.5) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/user-guide/8.5/exposure-analytics-and-ueba/entity-analysis-dashboard
[72] How to Detect Gaps in Endpoint Protection with Axonius — Axonius (blog vendor), 2025-06-02 (bậc 1). https://www.axonius.com/blog/detect-gaps-endpoint-protection-axonius
[73] Investigate a user (Cortex XSIAM) — Palo Alto Networks Docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/detect-investigate-and-respond-to-threats/investigation-and-response/investigate-artifacts-and-assets/investigate-a-user.md
[74] OCSF schema 1.9.0 – objects/endpoint.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/endpoint.json
[75] Create risk factors to adjust risk scores in Splunk Enterprise Security (ES 8.1) — Splunk, 2025 (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.1/risk-based-alerting/create-risk-factors-to-adjust-risk-scores-in-splunk-enterprise-security
[76] Risk Scores (Graylog Security 7.2) — Graylog Docs, không rõ ngày (bậc 1). https://go2docs.graylog.org/current/what_more_can_graylog_do_for_me/risk_scoring.htm
[77] What are Accounts & Groups — Exabeam Docs (Advanced Analytics admin guide), © 2026 (bậc 1; đọc qua trích đoạn search). https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/administration-guide/set-up-authentication-and-access-control/what-are-accounts---groups-.html
[78] Who Do I Belong To? Dynamic Peer Analysis for UEBA Explained — Derek Lin, Exabeam (blog vendor), 2016-09-20 (bậc 1, cũ). https://www.exabeam.com/blog/ueba/who-do-i-belong-to-dynamic-peer-analysis-for-ueba-explained/
[79] Prioritize incidents (Legacy) — Microsoft Learn, cập nhật 2026-09 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/incident-queue
[80] Introducing AI-powered incident prioritization in Microsoft Defender — Microsoft Tech Community (blog vendor), 2026-01 (bậc 1). https://techcommunity.microsoft.com/blog/microsoftthreatprotectionblog/introducing-ai-powered-incident-prioritization-in-microsoft-defender/4483834
[81] Better detections and cloud coverage with Splunk Enterprise Security 6.4 — Splunk (blog vendor, marketing), không rõ ngày (bậc 1; trả 404 ngày 2026-11-03, chỉ đọc qua trích đoạn search). https://splunk.com/en_us/blog/security/better-detections-and-cloud-coverage-with-splunk-enterprise-security-6-4.html
[82] Johnson Matthey customer success story — Splunk (marketing), không rõ ngày (bậc 1). https://splunk.com/content/dam/splunk2/en_us/pdfs/customer-success-stories/johnson-matthey.pdf
[83] Risk-Based Alerting: The New Frontier for SIEM — Splunk (blog vendor, marketing), không rõ ngày (bậc 1). https://www.splunk.com/en_us/blog/security/risk-based-alerting-the-new-frontier-for-siem
[84] Managing risk using risk-based alerting in Splunk Enterprise Security – best practices (ES 7.3) — Splunk, 2024 (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-7/risk-based-alerting/7.3/best-practices/managing-risk-using-risk-based-alerting-in-splunk-enterprise-security
[85] View and analyze risk score data — Elastic Docs, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/view-analyze-risk-score-data
[86] Silent-host monitoring — Google SecOps docs, 2025–2026 (bậc 1). https://docs.cloud.google.com/chronicle/docs/ingestion/silent-host-monitoring
[87] Check data ingestion health — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/ingestion/ingestion-overview
[88] Monitor the health of your data connectors — Microsoft Learn, 2026-07-02 (bậc 1). https://learn.microsoft.com/en-us/azure/sentinel/monitor-data-connector-health
[89] Devices in multitenant management — Microsoft Learn, 2024-03-15, cập nhật 2026-09 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/mto-tenant-devices
[90] CIS Controls Assessment Specification – Safeguard 8.2 — Center for Internet Security, không rõ ngày (bậc 1). https://controls-assessment-specification.readthedocs.io/en/latest/control-8/control-8.2.html
[91] CIS Controls Assessment Specification – Safeguard 1.1 — Center for Internet Security, không rõ ngày (bậc 1). https://controls-assessment-specification.readthedocs.io/en/latest/control-1/control-1.1.html
[92] MSSP multi-tenant (Cortex XSIAM) — Palo Alto Networks Docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/configure-cortex-xsiam/multi-tenant/what-is-cortex-xsiam-multi-tenant/mssp-multi-tenant
[93] Data RBAC overview — Google SecOps docs, 2025–2026 (bậc 1). https://docs.cloud.google.com/chronicle/docs/administration/datarbac-overview
[94] Impact of data RBAC on features — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/administration/datarbac-impact
[95] Multi-tenancy on a single Google SecOps, part 3: who sees what and where the alert lands — Google Cloud Security Community, không rõ ngày (bậc 2–3, community). https://security.googlecloudcommunity.com/google-security-operations-2/multi-tenancy-on-a-single-google-secops-part-3-who-sees-what-and-where-the-alert-lands-7899
[96] Domain definition and tagging — IBM QRadar Docs, không rõ ngày (bậc 1). https://www.ibm.com/docs/en/SSKMKU/com.ibm.qradar.doc/c_domain_defining.html
[97] QRadar domains and multi-tenancy — Holly Wright, IBM Community, 2020-04-24 (bậc 2). https://community.ibm.com/community/user/blogs/holly-wright/2020/04/24/qradar-domains-and-multi-tenancy
[98] Enable entity zones (ES 6.4.1) — Splunk, không rõ ngày (bậc 1, bản cũ). https://docs.splunk.com/Documentation/ES/6.4.1/Admin/Entityzones
[99] Wazuh dashboard multi-tenancy — Wazuh documentation, không rõ ngày (bậc 1). https://documentation.wazuh.com/current/user-manual/wazuh-dashboard/multi-tenancy.html
[100] Format an asset or identity list as a lookup in Splunk ES — Splunk, không rõ ngày (bậc 1). https://docs.splunk.com/Documentation/ES/latest/User/AssetandIdentityLookupReference
[101] OCSF schema CHANGELOG.md (tag 1.9.0) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md
[102] OCSF schema 1.9.0 – events/discovery/discovery.json — OCSF (GitHub), tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/discovery.json
[103] OCSF schema 1.9.0 – Device Inventory Info (events/discovery/inventory_info.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/inventory_info.json
[104] OCSF schema 1.9.0 – User Inventory Info (events/discovery/user_inventory.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/user_inventory.json
[105] OCSF schema 1.9.0 – Software Inventory Info (events/discovery/software_info.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/software_info.json
[106] OCSF schema 1.9.0 – Cloud Resources Inventory Info (events/discovery/cloud_resources_inventory_info.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/cloud_resources_inventory_info.json
[107] OCSF schema 1.9.0 – Device Config State Change (events/discovery/device_config_state_change.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/device_config_state_change.json
[108] OCSF schema 1.9.0 – Operating System Patch State (events/discovery/patch_state.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/patch_state.json
[109] OCSF schema 1.9.0 – Authentication (events/iam/authentication.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/iam/authentication.json
[110] OCSF schema 1.9.0 – Network Activity (events/network/network_activity.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network_activity.json
[111] OCSF schema 1.9.0 – profiles/host.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/profiles/host.json
[112] OCSF schema 1.9.0 – events/findings (Vulnerability/Compliance/Detection Finding) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/tree/1.9.0/events/findings
[113] OCSF schema 1.9.0 – User Management (events/iam/user_management.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/iam/user_management.json
[114] OCSF schema 1.9.0 – objects/device_hw_info.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/device_hw_info.json
[115] OCSF schema 1.9.0 – objects/agent.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/agent.json
[116] OCSF schema 1.9.0 – objects/network_interface.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/network_interface.json
[117] OCSF schema 1.9.0 – objects/user.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/user.json
[118] OCSF schema 1.9.0 – objects/ldap_person.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/ldap_person.json
[119] OCSF schema 1.9.0 – objects/_resource.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/_resource.json
[120] Add criticality_id, device, user to resource_details (PR #1693) — Paul Agbabian, OCSF (GitHub), merge 2026-07-28 (bậc 1). https://github.com/ocsf/ocsf-schema/pull/1693
[121] Issue #833: customer_uid / tenant identifier — Mike Radka, OCSF (GitHub), 2023-10-27 → đóng 2023-11-09 (bậc 1). https://github.com/ocsf/ocsf-schema/issues/833
[122] OCSF schema 1.9.0 – objects/enrichment.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/enrichment.json
[123] OCSF schema 1.9.0 – objects/observable.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/observable.json
[124] Sample exposure finding — AWS Security Hub Docs, mẫu 2024-11 (bậc 1). https://docs.aws.amazon.com/securityhub/latest/userguide/exposure-findings-sample.html
[125] Open Cybersecurity Schema Framework (OCSF) in Security Lake — AWS Docs, không rõ ngày (bậc 1). https://docs.aws.amazon.com/security-lake/latest/userguide/open-cybersecurity-schema-framework.html
[126] Enrich with asset inventory — Tenzir Docs, không rõ ngày (bậc 2). https://tenzir.com/docs/guides/enrich/enrich-with-asset-inventory/
[127] What's new in OCSF 1.4.0 — Jonathan Rau, Query, 2025-02-06 (bậc 2). https://www.query.ai/resources/blogs/whats-new-ocsf-1_4_0/
[128] Investigate a user — Palo Alto Networks, Cortex XSIAM docs, không rõ ngày, truy cập 2026-11-03 (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/detect-investigate-and-respond-to-threats/investigation-and-response/investigate-artifacts-and-assets/investigate-a-user
[129] Investigate an IP address — Google Cloud, Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/investigation/investigate-ipaddress
[130] Review an alert — Google Cloud, Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/review-alert
[131] Causality view — Palo Alto Networks, Cortex XDR 5.x docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xdr-5.x/detect-investigate-and-respond-to-threats/investigate-and-respond-to-cases/investigate-issues/causality-view
[132] Visual event analyzer — Elastic, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/investigate/visual-event-analyzer
[133] Session view — Elastic, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/investigate/session-view
[134] Investigate incidents (investigation graph) — Microsoft Learn, Microsoft Sentinel, không rõ ngày (bậc 1). https://learn.microsoft.com/en-us/azure/sentinel/investigate-incidents
[135] Graph Overview (Asset Graph) — Axonius, 2024 (bậc 1). https://docs.axonius.com/docs/asset-graph-overview
[136] Exploring connections and asset relationships — Axonius, 2024 (bậc 1). https://docs.axonius.com/docs/exploring-connections-and-asset-relationships
[137] Trend Vision One February 2024 release note — Trend Micro, 2024-02 (bậc 1, chỉ đọc qua snippet tìm kiếm). https://docs.trendmicro.com/en-us/documentation/article/trend-vision-one-february-2024
[138] Review attack paths — Microsoft Learn, Microsoft Security Exposure Management, không rõ ngày, truy cập 2026-11-03 (bậc 1). https://learn.microsoft.com/en-us/security-exposure-management/review-attack-paths
[139] OCSF Schema, tag 1.9.0 (commit 856d462; các file finding, detection_finding, incident_finding, compliance_finding, vulnerability, cve, metadata, device, endpoint, device_config_state_change, security_state, graph, finding_info, dictionary) — OCSF, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/tree/1.9.0
[140] Deeper Exposure Analytics in Splunk Enterprise Security 8.6 — Splunk blog, 2026-08-04 (bậc 1). https://www.splunk.com/en_us/blog/security/deeper-exposure-analytics-in-splunk-enterprise-security-8-6.html
[141] Use the Health Hub — Google Cloud, Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/reports/data-health-monitoring-and-troubleshooting-dashboard
[142] Agent Coverage Dashboards — Axonius, không rõ ngày (bậc 1). https://docs.axonius.com/docs/agent-coverage-dashboards
[143] Dashboard Design: Getting Started With Best Practices (Part 1) — Lizzy Li, Splunk, 2022-09-01 (bậc 1 về điều vendor khuyến nghị). https://www.splunk.com/en_us/blog/tips-and-tricks/dashboard-design-getting-started-with-best-practices-part-1.html
[144] Entity Analytics dashboard — Elastic, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/dashboards/entity-analytics-dashboard
[145] Dashboard Overview — Tenable Exposure Management docs, không rõ ngày; ảnh 2025 (bậc 1). https://docs.tenable.com/exposure-management/Content/analytics/dashboard-overview.htm
[146] Get started with Microsoft Security Exposure Management — Microsoft Learn, cập nhật 2026-07-26 (bậc 1). https://learn.microsoft.com/en-us/security-exposure-management/get-started-exposure-management
[147] Creating Dashboards and Charts with the AI Agent (danh mục loại chart) — Axonius, không rõ ngày (bậc 1). https://docs.axonius.com/docs/creating-dashboards-and-charts-with-the-ai-agent
[148] Viewing system inventory data — Wazuh documentation (4.13+), 2025–2026 (bậc 1). https://documentation.wazuh.com/current/user-manual/capabilities/system-inventory/viewing-system-inventory-data.html
[149] Release 4.13.0 — Wazuh, 2025-09-18 (bậc 1). https://documentation.wazuh.com/current/release-notes/release-4-13-0.html
[150] Query Timeline Chart — Axonius, không rõ ngày (bậc 1). https://docs.axonius.com/docs/query-timeline-chart
[151] CIS Controls Assessment Specification for Controls v8.1 — Control 8: Audit Log Management — Center for Internet Security, không rõ ngày (bậc 1). https://cas.docs.cisecurity.org/en/latest/source/Controls8/
[152] CDM Program AWARE Scoring fact sheet — CISA, 2020-09 (bậc 1). https://www.cisa.gov/sites/default/files/2023-01/cdm-program-aware-scoring-fact-sheet-092020-508_1.pdf
[153] Track your Microsoft Secure Score history, metrics, and trends — Microsoft Learn, không rõ ngày (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/microsoft-secure-score-history-metrics-trends
[154] Manage Microsoft Sentinel workspaces at scale — Microsoft Learn, Azure Lighthouse, không rõ ngày (bậc 1, nội dung đọc qua snippet). https://learn.microsoft.com/en-us/azure/lighthouse/how-to/manage-sentinel-workspaces
[155] Extend Microsoft Sentinel across workspaces and tenants — Microsoft Learn, không rõ ngày (bậc 1, nội dung đọc qua snippet). https://learn.microsoft.com/en-us/azure/sentinel/extend-sentinel-across-workspaces-tenants
[156] Azure Workbooks link actions — Microsoft Learn, 2026-04-02 (bậc 1). https://learn.microsoft.com/en-us/azure/azure-monitor/visualize/workbooks-link-actions
[157] CIS Controls Assessment Specification for Controls v8.1 — Control 1: Inventory and Control of Enterprise Assets — Center for Internet Security, không rõ ngày (bậc 1). https://cas.docs.cisecurity.org/en/latest/source/Controls1/
[158] NIST SP 800-55 Vol. 1: Measurement Guide for Information Security — Identifying and Selecting Measures — NIST, 2024-12 (bậc 1). https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-55v1.pdf
[159] Review security initiatives — Microsoft Learn, Microsoft Security Exposure Management, cập nhật 2026-10-09 (bậc 1). https://learn.microsoft.com/en-us/security-exposure-management/initiatives
[160] NIST SP 800-55 Vol. 2: Measurement Guide for Information Security — Developing an Information Security Measurement Program — NIST, 2024-12 (bậc 1). https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-55v2.pdf
[161] Graph visualization: fixing data hairballs — Dan Williams, Cambridge Intelligence, 2019-11-25 (bậc 2). https://cambridge-intelligence.com/how-to-fix-hairballs/
[162] Foundations for OT Cybersecurity: Asset Inventory Guidance for Owners and Operators — CISA và 8 cơ quan đồng ký, 2025-08-13 (bậc 1). https://www.cisa.gov/sites/default/files/2025-08/joint-guide-foundations-for-OT-cybersecurity-asset-inventory-guidance_508c.pdf
[163] Asset Deduplication FAQ — Tenable Docs, © 2026 (bậc 1). https://docs.tenable.com/exposure-management/Content/getting-started/asset-dedup-faq.htm
[164] Host Asset Details (Tenable Vulnerability Management) — Tenable Docs, không rõ ngày (bậc 1; đọc qua trích đoạn search). https://docs.tenable.com/vulnerability-management/Content/Explore/asset-details-hosts.htm
[165] Cloud Security (CS) scoring explained — Tenable Docs, không rõ ngày (bậc 1; đọc qua trích đoạn search). https://docs.tenable.com/quick-reference/scoring-explained/Content/cloud-security.htm
[166] Best practices for event logging and threat detection — ASD's ACSC, CISA và các đối tác, 2024-08-21 (bậc 1). https://cisa.gov/resources-tools/resources/best-practices-event-logging-and-threat-detection
