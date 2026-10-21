# Nghiên cứu thực nghiệm: LLM làm content analysis / thematic analysis quy nạp (2023–2026)

> **Giới hạn truy cập (đọc trước):** trong phiên này `WebFetch` không phân giải được DNS cho bất kỳ host nào (arxiv.org, jmir.org, pmc.ncbi.nlm.nih.gov, qualitative-research.net, census.gov, cả en.wikipedia.org đều `ENOTFOUND`), và `curl` qua proxy bị từ chối 403 với mọi host trừ GitHub/PyPI. Vì vậy **không mở được toàn văn paper nào**. Mọi số liệu dưới đây lấy từ **trích đoạn/tóm tắt do công cụ WebSearch trả về** (thường là abstract, đôi khi là câu trích nguyên văn từ thân bài). Mỗi dòng đều ghi "(qua search)". Số nào chỉ thấy trong nguồn thứ cấp dẫn lại thì ghi rõ "thứ cấp". Writer nên coi bảng này là bằng chứng mức abstract, không phải mức bảng số trong paper.

## Câu hỏi phụ 4a — Danh mục nghiên cứu: LLM làm bước nào, đo gì, được bao nhiêu

### Kết luận ngắn
Có khoảng 15 nghiên cứu thực nghiệm 2023–2026 cho LLM làm một phần chuỗi quy nạp (cô đọng → sinh phạm trù → định nghĩa → gán → đếm). Mẫu hình nhất quán: **gán mã theo codebook đã có (deductive) đạt đồng thuận ngang người; tự sinh phạm trù (inductive) thì khớp người một phần (khoảng 1/3 đến 3/4 phạm trù), biến động theo model và theo lần chạy.** Mức chắc chắn: trung bình — mẫu hình lặp lại qua nhiều nghiên cứu độc lập, nhưng phần lớn dữ liệu nhỏ (1 transcript, 40 tin nhắn), và tôi chỉ đọc được abstract/trích đoạn.

### Phát hiện có nguồn

**LACA — Chew, Bollenbacher, Wenger, Speer, Kim (RTI), 2023**
- Là phương pháp **deductive**, không quy nạp: LLM (GPT-3.5) "co-development of the codebook", kiểm độ tin cậy người–LLM, rồi LLM mã hóa toàn bộ thay người; thử trên 4 bộ dữ liệu công khai (báo cáo, tin tức, blog, mạng xã hội), case study là tweet của Trump — [arXiv 2306.14924](https://arxiv.org/pdf/2306.14924) (bậc 1, 2023-06, qua search)
- Dùng Gwet's AC1 thay Cohen's κ vì "many of the codes are rare", tránh nghịch lý "high agreement, low reliability". AC1 người–model "generally high across codes (>0.76)", trừ các mã trượt kiểm định "randomly guessing": HSTG 0,18; ATSN 0,58; CAPT 0,36; INDV 0,50, trong khi người–người trên cùng mã là HSTG 0,96, ATSN 1,00; AC1 người–người nói chung >0,73 — [arXiv 2306.14924](https://arxiv.org/pdf/2306.14924) (bậc 1, 2023, qua search; trích đoạn có vẻ từ thân bài, chưa đối chiếu được bảng)
- Tác giả tự giới hạn: chỉ thử ChatGPT; việc người đọc ít đi "may limit theory development and the discovery of themes"; LLM nên tăng tốc các giai đoạn lặp lại về sau, không thay người mã hóa — [arXiv 2306.14924](https://arxiv.org/abs/2306.14924v1) (bậc 1, 2023, qua search)
- **Đã xác minh lại so với report cũ:** LACA đúng là deductive (tiêu đề "…to Support Deductive Coding"); bước "LLM cùng phát triển codebook" không phải là để LLM tự rút phạm trù từ dữ liệu.

**Bijker, Merkouris, Dowling, Rodda — "ChatGPT for Automated Qualitative Research: Content Analysis", JMIR 2024;26:e59050** (gần nhất với content analysis quy nạp kiểu Elo & Kyngäs)
- Dữ liệu: 537 bài forum (tiếng Anh) về giảm đường; một số nguồn thứ cấp ghi 539 — [JMIR](https://www.jmir.org/2024/1/e59050) (bậc 1, 2024-07, qua search)
- Model: "ChatGPT, model 4o (March 2024 Version)", truy vấn 31/3–2/4/2024 — [JMIR PDF](https://www.jmir.org/2024/1/e59050/PDF) (bậc 1, qua search)
- Các bước LLM làm: (1) sinh **condensed meaning units** từ bài viết; (2) dựng **10 phiên bản** coding scheme quy nạp và 10 phiên bản coding scheme diễn dịch không ràng buộc (theo Theoretical Domains Framework) từ một tập con; (3) gán mã — [JMIR](https://www.jmir.org/2024/1/e59050) (bậc 1, qua search). Một nguồn thứ cấp nói LLM gom meaning units của tập con 20% thành phạm trù và cần chỉ dẫn rõ "to ensure that there was no overlap between the categories" (thứ cấp, chưa xác nhận con số 20%).
- Kết quả: "Overall kappa-scores for inter-coder agreement ranged from 0.72-0.82 across inductive coding schemes and from 0.58-0.73 across unconstrained coding schemes and structured coding matrix"; κ theo từng phạm trù 0,67–0,95 (quy nạp) và 0,13–0,87 (diễn dịch); độ chính xác phát hiện cơ chế thay đổi 66–88% — [JMIR Preprint #59050](https://preprints.jmir.org/preprint/59050) và [JMIR PDF](https://www.jmir.org/2024/1/e59050/PDF) (bậc 1, 2024, qua search). Một bài dẫn lại ghi 0,69–0,84 và 0,52–0,73 (thứ cấp, lệch với abstract; ưu tiên abstract).
- Kết luận tác giả: ChatGPT làm tốt hơn khi "developing an inductive coding scheme which emerged from the data" so với áp khung có sẵn; mô tả coding scheme quy nạp "lengthier than specified"; κ giả định phạm trù loại trừ nhau và đơn vị độc lập — [JMIR](https://www.jmir.org/2024/1/e59050) (bậc 1, qua search)
- Lưu ý: 10 phiên bản coding scheme là một dạng đo **biến thiên giữa các lần sinh** (0,72–0,82 là dải qua 10 phiên bản), nhưng tôi không thấy được bảng so sánh nội dung phạm trù giữa các phiên bản.

**Mayring — "Qualitative Content Analysis With ChatGPT: Pitfalls, Rough Approximations and Gross Errors. A Field Report", FQS 26(1), Art. 4, 01/2025** (chính tác giả phương pháp QCA)
- Chạy thử ChatGPT 3.5 và 4 trên một văn bản phỏng vấn mẫu, so với lời giải mẫu của chính Mayring: kết quả "at best, rough approximations… with many gross errors", với cả prompt ngây thơ lẫn prompt chi tiết có quy tắc mã hóa; công cụ không phản hồi hoặc phản hồi sai với nhiều khái niệm của content analysis, bỏ sót nội dung ẩn, không kiểm đồng thuận mã hóa; đầu ra nghiêng về "rough, superficial summary, essentially a list of topics" — [FQS 4252](https://www.qualitative-research.net/index.php/fqs/article/view/4252) (bậc 1, 2025-01, qua search, chỉ abstract)
- Trích đoạn khác: prompt quá "global" là một nguyên nhân kết quả kém; prompt chính xác cải thiện; template ChatGPT đưa ra chỉ mô tả đúng một kỹ thuật (inductive category formation); đầu ra giống lời giải theo Schreier (2012) — [FQS PDF](https://www.qualitative-research.net/index.php/fqs/article/download/4252/5160/19733) (bậc 1, qua search; ngữ cảnh câu chưa rõ)
- Không tìm thấy nguồn nào về QCAmap tích hợp AI (truy vấn "Mayring QCAmap ChatGPT…" không ra).

**Arlinghaus, Wulff, Maier — "Inductive Coding with ChatGPT… (LAIC: LLM-Assisted Inductive Categorization)", preprint OSF, 2024**
- Hai nghiên cứu **đăng ký trước**: Study 1 LLM gom phát biểu thành phạm trù quy nạp; Study 2 dùng phạm trù để phân loại từng phát biểu. GPT-3.5 Turbo và GPT-4o × 3 temperature (0; 0,5; 1) × 10 lần lặp = 120 lần chạy; 2 người mã hóa cũng tự rút phạm trù và gán. "All eight sets of categories (six created by ChatGPT plus two created by humans)" được đưa sang Study 2 — [OSF gpnye](https://osf.io/preprints/osf/gpnye), [ResearchGate](https://www.researchgate.net/publication/382949841_Inductive_Coding_with_ChatGPT_-_An_Evaluation_of_Different_GPT_Models_Clustering_Qualitative_Data_into_Categories) (bậc 1, preprint 2024, qua search)
- Kết quả: hai model "highly effective in developing and assigning inductive categories, even outperforming human coders in agreement rates"; khuyên GPT-4o, temperature 0, 10 lần lặp; đo bằng **tỉ lệ phần trăm đồng thuận** (trùng phạm trù = 100%, khác = 0%), không thấy κ/α — cùng nguồn (qua search). Chưa thấy con số % cụ thể. Bối cảnh dữ liệu (HRI, theo bản Zenodo) — [Zenodo 13693979](https://zenodo.org/records/13693979) (qua search).
- Không xác nhận được paper tự gắn với Mayring.

**De Paoli — "Performing an Inductive Thematic Analysis of Semi-Structured Interviews With a LLM", Social Science Computer Review 2024 (preprint arXiv 2305.13014, 2023)**
- GPT-3.5-Turbo qua API, làm pha 1–5 của Braun & Clarke trên 2 bộ phỏng vấn mở (người chơi game; giảng viên data science), so với phân tích đã công bố của tác giả gốc — [SAGE](https://journals.sagepub.com/doi/10.1177/08944393231220483), [arXiv 2305.13014](https://arxiv.org/pdf/2305.13014) (bậc 1, 2023/2024, qua search)
- Kết quả định tính: "The model can infer most of the main themes from previous research"; tên chủ đề khác nhưng mô tả "conveys a very similar meaning"; không bao giờ suy ra rõ chủ đề "psychological perspective" mà tác giả gốc coi trọng; ở một bảng pha 3 chỉ 2/5 chủ đề khớp rõ — cùng nguồn (qua search; con số 2/5 có thể từ bản nháp)
- Nối tiếp: De Paoli & Mathis, "Reflections on Inductive Thematic Saturation (ITS)…", Quality & Quantity 59 (2025) 683–709: đề xuất chỉ số ITS ≈ (số mã duy nhất)/(tổng số mã) để đo mức bão hòa của bước open coding bằng LLM; số mã duy nhất tích lũy **tăng gần tuyến tính** theo số phỏng vấn kể cả ở bộ lớn hơn, tức LLM không đạt bão hòa hoàn toàn; thứ tự mã hóa có thể ảnh hưởng điểm bão hòa — [arXiv 2401.03239](https://arxiv.org/pdf/2401.03239), [bản đăng Abertay](https://rke.abertay.ac.uk/ws/files/85988837/DePaoli_ReflectionsOnInduciveThematicSaturation_Published_2025.pdf) (bậc 1, 2024/2025, qua search; công thức chỉ thấy qua tóm tắt thứ cấp)

**Dai, Xiong, Ku — "LLM-in-the-loop: Leveraging LLM for Thematic Analysis", Findings of EMNLP 2023**
- Khung người–LLM dùng in-context learning, GPT-3.5 sinh codebook; 2 bộ khảo sát (music shuffle, password manager); "codes generated by the authors of the two datasets serve as the gold label"; Cohen's κ giữa coder người và coder model trên codebook cuối — [arXiv 2310.15100](https://arxiv.org/pdf/2310.15100), [ACL Anthology](https://aclanthology.org/2023.findings-emnlp.669/) (bậc 1, 2023, qua search)
- Số: κ = 0,87 cho cộng tác HC+MC trên bộ Music Shuffle — chỉ thấy qua một bài review bên thứ ba ([liner.com](https://liner.com/review/llmintheloop-leveraging-large-language-model-for-thematic-analysis), bậc 3); các số khác của Table 1 chưa thấy. Phê phán: một bài FQS nói Dai và cs. dùng mô hình cộng tác "simplistic" và không công bố prompt — [FQS 4196](https://www.qualitative-research.net/index.php/fqs/article/download/4196/5130/19336) (bậc 1, qua search)

**Prescott và cs. — "Comparing the Efficacy and Efficiency of Human and Generative AI: Qualitative Thematic Analyses", JMIR AI 2024;3:e54482**
- Dữ liệu: 40 tin nhắn SMS nhắc uống thuốc ARV (tiếng Anh); 2 nhóm người độc lập làm phân tích quy nạp và diễn dịch; một người khác làm bằng ChatGPT và Bard — [JMIR AI](https://ai.jmir.org/2024/1/e54482) (bậc 1, 2024, qua search)
- Quy nạp: chủ đề của GenAI (cả ChatGPT và Bard) "consistent with 71% (5/7) of the themes identified by human analysts"; 7 chủ đề người: time, adherence, religious, community care, health reminder, warning, encouragement; ChatGPT ra 10 chủ đề. Diễn dịch: ChatGPT 6/12 (50%), Bard 7/12 (58%) — cùng nguồn (qua search)
- Thời gian: ChatGPT 15/25 phút, Bard 20 phút so với người 492/705 phút — chỉ thấy qua nguồn thứ cấp dẫn lại (qua search)

**Hamilton, Elliott, Quick, Smith, Choplin — IJQM 22 (2023), dữ liệu phỏng vấn người nhận thu nhập đảm bảo**
- "human coders recognizing some themes that ChatGPT did not and vice versa"; đề xuất dùng chủ đề AI để tam giác hóa, phát hiện thiên kiến cá nhân — [DOAJ/IJQM](https://doaj.org/article/5813dd5772a54132bf5a86c71d6b224f) (bậc 1, 2023, qua search; không có số)

**Morgan — IJQM 22 (2023), "Exploring the Use of AI for Qualitative Data Analysis: The Case of ChatGPT"**
- Phân tích lại 2 bộ focus group đã mã hóa (6 nhóm sinh viên cao học năm đầu; 19 nhóm cặp vợ chồng cùng đi làm có trách nhiệm chăm sóc): ChatGPT tái tạo tốt chủ đề "concrete, descriptive", kém với chủ đề "subtle, interpretive"; đầu ra giống tóm tắt chủ đề hơn là chủ đề diễn giải — [slide của Morgan](https://goltc.org/wp-content/uploads/2026/03/Best-practices-for-Analysing-Qualitative-Data-with-AI-David-Morgan.pdf) (bậc 2, tác giả tự trình bày, qua search) và nguồn dẫn lại; không có số.

**Deiner và cs. — "LLMs Can Enable Inductive Thematic Analysis of a Social Media Corpus in a Single Prompt", JMIR Infodemiology 2024;4:e59641**
- So 3 LLM (GPT4-32K, Claude-instant-100K, Claude-2-100K) với phân tích người trước đó trên corpus mạng xã hội về vaping; mỗi LLM chạy 2 lần — [JMIR Infodemiology](https://infodemiology.jmir.org/2024/1/e59641) (bậc 1, 2024-08, qua search)
- "LLMs identified several themes similar to those identified by humans, with very low hallucination rates. Variability occurred between LLMs and between test runs of an individual LLM"; "unable to show that the LLMs… can replicate the depth of analysis… by consistently extracting the same themes from the same data"; LLM xếp hạng cao các chủ đề người coi là quan trọng nhất, khả năng đưa top-5 của người vào top của LLM cao hơn ngẫu nhiên (P<.001) — [PMC11393503](https://pmc.ncbi.nlm.nih.gov/articles/PMC11393503/) (bậc 1, qua search). Số cỡ corpus/số chủ đề chưa thấy.

**JMIR Formative Research 2026 — "LLM–Assisted Thematic Coding in Medical Education Research: Comparative Methodological Study" (doi 10.2196/85572)**
- 1 focus group 1 giờ, 4 sinh viên y năm 2; GPT-4o (02–07/2025). Quy nạp: 137 mã ban đầu, "31.4% (n=43) demonstrated agreement with human codes, 26.3% (n=36) represented reasonable alternatives, and 42.3% (n=58) were classified as not reasonable". Diễn dịch (áp codebook người): đồng thuận trung bình 96% (SD 4%, 79–100%), κ trung bình 0,71 (SD 0,26, 0–1,00) — [PMC13505884](https://pmc.ncbi.nlm.nih.gov/articles/PMC13505884/), [PubMed 42641075](https://pubmed.ncbi.nlm.nih.gov/42641075/) (bậc 1, 2026, qua search)

**Hill và cs. — "LLMs for thematic analysis in healthcare research: A blinded mixed-methods comparison with human analysts", PLOS Digital Health 2026;5(4):e0001189 (preprint medRxiv 12/2025)**
- 1 transcript focus group về AI trong y tế; 2 LLM đa dụng + 1 công cụ mã hóa dựa LLM vs người phân tích bị làm mù; chuẩn là đồng thuận chuyên gia; thiết kế kiểm định non-inferiority — [PLOS Digital Health](https://journals.plos.org/digitalhealth/article?id=10.1371%2Fjournal.pdig.0001189), [medRxiv](https://www.medrxiv.org/content/10.64898/2025.12.25.25343031v1.full) (bậc 1, 2025-12/2026, qua search)
- Diễn dịch: LLM đồng thuận trung bình 93,5% vs người 92,7% (κ = 0,34 cho LLM); bản preprint ghi Gwet AC1 0,92 (người) vs 0,93 (LLM), biên non-inferiority 0,03. Quy nạp: chỉ một model (ChatGPT-5) đạt non-inferiority ở biên 0,5 điểm trên thang Likert 5 (p = 0,043); tỉ lệ ảo giác chặt 1,2%; κ theo chủ đề –0,05 đến 0,54 — cùng nguồn (qua search; một phần số từ preprint, có thể khác bản in)

**Bergmann và 5 đồng tác giả — "LLMs for Survey Text Analysis – A Performance Comparison Between Humans and GPT-5 on Inductive Content Analysis", arXiv 2608.22417 (2026, preprint)** — gần nhất với bài toán "đếm câu trả lời mở"
- 903 câu trả lời mở, 6 biến, khảo sát nghiên cứu sinh châu Âu; 5 người làm inductive content analysis theo coding scheme chuẩn hóa; GPT-5.4 làm cùng nhiệm vụ; đo bằng Adjusted Rand Index (ARI) — [arXiv 2608.22417](https://arxiv.org/abs/2608.22417) (bậc 1, 2026-08, qua search)
- ARI người–LLM 0,61 (coding) và 0,54 (sinh chủ đề); nhất quán nội bộ người 0,68, LLM 0,76; theo biến dao động 0,31–0,89; biến có nhất quán nội bộ thấp thì đồng thuận giữa hai bên cũng thấp — cùng nguồn (qua search). Phê bình bên thứ ba: "internal" ARI so coding với theme của cùng một coder, không phải tin cậy giữa nhiều người; thiếu mốc người–người — [Pith](https://pith.science/paper/2608.22417) (bậc 3, qua search)

**Parfenova, Marfurt, Pfeffer, Denzler — "Text Annotation via Inductive Coding: Comparing Human Experts to LLMs", Findings of NAACL 2025**
- 6 LLM mã nguồn mở vs chuyên gia người, gán nhãn quy nạp (nhãn nảy sinh từ dữ liệu) cho các trích dẫn; chuyên gia chấm độ khó từng câu. "Human coders consistently perform well when labeling complex sentences but struggle with simpler ones, while LLMs exhibit the opposite trend"; một số LLM khớp nhãn vàng hơn nhưng bị chuyên gia chấm thấp hơn; LLM lệch nhãn vàng ít và đều hơn, nhất là câu dễ — [ACL Anthology 2025.findings-naacl.361](https://aclanthology.org/2025.findings-naacl.361/) (bậc 1, 2025, qua search; không có số)

**Liu và 6 đồng tác giả — "Agreement Is Not Quality: Blind Expert Verification of Human and LLM Qualitative Coding…", arXiv 2607.28890 (2026)**
- 5 hệ LLM và 3 người áp codebook phân cấp 72 mục lên 2.560 tin nhắn của giáo viên K-12 (codebook có sẵn, nên đây là bước gán): Jaccard người–LLM 0,30 vs người–người 0,52; nhưng chuyên gia mù chọn người/LLM gần ngang (51,5% vs 48,5%, 855 cặp); Bradley-Terry xếp 2 LLM trên 2/3 người — [arXiv 2607.28890](https://arxiv.org/abs/2607.28890) (bậc 1, 2026-07, qua search). Hạn chế: chỉ một người thẩm định.

**Khan và cs. — "Automating Thematic Analysis: How LLMs Analyse Controversial Topics", arXiv 2405.06919 (2024)**
- GPT-4 và Llama 2 vs người phân loại đoạn trích báo chí về Robodebt: "intriguing overlaps and variances"; prompt kiểu "Be Sceptical!", "Be Parsimonious!" giúp khớp người hơn; model có thiên kiến giống người — [arXiv 2405.06919](https://arxiv.org/html/2405.06919v1), [ADM+S](https://www.admscentre.org.au/research-finds-large-language-models-are-biased-but-can-still-help-analyse-complex-data/) (bậc 1/2, 2024, qua search; không có số)

**Tai và cs. — IJQM 23 (2024), "An Examination of the Use of LLMs to Aid Analysis of Textual Data"**
- Deductive: 3 văn bản phỏng vấn, codebook có sẵn, chạy LLM **160 lần**, mỗi lần coi như một coder mới; yêu cầu model đưa bằng chứng cho từng mã — [par.nsf.gov 10544479](https://par.nsf.gov/biblio/10544479) (bậc 1, 2024, qua search; không có số kết quả)

**Langer Research — white paper "A Pilot Test of AI Coding of Open-Ended Survey Responses" (2024/2025)**
- AI (một công cụ hàng đầu, không nêu tên trong trích đoạn) mã hóa câu trả lời mở Texas Education Poll 2024: "poor category creation, misclassification and an inability to detect nuance or valence"; phạm vi thử hẹp — [Langer Research PDF](https://www.langerresearch.com/wp-content/uploads/Langer-Research-White-Paper_AI-Coding.pdf) (bậc 1 với tư cách báo cáo của tổ chức, không bình duyệt, qua search; không có số)

### Nhận định
- Chuỗi bước của content analysis quy nạp đã được LLM làm trong ít nhất hai nghiên cứu theo đúng ngôn ngữ phương pháp luận: Bijker 2024 (condensed meaning units → coding scheme → gán → κ) và Arlinghaus/LAIC (sinh phạm trù quy nạp → gán → đồng thuận, đăng ký trước). Bergmann 2026 gọi thẳng là "inductive content analysis" trên câu trả lời khảo sát. Đây là ba trụ bằng chứng gần với bài toán nhất.
- Mayring, tác giả gốc của QCA, đánh giá tiêu cực khi giao cả quy trình cho ChatGPT 3.5/4 (đầu ra là "list of topics"). Các nghiên cứu lạc quan đều chia nhỏ bước và có người duyệt; Mayring đánh giá kiểu giao toàn bộ. Hai kết luận không nhất thiết mâu thuẫn.

### Khoảng trống
- Không mở được toàn văn nào, nên thiếu: bảng κ từng bộ của LACA, % đồng thuận của LAIC, số chủ đề/cỡ corpus của Deiner, Table 1 của Dai và cs., số của Hamilton/Morgan/Khan/Parfenova.
- Không có nghiên cứu nào trên tiếng Việt. (Có De Paoli và cs. thử tiếng Ý, [arXiv 2404.08488](https://arxiv.org/pdf/2404.08488), chưa đọc được số.)
- Không tìm thấy công bố về QCAmap tích hợp LLM.

## Câu hỏi phụ 4b — So sánh tập phạm trù quy nạp của LLM với tập phạm trù của người (overlap / recall)

### Kết luận ngắn
Các nghiên cứu đo trực tiếp cho thấy LLM **tìm lại được phần lớn chủ đề mô tả/hiển ngôn của người** (Prescott 5/7 = 71%; De Paoli "most of the main themes"), nhưng **ở mức mã chi tiết thì khớp thấp** (31% mã khớp, 42% không hợp lý trong JMIR Form Res 2026) và thường **sót chủ đề diễn giải/ẩn** (De Paoli, Morgan, Mayring). Không có chuẩn đo chung: mỗi bài một cách (đếm khớp bằng tay, ARI, Likert + non-inferiority, tương đồng ngữ nghĩa). Mức chắc chắn: trung bình.

### Phát hiện có nguồn
- Recall chủ đề: 71% (5/7) chủ đề quy nạp của người được GenAI tìm lại; LLM sinh nhiều chủ đề hơn (ChatGPT 10 so với người 7) — [Prescott 2024, JMIR AI](https://ai.jmir.org/2024/1/e54482) (bậc 1, qua search)
- Mức mã: 137 mã GPT-4o → 31,4% khớp người, 26,3% là phương án thay thế hợp lý, 42,3% không hợp lý — [JMIR Form Res 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13505884/) (bậc 1, qua search)
- Mức chủ đề, có chấm mù: chỉ 1 trong các LLM đạt non-inferiority với người ở phân tích quy nạp; κ theo chủ đề –0,05 đến 0,54 — [Hill 2026, PLOS Digit Health](https://journals.plos.org/digitalhealth/article?id=10.1371%2Fjournal.pdig.0001189) (bậc 1, qua search)
- Phân hoạch câu trả lời: ARI người–LLM 0,54 cho tập chủ đề, 0,61 cho coding; dải 0,31–0,89 theo biến — [Bergmann 2026](https://arxiv.org/abs/2608.22417) (bậc 1, preprint, qua search)
- Định tính: De Paoli thấy hầu hết chủ đề chính được suy ra, tên khác nghĩa giống, nhưng chủ đề "psychological perspective" bị sót — [SAGE 2024](https://journals.sagepub.com/doi/10.1177/08944393231220483) (bậc 1, qua search); Hamilton: mỗi bên thấy chủ đề bên kia không thấy — [IJQM 2023](https://doaj.org/article/5813dd5772a54132bf5a86c71d6b224f) (bậc 1, qua search); Morgan: tốt với chủ đề mô tả, kém với chủ đề diễn giải — [slide Morgan](https://goltc.org/wp-content/uploads/2026/03/Best-practices-for-Analysing-Qualitative-Data-with-AI-David-Morgan.pdf) (bậc 2, qua search); Deiner: chủ đề "similar" nhưng không nhất quán, chuyên gia vẫn thấy hợp lý — [JMIR Infodemiology 2024](https://infodemiology.jmir.org/2024/1/e59641) (bậc 1, qua search)
- Thứ tự quan trọng: LLM có xu hướng đưa top-5 chủ đề người cho là quan trọng nhất vào top của mình (P<.001) — [Deiner 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11393503/) (bậc 1, qua search). **Đây là bằng chứng trực tiếp nhất cho câu hỏi "cái gì nhiều nhất"**, dù đo bằng xếp hạng độ liên quan chứ không phải tần suất.
- Kết quả trái chiều: LAIC báo LLM còn **vượt** người về đồng thuận khi gán phạm trù quy nạp — [OSF gpnye](https://osf.io/preprints/osf/gpnye) (bậc 1, preprint, qua search); Langer báo "poor category creation" — [Langer Research](https://www.langerresearch.com/wp-content/uploads/Langer-Research-White-Paper_AI-Coding.pdf) (qua search).
- Đồng thuận thấp chưa chắc là chất lượng thấp: Jaccard người–LLM 0,30 < người–người 0,52, nhưng chuyên gia mù chọn ngang nhau — [arXiv 2607.28890](https://arxiv.org/abs/2607.28890) (bậc 1, qua search); LLM khớp nhãn vàng hơn ở câu dễ nhưng bị chuyên gia chấm thấp hơn — [Parfenova 2025](https://aclanthology.org/2025.findings-naacl.361/) (bậc 1, qua search)

### Nhận định
- Với bài toán đếm phạm trù xuất hiện nhiều/ít nhất, điểm quan trọng là: phạm trù **phổ biến, hiển ngôn** là loại LLM tìm lại tốt nhất (Prescott, De Paoli, Deiner top-5). Phạm trù **hiếm hoặc ngầm** là loại dễ bị sót (De Paoli "psychological perspective", Mayring "hidden text content"). Vậy đầu "ít nhất" của bảng tần suất kém tin cậy hơn đầu "nhiều nhất". Đây là suy luận từ các phát hiện trên; chưa có nghiên cứu nào đo riêng recall theo tần suất phạm trù.
- LLM có xu hướng sinh **nhiều** phạm trù hơn người (10 vs 7; 137 mã ở mức mã). Do đó bước gộp (reduction) phải có người kiểm.

### Khoảng trống
- Chưa thấy nghiên cứu nào đo recall/precision của tập phạm trù LLM **tách theo tần suất** của phạm trù (phạm trù hiếm có bị sót nhiều hơn không). Truy vấn đã thử không ra.
- Chưa có nghiên cứu nào so sánh **bảng tần suất cuối cùng** (thứ hạng phạm trù theo số đơn vị) giữa quy trình người và quy trình LLM quy nạp; Deiner gần nhất nhưng dùng xếp hạng độ liên quan.

## Câu hỏi phụ 4c — Độ tái lập giữa các lần chạy của phạm trù sinh quy nạp

### Kết luận ngắn
Bằng chứng ít và đo không thống nhất. Ở **mức gán nhãn theo codebook** thì độ ổn định giữa các lần chạy cao (κ > 0,8; ICC 0,92–0,93). Ở **mức tập chủ đề quy nạp** thì có biến động rõ: Deiner thấy chủ đề không nhất quán giữa 2 lần chạy; Jain thấy số chủ đề đồng thuận chỉ xuất hiện ở 50–83% số lần chạy; Bijker cho 10 phiên bản coding scheme với κ dao động 0,72–0,82. Mức chắc chắn: thấp–trung bình.

### Phát hiện có nguồn
- Deiner 2024: "Theme matching and reasonableness were inconsistent between the 2 test runs for each given LLM"; "Variability occurred between LLMs and between test runs of an individual LLM" — [PMC11393503](https://pmc.ncbi.nlm.nih.gov/articles/PMC11393503/) (bậc 1, 2024, qua search)
- Jain, Adeyinka, Roseman, Allsop và cs., arXiv 2512.20352 (2025-12): 3 LLM × 6 lần chạy trên một transcript phỏng vấn trị liệu nghệ thuật; κ giữa các lần chạy: Gemini 2.5 Pro 0,907 (cosine 95,3%), GPT-4o 0,853 (92,6%), Claude 3.5 Sonnet 0,842 (92,1%); Claude có dải κ rộng nhất (khoảng 0,396), "suggesting occasional divergent runs"; bước đồng thuận chỉ giữ chủ đề xuất hiện ở ≥50% số lần chạy; theo một bản tóm tắt: Gemini 6 chủ đề đồng thuận (độ nhất quán 50–83%), GPT-4o 5, Claude 4 — [arXiv 2512.20352](https://arxiv.org/abs/2512.20352) (bậc 1, preprint, qua search; abstract và thân bài mâu thuẫn psychedelic/ketamine)
- Bijker 2024: 10 phiên bản coding scheme quy nạp, κ tổng 0,72–0,82 — [JMIR](https://www.jmir.org/2024/1/e59050) (bậc 1, qua search). **Nhận định:** đây là dải κ người–LLM qua 10 lần sinh, gián tiếp cho thấy độ biến thiên; không phải đo trực tiếp độ trùng phạm trù giữa các phiên bản.
- LAIC: 10 lần lặp mỗi cấu hình, khuyên temperature 0 + 10 lần lặp; đo đồng thuận giữa các lần lặp bằng % — [OSF gpnye](https://osf.io/preprints/osf/gpnye) (bậc 1, preprint, qua search)
- Bergmann 2026: nhất quán nội bộ LLM ARI 0,76 (cao hơn người 0,68), nhưng đó là coding so với theme của cùng một lần chạy, không phải giữa các lần chạy — [arXiv 2608.22417](https://arxiv.org/abs/2608.22417), [Pith](https://pith.science/paper/2608.22417) (qua search)
- SFT-TA (arXiv 2509.17167) đề xuất chỉ số "dependability": ROUGE-1/2 hai chiều giữa các tập chủ đề của các lần chạy, trung bình 5 lần — [arXiv 2509.17167](https://arxiv.org/pdf/2509.17167) (bậc 1, qua search; không có số)
- Mức nhãn (không phải chủ đề): ICC giữa các lần chạy GPT-4 0,93 và 0,92 trên 2 bộ dữ liệu kỹ thuật yêu cầu — [arXiv 2504.19384](https://arxiv.org/pdf/2504.19384) (bậc 1, qua search)
- Tai 2024: 160 lần chạy, mỗi lần coi là một coder (deductive) — [par.nsf.gov](https://par.nsf.gov/biblio/10544479) (qua search; không có số)
- Bão hòa: số mã duy nhất do LLM sinh tăng gần tuyến tính, không bão hòa hẳn; thứ tự đưa dữ liệu có thể ảnh hưởng — [De Paoli & Mathis, arXiv 2401.03239](https://arxiv.org/pdf/2401.03239) (bậc 1, qua search)

### Nhận định
- Thiết kế phổ biến nhất để trị biến động là **chạy nhiều lần rồi lấy phạm trù xuất hiện ở đa số lần chạy** (Jain ≥50%; LAIC 10 lần lặp). Đây là thực hành đã có người làm, nhưng chưa có nghiên cứu nào kiểm chứng ngưỡng nào là tốt.
- Nên tách hai loại ổn định: (a) **tập phạm trù** giữa các lần sinh (bằng chứng yếu, có biến động); (b) **gán đơn vị vào phạm trù cố định** giữa các lần chạy (bằng chứng mạnh hơn, ổn định cao). Một quy trình nên cố định tập phạm trù sau bước người duyệt rồi mới đếm; khi đó độ ổn định của con số đếm dựa vào (b).

### Khoảng trống
- Chưa có nghiên cứu nào đo độ trùng tập phạm trù quy nạp giữa nhiều lần chạy trên **đoạn văn ngắn số lượng ~100** bằng một chỉ số đối chiếu tập (vd tỉ lệ phạm trù khớp sau khi người ghép cặp).
- Ảnh hưởng của thứ tự đưa dữ liệu lên tập phạm trù mới chỉ được nêu, chưa đo (De Paoli & Mathis).

## Câu hỏi phụ 4d — (theo cập nhật của coordinator) Mã hóa quy nạp mô tả vấn đề/phàn nàn/sự cố

### Kết luận ngắn
Có bằng chứng về câu trả lời khảo sát mở (Bergmann 2026; Langer; Mellon về "most important issue", vốn là deductive), nhưng **chưa tìm thấy nghiên cứu nào cho LLM tự rút phạm trù quy nạp từ phàn nàn hay báo cáo sự cố rồi so với người**. Các nghiên cứu về phàn nàn và sự cố đều dùng taxonomy có sẵn. Mức chắc chắn: trung bình (về sự vắng mặt, sau ~5 truy vấn).

### Phát hiện có nguồn
- Câu hỏi "most important issue" của British Election Study (Mellon và cs., Research & Politics 11(1), 2024): bối cảnh 133.917 câu trả lời, 28.099 câu trả lời khác nhau qua 5 đợt — [BES](https://britishelectionstudy.com/bes-resources/coding-the-single-most-important-issue) (bậc 1, qua search). Số độ chính xác của LLM (93,9%/94,7%, report cũ) **không tái xác nhận được** trong phiên này; nghiên cứu dùng bộ mã có sẵn nên là deductive.
- Câu trả lời khảo sát mở, quy nạp: Bergmann 2026 (xem 4a) — [arXiv 2608.22417](https://arxiv.org/abs/2608.22417); Langer: tạo phạm trù kém — [Langer Research](https://www.langerresearch.com/wp-content/uploads/Langer-Research-White-Paper_AI-Coding.pdf) (qua search)
- Quy trình GATOS (Humanities & Social Sciences Communications 2026): tóm tắt từng câu trả lời trước rồi mới dựng mã và chủ đề; trên dữ liệu mô phỏng 854 câu trả lời sinh ra 249 mã và 89 chủ đề; tác giả nêu câu hỏi mở về mức trừu tượng và đề xuất người duyệt — [Nature HSSC](https://www.nature.com/articles/s41599-026-06508-5) (bậc 1, 2026, qua search). Bài dùng kết hợp ML (có thể có phần gom cụm, ngoài phạm vi), chỉ dẫn ở mức quy trình.
- Phàn nàn của bệnh nhân: Claude 3.5 Sonnet phân loại theo taxonomy HCAT (GP) sau khi người đã mã hóa; đo accuracy, F1, κ — [PMC12327907](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12327907/) (bậc 1, qua search). Đây là deductive.
- Báo cáo sự cố hàng không ASRS: ChatGPT so với chuyên gia an toàn ở yếu tố con người, precision 0,61 (deductive) — [Aerospace/MDPI, preprint](https://www.preprints.org/manuscript/202307.0192) (bậc 1, 2023, qua search); bài UAV dùng khung HFACS (deductive). Không có bài quy nạp.
- Câu trả lời khảo sát tiếng Đức: LLM hay xử lý sai câu trả lời không thực chất ("don't know", trống); kết quả có thể không khái quát sang bối cảnh phức tạp hơn về chủ đề/ngôn ngữ — [arXiv 2506.14634](https://arxiv.org/pdf/2506.14634) (bậc 1, qua search)

### Nhận định
- Với bài toán "vấn đề nào được nhắc nhiều nhất", bằng chứng gần nhất là Bergmann 2026 (câu trả lời khảo sát mở, inductive content analysis, ARI người–LLM 0,54–0,61). Kết quả dao động mạnh theo biến (0,31–0,89), nên một bộ dữ liệu cụ thể có thể rơi vào đầu thấp.
- Cần xử lý riêng câu trả lời không thực chất (đơn vị không chứa phạm trù) trước khi đếm (arXiv 2506.14634).

### Khoảng trống
- Không tìm thấy nghiên cứu quy nạp trên phàn nàn hoặc báo cáo sự cố. Truy vấn đã thử: "LLM thematic analysis patient safety incident reports OR complaints inductive…", "LLM aviation safety reports ASRS narratives inductive…", "LLM inductive codebook generation open-ended survey… most important problem OR complaints".

## Câu hỏi phụ 4e — Bước nào LLM làm tốt, bước nào kém (theo các bước của reductive content analysis)

### Kết luận ngắn
Cô đọng (paraphrase/condense): có làm, chưa ai đo riêng. Sinh phạm trù: trung bình, biến động. Định nghĩa phạm trù: có làm, ít bằng chứng. Gán vào phạm trù cố định: tốt, ngang người. Đếm: chưa ai đánh giá riêng. Mức chắc chắn: trung bình cho "gán tốt", "sinh phạm trù biến động"; thấp cho các bước còn lại.

### Phát hiện có nguồn
| Bước | Nghiên cứu đã cho LLM làm | Kết quả đo được | Mức bằng chứng |
|---|---|---|---|
| Cô đọng/paraphrase đơn vị | Bijker 2024 (condensed meaning units); GATOS 2026 (tóm tắt từng câu trả lời) | Không đo riêng chất lượng bước này | thấp |
| Sinh phạm trù quy nạp | Bijker, LAIC, De Paoli, Prescott, Deiner, JMIR FR 2026, Hill 2026, Bergmann 2026 | Recall chủ đề 71% (Prescott); 31% mã khớp (JMIR FR); 1 model đạt non-inferiority (Hill); ARI theme 0,54 (Bergmann); biến động giữa lần chạy (Deiner, Jain) | trung bình, nhiều nghiên cứu nhỏ |
| Gộp/khử trùng lặp (reduction) | Bijker (cần ra lệnh "no overlap"); Jain (giữ chủ đề ≥50% lần chạy); ITS (De Paoli & Mathis) | Mã duy nhất tăng gần tuyến tính, không bão hòa (ITS) | thấp |
| Định nghĩa phạm trù | Bijker (mô tả coding scheme dài hơn yêu cầu); LACA (cùng phát triển codebook) | Không đo riêng | thấp |
| Gán đơn vị vào phạm trù cố định | LACA, Bijker, JMIR FR 2026, Hill 2026, Liu 2026, Tai 2024 | AC1 > 0,76 trừ mã "đoán mò" (LACA); κ 0,72–0,82 (Bijker, phạm trù quy nạp); 96%/κ 0,71 (JMIR FR); 93,5% vs người 92,7% (Hill) | trung bình–cao |
| Đếm tần suất | Không nghiên cứu nào đánh giá riêng sai số của bảng đếm | — | khoảng trống |

Nguồn từng ô: xem các mục 4a–4c ở trên (đều qua search).

### Nhận định
- Bằng chứng ủng hộ chia quy trình: LLM đề xuất phạm trù (nhiều lần chạy), người duyệt/gộp/định nghĩa, rồi LLM gán theo phạm trù cố định và kiểm đồng thuận với người trên một mẫu. Đó cũng là cách LACA, Bijker và Hill tổ chức. Riêng cách giao cả quy trình một lượt thì bị Mayring 2025 và Langer đánh giá kém.
- Chỉ số đồng thuận nên chọn theo độ hiếm của phạm trù: LACA dùng Gwet's AC1 vì mã hiếm làm κ sụt; Bijker nhắc κ giả định phạm trù loại trừ nhau. Điều này chạm trực tiếp vào bài toán đa nhãn và đầu "ít nhất".

### Khoảng trống
- Không có nghiên cứu nào đánh giá sai số của **con số đếm cuối** (tần suất phạm trù) do LLM tạo ra so với người trong thiết kế quy nạp hoàn toàn.
- Không có bằng chứng cho tiếng Việt.

## Truy vấn đã chạy
- LLM-assisted content analysis LACA Chew deductive coding (standard)
- Chew 2023 LACA GPT-3.5 Cohen's kappa four datasets codes agreement results (extended)
- De Paoli inductive thematic analysis semi-structured interviews large language model GPT-3.5 results themes compared original (extended)
- Bijker 2024 ChatGPT automated qualitative research content analysis JMIR inductive deductive agreement (extended)
- Mayring qualitative content analysis artificial intelligence QCAmap ChatGPT inductive category formation (extended)
- LLM-Assisted Inductive Categorization LAIC Mayring pre-registered GPT categories agreement human coders (extended)
- FQS "Qualitative Content Analysis With ChatGPT: Pitfalls, Rough Approximations and Gross Errors" author findings (extended)
- Dai Xiong Ku 2023 "LLM-in-the-loop" thematic analysis codebook Cohen's kappa human comparison results (extended)
- Prescott 2024 JMIR AI comparing human and generative AI qualitative thematic analyses SMS text messages themes overlap (extended)
- "LLMs for Survey Text Analysis" GPT-5 inductive content analysis humans ARI themes (extended)
- "Inductive Coding with ChatGPT" GPT-4o temperature repetitions categories Krippendorff agreement human coders results (extended)
- Bijker Merkouris Dowling Rodda ChatGPT content analysis sugar forum posts kappa inductive coding scheme 0.72 results PMC (extended)
- Large Language Model–Assisted Thematic Coding Medical Education Research Comparative Methodological Study GPT-4o 137 codes (extended)
- "Text Annotation via Inductive Coding: Comparing Human Experts to LLMs" results (extended)
- reproducibility inductive thematic analysis LLM repeated runs themes consistency across runs study (extended)
- LLM inductive codebook generation open-ended survey responses compared human codebook "most important problem" OR complaints (extended)
- Deiner 2024 JMIR Infodemiology vaping single prompt inductive thematic analysis themes human validation numbers (extended)
- Hamilton 2023 International Journal of Qualitative Methods ChatGPT guaranteed income thematic analysis comparison human themes (standard)
- Mathis 2024 inductive thematic analysis healthcare interviews open-source LLM Llama compared traditional themes results (standard)
- LLM thematic analysis patient safety incident reports OR complaints inductive themes compared human analysts study (extended)
- Morgan 2023 "Exploring the Use of Artificial Intelligence for Qualitative Data Analysis: The Case of ChatGPT" findings descriptive themes (standard)
- PLOS Digital Health 2026 "Large language models for thematic analysis in healthcare research" blinded focus groups non-inferiority concordance results (extended)
- arXiv 2512.20352 multi-LLM thematic analysis dual reliability six runs Gemini Claude GPT kappa cosine similarity interview transcript (extended)
- Bergmann 2608.22417 GPT-5 PhD survey 903 answers ARI coding themes variables human coders five results agreement range (extended)
- LLM aviation safety reports ASRS narratives inductive themes OR topics compared human experts (standard)
- "Agreement Is Not Quality" blind expert verification human LLM qualitative coding results (extended)
- Langer Research white paper pilot AI coding open-ended survey responses Texas Education Poll codebook results (standard)
- Tai 2024 International Journal of Qualitative Methods "An Examination of the Use of Large Language Models to Aid Analysis of Textual Data" 160 iterations (standard)
- Arlinghaus Wulff Maier inductive coding ChatGPT GPT-4o agreement percentage human coders categories number study 1 study 2 (extended)
- Mellon 2024 Research & Politics LLM code "most important issue" open-text British Election Study accuracy Claude GPT human coders categories (standard)
- De Paoli Mathis "inductive thematic saturation" LLM codes cumulative unique codes metric results (standard)
- Khan 2024 automating thematic analysis LLMs controversial topics Robodebt agreement human themes (standard)
- Parfenova 2025 inductive coding six open-source LLMs human experts dataset quotes gold labels ROUGE BERTScore results numbers (standard)
- "Do AIs know what the most important issue is" Claude accuracy 93.9 OR 94.7 human coders 50 categories (extended)
- Chew LACA "randomly guessing" permutation test Gwet's AC1 GPT-3.5 human coders codes datasets trust in science (extended)
- Bijker ChatGPT content analysis condensed meaning units 20% subset inductive categories kappa 0.72-0.82 results limitations repeated prompts consistency (extended)
