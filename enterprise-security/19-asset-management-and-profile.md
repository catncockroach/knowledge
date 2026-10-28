# Asset management and profile

> Asset management là việc liên tục biết tổ chức đang có những tài sản gì, của ai, quan trọng đến đâu và đang ở trạng thái nào; asset profile là hồ sơ của từng tài sản, gồm ba lớp: thông tin *khai báo* (nó nên là gì), *trạng thái quan sát* (nó đang là gì) và *hành vi* (nó thường làm gì).

## Tại sao cần biết
Mọi quyết định bảo mật đều xoay quanh tài sản. Vá lỗ hổng nào trước, alert nào xử lý trước, cô lập máy nào, báo cho ai đều không trả lời được nếu không biết máy đó là gì. Các framework cũng đặt việc này lên đầu: NIST CSF 2.0 mở chức năng Identify bằng category Asset Management (ID.AM); CIS Controls v8 có Control 1 (tài sản doanh nghiệp) và Control 2 (tài sản phần mềm) là hai control đầu tiên. Không biết mình có gì thì không bảo vệ được.

Trong chuyên đề này, asset management còn là **một ứng dụng của log OCSF**: khi mọi nguồn đã về một schema sạch, chính log trở thành nguồn dữ liệu tài sản đầy đủ và cập nhật nhất ([20-asset-profiling-from-ocsf-logs.md](20-asset-profiling-from-ocsf-logs.md)).

## Khái niệm cốt lõi

### Asset là gì
Theo [01-security-fundamentals.md](01-security-fundamentals.md), asset là bất cứ thứ gì có giá trị cần bảo vệ. Ở góc độ vận hành bảo mật, "asset" thường chỉ các **tài sản số có thể quan sát được**:

| Loại | Ví dụ | Định danh điển hình |
|---|---|---|
| Endpoint | laptop, desktop, điện thoại | hostname, EDR agent ID, serial |
| Server, VM | máy chủ vật lý, máy ảo | hostname, instance ID |
| Thiết bị mạng | firewall, switch, router, AP | hostname, IP quản trị, serial |
| Cloud resource | instance, bucket, database, function | ARN / resource ID, account |
| Container, workload | pod, container | container ID, image |
| IoT, OT | camera, máy in, PLC | MAC, IP |
| Phần mềm, dịch vụ | ứng dụng cài trên máy, dịch vụ đang chạy | tên + phiên bản, cổng |

Danh tính (user, service account) cũng là tài sản và có profile riêng; file này tập trung vào máy và workload, nhưng cách làm áp dụng tương tự cho danh tính.

### Asset management là gì
Một vòng lặp liên tục, không phải một bảng kê làm một lần:

1. **Discover**: phát hiện tài sản đang tồn tại, gồm cả tài sản không ai khai báo.
2. **Identify**: gán định danh ổn định, gộp các bản ghi trùng.
3. **Classify**: gán owner, đơn vị, môi trường, criticality.
4. **Monitor**: theo dõi trạng thái (OS, phần mềm, lỗ hổng, có EDR không) và thay đổi.
5. **Retire**: ghi nhận tài sản đã thu hồi, để sau này không nhầm "máy lạ".

Hai cách nhìn: **ITAM** (quản lý tài sản CNTT) quan tâm mua sắm, license, khấu hao; **cyber asset management** quan tâm độ phủ control, lỗ hổng, bề mặt tấn công. Nhóm công cụ gom dữ liệu tài sản từ nhiều nguồn cho mục đích bảo mật thường được gọi là **CAASM** (Cyber Asset Attack Surface Management).

### Inventory khác profile
- **Asset inventory**: *danh sách* tài sản đang có, mỗi dòng một tài sản với vài thuộc tính. Trả lời câu "có gì?".
- **Asset profile**: *hồ sơ* đầy đủ của một tài sản, gồm cả lịch sử và hành vi. Trả lời câu "nó là gì, của ai, đang thế nào, thường làm gì?".

### Ba lớp của một asset profile

| Lớp | Câu hỏi | Ví dụ thuộc tính | Nguồn chính |
|---|---|---|---|
| **Khai báo** (declared) | Nó *nên* là gì? | owner, đơn vị, dịch vụ nghiệp vụ, môi trường, criticality | CMDB, ITAM, tag cloud, AD OU |
| **Trạng thái quan sát** (observed state) | Nó *đang* là gì? | OS, phiên bản, IP, MAC, phần mềm, cổng mở, lỗ hổng, có EDR, managed/compliant, last seen | EDR, MDM, scanner, cloud API, DHCP, *log OCSF* |
| **Hành vi** (behavioral) | Nó *thường làm* gì? | user hay đăng nhập, process hay chạy, đích kết nối, giờ hoạt động, dịch vụ lắng nghe | *log OCSF* gom theo thời gian |

Lớp khai báo do con người nhập, dễ cũ. Lớp quan sát và lớp hành vi được dựng tự động từ dữ liệu, nên luôn mới. **Chỗ lệch giữa các lớp** mới là tín hiệu có giá trị: CMDB nói máy là server web nhưng log thấy nó chạy công cụ quản trị domain; máy khai báo "dev" nhưng nhận kết nối từ internet.

### Nguồn chuẩn cho từng thuộc tính
Không nguồn nào đúng về mọi thứ, nên mỗi thuộc tính chọn một *source of truth*:

| Nguồn | Mạnh ở |
|---|---|
| CMDB / ITAM | owner, dịch vụ nghiệp vụ, môi trường, criticality |
| AD / Entra ID / LDAP | tên máy trong domain, OU, nhóm |
| EDR | agent ID, OS, user đăng nhập, last seen, process |
| MDM | managed, compliant, thiết bị cá nhân hay công ty |
| Cloud inventory API | instance ID, tag, region, VPC, account |
| Vulnerability scanner | lỗ hổng, cổng mở, dịch vụ |
| DHCP / IPAM / NAC | IP ↔ MAC ↔ hostname theo thời gian |
| Log sự kiện (đã về OCSF) | mọi thuộc tính quan sát và hành vi, kể cả của tài sản không có trong các nguồn trên |

### Entity resolution: biết hai bản ghi là cùng một máy
- **Khóa mạnh**, ít đổi và gần như duy nhất: EDR agent ID, cloud instance ID, serial number, OS machine UUID.
- **Khóa yếu**, chỉ dùng khi thiếu khóa mạnh:
  - hostname: trùng giữa các domain, đổi khi cài lại máy;
  - IP: đổi theo DHCP, bị NAT/VPN che;
  - MAC: VM nhân bản, điện thoại dùng MAC ngẫu nhiên.
- **Quy tắc ghép**: nối theo khóa mạnh trước, khóa yếu sau, ghi độ tin cậy của mỗi lần ghép. Khi các nguồn mâu thuẫn, theo nguồn chuẩn của thuộc tính; ngang nhau thì lấy nguồn có `last_seen` mới hơn.

### Thời gian là một chiều của profile
IP `10.20.4.12` thuộc `WS-0412` lúc 9 giờ nhưng có thể thuộc máy khác lúc 15 giờ. Ánh xạ IP → máy phải lưu theo khoảng hiệu lực (`valid_from`, `valid_to`), và tra theo **thời điểm của event**. Owner, OS, criticality cũng cần lịch sử: điều tra sự cố cũ cần trạng thái *lúc xảy ra*.

### Criticality
Mức quan trọng của tài sản với tổ chức, thường 3–5 bậc (Low → Critical). Căn cứ:
- dịch vụ nghiệp vụ mà máy phục vụ;
- độ nhạy của dữ liệu trên máy;
- vai trò hạ tầng: domain controller, PKI, backup, máy quản trị; chiếm được chúng là chiếm được cả hệ thống;
- mức phơi ra ngoài.

Criticality là *giá trị nghiệp vụ*, khác với *risk* (khả năng bị tấn công thành công). Domain controller vá đầy đủ có criticality cao, risk thấp.

## Cách hoạt động

```
CMDB, AD, tag cloud ─────────────────────────────────┐ lớp khai báo
EDR, MDM, scanner, cloud API, DHCP ──────────────────┤ lớp trạng thái
Log OCSF (process, auth, network, DNS, inventory) ───┤ lớp trạng thái + hành vi
                                                     ▼
                         Entity resolution (khóa mạnh → yếu, nguồn chuẩn)
                                                     ▼
                         Asset profile store
                         ├─ bản hiện tại
                         ├─ lịch sử (IP↔máy, owner, OS theo thời gian)
                         ├─ baseline hành vi
                         └─ bảng lookup cho enrich (21)
                                                     ▼
                         Ứng dụng: enrich, ưu tiên, độ phủ, lỗ hổng, IR (22)
```

## Ví dụ
Hồ sơ của laptop `WS-0412`, ghép từ nhiều nguồn:

```
định danh   asset_id=edr-agent-7f3a  hostname=WS-0412  fqdn=WS-0412.corp.local
khai báo    owner=lan.nguyen  bu=Tài chính  env=prod  criticality=High        (CMDB, AD OU)
trạng thái  type=laptop  os=Windows 11  managed=true  edr=true                 (EDR, MDM)
            ip_history=[10.20.4.12 @ 06:58–14:58]                               (DHCP)
hành vi     user thường gặp: lan.nguyen (97% phiên)                             (log Authentication)
            giờ hoạt động: 08:00–18:00 ngày thường                              (mọi log)
            process phổ biến: outlook, excel, chrome, ứng dụng kế toán          (log Process)
            đích kết nối: mail, ERP, proxy; không SMB tới server ngoài file     (log Network)
```

Một event mới "`WS-0412` mở SMB tới 40 máy trong 5 phút lúc 02:00" lệch hẳn khỏi lớp hành vi. Profile biến event bình thường về mặt kỹ thuật thành một tín hiệu đáng chú ý.

## Hiểu nhầm thường gặp
- **"Asset management là việc của bộ phận IT, làm một lần bằng bảng kê"**: đó là inventory tĩnh. Asset management cho bảo mật là vòng lặp liên tục, và dữ liệu tốt nhất cho nó đến từ log.
- **"CMDB là đủ"**: CMDB chỉ là lớp khai báo, thường cũ và thiếu máy. Máy không có trong CMDB chính là máy nguy hiểm nhất.
- **"Profile = vài thuộc tính tĩnh"**: thiếu lớp hành vi thì profile chỉ giúp tra cứu, không giúp phát hiện bất thường.
- **"IP là định danh máy"**: IP chỉ là thuộc tính tạm thời; dùng làm khóa mà không kèm thời gian sẽ gán sự kiện cho nhầm máy.

## Liên quan
- [01-security-fundamentals.md](01-security-fundamentals.md): khái niệm asset và rủi ro.
- [03-frameworks-and-governance.md](03-frameworks-and-governance.md): NIST CSF, CIS Controls.
- [06-vulnerability-management.md](06-vulnerability-management.md): inventory là tiền đề quản lý lỗ hổng.
- [20-asset-profiling-from-ocsf-logs.md](20-asset-profiling-from-ocsf-logs.md): dựng lớp quan sát và hành vi từ log OCSF.
- [21-asset-enrichment-in-ocsf.md](21-asset-enrichment-in-ocsf.md): đưa profile ngược vào event.
- [22-asset-data-use-cases.md](22-asset-data-use-cases.md): ứng dụng của asset profile.
