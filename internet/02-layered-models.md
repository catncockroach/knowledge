# Layered models: OSI và TCP/IP

> Mạng được chia thành các tầng; mỗi tầng giải quyết một việc và chỉ làm việc với tầng sát nó.

## Tại sao cần biết
Truyền dữ liệu giữa hai máy là bài toán quá lớn để giải một lần. Chia tầng cho phép đổi công nghệ ở một tầng (Wi-Fi thay cáp) mà các tầng khác không cần đổi, và cho mọi người một ngôn ngữ chung ("lỗi ở L2", "load balancer L7").

## Khái niệm cốt lõi

### Mô hình OSI (7 tầng, mô hình tham chiếu)
| # | Tầng | Việc chính | Đơn vị dữ liệu (PDU) | Ví dụ |
|---|---|---|---|---|
| 7 | Application | Giao diện cho ứng dụng | Data | HTTP, DNS, SMTP |
| 6 | Presentation | Định dạng, mã hóa, nén | Data | TLS (một phần), JSON/ASCII |
| 5 | Session | Quản lý phiên | Data | RPC, session |
| 4 | Transport | Truyền giữa tiến trình, độ tin cậy | Segment / Datagram | TCP, UDP |
| 3 | Network | Địa chỉ logic, định tuyến | Packet | IP, ICMP |
| 2 | Data link | Truyền giữa hai nút kề nhau | Frame | Ethernet, Wi-Fi |
| 1 | Physical | Truyền bit qua môi trường | Bit | Cáp, sóng, tín hiệu |

### Mô hình TCP/IP (4 tầng, thực tế đang dùng)
| Tầng TCP/IP | Tương ứng OSI |
|---|---|
| Application | 5–7 |
| Transport | 4 |
| Internet | 3 |
| Link (Network access) | 1–2 |

OSI là mô hình để học và gọi tên; TCP/IP là thứ Internet thực sự chạy. Trong thực tế hay dùng tên tầng theo OSI nhưng cấu trúc theo TCP/IP.

### Nguyên tắc
- **Service**: tầng dưới cung cấp dịch vụ cho tầng trên qua một giao diện.
- **Protocol**: tầng N ở máy A "nói chuyện" với tầng N ở máy B theo protocol của tầng đó.
- **Encapsulation**: mỗi tầng bọc dữ liệu của tầng trên bằng header của mình (tầng 2 còn có trailer).

## Cách hoạt động

```
Gửi (A)                         Nhận (B)
Application   [Data]            Application
Transport     [TCP|Data]        Transport
Network       [IP|TCP|Data]     Network
Data link  [Eth|IP|TCP|Data|FCS]  Data link
Physical      bits ------------> Physical
```

Bên gửi đi từ trên xuống (thêm header), bên nhận đi từ dưới lên (gỡ header: **decapsulation**). Thiết bị trung gian chỉ gỡ đến tầng nó cần: switch đến L2, router đến L3.

## Ví dụ
Bạn mở `https://example.com`: HTTP request (L7) → bọc trong TLS → TCP segment có port đích 443 (L4) → IP packet có IP đích của server (L3) → Ethernet/Wi-Fi frame có MAC của router gần nhất (L2) → bit trên dây hoặc sóng (L1).

## Hiểu nhầm thường gặp
- **"Mọi protocol đều khớp gọn vào một tầng OSI"**: TLS, ARP, MPLS nằm lưng chừng; đừng ép cứng.
- **"Tầng cao dùng địa chỉ giống tầng thấp"**: mỗi tầng có định danh riêng: MAC (L2), IP (L3), port (L4), hostname/URL (L7).

## Liên quan
- [03-physical-layer.md](03-physical-layer.md) → [04-data-link-layer.md](04-data-link-layer.md) → [05-ip-addressing.md](05-ip-addressing.md): đi lần lượt từ tầng thấp lên.
