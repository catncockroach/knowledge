# DNS và DHCP

> DNS dịch tên miền thành IP; DHCP tự cấp cấu hình mạng (IP, gateway, DNS) cho host. Cả hai là "keo dính" giúp mạng dùng được mà không cần cấu hình tay.

## Tại sao cần biết
Người dùng nhớ tên, mạng chỉ hiểu IP. Gần như mọi kết nối đều bắt đầu bằng một truy vấn DNS, và hầu hết lỗi "mạng hỏng" thực chất là DNS hỏng. DHCP là lý do cắm máy vào mạng là chạy.

## Khái niệm cốt lõi

### DNS
- **Không gian tên phân cấp**: `www.example.com.` đọc từ phải sang trái: root `.` → TLD `com` → domain `example` → host `www`.
- **Zone**: phần không gian tên do một bên quản lý; được phục vụ bởi **authoritative name server**.
- **Recursive resolver**: máy chủ (của ISP, hoặc 8.8.8.8, 1.1.1.1) thay client đi hỏi các tầng và **cache** kết quả.
- **Bản ghi (resource record)**:
  | Loại | Ý nghĩa |
  |---|---|
  | A / AAAA | Tên → IPv4 / IPv6 |
  | CNAME | Tên là bí danh của tên khác |
  | MX | Máy chủ nhận mail của domain |
  | NS | Name server của zone |
  | TXT | Văn bản tùy ý (SPF, xác minh domain) |
  | PTR | IP → tên (reverse) |
- **TTL**: thời gian bản ghi được phép cache, đánh đổi giữa tốc độ và độ tươi.
- Truy vấn dùng chủ yếu UDP/TCP cổng 53.

### DHCP
Giao thức cấp phát cấu hình động. Server giữ một **pool** địa chỉ và cho **thuê (lease)** một khoảng thời gian cùng gateway, DNS server, mask. Chạy trên UDP (server 67, client 68).

## Cách hoạt động

### Phân giải tên (resolver chưa có cache)
```
Client → Resolver: www.example.com?
Resolver → Root:      "hỏi server của .com"
Resolver → .com TLD:  "hỏi server của example.com"
Resolver → Auth NS:   "www.example.com = 93.184.x.x"
Resolver → Client:    trả lời (và cache theo TTL)
```

### DHCP: DORA
1. **Discover**: client broadcast "ai là DHCP server?"
2. **Offer**: server đề nghị một địa chỉ.
3. **Request**: client chọn và yêu cầu địa chỉ đó.
4. **Acknowledge**: server xác nhận lease.

Client gia hạn lease khi đã dùng khoảng một nửa thời gian thuê.

## Ví dụ
```bash
dig example.com A +short       # hỏi bản ghi A
dig example.com NS             # name server của domain
dig +trace example.com         # đi theo chuỗi root → TLD → authoritative
cat /etc/resolv.conf           # DNS server máy đang dùng
```

## Hiểu nhầm thường gặp
- **"Đổi DNS là có hiệu lực ngay"**: cache theo TTL làm thay đổi lan chậm.
- **"DNS chỉ là tra IP"**: còn dùng cho mail routing, xác thực mail, load balancing, dịch vụ discovery.
- **DNS gốc không mã hóa**, nên truy vấn có thể bị nghe lén hoặc giả mạo (xem DoH/DoT, DNSSEC trong [10-network-security.md](10-network-security.md)).

## Liên quan
- [05-ip-addressing.md](05-ip-addressing.md): thứ DNS trả về và DHCP cấp.
- [09-http-and-web.md](09-http-and-web.md): bước tiếp theo sau khi biết IP.
