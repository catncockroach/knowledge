# Transport layer: TCP và UDP

> Tầng transport đưa dữ liệu giữa hai tiến trình (không chỉ hai máy), nhờ port; TCP thêm độ tin cậy, UDP thì không.

## Tại sao cần biết
IP chỉ "cố gắng hết sức" (best effort): gói có thể mất, trùng, sai thứ tự. Transport là nơi quyết định ứng dụng nhận dữ liệu tin cậy hay nhanh, và là nơi kiểm soát tắc nghẽn của cả Internet.

## Khái niệm cốt lõi

- **Port** (16 bit, 0–65535): định danh dịch vụ trên một máy. Well-known: 0–1023 (80 HTTP, 443 HTTPS, 22 SSH, 53 DNS). Một kết nối được xác định bởi **5-tuple**: (protocol, IP nguồn, port nguồn, IP đích, port đích).
- **Multiplexing/demultiplexing**: nhiều ứng dụng dùng chung một IP, transport dùng port để chia dữ liệu đúng ứng dụng.
- **Socket**: giao diện lập trình để ứng dụng dùng transport.

### UDP
- Không kết nối, không bảo đảm, header chỉ 8 byte (port nguồn, port đích, độ dài, checksum).
- Dùng khi cần nhanh, chấp nhận mất gói hoặc tự xử lý: DNS, streaming/gọi video, game, QUIC.

### TCP
Kết nối hướng luồng byte, tin cậy, đúng thứ tự.
- **3-way handshake** thiết lập kết nối: `SYN` → `SYN-ACK` → `ACK`.
- **Sequence number & ACK**: đánh số byte, bên nhận xác nhận; mất gói thì **retransmit** (hết timeout hoặc nhận nhiều ACK trùng).
- **Flow control**: bên nhận báo **window** (còn nhận được bao nhiêu), để người gửi không làm tràn bộ đệm.
- **Congestion control**: người gửi tự giảm tốc khi mạng tắc. Cơ bản: *slow start* (tăng gấp đôi mỗi RTT) rồi *congestion avoidance* (tăng tuyến tính); khi mất gói thì giảm cửa sổ (AIMD).
- **Đóng kết nối**: trao đổi `FIN`/`ACK` mỗi chiều; trạng thái `TIME_WAIT` giữ lại một lúc để dọn gói muộn.

## Cách hoạt động

```
Client                 Server
  │──── SYN seq=x ─────────►│
  │◄─── SYN-ACK seq=y,ack=x+1│
  │──── ACK ack=y+1 ───────►│
  │═══════ dữ liệu ═════════│
  │──── FIN ───────────────►│ ... (đóng 2 chiều)
```

Handshake tốn 1 RTT trước khi gửi dữ liệu; vì vậy kết nối mới tốn kém và các giao thức hiện đại cố gắng tái sử dụng kết nối.

## Ví dụ
```bash
ss -tn           # các kết nối TCP và trạng thái (ESTAB, TIME-WAIT, ...)
nc -zv host 443  # thử mở kết nối TCP tới host:443
```

## Hiểu nhầm thường gặp
- **"TCP nhanh hơn/chậm hơn UDP"**: TCP có thêm chi phí để bảo đảm; không phải lúc nào cũng cần.
- **"TCP đảm bảo dữ liệu đến"**: nó đảm bảo đúng thứ tự và phát hiện lỗi, nhưng nếu mạng đứt thì kết nối vẫn fail; ứng dụng phải xử lý.
- **TCP không giữ ranh giới message**: là luồng byte, một `send` có thể thành nhiều `recv` và ngược lại.

## Liên quan
- [05-ip-addressing.md](05-ip-addressing.md): IP đích + port đích xác định dịch vụ.
- [09-http-and-web.md](09-http-and-web.md): HTTP chạy trên TCP (HTTP/3 trên QUIC/UDP).
- [10-network-security.md](10-network-security.md): TLS bảo vệ luồng TCP.
