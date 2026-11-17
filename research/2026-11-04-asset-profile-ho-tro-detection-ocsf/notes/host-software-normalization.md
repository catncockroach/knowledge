# Bằng chứng trên host và chuẩn hoá phần mềm

Phạm vi: câu hỏi phụ 3 của brief. Schema OCSF đối chiếu với bản clone `ocsf-schema` tag `1.9.0` (commit `856d462`), đọc trực tiếp file JSON. Mapping cộng đồng đọc trực tiếp từ source code: `tenzir/library` (commit `932bfb2`, 2026-11-03) và `aws-samples/amazon-security-lake-transformation-library` (commit `af68fe6`, 2025-05-06).

## 3a. Bằng chứng trên host về phần mềm đã cài, đang chạy và service

### Kết luận ngắn
Mỗi nguồn host chỉ thấy một phần: inventory (MDVM, Tenable, Qualys, Wazuh, osquery) nói phần mềm **đã cài**; Sysmon 1/6/7 và Windows 7045/4697 nói phần mềm **đã chạy hoặc vừa được cài làm service**; Wazuh ports, osquery `listening_ports` nói **process nào đang lắng nghe port nào**, tức bằng chứng trực tiếp nhất cho `asset_service`. Nguồn inventory có điểm mù rõ (Linux chỉ thấy gói của package manager, Windows chỉ thấy mục Add/Remove Programs). Mức chắc chắn: **cao** cho phần mô tả nguồn (đọc docs chính thức, source code), **trung bình** cho cách gộp (suy luận).

### Phát hiện có nguồn

**Microsoft Defender Vulnerability Management (MDVM)**
- Discovery dùng "the same set of signals that is responsible for detection and vulnerability assessment" của Defender for Endpoint (sensor EDR); dữ liệu software inventory "updated every three to four hours. There's currently no way to force a sync" — [Software inventory – MDVM](https://learn.microsoft.com/en-us/defender-vulnerability-management/tvm-software-inventory) (bậc 1, ms.date 2026-10-14)
- Mặc định chỉ hiện phần mềm có CPE chính thức; bỏ filter "CPE Available" mới thấy phần mềm không có CPE. "Software products without a CPE are shown in the software inventory page, but they're not supported by vulnerability management". Phần mềm không hỗ trợ có Weaknesses = `Not available` — cùng nguồn (bậc 1, 2026-10-14)
- **Software Evidence**: cho biết phần mềm được phát hiện "in the registry, on the disk, or both" (đường dẫn registry/đĩa) — cùng nguồn
- Linux: "only lists software installed using native package managers such as rpm, dnf, and yum. Applications installed manually or with custom methods such as unpacked binaries or JAR based applications, aren't listed"; có custom inventory hẹp cho Log4j và SAP NetWeaver — cùng nguồn
- **Chuẩn hoá version có chủ đích**: SQL Server 2016 bản `13.0.7016.1` hiện là `13.3.7016.1` ("functionally equivalent"); MDVM "applies version normalization rules to ensure better cross-device correlation" — cùng nguồn. Hệ quả: version từ MDVM không so khớp trực tiếp với `FileVersion` của Sysmon hay version registry.
- Có lọc theo tag end-of-support; có API riêng "Export non product code software inventory assessment per device" cho phần mềm không CPE — cùng nguồn
- Bảng advanced hunting `DeviceTvmSoftwareInventory`: `DeviceId`, `DeviceName`, `OSPlatform`, `OSVersion`, `OSArchitecture`, `SoftwareVendor`, `SoftwareName`, `SoftwareVersion`, `EndOfSupportStatus`, `EndOfSupportDate`, `ProductCodeCpe` ("or 'not available' where there's no CPE"). Bảng này **không ingest vào Microsoft Sentinel** (chỉ có schema, query trả rỗng) — [DeviceTvmSoftwareInventory](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicetvmsoftwareinventory-table) (bậc 1, ms.date 2026-06-14)
- Tên phần mềm MDVM ở dạng gần CPE: docs khuyên tìm `windows_10` thay vì `Windows 10` — [Software inventory – MDVM](https://learn.microsoft.com/en-us/defender-vulnerability-management/tvm-software-inventory) (bậc 1)

**Tenable**
- Plugin 20811 "Microsoft Windows Installed Software Enumeration (credentialed check)" liệt kê phần mềm từ registry key Uninstall và Updates; Tenable.sc dùng 20811 cho Windows và 22869 "Software Enumeration (SSH)" cho non-Windows; blog Tenable lưu ý danh sách rất dài vì gồm cả ứng dụng đi kèm OS — [Plugin 20811](https://tenable.com/plugins/nessus/20811), [Enterprise Software Discovery with Nessus](https://www.tenable.com/blog/enterprise-software-discovery-with-nessus) (bậc 1, qua tóm tắt search, không rõ ngày)
- Plugin 45590 "Common Platform Enumeration (CPE)": liệt kê CPE khớp trên host; nếu không có CPE chính thức thì "computes the best available CPE" từ dữ liệu scan; hỗ trợ agent Windows/macOS/Unix; cập nhật 2026-09-29 (v1.189) — [Plugin 45590](https://www.tenable.com/plugins/nessus/45590) (bậc 1, 2026-09-29)

**Qualys CSAM**
- Phần mềm được chuẩn hoá vào taxonomy riêng 2 cấp (29 Level 1, 149 Level 2 category); bản ghi `UNKNOWN` nghĩa là "has not been normalized" và khi đó "category, lifecycle and license information has not been populated" — [Usage Guide – Software (CSAM)](https://docs.qualys.com/en/csam/latest/appendix/usage_guide_software.htm) (bậc 1, không rõ ngày)
- Mô hình release tách: publisher, family, product, component (Client/Server), market version (vd "2016"), version (major.minor), update (SP/maintenance), edition, architecture — cùng nguồn
- Lifecycle: "nearly 1700 publishers and over 65,000 software releases"; EOL = hết support cấp một, EOS = hết support cuối; ngày "estimated" khi publisher không công bố — cùng nguồn. Một blog Qualys nêu con số khác (5.500 publisher, 300.000 release) — [Qualys blog qua Vulners](https://vulners.com/qualysblog/QUALYSBLOG:C0E0BA67677D3EB8EA4FB68F41864A14) (bậc 2, qua snippet); hai nguồn lệch nhau.
- Trang không mô tả phương thức discovery cũng như liên hệ với CPE — cùng nguồn

**Axonius**
- Bảng Software gộp phần mềm từ mọi adapter; "Preferred Software Name" lấy "from the Axonius Catalog if it exists there", nếu không thì chọn tên tốt nhất trong các tên đã fetch; Catalog bổ sung "name, vendor, and category most commonly used" — [Software (Axonius docs)](https://docs.axonius.com/docs/software) (bậc 1, updatedAt 2026-10-22)
- Thừa nhận dữ liệu không nhất quán: Software Vendor "interchangeable with" Software Publisher "due to data parsing inconsistencies among different adapters"; trường version "might sometimes contain duplicate versions" nên có thêm Unique Version Count — cùng nguồn
- Có hai CPE: CPE từ adapter và "Generated CPE (Axonius)" sinh từ vendor + name + version — cùng nguồn. Static Analysis gửi CPE đó lên NVD và mọi CVE khớp thành finding; có tuỳ chọn loại CVE "without specific affected versions" để giảm sai — [Axonius Static Analysis](https://docs.axonius.com/docs/vulnerability-static-analysis) (bậc 1, updatedAt 2026-10-14)

**Wazuh Syscollector** (docs 4.14.x)
- Bảng: `sys_hwinfo`, `sys_osinfo`, `sys_programs` (packages), `sys_netiface`/`sys_netaddr`/`sys_netproto`, `sys_ports`, `sys_processes`, `sys_hotfixes`, `sys_users`, `sys_groups`, `sys_services` — [Available inventory fields](https://documentation.wazuh.com/current/user-manual/capabilities/system-inventory/available-inventory-fields.html) (bậc 1, docs 4.14)
- Packages: `package.name`, `version`, `type` (deb/rpm/pacman…), `vendor`, `architecture`, `installed` (thời điểm cài), `path` (chỉ Windows và macOS pkg) — cùng nguồn
- Ports: `interface.state` (vd listening), `network.transport`, `destination.ip/port` = địa chỉ local, `source.ip/port` = địa chỉ remote, **`process.name`/`process.pid` chỉ có trên Windows/macOS** — cùng nguồn. **Nhận định:** trên Linux, port listening từ Wazuh có thể không gắn được process, nên không suy ra ngay "nginx nghe 443".
- Services: `service.id`, `description`, `enabled` (Linux/macOS), `exit_code`, `process.executable`, `process.pid`, `process.user.name` — cùng nguồn (trang bị cắt, có thể chưa đủ)

**osquery** (specs ở commit `981c4d3`, 2026-11-02)
- `programs` (Windows): "products as they are installed by Windows Installer… Some fields may be blank"; cột `name`, `version`, `install_location`, `install_source`, `publisher`, `install_date`, `identifying_number` (ProductCode), `package_family_name`, `upgrade_code` — [specs/windows/programs.table](https://github.com/osquery/osquery/blob/master/specs/windows/programs.table) (bậc 1, 2026-11)
- `deb_packages`: `name`, `version`, `source`, `arch`, `revision`, `status`, `maintainer`; `rpm_packages`: `name`, `version`, `release`, `epoch`, `arch`, `vendor`, `sha1`, `install_time` — [specs/linux/](https://github.com/osquery/osquery/tree/master/specs/linux) (bậc 1)
- `apps` (macOS): `bundle_identifier`, `bundle_short_version`, `bundle_version`, `last_opened_time`… — [specs/darwin/apps.table](https://github.com/osquery/osquery/blob/master/specs/darwin/apps.table) (bậc 1)
- Service: `services` (Windows: `name`, `service_type`, `status`, `pid`, `start_type`, `path`, `module_path`, `user_account`); `systemd_units` (`id`, `active_state`, `sub_state`, `unit_file_state`, `fragment_path`, `user`); `launchd` (`label`, `program`, `program_arguments`, `run_at_load`, `keep_alive`, `disabled`) — [specs/](https://github.com/osquery/osquery/tree/master/specs) (bậc 1)
- Mạng: `listening_ports` ("Processes with listening (bound) network sockets/ports": `pid`, `port`, `protocol`, `family`, `address`, `path`); `process_open_sockets` (`pid`, `local/remote_address`, `local/remote_port`, `state`, `path`) — cùng nguồn
- Gói ngôn ngữ và extension: `python_packages`, `npm_packages`, `chrome_extensions` (`identifier`, `version`, `permissions`, `from_webstore`) — cùng nguồn. **Nhận định:** đây là nguồn chính cho phần mềm Linux "ngoài package manager" mà MDVM bỏ sót.
- Cộng đồng Fleet báo `programs` bỏ sót app nằm dưới `Program Files\WindowsApps` (MSIX/Store) — [osquery chat](https://chat.osquery.io/t/16141224/hello-we-are-using-the-programs-to-fetch-all-apps-installe-) (bậc 3, chỉ làm manh mối)

**Sysmon** (trang cập nhật 2026-09-10)
- Event 1 Process creation: full command line, hash ảnh (SHA1 mặc định, MD5, SHA256, IMPHASH), `ProcessGUID`. Event 3 Network connection "is disabled by default", gắn process qua `ProcessId`/`ProcessGuid`. Event 6 Driver loaded có hash và "signature information". Event 7 Image loaded "disabled by default", sinh "significant amount of logging" — [Sysmon – Sysinternals](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon) (bậc 1, 2026-09-10)
- Trường VERSIONINFO của Event 1/7: `FileVersion`, `Description`, `Product`, `Company`, `OriginalFileName`; Event 7 thêm `Signed`, `Signature`, `SignatureStatus`; giá trị rỗng là `"-"` — thấy trong mapping Tenzir (xem 3c) [image_load.tql](https://github.com/tenzir/library/blob/main/microsoft/operators/windows/ocsf/providers/sysmon/events/image_load.tql) (bậc 1, source code 2026-11); OSSEM mô tả `FileVersion` là "Version of the image associated with the main process" — [OSSEM Event 1](https://ossemproject.com/dd/dictionaries/linux/sysmon/event-1.html) (bậc 2, qua snippet)

**Windows 7045 / 4697 (service được cài)**
- 7045 (SCM, log System) mang `ServiceName`, `ImagePath`, `ServiceType`, `StartType`, `AccountName`; 4697 (Security audit) mang `ServiceFileName`, `ServiceStartType`, `ServiceAccount` — thấy qua mapping Tenzir [service_install_scm.tql](https://github.com/tenzir/library/blob/main/microsoft/operators/windows/ocsf/events/service_install_scm.tql), [service_install.tql](https://github.com/tenzir/library/blob/main/microsoft/operators/windows/ocsf/events/service_install.tql) (bậc 1, source code 2026-11)

### Nhận định
- Phân loại bằng chứng host theo mức tin cậy cho `asset_software`: (1) inventory agent/scan có credential, khai báo "đã cài" (MDVM, Tenable 20811/22869, Wazuh, osquery packages); (2) runtime: Sysmon 1/7 hoặc EDR process event có `FileVersion/Product/Company` + chữ ký, chứng minh "đã chạy" kể cả bản portable không có trong registry; (3) lifecycle: 7045/4697, AppX, MSI install. Inventory chứng minh *có mặt*, runtime chứng minh *được dùng*; hai loại nên lưu tách (`installed` vs `last_executed`).
- Cho `asset_service` trên host: bằng chứng mạnh nhất là `listening_ports`/Wazuh ports có PID, nối với process → file → product. Không có PID (Wazuh trên Linux) thì chỉ còn (port, proto) như bằng chứng mạng.
- Mỗi vendor đã có catalog riêng (MDVM: tên kiểu CPE + version normalize; Qualys: taxonomy + lifecycle; Axonius: Preferred Name + Generated CPE). Một sản phẩm SOC đa tenant nhận dữ liệu đã chuẩn hoá theo nhiều catalog khác nhau, nên phải giữ cả tên gốc (raw) và tên chuẩn của từng nguồn.

### Khoảng trống
- Linux auditd/journald cho systemd unit (unit mới được enable, `systemctl` gọi qua auditd `EXECVE`, message `Started …` của journald): chưa tìm nguồn chính thức trong ngân sách; chỉ có osquery `systemd_units`. Mapping Tenzir có `kunai` (`kunai/operators/ocsf/events/start.tql`) nhưng chưa đọc.
- Tenable: chưa tìm được tài liệu về software normalization ở tầng Tenable One/Exposure Management (chỉ có plugin).
- Qualys: trang Usage Guide không nói discovery method hay CPE; "Technology Catalog" không được nêu tên trên trang đã đọc.
- Wazuh: phần cuối trang (services, browser extensions) bị cắt khi đọc.

## 3b. Chuẩn hoá tên phần mềm: CPE, purl, SWID, SBOM và khoá sản phẩm

### Kết luận ngắn
Không có định danh nào đủ dùng một mình: CPE phủ phần mềm thương mại nhưng NVD gán CPE chậm, đổi tên vendor không backfill, và feed cũ đã bị khai tử 2025; purl mới thành chuẩn Ecma (ECMA-427, 12/2025) nhưng chỉ hợp với gói của package manager; SWID gần như không còn được dùng trong thực tế (NIST IR 8060 vẫn ở bản 2016). Vendor nào cũng dựa vào catalog riêng. Khuyến nghị: khoá nội bộ `(vendor_norm, product_norm)` cùng bảng alias sang CPE, purl, App-ID, tên process. Mức chắc chắn: **trung bình–cao** (sự kiện NVD/purl có nguồn; khuyến nghị khoá là suy luận).

### Phát hiện có nguồn
- **NVD feed**: tháng 2/2025 NVD lên kế hoạch thay các file feed legacy (gồm Official CPE 2.3 Dictionary và CPE Match 1.0) bằng file theo API 2.0 (`/cves/`, `/cpematch/`, `/cpes/`, dạng tar.gz chia khối); file legacy còn song song tới **20/8/2025** rồi bị gỡ — [NVD News](https://www.nist.gov/itl/nvd/nvd-news) (bậc 1, 2025; qua tóm tắt search, chưa mở trang gốc từng thông báo)
- **NVD ưu tiên enrich từ 15/4/2026**: chỉ CVE trong KEV, phần mềm liên bang, "critical software"; backlog trước 1/3/2026 thành "Not Scheduled" (~29.000) — tóm tắt ở report kế thừa [research/2026-10-27-agentic-phan-ung-nhanh-cve/report.md](../../2026-10-27-agentic-phan-ung-nhanh-cve/report.md) (nguồn [20]–[22] trong đó: NIST 2026-04, bậc 1 qua tóm tắt). Tỉ lệ CVE 2025 có CPE ~57,6% và so sánh VulnCheck 76,95% vs NVD 41,35% (CVE 2024) chỉ thấy qua snippet của [CSA Labs](https://labs.cloudsecurityalliance.org/research/csa-research-note-nist-nvd-enrichment-overhaul-20260429-csa/) (bậc 2, chưa mở) → xem Khoảng trống.
- **CPE matching sai do dữ liệu NVD**: Vercation thấy CPE của NVD thiếu ở 134 CVE và thừa ở 56 CVE vì mặc định coi mọi version trước version được nhắc là bị ảnh hưởng — report kế thừa trên, nguồn [23] (bậc 1 theo report đó)
- **Đổi tên vendor không backfill**: `arm:mbed_tls` → `trustedfirmware:mbed_tls`; tới 5/6/2026 cả 181 mục `arm:mbed_tls` deprecated, 16 CVE vẫn dùng `arm`, 2 CVE mới dùng `trustedfirmware`, nên không CPE nào tìm đủ 18 CVE; ví dụ khác `haxx:curl` → `curl_project:curl`; NVD backfill "slowly or not at all". Đề xuất: đồng bộ chuỗi `deprecated`/`deprecatedBy` của CPE Dictionary API để mở rộng vendor lúc match — [Dependency-Track #6494](https://github.com/DependencyTrack/dependency-track/issues/6494) (bậc 1, 2026-06-23)
- **purl / ECMA-427**: 1st edition 12/2025; định nghĩa cú pháp Package-URL và "the schema for defining PURL types" nhưng "does not include any specific PURL type definitions" (maven, pypi, npm… nằm ngoài chuẩn); song song là ISO/IEC DIS 27056 — [ECMA-427](https://www.ecma-international.org/publications-and-standards/standards/ecma-427/) (bậc 1, 2025-12). Theo snippet trang dự án: Ecma GA duyệt 2025-12-10, purl-spec v1.0.0 phát hành 2025-12-18 — [packageurl.org](https://package-url.github.io/www.packageurl.org) (bậc 1, qua snippet). Một purl có 7 thành phần (`pkg:type/namespace/name@version?qualifiers#subpath`) — [purl-spec](https://github.com/package-url/purl-spec) (bậc 1, cấu trúc theo spec; chưa mở lại trong phiên này)
- CVE Record format 5.2.0 hỗ trợ PURL, nên khớp thẳng SBOM được — report kế thừa trên, nguồn [68] [cvelistV5](https://github.com/CVEProject/cvelistV5) (bậc 1)
- **SWID**: NIST IR 8060 "Guidelines for the Creation of Interoperable Software Identification (SWID) Tags", bản Final 04/2016, dựa trên ISO/IEC 19770-2 — [NIST IR 8060](https://csrc.nist.gov/pubs/ir/8060/final) (bậc 1, 2016-04). Không thấy bản sửa mới.
- **CycloneDX 1.7** phát hành 10/2025, tương thích ngược 1.4–1.6, thêm phần cryptography (CBOM) và root `citations` — [CycloneDX v1.7 released](https://cyclonedx.org/news/cyclonedx-v1.7-released), [FOSSA](https://fossa.com/blog/whats-new-cyclone-dx-1-7/) (bậc 1/2, 2025-10)
- **Flexera Technopedia**: map package/file thô (Display Name + Publisher) vào Manufacturer → Software → Version → Release; phần không khớp nằm trong "Unmatched Package/Unmatched File" và phải map tay; Flexera coi luật map raw evidence → Technopedia là "our intellectual property" — [Creating Normalize Mapping (Flexera docs)](https://docs.flexera.com/dataplatform/UserConsoleGuide/Content/Creating_Normalize_Mapping_for_Private_Catalog_Software.htm) (bậc 1, không rõ ngày); [Flexera community](https://community.flexera.com/t5/Data-Platform-Forum/ProductName-in-Technopedia-vs-AddRemovePrograms-in-windows/m-p/192489) (bậc 3, manh mối)
- **Các bẫy về version, có nguồn**:
  - MDVM tự đổi version (13.0 → 13.3) — [MDVM](https://learn.microsoft.com/en-us/defender-vulnerability-management/tvm-software-inventory) (bậc 1)
  - Qualys tách market version / version / update / edition — [Qualys](https://docs.qualys.com/en/csam/latest/appendix/usage_guide_software.htm) (bậc 1)
  - RPM có `epoch` + `version` + `release`, deb có `revision` — [osquery specs](https://github.com/osquery/osquery/tree/master/specs/linux) (bậc 1); OCSF `package` có sẵn `epoch`, `release` (schema 1.9.0)
  - macOS có `bundle_short_version` và `bundle_version` — osquery `apps` (bậc 1)
  - Axonius gộp version bị trùng — [Axonius](https://docs.axonius.com/docs/software) (bậc 1)
  - Sysmon dùng `"-"` khi không có giá trị — Tenzir `image_load.tql` (bậc 1)

### Nhận định
- Không có một chuỗi CPE duy nhất đúng cho mọi thời điểm. CPE nên là **thuộc tính dẫn xuất** (alias có thời hạn, đi kèm chuỗi deprecated), không làm khoá chính.
- Khoá sản phẩm đề xuất: `product_key = (vendor_norm, product_norm)`, cộng `edition`/`component` khi cần (Qualys tách Client/Server). Version lưu riêng ba mức: `version_raw` (từ nguồn), `version_norm` (so sánh được: epoch:version-release cho rpm, dpkg cho deb, numeric tuple cho PE `FileVersion`), `market_version` (vd "2016"). Bảng alias trỏ về `product_key`, mỗi alias một loại:
  - `cpe` (vendor:product, bỏ version)
  - `purl` (bỏ version)
  - `process_name`, `internal_name` / `OriginalFileName`
  - `pe_product` + `pe_company`
  - `bundle_id` (macOS)
  - `msi_upgrade_code`
  - `app_id` (Palo Alto)
  - `saas_catalog_id`
  - `vendor_display_name` (tên hiển thị theo từng nguồn)
- Ví dụ Google Chrome: `chrome.exe` + `OriginalFileName=chrome.exe` + `Company=Google LLC` + `Product=Google Chrome` (Sysmon); `programs.name="Google Chrome"`, `publisher="Google LLC"` (osquery); `cpe:2.3:a:google:chrome:*`; bundle id `com.google.Chrome`; App-ID của Palo Alto (traffic web của trình duyệt, không phải sản phẩm). **Nhận định:** App-ID / NBAR và SaaS là trục *ứng dụng mạng* chứ không phải *phần mềm cài trên máy*, nên đi vào `asset_app_usage` qua alias riêng, đừng ép chung khoá với phần mềm cài.
- Khoá alias theo `OriginalFileName` + `Company` + chữ ký đáng tin hơn `process.name` (dễ đổi tên). Tuy vậy vẫn cần catalog, vì nhiều binary không có VERSIONINFO.

### Khoảng trống
- Tỉ lệ CVE có CPE theo năm (57,6%, 41,35%/76,95%) chưa mở được nguồn gốc; dùng cẩn thận.
- Chưa mở trang chính thức của NVD về CPE Dictionary (trang `nvd.nist.gov/products/cpe` trả về nội dung rỗng khi fetch); chưa xác nhận số mục CPE hiện tại hay chính sách gán CPE mới cho 2026.
- SPDX 3.0: chưa kiểm chứng trạng thái và ngày phát hành trên spdx.dev.
- Chưa tìm được tài liệu công khai mô tả *thuật toán* chuẩn hoá tên của Microsoft, Qualys hay Flexera; Flexera nói rõ đó là IP.
- Truy vấn đã thử cho NVD CPE: "NVD CPE dictionary deprecation 2025 CPE match criteria changes", "NVD CPE dictionary 2026 announcement CPE assignment backlog", "NVD legacy CPE dictionary feed retirement 2.0 API".

## 3c. Map nguồn host vào OCSF 1.9.0 và mapping công khai

### Kết luận ngắn
OCSF 1.9.0 có chỗ cho hầu hết bằng chứng host:
- `5020` cho inventory;
- `1007` / `1005` / `1002` cho runtime, với `file.product`, `company_name`, `version`, `internal_name`, `signatures`;
- `201004` cho service Windows;
- `5040` cho port, service, startup item;
- `6002` cho cài/gỡ.

Nhưng model có những chỗ vướng:
- `5020.package` đã deprecated từ 1.4.0 nhưng `sbom` lại bắt buộc `package` và `software_components`.
- Không có field chuẩn cho install time, EOL hay evidence path.
- Ví dụ `cpe_name` vẫn dùng định dạng CPE 2.2.

Mapping cộng đồng thì lệch nhau: Tenzir (target 1.9.0) giữ đủ `FileVersion`, `Product`, `Company`; mẫu AWS Security Lake (OCSF v1.0.0) bỏ hẳn chúng. Mức chắc chắn: **cao** (đọc trực tiếp schema và source code).

### Phát hiện có nguồn

**Schema OCSF 1.9.0 (đọc trực tiếp từ clone tag 1.9.0)**

- **5020 Software Inventory Info**: `device` required; `package` có `@deprecated` "Use the sbom attribute instead", since 1.4.0; `sbom` recommended; `product` optional ("Additional product attributes… enriched from a catalog"). Nguồn: [software_info.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/software_info.json), [CHANGELOG](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md) "Deprecated `package` in `Software Inventory Info` in favour of `sbom`" #1262 (bậc 1, 2026-08)
- **`sbom`**:
  - `package` required ("The software package or library that is being discovered or inventoried by an SBOM");
  - `software_components` required;
  - `product` là công cụ sinh SBOM (cdxgen, Syft);
  - `type_id`: 1 SPDX, 2 CycloneDX, 3 SWID.

  Nguồn: [sbom.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/sbom.json) (bậc 1)
- **`package`**:
  - Có: `name` và `version` (required), `vendor_name`, `purl`, `cpe_name`, `epoch`, `release`, `architecture`, `package_manager`, `package_manager_url`, `hash`, `license`, `src_url`, `uid`.
  - `type_id` chỉ có 1 Application, 2 Operating System.
  - **Không có** path, install time, publisher riêng hay EOL.

  Nguồn: [package.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/package.json) (bậc 1)
- **`product`**: `name`, `uid`, `vendor_name`, `version`, `cpe_name`, `path` ("installation path"), `lang`, `feature`, `url_string` — [product.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/product.json) (bậc 1). Toàn dictionary 1.9.0 không có field nào cho end-of-life/end-of-support hay install date (grep `dictionary.json`).
- **`cpe_name`**: ví dụ trong dictionary là `cpe:/a:apple:safari:16.2`, tức **CPE 2.2 URI**, không phải CPE 2.3 formatted string (`cpe:2.3:a:…`) — [dictionary.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/dictionary.json) (bậc 1)
- **`software_component`**: `type_id` 1 Framework, 2 Library, 3 Operating System; `relationship_id` 1 Depends On; `purl` recommended — [software_component.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/software_component.json) (bậc 1)
- **`file`** (dùng trong `process.file`, `module.file`, `driver.file`):
  - `product` ("The product that created or installed the file"), `company_name`, `version` (vd `8.0.7601.17514`), `desc`, `hashes`;
  - `internal_name` (mô tả nêu rõ VERSIONINFO của PE và Info.plist macOS: "the on-disk file name is not reliable");
  - `signature` deprecated từ 1.8.0, thay bằng `signatures`.

  Nguồn: [file.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/file.json) (bậc 1)
- **System category**: 1002 Kernel Extension Activity (`driver`, activity Load/Unload); 1005 Module Activity (`module`, Load/Unload/Invoke); 1007 Process Activity — [events/system @1.9.0](https://github.com/ocsf/ocsf-schema/tree/1.9.0/events/system) (bậc 1)
- **5040 Live Evidence Info**:
  - Có `query_evidence.query_type_id`: 6 Module, 7 Network Connection, 10 Process, 11 Service, 15 Startup Item, 16/17 Registry Key/Value, 18 Prefetch.
  - Với Service, field là `query_evidence.service`, kiểu object `service` mỏng (`name`, `uid`, `version`), **không có** state, start type hay binary path.
  - Muốn biết trạng thái thì dùng `startup_item`: `type_id` 3 Service; `start_type_id` 1 Auto, 2 Boot, 3 On Demand, 4 Disabled…; `run_state_id` 4 Running; extension Windows thêm `startup_item.win_service`.
  - Extension Windows thêm `reg_key`/`reg_value` cho `query_evidence`.

  Nguồn: [query_evidence.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/query_evidence.json), [startup_item.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/startup_item.json), [extensions/windows/objects](https://github.com/ocsf/ocsf-schema/tree/1.9.0/extensions/windows/objects) (bậc 1)
- **201004 Windows Service Activity** (ext Windows uid 2, class 4):
  - activity: 1 Create, 2 Reconfigure, 3 Start, 4 Stop, 5 Pause, 6 Continue, 7 Delete;
  - `win_service` required, `prev_win_service` thêm ở 1.9.0 (#1663);
  - extension Windows còn thêm `process.hosted_services`.

  Nguồn: [windows_service_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/windows/events/windows_service_activity.json), [CHANGELOG](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md) (bậc 1)
- **6002 Application Lifecycle**: `application` (recommended, mới 1.9.0) thay `app` (deprecated; trước đây "captioned 'Application' but typed as the product object", #1702); object `application` có thêm `product` "carrying product identity such as vendor_name, cpe_name, and canonical version" — [application_lifecycle.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/application/application_lifecycle.json), [application.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/application.json) (bậc 1)
- **4001 Network Activity**: activity Listen ("A network endpoint began listening for new network connections") — [network_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network_activity.json) (bậc 1)

**Mapping công khai**

- **Tenzir library** (target `"1.9.0"`, commit `932bfb2`, 2026-11-03):
  - Sysmon 1 → 1007 Launch. `FileVersion`→`process.file.version`, `Description`→`process.file.desc`, `Company`→`process.file.company_name`, `OriginalFileName`→`process.file.internal_name`, `Product`→`process.file.product.name`; `process.name` lấy phần cuối của path.
  - Sysmon 7 → **1005 Module Activity** Load; cũng map các field trên vào `module.file.*`; chỉ tạo `product` khi có giá trị ("product.name is a required field"); `"-"` thành null; `Signature` → `module.file.signature.certificate.issuer` (dùng field `signature` đã deprecated và đặt tên người ký vào issuer).
  - Sysmon 6 → 1002 Kernel Extension Activity Load; Sysmon 3 → 4001 Open, với `direction_id` = 2 nếu `Initiated`, ngược lại 1; Sysmon 4 → 201004.
  - Windows 7045 → 201004 Create (`win_service.name`, `cmd_line`=ImagePath, `service_file.path` tách từ ImagePath, `service_type_id`/`service_category_id` theo ServiceType); 4697 → 201004 Create (`service_start_type_id` theo ServiceStartType).
  - AppXDeployment 400/401/404 → 6002 Install (`application.name` = PackageDisplayName).

  Nguồn: [tenzir/library microsoft/operators/windows/ocsf](https://github.com/tenzir/library/tree/main/microsoft/operators/windows/ocsf) (bậc 1, source code 2026-11)
- **Tenzir, Microsoft Graph/Intune `detectedApps` → 5020**: dùng `package` (đã deprecated) với `type_id` 1, nhân bản sang `product`; **`device` là placeholder `"Microsoft Intune managed devices"`, `type_id` 0**, vì endpoint này "reports aggregate software inventory, not a specific device"; `deviceCount` để trong `unmapped` — [detected_app.tql](https://github.com/tenzir/library/blob/main/microsoft/operators/graph/ocsf/events/detected_app.tql) (bậc 1, 2026-11)
- **AWS Security Lake transformation library** (commit 2025-05-06):
  - Sysmon 1/5 → 1007, `metadata.version` "v1.0.0"; `process.name` = cả `Image` (full path); `loaded_modules` = `ImageLoaded`.
  - **Không map `FileVersion`, `Product`, `Company`, `Hashes`**, kể cả vào `unmapped` (chỉ giữ `rulename`).
  - Bảng tổng: 6 → "KERNEL_ACTIVITY", 7 → PROCESS_ACTIVITY, 8 CreateRemoteThread → NETWORK_ACTIVITY.
  - Thực tế chỉ có 4 event thuộc 2 class được map trong JSON.

  Nguồn: [windows-sysmon-mapping.md](https://github.com/aws-samples/amazon-security-lake-transformation-library/blob/main/mapping_docs/windows-sysmon-mapping.md), [windows_sysmon.json](https://github.com/aws-samples/amazon-security-lake-transformation-library/blob/main/transformation_function/mappings/windows_sysmon.json) (bậc 1, 2025-05)
- **Datadog**: pipeline Sysmon có OCSF normalization, merge 2026-09-18, gồm 1001, 1002, 1005, 1007, 1008, 4001, 4003, 6002, 6008; PR không nêu phiên bản OCSF hay map từng field — [DataDog/integrations-core #25250](https://github.com/DataDog/integrations-core/pull/25250) (bậc 1, 2026-09)
- **Đánh giá độc lập** (Jeremy Wiley, 2026-06, cập nhật 2026-08): mapping Sysmon của Tenzir 6.0.0 (OCSF 1.8.0) "expects raw Windows EVTX/XML and rejects the pre-parsed JSON"; Zeek conn sai `activity_id` ở 83% bản ghi, `service` rơi vào `unmapped` — [Six schemas into OCSF](https://securitydataworks.com/writing/ocsf/six-schemas-into-ocsf/) (bậc 2, 2026-08; benchmark tự dựng, dữ liệu tổng hợp)
- **osquery → OCSF, Wazuh → OCSF**: không tìm thấy mapping công khai nào cho inventory (packages, ports, services). Tenzir library không có thư mục osquery/wazuh (đã liệt kê thư mục gốc, commit `932bfb2`).

**Bảng map đề xuất (Nhận định, dựa trên schema đã đọc)**

| Nguồn / bằng chứng | OCSF 1.9.0 đích | Ghi chú |
|---|---|---|
| MDVM `DeviceTvmSoftwareInventory`, Tenable 20811/22869, Wazuh `sys_programs`, osquery `programs`/`deb_packages`/`rpm_packages`/`apps`/`python_packages` | 5020: `device` + `sbom.package` (hoặc `package` deprecated); `product` cho tên/vendor đã chuẩn hoá theo catalog | `cpe_name`/`purl` vào `package`; `EndOfSupportDate`, `install_date`/`installed`, `install_location`, registry/disk evidence của MDVM → **không có field chuẩn**, vào `unmapped` (riêng `install_location` có thể vào `product.path`) |
| Intune/Graph aggregated app | 5020 nhưng không gắn device | Không dùng làm bằng chứng per-asset |
| Sysmon 1 / EDR process | 1007 `process.file.{version, product.name, company_name, internal_name, desc, hashes, signatures}` | Bằng chứng "đã chạy"; kiểm tra mapper có giữ VERSIONINFO không (AWS sample bỏ) |
| Sysmon 7 | 1005 `module.file.*` | Thường tắt; nhiều nhiễu |
| Sysmon 6 | 1002 `driver.file.*` + `signatures` | Driver phần mềm bảo mật/VPN |
| Sysmon 3 | 4001 + `actor.process` | `Initiated=false` + port local cố định là bằng chứng phía server |
| osquery `listening_ports`, Wazuh `sys_ports` (state listening) | 5040 `query_type_id` 7 + `connection_info` + `process`, hoặc 4001 activity 7 Listen; hoặc `device.network_interfaces[].open_ports` trong 5001 | `open_ports` không có PID/process; nên ưu tiên 5040 nếu cần nối process |
| osquery `services`/`systemd_units`/`launchd`, Wazuh `sys_services` | 5040 `query_type_id` 15 `startup_item` (`type_id` 3, `start_type_id`, `run_state_id`, Windows: `win_service`) hoặc 11 `service` | `query_evidence.service` thiếu state/path |
| Windows 7045 / 4697 | 201004 activity 1 Create, `win_service` | Bằng chứng service mới, không phải "đang chạy" |
| AppX, MSI install, package manager log | 6002 Install/Remove/Update, `application.product` | `application.product` mới ở 1.9.0 |
| `sys_hotfixes`, KB | 5004 OS Patch State (theo report kế thừa) | |

### Nhận định
- Chỗ vướng thực tế: một inventory host có hàng trăm gói, nhưng `sbom.package` bắt buộc **một** package cùng mảng `software_components`. Mapper vì vậy hoặc phát một event 5020 cho mỗi gói (dùng `package` deprecated như Tenzir), hoặc gói tất cả vào `software_components` với một `package` giả. Bước extract phải đọc được cả ba kiểu: `package`, `sbom.package`, `sbom.software_components[]`.
- `cpe_name` có thể là CPE 2.2 hoặc 2.3 (ví dụ chính thức trong schema là 2.2), nên cần parse cả hai về `vendor:product`.
- Bằng chứng VERSIONINFO trong 1007 phụ thuộc vào mapper: Tenzir giữ, AWS sample bỏ. Kho entity cần một kiểm tra chất lượng theo nguồn, chẳng hạn tỉ lệ event 1007 có `process.file.product`.
- Vì OCSF không có field EOL, install time hay evidence path, các thông tin quan trọng cho `asset_software` (first seen, cài khi nào, hết support) sẽ nằm trong `unmapped` hoặc phải lấy từ catalog ngoài (MDVM `EndOfSupportDate`, Qualys lifecycle).

### Khoảng trống
- Splunk OCSF add-on, ocsf-examples: chưa kiểm tra, vì hết ngân sách.
- Wazuh có tích hợp Amazon Security Lake, nhưng theo hiểu biết chung nó chỉ chuyển alert, không chuyển syscollector inventory. Chưa xác minh.
- Chưa thấy mapping công khai osquery → OCSF 5020/5040. Truy vấn "osquery OCSF mapping software inventory info packages programs" không ra kết quả liên quan.

## Truy vấn đã chạy
- ECMA-427 Package-URL purl standard (standard)
- NVD CPE dictionary deprecation 2025 CPE match criteria changes (extended)
- Qualys software normalization Technology Catalog CSAM lifecycle (standard)
- Tenable plugin 20811 Microsoft Windows installed software enumeration credentialed (standard)
- Sysmon to OCSF mapping process_activity FileVersion Product Company file.product (extended)
- osquery OCSF mapping software inventory info packages programs (extended)
- NVD CPE dictionary 2026 announcement CPE assignment backlog (extended)
- Axonius software normalization aggregated software adapter (standard)
- CycloneDX 1.7 release 2025 SPDX 3.0 SWID tags NIST IR 8060 status (standard)
- NVD legacy CPE dictionary feed retirement 2.0 API (standard, giới hạn nvd.nist.gov/nist.gov)
- Flexera Technopedia normalization raw software title to product release (standard)
- Ngoài ra: đọc trực tiếp schema OCSF 1.9.0 (clone local), clone và grep `tenzir/library`, `aws-samples/amazon-security-lake-transformation-library`, `osquery/osquery` (specs).
