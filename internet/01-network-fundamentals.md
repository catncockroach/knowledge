# Network fundamentals

> Mạng máy tính là tập hợp các thiết bị nối với nhau để trao đổi dữ liệu theo những quy tắc chung (protocol).

## Tại sao cần biết
Mọi dịch vụ hiện đại (web, email, cloud, gọi video) đều chạy trên mạng. Hiểu các khái niệm nền (host, packet, băng thông, độ trễ) giúp đọc được mọi chủ đề sau, và giải thích được vì sao một hệ thống "chậm" hay "rớt kết nối".

## Khái niệm cốt lõi

- **Host / end system**: thiết bị đầu cuối (máy tính, điện thoại, server). **Intermediate device**: thiết bị trung gian chuyển dữ liệu (switch, router).
- **Link**: đường nối giữa hai thiết bị (cáp đồng, cáp quang, sóng vô tuyến).
- **Protocol**: tập quy tắc về định dạng và thứ tự thông điệp giữa hai bên (ví dụ HTTP, TCP, IP).
- **Phạm vi mạng**:
  - **LAN**: mạng cục bộ (nhà, văn phòng), tốc độ cao, do một tổ chức quản lý.
  - **WAN**: mạng diện rộng nối nhiều LAN qua nhà cung cấp dịch vụ.
  - **Internet**: mạng của các mạng (*inter-network*), nối hàng chục nghìn mạng độc lập bằng bộ giao thức TCP/IP.
- **Mô hình giao tiếp**: *client-server* (client yêu cầu, server phục vụ) và *peer-to-peer* (các bên ngang hàng).
- **Topology**: cách nối các nút, ví dụ star (hình sao, phổ biến nhất ở LAN), bus, ring, mesh.

### Chuyển mạch (switching)
| | Circuit switching | Packet switching |
|---|---|---|
| Cách làm | Dành riêng một đường cho cả cuộc gọi | Chia dữ liệu thành *packet*, mỗi packet đi độc lập |
| Hiệu quả | Lãng phí khi im lặng | Dùng chung đường truyền (statistical multiplexing) |
| Ví dụ | Điện thoại truyền thống | Internet |

Internet dùng packet switching vì lưu lượng dữ liệu thường bùng phát rồi nghỉ, chia sẻ đường truyền hiệu quả hơn nhiều.

### Hiệu năng
- **Bandwidth**: dung lượng tối đa của link (bit/s).
- **Throughput**: tốc độ thực tế đạt được, luôn ≤ bandwidth.
- **Latency**: thời gian một bit đi từ nguồn đến đích. Gồm 4 thành phần:
  1. *Processing delay*: thiết bị đọc header, quyết định chuyển đi đâu.
  2. *Queuing delay*: chờ trong hàng đợi khi link bận.
  3. *Transmission delay* = kích thước gói / bandwidth.
  4. *Propagation delay* = khoảng cách / tốc độ lan truyền (~2×10⁸ m/s trong cáp).
- **RTT** (round-trip time): thời gian đi và về. **Packet loss**: tỷ lệ gói bị rơi (thường do hàng đợi đầy). **Jitter**: độ dao động của latency.

## Cách hoạt động
Dữ liệu từ ứng dụng được cắt thành packet, mỗi packet mang header chứa địa chỉ đích. Thiết bị trung gian đọc header và chuyển tiếp từng packet theo kiểu **store-and-forward** (nhận trọn gói rồi mới gửi đi). Đầu cuối ghép các packet lại.

```
Host A --link-- Switch --link-- Router --link-- ... --link-- Server B
```

## Ví dụ
Gửi file 1 MB (8×10⁶ bit) qua link 100 Mbit/s: transmission delay = 8×10⁶ / 10⁸ = 0,08 s. Link dài 3.000 km: propagation delay ≈ 3×10⁶ / 2×10⁸ = 15 ms. Với file nhỏ, propagation chiếm ưu thế; với file lớn, bandwidth quyết định.

## Hiểu nhầm thường gặp
- **"Băng thông cao thì mạng nhanh"**: băng thông là độ rộng ống, latency là độ dài ống. Tải trang web nhỏ phụ thuộc latency nhiều hơn bandwidth.
- **Internet = Web**: Web (HTTP) chỉ là một ứng dụng chạy trên Internet, cùng email, SSH, DNS, ...
- **Mbps và MBps**: 1 byte = 8 bit; 100 Mbit/s ≈ 12,5 MB/s.

## Liên quan
- [02-layered-models.md](02-layered-models.md): cách tổ chức các protocol thành tầng.
