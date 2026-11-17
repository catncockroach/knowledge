# Dashboard inventory cấp tenant và MSSP

## Câu hỏi phụ 2: Dashboard inventory của một tenant gồm widget gì, loại biểu đồ nào cho câu hỏi nào, drill-down ra sao?

### Kết luận ngắn
Các vendor dùng chung một bộ khung: hàng KPI tile (số lớn, nhiều khi kèm % so với kỳ trước hoặc sparkline), donut hoặc pie cho phân bố theo loại/OS/mức exposure, bar xếp hạng (top N theo nguồn, phần mềm, CVE), line hoặc stacked bar theo thời gian (asset mới, xu hướng số asset, health của nguồn), Venn hoặc intersection cho độ phủ giữa các nguồn, bảng xếp hạng top asset rủi ro, và đôi khi bản đồ địa lý. Gần như mọi widget có drill-down: bấm vào một segment là mở danh sách asset đã lọc theo đúng truy vấn của segment đó. Mức chắc chắn **cao** cho khung chung và drill-down (docs chính thức của runZero, Axonius, Microsoft, Tenable, Elastic và Google đều mô tả rõ). Mức **trung bình** cho CrowdStrike, Cortex XSIAM, Trend và Armis vì không đọc được docs chi tiết.

### Phát hiện có nguồn

**runZero: danh mục widget và drill-down**
- Widget có sẵn chia nhóm: *Operational information* (Live assets, Active scans, Explorers online), *Trends* ("Asset trends: timeline of asset counts broken out by live, recent, and a couple of other states", Service trends), *Insights* (kết quả các truy vấn tự động sau lần scan gần nhất), *Most and least seen graphs* (biểu đồ theo Asset types, Operating systems, Hardware, MAC vendors, TCP/UDP ports, Products, Protocols, Risk, Criticality, Tags; mỗi biểu đồ bật được giữa most seen và least seen), *Goals*, *Asset count and trend tables* ("Asset ownership: view of all ownership types, including assets missing owners"; "Asset sources: view of all sources of asset data from supported integrations"; Custom integrations). — [runZero Dashboard docs](https://www.runzero.com/docs/dashboard/) (bậc 1, cập nhật 2026-09-17)
- Custom widget gồm 5 loại: Single match count, Single match trend, Multi-query match count, Multi-query trend line, Goal progress overview. Mỗi query chọn được màu riêng. — cùng nguồn
- Drill-down: "Except in timeline-based charts, you can view any widget's distinct data points in detail by clicking the relevant table row links or buttons, or individual segments of donut, bar, or column charts." Biểu đồ export ra SVG/PNG/JPEG, bảng export ra CSV. Có World Map và chế độ theater/kiosk. — cùng nguồn
- **Nhận định:** "least seen" là một mẫu đáng học. Nó lật biểu đồ phân bố để làm lộ các giá trị hiếm (OS lạ, MAC vendor lạ), vốn là tín hiệu của shadow IT.

**Axonius: loại chart và câu hỏi tương ứng**
- Có các loại chart: Field Segmentation (pie hoặc histogram, nhóm asset theo một field), Adapter Segmentation (asset theo nguồn dữ liệu), Query Intersection (Venn hoặc pie), Query Timeline, Multi-Line Timeline, Pivot (line, table, stacked bar hai chiều, 100% stacked bar, map), Query Comparison, Matrix Data (stacked), Field Summary, Asset Table, Adapter Connections Status, Device Discovery. — [Creating Dashboards and Charts with the AI Agent](https://docs.axonius.com/docs/creating-dashboards-and-charts-with-the-ai-agent) (bậc 1, không rõ ngày); danh sách trang lấy từ mục lục cùng site
- Query Intersection: so một base query với 1 đến nhiều query giao, "highlight the overlap between the intersecting queries". Pie và Bar cho tối đa 2 query giao, Venn tròn cho tối đa 3, Venn Triangle cho tối đa 6 (chỉ dành cho Axonius Identities). Ví dụ có sẵn: base "All devices" giao với "Missing EDR", tô màu theo ngưỡng; hoặc tất cả device giao với device seen trong 30 ngày. Bấm vào bar hay slice thì mở trang asset theo query đó. Vùng Venn không bấm được trong trường hợp Asset Investigation. — [Query Intersection Chart](https://docs.axonius.com/docs/query-intersection-chart) (bậc 1, không rõ ngày)
- Device Discovery chart là bar ngang xếp hạng adapter theo số device thấy được (top 20), kèm "Total Devices Seen" và "Total Unique Devices: The number of total unique devices after Axonius device correlation". Chart này trả lời câu "How many devices do I have?". Bấm vào một hàng thì mở trang Devices lọc theo adapter đó. — [Device Discovery Chart](https://docs.axonius.com/docs/device-discovery-chart) (bậc 1, không rõ ngày)
- Agent Coverage dashboards có 3 phần: *Scope & Compliance* ("evaluating the tool's footprint relative to the total managed inventory", ví dụ 500/1.000 device có CrowdStrike), *Coverage Status* ("total counts and proportions of devices based on their overall coverage status (active, inactive, missing, headless)"), *Coverage Health Trends Over Time* ("identify historical trends, spikes, or gradual degradation in coverage health"). — [Agent Coverage Dashboards](https://docs.axonius.com/docs/agent-coverage-dashboards) (bậc 1, không rõ ngày)
- Click-through: "Clicking a chart segment opens the Asset Table using the view associated with that segment". Với Query Intersection và Matrix, "the base query view is combined with the view for the specific intersecting query in the clicked segment". — [Chart Click-Through](https://docs.axonius.com/docs/chart-click-through) (bậc 1, không rõ ngày)

**Microsoft Defender**
- Device inventory không có biểu đồ. Nó dùng "count pills at the top of each tab (total, critical assets, high risk, high exposure, not onboarded, newly discovered)" và các tab theo loại (All devices, Computers & mobile, Network devices, IoT/OT, Uncategorized). Bấm pill hoặc thêm filter thì lọc ngay danh sách. — [Explore devices in the device inventory](https://learn.microsoft.com/en-us/defender-endpoint/machines-view-overview) (bậc 1, 2026)
- Overview của Exposure Management có: "Resolve Now" (Patch / Mitigate / Fix, mỗi mục là card đếm số recommendation, bấm để drill-down), bảng "Internet Exposed Resources" (cloud assets, devices, shadow resources), và "Domain initiative scores" (5 tile Code/Endpoint/Cloud/Identity/SaaS, mỗi tile có % so với target score kèm sparkline và delta). — [Get started with Exposure Management](https://learn.microsoft.com/en-us/security-exposure-management/get-started-exposure-management) (bậc 1, cập nhật 2026-07-26); ảnh đã xem
- Initiatives và metrics: mỗi initiative có "14 day change trend graph" và "14 day drift change". Top metrics hiển thị giá trị exposure hiện tại kèm trend 14 ngày, và drill-down được để sửa. — [Initiatives](https://learn.microsoft.com/en-us/security-exposure-management/initiatives), [Security metrics](https://learn.microsoft.com/en-us/security-exposure-management/security-metrics) (bậc 1, 2025–2026)
- Dashboard Vulnerability management gồm: gauge "Endpoint exposure score" (0–100, chia 3 dải màu), line "exposure score over time", bảng Top recommendations, Top vulnerable software (có sparkline exposed devices), Vulnerabilities insights (bar ngang tổng/exploitable/critical/zero-day), donut "Device exposure distribution" ("Select a section in the doughnut chart to go to the Devices list page..."), Top remediation activities (progress bar), Top exposed devices, Expiring certificates (stacked bar). Ghi chú: "Devices that aren't active in the last 30 days aren't factored in". — [Defender Vulnerability Management overview page](https://learn.microsoft.com/en-us/defender-vulnerability-management/tvm-dashboard-insights) (bậc 1, 2025–2026); ảnh đã xem
- Secure Score: History (line điểm theo thời gian kèm danh sách hành động), Metrics & trends (score zone, comparison trend so với tổ chức tương tự, score changes, regression trend, risk acceptance trend), comparison bar trên tab Overview. — [Track your Secure Score history](https://learn.microsoft.com/en-us/defender-xdr/microsoft-secure-score-history-metrics-trends) (bậc 1, không rõ ngày)

**Tenable Exposure Management**
- Dashboard dựng từ Widgets Library hoặc custom widget. Widget sửa được loại, categories, data labels, stacking, filter. Bấm widget thì drill-down vào trang Inventory. Data refresh 24 giờ một lần, giữ 90 ngày, chỉ tính asset có license. — [Dashboard Overview](https://docs.tenable.com/exposure-management/Content/analytics/dashboard-overview.htm) (bậc 1, không rõ ngày)
- Ảnh "Operational Dashboard": KPI tile (CES 533, Critical Detections 1.426, Assets With Critical Detections 103), mỗi tile kèm "Sequential Period Comparison" (%), bảng Top 5 Critical Detections, bar "Asset Exposure Score by Exposure Category", bộ chọn khoảng ngày, nhãn "Last Data Update". — cùng nguồn, ảnh dashboard-details.png (bậc 1, 2025)

**Splunk ES 8.6: Entity Discovery Insights**
- "Entity Discovery Insights offers visual, data-rich dashboards detailing asset trends, operating systems, cloud environments, default accounts, and NHI", và "users can drill directly from these dashboards into Entity Discovery Inventory". — [Deeper Exposure Analytics in Splunk ES 8.6](https://www.splunk.com/en_us/blog/security/deeper-exposure-analytics-in-splunk-enterprise-security-8-6.html) (bậc 1, 2026-08-04)
- Ảnh trong bài: tab Assets/Users/IPs/MACs; KPI "4,355 Discovered assets" và "6 Discovered asset types"; pie "Assets by type"; stacked bar "New assets by type" (theo ngày, tô màu theo loại); bản đồ "Asset locations" (bubble map); bảng "Asset subnets", "Ephemeral assets" (theo loại, kèm %), "Discovery sources" (vendor/nguồn × số asset); nút "View in Entity discovery inventory". — cùng nguồn (ảnh đã xem)

**Elastic Entity Analytics dashboard**
- Gồm Entity KPIs (số critical hosts, critical users, anomalies, có link sang trang Hosts/Users/Anomalies), các bảng User / Host / Service Risk Scores (top 5 gần nhất, lọc theo risk level, bấm tên thì mở flyout, bấm alert count thì sang Alerts hoặc Timeline), bảng Entities từ entity store (lọc theo Risk level, Criticality, Source), bảng Anomalies. — [Entity Analytics dashboard](https://www.elastic.co/docs/solutions/security/dashboards/entity-analytics-dashboard) (bậc 1, không rõ ngày)
- **Nhận định:** Elastic gần như chỉ dùng KPI và bảng xếp hạng, không dùng biểu đồ phân bố. Đây là trường phái "danh sách hành động" thay cho "biểu đồ toàn cảnh".

**Google SecOps: sức khoẻ dữ liệu (data freshness, coverage nguồn)**
- Health Hub có các big number widget: Healthy / Failed / Irregular Sources, Healthy / Failed / Irregular Parsers. Có các line graph: "Data Source Health Overview" (đường Healthy, Irregular, Failed theo ngày), "Parsing Health Overview", "Total Ingested Logs", "Failing Parser by Log Type". Bảng "Health Status by Data Source / by Parser" gồm trạng thái, source type, link sang Cloud Monitoring. Phát hiện bất thường bằng thống kê "with a 15-day lookback period"; irregular nghĩa là "unusual surges or drops in data volume or a significant change in error rates". Docs cảnh báo feed có thể hiện Active dù thu thập đang hỏng (silent auth failure). — [Use the Health Hub](https://docs.cloud.google.com/chronicle/docs/reports/data-health-monitoring-and-troubleshooting-dashboard) (bậc 1, không rõ ngày)
- Curated dashboards là read-only, copy ra để sửa. Có nhóm Ingestion metrics: throughput theo tuần, 6 tháng và all-time, bị giới hạn bởi hạn mức query 365 ngày. — [Curated dashboards overview](https://docs.cloud.google.com/chronicle/docs/reports/native-curated-dashboards) (bậc 1, không rõ ngày; chi tiết lấy từ snippet tìm kiếm, chưa đọc kỹ trang)

**Wazuh IT Hygiene (4.13+)**
- Từ 4.13.0 (2025-09-18) có dashboard IT Hygiene riêng cho truy vấn toàn cục. Các tab: Dashboard, System, Software, Processes, Network, Identity, Services. Tab Dashboard "visualizes key metrics such as operating system families, package types, installed packages, running packages, operating systems, host CPUs, source ports, and process start times". Hardware có top CPU models; Software có top vendors, package types, Windows KB most/least common. — [Viewing system inventory data](https://documentation.wazuh.com/current/user-manual/capabilities/system-inventory/viewing-system-inventory-data.html) (bậc 1, 2025–2026); [Release 4.13.0](https://documentation.wazuh.com/current/release-notes/release-4-13-0.html) (bậc 1, 2025-09-18)
- Ảnh cho thấy chủ yếu là bảng "Top 5" (OS families, installed packages, running processes, OS, host CPUs, endpoints by memory) và một stacked bar ngang "Package types". — cùng nguồn (ảnh đã xem)

**CrowdStrike Falcon Exposure Management**
- Phần "asset overview" của dashboard có số asset thiếu Falcon sensor (unmanaged). Người dùng bấm "the pink bar which represents all unmanaged assets" để drill-down, rồi lọc theo phân loại asset (vd critical infrastructure). Sau đó dùng Fusion workflow tự xử lý asset unmanaged mới. — [Identifying and Triaging Unmanaged Assets](https://www.crowdstrike.com/tech-hub/exposure-management/identifying-and-triaging-unmanaged-assets/) (bậc 1, 2024-05)

**Trend Vision One / Cortex XSIAM / Armis**
- Trend: views Devices / Cloud Assets / Internet-facing có widget Risk Summary (điểm rủi ro theo tháng: exposure, attack, security configuration) và "Assets at Risk" (nhóm theo loại asset, link sang Attack Surface Discovery). Nội dung widget phụ thuộc "asset visibility scope" của user. — snippet tìm kiếm từ [Trend Vision One Cloud Assets view](https://docs.trendmicro.com/en-us/documentation/article/trend-vision-one-cloud-assets-view) (bậc 1, không rõ ngày; **trang không mở được do redirect loop**, chỉ dùng làm manh mối)
- XSIAM: trang AI assets và data assets có "interactive widgets that summarize your risk" ở đầu trang. Unified Asset Inventory (beta) gom asset theo data source. — snippet từ [View the Unified Asset Inventory](https://docs-cortex.paloaltonetworks.com/r/Cortex-XSIAM/Cortex-XSIAM-Documentation/View-the-Unified-Asset-Inventory) (bậc 1; trang render JS, không đọc được nội dung)
- Armis: chỉ có tài liệu mua sắm hoặc marketing ("every report or dashboard is wholly customisable"), không có docs widget. — bậc 3, không dùng làm bằng chứng

### Bảng tổng hợp: câu hỏi vận hành → loại biểu đồ vendor dùng

| Câu hỏi | Loại biểu đồ | Vendor ví dụ |
|---|---|---|
| Có bao nhiêu asset, tăng hay giảm? | KPI tile + delta % kỳ trước, hoặc line/trend | Tenable (Sequential Period Comparison), Splunk, runZero Asset trends, MS initiative sparkline |
| Phân bố theo loại/OS/exposure level | Pie/donut (bấm segment để drill-down) | Splunk Assets by type, MS Device exposure distribution, Axonius Field Segmentation |
| Asset mới xuất hiện theo ngày | Stacked bar theo ngày, tô màu theo loại | Splunk New assets by type |
| Nguồn nào thấy bao nhiêu asset, unique sau correlation | Bar ngang xếp hạng + tổng unique | Axonius Device Discovery, Splunk Discovery sources, runZero Asset sources |
| Độ phủ EDR/agent, chồng lấn giữa nguồn | Venn / intersection pie / bar có ngưỡng màu; trend coverage | Axonius Query Intersection, Agent Coverage dashboards |
| Asset unmanaged / not onboarded | Count pill, bar riêng drill-down | MS count pills, CrowdStrike pink bar |
| Thiếu owner | Bảng count + trend | runZero Asset ownership |
| Exposure/vuln theo severity | Gauge điểm, line điểm theo thời gian, bar ngang theo loại vuln | MS Vulnerability management, Tenable |
| Top asset/user rủi ro | Bảng top N kèm link | Elastic Risk Scores, MS Top exposed devices, Tenable Top 5 |
| Sức khoẻ/độ tươi dữ liệu nguồn | Big number Healthy/Failed/Irregular + line theo ngày + bảng trạng thái | Google SecOps Health Hub |
| Giá trị hiếm/bất thường | Biểu đồ "least seen" | runZero |
| Vị trí địa lý | Bubble map / World Map | Splunk Asset locations, runZero World Map |
| Tiến độ mục tiêu | Goal progress, initiative % vs target | runZero Goals, MS Domain initiative scores |

### Nhận định
- Drill-down từ widget sang danh sách asset đã lọc đúng query của segment là chuẩn chung. Axonius còn ghép base query với query của segment. Dashboard của sản phẩm OCSF nên lưu mỗi widget dưới dạng query, để segment nào cũng mở được danh sách.
- KPI tile hầu như luôn đi kèm ngữ cảnh: delta % (Tenable), sparkline 14 ngày (MS), hoặc so với target (MS initiative). Một tile chỉ có con số trần thì hiếm gặp.
- Không vendor nào trong mẫu dùng Sankey cho coverage. Treemap cũng không thấy trong docs đã đọc. Coverage overlap được làm bằng Venn hoặc intersection (Axonius), hoặc bằng bảng nguồn × số asset (Splunk, runZero).
- "Data freshness" và health nguồn (Google Health Hub) tách thành dashboard riêng, không gộp vào inventory. Với SOC đa nguồn đây là mảnh thiết yếu, vì asset "silent" thường do nguồn hỏng chứ chưa chắc asset đã biến mất.

### Khoảng trống
- Không tìm được widget "% asset chưa phân loại criticality" hay "chất lượng dữ liệu inventory" như một widget có sẵn. MS chỉ có card "Classify critical assets", runZero có tab Uncategorized và least-seen, Axonius có thể tự dựng bằng Field Segmentation. Đây là nhận định, chưa có widget chuẩn.
- CrowdStrike, Cortex XSIAM, Trend, Armis: không đọc được danh sách widget chính thức (docs cần đăng nhập, render bằng JS hoặc redirect loop).
- Tenable Lumin và runZero Goals chưa đọc chi tiết.
- Không thấy vendor nào dùng heatmap giờ × ngày ở cấp inventory.

## Câu hỏi phụ 3: View tổng hợp đa tenant cho MSSP

### Kết luận ngắn
View MSSP của vendor hiện đơn giản: bảng tenant × vài KPI đếm (số device, critical, high exposure, chưa onboard), một hàng tổng ở trên, và link đi vào inventory của từng tenant. Mức chắc chắn **trung bình**: chỉ Microsoft có docs rõ. Sentinel và Wazuh cung cấp hạ tầng (cross-workspace query, tenant cho saved object), còn view tổng hợp do MSSP tự dựng. Không tìm thấy heatmap tenant × KPI dựng sẵn ở vendor nào.

### Phát hiện có nguồn
- Defender multitenant management, trang Tenants: "Each tenant page includes details such as the number of devices and device types, the number of high value and high exposure devices, and the number of devices available to onboard". Ở đầu trang có số tenant và số device onboarded/discovered trên mọi tenant. Bấm tên tenant thì sang device inventory của tenant đó. Trang Device inventory đa tenant giống trang của một tenant nhưng thêm cột Tenant name, và "the total number of devices, critical assets, high risk devices, and internet-facing devices for all tenants are shown at the top". — [Devices in multitenant management](https://learn.microsoft.com/en-us/defender-xdr/mto-tenant-devices) (bậc 1, không rõ ngày); ảnh tenant view đã có trong report cũ
- Sentinel cho MSSP: triển khai workbook ở managing tenant qua Azure Lighthouse để "create at-scale dashboards to monitor and query data across customer tenants". Cross-workspace query dùng `union` + `workspace()`, workbook có workspace selector dạng dropdown. Workspace manager (preview) quản lý nhiều workspace, kể cả qua nhiều tenant khi có Lighthouse. — [Manage Sentinel workspaces at scale (Lighthouse)](https://learn.microsoft.com/en-us/azure/lighthouse/how-to/manage-sentinel-workspaces), [Extend Sentinel across workspaces and tenants](https://learn.microsoft.com/en-us/azure/sentinel/extend-sentinel-across-workspaces-tenants), [Workspace manager](https://learn.microsoft.com/en-us/azure/sentinel/workspace-manager) (bậc 1; nội dung lấy từ snippet tìm kiếm, giới hạn "up to 20 workspaces per query" chỉ thấy trên bản docs.azure.cn, **chưa xác minh**)
- Microsoft Secure Score có "comparison bar chart" và "comparison trend" so điểm của tổ chức với các tổ chức tương tự (ẩn danh). Đây là mẫu peer benchmark có thể dùng lại cho ranking tenant. — [Secure Score history & trends](https://learn.microsoft.com/en-us/defender-xdr/microsoft-secure-score-history-metrics-trends) (bậc 1)
- Wazuh: "tenants are containers for saved objects such as index patterns, visualizations, and dashboards", gán cho role read/write. Bật bằng `opensearch_security.multitenancy.enabled`. Docs không nói tenant cô lập index. Cộng đồng gợi ý mỗi khách một cluster, thêm cluster trung tâm dùng cross-cluster search (bậc 3). — [Wazuh multi-tenancy](https://documentation.wazuh.com/current/user-manual/wazuh-dashboard/multi-tenancy.html) (bậc 1); [Google Groups thread](https://groups.google.com/g/wazuh/c/-141kWNG2Yc) (bậc 3, 2024)
- Cortex XSIAM: Tenant Navigator cho "view and switch to tenants to which you have access divided per CSP account"; XSIAM 3.1 hỗ trợ ghép cặp parent/child tenant cross-region. Không thấy mô tả dashboard tổng hợp inventory đa tenant. — snippet từ [Use the Interface – XSIAM Admin Guide](https://docs-cortex.paloaltonetworks.com/r/65fu08NUcsJMd3MV4tcofQ/e9HapcJCeha60seL43hn4Q) (bậc 1; chưa mở trang)
- Trend: nội dung widget phụ thuộc "asset visibility scope" của user. Mô hình phân quyền này cũng áp dụng được cho MSSP. — snippet Trend docs (bậc 1, chưa mở được trang)

### Nhận định
- Microsoft giữ cùng một bố cục cho view đa tenant và view một tenant (KPI ở trên, bảng ở dưới, thêm cột Tenant), rồi drill-down từ hàng tenant vào inventory của tenant. Đây là mẫu đơn giản, nhất quán, nên theo.
- Heatmap tenant × KPI và ranking tenant theo coverage hay freshness chưa có sẵn ở vendor nào trong mẫu. Đó là khoảng trống sản phẩm, và cũng là cơ hội. Các thành phần dựng nó đều đã có: bảng tenant × KPI (MS), peer comparison (Secure Score), workbook cross-workspace (Sentinel).

### Khoảng trống
- Google SecOps (MSSP / multi-instance), Axonius MSSP, Splunk ES đa tenant: chưa tìm được docs về view tổng hợp. Trang Axonius thử đoán `multi-tenant-dashboards` không có nội dung.
- Không có ảnh MSSP mới nào ngoài ảnh Defender tenant view đã có trong report cũ.

## Hình minh hoạ giao diện

Mọi URL đều đã kiểm tra ngày 2026-11-03 bằng `curl -sSIL`, trả về 200 với content-type image/*, và đã xác nhận magic bytes (PNG `89504e47`, JPEG `ffd8ffe0`). Cột mô tả ghi "(đã xem)" khi agent đã mở xem ảnh; các ảnh còn lại được mô tả theo chú thích hoặc tên file trong docs.

| Vendor | Dashboard/widget | Mô tả những gì ảnh thể hiện | Image URL | Trang nguồn | Đã kiểm tra |
|---|---|---|---|---|---|
| Splunk ES 8.6 | Entity discovery insights | (đã xem) KPI 4.355 discovered assets và 6 asset types; pie Assets by type; stacked bar New assets by type theo ngày; bubble map Asset locations; bảng Asset subnets, Ephemeral assets, Discovery sources (vendor × số asset); nút View in inventory | https://www.splunk.com/content/dam/splunk-blogs/images/media_163d82c78b9192b4325e24b26e6a06e7e828a320f.png | https://www.splunk.com/en_us/blog/security/deeper-exposure-analytics-in-splunk-enterprise-security-8-6.html | 200, image/jpeg (đuôi .png nhưng nội dung là JPEG) |
| Splunk ES 8.6 | Entity record change history (cấp asset) | (đã xem) bảng lịch sử bản ghi asset theo ngày (IP, MAC, OS version, User ID), ô thay đổi đánh dấu vạch tím "Record changed" | https://www.splunk.com/content/dam/splunk-blogs/images/media_10d8ff50825a5063fad076c825bd8c196c696750b.png | như trên | 200, image/jpeg |
| Microsoft | Exposure Management Overview | (đã xem) Resolve now (card Patch / Mitigate / Fix có số recommendation), bảng Internet-exposed resources, 5 tile Domain initiatives (% so với target, sparkline, delta %) | https://learn.microsoft.com/en-us/security-exposure-management/media/get-started-exposure-management/exposure-management-overview.png | https://learn.microsoft.com/en-us/security-exposure-management/get-started-exposure-management | 200, image/png |
| Microsoft | Vulnerability management dashboard | (đã xem) gauge exposure score 23/100; line exposure score theo thời gian; donut Device exposure distribution; bar ngang Vulnerabilities insights; progress bar remediation; bảng top exposed devices kèm criticality; stacked bar certificates | https://learn.microsoft.com/en-us/defender/media/defender-vulnerability-management/new-overview.png | https://learn.microsoft.com/en-us/defender-vulnerability-management/tvm-dashboard-insights | 200, image/png |
| Microsoft | Initiatives list | danh sách initiative kèm score và 14-day trend (theo chú thích) | https://learn.microsoft.com/en-us/security-exposure-management/media/initiatives/initiatives-window.png | https://learn.microsoft.com/en-us/security-exposure-management/initiatives | 200, image/png |
| Tenable | Operational Dashboard | (đã xem) KPI tile CES / Critical Detections / Assets With Critical Detections kèm Sequential Period Comparison %; bảng Top 5 CVE; bar Asset Exposure Score by category; bộ chọn khoảng ngày; Last Data Update | https://docs.tenable.com/exposure-management/Content/Resources/Images/Local/exposure-management/dashboard-details.png | https://docs.tenable.com/exposure-management/Content/analytics/dashboard-overview.htm | 200, image/png |
| Axonius | Device Discovery chart | (đã xem) bar ngang xếp hạng adapter theo số device (ServiceNow 1.975…), Total Devices Seen 19.643 và Total Unique 4.787 | https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/DeviceDiscoveryChart_24.png | https://docs.axonius.com/docs/device-discovery-chart | 200, image/png |
| Axonius | Query Intersection: cấu hình | (đã xem) chọn Venn hoặc Pie; base query giao với 3 query: device bị loại khỏi agent coverage (Trellix ePO), device có CISA KEV, device seen trong 30 ngày | https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/QueryIntersectionsChart2.png | https://docs.axonius.com/docs/query-intersection-chart | 200, image/png |
| Axonius | Venn chart preview | ví dụ Venn 3 vòng cho overlap giữa các query (theo chú thích) | https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/img/Dashboards/VennChartPreviewExample.png | https://docs.axonius.com/docs/query-intersection-chart | 200, image/png |
| Axonius | Adapter Segmentation chart | phân bố asset theo nguồn/adapter (theo chú thích) | https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/AdapterSegmentationChart.png | https://docs.axonius.com/docs/adapter-segmentation-chart | 200, image/png |
| Axonius | Query Timeline chart | line số asset khớp query theo thời gian (theo chú thích) | https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/TimeLineChart.png | https://docs.axonius.com/docs/query-timeline-chart | 200, image/png |
| Axonius | Query Timeline (chế độ %) | timeline hiển thị theo phần trăm (theo tên file) | https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/QTC-Percent.png | https://docs.axonius.com/docs/query-timeline-chart | 200, image/png |
| Axonius | Agents Deployment Status (lối vào Agent Coverage dashboard) | (đã xem) bảng agent (Zoom, CrowdStrike, IGEL) gồm Configuration status, Active agents, Potential issues, nút Dashboard / View issues | https://files.readme.io/9d03b26ed0a366aeb853129361808f49ab95cb85c0f37a2f670fae3c123698da-image.png | https://docs.axonius.com/docs/agent-coverage-dashboards | 200, image/png |
| Elastic | Entity Analytics: Entities section | bảng entity store lọc theo risk level, criticality, source (theo chú thích) | https://www.elastic.co/docs/solutions/images/security-entities-section.png | https://www.elastic.co/docs/solutions/security/dashboards/entity-analytics-dashboard | 200, image/png |
| Elastic | Entity Analytics: Host risk scores | bảng top host risk score kèm alert count (theo chú thích) | https://www.elastic.co/docs/solutions/images/security-host-score-data.png | như trên | 200, image/png |
| Wazuh | IT Hygiene dashboard | (đã xem) các bảng Top 5 (OS families, packages, processes, OS, CPU, endpoints by memory) và stacked bar Package types | https://documentation.wazuh.com/current/_images/system-inventory-dashboard1.png | https://documentation.wazuh.com/current/user-manual/capabilities/system-inventory/viewing-system-inventory-data.html | 200, image/png |
| Wazuh | Vulnerabilities inventory dashboard | dashboard lỗ hổng theo severity, package, OS (theo tên file và ngữ cảnh) | https://documentation.wazuh.com/current/_images/vulnerabilities-inventory-dashboard1.png | https://documentation.wazuh.com/current/getting-started/use-cases/it-hygiene.html | 200, image/png |
| Google SecOps | Health Hub: Health status by data source | bảng trạng thái nguồn Healthy / Irregular / Failed (theo tên file và ngữ cảnh) | https://docs.cloud.google.com/static/chronicle/images/health-status-by-data-source-mu.png | https://docs.cloud.google.com/chronicle/docs/reports/data-health-monitoring-and-troubleshooting-dashboard | 200, image/png |
| Microsoft | MTO tenant view (MSSP) | bảng tenant × số device / critical / high exposure / to onboard | https://learn.microsoft.com/en-us/defender-xdr/media/mto-tenant-devices/devices-tenant-view.png | https://learn.microsoft.com/en-us/defender-xdr/mto-tenant-devices | đã có trong report cũ (dùng lại vì không có ảnh MSSP khác) |

Các URL đã loại:
- `learn.microsoft.com/.../security-exposure-management/media/metrics.png`, `.../secure-score-comparison-trend.png`, `.../mto-tenant-devices/devices-choose-device.png`: trả về text/html (trang lỗi).
- CrowdStrike `femiatua1.png` và `femiatua2.png`: là màn hình Fusion workflow, không phải dashboard.
- Splunk `.avif`: định dạng nằm ngoài danh sách cho phép, đã thay bằng biến thể `.png`.

## Truy vấn đã chạy
- Axonius docs dashboard chart types segmentation intersection timeline (standard)
- Microsoft Defender Exposure Management overview dashboard metrics initiatives score trend (standard)
- Splunk Enterprise Security exposure analytics dashboard asset coverage help.splunk.com (standard)
- Google SecOps data ingestion and health dashboard curated dashboards (standard)
- Cortex XSIAM asset inventory dashboard widgets multi-tenant (standard)
- Wazuh 4.13 IT hygiene dashboard documentation (standard)
- Trend Vision One Attack Surface Risk Management overview dashboard widgets asset (standard)
- Tenable Exposure Management dashboards exposure view asset inventory widgets docs (standard)
- Microsoft Sentinel workbook multiple workspaces MSSP Azure Lighthouse cross-tenant workbook (standard)
- Wazuh multi-tenancy MSSP dashboard per-tenant index (standard)
- CrowdStrike Falcon Exposure Management dashboard asset inventory unmanaged assets coverage widgets (standard)
- Armis Centrix dashboard asset inventory widgets boundaries device types risk (standard)
- Truy cập trực tiếp (curl/WebFetch): runZero dashboard docs; các trang Axonius (query-intersection, agent-coverage, device-discovery, chart-click-through, adapter-segmentation, query-timeline); MS device inventory, device discovery, get-started EM, initiatives, metrics, TVM dashboard, MTO devices, Secure Score; Tenable dashboard-overview; Elastic entity analytics; Wazuh system inventory; Google Health Hub và curated dashboards; Splunk blog 8.6; CrowdStrike tech hub
