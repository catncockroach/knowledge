# Nhận diện thụ động qua mạng

## Câu hỏi phụ 2: Nhận diện thụ động dịch vụ, ứng dụng, OS và loại thiết bị qua mạng hoạt động thế nào, chính xác đến đâu, và bằng chứng đó nằm ở đâu trong OCSF 1.9.0?

### Kết luận ngắn
Nhận diện thụ động dựa trên vài nhóm tín hiệu: vai trò responder kèm xác nhận giao thức (Zeek known_services); chuỗi tự khai bằng cleartext (HTTP `Server`/`User-Agent`, banner SSH, DHCP option 12/60/81, mDNS/SSDP); fingerprint của handshake (JA3/JA4+, HASSH, p0f TCP SYN, DHCP option 55); và phân loại DPI của firewall (App-ID, NBAR2). OCSF 1.9.0 có chỗ native cho phần lớn fingerprint TLS/SSH/JA4+ và cho `app_name`/`app_protocol_name`, nhưng không có chỗ cho DHCP fingerprint/vendor class, banner SSH, header `Server` (chỉ có mảng `http_headers` chung) và nhãn phân loại của DB fingerprint. Độ chắc chắn **cao** với cơ chế và mapping schema, vì đã đọc mã nguồn, tài liệu chính thức và schema gốc. Độ chắc chắn **trung bình–thấp** với độ chính xác, vì số liệu độc lập ít, khác bộ dữ liệu, và phần lớn số liệu vendor là tự công bố.

### Phát hiện có nguồn

**Zeek: known_services, known_hosts, software.log, DHCP**
- `known_services.log` chỉ ghi service ở **phía responder** (`id$resp_h`) và mặc định chỉ cho host nội bộ (`service_tracking = LOCAL_HOSTS`). Với TCP, server phải đã bắt tay. Comment trong code: "Not a service unless the TCP server did a handshake (SYN+ACK)". Trạng thái chấp nhận gồm `TCP_ESTABLISHED`/`TCP_CLOSED`/`TCP_PARTIAL` hoặc history có `h`. Với UDP, mặc định server phải đã gửi dữ liệu (`service_udp_requires_response`). ICMP không bao giờ được coi là service. — [known-services.zeek](https://github.com/zeek/zeek/blob/master/scripts/policy/protocols/conn/known-services.zeek) (bậc 1, master, truy cập 2026-11-04)
- Script kiểm tra ở `analyzer_confirmation_info` (sự kiện analyzer xác nhận giao thức) và khi connection kết thúc. Nếu chưa nhận ra giao thức, nó chờ 5 phút rồi mới log, để kịp nhận giao thức từ connection khác. Service có tên bắt đầu bằng `-` (giao thức đã xác nhận rồi bị vi phạm) bị loại. Kết nối chỉ có `ftp-data` cũng bị bỏ qua. DNS phải có `resp$size > 0`. Kết quả được dedup theo (host, port) trong 1 ngày (`&create_expire=1day`). Các field: `ts`, `host`, `port_num`, `port_proto`, `service` (tập giao thức khớp payload). — [known-services.zeek](https://github.com/zeek/zeek/blob/master/scripts/policy/protocols/conn/known-services.zeek) (bậc 1)
- `known_hosts.log` ghi các IP "that Zeek determines have performed complete TCP handshakes", mỗi ngày một lần. Field chỉ có `ts` và `host`. — [known-hosts.zeek](https://github.com/zeek/zeek/blob/master/scripts/policy/protocols/conn/known-hosts.zeek) (bậc 1)
- `software.log` (framework Software) có các field `ts`, `host`, `host_p` ("Only sensible for server software"), `software_type`, `name`, `version` (major/minor/minor2/minor3/addl) và `unparsed_version`. Field cuối được giữ vì "version parsing doesn't always work reliably". Mặc định `asset_tracking = LOCAL_HOSTS`, và chỉ log khi phần mềm mới hoặc đổi version. — [software/main.zeek](https://github.com/zeek/zeek/blob/master/scripts/base/frameworks/software/main.zeek) (bậc 1)
- Các nguồn đưa dữ liệu vào software.log:
  - HTTP: `User-Agent` → `BROWSER` gắn cho `orig_h`; `Server` → `HTTP::SERVER` và `X-Powered-By` → `APPSERVER`, cả hai gắn cho `resp_h:resp_p`. — [http/software.zeek](https://github.com/zeek/zeek/blob/master/scripts/policy/protocols/http/software.zeek) (bậc 1)
  - SSH: banner client → `SSH::CLIENT` (orig), banner server → `SSH::SERVER` (resp + port). — [ssh/software.zeek](https://github.com/zeek/zeek/blob/master/scripts/policy/protocols/ssh/software.zeek) (bậc 1)
  - DHCP: option `vendor_class` (60) → `DHCP::CLIENT`/`DHCP::SERVER`, đồng thời được log thành `client_software`/`server_software`. — [dhcp/software.zeek](https://github.com/zeek/zeek/blob/master/scripts/policy/protocols/dhcp/software.zeek) (bậc 1)
- `dhcp.log` mặc định có `mac`, `host_name` (option 12), `client_fqdn` (option 81), `domain` (option 15), `requested_addr`, `assigned_addr`, `lease_time`, `msg_types`, `duration`. Script `sub-opts` thêm `circuit_id`, `agent_remote_id`, `subscriber_id` (option 82). Bản đã đọc không log Parameter Request List (option 55), tức fingerprint kiểu Fingerbank, nên muốn có thì phải viết script riêng. — [dhcp/main.zeek](https://github.com/zeek/zeek/blob/master/scripts/base/protocols/dhcp/main.zeek), [dhcp/sub-opts.zeek](https://github.com/zeek/zeek/blob/master/scripts/policy/protocols/dhcp/sub-opts.zeek) (bậc 1)

**Suricata**
- EVE có `app_proto` ở phần chung của flow/alert khi phát hiện giao thức app-layer.
- TLS có `sni`, `version`, `subject`, `issuerdn`, `fingerprint` (SHA-1 của cert), `ja3{hash,string}` và `ja3s`. `ja4` phải bật bằng `app-layer.protocols.tls.ja4-fingerprints`.
- HTTP có `http_user_agent`. Header `Server` không có field riêng, phải thêm vào danh sách `custom` hoặc bật `dump-all-headers`.
- SSH có `client`/`server`.`software_version`, `proto_version` và `hassh.hash`/`hassh.string` (phải bật `app-layer.protocols.ssh.hassh`).

  Nguồn: [Suricata EVE JSON format](https://docs.suricata.io/en/latest/output/eve/eve-json-format.html) (bậc 1, bản latest, truy cập 2026-11-04)

**JA3 / JA4+**
- Chrome xáo thứ tự extension của ClientHello, nên mỗi kết nối cho ra một JA3 khác nhau. Có gần 15! (≈10^12) hoán vị. Fastly thấy JA3 phổ biến nhất của Chrome (`cd08e31494f9531f560d64c695473da9`) giảm mạnh từ 2023-01-20. Tính năng dự kiến cho Chrome 110 nhưng đã có hiệu lực từ 108–109. — [Fastly: Examining Chrome's TLS ClientHello Permutation](https://www.fastly.com/blog/a-first-look-at-chromes-tls-clienthello-permutation-in-the-wild) (bậc 2, 2023-02-08)
- Bộ JA4+ gồm:
  - JA4: TLS client
  - JA4S: phản hồi/phiên TLS của server
  - JA4H: HTTP client
  - JA4L/JA4LS: độ trễ, ước lượng khoảng cách
  - JA4X: chứng chỉ X.509
  - JA4SSH: lưu lượng SSH
  - JA4T/JA4TS: TCP client/server
  - JA4TScan: quét chủ động
  - Mới hơn: JA4D/JA4D6 (DHCP/DHCPv6), JA4N (NTP), JA4Scan-TLS/QUIC

  Về license: "JA4: TLS Client Fingerprinting is open-source, BSD 3-Clause, same as JA3". Các phương pháp còn lại "patent-pending and licensed under the FoxIO License 1.1". License này cho phép dùng học thuật và nội bộ doanh nghiệp, nhưng vendor muốn bán JA4+ trong sản phẩm phải xin OEM license. DB chính thức là ja4db.com ("under very active development"), repo kèm `ja4plus-mapping.csv`. Có implementation cho Zeek và Wireshark, được hỗ trợ trong Arkime; Suricata có JA4 hash (JA4+ "under development"). — [FoxIO-LLC/ja4 README](https://github.com/FoxIO-LLC/ja4) (bậc 1, truy cập 2026-11-04)
- Satori (xnih) là công cụ passive viết bằng Python, fingerprint qua DHCP, TCP, HTTP (User-Agent và Server), SMB và SSL (JA3/JA3S/JA4). Fingerprint lưu ở file XML, dữ liệu SSL lấy chủ yếu từ sslbl.abuse.ch. Tác giả nói fingerprint được cập nhật "as time allows". — [xnih/satori](https://github.com/xnih/satori) (bậc 1, nội dung qua kết quả search, chưa mở trang)

**HASSH**
- HASSH/HASSHServer là MD5 của danh sách thuật toán kex;encryption;MAC;compression trong `SSH_MSG_KEXINIT` (gửi cleartext). Nó nhận diện implementation "regardless of higher level ostensible identifiers such as 'Client' or 'Server' strings". README lấy ví dụ honeypot Cowrie/Kippo lộ hasshServer dù banner giả OpenSSH. Repo Salesforce đã được archive ngày 2025-05-01 và "no longer being actively maintained"; tác giả tiếp tục phát triển ở fork của Corelight. — [salesforce/hassh](https://github.com/salesforce/hassh) (bậc 1)

**DHCP fingerprinting (Fingerbank)**
- API `interrogate` của Fingerbank nhận các input: `dhcp_fingerprint` (danh sách option theo thứ tự trong gói), `dhcp6_fingerprint`, `dhcp_vendor` (vd `MSFT 5.0`), `dhcp6_enterprise`, `mac`, `hostname`, `destination_hosts`, `ja3_fingerprints`/`ja3_data`, `mdns_services`, `upnp_user_agents`, `upnp_server_strings`, `tcp_syn_signatures`/`tcp_syn_ack_signatures` (định dạng p0f), `user_agents` và `client_hints`. Output gồm `device` (cây phân cấp, có `can_be_more_precise`), `device_name`, `manufacturer`, `operating_system`, `version` và `score` 0–100 ("<30 very little confidence", "51–75 High", ">76 Very high"). — [Fingerbank API v2 interrogate](https://api.fingerbank.org/api_doc/2/combinations/interrogate.html) (bậc 1, không rõ ngày)
- Fingerbank/PacketFence dùng option 55 làm tín hiệu chính, theo lời Olivier Bilodeau (lead dev PacketFence): "what we've been using for PacketFence, actually, is the option 55". — [DEF CON 19 transcript](https://media.defcon.org/DEF%20CON%2019/DEF%20CON%2019%20video%20and%20slides/DEF%20CON%2019%20video%20and%20slides%20captions/DEF%20CON%2019%20-%20Olivier%20Bilodeau%20-%20Fingerbank%20Open%20DHCP%20Fingerprints%20Database.eng.txt) (bậc 2, 2011). Cisco ISE lưu ý dữ liệu này phụ thuộc vendor và "can be duplicated by multiple device types". — [Cisco ISE profiling config](https://www.cisco.com/c/it_it/support/docs/security/identity-services-engine/116235-configure-ise-00.pdf) (bậc 1, không rõ ngày; qua search, chưa mở)

**Thương mại**
- **Palo Alto App-ID.** Thứ tự xử lý: áp policy → signature (dù app chạy trên port chuẩn hay không) → nếu có SSL/SSH và có rule decrypt thì giải mã rồi khớp signature lại → decoder giao thức (tìm app tunnel bên trong, như IM qua HTTP) → heuristic/hành vi cho app lẩn tránh. App-ID xác định app "irrespective of port, protocol, encryption". — [PAN-OS 11.1 App-ID Overview](https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-admin/app-id/app-id-overview) (bậc 1). KB của PAN khuyên chặn QUIC (UDP/443, UDP/80): nếu cho phép thì phiên Chrome tới Google chỉ được nhận là `quic` và "visibility and control of Google applications is lost". — [How to Block QUIC Protocol](https://live.paloaltonetworks.com/t5/Management-Articles/How-to-Block-QUIC-Protocol/ta-p/120207) (bậc 1, tạo 2018, sửa 2023-06)
- **Cisco NBAR2.** Signature được phân phối bằng Protocol Pack, tách khỏi chu kỳ phát hành IOS. App có thuộc tính category, sub-category, application-group, p2p, tunnel và encrypted. Với traffic mã hoá, NBAR2 phân tích DNS, phân tích handshake SSL (certificate, SNI), dùng ML/thống kê và heuristic. — [Cisco Live BRKENT-2336](https://www.ciscolive.com/c/dam/r/ciscolive/emea/docs/2025/pdf/BRKENT-2336.pdf) (bậc 1 vendor, 2025; qua search, chưa mở PDF)
- **Microsoft Defender for Endpoint device discovery.**
  - Basic là chế độ thụ động: SenseNDR.exe trên máy đã onboard "Passively collects events and extracts device information from all network traffic seen by onboarded devices".
  - Standard (mặc định) thêm probe chủ động, "typically no more than once every three weeks", tối đa 50KB mỗi lần.
  - Giao thức Basic: ARP, CDP, DHCP, DHCPv6, IP headers, LLDP, LLMNR, mDNS, MNDP, MSSQL, NBNS, SSDP, TCP SYN headers, UDP headers, WSD.
  - Mạng được coi là "corporate" khi nhiều thiết bị của tenant cùng báo một tên mạng, default gateway và DHCP server.
  - Microsoft mô tả Basic là "Provides limited visibility of unmanaged endpoints".

  Nguồn: [Defender for Endpoint device discovery overview](https://learn.microsoft.com/en-us/defender-endpoint/device-discovery) (bậc 1, ms.date 2025-05-08, cập nhật 2026-04-13)
- **Forescout.** Kết hợp phương pháp thụ động (SNMP trap, controller…) và chủ động (WMI/SMB, NMAP, SNMP query, agent), ưu tiên passive cho OT. Device Cloud tự công bố >11 triệu thiết bị, >1.900 phiên bản OS, >7.700 vendor/model (datasheet 2022). Một patent của Forescout mô tả việc dùng phương pháp phân loại tin cậy cao để huấn luyện phương pháp tin cậy thấp. — [Forescout agentless visibility white paper](https://forescout.com/resources/agentless-visibility-control-white-paper), [eyeSight datasheet](https://forescout.com/resources/forescout-eyesight-datasheet), [US11240132B2](https://patents.google.com/patent/US11240132) (bậc 1 vendor, tự tuyên bố; qua search, chưa mở)
- **Armis.** Agentless, nghe SPAN/TAP và tích hợp, rồi so profile với "Device Knowledgebase" crowd-sourced. Quy mô knowledgebase tự công bố thay đổi theo thời điểm: 80 triệu thiết bị (2019–2020), 230 triệu (brief sau này). — [Armis Solution Brief](https://www.cc.com.pl/pl/prods/armis/pdf/Armis_Solution_Brief.pdf) (bậc 1 vendor, tự tuyên bố; qua search, chưa mở)
- **runZero.**
  - Traffic sampling nghe SPAN/TAP, hỗ trợ 802.1q/QinQ, GRE, VXLAN; mỗi task giới hạn 1 CPU core và "temporarily skips packets" khi quá tải. Task passive dừng khi Explorer chạy active scan. IP trùng giữa các site có thể sinh asset trùng. — [runZero Traffic sampling](https://help.runzero.com/docs/traffic-sampling/) (bậc 1, truy cập 2026-11-04)
  - Sampler không giữ full pcap, chỉ lấy dữ liệu cần cho discovery/fingerprint, chuyển thành asset record cùng dạng với kết quả scan và "scrubs sensitive fields". — [runZero FAQ](https://runzero.freshdesk.com/support/solutions/articles/70000657769-what-information-does-runzero-traffic-sampling-collect-) (bậc 1, 2023-11-27)
- **Recog (Rapid7, BSD-2).** Fingerprint là các file XML chứa regex chạy trên banner/header (`ssh_banners.xml`, `http_servers.xml`, `http_cookies.xml`, `http_wwwauth.xml`, `ftp_banners.xml`, `favicons.xml`, `jarm.xml`…). Output có `os.vendor/family/product/cpe23`, `service.vendor/product/version/cpe23` (vd `cpe:/a:apache:http_server:2.4.38`) và `hw.vendor/product/device`. — [rapid7/recog](https://github.com/rapid7/recog) (bậc 1)

**Độ chính xác (học thuật, độc lập trừ khi ghi khác)**
- Anderson & McGrew (Cisco) kết hợp TLS + TCP/IP + HTTP qua nhiều session, đạt 99,4% ở major version OS và 97,5% ở minor version, >98% khi phát hiện OS chưa vá. Đây là nghiên cứu của vendor trên một mạng riêng. — [arXiv:1706.08003](https://arxiv.org/abs/1706.08003) (bậc 1, 2017-06)
- Bài FT-Transformer (2025) đo trên DAT2 (web server Masaryk, IPFIX): 95,04% ở mức family, 79,09% ở major, 68,52% ở minor; trên DAT1 (Eduroam): 90,69% ở mức family. Các phương pháp cũ mà bài trích lại cho DAT2 minor: Beverly (Bayes) 0,5%, Laštovička 2018/2020 (DT) ≈73%, Lippmann (kNN) 92,1%. Bài cảnh báo so sánh khó vì "the lack of accuracy metrics or detailed evaluation data", và việc gộp các version gần nhau làm số liệu đẹp lên. — [Application of Tabular Transformer Architectures for OS Fingerprinting](https://arxiv.org/html/2502.09084) (bậc 1, 2025-02)
- Laštovička et al. 2023 ("Passive OS fingerprinting revisited", Computer Networks 229:109782): theo tóm tắt, p0f chính xác cao trong bài toán đa lớp nhưng không nhận ra OS mới, và việc tái lập kết quả là một vấn đề. — [ResearchGate](https://www.researchgate.net/publication/370164594_Passive_Operating_System_Fingerprinting_Revisited_Evaluation_and_Current_Challenges) (bậc 1, 2023; chỉ đọc được tóm tắt qua search, PDF ở is.muni.cz không tải được)
- Sivanathan et al. (IEEE TMC): phân loại đa tầng 28 thiết bị IoT với >99% accuracy, dùng activity cycle, port, signalling và cipher suite. Kết quả từ testbed nhỏ, một nhà. — [UNSW PDF](https://www2.ee.unsw.edu.au/~hhabibi/pubs/jrnl/19TMC.pdf) (bậc 1, 2018–2019; qua search, chưa mở)

**Giới hạn: ECH, QUIC, NAT, CDN**
- ECH đã thành RFC 9849 "TLS Encrypted Client Hello", Proposed Standard, năm 2026. — [RFC 9849](https://www.rfc-editor.org/info/rfc9849) (bậc 1, 2026)
- Theo Cisco, khi có ECH, firewall chỉ thấy outer SNI (thường là tên CDN chung), nên rule URL category/AppID/SI bị vượt qua. Từ VDB 416 (2025-10), Cisco có App ID "ECH Servers" nhận các CDN hỗ trợ ECH. Encrypted Visibility Engine vẫn nhận được process phía client (Chrome, Firefox…) từ fingerprint handshake TLS/QUIC, nhưng "does not discover the actual target of the connection". Cisco khuyên không chặn ECH mà dùng kết hợp kiểm soát DNS (bỏ tham số ECH khỏi HTTPS RR), policy endpoint và decrypt chọn lọc. — [Cisco: ECH Defense Strategies](https://secure.cisco.com/secure-firewall/docs/encrypted-client-hello-defense-strategies-how-cisco-secure-firewall-tackles-ech) (bậc 1 vendor, cập nhật 2026-08-24)
- NAT: Maier et al. (PAM 2011) dùng initial TTL kết hợp User-Agent để đếm host sau NAT; ở một ISP DSL, >90% đường dây dùng NAT và 30–52% có nhiều end-host trong 24h. Theo cùng bài, Beverly ước tính NAT làm số host bị đếm lệch khoảng 9% (trace 2004). — [NAT Usage in Residential Broadband Networks](https://www.icir.org/gregor/papers/pam11-nat.pdf) (bậc 1, 2011; qua search)

**Mapping sang OCSF 1.9.0** (đối chiếu clone `ocsf-schema` tag 1.9.0, commit 856d462)

| Kỹ thuật / field nguồn | Chỗ trong OCSF 1.9.0 | Ghi chú |
|---|---|---|
| JA3 / JA3S | `tls.ja3_hash`, `tls.ja3s_hash` (kiểu `fingerprint`) | Native |
| JA4 / JA4S / JA4H / JA4L / JA4X / JA4SSH / JA4T / JA4TS / JA4TScan | `ja4_fingerprint_list[]` trên base Network event và trong `evidences` (kiểu `ja4_fingerprint`: `type_id` 1–9, `value`, `section_a..d`) | Native từ 1.3.0. JA4D/JA4N chưa có enum, phải dùng `type_id` 99 Other |
| HASSH client/server | `4007` SSH Activity `client_hassh` / `server_hassh` (`algorithm`, `fingerprint`); thêm `network_endpoint.fingerprints[]` với `algorithm_id` 20 HASSH, 19 NPF (Cisco) | `fingerprints` trên network_endpoint thêm ở 1.8.0 |
| Banner SSH (software_version) | Không có field riêng; 4007 chỉ có `protocol_ver` | → `unmapped` |
| User-Agent | `http_request.user_agent` | Native |
| HTTP `Server` / `X-Powered-By` | `http_response.http_headers[]` (name/value) | Có chỗ, nhưng không có field ngữ nghĩa riêng |
| SNI, cert, SANs | `tls.sni`, `tls.certificate` (`subject`, `issuer`, `fingerprints`, `serial_number`, `is_self_signed`), `tls.sans`, `tls.certificate_chain`; còn có `tls.client_ciphers`, `tls.extension_list` | Native |
| DPI app (App-ID, NBAR2) | `app_name` ("identified by tools such as NBAR or App ID") | Native; category/risk/subcategory → `unmapped` |
| L7 protocol (Zeek `service`, Suricata `app_proto`) | `app_protocol_name` (tên IANA, thêm ở 1.8.0) | Native |
| MAC OUI | `endpoint.mac`, `endpoint.mac_vendor` | `mac_vendor` thêm ở 1.8.0 |
| Kết quả DB (OS, loại, hãng) | `os.name/type_id/version/cpe_name`, `endpoint.type_id` (15 giá trị), `hw_info.vendor_name`, `device.model` | Cây phân cấp và `score` kiểu Fingerbank không có chỗ → `unmapped` |
| DHCP option 12 host_name / option 81 FQDN | `src_endpoint.hostname` / `domain` trong `4004` | Native, nhưng mất ngữ nghĩa "do client tự khai" |
| DHCP option 55 / 60 / 82 | Không có trong `4004` (chỉ `lease_dur`, `is_renewal`, `relay`, `transaction_uid`) | → `unmapped` |
| p0f TCP SYN signature, TTL | Không có field | → `unmapped` |
| mDNS / SSDP / NBNS / LLDP / CDP | Không có class riêng | → `unmapped` |
| Zeek known_services / software.log | Không có class "observed service"; gần nhất là `device.network_interfaces.open_ports`, `5040` query_evidence, `5020` package | Cần quy ước nội bộ |

Nguồn cho bảng: [ja4_fingerprint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/ja4_fingerprint.json), [hassh.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/hassh.json), [fingerprint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/fingerprint.json), [network_endpoint.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/network_endpoint.json), [tls.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/tls.json), [os.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/objects/os.json), [dhcp_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/dhcp_activity.json), [ssh_activity.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/ssh_activity.json), [network.json](https://github.com/ocsf/ocsf-schema/blob/1.9.0/events/network/network.json), [CHANGELOG](https://github.com/ocsf/ocsf-schema/blob/1.9.0/CHANGELOG.md) (#834 JA4 ở 1.3.0; #1560 `fingerprints`, #1575 `mac_vendor`, #1557 `app_protocol_name` ở 1.8.0) (bậc 1, 2026-08-03)

### Nhận định
- **Nhận định:** Có thể xếp hạng bằng chứng mạng thụ động theo độ tin cậy như sau.
  1. Banner/header cleartext có tên và version: Server, SSH banner, DHCP option 60. Dễ giả mạo, nhưng thường đúng với thiết bị không cố ý che giấu.
  2. Fingerprint handshake (JA4/HASSH/JA4S/p0f/option 55) tra DB. Cho ra họ implementation, hiếm khi ra version chính xác.
  3. DPI App-ID/NBAR2. Đáng tin với app, nhưng khi không decrypt thì phụ thuộc SNI/DNS.
  4. Chỉ có port/vai trò responder.

  Mỗi kết luận nên lưu nguồn, DB, version DB và score.
- **Nhận định:** Quy tắc của Zeek known_services đáng sao chép khi suy ra service từ flow OCSF: asset nằm trong phạm vi nội bộ; là responder (`dst_endpoint`, hoặc `initiator_id` ở 1.9.0); TCP đã bắt tay hoặc UDP có phản hồi; `app_protocol_name` do DPI xác nhận được ưu tiên hơn port; dedup theo (asset, port, proto) kèm first/last seen.
- **Nhận định:** JA3 không còn hữu ích để nhận diện trình duyệt Chromium từ 2023. Với client hiện đại nên ưu tiên JA4, có tính đến license FoxIO 1.1: JA4 (TLS client) là BSD, còn JA4S/JA4H/JA4X/JA4SSH/JA4T trong một sản phẩm thương mại cần OEM license nếu chính sản phẩm tự tính fingerprint. Trường hợp chỉ đọc giá trị JA4+ có sẵn trong log OCSF mà nguồn đã sinh ra thì nên hỏi pháp chế; chưa có nguồn nào làm rõ.
- **Nhận định:** Với kho đa tenant, mảng `unmapped` là chỗ chứa nhiều tín hiệu nhận diện thiết bị mạnh nhất: DHCP option 55/60, p0f, mDNS/SSDP. Parser nên chuẩn hoá chúng vào một namespace mở rộng thống nhất (vd profile hoặc extension riêng) để không mất đi khi ghép bằng chứng.
- **Nhận định:** Microsoft dùng DHCP, mDNS, SSDP, LLDP, CDP, NBNS và TCP SYN cho chế độ thụ động, và Fingerbank nhận gần như cùng bộ input. Đây là gợi ý thực tế về bộ tín hiệu tối thiểu để phân loại loại thiết bị.
- **Nhận định:** Khi có ECH/CDN, SNI và IP đích không còn định danh được server thật. Vì vậy chỉ nên coi `tls.sni`/`app_name` là bằng chứng *app usage* phía client (asset → SaaS), không dùng để suy ra service của IP đích ngoài Internet. Sau NAT/CGNAT, mọi fingerprint client gắn với IP public là tập hợp của nhiều host.

### Khoảng trống
- Chưa có con số độc lập về độ chính xác của JA4/JA4+, HASSH hay DHCP fingerprint (Fingerbank) trên mạng thực. Các truy vấn liên quan chỉ ra tài liệu vendor.
- Chưa đọc được bản đầy đủ của Laštovička 2023 (link is.muni.cz trả về HTML thay vì PDF), nên chưa có số chính xác của p0f.
- Chưa có tài liệu kỹ thuật chi tiết về cách Armis, Claroty và Forescout phân loại thiết bị, ngoài tài liệu marketing. Claroty chưa tra.
- Fortinet Application Control chưa tra, do hết ngân sách tool call.
- Danh sách giao thức cụ thể mà runZero traffic sampling parse chưa được docs công bố rõ.
- Không xác minh trang Zeek docs `software.log` (bị 429); đã thay bằng việc đọc thẳng mã nguồn script.
- Chưa có nguồn về tác động định lượng của QUIC/DoH lên độ phủ của App-ID, NBAR2 hay Zeek.

## Truy vấn đã chạy
- Chrome TLS ClientHello extension permutation JA3 fingerprint randomization (standard)
- passive OS fingerprinting accuracy evaluation p0f paper (standard)
- Microsoft Defender for Endpoint device discovery passive standard mode protocols classification (standard)
- "Passive operating system fingerprinting revisited" Laštovička accuracy (extended)
- Palo Alto App-ID how it works application signatures decoders heuristics (standard)
- Fingerbank DHCP fingerprint option 55 device profiling PacketFence (standard)
- Cisco NBAR2 protocol pack application identification DPI statistical ML encrypted traffic (standard)
- Encrypted Client Hello RFC published 2025 SNI visibility network security monitoring impact (extended)
- Forescout device classification passive active methods accuracy cloud Device Cloud (standard)
- Palo Alto Networks block QUIC UDP 443 App-ID visibility recommendation quic application (standard)
- Sivanathan classifying IoT devices smart environments network traffic characteristics accuracy (standard)
- Armis device knowledgebase classification passive traffic analysis how it works (standard)
- Satori passive fingerprinting DHCP TCP HTTP SMB tool xml fingerprints (standard)
- runZero passive discovery protocols fingerprints DHCP mDNS traffic sampling blog (standard)
- passive fingerprinting NAT detection multiple hosts behind single IP TTL user-agent study (standard)
