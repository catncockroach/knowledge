# Chuẩn, framework và nghiên cứu học thuật về chất lượng playbook SOAR

> Ghi chú về giới hạn truy cập: trong phiên này `WebFetch` bị chặn với docs.oasis-open.org, nvlpubs.nist.gov, arxiv.org, dl.acm.org, researchgate, fraunhofer, uni-regensburg (proxy trả 403 hoặc ENOTFOUND). Chỉ GitHub mở được. Vì vậy:
> - Các thuộc tính CACAO v2.0 dưới đây lấy **trực tiếp từ JSON schema chính thức** của OASIS CACAO TC trên GitHub (bậc 1, đã đọc).
> - Phát hiện về paper học thuật, NIST, ISO và CSF chủ yếu lấy từ **snippet/tóm tắt của WebSearch** (abstract, trích đoạn), chưa đọc toàn văn. Writer nên coi chúng là "theo abstract/trích đoạn" và verifier nên mở lại khi có mạng.

## Câu hỏi phụ 2: Chuẩn, framework và nghiên cứu định nghĩa những thuộc tính chất lượng nào cho playbook/automation rule?

### Kết luận ngắn
Không có chuẩn nào định nghĩa "chất lượng playbook SOAR" thành một bộ tiêu chí có điểm số. OASIS CACAO v2.0 là nguồn chuẩn hóa chi tiết nhất. Nó không chấm điểm, nhưng mã hóa nhiều thuộc tính chất lượng thành trường bắt buộc hoặc khuyến nghị: siêu dữ liệu và phiên bản, vòng đời (`valid_from/until`, `revoked`), nhánh lỗi (`on_failure`, `workflow_exception`), `timeout`/`delay`, `impact`, `owner`, chữ ký số, data marking, và ánh xạ hoạt động (`playbook_activities`). NIST 800-61r3, CSF 2.0 và ISO 27035 chỉ yêu cầu ở mức quy trình (có playbook, diễn tập, cải tiến liên tục), không nói về thuộc tính kỹ thuật. Nghiên cứu học thuật tập trung vào khả năng tái sử dụng và chia sẻ, đọc được bằng máy, tính đúng cú pháp/ngữ nghĩa khi sinh bằng LLM, và gần đây là kiểm chứng tuân thủ policy (approval, thứ tự hành động). Độ chắc chắn: **trung bình–cao** với CACAO (đã đọc schema), **trung bình** với phần còn lại (chỉ có abstract/snippet).

### Phát hiện có nguồn

**OASIS CACAO Security Playbooks v2.0**
- CACAO v2.0 là Committee Specification 01, ngày 27/11/2023; OASIS phê duyệt làm Committee Specification tháng 12/2023. JSON schema được chuyển sang repo của TC (oasis-open/cacao-json-schemas) tháng 12/2023 — [CACAO Security Playbooks v2.0 (OASIS)](https://docs.oasis-open.org/cacao/security-playbooks/v2.0/security-playbooks-v2.0.html) (bậc 1, 2023-11; thông tin qua snippet search vì trang bị chặn).
- Spec định nghĩa các lớp đối tượng: playbook, workflow step, command, authentication info, agent/target, extension, data marking, digital signature — [CACAO v2.0 CSD01](https://docs.oasis-open.org/cacao/security-playbooks/v2.0/csd01/security-playbooks-v2.0-csd01.html) (bậc 1, 2023; qua snippet).
- **Trường bắt buộc** của playbook: `type`, `spec_version` (= `cacao-2.0`), `id`, `name`, `created_by` (phải là STIX 2.1 identity), `created`, `modified`, `workflow_start`, `workflow`. `workflow` phải có start step, ít nhất một action hoặc playbook-action step, và end step — [playbook.json, oasis-open/cacao-json-schemas](https://github.com/oasis-open/cacao-json-schemas/tree/main/schemas) (bậc 1, schema v2.0, đã đọc).
- **Phiên bản và vòng đời:** cùng `id` thì là các phiên bản; `modified` xác định phiên bản và phải ≥ `created`; `created` không đổi giữa các phiên bản. `revoked` cho biết tác giả coi playbook hết hiệu lực. `valid_from`/`valid_until` là cửa sổ hiệu lực. `derived_from` ghi nguồn gốc (playbook gốc), `related_to` liên kết tới đối tượng STIX/CACAO — [playbook.json](https://github.com/oasis-open/cacao-json-schemas/tree/main/schemas) (bậc 1).
- **Mô tả mục đích:** `description` "should" được điền. `playbook_types` (vocab: attack, detection, engagement, investigation, mitigation, notification, prevention, remediation) và `playbook_activities` cũng "should" được điền. Nếu dùng vocab thì phải có ít nhất một activity, và **mỗi activity phải có workflow step tương ứng**. Vocab activity gồm 22 giá trị, vd `restrict-access`, `disconnect-system`, `eliminate-risk`, `revert-system`, `restore-data`, `scan-system`, `match-indicator` — [playbook.json](https://github.com/oasis-open/cacao-json-schemas/tree/main/schemas) (bậc 1).
- **Mức độ rủi ro của chính playbook:** `impact` (0–100) phản ánh "potential effect of execution, not the trigger", tức tác động khi chạy playbook chứ không phải mức nghiêm trọng của sự kiện kích hoạt. Ngoài ra có `priority` (1 là cao nhất) và `severity`. Spec để quy tắc chấm cho producer và marketplace — [playbook.json](https://github.com/oasis-open/cacao-json-schemas/tree/main/schemas) (bậc 1).
- **Tóm tắt xử lý** (`playbook_processing_summary`) gồm các cờ boolean: `manual_playbook` (chỉ gồm lệnh thủ công và mô tả văn bản), `external_playbooks`, `parallel_processing`, `if_logic`, `while_logic`, `switch_logic`, `temporal_logic` (delay/timeout), `data_markings`, `digital_signatures`, `countersigned_signatures`, `extensions`. Mục đích là để đánh giá nội dung "without full parsing" — [data-types/playbook-processing-summary.json](https://github.com/oasis-open/cacao-json-schemas/tree/main/schemas) (bậc 1).
- **Xử lý lỗi và timeout trên từng step:**
  - `timeout` (ms): quá hạn thì step bị coi là fail và gọi `on_failure` với `ACTION_TIMEOUT`. Nếu không khai báo, hệ thống thực thi "should consider enforcing a maximum timeout" để không step nào chặn playbook vô hạn.
  - `on_success`/`on_failure` loại trừ với `on_completion`. Không có `on_failure` thì gọi `workflow_exception` của playbook.
  - Có `delay`, `owner` (STIX identity chịu trách nhiệm cho step), `step_variables` và `external_references`.
  - Schema và mô tả của `delay` mâu thuẫn nhau về giá trị tối thiểu (mô tả nói ≥0, schema đặt min 1). Đây là một ví dụ spec có chỗ chưa nhất quán.

  Nguồn: [workflows/workflow-step.json](https://github.com/oasis-open/cacao-json-schemas/tree/main/schemas/workflows) (bậc 1).
- **Luồng điều khiển:** các loại step gồm start, end, action, playbook-action (gọi playbook con, tức module hóa và tái sử dụng), parallel, if-condition, while-condition, switch-condition — [workflows/](https://github.com/oasis-open/cacao-json-schemas/tree/main/schemas/workflows) (bậc 1).
- **Lệnh và human-in-the-loop:** vocab `command-type-ov` gồm `manual`, bash, caldera-cmd, elastic, http-api, jupyter, kestrel, openc2-http, powershell, sigma, ssh, yara. Lệnh trong action step có thể chạy "automatically or manually". Mỗi command "SHOULD" có `playbook_activity` — [commands/command-data.json](https://github.com/oasis-open/cacao-json-schemas/tree/main/schemas) (bậc 1). Schema không có trường "approval" riêng. Bước phê duyệt của con người chỉ biểu diễn được bằng lệnh `manual` hoặc extension.
- **Chữ ký số (toàn vẹn và nguồn gốc):**
  - Đối tượng `signature` (type `jss`) bắt buộc có signee, `related_to` (id playbook), `related_version` (= `modified` của phiên bản được ký), hash_algorithm (should SHA-256/512) và algorithm (RSA, ECDSA, RSASSA-PSS, EdDSA, XMSS, LMS; "should not" dùng HMAC đối xứng).
  - Chữ ký tính trên playbook đã canonicalize. Hỗ trợ countersign lồng nhau. `cert_url` phải lấy qua TLS có xác thực server.
  - Thêm chữ ký không làm đổi phiên bản playbook.

  Nguồn: [data-types/signature.json](https://github.com/oasis-open/cacao-json-schemas/tree/main/schemas) và [playbook.json](https://github.com/oasis-open/cacao-json-schemas/tree/main/schemas) (bậc 1).
- **Bảo mật dữ liệu và chia sẻ:** `markings` và `data_marking_definitions` (TLP, IEP, statement) gắn nhãn phân phối. Credential nằm tách riêng trong `authentication_info_definitions`, được agent/target tham chiếu chứ không nhúng vào step — [playbook.json](https://github.com/oasis-open/cacao-json-schemas/tree/main/schemas) (bậc 1).
- **Biểu diễn đồ họa và kiểm tra hình thức:**
  - CACAO không có ký pháp đồ họa riêng. Zych và cộng sự (IEEE CSR 2023) cho thấy ánh xạ CACAO↔BPMN khả thi ở mức trừu tượng nhưng một construct có nhiều cách biểu diễn — [Reviewing BPMN as a Modeling Notation for CACAO Security Playbooks](https://arxiv.org/pdf/2305.18928) (bậc 1, 2023; qua snippet).
  - Có repo chuyển CACAO JSON sang BPMN: [cyentific-rni/bpmn-cacao](https://github.com/cyentific-rni/bpmn-cacao) (bậc 1).

**NIST SP 800-61r3 và CSF 2.0**
- NIST SP 800-61r3 "Incident Response Recommendations and Considerations for Cybersecurity Risk Management: A CSF 2.0 Community Profile", phát hành tháng 4/2025, thay mô hình 4 pha cũ bằng các outcome của CSF 2.0 — [NIST SP 800-61r3 PDF](https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-61r3.pdf) (bậc 1, 2025-04; chỉ đọc được qua snippet).
- Theo các bản tóm tắt thứ cấp:
  - Rev.3 kỳ vọng tổ chức duy trì playbook, diễn tập, và đưa nhà cung cấp/cloud provider vào kế hoạch — [Security Boulevard](https://securityboulevard.com/2025/06/nist-launches-updated-incident-response-guide/) (bậc 2, 2025-06).
  - Rev.3 nhắc tự động hóa alert, ticketing và chia sẻ thông tin trong phân tích sự cố — [Tandem](https://tandem.app/blog/updated-nist-incident-response-guidance-sp-800-61-rev-3) (bậc 2–3, 2025).

  Chưa xác minh được câu chữ gốc của NIST về automation.
- CSF 2.0 Respond, theo các mirror thứ cấp:
  - RS.MA-02 là triage báo cáo người dùng và alert tự động; RS.MA-03 là phân loại và ưu tiên; RS.MA-04 là escalate; RS.MA-05 là "criteria for initiating incident recovery are applied" — [myctrl.tools CSF v2 RS](https://myctrl.tools/frameworks/nist-csf-v2/family/rs) (bậc 3), [KM-it-ops playbook](https://github.com/KM-it-ops/incident-response-playbooks/blob/main/nist-800-61-playbook.md) (bậc 3).
  - RS.MI-01 là containment, RS.MI-02 là eradication. Ví dụ triển khai của RS.MI-02 nêu rõ eradication có thể do "technologies performing eradication automatically", do người chọn thủ công, hoặc do MSSP làm thay — [stigviewer RS.MI-02](https://www.stigviewer.com/controls/csf/RS.MI-02), [cloudaware RS.MI](https://ce.prod.cloudaware.com/frameworks/nist-csf-v2.0/rs-mi) (bậc 3, mirror của văn bản NIST).

**ISO/IEC 27035**
- ISO/IEC 27035-2:2023 là hướng dẫn "plan and prepare for incident response and to learn lessons". Bản dự thảo (FDIS 2022) có câu: "if appropriate and possible, the incident handoff and information exchange should be automated" — [iTeh sample ISO/IEC 27035-2:2023](https://cdn.standards.iteh.ai/samples/78974/b94b42f6e6c84e70ad0c62f24a960698/ISO-IEC-27035-2-2023.pdf) (bậc 1 nhưng là bản trích mẫu/dự thảo, qua snippet). Không thấy hướng dẫn về chất lượng của chính playbook tự động.

**CISA**
- CISA Federal Government Cybersecurity Incident & Vulnerability Response Playbooks (11/2021) ra đời theo EO 14028 §6, nhằm "standardize" quy trình cho các cơ quan FCEB, gồm 2 playbook (incident, vulnerability). Đây là playbook quy trình cho con người, không phải playbook tự động — [CISA PDF](https://www.cisa.gov/sites/default/files/2023-02/Federal_Government_Cybersecurity_Incident_and_Vulnerability_Response_Playbooks_508C.pdf) (bậc 1, 2021; qua snippet), [Industrial Cyber](https://industrialcyber.co/article/cisa-reveals-federal-government-cybersecurity-incident-and-vulnerability-response-playbooks/?mid=1) (bậc 2).
- Splunk gắn việc phát hành gói playbook dựa trên D3FEND với yêu cầu của OMB M-21-31: "agencies should be completing and rolling out automated incident response playbooks" — [Splunk: SOARing High for M-21-31](https://www.splunk.com/en_us/blog/industries/soaring-high-for-m-21-31) (bậc 2, vendor blog, không rõ ngày).

**MITRE D3FEND và RE&CT**
- D3FEND là knowledge graph các biện pháp phòng thủ, ánh xạ tới ATT&CK, do MITRE phát triển và NSA tài trợ. Các vendor (Splunk, D3 Security, ServiceNow) dùng nó để gắn playbook với kỹ thuật phòng thủ — [Vectra: MITRE D3FEND Explained](https://www.vectra.ai/topics/mitre-d3fend) (bậc 2–3), [D3 Security](https://d3security.com/platform/mitre-d3fend/) (bậc 3, marketing). Con số "30% hiệu quả" trong một bài vendor không có nguồn, không dùng.
- RE&CT (ATC project) là knowledge base các kỹ thuật IR theo cấu trúc kiểu ATT&CK:
  - 6 stage (Preparation, Identification, Containment, Eradication, Recovery, Lessons Learned) × 7 category (General, Network, Email, File, Process, Configuration, Identity).
  - Mỗi Response Action là "atomic procedure", ID mã hóa stage/category (vd RA 2202).
  - Response Playbook là danh sách Response Action cho một threat, có thể map ATT&CK. Mục đích là ưu tiên phát triển năng lực và phân tích gap độ phủ IR.

  Nguồn: [atc-project/atc-react](https://github.com/atc-project/atc-react) (bậc 1, repo; ~524 commit, 180 issue mở, không rõ ngày commit cuối).

**Mô hình trưởng thành**
- SOC-CMM có 5 domain (Business, People, Process, Technology, Services). "SecOps automation" thuộc Technology, được chấm cả maturity lẫn capability, theo thang 0–5 kiểu CMMI. Số aspect lệch giữa các phiên bản (21/26/27) — [andrews.hu SOC-CMM part 3](https://andrews.hu/en/blog/soc-cmm-technology-services-capabilities-part-3/) (bậc 2–3), [cybilportal SOC-CMM](https://cybilportal.org/publications/soc-cmm/) (bậc 2). Chưa đọc được tiêu chí chi tiết của aspect automation.
- Splunk có "SOAR Adoption Maturity Model" riêng, không thay SOC-CMM — [Splunk blog](https://embargo.splunk.com/en_us/blog/security/explore-the-splunk-soar-adoption-maturity-model.html) (bậc 2, vendor).

**Nghiên cứu học thuật**
- Islam, Babar & Nepal, "A Multi-Vocal Review of Security Orchestration", ACM CSUR 2019:
  - Tổng hợp các thuộc tính chất lượng của nền tảng security orchestration (Fig. 6, Table 4 có metric đi kèm).
  - Kết luận rằng giải pháp hiện có thiếu bằng chứng cho flexibility, interoperability, scalability, modifiability, accuracy, extensibility, và rằng cần "defining evaluation criteria and metrics". Usability được coi là yếu tố then chốt.

  Nguồn: [arXiv 2002.09190](https://arxiv.org/pdf/2002.09190), [ACM](https://dl.acm.org/doi/fullHtml/10.1145/3305268) (bậc 1, 2019; qua snippet, chưa xem Table 4).
- Schlette, Empl, Caselli, Schreck, Pernul, "Do You Play It by the Books? A Study on Incident Response Playbooks and Influencing Factors", IEEE S&P 2024 (DOI 10.1109/SP54263.2024.00060):
  - Phương pháp: phân tích 1.217 playbook, khảo sát online 147 người, phỏng vấn sâu 9 chuyên gia.
  - Kết luận: playbook công khai "cannot be used outright", và có "intrinsic ambiguities" trong cách tổ chức định nghĩa playbook.

  Nguồn: [IEEE S&P 2024 accepted papers](https://sp2024.ieee-security.org/accepted-papers.html), [Uni Regensburg news](https://www.uni-regensburg.de/en/informatics-data-science/fids-news/news/25-01-2024_publikationserfolg-bei-ieee-sampp-2024) (bậc 1, 2024; qua snippet).
- Akbari Gurabi, Nitz và cộng sự, "Requirements for Playbook-Assisted Cyber Incident Response, Reporting and Automation", Digital Threats: Research and Practice, 10/2024 (DOI 10.1145/3688810):
  - Từ phỏng vấn chuyên gia rút ra **16 yêu cầu**. Đã thấy: R.1 tuân thủ chuẩn kỹ thuật (BPMN, CACAO, JSON), R.3 reusability, cùng reporting ability, adaptability, confidentiality.
  - Lập luận: playbook thường đặc thù tổ chức và chứa thông tin mật nên cần sanitize trước khi chia sẻ; nên chuyển sang định dạng machine-readable, interoperable xuyên suốt vòng đời.

  Nguồn: [ACM DTRAP](https://dl.acm.org/doi/10.1145/3688810), [Fraunhofer PDF](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/193159d1-dfd9-43e1-aa1e-5a04044ec0e3/content) (bậc 1, 2024; qua snippet, chưa có đủ 16 mục).
- Gurabi và cộng sự, "From Legacy to Standard: LLM-Assisted Transformation of Cybersecurity Playbooks into CACAO Format" (arXiv 2508.03342; Springer 2026):
  - Đánh giá chất lượng playbook sinh ra theo 3 lớp: (1) cú pháp, bằng syntax checker cộng vòng refine; (2) độ trung thực ngữ nghĩa từng trường (metadata, workflow, variables; string similarity/recall); (3) bảo toàn luồng điều khiển bằng normalized graph edit distance.
  - Kết quả tốt nhất: GPT-4o với prompt đầy đủ giảm 84% lỗi cú pháp, GED 0,15.

  Nguồn: [arXiv 2508.03342](https://arxiv.org/abs/2508.03342), [Springer](https://link.springer.com/chapter/10.1007/978-3-032-16092-8_27) (bậc 1, 2025; qua snippet).
- Tsirakis, Fysarakis, Mavroeidis, Papaefstathiou, "Operationalizing Cybersecurity Knowledge: …KMS for CACAO Playbooks", Computers & Security 10/2025: CACAO thiếu công cụ quản lý vòng đời playbook; nhóm xây dựng KMS mã nguồn mở để lưu trữ, truy xuất và quản lý — [arXiv 2503.05206](https://arxiv.org/abs/2503.05206), [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167404825003852) (bậc 1, 2025; qua snippet).
- Bridges và cộng sự (ORNL), "Testing SOAR Tools in Use", Computers & Security 2023:
  - Thiết kế: user study thực hành đầu tiên với 24 người và 6 SOAR thương mại, trong cyber range (AI ATAC 3).
  - Tiêu chí: cài đặt/cấu hình, khả năng chịu internet suy giảm, usability, tăng hiệu suất, giảm context switching, chất lượng điều tra.
  - Phát hiện: cấu hình theo từng SOC là cực kỳ quan trọng. SOAR tăng hiệu suất nhưng "potentially decreased ticketing accuracy/completeness". Sở thích người dùng tương quan hơi âm với hiệu năng thực. Analyst senior thích cân bằng giữa tự động và hỗ trợ ra quyết định.

  Nguồn: [arXiv 2208.06075](https://arxiv.org/abs/2208.06075), [ORNL](https://www.ornl.gov/publication/testing-soar-tools-use) (bậc 1, 2023; qua snippet). Paper này đánh giá **công cụ**, không đánh giá từng playbook.
- SOCpilot (arXiv 2605.05501, 5/2026):
  - Verifier tất định, có kiểu, kiểm tra và sửa chuỗi hành động do LLM đề xuất theo 3 họ rule: `mandatory`, `prohibit_before` (thứ tự, vd phải bảo toàn bằng chứng trước khi restore host), `require_approval`. Hành động ngoài catalog bị lọc và ghi log.
  - Trên 200 sự cố thật của một SOC tài chính, verifier loại bỏ 466 hành động vi phạm yêu cầu approval mà vẫn phủ các task baseline của analyst.
  - Một review bên thứ ba lưu ý rằng các rule policy chưa được kiểm chứng độc lập.

  Nguồn: [arXiv 2605.05501](https://arxiv.org/html/2605.05501v1) (bậc 1, preprint 2026), [Pith review](https://pith.science/paper/2605.05501) (bậc 3).
- Kiểm chứng hình thức:
  - Chưa thấy paper nào model-check playbook CACAO/SOAR trực tiếp.
  - Gần nhất là một paper Springer 2025 dùng model checker tìm deadlock/livelock trong kế hoạch ứng cứu security-safety — [A Model-Based Framework for Developing Security-Safety Incident Response Plans](https://link.springer.com/article/10.1007/s10207-025-01147-4) (bậc 1, 2025; qua snippet).
  - Có hướng BPMN→Petri net để phát hiện deadlock — [Model Checking of BPMN Models for Reconfigurable Workflows](https://www.researchgate.net/publication/304788360_Model_Checking_of_BPMN_Models_for_Reconfigurable_Workflows) (bậc 1, ~2016).
  - Có một bằng sáng chế USPTO về tự động kiểm tra tính hợp lệ của playbook khi cập nhật — [USPTO 12657292](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12657292) (bậc 1, patent, không rõ ngày).
- "A Mathematical Framework for Evaluation of SOAR Tools with Limited Survey Data" (arXiv 2112.00100) là một khung chấm điểm công cụ SOAR từ khảo sát — [arXiv 2112.00100](https://arxiv.org/pdf/2112.00100) (bậc 1, 2021; chỉ thấy tiêu đề, chưa đọc nội dung).

### Nhận định
- **Nhận định:** CACAO là "chuẩn chất lượng ngầm" tốt nhất hiện có cho playbook. Nhiều quy tắc của nó có thể chuyển thẳng thành lint rule:
  - các trường bắt buộc có mặt;
  - `modified ≥ created`;
  - mỗi `playbook_activity` khớp với một step;
  - mỗi step có `timeout` hoặc engine áp max timeout;
  - mọi action có `on_failure` hoặc playbook có `workflow_exception`;
  - không có HMAC trong chữ ký;
  - credential chỉ nằm trong `authentication_info_definitions`;
  - có `impact` và `owner`.
- **Nhận định:** Các chuẩn quy trình (NIST 800-61r3, CSF 2.0, ISO 27035, CISA) đặt yêu cầu ở cấp tổ chức: có playbook, có diễn tập, có cải tiến sau sự cố. Chúng không định nghĩa thuộc tính kỹ thuật như idempotency, retry, trigger scope hay hiệu năng. Các thuộc tính đó gần như chỉ có trong tài liệu vendor và practitioner (thuộc câu hỏi phụ 1 và 3).
- **Nhận định:** Idempotency và retry/backoff **không** xuất hiện trong CACAO hay các chuẩn đã xem. CACAO chỉ có timeout, `on_failure` và vòng lặp while.
- **Nhận định:** Human approval cho hành động phá hủy chưa có trường chuẩn trong CACAO, chỉ có lệnh `manual`. Nghiên cứu mới (SOCpilot) cụ thể hóa nó thành rule `require_approval` và `prohibit_before` có thể kiểm tra tất định. Đây là mẫu đáng chú ý cho cổng CI và cho kiểm soát AI agent.
- **Nhận định:** Học thuật đánh giá chất lượng playbook theo ba trục chính: (a) tái sử dụng và chia sẻ (Schlette 2024, Akbari Gurabi 2024); (b) đúng cú pháp, ngữ nghĩa và luồng điều khiển so với tham chiếu (Gurabi 2025: syntax, field fidelity, GED); (c) tuân thủ policy về thứ tự và phê duyệt (SOCpilot 2026). Chưa có benchmark chuẩn cho playbook SOAR thực thi được.
- **Nhận định:** Phát hiện của Bridges 2023 (SOAR tăng tốc độ nhưng có thể giảm độ chính xác và đầy đủ của ticket) là bằng chứng thực nghiệm rằng tiêu chí chất lượng phải đo cả độ chính xác và đầy đủ của đầu ra, không chỉ thời gian.

### Khoảng trống
- Không đọc được toàn văn CACAO v2.0 (docs.oasis-open.org bị chặn): chưa có câu chữ conformance (mục 11), chưa có nội dung data marking, authentication info chi tiết, cũng như khác biệt v1.0 so với v2.0. Truy vấn đã thử: "CACAO Security Playbooks v2.0 specification playbook types signatures", "github oasis-tcs cacao ... markdown".
- Chưa có danh sách đầy đủ 16 yêu cầu của Akbari Gurabi 2024 và Table 4 (thuộc tính + metric) của Islam & Babar 2019. Cả hai đều bị chặn toàn văn.
- Chưa có câu chữ gốc NIST 800-61r3 về automation/playbook (nvlpubs bị chặn). Các mô tả RS.MA/RS.MI lấy từ mirror bậc 3.
- Chưa có tiêu chí chi tiết của aspect "SecOps automation" trong SOC-CMM (soc-cmm.com chưa thử được).
- Không tìm thấy ENISA report nào chuyên về chất lượng playbook. Chưa chạy truy vấn riêng cho ENISA.
- Không tìm thấy paper "Empl & Pernul" chuyên về chất lượng playbook. Chỉ có Schlette et al. 2024 (Empl, Pernul là đồng tác giả) và Empl & Pernul 2023 "Generating ICS vulnerability playbooks with open standards" (IJIS, chỉ thấy tiêu đề) — [ResearchGate](https://www.researchgate.net/publication/376411868_Generating_ICS_vulnerability_playbooks_with_open_standards).
- Không có chuẩn nào về idempotency, retry, giới hạn phạm vi trigger hay hiệu năng playbook.

## Câu hỏi phụ 2b: Danh sách tiêu chí chất lượng ứng viên, kèm nguồn hỗ trợ

### Kết luận ngắn
Có thể dựng khoảng 14 tiêu chí. Mỗi tiêu chí có ít nhất một nguồn chuẩn hoặc học thuật hỗ trợ một phần, nhưng 4 tiêu chí (idempotency, retry/backoff, phạm vi trigger, hiệu năng) gần như không có nguồn chuẩn hay học thuật và phải dựa vào vendor/practitioner. Độ chắc chắn: **trung bình**.

### Phát hiện có nguồn (bảng tổng hợp; nguồn chi tiết ở mục trên)

| # | Tiêu chí | Hình thức trong chuẩn/nghiên cứu | Nguồn hỗ trợ |
|---|---|---|---|
| 1 | Hợp lệ cú pháp/schema | Trường bắt buộc; workflow phải có start, action và end | CACAO v2 schema; Gurabi 2025 (syntax checker) |
| 2 | Đúng đắn ngữ nghĩa và luồng điều khiển | Khớp tham chiếu theo trường; graph edit distance; không deadlock/livelock | Gurabi 2025; Springer 2025 model-based IR plan; BPMN→Petri net |
| 3 | Mục đích và phạm vi rõ ràng | `description`, `playbook_types`, `playbook_activities` khớp step | CACAO v2; Schlette 2024 (định nghĩa playbook mơ hồ) |
| 4 | Xử lý lỗi | `on_failure`, `workflow_exception` | CACAO v2 |
| 5 | Timeout / không treo vô hạn | `timeout` → `ACTION_TIMEOUT`; engine nên áp max timeout | CACAO v2 |
| 6 | Đánh giá tác động/rủi ro của hành động | `impact` (tác động khi thực thi), `priority`, `severity` | CACAO v2 |
| 7 | Human-in-the-loop / phê duyệt hành động nguy hiểm | lệnh `manual`; rule `require_approval`, `prohibit_before` | CACAO v2 (gián tiếp); SOCpilot 2026; Bridges 2023 (analyst senior thích cân bằng) |
| 8 | Trách nhiệm và audit | `created_by`, `owner` theo step, `modified`, name dùng cho log | CACAO v2 |
| 9 | Phiên bản và vòng đời (retire) | `id`+`modified`, `revoked`, `valid_from/until`, `derived_from` | CACAO v2; Tsirakis 2025 (KMS vòng đời) |
| 10 | Toàn vẹn và nguồn gốc | Chữ ký JSS bất đối xứng, countersign | CACAO v2 |
| 11 | Bảo mật credential và dữ liệu | `authentication_info_definitions` tách riêng; TLP/IEP marking; sanitize trước khi chia sẻ | CACAO v2; Akbari Gurabi 2024 (confidentiality) |
| 12 | Module hóa và tái sử dụng | `playbook-action` gọi playbook con; reusability (R.3); playbook công khai khó dùng ngay | CACAO v2; Akbari Gurabi 2024; Schlette 2024 |
| 13 | Interoperability / machine-readable | Tuân thủ BPMN/CACAO/JSON (R.1); interoperability là thuộc tính thiếu bằng chứng | Akbari Gurabi 2024; Islam & Babar 2019 |
| 14 | Ánh xạ use case và kỹ thuật phòng thủ | `external_references`, `related_to` (STIX); RE&CT Response Action; D3FEND↔ATT&CK | CACAO v2; RE&CT; D3FEND |
| 15 | Hiệu quả vận hành và độ chính xác đầu ra | Hiệu suất, context switching, độ chính xác và đầy đủ của ticket; usability | Bridges 2023; Islam & Babar 2019 |
| 16 | Được diễn tập và cải tiến liên tục | Playbook phải diễn tập và cập nhật sau sự cố | NIST 800-61r3 (qua thứ cấp); ISO 27035-2 (lessons learned); RE&CT stage Lessons Learned |
| — | Idempotency, retry/backoff, phạm vi trigger, hiệu năng/throughput | **Không thấy trong chuẩn hay paper đã xem** | Cần nguồn vendor/practitioner (câu phụ 1, 3) |

### Nhận định
- **Nhận định:** Các tiêu chí 1, 3–6, 8–11 kiểm được tĩnh, tức có thể tự động hóa thành lint/CI. Tiêu chí 2 cần test, simulation hoặc model checking. Tiêu chí 7 có thể kiểm tất định bằng policy rule kiểu SOCpilot. Các tiêu chí 15–16 chỉ đo được khi vận hành.
- **Nhận định:** Nếu công ty không dùng CACAO làm định dạng thực thi, vẫn có thể dùng CACAO làm "checklist tham chiếu" cho metadata playbook nội bộ.

### Khoảng trống
- Bảng trên do agent tổng hợp. Chưa có nguồn nào công bố một bộ tiêu chí playbook tương đương để đối chiếu.

## Truy vấn đã chạy
- CACAO Security Playbooks v2.0 specification playbook types signatures (standard)
- Empl Pernul security playbooks survey interoperability (standard)
- formal verification security playbooks SOAR paper (extended)
- github oasis-tcs cacao security playbooks v2 spec markdown (standard)
- NIST SP 800-61r3 playbooks automation incident response recommendations (standard)
- SOC-CMM automation SOAR capability maturity aspects (standard)
- "Do You Play It by the Books" playbook quality criteria findings (standard)
- Schlette Empl Caselli Schreck Pernul 2024 playbooks 1217 analysis results reuse quality (extended)
- NIST SP 800-61 Rev. 3 playbooks automation "RS.MA" incident response (extended)
- arXiv 2503.05206 playbook (standard)
- "Requirements for Playbook-Assisted Cyber Incident Response, Reporting and Automation" requirements list (extended)
- "From Legacy to Standard" LLM CACAO playbooks evaluation syntactic semantic accuracy (extended)
- RE&CT framework response actions ATC project stages categories (standard)
- Islam Babar Nepal multivocal review security orchestration quality attributes (extended)
- model checking incident response playbook verification CACAO BPMN Petri net (extended)
- D3FEND mapping SOAR playbook countermeasures automation (standard)
- "Multi-Vocal Review of Security Orchestration" quality attributes ... table (extended)
- Akbari Gurabi playbook requirements sixteen reusability confidentiality adaptability machine-readable list (extended)
- "Operationalizing Cybersecurity Knowledge" CACAO playbooks knowledge management system evaluation (extended)
- "Testing SOAR Tools in Use" Bridges ORNL evaluation criteria results (extended)
- ISO/IEC 27035-2:2023 incident response playbooks automation guidance (extended)
- CISA Federal Government Cybersecurity Incident Vulnerability Response Playbooks 2021 standardized playbook purpose (standard)
- LLM generated incident response playbook evaluation metrics CACAO correctness 2025 (extended)
- SOCpilot verifying policy compliance LLM incident response typed verifier action catalog destructive actions approval (extended)
- NIST CSF 2.0 RS.MI-01 RS.MI-02 ... RS.MA-05 text (standard)
- WebFetch trực tiếp: GitHub oasis-open/cacao-json-schemas (playbook.json, workflow-step.json, signature.json, playbook-processing-summary.json, command-data.json), github.com/atc-project/atc-react. Bị chặn: docs.oasis-open.org, nvlpubs.nist.gov, arxiv.org, dl.acm.org, researchgate, publica-rest.fraunhofer.de, epub.uni-regensburg.de, www.oasis-open.org.
