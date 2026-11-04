# Trước detection: asset profile tăng chất lượng phát hiện

Phạm vi: câu hỏi phụ 5 của brief. Notes này không nhắc lại ma trận urgency, risk multiplier, context-aware analytics có validity interval, asset group/peer group của Exabeam và silent-host monitoring, vì report `2026-11-03-asset-profile-vendor-giao-dien-soc` đã có các phần đó. Notes chỉ ghi phần mới: cơ chế **trong chính rule** (phạm vi, ngoại lệ, baseline, điều kiện lỗ hổng, coverage) và chỗ join ngữ cảnh.

Quy ước: "đã mở" nghĩa là đã đọc trang bằng WebFetch. "Trích đoạn search" nghĩa là trang không mở được (403) hoặc chưa mở, nên con số chỉ là manh mối.

## 5a. Scoping và tuning rule theo role/class của asset

### Kết luận ngắn
Mọi nền tảng lớn đều có chỗ để rule tham chiếu thuộc tính asset: thu hẹp rule về một lớp (DC, server) hoặc loại trừ một lớp (scanner, admin). Cách làm khác nhau. Sigma để ngoại lệ trong file filter riêng. Sentinel join watchlist. Google join entity graph trong rule. Defender có cột `DeviceType`/`DeviceRoles` ngay trong `DeviceInfo`. ATT&CK v18 còn đưa "mutable elements" vào analytic như điểm tuning theo ngữ cảnh. Mức chắc chắn **cao** về cơ chế (docs chính thức). Chưa có số liệu hiệu quả.

### Phát hiện có nguồn
- **Sigma filters** là file riêng chứa exclusion/inclusion cho rule, để rule gốc không đổi và cập nhật từ rule pack dễ hơn. Filter dùng khối `filter` thay cho `detection`, có `logsource` (chỉ áp khi khớp logsource của rule), `filter.rules` (danh sách id/tên rule, hoặc `any` để áp cho mọi rule cùng logsource), `selection` và `condition` (`not selection` để loại trừ, hoặc chỉ `selection` để giới hạn rule vào sự kiện khớp). Khi convert, điều kiện filter được nối vào điều kiện rule, kiểu `selection and (filter)`. Ví dụ trong docs: loại trừ user `adm_*` khỏi rule `proc_creation_win_sc_create_service`, hoặc loại trừ host tên "DC-". Chạy bằng `sigma convert --filter` — [Sigma Filters](https://sigmahq.io/docs/meta/filters.html) (bậc 1, không rõ ngày; đã mở)
- **Sigma correlation rules spec 2.1.0 (2025-08-02)** có các kiểu `event_count`, `value_count`, `temporal`, `temporal_ordered`, cùng `value_sum`/`value_avg`/`value_percentile` thêm ở 2.1.0. Riêng ba kiểu sau không có trong danh sách allowed values, nên spec tự mâu thuẫn. `group-by` (bắt buộc, nhiều field ghép AND) và `timespan` là bắt buộc. Correlation có thể tham chiếu correlation khác ("chain multiple correlations together"). `generate` quyết định có xuất rule con thành rule độc lập hay không — [sigma-correlation-rules-specification.md](https://github.com/SigmaHQ/sigma-specification/blob/main/specification/sigma-correlation-rules-specification.md) (bậc 1, 2025-08-02; đã mở)
- **Sentinel watchlist templates** (preview) có schema cố định:
  - High Value Assets: `Asset Type` (Device, Azure resource, AWS resource, URL, SPO, File share, Other), `Asset Id`, `Asset Name`, `Asset FQDN`, `IP Address`, `Tags`.
  - VIP Users: UPN bắt buộc, có SID/Object Id và `Tags`.
  - Network Addresses: `IP Subnet`, `Range Name` (ví dụ `DMZ`), `Tags`.
  - Terminated Employees: có `UserState` (Notified/Terminated) và `Termination date`.
  - Identity Correlation: gắn tài khoản thường với `Associated Privileged Account`.
  - Service Accounts: `Service Principal Name` cùng owner (UPN bắt buộc).
  — [Schemas for watchlist templates](https://learn.microsoft.com/en-us/azure/sentinel/watchlist-schemas) (bậc 1, ms.date 2023-12-15, cập nhật 2026-06-28; đã mở)
- Microsoft liệt kê "Reduce alert fatigue. Create allowlists to suppress alerts from a group of users, like users from authorized IP addresses…" là kịch bản chính của watchlist. Rule dùng `_GetWatchlist('alias')` với `join`/`lookup`/`in` trên cột `SearchKey`. Giới hạn: tối đa 10 triệu item active mỗi workspace, "Watchlists refresh every 12 days", bảng `Watchlist` giữ 28 ngày, upload local 3,8 MB. Không quản lý được watchlist xuyên workspace qua Azure Lighthouse. Docs cũng cảnh báo `_GetWatchlist()` có thể trả rỗng hoặc thiếu nếu time range của query hẹp hơn chu kỳ refresh — [Use watchlists…](https://learn.microsoft.com/en-us/azure/sentinel/watchlists) (bậc 1, 2026-06-23; đã mở)
- **Defender XDR `DeviceInfo`** có sẵn các cột cho rule scoping:
  - `DeviceCategory` (Endpoint, Network device, IoT, Unknown) và `DeviceType` (workstation, server, mobile, printer…).
  - `IsInternetFacing`, `ExposureLevel` (Low/Medium/High), `AssetValue` (Low/Normal/High).
  - `DeviceManualTags`, `DeviceDynamicTags`, `MachineGroup`.
  - `SensorHealthState`, `OnboardingStatus`, `DiscoverySources` ("Products or services that have seen or reported the device, including when they last reported it").
  - `IsTransient`.
  - **`DeviceRoles`**: "Device roles and characteristics… Includes roles identified by the system or defined by users, confidence levels, and the last time each role was seen".

  Bảng "updated continuously, and all updates contain the full current device data", nên muốn lấy trạng thái mới nhất phải `arg_max` theo DeviceId — [DeviceInfo table](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-deviceinfo-table) (bậc 1, ms.date 2026-07-27; đã mở)
- `ExposureGraphNodes` (Exposure Management) chứa node device/identity/cloud resource. `NodeProperties` là JSON "unstructured", có insight như internet-exposed hay vulnerable to RCE. Bảng chỉ có dữ liệu khi đã triển khai dịch vụ Defender tương ứng — [ExposureGraphNodes](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-exposuregraphnodes-table) (bậc 1, 2025-03-28; đã mở). Ví dụ cộng đồng chủ yếu lọc `criticalityLevel` của identity. Chưa thấy ví dụ chính thức join với DeviceInfo trong custom detection (trích đoạn search, kqlsearch.com, bậc 3).
- Dynamic tag của Defender (asset rule management) tự gắn và gỡ tag theo tên, domain, OS, internet-facing, onboarding status, và "refresh roughly hourly" (trích đoạn search của [configure-asset-rules](https://learn.microsoft.com/en-gb/defender-xdr/configure-asset-rules), bậc 1, chưa mở).
- **Google SecOps YARA-L** join event với entity graph bằng biến chung, ví dụ `$u.udm.principal.hostname = $hostname` và `$asset_context.graph.entity.hostname = $hostname`. Rule lấy `$asset_context.graph.entity.asset.vulnerabilities.severity` để cộng điểm trong `outcome`, rồi `condition: $risk_score > 50 and not arrays.contains($asset_id_list, "id_1234")` (loại trừ asset theo id) — [Default detection rules](https://docs.cloud.google.com/chronicle/docs/detection/default-rules) (bậc 1, không rõ ngày; đã mở)
- Context-aware analytics của Google lọc được theo quan hệ (`$e1.graph.entity.relations.relationship = "OWNS"`), theo role của resource (`resource.attribute.roles.type`) và theo `graph.metadata.entity_type`. Giới hạn: "It's impossible to have a rule that only uses Entity". Rule multi-event phải có UDM event. "Entity context cannot be used as the pivot for a sliding window". Outcome variable bị bỏ qua khi dedup — [Context-aware analytics](https://docs.cloud.google.com/chronicle/docs/detection/context-aware-analytics) (bậc 1, không rõ ngày; đã mở)
- **ATT&CK v18 analytic có "mutable elements"**, là các điểm tuning theo môi trường. Ví dụ AN0001 (DET0001, metadata API trên IaaS) có `TimeWindow`, `UserContext` ("Tunes detection based on which roles are expected to access metadata APIs, such as root or service accounts") và `RequestHeaderMatch` — [DET0001](https://attack.mitre.org/detectionstrategies/DET0001/) (bậc 1, v18 2025-10; đã mở)
- **Splunk ES asset lookup** có các field boolean `is_expected`, `should_timesync`, `should_update`, `requires_av` cùng `category`, `pci_domain` (wireless/trust/untrust/cardholder/dmz), `bunit`. `asset_tag` mặc định sinh từ `category, pci_domain, is_expected, should_timesync, should_update, requires_av, bunit` — [Asset and identity fields after processing, ES 7.3](https://help.splunk.com/en/splunk-enterprise-security-7/administer/7.3/asset-and-identity-validation/asset-and-identity-fields-after-processing-in-splunk-enterprise-security) (bậc 1, không rõ ngày; đã mở). Theo trích đoạn search của docs ES 4.5.0 (trang trả 403), `is_expected = true` làm correlation search "Expected Host Not Reporting" chạy adaptive response khi asset ngừng gửi event. Đây là ví dụ thuộc tính profile kích hoạt trực tiếp một detection — [AssetandIdentityLookupReference 4.5.0](https://docs.splunk.com/Documentation/ES/4.5.0/User/AssetandIdentityLookupReference) (bậc 1, phiên bản cũ; chưa mở)
- **Splunk entity zones** (`cim_entity_zone`): khi bật, khoá IP được ghép với zone, nên một IP có thể tồn tại ở nhiều zone và `ip`/`nt_host` không bị merge xuyên zone. Subnet directory nhận cùng subnet một lần cho mỗi zone. Entry không có zone chỉ enrich record có zone null (trích đoạn search của [Entity zones in Exposure Analytics 8.6](https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.6/exposure-analytics/entity-zones-in-exposure-analytics), bậc 1, chưa mở). Field chỉ không được xử lý khi entity zones tắt — docs 8.3 (bậc 1).

### Nhận định
- **Nhận định:** có ba kiểu scoping. (1) **Inclusion scope**: rule chỉ chạy trên một lớp, ví dụ "DCSync chỉ có nghĩa khi đích là DC", "service mới trên server". (2) **Exclusion theo lớp**: scanner, jump host, build server, admin. (3) **Tham số theo ngữ cảnh**: kiểu "mutable element" của ATT&CK (UserContext, TimeWindow). Sigma filter là mẫu tốt để giữ (2) tách khỏi nội dung rule. Profile nên xuất các lớp này thành **tập asset có tên**, ví dụ `role:domain-controller`, `role:vuln-scanner`, mà rule/filter tham chiếu, thay vì để rule chứa danh sách IP/host. Khi profile đổi, phạm vi rule tự đổi theo.
- **Nhận định:** `DeviceRoles` của Defender (role + confidence + last seen) là mẫu nên chép. Role suy diễn phải có độ tin và thời điểm thấy lần cuối, để rule biết chỉ scope theo role có confidence đủ cao. Khi role cũ quá hạn, asset tự rời khỏi phạm vi.
- **Nhận định:** đa tenant cần khoá theo zone/tenant như entity zones của Splunk. Nếu không, rule scope "DMZ" của tenant A sẽ áp nhầm sang IP trùng của tenant B.
- **Nhận định:** watchlist kiểu Sentinel là bảng tĩnh, refresh theo chu kỳ dài. Kho entity của sản phẩm nên thay nó bằng lookup sinh tự động từ profile, có version và validity interval.

### Khoảng trống
- Không tìm được số liệu (vendor hay độc lập) đo mức giảm FP khi scope rule theo role.
- Docs Elastic về exceptions + value lists và về điều kiện rule theo `host.asset.criticality` chưa được mở trong lượt này.
- Spec Sigma filter có version riêng hay không: trang docs không nói (link sang spec GitHub, chưa mở).

## 5b. Baseline và allowlist kỳ vọng theo role → detection lệch chuẩn

### Kết luận ngắn
"Lần đầu thấy" là primitive phổ biến nhất và có tham số rõ. Elastic new terms dùng 1–3 field và history window tự chọn (ví dụ 14 hoặc 30 ngày). Microsoft UEBA có khoảng 40 cờ FirstTime/Uncommon theo user, peer và tenant, mỗi cờ có baseline cố định từ 5 đến 180 ngày. Baseline theo **host** và theo **role của host** ít được chuẩn hoá hơn: Elastic ML rare-process-by-host có, còn Microsoft UEBA chủ yếu xoay quanh user. Mức chắc chắn **cao** về cơ chế. Số liệu hiệu quả **thấp** (chỉ có một preprint đo alert rate).

### Phát hiện có nguồn
- **Elastic new terms rule**: "Fires when a value (or combination of up to three values) has never appeared in a configurable history window". Ví dụ trong docs: `process.executable` chưa thấy trong 30 ngày, và cặp `user.name` + `host.name` chưa thấy cùng nhau trong 14 ngày (first-time logon vào host). Cảnh báo: "A window that is too short leads to excessive false positives". Window 1–7 ngày dễ báo những tổ hợp hiếm nhưng đã biết. Nên dùng window tương đối (`now-30d`), không dùng ngày tuyệt đối. Docs không nêu giới hạn tối đa của window — [New terms rule](https://www.elastic.co/docs/solutions/security/detect-and-alert/new-terms) (bậc 1, không rõ ngày; đã mở)
- **Microsoft Sentinel UEBA `BehaviorAnalytics.ActivityInsights`**: mỗi nhóm có 5 cờ theo các trục user / user-uncommon / peers / tenant-first / tenant-uncommon, mỗi cờ một baseline cố định. Ví dụ:
  - `FirstTimeUserPerformedAction` 180 ngày, `ActionUncommonlyPerformedByUser` 10 ngày, `ActionUncommonlyPerformedAmongPeers` 180 ngày;
  - `FirstTimeUserLoggedOnToDevice` 180 ngày ("The destination device was connected to for the first time by the user"), `FirstTimeUserConnectedFromDevice` 30 ngày, `FirstTimeDeviceObservedInTenant` 30 ngày, `DeviceUncommonlyUsedAmongPeers` 180 ngày, `DeviceFamilyUncommonlyUsedInTenant` 30 ngày;
  - `FirstTimeUserUsedApp` 180 ngày, `FirstTimeUserConnectedFromCountry` 90 ngày;
  - `UncommonHighVolumeOfOperations` 7 ngày, `UnusualNumberOfDevicesAdded` 5 ngày.

  Baseline "dynamically compiled each time it's used". Bảng có `InvestigationPriority` 0–10. `UsersInsights` có `IsDormantAccount` (180 ngày), `IsNewAccount` (30 ngày), `IsLocalAdmin`, `BlastRadius` (cần field Manager trong Entra). Đầu vào device-side gồm `DeviceLogonEvents`, SecurityEvent 4624/4625/4648/4672/4688, và CommonSecurityLog của Check Point/Fortinet/Zscaler. Chỉ dùng được event có `Computer` hợp lệ cho detection theo device — [UEBA reference](https://learn.microsoft.com/en-us/azure/sentinel/ueba-reference) (bậc 1, ms.date 2025-08-28, cập nhật 2026-08-05; đã mở)
- `IdentityInfo` của UEBA full-resync 14 ngày một lần, thay đổi được ghi lại trong 15–30 phút, giữ 30 ngày. `GroupMembership` chỉ lấy tối đa 500 group mỗi user — cùng nguồn trên.
- **Elastic ML** (trích đoạn search, docs 7.9 cũ): job `rare_process_by_host_windows_ecs` / `rare_process_by_host_linux_ecs` coi process là hiếm "when they only run occasionally as compared with other processes running on the host". `linux_anomalous_process_all_hosts_ecs` tìm process hiếm trên toàn fleet. Rule mới hơn "Unusual Process Spawned by a Host" dùng job `problem_child_rare_process_by_host` và cần integration LotL Attack Detection — [Prebuilt job reference 7.9](https://www.elastic.co/guide/en/security/7.9/prebuilt-ml-jobs.html), [detection-rules explorer](https://elastic.github.io/detection-rules-explorer/rules/56004189-4e69-4a39-b4a9-195329d226e9) (bậc 1, cũ; chưa mở)
- **Google SecOps**: rule có thể dùng role của resource và quan hệ entity (xem 5a). Report trước đã ghi lại prevalence. Trang data enrichment không nói về prevalence. `first_seen_time`/`last_seen_time` trên trang đó là metadata file lấy từ VirusTotal, không phải baseline nội bộ — [Data enrichment](https://docs.cloud.google.com/chronicle/docs/event-processing/data-enrichment) (bậc 1; đã mở)
- **Số liệu độc lập (preprint)**: Hawryluk và cộng sự (2022) mô hình peer group cho sự kiện xác thực Windows bằng Bayes phân tầng. Peer group được tạo bằng phương pháp data-driven và so sánh với nhóm theo hồ sơ HR. Bài báo "empirical evidence of alert reduction" trên dữ liệu một doanh nghiệp lớn. Theo trích đoạn search, alert rate khoảng 0,57–0,62% trên 439.689 quan sát test — [arXiv 2209.09769](https://arxiv.org/abs/2209.09769) (bậc 1 preprint, 2022-09; đã mở abstract, con số alert rate chưa đối chiếu trong full text)

### Nhận định
- **Nhận định:** các detection lệch chuẩn mà brief nêu đều quy về new-terms hoặc rare trên một **khoá tổ hợp có asset**:
  - dịch vụ mới lắng nghe: (`device`, `port`, `service`);
  - phần mềm mới trên server: (`device`, `product`);
  - binary/cha–con hiếm: (`device` hoặc `role`, `parent`, `child`);
  - first-time logon: (`user`, `device`);
  - đích outbound mới: (`device`, `dst domain/ASN`).

  Profile cần giữ sẵn các **tập "đã biết" có first_seen/last_seen**. Nhờ vậy rule chỉ cần so với profile, không phải quét lại 14–180 ngày log mỗi lần chạy. Đây cũng là dữ liệu "dịch vụ/ứng dụng đang dùng" của case 1–4.
- **Nhận định:** baseline theo **role/peer của host** quan trọng hơn baseline từng host đơn lẻ, vì host mới sẽ báo mọi thứ là "lần đầu". Phải có cơ chế **cold-start**: host mới dùng baseline của role/peer, hoặc tắt cờ "first time" trong N ngày đầu. UEBA của Microsoft có cờ `FirstTimeDeviceObservedInTenant` chính để nhận diện trường hợp này.
- **Nhận định:** kho entity cần ghi rõ baseline window cho từng loại tập (Microsoft dùng 10/30/90/180 ngày tuỳ loại). Retention log của tenant phải dài hơn window. Nếu không, baseline bị cắt và FP tăng.

### Khoảng trống
- Exabeam và Securonix có peer group cho host/asset (không chỉ user), nhưng chưa đọc docs hiện hành. Report trước đã có phần peer user của Exabeam.
- Không có số liệu độc lập so sánh baseline per-host với baseline per-role.
- Chưa xác minh danh sách job ML hiện hành của Elastic (9.x). Các ID trên lấy từ docs 7.x.

## 5c. Detection có điều kiện theo lỗ hổng/exposure

### Kết luận ngắn
Mẫu lâu đời và rõ nhất là "impact level" của Cisco Secure Firewall (Firepower). Nó ghép intrusion event với network map (host, service đang mở, OS) và lỗ hổng đã map, ra 5 mức từ Vulnerable đến Unknown. Mẫu này cho thấy chính xác asset profile cần những gì: host đã biết, port/service đang mở, OS/version và lỗ hổng. Google YARA-L kéo được severity lỗ hổng của asset vào điểm của rule. QRadar đưa asset (weight, lỗ hổng) vào magnitude, nhưng chưa có docs IBM gốc mô tả công thức. Mức chắc chắn **cao** với Cisco/Google, **thấp** với QRadar.

### Phát hiện có nguồn
- **Cisco impact levels** — [Intrusion Event Impact Levels](https://docs.manage.security.cisco.com/r_intrusion_event_impact_levels.html) (bậc 1, không rõ ngày; đã mở):
  - **Vulnerable** (đỏ, level 1): host nguồn hoặc đích "is in the network map, and a vulnerability is mapped to the host", hoặc host có thể đã bị malware xâm nhập.
  - **Potentially Vulnerable** (cam): host có trong map, và với traffic theo port thì "the port is running a server application protocol"; với traffic không theo port thì host dùng giao thức đó.
  - **Currently Not Vulnerable** (vàng): port không mở, hoặc host không dùng giao thức đó.
  - **Unknown Target** (xanh): host nằm trong mạng được giám sát nhưng không có trong network map.
  - **Unknown** (xám): cả hai host đều ngoài mạng do network discovery giám sát.
  - Màu là "the correlation between intrusion data, network discovery data, and vulnerability information". Host thêm vào map từ NetFlow không có OS, nên "the system cannot assign Vulnerable" và phải đặt OS thủ công qua host input.
- Theo trích đoạn search: nếu tắt cả hai tuỳ chọn vulnerability mapping thì event không bao giờ được đánh Vulnerable — [Network Discovery Vulnerability Impact Assessment Options](https://docs.manage.security.cisco.com/cdfmc/r_network_discovery_vulnerability_impact_assessment.html) (bậc 1, chưa mở). Một bài support của Cisco cho biết Impact=Unknown trên FMC 7.7 là do IP nằm ngoài phạm vi discovery policy — [Troubleshoot FMC intrusion events (PDF)](https://www.cisco.com/c/en/us/support/docs/security/secure-firewall-management-center/225934-troubleshoot-fmc-intrusion-events.pdf) (bậc 1, chưa mở)
- **Google SecOps**: rule mẫu đặt `$severity = $asset_context.graph.entity.asset.vulnerabilities.severity`, rồi trong `outcome` cộng 10/5/1 điểm cho HIGH/MEDIUM/LOW vào `$risk_score` — [Default detection rules](https://docs.cloud.google.com/chronicle/docs/detection/default-rules) (bậc 1; đã mở)
- **Defender**: `DeviceInfo.ExposureLevel` (theo exposure score) và `IsInternetFacing` có sẵn để lọc trong custom detection. `ExposureGraphNodes.NodeProperties` có insight "vulnerable to remote code execution" — [DeviceInfo](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-deviceinfo-table), [ExposureGraphNodes](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-exposuregraphnodes-table) (bậc 1; đã mở)
- **QRadar**: docs IBM chỉ nói biểu đồ Magnitude cho thấy magnitude được tính từ relevance, credibility và severity — [Offense investigation](https://www.ibm.com/docs/en/SSKMKU/com.ibm.qradar.doc/c_analyst_wf_ui_offense_details.html) (bậc 1, trích đoạn search, chưa mở). Phần còn lại là nguồn thứ cấp:
  - relevance phản ánh mức quan trọng của đích, lấy từ weight của network/asset do admin đặt trong network hierarchy và asset profile;
  - severity so mối đe doạ với mức chuẩn bị của đích;
  - lỗ hổng gắn vào asset record khi import từ scanner ngoài.

  Tỷ trọng 50% relevance / 30% severity / 20% credibility chỉ có trong một study guide trên Scribd — [IBM Community thread](https://community.ibm.com/community/user/discussion/sources-at-offences) (bậc 3), [Scribd](https://www.scribd.com/document/753563600/Qradar) (bậc 3). **Chưa xác minh.**

### Nhận định
- **Nhận định:** profile cần đủ ba thứ để làm vulnerability-aware detection theo kiểu Cisco:
  1. **service đang mở** (port/proto/app protocol, sản phẩm, version);
  2. **OS/sản phẩm có CPE**;
  3. **lỗ hổng mở** (CVE, sản phẩm bị ảnh hưởng, trạng thái).

  Phải có cả trạng thái **"không biết"** (Unknown Target / không có OS). Trạng thái này không được coi là "không có lỗ hổng". Đây là gap thật trong dữ liệu thụ động: host chỉ thấy qua flow sẽ không có OS (đúng như giới hạn NetFlow của Cisco).
- **Nhận định:** ghép theo CVE (signature IDS có `metadata cve` khớp với CVE trên asset) chính xác hơn ghép theo port. Ghép theo port/app protocol cho mức "potentially vulnerable". Còn port đóng hoặc không có dịch vụ thì hạ độ ưu tiên (Currently Not Vulnerable). Mức hạ này chỉ an toàn khi dữ liệu service mới, nên profile cần `last_seen` cho từng service.
- **Nhận định:** cách dùng an toàn là **điều chỉnh ưu tiên** (nâng hoặc hạ), không phải chặn alert. Lý do: dữ liệu lỗ hổng/service luôn có độ trễ, và scanner có thể sai version.

### Khoảng trống
- Không tìm được nghiên cứu 2019–2026 đo hiệu quả của việc kiểm chứng alert IDS bằng dữ liệu lỗ hổng. Truy vấn "Suricata alert CVE vulnerability scanner correlation…" không ra nguồn hữu ích. Các bài kinh điển về "alert verification" có trước 2018.
- Công thức magnitude của QRadar chưa có nguồn IBM chính thức.
- Chưa đọc docs Splunk ES về correlation search dùng dữ liệu lỗ hổng (Vulnerability data model).

## 5d. Coverage-aware detection: asset có nguồn log nào → rule nào chạy được

### Kết luận ngắn
Đã có ngôn ngữ chuẩn để khai báo "rule cần dữ liệu gì". ATT&CK v18 (2025-10) dùng Detection Strategy → Analytic → Log Source/Data Component. Splunk security_content có file `data_sources/*.yml` với `mitre_components`, `source`, `sourcetype` và `fields`. Elastic có `related_integrations` và `required_fields`. DeTT&CT chấm "device completeness" theo % thiết bị có nguồn đó. Chưa vendor nào **tính coverage theo từng asset** rồi đánh dấu rule "câm" trên asset đó. Phần này kho entity phải tự làm. Mức chắc chắn **cao** về chuẩn. Số liệu "rule hỏng" chỉ có từ một vendor.

### Phát hiện có nguồn
- **ATT&CK v18 (Oct 2025)**: "Detections in techniques have been replaced with Detection Strategies". Thêm Analytics, sửa Data Components, deprecate Data Sources. Enterprise có 691 Detection Strategies, 1739 Analytics, 106 Data Components. 37 Data Source Enterprise bị deprecate — [Updates October 2025](https://attack.mitre.org/resources/updates/updates-october-2025/) (bậc 1, 2025-10; đã mở)
- Mỗi analytic khai báo **platform** và bảng log source gồm Data Component + channel + ví dụ event. Ví dụ AN0001: `Network Connection Creation (DC0082)` qua `AWS:VPCFlowLogs`, `Cloud Service Metadata (DC0070)` qua `AWS:CloudTrail`, và `Network Traffic Content (DC0085)` qua `ebpf:syscalls` — [DET0001](https://attack.mitre.org/detectionstrategies/DET0001/) (bậc 1; đã mở). Theo trích đoạn blog MITRE trên Medium, Log Source không còn là object riêng mà nằm trên Data Component (bậc 1, chưa mở).
- **Splunk security_content** có file data source riêng. Ví dụ `sysmon_eventid_1.yml` (version 4, sửa 2026-05-13) có `mitre_components: [Process Creation, Process Metadata, Command Execution, OS API Execution]`, `source: XmlWinEventLog:Microsoft-Windows-Sysmon/Operational`, `separator: EventID = 1`, link cấu hình SwiftOnSecurity, `supported_TA` (Splunk Add-on for Sysmon 5.0.1) và danh sách `fields` (CommandLine, ParentImage, Hashes…). Detection tham chiếu bằng `data_source: [Sysmon EventID 1, Windows Event Log Security 4688, CrowdStrike ProcessRollup2]` — [sysmon_eventid_1.yml](https://raw.githubusercontent.com/splunk/security_content/develop/data_sources/sysmon_eventid_1.yml) (bậc 1, 2026-05-13; đã mở), [windows_suspicious_process_file_path.yml](https://github.com/splunk/security_content/blob/develop/detections/endpoint/windows_suspicious_process_file_path.yml) (bậc 1, theo trích đoạn search)
- **Elastic** prebuilt rule có `related_integrations`, `required_fields` và `setup`. Trang rule details hiện trạng thái cài của integration. Theo issue của đội docs, hai field này "informational and don't affect execution": rule vẫn chạy theo index pattern, và thường chỉ cần một trong các integration liên quan. Trước 8.7 có lỗi Elastic Defend hiện "not installed" sai (trích đoạn search của [docs-content #3994](https://github.com/elastic/docs-content/issues/3994) và [detection-rules PR 5249](https://github.com/elastic/detection-rules/pull/5249), bậc 1, chưa mở)
- **DeTT&CT**: file data source ghi `date_registered`, `date_connected`, `products`, loại hệ thống mà nguồn áp dụng, cờ `available_for_data_analytics`, và điểm chất lượng — [Data sources wiki](https://github.com/rabobank-cdc/DeTTECT/wiki/Data-sources) (bậc 1, sửa 2023-11-01; đã mở). Chất lượng có 5 chiều:
  - **Device completeness**: "Indicates if the required data is available for all devices", 1 = 1–25%, 2 = 26–50%, 3 = 51–75%, 4 = 76–99%, 5 = 100%;
  - data field completeness (% field cần có được điền);
  - timeliness;
  - consistency (% field được chuẩn hoá);
  - retention (% so với thời gian lưu mong muốn).

  — [Data quality scoring](https://github.com/rabobank-cdc/DeTTECT/wiki/data-quality-scoring) (bậc 1, không rõ ngày; đã mở). Wiki vẫn mô tả mô hình "30+ data sources, 90+ data components" trước v18, nên chưa theo cấu trúc Detection Strategy/Analytic.
- **Rule câm**: theo nhiều bài thứ cấp, báo cáo CardinalOps "State of SIEM Detection Risk" lần thứ 5 (2025-06) cho biết SIEM doanh nghiệp chỉ phủ **21%** kỹ thuật ATT&CK — [SDC Exec](https://www.sdcexec.com/safety-security/risk-compliance/news/22942866/cardinalops-enterprise-siems-miss-79-of-mitre-attck-techniques) (bậc 2, 2025-06; trích đoạn). Con số "~13% rule không hoạt động, chủ yếu do data source cấu hình sai và thiếu field" chỉ thấy trong trích đoạn search (betanews 403). Đây là **tuyên bố vendor, chưa xác minh**.
- Công cụ mã nguồn mở `deadair` (Go, Apache-2.0, giai đoạn sớm) chạy read-only trên SIEM. Nó tìm rule bật nhưng "mù": selector index/alias không trỏ tới gì, mọi nguồn khớp đều stale hoặc rỗng, field khai báo không có ở nguồn nào — [github.com/alephnull-sh/deadair](https://github.com/alephnull-sh/deadair) (bậc 3, dự án nhỏ; trích đoạn)

### Nhận định
- **Nhận định:** "coverage-aware" có hai cấp. **Cấp tenant** (DeTT&CT, CardinalOps) trả lời câu hỏi "tenant có nguồn X không". **Cấp asset** trả lời "asset này có nguồn X, đủ field, gần đây không". Rule scope theo role (5a) chỉ có nghĩa khi asset trong scope có đúng nguồn mà analytic cần. Vì thế profile cần một **ma trận asset × nguồn telemetry**. Mỗi ô ghi: nguồn (`metadata.product` + `metadata.log_source` + class_uid), last_seen, volume và tỉ lệ field bắt buộc được điền. Từ đó suy ra **"rule nào có thể bắn trên asset này"**, bằng cách join với khai báo nguồn của rule theo kiểu Splunk `data_source` / ATT&CK log source.
- **Nhận định:** chỉ số "device completeness" của DeTT&CT tính được trực tiếp từ ma trận này: % asset trong scope có nguồn, theo từng role. Đây là KPI coverage cho detection engineering, khác với KPI coverage chung của CIS đã có trong report trước.
- **Nhận định:** vì `required_fields` của Elastic chỉ mang tính thông tin, nền tảng không chặn rule câm. Sản phẩm cần chủ động đánh dấu "rule X không áp dụng hoặc câm trên N asset của role Y".

### Khoảng trống
- Chưa có ví dụ vendor tính coverage theo từng asset × rule. Docs đã đọc dừng ở cấp tenant/integration.
- OSSEM (data dictionaries, detection model) chưa được mở trong lượt này.
- Chưa có nguồn gốc của con số 13% rule hỏng.

## 5e. Chỗ join ngữ cảnh: lúc ingest, lúc rule chạy hay lúc tạo alert

### Kết luận ngắn
Cả ba chỗ đều có vendor dùng, và mỗi chỗ đánh đổi khác nhau:
- **Ingest** (Google aliasing/enrichment): rẻ khi query, nhưng ngữ cảnh đóng băng tại thời điểm vào.
- **Lúc rule chạy** (Sentinel watchlist, YARA-L `graph`, KQL join `DeviceInfo`): luôn lấy dữ liệu mới nhất có trong bảng, nhưng dễ sai point-in-time và phụ thuộc chu kỳ refresh.
- **Lúc tạo alert** (Elastic asset criticality): alert giữ ngữ cảnh lúc sinh, đổi criticality không sửa alert cũ.

Mức chắc chắn **trung bình**: cơ chế có docs, nhưng trade-off chủ yếu là suy luận cộng với nguồn thứ cấp.

### Phát hiện có nguồn
- **Google SecOps ở lúc ingest**:
  - aliasing gộp hostname, `asset_id` và MAC vào một asset profile (cần cùng namespace); IP chỉ dùng khi thiếu `asset_id`;
  - user được tra theo thứ tự email → SID → user ID → employee ID, lấy "the entity whose validity interval intersects with the event time";
  - entity context có lookback 5 ngày cho dữ liệu đến trễ;
  - dưới 1% event lỡ pass đầu và được xử lý lại sau;
  - enrichment không ghi đè giá trị log gốc (trừ process).

  — [How Google SecOps enriches event and entity data](https://docs.cloud.google.com/chronicle/docs/event-processing/data-enrichment) (bậc 1; đã mở)
- **Google ở lúc rule chạy**: entity context không có timestamp riêng mà có `entity.metadata.interval` (có thể không theo ranh giới ngày). Event chỉ join khi timestamp nằm trong interval — [Context-aware analytics](https://docs.cloud.google.com/chronicle/docs/detection/context-aware-analytics) (bậc 1; đã mở)
- **Elastic ở lúc tạo alert**: khi entity có criticality, "all subsequent alerts related to that entity are enriched with its criticality level". Khi xem risk score, phải kiểm "the entity's criticality level from the time the alert was generated". Bulk import (CSV/TXT/TSV ≤ 1 MB, cột type/name/level) ghi đè mức cũ, và risk score chỉ tính lại ở lượt hàng giờ — [Asset criticality](https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/asset-criticality) (bậc 1, không rõ ngày; đã mở)
- **Sentinel ở lúc rule chạy**: watchlist "cached for optimal query performance" nhưng "refresh every 12 days". Thời gian query hẹp có thể làm `_GetWatchlist()` trả thiếu — [Watchlists](https://learn.microsoft.com/en-us/azure/sentinel/watchlists) (bậc 1, 2026-06-23). `DeviceInfo` của Defender lưu lịch sử cập nhật (mỗi bản ghi chứa trạng thái đầy đủ). Nhờ vậy query vừa lấy được trạng thái mới nhất (`arg_max`), vừa tìm được trạng thái tại thời điểm event bằng join theo thời gian — [DeviceInfo](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-deviceinfo-table) (bậc 1)
- Ý kiến practitioner/vendor (trích đoạn search, chưa mở):
  - ngữ cảnh "high-value, low-volatility" nên đưa lên sớm, còn ngữ cảnh động/điều tra để sau;
  - enrich trước ingest có rủi ro "data staleness" và làm pipeline chậm khi lookup chậm.

  — [Tenzir: Enrichment complexity in the wild](https://docs.tenzir.com/blog/enrichment-complexity-in-the-wild) (bậc 2, vendor), [nhimg.org](https://nhimg.org/articles/legacy-siem-enrichment-is-a-timing-problem-not-a-tooling-problem/) (bậc 3, bài tài trợ, có con số DataBahn 50–70% chưa xác minh)

### Nhận định
- **Nhận định:** cách phối hợp đề xuất cho kho entity trên OCSF:
  1. **Lúc ingest**: chỉ ghi khoá ổn định `asset_uid` (resolve theo tenant + validity interval), cùng vài thuộc tính ít đổi (role chính, env, criticality), vào `enrichments[]`, kèm `profile_version`/thời điểm.
  2. **Lúc rule chạy**: join các tập động (service mở, phần mềm, lỗ hổng mở, baseline "đã biết", coverage) từ bảng profile **có lịch sử (SCD/interval)**, theo thời gian event, không theo "bây giờ". Cách này tránh hai lỗi: rule chạy lại hoặc backfill bị sai, và asset vừa được vá bị coi là chưa từng có lỗ hổng.
  3. **Lúc tạo alert**: chụp snapshot ngữ cảnh đã dùng vào alert (giống Elastic) để điều tra và audit sau này. Nếu profile đổi thì hiện "giá trị hiện tại khác lúc alert".
- **Nhận định:** watchlist refresh 12 ngày hay IdentityInfo resync 14 ngày cho thấy độ trễ ngữ cảnh ở cấp ngày là chuyện bình thường ở vendor lớn. Profile nên công bố độ tươi cho từng thuộc tính, để rule biết khi nào không nên tin vào thuộc tính đó (ví dụ không hạ ưu tiên khi dữ liệu service cũ hơn N ngày).

### Khoảng trống
- Không tìm được bài của Anton Chuvakin hay SpecterOps bàn trực tiếp ingest-time và query-time enrichment cho detection.
- Không có số liệu độc lập về chi phí và độ chính xác của từng chỗ join.

## Ánh xạ sang profile và nguồn OCSF 1.9.0

| Cơ chế trước detection | Profile phải lưu | Lấy từ OCSF 1.9.0 (class/field) | Ghi chú |
|---|---|---|---|
| Scope/loại trừ theo role/class | `role[]` có confidence + last_seen; `device_type`; `env`; tag có hạn; membership của tập có tên (`role:dc`, `role:scanner`) | `5001` Device Inventory Info (`device.type_id`, `os`, `is_managed`); suy diễn role từ `4001`/`4003`/`3002` (ví dụ phục vụ Kerberos/LDAP → DC); `device.agent_list[]`; `metadata.product` của log (firewall → network device) | `DeviceRoles` của Defender là mẫu; ATT&CK "mutable elements" là điểm gắn |
| Baseline "đã biết" → lệch chuẩn | Tập có first_seen/last_seen/count: service lắng nghe (port, proto, product), phần mềm, cặp cha–con process, user đã logon, đích outbound; baseline window; cờ cold-start | Service: `5040` Live Evidence Info (`query_evidence` LISTEN/service), `201004` Windows Service Activity, `4001` (`app_protocol_name`, phía `dst_endpoint`); phần mềm: `5020` Software Inventory Info; process: `1007` Process Activity; logon: `3002` Authentication; outbound: `4001`/`4003`/`4002` | Lấy class ID theo notes `ocsf-observation-map.md`. Window tham khảo theo UEBA (10/30/90/180 ngày) |
| Detection theo lỗ hổng/exposure | CVE mở + sản phẩm/version bị ảnh hưởng + trạng thái; service/port mở có last_seen; internet-facing; trạng thái "chưa biết OS/service" | `2002` Vulnerability Finding (`vulnerabilities[]`, `affected_packages`); `5004` Patch State; `5001` (`os.cpe_name`); service như trên; IDS alert `2004` Detection Finding hoặc `4001` có CVE trong finding/`unmapped` | Mẫu 5 mức impact của Cisco |
| Coverage-aware | Ma trận asset × nguồn: (`metadata.product`, `metadata.log_source`, `class_uid`) → last_seen, volume, % field bắt buộc; agent/sensor health | `metadata.product`, `metadata.log_source`, `metadata.reporter`, `metadata.loggers[]`; `device.agent_list[]`; `5001` | Join với khai báo nguồn của rule (ATT&CK log source / Splunk `data_source`) |
| Chỗ join | `asset_uid` theo tenant + validity interval; `profile_version`; snapshot ngữ cảnh trên alert | `enrichments[]` của `base_event`; `observables[]` | Profile có lịch sử, join theo thời gian event |

- **Nhận định:** class `2004` Detection Finding và vị trí của CVE trong alert IDS chưa được kiểm trong lượt này (cần đối chiếu notes `ocsf-observation-map.md` hoặc schema). Writer nên coi dòng đó là gợi ý.

## Truy vấn đã chạy
- Splunk Enterprise Security asset lookup fields is_expected requires_av should_update cim_entity_zone (standard)
- Elastic detection rule required_fields related_integrations missing integration (standard)
- MITRE ATT&CK v18 detection strategies analytics data components replace data sources (standard)
- Splunk ES "is_expected" "Expected Host Not Reporting" asset lookup header (standard)
- QRadar offense magnitude relevance credibility severity vulnerability asset (standard)
- Google SecOps YARA-L graph entity context "$e.graph" asset role example (standard)
- Defender XDR custom detection ExposureGraphNodes DeviceInfo criticality join KQL (standard)
- DeTT&CT data source quality visibility scoring per platform (standard)
- Elastic security ML job rare_process_by_host_windows peer anomaly host prebuilt jobs list (standard)
- Suricata alert CVE vulnerability scanner correlation false positive reduction asset vulnerable "not vulnerable" (standard)
- Cisco Secure Firewall Management Center intrusion event impact level "Vulnerable" "Potentially Vulnerable" host profile (standard)
- ibm.com docs QRadar "relevance" offense magnitude "weight" network asset vulnerabilities (standard)
- "QRadar" "magnitude" "relevance" "severity" "credibility" site:ibm.com docs offense (standard)
- splunk security_content detection yaml "data_source" field "Sysmon EventID 1" mapping data sources (standard)
- detection rules silently broken missing telemetry log source health detection engineering blog (standard)
- Chuvakin context enrichment detection "ingest time" vs "query time" SIEM enrichment trade-off (standard)
- peer group anomaly detection SOC false positive evaluation paper alerts host context 2022 2023 arXiv (standard)
- CardinalOps 2025 State of SIEM Detection Risk report 13% rules broken 21% techniques (standard)
- Splunk Enterprise Security asset and identity entity zones cim_entity_zone multi-tenant overlapping IP (standard)
- Defender XDR DeviceRoles "domain controller" "confidence" device role tagging criticality predefined classification (standard)
