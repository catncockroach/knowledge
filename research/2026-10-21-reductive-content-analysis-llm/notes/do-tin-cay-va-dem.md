# Độ tin cậy, tính hợp lệ và quy tắc đếm

> **Ghi chú truy cập (quan trọng cho writer):** Trong phiên này `WebFetch` lỗi DNS với mọi host và proxy chặn `curl` tới SSOAR, SAGE, PMC, Wiley, qualitative-research.net, ResearchGate, archive.org, upenn.edu, matthewlombard.com, atlasti.com, CRAN, Wikipedia. Chỉ `raw.githubusercontent.com` mở được. Vì vậy **gần như mọi phát hiện dưới đây đọc từ trích đoạn của WebSearch** (ghi "qua search"), chưa mở toàn văn. Câu trong ngoặc kép là trích đoạn search hiển thị lại từ trang nguồn, chưa đối chiếu số trang. Hai nguồn duy nhất đã mở trực tiếp: mã nguồn NLTK (`masi_distance`) và file DESCRIPTION của gói R `mvalpha`.
>
> **Phạm vi đã mở rộng theo coordinator:** bài toán thật là nhiều mô tả tự do về vấn đề/sự cố, tìm vấn đề được nhắc nhiều nhất/ít nhất, không có danh mục trước; ví dụ đức tính chỉ minh họa. Một văn bản có thể nêu nhiều vấn đề; n có thể lớn hơn 100.

## 1. Yêu cầu về độ tin cậy liên người mã hóa để con số tần suất có giá trị

### Kết luận ngắn
Truyền thống content analysis định lượng coi con số tần suất chỉ đáng tin khi một mẫu được hai người mã hóa **độc lập** và đạt hệ số đồng thuận có hiệu chỉnh cơ hội: Krippendorff đặt α ≥ 0,800 là tin được, 0,667–0,800 chỉ cho kết luận tạm, dưới 0,667 thì bỏ; Lombard và cộng sự cấm dùng phần trăm đồng thuận đơn lẻ. Mức chắc chắn: **trung bình–cao**: các ngưỡng được nhiều nguồn độc lập dẫn lại nhất quán (kể cả Carletta 1996 dẫn Krippendorff 1980), nhưng chưa đọc được nguyên văn trang sách.

### Phát hiện có nguồn
- Ngưỡng Krippendorff: "rely on data when the alpha is greater than 0.8, discard data when the alpha is smaller than 0.667, and only draw tentative conclusions when the alpha is in-between"; một nguồn ghi trang: "Krippendorff (2004) suggests ≥.800 is ideal with ≥.667 being the lowest acceptable point (p.241)" (qua search, chưa xác nhận số trang) — [Krippendorff 2004, Reliability in Content Analysis: Some Common Misconceptions and Recommendations](https://www.researchgate.net/publication/275371833_Reliability_in_Content_Analysis_Some_Common_Misconceptions_and_Recommendations) (bậc 1, 2004; qua search)
- Nguồn gốc sớm hơn: Carletta (1996) dẫn Krippendorff (1980) rằng giới content analysis coi "K > .8 as good reliability, with .67 < K < .8 allowing tentative conclusions to be drawn" — [Carletta 1996, Assessing agreement on classification tasks: the kappa statistic](https://arxiv.org/pdf/cmp-lg/9602004) (bậc 1, 1996; qua search)
- Ngưỡng là quy ước chứ không phải đại lượng suy ra; một số nhà phương pháp chấp nhận .667 với mã hóa diễn giải phức tạp — [CASRAI: Krippendorff's alpha](https://casrai.org/guides/krippendorffs-alpha) (bậc 2, không rõ ngày; qua search)
- Krippendorff (2004): phần trăm đồng thuận "is a meaningless measure of reliability"; một chỉ số đồng thuận chỉ cho phép suy ra độ tin cậy nếu (a) áp lên "proper reliability data involving independent coding" và (b) coi các đơn vị là mô tả được riêng rẽ; bài đề xuất ba điều kiện cho chỉ số độ tin cậy và xét bảy chỉ số — [Krippendorff 2004 (bản PDF đại học Washington)](http://faculty.washington.edu/jwilker/559/Krippendorf.pdf) (bậc 1, 2004; qua search, ba điều kiện chưa đọc được)
- Hayes & Krippendorff (2007) đề xuất α làm thước đo chuẩn, dùng được "regardless of the number of observers, levels of measurement, sample sizes, and presence or absence of missing data" — [Answering the Call for a Standard Reliability Measure for Coding Data](https://www.asc.upenn.edu/sites/default/files/2021-03/Answering%20the%20Call%20for%20a%20Standard%20Reliability%20Measure%20for%20Coding%20Data.pdf) (bậc 1, 2007; qua search)
- Lombard, Snyder-Duch & Bracken (2002): không nên dựa riêng vào phần trăm đồng thuận; "If percent agreement is selected (and this is not recommended), use a second index that accounts for agreement expected by chance"; phản đối chỉ số dựa trên tương quan vì độ tin cậy cần "intercoder agreement rather than covariation"; phải báo cáo độ tin cậy "in a careful, clear, and detailed manner" — [Lombard et al. 2002, HCR 28(4):587–604 (bản CSU)](https://engagedscholarship.csuohio.edu/cgi/viewcontent.cgi?article=1049&context=clcom_facpub) (bậc 1, 2002; qua search)
- Lombard et al. 2002 được dẫn cho mức sàn ≥ .70 (Cohen's κ); "consensus in literature regarding reliability standards is lacking" — [TU Delft repository (luận văn dẫn Lombard)](https://repository.tudelft.nl/file/File_88f07a4b-1581-4d3c-8f4f-e7f77558e674) (bậc 2, không rõ ngày; qua search). Chưa xác nhận được bậc .90/.80/.70 nguyên văn.
- Mayring: trong dự án định tính với thành viên nhóm được huấn luyện, "Cohen's kappa over .7 would be sufficient" — [Mayring, Qualitative Content Analysis (bản d-nb.info)](https://d-nb.info/1248197224/34) (bậc 1, không xác định được năm ấn bản từ snippet, có thể là sách SAGE 2022; qua search)
- So sánh trường phái: Mayring "particularly emphasizes the use of quantitative intercoder reliability as a quality criterion"; Kuckartz hoài nghi hơn, dành cả chương để chỉ ra việc tính hệ số này cho dữ liệu định tính "problematic and demanding" — [audiotranskription.de: Mayring or Kuckartz?](https://www.audiotranskription.de/en/qualitative-content-analysis-according-to-mayring-or-kuckartz/) (bậc 2, không rõ ngày; qua search)
- O'Connor & Joffe (2020): ICR "somewhat controversial" trong giới định tính, một số cho là không phù hợp; lợi ích: tăng tính hệ thống, khả năng truyền đạt, minh bạch, xây lòng tin với nhiều đối tượng đọc — [O'Connor & Joffe 2020, IJQM 19](https://journals.sagepub.com/doi/10.1177/1609406919899220) (bậc 1, 2020; qua search)
- Độ ổn định (intracoder): Krippendorff phân biệt stability (cùng người mã hóa lại cùng nội dung ở thời điểm khác cho cùng kết quả), reproducibility (người khác mã hóa cho cùng kết quả) và accuracy — [Scientific Inquiry in Social Work 14.5 (dẫn Krippendorff 2009)](https://pressbooks.pub/scientificinquiryinsocialwork/chapter/14-5-reliability-in-unobtrusive-research) (bậc 2, không rõ ngày; qua search)

### Nhận định
- **Nhận định:** Với bài toán dùng LLM, "người mã hóa thứ hai" có thể là người hoặc một lần chạy LLM khác; chạy lại cùng LLM trên cùng dữ liệu tương ứng với *stability* (intracoder), không thay được *reproducibility* giữa người mã hóa độc lập. Đây là suy luận ánh xạ khái niệm, không có nguồn phương pháp luận kinh điển nói thẳng.
- **Nhận định:** Kuckartz và một phần giới định tính không coi ICR là bắt buộc; nhưng khi mục tiêu là *con số tần suất để xếp hạng*, lập luận của Krippendorff/Lombard áp dụng trực tiếp vì con số phải tái lập được.

### Khoảng trống
- Chưa đọc nguyên văn ba điều kiện của Krippendorff 2004, các bậc ngưỡng nguyên văn của Lombard 2002, và câu nào nói stability là dạng yếu nhất (search không xác nhận).
- Năm ấn bản của trích dẫn Mayring "kappa over .7" chưa rõ.

## 2. Bao nhiêu dữ liệu phải mã hóa kép

### Kết luận ngắn
Quy tắc ngón tay cái phổ biến: mẫu kiểm độ tin cậy ≥ 50 đơn vị hoặc ≥ 10% mẫu, hiếm khi cần quá 300 (Neuendorf, qua Lombard); O'Connor & Joffe nói 10–25% là "typical"; Krippendorff tính cỡ mẫu theo xác suất của phạm trù hiếm nhất, nên phạm trù càng hiếm càng cần nhiều. Mức chắc chắn: **trung bình**: các con số đến từ trích đoạn và nguồn thứ cấp, và cách hiểu "hoặc/và" trong quy tắc Neuendorf chưa kiểm được.

### Phát hiện có nguồn
- Lombard et al. tóm tắt Neuendorf (2002): "it should not be less than 50 units or 10% of the full sample, and it rarely will need to be greater than 300 units"; cần lớn hơn khi mẫu đầy đủ lớn hoặc độ tin cậy dự kiến thấp; mẫu phải chọn "using a random or other justifiable procedure" — [Lombard: Intercoder Reliability (bản in)](https://matthewlombard.com/reliability/index_print.html) (bậc 1, không rõ ngày; qua search)
- Một chương Springer: không có đồng thuận về cỡ mẫu, thông lệ là 10% tổng mẫu, "no fewer than 50 items and no more than 300 items" (dẫn Krippendorff 2018, Neuendorf 2002) — [Methodology and Research Design (Springer)](https://link.springer.com/chapter/10.1007/978-3-658-52394-7_8) (bậc 2, không rõ ngày; qua search)
- O'Connor & Joffe (2020): "little consensus regarding the proportion of the data set needed"; "10–25% of data units would be typical", tùy cỡ bộ dữ liệu; chọn ngẫu nhiên hoặc theo tiêu chí bảo vệ được (vd phân tầng) "to ensure representativeness of the entire data set"; nên "first double-code a small amount of data" để bắt lỗi codebook dễ sửa — [O'Connor & Joffe 2020](https://www.researchgate.net/publication/338742863_Intercoder_Reliability_in_Qualitative_Research_Debates_and_Practical_Guidelines) (bậc 1, 2020; qua search)
- Krippendorff (2019) dùng công thức Bloch & Kraemer (1989) lập bảng cỡ mẫu theo α tối thiểu (.667/.800/.900), mức ý nghĩa và xác suất của từng mã; ví dụ: 4 mã phân bố đều (p_c = 0,25), α_min = .800 ở mức .05 cần 139 lượt mã hóa; α_min = .667 cần 81 (lượt mã hóa, không phải đơn vị) — [ATLAS.ti 9 Mac Manual: Sample Size and Decision Rules](https://doc.atlasti.com/ManualMac.v9/ICA/ICASampleSizeAndDecisionRules.html) (bậc 1 cho tài liệu phần mềm, thứ cấp với Krippendorff; qua search)
- Quan điểm ngược: α là phép đo chứ không phải kiểm định nên không có cỡ mẫu tối thiểu; thay vào đó chọn độ rộng khoảng tin cậy tối đa rồi suy ra cỡ mẫu — [Real Statistics: Krippendorff's Alpha](https://real-statistics.com/reliability/interrater-reliability/krippendorffs-alpha/krippendorffs-alpha-basic-concepts/) (bậc 2, không rõ ngày; qua search)
- Phân phối lệch kéo α/κ xuống, có thể âm dù đồng thuận > 98%; mỗi phạm trù cần đủ cặp giá trị nên phạm trù hiếm cần mẫu lớn hơn — [Appen: Krippendorff's alpha](https://www.appen.com/blog/krippendorffs-alpha) (bậc 3, chỉ làm manh mối); với α, "bootstrapping offers the only suitable approach" để có khoảng tin cậy vì phân phối của α không biết — [Zapf et al. 2016, Measuring inter-rater reliability for nominal data](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4974794/) (bậc 1, 2016; qua search)
- Bài về LLM-judge khuyên báo cáo đồng thuận thô cạnh α vì α và κ "may be deflated by prevalence effects" — [arXiv 2605.31381, LLM Judges Inconsistently Disagree…](https://arxiv.org/pdf/2605.31381) (bậc 1, 2026; qua search)

### Nhận định
- **Nhận định:** Với n ≈ 100, quy tắc "≥ 50 đơn vị hoặc 10%" nghĩa là phải mã hóa kép ít nhất một nửa bộ (10% chỉ là 10 đơn vị, dưới mức sàn 50). Mã hóa kép toàn bộ 100 là hợp lý khi bên mã hóa thứ hai là LLM chi phí thấp.
- **Nhận định:** Bài toán xếp hạng "ít nhất" đụng đúng chỗ yếu của α: phạm trù hiếm (1–3 lần/100) gần như không đủ dữ liệu để ước lượng độ tin cậy riêng cho nó. Kết luận về đáy bảng xếp hạng luôn kém chắc hơn đỉnh.

### Khoảng trống
- Chưa xem được bảng Krippendorff nguyên bản (sách 2019, chương 12) để tra cỡ mẫu cho trường hợp p_c nhỏ (vd 0,02–0,05).
- Không tìm được nguồn phương pháp luận nói riêng về cỡ mẫu kiểm độ tin cậy cho mã hóa đa nhãn.

## 3. Đơn vị đếm: số văn bản có nhắc phạm trù hay số lần nhắc

### Kết luận ngắn
Krippendorff tách sampling unit, recording/coding unit và context unit; Sandelowski coi "đếm cái gì và đếm thế nào" là phán đoán trung tâm, không hiển nhiên. Không tìm được quy tắc kinh điển bắt buộc chọn "đơn vị có nhắc" hay "số lần nhắc"; nguồn chỉ yêu cầu khai báo rõ thứ được đếm và mẫu số. Mức chắc chắn: **trung bình** về nguyên tắc khai báo, **thấp** về việc có quy tắc chọn cụ thể.

### Phát hiện có nguồn
- Krippendorff, *Content Analysis* (4th ed.), chương 5 "Unitizing": 5.2.1 Sampling Units, 5.2.2 Recording/Coding Units, 5.2.3 Context Units; cách định nghĩa đơn vị: physical, syntactical, categorial, propositional, thematic; chương 10.1 bàn về counts — [Mục lục sách (obalkyknih.cz)](https://obalkyknih.cz/file/toc/434034/pdf) (bậc 1, mục lục; qua search)
- Định nghĩa context unit trong glossary Krippendorff: "textual matter defined to limit what observers or readers consider when categorizing or describing recording/coding units. If allowed to be too large, coding tends to become unreliable. If defined too small or not at all, recording units may lose the information that stems from the textual environment" — [SAGE Research Methods, Content Analysis 4e back matter](https://methods.sagepub.com/book/mono/embed/content-analysis-4e/back-matter/i2137) (bậc 1, 2019; qua search)
- Sandelowski, Voils & Knafl (2009): quantitizing là "the numerical translation, transformation, or conversion of qualitative data" (tr. 208); "Among the judgments are deciding what and how to count"; một giả định họ phê phán là "counting is an unambiguous process" — [On Quantitizing, JMMR 3(3):208–222](https://journals.sagepub.com/doi/10.1177/1558689809334210) (bậc 1, 2009; qua search; toàn văn ở [UNC repository](https://cdr.lib.unc.edu/downloads/8k71nq82d) chưa mở được)
- Maxwell (trả lời trên diễn đàn, bậc 3, chỉ làm manh mối): khi không xác định được đơn vị thì có thể đếm "mentions", "anytime a participant mentions something codable" — [ResearchGate Q&A](https://www.researchgate.net/post/Does-number-or-count-make-sense-in-qualitative-research) (bậc 3; qua search)
- MAXQDA (Kuckartz & Rädiker) đếm hai thứ khác nhau: số đoạn được gán mã ("how often a code is attached to text segments") và, khi chuyển mã thành biến, "for each case (person) the number of segments coded … is counted"; ma trận Kuckartz: hàng = case, cột = phạm trù — [Kuckartz, Realizing Mixed-Methods Approaches with MAXQDA](https://www.maxqda.com/download/MixMethMAXQDA-Nov01-2010.pdf) (bậc 1, 2010; qua search)
- Neuendorf (qua nguồn dẫn): phạm trù phải "exhaustive and mutually exclusive", thường cần thêm "other" và "unable to determine"; một đơn vị không được mã vào nhiều phạm trù, với "rare exceptions" — [Zhang & Wildemuth, Qualitative Analysis of Content](https://pages.ischool.utexas.edu/yanz/Content_analysis.pdf) và [ERIC Digest ED458218](https://files.eric.ed.gov/fulltext/ED458218.pdf) (bậc 2; qua search, chưa rõ câu nào thuộc nguồn nào)
- Ngược lại, content analysis định tính "allows you to assign a unit of text to more than one category simultaneously" — [Zhang & Wildemuth](https://pages.ischool.utexas.edu/yanz/Content_analysis.pdf) (bậc 2, không rõ ngày; qua search)

### Nhận định
- **Nhận định:** Với mô tả vấn đề tự do (mỗi văn bản là một báo cáo/ý kiến độc lập), "số văn bản có nhắc tới vấn đề X" (đếm theo case, tối đa 1 lần/văn bản) trả lời câu "vấn đề nào phổ biến nhất", còn "số lần nhắc" bị thổi phồng bởi văn bản dài hoặc lặp ý. Đây là suy luận từ cách Kuckartz tách case và segment, cùng cảnh báo "overcounting" của Sandelowski (mục 6), không phải một quy tắc có nguồn nói thẳng.
- **Nhận định:** Nếu đếm theo văn bản và cho đa nhãn thì tổng tần suất > n; khi báo cáo phải nêu mẫu số là số văn bản và nói rõ các tỉ lệ không cộng thành 100%.

### Khoảng trống
- Chưa đọc được chương 10.1 (counts) của Krippendorff và phần Neuendorf về "unit of data collection" và "unit of analysis"; không có trích nguyên văn về quy tắc chọn đơn vị đếm.
- Không tìm được nguồn gốc nói rõ "rare exceptions" của Neuendorf với nguyên tắc loại trừ nhau là gì.

## 4. Phạm trù loại trừ nhau hay đa nhãn, và đo độ tin cậy cho mã hóa đa trị

### Kết luận ngắn
Content analysis định lượng truyền thống đòi phạm trù loại trừ nhau và bao quát hết (Neuendorf); content analysis định tính cho phép đa nhãn. Với đa nhãn có hai công cụ đo độ tin cậy có nguồn: mvα của Krippendorff & Craggs (2016) và α kết hợp khoảng cách MASI (Passonneau 2006). Mức chắc chắn: **cao** về sự tồn tại và định nghĩa công cụ (đã mở mã nguồn), **thấp** về ngưỡng chấp nhận riêng cho chúng (không tìm thấy).

### Phát hiện có nguồn
- Krippendorff & Craggs (2016), "The Reliability of Multi-Valued Coding of Data", *Communication Methods and Measures* 10(4):181–198: đề xuất hệ số cho dữ liệu mà một người mã hóa có thể gán nhiều giá trị cho một đơn vị; trước đó chưa có cách thực dụng để đo — [Academia.edu record](https://www.academia.edu/83842160/The_Reliability_of_Multi_Valued_Coding_of_Data) (bậc 1, 2016; qua search)
- Gói R `mvalpha` 0.6.3 (đã mở DESCRIPTION): "Calculate Krippendorff's alpha for multi-valued data using the methods introduced by Krippendorff and Craggs (2016) <doi:10.1080/19312458.2016.1228863>. Nominal, ordinal, interval, and ratio data types are supported, with option to create bootstrapped estimates of alpha." — [cran/mvalpha DESCRIPTION](https://raw.githubusercontent.com/cran/mvalpha/master/DESCRIPTION) (bậc 1, đã mở, 2026-10-21)
- MASI (Passonneau, LREC 2006): khoảng cách giữa hai tập nhãn; mã NLTK (đã mở): hệ số đơn điệu m = 1 nếu hai tập bằng nhau, 2/3 nếu một tập là tập con của tập kia, 1/3 nếu giao nhau một phần, 0 nếu rời nhau; `masi_distance = 1 - |A∩B|/|A∪B| * m`; docstring: "Distance metric that takes into account partial agreement when multiple labels are assigned", ví dụ `masi_distance({1,2},{1,2,3,4}) = 0.6667` — [nltk/metrics/distance.py](https://raw.githubusercontent.com/nltk/nltk/develop/nltk/metrics/distance.py) (bậc 1, đã mở, 2026-10-21); bài gốc: [Passonneau 2006, ACL Anthology L06-1392](https://aclanthology.org/L06-1392/) (bậc 1, 2006; chưa mở)
- `nltk.metrics.agreement.AnnotationTask` tính Alpha (Krippendorff 1980) với tham số khoảng cách tùy chọn (mặc định `binary_distance`), triển khai theo khảo sát của Artstein & Poesio — [nltk/metrics/agreement.py](https://raw.githubusercontent.com/nltk/nltk/develop/nltk/metrics/agreement.py) (bậc 1, đã mở)
- Ví dụ áp dụng: α với δ_MASI(v,v') = 1 − MASI(v,v') cho nhãn tập hợp — [THAI-SER corpus, arXiv 2507.09618](https://arxiv.org/pdf/2507.09618) (bậc 1, 2025; qua search)
- Lombard et al. (2002), qua nguồn khác: thử độ tin cậy không chính thức trên một số ít đơn vị "ideally are not part of the full sample", rồi chính thức ở pilot — [Lombard et al. 2002 (ResearchGate)](https://www.researchgate.net/publication/227605219_Content_Analysis_in_Mass_Communication_Assessment_and_Reporting_of_Intercoder_Reliability) (bậc 1, 2002; qua search)

### Nhận định
- **Nhận định:** Có hai cách đo độ tin cậy cho đa nhãn, mỗi cách trả lời một câu hỏi khác nhau: (a) mvα hoặc α+MASI cho cả tập nhãn mỗi đơn vị, cho một con số tổng; (b) tách mỗi phạm trù thành một biến nhị phân có/không và tính α cho từng phạm trù. Cách (b) cho biết phạm trù nào không đáng tin, điều cần cho bảng xếp hạng; nhưng không tìm được nguồn kinh điển mô tả cách (b) cho bài toán này (search Neuendorf về present/absent không ra).
- **Nhận định:** Ngưỡng .800/.667 được nêu cho α nói chung; không tìm thấy nguồn nói ngưỡng đó áp dụng y nguyên cho mvα hay α+MASI.

### Khoảng trống
- Không đọc được toàn văn Krippendorff & Craggs 2016 (công thức, ngưỡng, ví dụ).
- Không tìm được nguồn phương pháp luận cho cách mã hóa có/không theo từng phạm trù (truy vấn: "Neuendorf … dichotomous present absent variables").

## 5. Khi phạm trù được rút quy nạp: kiểm độ tin cậy ở bước nào

### Kết luận ngắn
Các nguồn thống nhất về trình tự: rút và sửa phạm trù trên một phần dữ liệu (Mayring: sau 10–50% tài liệu, gọi là kiểm tra độ tin cậy *formative*), chốt hệ thống phạm trù/coding frame, rồi kiểm độ tin cậy trên lượt mã hóa cuối hoặc trên dữ liệu mới (*summative*; Schreier: pilot/trial coding → đánh giá và sửa → main coding; Lombard: thử trên đơn vị ngoài mẫu chính). Mayring lưu ý rằng ở bước quy nạp, sự đồng thuận được xét "thủ công" theo độ tương đồng nghĩa chứ không bằng κ. Mức chắc chắn: **trung bình**: trình tự nhất quán qua nhiều nguồn, nhưng thuật ngữ "formative/summative" của Mayring chỉ thấy qua nguồn thứ cấp tiếng Đức.

### Phát hiện có nguồn
- Mayring (2000, FQS): "within a feedback loop those categories are revised, eventually reduced to main categories and checked in respect to their reliability"; phạm trù được "tentatively and step by step deduced from the material" — [Mayring 2000, Qualitative Content Analysis, FQS 1(2)](https://www.qualitative-research.net/index.php/fqs/article/download/1089/2385?inline=1) (bậc 1, 2000; qua search) và [bản PDF khác](https://www.miguelangelmartinez.net/IMG/pdf/2000_mayring_content_analysis.pdf)
- Mô hình bước của Mayring: định câu hỏi, tiêu chí chọn lọc và mức trừu tượng → duyệt tài liệu, gộp vào phạm trù cũ hoặc lập phạm trù mới → "Revision der Kategorien nach etwa 10 bis 50% des Materials" → duyệt lại toàn bộ lần cuối — [Skript Uni Oldenburg "4 Kategorienbildung" (tác giả không rõ từ snippet)](https://wp.uni-oldenburg.de/wp-content/uploads/sites/10996/2024/03/Qualitative_Inhaltsanalyse._Methoden_Praxis_Computeruntersttzung_4._Kategorienbildung.pdf) (bậc 2, 2024, dẫn Mayring 2015; qua search)
- Bước sửa sau 10–50% được gọi là "Formative Reliabilitätsprüfung (Revision)" — [DGRW Summerschool 2023, Qualitative Inhaltsanalyse](https://www.dgrw-online.de/wp-content/uploads/DGRW-Qualitative-Inhaltsanalyse_2023_FV.pdf) (bậc 2, 2023; qua search). Không tìm thấy cụm "formative check of reliability" trong bản tiếng Anh qua search.
- Directed content analysis (Assarroudi et al.) liệt kê "revision of the category and coding guideline after working through 10–50% of the data" là bước của Mayring (2000, 2014), và lưu ý Mayring không nói rõ mã sơ bộ được tạo quy nạp hay suy diễn — [PMC7932246](https://pmc.ncbi.nlm.nih.gov/articles/PMC7932246/) (bậc 1, 2018; qua search)
- Mayring (bài FQS về phân định và biến thể, có thể 2019): với ứng dụng phạm trù suy diễn, mong muốn đồng thuận cao, kiểm bằng xác suất đồng thuận hiệu chỉnh ngẫu nhiên (vd Cohen's κ); "In the case of inductive category developments, the agreement would be assessed 'manually' according to similarity, since the exact category formulations can vary linguistically" — [Mayring, Qualitative Content Analysis: Demarcation, Varieties, Developments (FQS)](https://www.qualitative-research.net/index.php/fqs/article/view/3343) (bậc 1, 2019; qua search, quy thuộc bài cụ thể chưa chắc)
- Mayring phản bác quan niệm "that Mayring's method ultimately analyzes frequencies instead of extracting information"; quy trình của ông có bước "establishment and comparison of frequencies … possibly further statistical processing" — [ScienceDirect Topics: Qualitative Content Analysis](https://www.sciencedirect.com/topics/social-sciences/qualitative-content-analysis) (bậc 2; qua search)
- Schreier (2012): các bước gồm lập coding frame, phân đoạn tài liệu, thử coding frame, đánh giá lượt mã hóa thử, rồi main coding; "The trial coding is at the core of the pilot phase which we will describe in Chapter 8"; bước 6 "Evaluating and modifying your coding frame" (đánh giá theo tính nhất quán và tính hợp lệ) — [Schreier 2012, chương 1 (SAGE)](https://uk.sagepub.com/sites/default/files/upm-binaries/46241_Schreier.pdf) (bậc 1, 2012; qua search) và [Internet Archive record](https://archive.org/details/qualitativeconte0000schr). Một nghiên cứu theo Schreier thêm 6 tiểu phạm trù từ dữ liệu sau pilot, mã lại các đoạn pilot cần mã mới, rồi lặp lại so sánh mã hóa thử trên phần còn lại (qua search, nguồn ứng dụng chưa xác định URL riêng).
- Lombard et al. 2002: thử độ tin cậy không chính thức trên vài đơn vị "ideally are not part of the full sample", sau đó chính thức trong pilot test, rồi trên mẫu kiểm độ tin cậy ngẫu nhiên của mẫu đầy đủ — [ERIC EJ658925](https://eric.ed.gov/?id=EJ658925), [Lombard et al. 2002](https://www.researchgate.net/publication/227605219_Content_Analysis_in_Mass_Communication_Assessment_and_Reporting_of_Intercoder_Reliability) (bậc 1, 2002; qua search)
- Campbell, Quincy, Osserman & Pedersen (2013), dựng codebook quy nạp cho 101 phỏng vấn: PI xác định đơn vị có nghĩa bằng cách mã một bản ghi trong Atlas.ti; người mã đọc toàn bộ để tạo phạm trù rộng, cùng mã một bản ghi rồi hòa giải khác biệt; bỏ, gộp, sửa mã; cải thiện khả năng phân biệt của sơ đồ cho tới khi đạt mức chấp nhận được theo chỉ số tin cậy/đồng thuận — [Campbell et al. 2013, SMR 42(3):294–320 (PDF)](https://assets.super.so/6b4b5d92-904a-4e7b-95bd-914dd1d1528f/files/1974c860-4d69-496b-93bc-a67fca1d1e4b/Campbell_et_al_2013.pdf) (bậc 1, 2013; qua search)
- O'Connor & Joffe 2020: các quyết định thiết kế gồm "the unit of coding (i.e., sentences, paragraphs, conceptually mean[ingful units])", số người mã hóa, lượng dữ liệu mã kép; nên mã kép một lượng nhỏ trước để sửa codebook — [O'Connor & Joffe 2020](https://journals.sagepub.com/doi/pdf/10.1177/1609406919899220) (bậc 1, 2020; qua search)

### Nhận định
- **Nhận định:** Ghép các nguồn, trình tự có căn cứ cho bài toán là: (1) rút phạm trù quy nạp trên một phần dữ liệu và sửa (Mayring 10–50%; đồng thuận giữa hai lần rút phạm trù độc lập được so "thủ công" theo nghĩa); (2) chốt codebook với định nghĩa, ví dụ neo, quy tắc mã hóa; (3) mã hóa thử (Schreier) trên dữ liệu chưa dùng để dựng phạm trù (Lombard), tính α; sửa và lặp nếu < .667/.800; (4) mã hóa chính và kiểm độ tin cậy trên mẫu ngẫu nhiên. Nếu cùng phần dữ liệu vừa dùng để rút vừa dùng để kiểm phạm trù, α sẽ bị thổi phồng; đây là suy luận, không có nguồn nói thẳng.
- **Nhận định:** Với n ≈ 100, không có "dữ liệu mới" dồi dào: ví dụ rút phạm trù trên 30–50 văn bản, kiểm trên phần còn lại; với n lớn hơn thì dễ tách hơn. Cách chia này là suy luận áp dụng quy tắc 10–50% của Mayring, chưa có nguồn kiểm chứng cho n nhỏ.

### Khoảng trống
- Chưa đọc được nguyên văn Mayring 2014 (SSOAR) về "formative/summative check of reliability", intracoder check, và mô hình bước đầy đủ: SSOAR bị chặn.
- Chưa đọc được Schreier chương 8–9 (cách tính đồng thuận trong pilot, tiêu chí sửa).
- Không có nguồn nói tỷ lệ chia tách dữ liệu rút phạm trù / dữ liệu kiểm cho n nhỏ.

## 6. Summative content analysis và quantitizing: cách đối xử với con số và các cảnh báo

### Kết luận ngắn
Hsieh & Shannon coi đếm trong summative content analysis là để "khám phá cách dùng" chứ không suy ra nghĩa, và phải đi tiếp tới diễn giải ngữ cảnh; Sandelowski cảnh báo đếm là một chuỗi phán đoán, và nêu bốn lỗi: verbal counting, overcounting, misleading counting, acontextual counting. Mức chắc chắn: **trung bình–cao** (định nghĩa và danh sách lỗi có trong abstract, nhiều nguồn trùng), **thấp** về định nghĩa chi tiết từng lỗi (chưa đọc thân bài).

### Phát hiện có nguồn
- Hsieh & Shannon (2005): ba cách tiếp cận khác nhau ở "coding schemes, origins of codes, and threats to trustworthiness"; "A summative content analysis involves counting and comparisons, usually of keywords or content, followed by the interpretation of the underlying context"; trong conventional, phạm trù "derived directly from the text data" — [Hsieh & Shannon 2005, QHR 15(9):1277–1288](https://studysites.sagepub.com/millsandbirks/study/Journal%20Articles/Qual%20Health%20Res-2005-Hsieh-1277-88.pdf) (bậc 1, 2005; qua search)
- Hsieh & Shannon: summative "goes beyond mere word counts to include latent content analysis"; đếm đơn thuần là manifest content analysis; "This quantification is an attempt not to infer meaning but, rather, to explore usage" — [Hsieh & Shannon 2005 (bản SAGE study)](https://study.sagepub.com/sites/default/files/Hsieh%20and%20Shannon%20-%20Three%20Approaches%20to%20Qualitative%20Content%20Analysis.pdf) (bậc 1, 2005; qua search)
- Hạn chế summative (nguồn thứ cấp): bị ràng buộc bởi từ khóa chọn ban đầu, ít chú ý nghĩa ngầm (ẩn dụ, so sánh) — [Delve: summative content analysis](https://delvetool.com/blog/what-is-qualitative-summative-content-analysis) (bậc 3, chỉ làm manh mối)
- Sandelowski (2001), "Real qualitative researchers do not count": hai huyền thoại là nhà nghiên cứu định tính "do not count and cannot count"; "qualitative researchers should avoid the counting pitfalls of verbal counting, overcounting, misleading counting, and acontextual counting" — [Research in Nursing & Health 24:230–240](https://onlinelibrary.wiley.com/doi/abs/10.1002/nur.1025) (bậc 1, 2001; qua search, abstract)
- Sandelowski, Voils & Knafl (2009): đếm đòi hỏi các phán đoán ("deciding what and how to count") và thỏa hiệp ("balancing numerical precision with narrative complexity"); phê phán giả định "counting is an unambiguous process"; ba lập trường về giá trị của quantitizing: "conditional complementarity", "critical remediation", "analytic alternation" — [On Quantitizing](https://journals.sagepub.com/doi/10.1177/1558689809334210) (bậc 1, 2009; qua search). Bài nhìn lại năm 2025 ghi bài gốc có hơn 1.000 trích dẫn — [Onwuegbuzie, On quantitizing revisited, Front. Psychol.](https://pmc.ncbi.nlm.nih.gov/articles/PMC11801310/) (bậc 1, 2025; qua search)
- Maxwell (2010): Becker và Hammersley ủng hộ "quasi-statistics", tức đếm đơn giản để làm chính xác các chữ "some", "usually", "most"; bài trình bày cả lợi ích và "potential problems created by such uses and how these can be dealt with" — [Maxwell 2010, Qualitative Inquiry](https://journals.sagepub.com/doi/pdf/10.1177/1077800410364740) (bậc 1, 2010; qua search, abstract)
- Hannah & Lautsch (2011): bàn bốn kiểu đếm và mục đích của chúng, trong nghiên cứu định tính nhằm xây lý thuyết mới; một số dữ liệu định tính không nên định lượng — [Hannah & Lautsch 2011, J. Management Inquiry 20(1):14–22](https://www.researchgate.net/publication/254117926_Counting_in_Qualitative_Research_Why_to_Conduct_it_When_to_Avoid_it_and_When_to_Closet_it) (bậc 1, 2011; qua search, abstract)

### Nhận định
- **Nhận định:** Bài toán đếm vấn đề nhiều/ít nhất nằm giữa conventional (phạm trù rút từ dữ liệu) và summative (đếm rồi diễn giải). Hsieh & Shannon mô tả summative bắt đầu từ từ khóa đã xác định, nên bài toán thuần quy nạp dùng conventional để tạo phạm trù rồi mới đếm; nguồn không mô tả sẵn tổ hợp này dưới một tên.
- **Nhận định:** "Overcounting" và "acontextual counting" của Sandelowski là lý do để đếm theo văn bản (case) thay vì theo lần nhắc, và để kèm trích dẫn minh họa cạnh mỗi con số; định nghĩa chi tiết của hai lỗi này chưa đọc được nên đây là suy luận từ tên gọi.

### Khoảng trống
- Chưa đọc thân bài Sandelowski 2001/2009 để có định nghĩa và ví dụ của từng lỗi đếm.
- Chưa đọc nguyên văn phần "trustworthiness" của Hsieh & Shannon cho summative.

## 7. Báo cáo tần suất với n nhỏ (≈100) và n lớn hơn: xếp hạng, đồng hạng, độ bất định

### Kết luận ngắn
Văn liệu phương pháp content analysis đã tìm **không** đưa quy tắc cụ thể cho việc báo cáo "nhiều nhất/ít nhất", đồng hạng hay độ bất định của thứ hạng; đây là khoảng trống. Thống kê học có công cụ: khoảng tin cậy đồng thời cho tỉ lệ đa thức (Goodman 1965, Sison–Glaz 1995) và suy luận về thứ hạng từ dữ liệu đa thức với kích thước mẫu 10–100. Mức chắc chắn: **trung bình** về sự tồn tại công cụ, **thấp** về việc chúng là chuẩn trong content analysis.

### Phát hiện có nguồn
- statsmodels `multinomial_proportions_confint`: phương pháp Goodman "valid if all values in counts are greater or equal to 5"; Sison-Glaz "less conservative than goodman, but only valid if counts has 7 or more categories" — [statsmodels docs](https://www.statsmodels.org/dev/generated/statsmodels.stats.proportion.multinomial_proportions_confint.html) (bậc 1, không rõ ngày; qua search)
- R DescTools `MultinomCI` triển khai Sison-Glaz, Goodman, Wilson, Fitzpatrick-Scott… — [DescTools MultinomCI](https://search.r-project.org/CRAN/refmans/DescTools/html/MultinomCI.html) (bậc 1; qua search)
- Suy luận về thứ hạng từ dữ liệu đa thức (áp dụng xếp hạng đảng phái): các tập tin cậy bootstrap có "coverage frequencies may be far below the desired level, especially for small sample sizes and/or small success probabilities"; mô phỏng với cỡ mẫu 10–100 — [arXiv 2402.00192, Finite- and Large-Sample Inference for Ranks using Multinomial Data](https://arxiv.org/pdf/2402.00192) (bậc 1, 2024; qua search)
- Với α, khoảng tin cậy nên lấy bằng bootstrap — [Zapf et al. 2016](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4974794/) (bậc 1, 2016; qua search); `mvalpha` có tùy chọn bootstrap cho α đa trị (đã mở, xem mục 4)
- Maxwell (2010), qua nguồn thứ cấp: đếm làm rõ báo cáo định tính khi đối tượng được đếm và mẫu số được nêu rõ — [ERIC EJ886130](https://eric.ed.gov/?id=EJ886130) (bậc 2 cho câu này; qua search)

### Nhận định
- **Nhận định:** Với n = 100, mỗi văn bản là 1 điểm phần trăm; chênh lệch vài văn bản giữa hai phạm trù gần đỉnh hoặc gần đáy thường nằm trong khoảng bất định, nên báo cáo nên dùng nhóm hạng (vd "nhóm phổ biến nhất" gồm các phạm trù có khoảng tin cậy chồng nhau) thay vì một hạng 1 duy nhất, và đồng hạng là tình huống bình thường ở đáy (nhiều phạm trù chỉ 1–2 lần). Đây là suy luận thống kê, không có nguồn content-analysis nói thẳng.
- **Nhận định:** "Ít nhất" phụ thuộc mạnh vào mức trừu tượng khi gộp phạm trù (một phạm trù hiếm có thể biến mất khi gộp lên cấp cao hơn) và vào độ tin cậy riêng của phạm trù hiếm (mục 2). Nên báo cáo kèm: định nghĩa phạm trù, mẫu số, đơn vị đếm (văn bản hay lần nhắc), α theo phạm trù hoặc ghi chú "không đủ dữ liệu để ước lượng", và ví dụ trích dẫn.
- **Nhận định:** Với n lớn hơn (hàng nghìn), khoảng tin cậy hẹp đi nên thứ hạng ở đỉnh ổn định hơn; nút thắt chuyển sang độ tin cậy của phân loại (mẫu kiểm 50–300 đơn vị theo Neuendorf) và độ ổn định của tập phạm trù quy nạp. Công thức Goodman cần mọi ô ≥ 5, nên với phạm trù đuôi dài vẫn phải dùng phương pháp khác hoặc báo cáo dạng "≤ k lần".

### Khoảng trống
- Không tìm được hướng dẫn trong Krippendorff, Neuendorf, Mayring, Schreier hay Hsieh & Shannon về báo cáo thứ hạng, đồng hạng hay khoảng tin cậy cho tần suất phạm trù (chưa đọc được chương 10 của Krippendorff về counts).
- Chưa kiểm phương pháp của arXiv 2402.00192 ngoài abstract.

## Truy vấn đã chạy
- Mayring 2014 qualitative content analysis theoretical foundation basic procedures ssoar pdf (standard)
- Sandelowski Voils Knafl 2009 "On quantitizing" PMC (standard)
- O'Connor Joffe 2020 intercoder reliability qualitative research debates practical guidelines (standard)
- Krippendorff "reliability of multi-valued coding of data" (standard)
- Mayring inductive category formation "formative check of reliability" "10-50%" material revision (extended)
- Krippendorff "α ≥ .800" "α ≥ .667" tentative conclusions reliability content analysis (extended)
- Lombard Snyder-Duch Bracken 2002 intercoder reliability content analysis recommendations 10% subsample 50 units minimum (extended)
- Hsieh Shannon 2005 summative content analysis counting keywords latent content "frequency" limitations (extended)
- Neuendorf Content Analysis Guidebook reliability subsample "10%" "no fewer than 50" "rarely more than 300" (extended)
- Krippendorff reliability sample size smallest category probability table minimum number of units alpha (extended)
- O'Connor Joffe 2020 "10–25%" data double-coded intercoder reliability segmentation units codebook (extended)
- Schreier 2012 qualitative content analysis in practice pilot phase "trial coding" segmentation coding frame modify (extended)
- Mayring 2014 "intracoder" "intercoder" reliability "kappa" qualitative content analysis "frequencies" categories quantitative steps (extended)
- Sandelowski Voils Knafl "On quantitizing" counting "judgment" cautions "numbers" qualitative data quote (extended)
- Passonneau 2006 MASI measuring agreement set-valued items annotation Krippendorff alpha (standard)
- Krippendorff rare categories reliability "variation" alpha cannot be established skewed distribution content analysis (extended)
- Krippendorff 2004 "Reliability in content analysis: some common misconceptions and recommendations" independent coders codebook conditions (extended)
- Campbell Quincy Osserman Pedersen 2013 coding in-depth semistructured interviews unitization intercoder reliability codebook development (extended)
- Hannah Lautsch 2011 "Counting in qualitative research: why to conduct it, when to avoid it" (extended)
- Maxwell 2010 "Using numbers in qualitative research" quasi-statistics counts cautions (extended)
- Sandelowski 2001 "Real qualitative researchers do not count" errors overcounting undercounting misleading (extended)
- Neuendorf content analysis multiple coding one unit several categories dichotomous present absent variables mutually exclusive exhaustive (extended)
- Hsieh Shannon 2005 summative approach "counting and comparisons" "trustworthiness" "credibility" keywords "latent" quote (standard)
- confidence intervals for ranks of proportions multinomial "uncertainty in ranking" categories small sample (extended)
- Lombard intercoder reliability "coefficients of .90 or greater" ".80 or greater" ".70" exploratory studies recommendations (standard)
- Kuckartz qualitative text analysis category frequencies number of cases versus number of coded segments "case" counting (extended)
- Krippendorff content analysis units "sampling units" "recording units" "context units" definition counting (standard)
- Mayring "induktive Kategorienbildung" "10 bis 50 %" Materials Revision Kategorien "Intercoderreliabilität" summative Reliabilitätsprüfung (extended)
- Mayring "feedback loop those categories are revised, eventually reduced to main categories and checked in respect to their reliability" (extended)
- Krippendorff three types of reliability stability reproducibility accuracy "test-retest" intraobserver weakest content analysis (standard)
- Mở trực tiếp (GitHub raw): cran/mvalpha DESCRIPTION; nltk/metrics/distance.py; nltk/metrics/agreement.py
