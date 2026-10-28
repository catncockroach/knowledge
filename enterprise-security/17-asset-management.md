# Asset management

> Asset management là năng lực liên tục biết tổ chức có những tài sản gì, của ai, quan trọng đến đâu và đang ở trạng thái nào; asset profile là hồ sơ của từng tài sản, gồm những gì được khai báo, những gì quan sát được và những gì nó thường làm.

## Tại sao cần biết
Mọi quyết định bảo mật xoay quanh tài sản: vá gì trước, alert nào xử lý trước, cô lập máy nào, báo cho ai. Vì vậy các framework đặt việc này lên đầu:
- NIST CSF 2.0 mở chức năng Identify bằng category Asset Management (ID.AM), với inventory phần cứng (ID.AM-01) và phần mềm, dịch vụ, hệ thống (ID.AM-02);
- CIS Controls v8 có Control 1 (tài sản doanh nghiệp) và Control 2 (tài sản phần mềm) là hai control đầu tiên.

Không biết mình có gì thì không bảo vệ được.

## Khái niệm cốt lõi
- **Asset** ([01-security-fundamentals.md](01-security-fundamentals.md)) là thứ có giá trị cần bảo vệ. Trong vận hành bảo mật, chủ yếu là **tài sản số quan sát được**: endpoint, server, VM, thiết bị mạng, tài nguyên cloud, container, thiết bị IoT/OT, phần mềm và dịch vụ. Danh tính (user, service account) cũng là tài sản, có vòng quản lý riêng ([04-identity-and-access.md](04-identity-and-access.md)).
- **Vòng đời asset management**: *discover* (phát hiện) → *identify* (định danh, gộp trùng) → *classify* (owner, đơn vị, môi trường, criticality) → *monitor* (trạng thái, thay đổi) → *retire* (thu hồi). Đây là vòng lặp, không phải bảng kê làm một lần.
- **Hai góc nhìn**: **ITAM** quan tâm mua sắm, license, khấu hao; **cyber asset management** quan tâm độ phủ control, lỗ hổng, bề mặt tấn công. Nhóm công cụ gom dữ liệu tài sản từ nhiều nguồn cho mục đích bảo mật được gọi là **CAASM** (Cyber Asset Attack Surface Management).
- **Các cách phát hiện tài sản**:

  | Cách | Thấy được | Bỏ sót |
  |---|---|---|
  | Khai báo (CMDB, ITAM) | owner, mục đích nghiệp vụ | máy không ai khai báo, thông tin cũ |
  | Quét chủ động | máy đang bật, cổng mở | máy tắt lúc quét, mạng không quét tới |
  | Agent (EDR, MDM) | trạng thái chi tiết bên trong máy | máy không cài agent |
  | Tích hợp API (cloud, directory) | tài nguyên cloud, máy trong domain | thứ nằm ngoài hệ thống đó |
  | Thụ động (log, lưu lượng mạng) | mọi máy *thực sự hoạt động* | máy im lặng, chi tiết bên trong máy |

  Không cách nào đủ một mình. CIS Control 1 đưa cả quét chủ động, DHCP log và phát hiện thụ động vào các safeguard của mình.
- **Inventory và profile**: *inventory* là danh sách "có gì"; *profile* là hồ sơ đầy đủ của một tài sản, có lịch sử.
- **Ba lớp của asset profile**:
  - *Khai báo*: nó **nên** là gì: owner, dịch vụ nghiệp vụ, môi trường, criticality. Do con người nhập, dễ cũ.
  - *Quan sát*: nó **đang** là gì: OS, IP, phần mềm, cổng mở, lỗ hổng, có agent hay không, lần cuối thấy.
  - *Hành vi*: nó **thường làm** gì: ai đăng nhập, process nào chạy, kết nối tới đâu, giờ hoạt động. Đây là *baseline* để nhận ra bất thường (cùng ý tưởng với UEBA, [08-siem.md](08-siem.md)).

  Độ lệch giữa các lớp là tín hiệu: máy khai báo là web server nhưng chạy công cụ quản trị domain; máy "dev" nhận kết nối từ internet.
- **Định danh tài sản**: một máy có nhiều định danh với độ bền khác nhau.
  - *Định danh mạnh*, ít đổi: agent ID, cloud instance ID, serial, machine UUID.
  - *Định danh yếu*: hostname (trùng, đổi khi cài lại), IP (đổi theo DHCP, bị NAT che), MAC (VM nhân bản, MAC ngẫu nhiên).

  **Entity resolution** là việc xác định nhiều bản ghi từ nhiều nguồn là cùng một tài sản.
- **Thời gian là một chiều của profile**: IP, owner, OS thay đổi theo thời gian. Một sự kiện phải được hiểu theo trạng thái tài sản *tại thời điểm xảy ra*, không theo trạng thái hiện tại.
- **Criticality và risk**: *criticality* là giá trị của tài sản với nghiệp vụ, căn cứ vào dịch vụ nó phục vụ, dữ liệu nó giữ, vai trò hạ tầng (domain controller, PKI, backup là các tài sản "Tier 0") và mức phơi ra ngoài. *Risk* là khả năng tài sản bị tấn công thành công. Domain controller vá đầy đủ: criticality cao, risk thấp.

## Cách hoạt động
```
khai báo (CMDB) ──┐
quét chủ động ────┤
agent (EDR, MDM) ─┼─► entity resolution ─► asset profile ─► vá lỗ hổng, detection, ứng phó
API (cloud, AD) ──┤                        (khai báo + quan sát
log, lưu lượng ───┘                         + hành vi, có lịch sử)
```

## Ví dụ
Hồ sơ của laptop `WS-0412`:
- *Khai báo*: owner `lan.nguyen`, phòng Tài chính, môi trường prod, criticality High (truy cập hệ thống thanh toán).
- *Quan sát*: Windows 11, có EDR, IP `10.20.4.12` trong khung 06:58–14:58.
- *Hành vi*: 97% phiên đăng nhập là `lan.nguyen`, hoạt động 08:00–18:00 ngày thường, kết nối tới mail, ERP, proxy.

Lúc 02:00, `WS-0412` mở kết nối SMB tới 40 máy. Riêng event đó không có gì sai về kỹ thuật, nhưng so với lớp hành vi thì đây là dấu hiệu lateral movement.

## Hiểu nhầm thường gặp
- **"CMDB là inventory"**: CMDB chỉ là lớp khai báo; máy không có trong CMDB thường là máy nguy hiểm nhất.
- **"IP là định danh máy"**: IP là thuộc tính tạm thời; thiếu chiều thời gian sẽ gán sự việc cho nhầm máy.
- **"Criticality do security tự đặt"**: criticality phản ánh giá trị nghiệp vụ, cần chủ sở hữu nghiệp vụ xác nhận.

## Liên quan
- [06-vulnerability-management.md](06-vulnerability-management.md): inventory là tiền đề của quản lý lỗ hổng.
- [03-frameworks-and-governance.md](03-frameworks-and-governance.md): NIST CSF, CIS Controls.
- [18-asset-context-and-enrichment.md](18-asset-context-and-enrichment.md): log nuôi profile và profile làm giàu log.
