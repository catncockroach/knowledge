# Đánh giá, thống kê và thực tiễn ngành

> **Lưu ý phương pháp:** trong phiên này proxy chặn `WebFetch` tới hầu hết các host (arxiv.org, nist.gov, emerald.com, phmsociety.org, link.springer.com, pmc.ncbi.nlm.nih.gov, scikit-learn.org đều bị từ chối CONNECT). Chỉ đọc trực tiếp được tài liệu scikit-learn qua `raw.githubusercontent.com`. Các phát hiện còn lại lấy từ phần tóm tắt/trích đoạn mà `WebSearch` trả về (thường là abstract hoặc trang tài liệu chính thức). Những phát hiện đó ghi "(qua search)" và nên được verifier mở lại nguồn khi có mạng.

## 1. Khi nào nhóm đủ tốt để tin con số tần suất

### Kết luận ngắn
Metric nội tại (silhouette, Davies-Bouldin, Calinski-Harabasz, DBCV) chỉ dùng để so sánh tương đối các cấu hình, không chứng minh được nhóm "đúng nghĩa". Bằng chứng đáng tin là đối chiếu với một mẫu do người gán nhãn: metric có hiệu chỉnh cơ hội (ARI, AMI) cộng với độ chính xác sau khi ánh xạ cụm→nhãn. Mức đồng thuận giữa hai người gán nhãn (Krippendorff α / Cohen κ) là trần thực tế. Bổ sung bằng độ ổn định bootstrap (Jaccard theo cụm) và tỷ lệ "khác/noise". Mức chắc chắn: **cao** cho tính chất của metric (docs chính thức), **trung bình** cho ngưỡng cụ thể (vì đó là quy ước, không phải định lý).

### Phát hiện có nguồn
- Silhouette, Calinski-Harabasz và Davies-Bouldin đều "generally higher for convex clusters than other concepts of clusters", nên chấm thấp các cụm dựa trên mật độ như kết quả DBSCAN. Davies-Bouldin còn dùng khoảng cách centroid nên "limits the distance metric to Euclidean space" — [scikit-learn User Guide: Clustering performance evaluation (clustering.rst)](https://raw.githubusercontent.com/scikit-learn/scikit-learn/main/doc/modules/clustering.rst) (bậc 1, bản main, đọc 2026-10-21)
- ARI: nhãn ngẫu nhiên cho điểm gần 0.0, còn Rand index chưa hiệu chỉnh "often close to 1.0 even if the clusterings themselves differ significantly". NMI và MI "are not adjusted against chance". V-measure/homogeneity/completeness không chuẩn hóa theo cơ hội: "random labeling won't yield zero scores especially when the number of clusters is large". Với mẫu nhỏ hoặc nhiều cụm thì "it is safer to use an adjusted index such as the Adjusted Rand Index (ARI)" — [scikit-learn clustering.rst](https://raw.githubusercontent.com/scikit-learn/scikit-learn/main/doc/modules/clustering.rst) (bậc 1, đọc 2026-10-21)
- Ví dụ chính thức của scikit-learn: V-measure trung bình của nhãn ngẫu nhiên tăng mạnh khi số cụm tiến gần số mẫu. Chỉ các metric đã hiệu chỉnh mới dùng an toàn làm "consensus index" để đánh giá độ ổn định trên các mẫu con chồng lấn — [Adjustment for chance in clustering performance evaluation](https://scikit-learn.org/1.8/auto_examples/cluster/plot_adjusted_for_chance_measures.html) (bậc 1, qua search, 2025)
- FAQ của HDBSCAN: thuật toán "can do well on up to around 50 or 100 dimensional data, but performance can see significant decreases beyond that". Embedding câu thường có 384–1024 chiều, nên thường phải giảm chiều (UMAP/PCA) trước khi chạy — [hdbscan FAQ](https://hdbscan.readthedocs.io/en/stable/faq.html) (bậc 1, qua search, không rõ ngày)
- DBCV được thiết kế cho clustering mật độ và có tính đến noise (khoảng −1 đến 1). Tuy vậy, các tutorial tune `min_cluster_size`/`min_samples` bằng cách tối đa hóa DBCV, tức là dễ overfit chính metric đó. Search không tìm được nghiên cứu nào về hành vi của DBCV trong không gian embedding nhiều chiều — [How To Tune HDBSCAN (Towards Data Science)](https://towardsdatascience.com/tuning-with-hdbscan-149865ac2970/) (bậc 3, chỉ dùng làm manh mối)
- Ổn định bootstrap: `fpc::clusterboot` (theo Hennig 2007) lấy mẫu lại bằng bootstrap/subset/jitter/thay điểm bằng noise, rồi tính Jaccard giữa mỗi cụm gốc và cụm khớp nhất trong mẫu lại. Hướng dẫn diễn giải: Jaccard trung bình < 0.6 thì không nên tin cụm, ≥ 0.85 là "highly stable", ≤ 0.5 là dấu hiệu "dissolved cluster". Bản 2.1-11 cũ hơn lấy 0.75 làm mốc "valid, stable". Tài liệu cũng cảnh báo phương pháp cứng nhắc có thể cho cụm ổn định mà vẫn sai — [clusterboot {fpc} R documentation](https://search.r-project.org/CRAN/refmans/fpc/html/clusterboot.html) (bậc 1, qua search, không rõ ngày)
- Krippendorff α: tin được khi α ≥ 0.800, chỉ kết luận tạm khi 0.667–0.800, bỏ dữ liệu khi < 0.667. α xử lý được nhiều người mã hóa, dữ liệu thiếu và mọi thang đo — [CASRAI: Krippendorff's alpha](https://casrai.org/guides/krippendorffs-alpha) (bậc 2, qua search); [Reliability in SE Qualitative Research through Inter-Coder Agreement (arXiv 2008.00977)](https://arxiv.org/pdf/2008.00977) (bậc 1, qua search, 2020). ATLAS.ti khuyên mỗi mã cần đủ lượt mã hóa để riêng cơ hội đã sinh ≥ 5 lần đồng thuận — [ATLAS.ti: Sample Size and Decision Rules](https://doc.atlasti.com/ManualWin/ICA/ICASampleSizeAndDecisionRules.html) (bậc 1, qua search)
- TnT-LLM (Microsoft, KDD 2024) đo đồng thuận giữa nhiều người gán nhãn bằng Cohen κ (từng cặp) và Fleiss κ (nhóm), lấy nhãn đồng thuận bằng bỏ phiếu/thảo luận, rồi xem LLM như một người gán nhãn thêm và đo κ của nó với nhãn đồng thuận. Ngưỡng dùng trong bảng: moderate (0.4–0.6], substantial > 0.6. Tác giả lưu ý LLM xấp xỉ được ý kiến tập thể ở một số tác vụ nhưng "struggle" với phán đoán chủ quan, tinh tế — [TnT-LLM (Microsoft Research)](https://www.microsoft.com/en-us/research/?p=1017927) (bậc 1, qua search, 2024); trích đoạn qua [mirror Hackernoon](https://www.hackernoon.com/evaluating-tnt-llm-text-classification-human-agreement-and-scalable-llm-metrics) (bậc 3)
- Clio (Anthropic) kiểm chứng pipeline tóm tắt→gom cụm bằng một tập 19.476 hội thoại tổng hợp sinh từ một cây chủ đề đã biết: dựng lại đúng danh mục gốc với độ chính xác 94%, so với 5% nếu đoán ngẫu nhiên, và giữ được mức này qua nhiều ngôn ngữ (Phụ lục C). Đây là cách "gieo nhãn đã biết rồi xem có tìm lại được không" — [Clio: Privacy-Preserving Insights into Real-World AI Use (arXiv 2412.13678)](https://arxiv.org/pdf/2412.13678) (bậc 1, qua search, 2024-12)
- Cỡ mẫu kiểm tra: muốn ước lượng độ chính xác với khoảng tin cậy 90% và bán kính ±0.05 thì cần ít nhất 271 mẫu gán nhãn (Z-test). Bán kính khoảng tin cậy giảm theo căn bậc hai của n, nên muốn thu hẹp một nửa thì cần gấp khoảng 4 lần số nhãn. Độ chính xác kỳ vọng càng cao thì khoảng càng hẹp — [confidence-planner (arXiv 2301.05702)](https://arxiv.org/pdf/2301.05702) (bậc 1, qua search, 2023); [Estimating Uncertainty in Classifier Performance… (arXiv 2606.26422)](https://arxiv.org/pdf/2606.26422) (bậc 1, qua search, 2026-06)
- Tỷ lệ "khác" làm tín hiệu chất lượng: guide mã hóa câu hỏi mở khuyên < 10% câu trả lời rơi vào "Other", đọc ít nhất 10% câu trả lời trước khi dựng code frame, và không dựng xong toàn bộ frame trước khi bắt đầu mã hóa — [Thematic: 3 best practices for coding open-ended questions](https://getthematic.com/insights/3-best-practices-for-coding-open-ended-questions) (bậc 3, vendor; dùng như quy ước thực hành)
- Zendesk gắn cho mỗi dự đoán intent một nhãn confidence High/Medium/Low. Một tài khoản chỉ đủ điều kiện khi mẫu có ≥ 30% ticket ở mức high và ≥ 60% ở mức medium, tức là dùng tỷ lệ dự đoán tự tin làm cổng chất lượng — [Zendesk: Automatically detecting customer intent, sentiment, and language](https://support.zendesk.com/hc/en-us/articles/4550640560538-Automatically-detecting-customer-intent-sentiment-and-language) (bậc 1, qua search, không rõ ngày)

### Nhận định
- Quy trình kiểm chứng hợp lý: (1) lấy mẫu ngẫu nhiên phân tầng theo cụm, khoảng 300–500 dòng; (2) hai người gán nhãn độc lập, tính α hoặc κ; nếu α < 0.667 thì vấn đề nằm ở định nghĩa danh mục chứ chưa phải ở thuật toán; (3) so cụm với nhãn đồng thuận bằng ARI/AMI cộng với accuracy sau ánh xạ đa số (purity, dễ giải thích cho người đọc báo cáo); (4) chạy lại với 5–10 seed/bootstrap, giữ các cụm có Jaccard ≥ 0.75; (5) theo dõi tỷ lệ noise/"khác".
- Purity và V-measure tăng dần khi số cụm tăng, nên luôn báo kèm ARI/AMI hoặc kiểm soát số cụm.
- Với dữ liệu kiểu này, accuracy sau ánh xạ không nên vượt mức đồng thuận giữa người với người. Nếu vượt thì nghi mẫu kiểm tra bị lệch.

### Khoảng trống
- Chưa đọc được bài gốc DBCV (Moulavi et al., 2014) và bài benchmark nào về DBCV/silhouette trên embedding câu. Không có số liệu.
- Không có nguồn bậc 1 nào cho ngưỡng "tỷ lệ noise chấp nhận được" khi dùng HDBSCAN. Con số < 10% "Other" chỉ đến từ vendor khảo sát.
- Chưa lấy được các giá trị κ cụ thể trong bảng của TnT-LLM.

## 2. Thống kê trên các nhóm thu được

### Kết luận ngắn
Đếm thẳng nhãn của classifier ("classify and count", CC) cho tỷ lệ bị lệch có hệ thống, nhất là khi tỷ lệ thật khác tỷ lệ trong tập huấn luyện. Cần hiệu chỉnh bằng TPR/FPR đo trên tập kiểm tra (ACC, Forman) hoặc dùng thư viện quantification (QuaPy). Mỗi tỷ lệ nên kèm khoảng tin cậy: Wilson cho từng nhóm, Sison-Glaz/Goodman cho khoảng đồng thời. Khi so giữa các nhóm con, kiểm tra điều kiện kỳ vọng ≥ 5 hoặc dùng Fisher. Mức chắc chắn: **cao** về nguyên lý, **trung bình** về áp dụng cho nhiều lớp.

### Phát hiện có nguồn
- Forman định nghĩa bài toán quantification là ước lượng số ca dương (hoặc phân phối lớp) trong tập test, khi tập huấn luyện có thể có phân phối khác hẳn. Các phương pháp vẫn hữu ích khi dữ liệu huấn luyện ít, phân phối test lệch xa và lớp dương hiếm — [Quantifying counts and costs via classification, Forman, DMKD 17 (2008), DOI 10.1007/s10618-008-0097-y](https://datalearner.com/academic/journal-papers/1384-5810/volumes-and-issues/17/paper-detail/9256) (bậc 1 qua bản ghi metadata, qua search, 2008)
- ACC: tỷ lệ đếm được p̂_CC = TPR·p + FPR·(1−p), nên p = (p̂_CC − FPR)/(TPR − FPR), với TPR và FPR đo trên tập kiểm tra. Bunse (2022) cho thấy ACC dạng bình phương tối thiểu có ràng buộc (cho nhiều lớp) thường hoạt động tốt — [Adjusted Count Quantification Learning on Graphs (arXiv 2503.09395)](https://arxiv.org/pdf/2503.09395) (bậc 1, qua search, 2025)
- Classifier tối ưu FP+FN, còn quantifier cần tối ưu |FP−FN|. CC cho kết quả kém "especially in scenarios characterized by distribution shift". Phản biện: CC được tune bằng loss của quantification thì gần đạt state of the art, dù vẫn kém một số phương pháp mới nhất — [Moreo & Sebastiani, Re-Assessing the "Classify and Count" Quantification Method (ar5iv 2011.02552)](https://ar5iv.labs.arxiv.org/html/2011.02552) (bậc 1, qua search, 2021)
- QuaPy (Moreo, Esuli, Sebastiani, CIKM 2021, trang 4534–4543) là thư viện Python BSD-3, cài bằng `pip install quapy`. Nó có các phương pháp baseline và nâng cao (ví dụ `qp.method.aggregative.ACC()`), model selection hướng quantification và các giao thức đánh giá — [QuaPy trên PyPI](https://pypi.org/project/QuaPy) (bậc 1, qua search); [QuaPy CIKM paper](https://ir.webis.de/anthology/2021.cikm_workshop-2021w.44) (bậc 1, qua search, 2021)
- Sách *Learning to Quantify* (Esuli, Fabris, Moreo, Sebastiani; Springer Information Retrieval Series vol. 47, 2023) là sách open access, 137 trang — [Springer](https://link.springer.com/book/978-3-031-20467-8) (bậc 1, qua search, 2023-03)
- Khoảng tin cậy đồng thời cho tỷ lệ đa thức: Sison-Glaz (JASA 1995), có trong gói R `MultinomialCI`. `DescTools::MultinomCI` có các tùy chọn Sison-Glaz, Goodman (Technometrics 1965), Wald, Wald có hiệu chỉnh liên tục và Wilson. Một nguồn thứ cấp nói Goodman kém khi số đếm kỳ vọng rất nhỏ, còn Sison-Glaz có độ phủ gần danh nghĩa hơn — [MultinomialCI refman](https://cran.uni-muenster.de/web/packages/MultinomialCI/refman/MultinomialCI.html) (bậc 1, qua search); [DescTools MultinomCI](https://www.quantargo.com/help/r/latest/packages/DescTools/0.99.41/MultinomCI.html) (bậc 1, qua search); nhận xét về độ phủ từ [MetricGate](https://metricgate.com/docs/goodman-simultaneous-multinomial-ci/) (bậc 3)
- So sánh tỷ lệ giữa các nhóm con (bảng chéo nhóm × nguồn): quy tắc phổ biến là mọi tần số kỳ vọng > 1 và không quá 20% ô có kỳ vọng < 5. Nếu vượt thì dùng Fisher exact, áp dụng được cho bảng r×c. Cochran (1952, 1954) đòi chặt hơn. Kỳ vọng thấp làm tăng sai lầm loại I — [The Analysis Factor: Chi-Square rule of thumb](https://www.theanalysisfactor.com/chi-square-test-of-independence-rule-of-thumb/) (bậc 2, qua search); [HealthyR: Fisher's exact test](https://argoshare.is.ed.ac.uk/healthyr_book/fishers-exact-test.html) (bậc 2, qua search)
- Phân cấp thô→mịn trong sản phẩm thật: Intercom Topics Explorer tìm *subtopic* trước bằng cách gom cụm các câu hỏi tương tự, rồi gộp subtopic thành *topic* rộng hơn; tiêu đề do AI sinh, không dựa trên từ khóa định trước. Mỗi topic có metric riêng (CX score, tỷ lệ giải quyết, thời gian xử lý) — [Intercom Help: Use the Topics Explorer](https://www.intercom.com/help/en/articles/11390087-use-the-topics-explorer-to-see-what-s-driving-volume) (bậc 1, qua search, không rõ ngày)
- Danh mục con quá nhỏ thì không đủ lực thống kê để phát hiện khác biệt thật giữa các nhóm. Một hai câu "Other" làm hàng "Other" trong bảng chéo rất thưa — [Mosaic of Minds: Why survey researchers don't want "Other"](https://mosaicofmindss.substack.com/p/why-avoid-saying-other-on-a-survey) (bậc 3, manh mối)

### Nhận định
- Trình bày: biểu đồ Pareto (cột giảm dần cộng đường tích lũy) ở cấp thô, gộp mọi nhóm < 1–2% vào một dòng "đuôi dài (N nhóm)", có drill-down sang cấp mịn. Mỗi cột hiện tỷ lệ kèm khoảng Wilson 95%. Wilson là công thức sách giáo khoa, có trong `statsmodels.stats.proportion.proportion_confint(method="wilson")` (nguồn chưa đọc trực tiếp ở phiên này).
- Khi gán nhóm bằng classifier/LLM và có tập kiểm tra, nên báo cả hai con số: tỷ lệ CC và tỷ lệ đã hiệu chỉnh bằng ACC với ma trận nhầm lẫn. Với nhiều lớp, ACC là giải hệ p̂ = M·p (M là ma trận P(dự đoán|thật)) với ràng buộc p ≥ 0, Σp = 1.
- Khi so theo cột phân nhóm (nguồn/loại), gộp các nhóm hiếm trước theo cây phân cấp đã định sẵn (không gộp sau khi xem kết quả), rồi mới chạy chi-square hoặc Fisher. Nếu so nhiều cặp thì hiệu chỉnh đa so sánh.

### Khoảng trống
- Chưa đọc trực tiếp được bài của Forman, Bunse 2022 hay sách *Learning to Quantify*: không có số liệu về sai số CC vs ACC trên văn bản ngắn.
- Không tìm được nguồn bậc 1 nào hướng dẫn cụ thể cỡ mẫu tối thiểu cho mỗi nhóm con khi so tỷ lệ danh mục. Mới có quy tắc kỳ vọng ≥ 5.
- Chưa có nguồn cho cách lan truyền sai số khi vừa có sai số gán nhóm vừa có sai số lấy mẫu (bootstrap trên cả tập kiểm tra là một hướng, chưa có trích dẫn).

## 3. Nhóm mới và drift theo thời gian

### Kết luận ngắn
Thực tiễn chung: một taxonomy cố định gán bản ghi mới theo ngày, kèm (a) theo dõi tỷ lệ "khác/không gán được/độ tự tin thấp", (b) định kỳ chạy lại khám phá (gom cụm lại) trên phần chưa gán, (c) người duyệt và đổi tên nhóm. Active learning ưu tiên mẫu bất định cho người gán nhãn. Mức chắc chắn: **trung bình**. Có tài liệu sản phẩm và guide, nhưng ít nghiên cứu định lượng về ngưỡng.

### Phát hiện có nguồn
- Intercom: mô hình topic ban đầu dùng hội thoại của 90 ngày gần nhất, sau đó một pipeline hằng ngày gán topic cho hội thoại mới đóng. "Topic Curation" cho phép đổi tên topic/subtopic theo ngôn ngữ của team. Topics Explorer hiện chỉ hỗ trợ tiếng Anh — [Intercom Help: Topics Explorer](https://www.intercom.com/help/en/articles/11390087-use-the-topics-explorer-to-see-what-s-driving-volume); [How to tailor your AI topics with topic curation](https://intercom.help/fin4all/en/articles/13753506-how-to-tailor-your-ai-topics-with-topic-curation) (bậc 1, qua search, không rõ ngày)
- Mã hóa câu hỏi mở: khi nhóm "Other" phình quá lớn thì thêm mã mới. Khi có danh mục mới, "all previously coded responses need to be re-analyzed" — [Thematic best practices](https://getthematic.com/insights/3-best-practices-for-coding-open-ended-questions) (bậc 3, vendor; quy ước thực hành)
- Schonlau & Couper (Survey Research Methods 10(2), 2016, tr. 143–152): máy tự phân loại các câu trả lời "dễ", người mã hóa phần còn lại, ngưỡng dễ/khó chọn theo độ chính xác kỳ vọng. Với mục tiêu 80% độ chính xác tổng thể, 54%–80% dữ liệu được phân loại tự động (dùng multinomial boosting). Tác giả kết luận thuật toán chưa đủ chính xác để thay hẳn người mã hóa — [Semi-automated categorization of open-ended questions (SSOAR)](https://www.ssoar.info/ssoar/handle/document/49780?show=full) (bậc 1, qua search, 2016)
- Label Studio: vòng active learning tự động (webhook kích hoạt `fit()` khi có annotation mới, `predict()` khi người gán nhãn mở task tiếp, sắp task theo prediction score) chỉ có ở bản Enterprise. Bản Community phải sắp task và lấy prediction thủ công — [Label Studio docs: Set up active learning](https://docs.humansignal.com/guide/active_learning) (bậc 1, qua search, không rõ ngày)
- Zendesk cho admin thêm custom topic ngoài taxonomy intent mặc định. Theo một blog thứ cấp, "Intent" được đổi tên thành "Topic" vào 06/2026 (chưa xác nhận trên docs chính thức) — [Zendesk Help](https://support.zendesk.com/hc/en-us/articles/4550640560538-Automatically-detecting-customer-intent-sentiment-and-language) (bậc 1, qua search); [eesel.ai](https://eesel.ai/blog/zendesk-intelligent-triage) (bậc 3)
- Tavakoli, Bankey, Bravo (arXiv 2606.26595, 06/2026; Western Ontario và Canada Revenue Agency): framework kết hợp LLM (fine-tune, lượng tử hóa), kỹ thuật thống kê và human-AI collaboration để phát hiện chủ đề mới nổi trong phản hồi dịch vụ đa ngôn ngữ, cùng chênh lệch giữa các nhóm dân cư. Đánh giá bằng phân tích tương đồng và review của cán bộ thuế: khớp chuyên gia hơn baseline; human-in-the-loop giảm hallucination. Chỉ đọc được abstract — [LLM-based Models for Detecting Emerging Topics in Service Feedback](https://arxiv.org/pdf/2606.26595) (bậc 1, qua search, 2026-06)
- Tách bước khám phá chủ đề khỏi taxonomy chính thức: nhiều team chạy topic discovery trước khi chốt taxonomy, còn noise point của HDBSCAN có thể báo sớm vấn đề mới — các bài thực hành tổng hợp qua search (bậc 3, không trích làm bằng chứng)

### Nhận định
- Thiết kế đề xuất: taxonomy có số phiên bản (v1, v2…), mỗi bản ghi lưu `category_id` kèm `taxonomy_version` và `assign_method` (template/cache/classifier/LLM/người). Khi gộp hoặc tách nhóm, giữ bảng ánh xạ cũ→mới để chuỗi thời gian vẫn so được.
- Tín hiệu kích hoạt khám phá lại: tỷ lệ "khác"/confidence thấp vượt ngưỡng (vd > 10% hoặc tăng gấp đôi so với baseline 4 tuần), hoặc một cụm mới trong phần chưa gán đạt kích thước tối thiểu.
- Cách của Schonlau (máy làm phần chắc, người làm phần khó) chuyển thẳng được sang pipeline: ngưỡng confidence quyết định dòng nào vào hàng đợi review. Nhãn người sinh ra quay lại làm tập kiểm tra cho bước ACC ở mục 2.

### Khoảng trống
- Không tìm được nguồn bậc 1 nào cho ngưỡng cảnh báo drift cụ thể (tỷ lệ chưa gán) trên văn bản ngắn.
- Chưa có case study công khai nào mô tả versioning taxonomy (ánh xạ cũ→mới) cho thống kê theo thời gian.

## 4. Case study ngành

### Kết luận ngắn
Mẫu hình lặp lại trong các nguồn công khai: (1) khám phá bằng gom cụm/LLM để dựng taxonomy phân cấp, (2) chốt taxonomy và gán hằng ngày bằng classifier, có độ tự tin, (3) người duyệt hoặc đổi tên, đo đồng thuận, (4) văn bản là feature quan trọng nhất nhưng nên kết hợp với trường có cấu trúc. Lĩnh vực bảo trì công nghiệp (NIST TLP) có tài liệu học thuật tốt nhất về văn bản ngắn, nhiều viết tắt, do người nhập. Mức chắc chắn: **trung bình**. Không tìm được bài engineering blog của Airbnb, Spotify, Shopify, Dropbox, LinkedIn hay Grab về đúng chủ đề này.

### Phát hiện có nguồn
- **Uber COTA** (KDD 2018, Molino, Zheng, Wang): v1 dùng feature engineering và biến bài toán phân loại nhiều lớp thành bài toán ranking để xử lý hàng nghìn lớp; v2 là mạng sâu encoder-combiner-decoder. A/B test production cho thời gian giải quyết giảm khoảng 10% mà không giảm hài lòng khách hàng. Đầu vào gồm tin nhắn, dữ liệu chuyến đi và lựa chọn menu của khách; văn bản là feature quan trọng nhất. Bài sau cho biết hệ chạy trên Michelangelo, gợi ý top-3 loại vấn đề, phủ > 90% ticket đến, lúc đó chỉ hỗ trợ tiếng Anh — [COTA paper (ar5iv 1807.01337)](https://ar5iv.labs.arxiv.org/html/1807.01337) (bậc 1, qua search, 2018); [Uber blog: COTA](https://www.uber.com/gb/en/blog/cota/) (bậc 1, qua search, 2018-01)
- **Intercom Topics Explorer**: gom cụm câu hỏi thành subtopic, gộp lên topic, AI tự đặt tên, không cần tag thủ công; bản cũ hơn ("Conversation topics report") dựa trên key phrase do người định nghĩa và chạy độc lập — [Intercom Help](https://www.intercom.com/help/en/articles/11390087-use-the-topics-explorer-to-see-what-s-driving-volume); [Track and understand the topics your customers chat about](https://www.intercom.com/help/en/articles/4612191-track-and-understand-the-topics-your-customers-chat-about) (bậc 1, qua search)
- **Zendesk intelligent triage**: dùng một mô hình intent chung cho mọi ngành, có trường Intent kèm Intent confidence (High/Medium/Low), cổng chất lượng ≥ 30% high / ≥ 60% medium; ngôn ngữ hạn chế, báo cáo Explore chỉ hiện intent tiếng Anh — [Zendesk Help](https://support.zendesk.com/hc/en-us/articles/4550640560538-Automatically-detecting-customer-intent-sentiment-and-language) (bậc 1, qua search)
- **Microsoft TnT-LLM** (KDD 2024, log hội thoại Bing): LLM sinh taxonomy, LLM gán nhãn giả, rồi huấn luyện classifier nhẹ; đánh giá bằng nhiều người gán nhãn (κ) và dùng GPT-4 làm người chấm phụ sau khi kiểm tra nó đồng thuận cao với người — [Microsoft Research: TnT-LLM](https://www.microsoft.com/en-us/research/?p=1017927) (bậc 1, qua search, 2024)
- **Anthropic Clio**: tóm tắt → gom cụm → phân cấp; có lớp bảo vệ riêng tư (chỉ giữ cụm đủ số tài khoản/hội thoại tối thiểu); kiểm chứng bằng dữ liệu tổng hợp có nhãn gieo sẵn (94%) — [Clio (arXiv 2412.13678)](https://arxiv.org/pdf/2412.13678) (bậc 1, qua search, 2024-12)
- **Khảo sát (Schonlau & Couper 2016)**: dữ liệu là câu hỏi mở "lý do bỏ thuốc lá" (Ontario Smoker's Helpline), lời khuyên cho bệnh nhân và một câu hỏi thăm dò về rủi ro riêng tư; cách lai máy+người tự động được 54–80% ở mức 80% độ chính xác. Nhóm này có công trình tiếp theo về mã hóa đa nhãn và dữ liệu mã hóa kép (He et al., SRM 14(3), 2020) — [SSOAR record](https://www.ssoar.info/ssoar/handle/document/49780?show=full) (bậc 1, qua search, 2016); [Haensch et al., Frontiers in Big Data 2022](https://www.frontiersin.org/articles/10.3389/fdata.2022.880554/pdf) (bậc 1, qua search, 2022)
- **Bảo trì công nghiệp, NIST Technical Language Processing**: Brundage, Sexton, Hodkiewicz, Dima, Lukens, "Technical Language Processing: Unlocking Maintenance Knowledge", *Manufacturing Letters* (online 2020-12-11, DOI 10.1016/j.mfglet.2020.11.001). Lập luận: triển khai công nghiệp dựa trên công cụ NLP vốn dành cho văn bản phi kỹ thuật, "suffering from a lack of verification, validation, and ultimately, personnel trust". Bài kêu gọi xây biểu diễn dữ liệu theo mục tiêu, định nghĩa thực thể và từ điển, và bộ dữ liệu có chú thích — [academia.edu copy](https://www.academia.edu/80398248/Technical_language_processing_Unlocking_maintenance_knowledge) (bậc 1, qua search, 2020)
- **NIST Nestor**: toolkit mã nguồn mở, human-in-the-loop, để "tag" văn bản work order bảo trì (Brundage & Sexton, J. Res. NIST 124, 2019, DOI 10.6028/jres.124.029). Công trình nền: Sexton, Brundage, Hoffman, Morris, "Hybrid Datafication of Maintenance Logs from AI-Assisted Human Tags", IEEE Big Data 2017 (DOI 10.1109/BigData.2017.8258120). Sharp, Sexton, Brundage (2017) gom cụm và tag ticket bảo trì vì "different technicians rarely describe the problem in an identical manner" — [Nestor docs](https://pages.nist.gov/nestor/) (bậc 1, qua search); [NIST: Nestor tool for natural language annotation of short texts](https://www.nist.gov/publications/nestor-tool-natural-language-annotation-short-texts) (bậc 1, qua search, 2019)
- **Hodkiewicz & Ho** (*J. Quality in Maintenance Engineering* 22(2):146–163, 2016): work order lịch sử thường thiếu hoặc sai các trường functional location, failure mode, maintenance action, status. Trường free-text, cộng với hiểu biết về quy trình bảo trì và vòng đời tài sản, cho phép cứu lại các bản ghi này bằng quy trình làm sạch dựa trên luật, minh bạch và lặp lại được (thử trên dữ liệu thiết bị di động hạng nặng của nhiều tổ chức) — [Emerald](https://www.emerald.com/insight/content/doi/10.1108/JQME-04-2015-0013/full/html) (bậc 1, qua search, 2016)
- Conte et al. (PHM Society 2021): case study work order HVAC; giá trị thiếu ở trường then chốt làm sai quyết định giám sát tài sản; dùng NLP tagging để trích dữ liệu có cấu trúc từ free text — [The Impact of Data Quality on Maintenance Work Order Analysis](https://papers.phmsociety.org/index.php/phme/article/view/2814) (bậc 1, qua search, 2021)
- Microsoft ISE: dùng GPT gán phản hồi khách bán lẻ vào một danh sách theme cố định, trả về JSON — [ISE Developer Blog](https://devblogs.microsoft.com/ise/insights_generation_from_customer_feedback_using_llms/) (bậc 1 cho mô tả của chính họ, qua search)

### Nhận định
- Cả Uber, Zendesk và Intercom đều gán nhóm theo một taxonomy cố định có confidence, không đếm trực tiếp trên cụm thô. Gom cụm chỉ dùng ở bước khám phá và cập nhật taxonomy.
- Văn bản bảo trì (ngắn, viết tắt, sai chính tả, nhiều người viết) giống nhất với dữ liệu trong brief. Bài học từ NIST: trợ giúp người gán tag thay vì tự động hóa hoàn toàn, và tin cậy đến từ kiểm chứng.

### Khoảng trống
- Không tìm được bài engineering blog công khai nào của Airbnb, Spotify, Shopify, Dropbox, LinkedIn hay Grab về gom/phân loại lý do bằng văn bản tự do ngắn (đã thử các truy vấn ở cuối file). Bài "Discovering and Classifying In-app Message Intent at Airbnb" chỉ thấy qua tóm tắt thứ cấp của Harvard Digit, không thấy bản gốc.
- Chưa có case study công khai nào về lý do hủy đơn hay lý do churn có số liệu pipeline.
- Không đọc được full text các bài NIST/PHM để lấy số liệu (vd độ phủ tag so với công gán).

## 5. Phòng ngừa từ thiết kế nhập liệu

### Kết luận ngắn
Mã lý do có cấu trúc kèm ghi chú tự do tùy chọn là thực hành chuẩn, nhưng picklist không tự động cho dữ liệu sạch. Nếu schema không khớp cách người nhập nghĩ, họ chọn sai mã hoặc dồn vào "Other" (NIST/HRA). Free text vẫn cần để cứu và bổ sung trường có cấu trúc. Cách bền nhất: lấy taxonomy khai phá từ cụm làm picklist, giữ ô "khác — ghi rõ", và theo dõi tỷ lệ "khác" để bổ sung mã. Mức chắc chắn: **trung bình**. Bằng chứng định lượng trực tiếp "free-text-only làm hỏng analytics" còn mỏng.

### Phát hiện có nguồn
- Sexton, Hodkiewicz, Brundage, "Categorization Errors for Data Entry in Maintenance Work-Orders" (PHM Society 2019): buộc kỹ thuật viên chọn từ danh mục định sẵn dễ sinh lỗi khi schema không khớp cách họ nghĩ hay mô tả vấn đề. Bài dùng Human Reliability Analysis để định lượng lỗi nhập liệu vào cơ sở dữ liệu có cấu trúc và đề xuất biện pháp giảm thiểu — [PHM Society](https://papers.phmsociety.org/index.php/phmconf/article/view/790) (bậc 1, qua search, 2019)
- Hodkiewicz & Ho 2016: các trường mã có cấu trúc (failure mode…) thường thiếu hoặc sai, và free text là nguồn để sửa — [Emerald](https://www.emerald.com/insight/content/doi/10.1108/JQME-04-2015-0013/full/html) (bậc 1, qua search, 2016)
- Y tế (525 bản ghi về thuốc lá): bác sĩ chuyển sang free text khi trường có cấu trúc không ghi được lượng, tần suất hay ngày bỏ thuốc; bổ sung free text vào trường có cấu trúc "substantially improve smoking status data" — [PMC4419995](https://pmc.ncbi.nlm.nih.gov/articles/PMC4419995) (bậc 1, qua search, không rõ ngày)
- Linder et al. (JAMIA): bác sĩ đọc chép (dictation) đạt điểm chất lượng kém hơn ở 3/15 chỉ số so với nhóm dùng template có cấu trúc hoặc gõ free text. Hai nhóm sau không khác nhau có ý nghĩa — [HealthExec tóm tắt JAMIA](https://healthexec.com/topics/healthcare-management/healthcare-economics/jamia-dictated-ehr-documentation-low-quality) (bậc 2, qua search)
- Trường rời rạc (discrete) hỗ trợ ra quyết định và nghiên cứu, còn free text khó trích nếu không có NLP/AI — [WMJ 2025, 124(3):236](https://wmjonline.org/wp-content/uploads/2025/124/3/236.pdf) (bậc 1, qua search, 2025)
- "Other, please explain" trong khảo sát: câu trả lời được mã hóa lại vào danh mục có sẵn hoặc tạo danh mục mới; trong 467 người, 15 câu "other" không khớp cả danh mục cũ lẫn mới — [PMC6050098 figure F2](https://pmc.ncbi.nlm.nih.gov/articles/PMC6050098/figure/F2) (bậc 1, qua search, không rõ ngày)
- ISO 14224 (bảo trì dầu khí) tách mỗi sự cố thành failure mode / cause / mechanism, tức là taxonomy nhiều trục thay vì một ô lý do — [Fabrico blog](https://www.fabrico.io/blog/iso-14224-failure-taxonomy-codes/) (bậc 3, vendor; cần đối chiếu với tiêu chuẩn gốc)
- Uber COTA dùng cả lựa chọn menu của khách (cấu trúc) lẫn văn bản; văn bản là feature quan trọng nhất — [Uber blog](https://www.uber.com/gb/en/blog/cota/) (bậc 1, qua search, 2018)
- NORC: quy trình ba bước dựng code frame cho câu trả lời mở: phân tích tần suất từ có phần mềm hỗ trợ, chuyên gia review, rồi phân tích tâm trắc — [ASA JSM Proceedings 2014](https://ww2.amstat.org/meetings/proceedings/2014/data/assets/pdf/311294_87259.pdf) (bậc 1, qua search, 2014)

### Nhận định
- Vòng retro-fit đề xuất: (1) khai phá cụm trên lịch sử free text → taxonomy 2 cấp; (2) người duyệt, đặt tên theo ngôn ngữ người nhập (Intercom gọi là "topic curation"); (3) dùng cấp thô làm picklist bắt buộc, cấp mịn làm gợi ý autocomplete; (4) giữ ô ghi chú tự do và một mã "khác"; (5) đo tỷ lệ "khác" và độ khớp giữa mã chọn và nội dung ghi chú (mẫu kiểm tra), chạy lại khai phá trên phần "khác" mỗi kỳ.
- Phần do máy sinh theo mẫu (vd "đã khóa tài khoản X") nên được ghi mã sự kiện ngay tại nguồn (event type + tham số ở cột riêng). Cách này rẻ hơn nhiều so với parse ngược. Đây là suy luận, chưa có nguồn đo.
- Picklist dài và không khớp nghiệp vụ sinh ra lỗi chọn mã hệ thống, lỗi này còn khó phát hiện hơn free text. Vì vậy vẫn cần kiểm tra mẫu định kỳ cả trên trường có cấu trúc.

### Khoảng trống
- Không tìm được nghiên cứu định lượng nào so sánh trực tiếp "chỉ free text" với "mã + free text" về chất lượng phân tích lý do (hủy đơn/đóng ticket).
- Chưa có nguồn bậc 1 về autocomplete/gợi ý mã giúp giảm lỗi chọn mã.
- Chưa lấy được tỷ lệ lỗi cụ thể từ bài Sexton et al. 2019.

## Truy vấn đã chạy
- Forman quantifying counts and costs via classification adjusted classify and count (standard)
- scikit-learn clustering performance evaluation adjusted rand index V-measure silhouette (standard)
- technical language processing maintenance work orders Brundage NIST (standard)
- Uber customer support ticket classification COTA engineering blog (standard)
- Schonlau semi-automated coding open-ended survey responses (standard)
- Airbnb customer support text classification engineering blog contact reasons (standard)
- QuaPy quantification library Moreo Esuli Sebastiani (standard)
- DBCV density-based clustering validation HDBSCAN limitations high-dimensional embeddings (standard)
- Anthropic Clio privacy-preserving insights evaluation accuracy synthetic data clustering (standard)
- "other (please specify)" open-ended survey closed-ended response categories data quality study (standard)
- clustering stability bootstrap Jaccard clusterboot Hennig von Luxburg (standard)
- engineering blog clustering support tickets topics embeddings taxonomy Intercom OR Zendesk OR Shopify OR Spotify (extended)
- Grab OR LinkedIn OR Dropbox engineering blog classify customer feedback free text LLM taxonomy (extended)
- "Discovering and Classifying In-app Message Intent at Airbnb" (standard)
- Sexton Brundage Nestor hybrid datafication maintenance logs tagging (standard)
- maintenance work order failure codes free text data quality "other" code misuse study (standard)
- Brundage "technical language processing" unlocking maintenance knowledge 2021 Manufacturing Letters (standard)
- Esuli Moreo Sebastiani "Learning to Quantify" book Springer 2023 open access (standard)
- TnT-LLM text mining at scale evaluation human annotators agreement Cohen kappa taxonomy (standard)
- simultaneous confidence intervals multinomial proportions Sison Glaz Goodman Wilson score small counts (standard)
- Krippendorff alpha coding open-ended responses intercoder reliability threshold 0.8 0.667 (standard)
- classify and count bias prevalence shift quantification why classification accuracy not enough Sebastiani (standard)
- Zendesk intelligent triage intent taxonomy predicted intent confidence documentation (standard)
- structured data entry versus free text EHR documentation comparison completeness study coded fields (standard)
- Intercom topics explorer AI automatically groups conversations topics documentation (standard)
- sample size to estimate classifier accuracy confidence interval margin of error labeled validation set annotation (standard)
- Label Studio active learning ML backend uncertainty sampling documentation (standard)
- open-ended survey responses code frame development coding manual iterative "code frame" methodology (standard)
- "LLM-based Models for Detecting Emerging Topics in Service Feedback" (standard)
- chi-square test expected cell count at least 5 rule contingency table sparse categories Fisher exact collapse categories (standard)
- Hodkiewicz Ho 2016 cleaning historical maintenance work order data reliability analysis free text (standard)
- Sexton Hodkiewicz Brundage 2019 categorization errors data entry maintenance work orders PHM (standard)
