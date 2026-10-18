# Internet (Computer networking)

Kiến thức cơ sở cốt lõi của mạng máy tính trong công nghệ thông tin: dữ liệu đi từ ứng dụng này sang ứng dụng khác thế nào, qua những tầng nào, nhờ những protocol nào. Đây là nền tảng cho backend, DevOps, cloud và security.

## Phạm vi
- **Có:** mô hình phân tầng, từ physical đến application, địa chỉ và định tuyến, TCP/UDP, DNS/DHCP, HTTP/TLS, bức tranh kiến trúc Internet, công cụ chẩn đoán.
- **Không:** cấu hình sâu theo hãng thiết bị, lập trình socket, mạng di động/viễn thông chi tiết, SDN/cloud networking.
- **Đối tượng:** người biết CNTT cơ bản, học lại mạng từ gốc.

## Bản đồ tư duy

```
Application  ── HTTP, DNS, DHCP ──────── 08, 09        ┐
Transport    ── TCP, UDP, port ───────── 07            │ 10: bảo mật (TLS, firewall)
Network      ── IP, routing, NAT ─────── 05, 06        │ cắt ngang các tầng
Data link    ── Ethernet, ARP, switch ── 04            ┘
Physical     ── cáp, sóng, tín hiệu ──── 03
Khung nhìn: 01 nền tảng · 02 mô hình tầng · 11 kiến trúc Internet · 12 công cụ
```

## Các file
Đọc theo thứ tự:

| File | Nội dung |
|---|---|
| [01-network-fundamentals.md](01-network-fundamentals.md) | Mạng là gì: host, link, protocol, LAN/WAN, packet switching, và 4 loại độ trễ, băng thông, throughput. |
| [02-layered-models.md](02-layered-models.md) | Mô hình OSI 7 tầng và TCP/IP 4 tầng, đơn vị dữ liệu mỗi tầng, cơ chế encapsulation. |
| [03-physical-layer.md](03-physical-layer.md) | Cách bit thành tín hiệu: cáp đồng, cáp quang, vô tuyến, suy hao, nhiễu, giới hạn Shannon. |
| [04-data-link-layer.md](04-data-link-layer.md) | Frame, địa chỉ MAC, Ethernet, cách switch học MAC, ARP, VLAN, truy cập môi trường dùng chung. |
| [05-ip-addressing.md](05-ip-addressing.md) | IPv4/IPv6, CIDR và subnetting, địa chỉ private, gateway, NAT. |
| [06-routing.md](06-routing.md) | Forwarding và routing, routing table, longest prefix match, TTL/ICMP, distance-vector, link-state, BGP. |
| [07-transport-layer.md](07-transport-layer.md) | Port và socket, UDP, TCP: handshake, tin cậy, flow control, congestion control. |
| [08-dns-and-dhcp.md](08-dns-and-dhcp.md) | DNS phân giải tên (cấp bậc, bản ghi, cache) và DHCP cấp cấu hình tự động. |
| [09-http-and-web.md](09-http-and-web.md) | HTTP: request/response, method, status code, cookie, cache, HTTP/1.1–3, proxy và CDN. |
| [10-network-security.md](10-network-security.md) | Mã hóa và chứng chỉ, TLS, firewall, VPN, phân đoạn mạng, các kiểu tấn công thường gặp theo tầng. |
| [11-internet-architecture.md](11-internet-architecture.md) | Internet như mạng của các AS: ISP, transit/peering, IXP, BGP, CDN, các tổ chức quản trị. |
| [12-troubleshooting-tools.md](12-troubleshooting-tools.md) | Quy trình chẩn đoán theo tầng và các công cụ: ping, traceroute, dig, ss, curl, tcpdump. |

## Thuật ngữ nền
- **Packet / frame / segment**: đơn vị dữ liệu ở từng tầng (xem 02).
- **Hop**: một bước nhảy qua một thiết bị L3.
- **Gateway**: router mà host gửi tới khi đích ở ngoài subnet.
- **RTT**: thời gian đi và về của một gói.
- **AS (Autonomous System)**: một mạng dưới chính sách định tuyến chung.
