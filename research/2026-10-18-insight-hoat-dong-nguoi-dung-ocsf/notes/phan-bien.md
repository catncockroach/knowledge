# Phản biện: giới hạn của "cứ đưa log cho LLM là nó kể được người dùng đã làm gì"

Ghi chú về độ tin: những số liệu đánh dấu *(snippet)* mới chỉ thấy qua kết quả search hoặc trang tóm tắt, chưa mở được nguồn gốc. Writer nên coi chúng là chỉ dấu, chưa phải số đã xác minh.

## 1. (Câu phụ 6) LLM sai ở đâu khi đọc log dài và dữ liệu event có cấu trúc

### Kết luận ngắn
Có nhiều bằng chứng độc lập: độ chính xác của LLM giảm mạnh khi ngữ cảnh dài ra (kể cả những model quảng cáo 128K+), kém nhất ở các tác vụ đếm/gộp trên nhiều mục (đúng dạng việc "tóm tắt một ngày hoạt động"), nhạy với định dạng serialize, và log là một kênh prompt injection đã được đo đạc. Mức chắc chắn: **cao** cho suy giảm ngữ cảnh dài và prompt injection (nhiều benchmark bậc 1, có bình duyệt). **Trung bình** cho con số cụ thể trên log bảo mật (preprint 2026 chưa bình duyệt).

### Phát hiện có nguồn

**Ngữ cảnh dài suy giảm**
- "Lost in the Middle": độ chính xác phụ thuộc vị trí thông tin. Cao khi thông tin nằm đầu hoặc cuối ngữ cảnh, giảm khi nằm giữa (đường cong hình chữ U), kể cả với model chuyên ngữ cảnh dài. Đo trên multi-doc QA và key-value retrieval. — [Liu et al., Lost in the Middle, TACL vol.12 tr.157–173](https://aclanthology.org/2024.tacl-1.9/) (bậc 1, 2024; arXiv 07/2023)
- RULER: 17 model long-context, 13 tác vụ. Gần như đạt điểm tuyệt đối với needle-in-a-haystack cơ bản nhưng "almost all" giảm mạnh khi ngữ cảnh dài ra. Mọi model đều tuyên bố hỗ trợ ≥32K token, nhưng chỉ khoảng một nửa giữ được hiệu năng chấp nhận được ở 32K. — [Hsieh et al., RULER, COLM 2024](https://arxiv.org/abs/2404.06654) (bậc 1, 2024-04/08)
- NoLiMa: needle ít trùng từ với câu hỏi, nên model phải suy luận liên kết chứ không khớp chuỗi được. Ở 32K, 11/13 model rơi xuống dưới 50% mức baseline ngữ cảnh ngắn. GPT-4o giảm từ 99,3% xuống 69,7%. Reasoning model và CoT không khắc phục hết. Bản arXiv ghi 12 model và 10 model rơi dưới 50%, khác bản ICML. — [Modarressi et al., NoLiMa, ICML 2025](https://proceedings.mlr.press/v267/modarressi25a.html) (bậc 1, 2025)
- Context Rot (Chroma): 18 LLM (GPT-4.1, Claude 4, Gemini 2.5, Qwen3…). Chỉ thay đổi độ dài input, độ tin cậy của output giảm ngay cả với tác vụ đơn giản. Distractor gần nghĩa làm kết quả tệ hơn. — [Hong, Troynikov, Huber, Context Rot](https://trychroma.com/research/context-rot) (bậc 1 nhưng là báo cáo kỹ thuật của vendor, không bình duyệt, 2025-07-14)

**Đếm, gộp, quan hệ thời gian**
- Oolong yêu cầu phân tích từng mẩu văn bản rồi gộp lại để trả lời câu hỏi phân phối (phân loại, đếm, quan hệ thời gian và người dùng). GPT-5, Claude Sonnet 4 và Gemini 2.5 Pro đều dưới 50% accuracy trên cả hai split ở 128K. — [Bertsch et al., Oolong, arXiv 2511.02817](https://arxiv.org/abs/2511.02817) (bậc 1, preprint 11/2025, sửa 10/2026)
- Một bản replication Oolong (Recursive Language Models) phải đính chính: con số 87,8% exact match từng công bố bị thổi phồng vì nhãn ground-truth lọt vào context. Khi có nhãn, một regex cũng đạt khoảng 100%. Bài học: tác vụ gộp là việc của code tất định. — [OOLONG replication README](https://cdn.jsdelivr.net/gh/Cornjebus/rlm-replication-study@main/README.md) (bậc 3, *(snippet)*, không rõ ngày)
- Test of Time (Google): benchmark tổng hợp về suy luận thời gian (ToT-Semantic: logic thời gian; ToT-Arithmetic: tính toán mốc và khoảng thời gian), khảo sát ảnh hưởng của cấu trúc bài toán, kích thước và **thứ tự đưa fact vào**. Ví dụ được nêu: model trả lời đúng khi có tên thật nhưng sai khi tên bị ẩn danh, tức là dựa vào kiến thức sẵn có thay vì suy luận. — [Fatemi et al., Test of Time, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/eb7295a8bc613b375726659c2ecd6f14-Abstract-Conference.html) (bậc 1, 2025). Ví dụ Gemini lấy từ [Liner review](https://liner.com/review/test-of-time-a-benchmark-for-evaluating-llms-on-temporal) (bậc 3)

**Nhạy với định dạng serialize (bảng hoặc dữ liệu có cấu trúc)**
- ToRR: kể cả model mạnh cũng hành xử giòn khi đổi định dạng hay nhiễu bảng, và không có định dạng nào luôn tốt nhất. Tác giả khuyến nghị đánh giá trên nhiều định dạng. — [ToRR, arXiv 2502.19412](https://arxiv.org/html/2502.19412v3) (bậc 1, 2025) *(snippet)*
- TQA-Bench: Markdown cho accuracy tốt hơn CSV/JSON/HTML với đa số model. HTML tốn khoảng 3 lần token so với CSV cho cùng một database. — [TQA-Bench, arXiv 2411.19504](https://arxiv.org/pdf/2411.19504) (bậc 1, 2024) *(snippet)*
- Survey bảng: đổi thứ tự input hay bỏ dấu phân tách làm giảm tới 20%, bỏ few-shot làm giảm tới 50% (trích từ Sui et al., 2024). — [Tabular Data Understanding with LLMs survey, arXiv 2508.00217](https://arxiv.org/pdf/2508.00217) (bậc 1, 2025) *(snippet)*

**Prompt injection qua nội dung log**
- OWASP LLM01:2025 định nghĩa indirect prompt injection là khi LLM nhận input từ nguồn ngoài (website, file) có chứa chỉ thị. Các biện pháp: ràng buộc hành vi model; định nghĩa và **kiểm tra định dạng output bằng code tất định**; lọc input/output; least privilege; human approval cho hành động rủi ro cao; **tách và đánh dấu nội dung không tin cậy**; adversarial testing. — [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) (bậc 1, 2025)
- "Poisoning the Watchtower": kẻ tấn công kiểm soát các field user agent, URL, payload, DNS query, username thử đăng nhập, rồi nhét chỉ thị vào. Analyst là gpt-4o-mini, 48 tổ hợp chiến lược × defense × tác vụ. Kết quả:
  - Direct override ("ignore previous…") **0%** suppression trên tác vụ phân loại.
  - Persona hijack suppress 68% log độc hại khi dùng classifier ngây thơ.
  - Context manipulation đạt 96% khi không có phòng thủ, còn 38% khi ràng buộc output.
  - **Tóm tắt (summarization) là tác vụ rủi ro nhất.**
  - Phòng thủ mạnh nhất hạ tỷ lệ thành công trung bình từ 26,6% xuống 11,8%, giảm chứ không loại bỏ được.

  — [Pandey & Bhujang, arXiv 2605.24421](https://arxiv.org/abs/2605.24421) (bậc 1, preprint 2026-05-23, chưa bình duyệt)
- "Context Contamination": khái niệm "passive prompt injection", payload nằm sẵn trong log rồi kích hoạt khi analyst hỏi LLM. Benchmark LogInject-1.0 gồm 12.847 entry, trong đó 2.569 entry độc. Thử trên 3 LLM production với 4 mục tiêu tấn công: che giấu hoạt động, tạo false positive, rò rỉ thông tin, chiếm output. Kết quả:
  - ASR tối đa 88,2%, trung bình 83,4%.
  - "Context Stitching" (chia payload ra nhiều entry để qua mặt bộ lọc stateless) đạt 76,4%.
  - Phòng thủ nhiều lớp (lọc input + harden prompt + kiểm tra output) giảm 90,4% số tấn công nhưng vẫn còn 8,4% lọt.

  — [Karanjai et al., arXiv 2607.14493](https://arxiv.org/abs/2607.14493) (bậc 1, preprint 2026-07-16)

**Quyền riêng tư khi gửi telemetry lên LLM cloud**
- LLM-Redactor so sánh 8 kỹ thuật (inference local, redaction placeholder, rephrase, TEE, HE, MPC…). Kết hợp route local + redaction + rephrase hạ rò rỉ PII còn 0,6%, nhưng 31% mã độc quyền vẫn lộ. TEE, HE và MPC phần lớn còn ở mức nghiên cứu. — [LLM-Redactor, arXiv 2604.12064 (qua Emergent Mind)](https://www.emergentmind.com/papers/2604.12064) (bậc 2–3, 2026) *(snippet)*
- Tài liệu của chính một proxy ẩn PII (PrivAiTe) thừa nhận: phát hiện mang tính thống kê, "never 100%". Ngữ cảnh xung quanh vẫn có thể định danh người dùng dù tên đã bị thay. Với GDPR/HIPAA nên coi đây là "pseudonymization + transfer minimization, not anonymization". — [privaite trên PyPI](https://pypi.org/project/privaite/0.4.1/) (bậc 3, tài liệu sản phẩm, 2026) *(snippet)*

### Nhận định
- **Nhận định:** Bài toán "tóm tắt một ngày thành các hoạt động" về bản chất là tác vụ kiểu Oolong: phân loại từng event hay phiên rồi đếm và gộp theo thời gian. Đây đúng là chỗ frontier model ở 128K đạt dưới 50%. Vì vậy phải đếm, gộp, sắp xếp và tính khoảng thời gian bằng code. LLM chỉ nên nhận các đơn vị đã gộp sẵn (phiên hay cụm hoạt động có kèm số đếm) và viết lời.
- **Nhận định (ước lượng, không có nguồn đo):** Một event OCSF dạng JSON đầy đủ cỡ vài trăm đến vài nghìn token. Với 100k–500k event, đưa thô vào prompt sẽ ra khoảng 10⁷–10⁸ token mỗi batch, vượt xa mọi context window và rơi đúng vào vùng suy giảm mà RULER, NoLiMa và Context Rot đã đo. Muốn số token tăng chậm hơn n thì bắt buộc phải nén hoặc gộp trước, không chỉ vì chi phí.
- **Nhận định:** Telemetry Windows chứa nhiều field do kẻ tấn công hoặc bên thứ ba điều khiển: command line, URL, tên file, tiêu đề cửa sổ, DNS query, username sai. Hai preprint 2026 cho thấy summarization là tác vụ dễ bị injection nhất. Pipeline nên (a) không đưa chuỗi thô vào prompt khi template hay nhãn đủ dùng, (b) bọc và đánh dấu nội dung không tin cậy, (c) kiểm tra output tất định (mọi event, entity và số liệu LLM nêu phải tra được trong dữ liệu).
- **Nhận định:** Telemetry endpoint chứa đường dẫn có username, URL, tên tài liệu, IP nội bộ. Redaction chỉ giảm chứ không xóa được rủi ro, nên dùng LLM local cho bước chạm vào chuỗi thô, LLM cloud chỉ nhận bản tóm lược đã trừu tượng hóa. Đây là đánh đổi cần nêu trong report.

### Khoảng trống
- Chưa tìm được benchmark nào đo trực tiếp hallucination khi LLM đọc **log endpoint hay OCSF** (sinh ra process, file hay URL không có thật). Bằng chứng gần nhất nằm ở mục 2 và 4 (bug report, incident summary). Đã thử: "LLM log summarization hallucination evaluation study logs".
- Chưa có số đo chi phí và độ trễ thực tế cho 100k+ event. Phần token ở trên là ước lượng của agent.
- Số liệu ToRR, TQA-Bench và LLM-Redactor mới thấy qua snippet, chưa mở bài gốc.

## 2. Khi nào luật / thống kê / ML cổ điển thắng LLM trên tác vụ log

### Kết luận ngắn
Với **gom nhóm template** (bước then chốt để nén n event), Drain, một phương pháp thống kê O(n), vẫn dẫn đầu về grouping accuracy trên Loghub-2.0 và thuộc số ít parser chạy xong toàn bộ dataset lớn. LLM parser thắng ở độ chính xác từng template (PA), nhưng thường phải dựa vào cache hay khung kiểu Drain. Với **phát hiện bất thường**, model nhỏ fine-tune hoặc ML đơn giản thường ngang hoặc hơn LLM prompt-based, rẻ hơn nhiều bậc. Mức chắc chắn: **trung bình–cao** (ISSTA 2024, ICSE 2024 có bình duyệt; benchmark 2026 là preprint một tác giả).

### Phát hiện có nguồn
- Loghub-2.0: 14 dataset, trung bình 3,6 triệu dòng mỗi dataset, đánh giá lại 15 parser. Kết quả:
  - "Drain is the most performant parsers that are more capable of grouping log messages, as evidenced by the highest average GA and FGA".
  - Parser ngữ nghĩa (LogPPT, UniParser) có PA và FTA cao hơn hẳn nhưng GA và FGA "generally lower".
  - 9/15 parser không xử lý xong mọi dataset trong 12 giờ. Drain thuộc 6 parser chạy xong. CPU time của LogPPT "considerably higher" so với Drain.
  - FGA của Drain giảm từ 0,75 (Loghub-2k) xuống khoảng 0,55 (Loghub-2.0), tức là ngay cả Drain cũng kém đi trên dữ liệu thực tế lớn.
  - Log của sự kiện hiếm vẫn là thách thức chưa giải.

  — [Jiang et al., A Large-Scale Evaluation for Log Parsing Techniques: How Far Are We?, ISSTA 2024](https://arxiv.org/html/2308.10828v2) (bậc 1, 2023-08/2024-03)
- LILAC (LLM parser có adaptive cache) chọn Drain và AEL làm baseline cú pháp vì chúng mạnh nhất trong nhóm này. Hướng LLM parser hiện đại cần cache để giảm số lời gọi. — [LILAC, arXiv 2310.01796](https://arxiv.org/pdf/2310.01796) (bậc 1, 2023) *(snippet)*
- Một benchmark 2025 gồm 29 cách tiếp cận LLM parser kết luận LLM parser chính xác và tổng quát hơn **với điều kiện** có caching và retrieval augmentation. — [alphaxiv overview 2504.04877](https://alphaxiv.org/overview/2504.04877v2) (bậc 3, *(snippet)*; mâu thuẫn một phần với kết quả GA của Loghub-2.0 ở trên)
- ICSE 2024 ("Deep Learning or Classical Machine Learning?"): thuật toán đơn giản thắng deep learning cả về tốc độ lẫn độ chính xác. Trên Thunderbird, KNN huấn luyện nhanh hơn NeuralLog khoảng 1.000 lần và có F1 cao hơn 0,0625. — [ICSE 2024 research track](https://conf.researchr.org/details/icse-2024/icse-2024-research-track/21/Deep-Learning-or-Classical-Machine-Learning-An-Empirical-Study-on-Log-Based-Anomaly-) (bậc 1, 2024) *(snippet)*
- Benchmark 2026 trên HDFS, BGL, Thunderbird và Spirit: transformer fine-tune (BERT, RoBERTa) đạt F1 0,96–0,99. LLM prompt-based (GPT-3.5, GPT-4, LLaMA-3) zero-shot chỉ đạt 0,82–0,91, lợi thế duy nhất là không cần nhãn. — [Patel, LLM-Enhanced Log Anomaly Detection, arXiv 2604.12218](https://arxiv.org/abs/2604.12218) (bậc 1, preprint một tác giả, 2026-04-14)
- Trong một bảng so sánh, LogGPT (LLM) đạt F1 72,56% so với 87,31% của LogRobust (truyền thống). LogGPT recall tuyệt đối nhưng precision thấp vì gắn cờ cả những vấn đề nhỏ. — [RuAG, arXiv 2411.03349](https://arxiv.org/pdf/2411.03349) (bậc 1, 2024) *(snippet)*

### Nhận định
- **Nhận định:** Với pipeline này, Drain-like template mining hay so khớp theo (class_uid, activity_id, process image) là lựa chọn mặc định cho bước nén: O(n), tất định, gom nhóm tốt hơn LLM. LLM nên dùng để **đặt tên hay giải nghĩa template hoặc cụm** (số lượng tăng chậm hơn n nhiều), không dùng để parse từng event. Điều này khớp với việc các LLM parser tốt nhất đều phải cache.
- **Nhận định:** Telemetry OCSF đã là dữ liệu có cấu trúc, nên lợi thế "hiểu log tự do" của LLM nhỏ hơn so với log text trên Loghub. Phần lớn công việc (lọc, nhóm, đếm) là truy vấn có cấu trúc, nơi code thắng tuyệt đối về độ đúng.

### Khoảng trống
- Chưa có so sánh trực tiếp LLM với luật hay thống kê cho việc **gán nhãn hoạt động người dùng** trên telemetry endpoint. Các benchmark trên là parsing và anomaly detection, không phải activity labeling.
- Chưa mở bản đầy đủ để lấy số chi phí và độ trễ của benchmark 2604.12218.

## 3. Mơ hồ nền tảng: telemetry mức thấp có xác định được ý định hay hành động "người" không?

### Kết luận ngắn
Không xác định hoàn toàn được. Bằng chứng forensic và host-log cho thấy event do nền hoặc hệ thống sinh ra áp đảo về số lượng, ngay cả artifact "hướng người dùng" như UserAssist cũng có thể do tiến trình tự động sinh ra, và chuyển event mức thấp thành hành động mức người dùng vẫn là việc thủ công của analyst. Mức chắc chắn: **trung bình**, vì có nhiều nguồn chỉ cùng hướng nhưng chưa có benchmark hệ thống nào đo tỷ lệ phân biệt người và máy trên telemetry Windows.

### Phát hiện có nguồn
- Verma & Bridges (ORNL) dựng metric space trên Windows Event Log và dùng nó để phân cụm log và chuỗi ngắn nhằm "identify and visualize user behaviors and background processes over time". Bài coi việc tách tiến trình nền khỏi hành vi người dùng là bài toán riêng cần xử lý. — [Defining a Metric Space of Host Logs and Operational Use Cases, IEEE BigData 2018](https://arxiv.org/abs/1811.00591v1) (bậc 1, 2018-11). Một tóm tắt search cho rằng bài nêu log nền "vastly outnumber" log do người dùng, nhưng chưa mở được bản gốc để xác nhận câu này *(snippet)*.
- Magnet Forensics: entry UserAssist có thể do tiến trình tự động sinh ra (shell preloading, refresh shortcut) chứ không chỉ do người dùng chủ động. Bộ đếm focus time vẫn chạy khi người dùng rời máy. — [Magnet Forensics, Artifact Profile: UserAssist](https://www.magnetforensics.com/blog/artifact-profile-userassist/) (bậc 2, không rõ ngày) *(snippet)*
- Telemetry chẩn đoán của Windows được ghi định kỳ, không phụ thuộc hành vi cụ thể, khác với Registry, Prefetch và Event Log vốn phát sinh khi có hành động người dùng hoặc sự kiện hệ thống. — [Forensic analysis of the Windows telemetry for diagnostics, arXiv 2002.12506](https://arxiv.org/pdf/2002.12506) (bậc 1, 2020) *(snippet)*
- Phỏng vấn analyst bảo mật: một event mức thấp thường không đủ để hiểu hay phản ứng. Analyst dựa nhiều vào thao tác thủ công để chuyển system event thành hành động mức người dùng. — [How do information security workers use host data?, arXiv 1812.02867](https://arxiv.org/pdf/1812.02867) (bậc 1, 2018) *(snippet)*
- Ở mảng gần (log của công cụ sáng tạo), muốn dựng lại workflow người dùng phải lọc trước các server call thừa và event đồng bộ trạng thái. — [From Logs to Agents, arXiv 2603.07609](https://arxiv.org/html/2603.07609v1) (bậc 1, 2026) *(snippet)*
- Một bài forensic thời LLM nêu việc phân biệt artifact do người, do máy hay do agent cộng tác sinh ra là "novel challenge", vì signature forensic truyền thống không cho biết nguồn gốc. Agent AI chạy trên máy (ví dụ Claude Code) làm mờ thêm ranh giới "hoạt động người". — [Digital Forensics in the Age of Large Language Models, arXiv 2504.02963](https://arxiv.org/pdf/2504.02963) (bậc 1, 2025) *(snippet)*
- Các tín hiệu thường dùng để phân biệt người và tự động, dù không tín hiệu nào đáng tin một mình: nhịp thời gian (người không đều, script đều hoặc dồn dập), danh tính tài khoản dịch vụ so với tài khoản người, tốc độ và tính ngẫu nhiên của input event. — [patent USPTO 11483324](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11483324) (bậc 1 về tuyên bố, không phải bằng chứng hiệu quả) và [Kinsta](https://kinsta.com/blog/bot-traffic-vs-real-visits/) (bậc 3, chỉ làm manh mối)

### Nhận định
- **Nhận định:** Gắn nhãn "người" cho hoạt động là **suy luận xác suất**, không phải sự thật đọc ra từ log. Các tín hiệu khả dĩ trong OCSF/Windows: logon type (interactive hoặc RDP so với service hoặc batch), process lineage có explorer.exe hay shell người dùng làm tổ tiên so với services.exe, svchost hay Task Scheduler, tài khoản SYSTEM hay service so với tài khoản người, nhịp thời gian. Đây là heuristic của agent, chưa có nguồn đo độ chính xác, nên writer cần ghi rõ.
- **Nhận định:** Timeline nên kèm **mức tin cậy và lý do** cho mỗi hoạt động ("có khả năng do người khởi tạo vì cha là explorer.exe, logon interactive") thay vì khẳng định. Nên tách riêng các khoảng không có telemetry (agent tắt, máy sleep) để LLM không "lấp" chỗ trống bằng câu chuyện.
- **Nhận định:** LLM dễ áp đặt ý định ("người dùng muốn…"). Từ log chỉ có thể suy ra **hành động quan sát được**, không suy ra được ý định. Prompt và định dạng output nên cấm ngôn ngữ ý định nếu không có bằng chứng.

### Khoảng trống
- Chưa tìm được nghiên cứu có ground truth đo tỷ lệ phân biệt event do người và do hệ thống trên Sysmon hay Windows Security. Đã thử: "distinguishing user-initiated vs automated activity host logs", "digital forensics attributing actions to user vs system automated Windows artifacts", "inferring high-level user activities from low-level host events".
- Bản gốc bài ORNL (osti.gov) không truy cập được (ECONNREFUSED), nên chưa xác minh tỷ lệ log nền so với log người dùng.

## 4. Bằng chứng LLM tóm tắt log hay sự cố làm sai lệch, và rủi ro với analyst

### Kết luận ngắn
Có bằng chứng thực nghiệm trực tiếp trong mảng bảo mật: summary sự cố do LLM tự viết bỏ sót chi tiết quan trọng ở 35% trường hợp và/hoặc chèn thông tin sai ở 42% (18 analyst, 50 sự cố thật). Analyst có xu hướng tin dần thành chấp nhận không phê phán. Mức chắc chắn: **cao** cho số liệu Kramer et al. (SOUPS 2025, bình duyệt). **Trung bình** cho phần automation bias (định tính).

### Phát hiện có nguồn
- Kramer et al. (Google), 18 analyst, 50 sự cố thật: LLM tự hành tạo summary "omit critical details in 35% of cases and/or inject factual inaccuracies in 42% of cases". LLM "may lack the security reasoning necessary to operate autonomously". Khi dùng cộng tác, LLM giảm công sức và tăng độ dễ đọc và nhất quán. — [Integrating Large Language Models into Security Incident Response, SOUPS 2025](https://www.usenix.org/conference/soups2025/presentation/kramer) (bậc 1, 2025)
- Phỏng vấn 25 người làm SOC: lo ngại trung tâm là phụ thuộc quá mức. Dùng liên tục làm giảm khả năng tự kiểm tra, và khi niềm tin tăng thì hành vi trôi dần về chấp nhận không phê phán. — [From Chasing Ghosts to Missed Attacks, arXiv 2608.00672](https://arxiv.org/html/2608.00672) (bậc 1, preprint 2026) *(snippet)*
- Scoping review 599 bài: tự động hóa trong SOC làm tăng automation bias và complacency, analyst không đi tìm thông tin xác nhận hay phản bác. — [Automation Bias and Complacency in SOCs, MDPI Computers 13(7):165](https://www.mdpi.com/2073-431X/13/7/165) (bậc 1, 2024) *(snippet)*
- Brian Carrier (Cyber Triage) kể ví dụ thực tế: Claude khẳng định hostname "co1bld" trong file LNK là hạ tầng build chuẩn của Microsoft nên không đáng ngờ. Khi bị hỏi nguồn, model thừa nhận "I don't have a reliable citation". Ba loại lỗi: bịa enrichment, kết luận không đủ căn cứ, và lỗi kiến thức chung mà model thứ hai có thể lặp lại. — [DFIR + AI Primer: How to Combat Hallucinations, Cyber Triage](https://www.cybertriage.com/ai/dfirai-primer-how-to-combat-hallucinations/) (bậc 2, chuyên gia có tên tuổi, 2026-05-28)
- GenDFIR (RAG cho timeline sự cố) tự nhận output là dự đoán xác suất mà expert không trực tiếp kiểm soát được, và LLM hiện chưa đạt độ chính xác đầy đủ cho phân tích timeline. Chỉ thử trên sự cố tổng hợp. — [GenDFIR, arXiv 2409.02572](https://arxiv.org/pdf/2409.02572) (bậc 1, 2024) *(snippet)*
- Mảng gần: trong 80 summary bug report do LLM viết, khoảng 47,9% thiếu thông tin và 12,3% có nội dung bịa. — [Empirical Analysis and Detection of Hallucinations…, arXiv 2605.24137](https://www.alphaxiv.org/abs/2605.24137.md) (bậc 1, preprint 2026) *(snippet)*
- Sách dài (FABLES, 3.158 claim, 26 cuốn sách xuất bản 2023–2024): tỷ lệ claim đáng tin là khoảng 90% với Claude 3 Opus, 78% với GPT-4/4 Turbo, 72% với GPT-3.5 Turbo, 70% với Mixtral. Lỗi tập trung vào **sự kiện, nhân vật, quan hệ**, và nhiều lỗi chỉ lộ ra khi suy luận gián tiếp. — [The Decoder, về FABLES arXiv 2404.01261](https://the-decoder.com/anthropics-claude-3-beats-openais-gpt-4-at-text-summarization/) (bậc 2, 2024) *(snippet; chưa đối chiếu bài gốc)*

### Nhận định
- **Nhận định:** Tỷ lệ 35% bỏ sót và 42% sai lệch là trên summary sự cố, với input đã được analyst chọn lọc. Với timeline từ hàng trăm nghìn event thô, rủi ro nhiều khả năng còn cao hơn. Lỗi "event, entity, quan hệ" của FABLES ứng đúng với process, file, user và quan hệ cha–con trong timeline.
- **Nhận định:** Theo Kramer et al., thiết kế hợp lý là "analyst-in-the-loop": LLM soạn lời từ dữ liệu đã gộp, người hoặc code kiểm tra, có nhãn rõ phần nào do AI sinh.

### Khoảng trống
- Chưa có nghiên cứu người dùng nào về việc analyst bị **timeline hoạt động** do LLM viết dẫn sai. Kramer et al. là summary sự cố, không phải timeline người dùng.

## 5. (Câu phụ 5, phần phản biện) Điểm yếu của cách đánh giá tóm tắt và các kiểm tra faithfulness nên dùng

### Kết luận ngắn
ROUGE và các metric trùng lặp từ không đo được tính trung thực: đảo "increased" thành "decreased" không làm đổi ROUGE-L. Metric dựa trên QA hay NLI tương quan với người tốt hơn, nhưng bộ phát hiện hallucination tốt nhất vẫn chỉ khoảng 50% trên FaithBench. Với dữ liệu có cấu trúc như OCSF, kiểm tra tất định (mọi entity, thời điểm, số đếm trong output phải tra được về event gốc) mạnh hơn mọi metric văn bản. Mức chắc chắn: **cao** cho điểm yếu của ROUGE, **trung bình** cho khuyến nghị cụ thể.

### Phát hiện có nguồn
- GO FIGURE (meta-evaluation): ROUGE-1 và ROUGE-L không đo đúng sự thiếu nhất quán sự thật trên nhiều domain. Ví dụ: đổi "decreased" thành "increased" đảo nghĩa câu nhưng ROUGE-L không đổi. — [GO FIGURE, arXiv 2010.12834](https://arxiv.org/pdf/2010.12834) (bậc 1, 2020) *(snippet)*
- QAGS (metric dựa trên hỏi–đáp) đạt tương quan Pearson 54,52 với đánh giá factuality của người trên CNN/DailyMail, so với 17,72 của ROUGE-2. — [Wang et al., QAGS, arXiv 2004.04228](https://alphaxiv.org/abs/2004.04228) (bậc 1, 2020) *(snippet)*
- Survey về đánh giá văn bản sinh: các metric tương đồng không đo được faithfulness (Maynez et al.). Metric huấn luyện trên lỗi chèn nhân tạo có thể không tổng quát, vì lỗi nhân tạo hiếm khi giống lỗi thật của model. — [Repairing the Cracked Foundation, arXiv 2202.06935](https://arxiv.org/pdf/2202.06935) (bậc 1, 2022) *(snippet)*
- Kryściński et al.: 60/200 (30%) summary abstractive có vấn đề nhất quán. Giao thức đánh giá chủ yếu dựa vào ROUGE nên không bắt được lỗi này. — [Neural Text Summarization: A Critical Evaluation, arXiv 1908.08960](https://arxiv.org/pdf/1908.08960) (bậc 1, 2019) *(snippet)*
- FaithBench (10 LLM hiện đại, nhãn do chuyên gia gán): bộ phát hiện hallucination tốt nhất chỉ đạt gần 50% accuracy. — [FaithBench, NAACL 2025 short](https://aclanthology.org/2025.naacl-short.38) (bậc 1, 2025) *(snippet)*
- REFLEX (đánh giá tóm tắt log không cần tham chiếu, dùng LLM làm giám khảo): tương quan tốt với sở thích của người trên nhiều dataset log. Tác giả ghi rằng ROUGE gặp khó vì summary log có thể khác chữ nhưng cùng nghĩa. — [REFLEX, arXiv 2511.07458](https://arxiv.org/html/2511.07458v1) (bậc 1, 2025) *(snippet)*
- Khuyến nghị thực hành từ DFIR:
  - **Existence check**: truy vấn tất định xác nhận mọi item AI nhắc tới (path, timestamp) có trong dữ liệu.
  - Judge LLM thứ hai bắt được lỗi suy luận nhưng có thể bỏ sót lỗi kiến thức mà hai model cùng mắc.
  - Mức kiểm tra tỷ lệ với mức rủi ro.
  - Gắn nhãn nội dung do AI sinh.

  — [Cyber Triage primer](https://www.cybertriage.com/ai/dfirai-primer-how-to-combat-hallucinations/) (bậc 2, 2026-05-28)
- OWASP: kiểm tra định dạng output bằng code tất định. — [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) (bậc 1, 2025)

### Nhận định
- **Nhận định:** Bộ kiểm tra faithfulness phù hợp cho timeline OCSF, xếp theo thứ tự ưu tiên:
  1. Output có cấu trúc (JSON), mỗi hoạt động kèm danh sách ID event hoặc cụm làm bằng chứng.
  2. Code kiểm tra mọi entity (process, file, URL, user), mốc thời gian và số đếm đều khớp với event được trích. Câu nào có claim không truy về được event thì bị loại.
  3. Kiểm tra độ phủ (coverage): bao nhiêu % cụm hoạt động lớn trong ngày được nhắc tới, nhằm bắt lỗi bỏ sót kiểu 35% của Kramer.
  4. LLM-judge hoặc NLI chỉ là lớp bổ sung, vì FaithBench cho thấy bộ phát hiện tự động vẫn yếu.
  5. Đánh giá thủ công trên mẫu có ground truth.

  Không dùng ROUGE làm metric chính.
- **Nhận định:** Lợi thế của bài toán này so với tóm tắt văn bản tự do là "nguồn sự thật" có cấu trúc, nên kiểm tra tất định khả thi và rẻ (O(số claim)). Đây là điểm cần tận dụng.

### Khoảng trống
- Chưa có metric hay benchmark chuẩn nào cho "timeline hoạt động từ telemetry endpoint". Các metric trên đều xuất phát từ tóm tắt văn bản. Phần ground truth hoạt động thuộc câu phụ 5 do researcher khác phụ trách.

## Truy vấn đã chạy
- NoLiMa long-context evaluation beyond literal matching (standard)
- Chroma context rot report LLM input tokens (standard)
- LLM log parsing empirical study Drain comparison LogHub accuracy (standard)
- prompt injection via log data LLM security analyst attack (standard)
- LLM log anomaly detection empirical study traditional deep learning outperform (standard)
- LLM table serialization format sensitivity benchmark performance varies (standard)
- Oolong benchmark long-context aggregation counting LLM (standard)
- Test of Time benchmark LLM temporal reasoning ordering events (standard)
- DFIR AI generated timeline hallucination forensic analyst risk (extended)
- distinguishing user-initiated vs automated activity host logs human interaction (extended)
- ROUGE fails factual consistency summarization evaluation faithfulness survey (standard)
- digital forensics attributing actions to user vs system automated Windows artifacts study (extended)
- FABLES faithfulness book-length summarization unfaithful claims LLM (standard)
- LLM summaries security analysts automation bias trust study SOC (extended)
- Kramer LLM incident summarization analysts 50 real-world incidents omit critical details (extended)
- Lost in the Middle: How Language Models Use Long Contexts TACL (standard)
- privacy-preserving LLM log analysis sensitive data cloud local model logs PII (standard)
- LLM log summarization hallucination evaluation study logs (standard)
- inferring high-level user activities from low-level host events semantic gap background noise (extended)
- "Defining a Metric Space of Host Logs and Operational Use Cases" (standard)
