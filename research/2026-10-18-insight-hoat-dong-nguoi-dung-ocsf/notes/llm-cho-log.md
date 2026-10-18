# Dùng LLM để biến log/chuỗi event thành tóm tắt và tường thuật

## Câu phụ 2a: LLM cho log parsing (LILAC, LogBatcher, DivLog, LLMParser…) và kết quả đo được

### Kết luận ngắn
Các parser LLM tốt nhất hiện nay chỉ gọi LLM cho mỗi template mới, không gọi cho mỗi dòng log, nhờ có cache template. Ví dụ, LILAC chỉ cần khoảng 280 lời gọi cho một dataset khoảng 3,6 triệu dòng mà vẫn chính xác hơn Drain. Mức chắc chắn **cao**: số liệu lấy từ paper gốc (FSE/ASE 2024), dù tác giả tự đánh giá trên benchmark Loghub.

### Phát hiện có nguồn
- LILAC gồm một parser dùng ICL (in-context learning) và một "adaptive parsing cache". Cache là một cây: mỗi nút trung gian là một token, `<*>` là wildcard, mỗi lá là một template. Tra cứu chỉ cần duyệt một lần từ gốc tới lá. Trung bình mỗi dataset Loghub-2.0 (khoảng 3,6 triệu message) cần **279,7 lời gọi LLM**, so với trung bình 249 template thật. Các phương pháp LLM trước đó cần hơn 3,6 triệu lời gọi. — [LILAC (arXiv 2310.01796v3)](https://arxiv.org/html/2310.01796v3) (bậc 1, FSE 2024)
- Độ chính xác trung bình của LILAC trên Loghub-2.0 (GA/FGA/PA/FTA, %) là 92,7/92,4/84,2/81,0. Drain đạt 84,3/55,4/46,8/28,2, LogPPT đạt 61,2/57,4/73,6/47,8. Model là gpt-3.5-turbo-0613, temperature 0. Một lần chạy LILAC mất trung bình 569,6 s mỗi dataset, so với 425,4 s của Drain. Trong đó 66% thời gian dành cho thao tác cache, chỉ 34% cho lời gọi LLM. — [LILAC](https://arxiv.org/html/2310.01796v3) (bậc 1, 2024)
- LogBatcher không cần demonstration. Pipeline của nó gồm các bước sau:
  - Mask số, IP và URL rồi vector hóa bằng TF-IDF, gom cụm bằng DBSCAN (eps 0,5, min_samples 5).
  - Khớp với template đã có trong cache bằng regex.
  - Với log chưa khớp, lấy một batch khoảng 10 log đa dạng (lấy mẫu DPP) trong mỗi cụm và gửi vào một prompt.

  Trên 16 dataset Loghub-2k, tổng token trung bình là 11.701, so với 24.020 của LILAC và 469.109 của DivLog. Token mỗi lời gọi là 173, 309 và 235 tương ứng. Batch 5–10 log cho kết quả tốt nhất, batch 1 log thì kém đi. Câu "giảm chi phí ít nhất 106%" trong phần giới thiệu của paper là sai về mặt số học. — [LogBatcher (arXiv 2406.06156v2)](https://arxiv.org/html/2406.06156v2) (bậc 1, ASE 2024)
- DivLog đạt PA 98,1%, PTA 92,1% và RTA 92,9% trung bình trên 16 dataset theo paper gốc. Tuy vậy, DivLog phải gọi LLM cho mỗi log nên tổng token rất lớn (xem bảng LogBatcher). — [DivLog (arXiv 2307.09950)](https://arxiv.org/abs/2307.09950v3) (bậc 1, ICSE 2024); [LogBatcher](https://arxiv.org/html/2406.06156v2) (bậc 1)
- LLMParser fine-tune các LLM nhỏ. Kết quả được thuật lại là PA trung bình khoảng 96% trên 16 hệ thống, và Flan-T5-base ngang LLaMA-7B mà suy luận nhanh hơn. Con số này lấy từ snippet tìm kiếm, chưa đọc bản đầy đủ. — [LLMParser (arXiv 2404.18001)](https://arxiv.org/pdf/2404.18001) (bậc 1, 2024)
- Survey LLM4Log (145 paper, thu thập tới 11/2025) nêu năm mẫu thiết kế lặp lại: prompting/ICL, retrieval grounding, fine-tuning, agent/tool, và verification. Rủi ro triển khai gồm độ trễ, chi phí, giới hạn context, quyền riêng tư và hallucination. Survey nhấn mạnh grounding/faithfulness cho output dành cho người vận hành. Log summarization là một task riêng trong survey. — [LLM4Log (arXiv 2604.16359)](https://arxiv.org/abs/2604.16359) (bậc 1, 2026-03, v3 2026-09)

### Nhận định
- **Nhận định:** Với OCSF thì message tự do không phải là vấn đề chính, vì event đã có cấu trúc. Phần đáng học từ log parsing là **mẫu "cache theo chữ ký + chỉ gọi LLM khi gặp chữ ký mới"**. Trong OCSF, "template" tương ứng với một tổ hợp kiểu `(class_uid, activity_id, process.name, parent, đường dẫn đã chuẩn hóa, domain đã rút gọn…)`. Số chữ ký bị chặn bởi sự đa dạng hành vi, không tăng theo n.
- **Nhận định:** Phần chuỗi tự do trong OCSF (command line, URL, đường dẫn file) có thể được "template hóa" bằng Drain hoặc LILAC trước khi gán nhãn.

### Khoảng trống
- Chưa có benchmark parsing LLM nào chạy trên Windows/Sysmon/OCSF. Loghub chủ yếu gồm HDFS, BGL, OpenStack, Zookeeper…, chỉ có một dataset Windows (CBS log).
- Chưa lấy được bảng so sánh cùng điều kiện cho cả LogPrompt, LLMParser và DivLog. Benchmark 2025 (arXiv 2504.04877) có thể có, nhưng chưa đọc.

## Câu phụ 2b: Serialize/nén event có cấu trúc trước khi prompt (JSON, bảng hay text theo template; chọn field; chi phí token)

### Kết luận ngắn
Chưa có định dạng nào tốt nhất cho mọi trường hợp. Hiệu quả phụ thuộc vào model và task. CSV/Markdown rẻ token hơn JSON/HTML. Đưa vào biểu diễn đã trừu tượng hóa (cạnh provenance, câu "góc nhìn chủ thể") giảm khối lượng hàng trăm lần, nhưng không phải model nào cũng làm tốt hơn với nó. Mức chắc chắn **trung bình**: các nghiên cứu mâu thuẫn nhau và ít nghiên cứu đo trên log bảo mật.

### Phát hiện có nguồn
- Nghiên cứu của Google trên log tấn công đối chiếu log thô (auditd/ProcMon) với biểu diễn cạnh provenance SPADE (subject–object–action, sắp theo thời gian):
  - Khối lượng chênh nhau rất lớn: một kịch bản có 1.229.728 dòng thô nhưng chỉ 5.198 dòng cạnh. Tác giả gọi ProcMon thô là "simply too verbose and voluminous to be practically used as inputs to LLMs".
  - Chunk log thô gồm 1.000 dòng, chunk cạnh gồm 400 dòng, mỗi chunk khoảng 100–128k token.
  - Hiệu quả phụ thuộc vào model: biểu diễn cạnh luôn giúp Llama 4 Maverick, còn Gemini 2.5 Pro làm tốt hơn trên log thô ở mọi task.
  - Với dữ liệu cạnh, chunk 200/400/800/1.600 dòng cho kết quả khá ổn định, nhưng 200 dòng đôi khi thiếu ngữ cảnh.
  
  — [Benchmarking and Exploring the Capabilities of LLMs for Attack Investigations (arXiv 2606.10281v2)](https://arxiv.org/html/2606.10281v2) (bậc 1, 2026-06/09)
- ADL-LLM (nhận dạng hoạt động sống hằng ngày từ cảm biến nhà thông minh) là phép tương tự gần nhất với bài toán "event → hoạt động người":
  - Event được chuyển thành câu viết **theo góc nhìn chủ thể** ("After t2−t1 seconds, they close the fridge door"), dùng thời gian tương đối. Mỗi cửa sổ mở đầu bằng độ dài cửa sổ, thời điểm trong ngày và vị trí, rồi tới các trạng thái "already active", sau đó là hành động theo từng phòng.
  - Prompt dùng chain-of-thought và một danh sách nhãn đóng.
  - Với gpt-3.5-turbo zero-shot, weighted F1 đạt 0,94, 0,75 và 0,80 trên ba dataset (UCI A, UCI B, MARBLE), ngang các mô hình giám sát (0,97, 0,75 và 0,82 với DeepConvLSTM).
  - Thêm few-shot k=7, lấy theo độ tương đồng embedding, với 5% dữ liệu huấn luyện thì vượt DeepConvLSTM (MARBLE 0,80 so với 0,75).
  - Llama-2-13b chỉ đạt 0,68, còn gpt-4o đạt 0,84 nhưng tốn khoảng 10 lần chi phí.
  - Độ trễ khoảng 2 s mỗi cửa sổ, so với dưới 1 ms của baseline.
  
  — [ADL-LLM (arXiv 2407.01238v3)](https://arxiv.org/html/2407.01238v3) (bậc 1, 2024)
- Bài tiếp nối năm 2026 cho rằng cửa sổ thời gian cố định không hợp với event thưa. Bài đề xuất phân đoạn theo event kèm ước lượng độ tin cậy, vượt cả cách dùng cửa sổ thời gian lẫn mô hình giám sát với Gemma 3 27B. Bài đang chờ bình duyệt, thông tin lấy từ snippet. — [Improving Zero-shot ADL Recognition… (arXiv 2601.08241)](https://www.arxiv.org/pdf/2601.08241) (bậc 1, 2026, preprint)
- Kết quả về định dạng bảng mâu thuẫn nhau:
  - TQA-Bench: Markdown cho kết quả tốt nhất với đa số LLM, CSV tiết kiệm token nhất, HTML tốn gần gấp 3 token. — [TQA-Bench (arXiv 2411.19504)](https://arxiv.org/pdf/2411.19504) (bậc 1, 2024)
  - Một nghiên cứu trích xuất từ tài liệu dài cho độ chính xác khoảng 0,70 với plain text, 0,69 với CSV, 0,51 với HTML và 0,46 với XML. — [arXiv 2305.16344](https://arxiv.org/pdf/2305.16344) (bậc 1, 2023)
  - "Table Meets LLM" (WSDM 2024) chỉ kết luận rằng định dạng input, thứ tự nội dung, role prompt và dấu phân vùng đều ảnh hưởng tới kết quả. Thứ hạng HTML > XML > JSON > Markdown chỉ thấy qua một blog thứ cấp, chưa xác minh trong paper. — [Sui et al. (arXiv 2305.13062)](https://arxiv.org/abs/2305.13062) (bậc 1, 2023/2024)
- Timesketch (Google, mã nguồn mở) có tính năng `llm_summarize`. Nó chạy một query, **chỉ giữ cột `message` và loại trùng (`drop_duplicates(subset="message")`)**, rồi `json.dumps` danh sách đó vào placeholder `<EVENTS_JSON>` trong prompt template. Nó đếm số "unique events sent to the LLM" làm metric Prometheus. Nhận xét này rút ra từ việc đọc source. — [timesketch/lib/llms/features/llm_summarize.py](https://github.com/google/timesketch/blob/master/timesketch/lib/llms/features/llm_summarize.py) (bậc 1, source code, đọc 2026-10-18)
- Elastic Attack Discovery gửi alert (không phải event thô) cho LLM. Mặc định là 100 alert, tối đa 500. Mỗi lời gọi phải chỉ định `anonymizationFields`, tức danh sách field được phép gửi và field bị làm mờ. Field ngoài ECS bị loại trừ trừ khi người dùng cho phép. Gửi nhiều alert hơn mức model chịu được có thể gây lỗi. — [Elastic docs: Attack Discovery](https://www.elastic.co/docs/solutions/security/ai/attack-discovery) (bậc 1, docs chính thức, không rõ ngày); [Run Attack Discovery in a workflow](https://www.elastic.co/docs/solutions/security/ai/attack-discovery/run-attack-discovery-in-a-workflow) (bậc 1)
- Các công cụ nén log cho LLM như logzip (thay pattern lặp bằng legend, tự báo tiết kiệm 52–58%, mặc định lossy) hay ctrlb-decompose (CLP + Drain3) chỉ có số liệu do tác giả tự công bố. — [logzip (PyPI)](https://pypi.org/project/logzip/) (bậc 3, chỉ làm manh mối)

### Nhận định
- **Nhận định:** Với OCSF khoảng 500 field, cách mà các hệ thống thật đang dùng là **allowlist field theo class**, giống `anonymizationFields` của Elastic hay việc Timesketch chỉ gửi `message`. Kết hợp với loại trùng, cách này có thể kéo prompt từ JSON đầy đủ xuống một vài field mỗi event.
- **Nhận định:** Cách làm của ADL-LLM gợi ý một bước nên có: viết event thành câu ngắn theo góc nhìn người dùng, dùng thời gian tương đối, gom theo phiên. Bước này hợp hơn đưa JSON OCSF thô vào prompt để gán nhãn hoạt động "người". Cần thử với chính model định dùng vì hiệu quả của biểu diễn phụ thuộc model (theo arXiv 2606.10281).
- **Nhận định:** Nếu dữ liệu có dạng bảng thì CSV hoặc Markdown với cột cố định cho mỗi class OCSF là lựa chọn mặc định hợp lý về token. JSON lặp lại tên khóa ở mọi bản ghi.

### Khoảng trống
- Chưa tìm thấy nghiên cứu nào đo trực tiếp hiệu quả JSON, bảng và text theo template trên event OCSF hay Sysmon, gồm cả số token và độ chính xác gán nhãn.
- Chưa đọc được phần prompt template mặc định của Timesketch (`llm_summarize` prompt file).

## Câu phụ 2c: Gán nhãn hoạt động cho cụm/phiên bằng LLM, và mẫu "LLM gán nhãn mẫu → mô hình nhẹ/cluster xử lý phần còn lại"

### Kết luận ngắn
Mẫu được kiểm chứng rõ nhất gồm ba bước: trích thuộc tính, gom cụm (embedding + k-means hoặc theo chữ ký), rồi cho LLM đặt tên và mô tả từng cụm từ vài mẫu đại diện, có thể dựng phân cấp. Cách thứ hai là cho LLM sinh taxonomy và nhãn giả, rồi huấn luyện một bộ phân loại nhẹ để chạy ở quy mô lớn. Mức chắc chắn **trung bình–cao**: có số liệu từ Anthropic (Clio) và Microsoft (TnT-LLM), nhưng trên dữ liệu hội thoại chứ không phải log.

### Phát hiện có nguồn
- Clio (Anthropic) hoạt động qua bốn bước:
  1. Trích "facet" cho từng hội thoại, một số tính trực tiếp, một số do model sinh.
  2. Embed một facet dạng văn bản rồi gom cụm bằng k-means.
  3. Model đọc các mẫu trong cụm để viết tiêu đề và tóm tắt.
  4. Gom cụm đệ quy thành cây nhiều tầng bằng k-means và prompting.
  
  Trên 19.476 hội thoại tổng hợp có nhãn thật, Clio dựng lại đúng danh mục với độ chính xác 94% (ngẫu nhiên là 5%). Ước tính chi phí cho 100.000 hội thoại là 48,81 USD. — [Clio (arXiv 2412.13678)](https://arxiv.org/html/2412.13678v1) (bậc 1, 2024-12)
- TnT-LLM (Microsoft) có hai pha. Pha 1, LLM sinh và tinh chỉnh taxonomy nhãn bằng suy luận nhiều bước zero-shot. Pha 2, LLM làm người gán nhãn để tạo dữ liệu huấn luyện, nhờ đó "lightweight supervised classifiers can be reliably built, deployed, and served at scale". Hệ thống được áp dụng cho intent của Bing Copilot. Trang abstract không có số liệu chi phí cụ thể. — [TnT-LLM (arXiv 2403.12173)](https://arxiv.org/abs/2403.12173) (bậc 1, 2024-03)
- ADL-LLM gán một nhãn hoạt động cho mỗi cửa sổ event từ danh sách nhãn đóng. Nó yếu với các hoạt động có mẫu cảm biến giống nhau (dọn bàn, bày bàn, ăn nguội). Model nhỏ hay phá format và tự bịa nhãn. — [ADL-LLM](https://arxiv.org/html/2407.01238v3) (bậc 1, 2024)
- Một nghiên cứu zero-shot phân cấp trên dataset van Kasteren (đoán vị trí trước rồi mới đoán hoạt động) cho kết quả khiêm tốn: ChatGPT đạt macro-F 26,63%, cách hai bước dùng SBERT đạt 37,83%. — [Hierarchical Zero-Shot Approach for HAR in Smart Homes (Ulster, UCAmI 2024)](https://pure.ulster.ac.uk/en/publications/hierarchical-zero-shot-approach-forhuman-activity-recognition-ins/) (bậc 1, 2024; số liệu lấy từ snippet)

### Nhận định
- **Nhận định:** Áp vào OCSF, pipeline sẽ gồm các bước sau:
  1. Gom phiên theo khoảng trống thời gian và entity (process tree, logon session).
  2. Tạo chữ ký cho phiên (tập/đa tập các chữ ký event).
  3. Gom cụm chữ ký.
  4. Gọi LLM một lần cho mỗi cụm mới để đặt nhãn "người", kèm vài phiên mẫu.
  5. Lưu nhãn vào cache theo chữ ký.

  Số lời gọi LLM khi đó tỉ lệ với số cụm hay chữ ký khác nhau, không tỉ lệ với n.
- **Nhận định:** Kết quả của ADL-LLM (zero-shot ngang mô hình giám sát với nhãn đóng) và Clio (94% tái tạo danh mục) cho thấy gán nhãn cấp cụm/phiên khả thi. Bằng chứng trên endpoint log thì chưa có.

### Khoảng trống
- Chưa tìm thấy paper nào đo độ chính xác LLM khi gán nhãn hoạt động người dùng (duyệt web, cập nhật phần mềm, lập trình…) từ telemetry Windows hay OCSF. Truy vấn đã thử: "LLM summarize Windows event logs Sysmon user activity narrative" (extended) không ra nghiên cứu có đánh giá.

## Câu phụ 2d: Agent LLM truy vấn log qua tool/SQL thay vì đọc event thô

### Kết luận ngắn
Mẫu phổ biến có ba bước: bắt đầu từ một truy vấn tổng quan (đếm, top-k), cho agent gọi SQL có giới hạn (theo thời gian, số dòng, chỉ SELECT), rồi để một LLM khác tóm tắt. Độ chính xác hiện còn thấp với bài điều tra mở (model tốt nhất trên ExCyTIn chỉ đạt reward 0,368). NL→SQL đơn giản thì dễ hơn (khoảng 85–88%). Mức chắc chắn **trung bình**: chủ yếu là preprint.

### Phát hiện có nguồn
- Trên ExCyTIn-Bench (Microsoft Security AI Research cùng các trường đại học), 57–59 bảng log kiểu Sentinel và 589 câu hỏi, agent mỗi lượt chạy một truy vấn SQL hoặc nộp đáp án:
  - Kết quả trả về bị giới hạn 15 dòng và 100.000 ký tự, tối đa 25 bước.
  - Reward trung bình là 0,249. Model tốt nhất là o4-mini với 0,368, sau đó là GPT-4.1 với 0,338.
  - Tỉ lệ query thành công tương quan với reward ở mức r = 0,86.
  - Bỏ bảng alert làm giảm hiệu quả (0,213 so với 0,260). Cửa sổ thời gian dài hơn cũng làm giảm (0,248).
  - Model nhỏ hay nộp đáp án sớm.
  
  — [ExCyTIn-Bench (arXiv 2507.14201)](https://arxiv.org/html/2507.14201v1) (bậc 1, 2025-07)
- Paper "Towards Agentic Investigation of Security Alerts" bắt đầu bằng một "overview query" đếm event, alert, top signature và top IP. Investigator LLM chọn trong các query định sẵn cộng thêm tối đa một SQL tự do (một SELECT trên một bảng). Mọi query bị giới hạn thời gian, tham số hóa và trả về 1–5 kết quả. Một Summary LLM riêng đưa ra kết luận. Thông tin lấy từ snippet tìm kiếm. — [arXiv 2604.25846](https://arxiv.org/pdf/2604.25846) (bậc 1, 2026-04, preprint)
- SherAgent cho rằng LLM không bị ràng buộc sẽ bị "semantic drift and dependency explosion due to overly broad querying". Nó dùng SQL lặp kết hợp lọc ngữ nghĩa. Thông tin lấy từ snippet. — [SherAgent (arXiv 2607.09176)](https://arxiv.org/pdf/2607.09176) (bậc 1, 2026-07, preprint)
- Benchmark của Sophos (14 model): NL→SQL với schema và 3 ví dụ, 100 truy vấn, đạt 88% với GPT-4 và 85% với CodeLlama-34B, Claude-Instant và Claude-v2. Tác giả kết luận đây là task "relatively easy". — [Sophos: Benchmarking the security capabilities of LLMs](https://www.sophos.com/en-us/blog/benchmarking-the-security-capabilities-of-large-language-models) (bậc 1, báo cáo của chính tổ chức, 2024)
- Timesketch có tính năng `nl2q` (ngôn ngữ tự nhiên → query) và `log_analyzer`. `log_analyzer` stream **toàn bộ** event trong timeline tới một provider bên ngoài (Sec-Gemini, commit 2026-06/07 thêm chế độ "BYOT"), nhận về JSON findings rồi tạo đối tượng DFIQ. — [timesketch/lib/llms/features](https://github.com/google/timesketch/tree/master/timesketch/lib/llms/features) (bậc 1, source code, đọc 2026-10-18)

### Nhận định
- **Nhận định:** Với batch hàng trăm nghìn event, agent truy vấn hợp nhất ở vai trò **bổ sung**. Agent đọc bảng tổng hợp đã tính sẵn theo ngày, phiên và cụm, và chỉ gọi SQL khoan sâu khi cần bằng chứng. Agent không nên là cơ chế chính để sinh timeline, vì số bước và độ chính xác của nó chưa ổn định theo ExCyTIn.

### Khoảng trống
- Chưa đọc bản đầy đủ của arXiv 2604.25846 và SherAgent. Các chi tiết trên chỉ lấy từ snippet.

## Câu phụ 2e: Tóm tắt phân cấp / map-reduce và tường thuật timeline/sự cố do LLM sinh

### Kết luận ngắn
Với văn bản dài, gộp phân cấp (map-reduce) cho kết quả mạch lạc hơn và ít lỗi bỏ sót hơn cập nhật tăng dần, trừ khi chunk rất lớn. Trên dữ liệu sự cố thật, tóm tắt LLM tự động vẫn bỏ sót chi tiết quan trọng (35%) và sai sự thật (42%). Khi analyst cùng làm với LLM thì kết quả tốt hơn. Mức chắc chắn **cao** về hướng chung, **trung bình** khi suy rộng sang log.

### Phát hiện có nguồn
- BooookScore so sánh hai cách tóm tắt sách dài, chia chunk:
  - Hierarchical merging thắng incremental updating ở hầu hết cấu hình (GPT-4, chunk 2048: 89,1 so với 82,5; Claude 2: 91,1 so với 78,6). Ngoại lệ là Claude 2 với chunk 88K, khi incremental đạt 90,9 so với 90,3.
  - Incremental chi tiết hơn: người chấm chọn nó vì độ chi tiết 83% số lần. Nhưng nó có nhiều lỗi bỏ sót entity, event và quan hệ nhân quả hơn, và tốn hơn (GPT-4: 873 USD so với 628 USD).
  - Lỗi bỏ sót là loại lỗi phổ biến nhất ở cả hai cách.
  
  — [BooookScore (arXiv 2310.00785, ICLR 2024)](https://arxiv.org/html/2310.00785v2) (bậc 1, 2023/2024)
- Google (SOUPS 2025) làm thí nghiệm với 18 analyst trên 50 sự cố thật. LLM tự động "omit critical details in 35% of cases and/or inject factual inaccuracies in 42% of cases". Khi dùng cộng tác, LLM giảm công sức của analyst và tăng tính dễ đọc, nhất quán. — [Integrating LLMs into Security Incident Response (Kramer et al., SOUPS 2025)](https://www.usenix.org/conference/soups2025/presentation/kramer) (bậc 1, 2025)
- Sophos thử tóm tắt sự cố trên 310 sự cố MDR. Input là chuỗi event JSON có schema khác nhau tùy sensor, kèm một template output cố định (tóm tắt, host, user, event, file, command line). GPT-4 dẫn đầu, Llama-70B tốt nhất trong nhóm mở. CodeLlama-34B cho output không dùng được và có phần bịa. — [Sophos benchmark](https://www.sophos.com/en-us/blog/benchmarking-the-security-capabilities-of-large-language-models) (bậc 1, 2024)
- Studiawan, Breitinger và Scanlon (DFRWS APAC 2025) đánh giá LLM cho phân tích timeline pháp y:
  - Kịch bản Windows 11 (duyệt Bing/Google, tải và cài Firefox, tìm SQL injection) được trích bằng Plaso sang CSV. Timeline đầy đủ vượt giới hạn token nên chỉ đưa khoảng 2.000 dòng vào ChatGPT-4o. File khoảng 10 MB trở lên thường lỗi.
  - Ở task tóm tắt event (so với dftpl), ROUGE chỉ đạt 0,134 (một event) và 0,106 (nhiều event) khi không có thêm tri thức. Có thêm tri thức thì lên 1,0 và 0,775.
  - Tác giả kết luận ChatGPT kém hơn cách dựa trên luật/regex do người điều tra dùng.
  
  — [Towards a standardized methodology… (arXiv 2505.03100)](https://arxiv.org/html/2505.03100v1) (bậc 1, 2025)
- GenDFIR có ba bước: lọc bằng luật trước, mỗi event thành một chunk được embed (mxbai-embed-large), rồi RAG với Llama-3.1-8B chạy local trên GPU 8 GB để sinh báo cáo timeline. Thử trên 6 kịch bản tổng hợp, tổng cộng chỉ 177 event (121 chunk sau khi lọc). Bảng accuracy cho 75 fact đúng và 5 sai từ knowledge base. — [GenDFIR (arXiv 2409.02572v3)](https://arxiv.org/html/2409.02572v3) (bậc 1, 2024/2025)
- Auto-Prov dùng LLM chuyển log thành đoạn văn có cấu trúc mô tả entity và tương tác để dựng provenance graph, rồi tóm tắt tấn công bằng ngôn ngữ tự nhiên. Chưa đọc phần đánh giá. — [Auto-Prov (arXiv 2603.17100)](https://arxiv.org/html/2603.17100v1) (bậc 1, 2026-03)

### Nhận định
- **Nhận định:** Tường thuật theo ngày hợp với cấu trúc map-reduce: phiên → khối hoạt động → ngày → (tùy chọn) cả batch. Mỗi tầng chỉ đọc output đã nén của tầng dưới. Số lời gọi bằng số phiên hay cụm cần mô tả cộng số ngày, không tỉ lệ với n. Lỗi chính cần chống là **bỏ sót**, theo cả BooookScore lẫn Google. Vì vậy các con số (đếm, khoảng thời gian, số lần đăng nhập thất bại) nên được tính bằng code rồi chèn vào, không để LLM tự đếm.
- **Nhận định:** Các thí nghiệm pháp y hiện có đều rất nhỏ (2.000 dòng, 177 event), nên chưa có bằng chứng LLM "đọc" trực tiếp hàng trăm nghìn event được.

### Khoảng trống
- Chưa tìm thấy hệ thống công khai nào sinh timeline hoạt động **người dùng** theo ngày từ telemetry endpoint mà có đánh giá định lượng. Các nghiên cứu hiện có đều đặt khung sự cố hoặc tấn công.

## Câu phụ 5 (phần LLM): Đánh giá tóm tắt log do LLM sinh

### Kết luận ngắn
Thực tế đang chia thành ba hướng: (1) metric chồng lấp từ (ROUGE/BLEU/METEOR/BERTScore) so với gold summary, bị chính các tác giả chê là không đo ngữ nghĩa; (2) đếm fact đúng/sai, bỏ sót/sai lệch, do chuyên gia chấm; (3) bắt LLM trích ID event gốc rồi kiểm bằng code. Chưa có metric chuẩn nào cho tóm tắt log. Mức chắc chắn **trung bình–cao**.

### Phát hiện có nguồn
- Paper DFRWS dùng BLEU/ROUGE và buộc output theo format cố định để so được. Paper thừa nhận metric bỏ qua tương đương ngữ nghĩa và phạt tóm tắt nhiều event chỉ vì khác thứ tự. — [arXiv 2505.03100](https://arxiv.org/html/2505.03100v1) (bậc 1, 2025)
- Sophos dùng năm metric để so với gold summary do GPT-4 viết nháp rồi analyst sửa: LCS và Levenshtein cho từng fact trích xuất, BERTScore, độ tương đồng embedding ADA2, và METEOR. Bài tự nêu thiên lệch: GPT-4 có lợi thế vì đã tham gia tạo gold. — [Sophos](https://www.sophos.com/en-us/blog/benchmarking-the-security-capabilities-of-large-language-models) (bậc 1, 2024)
- Google (SOUPS 2025) dùng analyst thật để đánh giá tỉ lệ bỏ sót chi tiết quan trọng (35%) và sai sự thật (42%). — [Kramer et al.](https://www.usenix.org/conference/soups2025/presentation/kramer) (bậc 1, 2025)
- GenDFIR đo accuracy theo số fact đúng/sai so với knowledge base, cùng relevance, exact match và độ tương đồng top-k. — [GenDFIR](https://arxiv.org/html/2409.02572v3) (bậc 1)
- REFLEX (11/2025) tự nhận là metric không cần tham chiếu, chấm bằng LLM, cho tóm tắt log, dùng dataset LogSummary với nhóm khoảng 20 dòng log. Nhưng phần phương pháp lại mô tả cosine Sentence-BERT so với tóm tắt tham chiếu, và không đưa ra hệ số tương quan nào với người chấm. Đây là bằng chứng yếu. — [REFLEX (arXiv 2511.07458)](https://arxiv.org/html/2511.07458v1) (bậc 1, preprint chất lượng thấp, 2025-11)
- BooookScore là metric tự động đo độ mạch lạc: GPT-4 chấm từng câu theo phân loại lỗi (bỏ sót entity/event/nhân quả, mâu thuẫn, trùng lặp). Cách chấm này tốn kém vì gọi model một lần cho mỗi câu. — [BooookScore](https://arxiv.org/html/2310.00785v2) (bậc 1)
- **Grounding bằng ID event**: `log_analyzer` của Timesketch yêu cầu mỗi finding có `record_ids`. Finding thiếu ID bị từ chối ("Finding is missing its associated Timesketch event IDs"). Mỗi ID được tra lại thành `Event` trong sketch, và finding không liên kết được event nào thì báo "Could not link any events from the finding". — [log_analyzer.py](https://github.com/google/timesketch/blob/master/timesketch/lib/llms/features/log_analyzer.py) (bậc 1, source code, đọc 2026-10-18)
- Survey LLM4Log nêu "verification" là một trong năm mẫu thiết kế chính, và coi grounding/faithfulness là thách thức mở. — [LLM4Log](https://arxiv.org/abs/2604.16359) (bậc 1, 2026)

### Nhận định
- **Nhận định:** Với timeline hoạt động người, cách kiểm tra rẻ và chắc nhất có ba bước. (1) Bắt mỗi dòng timeline mang ID phiên/cụm hoặc ID event mẫu. (2) Dùng code kiểm rằng ID tồn tại, thời gian của chúng nằm đúng ngày và khoảng giờ đã ghi, và các con số khớp với aggregate. (3) Lấy mẫu một phần để người chấm theo hai trục bỏ sót và sai sự thật, như Google đã làm. ROUGE/BLEU ít giá trị nếu không có gold summary.

### Khoảng trống
- Chưa có dataset công khai nào có ground truth "hoạt động người dùng theo ngày" trên telemetry Windows. Dataset DFRWS (Zenodo) là ứng viên gần nhất: một kịch bản có ghi màn hình làm ground truth.
- Chưa đọc được PDF đầy đủ của Google SOUPS 2025 (môi trường thiếu công cụ đọc PDF) để lấy rubric chấm chi tiết.

## Mẫu thiết kế giữ số lời gọi LLM và số token tăng chậm hơn n

### Kết luận ngắn
Mọi hệ thống có số liệu tốt đều làm ba việc: (1) loại trùng hoặc gom theo chữ ký/template trước, (2) gọi LLM cho mỗi chữ ký **mới** và cache kết quả, (3) đưa vào prompt các batch nhỏ đa dạng hoặc bản tổng hợp, không đưa từng event. Mức chắc chắn **cao** cho log parsing (có số đo), **trung bình** khi áp sang tóm tắt hoạt động.

### Phát hiện có nguồn
- Cache template giúp LILAC chỉ cần khoảng 280 lời gọi cho khoảng 3,6 triệu dòng, so với hơn 3,6 triệu lời gọi nếu gọi cho từng dòng. — [LILAC](https://arxiv.org/html/2310.01796v3) (bậc 1)
- LogBatcher kết hợp cụm, cache và batch đa dạng khoảng 10 log. Tổng token chỉ bằng khoảng một nửa LILAC và khoảng 1/40 DivLog. — [LogBatcher](https://arxiv.org/html/2406.06156v2) (bậc 1)
- Timesketch loại trùng theo `message` trước khi đưa vào prompt. — [llm_summarize.py](https://github.com/google/timesketch/blob/master/timesketch/lib/llms/features/llm_summarize.py) (bậc 1)
- Clio gọi LLM để đặt tên cụm từ vài mẫu chứ không gọi cho từng phần tử. Chi phí khoảng 49 USD cho 100.000 phần tử, đã tính cả bước trích facet cho từng hội thoại. — [Clio](https://arxiv.org/html/2412.13678v1) (bậc 1)
- TnT-LLM dùng LLM gán nhãn một mẫu rồi chưng cất sang bộ phân loại nhẹ để chạy ở quy mô lớn. — [TnT-LLM](https://arxiv.org/abs/2403.12173) (bậc 1)
- Elastic gửi alert đã tổng hợp với số lượng có trần (100–500) và allowlist field. ExCyTIn giới hạn kết quả query ở 15 dòng mỗi bước. Cả hai đều giữ token mỗi lời gọi bị chặn trên, độc lập với n. — [Elastic](https://www.elastic.co/docs/solutions/security/ai/attack-discovery) (bậc 1); [ExCyTIn](https://arxiv.org/html/2507.14201v1) (bậc 1)
- Biểu diễn đã trừu tượng hóa (cạnh provenance) giảm khoảng 237 lần số dòng trong một kịch bản (1.229.728 → 5.198). — [arXiv 2606.10281v2](https://arxiv.org/html/2606.10281v2) (bậc 1)

### Nhận định
- **Nhận định:** Gộp lại, số lời gọi LLM có dạng O(số chữ ký phiên khác nhau + số ngày). Số chữ ký này tăng theo độ đa dạng hành vi, gần như bão hòa khi n lớn, giống số template trong log parsing. Token mỗi lời gọi bị chặn bởi trần mẫu cho mỗi cụm (vài phiên đại diện, vài field) và trần số khối mỗi ngày.
- **Nhận định:** Có hai rủi ro của mẫu cache theo chữ ký. Thứ nhất, chữ ký quá mịn (giữ nguyên PID, GUID, đường dẫn tạm) làm số chữ ký tăng theo n. Thứ hai, chữ ký quá thô làm gộp nhầm hoạt động khác nhau. LILAC gặp vấn đề tương tự và xử lý bằng bước "refine template" trong cache, có thể học theo.

### Khoảng trống
- Chưa có số đo về tỉ lệ cache hit hay số chữ ký phiên khác nhau trên telemetry endpoint thật.

## Truy vấn đã chạy
- LILAC LLM log parsing adaptive parsing cache (standard)
- LLM forensic timeline analysis summarization paper (standard)
- table serialization LLM benchmark markdown JSON CSV tokens accuracy (standard)
- Timesketch LLM features summarization event (standard), sau đó đọc trực tiếp source GitHub
- LogBatcher LLM log parsing demonstration-free batching (standard)
- LLM log summarization hierarchical chunking evaluation arXiv 2024 (standard)
- LLM human activity recognition smart home sensor events textual serialization zero-shot (standard)
- LLM agent SQL query security logs instead of raw events investigation (standard)
- LLM provenance graph natural language description system behavior summarization (standard)
- Elastic Attack Discovery how alerts are sent to LLM fields anonymization token limit (standard)
- LLMParser DivLog LogPrompt log parsing accuracy results comparison survey (standard)
- LLM generated incident summary evaluation analysts faithfulness security copilot study (standard)
- LLM summarize Windows event logs Sysmon user activity narrative (extended)
- LLM audit log provenance event abstraction token reduction compress logs before prompting (standard)
