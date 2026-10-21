---
title: Thống kê tần suất có ý nghĩa trên cột văn bản tự do ngắn
date: 2026-10-21
question: Với một cột văn bản ngắn vừa có giá trị máy sinh theo mẫu có tham số, vừa có giá trị người nhập tay (tiếng Việt lẫn tiếng Anh, viết tắt, sai chính tả), nên chuẩn hóa và gom nhóm thế nào để mỗi nhóm là một "lý do" và phân phối tần suất theo nhóm có giá trị thống kê, trong khi giữ latency và chi phí LLM thấp?
tags: [text-clustering, template-mining, sentence-embedding, llm-taxonomy, quantification, tieng-viet]
---

# Che tham số, gom theo nghĩa, chỉ gọi LLM theo cụm

> **Câu hỏi:** Chuẩn hóa và gom nhóm một cột văn bản ngắn (dòng máy sinh lẫn dòng người viết, tiếng Việt lẫn tiếng Anh) thế nào để bảng tần suất theo "lý do" đáng tin, với latency và chi phí LLM thấp? · **Ngày:** 2026-10-21 · **Phạm vi:** phương pháp và công cụ công khai 2019–2026 (phần LLM 2023–2026); dữ liệu vài nghìn đến vài triệu dòng; ưu tiên chạy on-prem nhưng có so với API; ví dụ trung tính (lý do đóng ticket, lý do hủy đơn, ghi chú xử lý). · **Kiểm chứng:** 85 khẳng định đã đối chiếu nguồn, 10 đã sửa

## Tóm tắt

Cách làm đáng chọn là một pipeline xếp tầng theo chi phí: chuẩn hóa Unicode và dấu tiếng Việt, che tham số bằng regex rồi đếm chính xác; dòng máy sinh đi qua template miner kiểu Drain3, dòng người viết đi qua embedding đa ngữ và gom cụm; LLM chỉ được gọi **một lần cho mỗi cụm** (đặt tên, gộp, dựng taxonomy) và trên **một mẫu vài nghìn dòng** để huấn luyện một classifier rẻ; dòng mới được gán bằng cache, template đã học và nearest-centroid có ngưỡng. Lý do chính: số template hay cụm nhỏ hơn số dòng vài bậc độ lớn (Loghub-2.0 có hơn **50 triệu dòng** nhưng chỉ **3.488 template** [1]). Vì vậy gọi LLM theo từng dòng là lãng phí: với giá model nhỏ hiện nay, đặt tên 5.000 cụm tốn dưới **$1** với 5.000 request, còn để LLM phân loại toàn bộ 1 triệu dòng tốn khoảng **$5–88** và cần từ 20.000 đến 1 triệu request tùy cách đóng gói (phép tính theo bảng giá Claude Haiku 5.5) [2]. Bằng chứng rằng LLM không cần chạm vào phần lớn dữ liệu đến từ TnT-LLM: classifier nhẹ học từ nhãn LLM đạt accuracy **0,658**, ngang GPT-4 (**0,655**) (qua search) [3]. Con số tần suất chỉ đáng tin khi đã đối chiếu với vài trăm dòng do người gán, báo rõ tỷ lệ "khác/chưa xếp", và hiệu chỉnh tỷ lệ bằng ma trận nhầm lẫn thay vì đếm thẳng nhãn [4][5]. Kiến trúc và cơ chế có độ chắc chắn cao (docs và README đã mở). Phần lớn số benchmark chỉ có độ chắc chắn trung bình: môi trường nghiên cứu bị chặn arXiv/Hugging Face nên nhiều con số chỉ đọc được **qua trích đoạn search**, và mọi benchmark đều là log tiếng Anh hoặc tiếng Việt dịch máy. Chất lượng thật phải đo trên chính dữ liệu của mình.

**Điểm chính**
- Che tham số bằng regex rồi đếm chính xác đã gom được phần lớn dòng máy sinh. Drain3 gom phần còn lại theo vị trí token, chạy streaming và trả sẵn `size` của mỗi template [6]. Số "accuracy" đo trên tập nhỏ thì quá lạc quan: FGA trung bình của Drain rơi từ 0,74 trên Loghub-2k xuống 0,55 trên Loghub-2.0 [7].
- Parser log và fingerprint không gom được câu diễn đạt khác cùng nghĩa, nên dòng người viết cần embedding đa ngữ. Trên VN-MTEB, multilingual-e5-large-instruct đạt khoảng 53,0 điểm clustering, gần bằng model 7B (53,2) và hơn bge-m3 (45,9) (qua snippet) [8].
- Với văn bản ngắn, HDBSCAN có thể xếp phần lớn dữ liệu vào nhiễu [9], còn ép giảm outlier thì có thể đẩy dòng vào chủ đề không thuộc về nó [10]. Cách an toàn là khám phá cụm trước, gán lại theo ngưỡng cosine, giữ nhãn "chưa xếp" và báo tỷ lệ của nó.
- LLM đáng tiền ở bước đặt tên, gộp cụm và gán nhãn mẫu để distill (TnT-LLM, Clio, k-LLMmeans) [11][12][13]. Batch API giảm 50% giá; trên Haiku 5.5, đọc prompt cache chỉ tính 0,1× giá input [14][2].
- Đếm thẳng nhãn classifier ("classify and count") bị lệch khi phân phối thay đổi. Cần hiệu chỉnh bằng TPR/FPR đo trên tập kiểm và kèm khoảng tin cậy Wilson hoặc Sison-Glaz [15][5][16].
- Uber, Intercom và Zendesk đều chốt một taxonomy rồi gán hằng ngày kèm độ tự tin, chỉ dùng gom cụm để khám phá (qua search) [17][18][19]. Song song với phân tích, nên đưa taxonomy đã khai phá vào form nhập dưới dạng mã lý do kèm ghi chú tự do [20].

## Chuẩn hóa và che tham số xử lý phần máy sinh gần như miễn phí

### Chuẩn hóa tiếng Việt phải đứng trước mọi phép đếm

Hai chuỗi trông giống hệt nhau có thể là hai khóa khác nhau trong bảng tần suất. **Nhận định:** kiểm bằng `unicodedata` của Python 3 (Unicode 15.1.0) cho thấy "Việt" ở dạng NFC dài 4 code point, ở dạng NFD dài 6. Chuẩn hóa NFC cũng **không** thống nhất kiểu bỏ dấu cũ và mới: `NFC("hòa") != NFC("hoà")`. Bỏ dấu bằng cách xóa ký tự loại `Mn` sau NFD vẫn giữ nguyên "đ", nên phải map tay `đ→d`. underthesea có `text_normalize` sửa cả ký tự nhầm lẫn lẫn vị trí dấu: ví dụ chính thức đổi "Ðảm baỏ chất lựơng phòng thí nghịêm hoá học" thành "Đảm bảo chất lượng phòng thí nghiệm hóa học", tức là chuẩn về **kiểu bỏ dấu cũ** ("hóa"). Thư viện còn có `restore_diacritics` để khôi phục dấu cho văn bản gõ không dấu [21]. Văn bản mạng xã hội còn có teencode và viết tắt: corpus ViLexNorm có hơn **10.000 cặp câu**, và hệ tốt nhất chỉ đạt ERR **57,74%** (qua search) [22]. Như vậy chuẩn hóa từ vựng tự động mới xử lý được một phần; với dữ liệu nội bộ, một từ điển viết tắt dựng từ chính các token tần suất cao ("kh" → "khách hàng", "ko" → "không") rẻ hơn và sát hơn.

**Nhận định:** thứ tự cho mỗi giá trị nên là: NFC → sửa ký tự nhầm và vị trí dấu → `casefold` → gộp khoảng trắng, bỏ dấu câu thừa → che tham số → tạo thêm một **khóa không dấu** để gom ứng viên. Bản có dấu được giữ lại để hiển thị. Khóa không dấu gộp nhầm được các từ chỉ khác dấu ("khóa"/"khoa", "chặn"/"chán"), nên chỉ dùng nó làm khóa ứng viên, không làm nhãn cuối.

### Regex masking làm phần lớn công việc, Drain3 gom phần còn lại

Drain3, bản Python streaming của Drain, áp dụng danh sách mask `{regex_pattern, mask_with}` **trước** lõi thuật toán (ví dụ che IPv4 thành `<IP>`, số thành `<NUM>`). Phần biến mà regex không bắt được thì lõi Drain xử lý bằng cây có độ sâu cố định: tầng đầu nhóm theo số token, các tầng sau theo vài token đầu, ở lá so tỷ lệ token giống nhau với ngưỡng `sim_th` (mặc định **0,4**). Mỗi cụm có `cluster_id`, template và `size`, tức là tần suất của template. Trạng thái được snapshot ra Kafka, Redis hoặc file. Thư viện có hai chế độ: `add_log_message()` học và tạo cụm mới, còn `match()` chỉ khớp với cụm đã học và trả `None` nếu không khớp [6]. Theo tài liệu của logparser, độ phức tạp của Drain là O(N) (qua search) [23]. Với ví dụ trong brief, "Đã khóa tài khoản user123" và "Đã khóa tài khoản user456" trùng nhau ngay sau mask thành "đã khóa tài khoản `<id>`", và "Đã chặn IP 10.0.0.5" thành "đã chặn ip `<ip>`". Bước này không cần Drain: `value_counts` trên chuỗi đã mask là đủ.

Benchmark cho thấy Drain là mặc định hợp lý nhưng không phải phép màu. Năm 2019, Zhu và cộng sự đánh giá 13 parser trên 16 dataset và thấy Drain có độ chính xác trung bình cao nhất, phương sai nhỏ nhất, đồng thời khuyên thử nhiều parser trên log của chính mình (qua search) [24]. Loghub-2.0 lớn hơn nhiều: 14 dataset, khoảng **50,4 triệu dòng** gán nhãn, **3.488 template**, so với **1.147 template** của Loghub-2k (tổng cộng từ bảng theo dataset trong README) [1]. Theo bảng kết quả trong repo, FGA trung bình của Drain rơi từ **0,74 xuống 0,55**, và chỉ 6/15 parser (Drain, IPLoM, LFA, LogCluster, UniParser, LogPPT) có thời gian chạy cho cả 14 dataset [7]. Paper nói giới hạn là 12 giờ mỗi dataset, và parser thống kê gom nhóm tốt hơn, còn parser ngữ nghĩa nhận diện tham số tốt hơn (qua search) [25]. Về tốc độ, bảng thời gian của Loghub-2.0 ghi Drain (bản logparser) mất trung bình khoảng **425** đơn vị thời gian mỗi dataset, và **2.492** cho Thunderbird, dataset lớn nhất với khoảng 16,6 triệu dòng [7]. **Nhận định:** bảng không ghi đơn vị; nếu là giây thì Drain parse cả ~50 triệu dòng trong khoảng 1,7 giờ, tức vài nghìn dòng mỗi giây. Tác giả Brain tự báo khoảng **46 giây cho 1 triệu dòng** (qua search) [26]. README của Drain3 không đưa số throughput [6]. **Nhận định:** con số "accuracy > 0,9" trên tập 2.000 dòng không chuyển được sang dữ liệu thật có nhiều template. Danh sách mask (email, URL, IP, UUID, hash, ngày giờ, số, mã kiểu `chữ+số`) quan trọng hơn việc chọn parser, và mask cụ thể phải chạy trước mask chung.

### LLM parser chỉ có lời khi gọi theo template, không theo dòng

Các parser dùng LLM đời mới đều dựa trên một quan sát: số template ít hơn số dòng vài bậc độ lớn. LILAC (FSE 2024) giữ một adaptive parsing cache và chỉ hỏi LLM cho dòng chưa khớp template nào. Tác giả báo số truy vấn giảm "by several orders of magnitude" và hiệu năng tương đương Drain (qua search) [27]. LogBatcher gom các dòng giống nhau rồi hỏi theo batch (mặc định 10 dòng), không cần nhãn, và chạy được với model mở như Llama 3.1 [28]. Paper của LogBatcher chỉ ra rằng riêng phần hướng dẫn đã tốn 66 token, nhiều hơn chính dòng log (55 token), nên gộp nhiều dòng vào một prompt giảm chi phí đáng kể (qua search) [29]. Ngược lại, DivLog gọi LLM **một lần cho mỗi dòng**: chính xác (PA trung bình 98,1% trên Loghub-2k, tác giả tự báo) nhưng tổng số lần gọi rất cao (qua search) [30]. Một so sánh thời gian trên toàn bộ Loghub-2.0 với model mở cho kết quả: LibreLog **5,94 giờ**, LUNAR **10,6 giờ**, LILAC **16 giờ**, LLMParser (T5) **258 giờ**. Lưu ý LibreLog là đối thủ của các hệ còn lại (qua search) [31]. Một đánh giá độc lập cùng setup (paper Matryoshka) cho LILAC **0,90/0,82** và Drain3 **0,89/0,81** trên hai metric chất lượng template, tức gần như ngang nhau; một phiên bản khác của paper lại ghi LILAC 0,95/0,87 (qua search) [32].

**Nhận định:** với kiểu "cache theo template", số lần gọi LLM xấp xỉ số template khác nhau và không phụ thuộc số dòng; với Loghub-2.0, cận trên lý thuyết là khoảng 3.500 lần gọi cho 50 triệu dòng. Với cột lý do ngắn, LLM chỉ đáng dùng cho phần máy sinh khi template chứa biến không có "hình dạng" mà regex bắt được (tên người, tên sản phẩm), và khi đó nên gọi cho từng cụm Drain nhỏ hoặc từng dòng không khớp, theo cách của LILAC và LUNAR [33].

### Tách "máy sinh" và "người viết" bằng chính đầu ra của template miner

Không tìm thấy tài liệu nào đo việc tách dòng template máy sinh khỏi văn bản người nhập trong cùng một cột. Tài liệu "machine-generated text" hiện nay nói về văn bản do LLM viết, không áp dụng được ở đây. Tuy vậy, Drain3 cung cấp đủ tín hiệu để dựng heuristic: `size` của cụm và việc `match()` có khớp chính xác hay không [6]. **Nhận định:** các tín hiệu dưới đây cần hiệu chỉnh ngưỡng trên vài trăm dòng gán tay:

| Tín hiệu | Nghiêng về máy sinh | Nghiêng về người viết |
|---|---|---|
| Support của template sau mask + Drain | cụm lớn (vd ≥ 20 dòng hoặc ≥ 0,1% tổng), có ít nhất một tham số | cụm cỡ 1–2 |
| Phần hằng ở đầu câu | trùng tiền tố của template support cao ("đã khóa tài khoản") | đa dạng |
| Tỷ lệ token bị mask, độ dài | cao, độ dài ổn định trong cụm | thấp; có viết tắt, emoji, độ dài dao động |
| Entropy token theo vị trí | ≈ 0 ở vị trí hằng, cao ở vị trí tham số | cao rải rác ở mọi vị trí |
| Cột phân loại khác (nguồn/loại bản ghi) | nguồn tự động | nguồn nhập tay |

**Nhận định:** không cần tách hoàn hảo. Dòng bị nghi ngờ cứ đưa sang nhánh người viết, vì embedding vẫn gom được dòng máy sinh, chỉ tốn hơn một chút. Tách theo cột nguồn trước khi gom là tín hiệu rẻ nhất.

## Dòng người viết cần embedding đa ngữ; lớp từ vựng chỉ để khử trùng lặp

### Fingerprint và char n-gram gộp được biến thể chính tả, không gộp được paraphrase

OpenRefine tài liệu hóa hai họ kỹ thuật rẻ. **Key collision** gồm fingerprint (lowercase, bỏ dấu câu, ASCII hóa, tách token, **sort và bỏ trùng token**), n-gram fingerprint và phonetic. **Nearest neighbor** gồm Levenshtein và PPM, có blocking để tránh so mọi cặp. Docs xếp fingerprint là phương pháp ít gộp nhầm nhất nên chọn nó làm mặc định, nhưng lưu ý bước ASCII hóa cũng có thể gộp nhầm. PPM thì "very lax" và chỉ nên dùng như "last resort". Thứ tự khuyến nghị là đi từ chặt đến lỏng [34]. **Nhận định:** với tiếng Việt, bước ASCII hóa chính là khóa không dấu, nên chạy fingerprint **có dấu** trước rồi mới đến bản không dấu. Sort token giúp miễn nhiễm với đảo trật tự ("khóa tài khoản" = "tài khoản khóa"), bù một phần cho giới hạn vị trí cố định của Drain. Phonetic của OpenRefine thiết kế cho tiếng Anh và tiếng Đức, vô dụng với tiếng Việt [34]. Char n-gram TF-IDF (vd n = 3–5) cộng cosine hoặc MinHash-LSH cho hàng triệu dòng là cách gộp near-duplicate không cần tách từ. Nhưng cả họ này chỉ thấy trùng lặp bề mặt: "khách đổi ý" và "KH không muốn mua nữa" sẽ không bao giờ chung khóa, và "không liên lạc được KH" với "KH không liên lạc lại" lại dễ bị gộp sai. Đó là chỗ cần embedding.

### Chọn model embedding: e5-large-instruct là điểm cân bằng, nhưng benchmark là văn bản dịch máy

VN-MTEB (Findings of EACL 2026) là benchmark tiếng Việt chuẩn, gồm 41 dataset và 6 task, dữ liệu dịch tự động từ MTEB tiếng Anh bằng LLM rồi lọc. Kết luận chính của paper là model lớn dùng rotary positional embedding vượt model dùng absolute positional embedding (qua snippet) [8]. Benchmark đã có trong thư viện `mteb` dưới tên `VN-MTEB (vie, v1)`, với 5 task clustering đều là Reddit, StackExchange và 20 Newsgroups bản dịch [35]. Như vậy đây là tiếng Việt sạch, có dấu, dịch máy, không phải văn bản gõ tay có viết tắt hay thiếu dấu.

| Model | Cỡ / số chiều | Clustering VN-MTEB (TB 5 dataset, qua snippet) | Ghi chú |
|---|---|---|---|
| gte-Qwen2-7B-instruct | 7B | **53,15** | hơn e5-large-instruct 0,2 điểm, đắt hơn nhiều lần |
| multilingual-e5-large-instruct | 560M, 24 layer, 1024 chiều | **52,96** | lựa chọn chính cho GPU tầm trung |
| gte-multilingual-base | — | 50,25 | |
| bge-m3 | 568M, max_length 8192, dense/sparse/multi-vector | 45,90 | mạnh cho retrieval; một model cho hai việc |
| multilingual-e5-large | 24 layer, 1024 chiều | 45,78 | |
| multilingual-e5-small | 12 layer, 384 chiều | không có số | phương án CPU |

Nguồn: điểm clustering và số tham số từ [8] (qua snippet; ba số 53,15 / 52,96 / 45,90 được hai lần search khớp nhau, hai số còn lại chưa đối chiếu lại); cấu hình e5 từ [36]; bge-m3 từ [37]. Với E5 không-instruct, model card trên Hugging Face hướng dẫn dùng tiền tố `query: ` cho task đối xứng như clustering; README của E5 trên GitHub không nói điều này, và model card chưa mở được. Hai model `paraphrase-multilingual-MiniLM-L12-v2` và `-mpnet-base-v2` có hỗ trợ tiếng Việt; `distiluse-base-multilingual-cased-v1` thì **không**; LaBSE hợp với bitext mining hơn similarity [38]. FAQ BERTopic khen MiniLM đa ngữ nhưng thừa nhận không có danh sách model tốt nhất cho từng ngôn ngữ [10]. Các model chuyên tiếng Việt (AITeamVN/Vietnamese_Embedding, dangvantuan/vietnamese-embedding, halong_embedding) được tối ưu cho retrieval, và không tìm thấy số clustering công khai của chúng. Model nào dựa trên PhoBERT thì **bắt buộc** tách từ bằng RDRSegmenter trước khi encode (qua snippet) [39]. **Nhận định:** model đa ngữ đặt câu tiếng Việt và tiếng Anh cùng nghĩa vào cùng một không gian, nên code-mixing không cần xử lý riêng; đây là lợi thế lớn so với model chỉ tiếng Việt. Vì văn bản ngắn, đặt `max_seq_length` 64–128 sẽ tăng tốc đáng kể. Không có nguồn bậc 1–2 nào cho throughput CPU, nên phải tự đo.

### Thuật toán gom cụm: điểm quyết định là cách xử lý dòng không thuộc cụm nào

| Thuật toán | Số cụm | Dòng lẻ | Quy mô |
|---|---|---|---|
| k-means | phải chọn k; cụm cỡ gần đều [40] | ép vào cụm, không có outlier [10] | lớn; có `sample_weight` |
| Agglomerative + ngưỡng | ngưỡng quyết định độ mịn | tùy ngưỡng | "only applicable for maybe a few thousand sentences" [40] |
| `community_detection` (sentence-transformers) | ngưỡng cosine + cỡ tối thiểu | dòng lẻ không vào cộng đồng nào | "50k sentences in less than 5 seconds" [40] |
| UMAP + HDBSCAN (BERTopic) | tự chọn, điều khiển bằng `min_cluster_size` [41] | nhãn −1, có thể chiếm phần lớn dữ liệu [9] | hàng triệu dòng "quite computationally expensive" [10] |

Trên văn bản ngắn đa miền, HDBSCAN xếp **phần lớn** tài liệu là outlier, trong khi k-means cho hiệu năng tương đương mà không bỏ dòng nào (qua snippet) [9]. Một ví dụ khác trên 12.211 tiêu đề sách cho silhouette 0,6289 với **31% điểm nhiễu** (qua snippet) [42]. BERTopic có `reduce_outliers` với bốn chiến lược và tham số `threshold` để chỉ gán outlier đủ gần [43]. FAQ lưu ý rằng giảm outlier bằng cách hạ `min_samples` của HDBSCAN "might force outliers to be put into topics where they do not belong" [10]. HDBSCAN cũng xuống cấp trên dữ liệu quá khoảng 50–100 chiều, nên phải giảm chiều trước (qua search) [44]. UMAP lại thêm yếu tố ngẫu nhiên giữa các lần chạy [41]. **Nhận định:** với mục tiêu đếm, nên dùng HDBSCAN hoặc `community_detection` để *khám phá*, hoặc over-cluster bằng k-means (100–300 cụm) rồi gộp theo khoảng cách centroid. Sau đó gán outlier vào centroid gần nhất **chỉ khi** cosine vượt ngưỡng, phần còn lại giữ là "chưa xếp" và luôn báo tỷ lệ của nó. Gom trên tập chuỗi duy nhất (sau dedup) rồi nhân lại tần suất sẽ rẻ hơn nhiều so với gom trên dòng thô.

BERTopic tiện làm khung khám phá: embedding → UMAP → HDBSCAN → c-TF-IDF, kèm phân cấp, online, zero-shot và nhãn LLM [41][45]. Vì c-TF-IDF chạy **sau** khi gom, tokenizer chỉ ảnh hưởng keyword chứ không ảnh hưởng cụm. Với tiếng Việt, `CountVectorizer` mặc định tách theo khoảng trắng, nên keyword sẽ là âm tiết rời nếu không thay tokenizer (vd `ngram_range=(1, 3)` trên âm tiết, hoặc tách từ) [10][41]. Tách từ tiếng Việt rẻ: RDRSegmenter đạt F1 **97,90** với khoảng **62k từ/giây** một luồng (qua search) [46]. Topic model xác suất kiểu LDA yếu trên văn bản ngắn vì thiếu đồng xuất hiện từ. GSDMM và BTM ra đời để khắc phục, nhưng vẫn là bag-of-words (qua snippet) [47]. **Nhận định:** GSDMM/BTM không gom được đồng nghĩa hay câu đa ngữ, nên chỉ đáng cân nhắc khi không thể chạy model embedding.

## LLM đáng tiền khi gọi theo cụm hoặc theo mẫu, không theo dòng

### Số lần gọi của mỗi phương pháp quyết định nó có chạy nổi ở quy mô triệu dòng không

| Phương pháp | LLM làm gì | Số lần gọi (N dòng, k cụm) | Bằng chứng chi phí/chất lượng |
|---|---|---|---|
| TnT-LLM (Microsoft, KDD 2024) | sinh taxonomy lặp qua minibatch, gán nhãn mẫu, distill sang LR/MLP trên embedding | theo cỡ mẫu, không theo N | LR 0,658 vs GPT-4 0,655 (intent) [3] |
| Clio (Anthropic, 2024) | trích facet từng bản ghi, đặt tên cụm, dựng phân cấp | 1/bản ghi + 1/cụm | $48,81/100.000 hội thoại [12] |
| ClusterLLM (EMNLP 2023) | trả lời truy vấn bộ ba để fine-tune embedder | ~1.024 cố định | ~$0,6/dataset với gpt-3.5-turbo [48] |
| Few-shot clustering (TACL 2024) | mở rộng keyphrase / ràng buộc cặp / sửa lỗi | keyphrase 1/dòng; ~20K cặp | $2,24 / $42,03 / $12,73 trên OPIEC59k [49] |
| k-LLMmeans (ICLR 2026) | tóm tắt mỗi cụm làm centroid | k mỗi bước | 750 lần gọi trên CLINC [13] |
| Text clustering as classification (2024) | đề xuất nhãn theo batch, gộp, phân loại từng dòng | ∝ N | 143 → 122 nhãn sau gộp (thật: 93) [50] |
| IDAS, LLooM, GoalEx | tóm tắt hoặc chấm từng dòng | ∝ N | — [51][52][53] |

Mọi số trong bảng đều **qua trích đoạn search**, trừ phần mô tả kiến trúc. TnT-LLM hoạt động theo hai pha: LLM tóm tắt một mẫu rồi sinh và tinh chỉnh taxonomy qua các minibatch (200 bản tóm tắt mỗi vòng); sau đó LLM gán nhãn một mẫu để huấn luyện classifier nhẹ dùng ở quy mô lớn [11][54]. Clio trích facet, gom cụm, cho LLM đặt tên và mô tả, rồi dựng phân cấp khoảng 10/100/1.000 cụm. Trong chi phí $48,81 cho 100.000 hội thoại (giả định 1.000 token mỗi hội thoại), khoảng $45 là bước trích facet theo từng bản ghi bằng Claude 3 Haiku, chỉ **$3,75** là bước đặt tên cụm [12]. k-LLMmeans đạt 76,0 ACC / 92,1 NMI trên CLINC với 750 lần gọi, thấp hơn ClusterLLM (83,8 / 94,0, 1.618 lần gọi). Tác giả tự nói phương pháp không nhằm vượt các hệ phức tạp hơn; số so sánh lấy từ một bài review [13]. Bản mã nguồn mở OpenClio chạy toàn bộ quy trình Clio on-prem với Qwen3-8B qua vLLM và `all-mpnet-base-v2` [55].

**Nhận định:** với văn bản chỉ dài vài từ đến vài câu, bước "tóm tắt/trích facet" của TnT-LLM và Clio gần như thừa, vì văn bản đã ngắn hơn bản tóm tắt. Bỏ được bước này thì phần đắt nhất của Clio biến mất. Mọi phương pháp có số gọi ∝ N chỉ nên chạy trên **giá trị duy nhất sau chuẩn hóa/template**, không chạy trên dòng thô.

### Theo giá 2026-10, chi phí tiền không còn là rào cản; số request và rate limit mới là chênh lệch lớn

Bảng giá Claude (truy cập 2026-10-21): Haiku 5.5 có giá **$0,10 input / $0,50 output** mỗi triệu token (prompt đến 100.000 token), đọc cache **$0,01**, batch **$0,05 / $0,25** [2]. Prompt caching tính **0,1×** giá input khi đọc cache, **1,25×** khi ghi cache 5 phút, và cộng dồn với chiết khấu batch [2]. Prompt tối thiểu để cache trên Haiku 5.5 là **512 token** [56]. Message Batches API giảm **50%**, nhận tối đa **100.000 request** hoặc **256 MB** mỗi batch, đa số xong trong 1 giờ, hạn chót 24 giờ [14]. **Nhận định:** các phép tính dưới đây giả định mỗi giá trị khoảng 30 token, system prompt chứa taxonomy khoảng 800 token, output khoảng 10 token mỗi dòng, N = 1 triệu dòng, giá Haiku 5.5:

| Kịch bản | Số request | Chi phí thường | Chi phí batch |
|---|---|---|---|
| A. 1 dòng/lần gọi, không cache | 1.000.000 | ~$88 | ~$44 |
| B. 1 dòng/lần gọi, cache taxonomy | 1.000.000 | ~$16 | ~$8 |
| C. 50 dòng/lần gọi | 20.000 | ~$10 | ~$5 |
| D. Theo cụm: 5.000 cụm × 20 ví dụ, đặt tên | 5.000 | < $1 | < $0,5 |
| E. Gán nhãn mẫu 5.000 dòng để distill (cách C) | 100 | ~$0,05 | — |

**Nhận định:** chênh lệch thật nằm ở latency. README few-shot-clustering ước tính 10.000 truy vấn tới OpenAI API "may take an hour" [57], tức khoảng 0,36 giây mỗi truy vấn tuần tự (số năm 2023, không phải Haiku 5.5). Ở tốc độ đó, kịch bản A/B cần khoảng 100 giờ nếu không song song, hoặc 10 batch × 100K request. Kịch bản D xong trong vài phút. Kịch bản C rẻ nhất cho việc phân loại toàn bộ, nhưng dễ lệch thứ tự hoặc bỏ sót dòng, nên schema output phải có ID từng dòng. Nếu chạy local, vLLM có continuous batching, prefix caching (system prompt chứa taxonomy được tái dùng giữa các request) và lượng tử hóa [58]. Một benchmark của Microsoft đo Llama-3.1-8B trên 1×H100 đạt khoảng **6.067 token/s** throughput sinh (qua search) [59]. **Nhận định:** với tốc độ đó, 10 triệu token output của 1 triệu dòng mất khoảng nửa giờ phần sinh trên một GPU. Về chất lượng tiếng Việt, Qwen2.5-7B-Instruct đạt **57,51** trên VMLU, cao nhất trong nhóm 7B được liệt kê, còn Qwen2.5-72B đạt **69,17** (qua search; bản mirror và leaderboard chính thức không khớp hoàn toàn) [60]. Giá OpenAI và Gemini chỉ tìm được từ nguồn tổng hợp mâu thuẫn nhau, nên không đưa vào bảng.

### Distill sang classifier rẻ thay vì để LLM phân loại mọi dòng

TnT-LLM cho thấy LR trên embedding, huấn luyện từ nhãn LLM, ngang GPT-4 khi đối chiếu với nhãn người: 0,658 so với 0,655 cho intent, 0,650 so với 0,638 cho domain. Ở bài toán đa nhãn, classifier distill có precision cao hơn nhưng recall thấp hơn GPT-4 (qua search, trích đoạn từ trang tóm tắt nên cần đối chiếu Bảng 3) [3]. Pangakis & Wolken tái lập 14 nhiệm vụ và thấy classifier fine-tune trên nhãn GPT-4 "comparable" với classifier fine-tune trên nhãn người; lớp thiểu số có thể có precision/recall thấp (qua search) [61]. Trên tập Customer Reviews (sentiment), SetFit với **8 ví dụ mỗi lớp** đã cạnh tranh được với RoBERTa-Large fine-tune trên toàn bộ 3.000 ví dụ. SetFit không cần prompt, dùng được checkpoint đa ngữ, và nhanh hơn "an order of magnitude (or more)" so với few-shot dùng model lớn [62]. NLI zero-shot đa ngữ (mDeBERTa-v3 mnli-xnli) đạt trung bình **0,808** trên XNLI 15 ngôn ngữ (qua search) [63] nhưng dễ hỏng khi lệch miền. **Nhận định:** khi đã có taxonomy, thứ tự ưu tiên là SetFit hoặc LR trên nhãn LLM của mẫu, rồi đến nearest-centroid (centroid tính từ vài ví dụ thật, không chỉ từ câu mô tả nhãn), sau cùng mới là NLI zero-shot.

Nhãn LLM không hoàn toàn ổn định. Pangakis và cộng sự khuyên phân loại mỗi mẫu ít nhất 3 lần ở temperature > 0 và dùng "consistency score". Mẫu có consistency 1,0 có accuracy cao hơn **19,4 điểm phần trăm** so với mẫu kém nhất quán (qua search) [64]. Ổn định là điều kiện cần nhưng chưa đủ cho chính xác (qua search) [65]. Structured outputs dùng constrained decoding để bảo đảm JSON đúng schema, kể cả enum [66]. Cơ chế này chặn nhãn ngoài taxonomy ở mức cú pháp nhưng không bảo đảm nhãn đúng. **Nhận định:** nhãn bịa chủ yếu xuất hiện ở bước *đặt tên* (tên rộng hơn nội dung ví dụ), nên mỗi nhãn cần kèm định nghĩa và ví dụ, rồi kiểm bằng cách gán ngược ví dụ vào nhãn.

## Pipeline đề xuất: tám tầng, mỗi tầng cắt khối lượng cho tầng sau

**Nhận định:** pipeline dưới đây tổng hợp các bằng chứng ở trên. Latency là bậc độ lớn cho khoảng 1 triệu dòng; ô nào không có trích dẫn là ước lượng và phải tự đo.

| Tầng | Đầu vào → đầu ra | Công cụ on-prem | Latency / chi phí | LLM? |
|---|---|---|---|---|
| 1. Chuẩn hóa + mask | N dòng → N chuỗi chuẩn hóa + khóa không dấu | `unicodedata`, underthesea `text_normalize` [21], regex | vài giây đến vài phút CPU | không |
| 2. Đếm chính xác + tách nhánh | N → U chuỗi duy nhất có trọng số; gắn cờ máy/người | `value_counts`, cột nguồn, heuristic ở trên | giây | không |
| 3. Template mining (nhánh máy) | chuỗi máy → template + `size` | Drain3 (`add_log_message`, snapshot) [6] | O(N) [23]; Drain ~1,7 giờ cho ~50 triệu dòng nếu đơn vị là giây [7]; Brain tự báo 46 s/1 triệu dòng [26] | chỉ cho cụm nhỏ/dòng không khớp, kiểu LILAC [27] |
| 4. Khử trùng lặp + embedding + gom (nhánh người) | U chuỗi → k cụm (vài trăm đến vài nghìn) + "chưa xếp" | fingerprint/char n-gram [34]; e5 [36]; `community_detection` hoặc HDBSCAN [40] | embed chỉ U chuỗi, phải tự đo; 50k câu < 5 s cho community detection [40] | không |
| 5. Đặt tên, gộp, dựng taxonomy 2 cấp | k cụm × 10–30 ví dụ → taxonomy có định nghĩa | LLM local (Qwen qua vLLM) [55][58] hoặc API batch | < $1 cho 5.000 cụm; vài phút [2] | **có, 1 lần/cụm** + vài lần gộp |
| 6. Gán nhãn mẫu + distill | mẫu phân tầng vài nghìn dòng → LR/MLP hoặc SetFit | SetFit [62], scikit-learn | ~$0,05 nhãn LLM; inference micro giây/dòng | **có, trên mẫu** |
| 7. Gán dòng mới | dòng mới → nhãn hoặc "chưa xếp" | cache hash → `match()` [6] → classifier/nearest-centroid → ngưỡng | ms/dòng; LLM chỉ cho dòng tin cậy thấp | hiếm |
| 8. Kiểm chứng + thống kê | nhãn → tỷ lệ hiệu chỉnh + khoảng tin cậy | mẫu người 300–500 dòng, QuaPy [67] | công người là chi phí chính | tùy chọn làm người chấm phụ |

Phác thảo dưới đây chỉ để minh họa tầng 1, 2 và 7 (đã chạy thử phần chuẩn hóa):

```python
import re, unicodedata, numpy as np
MASKS = [  # cụ thể trước, chung sau
    (r"[\w.+-]+@[\w-]+\.[\w.]+", "<email>"), (r"https?://\S+", "<url>"),
    (r"\b\d{1,3}(?:\.\d{1,3}){3}\b", "<ip>"),
    (r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b", "<uuid>"),
    (r"\b[a-z]+[-_]?\d[\w-]*", "<id>"),          # user123, ord-2024-001
    (r"\b\d+(?:[.,]\d+)?%?", "<num>"),
]
def norm(s):  # thêm underthesea.text_normalize(s) để thống nhất vị trí dấu
    s = re.sub(r"\s+", " ", unicodedata.normalize("NFC", s).casefold()).strip(" .;,!")
    for pat, tok in MASKS:
        s = re.sub(pat, tok, s)
    return s          # "Đã chặn IP 10.0.0.5" -> "đã chặn ip <ip>"

def no_accent(s):     # khóa phụ để gom bản thiếu dấu, không dùng làm nhãn
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")

# Tầng 2: df["key"] = df.text.map(norm); counts = df.key.value_counts()
# Tầng 7: emb đã chuẩn hóa L2 (vd model.encode(["query: " + t ...], normalize_embeddings=True))
def assign(emb_new, centroids, tau):
    sims = emb_new @ centroids.T
    return np.where(sims.max(1) >= tau, sims.argmax(1), -1)   # -1 = "chưa xếp"
```

Dòng mới đến liên tục nên được xử lý theo thứ tự rẻ đến đắt. Trước hết tra cache theo chuỗi chuẩn hóa. Nếu không có, khớp template bằng `match()`, vốn không tạo cụm mới [6]. Sau đó embed và gán nearest-centroid với ngưỡng τ. Dòng dưới ngưỡng vào hàng đợi "chưa xếp", được gom lại định kỳ để tìm cụm mới, rồi người duyệt và thêm vào taxonomy. Các công cụ có sẵn hỗ trợ đúng mô thức này. `hdbscan.approximate_predict` giữ nguyên cụm, "a very fast operation", trả −1 cho điểm không khớp, và tác giả khuyên "retrain your model periodically to avoid drift" [68]. Zero-shot topic list của BERTopic gán theo nhãn định sẵn khi cosine vượt `zeroshot_min_similarity`, phần còn lại đi tiếp vào clustering để tìm chủ đề mới; ngưỡng phải thử riêng cho từng model embedding [69]. Docs BERTopic giới thiệu `merge_models` (train model mới trên dữ liệu mới rồi gộp để xem có chủ đề mới không) như một cách khác cho online; so với `.partial_fit`, cách này giữ được UMAP và HDBSCAN gốc, "which tends result in improved performance" [70]. Intercom dựng topic ban đầu từ 90 ngày hội thoại, rồi một pipeline hằng ngày gán topic cho hội thoại mới (qua search) [18]. **Nhận định:** nearest-centroid ổn định hơn `approximate_predict` khi taxonomy đã được người gộp hoặc tách tay, vì centroid tính lại được từ nhãn hiện tại. Mỗi bản ghi nên lưu `category_id`, `taxonomy_version` và `assign_method` (template/cache/classifier/LLM/người), kèm bảng ánh xạ phiên bản cũ → mới để chuỗi thời gian vẫn so được. Tỷ lệ "chưa xếp" theo tuần là chỉ báo drift rẻ nhất. Ngưỡng cosine phụ thuộc model (E5 có phân phối cosine dồn cao), nên phải hiệu chỉnh trên mẫu gán tay.

## Con số tần suất chỉ đáng tin sau ba kiểm tra: mẫu người, độ ổn định, đếm có hiệu chỉnh

### Metric nội tại chỉ để so cấu hình; bằng chứng thật là đối chiếu với nhãn người

Silhouette, Calinski-Harabasz và Davies-Bouldin "generally higher for convex clusters", nên chấm thấp các cụm dựa trên mật độ như HDBSCAN. Rand index chưa hiệu chỉnh "often close to 1.0" ngay cả khi hai phân cụm rất khác nhau. NMI và V-measure không hiệu chỉnh theo cơ hội và tăng khi số cụm tăng. Với mẫu nhỏ hoặc nhiều cụm thì "it is safer to use an adjusted index such as the Adjusted Rand Index (ARI)" [4]. DBCV được thiết kế cho clustering mật độ, nhưng tune bằng cách tối đa hóa chính DBCV thì dễ overfit metric. Không tìm được nghiên cứu về hành vi của DBCV trên embedding nhiều chiều. **Nhận định:** dùng metric nội tại để chọn giữa các cấu hình, còn kết luận "nhóm có đúng nghĩa không" thì đến từ nhãn người.

Mức đồng thuận giữa người với người là trần của mọi con số. Theo quy ước Krippendorff, α ≥ **0,800** thì tin được, 0,667–0,800 chỉ kết luận tạm, dưới 0,667 thì bỏ (qua search) [71]. TnT-LLM đo Cohen κ và Fleiss κ giữa người, rồi coi LLM như một người gán thêm (qua search) [11]. Cỡ mẫu không cần lớn: ước lượng accuracy với khoảng tin cậy 90% và bán kính ±0,05 cần ít nhất **271 mẫu**; muốn thu hẹp bán kính một nửa thì cần khoảng gấp 4 lần (qua search; khớp công thức n = z²·p(1−p)/E² với z = 1,645, p = 0,5, E = 0,05) [72]. Clio đưa ra một cách kiểm khác: gieo 19.476 hội thoại tổng hợp từ một cây chủ đề đã biết, rồi xem pipeline có dựng lại được không. Kết quả đúng **94%**, so với 5% nếu đoán ngẫu nhiên, và ổn định qua nhiều ngôn ngữ (qua search) [12]. Độ ổn định đo bằng bootstrap: `clusterboot` tính Jaccard giữa mỗi cụm gốc và cụm khớp nhất trong mẫu lại. Jaccard trung bình dưới 0,6 thì không nên tin cụm, từ 0,85 trở lên là "highly stable" (qua search) [73]. **Nhận định:** quy trình tối thiểu gồm năm bước. (1) Lấy 300–500 dòng phân tầng theo cụm. (2) Cho hai người gán độc lập và tính α; nếu α < 0,667 thì lỗi nằm ở định nghĩa danh mục, chưa phải ở thuật toán. (3) Tính ARI/AMI và accuracy sau ánh xạ đa số. (4) Chạy 5–10 seed hoặc bootstrap, giữ các cụm có Jaccard ≥ 0,75. (5) Báo tỷ lệ "khác/chưa xếp" cạnh mọi bảng tần suất.

### Đếm thẳng nhãn bị lệch; cần hiệu chỉnh và khoảng tin cậy

Bài toán "ước lượng phân phối lớp" (quantification) khác bài toán phân loại. Forman định nghĩa nó là ước lượng số ca trong tập test khi phân phối có thể khác tập huấn luyện (qua search) [15]. Với "adjusted classify and count" (ACC), tỷ lệ đếm được là p̂ = TPR·p + FPR·(1−p), nên p = (p̂ − FPR)/(TPR − FPR), với TPR và FPR đo trên tập kiểm; bản nhiều lớp giải hệ có ràng buộc (qua search) [5]. Thư viện QuaPy (BSD-3) cài đặt sẵn ACC và các phương pháp mạnh hơn [67]. Mỗi tỷ lệ nên có khoảng tin cậy: Wilson cho từng nhóm, và Sison-Glaz hoặc Goodman cho khoảng đồng thời trên cả phân phối (gói R `MultinomialCI`, `DescTools::MultinomCI`) (qua search) [16]. Khi cắt theo một cột khác như "nguồn" hay "loại bản ghi", quy tắc thường dùng cho chi-square là mọi tần số kỳ vọng > 1 và không quá 20% ô có kỳ vọng < 5; nếu không đạt thì dùng Fisher exact (qua search) [74]. **Nhận định:** nên gộp nhóm hiếm theo cây phân cấp định sẵn *trước* khi xem kết quả, rồi mới kiểm định, và hiệu chỉnh đa so sánh khi so nhiều cặp.

Cách trình bày nên đi từ thô đến mịn. Intercom tìm subtopic bằng cách gom câu hỏi tương tự, rồi gộp lên topic rộng hơn với tên do AI đặt (qua search) [18]. Clio dựng ba cấp khoảng 10/100/1.000 cụm [12]. Zendesk gắn mức tự tin High/Medium/Low cho mỗi dự đoán và chỉ bật tính năng khi mẫu có ≥ 30% ở mức high và ≥ 60% ở mức medium (qua search) [19]. Theo Schonlau & Couper, để máy làm phần chắc và người làm phần khó thì ở mức 80% độ chính xác tổng thể, **54–80%** dữ liệu được phân loại tự động (qua search) [75]. **Nhận định:** bảng cuối cùng nên là biểu đồ Pareto ở cấp thô, kèm đường tích lũy. Mọi nhóm dưới 1–2% gộp thành một dòng "đuôi dài (N nhóm)", có drill-down xuống cấp mịn. Mỗi cột ghi tỷ lệ kèm khoảng Wilson 95%, tỷ lệ "chưa xếp", và nếu có tập kiểm thì ghi cả tỷ lệ đếm thẳng lẫn tỷ lệ đã hiệu chỉnh.

## Hệ thống thật đều chốt taxonomy rồi mới gán; sửa form nhập là phòng ngừa song song

Các case study công khai cùng một mẫu hình. Uber COTA phân loại ticket hỗ trợ vào hàng nghìn lớp; văn bản là feature quan trọng nhất, nhưng được kết hợp với lựa chọn menu và dữ liệu chuyến đi. A/B test cho thời gian giải quyết giảm khoảng **10%** mà không giảm mức hài lòng (qua search) [17]. Intercom và Zendesk gán theo taxonomy cố định có độ tự tin và cho người đổi tên hoặc thêm topic. Cả hai chỉ hỗ trợ đầy đủ tiếng Anh ở phần báo cáo (qua search) [18][19]. TnT-LLM và Clio dùng gom cụm và LLM để *dựng* taxonomy, còn việc gán ở quy mô lớn do classifier hoặc pipeline cố định đảm nhiệm [11][12]. Ở mảng bảo trì công nghiệp, nơi ghi chú cũng ngắn, nhiều viết tắt và nhiều người viết, nhóm NIST lập luận rằng công cụ NLP chung "suffering from a lack of verification, validation, and ultimately, personnel trust". Họ xây Nestor để hỗ trợ người gán tag thay vì tự động hóa hoàn toàn (qua search) [76][77]. Không tìm thấy case study công khai nào về lý do hủy đơn có số liệu pipeline.

Mã lý do có cấu trúc kèm ghi chú tự do là thực hành chuẩn, nhưng picklist không tự động cho dữ liệu sạch. Sexton, Hodkiewicz và Brundage dùng Human Reliability Analysis để cho thấy buộc người nhập chọn từ danh mục định sẵn dễ sinh lỗi khi schema không khớp cách họ mô tả vấn đề (qua search) [20]. Hodkiewicz & Ho thấy các trường mã có cấu trúc thường thiếu hoặc sai, và chính free text là nguồn để sửa lại (qua search) [78]. Trong y tế, bổ sung free text vào trường có cấu trúc "substantially improve" dữ liệu về tình trạng hút thuốc (qua search) [79]. **Nhận định:** vòng phòng ngừa hợp lý gồm năm bước. (1) Dùng pipeline ở trên khai phá lịch sử thành taxonomy 2 cấp. (2) Cho người duyệt và đặt tên bằng ngôn ngữ của người nhập. (3) Đưa cấp thô vào form làm mã lý do bắt buộc, cấp mịn làm gợi ý. (4) Giữ ô ghi chú tự do và một mã "khác — ghi rõ". (5) Kiểm định kỳ độ khớp giữa mã đã chọn và ghi chú. Với dòng máy sinh như "Đã khóa tài khoản user123", cách rẻ nhất là cho hệ thống nguồn ghi luôn mã sự kiện và tham số vào cột riêng, thay vì parse ngược.

## Các nguồn bất đồng ở đâu

**Ép điểm vào cụm hay để là nhiễu.** Một paper về BERTopic trên văn bản ngắn thấy k-means cho hiệu năng tương đương HDBSCAN mà không bỏ dòng nào (qua snippet) [9]. Docs BERTopic lại lưu ý rằng giảm outlier có thể đẩy dòng vào chủ đề không thuộc về nó [10]. Hai bên đo khác thứ: paper đo chất lượng chủ đề, docs nói về độ đúng của từng phép gán. Với mục tiêu đếm tần suất, sai lệch ở từng phép gán cộng dồn thẳng vào tỷ lệ, nên báo cáo này theo hướng giữ "chưa xếp" có ngưỡng.

**Classifier distill có thay được LLM không.** TnT-LLM cho thấy LR ngang GPT-4 trên nhãn đơn nhưng recall thấp hơn ở đa nhãn [3]. Pangakis & Wolken viết "comparable" ở bản cuối, còn bản đầu thận trọng hơn ("slightly worse"), và lớp thiểu số yếu hơn [61]. **Nhận định:** distill đủ tốt cho các nhóm lớn chiếm phần đầu Pareto, nhưng nhóm hiếm nên có kiểm tra riêng hoặc ngưỡng chuyển sang LLM/người.

**Đếm thẳng có tệ đến thế không.** Nhánh quantification coi "classify and count" là lệch có hệ thống khi phân phối dịch chuyển [15][5]. Moreo & Sebastiani phản biện rằng CC được tune bằng loss của quantification thì gần đạt state of the art, dù vẫn kém một số phương pháp mới (qua search) [80]. Cả hai bên đồng ý rằng CC không tune là không đủ.

**Số benchmark log parsing lệch giữa các nguồn.** Paper Matryoshka có hai phiên bản ghi điểm LILAC khác nhau (0,90/0,82 và 0,95/0,87) [32]. Tóm tắt search về LogBatcher có câu "reduce LLM invocation cost by at least 106%", một con số không thể đúng nếu hiểu theo nghĩa đen [29]. AdaParser tự báo vượt SOTA kể cả zero-shot, trong khi một survey ghi kết quả zero-shot của nó "significantly inferior" so với few-shot (qua search) [81]. Vì vậy báo cáo chỉ dùng các số này để nói về xu hướng (gọi theo template rẻ hơn gọi theo dòng nhiều bậc), không dùng để xếp hạng parser.

## Kết luận và hàm ý

Điều rút ra quan trọng nhất là bài toán "mỗi giá trị đều khác nhau" phần lớn không phải bài toán ngữ nghĩa. Tính khác biệt chủ yếu đến từ tham số, cách gõ dấu và biến thể chính tả, và những thứ đó được giải gần như miễn phí bằng chuẩn hóa, mask và đếm chính xác trước khi bất kỳ model nào chạy. Embedding chỉ cần cho phần đuôi thật sự do người diễn đạt khác nhau, và LLM chỉ cần ở chỗ con người cũng phải suy nghĩ: đặt tên, gộp, vạch ranh giới giữa các lý do. Đặt LLM ở mức cụm thay vì mức dòng làm số lần gọi giảm từ hàng triệu xuống vài nghìn. Nhờ vậy model local cỡ 7–8B trên một GPU, hoặc API batch với chi phí dưới vài đô, đều khả thi cho dữ liệu nhạy cảm. Việc chọn model LLM vì thế ít quan trọng hơn việc thiết kế tầng.

Hàm ý thứ hai là độ tin của bảng tần suất phụ thuộc vào việc kiểm chứng hơn là vào thuật toán. Benchmark công khai không đo đúng loại dữ liệu này: log tiếng Anh, tiếng Việt dịch máy, không có văn bản gõ tay thiếu dấu. Vì vậy bước đầu tiên nên là gán tay 300–500 dòng của chính mình. Bộ nhãn đó dùng ba lần: chọn model embedding và ngưỡng, đo accuracy và độ đồng thuận, và hiệu chỉnh tỷ lệ đếm. Một bảng Pareto có khoảng tin cậy, tỷ lệ "chưa xếp" và phiên bản taxonomy đáng giá hơn nhiều so với một bảng đếm cụm thô trông chính xác. Về dài hạn, khi taxonomy đã ổn định, đưa nó ngược vào form nhập liệu là cách trực tiếp nhất để bài toán nhỏ lại theo thời gian.

## Chưa kiểm chứng được

- Phần lớn số liệu từ paper arXiv/ACL chỉ đọc được **qua trích đoạn search** vì proxy chặn arxiv.org, aclanthology.org, huggingface.co: giới hạn 12 giờ và kết luận thống kê/ngữ nghĩa của Jiang et al. (FGA 0,74 → 0,55 và 6/15 parser đã đối chiếu được với bảng trong repo Loghub-2.0), kết quả ICSE 2019, số của LILAC/LogBatcher/DivLog/LibreLog/Matryoshka, điểm clustering VN-MTEB (bảng có ô bị lỗi khi trích), số TnT-LLM (trích từ trang tóm tắt, cần đối chiếu Bảng 3), chi phí và accuracy của Clio, chi phí ClusterLLM và few-shot clustering, so sánh k-LLMmeans với ClusterLLM (lấy từ bài review), số Pangakis 19,4 điểm phần trăm, ngưỡng clusterboot, cỡ mẫu 271.
- Không có số "LLM calls per N lines" cụ thể của LILAC (bảng RQ4 trong paper). Câu "at least 106%" của LogBatcher chưa đối chiếu được.
- Không có benchmark nào đo việc tách dòng máy sinh và người viết trong cùng một cột (truy vấn đã thử: "distinguish template-generated vs human-written text messages free-text field…").
- Không có đánh giá công khai nào về embedding trên tiếng Việt không dấu hay viết tắt kiểu chat, và không có số clustering VN-MTEB cho multilingual-e5-small, paraphrase-multilingual-*, các model chuyên tiếng Việt. Có thể tự chạy thư viện `mteb` để lấy.
- Không có số throughput CPU (câu/giây) từ nguồn bậc 1–2 cho các model embedding, không có throughput chính thức của Drain3 (bảng thời gian Loghub-2.0 là của Drain bản logparser và không ghi đơn vị), và không có benchmark vLLM cho dạng "prompt chung dài + input ngắn + output vài token".
- Giá OpenAI và Gemini tháng 10/2026 chỉ có từ nguồn tổng hợp mâu thuẫn nhau (vd output GPT-5 mini ghi $2,00 ở nguồn này, $1,00 ở nguồn khác); trang chính thức bị chặn hoặc bị cắt.
- Chưa có số đo token/từ cho tiếng Việt của tokenizer Claude/GPT/Gemini; chi phí thực có thể cao hơn phép tính giả định 30 token/dòng.
- Không có nguồn bậc 1 cho ngưỡng "tỷ lệ khác/nhiễu chấp nhận được" hay ngưỡng drift. Con số "< 10% Other" chỉ đến từ một vendor khảo sát (getthematic.com, bậc 3), không dùng làm bằng chứng.
- Chưa có case study công khai nào về lý do hủy đơn có số liệu pipeline, và chưa có nghiên cứu định lượng so sánh "chỉ free text" với "mã + free text" về chất lượng phân tích lý do.
- Chưa lấy được điểm XNLI riêng cho tiếng Việt của mDeBERTa, chưa xác nhận model card của các model embedding tiếng Việt dựa trên PhoBERT có yêu cầu tách từ hay không, và chưa mở được model card E5 để xác nhận quy ước tiền tố `query: `.
- Các trang trợ giúp của Intercom, Zendesk và blog Uber COTA không mở được (lỗi DNS qua proxy); mọi chi tiết về chúng là qua search.

## Nguồn

[1] logpai/loghub-2.0 README (Loghub-2.0, ISSTA 2024) — LogPAI, 2024 (bậc 1, đã mở). https://github.com/logpai/loghub-2.0
[2] Pricing — Claude Docs, Anthropic, truy cập 2026-10-21 (bậc 1, đã mở). https://platform.claude.com/docs/en/about-claude/pricing
[3] TnT-LLM: Text Mining at Scale with Large Language Models — Microsoft, arXiv 2403.12173, 2024-03 (bậc 1, qua trích đoạn search). https://arxiv.org/abs/2403.12173
[4] Clustering performance evaluation (User Guide, clustering.rst) — scikit-learn, bản main, đọc 2026-10-21 (bậc 1, đã mở). https://raw.githubusercontent.com/scikit-learn/scikit-learn/main/doc/modules/clustering.rst
[5] Adjusted Count Quantification Learning on Graphs — arXiv 2503.09395, 2025 (bậc 1, qua search). https://arxiv.org/pdf/2503.09395
[6] Drain3 README — LogPAI, không rõ ngày (changelog mới nhất v0.9.11) (bậc 1, đã mở). https://github.com/logpai/Drain3
[7] Loghub-2.0 RQ2: effectiveness_results.csv và efficiency_results.csv — LogPAI, artifact của Jiang et al. ISSTA 2024, đọc 2026-10-21 (bậc 1, đã mở). https://github.com/logpai/loghub-2.0/tree/main/RQs_experiments/RQ2
[8] VN-MTEB — Pham, Luu, Vo, Nguyen, Hoang (GreenNode AI, ĐHQG-HCM), arXiv 2507.21500, 2025-07; Findings of EACL 2026 (bậc 1, qua snippet). https://arxiv.org/html/2507.21500
[9] Experiments on Generalizability of BERTopic on Multi-Domain Short Text — arXiv 2212.08459, 2022-12 (bậc 1, qua snippet). https://arxiv.org/pdf/2212.08459
[10] BERTopic FAQ — Maarten Grootendorst, docs trên GitHub, đọc 2026-10 (bậc 1, đã mở). https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/faq.md
[11] TnT-LLM: Text Mining at Scale with Large Language Models — Microsoft Research, 2024 (bậc 1, đã mở trang; số liệu qua search). https://www.microsoft.com/en-us/research/publication/tnt-llm-text-mining-at-scale-with-large-language-models/
[12] Clio: Privacy-Preserving Insights into Real-World AI Use — Anthropic, arXiv 2412.13678, 2024-12 (bậc 1, qua trích đoạn search). https://arxiv.org/abs/2412.13678
[13] k-LLMmeans (Summaries as Centroids) — arXiv 2502.09667, 2025-02, ICLR 2026 (bậc 1, qua trích đoạn search; số so sánh từ bài review). https://arxiv.org/abs/2502.09667
[14] Batch processing — Claude Docs, Anthropic, truy cập 2026-10-21 (bậc 1, đã mở). https://platform.claude.com/docs/en/build-with-claude/batch-processing
[15] Quantifying counts and costs via classification — George Forman, Data Mining and Knowledge Discovery 17, 2008 (bậc 1, bản ghi metadata qua search). https://datalearner.com/academic/journal-papers/1384-5810/volumes-and-issues/17/paper-detail/9256
[16] MultinomialCI: Simultaneous confidence intervals for multinomial proportions (Sison-Glaz) — CRAN refman, không rõ ngày (bậc 1, qua search). https://cran.uni-muenster.de/web/packages/MultinomialCI/refman/MultinomialCI.html
[17] COTA — Molino, Zheng, Wang (Uber), KDD 2018, arXiv 1807.01337 (bậc 1, qua search). https://ar5iv.labs.arxiv.org/html/1807.01337
[18] Use the Topics Explorer to see what's driving volume — Intercom Help, không rõ ngày (bậc 1, qua search). https://www.intercom.com/help/en/articles/11390087-use-the-topics-explorer-to-see-what-s-driving-volume
[19] Automatically detecting customer intent, sentiment, and language — Zendesk Help, không rõ ngày (bậc 1, qua search). https://support.zendesk.com/hc/en-us/articles/4550640560538-Automatically-detecting-customer-intent-sentiment-and-language
[20] Categorization Errors for Data Entry in Maintenance Work-Orders — Sexton, Hodkiewicz, Brundage, PHM Society 2019 (bậc 1, qua search). https://papers.phmsociety.org/index.php/phmconf/article/view/790
[21] underthesea README và NLP.md — undertheseanlp, không rõ ngày (bậc 1, đã mở). https://github.com/undertheseanlp/underthesea
[22] ViLexNorm — EACL 2024, arXiv 2401.16403 (bậc 1, qua search). https://arxiv.org/html/2401.16403v2
[23] logparser docs: Drain — LogPAI, không rõ ngày (bậc 1, qua search). https://logparser.readthedocs.io/en/latest/tools/Drain.html
[24] Tools and Benchmarks for Automated Log Parsing — Zhu et al., ICSE-SEIP 2019, arXiv 1811.03509 (bậc 1, qua search). https://arxiv.org/pdf/1811.03509
[25] A Large-scale Evaluation for Log Parsing Techniques: How Far are We? — Jiang et al., ISSTA 2024, arXiv 2308.10828 (bậc 1, qua search). https://arxiv.org/html/2308.10828v2
[26] Brain (log parser, TSC 2023) — gaiusyu, GitHub (bậc 1, tác giả tự báo, qua search). https://github.com/gaiusyu/Brain
[27] LILAC (adaptive parsing cache) — LogPAI, FSE 2024, arXiv 2310.01796 (bậc 1, qua search; README đã mở tại https://github.com/logpai/LILAC). https://arxiv.org/abs/2310.01796
[28] LogBatcher README — LogIntelligence, không rõ ngày (bậc 1, đã mở). https://github.com/LogIntelligence/LogBatcher
[29] Demonstration-Free: Towards More Practical Log Parsing with Large Language Models (LogBatcher) — Xiao, Le, Zhang, ASE 2024, arXiv 2406.06156 (bậc 1, qua search). https://arxiv.org/pdf/2406.06156
[30] DivLog — ICSE 2024, arXiv 2307.09950 (bậc 1, qua search). https://arxiv.org/html/2307.09950
[31] LibreLog (OpenLogParser) — arXiv 2408.01585, 2024-08 (bậc 1, qua search). https://arxiv.org/pdf/2408.01585
[32] Matryoshka (log parsing) — arXiv 2506.17512, 2025 (bậc 1, qua search; hai phiên bản ghi số khác nhau). https://arxiv.org/html/2506.17512v2
[33] LUNAR: Unsupervised LLM-based Log Parsing — FSE 2025, arXiv 2406.07174 (bậc 1, qua search). https://arxiv.org/html/2406.07174v2
[34] Clustering methods in-depth — OpenRefine docs (nguồn trên GitHub), không rõ ngày (bậc 1, đã mở). https://github.com/OpenRefine/openrefine.org/blob/master/docs/technical-reference/clustering-in-depth.md
[35] mteb/benchmarks.py (định nghĩa VN-MTEB (vie, v1)) — embeddings-benchmark, đọc 2026-10 (bậc 1, đã mở). https://raw.githubusercontent.com/embeddings-benchmark/mteb/main/mteb/benchmarks/benchmarks/benchmarks.py
[36] E5 / Multilingual E5 README — Microsoft unilm, đọc 2026-10 (bậc 1, đã mở). https://raw.githubusercontent.com/microsoft/unilm/master/e5/README.md
[37] BGE-M3 README — FlagEmbedding (BAAI), đọc 2026-10 (bậc 1, đã mở). https://raw.githubusercontent.com/FlagOpen/FlagEmbedding/master/research/BGE_M3/README.md
[38] Pretrained Models — sentence-transformers docs, đọc 2026-10 (bậc 1, đã mở). https://raw.githubusercontent.com/UKPLab/sentence-transformers/master/docs/sentence_transformer/pretrained_models.md
[39] vinai/phobert-base-v2 model card — VinAI, không rõ ngày (bậc 1, qua snippet). https://huggingface.co/vinai/phobert-base-v2
[40] Clustering (examples README) — sentence-transformers, đọc 2026-10 (bậc 1, đã mở). https://raw.githubusercontent.com/UKPLab/sentence-transformers/master/examples/sentence_transformer/applications/clustering/README.md
[41] BERTopic Best Practices — Maarten Grootendorst, đọc 2026-10 (bậc 1, đã mở). https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/best_practices/best_practices.md
[42] Penerapan UMAP dan HDBSCAN … Judul Buku — JINACS, Universitas Negeri Surabaya, ~2025 (bậc 2, qua snippet). https://ejournal.unesa.ac.id/index.php/jinacs/article/view/82679
[43] BERTopic Outlier reduction — Maarten Grootendorst, đọc 2026-10 (bậc 1, đã mở). https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/outlier_reduction/outlier_reduction.md
[44] HDBSCAN FAQ — scikit-learn-contrib/hdbscan, không rõ ngày (bậc 1, qua search). https://hdbscan.readthedocs.io/en/stable/faq.html
[45] BERTopic LLM & Generative AI representation — Maarten Grootendorst, đọc 2026-10 (bậc 1, đã mở). https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/representation/llm.md
[46] A Fast and Accurate Vietnamese Word Segmenter (RDRSegmenter) — LREC 2018, arXiv 1709.06307 (bậc 1, qua search). https://arxiv.org/pdf/1709.06307
[47] Short Text Topic Modeling Techniques, Applications, and Performance: A Survey — Qiang et al., arXiv 1904.07695, 2019 (bậc 1, qua snippet). https://arxiv.org/pdf/1904.07695
[48] ClusterLLM — EMNLP 2023 (bậc 1, qua trích đoạn search; README đã mở tại https://github.com/zhang-yu-wei/ClusterLLM). https://aclanthology.org/2023.emnlp-main.858.pdf
[49] Large Language Models Enable Few-Shot Clustering — Viswanathan et al., TACL 2024 (bậc 1, qua trích đoạn search). https://aclanthology.org/2024.tacl-1.18.pdf
[50] Text Clustering as Classification with LLMs — Huang & He, arXiv 2410.00927, 2024-10 (bậc 1, qua trích đoạn search). https://arxiv.org/abs/2410.00927
[51] IDAS: Intent Discovery with Abstractive Summarization — NLP4ConvAI 2023 (bậc 1, qua trích đoạn search). https://aclanthology.org/2023.nlp4convai-1.7
[52] LLooM (Concept Induction, CHI 2024) — Michelle Lam et al., GitHub, truy cập 2026-10-21 (bậc 1, đã mở). https://github.com/michelle123lam/lloom
[53] GoalEx (Propose-Assign-Select) — EMNLP 2023, GitHub (bậc 1, đã mở). https://github.com/ZihanWangKi/GoalEx
[54] TnT-LLM (bản KDD 2024) — ACM Digital Library, 2024-08 (bậc 1, qua trích đoạn search). https://dl.acm.org/doi/pdf/10.1145/3637528.3671647
[55] OpenClio — Phylliida, GitHub, không rõ ngày, truy cập 2026-10-21 (bậc 1, đã mở). https://github.com/Phylliida/OpenClio
[56] Prompt caching — Claude Docs, Anthropic, truy cập 2026-10-21 (bậc 1, đã mở). https://platform.claude.com/docs/en/build-with-claude/prompt-caching
[57] few-shot-clustering README — viswavi, GitHub, không rõ ngày (bậc 1, đã mở). https://github.com/viswavi/few-shot-clustering
[58] vLLM README — vllm-project, GitHub, truy cập 2026-10-21 (bậc 1, đã mở). https://github.com/vllm-project/vllm
[59] Inference performance of Llama 3.1 8B using vLLM across various GPUs and CPUs — Microsoft Azure HPC Blog, 2025 (bậc 2, qua trích đoạn search). https://techcommunity.microsoft.com/blog/azurehighperformancecomputingblog/inference-performance-of-llama-3-1-8b-using-vllm-across-various-gpus-and-cpus/4448420
[60] VMLU Leaderboard — ZaloAI & JAIST, 2025-02 (bậc 1–2, qua trích đoạn search; mirror tại https://github.com/ZaloAI-Jaist/VMLU). https://vmlu.ai/leaderboard
[61] Knowledge Distillation in Automated Annotation — Pangakis & Wolken, NLP+CSS 2024, arXiv 2406.17633 (bậc 1, qua trích đoạn search). https://arxiv.org/abs/2406.17633
[62] SetFit README — Hugging Face, GitHub, truy cập 2026-10-21 (bậc 1, đã mở). https://github.com/huggingface/setfit
[63] MoritzLaurer/mDeBERTa-v3-base-mnli-xnli model card — Hugging Face, không rõ ngày (bậc 1, qua trích đoạn search). https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-mnli-xnli
[64] Automated Annotation with Generative AI Requires Validation — Pangakis et al., arXiv 2306.00176, 2023-06 (bậc 1, qua trích đoạn search). https://arxiv.org/abs/2306.00176
[65] Prompt Stability Score — arXiv 2407.02039, 2024-07 (bậc 1, qua trích đoạn search). https://arxiv.org/abs/2407.02039
[66] Structured outputs — Claude Docs, Anthropic, truy cập 2026-10-21 (bậc 1, đã mở). https://platform.claude.com/docs/en/build-with-claude/structured-outputs
[67] QuaPy: A Python-based framework for quantification — Moreo, Esuli, Sebastiani, PyPI (CIKM 2021) (bậc 1, qua search). https://pypi.org/project/QuaPy
[68] Predicting clusters for new points (prediction_tutorial.rst) — scikit-learn-contrib/hdbscan, đọc 2026-10 (bậc 1, đã mở). https://raw.githubusercontent.com/scikit-learn-contrib/hdbscan/master/docs/prediction_tutorial.rst
[69] BERTopic Zero-shot Topic Modeling — Maarten Grootendorst, đọc 2026-10 (bậc 1, đã mở). https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/zeroshot/zeroshot.md
[70] BERTopic Online Topic Modeling — Maarten Grootendorst, đọc 2026-10 (bậc 1, đã mở). https://raw.githubusercontent.com/MaartenGr/BERTopic/master/docs/getting_started/online/online.md
[71] Reliability in Software Engineering Qualitative Research through Inter-Coder Agreement — arXiv 2008.00977, 2020 (bậc 1, qua search). https://arxiv.org/pdf/2008.00977
[72] confidence-planner — arXiv 2301.05702, 2023 (bậc 1, qua search). https://arxiv.org/pdf/2301.05702
[73] clusterboot {fpc} — Christian Hennig, R documentation, không rõ ngày (bậc 1, qua search). https://search.r-project.org/CRAN/refmans/fpc/html/clusterboot.html
[74] Chi-Square Test of Independence Rule of Thumb: n > 5 — The Analysis Factor, không rõ ngày (bậc 2, qua search). https://www.theanalysisfactor.com/chi-square-test-of-independence-rule-of-thumb/
[75] Semi-automated categorization of open-ended questions — Schonlau & Couper, Survey Research Methods 10(2), 2016 (bậc 1, qua search). https://www.ssoar.info/ssoar/handle/document/49780?show=full
[76] Technical Language Processing: Unlocking Maintenance Knowledge — Brundage, Sexton, Hodkiewicz, Dima, Lukens, Manufacturing Letters, 2020-12 (bậc 1, qua search). https://www.academia.edu/80398248/Technical_language_processing_Unlocking_maintenance_knowledge
[77] Nestor: A Tool for Natural Language Annotation of Short Texts — Brundage & Sexton, NIST, 2019 (bậc 1, qua search). https://www.nist.gov/publications/nestor-tool-natural-language-annotation-short-texts
[78] Hodkiewicz & Ho — J. Quality in Maintenance Engineering 22(2):146–163, 2016 (bậc 1, qua search). https://www.emerald.com/insight/content/doi/10.1108/JQME-04-2015-0013/full/html
[79] Bài về bổ sung free text vào trường có cấu trúc cho tình trạng hút thuốc (525 bản ghi) — PMC4419995, không rõ ngày (bậc 1, qua search). https://pmc.ncbi.nlm.nih.gov/articles/PMC4419995
[80] Re-Assessing the "Classify and Count" Quantification Method — Moreo & Sebastiani, 2021, arXiv 2011.02552 (bậc 1, qua search). https://ar5iv.labs.arxiv.org/html/2011.02552
[81] AdaParser — Wu, Yu, Li, IEEE Xplore, 2024 (bậc 1, qua search); nhận xét zero-shot từ survey arXiv 2509.10858 (bậc 2). https://ieeexplore.ieee.org/document/11025900/
