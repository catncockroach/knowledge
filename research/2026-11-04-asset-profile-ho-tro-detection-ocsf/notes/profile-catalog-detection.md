# Danh mục thông tin asset/user profile phục vụ detection và ánh xạ OCSF 1.9.0

Góc này khảo sát các mô hình entity/UEBA/asset của vendor lưu những thuộc tính gì và đưa thuộc tính nào cho logic detection dùng. Từ đó dựng danh mục nhóm thông tin mà profile cần có. Field OCSF đã đối chiếu với bản clone `ocsf-schema` tag 1.9.0 (đọc `objects/*.json`, `events/**/*.json`, `dictionary.json` bằng `python3 -I`). Link schema dạng `https://github.com/ocsf/ocsf-schema/blob/1.9.0/<path>` là bậc 1. Note này kế thừa, không làm lại: [ocsf-observation-map.md](ocsf-observation-map.md) (bản đồ bằng chứng thiết bị/dịch vụ/ứng dụng) và report [2026-11-03 asset-profile-vendor-giao-dien-soc](../../2026-11-03-asset-profile-vendor-giao-dien-soc/report.md) (các khối thông tin trên profile, extension đề xuất, provenance, lifecycle, đa tenant). Phần dưới chỉ thêm những gì hai tài liệu đó chưa có: thuộc tính cụ thể mà vendor phơi ra cho rule, và cột "dùng trước / dùng sau detection".

## Câu hỏi phụ 7: Profile cần thể hiện những nhóm thông tin nào để phục vụ detection, mỗi nhóm dùng vào bước nào, lấy từ OCSF ở đâu hay phải tự giữ?

### Kết luận ngắn

Các vendor lớn đều phơi cho rule cùng một bộ khung, gồm khoảng 12 nhóm. Ba nhóm được thiết kế **riêng cho detection** chứ không phải cho inventory:
1. **Cờ kỳ vọng.** Splunk `is_expected`/`should_timesync`/`should_update`/`requires_av` là ví dụ: profile nói "asset này *phải* có X", rồi rule báo khi X vắng mặt.
2. **Baseline "lần đầu / hiếm" theo nhiều tầng.** Microsoft UEBA có ma trận user × peer × tenant với cửa sổ 10/30/90/180 ngày. Google có prevalence và first_seen.
3. **Nguồn đã thấy và sức khoẻ sensor.** Ví dụ là `DiscoverySources` và `SensorHealthState` của Defender, `reduced_functionality_mode` của CrowdStrike.

OCSF 1.9.0 cung cấp được bằng chứng quan sát cho phần lớn các nhóm, nhưng chỉ dưới dạng event hoặc ảnh chụp. Sáu nhóm phải tự giữ trong kho entity, vì OCSF không có thực thể bền vững hay field tương ứng trên `device`/`user`:
- cờ kỳ vọng,
- baseline tích luỹ,
- coverage theo nguồn,
- lịch sử thay đổi,
- verdict gắn ngược về entity,
- ngoại lệ có hạn.

**Mức chắc chắn:**
- **Cao** về danh sách thuộc tính của Microsoft, Splunk, Google, Elastic ECS và CrowdStrike, vì đã đọc docs bậc 1 hoặc source code của chính vendor.
- **Cao** về field OCSF, vì đã đọc trực tiếp JSON tag 1.9.0.
- **Trung bình** về việc correlation search nào dùng `should_update`/`requires_av`, vì docs không nêu tên.
- **Thấp** về Exabeam và CrowdStrike Identity, vì docs bị khoá hoặc chỉ có tài liệu marketing.

### Phát hiện có nguồn

#### Microsoft Sentinel UEBA: `BehaviorAnalytics` và `IdentityInfo`

- **Bảng `BehaviorAnalytics`** có ba trường dynamic: `UsersInsights`, `DevicesInsights` và `ActivityInsights`. Đi kèm là `InvestigationPriority`, một anomaly score 0–10 ("0=benign, 10=highly anomalous"). Baseline của ActivityInsights "is dynamically compiled each time it's used". Mỗi activity có cửa sổ lookback riêng — [Microsoft Sentinel UEBA reference](https://learn.microsoft.com/en-us/azure/sentinel/ueba-reference) (bậc 1, ms.date 2025-08-28, cập nhật 2026-08-05)
- **`UsersInsights`** gồm `BlastRadius` (Low/Medium/High), `IsDormantAccount`, `IsLocalAdmin`, `IsNewAccount` và `OnPremisesSID`.
  - `BlastRadius` tính từ vị trí của user trong cây tổ chức cộng với role và quyền Entra. Nó chỉ tính được khi thuộc tính *Manager* có giá trị.
  - `IsDormantAccount` nghĩa là "hasn't been used for the past 180 days".
  - `IsNewAccount` nghĩa là "created within the past 30 days".
  - Nguồn: [UEBA reference](https://learn.microsoft.com/en-us/azure/sentinel/ueba-reference) (bậc 1, 2025-08)
- **`DevicesInsights`** gồm `Browser`, `DeviceFamily`, `DeviceType`, `ISP`, `OperatingSystem`, `ThreatIntelIndicatorType`/`Description` (resolve từ IP), `UserAgent` và `UserAgentFamily`. Đây là ngữ cảnh của *client device trong hành động*, không phải bản ghi asset bền vững — [UEBA reference](https://learn.microsoft.com/en-us/azure/sentinel/ueba-reference) (bậc 1, 2025-08)
- **`ActivityInsights`** dùng cùng một mẫu 5 cờ cho mỗi chiều: *FirstTimeUser…*, *…UncommonlyBy User*, *…Among Peers*, *FirstTime…InTenant*, *…Uncommonly…InTenant*.
  - Các chiều gồm Action, App, Browser, Country, Device, ISP và Resource.
  - Cửa sổ baseline: thường là **10 ngày** cho mức user ("uncommon by user"); **30, 90 hoặc 180 ngày** cho mức first-time, peer và tenant. Ví dụ: Country là 90/10/90/90/90; Action và Resource là 180/10/180/180/180; Browser và ISP là 30/10/30/30/30.
  - Cờ dành riêng cho host: `FirstTimeUserLoggedOnToDevice` (180 ngày) và `DeviceFamilyUncommonlyUsedInTenant` (30 ngày).
  - Cờ khác: `LastTimeUserPerformedAction` (180 ngày), `UncommonHighVolumeOfOperations` (7 ngày), `UnusualNumberOfUsersAddedToGroup` (5 ngày).
  - Nguồn: [UEBA reference](https://learn.microsoft.com/en-us/azure/sentinel/ueba-reference) (bậc 1, 2025-08)
- **Bảng `IdentityInfo`** được Microsoft mô tả là dùng được "in analytics rules, hunting queries, and workbooks, enhancing your analytics to fit your use cases and reducing false positives". Các field liên quan detection:
  - `AssignedRoles`: chỉ built-in role.
  - `GroupMembership`: tối đa 500 nhóm, tính bắc cầu.
  - `BlastRadius`.
  - `ChangeSource`: AzureActiveDirectory/ActiveDirectory/UEBA/Watchlist/FullSync.
  - `IsAccountEnabled`.
  - `UserAccountControl`: gồm các cờ như `PasswordNeverExpires`, `TrustedForDelegation`, `DontRequirePreauthentication`, `PasswordNotRequired`.
  - `RiskLevel`/`RiskState`.
  - `UserState` (Active/Disabled/Dormant/Lockout) và `UserStateChangedOn`.
  - `AccountCreationTime`, `DeletedDateTime`.
  - `Manager`, `Department`, `JobTitle`, `EmployeeId`.
  - Nguồn: [UEBA reference](https://learn.microsoft.com/en-us/azure/sentinel/ueba-reference) (bậc 1, 2025-08)
- **Đồng bộ và lưu giữ của `IdentityInfo`:**
  - Đồng bộ toàn bộ **14 ngày** một lần. Khi user, group hoặc role thay đổi thì ingest lại trong **15–30 phút**.
  - Retention mặc định **30 ngày**.
  - Bản ghi user đã xoá được giữ lại (có `deletedDateTime`) "to audit changes to user records".
  - Microsoft dặn bỏ qua các field `IsServiceAccount`, `Tags`, `IsMFARegistered`, `LastSeenDate`, `EntityRiskScore`, `RelatedAccounts`, vì "not used or supported". Schema unified từ 05/2025 không còn các field này.
  - Nguồn: [UEBA reference](https://learn.microsoft.com/en-us/azure/sentinel/ueba-reference) (bậc 1, 2025-08)

#### Microsoft Defender XDR: `DeviceInfo`, TVM và exposure graph

- **Bảng `DeviceInfo`** có các cột phục vụ detection và coverage. Bảng "is updated continuously, and all updates contain the full current device data" — [DeviceInfo table](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-deviceinfo-table) (bậc 1, ms.date 2026-07-27). Các cột:
  - Phân loại: `DeviceCategory` (Endpoint/Network device/IoT/Unknown), `DeviceType`, `DeviceSubtype`.
  - Coverage và sensor: `OnboardingStatus`, `SensorHealthState` ("health of the device's EDR sensor"), `ClientVersion`.
  - Exposure và giá trị: `IsInternetFacing`, `ExposureLevel` (Low/Medium/High), `AssetValue` (Low/Normal/High).
  - Tag và nhóm: `DeviceManualTags`, `DeviceDynamicTags` ("added and removed dynamically based on dynamic rules"), `MachineGroup` (dùng cho RBAC).
  - Loại trừ: `IsExcluded`/`ExclusionReason`.
  - Hợp nhất ID: `MergedDeviceIds`/`MergedToDeviceId`.
  - Vòng đời: `IsTransient` ("short-lived or transient based on the frequency of appearance").
  - Nguồn đã thấy: `DiscoverySources` ("Products or services that have seen or reported the device, including when they last reported it").
  - Vai trò: `DeviceRoles` ("roles identified by the system or defined by users, confidence levels, and the last time each role was seen").
  - Khác: `LoggedOnUsers`, `PublicIP`, `Site`, `CloudPlatforms`, `MitigationStatus`.
- **Bảng `DeviceTvmSoftwareInventory`** có các cột `SoftwareVendor`, `SoftwareName`, `SoftwareVersion`, `EndOfSupportStatus`, `EndOfSupportDate` và `ProductCodeCpe`. Lưu ý quan trọng cho detection: bảng này "isn't ingested into Microsoft Sentinel … Using TVM table data directly in Microsoft Sentinel analytics and detections isn't currently supported unless you build a custom ingestion path" — [DeviceTvmSoftwareInventory](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicetvmsoftwareinventory-table) (bậc 1, ms.date 2026-06-14)
- **Bảng `ExposureGraphNodes`** có `NodeId`, `NodeLabel`, `NodeName`, `Categories`, `NodeProperties` và `EntityIds`. `NodeProperties` là "JSON formatted raw data (unstructured)", chứa các insight như internet exposure và RCE — [ExposureGraphNodes](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-exposuregraphnodes-table) (bậc 1, ms.date 2025-03-28)
- **Query mẫu chính thức trên exposure graph** dùng:
  - các thuộc tính `NodeProperties.rawData.exposedToInternet`, `vulnerableToRCE`, `IsInternetFacing`, `VulnerableToPrivilegeEscalation`, `criticalityLevel.criticalityLevel`, `containsSensitiveData`;
  - các edge `"Can Authenticate As"` và `"CanRemoteInteractiveLogonTo"`.
  - Ví dụ: "users logged in to more than one critical device", hoặc đường đi DeviceWithRCE → Identity → CriticalDevice.
  - Nguồn: [Query the enterprise exposure graph](https://learn.microsoft.com/en-us/security-exposure-management/query-enterprise-exposure-graph) (bậc 1, ms.date 2025-07-30, cập nhật 2026-10-09)

#### Splunk ES Asset & Identity

- **Field asset của Splunk ES Asset & Identity** (theo tài liệu ES 7.2; trang này không cho chép nguyên văn nên đây là diễn giải):
  - Định danh: `ip`, `mac`, `nt_host`, `dns`. Asset cần ít nhất một trong bốn field này.
  - `owner`.
  - `priority` (unknown/low/medium/high/critical): đưa vào Urgency của notable. "Unknown" làm giảm urgency.
  - `bunit`: dùng để lọc trên dashboard.
  - `category`: "logical classifications used for asset and identity correlation".
  - `pci_domain`.
  - `is_expected`: true thì correlation search **Expected Host Not Reporting** báo khi asset ngừng gửi log.
  - `should_timesync`: true thì **Should Timesync Host Not Syncing** báo khi không có event time-sync trong **24 giờ**.
  - `should_update`: asset phải được giám sát event cập nhật hệ thống.
  - `requires_av`: asset phải có anti-virus.
  - `cim_entity_zone`.
  - Nguồn: [Format an asset or identity list as a lookup (ES 7.2)](https://help.splunk.com/en/splunk-enterprise-security-7/administer/7.2/asset-and-identity-manual-registration/format-an-asset-or-identity-list-as-a-lookup-in-splunk-enterprise-security) (bậc 1, không rõ ngày; ES 7.2)
- **Field identity:**
  - `identity`, `email`, `managedBy`, `priority` (đưa vào urgency), `bunit`, `category`.
  - `watchlist`: đánh dấu identity để giám sát hoạt động, dùng ở User Activity Monitoring.
  - `startDate`/`endDate`: ngày vào làm và ngày nghỉ việc.
  - `work_city`/`work_country`/`work_lat`/`work_long`, `cim_entity_zone`.
  - Trang này không nêu correlation search nào dùng `should_update`, `requires_av`, `endDate` hay `managedBy`.
  - Nguồn: [Format an asset or identity list (ES 7.2)](https://help.splunk.com/en/splunk-enterprise-security-7/administer/7.2/asset-and-identity-manual-registration/format-an-asset-or-identity-list-as-a-lookup-in-splunk-enterprise-security) (bậc 1)
- **Tag và giá trị mặc định:** tag asset mặc định sinh từ các giá trị `category`, `pci_domain`, `is_expected`, `should_timesync`, `should_update`, `requires_av` và `bunit`. Các field boolean được chuẩn hoá sau xử lý — [Asset and identity fields after processing (ES 7.2)](https://help.splunk.com/splunk-enterprise-security-7/administer/7.2/asset-and-identity-validation/asset-and-identity-fields-after-processing-in-splunk-enterprise-security) (bậc 1; chỉ đọc qua snippet search). `pci_domain` để trống thì mặc định là `untrust` — [Format an asset or identity list](https://help.splunk.com/en/splunk-enterprise-security-7/administer/7.2/asset-and-identity-manual-registration/format-an-asset-or-identity-list-as-a-lookup-in-splunk-enterprise-security) (bậc 1)
- **Thực hành từ cộng đồng** (bậc 3, chỉ để lần manh mối):
  - `is_expected` dùng để lộ ra "rogue or surprise assets that are sending logs", với CMDB làm danh sách gốc.
  - Một mẫu hay gặp: lookup chính đặt mặc định các cờ là true, lookup ngoại lệ nhỏ đặt `requires_av=false` cho máy không chạy AV.
  - Nguồn: [Splunk Community: how to populate is_expected, should_timesync, requires_av and should_update](https://community.splunk.com/t5/Splunk-Enterprise-Security/how-to-you-populate-is-expected-should-timesync-requires-av-and/m-p/532635) (bậc 3, 2020)
- **Identity hết hạn** (bậc 3): object "expired identities" trong data model Assets & Identities từng định nghĩa `endDate=*`, nên bắt cả account không bao giờ hết hạn. Nhân viên Splunk gợi ý đổi thành `endDate < now` — [Splunk Community: Expired account activity](https://community.splunk.com/t5/Splunk-Enterprise-Security/Splunk-Expired-account-activity/td-p/234547) (bậc 3, không rõ ngày)

#### Google SecOps: entity context và YARA-L

- **YARA-L join được ngữ cảnh entity** qua tiền tố `graph.` (event dùng `udm.`), ghép qua match variable chung như `$user`, `$host`, `$hash`.
  - Event chỉ ghép được với bản ghi entity khi timestamp của event nằm trong `entity.metadata.interval`.
  - "It's impossible to have a rule that only uses Entity": rule phải có ít nhất một event UDM.
  - Ví dụ chính thức: rule AdminLogin lọc `graph.entity.resource.attribute.roles.type = "ADMINISTRATOR"`. Các ví dụ khác dùng `graph.entity.user.title` và `graph.entity.user.termination_date.seconds`.
  - Nguồn: [Context-aware analytics](https://docs.cloud.google.com/chronicle/docs/detection/context-aware-analytics) (bậc 1, không rõ ngày)
- **First seen, prevalence và context từ bên ngoài:**
  - `first_seen_time`/`last_seen_time` chỉ có cho entity DOMAIN, IP_ADDRESS và FILE. Với USER và ASSET thì **chỉ có `first_seen_time`**.
  - Prevalence đọc qua `graph.entity.domain.prevalence.rolling_max`. Rule mẫu `network_prevalence_low_prevalence_domain_access` chấm điểm theo `rolling_max`.
  - Context entity được tạo với **lookback 5 ngày**. Thiếu `interval.end_time` thì bản ghi coi như hiệu lực 5 ngày.
  - Có context từ bên ngoài: WHOIS (`domain.expiration_time`), Safe Browsing, GCTI (feed "Tor Exit Nodes", "Benign Binaries", "Remote Access Tools").
  - Nguồn: [Context-enriched data in rules](https://docs.cloud.google.com/chronicle/docs/detection/use-enriched-data-in-rules) (bậc 1, không rõ ngày)
- **Field UDM entity:**
  - Message `Asset`: `asset_id`, `hostname`, `category`, `type`, `deployment_status` (enum vòng đời), `platform_software`, `software[]`, `vulnerabilities[]`, `attribute.{roles,labels,permissions,creation_time,last_update_time}`, `first_seen_time`, `first_discover_time`/`last_discover_time`, `last_boot_time`, `system_last_update_time`, `network_domain`, `product_object_id`, `hardware[]`, `location`.
  - Message `User`: `hire_date`, `termination_date`, `title`, `department[]`, `managers[]`, `account_type` (service/domain/cloud), `first_seen_time`, `account_lockout_time`, `last_login_time`, `last_password_change_time`, `password_expiration_time`, `time_off[]`.
  - `metadata.source_type` có ba giá trị: `ENTITY_CONTEXT` (khách hàng nạp vào, ví dụ AD), `DERIVED_CONTEXT` (tính từ dữ liệu khách: prevalence, first/last seen) và `GLOBAL_CONTEXT` (WHOIS, Safe Browsing).
  - Message `EntityRisk`: `risk_window`, `normalized_risk_score` (0–1000), `risk_delta`, `detections_count`, `first_detection_time`/`last_detection_time`, `risk_window_has_new_detections`.
  - Nguồn: [UDM field list](https://docs.cloud.google.com/chronicle/docs/reference/udm-field-list) (bậc 1, không rõ ngày)

#### Elastic ECS entity và entity store

- **Fieldset `entity` của ECS:**
  - `entity.type`: enum bucket/database/container/function/queue/host/user/application/service/session/cloud/orchestrator.
  - `entity.sub_type`, `entity.source`.
  - `entity.attributes.{managed, mfa_enabled, permissions, oauth_consent_restriction, known_redirects, storage_class}`.
  - `entity.behavior`: "ephemeral characteristics derived from observed behavior over a time period", thường là boolean.
  - `entity.metrics`, `entity.raw`, `entity.reference`.
  - `entity.last_seen_timestamp`, `entity.lifecycle.last_activity`.
  - `entity.relationships.{administers, depends_on, owns, supervises}`.
  - Hầu hết field đang ở trạng thái beta.
  - Nguồn: [ECS entity fields](https://www.elastic.co/docs/reference/ecs/ecs-entity) (bậc 1, không rõ ngày)
- **Entity store:** criticality có bốn mức `low_impact`/`medium_impact`/`high_impact`/`extreme_impact`. Xoá dữ liệu entity store không xoá risk score hay criticality đã gán. Đây là bằng chứng Elastic tách thuộc tính do người gán khỏi thuộc tính quan sát — [Elastic entity store API (search snippet)](https://www.elastic.co/docs/api/doc/serverless/operation/operation-upsertentity) (bậc 1; chỉ đọc qua snippet, trang trả 404 khi fetch). Từ 9.4, entity store có snapshot lịch sử hằng ngày `.entities.v2.history.security_<space-id>.<timestamp>`. Nguồn nạp gồm IdP (AD, Entra, Okta, Google Workspace, M365, CloudTrail) và EDR (Elastic Defend, CrowdStrike, SentinelOne, MDE) — [Entity store](https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/entity-store) (bậc 1, Stack 9.4+, không rõ ngày)

#### Exabeam

- **Context table có sẵn:** 13 bảng nạp từ LDAP (`user_department`, `user_manager`, `user_title`, `user_location`, `user_country`, `user_division`, `user_account`…) cộng `user_is_privileged`, bảng duy nhất do admin nhập tay, qua CSV hoặc bộ lọc AD. Trang này không mô tả model hay rule nào dùng chúng — [Exabeam out-of-the-box context tables](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/administration-guide/set-up-authentication-and-access-control/set-up-context-management/out-of-the-box-context-tables.html) (bậc 1, không rõ ngày)
- **Context table tự tạo:** dùng làm watchlist hoặc danh sách tham chiếu cho asset, IOC và user/group. Ví dụ: financial servers, privileged insiders, departed employees — [Exabeam custom context tables](https://docs.exabeam.com/en/cloud-delivered-advanced-analytics/all/administration-guide/set-up-authentication-and-access-control/custom-context-tables.html) (bậc 1; chỉ đọc qua snippet search)
- Report trước đã có cách Exabeam chấm cao hơn khi service account đăng nhập interactive hoặc khi người không phải executive truy cập máy của executive, và cách dùng asset group để giảm FP. Xem [57][77] trong [report 2026-11-03](../../2026-11-03-asset-profile-vendor-giao-dien-soc/report.md).

#### CrowdStrike Falcon

- **Thuộc tính host lọc được bằng FQL**, theo hướng dẫn trong repo `falcon-mcp` của chính CrowdStrike:
  - Phân loại: `product_type_desc` (Workstation, Server, Domain Controller, Mobile), `platform_name`.
  - Sức khoẻ sensor: `reduced_functionality_mode` (yes/no/"").
  - Containment: `status`, với giá trị như normal, containment_pending, lift_containment_pending.
  - Thời gian: `first_seen`, `last_seen`, `last_login_timestamp` ("once a week"), `modified_timestamp`.
  - Tag: `tags`. FalconGroupingTags đặt từ cloud và sửa được; SensorGroupingTags do bộ cài sensor ghi sẵn và chỉ đọc.
  - Thư mục: `ou`, `site_name`, `machine_domain`.
  - Cloud: `service_provider`, `service_provider_account_id`, `instance_id`.
  - Khác: `linux_sensor_mode` (Kernel/User), `release_group`, `agent_version`, `local_ip`, `external_ip`, `mac_address`, `serial_number`.
  - Nguồn: [CrowdStrike/falcon-mcp `falcon_mcp/resources/hosts.py`](https://github.com/CrowdStrike/falcon-mcp/blob/d766b1abaf38a2e668828a57a7a881f82f94be83/falcon_mcp/resources/hosts.py) và [`modules/hosts.py`](https://github.com/CrowdStrike/falcon-mcp/blob/d766b1abaf38a2e668828a57a7a881f82f94be83/falcon_mcp/modules/hosts.py) (bậc 1, source code của vendor, commit `d766b1a`, đọc ngày 2026-11-04)
- **Falcon Identity Protection:** chỉ tìm được tài liệu marketing. Nó nói tới stale account, privileged account, password aging, profile hành vi của service account và "100+ behavior analytics and risk scores". Không có danh sách thuộc tính — [CrowdStrike Identity Security Assessment data sheet](https://www.crowdstrike.com/resources/data-sheets/identity-security-assessment-data-sheet/) (bậc 2–3, marketing, không rõ ngày)

#### OCSF 1.9.0: đối chiếu trực tiếp schema

- **`device`** (extends `endpoint`) có:
  - `groups` ("The group names to which the device belongs"), `org`;
  - `is_managed`, `is_compliant`, `is_trusted`, `is_personal`, `is_shared`, `is_backed_up`, `is_supervised`;
  - `risk_level_id` (0 Info … 4 Critical), `risk_score`;
  - `first_seen_time` ("initial discovery time"), `last_seen_time`, `created_time`, `modified_time`, `boot_time`;
  - `type_id`, `network_interfaces`, `hypervisor`, `image`, `location`, `region`, `subnet`.
  - `endpoint` có `agent_list`, `owner` ("owns the endpoint or was last logged into it"), `zone` ("network zone or LAN segment"), `os`, `hw_info`, `instance_uid`.
  - `device` và `endpoint` **không có** `criticality_id`, `tags`, `labels` hay role.
  - Nguồn: [device.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/device.json), [endpoint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/endpoint.json) (bậc 1, 2026-08-03)
- **`agent`:**
  - `agent.type_id` có 1 EDR, 2 DLP, 3 Backup & Recovery, 4 Performance Monitoring, 5 Vulnerability Management, 6 Log Forwarding, 7 MDM, 8 Configuration Management, 9 Remote Access.
  - `agent.policies[]` là các `policy` có `is_applied`, `name`, `version`.
  - Đây là chỗ hợp chuẩn duy nhất để biết "asset có agent loại X, policy Y đã áp chưa".
  - Nguồn: [agent.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/agent.json), [policy.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/policy.json) (bậc 1)
- **Class 5019 Device Config State Change** có `security_states[]`/`prev_security_states` và `security_level_id`/`prev_security_level_id`. `security_state.state_id` có 23 giá trị, ví dụ 1 Missing or outdated content, 2 Policy mismatch, 3 In network quarantine, 4 Protection off, 5 Protection malfunction, 6 Protection not licensed, 7 Unremediated threat, 9 Reboot pending, 11 Not installed, 16 SELinux disabled, 19 Open remote access, 21 Rooted, 23 Compliance failure. Class 5002 Device Config State có `assessments` và `cis_benchmark_result` — [device_config_state_change.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/device_config_state_change.json), [security_state.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/security_state.json), [config_state.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/config_state.json) (bậc 1)
- **`user`** có:
  - `type_id` (1 User, 2 Admin, 3 System, **4 Service**), `has_mfa`, `groups[]`, `risk_level_id`, `risk_score`, `uid_alt`, `credential_uid`, `programmatic_credentials`.
  - `account` có `is_disabled`, `is_locked`, `labels`, `tags`.
  - `group.privileges`.
  - `ldap_person` có `hire_time`, `leave_time`, `manager`, `department`, `cost_center`, `job_title`, `last_login_time`, `deleted_time`, `employee_uid`, `labels`, `tags`.
  - Lớp 5003 User Inventory Info và 5001 Device Inventory Info chỉ có `actor` + `user`/`device`.
  - Nguồn: [user.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/user.json), [account.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/account.json), [ldap_person.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/ldap_person.json), [group.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/group.json), [user_inventory.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/user_inventory.json) (bậc 1)
- **`resource_details`** (dùng trong `resources[]` của Finding) có `criticality_id` (0 Unknown, 1 Low, 2 Medium, 3 High, 4 Very High, 99 Other), `role_id` (1 Target, 2 Actor, 3 Affected, 4 Related), `owner`, `namespace`, `zone`, `agent_list`, `group`, `device`, `user`, `resource_relationship`. Nó kế thừa `tags`/`labels` từ `_resource` — [resource_details.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/resource_details.json), [_resource.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/_resource.json) (bậc 1)
- **Finding, verdict và baseline:**
  - `finding.status_id` có 1 New, 2 In Progress, **3 Suppressed**, 4 Resolved, 5 Archived, 6 Deleted.
  - `verdict_id` chỉ có trên **2005 Incident Finding**: 1 False Positive, 2 True Positive, 3 Disregard, 4 Suspicious, 5 Benign, 6 Test, 7 Insufficient Data, 8 Security Risk, 9 Managed Externally, 10 Duplicate.
  - 2004 Detection Finding có `anomaly_analyses`, `confidence_id`, `risk_score`, `impact_id`, `is_alert`, `vulnerabilities`, `resources`.
  - `finding_info` có `data_sources[]` ("data sources utilized in generation of the finding"), `analytic`, `related_events`, `first_seen_time`/`last_seen_time`.
  - Các object `anomaly_analysis` (`analysis_targets`, `anomalies`, `baselines`), `baseline`/`anomaly` (`observation_parameter`, `observation_type`, `observations[]`, `observed_pattern`) và `observation` (`count`, `timespan`, `value`) được thêm ở **1.5.0** (#1358).
  - Nguồn: [finding.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/findings/finding.json), [incident_finding.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/findings/incident_finding.json), [detection_finding.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/findings/detection_finding.json), [finding_info.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/finding_info.json), [anomaly_analysis.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/anomaly_analysis.json), [baseline.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/baseline.json), [CHANGELOG v1.5.0](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md) (bậc 1)
- **Lỗ hổng:**
  - `vulnerability` có `is_exploit_available`, `exploit_last_seen_time`, `is_fix_available`, `fix_coverage_id`, `first_seen_time`/`last_seen_time`, `affected_packages`, `remediation`, `severity`.
  - `cve` có `cvss`, `epss` (`score`, `percentile`), `cwe`.
  - Nguồn: [vulnerability.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/vulnerability.json), [cve.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/cve.json), [epss.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/epss.json) (bậc 1)
- **Exposure, network scope và thay đổi entity:**
  - `network_endpoint.network_scope_id` có 1 Internal, 2 External.
  - `network_interface.open_ports`, `namespace`.
  - Class 3004 Entity Management có `entity`, `entity_result`, `updated_entity` (trạng thái trước/sau).
  - Nguồn: [network_endpoint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/network_endpoint.json), [network_interface.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/network_interface.json), [entity_management.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/iam/entity_management.json) (bậc 1)

### Bảng danh mục: nhóm thông tin → dùng trước/sau detection → vendor → nguồn OCSF 1.9.0

Quy ước cột cuối:
- **OCSF** là lấy thẳng (hoặc gần như thẳng) từ field đã nêu.
- **OCSF→tổng hợp** là có bằng chứng thô trong OCSF, nhưng giá trị trên profile phải tính gộp theo thời gian.
- **Kho entity** là OCSF không có chỗ chứa, phải tự giữ. Có thể xuất ra qua `enrichments[]` hoặc `resources[]`, hoặc qua extension đề xuất ở report 2026-11-03.

Các ô "dùng trước" và "dùng sau" là **Nhận định** của researcher, dựng từ cách vendor mô tả field. Các ví dụ có dẫn nguồn ở trên.

| # | Nhóm thông tin | Thuộc tính cụ thể (gợi ý) | Dùng trước detection | Dùng sau detection | Vendor tham khảo | Nguồn OCSF 1.9.0 / chỗ giữ |
|---|---|---|---|---|---|---|
| 1 | Định danh và sở hữu | asset_uid ổn định; hostname/FQDN, IP–MAC theo khoảng thời gian, cloud instance/account; ID theo từng nguồn và lịch sử merge; owner (CMDB) tách khỏi người dùng gần nhất; BU, site, zone; với user: UPN, SID, các account liên kết, manager, department | Resolve event về đúng entity, là điều kiện để mọi enrichment khác hoạt động. Zone/tenant làm khoá. Merge ID để baseline không bị chia đôi | Biết "đây là máy nào, của ai"; liên hệ owner/manager; pivot sang mọi ID của cùng entity | Defender `MergedDeviceIds`, `Site`, `CloudPlatforms`; Splunk `ip/mac/nt_host/dns`, `owner`, `bunit`, `cim_entity_zone`, `managedBy`; Google `asset_id`, `product_object_id`, `network_domain`; IdentityInfo `Manager`, `EmployeeId`; CrowdStrike `ou`, `site_name`, `instance_id` | **OCSF**: 5001 `device.{uid,uid_alt,hostname,ip,network_interfaces,instance_uid,os_machine_uuid,org,location,region}`, `endpoint.zone`; 5003 `user.{uid,uid_alt,email_addr,domain,account}`, `ldap_person.{manager,department,cost_center,employee_uid}`; `metadata.tenant_uid`. **Kho entity**: asset_uid, lịch sử alias/merge, owner nghiệp vụ (`endpoint.owner` gộp cả "owner" lẫn "last logged" nên không dùng làm owner) |
| 2 | Role/class và criticality | Loại thiết bị (endpoint/server/DC/network/IoT); role kèm độ tin và last seen (DC, jump host, scanner, build server, service account); criticality 5 mức, kèm nguồn gán (rule/override) và lý do; với user: type (user/admin/service), privileged, executive, blast radius | **Scoping rule**: chỉ chạy trên DC, loại scanner. Chọn baseline theo role. Ngưỡng hoặc hệ số RBA theo criticality | Ưu tiên triage (ma trận severity × priority); ràng buộc khi phản ứng (không tự cô lập DC); ước lượng impact | Defender `DeviceCategory`/`DeviceType`/`DeviceRoles` (confidence + last seen)/`AssetValue`; exposure graph `criticalityLevel`; Splunk `priority`, `category`; CrowdStrike `product_type_desc`; Google `asset.category/type`, `attribute.roles`; Elastic criticality 4 mức; Exabeam `user_is_privileged`; UEBA `BlastRadius`, `IsLocalAdmin` | **OCSF**: `device.type_id`, `user.type_id` (4 Service), `group.privileges`, 3005 User Access Management (`privileges`), 3006 Group Management, 5009 Admin Group Query (nhóm admin). Criticality chỉ xuất được qua `resource_details.criticality_id` trên Finding. **Kho entity**: role[] kèm confidence/evidence, criticality và nguồn gán, cờ executive/privileged |
| 3 | Exposure | Internet-facing (kèm bằng chứng, có hạn), port/service mở ra ngoài, network scope, exposure level, đường tấn công tới critical asset | Detection có điều kiện theo exposure: exploit hoặc brute force nhắm vào service đang lộ ra internet; nâng severity | Đánh giá điểm vào ban đầu; blast radius; ưu tiên vá hoặc đóng cổng | Defender `IsInternetFacing`, `ExposureLevel`; exposure graph `exposedToInternet`/`IsInternetFacing`, edge `CanRemoteInteractiveLogonTo` | **OCSF→tổng hợp**: 4001 có `initiator_id` + `dst_endpoint` (phía server) với `src_endpoint.network_scope_id = 2 External`; `network_interface.open_ports`; 5040 LISTEN. **Kho entity**: cờ internet-facing có TTL (Defender tự bỏ sau 48 giờ, theo report trước), exposure score |
| 4 | Dịch vụ, phần mềm, ứng dụng | Service đang lắng nghe (port/proto/product/version), phần mềm đã cài (CPE/purl, EOL), binary đã chạy, agent đã cài, SaaS/app đang dùng, first/last seen từng mục | Allowlist kỳ vọng theo role, để bắt dịch vụ mới lắng nghe hoặc phần mềm mới trên server; join CVE ↔ phần mềm; rule riêng cho phần mềm EOL | "Còn asset nào cùng phần mềm hoặc phiên bản này?"; xác định vector; gỡ phần mềm | Defender `DeviceTvmSoftwareInventory` (`ProductCodeCpe`, `EndOfSupportStatus`), nhưng không ingest vào Sentinel; Google `asset.software[]`, `platform_software`; Sentinel `FirstTimeUserUsedApp`, `AppUncommonlyUsed…` | **OCSF→tổng hợp**: 5020 `sbom`/`package` (deprecated), 6002 `application`, 1007 `process.file.*`, 201004 `win_service`, 5040; chi tiết ở [ocsf-observation-map.md](ocsf-observation-map.md). **Kho entity**: bảng asset_service / asset_software kèm evidence + first/last seen |
| 5 | Baseline hành vi | Với user: quốc gia, ISP, thiết bị, app, browser, resource, action, giờ hoạt động. Với host: user logon, process/binary, peer nội bộ, domain, lịch job. Mỗi chiều có cả ba tầng entity, peer và tenant; có cửa sổ và last time | Cờ "lần đầu / hiếm" làm điều kiện rule hoặc làm risk modifier; prevalence thấp làm tăng điểm | Trả lời "hành vi này có bình thường với asset/role/peer không"; giải thích điểm anomaly | Sentinel `ActivityInsights` (5 cờ × 7 chiều, cửa sổ 10/30/90/180 ngày), `InvestigationPriority`; Google prevalence `rolling_max`, `first_seen_time`; Elastic `entity.behavior`; Exabeam peer group | **OCSF**: chỉ có ở *đầu ra* của detection (2004 `anomaly_analyses[].baselines[]`, từ 1.5.0). **Kho entity**: baseline tích luỹ (đếm theo ngày, first/last seen theo cặp entity–giá trị), tính từ 3002, 1007, 4001, 4003, 6003 |
| 6 | Độ phủ telemetry và trạng thái kiểm soát bảo mật | Cờ kỳ vọng (phải gửi log, phải có EDR/AV, phải time-sync, phải được cập nhật); nguồn đã thấy asset kèm last seen theo nguồn; loại log thực có (theo class); trạng thái sensor (healthy, RFM, onboarded); policy đã áp; trạng thái containment | **Coverage-aware**: rule nào chạy được trên asset; rule "expected host not reporting"; phân biệt "không alert" với "không có dữ liệu"; rule "host thiếu AV hoặc AV tắt" | Biết có thể phản ứng gì (có agent để isolate không); độ tin của kết luận "không thấy gì" | Splunk `is_expected`, `requires_av`, `should_update`, `should_timesync`; Defender `OnboardingStatus`, `SensorHealthState`, `DiscoverySources`, `ClientVersion`; CrowdStrike `reduced_functionality_mode`, `status`, `linux_sensor_mode` | **OCSF**: `device.agent_list[].{type_id,version,policies[].is_applied}`, `device.is_managed`; 5019 `security_states[].state_id` (4 Protection off, 11 Not installed…); 5002 `assessments`. **OCSF→tổng hợp**: last seen theo (`metadata.product`, `class_uid`). **Kho entity**: cờ kỳ vọng và coverage[] (nguồn, log type, expected, last_seen) |
| 7 | Lỗ hổng | CVE đang mở trên asset/phần mềm, CVSS/EPSS, exploit có sẵn, fix có sẵn, first/last seen | Detection có điều kiện: exploit nhắm vào CVE còn mở (sẽ có ích hơn); nâng hoặc hạ severity; exposure graph dạng "RCE + internet-facing" | Xác định vector khả dĩ; tìm asset khác cùng CVE; ưu tiên vá | Defender TVM, exposure graph `vulnerableToRCE`, `VulnerableToPrivilegeEscalation`; Google `asset.vulnerabilities[]`; CrowdStrike ma trận criticality × exploit status (report trước) | **OCSF**: 2002 `vulnerabilities[].{cve.{uid,cvss,epss},is_exploit_available,is_fix_available,affected_packages,first_seen_time,last_seen_time}`. **Kho entity**: trạng thái mở/đã vá theo asset (OCSF chỉ có từng finding) |
| 8 | Quan hệ | user ↔ host (logon interactive/remote), host ↔ host (peer, lateral), asset ↔ service/app, user ↔ group/role, "can authenticate as", asset group/cluster | Rule đồ thị: user không thuộc peer mà lại logon vào máy critical; dùng asset group để giảm FP (cụm cân bằng tải) | Blast radius; tìm asset liên quan; dựng timeline nhiều entity | Exposure graph edge `Can Authenticate As`, `CanRemoteInteractiveLogonTo`; Elastic `entity.relationships.{administers,depends_on,owns,supervises}`; IdentityInfo `GroupMembership`; Defender `LoggedOnUsers`; Sentinel `FirstTimeUserLoggedOnToDevice` | **OCSF→tổng hợp**: 3002 (`user`, `dst_endpoint`, `logon_type_id`), 4001/4006/4005, 3006 Group Management, `resource_details.resource_relationship`. **Kho entity**: bảng cạnh có trọng số + first/last seen |
| 9 | Lịch sử thay đổi | Thay đổi thuộc tính (OS, owner, role, criticality, IP), phần mềm hoặc dịch vụ mới, thay đổi trạng thái tài khoản (enable, lock, group, role), nguồn thay đổi | Rule "thay đổi gần đây + hành vi lạ"; suppress trong change window | "Có gì thay đổi gần đây trên asset?"; phân biệt thay đổi hợp lệ với thay đổi do tấn công | IdentityInfo `ChangeSource`, `UserStateChangedOn`, giữ bản ghi đã xoá để audit; Elastic snapshot lịch sử hằng ngày (9.4+); Google `attribute.last_update_time`, `system_last_update_time` | **OCSF**: 3004 `entity`/`updated_entity`, 3001 Account Change, 5019 `prev_security_states`, 6002, `device.modified_time`. **Kho entity**: phiên bản thuộc tính có thời gian hiệu lực (OCSF không giữ trạng thái theo thời gian) |
| 10 | Lịch sử detection và verdict | Alert/finding liên quan, verdict (TP/FP/benign/test), rule nào bắn, số lần bắn, risk score có lý do và cửa sổ | Tuning: rule hay ra FP trên asset hoặc role này; hạ trọng số; RBA cộng dồn theo entity | Triage: "asset này từng có alert tương tự, kết luận ra sao"; risk trend | Google `EntityRisk` (`detections_count`, `first/last_detection_time`, `risk_delta`); Defender `RiskLevel`; Sentinel `InvestigationPriority` | **OCSF**: 2004 (`finding_info.{analytic,uid}`, `risk_score`, `resources[]`), 2005 `verdict_id`, `finding.status_id`. **Kho entity**: tổng hợp theo entity × rule × verdict |
| 11 | Ngoại lệ và tag có hạn | Tag thủ công hoặc động, watchlist, ngoại lệ suppress theo rule kèm phạm vi, lý do, người duyệt, **hạn**; loại trừ khỏi quản lý lỗ hổng | Suppression theo tag hoặc role thay vì theo IP; watchlist làm tăng hệ số rủi ro | Analyst ghi ngược verdict thành ngoại lệ; review khi ngoại lệ hết hạn | Defender `DeviceManualTags`/`DeviceDynamicTags`, `IsExcluded`/`ExclusionReason`; Splunk `watchlist`; CrowdStrike FalconGroupingTags (sửa được) và SensorGroupingTags (chỉ đọc); Exabeam watchlist context table | **OCSF**: chỉ có `tags`/`labels` trên `account`, `resource_details`, `ldap_person`, `metadata`; `finding.status_id = 3 Suppressed`. **Kho entity**: tag và ngoại lệ có hạn, kèm audit |
| 12 | Lifecycle state | first seen, last seen tổng và theo nguồn, trạng thái (candidate/active/not_seen/stale/retired), transient, với user: ngày vào/nghỉ, dormant, new account, disabled/locked | Rule cho tài khoản dormant hoặc mới hoạt động, user đã nghỉ việc mà vẫn đăng nhập, host stale bỗng có hoạt động; không baseline trên asset transient | Biết asset có còn tồn tại không; thu hồi quyền khi nghỉ việc | UEBA `IsDormantAccount` (180 ngày), `IsNewAccount` (30 ngày); IdentityInfo `UserState`; Defender `IsTransient`; Splunk `startDate`/`endDate`; Google `deployment_status`, `hire_date`, `termination_date`, `time_off`; CrowdStrike `first_seen`/`last_seen` | **OCSF**: `device.first_seen_time`/`last_seen_time`/`created_time`, `ldap_person.hire_time`/`leave_time`/`deleted_time`, `account.is_disabled`/`is_locked`. **Kho entity**: trạng thái lifecycle, ngưỡng theo lớp tài sản |
| 13 | Trạng thái và bảo vệ tài khoản (user) | MFA, password never expires, Kerberos preauth tắt, delegation, last password change, password expiration, rủi ro từ IdP | Rule nhắm vào tài khoản yếu (AS-REP roasting khi `DontRequirePreauthentication`); nâng severity | Hành động: reset mật khẩu, revoke session; biết tài khoản có MFA không | IdentityInfo `UserAccountControl`, `RiskLevel`/`RiskState`; Google `last_password_change_time`, `password_expiration_time`, `account_lockout_time`; Elastic `entity.attributes.mfa_enabled` | **OCSF**: `user.has_mfa`, `user.risk_level_id`, `account.is_disabled`/`is_locked`, `ldap_person.last_login_time`. Không có field cho cờ UAC hay ngày đổi mật khẩu, nên chúng rơi vào `unmapped` hoặc **kho entity** |

### Nhận định

- **Nhận định:** cờ kỳ vọng (nhóm 6) là thiết kế học được rõ nhất từ Splunk. Profile không chỉ ghi "đã thấy gì" mà còn ghi "đáng lẽ phải thấy gì". Rule absence (Expected Host Not Reporting, Should Timesync Host Not Syncing trong 24 giờ) chỉ làm được khi có cờ này. Với kho entity trên OCSF, có thể *suy* cờ kỳ vọng mặc định theo role và lớp tài sản (server → `expects: EDR, auth log, timesync`), rồi cho người override, giống mẫu "mặc định true + lookup ngoại lệ" mà practitioner Splunk dùng.
- **Nhận định:** mẫu baseline 5 cờ × nhiều chiều của Microsoft (user, peer, tenant; first time và uncommon) là cấu trúc baseline đáng sao chép nhất, vì nó đóng gói thành boolean dễ dùng trong rule. Với asset, có thể chuyển sang: "lần đầu process X trên host", "process X hiếm trong role", "lần đầu trong tenant". Cửa sổ 10 ngày cho mức entity và 30–180 ngày cho mức tenant/peer là điểm khởi đầu có tài liệu.
- **Nhận định:** cả Microsoft (`DiscoverySources` ghi nguồn kèm lần báo cuối, `DeviceRoles` ghi role kèm confidence và last seen) lẫn Google (`source_type`, `interval`) đều gắn **nguồn, độ tin và thời gian hiệu lực ngay trên thuộc tính**. Danh mục ở trên nên áp quy ước này cho mọi thuộc tính suy diễn (role, service, internet-facing), không chỉ cho owner/criticality.
- **Nhận định:** Microsoft bỏ `IsServiceAccount`, `Tags`, `IsMFARegistered` khỏi IdentityInfo ("not used or supported"). Điều này cho thấy cờ "service account" khó suy ra đáng tin chỉ từ IdP. Khi profile suy ra cờ này (từ `user.type_id = 4`, mẫu logon, SPN), nó nên mang confidence.
- **Nhận định:** việc TVM không ingest vào Sentinel cho thấy rủi ro kiến trúc. Nếu dữ liệu phần mềm và lỗ hổng chỉ nằm ở kho inventory mà engine detection không join được, thì nhóm 4 và nhóm 7 chỉ phục vụ được *sau* detection. Sản phẩm của chủ repo nên đảm bảo các nhóm 2, 3, 4, 6, 7 join được *lúc rule chạy*, qua `enrichments[]` hoặc lookup theo tenant, chứ không chỉ hiển thị trên trang profile.
- **Nhận định:** Google chỉ tính `first_seen_time` cho USER/ASSET, còn `last_seen` thì không. Với SOC, last seen *theo nguồn* lại là thứ quan trọng cho coverage (nhóm 6). Đây là chỗ sản phẩm có thể làm tốt hơn.
- **Nhận định:** OCSF 1.9.0 đã có chỗ ghi *kết quả* baseline (`anomaly_analyses`) và *verdict* (2005), nhưng verdict chỉ có trên Incident Finding, không có trên Detection Finding. Vì vậy vòng phản hồi verdict → entity phải đi qua incident, hoặc qua kho entity.

### Khoảng trống

- Chưa tìm được tên correlation search của Splunk ES dùng `should_update` và `requires_av`. Docs ES 7.2 chỉ mô tả ý nghĩa field, còn trang `docs.splunk.com` bản mới trả 403. Truy vấn đã thử: "Splunk Enterprise Security asset lookup fields is_expected should_timesync should_update requires_av", "Splunk security content should_update OR requires_av…".
- Chưa đọc được trang ES 8.x mô tả field A&I đầy đủ. Các field cũ vẫn xuất hiện trong header lookup của ES 8.0 (theo snippet search), nhưng chưa xác minh ngữ nghĩa ở 8.x.
- Exabeam: không có trang nào mô tả model hoặc rule nào tiêu thụ context table nào. Trang context table có sẵn không liệt kê Executive Users hay Service Accounts, dù trang tổng quan Context Management nhắc tới chúng. Hai trang có thể thuộc hai phiên bản khác nhau.
- CrowdStrike Identity Protection: không có docs công khai về thuộc tính entity. Danh sách field host chỉ lấy từ hướng dẫn FQL trong `falcon-mcp`, chưa đối chiếu với swagger của API.
- Elastic: chưa đọc được tên field đầy đủ của entity store 9.4+ (`entity.attributes.privileged`, `entity.lifecycle.first_seen`…). Trang API trả 404, nên mới dựa vào fieldset ECS `entity`.
- Securonix: không tìm kiếm, vì giới hạn số lượt gọi tool. Report trước đã ghi Securonix là vendor có docs khoá.
- Defender `DeviceNetworkInfo` và các key cụ thể của `DeviceRoles`/`DiscoverySources` (định dạng JSON): chưa mở.
- Không có số liệu độc lập cho thấy nhóm thông tin nào làm tăng chất lượng detection bao nhiêu. Mọi liên hệ "nhóm → bước" trong bảng là suy luận từ mô tả field của vendor.

## Truy vấn đã chạy

- Splunk Enterprise Security asset lookup fields is_expected should_timesync should_update requires_av (standard)
- help.splunk.com asset and identity fields "should_timesync" "requires_av" description (extended)
- Splunk ES correlation search "Activity from Expired User Identity" endDate (standard)
- Splunk security content "should_update" OR "requires_av" Update data model correlation search Endpoint Malware (standard)
- Elastic entity store fields entity.attributes.privileged entity.lifecycle.first_seen asset.criticality (standard)
- Google SecOps UDM entity prevalence first_seen_time last_seen_time risk_score entity graph derived context (standard)
- Exabeam context tables out-of-the-box executive_users service_accounts privileged users asset types (standard)
- Exposure Management graph NodeProperties criticalityLevel exposedToInternet vulnerableToRCE query example (standard)
- CrowdStrike Falcon Identity Protection entity attributes "stale account" "privileged" "service account" detection risk factors list (standard)
- falconpy hosts GetDeviceDetails response fields reduced_functionality_mode product_type_desc device_policies first_seen last_seen (standard)
- Trang đã mở trực tiếp: Sentinel UEBA reference; Defender DeviceInfo, DeviceTvmSoftwareInventory, ExposureGraphNodes; Exposure Management query graph; Splunk ES 7.2 format lookup; Google context-aware analytics, use-enriched-data-in-rules, UDM field list (offset 0 và 200000); ECS entity; Elastic entity store; Exabeam OOTB context tables; raw `falcon-mcp` hosts.py (2 file)
