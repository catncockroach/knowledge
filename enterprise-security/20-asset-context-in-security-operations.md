# Asset context in security operations

> Khi log đã chuẩn hóa và mang ngữ cảnh tài sản, cùng một lớp dữ liệu phục vụ cả ba mảng của bảo mật: phòng ngừa (biết có gì, hở ở đâu), phát hiện (điều gì đáng lo, điều gì bất thường) và ứng phó (của ai, lan đến đâu, xử lý thế nào).

## Tại sao cần biết
Một sự kiện tự nó không mang mức độ rủi ro. Rủi ro là tổ hợp của *threat*, *vulnerability* và *asset* ([01-security-fundamentals.md](01-security-fundamentals.md)): cùng một hành vi, trên máy lab và trên domain controller là hai mức rủi ro khác hẳn. Ngữ cảnh tài sản là thành phần "asset" trong phép tính đó. Đây là lý do asset management là ứng dụng cốt lõi của dữ liệu đã chuẩn hóa, chứ không chỉ là việc của bộ phận IT.

## Khái niệm cốt lõi
- **Phòng ngừa: biết mình có gì và hở ở đâu**
  - *Tài sản chưa được quản lý*: máy xuất hiện trong log nhưng không có trong lớp khai báo (shadow IT, thiết bị lạ).
  - *Độ phủ control*: tài sản nào thiếu EDR, thiếu log, thiếu MDM. Nhìn từ góc "cảm biến nào thấy máy này".
  - *Ưu tiên lỗ hổng*: mức nghiêm trọng của lỗ hổng × criticality × mức phơi ra ngoài × phần mềm có *thực sự chạy* hay chỉ được cài ([06-vulnerability-management.md](06-vulnerability-management.md)).
  - *Bề mặt tấn công*: dịch vụ đang lắng nghe, tài sản nhận kết nối từ internet, so với những gì được khai báo.
  - *Tuân thủ*: bằng chứng cho yêu cầu inventory của NIST CSF (ID.AM) và CIS Controls 1, 2.
- **Phát hiện: điều gì đáng lo, điều gì bất thường**
  - *Severity khác priority*: severity là đánh giá của rule; priority là thứ tự xử lý, có tính criticality của tài sản ([08-siem.md](08-siem.md)). Risk-based alerting cộng dồn rủi ro theo tài sản.
  - *Bất thường so với baseline*: user lần đầu đăng nhập máy, process lần đầu chạy, cổng mới mở, hoạt động ngoài giờ, máy trạm kết nối tới nhiều máy khác. Đều là "lệch khỏi lớp hành vi" của profile.
  - *Logic theo vai trò tài sản*: rule và ngoại lệ dựa trên nhóm tài sản (máy quét, jump host, Tier 0) thay vì danh sách IP; đây cũng là một nguồn chính để giảm false positive ([09-detection-engineering.md](09-detection-engineering.md)).
  - *Thay đổi trạng thái*: agent EDR ngừng báo về trong khi mạng vẫn thấy máy; máy đổi tên hay đổi OS đột ngột.
- **Ứng phó: của ai, lan đến đâu, xử lý thế nào**
  - *Triage*: alert đến kèm owner, đơn vị, criticality, trạng thái control.
  - *Trách nhiệm*: biết owner thì biết ai xác nhận hành vi là hợp lệ hay không, ai cần được báo.
  - *Timeline*: gom sự kiện theo tài sản quanh thời điểm sự cố, đối chiếu với "bình thường" của chính tài sản đó.
  - *Scoping (blast radius)*: tài sản nào khác có cùng dấu vết, cùng user, từng kết nối tới tài sản bị chiếm ([12-incident-response.md](12-incident-response.md)).
  - *Containment tương xứng*: cô lập một laptop gần như không ảnh hưởng nghiệp vụ; cô lập server Critical cần cân nhắc và phê duyệt ([13-soar-xdr-and-automation.md](13-soar-xdr-and-automation.md)).
- **Đo lường**: số tài sản chưa quản lý, % độ phủ control, thời gian phát hiện và xử lý tách theo criticality.

## Cách hoạt động
```
                        log đã chuẩn hóa + ngữ cảnh tài sản
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
   Phòng ngừa                      Phát hiện                      Ứng phó
   có gì, hở ở đâu                 đáng lo, bất thường            của ai, lan đến đâu
        │                              │                              │
        └──── phản hồi: sửa khai báo, tuning rule, thêm nguồn log ────┘
```
Vòng phản hồi làm chính lớp dữ liệu tốt lên: điều tra phát hiện CMDB sai thì sửa CMDB; rule bắn nhầm vì thiếu ngữ cảnh thì bổ sung ngữ cảnh.

## Ví dụ
Hai alert cùng loại "PowerShell mã hóa", cùng severity High:
- Alert A trên máy lab của đội phát triển, criticality Low, owner xác nhận đang thử script. Đây là benign true positive.
- Alert B trên máy chủ backup, criticality Critical, không có lịch sử chạy PowerShell, tài khoản thực thi chưa từng đăng nhập máy này.

Không có ngữ cảnh, hai alert xếp hàng như nhau. Có ngữ cảnh, B được xử lý ngay, phạm vi điều tra mở rộng sang các máy tài khoản đó từng đăng nhập, và việc cô lập máy được cân nhắc theo ảnh hưởng nghiệp vụ của máy chủ backup.

## Câu hỏi và trả lời

**Severity khác priority thế nào?**
Severity là thuộc tính của *sự việc* theo đánh giá của nguồn; priority là *quyết định của tổ chức* về thứ tự xử lý. Priority tổ hợp severity với criticality của tài sản, độ tin cậy của phát hiện và ngữ cảnh khác. Hai alert cùng severity vì thế có thể có priority rất khác nhau, như phần Ví dụ.

**Ngữ cảnh tài sản giảm false positive bằng cách nào?**
Ngữ cảnh không làm logic rule đúng hơn. Nó giúp phân biệt hành vi *có thật nhưng hợp lệ* (benign true positive) với hành vi đáng lo. Rule bắn đúng hành vi đã mô tả, chẳng hạn công cụ quản trị chạy trên jump host. Ngữ cảnh cho biết với *vai trò của máy này*, hành vi đó là bình thường. Alert do logic rule sai (false positive thật) vẫn phải sửa ở rule ([09](09-detection-engineering.md)).

**Asset management thuộc phòng ngừa, phát hiện hay ứng phó?**
Nó là nền chung của cả ba, nên các framework đặt nó ở bước đầu (Identify trong NIST CSF). Cùng một profile cho phòng ngừa biết cần bảo vệ gì, cho phát hiện biết điều gì là bất thường, cho ứng phó biết ai chịu trách nhiệm và ảnh hưởng đến đâu.

**Thiếu ngữ cảnh tài sản thì chuyện gì xảy ra?**
Hệ thống vẫn chạy, nhưng mọi tài sản bị đối xử như nhau. Ưu tiên chỉ còn dựa vào severity của nguồn. Ngoại lệ phải viết bằng danh sách IP cứng, dễ sai khi IP đổi chủ. Việc tra owner, vai trò máy dồn sang analyst làm tay trong lúc triage.

## Hiểu nhầm thường gặp
- **"Asset management chỉ để báo cáo"**: nó là đầu vào của mọi quyết định ưu tiên, triage và containment.
- **"Có ngữ cảnh thì detection tự tốt lên"**: rule và quy trình phải được thiết kế để *dùng* ngữ cảnh; ngữ cảnh không ai dùng chỉ tốn dung lượng.
- **"Dữ liệu sạch là đích đến"**: dữ liệu sạch là nền móng; giá trị nằm ở các quyết định nó giúp đưa ra.

## Liên quan
- [18-asset-management.md](18-asset-management.md): asset profile là gì.
- [19-asset-context-and-enrichment.md](19-asset-context-and-enrichment.md): ngữ cảnh đến từ đâu và gắn vào event thế nào.
- [11-soc-organization.md](11-soc-organization.md): metric và alert fatigue.
