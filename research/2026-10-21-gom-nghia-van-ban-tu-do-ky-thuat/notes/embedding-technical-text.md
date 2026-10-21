# Embedding và gom cụm cho văn bản tự do dài vài câu, có token kỹ thuật

Phạm vi đã điều chỉnh theo coordinator: mỗi lần phân tích chỉ **vài trăm** bản ghi (tối đa vài nghìn khi cộng dồn), nên phần runtime quy mô lớn được bỏ. Thay vào đó là hành vi gom cụm khi n = 200–500 và vai trò của embedding như công cụ kiểm tra bên cạnh LLM coding. Những gì report trước đã có (bảng VN-MTEB, bảng thuật toán, outlier của BERTopic, `community_detection`) chỉ được dẫn lại, không lặp lại: xem `research/2026-10-21-thong-ke-tan-suat-van-ban-tu-do/report.md`, mục "Dòng người viết cần embedding đa ngữ".

Ghi chú truy cập: proxy chặn arxiv.org, aclanthology.org, huggingface.co, ar5iv, semanticscholar, alphaxiv. Chỉ GitHub/raw.githubusercontent.com mở được. Mọi số từ paper ghi "(qua search)" là đọc từ trích đoạn search, chưa mở bản gốc.

## 1. Giới hạn độ dài và đoạn văn nhiều ý

### Kết luận ngắn
Độ dài 4–5 câu không chạm giới hạn của model nào trong danh sách (thấp nhất là 512 token). Vấn đề thật là **một vector cho cả đoạn nhiều ý**: một đoạn nhắc cả triệu chứng, cách xử lý lẫn nguyên nhân sẽ bị kéo về "chủ đề chung" thay vì nguyên nhân. Có tài liệu khuyên tách câu, nhưng chưa có so sánh định lượng nào cho đúng bài toán này. Mức chắc chắn: cao cho phần giới hạn độ dài, thấp–trung bình cho phần "tách câu tốt hơn", vì bằng chứng gián tiếp và có kết quả ngược chiều.

### Phát hiện có nguồn
- Qwen3-Embedding 0.6B/4B/8B: sequence length **32K**, số chiều 1024 / 2560 / 4096, có MRL và "Instruction Aware". Code mẫu đặt `max_length = 8192` — [Qwen3-Embedding README](https://github.com/QwenLM/Qwen3-Embedding) (bậc 1, 2025-06, đã mở).
- bge-m3: max_length 8192 (đã có ở report trước, [37] — [BGE-M3 README](https://raw.githubusercontent.com/FlagOpen/FlagEmbedding/master/research/BGE_M3/README.md)) (bậc 1).
- gte-multilingual-base (mGTE): encoder cỡ base, RoPE, "pre-trained in a native 8192-token context", khoảng 305M tham số, 768 chiều, có sparse vector — [mGTE, EMNLP 2024 Industry, arXiv 2407.19669](https://arxiv.org/pdf/2407.19669) (bậc 1, 2024, qua search).
- jina-embeddings-v3: 570M tham số, tối đa 8192 token, có các LoRA adapter theo task. Adapter `separation` dành cho clustering. Theo blog Jina model hỗ trợ 89 ngôn ngữ; một trang tổng hợp ghi "30 languages" và giấy phép CC BY-NC 4.0 (không dùng thương mại, chưa đối chiếu model card) — [jina-embeddings-v3, arXiv 2409.10173](https://arxiv.org/html/2409.10173v3) (bậc 1, 2024-09, qua search); [Jina blog (DE)](https://jina.ai/de/news/jina-embeddings-v3-a-frontier-multilingual-embedding-model) (bậc 1, 2024, qua search).
- EmbeddingGemma-300M: context tối đa **2048** token, 768 chiều (MRL xuống 128). MTEB Multilingual v2 mean(task) 61,15 ở 768 chiều và 58,23 ở 128 chiều. Không tìm thấy điểm clustering riêng — [google/embeddinggemma-300m model card](https://huggingface.co/google/embeddinggemma-300m) (bậc 1, 2025, qua search); [EmbeddingGemma paper, arXiv 2509.20354](https://arxiv.org/pdf/2509.20354v3) (bậc 1, 2025-09, qua search).
- multilingual-e5-large-instruct: 24 layer, 1024 chiều ([E5 README](https://raw.githubusercontent.com/microsoft/unilm/master/e5/README.md), bậc 1, đã mở). README không ghi giới hạn token. Nền XLM-R nên giới hạn thường được nêu là 512, nhưng **chưa xác nhận được bằng nguồn mở được** (model card bị chặn).
- AITeamVN/Vietnamese_Embedding: fine-tune từ bge-m3 trên khoảng 300k bộ ba (query, positive, negative) tiếng Việt, `max_seq_length = 2048`, 1024 chiều, Apache 2.0. Model tối ưu cho retrieval (Acc@1 Legal Zalo 0,7274 so với 0,5682 của bge-m3 gốc) — [mirror model card](https://huggingface.co/spaces/shayan5422/back_rag_huggingface/blob/main/model_data_json/AITeamVN_Vietnamese_Embedding.json) (bậc 3, qua search; model card gốc bị chặn).
- BERTopic docs: mỗi document chỉ nhận một topic, trong khi "documents may contain a mixture of topics. This can be accounted for by splitting up the documents into sentences". Cách thay thế là `.approximate_distribution` (cửa sổ trượt trên token, so c-TF-IDF với topic). Tip trong docs: với document lớn thì "typically want to split them up into either paragraphs or sentences" — [BERTopic Topic Distributions](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/distribution/distribution.md) (bậc 1, đọc 2026-10, đã mở).
- Bằng chứng ngược chiều: trong một nghiên cứu về domain, lấy trung bình vector câu thành vector document rồi gom thì khôi phục domain gốc tốt hơn hẳn so với gom từng câu. Gom theo câu bám vào đặc trưng bề mặt nông hơn — [Translation Transformers Rediscover Inherent Data Domains, arXiv 2109.07864](https://arxiv.org/pdf/2109.07864) (bậc 1, 2021, qua search). Lưu ý: ở đây mục tiêu là domain (chủ đề rộng), không phải "nguyên nhân" trong đoạn nhiều ý.
- "Length-induced embedding collapse": embedding của văn bản dài hơn có cosine với nhau cao hơn, dồn cụm lại. Tác giả giải thích là self-attention hoạt động như bộ lọc thông thấp mạnh dần theo độ dài, và đề xuất TempScale (+0,94% MTEB, +1,10% LongEmbed) — [Zhou et al., ACL 2025, arXiv 2410.24200](https://aclanthology.org/2025.acl-long.1396) (bậc 1, 2025, qua search).
- Sub-Sentence Encoder: embedding theo mệnh đề (proposition) thay vì cả câu. Trên C-STS, zero-shot GPT-4 đạt Spearman 36,9 → 37,2 khi thêm sub-encoder — [Sub-Sentence Encoder, arXiv 2311.04335](https://arxiv.org/pdf/2311.04335) (bậc 1, 2023-11, qua search).

### Nhận định
- Đoạn 4–5 câu tiếng Việt có lẫn tiếng Anh thường chỉ khoảng vài trăm token, dưới cả ngưỡng 512, nên **không cần quan tâm truncation**. Giới hạn 32K/8192 không phải lợi thế ở bài toán này. Ước lượng này chưa có nguồn, nên đếm thử bằng tokenizer của model đã chọn.
- Rủi ro chính là **pha loãng ý**: đoạn kể "hiện tượng X, đã thử Y, nguyên nhân là Z" thì phần lớn token nói về X và Y. Ba hướng xử lý: (a) tách câu rồi embed từng câu, (b) dùng LLM trích riêng câu/phát biểu nguyên nhân rồi embed (xem câu phụ 4), (c) dùng instruction (xem câu phụ 3). Hướng (a) rẻ nhưng sinh ra bài toán đa nhãn và nhiều câu "đã thử khởi động lại" chung chung lấn át. Với vài trăm bản ghi, hướng (b) khả thi và nhắm đúng mục tiêu hơn.
- Collapse theo độ dài cho thấy nếu trộn bản ghi rất ngắn ("đã xử lý") với đoạn dài, các đoạn dài sẽ dễ bị gom chung với nhau chỉ vì dài. Nên lọc riêng bản ghi quá ngắn.

### Khoảng trống
- Không tìm thấy thí nghiệm nào so sánh gom theo câu với gom theo đoạn cho văn bản nhiều ý ở cấp "nguyên nhân/lý do". Truy vấn đã thử: "sentence-level vs document-level embeddings clustering multi-topic paragraphs split sentences".
- Chưa xác nhận được giới hạn 512 của multilingual-e5-large-instruct từ model card (bị chặn).

## 2. Token kỹ thuật (IP, path, lệnh, hash, mã lỗi, tên tiến trình)

### Kết luận ngắn
Có bằng chứng định tính khá nhất quán: embedding thiên về trùng lặp bề mặt (từ, danh từ chung, cấu trúc), và chuỗi định danh như IP, timestamp, hostname bị tokenizer chặt vụn rồi chiếm trọng số không tương xứng. Thay bằng placeholder giúp cải thiện, nhưng **không tìm thấy ablation định lượng** về mask trước khi embed văn bản người viết. Mức chắc chắn: trung bình cho hướng xử lý, thấp cho độ lớn hiệu ứng.

### Phát hiện có nguồn
- Trong sentence transformer SOTA, cosine phụ thuộc vào mức trùng **danh từ tham thể** giữa hai câu nhiều hơn là vào vị ngữ hay bổ ngữ chung — [Nikolaev & Padó, Representation biases in sentence transformers, arXiv 2301.13039](https://ar5iv.labs.arxiv.org/html/2301.13039) (bậc 1, 2023, qua search).
- Học tương phản kiểu SimCSE chấm câu có cấu trúc bề mặt giống nhau là gần nghĩa. Trong ví dụ của paper, một paraphrase khác cấu trúc có điểm thấp hơn một câu chỉ chèn thêm phủ định — [OssCSE, EMNLP 2023](https://aclanthology.org/2023.emnlp-main.448) (bậc 1, 2023, qua search).
- Test bộ ba (anchor, paraphrase, distractor trùng từ): "lexical influence" tồn tại ở mọi độ sâu của model, nhất quán qua kiến trúc, chế độ huấn luyện và hàm mục tiêu, "including the models trained for semantic similarity". Instruction tuning và metric learning giảm thiên lệch nhưng không xóa được — [On the Persistent Effects of Lexicality in LLMs, arXiv 2606.02750](https://arxiv.org/pdf/2606.02750) (bậc 1, 2026-06, qua search).
- Về log: cosine giữa embedding của hai dòng log "overlooks the importance of several keywords and favors irrelevant words with a large number of letters, such as timestamps or IP addresses" — [LLMLog, arXiv 2508.09594](https://arxiv.org/pdf/2508.09594) (bậc 1, 2025-08, qua search).
- Embed nguyên dòng log cho kết quả kém vì định danh (IP, port, ngày, hostname) không được tokenizer và model ngôn ngữ xử lý tốt. Thay bằng placeholder cải thiện được, "but the embedding still represents syntax rather than meaning". Paper đề xuất sinh mô tả ngữ nghĩa trước khi embed — [arXiv 2506.17512 (Matryoshka / semantic-aware parsing)](https://arxiv.org/html/2506.17512v1) (bậc 1, 2025, qua search; cùng paper với [32] của report trước).
- BERTopic FAQ: với document embedding thường "no need to preprocess", ngoại trừ dữ liệu nhiều nhiễu như HTML tag, vì chúng "typically do not contribute to the meaning" — [BERTopic FAQ](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/faq.md) (bậc 1, đọc 2026-10, đã mở).
- Model cho code/kỹ thuật: Qwen3-Embedding-8B đạt **80,68 MTEB Code** — [Qwen3 Embedding tech report, arXiv 2506.05176](https://arxiv.org/html/2506.05176v1) (bậc 1, 2025-06, qua search). Qwen3-Embedding-0.6B đạt 75,41 MTEB-Code — [Qwen3-Embedding README](https://github.com/QwenLM/Qwen3-Embedding) (bậc 1, đã mở).
- Trùng lặp bug report và crash: nhóm stack-trace dùng thước đo tương đồng riêng cho stack (S3M; dedupT coi cả stack trace là một document và adapt LM lên stack trace) thay vì embedding văn bản thường — [S3M, arXiv 2103.10526](https://ar5iv.labs.arxiv.org/html/2103.10526) (bậc 1, 2021, qua search); [dedupT, arXiv 2508.19449](https://arxiv.org/abs/2508.19449v1) (bậc 1, 2025, qua search).

### Nhận định
- Với mục tiêu gom theo **nguyên nhân**, token định danh cụ thể (IP, đường dẫn đầy đủ, hash, PID, timestamp) gần như luôn là nhiễu. Chúng khiến hai bản ghi cùng máy/cùng đường dẫn bị coi là gần nhau dù khác nguyên nhân, đúng kiểu "trùng danh từ tham thể" ở trên. Nên thay bằng **placeholder có kiểu** (`<IP>`, `<PATH>`, `<HASH>`, `<NUM>`) thay vì xóa hẳn, để giữ thông tin "có một đường dẫn ở đây". Regex mask của report trước dùng lại được.
- Ngược lại, token mang **loại** lỗi (tên tiến trình, mã lỗi, tên lệnh, tên dịch vụ) có thể chính là tín hiệu nguyên nhân. Không nên mask; có thể chuẩn hóa (vd gom các biến thể viết của cùng mã lỗi). Ranh giới "định danh hay loại" phụ thuộc domain, nên quyết định bằng cách xem nearest neighbour trên mẫu thật. Không có nguồn cho quy tắc chung.
- Có thể tách token kỹ thuật ra thành **cột đặc trưng riêng** (tập mã lỗi, tên tiến trình) để thống kê chéo với cụm nghĩa, thay vì để chúng chi phối vector.
- Với vài trăm bản ghi, chạy cả hai phiên bản (mask và không mask) rồi so cụm hoặc nearest neighbour với 50–100 bản ghi đã gán tay là rẻ, và đó là cách duy nhất có số liệu cho chính dữ liệu của mình.

### Khoảng trống
- Không có ablation định lượng mask/không mask cho văn bản người viết có lẫn token kỹ thuật. Truy vấn đã thử: "log embedding masking variables IP numbers before encoding semantic similarity effect study", "duplicate bug report detection sentence embeddings stack traces identifiers preprocessing effect".
- Không có đánh giá embedding cho tiếng Việt lẫn token kỹ thuật.

## 3. Instruction-aware / goal-aware embedding: lái embedding về "nguyên nhân"

### Kết luận ngắn
Có thể lái được một phần. Model instruction-aware (Qwen3-Embedding, e5-instruct, INSTRUCTOR) tăng khoảng 1–5% khi có instruction đúng task. Benchmark có điều kiện (C-STS) và benchmark instruction-following cho thấy model tổng quát **lái theo khía cạnh kém**: Spearman dưới 50 trên C-STS, điểm bị dao động mạnh theo cách viết prompt, và có bằng chứng instruction không liên quan vẫn cho điểm tốt. Các phương pháp chuyên dụng (InBedder, GSTransform, CASE) lái tốt hơn rõ, nhưng chỉ đánh giá trên tiếng Anh. Mức chắc chắn: trung bình.

### Phát hiện có nguồn
- Qwen3-Embedding: "using instructions (instruct) typically yields an improvement of 1% to 5% compared to not using them". Khuyến nghị tự viết instruction cho task, và **viết instruction bằng tiếng Anh** trong bối cảnh đa ngữ vì phần lớn instruction lúc train là tiếng Anh. Định dạng: `Instruct: {task_description}\nQuery:{text}` — [Qwen3-Embedding README](https://github.com/QwenLM/Qwen3-Embedding) (bậc 1, 2025-06, đã mở).
- e5-instruct dùng instruction riêng cho từng dataset clustering, dạng "Identify the topic or theme of StackExchange posts based on the given paragraphs", "Identify the main category of Biorxiv papers based on the titles and abstracts" — [unilm/e5/utils.py](https://raw.githubusercontent.com/microsoft/unilm/master/e5/utils.py) (bậc 1, đọc 2026-10, đã mở). Như vậy instruction clustering kiểu "Identify the <khía cạnh> of <loại văn bản>" là đúng phân phối lúc train.
- INSTRUCTOR: template "Represent the `domain` `text_type` for `task_objective`:", repo có ví dụ dùng embedding tùy biến cho clustering — [INSTRUCTOR README](https://github.com/xlang-ai/instructor-embedding) (bậc 1, đã mở). Ablation trong paper: fine-tune không instruction trên dữ liệu trộn đối xứng/bất đối xứng thì giảm điểm, có instruction thì hưởng lợi cộng dồn. Chưa thấy ablation riêng cho clustering — [One Embedder, Any Task, Findings ACL 2023, arXiv 2212.09741](https://arxiv.org/pdf/2212.09741) (bậc 1, 2023, qua search). **Nhận định:** INSTRUCTOR dựa trên GTR/T5 tiếng Anh, không hợp với tiếng Việt.
- C-STS (đo tương đồng theo một điều kiện bằng ngôn ngữ tự nhiên, khoảng 19k ví dụ): các hệ tốt nhất là SimCSE và GPT-4 chỉ đạt Spearman **47,5 và 43,6** — [C-STS, Deshpande et al., EMNLP 2023, arXiv 2305.15093](https://ar5iv.labs.arxiv.org/html/2305.15093) (bậc 1, 2023, qua search). Một paper sau ghi SimCSE-large 43,2 (cấu hình khác) — [PoLi-RL, arXiv 2510.04080](https://arxiv.org/pdf/2510.04080) (bậc 1, 2025, qua search).
- CASE: embedding từ LLM luôn tốt hơn embedding MLM trên C-STS. Trừ đi embedding của điều kiện giúp ổn định, và một phép giảm chiều có giám sát cải thiện thêm. Chỉ đánh giá tiếng Anh — [CASE, arXiv 2503.17279](https://arxiv.org/pdf/2503.17279) (bậc 1, 2025, qua search). Projection phi tuyến có giám sát 512 chiều: NV-Embed 69,30, SFR 62,85, SimCSE-base 56,60 — [arXiv 2509.14399, Bảng 12](https://arxiv.org/pdf/2509.14399) (bậc 1, 2025, qua search).
- InBedder ("Answer is All You Need", ACL 2024): coi instruction là câu hỏi về văn bản và embed **câu trả lời dự kiến**. Cùng một corpus gom theo các instruction khác nhau cho ra các cách gom khác nhau và diễn giải được — [InBedder, ACL 2024](https://aclanthology.org/2024.acl-long.27) (bậc 1, 2024, qua search); [repo InBedder](https://github.com/zhang-yu-wei/InBedder) (bậc 1, đã mở: định dạng `### Input ... ### Instruction ... ### Response`, checkpoint llama-2-7b và roberta-large).
- GSTransform (ACL 2025, oral): biến đổi không gian embedding có sẵn theo instruction, không cần encode lại corpus. Instruction-aware clustering trung bình **66,01** so với 55,31 của baseline mạnh nhất (InBedder-Llama2). Dataset clustering gồm chủ đề (AG-News, NYTClust), địa lý (MNews), loại ngôn ngữ (MultiHate), intent/cảm xúc (IntEmo). Paper ghi nhận "generic embedding models lack instruction-following ability" — [GSTransform, arXiv 2505.24754](https://arxiv.org/pdf/2505.24754) (bậc 1, 2025, qua search); [repo GSTransform](https://github.com/YingchaojieFeng/GSTransform) (bậc 1, đã mở: quy trình `pre_encode` một lần rồi áp instruction).
- Độ nhạy prompt: 6 model, 11 dataset, 15 prompt mỗi dataset. Điểm báo cáo bằng một prompt "misrepresent the distribution". Chọn prompt có lợi có thể đưa bất kỳ model nào lên hạng nhất. Hệ số biến thiên đến 45% chỉ thấy ở trang tóm tắt thứ cấp, chưa xác nhận — [One prompt is not enough, Kostiuk & Enevoldsen, arXiv 2605.22544](https://arxiv.org/html/2605.22544) (bậc 1, 2026-05, qua search).
- Instruction không liên quan vẫn có thể cho điểm tốt trên task embedding, nên chưa chắc model thật sự "làm theo" instruction (Gonzalez-Gutierrez & Hovy 2025, qua phần related work của một paper khác) — [Your Prompt Should Do More, arXiv 2610.10508](https://arxiv.org/html/2610.10508v1) (bậc 1, 2026-10, qua search; nguồn gốc chưa mở).
- FollowIR: phần lớn retriever **kém đi** khi instruction dài hơn, chỉ model dùng instruction đúng cách mới hưởng lợi — [FollowIR, arXiv 2403.15246](https://arxiv.org/pdf/2403.15246) (bậc 1, 2024, qua search). Qwen3-Embedding-0.6B đạt FollowIR 5,09, bge-m3 −3,11, e5-large-instruct −0,40, Qwen3-4B 11,56 (cột "Inst. Retri." trong MMTEB) — [Qwen3-Embedding README](https://github.com/QwenLM/Qwen3-Embedding) (bậc 1, đã mở).

### Nhận định
- Với e5-instruct hoặc Qwen3-Embedding, một instruction dạng "Instruct: Identify the root cause of the problem described in this maintenance note\nQuery: …" đáng thử vì gần như miễn phí. Kỳ vọng tăng vài phần trăm, không phải biến đổi về chất. Benchmark C-STS và GSTransform cho thấy embedding tổng quát vẫn bị chi phối bởi chủ đề và bề mặt dù có điều kiện.
- Vì điểm dao động mạnh theo cách viết prompt, cần thử 3–5 cách viết instruction và đo trên bộ nhãn tay nhỏ, không tin một prompt.
- Cách "lái" chắc chắn hơn trong khung on-prem là ý tưởng của InBedder ở dạng thủ công: cho LLM **trả lời câu hỏi "nguyên nhân là gì?"** cho từng bản ghi, rồi embed câu trả lời. Đây chính là extract-then-embed ở câu phụ 4. Với vài trăm bản ghi, chi phí không đáng kể.
- jina-v3 adapter `separation` là một cách lái theo task (clustering), không theo khía cạnh. Không giúp tập trung vào nguyên nhân.

### Khoảng trống
- Không có đánh giá instruction-aware clustering cho tiếng Việt hoặc đa ngữ. Mọi benchmark trên (C-STS, GSTransform, InBedder, CASE) đều tiếng Anh.
- Chưa mở được bảng chi tiết GSTransform, InBedder, C-STS. Không có số đo riêng cho "instruction clustering có/không" của Qwen3 hay e5-instruct (README Qwen3 chỉ có con số chung 1–5%).

## 4. Embed nguyên văn so với embed bản tóm tắt / phát biểu trích xuất

### Kết luận ngắn
Bằng chứng lẫn lộn. Tóm tắt chung chung trước khi embed **không cải thiện nhất quán**. Viết lại có hướng (tóm tắt "intent" của IDAS, keyphrase theo mục tiêu, mô tả ngữ nghĩa thay dòng log) thì thường giúp, nhưng có rủi ro bản viết lại lệch nghĩa. Mức chắc chắn: trung bình–thấp, vì phần lớn chỉ đọc qua snippet và không có ablation sạch.

### Phát hiện có nguồn
- Petukhova et al. 2024: thêm bước tóm tắt (như một cách giảm chiều) trước khi embed "do not consistently enhance clustering efficiency", và tăng số chiều cũng vậy — [Text Clustering with LLM Embeddings, arXiv 2403.15112](https://arxiv.org/pdf/2403.15112) (bậc 1, 2024-03, qua search).
- IDAS dùng LLM viết tóm tắt trừu tượng cho utterance trước khi gom, "cleaning the input for more effective clustering" (đã có ở report trước [51]). Mô tả lại trong [NILC, arXiv 2511.05913](https://arxiv.org/pdf/2511.05913) (bậc 1, 2025-11, qua search).
- Dial-In LLM: keyphrase expansion tăng NMI, nhưng keyphrase sinh ra "could distort the original sentence's meaning, leading to less representative clusters". Goodness score và NMI không phải lúc nào cũng khớp nhau — [Dial-In LLM, arXiv 2412.09049](https://arxiv.org/pdf/2412.09049) (bậc 1, 2024-12, qua search).
- Với log, mask placeholder vẫn để embedding "represents syntax rather than meaning". Paper chọn sinh mô tả ngữ nghĩa trước rồi mới embed — [arXiv 2506.17512](https://arxiv.org/html/2506.17512v1) (bậc 1, 2025, qua search).
- InBedder embed "câu trả lời" cho instruction thay cho nguyên văn, và cho thấy cách gom thay đổi theo câu hỏi — [InBedder](https://aclanthology.org/2024.acl-long.27) (bậc 1, 2024, qua search).
- Few-shot clustering (Viswanathan et al., TACL 2024; report trước [49]) dùng LLM mở rộng keyphrase trước khi embed. Report trước chỉ có số qua trích đoạn.

### Nhận định
- Phân biệt **tóm tắt chung** (mất định hướng, kết quả không ổn định) với **trích có mục tiêu** (một câu "nguyên nhân: …" chuẩn hóa theo schema). Bằng chứng tích cực đều thuộc loại thứ hai. Với mục tiêu đếm theo nguyên nhân, nên trích có mục tiêu.
- Nên giữ cả hai vector (nguyên văn đã mask và phát biểu trích xuất). Nearest neighbour trên nguyên văn dùng để kiểm tra phát biểu trích có trung thành không: hai bản ghi nguyên văn rất gần mà phát biểu nguyên nhân khác hẳn là dấu hiệu cần xem lại (xem câu phụ 6).
- Phần so sánh định lượng extract-then-cluster (Clio, TnT-LLM, KPA) thuộc góc nghiên cứu khác (câu phụ 1 của brief).

### Khoảng trống
- Không có ablation nào giữ nguyên model embedding và thuật toán, chỉ thay "nguyên văn" bằng "phát biểu trích xuất có mục tiêu" trên văn bản kỹ thuật nhiều câu. Truy vấn đã thử: "summarize then embed LLM summary improves text clustering comparison raw text", "LLM rewrite or summarize texts before embedding improves clustering NMI intent discovery 2024 2025".

## 5. Gom cụm khi chỉ có 200–500 điểm (đến vài nghìn), và điểm MTEB clustering của model mới

### Kết luận ngắn
Ở n = vài trăm, UMAP+HDBSCAN (mặc định của BERTopic) là lựa chọn kém ổn định. Chính docs BERTopic nói khoảng 1000 document đã "very difficult". HDBSCAN rất nhạy với `min_cluster_size`/`min_samples` và dễ sinh nhiều cụm nhỏ hoặc nhiều nhiễu; UMAP có tính ngẫu nhiên. Agglomerative (average linkage, cosine) với `distance_threshold` tất định, có dendrogram để chọn độ mịn, và ở quy mô này chạy tức thì. Vài bằng chứng thực nghiệm cho thấy nó ổn định hơn. Mức chắc chắn: trung bình–cao cho hướng đi, thấp cho con số cụ thể.

### Phát hiện có nguồn
- BERTopic FAQ: "you might only have a few documents (~1000). This makes it very difficult to properly extract topics". Ít topic thì giảm `min_topic_size` hoặc `n_neighbors` của UMAP. Nhiều nhãn `-1` có thể nghĩa là không có nhiều topic — [BERTopic FAQ](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/faq.md) (bậc 1, đọc 2026-10, đã mở).
- BERTopic FAQ: kết quả khác nhau giữa các lần chạy do UMAP ngẫu nhiên. Cố định `random_state` để tái lập, đổi lại mất hiệu năng. Nên tính embedding một lần rồi chạy nhiều lần với tham số khác nhau — [BERTopic FAQ](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/faq.md) (bậc 1, đã mở).
- UMAP docs: UMAP "relatively stable" nhưng vẫn biến động giữa các lần chạy. Ở chế độ đa luồng, kết quả **không thể tái lập** kể cả khi đặt seed, do race condition; muốn tái lập tuyệt đối phải đặt seed (chạy đơn luồng) — [UMAP Reproducibility](https://github.com/lmcinnes/umap/blob/master/doc/reproducibility.rst) (bậc 1, không rõ ngày, đã mở).
- HDBSCAN docs: `min_cluster_size` là tham số chính ("smallest size grouping that you wish to consider a cluster"). `min_samples` mặc định bằng `min_cluster_size` và quyết định mức "bảo thủ": lớn thì nhiều nhiễu hơn. Trên digits, `min_cluster_size` 60 chỉ ra 2 cụm, còn thêm `min_samples=15` thì khôi phục được các cụm. `cluster_selection_epsilon` gộp các micro-cluster khi muốn `min_cluster_size` nhỏ. `cluster_selection_method='leaf'` cho nhiều cụm nhỏ đồng nhất, còn `'eom'` mặc định có xu hướng ra "one or two large clusters and then a number of small extra clusters". `allow_single_cluster` dùng khi dữ liệu có thể chỉ có một khối — [HDBSCAN Parameter Selection](https://github.com/scikit-learn-contrib/hdbscan/blob/master/docs/parameter_selection.rst) (bậc 1, không rõ ngày, đã mở).
- scikit-learn: `min_cluster_size` mặc định 5; giá trị quá nhỏ "will lead to false sub-clusters being picked up". Trong demo, cùng dữ liệu ra 4 cụm ở `min_cluster_size=5` và khoảng 90 cụm ở 3 — [scikit-learn HDBSCAN demo](https://scikit-learn.org/stable/auto_examples/cluster/plot_hdbscan.html) (bậc 1, qua search).
- scikit-learn: agglomerative có hành vi "rich get richer" nên cỡ cụm không đều. Single linkage tệ nhất về mặt này; Ward đều nhất nhưng chỉ dùng được khoảng cách Euclid; "for non Euclidean metrics, average linkage is a good alternative". Dendrogram hữu ích "more so in the case of small sample sizes" — [scikit-learn clustering user guide](https://raw.githubusercontent.com/scikit-learn/scikit-learn/main/doc/modules/clustering.rst) (bậc 1, bản main, đã mở).
- sentence-transformers: agglomerative với ngưỡng cho phép điều khiển cụm "many small and fine-grained clusters or few coarse-grained clusters", chỉ hợp với "a few thousand sentences" (đúng quy mô ở đây) — [sentence-transformers clustering README](https://raw.githubusercontent.com/UKPLab/sentence-transformers/master/examples/sentence_transformer/applications/clustering/README.md) (bậc 1, đã mở; report trước [40]).
- Trong một mô phỏng, HDBSCAN chỉ tốt khi đã giảm chiều bằng UMAP, có thể vì nó chỉ gán lõi dày đặc và để nhiều điểm không gán — [Statistical power for cluster analysis, arXiv 2003.00381](https://arxiv.org/pdf/2003.00381) (bậc 1, 2020, qua search). Một nghiên cứu khác thấy UMAP mặc định làm tăng cả số cụm lẫn số điểm không gán, và gọi hành vi đó "too unstable to be useful in practice" (bối cảnh không phải văn bản) — [arXiv 2505.15570](https://arxiv.org/pdf/2505.15570) (bậc 1, 2025, qua search).
- Agglomerative ổn định hơn trong hai nghiên cứu dùng embedding văn bản: (a) average linkage có bootstrap mean ARI **0,807 (SD 0,117)** — [ASTRA, arXiv 2603.28816](https://arxiv.org/pdf/2603.28816) (bậc 1, 2026, qua search); (b) Claim2Vec so 7 thuật toán không cần biết trước số cụm, tune bằng silhouette, HDBSCAN chạy trên UMAP. Theo tóm tắt search, agglomerative nhất quán nhất, còn HDBSCAN cạnh tranh trên dataset nhỏ nhưng xuống khi dữ liệu lớn — [Claim2Vec, arXiv 2604.09812](https://arxiv.org/pdf/2604.09812) (bậc 1, 2026-04, qua search; chưa thấy bảng số).
- Ngưỡng Jaccard của `clusterboot`: 0,6–0,75 là "doubtful", trên 0,85 là ổn định cao. Cụm ổn định từ phương pháp cứng nhắc vẫn có thể không hợp lệ — [clusterboot {fpc}](https://search.r-project.org/CRAN/refmans/fpc/html/clusterboot.html) (bậc 1, qua search; report trước [73]).
- Điểm MMTEB clustering (cột "Clust.", lấy từ leaderboard ngày 2025-06-06 cho model so sánh): **Qwen3-Embedding-8B 57,65; 4B 57,15; 0.6B 52,33**; gemini-embedding-exp-03-07 54,59; gte-Qwen2-7B-instruct 52,77; gte-Qwen2-1.5B 52,05; multilingual-e5-large-instruct 50,75; GritLM-7B 49,75; text-embedding-3-large 46,89; Cohere-multilingual-v3 46,89; bge-m3 40,88; NV-Embed-v2 40,80. Mean(Task): Qwen3-8B 70,58, 4B 69,45, 0.6B 64,33, e5-large-instruct 63,22, bge-m3 59,56 — [Qwen3-Embedding README](https://github.com/QwenLM/Qwen3-Embedding) (bậc 1, 2025-06, đã mở; đây là số tự báo của Qwen, số của model khác lấy từ leaderboard).
- VN-MTEB không có Qwen3-Embedding trong bảng kết quả. Bảng clustering của report trước vẫn là số tiếng Việt duy nhất (e5-large-instruct 52,96; bge-m3 45,90; gte-Qwen2-7B 53,15) — [VN-MTEB, arXiv 2507.21500](https://arxiv.org/pdf/2507.21500) (bậc 1, 2025-07, qua search).

### Nhận định
- Ở n = 200–500, **agglomerative (cosine, average linkage) + `distance_threshold`** nên là mặc định. Lý do: tất định, không cần UMAP, độ mịn điều khiển bằng một ngưỡng có ý nghĩa (cosine), và đọc được dendrogram. Chi phí O(n²) không đáng kể với vài nghìn điểm. Nếu muốn có nhãn nhiễu thì dùng HDBSCAN trực tiếp trên embedding đã chuẩn hóa (không UMAP) hoặc PCA nhẹ, với `min_cluster_size` 3–5, `min_samples` nhỏ, quét vài giá trị. Nên coi kết quả đó là gợi ý, không phải đáp án.
- Vài trăm bản ghi sẽ sinh **nhiều cụm nhỏ (2–4 phần tử)** và một đuôi dài singleton. Đó là thực tế của dữ liệu, không phải lỗi. Với mục tiêu đếm, cụm nhỏ chỉ là đơn vị để LLM hoặc người gộp/đặt tên, không nên báo tần suất trực tiếp.
- Kiểm tra ổn định rẻ ở quy mô này: chạy lại với 5–10 seed (nếu dùng UMAP/k-means) hoặc bootstrap 80% mẫu, rồi tính ARI hay Jaccard theo cụm (`clusterboot`). Chỉ những cụm có Jaccard trên khoảng 0,75 mới đáng đưa vào bảng.
- MMTEB đặt Qwen3-Embedding-0.6B (52,33) ngang e5-large-instruct (50,75) về clustering, và 4B/8B cao hơn khoảng 5–7 điểm. Nhưng benchmark là chủ đề rộng (arXiv, Reddit), không phải nguyên nhân kỹ thuật, và chưa có số tiếng Việt cho Qwen3. Với vài trăm bản ghi, chạy cả 8B trên CPU/GPU nhỏ vẫn khả thi, nên chi phí không còn là lý do loại 8B. Quyết định nên dựa trên đo với bộ nhãn tay.

### Khoảng trống
- Không có benchmark công khai nào đo trực tiếp chất lượng/ổn định của HDBSCAN so với agglomerative cho text embedding ở n = 200–500. Hai nghiên cứu ASTRA và Claim2Vec chỉ đọc qua snippet. Truy vấn đã thử: "HDBSCAN small dataset few hundred points min_cluster_size instability UMAP random seed", "clustering stability bootstrap adjusted rand index small sample text embeddings agglomerative vs HDBSCAN".
- Không có số VN-MTEB cho Qwen3-Embedding, EmbeddingGemma, jina-v3.

## 6. Embedding ở quy mô nhỏ như công cụ hỗ trợ / kiểm tra bên cạnh LLM coding

### Kết luận ngắn
Khi LLM đã gán nhãn từng bản ghi, embedding vẫn hữu ích ở vai trò **phân loại ưu tiên (triage)**: khử trùng lặp, xem nearest neighbour, và đánh dấu bản ghi có nhãn khác hẳn hàng xóm gần nhất để người xem lại. Có tiền lệ: phát hiện lỗi gán nhãn bằng phương pháp dựa trên lân cận, và dùng độ tương đồng embedding để đánh dấu bất đồng trong coding. Nhưng độ tương đồng không thay được đánh giá của chuyên gia. Mức chắc chắn: trung bình.

### Phát hiện có nguồn
- Klie et al. tái hiện **18 phương pháp** phát hiện lỗi gán nhãn trên 9 dataset tiếng Anh (phân loại văn bản, token, span), kèm giao thức đánh giá thống nhất và mã nguồn mở — [Annotation Error Detection, Computational Linguistics 2023, arXiv 2206.02280](https://arxiv.org/pdf/2206.02280) (bậc 1, 2023, qua search). Chưa xác nhận danh sách phương pháp có kNN.
- "Disagreement as Data" (LAK 2026): cosine giữa embedding các reasoning trace của LLM coder "robustly differentiates consensus from disagreement and correlates with human coding reliability". Paper cũng dùng tín hiệu này để tìm chỗ cần tinh chỉnh codebook — [arXiv 2601.12618](https://arxiv.org/html/2601.12618v1) (bậc 1, 2026-01, qua search).
- Đồng thuận người–LLM (Jaccard 0,30) thấp hơn người–người (0,52), nhưng chuyên gia mù chọn hai bên với tỷ lệ gần bằng nhau. Kết luận: "agreement-based evaluation is therefore insufficient for automation decisions" — [Agreement Is Not Quality, arXiv 2607.28890](https://arxiv.org/pdf/2607.28890) (bậc 1, 2026-07, qua search).
- Luận văn Waterloo với GPT-4o-mini: các thước đo tương đồng định lượng như cosine "missed qualitative distinctions", nên phải thêm đánh giá có cấu trúc của người — [Use of LLMs in Qualitative Analysis, UWSpace](https://uwspace.uwaterloo.ca/items/bc685484-cbde-4a59-9bb2-6f650632ae22) (bậc 2, không rõ ngày, qua search).
- Ma trận cosine cho vài nghìn câu là tức thì. `community_detection` của sentence-transformers xử lý 50k câu dưới 5 giây — [sentence-transformers clustering README](https://raw.githubusercontent.com/UKPLab/sentence-transformers/master/examples/sentence_transformer/applications/clustering/README.md) (bậc 1, đã mở).

### Nhận định
Ở vài trăm đến vài nghìn bản ghi, các cách dùng có lời nhất là:
1. **Khử trùng lặp / gần trùng** (cosine rất cao, vd ≥ 0,95, ngưỡng phải tự hiệu chỉnh): gộp bản ghi copy-paste trước khi gửi LLM, giảm số lần gọi và tránh đếm trùng.
2. **Kiểm tra nhất quán nhãn LLM**: với mỗi bản ghi, lấy k = 5 hàng xóm gần nhất trên nguyên văn đã mask. Nếu nhãn LLM khác nhãn đa số của hàng xóm *và* cosine cao, đưa vào hàng đợi người xem. Đây là tín hiệu triage, không phải phán quyết, đúng như cảnh báo "Agreement Is Not Quality".
3. **Kiểm tra độ chặt của từng nhãn**: tính cosine trung bình từ các bản ghi tới centroid của nhãn. Nhãn có độ phân tán lớn có thể đang gộp nhiều nguyên nhân, nên tách. Hai nhãn có centroid rất gần có thể là trùng, nên gộp.
4. **Lấy mẫu few-shot / mẫu đại diện**: chọn bản ghi gần centroid làm ví dụ trong prompt, và chọn bản ghi xa mọi cụm làm ứng viên cho nhãn mới.
5. **Bản ghi mới**: gán nhãn tạm bằng nearest-centroid khi cosine vượt ngưỡng, còn lại chuyển cho LLM.

### Khoảng trống
- Không tìm thấy nghiên cứu định lượng nào về "kNN trên embedding để bắt lỗi nhãn do LLM gán" cho văn bản tự do ngắn, hay ngưỡng cosine nên dùng. Truy vấn đã thử: "annotation error detection kNN embeddings Klie benchmark label noise text classification", "LLM qualitative coding consistency check embeddings nearest neighbors disagreement flag human review".

## 7. Fine-tune nhẹ theo domain

### Kết luận ngắn
Học không giám sát thuần (TSDAE, SimCSE, CT) cho embedding câu "generally perform rather badly". Adaptive pre-training (TSDAE/MLM) cộng fine-tune có nhãn tăng đến khoảng 8 điểm trên các tập theo domain, và GPL tăng đến khoảng 10 điểm cho retrieval, nhưng tốn công. Với vài trăm bản ghi, SetFit (contrastive trên ít cặp, khoảng 8 ví dụ mỗi lớp) là đường thực tế hơn khi đã có taxonomy. Mức chắc chắn: trung bình, vì số liệu là cho retrieval/duplicate tiếng Anh, không phải clustering nguyên nhân.

### Phát hiện có nguồn
- sentence-transformers: phương pháp học không giám sát "generally perform rather badly: They are not really able to learn domain specific concepts". Domain adaptation (corpus không nhãn của domain + dataset có nhãn sẵn) tốt hơn — [Domain Adaptation](https://raw.githubusercontent.com/UKPLab/sentence-transformers/master/examples/sentence_transformer/domain_adaptation/README.md) (bậc 1, đọc 2026-10, đã mở).
- Bảng TSDAE (pre-train trên corpus đích rồi fine-tune): trung bình 4 tập AskUbuntu, CQADupStack, Twitter, SciDocs là zero-shot **52,3** → TSDAE **56,5**, MLM 55,9, CT 53,0, SimCSE 52,4 ("up-to 8 points"). Với retrieval (GPL): zero-shot 45,2 → TSDAE 49,2 → GPL 51,4 → TSDAE+GPL **52,4**. GPL train khoảng 1 ngày trên V100 — cùng nguồn trên (bậc 1, đã mở).
- TSDAE chỉ cần danh sách câu: mã hóa câu bị làm hỏng (xóa 60% từ) và tái tạo lại — [TSDAE README](https://raw.githubusercontent.com/UKPLab/sentence-transformers/master/examples/sentence_transformer/unsupervised_learning/TSDAE/README.md) (bậc 1, đã mở).
- SetFit: với 8 ví dụ có nhãn mỗi lớp trên Customer Reviews, SetFit cạnh tranh được với RoBERTa-large fine-tune trên toàn bộ 3k ví dụ. Không cần prompt, train nhanh hơn một bậc trở lên — [SetFit README](https://github.com/huggingface/setfit) (bậc 1, đã mở; report trước [62]).
- Isotani et al. fine-tune Sentence-BERT riêng cho từng phần của bug report để tìm trùng lặp — [Frontiers in Computer Science 2022](https://frontiersin.org/articles/10.3389/fcomp.2022.1032452) (bậc 1, 2022, qua search).
- Chiếu có giám sát trên embedding đóng băng (không fine-tune model) đưa C-STS lên Spearman 62–69 với NV/SFR — [arXiv 2509.14399](https://arxiv.org/pdf/2509.14399) (bậc 1, 2025, qua search).

### Nhận định
- Với vài trăm bản ghi mỗi lần, corpus không đủ để TSDAE có ý nghĩa. Bảng TSDAE dùng corpus domain lớn hơn nhiều. Chỉ đáng cân nhắc khi đã cộng dồn hàng chục nghìn bản ghi.
- Khi đã có vài trăm bản ghi gán nhãn nguyên nhân (từ LLM rồi người duyệt), tận dụng chúng theo thứ tự chi phí tăng dần: (1) classifier nhẹ (logistic regression) trên embedding đóng băng; (2) SetFit để vừa tinh chỉnh không gian vừa có classifier; (3) chỉ fine-tune contrastive đầy đủ khi (1) và (2) không đủ. Cả ba đều chạy on-prem trong vài phút ở quy mô này. Đây là suy luận, chưa có số đo cho văn bản kỹ thuật tiếng Việt.
- Một phương án không đụng model: học một phép chiếu tuyến tính/MLP nhỏ trên embedding đóng băng từ các cặp "cùng nguyên nhân / khác nguyên nhân", theo ý tưởng của CASE và arXiv 2509.14399. Đây là cách "lái" về nguyên nhân có giám sát rẻ nhất.

### Khoảng trống
- Không có số đo nào về fine-tune nhẹ (vài trăm cặp) cải thiện **clustering** theo khía cạnh nguyên nhân trên văn bản kỹ thuật. Bảng của sentence-transformers là duplicate-question và retrieval.

## Truy vấn đã chạy
- Qwen3-Embedding technical report MMTEB clustering score instruction (standard)
- C-STS conditional semantic textual similarity results embedding models (standard)
- INSTRUCTOR "one embedder, any task" clustering instruction ablation (standard)
- lexical overlap bias sentence embeddings surface form similarity (standard)
- summarize then embed LLM summary improves text clustering comparison raw text (standard)
- "Answer is All You Need" instruction-following text embedding InBedder clustering (standard)
- do instruction-tuned embedding models follow instructions evaluation aspect clustering 2025 (extended)
- sentence-level vs document-level embeddings clustering multi-topic paragraphs split sentences (standard)
- HDBSCAN small dataset few hundred points min_cluster_size instability UMAP random seed (standard)
- log embedding masking variables IP numbers before encoding semantic similarity effect study (extended)
- duplicate bug report detection sentence embeddings stack traces identifiers preprocessing effect (standard)
- "On the Persistent Effects of Lexicality" embeddings paraphrase distractor results (standard)
- jina-embeddings-v3 task LoRA "separation" clustering 8192 tokens (standard)
- EmbeddingGemma 300M context length 2048 MTEB multilingual clustering prompt "task: clustering" (standard)
- AITeamVN Vietnamese_Embedding max_seq_length bge-m3 fine-tuned (standard)
- gte-multilingual-base 8192 context mGTE paper (standard)
- LLM rewrite or summarize texts before embedding improves clustering NMI intent discovery 2024 2025 (extended)
- GSTransform instruction-aware clustering benchmark datasets instructions results (standard)
- "One prompt is not enough" instruction sensitivity embedding model clustering variance (standard)
- "length-induced embedding collapse" longer texts embeddings similarity (standard)
- annotation error detection kNN embeddings Klie benchmark label noise text classification (standard)
- C-STS Deshpande 2023 condition "Spearman" SimCSE GPT-4 fine-tuned results conditional similarity (standard)
- clustering stability bootstrap adjusted rand index small sample text embeddings agglomerative vs HDBSCAN (standard)
- Claim2Vec embedding fact-check claims clustering agglomerative HDBSCAN dataset size results (standard)
- VN-MTEB leaderboard Qwen3-Embedding Vietnamese clustering score (standard)
- LLM qualitative coding consistency check embeddings nearest neighbors disagreement flag human review (standard)
- Tài liệu GitHub đọc trực tiếp: Qwen3-Embedding README; unilm/e5 README và utils.py; INSTRUCTOR, InBedder, GSTransform README; BERTopic faq.md và distribution.md; HDBSCAN parameter_selection.rst; UMAP reproducibility.rst; scikit-learn clustering.rst; sentence-transformers clustering, domain_adaptation, TSDAE README; SetFit README.
