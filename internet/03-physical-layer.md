# Physical layer

> Tầng vật lý biến bit thành tín hiệu (điện, ánh sáng, sóng vô tuyến) và truyền chúng qua môi trường.

## Tại sao cần biết
Mọi giới hạn cuối cùng của mạng (tốc độ, khoảng cách, nhiễu) đều bắt nguồn từ vật lý. Chọn sai cáp hoặc sóng sẽ làm hỏng mọi thứ ở trên, dù cấu hình đúng.

## Khái niệm cốt lõi

### Môi trường truyền
| Môi trường | Tín hiệu | Đặc điểm |
|---|---|---|
| Cáp xoắn đôi (UTP, Cat5e/6) | Điện | Rẻ, phổ biến ở LAN, tối đa 100 m cho Ethernet đồng |
| Cáp đồng trục | Điện | Truyền hình cáp, một số mạng truy cập |
| Cáp quang (multi-mode / single-mode) | Ánh sáng | Tốc độ cao, khoảng cách xa, không bị nhiễu điện từ |
| Vô tuyến (Wi-Fi, 4G/5G) | Sóng điện từ | Di động, dùng chung môi trường, dễ nhiễu |

### Tín hiệu và mã hóa
- **Bit** được biểu diễn bằng sự thay đổi của tín hiệu (mức điện áp, cường độ ánh sáng, pha/biên độ sóng): đó là **line coding** hoặc **modulation**.
- **Bandwidth (Hz)** là độ rộng dải tần của kênh; **bit rate** là số bit/s. Hai thứ này liên quan nhưng không giống nhau.
- **Giới hạn Shannon**: dung lượng tối đa của kênh có nhiễu, C = B · log₂(1 + SNR). Tăng dải tần hoặc tăng tỷ lệ tín hiệu/nhiễu thì mới tăng được dung lượng.

### Suy hao và nhiễu
- **Attenuation**: tín hiệu yếu dần theo khoảng cách → cần bộ lặp (repeater) hoặc cáp quang.
- **Noise / interference**: nhiễu điện từ, crosstalk giữa các đôi dây (xoắn đôi dây giúp triệt tiêu).

### Truyền một chiều và hai chiều
- **Simplex**: một chiều. **Half-duplex**: hai chiều luân phiên (Wi-Fi). **Full-duplex**: hai chiều đồng thời (Ethernet switch hiện đại).

### Wi-Fi ở mức nền
Wi-Fi (IEEE 802.11) dùng dải 2,4 GHz, 5 GHz (và 6 GHz với các chuẩn mới). Dải thấp đi xa, xuyên tường tốt nhưng ít kênh, dễ nhiễu; dải cao nhanh hơn nhưng tầm ngắn. Môi trường vô tuyến là *dùng chung*, nên cần cơ chế tránh va chạm (xem tầng data link).

## Cách hoạt động
```
bit: 1 0 1 1 0
        ↓ line coding / modulation
tín hiệu: ‾\_/‾‾\_   ──(cáp, sợi quang, sóng)──►  giải mã ngược lại thành bit
```
Bên nhận lấy mẫu tín hiệu tại các thời điểm đồng bộ để khôi phục bit, nên cần cơ chế đồng bộ đồng hồ (clock).

## Ví dụ
Ethernet 1000BASE-T chạy 1 Gbit/s trên cáp Cat5e/Cat6 dài tối đa 100 m dùng cả 4 đôi dây ở chế độ full-duplex. Muốn nối hai tòa nhà cách nhau vài km, dùng cáp quang single-mode.

## Hiểu nhầm thường gặp
- **"Wi-Fi 'nhanh X Gbit/s' là tốc độ thực"**: đó là tốc độ lý thuyết của giao thức; thực tế thấp hơn nhiều do nhiễu, khoảng cách và dùng chung.
- **"Cáp dài hơn chút cũng được"**: vượt giới hạn khoảng cách làm tín hiệu suy hao và lỗi bit tăng.

## Liên quan
- [04-data-link-layer.md](04-data-link-layer.md): tầng dùng các bit này để tạo frame.
