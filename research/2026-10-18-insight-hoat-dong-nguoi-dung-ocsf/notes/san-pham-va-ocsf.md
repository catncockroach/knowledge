# Thực tiễn: sản phẩm/công cụ hiện có và schema OCSF

## Câu phụ 3a: sản phẩm/công cụ nào đã sinh timeline hay tóm tắt hoạt động dễ đọc từ telemetry, và chúng làm thế nào

### Kết luận ngắn
Có ba nhóm. (1) Công cụ forensic timeline (plaso, Timesketch, Velociraptor) **chuẩn hóa mỗi event thành một dòng `timestamp + message` dễ đọc bằng formatter/luật**, còn LLM chỉ là lớp mỏng phía sau: Timesketch khử trùng lặp theo `message` rồi nhồi JSON vào một prompt, hoặc stream toàn bộ event cho một agent trả về finding kèm `record_id`. (2) Trợ lý AI trong SIEM/XDR (Copilot, Elastic, Purple AI, Charlotte, Google SecOps, AWS Bedrock sample) gần như đều **tóm tắt trên alert/finding hoặc trên kết quả truy vấn đã được hệ thống gom sẵn** (incident, Storyline, text-to-SQL), chứ không tóm tắt thẳng hàng trăm nghìn event thô, và đều hướng an ninh. (3) Công cụ phân tích năng suất (ActivTrak, Viva Insights, Recall) suy ra "người dùng đang làm gì" chủ yếu bằng **phân loại app/website theo danh mục** (luật, crowd-source, ML) và metadata cộng tác, không phải bằng LLM đọc log. Mức chắc chắn: **trung bình–cao** cho nhóm 1 (đã đọc docs và source code), **trung bình** cho nhóm 2–3 (chủ yếu là docs và tài liệu của vendor, không có đánh giá độc lập; có vài mục chỉ có snippet).

### Phát hiện có nguồn

**plaso / log2timeline (forensic super-timeline)**
- Mỗi loại event data có một *formatter* định nghĩa `message` và `short_message`. Formatter khai báo trong `data/formatters/*.yaml` (từ bản 20200227). Có formatter cơ bản (một chuỗi) và formatter có điều kiện (ghép các mảnh, mặc định nối bằng một dấu cách). *Helper* biến giá trị thô thành nhãn: boolean, enumeration ("map a value of an event attribute to a more descriptive value"), flags, custom Python — [Plaso: Output and formatting](https://plaso.readthedocs.io/en/latest/sources/user/Output-and-formatting.html) (bậc 1, không rõ ngày)
- Định dạng đầu ra: `dynamic` (CSV với các field tự chọn qua `--fields`), `json`/`json_line` (có `message`, `parser`, `timestamp_desc`), `l2tcsv` (17 field cố định), `l2ttln`/`tln` (7 và 5 field), `opensearch_ts` để nạp vào Timesketch — cùng nguồn (bậc 1)
- **Nhận định:** cách plaso làm (template message theo kiểu event và helper ánh xạ enum ra nhãn) chính là kiểu "render một event thành một câu ngắn bằng luật, O(1) mỗi event". Pipeline OCSF có thể làm y hệt theo `type_uid`.

**Timesketch (Google), gồm các tính năng LLM**
- Có các tính năng LLM thử nghiệm: tóm tắt event (`llm_summarization`) và NL2Q (chuyển câu hỏi tự nhiên thành query). Provider hỗ trợ: Ollama (tự host), Google GenAI (Vertex AI/Gemini API), Sec-Gemini. Docs khuyên dùng model nhanh như `gemini-2.0-flash`. Có thêm "AI Investigation Agent" trong Investigation View, tự sinh câu hỏi điều tra và finding — [Timesketch docs: llm-features.md](https://github.com/google/timesketch/blob/master/docs/guides/admin/llm-features.md) (bậc 1, truy cập 2026-10-18)
- Source `llm_summarize.py`: lấy các event khớp filter hiện tại, **`drop_duplicates(subset="message")`** (chỉ giữ cột `message`), rồi `json.dumps` cả danh sách vào chỗ `<EVENTS_JSON>` của prompt, gọi LLM **một lần**. Nó ghi metric "events processed" và "unique events sent to the LLM" — [timesketch/lib/llms/features/llm_summarize.py](https://github.com/google/timesketch/blob/master/timesketch/lib/llms/features/llm_summarize.py) (bậc 1, nhánh master, truy cập 2026-10-18)
- Prompt mặc định: "Summarize the following security events to provide a concise overview of what happened. Identify the main activity or incident…", và yêu cầu bọc các observable (IP, domain, đường dẫn file, username, tên process, search query) trong `<strong>` — [data/llm_summarize/prompt.txt](https://github.com/google/timesketch/blob/master/data/llm_summarize/prompt.txt) (bậc 1, truy cập 2026-10-18)
- `log_analyzer.py`: "always processes ALL events within the active timelines of a sketch". Event được export bằng sliced scroll (`num_slices=20`), có thể giới hạn `return_fields`, rồi **stream** sang provider (`generate_stream_from_logs`). Provider trả JSON có `summaries` là danh sách finding, mỗi finding có `log_records[].record_id` cùng annotations. Finding nào thiếu record_id bị bỏ. Finding được ghi lại thành đối tượng DFIQ (Question/Conclusion) và gắn annotation vào đúng event gốc — [timesketch/lib/llms/features/log_analyzer.py](https://github.com/google/timesketch/blob/master/timesketch/lib/llms/features/log_analyzer.py) (bậc 1, truy cập 2026-10-18)
- **Nhận định:** đây là hai mẫu thiết kế đáng chú ý. (a) Khử trùng lặp theo chuỗi message trước khi gọi LLM, nên số token phụ thuộc số message *khác nhau* chứ không phụ thuộc n. (b) Bắt LLM trả về ID của event gốc cho mỗi kết luận, và vứt kết luận không có ID: một cơ chế truy vết/chống hallucination đơn giản. Cách (a) làm mất thông tin tần suất và thời gian (chỉ còn `message`), nên không đủ cho một timeline theo ngày.

**Velociraptor**
- Từ bản 0.73 (2024-09) có tính năng timeline. Mỗi `Event` "must have a `Timestamp` and a `Message` field", còn lại để trong `data` dạng key/value. *Supertimeline* là tập nhiều timeline chồng lên nhau, bật/tắt được từng cái. *Annotation* là một timeline đặc biệt chứa các event analyst chọn ra kèm giải thích ("the investigative timeline"), và export nó ra thì được narrative của vụ việc. Case study dùng `Windows.Hayabusa.Rules` (Sigma), lọc ~18.000 hit xuống ~100 event tin cậy cao, cùng `Windows.Forensics.Usn`, `Windows.Timeline.Prefetch`, `Windows.System.TaskScheduler`, `Windows.Sys.Users` — [Velociraptor blog: Timelines in Velociraptor](https://docs.velociraptor.app/blog/2024/2024-09-12-timelines/) (bậc 1, 2024-09-12)
- **Nhận định:** narrative ở Velociraptor do *người* viết (annotation), và bước giảm dữ liệu dựa vào luật (Sigma) cộng lọc thủ công. Mô hình dữ liệu tối thiểu `Timestamp + Message + data` lại khớp với một biểu diễn rút gọn cho event OCSF.

**Microsoft Security Copilot: device summary trong Defender XDR**
- Device summary tóm tắt posture và hoạt động của một thiết bị: trạng thái các bảo vệ (ASR, tamper protection), "Any significant user activity observed, like unusual sign-in attempts", phần mềm có lỗ hổng, firewall, lần thấy online gần nhất, và thông tin từ Intune (người dùng chính, device group, app đã phát hiện). Mở trang thiết bị là Copilot tự sinh summary, copy hoặc regenerate được — [Summarize device information with Microsoft Copilot in Microsoft Defender](https://learn.microsoft.com/en-us/defender-xdr/copilot-in-defender-device-summary) (bậc 1, ms.date 2025-04-25, cập nhật 2026-06-24)
- Docs **không** mô tả input chi tiết (bảng nào, bao nhiêu event) hay cách gom — cùng nguồn
- **Nhận định:** đầu ra là một bản tóm tắt posture và bất thường của thiết bị, không phải timeline hoạt động theo ngày.

**Elastic Attack Discovery / AI Assistant**
- Attack Discovery dùng LLM để phân tích **alert** (không phải event thô). Mặc định lấy tối đa 100 alert, kéo lên được 500, và "sending more alerts than your chosen LLM can handle may result in an error". Nó dùng chung thiết lập anonymization với AI Assistant, nơi chọn field nào của alert được gửi cho LLM và field nào bị che. Đầu ra mỗi discovery gồm tiêu đề, tóm tắt, số alert liên quan và ánh xạ MITRE ATT&CK, cùng user/host liên quan và hoạt động đáng ngờ của từng entity — [Elastic Security 8.17: Attack discovery](https://www.elastic.co/guide/en/security/8.17/attack-discovery.html) (bậc 1, docs bản 8.17, không còn cập nhật)
- Docs 8.14/8.15 (theo snippet tìm kiếm) ghi mặc định 20 alert, tối đa 100, xét alert trong 24 giờ qua. Docs mới hơn ghi GA từ 9.1 — [Elastic 8.14 Attack discovery](https://www.elastic.co/guide/en/security/8.14/attack-discovery.html) (bậc 1, chỉ đọc snippet)
- **Nhận định:** giới hạn cứng vài trăm alert cho thấy vendor xử lý vấn đề quy mô bằng cách đưa vào LLM *đơn vị đã gom* (alert), không phải event. Đây cũng là sản phẩm lấy ATT&CK làm khung, tức đúng hướng mà brief loại trừ.

**SentinelOne Purple AI + Storyline**
- "the powerful combination of SentinelOne's patented Storylines technology and Purple AI allows analysts to not only quickly find all events associated with a given activity but also get a summary of these events and their suspicion level". Summary gồm: có hoạt động độc hại không và ở đâu, chuỗi event, hoạt động file/network/DNS **đã được gom theo process đáng ngờ**, user/file liên quan, và kết luận. "Purple AI uses a variety of models both open source and proprietary" — [SentinelOne blog: Purple AI…](https://www.sentinelone.com/blog/purple-ai-empowering-cybersecurity-analysts-with-ai-driven-threat-hunting-analysis-response/) (bậc 1 nhưng là marketing, cập nhật 2024-09-04)
- Ví dụ trong blog: "The suspicious activity was initiated by the 'ResistanceIsFutile.exe' process, which is unsigned and located on the user's desktop. This process started another process, 'powershell.exe'…" — cùng nguồn
- Trang demo của SentinelOne mô tả Storyline view "organizes all atomic endpoint events into a single narrative describing the full chain of events on an endpoint" — [SentinelOne tour](https://www.sentinelone.com/lp/tour) (bậc 1, marketing, chỉ đọc snippet)
- Ngày GA không thống nhất: một trang của N-able ghi "generally available as of September 11, 2025", có lẽ là GA trong kênh phân phối của N-able, không phải ngày GA gốc — [N-able status](https://status.n-able.com/2025/09/17/sentinelone-purple-ai-is-now-generally-available-conversational-threat-hunting-for-every-soc/) (bậc 3)
- **Nhận định:** Storyline (gán một ID chung cho mọi event cùng một cây process ngay tại agent) là phần gom theo lineage, làm trước LLM. LLM chỉ tóm tắt một Storyline đã gom.

**CrowdStrike Charlotte AI**
- Tài liệu hướng dẫn của CrowdStrike liệt kê tính năng "Generate an in-depth incident summary and next-step suggestions to understand the scope of an attack". Agent triage trả về "a detection verdict, a confidence score, a recommendation, and an explanation of its reasoning" — [CrowdStrike Charlotte AI User Guide (PDF)](https://www.crowdstrike.com/content/dam/crowdstrike/marketing/en-us/documents/pdfs/guides/CrowdStrike-Charlotte-AI-User-Guide.pdf) và [trang Charlotte AI](https://www.crowdstrike.com/platform/charlotte-ai/) (bậc 1, marketing, chỉ đọc snippet, không rõ ngày)
- Không tìm thấy mô tả cách Charlotte đọc process tree hay event thô.

**Google SecOps (Chronicle) + Gemini**
- Widget AI Investigation (tab Case Overview) xem xét alert, event và entity của một *case* rồi sinh tóm tắt và đề xuất bước tiếp theo. Gemini chuyển câu hỏi tự nhiên thành truy vấn UDM Search. Các tính năng này có trong gói Enterprise của Security Command Center — [Gemini in Security Command Center overview](https://docs.cloud.google.com/security-command-center/docs/gemini-overview) (bậc 1, chỉ đọc snippet)
- Một nguồn thứ cấp nói Gemini tự tóm tắt kết quả sau mỗi lần UDM search và cho phép hỏi tiếp — [CyberProof](https://www.cyberproof.com/siem/google-chronicle-and-its-usage-of-ai-in-secops/) (bậc 2–3)

**Amazon Security Lake (OCSF) + Bedrock: hai sample chính thức của AWS**
- 2024-01-16: notebook SageMaker dùng LangChain và Claude 2 trên Bedrock, chạy một Conversational ReAct agent (có memory) với các tool liệt kê bảng, xem schema, kiểm tra và chạy SQL trên Athena, tức **text-to-SQL** trên các bảng Security Lake (CloudTrail, Route 53 resolver, Security Hub findings `sh_findings_1_0`, VPC flow) — [AWS Security Blog: Generate AI powered insights for Amazon Security Lake using SageMaker Studio and Bedrock](https://aws.amazon.com/blogs/security/generate-ai-powered-insights-for-amazon-security-lake-using-amazon-sagemaker-studio-and-amazon-bedrock) (bậc 1, 2024-01-16)
- 2025-05-01: chatbot với Bedrock Agent (Claude 3 Sonnet), hai knowledge base (một chứa schema bảng Security Lake mẫu, một chứa playbook IR) và một action group chạy SQL trên Athena. "providing example table schemas improves SQL query generation accuracy". Agent diễn giải kết quả SQL thành câu trả lời tự nhiên. Field OCSF duy nhất được nêu là `type_name`. Repo: `aws-samples/sample-generative-ai-chatbot-for-amazon-security-lake` — [AWS Security Blog: Use an Amazon Bedrock powered chatbot with Amazon Security Lake…](https://aws.amazon.com/blogs/security/use-an-amazon-bedrock-powered-chatbot-with-amazon-security-lake-to-help-investigate-incidents) (bậc 1, 2025-05-01)
- Docs Security Lake có trang "Integration with Amazon Bedrock": dùng ngôn ngữ tự nhiên trong SageMaker AI Studio để tự xác định nguồn dữ liệu, sinh và chạy SQL, rồi trực quan hóa — [Security Lake User Guide: Integration with Amazon Bedrock](https://docs.aws.amazon.com/security-lake/latest/userguide/bedrock-integration.html) (bậc 1, chỉ đọc snippet)
- **Nhận định:** mẫu chung trên dữ liệu OCSF là *LLM sinh SQL, SQL engine aggregate, LLM diễn giải kết quả nhỏ*. Phần nặng O(n) để cho engine truy vấn làm, và số token không phụ thuộc n. Đây là một mẫu kiến trúc dùng được cho bài toán (truy vấn aggregate theo ngày/class/process), nhưng các sample này dùng để hỏi đáp, không tự sinh timeline.

**Phân tích năng suất / hoạt động người dùng**
- ActivTrak phân loại app/website theo *danh mục* và *mức năng suất* (productive/unproductive/undefined). Vendor nói AI tự phân loại được ">80% of apps and websites" từ ngày đầu, và engine crowd-source phủ ">90% of activity duration". Thứ tự ưu tiên: thiết lập theo nhóm, phân loại thủ công, Custom Rules, rồi mới tới Intelligent Auto-Classification (không ghi đè phân loại thủ công) — [ActivTrak: AI-Powered Activity Classification](https://www.activtrak.com/product/activity-classification/) và [ActivTrak support](https://support.activtrak.com/hc/en-us/articles/210214426) (bậc 1, vendor, chỉ đọc snippet, không rõ ngày)
- Microsoft Viva Insights dùng *metadata* cộng tác: email (timestamp, người gửi, người nhận, tín hiệu đã đọc), lịch (loại, trạng thái busy/free, category, subject, thời lượng, người dự), cuộc gọi và chat Teams, số tài liệu OneDrive/SharePoint đã làm việc. Giờ làm việc tính theo thiết lập working hours của Outlook. Có luật loại trừ cuộc họp phi công việc theo từ khóa trong subject — [Viva Insights FAQ](https://learn.microsoft.com/en-us/viva/insights/personal/overview/mya-faq) và [Advanced insights FAQ](https://learn.microsoft.com/en-ca/Viva/insights/advanced/reference/faq) (bậc 1, chỉ đọc snippet)
- Windows Recall (Copilot+ PC) chụp snapshot màn hình định kỳ "while content on the screen is different from the previous snapshot", phân tích tại máy, lưu trong một vector DB mã hóa để tìm kiếm ngữ nghĩa bằng ngôn ngữ tự nhiên. Snapshot cũ tự xóa khi chạm hạn mức lưu trữ — [Manage Recall](https://learn.microsoft.com/windows/client-management/manage-recall) (bậc 1, chỉ đọc snippet) và [Windows Central](https://www.windowscentral.com/software-apps/windows-11/how-does-windows-recall-work) (bậc 2)
- **Nhận định:** nhóm này cho thấy "hoạt động người" thường được suy ra bằng **bảng tra phân loại app/domain theo danh mục** (một phép tra O(1) mỗi event) cộng **gom theo thời lượng**. Với OCSF, việc này tương ứng với tra `process.file.name` / `http_request.url.hostname` / `query.hostname` vào một taxonomy app/website. Thứ tự ưu tiên luật của ActivTrak (thủ công trước, AI lấp chỗ trống) là gợi ý tốt cho chỗ đặt LLM: dùng LLM để gán nhãn những app/domain *chưa biết*, một lần cho mỗi giá trị khác nhau, rồi cache lại.

### Nhận định (tổng hợp 3a)
- Không sản phẩm nào được tìm thấy (có tài liệu công khai) làm đúng bài toán "timeline hoạt động người theo ngày từ event OCSF thô". Các sản phẩm gần nhất gồm hai phần: phần gom/render tất định (formatter của plaso, Storyline của S1, incident/case, SQL aggregate) và LLM đặt **sau** bước gom, chạy trên vài chục đến vài trăm đơn vị đã gom (Elastic ≤500 alert). Các mẫu đáng mượn: (1) render message theo template + khử trùng lặp (Timesketch, plaso); (2) gom theo cây process trước khi tóm tắt (Purple AI/Storyline); (3) LLM chỉ sinh query, engine tự aggregate (AWS); (4) bắt LLM trả về record_id để truy vết (Timesketch log_analyzer); (5) bảng tra danh mục app/domain, LLM chỉ dùng cho phần đuôi dài (ActivTrak).

### Khoảng trống
- KAPE / Timeline Explorer (Eric Zimmerman), Windows Timeline (ActivitiesCache.db, đã bị Microsoft bỏ), RescueTime, Splunk AI Assistant: chưa mở được nguồn trong giới hạn số lời gọi, nên không có phát hiện kèm URL.
- Query.ai và Splunk ứng dụng OCSF để sinh narrative: không tìm được bài nào. Truy vấn "OCSF events LLM summarization narrative blog" (extended) chỉ trả về paper tóm tắt narrative chung.
- Không có đánh giá độc lập về độ chính xác summary của Copilot, Purple AI, Charlotte, Gemini. Mọi mô tả là tài liệu của vendor.
- Không biết input thật (bảng nào, bao nhiêu event, nén ra sao) của Copilot device summary và Google SecOps case summary.

## Câu phụ 3b: cấu trúc OCSF và cách nó giúp giảm ~500 field xuống biểu diễn gọn

### Kết luận ngắn
OCSF phiên bản ổn định hiện tại là **1.9.0** (release 2026-08-03; 1.10.0-dev đang phát triển). Mỗi class có khoảng **60–96 attribute cấp cao nhất** khi bật mọi profile (Process Activity 68, nhưng chỉ 39 khi không bật profile). Nếu trải phẳng các object lồng thêm một cấp thì mỗi class có **khoảng 290–590 đường dẫn field lá**, khớp với con số "~500 field" của brief. Biểu diễn gọn cho từng event có thể dựng gần như hoàn toàn từ một nhóm nhỏ field chuẩn: `time`, `type_uid` (= class_uid·100 + activity_id), `status_id`/`disposition_id`/`action_id`, `severity_id`, `actor.user` và `actor.process` (kèm `parent_process`/`lineage`), object chính của class (`process`, `file`, `dst_endpoint`, `query`, `http_request.url`, `reg_key`…), `message` và `observables`. Mức chắc chắn: **cao**, vì các con số được tính trực tiếp từ API schema.ocsf.io, phiên bản 1.9.0.

### Phát hiện có nguồn
- Danh sách phiên bản trên server schema: mặc định 1.9.0, có 1.10.0-dev. GitHub releases: 1.9.0 (2026-08-03), 1.8.0 (2026-03-18), 1.7.0 (2025-11-14), 1.6.0 (2025-08-01), 1.5.0 (2025-04-28) — [schema.ocsf.io/api/versions](https://schema.ocsf.io/api/versions) và [github.com/ocsf/ocsf-schema/releases](https://github.com/ocsf/ocsf-schema/releases) (bậc 1, truy cập 2026-10-18)
- Các category trong 1.9.0 (số class, kể cả class deprecated và class của extension): System Activity (1) 16, Findings (2) 8, IAM (3) 8, Network Activity (4) 14, Discovery (5) 26, Application Activity (6) 8, Remediation (7) 4, Unmanned Systems (8) 2. API `/classes` trả về 87 class và `/objects` trả về 194 object. Có 3 platform extension: linux, win, macos — [schema.ocsf.io/1.9.0/api/categories](https://schema.ocsf.io/1.9.0/api/categories), [/api/classes](https://schema.ocsf.io/1.9.0/api/classes), [/api/extensions](https://schema.ocsf.io/1.9.0/api/extensions) (bậc 1, 1.9.0)
- Các class liên quan tới endpoint Windows (uid): File System Activity 1001, Kernel Extension 1002, Kernel 1003, Memory 1004, Module 1005, Scheduled Job 1006, Process 1007, Event Log 1008, Script 1009, Peripheral 1010, Device Power State 1011, Clipboard 1012. Detection Finding 2004 (Security Finding 2001 đã deprecated). Authentication 3002, Authorize Session 3003, User Management 3007 (Account Change 3001 deprecated từ 1.9.0). Network 4001, HTTP 4002, DNS 4003, DHCP 4004, RDP 4005, SMB 4006, SSH 4007. Web Resources 6001, Application Lifecycle 6002, API 6003, File Hosting 6006. Extension Windows: Registry Key Activity 201001, Registry Value Activity 201002, Windows Resource Activity 201003, Windows Service Activity 201004 — cùng nguồn (bậc 1, 1.9.0)
- Ngữ nghĩa các field lõi trong `base_event`:
  - `type_uid`: "Producers and mappers must compute this as class_uid * 100 + activity_id. It uniquely identifies the combination of event class and activity across the entire schema. For example, Detection Finding: Create is 200401."
  - `activity_id`: mỗi class có tập giá trị riêng, 0 = Unknown, 99 = Other (khi đó phải điền `activity_name`).
  - `message` (recommended): "A human-readable description of the event, as defined by the source… concise, meaningful summary suitable for display in a UI… not a raw log line. For example: 'User john_doe logged in from 10.0.0.1.'"
  - `observables` (recommended): "surfaces key indicators and entities from the event… in a single, consistent location… Each entry references an attribute path within the event (e.g., src_endpoint.ip) along with its type and value".
  - `time`: thời điểm hoạt động xảy ra tại nguồn (khác `metadata.logged_time`/`processed_time`).
  - `raw_data` và `unmapped`: chứa dữ liệu gốc và field không ánh xạ được, "not intended for structured querying".
  - Base event có 55 attribute, 9 required (activity_id, time, type_uid, metadata, category_uid, severity_id, class_uid, cùng osint/cloud do profile).
  — [schema.ocsf.io/1.9.0/api/classes/base_event](https://schema.ocsf.io/1.9.0/api/classes/base_event) (bậc 1, 1.9.0)
- Các enum chuẩn dùng chung, giúp nén một event thành vài mã nhỏ: `severity_id` 0–6 (Unknown, Informational, Low, Medium, High, Critical, Fatal), 99 Other. `status_id` 1 Success, 2 Failure. `action_id` 1 Allowed, 2 Denied, 3 Observed, 4 Modified. `disposition_id` có ~28 giá trị (1 Allowed, 2 Blocked, 3 Quarantined, 15 Detected, 17 Logged…) — [schema.ocsf.io/1.9.0/api/classes/process_activity](https://schema.ocsf.io/1.9.0/api/classes/process_activity) (bậc 1, 1.9.0)
- activity_id theo từng class (1.9.0):
  - Process Activity: 1 Launch, 2 Terminate, 3 Open, 4 Inject, 5 Set User ID.
  - File System Activity: 1 Create, 2 Read, 3 Update, 4 Delete, 5 Rename, 6 Set Attributes, 7 Set Security, 8 Get Attributes, 9 Get Security, 10 Encrypt, 11 Decrypt, 12 Mount, 13 Unmount, 14 Open.
  - Network Activity: 1 Open, 2 Close, 3 Reset, 4 Fail, 5 Refuse, 6 Traffic, 7 Listen.
  - DNS: 1 Query, 2 Response, 6 Traffic.
  - HTTP: khoảng 40 method (Get, Post, Put, Connect…).
  - Authentication: 1 Logon, 2 Logoff, 3 Authentication Ticket, 4 Service Ticket Request, 5 Renew, 6 Preauth, 7 Account Switch. `logon_type_id` gồm 2 Interactive, 3 Network, 7 Unlock, 10 Remote Interactive, 11 Cached Interactive…
  - Module: 1 Load, 2 Unload, 3 Invoke.
  - Scheduled Job: 1 Create … 6 Start.
  - Registry Key: 1 Create, 2 Read, 3 Modify, 4 Delete…
  - Windows Service: 1 Create, 2 Reconfigure, 3 Start, 4 Stop…
  - Detection Finding: 1 Create, 2 Update, 3 Close.
  — các trang `/api/classes/<name>` tương ứng trên schema.ocsf.io (bậc 1, 1.9.0)
- Số attribute mỗi class (cấp cao nhất, API mặc định áp mọi profile), tính bằng script trên API 1.9.0:

  | Class | Attr cấp 1 | trong đó required / recommended | Attr kiểu object | Field lá: không trải / trải 1 cấp object / trải 2 cấp |
  |---|---|---|---|---|
  | Process Activity 1007 | 68 | 12 / 20 | 23 | 45 / 301 / 1177 |
  | File System Activity 1001 | 66 | 12 / 16 | 23 | 43 / 340 / 1347 |
  | Network Activity 4001 | 84 | 9 / 25 | 39 | 45 / 534 / 1991 |
  | Authentication 3002 | 80 | 10 / 27 | 32 | 48 / 433 / 1656 |
  | DNS Activity 4003 | 96 | 9 / 29 | 43 | 53 / 550 / 2025 |
  | HTTP Activity 4002 | 86 | 9 / 27 | 43 | 43 / 590 / 2224 |
  | Registry Value Activity 201002 | 61 | 12 / 12 | 23 | 38 / 291 / 1004 |
  | Module 1005 / Script 1009 / Scheduled Job 1006 / Win Service 201004 | 60 / 60 / 61 / 61 | ~11–12 / 12–13 | 22–23 | — |
  | Detection Finding 2004 | 77 | 10 / 16 | 29 | — |

  Process Activity khi tắt hết profile (`?profiles=`) chỉ còn 39 attribute. "Trải N cấp" nghĩa là mở rộng các attribute kiểu object N lớp, không đệ quy lại cùng một object và không tính phần tử mảng, nên đây là số đường dẫn *có thể có*, không phải số field thực sự được điền — tính từ [schema.ocsf.io/1.9.0/api/classes/…](https://schema.ocsf.io/1.9.0/api/classes/process_activity) và [/api/objects/…](https://schema.ocsf.io/1.9.0/api/objects/process) (bậc 1, tự tính ngày 2026-10-18)
- Profile áp được lên các class hệ thống: `host`, `datetime`, `cloud`, `container`, `data_classification`, `osint`, `record_integrity`, `security_control`, `ai_operation`, `linux/linux_users`, `macos/macos_users`. Toàn schema có thêm `trace`, `load_balancer`, `network_proxy`, `incident`. Profile `security_control` là nhóm thêm `action_id`/`disposition_id`/`is_alert`… — [schema.ocsf.io/1.9.0/api/profiles](https://schema.ocsf.io/1.9.0/api/profiles) (bậc 1, 1.9.0)
- Object lineage và actor:
  - `process` có 35 attribute: `pid`, `uid`, `name`, `cmd_line`, `file`, `user`, `session`, `parent_process`, `ancestry`, `lineage`, `integrity`, `created_time`, `terminated_time`, `working_directory`, `loaded_modules`… `process.uid`: "A unique identifier for this process assigned by the producer… Facilitates correlation of a process event with other events for that process."
  - `parent_process`: "recommended to only populate this field for the top-level process object, to prevent deep nesting". `ancestry` là mảng Process Entity xếp từ cha trực tiếp đi lên. `lineage` là "a list of paths for each ancestor process", ví dụ `['/usr/sbin/sshd','/usr/bin/bash','/usr/bin/whoami']`.
  - `actor` có 10 attribute: `user`, `process`, `session`, `application`, `app_name`, `app_uid`, `authorizations`, `iam_role`, `idp`, `invoked_by`. `actor.process` là "The process that initiated the activity".
  - `user` có 22 attribute (name, uid, domain, type_id, groups…). `device` có 67 attribute (hostname, os, ip, uid…). `observable` có 7 attribute (name, type_id, value…, với ~50 loại type_id như Hostname, IP, File Path, Command Line, Process Name, URL, Registry Key Path, User Name).
  — [schema.ocsf.io/1.9.0/api/objects/process](https://schema.ocsf.io/1.9.0/api/objects/process), [/actor](https://schema.ocsf.io/1.9.0/api/objects/actor), [/observable](https://schema.ocsf.io/1.9.0/api/objects/observable), [/device](https://schema.ocsf.io/1.9.0/api/objects/device) (bậc 1, 1.9.0)

### Nhận định
- **Biểu diễn gọn đề xuất (khoảng 8–15 field mỗi event, thay cho 300–600 đường dẫn có thể có):**
  - `time`
  - `type_uid` (mã hóa luôn class + activity; tra ra nhãn như "Process: Launch" hay "Auth: Logon")
  - `status_id` / `disposition_id` / `action_id` (thành công, thất bại, bị chặn)
  - `severity_id`
  - `actor.user.name`
  - `actor.process.uid` cùng `name` (hoặc `process.uid` / `parent_process.uid` với Process Activity)
  - một "đối tượng chính" theo class: `process.cmd_line`, `file.path`, `dst_endpoint.hostname/ip:port`, `query.hostname`, `http_request.url.hostname`, `reg_key.path`, `job.name`, `win_service.name`, `logon_type_id`
  - `message` nếu nguồn có điền
  - mảng `observables` (đã được chuẩn hóa sẵn thành cặp path/type/value).

  `device` gần như hằng số trong một batch một thiết bị, nên chỉ cần ghi một lần cho cả batch. `metadata`, `raw_data`, `unmapped`, `cloud`, `osint` có thể bỏ khi sinh insight.
- Vì `type_uid` là một số nguyên duy nhất trên toàn schema, nó dùng được trực tiếp làm khóa cho template render (giống formatter của plaso), cho bảng đếm tần suất và cho việc chọn "đối tượng chính". Khoảng 40–50 loại event của brief tương ứng 40–50 template.
- `process.uid` cộng `parent_process` cho phép dựng cây process chỉ trong một lượt duyệt (hash map uid → node), là khóa gom phiên tự nhiên kiểu Storyline. `lineage` (danh sách path) đã là dạng nén của tổ tiên, hợp để đưa thẳng vào prompt.
- Field `message` chỉ là *recommended* và do nguồn định nghĩa, nên không thể trông cậy nó luôn có hoặc đồng nhất. Pipeline nên tự render message từ template theo `type_uid`, và chỉ dùng `message` của nguồn khi có.
- Số đếm attribute phụ thuộc mạnh vào profile (39 so với 68 với Process Activity). Khi nói "500 field" cần nêu rõ là đang tính có profile và có trải object hay không.

### Khoảng trống
- Không có thống kê công khai về tỉ lệ field *thực sự được điền* trong event OCSF Windows thực tế, ví dụ từ Security Lake hay từ các mapper Sysmon → OCSF.
- Không tìm được bài/blog công khai nào dựng "activity narrative" trên dữ liệu OCSF ngoài hai sample text-to-SQL của AWS. Đã thử "OCSF events LLM summarization narrative blog" (extended) nhưng không có kết quả liên quan.
- Endpoint export toàn schema (`/export/schema`) của 1.9.0 báo lỗi legacy format, nên số field lá được tính bằng cách crawl API theo từng object.

## Truy vấn đã chạy
- Timesketch LLM features summarize events Gemini (standard)
- Security Copilot device summary Intune Defender (standard)
- Amazon Security Lake OCSF Bedrock generative AI sample (standard)
- Elastic Attack Discovery how it works alerts LLM (standard)
- ActivTrak productivity classification apps websites categories how it works (standard)
- Purple AI SentinelOne summarize process tree storyline natural language (standard)
- Windows Recall semantic index snapshots how it works on-device (standard)
- Google SecOps Gemini summarize case investigation UDM events (standard)
- Charlotte AI incident summary Falcon process tree explain (standard)
- Viva Insights data sources collaboration metadata email meeting hours (standard)
- Velociraptor timeline artifact super timeline Windows (standard)
- OCSF events LLM summarization narrative blog (extended)
- Truy vấn trực tiếp API schema.ocsf.io 1.9.0 (versions, categories, classes, objects, profiles, extensions) và GitHub API/raw cho google/timesketch, ocsf/ocsf-schema
