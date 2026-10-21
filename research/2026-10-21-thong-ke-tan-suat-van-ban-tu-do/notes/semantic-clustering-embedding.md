# Gom nhóm theo nghĩa cho văn bản ngắn do người viết (không dùng LLM, dựa trên embedding)

> **Ghi chú về phương pháp thu thập:** trong phiên này `WebFetch` chỉ mở được `github.com` / `raw.githubusercontent.com`; arxiv.org, huggingface.co, aclanthology.org, sbert.net, readthedocs, maartengr.github.io đều lỗi DNS, còn Bash bị proxy chặn (403). Vì vậy:
> - Docs BERTopic, HDBSCAN, sentence-transformers, FlagEmbedding, E5, mteb, STTM được đọc **trực tiếp từ mã nguồn docs trên GitHub** (bậc 1).
> - Số liệu từ paper arXiv (VN-MTEB, survey Qiang et al., paper BERTopic short text) **chỉ lấy được qua snippet của công cụ search**, chưa mở được bản gốc. Những số này được đánh dấu *(qua snippet, chưa đối chiếu bản gốc)*; writer/verifier nên coi là độ tin cậy trung bình.

## 1. Gom theo trùng lặp từ vựng (TF-IDF word/char n-gram + cosine, MinHash/LSH, SimHash)

### Kết luận ngắn
Các kỹ thuật từ vựng đủ tốt để gom bản ghi "gần như giống nhau" (cùng câu, khác chính tả nhỏ, khác số/tên, thêm bớt vài từ) và rất rẻ, nhưng không gom được các câu diễn đạt khác nhau cùng một nghĩa (paraphrase); với văn bản rất ngắn thì MinHash/SimHash còn kém ổn định. Mức chắc chắn: **trung bình–cao** (nguyên lý thì rõ, nhưng nguồn tìm được phần lớn là docs sản phẩm/bài kỹ thuật, không có benchmark riêng cho văn bản ngắn tiếng Việt).

### Phát hiện có nguồn
- MinHash "captures lexical overlap only; it will not detect paraphrases that reuse meaning but not words"; văn bản quá ngắn có tập shingle không ổn định, làm similarity bị thổi phồng hoặc kéo xuống — [MetricGate: MinHash near-duplicate detection](https://metricgate.com/docs/minhash-near-duplicate-detection/) (bậc 3, 2026-06; nội dung qua snippet search)
- SimHash "can underperform on very short texts (headlines, snippets, titles) because the feature set is too small to stabilise the accumulator vector"; gợi ý kết hợp MinHash trên shingle hoặc "embedding-based semantic dedup for paraphrase collapse" — [geosurge.ai: SimHash](https://www.geosurge.ai/corpus/gen-4163/data-deduplication/simhash.html) (bậc 3, không rõ ngày; trang mang tính quảng bá)
- ClickHouse có sẵn hàm `wordShingleMinHash()` / `wordShingleSimHash()` để tính fingerprint ngay trong DB — [OneUptime: How to Use wordShingleMinHash() and wordShingleSimHash() in ClickHouse](https://oneuptime.com/blog/post/2026-03-31-clickhouse-how-to-use-wordshingleminhash-and-wordshinglesimhash-in-clic/markdown) (bậc 3, 2026-03)
- Một dự án so sánh TF-IDF với Sentence-BERT trên ~57.000 README GitHub: TF-IDF đạt điểm số metric tốt hơn nhưng "rely on surface-level tokens", còn BERT + HDBSCAN cho cụm "far more meaningful and coherent" — [HTLinh0604/Programming_Project_Clustering](https://github.com/HTLinh0604/Programming_Project_Clustering) (bậc 3, không rõ ngày; project sinh viên, không bình duyệt)

### Nhận định
- **Nhận định:** Với cột lý do, lớp từ vựng nên đứng **trước** embedding như một bước khử trùng lặp rẻ: chuẩn hóa (lowercase, bỏ dấu câu, che số/ID) rồi gộp exact/near-duplicate bằng char n-gram TF-IDF (vd n=3–5, `analyzer="char_wb"`) + cosine ≥ ~0.8–0.9, hoặc MinHash-LSH khi dữ liệu hàng triệu dòng. Việc này giảm số chuỗi duy nhất cần embed/cluster và gom luôn lỗi chính tả/viết tắt nhẹ. Char n-gram hợp với tiếng Việt vì không cần tách từ và chịu được sai dấu một phần.
- **Nhận định:** Lớp từ vựng thất bại với paraphrase ("khách đổi ý" vs "KH không muốn mua nữa"), với code-mixing (cùng nghĩa nhưng một bản tiếng Anh), và với câu ngắn chung nhiều từ chức năng nhưng khác nghĩa ("không liên lạc được KH" vs "KH không liên lạc lại") — đó là chỗ cần embedding.
- **Nhận định:** Ngưỡng cosine/Jaccard cần chọn bằng cách xem mẫu cặp ở các mức ngưỡng, không có giá trị chuẩn chung.

### Khoảng trống
- Không tìm được benchmark công khai (bậc 1–2) so sánh MinHash/SimHash/char-TF-IDF với embedding trên văn bản *ngắn* hoặc tiếng Việt. Truy vấn đã thử: "MinHash SimHash short text near-duplicate limitation paraphrase char n-gram TF-IDF fuzzy matching", "short text clustering sentence embeddings benchmark TF-IDF vs SBERT HDBSCAN UMAP evaluation paper".
- Search gợi ý có survey Ahmed et al. 2023 về short text clustering (TF-IDF → transformer, LDA → DBSCAN) qua một luận văn CVUT, nhưng chưa xác minh được trích dẫn — [luận văn CVUT 2024](https://dspace.cvut.cz/bitstream/handle/10467/113511/F3-BP-2024-Sarana-Egor-thesis.pdf) (bậc 3).

## 2. Sentence embedding cho tiếng Việt: model nào, điểm VN-MTEB, kích thước, tốc độ

### Kết luận ngắn
Có benchmark tiếng Việt chuẩn là **VN-MTEB** (41 dataset, 6 task, trong đó 5 dataset clustering; đã tích hợp vào thư viện `mteb` dưới tên `VN-MTEB (vie, v1)`). Theo snippet bảng kết quả: model lớn dùng RoPE (gte-Qwen2-7B-instruct ~53.2 clustering) và `multilingual-e5-large-instruct` (~53.0) dẫn đầu clustering; `bge-m3` (~45.9) và `multilingual-e5-large` (~45.8) thấp hơn rõ. Model chuyên tiếng Việt (AITeamVN/Vietnamese_Embedding, dangvantuan/vietnamese-embedding, halong_embedding) chủ yếu được tối ưu và báo cáo cho **retrieval**, không có số clustering công khai tìm được. Mức chắc chắn: **trung bình** (số VN-MTEB chỉ đến qua snippet, chưa mở được PDF; số của model chuyên tiếng Việt là bên thứ ba).

### Phát hiện có nguồn
**VN-MTEB**
- VN-MTEB (Pham, Luu, Vo, Nguyen, Hoang — GreenNode AI & ĐHQG-HCM), arXiv 2507.21500 (2025-07), đăng ở Findings of EACL 2026; 41 dataset, 6 task (retrieval, reranking, classification, clustering, pair classification, STS); dữ liệu dịch tự động từ MTEB tiếng Anh bằng LLM + lọc bằng embedding, giữ nguyên named entity và code; kết luận chính: model lớn dùng Rotary Positional Embedding vượt model dùng Absolute Positional Embedding — [VN-MTEB (arXiv)](https://arxiv.org/html/2507.21500v1) (bậc 1, 2025-07; *qua snippet*) và [ACL Anthology 2026.findings-eacl.86](https://preview.aclanthology.org/ingest-eacl/2026.findings-eacl.86.pdf) (bậc 1, 2026)
- Trong thư viện `mteb`, benchmark được định nghĩa là `"VN-MTEB (vie, v1)"` với 5 task clustering: `TwentyNewsgroupsClustering-VN`, `RedditClusteringP2P-VN`, `StackExchangeClusteringP2P-VN`, `StackExchangeClustering-VN`, `RedditClustering-VN` — [mteb/benchmarks.py](https://raw.githubusercontent.com/embeddings-benchmark/mteb/main/mteb/benchmarks/benchmarks/benchmarks.py) (bậc 1, đọc 2026-10)
- Điểm clustering trung bình VN-MTEB (5 dataset): gte-Qwen2-7B-instruct **53.15**; multilingual-e5-large-instruct **52.96**; gte-multilingual-base **50.25**; gte-Qwen2-1.5B-instruct **47.64**; bge-m3 **45.90**; multilingual-e5-large **45.78** — [VN-MTEB (arXiv)](https://arxiv.org/html/2507.21500) (bậc 1, 2025; *qua snippet, chưa đối chiếu bản gốc; bảng có dòng đánh dấu `*` chưa rõ nghĩa*)
- Riêng `RedditClustering-VN`: m-e5-large-instruct 49.06, bge-m3 43.25, m-e5-large 42.12 — cùng nguồn (bậc 1; *qua snippet, công cụ search cảnh báo bảng trích xuất có ô bị lỗi*)
- Lưu ý: các dataset clustering của VN-MTEB là tiêu đề/bài Reddit, StackExchange, 20 Newsgroups dịch sang tiếng Việt — tức văn bản tiếng Việt "dịch máy", không phải văn bản người Việt gõ tay có viết tắt/không dấu — suy ra từ tên task trong [mteb/benchmarks.py](https://raw.githubusercontent.com/embeddings-benchmark/mteb/main/mteb/benchmarks/benchmarks/benchmarks.py) và mô tả phương pháp dịch của paper.

**Model đa ngữ**
- multilingual-e5: small 12 layer / 384 chiều, base 12 layer / 768 chiều, large 24 layer / 1024 chiều, large-instruct 24 layer / 1024 chiều; BEIR lần lượt 46.6 / 48.9 / 51.4 / 52.5 — [microsoft/unilm e5 README](https://raw.githubusercontent.com/microsoft/unilm/master/e5/README.md) (bậc 1, đọc 2026-10)
- Technical report Multilingual E5 (arXiv 2402.05672, 2024-02): 3 cỡ small/base/large, tiền huấn luyện contrastive trên ~1 tỷ cặp văn bản đa ngữ rồi fine-tune — [arXiv 2402.05672](https://arxiv.org/abs/2402.05672v1) (bậc 1, 2024-02; *qua snippet*). Kích thước tham số: small ~118M ([PromptLayer](https://www.promptlayer.com/models/sentence-transformers-multilingual-e5-small), bậc 3), large ~560M ([Superlinked E5 guide](https://superlinked.com/blog/e5-embedding-family-guide), bậc 3); base ~278M chưa xác minh.
- Với E5 không-instruct, cho task đối xứng như similarity và clustering dùng tiền tố `query: ` cho mọi câu — [Superlinked E5 guide](https://superlinked.com/blog/e5-embedding-family-guide) (bậc 3, *qua snippet*; nhất quán với model card nhưng chưa mở được model card)
- BGE-M3: dòng XLM-RoBERTa mở rộng max_length lên 8192, hỗ trợ >100 ngôn ngữ, cho cả dense/sparse/multi-vector, "no longer requires adding instructions to the queries"; `use_fp16=True` tăng tốc với "slight performance degradation"; giảm `max_length` để encode nhanh hơn — [FlagEmbedding BGE_M3 README](https://raw.githubusercontent.com/FlagOpen/FlagEmbedding/master/research/BGE_M3/README.md) (bậc 1, đọc 2026-10)
- `paraphrase-multilingual-MiniLM-L12-v2` và `paraphrase-multilingual-mpnet-base-v2`: bản đa ngữ huấn luyện trên dữ liệu song ngữ cho 50+ ngôn ngữ, danh sách có `vi`; LaBSE (109 ngôn ngữ) là "best choice for bitext mining" nhưng kém tin cậy hơn cho similarity giữa các câu không phải bản dịch của nhau; `distiluse-base-multilingual-cased-v1` (15 ngôn ngữ) **không** có tiếng Việt — [sentence-transformers pretrained_models.md](https://raw.githubusercontent.com/UKPLab/sentence-transformers/master/docs/sentence_transformer/pretrained_models.md) (bậc 1, đọc 2026-10)
- FAQ BERTopic: `paraphrase-multilingual-MiniLM-L12-v2` "has shown great performance" cho tài liệu đa ngữ, muốn chất lượng cao hơn thì dùng `paraphrase-multilingual-mpnet-base-v2`; tác giả thừa nhận "there is not a definitive list of the best models for each language" — [BERTopic FAQ](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/faq.md) (bậc 1, đọc 2026-10)
- Bản ONNX của paraphrase-multilingual-MiniLM-L12-v2: 384 chiều, max seq length 128 — [LightEmbed ONNX](https://huggingface.co/LightEmbed/sbert-paraphrase-multilingual-MiniLM-L12-v2-onnx) (bậc 3, *qua snippet*)

**Model chuyên tiếng Việt**
- AITeamVN/Vietnamese_Embedding: fine-tune từ BGE-M3 trên ~300.000 triplet (query, positive, negative) tiếng Việt; 1024 chiều; max seq 2048; có bản v2 và reranker huấn luyện trên 1,1 triệu triplet — [AITeamVN model data (HF Space mirror)](https://huggingface.co/spaces/shayan5422/back_rag_huggingface/blob/main/model_data_json/AITeamVN_Vietnamese_Embedding.json) (bậc 3, *qua snippet*)
- Bảng retrieval của bên thứ ba (model card huyydangg/DEk21_hcmute_embedding): AITeamVN/Vietnamese_Embedding dense ~0.833 (cột trung bình), dangvantuan/vietnamese-embedding ~0.719, hiieu/halong_embedding dense ~0.652 (hybrid ~0.732) — [DEk21_hcmute_embedding commit](https://www.huggingface.co/huyydangg/DEk21_hcmute_embedding/commit/e8a10c849d5f9fb21441285f5a031d6b8d0ca802) (bậc 3, *qua snippet*; là retrieval trên dữ liệu riêng, không phải clustering)
- dangvantuan/vietnamese-embedding: dựa trên PhoBERT (RoBERTa), 768 chiều; trang listing nêu ~84.87% trên STSB nhưng chi tiết context window giữa các nguồn không khớp — [PromptLayer: vietnamese-embedding](https://www.promptlayer.com/models/vietnamese-embedding) (bậc 3, *qua snippet*)
- Paper VN-MTEB có so cả `sup-SimCSE-VN` (PhoBERT-based) nhưng snippet không cho số clustering của nó — [VN-MTEB](https://arxiv.org/pdf/2507.21500) (bậc 1, *qua snippet*)

**Tốc độ**
- Không tìm được benchmark bậc 1–2 về sentences/sec trên CPU cho các model trên. Docs sentence-transformers chỉ nói `all-MiniLM-L6-v2` "about 5 times faster" so với `all-mpnet-base-v2` (model tiếng Anh) — [pretrained_models.md](https://raw.githubusercontent.com/UKPLab/sentence-transformers/master/docs/sentence_transformer/pretrained_models.md) (bậc 1). Một tài liệu thứ cấp nêu 500–800 docs/giây trên GPU cho MiniLM-L12 đa ngữ, chưa kiểm chứng — [folder-mcp embedding research](https://glama.ai/mcp/servers/@okets/folder-mcp/blob/d01bb52143b8721e59eae8d588a80c2dd8391cc9/docs/features/embedding-models-research.md) (bậc 3).

### Nhận định
- **Nhận định:** Cho bài toán gom văn bản ngắn tiếng Việt lẫn tiếng Anh, chạy on-prem, lựa chọn hợp lý theo thứ tự chất lượng/chi phí: (1) `multilingual-e5-large-instruct` (~560M, 1024 chiều) — điểm clustering VN-MTEB cao nhất trong nhóm model vừa phải, chạy được trên 1 GPU tầm trung; (2) `bge-m3` hoặc AITeamVN/Vietnamese_Embedding khi đã dùng chúng cho retrieval (một model cho cả hai việc), nhưng clustering VN-MTEB kém hơn ~7 điểm; (3) `multilingual-e5-small` / `paraphrase-multilingual-MiniLM-L12-v2` (~118M, 384 chiều) khi cần chạy CPU. Model 7B (gte-Qwen2-7B) chỉ hơn e5-large-instruct ~0.2 điểm clustering mà đắt hơn hơn 10 lần — không đáng cho bài toán này.
- **Nhận định:** Model đa ngữ chung không gian embedding cho tiếng Việt và tiếng Anh, nên câu tiếng Anh và tiếng Việt cùng nghĩa có thể rơi cùng cụm — đây là lợi thế lớn so với model chỉ tiếng Việt (PhoBERT-based) khi dữ liệu code-mixing.
- **Nhận định:** Vì văn bản ngắn (vài từ – vài câu), có thể đặt `max_seq_length` 64–128 để tăng tốc đáng kể; với văn bản ngắn, độ dài chuỗi gần như quyết định throughput. Throughput thực phải tự đo trên phần cứng của mình (batch size, ONNX/int8, fp16); sau bước khử trùng lặp (mục 1) số chuỗi cần embed thường giảm mạnh nên embedding hiếm khi là nút cổ chai ở quy mô vài triệu dòng.
- **Nhận định:** Điểm VN-MTEB đo trên văn bản dịch máy, sạch, có dấu; thứ hạng có thể khác trên văn bản gõ tay có viết tắt/không dấu. Nên tự dựng một bộ kiểm nhỏ (vài trăm cặp/nhóm gán tay từ chính dữ liệu) để chọn model.

### Khoảng trống
- Chưa mở được bảng kết quả gốc VN-MTEB (arXiv/ACL Anthology bị chặn trong phiên) — chưa có số clustering cho multilingual-e5-small/base, paraphrase-multilingual-*, LaBSE, sup-SimCSE-VN, AITeamVN, halong. Truy vấn đã thử: "VN-MTEB clustering results multilingual-e5-large bge-m3 table", "\"VN-MTEB\" clustering average multilingual-e5 gte-Qwen2 bge-m3 scores". Có thể lấy được bằng cách chạy `mteb` hoặc xem tab "Vietnamese" trên MTEB leaderboard.
- Không có số sentences/sec trên CPU từ nguồn bậc 1–2.
- Không xác minh được bài "Systematic Evaluation of Modern Text Embeddings for Large-Scale Vietnamese News Clustering: E5-Large, BGE-M3, and SimCSE" (ResearchGate) — theo snippet: E5-Large + GMM tốt nhất trên metric có nhãn, BGE-M3 + K-Means có silhouette cao nhất — [ResearchGate](https://www.researchgate.net/publication/403388005_Systematic_Evaluation_of_Modern_Text_Embeddings_for_Large-_Scale_Vietnamese_News_Clustering_E5-Large_BGE-M3_and_SimCSE) (bậc 3 cho đến khi đọc được bản gốc).

## 3. Thuật toán gom cụm trên embedding (HDBSCAN, UMAP, agglomerative, k-means, community detection)

### Kết luận ngắn
Không có thuật toán "tốt nhất"; với mục tiêu đếm tần suất, khác biệt quan trọng là **cách xử lý điểm không thuộc cụm nào**: HDBSCAN tự chọn số cụm và trả về nhãn nhiễu -1 (có thể chiếm phần lớn với văn bản ngắn), k-means ép mọi điểm vào cụm nhưng phải chọn k, agglomerative với ngưỡng khoảng cách chỉ chạy được vài nghìn câu, còn `community_detection` của sentence-transformers rất nhanh (50k câu < 5 giây) và điều khiển bằng ngưỡng cosine dễ hiểu. Mức chắc chắn: **cao** cho đặc tính thuật toán (docs bậc 1), **trung bình** cho tỷ lệ nhiễu trên văn bản ngắn.

### Phát hiện có nguồn
- k-means: "requires that the number of clusters is specified beforehand" và cho các nhóm "of about equal size" — [sentence-transformers clustering README](https://raw.githubusercontent.com/UKPLab/sentence-transformers/master/examples/sentence_transformer/applications/clustering/README.md) (bậc 1, đọc 2026-10)
- Agglomerative với threshold: dùng khi không biết số cụm, ngưỡng điều khiển độ mịn ("many small and fine-grained clusters or few coarse-grained clusters"), nhưng "quite slow, so it is only applicable for maybe a few thousand sentences" — cùng nguồn (bậc 1)
- Fast clustering / community detection (`util.community_detection`): tìm "local community" = tập câu rất giống nhau, tham số ngưỡng cosine và kích thước cộng đồng tối thiểu; "tuned for large datasets (50k sentences in less than 5 seconds)" — cùng nguồn (bậc 1)
- BERTopic mặc định dùng UMAP `n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine'`; UMAP ngẫu nhiên giữa các lần chạy, đặt `random_state` để tái lập; số topic điều khiển qua `min_cluster_size` của HDBSCAN ("A higher `min_cluster_size` will generate fewer topics") thay vì `nr_topics` — [BERTopic best practices](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/best_practices/best_practices.md) (bậc 1, đọc 2026-10)
- Số điểm bị coi là nhiễu do `min_samples` của HDBSCAN quyết định, giảm nó để ít nhiễu hơn; thay HDBSCAN bằng k-means thì "does not produce any outliers at all"; đặt `random_state` cho UMAP thì tái lập được nhưng "at the expense of performance" — [BERTopic FAQ](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/faq.md) (bậc 1)
- Trên văn bản ngắn đa miền, HDBSCAN xếp **phần lớn** tài liệu là outlier; thay bằng k-means cho hiệu năng tương đương mà không để tài liệu nào bị bỏ ngoài — [Experiments on Generalizability of BERTopic on Multi-Domain Short Text (arXiv 2212.08459)](https://arxiv.org/pdf/2212.08459) (bậc 1, 2022-12; *qua snippet*)
- Ví dụ thực nghiệm: SBERT + UMAP + HDBSCAN trên 12.211 tiêu đề sách, cấu hình tốt nhất silhouette 0.6289 với **31% điểm nhiễu** — [Penerapan UMAP dan HDBSCAN ... Judul Buku (JINACS)](https://ejournal.unesa.ac.id/index.php/jinacs/article/view/82679) (bậc 2, ~2025; *qua snippet*)

### Nhận định
- **Nhận định:** Cho mục tiêu đếm tần suất "lý do", nhiễu -1 là con dao hai lưỡi: tỷ lệ nhiễu cao (30% đến >50% trên văn bản ngắn) làm phân phối tần suất thiếu một phần lớn dữ liệu, nhưng ép tất cả vào cụm (k-means, `reduce_outliers`) thì làm phồng các cụm lớn bằng bản ghi không thuộc về chúng. Cách thực tế: dùng HDBSCAN (hoặc community detection) để *khám phá* cụm, báo cáo rõ tỷ lệ "chưa xếp được", rồi gán lại outlier vào centroid gần nhất **chỉ khi** cosine vượt ngưỡng; phần còn lại giữ là "khác".
- **Nhận định:** UMAP trước HDBSCAN là cần thiết vì mật độ trên 384–1024 chiều kém ý nghĩa; nhưng UMAP thêm ngẫu nhiên và chi phí (đáng kể ở hàng triệu điểm, có thể tăng tốc bằng cuML GPU). Với `community_detection`, không cần UMAP vì làm việc trực tiếp trên cosine.
- **Nhận định:** Nên cluster trên **tập chuỗi duy nhất có trọng số** (sau chuẩn hóa/khử trùng lặp) rồi nhân tần suất ngược lại, nhưng lưu ý HDBSCAN/k-means coi mỗi điểm một phiếu — nếu cần, lặp chuỗi hoặc dùng `sample_weight` (k-means của scikit-learn hỗ trợ). Đây là suy luận, chưa có nguồn.
- **Nhận định:** Chọn k cho k-means: quét k và xem silhouette/độ tách, hoặc chọn k lớn (over-cluster, vd 100–300) rồi gộp cụm theo khoảng cách centroid/phân cấp — thường dễ dùng hơn tìm k "đúng".

### Khoảng trống
- Chưa có số đo chuẩn về tỷ lệ nhiễu của HDBSCAN theo `min_cluster_size`/`min_samples` trên văn bản ngắn tiếng Việt.
- Chưa đọc được tên tham số chính xác của `util.community_detection` từ docs (README chỉ mô tả khái niệm; theo code là `threshold` và `min_community_size`, chưa xác minh trực tiếp trong phiên).

## 4. BERTopic và topic model cho văn bản ngắn (GSDMM, BTM, LDA)

### Kết luận ngắn
BERTopic = embedding → UMAP → HDBSCAN → c-TF-IDF (biểu diễn chủ đề), kèm công cụ giảm outlier, phân cấp, online, zero-shot/guided và gắn nhãn bằng LLM (một prompt mỗi chủ đề). Đây là "khung" tiện nhất để đóng gói pipeline, nhưng với văn bản ngắn vấn đề chính là tỷ lệ outlier cao. Topic model xác suất kiểu LDA yếu trên văn bản ngắn vì thiếu đồng xuất hiện từ; GSDMM/BTM ra đời để khắc phục nhưng là mô hình bag-of-words, không hiểu paraphrase/đa ngữ như embedding. Mức chắc chắn: **cao** cho BERTopic (docs bậc 1), **trung bình** cho so sánh GSDMM/BTM/LDA (chưa mở được bảng kết quả survey).

### Phát hiện có nguồn
**Pipeline & outlier**
- `reduce_outliers(docs, topics)` có các chiến lược: c-TF-IDF (mặc định), `probabilities` (cần `calculate_probabilities=True`), `distributions` (dùng `approximate_distribution`), `embeddings` (cosine giữa embedding tài liệu và embedding chủ đề), và có thể **chain** (c-TF-IDF trước, rồi distributions cho phần còn lại); tham số `threshold` đặt độ giống tối thiểu (ví dụ 0.1 cho c-TF-IDF, 0.05 cho probabilities); hàm **không** tự cập nhật topic, phải gọi `.update_topics`; cập nhật như vậy "may lead to errors if topic reduction or topic merging techniques are used afterwards" — [BERTopic outlier reduction](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/outlier_reduction/outlier_reduction.md) (bậc 1, đọc 2026-10)
- FAQ cảnh báo giảm outlier "might force outliers to be put into topics where they do not belong" — [BERTopic FAQ](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/faq.md) (bậc 1)
- Quá nhiều topic: tăng `min_topic_size` "much higher (e.g., 300)", tăng `n_neighbors` của UMAP, hoặc `nr_topics="auto"`; "a few hundred topics at most" là đủ để diễn giải; tính probabilities chỉ thực tế với "less than a couple of hundred thousand documents"; xử lý "millions of documents is quite computationally expensive"; có thể tăng tốc UMAP/HDBSCAN bằng cuML GPU, dùng `low_memory=True` — [BERTopic FAQ](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/faq.md) (bậc 1)
- `CountVectorizer` mặc định tách theo khoảng trắng — với tiếng Trung phải tự cấp tokenizer (jieba) — cùng nguồn (bậc 1). Biểu diễn c-TF-IDF chạy **sau** clustering nên không ảnh hưởng hình thành cụm; khuyến nghị `min_df=2`, `ngram_range=(1, 2)`, bỏ stopword — [BERTopic best practices](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/best_practices/best_practices.md) (bậc 1)
- Biểu diễn bổ sung: KeyBERTInspired, PartOfSpeech, MaximalMarginalRelevance (`diversity=0.3`), nhãn OpenAI (`gpt-4o-mini`); `set_topic_labels` để đặt nhãn tay; `visualize_hierarchy()` cho phân cấp chủ đề — cùng nguồn (bậc 1)

**Online / incremental**
- `.partial_fit` với IncrementalPCA (`n_components=5`), MiniBatchKMeans (vd `n_clusters=50`), `OnlineCountVectorizer` (`decay`, `delete_min_df`), hoặc River DBSTREAM để phát hiện cụm mới; giới hạn: không dùng được `.partial_fit` sau `.fit`, "Only the most recent batch of documents is tracked"; phương án thay thế: `merge_models` — train model mới trên dữ liệu mới rồi gộp để xem có chủ đề mới, giữ nguyên UMAP/HDBSCAN gốc, tác giả nói cách này "often performs better" — [BERTopic online](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/online/online.md) (bậc 1)

**Zero-shot**
- `zeroshot_topic_list` + `zeroshot_min_similarity` (ví dụ `.85`): tài liệu có cosine với nhãn định sẵn vượt ngưỡng được gán nhãn đó, còn lại "will follow the regular BERTopic pipeline" để tìm chủ đề mới; ngưỡng phải thử vì mỗi embedding model có phân phối similarity khác nhau — [BERTopic zero-shot](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/zeroshot/zeroshot.md) (bậc 1)

**Gắn nhãn bằng LLM (chỉ phần tích hợp)**
- Backend: OpenAI, 🤗 Transformers `TextGeneration`, llama.cpp `LlamaCPP`, LangChain, Cohere, LiteLLM, Ollama (qua client tương thích OpenAI); LLM nhận keyword c-TF-IDF + một ít tài liệu đại diện mỗi chủ đề (`nr_docs` mặc định 4, `diversity`, `doc_length`); "we can describe a topic with only a few documents" nên không cần nhiều credit API — [BERTopic LLM representation](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/representation/llm.md) (bậc 1). Docs không nói rõ số lần gọi; suy ra là một prompt mỗi chủ đề.

**Short-text topic models**
- Survey "Short Text Topic Modeling Techniques, Applications, and Performance" (Qiang, Qian, Li, Yuan, Wu; arXiv 1904.07695, 2019): chia ba họ — Dirichlet multinomial mixture (DMM/GSDMM), global word co-occurrence (BTM, WNTM), self-aggregation (PTM, SATM); LDA/PLSA dựa trên đồng xuất hiện từ trong tài liệu "cannot solve this problem very well on short texts" — [arXiv 1904.07695](https://arxiv.org/pdf/1904.07695) (bậc 1, 2019; *qua snippet*)
- Thư viện STTM (Java) đi kèm survey: DMM, BTM, WNTM, PTM, SATM, ETM, GPU-DMM, GPU-PDMM, LF-DMM + LDA, LF-LDA; 6 dataset (SearchSnippets 12.295 docs/8 lớp, StackOverflow 16.407/20, Biomedical 19.448/20, Tweet 2.472/89, GoogleNews 11.109/152, Pascal_Flickr 4.834/20); đánh giá bằng PMI coherence, purity/NMI, độ chính xác SVM — [STTM README](https://raw.githubusercontent.com/qiang2100/STTM/master/README.md) (bậc 1, đọc 2026-10)
- Weisser et al. 2023 (Computational Statistics) trên tweet COVID-19: GSDMM và Gamma-Poisson mixture "may generate better topics than the standard LDA model"; coherence chuẩn "perform poorly as an evaluation metric" — nêu qua snippet search, chưa có URL gốc mở được (xem Khoảng trống).

### Nhận định
- **Nhận định:** Với cột lý do ngắn, BERTopic hợp làm **công cụ khám phá** (gợi ý cụm, keyword, phân cấp, nhãn LLM rẻ vì một prompt/cụm), còn bảng tần suất cuối cùng nên dựa trên một taxonomy đã được người duyệt (có thể khởi tạo từ BERTopic rồi chuyển sang zero-shot topic list hoặc nearest-centroid). Zero-shot topic modeling của BERTopic chính là cơ chế "đã biết thì gán, chưa biết thì cluster tiếp" — rất khớp với dữ liệu đến liên tục.
- **Nhận định:** Với tiếng Việt, cần thay tokenizer của `CountVectorizer` (tách từ bằng underthesea/pyvi/VnCoreNLP hoặc dùng `ngram_range=(1,3)` trên âm tiết) và tự cấp danh sách stopword tiếng Việt, nếu không keyword c-TF-IDF sẽ là các âm tiết rời rạc kém nghĩa. Bước này chỉ ảnh hưởng nhãn, không ảnh hưởng cụm.
- **Nhận định:** GSDMM/BTM nhanh, không cần GPU, nhưng không gom được đồng nghĩa/đa ngữ và phụ thuộc nặng vào tiền xử lý từ vựng; với tiếng Việt viết tắt/không dấu sẽ kém hơn embedding. Chỉ nên cân nhắc khi không thể chạy model embedding.

### Khoảng trống
- Chưa mở được bảng kết quả survey Qiang et al. để nói GSDMM hay BTM tốt hơn trên từng dataset. Truy vấn đã thử: "Short Text Topic Modeling survey Qiang GSDMM BTM benchmark", "Qiang short text topic modeling survey results GSDMM best classification accuracy LDA poor sparsity conclusion".
- Chưa đọc trực tiếp paper arXiv 2212.08459 để lấy tỷ lệ outlier cụ thể.
- Chưa tìm được tài liệu BERTopic về guided topic modeling (`seed_topic_list`) trong phiên.

## 5. Tiền xử lý tiếng Việt cho embedding (tách từ, không dấu, code-mixing)

### Kết luận ngắn
Model dựa trên PhoBERT **bắt buộc** tách từ (RDRSegmenter của VnCoreNLP) trước khi đưa vào; model đa ngữ (e5, bge-m3, paraphrase-multilingual, LaBSE) dùng tokenizer SentencePiece/WordPiece nên đưa thẳng văn bản thô. Chưa có nghiên cứu công khai đo độ bền của embedding với tiếng Việt không dấu. Mức chắc chắn: **cao** cho yêu cầu tách từ của PhoBERT, **thấp** cho vấn đề không dấu.

### Phát hiện có nguồn
- Model card PhoBERT: phải áp dụng word segmenter để tạo văn bản đã tách từ trước khi đưa vào PhoBERT; vì PhoBERT dùng RDRSegmenter của VnCoreNLP khi tiền xử lý dữ liệu pretrain nên khuyên dùng đúng segmenter đó; ví dụ đầu vào `'Chúng_tôi là những nghiên_cứu_viên .'` qua `py_vncorenlp` — [vinai/phobert-base-v2](https://huggingface.co/vinai/phobert-base-v2) (bậc 1, *qua snippet*) và [PhoBERT paper (arXiv 2003.00744)](https://ar5iv.arxiv.org/html/2003.00744) (bậc 1, 2020; *qua snippet*)
- Hầu hết nghiên cứu tiếng Việt tập trung vào văn bản có dấu, trang trọng; văn bản không dấu dễ gây hiểu sai vì các từ đồng tự (homograph) không phân biệt được nếu thiếu ngữ cảnh; Transformer thường được fine-tune trên tiếng Việt sạch — [Using transformer-based models for Vietnamese language detection (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12904414/) (bậc 1, 2026; *qua snippet*)
- Khôi phục dấu (diacritic restoration) bằng Transformer seq2seq vượt BiLSTM-CRF — [ICTU repository 247.pdf](https://repository.ictu.edu.vn/wp-content/uploads/2026/05/247.pdf) (bậc 2, 2026-05; *qua snippet*)
- `CountVectorizer` của BERTopic tách theo khoảng trắng, ngôn ngữ đặc thù cần tokenizer riêng — [BERTopic FAQ](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/faq.md) (bậc 1)

### Nhận định
- **Nhận định:** Tiền xử lý tối thiểu cho embedding đa ngữ: chuẩn hóa Unicode NFC (văn bản tiếng Việt hay lẫn dạng tổ hợp NFD), lowercase, gộp khoảng trắng, che tham số (số, mã, ID, email, IP) bằng placeholder để câu cùng mẫu trùng nhau, mở rộng viết tắt phổ biến bằng từ điển (vd "kh"/"KH" → "khách hàng", "ko"/"k" → "không") — từ điển nên xây từ chính dữ liệu (đếm token tần suất cao). Không cần tách từ cho model đa ngữ.
- **Nhận định:** Với dữ liệu lẫn có dấu và không dấu: (a) đo tỷ lệ bản ghi không dấu; (b) nếu đáng kể, hoặc khôi phục dấu bằng model diacritic restoration, hoặc thêm một khóa phụ "bản bỏ dấu" cho bước khử trùng lặp từ vựng (để "khong lien lac duoc" và "không liên lạc được" gộp ngay ở lớp char n-gram). Nên kiểm tra nhanh cosine giữa cặp có dấu/không dấu trên model đã chọn trước khi quyết định.
- **Nhận định:** Code-mixing không cần xử lý riêng nếu dùng model đa ngữ; nếu dùng model chỉ tiếng Việt (PhoBERT-based) thì câu tiếng Anh sẽ bị biểu diễn kém.

### Khoảng trống
- Không tìm được đánh giá công khai về embedding trên tiếng Việt không dấu hay tiếng Việt viết tắt kiểu chat. Truy vấn đã thử: "Vietnamese text without diacritics embedding model robustness \"không dấu\" sentence embedding".
- Chưa xác nhận model card của `keepitreal/vietnamese-sbert` / `dangvantuan/vietnamese-embedding` có yêu cầu tách từ hay không (HF không truy cập được). Vì dựa trên PhoBERT nên rất có thể cần — phải kiểm tra model card trước khi dùng.

## 6. Gán bản ghi mới vào cụm có sẵn

### Kết luận ngắn
Ba cách chính: `hdbscan.approximate_predict` (giữ nguyên cụm, nhanh, điểm không khớp thành -1, không tạo cụm mới), `BERTopic.transform` (embed → UMAP → HDBSCAN predict, hoặc khi lưu bằng safetensors thì so embedding với topic embedding — nhanh hơn nhưng kết quả có thể khác), và nearest-centroid với ngưỡng cosine (đơn giản nhất, không phụ thuộc UMAP). Cả ba đều cần train lại định kỳ để bắt chủ đề mới và drift. Mức chắc chắn: **cao** (docs bậc 1).

### Phát hiện có nguồn
- `approximate_predict` gán nhãn cho điểm mới mà không train lại, "effectively holding a clustering fixed (after a potentially expensive training run)", trả về nhãn + strength; cần `prediction_data=True` khi fit (hoặc gọi `generate_prediction_data` sau); "a very fast operation, even with large datasets"; điểm mới không tạo/tách/gộp cụm, điểm không khớp thành -1; khuyến nghị "cache your data and retrain your model periodically to avoid drift!" — [HDBSCAN prediction tutorial](https://raw.githubusercontent.com/scikit-learn-contrib/hdbscan/master/docs/prediction_tutorial.rst) (bậc 1, đọc 2026-10)
- BERTopic lưu bằng `safetensors` thì model nhỏ, bỏ UMAP/HDBSCAN; khi đó `.transform` dựa vào similarity embedding và "might give different results"; ví dụ của docs: 100 abstract mất 343 ms so với 1,37 s với model gốc — [BERTopic best practices](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/best_practices/best_practices.md) (bậc 1)
- Zero-shot topic list: bản ghi mới có cosine với nhãn định sẵn ≥ `zeroshot_min_similarity` thì được gán, phần còn lại đi vào clustering để tìm chủ đề mới — [BERTopic zero-shot](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/zeroshot/zeroshot.md) (bậc 1)
- Online: `.partial_fit` với MiniBatchKMeans hoặc River DBSTREAM (tạo cụm mới khi dữ liệu đến) hoặc `merge_models` để phát hiện chủ đề mới — [BERTopic online](https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/online/online.md) (bậc 1)

### Nhận định
- **Nhận định:** Kiến trúc gán gần real-time hợp lý: (1) cache theo chuỗi đã chuẩn hóa (exact match → nhãn ngay, không cần embed); (2) chuỗi mới → embed (model nhỏ, seq ngắn, vài ms/câu trên CPU, cần tự đo) → nearest centroid bằng cosine trên index (FAISS/numpy; với vài trăm cụm thì chỉ là một phép nhân ma trận); (3) cosine < ngưỡng → nhãn "chưa xếp" và đưa vào hàng đợi; (4) định kỳ cluster lại hàng đợi "chưa xếp" để tìm cụm mới, người duyệt rồi thêm vào taxonomy. Tỷ lệ "chưa xếp" theo thời gian là tín hiệu drift.
- **Nhận định:** Nearest-centroid ổn định hơn `approximate_predict` khi taxonomy đã được người chỉnh sửa (gộp/tách cụm tay), vì centroid tính lại dễ từ nhãn hiện tại, không phụ thuộc cây HDBSCAN hay UMAP đã fit. Nếu cụm có hình dạng phức tạp, dùng k-NN (bỏ phiếu theo k láng giềng đã gán nhãn) thay vì centroid.
- **Nhận định:** Ngưỡng cosine phụ thuộc model (E5 có phân phối cosine dồn cao, thường 0.7–0.9 với mọi cặp), nên phải hiệu chỉnh bằng mẫu gán tay, không dùng chung một con số giữa các model — phù hợp với cảnh báo của docs BERTopic zero-shot rằng mỗi model có phân phối similarity khác nhau.

### Khoảng trống
- Chưa có số throughput chuẩn của `transform`/`approximate_predict` trên quy mô hàng triệu bản ghi ngoài ví dụ 100 tài liệu của BERTopic.

## Truy vấn đã chạy
- VN-MTEB Vietnamese massive text embedding benchmark arXiv (standard)
- BERTopic short texts outlier reduction reduce_outliers documentation (standard)
- Short Text Topic Modeling survey Qiang GSDMM BTM benchmark (standard)
- github VN-MTEB GreenNode Vietnamese embedding benchmark leaderboard (standard)
- dangvantuan vietnamese-embedding AITeamVN Vietnamese_Embedding halong_embedding benchmark comparison (standard)
- VN-MTEB clustering results multilingual-e5-large bge-m3 table (extended)
- "VN-MTEB" clustering average multilingual-e5 gte-Qwen2 bge-m3 scores (extended)
- PhoBERT word segmentation required VnCoreNLP sentence embedding vietnamese-sbert input (standard)
- short text clustering sentence embeddings benchmark TF-IDF vs SBERT HDBSCAN UMAP evaluation paper (standard)
- Qiang short text topic modeling survey results GSDMM best classification accuracy LDA poor sparsity conclusion (standard)
- MinHash SimHash short text near-duplicate limitation paraphrase char n-gram TF-IDF fuzzy matching (standard)
- multilingual E5 technical report 2402.05672 parameters small 118M base 278M large 560M "query: " prefix clustering (standard)
- Systematic Evaluation Modern Text Embeddings Vietnamese News Clustering E5-Large BGE-M3 SimCSE results (standard)
- Vietnamese text without diacritics embedding model robustness "không dấu" sentence embedding (standard)
- sentence embedding CPU throughput sentences per second multilingual-e5-small paraphrase-multilingual-MiniLM-L12-v2 ONNX benchmark (standard)
- Trang đọc trực tiếp (raw GitHub): BERTopic docs (outlier_reduction, best_practices, online, zeroshot, llm, faq), HDBSCAN prediction_tutorial.rst, sentence-transformers clustering README + pretrained_models.md, mteb benchmarks.py, microsoft/unilm e5 README, FlagEmbedding BGE_M3 README, STTM README.
