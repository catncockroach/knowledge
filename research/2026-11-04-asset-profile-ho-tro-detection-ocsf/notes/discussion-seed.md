# Seed từ thảo luận 2026-11-04 (cần kiểm chứng và mở rộng)

Các tên class/object/field dưới đây đã được coordinator đối chiếu với bản clone `ocsf-schema` tag `1.9.0` (commit 856d462). Mỗi dòng dẫn tới file schema gốc. Phần "Nhận định" là suy luận, chưa có nguồn ngoài.

## Bằng chứng về thiết bị

- `5001` Device Inventory Info mang object `device`; `device` có `type_id`, `os`, `hw_info`, `vendor_name`, `model`, `is_managed`, `network_interfaces`, `first_seen_time`, `last_seen_time`, `risk_level_id` — [device.json @1.9.0](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/device.json) (bậc 1, 2026-08)
- `endpoint` (lớp cha của `device` và `network_endpoint`) có `agent_list`, `hostname`, `ip`, `mac`, `mac_vendor`, `os`, `hw_info`, `type_id`. Enum `type_id`: 1 Server, 2 Desktop, 3 Laptop, 4 Tablet, 5 Mobile, 6 Virtual, 7 IOT, 8 Browser, 9 Firewall, 10 Switch, 11 Hub, 12 Router, 13 IDS, 14 IPS, 15 Load Balancer — [endpoint.json @1.9.0](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/endpoint.json) (bậc 1)
- Enum `agent.type_id`: 1 EDR, 2 DLP, 3 Backup & Recovery, 4 Performance Monitoring & Observability, 5 Vulnerability Management, 6 Log Forwarding, 7 MDM, 8 Configuration Management, 9 Remote Access — [agent.json @1.9.0](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/agent.json) (bậc 1)
- `4004` DHCP Activity có `src_endpoint`, `dst_endpoint`, `lease_dur`, `is_renewal`, `relay`, nhưng không có field chuẩn nào cho DHCP option 55/60 (fingerprint, vendor class) — [dhcp_activity.json @1.9.0](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/dhcp_activity.json) (bậc 1)
- Base `Network` event có `app_name`, `app_protocol_name`, `connection_info`, `ja4_fingerprint_list`, `network_observation_point`, `observation_point_id`, `proxy`, `tls`, `traffic` — [network.json @1.9.0](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network.json) (bậc 1)
- `tls` có `sni`, `ja3_hash`, `ja3s_hash`, `certificate`, `certificate_chain`, `sans`, `version`, `cipher` — [tls.json @1.9.0](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/tls.json) (bậc 1)
- `http_request` có `user_agent`, `url`, `http_headers`, `x_forwarded_for`; `http_response` có `http_headers`, `content_type`, `code` — [http_request.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/http_request.json), [http_response.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/http_response.json) (bậc 1)
- `4007` SSH Activity có `client_hassh`, `server_hassh`, `protocol_ver` — [ssh_activity.json @1.9.0](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/ssh_activity.json) (bậc 1)

## Bằng chứng về dịch vụ (phía server)

- `4001` Network Activity: `activity_id` 7 = Listen; `initiator_id` (mới ở 1.9.0) thay `is_src_dst_assignment_known` (deprecated) — [network_activity.json @1.9.0](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network_activity.json), [CHANGELOG 1.9.0](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md) (bậc 1)
- `app_name` của Network: "network application name identified by tools such as NBAR or App ID (e.g., youtube, facebook, webex)"; `app_protocol_name`: giao thức L7 theo tên IANA, thêm ở 1.8.0, kèm ghi chú "Port numbers alone are not always a reliable indicator of the actual application protocol in use" — [network.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network.json), [CHANGELOG](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md) (bậc 1)
- `network_interface.open_ports` (mảng `port_info`: `port`, `protocol_name`, `protocol_num`), thêm ở 1.6.0 — [network_interface.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/network_interface.json) (bậc 1)
- `network_endpoint.svc_name`: tên service trong kết nối service-to-service (ví dụ trường pkt-src-aws-service của AWS VPC) — [network_endpoint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/network_endpoint.json) (bậc 1)
- `5040` Live Evidence Info: `query_evidence.query_type_id` 7 Network Connection (kèm `tcp_state_id`), 11 Service, 15 Startup Item. Thay cho các class query đã deprecated như 5016 Service Query và 5012 Network Connection Query — [query_evidence.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/query_evidence.json), [evidence_info.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/evidence_info.json) (bậc 1)
- Extension Windows (uid 2): Windows Service Activity (category System, uid 4, tức 201004) mang object `win_service` (`name`, `service_file`, `service_dll_file`, `service_start_type_id`, `service_start_name`, `service_type_id`, `hosting_process`, `cmd_line`) — [windows_service_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/windows/events/windows_service_activity.json), [win_service.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/extensions/windows/objects/win_service.json) (bậc 1)
- `6002` Application Lifecycle: activity 1 Install, 2 Remove, 3 Start, 4 Stop, 5 Restart, 6 Enable, 7 Disable, 8 Update. Field `application` thay `app` (deprecated ở 1.9.0) — [application_lifecycle.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/application/application_lifecycle.json) (bậc 1)
- Lộ chi tiết service theo từng giao thức:
  - `4005` RDP: `protocol_ver`, `certificate_chain`
  - `4006` SMB: `dialect`, `share`
  - `4009` Email: `banner`
  - `4013` NTP: `stratum`
  - `4014` Tunnel
  - `3002` Authentication: `service` ("The service or gateway to which the user or process is being authenticated")
  - `6005` Datastore: `database`
  - `6003` API Activity: `api.service`

  Nguồn: các file trong [events/ @1.9.0](https://github.com/ocsf/ocsf-schema/tree/1.9.0/events) (bậc 1)
- Object `service` rất mỏng (`name`, `uid`, `version`, `labels`, `tags`) và mô tả theo kiểu dịch vụ cloud ("e.g. AWS EC2"). Nó vẫn được dùng ở `3002.service`, `api.service` và `query_evidence.service` với nghĩa khác nhau — [service.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/service.json) (bậc 1)

## Bằng chứng về ứng dụng

- `5020` Software Inventory Info mang `package` (`name`, `version`, `vendor_name`, `purl`, `cpe_name`, `package_manager`, `type_id`), `product` và `sbom` (`software_components`) — [software_info.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/discovery/software_info.json), [package.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/package.json) (bậc 1)
- `1007` Process Activity: `process.file` có `name`, `path`, `hashes`, `product`, `company_name`, `version`, `signature`/`signatures` — [file.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/file.json) (bậc 1)
- `actor.application` (1.9.0) thay `actor.app_name`/`app_uid` (deprecated). `app_name` trên Network vẫn giữ nghĩa phân loại traffic kiểu DPI/NBAR. Object `application` được thêm `product` ở 1.9.0 — [CHANGELOG 1.9.0](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md), [actor.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/actor.json) (bậc 1)
- `vulnerability.affected_packages` (kiểu `affected_package`, mở rộng `package`) trong `2002` — [vulnerability.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/vulnerability.json) (bậc 1)
- Nhóm class Application Activity: 6001 Web Resources Activity, 6002 Application Lifecycle, 6003 API Activity, 6005 Datastore Activity, 6006 File Hosting Activity, 6007 Scan Activity, 6008 Application Error; 6004 Web Resource Access Activity đã deprecated — [events/application @1.9.0](https://github.com/ocsf/ocsf-schema/tree/1.9.0/events/application) (bậc 1)

## Nhận định (từ thảo luận, cần nguồn)

- Một sự thật bị rải ra năm mảnh. Ví dụ "máy X chạy nginx trên 443" có thể đến từ:
  - `5020` package;
  - `1007` `process.file.name`;
  - `4001` Listen, hoặc nhiều initiator tới X:443;
  - header `Server` trong `4002` `http_response.http_headers`;
  - `2002` `affected_packages`.
- Trên log host, asset là `device`; trên log mạng, là `src_endpoint`/`dst_endpoint`; trên log của chính thiết bị mạng, là `observation_point`. Một service là bộ (asset, port, proto) suy ra từ nhiều flow. Khi thiếu `initiator_id` thì phải dùng heuristic (port, số peer).
- Tên ứng dụng không đồng nhất giữa process, App-ID, CPE và purl, nên cần một catalog sản phẩm.
- Nhiều thông tin nằm trong `unmapped`: DHCP option 60, header `Server`, application ID của NetFlow.
- Đề xuất ba bảng suy diễn có evidence và confidence: `asset_service`, `asset_software`, `asset_app_usage`. Thang tin cậy: khai báo > runtime trên host > mạng thụ động có banner hoặc fingerprint > chỉ có port.
