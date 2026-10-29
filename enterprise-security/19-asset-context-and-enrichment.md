# Asset context and enrichment

> Log và asset profile nuôi nhau theo hai chiều: mỗi event đã chuẩn hóa là một lần quan sát tài sản, góp vào profile; ngược lại, profile được gắn vào event dưới dạng ngữ cảnh (enrichment) để event mang đủ nghĩa cho người và máy đọc.

## Tại sao cần biết
Log nguồn chỉ biết những gì nó thấy: một hostname, một IP, có khi chỉ một agent ID. Câu hỏi cần trả lời lại nằm ngoài log: máy đó của ai, quan trọng đến đâu, có EDR không. Mặt khác, chính log là nguồn phát hiện tài sản đầy đủ và mới nhất ([18-asset-management.md](18-asset-management.md)). Hiểu quan hệ hai chiều này là hiểu vì sao log đã chuẩn hóa ([15-security-data-normalization.md](15-security-data-normalization.md)) có giá trị vượt ra ngoài detection.

## Khái niệm cốt lõi
- **Event là một lần quan sát (sighting)**: mỗi event khẳng định "tài sản X tồn tại, với thuộc tính Y, lúc T, theo nguồn S". Độ tin cậy tùy vai trò:
  - `device` (observer) là quan sát mạnh: nguồn mô tả chính máy nó chạy trên đó;
  - `src_endpoint`/`dst_endpoint` yếu hơn: một máy khác nhìn thấy, vd hostname do client tự khai.
- **Log nuôi profile**:
  - Class inventory của OCSF (Device Inventory Info, Software Inventory Info, Vulnerability Finding...) cho lớp *quan sát* dạng snapshot.
  - Class hoạt động cho cả lớp quan sát lẫn lớp *hành vi*: Authentication cho biết ai dùng máy; Process Activity cho biết phần mềm thực sự chạy; Network Activity cho biết dịch vụ lắng nghe và đích kết nối; DHCP Activity cho biết IP ↔ MAC ↔ hostname theo thời gian.
  - `metadata.product` cho biết cảm biến nào thấy máy, tức máy đang có những control nào.
  - Đây là phát hiện tài sản *thụ động*. Nó chỉ khả thi ở quy mô lớn khi mọi nguồn đã về cùng schema, vì tài sản luôn nằm ở cùng object với cùng tên field.
- **Enrichment**: bổ sung vào event thông tin mà nguồn không có. Các loại chính:
  - *asset*: owner, đơn vị, criticality, trạng thái control;
  - *identity*: phòng ban, chức danh, quyền của user ([04-identity-and-access.md](04-identity-and-access.md));
  - *network*: GeoIP, ASN, nội bộ hay bên ngoài;
  - *threat intel*: danh tiếng của IP, domain, hash ([10-threat-intelligence.md](10-threat-intelligence.md)).
- **Ngữ cảnh tài sản nằm ở đâu trong OCSF**:
  - attribute có sẵn của `device`/endpoint: `owner`, `org`, `groups`, `type_id`, `os`, `is_managed`, `is_compliant`, `risk_level_id`, `first_seen_time`, `last_seen_time`;
  - `enrichments[]` cho ngữ cảnh không có attribute riêng, kèm nguồn cung cấp và thời điểm;
  - `resources[]` của finding, nơi có `criticality_id`.

  Object `device` (OCSF 1.9.0) không có attribute criticality; `risk_level_id` là mức rủi ro, không phải giá trị nghiệp vụ.
- **Quan sát và suy luận**: giá trị nguồn báo là *bằng chứng*; giá trị từ profile là *suy luận*. Hai loại cần phân biệt được trong dữ liệu, để khi profile sai vẫn biết nguồn đã nói gì.
- **Thời điểm enrich quyết định "ngữ cảnh của lúc nào"**:
  - *lúc ingest*: event giữ ngữ cảnh tại thời điểm xảy ra, đúng cho điều tra về sau, nhưng sai mãi nếu profile lúc ấy sai;
  - *lúc truy vấn*: luôn theo profile mới nhất, nhưng chỉ là trạng thái hiện tại nếu profile không có lịch sử;
  - *lúc có alert*: chỉ enrich số ít event cần xử lý, nhưng ngữ cảnh không có sẵn cho rule dùng.

## Cách hoạt động
```
         ┌──────────────── quan sát (sighting) ───────────────┐
         │                                                    ▼
Log ─► Event OCSF ───────────────────────────────────► Asset profile
         ▲                                            (khai báo + quan sát + hành vi)
         └──────────────── ngữ cảnh (enrichment) ─────────────┘
```
Vòng này tự củng cố: log đầy đủ cho profile chính xác, profile chính xác cho event giàu ngữ cảnh. Một mắt xích hỏng (map sai vai trò máy, tra sai thời điểm) làm hỏng cả hai chiều.

## Ví dụ
Event `4625` trên `DC01` từ `WS-0412` (xem [15](15-security-data-normalization.md)) sau khi enrich:
- `device` = DC01: thuộc nhóm `Tier0`, `Domain Controllers`; criticality Critical.
- `src_endpoint` = WS-0412: laptop phòng Tài chính, owner `lan.nguyen`, có EDR. Mối nối IP → máy suy ra từ DHCP lease tại đúng thời điểm event, tức là suy luận từ định danh yếu.

Cùng một lần gõ sai mật khẩu, nhưng giờ đọc được là: đích là tài sản quan trọng nhất của domain, nguồn là một máy đã được quản lý.

## Câu hỏi và trả lời

**Enrichment có sửa dữ liệu nguồn không?**
Enrichment thêm, không sửa. Dữ liệu nguồn là bằng chứng về điều nguồn đã thấy; enrichment là thông tin từ bên ngoài, có nguồn cung cấp và thời điểm riêng. Trong OCSF, `enrichments[]` ghi rõ `provider`, `created_time` và field được làm giàu. Khi ngữ cảnh được điền vào attribute của `device`, cần phân biệt được attribute nào nguồn báo và attribute nào được bổ sung.

**Một event được enrich cho bao nhiêu thực thể?**
Mỗi thực thể trong event có thể có ngữ cảnh riêng. Mỗi phần tử của `enrichments[]` trỏ tới đúng một field qua `name` và `value`, nên một event có thể mang ngữ cảnh cho `device`, `src_endpoint.ip`, `user.name`... cùng lúc mà không lẫn.

**Ngữ cảnh gắn vào event là của thời điểm nào?**
Là của thời điểm enrich, không tự động là của thời điểm sự việc. Enrich ngay khi event đến thì hai thời điểm gần như trùng nhau. Enrich lúc truy vấn thì ngữ cảnh là của hiện tại, trừ khi nguồn ngữ cảnh lưu lịch sử và được tra theo `time` của event. Điều tra một sự việc cũ cần ngữ cảnh *lúc sự việc xảy ra*.

**Vì sao log có thể dùng làm nguồn inventory?**
Mọi event có tài sản đều là một bằng chứng rằng tài sản đó tồn tại và đang hoạt động, kèm một số thuộc tính của nó. Tập hợp các lần quan sát theo thời gian cho ra lớp quan sát và lớp hành vi của profile. Giới hạn: log chỉ thấy tài sản *có hoạt động* và *được ít nhất một nguồn ghi lại*. Tài sản im lặng hoặc nằm ngoài vùng thu log vẫn cần các cách phát hiện khác.

## Hiểu nhầm thường gặp
- **"Enrichment là việc phụ"**: thiếu ngữ cảnh tài sản thì mọi alert trông như nhau; ưu tiên và triage đều dựa vào nó.
- **"Mọi hostname trong log là một máy"**: proxy, NAT, VPN gateway làm nhiều máy hiện như một; terminal server có hàng trăm user. Quan sát cần độ tin cậy theo vai trò và nguồn.
- **"Không khớp profile thì bỏ qua"**: tài sản không có trong profile chính là phát hiện: máy chưa quản lý, chưa có EDR, hoặc không phải của tổ chức.

## Liên quan
- [17-ocsf-event-anatomy.md](17-ocsf-event-anatomy.md): `device`, `observables`, `enrichments`, `metadata` dùng để làm gì.
- [18-asset-management.md](18-asset-management.md): ba lớp profile, định danh, thời gian.
- [20-asset-context-in-security-operations.md](20-asset-context-in-security-operations.md): ngữ cảnh tài sản được dùng vào việc gì.
