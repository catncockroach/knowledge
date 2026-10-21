# Trích template, che tham số và chuẩn hóa cho văn bản do máy sinh (kèm chuẩn hóa tiếng Việt)

> **Lưu ý về cách kiểm chứng.** Trong phiên này proxy chặn arxiv.org, dl.acm.org, openrefine.org, unicode.org, *.github.io, wikipedia và docs.python.org. Chỉ mở trực tiếp được trang **github.com** (README, file docs trong repo). Vì vậy:
> - Phát hiện ghi "(đã mở)" là đã đọc trực tiếp trang đó bằng WebFetch.
> - Phát hiện ghi "(qua search)" lấy từ phần tóm tắt của `WebSearch` chế độ extended, vốn đọc trang gốc nhưng agent **không mở lại được** để đối chiếu nguyên văn. URL vẫn là nguồn gốc (bậc 1), nhưng writer/verifier nên coi con số loại này là *cần kiểm tra lại* trước khi đưa vào report như số chắc chắn.
> - Phát hiện ghi "(agent tự chạy)" là agent tự kiểm bằng Python 3 (`unicodedata`, Unicode 15.1.0) trong sandbox.

## 1. Che tham số (masking) và các thuật toán trích template log: Drain/Drain3, Spell, LogMine, IPLoM, LenMa, Brain; độ chính xác và tốc độ trên LogPAI/Loghub/Loghub-2.0

### Kết luận ngắn
Pipeline chuẩn là: regex che các tham số "có hình dạng" (IP, số, ID, hash…) trước, rồi để một parser heuristic (Drain là mặc định của ngành) gom các dòng còn lại theo vị trí token và độ giống. Drain nhanh (O(N), chạy streaming), đứng đầu benchmark năm 2019, nhưng khi đo trên Loghub-2.0 (lớn hơn, nhiều template hơn) thì FGA trung bình rơi từ khoảng 0,75 xuống khoảng 0,55. Mức chắc chắn **cao** cho cơ chế (đã mở README Drain3), **trung bình** cho các con số benchmark (lấy qua search, chưa mở được paper).

### Phát hiện có nguồn
**Drain / Drain3 (cơ chế, cấu hình):**
- Drain dùng "fixed depth parse tree" để dẫn đường tìm nhóm log, tránh cây sâu và lệch. Drain3 là bản nâng cấp sang Python 3.6+, chạy online (streaming), xử lý từng message một — [logpai/Drain3 README](https://github.com/logpai/Drain3) (bậc 1, không rõ ngày; changelog mới nhất v0.9.11) (đã mở).
- Tham số `[DRAIN]`: `sim_th` mặc định `0.4` (nếu tỉ lệ token giống nhau dưới ngưỡng thì tạo cụm mới); `depth` mặc định `4`, tối thiểu `3`; `max_children` mặc định `100`; `max_clusters` mặc định không giới hạn, khi đầy thì thay cụm ít dùng nhất (LRU); `extra_delimiters` (vd `['_', ':']`) — [Drain3 README](https://github.com/logpai/Drain3) (bậc 1) (đã mở).
- Masking `[MASKING]`: danh sách object `{regex_pattern, mask_with}`, áp dụng **trước** lõi Drain; phần biến không bị regex bắt thì để lõi Drain xử lý. Ví dụ trong README: che IPv4 bằng `IP`, che số nguyên bằng `NUM`. `mask_prefix`/`mask_suffix` mặc định `<` và `>` (template ra dạng `<IP>`, `<NUM>`) — [Drain3 README](https://github.com/logpai/Drain3) (bậc 1) (đã mở).
- Persistence `[SNAPSHOT]`: snapshot là JSON nén chứa cây tìm kiếm và các cụm (`cluster_id`, token template, `size`); chụp khi có cụm mới, khi template đổi, và theo chu kỳ `snapshot_interval_minutes` (mặc định 1). Backend: Kafka (`topic_name`, đọc message cuối khi khởi động lại), Redis, File, Memory, None; có thể tự viết bằng cách kế thừa `PersistenceHandler`. Có `compress_state` — [Drain3 README](https://github.com/logpai/Drain3) (bậc 1) (đã mở).
- Hai chế độ: `add_log_message()` (training: khớp hoặc tạo cụm mới) và `match()` (inference: chỉ khớp cụm đã học, không tạo cụm mới, trả `None` nếu không khớp chính xác). `extract_parameters(template, log_line, exact_matching=True)` trả danh sách biến theo thứ tự kèm tên mask — [Drain3 README](https://github.com/logpai/Drain3) (bậc 1) (đã mở). README **không** đưa con số throughput.
- Các bước của Drain gốc: tiền xử lý bằng regex theo tri thức miền → tầng 1 nhóm theo **số token** → các tầng tiếp theo rẽ nhánh theo **k token đầu** (mặc định khoảng 3) → ở lá, so độ giống token với từng nhóm theo ngưỡng `st` → nếu khớp thì cập nhật template bằng cách thay vị trí khác nhau bằng wildcard, nếu không thì tạo nhóm mới; độ phức tạp O(N) — [logparser docs: Drain](https://logparser.readthedocs.io/en/latest/tools/Drain.html), [Tipping, arXiv 2408.00645](https://arxiv.org/html/2408.00645v2) (bậc 1, 2024) (qua search).

**Các thuật toán khác (danh mục và cơ chế):**
- Bảng parser của LogPAI: SLCT (IPOM'03), AEL (QSIC'08), IPLoM (KDD'09), LKE (ICDM'09), LFA (MSR'10), LogSig (CIKM'11), SHISO (SCC'13), LogCluster (CNSM'15), LenMa (CNSM'15), LogMine (CIKM'16), Spell (ICDM'16), Drain (ICWS'17), MoLFI (ICPC'18), Logram (TSE'20), NuLog (ECML-PKDD'20), ULP (ICSME'22), Brain (TSC'23), DivLog (ICSE'24). Cài bằng `pip install logparser3`; benchmark trong repo chạy trên loghub_2k — [logpai/logparser README](https://github.com/logpai/logparser) (bậc 1) (đã mở).
- **Spell**: online, so dòng mới với template có sẵn bằng Longest Common Subsequence; nhược điểm là thời gian khớp LCS tăng khi lượng log lớn — [Survey on Online Log Parsers, IJEAT](https://www.ijeat.org/wp-content/uploads/papers/v10i5/E28160610521.pdf) (bậc 2), [Spell (ResearchGate)](https://www.researchgate.net/publication/328245654_Spell_Online_Streaming_Parsing_of_Large_Unstructured_System_Logs) (bậc 1) (qua search).
- **LogMine**: gom cụm theo độ giống từ chung (hierarchical clustering), rồi sinh template mỗi cụm; thiên về batch offline — [MDPI CFTL 2025](https://www.mdpi.com/2076-3417/15/4/1740) (bậc 2) (qua search).
- **IPLoM**: chia từ trên xuống: (1) theo số từ, (2) theo vị trí token có ít giá trị phân biệt nhất, (3) tìm ánh xạ song ánh giữa token rồi sinh template — [MDPI CFTL 2025](https://www.mdpi.com/2076-3417/15/4/1740) (bậc 2) (qua search).
- **LenMa**: dựa trên quan sát từ hằng của template có cùng độ dài ký tự ở mọi message, còn từ biến thì không; biến message thành vector độ dài từ, gom theo cosine giữa các message cùng số từ — [MDPI CFTL 2025](https://www.mdpi.com/2076-3417/15/4/1740) (bậc 2) (qua search).
- **Brain**: dựa trên quan sát từ của template lặp lại với tần suất cao nhất; tìm "longest common pattern" làm nhóm khởi tạo, rồi dùng cây song song hai chiều để bổ sung từ hằng; tác giả báo khoảng 46 giây cho 1 triệu dòng log — [gaiusyu/Brain](https://github.com/gaiusyu/Brain) (bậc 1), [SCOPE, arXiv 2603.27247](https://arxiv.org/pdf/2603.27247) (bậc 1, 2026) (qua search).
- **Xu hướng mới (2026)**: DeepParse dùng LLM để *sinh regex mask* rồi chạy parser heuristic — [DeepParse, arXiv 2604.20553](https://arxiv.org/pdf/2604.20553) (bậc 1, 2026) (chỉ thấy tiêu đề qua search, chưa đọc nội dung).

**Benchmark và metric:**
- Zhu et al., "Tools and Benchmarks for Automated Log Parsing" (ICSE-SEIP 2019): đánh giá 13 parser trên 16 dataset (hệ phân tán, siêu máy tính, OS, mobile, server, standalone); Drain có độ chính xác trung bình cao nhất và phương sai nhỏ nhất; nhiều parser đạt tối đa trên 0,9 nhưng dao động lớn giữa các dataset; tác giả khuyên thử nhiều parser trên log của chính mình — [arXiv 1811.03509](https://arxiv.org/pdf/1811.03509) (bậc 1, 2018-11/2019) (qua search).
- Loghub-2.0: 14 dataset, khoảng 50,4 triệu dòng có gán nhãn (trung bình 3.601.187 dòng/dataset), 3.488 template (trung bình 249,1); so với Loghub-2k: 1.147 template (trung bình 81,9). Benchmark đánh giá 16 parser, chia thành statistic-based và semantic-based (LogPPT, UniParser cần GPU). Chạy toàn bộ benchmark mất hơn 48 giờ — [logpai/loghub-2.0 README](https://github.com/logpai/loghub-2.0) (bậc 1, ISSTA 2024) (đã mở).
- Jiang et al., "A Large-scale Evaluation for Log Parsing Techniques: How Far are We?" (ISSTA 2024): mọi parser đều giảm mạnh ở metric cấp template trên Loghub-2.0 so với Loghub-2k; Drain (FGA cao nhất trên Loghub-2k) có FGA trung bình rơi từ 0,75 xuống khoảng 0,55; 9/15 parser không chạy xong cả 14 dataset trong 12 giờ, chỉ 6 parser (có Drain) chạy xong; parser thống kê (như Drain) gom nhóm tốt hơn, parser ngữ nghĩa (như LogPPT) nhận diện tham số tốt hơn — [arXiv 2308.10828](https://arxiv.org/html/2308.10828v2) (bậc 1, 2023-08/2024) (qua search).
- Định nghĩa metric (tóm tắt theo hiểu biết chung về bộ benchmark, **chưa mở được trang định nghĩa nguyên văn**): GA = tỉ lệ message được xếp đúng nhóm; PA = tỉ lệ message có template đúng hoàn toàn; FGA = F1 cấp nhóm (tính theo template, không theo message, nên không bị template phổ biến "che"); FTA = F1 cấp template, yêu cầu vừa đúng nhóm vừa đúng chữ template. Xem Khoảng trống.

### Nhận định
- **Nhận định:** Với cột văn bản ngắn do máy sinh, phần lớn giá trị đến từ **regex masking**; Drain chỉ cần gom phần còn lại. Danh sách mask nên có: email, URL, IPv4/IPv6, MAC, UUID, hash hex (32/40/64 ký tự), số (kèm số thập phân, %), ngày/giờ (ISO, dd/mm/yyyy), đường dẫn file, mã dạng `chữ+số` (vd `user123`, `ORD-2024-001`). Thứ tự quan trọng: mask cụ thể (email, URL, UUID, IP) chạy trước mask chung (số).
- **Nhận định:** Con số Loghub-2.0 cho thấy chỉ số "accuracy" trên tập nhỏ (2k dòng/dataset) quá lạc quan; khi số template tăng, chất lượng gom giảm. Với dữ liệu thực, cần đo trên mẫu gán nhãn của chính mình, không dựa vào số benchmark.
- **Nhận định:** Drain3 có sẵn những gì pipeline thống kê tần suất cần: `size` mỗi cụm (chính là tần suất template), snapshot để chạy định kỳ/streaming, `match()` để gán bản ghi mới vào template cũ mà không tạo cụm mới.

### Khoảng trống
- Chưa mở được bảng số GA/FGA/PA/FTA từng parser trong paper ISSTA 2024 và Table IV của paper ICSE 2019 (arxiv bị chặn; thư mục `RQ_experiments` trên GitHub trả 404). Truy vấn đã thử: xem mục Truy vấn.
- Chưa có định nghĩa metric nguyên văn từ nguồn bậc 1.
- Chưa có số throughput (dòng/giây) của Drain3 từ nguồn chính thức; chỉ có "46 giây / 1 triệu dòng" của Brain (tác giả tự báo) và "demo Drain trên Loghub-2k và 2.0 mất khoảng 2–3 giờ" (README loghub-2.0, gồm cả đánh giá).

## 2. LLM-based log parsing có cache để giảm số lần gọi LLM: LILAC, LogBatcher, LLMParser, DivLog, LogPrompt, LUNAR, AdaParser…

### Kết luận ngắn
Ý tưởng chung: số template nhỏ hơn số dòng nhiều bậc độ lớn (Loghub-2.0: hơn 50 triệu dòng, dưới 3.500 template), nên chỉ gọi LLM cho dòng **chưa khớp template nào trong cache** (LILAC) hoặc một lần cho mỗi cụm/batch dòng giống nhau (LogBatcher, LUNAR). Cách gọi LLM cho từng dòng (DivLog, LogPrompt) chính xác nhưng đắt. Mức chắc chắn **trung bình**: cơ chế rõ, nhưng phần lớn số liệu lấy qua search và do tác giả tự báo, setup khác nhau nên không so trực tiếp được.

### Phát hiện có nguồn
- **LILAC** (FSE 2024): hai thành phần là ICL-enhanced parser và adaptive parsing cache; tự nhận là "the first practical LLM-based log parsing framework"; code dùng OpenAI API (`--model`) — [logpai/LILAC README](https://github.com/logpai/LILAC) (bậc 1) (đã mở). Cache lưu template đã sinh và tinh chỉnh dần để vừa hiệu quả vừa nhất quán; tác giả lập luận số template nhỏ hơn số message vài bậc (Loghub-2.0 hơn 50 triệu message, dưới 3.500 template); báo cáo cải thiện 69,5% F1 trung bình của template accuracy so với SOTA, giảm số lần hỏi LLM "by several orders of magnitude", hiệu năng tương đương baseline nhanh nhất (Drain) — [arXiv 2310.01796](https://arxiv.org/abs/2310.01796) (bậc 1, 2023-10/2024) (qua search).
- **LogBatcher** (ASE 2024, "Demonstration-Free: Towards More Practical Log Parsing with Large Language Models", Xiao, Le, Zhang): ba bước Partitioning (clustering: dbscan mặc định, meanshift, hierarchical) → Caching → Batching-Querying (chọn mẫu bằng dpp mặc định / similar / random); batch size mặc định 10, chunk size 2000; không cần training hay dữ liệu gán nhãn; model mặc định `gpt-3.5-turbo-0125`, khuyên `gpt-4o-mini`, hỗ trợ model mở như Llama 3.1. Demo trên Apache 2k: khoảng 4,76 giây cho 2.000 dòng, 6 template, GA/PA/FGA/FTA = 1,0 (chỉ là sanity check) — [LogIntelligence/LogBatcher README](https://github.com/LogIntelligence/LogBatcher) (bậc 1) (đã mở).
- LogBatcher (bản arXiv): đánh giá 16 dataset, GA 0,972 và message-level accuracy 0,895; ví dụ phần instruction của prompt đã tốn 66 token, nhiều hơn chính dòng log (55 token), nên gộp nhiều dòng vào một prompt giảm chi phí; câu "reduce LLM invocation cost by at least 106%" trong tóm tắt search là phát biểu bất thường (không thể giảm quá 100%), cần đối chiếu paper — [arXiv 2406.06156](https://arxiv.org/pdf/2406.06156) (bậc 1, 2024-06) (qua search).
- **DivLog** (ICSE 2024): ICL, chọn mẫu đa dạng; PA 98,1%, PTA 92,1%, RTA 92,9% trung bình trên 16 dataset (Loghub-2k); vượt Drain về PA/PTA/RTA lần lượt 48,3%/50,2%/42,6% (tác giả tự báo); nhược điểm: **gọi LLM một lần cho mỗi dòng**, nên tổng số lần gọi rất cao dù token/lần thấp hơn LILAC — [arXiv 2307.09950](https://arxiv.org/html/2307.09950) (bậc 1, 2023-07/2024), [LogBatcher arXiv 2406.06156](https://arxiv.org/pdf/2406.06156) (bậc 1) (qua search).
- **LLMParser** (ICSE 2024, Ma et al., fine-tune model nhỏ): PA trung bình 0,96, cao hơn Drain, Logram, LogPPT; T5 parse 100 dòng trong khoảng 1,27 s và 4 s (hai biến thể), ChatGLM khoảng 19,87 s, LLaMA khoảng 28,93 s — [arXiv 2404.18001](https://arxiv.org/html/2404.18001v1), [zeyang919/LLMParser](https://github.com/zeyang919/LLMParser) (bậc 1, 2024) (qua search).
- **LUNAR** (FSE 2025, không cần nhãn): hierarchical sharder chia log thành bucket theo độ dài và top-k token phổ biến, chọn "LCU" (nhóm log chỉ khác ở phần biến), hỏi LLM một lần cho mỗi nhóm, các bucket chạy song song; tốc độ tương đương phần lớn parser cú pháp — [arXiv 2406.07174](https://arxiv.org/html/2406.07174v2) (bậc 1, 2024-06/2025) (qua search).
- So sánh thời gian độc lập (paper LibreLog/OpenLogParser, model mở): parse toàn bộ 14 hệ của Loghub-2.0 (50 triệu dòng) mất LibreLog 5,94 giờ, LUNAR 10,6 giờ, LILAC 16 giờ, LLMParser (T5Base) 258 giờ — [LibreLog, arXiv 2408.01585](https://arxiv.org/pdf/2408.01585) (bậc 1, 2024-08) (qua search). Lưu ý: LibreLog là tác giả của một đối thủ.
- So sánh độc lập về chất lượng template trên Loghub-2.0 (paper Matryoshka, cùng setup): LILAC PGS 0,90 / TS 0,82, Drain3 0,89 / 0,81; một phiên bản khác của paper ghi LILAC 0,95 / 0,87 → số lệch giữa các phiên bản — [Matryoshka, arXiv 2506.17512](https://arxiv.org/html/2506.17512v2) (bậc 1, 2025) (qua search).
- **LogPrompt** (poster ICSE 2024, full paper ICPC 2024): zero-shot, thử các chiến lược prompt (self-prompt, CoT, in-context); báo tăng tới 380,7% so với prompt đơn giản, vượt phương pháp có huấn luyện tới 55,9%, đánh giá trên 9 dataset cho log parsing và anomaly detection; 6 chuyên gia chấm tính giải thích được 4,42/5 — [arXiv 2308.07610](https://arxiv.org/pdf/2308.07610) (bậc 1, 2023-08/2024) (qua search). Không tìm thấy số lần gọi LLM.
- **AdaParser** (Wu, Yu, Li; 2024): self-generated in-context learning (dùng chính template đã sinh trước đó làm mẫu) + template corrector (LLM tự sửa template vi phạm quy tắc, lặp tới giới hạn); tác giả báo vượt SOTA ở mọi metric kể cả zero-shot, nhưng một survey ghi kết quả zero-shot "significantly inferior" so với few-shot — [IEEE Xplore 11025900](https://ieeexplore.ieee.org/document/11025900/) (bậc 1), [survey arXiv 2509.10858](https://arxiv.org/pdf/2509.10858) (bậc 2) (qua search).
- Chi phí minh họa (paper LogRules, NAACL Findings 2025): một query GPT-3.5-turbo-0613 sinh 200 token tốn khoảng $0,000775/dòng; model khoảng 8B tốn khoảng $0,00009/dòng (giảm khoảng 88,4%), theo giả định giá/token của paper đó — [LogRules, ACL Anthology 2025.findings-naacl.28](https://aclanthology.org/2025.findings-naacl.28.pdf) (bậc 1, 2025) (qua search).
- Tổng quan: [System Log Parsing with LLMs: A Review, arXiv 2504.04877](https://arxiv.org/pdf/2504.04877) (bậc 2, 2025) và [MicLog, arXiv 2601.07005](https://arxiv.org/pdf/2601.07005) (MicLog tự báo PA cao hơn 10,3% và giảm 42,4% thời gian parse so với SOTA) (bậc 1, 2026) (qua search).

### Nhận định
- **Nhận định:** Số lần gọi LLM của kiểu "cache theo template" xấp xỉ **số template khác nhau** (cộng một ít lần sửa cache), không phụ thuộc số dòng N. Với Loghub-2.0, cận trên lý thuyết là khoảng 3.500 lần cho 50 triệu dòng (khoảng 0,007%). Đây là suy luận từ thiết kế, chưa phải số đo được báo cáo.
- **Nhận định:** Với bài toán của brief, LLM chỉ đáng dùng cho phần máy sinh khi regex + Drain gom sai nhiều (template có từ biến không theo hình dạng, ví dụ tên người, tên sản phẩm). Đi theo hướng "Drain/regex trước, LLM chỉ cho cụm nhỏ hoặc dòng không khớp" là hợp lý, tương tự LILAC/LUNAR.
- **Nhận định:** Các repo LILAC, LogBatcher mặc định dùng API OpenAI, nhưng LogBatcher, LibreLog, LLMParser chạy được với model mở (Llama 3.1, T5), tức triển khai on-prem được.

### Khoảng trống
- Không lấy được số "LLM calls per N lines" cụ thể của LILAC (bảng RQ4 nằm trong paper, arxiv bị chặn). Không có số lần gọi của LogPrompt, AdaParser.
- Con số "at least 106%" của LogBatcher cần kiểm tra lại trong paper.
- Mọi benchmark đều là log hệ thống tiếng Anh; không có số nào cho văn bản tiếng Việt.

## 3. Phân biệt giá trị "máy sinh theo template" với "người viết"

### Kết luận ngắn
Không tìm thấy tài liệu chuyên về tách dòng "template máy sinh" với "văn bản tự do người nhập" trong cùng một cột; tài liệu "machine-generated text detection" hiện nay gần như chỉ nói về văn bản do LLM viết, không áp dụng được. Có thể dựng heuristic từ chính đầu ra của template miner (kích thước cụm, khớp chính xác, tỉ lệ token là mask). Mức chắc chắn **thấp** về mặt có tài liệu; **trung bình** về tính hợp lý của heuristic.

### Phát hiện có nguồn
- Search "template-generated vs human-written" chỉ trả về tài liệu phát hiện văn bản do AI viết; một paper cũ ghi nhận cách lọc message tự động truyền thống dựa vào thành phần từ khóa hơn là cấu trúc — [Algorithmic Detection of Computer Generated Text, arXiv 1008.0706](https://arxiv.org/pdf/1008.0706) (bậc 1, 2010) (qua search).
- Một nghiên cứu so sánh ngôn ngữ người và AI thấy văn bản người viết có độ biến thiên độ dài lớn hơn — [A linguistic comparison between human- and AI-generated content, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12969083/) (bậc 1, 2025/2026) (qua search). Ngưỡng entropy "< 4" chỉ thấy trên blog vendor, không dùng làm bằng chứng (bậc 3).
- Công cụ có sẵn hỗ trợ heuristic: Drain3 `match()` chỉ trả cụm khi khớp chính xác template đã học, ngược lại trả `None`; mỗi cụm có `size` — [Drain3 README](https://github.com/logpai/Drain3) (bậc 1) (đã mở).
- Paper ICSE 2019 khuyên thử parser trên log của chính mình vì không parser nào tốt cho mọi dữ liệu — [arXiv 1811.03509](https://arxiv.org/pdf/1811.03509) (bậc 1) (qua search).

### Nhận định
- **Nhận định:** Bộ heuristic đề xuất (cần hiệu chỉnh trên mẫu gán nhãn tay vài trăm dòng):
  1. **Support của template**: sau mask + Drain, dòng thuộc cụm có `size` ≥ k (vd ≥ 20 hoặc ≥ 0,1% số dòng) và template có ít nhất một tham số → nghiêng về máy sinh. Cụm cỡ 1–2 → nghiêng về người viết.
  2. **Khớp tiền tố chính xác**: phần token hằng ở đầu (vd "đã khóa tài khoản", "Blocked IP") trùng với template có support cao → máy sinh.
  3. **Tỉ lệ token bị mask** cao (nhiều `<NUM>`, `<IP>`, `<ID>`) và độ dài ổn định trong cụm → máy sinh; câu có dấu câu tự do, viết tắt, emoji, độ dài dao động → người viết.
  4. **Entropy token trong cụm**: vị trí hằng có entropy ≈ 0, vị trí tham số có entropy cao; cụm người viết thì entropy cao rải rác mọi vị trí.
  5. **Edit distance tới template gần nhất** (sau khi mask): nhỏ → máy sinh nhưng có biến thể (version template khác); lớn → người viết.
  6. **Theo cột phân loại khác** (nguồn/loại bản ghi): nhiều hệ thống chỉ ghi máy sinh từ một số nguồn nhất định; tách theo nguồn trước khi gom là tín hiệu rẻ nhất.
- **Nhận định:** Không cần phân loại hoàn hảo: dòng bị nghi ngờ có thể đưa sang nhánh "người viết" (gom theo nghĩa bằng embedding), vì nhánh đó vẫn gom được dòng máy sinh, chỉ tốn hơn.

### Khoảng trống
- Không tìm thấy paper/benchmark nào đo độ chính xác của việc tách template vs free text trong cùng cột. Truy vấn đã thử: "distinguish template-generated vs human-written text messages free-text field log lines…".
- Paper "Investigating and Improving Log Parsing in Practice" (FSE 2022) và "Interactive Log Parsing via Light-weight User Feedback" (arXiv 2301.12225) xuất hiện trong kết quả search, có thể liên quan đến xử lý log lẫn ngôn ngữ tự nhiên, nhưng chưa đọc.

## 4. Giới hạn khi áp dụng cho văn bản ngắn tiếng Việt người viết; chuẩn hóa tiếng Việt cơ bản

### Kết luận ngắn
Các parser log giả định token ở vị trí cố định và cùng số token (Drain nhóm theo độ dài và k token đầu; IPLoM theo số từ và vị trí; LenMa theo độ dài từ), nên với câu người viết (đảo trật tự, thêm/bớt từ, thiếu dấu, sai chính tả) chúng sẽ tách thành rất nhiều cụm cỡ 1. Trước mọi bước đếm cần chuẩn hóa: Unicode NFC, thống nhất vị trí dấu thanh (NFC **không** làm việc này), lowercase, và một khóa không dấu để so khớp. Tách từ không bắt buộc cho đếm/khớp khóa và embedding hiện đại. Mức chắc chắn **cao** cho Unicode (agent tự kiểm), **trung bình** cho tách từ.

### Phát hiện có nguồn
**Giới hạn của parser log:**
- Drain nhóm tầng 1 theo **số token**, rồi theo **các token đầu**, rồi so token **cùng vị trí** — [logparser docs: Drain](https://logparser.readthedocs.io/en/latest/tools/Drain.html), [Tipping arXiv 2408.00645](https://arxiv.org/html/2408.00645v2) (bậc 1) (qua search). IPLoM chia theo số từ rồi theo vị trí token; LenMa chỉ so các message cùng số từ — [MDPI CFTL 2025](https://www.mdpi.com/2076-3417/15/4/1740) (bậc 2) (qua search).
- Parser thống kê kém về "ngữ nghĩa", parser ngữ nghĩa kém về gom nhóm ở quy mô lớn — [arXiv 2308.10828](https://arxiv.org/html/2308.10828v2) (bậc 1) (qua search).

**Unicode NFC/NFD và vị trí dấu thanh (agent tự chạy, Python 3, Unicode 15.1.0):**
- "hòa" (dấu trên o) NFC = `h ò a` (U+00F2), NFD = `h o U+0300 a`; "hoà" (dấu trên a) NFC = `h o à` (U+00E0), NFD = `h o a U+0300`. `NFC("hòa") == NFC("hoà")` là **False**: chuẩn hóa Unicode không thống nhất kiểu bỏ dấu cũ/mới — (agent tự chạy).
- "Việt" NFC dài 4 code point (ệ = U+1EC7), NFD dài 6 (e + U+0323 dấu nặng + U+0302 mũ): cùng chữ nhìn giống hệt nhưng so chuỗi/đếm tần suất sẽ khác nếu không chuẩn hóa — (agent tự chạy).
- "Đ/đ" (U+0110/U+0111) **không** tách được bằng NFD; bỏ dấu bằng cách xóa ký tự loại `Mn` sau NFD sẽ giữ nguyên "đ", phải map tay `đ→d`. Sau khi map, "Đã khóa tài khoản" → "Da khoa tai khoan" và khóa không dấu của "hoà" bằng "hòa" — (agent tự chạy).
- Kiểu bỏ dấu cũ đặt dấu gần giữa từ (vd *hóa*), kiểu mới đặt trên nguyên âm chính (*hoá*); cả hai đều được chấp nhận trong thực tế với cụm "oa" — [I Can Read Vietnamese: Rules of tone mark placement](https://icanreadvietnamese.com/blog/14-rule-of-tone-mark-placement) (bậc 3), [primidi: Vietnamese alphabet – tone marks](https://www.primidi.com/vietnamese_alphabet/tone_marks) (bậc 3) (qua search). Tài liệu Unicode Core Spec chương 16 có trong kết quả search nhưng không mở được — [Unicode 17.0 chapter 16](https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-16/) (bậc 1).
- Một vowel mang cả dấu phụ (mũ, móc) và dấu thanh có thể mã hóa dạng dựng sẵn, dạng gốc + dấu phụ kết hợp + dấu thanh, hoặc phân rã hoàn toàn; khi sort nên bỏ qua dấu thanh nhưng không bỏ dấu phụ — [Unicode mailing list 2002](https://www.unicode.org/mail-arch/unicode-ml/y2002-m01/0600.html) (bậc 2, 2002, chỉ là bối cảnh) (qua search).

**Công cụ tiếng Việt:**
- underthesea (Apache-2.0) có `text_normalize`, `word_tokenize`, `restore_diacritics`, `sent_tokenize`, `lang_detect`, `classify`… Ví dụ chính thức: `text_normalize("Ðảm baỏ chất lựơng phòng thí nghịêm hoá học")` → `"Đảm bảo chất lượng phòng thí nghiệm hóa học"` (sửa chữ "Ð" nhầm ký tự, sửa vị trí dấu sai, và đổi "hoá" thành "hóa", tức chuẩn về **kiểu cũ**); `word_tokenize(..., format="text")` → `"Chàng_trai 9X Quảng_Trị khởi_nghiệp từ nấm sò"`; `restore_diacritics("chung ta co the lam duoc")` → `"chúng ta có thể làm được"` — [underthesea README](https://github.com/undertheseanlp/underthesea), [underthesea NLP.md](https://github.com/undertheseanlp/underthesea/blob/main/NLP.md) (bậc 1, không rõ ngày; README nói từ v9.3.0 là "Agentic AI Toolkit") (đã mở).
- RDRSegmenter (lõi tách từ của VnCoreNLP): F1 97,90 trên tập test chuẩn, khoảng 62k từ/giây một luồng (Intel i7), load model 50 ms — [A Fast and Accurate Vietnamese Word Segmenter, arXiv 1709.06307](https://arxiv.org/pdf/1709.06307) (bậc 1, 2017/LREC 2018) (qua search).
- Benchmark bên thứ ba trên VLSP2013 (2026): F1 underthesea 97,5, VnCoreNLP 97,8, RDRSegmenter 97,9; tốc độ 2.800 / 5.000 / 4.700 câu/giây — [FreeTxt-Vi, arXiv 2603.05690](https://arxiv.org/html/2603.05690v1) (bậc 1, 2026-03) (qua search). Một blog benchmark không rõ setup cho pyvi nhanh nhất nhưng chính xác thấp (khoảng 57,8%) — [huybik Word-Tokenizer-Benchmark](https://huybik.github.io/Word-Tokenizer-Benchmark/) (bậc 3, chỉ tham khảo).
- Tách từ có cần không: với classifier truyền thống (Naive Bayes, SVM) trên corpus mạng xã hội, tách từ "maybe not be necessary"; tách từ cần khi dùng trước BPE rồi đưa vào model deep learning (thí nghiệm so 5 model S4, một không tách từ, bốn dùng RDRsegmenter/uitnlp/pyvi/underthesea) — [Is word segmentation necessary for Vietnamese sentiment classification?, arXiv 2301.00418](https://arxiv.org/pdf/2301.00418) (bậc 1, 2023-01) (qua search). Một paper AAAI 2025 lập luận tách từ không phù hợp cho hiểu văn bản tiếng Việt — [AAAI 2025, ojs.aaai.org 34581](https://ojs.aaai.org/index.php/AAAI/article/view/34581) (bậc 1, 2025) (qua search, chưa đọc chi tiết).
- Chuẩn hóa từ vựng văn bản mạng xã hội (teencode, viết tắt, sai chính tả): corpus ViLexNorm (EACL 2024) hơn 10.000 cặp câu; hệ tốt nhất đạt ERR 57,74%; một bản tóm tắt thứ cấp nói "không" có 53 biến thể — [ViLexNorm, arXiv 2401.16403](https://arxiv.org/html/2401.16403v2), [ACL Anthology 2024.eacl-long.85](https://preview.aclanthology.org/setup/2024.eacl-long.85) (bậc 1, 2024) (qua search; con số 53 biến thể từ review AI, bậc 3).

### Nhận định
- **Nhận định:** Thứ tự chuẩn hóa đề xuất cho mỗi giá trị: (1) `unicodedata.normalize("NFC")`; (2) sửa ký tự nhầm (Ð U+00D0 → Đ U+0110) và thống nhất vị trí dấu thanh về một kiểu (dùng `underthesea.text_normalize`, nó chuẩn về kiểu cũ "hóa"); (3) lowercase (`casefold`); (4) gộp khoảng trắng, bỏ dấu câu thừa; (5) mask tham số; (6) tạo thêm **khóa không dấu** (NFD → bỏ `Mn` → `đ→d`) dùng để so khớp/gom, nhưng giữ bản có dấu để hiển thị. Khóa không dấu có rủi ro gộp nhầm (vd "khóa" và "khoa"), nên chỉ dùng làm khóa ứng viên, không dùng làm nhãn cuối.
- **Nhận định:** Với bước đếm khóa/fingerprint và embedding đa ngữ hiện đại (subword), tách từ không bắt buộc; nó hữu ích khi dùng TF-IDF theo từ hoặc từ điển đồng nghĩa nhiều âm tiết ("tài khoản", "khách hàng"). Char n-gram TF-IDF là cách né tách từ.
- **Nhận định:** Có thể dùng Drain cho phần người viết chỉ như bước "dedup sau chuẩn hóa"; gom theo nghĩa phải dùng phương pháp khác (thuộc câu hỏi phụ của researcher khác).

### Khoảng trống
- Không mở được tài liệu Unicode chính thức (UAX #15) và trang docs Python; phần NFC/NFD dựa trên kiểm thử của agent.
- Không có nguồn bậc 1 về quy định chính thức kiểu bỏ dấu (cũ/mới) ở Việt Nam hiện hành.
- Không có benchmark về hiệu quả `text_normalize` của underthesea hay độ chính xác `restore_diacritics`.
- Chưa có nguồn đo trực tiếp ảnh hưởng của văn bản thiếu dấu/sai chính tả lên Drain.

## 5. Baseline đơn giản mà mạnh: chuẩn hóa + mask + đếm chính xác; fingerprint/key collision và các phương pháp clustering của OpenRefine

### Kết luận ngắn
OpenRefine tài liệu hóa hai họ: **key collision** (fingerprint, n-gram fingerprint, phonetic) và **nearest neighbor** (Levenshtein, PPM, có blocking). Fingerprint là mặc định vì ít false positive nhất; nên đi từ phương pháp chặt đến lỏng. Đây là baseline rẻ cho bước "chuẩn hóa + gộp biến thể chính tả" trước khi gom theo nghĩa. Mức chắc chắn **cao** (đã mở file docs nguồn trên GitHub).

### Phát hiện có nguồn
- **Fingerprint** (thứ tự các bước quan trọng): bỏ khoảng trắng đầu/cuối → lowercase → bỏ dấu câu và ký tự điều khiển → "normalize extended western characters to their ASCII representation (for example "gödel" → "godel")" → tách token theo khoảng trắng → **sort token và bỏ trùng** → nối lại. "The fingerprinting method is the least likely to produce false positives, which is why it is the default method." Bước ASCII hóa "can also lead to false positives" — [OpenRefine docs: Clustering methods in-depth (nguồn trên GitHub)](https://github.com/OpenRefine/openrefine.org/blob/master/docs/technical-reference/clustering-in-depth.md) (bậc 1, không rõ ngày) (đã mở); bản web: https://openrefine.org/docs/technical-reference/clustering-in-depth.
- **N-gram fingerprint**: lowercase → bỏ dấu câu, **khoảng trắng** và ký tự điều khiển → lấy mọi n-gram ký tự → sort, bỏ trùng → nối → ASCII hóa — [OpenRefine docs](https://github.com/OpenRefine/openrefine.org/blob/master/docs/technical-reference/clustering-in-depth.md) (bậc 1) (đã mở). Theo search, docs nói n lớn không có lợi hơn n nhỏ (qua search, câu bị cắt).
- **Phonetic**: Metaphone3 (mọi nguyên âm mã thành 'A', cặp phụ âm hữu thanh/vô thanh cùng mã, "TH" → '0'), Cologne (cho tiếng Đức), Daitch-Mokotoff, Beider-Morse (cho tên người, đoán ngôn ngữ từ chính tả) — [OpenRefine docs](https://github.com/OpenRefine/openrefine.org/blob/master/docs/technical-reference/clustering-in-depth.md) (bậc 1) (đã mở). Tất cả thiết kế cho tiếng Anh/Đức/tên người châu Âu.
- **Nearest neighbor**: Levenshtein ("minimal number of edit operations") và PPM (khoảng cách dựa trên nén); PPM "is very lax even for small radius values and tends to generate many false positives", dùng như "last resort". Tham số **radius** (cặp chuỗi gần hơn ngưỡng thì gộp) và **blocking** (mặc định 6 ký tự; "anything lower than 3 normally turns out to be a waste of time") để tránh so mọi cặp O(n²). Docs: "it's usually best to use heavy algorithms for shorter strings that can provide better quality" — [OpenRefine docs](https://github.com/OpenRefine/openrefine.org/blob/master/docs/technical-reference/clustering-in-depth.md) (bậc 1) (đã mở).
- Thứ tự khuyến nghị: từ phương pháp bảo thủ nhất đến lỏng nhất (fingerprint → n-gram → phonetic → nearest neighbor) — [OpenRefine docs](https://openrefine.org/docs/technical-reference/clustering-in-depth) (bậc 1) (qua search), [padjo.org tutorial](http://www.padjo.org/tutorials/open-refine/clustering/) (bậc 2) (qua search).
- Case study so khớp tên người: Metaphone3 tạo 66 cụm với precision 0,65, fingerprint 60 cụm precision 1,0 — [String matching algorithms in OpenRefine clustering…, ResearchGate](https://www.researchgate.net/publication/356666333_String_matching_algorithms_in_OpenRefine_clustering_and_reconciliation_functions_-_a_case_study_of_person_name_matching) (bậc 1/2, 2021) (qua search).
- Có port R: package `refinr` (key collision và ngram + nearest neighbor) — [refinr trên CRAN](https://cran.r-project.org/package=refinr) (bậc 1) (qua search).

### Nhận định
- **Nhận định:** Với tiếng Việt, bước "ASCII hóa" của fingerprint chính là tạo khóa không dấu: gộp được "hoà/hòa/hoa" (tốt cho lỗi thiếu dấu) nhưng cũng gộp nhầm các từ khác nghĩa chỉ khác dấu ("khóa"/"khoa", "chặn"/"chán"). Nên chạy fingerprint **có dấu** trước, rồi mới đến bản không dấu và xem xét cụm bị gộp.
- **Nhận định:** Fingerprint sort token nên miễn nhiễm với đảo trật tự từ ("khóa tài khoản" = "tài khoản khóa"), một phần bù cho giới hạn "vị trí token cố định" của Drain. Nhưng nó không xử lý được thêm/bớt từ (vd "đã", "bị") — cần stopword list tiếng Việt, hoặc chuyển sang n-gram/Levenshtein/embedding.
- **Nhận định:** Phonetic của OpenRefine không có ý nghĩa cho tiếng Việt; bỏ qua.
- **Nhận định:** Baseline đầy đủ, chạy on-prem, rất rẻ: NFC + sửa dấu + lowercase → mask regex → Drain3 cho phần máy sinh → fingerprint (có dấu, rồi không dấu) cho phần còn lại → đếm `value_counts`. Đo tỉ lệ dòng nằm trong top-K khóa; nếu đuôi dài (phần lớn khóa có tần suất 1) thì mới chuyển sang gom theo nghĩa.

### Khoảng trống
- OpenRefine không có số đo hiệu năng/độ chính xác chính thức cho từng phương pháp; chỉ có case study bên ngoài về tên người tiếng Anh.
- Không tìm thấy đánh giá fingerprint/key collision trên văn bản tiếng Việt.

## Truy vấn đã chạy
- WebFetch (đã mở): github.com/logpai/Drain3, github.com/logpai/loghub-2.0, github.com/logpai/LILAC, github.com/LogIntelligence/LogBatcher, github.com/logpai/logparser, github.com/OpenRefine/openrefine.org/…/clustering-in-depth.md, github.com/undertheseanlp/underthesea, …/underthesea/blob/main/NLP.md
- WebFetch thất bại (bị chặn hoặc 404): arxiv.org/abs/2308.10828, openrefine.org/docs/…, zbchern.github.io/papers/issta24.pdf, LogBatcher docs/experimental_results.md (404), loghub-2.0/RQ_experiments (404)
- LILAC adaptive parsing cache LLM queries Loghub-2.0 FGA abstract (standard)
- "How Far are We" log parsing Loghub-2.0 Drain FGA FTA results parsers performance drop (extended)
- LogBatcher demonstration-free log parsing LLM cost tokens invocations ASE 2024 (extended)
- "Tools and Benchmarks for Automated Log Parsing" Drain parsing accuracy 16 datasets 13 parsers (standard)
- LILAC log parsing number of LLM queries per dataset parsing time compared Drain Loghub-2.0 results table (extended)
- LUNAR unsupervised LLM-based log parsing parallel LLM calls efficiency (extended)
- AdaParser self-generated in-context learning self-correction log parsing template corrector (extended)
- OpenRefine clustering in depth fingerprint keying function steps ngram-fingerprint metaphone3 levenshtein PPM blocking (extended)
- Vietnamese tone mark placement old style new style "hoà" "hòa" Unicode NFC NFD normalization text processing (extended)
- underthesea text_normalize word_tokenize pyvi VnCoreNLP RDRSegmenter word segmentation accuracy speed (extended)
- distinguish template-generated vs human-written text messages free-text field log lines natural language classification heuristic (extended)
- DivLog LLMParser LogPrompt log parsing comparison number of LLM calls cost per log accuracy Drain survey (extended)
- Drain fixed depth parse tree algorithm steps preprocessing domain knowledge regex token length similarity threshold Spell longest common subsequence (standard)
- Spell LCS streaming log parsing; LogMine hierarchical clustering; IPLoM iterative partitioning; LenMa word length vector; Brain bidirectional parallel tree how they work (extended)
- "Is word segmentation necessary" Vietnamese sentiment classification 2301.00418 results conclusion (standard)
- LILAC FGA FTA average Loghub-2.0 0.9 Drain 0.55 LLM query times orders of magnitude (extended)
- Brain log parsing bidirectional parallel tree longest common pattern initial group frequency how it works (standard)
- LogPrompt zero-shot interpretable log analysis prompt strategies log parsing results ICSE 2024 (standard)
- Vietnamese user-generated text normalization teencode missing diacritics typos social media lexical normalization dataset ViLexNorm (standard)
