# OCSF data model

> OCSF dựng schema từ một số thành phần cố định: dictionary attribute, kiểu dữ liệu, object, cây phân loại category → class → activity, mức bắt buộc, enum, profile, extension và phiên bản. Mỗi thành phần giải một vấn đề cụ thể của việc mô tả dữ liệu bảo mật từ nhiều nguồn.

## Tại sao cần biết
Biết từng thành phần dùng để làm gì thì đọc được mọi class OCSF, kể cả class chưa gặp, và hiểu vì sao dữ liệu đã chuẩn hóa so sánh được với nhau. File này mô tả *khung* của schema. Những gì một event cụ thể chứa nằm ở [17-ocsf-event-anatomy.md](17-ocsf-event-anatomy.md).

## Khái niệm cốt lõi

### Dictionary và attribute
- **Là gì**: dictionary là danh sách *mọi* attribute của schema. Mỗi attribute có tên, kiểu, mô tả; class và object chỉ *tham chiếu* attribute từ dictionary, không tự định nghĩa lại.
- **Dùng để**: bảo đảm một tên chỉ có một nghĩa ở khắp nơi. `hostname` trong `device`, trong `src_endpoint` hay trong `dst_endpoint` đều là cùng một khái niệm, cùng kiểu.

### Kiểu dữ liệu (data type)
- **Là gì**: kiểu cơ bản (`string_t`, `integer_t`, `long_t`, `float_t`, `boolean_t`, `json_t`) và kiểu có ngữ nghĩa dựa trên kiểu cơ bản: `timestamp_t` (epoch milliseconds UTC), `ip_t`, `mac_t`, `hostname_t`, `port_t`, `url_t`, `email_t`, `file_hash_t`, `file_path_t`, `username_t`, `uuid_t`...
- **Dùng để**:
  - kiểm tra giá trị hợp lệ (một IP phải là IP);
  - so sánh và tính toán đúng (thời gian từ mọi nguồn cùng đơn vị, cùng múi giờ);
  - nhận diện thực thể: nhiều kiểu được gắn sẵn loại *observable* (hostname, IP, MAC, hash...), nhờ đó có thể tự động gom các thực thể đáng chú ý của event.

### Object
- **Là gì**: một nhóm attribute có cấu trúc, dùng lại được, lồng vào nhau như JSON. Ví dụ `device`, `user`, `process`, `file`, `network_endpoint`, `metadata`. Object có thể *kế thừa* object khác: `device` và `network_endpoint` cùng mở rộng từ `endpoint`, nên cùng có `hostname`, `ip`, `mac`, `os`, `owner`.
- **Dùng để**: mô tả một *thực thể* (máy, người, tiến trình, tệp) theo một cách duy nhất ở mọi class. Phân tích lấy thực thể làm trung tâm (gom mọi event của một máy, một user) dựa trên điều này.

### Category, class, activity và `type_uid`
- **Category**: nhóm lớn theo lĩnh vực: System Activity (1), Findings (2), Identity & Access Management (3), Network Activity (4), Discovery (5), Application Activity (6), Remediation (7)...
- **Class**: một loại bản ghi với tập attribute riêng. `class_uid = category_uid × 1000 + n`, vd Process Activity `1007`, Detection Finding `2004`, Authentication `3002`, Network Activity `4001`, Device Inventory Info `5001`.
- **Activity**: hành động cụ thể trong class (`activity_id`). Process Activity có Launch, Terminate, Open, Inject; Authentication có Logon, Logoff, Authentication Ticket...
- **`type_uid = class_uid × 100 + activity_id`**: một số duy nhất trên toàn schema cho cặp "loại + hành động", vd Process Launch `100701`, Logon `300201`.
- **Dùng để**:
  - biết class là biết bản ghi *có những field nào* và *nghĩa của chúng*;
  - lọc và đếm theo loại sự việc mà không phụ thuộc nguồn;
  - `type_uid` làm khóa cho mọi thứ gắn với "một loại sự việc": khuôn mô tả, thống kê tần suất, ánh xạ sang detection.
- **Ba kiểu class** theo bản chất dữ liệu:
  - *activity*: một việc đã xảy ra (System, IAM, Network, Application);
  - *finding*: một kết luận về việc đã xảy ra: alert, lỗ hổng, vi phạm tuân thủ (category Findings);
  - *discovery/inventory*: trạng thái của một thứ tại một thời điểm: máy, phần mềm, user (category Discovery).

  Ba kiểu cùng một schema nên log, alert và dữ liệu tài sản nối được với nhau trực tiếp.

### Kế thừa giữa các tầng
- **Là gì**: mọi class kế thừa *base event* (các field chung như `time`, `severity_id`, `metadata`); class trong một category kế thừa thêm field chung của category đó (vd mọi class Network có `src_endpoint`, `dst_endpoint`, `connection_info`). Class chỉ khai báo phần riêng của mình.
- **Dùng để**: các field chung luôn có mặt và cùng nghĩa ở mọi class, nên một truy vấn trên `time` hay `src_endpoint.ip` chạy được trên mọi event mạng.

### Requirement và constraint
- **Là gì**: mỗi attribute trong class có mức *required* (bắt buộc), *recommended* (nên có), *optional*. *Constraint* ràng buộc theo nhóm, vd Authentication cần ít nhất một trong `service` hoặc `dst_endpoint`; một endpoint cần ít nhất một trong `ip`, `hostname`, `uid`, `name`...
- **Dùng để**: định nghĩa mức tối thiểu để một bản ghi có nghĩa, và đo được chất lượng dữ liệu (bản ghi thiếu field bắt buộc là bản ghi lỗi).

### Enum: cặp `_id` và caption
- **Là gì**: attribute liệt kê đi theo cặp: `severity_id` (số) và `severity` (chữ), `status_id`/`status`, `activity_id`/`activity_name`. Quy ước chung: `0` là Unknown, `99` là Other (khi đó caption giữ chuỗi gốc của nguồn).
- **Dùng để**: số ổn định cho máy lọc và so sánh; chữ cho người đọc; `99` giữ được giá trị nguồn không khớp danh sách mà không làm sai nghĩa.

### Profile
- **Là gì**: một nhóm attribute được "gắn thêm" vào class khi ngữ cảnh phù hợp, không cần tạo class mới. Ví dụ:
  - `host`: thêm `device` và `actor`, cho event xảy ra trên một máy;
  - `security_control`: thêm hành động và kết luận của control (`action_id`, `disposition_id`, `is_alert`...);
  - `cloud`, `container`: thêm thông tin tài khoản cloud, container;
  - `osint`, `datetime`: thêm chỉ báo tình báo, thời gian dạng chuỗi dễ đọc.

  Profile đã dùng được ghi trong `metadata.profiles`.
- **Dùng để**: một khía cạnh chung (máy, cloud, control) được mô tả giống nhau ở mọi class có khía cạnh đó, thay vì mỗi class tự định nghĩa.

### Extension
- **Là gì**: phần mở rộng có `uid` và tên riêng, thêm category, class, object, attribute hay profile mới. Schema chính thức đi kèm extension `linux`, `macos`, `windows` cho dữ liệu đặc thù hệ điều hành.
- **Dùng để**: vendor hay tổ chức bổ sung thứ schema lõi chưa có mà không phá tương thích; schema lõi giữ gọn.

### Phiên bản
- **Là gì**: schema đánh số theo SemVer; mỗi bản ghi ghi phiên bản mình theo trong `metadata.version`. Field cũ được đánh dấu *deprecated* trước khi bỏ.
- **Dùng để**: bên đọc biết phải hiểu bản ghi theo định nghĩa nào; schema tiến hóa mà dữ liệu cũ vẫn đọc được.

## Cách hoạt động
Một class hoàn chỉnh được lắp từ các tầng:

```
Base event          time, severity_id, status_id, metadata, observables, enrichments, unmapped, raw_data
 + Category         (vd IAM)  actor, src_endpoint
 + Class            (vd Authentication 3002)  user, dst_endpoint, logon_type_id, auth_protocol_id, is_mfa...
 + Profile          host → device · security_control → action_id, disposition_id · cloud → cloud
 + Extension        (nếu có) field riêng của vendor/tổ chức
 ───────────────────────────────────────────────────────────
 = Bản ghi Authentication: mọi attribute đều tham chiếu từ dictionary, có kiểu, có mức bắt buộc
```

## Ví dụ
Vì `user`, `device`, `src_endpoint` là object dùng chung, cùng câu hỏi "user `lan.nguyen` đã làm gì trên máy `WS-0412`?" áp được cho Authentication (`3002`), Process Activity (`1007`), File System Activity (`1001`), Detection Finding (`2004`). Bốn class khác nhau, nhưng máy luôn ở `device.hostname` và người luôn ở `actor.user.name` hoặc `user.name`. Chỉ cần `class_uid` để biết phần còn lại của bản ghi nói về process, tệp hay alert.

## Câu hỏi và trả lời

**Một log OCSF có thể thể hiện nhiều class hay chỉ một class?**
Mỗi event OCSF là đúng một bản ghi của một class: một `class_uid`, một `activity_id`, và vì `class_uid` mã hóa category nên cũng đúng một `category_uid`. Tài liệu OCSF nêu rõ mục tiêu thiết kế là mọi event nguồn map được vào *một* class, nhờ ghép thành phần (composition) thay vì đa kế thừa. Một lần đăng nhập là một event Authentication, activity Logon. Một sự việc có nhiều khía cạnh (truy cập file và bị antivirus chặn) vẫn là một class (File System Activity); khía cạnh còn lại được thêm bằng profile (`security_control`), không bằng class thứ hai. Kết luận rút ra từ nhiều event (một finding của SIEM) là một event *khác*, thuộc class Finding, và trỏ về các event gốc.

**Category, class và activity quan hệ với nhau thế nào?**
Đó là một cây: mỗi class thuộc đúng một category, mỗi activity thuộc đúng một class. Giá trị `activity_id` chỉ có nghĩa bên trong class của nó: `1` là Launch ở Process Activity nhưng là Logon ở Authentication. Vì vậy mới cần `type_uid = class_uid × 100 + activity_id`, một số mang đủ nghĩa mà không cần nhìn field khác.

**Profile và extension khác nhau thế nào?**
Profile là một *cách gắn* nhóm attribute vào class khi ngữ cảnh phù hợp; extension là một *nguồn định nghĩa* mới nằm ngoài schema lõi. Profile không tạo loại bản ghi mới: event vẫn thuộc class cũ, chỉ có thêm field (`host` thêm `device`, `actor`). Extension có thể thêm attribute, object, class, cả profile mới. Hai khái niệm không loại trừ nhau: vendor có thể định nghĩa một profile trong extension của mình.

**Có được thêm field mà class không định nghĩa không?**
Một event chỉ hợp lệ với các attribute mà class định nghĩa, gồm cả phần kế thừa từ base event, từ category và từ các profile đã áp. Dữ liệu nằm ngoài tập đó đi vào `unmapped`, hoặc được định nghĩa qua extension. Không có "field tự do" ở cấp cao nhất của event.

**Required nghĩa là gì khi nguồn không có giá trị?**
Required là điều kiện tối thiểu để bản ghi có nghĩa: thiếu nó thì bản ghi không hợp lệ. Với attribute liệt kê, "không biết" vẫn là một giá trị hợp lệ (`0` Unknown), nên điền `0` chứ không bỏ trống. Với `99` Other, caption giữ chuỗi gốc của nguồn để không mất nghĩa.

**Vì sao một thực thể (máy, user) được mô tả giống nhau ở mọi class?**
Vì class không tự định nghĩa field mà tham chiếu dictionary và object dùng chung. `device` trong Authentication và trong Process Activity là cùng một object, cùng attribute. Nhờ đó gom được mọi event của một máy hay một user mà không cần biết class.

## Hiểu nhầm thường gặp
- **"OCSF là một định dạng file"**: OCSF là mô hình dữ liệu; có thể biểu diễn bằng JSON, Parquet hay bảng.
- **"Phải điền hết field"**: chỉ required là bắt buộc; mỗi class có hàng chục attribute cấp cao và hàng trăm đường dẫn lá, phần lớn chỉ có khi nguồn cung cấp.
- **"Extension là OCSF"**: field trong extension chỉ có nghĩa với bên hiểu extension đó; dữ liệu trao đổi rộng nên dựa vào schema lõi.

## Liên quan
- [15-security-data-normalization.md](15-security-data-normalization.md): vì sao cần schema chung.
- [17-ocsf-event-anatomy.md](17-ocsf-event-anatomy.md): các nhóm field trong một event và cách đọc.
- [18-asset-management.md](18-asset-management.md): class inventory và object `device` trong quản lý tài sản.
