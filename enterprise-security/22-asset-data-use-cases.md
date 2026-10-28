# Asset data use cases

> Khi mọi nguồn log đã về OCSF, đã enrich và đã dựng được asset profile, cùng một lớp dữ liệu phục vụ được cả ba mảng: phòng ngừa (biết mình có gì, hở ở đâu), phát hiện (alert nào đáng lo, hành vi nào bất thường) và ứng phó (máy này của ai, lan rộng đến đâu, xử lý thế nào).

## Tại sao cần biết
Chuẩn hóa ([15-why-ocsf.md](15-why-ocsf.md)) và dựng profile ([20-asset-profiling-from-ocsf-logs.md](20-asset-profiling-from-ocsf-logs.md)) tốn công. Công sức đó chỉ đáng khi dữ liệu được dùng. Điểm khác biệt của dữ liệu sạch là **một lần đầu tư, nhiều lần dùng**: cùng bảng event OCSF và cùng asset profile trả lời câu hỏi của đội vận hành IT, quản lý lỗ hổng, SOC, IR và ban lãnh đạo, mỗi bên không phải tự thu thập lại.

## Khái niệm cốt lõi

### Chuỗi giá trị

```
Log thô ─► OCSF (sạch, nhất quán) ─► asset profile (khai báo + quan sát + hành vi)
                      ▲                          │
                      └──── enrich event ◄───────┘
                                   │
          ┌────────────────────────┼─────────────────────────┐
     Phòng ngừa                Phát hiện                  Ứng phó
     inventory, độ phủ,        ưu tiên theo tài sản,      triage, định tuyến,
     lỗ hổng, bề mặt tấn công  bất thường so baseline     scoping, containment
          │                        │                         │
          └── phản hồi: sửa CMDB, tuning rule, bổ sung log ──┘
```

### A. Phòng ngừa: biết mình có gì và hở ở đâu

| Ứng dụng | Câu hỏi | Dữ liệu OCSF dùng | Đầu ra |
|---|---|---|---|
| **Phát hiện tài sản chưa khai báo** | Máy nào đang hoạt động mà không ai quản lý? | sighting từ mọi class, DHCP Activity, so với CMDB | Danh sách máy lạ cần tìm owner hoặc chặn (CIS Control 1) |
| **Độ phủ control** | Máy nào thiếu EDR, thiếu log, thiếu MDM? | `metadata.product` theo từng `device` (*seen_by*) | Ma trận tài sản × cảm biến; % độ phủ theo đơn vị |
| **Ưu tiên lỗ hổng** | Lỗ hổng nào vá trước? | Vulnerability Finding × criticality × phơi internet (Network Activity inbound) × phần mềm *thực sự chạy* (Process Activity) | Danh sách vá theo rủi ro thực ([06](06-vulnerability-management.md)) |
| **Quản lý phần mềm** | Phần mềm nào chưa được phép, hết hỗ trợ, đang chạy ở đâu? | Process Activity, Application Lifecycle, Software Inventory Info | Phần mềm trái phép, phiên bản EOL (CIS Control 2) |
| **Bề mặt tấn công** | Dịch vụ nào đang mở, ai kết nối được? | Network Activity (Listen, inbound từ ngoài), `network_scope_id` | Danh sách dịch vụ phơi ra ngoài, so với khai báo |
| **Tuân thủ và kiểm toán** | Có bằng chứng inventory đầy đủ không? | Profile store, lịch sử | Báo cáo cho NIST CSF ID.AM, CIS 1/2 |

### B. Phát hiện: alert nào đáng lo, hành vi nào lạ

| Ứng dụng | Cách làm | Dữ liệu OCSF dùng |
|---|---|---|
| **Ưu tiên theo tài sản** | Mức ưu tiên = severity của alert × criticality của tài sản; cộng dồn điểm rủi ro theo tài sản (risk-based alerting, [08](08-siem.md)) | `severity_id`, ngữ cảnh asset trong `device`/`enrichments`/`resources[]` |
| **Bất thường so với baseline** | So event mới với lớp hành vi của profile: user lần đầu đăng nhập máy này, process lần đầu chạy, cổng mới lắng nghe, hoạt động ngoài giờ, máy trạm kết nối tới nhiều máy khác | Authentication, Process Activity, Network Activity + baseline |
| **Rule theo vai trò tài sản** | Viết rule và ngoại lệ theo nhóm tài sản thay vì danh sách IP cứng: miễn trừ máy quét lỗ hổng, siết chặt với Tier 0 | `device.groups`, `device.type_id`, enrichment |
| **Giảm false positive** | Hành vi "đáng ngờ" là bình thường với vai trò của máy (jump host chạy công cụ quản trị, build server tải nhiều package) → hạ mức hoặc đóng tự động | profile + lịch sử verdict ([09](09-detection-engineering.md)) |
| **Phát hiện thay đổi trạng thái** | EDR ngừng báo về trong khi mạng vẫn thấy máy (agent bị gỡ, bị vô hiệu); máy đổi tên, đổi OS đột ngột | `last_seen` theo từng `metadata.product` |

### C. Ứng phó: của ai, lan đến đâu, xử lý thế nào

| Ứng dụng | Cách làm | Dữ liệu OCSF dùng |
|---|---|---|
| **Triage nhanh** | Alert đến kèm owner, đơn vị, criticality, có EDR không; analyst không phải tra tay | event đã enrich ([21](21-asset-enrichment-in-ocsf.md)) |
| **Định tuyến và SLA** | Case gửi đúng owner/đơn vị; SLA theo criticality | `device.owner`, `device.org`, criticality |
| **Timeline điều tra** | Gom mọi event của một máy theo `device.uid` quanh thời điểm sự cố; so với "bình thường" của máy đó | mọi class, đọc theo [17](17-reading-an-ocsf-event.md) |
| **Scoping, blast radius** | Máy nào khác có cùng hash, cùng domain, cùng user đăng nhập, từng kết nối tới máy bị chiếm? | `observables[]`, Authentication, Network Activity |
| **Quyết định containment** | Laptop thường thì SOAR tự cô lập; server Critical cần phê duyệt vì ảnh hưởng nghiệp vụ | criticality, `device.type_id`, môi trường ([13](13-soar-xdr-and-automation.md)) |

### D. Đo lường và điều hành
- Số tài sản chưa khai báo theo thời gian, % độ phủ EDR theo đơn vị.
- MTTD/MTTR tách theo criticality: alert trên tài sản Critical có được xử lý nhanh hơn không ([11](11-soc-organization.md)).
- Tỷ lệ event được enrich thành công: chỉ số chất lượng của chính lớp dữ liệu.
- Với MSSP nhiều khách hàng: inventory và độ phủ theo từng `tenant_uid` là một dịch vụ cung cấp cho khách hàng.

### E. Đầu vào cho tự động hóa và AI
Event có cấu trúc cố định và ngữ cảnh asset đi kèm là đầu vào tốt cho SOAR playbook, cho model ML (feature ổn định) và cho LLM tóm tắt máy hay alert: thay vì đưa log thô, đưa các field đã chuẩn hóa và profile của máy.

## Cách hoạt động
Một ứng dụng thường đi theo ba bước giống nhau, nên khi đã có lớp dữ liệu chung thì thêm ứng dụng mới chỉ còn là viết thêm truy vấn hay rule:

1. **Chọn class và field** trong bảng OCSF (không phụ thuộc nguồn).
2. **Join hoặc đọc ngữ cảnh asset**: từ enrichment có sẵn trong event, hoặc join với profile store theo `device.uid` + thời gian.
3. **Xuất kết quả** thành alert, case, báo cáo, hoặc ghi ngược về profile (vd đánh dấu "thiếu EDR").

## Ví dụ
Một lỗ hổng nghiêm trọng mới được công bố trong phần mềm `X` phiên bản dưới 5.2. Dữ liệu sạch trả lời liên tiếp nhiều câu hỏi:

1. **Có bao nhiêu máy bị ảnh hưởng?** Software Inventory Info cho máy *đã cài* `X` < 5.2: 140 máy.
2. **Máy nào thực sự chạy nó?** Process Activity 30 ngày qua có `process.file.name = X`: 35 máy.
3. **Máy nào quan trọng và phơi ra ngoài?** Join profile: 4 máy criticality Critical/High có Network Activity inbound từ internet tới cổng của `X`.
4. **Vá theo thứ tự**: 4 máy trên trước, rồi 31 máy còn lại, cuối cùng 105 máy cài mà không chạy (cân nhắc gỡ).
5. **Đã bị khai thác chưa?** Tìm Detection Finding và process con bất thường của `X` trên 35 máy, so với baseline process của từng máy.
6. **Nếu có máy dính**: scoping qua `observables` (hash, domain C2), quyết định cô lập theo criticality, case gửi owner trong profile.

Không bước nào cần biết log gốc đến từ EDR hay firewall nào. Đó là lợi ích trực tiếp của chuẩn hóa cộng với asset management.

## Hiểu nhầm thường gặp
- **"Asset management chỉ phục vụ báo cáo"**: nó là ngữ cảnh cho mọi quyết định của SOC: ưu tiên, triage, containment.
- **"Có profile rồi thì rule tự giỏi hơn"**: rule phải được viết lại để *dùng* ngữ cảnh (lọc theo nhóm, nhân criticality); enrich mà không dùng chỉ tốn dung lượng.
- **"Ưu tiên chỉ theo severity của vendor"**: cùng một alert High, trên máy lab và trên domain controller khác nhau hoàn toàn về rủi ro.
- **"Dữ liệu sạch là đích đến"**: nó là nền tảng. Giá trị nằm ở các ứng dụng xây trên đó, và ở vòng phản hồi giúp sửa CMDB, tuning rule, bổ sung nguồn log còn thiếu.

## Liên quan
- [15-why-ocsf.md](15-why-ocsf.md): vì sao chuẩn hóa là điều kiện của các ứng dụng trên.
- [19-asset-management-and-profile.md](19-asset-management-and-profile.md): asset profile là gì.
- [20-asset-profiling-from-ocsf-logs.md](20-asset-profiling-from-ocsf-logs.md): dựng profile từ log.
- [21-asset-enrichment-in-ocsf.md](21-asset-enrichment-in-ocsf.md): đưa ngữ cảnh vào event.
- [06-vulnerability-management.md](06-vulnerability-management.md), [08-siem.md](08-siem.md), [12-incident-response.md](12-incident-response.md): các quy trình dùng dữ liệu này.
