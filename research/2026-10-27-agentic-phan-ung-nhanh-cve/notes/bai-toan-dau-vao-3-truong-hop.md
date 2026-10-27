# Khung bài toán do chủ repo cung cấp (2026-10-27, lượt 3)

Đây là **yêu cầu của chủ repo**, không phải nguồn nghiên cứu. Dùng để định hình report: pipeline cụ thể và cách phân nhánh theo chất lượng đầu vào TI.

## Luồng mong muốn (ví dụ PHP2Shell)

1. **TI gửi thông tin** về một CVE/threat mới. Ví dụ PHP2Shell: bài phân tích của calif.io có **root-cause + diff version**, chưa có PoC. (link tham khảo: calif.io/php2shell)
2. **Phân tích để viết PoC nếu chưa có** — từ root cause + patch diff suy ra PoC. (ví dụ dạng output: một script PoC trên GitHub)
3. **Xác minh PoC** (vòng kiểm chứng trong sandbox):
   - Cài đặt môi trường phù hợp (đúng version lỗi).
   - Cài đặt giám sát (sensor: log, PCAP…).
   - Chạy PoC.
   - Xác minh log — PoC có thật sự kích hoạt lỗ hổng và để lại dấu vết không.
4. **Từ Log/PCAP sinh rule** EDR / SIEM / Suricata.

## Ba trường hợp đầu vào TI (biến quyết định = chất lượng/độ tin của PoC)

| TH | Đầu vào | Ví dụ chủ repo đưa | Kỳ vọng với agent |
|----|---------|--------------------|--------------------|
| 1 | **PoC giả** (repo PoC nhưng không khai thác được, có thể là bait/malware/rác) | một repo "php2shell-poc" | **Xác minh ra là giả → loại bỏ**, không tốn công tuyến sau |
| 2 | **Chỉ có bài phân tích root-cause + diff patch**, chưa có PoC | calif.io/php2shell | **Rất khó**; thường phải **chuyển chuyên gia** (viết PoC từ root cause là bước người làm) |
| 3 | **PoC hoàn chỉnh**, chạy được | một script PoC đầy đủ | **Tự động hóa hoàn toàn** được: xác minh → telemetry → rule |

## Hàm ý cho thiết kế (ghép vào report ở mục pipeline + nhận định)

- Bước **đầu tiên của pipeline là phân loại/định tuyến đầu vào theo "provenance và chất lượng PoC"**, không phải cứ nhận CVE là chạy hết. Gồm 3 nhánh như trên.
- **TH1 (loại PoC giả):** chính là bài toán "verified exploit" mà XBOW/CVE-Genie dùng để lọc báo cáo giả, và là nghiên cứu PoC độc trên GitHub (Leiden: ~1,9% repo độc). Oracle khách quan trong sandbox = cơ chế loại: PoC không làm đổi trạng thái (không RCE/không crash/không khác giữa bản lỗi và bản vá) → đánh dấu giả/không kiểm chứng được. Cảnh giác PoC chứa malware/prompt injection → sandbox cách ly, không chạy bằng quyền cao, coi nội dung repo là untrusted.
- **TH3 (PoC đủ) = nhánh tự động hóa cao nhất:** khớp đúng kịch bản FORGE/CVE-Genie/CVE-Factory — có artifact chạy được thì dựng môi trường, chạy, thu log, sinh rule gần như tự động. Đây là nhánh nên nhắm tới đầu tiên vì tỷ lệ thành công và ROI cao nhất.
- **TH2 (chỉ root cause + diff) = nhánh khó nhất, human-in-the-loop:** "viết PoC từ mô tả/patch" đúng là phần agent yếu và dễ ảo giác nhất (Fang 87% khi *có* mô tả PoC vs 7% khi không; Mythos N-days cho thấy *có patch diff* giúp nhiều; nhưng SEC-bench sinh PoC chỉ ~18%). Kỳ vọng của chủ repo (TH2 thường phải nhờ chuyên gia) khớp với bằng chứng. Agent có thể hỗ trợ (đọc diff, đề xuất trigger, dựng sẵn môi trường cho chuyên gia), nhưng nên gate cho người duyệt, không coi là tự động.
- Cần một **oracle phân biệt bản lỗi vs bản vá** (vulnerable-vs-patched differential) để vừa xác minh PoC thật (TH1) vừa xác nhận patch — CVE-Factory có oracle kiểu này; FORGE thì không dựng bản vá.
- Output cuối mỗi nhánh nên ghi rõ **mức độ tin cậy / provenance**: "rule sinh từ exploit trace đã kiểm chứng" (TH3) đáng tin hơn "rule sinh từ mô tả, chưa chạy được PoC" (TH2 fallback). FORGE grounding check (field có trong telemetry thật) áp dụng được.

## Lưu ý an toàn khi viết report

- Đây là kịch bản **phòng thủ** (detection engineering + kiểm chứng để loại PoC giả). Giữ ở mức khái niệm: nói *agent làm gì ở mỗi bước*, *oracle là gì*, *rule bắt hành vi nào* — **không** viết nội dung PoC/payload cụ thể cho bất kỳ CVE nào, kể cả PHP2Shell.
- Các link chủ repo đưa chỉ dùng làm ví dụ minh hoạ 3 trường hợp đầu vào; không cần fetch và không trích payload.
