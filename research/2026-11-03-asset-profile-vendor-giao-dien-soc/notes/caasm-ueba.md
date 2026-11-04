# CAASM, UEBA và mã nguồn mở (Axonius, runZero, Armis, Tenable, Exabeam, Securonix, Wazuh, Graylog)

Ghi chú chung: phần lớn nguồn là docs chính thức (bậc 1) nhưng docs vendor thường không ghi ngày đăng; khi không có ngày thì ghi theo metadata `updatedAt` hoặc năm copyright. Docs vendor là bằng chứng về điều vendor *tuyên bố/thiết kế*, không phải về hiệu quả.

## 1. Entity resolution / correlation tài sản từ nhiều nguồn

### Kết luận ngắn
Cả ba nền tảng CAASM/exposure có docs công khai (Axonius, runZero, Tenable) đều dùng **so khớp tất định theo thứ tự ưu tiên khoá định danh** (ID ngoài/agent → MAC → tổ hợp hostname/FQDN/IP → IP trong cửa sổ thời gian), **không công bố điểm confidence dạng số**. Thay vào đó họ đầu tư vào *giải thích* việc ghép (Axonius "Explain Correlation/Non-Correlation", Tenable "Asset Cluster Logic") và *thứ tự ưu tiên nguồn theo trường* (Tenable "Information Order", Axonius "Preferred Fields"). Mức chắc chắn: **cao** cho cơ chế khoá/ưu tiên (docs bậc 1), **trung bình** cho chi tiết giải quyết xung đột (docs mô tả chung chung, có chỗ mâu thuẫn).

### Phát hiện có nguồn
**Tenable Exposure Management (bậc 1, docs © 2026, không rõ ngày)**
- Thứ tự tiêu chí ghép thiết bị từ connector bên thứ ba: "External Identifier" → "Mac Addresses" → "Name + FQDNs + IP Addresses" → "Name + FQDNs" → "FQDNs + IP Addresses" → "Name + IP Addresses" → "Name"; chỉ cần một tổ hợp thoả là ghép; so khớp không phân biệt hoa thường và có parse định dạng MAC/hostname phổ biến — [Asset Deduplication in Tenable Exposure Management](https://docs.tenable.com/exposure-management/Content/getting-started/asset-deduping.htm) (bậc 1, © 2026)
- Ràng buộc cứng: "Assets with different Tenable UUIDs will never be merged, even if all other third-party matching criteria are met"; "Assets must belong to the same class to be merged" — cùng nguồn trên.
- Xung đột giá trị: "Tenable uses a fixed priority order to determine which value appears in the unified view"; nguồn Tenable-native ưu tiên hơn bên thứ ba; connector bên thứ ba ưu tiên "by the order they were connected" — cùng nguồn trên. Mâu thuẫn nhỏ: một trang FAQ khác nói connector xử lý thành công đầu tiên làm nguồn chính khi không có dữ liệu Tenable-native, và FAQ còn sót ghi chú nội bộ "[SME REVIEW]" — [Asset Deduplication FAQ](https://docs.tenable.com/exposure-management/Content/getting-started/asset-dedup-faq.htm) (bậc 1, © 2026).
- Không có merge thủ công trong UI cho trùng lặp Tenable-native: "Forced merging is not available in the UI"; không thấy mô tả unmerge — [Asset Deduplication](https://docs.tenable.com/exposure-management/Content/getting-started/asset-deduping.htm) (bậc 1).
- Trang chi tiết tài sản có **Asset Cluster Logic** (chỉ với tài sản đa nguồn) hiển thị tiêu chí và giá trị khớp (hostname, IP, MAC) đã kích hoạt mỗi lần ghép; **Show information order** cho biết thứ tự lấy giá trị thuộc tính từ các nguồn, chỉnh được ở Settings > Information Order Configuration — [Asset Details](https://docs.tenable.com/exposure-management/Content/inventory/asset-details.htm) (bậc 1, © 2026).

**runZero (bậc 1)**
- Ghép dữ liệu integration vào tài sản có sẵn theo thứ tự: MAC address → IP address (cửa sổ 3 ngày) → Hostname; khớp thì "updates the asset-level attributes and adds the integration-specific attributes", không khớp thì tạo tài sản mới trong site đã chọn (integration-only asset); có nút **Merge** thủ công trên Asset Inventory — [Inbound integrations](https://help.runzero.com/docs/integrations-inbound/) (bậc 1, không rõ ngày).
- Phạm vi ghép theo **site**: "An asset always belongs to a single site" và tài sản chỉ được correlate "only against assets within that site"; correlate "across multiple attributes"; khi fingerprint đổi nhiều thì có thể không correlate được, để lại trùng lặp "usually marked as offline", xoá tay — [Understanding assets](https://help.runzero.com/docs/understanding-assets/) (bậc 1, không rõ ngày).
- Khi fingerprint tùy biến và built-in cùng khớp, "the fingerprint with the higher 'certainty' value(s) wins"; thuộc tính `fp.*` được chuẩn hoá thành `os`, `os_version`, `hw`, `type` — [Using custom fingerprints](https://help.runzero.com/docs/using-custom-fingerprints/) và [Understanding fingerprints](https://help.runzero.com/docs/fingerprinting/) (bậc 1; trích qua kết quả search, chưa mở trang đầy đủ).
- Bản 3.7 sửa lỗi "could cause assets to incorrectly merge" — [runZero 3.7](https://www.runzero.com/blog/runzero-3-7/) (bậc 1, blog vendor; trích qua search).
- Docs không nói nguồn nào thắng khi xung đột; chỉ cảnh báo vì "some asset attribute fields are merged", gỡ integration có thể xoá thuộc tính mà scan cũng đã điền — [Inbound integrations](https://help.runzero.com/docs/integrations-inbound/) (bậc 1).

**Axonius (bậc 1, docs `updatedAt` 2026-10-14)**
- Axonius "automatically merges matching asset data from multiple sources into a single inventory record". **Explain Correlation** (Actions > Correlation): chọn 2 adapter, drawer hiển thị chuỗi từng bước, có thể đi qua bản ghi trung gian (ví dụ ForeScout ↔ ServiceNow qua Trend Micro Deep Security và Palo Alto Panorama), mỗi bước ghi ngày khớp; xem dạng Flow hoặc Text, xuất PDF; tag **Historical** cho adapter connection không còn hoạt động. Chỉ hỗ trợ Devices — [Exploring Asset Correlation](https://docs.axonius.com/docs/correlation-explainability) (bậc 1, 2026-10-14).
- **Explain Non-Correlation**: so từng identifier, kết quả mỗi bước là *Contradiction* (giá trị khác), *Missing Values*, hoặc *Match nhưng không đủ để ghép* — lý do: giá trị khớp yếu, giá trị không tin cậy bị đánh dấu khi chuẩn hoá, giá trị placeholder, quá ngắn, hoặc bị loại khi chuẩn hoá — cùng nguồn trên. **Nhận định:** đây là dạng "confidence" ngầm: identifier có trọng số/độ tin cậy, có danh sách placeholder bị loại (vd serial "To be filled by O.E.M.", MAC ảo).
- Quy tắc trong discovery cycle: thiết bị cùng IP và không có định danh duy nhất khác (không hostname, MAC...) thì được ghép — [Discovery Cycle](https://docs.axonius.com/pl/docs/discovery-cycle) (bậc 1; trích qua search).
- Release notes 10.0.0: các module Explain giúp xử lý thiết bị bị ghép sai hoặc trùng lặp bất ngờ — [Axonius Release Notes 10.0.0](https://docs.axonius.com/changelog/release-notes-1000) (bậc 1; trích qua search).
- Tách bản ghi: header Asset Profile có nút **Unlink Device**; dữ liệu nhập tay không tự ghép với adapter, cách sửa là đưa qua "Custom Data Asset Source" để chạy qua correlation engine như một adapter — [Asset Profile View](https://docs.axonius.com/docs/asset-profile-page) (bậc 1, 2026-10-14); [Converting Custom Data to Managed Assets](https://docs.axonius.com/docs/converting-custom-data-to-managed-assets) (bậc 1; trích qua search).
- Field: **Aggregated** (gộp từ mọi adapter), **Preferred** (giá trị được chọn làm "đại diện", ví dụ preferred OS, preferred model), **Specific** (chỉ thuộc một adapter, không gộp), **Common** — [Asset Profile View](https://docs.axonius.com/docs/asset-profile-page) (bậc 1).

**Truy vấn khoảng trống (unmanaged / thiếu agent)**
- Axonius: Query Wizard `OS: Type equals Windows` AND `CrowdStrike Agent ID does not exist` → thiết bị Windows thiếu agent kể cả khi chỉ AD hoặc adapter khác biết đến; biến thể "agent không hoạt động": có Agent ID nhưng CrowdStrike last seen > 30 ngày trong khi AD (hay nguồn khác) thấy trong 7 ngày; biến thể đa công cụ: không CrowdStrike và không Defender = noncompliant. Sau đó Enforcement Center: deploy agent qua SCCM/Tanium, báo owner qua email/Slack/Syslog, mở ticket ServiceNow/Jira/Zendesk, chạy lệnh/SSH scan; query lịch chạy liên tục — [How to Detect Gaps in Endpoint Protection with Axonius](https://www.axonius.com/blog/detect-gaps-endpoint-protection-axonius) (bậc 1 blog vendor, 2025-06-02).
- Axonius Devices page có cột **Adapter Connections** hiển thị icon các nguồn đã thấy thiết bị; AI Agent nhận câu hỏi kiểu "How many Windows servers are missing CrowdStrike?" và chuyển thành AQL — [Devices Page](https://docs.axonius.com/docs/devices-page) (bậc 1; trích qua search); [The Axonius AI Agent](https://docs.axonius.com/docs/the-axonius-ai-agent-copy) (bậc 1; trích qua search).
- runZero: có bảng source name/ID để truy vấn theo nguồn (vd CrowdStrike, SentinelOne) nhưng trang integration không có ví dụ query thiếu EDR — [Inbound integrations](https://help.runzero.com/docs/integrations-inbound/) (bậc 1).

### Nhận định
- Mẫu chung đáng học: (a) danh sách khoá có **thứ tự ưu tiên và tổ hợp** theo *lớp tài sản*; (b) **khoá chặn** (hai agent ID / UUID khác nhau thì không bao giờ ghép) để tránh ghép nhầm; (c) **cửa sổ thời gian cho IP** (runZero 3 ngày) vì IP động/DHCP; (d) **phạm vi ghép** (runZero theo site ≈ tenant/network zone) — áp dụng trực tiếp cho xung đột IP private giữa tenant: ghép chỉ trong (tenant, network segment); (e) **danh sách giá trị placeholder/không tin cậy** bị loại khỏi so khớp; (f) **giải thích ghép/không ghép** cho analyst; (g) **thứ tự ưu tiên nguồn theo trường** cấu hình được (Tenable Information Order) và giá trị "preferred" (Axonius).
- "Gap query" là chức năng cốt lõi của CAASM: thực chất là truy vấn *tồn tại/không tồn tại nguồn X* trên bản ghi đã hợp nhất, cộng điều kiện độ tươi (last seen theo từng nguồn). Với dữ liệu OCSF, cần lưu `last_seen` **theo từng nguồn** (per source/product) chứ không chỉ một last_seen tổng.

### Khoảng trống
- Không vendor nào trong nhóm công bố điểm confidence dạng số cho việc ghép; Axonius chỉ mô tả định tính.
- runZero không công bố nguồn nào thắng khi xung đột trường; Tenable mô tả mâu thuẫn giữa 2 trang về connector ưu tiên.
- Không tìm được docs công khai về unmerge/split ở Tenable, runZero (chỉ Axonius có "Unlink Device").
- Armis: docs sản phẩm cần đăng nhập; không tìm được mô tả công khai về khoá correlation (truy vấn "Armis Centrix device profile page..." chỉ ra tài liệu marketing).

## 2. Asset profile và user profile hiển thị gì

### Kết luận ngắn
CAASM (Axonius, Tenable) tổ chức profile quanh **bảng thuộc tính hợp nhất có provenance theo từng trường** (hover/mở rộng để xem giá trị của từng nguồn, xem raw JSON từng nguồn), cộng tab theo chủ đề (tags, notes, custom data, findings/weakness, relationships, enforcement/ticket, lịch sử snapshot). UEBA (Exabeam) tổ chức profile quanh **rủi ro theo thời gian**: thông tin directory → risk trend theo session → risk reasons (có công thức điểm, MITRE, độ tin cậy mô hình) → Smart Timeline của session. Mức chắc chắn: **cao** (docs bậc 1 mô tả chi tiết, ảnh đã kiểm tra).

### Phát hiện có nguồn
**Axonius Asset Profile (bậc 1, 2026-10-14)** — [Asset Profile View](https://docs.axonius.com/docs/asset-profile-page)
- Mở dạng **drawer** bên phải trang Assets (mũi tên duyệt qua kết quả query) hoặc trang đầy đủ ("Open Device Profile").
- Header: tiêu đề = Asset Profile ID (mặc định hostname với device / username với user, sửa được thành 1 trường chính + 2 trường phụ); hành động: Display by Date, Tag, Add Custom Field, Create Ticket, Enforce, Export Comparison Report, Unlink Device, Delete Device.
- Pane trái: Asset Profile Information (ảnh OS, preferred OS, preferred model, last seen; với user: ảnh, tên, title, department), bộ lọc Asset Fields (All / Aggregated / Preferred), Tags (ngày tạo/cập nhật/hết hạn), Tables (trường phức), **Adapter Connections** (từng kết nối nguồn, bấm mở bảng trường lọc Common/Specific, xem Table/XML/JSON thô), Custom Data.
- Bảng chính: mỗi hàng = tên trường, giá trị (vài giá trị đầu + số còn lại, hover tới 10), **cột Adapter Connections đã cung cấp**; mũi tên mở rộng để xem giá trị của **từng adapter**; hover tên trường thấy đường dẫn cú pháp (vd `specific_data.data.hostname`); tìm kiếm tự do, xuất CSV.
- Tab khác: Noncompliant CIS Controls, Location (bản đồ toà nhà), Dashboards, Enforcement Runs, Tickets, Notes, **Asset Investigation** (tài sản thay đổi thế nào theo thời gian), **Asset Graph** (quan hệ giữa tài sản), Display by Date (snapshot theo ngày).

**Tenable Exposure Management Asset Details (bậc 1, © 2026)** — [Asset Details](https://docs.tenable.com/exposure-management/Content/inventory/asset-details.htm)
- Header: tên tài sản, asset class, icon + số đếm theo exposure category; Export; **Summarize** (tóm tắt AI).
- Key Properties: Asset Class, Owner, Drivers, Location, Last Observed At; bảng Asset Information có **ACR** (Asset Criticality Rating 1–10) và **AES** (Asset Exposure Score 0–1000).
- Tab: Properties (gồm Asset Cluster Logic), **Connectors Details** (dữ liệu connector bên thứ ba + Show raw data), Accounts/Devices/Users/Device Accounts, Attack Paths, Weaknesses, Active Findings (Active/New/Resurfaced), Tags, Entitlements/Roles/Groups/Access (từ Entra ID/AD), Exposure Cards, **Relationships** (Source/Target), Software (version, CPE, port, file location), Exposure Signals (xu hướng 7 ngày).
- ACR có "ACR Key Drivers"; AES kết hợp VPR và ACR — [Host Asset Details](https://docs.tenable.com/vulnerability-management/Content/Explore/asset-details-hosts.htm) (bậc 1; trích qua search). Mâu thuẫn: một trang scoring cloud nói ACR không ảnh hưởng AES — [Cloud Security (CS) scoring](https://docs.tenable.com/quick-reference/scoring-explained/Content/cloud-security.htm) (bậc 1; trích qua search, chưa đối chiếu).

**runZero (bậc 1)** — [Understanding assets](https://help.runzero.com/docs/understanding-assets/)
- Trường tài sản: primary/secondary addresses, hostnames, OS, type, category, functions, hardware, MAC addresses, services, round trip time, detected by, alive status, first seen ("when it first identified an asset"), last seen ("most recent timestamp when an asset responded to a probe"), explorer, **outlier score 0–5** ("The more unusual properties an asset has, the higher its outlier score"); tài sản không thấy ở lần scan gần nhất bị đánh dấu offline.
- Trang Asset detail là "merged view of all metadata", gồm thuộc tính từ từng nguồn và services — [runZero 101 training](https://help.runzero.com/docs/training/) (bậc 1; trích qua search).

**Exabeam Advanced Analytics — User profile (bậc 1, © 2026)** — [Get to Know a User Profile](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153664-get-to-know-a-user-profile.html)
- General Information: họ tên, job title, location, label (executive, privileged), First/Last seen, Department, Manager (link), **Top peer group**, Last activity, Employee type, Last password reset, risk score của session gần nhất; nút Watchlist; comments.
- Data Insights: top 5 workstation và asset, zone và quốc gia kết nối, giờ hoạt động/không hoạt động.
- Active Incidents (Case Manager): ngày tạo, priority, status, assignee.
- User Risk Trend: điểm /100 theo 1 tuần/1 tháng/3 tháng/1 năm, mỗi điểm = 1 session (hoặc session rủi ro nhất trong tuần), màu xanh/vàng/đỏ, chọn điểm để xem Risk Reasons.
- Risk Reasons: mỗi sự kiện có mô tả, event type, **model confidence**, tag **MITRE ATT&CK**, công thức điểm "the anchor score multiplied by the anomaly factor"; link Event Details, Rule Definition, Data Insights.
- Smart Timeline của session: bộ đếm Reasons/Events/Alerts/Accounts/Assets/Locations/Score; tag VPN-in/within/out; lọc All Events hay chỉ anomaly; lịch tô đỏ/xanh/đen; Account Lockout Sequence (sequence rủi ro +50 điểm); hành động Export CSV, mở log SIEM, **Accept Session** (whitelist hành vi cho user/asset — "permanently whitelisted", không hoàn tác; khuyên tune rule thay vì accept).

**Exabeam — Asset page (bậc 1, © 2026)** — [Get Started with the Asset Page](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153684-get-started-with-the-asset-page.html)
- Asset Directory Information (từ LDAP hoặc analyst nhập): IP, labels, first/last seen, location, **Top User** (user đăng nhập nhiều nhất); badge cam = số alert bên thứ ba; góc phải = điểm sequence gần nhất.
- Asset Risk Trend, Asset Risk Reasons (hiện icon các user rủi ro cao đã tương tác với asset trong session), Asset Timeline (đếm Users, Assets đã kết nối, Zones...; lọc User Events/Asset Events/Security Alerts; Create Incident, mở log Splunk/QRadar/Elasticsearch). Timeline chỉ cập nhật sau khi xử lý dữ liệu như **host-to-IP mapping**, có thể trễ tới 2 giờ.

**Wazuh (bậc 1)** — [IT hygiene (current, ≈4.14)](https://documentation.wazuh.com/current/getting-started/use-cases/it-hygiene.html)
- Security operations > **IT Hygiene**: inventory từ module Syscollector của agent (phần cứng, OS, user account, package, process, service, network port, users, groups, browser extensions), gom vào index riêng trên Wazuh indexer, query qua Server API / Indexer API / Dev Tools; báo cáo theo từng endpoint. Bản 4.12 gọi module là "Inventory data", mỗi agent có DB riêng trên server — [System inventory 4.12](https://documentation.wazuh.com/4.12/user-manual/capabilities/system-inventory/index.html) (bậc 1). Inventory package dùng cho vulnerability detection.
- **Nhận định:** Wazuh là inventory *một nguồn* (agent), không có hợp nhất đa nguồn hay provenance; phù hợp làm một "adapter" chứ không phải asset store.

**Graylog Security 7.2 (bậc 1)** — [Risk Scores](https://go2docs.graylog.org/current/what_more_can_graylog_do_for_me/risk_scoring.htm)
- "An asset can be a user or a machine"; trang Security > Assets và asset sidebar hiển thị risk score tài sản (0–100). Không thấy mô tả layout chi tiết.

**Armis, Securonix:** xem Khoảng trống.

### Hình minh hoạ giao diện
Tất cả URL dưới đây đã `curl -sSIL` ngày 2026-11-03: HTTP 200 và content-type `image/png`/`image/jpeg`/`image/gif`. Mô tả lấy từ caption/văn bản quanh ảnh trong docs (chưa xem trực tiếp nội dung ảnh).

| vendor | màn hình | mô tả ngắn những gì ảnh thể hiện | image URL | trang nguồn | đã kiểm tra |
|---|---|---|---|---|---|
| Axonius | Asset Profile drawer | Drawer profile mở từ bảng Assets, header + pane trái + bảng trường hợp nhất | https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/img/asset_profile/AssetProfileDraweronAssetsPage.png | https://docs.axonius.com/docs/asset-profile-page | yes (png, 233 KB) |
| Axonius | Device Profile toàn trang | Trang device profile đầy đủ với tab và bảng field | https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/image-L4BUVALY.png | https://docs.axonius.com/docs/asset-profile-page | yes (png) |
| Axonius | Provenance theo trường | Tooltip liệt kê các adapter connection đã cung cấp một trường | https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/AdapterConnectionsHover.png | https://docs.axonius.com/docs/asset-profile-page | yes (png) |
| Axonius | Giá trị theo từng adapter | Mũi tên mở rộng một trường để xem giá trị mỗi adapter báo | https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/ClickArrow.png | https://docs.axonius.com/docs/asset-profile-page | yes (png) |
| Axonius | Bảng trường của 1 adapter connection | Bảng field của một nguồn, lọc Common/Specific | https://raw.githubusercontent.com/Axonius/ax-docs-pub/refs/heads/main/Images/image-WCD6PUF1.png | https://docs.axonius.com/docs/asset-profile-page | yes (png) |
| Axonius | Explain Correlation | Ví dụ chuỗi correlation giữa hai adapter qua các bản ghi trung gian | https://files.readme.io/5c066413acf4f063e0f6de1bd5b0bdeb1b864017af5625e8c4c7d45eeb1e0dc0-image.png | https://docs.axonius.com/docs/correlation-explainability | yes (png) |
| Axonius | Explain Correlation (ví dụ 2) | Ví dụ chuỗi correlation thứ hai | https://files.readme.io/81013cd96993ffc8478d80685f600e7183c567a194a357319ea33ddfca87dd50-image.png | https://docs.axonius.com/docs/correlation-explainability | yes (png) |
| Axonius | Menu Explain Non-Correlation | Đường dẫn More Actions > Correlation > Explain Non-Correlation | https://files.readme.io/db0967c7d6ec8c711af26fcc5d51ba8107c8c11adb53353cc25a16377456940b-image.png | https://docs.axonius.com/docs/correlation-explainability | yes (png) |
| Axonius | Gap query: agent ngừng check-in | Query thiết bị CrowdStrike lâu không check-in nhưng vẫn được nguồn khác thấy | https://images.contentstack.io/v3/assets/blt309b1de7d109902d/blt3f5b277a70d3e42e/6839c6eb116bcf82b521d22f/AX_DetectGaps_EP_Blog_Product01_1600x900_(1).png | https://www.axonius.com/blog/detect-gaps-endpoint-protection-axonius | yes (png) |
| Axonius | Gap query: thiếu agent (GIF) | Query theo chính sách lọc ra thiết bị thiếu agent bắt buộc | https://images.contentstack.io/v3/assets/blt309b1de7d109902d/bltf28ba2822cf7c080/6839c59821ef7a70ba183df9/crowdstrike_gif_1.gif | https://www.axonius.com/blog/detect-gaps-endpoint-protection-axonius | yes (gif) |
| Axonius | Enforcement Center | Chọn hành động tự động cho thiết bị thiếu agent | https://images.contentstack.io/v3/assets/blt309b1de7d109902d/blt9713599c5eed7530/6839c7b0fd6bfcf19698e91b/AX_DetectGaps_EP_Blog_Product02_1600x900_(1).png | https://www.axonius.com/blog/detect-gaps-endpoint-protection-axonius | yes (png) |
| Tenable | Asset Details tổng quan | Trang chi tiết tài sản: header, exposure category, tab | https://docs.tenable.com/exposure-management/Content/Resources/Images/Local/exposure-management/asset-details.png | https://docs.tenable.com/exposure-management/Content/inventory/asset-details.htm | yes (png) |
| Tenable | Asset Cluster Logic | Tiêu chí và giá trị khớp đã khiến các nguồn được ghép | https://docs.tenable.com/exposure-management/Content/Resources/Images/Local/exposure-management/asset-cluster-logic.png | https://docs.tenable.com/exposure-management/Content/inventory/asset-details.htm | yes (png) |
| Tenable | Information order | Thứ tự ưu tiên nguồn khi lấy giá trị thuộc tính | https://docs.tenable.com/exposure-management/Content/Resources/Images/Local/exposure-management/property-merge-order.png | https://docs.tenable.com/exposure-management/Content/inventory/asset-details.htm | yes (png) |
| Tenable | Connectors Details | Dữ liệu từ connector bên thứ ba + raw data | https://docs.tenable.com/exposure-management/Content/Resources/Images/Local/exposure-management/connector-details-tab.png | https://docs.tenable.com/exposure-management/Content/inventory/asset-details.htm | yes (png) |
| Exabeam | User General Information | Khối thông tin user: title, dept, manager, top peer group, labels, risk score | https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-cb33dad9-918f-2707-97ac-cedb4c8433a2.png | https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153664-get-to-know-a-user-profile.html | yes (png) |
| Exabeam | User Risk Trend | Biểu đồ điểm rủi ro theo session, màu theo mức | https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-4a912150-18a6-93cf-0ed4-0c7b6d454896.png | (như trên) | yes (png) |
| Exabeam | Risk Reasons | Danh sách sự kiện góp điểm, có model confidence, MITRE | https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-7bd36e84-66b7-6a0c-8c35-10f1f457dc6f.png | (như trên) | yes (png) |
| Exabeam | User Session Timeline | Smart Timeline: sự kiện theo thời gian + bộ đếm session | https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-3a81a24c-e971-dc45-e115-df496a9d151f.png | (như trên) | yes (png) |
| Exabeam | Asset Directory Information | Khối thông tin asset: IP, labels, first/last seen, top user, alert badge | https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-75d91051-bd0e-eada-5417-7f45601f4e11.jpg | https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153684-get-started-with-the-asset-page.html | yes (jpeg) |
| Exabeam | Asset Risk Trend | Biểu đồ điểm rủi ro session của asset | https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-1ce68030-0d9e-06aa-84db-834e3e01a364.jpg | (như trên) | yes (jpeg) |
| Exabeam | Asset Session Timeline | Timeline session của asset | https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/image/uuid-87f37b44-f22f-8781-eb7a-109609e730f1.png | (như trên) | yes (png) |
| Wazuh | IT Hygiene / Inventory data | Dashboard inventory của endpoint | https://documentation.wazuh.com/current/_images/inventory-data-dashboard1.png | https://documentation.wazuh.com/current/getting-started/use-cases/it-hygiene.html | yes (png; URL suy từ đường dẫn tương đối) |
| Wazuh | Vulnerability inventory | Dashboard inventory lỗ hổng | https://documentation.wazuh.com/current/_images/vulnerabilities-inventory-dashboard1.png | (như trên) | yes (png; URL suy từ đường dẫn tương đối) |

Mô tả bố cục bằng lời:
- **Axonius:** drawer/trang gồm header (tên + 2 trường phụ + thanh hành động Tag/Enforce/Ticket/Unlink), pane trái là "mục lục nguồn" (thông tin tóm tắt, chọn All/Aggregated/Preferred, tags, adapter connections, custom data), vùng chính là bảng field–value–sources có mở rộng theo nguồn; tab ngang cho CIS, Location, Dashboards, Enforcement Runs, Tickets, Notes, Asset Investigation, Asset Graph.
- **Tenable:** header (tên, class, đếm exposure theo category, Export, AI Summarize) → Key Properties (owner, location, last observed, ACR/AES) → hàng tab dài theo loại dữ liệu (properties/cluster logic, connectors, identity, attack paths, weaknesses, findings, software, relationships, exposure signals).
- **Exabeam:** bố cục dọc: khối directory/thông tin (trái) + điểm hiện tại (phải) → risk trend (đồ thị chấm theo session) → risk reasons (danh sách có công thức điểm) → nút "Go to timeline" sang Smart Timeline (bộ đếm trên cùng, sự kiện bên trái, chi tiết rủi ro bên phải).

### Nhận định
- Khác biệt thiết kế cần kết hợp cho SOC: CAASM trả lời "tài sản này là gì, ai biết về nó, thiếu gì" (provenance theo trường, gap); UEBA trả lời "nó đang làm gì bất thường, vì sao điểm cao" (risk trend + reasons có thể giải thích + timeline). Profile cho SOC nên có cả hai lớp: header/tóm tắt + provenance (CAASM) và rủi ro/timeline (UEBA).
- "Accept session" của Exabeam vĩnh viễn, không hoàn tác — **bài học ngược:** nếu xây suppression/allow-list theo asset, cần có hạn dùng, audit và hoàn tác (Axonius tags có ngày hết hạn).

### Khoảng trống
- **Armis:** không có docs công khai về layout device profile; chỉ có tài liệu marketing (risk score dựa trên phần mềm chưa vá, exploit phần cứng, lỗ hổng; baseline "known good" của thiết bị) — [Armis Centrix for Medical Device Security](https://www.armis.com/solutions/vulnerability-and-threat-monitoring/) (bậc 1 marketing; trích qua search). Không có ảnh đã kiểm tra.
- **runZero:** không tìm được ảnh chụp trang asset detail trên docs; ảnh duy nhất là sơ đồ phân loại https://www.runzero.com/img/docs/img/asset-classification-4-9.jpg (chưa curl).
- **Securonix:** `legacy-documentation.securonix.com` bị chặn trong network của session (cần cho phép host này); documentation.securonix.com không ra trong kết quả search. Không có ảnh.
- **Exabeam New-Scale Threat Center:** không tìm được trang "entity details" cụ thể trong Threat Center.
- Security Onion và OpenSearch Security Analytics: không kịp tra (hết ngân sách tool call); chưa có bằng chứng về tính năng asset/entity.

## 3. UEBA baseline per user/asset, peer group, và ngữ cảnh thay đổi điểm rủi ro

### Kết luận ngắn
Exabeam là mô hình rõ nhất: điểm rủi ro **cộng dồn theo session** (≈1 ngày, đóng sau 5 giờ không hoạt động hoặc 24 giờ), mỗi rule = anchor score × anomaly factor, ngưỡng notable mặc định 90; ngữ cảnh tài sản/user (executive, service account, server vs workstation, asset group, peer group) làm *tăng/giảm điểm* hoặc *đổi cách mô hình hoá*. Graylog là mô hình đơn giản cho SIEM mã nguồn mở: event risk = f(severity log, priority rule, priority asset), asset risk = điểm event mở cao nhất, khuếch đại khi nhiều rule + lỗ hổng. Mức chắc chắn: **trung bình–cao** cho Exabeam/Graylog (docs bậc 1, nhưng không có công thức đầy đủ); **thấp** cho Securonix (chỉ nguồn thứ cấp).

### Phát hiện có nguồn
**Exabeam**
- Session: sự kiện gán cho user trong khung thời gian, đóng session sau 5 giờ không hoạt động hoặc 24 giờ tối đa; mỗi lần rule bắn điểm cộng vào session; notable user khi vượt ngưỡng, mặc định 90; điểm session của asset được cộng vào session của user — tổng hợp từ docs Advanced Analytics (bậc 1; trích qua search ["Exabeam Smart Timelines..."], trang gốc [User guide index](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/index-en.html)).
- Công thức điểm từng risk reason: "the anchor score multiplied by the anomaly factor"; sequence lockout rủi ro +50 — [Get to Know a User Profile](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153664-get-to-know-a-user-profile.html) (bậc 1, © 2026).
- Entity Analytics (add-on có license): host/IP có điểm riêng; asset có session score ≥ 90 hiện là Notable Assets; "Asset criticality and threat intelligence information can also be factored into the risk analysis" — [Entity Analytics](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153683-entity-analytics.html) (bậc 1; trích qua search).
- Ngữ cảnh tài sản: lấy asset từ LDAP và "categorizes them as servers or workstations based on the OS property or the Organizational Units"; classifier liên tục gán nhãn theo hành vi; **asset group** (vd Exchange cân bằng tải) được mô hình như một thực thể để "reduces the amount of false positives"; network zones nhập CSV/tay — [What are Assets & Networks](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/administration-guide/set-up-authentication-and-access-control/what-are-assets---networks-.html) (bậc 1, © 2026).
- Executive: anomaly của non-executive truy cập workstation của executive bị chấm cao hơn; service account đăng nhập interactive vào ứng dụng bị cộng điểm; context table Executive Users, Service Accounts — docs admin Exabeam (bậc 1; trích qua search, vd [what are accounts & groups](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/administration-guide/set-up-authentication-and-access-control/what-are-accounts---groups-.html)). Không tìm được giá trị điểm cụ thể.
- Peer group: khởi điểm từ thuộc tính AD (department, division, title, manager) nhưng các trường này thường cũ/thiếu (độ phủ 50–90% mỗi thuộc tính); user thuộc nhiều peer group với **degree of membership** tính từ khoảng cách hành vi; nhóm có độ gắn kết (cohesion) thấp bị loại; hành động peers hay làm → giảm điểm, peers hiếm làm → tăng điểm; nhóm nhỏ dễ báo động hơn — [Who Do I Belong To? Dynamic Peer Analysis for UEBA Explained](https://www.exabeam.com/blog/ueba/who-do-i-belong-to-dynamic-peer-analysis-for-ueba-explained/) (bậc 1 blog vendor, Derek Lin, 2016-09-20 — cũ, implementation hiện tại có thể khác). User profile hiện "Top peer group" = nhóm có liên kết mạnh nhất theo cohesiveness — [User Profile](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/user-guide/153664-get-to-know-a-user-profile.html) (bậc 1).
- Threat Center (New-Scale): detection correlation rule có điểm theo severity (Critical 100, High 75, Medium 50, Low 25, None 0); detection Advanced Analytics = tổng điểm rule; điểm case/alert = tổng điểm detection; priority mặc định Critical ≥ 75, High 50–<75, Medium 25–<50, Low < 25; đổi priority tay không đổi điểm — [Risk scores in Security Operations portfolio and Fusion licenses](https://docs.exabeam.com/en/threat-center/all/threat-center-guide/get-started-with-threat-center/threat-center-risk-score/risk-scores-in-the-exabeam-security-operations-portfolio-and-fusion-licenses.html) (bậc 1, © 2026). Trang này không nói về criticality tài sản.

**Graylog Security 7.2** — [Risk Scores](https://go2docs.graylog.org/current/what_more_can_graylog_do_for_me/risk_scoring.htm) (bậc 1)
- Event risk score lấy từ: message severity (`alert_severity_level` theo GIM, trung bình nếu là event aggregation), event priority (đặt trong event definition; Sigma mặc định medium), asset priority (đặt theo asset type ở Security > Assets). **Không có asset liên kết thì không tính event risk score.**
- Asset risk score (user hoặc machine): base = event risk mở cao nhất, **khuếch đại** khi nhiều event definition khác nhau gắn vào asset, cộng lỗ hổng từ scanner (chỉ machine); chuẩn hoá 0–100; tính lại khi event mở/đóng; không còn event mở → 0.

**Securonix (bậc 2–3, gián tiếp)**
- Theo docs SNYPR 6.4 cũ (qua search): "High Risk User scoring is based on peer group behavior"; khi một thành viên peer group hành xử khác peers thì điểm tăng; Threat Model tăng điểm policy theo category — [View High Risk Users (6.4)](https://legacy-documentation.securonix.com/onlinedoc/Content/6.4%20On-Prem/Content/Apps%20and%20Add%20ons/Access%20Analytics/6.4%20Access%20Outliers_View%20High%20Risk%20Users.htm) (bậc 1 nhưng **không mở được**, chỉ đọc snippet); [Threat Modeler 6.0](https://documentation.securonix.com/onlinedoc/Content/6.0/Content/SNYPR%206.0/Integration%20Guide/6.0%20Threat%20Modeler.htm) (bậc 1, snippet).
- Ví dụ violation peer: "Abnormal number of emails sent to external domain as compared to peer members" — [Securonix Unified Defense SIEM CDF (ThreatQ)](https://helpcenter.threatq.com/Integration_Documentation/cdf/Securonix_Unified_Defense_SIEM_CDF.htm) (bậc 2, snippet). API peer group trả `name` và `criticality` — [FortiSOAR Securonix SNYPR connector](https://docs.fortinet.com/document/fortisoar/2.3.0/securonix-snypr/230/securonix-snypr-v2-3-0) (bậc 2, snippet). **Nhận định:** peer group ở Securonix có thuộc tính criticality riêng.

**Tham chiếu so sánh (ngoài nhóm, chỉ để đối chiếu):** Microsoft Sentinel UEBA có investigation priority score 0–10 và anomaly score 0–1, kết hợp peer analysis — [Microsoft Sentinel UEBA](https://learn.microsoft.com/en-in/azUre/sentinel/identify-threats-with-entity-behavior-analytics) (bậc 1; snippet). ManageEngine Log360: peer có hành vi tương tự làm *giảm* confidence và điểm của anomaly — [ManageEngine UEBA risk scoring](https://www.manageengine.com/log-management/ueba/help/risk-scoring.html) (bậc 1; snippet).

### Nhận định
- Hai cách đưa ngữ cảnh tài sản vào điểm: (1) **nhân/cộng trực tiếp** vào điểm event (Graylog asset priority; Exabeam executive asset); (2) **đổi mô hình baseline** (Exabeam asset group gộp server cùng chức năng, phân loại server/workstation, peer group) — cách (2) giảm nhiễu ở gốc, cách (1) chỉ xếp hạng lại.
- Quy tắc "không có asset thì không có risk score" (Graylog) cho thấy entity resolution là điều kiện tiên quyết cho risk-based alerting; với OCSF cần resolve `device`/`user` trong mỗi event về asset ID ổn định của tenant trước khi chấm điểm.
- Peer group từ HR/AD thường thiếu (50–90% độ phủ theo Exabeam 2016) → nên cho phép peer group động hoặc nhóm thủ công, và hiển thị "top peer group" cùng lý do.

### Khoảng trống
- Không có công thức đầy đủ hay trọng số criticality cụ thể ở Exabeam/Graylog.
- Securonix: không đọc được docs chính thức (host legacy bị chặn trong session; cần cho phép `legacy-documentation.securonix.com` nếu muốn kiểm chứng).
- Không có số liệu đo hiệu quả giảm nhiễu (chỉ tuyên bố "reduces false positives" của vendor).
- Armis: baseline hành vi thiết bị chỉ có ở tài liệu marketing.

## Truy vấn đã chạy
- Axonius asset profile page "preferred fields" adapter connections (standard)
- Axonius correlation logic adapters devices same asset docs (standard)
- runZero asset merge fingerprinting docs inventory (standard)
- Axonius query devices missing EDR agent "adapter connections" count (standard)
- Exabeam Smart Timelines user asset timeline session risk score peer group (standard)
- Securonix UEBA peer group behavior profile risk score user documentation (standard)
- documentation.securonix.com peer group "violation" risk score entity (extended)
- Wazuh IT hygiene dashboard syscollector inventory documentation 4.12 (standard)
- Armis Centrix device profile page "boundaries" risk factors device details screenshot (standard)
- Tenable One inventory asset details page "Asset Exposure Score" "Asset Criticality Rating" docs (standard)
- Tenable Exposure Management asset deduplication third-party connectors merge "same asset" (standard)
- runZero asset details page attributes sources "outlier score" docs (standard)
- Exabeam New-Scale Threat Center entity details user asset risk score Advanced Analytics docs (standard)
- Securonix "peer group" "behavior profile" SNYPR documentation users dynamic peer groups (standard)
- Exabeam context tables asset labels "is_executive" "service account" risk score modifier rules (standard)
- Graylog Security assets risk score asset priority documentation (standard)
- documentation.securonix.com Unified Defense SIEM "peer" "spotter" user profile entity view (extended)
