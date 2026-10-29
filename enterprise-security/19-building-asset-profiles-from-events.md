# Building asset profiles from events

> Dựng asset profile từ event đã chuẩn hóa là một vòng bốn bước: thu thập các lần "nhìn thấy" tài sản trong event và nguồn khai báo → nhận diện và gộp các lần nhìn thấy cùng một tài sản → gập thành hồ sơ ba lớp → nối ngữ cảnh ngược vào event và alert. Microsoft, Splunk và Google đều chạy vòng này, chỉ khác điểm xuất phát.

## Tại sao cần biết
[18-asset-inventory-and-profile.md](18-asset-inventory-and-profile.md) định nghĩa profile là trạng thái gập từ nhiều event. File này giải thích *cơ chế gập*: mỗi bước làm gì, khó ở đâu, và các vendor lớn hiện thực nó ra sao. Hiểu cơ chế thì đọc được bất kỳ sản phẩm "asset inventory", "CAASM", "entity analytics" nào, và biết vì sao profile có khi sai.

## Khái niệm cốt lõi

### Bước 1: Thu thập quan sát (sighting)
- **Là gì**: một *quan sát* là câu "tài sản có định danh X, với thuộc tính Y, được nguồn S thấy lúc T". Mỗi event có máy bên trong sinh ra một hoặc vài quan sát. Nguồn khai báo (CMDB, AD) và ảnh chụp inventory (OCSF `5001`) cũng sinh quan sát.
- **Dùng để**: làm nguyên liệu cho mọi bước sau. Độ tin cậy của quan sát phụ thuộc *vai* của máy trong event:
  - `device`: mạnh, vì nguồn tự báo về máy nó chạy trên đó;
  - `src_endpoint`/`dst_endpoint`: yếu hơn, vì đây là một máy khác nhìn thấy, vd hostname do client tự khai.
- **Phát hiện thụ động** là trường hợp đặc biệt: máy có agent trở thành *cảm biến* cho máy không có agent.
  - Defender for Endpoint ở chế độ Basic chỉ nghe ARP, DHCP, mDNS, NBNS, LLMNR... mà các máy đã onboard nhìn thấy, rồi rút ra thông tin thiết bị. Theo tài liệu Microsoft, bất kỳ thiết bị nào giao tiếp với máy đã onboard *trong mạng corporate* đều có thể được phát hiện. Mạng được coi là corporate khi đa số máy báo cùng tên mạng, gateway và DHCP server. Thiết bị ở mạng khác không vào inventory.
  - Chế độ Standard dò chủ động thêm các máy chưa quản lý, thường không quá một lần mỗi ba tuần cho mỗi thiết bị.

### Bước 2: Nhận diện và gộp (entity resolution)
- **Là gì**: quyết định các quan sát nào thuộc *cùng một* tài sản, dựa trên định danh, ưu tiên định danh bền hơn IP ([18](18-asset-inventory-and-profile.md)).
- **Dùng để**: một máy có một hồ sơ, không phải mười.
- Hai kiểu lỗi ngược chiều nhau:
  - **Gộp quá tay**: hai máy khác nhau bị nhập làm một. Splunk ES cổ điển gộp các bản ghi trùng giá trị ở key field (`ip`, `mac`, `nt_host`, `dns`), và docs ghi rõ phép gộp không kiểm tra hay khử trùng đầu vào. Người dùng ES đã báo các workstation dùng lại IP DHCP bị kéo về một tài sản, và một load balancer trả lời máy quét bằng cùng một MAC gây gộp sai. Bản vá là *entity zones*: tách bản ghi cùng khóa nhưng khác phân đoạn mạng.
  - **Gộp quá ít**: một máy thành nhiều bản ghi. Đổi tên, join domain, reimage hay một lần device discovery quét trúng máy đã onboard đều có thể sinh bản ghi mới. Defender *ẩn* bản trùng dựa trên hostname và last seen, nhưng bản trùng vẫn còn trong advanced hunting, alert và incident. Bảng `DeviceInfo` giữ cột `MergedDeviceIds` cho các ID cũ của cùng máy; tiêu chí gộp `DeviceId` thì Microsoft không công bố.
- **Ưu tiên nguồn**: khi hai nguồn nói khác nhau về cùng một thuộc tính, chọn theo thứ hạng.
  - Splunk ES xếp hạng theo danh sách asset.
  - Splunk Asset and Risk Intelligence (ARI) xếp hạng theo nguồn *và theo từng field*, nên một nguồn có thể thắng ở field mà nó chính xác nhất.

### Bước 3: Gập thành hồ sơ
- **Là gì**: tính từng thuộc tính của profile từ tập quan sát đã gộp.
- **Dùng để**: có một bản ghi trả lời ngay "máy này là gì". Mỗi loại thuộc tính gập một kiểu:
  - *thời gian*: `first_seen` = lần thấy sớm nhất, `last_seen` = lần thấy gần nhất;
  - *giá trị hiện tại*: OS, hostname, lấy theo nguồn ưu tiên rồi theo thời gian mới nhất;
  - *danh sách nguồn đã thấy*: Defender gọi là *discovery sources*, ARI liệt kê nguồn đã thấy kèm lần thấy cuối. Thiếu một nguồn trong danh sách này chính là lỗ hổng độ phủ;
  - *tính toán*: điểm rủi ro, baseline hành vi (Sentinel UEBA dựng baseline theo user, host, peer group).
- Kết quả thường là một bảng *ảnh chụp lặp lại* đặt cạnh bảng event. Ở Microsoft là `DeviceInfo`: mỗi bản cập nhật chứa đủ trạng thái hiện tại của thiết bị, truy vấn lấy bản mới nhất theo `DeviceId`.

### Ánh xạ IP → máy theo thời gian
- **Là gì**: bảng ghi "IP này thuộc máy kia từ lúc A đến lúc B", dựng từ DHCP, VPN, log đăng nhập.
- **Dùng để**: gán đúng máy cho event chỉ có IP. Thiết kế mới của các vendor coi IP là *thực thể quan hệ có thời hạn*:
  - ARI và Exposure Analytics của Splunk tách IP thành inventory riêng, theo dõi first/last time của từng liên kết user–host–IP–MAC;
  - Google SecOps dùng log DHCP để tạo alias nối hostname, IP, MAC theo thời gian;
  - CIS Control 1 yêu cầu dùng log DHCP để cập nhật inventory.

### Bước 4: Nối ngữ cảnh ngược (enrichment)
- **Là gì**: gắn thuộc tính của profile vào event hay alert có chứa tài sản đó.
- **Dùng để**: rule, ưu tiên và analyst dùng được ngữ cảnh mà nguồn log không có ([20](20-asset-context-in-security-operations.md)).
- Hai thời điểm nối, sai theo hai chiều ngược nhau:

  | | Nối lúc truy vấn (search time) | Nối lúc nạp (ingest time) |
  |---|---|---|
  | Ví dụ | Splunk ES khớp `src`/`dest`/`dvc` với asset lookup, thêm `src_priority`, `dest_category`; Microsoft join `DeviceInfo` vào bảng event | Google SecOps điền hostname khi event chỉ có IP; OCSF đặt `enrichments` vào event trước khi lưu |
  | Đúng ở | luôn có ngữ cảnh mới nhất (criticality vừa sửa) | giữ đúng ngữ cảnh *lúc sự việc xảy ra* |
  | Sai ở | event cũ bị gán cho máy đang giữ IP *hôm nay* | ngữ cảnh bị "đóng băng"; event đến trước log DHCP thì chưa gán được (Google sửa lại event trong khoảng 24 giờ, quá hạn đó thì thôi) |

  Cách giải bền vững: lưu ánh xạ có khoảng hiệu lực, rồi nối theo cả định danh lẫn thời gian của event.
- Trong OCSF, ngữ cảnh nối ngược đi vào `enrichments[]` (có `name`, `value`, `type`, `data`, `provider`), kèm `metadata.modified_time`; hoặc điền vào attribute còn trống của `device`.

### Hai điểm xuất phát
- **Bắt đầu từ quan sát** (Microsoft Defender): mỗi máy có agent là một cảm biến, inventory sinh ra từ telemetry và discovery; criticality được *suy ra* bằng bộ phân loại hành vi, người dùng duyệt hoặc gán thêm.
- **Bắt đầu từ khai báo** (Splunk ES cổ điển): asset lookup từ CMDB, AD được gộp theo key field rồi khớp vào event lúc search. Các sản phẩm mới hơn (ARI, Exposure Analytics trong ES 8.5) chuyển sang khám phá tài sản từ log. Tài liệu Splunk cũng cảnh báo rằng trộn với lookup khai báo thủ công có thể kéo dữ liệu cũ vào.

## Cách hoạt động
```
                1. Thu thập                   2. Gộp                   3. Gập
event OCSF ─► quan sát (định danh, ─► nhóm theo định danh ─► profile: first/last seen,
CMDB, AD   ─►  thuộc tính, nguồn,      mạnh → yếu; IP kèm        giá trị hiện tại, nguồn đã thấy,
5001, 5020 ─►  thời điểm)              khoảng thời gian          khai báo, điểm tính toán
                                                                      │
                4. Nối ngược ◄─────────────────────────────────────────┘
event/alert mới ─► tra profile theo định danh + thời điểm ─► device.*, enrichments[]
```

Mỗi thành phần trong vòng ứng với một chỗ trong OCSF:

| Thành phần của vòng | Trong OCSF |
|---|---|
| Quan sát từ event hoạt động | `device`, `src_endpoint`, `dst_endpoint` lồng trong event |
| Ảnh chụp từ nguồn khai báo, máy quét | class Discovery `5001`, `5020`, `5003`, `5023` |
| Định danh để gộp | `uid`, `uid_alt`, `hostname`, `mac`, `os_machine_uuid`, `ip` |
| Thuộc tính thời gian của profile | `first_seen_time`, `last_seen_time` (nền tảng tự tính) |
| Ngữ cảnh nối ngược | `enrichments[]`, attribute của `device` |
| Quy tắc gộp, khoảng hiệu lực của IP, criticality trên `device` | không có, nền tảng tự định nghĩa |

## Ví dụ
Firewall ghi một kết nối từ `10.20.4.12` lúc 09:02, event OCSF chỉ có `src_endpoint.ip`.
1. *Thu thập*: event là một quan sát "IP 10.20.4.12 hoạt động lúc 09:02, theo firewall".
2. *Gộp*: tra ánh xạ IP → máy. Log DHCP cho biết `10.20.4.12` được cấp cho MAC `3c:22:fb:..` từ 06:58 đến 14:58. MAC đó thuộc `WS-0412`, nơi agent EDR có ID `agent-7f3a`.
3. *Gập*: quan sát này cập nhật `last_seen` của `WS-0412`, thêm "firewall" vào danh sách nguồn đã thấy.
4. *Nối ngược*: event được gắn `enrichments` với `name = "src_endpoint.ip"`, `data` gồm hostname `WS-0412`, owner, criticality High, cùng ghi chú rằng mối nối đi qua IP và DHCP, tức là định danh yếu.

Nếu cùng IP xuất hiện lúc 16:00 thì lease đã hết. Gán nó cho `WS-0412` là sai.

## Câu hỏi và trả lời

**Một event đóng góp gì cho profile, và một profile cần bao nhiêu event?**
Mỗi event có tài sản đóng góp *một quan sát*: tài sản tồn tại, có vài thuộc tính, tại một thời điểm, theo một nguồn. Profile là kết quả gập *mọi* quan sát của tài sản đó. Vì vậy profile càng đầy đủ khi càng nhiều nguồn thấy tài sản. Một máy chỉ được firewall thấy có profile mỏng (IP, last seen); máy có agent có profile dày (OS, phần mềm, user). Ranh giới: quan sát ở vai `src_endpoint` (hostname do client khai) đóng góp ít tin cậy hơn quan sát ở vai `device`.

**Vì sao gộp tài sản theo IP lại nguy hiểm?**
Vì IP là quan hệ có thời hạn: cùng một IP lần lượt thuộc nhiều máy (DHCP), và nhiều máy có thể hiện ra sau một IP (NAT, proxy, VPN). Dùng IP làm khóa gộp ngang hàng với hostname thì các máy khác nhau dùng lại IP bị nhập làm một. Đây là lỗi đã được ghi nhận với Splunk ES cổ điển. Các thiết kế mới tách IP thành thực thể riêng, có thời gian và phạm vi mạng (zone). Sentinel chỉ coi IP nội bộ là định danh mạnh khi đi kèm phạm vi (`AddressScope`).

**Nên nối ngữ cảnh lúc nạp hay lúc truy vấn?**
Thời điểm nối quyết định ngữ cảnh "của lúc nào". Nối lúc nạp cho ngữ cảnh lúc sự việc xảy ra nhưng đóng băng nó. Nối lúc truy vấn cho ngữ cảnh mới nhất nhưng có thể sai với event cũ. Câu hỏi điều tra ("máy này *khi đó* của ai") cần ngữ cảnh lúc xảy ra. Câu hỏi ưu tiên hiện tại ("máy này *bây giờ* quan trọng đến đâu") cần ngữ cảnh mới nhất. Nối theo khoảng hiệu lực đáp được cả hai.

**OCSF có định nghĩa cách dựng asset inventory không?**
Không. OCSF định nghĩa *từ vựng*: `device`, các class Discovery, `enrichments`, `first_seen_time`, `last_seen_time`. Nó không định nghĩa quy tắc gộp, ưu tiên nguồn, khoảng hiệu lực cho IP, và chưa có criticality trên `device`. Những phần đó do nền tảng dùng dữ liệu OCSF tự hiện thực, giống như Microsoft và Splunk tự hiện thực trên ASIM và CIM.

**Vendor có công bố độ chính xác của việc gộp không?**
Không. Theo khảo sát (xem research), cả Microsoft lẫn Splunk đều không công bố thuật toán gộp đầy đủ, tỷ lệ gộp nhầm hay độ chính xác của bộ phân loại criticality. Vì vậy profile luôn cần được xem như *suy luận có độ tin cậy*, và việc phân biệt mối nối qua định danh mạnh với định danh yếu nên hiện ra trong dữ liệu.

## Hiểu nhầm thường gặp
- **"Inventory là một bảng có sẵn trong SIEM"**: inventory là kết quả của một quy trình chạy liên tục (thu thập, gộp, gập); dừng quy trình thì inventory cũ dần.
- **"Gộp càng mạnh càng tốt"**: gộp mạnh làm nhập nhầm máy, gộp yếu làm trùng máy; cả hai đều làm sai ưu tiên và điều tra.
- **"Enrich một lần là xong"**: profile thay đổi (owner, criticality, IP); ngữ cảnh gắn vào event chỉ đúng tại thời điểm gắn.

## Liên quan
- [18-asset-inventory-and-profile.md](18-asset-inventory-and-profile.md): event và trạng thái thực thể, ba lớp profile, định danh.
- [17-ocsf-event-anatomy.md](17-ocsf-event-anatomy.md): vai của máy trong event, `enrichments`, `metadata`.
- [20-asset-context-in-security-operations.md](20-asset-context-in-security-operations.md): ngữ cảnh nối ngược dùng vào việc gì.
- [Research: Microsoft và Splunk dựng asset inventory từ event chuẩn hóa](../research/2026-10-29-asset-profile-tu-event-chuan-hoa/report.md): nguồn, mức chắc chắn, chỗ chưa kiểm chứng.
