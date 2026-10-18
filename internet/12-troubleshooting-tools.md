# Troubleshooting tools

> Cách tiếp cận có hệ thống để chẩn đoán lỗi mạng: đi từng tầng, dùng đúng công cụ cho tầng đó.

## Tại sao cần biết
Kiến thức mạng chỉ thật sự "vào đầu" khi bạn dùng nó để tìm lỗi. Các công cụ dưới đây cho bạn quan sát chính các khái niệm đã học: ARP, route, TTL, DNS, TCP.

## Khái niệm cốt lõi

### Phương pháp: đi từ dưới lên (hoặc chia đôi)
1. **L1**: dây cắm chưa? đèn link? sóng Wi-Fi đủ mạnh?
2. **L2**: interface up? có MAC hàng xóm trong ARP table?
3. **L3**: có IP đúng subnet? ping được gateway? ping được IP ngoài (ví dụ `1.1.1.1`)?
4. **DNS**: ping được IP nhưng không ping được tên → lỗi DNS.
5. **L4**: cổng có mở không? bị firewall chặn?
6. **L7**: ứng dụng/HTTP trả gì?

Mỗi bước loại bỏ một nhóm nguyên nhân.

### Công cụ
| Công cụ | Mục đích | Ví dụ |
|---|---|---|
| `ip addr`, `ip link` | Địa chỉ và trạng thái interface | `ip -br addr` |
| `ip route` | Routing table, gateway | `ip route get 8.8.8.8` |
| `ip neigh` | ARP cache | |
| `ping` | Kiểm tra tới được (ICMP echo), đo RTT và mất gói | `ping -c 4 1.1.1.1` |
| `traceroute` / `mtr` | Liệt kê các hop (dùng TTL tăng dần) | `mtr example.com` |
| `dig` / `nslookup` | Truy vấn DNS | `dig example.com` |
| `ss` | Socket, cổng đang lắng nghe, trạng thái TCP | `ss -tulpn` |
| `nc` | Thử mở kết nối TCP/UDP | `nc -zv host 443` |
| `curl` | Thử HTTP(S) và xem handshake | `curl -v https://example.com` |
| `tcpdump`, Wireshark | Bắt và đọc packet | `tcpdump -i eth0 port 53` |
| `openssl s_client` | Kiểm tra TLS và chứng chỉ | |

## Cách hoạt động
`traceroute` gửi packet với TTL=1, 2, 3, ...; mỗi router làm TTL về 0 sẽ trả ICMP "TTL exceeded", nhờ đó lộ ra từng hop và RTT đến nó.

`tcpdump`/Wireshark đặt card mạng vào chế độ bắt toàn bộ frame đi qua, cho thấy từng header theo tầng: nơi tốt nhất để nhìn thấy handshake TCP, truy vấn DNS hay ARP bằng mắt.

## Ví dụ
"Truy cập được `1.1.1.1` nhưng `example.com` thì không":
```bash
ping -c 2 1.1.1.1        # OK  → L1–L3 ổn
dig example.com          # timeout → DNS có vấn đề
cat /etc/resolv.conf     # kiểm tra DNS server cấu hình
dig @1.1.1.1 example.com # thử resolver khác để xác nhận
```

## Hiểu nhầm thường gặp
- **"Ping không được nghĩa là máy chết"**: nhiều nơi chặn ICMP.
- **`traceroute` hiện `* * *`** không nhất thiết là lỗi: router có thể không trả lời ICMP.
- **Độ trễ cao ở một hop** chưa chắc là nút thắt: router có thể ưu tiên thấp việc trả ICMP nhưng vẫn chuyển tiếp tốt.

## Liên quan
- Toàn bộ các file trước: mỗi công cụ ở đây soi một tầng, xem [02-layered-models.md](02-layered-models.md) để định vị tầng.
