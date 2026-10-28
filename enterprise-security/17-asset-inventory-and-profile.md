# Asset inventory and profile

> Asset profile là hồ sơ hợp nhất của một tài sản (máy, VM, thiết bị mạng, workload cloud): định danh, thông tin kỹ thuật, ngữ cảnh nghiệp vụ và tư thế bảo mật, được ghép từ nhiều nguồn inventory và có lịch sử theo thời gian.

## Tại sao cần biết
Một alert "PowerShell mã hóa chạy trên `10.20.4.12`" chưa trả lời được câu hỏi analyst cần: máy đó là gì, của ai, quan trọng đến đâu, có EDR không, đang có lỗ hổng gì. Câu trả lời nằm rải rác ở CMDB, Active Directory, EDR console, MDM, cloud và máy quét lỗ hổng, mỗi nơi định danh máy theo một kiểu. Asset profile gom chúng lại để bước enrich ([18-asset-enrichment-in-ocsf.md](18-asset-enrichment-in-ocsf.md)) chỉ cần tra một chỗ. Đây cũng là nền của quản lý lỗ hổng ([06-vulnerability-management.md](06-vulnerability-management.md)): không biết có gì thì không bảo vệ được.

## Khái niệm cốt lõi

### Nội dung một asset profile
| Nhóm | Thuộc tính điển hình |
|---|---|
| Định danh | hostname, FQDN, IP, MAC, EDR agent ID, cloud instance ID, serial number, AD object |
| Kỹ thuật | loại máy (server/laptop/VM), OS và phiên bản, vị trí, subnet/VLAN/VPC, zone mạng |
| Nghiệp vụ | owner (người chịu trách nhiệm), đơn vị/bộ phận, dịch vụ nghiệp vụ, môi trường (prod/staging/dev), **criticality** |
| Tư thế bảo mật | managed hay không, compliant hay không, có agent EDR, số lỗ hổng mở, phơi ra internet, risk level |
| Vòng đời | first seen, last seen, trạng thái (đang dùng, đã thu hồi) |

### Nguồn và "nguồn chuẩn" cho từng thuộc tính
Không nguồn nào đúng về mọi thứ. Mỗi thuộc tính chọn một *source of truth*, các nguồn khác là dự phòng:

| Nguồn | Mạnh ở |
|---|---|
| CMDB / ITAM | owner, dịch vụ nghiệp vụ, môi trường, criticality |
| Active Directory / Entra ID / LDAP | tên máy trong domain, OU, nhóm, trạng thái tài khoản máy |
| EDR inventory | agent ID, OS, user đăng nhập gần nhất, last seen, trạng thái agent |
| MDM | managed, compliant, thiết bị cá nhân hay công ty |
| Cloud inventory API | instance ID, tag, region, VPC, account/subscription |
| Vulnerability scanner | lỗ hổng mở, cổng mở, dịch vụ chạy |
| DHCP / IPAM / NAC | IP ↔ MAC ↔ hostname theo thời gian |

### Entity resolution: biết hai bản ghi là cùng một máy
- **Khóa mạnh**, ít đổi và gần như duy nhất: EDR agent ID, cloud instance ID, serial number, OS machine UUID.
- **Khóa yếu**, dùng để nối khi thiếu khóa mạnh:
  - hostname: trùng giữa các domain, đổi khi cài lại máy;
  - IP: đổi theo DHCP, bị NAT/VPN che;
  - MAC: VM nhân bản, điện thoại dùng MAC ngẫu nhiên.
- **Quy tắc ghép**: nối theo khóa mạnh trước, khóa yếu sau và ghi độ tin cậy của mỗi lần ghép. Khi các nguồn mâu thuẫn, lấy theo nguồn chuẩn của thuộc tính đó, nếu ngang nhau thì lấy nguồn có `last_seen` mới hơn.

### Thời gian là một chiều của profile
IP `10.20.4.12` thuộc `WS-0412` lúc 9 giờ nhưng có thể thuộc máy khác lúc 15 giờ. Ánh xạ IP → máy phải lưu theo khoảng hiệu lực (`valid_from`, `valid_to`), lấy từ DHCP lease hoặc từ log đăng nhập/agent. Khi enrich, tra theo **thời điểm của event**, không theo trạng thái hiện tại. Điều này quan trọng nhất khi điều tra lại sự cố cũ.

### Criticality
Mức quan trọng của tài sản với tổ chức, thường 3–5 bậc (Low → Critical). Căn cứ:
- dịch vụ nghiệp vụ mà máy phục vụ;
- độ nhạy của dữ liệu trên máy;
- vai trò hạ tầng: domain controller, PKI, máy chủ backup, máy quản trị là các asset mà chiếm được thì chiếm được cả hệ thống;
- mức phơi ra ngoài.

Criticality nhân với severity của alert để ra mức ưu tiên (xem risk-based alerting trong [08-siem.md](08-siem.md)).

## Cách hoạt động

```
CMDB ─┐
AD ───┤
EDR ──┼─► Thu thập snapshot ─► Chuẩn hóa ─► Entity resolution ─► Asset profile store
MDM ──┤     (định kỳ / API)    (tên field,   (khóa mạnh → yếu,      ├─ bản hiện tại
Cloud ┤                         kiểu OCSF)    nguồn chuẩn, xung đột) ├─ lịch sử IP↔máy theo thời gian
Scan ─┤                                                              └─ danh sách tra cứu (lookup)
DHCP ─┘
```

- Snapshot inventory có thể chuẩn hóa luôn sang OCSF bằng class Discovery: Device Inventory Info (`5001`) cho thông tin máy, Software Inventory Info (`5020`) cho phần mềm, Vulnerability Finding (`2002`) cho lỗ hổng. Khi đó inventory nằm cùng data lake và cùng schema với log sự kiện.
- Profile store xuất ra một bảng tra cứu gọn, đánh index theo các khóa (agent ID, hostname, IP + thời gian) để pipeline enrich tra nhanh.
- Event từ IP hay hostname **không khớp** profile nào là tín hiệu riêng: máy lạ, máy chưa cài EDR, hoặc inventory thiếu.

## Ví dụ
Bốn nguồn nói về cùng một laptop:

| Nguồn | Bản ghi |
|---|---|
| EDR | agent `edr-agent-7f3a`, host `WS-0412`, Windows 11, last seen 07:05, user `lan.nguyen` |
| AD | `CN=WS-0412,OU=Finance,DC=corp,DC=local` |
| CMDB | `WS-0412`, owner `lan.nguyen`, phòng Tài chính, criticality *High* (máy truy cập hệ thống thanh toán) |
| DHCP | `10.20.4.12` ↔ MAC `3c:22:fb:..` ↔ `WS-0412`, lease 06:58–14:58 |

Ghép theo hostname `WS-0412` (EDR, AD, CMDB) và theo hostname + MAC (DHCP). Profile kết quả:

```
asset_id=edr-agent-7f3a  hostname=WS-0412  fqdn=WS-0412.corp.local
type=laptop  os=Windows 11  ou=Finance  owner=lan.nguyen  bu=Tài chính
criticality=High  managed=true  edr=true
ip_history=[10.20.4.12 @ 06:58–14:58]
```

Event lúc 10:00 từ `10.20.4.12` tra ra `WS-0412`; event lúc 16:00 cùng IP thì không, vì lease đã hết.

## Hiểu nhầm thường gặp
- **"CMDB là đủ"**: CMDB thường cũ và thiếu máy; EDR và DHCP cho biết máy *thực sự* đang chạy. Cần đối chiếu, và chính độ lệch giữa các nguồn là một chỉ số chất lượng.
- **"IP là định danh máy"**: IP chỉ là thuộc tính tạm thời; dùng làm khóa mà không có thời gian sẽ gán alert cho nhầm máy.
- **"Criticality do đội security tự đặt"**: criticality phản ánh giá trị nghiệp vụ, phải do chủ sở hữu nghiệp vụ xác nhận; security chỉ đề xuất theo vai trò hạ tầng.
- **"Profile chỉ cần bản hiện tại"**: điều tra sự cố cần trạng thái *lúc xảy ra*: owner, IP, OS khi đó.

## Liên quan
- [01-security-fundamentals.md](01-security-fundamentals.md): khái niệm asset và rủi ro.
- [06-vulnerability-management.md](06-vulnerability-management.md): asset inventory là tiền đề.
- [16-mapping-logs-to-ocsf.md](16-mapping-logs-to-ocsf.md): event đã map chứa các khóa để tra profile.
- [18-asset-enrichment-in-ocsf.md](18-asset-enrichment-in-ocsf.md): gắn profile vào event OCSF.
