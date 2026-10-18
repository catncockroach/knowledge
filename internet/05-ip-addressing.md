# IP addressing

> IP cho mỗi interface một địa chỉ logic phân cấp, để packet có thể tìm đường qua nhiều mạng.

## Tại sao cần biết
Địa chỉ IP, subnet và gateway là cấu hình mạng cơ bản nhất; hiểu chúng là điều kiện để thiết kế mạng, đọc routing table và debug "không ping được".

## Khái niệm cốt lõi

### IPv4
- 32 bit, viết dạng 4 octet: `192.168.1.10`. Khoảng 4,3 tỷ địa chỉ, đã cạn.
- Mỗi địa chỉ gồm **phần network** và **phần host**, phân tách bằng **subnet mask** hoặc ký hiệu **CIDR** `/n` (n = số bit network).
  - `192.168.1.10/24` ⇒ mask `255.255.255.0`, network `192.168.1.0`, 8 bit host.
- Với `/n`, số địa chỉ = 2^(32−n); số host dùng được = 2^(32−n) − 2 (trừ địa chỉ *network* và *broadcast*).

### Địa chỉ đặc biệt
| Dải | Ý nghĩa |
|---|---|
| `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` | Private (RFC 1918), không route trên Internet |
| `127.0.0.0/8` | Loopback (`127.0.0.1` = chính máy này) |
| `169.254.0.0/16` | Link-local, tự gán khi không có DHCP |
| `0.0.0.0` | "Không xác định" / mặc định |

### Subnetting
Chia một mạng lớn thành các mạng nhỏ bằng cách mượn bit từ phần host.
`192.168.1.0/24` chia thành hai `/25`: `192.168.1.0/25` (host .1–.126) và `192.168.1.128/25` (host .129–.254).

### Cấp địa chỉ
- **Tĩnh** hoặc **DHCP** (máy xin địa chỉ tự động, xem [08-dns-and-dhcp.md](08-dns-and-dhcp.md)).
- **Default gateway**: router mà host gửi packet đến khi đích nằm ngoài subnet.

### NAT
Router biên dịch địa chỉ private sang một địa chỉ public. **NAPT/PAT** dùng thêm port để nhiều máy chia sẻ một IP public. NAT phát sinh vì IPv4 cạn; nó phá tính end-to-end (máy bên ngoài khó chủ động kết nối vào trong).

### IPv6
- 128 bit, viết hex: `2001:db8::1`. Không cần NAT, mặc định `/64` cho một subnet.
- Không có broadcast (dùng multicast), header đơn giản hơn, có SLAAC (tự cấu hình).

## Cách hoạt động
Host kiểm tra: đích có cùng subnet không? (AND địa chỉ đích với mask rồi so với network của mình.)
- Cùng subnet → gửi trực tiếp (ARP lấy MAC đích).
- Khác subnet → gửi cho default gateway.

## Ví dụ
Host `192.168.1.10/24` gửi tới `192.168.1.77`: cùng `192.168.1.0/24` → ARP trực tiếp. Gửi tới `8.8.8.8`: khác subnet → gửi cho gateway `192.168.1.1`, router đó NAT ra IP public.

## Hiểu nhầm thường gặp
- **"IP là của máy"**: IP gắn với interface và mạng nó đứng, đổi mạng thì đổi IP.
- **"Private IP không ra Internet được"**: ra được nhờ NAT; chỉ là không được route trực tiếp.
- **Quên trừ 2** khi đếm host của subnet IPv4.

## Liên quan
- [04-data-link-layer.md](04-data-link-layer.md): ARP nối IP với MAC.
- [06-routing.md](06-routing.md): packet IP được chuyển đi thế nào.
