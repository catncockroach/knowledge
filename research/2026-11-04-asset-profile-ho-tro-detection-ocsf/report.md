---
title: Asset profile dựng từ log OCSF 1.9.0 phục vụ detection trước và sau khi phát hiện
date: 2026-11-04
question: Asset profile dựng từ log nhiều nguồn đã chuẩn hoá OCSF v1.9.0 cần thể hiện những nhóm thông tin nào để tăng chất lượng phát hiện (trước detection) và hỗ trợ triage, điều tra, phản ứng, vòng phản hồi (sau detection); mỗi nhóm lấy bằng chứng từ đâu trong OCSF, ghép thế nào, với case chi tiết là xác định thiết bị, dịch vụ, ứng dụng trên asset?
tags: [asset-profile, detection-engineering, ocsf, soc, entity-resolution, multi-tenant]
---

# Profile phục vụ detection phải lưu kỳ vọng, độ tin, thời hạn

> **Câu hỏi:** Asset profile dựng từ log OCSF 1.9.0 cần thông tin gì, lấy từ đâu và ghép thế nào để phục vụ detection trước (scoping, baseline, exposure, coverage, chỗ join) và sau khi có alert (triage, điều tra, phản ứng, verdict)? · **Ngày:** 2026-11-04 · **Phạm vi:** SOC/MSSP đa tenant, mọi nguồn đã chuẩn hoá OCSF v1.9.0 (tag 2026-08-03), chỉ log thụ động (EDR, firewall, proxy, DNS, DHCP, IdP, scanner, inventory); không gồm quét chủ động, ITAM, giao diện, viết rule cụ thể.

## Tóm tắt

Một asset profile phục vụ được detection khi nó trả lời năm câu hỏi mà rule đặt ra trước khi bắn và bốn câu hỏi mà analyst đặt ra sau khi alert đến: asset này thuộc **tập có tên** nào (role, zone, tenant) và với độ tin bao nhiêu; nó **đã từng** chạy dịch vụ, phần mềm, process, peer nào (kèm first/last seen); nó **lộ ra** gì và còn lỗ hổng gì, kể cả trạng thái "không biết"; nó **đáng lẽ phải** gửi những nguồn log nào và hiện có gửi không; rồi sau alert là ai sở hữu, gần đây đổi gì, phản ứng được bằng gì và bị ràng buộc gì, và các alert trước trên asset/role này được kết luận ra sao. Vendor lớn (Microsoft, Splunk, Google, Elastic, CrowdStrike) phơi cho rule cùng một khung khoảng 12 nhóm thuộc tính, và điểm chung đáng chép nhất là mọi thuộc tính suy diễn đều mang **nguồn, độ tin và thời gian hiệu lực** ngay trên nó [1][2][3]. OCSF 1.9.0 có chỗ cho bằng chứng quan sát của phần lớn các nhóm, rải ở khoảng **25 class và 40 object**, nhưng chỉ dưới dạng event hoặc ảnh chụp: không có thực thể asset bền vững, không có "service instance" (host, port, proto, sản phẩm, version), không có field cho cờ kỳ vọng, coverage, ngoại lệ có hạn hay role nghiệp vụ [4][5][6]. Vì vậy sáu nhóm phải tự giữ trong kho entity, và case "xác định thiết bị, dịch vụ, ứng dụng" thực chất là bước suy diễn ba bảng `asset_service`, `asset_software`, `asset_app_usage` từ ít nhất sáu loại bằng chứng có độ tin khác nhau. Mức chắc chắn **cao** về cơ chế vendor và cấu trúc schema (đọc docs bậc 1 và JSON gốc), **thấp** về hiệu quả định lượng: không có nghiên cứu độc lập nào đo mức giảm FP hay thời gian triage nhờ từng nhóm thông tin.

**Điểm chính**
- Scoping tốt nhất là rule tham chiếu **tập asset có tên** (`role:domain-controller`, `role:vuln-scanner`) sinh tự động từ profile, có confidence và last seen như `DeviceRoles` của Defender, thay cho danh sách IP hay watchlist tĩnh refresh **12 ngày** [1][7][8].
- Detection lệch chuẩn quy về new-terms/rare trên khoá tổ hợp có asset; Microsoft UEBA dùng cửa sổ **10/30/90/180 ngày** tuỳ chiều, nên profile cần sẵn các tập "đã biết" có first/last seen và cơ chế cold-start theo role [9][10].
- Mẫu impact 5 mức của Cisco cho thấy vulnerability-aware detection cần đủ ba thứ: service đang mở, OS/sản phẩm có CPE, lỗ hổng mở, và phải giữ trạng thái "Unknown" thay vì coi là "không lỗ hổng" [11].
- Chưa vendor nào tính coverage **theo từng asset × rule**; chuẩn khai báo dữ liệu rule cần đã có (ATT&CK v18 Analytic → Data Component, Splunk `data_source`, DeTT&CT device completeness), phần còn lại kho entity phải tự làm [12][13][14].
- Sau alert, phần lớn "false positive" thực chất là **benign trigger**, chỉ gỡ được bằng ngữ cảnh môi trường và thay đổi gần đây; verdict và ngoại lệ có hạn của vendor đều gắn với rule/incident, chưa ai ghi ngược thành kỳ vọng của asset/role [15][16][17].
- Nhận diện dịch vụ/ứng dụng thụ động bắt rất nhanh server đông khách (**99%** server theo trọng số client trong 14 phút) nhưng chỉ đạt **71%** tổng số server sau 18 ngày so với 94% của quét chủ động, nên `asset_service` không được "đóng" chỉ vì không còn thấy traffic [18].

## Profile vào vòng đời detection ở năm điểm trước alert và bốn điểm sau

Sơ đồ dưới tóm tắt vai trò của profile. Phía trên là kho entity theo tenant, có lịch sử; mũi tên xuống là các chỗ rule hoặc analyst đọc profile; mũi tên ngược lên là vòng phản hồi ghi vào profile.

```
        ┌──────── KHO ENTITY theo tenant, có lịch sử (SCD / validity interval) ────────┐
        │ định danh · role · exposure · service/software/app · baseline · coverage ·   │
        │ lỗ hổng · quan hệ · thay đổi · verdict · ngoại lệ có hạn · khả năng phản ứng  │
        └──┬─────────┬──────────┬───────────┬───────────┬────────────────────▲─────────┘
 TRƯỚC     │①scope   │②baseline │③exposure  │④coverage  │⑤join               │ verdict, ngoại lệ có hạn,
           ▼         ▼          ▼           ▼           ▼                    │ sửa profile, trạng thái
 log OCSF ─► ingest (asset_uid) ─► rule chạy (join theo giờ event) ─► ALERT 2004 + snapshot ngữ cảnh
                                                                       │
 SAU                                  ⑥triage ─► ⑦điều tra ─► ⑧phản ứng ─► ⑨báo cáo/verdict ──┘
```

Năm điểm trước alert là: ① scoping/loại trừ theo role, ② baseline "đã biết" để bắt lần đầu/hiếm, ③ điều kiện theo exposure và lỗ hổng, ④ biết rule nào chạy được trên asset nào, ⑤ chọn chỗ join ngữ cảnh. Bốn điểm sau là ⑥ triage, ⑦ điều tra, ⑧ phản ứng, ⑨ báo cáo và verdict, trong đó ⑨ nối ngược lên kho entity. Report này không lặp lại những gì hai report trước đã có: mô hình bảng asset, pipeline và profile theo loại asset ở report 2026-11-01, và ma trận urgency, risk multiplier, provenance, lifecycle, bố cục UI ở report 2026-11-03 (xem `research/2026-11-01-asset-inventory-profile-ocsf-1-9/report.md` và `research/2026-11-03-asset-profile-vendor-giao-dien-soc/report.md`).

## Danh mục 14 nhóm thông tin: sáu nhóm OCSF không có chỗ giữ

Bảng dưới là lõi của report. Cột "Trước" và "Sau" là **Nhận định** dựng từ cách vendor mô tả và dùng field; cột vendor là nơi thuộc tính đã có trong sản phẩm thật. Cột cuối phân ba loại: **OCSF** (lấy gần như thẳng), **OCSF→tổng hợp** (có bằng chứng thô nhưng giá trị trên profile phải tính gộp theo thời gian), **Kho entity** (OCSF không có chỗ chứa).

| # | Nhóm | Thuộc tính chính | Trước detection | Sau detection | Vendor tham khảo | Nguồn OCSF 1.9.0 / kho entity |
|---|---|---|---|---|---|---|
| 1 | Định danh và sở hữu | `asset_uid` ổn định; hostname/FQDN; IP–MAC theo khoảng thời gian; ID theo từng nguồn và lịch sử merge; owner nghiệp vụ tách khỏi người dùng gần nhất; BU, site, zone, tenant | Resolve event về đúng entity, điều kiện của mọi enrichment; zone/tenant làm khoá để rule DMZ của tenant A không áp sang IP trùng của tenant B | "Máy nào, của ai", liên hệ owner, pivot sang mọi ID của cùng entity | Defender `MergedDeviceIds`, `Site`; Splunk `ip/mac/nt_host/dns`, `owner`, `bunit`, `cim_entity_zone` [1][19] | **OCSF**: 5001 `device.{uid,uid_alt,hostname,ip,network_interfaces,instance_uid,os_machine_uuid,org}`, `endpoint.zone`, `metadata.tenant_uid`. **Kho entity**: asset_uid, alias/merge, owner (`endpoint.owner` gộp hai nghĩa, issue #1752) [5][20] |
| 2 | Role/class và criticality | Loại thiết bị; role[] kèm confidence, evidence, last seen (DC, jump host, scanner, build server); criticality kèm nguồn gán và lý do; với user: admin/service, privileged | **Scoping** rule; chọn baseline theo role; ngưỡng RBA theo criticality | Ưu tiên triage; ràng buộc containment; ước lượng impact | Defender `DeviceType`, `DeviceRoles`, `AssetValue`; CrowdStrike `product_type_desc` (Workstation/Server/Domain Controller); Google `attribute.roles` [1][21][2] | **OCSF**: `device.type_id` (15 giá trị), `user.type_id` 4 Service; criticality chỉ có ở `resource_details.criticality_id` trên Finding. **Kho entity**: role[], criticality [22][23] |
| 3 | Exposure | Internet-facing kèm bằng chứng và hạn; port/service mở ra ngoài; network scope | Điều kiện exploit/brute force nhắm vào service đang lộ; nâng severity | Điểm vào ban đầu; blast radius | Defender `IsInternetFacing`, `ExposureLevel`; exposure graph `exposedToInternet` [1][24] | **OCSF→tổng hợp**: 4001 `initiator_id` + `dst_endpoint` với `src_endpoint.network_scope_id` = 2 External; `open_ports`; 5040 LISTEN [25][26] |
| 4 | Dịch vụ, phần mềm, ứng dụng | Service lắng nghe (port/proto/product/version); phần mềm đã cài (CPE/purl, EOL); binary đã chạy; agent; SaaS đang dùng; first/last seen từng mục | Allowlist kỳ vọng theo role; "service mới lắng nghe", "phần mềm mới trên server"; join CVE ↔ phần mềm | "Asset nào khác cùng phần mềm/version?"; xác định vector | Defender `DeviceTvmSoftwareInventory` (`ProductCodeCpe`, `EndOfSupportDate`); Google `asset.software[]` [27][2] | **OCSF→tổng hợp**: 5020, 6002, 1007, 201004, 5040, 4001/4002/4007 (xem mục case). **Kho entity**: `asset_service`, `asset_software`, `asset_app_usage` |
| 5 | Baseline hành vi | Với host: user logon, process/cặp cha–con, peer, domain, lịch job; mỗi chiều ba tầng entity/peer/tenant, có cửa sổ | Cờ "lần đầu/hiếm" làm điều kiện rule hoặc risk modifier | "Hành vi này bình thường với asset/role không" | Sentinel `ActivityInsights`; Google prevalence `rolling_max` [10][28] | **OCSF**: chỉ có ở *đầu ra* (2004 `anomaly_analyses[].baselines[]`, từ 1.5.0). **Kho entity**: tập đã biết, đếm theo ngày [29] |
| 6 | Độ phủ telemetry và kiểm soát | Cờ kỳ vọng (phải gửi log, phải có EDR/AV, phải time-sync); nguồn đã thấy asset kèm last seen theo nguồn; class log thực có; sức khoẻ sensor; policy đã áp | **Coverage-aware**: rule nào chạy được; "expected host not reporting"; phân biệt "không alert" với "không dữ liệu" | Độ tin của kết luận "không thấy gì" | Splunk `is_expected`, `requires_av`, `should_timesync`; Defender `DiscoverySources`, `SensorHealthState`; CrowdStrike `reduced_functionality_mode` [19][1][21] | **OCSF**: `device.agent_list[].{type_id,policies[].is_applied}`, `is_managed`; 5019 `security_states[].state_id` (4 Protection off, 11 Not installed…). **Kho entity**: cờ kỳ vọng, ma trận coverage [30][31] |
| 7 | Lỗ hổng | CVE mở trên asset/phần mềm, CVSS/EPSS, exploit/fix có sẵn, first/last seen, trạng thái mở/đã vá | Ưu tiên theo "exploit nhắm vào CVE còn mở"; nâng/hạ severity | Vector khả dĩ; asset khác cùng CVE; ưu tiên vá | Defender exposure graph `vulnerableToRCE`; Google `asset.vulnerabilities[]` [24][32] | **OCSF**: 2002 `vulnerabilities[].{cve.{uid,cvss,epss},is_exploit_available,is_fix_available,affected_packages}`. **Kho entity**: trạng thái theo asset [33] |
| 8 | Quan hệ | user↔host, host↔host, asset↔service/app, user↔group, asset group/cluster | Rule đồ thị (user ngoài peer logon vào máy critical) | Blast radius, asset liên quan, timeline nhiều entity | Exposure graph edge `CanRemoteInteractiveLogonTo`; ECS `entity.relationships` [24][34] | **OCSF→tổng hợp**: 3002, 4001, 3006; `resource_details.resource_relationship` chỉ chở đồ thị producer tính sẵn. **Kho entity**: bảng cạnh có first/last seen |
| 9 | Lịch sử thay đổi | Thay đổi OS, owner, role, IP; phần mềm/dịch vụ mới; thay đổi trạng thái tài khoản; nguồn thay đổi | "Thay đổi gần đây + hành vi lạ"; suppress trong change window | "Gần đây đổi gì?" (nguồn benign trigger chính) | IdentityInfo `ChangeSource`; Elastic snapshot lịch sử hằng ngày [10][35] | **OCSF**: 3004 `entity`/`updated_entity`, 5019 `prev_security_states`, 6002, `device.modified_time`. **Kho entity**: phiên bản thuộc tính có thời gian hiệu lực [36] |
| 10 | Lịch sử detection và verdict | Finding liên quan, verdict, rule nào bắn, số lần, risk có lý do | Tuning rule hay ra benign trên asset/role; RBA cộng dồn | "Từng có alert tương tự, kết luận ra sao" | Google `EntityRisk` (`detections_count`, `risk_delta`) [2] | **OCSF**: 2004 `finding_info.analytic`, `resources[]`; `verdict_id` (profile `incident`), `status_id` 3 Suppressed. **Kho entity**: tổng hợp entity × rule × verdict [37][38] |
| 11 | Ngoại lệ và tag có hạn | Tag thủ công/động; ngoại lệ theo rule kèm phạm vi, lý do, người duyệt, **hạn** | Suppression theo tag/role thay vì IP | Ghi verdict thành ngoại lệ; review khi sắp hết hạn | Defender `DeviceDynamicTags`, `IsExcluded`; Sentinel automation rule có expiration [1][16] | **OCSF**: chỉ có `tags`/`labels` trên `account`, `resource_details`, `metadata`; không có class ngoại lệ. **Kho entity** |
| 12 | Lifecycle | first/last seen tổng và theo nguồn; candidate/active/stale/retired; transient | Không baseline trên asset transient; host stale bỗng hoạt động | Asset còn tồn tại không | Defender `IsTransient`; Google `deployment_status` [1][2] | **OCSF**: `device.first_seen_time`/`last_seen_time`/`created_time`. **Kho entity**: trạng thái, ngưỡng theo lớp |
| 13 | Bảo vệ tài khoản (user) | MFA, preauth tắt, delegation, đổi mật khẩu lần cuối, rủi ro IdP | Rule nhắm tài khoản yếu (AS-REP roasting khi `DontRequirePreauthentication`) | Reset mật khẩu, revoke session | IdentityInfo `UserAccountControl`, `RiskLevel` [10] | **OCSF**: `user.has_mfa`, `risk_level_id`, `account.is_disabled/is_locked`; cờ UAC không có field → `unmapped` [39] |
| 14 | Khả năng và chính sách phản ứng | Có EDR quản lý được không; nằm sau firewall/NAC nào; IdP nào khoá được user; backup; chính sách containment theo role/criticality; trạng thái "đang cô lập" | — | Chọn hành động khả dụng; bắt buộc duyệt với DC/critical | Defender device group Full/Semi/No automation, containment theo role; XSOAR allowlist hostname [40][41] | **OCSF**: `agent_list[].type_id` 1 EDR/3 Backup, `is_backed_up`, 7001–7004 Remediation (Isolate/Restore). **Kho entity**: chính sách, trạng thái tạm [42] |

Sáu nhóm OCSF không có chỗ giữ bền vững là cờ kỳ vọng (6), baseline tích luỹ (5), coverage theo nguồn (6), lịch sử thay đổi (9), verdict gắn ngược về entity (10) và ngoại lệ có hạn (11); thêm vào đó, `device` và `endpoint` của 1.9.0 **không có** `criticality_id`, `tags`, `labels` hay role [5][22]. Ba nhóm được thiết kế riêng cho detection chứ không cho inventory là cờ kỳ vọng, baseline nhiều tầng và nguồn đã thấy kèm sức khoẻ sensor: Splunk dùng `is_expected` để correlation search **Expected Host Not Reporting** báo khi asset ngừng gửi log, và `should_timesync` để báo khi không có event time-sync trong **24 giờ** [19].

**Nhận định:** quy ước đáng áp cho mọi thuộc tính suy diễn (role, service, internet-facing, OS) là kèm `source`, `confidence`, `valid_from/valid_to` và `last_seen`, giống `DeviceRoles` ("roles identified by the system or defined by users, confidence levels, and the last time each role was seen") và `DiscoverySources` của Defender, hay `metadata.source_type` (ENTITY_CONTEXT / DERIVED_CONTEXT / GLOBAL_CONTEXT) và `interval` của Google [1][2]. Rule khi đó có thể nói "chỉ scope theo role có confidence ≥ ngưỡng và thấy trong 7 ngày", và asset tự rời phạm vi khi role cũ hết hạn.

**Nhận định:** dữ liệu phần mềm/lỗ hổng chỉ có ích *trước* detection nếu engine join được nó lúc rule chạy. Microsoft ghi rõ `DeviceTvmSoftwareInventory` "isn't ingested into Microsoft Sentinel … Using TVM table data directly in Microsoft Sentinel analytics and detections isn't currently supported unless you build a custom ingestion path" [27]. Với sản phẩm của chủ repo, các nhóm 2, 3, 4, 6, 7 phải join được lúc rule chạy, không chỉ hiện trên trang profile.

## Trước detection: profile quyết định rule chạy ở đâu, so với cái gì, và có tin được không

### Scoping: rule tham chiếu tập asset có tên, profile đổi thì phạm vi đổi theo

Mọi nền tảng lớn đều có chỗ để rule thu hẹp về một lớp asset hoặc loại trừ một lớp, nhưng đặt ở các tầng khác nhau. Sigma để ngoại lệ trong **file filter riêng** (`filter.rules`, `selection`, `condition: not selection`), được nối vào điều kiện rule lúc convert, nhờ đó rule gốc từ rule pack không bị sửa; docs lấy ví dụ loại trừ user `adm_*` hoặc host tên "DC-" [8]. Sentinel join watchlist bằng `_GetWatchlist('alias')`, nhưng watchlist "refresh every 12 days", tối đa 10 triệu item mỗi workspace, không quản lý xuyên workspace qua Lighthouse, và có thể trả thiếu khi time range của query hẹp hơn chu kỳ refresh [7]. Defender đặt sẵn trong `DeviceInfo` các cột `DeviceCategory`, `DeviceType`, `DeviceRoles`, `MachineGroup`, `DeviceDynamicTags`; bảng "updated continuously, and all updates contain the full current device data", nên muốn lấy trạng thái mới nhất phải `arg_max` theo `DeviceId` [1]. Google YARA-L join event với entity graph qua biến chung (`$asset_context.graph.entity.hostname = $hostname`) và lọc theo `resource.attribute.roles.type` hay quan hệ `OWNS`, với giới hạn "It's impossible to have a rule that only uses Entity" và entity context không làm pivot cho sliding window được [3]. ATT&CK v18 còn đưa "mutable elements" vào analytic như điểm tuning theo môi trường, ví dụ AN0001 có `UserContext` ("Tunes detection based on which roles are expected to access metadata APIs") và `TimeWindow` [43].

**Nhận định:** có ba kiểu scoping cần profile cấp dữ liệu: inclusion ("DCSync chỉ có nghĩa khi đích là DC"), exclusion theo lớp (scanner, jump host, build server) và tham số theo ngữ cảnh kiểu mutable element. Profile nên xuất chúng thành tập asset có tên, có version và validity interval, để rule/filter tham chiếu tên tập thay vì danh sách IP. Với đa tenant, khoá tập phải chứa tenant/zone, theo cách entity zones của Splunk ghép IP với zone để `ip`/`nt_host` không bị merge xuyên zone (theo trích đoạn docs) [44]. Không tìm được số liệu vendor hay độc lập nào đo mức giảm FP khi scope theo role.

### Baseline: "lần đầu/hiếm" trên khoá tổ hợp có asset, cần cold-start theo role

"Lần đầu thấy" là primitive phổ biến nhất và có tham số rõ. Elastic new terms "fires when a value (or combination of up to three values) has never appeared in a configurable history window", với ví dụ `process.executable` chưa thấy trong 30 ngày và cặp `user.name` + `host.name` chưa thấy cùng nhau trong 14 ngày; docs cảnh báo "A window that is too short leads to excessive false positives" [9]. Microsoft Sentinel UEBA đóng gói baseline thành boolean theo mẫu 5 cờ cho mỗi chiều (user first-time, user uncommon, peers, tenant first-time, tenant uncommon), mỗi cờ có cửa sổ cố định: `ActionUncommonlyPerformedByUser` **10 ngày**, `FirstTimeUserConnectedFromCountry` **90 ngày**, `FirstTimeUserLoggedOnToDevice` và `DeviceUncommonlyUsedAmongPeers` **180 ngày**, `FirstTimeDeviceObservedInTenant` **30 ngày**; baseline "dynamically compiled each time it's used" [10]. Baseline theo **host** và theo **role của host** ít được chuẩn hoá hơn: UEBA chủ yếu xoay quanh user, còn Elastic có job ML `rare_process_by_host_*` coi process hiếm khi nó "only run occasionally as compared with other processes running on the host" (docs 7.9 cũ) [45]. Số liệu hiệu quả gần như không có: preprint của Hawryluk và cộng sự mô hình peer group cho xác thực Windows bằng Bayes phân tầng và báo cáo "empirical evidence of alert reduction" trên dữ liệu một doanh nghiệp lớn, chưa bình duyệt [46].

Các detection lệch chuẩn mà brief nêu đều quy về một khoá tổ hợp có asset, và mỗi khoá cần một tập "đã biết" trong profile:

| Detection lệch chuẩn | Khoá tổ hợp | Tập "đã biết" trong profile | Bằng chứng OCSF 1.9.0 |
|---|---|---|---|
| Dịch vụ mới lắng nghe | (asset, port, proto, product) | `asset_service` | 5040 LISTEN, 4001 Listen/`initiator_id`, 201004 |
| Phần mềm mới trên server | (asset hoặc role, product_key) | `asset_software` | 5020, 6002 Install, 1007 `process.file.product` |
| Binary/cặp cha–con hiếm | (asset hoặc role, parent, child, hash) | tập process theo role | 1007 |
| First-time logon | (user, asset) | cạnh user↔host | 3002 |
| Đích outbound mới | (asset, domain/ASN/app) | `asset_app_usage`, peer | 4001, 4002, 4003 |

**Nhận định:** giữ sẵn các tập này với first_seen/last_seen/count giúp rule chỉ so với profile, không phải quét lại 14–180 ngày log mỗi lần chạy, và đây chính là dữ liệu "dịch vụ/ứng dụng đang dùng" của case ở mục sau. Baseline theo role/peer quan trọng hơn baseline từng host, vì host mới sẽ báo mọi thứ là "lần đầu"; cần cold-start (host mới dùng baseline của role, hoặc tắt cờ first-time N ngày đầu, nhận diện bằng cờ kiểu `FirstTimeDeviceObservedInTenant`). Retention log của tenant phải dài hơn cửa sổ baseline, nếu không baseline bị cắt và FP tăng.

### Exposure và lỗ hổng: mẫu 5 mức của Cisco, và "không biết" khác "không có lỗ hổng"

Mẫu lâu đời và rõ nhất là impact level của Cisco Secure Firewall, ghép intrusion event với network map (host, service đang mở, OS) và lỗ hổng đã map [11]. **Vulnerable** khi host "is in the network map, and a vulnerability is mapped to the host"; **Potentially Vulnerable** khi port "is running a server application protocol"; **Currently Not Vulnerable** khi port không mở hoặc host không dùng giao thức đó; **Unknown Target** khi host thuộc mạng giám sát nhưng không có trong map; **Unknown** khi cả hai host ở ngoài. Docs còn ghi host thêm vào map từ NetFlow không có OS nên "the system cannot assign Vulnerable" [11]. Google YARA-L kéo `$asset_context.graph.entity.asset.vulnerabilities.severity` vào `outcome` và cộng 10/5/1 điểm cho HIGH/MEDIUM/LOW [32]; Defender có sẵn `ExposureLevel` và `IsInternetFacing` để lọc trong custom detection, còn `ExposureGraphNodes.NodeProperties` là JSON "unstructured" chứa insight như vulnerable to RCE [1][47].

**Nhận định:** profile cần đủ ba thứ để làm điều kiện kiểu Cisco: service đang mở (port/proto/app protocol, sản phẩm, version, last_seen), OS/sản phẩm có khoá CPE, và lỗ hổng mở theo asset. Ghép theo CVE (signature IDS có CVE khớp CVE trên asset) chính xác hơn ghép theo port; ghép theo port/app protocol chỉ cho "potentially vulnerable". Hạ ưu tiên ("Currently Not Vulnerable") chỉ an toàn khi dữ liệu service còn tươi, vì vậy cách dùng an toàn là **điều chỉnh ưu tiên**, không chặn alert. Host chỉ thấy qua flow sẽ không có OS và phải mang trạng thái "Unknown", đây là gap thật của dữ liệu thụ động.

### Coverage-aware: ma trận asset × nguồn cho biết rule nào câm trên asset nào

Ngôn ngữ chuẩn để khai báo "rule cần dữ liệu gì" đã có. ATT&CK v18 (2025-10) thay Detections bằng Detection Strategies, thêm Analytics và deprecate Data Sources: Enterprise có **691** Detection Strategies, **1.739** Analytics, **106** Data Components [12]; mỗi analytic khai platform và bảng log source theo Data Component, ví dụ AN0001 cần `Network Connection Creation (DC0082)` qua `AWS:VPCFlowLogs` [43]. Splunk security_content có file `data_sources/*.yml`, ví dụ `sysmon_eventid_1.yml` liệt kê `mitre_components`, `source`, `supported_TA` và danh sách `fields`, và detection tham chiếu `data_source: [Sysmon EventID 1, Windows Event Log Security 4688, CrowdStrike ProcessRollup2]` [13]. Elastic có `related_integrations` và `required_fields`, nhưng theo issue của đội docs hai field này "informational and don't affect execution" (trích đoạn) [48]. DeTT&CT chấm chất lượng nguồn theo 5 chiều, trong đó **device completeness** là "if the required data is available for all devices", thang 1 = 1–25% đến 5 = 100% [14]. Về quy mô vấn đề, CardinalOps tuyên bố SIEM doanh nghiệp chỉ phủ **21%** kỹ thuật ATT&CK (báo cáo 2025-06, qua nguồn thứ cấp); đây là **tuyên bố vendor** [49].

**Nhận định:** coverage có hai cấp. Cấp tenant (DeTT&CT, CardinalOps) trả lời "tenant có nguồn X không"; cấp asset trả lời "asset này có nguồn X, đủ field, gần đây không", và đây là phần chưa vendor nào làm. Profile cần ma trận asset × nguồn, mỗi ô là (`metadata.product`, `metadata.log_source`, `class_uid`) → last_seen, volume, tỉ lệ field bắt buộc được điền [50]. Join ma trận này với khai báo nguồn của rule cho ra "rule X câm trên N asset của role Y", và cũng cho device completeness theo role. Cờ kỳ vọng kiểu Splunk là nửa còn lại: không có `is_expected` thì không có rule vắng mặt.

### Chỗ join: khoá ổn định lúc ingest, tập động lúc rule chạy, snapshot lúc alert

Cả ba chỗ đều có vendor dùng. Google enrich lúc ingest: aliasing gộp hostname, `asset_id`, MAC vào một asset (IP chỉ dùng khi thiếu `asset_id`), lấy "the entity whose validity interval intersects with the event time", có lookback **5 ngày** cho dữ liệu đến trễ và dưới **1%** event lỡ pass đầu được xử lý lại [51]; lúc rule chạy, event chỉ join khi timestamp nằm trong `entity.metadata.interval` [3]. Elastic chụp ngữ cảnh lúc tạo alert: khi entity có criticality, "all subsequent alerts related to that entity are enriched with its criticality level", và khi xem risk phải kiểm "the entity's criticality level from the time the alert was generated" [52]. Sentinel join lúc rule chạy với watchlist refresh 12 ngày [7], còn `DeviceInfo` của Defender giữ mọi bản cập nhật nên join được theo thời gian event [1].

**Nhận định:** cách phối hợp đề xuất trên OCSF có ba tầng. (1) Lúc ingest chỉ ghi khoá ổn định `asset_uid` (resolve theo tenant và validity interval) cùng vài thuộc tính ít đổi (role chính, env, criticality) vào `enrichments[]` của base event, object này có sẵn `name`, `value`, `data`, `provider`, `created_time` [53][54]. (2) Lúc rule chạy, join các tập động (service, phần mềm, lỗ hổng mở, baseline, coverage) từ bảng profile có lịch sử, **theo giờ event** chứ không theo "bây giờ", để backfill không sai và asset vừa vá không bị coi là chưa từng có lỗ hổng. (3) Lúc tạo alert, chụp snapshot ngữ cảnh đã dùng vào alert, và nếu profile đổi thì hiện "giá trị hiện tại khác lúc alert". Độ trễ ngữ cảnh cấp ngày (watchlist 12 ngày, IdentityInfo resync **14 ngày** [10]) là bình thường ở vendor lớn, nên profile nên công bố độ tươi từng thuộc tính để rule biết khi nào không được tin nó.

## Sau detection: profile quyết định alert có lành tính không, lan tới đâu, xử lý được bằng gì

### Triage: phần lớn alert là benign trigger, chỉ ngữ cảnh môi trường và thay đổi gần đây gỡ được

Alahmadi, Axon và Martinovic (USENIX Security 2022) phỏng vấn **21** practitioner ở **7** SOC. Câu "99% false positives" là lời một người được phỏng vấn, và bài kết luận phần lớn là "benign triggers and not necessarily a measurement of the performance of the technology itself": alert đúng kỹ thuật (khớp signature, ví dụ "vulnerable java version") nhưng tổ chức chọn bỏ qua [15]. **58%** người tham gia xử lý alert dựa trên "awareness of regular network activity", **47%** dựa trên severity, **35%** theo lỗ hổng mới công bố. Ngữ cảnh asset analyst cần là "the network topology and devices, what these devices are used for, and their location and owner", ví dụ "knowing an asset is a Windows machine helps when receiving an alarm for a Linux signature"; thay đổi hợp lệ không báo SOC là nguồn benign trigger, và MSSP phải hỏi ngược khách hàng "this server has gone quiet, have you changed it?" [15]. Kokulu và cộng sự (CCS 2019, n = 18) thấy **71,43%** analyst và **60%** manager không nắm toàn bộ cấu hình mạng, với câu "We do not have a full asset inventory, that is a big constraint (for fast response)" [55]. NIST SP 800-61r3 đưa điều này vào khuyến nghị: DE.AE-07 R1 "Integrate up-to-date CTI and other contextual information (e.g., asset inventories) into adverse event analysis", và RS.MA N2 liệt kê "asset criticality, functional impact…" trong yếu tố đánh giá rủi ro để triage [56].

**Nhận định:** triage dùng sáu khối của profile: định danh và loại (OS, device type, IP/MAC trong cửa sổ thời gian), role và criticality, owner/BU để liên hệ, vị trí mạng và exposure, trạng thái kỳ vọng so với quan sát (dịch vụ/phần mềm kỳ vọng theo role, giờ hoạt động), và **thay đổi gần đây** (phần mềm mới, dịch vụ mới lắng nghe, owner/role đổi, asset im lặng). Khối cuối là thứ Alahmadi nêu rõ nhưng vendor ít đưa lên flyout. Với MSSP, profile còn phải ghi khách hàng đã chia sẻ nguồn context nào (CMDB, change calendar) và thiếu gì, vì "the more they share, the better a job we can do" [15]. Không có nghiên cứu bình duyệt nào đo thời gian triage có và không có ngữ cảnh asset; hai nghiên cứu trên đều định tính, mẫu nhỏ.

### Điều tra: quan hệ theo thời gian, nhóm cùng phần mềm/CVE, và "reach" tới critical asset

NIST 800-61r3 yêu cầu "Determine the sequence of events … and which assets and resources were involved in each of those events" (RS.AN-03) và tìm IOC "on both the assets known to be targeted and other potential targets" (RS.AN-08); ID.AM-05 nhấn mạnh biết "the dependencies between those and other assets" [56]. Microsoft đi xa nhất: blast radius trong Defender XDR "generates an interactive graph showing possible propagation paths from the selected node to predefined critical targets", tối đa **7 hops**, top 8 path, và chính docs cảnh báo "If you don't … fully define critical assets, blast radius graphs won't fully represent your environmental risks" [57]; attack path on-prem dừng khi chạm "End Game assets (Domain Admins, Enterprise Admins, Administrators, or Domain Controllers)" [58]. Elastic dùng prevalence (số alert cùng giá trị field) làm lối vào Timeline [59].

**Nhận định:** điều tra cần ba loại truy vấn trên profile mà OCSF không trả lời trực tiếp: quan hệ theo thời gian (user↔host từ 3002, host↔host từ 4001, process↔host từ 1007); nhóm asset cùng thuộc tính (cùng `product_key`/version từ 5020, cùng CVE từ 2002, cùng IOC từ `2004.evidences[]` và `observables[]`); và đường tới critical asset. OCSF có `finding_info.attack_graph` và `resource_details.resource_relationship` để *chở* đồ thị do producer tính, nhưng không có nơi lưu đồ thị bền vững [23]. Chỉ với log thụ động, đồ thị dựng được từ quan sát (ai đăng nhập vào đâu, host nào nói với host nào), không từ cấu hình quyền, nên nên gọi là "reach quan sát được" chứ không phải attack path. Prevalence theo tenant là truy vấn rẻ nhất và cần chỉ mục trên observable của 1007, 4001, 4003 và `2004.evidences`.

### Phản ứng: khả năng phản ứng theo agent hiện có, chính sách theo role và criticality

NIST RS.MI N1 cho phép chọn containment theo "risk evaluation factors in RS.MA" (gồm criticality) và theo **thời hạn** biện pháp ("an emergency workaround that must be removed within hours, a temporary workaround to be removed within two weeks, or a permanent solution"), còn R1 yêu cầu cho phép handler chọn tay thay hoặc bổ sung cho tự động [56]. Microsoft automatic attack disruption cho loại trừ user (service accounts, emergency admin), device group (Full / Semi cần duyệt / No automated response) và dải IP hạ tầng, có dynamic tag dựng từ thuộc tính thiết bị để tắt riêng từng control, kèm cảnh báo "Excluding assets from automated responses isn't recommended" [40]. Từ 2025, containment cho DC, DNS, DHCP là "device role-based": MDE "limit[s] only specific network functionalities and interfaces used for malicious activity" để "Key network functions are preserved", và có containment IP cho "unmanaged or undiscovered devices" [60]. Cortex XSOAR playbook "Port Scan - Internal Source" chỉ tự cô lập khi severity critical và endpoint không nằm trong `WhitelistedHostnames`, ngược lại chờ duyệt [41]. Alahmadi ghi nhận "most SOCs want to avoid any automated decision that could result in business disruption" [15].

**Nhận định:** profile cần khối **khả năng phản ứng** (có EDR quản lý được không và agent thấy lần cuối khi nào, asset nằm sau firewall/NAC nào, user khoá được ở IdP nào, có backup không), suy từ `agent_list[].type_id` (1 EDR, 3 Backup & Recovery), `is_backed_up`, `device` của log firewall và `3002.service` [30]. Từ đó suy ra hành động khả dụng: isolate bằng EDR, chặn IP/MAC ở firewall/NAC, disable account ở IdP, hoặc chỉ báo owner; đây là bản thụ động của phân biệt managed/unmanaged mà Microsoft dùng. Khối **chính sách phản ứng** gắn theo role/criticality/tag (ví dụ `role:domain-controller` → không cô lập toàn phần, phải duyệt), có lý do, người duyệt và hạn theo RS.MI N1. Kết quả phản ứng ghi ngược qua `7001` Remediation Activity (activity 1 Isolate, 3 Restore) thành trạng thái tạm "đang cô lập từ … đến …" mà ca sau cần thấy [42].

### Báo cáo và vòng phản hồi: verdict và ngoại lệ có hạn đều gắn rule, chưa ai ghi ngược vào profile

Vendor đều có verdict ba nhánh. Defender XDR có True positive / Informational, expected activity (security testing, line-of-business application, confirmed user activity) / False positive (not malicious, not enough data) [61]; Sentinel có `BenignPositive`, `FalsePositive`, `TruePositive`, `Undetermined` kèm reason như `SuspiciousButExpected`, `IncorrectAlertLogic` [62]. Suppression có hạn cũng phổ biến: automation rule của Sentinel có **Expiration date** cho "planned, time-limited activities such as penetration testing", và khi tạo rule từ incident hệ thống "uses all the available entities in the incident as conditions … and suggests an expiration date" [16]; exception của Elastic có expiration tuỳ chọn và có thể đóng mọi alert khớp [17]. NIST yêu cầu "Tune the continuous monitoring technologies to reduce false positives and false negatives" (DE.CM R2) và cập nhật inventory khi asset thay đổi (ID.AM-08) [56]. OCSF 1.9.0 chở được verdict: base `finding` khai profile `incident`, nên mọi Finding kể cả 2004 có thể mang `verdict_id` (1 False Positive, 2 True Positive, 5 Benign, 6 Test, 7 Insufficient Data…), `evidences[].verdict_id` dùng cùng enum ở mức từng evidence, và `finding.status_id` có **3 Suppressed** [38][37][63].

| Verdict vendor | `verdict_id` OCSF | Hành động vào profile (**Nhận định**) |
|---|---|---|
| Defender TP; Sentinel `TruePositive` | 2 True Positive | Cập nhật lịch sử detection; xét lại criticality/exposure |
| Defender "expected activity: security testing" | 6 Test | Ngoại lệ có hạn theo asset/tag (pentest window) |
| Defender "line-of-business app / confirmed user activity"; Sentinel `BenignPositive` | 5 Benign | Đề xuất thêm kỳ vọng vào profile asset/role, qua hàng chờ duyệt |
| Defender FP "not malicious"; Sentinel `FalsePositive` + `IncorrectAlertLogic` | 1 False Positive | Sửa rule, không sửa profile |
| Defender "not enough data"; `Undetermined` | 7 Insufficient Data / 0 | Đánh dấu gap coverage trên asset |

**Nhận định:** tách 5/6 khỏi 1 chính là tách benign trigger khỏi false alarm theo Alahmadi, và hai loại dẫn tới hai hành động khác nhau. Vòng phản hồi vào profile nên đi theo bốn đường: (1) lịch sử entity × rule × verdict (ví dụ "rule X trên role scanner: 40 Benign / 0 TP trong 90 ngày" là đề xuất suppression có bằng chứng); (2) verdict Benign/Test sinh đề xuất thuộc tính kỳ vọng cho asset/role; (3) ngoại lệ có phạm vi (asset, role, tag, tenant), lý do, người duyệt, `expires_at`, audit và hàng review khi sắp hết hạn; (4) sửa profile khi verdict lộ dữ liệu sai (alert Linux trên máy Windows cho thấy OS sai). Ngoại lệ không có class OCSF riêng nên phải là object của kho entity; khi suppress vẫn nên phát 2004 với `status_id` = 3 để đo khối lượng bị suppress theo asset. Báo cáo sau incident (NIST ID.IM-03) cần profile trả lời asset nào bị ảnh hưởng, criticality và owner, asset nào cùng phần mềm/lỗ hổng đã được kiểm, và chỗ mù telemetry nào làm chậm phát hiện, mục cuối nối thẳng về coverage-aware detection.

## Case: xác định thiết bị, dịch vụ, ứng dụng là bước suy diễn ba bảng có bằng chứng

Case này là một use case của profile chứ không phải mục tiêu riêng: `asset_service` nuôi scoping (role DC suy từ service 88/389/445), baseline ("service mới lắng nghe"), exposure-aware detection (service nào đang lộ, version nào) và triage ("máy này là web server nginx"); `asset_software` nuôi join CVE và "phần mềm mới trên server"; `asset_app_usage` nuôi "đích outbound mới" và shadow IT.

### OCSF 1.9.0 rải bằng chứng ra khoảng 25 class, không có đơn vị "service instance"

Bảng dưới gom các chỗ chính. Cột độ tin là **Nhận định** theo bản chất nguồn (khai báo/agent > runtime > giao thức có định danh > port), chưa có số đo.

| Mục tiêu | Class | Field chính | Độ tin / hạn chế |
|---|---|---|---|
| Thiết bị | 5001 Device Inventory Info | `device.{type_id,os.{type_id,version,cpe_name},hw_info,vendor_name,model,is_managed,first_seen_time}` | Cao; `type_id` chỉ 15 giá trị, không có Printer/Camera/PLC [22] |
| Thiết bị | mọi class có profile `host` | `device.*`, `device.agent_list[]` | Cao với EDR; tuỳ mapper điền đủ `os` [30] |
| Thiết bị | mọi class | `metadata.product`, `metadata.reporter`, `metadata.loggers[].device` | Sản phẩm/thiết bị ghi log; reporter có thể là collector [50] |
| Thiết bị | 4004 DHCP | `src_endpoint.{mac,hostname,domain,ip}`, `lease_dur` | Cao cho binding MAC↔IP↔hostname; **không có chỗ** cho option 55/60/61 [64] |
| Thiết bị/ứng dụng | Network | `mac_vendor` (1.8.0), `http_request.user_agent`, `ja4_fingerprint_list`, `network_endpoint.fingerprints` (1.8.0) | Thấp–TB; UA là chuỗi tự do; privacy MAC làm sai OUI [26][65] |
| Thiết bị | profile `container`, `load_balancer`, `network_proxy` | `container.image`, `load_balancer.dst_endpoint`, `proxy_endpoint` | Thiếu LB thì `dst_endpoint` có thể là VIP [66] |
| Dịch vụ | 4001 Network Activity | `activity_id` 7 Listen; `initiator_id` (1.9.0) thay `is_src_dst_assignment_known` | Listen hiếm (chỉ khi EDR phát); dữ liệu trước 1.9 thiếu hướng [25] |
| Dịch vụ | Network | `app_protocol_name` (1.8.0, tên IANA) | TB–cao; chỉ giao thức, không sản phẩm [67] |
| Dịch vụ | 5001 | `network_interfaces[].open_ports[]` (`port`, `protocol_name`, `protocol_num`) | Port, không tên sản phẩm hay PID [6] |
| Dịch vụ | 5040 Live Evidence Info | `query_type_id` 7 + `tcp_state_id` LISTEN; 11 Service → object `service` mỏng (`name`, `uid`, `version`), **không phải** `win_service`; 15 Startup Item | Cao (truy vấn OS) nhưng `service` không có binary/port/state [68] |
| Dịch vụ | 201004 Windows Service Activity | `win_service.{name,service_file,service_start_type_id,service_start_name}`, `prev_win_service` (1.9.0) | Cao, chỉ Windows [69] |
| Dịch vụ (Linux/macOS) | 1006, 5040 | `job.type_id` 3 Systemd / 4 Launchd; `startup_item.{type_id,run_state_id}` | TB; extension linux/macos chỉ thêm uid/gid; cgroup→unit chưa có (PR #1725 mở) [70][71] |
| Dịch vụ | 4002, 4007, Network `tls` | `http_response.http_headers[name=Server]`; `server_hassh`; `tls.certificate.{subject,sans}`, `ja4` type 2 JA4Server | TB; không có field `server`; TLS 1.3 che certificate [72][73][74] |
| Dịch vụ | 4005 RDP, 4006 SMB, 4009 Email, 4008/4013 | `protocol_ver`, `dialect`, `banner`, `stratum_id` | TB; **4009 extends `base_event`**, không có `tls`/`ja4`/`app_protocol_name` [75] |
| Dịch vụ (cloud/DB) | 6003, 4001 VPC Flow, 6005 | `api.service.name`, `network_endpoint.svc_name`, `database.type_id` | Cao cho cloud; `database.type_id` là mô hình dữ liệu, không có "PostgreSQL" [76] |
| Phần mềm đã cài | 5020 Software Inventory Info | `sbom.package`, `sbom.software_components[]`; `package` **deprecated từ 1.4.0**; `product` | Cao; hai đường cùng tồn tại [77][78] |
| Phần mềm | 2002, 5004, 6002 | `affected_packages`; `kb_article_list`; `application` (1.9.0) thay `app` | 2002 chỉ phủ phần mềm có CVE [33][79] |
| Đã chạy | 1007, 1005, 1002 | `process.file.{product,company_name,version,internal_name,hashes,signatures}` | Cao cho "đã chạy"; phụ thuộc mapper có giữ VERSIONINFO [80] |
| Dùng qua mạng | Network, 4002, 4003, 3002 | `app_name` (nhãn DPI/NBAR), `tls.sni`, `url.{hostname,category_ids}`, `query.hostname`, `actor.application` (1.9.0) | TB; `app_name` là từ vựng riêng vendor; `category_ids` là hạng mục website [81][82] |
| Mọi mục tiêu | mọi class | `unmapped`, `raw_data`, `enrichments[]`, `observables[]` | `unmapped` không schema, khác theo mapper [53] |

PR #1466 thêm `open_ports` ở 1.6.0 với lời hứa "Down the roads, we can also tie in the services that are listening on those ports, in the same `port_info` object", nhưng đến 1.9.0 `port_info` vẫn chỉ có ba field [6][83]. PR #1702 (1.9.0) gỡ nhầm lẫn Application/Product: `6002.app` và `actor.app_name` bị deprecated, còn "The `app_name` usage in `Network` is unchanged - there it is a DPI/NBAR traffic classification label, not an application entity" [82].

### Tám kiểu phân tán quyết định pipeline phải làm gì

| Kiểu phân tán | Ví dụ trong OCSF 1.9.0 | Hệ quả cho pipeline (**Nhận định**) |
|---|---|---|
| 1. Một sự thật ở nhiều class | "OpenSSH 8.9 trên 22/tcp" có ở 5020, 1007 (`sshd`), 5040 LISTEN, 1006 Systemd, 4007 (`server_hassh`), 4001 (`app_protocol_name = ssh`), 2002 | Gộp theo (asset, port, proto) và `product_key`, giữ một dòng bằng chứng mỗi nguồn |
| 2. Một host nhiều vai trò theo đường dẫn | `device`, `src/dst_endpoint`, `observation_point`, `proxy_endpoint`, `load_balancer.dst_endpoint`, `metadata.reporter`, `resources[]`; VPC Flow đổi chỗ `instance_id` theo `flow_direction` [84] | Extractor theo đường dẫn, biết đường nào là "asset của event" |
| 3. Định danh lệch | `device.uid`, `uid_alt`, `hw_info.uuid`, `os_machine_uuid`, `agent_list[].uid`, `mac`, `hostname`/`name`; phần mềm: `purl`, `cpe_name`, `product.uid`, `file.hashes` | Entity resolution cho cả asset lẫn sản phẩm |
| 4. "service" và "app" đa nghĩa | `service` = dịch vụ cloud, gateway xác thực, service OS; `svc_name` hai nghĩa; Tenzir đặt banner SSH vào `agent_list` type 9 [85] | Quy tắc đọc theo (`metadata.product`, mapper), không chỉ theo ngữ nghĩa schema |
| 5. Deprecated và mới cùng tồn tại | `5020.package`→`sbom`, `tls.sans`→`tls.certificate.sans` (1.4.0); `is_src_dst_assignment_known`→`initiator_id`, `6002.app`→`application`, `actor.app_name`→`actor.application` (1.9.0) [86] | Path alias theo phiên bản, sinh từ `superseded_by` máy đọc được (1.9.0, #1707) |
| 6. Enum lẫn chuỗi tự do | Enum: `device.type_id`, `job.type_id`, `ja4_fingerprint.type_id`; tự do: `app_name`, `product.name`, `banner`, `http_headers[].value` | Catalog chuẩn hoá cho mọi chuỗi tự do |
| 7. Không có chỗ nên vào `unmapped` | DHCP option, Zeek `software.log`/`known_services.log`, cgroup, chi tiết giao thức chưa có class (issue #1384) [87][88] | Registry key `unmapped` quen thuộc theo `metadata.product` |
| 8. Chỉ trong mảng key-value | Header `Server`, `X-Powered-By` trong `http_headers[]`; version image trong `labels`/`tags` | Parser mảng header có danh sách tên cần tách |

Mapper thực tế làm lệch thêm. Mapper Zeek của Tenzir nhắm 1.9.0, ghi `conn.service` vào `app_protocol_name`, nhưng chỉ có mapper riêng cho `conn, dhcp, dns, ftp, http, rdp, smb_files, smtp, ssh, ssl, x509`; `software.log` và `known_services.log` rơi vào nhánh mặc định và mọi field chưa move đi vào `unmapped` [89][87]. **Nhận định:** `observables[]` không giúp gom phần mềm vì 1.9.0 không có observable type cho product, CPE, purl, service hay JA3/JA4 (JA3 chỉ gián tiếp qua type 30 Fingerprint); chỉ nên dùng nó để pivot theo IP, hostname, MAC, process, hash, user-agent [81].

### Nhận diện thụ động qua mạng: banner hơn fingerprint, fingerprint hơn DPI, DPI hơn port

| Kỹ thuật | Tín hiệu | Cho ra | Độ chính xác / giới hạn | Chỗ trong OCSF 1.9.0 |
|---|---|---|---|---|
| Zeek known_services / known_hosts | Responder đã bắt tay (SYN-ACK, history `h`) hoặc UDP có phản hồi; dedup (host, port) **1 ngày** [90] | Service (IP, port, proto, giao thức) | Mặc định chỉ host nội bộ; log lại mỗi ngày | Không có class "observed service"; gần nhất 5040/`open_ports` |
| Zeek software.log | `Server`→`HTTP::SERVER`, `X-Powered-By`→`APPSERVER`, banner SSH, DHCP option 60 [91][92] | Sản phẩm + version (kèm `unparsed_version` vì "version parsing doesn't always work reliably") | Chỉ log khi mới hoặc đổi version | Không có mapper riêng → `unmapped` |
| Banner/header cleartext | HTTP `Server`, SSH banner, DHCP option 12/60/81 | Sản phẩm, version | Dễ giả, nhưng thường đúng với thiết bị không cố che | `http_headers[]`; banner SSH và option 60 → `unmapped` |
| JA3/JA3S | Hash ClientHello/ServerHello | Họ client/server | Chrome xáo extension từ 2023-01, gần 15! hoán vị, JA3 phổ biến nhất của Chrome rơi mạnh [93] | `tls.ja3_hash`, `ja3s_hash` |
| JA4+ | JA4, JA4S, JA4H, JA4X, JA4SSH, JA4T/TS; mới hơn JA4D, JA4N | Họ implementation, client app, stack TCP | Chỉ JA4 là BSD-3; còn lại FoxIO License 1.1, bán trong sản phẩm cần OEM license [94] | `ja4_fingerprint_list[]` type 1–9; JA4D/JA4N phải dùng 99 Other |
| HASSH | MD5 thuật toán `SSH_MSG_KEXINIT` | Implementation SSH bất kể banner (lộ honeypot giả OpenSSH) | Repo Salesforce archive 2025-05 [95] | `client_hassh`/`server_hassh`; `fingerprints` algorithm_id 20 |
| DHCP fingerprint (Fingerbank) | Option 55 (thứ tự), option 60, MAC, hostname, UA, p0f… | Cây loại thiết bị, OS, `score` 0–100 [96] | Cisco lưu ý "can be duplicated by multiple device types" | Option 55/60 → `unmapped`; score không có chỗ |
| p0f, TTL, mDNS/SSDP/LLDP/CDP | TCP SYN, broadcast tự khai | OS, loại thiết bị | Laštovička 2023: p0f không nhận OS mới, khó tái lập [97] | Không có field/class → `unmapped` |
| App-ID / NBAR2 | Signature, decode, heuristic | Ứng dụng mạng | PAN khuyên chặn QUIC, nếu không phiên Chrome→Google chỉ là `quic` [98][99] | `app_name`; category/risk → `unmapped` |
| Defender device discovery (Basic) | ARP, CDP, DHCP, LLDP, mDNS, NBNS, SSDP, TCP SYN… do máy đã onboard nghe | Thiết bị unmanaged | Microsoft tự mô tả "limited visibility" [100] | (nguồn ngoài OCSF) |

Số độ chính xác có nhưng khó so sánh. Anderson và McGrew (Cisco, một mạng riêng) kết hợp TLS + TCP/IP + HTTP qua nhiều session, đạt **99,4%** ở major version OS và **97,5%** ở minor [101]. Bài FT-Transformer 2025 trên IPFIX đạt **95,04%** ở mức family, **79,09%** major, **68,52%** minor trên DAT2, và cảnh báo so sánh khó vì "the lack of accuracy metrics or detailed evaluation data" [102]. Số của vendor thương mại chỉ là quy mô knowledge base tự công bố: Forescout >11 triệu thiết bị, >7.700 vendor/model (datasheet 2022), Armis 80 rồi 230 triệu thiết bị tuỳ thời điểm, đều là **tuyên bố vendor** [103][104]. Giới hạn nền tảng đang nặng thêm: ECH đã là RFC 9849 (2026), và theo Cisco khi có ECH firewall chỉ thấy outer SNI (thường là tên CDN chung), Encrypted Visibility Engine vẫn nhận ra process client nhưng "does not discover the actual target of the connection" [105][106].

**Nhận định:** thứ tự tin cậy cho bằng chứng mạng là: banner/header có tên và version > fingerprint handshake tra DB (ra họ implementation, hiếm khi ra version) > DPI App-ID/NBAR2 (phụ thuộc SNI/DNS khi không decrypt) > chỉ port/vai trò responder. Mỗi kết luận nên lưu nguồn, DB, version DB và score. Khi có ECH/CDN, `tls.sni` và `app_name` chỉ là bằng chứng *app usage* phía client, không dùng để suy service của IP đích ngoài Internet; sau NAT, fingerprint client gắn với IP public là tập của nhiều host. Về license FoxIO, trường hợp chỉ đọc giá trị JA4+ có sẵn trong log mà nguồn đã sinh ra nên hỏi pháp chế, chưa có nguồn làm rõ.

### Bằng chứng host: inventory chứng minh có mặt, runtime chứng minh được dùng, socket có PID chứng minh service

| Nguồn | Thấy gì | Điểm mù | Đích OCSF 1.9.0 |
|---|---|---|---|
| MDVM | Software inventory cập nhật "every three to four hours", có Software Evidence (registry/disk) [107][108] | Linux "only lists software installed using native package managers"; mặc định chỉ hiện phần mềm có CPE; tự đổi version (SQL Server `13.0.7016.1` → `13.3.7016.1`) | 5020; `EndOfSupportDate`, đường dẫn evidence → `unmapped` |
| Tenable 20811/22869, 45590 | Registry Uninstall / SSH enumeration; CPE khớp hoặc "computes the best available CPE" [109] | Danh sách dài gồm cả app đi kèm OS | 5020, 2002 |
| Qualys CSAM | Taxonomy 2 cấp, tách market version / version / update / edition [110] | Bản ghi `UNKNOWN` = chưa chuẩn hoá | 5020 |
| Axonius | Preferred Name từ catalog, "Generated CPE (Axonius)" [111] | Vendor/Publisher "interchangeable" do parse không nhất quán | 5020 |
| Wazuh Syscollector | packages, ports, services, hotfixes [112] | Ports: `process.name/pid` **chỉ Windows/macOS** | 5020; 5040 hoặc `open_ports` |
| osquery | `programs`, `deb/rpm_packages`, `apps`, `python/npm_packages`, `listening_ports` (có PID, path), `systemd_units`, `launchd` [113] | `programs` chỉ là Windows Installer | 5020; 5040 type 7/15 |
| Sysmon 1/6/7, EDR | Image, hash, `FileVersion`, `Product`, `Company`, `OriginalFileName`, chữ ký [114] | Event 3 và 7 tắt mặc định | 1007, 1005, 1002 |
| Windows 7045/4697 | Service mới: `ImagePath`, `StartType`, `AccountName` | Là "vừa cài", không phải "đang chạy" | 201004 Create |

Mapper quyết định bằng chứng có sống sót qua chuẩn hoá hay không: Tenzir (nhắm 1.9.0) map `FileVersion`, `Company`, `OriginalFileName`, `Product` của Sysmon 1 vào `process.file.{version,company_name,internal_name,product.name}` [115], còn mẫu AWS Security Lake (OCSF v1.0.0) **không map** `FileVersion`, `Product`, `Company`, `Hashes`, kể cả vào `unmapped` [116]. Tenzir map Intune `detectedApps` vào 5020 với `device` là placeholder "Microsoft Intune managed devices", vì endpoint này "reports aggregate software inventory, not a specific device" [117]. Một đánh giá độc lập (benchmark tự dựng, dữ liệu tổng hợp) thấy mapper Zeek conn của Tenzir 6.0.0 (OCSF 1.8.0) sai `activity_id` ở **83%** bản ghi và để `service` vào `unmapped` [118]. Schema cũng có chỗ vướng: `sbom` bắt buộc **một** `package` cùng `software_components`, trong khi một host có hàng trăm gói; ví dụ `cpe_name` trong dictionary là CPE 2.2 (`cpe:/a:apple:safari:16.2`); và toàn dictionary 1.9.0 không có field cho install time, EOL hay evidence path [78][81].

**Nhận định:** lưu tách `installed` (inventory) và `last_executed` (runtime), vì portable binary có thể chạy mà không có trong registry. Bằng chứng service mạnh nhất trên host là socket LISTEN có PID (osquery `listening_ports`, Wazuh trên Windows/macOS) nối process → file → product; không có PID thì chỉ còn (port, proto) như bằng chứng mạng. Extractor phải đọc cả ba kiểu của 5020 (`package`, `sbom.package`, `sbom.software_components[]`), parse cả CPE 2.2 lẫn 2.3, và có kiểm tra chất lượng theo nguồn (ví dụ tỉ lệ 1007 có `process.file.product`).

### Khoá sản phẩm: (vendor_norm, product_norm) cộng bảng alias, CPE chỉ là thuộc tính dẫn xuất

Không định danh nào đủ dùng một mình. NVD gỡ feed legacy (CPE Dictionary, CPE Match 1.0) sau **20/8/2025** để chuyển sang file theo API 2.0 [119]. Đổi tên vendor không được backfill: `arm:mbed_tls` → `trustedfirmware:mbed_tls` khiến tới 5/6/2026 không CPE nào tìm đủ 18 CVE, và NVD backfill "slowly or not at all" [120]. purl thành chuẩn ECMA-427 (12/2025) nhưng "does not include any specific PURL type definitions", và chỉ hợp với gói của package manager [121]. SWID thì NIST IR 8060 vẫn ở bản 2016 [122]. Vendor nào cũng dựa vào catalog riêng, và Flexera coi luật map raw evidence → Technopedia là "our intellectual property" [123].

**Nhận định:** khoá nội bộ nên là `product_key = (vendor_norm, product_norm)`, thêm `edition`/`component` khi cần (Qualys tách Client/Server). Version lưu ba mức: `version_raw`, `version_norm` so sánh được (epoch:version-release cho rpm, quy tắc dpkg cho deb, tuple số cho PE `FileVersion`) và `market_version`. Bảng alias trỏ về `product_key`, mỗi alias một loại: `cpe` (vendor:product, bỏ version, kèm chuỗi deprecated), `purl` (bỏ version), `process_name`, `OriginalFileName`, `pe_product + pe_company`, `bundle_id`, `msi_upgrade_code`. App-ID/NBAR và SaaS là trục *ứng dụng mạng*, đi vào catalog app riêng của `asset_app_usage` chứ không ép chung khoá với phần mềm cài. Alias theo `OriginalFileName` + `Company` + chữ ký đáng tin hơn `process.name`, vì tên file dễ đổi.

### Ghép bằng chứng: service là (IP, port, proto) mà responder đã trả lời, và passive không bao giờ "đủ"

Quy tắc nền mà cả học thuật lẫn công cụ dùng là "even just the presence of a positive response to a connection request (SYN-ACK) is sufficient evidence of a TCP service" [18], và Zeek cài nó thành `has_active_service()` (TCP ESTABLISHED/CLOSED/PARTIAL hoặc history `h`, UDP phải có phản hồi, DNS phải `resp$size > 0`, bỏ `ftp-data`) [90]. Bartlett, Heidemann và Papadopoulos (IMC 2007, 38 subnet, khoảng 6.450 host sống) lấy union passive + active làm ground truth: sau 12 giờ passive chỉ thấy **19%** server, sau 18 ngày passive **71%** so với active **94%**, chỉ passive thấy **6,3%**; nhưng tính theo trọng số, passive "finds 99% of the client-weighted servers in 14 minutes", và passive "never levels off" vì host transient đổi IP [18]. Khi chỉ có NetFlow/IPFIX không rõ hướng, ntop thừa nhận "only port-based heuristics can be used" và dấu hiệu client port < server port "not necessarily true, but it is true for known services" [124]. Role là tầng suy diễn thứ hai dựng trên service: Stamus ghi "Role is based on the services that the host has been observed to provide" và lưu first/last seen cho từng giá trị metadata (UA, TLS agent, login) [125]; Corelight Entity Collection tóm tắt hosts, services, software theo cửa sổ **15 phút**, mặc định chỉ mạng nội bộ [126]. Ở cấp quan hệ, Defender lưu `RegistryPaths`, `DiskPaths`, `LastSeenTime` cho từng (device, software) [108], runZero lưu first/last seen và phương thức phát hiện cho từng service, và tạo asset mới khi fingerprint thay đổi lớn [127]; không vendor nào trong mẫu công bố điểm confidence số cho một quan hệ software/service.

**Nhận định:** ba bảng suy diễn đề xuất, mỗi dòng là (quan hệ, nguồn), rồi tính dòng hợp nhất (`first_seen = min`, `last_seen = max`, `confidence` = max hoặc noisy-OR theo loại bằng chứng):

| Bảng | Khoá | Cột bằng chứng | Thang tin cậy (cao → thấp) |
|---|---|---|---|
| `asset_service` | (tenant, asset_uid, port, proto) | `app_protocol_name`, `product_key`, `version`, `detected_method{listen, socket_pid, handshake, banner, fingerprint, flow_heuristic}`, `evidence_ref` (`metadata.uid`), `source`, first/last seen, `seen_count`, `peer_count` | Listen/socket có PID trên host > handshake mạng có `initiator_id` + DPI xác nhận > banner/fingerprint > flow không hướng theo port + fan-in |
| `asset_software` | (tenant, asset_uid, product_key) | `raw_name`, `raw_vendor`, `version_raw/norm`, `evidence_type{package, registry, disk, process, service, vuln_scan, network_banner}`, `installed_at`, `last_executed`, `eol_date`, first/last seen | Inventory agent/scan có credential > runtime có chữ ký > lifecycle (6002, 201004) > banner mạng |
| `asset_app_usage` | (tenant, asset_uid hoặc user_uid, app_id) | `transactions`, `bytes_up/down`, `match_key{url, sni, dns, app_name, ip_range, idp, api}`, first/last seen | Log SaaS/IdP có định danh > URL proxy > SNI > `app_name` > DNS |

Vì passive bỏ sót server idle và không bao giờ bão hoà, `asset_service` không nên có trạng thái "đóng" chỉ vì vắng traffic; dùng `observed` / `not_recently_observed` với ngưỡng theo loại bằng chứng (Listen trên host ngắn, flow dài). Xung đột version giữa nguồn thì giữ mọi version như Axonius (`Unique Version Count`), ưu tiên nguồn host hơn banner, và cảnh báo khi hai nguồn cùng last_seen mà khác version [111]. Chất lượng nên đo theo tenant và theo `detected_method`: precision (quan hệ từ flow được 5040/4001 Listen xác nhận), recall trên tập asset có cả agent inventory, recall có trọng số client/flow theo Bartlett, time-to-detect, staleness và churn theo `metadata.product.name`; số rơi đột ngột thường là mất nguồn log chứ không phải service biến mất.

### SaaS discovery: domain hoặc App-ID tra catalog, gán về asset qua IP theo thời gian

Mọi sản phẩm đi cùng một luồng: parse log theo parser riêng từng nguồn → so domain/URL (hoặc IP nếu log không có URL) với catalog có điểm rủi ro → đếm user, IP, device, transaction theo app. Microsoft Defender for Cloud Apps so với catalog tự công bố "over 31,000 cloud apps" và "more than 90 risk factors" (**tuyên bố vendor**), phân tích lại bốn lần mỗi ngày, và mặc định "cannot discover apps that aren't in the catalog" [128]. Bảng nguồn của MDA cho thấy nhiều log firewall **không có URL** (Check Point, Cisco ASA, FortiGate, Juniper SRX, Palo Alto) và nhiều nguồn **không có username** [128]. Gán usage cho device cần agent: tích hợp MDE "provide user and device information for traffic activities", nhưng trên macOS network protection "only audits TCP connection close events, UDP protocols aren't covered" [129]. Custom app được khai bằng domain trước, IP sau nếu nguồn không có URL [130].

**Nhận định:** nguồn OCSF cho `asset_app_usage` xếp theo độ tin của khoá match: `6003` `api.service.name` và `3002` `service`/`dst_endpoint` của IdP (dùng thật, có định danh) > `4002` `url.hostname` từ proxy có URL đầy đủ kèm `user_agent` để tách client app với trình duyệt > `tls.sni` (mất tác dụng khi ECH) > `app_name` của firewall không có URL > `4003` `query.hostname` (ý định, không phải truy cập thật). Gán về asset bằng `src_endpoint.ip` tại thời điểm event qua chỉ mục IP→asset theo thời gian từ DHCP 4004; có NAT/proxy thì dùng `x_forwarded_for` hoặc log endpoint; log chỉ có user thì lưu user → app, không ép về asset. Catalog app giữ ba loại khoá (domain có wildcard, IP range, `app_name` theo từng vendor) và đánh dấu domain dùng chung (CDN, `*.amazonaws.com`) là "không đủ để kết luận app".

### Ví dụ: "máy X chạy nginx 1.24 trên 443"

Giả sử tenant có EDR Linux trên X, osquery, Zeek ở biên DMZ và scanner. Đây là ví dụ minh hoạ (**Nhận định**), không phải log thật.

| Bằng chứng | Class / field | `detected_method` | Đóng góp |
|---|---|---|---|
| Gói `nginx` version `1.24.0-2ubuntu7` | 5020 `sbom.package.{name,version,purl}` hoặc `package` (deprecated) | package | `asset_software(X, nginx/nginx)`, `version_norm` theo dpkg |
| Process `/usr/sbin/nginx`, cha systemd | 1007 `process.file.path`, `hashes`; 1006 `job.type_id` 3 | process | `last_executed`; xác nhận đang chạy |
| Socket LISTEN 0.0.0.0:443, PID của nginx | 5040 `query_type_id` 7, `tcp_state_id` LISTEN + `process` | socket_pid | `asset_service(X, 443, tcp)` độ tin cao nhất, nối product |
| Nhiều client nội bộ và Internet tới X:443, X là responder | 4001 `initiator_id` = 1, `dst_endpoint.port` 443, `app_protocol_name` = `ssl`/`http`; `src_endpoint.network_scope_id` = 2 | handshake | `peer_count`, cờ **internet-facing** có bằng chứng |
| Header `Server: nginx/1.24.0` | 4002 `http_response.http_headers[name=Server]` (Zeek software.log nếu có thì nằm `unmapped`) | banner | Xác nhận product/version từ mạng |
| Certificate, JA4S | `tls.certificate.{subject,sans}`, `ja4_fingerprint_list[type_id=2]` | fingerprint | Danh tính server, phát hiện đổi stack |
| CVE trên gói nginx | 2002 `vulnerabilities[].affected_packages[{name, version, fixed_in_version}]` | vuln_scan | Lỗ hổng mở theo asset |

Dòng hợp nhất `asset_service(X, 443/tcp) = {app_protocol: https, product: nginx, version: 1.24.0, internet_facing: true, confidence: cao, first_seen, last_seen}` phục vụ ba chỗ trước detection: role `web-server` để scope rule web; baseline để "service mới lắng nghe" không bắn khi nginx restart nhưng bắn khi X mở thêm 8443 do process lạ; và điều kiện kiểu Cisco: alert exploit nhắm vào nginx có CVE khớp 2002 → "Vulnerable", alert nhắm IIS vào X → "Currently Not Vulnerable" và hạ ưu tiên, *nếu* `last_seen` còn tươi. Sau detection, analyst thấy ngay "X là web server nginx lộ Internet, owner Y, vừa cài bản mới hôm qua (6002/5020 diff)", và truy vấn "asset nào khác chạy nginx 1.24" trả từ `asset_software`. Nếu X không có agent, chỉ còn 4001 + header + cert: `asset_service` vẫn có nhưng `confidence` thấp hơn, version chỉ từ banner, và OS ở trạng thái Unknown.

### Ví dụ: "user Y dùng Dropbox"

| Bằng chứng | Class / field | Khoá match | Ghi chú |
|---|---|---|---|
| Proxy ghi Y truy cập `www.dropbox.com` | 4002 `url.hostname`, `actor.user`, `src_endpoint.ip`, `http_request.user_agent` | domain | UA tách trình duyệt với client desktop |
| Firewall không có URL, nhãn App-ID của Dropbox | 4001 `app_name`, `dst_endpoint.ip` | app_name | Tên nhãn là từ vựng riêng vendor, map qua catalog |
| TLS SNI tới domain Dropbox | 4001 `tls.sni` | sni | Mất khi ECH |
| DNS hỏi domain Dropbox | 4003 `query.hostname` | dns | Chỉ là ý định |
| Process client Dropbox chạy trên máy của Y | 1007 `process.file.{product,company_name}` | (phần mềm) | Vào `asset_software`, không vào `asset_app_usage` |
| Đăng nhập SSO tới Dropbox doanh nghiệp | 3002 `service.name` từ IdP | idp | Phân biệt tài khoản doanh nghiệp |

`src_endpoint.ip` được resolve qua 4004 DHCP tại thời điểm event thành `asset_uid` của laptop Y, sinh `asset_app_usage(laptop, dropbox)` và `user_app_usage(Y, dropbox)`. Trước detection, cặp này là tập "đã biết" cho rule "upload lớn tới dịch vụ lưu trữ lần đầu" (Sentinel có sẵn `FirstTimeUserUsedApp` 180 ngày [10]); sau detection, nó trả lời "Y có thường dùng Dropbox không, từ máy nào, có qua SSO doanh nghiệp không". **Nhận định:** chỉ có DNS hoặc chỉ có SNI qua CDN thì không đủ kết luận, nên giữ ở độ tin thấp và không đưa vào allowlist.

## OCSF 1.9.0 thiếu gì, và extension nên thêm ở đâu

| Khoảng trống | Hệ quả cho profile/detection | Đề xuất (**Nhận định**) |
|---|---|---|
| Không có "service instance": `port_info` chỉ `port`, `protocol_name`, `protocol_num` [6] | Mỗi kho tự tổng hợp từ ≥ 6 nguồn | Mở rộng `port_info` (hoặc object `service_instance`) với `app_protocol_name`, `product`, `version`, `process`, `first/last_seen`, đúng hướng PR #1466 đã hứa [83] |
| `5040` Service trỏ `service` mỏng, không state/binary/port [68] | Không ghép service OS với socket | Thêm `process`/`file`/`port_info` vào `service` hoặc dùng `startup_item` kèm `win_service` |
| DHCP không có option 55/60/61/82 [64] | Tín hiệu loại thiết bị mạnh nhất nằm `unmapped` | Thêm `dhcp_options[]` hoặc `fingerprints` trên `src_endpoint` của 4004 |
| Banner SSH, header `Server`, p0f, mDNS/SSDP/LLDP không có field/class | Banner chỉ còn trong `http_headers[]` hoặc mapper tự đặt vào `agent_list` | Field `software_banner` trên `network_endpoint`; class discovery thụ động cho broadcast |
| Enum JA4 thiếu JA4D, JA4D6, JA4N, JA4LS [65] | Phải dùng 99 Other | Bổ sung enum |
| Không observable type cho product, CPE, purl, service, JA4 [81] | Không pivot "mọi event của phần mềm X" | Thêm observable type |
| Linux/macOS không có object systemd/launchd; cgroup→unit chưa có (PR #1725) [71] | Không gắn process với unit trên Linux | Theo dõi PR #1725 |
| Không có install time, EOL, evidence path; ví dụ `cpe_name` là CPE 2.2 [81] | `asset_software` thiếu "cài khi nào, hết support khi nào" | Thêm `install_time`, `eol_time`, `evidence_paths` vào `package`/`product` |
| `sbom` bắt buộc đúng một `package` [78] | Mapper chọn ba cách khác nhau | Cho phép `packages[]` trong 5020 |
| `device` không có criticality, tags, role; `endpoint.owner` hai nghĩa [20] | Criticality chỉ xuất qua `resource_details` | Extension `asset_context` (đã đề xuất ở report 2026-11-03) cộng `roles[]` có confidence |
| Không có class ngoại lệ/suppression, không có coverage | Vòng phản hồi phải ở ngoài OCSF | Giữ trong kho entity; xuất qua `enrichments[]` và `status_id` 3 Suppressed |
| `app_name` không có catalog; `url.category_ids` là hạng mục website [82] | Tên app không đồng nhất giữa vendor | Catalog app nội bộ, alias theo vendor |

## Khuyến nghị thiết kế và MVP

Toàn bộ mục này là **Nhận định**, rút từ các phần trên.

**Nguyên tắc dữ liệu.** Mọi thuộc tính suy diễn mang `source`, `confidence`, `valid_from/valid_to`, `last_seen`; mọi bảng profile có lịch sử để join theo giờ event; mọi khoá chứa tenant (`metadata.tenant_uid` phải bắt buộc dù OCSF chỉ để recommended). Extractor có lớp path alias theo phiên bản sinh từ `superseded_by`, và registry key `unmapped` theo (`metadata.product`, mapper).

**MVP 1: profile để rule chạy đúng chỗ và biết mình mù ở đâu.** Resolve `asset_uid` lúc ingest và ghi vào `enrichments[]`; `role[]` có confidence suy từ `asset_service` (DC từ 88/389/445 phục vụ nhiều client, DNS/DHCP server từ phía server của 4003/4004) cộng override thủ công kiểu "Auto"; xuất tập asset có tên cho rule/filter; ma trận coverage asset × (`metadata.product`, `class_uid`) với cờ kỳ vọng mặc định theo role (server → EDR, auth log, timesync); `asset_service` và `asset_software` từ các nguồn tin cậy cao (5040, 5020, 201004, 4001 có `initiator_id`); snapshot ngữ cảnh trên alert.

**MVP 2: profile để ưu tiên và lan rộng điều tra.** Lỗ hổng mở theo asset từ 2002 nối `product_key`; điều kiện impact 5 mức kiểu Cisco, chỉ nâng/hạ ưu tiên, có trạng thái Unknown; `asset_app_usage` từ proxy/firewall/IdP; bằng chứng mạng thụ động (banner, JA4, HASSH, DHCP từ `unmapped`) ở độ tin thấp hơn; tập "đã biết" theo role và peer cho các khoá lệch chuẩn, có cold-start; khối khả năng và chính sách phản ứng.

**MVP 3: vòng phản hồi.** Lịch sử entity × rule × verdict (map verdict vendor về `verdict_id`); đề xuất kỳ vọng từ verdict Benign/Test qua hàng chờ duyệt; ngoại lệ có phạm vi, lý do, người duyệt, hạn và review; báo "rule X câm trên N asset của role Y" và device completeness theo role; đo precision/recall/staleness/churn của ba bảng suy diễn theo `detected_method`.

## Các nguồn bất đồng ở đâu

**`verdict_id` có trên Detection Finding không.** Một note ghi `verdict_id` "chỉ có trên 2005 Incident Finding", note khác ghi profile `incident` được include vào base `finding`. Đọc lại schema 1.9.0: `finding.json` khai `profiles: ["incident"]`, profile này chứa `verdict_id`, `priority_id`, `assignee`, `ticket`; 2005 có sẵn các field đó như attribute riêng [38][37][131]. Vậy 2004 mang được `verdict_id` khi producer áp profile `incident`, nhưng đó là tuỳ chọn; consumer không được giả định mọi 2004 đều có.

**Bản thảo thảo luận và schema.** Bản nháp ban đầu coi `5020.package` và `tls.sans` là field bình thường, nhưng cả hai deprecated từ 1.4.0 (thay bằng `sbom` và `tls.certificate.sans`); cho `4009` Email mang `tls`/`ja4` trong khi class này extends `base_event`; cho 5040 Service dùng `win_service` trong khi nó trỏ object `service` mỏng; và bỏ sót `network_endpoint.fingerprints` (1.8.0) [86][75][68][26]. Report này theo schema gốc.

**Số liệu passive vs active.** Security Boulevard viết "active 29%, passive 6.3%, combined 65%" cho Bartlett 2007, tức đọc nhầm các cột "chỉ active", "chỉ passive", "cả hai"; paper gốc cho passive **71%**, active **94%** sau 18 ngày [18]. Tin paper gốc.

**FP có phải vấn đề lớn.** Kokulu (2019) thấy 15/18 người nói FP không phải vấn đề lớn, Alahmadi (2022) thấy alert áp đảo. Alahmadi giải thích sự lệch bằng benign trigger: analyst không coi alert đúng-nhưng-lành-tính là FP của tool [55][15]. Hai kết quả tương thích nếu tách hai khái niệm, và đó là lý do report đề nghị tách verdict 5/6 khỏi 1.

**Mapper Zeek của Tenzir.** Changelog hiện tại nói `conn.service` vào `app_protocol_name` [89], đánh giá độc lập thấy `service` rơi vào `unmapped` và `activity_id` sai 83% [118]. Hai nguồn đo hai phiên bản khác nhau (6.0.0/OCSF 1.8.0 so với bản nhắm 1.9.0), nên kết luận đúng là phải kiểm chất lượng mapper theo phiên bản, không tin mặc định.

**Quy mô catalog của Qualys.** Docs ghi "nearly 1700 publishers and over 65,000 software releases", một blog Qualys (qua nguồn thứ cấp) ghi 5.500 publisher và 300.000 release [110]. Không dùng con số nào làm căn cứ thiết kế.

## Kết luận và hàm ý

Điểm mới so với hai report trước là tách được thứ *làm cho profile phục vụ detection* khỏi thứ chỉ làm cho nó đầy đủ: tập có tên với độ tin và hạn (để scope), tập "đã biết" với first/last seen (để baseline), trạng thái "không biết" tường minh (để điều kiện exposure không hạ nhầm ưu tiên), cờ kỳ vọng cộng ma trận coverage theo asset (để biết rule câm), và lịch sử theo thời gian (để join đúng giờ event và để triage hỏi "gần đây đổi gì"). Phía sau alert, khoảng trống lớn nhất của thị trường là vòng phản hồi: vendor có verdict ba nhánh và suppression có hạn, nhưng chưa ai biến verdict Benign thành kỳ vọng của asset/role. Đây là chỗ sản phẩm đa tenant trên OCSF có thể khác biệt, vì MSSP thấy cùng một rule bắn benign trên nhiều tenant và có lý do để học theo role thay vì theo IP.

Với OCSF 1.9.0, hàm ý kiến trúc là coi OCSF là **lớp bằng chứng** chứ không phải lớp thực thể: profile là kho entity riêng, có ba bảng suy diễn `asset_service`/`asset_software`/`asset_app_usage` gom từ hơn chục class, path alias theo phiên bản, registry `unmapped` theo mapper, và xuất ngược vào event qua `enrichments[]`, vào finding qua `resources[]` và `verdict_id`. Chất lượng của case dịch vụ/ứng dụng phụ thuộc vào mapper nhiều ngang với thuật toán ghép, nên đo chất lượng theo nguồn và theo `detected_method` nên có ngay từ MVP chứ không để sau.

## Chưa kiểm chứng được

- Không có số liệu vendor hay độc lập về mức giảm FP khi scope rule theo role, hay về thời gian triage có/không có ngữ cảnh asset; hai nghiên cứu người dùng (n = 21, n = 18) đều định tính.
- Chưa có nghiên cứu 2018–2026 đo precision/recall của service/software inventory suy diễn từ log so với agent inventory hoặc CMDB; truy vấn "passive asset discovery evaluation accuracy ground truth" chỉ ra Bartlett 2007 và blog vendor.
- Chưa có số độc lập về độ chính xác của JA4+, HASSH, DHCP fingerprint (Fingerbank) trên mạng thật, hay về tỉ lệ match đúng domain → SaaS app khi có CDN; bản đầy đủ Laštovička 2023 không tải được.
- Chưa vendor nào được thấy tính coverage theo asset × rule hoặc ghi verdict ngược thành thuộc tính kỳ vọng của asset/role; Exabeam/Securonix chưa kiểm.
- Chưa kiểm mapper OCSF của CrowdStrike, Palo Alto (App-ID ở `app_name` hay `unmapped`), Splunk, Cribl, và chưa thấy mapping công khai osquery/Wazuh → 5020/5040.
- Công thức magnitude của QRadar và con số "13% rule hỏng" của CardinalOps chưa có nguồn gốc; tỉ lệ CVE có CPE theo năm chỉ thấy qua trích đoạn.
- Vấn đề pháp lý khi sản phẩm thương mại chỉ *đọc* JA4+ do nguồn khác sinh ra (FoxIO License 1.1) chưa có nguồn làm rõ.
- Truy vấn đã thử (tiêu biểu): "Suricata alert CVE vulnerability scanner correlation false positive reduction", "host role inference flow data precision recall ground truth CMDB", "osquery OCSF mapping software inventory info", "CardinalOps 2025 State of SIEM Detection Risk 13% rules broken", "Defender XDR DeviceRoles domain controller confidence".

## Nguồn

[1] DeviceInfo table — Microsoft Defender XDR, Microsoft Learn, ms.date 2026-07-27 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-deviceinfo-table
[2] UDM field list — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/reference/udm-field-list
[3] Context-aware analytics — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/detection/context-aware-analytics
[4] OCSF schema, tag 1.9.0 (commit 856d462) — OCSF, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/tree/1.9.0
[5] OCSF schema 1.9.0: objects/device.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/device.json
[6] OCSF schema 1.9.0: objects/port_info.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/port_info.json
[7] Use watchlists in Microsoft Sentinel — Microsoft Learn, 2026-06-23 (bậc 1). https://learn.microsoft.com/en-us/azure/sentinel/watchlists
[8] Sigma Filters — SigmaHQ docs, không rõ ngày (bậc 1). https://sigmahq.io/docs/meta/filters.html
[9] New terms rule — Elastic docs, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/detect-and-alert/new-terms
[10] Microsoft Sentinel UEBA reference — Microsoft Learn, ms.date 2025-08-28, cập nhật 2026-08-05 (bậc 1). https://learn.microsoft.com/en-us/azure/sentinel/ueba-reference
[11] Intrusion Event Impact Levels — Cisco Security Cloud Control docs, không rõ ngày (bậc 1). https://docs.manage.security.cisco.com/r_intrusion_event_impact_levels.html
[12] Updates – October 2025 (ATT&CK v18) — MITRE, 2025-10 (bậc 1). https://attack.mitre.org/resources/updates/updates-october-2025/
[13] data_sources/sysmon_eventid_1.yml — Splunk security_content, 2026-05-13 (bậc 1). https://raw.githubusercontent.com/splunk/security_content/develop/data_sources/sysmon_eventid_1.yml
[14] DeTT&CT data quality scoring — Rabobank CDC wiki, không rõ ngày (bậc 1). https://github.com/rabobank-cdc/DeTTECT/wiki/data-quality-scoring
[15] 99% False Positives: A Qualitative Study of SOC Analysts' Perspectives on Security Alarms — Alahmadi, Axon, Martinovic, USENIX Security 2022-08 (bậc 1). https://www.usenix.org/system/files/sec22-alahmadi.pdf
[16] Automate threat response with automation rules — Microsoft Learn, cập nhật 2026-06-30 (bậc 1). https://learn.microsoft.com/en-us/azure/sentinel/automate-incident-handling-with-automation-rules
[17] Add and manage exceptions — Elastic docs, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/detect-and-alert/add-manage-exceptions
[18] Understanding Passive and Active Service Discovery — Bartlett, Heidemann, Papadopoulos, IMC 2007-10 (bậc 1). https://ant.isi.edu/~johnh/PAPERS/Bartlett07d.pdf
[19] Format an asset or identity list as a lookup (ES 7.2) — Splunk, không rõ ngày (bậc 1). https://help.splunk.com/en/splunk-enterprise-security-7/administer/7.2/asset-and-identity-manual-registration/format-an-asset-or-identity-list-as-a-lookup-in-splunk-enterprise-security
[20] Issue #1752: endpoint.owner conflates accountable owner with last logged-in account — OCSF, 2026-09-06 (bậc 1). https://github.com/ocsf/ocsf-schema/issues/1752
[21] falcon-mcp: falcon_mcp/resources/hosts.py (commit d766b1a) — CrowdStrike, đọc 2026-11-04 (bậc 1). https://github.com/CrowdStrike/falcon-mcp/blob/d766b1abaf38a2e668828a57a7a881f82f94be83/falcon_mcp/resources/hosts.py
[22] OCSF schema 1.9.0: objects/endpoint.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/endpoint.json
[23] OCSF schema 1.9.0: objects/resource_details.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/resource_details.json
[24] Query the enterprise exposure graph — Microsoft Security Exposure Management, cập nhật 2026-10-09 (bậc 1). https://learn.microsoft.com/en-us/security-exposure-management/query-enterprise-exposure-graph
[25] OCSF schema 1.9.0: events/network/network_activity.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network_activity.json
[26] OCSF schema 1.9.0: objects/network_endpoint.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/network_endpoint.json
[27] DeviceTvmSoftwareInventory table — Microsoft Learn, ms.date 2026-06-14 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicetvmsoftwareinventory-table
[28] Context-enriched data in rules — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/detection/use-enriched-data-in-rules
[29] OCSF schema 1.9.0: objects/anomaly_analysis.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/anomaly_analysis.json
[30] OCSF schema 1.9.0: objects/agent.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/agent.json
[31] OCSF schema 1.9.0: events/discovery/device_config_state_change.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/device_config_state_change.json
[32] Default detection rules (YARA-L) — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/detection/default-rules
[33] OCSF schema 1.9.0: objects/vulnerability.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/vulnerability.json
[34] ECS entity fields — Elastic, không rõ ngày (bậc 1). https://www.elastic.co/docs/reference/ecs/ecs-entity
[35] Entity store (Stack 9.4+) — Elastic docs, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/entity-store
[36] OCSF schema 1.9.0: events/iam/entity_management.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/iam/entity_management.json
[37] OCSF schema 1.9.0: profiles/incident.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/profiles/incident.json
[38] OCSF schema 1.9.0: events/findings/finding.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/findings/finding.json
[39] OCSF schema 1.9.0: objects/user.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/user.json
[40] Exclude assets from automated response (automatic attack disruption) — Microsoft Learn, ms.date 2026-10-04 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/automatic-attack-disruption-exclusions
[41] Port Scan - Internal Source playbook — Cortex XSOAR docs, không rõ ngày (bậc 1). https://xsoar.pan.dev/docs/reference/playbooks/port-scan---internal-source
[42] OCSF schema 1.9.0: events/remediation (7001–7004) — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/tree/1.9.0/events/remediation
[43] DET0001 (Detection Strategy, analytic AN0001) — MITRE ATT&CK v18, 2025-10 (bậc 1). https://attack.mitre.org/detectionstrategies/DET0001/
[44] Entity zones in Exposure Analytics (ES 8.6) — Splunk, không rõ ngày (bậc 1; chỉ đọc trích đoạn). https://help.splunk.com/en/splunk-enterprise-security-8/administer/8.6/exposure-analytics/entity-zones-in-exposure-analytics
[45] Prebuilt job reference (7.9) — Elastic, bản cũ, không rõ ngày (bậc 1; chỉ đọc trích đoạn). https://www.elastic.co/guide/en/security/7.9/prebuilt-ml-jobs.html
[46] Peer-group behavioural analytics of Windows authentications events using hierarchical Bayesian modelling — Hawryluk et al., arXiv:2209.09769, 2022-09 (bậc 1, preprint). https://arxiv.org/abs/2209.09769
[47] ExposureGraphNodes table — Microsoft Learn, ms.date 2025-03-28 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-exposuregraphnodes-table
[48] docs-content issue #3994 (related_integrations, required_fields) — Elastic, không rõ ngày (bậc 1; chỉ đọc trích đoạn). https://github.com/elastic/docs-content/issues/3994
[49] CardinalOps: Enterprise SIEMs miss 79% of MITRE ATT&CK techniques — SDC Exec, 2025-06 (bậc 2, tuyên bố vendor). https://www.sdcexec.com/safety-security/risk-compliance/news/22942866/cardinalops-enterprise-siems-miss-79-of-mitre-attck-techniques
[50] OCSF schema 1.9.0: objects/metadata.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/metadata.json
[51] How Google SecOps enriches event and entity data — Google SecOps docs, không rõ ngày (bậc 1). https://docs.cloud.google.com/chronicle/docs/event-processing/data-enrichment
[52] Asset criticality — Elastic docs, không rõ ngày (bậc 1). https://www.elastic.co/docs/solutions/security/advanced-entity-analytics/asset-criticality
[53] OCSF schema 1.9.0: events/base_event.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/base_event.json
[54] OCSF schema 1.9.0: objects/enrichment.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/enrichment.json
[55] Matched and Mismatched SOCs: A Qualitative Study on Security Operations Center Issues — Kokulu et al., ACM CCS 2019-11 (bậc 1). https://adamdoupe.com/publications/matched-and-mismatched-socs-ccs2019.pdf
[56] NIST SP 800-61r3: Incident Response Recommendations and Considerations for Cybersecurity Risk Management — NIST, 2025-04-03 (bậc 1). https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r3.pdf
[57] Investigate incidents in Microsoft Defender XDR — Microsoft Learn, ms.date 2026-09-09 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/investigate-incidents
[58] Work with attack paths — Microsoft Security Exposure Management, ms.date 2026-05-14 (bậc 1). https://learn.microsoft.com/en-us/security-exposure-management/work-attack-paths-overview
[59] View detection alert details — Elastic docs, không rõ ngày (bậc 1). https://www.elastic.co/guide/en/security/current/view-alert-details.html
[60] Automatic attack disruption: enhanced containment for critical assets and shadow IT — Microsoft Tech Community, 2025-04-09 (bậc 1 vendor). https://techcommunity.microsoft.com/blog/microsoftthreatprotectionblog/automatic-attack-disruption-enhanced-containment-for-critical-assets-and-shadow-/4402157
[61] Defender XDR incident API (classification, determination) — Microsoft Learn, không rõ ngày (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/api-incident
[62] Microsoft.SecurityInsights automationRules (ARM template) — Microsoft Learn, không rõ ngày (bậc 1). https://docs.microsoft.com/en-us/azure/templates/microsoft.securityinsights/2019-01-01-preview/automationrules
[63] OCSF schema 1.9.0: objects/evidences.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/evidences.json
[64] OCSF schema 1.9.0: events/network/dhcp_activity.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/dhcp_activity.json
[65] OCSF schema 1.9.0: objects/ja4_fingerprint.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/ja4_fingerprint.json
[66] OCSF schema 1.9.0: objects/load_balancer.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/load_balancer.json
[67] OCSF schema 1.9.0: events/network/network.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network.json
[68] OCSF schema 1.9.0: objects/query_evidence.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/query_evidence.json
[69] OCSF schema 1.9.0: extensions/windows/events/windows_service_activity.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/windows/events/windows_service_activity.json
[70] OCSF schema 1.9.0: extensions/linux/extension.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/linux/extension.json
[71] PR #1725: control_group object (đang mở) — OCSF, 2026-08-12 (bậc 1). https://github.com/ocsf/ocsf-schema/pull/1725
[72] OCSF schema 1.9.0: objects/http_response.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/http_response.json
[73] OCSF schema 1.9.0: events/network/ssh_activity.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/ssh_activity.json
[74] OCSF schema 1.9.0: objects/tls.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/tls.json
[75] OCSF schema 1.9.0: events/network/email_activity.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/email_activity.json
[76] OCSF schema 1.9.0: objects/database.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/database.json
[77] OCSF schema 1.9.0: events/discovery/software_info.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/software_info.json
[78] OCSF schema 1.9.0: objects/sbom.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/sbom.json
[79] OCSF schema 1.9.0: events/application/application_lifecycle.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/application/application_lifecycle.json
[80] OCSF schema 1.9.0: objects/file.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/file.json
[81] OCSF schema 1.9.0: dictionary.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/dictionary.json
[82] PR #1702: Application/Product cleanup (deprecate 6002.app, actor.app_name) — OCSF, 2026-07 (bậc 1). https://github.com/ocsf/ocsf-schema/pull/1702
[83] PR #1466: Add open_ports to network_interface — OCSF, 2025 (bậc 1). https://github.com/ocsf/ocsf-schema/pull/1466
[84] AWS VPC Flow Logs → OCSF v1.5.0 mapping — ocsf/examples, không rõ ngày (bậc 1). https://github.com/ocsf/examples/blob/main/mappings/markdown/AWS/v1.5.0/VPC%20Flowlogs/README.md
[85] zeek/operators/ocsf/logs/ssh.tql @932bfb2 — Tenzir library, 2026-11-03 (bậc 1). https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/logs/ssh.tql
[86] OCSF schema CHANGELOG (đến 1.9.0) — OCSF, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md
[87] zeek/operators/ocsf/map.tql @932bfb2 — Tenzir library, 2026-11-03 (bậc 1). https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/map.tql
[88] Issue #1384: Profiles for Network Activity — OCSF, 2025-03-26 (bậc 1). https://github.com/ocsf/ocsf-schema/issues/1384
[89] Zeek OCSF changelog: application protocol fields — Tenzir library, 2026-05 (bậc 1). https://github.com/tenzir/library/blob/main/zeek/changelog/unreleased/ocsf-application-protocol-fields.md
[90] known-services.zeek — Zeek, master, truy cập 2026-11-04 (bậc 1). https://github.com/zeek/zeek/blob/master/scripts/policy/protocols/conn/known-services.zeek
[91] Software framework main.zeek — Zeek, master, truy cập 2026-11-04 (bậc 1). https://github.com/zeek/zeek/blob/master/scripts/base/frameworks/software/main.zeek
[92] protocols/http/software.zeek — Zeek, master, truy cập 2026-11-04 (bậc 1). https://github.com/zeek/zeek/blob/master/scripts/policy/protocols/http/software.zeek
[93] Examining Chrome's TLS ClientHello Permutation in the wild — Fastly, 2023-02-08 (bậc 2). https://www.fastly.com/blog/a-first-look-at-chromes-tls-clienthello-permutation-in-the-wild
[94] JA4+ README — FoxIO-LLC, truy cập 2026-11-04 (bậc 1). https://github.com/FoxIO-LLC/ja4
[95] HASSH — Salesforce, archive 2025-05-01 (bậc 1). https://github.com/salesforce/hassh
[96] Fingerbank API v2: interrogate — Fingerbank/Inverse, không rõ ngày (bậc 1). https://api.fingerbank.org/api_doc/2/combinations/interrogate.html
[97] Passive Operating System Fingerprinting Revisited: Evaluation and Current Challenges — Laštovička et al., Computer Networks 229, 2023 (bậc 1; chỉ đọc tóm tắt). https://www.researchgate.net/publication/370164594_Passive_Operating_System_Fingerprinting_Revisited_Evaluation_and_Current_Challenges
[98] How to Block QUIC Protocol — Palo Alto Networks, 2018, sửa 2023-06 (bậc 1). https://live.paloaltonetworks.com/t5/Management-Articles/How-to-Block-QUIC-Protocol/ta-p/120207
[99] App-ID Overview (PAN-OS 11.1) — Palo Alto Networks, không rõ ngày (bậc 1). https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-admin/app-id/app-id-overview
[100] Device discovery overview — Microsoft Learn, cập nhật 2026-04-13 (bậc 1). https://learn.microsoft.com/en-us/defender-endpoint/device-discovery
[101] OS Fingerprinting: New Techniques and a Study of Information Gain and Obfuscation — Anderson & McGrew (Cisco), arXiv:1706.08003, 2017-06 (bậc 1). https://arxiv.org/abs/1706.08003
[102] Application of Tabular Transformer Architectures for Operating System Fingerprinting — arXiv:2502.09084, 2025-02 (bậc 1). https://arxiv.org/html/2502.09084
[103] Forescout eyeSight datasheet — Forescout, 2022 (bậc 1 vendor, tuyên bố vendor). https://forescout.com/resources/forescout-eyesight-datasheet
[104] Armis Solution Brief — Armis, không rõ ngày (bậc 1 vendor, tuyên bố vendor). https://www.cc.com.pl/pl/prods/armis/pdf/Armis_Solution_Brief.pdf
[105] RFC 9849: TLS Encrypted Client Hello — IETF/RFC Editor, 2026 (bậc 1). https://www.rfc-editor.org/info/rfc9849
[106] Encrypted Client Hello defense strategies — Cisco Secure Firewall, cập nhật 2026-08-24 (bậc 1 vendor). https://secure.cisco.com/secure-firewall/docs/encrypted-client-hello-defense-strategies-how-cisco-secure-firewall-tackles-ech
[107] Software inventory — Microsoft Defender Vulnerability Management, Microsoft Learn, ms.date 2026-10-14 (bậc 1). https://learn.microsoft.com/en-us/defender-vulnerability-management/tvm-software-inventory
[108] DeviceTvmSoftwareEvidenceBeta table — Microsoft Learn, 2026-06-14 (bậc 1). https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicetvmsoftwareevidencebeta-table
[109] Plugin 45590: Common Platform Enumeration (CPE) — Tenable, 2026-09-29 (bậc 1). https://www.tenable.com/plugins/nessus/45590
[110] Usage Guide – Software (CSAM) — Qualys, không rõ ngày (bậc 1). https://docs.qualys.com/en/csam/latest/appendix/usage_guide_software.htm
[111] Software — Axonius docs, cập nhật 2026-10-22 (bậc 1). https://docs.axonius.com/docs/software
[112] System inventory: available inventory fields (4.14) — Wazuh, không rõ ngày (bậc 1). https://documentation.wazuh.com/current/user-manual/capabilities/system-inventory/available-inventory-fields.html
[113] osquery table specs (commit 981c4d3) — osquery, 2026-11-02 (bậc 1). https://github.com/osquery/osquery/tree/master/specs
[114] Sysmon — Microsoft Sysinternals, 2026-09-10 (bậc 1). https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon
[115] microsoft/operators/windows/ocsf (Sysmon, 7045, 4697 → OCSF) — Tenzir library, 2026-11 (bậc 1). https://github.com/tenzir/library/tree/main/microsoft/operators/windows/ocsf
[116] Windows Sysmon mapping — aws-samples/amazon-security-lake-transformation-library, 2025-05-06 (bậc 1). https://github.com/aws-samples/amazon-security-lake-transformation-library/blob/main/mapping_docs/windows-sysmon-mapping.md
[117] microsoft/operators/graph/ocsf/events/detected_app.tql — Tenzir library, 2026-11 (bậc 1). https://github.com/tenzir/library/blob/main/microsoft/operators/graph/ocsf/events/detected_app.tql
[118] Six schemas into OCSF — Jeremy Wiley, Security Data Works, 2026-08 (bậc 2). https://securitydataworks.com/writing/ocsf/six-schemas-into-ocsf/
[119] NVD News (thay legacy feed bằng file theo API 2.0) — NIST NVD, 2025 (bậc 1, qua tóm tắt). https://www.nist.gov/itl/nvd/nvd-news
[120] Dependency-Track issue #6494 (CPE vendor rename, deprecatedBy) — DependencyTrack, 2026-06-23 (bậc 1). https://github.com/DependencyTrack/dependency-track/issues/6494
[121] ECMA-427 Package-URL (PURL), 1st edition — Ecma International, 2025-12 (bậc 1). https://www.ecma-international.org/publications-and-standards/standards/ecma-427/
[122] NIST IR 8060: Guidelines for the Creation of Interoperable SWID Tags — NIST, 2016-04 (bậc 1). https://csrc.nist.gov/pubs/ir/8060/final
[123] Creating Normalize Mapping for Private Catalog Software — Flexera docs, không rõ ngày (bậc 1). https://docs.flexera.com/dataplatform/UserConsoleGuide/Content/Creating_Normalize_Mapping_for_Private_Catalog_Software.htm
[124] Flow Direction Swapping Explained — ntop, 2025-10-17 (bậc 1 cho hành vi sản phẩm). https://www.ntop.org/flow-direction-swapping-explained/
[125] Host Insights (39.0.0) — Stamus Networks docs, không rõ ngày (bậc 1). https://docs.stamus-networks.com/39.0.0/concepts/host-insights.html
[126] Corelight launches the Entity Collection — Corelight, 2022-12-13, cập nhật 2026-04-03 (bậc 1). https://corelight.com/blog/corelight-launches-the-entity-collection
[127] Understanding assets — runZero docs, truy cập 2026-11-04 (bậc 1). https://help.runzero.com/docs/understanding-assets/index.md
[128] Set up Cloud Discovery — Microsoft Defender for Cloud Apps, Microsoft Learn, 2025-09-17 (bậc 1). https://learn.microsoft.com/en-us/defender-cloud-apps/set-up-cloud-discovery
[129] Integrate Microsoft Defender for Endpoint (Defender for Cloud Apps) — Microsoft Learn, 2026-07-03 (bậc 1). https://learn.microsoft.com/en-us/defender-cloud-apps/mde-integration
[130] Add custom apps to cloud discovery — Microsoft Learn, 2026-07-03 (bậc 1). https://learn.microsoft.com/en-us/defender-cloud-apps/cloud-discovery-custom-apps
[131] OCSF schema 1.9.0: events/findings/incident_finding.json — OCSF, tag 1.9.0, 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/findings/incident_finding.json
