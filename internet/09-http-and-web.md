# HTTP và Web

> HTTP là protocol request–response mà Web chạy trên đó; client gửi yêu cầu cho một tài nguyên (URL), server trả về phản hồi.

## Tại sao cần biết
Hầu hết ứng dụng và API ngày nay nói HTTP. Hiểu nó cho thấy hiệu năng web đến từ đâu (số lần round-trip, cache, kết nối tái sử dụng) và là cơ sở để hiểu REST, proxy, CDN, load balancer.

## Khái niệm cốt lõi

- **URL**: `https://example.com:443/path?q=1#frag`: scheme, host, port, path, query, fragment (fragment chỉ ở client).
- **Request**: dòng yêu cầu (`GET /path HTTP/1.1`) + header + body (tuỳ chọn).
- **Response**: status line + header + body.
- **Method**: `GET` (đọc), `POST` (tạo/gửi), `PUT` (thay thế), `PATCH` (sửa một phần), `DELETE`. `GET`, `PUT`, `DELETE` là **idempotent** (lặp lại cho cùng kết quả); `GET` còn là **safe** (không đổi trạng thái).
- **Status code**: `2xx` thành công (200, 201, 204), `3xx` chuyển hướng (301, 302, 304), `4xx` lỗi client (400, 401, 403, 404, 429), `5xx` lỗi server (500, 502, 503).
- **Header quan trọng**: `Host`, `Content-Type`, `Content-Length`, `Authorization`, `Cache-Control`, `ETag`, `Cookie`/`Set-Cookie`, `User-Agent`.
- **Stateless**: mỗi request độc lập; trạng thái phiên được giữ bằng cookie/token.
- **Cookie**: server gửi `Set-Cookie`, client gửi lại ở các request sau.
- **Caching**: `Cache-Control` và `ETag`/`If-None-Match` cho phép dùng lại phản hồi; `304 Not Modified` tránh tải lại body.

### Các phiên bản
| Phiên bản | Điểm chính |
|---|---|
| HTTP/1.1 | Văn bản, kết nối giữ lâu (keep-alive), bị nghẽn đầu hàng đợi (head-of-line) |
| HTTP/2 | Nhị phân, ghép nhiều luồng trên một kết nối TCP |
| HTTP/3 | Chạy trên QUIC (UDP), tránh head-of-line blocking ở tầng transport |

### HTTPS
HTTP bên trong kênh TLS (cổng 443): mã hóa, toàn vẹn, xác thực server (xem [10-network-security.md](10-network-security.md)).

### Các thành phần trung gian
- **Proxy**: đại diện client. **Reverse proxy / load balancer**: đại diện server, phân tải. **CDN**: bản sao nội dung đặt gần người dùng.

## Cách hoạt động
Để tải `https://example.com/`: DNS tra IP → TCP handshake → TLS handshake → gửi `GET /` → nhận phản hồi HTML → trình duyệt tải thêm tài nguyên phụ (CSS, JS, ảnh), tái dùng kết nối.

```
GET /index.html HTTP/1.1
Host: example.com
Accept: text/html

HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 1256
...
```

## Ví dụ
```bash
curl -v https://example.com/        # xem request/response, handshake TLS
curl -I https://example.com/        # chỉ lấy header
```

## Hiểu nhầm thường gặp
- **"POST an toàn hơn GET"**: cả hai đều lộ nếu không có HTTPS; khác nhau ở ngữ nghĩa, không phải bảo mật.
- **"401 và 403 như nhau"**: 401 = chưa xác thực; 403 = đã biết bạn là ai nhưng không được phép.
- **"HTTP lưu phiên"**: HTTP không có phiên; cookie/token mới tạo cảm giác phiên.

## Liên quan
- [07-transport-layer.md](07-transport-layer.md): TCP/QUIC bên dưới HTTP.
- [08-dns-and-dhcp.md](08-dns-and-dhcp.md): bước tra tên trước khi gửi request.
