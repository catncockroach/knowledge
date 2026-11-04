# Ghép bằng chứng thành quan hệ asset → service / software / app usage

Phạm vi: câu hỏi phụ 4 của brief. Không lặp lại mô hình entity, provenance theo trường và ưu tiên nguồn (Tenable Information Order, Axonius Preferred, ngưỡng Active/Not Seen/Lost của Cortex) đã có ở `research/2026-11-03-asset-profile-vendor-giao-dien-soc/report.md`, cũng không lặp lại các bảng asset ở `research/2026-11-01-asset-inventory-profile-ocsf-1-9/report.md`. Tên field OCSF lấy từ `notes/discussion-seed.md` (đã đối chiếu tag 1.9.0).

## 4a. Thuật toán và heuristic suy ra server/service từ flow và connection log

### Kết luận ngắn
Quy tắc nền mà cả học thuật lẫn công cụ đều dùng: **một service = (IP, port, transport) mà phía responder đã trả lời**. Với TCP, bằng chứng là SYN-ACK hoặc handshake hoàn tất. Với UDP, bằng chứng là responder gửi lại gói. Khi không biết hướng flow (NetFlow/IPFIX), chỉ còn heuristic theo port và số peer, và heuristic này sai khi service chạy port lạ. Passive bắt được rất nhanh các server đông khách (99% server tính theo trọng số client trong 14 phút), nhưng bỏ sót nhiều server ít dùng hoặc đứng yên (sau 12 giờ chỉ đạt 19% tổng số server). Mức chắc chắn **cao** cho quy tắc và số liệu Bartlett 2007 (đọc trực tiếp paper và source Zeek). Mức chắc chắn **thấp** cho cách các NDR thương mại gán role, vì tài liệu không công bố thuật toán hay độ chính xác.

### Phát hiện có nguồn
- **Bartlett, Heidemann, Papadopoulos (IMC 2007)** định nghĩa bằng chứng thụ động như sau: "even just the presence of a positive response to a connection request (SYN-ACK) is sufficient evidence of a TCP service". Với UDP, "the concept of 'server' and 'client' is not clear without application protocol information". Traffic hai chiều chứng tỏ có service, còn traffic một chiều "may also indicate unsolicited probe traffic". Trong thực nghiệm, họ coi "any host sending a SYN-ACK is running a service" và coi host "sends UDP traffic from a well known server port" là đang chạy UDP service. Passive "can not identify services that do not run on well-known ports or are indirected without protocol-specific decoders" — [Understanding Passive and Active Service Discovery](https://ant.isi.edu/~johnh/PAPERS/Bartlett07d.pdf) (bậc 1, IMC 2007-10)
- Bối cảnh dữ liệu: 38 subnet của một trường đại học, 16.130 địa chỉ, khoảng 6.450 host sống. Bộ dữ liệu chính dài 18 ngày, có quét chủ động mỗi 12 giờ. Không có ground truth thật, nên tác giả "define ground truth as the union of servers found by passive and active methods" — [Bartlett 2007](https://ant.isi.edu/~johnh/PAPERS/Bartlett07d.pdf) (bậc 1, 2007)
- Số liệu Bảng 2 của Bartlett 2007 (đã cộng kiểm tra từng cột):
  - 12 giờ passive, 1 lần scan: union 1.748 server. Active tìm thấy 1.707 (98%), passive 327 (19%). Chỉ passive thấy 41 server (2,3%). 81% server là idle.
  - 25 giờ, 2 lần scan: union 1.848. Active 92%, passive 61%, chỉ passive thấy 3,1%.
  - 9 ngày, 17 lần scan: union 2.551. Active 95%, passive 73%, chỉ passive thấy 5,0%.
  - 18 ngày, 35 lần scan: union 2.960. Cả hai cùng thấy 1.925 (65%), chỉ active thấy 848 (29%), chỉ passive thấy 186 (6,3%). Tổng active 2.773 (94%), tổng passive 2.111 (71%).
  
  Nguồn: [Bartlett 2007](https://ant.isi.edu/~johnh/PAPERS/Bartlett07d.pdf) (bậc 1, 2007). Security Boulevard viết "active 29%, passive 6.3%, combined 65%", tức là hiểu nhầm các cột "chỉ active", "chỉ passive" và "cả hai" của bảng này. Theo paper gốc, passive đạt 71% và active đạt 94% — [Security Boulevard](https://securityboulevard.com/2025/06/active-scanning-vs-passive-scanning-key-differences/) (bậc 3, 2025-06)
- Theo Bartlett 2007, khi tính theo trọng số độ phổ biến, passive "finds 99% of the client-weighted servers in 14 minutes, and 99% of the flow-weighted servers in 5 minutes", nhanh hơn một lượt scan ("well over an hour"). Sau 18 ngày, passive bắt được 92,5% (1.587/1.714) số server mà một lượt active tìm ra. Với server idle, passive dài hạn tìm được 72–91%, và "external, possibly malicious scans" giúp ích nhiều cho việc này. Service trên địa chỉ VPN/PPP (transient) "almost never discovered passively". Passive "never levels off": trong 5 ngày cuối vẫn thấy server mới với tốc độ khoảng một server mỗi giờ, do host transient đổi IP — [Bartlett 2007](https://ant.isi.edu/~johnh/PAPERS/Bartlett07d.pdf) (bậc 1, 2007)
- **Zeek `known-services.zeek`** định nghĩa active service là "an IP address and port of a server for which a TCP handshake (SYN+ACK) is observed, assumed to have been done in the past (started seeing packets mid-connection, but the server is actively sending data), or sent at least one UDP packet". Hàm `has_active_service()` xử lý theo transport:
  - TCP: nhận khi `resp$state` là ESTABLISHED, CLOSED hoặc PARTIAL, hoặc khi history có cờ `h` (SYN-ACK).
  - UDP: mặc định đòi `UDP_ACTIVE` (option `service_udp_requires_response = T`).
  - ICMP và transport khác: không tính là service.

  Script còn loại phiên `ftp-data`, và với DNS thì đòi server có trả lời (`resp$size > 0`). Option `service_tracking = LOCAL_HOSTS` nghĩa là mặc định chỉ theo dõi host nội bộ. Log gồm `ts, host, port_num, port_proto, service` (`service` là "set of protocols that match the service's connection payloads"). Service không xác định được tên vẫn được log. Bảng chống trùng `Known::services` có `&create_expire=1day`, persistence cũng mặc định hết hạn sau `1day`. Vì vậy mỗi (host, port, service) **được log lại mỗi ngày**: đây là cơ chế "heartbeat" ngầm, dùng được để dựng last_seen — [known-services.zeek source](https://raw.githubusercontent.com/zeek/zeek/master/scripts/policy/protocols/conn/known-services.zeek) (bậc 1, master, truy cập 2026-11-04); [Zeek docs known-services](https://docs.zeek.org/en/current/scripts/policy/protocols/conn/known-services.zeek.html) (bậc 1)
- **Đảo hướng flow (ntop)**: nếu bắt đầu quan sát giữa chừng một kết nối, gói đầu tiên có thể đến từ server, tạo ra "swapped flow". ntopng/nProbe nhận diện flow bị đảo theo các dấu hiệu sau:
  - DNS, NTP, ICMP echo: gói đầu tiên là response.
  - RDP: client port là 3389.
  - TCP: SYN đến sau SYN|ACK.
  - TCP: client port < server port với các service quen như HTTP, HTTPS, SSH, Telnet. Chính ntop thừa nhận dấu hiệu này "not necessarily true, but it is true for known services".

  Với interface flow (NetFlow/IPFIX), "only port-based heuristics can be used". Tính năng đảo hướng bật mặc định, và nên tắt khi làm forensic vì attacker có thể dùng port lạ — [Flow Direction Swapping Explained](https://www.ntop.org/flow-direction-swapping-explained/) (bậc 1 cho hành vi của sản phẩm, 2025-10-17)
- Bài TMA 2025 về "orphan flows" định hướng NetFlow bằng cặp port: phía có ephemeral port là client, phía có well-known/registered port là server. Flow có tổ hợp port bất thường thì bị loại để giữ độ chính xác (theo snippet tìm kiếm, chưa mở paper) — [Understanding Orphan Flows](https://zanema.com/papers/tma25_orphan_flows.pdf) (bậc 1, 2025; chưa đọc toàn văn)
- **Tan, Poletto, Guttag, Kaashoek (USENIX ATC 2003)** gom host thành "role" theo mẫu kết nối, dùng một thuật toán grouping và một thuật toán correlation để khớp các nhóm qua nhiều lần chạy. Thuật toán đã được đưa vào một sản phẩm thương mại (Mazu). Trên hai mạng doanh nghiệp với 110 và 3.638 host, số nhóm nhỏ hơn số host hai bậc độ lớn, và thời gian chạy tăng theo bình phương số host (theo abstract và snippet, chưa đọc toàn văn; paper không công bố precision/recall so với ground truth) — [Role Classification of Hosts within Enterprise Networks Based on Connection Patterns](https://usenix.org/legacy/event/usenix03/tech/full_papers/tan/tan.pdf) (bậc 1, 2003)
- **ExtraHop** "automatically discovers and classifies devices ... based on the protocol activity or device model and assigns a role", ví dụ gateway, file server, database, load balancer. Khi hoạt động không chỉ rõ một role thì gán "Other". Người dùng ghi đè được role, và tuỳ chọn "Auto" khôi phục role do hệ thống tính (hiển thị trong ngoặc). Thay đổi role không đồng bộ giữa sensor và console. Tài liệu không công bố tiêu chí cụ thể (theo snippet docs; trang trả 403 khi fetch) — [ExtraHop: Change a device role 9.8](https://docs.extrahop.com/9.8/change-device-role) (bậc 1, chưa mở được)
- **Stamus (Suricata NDR) Host Insights**: "Role is based on the services that the host has been observed to provide", kèm protocol và port thấy dùng. Một host có thể mang nhiều role, ví dụ Domain Controller, DHCP Server, HTTP Proxy, Printer. "Each metadata value is tracked with a first seen and last seen timestamps", ví dụ HTTP User-Agent, TLS agent, user login — [Stamus Host Insights 39.0.0](https://docs.stamus-networks.com/39.0.0/concepts/host-insights.html) (bậc 1, phiên bản 39.0.0; bản hiện hành 42.2.0)
- **Vectra**: theo release note 6.3 (2020-12), host được thấy hoạt động như DC, DNS, DHCP, web, print, proxy, file hoặc database server sẽ được gắn role tương ứng. "Observed privilege" tính từ lịch sử tương tác giữa các entity, không lấy từ quyền khai báo trong directory (theo snippet tìm kiếm, chưa mở PDF) — [Vectra 6.3 Release Notes](https://2700995531-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2Fpn0NCs7YgGCODlBZmgu3%2Fuploads%2Fgit-blob-06d98323c1229fff41317138f36c0b6573e983ca%2F2020DEC_Vectra_6.3_Release_Notes.pdf?alt=media) (bậc 1, 2020-12, chưa mở); [Vectra PTA blog](https://vectra.ai/blog/paa) (bậc 2)
- **Corelight Entity Collection** gồm các log known hosts, devices, services, names, domains, certs, users, remotes. Log tóm tắt hoạt động theo cửa sổ **15 phút** và mặc định chỉ chạy trên mạng nội bộ. Log `remotes` tắt mặc định "due to its high volume". Loại thiết bị lấy từ MAC trong DHCP, RADIUS... Collection phân loại "80+ types of applications" bằng DNS query, SNI của certificate và protocol metadata, ghi vào một field mới của conn log. Ra mắt ở v26, cập nhật ở v27 — [Corelight launches the Entity Collection](https://corelight.com/blog/corelight-launches-the-entity-collection) (bậc 1, 2022-12-13, cập nhật 2026-04-03)

### Nhận định
- Ánh xạ sang OCSF 1.9.0, chia thành ba tầng bằng chứng cho `asset_service(asset, port, proto)`:
  1. **Khai báo hoặc runtime trên host**: `4001` có `activity_id = 7` (Listen) với `device`/`src_endpoint` là asset, `5040` có `query_evidence.query_type_id = 7` (Network Connection, `tcp_state_id` LISTEN), `network_interface.open_ports`.
  2. **Mạng có xác nhận phía responder**: `4001`/`4002`/`4003`... có `initiator_id` cho biết bên nào khởi tạo, bên kia là server tại `dst_endpoint.port`. Tầng này tương đương quy tắc SYN-ACK/handshake của Zeek: nên chỉ nhận khi `traffic.bytes_in > 0` hoặc `connection_info` cho thấy handshake hoàn tất. `app_protocol_name` (L7 do DPI xác nhận) nâng độ tin cậy hơn hẳn so với chỉ có port.
  3. **Chỉ có flow không rõ hướng**: suy hướng theo ephemeral port so với well-known port, kèm fan-in (số `src_endpoint.ip` khác nhau tới cùng (ip, port)). Chỉ chấm điểm thấp.
- Zeek, khi được map sang OCSF, thường cho `known_services` ra `5040`/`5001` hoặc `unmapped`. Cần giữ `service` (set protocol) dưới dạng `app_protocol_name`. Vì Zeek log lại mỗi ngày, mỗi bản ghi nên được coi là một lần quan sát (tăng `last_seen`), không phải một service mới.
- Vì passive "never levels off" và hay sót server idle, `asset_service` không nên có trạng thái "đóng" chỉ vì không còn thấy traffic. Nên dùng trạng thái `observed`/`not_recently_observed` với ngưỡng riêng theo loại bằng chứng (Listen trên host thì ngắn, flow thì dài).
- Role kiểu ExtraHop, Vectra, Stamus là **tầng suy diễn thứ hai** dựng trên `asset_service`: DC ⇐ có 88/389/445 phục vụ nhiều client, DHCP server ⇐ phía server của `4004`, DNS server ⇐ phía server của `4003`. Nên lưu role thành bảng riêng, có liên kết về các service làm bằng chứng, và cho analyst ghi đè theo kiểu "Auto (giá trị hệ thống)" của ExtraHop.

### Khoảng trống
- Chưa có nghiên cứu học thuật mới (2018–2026) công bố precision/recall của việc suy service hoặc role từ flow so với ground truth CMDB. Các truy vấn "host role inference flow data ... precision recall" chỉ trả về patent. Webster và cộng sự (MIT LL, active vs passive mapping) và Hofstede và cộng sự chưa kịp tìm.
- Tiêu chí gán role cụ thể của ExtraHop (docs trả 403), Darktrace và Vectra chưa được đọc trực tiếp.
- Microsoft Defender: chỉ thấy query cộng đồng dùng `DeviceNetworkEvents` với `ActionType == "ListeningConnectionCreated"` và `LocalPort` ([kqlsearch](https://kqlsearch.com/query/Network%20-%20DevicesWithMostOpenPorts&clmnzgk5q001o5iskll19bz6e), bậc 3). Chưa mở được trang schema chính thức hay trang exposure graph về "open ports".

## 4b. Cách vendor lưu evidence, confidence, first/last seen cho quan hệ asset → software/service, và xử lý xung đột

### Kết luận ngắn
Mẫu chung của các vendor: **mỗi quan hệ asset → software/service mang theo bằng chứng có thể kiểm tra** (đường dẫn registry/đĩa, phương thức phát hiện), **first_seen/last_seen theo từng quan hệ** (không chỉ theo asset), và **tên "preferred" lấy từ catalog**. Không vendor nào trong mẫu công bố điểm confidence số cho một quan hệ software/service. Xung đột được xử lý bằng catalog và tên preferred, chứ không bằng biểu quyết. Mức chắc chắn **trung bình**: tài liệu chính thức có mô tả field, nhưng không mô tả thuật toán.

### Phát hiện có nguồn
- **Microsoft Defender Vulnerability Management**: bảng `DeviceTvmSoftwareEvidenceBeta` cho phép "view evidence of where a specific software was detected on a device". Các cột: `DeviceId`, `SoftwareVendor`, `SoftwareName`, `SoftwareVersion`, `RegistryPaths` ("Registry paths where evidence indicating the existence of the software ... was detected"), `DiskPaths` ("file-level evidence"), `LastSeenTime`. Bảng vẫn đang beta, tên sẽ đổi, và "isn't ingested into Microsoft Sentinel" — [DeviceTvmSoftwareEvidenceBeta](https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicetvmsoftwareevidencebeta-table) (bậc 1, 2026-06-14)
- API xuất software inventory theo device có `SoftwareFirstSeenTimestamp` (lần đầu software được thấy trên device) cùng hai mảng `RegistryPaths` và `DiskPaths`. Bộ lọc mặc định của inventory chỉ hiện software có CPE chính thức. Trên Linux, chỉ liệt kê software cài qua package manager gốc (rpm, dnf, yum...) (theo snippet tìm kiếm của hai trang Learn, chưa mở trang) — [Export software inventory assessment per device](https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-software-inventory) (bậc 1); [Software inventory](https://learn.microsoft.com/defender-vulnerability-management/tvm-software-inventory) (bậc 1)
- **runZero**: theo docs, asset có first seen ("first identified"), last seen ("most recent timestamp when an asset responded to a probe during a scan") và alive. Field `services` "lists the most recently recorded services". Khi fingerprint thay đổi lớn, runZero đánh dấu asset cũ là offline và tạo asset mới — [Understanding assets](https://help.runzero.com/docs/understanding-assets/index.md) (bậc 1, truy cập 2026-11-04)
- runZero ở cấp service: integration XSOAR trả `RunZero.Service.First_Seen`, `Last_Seen` và `Detected` ("method of detection") cho từng service (theo snippet, chưa mở) — [XSOAR runZero integration](https://xsoar.pan.dev/docs/reference/integrations/run-zero) (bậc 1, không rõ ngày)
- Theo docs, runZero ghi nhận service từ active scan, passive discovery và integration. Passive sampling có các giới hạn: tối đa 1 lõi CPU (quá mức thì bỏ gói), tạm dừng khi có active scan trên cùng Explorer, bỏ qua traffic ngoài Discovery scope (theo snippet) — [runZero passive sampling](https://help.runzero.com/docs/traffic-sampling/) (bậc 1, chưa mở)
- **Axonius Software Assets** là "consolidated view of all installed software ... from all sources across all devices". "Preferred Software Name" và "Preferred Vendor Name" lấy từ Axonius Catalog nếu có, nếu không thì Axonius "selects the best naming option from all the fetched names", và tài liệu không định nghĩa thế nào là "best". Field Vendor và Publisher "interchangeable ... due to data parsing inconsistencies among different adapters". Có thêm field `Unique Version Count`. Preferred Software Name/Vendor được thêm ở bản 6.1.48 (theo snippet tìm kiếm) — [Axonius Software](https://docs.axonius.com/docs/software) (bậc 1); [What's New 6.1.48](https://docs.axonius.com/docs/whats-new-in-axonius-6148) (bậc 1)
- **Elastic/ECS**: trong ECS, `entity.attributes` là thuộc tính "static or semi-static", `entity.behavior` là đặc điểm "ephemeral ... derived from observed behavior over a time period", `entity.raw` giữ field gốc, và `entity.source` (beta) cho biết module hoặc integration đã cung cấp dữ liệu. Entity store có snapshot lịch sử hằng ngày (`.entities.v1.history.*`) (theo snippet tìm kiếm) — [ECS Entity fields](https://www.elastic.co/docs/reference/ecs/ecs-entity) (bậc 1); [Elastic entity store](https://www.elastic.co/guide/en/security/current/entity-store.html) (bậc 1)
- **Stamus**: first seen và last seen được lưu cho từng giá trị metadata của host (UA, TLS agent, login), không chỉ cho host — [Stamus Host Insights](https://docs.stamus-networks.com/39.0.0/concepts/host-insights.html) (bậc 1)
- **Zeek** (nhắc lại từ 4a): known_services chỉ giữ `ts` của lần phát hiện. Không có first_seen hay last_seen riêng, nhưng bản ghi lặp lại sau mỗi `1day` — [known-services.zeek](https://raw.githubusercontent.com/zeek/zeek/master/scripts/policy/protocols/conn/known-services.zeek) (bậc 1)

### Nhận định
- Đề xuất schema quan hệ, theo mẫu Defender và runZero:

  `asset_software(tenant, asset_id, product_id (catalog), raw_name, raw_vendor, version, evidence_type{package|process|registry|disk|network_banner|vuln_scan}, evidence_ref (path/registry/event uid), source (metadata.product + log_name), first_seen, last_seen, seen_count, confidence)`

  `asset_service` dùng cùng khung, thêm `port`, `proto`, `app_protocol_name`, `detected_method{listen|handshake|flow_heuristic|banner}`. Lưu **một dòng cho mỗi (quan hệ, nguồn)**, rồi tính dòng hợp nhất (`first_seen = min`, `last_seen = max`, `confidence = max` hoặc công thức noisy-OR theo loại bằng chứng).
- Xung đột phiên bản giữa các nguồn: Axonius giữ mọi version (`Unique Version Count`) chứ không chọn một. Ở bảng hợp nhất nên ưu tiên nguồn host (package/registry) hơn nguồn mạng (banner), và hiện cảnh báo khi các nguồn cùng `last_seen` mà version khác nhau.
- Nguồn OCSF cho `evidence_ref`:

  | Nguồn | Field làm bằng chứng |
  |---|---|
  | `5020` | `package.purl`/`cpe_name` |
  | `1007` | `process.file.path` + `hashes` |
  | `201004` | `win_service.service_file` |
  | `2002` | `affected_packages` |
  | `4002` | header `Server` |

  Mọi bằng chứng đều giữ `metadata.uid` của event gốc để truy vết.

### Khoảng trống
- Chưa tìm được tài liệu Splunk Exposure Analytics về evidence hay confidence cho quan hệ software/service.
- Chưa có tài liệu vendor nào công bố công thức confidence số cho quan hệ asset → software/service.
- Thuật toán chọn "best" name của Axonius không được công bố.

## 4c. Phát hiện SaaS/app usage từ log firewall/proxy

### Kết luận ngắn
Các sản phẩm đều đi theo một luồng: **parse log (theo parser riêng từng nguồn) → so domain/URL (hoặc IP nếu log không có URL) với catalog ứng dụng có điểm rủi ro → đếm user, IP, device, transaction, traffic theo app**. Ứng dụng nằm ngoài catalog thì không được phát hiện, trừ khi khai báo custom app (domain hoặc IP). Gán usage cho device/user cần log có username, hoặc agent endpoint (MDE). Mức chắc chắn **cao** cho Microsoft (docs đã đọc), **trung bình** cho Netskope, Zscaler, Palo Alto, Cloudflare (snippet docs).

### Phát hiện có nguồn
- **Microsoft Defender for Cloud Apps (MDA) Cloud Discovery** so traffic log với catalog "over 31,000 cloud apps", xếp hạng theo "more than 90 risk factors". Mặc định "cannot discover apps that aren't in the catalog". Quy trình: Upload → Parse ("dedicated parser for each data source") → Analyze (so với catalog, nhận diện "Active users and IP addresses") → Report. Dữ liệu "analyzed and updated four times a day" — [Cloud app discovery overview](https://learn.microsoft.com/en-us/defender-cloud-apps/set-up-cloud-discovery) (bậc 1, cập nhật 2025-09-17)
- MDA có các nguồn đầu vào: snapshot (upload tay), continuous qua log collector (Syslog/FTP), tích hợp MDE, tích hợp SWG (Zscaler, iboss, Corrata, Menlo) và API. Có khoảng 35 nguồn firewall/proxy được hỗ trợ. Trang có bảng thuộc tính cho từng nguồn: Target App URL, Target App IP, Username, Origin IP, Total traffic, Uploaded bytes. Nhiều nguồn **không có URL**, ví dụ Check Point, Cisco ASA syslog, Fortinet FortiGate, Juniper SRX, Palo Alto Networks, Stormshield. Một số nguồn **không có username**, ví dụ Check Point, Cisco ASA, Meraki, Juniper SRX, McAfee SWG, SonicWall. Nếu log không được hỗ trợ thì chọn "Other" hoặc viết custom parser — [set-up-cloud-discovery](https://learn.microsoft.com/en-us/defender-cloud-apps/set-up-cloud-discovery) (bậc 1, 2025-09-17)
- MDA **gán usage cho device**: tích hợp MDE dùng "network transaction logs" mà agent tạo ra, và "provide user and device information for traffic activities", nhờ đó biết "which user did which activity from which device". Yêu cầu MDE Plan 2 hoặc Defender for Business. Trên macOS phải bật network protection, và vì network protection "only audits TCP connection close events, UDP protocols aren't covered". Dữ liệu xuất hiện tối đa 2 giờ sau khi bật — [Integrate Microsoft Defender for Endpoint](https://learn.microsoft.com/en-us/defender-cloud-apps/mde-integration) (bậc 1, 2026-07-03)
- **Custom app** của MDA: khai báo "unique domains that are used when accessing the custom app. These domains are used to match traffic log messages to this app". Nếu nguồn không có URL thì khai báo IPv4/IPv6. Kết quả gồm số user, số IP nguồn duy nhất và lưu lượng vào/ra — [Add custom apps to cloud discovery](https://learn.microsoft.com/en-us/defender-cloud-apps/cloud-discovery-custom-apps) (bậc 1, 2026-07-03)
- MDA Discovered apps:
  - Bộ lọc usage dùng ngưỡng Users và Transactions, ví dụ trên 50 user và trên 100 transaction.
  - Deep dive và discovery tài nguyên IaaS/PaaS "supported only in firewalls and proxies that contain target URL data".
  - Subdomain không khớp catalog bị gắn "Other". Tính năng discovered subdomains bị deprecate từ 31/12/2025.
  - Loại trừ được user, nhóm, IP và device gây nhiễu, nhưng chỉ áp dụng cho dữ liệu mới. Dữ liệu cũ lưu 90 ngày.
  - Global report "doesn't include data from Microsoft Defender for Endpoint", tức stream MDE tách riêng.
  - Report tuỳ chỉnh tối đa 1 GB.
  - Microsoft khuyên xoá dữ liệu discovery khi dữ liệu cũ làm sai kết quả, hoặc khi user quay lại sau thời gian offline bị coi là bất thường.

  Nguồn: [View discovered apps](https://learn.microsoft.com/en-us/defender-cloud-apps/discovered-apps) (bậc 1, 2026-07-03)
- MDA risk score là trung bình có trọng số của các nhóm General, Security, Compliance, Legal, có thể ghi đè điểm cho từng app (theo snippet) — [Risk score](https://learn.microsoft.com/en-us/defender-cloud-apps/risk-score) (bậc 1)
- **Palo Alto SaaS Security Inline** theo dõi "over 80 attributes" và tính risk score từ "over 55" thuộc tính thuộc các nhóm Compliance, IAM, Security & Privacy. App GenAI có thêm điểm GenAI, được trọng số cao hơn. Thang điểm 1–5 (4–5 High, 3 Medium, 1–2 Low) từ 6/2024. Có app "temporarily have no risk score" vì đang chờ đánh giá (snippet docs) — [How SaaS Security Inline Determines an Application's Risk Score](https://docs.paloaltonetworks.com/saas-security/saas-security-admin/saas-security-inline/assess-risks/view-data/how-saas-security-inline-determines-an-applications-risk-score) (bậc 1); [June 2024 release](https://docs.paloaltonetworks.com/saas-security/saas-security-release-notes/features-introduced-in-2024/new-features-introduced-in-june-2024) (bậc 1, 2024-06)
- **Zscaler ZIA Shadow IT report** có Application Risk Index từ 1 đến 5, ghi đè được, và metric "Total Applications" là số SaaS app duy nhất phát hiện được. Thuộc tính rủi ro gồm: từng bị breach trong 3 năm, hỗ trợ IP restriction/MFA/WAF, chứng chỉ SSL hợp lệ, CVE, Heartbleed/POODLE/Logjam. Zscaler không công bố số app trong catalog (snippet; con số "50K" là giới hạn hỗ trợ, không phải số app trong catalog) — [Zscaler Shadow IT report](https://help.zscaler.com/zia/shadow-it-report) (bậc 1); [About application information](https://help.zscaler.com/zia/about-application-information) (bậc 1)
- **Netskope CCI** cho mỗi app điểm 0–100, chia 5 mức Poor, Low, Medium, High, Excellent, dựa trên tiêu chí phỏng theo Cloud Security Alliance. Từ khi có GenAI thì thêm thuộc tính rủi ro GenAI. Con số khoảng 2.600–3.000 app là của năm 2013, đã cũ (snippet) — [Netskope Cloud Confidence Index](https://docs.netskope.com/en/cloud-confidence-index/) (bậc 1); [Numbers behind CCI](https://www.netskope.com/blog/numbers-behind-cci) (bậc 1, 2013)
- **Cloudflare Gateway Shadow IT** dựng từ Gateway HTTP traffic: "you must set up HTTP filtering". App mới phát hiện mặc định ở trạng thái "Unreviewed". Trạng thái phê duyệt "does not impact a user's ability to access an application", muốn chặn thì phải viết Gateway policy (snippet) — [Cloudflare Shadow IT discovery](https://developers.cloudflare.com/cloudflare-one/insights/analytics/shadow-it-discovery/) (bậc 1); [Shadow IT analytics changelog](https://developers.cloudflare.com/changelog/2025-08-27-shadow-it-analytics/) (bậc 1, 2025-08-27)
- Giới hạn của phát hiện theo domain: CDN dùng chung IP, ECH che SNI, cùng hostname cho cả tài khoản cá nhân và doanh nghiệp, user remote không đi qua firewall. Các nguồn tìm được chỉ là blog vendor — [dope.security](https://dope.security/post/shadow-ai-vs-shadow-it-discovery-gap) (bậc 3); [fitgap](https://us.fitgap.com/stack-guides/closing-shadow-it-visibility-gaps-with-network-sso-and-saas-discovery-signals) (bậc 3)

### Nhận định
- Ánh xạ sang OCSF 1.9.0 cho `asset_app_usage(tenant, asset_id | user_id, app_id (catalog), first_seen, last_seen, transactions, bytes_up, bytes_down, evidence_source)`. Các nguồn xếp theo độ tin cậy của khoá:
  1. `4002` HTTP Activity: `http_request.url.hostname`/`url.domain` (từ proxy/SWG có URL đầy đủ), `user_agent` (để phân biệt client app hay trình duyệt), `actor.user`, `src_endpoint`.
  2. `4001`/`4002`: `tls.sni`. Dùng được khi firewall chỉ thấy SNI, nhưng mất tác dụng khi có ECH.
  3. `4003` DNS Activity: `query.hostname`. Đây là ý định truy cập, không phải truy cập thật, nên chỉ dùng làm bằng chứng phụ hoặc để gắn IP với domain theo thời gian.
  4. `4001`: `app_name` (App-ID/NBAR do firewall đã phân loại sẵn) và `dst_endpoint.ip`. Đây là trường hợp log không có URL, giống Palo Alto, FortiGate, Check Point trong bảng của MDA. Ghép bằng `app_name` → catalog, hoặc IP → dải IP đã khai báo của app.
  5. `3002` Authentication: `service.name`/`dst_endpoint` của IdP (SSO), và `6003` API Activity: `api.service.name` (log SaaS do chính SaaS cung cấp). Đây là bằng chứng "dùng thật có định danh". Không đọc được nguồn chính thức nào trong lượt này, các nhận xét về SSO đều từ blog bậc 3.
- Gán usage cho asset: lấy `src_endpoint.ip` ở thời điểm event, phân giải qua chỉ mục IP→asset theo thời gian (DHCP `4004`, cách làm đã có ở report 2026-11-03). Khi có NAT hoặc proxy thì phải dùng `http_request.x_forwarded_for` hoặc log từ endpoint (giống tích hợp MDE). Nếu log chỉ có user mà không có device thì lưu quan hệ user → app, không ép về asset.
- Catalog nên giữ ba loại khoá match là domain (có wildcard), IP range và App-ID/`app_name`, mỗi khoá kèm thứ tự ưu tiên khi trùng. Đây là suy luận từ cách MDA định nghĩa custom app theo domain trước, IP sau. Domain dùng chung (CDN, `*.amazonaws.com`, `*.googleusercontent.com`) cần được đánh dấu "không đủ để kết luận app".

### Khoảng trống
- Chưa có số liệu độc lập về tỉ lệ match đúng giữa domain và app hay tỉ lệ dương tính giả do CDN. Không có nguồn bậc 1–2.
- Chưa đọc trực tiếp các trang Netskope, Zscaler, Palo Alto, Cloudflare (chỉ có snippet).
- Chưa rõ MDA xử lý thứ tự ưu tiên URL hay IP thế nào khi một log có cả hai.

## 4d. Đo chất lượng service/software inventory suy diễn

### Kết luận ngắn
Không có chuẩn đánh giá công khai nào dành riêng cho việc này. Bartlett 2007 là khuôn mẫu gần nhất. Họ thiếu ground truth thật nên lấy **union các phương pháp làm ground truth**, rồi đo completeness theo ba trọng số: số server, số client và số flow, cộng với đường cong theo thời gian quan sát. Áp vào SOC: dùng agent inventory hoặc CMDB làm ground truth cục bộ, đo precision/recall theo từng loại bằng chứng, thêm chỉ số độ trễ phát hiện và độ cũ. Mức chắc chắn **trung bình** cho phương pháp (có nguồn bậc 1). Mức chắc chắn **thấp** cho chỉ số cụ thể, vì đó là suy luận.

### Phát hiện có nguồn
- Bartlett 2007 định nghĩa ground truth là union giữa passive và active. Họ đo completeness không trọng số và có trọng số (theo client duy nhất, theo flow), và đo theo thời lượng quan sát (12 giờ, 25 giờ, 9 ngày, 18 ngày, 90 ngày). Paper cũng tách riêng địa chỉ transient (VPN/PPP) vì chúng làm passive "never levels off" — [Bartlett 2007](https://ant.isi.edu/~johnh/PAPERS/Bartlett07d.pdf) (bậc 1, 2007)
- Bằng chứng cho thấy độ cũ (staleness) là vấn đề vận hành có thật:
  - Zeek cho mục known_services hết hạn sau 1 ngày, rồi log lại.
  - MDA khuyên xoá dữ liệu discovery cũ khi nó làm sai kết quả, và giữ dữ liệu 90 ngày.
  - runZero tạo asset mới khi fingerprint đổi nhiều, nên có thể sinh bản trùng ở trạng thái offline.

  Nguồn: [known-services.zeek](https://raw.githubusercontent.com/zeek/zeek/master/scripts/policy/protocols/conn/known-services.zeek) (bậc 1); [MDA discovered apps](https://learn.microsoft.com/en-us/defender-cloud-apps/discovered-apps) (bậc 1, 2026-07-03); [runZero understanding assets](https://help.runzero.com/docs/understanding-assets/index.md) (bậc 1)
- Defender lọc mặc định theo software có CPE chính thức, nên inventory "chuẩn" của vendor tự nó cũng là một tập con. Khi dùng làm ground truth cần biết điều này (snippet) — [Software inventory](https://learn.microsoft.com/defender-vulnerability-management/tvm-software-inventory) (bậc 1)

### Nhận định
- Đề xuất bộ chỉ số, tính theo tenant và theo `evidence_type`:
  - **Precision**: tỉ lệ quan hệ suy diễn được xác nhận bởi nguồn tham chiếu. Ví dụ, `asset_service` từ flow được xác nhận bởi `4001` Listen hoặc `5040` từ EDR trên cùng asset.
  - **Recall**: tỉ lệ quan hệ trong nguồn tham chiếu (agent inventory, CMDB) mà pipeline suy diễn được. Chỉ đo trên tập asset có cả hai loại nguồn.
  - **Recall có trọng số**: tính theo số client hoặc số flow, như Bartlett.
  - **Time-to-detect**: thời gian từ khi service hoặc app xuất hiện tới lúc pipeline thấy.
  - **Staleness rate**: tỉ lệ quan hệ có `last_seen` quá ngưỡng mà nguồn tham chiếu vẫn báo còn.
  - **Churn**: số quan hệ mới hoặc mất mỗi ngày, để phát hiện drift do parser hỏng hoặc nguồn log tắt.
- Có ba bẫy khi đánh giá:
  1. Nguồn tham chiếu cũng thiếu: CMDB lỗi thời, Defender chỉ có software có CPE. Vì thế nên báo cáo dạng Venn hoặc union như Bartlett, không coi một nguồn là sự thật tuyệt đối.
  2. Asset có IP transient làm recall thấp giả tạo.
  3. Service idle không bao giờ thấy được bằng passive. Nên ghi nhận đây là giới hạn đã biết, không tính là lỗi pipeline.
- Phát hiện drift: so số `asset_service`/`asset_app_usage` theo ngày cho từng `metadata.product.name`. Số rơi đột ngột thường là do mất nguồn log, không phải do service biến mất. Nên gắn chỉ số này với coverage theo nguồn (đã đề xuất ở report 2026-11-03).

### Khoảng trống
- Chưa tìm thấy nghiên cứu 2018–2026 đo precision/recall của software/service inventory suy diễn từ log so với agent inventory. Truy vấn "passive asset discovery evaluation accuracy ... ground truth" chỉ trả về Bartlett 2007 và blog vendor.
- Chưa có số liệu độc lập về độ chính xác SaaS discovery.

## Truy vấn đã chạy
- Bartlett Heidemann Papadopoulos understanding passive and active service discovery IMC 2007 (standard)
- Zeek known_services.zeek how service detected protocol confirmation (standard)
- Defender for Cloud Apps cloud discovery supported firewalls proxies log collector (standard)
- runZero services table first seen last seen asset (standard)
- Defender for Cloud Apps cloud app catalog risk score 90 risk factors 31000 apps (standard)
- Defender Vulnerability Management software inventory "evidence" path registry last seen device (standard)
- Tan role classification of hosts within enterprise networks based on connection patterns USENIX 2003 (standard)
- flow direction inference client server unknown NetFlow heuristic ephemeral port paper (extended)
- ExtraHop device role automatic assignment discovery how roles are assigned (standard)
- Defender for Endpoint DeviceNetworkInfo open ports exposure graph listening ports (standard)
- Elastic entity store observed attributes host entity definition fields "entity.source" latest (standard)
- runZero passive discovery traffic sampling services detected (standard)
- Cloudflare Zero Trust shadow IT SaaS discovery Gateway HTTP logs application status unreviewed (standard)
- Netskope Cloud Confidence Index CCI number of apps attributes score (standard)
- shadow IT discovery limitations SNI CDN shared domains cannot identify application TLS encrypted firewall logs (standard)
- host role inference flow data servers clients precision recall enterprise network ground truth CMDB (extended)
- Corelight known entities "known_services" "known_hosts" entity collection software log (standard)
- Vectra AI host roles observed privilege "detected roles" DNS server, domain controller inference (standard)
- passive asset discovery evaluation accuracy compared active scanning ground truth study services coverage (extended)
- Palo Alto SaaS Security discovered apps App-ID SaaS application attributes risk score number of apps (standard)
- Zscaler Shadow IT report cloud application catalog risk index attributes number of applications (standard)
- Axonius installed software aggregated multiple adapters "software" normalization conflict preferred value (standard)
