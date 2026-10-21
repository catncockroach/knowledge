# Trích ý trước, gom sau; Key Point Analysis; mã hóa định tính bằng LLM; chi phí ở quy mô vài trăm–vài nghìn bản ghi

Ghi chú môi trường: proxy chặn arxiv.org, aclanthology.org, openreview, semanticscholar, dl.acm.org, các trang *.github.io và hầu hết site PDF của trường/viện. Mọi con số lấy từ paper (trừ khi ghi "đã mở") đều **qua search**, tức chỉ thấy trong trích đoạn của công cụ tìm kiếm. Các nguồn **đã mở** gồm: README/mã nguồn trên raw.githubusercontent.com, trang giá/rate limit/models của Claude Docs, trang Clio của Anthropic.

Phạm vi đã điều chỉnh theo yêu cầu điều phối (giữa chừng): dữ liệu điển hình là **vài trăm bản ghi viết tay mỗi lần phân tích, tối đa vài nghìn khi cộng dồn**. Phần chi phí tính cho 200, 500 và 2.000 bản ghi. Phần quy mô 100k đã bỏ.

## 1. Trích ý trước, gom sau (extract-then-cluster)

### Kết luận ngắn
Có bằng chứng định lượng rằng biểu diễn văn bản bằng đầu ra do LLM sinh ra (nhãn tóm tắt, keyphrase, giải thích) giúp gom cụm tốt hơn so với embed nguyên văn: IDAS tăng tới +7,42% trên các metric cụm, Few-shot clustering cải thiện mọi metric trên mọi dataset. Nhưng các bằng chứng này đều đo trên **câu ngắn** (intent), và có một nghiên cứu ngược chiều: tóm tắt trước khi embed "không cải thiện nhất quán". Mức chắc chắn **trung bình**: chiều tác động khá nhất quán ở các paper dùng LLM, nhưng chưa có thí nghiệm nào trên đoạn kỹ thuật 4–5 câu, và mọi số đều qua search.

### Phát hiện có nguồn
- **Clio (Anthropic)** có 4 bước, theo trang chính thức: (1) trích "facet" cho từng hội thoại (chủ đề, số lượt, ngôn ngữ...); (2) gom cụm ngữ nghĩa; (3) Claude đặt tiêu đề và mô tả cho từng cụm; (4) dựng phân cấp nhiều tầng. "These four steps are powered entirely by Claude." Bài đăng 2024-12-12. Ghi chú cập nhật 2026-08-24 cho biết công cụ nay mang tên "Anthropic Insights". — [Clio: Privacy-preserving insights into real-world AI use](https://www.anthropic.com/research/clio) (bậc 1, 2024-12-12, cập nhật 2026-08-24; đã mở)
- Đánh giá Clio trên dữ liệu tổng hợp: Clio tái dựng đúng phân bố với **94%** accuracy trên 20 cụm cấp cao (19.476 hội thoại tổng hợp thông thường) và **84%** trên 18 cụm (dữ liệu "concerning"). Ở thí nghiệm này, tầng cấp cao được cố định theo ground truth, và hệ thống gán các cụm cơ sở vào tầng đó. — [Clio, arXiv 2412.13678](https://arxiv.org/pdf/2412.13678) (bậc 1, 2024-12; qua search)
- **Thiết kế prompt trích facet** (bản tái lập mã nguồn mở OpenClio, theo phụ lục của paper): đặt câu hỏi `question` về bản ghi, yêu cầu trả lời bằng tiếng Anh trong `<answer>`, "be clear and concise and get to the point in at most two sentences", không có PII hay danh từ riêng, kèm 3 câu ví dụ đầu ra. Dùng **prefill** cho lượt assistant (vd "The user's overall request for the assistant is to"), ép đầu ra bắt đầu bằng cùng một khuôn câu. Với dữ liệu không phải hội thoại, OpenClio có `genericSummaryFacets`: "Please summarize the provided data in a single sentence". — [OpenClio prompts.py](https://raw.githubusercontent.com/Phylliida/OpenClio/main/openclio/prompts.py) và [README](https://github.com/Phylliida/OpenClio) (bậc 1, không rõ ngày, đọc 2026-10-21; đã mở)
- **Prompt đặt tên cụm** của OpenClio ("from G.5"): đưa vào các phát biểu trong cụm **cùng các phát biểu của cụm lân cận làm "contrastive_answers"**, yêu cầu mô tả 2 câu và tên tối đa 10 từ, "specific but also reflective of most of the statements (rather than reflecting only one or two)". — [OpenClio prompts.py](https://raw.githubusercontent.com/Phylliida/OpenClio/main/openclio/prompts.py) (bậc 1; đã mở)
- **Tham số mặc định OpenClio**: số cụm cơ sở `n//10` (trung bình 10 điểm mỗi cụm); lấy mẫu 10 điểm trong cụm và 10 điểm ngoài cụm để đặt tên; **đặt tên 5 lần rồi lấy đáp án xuất hiện nhiều nhất** (`nNameDescriptionSamplesPerCluster=5`, "help avoid any noise from data ordering"); gán cụm vào tầng cao cũng lấy mẫu 5 lần theo đa số; `temperature 0.7`; `seed=27` "so runs are deterministic"; `dedupData=True` vì "non-deduped data can result in very large cluster sizes". Ví dụ chạy dùng `Qwen/Qwen3-8B` qua vLLM. — [OpenClio opencliotypes.py](https://raw.githubusercontent.com/Phylliida/OpenClio/main/openclio/opencliotypes.py) (bậc 1; đã mở)
- **IDAS** (NLP4ConvAI 2023): LLM sinh "abstractive summaries, i.e., labels" cho từng utterance, dùng ICL bootstrap từ một tập seed prototypical. Utterance và nhãn được encode bằng encoder đóng băng rồi gom cụm. Kết quả: "outperforms the state-of-the-art by up to **+7.42%** in standard cluster metrics" trên Banking, StackOverflow, Transport. — [IDAS README (abstract)](https://github.com/maarten-deraedt/idas-intent-discovery-with-abstract-summarization) (bậc 1, 2023; đã mở)
- **Few-shot clustering, keyphrase expansion** (Viswanathan et al., TACL 2024): LLM sinh danh sách keyphrase JSON cho từng văn bản. Keyphrase được encode **bằng cùng encoder** rồi nối vector với embedding gốc. Prompt mẫu: "provide a comprehensive set of keyphrases that could describe this query's intent. These keyphrases should be distinct from those that might describe queries with different intents" (đã mở trong README). Kết quả: "improve cluster quality on every metric for all datasets considered" so với K-Means trên embedding văn bản (qua search, bài viết của NEC). — [few-shot-clustering README](https://github.com/viswavi/few-shot-clustering) (bậc 1; đã mở), [NEC Technical Journal](https://www.nec.com/en/global/techrep/journal/g23/n02/230216.html) (bậc 2; qua search)
- **Bằng chứng ngược chiều**: Petukhova et al. thêm bước tóm tắt (bằng summarizer BERT-large, không phải LLM) trước khi embed và thấy "summarisation techniques do not consistently enhance clustering efficiency". Các tập dữ liệu nhỏ (299, 333, 18.846 văn bản). — [Text Clustering with LLM Embeddings, arXiv 2403.15112](https://arxiv.org/abs/2403.15112v1) (bậc 1, 2024-03; qua search)
- **Giải thích do LLM sinh làm feature**: Llama-3.1-8B/70B và DeepSeek-R1-Llama-8B sinh zero-shot một lời giải thích cho từng văn bản. Embedding của lời giải thích được ghép với embedding văn bản rồi đưa vào BERTopic. Nghiên cứu báo cáo coherence tăng và kết quả "closer to golden annotations when facing user-created data". Không thấy số cụ thể. — [Leveraging LLMs to enhance clustering-based topic modeling (Univ. Alcalá, KIS 2025)](https://ebuah.uah.es/dspace/handle/10017/67478) (bậc 1, 2025; qua search)
- **GoalEx** (Propose-Assign-Select): đầu vào là corpus kèm một **mục tiêu** bằng ngôn ngữ tự nhiên. Đầu ra là các cụm, mỗi cụm có một mô tả khớp với mục tiêu đó. Chạy đệ quy thì sinh được taxonomy. — [GoalEx README](https://github.com/ZihanWangKi/GoalEx) (bậc 1, EMNLP 2023; đã mở)
- **TnT-LLM** (đã có trong report trước) có bước tóm tắt từng bản ghi trước khi sinh taxonomy theo minibatch. — xem report trước [3][11].

### Nhận định
- **Nhận định:** với đoạn 4–5 câu chứa lệnh, đường dẫn và IP, lý do nên trích ý trước mạnh hơn hẳn so với câu ngắn: embedding nguyên văn bị kéo theo token kỹ thuật và văn phong của người viết. Một câu chuẩn hóa kiểu "Nguyên nhân: …" (dùng prefill như Clio để ép khuôn) đưa mọi bản ghi về cùng một không gian diễn đạt. Bằng chứng trực tiếp cho đúng loại văn bản này chưa có.
- **Nhận định:** nên dùng biến thể "ghép" như Few-shot clustering hoặc paper Alcalá (embedding phát biểu trích ra nối với embedding gốc) thay vì chỉ embed phát biểu. Cách này giữ được tín hiệu khi LLM trích sai.
- **Nhận định:** prompt trích nên là JSON schema với các trường tách biệt, ví dụ `cause` (1 câu, không chứa định danh cụ thể), `action`, `evidence_tokens` (giữ nguyên lệnh/mã lỗi để tra cứu), `confidence`, `n_causes`. Gom cụm chỉ trên `cause`. Tách token kỹ thuật ra trường riêng tương đương bước "mask" của report trước, nhưng làm theo ngữ nghĩa thay vì regex.

### Khoảng trống
- Không đọc được bảng số của IDAS, Few-shot clustering hay Clio vì arXiv/ACL bị chặn. Không có thí nghiệm nào so "embed nguyên văn đoạn dài kỹ thuật" với "embed phát biểu trích ra".
- Không tìm được paper với đúng tên "LLM-based text clustering via summaries" hay "Explanation-based clustering". Bằng chứng gần nhất là paper Alcalá 2025 ở trên.

## 2. Key Point Analysis (KPA)

### Kết luận ngắn
KPA là mẫu "sinh danh sách ý chính → ghép từng văn bản với các ý → đếm" có định nghĩa và metric rõ ràng. Thiết kế của nó hỗ trợ sẵn **đa nhãn** (một văn bản khớp nhiều key point) và **không khớp** (None). Trong dữ liệu ArgKP, khoảng **35%** văn bản không khớp key point nào. Các bản LLM 2024 (PAKPA, QANA) cho thấy LLM sinh key point tốt, nhưng bước ghép bằng LLM thuần không phải lúc nào cũng thắng model chuyên dụng. Mức chắc chắn **cao** về cơ chế (README chính thức), **thấp–trung bình** về số liệu LLM (qua search, mâu thuẫn nhau).

### Phát hiện có nguồn
- Định nghĩa trong shared task 2021: với một tập văn bản ngắn có quan điểm về một chủ đề, đầu ra là "a succinct list of the most prominent key-points in the input corpus, along with their relative prevalence". Track 1 là ghép argument với key point cho sẵn. Track 2 gồm sinh **5–10 key point** cho mỗi chủ đề và lập trường, rồi ghép. — [IBM KPA_2021_shared_task README](https://github.com/IBM/KPA_2021_shared_task) (bậc 1, 2021; đã mở)
- **Đa nhãn và không khớp**: "Given a set of key points for a topic, an argument could be matched to one or more key points, or to none of them." Người gán nhãn được hướng dẫn "mark all of the key points this argument can be associated with, and if none are relevant, select the 'None' option". Đầu ra hệ thống là một **match score cho mỗi cặp** (argument, key point). — [KPA README](https://github.com/IBM/KPA_2021_shared_task) (bậc 1; đã mở)
- **Đánh giá**: ghép mỗi argument với key point có điểm cao nhất, bỏ **50% cặp có điểm thấp nhất** ("we expect any set of arguments to contain some number of unique claims which do not match any of the key points... the fraction arguments not matching any of the given key points is **0.35**, yet ranging widely"), rồi tính mAP strict và relaxed trên 6 tổ hợp chủ đề × lập trường. Các cặp mơ hồ là cặp có từ 15% đến dưới 60% người gán nhãn đánh dấu match. Track 2 còn có bước người chấm xếp hạng các bộ key point, giả định prevalence đã báo là đúng. — [KPA README](https://github.com/IBM/KPA_2021_shared_task) (bậc 1; đã mở)
- Ví dụ đếm (chủ đề "Homeschooling should be banned", phía pro): key point "Mainstream schools are essential to develop social skills" khớp **61** argument, "Parents are not qualified as teachers" khớp 20. — [KPA README](https://github.com/IBM/KPA_2021_shared_task) (bậc 1; đã mở)
- Dataset ArgKP: khoảng **24K cặp** argument/key point trên **28 chủ đề**, mỗi cặp gán match/no-match và lập trường. — [KPA README](https://github.com/IBM/KPA_2021_shared_task) (bậc 1; đã mở)
- Bar-Haim et al. ACL 2020: "a small number of key points per topic is typically sufficient for covering the vast majority of the arguments", và chuyên gia thường đoán trước được các key point. — [From Arguments to Key Points, ACL 2020](https://aclanthology.org/2020.acl-main.371) (bậc 1, 2020; qua search)
- KPA cho review doanh nghiệp ("Every Bite Is an Experience", ACL 2021): precision tại review coverage 0,8 là **0,77** (khách sạn) và **0,83** (nhà hàng). Có người giám sát để cải thiện tập key point thì kết quả tăng đáng kể. — [arXiv 2106.06758](https://arxiv.org/pdf/2106.06758) (bậc 1, 2021; qua search)
- **PAKPA** (ACL 2024) có 3 giai đoạn: (1) prompted ABSA để trích khía cạnh và cảm xúc của từng comment; (2) gom comment theo khía cạnh-cảm xúc; (3) LLM sinh key point cho từng cụm. Như vậy PAKPA chính là extract-then-cluster áp vào KPA. Tác giả lập luận rằng sinh KP từ nguyên câu "often leading to KPs with overlapping and hallucinated opinions, and inaccurate quantification" (qua search). Kết quả SOTA trên Yelp và SPACE (qua search). — [PAKPA README](https://github.com/antangrocket1312/PAKPA) (bậc 1, 2024; đã mở), [ACL 2024.acl-long.576](https://aclanthology.org/2024.acl-long.576) (bậc 1; qua search)
- **QANA** (2024): ghép zero-shot bằng câu hỏi do LLM (GPT-4) sinh cộng với embedding lớn. Theo tác giả, kết quả "comparable to state-of-the-art supervised models" về mAP trên ArgKP-2021. — [QANA, arXiv 2404.18371](https://arxiv.org/pdf/2404.18371) (bậc 1, 2024; qua search)
- Nguồn mâu thuẫn về LLM ghép trực tiếp: một luận văn TU Delft dẫn lại van der Meer et al. rằng GPT-3.5-turbo sinh key point tốt nhưng ghép kém (mAP khoảng 0,17–0,46, so với tối đa 0,82 của RoBERTa), có thể do thiết lập JSON và prompt theo batch. Cũng luận văn này báo GPT-3.5/o4-mini zero-shot vượt RoBERTa (macro-F1 tới 0,880) trên transcript quốc hội. — [TU Delft repository](https://repository.tudelft.nl/file/File_b180a9f8-d055-4d4e-a524-13c8ea1ce70d) (bậc 2, luận văn, ~2025; qua search, không mở được)
- Một benchmark 2026 cho rằng các bộ dữ liệu KPA cũ có vấn đề về nhóm, trùng lặp, coverage và ánh xạ. Benchmark này gán nhãn lại ArgKP21 và đánh giá LLM với greedy decoding ở temperature 0. — [Key Point Analysis Needs Structure Recovery, arXiv 2608.25854](https://arxiv.org/pdf/2608.25854) (bậc 1, 2026; qua search; ID arXiv chưa kiểm được)

### Nhận định
- **Nhận định:** KPA khớp với bài toán "đếm nguyên nhân" hơn topic modeling, vì đầu ra chính là danh sách phát biểu kèm số đếm. Ngưỡng match score cho phép báo riêng phần "không khớp / ý hiếm", thay vì ép mọi bản ghi vào một cụm.
- **Nhận định:** đa nhãn khiến tổng các tần suất vượt quá N. Báo cáo cần nêu rõ mẫu số: "% bản ghi có nhắc nguyên nhân X", không phải phân bố chia 100%.
- **Nhận định:** metric của KPA (precision tại một mức coverage; bỏ phần đuôi điểm thấp) dùng lại được làm phép kiểm tra thủ công: lấy mẫu cặp (bản ghi, nhãn) rồi đo precision, và đo coverage bằng % bản ghi được gán ít nhất một nhãn.
- **Nhận định:** sinh key point "theo stance/topic" của KPA chính là gom trong từng nhóm theo cột ngữ cảnh (xem mục 4).

### Khoảng trống
- Không mở được paper "Prompted opinion summarization" hay bất kỳ bảng số nào của các paper KPA dùng LLM. Số của van der Meer chỉ thấy qua một luận văn dẫn lại.

## 3. Mã hóa định tính / phân tích chủ đề có LLM hỗ trợ ở quy mô nhỏ (bổ sung theo yêu cầu điều phối)

### Kết luận ngắn
Ở quy mô vài trăm bản ghi, mô hình tham chiếu là **TopicGPT** (sinh chủ đề từ mẫu → tinh chỉnh → gán kèm trích dẫn → sửa) và **LLooM** (tóm tắt thành ý → gom → tổng hợp khái niệm có tiêu chí bao gồm rõ ràng → chấm từng bản ghi). Độ đồng thuận giữa LLM và người khi mã hóa theo codebook thường ở mức trung bình đến khá (κ khoảng 0,4–0,9 tùy nghiên cứu). Các nguồn đều khuyên dùng LLM để hỗ trợ, chạy nhiều lần, và luôn có người duyệt. Mức chắc chắn **trung bình**: nhiều nghiên cứu cùng chiều, nhưng số liệu không so sánh được với nhau và đều qua search.

### Phát hiện có nguồn
- **TopicGPT** (NAACL 2024) có 5 hàm: `generate_topic_lvl1` (chủ đề cấp cao), `generate_topic_lvl2`, `refine_topics` ("merging near duplicates and removing topics with low frequency"), `assign_topics` ("along with a quote that supports the assignment"), `correct_topics` ("reprompting the model so that the final topic assignment is grounded in the topic list"). README khuyên gán bằng model yếu hơn để tiết kiệm, chạy thử trên tập con trước. Hỗ trợ vLLM. Kèm metric ARI, Harmonic Purity, NMI. — [topicGPT README](https://github.com/chtmp223/topicGPT) (bậc 1, 2024-11; đã mở)
- Kết quả TopicGPT: harmonic purity **0,74** so với ground truth Wikipedia, baseline mạnh nhất **0,64** (qua search, abstract). Kiểm tra độ bền gồm chuyển prompt sang dataset khác, thêm hoặc bớt chủ đề mồi, xáo thứ tự tài liệu; chất lượng "holds up" (qua search). Không có đo lường biến thiên giữa các lần chạy lặp. — [TopicGPT, ACL 2024.naacl-long.164](https://preview.aclanthology.org/naacl24-info/2024.naacl-long.164) (bậc 1, 2024; qua search)
- **LLooM** (CHI 2024) dùng GPT-4o và GPT-4o mini để "synthesize sampled text spans, generate concepts defined by explicit criteria, apply concepts back to data, and iteratively generalize to higher-level concepts". Workbench hiển thị prevalence của từng khái niệm, cùng **ma trận khái niệm × "slice columns" do người dùng chọn từ metadata**. Với mỗi bản ghi: bullet summary, điểm, đoạn văn được highlight, lý do chấm. — [LLooM README](https://github.com/michelle123lam/lloom) (bậc 1, 2024; đã mở)
- Đánh giá LLooM: trên tập Bills, coverage khác biệt có ý nghĩa giữa các phương pháp (LLooM vs GPT-4 Turbo p<.02). Trên tập Wiki, khác biệt có ý nghĩa duy nhất là giữa BERTopic và GPT-4; LLooM không vượt có ý nghĩa. Về định tính, chủ đề của BERTopic mơ hồ hơn, còn GPT-4 đôi khi gộp nhiều chủ đề làm một. — [Concept Induction (LLooM), arXiv 2404.12259](https://arxiv.org/abs/2404.12259v1) (bậc 1, 2024; qua search)
- **LLM so với người khi mã hóa** (các nghiên cứu khác nhau, không so sánh trực tiếp được):
  - QualiGPT: giữa người với người, κ = 0,73 (deductive). GPT-4 so với người: Fleiss κ 0,44–0,50 (deductive), Cohen κ 0,57 (inductive). LLM nhất quán nội bộ hơn người khi áp codebook. — [QualiGPT, arXiv 2407.14925](https://arxiv.org/pdf/2407.14925) (bậc 1, 2024; qua search); [AHFE/CMS 2025](https://openaccess.cms-conferences.org/publications/book/978-1-964867-71-7/article/978-1-964867-71-7_14) (bậc 1; qua search)
  - JMIR Formative 2026: chỉ **31%** mã inductive của GPT-4o khớp mã của người, 26% là phương án thay thế hợp lý, **42%** không hợp lý. — [JMIR Formative Research 2026;e85572](https://formative.jmir.org/2026/1/e85572/PDF) (bậc 1, 2026; qua search)
  - Nhiều LLM cho thematic analysis: κ > 0,80 (Gemini 2.5 Pro 0,907). Tác giả lưu ý κ giữa người với người trong thematic analysis thường chỉ 0,40–0,60. — [arXiv 2512.20352](https://arxiv.org/html/2512.20352v2) (bậc 1, 2025-12; qua search)
  - Physics education: GPT-4o/4.5 sau khi tinh chỉnh prompt đạt κ > 0,6 ở 3 chủ đề và mức trung bình ở 1 chủ đề. — [arXiv 2508.14764](https://arxiv.org/html/2508.14764v2) (bậc 1, 2025; qua search)
- **LACA** (RTI, Chew et al. 2023): GPT-3.5 mã hóa deductive đạt đồng thuận "comparable to human coders". Quy trình khác chuẩn ở 3 điểm: đồng phát triển codebook với LLM, kiểm reliability giữa người và LLM, rồi để LLM mã hóa tập cuối. Phương pháp giúp "identify codes for which an LLM is randomly guessing". Hạn chế: model bị ép chọn Yes/No, không có lựa chọn "không biết". — [LACA, arXiv 2306.14924](https://arxiv.org/pdf/2306.14924) (bậc 1, 2023-06; qua search); [RTI](https://www.rti.org/publication/llm-assisted-content-analysis-using-large-language-models-to-supp) (bậc 1; qua search)
- **Tai et al. 2024** (IJQM): đưa 3 văn bản cùng codebook vào LLM, hỏi code có xuất hiện không và yêu cầu bằng chứng. Mỗi văn bản chạy **160 lần**, mỗi lần coi như một coder mới. Kết luận: LLM mã hóa deductive được và "reduce analysis misalignment". — [Tai et al., IJQM 23 (2024)](https://doaj.org/article/25c5015365a0467da462b8a73e3e2f56) (bậc 1, 2024; qua search)
- Temperature: với codebook 8 mã, 6 model mã nguồn mở và 18 cấu hình, temperature ảnh hưởng tới việc các agent có đạt đồng thuận hay không nhưng "did not reliably improve coding accuracy". — [arXiv 2507.11198](https://arxiv.org/pdf/2507.11198) (bậc 1, 2025; qua search)
- Ổn định taxonomy do LLM sinh: F1 cao nhưng consistency giữa các lần sinh dao động mạnh, và cấu hình cho taxonomy phong phú nhất không phải là cấu hình ổn định nhất. Kết luận: một lần chạy không đủ tin cậy. — nguồn qua search, có thể là [CEUR-WS Vol-4293 paper38](https://ceur-ws.org/Vol-4293/paper38.pdf) (bậc 1, 2025; qua search, chưa xác minh đúng paper)
- Khuyến nghị thực hành: LLM "can support, but not substitute" phân tích diễn giải. Nhà nghiên cứu nên tự đọc dữ liệu trước khi gọi model, đặt các điểm kiểm duyệt (checkpoint) do người phê duyệt, và rà soát codebook máy sinh vì nó hay có mã chồng chéo hoặc lệch cấp trừu tượng. Few-shot với codebook định sẵn "often yields overgeneralized or incorrect labels". — [LLM-Assisted Thematic Analysis, arXiv 2511.14528](https://arxiv.org/pdf/2511.14528) (bậc 1, 2025-11; qua search); [DeTAILS, arXiv 2510.17575](https://arxiv.org/pdf/2510.17575) (bậc 1, 2025-10; qua search)

### Nhận định
- **Nhận định:** với vài trăm bản ghi, quy trình hợp lý là: (1) người đọc khoảng 50 bản ghi; (2) LLM đề xuất codebook từ toàn bộ hoặc từ mẫu, mỗi mã có định nghĩa, tiêu chí bao gồm/loại trừ và ví dụ (kiểu LLooM); (3) người sửa codebook; (4) LLM gán đa nhãn, kèm trích dẫn bằng chứng và lựa chọn "không thuộc mã nào" (kiểu TopicGPT/KPA); (5) chạy gán 3–5 lần, đo độ nhất quán; (6) người duyệt các bản ghi không nhất quán và một mẫu ngẫu nhiên, tính κ.
- **Nhận định:** codebook nên được "khóa" giữa các kỳ phân tích để số đếm so sánh được theo thời gian. Mã mới chỉ thêm qua bước người duyệt, giống bước "chốt taxonomy rồi mới gán" của report trước.

### Khoảng trống
- Không đọc được bảng số của TopicGPT/LLooM. Không có nghiên cứu nào đo trực tiếp độ ổn định giữa các lần chạy TopicGPT. Các nghiên cứu về κ dùng dữ liệu phỏng vấn/khảo sát, không phải ghi chú kỹ thuật.

## 4. Dùng các cột ngữ cảnh

### Kết luận ngắn
Các hệ thống tham chiếu đều phân tích **trong từng nhóm** do metadata xác định. KPA ghép argument chỉ với key point "under the same topic and in the same stance"; PAKPA làm theo từng doanh nghiệp; LLooM có ma trận khái niệm × slice column. Chưa có benchmark định lượng nào đo tác dụng của việc đưa cột có cấu trúc vào prompt trích ý. Mức chắc chắn **trung bình** về thiết kế, **thấp** về hiệu quả định lượng.

### Phát hiện có nguồn
- KPA: "report for each argument its match score for each of the key points **under the same stance** towards the topic". Key point được sinh riêng cho mỗi topic × stance. — [KPA README](https://github.com/IBM/KPA_2021_shared_task) (bậc 1; đã mở)
- PAKPA: "Given reviews for a business entity", sinh KP cho từng thực thể và gom theo khía cạnh-cảm xúc. — [PAKPA README](https://github.com/antangrocket1312/PAKPA) (bậc 1; đã mở)
- LLooM: "Aids comparison between concepts and other metadata columns with user-defined slice columns" — khái niệm được sinh **toàn cục**, rồi đếm cắt lát theo metadata. — [LLooM README](https://github.com/michelle123lam/lloom) (bậc 1; đã mở)
- Clio: mỗi facet (chủ đề, ngôn ngữ, mức độ...) được trích riêng, và giao diện cho khám phá theo từng chiều. — [Anthropic Clio](https://www.anthropic.com/research/clio) (bậc 1; đã mở)
- Lưu ý về độ tin cậy của metadata: UiPath thấy xác suất cả 3 trường metadata (product, deployment type, issue type) cùng đúng lúc tạo ticket là **dưới 50%**, nên họ dựng trợ lý suy ra các trường này từ mô tả. Họ cũng ràng buộc đầu ra vào các tổ hợp hợp lệ và lọc theo ngưỡng confidence. — [UiPath Engineering blog](https://engineering.uipath.com/enterprise-case-classification-agent-support-ticket-routing-with-ai-de5c822d8153) (bậc 2, vendor; qua search)

### Nhận định
- **Nhận định:** nên sinh taxonomy **toàn cục**, rồi thống kê ý nghĩa × nhóm như LLooM làm. Gom riêng trong từng nhóm sẽ sinh ra các nhãn trùng nghĩa giữa các nhóm và nhóm nhỏ không đủ dữ liệu, trừ khi các nhóm thực sự có tập nguyên nhân tách biệt (giống stance của KPA).
- **Nhận định:** đưa cột ngữ cảnh vào prompt trích ý theo dạng khối có nhãn (`<context>loại bản ghi: …; nguồn: …</context>`) giúp LLM hiểu từ viết tắt. Nhưng cần cảnh báo trong prompt rằng metadata có thể sai (theo dữ liệu UiPath), và không cho LLM suy nguyên nhân chỉ từ metadata.

### Khoảng trống
- Không tìm thấy thí nghiệm có kiểm soát nào so "có metadata trong prompt" với "không có" cho bài toán trích hoặc gom ý.

## 5. Chi phí và latency ở quy mô 200 / 500 / 2.000 bản ghi

### Kết luận ngắn
Với giá Haiku 5.5 (2026-10), mọi phương án đều dưới **$1** cho 2.000 bản ghi, kể cả khi chạy lặp 5 lần. Chi phí tiền không còn là tiêu chí. Tiêu chí thật là chất lượng, độ ổn định và thời gian chờ. Gọi theo từng bản ghi qua API xong trong vài phút (giới hạn 1.000 RPM ở tier thấp nhất). Gọi "cả corpus trong một prompt" rẻ và nhanh ở 200 bản ghi, nhưng có rủi ro chất lượng đã được ghi nhận khi nhiều mục nằm trong một prompt, và đắt hơn khi prompt vượt 100k token. Mức chắc chắn **cao** về giá và rate limit (docs đã mở), **trung bình** về latency (giả định tốc độ).

### Phát hiện có nguồn
- **Giá Claude Haiku 5.5**: $0,10/MTok input và $0,50/MTok output cho prompt ≤ 100.000 token. Prompt > 100.000 token tính **$0,50 / $2,50**. Cache write 5 phút $0,125, 1 giờ $0,20, cache read $0,01. Batch: $0,05 / $0,25 (≤100k) và $0,25 / $1,25 (>100k). "A request whose prompt is over 100,000 tokens pays higher prices... including cache reads and cache writes." Sonnet 5.5 giá $2 / $10. — [Pricing, Claude Docs](https://platform.claude.com/docs/en/about-claude/pricing) (bậc 1, đọc 2026-10-21; đã mở)
- **Haiku 5.5**: context window **1M token**, max output **128K token**, "Comparative latency: Fastest", ID `claude-haiku-5-5`. — [Models overview, Claude Docs](https://platform.claude.com/docs/en/about-claude/models) (bậc 1, đọc 2026-10-21; đã mở)
- **Rate limit Haiku 5.5**: Start tier **1.000 RPM / 2.000.000 ITPM / 400.000 OTPM**; Build tier 5.000 / 5M / 1M; Scale tier 10.000 / 10M / 2M. Token đọc từ cache không tính vào ITPM. — [Rate limits, Claude Docs](https://platform.claude.com/docs/en/api/rate-limits) (bậc 1, đọc 2026-10-21; đã mở)
- Batch API giảm 50%, đa số batch xong trong 1 giờ. Cache tối thiểu 512 token trên Haiku 5.5. — report trước [14][56] (bậc 1)
- **llama.cpp, ví dụ trong README của llama-bench** (phần cứng không ghi rõ, model cũ): llama 7B Q4_0 trên **CPU** đạt tg khoảng **16 t/s** và pp64 khoảng **33–59 t/s** với 16–32 luồng. qwen2 7B Q4_K_M trên **CUDA** đạt pp512 **7.340 t/s**, tg128 **120,6 t/s** (một luồng sinh). — [llama-bench README](https://raw.githubusercontent.com/ggml-org/llama.cpp/master/tools/llama-bench/README.md) (bậc 1, không rõ ngày; đã mở; chỉ là ví dụ đầu ra)
- CPU hiện đại với 8B Q4_K_M: khoảng 3,2 t/s (Xeon 4 nhân, DDR4) đến 10–26 t/s (Ryzen 7950X 16 nhân); các nguồn lệch nhau. — [DEV Community](https://dev.to/manoir_yantai_f22f01340f0/-running-llms-on-cpu-in-2026-real-benchmarks-from-a-4-core-xeon-server-a-4-57c6), [markaicode](https://markaicode.com/benchmarks/llamacpp-tokens-per-second-benchmark/) (bậc 3; qua search, chỉ để định cỡ)
- vLLM Llama-3.1-8B trên 1×H100: throughput sinh khoảng 6.067 tok/s. — report trước [59] (bậc 2, qua search)
- **Nhiều mục trong một prompt làm giảm chất lượng**: Batch Prompting (Cheng et al.) giảm tới 5× chi phí với 6 mẫu/batch, "better or comparable", nhưng hiệu năng giảm khi tăng số mẫu và có lan truyền lỗi giữa các mẫu. BatchPrompt (ICLR 2024) kết luận gộp dữ liệu vào ngữ cảnh dài "will inevitably lead to worse performance" và phụ thuộc thứ tự/vị trí. Một paper 2026 thấy ổn định khi b < 16 (AGNews) rồi giảm mạnh; model nhỏ giảm nhiều hơn. BatchGEMBA: một biến thể GPT-4o chỉ còn 2% chất lượng ở batch 16, trong khi GPT-4o-mini ổn định. — [Batch Prompting, arXiv 2301.08721](https://arxiv.org/pdf/2301.08721) (bậc 1, 2023; qua search); [BatchPrompt, Microsoft Research](https://www.microsoft.com/en-us/research/?p=1014516) (bậc 1, 2024; qua search); [arXiv 2605.28268](https://arxiv.org/pdf/2605.28268) (bậc 1, 2026; qua search); [BatchGEMBA, arXiv 2503.02756](https://arxiv.org/pdf/2503.02756) (bậc 1, 2025; qua search)
- Ngữ cảnh dài: LongICLBench (28–174 nhãn, prompt 2K–50K token) cho thấy thiên lệch về nhãn xuất hiện sau và hiệu năng giảm sau khoảng 20K token. Nhiều model tụt mạnh từ 16k token ở các tác vụ cần xét toàn bộ ví dụ. — [Many-shot ICL for long-context evaluation, arXiv 2411.07130](https://arxiv.org/pdf/2411.07130) (bậc 1, 2024; qua search)

### Tính toán (Nhận định; giả định ghi rõ)
Giả định: mỗi bản ghi 4–5 câu tiếng Việt lẫn ký hiệu kỹ thuật ≈ **250 token**, cộng 30 token cột ngữ cảnh = **280 token**. System prompt (hướng dẫn, schema, ví dụ, hoặc codebook) ≈ **1.000 token**. Đầu ra trích JSON ≈ **80 token/bản ghi**; đầu ra gán nhãn ≈ **15 token/bản ghi**. Giá Haiku 5.5 như trên. Đã chạy lại phép tính bằng Python.

**A. Trích hoặc gán theo từng bản ghi** (N request): input = N × 1.280 token, output = N × 80.
- 200: 256k × $0,10/M = $0,026; 16k × $0,50/M = $0,008 → **≈ $0,034** (cache system prompt: ≈ $0,016; batch: ≈ $0,017)
- 500: 640k → $0,064; 40k → $0,020 → **≈ $0,084** (cache ≈ $0,039)
- 2.000: 2,56M → $0,256; 160k → $0,080 → **≈ $0,34** (cache ≈ $0,16)
- Latency: Start tier 1.000 RPM nên 2.000 request cần ≥ 2 phút. ITPM: 2.000 × 280 = 560k token chưa cache, dưới 2M/phút. Chạy với độ song song khoảng 20–50 thì 200 bản ghi xong dưới 1 phút và 2.000 bản ghi xong khoảng 2–4 phút. Giả định thời gian mỗi request vài giây; không có số chính thức về tốc độ sinh của Haiku 5.5. Chạy lặp 5 lần để đo độ ổn định: ≤ $1,7 với 2.000 bản ghi.

**B. Cả corpus trong một prompt** (gọi 1: sinh taxonomy, output khoảng 2.000 token; gọi 2: gán toàn bộ, output 15 × N):
- 200: corpus 56k + 1k = 57k token (< 100k). Input 2 × 57k × $0,10/M = $0,011; output 5k × $0,50/M = $0,0025 → **≈ $0,014**, chỉ 2 request.
- 500: 141k token, **vượt 100k** nên tính giá $0,50 / $2,50. Input 282k × 0,50 = $0,141; output 9,5k × 2,50 = $0,024 → **≈ $0,165**, gấp khoảng 2 lần phương án A.
- 2.000: 561k token (vẫn dưới context 1M). Input 1,12M × 0,50 = $0,56; output 32k × 2,50 = $0,08 → **≈ $0,64**. Output 32k token nằm dưới giới hạn 128K, nhưng sinh tuần tự trong một request. Ở tốc độ giả định 100–200 tok/s thì mất khoảng 3–5 phút, lâu hơn A chạy song song.
- **B′, chia khúc dưới 100k token** (khoảng 300 bản ghi/khúc, taxonomy sinh từ một khúc): 500 → ≈ $0,028; 2.000 → ≈ $0,083. Rẻ nhất, nhưng mỗi khúc là một "batch prompt" 300 mục, đúng vùng mà các nghiên cứu trên ghi nhận chất lượng giảm.

**C. Chỉ gọi theo cụm** (embed rồi k-means với k = N/10 như OpenClio; mỗi lần đặt tên gồm 10 mẫu trong cụm và 10 mẫu ngoài cụm, khoảng 500 token hướng dẫn, 100 token output):
- Mẫu là văn bản thô (280 token): 2.000 bản ghi → 200 cụm × 6.100 token ≈ $0,13 (lấy mẫu 5 lần như OpenClio: ≈ $0,66). 200 bản ghi → ≈ $0,013.
- Mẫu là phát biểu đã trích (≈ 40 token): 2.000 bản ghi → ≈ $0,036, cộng thêm chi phí A nếu phải trích trước.

**Local**, 2.000 bản ghi, phần không cache = 560k token prefill, 160k token sinh:
- GPU với vLLM (prefill khoảng 7.000 t/s, sinh theo batch khoảng 6.000 t/s): ≈ 76 s + 26 s ≈ **2 phút**. 200 bản ghi: khoảng 10 s.
- llama.cpp trên GPU, sinh một luồng 120 t/s: phần sinh ≈ 22 phút (cần bật nhiều slot song song để rút ngắn).
- llama.cpp trên CPU (pp khoảng 50 t/s, tg khoảng 16 t/s theo ví dụ trong README): prefill ≈ 3,1 giờ và sinh ≈ 2,8 giờ, tổng **≈ 6 giờ**. 200 bản ghi khoảng 35 phút. **Prefill trên CPU là nút cổ chai**, vì bản ghi dài 280 token lớn hơn nhiều so với 80 token đầu ra.

### Nhận định
- **Nhận định:** ở quy mô vài trăm đến 2.000 bản ghi, gọi LLM cho từng bản ghi (A) là hợp lý cả về tiền lẫn thời gian, và còn đủ ngân sách để chạy lặp 3–5 lần đo độ nhất quán. Lập luận "chỉ gọi theo cụm" của report trước (tối ưu cho hàng triệu dòng) không còn cần thiết ở quy mô này.
- **Nhận định:** "một prompt cho cả corpus" phù hợp nhất cho bước **khám phá taxonomy** (LLM thấy toàn cảnh 200–300 bản ghi). Không nên dùng nó cho bước **gán nhãn cuối**: vượt 100k token thì đắt gấp 5 lần đơn giá, và chất lượng gán nhiều mục trong một prompt đã được ghi nhận là giảm. Kết hợp hợp lý: B để đề xuất codebook, A để gán, C để kiểm tra chéo (cụm embedding nào chứa nhiều nhãn khác nhau là dấu hiệu codebook có vấn đề).
- **Nhận định:** on-prem nên dùng GPU với vLLM. CPU chỉ chạy được cho vài trăm bản ghi hoặc chạy qua đêm.

### Khoảng trống
- Không có số chính thức về tốc độ output (tok/s) hay thời gian phản hồi của Haiku 5.5. Thời gian ở phương án A và B dựa trên giả định.
- Số token thực của văn bản tiếng Việt lẫn ký hiệu kỹ thuật theo tokenizer Claude chưa đo; 250 token/bản ghi chỉ là ước lượng.

## 6. Độ tin cậy

### Kết luận ngắn
Các biện pháp có nguồn: lấy mẫu nhiều lần rồi bỏ phiếu đa số (mặc định 5 lần trong OpenClio); đo độ nhất quán qua nhiều lần chạy (Tai: 160 lần; Pangakis: ≥ 3 lần, theo report trước); ràng buộc đầu ra vào tập nhãn đã chốt (structured outputs/enum); cho phép "không thuộc mã nào"; người kiểm tra mẫu bằng κ hoặc precision@coverage kiểu KPA. Temperature 0 không bảo đảm kết quả đúng. Mức chắc chắn **trung bình**.

### Phát hiện có nguồn
- OpenClio lấy mẫu tên cụm 5 lần và việc gán cụm vào tầng cao 5 lần, chọn đáp án phổ biến nhất, ở temperature 0,7, seed cố định. — [OpenClio opencliotypes.py](https://raw.githubusercontent.com/Phylliida/OpenClio/main/openclio/opencliotypes.py) (bậc 1; đã mở)
- Tai et al.: chạy 160 lần trên mỗi văn bản, coi mỗi lần là một coder. — [IJQM 2024](https://doaj.org/article/25c5015365a0467da462b8a73e3e2f56) (bậc 1; qua search)
- Temperature ảnh hưởng tới đồng thuận nhưng không cải thiện accuracy một cách tin cậy. — [arXiv 2507.11198](https://arxiv.org/pdf/2507.11198) (bậc 1, 2025; qua search)
- LACA: phát hiện mã mà LLM "đoán ngẫu nhiên" bằng kiểm định đồng thuận giữa người và LLM. — [arXiv 2306.14924](https://arxiv.org/pdf/2306.14924) (bậc 1; qua search)
- TopicGPT: bước `correct_topics` gọi lại model khi nhãn gán không có trong danh sách. Mỗi lần gán kèm một trích dẫn làm bằng chứng. — [topicGPT README](https://github.com/chtmp223/topicGPT) (bậc 1; đã mở)
- KPA: điểm match liên tục cho từng cặp, ngưỡng loại 50% đuôi điểm thấp, cặp mơ hồ (15–60% người đồng ý) tách riêng khi chấm. — [KPA README](https://github.com/IBM/KPA_2021_shared_task) (bậc 1; đã mở)
- Report trước đã có: consistency score của Pangakis (+19,4 điểm phần trăm accuracy ở mẫu nhất quán), structured outputs với enum, và hiệu chỉnh tỷ lệ. — report trước [64][65][66]

### Nhận định
- **Nhận định:** sau khi chốt codebook, nên gán bằng enum hoặc structured output, chạy 3 lần (temperature mặc định hoặc thấp), lấy đa số, và gắn cờ "không nhất quán" cho bản ghi có ít hơn 2/3 lần chạy đồng ý. Con số tần suất nên báo dưới dạng khoảng: cận dưới là số bản ghi nhất quán, cận trên là số bản ghi có ít nhất một lần chạy gán nhãn đó. Ở 2.000 bản ghi, chi phí cho cách này chỉ khoảng $0,5–1.
- **Nhận định:** bước sinh taxonomy kém ổn định hơn bước gán. Nên sinh taxonomy 2–3 lần (với mẫu xáo thứ tự khác nhau), hợp nhất bằng người hoặc LLM, rồi khóa lại.

### Khoảng trống
- Không có nghiên cứu nào đo trực tiếp độ ổn định giữa các lần chạy khi trích "nguyên nhân" từ ghi chú kỹ thuật. Chưa kiểm chứng được temperature 0 trên Haiku 5.5 có cho kết quả tất định hay không.

## Truy vấn đã chạy
- key point analysis LLM 2024 matching coverage (standard)
- Bar-Haim "From Arguments to Key Points" key point matching coverage (standard)
- LLM generated explanations as features text clustering summaries improve over raw embeddings (standard)
- LLM key point analysis reviews PAKPA aspect-based prompted (standard)
- "Every Bite Is an Experience" key point analysis business reviews coverage results (standard)
- TopicGPT Pham 2024 NAACL harmonic purity assignment results (standard)
- LLM qualitative coding thematic analysis agreement human coders Cohen kappa 2024 2025 (standard)
- Clio Anthropic synthetic conversations reconstruction accuracy 94% cluster evaluation (standard)
- Viswanathan few-shot clustering keyphrase expansion results Bank77 CLINC improvement over E5 embeddings (standard)
- IDAS intent discovery abstractive summarization results NMI improvement summaries vs utterances (standard)
- summarize then cluster long documents LLM summaries embedding clustering performance comparison 2024 (standard)
- LLooM concept induction evaluation BERTopic GPT-4 coverage results CHI 2024 (standard)
- key point generation matching large language models ArgKP GPT-4 evaluation 2024 2025 (standard)
- LLM deductive coding codebook consistency repeated runs temperature intercoder reliability study (standard)
- batch prompting multiple samples one prompt accuracy degradation batch size Cheng 2023 (standard)
- llama.cpp CPU benchmark 8B Q4_K_M tokens per second prompt processing text generation (standard)
- long-context LLM classify hundreds of items single prompt per-item accuracy drop many instructions (standard)
- LLM topic generation reproducibility across runs TopicGPT stability different seeds topics vary (standard)
- "explanations" BERTopic Llama-3.1 DeepSeek-R1 zero-shot topic coherence user-created data 2025 clustering (standard)
- LLM-assisted thematic analysis best practices codebook human review guidelines 2025 qualitative researchers (standard)
- Chew 2023 LLM-assisted content analysis LACA deductive coding agreement codebook RTI (standard)
- Tai 2024 International Journal of Qualitative Methods large language models aid analysis textual data multiple iterations deductive coding (standard)
- PAKPA results Yelp SPACE textual entailment coverage precision KP quantification hallucination (standard)
- Bar-Haim 2021 "Every Bite" key point analysis Yelp reviews collective key point mining (standard)
- LLM classification include metadata context in prompt improves accuracy structured fields ticket category (standard)
- Đã mở trực tiếp (curl/raw GitHub): OpenClio README, prompts.py, opencliotypes.py; IBM KPA_2021_shared_task README; PAKPA, topicGPT, LLooM, IDAS, few-shot-clustering, GoalEx README; llama-bench README; Claude Docs pricing, rate-limits, models; anthropic.com/research/clio. Bị chặn: arxiv.org, aclanthology.org, openreview, semanticscholar, *.github.io, hci.stanford.edu, par.nsf.gov, biorxiv, nec.com, rti.org, census.gov, engineering.uipath.com, api.github.com.
