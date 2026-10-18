# Routing và forwarding

> Router chuyển packet từng bước (hop-by-hop) về phía đích dựa trên routing table; routing protocol giúp các router tự xây bảng đó.

## Tại sao cần biết
Routing là thứ biến vô số mạng riêng lẻ thành một Internet. Hiểu nó là hiểu vì sao packet đi đường này, vì sao có sự cố "không tới được", và `traceroute` cho thấy gì.

## Khái niệm cốt lõi

- **Forwarding**: hành động cục bộ: nhận packet, tra bảng, đẩy ra cổng phù hợp.
- **Routing**: quá trình toàn cục: xác định bảng đó chứa gì.
- **Routing table**: danh sách `prefix → next hop / interface`. Router chọn bản ghi có **longest prefix match** (prefix khớp dài nhất, cụ thể nhất).
- **Default route** `0.0.0.0/0`: khớp mọi thứ, dùng khi không có bản ghi cụ thể hơn.
- **Static routing**: quản trị viên tự khai báo. **Dynamic routing**: router trao đổi thông tin để tự học.
- **TTL** (Time To Live, trường trong header IP): giảm 1 mỗi hop; về 0 thì bị hủy. Chặn packet quay vòng vô tận.
- **ICMP**: protocol báo lỗi/chẩn đoán đi kèm IP (echo của `ping`, "TTL exceeded", "destination unreachable").

### Phân loại routing protocol
| Loại | Ý tưởng | Ví dụ |
|---|---|---|
| Distance-vector | Mỗi router báo cho hàng xóm "tôi đến X mất bao nhiêu" | RIP |
| Link-state | Mỗi router biết cả bản đồ, tự tính đường ngắn nhất (Dijkstra) | OSPF, IS-IS |
| Path-vector | Trao đổi cả đường đi (danh sách AS) kèm chính sách | BGP |

- **IGP** (trong một tổ chức: OSPF, IS-IS) và **EGP** (giữa các tổ chức: BGP).
- **Autonomous System (AS)**: một cụm mạng dưới cùng chính sách định tuyến, có số hiệu ASN.

## Cách hoạt động

1. Host gửi packet cho default gateway (frame L2 mang MAC của gateway, packet L3 mang IP của đích cuối).
2. Router gỡ frame, đọc IP đích, tra routing table (longest prefix match), giảm TTL, tính lại checksum header.
3. Router xác định next hop, ARP lấy MAC next hop, đóng frame mới và gửi đi.
4. Lặp lại đến khi tới mạng của đích.

```
A ──► R1 ──► R2 ──► R3 ──► B
IP:  A→B không đổi (trừ NAT)
MAC: đổi ở mỗi hop
```

## Ví dụ
```bash
ip route          # xem routing table Linux
# default via 192.168.1.1 dev eth0
# 192.168.1.0/24 dev eth0 scope link
```
Đích `192.168.1.5` khớp `/24` → gửi trực tiếp; đích `1.1.1.1` chỉ khớp default → gửi tới `192.168.1.1`.

## Hiểu nhầm thường gặp
- **"Router biết toàn bộ đường đi"**: nó chỉ biết next hop; mỗi router quyết định độc lập.
- **"Đường đi đến và đi về giống nhau"**: không nhất thiết (asymmetric routing).
- **BGP chọn đường ngắn nhất**: BGP chọn theo policy (hợp đồng, chi phí), không phải tốc độ.

## Liên quan
- [05-ip-addressing.md](05-ip-addressing.md): prefix và CIDR dùng trong routing.
- [11-internet-architecture.md](11-internet-architecture.md): BGP nối các AS thành Internet.
- [12-troubleshooting-tools.md](12-troubleshooting-tools.md): `traceroute` dùng TTL.
