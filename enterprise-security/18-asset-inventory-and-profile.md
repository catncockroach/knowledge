# Asset inventory and profile

> Event ghi *một việc xảy ra*; asset inventory và asset profile ghi *một tài sản là gì* trong một khoảng thời gian. Profile không nằm sẵn trong event nào: nó là trạng thái được "gập" (fold) từ rất nhiều event và nguồn khai báo theo định danh của tài sản, lưu thành bảng riêng, rồi nối ngược vào event khi cần.

## Tại sao cần biết
Một alert "PowerShell mã hóa trên `10.20.4.12`" chưa trả lời được câu analyst cần: máy đó là gì, của ai, quan trọng đến đâu, có EDR không. Câu trả lời nằm trong asset profile. Khi mọi log đã chuẩn hóa về OCSF ([15](15-security-data-normalization.md), [16](16-ocsf-data-model.md)), định danh máy luôn nằm đúng chỗ (`device`, `src_endpoint`, `dst_endpoint`). Nhờ đó *chính các event* trở thành nguồn để dựng inventory và profile. Đây là một hướng khai thác dữ liệu đã chuẩn hóa: dữ liệu vốn chỉ để phát hiện tấn công nay còn cho biết tổ chức đang có những gì. File này định nghĩa các khái niệm. Cách dựng nằm ở [19](19-building-asset-profiles-from-events.md), cách dùng ở [20](20-asset-context-in-security-operations.md).

## Khái niệm cốt lõi

### Asset
- **Là gì**: thứ có giá trị cần bảo vệ ([01](01-security-fundamentals.md)). Trong vận hành bảo mật, chủ yếu là tài sản số *quan sát được*: máy trạm, server, VM, thiết bị mạng, thiết bị IoT/OT, tài nguyên cloud, phần mềm. Danh tính (user, service account) cũng là tài sản, có vòng quản lý riêng ([04](04-identity-and-access.md)).
- **Dùng để**: làm đơn vị để hỏi "cái gì cần bảo vệ, của ai, quan trọng đến đâu".

### Event và trạng thái thực thể
Đây là phân biệt quan trọng nhất của chủ đề:

| | Event | Trạng thái thực thể (entity state) |
|---|---|---|
| Ghi lại | một việc xảy ra tại một thời điểm | một thứ *là gì* trong một khoảng thời gian |
| Ví dụ | "máy `10.20.4.12` mở kết nối SMB lúc 09:02" | "`WS-0412`: Windows 11, phòng Tài chính, criticality High, thấy lần đầu tháng 3" |
| Số lượng | hàng tỷ, chỉ thêm, không sửa | một bản ghi mỗi tài sản, được cập nhật |
| Trong OCSF | event hoạt động, có `device` lồng bên trong | không có bảng sẵn; class Discovery chỉ là *ảnh chụp* trạng thái tại một thời điểm |

Inventory là tập các trạng thái thực thể. Profile là một dòng của tập đó, cộng lịch sử và thống kê.

### Asset inventory
- **Là gì**: danh sách các tài sản đang tồn tại, mỗi tài sản một bản ghi với định danh và vài thuộc tính. CIS Controls v8 tách hai danh sách: danh sách *đã duyệt* và danh sách *mọi thiết bị phát hiện được*, bằng tay hay bằng quét tự động. Tài sản có trong danh sách sau mà không có trong danh sách trước là tài sản chưa được phép hoặc chưa được quản lý.
- **Dùng để**: trả lời "tổ chức có những gì", nền của quản lý lỗ hổng ([06](06-vulnerability-management.md)) và đo độ phủ control. NIST CSF 2.0 (ID.AM) và CIS Control 1, 2 đặt việc này đầu tiên.

### Asset profile và ba lớp thuộc tính
- **Là gì**: hồ sơ đầy đủ của một tài sản. Thuộc tính chia ba lớp theo *cách có được*:

  | Lớp | Câu hỏi | Ví dụ | Nguồn |
  |---|---|---|---|
  | **Khai báo** | nó *nên* là gì? | owner, đơn vị, môi trường, criticality, "có bắt buộc cài EDR không" | CMDB, AD, tag cloud, người gán tay |
  | **Quan sát** | nó *đang* là gì? | hostname, IP, MAC, OS, phần mềm, first seen, last seen, *những nguồn nào đã thấy nó* | event và các ảnh chụp inventory |
  | **Tính toán** | rút ra được gì? | điểm rủi ro, mức phơi nhiễm, baseline hành vi (ai hay đăng nhập, process nào hay chạy) | phép tính trên lớp quan sát và alert |

- **Dùng để**: gắn ngữ cảnh cho event và alert. Chỗ lệch giữa các lớp là tín hiệu: thấy trong log nhưng không có trong CMDB là máy chưa quản lý; khai báo "bắt buộc EDR" mà EDR chưa từng báo về là lỗ hổng độ phủ.

### Nguồn khai báo và nguồn quan sát
- **Nguồn khai báo** (CMDB, ITAM, AD, watchlist): con người hay quy trình nhập vào. Biết được ý nghĩa nghiệp vụ, nhưng dễ cũ và thiếu.
- **Nguồn quan sát**: chính dữ liệu máy móc sinh ra.
  - *agent* trên máy (EDR, MDM) báo trạng thái bên trong máy;
  - *quét chủ động* dò mạng tìm máy đang bật;
  - *phát hiện thụ động*: đọc log và lưu lượng (DHCP, ARP, xác thực, kết nối) để thấy cả máy không có agent;
  - *API* của cloud, directory.

  CIS Control 1 có safeguard riêng cho quét chủ động, cho dùng log DHCP để cập nhật inventory, và cho phát hiện thụ động.

### Định danh tài sản
- **Là gì**: giá trị dùng để nhận ra cùng một tài sản giữa các nguồn. Thứ tự tin cậy mà các vendor dùng gần như giống nhau:
  1. ID do agent hay nền tảng cấp (agent ID, cloud instance ID);
  2. định danh phần cứng (UUID máy, MAC);
  3. hostname, FQDN, DN trong AD;
  4. IP, chỉ có nghĩa trong một khoảng thời gian và một phạm vi mạng.
- **Dùng để**: gộp các bản ghi về cùng một máy ([19](19-building-asset-profiles-from-events.md)).

### Criticality
- **Là gì**: mức quan trọng của tài sản với nghiệp vụ. Căn cứ vào dịch vụ nó phục vụ, dữ liệu nó giữ, và vai trò hạ tầng: domain controller, PKI, backup thường ở mức cao nhất. Khác với *risk* (khả năng bị tấn công thành công).
- **Dùng để**: biến cùng một alert thành mức ưu tiên khác nhau tùy máy.
- Có hai cách gán, và các vendor đang kết hợp cả hai:
  - *khai báo*: người gán, vd field `priority` trong asset lookup của Splunk ES;
  - *suy ra từ hành vi*: vd Microsoft Exposure Management tự nhận ra domain controller hay máy của domain admin, rồi xếp mức criticality.

### Tài sản trong OCSF
- **Object `device`**: mô tả một máy ở mọi nơi nó xuất hiện. Gồm định danh (`uid`, `uid_alt`, `hostname`, `ip`, `mac`, `os_machine_uuid`), ngữ cảnh khai báo (`owner`, `org`, `groups`, `zone`, `vpc_uid`), trạng thái quản lý (`is_managed`, `is_compliant`, `agent_list`), rủi ro (`risk_level_id`, `risk_score`) và thời gian (`first_seen_time`, `last_seen_time`).
- **Class Discovery**: Device Inventory Info (`5001`), Software Inventory Info (`5020`), User Inventory Info (`5003`), Cloud Resources Inventory Info (`5023`). Ghi *ảnh chụp* trạng thái lấy từ CMDB, máy quét, API.
- **Chỗ OCSF để trống**:
  - `device` không có attribute criticality; `criticality_id` chỉ có ở `resource_details` (trong `resources[]` của finding);
  - không có khái niệm khoảng hiệu lực cho ánh xạ IP → máy;
  - không định nghĩa cách gộp bản ghi.

  OCSF cho *từ vựng*, còn *quy trình* dựng profile là việc của nền tảng tiêu thụ dữ liệu.

## Cách hoạt động
```
nguồn khai báo (CMDB, AD) ──────────────┐
ảnh chụp inventory (OCSF 5001, 5020) ───┼─► gập theo định danh ─► asset inventory
event hoạt động có device/src/dst ──────┘   (19)                 (mỗi tài sản một profile:
                                                                  khai báo + quan sát + tính toán)
                                                                       │
event mới ◄──────────────── nối ngược ngữ cảnh (19) ◄──────────────────┘
```

## Ví dụ
Hồ sơ của `WS-0412` sau khi gập dữ liệu một tháng:
- *Khai báo* (CMDB): owner `lan.nguyen`, phòng Tài chính, criticality High.
- *Quan sát* (event):
  - Windows 11, MAC `3c:22:fb:..`;
  - IP `10.20.4.12` trong khung 06:58–14:58 (theo DHCP);
  - thấy lần đầu 02/03, lần cuối 5 phút trước;
  - được EDR, AD, firewall, DHCP báo về.
- *Tính toán*: 97% phiên đăng nhập là `lan.nguyen`; hoạt động 08:00–18:00; chưa từng mở SMB tới server khác ngoài file server.

Không event nào chứa cả hồ sơ này. Mỗi dòng trên là kết quả gập hàng trăm đến hàng nghìn event.

## Câu hỏi và trả lời

**Asset profile có nằm trong event OCSF không?**
Không. Event chỉ mang các *mảnh* thông tin về tài sản tại một thời điểm. Profile là trạng thái được gập từ nhiều event và nguồn khai báo, lưu riêng, rồi có thể gắn ngược vào event dưới dạng ngữ cảnh. Một event OCSF chứa `device.hostname` và `device.ip` của lúc đó. Hồ sơ "máy này của ai, thấy lần đầu khi nào, những nguồn nào thấy nó" chỉ có sau khi gập. Ranh giới: event Device Inventory Info (`5001`) trông giống bản ghi tài sản, nhưng vẫn là *ảnh chụp có thời điểm* từ một nguồn, chưa phải profile hợp nhất.

**Vì sao chuẩn hóa OCSF lại giúp dựng inventory?**
Vì muốn gập event theo tài sản, mọi nguồn phải đặt định danh tài sản ở cùng chỗ và cùng nghĩa. Chuẩn hóa làm đúng việc đó. Sau khi về OCSF, một quy tắc duy nhất đọc được máy từ `device`, `src_endpoint`, `dst_endpoint` của mọi nguồn, thay vì mỗi nguồn một bộ trích xuất. Ở Splunk, ngữ cảnh tài sản chỉ được khớp vào các field chuẩn `src`, `dest`, `dvc`; event chưa chuẩn hóa về các field này thì không nhận được ngữ cảnh. Ranh giới: chuẩn hóa chỉ giải phần cơ học. Quyết định hai bản ghi có phải một máy, và IP lúc 9 giờ thuộc máy nào, vẫn phải do bước gộp xử lý.

**Inventory, CMDB và profile khác nhau thế nào?**
Khác ở *nội dung* và *cách có*. CMDB là một nguồn khai báo, chỉ biết những gì con người nhập. Inventory là danh sách tài sản đang tồn tại, hợp nhất từ cả khai báo lẫn quan sát. Profile là hồ sơ đầy đủ của một tài sản trong inventory, có lịch sử và phần tính toán. CMDB là đầu vào; inventory và profile là đầu ra.

**Lớp nào của profile đáng tin hơn: khai báo hay quan sát?**
Mỗi lớp đáng tin cho một loại câu hỏi. Quan sát cho biết *cái gì tồn tại và đang làm gì*. Khai báo cho biết *nó quan trọng với nghiệp vụ ra sao*, điều máy móc không tự thấy (máy nào giữ dữ liệu lương). Vì vậy OS và last seen nên lấy từ quan sát; owner và criticality lấy từ khai báo, có thể kèm phân loại tự động để gợi ý. Các vendor đang hội tụ về mô hình lai này.

**Một tài sản có bao nhiêu định danh, và một định danh trỏ tới bao nhiêu tài sản?**
Một tài sản luôn có nhiều định danh. Định danh mạnh gắn với đúng một tài sản suốt vòng đời. Định danh yếu là quan hệ nhiều–nhiều theo thời gian: một IP lần lượt thuộc nhiều máy, một máy lần lượt có nhiều IP. Vì thế IP nên được hiểu là *một quan hệ có thời hạn* giữa địa chỉ và máy, không phải một thuộc tính cố định của máy.

## Hiểu nhầm thường gặp
- **"CMDB là inventory"**: CMDB chỉ là lớp khai báo; máy không có trong CMDB thường là máy nguy hiểm nhất.
- **"Máy không cài agent thì không biết gì về nó"**: máy đó vẫn để lại dấu vết trong log DHCP, ARP, xác thực, kết nối của các máy khác; phát hiện thụ động dựa vào chính điều này.
- **"Inventory là kiểm kê định kỳ"**: VM, container, thiết bị di động xuất hiện và biến mất liên tục; inventory phải được cập nhật liên tục từ dữ liệu.

## Liên quan
- [17-ocsf-event-anatomy.md](17-ocsf-event-anatomy.md): `device`, `src_endpoint`, `dst_endpoint` trong event.
- [19-building-asset-profiles-from-events.md](19-building-asset-profiles-from-events.md): cách gập event thành profile và nối ngược.
- [20-asset-context-in-security-operations.md](20-asset-context-in-security-operations.md): profile dùng vào việc gì.
- [Research: Microsoft và Splunk dựng asset inventory từ event chuẩn hóa](../research/2026-10-29-asset-profile-tu-event-chuan-hoa/report.md): chi tiết và nguồn.
