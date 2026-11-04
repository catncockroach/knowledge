# Bản đồ quan sát trong OCSF 1.9.0

Nguồn chính là bản clone `ocsf-schema` ở tag `1.9.0` (commit `856d462`, ngày 2026-08-03). Mọi link schema dạng `https://github.com/ocsf/ocsf-schema/blob/1.9.0/<path>` đều là bậc 1. Mapping của bên thứ ba lấy từ `tenzir/library` (commit `932bfb2`, ngày 2026-11-03) và `ocsf/examples`. Seed (`discussion-seed.md`) đã được đối chiếu lại: phần lớn đúng. Các chỗ sai hoặc thiếu ghi ở mục **Đính chính seed**.

## Câu hỏi phụ 1: Class, object, field nào chứa bằng chứng về thiết bị, dịch vụ và ứng dụng; thông tin bị phân tán theo những kiểu nào?

### Kết luận ngắn

OCSF 1.9.0 có đủ chỗ để chứa bằng chứng cho cả ba mục tiêu. Tuy vậy, bằng chứng nằm rải ở khoảng 25 class và 40 object. Không có object nào biểu diễn "service đang lắng nghe trên host" mà có đủ sản phẩm và phiên bản. Không có observable type nào cho tên phần mềm, CPE, purl hay JA3/JA4. Linux và macOS không có extension riêng cho daemon, systemd, launchd hay package: hai extension này chỉ thêm uid/gid cho process. **Mức chắc chắn: cao** về cấu trúc schema, vì đã đọc trực tiếp JSON. **Trung bình** về cách các mapper thực tế đổ dữ liệu vào schema, vì mới kiểm tra mapper của Tenzir (Zeek, Suricata) và AWS (VPC Flow, Route 53, WAF).

### Đính chính seed

- **`5020.package` đã deprecated từ 1.4.0** và được thay bằng `sbom` (`sbom.package` + `sbom.software_components`). Seed coi `package` là field chính mà không ghi chú điều này. Dữ liệu cũ hoặc mapper cũ vẫn có thể điền `package`, nên khi đọc phải xét cả hai đường — [software_info.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/software_info.json), [CHANGELOG mục 1.4.0 "Deprecated `package` in `Software Inventory Info` in favour of `sbom`" #1262](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md) (bậc 1, 2025-01)
- **`tls.sans` đã deprecated từ 1.4.0** và được thay bằng `tls.certificate.sans` (#1325). Seed liệt kê `tls.sans` như field bình thường — [tls.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/tls.json), [CHANGELOG](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md) (bậc 1)
- **`4009` Email Activity extends `base_event`, không extends `network`.** Vì vậy class này không có `tls`, `ja4_fingerprint_list`, `app_protocol_name` hay `observation_point_id`, chỉ có `src_endpoint`, `dst_endpoint`, `banner`, `protocol_name` — [email_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/email_activity.json) (bậc 1)
- Seed bỏ sót **`network_endpoint.fingerprints`** (thêm ở 1.8.0, #1560), mô tả là "Fingerprints that identify the specific application implementation on this endpoint, such as Cisco NPF or HASSH". Seed cũng bỏ sót enum `fingerprint.algorithm_id` có `18 Imphash`, `19 NPF`, `20 HASSH` — [network_endpoint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/network_endpoint.json), [fingerprint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/fingerprint.json), [issue #1556](https://github.com/ocsf/ocsf-schema/issues/1556) (bậc 1, 2026-01)
- Mốc phiên bản của các field nhắc trong seed, theo CHANGELOG:
  - 1.6.0: `observation_point`/`observation_point_id` (#1481), `is_src_dst_assignment_known` (#1464), `open_ports`/`port_info` (#1466).
  - 1.8.0: `app_protocol_name` (#1557), `network_observation_point` (#1571), `mac_vendor` (#1575).
  - 1.9.0: `initiator_id` (#1598); `is_src_dst_assignment_known` bị deprecated.

  Nguồn: [CHANGELOG](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md) (bậc 1)
- Seed viết "5040 thay cho 5016 Service Query, 5012…". Điều này đúng: 17 class query bị deprecated **từ 1.5.0** (#1382). Cần bổ sung: `query_type_id` 11 Service trỏ tới object **`service` mỏng của core** (`name`, `uid`, `version`, `labels`, `tags`), không trỏ tới `win_service`. Extension Windows của `query_evidence` chỉ thêm `reg_key`/`reg_value` — [query_evidence.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/query_evidence.json), [windows/objects/query_evidence.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/windows/objects/query_evidence.json), [service_query.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/service_query.json) (bậc 1)

### Phát hiện có nguồn

**Extension theo OS**
- Extension `linux` (uid 1) chỉ có `objects/process.json` và profile `linux_users`, gồm `auid`, `euid`, `egid`, `group`. Extension `macos` chỉ có `process.json` và profile `macos_users`, gồm `euid`, `egid`. Cả hai không có object nào cho systemd unit, launchd plist, daemon hay package — [linux/extension.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/linux/extension.json), [linux_users.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/linux/profiles/linux_users.json), [macos_users.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/macos/profiles/macos_users.json) (bậc 1)
- Thông tin systemd và launchd nằm ở **core**:
  - `job.type_id` có `1 Task Scheduler, 2 Cron, 3 Systemd, 4 Launchd`.
  - `startup_item.type_id` có `1 Kernel Mode Driver, 2 User Mode Driver, 3 Service, 4 User Mode Application, 5 Autoload, 6 System Extension, 7 Kernel Extension, 8 Scheduled Job, Task`.
  - `startup_item.run_state_id` có `4 Running`.
  - `startup_item.start_type_id` có `1 Auto, 2 Boot, 3 On Demand, 4 Disabled, 5 All Logins…`.

  Nguồn: [job.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/job.json), [startup_item.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/startup_item.json) (bậc 1)
- Ở 1.9.0, `job.cmd_line`, `job.last_run_time` và `job.next_run_time` bị deprecated, chuyển sang `job_actions[].cmd_line` và `job_triggers[]` (#1597) — [job.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/job.json), [CHANGELOG](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md) (bậc 1)
- Extension Windows còn có:
  - `process.hosted_services` (mảng `win_service`), cho biết process `svchost` đang host service nào;
  - `startup_item.win_service`;
  - `win_service` với `service_category_id`, `service_dependencies`, `load_order_group`, `prev_win_service` (1.9.0, #1663);
  - `win_resource.svc_name` ("The Windows service acting as the object server…").

  `prefetch_query` (uid 19 của extension, tức 205019) đã deprecated. Field `run_count` và `last_run_time` của nó là bằng chứng "ứng dụng đã từng chạy" — [windows/dictionary.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/windows/dictionary.json), [windows/objects/process.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/windows/objects/process.json), [prefetch_query.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/windows/events/prefetch_query.json) (bậc 1)
- PR **#1725 (đang mở, 2026-08-12)** đề xuất object `control_group` (Linux cgroup / Windows job object) và `process.control_group`. Lý do nêu trong PR: "Producers that observe this, such as eBPF-based and LSM-based security sensors, currently have to put it under `unmapped`… Group membership is the natural key for attributing kernel-level activity to a container, pod, system service or user session." Nghĩa là ở 1.9.0, việc gắn một process với systemd unit (qua cgroup) chưa có field chuẩn — [PR #1725](https://github.com/ocsf/ocsf-schema/pull/1725) (bậc 1, 2026-08)

**Profile**
- `host`: thêm `device` (recommended) và `actor`. Mô tả: "Apply this profile when the event originates from or is observed on a specific host" — [profiles/host.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/profiles/host.json) (bậc 1)
- `network_proxy`: thêm `proxy_connection_info`, `proxy_endpoint`, `proxy_http_request`, `proxy_http_response`, `proxy_tls`, `proxy_traffic`. Profile này được gắn vào base `network` (cùng `load_balancer`, `ai_operation`) và vào `6001` Web Resources Activity — [network_proxy.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/profiles/network_proxy.json), [network.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network.json) (bậc 1)
- `load_balancer`: thêm object `load_balancer`, gồm `ip` (IP node LB), `dst_endpoint` (backend target), `endpoint_connections[].network_endpoint`/`code`, `name`, `uid` — [load_balancer.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/load_balancer.json) (bậc 1)
- `container`: thêm `container` và `namespace_pid`. Profile này gắn vào `endpoint`, nên mọi `device`/`src_endpoint`/`dst_endpoint` đều có thể mang `container`. `container` có `image` (`name`, `uid`, `path`; `tag` đã deprecated từ 1.4.0, thay bằng `labels`/`tags`), `runtime`, `orchestrator`, `hash`, `pod_uuid` — [container.json profile](https://github.com/ocsf/ocsf-schema/blob/1.9.0/profiles/container.json), [objects/container.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/container.json), [image.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/image.json) (bậc 1)
- `cloud`: thêm `cloud` (`provider`, `account`, `region`, `zone`) và `api` (`service`, `operation`, `version`) — [profiles/cloud.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/profiles/cloud.json), [api.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/api.json) (bậc 1)
- `osint`: thêm `osint`, với `type_id` gồm `6 User Agent`, `7 Digital Certificate`, `3 Hostname`, `4 Hash`… và `confidence_id` — [osint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/osint.json) (bậc 1)

**Nguồn gốc log: `metadata`, `reporter`, `logger`**
- `metadata.product` (required) là "The product that reported the event". `metadata.log_source` là "The log system or component where the data originated… a Windows hostname and logging subsystem". `metadata.reporter` (thêm ở 1.7.0, #1476) có `hostname`, `ip`, `name`, `uid`, `org`. `metadata.loggers[]` chứa `logger.device` và `logger.product` của từng chặng — [metadata.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/metadata.json), [reporter.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/reporter.json), [logger.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/logger.json) (bậc 1)

**Observables**
- `observable.type_id` (lấy từ dictionary và object) gồm:
  - 1 Hostname, 2 IP, 3 MAC, 6 URL String, 7 File Name, 8 Hash, 9 Process Name, 10 Resource UID, 11 Port, 13 Command Line, 16 **HTTP User-Agent**;
  - 20 Endpoint, 23 URL, 24 File, 25 Process, 27 Container, 30 Fingerprint;
  - 37 serial_number, 38 resource_details.name, 39 process_entity.uid, 47 device.uid, 48 network_endpoint.uid;
  - extension Windows: 28/29 registry key/value, 46 Registry Key Path.

  **Không có** type nào cho product name, CPE, purl, service name, app_name hay JA3/JA4. JA3/JA4 chỉ được index gián tiếp qua type 30 `fingerprint` (với JA3) — [dictionary.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/dictionary.json), [observable.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/observable.json), [device.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/device.json) (bậc 1)

**Fingerprint**
- `ja4_fingerprint.type_id` gồm `1 JA4, 2 JA4Server, 3 JA4HTTP, 4 JA4Latency, 5 JA4X509, 6 JA4SSH, 7 JA4TCP, 8 JA4TCPServer, 9 JA4TCPScan, 99 Other`, và có thêm `section_a…d`. `ja4_fingerprint_list` nằm ở base `network` và trong `evidences` — [ja4_fingerprint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/ja4_fingerprint.json) (bậc 1)
- Bộ JA4+ hiện tại của FoxIO còn có **JA4LatencyServer (JA4LS), JA4DHCP (JA4D), JA4DHCPv6 (JA4D6), JA4NTP (JA4N), JA4Scan-TLS, JA4Scan-QUIC**, nhưng enum OCSF 1.9.0 không có các loại này. Chỉ JA4 là BSD-3; các loại còn lại theo "FoxIO License 1.1" — [FoxIO-LLC/ja4 README](https://github.com/FoxIO-LLC/ja4) (bậc 1, truy cập 2026-11-04)
- `tls.ja3_hash` và `tls.ja3s_hash` có kiểu `fingerprint` ("The MD5 hash of a JA3 string"). `tls` còn có `client_ciphers`, `server_ciphers`, `extension_list`, `tls_extension_list`, `certificate`, `certificate_chain`, `sni`, `version`, `cipher` — [tls.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/tls.json) (bậc 1)
- `hassh` = {`algorithm`, `fingerprint`}, được dùng ở `4007.client_hassh`/`server_hassh` — [hassh.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/hassh.json), [ssh_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/ssh_activity.json) (bậc 1)
- `certificate` có `subject`, `issuer`, `sans`, `fingerprints`, `is_self_signed`, `serial_number`, `expiration_time` — [certificate.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/certificate.json) (bậc 1)

**HTTP, URL, DNS, DHCP**
- `http_response` chỉ có `code`, `status`, `content_type`, `http_headers`, `length`, `body_length`, `latency`; `message` bị deprecated ở 1.9.0. **Không có field `server`**, nên header `Server` chỉ nằm trong mảng `http_headers` (name/value). `user_agent` (dictionary): "The request header that identifies the operating system and web browser" — [http_response.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/http_response.json), [http_request.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/http_request.json), [http_header.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/http_header.json) (bậc 1)
- `url.category_ids` là enum hạng mục **website** (không phải ứng dụng), ví dụ `51 Chat (IM)/SMS`, `56 File Storage/Sharing`, `57 Remote Access Tools`, `85 Office/Business Applications`, `111 Online Meetings`, `109 Internet Connected Devices`. Trong OCSF không có field "SaaS app id" — [dictionary.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/dictionary.json), [url.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/url.json) (bậc 1)
- DNS ở 1.9.0:
  - `dns_answer` giờ extends `dns_resource_record` (`class`, `hostname`, `rdata`, `ttl`, `type`).
  - `flags`, `flag_ids`, `opcode`, `packet_uid` trên `dns_query`/`dns_answer` bị deprecated, chuyển lên `dns_activity` (`transaction_id`, `flags`, `opcode`, #1634).
  - `4003` có `query`, `answers`, `authority`, `query_additional`, `response_additional`.

  Nguồn: [dns_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/dns_activity.json), [dns_answer.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/dns_answer.json), [CHANGELOG](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md) (bậc 1)
- `4004` DHCP có `activity_id` 1 Discover … 9 Expire, `is_renewal`, `lease_dur`, `relay`, `transaction_uid`, `src_endpoint`, `dst_endpoint`. Không có field nào cho option 55, 60, 61 hay 12. Hostname client chỉ có thể đặt vào `src_endpoint.hostname`. Search issue/PR trên ocsf-schema với từ khoá "dhcp" không thấy đề xuất nào về fingerprint/option, chỉ thấy #886/#887 (DHCP extends Network) và #1400 (`is_renewal`) — [dhcp_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/dhcp_activity.json), [search issues dhcp](https://github.com/ocsf/ocsf-schema/issues?q=dhcp) (bậc 1, 2026-11-04)

**Ứng dụng: các class và object**
- Object `application` (thêm ở 1.5.0 cùng `2007` Application Security Posture Finding, #1357) được mô tả là "an inventoried application as reported by an Application Security tool or other Developer-centric tooling… Kubernetes resources, Containerized resources… AWS Elastic BeanStalk". Object này có `name`, `uid`, `uid_alt`, `version`, `hostname`, `url`, `owner`, `sbom`, `type` (free string, ví dụ "GitHub"), `criticality`, `risk_level_id`, `resource_relationship` (graph), và `product` (thêm ở 1.9.0) — [application.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/application.json), [application_security_posture_finding.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/findings/application_security_posture_finding.json) (bậc 1)
- PR #1702 (1.9.0) sửa sự nhầm lẫn Application/Product:
  - `6002.app` (caption "Application" nhưng kiểu `product`) bị deprecated, thay bằng `application`;
  - `actor.app_name`/`app_uid` bị deprecated, thay bằng `actor.application`;
  - "The `app_name` usage in `Network` is unchanged - there it is a DPI/NBAR traffic classification label, not an application entity."

  Nguồn: [CHANGELOG 1.9.0](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md), [PR #1702](https://github.com/ocsf/ocsf-schema/pull/1702) (bậc 1, 2026-07)
- `product` có `name`, `vendor_name`, `version`, `cpe_name`, `path` (installation path), `uid`, `url_string`, `lang`, `feature`. Object này xuất hiện ở `metadata.product` (sản phẩm ghi log), `file.product`, `5020.product` ("discovered or enriched from a catalog"), `application.product`, `sbom.product` (công cụ tạo SBOM) — [product.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/product.json), [software_info.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/software_info.json) (bậc 1)
- `package` có `name`, `version` (required), `vendor_name`, `purl`, `cpe_name`, `package_manager`, `architecture`, `epoch`, `release`, `hash`, `license`, `type_id` (1 Application, 2 Operating System). `software_component.type_id` có 1 Framework, 2 Library, 3 OS. `sbom.type_id` có 1 SPDX, 2 CycloneDX, 3 SWID — [package.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/package.json), [software_component.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/software_component.json), [sbom.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/sbom.json) (bậc 1)
- `5004` Patch State (`device`, `kb_article_list`) cho biết bản vá OS đã cài. `5023` Cloud Resources Inventory Info có `cloud`, `container`, `database`, `databucket`, `idp`, `resources`, `table`. `6005` Datastore có `database` (`type_id`: 1 Relational … 6 NoSQL, 7 Vector, 8 Knowledge Graph), `databucket`, `table`, `query_info`, `src_endpoint`, `dst_endpoint` — [patch_state.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/patch_state.json), [cloud_resources_inventory_info.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/cloud_resources_inventory_info.json), [datastore_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/application/datastore_activity.json), [database.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/database.json) (bậc 1)
- Các object khác:
  - `kernel_driver` chỉ có `file`; được dùng ở `1002` Kernel Extension Activity (`driver`, required) và `startup_item.driver`.
  - `module` có `file`, `load_type_id`, `type`.
  - `process.loaded_modules` là danh sách tên module.
  - `peripheral_device` có `vendor_name`, `model`, `vendor_id_list`, `serial_number`.

  Nguồn: [kernel_driver.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/kernel_driver.json), [kernel_extension_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/system/kernel_extension_activity.json), [module.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/module.json), [process.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/process.json) (bậc 1)

**Thiết bị**
- `device`/`endpoint`:
  - `os.type_id` có 100 Windows, 101 Windows Mobile, 200 Linux, 201 Android, 300 macOS, 301 iOS, 302 iPadOS, 400 Solaris, 401 AIX, 402 HP-UX.
  - `os` có `cpe_name`, `kernel_release`, `build`, `edition`.
  - `hw_info` có `vendor_name`, `serial_number`, `uuid`, `chassis`, `bios_*`. Các field CPU phẳng bị deprecated ở 1.9.0, chuyển sang `cpu_info_list[*]` (#1630).
  - `device` có `hypervisor`, `image`, `is_managed`, `udid`, `imei_list`, `boot_uid`, `os_machine_uuid`.
  - `network_interface.type_id` có 1 Wired, 2 Wireless, 3 Mobile, 4 Tunnel.

  Nguồn: [os.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/os.json), [device_hw_info.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/device_hw_info.json), [device.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/device.json), [network_interface.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/network_interface.json) (bậc 1)
- Issue #1752 (đang mở, 2026-09-06): "`endpoint.owner` conflates accountable owner with last logged-in account… a consumer cannot tell which one a producer populated" — [issue #1752](https://github.com/ocsf/ocsf-schema/issues/1752) (bậc 1)
- PR #1466 (`open_ports`, 1.6.0) ghi: "Down the roads, we can also tie in the services that are listening on those ports, in the same `port_info` object". Đến 1.9.0, `port_info` vẫn chỉ có `port`, `protocol_name`, `protocol_num`: không có tên service, sản phẩm hay phiên bản — [PR #1466](https://github.com/ocsf/ocsf-schema/pull/1466), [port_info.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/port_info.json) (bậc 1, 2025-07)
- Issue #1384 (đang mở, 2025-03-26), "Profiles for Network Activity": "When mapping rich protocol data (like Zeek logs), critical protocol attributes must be forced into generic fields or left unmapped, leading to inconsistent implementations and lost security context." — [issue #1384](https://github.com/ocsf/ocsf-schema/issues/1384) (bậc 1)

**Mapper thực tế: field nào đi vào đâu**
- **Tenzir Zeek→OCSF** nhắm OCSF 1.9.0. Mapper có `metadata.version: "1.9.0"`. Changelog của mapper ghi: "now writes the protocol identified by Zeek, such as `http`, to OCSF 1.9's `app_protocol_name` field instead of `app_name`". Changelog khác ghi: "unsupported protocol details remain in `unmapped`" — [ocsf-application-protocol-fields.md](https://github.com/tenzir/library/blob/main/zeek/changelog/unreleased/ocsf-application-protocol-fields.md), [expanded-ocsf-field-coverage.md](https://github.com/tenzir/library/blob/main/zeek/changelog/unreleased/expanded-ocsf-field-coverage.md) (bậc 1, 2026-05 và 2026-10)
- Mapper riêng chỉ có cho `conn, dhcp, dns, ftp, http, rdp, smb_files, smtp, ssh, ssl, x509`. Các log `software.log`, `known_services.log`, `known_hosts.log` **không có mapper riêng** và rơi vào nhánh mặc định `zeek::ocsf::base`. Cuối pipeline, mapper chạy `$ocsf.unmapped = move $event` (mọi field chưa `move` đều vào `unmapped`) — [zeek/operators/ocsf/map.tql @932bfb2](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/map.tql) (bậc 1, 2026-11-03)
- Chi tiết theo log của mapper Zeek:
  - `conn.service` → `app_protocol_name`; `history` → `connection_info.flag_history`.
  - Zeek DHCP: chỉ map `host_name` → `src_endpoint.hostname`, `client_fqdn` → `src_endpoint.domain`, `mac`, `client_addr`/`assigned_addr`, `server_addr`, `domain`, `lease_time`. Các field khác của dhcp.log còn lại trong `unmapped`.
  - Zeek SSH: chuỗi phần mềm client/server (ví dụ `OpenSSH_8.9`) → `src_endpoint.agent_list[]`/`dst_endpoint.agent_list[]` với `type_id: 9 Remote Access`; HASSH → `client_hassh`/`server_hassh`.
  - Zeek HTTP: `client_headers`/`server_headers` → `http_request.http_headers`/`http_response.http_headers`; `user_agent` → `http_request.user_agent`.
  - Zeek SSL: `ja3`/`ja3s` → `tls.ja3_hash`/`ja3s_hash`; `server_name` → `tls.sni`.

  Nguồn: [conn.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/logs/conn.tql), [dhcp.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/logs/dhcp.tql), [ssh.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/logs/ssh.tql), [http.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/logs/http.tql), [ssl.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/logs/ssl.tql) (bậc 1)
- **Tenzir Suricata→OCSF**:
  - `app_proto` → `app_protocol_name`, trừ khi giá trị là `failed`.
  - `tls.ja4` → `ja4_fingerprint_list[{type_id: 1, value}]`.
  - `tls.subjectaltname` → `tls.certificate.sans`.
  - `ssh.client/server.software_version` → `src/dst_endpoint.agent_list[{name, type_id: 9}]`.
  - `http_user_agent` → `http_request.user_agent`.
  - Cuối pipeline cũng chạy `$ocsf.unmapped = move $event`.

  Nguồn: [suricata/operators/ocsf/map.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/suricata/operators/ocsf/map.tql), [suricata logs/ssh.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/suricata/operators/ocsf/logs/ssh.tql), [suricata logs/tls.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/suricata/operators/ocsf/logs/tls.tql) (bậc 1)
- **AWS VPC Flow Logs → 4001** (mapping OCSF 1.5.0):
  - `pkt_src_aws_service`/`pkt_dst_aws_service` → `src/dst_endpoint.svc_name`.
  - `instance_id`, `interface_id`, `vpc_id`, `subnet_id` được gán vào `dst_endpoint` khi `flow_direction = ingress` và vào `src_endpoint` khi `egress`.
  - `dstaddr` → `intermediate_ips` khi khác `pkt_dstaddr`.
  - "Any fields not present in an explicit mapping will be mapped to the unmapped object."
  - Mapping không có field L7 hay app nào.

  Nguồn: [ocsf/examples AWS v1.5.0 VPC Flowlogs](https://github.com/ocsf/examples/blob/main/mappings/markdown/AWS/v1.5.0/VPC%20Flowlogs/README.md) (bậc 1, không rõ ngày)
- **AWS Route 53 Resolver → 4003**: `query_name` → `query.hostname`; `answers[].Rdata` → `answers[].rdata`; `srcids.instance` → `src_endpoint.instance_uid`; `srcids.resolver_endpoint` → `dst_endpoint.instance_uid`. Các field còn lại vào `unmapped` — [Route53 v1.5.0](https://github.com/ocsf/examples/blob/main/mappings/markdown/AWS/v1.5.0/Route53/README.md) (bậc 1)
- **AWS WAF → 4002** (1.1.0): lấy header `User-Agent` ra `http_request.user_agent`, `Host` ra `url.hostname`, `X-Forwarded-For` ra `x_forwarded_for`, và chép toàn bộ header vào `http_request.http_headers[]` — [WAF v1.1.0](https://github.com/ocsf/examples/blob/main/mappings/markdown/AWS/v1.1.0/WAF/README.md) (bậc 1)

### Bảng lớn: bằng chứng theo mục tiêu

Quy ước cột "Độ tin/hạn chế": **Cao** là dữ liệu khai báo hoặc thu từ OS/agent. **TB** là quan sát runtime hoặc giao thức có định danh phần mềm. **Thấp** là suy luận từ port, phân loại hoặc chuỗi tự do. Cột này là **Nhận định** của researcher, dựa trên bản chất nguồn, chưa có số đo.

| Mục tiêu | Class | Đường dẫn field | Ý nghĩa | Độ tin/hạn chế | Link |
|---|---|---|---|---|---|
| Thiết bị | 5001 Device Inventory Info | `device.type_id`, `os.{type_id,name,version,build,cpe_name,kernel_release}`, `hw_info.{vendor_name,serial_number,uuid,chassis}`, `vendor_name`, `model`, `is_managed`, `first_seen_time`, `last_seen_time` | Hồ sơ thiết bị do MDM/EDR/CMDB khai báo | Cao; `type_id` là enum cố định 15 giá trị, không có Printer/Camera/PLC (phải dùng 99 Other hoặc 7 IOT) | [device.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/device.json), [endpoint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/endpoint.json) |
| Thiết bị | Mọi class có profile `host` (System 1xxx, nhiều class khác) | `device.*`, `device.agent_list[].{type_id,name,version,vendor_name}` | Host nơi event xảy ra; agent đã cài (EDR, MDM, VM…) | Cao với agent EDR; tuỳ mapper điền đủ `os`/`hw_info` hay không | [host.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/profiles/host.json), [agent.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/agent.json) |
| Thiết bị | Mọi class | `metadata.reporter.{hostname,ip,uid}`, `metadata.loggers[].device`, `metadata.log_source` | Thiết bị phát ra log, ví dụ firewall hoặc syslog relay | TB; có thể là collector, không phải thiết bị gốc | [metadata.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/metadata.json), [reporter.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/reporter.json) |
| Thiết bị | Mọi class | `metadata.product.{vendor_name,name,version}` | Sản phẩm ghi log, tức là loại thiết bị mạng/bảo mật (ví dụ PAN-OS → firewall) | Cao cho chính thiết bị log; chỉ suy ra loại thiết bị qua catalog | [metadata.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/metadata.json) |
| Thiết bị | 4004 DHCP | `src_endpoint.{mac,hostname,domain,ip}`, `activity_id`, `lease_dur` | Gắn MAC↔IP↔hostname theo thời gian | Cao cho binding; **không có chỗ** cho option 55/60/61 nên vendor class/fingerprint rơi vào `unmapped` (mapper Zeek của Tenzir không map) | [dhcp_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/dhcp_activity.json), [Tenzir dhcp.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/logs/dhcp.tql) |
| Thiết bị | Network 4xxx | `src_endpoint.mac_vendor` (1.8.0), `mac` | Hãng NIC theo OUI | Thấp–TB; MAC ngẫu nhiên (privacy MAC) làm sai | [endpoint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/endpoint.json) |
| Thiết bị / ứng dụng | 4002 HTTP, 6001, 6003 | `http_request.user_agent` | OS, trình duyệt, client app | TB; chuỗi tự do, dễ giả mạo; OCSF không có object user-agent đã parse | [http_request.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/http_request.json), [dictionary.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/dictionary.json) |
| Thiết bị | Network | `ja4_fingerprint_list[type_id=7 JA4TCP]`, `network_endpoint.fingerprints[algorithm_id=19 NPF]` | Fingerprint TCP/NPF của stack OS | TB; JA4T và JA4TS bị trộn trong một list, không gắn với endpoint | [ja4_fingerprint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/ja4_fingerprint.json), [network_endpoint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/network_endpoint.json) |
| Thiết bị | Mọi class có `endpoint` | `*.container.{image.name,image.uid,runtime,orchestrator}`, `device.hypervisor`, `device.image` | Workload ảo hoá/container | Cao nếu lấy từ runtime/cloud | [container.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/container.json), [image.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/image.json) |
| Thiết bị (mạng) | Network | `observation_point_id` (1 Source, 2 Destination, 3 Neither, 4 Both), `network_observation_point` | Thiết bị quan sát (tap, IDS, firewall) | Cao cho vai trò "observer"; `network_observation_point` chỉ dùng khi `observation_point_id` = 3 | [network.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network.json) |
| Thiết bị (LB/proxy) | Network, 6001 (profile) | `load_balancer.{name,ip,dst_endpoint,endpoint_connections}`, `proxy_endpoint`, `proxy`, `proxy_http_request` | LB/proxy và backend thật phía sau | Cao; nếu thiếu thì `dst_endpoint` có thể là VIP chứ không phải server thật | [load_balancer.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/load_balancer.json), [network_proxy.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/profiles/network_proxy.json) |
| Thiết bị | 1010 Peripheral Activity / `device.peripheral_devices` | `vendor_name`, `model`, `vendor_id_list`, `serial_number` | Phần cứng gắn ngoài (USB) | Cao | [peripheral_device.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/peripheral_device.json) |
| Dịch vụ | 4001 Network Activity | `activity_id = 7 Listen`, `dst_endpoint.{ip,port}`, `connection_info.protocol_num` | Socket đang lắng nghe | Cao nhưng hiếm; chỉ có khi nguồn (EDR) phát sự kiện listen | [network_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network_activity.json) |
| Dịch vụ | 4001 | `initiator_id` (1.9.0; 1 Source, 2 Destination), `is_src_dst_assignment_known` (đã deprecated) | Xác định phía server | Cao nếu có; dữ liệu trước 1.9 chỉ có field boolean cũ hoặc không có gì | [network_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network_activity.json), [CHANGELOG](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md) |
| Dịch vụ | Network | `app_protocol_name` (1.8.0) | Giao thức L7 do DPI xác định (Zeek `service`, Suricata `app_proto`) | TB–cao; chỉ là giao thức, không có sản phẩm hay phiên bản | [network.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network.json), [Tenzir conn.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/logs/conn.tql) |
| Dịch vụ | 5001 / `device.network_interfaces[]` | `open_ports[].{port,protocol_name,protocol_num}` | Port mở do inventory/scanner báo | Cao cho port; không có tên sản phẩm (PR #1466 hứa "down the roads") | [port_info.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/port_info.json), [PR #1466](https://github.com/ocsf/ocsf-schema/pull/1466) |
| Dịch vụ | 5040 Live Evidence Info | `query_evidence.query_type_id = 7` + `connection_info` + `tcp_state_id = 10 LISTEN`; `query_type_id = 11` + `service.{name,version}` | Ảnh chụp socket LISTEN / service trên host | Cao (truy vấn trực tiếp OS); `service` là object mỏng, không có binary/port | [query_evidence.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/query_evidence.json), [dictionary.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/dictionary.json) |
| Dịch vụ | 201004 Windows Service Activity | `win_service.{name,service_file,service_dll_file,service_start_type_id,service_start_name,service_type_id,hosting_process}`, `prev_win_service` | Service Windows được cài/sửa/khởi động | Cao; chỉ có trên Windows | [windows_service_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/windows/events/windows_service_activity.json), [win_service.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/windows/objects/win_service.json) |
| Dịch vụ | Mọi class có `process` (Windows) | `process.hosted_services[]` | Service nào chạy trong `svchost` nào | Cao | [windows/objects/process.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/windows/objects/process.json) |
| Dịch vụ (Linux/macOS) | 1006 Scheduled Job, 5040 (Job/Startup Item) | `job.type_id = 3 Systemd / 4 Launchd`, `startup_item.{type_id=3 Service / 6 System Extension, run_state_id, start_type_id, process}` | Unit systemd/launchd, daemon tự khởi động | TB; không có object "unit" riêng, cgroup→unit chưa có field (PR #1725 đang mở) | [job.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/job.json), [startup_item.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/startup_item.json), [PR #1725](https://github.com/ocsf/ocsf-schema/pull/1725) |
| Dịch vụ | 4002 HTTP | `http_response.http_headers[name="Server"]`, `http_headers[name="X-Powered-By"]` | Banner sản phẩm/phiên bản web server | TB; không có field chuẩn, chỉ có nếu nguồn ghi header; nhiều nguồn không ghi | [http_response.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/http_response.json), [Tenzir http.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/logs/http.tql) |
| Dịch vụ | 4007 SSH | `server_hassh`, `protocol_ver`, `dst_endpoint.agent_list[].name` (cách Tenzir đặt chuỗi `OpenSSH_x`) | Phần mềm SSH server | TB; cách đặt chuỗi version vào `agent_list` là quy ước riêng của mapper, không phải ngữ nghĩa của schema | [ssh_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/ssh_activity.json), [Tenzir ssh.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/logs/ssh.tql) |
| Dịch vụ | Network (`tls`) | `tls.certificate.{subject,issuer,sans,is_self_signed,fingerprints}`, `tls.ja3s_hash`, `ja4_fingerprint_list[type_id=2 JA4Server / 5 JA4X509]`, `tls.sni` | Danh tính và stack TLS của server | TB; TLS 1.3 mã hoá certificate, nên log thụ động thường không có `certificate` | [tls.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/tls.json), [certificate.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/certificate.json) |
| Dịch vụ | 4005 RDP | `protocol_ver`, `certificate_chain`, `capabilities` | Có RDP server | TB | [rdp_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/rdp_activity.json) |
| Dịch vụ | 4006 SMB | `dialect`, `client_dialects`, `share`, `share_type_id` | File server SMB, phiên bản dialect | TB | [smb_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/smb_activity.json) |
| Dịch vụ | 4009 Email (extends base_event) | `banner`, `protocol_name`, `dst_endpoint` | Banner SMTP, MTA | TB; class không có `tls`/`ja4` | [email_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/email_activity.json) |
| Dịch vụ | 4008 FTP, 4013 NTP | FTP `command_responses`, `codes`; NTP `stratum_id`, `version` | FTP server, NTP server (stratum cho thấy máy chủ thời gian nội bộ) | TB | [ftp_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/ftp_activity.json), [ntp_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/ntp_activity.json) |
| Dịch vụ | 4003 DNS | `dst_endpoint` của các truy vấn, `answers[].{type,rdata}`, `query.{hostname,type}` | Resolver nội bộ; bản ghi SRV/MX cho biết vai trò service | TB | [dns_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/dns_activity.json) |
| Dịch vụ | 3002 Authentication | `service.{name,uid}`, `dst_endpoint`, `auth_protocol_id` | Service/gateway được đăng nhập vào (VPN, SSO app, Kerberos) | TB; ngữ nghĩa của `service` tuỳ nguồn | [authentication.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/iam/authentication.json) |
| Dịch vụ (cloud) | 6003 API Activity (profile cloud) | `api.service.name`, `api.operation`, `cloud.provider` | Dịch vụ cloud được gọi (ví dụ S3) | Cao cho cloud | [api.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/api.json) |
| Dịch vụ (cloud) | 4001 VPC Flow | `src/dst_endpoint.svc_name` | Đầu kia là dịch vụ AWS | Cao, nhưng chỉ đúng với AWS service | [network_endpoint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/network_endpoint.json), [AWS VPC mapping](https://github.com/ocsf/examples/blob/main/mappings/markdown/AWS/v1.5.0/VPC%20Flowlogs/README.md) |
| Dịch vụ (DB) | 6005 Datastore, 5023 | `database.{name,type_id,uid}`, `databucket`, `table`, `dst_endpoint` | Cơ sở dữ liệu, bucket | Cao (log của chính DB/cloud); `database.type_id` là kiểu mô hình dữ liệu, không phải sản phẩm (không có "PostgreSQL") | [datastore_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/application/datastore_activity.json), [database.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/database.json) |
| Ứng dụng (đã cài) | 5020 Software Inventory Info | `sbom.package.*`, `sbom.software_components[]`, `package.{name,version,vendor_name,purl,cpe_name,package_manager,type_id}` (đã deprecated), `product` | Phần mềm/gói đã cài | Cao; hai đường (deprecated và mới) cùng tồn tại | [software_info.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/software_info.json), [package.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/package.json), [sbom.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/sbom.json) |
| Ứng dụng (đã cài/OS) | 5004 Patch State | `kb_article_list[]`, `device.os` | Bản vá OS đã cài | Cao (Windows KB) | [patch_state.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/patch_state.json) |
| Ứng dụng (đã cài) | 2002 Vulnerability Finding | `vulnerabilities[].affected_packages[].{name,version,purl,cpe_name,path,fixed_in_version}`, `resources[]` | Gói bị scanner phát hiện có lỗ hổng | Cao, nhưng chỉ phủ phần mềm có CVE | [vulnerability.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/vulnerability.json), [affected_package.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/affected_package.json) |
| Ứng dụng (cài/gỡ/chạy) | 6002 Application Lifecycle | `activity_id` 1 Install … 8 Update; `application.{name,version,product}` (1.9.0); `app` (deprecated, kiểu `product`) | Vòng đời ứng dụng | Cao; dữ liệu cũ dùng `app` | [application_lifecycle.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/application/application_lifecycle.json) |
| Ứng dụng (đang chạy) | 1007 Process Activity | `process.file.{name,path,hashes,product,company_name,version,signatures}`, `process.cmd_line`, `process.loaded_modules` | Binary đang chạy, chữ ký số, metadata PE | Cao cho "đã chạy"; `file.product` là free string theo PE header | [process.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/process.json), [file.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/file.json) |
| Ứng dụng (đang chạy) | 1005 Module, 1002 Kernel Extension | `module.file`, `driver.file` | Thư viện/driver đã nạp | Cao | [module.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/module.json), [kernel_extension_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/system/kernel_extension_activity.json) |
| Ứng dụng (đã chạy, Windows) | 205019 Prefetch Query (deprecated; uid 19 trong extension Windows uid 2, category Discovery) / 5040 type 18 | `run_count`, `last_run_time`, `name` | Lịch sử thực thi | Cao | [prefetch_query.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/windows/events/prefetch_query.json) |
| Ứng dụng (tự khởi động) | 5040 (type 15), 5022 Startup Item Query (deprecated) | `startup_item.{name,type_id,process,driver,job,win_service}` | Persistence / autostart | Cao | [startup_item.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/startup_item.json) |
| Ứng dụng (dev/cloud) | 2007 Application Security Posture Finding | `application.{name,uid,type,version,url,hostname,sbom,product,resource_relationship}` | Ứng dụng nội bộ do ASPM/AppSec quản lý | Cao, nhưng chỉ ở ngữ cảnh DevSecOps | [application.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/application.json), [application_security_posture_finding.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/findings/application_security_posture_finding.json) |
| Ứng dụng (client gây ra hành động) | IAM 3xxx, 6xxx | `actor.application` (1.9.0); `actor.app_name`/`app_uid` (deprecated); `actor.process` | App/OAuth client đứng sau hành động | TB–cao; dữ liệu trước 1.9 dùng chuỗi `app_name` | [actor.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/actor.json) |
| Ứng dụng (qua mạng) | Network | `app_name` | Nhãn phân loại traffic DPI/App-ID/NBAR ("youtube, facebook, webex") | TB; tên là từ vựng riêng của từng vendor, không có catalog | [network.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network.json), [CHANGELOG](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md) |
| Ứng dụng (qua mạng) | Network, 4002, 6001 | `tls.sni`, `url.{hostname,domain}`, `url.category_ids`, `dst_endpoint.hostname` | Truy cập SaaS/website | TB; `category_ids` là hạng mục website, không phải định danh app | [url.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/url.json), [dictionary.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/dictionary.json) |
| Ứng dụng (qua mạng) | Network | `ja4_fingerprint_list[type_id=1 JA4 / 3 JA4HTTP / 6 JA4SSH]`, `tls.ja3_hash`, `src_endpoint.fingerprints[]` | Fingerprint của client app (trình duyệt, agent, malware) | TB; cần tra DB (ja4db.com); enum không có JA4D/JA4LS | [ja4_fingerprint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/ja4_fingerprint.json), [FoxIO ja4](https://github.com/FoxIO-LLC/ja4) |
| Ứng dụng (qua mạng) | 4003 DNS | `query.hostname` | Domain app gọi tới (telemetry, update, SaaS) | Thấp–TB; CDN dùng chung domain, DoH vượt qua resolver | [dns_query.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/dns_query.json) |
| Ứng dụng (TI) | 5021 OSINT Inventory, profile osint | `osint.{type_id=6 User Agent / 7 Digital Certificate, value, confidence_id}` | Tri thức ngoài về UA/cert | Bổ trợ cho enrichment | [osint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/osint.json) |
| Mọi mục tiêu | Mọi class | `unmapped`, `raw_data`, `enrichments[]`, `observables[]` | Field gốc không map được, log thô, dữ liệu enrich, chỉ mục pivot | `unmapped` không có schema, khác nhau theo từng mapper | [base_event.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/base_event.json), [dictionary.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/dictionary.json) |

### Phân loại các kiểu phân tán (có ví dụ nguồn)

1. **Một sự thật nằm ở nhiều class.** Ví dụ "host X chạy OpenSSH 8.9 trên 22/tcp" có thể có mặt ở:
   - `5020` (`sbom.package` hoặc `package` đã deprecated);
   - `1007` (`process.file.name = sshd`);
   - `5040` (`tcp_state_id = 10 LISTEN` + `service.name`);
   - `1006`/`startup_item` (`job.type_id = 3 Systemd`);
   - `4007` (`server_hassh` + `dst_endpoint.agent_list[].name = "OpenSSH_8.9…"` theo mapper Tenzir);
   - `4001` (`app_protocol_name = ssh`);
   - `2002` (`affected_packages`).

   Nguồn: các link trong bảng trên.
2. **Một host đóng nhiều vai trò theo đường dẫn.**
   - Log host: host nằm ở `device`.
   - Log mạng: host nằm ở `src_endpoint`/`dst_endpoint`. Ở 1.9.0, mô tả của `src_endpoint` nói rõ "In bi-flow or asymmetric flow scenarios, this endpoint may represent the response side… Use `initiator_id`".
   - Thiết bị quan sát: `observation_point_id` và `network_observation_point`.
   - Thiết bị trung gian: `proxy`, `proxy_endpoint`, `load_balancer.dst_endpoint`, `intermediate_ips`.
   - Thiết bị ghi log: `metadata.reporter`, `metadata.loggers[].device`.
   - Thiết bị bị tác động: `resources[]` (`resource_details.hostname`/`ip`/`device`) trong finding.

   VPC Flow thậm chí đổi chỗ đặt `instance_id` theo `flow_direction`. Nguồn: [network_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network_activity.json), [resource_details.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/resource_details.json), [AWS VPC mapping](https://github.com/ocsf/examples/blob/main/mappings/markdown/AWS/v1.5.0/VPC%20Flowlogs/README.md)
3. **Định danh lệch nhau.**
   - Thiết bị có nhiều định danh: `device.uid` ("Windows TargetSID or AWS EC2 ARN"), `uid_alt` (AD DN), `instance_uid`, `hw_info.uuid` (SMBIOS), `os_machine_uuid`, `hw_info.serial_number`, `udid`, `agent_list[].uid` (aid), `mac`, `hostname` (FQDN) so với `name` (short name).
   - Phần mềm có nhiều định danh: `package.purl`, `package.cpe_name`, `product.cpe_name`, `os.cpe_name`, `product.uid`, `file.hashes`, `application.uid`/`uid_alt`.
   - `endpoint.owner` có hai nghĩa (issue #1752).

   Nguồn: [device.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/device.json), [issue #1752](https://github.com/ocsf/ocsf-schema/issues/1752)
4. **Chữ "service" và "app" mang nhiều nghĩa.**
   - `service` object: dịch vụ cloud (mô tả gốc "e.g. AWS EC2"), service/gateway xác thực (`3002.service`), service OS (`query_evidence.service`), dịch vụ cloud được gọi API (`api.service`).
   - `svc_name` có hai nghĩa: dịch vụ AWS trong flow (`network_endpoint.svc_name`) và service Windows làm object server (`win_resource.svc_name`).
   - `win_service` là service Windows đầy đủ.
   - `user.type_id` có giá trị Service (tài khoản service, thêm ở 1.6.0).
   - Mapper còn đặt phần mềm SSH vào `agent_list` với `type_id` 9 Remote Access.
   - Về phía app: `app_name` (DPI) khác `actor.application` khác `application` (ASPM) khác `product` khác `metadata.product` (sản phẩm ghi log) khác `file.product`.

   Nguồn: [service.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/service.json), [win_resource.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/windows/objects/win_resource.json), [PR #1702](https://github.com/ocsf/ocsf-schema/pull/1702), [Tenzir ssh.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/logs/ssh.tql)
5. **Field deprecated và field mới cùng tồn tại.** Dữ liệu nhiều phiên bản trong một kho phải đọc cả hai đường:

   | Field cũ | Field mới | Deprecated từ |
   |---|---|---|
   | `5020.package` | `sbom` | 1.4.0 |
   | `tls.sans` | `tls.certificate.sans` | 1.4.0 |
   | `container.tag`, `image.tag` | `labels`/`tags` | 1.4.0 |
   | `device.imei` | `imei_list` | 1.4.0 |
   | `file.signature` | `signatures` | 1.8.0 |
   | 17 class query | `5040` | 1.5.0 |
   | `is_src_dst_assignment_known` | `initiator_id` | 1.9.0 |
   | `6002.app` | `application` | 1.9.0 |
   | `actor.app_name`/`app_uid` | `actor.application` | 1.9.0 |
   | `job.cmd_line`/`last_run_time`/`next_run_time` | `job_actions`/`job_triggers` | 1.9.0 |
   | `hw_info.cpu_*` | `cpu_info_list[*]` | 1.9.0 |
   | `dns_query.opcode`, `dns_answer.flags` | field trên `dns_activity` | 1.9.0 |

   Từ 1.9.0, `@deprecated` có thêm `superseded_by` dạng máy đọc được (#1707), dùng được để tự động hoá việc đọc cả hai đường. Nguồn: [CHANGELOG](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md)
6. **Enum và chuỗi tự do lẫn lộn.**
   - Có enum: `device.type_id`, `os.type_id`, `agent.type_id`, `job.type_id`, `startup_item.type_id`, `ja4_fingerprint.type_id`, `fingerprint.algorithm_id`, `database.type_id`, `package.type_id`, `url.category_ids`, `observation_point_id`, `initiator_id`.
   - Chuỗi tự do: `app_name`, `app_protocol_name` (chỉ khuyến nghị tên IANA), `application.type`, `product.name`/`vendor_name`, `file.company_name`, `user_agent`, `banner`, `http_headers[].value`, `service.name`, `container.runtime`, `orchestrator`, `device.hypervisor`.
   - Enum `ja4_fingerprint` thiếu các loại JA4+ mới hơn, nên các loại này phải dùng `99 Other` kèm `type`.

   Nguồn: các link trong bảng trên.
7. **Thông tin không có chỗ trong schema nên rơi vào `unmapped`** (chính sách chung của mapper Tenzir và AWS là "mọi field không map → `unmapped`"):
   - DHCP option (vendor class, parameter list);
   - Zeek `software.log`, `known_services.log`, `known_hosts.log`;
   - cgroup/systemd unit của process (PR #1725 nói rõ);
   - chi tiết giao thức chưa có class (issue #1384);
   - các field VPC Flow không có trong bảng map.

   Nguồn: [Tenzir map.tql](https://github.com/tenzir/library/blob/932bfb21f493312fa985e53517660799ddd781b5/zeek/operators/ocsf/map.tql), [PR #1725](https://github.com/ocsf/ocsf-schema/pull/1725), [issue #1384](https://github.com/ocsf/ocsf-schema/issues/1384), [AWS VPC mapping](https://github.com/ocsf/examples/blob/main/mappings/markdown/AWS/v1.5.0/VPC%20Flowlogs/README.md)
8. **Thông tin chỉ có trong mảng header hoặc mảng key-value.**
   - Header `Server` và `X-Powered-By` chỉ nằm trong `http_response.http_headers[]`. AWS WAF chỉ tách riêng `User-Agent`, `Host`, `XFF`, `Referer`, còn lại để trong `http_headers[]`.
   - `labels`/`tags` trên `container`/`image`/`service`/`application` chứa phiên bản image, tên app…

   Nguồn: [AWS WAF mapping](https://github.com/ocsf/examples/blob/main/mappings/markdown/AWS/v1.1.0/WAF/README.md), [http_response.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/http_response.json)

### Nhận định

- **Nhận định:** Bước extract nên có lớp "path alias" theo phiên bản. Mỗi khái niệm (ví dụ `software.name`) ánh xạ tới danh sách đường dẫn theo thứ tự ưu tiên: `sbom.package.name` → `package.name` → `application.name` → `app.name`. Có thể sinh danh sách này tự động từ `superseded_by` của schema 1.9.0.
- **Nhận định:** Ở 1.9.0, OCSF không có đơn vị "service instance" (host, port, proto, product, version). Bảng `asset_service` phải tự tổng hợp từ ít nhất 6 nguồn: Listen/initiator, `open_ports`, `5040` LISTEN, `win_service`/`startup_item`/`job`, banner/header/HASSH/cert, `app_protocol_name`. Chỉ `app_protocol_name` và `open_ports` là có chuẩn hoá, nhưng cả hai đều không có sản phẩm.
- **Nhận định:** Kho dữ liệu cần một chiến lược cho `unmapped` theo từng `metadata.product`, ví dụ registry các key quen thuộc như `unmapped.vendor_class` của DHCP hay `unmapped.software_type` của Zeek. Dữ liệu chủ chốt cho fingerprint thiết bị (DHCP, software.log) nằm ngoài schema.
- **Nhận định:** `observables[]` không giúp gom phần mềm, vì không có type cho product, CPE hay purl. Chỉ nên dùng nó để pivot theo IP/hostname/MAC/process/hash/user-agent/fingerprint.
- **Nhận định:** Việc mapper Tenzir đặt chuỗi phiên bản SSH vào `agent_list` (vốn mô tả agent/sensor đã cài) cho thấy chỉ đọc theo ngữ nghĩa schema là không đủ. Cần quy tắc riêng cho từng mapper, theo cặp `metadata.product` + `metadata.version`/tên mapper.
- **Nhận định:** `ja4_fingerprint_list` và `tls.ja3_hash`/`ja3s_hash` nằm ở cấp event, không gắn với endpoint. Phải suy ra fingerprint thuộc client hay server qua `type_id` (JA4 là client, JA4Server là server, JA4TCP là client, JA4TCPServer là server) kết hợp `initiator_id`. Riêng `network_endpoint.fingerprints` (1.8.0) gắn trực tiếp với endpoint, nhưng hiện mới thấy dùng cho NPF/HASSH.

### Khoảng trống

- Chưa đọc được nội dung thảo luận của PR #1702 và issue #1695 (API `gh` cho repo này bị chặn; chỉ đọc được qua search). Mới dựa vào CHANGELOG.
- Chưa kiểm tra mapper OCSF của các vendor lớn: CrowdStrike, Palo Alto (App-ID nằm ở `app_name` hay `unmapped`?), Microsoft Sentinel ASIM→OCSF, Splunk, Cribl, và các nguồn native khác của Amazon Security Lake ngoài VPC Flow/Route 53/WAF. Vì vậy chưa có bằng chứng về nơi các vendor này đặt App-ID, UA đã parse hay DHCP vendor class.
- Chưa xác minh Zeek `dhcp.log` có những field nào ngoài các field được map (ví dụ có `client_software` hay không), nên chưa thể liệt kê chính xác key nào rơi vào `unmapped`.
- Search issue ocsf-schema với các từ khoá "listening port", "banner", "software fingerprint", "user agent" không ra đề xuất nào cho service inventory hay UA parsing. Có thể đề xuất nằm trong Discussions/Slack (chưa tìm). Truy vấn đã thử: liệt kê dưới đây.
- Chưa kiểm tra Suricata `dhcp.tql` đầy đủ (mới thấy map `dhcp.hostname` → `src_endpoint.hostname`).

## Truy vấn đã chạy

- Đọc schema local: `extensions/{linux,macos,windows}`, `profiles/*`, khoảng 45 object, khoảng 30 class, `dictionary.json` (observable, enum), `CHANGELOG.md` (grep JA4, NPF, initiator, deprecated…)
- `gh api search/issues` repo:ocsf/ocsf-schema, mỗi từ khoá tìm cả is:issue và is:pull-request: "service inventory", "listening port", "user agent", "dhcp", "software fingerprint", "JA4", "systemd", "app_name", "launchd", "banner", "installed software", "NPF fingerprint"; thêm "application fingerprint support", "control_group", "Profiles for Network Activity", "open_ports", "endpoint.owner conflates"
- `gh api search/code`: repo:ocsf/examples "vpc flow", "route53", "WAF README"; repo:tenzir/library "zeek ocsf"
- WebSearch: "Tenzir Zeek OCSF mapping unmapped" (standard), "Amazon Security Lake VPC flow logs OCSF mapping unmapped fields" (standard), "Suricata eve.json OCSF mapping" (standard)
- WebFetch: github.com/FoxIO-LLC/ja4 (bảng JA4+)
- Clone sparse `tenzir/library` (zeek, suricata) @932bfb2; curl raw `ocsf/examples` AWS VPC Flowlogs v1.5.0, Route53 v1.5.0, WAF v1.1.0
