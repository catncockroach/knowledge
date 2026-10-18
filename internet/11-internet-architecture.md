# Internet architecture

> Internet là mạng của hàng chục nghìn mạng tự trị (AS), nối nhau bằng hợp đồng thương mại và trao đổi route qua BGP.

## Tại sao cần biết
Nhìn lại bức tranh lớn: packet của bạn đi qua ai, ai trả tiền cho ai, vì sao một sự cố ở nhà mạng này có thể làm gián đoạn dịch vụ ở nơi khác (ví dụ cấu hình BGP sai).

## Khái niệm cốt lõi

- **Access network**: đường từ nhà/tổ chức đến ISP (cáp quang FTTH, cáp đồng DSL, mạng di động).
- **ISP phân tầng**:
  - **Tier 1**: mạng lớn, kết nối với nhau ngang hàng mà không phải trả tiền *transit* cho ai.
  - **Tier 2/3, ISP khu vực**: mua *transit* từ mạng lớn hơn và/hoặc *peering* với nhau.
- **Quan hệ giữa các AS**:
  - *Customer–provider (transit)*: khách trả tiền cho nhà cung cấp để tới toàn Internet.
  - *Peer–peer (peering)*: hai mạng trao đổi traffic của khách hàng của nhau, thường không tính phí.
- **IXP** (Internet Exchange Point): nơi nhiều mạng đặt thiết bị để peering, giảm chi phí và độ trễ.
- **BGP**: protocol các AS dùng để quảng bá "tôi đến được prefix này qua đường này". Mỗi AS chọn route theo chính sách (ưu tiên khách hàng > peer > transit trả tiền), không phải theo hiệu năng.
- **CDN & data center**: nội dung được đặt gần người dùng; các công ty lớn tự dựng mạng backbone riêng, peering trực tiếp với ISP.
- **Quản trị tài nguyên**: **IANA** và các **RIR** (như APNIC cho châu Á–Thái Bình Dương) phân phối dải IP và số ASN; **ICANN** điều phối hệ thống tên miền.
- **Chuẩn hóa**: **IETF** viết RFC (quy trình "rough consensus"); IEEE định nghĩa chuẩn L1–L2 (Ethernet, Wi-Fi).

## Cách hoạt động
```
Người dùng ── ISP A ──(transit)── Backbone ──(peering)── ISP B ── Server
                 └────────── IXP (peering) ──────────┘
```
Mỗi AS quảng bá prefix của mình qua BGP; các AS khác học đường đi, lọc theo chính sách, rồi chọn route tốt nhất để đưa vào bảng chuyển tiếp.

## Ví dụ
Một sự cố BGP thường thấy: một AS vô tình quảng bá prefix không thuộc về mình (*route leak* hoặc *hijack*) và hút traffic đi nhầm đường; vì BGP vốn dựa trên sự tin cậy, cần các cơ chế như RPKI để xác thực nguồn gốc prefix.

## Hiểu nhầm thường gặp
- **"Internet có một người điều hành"**: không, nó là sự phối hợp phân tán của các bên độc lập.
- **"Đường ngắn nhất về địa lý là đường đi"**: đường đi do hợp đồng và chính sách quyết định.
- **"Cloud nằm ngoài Internet"**: cloud là hạ tầng nằm trong và peering với Internet.

## Liên quan
- [06-routing.md](06-routing.md): cơ chế routing bên trong và giữa các AS.
- [10-network-security.md](10-network-security.md): rủi ro của các protocol dựa trên sự tin cậy.
