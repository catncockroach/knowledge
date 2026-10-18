# Network security

> An ninh mạng bảo vệ ba thuộc tính: bí mật (confidentiality), toàn vẹn (integrity), sẵn sàng (availability), bằng mã hóa, xác thực và kiểm soát luồng.

## Tại sao cần biết
Các protocol nền của Internet được thiết kế khi mọi người tin nhau: IP, ARP, DNS, HTTP đều không xác thực. Bảo mật được thêm vào bằng các lớp phía trên, nên biết lớp nào bảo vệ cái gì là điều bắt buộc.

## Khái niệm cốt lõi

### Nền tảng mật mã (mức khái niệm)
- **Mã hóa đối xứng** (AES): cùng một khóa; nhanh, dùng cho dữ liệu. Vấn đề: chia sẻ khóa.
- **Mã hóa bất đối xứng** (RSA, ECC): cặp khóa public/private; dùng để trao đổi khóa và ký.
- **Hàm băm** (SHA-256): "vân tay" của dữ liệu, kiểm tra toàn vẹn.
- **Chữ ký số** và **chứng chỉ (certificate)**: CA tin cậy ký xác nhận "public key này thuộc về domain X".

### TLS
Tầng bảo mật nằm giữa ứng dụng và TCP (HTTPS = HTTP + TLS).
1. Client và server thỏa thuận phiên bản và thuật toán.
2. Server gửi chứng chỉ; client kiểm tra chuỗi tin cậy và tên domain.
3. Hai bên thỏa thuận khóa phiên bằng trao đổi khóa (ECDHE, có *forward secrecy*).
4. Dữ liệu được mã hóa đối xứng bằng khóa phiên.

### Kiểm soát lưu lượng
- **Firewall**: lọc theo luật (IP, port, trạng thái kết nối). *Stateful firewall* theo dõi kết nối. Nguyên tắc: mặc định chặn, chỉ mở thứ cần.
- **VPN**: tạo đường hầm mã hóa qua mạng không tin cậy (IPsec, WireGuard, OpenVPN).
- **Phân đoạn mạng (segmentation)**: VLAN/subnet/DMZ giới hạn phạm vi ảnh hưởng.
- **IDS/IPS**: phát hiện / chặn hành vi tấn công.

### Tấn công thường gặp
| Tấn công | Ý tưởng | Tầng |
|---|---|---|
| ARP spoofing | Giả MAC để chen giữa | L2 |
| IP spoofing | Giả địa chỉ nguồn | L3 |
| SYN flood / DDoS | Làm cạn tài nguyên bằng lượng yêu cầu lớn | L4, L7 |
| DNS spoofing / cache poisoning | Trả IP giả | L7 |
| Man-in-the-middle | Nghe và/hoặc sửa traffic | nhiều tầng |
| Phishing | Lừa người dùng, không phải lỗi protocol | L7 + con người |

### Bảo vệ DNS
**DNSSEC** ký bản ghi để chống giả mạo; **DoT/DoH** mã hóa đường truyền truy vấn.

## Cách hoạt động
Phòng thủ nhiều lớp (defense in depth): mã hóa ở transport (TLS), kiểm soát ở biên (firewall), phân đoạn bên trong, xác thực ở ứng dụng. Không có một lớp nào đủ.

## Ví dụ
```bash
openssl s_client -connect example.com:443 -servername example.com   # xem handshake và chứng chỉ
```

## Hiểu nhầm thường gặp
- **"Có ổ khóa HTTPS nghĩa là trang an toàn"**: nó chỉ nói kết nối được mã hóa tới đúng domain đó, không nói domain đáng tin.
- **"VPN làm bạn ẩn danh hoàn toàn"**: nó chuyển niềm tin từ ISP sang nhà cung cấp VPN.
- **"NAT là firewall"**: NAT vô tình chặn kết nối đi vào nhưng không phải cơ chế bảo mật có chủ đích.

## Liên quan
- [07-transport-layer.md](07-transport-layer.md): TLS chạy trên TCP.
- [08-dns-and-dhcp.md](08-dns-and-dhcp.md): các điểm yếu của DNS.
