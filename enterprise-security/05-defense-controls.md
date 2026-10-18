# Defense controls: endpoint, network, cloud, data

> Biện pháp phòng thủ được đặt theo lớp tài sản: endpoint, mạng, cloud/ứng dụng và dữ liệu; mỗi lớp vừa ngăn chặn vừa tạo telemetry cho phát hiện.

## Tại sao cần biết
Nhìn bản đồ các sản phẩm security (EDR, NDR, WAF, CASB, DLP...) theo lớp tài sản giúp hiểu mỗi cái che vùng nào và để lộ khoảng trống nào.

## Khái niệm cốt lõi

### Endpoint
- **Antivirus (AV)**: chặn mã độc đã biết bằng signature.
- **EDR** (Endpoint Detection & Response): sensor trên máy ghi lại hành vi (tiến trình, file, registry, mạng), phát hiện bất thường, cho phép điều tra và phản ứng (cô lập máy, kill tiến trình).
- **Hardening và patching**: cấu hình an toàn, cập nhật; **application allowlisting**; mã hóa ổ đĩa; quản lý thiết bị (MDM).

### Mạng
- **Firewall / NGFW**, **segmentation** (chia vùng, VLAN, DMZ), **proxy**, **VPN / ZTNA**.
- **IDS/IPS**: phát hiện / chặn xâm nhập theo signature hoặc bất thường.
- **NDR** (Network Detection & Response): phân tích lưu lượng mạng để phát hiện hành vi, mạnh với thiết bị không cài được agent.
- **DNS security, email security** (lọc phishing, SPF/DKIM/DMARC), **WAF** bảo vệ ứng dụng web.
- Chi tiết kỹ thuật nền xem [../internet/10-network-security.md](../internet/10-network-security.md).

### Cloud và ứng dụng
- **Shared responsibility**: nhà cung cấp cloud bảo vệ hạ tầng bên dưới; khách hàng chịu trách nhiệm cấu hình, danh tính, dữ liệu của mình. Phần lớn sự cố cloud đến từ cấu hình sai.
- **CSPM** (phát hiện cấu hình sai), **CWPP** (bảo vệ workload), **CASB** (kiểm soát SaaS).
- **Secure SDLC / DevSecOps**: tích hợp kiểm tra bảo mật vào vòng đời phát triển: SAST, DAST, SCA (phụ thuộc), quét secret, quét IaC và container image.

### Dữ liệu
Phân loại dữ liệu, **mã hóa** khi lưu và khi truyền, **DLP** (chống rò rỉ), backup bất biến và kiểm thử khôi phục (phòng ransomware).

### Con người
Đào tạo nhận thức, mô phỏng phishing, quy trình báo cáo sự cố dễ dùng.

## Cách hoạt động
Mỗi lớp là một **sensor** và một **control**: nó vừa chặn (prevent) vừa sinh log/alert (detect). Dữ liệu đó đổ về điểm tập trung để tương quan:

```
Endpoint(EDR) ─┐
Network(NDR,FW)├─► log/alert ─► SIEM / XDR ─► SOC
Identity(IdP)  │
Cloud/SaaS ────┘
```

## Ví dụ
Một email phishing: email gateway bỏ lọt → người dùng bấm link → proxy/DNS ghi domain lạ → EDR thấy Word sinh PowerShell → IdP ghi đăng nhập từ IP bất thường. Mỗi lớp thấy một mảnh; chỉ khi tương quan mới thấy toàn cảnh.

## Hiểu nhầm thường gặp
- **"EDR thay được SIEM"** (và ngược lại): EDR sâu về endpoint, SIEM rộng khắp mọi nguồn.
- **"Cloud tự động an toàn"**: cấu hình sai do khách là nguyên nhân hàng đầu.
- **"Firewall ở biên là đủ"**: kẻ tấn công đã vào trong, lưu lượng ngang (lateral) không đi qua biên.

## Liên quan
- [04-identity-and-access.md](04-identity-and-access.md): lớp danh tính.
- [07-logging-and-telemetry.md](07-logging-and-telemetry.md): thu telemetry từ các lớp này.
- [13-soar-xdr-and-automation.md](13-soar-xdr-and-automation.md): XDR hợp nhất nhiều sensor.
