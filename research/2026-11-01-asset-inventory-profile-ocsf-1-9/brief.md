# Brief: Dựng asset inventory và asset profile từ log OCSF 1.9.0 như thế nào?

- **Ngày:** 2026-11-01
- **Câu hỏi chính:** Với log bảo mật đã chuẩn hóa theo OCSF 1.9.0, nên dựng asset inventory và asset profile theo phương pháp nào (định danh, gộp, mô hình dữ liệu, pipeline, nội dung profile) để phục vụ detection và triage?
- **Mục đích:** Có thiết kế đủ cụ thể để triển khai MVP inventory trên dữ liệu OCSF, dựa trên khái niệm có thật của Microsoft (entity, strong/weak identifier, asset và evidence) và trên đúng schema OCSF 1.9.0.
- **Câu hỏi phụ:**
  1. Microsoft định nghĩa entity, asset, evidence, strong/weak identifier và merge thế nào?
  2. Microsoft tách inventory và profile thành những thành phần nào (DeviceInfo, device discovery, dedup, critical asset, Exposure Graph, UEBA)?
  3. OCSF 1.9.0 có những class, trường, observable type nào cho asset, và trường nào đã deprecated?
  4. Mô hình dữ liệu, điều kiện promote entity thành asset và pipeline từ log tới inventory nên ra sao?
  5. Profile của từng loại asset gồm gì, lấy từ class OCSF nào; bẫy thường gặp; lộ trình MVP?
- **Phạm vi:** OCSF 1.9.0 (phát hành 2026-08-03); docs Microsoft Learn hiện hành; asset dạng device và account trước, cloud resource để sau.
- **Ngoài phạm vi:** Splunk và Google SecOps (đã có ở báo cáo kế thừa); cấu hình sản phẩm; giá, license.
- **Độ sâu:** sâu (báo cáo do chủ repo viết, coordinator đối chiếu và kiểm chứng các khẳng định chính).
- **Kế thừa:** `research/2026-10-29-asset-profile-tu-event-chuan-hoa/report.md`
