# Thuật toán, độ phức tạp và kỹ thuật triển khai

Góc này trả lời câu phụ 4 của brief: những khối thuật toán nào giữ phần xử lý trước LLM ở mức O(n) đến O(n log n), làm sao để số lời gọi LLM và số token tăng chậm hơn n, và cách xử lý dạng cột trên OCSF Parquet.

Ký hiệu dùng trong file: n là số event trong batch (khoảng 500k), k là số cột thật sự đọc (khoảng 20–40 trên ~500 field), S là số phiên (session), U là số chữ ký (signature) khác nhau.

---

## Câu phụ 4a: Các khối thuật toán và độ phức tạp đã được công bố

### Kết luận ngắn
Mọi bước trước LLM đều có thể giữ trong O(n log n): một lần sắp xếp theo (thiết bị, thời gian) là bước đắt nhất, còn lại là hash map, hash join và quét tuyến tính. Mức chắc chắn: **cao** cho sort, hash join, Drain và gom phiên theo khoảng trống, vì có nguồn bậc 1. Mức chắc chắn **trung bình** cho change-point/burst và phân cụm, vì độ tuyến tính của chúng phụ thuộc điều kiện hoặc tham số. Rủi ro phức tạp thật sự nằm ở episode mining và sequential pattern mining: số mẫu đầu ra bùng nổ, không phải chi phí của bước quét.

### Phát hiện có nguồn

**Sắp xếp theo thời gian / external sort**
- DuckDB: mỗi thread sắp phần dữ liệu của mình bằng radix sort, sau đó trộn các khối đã sắp bằng merge sort; với external sort, DuckDB dùng k-way merge vì cách này tối thiểu I/O — [Fastest Table Sort in the West – Redesigning DuckDB's Sort](https://duckdb.org/2021/08/27/external-sorting) (bậc 1, 2021-08-27).
- Bản thiết kế lại năm 2025 (M1 Max, 10 thread, 64 GB RAM, trung vị 5 lần chạy): sắp 1 tỷ số nguyên ngẫu nhiên hết **6,493 s** (bản cũ 17,554 s); 1 tỷ số đã sắp tăng dần hết 1,475 s; 10 triệu số ngẫu nhiên hết 0,094 s. Bảng rộng TPC-H lineitem 15 cột: 60 triệu dòng hết 1,520 s; 600 triệu dòng (SF100, vượt giới hạn RAM 30 GB, tức chạy larger-than-memory) hết 80,919 s. Dữ liệu đã sắp sẵn được hưởng lợi nhiều nhất (nhanh hơn khoảng 10 lần) — [Redesigning DuckDB's Sort, Again](https://duckdb.org/2025/09/24/sorting-again) (bậc 1, 2025-09-24).
- Bài báo của Kuiper, Raasveldt và Mühleisen cho thấy hiệu năng gần như không giảm khi dữ liệu vượt xa bộ nhớ — [Efficient External Sorting in DuckDB](https://ceur-ws.org/Vol-3163/BICOD21_paper_9.pdf) (bậc 1, 2022). Kết luận này lấy từ snippet tìm kiếm; chưa đọc phần thực nghiệm.

**Dựng cây process và xử lý PID bị dùng lại**
- Sysmon "Includes a process GUID in process create events to allow for correlation of events even when Windows reuses process IDs" và "Includes a session GUID in each event to allow correlation of events on same logon session". Event ID 1: "`ProcessGUID` field is a unique value for this process across a domain". Event ID 3 (network) "is linked to a process through the `ProcessId` and `ProcessGuid` fields". Event ID 5 (terminate) mang `UtcTime`, `ProcessGuid`, `ProcessId` — [Sysmon - Sysinternals, Microsoft Learn](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon) (bậc 1, cập nhật 2026-09-10).
- Event 1 của Sysmon có các trường ProcessGuid, ParentProcessGuid, LogonGuid và LogonId — [EventSentry Sysmon Event ID 1](https://system32.eventsentry.com/sysmon/event/1) (bậc 2, không rõ ngày).
- OCSF 1.3.0, object Process: `uid` "A unique identifier for this process assigned by the producer (tool)"; `pid` "as reported by the operating system"; `created_time`; `parent_process` "It is recommended to only populate this field for the first process object, to prevent deep nesting"; `lineage` là mảng đường dẫn của các process tổ tiên; `session` "The user session under which this process is running". Mỗi event phải có ít nhất một trong hai trường `pid` hoặc `uid` — [OCSF Process object 1.3.0](https://schema.ocsf.io/1.3.0/objects/process) (bậc 1, phiên bản 1.3.0).
- Cấu trúc bên trong ProcessGuid (đoạn giữa là thời điểm tạo, tính bằng giây Unix, rồi đến một bộ đếm) là quan sát không chính thức và đã thay đổi theo phiên bản; không nên parse nó — [Structure of process GUIDs used in Sysmon ETW events, Microsoft Q&A](https://learn.microsoft.com/en-au/answers/questions/234884/structure-of-process-guids-used-in-sysmon-etw-even) (bậc 3, 2021).
- Logpoint dựng Process Tree bằng cách nối ParentProcessGuid của tiến trình con với ProcessGuid của tiến trình cha (ví dụ LogonUI.exe ← winlogon.exe) — [Logpoint Process Tree docs](https://docs.logpoint.com/docs/process-tree/en/latest/index.html) (bậc 1 về hành vi sản phẩm, không rõ ngày).

**Liên kết entity (process ↔ network ↔ file ↔ auth)**
- Event 4624: trường Logon ID (HexInt64) "can help you correlate this event with recent events that might contain the same Logon ID"; Linked Logon ID là "the paired logon session" (giá trị 0x0 nếu không có phiên ghép); Logon GUID dùng để nối với 4769, 4648, 4964 và "might not be captured", khi đó có giá trị toàn số 0; Process ID nối được với "New Process ID" của 4688; các trường IP và workstation có thể trống tùy giao thức (Kerberos thường không có workstation, NTLM không có TCP/IP) — [4624(S) An account was successfully logged on, Microsoft Learn](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4624) (bậc 1, cập nhật 2026-04-27).
- TrustedSec mô tả LogonID sinh ra ở 4624, xuất hiện lại trong 4688 và Sysmon Event 1 cho các process do phiên đó tạo ra; phiên được giới hạn bởi 4624 (bắt đầu) và 4634 (kết thúc) — [TrustedSec: Building a Detection Foundation Part 5](https://trustedsec.com/blog/building-a-detection-foundation-part-5-correlation-in-practice) (bậc 2, không rõ ngày).

**Gom phiên (sessionization) theo khoảng trống thời gian**
- Spark định nghĩa session window như sau: "A session window closes when there's no input received within the gap duration after receiving the latest input". Mỗi event được coi là một phiên riêng, và các phiên giao nhau thì được gộp lại. Từ Spark 3.2, khoảng trống (gap) có thể là biểu thức tính theo từng dòng (dynamic gap) — [Databricks: Native support of session window in Spark Structured Streaming](https://www.databricks.com/blog/2021/10/12/native-support-of-session-window-in-spark-structured-streaming.html) (bậc 1, 2021-10-12); [pyspark session_window docs 3.2.0](https://spark.apache.org/docs/3.2.0/api/python/reference/api/pyspark.sql.functions.session_window.html) (bậc 1).

**Template mining (Drain, Spell, IPLoM, Brain…)**
- Drain: "The time complexity of Drain is O((d+cm)n)", trong đó d là độ sâu cây, c là số nhóm ứng viên ở node lá, m là độ dài message, n là số message. Tác giả coi d, m, c là hằng số nên "the time complexity of Drain is O(n)". Thực nghiệm (Xeon E5-2670v2): "2 min to parse 4m BGL log messages and 7 min to parse 11m HDFS log messages" — [A Directed Acyclic Graph Approach to Online Log Parsing (bản mở rộng của Drain)](https://arxiv.org/abs/1806.04356) (bậc 1, 2018). Paper gốc: He, Zhu, Zheng, Lyu, "Drain: An Online Log Parsing Approach with Fixed Depth Tree", ICWS 2017 — [logparser docs: Drain](https://logparser.readthedocs.io/en/latest/tools/Drain.html) (bậc 1).
- Benchmark Loghub (16 bộ dữ liệu): "Drain and IPLoM have better efficiency, which scales linearly with the log size"; cả hai parse 1 GB log trong vài chục phút. LenMa và MoLFI "cannot even finish parsing 1GB of BGL data or Android data within 6 hours"; LKE không chạy được trên dữ liệu gốc trong thời gian hợp lý. Drain có độ chính xác trung bình cao nhất — [Tools and Benchmarks for Automated Log Parsing (Zhu et al.)](https://arxiv.org/abs/1811.03509) (bậc 1, 2019).
- Loghub-2.0 có 14 bộ dữ liệu, trung bình 3.601.187 dòng và 249,1 template mỗi bộ. Với timeout 12 giờ, chỉ Drain, IPLoM, LFA, LogCluster, LogSig, UniParser và LogPPT chạy xong mọi bộ (paper ghi "six" nhưng liệt kê bảy). FGA trung bình của Drain giảm từ 0,75 trên Loghub-2k xuống khoảng 0,55 trên Loghub-2.0 — [A Large-Scale Evaluation for Log Parsing Techniques: How Far Are We? (ISSTA 2024)](https://arxiv.org/html/2308.10828) (bậc 1, 2024).
- Về tốc độ của Brain, các nguồn lệch nhau. Repo của tác giả ghi khoảng 46 s cho 1 triệu dòng — [gaiusyu/Brain](https://github.com/gaiusyu/Brain) (bậc 1, tự công bố). Paper Tipping đo trên HDFS đầy đủ được Brain khoảng 1016 s, Drain khoảng 129 s, IPLoM khoảng 256 s — [Tipping](https://arxiv.org/html/2408.00645v2) (bậc 1, 2024). Số đo của Tipping lấy từ snippet tìm kiếm, chưa mở bảng gốc để kiểm tra.
- Spell (Du & Li, ICDM 2016; TKDE 2019) là parser trực tuyến dựa trên longest common subsequence (LCS) — [Spell TKDE 2019](https://users.cs.utah.edu/~lifeifei/papers/spell-tkde19.pdf) (bậc 1). Chưa đọc được phần phân tích độ phức tạp.

**Khử trùng lặp, đếm tần suất và sketch**
- Count-Min Sketch (Cormode & Muthukrishnan, LATIN 2004 / J. Algorithms 2005) dùng d hàng hash, mỗi hàng w ô. Không gian là O((1/ε)·log(1/δ)), mỗi lần cập nhật tốn O(log(1/δ)). Tác giả nhấn mạnh cải tiến từ 1/ε² xuống 1/ε về không gian — [countmin-latin2004.pdf](https://dsf.berkeley.edu/cs286/papers/countmin-latin2004.pdf) (bậc 1, 2004); [DIMACS TR 2003-20](https://archive.dimacs.rutgers.edu/archive/TechnicalReports/abstracts/2003/2003-20.html) (bậc 1). Công thức O(·) lấy qua tóm tắt tìm kiếm và bài giảng; chưa đọc nguyên văn định lý.
- HyperLogLog (Flajolet, Fusy, Gandouet, Meunier 2007): sai số chuẩn khoảng 1,04/√m với m thanh ghi, mỗi thanh ghi tối đa 5 bit — [HyperLogLog: the analysis of a near-optimal cardinality estimation algorithm](https://dmtcs.episciences.org/3545/pdf) (bậc 1, 2007). Redis dùng 16.384 thanh ghi, tức 12 KB mỗi key, với sai số chuẩn 0,81% — [antirez.com/news/75](https://antirez.com/news/75) (bậc 1 về Redis, 2014). Chưa kiểm chứng được câu "1.5 kB cho 10^9 phần tử" trong paper.

**Phát hiện burst và change-point**
- PELT (Killick, Fearnhead, Eckley, JASA 2012, vol. 107, tr. 1590–1598) là thuật toán chính xác cho bài toán tối thiểu hóa hàm chi phí có phạt. Chi phí của nó "under mild conditions, linear in the number of observations", trong khi các phương pháp chính xác trước đó tốn bậc hai hoặc bậc ba. Điều kiện ở đây là số change-point tăng tuyến tính theo n; trường hợp xấu nhất PELT vẫn là O(n²). Tác giả so với Binary Segmentation (heuristic) và thấy PELT cho phân đoạn chính xác hơn — [Optimal detection of changepoints with a linear computational cost](https://arxiv.org/abs/1101.1438v3) (bậc 1, 2012); [Lancaster eprint](https://eprints.lancs.ac.uk/id/eprint/60321) (bậc 1).
- Kleinberg (KDD 2002; DMKD 2003) mô hình hóa luồng event bằng một automaton vô hạn trạng thái, trong đó burst là các chuyển trạng thái. Thuật toán "highly efficient" và cho một biểu diễn lồng nhau, có thứ bậc, của các burst — [Bursty and Hierarchical Structure in Streams](https://www.cs.cornell.edu/home/kleinber/bhs.pdf) (bậc 1, 2002). Chi phí tăng một mức trạng thái tỉ lệ với γ, còn giảm mức thì miễn phí; bài giảng Cornell mô tả cách giải bằng Viterbi để tối thiểu chi phí — [CRAN bursts::kleinberg](https://rdrr.io/cran/bursts/man/kleinberg.html) (bậc 1, docs); [Cornell INFO 2950 lec28](https://courses.cit.cornell.edu/info2950_2012sp/lec28.pdf) (bậc 2, 2012). Package PyPI `burst_detection` hiện thực bản 2 trạng thái (baseline hoặc bursty) — [pypi burst_detection](https://pypi.org/project/burst_detection/) (bậc 1, docs).

**Phân cụm ở quy mô lớn (MinHash/LSH)**
- Với LSH banding (b band, mỗi band r hàng), hai tập có độ tương tự Jaccard s trở thành ứng viên với xác suất 1 − (1 − s^r)^b. Ngưỡng của đường cong chữ S nằm ở khoảng (1/b)^(1/r); ví dụ b = 16, r = 4 cho ngưỡng khoảng 0,5 — [Narasimhan, FIU lecture UnitX-Similarity](https://users.cs.fiu.edu/~giri/teach/5768/F18/lecs/UnitX-Similarity.pdf) (bậc 2, 2018). Thư viện datasketch chọn 25×5 cho ngưỡng 0,5 và 9×13 cho ngưỡng 0,8 — [mojoauth LSH in Python](https://mojoauth.com/security-guides/lsh-in-python.md) (bậc 3, chỉ dùng làm manh mối). Không truy cập được MMDS chương 3 (bị lỗi kết nối).

**Episode mining và sequential pattern mining: bẫy chi phí**
- WINEPI (Mannila, Toivonen, Verkamo 1995/1997) trượt cửa sổ cố định và tìm theo từng mức (breadth-first). MINEPI đếm các cửa sổ tối thiểu; Tatti sau này chỉ ra định nghĩa của MINEPI có lỗi — [Fournier-Viger: Key papers about episode mining](https://data-mining.philippe-fournier-viger.com/key-papers-about-episode-mining/) (bậc 2, chuyên gia SPMF); [Mining Closed Strict Episodes](https://arxiv.org/pdf/1904.09231) (bậc 1).
- "millions of episodes may be found for minsup = 2" trên một số chuỗi. Người dùng "typically dont have time to look at millions of episodes", và việc chỉnh minsup phải làm "by trial and error". Hướng khắc phục là top-k episode mining — [Fournier-Viger: An Introduction to Episode Mining](https://data-mining.philippe-fournier-viger.com/introduction-to-episode-mining/) (bậc 2, không rõ ngày).

### Nhận định
- **Bảng độ phức tạp đề xuất cho pipeline trước LLM** (suy luận từ các nguồn trên; hằng số ẩn phụ thuộc k):
  1. Đọc Parquet chỉ các cột cần (projection pushdown): O(n·k).
  2. Sắp xếp theo (device, time): O(n log n). Ngoại suy từ số đo DuckDB (1 tỷ số ngẫu nhiên hết khoảng 6,5 s), 500k dòng chỉ mất cỡ mili-giây đến dưới 1 giây; bước này không phải nút cổ chai.
  3. Dựng cây process: một hash map `process.uid` (ProcessGuid) → node, rồi nối `parent_process.uid`. Kỳ vọng O(n).
     - Khi chỉ có PID, dùng khóa ghép (pid, created_time). Nếu event con chỉ có pid, với mỗi pid giữ danh sách thời điểm start đã sắp, rồi tìm nhị phân "process có pid đó, start gần nhất trước t". Tổng chi phí O(n log n).
     - Không dựa vào chuỗi `lineage` hay `parent_process` lồng nhau, vì OCSF khuyên chỉ điền một cấp.
  4. Liên kết entity bằng hash join trên process uid / logon_uid (OCSF `session.uid`, LogonId). Kỳ vọng O(n).
  5. Gom phiên theo khoảng trống: sau khi đã sắp, một lượt quét so `t[i] − t[i−1] > gap` (window function LAG), chi phí O(n). Gom theo entity (logon session, cây process của trình duyệt, app đang focus) là group-by trên khóa entity, rồi lại gom theo khoảng trống trong từng nhóm; tổng vẫn O(n log n).
  6. Chuẩn hóa field: dùng Drain (O(n)) chỉ cho các field văn bản tự do (cmd_line, đường dẫn, URL). Phần còn lại của OCSF đã có cấu trúc, nên "template" thực chất là một tuple phân loại (class_uid, activity_id, image name, tên miền eTLD+1, mẫu đường dẫn đã được che bằng regex). Hash tuple đó có chi phí O(n·k).
  7. Đếm: với 500k event, dùng hash map chính xác (O(n), bộ nhớ O(U)). Count-Min Sketch và HyperLogLog chỉ cần khi gộp nhiều batch hoặc cả fleet, chẳng hạn đếm "đã thấy chữ ký này ở bao nhiêu máy" bằng HLL vài KB mỗi chữ ký.
  8. Burst, ví dụ chuỗi 4625 thất bại: cửa sổ trượt hai con trỏ trên chuỗi đã sắp, chi phí O(n). Kleinberg (Viterbi) tốn O(n·số trạng thái); với bản 2 trạng thái là O(n). Chỉ dùng PELT trên chuỗi đếm theo bucket (ví dụ số event mỗi phút), khi đó độ dài chuỗi là số bucket chứ không phải n.
  9. Phân cụm phiên: MinHash trên tập chữ ký của phiên, O(S·h) với h hàm hash; LSH banding tránh phải so O(S²) cặp. Đơn giản hơn nữa là "signature hashing": hash có thứ tự của chuỗi template đã nén lặp (run-length), rồi group by. Cách này O(n), đủ cho mục tiêu gom các phiên lặp lại y hệt.
  10. Cấu trúc tóm tắt nhiều mức: các bucket thời gian lồng nhau (phút → giờ → ngày), dựng bằng group-by tăng dần, chi phí O(n). Cây đoạn (segment tree) dựng O(B) và truy vấn O(log B) trên B bucket. Đây là kiến thức giáo khoa; chưa tìm nguồn riêng cho ứng dụng này.
- **Nên tránh** WINEPI, MINEPI và sequential pattern mining tổng quát (PrefixSpan…) ở dạng không giới hạn: số mẫu bùng nổ khi minsup thấp. Nếu cần, giới hạn bằng n-gram có độ dài cố định L trên chuỗi template trong từng phiên, chi phí O(n·L), hoặc dùng top-k.
- Kết quả Loghub-2.0 (FGA của Drain chỉ khoảng 0,55 khi số template lớn) gợi ý: với dữ liệu OCSF đã có cấu trúc, không nên đẩy cả event thành chuỗi văn bản rồi chạy Drain. Hash trực tiếp trên field phân loại vừa chính xác hơn vừa rẻ hơn.

### Khoảng trống
- Chưa đọc nguyên văn phân tích độ phức tạp của Spell (LCS) và IPLoM. Các file PDF tải về không trích xuất được text, vì môi trường không có pdftotext.
- Chưa xác nhận được bằng nguồn gốc số trạng thái cần thiết trong mô hình Kleinberg (đoán là cỡ log của khoảng thời gian), nên chưa có chặn trên chính xác dạng O(n log n).
- Không tìm thấy bài kỹ thuật công khai (engineering blog) của vendor EDR mô tả cụ thể thuật toán dựng cây process ở quy mô lớn; Logpoint chỉ mô tả ở mức tính năng.
- Chưa có số liệu benchmark của streaming clustering (BIRCH, CluStream) trên log; mục này không được tìm sâu.

---

## Câu phụ 4b: Làm số lời gọi LLM và số token tăng chậm hơn n

### Kết luận ngắn
Cách đã có bằng chứng là: gom thành chữ ký (template, signature), cache nhãn theo chữ ký và chỉ gọi LLM khi cache trượt (cache miss). Khi đó số lời gọi tỉ lệ với số chữ ký khác nhau U chứ không tỉ lệ với n. LILAC đo được khoảng 280 lời gọi cho 3,6 triệu dòng log. Mức chắc chắn: **cao** cho nguyên lý và số liệu của LILAC; **thấp đến trung bình** cho các con số ước tính với 500k event OCSF, vì đó là suy luận của agent.

### Phát hiện có nguồn
- LILAC (FSE 2024) dùng "adaptive parsing cache" và luôn tra cache trước, nhờ đó "can avoid duplicated queries to LLMs". Trung bình LILAC gọi LLM **279,7 lần mỗi bộ dữ liệu**, trong khi mỗi bộ có trung bình 249 template thật và khoảng 3,6 triệu dòng. Phần chênh so với 249 đến từ các template sai làm cache match thất bại. Theo paper, các parser LLM theo kiểu từng dòng "necessitate over 3.6 million queries" — [LILAC: Log Parsing using LLMs with Adaptive Parsing Cache](https://arxiv.org/html/2310.01796) (bậc 1, 2024).
- Thời gian xử lý của LILAC là 569,6 s cho trung bình 3,6 triệu dòng, so với 425,4 s của Drain (chậm hơn khoảng 1,34 lần). Trong đó thao tác cache chiếm 376,5 s (66,1%) và gọi LLM chiếm 193,1 s (33,9%). Cache tra khớp bằng "only one single traversal from the root to the leaf node" — cùng nguồn (bậc 1, 2024).
- So sánh tốc độ: LibreLog (parser LLM) cần khoảng 2,5 giờ trên một bộ dữ liệu lớn, tức khoảng 7,9 lần Drain — [Log Parsing using LLMs with Self-Generated In-Context Learning and Self-Correction](https://arxiv.org/pdf/2406.03376) (bậc 1, 2024). Số liệu lấy qua snippet tìm kiếm, chưa kiểm tra trong bảng.

### Nhận định
- **Thiết kế gọi LLM theo bậc** (suy luận):
  1. *Mức chữ ký event*: không gọi LLM. Ánh xạ bằng luật hoặc bảng tra (ví dụ chrome.exe kèm DNS tới domain X thì là "lướt web").
  2. *Mức chữ ký phiên*: chữ ký phiên = hash của (entity chính, multiset top-N chữ ký event, đã bỏ tham số như thời gian và PID). Gọi LLM một lần cho mỗi chữ ký phiên **mới**, và lưu nhãn vào một cache bền (SQLite, DuckDB table) để dùng lại cho các batch sau, theo đúng mô hình LILAC.
  3. *Mức ngày*: một lời gọi mỗi ngày, input là danh sách phân đoạn đã có nhãn (thời gian bắt đầu và kết thúc, nhãn, số đếm, ID bằng chứng), để LLM viết tường thuật. Token đầu vào tỉ lệ với số phân đoạn trong ngày, không tỉ lệ với số event.
  4. *Ngân sách token mỗi ngày*: nếu số phân đoạn vượt ngân sách, gộp các phân đoạn liền kề cùng nhãn và cắt phần đuôi có tần suất thấp, hoặc nâng mức bucket (ví dụ từ 15 phút lên 1 giờ).
- **Ước tính cho 500k event** (giả định: 7 ngày, khoảng 70k event/ngày, một thiết bị hoặc một người dùng; mọi con số là ước lượng của agent, chưa đo):
  - Gửi thẳng: một event OCSF dạng JSON với hàng trăm field dễ dài 1–3 KB, tức khoảng 300–1000 token. 500k event sẽ thành khoảng **150–500 triệu token**, vượt xa context window, nên phải có map-reduce với hàng nghìn lời gọi.
  - Sau bước gom: giả định khoảng 100–300 phân đoạn/ngày và khoảng 50–200 chữ ký phiên khác nhau trong lần chạy đầu. Con số này cùng bậc với 249 template/bộ của Loghub-2.0, dù bản chất khác. Khi đó:
    - Gán nhãn: 50–200 lời gọi × khoảng 1–2k token = **50k–400k token**.
    - Tường thuật: 7 lời gọi × khoảng 3–10k token = **20k–70k token**.
    - Tổng cỡ **0,1–0,5 triệu token**, tức giảm khoảng 3 bậc độ lớn.
  - Ở các batch sau, phần gán nhãn chỉ còn các chữ ký mới (cache trượt), nên chi phí tiến gần mức "một lời gọi mỗi ngày".
- Số lời gọi tăng theo U chứ không theo n. Với hành vi người dùng lặp lại, U thường tăng chậm, kiểu dưới tuyến tính (giống đường cong số template mới giảm dần khi parse thêm log). Tuy vậy, chưa có nguồn đo đường cong này cho telemetry endpoint. Cần đo thực tế bằng HLL hoặc đếm chính xác số chữ ký mới mỗi ngày.

### Khoảng trống
- Không tìm thấy nghiên cứu nào đo số chữ ký phiên khác nhau mỗi ngày trên telemetry Windows thật; các ước tính ở trên chưa được kiểm chứng.
- Chưa đối chiếu giá token cụ thể của từng nhà cung cấp; cố ý bỏ qua vì giá thay đổi thường xuyên. Writer nên ghi chi phí ở dạng số token.

---

## Câu phụ 4c: Kỹ thuật thực tế: xử lý dạng cột trên OCSF Parquet

### Kết luận ngắn
OCSF trên Amazon Security Lake được lưu dưới dạng Parquet, phân vùng theo vùng, tài khoản và `eventDay`. Phân vùng theo ngày khớp tự nhiên với yêu cầu chia output theo ngày, và định dạng cột cho phép chỉ đọc vài chục trên khoảng 500 field. Với 500k dòng, DuckDB hoặc Polars xử lý trong vài giây trên laptop. Mức chắc chắn: **cao** cho định dạng (docs AWS); **trung bình** cho số throughput (benchmark của bên thứ ba, ngoại suy về quy mô).

### Phát hiện có nguồn
- Security Lake yêu cầu object của custom source "partitioned by region, AWS account, eventDay", với tiền tố `region=/accountId=/eventDay=yyyyMMdd/`. Nó hỗ trợ Parquet 1.x và 2.x, data page tối đa 1 MB (chưa nén), row group tối đa 256 MB (đã nén), ưu tiên nén zstandard. File gửi lên theo bước từ 5 phút đến 1 ngày event. Custom source phải chuyển sang OCSF trước khi gửi — [Collecting data from custom sources in Security Lake, AWS docs](https://docs.aws.amazon.com/security-lake/latest/userguide/custom-sources.html) (bậc 1, không rõ ngày cập nhật). Bản tiếng Pháp ghi custom source hỗ trợ OCSF 1.3 trở xuống — [bản fr_fr](https://docs.aws.amazon.com/fr_fr/security-lake/latest/userguide/custom-sources.html) (bậc 1, chưa đối chiếu với bản tiếng Anh).
- Exporter của bên thứ ba (Praxis/Netenrich) gom bản ghi theo custom source, event day và OCSF `class_uid`, rồi ghi Parquet nén ZSTD cho từng nhóm — [Praxis AWS Security Lake destination](https://praxis.netenrich.com/docs/praxis/Destinations/awssecuritylake) (bậc 1 về sản phẩm của họ).
- Throughput sort của DuckDB (M1 Max, 10 thread): 1 tỷ số ngẫu nhiên hết 6,493 s; 60 triệu dòng × 15 cột hết 1,52 s — [DuckDB: Redesigning DuckDB's Sort, Again](https://duckdb.org/2025/09/24/sorting-again) (bậc 1, 2025-09-24).
- So sánh DuckDB và Polars: One Billion Row Challenge trên Apple M1 8 GB cho DuckDB khoảng 14,98 s, Polars khoảng 33,86 s, Pandas khoảng 263 s — [wikidocs.net/237670](https://wikidocs.net/237670) (bậc 3, không rõ ngày; chỉ là manh mối). Một benchmark 10 triệu dòng năm 2026 cho thấy hai engine ngang nhau trên group-by (mỗi bên nhanh hơn ở một số truy vấn) — [uvik.net](https://uvik.net/blog/polars-vs-pandas/) (bậc 3, vendor). Benchmark độc lập có phương pháp công khai là H2O db-benchmark, hiện do DuckDB Labs duy trì, chưa mở được.

### Nhận định
- Bố cục đề xuất (suy luận):
  - Đọc Parquet theo `eventDay` và `class_uid`, chỉ chiếu các cột cần: `time`, `class_uid`, `activity_id`, `status_id`, `actor.process.uid`, `process.uid`, `process.parent_process.uid`, `process.file.name`, `process.cmd_line`, `actor.user.uid`, `actor.session.uid`, `dst_endpoint.hostname`, `query.hostname`, `file.path`, `url.hostname`…
  - Toàn bộ bước 1–9 ở mục 4a viết được bằng SQL của DuckDB: window function LAG để gom phiên, hash join, GROUP BY, và hàm `approx_count_distinct` (HLL) có sẵn.
  - Chỉ cần mã Python hoặc Rust cho Drain (đã có thư viện drain3) và cho lời gọi LLM.
- Chia theo ngày: dùng `eventDay` nếu cần khớp UTC; nếu cần "ngày" theo giờ địa phương của người dùng thì tính lại từ `time` cộng `timezone_offset`. Khi đó phiên vắt qua nửa đêm phải được cắt hoặc gán cho ngày bắt đầu. Đây là quy ước cần chốt với chủ repo.
- Với n = 500k, nút cổ chai thực tế sẽ là độ trễ và chi phí của LLM, không phải phần tính toán cột, vốn chỉ mất vài giây (ngoại suy từ số liệu DuckDB, chưa đo trên OCSF thật).

### Khoảng trống
- Chưa có benchmark công khai nào đo DuckDB hoặc Polars trực tiếp trên OCSF Parquet thật (schema lồng sâu, khoảng 500 field). Chi phí unnest các struct lồng nhau chưa được định lượng.
- Chưa mở được kết quả H2O db-benchmark hiện tại; các số liệu Polars và DuckDB ở trên là nguồn yếu.

---

## Truy vấn đã chạy
- Drain online log parsing fixed depth tree He 2017 complexity (standard)
- PELT Killick 2012 optimal detection changepoints linear computational cost (standard)
- Sysmon ProcessGuid LogonGuid event ID 1 process tree (standard)
- loghub-2.0 log parsing benchmark efficiency Drain Brain parsing time (standard)
- Drain log parser time complexity "O((d+cm)n)" (standard)
- Kleinberg "Bursty and hierarchical structure in streams" two-state automaton algorithm (standard)
- Microsoft Learn Sysmon ProcessGuid "process GUID" PID reuse correlation (standard)
- Brain log parser bidirectional parallel tree Yu 2023 efficiency (standard)
- Amazon Security Lake OCSF Apache Parquet storage format partition (standard)
- Kleinberg burst detection Viterbi complexity number of states log n (standard)
- Cormode Muthukrishnan count-min sketch space O(1/epsilon log 1/delta) update time (standard)
- HyperLogLog Flajolet 2007 standard error 1.04/sqrt(m) 1.5 kilobytes cardinalities 10^9 (standard)
- WINEPI MINEPI frequent episodes event sequences Mannila exponential candidates (standard)
- DuckDB Polars benchmark group by 1 billion rows seconds 2025 (standard)
- LILAC log parsing LLM adaptive parsing cache number of LLM queries reduced (standard)
- DuckDB external sorting larger than memory blog radix sort performance (standard)
- Windows event 4624 Logon ID correlate 4634 4688 logon session Microsoft Learn (standard)
- Spark session_window gap duration sessionization dynamic gap (standard)
- Spell streaming log parser longest common subsequence Du Li 2016 complexity prefix tree (standard)
- MinHash LSH banding b bands r rows threshold (1/b)^(1/r) Jaccard probability (standard)
