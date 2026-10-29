# OCSF data model

> OCSF dựng schema từ một số thành phần cố định: dictionary attribute, kiểu dữ liệu, object, cây phân loại category → class → activity, mức bắt buộc, enum, profile, extension và phiên bản. Mỗi event là bản ghi của **đúng một class**, có thể được **gắn thêm nhiều profile**, và có thể dùng định nghĩa từ **nhiều extension**: ba trục này độc lập với nhau.

## Tại sao cần biết
Biết từng thành phần dùng để làm gì thì đọc được mọi class OCSF, kể cả class chưa gặp, và hiểu vì sao dữ liệu đã chuẩn hóa so sánh được với nhau. Câu hỏi hay gặp nhất khi bắt đầu là "một log thuộc mấy class" và "profile khác extension ở đâu"; cả hai được trả lời bằng cùng một mô hình: class quyết định *bản ghi là loại gì*, profile quyết định *bản ghi có thêm khía cạnh nào*, extension quyết định *định nghĩa đến từ đâu*. File này mô tả *khung* của schema; những gì một event cụ thể chứa nằm ở [17-ocsf-event-anatomy.md](17-ocsf-event-anatomy.md). Vì sao cần một schema chung thì xem [15-security-data-normalization.md](15-security-data-normalization.md).

## Khái niệm cốt lõi

### Dictionary và attribute
- **Là gì**: dictionary là danh sách *mọi* attribute của schema. Mỗi attribute có tên, kiểu, mô tả; class, object và profile chỉ *tham chiếu* attribute từ dictionary và đặt mức bắt buộc cho nó, không định nghĩa lại kiểu.
- **Dùng để**: bảo đảm một tên chỉ có một nghĩa và một kiểu ở khắp nơi. `hostname` trong `device`, `src_endpoint` hay `dst_endpoint` là cùng một khái niệm.

### Kiểu dữ liệu (data type)
- **Là gì**: kiểu cơ bản (`string_t`, `integer_t`, `long_t`, `float_t`, `boolean_t`, `json_t`) và kiểu có ngữ nghĩa dựng trên kiểu cơ bản: `timestamp_t` (epoch milliseconds UTC), `ip_t`, `mac_t`, `hostname_t`, `port_t`, `url_t`, `email_t`, `file_hash_t`, `file_path_t`, `username_t`, `uuid_t`... Object cũng là một kiểu (kiểu phức hợp).
- **Dùng để**: kiểm tra giá trị hợp lệ (một IP phải là IP); so sánh đúng (thời gian mọi nguồn cùng đơn vị, cùng múi giờ); nhận diện thực thể (nhiều kiểu gắn sẵn loại *observable*, nhờ đó gom được các thực thể đáng chú ý của event).

### Object
- **Là gì**: một nhóm attribute có cấu trúc, dùng lại được, lồng nhau như JSON: `device`, `user`, `process`, `file`, `network_endpoint`, `metadata`... Object có thể kế thừa object khác: `device` và `network_endpoint` cùng mở rộng từ `endpoint`, nên cùng có `hostname`, `ip`, `mac`, `os`.
- **Dùng để**: mô tả một *thực thể* (máy, người, tiến trình, tệp) theo một cách duy nhất ở mọi class, nên gom được mọi event của một máy hay một user mà không cần biết class.

### Category, class, activity và `type_uid`
- **Category**
  - **Là gì**: nhóm class theo lĩnh vực: System Activity (1), Findings (2), Identity & Access Management (3), Network Activity (4), Discovery (5), Application Activity (6), Remediation (7), Unmanned Systems (8).
  - **Dùng để**: gom các class cùng miền để tìm kiếm, báo cáo, phân vùng lưu trữ, phân quyền. Category chỉ là nhóm; nó không quy định cấu trúc bản ghi.
- **Class (event class)**
  - **Là gì**: một loại bản ghi với tập attribute, mức bắt buộc và enum riêng. Mỗi event là một *instance* của một class. `class_uid = category_uid × 1000 + n`: Process Activity `1007`, Detection Finding `2004`, Authentication `3002`, Network Activity `4001`, Device Inventory Info `5001`.
  - **Dùng để**: biết class là biết bản ghi *có những field nào* và *nghĩa của chúng*; lọc và đếm theo loại sự việc mà không phụ thuộc nguồn.
- **Activity**
  - **Là gì**: hành động cụ thể trong class (`activity_id`, enum riêng của từng class). Process Activity có Launch, Terminate, Open, Inject; Authentication có Logon, Logoff, Authentication Ticket...
  - **Dùng để**: phân biệt các hành động dùng *chung một cấu trúc bản ghi*, không phải tạo class cho mỗi hành động.
- **`type_uid = class_uid × 100 + activity_id`**
  - **Là gì**: một số duy nhất trên toàn schema cho cặp "class + activity", vd Process Launch `100701`, Logon `300201`.
  - **Dùng để**: một khóa duy nhất cho "một loại sự việc" (thống kê, ánh xạ sang detection) mà không cần đọc kèm field khác.
- **Ba kiểu class chính** theo bản chất dữ liệu: *activity* (một việc đã xảy ra: System, IAM, Network, Application); *finding* (một kết luận rút ra từ xử lý một hay nhiều event: phát hiện, lỗ hổng, vi phạm tuân thủ); *discovery/inventory* (trạng thái của một thứ tại một thời điểm: máy, phần mềm, user). Cùng một schema nên log, alert và dữ liệu tài sản nối được với nhau.

### Kế thừa giữa các tầng
- **Là gì**: mọi class kế thừa *base event* (`time`, `severity_id`, `metadata`, `observables`, `unmapped`...); class trong một category kế thừa thêm phần chung của category (mọi class Network có `src_endpoint`, `dst_endpoint`, `connection_info`). Class chỉ khai báo phần riêng. OCSF không có "class con của class": kế thừa chỉ để dựng định nghĩa, còn event thì mang `class_uid` của đúng một class cụ thể.
- **Dùng để**: field chung luôn có mặt và cùng nghĩa, nên một truy vấn trên `time` hay `src_endpoint.ip` chạy được trên mọi event mạng.

### Requirement và constraint
- **Là gì**: mỗi attribute trong class có mức *required*, *recommended* hoặc *optional*; mức này thuộc về class, không thuộc về attribute (cùng `device` có thể required ở class này, recommended ở class khác). *Constraint* ràng buộc theo nhóm: `at_least_one` (vd Authentication cần ít nhất một trong `service`, `dst_endpoint`; một endpoint cần ít nhất một trong `ip`, `hostname`, `uid`, `name`...) và `just_one`.
- **Dùng để**: định nghĩa mức tối thiểu để bản ghi có nghĩa và đo được chất lượng dữ liệu. Base event bắt buộc mọi event có `class_uid`, `category_uid`, `activity_id`, `type_uid`, `time`, `severity_id`, `metadata`.

### Enum: cặp `_id` và caption
- **Là gì**: attribute liệt kê đi theo cặp số và chữ: `severity_id`/`severity`, `status_id`/`status`, `activity_id`/`activity_name`. Quy ước: `0` là Unknown, `99` là Other.
- **Dùng để**: số ổn định cho máy lọc; chữ cho người đọc. "Không biết" vẫn là giá trị hợp lệ (`0`), nên attribute required không bị bỏ trống; với `99` Other, caption giữ chuỗi gốc của nguồn để không mất nghĩa.

### Profile
- **Là gì**: một **nhóm attribute trộn thêm (mix-in)**, có tên, được *áp tùy chọn* vào một event (hoặc vào một object bên trong event) khi ngữ cảnh phù hợp. Profile được định nghĩa một lần và class/object nào muốn nhận thì *đăng ký* nó trong định nghĩa của mình. Event áp profile nào thì ghi tên profile đó vào `metadata.profiles` (profile lõi ghi `name`, profile của extension ghi `extension/name`). Một event áp được nhiều profile cùng lúc.

  | Profile | Thêm attribute | Áp khi |
  |---|---|---|
  | `host` | `device`, `actor` | event được ghi nhận trên một máy và biết ai/tiến trình nào làm |
  | `security_control` | `action_id`, `disposition_id`, `is_alert`, `malware`, `attacks`, `policy`, `firewall_rule`, `risk_level_id`... | nguồn là một control (AV, IPS, firewall, DLP, điểm thực thi phân quyền) và có phán quyết |
  | `cloud` | `cloud`, `api` | sự việc xảy ra trên nền tảng cloud |
  | `container` | `container`, `namespace_pid` | tiến trình hay endpoint nằm trong container (áp vào object `process`, `endpoint`) |
  | `network_proxy`, `load_balancer` | `proxy_*`, `load_balancer` | kết nối đi qua proxy, load balancer |
  | `incident` | `assignee`, `priority_id`, `verdict_id`, `ticket`... | finding được quản lý như một vụ việc |
  | `osint`, `datetime` | `osint`; bản sao chuỗi RFC 3339 `*_dt` cạnh mỗi `timestamp_t` | có chỉ báo tình báo; cần thời gian dễ đọc |

- **Dùng để**: mô tả một khía cạnh *cắt ngang* nhiều class (máy, control, cloud) theo một cách duy nhất, thay vì mỗi class tự định nghĩa hay phải sinh class mới cho mỗi tổ hợp. Profile cũng là một **trục phân loại thứ hai**: event áp `security_control` vừa là một File System Activity, vừa là "một event của security control", nên truy vấn `security_control ∈ metadata.profiles` lấy được mọi phán quyết của control trên mọi class.

### Extension
- **Là gì**: một **gói định nghĩa schema** nằm ngoài schema lõi, có `name`, `uid` và `version` riêng (uid đăng ký trong registry chung để không trùng). Gói này có cấu trúc như schema lõi và có thể chứa attribute mới (dictionary riêng), object, class, category (uid từ 30 trở lên), profile mới, hoặc **vá** class/object lõi (thêm attribute vào thẳng chúng mà không tạo class mới). Class và category của extension có uid được dịch theo uid của extension nên không trùng với lõi. Schema chính thức kèm ba extension nền tảng: `linux` (uid 1), `win` (uid 2), `macos` (uid 3). Event dùng extension nào thì ghi vào `metadata.extensions` (mỗi phần tử gồm `name`, `uid`, `version`).
- **Dùng để**: vendor hay tổ chức bổ sung thứ lõi chưa có (dữ liệu đặc thù hệ điều hành, sản phẩm, pipeline enrichment nội bộ) mà không sửa và không phá lõi; cũng là nơi thử nghiệm thứ sau này có thể được đưa vào lõi. Ví dụ: `win` thêm class Registry Key Activity (thuộc category System Activity); `linux` vá object `process` để nhận profile `linux/linux_users` (thêm `euid`, `egid`, `auid`, `group`).

### Phiên bản
- **Là gì**: schema đánh số theo SemVer; mỗi event ghi phiên bản schema nó theo trong `metadata.version` (required). Trong cùng major (1.x), bản sau chỉ thêm, không bỏ hay đổi nghĩa; thứ cũ được đánh dấu *deprecated* trước khi bỏ ở major sau. Extension có phiên bản riêng.
- **Dùng để**: bên đọc biết phải hiểu event theo định nghĩa nào; schema tiến hóa mà dữ liệu cũ vẫn đọc được.

## Cách hoạt động

### Một event được lắp từ các tầng
```
Base event      time, severity_id, metadata, observables, enrichments, unmapped, raw_data
 + Category     (vd Network)  src_endpoint, dst_endpoint, connection_info, traffic
 + Class        (vd Network Activity 4001)  phần riêng của class          ← đúng 1 class
 + Profile(s)   host → device, actor · security_control → action_id...   ← 0..n, chỉ profile class đã đăng ký
 + Extension(s) attribute/object/profile từ extension (nếu có)            ← 0..n
 ──────────────────────────────────────────────────────────────────────
 = một event: mọi attribute tham chiếu dictionary, có kiểu, có mức bắt buộc
```

### Ba trục của một event
```
                    ┌─ Loại bản ghi: category → class → activity   (đúng 1; type_uid)
Một event OCSF  ────┼─ Khía cạnh thêm: profile                     (0..n; metadata.profiles)
                    └─ Nguồn định nghĩa: lõi + extension            (0..n; metadata.extensions)
```
Ba trục độc lập: đổi profile không đổi class; dùng extension không bắt buộc đổi class (extension vá lõi thì event vẫn là class lõi); một profile có thể nằm trong lõi hoặc trong extension.

### Profile được áp như thế nào
1. Người viết schema định nghĩa profile (tên + attribute + mức bắt buộc).
2. Class, category hay object *đăng ký* profile. Base event đăng ký `host`, `security_control`, `cloud`, `osint`, `datetime`, `record_integrity`, nên mọi class nhận được các profile này; profile như `network_proxy` chỉ đăng ký ở category Network và vài class Application; `container` đăng ký ở object `process` và `endpoint`.
3. Producer hay mapper quyết định *từng event* có áp không: điền attribute của profile và ghi tên vào `metadata.profiles`.
4. Một số class đã có sẵn attribute của profile (category System định nghĩa thẳng `device`, `actor` là required). Class vẫn đăng ký profile để truy vấn theo profile khớp; khi đó mức bắt buộc của class được ưu tiên.

## Ví dụ
Agent EDR trên máy Linux `srv-web-01` chặn tiến trình `curl` (chạy với euid 1000) mở kết nối tới một IP độc hại.

```json
{
  "category_uid": 4, "class_uid": 4001, "activity_id": 1, "type_uid": 400101,
  "time": 1761638400000, "severity_id": 3,
  "src_endpoint": { "ip": "10.0.5.21" },
  "dst_endpoint": { "ip": "203.0.113.50", "port": 443 },
  "device": { "hostname": "srv-web-01" },
  "actor": { "process": { "name": "curl", "pid": 4242, "euid": 1000 } },
  "action_id": 2, "disposition_id": 2, "is_alert": true,
  "metadata": {
    "version": "1.9.0", "product": { "name": "EDR" },
    "profiles": [ "host", "security_control", "linux/linux_users" ],
    "extensions": [ { "name": "linux", "uid": "1", "version": "1.9.0" } ]
  }
}
```

| Thành phần | Ở đâu trong event | Đóng góp gì |
|---|---|---|
| 1 class | `class_uid 4001`, `activity_id 1` → `type_uid 400101` | đây là Network Activity: Open; quyết định có `src_endpoint`, `dst_endpoint` |
| profile `host` | `device`, `actor` | Network Activity vốn không có hai field này; profile thêm máy ghi nhận và tiến trình gây ra |
| profile `security_control` | `action_id 2` Denied, `disposition_id 2` Blocked, `is_alert` | phán quyết của control: đã chặn, cần chú ý |
| extension `linux` + profile `linux/linux_users` | `actor.process.euid` | `euid` không có trong `process` lõi; extension vá `process`, profile của nó thêm field |

Một sự việc, một class, ba profile, một extension. Truy vấn theo `class_uid = 4001` lấy được event này cùng mọi kết nối mạng khác; truy vấn theo `security_control ∈ metadata.profiles` lấy được nó cùng mọi phán quyết control ở class khác (file bị AV chặn, đăng nhập bị từ chối...).

## Câu hỏi và trả lời

**Một log OCSF có thể thể hiện nhiều class hay chỉ một class?**
Mỗi event OCSF là instance của đúng một class, nên có đúng một `class_uid`, một `activity_id`, một `type_uid` và một `category_uid` (mỗi class chỉ thuộc một category); ngược lại, số profile và số extension của một event là từ 0 đến nhiều. OCSF thiết kế để mọi event nguồn map vào *một* class nhờ ghép thành phần thay vì đa kế thừa: khía cạnh thứ hai của sự việc được thêm bằng profile. Vì vậy một lần mở file bị antivirus chặn là *một* File System Activity áp `security_control`, không phải File System Activity cộng thêm một class "malware"; kết nối bị EDR chặn trong [ví dụ](#ví-dụ) là một Network Activity với ba profile. Điều dễ nhầm: profile cũng là một trục phân loại (event "là một" event của security control), nên tìm theo profile ra được event của nhiều class, nhưng bản thân mỗi event vẫn chỉ có một class.

**Profile với extension khác nhau thế nào?**
Tiêu chí phân biệt: profile trả lời "*event này có thêm khía cạnh nào*", được chọn cho từng event; extension trả lời "*định nghĩa này đến từ đâu*", là một gói schema nằm ngoài lõi. Cụ thể:

| | Profile | Extension |
|---|---|---|
| Bản chất | một nhóm attribute trộn vào class/object | một gói định nghĩa có `name`, `uid`, `version` |
| Chứa được | chỉ attribute (với mức bắt buộc) | attribute, object, class, category, profile; hoặc vá class/object lõi |
| Tạo loại bản ghi mới? | không, event giữ class cũ | có thể (class mới với uid riêng), hoặc không (khi chỉ vá lõi) |
| Ai quyết định dùng | producer/mapper, từng event | người dựng schema nạp extension; event dùng định nghĩa của nó |
| Ghi ở đâu trong event | `metadata.profiles` | `metadata.extensions` |
| Ai hiểu được | mọi bên hiểu schema có profile đó | chỉ bên đã nạp extension |

Hai khái niệm khác tầng nên không loại trừ nhau: profile có thể nằm trong lõi (`host`) hoặc trong extension (`linux/linux_users`), và extension có thể vừa vá lõi vừa định nghĩa profile mới.

**Muốn đưa thêm thông tin vào event thì dùng cơ chế nào: class khác, profile, extension hay `unmapped`?**
Quy tắc: chọn theo việc thông tin đó *đổi loại sự việc*, *là một khía cạnh lặp lại ở nhiều class*, *là định nghĩa schema lõi chưa có*, hay *chỉ là dữ liệu thừa của một nguồn*. Đổi loại sự việc (từ "mở kết nối" sang "kết luận sau phân tích") thì là class khác, tức một event khác. Khía cạnh lặp lại ở nhiều class (máy, control, cloud) thì là profile đã có. Attribute, object hay class mà lõi chưa có và cần được kiểm tra kiểu thì định nghĩa trong extension; tài liệu OCSF khuyên producer gốc đi đường này. Field riêng của nguồn mà mapper không có chỗ đặt thì để trong `unmapped`: không mất dữ liệu, nhưng cũng không được kiểm tra kiểu và không ai khác hiểu được. Ranh giới: không có "field tự do" ở cấp cao nhất của event. Cấu trúc class quy định attribute nào được phép có, và áp profile chính là "xin phép" thêm attribute của nó; field nằm ngoài class, profile và extension đã dùng thì không phải OCSF hợp lệ, chỗ của nó là `unmapped`.

**Một log nguồn mô tả nhiều việc, hay một alert tổng hợp từ nhiều log, thì thành mấy event?**
Quy tắc: một event OCSF ứng với một sự việc của một class, nên số event bằng số sự việc, không bằng số dòng log. Một dòng log chỉ một việc thì thành một event. Một bản ghi nguồn gói nhiều việc khác nhau (máy quét lỗ hổng báo bắt đầu quét, kết thúc quét và từng lỗ hổng tìm thấy) thì tách thành nhiều event, nối với nhau bằng cùng `metadata.correlation_uid`. Một kết luận rút ra từ phân tích nhiều event (SIEM tương quan, UEBA) là một event *mới* thuộc class Findings (vd Detection Finding), trỏ về event gốc qua `finding_info.related_events`. Ranh giới: alert *không* nhất thiết là finding. Alert của một control tại chỗ (AV chặn file, firewall chặn kết nối) là event hoạt động áp `security_control` với `is_alert: true`; Detection Finding dành cho kết luận có vòng đời (Create, Update, Close) sau khi phân tích.

**Khi nào là một activity mới, khi nào là một class mới?**
Quy tắc: class định nghĩa *cấu trúc* bản ghi (tập attribute), activity phân biệt *hành động* trong cùng cấu trúc đó; hành động nào mô tả được bằng cùng tập attribute thì là activity, cần tập attribute khác thì là class khác. Process Launch và Process Terminate cùng mô tả bằng `process`, `actor`, `device`, nên là hai activity của Process Activity; DNS cần `query`, `answers` nên có class DNS Activity riêng thay vì là một activity của Network Activity. Hệ quả: `activity_id` chỉ có nghĩa trong class của nó (`1` là Launch ở Process Activity nhưng là Logon ở Authentication), nên khi so giữa các class phải dùng `type_uid`.

**Vì sao OCSF dùng profile thay vì tạo thêm class?**
Vì các khía cạnh như "xảy ra trên một máy", "do control phán quyết", "trên cloud" cắt ngang hầu hết class; tạo class cho mỗi tổ hợp (File Activity có malware, Network Activity trên host có malware, trên cloud...) sẽ làm số class bùng nổ và mỗi khía cạnh bị định nghĩa lặp lại nhiều nơi. Profile chọn đánh đổi ngược lại: giữ một class cho mỗi loại sự việc, định nghĩa mỗi khía cạnh một lần, rồi trộn vào khi cần. Cái giá là event cùng class có thể khác nhau về field có mặt, nên bên đọc phải xem `metadata.profiles` để biết một event có những khía cạnh nào.

**Event có áp được profile bất kỳ không, và áp rồi thì field của profile có bắt buộc không?**
Quy tắc: một event chỉ áp được profile mà class của nó (hoặc base event, category, object bên trong nó) đã đăng ký; profile luôn là tùy chọn, nhưng đã áp thì mức bắt buộc khai báo trong profile có hiệu lực. Mọi class nhận được `host` và `security_control` vì base event đăng ký chúng; `network_proxy` chỉ áp được cho class mạng và vài class Application đã đăng ký. Áp `host` thì `device` là recommended theo profile. Ranh giới: khi class đã định nghĩa sẵn attribute của profile (category System có `device`, `actor` là required), mức của class được ưu tiên, nên ở System Activity hai field này bắt buộc dù có ghi `host` hay không.

**Nhìn vào một event, làm sao biết nó thuộc class nào, dùng profile, extension và phiên bản nào?**
Quy tắc: phân loại nằm ở các field phân loại của base event, còn những gì đã "trộn" vào event nằm trong `metadata`. Class và hành động: `class_uid`, `activity_id`, hoặc gộp trong `type_uid` (`400101` = Network Activity: Open). Profile: `metadata.profiles`. Extension: `metadata.extensions`; nếu là class của extension thì `class_uid` nằm ngoài dải uid của lõi vì đã được dịch theo uid extension. Phiên bản schema: `metadata.version`. Ranh giới: `metadata.profiles` và `metadata.extensions` là optional, nên có thể vắng dù event có field của profile; khi đó suy ra từ field có mặt, và đây là một điểm chất lượng dữ liệu cần kiểm tra.

## Hiểu nhầm thường gặp
- **"OCSF là một định dạng file"**: OCSF là mô hình dữ liệu; có thể biểu diễn bằng JSON, Parquet hay bảng.
- **"Profile là một loại class con"**: profile không có `class_uid` và không thay class; nó chỉ thêm attribute vào class đã chọn.
- **"Extension là một profile lớn"**: extension là gói định nghĩa (có thể chứa profile), profile là cách trộn attribute; khác tầng.
- **"Phải điền hết field"**: chỉ required là bắt buộc; mỗi class có hàng chục attribute cấp cao và hàng trăm đường dẫn lá, phần lớn chỉ có khi nguồn cung cấp.
- **"Field của extension cũng là OCSF chuẩn"**: field trong extension chỉ có nghĩa với bên đã nạp extension đó; dữ liệu trao đổi rộng nên dựa vào lõi.

## Liên quan
- [15-security-data-normalization.md](15-security-data-normalization.md): vì sao cần schema chung, schema hướng class khác schema tập field dùng chung.
- [17-ocsf-event-anatomy.md](17-ocsf-event-anatomy.md): các nhóm field trong một event (gồm field của `security_control`, `finding_info`, `metadata`) và cách đọc.
- [12-incident-response.md](12-incident-response.md): event, alert, incident; đối chiếu với finding và `is_alert`.
- [18-asset-inventory-and-profile.md](18-asset-inventory-and-profile.md): class inventory và object `device` trong quản lý tài sản.
