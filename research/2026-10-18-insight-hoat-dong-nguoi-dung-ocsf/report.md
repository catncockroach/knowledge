---
title: Pipeline sinh insight hoạt động người dùng từ telemetry Windows chuẩn OCSF, có dùng LLM
date: 2026-10-18
question: Kiến trúc/pipeline nào biến một batch hàng trăm nghìn event OCSF thành dòng thời gian theo ngày gồm các hoạt động mang tính "người", dùng LLM ở đâu, và giữ độ phức tạp O(n)–O(n log n) như thế nào?
tags: [ocsf, llm, telemetry, event-abstraction, sessionization, timeline]
---

# Code gom và đếm, LLM chỉ đặt tên và kể lại

> **Câu hỏi:** Kiến trúc nào biến hàng trăm nghìn event OCSF của một thiết bị/người dùng thành dòng thời gian hoạt động "người" theo ngày, LLM đặt ở đâu, và giữ chi phí O(n)–O(n log n) ra sao? · **Ngày:** 2026-10-18 · **Phạm vi:** telemetry endpoint Windows (Sysmon, Windows Security/ETW, EDR) đã chuẩn hóa OCSF, xử lý theo batch, nguồn LLM 2022–2026, thuật toán kinh điển; không lấy MITRE ATT&CK làm khung.
> · **Kiểm chứng:** 52 khẳng định đã đối chiếu nguồn, 11 đã sửa

## Tóm tắt

Kiến trúc nên dùng là một pipeline hai pha. Pha tất định gồm chiếu cột, sắp theo thời gian, dựng cây process, gom phiên theo entity rồi theo khoảng trống thời gian, băm chữ ký, đếm và phát hiện burst; nó chạy trong O(n log n) và nén hàng trăm nghìn event xuống vài trăm phân đoạn mỗi ngày. LLM chỉ xuất hiện ở hai chỗ chính: đặt nhãn "người" cho mỗi chữ ký phiên **mới** (có cache bền), và viết tường thuật **một lần mỗi ngày** từ bảng phân đoạn mà code đã đếm sẵn. Nhờ vậy số lời gọi tăng theo số chữ ký khác nhau cộng số ngày, không theo n. Cách chia vai này có bằng chứng mạnh từ ba phía: log parsing bằng LLM chỉ hiệu quả khi có cache theo template (LILAC trung bình khoảng **280 lời gọi cho mỗi dataset cỡ 3,6 triệu dòng** [1]), frontier model đạt **dưới 50%** ở các tác vụ gộp/đếm trên ngữ cảnh 128K [2], và hầu hết sản phẩm SIEM/XDR có tài liệu công khai đặt LLM *sau* bước gom. OCSF làm việc nén dễ hơn log text: `type_uid` đã là "template" sẵn, còn `process.uid` và logon session là khóa gom tự nhiên. Mức chắc chắn **cao** cho từng khối thuật toán và cho chỗ đặt LLM; **thấp** cho các con số cụ thể trên endpoint Windows, vì chưa có nghiên cứu hay dataset công khai nào làm đúng bài toán này, nên chủ repo sẽ phải tự dựng ground truth. Ba rủi ro lớn còn mở: "người hay máy" chỉ là suy luận xác suất, đa nhiệm xen kẽ làm phân đoạn sai, và field log là kênh prompt injection đã được đo.

**Điểm chính**
- Bài toán là **event abstraction** (nâng event mức thấp lên hoạt động mức cao), gần nhất là WATSON: gom hành vi theo phiên, phân cụm, rồi chỉ gán nhãn đại diện cụm, đạt F1 92,8% và giảm khối lượng phân tích hai bậc độ lớn [3].
- Gọi LLM theo chữ ký mới thay vì theo event là mẫu đã được đo: LILAC trung bình 279,7 lời gọi mỗi dataset Loghub-2.0 (trung bình 3,6 triệu dòng mỗi dataset) [1]; Clio đặt tên cụm từ vài mẫu, dựng lại đúng 94% danh mục trên dữ liệu tổng hợp [4].
- Đếm, gộp, sắp thứ tự thời gian phải do code làm: GPT-5, Claude Sonnet 4 và Gemini 2.5 Pro đều dưới 50% trên Oolong ở 128K [2], còn tóm tắt sự cố do LLM tự viết bỏ sót chi tiết quan trọng ở 35% và chèn sai sự thật ở 42% trong 50 sự cố thật [5].
- OCSF 1.9.0 có 290–590 đường dẫn field lá mỗi class, nhưng một event hoạt động mô tả đủ bằng khoảng 10–15 field quanh `type_uid = class_uid·100 + activity_id` [6][7].
- Bước đắt nhất của phần tất định là sắp xếp O(n log n) (DuckDB sắp 1 tỷ số nguyên ngẫu nhiên trong khoảng 6,5 s trên một laptop M1 Max [8]); các bước còn lại là hash map, group-by và quét tuyến tính. Bẫy chi phí là episode mining và phân cụm phân cấp trên dữ liệu thô [9][3].
- Không có dataset Windows nào có nhãn hoạt động lành tính; ATLASv2 (Sysmon + Windows Security, 4 ngày người thật dùng trên VM Windows 7) là nền thử tốt nhất nhưng phải tự gán nhãn [10].

## Bài toán là event abstraction trên host log: sáu dòng nghiên cứu, mỗi dòng cho một khối

Không có công trình nào giải trọn bài toán "telemetry endpoint → dòng thời gian hoạt động người", nhưng sáu dòng nghiên cứu mỗi dòng cung cấp một khối của pipeline. Process mining gọi đây là **event abstraction**: dữ liệu ghi ở nhiều mức granularity trong khi phân tích cần một mức nhất quán, nên phải "abstract event data into the right level of granularity" [11]. Hai cách kinh điển là mô tả mỗi hoạt động bằng một pattern do chuyên gia viết rồi alignment với log mức thấp [12], và học có giám sát bằng Conditional Random Fields; cách sau đã được áp vào smart home, nơi event cảm biến phải thành hoạt động sinh hoạt của người [13]. Nhánh LLM của smart home cho thấy cả tiềm năng lẫn bẫy: GPT-4 gán nhãn hoạt động đạt **0,81–0,97** tùy loại cảm biến, nhưng lớp "không có hoạt động" kém nhất ở cả ba dataset, và model thường đoán ra một hoạt động thật (ví dụ xem TV) khi đáp án là không có hoạt động [14].

Phía bảo mật, **WATSON** là công trình gần nhất và tự nhận là "the first to abstract both benign and malicious behaviors". Nó dựng knowledge graph từ audit log, cắt thành *behavior instance* trong từng phiên đăng nhập bằng DFS có ràng buộc thời gian, hạ trọng số event lặp ở nhiều phiên bằng **IDF**, phân cụm phân cấp với ngưỡng cosine 0,85, rồi để analyst chỉ gán nhãn đại diện mỗi cụm; kết quả F1 trung bình **92,8%** trên 25 hành vi trong 5.280 phiên [3]. Các phép giảm provenance cho bước tiền xử lý rẻ: CPR gộp event lặp cùng cặp nguồn–đích bằng một lượt quét với hash table, giảm trung bình **56%** dữ liệu (riêng Windows chỉ 1,61×) [15]; DPR giảm 4,6–19× và xử lý gần 1 triệu event/giây [16]. Kiernan và Terzi tóm tắt chuỗi event bằng MDL trên chính Windows Event Log; biến thể Greedy-Greedy O(nm log n log m) chạy 1–24 giây trên ba log, với tỉ lệ nén gần như bằng bản DP-DP tối ưu, vốn mất khoảng 10 giờ trên log system [17].

| Dòng nghiên cứu | Khối đóng góp cho pipeline | Kỹ thuật tiêu biểu | Chi phí |
|---|---|---|---|
| Log parsing | Biến chuỗi tự do (cmd_line, URL, đường dẫn) thành template | Drain, cây độ sâu cố định [18] | O(n) |
| Giảm provenance | Bỏ event lặp mà không mất phụ thuộc | CPR, DPR [15][16] | O(n) |
| Sessionization, task mining | Cắt dòng event thành phiên/task | Gap timeout, cửa sổ 30 s (CAAD) [19], back-edge (Leno) [20] | O(n log n) |
| Behavior abstraction | Gom event trong phiên thành hành vi theo đồ thị nhân quả | WATSON [3] | Vượt ngân sách nếu chạy trên dữ liệu thô |
| Event-sequence summarization | Phân đoạn trục thời gian | MDL Greedy-Greedy [17] | O(nm log n log m) |
| Event abstraction | Gán nhãn hoạt động mức cao | Pattern [12], CRF [13], phân cụm + gán nhãn [3] | Theo số cụm |

Phần khó nhất là **đa nhiệm xen kẽ**. Phương pháp phân đoạn UI log của Leno et al. (dựa trên back-edge của đồ thị luồng điều khiển) đạt edit distance 0,059–0,095 trên hai log thật đơn task, nhưng tăng lên **0,331** và chỉ tìm được **50/100** segment khi hai task xen kẽ [20]. Phát hiện chuyển task của Meyer et al. trên 25 lập trình viên đạt 84% cho thời điểm chuyển nhưng chỉ **61%** cho loại task [21]. **Nhận định:** trên Windows, Chrome, IDE và chat chạy song song là chuyện thường, nên phải tách theo entity (cây process, logon session) *trước* khi cắt theo thời gian, như WATSON và các hệ thống gom theo process đã làm; cắt thuần theo thời gian sẽ trộn các hoạt động song song vào một phân đoạn.

## LLM thua code ở đếm và gộp, thắng ở đặt tên, nên phải đứng sau bước gom

Bằng chứng về giới hạn ngữ cảnh dài rất nhất quán. Độ chính xác có dạng chữ U theo vị trí thông tin [22]; trong 17 model tuyên bố hỗ trợ ít nhất 32K token, chỉ khoảng một nửa giữ hiệu năng chấp nhận được ở 32K [23]; khi cần suy luận liên kết thay vì khớp chuỗi, 11/13 model rơi dưới 50% mức baseline ngữ cảnh ngắn ở 32K [24]. Tệ nhất cho bài toán này là Oolong, nơi model phải phân tích từng mẩu rồi gộp kết quả để trả lời câu hỏi mang tính phân phối; GPT-5, Claude Sonnet 4 và Gemini 2.5 Pro đều dưới 50% ở 128K [2]. **Nhận định:** "tóm tắt một ngày thành các hoạt động" chính là tác vụ kiểu Oolong; với một event OCSF JSON cỡ 300–1.000 token, 500k event thành khoảng 150–500 triệu token, nên đưa thô vào prompt vừa không vừa context vừa rơi đúng vùng suy giảm đã đo. Thực nghiệm forensic xác nhận điều đó ở quy mô nhỏ: trên kịch bản Windows 11 trích bằng Plaso, toàn timeline vượt giới hạn token nên tác giả chỉ đưa khoảng 2.000 dòng cho ChatGPT-4o; điểm trung bình BLEU/ROUGE của tóm tắt event khi không có tri thức bổ sung chỉ 0,106–0,134, và tác giả kết luận ChatGPT kém cách dùng luật/regex cùng người điều tra [25]. Ở dữ liệu thật, tóm tắt sự cố do LLM tự viết "omit critical details in 35% of cases and/or inject factual inaccuracies in 42% of cases" trên 50 sự cố, dù LLM cộng tác với analyst thì giảm công sức và tăng tính nhất quán [5]. Với văn bản dài, gộp phân cấp (map-reduce) cho kết quả mạch lạc hơn cập nhật tăng dần ở hầu hết cấu hình, và **bỏ sót** là lỗi phổ biến nhất ở cả hai cách [26].

Ngược lại, các hệ thống có số đo tốt đều dùng LLM cho việc *đặt tên* những đơn vị đã gom, với số lần gọi tỉ lệ số đơn vị khác nhau. LILAC tra một cache template dạng cây trước mỗi lời gọi, nên chỉ cần trung bình **279,7** lời gọi mỗi dataset, mỗi dataset trung bình 3,6 triệu dòng (so với trung bình 249 template thật) mà vẫn chính xác hơn Drain (GA 92,7 so với 84,3) [1]; LogBatcher thêm phân cụm (DBSCAN) và batch 10 log đa dạng, tổng token trung bình 11.701 so với 24.020 của LILAC, tức khoảng một nửa [27]. Clio của Anthropic trích facet, phân cụm bằng k-means rồi để model đặt tên cụm từ vài mẫu, dựng lại đúng **94%** danh mục trên hội thoại tổng hợp và tốn **48,81 USD cho một lần chạy 100.000 hội thoại** [4]; TnT-LLM dùng LLM gán nhãn mẫu rồi chưng cất sang bộ phân loại nhẹ để chạy quy mô lớn [28]. Gần nhất với "event → hoạt động người", ADL-LLM viết event cảm biến thành câu ngắn theo góc nhìn chủ thể, dùng thời gian tương đối và danh sách nhãn đóng; gpt-3.5-turbo zero-shot đạt weighted F1 **0,94/0,75/0,80** trên ba dataset, chỉ kém 0–3 điểm so với DeepConvLSTM huấn luyện trên 30% dữ liệu [29]. Nhưng kết quả phụ thuộc mạnh vào cách đặt bài: một cách zero-shot phân cấp khác trên dataset van Kasteren chỉ đạt macro-F 26,63% với ChatGPT [30].

Sản phẩm thực tế đi cùng hướng. Timesketch khử trùng lặp event theo cột `message` rồi gọi LLM một lần [31], còn tính năng `log_analyzer` bắt mỗi finding mang `record_id` của event gốc và bỏ finding thiếu ID [32]. Elastic Attack Discovery gửi alert chứ không gửi event, mặc định tối đa 100 alert và nâng được tới 500, dùng chung thiết lập anonymization quy định field nào được gửi và field nào bị che [33]. SentinelOne mô tả Purple AI tóm tắt một Storyline, tức hoạt động file/network/DNS đã được gom theo cây process [34]. Hai sample chính thức của AWS trên Security Lake (dữ liệu OCSF) cho LLM sinh SQL, để Athena aggregate, rồi LLM diễn giải kết quả nhỏ [35][36]. Phía phân tích năng suất, ActivTrak suy ra "người dùng đang làm gì" bằng phân loại app/website theo danh mục, ưu tiên luật thủ công, và chỉ để AI lấp phần chưa phân loại [37]. Agent tự do truy vấn log thì chưa đủ tin cậy để làm cơ chế chính: trên ExCyTIn-Bench, model tốt nhất (o4-mini) chỉ đạt reward trung bình **0,368** [38].

**Nhận định:** gộp lại, LLM có ba vị trí đáng đặt: (a) gán danh mục cho giá trị app/domain chưa biết, một lần cho mỗi giá trị; (b) đặt nhãn hoạt động cho mỗi chữ ký phiên mới; (c) viết tường thuật mỗi ngày từ bảng đã gom. LLM không nên parse từng event, đếm, sắp thời gian hay tính khoảng thời gian.

## OCSF cho sẵn khóa nén: `type_uid`, `process.uid` và 10–15 field thay cho ~500

Con số "~500 field" của brief khớp với schema thật nếu tính đường dẫn lá. OCSF ổn định hiện tại là **1.9.0** (phát hành 2026-08-03) [39]. Mỗi class endpoint có khoảng 60–96 attribute cấp cao nhất khi bật mọi profile, và **290–590** đường dẫn lá khi trải object một cấp (Process Activity 301, HTTP Activity 590); riêng Process Activity chỉ còn 39 attribute khi tắt profile [7]. Đó là số đường dẫn *có thể có*, không phải số field thực sự được điền.

Phần lớn thông tin cần cho insight nằm trong vài field chuẩn. `type_uid` bắt buộc bằng `class_uid * 100 + activity_id` và "uniquely identifies the combination of event class and activity across the entire schema" [6]; với khoảng 40–50 loại event của brief, đó là 40–50 khóa template sẵn có. Các enum chung (`status_id` 1 Success/2 Failure, `action_id`, khoảng 28 giá trị `disposition_id` như Blocked, Quarantined) nén kết quả của event thành một mã nhỏ [7]. Object `process` có `uid` để "facilitates correlation of a process event with other events for that process", còn `parent_process` chỉ nên điền ở mức trên cùng để tránh lồng sâu [40]. Ở phía nguồn, Sysmon gắn ProcessGuid duy nhất "even when Windows reuses process IDs" và session GUID cho mỗi logon [41]; event 4624 có Logon ID để nối với các event cùng phiên [42]. Field `message` chỉ là *recommended* và do nguồn tự định nghĩa [6], nên không thể trông vào nó.

| Nhóm | Field OCSF | Dùng làm gì trong pipeline |
|---|---|---|
| Thời gian và loại | `time`, `type_uid` | Sắp xếp, khóa template render, khóa đếm |
| Kết quả | `status_id`, `action_id`, `disposition_id`, `severity_id` | Phân biệt thành công/thất bại/bị chặn, dò burst thất bại |
| Chủ thể | `actor.user.name`, `actor.session.uid`, `actor.process.uid`/`name` | Khóa gom theo người, logon session, cây process |
| Lineage | `process.uid`, `parent_process.uid`, `lineage` | Dựng cây process, phân biệt khởi tạo bởi shell người dùng hay dịch vụ |
| Đối tượng chính theo class | `process.cmd_line`, `file.path`, `dst_endpoint`, `query.hostname`, `http_request.url`, `reg_key.path`, `logon_type_id` | Chuẩn hóa thành phần "cái gì" của chữ ký |
| Bằng chứng | `metadata.uid` hoặc ID bản ghi, `observables` | Truy vết từ câu tường thuật về event gốc |

**Nhận định:** `device` gần như hằng số trong batch một thiết bị nên chỉ ghi một lần; `raw_data`, `unmapped`, `cloud`, `osint` có thể bỏ khi sinh insight. Pipeline nên tự render một câu ngắn cho mỗi event theo template khóa bằng `type_uid`, giống cách formatter của plaso ánh xạ mỗi loại event và enum thành `message` dễ đọc [43]. Dữ liệu OCSF trên Security Lake là Parquet phân vùng theo `eventDay` [44], nên đọc theo ngày và chỉ chiếu khoảng 20–40 cột là việc tự nhiên.

## Pipeline đề xuất: tám tầng tất định trong O(n log n), hai tầng LLM chính tăng theo số chữ ký mới và số ngày

**Nhận định:** bảng dưới là kiến trúc agent đề xuất, ghép từ các khối có nguồn ở trên; độ phức tạp của từng khối có nguồn, còn cách ghép và các ngưỡng là thiết kế chưa đo. Ký hiệu: n số event, k số cột đọc, S số phân đoạn, U số chữ ký phiên khác nhau, V số giá trị app/domain khác nhau, D số ngày.

| Tầng | Việc làm | Khối, nguồn | Chi phí | LLM |
|---|---|---|---|---|
| T0. Nạp | Đọc Parquet theo ngày và class, chiếu cột cần | Partition `eventDay` [44] | O(n·k) | Không |
| T1. Sắp xếp | Sắp theo `time` | Radix + merge sort của DuckDB [8] | O(n log n) | Không |
| T2. Entity | Dựng cây process bằng hash map `process.uid`; nối logon session; dự phòng (pid, thời điểm tạo) | ProcessGuid, Logon ID [41][42] | O(n), dự phòng O(n log n) | Không |
| T3. Chữ ký event và lọc nền | Tuple (`type_uid`, kết quả, tên image, đối tượng đã chuẩn hóa); Drain chỉ cho chuỗi tự do; tra bảng danh mục app/domain; gộp lặp kiểu CPR; hạ trọng số nền bằng IDF theo ngày | [18][15][3][37] | O(n) | Có, chỉ cho giá trị app/domain chưa biết: O(V mới) |
| T4. Phân đoạn | Group theo entity gốc, rồi cắt theo khoảng trống trong từng nhóm; dò burst; gắn event điểm (detection) vào phân đoạn đang chạy | Session window [45], Kleinberg 2 trạng thái [46] | O(n log n) | Không |
| T5. Chữ ký phiên | Hash của (entity gốc, multiset chữ ký event đã nén lặp); tùy chọn MinHash/LSH để gom gần đúng | LSH banding [47] | O(n) + O(S·h) | Không |
| T6. Gán nhãn | Với chữ ký phiên chưa có trong cache: gửi 2–3 phiên đại diện đã render thành câu, danh sách nhãn đóng + "không rõ"; nhận JSON {nhãn, độ tin, lý do, ID bằng chứng}; lưu cache bền | LILAC, Clio, ADL-LLM [1][4][29] | — | **O(U mới)** lời gọi |
| T7. Gộp ngày | Hợp nhất phân đoạn liền kề cùng nhãn, tính số đếm, thời lượng, khoảng không có telemetry | Group-by | O(S log S) | Không |
| T8. Tường thuật | Một lời gọi mỗi ngày, input là bảng phân đoạn có trần kích thước; mỗi dòng output mang ID phân đoạn | Map-reduce [26] | — | **O(D)** lời gọi |
| T9. Kiểm tra | Mọi entity, mốc giờ, số đếm trong output phải tra được về phân đoạn/event; đo độ phủ | Record ID của Timesketch [32] | O(số claim) | Không |

Vài chi tiết quyết định chất lượng. Ở T2, nếu event con chỉ có pid, **Nhận định:** giữ cho mỗi pid danh sách thời điểm start đã sắp rồi tìm nhị phân "process mang pid đó, start gần nhất trước t", tổng O(n log n); không dựa vào `parent_process` lồng nhau vì OCSF khuyên chỉ điền một cấp [40]. Ở T3, chữ ký là điểm tựa của toàn bộ cơ chế cache: nếu giữ nguyên PID, GUID hay đường dẫn tạm, số chữ ký sẽ tăng theo n; nếu quá thô, các hoạt động khác nhau bị gộp nhầm. LILAC gặp đúng vấn đề này và phải có bước tinh chỉnh template trong cache [1]. Với dữ liệu đã có cấu trúc, hash trực tiếp trên field phân loại tốt hơn đẩy cả event thành text rồi chạy Drain, vì FGA của Drain tụt từ 0,75 xuống khoảng 0,55 khi chuyển từ Loghub-2k sang Loghub-2.0 lớn hơn [48]. Việc lọc nền mượn nguyên lý IDF của WATSON (event có mặt ở mọi phiên là boilerplate) [3], với "ngày" thay cho "phiên". Ở T4, burst thất bại tính bằng cửa sổ trượt hai con trỏ O(n) hoặc mô hình Kleinberg hai trạng thái [46]; PELT tuyến tính chỉ "under mild conditions" và xấu nhất O(n²) [49], nên chỉ chạy nó trên chuỗi đếm theo phút, nơi độ dài chuỗi là số bucket chứ không phải n.

Hai khối cần tránh ở dạng không giới hạn. Episode mining kiểu WINEPI/MINEPI có thể sinh "millions of episodes" với minsup thấp [9]; nếu cần mẫu tuần tự, giới hạn bằng n-gram độ dài cố định trong từng phiên. Phân cụm phân cấp của WATSON và DFS từ mọi data object chỉ chạy được vì đơn vị là phiên đã cắt [3]; ở đây nên chạy chúng (nếu cần) trên S phân đoạn, không trên n event.

Về số lời gọi LLM, **Nhận định:** tổng số lời gọi là V_mới + U_mới + D, mỗi lời gọi có trần token (vài phiên đại diện, vài field mỗi event, trần số phân đoạn mỗi ngày), nên tổng token không phụ thuộc trực tiếp vào n. U tăng theo độ đa dạng hành vi chứ không theo khối lượng, giống số template trong log parsing (khoảng 249 template cho 3,6 triệu dòng [1]). Ước tính của agent cho batch 500k event, 7 ngày, chưa đo trên dữ liệu thật:

| Cách làm | Lời gọi LLM | Token |
|---|---|---|
| Gửi thẳng event JSON | Hàng nghìn (map-reduce bắt buộc) | ~150–500 triệu |
| Pipeline trên, batch đầu (giả định 50–200 chữ ký phiên mới) | 50–200 gán nhãn + 7 tường thuật | ~0,1–0,5 triệu |
| Pipeline trên, batch sau (cache đã ấm) | Chữ ký mới + 7 | Tiến về ~20–70 nghìn |

Kiểm chứng bằng số đo là việc đầu tiên nên làm khi hiện thực: đếm số chữ ký phiên mới mỗi ngày trên dữ liệu thật để biết U có thật sự bão hòa hay không. Nút cổ chai tính toán gần như chắc chắn không phải phần tất định: DuckDB sắp 10 triệu số ngẫu nhiên trong 0,094 s [8], trong khi trong ADL-LLM khoảng 80% lời gọi LLM gán nhãn một cửa sổ mất tới 2 s [29].

**Nhận định:** agent truy vấn SQL chỉ nên là lớp khoan sâu tùy chọn, đọc các bảng đã gom ở T5/T7 và lấy bằng chứng khi người dùng hỏi tiếp, theo mẫu text-to-SQL của AWS trên Security Lake [35]; reward 0,368 của model tốt nhất trên ExCyTIn-Bench [38] cho thấy chưa nên để agent tự sinh timeline.

Lựa chọn LLM local hay cloud nên chia theo dữ liệu mà bước đó chạm tới. T3 (gán danh mục domain/app) và T6 (đọc câu render có đường dẫn, URL, tên file) chạm chuỗi thô nhạy cảm; T8 chỉ đọc bảng nhãn đã trừu tượng. Redaction không đủ an toàn: một so sánh tám kỹ thuật cho thấy kết hợp route local, redaction và rephrase hạ rò rỉ PII xuống 0,6% nhưng 31,3% mã độc quyền vẫn lộ (preprint, mới đối chiếu abstract) [50]. Đổi lại, model nhỏ yếu hơn rõ: trong ADL-LLM, trên dataset MARBLE, Llama-2-13b chỉ đạt 0,68 còn gpt-4o đạt 0,84 với chi phí gấp khoảng 10 lần gpt-3.5, và Llama-2 hay phá format, trả nhãn ngoài danh sách [29]; GenDFIR chạy được Llama-3.1-8B local trên GPU 8 GB nhưng mới thử trên 177 event của sáu kịch bản [51]. **Nhận định:** cấu hình hợp lý là model local cỡ vừa cho T3/T6, nơi output là JSON với nhãn đóng và dễ kiểm bằng code, còn model cloud mạnh hơn cho T8, nơi input đã sạch chuỗi thô. Biểu diễn đầu vào cũng phải thử với chính model định dùng, vì cùng một dạng nén có thể giúp model này và hại model khác [52].

## Năm hoạt động mẫu đi qua pipeline: phần lớn nhận ra bằng luật, LLM chỉ đặt tên và nối câu

**Nhận định:** bảng dưới là thiết kế của agent, áp tầng T2–T8 vào các ví dụ trong brief; tên class, activity và enum lấy từ schema OCSF 1.9.0 [7][6], còn tín hiệu phân biệt người/máy là heuristic chưa có nguồn đo độ chính xác.

| Hoạt động | Event OCSF chính | Khóa gom và phân đoạn | Code tính | LLM làm |
|---|---|---|---|---|
| Lướt web bằng Chrome | Network 4001, DNS 4003 (`query.hostname`), HTTP 4002 (`url.hostname`), File 1001 trong thư mục Downloads | Cây process gốc `chrome.exe`, cha là shell người dùng; cắt theo khoảng trống | Số domain, top domain theo danh mục, thời lượng, số file tải | Gán danh mục cho domain chưa biết (mỗi domain một lần); đặt tên phiên |
| Admin cập nhật phần mềm | Process 1007 Launch có integrity cao, Windows Service 201004 Create/Reconfigure/Start, File 1001 trong thư mục chương trình, Registry Value 201002 | Logon session (`actor.session.uid`) cộng cây process của trình cài đặt | Phiên do người khởi tạo hay dịch vụ tự chạy (lineage, `logon_type_id`), số dịch vụ/file thay đổi | Đặt nhãn "cài/cập nhật phần mềm X với quyền admin" |
| Phát hiện malware trong lúc người dùng làm X | Detection Finding 2004 Create, `disposition_id` Quarantined/Blocked | Event điểm, gắn vào phân đoạn đang chạy theo `process.uid` hoặc chồng thời gian | Quan hệ "trong lúc" và "file do process nào tạo" bằng join | Viết câu nối hai hoạt động |
| Lập trình với Claude, tải file thực thi bị chặn | Process 1007 của agent dưới terminal/IDE, Network/HTTP tới API của nhà cung cấp, File 1001 Create `.exe` hoặc Network Refuse với `status_id` Failure, `disposition_id` Blocked | Cây process của agent trong phiên người dùng | Số lần tải thất bại, khoảng thời gian, tên file đã chuẩn hóa | Đặt nhãn "phiên lập trình có trợ lý AI, 7 lần tải .exe bị chặn" |
| Đăng nhập thất bại liên tiếp | Authentication 3002 Logon, `status_id` 2 Failure, `logon_type_id` | Chuỗi theo user đích, cửa sổ trượt hoặc Kleinberg 2 trạng thái | Số lần, khoảng thời gian, có thành công ngay sau không, local hay remote | Chỉ diễn đạt; không đếm |

Ba ví dụ cần cẩn trọng riêng. Thứ nhất, "người hay máy" không đọc ra được trực tiếp từ log: nghiên cứu host log coi việc tách tiến trình nền khỏi hành vi người dùng là bài toán riêng [53], và chuyển event mức thấp thành hành động người vẫn chủ yếu là việc thủ công của analyst [54]. **Nhận định:** với "admin cập nhật phần mềm", tín hiệu khả dĩ là tổ tiên là shell người dùng chứ không phải `services.exe` hay Task Scheduler, logon interactive (`logon_type_id` 2 hoặc 10), tài khoản người chứ không phải SYSTEM, và nhịp thời gian không đều; timeline nên ghi kèm mức tin cậy và lý do thay vì khẳng định. Thứ hai, ví dụ lập trình với Claude cho thấy ranh giới "hoạt động người" đang mờ đi: phân biệt artifact do người, do máy hay do agent cộng tác sinh ra đã được gọi là "novel challenge" [55]. **Nhận định:** nên có một lớp chủ thể riêng "agent chạy dưới phiên người dùng", suy ra từ lineage, thay vì gán mọi thứ cho người. Thứ ba, ví dụ phát hiện malware chỉ dùng finding như một event điểm trong timeline; quan hệ "trong lúc lướt web, file vừa tải bị cách ly" là kết quả join theo `process.uid` và thời gian, không phải suy luận của LLM.

Output của T8 nên là JSON có cấu trúc trước, văn xuôi sau. Ví dụ minh họa (dữ liệu giả định):

```json
{"day": "2026-10-17", "items": [
  {"start": "09:12", "end": "10:40", "label": "Lướt web bằng Chrome", "confidence": "cao",
   "facts": {"domains": 38, "top_categories": ["tài liệu kỹ thuật", "tin tức"], "downloads": 2},
   "segments": ["s-0142", "s-0147"]},
  {"start": "10:05", "end": "10:05", "label": "Defender cách ly file vừa tải trong phiên Chrome",
   "facts": {"disposition": "Quarantined"}, "segments": ["s-0147"], "evidence": ["evt-88213"]},
  {"start": "13:30", "end": "16:10", "label": "Lập trình có trợ lý AI; tải file .exe bị chặn",
   "facts": {"blocked_downloads": 7}, "segments": ["s-0210"]},
  {"start": "21:02", "end": "21:04", "label": "12 lần đăng nhập thất bại, sau đó thành công (cục bộ)",
   "facts": {"failures": 12, "logon_type": "Interactive"}, "segments": ["s-0388"]}],
 "gaps": [{"start": "17:45", "end": "20:50", "reason": "không có telemetry"}]}
```

Mọi số trong `facts` do T7 tính và chèn vào; LLM chỉ chọn cách nói và thứ tự kể. Khoảng `gaps` được ghi tường minh để LLM không lấp chỗ trống bằng câu chuyện.

## Đánh giá phải tự dựng ground truth; kiểm tra tất định mạnh hơn mọi metric văn bản

Không có dataset công khai nào vừa là telemetry endpoint Windows đầy đủ vừa có nhãn hoạt động lành tính. ATLASv2 gần nhất: hai nhà nghiên cứu, mỗi người một VM Windows 7 32-bit, làm việc thật khoảng 8 giờ/ngày trong 4 ngày (web, Zoom, Office, Discord…), thu Sysmon, Windows Security, Carbon Black, tổng 154 GB cho cả 5 ngày (gồm ngày tấn công), nhưng benign chỉ là giả định ("We operate under the assumption that all activity logged during the first four days is benign") và không có nhật ký hoạt động [10]. DARPA OpTC lớn (khoảng 17,4 tỉ event) nhưng "there is little to no explanation provided about the events in the dataset" [56], và ground truth chỉ là tài liệu red team [57]. WATSON tự dựng ground truth bằng kịch bản lặp: 4 người, 7 task, mỗi task 150 lần, cộng 1.000 phiên nền thật được lọc tay, nhưng trên Linux [3]. Leno et al. đo phân đoạn bằng edit distance chuẩn hóa so với log ghi có giám sát [20], còn Meyer et al. lấy nhãn bằng quan sát trực tiếp và experience sampling, đo cả độ trễ phát hiện chuyển task (dưới 1,6 phút) [21]. **Nhận định:** cách khả thi nhất cho chủ repo là chạy chính các kịch bản trong brief có nhãn trên một máy Windows có Sysmon → OCSF, xen với vài ngày dùng thật có nhật ký tự ghi, rồi chấm bằng ba metric: edit distance giữa chuỗi hoạt động dự đoán và tham chiếu, F1 theo loại hoạt động, và độ lệch ranh giới thời gian.

Phần tường thuật không nên chấm bằng ROUGE. Đổi "decreased" thành "increased" đảo nghĩa câu mà ROUGE-L không đổi [58], và bộ phát hiện hallucination tốt nhất trên FaithBench chỉ đạt gần 50% [59]. Lợi thế của bài toán này là nguồn sự thật có cấu trúc, nên kiểm tra tất định khả thi và rẻ: Timesketch đã loại mọi finding không mang ID event gốc [32], và khuyến nghị DFIR là "existence check" mọi đường dẫn, mốc thời gian mà AI nhắc tới, trong khi judge LLM thứ hai có thể cùng mắc lỗi kiến thức với model đầu [60]. **Nhận định:** thứ tự kiểm nên là (1) mọi item mang ID phân đoạn/event; (2) code đối chiếu entity, giờ, số đếm; (3) độ phủ, tức tỉ lệ phân đoạn lớn trong ngày được nhắc tới, để bắt lỗi bỏ sót kiểu 35% của Kramer et al. [5]; (4) LLM-judge chỉ là lớp bổ sung; (5) chấm tay trên mẫu có ground truth.

Hai rủi ro vận hành còn lại cần đưa vào thiết kế ngay từ đầu. **Prompt injection qua field log** đã được đo trên log bảo mật: user agent, URL, payload, DNS query, username thử đăng nhập đều do bên ngoài điều khiển, và tóm tắt là tác vụ rủi ro cao nhất; với gpt-4o-mini, phòng thủ mạnh nhất chỉ hạ tỉ lệ tiêm thành công trung bình từ 26,6% xuống 11,8% [61]. Trên LogInject-1.0 (log mạng), ASR trung bình 83,4%, và phòng thủ nhiều lớp vẫn để lọt 8,4% [62]. **Nhận định:** command line và đường dẫn file trên endpoint cũng do tiến trình hay người ngoài kiểm soát được, nên cùng loại rủi ro. OWASP khuyên tách và đánh dấu nội dung không tin cậy và kiểm tra định dạng output bằng code tất định [63]. **Nhận định:** pipeline trên tự nhiên giảm bề mặt tấn công vì T8 chỉ nhận nhãn và số đếm chứ không nhận chuỗi thô; T6 vẫn chạm chuỗi thô nên phải bọc chúng như dữ liệu và chỉ chấp nhận output thuộc danh sách nhãn đóng. **Thiên kiến tự động hóa** là rủi ro thứ hai: phỏng vấn 25 người làm SOC cho thấy niềm tin tăng dần trôi thành chấp nhận không phê phán [64]. **Nhận định:** output nên cấm ngôn ngữ ý định ("người dùng muốn…") khi không có bằng chứng, chỉ kể hành động quan sát được, và gắn nhãn rõ phần do AI sinh.

## Các nguồn bất đồng ở đâu

Về **định dạng đưa vào prompt**, nghiên cứu của Google trên log Procmon Windows của các kịch bản tấn công thấy biểu diễn cạnh provenance (ở kịch bản lớn nhất giảm khoảng 237 lần số dòng, từ 1.229.728 xuống 5.198) luôn giúp Llama 4 Maverick, trong khi tác giả ghi Gemini 2.5 Pro làm tốt hơn trên log thô ở mọi task (bảng kết quả cho thấy hòa ở task lateral movement) [52]. Với bảng, TQA-Bench thấy Markdown tốt nhất với đa số model [65], còn một nghiên cứu trích xuất từ báo cáo tài chính dài thấy plain text (0,70) và CSV (0,69) vượt HTML (0,51) và XML (0,46) [66]. Hai bên lệch vì khác model và khác tác vụ, nên không có định dạng thắng tuyệt đối; nên tin kết luận chung "phụ thuộc model" và tự đo với model định dùng. Về **LLM parser so với Drain**, LILAC báo GA 92,7 so với 84,3 của Drain [1], trong khi đánh giá độc lập ISSTA 2024 trên 15 parser kết luận Drain gom nhóm tốt nhất [48]; đánh giá ISSTA không gồm LILAC, và LILAC tự đánh giá, nên con số của LILAC cần đọc như kết quả của tác giả. Với OCSF, bất đồng này ít quan trọng vì phần lớn chữ ký là tuple field có cấu trúc. Về **gộp phân cấp hay tăng dần**, BooookScore thấy gộp phân cấp thắng ở hầu hết cấu hình, ngoại trừ Claude 2 với chunk 88K, nơi tăng dần nhỉnh hơn (90,9 so với 90,3) và người chấm thích độ chi tiết của tăng dần 83% số lần [26]. Với timeline theo ngày, gộp phân cấp vẫn hợp hơn vì cấu trúc ngày → phân đoạn đã là phân cấp.

## Kết luận và hàm ý

**Nhận định:** điều rút ra mới là bài toán "insight hoạt động người" có cùng cấu trúc với log parsing bằng LLM, chỉ ở mức cao hơn một bậc: thay vì template của dòng log, đơn vị là **chữ ký phiên**, và mẹo khiến LLM rẻ, ổn định là cache theo chữ ký đó. Vì OCSF đã cho sẵn `type_uid`, enum kết quả và khóa lineage, phần tất định của pipeline gần như toàn là SQL trên DuckDB (window function cho khoảng trống, hash join cho entity, group-by cho đếm), và độ phức tạp O(n log n) không phải là thách thức. Thách thức thật nằm ở ba chỗ code không tự giải được: chọn độ mịn của chữ ký, tách hoạt động song song, và phân biệt người, dịch vụ và agent AI. Hướng MITRE mà chủ repo bỏ đi sai ở chỗ nó gán nhãn theo kỹ thuật tấn công, trong khi ở đây nhãn là *hoạt động*, và finding an ninh chỉ là một loại event điểm gắn vào hoạt động đang diễn ra.

Hàm ý cho việc hiện thực, theo thứ tự: (1) chốt quy ước "ngày" (UTC theo `eventDay` hay giờ địa phương từ `time` cộng `timezone_offset`, phiên vắt qua nửa đêm gán cho ngày nào); (2) dựng T0–T5 và T7 bằng DuckDB trước, chưa có LLM, rồi đo số chữ ký phiên mới mỗi ngày trên vài ngày dữ liệu thật; nếu đường cong không bão hòa thì chữ ký quá mịn; (3) viết bảng danh mục app/domain và tập nhãn hoạt động đóng (bắt đầu từ năm hoạt động trong brief), thêm T6 với cache bền; (4) thêm T8 và T9 cùng lúc, không tách rời; (5) dựng bộ kịch bản có nhãn trên một máy Windows có Sysmon, hoặc gán nhãn lại một phần ATLASv2, trước khi tinh chỉnh prompt.

## Chưa kiểm chứng được

- Không tìm thấy nghiên cứu nào đo độ chính xác LLM gán nhãn hoạt động người (duyệt web, cập nhật phần mềm, lập trình) từ telemetry Windows hay OCSF. Truy vấn đã thử: "LLM summarize Windows event logs Sysmon user activity narrative" (extended), "process mining operating system logs Windows user activity discovery Sysmon event abstraction", "OCSF events LLM summarization narrative blog" (extended).
- Chưa có số đo về số chữ ký phiên khác nhau mỗi ngày hay tỉ lệ cache hit trên telemetry endpoint thật; mọi ước tính lời gọi và token trong report là của agent.
- Chưa có nghiên cứu có ground truth đo độ chính xác phân biệt hoạt động người với hệ thống trên Sysmon/Windows Security. Truy vấn: "distinguishing user-initiated vs automated activity host logs", "inferring high-level user activities from low-level host events semantic gap background noise".
- Không có thống kê công khai về tỉ lệ field OCSF thực sự được điền trong event Windows, cũng chưa có benchmark DuckDB/Polars trên OCSF Parquet lồng sâu.
- Chưa lấy được số liệu kết quả của DEPCOMM (gom đồ thị theo cộng đồng process) vì trang nguồn từ chối kết nối, và chưa đọc toàn văn survey event abstraction của van Zelst et al.
- Không rõ input thật (bảng nào, bao nhiêu event) của Security Copilot device summary và Google SecOps case summary; không có đánh giá độc lập nào về độ chính xác của các trợ lý AI trong SIEM/XDR.
- Chưa có nghiên cứu người dùng nào về việc người đọc bị timeline hoạt động do LLM viết dẫn sai; Kramer et al. là tóm tắt sự cố.
- Một số số liệu chỉ đọc qua snippet hoặc abstract: TQA-Bench, LLM-Redactor, FaithBench, GO FIGURE, Meyer et al., phỏng vấn SOC về thiên kiến tự động hóa.

## Nguồn

[1] LILAC: Log Parsing using LLMs with Adaptive Parsing Cache — Jiang et al., FSE 2024 (bậc 1). https://arxiv.org/html/2310.01796v3
[2] Oolong: Evaluating Long Context Reasoning and Aggregation Capabilities — Bertsch, Pratapa, Mitamura, Neubig, Gormley, arXiv 2511.02817, 2025-11-04, sửa 2026-10-05 (bậc 1, preprint). https://arxiv.org/abs/2511.02817
[3] WATSON: Abstracting Behaviors from Audit Logs via Aggregation of Contextual Semantics — Zeng et al., NDSS 2021 (bậc 1). https://www.ndss-symposium.org/wp-content/uploads/2021-549-paper.pdf
[4] Clio: Privacy-Preserving Insights into Real-World AI Use — Anthropic, 2024-12 (bậc 1). https://arxiv.org/html/2412.13678v1
[5] Integrating Large Language Models into Security Incident Response — Kramer, Rosique, Narotam, Bursztein, Kelley, Thomas, Woodruff (Google, DataPhant), SOUPS 2025 (bậc 1). https://www.usenix.org/conference/soups2025/presentation/kramer
[6] OCSF Schema 1.9.0: Base Event — OCSF, 1.9.0 (bậc 1). https://schema.ocsf.io/1.9.0/api/classes/base_event
[7] OCSF Schema 1.9.0: Process Activity (và các trang class cùng phiên bản; số attribute do researcher tự tính từ API ngày 2026-10-18) — OCSF, 1.9.0 (bậc 1). https://schema.ocsf.io/1.9.0/api/classes/process_activity
[8] Redesigning DuckDB's Sort, Again — Laurens Kuiper, DuckDB blog, 2025-09-24 (bậc 1). https://duckdb.org/2025/09/24/sorting-again
[9] An Introduction to Episode Mining — Philippe Fournier-Viger, không rõ ngày (bậc 2). https://data-mining.philippe-fournier-viger.com/introduction-to-episode-mining/
[10] ATLASv2: ATLAS Attack Engagements, Version 2 — Riddle, Westfall, Bates, arXiv 2401.01341, 2023-10 (bậc 1). https://ar5iv.labs.arxiv.org/html/2401.01341
[11] Event abstraction in process mining: literature review and taxonomy — van Zelst, Mannhardt, de Leoni, Koschmider, Granular Computing, 2020 (bậc 1; chỉ đọc abstract). https://link.springer.com/article/10.1007/s41066-020-00226-2
[12] From Low-Level Events to Activities – A Pattern-Based Approach — Mannhardt et al., BPM 2016 (bậc 1; abstract). https://research.vu.nl/en/publications/from-low-level-events-to-activities-a-pattern-based-approach/
[13] Mining Process Model Descriptions of Daily Life through Event Abstraction — Tax, Sidorova, Haakma, van der Aalst, arXiv 1705.10202, 2017-05 (bậc 1). https://arxiv.org/pdf/1705.10202
[14] LLM-based event abstraction and integration for IoT-sourced logs — Shirali, Fani Sani, Ahmadi, Serral, arXiv 2409.03478, 2024-09 (bậc 1). https://arxiv.org/html/2409.03478v1
[15] High Fidelity Data Reduction for Big Data Security Dependency Analyses (CPR/PCAR) — Xu et al., CCS 2016 (bậc 1). https://www.eecis.udel.edu/~hnw/paper/ccs16b.pdf
[16] Dependence-Preserving Data Compaction for Scalable Forensic Analysis (DPR) — Hossain et al., USENIX Security 2018 (bậc 1). https://www3.cs.stonybrook.edu/%7Estoller/papers/compaction2018.pdf
[17] Constructing Comprehensive Summaries of Large Event Sequences — Kiernan & Terzi, KDD 2008 (bậc 1). https://sites.cs.ucsb.edu/~xyan/classes/CS290D-2009spring/reviews/p417.pdf
[18] A Directed Acyclic Graph Approach to Online Log Parsing (bản mở rộng của Drain) — He et al., arXiv 1806.04356, 2018 (bậc 1). https://arxiv.org/abs/1806.04356
[19] CAAD: An Automatic Task Support System — Rattenbury & Canny, CHI 2007 (bậc 1). https://people.eecs.berkeley.edu/~jfc/papers/07/CHI-CAAD2007.pdf
[20] Identifying candidate routines for Robotic Process Automation from unsegmented UI logs — Leno, Augusto, Dumas, La Rosa, Maggi, Polyvyanyy, ICPM 2020, arXiv 2008.05782 (bậc 1). https://arxiv.org/html/2008.05782v2
[21] Detecting Developers' Task Switches and Types — Meyer et al., IEEE TSE 48(1), 2022 (bậc 1; chỉ đọc abstract). https://www.merlin.uzh.ch/publication/show/19540
[22] Lost in the Middle: How Language Models Use Long Contexts — Liu et al., TACL vol. 12, 2024 (bậc 1). https://aclanthology.org/2024.tacl-1.9/
[23] RULER: What's the Real Context Size of Your Long-Context Language Models? — Hsieh et al., COLM 2024 (bậc 1). https://arxiv.org/abs/2404.06654
[24] NoLiMa: Long-Context Evaluation Beyond Literal Matching — Modarressi et al., ICML 2025 (bậc 1). https://proceedings.mlr.press/v267/modarressi25a.html
[25] Towards a standardized methodology and dataset for evaluating LLM-based digital forensic timeline analysis — Studiawan, Breitinger, Scanlon, DFRWS APAC 2025, arXiv 2505.03100 (bậc 1). https://arxiv.org/html/2505.03100v1
[26] BooookScore: A systematic exploration of book-length summarization in the era of LLMs — Chang, Lo, Goyal, Iyyer, ICLR 2024 (bậc 1). https://arxiv.org/html/2310.00785v2
[27] Stronger, Cheaper and Demonstration-Free Log Parsing with LLMs (LogBatcher) — Xiao, Le, Zhang, ASE 2024, arXiv 2406.06156 (bậc 1). https://arxiv.org/html/2406.06156v2
[28] TnT-LLM: Text Mining at Scale with Large Language Models — Microsoft, arXiv 2403.12173, 2024-03 (bậc 1). https://arxiv.org/abs/2403.12173
[29] Large Language Models are Zero-Shot Recognizers for Activities of Daily Living (ADL-LLM) — Civitarese, Fiori, Choudhary, Bettini, arXiv 2407.01238v3, 2024-07, sửa 2025-03 (bậc 1). https://arxiv.org/html/2407.01238v3
[30] Hierarchical Zero-Shot Approach for Human Activity Recognition in Smart Homes — Ulster University, UCAmI 2024 (bậc 1; số liệu qua snippet). https://pure.ulster.ac.uk/en/publications/hierarchical-zero-shot-approach-forhuman-activity-recognition-ins/
[31] timesketch/lib/llms/features/llm_summarize.py — Google (source code, đọc 2026-10-18) (bậc 1). https://github.com/google/timesketch/blob/master/timesketch/lib/llms/features/llm_summarize.py
[32] timesketch/lib/llms/features/log_analyzer.py — Google (source code, đọc 2026-10-18) (bậc 1). https://github.com/google/timesketch/blob/master/timesketch/lib/llms/features/log_analyzer.py
[33] Attack discovery — Elastic Security docs 8.17, không rõ ngày (bậc 1). https://www.elastic.co/guide/en/security/8.17/attack-discovery.html
[34] Purple AI: Empowering Cybersecurity Analysts with AI-Driven Threat Hunting, Analysis & Response — SentinelOne blog, cập nhật 2024-09-04 (bậc 1, tài liệu marketing). https://www.sentinelone.com/blog/purple-ai-empowering-cybersecurity-analysts-with-ai-driven-threat-hunting-analysis-response/
[35] Generate AI powered insights for Amazon Security Lake using Amazon SageMaker Studio and Amazon Bedrock — AWS Security Blog, 2024-01-16 (bậc 1). https://aws.amazon.com/blogs/security/generate-ai-powered-insights-for-amazon-security-lake-using-amazon-sagemaker-studio-and-amazon-bedrock
[36] Use an Amazon Bedrock powered chatbot with Amazon Security Lake to help investigate incidents — AWS Security Blog, 2025-05-01 (bậc 1). https://aws.amazon.com/blogs/security/use-an-amazon-bedrock-powered-chatbot-with-amazon-security-lake-to-help-investigate-incidents
[37] AI-Powered Activity Classification — ActivTrak, không rõ ngày (bậc 1, tài liệu vendor; chỉ đọc snippet). https://www.activtrak.com/product/activity-classification/
[38] ExCyTIn-Bench: Evaluating LLM agents on Cyber Threat Investigation — Wu et al. (Microsoft), arXiv 2507.14201, 2025-07 (bậc 1). https://arxiv.org/html/2507.14201v1
[39] ocsf/ocsf-schema releases — OCSF, bản 1.9.0 ngày 2026-08-03 (bậc 1). https://github.com/ocsf/ocsf-schema/releases
[40] OCSF Schema 1.9.0: Process object — OCSF, 1.9.0 (bậc 1). https://schema.ocsf.io/1.9.0/api/objects/process
[41] Sysmon — Microsoft Sysinternals, Microsoft Learn, cập nhật 2026-09-10 (bậc 1). https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon
[42] 4624(S): An account was successfully logged on — Microsoft Learn, cập nhật 2026-04-27 (bậc 1). https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4624
[43] Plaso: Output and formatting — Plaso docs, không rõ ngày (bậc 1). https://plaso.readthedocs.io/en/latest/sources/user/Output-and-formatting.html
[44] Collecting data from custom sources in Security Lake — AWS docs, không rõ ngày (bậc 1). https://docs.aws.amazon.com/security-lake/latest/userguide/custom-sources.html
[45] Native support of session window in Spark Structured Streaming — Databricks, 2021-10-12 (bậc 1). https://www.databricks.com/blog/2021/10/12/native-support-of-session-window-in-spark-structured-streaming.html
[46] Bursty and Hierarchical Structure in Streams — Jon Kleinberg, KDD 2002 (bậc 1). https://www.cs.cornell.edu/home/kleinber/bhs.pdf
[47] UnitX-Similarity (MinHash/LSH lecture) — Giri Narasimhan, FIU, 2018 (bậc 2). https://users.cs.fiu.edu/~giri/teach/5768/F18/lecs/UnitX-Similarity.pdf
[48] A Large-Scale Evaluation for Log Parsing Techniques: How Far Are We? — Jiang et al., ISSTA 2024 (bậc 1). https://arxiv.org/html/2308.10828v2
[49] Optimal detection of changepoints with a linear computational cost — Killick, Fearnhead, Eckley, JASA 2012 (bậc 1). https://arxiv.org/abs/1101.1438v3
[50] LLM-Redactor: An Empirical Evaluation of Eight Techniques for Privacy-Preserving LLM Requests — Owusu Agyemang et al., arXiv 2604.12064, 2026-04-13 (bậc 1, preprint; chỉ đọc abstract). https://arxiv.org/abs/2604.12064
[51] GenDFIR: Advancing Cyber Incident Timeline Analysis Through Retrieval Augmented Generation and Large Language Models — Loumachi, Ghanem, Ferrag, arXiv 2409.02572v3, 2024 (bậc 1). https://arxiv.org/html/2409.02572v3
[52] Benchmarking and Exploring the Capabilities of LLMs for Attack Investigations — Anand et al. (Google), arXiv 2606.10281v2, 2026-06-09, sửa 2026-09-26 (bậc 1, preprint). https://arxiv.org/html/2606.10281v2
[53] Defining a Metric Space of Host Logs and Operational Use Cases — Verma & Bridges (ORNL), IEEE BigData 2018 (bậc 1; chỉ đọc abstract). https://arxiv.org/abs/1811.00591v1
[54] How do information security workers use host data? A summary of interviews with security analysts — Bridges, Iannacone, Goodall, Beaver, arXiv 1812.02867, 2018 (bậc 1; chỉ đọc snippet). https://arxiv.org/pdf/1812.02867
[55] Digital Forensics in the Age of Large Language Models — Yin et al., arXiv 2504.02963, 2025-04 (bậc 1; chỉ đọc snippet). https://arxiv.org/pdf/2504.02963
[56] Analyzing the Usefulness of the DARPA OpTC Dataset in Cyber Threat Detection Research — Anjum et al., SACMAT 2021, arXiv 2103.03080 (bậc 1). https://arxiv.org/html/2103.03080v3
[57] OpTC-data — FiveDirections (GitHub), không rõ ngày (bậc 1). https://github.com/FiveDirections/OpTC-data
[58] GO FIGURE: A Meta Evaluation of Factuality in Summarization — Gabriel, Celikyilmaz, Jha, Choi, Gao, arXiv 2010.12834, 2020 (bậc 1; chỉ đọc snippet). https://arxiv.org/pdf/2010.12834
[59] FaithBench — NAACL 2025 (bậc 1; chỉ đọc snippet). https://aclanthology.org/2025.naacl-short.38
[60] DFIR + AI Primer: How to Combat Hallucinations — Brian Carrier, Cyber Triage, 2026-05-28 (bậc 2). https://www.cybertriage.com/ai/dfirai-primer-how-to-combat-hallucinations/
[61] Poisoning the Watchtower: Prompt Injection Attacks Against LLM-Augmented Security Operations Through Adversarial Log Content — Pandey & Bhujang, arXiv 2605.24421, 2026-05-23 (bậc 1, preprint). https://arxiv.org/abs/2605.24421
[62] Context Contamination in LLM Analysis of Network Security Logs: Poison with Passive Prompt Injection and Mitigation Evaluation — Karanjai et al., arXiv 2607.14493, 2026-07-16 (bậc 1, preprint). https://arxiv.org/abs/2607.14493
[63] LLM01:2025 Prompt Injection — OWASP GenAI Security Project, 2025 (bậc 1). https://genai.owasp.org/llmrisk/llm01-prompt-injection/
[64] From Chasing Ghosts to Missed Attacks: Perspectives and Perceptions of SOC Practitioners on LLM Integration, Risks, and Readiness — Thurner et al., arXiv 2608.00672, 2026-08 (bậc 1, preprint; chỉ đọc snippet). https://arxiv.org/html/2608.00672
[65] TQA-Bench: Evaluating LLMs for Multi-Table Question Answering — Qiu et al., arXiv 2411.19504, 2024-11 (bậc 1; chỉ đọc snippet). https://arxiv.org/pdf/2411.19504
[66] Enabling and Analyzing How to Efficiently Extract Information from Hybrid Long Documents with LLMs — Yue et al., arXiv 2305.16344, 2023-05, sửa 2024-03 (bậc 1). https://arxiv.org/pdf/2305.16344
