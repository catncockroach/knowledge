---
title: Asset profile và giao diện asset/user profile của các vendor security, và bài học cho SOC đa tenant trên OCSF 1.9.0
date: 2026-11-03
question: Trong các nền tảng SIEM/XDR/CAASM, asset profile và user profile được xây dựng thế nào, giao diện thể hiện thông tin và tác vụ gì, và nên thiết kế quản lý tài sản + asset profile cho tenant SOC (dữ liệu OCSF v1.9.0) ra sao?
tags: [asset-management, entity-resolution, soc, ocsf, multi-tenant, ueba]
---

# Asset profile tốt là hồ sơ hợp nhất có provenance, khoá theo tenant

> **Câu hỏi:** Vendor dựng asset/user profile và giao diện profile thế nào, và nên thiết kế quản lý tài sản + asset profile cho SOC đa tenant trên OCSF 1.9.0 ra sao? · **Ngày:** 2026-11-03 · **Phạm vi:** Splunk ES, Google SecOps, Elastic Security, IBM QRadar, Rapid7 InsightIDR, Sumo Logic, Microsoft Defender XDR/Sentinel/Exposure Management, Cortex XSIAM, Trend Vision One, CrowdStrike Falcon, Axonius, Tenable, runZero, Exabeam, Wazuh, Graylog; schema OCSF tag 1.9.0; docs chính thức 2023–2026. · **Kiểm chứng:** khoảng 140 khẳng định đã đối chiếu nguồn (≈ 80 qua 25 lần mở trang vendor/GitHub, ≈ 60 tên class/field/enum OCSF đối chiếu file schema tag 1.9.0), 9 đã sửa

## Tóm tắt

Các vendor đang hội tụ về cùng một mô hình: **một hồ sơ hợp nhất cho mỗi asset hoặc identity, dựng từ nhiều nguồn quan sát**, mỗi giá trị biết nguồn nào báo và thấy lần cuối khi nào, cộng thêm ba trục điểm tách nhau: criticality do người hoặc rule gán, risk từ alert, exposure từ lỗ hổng và cấu hình. Họ khác nhau chủ yếu ở cách hợp nhất (gộp khi trùng bất kỳ khoá nào, khoá có thứ tự ưu tiên, hay nhóm primary/alias gỡ được), và ở chỗ UI xoay quanh "hồ sơ bền vững" (Microsoft, Elastic, Sumo, Axonius, Tenable) hay "trang điều tra theo thời gian" (Google, Splunk, Exabeam). Ngữ cảnh tài sản được dùng để giảm nhiễu qua ba cơ chế có tài liệu rõ: ma trận severity × priority, hệ số nhân/cộng vào risk score, và đổi baseline theo vai trò hoặc nhóm tài sản. Các con số giảm 30–80% alert đều là tuyên bố của vendor, không có đo lường độc lập. Đa tenant chỉ có QRadar (khoá domain + IP), Splunk (zone + IP) và runZero (site) mô tả rõ cách xử lý IP private trùng nhau. OCSF 1.9.0 cung cấp đủ dữ liệu quan sát (class Inventory, Activity, Finding và `metadata.tenant_uid`), nhưng không có thực thể asset bền vững, và `criticality_id` chỉ nằm trên `resource_details`. Vì vậy sản phẩm cần một kho entity riêng theo tenant cùng một extension OCSF nhỏ. Mức chắc chắn về cơ chế là cao (phần lớn từ docs bậc 1). Về hiệu quả giảm nhiễu thì thấp, và về các vendor có docs khoá (CrowdStrike, SentinelOne, Armis, Securonix) cũng thấp.

**Điểm chính**
- Hợp nhất an toàn nhất là khoá có thứ tự ưu tiên, kèm khoá chặn (hai agent ID khác nhau thì không bao giờ gộp), cửa sổ thời gian cho IP, và nhóm primary/alias có unlink và giải thích được [1][2][3][4].
- Criticality hội tụ về **3–4 mức**: gán bằng classifier hoặc rule, khi nhiều rule cùng khớp thì mức cao nhất thắng, ghi đè thủ công có ô ghi lý do, tài sản dưới ngưỡng tự phân loại vào hàng chờ duyệt [5][6][7].
- UI chuẩn de facto: header (định danh, risk, criticality, tag, action) → tab → sidebar thuộc tính và thẻ KPI có "View all". CAASM thêm provenance theo từng trường, UEBA thêm risk trend kèm lý do điểm [8][9][10].
- Giảm nhiễu: Splunk có sẵn risk factor nhân **×1,5** cho đích critical (mặc định tắt), Elastic nhân trọng số **0,5–2** theo criticality, Cortex đẩy alert nhỏ trên asset quan trọng lên. Mức giảm alert 30–80% của Splunk RBA chỉ là tuyên bố vendor [124][12][13][14].
- Đa tenant: mọi khoá entity phải chứa tenant. `metadata.tenant_uid` của OCSF chỉ là *recommended*, nên pipeline phải bắt buộc điền nó [15][16][17].
- OCSF 1.9.0 thiếu thực thể asset bền vững, provenance, lifecycle, coverage theo nguồn, cùng `criticality_id`/`tags` trên `device`. Các bên dùng OCSF (DataBee, AWS, Tenzir) đều tự xây kho entity riêng [18][19][20].

## Vendor hội tụ về "một hồ sơ, nhiều nguồn quan sát" nhưng hợp nhất theo ba kiểu khác nhau

### Từ bảng ngữ cảnh do admin nạp sang inventory tự khám phá từ telemetry

Thế hệ cũ dựa vào bảng ngữ cảnh do admin nạp vào. Splunk ES Asset & Identity poll lookup từ CMDB, AD, LDAP rồi merge các list [21]. Sumo Logic import metadata entity bằng CSV [22]. Elastic import asset criticality bằng CSV [23]. Hướng 2025–2026 là tự khám phá từ dữ liệu đã có. **Splunk Exposure Analytics** (RSAC 2026) khám phá liên tục workstation, server, cloud asset và IoT [24]. Nó tách nguồn "streaming" (DHCP, VPN, EDR: cái gì đang chạy, quan hệ IP–host–user tại một thời điểm) khỏi nguồn "batch" (CMDB, scanner: làm giàu metadata), và dùng source prioritization để giải xung đột [25]. Elastic entity store đối soát entity từ log, IdP, alert và kho asset ngoài, theo từng space [26]. Microsoft Defender dùng chính endpoint đã onboard làm cảm biến khám phá thiết bị unmanaged. Chế độ Standard quét chủ động mỗi thiết bị **không quá một lần mỗi ba tuần**, dưới **50 KB** mỗi lần [27]. Cortex XSIAM "collects, normalizes, and aggregates data from multiple sensors to create a single, holistic profile for each asset" [28]. **Nhận định:** sản phẩm của chủ repo đã có sẵn log OCSF của tenant, nên ở vị trí giống Splunk Exposure Analytics và Elastic: dựng inventory từ telemetry, coi CMDB/IdP chỉ là một nguồn có thứ hạng, không phải nguồn sự thật duy nhất.

| Vendor | Nguồn dựng profile | Khoá định danh / cách hợp nhất | IP động, vòng đời | Criticality | Điểm rủi ro |
|---|---|---|---|---|---|
| Splunk ES | Lookup CMDB/AD/LDAP; Exposure Analytics: CMDB, EDR, DHCP, VPN, scanner [21][25] | Gộp khi trùng bất kỳ `ip`/`dns`/`mac`/`nt_host`; list hạng cao thắng khi xung đột [21] | Lịch sử discovery theo thời điểm [25]; đẩy entity thấy trong **30 ngày**, mỗi **15 phút** [29] | `priority` vào urgency [30] | Entity risk score từ risk event 7 ngày [31] |
| Google SecOps | Log, DHCP, EDR, AD/Workday/Okta, entity context [32][33] | Aliasing DHCP/EDR; ưu tiên alias asset hostname > mac > asset_id > ip [34] | Alias theo thời gian; context có validity interval [35] | Context do admin nạp (entity data, data tables) [36] | max finding + 0,2 × tổng còn lại, chuẩn hoá 1–1000 [34] |
| Elastic Security | Log, IdP, alert, kho asset ngoài [26] | EUID `host.id` > `host.name` > `host.hostname`; resolution group primary/alias [26][3] | Snapshot lịch sử hằng ngày [26] | 4 mức low → extreme [23] | 0–100, nhân 0,5–2 theo criticality, tính lại mỗi giờ [12] |
| IBM QRadar | Flow hai chiều, scanner VA, identity event [37] | Đối soát MAC/NetBIOS/DNS/IP; blocklist dữ liệu "nhảy" [38] | MAC gắn ≥ 3 IP trong 2 giờ → blocklist; retention threshold [38][39] | Không rõ | Không rõ |
| Rapid7 InsightIDR | Event source, agent, network sensor, DHCP [40] | Attribution IP → asset theo thời gian; primary user = user logon nhiều nhất trong tuần [40] | Theo DHCP | Không rõ | Không rõ |
| Sumo Logic | Entity tạo khi signal bắn lần đầu; import CSV [22] | Theo giá trị field entity | Không rõ | Biểu thức severity (`severity+2`) [41] | Activity score = tổng severity trong 2 tuần [41] |
| Microsoft Defender XDR | Agent MDE, network discovery, MDI, Entra, cloud [42][27] | Nhiều account gộp thành một identity có primary account [43] | Tag internet-facing tự bỏ sau **48 giờ** [44] | 4 mức: classifier, custom rule, thủ công [5] | Risk (alert) tách khỏi exposure [8]; identity 0–100 có decay [43] |
| Cortex XSIAM | Nhiều sensor, Workday, AD [28][13] | Gộp điểm theo đúng hostname/username [13] | Active 0–3 → Not Seen 3–5 → Lost 5–7 ngày → ẩn [28] | Asset Roles tự phân loại [45] | Tổng điểm case/alert, thường 10–100 [13] |
| Trend Vision One | Các nguồn đã kết nối [7] | Không rõ | Không rõ | 3 mức từ profile tag, đánh giá hằng ngày [7] | Tính lại mỗi 4 giờ trên 30 ngày [46] |
| CrowdStrike Falcon | Sensor khám phá unmanaged, ServiceNow [6] | Không rõ (docs khoá) | Managed / Unmanaged / Unsupported | Critical/High/Noncritical/Unassigned + lý do [6] | Không rõ |
| Tenable EM | Sensor Tenable và connector bên thứ ba [1] | External ID → MAC → tổ hợp Name/FQDN/IP; UUID khác nhau không bao giờ gộp [1] | Không rõ | ACR 1–10 [47] | AES 0–1000 [47] |
| runZero | Scan, integration [2] | MAC → IP (cửa sổ 3 ngày) → hostname, chỉ trong cùng site [2][48] | Offline nếu vắng ở lần scan gần nhất [48] | Không rõ | Outlier score 0–5 [48] |
| Axonius | Adapter (EDR, AD, CMDB, cloud…) [9] | Tự gộp; có Explain Correlation / Non-Correlation [4] | Không rõ | Tag có ngày hết hạn [9] | Không rõ |
| Exabeam | LDAP, log, CSV zone [49] | Host-to-IP mapping, trễ tới 2 giờ [50] | Theo session | Label executive/privileged, asset group [10][49] | anchor × anomaly factor; notable ≥ 90 [10][51] |
| Wazuh | Agent (Syscollector) [52] | Agent ID, một nguồn | Không rõ | Không có | Không có |

### Ba kiểu hợp nhất thực thể, và kiểu nhóm primary/alias gỡ được là an toàn nhất

Kiểu thứ nhất là **gộp khi trùng bất kỳ khoá nào**. Splunk A&I coi hai dòng là cùng asset khi một trong `ip`, `dns`, `mac`, `nt_host` trùng nhau [21]. Cách này dễ gộp nhầm, nên Splunk phải cho tắt merge toàn cục khi file nguồn có khoá trùng mà không làm sạch được [53]. Kiểu thứ hai là **khoá có thứ tự ưu tiên**. Tenable thử lần lượt External Identifier → MAC → Name+FQDN+IP → … → Name, và đặt hai ràng buộc cứng: "Assets with different Tenable UUIDs will never be merged" và "Assets must belong to the same class to be merged" [1]. runZero khớp MAC → IP trong **cửa sổ 3 ngày** → hostname, và chỉ ghép trong cùng một site [2][48]. Elastic chỉ tạo entity khi đủ dữ liệu để sinh EUID ổn định. User từ các IdP khác nhau có namespace riêng, còn user từ EDR được coi là "medium-confidence local user" gắn với host [26]. Kiểu thứ ba là **nhóm resolution gỡ được**. Elastic (GA 9.4) giữ bản ghi gốc, gom chúng vào một group có primary entity (ưu tiên entity từ IdP) và các alias trỏ về qua `resolved_to`. Tự động resolve chỉ dựa vào email, link thủ công làm qua CSV hoặc flyout, còn bulk unlink chỉ có qua API [3]. Microsoft gộp nhiều account (AD, Entra, SaaS) thành một identity có primary account và cho analyst link thêm bằng tay [43]. Axonius có nút **Unlink Device** trên header profile [9].

IP động được xử lý bằng chỉ mục theo thời gian. Google lấy liên kết hostname–MAC–IP từ DHCP ACK/OFFER/RELEASE, và lấy liên kết product ID–hostname từ EDR [32]. Rapid7 "model the relationship between IP addresses and assets over time" và tự nhận đây là "best-effort algorithm that is not guaranteed to be accurate" [40]. QRadar đi theo hướng phòng thủ: dữ liệu có hành vi đáng ngờ từ hai lần trở lên trong **2 giờ** (ví dụ một MAC gắn với **≥ 3 IP**) bị đưa vào blocklist và không được áp vào asset DB, và có allowlist cho dữ liệu hợp lệ [38]. QRadar cũng cảnh báo hiện tượng "asset growth deviation", khi asset mới sinh nhanh hơn tốc độ dọn hoặc một asset tích tụ quá nhiều identity [39]. Axonius cho thấy "confidence" ngầm định khi giải thích vì sao hai bản ghi *không* được ghép. Mỗi identifier ra một trong các kết quả: Contradiction, Missing Values, hoặc khớp nhưng không đủ (giá trị yếu, placeholder, quá ngắn, bị loại khi chuẩn hoá) [4].

![Tenable Asset Cluster Logic hiển thị tiêu chí và giá trị đã khiến các nguồn được ghép](https://docs.tenable.com/exposure-management/Content/Resources/Images/Local/exposure-management/asset-cluster-logic.png)
*Tenable – Asset Cluster Logic: tiêu chí khớp (hostname, IP, MAC) và giá trị cụ thể đã kích hoạt mỗi lần ghép một tài sản đa nguồn. Nguồn: [47]*

![Axonius Explain Correlation hiển thị chuỗi ghép giữa hai adapter qua bản ghi trung gian](https://files.readme.io/5c066413acf4f063e0f6de1bd5b0bdeb1b864017af5625e8c4c7d45eeb1e0dc0-image.png)
*Axonius – Explain Correlation: chuỗi từng bước nối hai adapter, có thể đi qua bản ghi trung gian, mỗi bước ghi ngày khớp. Nguồn: [4]*

### Provenance theo trường và ưu tiên nguồn quyết định giá trị hiển thị

CAASM là nhóm làm phần này kỹ nhất. Tenable dùng "a fixed priority order to determine which value appears in the unified view": nguồn native đứng trước, rồi đến connector bên thứ ba theo thứ tự kết nối. Thứ tự này xem được qua "Show information order" và chỉnh được ở Settings > Information Order Configuration [1][47]. Axonius chia field thành Aggregated (gộp từ mọi adapter), Preferred (giá trị đại diện, ví dụ preferred OS), Specific (chỉ thuộc một adapter) và Common. Mỗi hàng trong bảng field có cột adapter đã cung cấp, và mở rộng ra được giá trị của từng nguồn kèm raw JSON [9]. Splunk Exposure Analytics giải xung đột kiểu "nguồn có IP mới nhất" và "nguồn có owner tin cậy" bằng source prioritization, có field aging rule để xoá giá trị cũ [25][16]. Cả Splunk lẫn Elastic đều cảnh báo dữ liệu ngữ cảnh cũ. Splunk nói chế độ trộn có thể gộp dữ liệu discovery với A&I cũ hoặc sai [29]. Elastic yêu cầu clear entity store khi đổi chuẩn hoá `host.name`/`user.name` [26]. **Nhận định:** đây là lý do nên tách thuộc tính *quan sát* (dựng lại được từ log) khỏi thuộc tính *do người gán* (criticality, owner, tag, ghi chú), để rebuild không làm mất công sức của analyst.

![Tenable Information order: thứ tự ưu tiên nguồn khi lấy giá trị thuộc tính](https://docs.tenable.com/exposure-management/Content/Resources/Images/Local/exposure-management/property-merge-order.png)
*Tenable – Information order: thứ tự nguồn được dùng để chọn giá trị hiển thị cho từng thuộc tính của tài sản hợp nhất. Nguồn: [47]*

![Axonius tooltip liệt kê các adapter connection đã cung cấp một trường](https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/AdapterConnectionsHover.png)
*Axonius – Provenance theo trường: hover trên một trường để thấy những adapter connection nào đã báo giá trị đó. Nguồn: [9]*

### Vòng đời dùng ngưỡng last seen khác nhau theo loại tài sản

Cortex dùng ngưỡng ngắn: **Active 0–3 ngày → Not Seen 3–5 → Lost 5–7**, sau 7 ngày bị ẩn khỏi bảng [28]. Splunk đẩy vào A&I các entity thấy trong **30 ngày**, ngưỡng chỉnh được, và báo Fail khi nguồn discovery vượt health window **1 ngày** [29][54]. DataBee (kho entity trên OCSF) cho virtual asset age-out sau **7 ngày**, còn user, thiết bị vật lý, application và cloud resource sau **1 năm** [20]. runZero đánh dấu offline khi tài sản vắng mặt ở lần scan gần nhất [48]. Microsoft lưu ý "the device profile doesn't consider all cyber evidence when determining the 'Last Seen' timeframe" [44]. **Nhận định:** ngưỡng phải tuỳ theo lớp tài sản (container/VM tự scale khác laptop, khác DC), và "last seen" phải tính theo từng nguồn chứ không chỉ một giá trị tổng.

## Criticality hội tụ về 3–4 mức, gán bằng rule, ghi đè có lý do và hàng chờ duyệt

Thang mức khá giống nhau giữa các vendor: Microsoft Very High/High/Medium/Low [5], Elastic low/medium/high/extreme_impact [23], CrowdStrike Critical/High/Noncritical/Unassigned [6], Trend High/Medium/Low [7], Tenable ACR 1–10 [47]. Microsoft có cơ chế gán hoàn chỉnh nhất. Gồm ba lớp: classifier định sẵn (domain controller, file server, database có dữ liệu nhạy cảm, Privileged Role Administrator, tài nguyên Azure/AWS/GCP), custom query bằng query builder Boolean có preview tài sản bị ảnh hưởng, và gán thủ công. Khi nhiều rule cùng khớp, "the rule with the highest criticality level takes precedence". Asset hết khớp rule thì tự về mức của rule kế tiếp. Tài sản khớp classifier nhưng chưa đạt ngưỡng tự phân loại vào hàng chờ **Pending Approval** [5][55]. Microsoft khuyến nghị dùng rule rộng thay vì gán tay từng máy, và cảnh báo attack path "might not be fully representative" nếu critical asset chưa được định nghĩa đủ [5][56]. CrowdStrike có ô "Reason for assignment" (tuỳ chọn, tối đa 300 ký tự) và có link "Create rule using these asset filters" để biến một bộ lọc thành rule [6]. Trend ghi rõ nguồn của mức criticality (system hay Custom), cho phép sửa hàng loạt và quay về mức hệ thống bất kỳ lúc nào [7]. Cortex Asset Roles tự phân loại theo hành vi (Domain Controller, Administrator, Executive User, Honey user), cho ghi đè và import CSV. Role được dùng làm baseline cho analytics, để so sánh peer, và làm tag family để lọc alert [45].

Ba trục được giữ tách nhau. Microsoft: "Exposure level relates to how much the device is complying with security recommendations, while risk level is calculated based on ... active alerts" [8]. Identity risk của Microsoft tách *likelihood* (alert theo chặng kill chain) khỏi *impact* (criticality, Global Admin, vai trò PIM), có decay, và có action "Confirm safe" [43]. Trend nói "Two assets with the same risk events and different criticality levels are not assigned the same risk scores" [7].

![Microsoft Exposure Management: tạo custom critical asset classification bằng query builder](https://learn.microsoft.com/en-us/security-exposure-management/media/classify-critical-assets/create-critical-asset-classification.png)
*Microsoft Security Exposure Management – Tạo critical asset classification: query builder với điều kiện Boolean theo device/identity/cloud resource để định nghĩa rule criticality. Nguồn: [5]*

![Microsoft Exposure Management: trang Critical asset management với các classification](https://learn.microsoft.com/en-us/security-exposure-management/media/classify-critical-assets/critical-asset-management-window.png)
*Microsoft Security Exposure Management – Critical asset management: danh sách classification định sẵn và custom, số asset khớp, bật/tắt và mức criticality từng rule. Nguồn: [5]*

![CrowdStrike Falcon: hộp thoại Assign asset criticality](https://www.crowdstrike.com/wp-content/uploads/2024/05/femiatua8.png)
*CrowdStrike Falcon – Assign asset criticality: chọn Critical/High/Noncritical/Unassigned, ô "Reason for assignment (optional)" (0/300) và link "Create rule using these asset filters". Nguồn: [6]*

## Giao diện profile: header bền vững cộng tab điều tra theo thời gian

### Asset/device profile: khung header → tab → sidebar + thẻ KPI

Microsoft đã chuẩn hoá một khung dùng chung cho device, identity và IP. **Header** gồm tên, các chỉ báo risk severity, criticality, device value, tag (từ MDE, MDI hoặc người dùng) và response actions. **Dãy tab** gồm Overview, Incidents and alerts, Timeline, Security recommendations, Inventories, Discovered vulnerabilities, Missing KBs, Sentinel events… **Overview** có sidebar thu gọn được (VM details, Cloud resource details, Hardware, Directory data) và lưới thẻ: Active alerts trong **180 ngày** cùng Risk level, Exposure level, Logged on users trong **30 ngày**, Device health [8]. Timeline mặc định 30 ngày, export tối đa 7 ngày ra CSV, có nút "Hunt for related events". Từ 01/2025 timeline gộp cả activity của Sentinel [8]. Action có cả Set criticality, Manage tags và **Report device inaccuracy**, tức analyst phản hồi được khi phân loại sai [8][44]. Sentinel trên Azure portal dùng bố cục 3 cột (info, timeline, insights) và có Watchlist insights [57]. Sentinel trên Azure portal ngừng hỗ trợ sau 31/03/2027 [57].

Bảng dưới so các khối thông tin trên asset profile. ✓ là có trong docs, "—" là không thấy trong nguồn đã đọc (không có nghĩa là sản phẩm không có).

| Vendor | Header: risk/criticality/tag | Thuộc tính + first/last seen | Provenance nguồn | Alert/case liên quan | Timeline | Phần mềm/lỗ hổng | User liên quan | Quan hệ/graph | Notes/audit | Hành động |
|---|---|---|---|---|---|---|---|---|---|---|
| Defender XDR [8] | ✓ | ✓ | onboarding/discovery | ✓ 180 ngày | ✓ | ✓ | ✓ logged-on | attack path | — | ✓ isolate, live response… |
| Elastic [58] | ✓ (9.4+) | ✓ observed attributes | resolution | top 10 alert | qua Timeline | vuln (host) | — | graph 30 ngày | — | Add to case |
| Sumo Logic [22] | ✓ | metadata, inventory | — | signal/insight | ✓ 3 ngày | — | related entities | — | ✓ notes + audit log | suppress, create insight |
| Google SecOps [59] | — | IP/MAC theo thời gian, first seen | — | ✓ | ✓ prevalence | — | — | domain prevalence | — | lọc procedural |
| Splunk ES [60] | asset description | ✓ | — | notable | swim lane heat map | — | — | graph (8.5) | — | Create notable |
| Axonius [9] | tag | ✓ | ✓ theo trường | — | snapshot theo ngày | CIS | — | Asset Graph | ✓ notes | ticket, enforce, unlink |
| Tenable [47] | ACR/AES | ✓ | ✓ cluster logic | findings | exposure signals 7 ngày | ✓ | accounts/users | relationships, attack path | — | export, AI summary |
| Cortex XSIAM [61] | score + delta | ✓ panel | — | cases | risk trend | CVE | — | — | — | actions, star |
| Trend Vision One [46] | ✓ hover card | ✓ | — | risk event | — | local apps | ✓ kèm risk | asset risk graph | — | exception, response |
| Exabeam [50] | điểm session | ✓ top user | — | badge alert | ✓ smart timeline | — | ✓ | — | — | create incident |
| Rapid7 [62] | — | local accounts | — | related alerts | — | vuln (InsightVM) | primary asset | lateral movement | — | download PDF |

![Microsoft Defender XDR device page, tab Overview](https://learn.microsoft.com/en-us/defender-xdr/media/entity-page-device/entity-device-overview-tab.png)
*Microsoft Defender XDR – Device entity page, tab Overview: header có risk "High", "Criticality: None", tag, nút Device value/Set criticality; sidebar VM details (domain, OS, health, IP, first/last seen); thẻ Active alerts/Risk level, Exposure level, Logged on users. Nguồn: [8]*

![Microsoft Sentinel entity page bố cục 3 cột](https://learn.microsoft.com/en-us/azure/sentinel/media/entity-pages/entity-page-sentinel.png)
*Microsoft Sentinel – Entity page (Azure portal): thông tin định danh bên trái, timeline alert/bookmark/anomaly/activity ở giữa, insights bên phải. Nguồn: [57]*

Elastic gom profile vào một **flyout** trượt từ phải, có thể mở từ bảng alert, trang Entity analytics hoặc trang Users/Hosts. Các section xếp dọc, thu gọn được: header (gán criticality ngay tại chỗ, từ 9.4), Entity summary do AI viết (9.3), Risk score kèm history từng lần tính (bấm một điểm để xem Contexts/Alerts của lần tính đó, 9.5), Behavioral anomalies ánh xạ MITRE, graph 30 ngày, Resolution, Insights (vuln, misconfig), Observed attributes. Từ 9.5 có thêm nút Take action → Add to case [58]. Docs Elastic không có ảnh flyout 9.4+. Ảnh dưới là trang Host details kiểu cũ [63].

![Elastic Security trang Host details](https://www.elastic.co/docs/solutions/images/security-hosts-detail-pg.png)
*Elastic Security – Host details (UI cổ điển): summary gồm host ID, first/last seen, IP, OS, host risk score; alert metrics theo severity/rule/status; các data table lọc theo host. Nguồn: [63]*

Sumo Logic là vendor duy nhất trong nhóm SIEM đặt **Notes** và **Audit Log** ngay trên entity, kèm slider suppression, tags, criticality, indicators, metadata, network blocks, inventory. Khu chính có tab Activity, Enrichments, Timeline 3 ngày, Related Entities, Automations, cùng danh sách signal có checkbox để Create Insight thủ công [22].

![Sumo Logic Cloud SIEM Entity Details của một host](https://www.sumologic.com/help/img/cse/entity-details-new-host.png)
*Sumo Logic Cloud SIEM – Entity Details (host): cột trái là suppression, tags, criticality, indicators, metadata, inventory, notes, audit log; khu chính là timeline, related entities và danh sách signal để tạo insight. Nguồn: [22]*

Google SecOps Asset view là trang điều tra theo thời gian. Bạn tìm theo hostname, IP hoặc MAC cùng một timestamp, cửa sổ mặc định 2 giờ. Trung tâm trang là prevalence graph: domain hiếm nổi lên trên, vòng xám là kết nối lần đầu, tam giác đỏ là alert. Bên cạnh là các khối insight: Forwarded alerts, Newly registered domains (≤ 30 ngày), Domains new to the enterprise, Low prevalence domains (≤ 10). Prevalence tính trên 7 ngày [59].

![Google SecOps Asset view: các khối Asset insight](https://docs.cloud.google.com/static/chronicle/images/asset-insight-blocks.png)
*Google SecOps – Asset view, Asset insight blocks: các khối forwarded alerts, newly registered domains, domains new to enterprise, low prevalence đặt cạnh timeline của asset. Nguồn: [59]*

Splunk ES Asset Investigator xếp chồng các swim lane, mỗi lane là một heat map mật độ sự kiện gắn với một data model (authentication, malware, notable…). Phía trên là asset description để xác nhận đúng máy, phía dưới là Event Panel với Go to Search và Create Notable Event [60]. ES 8.5 thêm Entity analysis dashboard với các tab health, activity, risk, network associations cùng graph explorer [64]. Không tìm được ảnh UI 8.x công khai. Ảnh duy nhất là ngữ cảnh A&I trong blog năm 2020.

![Splunk ES ngữ cảnh asset từ framework Asset & Identity (ảnh 2020)](https://www.splunk.com/content/dam/splunk-blogs/images/media_1740d4f15dc5d96133b8142263a74f0bca47d8bb1.webp)
*Splunk ES – Ngữ cảnh asset A&I (ảnh cũ, trước ES 8.x): asset titan.thirstyberner.com kèm city San Francisco, category Active Directory/Windows, bunit IT, IP 10.1.1.10. Nguồn: [21]*

Axonius và Tenable (CAASM) đặt **bảng thuộc tính hợp nhất có provenance** vào trung tâm. Axonius có header gồm tên và 2 trường phụ, thanh action Tag/Add Custom Field/Create Ticket/Enforce/Unlink. Pane trái là "mục lục nguồn" (Adapter Connections, Tags có ngày hết hạn, Custom Data). Vùng chính là bảng field–value–sources. Các tab khác gồm CIS, Enforcement Runs, Tickets, Notes, Asset Investigation (thay đổi theo thời gian), Asset Graph [9]. Tenable có header gồm tên, asset class, số đếm theo exposure category và nút Summarize bằng AI, sau đó là Key Properties (Owner, Location, Last Observed, ACR, AES) và một dãy tab dài: Connectors Details kèm raw data, Weaknesses, Findings, Software, Relationships, Attack Paths, Exposure Signals [47].

![Axonius Asset Profile drawer mở từ bảng Assets](https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/img/asset_profile/AssetProfileDraweronAssetsPage.png)
*Axonius – Asset Profile drawer: mở từ bảng Assets, gồm header và thanh hành động, pane trái liệt kê nguồn và tag, bảng trường hợp nhất ở giữa. Nguồn: [9]*

![Tenable Exposure Management trang Asset Details](https://docs.tenable.com/exposure-management/Content/Resources/Images/Local/exposure-management/asset-details.png)
*Tenable Exposure Management – Asset Details: header với asset class và số đếm theo exposure category, Key Properties và dãy tab dữ liệu. Nguồn: [47]*

Exabeam (UEBA) bố trí profile theo chiều dọc và xoay quanh rủi ro theo thời gian. Asset Directory Information (IP, labels, first/last seen, **Top User**, badge số alert bên thứ ba) → Asset Risk Trend → Risk Reasons (hiện icon các user rủi ro cao đã tương tác) → Asset Timeline. Exabeam lưu ý timeline chỉ cập nhật sau khi đã xử lý host-to-IP mapping, nên có thể trễ tới **2 giờ** [50].

![Exabeam Asset Directory Information](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-75d91051-bd0e-eada-5417-7f45601f4e11.jpg)
*Exabeam – Asset page, Asset Directory Information: IP, labels, first/last seen, top user, badge alert bên thứ ba và điểm sequence gần nhất. Nguồn: [50]*

Wazuh là inventory một nguồn. Module Syscollector của agent thu phần cứng, OS, package, process, service, port, user, group và browser extension, đưa vào trang IT Hygiene. Không có hợp nhất đa nguồn hay provenance [52].

![Wazuh IT Hygiene dashboard inventory endpoint](https://documentation.wazuh.com/current/_images/inventory-data-dashboard1.png)
*Wazuh – IT Hygiene / Inventory data: dashboard inventory của endpoint lấy từ Syscollector (phần cứng, OS, package, port, process). Nguồn: [52]*

Các vendor không có ảnh công khai được mô tả bằng lời dưới đây. **Cortex XSIAM Host Risk View** (cần ITDR add-on): header gồm định danh, risk score và mức thay đổi trong kỳ. Tiếp theo là hàng widget highlight bấm được (Case Breakdown theo severity, CVEs Breakdown, MITRE ATT&CK Overview). Tab Risk Assessment có đường Risk Score Trend với bong bóng số issue theo ngày và chế độ "Compare To" theo asset role, trong đó đường đứt nét là trung bình của peer. Bảng Cases có cột Status giải thích vì sao điểm đổi. Tab Activities gồm Failed Logins và Login Attempts. Star để đưa host vào watchlist [61]. **Trend Vision One device profile**: hover card trên tên hiện score, criticality và significant profile tags. Các tab gồm Risk Assessment (score 30 ngày, risk indicators kèm rule giảm thiểu), Asset Risk Graph (bấm mũi tên xem first/last time kết nối), Local Apps, Users (kèm risk score từng người), Asset Profile (Manage Tags, Modify Criticality) [46]. **Rapid7 InsightIDR Asset Details**: Local Accounts từ Insight Agent, lateral movement graph, bản đồ Ingress Locations [62]. **IBM QRadar**: tab Assets hiển thị lỗ hổng, port, ứng dụng và lịch sử, còn Asset Profile có Vulnerabilities pane. Docs IBM chặn truy cập trực tiếp nên không có mô tả bố cục [37].

**Nhận định:** hai kiểu UI bổ sung cho nhau. "Hồ sơ bền vững" (Microsoft, Elastic, Sumo, Axonius, Tenable) trả lời câu hỏi *tài sản này là gì, ai biết về nó, quan trọng đến đâu, thiếu gì*. "Trang điều tra theo thời gian" (Google, Splunk, Exabeam) trả lời *nó đang làm gì bất thường*. Asset profile cho SOC cần header bền vững cộng tab timeline/prevalence. Các chi tiết đáng chép: mọi thẻ có "View all…" và có link mở query gốc; điểm số phải có lý do (cột Status của Cortex, "factors influencing priority" của Microsoft); có nút báo sai.

### Danh sách inventory và thao tác hàng loạt

Defender device inventory có các tab theo loại (Computers & mobile, Network devices, IoT/OT, Uncategorized) và các "count pills": total, critical assets, high risk, high exposure, not onboarded, newly discovered. Bộ lọc dùng cho vận hành gồm Onboarding status = "Can be onboarded", Managed by = Unknown, Sensor health = Inactive/Misconfigured [42]. Sumo Entities có bộ lọc theo activity score, criticality, sensor zone, suppressed, tags. Nút Import Metadata (CSV) và checkbox cho phép Change Tags/Suppression/Criticality hàng loạt. Criticality còn quản lý được bằng Terraform [22][41]. Axonius thêm cột Adapter Connections dạng icon nguồn, nhìn vào là biết thiết bị đang thiếu nguồn nào [65].

![Sumo Logic Cloud SIEM trang Entities](https://www.sumologic.com/help/img/cse/entities-page-2.png)
*Sumo Logic Cloud SIEM – Entities list: bộ lọc, nút Import Metadata, checkbox sửa hàng loạt, các cột activity score, signal severity total, suppressed lists và criticality. Nguồn: [22]*

### User/identity profile: danh tính hợp nhất, heat map hoạt động và điểm có giải thích

User profile có cùng khung với device page, cộng ba phần riêng. Phần thứ nhất là **danh tính hợp nhất**. Tab "Observed in organization" của Defender liệt kê Accounts (đánh dấu primary, cho link tay), Devices, Locations, Groups. Timeline gộp 8 bảng (AlertInfo, IdentityLogonEvents, EntraIdSignInEvents…) và khử trùng: khi một sign-in có ở cả Entra lẫn cloud app thì ưu tiên bản ghi Entra [43]. Google gộp `dennis` và `dennis@altostrat.com` thành một user [33]. Phần thứ hai là **nhịp hoạt động**. Google User view có gradient heat map 7 ngày × 24 giờ UTC để phát hiện hoạt động lúc 3 giờ sáng, nút nhảy tới First/Last Seen, và tab Assets liệt kê thiết bị của user trong khoảng thời gian [33]. Exabeam có Data Insights (top 5 workstation, zone, quốc gia, giờ hoạt động) và Smart Timeline theo session [10]. Phần thứ ba là **rủi ro có giải thích**. Exabeam ghi cho mỗi risk reason: model confidence, tag MITRE và công thức "the anchor score multiplied by the anomaly factor" [10]. Defender tách likelihood khỏi impact và hiển thị percentile so với toàn tổ chức [43]. Header của Defender có các action lên tài khoản: disable, revoke sessions, force password change, mark as compromised. Panel Protection gồm MFA status và last password change [43].

![Google SecOps User view đánh số 1–7](https://docs.cloud.google.com/chronicle/images/user-view-numbered.png)
*Google SecOps – User view: (1) user info từ AD/Workday/Okta, (2) chọn tuần và nhảy First/Last Seen, (3) time shift, (4) heat map theo giờ, (5) user alerts, (6) tab Timeline/Assets, (7) tuỳ chỉnh cột. Nguồn: [33]*

![Microsoft Defender XDR Identity page tab Overview](https://learn.microsoft.com/en-us/defender-xdr/media/investigate-users/identity-page.png)
*Microsoft Defender XDR – Identity page, tab Overview: header có UPN, trạng thái, action "Mark as compromised"; panel Entity details chia Protection (MFA, last password change) và User threat (insider risk, blast radius, UEBA anomalies, risk score); thẻ incidents và thiết bị logon tương tác. Nguồn: [43]*

![Microsoft Defender XDR Identity page tab Observed in organization](https://learn.microsoft.com/en-us/defender-xdr/media/investigate-users/identity-observed-in-organization.png)
*Microsoft Defender XDR – Identity page, Observed in organization: các account đã hợp nhất (đánh dấu primary), devices, locations và groups của một identity. Nguồn: [43]*

![Exabeam User General Information](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-cb33dad9-918f-2707-97ac-cedb4c8433a2.png)
*Exabeam – User profile, General Information: title, department, manager, top peer group, labels (executive, privileged), first/last seen và risk score session gần nhất. Nguồn: [10]*

![Exabeam Risk Reasons](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-7bd36e84-66b7-6a0c-8c35-10f1f457dc6f.png)
*Exabeam – Risk Reasons: danh sách sự kiện góp điểm vào session, kèm model confidence và tag MITRE ATT&CK. Nguồn: [10]*

Cortex XSIAM User Risk View có panel phải hiện title, department, primary location, endpoint, last activity và tags. Ngoài ra có working hours và heatmap Issues & Insights [66]. Rapid7 User Details hiện số lỗ hổng đang mở trên từng asset của user, tag Primary Asset, Search Related Logs (mặc định 1 giờ qua), Related Alerts có toggle Include Actor, và nút Download PDF [62]. Rapid7 xác định primary user bằng số lần đăng nhập trong tuần [40], còn OCSF định nghĩa `endpoint.owner` là người "owns the endpoint **or was last logged into it**" [67]. **Nhận định:** "owner" (ai chịu trách nhiệm, lấy từ CMDB/HR) và "top/last user" (ai đang dùng, suy ra từ authentication) phải là hai trường khác nhau trên profile.

## Ngữ cảnh tài sản giảm nhiễu bằng ma trận, hệ số và đổi baseline; số liệu hiệu quả chỉ là tuyên bố vendor

Có ba cơ chế có tài liệu rõ. Cơ chế thứ nhất là **ma trận**. Urgency của notable trong Splunk ES là tổ hợp severity × priority của asset/identity, lấy giá trị priority cao hơn nếu cả hai cùng có. Asset priority unknown/low thì severity high chỉ ra urgency medium. Asset critical thì severity high đã ra urgency critical. Bảng ma trận là một lookup sửa được [30]. Cơ chế thứ hai là **hệ số**. Risk factor của Splunk chạy các phép cộng trước rồi mới đến phép nhân, có factor dựng sẵn "if the dest_priority field value is 'critical', the risk factor is multiplied by **1.5**", nhưng mọi factor có sẵn đều "turned off" cho tới khi bật [124]. Docs còn nêu ví dụ tự cấu hình: user trong watchlist cộng asset critical thì nhân **1,2** [11]. Elastic nhân trọng số **Low 0,5 / Medium 1 / High 1,5 / Extreme 2** ("subject to change") và tách phần đóng góp thành category "Asset Criticality". Ví dụ trong docs: Alerts 36,16 cộng Asset Criticality 16,95 ra **53,11 (Moderate)** [12]. Sumo dùng biểu thức như `severity+2` [41]. Graylog tính event risk từ severity, priority của rule và priority của asset, và **không có asset liên kết thì không tính event risk score** [68]. Cơ chế thứ ba là **đưa ngữ cảnh vào lúc phát hiện, hoặc đổi baseline**. Google context-aware analytics đưa context vào "at detection execution time" để lọc "entire clusters of threats that may be expected", ví dụ sandbox/dev network không có dữ liệu nhạy cảm. Context có validity interval, và event chỉ join được khi timestamp nằm trong khoảng hiệu lực [35]. Exabeam mô hình asset group (vd cụm Exchange cân bằng tải) như một thực thể để "reduces the amount of false positives", phân loại server/workstation theo OS hoặc OU [49], và chấm cao hơn khi non-executive truy cập workstation của executive hoặc khi service account đăng nhập interactive [69]. Peer group của Exabeam khởi đầu từ thuộc tính AD, nhưng blog năm 2016 cho biết mỗi thuộc tính chỉ phủ **50–90%** user, nên họ dùng peer động có degree of membership [70]. Cortex SmartScore: "a critical alert on an asset with a low risk score might be given a lower overall SmartScore, while minor alerts on highly critical assets might be elevated" [13]. Microsoft đưa asset criticality vào priority score 0–100 của incident (đỏ > 85, cam 15–85, xám < 15) cùng với các yếu tố khác, hiển thị "factors influencing the priority score", nhưng không công bố trọng số [71][72].

Không vendor nào công bố trọng số criticality trong công thức ML, và cũng không có nghiên cứu độc lập nào đo hiệu quả. Các con số của Splunk là **tuyên bố vendor** và lệch nhau giữa các tài liệu: blog ES 6.4 nói giảm **60–80%** khối lượng alert (trang này nay trả 404, con số chỉ còn đối chiếu được qua trích đoạn search) [73]. "The Splunk Guide to RBA" ghi **30–80%**, với chú thích con số lấy từ một testimonial [14]. Case study Johnson Matthey ghi fidelity +30% và thời gian xử lý case −83% [74]. Một blog nói true positive rate của một khách hàng tăng từ dưới 10% lên trên 30% [75]. Chính Splunk cũng thừa nhận RBA chưa được curate "can generate as many notables as traditional alerting", và khuyên dedup, rút cửa sổ từ 24h xuống 12h, tinh chỉnh các hoạt động dự đoán được [76].

![Elastic Security: bảng alert nhóm theo asset criticality](https://www.elastic.co/docs/solutions/images/security-group-by-asset-criticality.png)
*Elastic Security – Alerts group by asset criticality: bảng alert được nhóm theo mức criticality của host/user để triage theo giá trị tài sản. Nguồn: [77]*

![Microsoft Defender XDR incident queue với priority score](https://learn.microsoft.com/en-us/defender-xdr/media/incidents-queue/incidents-page.png)
*Microsoft Defender XDR – Incident queue: hàng đợi incident có cột priority score 0–100, trong đó asset criticality là một yếu tố đầu vào. Nguồn: [71]*

Suppression có một bài học ngược. "Accept Session" của Exabeam whitelist vĩnh viễn hành vi cho user/asset, không hoàn tác được, và chính Exabeam khuyên tune rule thay vì accept [10]. Tag của Axonius thì có ngày hết hạn [9]. **Nhận định:** cơ chế (b) chỉ xếp hạng lại, còn cơ chế (c) giảm nhiễu từ gốc. Sản phẩm nên có cả hai, và suppression theo lớp tài sản (scanner, jump host, build server) phải dựa trên role/tag của profile, có lý do, người duyệt, hạn và audit, không phải exception cứng theo IP.

## Vận hành, phòng thủ và đa tenant: phân biệt "không có alert" với "không có dữ liệu", và khoá phải chứa tenant

### Coverage, health và gap query

Có ba cách giám sát "asset im lặng". Cách thứ nhất là rule hoặc metric absence. Google SecOps silent-host monitoring gắn ingestion label theo `host.name` rồi đặt alert Cloud Monitoring khi log count xuống dưới ngưỡng. Phương án dashboard trễ tới **6 giờ** và không alert được [78]. Theo trích đoạn, rule YARA-L mẫu báo khi host vắng event trong 10 phút gần nhất nhưng vẫn có event trong 20 phút [79]. Cách thứ hai là bảng health của connector: workbook "Data collection health monitoring" của Sentinel có tab Overview (volume, EPS, last log), Anomalies (`series_decompose_anomalies()`) và Agent info, nhưng bảng `SentinelHealth` chỉ hỗ trợ một số connector [80]. Cách thứ ba là cột sensor health trong inventory: Defender lọc theo Sensor health, Managed by, Antivirus status [42][81]. CAASM biến coverage thành **gap query** trên bản ghi đã hợp nhất. Axonius có `OS = Windows AND CrowdStrike Agent ID does not exist`, biến thể "agent có nhưng CrowdStrike last seen > 30 ngày trong khi AD thấy trong 7 ngày", rồi chuyển kết quả sang Enforcement Center (deploy agent, báo owner, mở ticket) với lịch chạy liên tục [65]. CIS cung cấp KPI dùng được ngay: Safeguard 8.2 có Coverage = M2/M1 (asset được cấu hình log đúng / asset có khả năng log) [82]. Safeguard 1.1 có Accuracy = M3/M2, M4 = có trong inventory mà discovery không thấy (stale), M5 = discovery thấy mà không có trong inventory (unknown), và review "bi-annually, or more frequently" [83].

![Axonius gap query: thiết bị CrowdStrike lâu không check-in](https://images.contentstack.io/v3/assets/blt309b1de7d109902d/blt3f5b277a70d3e42e/6839c6eb116bcf82b521d22f/AX_DetectGaps_EP_Blog_Product01_1600x900_%281%29.png)
*Axonius – Gap query: truy vấn thiết bị có agent CrowdStrike nhưng lâu không check-in trong khi nguồn khác vẫn thấy thiết bị. Nguồn: [65]*

![Microsoft Sentinel Data collection health workbook, tab Overview](https://learn.microsoft.com/en-us/azure/sentinel/media/monitor-data-connector-health/data-health-workbook-1.png)
*Microsoft Sentinel – Data collection health workbook, Overview: volume, EPS và thời điểm nhận log cuối theo từng nguồn. Nguồn: [80]*

### Exposure và attack path lấy critical asset làm đích

Microsoft định nghĩa attack path là "end-to-end paths that attackers can create to get from an entry point ... to critical assets". Họ có choke point, blast radius và cách nhóm path theo target criticality [56]. Trang Security recommendations đếm số "exposed critical assets" cho mỗi khuyến nghị [5]. CrowdStrike dùng ma trận Asset criticality × Exploit status để ưu tiên lỗ hổng, cộng các widget Managed/Unmanaged/Unsupported và Internet-exposed. Workflow Falcon Fusion tự gợi ý cài sensor và mở ticket ServiceNow cho tài sản unmanaged có confidence High [6].

![CrowdStrike Falcon Exposure Management dashboard](https://www.crowdstrike.com/wp-content/uploads/2024/05/femiatua7.png)
*CrowdStrike Falcon – Exposure Management overview: bộ lọc criticality/host group/tag; Assets overview Managed 1K / Unmanaged 5.9K / Unsupported 305; internet-exposed assets; ma trận criticality × exploit status; Venn network exploitability. Nguồn: [6]*

### Đa tenant: hai mô hình, và chỉ ba vendor mô tả rõ cách xử lý IP trùng

Mô hình thứ nhất là instance riêng cho mỗi khách cộng một lớp tổng hợp. Defender XDR multitenant management có trang Tenants (mỗi tenant: số device, số high value, high exposure, can-onboard, cùng tổng toàn bộ ở đầu trang) và một device inventory gộp có cột **Tenant name**. Thao tác sửa tag, exclusion làm ngay trên danh sách. Muốn thao tác đầy đủ thì bấm vào tên tenant để sang portal của tenant đó [81]. Cortex XSIAM có parent/child, mỗi child là một instance lưu dữ liệu riêng [84]. Mô hình thứ hai là một instance chung, tách bằng nhãn. Google Data RBAC dùng scope gồm allow/deny label (namespace, ingestion label, log type), và deny thắng [85]. Bật Data RBAC thì Risk Analytics chỉ còn cho user có global scope [34], và rule cũ nhận global scope [86]. Practitioner gọi multi-tenancy ở Google là "một bộ quy ước", không phải tính năng [87]. Về IP trùng: QRadar nói thẳng "Log sources that have the same IP address cause problems with correlation, reporting, searching, and asset profiling", nên gán log source vào domain và mỗi asset mang domain ID [15][88]. Thực thể được định danh bằng cặp (IP, domain) [89]. Splunk ghép `cim_entity_zone` với `ip` làm khoá duy nhất cho IP inventory, cho phép khai cùng một subnet ở nhiều zone. Với asset/user inventory thì không tách theo zone mà chỉ giữ zone thấy gần nhất [16]. Khi bật zone ở A&I cổ điển, `ip` và `nt_host` không bị merge xuyên zone [90]. runZero chỉ correlate trong cùng site [48]. Elastic đặt mọi index entity, risk và criticality theo `<space-id>` [26][12]. Wazuh tách saved object theo tenant của dashboard [91]. Không vendor nào có tài liệu về cấu hình criticality hoặc tag riêng mỗi tenant kế thừa từ template của MSSP. Splunk A&I cũng không có trường tenant chính thức [92].

![Microsoft Defender XDR multitenant: danh sách tenant](https://learn.microsoft.com/en-us/defender-xdr/media/mto-tenant-devices/devices-tenant-view.png)
*Microsoft Defender XDR – Multitenant management, Tenants list: mỗi tenant có số device và loại, high value, high exposure, can-onboard; tổng toàn bộ tenant ở đầu trang. Nguồn: [81]*

![Microsoft Defender XDR multitenant: device inventory gộp](https://learn.microsoft.com/en-us/defender-xdr/media/mto-tenant-devices/devices-device-inventory.png)
*Microsoft Defender XDR – Multitenant device inventory: inventory gộp mọi tenant có cột Tenant name, lọc theo risk, criticality, sensor health. Nguồn: [81]*

## OCSF 1.9.0 đủ dữ liệu quan sát nhưng không có thực thể asset bền vững

Tag `1.9.0` (commit `856d462`, 2026-08-03; từ 1.3.0 tag không còn tiền tố `v`) cung cấp ba nhóm vật liệu [93]. Nhóm thứ nhất là **dữ liệu khai báo** trong category Discovery, có `activity_id` 1 = Log (thụ động) và 2 = Collect (chủ động) [94]. Gồm Device Inventory Info **5001** ("collecting device information from a CMDB or running a network sweep") [95], User Inventory Info **5003** [96], Software Inventory Info **5020** (`sbom`, `package`) [97], Cloud Resources Inventory Info **5023** (thêm ở 1.4.0, nhắc rõ nguồn CMDB, CAASM, API cloud/SaaS) [98], Device Config State Change **5019** (`security_states`, hợp để phát hiện EDR bị tắt) [99], và OS Patch State **5004** [100]. Nhóm thứ hai là **dữ liệu quan sát** từ các class Activity: Authentication **3002** (`user`, `dst_endpoint`, `logon_type_id`, `is_remote`, `is_mfa`) cho quan hệ user–host [101]; Network Activity **4001**, ở 1.9.0 có thêm `initiator_id` để biết phía nào khởi tạo [102]; profile `host` gắn `device`/`actor` vào event [103]. Nhóm thứ ba là **finding**: Vulnerability Finding 2002, Compliance Finding 2003, Detection Finding 2004 với `resources[]` [104]. Ở 1.9.0 còn có thêm User Management 3007, thay `account_change` và `user_access` [105].

Về field định danh, `endpoint` yêu cầu `at_least_one` của `ip`, `uid`, `name`, `hostname`, `instance_uid`, `interface_uid`, `interface_name` [67]. `device` bổ sung `uid` (vd EC2 ARN, SID), `uid_alt` (AD DN), `os_machine_uuid`, `boot_uid` (đổi sau mỗi lần reboot), `imei`/`udid`, `first_seen_time`/`last_seen_time`, `type_id` (req), `groups`, `org`, `network_interfaces[]`, `is_managed`/`is_compliant`, và `risk_level_id`/`risk_score` (dictionary mô tả `risk_score` là "as reported by the event source") [18]. `device_hw_info` có `serial_number` và `uuid` SMBIOS [106]. `agent` có `uid` (sensor ID/aid), và `type_id` 1 EDR … 6 Log Forwarding … 7 MDM [107]. `network_interface.namespace` được mô tả là hữu ích khi "similar entities exist that you need to keep separate" [108]. `user` có `uid` (SID/DN/ARN), `uid_alt`, `email_addr`, `domain`, `type_id` (User/Admin/System/Service), `has_mfa`, `risk_level_id` [109]. `ldap_person` có `employee_uid`, `department`, `job_title`, `manager`, `cost_center`, `hire_time`, `leave_time` [110].

Khoảng trống quan trọng nhất là OCSF không có chỗ cho "giá trị nghiệp vụ" của `device`. `device` và `endpoint` **không có** `criticality`, `tags` hay `labels` [18]. `criticality_id` (0 Unknown, 1 Low, 2 Medium, 3 High, **4 Very High**, 99 Other) mới được thêm ở 1.9.0 và chỉ nằm trên `resource_details`; ngoài ra chỉ `application` và `databucket` có `criticality` dạng chuỗi tự do. `resource_details` cũng có sẵn `tags`, `labels`, `owner`, `namespace`, và từ 1.9.0 có thêm hai field `device`/`user` lồng bên trong [19][111]. PR #1693 (Splunk, merge 2026-07-28) thêm chúng với lý do "the criticality of any of the resources populated (in particular `device`)" [112]. `metadata.tenant_uid` chỉ là *recommended*. Field này ra đời từ issue #833 năm 2023, với ví dụ "an MSSP collecting EDR data from a product, for a particular customer" [17][113]. Đừng nhầm nó với tenant phía IdP/SaaS nguồn (`idp.tenant_uid`). OCSF có ba điểm gắn ngữ cảnh hợp chuẩn: `enrichments[]` (name, value, type, provider, `data` json) [114], `observables[]` [115], và `metadata.extensions` [17]. Các bên dùng OCSF đều tự xây kho entity. DataBee "generates a unique ID for each device and user" và gán ID đó vào event, có ưu tiên nguồn ("reduce metadata thrashing"), tuỳ chọn "Allow Merge on IP", owner gợi ý từ authentication 7 ngày, và "OCSF Activity Inclusion List" để chọn class nào đi vào entity resolution [20]. AWS Security Hub giữ resource inventory riêng và chỉ dùng OCSF cho finding [116]. Bảng nguồn native của Security Lake vẫn ghi `metadata.version` 1.1.0 [117]. Tenzir tra lookup inventory rồi ghi vào `enrichments[]` hoặc thẳng vào `src_endpoint` [118]. Trước 1.4.0, tài sản cloud chỉ map "crudely" được vào các class Discovery [119].

## Khuyến nghị thiết kế quản lý tài sản và asset profile đa tenant trên OCSF 1.9.0

**Nhận định:** toàn bộ mục này là đề xuất thiết kế suy ra từ các bằng chứng ở trên, không phải thực tiễn đã được kiểm chứng ở một sản phẩm cụ thể. Vendor tham khảo được ghi cho từng điểm để truy lại.

### Mô hình thực thể và khoá hợp nhất theo tenant

**Nhận định:** dùng bốn lớp dữ liệu. (1) **Observation**: mỗi lần một nguồn thấy một identifier, lưu `(tenant_uid, source = metadata.product.name + log_name, identifier type, value, first_seen, last_seen)`, dựng lại được từ log. (2) **Source record**: bản ghi asset theo từng nguồn (từ 5001/5003/5023 hoặc gom từ Activity), giữ `device.uid` của nguồn làm "source identifier", không dùng làm khoá toàn cục [18]. (3) **Resolved entity**: `asset_uid` và `identity_uid` nội bộ (không có trong OCSF 1.9.0; xem phần extension), mỗi entity là một resolution group có primary record và các alias, theo mẫu Elastic [3]. (4) **Curated attributes**: criticality, owner, tag, role, ghi chú, override. Lớp này lưu riêng và không bao giờ bị rebuild ghi đè. Mọi khoá đều mở đầu bằng `tenant_uid`. Khoá hợp nhất cho device xếp từ mạnh đến yếu:

| Hạng | Khoá (luôn kèm `tenant_uid`) | Trường OCSF 1.9.0 | Ghi chú |
|---|---|---|---|
| 1 | Agent ID theo sản phẩm | `device.agent_list[].uid` + `vendor_name`, `type_id` | Khoá chặn: hai agent cùng sản phẩm có ID khác nhau thì không bao giờ gộp (Tenable UUID) [1] |
| 2 | Cloud instance ID / ARN | `device.instance_uid`, `device.uid` (ARN), `cloud.account.uid`, `resource_details.uid` | Ổn định với VM/cloud |
| 3 | Machine/hardware ID | `device.os_machine_uuid`, `hw_info.uuid`, `hw_info.serial_number`, `imei`/`udid` | Loại placeholder ("To be filled by O.E.M.") như Axonius [4] |
| 4 | MAC | `device.mac`, `network_interfaces[].mac` | Loại MAC ngẫu nhiên/ảo; chặn MAC gắn ≥ N IP trong 2 giờ (QRadar) [38] |
| 5 | Hostname/FQDN + domain | `device.hostname`, `name`, `domain` | Không phân biệt hoa thường, chuẩn hoá FQDN (Tenable) |
| 6 | IP trong (zone, cửa sổ thời gian) | `device.ip`, `src_endpoint.ip`, `network_interface.namespace` | Chỉ là bằng chứng có thời hạn, cửa sổ ngắn (runZero 3 ngày) [2]; không tự gộp chỉ vì trùng IP |

**Nhận định:** với identity, dùng thứ tự `user.uid` (SID/ObjectID/ARN) → `ldap_person.employee_uid` → `email_addr` → `uid_alt` → `name`+`domain`. Có namespace theo IdP như Elastic, nên cùng username ở Okta và AD không tự gộp nếu thiếu bằng chứng mạnh. Account local thấy từ EDR được coi là "medium confidence", gắn với host [26][20]. Thứ tự alias của Google (`windows_sid` > email > userid > employee_id) là một tham chiếu khác [34]. Chỉ gộp tự động khi khớp hạng 1–3, hoặc khớp hạng 4–5 mà không có mâu thuẫn ở hạng cao hơn. Mọi trường hợp còn lại đưa vào hàng chờ "đề xuất gộp", có nút Explain kiểu Axonius (Match / Contradiction / Missing / Weak) [4].

### Provenance và ưu tiên nguồn theo trường

**Nhận định:** giá trị hiển thị của mỗi trường lấy từ bảng ưu tiên nguồn **theo trường, theo tenant**, theo mẫu Tenable Information Order và Axonius Preferred [47][9]. UI luôn cho mở ra xem giá trị của từng nguồn kèm last seen. Bảng mặc định gợi ý: hostname, OS, agent lấy EDR > MDM > scanner > CMDB. IP và MAC lấy nguồn streaming mới nhất (EDR, DHCP, VPN) trước nguồn batch, đúng như Splunk mô tả [25]. Owner, business unit, environment lấy CMDB > IdP/HR > suy luận từ authentication (top 3 user trong 7 ngày như DataBee) [20]. Criticality theo thứ tự override thủ công > rule > classifier. Mỗi trường có field aging: giá trị không được nguồn nào xác nhận lại trong N ngày thì hết hiệu lực [16].

### Vòng đời

**Nhận định:** dùng các trạng thái `candidate` (mới thấy, chưa đủ khoá mạnh) → `active` → `not_seen` → `stale` → `retired`/`archived`, với ngưỡng tuỳ lớp tài sản. VM/container tự scale dùng ngưỡng ngắn kiểu Cortex 3/5/7 ngày [28]. Endpoint và server dùng 7/30 ngày. User và thiết bị vật lý archive sau 1 năm như DataBee [20]. Thêm hai cờ nội bộ độc lập với trạng thái: `managed` (có agent EDR, suy từ `device.agent_list[].type_id = 1`; OCSF cũng có `device.is_managed` do nguồn báo) và `telemetry_gap` (asset active theo nguồn này nhưng im lặng ở nguồn kỳ vọng khác). Dùng CIS 1.1 để đo inventory: M4 là stale, M5 là unknown [83].

### Criticality, role và tag

**Nhận định:** dùng thang 5 giá trị khớp `resource_details.criticality_id` của OCSF 1.9.0 (Unknown, Low, Medium, High, Very High) để xuất ra chuẩn mà không phải dịch [19], và giữ tách khỏi risk score tính toán. Gán qua ba lớp theo mẫu Microsoft: classifier dựng sẵn (DC, Exchange, DB, jump host, máy có tài khoản privileged, cloud prod), rule dạng query builder trên các trường profile có preview, và override thủ công bắt buộc có lý do và hạn review (CrowdStrike chỉ để ô lý do tuỳ chọn, nên đây là mức chặt hơn) [5][6]. Khi nhiều rule cùng khớp thì mức cao nhất thắng. Tài sản dưới ngưỡng tự phân loại vào hàng Pending Approval, và luôn có nút revert về mức hệ thống [5][7]. **Role** (vulnerability scanner, DC, jump host, build server, honey user, service account) là một tag family riêng, dùng làm điều kiện cho detection, suppression và baseline, theo mẫu Cortex Asset Roles [45]. Tag thủ công có ngày hết hạn [9]. Mỗi tenant có bộ rule riêng, khởi tạo từ template của MSSP và có thể override. Không vendor nào có tài liệu về cơ chế này, nên đây là chỗ để sản phẩm tạo khác biệt.

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
| Khai báo nguồn context | Connector CMDB/IdP/cloud/scanner theo tenant, có lịch đồng bộ, thứ hạng ưu tiên theo trường, chọn class OCSF nào đi vào resolution | Splunk A&I/Exposure Analytics, DataBee Inclusion List [21][20] |
| Import CSV | Import asset, criticality, role, link identity. Kiểm tra từng dòng, chạy thử (dry-run), báo dòng lỗi, ghi audit | Elastic, Sumo [23][22] |
| Rule phân loại | Query builder trên trường profile, có preview số asset bị ảnh hưởng, mức cao nhất thắng, bật/tắt từng rule, tạo rule từ bộ lọc đang xem | Microsoft, CrowdStrike [5][6] |
| Merge / unmerge | Hàng chờ đề xuất gộp kèm Explain; gộp hay tách bằng tay đều ghi audit; unlink hàng loạt có trên cả UI, không chỉ API | Elastic, Axonius, Tenable [3][4] |
| Duyệt thay đổi | Pending Approval cho tài sản dưới ngưỡng tự phân loại, override criticality ở mức Very High, suppression theo role; người duyệt phải khác người đề xuất | Microsoft Pending Approval [5] |
| Vệ sinh dữ liệu | Rule chặn dữ liệu bẩn (MAC nhiều IP, Wi-Fi công cộng, placeholder), allowlist, cảnh báo "asset growth deviation" | QRadar [38][39] |
| Coverage gap query | Truy vấn lưu sẵn, chạy theo lịch, ví dụ: server Very High không có EDR; có EDR nhưng EDR last seen > 7 ngày trong khi auth vẫn thấy; asset active không có log auth; asset có trong CMDB mà telemetry 30 ngày không thấy (M4); telemetry thấy mà không có trong CMDB (M5) | Axonius, CIS 1.1/8.2 [65][83][82] |
| Tính lại và health | Nút "tính lại risk ngay", health của từng nguồn context theo last seen (Fail khi vượt cửa sổ) | Elastic, Splunk diagnostics [23][54] |
| Review định kỳ | Hàng việc review criticality và role, ưu tiên asset "Unassigned" và rule hết hạn | Microsoft, CrowdStrike [56][6] |
| API/IaC | API cho mọi thao tác ghi, có thể quản lý rule bằng Terraform | Sumo, Elastic [41][26] |

Workflow triage dùng profile: analyst mở alert và thấy ngay criticality, role, owner và coverage của asset trong flyout. Profile bổ sung prevalence và "lần đầu thấy" để đánh giá mức bất thường. Analyst đánh dấu là hành vi kỳ vọng thì tạo suppression gắn role, có hạn và vào hàng duyệt, không whitelist vĩnh viễn kiểu Exabeam [10].

### Profile nuôi giảm nhiễu như thế nào

**Nhận định:** cách triển khai theo thứ tự. (1) **Enrich lúc ingest/detection**: resolve `device`, `src_endpoint`, `dst_endpoint`, `user`, `actor.user` của mỗi event OCSF về `asset_uid`/`identity_uid` của **cùng tenant**, rồi gắn criticality, role, owner, environment vào `enrichments[]` (`type` = `"asset_context"`, `provider` = tên hệ thống) [114][118]. Lấy theo validity interval tại thời điểm event, giống Google [35]. (2) **Ma trận urgency severity × criticality** theo mẫu Splunk, mỗi tenant sửa được [30]. (3) **Risk modifier minh bạch**: nhân theo criticality (gợi ý khởi điểm như Elastic: 0,5/1/1,5/2, hoặc ×1,5 cho đích critical như Splunk), cộng cho watchlist hoặc privileged. Hiển thị phần đóng góp theo category trên alert và trên profile [12][124]. (4) **Suppression theo lớp tài sản**: rule detection tham chiếu `role:vuln-scanner`, `role:jump-host`, `env:dev` thay vì IP, có lịch (cửa sổ scan), hạn và audit. (5) **Baseline theo role/asset group** để giảm nhiễu từ gốc (Exabeam asset group, Cortex role baseline) [49][45]. (6) **Đo lường bằng dữ liệu của chính hệ thống, không dựa vào số vendor**: tỉ lệ alert có asset resolve được (Graylog cho thấy không có asset thì không có risk) [68], số alert mỗi tenant trước và sau, tỉ lệ true positive theo mức criticality, và số suppression hết hạn chưa review.

### Đa tenant

**Nhận định:** (1) Pipeline **ghi đè** `metadata.tenant_uid` theo kênh ingest (collector hoặc API key của tenant), không tin giá trị nguồn gửi lên. Không nhầm nó với `idp.tenant_uid` hay `cloud.account.uid` [17][113]. (2) Khoá IP có dạng `(tenant_uid, network_zone, ip, khoảng thời gian)`. Zone lấy từ subnet directory của tenant, hoặc từ `network_interface.namespace`/`resource_details.namespace`, theo mẫu Splunk zone và QRadar domain [16][15][108]. Mọi lookup enrichment phải chạy trong phạm vi tenant của event, không bao giờ tra toàn cục. (3) Cấu hình (ma trận urgency, risk factor, classifier, role, ngưỡng lifecycle, thứ hạng nguồn) tách theo tenant, kế thừa từ template MSSP, có hiển thị "khác template ở đâu". (4) View MSSP theo mẫu Defender MTO: danh sách tenant với các chỉ số chuẩn hoá (asset Very High, unmanaged, silent, stale, coverage %, newly discovered), inventory gộp có cột tenant, và drill-down sang profile của tenant [81]. (5) Risk score và entity graph không được trộn giữa các tenant. Google phải giới hạn Risk Analytics cho global scope khi bật RBAC, cho thấy điểm thực thể khó tách phạm vi về sau, nên tách từ đầu [34]. (6) Thao tác ghi từ view MSSP vẫn ghi audit theo tenant.

### Khoảng trống OCSF cần extension

**Nhận định:** đặt các trường còn thiếu vào một extension OCSF riêng của SOC (đăng ký qua `metadata.extensions`), không đưa vào `unmapped` [17][93]. Mọi trường trong bảng dưới là **extension đề xuất**, không tồn tại trên các object này trong schema 1.9.0 (đã đối chiếu `objects/*.json` và `dictionary.json` tại tag 1.9.0). Ba trường `criticality_id`, `tags`, `labels` đã có trong dictionary nên extension chỉ cần gắn chúng vào object mới, giữ nguyên enum; các trường còn lại là tên mới.

| Trường (extension đề xuất) | Gắn vào | Có trong dictionary 1.9.0? | Ghi chú |
|---|---|---|---|
| `asset_uid` / `identity_uid` | `device`, `endpoint` / `user` | Không | ID entity đã resolve của kho asset, khác `device.uid` của nguồn |
| `criticality_id` (+ `criticality`) | `device`, `user` | Có (hiện chỉ trên `resource_details`) | Cùng enum 0–4, 99 [19] |
| `tags`, `labels` | `device`, `user` | Có (hiện trên `account`, `resource_details`, `metadata`…) | Tag/role của profile |
| `asset_role[]` | `device`, `user` | Không | Vd `vuln-scanner`, `jump-host`, `service-account` |
| `environment`, `business_unit` | `device` | Không | prod/stage/dev; BU từ CMDB |
| `last_logon_user` | `device` | Không | Tách khỏi `owner`, vì định nghĩa `endpoint.owner` đang gộp hai nghĩa [67] |
| `lifecycle_state` | `device`, `user` | Không | candidate/active/not_seen/stale/retired |
| `coverage[]` | `device` | Không | Nguồn, log type, last_seen, expected |
| `resolution_confidence` | `device`, `user` | Không | Độ tin cậy của việc gắn event vào entity |

Trong lúc chưa có extension, dùng hai đường hợp chuẩn: gắn `enrichments[]` cho event Activity, và gắn `resources[]` (`resource_details` có `criticality_id`, `tags`, `labels`, `owner`, `namespace`, lồng `device`/`user`) cho Finding [19]. Có thể xuất ngược kho asset thành event Device Inventory Info 5001 / User Inventory Info 5003 với `metadata.product` là hệ thống asset của SOC, để consumer OCSF khác dùng chung [95][96]. Lịch sử thuộc tính và trạng thái thực thể theo thời gian nằm ngoài phạm vi OCSF (OCSF chỉ có `updated_*` trong một event), nên phải lưu trong kho entity [93].

## Các nguồn bất đồng ở đâu

Ba điểm lệch đáng chú ý, cộng một mâu thuẫn khái niệm. Thứ nhất, Tenable tự mâu thuẫn về connector nào thắng khi không có dữ liệu native: trang Deduplication nói ưu tiên "by the order they were connected" [1], còn FAQ nói connector xử lý thành công đầu tiên làm nguồn chính, và trang FAQ còn sót ghi chú nội bộ "[SME REVIEW]" [120]. Nên tin trang chính hơn, nhưng bài học là thứ tự ưu tiên phải hiện rõ và chỉnh được, như chính Tenable làm với Information Order. Thứ hai, Tenable nói AES kết hợp VPR với ACR [121], trong khi trang scoring cloud nói ACR không ảnh hưởng AES [122]. Có lẽ khác nhau theo loại tài sản. Cả hai chỉ đọc qua trích đoạn nên chưa phân xử được. Thứ ba, các con số giảm alert của Splunk RBA lệch nhau giữa các tài liệu: 60–80% trong blog ES 6.4 [73], 30–80% trong ebook RBA (ghi chú là từ một testimonial) [14]. Không con số nào có phương pháp đo công bố, nên không dùng được làm benchmark. Về khái niệm, OCSF gộp "chủ sở hữu" với "người đăng nhập gần nhất" vào `endpoint.owner` [67], còn các vendor tách hai khái niệm này (Exabeam Top User, Rapid7 primary user theo số lần logon, DataBee owner gợi ý) [50][40][20]. Nên theo cách của vendor.

## Kết luận và hàm ý

Phát hiện quan trọng nhất là giá trị của một asset profile cho SOC không nằm ở số trường, mà ở ba thuộc tính ít được quảng cáo. Một là **hợp nhất gỡ được và giải thích được** (Elastic resolution group, Axonius Explain, Tenable Cluster Logic). Hai là **provenance và last seen theo từng nguồn**, thứ biến profile thành công cụ coverage. Ba là **ngữ cảnh do người gán được tách khỏi dữ liệu dựng lại từ log**, để hệ thống rebuild được mà không mất công sức của analyst. Ngữ cảnh tài sản giúp giảm nhiễu, nhưng bằng chứng chỉ xác nhận *cơ chế*, chưa xác nhận *mức độ*. Vì vậy sản phẩm nên đo hiệu quả bằng dữ liệu tenant của chính nó ngay từ đầu.

Với mục đích của chủ repo, OCSF 1.9.0 là lớp vận chuyển đủ tốt cho dữ liệu quan sát, nhưng không thay được kho entity. Ba quyết định nên chốt sớm vì khó sửa về sau: khoá entity luôn mở đầu bằng `tenant_uid` cộng zone cho IP; thang criticality khớp `criticality_id` (1–4) của OCSF; và một extension nhỏ cho `asset_uid`, criticality, tag và role trên `device`/`user`. Khoảng trống chung của mọi vendor (cấu hình criticality theo tenant kế thừa template MSSP, quy trình duyệt cho sửa tay, suppression có hạn) cũng là chỗ sản phẩm có thể làm tốt hơn hiện trạng.

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
- Nội dung PDF CISA/ASD "Best practices for event logging and threat detection" (2024-08-21) chưa đọc được (cyber.gov.au trả 503) [123]. Nhóm task INV của NIST SP 800-92r1 (bản ipd 2023) cũng chưa đọc.
- OCSF: chưa đối chiếu enum `device.type_id` sau khi compile trên schema.ocsf.io/1.9.0, chưa xem extension `windows`/`linux`/`macos`. Các PR đang mở #1750 (physical_site) và #1724 (agent trust-base inventory) mới chỉ biết tiêu đề.
- Blog Splunk ES 6.4 [73] trả 404 khi kiểm chứng lại (2026-11-03); con số 60–80% chỉ còn thấy qua trích đoạn search.
- Giá trị điểm cụ thể Exabeam cộng cho executive hay service account, và implementation peer group hiện tại (blog nguồn từ 2016).

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
[11] Create risk factors to adjust risk scores in Splunk Enterprise Security (ES 8.1) — Splunk, 2025 (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.1/risk-based-alerting/create-risk-factors-to-adjust-risk-scores-in-splunk-enterprise-security
[12] Entity risk scoring — Elastic Docs, bản hiện hành 2026 (bậc 1). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/entity-risk-scoring
[13] Manage Risk Scores (Cortex Cloud) — Palo Alto Networks Docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-cloud-runtime-security/asset-managment/manage-asset-scores.md
[14] The Splunk Guide to Risk-Based Alerting (ebook) — Splunk (marketing), không rõ ngày (bậc 1). https://www.splunk.com/en_us/pdfs/gated/ebooks/the-splunk-guide-to-risk-based-alerting.pdf
[15] Overlapping IP addresses (domain example) — IBM QRadar Docs, không rõ ngày (bậc 1). https://www.ibm.com/docs/SSKMKU/com.ibm.qradar.doc/c_domain_example_ip_separation.html
[16] Entity zones in Exposure Analytics (ES 8.7) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.7/exposure-analytics/entity-zones-in-exposure-analytics
[17] OCSF schema 1.9.0 – objects/metadata.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/metadata.json
[18] OCSF schema 1.9.0 – objects/device.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/device.json
[19] OCSF schema 1.9.0 – objects/resource_details.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/resource_details.json
[20] Asset and Entity Resolution — DataBee Docs, không rõ ngày (bậc 1 về điều vendor mô tả). https://docs.databee.buzz/docs/entity-resolution
[21] Asset & Identity for Splunk Enterprise Security Part 1: Contextualizing Systems — Splunk (blog vendor), 2020-03-27 (bậc 1). https://www.splunk.com/en_us/blog/security/asset-identity-for-splunk-enterprise-security-part-1-contextualizing-systems.html
[22] View and Manage Entities — Sumo Logic Cloud SIEM Docs, không rõ ngày (bậc 1). https://www.sumologic.com/help/docs/cse/records-signals-entities-insights/view-manage-entities/
[23] Asset criticality — Elastic Docs, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/asset-criticality
[24] Introducing Exposure Analytics in Splunk Enterprise Security — Splunk (blog vendor), 2026-04-23 (bậc 1). https://www.splunk.com/en_us/blog/security/introducing-exposure-analytics-in-splunk-enterprise-security.html
[25] From Static A&I to Continuous Entity Discovery (Using Exposure Analytics in Splunk ES) — Splunk (blog vendor), 2026-06-12 (bậc 1). https://www.splunk.com/en_us/blog/security/using-exposure-analytics-in-splunk-es.html
[26] Entity store — Elastic Docs (Stack 9.4+), không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/entity-store
[27] Device discovery overview — Microsoft Learn, cập nhật 2026-04 (bậc 1). https://learn.microsoft.com/en-us/defender-endpoint/device-discovery
[28] Asset inventory overview (Cortex XSIAM) — Palo Alto Networks Docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/detect-investigate-and-respond-to-threats/asset-management/asset-inventory-overview.md
[29] Populate Splunk ES asset and identity lookups with entity discovery data (ES 8.8) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.8/exposure-analytics/populate-splunk-es-asset-and-identity-ai-lookups-with-entity-discovery-data
[30] How urgency is assigned to notable events in Splunk Enterprise Security (ES 7.2) — Splunk, 2023–2024 (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-7/user-guide/7.2/incident-review/how-urgency-is-assigned-to-notable-events-in-splunk-enterprise-security
[31] Review risk-based findings in Splunk Enterprise Security (ES 8.3) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.3/risk-based-alerting/review-risk-based-findings-in-splunk-enterprise-security
[32] Configure aliasing — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/event-processing/aliasing-overview
[33] Investigate users — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/investigation/investigate-user
[34] Risk Analytics overview — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/detection/risk-analytics-overview
[35] Overview of context-aware analytics — Google SecOps docs, 2025–2026 (bậc 1). https://docs.cloud.google.com/chronicle/docs/detection/context-aware-analytics
[36] Data enrichment and aliasing overview — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/event-processing/overview-of-aliasing-and-enrichment
[37] Asset profiles (QRadar 7.5) — IBM Docs, không rõ ngày (bậc 1; chỉ đọc qua bản tóm tắt). https://www.ibm.com/docs/en/qsip/7.5?topic=management-asset-profiles
[38] Asset reconciliation exclusion rules — IBM QRadar Docs, không rõ ngày (bậc 1). https://www.ibm.com/docs/en/SSKMKU/com.ibm.qradar.doc/c_qradar_ug_asset_recon_rules.html
[39] Prevention of asset growth deviations — IBM QRadar Docs, không rõ ngày (bậc 1). https://www.ibm.com/docs/en/SSKMKU/com.ibm.qradar.doc/c_qradar_adm_prevent_asset_grwth_deviat.html
[40] User Attribution — Rapid7 InsightIDR Docs, không rõ ngày (bậc 1). https://docs.rapid7.com/insightidr/user-attribution/
[41] Entity criticality — Sumo Logic Cloud SIEM Docs, không rõ ngày (bậc 1). https://www.sumologic.com/help/docs/cse/records-signals-entities-insights/entity-criticality/
[42] Explore devices in the device inventory — Microsoft Learn, cập nhật 2026-07 (bậc 1). https://learn.microsoft.com/en-us/defender-endpoint/machines-view-overview
[43] Investigate Identities — Microsoft Learn, cập nhật 2026-10 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/investigate-users
[44] Investigate devices in the Microsoft Defender for Endpoint devices list — Microsoft Learn, cập nhật 2026-07 (bậc 1). https://learn.microsoft.com/en-us/defender-endpoint/investigate-machines
[45] Asset Roles (Cortex XSIAM) — Palo Alto Networks Docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/detect-investigate-and-respond-to-threats/asset-management/asset-configurations/asset-roles.md
[46] Device profile — Trend Vision One Docs, không rõ ngày (bậc 1). https://docs.trendmicro.com/en-us/documentation/article/trend-vision-one-device-profile
[47] Asset Details (Tenable Exposure Management) — Tenable Docs, © 2026 (bậc 1). https://docs.tenable.com/exposure-management/Content/inventory/asset-details.htm
[48] Understanding assets — runZero Docs, không rõ ngày (bậc 1). https://help.runzero.com/docs/understanding-assets/
[49] What are Assets & Networks — Exabeam Docs (Advanced Analytics admin guide), © 2026 (bậc 1). https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/administration-guide/set-up-authentication-and-access-control/what-are-assets---networks-.html
[50] Get Started with the Asset Page — Exabeam Docs (Advanced Analytics), © 2026 (bậc 1). https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153684-get-started-with-the-asset-page.html
[51] Entity Analytics — Exabeam Docs (Advanced Analytics), © 2026 (bậc 1; đọc qua trích đoạn search). https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153683-entity-analytics.html
[52] IT hygiene — Wazuh documentation (current, ≈4.14), không rõ ngày (bậc 1). https://documentation.wazuh.com/current/getting-started/use-cases/it-hygiene.html
[53] Turn off merge for assets and identities in Splunk Enterprise Security (ES 8.4) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.4/asset-and-identity-management/turn-off-merge-for-assets-and-identities-in-splunk-enterprise-security
[54] Exposure Analytics diagnostics (ES 8.6) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.6/exposure-analytics/exposure-analytics-diagnostics
[55] Critical asset management overview — Microsoft Learn (Security Exposure Management), cập nhật 2026-10 (bậc 1). https://learn.microsoft.com/en-us/security-exposure-management/critical-asset-management
[56] Work with attack paths — Microsoft Learn (Security Exposure Management), cập nhật 2026-10 (bậc 1). https://learn.microsoft.com/en-us/security-exposure-management/work-attack-paths-overview
[57] Entity pages in Microsoft Sentinel — Microsoft Learn, cập nhật 2026-05 (bậc 1). https://learn.microsoft.com/en-us/azure/sentinel/entity-pages
[58] View entity details — Elastic Docs (Stack 9.3–9.5), không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/view-entity-details
[59] Investigate assets — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/investigation/investigate-asset
[60] Asset and identity investigator dashboards (ES 8.7) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/user-guide/8.7/analytics/asset-and-identity-investigator-dashboards
[61] Investigate a host (Cortex XSIAM) — Palo Alto Networks Docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/detect-investigate-and-respond-to-threats/investigation-and-response/investigate-artifacts-and-assets/investigate-a-host.md
[62] Users and Accounts — Rapid7 InsightIDR Docs, không rõ ngày (bậc 1). https://docs.rapid7.com/insightidr/users-and-accounts-on-your-domain/
[63] Hosts page — Elastic Docs, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/explore/hosts-page
[64] Entity analysis dashboard (ES 8.5) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/user-guide/8.5/exposure-analytics-and-ueba/entity-analysis-dashboard
[65] How to Detect Gaps in Endpoint Protection with Axonius — Axonius (blog vendor), 2025-06-02 (bậc 1). https://www.axonius.com/blog/detect-gaps-endpoint-protection-axonius
[66] Investigate a user (Cortex XSIAM) — Palo Alto Networks Docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/detect-investigate-and-respond-to-threats/investigation-and-response/investigate-artifacts-and-assets/investigate-a-user.md
[67] OCSF schema 1.9.0 – objects/endpoint.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/endpoint.json
[68] Risk Scores (Graylog Security 7.2) — Graylog Docs, không rõ ngày (bậc 1). https://go2docs.graylog.org/current/what_more_can_graylog_do_for_me/risk_scoring.htm
[69] What are Accounts & Groups — Exabeam Docs (Advanced Analytics admin guide), © 2026 (bậc 1; đọc qua trích đoạn search). https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/administration-guide/set-up-authentication-and-access-control/what-are-accounts---groups-.html
[70] Who Do I Belong To? Dynamic Peer Analysis for UEBA Explained — Derek Lin, Exabeam (blog vendor), 2016-09-20 (bậc 1, cũ). https://www.exabeam.com/blog/ueba/who-do-i-belong-to-dynamic-peer-analysis-for-ueba-explained/
[71] Prioritize incidents (Legacy) — Microsoft Learn, cập nhật 2026-09 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/incident-queue
[72] Introducing AI-powered incident prioritization in Microsoft Defender — Microsoft Tech Community (blog vendor), 2026-01 (bậc 1). https://techcommunity.microsoft.com/blog/microsoftthreatprotectionblog/introducing-ai-powered-incident-prioritization-in-microsoft-defender/4483834
[73] Better detections and cloud coverage with Splunk Enterprise Security 6.4 — Splunk (blog vendor, marketing), không rõ ngày (bậc 1; trả 404 ngày 2026-11-03, chỉ đọc qua trích đoạn search). https://splunk.com/en_us/blog/security/better-detections-and-cloud-coverage-with-splunk-enterprise-security-6-4.html
[74] Johnson Matthey customer success story — Splunk (marketing), không rõ ngày (bậc 1). https://splunk.com/content/dam/splunk2/en_us/pdfs/customer-success-stories/johnson-matthey.pdf
[75] Risk-Based Alerting: The New Frontier for SIEM — Splunk (blog vendor, marketing), không rõ ngày (bậc 1). https://www.splunk.com/en_us/blog/security/risk-based-alerting-the-new-frontier-for-siem
[76] Managing risk using risk-based alerting in Splunk Enterprise Security – best practices (ES 7.3) — Splunk, 2024 (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-7/risk-based-alerting/7.3/best-practices/managing-risk-using-risk-based-alerting-in-splunk-enterprise-security
[77] View and analyze risk score data — Elastic Docs, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/view-analyze-risk-score-data
[78] Silent-host monitoring — Google SecOps docs, 2025–2026 (bậc 1). https://docs.cloud.google.com/chronicle/docs/ingestion/silent-host-monitoring
[79] Check data ingestion health — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/ingestion/ingestion-overview
[80] Monitor the health of your data connectors — Microsoft Learn, 2026-07-02 (bậc 1). https://learn.microsoft.com/en-us/azure/sentinel/monitor-data-connector-health
[81] Devices in multitenant management — Microsoft Learn, 2024-03-15, cập nhật 2026-09 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/mto-tenant-devices
[82] CIS Controls Assessment Specification – Safeguard 8.2 — Center for Internet Security, không rõ ngày (bậc 1). https://controls-assessment-specification.readthedocs.io/en/latest/control-8/control-8.2.html
[83] CIS Controls Assessment Specification – Safeguard 1.1 — Center for Internet Security, không rõ ngày (bậc 1). https://controls-assessment-specification.readthedocs.io/en/latest/control-1/control-1.1.html
[84] MSSP multi-tenant (Cortex XSIAM) — Palo Alto Networks Docs, không rõ ngày (bậc 1). https://cortex-docs.paloaltonetworks.com/cortex-xsiam/configure-cortex-xsiam/multi-tenant/what-is-cortex-xsiam-multi-tenant/mssp-multi-tenant
[85] Data RBAC overview — Google SecOps docs, 2025–2026 (bậc 1). https://docs.cloud.google.com/chronicle/docs/administration/datarbac-overview
[86] Impact of data RBAC on features — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/administration/datarbac-impact
[87] Multi-tenancy on a single Google SecOps, part 3: who sees what and where the alert lands — Google Cloud Security Community, không rõ ngày (bậc 2–3, community). https://security.googlecloudcommunity.com/google-security-operations-2/multi-tenancy-on-a-single-google-secops-part-3-who-sees-what-and-where-the-alert-lands-7899
[88] Domain definition and tagging — IBM QRadar Docs, không rõ ngày (bậc 1). https://www.ibm.com/docs/en/SSKMKU/com.ibm.qradar.doc/c_domain_defining.html
[89] QRadar domains and multi-tenancy — Holly Wright, IBM Community, 2020-04-24 (bậc 2). https://community.ibm.com/community/user/blogs/holly-wright/2020/04/24/qradar-domains-and-multi-tenancy
[90] Enable entity zones (ES 6.4.1) — Splunk, không rõ ngày (bậc 1, bản cũ). https://docs.splunk.com/Documentation/ES/6.4.1/Admin/Entityzones
[91] Wazuh dashboard multi-tenancy — Wazuh documentation, không rõ ngày (bậc 1). https://documentation.wazuh.com/current/user-manual/wazuh-dashboard/multi-tenancy.html
[92] Format an asset or identity list as a lookup in Splunk ES — Splunk, không rõ ngày (bậc 1). https://docs.splunk.com/Documentation/ES/latest/User/AssetandIdentityLookupReference
[93] OCSF schema CHANGELOG.md (tag 1.9.0) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md
[94] OCSF schema 1.9.0 – events/discovery/discovery.json — OCSF (GitHub), tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/discovery.json
[95] OCSF schema 1.9.0 – Device Inventory Info (events/discovery/inventory_info.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/inventory_info.json
[96] OCSF schema 1.9.0 – User Inventory Info (events/discovery/user_inventory.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/user_inventory.json
[97] OCSF schema 1.9.0 – Software Inventory Info (events/discovery/software_info.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/software_info.json
[98] OCSF schema 1.9.0 – Cloud Resources Inventory Info (events/discovery/cloud_resources_inventory_info.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/cloud_resources_inventory_info.json
[99] OCSF schema 1.9.0 – Device Config State Change (events/discovery/device_config_state_change.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/device_config_state_change.json
[100] OCSF schema 1.9.0 – Operating System Patch State (events/discovery/patch_state.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/patch_state.json
[101] OCSF schema 1.9.0 – Authentication (events/iam/authentication.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/iam/authentication.json
[102] OCSF schema 1.9.0 – Network Activity (events/network/network_activity.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network_activity.json
[103] OCSF schema 1.9.0 – profiles/host.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/profiles/host.json
[104] OCSF schema 1.9.0 – events/findings (Vulnerability/Compliance/Detection Finding) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/tree/1.9.0/events/findings
[105] OCSF schema 1.9.0 – User Management (events/iam/user_management.json) — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/iam/user_management.json
[106] OCSF schema 1.9.0 – objects/device_hw_info.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/device_hw_info.json
[107] OCSF schema 1.9.0 – objects/agent.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/agent.json
[108] OCSF schema 1.9.0 – objects/network_interface.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/network_interface.json
[109] OCSF schema 1.9.0 – objects/user.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/user.json
[110] OCSF schema 1.9.0 – objects/ldap_person.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/ldap_person.json
[111] OCSF schema 1.9.0 – objects/_resource.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/_resource.json
[112] Add criticality_id, device, user to resource_details (PR #1693) — Paul Agbabian, OCSF (GitHub), merge 2026-07-28 (bậc 1). https://github.com/ocsf/ocsf-schema/pull/1693
[113] Issue #833: customer_uid / tenant identifier — Mike Radka, OCSF (GitHub), 2023-10-27 → đóng 2023-11-09 (bậc 1). https://github.com/ocsf/ocsf-schema/issues/833
[114] OCSF schema 1.9.0 – objects/enrichment.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/enrichment.json
[115] OCSF schema 1.9.0 – objects/observable.json — OCSF (GitHub), 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/observable.json
[116] Sample exposure finding — AWS Security Hub Docs, mẫu 2024-11 (bậc 1). https://docs.aws.amazon.com/securityhub/latest/userguide/exposure-findings-sample.html
[117] Open Cybersecurity Schema Framework (OCSF) in Security Lake — AWS Docs, không rõ ngày (bậc 1). https://docs.aws.amazon.com/security-lake/latest/userguide/open-cybersecurity-schema-framework.html
[118] Enrich with asset inventory — Tenzir Docs, không rõ ngày (bậc 2). https://tenzir.com/docs/guides/enrich/enrich-with-asset-inventory/
[119] What's new in OCSF 1.4.0 — Jonathan Rau, Query, 2025-02-06 (bậc 2). https://www.query.ai/resources/blogs/whats-new-ocsf-1_4_0/
[120] Asset Deduplication FAQ — Tenable Docs, © 2026 (bậc 1). https://docs.tenable.com/exposure-management/Content/getting-started/asset-dedup-faq.htm
[121] Host Asset Details (Tenable Vulnerability Management) — Tenable Docs, không rõ ngày (bậc 1; đọc qua trích đoạn search). https://docs.tenable.com/vulnerability-management/Content/Explore/asset-details-hosts.htm
[122] Cloud Security (CS) scoring explained — Tenable Docs, không rõ ngày (bậc 1; đọc qua trích đoạn search). https://docs.tenable.com/quick-reference/scoring-explained/Content/cloud-security.htm
[123] Best practices for event logging and threat detection — ASD's ACSC, CISA và các đối tác, 2024-08-21 (bậc 1). https://cisa.gov/resources-tools/resources/best-practices-event-logging-and-threat-detection
[124] Adjusting risk using risk factors in Splunk Enterprise Security (ES 8.4) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.4/risk-based-alerting/adjusting-risk-using-risk-factors-in-splunk-enterprise-security
