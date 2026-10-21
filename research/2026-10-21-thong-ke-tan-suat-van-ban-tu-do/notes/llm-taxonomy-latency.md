# LLM cho sinh taxonomy, gom cụm và phân loại: đánh đổi latency/chi phí

> Ghi chú về cách truy cập nguồn (2026-10-21): proxy của phiên này chặn `arxiv.org`, `aclanthology.org`, `huggingface.co`, `openai.com`, `ai.google.dev`, `assets.anthropic.com`, `hackernoon.com`. Vì vậy số liệu của các paper arXiv dưới đây lấy từ **trích đoạn mà WebSearch trả về** (đã đối chiếu chéo khi có thể), không phải từ việc mở trực tiếp PDF. Các nguồn đã mở trực tiếp: trang giá và docs của Claude (`platform.claude.com`), trang Clio và TnT-LLM của Anthropic/Microsoft Research, README GitHub của ClusterLLM, few-shot-clustering, GoalEx, LLooM, OpenClio, SetFit, vLLM. Mỗi phát hiện ghi rõ "(qua trích đoạn search)" khi chưa mở được nguồn gốc. Writer/verifier nên coi các số đó là cần kiểm lại nếu có đường vào arXiv.

## 1. LLM sinh taxonomy từ văn bản phi cấu trúc: các phương pháp, số lần gọi LLM, chất lượng

### Kết luận ngắn
Các phương pháp chia làm hai họ: (a) **LLM đọc mẫu rồi đề xuất taxonomy** (TnT-LLM, GoalEx, LLooM, "Text clustering as classification"), số lần gọi tỷ lệ với cỡ mẫu chứ không với cỡ tập; (b) **LLM hỗ trợ clustering trên embedding** (Clio, ClusterLLM, few-shot clustering, IDAS, k-LLMmeans), số lần gọi cố định theo ngân sách (≈1.000–20.000 truy vấn) hoặc theo số cụm k. Với dữ liệu hàng triệu dòng, chỉ các phương pháp có số lần gọi không phụ thuộc N (hoặc chỉ gọi trên mẫu) là khả thi về chi phí. Mức chắc chắn: **trung bình** — kiến trúc từng phương pháp chắc chắn cao (README/trang chính thức), nhưng số liệu định lượng phần lớn đến từ trích đoạn search.

### Phát hiện có nguồn
- **TnT-LLM (Microsoft, KDD 2024):** hai pha. Pha 1: LLM tóm tắt từng tài liệu trong một mẫu, rồi sinh và tinh chỉnh taxonomy lặp qua các minibatch tóm tắt theo kiểu "stochastic optimization", zero-shot nhiều bước. Pha 2: LLM gán nhãn một mẫu cỡ vừa–lớn để làm dữ liệu huấn luyện cho classifier nhẹ (logistic regression hoặc MLP trên embedding) dùng ở quy mô lớn. Áp dụng cho phân tích intent và domain hội thoại Bing Copilot; tác giả báo taxonomy chính xác và liên quan hơn baseline, "favorable accuracy-efficiency balance" — [TnT-LLM, Microsoft Research](https://www.microsoft.com/en-us/research/publication/tnt-llm-text-mining-at-scale-with-large-language-models/) (bậc 1, 2024-03; đã mở trang, trang không có số liệu).
- TnT-LLM dùng minibatch **200** tóm tắt mỗi vòng sinh taxonomy (paper ACM; tutorial DataCamp cũng mặc định 200) — [TnT-LLM, ACM KDD](https://dl.acm.org/doi/pdf/10.1145/3637528.3671647) (bậc 1, 2024-08, qua trích đoạn search); [DataCamp tutorial](https://www.datacamp.com/tutorial/gpt-4o-langgraph-tnt-llm) (bậc 3, không rõ ngày).
- Kết quả phân loại TnT-LLM trên tập tiếng Anh có nhãn người: logistic regression trên embedding ada2 đạt accuracy **0,658** cho user intent, nhỉnh hơn GPT-4 (**0,655**); MLP trên ada2 đạt **0,650** cho domain so với GPT-4 **0,638**; ở nhiệm vụ đa nhãn, classifier distill có precision cao hơn nhưng recall thấp hơn GPT-4 (vd micro-precision 0,606 so với 0,518) — [TnT-LLM arXiv 2403.12173](https://arxiv.org/abs/2403.12173) (bậc 1, 2024-03, qua trích đoạn search, nguồn gốc của trích đoạn là các trang tóm tắt Liner/HackerNoon nên cần đối chiếu Bảng 3 của paper).
- TnT-LLM: trên các nhiệm vụ có mức đồng thuận vừa phải, evaluator GPT-4 đồng ý với đa số người nhiều hơn mức người đồng ý với nhau — [TnT-LLM arXiv](https://arxiv.org/abs/2403.12173) (bậc 1, 2024-03, qua trích đoạn search).
- Một biến thể sau TnT-LLM (arXiv 2505.23765) thêm KMeans trên embedding tóm tắt và lấy minibatch round-robin theo cụm (lấy mẫu phân tầng) — [From Chat Logs to Collective Insights](https://arxiv.org/pdf/2505.23765) (bậc 1, 2025-05, qua trích đoạn search). Có bản hiện thực mã nguồn mở "Textonomy" của mô thức TnT-LLM (ICNLSP 2026) — [ACL Anthology 2026.icnlsp-1.3](https://aclanthology.org/2026.icnlsp-1.3.pdf) (bậc 1, 2026, qua trích đoạn search).
- **Clio (Anthropic, 2024-12):** 4 bước — trích "facet" từ từng hội thoại (chủ đề, ngôn ngữ, số lượt...), gom cụm ngữ nghĩa, LLM viết tên + mô tả cụm (loại bỏ thông tin riêng tư), dựng phân cấp; "powered entirely by Claude"; tương quan r = 0,71 giữa mức đáng lo do Clio chấm và classifier của Trust & Safety — [Clio, Anthropic](https://www.anthropic.com/research/clio) (bậc 1, 2024-12; đã mở).
- Clio: chi phí ví dụ **$48,81 cho 100.000 hội thoại** (giả định trung bình 1.000 token/hội thoại): khoảng $45 cho trích facet bằng Claude 3 Haiku và $3,75 cho đặt tên cụm bằng Claude 3.5 Sonnet; phân cấp 3 mức khoảng 10/100/1.000 cụm; kiểm tra thủ công cho accuracy 96% với bộ trích tóm tắt và 97% với bộ gom cụm mức đáy — [Clio arXiv 2412.13678](https://arxiv.org/abs/2412.13678) (bậc 1, 2024-12, qua trích đoạn search).
- Clio dựng phân cấp: embed tên + mô tả từng cụm bằng `all-mpnet-base-v2` (768 chiều), k-means thành các "neighborhood" sao cho trung bình 40 cụm/neighborhood, LLM đề xuất cụm cha, lặp đến khi số cụm đỉnh đạt khoảng mong muốn; cụm chỉ được giữ nếu vượt ngưỡng tối thiểu về số tài khoản và số hội thoại; paper không công bố giá trị k chính xác — [Clio arXiv](https://arxiv.org/abs/2412.13678) (bậc 1, 2024-12, qua trích đoạn search); xác nhận chéo bởi [Urania, COLM 2025](https://arxiv.org/pdf/2506.04681) (bậc 1, 2025-06, dùng lại Simple-Clio với all-mpnet-base-v2).
- Bản mã nguồn mở **OpenClio** chạy Clio hoàn toàn local: LLM `Qwen/Qwen3-8B` qua vLLM + embedding `sentence-transformers/all-mpnet-base-v2`; có `genericSummaryFacets` cho dữ liệu không phải hội thoại; ví dụ chạy trên ~400.000 hội thoại WildChat — [OpenClio GitHub](https://github.com/Phylliida/OpenClio) (bậc 1 cho chính phần mềm, không rõ ngày, truy cập 2026-10-21).
- **GoalEx (Propose-Assign-Select, EMNLP 2023):** input là corpus + mục tiêu bằng ngôn ngữ tự nhiên; proposer (gpt-3.5-turbo/gpt-4) đề xuất mô tả cụm, assigner (flan-t5-xl local, ~20 GB VRAM, hoặc gpt-3.5) gán văn bản vào mô tả, rồi chọn tập mô tả phủ tốt; áp dụng đệ quy để dựng taxonomy (mặc định 2 mức, 8 cụm mỗi nút). README khuyến nghị tiết kiệm bằng subsample (vd `--subsample 1024`) và dùng assigner FlanT5 trước; công cụ ước tính chi phí query trước khi chạy — [GoalEx GitHub](https://github.com/ZihanWangKi/GoalEx) (bậc 1, 2023, đã mở).
- **ClusterLLM (EMNLP 2023):** LLM trả lời các truy vấn bộ ba (triplet: A giống B hay C hơn) để fine-tune embedder (Instructor/E5) và truy vấn cặp để chọn độ chi tiết (số cụm) — [ClusterLLM GitHub](https://github.com/zhang-yu-wei/ClusterLLM) (bậc 1, 2023, đã mở). Ngân sách cố định **Q = 1.024 triplet**, không phụ thuộc cỡ dataset; chi phí trung bình **~$0,6/dataset với gpt-3.5-turbo** trên 14 dataset; GPT-4 chỉ cải thiện nhẹ so với GPT-3.5 dù đắt hơn nhiều — [ClusterLLM, EMNLP 2023](https://aclanthology.org/2023.emnlp-main.858.pdf) (bậc 1, 2023-12, qua trích đoạn search).
- **"Large Language Models Enable Few-Shot Clustering" (Viswanathan et al., TACL 2024):** LLM can thiệp ở 3 điểm — trước (mở rộng keyphrase để làm giàu đặc trưng), trong (gán nhãn ràng buộc cặp cho PCKMeans), sau (sửa lỗi gán cụm). Keyphrase expansion tốt nhất, vượt K-Means baseline trên mọi dataset văn bản; PCKMeans với 20K ràng buộc do LLM gán nhãn mạnh ở 3/5 dataset. Chi phí trên OPIEC59k (gpt-3.5-turbo-0301, $1/1M token): **$42,03** PCKMeans, **$12,73** correction, **$2,24** keyphrase expansion; $41 tiền thuê người chỉ mua được <700 nhãn so với 20K nhãn GPT-3.5 — [TACL 2024](https://aclanthology.org/2024.tacl-1.18.pdf) (bậc 1, 2024, qua trích đoạn search). README cho biết 10.000 ràng buộc cặp có thể mất khoảng 1 giờ do latency API, có `cache_file` để cache kết quả — [few-shot-clustering GitHub](https://github.com/viswavi/few-shot-clustering) (bậc 1, đã mở).
- **IDAS (NLP4ConvAI 2023):** LLM viết nhãn ngắn (tóm tắt trừu tượng) cho một tập hạt giống utterance điển hình, dùng chúng làm ví dụ in-context để gán nhãn phần còn lại; encoder đóng băng embed utterance + nhãn rồi clustering; cải thiện tới **7,42%** so với SOTA không giám sát trên Banking/StackOverflow/Transport — [IDAS, ACL Anthology](https://aclanthology.org/2023.nlp4convai-1.7) (bậc 1, 2023, qua trích đoạn search). Lưu ý: IDAS gọi LLM một lần cho **mỗi** utterance (số gọi ∝ N) — **Nhận định** dựa trên mô tả phương pháp.
- **k-LLMmeans / "Summaries as Centroids" (ICLR 2026):** thay centroid số bằng bản tóm tắt do LLM viết; chỉ cần **k lần gọi LLM mỗi bước tóm tắt**, nên số gọi theo số cụm chứ không theo cỡ dữ liệu; ACC/NMI cao hơn k-means đều đặn; trên CLINC với GPT-3.5: 76,0 ACC / 92,1 NMI với **750 lần gọi**, so với ClusterLLM 83,8 ACC / 94,0 NMI với 1.618 lần gọi; tác giả nói phương pháp không nhằm vượt các phương pháp LLM-clustering SOTA phức tạp — [k-LLMmeans arXiv 2502.09667](https://arxiv.org/abs/2502.09667) (bậc 1, 2025-02/ICLR 2026, qua trích đoạn search; con số so sánh lấy từ bài review nên cần kiểm bảng gốc).
- **"Text Clustering as Classification with LLMs" (Huang & He, 2024):** chia dữ liệu thành minibatch, LLM đề xuất nhãn mỗi batch, gộp nhãn trùng nghĩa bằng một lần gọi merge, rồi LLM phân loại từng văn bản vào nhãn; trên ArxivS2S, merge giảm 143 → 122 nhãn (ground truth 93) — [arXiv 2410.00927](https://arxiv.org/abs/2410.00927) (bậc 1, 2024-10, qua trích đoạn search). Số gọi ≈ (số minibatch) + 1 merge + N lần phân loại — **Nhận định**, không phải số trong paper.
- **LLooM (CHI 2024, concept induction):** LLM tóm tắt (Distill), gom (Cluster, embedding), tổng hợp khái niệm có tiêu chí bao hàm bằng ngôn ngữ tự nhiên (Synthesize, dùng GPT-4), rồi chấm điểm từng tài liệu theo từng khái niệm (Score, 0–1, ngưỡng hóa thành nhãn nhị phân); paper dùng GPT-3.5 cho mọi bước trừ Synthesize; docs hiện tại mặc định gpt-4o-mini cho Distill/Score, gpt-4o cho Synthesize, text-embedding-3-large cho Cluster, và có `estimate_score_cost` chạy trước bước Score — [LLooM paper (Stanford HCI)](https://hci.stanford.edu/publications/2024/Lam_LLooM_CHI24.pdf) (bậc 1, 2024-05, qua trích đoạn search); [LLooM GitHub](https://github.com/michelle123lam/lloom) (bậc 1, đã mở: "GPT-4o and GPT-4o mini in the current implementation"). Ví dụ BERTopic cho ra "women, power, female" trong khi LLooM cho "Criticism of gender roles" — [LLooM GitHub](https://github.com/michelle123lam/lloom) (bậc 1).
- **Miller & Alexander, "Human-interpretable clustering of short text using LLMs" (Royal Society Open Science, 2025-01):** embedding từ LLM + Gaussian mixture model; cụm phân biệt và dễ diễn giải hơn doc2vec và LDA; dùng LLM sinh để đánh giá và thấy đồng thuận tốt với người, đề xuất LLM để lấp "validation gap"; cảnh báo nhãn người không tự động là gold standard — [arXiv 2405.07278](https://arxiv.org/abs/2405.07278) (bậc 1, 2024-05/2025-01, qua trích đoạn search); [PMC bản RSOS](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11750404/) (bậc 1).

### Nhận định
- **Bảng số lần gọi LLM (N = số dòng, k = số cụm, S = cỡ mẫu):**
  | Phương pháp | Gọi LLM | Phụ thuộc N? |
  |---|---|---|
  | TnT-LLM | S tóm tắt + S/200 vòng taxonomy + S' nhãn huấn luyện; phần còn lại do classifier | Không (chỉ mẫu) |
  | Clio | 1 lần/bản ghi (trích facet) + 1 lần/cụm (đặt tên) + vài lần/mức phân cấp | **Có** (facet), có thể giảm bằng dedup |
  | ClusterLLM | ~1.024 triplet + vài trăm cặp | Không |
  | Few-shot clustering | keyphrase: 1/bản ghi; PCKMeans: ~20K cặp | Keyphrase có; PCK không |
  | IDAS | 1/bản ghi | Có |
  | k-LLMmeans | k/bước × số bước (vd 750 trên CLINC) | Không |
  | GoalEx | proposer vài chục lần + assigner N×(số mô tả) nếu dùng LLM assigner | Có (nếu assigner là API) |
  | LLooM | Distill 1/bản ghi + Synthesize vài lần + Score N×(số khái niệm) | Có |
  | Text-clustering-as-classification | N/batch + 1 merge + N phân loại | Có |
- Với văn bản rất ngắn (vài từ – vài câu), bước "tóm tắt/trích facet" của TnT-LLM/Clio gần như thừa: văn bản đã ngắn hơn bản tóm tắt. Có thể đưa thẳng văn bản (sau dedup/che tham số) vào bước sinh taxonomy.
- Các phương pháp ∝ N (Clio facet, IDAS, LLooM Score) chỉ nên chạy trên **giá trị duy nhất sau chuẩn hóa/template**, không phải trên dòng thô.

### Khoảng trống
- Không mở được full-text arXiv nên chưa xác nhận: cỡ mẫu chính xác TnT-LLM dùng để sinh taxonomy và để huấn luyện classifier, số liệu latency/chi phí cụ thể (nếu có) trong paper, và bảng chi phí đầy đủ của Clio. Truy vấn đã thử: xem mục cuối.
- Không có phương pháp nào trong danh sách được đánh giá trên tiếng Việt hay văn bản lẫn Việt–Anh; Clio có nói đã kiểm tra đa ngôn ngữ nhưng chưa lấy được số liệu theo ngôn ngữ.

## 2. Mô thức lai để tối thiểu số lần gọi LLM

### Kết luận ngắn
Mô thức tiết kiệm nhất đã được tài liệu hóa: **dedup/che tham số → embedding + clustering → LLM 1 lần/cụm (đặt tên, gộp, tách) → LLM gán nhãn một mẫu → distill sang classifier rẻ (LR/MLP trên embedding, SetFit) → LLM chỉ cho bản ghi độ tin cậy thấp**, cộng thêm cache theo văn bản chuẩn hóa, Batch API (−50%) và prompt caching (cache hit = 0,1× giá input). Có thể chạy toàn bộ on-prem bằng model mở (Qwen) qua vLLM. Mức chắc chắn: **cao** cho các cơ chế (docs chính thức, paper), **trung bình** cho số throughput local (nguồn thứ cấp).

### Phát hiện có nguồn
- TnT-LLM chính là mô thức "LLM gán nhãn mẫu → classifier nhẹ", và classifier nhẹ (LR trên embedding) đạt accuracy ngang GPT-4 trên nhãn người (0,658 vs 0,655) — xem mục 1 — [TnT-LLM](https://arxiv.org/abs/2403.12173) (bậc 1, 2024-03, qua trích đoạn search).
- Pangakis & Wolken (NLP+CSS 2024): tái lập 14 nhiệm vụ phân loại; classifier fine-tune trên nhãn GPT-4 cho kết quả "comparable" với classifier fine-tune trên nhãn người (bản v1 viết thận trọng hơn: "slightly worse"); lớp thiểu số có thể precision/recall thấp — [Knowledge Distillation in Automated Annotation, arXiv 2406.17633](https://arxiv.org/abs/2406.17633) (bậc 1, 2024-06, qua trích đoạn search).
- SetFit: few-shot fine-tune Sentence Transformers không cần prompt; với **8 ví dụ/lớp** trên Customer Reviews cạnh tranh với RoBERTa-Large fine-tune trên 3.000 ví dụ; "typically an order of magnitude (or more) faster to train and run inference with" so với các phương pháp few-shot dùng model lớn; dùng được với checkpoint đa ngữ — [SetFit GitHub README](https://github.com/huggingface/setfit) (bậc 1, truy cập 2026-10-21).
- ClusterLLM và few-shot-clustering đều cache kết quả truy vấn LLM (`cache_file`) — [few-shot-clustering GitHub](https://github.com/viswavi/few-shot-clustering) (bậc 1).
- **Anthropic Message Batches API:** giảm **50%** cả input và output; một batch tối đa **100.000 request hoặc 256 MB**; "most batches completing within 1 hour", kết quả có khi xong hết hoặc sau 24 giờ, batch hết hạn nếu chưa xong trong 24 giờ; kết quả giữ 29 ngày; khi tải cao có thể nhiều request hết hạn hơn — [Batch processing, Claude docs](https://platform.claude.com/docs/en/build-with-claude/batch-processing) (bậc 1, truy cập 2026-10-21).
- **Prompt caching (Claude):** ghi cache 5 phút = 1,25× giá input, 1 giờ = 2×; đọc cache = **0,1×** giá input (0,05× trên Opus 5.5/Sonnet 5.5); có lãi sau 1 lần đọc (cache 5 phút); hệ số cộng dồn với chiết khấu Batch; prompt tối thiểu để cache trên Haiku 5.5 là **512 token** — [Pricing, Claude docs](https://platform.claude.com/docs/en/about-claude/pricing) và [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) (bậc 1, truy cập 2026-10-21).
- **OpenAI/Gemini Batch:** nhiều nguồn tổng hợp mô tả chiết khấu ~50%, hoàn tất trong 24 giờ — [benchlm.ai OpenAI pricing](https://benchlm.ai/openai/api-pricing), [morphllm Gemini pricing](https://www.morphllm.com/gemini-api-pricing) (bậc 3, 2026; không mở được trang chính thức của OpenAI/Google do proxy).
- **vLLM:** continuous batching, chunked prefill, **prefix caching**, PagedAttention, nhiều kiểu lượng tử hóa (FP8, INT8, INT4, GPTQ/AWQ, GGUF...) — [vLLM GitHub README](https://github.com/vllm-project/vllm) (bậc 1, truy cập 2026-10-21). Prefix caching quan trọng cho phân loại: phần system prompt chứa taxonomy được dùng lại giữa các request.
- Throughput local tham khảo: Llama-3.1-8B trên 1×H100 với vLLM, profile chat, avg generation throughput **~6.067 token/s** (max_num_seqs 1024) — [Microsoft Azure HPC blog](https://techcommunity.microsoft.com/blog/azurehighperformancecomputingblog/inference-performance-of-llama-3-1-8b-using-vllm-across-various-gpus-and-cpus/4448420) (bậc 2, 2025, qua trích đoạn search, không mở được); DeepSeek-R1-Distill-Llama-8B offline trên H100 **~5.561 output token/s**; Llama-3.1-8B trên RTX Pro 6000 **~2.744 output token/s** — [databasemart H100](https://www.databasemart.com/blog/vllm-gpu-benchmark-h100), [databasemart Pro 6000](https://www.databasemart.com/blog/vllm-gpu-benchmark-pro6000) (bậc 3, 2025). Các số khác cấu hình nên chỉ dùng làm bậc độ lớn.
- **Model local có tiếng Việt:** bảng VMLU (zero-shot, 2025-02): Qwen2.5-72B-Instruct-AWQ trung bình **69,17**, Qwen2.5-7B-Instruct **57,51**; bản mirror GitHub: SeaLLM-7B-v2.5 **53,30**, Vistral-7B-Chat **50,07**, SeaLLM-7B-v2 45,79 (mirror và leaderboard chính thức không khớp hoàn toàn) — [VMLU leaderboard](https://vmlu.ai/leaderboard), [ZaloAI-Jaist/VMLU GitHub](https://github.com/ZaloAI-Jaist/VMLU) (bậc 1–2, 2025, qua trích đoạn search). Paper VMLU (ACL 2025) ghi Qwen2.5 vượt Llama-3 cùng cỡ trên tiếng Việt — [ACL 2025 long 563](https://aclanthology.org/2025.acl-long.563.pdf) (bậc 1, 2025, qua trích đoạn search).

### Nhận định
- Pipeline đề xuất (mỗi bước cắt số lần gọi LLM tiếp theo):
  1. Chuẩn hóa + che tham số + dedup chính xác → từ N dòng còn U giá trị duy nhất (với log máy sinh, U ≪ N).
  2. Embedding + clustering U giá trị → k cụm (k cỡ vài trăm – vài nghìn).
  3. LLM **1 lần/cụm**: đọc ~10–30 ví dụ (gần tâm + biên) → tên/mô tả; thêm 1 lần (hoặc vài lần theo nhóm láng giềng như Clio) để gộp tên trùng nghĩa và dựng cấp cha → taxonomy cuối cùng có định nghĩa.
  4. LLM gán nhãn một mẫu phân tầng (vài nghìn giá trị) vào taxonomy, structured output enum → dữ liệu huấn luyện.
  5. Huấn luyện LR/MLP trên embedding đã có (gần như miễn phí) hoặc SetFit → phân loại mọi giá trị mới.
  6. Chỉ gửi LLM những bản ghi có xác suất classifier thấp hoặc xa mọi centroid; cache kết quả theo văn bản chuẩn hóa (hash) để bản ghi trùng không bao giờ gọi lại.
- Với dữ liệu nhạy cảm, Qwen2.5-7B/Qwen3-8B qua vLLM là lựa chọn on-prem hợp lý vì vừa có điểm tiếng Việt tốt nhất trong nhóm 7B trên VMLU vừa được OpenClio dùng sẵn; cần tự đo chất lượng trên dữ liệu thật.

### Khoảng trống
- Chưa có số throughput cho llama.cpp trên CPU, và chưa có benchmark chính thức của vLLM cho workload "prompt dài chung + input ngắn + output vài token" (đúng dạng phân loại).
- Chưa có số liệu công khai về tỷ lệ bản ghi rơi vào "độ tin cậy thấp" trong mô thức cascade.
- Chưa kiểm tra SeaLLM/Vistral phiên bản mới hơn (2025–2026) hay Qwen3 trên VMLU.

## 3. Ước lượng latency và chi phí cụ thể (giá 2026-10)

### Kết luận ngắn
Với model nhỏ giá rẻ nhất hiện có (Claude Haiku 5.5: $0,10 / $0,50 mỗi 1M token input/output; batch $0,05 / $0,25), phân loại **từng dòng** 1 triệu dòng tốn khoảng **$5–90** tùy có gom nhiều dòng/lần gọi, cache và batch hay không; gán nhãn **theo cụm** (vài nghìn cụm) tốn **dưới $1**. Chi phí tiền không còn là rào cản chính; latency và rate limit mới là chênh lệch lớn (1 triệu lần gọi so với vài nghìn). Mức chắc chắn: **cao** cho giá Claude (trang chính thức đã mở), **thấp–trung bình** cho giá OpenAI/Gemini (chỉ có nguồn tổng hợp, các nguồn lệch nhau); các phép tính là **Nhận định** dựa trên giả định token.

### Phát hiện có nguồn
- Giá Claude (truy cập 2026-10-21): **Haiku 5.5** (prompt ≤100K token) $0,10 input / $0,50 output / cache hit $0,01 / ghi cache 5 phút $0,125 mỗi MTok; batch $0,05 / $0,25. **Haiku 4.5** $1 / $5 (batch $0,50 / $2,50). **Sonnet 5.5** $2 / $10 (batch $1 / $5). Haiku 5.5 có giá cao hơn khi prompt >100K token ($0,50 / $2,50) — [Pricing, Claude docs](https://platform.claude.com/docs/en/about-claude/pricing) (bậc 1, truy cập 2026-10-21).
- Giá Claude 3 Haiku/3.5 Sonnet thời Clio dẫn tới $48,81/100K hội thoại 1.000 token — [Clio arXiv](https://arxiv.org/abs/2412.13678) (bậc 1, 2024-12, qua trích đoạn search). Giá hiện tại của Haiku 5.5 thấp hơn nhiều so với thời đó.
- OpenAI (nguồn tổng hợp, chưa xác minh trên trang chính thức): GPT-5 mini $0,25 input / $0,025 cached / $2,00 output, batch $0,125 / $1,00; GPT-5 nano $0,05 / $0,40, batch $0,025 / $0,20; GPT-5.4 nano $0,20 / $1,25 (trang công bố của OpenAI); có nguồn nói GPT-5.4 nano đã deprecated, chuyển sang "GPT-6 Luna" — [Introducing GPT-5.4 mini and nano, OpenAI](https://openai.com/index/introducing-gpt-5-4-mini-and-nano/) (bậc 1, 2026, qua trích đoạn search); [benchlm.ai](https://benchlm.ai/openai/api-pricing), [economize.cloud](https://www.economize.cloud/resources/open-ai/pricing/gpt-5-mini/) (bậc 3, 2026). Một nguồn ghi output GPT-5 mini $1,00 — mâu thuẫn.
- Google Gemini (nguồn tổng hợp, chưa xác minh): Gemini 3.1 Flash-Lite $0,25 / $1,50 (batch $0,125 / $0,75); Gemini 3.5 Flash-Lite $0,30 / $2,50 (batch $0,15 / $1,25); Gemini 2.5 Flash-Lite $0,10 / $0,40 nhưng được ghi là legacy, có thể đã ngừng 2026-10-16; Flash mới nhất (tên 3.7 hoặc 3.8 tùy nguồn) giá khuyến mãi $0,75 / $3,75 đến 2026-12-31 — [morphllm](https://www.morphllm.com/gemini-api-pricing), [benchlm.ai Google](https://benchlm.ai/google/api-pricing), [pricepertoken](https://pricepertoken.com/pricing-page/model/google-gemini-3.5-flash-lite) (bậc 3, 2026). Trang giá Vertex AI chính thức mở được nhưng nội dung bị cắt, không đọc được bảng giá — [Vertex AI pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing).
- Batch Claude: tối đa 100.000 request/batch, đa số xong trong 1 giờ, hạn 24 giờ — [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing) (bậc 1).
- Few-shot clustering: 10.000 truy vấn cặp tuần tự ≈ 1 giờ do latency API (≈0,36 s/truy vấn) — [few-shot-clustering README](https://github.com/viswavi/few-shot-clustering) (bậc 1).

### Nhận định (phép tính, giả định rõ ràng)
Giả định: mỗi giá trị văn bản ~30 token; system prompt chứa taxonomy + hướng dẫn ~800 token (≥512 nên cache được trên Haiku 5.5); output JSON nhãn ~10 token/dòng; N = 1.000.000 dòng.

| Kịch bản | Token input | Token output | Haiku 5.5 thường | Haiku 5.5 batch | GPT-5 mini (chưa xác minh) |
|---|---|---|---|---|---|
| A. 1 dòng/lần gọi, không cache | 830M | 10M | $83 + $5 = **~$88** | **~$44** | $207 + $20 = ~$227 |
| B. 1 dòng/lần gọi, cache taxonomy | 800M cache-hit + 30M | 10M | $8 + $3 + $5 = **~$16** | ~$8 (nếu cache hit trong batch) | $20 + $7,5 + $20 = ~$48 |
| C. 50 dòng/lần gọi (20.000 lần gọi) | 46M | 10M | $4,6 + $5 = **~$10** | **~$5** | ~$12 + $20 = ~$32 |
| D. Theo cụm: 5.000 cụm × (500 token hướng dẫn + 20 ví dụ × 30 token), 50 token output | 5,5M | 0,25M | $0,55 + $0,13 = **<$1** | <$0,5 | ~$1,9 |
| E. Mẫu distill: 5.000 dòng gán nhãn theo kịch bản C | ~0,23M | 0,05M | **~$0,05** | — | — |

- Latency: kịch bản A/B cần 1 triệu request; nếu ~0,5–1 s/request tuần tự thì 140–280 giờ, nên phải chạy song song (bị chặn bởi rate limit) hoặc dùng batch: 10 batch × 100K request, đa số xong trong ~1 giờ, tối đa 24 giờ. Kịch bản C còn 20.000 request (1 batch). Kịch bản D là 5.000 request: vài phút với song song vừa phải.
- Kịch bản C (nhiều dòng/lần gọi) rẻ nhất cho phân loại toàn bộ nhưng tăng rủi ro lệch thứ tự/bỏ sót dòng; cần ID cho từng dòng trong schema output và kiểm tra đủ số dòng.
- Local (vLLM, model 8B, 1×H100): 1M dòng × 10 token output = 10M token output; ở ~5.000 token/s thì ~35 phút cho phần sinh, cộng prefill (giảm nhiều nhờ prefix caching vì taxonomy chung). Bậc độ lớn: dưới vài giờ/triệu dòng trên 1 GPU. Chi phí là thời gian GPU, không phụ thuộc token.
- So sánh: classifier LR trên embedding đã có thì gần như tức thời (micro giây/dòng); chi phí chính là tính embedding, vốn đã trả ở bước clustering.
- Bất định lớn: giá OpenAI/Gemini thay đổi nhanh (nhiều model mới/deprecated trong 2026); số token thực của văn bản tiếng Việt có thể cao hơn tiếng Anh với cùng số từ (tokenizer) — chưa có số đo.

### Khoảng trống
- Không xác minh được giá OpenAI/Gemini trên trang chính thức (proxy chặn `openai.com/api/pricing`, `ai.google.dev`; trang Vertex AI bị cắt).
- Chưa có số đo token/từ cho tiếng Việt của tokenizer Claude/GPT/Gemini.
- Chưa tìm được số latency p50/p95 chính thức cho Haiku 5.5 hay GPT-5 mini.

## 4. Phân loại zero-shot không dùng LLM sinh

### Kết luận ngắn
Ba lựa chọn rẻ chạy on-prem: NLI zero-shot (mDeBERTa-v3 xnli), độ tương đồng embedding với mô tả nhãn, và SetFit few-shot (8–16 ví dụ/lớp). SetFit có bằng chứng mạnh nhất (cạnh tranh với fine-tune full data); NLI zero-shot đa ngữ ổn trên XNLI nhưng có thể rất kém khi lệch miền; chưa tìm được so sánh trực tiếp, cùng điều kiện giữa các lựa chọn này và LLM hiện đại trên tiếng Việt. Mức chắc chắn: **trung bình–thấp**.

### Phát hiện có nguồn
- `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`: accuracy trung bình **0,808** trên XNLI test 15 ngôn ngữ (tiếng Anh 0,883; ngôn ngữ ít tài nguyên như Swahili/Urdu ~0,74–0,75); có thể dùng cho 73 ngôn ngữ khác mà mDeBERTa đã pretrain nhưng hiệu năng có thể thấp hơn với ngôn ngữ không có trong fine-tune NLI — [Model card, Hugging Face](https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-mnli-xnli) (bậc 1, qua trích đoạn search; XNLI có tiếng Việt trong 15 ngôn ngữ — **Nhận định** từ kiến thức về XNLI, chưa mở model card để lấy số cho tiếng Việt).
- NLI zero-shot có thể thất bại lệch miền: một nghiên cứu 2025 phát hiện văn bản do IndoT5 sinh, mDeBERTa v3 zero-shot chỉ đạt 53,52% so với Random Forest 91,21% — [ResearchGate](https://www.researchgate.net/publication/411302971_Zero-Shot_Detection_of_IndoT5-Synthesized_Indonesian_Scientific_Abstracts_Using_mDeBERTa_v3) (bậc 2–3, 2025, qua trích đoạn search; nhiệm vụ khác hẳn phân loại lý do nên chỉ minh họa rủi ro).
- SetFit: 8 ví dụ/lớp cạnh tranh RoBERTa-Large full data (3K ví dụ) trên Customer Reviews; không cần prompt; đa ngữ qua checkpoint đa ngữ; train và inference nhanh hơn một bậc độ lớn so với few-shot dùng model lớn — [SetFit README](https://github.com/huggingface/setfit) (bậc 1, truy cập 2026-10-21).
- TnT-LLM cho thấy classifier nhẹ trên embedding (huấn luyện từ nhãn LLM) bằng GPT-4 trên nhãn người — [TnT-LLM](https://arxiv.org/abs/2403.12173) (bậc 1, qua trích đoạn search).

### Nhận định
- Độ tương đồng embedding với mô tả nhãn (nearest label description) là cách rẻ nhất, tái sử dụng embedding sẵn có; dùng tốt làm bước khởi đầu hoặc baseline, nhưng mô tả nhãn ngắn thường khác phân bố với văn bản thật — nên dùng centroid của vài ví dụ thật thay vì chỉ mô tả.
- Thứ tự ưu tiên hợp lý khi đã có taxonomy: SetFit/LR trên nhãn LLM của mẫu > embedding-to-centroid > NLI zero-shot.

### Khoảng trống
- Không tìm được benchmark công khai so sánh NLI zero-shot, embedding similarity, SetFit và LLM trên cùng tập tiếng Việt văn bản ngắn. Truy vấn đã thử: "zero-shot classification NLI mDeBERTa xnli versus LLM GPT comparison accuracy text classification benchmark".
- Chưa lấy được số XNLI riêng cho tiếng Việt (huggingface.co bị chặn).

## 5. Độ tin cậy: ổn định nhãn, structured output, drift taxonomy, nhãn bịa

### Kết luận ngắn
LLM gán nhãn không hoàn toàn ổn định giữa các lần chạy và giữa các cách diễn đạt prompt; khuyến nghị đo bằng chạy lặp (≥3 lần) và biến thể prompt, dùng structured output có enum để chặn nhãn ngoài taxonomy, giữ mẫu người kiểm và dùng LLM làm evaluator có kiểm chứng (như TnT-LLM, Clio). Mức chắc chắn: **trung bình** (chủ yếu preprint, nhưng nhất quán).

### Phát hiện có nguồn
- Pangakis et al. ("Automated Annotation with Generative AI Requires Validation", 2023): khuyến nghị phân loại mỗi mẫu ít nhất 3 lần ở temperature >0; "consistency score" = tỷ lệ lần chạy trùng nhãn mode; accuracy cao hơn **19,4 điểm phần trăm** với mẫu có consistency 1,0 so với mẫu kém nhất quán hơn — [arXiv 2306.00176](https://arxiv.org/abs/2306.00176) (bậc 1, 2023-06, qua trích đoạn search).
- Prompt Stability Score: đo đồng thuận qua cả lần chạy lặp và các biến thể diễn đạt prompt; ổn định là điều kiện cần nhưng không đủ cho chính xác — [arXiv 2407.02039](https://arxiv.org/abs/2407.02039) (bậc 1, 2024-07, qua trích đoạn search).
- Một nghiên cứu gán nhãn cognitive distortions tránh temperature 0 vì "trivially consistent", dùng 0,5–0,7, báo Fleiss' kappa 0,78 giữa các lần chạy của GPT-4 — [arXiv 2511.01482](https://arxiv.org/abs/2511.01482) (bậc 1, 2025-11, qua trích đoạn search).
- **Structured outputs (Claude):** "guarantee schema-compliant responses through constrained decoding" — luôn là JSON hợp lệ, đúng kiểu và đủ trường bắt buộc; hỗ trợ enum (vd `EnumOf` trong SDK) — [Structured outputs, Claude docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) (bậc 1, truy cập 2026-10-21). Điều này chặn nhãn ngoài danh sách ở mức cú pháp, không đảm bảo nhãn đúng.
- TnT-LLM: GPT-4 làm evaluator đồng ý với đa số người nhiều hơn người đồng ý với nhau ở nhiệm vụ đồng thuận vừa phải — [TnT-LLM](https://arxiv.org/abs/2403.12173) (bậc 1, qua trích đoạn search).
- Clio kiểm tra bằng dữ liệu tổng hợp và thật, đánh giá thủ công (96–97%), so với classifier sẵn có (r = 0,71), bỏ cụm nhỏ dưới ngưỡng — [Clio](https://www.anthropic.com/research/clio), [Clio arXiv](https://arxiv.org/abs/2412.13678) (bậc 1, 2024-12). Privacy auditor bằng LLM của Clio bị Cliopatra (2026) chỉ ra là không phát hiện được cả rò rỉ lớn — [arXiv 2603.09781](https://arxiv.org/abs/2603.09781) (bậc 1, 2026-03, qua trích đoạn search) — bài học: kiểm tra do LLM tự làm cần được kiểm chứng độc lập.
- Miller & Alexander: LLM sinh đồng thuận tốt với người khi đánh giá cụm, nhưng cả hai đều có thiên lệch — [arXiv 2405.07278](https://arxiv.org/abs/2405.07278) (bậc 1, qua trích đoạn search).
- Gộp nhãn trùng nghĩa: "Text clustering as classification" cần bước merge riêng vì LLM sinh nhiều nhãn khác chữ cùng nghĩa (143 → 122 nhãn, ground truth 93) — [arXiv 2410.00927](https://arxiv.org/abs/2410.00927) (bậc 1, qua trích đoạn search). Đây là dạng "taxonomy phình/nhãn trùng" điển hình.
- EvoTaxo (2026) nghiên cứu dựng và tiến hóa taxonomy từ luồng mạng xã hội — liên quan drift — [arXiv 2603.19711](https://arxiv.org/abs/2603.19711) (bậc 1, 2026-03, chỉ thấy tiêu đề trong kết quả search, chưa đọc nội dung).

### Nhận định
- Khuyến nghị kiểm chứng: (1) cố định taxonomy có phiên bản + định nghĩa từng nhãn + nhãn "Khác/không rõ"; (2) structured output với enum + ID dòng; (3) chạy lặp 3 lần trên mẫu kiểm, dùng consistency score làm độ tin cậy, đưa bản ghi kém nhất quán vào hàng người kiểm; (4) mẫu người kiểm vài trăm bản ghi để đo accuracy và hiệu chỉnh tỷ lệ; (5) theo dõi tỷ lệ "Khác" và tỷ lệ độ tin cậy thấp theo thời gian như tín hiệu drift, định kỳ chạy lại bước sinh taxonomy trên phần "Khác".
- Nhãn bịa chủ yếu xảy ra ở bước **sinh** taxonomy (đặt tên cụm vượt quá nội dung ví dụ); nên yêu cầu LLM trích ví dụ minh họa cho từng nhãn và kiểm tra lại bằng cách cho LLM/người gán ngược ví dụ vào nhãn.

### Khoảng trống
- Chưa có nghiên cứu đo độ ổn định nhãn LLM trên tiếng Việt.
- Chưa lấy được khuyến nghị kiểm chứng chi tiết trong phần "lessons" của TnT-LLM (không mở được full text).

## Truy vấn đã chạy
- TnT-LLM text mining at scale taxonomy generation lightweight classifiers (standard)
- Clio privacy-preserving insights real-world AI use (standard)
- TnT-LLM results GPT-4 labels logistic regression embeddings accuracy agreement Bing Copilot cost latency findings (extended)
- Clio Anthropic paper k-means clusters Claude 3 Haiku facet extraction 94% accuracy synthetic multilingual cost per 100,000 conversations (extended)
- ClusterLLM triplet queries cost per dataset $0.6 GPT-3.5 Instructor clustering improvement (extended)
- Large Language Models Enable Few-Shot Clustering Viswanathan keyphrase expansion pairwise constraints results cost (extended)
- k-LLMmeans LLM-based centroids number of LLM calls results compared k-means (extended)
- OpenAI API pricing GPT-5 mini nano per 1M tokens Batch API 50% October 2026 (extended)
- LLooM concept induction Lam CHI 2024 GPT-4 synthesize score concepts cost (extended)
- Gemini Flash-Lite Flash API pricing per million tokens batch October 2026 (extended)
- zero-shot classification NLI mDeBERTa xnli versus LLM GPT comparison accuracy text classification benchmark (extended)
- LLM annotation consistency across runs temperature zero label stability text classification reliability study (extended)
- TnT-LLM taxonomy generation minibatch summarization sample size labels 0.5 human agreement "lessons" practical LLM text mining (extended)
- "Text Clustering as Classification with LLMs" label generation merge classification results LLM calls (extended)
- Knowledge distillation automated annotation LLM-generated training labels supervised classifier performance compared GPT-4 2024 (standard)
- vLLM throughput benchmark Llama 8B H100 output tokens per second offline batch (extended)
- Vietnamese LLM benchmark VMLU Qwen2.5 SeaLLM Vistral comparison (extended)
- Clio paper k-means embedding all-mpnet-base-v2 hierarchy minimum cluster size aggregation threshold privacy auditor (extended)
- IDAS intent discovery abstractive summarization LLM short text clustering results (standard)
- "Human-interpretable clustering of short text using large language models" Miller (standard)
- Trang/README mở trực tiếp: platform.claude.com (pricing, batch-processing, prompt-caching, structured-outputs), anthropic.com/research/clio, microsoft.com (TnT-LLM), GitHub README của ClusterLLM, few-shot-clustering, GoalEx, LLooM, OpenClio, SetFit, vLLM.
