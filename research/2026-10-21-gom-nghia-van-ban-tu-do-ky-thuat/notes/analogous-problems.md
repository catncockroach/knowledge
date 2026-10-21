# Bài toán tương tự và case study

Phạm vi đã điều chỉnh (theo coordinator): mỗi lần phân tích chỉ **vài trăm** bản ghi viết tay (tích lũy tới vài nghìn). Vì vậy mỗi case ghi rõ **cỡ dữ liệu**, và phần "chuyển được gì" ưu tiên bài học ở quy mô nhỏ: dựng codebook, người + LLM cùng mã hóa vài trăm đoạn, đo đồng thuận.

Ghi chú về nguồn: proxy chặn arxiv.org, ar5iv, aclanthology, usenix.org, mdpi, ntrs.nasa.gov, nist.gov (nvlpubs), phmsociety, engineering.fb.com, các trang trường đại học và nhiều host khác. Các trang **đã mở được** gồm: README GitHub của CUPID, nestor, TopicGPT, ai-survey-coding-eval; trang publication của Microsoft Research (RCACopilot, AutoARTS); blog Microsoft Research về bài ICSE 2023. Mọi chi tiết khác là **(qua search)**: lấy từ snippet/tóm tắt của công cụ search, chưa đọc bản gốc.

## 1. Phát hiện trùng lặp bug report (DBRD)

### Kết luận ngắn
Đây là bài toán "cùng một lỗi, diễn đạt khác nhau" được nghiên cứu lâu nhất, nhưng nó được đóng khung là **truy hồi theo cặp** (top‑k ứng viên trùng) chứ không phải đếm tần suất. Hai bài học chuyển được: (a) dùng LLM **trích ý chính / giải nghĩa thuật ngữ** trước rồi mới so khớp tốt hơn là cho LLM so mọi cặp; (b) phương pháp đơn giản thường thắng deep learning khi dữ liệu nhỏ. Mức chắc chắn: trung bình (phần lớn số liệu qua search).

### Phát hiện có nguồn
- CUPID (Zhang và cộng sự, SMU, 2023, sửa 2024): ChatGPT zero-shot rút "essential information"/keyword từ mỗi bug report, rồi đưa vào REP (phương pháp truyền thống tốt nhất). Recall Rate@10 đạt 0,59–0,67 (bản v1), 0,602–0,654 (bản sau), là SOTA trên 3 tập; thời gian truy vấn trung bình < 5 giây/bug report. Động cơ: "in the bug repositories with a smaller number of bug reports, around 10k, the existing deep learning approaches show worse performance than the traditional approaches" (qua search) — [CUPID, arXiv 2308.10022](https://arxiv.org/abs/2308.10022) (bậc 1, 2023-08/2024-07)
- README CUPID: ba project Spark, Hadoop, Kibana; số cặp trùng dùng để train lần lượt 273, 285, 286; so với các cách rút keyword khác (LLaMA 3, Phi-3, OpenChat, TF-IDF, KP-Miner, YAKE); RankNet với ràng buộc thời gian 365 ngày — [soarsmu/CUPID README](https://github.com/soarsmu/CUPID) (bậc 1, đã mở, không rõ ngày)
- Thiết kế của CUPID tránh cho ChatGPT so bug report mới với toàn bộ kho ("avoids using ChatGPT to compare the given bug report with all the bug reports in the repository") (qua search) — [CUPID HTML v3](https://arxiv.org/html/2308.10022v3) (bậc 1, 2024)
- "Duplicate Bug Report Detection: How Far Are We?" (Zhang và cộng sự, TOSEM 32(4), 2023): tuổi dữ liệu và loại issue tracker gây khác biệt đáng kể ("age bias", "ITS bias"); "a simpler technique outperforms recently proposed sophisticated techniques on most projects"; REP hơn SABD trung bình 22,3% RR@10 trên 6 project, trừ Mozilla và VSCode (qua search) — [arXiv 2212.00548](https://arxiv.org/abs/2212.00548) (bậc 1, 2023)
- Mukherjee & Rahman (EASE 2025): tới 23% bug report trùng là "textually dissimilar", khoảng 78% bug report ở dự án mã nguồn mở rất ngắn; họ làm giàu report bằng **giải nghĩa thuật ngữ miền** (T5 fine-tune sinh giải nghĩa), trên 92.854 report của 3 hệ thống, 7 baseline đều tăng, tăng nhiều nhất ở cặp trùng khác chữ (qua search) — [Understanding the Impact of Domain Term Explanation on DBRD, arXiv 2503.18832](https://arxiv.org/html/2503.18832v1) (bậc 1, 2025-03)
- So sánh embedding cho độ tương đồng bug report (2023): BERT cho recall tốt nhất, rồi ADA (OpenAI), Gensim, FastText, TF-IDF (qua search) — [Comparative Analysis of Text Embedding Models for Bug Report Semantic Similarity, arXiv 2308.09193](https://arxiv.org/html/2308.09193v2) (bậc 1, 2023)
- Fine-tune all-mpnet-base-v2 trên Eclipse, OpenOffice, Firefox, NetBeans chỉ cải thiện "marginal" (qua search) — [SBES 2025](https://sol.sbc.org.br/index.php/sbes/article/download/36991/36776) (bậc 1, 2025)
- Case công nghiệp (Chalmers, 2024): kỹ thuật tự động "have not seen widespread industrial adoption", nên nghiên cứu tập trung vào quy trình human-in-the-loop (qua search) — [Exploring the Role of Automation in DBRD: An Industrial Case Study](https://research.chalmers.se/publication/?id=542072) (bậc 1, 2024)

### Nhận định
- **Nhận định:** cách CUPID và giải nghĩa thuật ngữ cùng chỉ một hướng: **chuẩn hóa nội dung trước khi so** (rút ý chính, giải thích jargon) giúp nhiều nhất ở đúng ca "cùng nguyên nhân, khác chữ". Đây là bằng chứng gián tiếp cho "trích ý trước, gom sau".
- **Nhận định:** với vài trăm bản ghi, bài toán DBRD (top‑k truy hồi trong kho hàng chục nghìn) không chuyển nguyên được. Phần chuyển được là bước tiền xử lý bằng LLM và cảnh báo rằng deep learning tốn công không thắng baseline đơn giản khi dữ liệu nhỏ.

### Khoảng trống
- Không đọc được bảng số đầy đủ của CUPID và của bài domain-term (arxiv bị chặn). Không tìm thấy nghiên cứu 2024–2026 so sánh trực tiếp embedding LLM hiện đại với REP/SABD trên Recall@k.
- DBRD đo truy hồi theo cặp, không có số liệu về "tần suất theo nhóm nguyên nhân".

## 2. Ticket/sự cố IT và postmortem

### Kết luận ngắn
Các nhóm vận hành cloud lớn đều đi theo mẫu **taxonomy (thường phân cấp, đa nhãn) + gán tự động có người duyệt**; LLM được dùng với ví dụ lấy từ sự cố tương tự và một bước **tóm tắt trước** khi truy hồi. Số liệu cho thấy lớp hiếm (đuôi dài) là điểm yếu chung: micro-F1 cao nhưng macro-F1 thấp. Mức chắc chắn: trung bình–cao cho Microsoft (có trang gốc), thấp–trung bình cho phần còn lại.

### Phát hiện có nguồn
- RCACopilot (Microsoft, EuroSys '24, 2024-04): khớp sự cố với handler theo loại alert, thu thập chẩn đoán, **dự đoán nhóm nguyên nhân gốc** và viết giải thích; "RCA accuracy of up to 0.766" trên dữ liệu một năm sự cố của Microsoft; phần thu thập chẩn đoán đã chạy ở Microsoft "for over four years" — [Automatic Root Cause Analysis via LLMs for Cloud Incidents, Microsoft Research](https://www.microsoft.com/en-us/research/publication/automatic-root-cause-analysis-via-large-language-models-for-cloud-incidents) (bậc 1, đã mở, 2024-04)
- Chi tiết RCACopilot: tập đánh giá **653 sự cố** trong một năm của dịch vụ Transport; GPT-4 đạt Micro-F1 0,766 / Macro-F1 0,533 (GPT-3.5: 0,761 / 0,505), suy luận trung bình 4,205 giây; baseline FastText 0,076 / 0,004 và XGBoost 0,022 / 0,009; tác giả giải thích bằng phân phối nhóm nguyên nhân đuôi dài (qua search) — [arXiv 2305.15778v3](https://arxiv.org/pdf/2305.15778v3) (bậc 1, 2023–2024)
- RCACopilot cho LLM tóm tắt chẩn đoán còn 120–140 từ "without outputting any unrelated information", vì chẩn đoán của một sự cố có thể > 2.000 token; prompt few-shot chain-of-thought lấy K=5 sự cố tương tự nhất (ưu tiên khác nhóm) làm ví dụ (qua search) — [arXiv 2305.15778](https://arxiv.org/pdf/2305.15778); [emergentmind digest](https://www.emergentmind.com/papers/2305.15778) (bậc 1 / bậc 3, 2023–2024)
- Ahmed và cộng sự (ICSE 2023): > 40.000 sự cố từ > 1.000 dịch vụ; đầu vào chỉ **tiêu đề + tóm tắt** sự cố; sinh nguyên nhân gốc và bước khắc phục. Fine-tune GPT-3.5 tăng độ tương đồng từ vựng trung bình 45,5% cho nguyên nhân gốc và 131,3% cho khắc phục so với zero-shot; LLM làm tốt hơn ở sự cố do máy báo (MRI) so với sự cố khách báo (CRI) vì MRI lặp lại nhiều; > 70% on-call engineer chấm hữu ích ≥ 3/5; cần retrain thường xuyên vì "staleness", đang thử retrieval-augmented — [Large-language models for automatic cloud incident management, Microsoft Research Blog](https://www.microsoft.com/en-us/research/blog/large-language-models-for-automatic-cloud-incident-management) (bậc 1, đã mở, 2023)
- AutoARTS (Microsoft Azure, USENIX ATC 2023): phân tích > 2.000 sự cố từ > 450 dịch vụ qua nhiều năm; dựng taxonomy **phân cấp** các yếu tố góp phần (ARTS); lập luận rằng gán một nguyên nhân gốc duy nhất theo taxonomy ad hoc là dễ sai và "a single root cause is inadequate to capture all contributing factors"; xây công cụ hỗ trợ người gán nhãn — [AutoARTS, Microsoft Research](https://www.microsoft.com/en-us/research/publication/autoarts-taxonomy-insights-and-tools-for-root-cause-labelling-of-incidents-in-microsoft-azure/) (bậc 1, đã mở, 2023)
- AutoARTS gợi ý nhiều tag cho mỗi sự cố kèm đoạn trích ngữ cảnh; phân loại đa nhãn F1 0,89; mô hình phân cấp (HiAGM) hơn cách phẳng và BERT fine-tune; trong user study, snippet giúp chuyên gia phát hiện thêm 2 yếu tố góp phần bị bỏ sót trong 10 sự cố (qua search) — [AutoARTS, USENIX ATC 2023](https://www.usenix.org/conference/atc23/presentation/dogga) (bậc 1, 2023)
- Salesforce ICA (Saha & Hoi, ICSE-SEIP 2022): rút thông tin có mục tiêu (triệu chứng, nguyên nhân, cách xử lý) từ tài liệu điều tra sự cố (PRB) thành đồ thị tri thức nhân quả, rồi truy hồi sự cố cũ để gợi ý nguyên nhân; xây trên khoảng 2.000 bản điều tra sự cố trong vài năm; có chuyên gia kiểm định (qua search) — [Mining Root Cause Knowledge from Cloud Service Incident Investigations for AIOps, arXiv 2204.11598](https://arxiv.org/pdf/2204.11598) (bậc 1, 2022)
- Meta (2024-06): hệ thống hỗ trợ điều tra kết hợp truy hồi theo heuristic với **xếp hạng bằng LLM**, đạt 42% độ chính xác xác định nguyên nhân gốc ngay lúc tạo điều tra (backtest, monorepo web); thu hẹp hàng nghìn thay đổi code xuống 5 ứng viên; nhấn mạnh rủi ro gợi ý sai, cần vòng phản hồi, giải thích và đo độ tự tin (qua search; nguồn thứ cấp nói model là Llama 2 7B fine-tune) — [Leveraging AI for efficient incident response, Engineering at Meta](https://engineering.fb.com/2024/06/24/data-infrastructure/leveraging-ai-for-efficient-incident-response/) (bậc 1, 2024-06)
- Chu và cộng sự (ICPE 2026, WIP): > 3.000 báo cáo sự cố công khai từ AWS, Azure, GCP được gán tay; so 6 chiến lược prompt × 6 LLM; độ chính xác **trích metadata** khoảng 75–95% tùy tập; few-shot thường tăng độ chính xác, giảm latency nhưng tốn 1,5–2× token đầu vào (qua search) — [Leveraging LLMs for Structured Information Extraction and Analysis from Cloud Incident Reports, arXiv 2603.16818](https://arxiv.org/abs/2603.16818) (bậc 1, 2026-03)

### Nhận định
- **Nhận định:** RCACopilot là case gần nhất với quy mô vài trăm: 653 sự cố, gán vào nhóm nguyên nhân có sẵn bằng LLM few-shot với ví dụ truy hồi. Classifier truyền thống gần như vô dụng ở cỡ này (F1 < 0,1), còn LLM đạt 0,77 micro nhưng 0,53 macro. Với vài trăm bản ghi, nên kỳ vọng LLM gán tốt nhóm lớn và yếu ở nhóm hiếm; phải kiểm tay riêng nhóm hiếm.
- **Nhận định:** bước "tóm tắt 120–140 từ, bỏ thông tin không liên quan" của RCACopilot và "chỉ dùng tiêu đề + tóm tắt" của Ahmed là cùng một thực hành: rút gọn văn bản dài/nhiễu thành phát biểu ngắn trước khi so khớp.
- **Nhận định:** AutoARTS là bằng chứng mạnh cho **đa nhãn + phân cấp**: một sự cố có nhiều yếu tố góp phần; ép một nhãn làm sai lệch thống kê tần suất.

### Khoảng trống
- Không đọc được bản đầy đủ của RCACopilot (ablation tóm tắt / không tóm tắt; cách xử lý nhóm mới), AutoARTS (số tầng, số nhóm, đồng thuận người gán) và ICA (số liệu độ chính xác).
- Không tìm thấy công bố của Google SRE về gom/thống kê postmortem có số liệu pipeline.

## 3. Narrative an toàn: hàng không (ASRS, NTSB), thiết bị y tế (MAUDE), tai nạn giao thông

### Kết luận ngắn
Các kho narrative an toàn có taxonomy chính thức nhưng mã gán sẵn thường **không đáng tin** ở cấp mịn; LLM đồng thuận tốt ở cấp thô và giảm mạnh ở cấp mịn. Nhiều nghiên cứu dùng **mẫu nhỏ (50–2.000)** và nhấn mạnh đo đồng thuận với chuyên gia hơn là accuracy. Mức chắc chắn: thấp–trung bình (toàn bộ qua search).

### Phát hiện có nguồn
- ASRS nhận 65.656 báo cáo năm 2020 (qua search) — [NLP of Aviation Occurrence Reports for Safety Management, arXiv 2301.05663](https://arxiv.org/pdf/2301.05663) (bậc 1, 2023)
- Tikayat Ray và cộng sự (Aerospace 10(9):770, 2023): ChatGPT sinh synopsis từ narrative ASRS và xác định yếu tố con người; so với nhà phân tích an toàn, precision 0,61, ChatGPT "cautious approach toward attributing human factors issues"; aeroBERT (fine-tune chuyên ngành) cho embedding gần synopsis gốc nhất (qua search) — [Examining the Potential of Generative Language Models for Aviation Safety Analysis](https://www.mdpi.com/2226-4310/10/9/770) (bậc 1, 2023)
- NASA NTRS (2025): đề xuất dùng Llama 3.1 Instruct gắn cờ hành vi "resilient" trên > 250.000 narrative ASRS theo nhóm anomaly; mới là đề xuất, chưa có kết quả (qua search) — [NTRS 20250004265](https://ntrs.nasa.gov/citations/20250004265) (bậc 1, 2025)
- Dự án GitHub cá nhân: BERT phân loại narrative ASRS vào 15 nhóm (nhóm do gom bằng embedding) đạt khoảng 54% (qua search) — [jfernsler/ASRS_Classifier](https://github.com/jfernsler/ASRS_Classifier) (bậc 3, không rõ ngày)
- GA-ACAPS: khoảng 2.250 báo cáo NTSB hàng không chung, prompt LLM theo nhóm HFACS; thêm lời khai nhân chứng vào thông tin cơ bản cải thiện đáng kể; dự đoán tốt "unsafe acts" và một số "preconditions" (qua search) — [Show the Way: Accelerating GA Accident Investigations through LLMs and HFACS](https://openaccess.cms-conferences.org/publications/book/978-1-964867-24-3/article/978-1-964867-24-3_8) (bậc 1, không rõ năm)
- MAUDE (2026): từ 10.000 bản ghi, giữ 1.728 bản ghi device-problem và 1.224 health-effect nơi mã người và LLM khớp ở cấp 2 IMDRF; model reasoning mã nguồn mở chỉ đạt 59,49% đồng thuận ở cấp 1 và 23,04% ở cấp 3 → zero-shot không đủ (qua search) — [A Framework for LLM-Guided and ISO 5338-Aligned Data Engineering in Medical Device Adverse Event Reporting, DkIT](https://eprints.dkit.ie/id/eprint/1049/) (bậc 1, 2026)
- Luận án Rutgers: phân loại > 11 triệu narrative MAUDE (2007–2016); kết luận mã problem code liên quan máy tính "are inaccurate at a significant rate and should not be used in research" (qua search) — [Rutgers RUcore](https://rucore.libraries.rutgers.edu/rutgers-lib/56984/) (bậc 1, không rõ ngày)
- "Accuracy is Not Agreement" (Bhagat, Shihab, Sharma, Iowa State, 2025): model có accuracy cao hơn lại đồng thuận (Cohen's kappa) với chuyên gia thấp hơn; LLM (GPT-4, LLaMA 3, Qwen, Claude) accuracy thấp hơn nhưng khớp chuyên gia hơn, dựa vào ngữ cảnh/thời gian hơn từ khóa địa điểm; đánh giá trên 50 narrative tai nạn có nhãn chuyên gia (qua search) — [arXiv 2504.13068](https://arxiv.org/html/2504.13068v2) (bậc 1, 2025)

### Nhận định
- **Nhận định:** bài học chuyển được nhất là **đo đồng thuận ở từng cấp taxonomy**: đồng thuận người–LLM ở cấp thô có thể chấp nhận được trong khi cấp mịn tụt xuống 20–30% (MAUDE). Với vài trăm bản ghi, nên báo tần suất ở cấp thô và chỉ báo cấp mịn khi có kiểm tay.
- **Nhận định:** mã có cấu trúc mà người nhập chọn sẵn (MAUDE problem code) không phải ground truth; đọc lại narrative là cách sửa. Khớp với kết luận ở mảng bảo trì (mục 4) và report trước.

### Khoảng trống
- Không mở được bất kỳ bài ASRS/MAUDE/NTSB nào; số mẫu của Tikayat Ray (search gợi ý 210 nhưng không xác nhận) và chi tiết FAERS chưa tìm.
- Không tìm thấy nghiên cứu công khai dùng LLM để **khám phá** taxonomy mới từ narrative ASRS kèm số liệu.

## 4. Work order bảo trì / Technical Language Processing (NIST, MaintNet)

### Kết luận ngắn
Nhóm NIST xử lý văn bản ngắn nhiều viết tắt bằng **gán tag có máy hỗ trợ**: xếp hạng token theo TF-IDF, người gộp biến thể vào alias (thesaurus) và phân loại; ưu tiên kiểm chứng và lòng tin của người dùng hơn tự động hóa. Bằng chứng: gán tag có hỗ trợ nhanh hơn nhiều nhưng kém chính xác hơn gán tay chuyên gia khi tính KPI. Mức chắc chắn: trung bình.

### Phát hiện có nguồn
- Nestor (NIST): xếp hạng keyword theo độ quan trọng, gợi ý các term là biến thể của nhau (lỗi chính tả...) để duyệt nhanh, công cụ dựng problem code và taxonomy, xuất tag dạng CSV/sparse matrix; "very early alpha" — [usnistgov/nestor README](https://github.com/usnistgov/nestor) (bậc 1, đã mở, không rõ ngày)
- Docs Nestor: chỉ đưa ra các term liên quan nhất theo TF-IDF; file vocab đóng vai thesaurus, alias mặc định gộp nhiều token khác nhau, giảm mạnh số chiều; có báo cáo độ phủ tag (`report_completeness`) (qua search) — [Nestor Toolkit Documentation](https://pages.nist.gov/nestor/pdf/nestor-documentation.pdf) (bậc 1, không rõ ngày)
- Một phát biểu của Brundage: khoảng một giờ tag được 3.100 work order và tag một phần 5.400 (diễn đạt mơ hồ) (qua search) — [AMT: An Introduction to Technical Language Processing](https://www.amtonline.org/article/an-introduction-to-technical-language-processing-unlocking-maintenance) (bậc 2, không rõ ngày)
- Hastings, Sexton, Brundage, Hodkiewicz (PHM 2019) nghiên cứu đồng thuận giữa các chuyên gia gán tag **độc lập** trên work order, vì nhược điểm của Nestor là chỉ một chuyên gia làm; không lấy được số liệu đồng thuận (qua search) — [Agreement Behavior of Isolated Annotators for Maintenance Work-Order Data Mining, NIST](https://www.nist.gov/publications/agreement-behavior-isolated-annotators-maintenance-work-order-data-mining) (bậc 1, 2019)
- Lutz và cộng sự (Energies 16(24):7937, 2023), work order tuabin gió: công cụ gán tag có AI hỗ trợ giảm 88% thời gian gán so với gán tay chuyên gia và text classification, nhưng hai cách kia chính xác hơn khi tính KPI (tỷ lệ hỏng) (qua search) — [KPI Extraction from Maintenance Work Orders, arXiv 2311.04064](https://arxiv.org/html/2311.04064v2) (bậc 1, 2023-12)
- MaintNet (COLING 2020 demo): thư viện mở gồm logbook bảo trì hàng không, ô tô, cơ sở vật chất kèm công cụ tiền xử lý, gom cụm; văn bản trộn jargon, viết tắt, sai chính tả, gây khó cho pipeline NLP huấn luyện trên văn bản chuẩn (qua search) — [MaintNet, ACL Anthology 2020.coling-demos.2](https://aclanthology.org/2020.coling-demos.2) (bậc 1, 2020)

### Nhận định
- **Nhận định:** với vài trăm bản ghi, mô thức Nestor (người duyệt danh sách term xếp hạng + thesaurus alias cho viết tắt) là cách rẻ để xử lý jargon/viết tắt trước khi gom; nó cũng sinh ra từ điển viết tắt dùng lại được trong prompt LLM (tương tự ý "giải nghĩa thuật ngữ" của mục 1).
- **Nhận định:** kết quả 88% thời gian nhưng kém chính xác hơn cho thấy: khi con số tần suất được dùng ra quyết định, cần một mẫu gán tay chuyên gia để hiệu chỉnh.

### Khoảng trống
- Chưa có số đồng thuận giữa người gán độc lập (Hastings 2019) và số chính xác KPI của Lutz 2023. Không tìm thấy công trình NIST 2024–2026 dùng LLM cho work order.

## 5. Khiếu nại khách hàng (CFPB complaint narratives)

### Kết luận ngắn
Mảng này chủ yếu là phân loại theo taxonomy có sẵn (product/issue) trên tập rất lớn hoặc LDA để theo dõi chủ đề; ít bài học riêng cho quy mô vài trăm. Mức chắc chắn: thấp.

### Phát hiện có nguồn
- LDA trên khoảng 1,7 triệu narrative CFPB để nhận diện ưu tiên quản lý (credit reporting, mortgage) (qua search) — [Predictive Analysis of CFPB Consumer Complaints, arXiv 2407.06399](https://arxiv.org/pdf/2407.06399) (bậc 1, 2024)
- Bài 2026: một số LLM làm tốt zero-shot; few-shot chọn ví dụ theo độ liên quan (retrieval) tốt hơn zero-shot; cảnh báo kết quả topic modeling "may not be reproducibly recovered" (qua search) — [From Complaint Narratives to Monetary Relief, arXiv 2606.22664](https://arxiv.org/pdf/2606.22664) (bậc 1, 2026)
- Federal Reserve Board có quy trình topic modeling nội bộ gán mỗi narrative một số và nhãn chủ đề (qua search) — [Consumer Complaints Topic Modeling Process PIA](https://www.federalreserve.gov/files/consumer-complaints-topic-modeling-process-pia.pdf) (bậc 1, không rõ ngày)
- Taxonomy CFPB không tách lừa đảo (scam) khỏi gian lận (fraud) khác; một dự án dùng ensemble LLM để tách (qua search) — [aitopics](https://aitopics.org/tag/consumer%20financial%20protection%20bureau) (bậc 3, không rõ ngày)

### Nhận định
- **Nhận định:** ví dụ scam/fraud minh họa vì sao taxonomy cố định có thể thiếu đúng nhóm người phân tích cần, nên cần vòng khám phá. Few-shot với ví dụ truy hồi theo độ liên quan lặp lại mẫu RCACopilot.

### Khoảng trống
- Không mở được nguồn nào; không có số đồng thuận người–LLM trên mẫu nhỏ CFPB.

## 6. Mã hóa câu trả lời mở trong khảo sát bằng LLM (ưu tiên cho quy mô nhỏ)

### Kết luận ngắn
Đây là mảng chuyển được nhiều nhất sang bài toán vài trăm bản ghi. Với codebook rõ và số nhóm vừa phải, LLM đạt đồng thuận **gần bằng giữa hai người mã hóa** (khoảng 94–96% trên câu hỏi "vấn đề quan trọng nhất", 50 nhóm). Nhưng kết quả phụ thuộc mạnh vào nhiệm vụ: đa nhãn, nhiều nhóm, phải suy luận ý (valence) thì tụt rõ. Phân phối tần suất do LLM sinh có thể lệch khỏi phân phối của người dù độ tin cậy cao. Mức chắc chắn: trung bình (số chính đến từ search cộng một README đã mở).

### Phát hiện có nguồn
- Mellon và cộng sự (Research & Politics, 2024), British Election Study, câu "most important issue", 50 nhóm: không có dữ liệu train, LLM tốt nhất (Claude-1.3) đạt 93,9% so với 94,7% của người mã hóa thứ hai, hơn model supervised train trên 1.000 ca (93,5%); khi gán cho văn bản mới, Claude-1.3 80,9% so với người 88,6%, hơn model supervised train trên 576.000 ca; PaLM-2, Llama-2, SVM kém rõ (qua search) — [Do AIs know what the most important issue is?, Cardiff ORCA](https://orca.cardiff.ac.uk/id/eprint/177688/) (bậc 1, 2024); slide hội nghị SRA 2023 trước đó nói GPT-3 khớp nhóm gộp của người khoảng 95% — [Ralph Scott, SRA 2023](https://the-sra.org.uk/common/Uploaded%20files/Annual%20conference%202023/Main%20Speakers/ralph-scott.pdf) (bậc 1, 2023)
- Đánh giá độc lập (README GitHub, cá nhân, 2026): BES wave 25, dev 300 câu để chỉnh codebook, test 1.200 câu chạy một lần; Llama 3.1 8B chạy local qua Ollama chỉ với codebook, không dữ liệu train: 95,4% (κ 0,93) ở 12 nhóm, 95,9% (κ 0,95) ở 50 nhóm; TF-IDF + logistic regression train trên 40.956 câu: 97,4% (κ 0,96) và 95,8%; ở ~95% câu hai cách đồng ý, nhãn chung khớp BES 98,7–99,2%; chỉ đưa ~5% bất đồng cho người → khoảng 99% trong trường hợp tốt nhất; ước tính 7–21 phút người cho 1.000 câu so với ~2,2 giờ mã tay; chính tác giả (chưa huấn luyện) chỉ khớp BES 83% — [adeelmanaf43/ai-survey-coding-eval](https://github.com/adeelmanaf43/ai-survey-coding-eval) (bậc 3, đã mở, ~2026)
- Langer Research (pilot, hè 2025): Claude Opus 4 qua giao diện web mã hóa câu mở "điều gì đang tốt ở trường công địa phương" (Texas Education Poll 2024), > 40 nhóm; kết quả "performed poorly": tạo nhóm kém, phân loại sai, không bắt được sắc thái và chiều tích cực/tiêu cực (vd người trả lời nêu vấn đề thay vì điểm tốt); khuyên thận trọng khi chất lượng dữ liệu là ưu tiên (qua search) — [A Pilot Test of AI Coding of Open-Ended Survey Responses](https://www.langerresearch.com/white-paper_ai-coding/) (bậc 1, 2025); README trên cho biết pilot có 1.166 câu, 45 nhóm, đa nhãn và chỉ tính khớp khi **mọi** mã trùng, AI khớp 29% — [ai-survey-coding-eval](https://github.com/adeelmanaf43/ai-survey-coding-eval) (bậc 3, đã mở) — hai nguồn nhất quán về thiết kế, số 29% chỉ từ nguồn bậc 3
- von der Heyde, Haensch, Weiß, Daikeler (arXiv 2506.14634, 2025; bản Survey Research Methods): 5.072 câu tiếng Đức về lý do tham gia khảo sát, hai người mã hóa độc lập κ 0,91, bất đồng do chuyên gia phân xử; so GPT-4o, Llama 3.2, Mistral NeMo ở zero-shot, few-shot, fine-tune; chỉ LLM fine-tune (trên 1.024 câu) đạt mức dự đoán "satisfactory"; mô tả nhóm giúp hơn zero-shot, few-shot giúp thêm; mọi model ICC > 0,93; **không fine-tune thì độ chính xác không đều giữa các nhóm khiến phân phối nhóm khác phân phối của người** (qua search) — [AIn't Nothing But a Survey?](https://arxiv.org/abs/2506.14634) (bậc 1, 2025-06)
- Một abstract ESRA 2025: LLM không độc quyền chỉ sinh tối đa 10 nhóm khi mã hóa quy nạp, tác giả không khuyên dùng chúng cho mã hóa quy nạp câu hỏi mở (qua search) — [ESRA 2025 session 38](https://europeansurveyresearch.org/conf2025/progGlance.php?sess=38) (bậc 1, 2025)
- Schonlau & Couper (Survey Research Methods 10(2), 2016) đã có trong report trước: 54–80% tự động ở mức 80% độ chính xác tổng (qua search) — [SSOAR](https://www.ssoar.info/ssoar/handle/document/49780?show=full) (bậc 1, 2016)

### Nhận định
- **Nhận định:** trần thực tế cho "LLM đúng bao nhiêu" là **đồng thuận người–người** (κ 0,91; 94,7%), không phải 100%. Mọi đánh giá vài trăm bản ghi nên có hai người mã hóa độc lập trên một mẫu để biết trần này.
- **Nhận định:** quy trình "hai phương pháp độc lập (vd LLM + classifier hoặc hai LLM/hai prompt), người chỉ xem chỗ bất đồng" cho tỷ lệ đúng cao với ít công người; ở quy mô vài trăm, phần người duyệt chỉ vài chục bản ghi.
- **Nhận định:** cảnh báo về phân phối (von der Heyde) quan trọng trực tiếp cho mục tiêu *đếm tần suất*: độ chính xác tổng cao không bảo đảm tỷ lệ từng nhóm đúng; phải so phân phối trên mẫu gán tay (hiệu chỉnh kiểu report trước).
- **Nhận định:** kết quả Langer so với Mellon cho thấy độ khó tăng mạnh khi: đa nhãn, > 40 nhóm, nhóm do chính LLM tự đặt, và câu trả lời lạc đề/khác chiều. Văn bản 4–5 câu chứa nhiều ý thuộc đúng vùng khó này.

### Khoảng trống
- Không mở được bài Mellon, Langer, von der Heyde; các số lấy qua search hoặc qua README bậc 3. Không có số chi tiết theo từng model/cách prompt của von der Heyde.
- Không tìm thấy nghiên cứu khảo sát nào đo tỷ lệ "không xếp được" do LLM trả về.

## 7. Dựng codebook có người trong vòng lặp; "cùng ý, khác chữ"; thuật ngữ

### Kết luận ngắn
Nghiên cứu định tính 2023–2026 hội tụ về quy trình: **người viết/duyệt codebook → LLM gán theo codebook (deductive) → đo đồng thuận với người trên mẫu → sửa định nghĩa → lặp**. LLM tự sinh code (inductive) chỉ khoảng 1/3 khớp code của người, nên dùng như góc nhìn bổ sung. Đồng thuận không đồng nghĩa chất lượng: người–người cũng chỉ đồng thuận vừa phải ở codebook lớn, đa nhãn. Mức chắc chắn: trung bình.

### Phát hiện có nguồn
- Xiao và cộng sự (IUI '23): GPT-3 + codebook chuyên gia cho mã hóa deductive câu hỏi tò mò của trẻ; đồng thuận với chuyên gia "fair to substantial" (Cohen's κ); prompt dựa trên codebook tốt hơn prompt dựa trên ví dụ (qua search) — [Supporting Qualitative Analysis with LLMs: Combining Codebook with GPT-3 for Deductive Coding, arXiv 2304.10548](https://arxiv.org/abs/2304.10548v1) (bậc 1, 2023)
- Nghiên cứu tiếp theo (arXiv 2401.15170, 2024): GPT-4 zero-shot vượt ngưỡng κ 0,6 ở 8/9 nhiệm vụ, GPT-3.5 trung bình chỉ 0,34; codebook viết cho người cần viết lại cho LLM, phải thử tay lặp lại để chỉnh câu chữ (qua search) — [arXiv 2401.15170](https://arxiv.org/html/2401.15170v2) (bậc 1, 2024)
- Chew và cộng sự (RTI, LACA, 2023): GPT-3.5 trên 4 tập công khai thường đạt đồng thuận ngang người; quy trình khác thông thường ở 3 điểm: **cùng LLM phát triển codebook**, kiểm độ tin cậy người–LLM, rồi mới thay mã tay bằng LLM cho toàn bộ dữ liệu; giúp nhận ra code mà LLM "randomly guessing" và quyết định khi nào dùng LLM hay người; LLM có xu hướng hiểu định nghĩa quá rộng (qua search) — [LLM-Assisted Content Analysis, arXiv 2306.14924](https://arxiv.org/abs/2306.14924v1) (bậc 1, 2023-06)
- Dai, Xiong, Ku (Findings EMNLP 2023): LLM-in-the-loop cho thematic analysis; người viết ví dụ và prompt, LLM (GPT-3.5) trích code ban đầu bằng in-context learning, hỗ trợ cả quy nạp lẫn diễn dịch; hai case study khảo sát (nghe nhạc, password manager) đạt chất lượng gần người mà giảm công và thời gian (qua search) — [LLM-in-the-loop, arXiv 2310.15100](https://arxiv.org/abs/2310.15100v1) (bậc 1, 2023)
- Tai và cộng sự (Int. J. Qualitative Methods 23, 2024): nhập mỗi văn bản mẫu 160 lần, coi mỗi lần là một "người mã hóa" mới, để đo độ ổn định của LLM khi gán theo codebook kèm bằng chứng trích dẫn (qua search) — [An Examination of the Use of LLMs to Aid Analysis of Textual Data, DOI 10.1177/16094069241231168](https://doaj.org/article/25c5015365a0467da462b8a73e3e2f56) (bậc 1, 2024-01)
- JMIR Formative Research (2026), GPT-4o mã hóa quy nạp một transcript nhóm tập trung: 137 code, 31,4% khớp code người, 26,3% là phương án hợp lý khác, 42,3% không hợp lý (qua search) — [LLM-Assisted Thematic Coding in Medical Education Research](https://doi.org/10.2196/85572) (bậc 1, 2026)
- So sánh cách prompt sinh codebook quy nạp: prompt theo chunk tìm nhiều insight, ít lỗi bám nguồn, nhưng code quá rộng và chồng chéo (qua search) — [Prompts Matter, arXiv 2411.06316](https://arxiv.org/pdf/2411.06316) (bậc 1, 2024)
- "Agreement Is Not Quality" (arXiv 2607.28890, 2026): 5 hệ LLM và 3 người mã hóa đã huấn luyện áp codebook phân cấp 72 mục lên 2.560 tin nhắn của giáo viên; Jaccard người–LLM trung bình 0,30 so với người–người 0,52; nhưng chuyên gia kiểm mù chọn bản của người và của LLM gần ngang nhau (51,5% vs 48,5%, p = 0,537); ở vài code, đồng thuận của người chứa thiên kiến chung bị chuyên gia bác (qua search) — [Agreement Is Not Quality](https://arxiv.org/pdf/2607.28890) (bậc 1, 2026)
- Hệ số đồng thuận hiệu chỉnh ngẫu nhiên giả định đơn nhãn và phạt chồng lấn một phần như bất đồng hoàn toàn, nên kém phù hợp cho mã hóa đa nhãn (qua search) — [Human-LLM Collaborative Inductive Coding, arXiv 2607.28889](https://arxiv.org/pdf/2607.28889) (bậc 1, 2026)
- TopicGPT (NAACL 2024): pipeline 4 bước — sinh topic cấp 1 (tùy chọn cấp 2), tinh chỉnh (gộp topic gần trùng, bỏ topic tần suất thấp), **gán topic cho từng văn bản kèm trích dẫn hỗ trợ**, sửa lại phần gán chưa bám danh sách; hỗ trợ OpenAI, Vertex, Azure, Gemini, vLLM; có sẵn metric ARI, Harmonic Purity, NMI — [chtmp223/topicGPT README](https://github.com/chtmp223/topicGPT) (bậc 1, đã mở, 2024)

### Nhận định
- **Nhận định:** quy trình đề xuất cho vài trăm bản ghi, rút từ LACA + TopicGPT + Mellon: (1) LLM đọc toàn bộ hoặc một mẫu và đề xuất danh sách nguyên nhân; (2) người gộp/tách/đặt tên, viết định nghĩa + ví dụ biên; (3) LLM gán đa nhãn theo codebook, bắt buộc kèm trích dẫn câu làm bằng chứng và cho phép "khác/không rõ"; (4) hai người mã hóa độc lập 50–100 bản ghi để đo trần người–người và độ khớp người–LLM theo từng code; (5) sửa định nghĩa ở code yếu, chạy lại.
- **Nhận định:** "cùng nguyên nhân, khác chữ" được giải ở mảng này không bằng embedding mà bằng **định nghĩa code + ví dụ** để LLM suy luận; với vài trăm bản ghi, đây có lẽ là cách thẳng nhất. Jargon/viết tắt được đưa vào codebook như phần giải nghĩa (giống domain-term explanation ở DBRD, thesaurus ở Nestor).
- **Nhận định:** với đa nhãn nên đo đồng thuận bằng Jaccard hoặc κ theo từng code (nhị phân có/không), không dùng một κ cho cả bộ.

### Khoảng trống
- Không lấy được bảng κ theo dataset của LACA và của Xiao 2023; con số Gwet's AC1 0,23–1 của LACA chỉ từ bản tóm tắt thứ cấp nên không ghi vào phát hiện.
- Không có bằng chứng định lượng trực tiếp về việc LLM xử lý ký hiệu kỹ thuật (IP, path, lệnh) trong mã hóa định tính.

## 8. Bài học xuyên ngành

### Kết luận ngắn
(a) Hệ thống thực tế gần như luôn **taxonomy trước (hoặc dựng taxonomy một lần rồi chốt), gán sau**; khám phá chỉ dùng để dựng/cập nhật taxonomy. (b) Nhiều case **rút trường/tóm tắt trước** rồi mới so khớp hoặc gán. (c) Đồng thuận LLM–chuyên gia: cao ở nhóm thô, codebook rõ; thấp ở cấp mịn, đa nhãn, nhóm hiếm. (d) Hầu như không ai công bố tỷ lệ "không xếp được". Mức chắc chắn: trung bình.

### Bảng tổng hợp (cỡ dữ liệu và mức chuyển được sang vài trăm bản ghi)

| Case | Cỡ dữ liệu | Thô hay trích trước | Taxonomy trước / khám phá | Kết quả chính | Chuyển sang vài trăm bản ghi |
|---|---|---|---|---|---|
| RCACopilot (Microsoft) | 653 sự cố/1 năm | Tóm tắt 120–140 từ rồi truy hồi | Nhóm có sẵn | Micro-F1 0,766, Macro-F1 0,533; baseline < 0,1 | Cao: đúng cỡ; few-shot với ví dụ tương tự |
| Ahmed ICSE 2023 | > 40.000 sự cố | Chỉ tiêu đề + tóm tắt | Sinh văn bản tự do | > 70% engineer chấm ≥ 3/5 | Thấp (cần fine-tune, dữ liệu lớn) |
| AutoARTS (Azure) | > 2.000 postmortem | Trích snippet theo yếu tố | Taxonomy phân cấp dựng tay rồi gán | Đa nhãn F1 0,89 (qua search) | Cao về thiết kế: đa nhãn + phân cấp |
| Salesforce ICA | ~2.000 bản điều tra | Trích triệu chứng/nguyên nhân/xử lý | Đồ thị tri thức | Chưa có số | Trung bình |
| CUPID (DBRD) | Kho ~10k report/project | LLM rút keyword rồi REP | Không (truy hồi cặp) | RR@10 0,59–0,67 | Trung bình: bước rút ý |
| Domain-term explanation | 92.854 report | Thêm giải nghĩa jargon | Không | Tăng ở cả 7 baseline | Trung bình: giải nghĩa thuật ngữ |
| MAUDE IMDRF (2026) | 10.000 → 1.728/1.224 | Thô | Taxonomy chính thức | 59% cấp 1 → 23% cấp 3 | Cao: cảnh báo cấp mịn |
| Crash narrative | 50 narrative có nhãn chuyên gia | Thô | Có sẵn | Accuracy ≠ đồng thuận chuyên gia | Cao: cách đánh giá |
| Nestor / work order | Hàng nghìn MWO | Token → alias | Người dựng tag | −88% thời gian, kém chính xác hơn (Lutz) | Cao: thesaurus viết tắt |
| Mellon (BES) | 50 nhóm, cỡ mẫu test chưa rõ | Thô | Codebook có sẵn | 93,9% vs người 94,7% | Cao |
| ai-survey-coding-eval | dev 300 + test 1.200 | Thô | Codebook có sẵn | 95–96%, κ 0,93–0,95 (Llama 8B local) | Cao: đúng cỡ, on-prem |
| Langer pilot | 1.166 câu, 45 nhóm, đa nhãn | Thô | AI tự tạo nhóm | "poor"; khớp đủ mã 29% (bậc 3) | Cao: phản ví dụ |
| von der Heyde | 5.072 câu (fine-tune 1.024) | Thô | Codebook | Chỉ fine-tune đạt; phân phối lệch | Cao: cảnh báo phân phối |
| Agreement Is Not Quality | 2.560 tin nhắn, 72 code | Thô | Codebook phân cấp | Jaccard 0,30 vs 0,52; mù 51,5/48,5 | Cao: cách đánh giá |
| JMIR inductive | 1 transcript | Thô | LLM tự sinh | 31% code khớp người | Cao: giới hạn khám phá bằng LLM |

(Mọi số trong bảng lấy từ các phát hiện có nguồn ở mục 1–7.)

### Nhận định
- **Nhận định:** "cluster văn bản thô" gần như không xuất hiện trong các case vận hành; các case có kết quả tốt đều đưa vào LLM một **danh sách nhóm có định nghĩa** hoặc rút trường trước. Gom cụm/khám phá đóng vai dựng danh sách ban đầu (TopicGPT, LACA, AutoARTS dựng taxonomy tay từ > 2.000 postmortem).
- **Nhận định:** ở quy mô vài trăm, chi phí người cho một vòng codebook + hai người mã hóa 50–100 bản ghi là nhỏ so với rủi ro báo sai tần suất; đây là điểm khác lớn so với quy mô triệu dòng của report trước.
- **Nhận định:** nên luôn có nhãn "khác/không rõ" và báo tỷ lệ của nó; các case công khai không báo con số này nên không có chuẩn so sánh.

### Khoảng trống
- Không tìm thấy case nào công bố tỷ lệ bản ghi "không xếp được" (uncategorized) sau khi gán bằng LLM.
- Không tìm thấy nghiên cứu so sánh trực tiếp "gom văn bản thô" với "trích ý rồi gom" trong các ngành này (bằng chứng định lượng cho câu hỏi phụ 1 phải lấy từ góc khác).
- Phần lớn bản gốc không mở được do proxy; mọi số "(qua search)" cần verifier đối chiếu nếu có đường vào.

## Truy vấn đã chạy
- Cupid LLM duplicate bug report detection (standard)
- RCACopilot root cause analysis incidents Microsoft LLM (standard)
- NASA ASRS narratives LLM classification (standard)
- LLM coding open-ended survey responses agreement human coders (standard)
- LLM deductive coding qualitative analysis codebook GPT-3 Xiao 2023 agreement (standard)
- Ahmed ICSE 2023 recommending root-cause mitigation cloud incidents LLM 40,000 incidents (standard)
- LLM-assisted content analysis LACA Chew 2023 deductive coding kappa (standard)
- Meta engineering AI incident response root cause 42% accuracy (standard)
- Mellon "Do AIs know what the most important issue is" open-ended survey GPT coding (standard)
- Langer Research pilot test AI coding open-ended survey responses Texas Education Poll results (extended)
- "AIn't Nothing But a Survey" LLM coding German open-ended responses results fine-tuning (extended)
- LLM-in-the-loop thematic analysis Dai 2023 codebook human-AI collaboration (standard)
- Tai 2024 large language models deductive coding qualitative data codebook repeated runs IJQM (standard)
- "Duplicate Bug Report Detection: How Far Are We" TOSEM age bias REP outperforms deep learning (standard)
- domain term explanation duplicate bug report detection LLM 2025 results (standard)
- "Understanding the Impact of Domain Term Explanation on Duplicate Bug Report Detection" (standard)
- MaintNet maintenance logbook dataset abbreviations technical language (standard)
- FDA MAUDE adverse event narratives large language model classification device problem codes (standard)
- Mining Root Cause Knowledge from Cloud Service Incident Investigations AIOps Salesforce ICA (standard)
- CFPB consumer complaint narratives topic modeling LLM classification issue product (standard)
- ASRS narratives large language model human factors classification 2024 accuracy anomaly (extended)
- "Accuracy is Not Agreement" crash narrative classification expert-aligned evaluation results (standard)
- "Leveraging LLMs for Structured Information Extraction and Analysis from Cloud Incident Reports" (standard)
- LLM postmortem analysis incident reports taxonomy clustering root cause categories public postmortems study (standard)
- Schonlau open-ended survey questions automatic coding uncertain responses human 2023 2024 LLM (standard)
- AutoARTS Dogga ATC 2023 taxonomy contributing factors precision recall labelling tool keywords (extended)
- RCACopilot micro-F1 macro-F1 FastText XGBoost baseline root cause categories incidents dataset 653 (extended)
- Mellon Research & Politics 2024 LLM coding open-text survey 50 categories Claude 93.9% second human coder (standard)
- RCACopilot summarization diagnostic information ablation "without summary" new root cause category unseen incidents (extended)
- NIST technical language processing maintenance work orders LLM 2024 annotation agreement (standard)
- LLM inductive coding codebook generation open-ended responses evaluation human themes overlap 2024 2025 (extended)
- Hastings Sexton Brundage Hodkiewicz 2019 agreement isolated experts tagging maintenance work orders (extended)
- Nestor tagging maintenance work orders percent tagged hour annotation vocabulary Sexton Brundage results (extended)
- Chew LLM-assisted content analysis GPT-3.5 four datasets kappa human coders codebook co-development results (extended)
- KPI extraction maintenance work orders wind turbines expert labeling text classification AI-assisted tagging comparison results (standard)
- "Agreement Is Not Quality" blind expert verification human LLM qualitative coding (standard)
- Tikayat Ray 2023 ChatGPT ASRS narratives synopsis human factors 61% concurrence 210 reports (standard)
- duplicate bug report detection LLM embeddings 2024 2025 empirical study GPT recall@k comparison REP SABD (standard)
- NTSB accident narratives LLM probable cause classification human factors 2024 2025 (standard)
