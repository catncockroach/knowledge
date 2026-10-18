# Data link layer

> Tầng data link đưa frame từ một nút đến nút kề nó trên cùng một mạng cục bộ, dùng địa chỉ MAC.

## Tại sao cần biết
Đây là tầng của Ethernet, Wi-Fi, switch và VLAN: nơi hầu hết lưu lượng LAN thực sự diễn ra. Nhiều sự cố "mạng nội bộ" (loop, trùng MAC, ARP sai) nằm ở đây.

## Khái niệm cốt lõi

- **Frame**: đơn vị dữ liệu của tầng 2 = header (MAC đích, MAC nguồn, type) + payload + FCS (CRC phát hiện lỗi).
- **MAC address**: địa chỉ 48 bit gắn với card mạng, viết như `00:1A:2B:3C:4D:5E`. Chỉ có ý nghĩa trong một mạng L2, không đi qua router. Địa chỉ `FF:FF:FF:FF:FF:FF` là broadcast.
- **Ethernet (IEEE 802.3)**: chuẩn LAN có dây chủ đạo.
- **Switch**: thiết bị L2 chuyển frame dựa trên MAC.
- **Hub** (cũ): lặp mọi bit ra mọi cổng, nay không còn dùng.
- **Broadcast domain**: tập thiết bị nhận được frame broadcast của nhau. Router chia tách các broadcast domain, switch thì không.
- **Truy cập môi trường dùng chung**:
  - Ethernet cũ: **CSMA/CD** (nghe, phát hiện va chạm). Ethernet full-duplex qua switch không còn va chạm.
  - Wi-Fi: **CSMA/CA** (tránh va chạm), vì không phát hiện va chạm được khi đang phát.
- **VLAN (802.1Q)**: chia một switch vật lý thành nhiều mạng L2 logic, bằng tag 12 bit trong frame.
- **STP (Spanning Tree)**: chặn vòng lặp L2 (frame broadcast quay vòng vô tận sẽ làm sập mạng).

## Cách hoạt động

### Switch học và chuyển frame
1. Frame đến cổng 1 với MAC nguồn `A` → switch ghi vào **MAC table**: `A ↔ cổng 1`.
2. Tra MAC đích: có trong bảng → gửi đúng cổng đó; chưa biết hoặc là broadcast → **flood** ra mọi cổng (trừ cổng nhận).
3. Bản ghi cũ tự hết hạn.

### ARP: từ IP ra MAC
Host biết IP của đích (cùng subnet) nhưng cần MAC để tạo frame. Nó broadcast "ai có IP 192.168.1.10?"; chủ nhân trả lời unicast kèm MAC. Kết quả được lưu trong **ARP cache**. Nếu đích khác subnet, host ARP cho MAC của **default gateway** (router).

```
Host A ──ARP who-has 192.168.1.10? (broadcast)──► cả LAN
Host B ◄─ARP reply: MAC của B (unicast)──────────  B
```

## Ví dụ
Xem ARP cache và MAC trên Linux:
```bash
ip neigh          # bảng ARP
ip link show      # MAC của các interface
```

## Hiểu nhầm thường gặp
- **"MAC address định tuyến được trên Internet"**: không, MAC chỉ dùng trong một link/LAN; mỗi hop sẽ thay MAC nguồn và đích.
- **"Switch và router giống nhau"**: switch nối thiết bị trong cùng mạng (L2); router nối các mạng khác nhau (L3).
- **ARP không có xác thực**, nên có thể bị giả mạo (ARP spoofing).

## Liên quan
- [05-ip-addressing.md](05-ip-addressing.md): địa chỉ logic ở tầng trên.
- [06-routing.md](06-routing.md): cách frame được "thay vỏ" qua từng router.
