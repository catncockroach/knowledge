# Ứng dụng LLM vào phân tích FP và đề xuất tuning rule, kèm rủi ro/phản biện

Ghi chú về mức kiểm chứng: "đã đọc abstract/HTML" nghĩa là đã mở trang arXiv bằng WebFetch. "Chỉ snippet" nghĩa là con số lấy từ kết quả search, chưa mở bài gốc, writer nên dùng thận trọng hoặc chỉ nêu tên.

## 1. Nghiên cứu học thuật 2023–2026

### Kết luận ngắn
Nghiên cứu dày ở hai mảng: (a) **triage alert / phân loại TP-FP** và (b) **sinh rule mới** (Sigma, Suricata/Snort, MQL) từ CTI hoặc mẫu tấn công. Mảng **sửa/tuning rule có sẵn để giảm FP** (đúng task của chủ repo) gần như chưa có paper chuyên biệt; gần nhất là RuleGenie (tối ưu tập rule SIEM), ADÉ của Sublime (sinh rule + retro-hunt đo TP/FP), các vòng "repair" trong GRIDAI/RulePilot, và REFINE (học "skill" triage với ràng buộc recall). Mức chắc chắn: **trung bình–cao** về bức tranh chung; **thấp** về việc "không có paper nào" vì nhiều preprint mới 2026 chưa đọc hết.

### Phát hiện có nguồn

**Triage / phân loại TP-FP**
- REFINE (Baidu + ĐH Hoa Đông, 2026-09): agent triage học một "skill" có cấu trúc (luật phán đoán, chuỗi bằng chứng, giao thức dùng tool) từ quyết định dismiss/escalate hằng ngày của analyst tại một SOC công nghiệp thật. Dữ liệu 4 kịch bản (Phishing, Host-Process, NTLM-Hash, PROC2_HEYE), mỗi kịch bản 100 alert để "tiến hóa" + 150 alert test, tổng 1.000 alert. **Recall = 1.0 là ràng buộc cứng**; chọn mẫu ưu tiên threat bị bỏ sót > FP > ca đúng; có cổng recall theo batch và toàn cục; sau deploy tái huấn luyện khi phát hiện threat bị auto-close sai (safety trigger) hoặc accuracy giảm có ý nghĩa thống kê. Kết quả: NTLM-Hash accuracy từ 0,217 (LLM trực tiếp) lên 0,907 trên tập tiến hóa; trên tập test recall giữ 1.0 ở 3/4 kịch bản, Host-Process chỉ 0,807 (baseline GEPA/ACE 0,49–0,58); NTLM-Hash test accuracy rơi còn 0,537 do nguồn process lành tính chưa thấy. Hạn chế tự nêu: 1 tổ chức, 4 kịch bản, nhãn là "phán đoán vận hành" chứ không phải ground truth tuyệt đối, chỉ dùng model open-weight vì quy định privacy cấm API đóng, chưa xét tấn công né tránh, safety trigger chỉ kích hoạt **sau khi** đã có threat bị bỏ sót — [REFINE: A Resilient Evolution Framework for Intelligent Enterprise Alert Triage in SOCs](https://arxiv.org/html/2609.32516) (bậc 1, preprint, 2026-09-26; đã đọc HTML)
- SIABENCH ("Before You Hand Over the Wheel", 2026-03): benchmark agentic cho phân tích sự cố, 25 kịch bản phân tích sâu + 135 kịch bản triage alert (gồm "false-alert detection"), đánh giá 11 LLM. Abstract không nêu số — [Before You Hand Over the Wheel: Evaluating LLMs for Security Incident Analysis](https://arxiv.org/abs/2603.06422) (bậc 1, preprint, 2026-03-06; đã đọc abstract). Snippet search nói GPT-5 gần như tuyệt đối ở phát hiện FP trên một dataset, GPT-4o-mini thiên về coi alert là threat thật (**chỉ snippet**).
- CORTEX (multi-agent triage): snippet nói FP rate giảm từ 24,9% xuống 14,2% so với single-agent tốt nhất — [ResearchGate](https://www.researchgate.net/publication/396094185_CORTEX_Collaborative_LLM_Agents_for_High-Stakes_Alert_Triage) (**chỉ snippet**, chưa xác minh).
- "Information-Dense Reasoning for Efficient and Auditable Security Alert Triage": snippet nêu độ trễ triage bằng LLM khoảng 3–5 giây/alert và yêu cầu auditability theo NIST SP 800-61r3 — [arXiv 2512.08169](https://arxiv.org/pdf/2512.08169) (**chỉ snippet**).
- "Cybersecurity Detection Classification with Reasoning-enabled Language Models": huấn luyện model chain-of-thought trên detection endpoint Windows đã gắn nhãn người để phán đoán threat thật — [arXiv 2607.28460](https://arxiv.org/html/2607.28460v1) (**chỉ snippet**).
- Survey 2026 về sàng lọc alert bằng AI: không dataset công khai nào trong danh sách có ground truth disposition đầy đủ của analyst, dẫn tới con số hiệu năng công bố bị thổi phồng so với production — [AI-Driven Security Alert Screening and Alert Fatigue Mitigation in SOCs: A Survey](https://arxiv.org/pdf/2605.08316) (**chỉ snippet**, bậc 1).

**Sinh / sửa detection rule**
- ADÉ của Sublime Security (CAMLIS 2025): agent sinh rule MQL cho email, tự kiểm cú pháp, test trên mẫu gốc, **retro-hunt trên email lịch sử**, subagent chấm TP rate/FP rate/độ bền rồi lặp lại. Đánh giá holdout: 11 rule người viết bị giấu, ADÉ chỉ nhận 1 email TP cho mỗi rule; tập ~45.000 email trong 14 ngày gán nhãn tay. Kết quả: rule ADÉ **hẹp hơn** (ít TP hơn, thường ít FP hơn). Ví dụ "Callback PDF": người 756 TP/9 FP (score 0,982) vs ADÉ 31 TP/0 FP (0,871); "BEC Reply-to mismatch": người 1557/1 vs ADÉ 35/0; "Coinbase impersonation": ADÉ 116 TP/16 FP vs người 33/2. Chi phí $1,51–$5,13/rule, pass@k từ 1–3. Metric: detection accuracy = ½(precision + unique-TP precision); economic cost (cost-of-pass); robustness (match trực tiếp IP/domain/hash bị coi là "brittle", hành vi/fuzzy là "robust"). Hạn chế: không đo false negative, mỗi rule chỉ 1 TP, chưa test đối kháng — [Evaluating LLM Generated Detection Rules in Cybersecurity](https://arxiv.org/html/2509.16749) (bậc 1, 2025-09-20; đã đọc HTML)
- RuleGenie (ĐH Ben-Gurion, 2025-05): embedding transformer của rule SIEM + top-k tương tự, LLM phân tích độ trùng, coverage, metric hiệu năng để đề xuất tinh gọn tập rule; thử trên rule Splunk, Sigma, AQL thật. Abstract tuyên bố phát hiện rule thừa và giảm FP nhưng **không có số** — [RuleGenie: SIEM Detection Rule Set Optimization](https://arxiv.org/abs/2505.06701) (bậc 1, 2025-05-10; đã đọc abstract)
- "Beyond the Syntax" (2026-07): user study 10 chuyên gia về rule NIDS do LLM sinh. Model ≥70B sinh cú pháp hợp lệ ổn định, model ≤4B gần như vô dụng; chuyên gia đánh giá rule "chỉ triển khai được một phần" do **thiếu tính đặc hiệu** ("syntax-semantics paradox"); **logic hallucination 12%**; SUS 67; chuyên gia coi LLM là công cụ nháp/kiểm tra, không phải tự động — [Beyond the Syntax: Do Security Experts Trust LLMs for NIDS Rule Engineering?](https://arxiv.org/abs/2607.05916) (bậc 1, 2026-07-07; đã đọc abstract)
- GRIDAI (2025-10): multi-agent sinh và **sửa** rule IDS; prompt ép rule hẹp, có bước replay PCAP để kiểm — [arXiv 2510.13257](https://arxiv.org/pdf/2510.13257) (**chỉ snippet**).
- RulePilot / "Synthesizing Deployable Suricata Rules from Raw Network Traffic" (Virginia Tech): loại flow lành tính trước khi sinh, sửa rule nếu bắn trên corpus lành tính; đánh giá trên 1.296 PCAP malware và 1.172 PCAP lành tính — [VTechWorks](https://vtechworks.lib.vt.edu/items/1fd5206d-c461-414f-a3d7-a7b18c25cd3c) (**chỉ snippet**). Lưu ý: có một RulePilot khác trên arXiv 2511.12224 dùng BLEU-4/METEOR + LLM-as-judge 6 chiều — [arXiv 2511.12224](https://arxiv.org/pdf/2511.12224) (**chỉ snippet**).
- Verification-guided synthesis cho rule IDS (2026-08): snippet nêu FP 0,0% với detection 81,5% (so với RuleXploit 5,3% FP, GRIDAI 0,5%), nhưng detection rate đo trên chính trace dùng để sinh rule → đo khả năng sinh, không đo tổng quát hóa — [arXiv 2608.22889](https://arxiv.org/pdf/2608.22889) (**chỉ snippet**).
- Sigma: SIGMERGE (USENIX Security 2026, sinh Sigma từ báo cáo threat, 23 metric, 16 baseline, 13 LLM, tuyên bố tăng completeness 33,17% so với DeepSeek-V3) — [USENIX prepub](https://www.usenix.org/system/files/conference/usenixsecurity26/sec26_prepub_cai.pdf); SigmaForge (AINA 2026, RAG + LLM-as-judge dạng DAG, Cohen's kappa 0,66 với người, Qwen3-Coder-30B on-prem gần chất lượng model cloud) — [Springer](https://link.springer.com/chapter/10.1007/978-3-032-23335-6_4); AUTOSIGMA — [arXiv 2608.19011](https://arxiv.org/pdf/2608.19011); Sigma-Hunter (model chuyên biệt huấn luyện trên 3.635 rule Sigma) — [arXiv 2610.09007](https://arxiv.org/html/2610.09007); LLMCloudHunter (121/122 rule ứng viên compile được và chuyển sang Splunk) — [arXiv 2407.05194](https://arxiv.org/html/2407.05194v1) (tất cả **chỉ snippet**).
- Lĩnh vực lân cận (SAST) cho bài học về TP retention: "Sifting the Noise" – agent LLM lọc FP SAST trên OWASP Benchmark gắn nhầm 314 lỗ hổng thật thành FP, TP retention 77,7% (miss 22,25%) — [arXiv 2601.22952](https://arxiv.org/html/2601.22952v2); LLM4PFA lọc 72–96% FP của static analyzer, bỏ sót 3/45 TP — [arXiv 2506.10322](https://arxiv.org/pdf/2506.10322) (cả hai **chỉ snippet**).

**Nghiên cứu định tính về practitioner**
- Phỏng vấn bán cấu trúc 25 practitioner SOC đã dùng LLM (2026-08, v2 2026-10): 15 use case trong 6 nhóm; LLM được đánh giá cao cho việc lặp lại, mức thấp (viết báo cáo); "practitioners rate high-impact tasks such as incident analysis as not yet feasible" vì thiếu chiều sâu kỹ thuật, thiếu nhận biết ngữ cảnh, thiếu kiến thức riêng của tổ chức; rủi ro chính là **over-reliance**; vẫn muốn áp dụng vì áp lực cạnh tranh — [From Chasing Ghosts to Missed Attacks](https://arxiv.org/abs/2608.00672) (bậc 1, 2026-08-01; đã đọc abstract)

### Nhận định
- Mẫu chung của các paper tốt: **LLM sinh → validator tất định (cú pháp, replay dữ liệu lành tính và độc hại) → lặp sửa**. Không paper nào để LLM tự quyết mà không có bước đo trên dữ liệu.
- ADÉ cho thấy xu hướng tự nhiên của LLM khi bị tối ưu theo FP là **viết rule quá hẹp** (mất TP). Đây đúng là rủi ro over-tuning khi dùng LLM để tuning: muốn ít FP thì cách dễ nhất là siết đến mức không còn bắt được gì.
- REFINE là thiết kế gần với task "học từ quyết định FP của analyst" nhất và đặt **recall làm ràng buộc cứng** — có thể mượn nguyên tắc này cho tuning rule: đề xuất nào làm rơi bất kỳ TP lịch sử nào thì loại.

### Khoảng trống
- Chưa tìm thấy paper nào lấy đầu vào là **tập alert/case FP kèm ghi chú analyst + rule hiện tại** và xuất ra **diff rule/exclusion** rồi đo FP giảm + TP giữ lại trên dữ liệu SIEM thật. Truy vấn đã thử: "LLM detection rule tuning reduce false positives", "LLM agent refine detection rule false positives backtest historical true positives arXiv".
- Chưa đọc full paper RuleGenie, SIABENCH, CORTEX nên thiếu số liệu cụ thể.

## 2. Sản phẩm thương mại và triển khai thực tế

### Kết luận ngắn
Đa số sản phẩm "AI SOC" làm **triage** (phán TP/FP, tóm tắt, đề xuất hành động), không sửa rule. Một số có tính năng gần tuning: Google SecOps (Gemini thêm exclusion vào YARA-L theo yêu cầu; Detection Engineering Agent sinh rule lấp **gap coverage**, không tuning FP), Dropzone và Prophet (tuyên bố đề xuất sửa rule từ FP lặp lại — marketing, chưa có kiểm chứng độc lập). Số liệu có kiểm chứng tốt nhất là RCT của Microsoft về phishing triage. Mức chắc chắn: **trung bình** (tài liệu vendor thay đổi nhanh, nhiều claim chỉ là marketing).

### Phát hiện có nguồn

**Google SecOps (Gemini)**
- Detection Engineering Agent (public preview, bài ngày 2026-09-01): trích hành vi tấn công từ báo cáo threat intel → sinh sự kiện UDM giả lập → chạy qua pipeline ingest thật (telemetry giả lập tách khỏi view/dashboard/case của analyst) → xem Curated Detections và rule YARA-L tự viết nào bắn → nếu có gap thì nháp rule YARA-L mới. Chạy end-to-end 15–30 phút; mô tả TTP chi tiết cho kết quả tốt hơn IoC đơn lẻ như IP; cần parser UDM cho log source liên quan; dành cho Enterprise/Enterprise Plus; cần Remote MCP Server. **Bài không nói agent tuning rule có sẵn để giảm FP và không nhắc bước phê duyệt** — [Announcing Public Preview of the Google SecOps Detection Engineering Agent](https://security.googlecloudcommunity.com/community-blog-42/announcing-public-preview-of-the-google-security-operations-detection-engineering-agent-8178) (bậc 1, vendor, 2026-09-01; đã đọc)
- Hướng dẫn cộng đồng Google (theo snippet): cho rule mới chạy "silent" (alerting tắt) 7–14 ngày, khi FP gần 0 mới bật; nếu rule bắn vào hành vi được phép thì đưa ngữ cảnh vào pane Gemini để Gemini **thêm logic exclusion** — [Tuesday's Tip: Tuning Detection Rules with Exclusions and Data Tables](https://security.googlecloudcommunity.com/tuesday-s-tip-of-the-week-93/tuesday-s-tip-of-the-week-signal-not-noise-tuning-detection-rules-with-exclusions-and-data-tables-8179) và adoption guide Gemini (**chỉ snippet**).
- PoC của David French (Google, 2025-05-12): tuning rule bằng Gemini + MCP server cho SecOps, GTI, SCC, GitHub, dùng Cline, rule quản lý qua pipeline **detection-as-code trên GitHub**. Chỉ là thử nghiệm cá nhân, các bước nằm trong video — [Tuning Rules in Google SecOps Using Gemini and MCP Servers](https://security.googlecloudcommunity.com/google-security-operations-2/tuning-rules-in-google-security-operations-using-gemini-and-mcp-servers-824) (bậc 2, 2025-05-12; đã đọc)
- Một bài Medium bên thứ ba mô tả agent `detection_engineer` tự kích hoạt khi đóng case và bắt buộc phê duyệt khi deploy rule mới hoặc suppress rule — [Building a Curated Detections Agent Skill / A Gemini CLI powered Agentic SOC](https://medium.com/@thatsiemguy/a-gemini-cli-powered-agentic-soc-ce9b8ce98c5f) (bậc 3, **chỉ snippet**, không phải tài liệu chính thức).

**Microsoft Security Copilot**
- RCT Phishing Triage Agent (James Bono và cộng sự, Microsoft, arXiv 2511.13860, 2025-11): 167 analyst bên ngoài chia 3 nhóm (Control 52, Aware 56, Blind 59); corpus 93 email do nhân viên Microsoft báo cáo (11 độc, 82 lành); mỗi analyst xử lý queue 25 email gồm 1 synthetic FN và 1 synthetic FP (phải tự tạo vì agent không sai trên corpus). Kết quả: 6,5× TP/analyst-phút trên corpus (3,1× ở kịch bản bi quan 20% độc và agent precision/recall 80%); 79–84% lợi ích đến từ **sắp xếp queue/resolve-benign**, chỉ 13–17% từ verdict + giải thích. F1 Control 0,53 → Aware 0,93 (+77%); precision 0,42 → 1,00. Ở kịch bản phản thực tế về độ chính xác: F1 +48%, recall 0,79 → 0,70 (không ý nghĩa thống kê). **Quan trọng:** nhóm Aware đồng ý với verdict "lành tính" của agent nhiều hơn hẳn — bỏ sót synthetic FN 46% vs 17% ở Control (+29 điểm, p=0,001). Hạn chế: FP/FN là giả lập, corpus nội bộ Microsoft, analyst không được render HTML hay mở URL — [Randomized Controlled Trials for Phishing Triage Agent](https://arxiv.org/html/2511.13860v1) (bậc 1, nhưng do vendor tự làm, 2025-10/11; đã đọc HTML)
- Phishing Triage Agent đã được mở rộng thành Security Alert Triage Agent trong Defender (preview) — [Microsoft Learn](https://learn.microsoft.com/en-us/defender-xdr/security-alert-triage-agent) (**chỉ snippet**).
- Microsoft Sentinel "SOC optimization": khuyến nghị về giá trị dữ liệu, coverage theo MITRE, "similar organizations"; tính năng AI duy nhất liên quan là **gợi ý tag MITRE ATT&CK cho detection** (preview). Không có tính năng AI sửa rule giảm FP — [SOC optimization reference](https://learn.microsoft.com/azure/sentinel/soc-optimization/soc-optimization-reference) (bậc 1, **chỉ snippet**).

**CrowdStrike Charlotte AI Detection Triage** (GA 2025-02): tự đánh giá detection endpoint, cho priority, phân loại TP/FP, đề xuất hành động; "98%+" là **tỷ lệ đồng thuận với quyết định triage của đội Falcon Complete** (MDR của chính CrowdStrike), không phải accuracy so với ground truth độc lập; huấn luyện trên hàng triệu quyết định triage của Falcon Complete. Chỉ triage, không tuning rule — [CrowdStrike blog](https://www.crowdstrike.com/en-us/blog/agentic-ai-innovation-in-cybersecurity-charlotte-ai-detection-triage/) (bậc 1 vendor/marketing, **chỉ snippet**).

**Splunk AI Assistant for SPL**: sinh SPL từ ngôn ngữ tự nhiên; tài liệu định nghĩa 3 metric: token similarity, structural similarity, **execution accuracy** (kết quả chạy có khớp không). Bảng benchmark do Splunk tự công bố: execution accuracy 39,30% (Splunk) vs GPT-4 Turbo 20,40% vs Llama 3 70B 8,40%; Splunk khuyến cáo người kiểm tra trước khi dùng — [Model accuracy measures in Splunk AI Assistant](https://help.splunk.com/en/splunk-enterprise/search/splunk-ai-assistant/2.1.0/use-splunk-ai-assistant/model-accuracy-measures-in-splunk-ai-assistant) (bậc 1 vendor, **chỉ snippet**). Không phải tính năng tuning.

**Elastic**: Attack Discovery gom và xếp hạng alert thành kịch bản tấn công, tóm tắt dạng tường thuật; đội Elastic dựng framework đánh giá tự động bằng LangSmith trên nhiều LLM và dataset alert dựng sẵn vì đánh giá cần chuyên môn security — [Behind the scenes of Elastic Security's generative AI features](https://www.elastic.co/blog/elastic-security-generative-ai-features) (bậc 1 vendor, **chỉ snippet**). Không phải tuning.

**Startup "AI SOC analyst"**
- Prophet Security: trang "How it works" quảng cáo "AI Detection Engineer" để "close coverage gaps" (coverage, không phải FP); "only takes actions you've approved"; "changes are previewed and backtested against your own history before they apply" (không rõ áp dụng cho rule hay cho "memory" triage); khách hàng nói giảm 95% review thủ công — [How Prophet AI works](https://prophetsecurity.ai/how-it-works) (bậc 1 marketing, đã đọc). Một nguồn thứ cấp nhắc agent "Detection Advisor" tuning detection — chưa xác minh trên trang gốc.
- Dropzone AI: theo snippet, khi thấy FP lặp lại từ một rule thì sinh khuyến nghị sửa rule; phụ thuộc vào log có sẵn — [Intezer guide về Dropzone](https://intezer.com/guides/soc-as-a-service/dropzone-ai) (bậc 3, **chỉ snippet**, nguồn là đối thủ cạnh tranh).
- Glossary của Conifers mô tả "SIEM tuning via agentic feedback": agent thấy cùng một FP đóng 40 lần/tuần thì nháp exclusion hoặc thay đổi threshold — [Conifers glossary](https://www.conifers.ai/glossary/siem-tuning-via-agentic-feedback/) (bậc 3, marketing).

**Bằng chứng thực địa / phản biện thị trường**
- Báo cáo của Anton Chuvakin (Google Cloud OCISO) và Oliver Rochford, dựa trên >30 buổi briefing vendor, thảo luận practitioner Reddit/Discord, phỏng vấn CISO/detection engineer: Gartner Hype Cycle 2025 xếp AI SOC agent ở "Innovation Trigger", mức áp dụng khoảng 1–5%; triển khai thực tế chủ yếu là enrichment, tóm tắt điều tra, viết báo cáo; "pilot purgatory"; vendor đếm "kích hoạt tính năng" thay vì dùng thật; một số đội trưởng thành tự build trên LLM đa dụng + tài liệu nội bộ và đạt kết quả tốt hơn sản phẩm thiếu ngữ cảnh môi trường. Chuvakin: "Right now, '50% faster investigations' could mean almost anything" — [Help Net Security](https://www.helpnetsecurity.com/2026/03/26/future-ai-soc-vendor-claims/) (bậc 2, 2026-03-26; đã đọc, chưa đọc báo cáo gốc)

### Nhận định
- Thị trường tách rõ: **triage (phổ biến, có số liệu)** vs **tuning rule (ít, phần lớn là claim marketing hoặc PoC)**. Google là vendor lớn duy nhất có tài liệu cụ thể về LLM chỉnh rule (thêm exclusion qua Gemini, PoC detection-as-code qua MCP), và cả hai đều là hướng dẫn cộng đồng/PoC.
- Microsoft RCT cho thấy giá trị lớn nhất đến từ **xếp hạng/ưu tiên**, không phải từ "suy luận" của LLM; đồng thời có tín hiệu analyst **tin verdict "lành tính" quá mức** — đúng loại lỗi nguy hiểm nhất khi LLM đề xuất "đây là FP, hãy exclude".
- Các con số "98%" (CrowdStrike), "95% giảm review" (Prophet) đo **đồng thuận với người** hoặc tự báo cáo, không đo TP bị bỏ sót.

### Khoảng trống
- Không có đánh giá độc lập nào về chất lượng khuyến nghị tuning của Dropzone/Prophet/Torq/Intezer. Chưa tra Palo Alto Cortex XSIAM, Torq, Intezer cụ thể (hết ngân sách tool call).
- Chưa tìm được blog kỹ thuật của công ty lớn mô tả tự xây hệ thống LLM tuning rule giảm FP trong production (truy vấn: "detection engineering LLM internal blog how we use AI to tune detections false positives 2025" không ra kết quả phù hợp).

## 3. Kiến trúc phù hợp cho task "FP cases + rule → nguyên nhân → đề xuất → kiểm chứng"

### Kết luận ngắn
Bằng chứng ủng hộ kiến trúc **agent có tool + validator tất định + human-in-the-loop** trên nền **detection-as-code**: LLM chỉ đề xuất (structured diff), còn việc đo FP giảm/TP giữ lại do backtest trên dữ liệu lịch sử làm; chỉ merge khi người duyệt. Prompting thuần không đủ vì không kiểm chứng được. RAG có ích (Splunk, SigmaForge). Fine-tune model nhỏ là lựa chọn khi bắt buộc on-prem (REFINE, SigmaForge, Sigma-Hunter) nhưng model ≤4B kém rõ. Mức chắc chắn: **trung bình** (tổng hợp từ các hệ thống lân cận; chưa có hệ thống công khai nào làm đúng task này).

### Phát hiện có nguồn
- Vòng sinh–kiểm–lặp: ADÉ kiểm cú pháp → test mẫu gốc → retro-hunt dữ liệu lịch sử → subagent chấm TP/FP/độ bền → lặp — [arXiv 2509.16749](https://arxiv.org/html/2509.16749) (bậc 1, 2025-09). GRIDAI và RulePilot: replay PCAP lành tính/độc hại, sửa rule khi bắn trên corpus lành tính — [arXiv 2510.13257](https://arxiv.org/pdf/2510.13257), [VTechWorks](https://vtechworks.lib.vt.edu/items/1fd5206d-c461-414f-a3d7-a7b18c25cd3c) (**chỉ snippet**).
- Ràng buộc recall + cổng an toàn + tái học khi phát hiện bỏ sót + fallback về người khi không tìm được cấu hình đạt recall — [REFINE](https://arxiv.org/html/2609.32516) (bậc 1, 2026-09).
- Detection-as-code + MCP: LLM thao tác qua MCP server của SIEM và GitHub, thay đổi rule đi qua repo/pipeline — [Google community PoC](https://security.googlecloudcommunity.com/google-security-operations-2/tuning-rules-in-google-security-operations-using-gemini-and-mcp-servers-824) (bậc 2, 2025-05).
- Mô phỏng sự kiện để kiểm rule: Detection Engineering Agent sinh event UDM giả lập, chạy qua pipeline ingest thật để xác nhận rule bắn — [Google](https://security.googlecloudcommunity.com/community-blog-42/announcing-public-preview-of-the-google-security-operations-detection-engineering-agent-8178) (bậc 1, 2026-09).
- Preview + backtest trước khi áp dụng thay đổi, chỉ làm hành động đã được duyệt — [Prophet](https://prophetsecurity.ai/how-it-works) (bậc 1 marketing).
- RAG + fine-tune + CoT: Splunk quy cải thiện execution accuracy cho fine-tune kết hợp CoT và RAG — [Splunk technical review](https://www.splunk.com/en_us/blog/artificial-intelligence/technical-review-of-splunk-ai-assistant-for-spl.html) (bậc 1 vendor, **chỉ snippet**). SigmaForge dùng truy xuất để sinh Sigma — [Springer](https://link.springer.com/chapter/10.1007/978-3-032-23335-6_4) (**chỉ snippet**).
- Kích thước model: ≥70B sinh cú pháp NIDS ổn định, ≤4B gần như vô dụng — [arXiv 2607.05916](https://arxiv.org/abs/2607.05916) (bậc 1, 2026-07). Ràng buộc privacy buộc REFINE chỉ dùng model open-weight — [REFINE](https://arxiv.org/html/2609.32516).
- Nén ngữ cảnh: "skill" cuối của REFINE chỉ 4,1K–7,6K token so với 18K–58K của playbook ACE — [REFINE](https://arxiv.org/html/2609.32516). Carbon Filter dùng phân cụm quy mô lớn + tìm kiếm nhanh để triage alert real-time — [arXiv 2405.04691](https://arxiv.org/pdf/2405.04691) (**chỉ snippet**, liên quan đến bước gom nhóm alert trước khi đưa cho LLM).
- Ưu tiên logic tất định khi có thể, kết quả đa trạng thái thay vì nhị phân, "circuit breaker" khi độ tin cậy thấp, giải thích được để hậu kiểm (Rochford) — [Help Net Security](https://www.helpnetsecurity.com/2026/03/26/future-ai-soc-vendor-claims/) (bậc 2, 2026-03).
- Chọn exclusion hẹp (1 field/1 rule/1 chuỗi process) thay vì suppress cả rule — tổng hợp practitioner, xem [Future of SecOps](https://www.futureofsecops.com/blog/tuning-detections-cut-false-positives-without-killing-coverage) (bậc 3, **chỉ snippet**).

### Nhận định
Pipeline gợi ý (suy luận từ các nguồn trên, chưa có hệ thống công khai nào triển khai y hệt):
1. **Chuẩn bị dữ liệu tất định**: gom alert FP theo rule_id + bộ giá trị field quyết định (vd process path, parent, user, host group, destination); đếm tần suất; lấy mẫu đại diện mỗi cụm; tóm tắt ghi chú analyst. LLM không đọc log thô hàng loạt → giảm context và giảm bề mặt prompt injection.
2. **RAG**: đưa vào rule hiện tại (dạng code), tài liệu rule/ATT&CK mapping, schema field hợp lệ, asset inventory/CMDB, case cũ tương tự, lịch sử thay đổi rule.
3. **LLM phân loại nguyên nhân FP** của từng cụm (hành vi lành tính đã biết, IoC hết hạn/CDN, logic rule quá rộng, dữ liệu parse sai...) và **đề xuất thay đổi dạng structured output** (JSON: loại thay đổi, diff rule, lý do, cụm FP bị ảnh hưởng, rủi ro).
4. **Validator tất định**: kiểm cú pháp (compiler/linter của SIEM, `sigma check`), kiểm field có tồn tại; **backtest** trên N ngày: số FP bị loại, **mọi TP lịch sử + test tấn công giả lập phải vẫn bắn**; kiểm "exclusion có dễ bị attacker thỏa không" (vd chỉ dựa vào tên file).
5. **Human-in-the-loop**: mở PR trong repo detection-as-code; analyst/detection engineer duyệt; deploy shadow/silent trước; theo dõi; gắn ngày hết hạn/review cho exclusion.
6. LLM **không có quyền ghi** trực tiếp vào SIEM production (giới hạn agency).

### Khoảng trống
- Chưa có nguồn định lượng so sánh trực tiếp prompting thuần vs RAG vs agent vs fine-tune cho task tuning rule.
- Chưa có nguồn cụ thể về kỹ thuật gom nhóm/tóm tắt alert FP trước khi đưa cho LLM (Carbon Filter chưa đọc).

## 4. Đánh giá chất lượng đề xuất

### Kết luận ngắn
Metric cần kết hợp **(a) tất định trên dữ liệu**: FP giảm, TP retention/recall trên TP lịch sử và tấn công giả lập, execution/syntax validity, độ bền của rule (không dựa vào IoC dễ đổi), chi phí/pass@k; **(b) đánh giá của người**: tỷ lệ đề xuất được chấp nhận; **(c) LLM-as-judge** chỉ làm bổ trợ (đồng thuận với người chỉ ở mức vừa phải, kappa 0,66). Benchmark công khai hiện có (CyberSecEval/CyberSOCEval, CTIBench, SIABENCH) **không đo được tuning rule**; cần bộ đánh giá nội bộ. Mức chắc chắn: **trung bình–cao**.

### Phát hiện có nguồn
- Metric của ADÉ: detection accuracy = ½(precision + unique-TP precision); economic cost = chi phí/lần × k (pass@k); robustness theo tỷ lệ pattern hành vi/fuzzy vs match trực tiếp IP/domain/hash — [arXiv 2509.16749](https://arxiv.org/html/2509.16749) (bậc 1, 2025-09).
- Splunk dùng token similarity, structural similarity, execution accuracy; execution accuracy tốt nhất chỉ 39,3% — [Splunk docs](https://help.splunk.com/en/splunk-enterprise/search/splunk-ai-assistant/2.1.0/use-splunk-ai-assistant/model-accuracy-measures-in-splunk-ai-assistant) (bậc 1 vendor, **chỉ snippet**). Snippet nhận xét các metric kiểu BLEU có thể đánh giá cao rule giống cú pháp nhưng sai.
- LLM-as-judge: SigmaForge chấm theo DAG (logic, log source, điều kiện, MITRE), kappa 0,66 với người — [Springer](https://link.springer.com/chapter/10.1007/978-3-032-23335-6_4) (**chỉ snippet**); RulePilot (arXiv) dùng judge 6 chiều — [arXiv 2511.12224](https://arxiv.org/pdf/2511.12224) (**chỉ snippet**).
- TP retention là metric bắt buộc: REFINE giữ recall = 1,0 làm ràng buộc cứng — [REFINE](https://arxiv.org/html/2609.32516); "Sifting the Noise" cho thấy agent lọc FP có thể làm mất 22,25% TP — [arXiv 2601.22952](https://arxiv.org/html/2601.22952v2) (**chỉ snippet**).
- Microsoft RCT: chèn **synthetic FN/FP** vào queue để đo xem người có bắt được lỗi của agent không — [arXiv 2511.13860](https://arxiv.org/html/2511.13860v1) (bậc 1, 2025-11). Kỹ thuật này dùng được để đo analyst có duyệt "rubber-stamp" đề xuất tuning không.
- "Phần trăm đồng thuận với người" (Charlotte 98%+) là metric khác với accuracy so với ground truth — [CrowdStrike](https://www.crowdstrike.com/en-us/blog/agentic-ai-innovation-in-cybersecurity-charlotte-ai-detection-triage/) (**chỉ snippet**).
- "Giảm số lượng alert" — metric vendor phổ biến nhất — có thể che giấu tín hiệu bị suppress nếu không truy vết được (Gillespie, Cybanetix) — [Help Net Security](https://www.helpnetsecurity.com/2026/03/26/future-ai-soc-vendor-claims/) (bậc 2, 2026-03).
- Benchmark công khai:
  - CyberSOCEval (Meta + CrowdStrike, trong CyberSecEval 4, 2025-09): hai phần malware analysis và threat intelligence reasoning; snippet báo accuracy khoảng 15–28% (malware) và 43–53% (TI reasoning); model reasoning không được lợi nhiều từ test-time compute như ở code/toán — [arXiv 2509.20166](https://arxiv.org/html/2509.20166v2) (bậc 1, **chỉ snippet**).
  - CTIBench (NeurIPS 2024 Datasets & Benchmarks, RIT): task CTI như map lỗ hổng sang CWE, tính CVSS — [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2024/hash/5acd3c628aa1819fbf07c39ef73e7285-Abstract.html) (bậc 1, **chỉ snippet**).
  - SIABENCH: 135 kịch bản triage alert, có "false-alert detection" — [arXiv 2603.06422](https://arxiv.org/abs/2603.06422) (bậc 1, 2026-03).
  - SIR-Bench (độ sâu điều tra; nhãn TP/FP do 5 kỹ sư IR 3–8 năm kinh nghiệm gán) — [arXiv 2604.12040](https://arxiv.org/pdf/2604.12040) (**chỉ snippet**).
  - "SecBench": không tìm được nguồn xác nhận; SEC-bench (NeurIPS 2025) là benchmark khác về bảo mật phần mềm (PoC, vá lỗi) — [mlanthology](https://mlanthology.org/neurips/2025/lee2025neurips-secbench) (**chỉ snippet**).

### Nhận định
Bộ metric đề xuất cho task (suy luận):
- **FP reduction %** trên cửa sổ backtest (theo cụm và tổng).
- **TP retention = 100%** trên TP lịch sử + bộ test tấn công giả lập (Atomic Red Team/sự kiện giả lập) — là cổng chặn, không phải metric tối ưu.
- **Syntax/execution validity** (compile được, chạy được, field tồn tại).
- **Độ hẹp & độ dễ khai thác của exclusion** (vd exclusion chỉ theo tên file/path ghi được bởi user thường → điểm phạt).
- **Acceptance rate** của analyst/detection engineer và **tỷ lệ phải chỉnh sửa trước khi merge**; theo dõi rollback sau deploy.
- **Đo rubber-stamping** bằng đề xuất "bẫy" (synthetic bad suggestion) như cách Microsoft chèn synthetic FN/FP.
- LLM-as-judge chỉ để lọc sơ bộ chất lượng giải thích, không thay backtest.

### Khoảng trống
- Không có benchmark công khai cho "tuning rule từ FP". Truy vấn đã chạy: "CyberSOCEval benchmark Meta CrowdStrike SOC LLM", "CTIBench SecBench cybersecurity LLM benchmark NeurIPS".

## 5. Rủi ro & phản biện

### Kết luận ngắn
Có bằng chứng định lượng cho ba rủi ro chính: (1) **prompt injection gián tiếp qua log** — đã đo được LLM bị khiến bỏ qua log độc (persona hijack 68% suppression ở gpt-4o-mini) và guardrail cloud gần như không bắt được payload nằm trong log; (2) **over-tuning / tích tụ exclusion** — trên SigmaHQ, exclusion thêm vào gấp 5,4 lần số bị gỡ, 86,7% còn hiệu lực sau 3 năm, 64,1% exclusion theo path có thể bị process không đặc quyền thỏa mãn; (3) **hallucination / rule quá hẹp** — 12% logic hallucination, rule LLM hẹp hơn rule người. Nhãn FP sai và rò rỉ dữ liệu có cơ sở nhưng ít số liệu trực tiếp. Mức chắc chắn: **cao** về sự tồn tại của rủi ro, **trung bình** về độ lớn trong môi trường thật.

### Phát hiện có nguồn

**Prompt injection gián tiếp qua dữ liệu log**
- "Poisoning the Watchtower" (Pandey & Bhujang, 2026-05): attacker kiểm soát user-agent, URL, payload, DNS query, username thử đăng nhập → chèn lệnh cho LLM analyst ("log-substrate prompt injection"). 4 chiến lược S1 direct override, S2 persona hijack, S3 context manipulation, S4 obfuscated. Với gpt-4o-mini, 48 tổ hợp chiến lược–phòng thủ–task: S1 0% suppression ở task phân loại; **S2 làm suppress 68% log độc** với classifier ngây thơ và vẫn hiệu quả dưới phòng thủ mạnh hơn; S3 96% thành công ở task tóm tắt khi không phòng thủ, 38% khi ràng buộc output; trung bình 26,6% (prompt ngây thơ) → 11,8% (phòng thủ mạnh nhất). Phòng thủ giảm chứ không loại bỏ được bề mặt tấn công — [Poisoning the Watchtower](https://arxiv.org/abs/2605.24421) (bậc 1, preprint, 2026-05-23; đã đọc abstract)
- LogJack (Harsh Shah, 2026-04): 42 payload trong 5 loại log cloud; 8 model; chế độ "active" thực thi lệnh nguyên văn từ 0% (Claude Sonnet 4.6) đến 86,2% (Llama 3.3 70B); `curl | bash` RCE thành công trên 6/8 model; hiện tượng "sanitize and execute" (bỏ phần độc rõ ràng nhưng vẫn chạy phần còn lại); **Azure Prompt Shield chỉ phát hiện 1/32, GCP Model Armor 0** payload nằm trong log dù bắt được cùng payload khi đứng riêng; dặn "không thực thi" giúp hầu hết model về 0% nhưng Llama 3.3 70B vẫn 30% — [LogJack](https://arxiv.org/abs/2604.15368) (bậc 1, 2026-04-15; đã đọc abstract)
- OWASP Top 10 for LLM 2025: LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure, LLM05 Improper Output Handling, LLM06 Excessive Agency, LLM09 Misinformation — [OWASP GenAI](https://genai.owasp.org/llm-top-10/) (bậc 1, 2025; đã đọc)

**Over-tuning, điểm mù, exclusion bị lợi dụng**
- "The Exclusion Ratchet" (Dhananjeyan & Kumaran U., 2026-08, nộp Computers & Security): 9 năm, 8.234 revision của SigmaHQ. Exclusion được thêm 1.642 lần, gỡ 304 lần (**5,4:1**, ở mức từng rule 13:1); 31% sự thu hẹp không thấy được bằng so sánh cấu trúc; **86,7% exclusion còn hiệu lực sau 3 năm**; việc giữ exclusion không phụ thuộc rule đó có phải coverage duy nhất cho kỹ thuật ATT&CK không (p=0,49); **64,1% exclusion theo path có thể bị process không đặc quyền thỏa mãn chỉ bằng cách chọn tên file**. Phát hiện suppression có precision 0,828/recall 0,911 so với gán nhãn tay — [The Exclusion Ratchet](https://arxiv.org/abs/2608.31062) (bậc 1, preprint, 2026-08-31; đã đọc abstract)
- Rule LLM sinh ra hẹp hơn, ít TP hơn (ADÉ) — [arXiv 2509.16749](https://arxiv.org/html/2509.16749); practitioner cảnh báo FP gần 0 có thể nghĩa là rule đã bị thu hẹp tới mức bỏ sót tấn công, khuyên đếm số TP lịch sử mà exclusion sẽ suppress trước khi ship — [Future of SecOps](https://www.futureofsecops.com/blog/tuning-detections-cut-false-positives-without-killing-coverage) (bậc 3, **chỉ snippet**).

**Hallucination / sai cú pháp-ngữ nghĩa**
- Logic hallucination 12%; cú pháp đúng nhưng thiếu đặc hiệu — [arXiv 2607.05916](https://arxiv.org/abs/2607.05916) (bậc 1, 2026-07).
- Execution accuracy SPL tốt nhất 39,3% (Splunk tự công bố) — [Splunk docs](https://help.splunk.com/en/splunk-enterprise/search/splunk-ai-assistant/2.1.0/use-splunk-ai-assistant/model-accuracy-measures-in-splunk-ai-assistant) (**chỉ snippet**).

**Over-reliance của người duyệt**
- RCT Microsoft: nhóm thấy verdict AI bỏ sót synthetic FN 46% vs 17% ở nhóm không thấy — tức người tin verdict "lành tính" sai của agent — [arXiv 2511.13860](https://arxiv.org/html/2511.13860v1) (bậc 1, 2025-11).
- 25 practitioner: rủi ro chính là over-reliance do yếu tố con người — [arXiv 2608.00672](https://arxiv.org/abs/2608.00672) (bậc 1, 2026-08).
- "AI improves comprehension speed. It can degrade judgment if its outputs are treated as authoritative." (Gillespie) — [Help Net Security](https://www.helpnetsecurity.com/2026/03/26/future-ai-soc-vendor-claims/) (bậc 2, 2026-03).

**Nhãn FP sai / nhiễu nhãn**
- REFINE nói rõ nhãn là quyết định dismiss/escalate vận hành hằng ngày, "không phải ground truth tuyệt đối" — [REFINE](https://arxiv.org/html/2609.32516) (bậc 1, 2026-09).
- Survey 2026: không dataset công khai nào có ground truth disposition đầy đủ, dẫn tới hiệu năng công bố bị thổi phồng — [arXiv 2605.08316](https://arxiv.org/pdf/2605.08316) (**chỉ snippet**).
- Practitioner: hai analyst có thể kết luận khác nhau về cùng alert do khác giả định/ngữ cảnh — [INE](https://ine.com/blog/soc-alert-triage-a-practical-framework-for-reducing-noise-without-missing-risk) (bậc 3, **chỉ snippet**).

**Phản biện "AI SOC" nói chung**
- Thử nghiệm được trích nhiều trên Reddit: LLM chạy trên 348 FP đã biết + 1 TP giả lập đạt 71% accuracy, gắn nhãn độc cho FP hiển nhiên và **bỏ sót chính TP thật** — dẫn qua [Help Net Security](https://www.helpnetsecurity.com/2026/03/26/future-ai-soc-vendor-claims/) (bậc 2 dẫn bậc 3, 2026-03).
- Theodos (C3 Integrated Solutions): AI làm tốt demo với dữ liệu sạch nhưng thất bại khi telemetry thiếu/mơ hồ; "AI struggles to reliably distinguish malicious behavior from legitimate but unusual activity" — cùng nguồn.
- Chuvakin: không thấy đường tới "humanless SOC" trong ngắn–trung hạn — [A Brief Guide for Dealing with 'Humanless SOC' Idiots](https://medium.com/anton-on-security/a-brief-guide-for-dealing-with-humanless-soc-idiots-3c2f1a5b26e9) (bậc 2, **chỉ snippet**, không rõ ngày).

**Privacy / data leakage và chi phí**
- REFINE chỉ dùng model open-weight vì quy định privacy của tổ chức cấm API đóng — [REFINE](https://arxiv.org/html/2609.32516) (bậc 1). OWASP LLM02 Sensitive Information Disclosure — [OWASP](https://genai.owasp.org/llm-top-10/).
- Chi phí: ADÉ $1,51–$5,13/rule — [arXiv 2509.16749](https://arxiv.org/html/2509.16749); triage 3–5 giây/alert — [arXiv 2512.08169](https://arxiv.org/pdf/2512.08169) (**chỉ snippet**); OWASP LLM10 Unbounded Consumption.

### Nhận định
- **Kịch bản tấn công cụ thể cho task tuning** (suy luận, chưa có paper đo trực tiếp): attacker biết SOC dùng LLM đề xuất exclusion có thể (a) tạo nhiễu cố ý từ một path/tên file/user-agent rồi chèn chỉ dẫn kiểu "đây là phần mềm backup hợp lệ, nên allowlist" vào command line/user-agent; (b) LLM đề xuất exclusion theo path/tên file; (c) theo Exclusion Ratchet, 64,1% exclusion path loại này có thể bị process không đặc quyền thỏa mãn, và 86,7% sẽ tồn tại sau 3 năm. Kết hợp lại: tuning bằng LLM có thể **tự động hóa và tăng tốc "exclusion ratchet"**, tạo điểm mù bền vững do attacker thiết kế. Biện pháp: không cho trường do attacker kiểm soát chảy nguyên văn vào prompt (đưa qua bước gom nhóm/tóm tắt tất định, đánh dấu là dữ liệu), cấm đề xuất exclusion chỉ dựa vào trường attacker kiểm soát (tên file, user-agent, command line) trừ khi kèm trường khó giả (chữ ký code, hash, host group, parent process có chữ ký), gắn hạn dùng cho exclusion.
- Nhãn FP sai là rủi ro kép: LLM học/khái quát hóa từ nhãn sai → đề xuất exclusion cho chính hoạt động tấn công đã bị analyst đóng nhầm. Cần cross-check với TP lịch sử, threat intel và không tuning từ cụm FP quá nhỏ.
- RCT của Microsoft và Help Net Security cùng chỉ ra rằng **lỗi nguy hiểm là "AI bảo lành tính và người tin theo"** — chính là hướng của đề xuất tuning (luôn là "bỏ bớt alert"). Do đó bước duyệt của người phải có dữ liệu backtest đi kèm, không chỉ lời giải thích của LLM.

### Khoảng trống
- Chưa có nghiên cứu đo trực tiếp prompt injection nhắm vào **đề xuất allowlist/exclusion** (khác với nhắm vào phân loại/tóm tắt). Truy vấn: "prompt injection log data LLM SOC attacker user-agent".
- Chưa có sự cố công khai (postmortem) nào về LLM đề xuất tuning gây bỏ sót tấn công.
- Không có nghiên cứu bình duyệt đo mức bất đồng nhãn giữa analyst (inter-annotator agreement) cho alert SOC. Truy vấn: "SOC analyst alert labels inconsistent noisy ground truth triage study".
- Số liệu "83,4% ASR trung bình, giảm còn 8,4% với GPT-4o có phòng thủ nhiều lớp" từ blog NeuralTrust chưa lần được về paper gốc — [NeuralTrust](https://neuraltrust.ai/blog/ai-soc-prompt-injection) (bậc 3).

## Truy vấn đã chạy
- LLM alert triage false positive SOC arXiv (extended)
- LLM Sigma rule generation evaluation paper (extended)
- LLM detection rule tuning reduce false positives blog (extended)
- prompt injection log data LLM SOC attacker user-agent (extended)
- Google SecOps Gemini detection engineering agent tuning rules (extended)
- Security Copilot phishing triage agent study accuracy results (extended)
- AI agent recommends detection rule exclusion false positive tuning product (extended)
- Anton Chuvakin AI SOC skeptic hype (extended)
- CyberSOCEval benchmark Meta CrowdStrike SOC LLM (standard)
- Elastic Security Labs LLM detection rules Attack Discovery evaluation (standard)
- Microsoft Sentinel SOC optimization recommendations AI rule tuning (standard)
- Dropzone AI Prophet Security detection tuning recommendations feedback (standard)
- LLM Suricata Snort rule generation false positives evaluation arXiv (standard)
- LLM agent refine detection rule false positives backtest historical true positives arXiv (extended)
- Bono randomized controlled trial phishing triage agent Security Copilot arXiv (standard)
- "detection engineering" LLM internal blog how we use AI to tune detections false positives 2025 (extended)
- CrowdStrike Charlotte AI detection triage accuracy agentic Splunk AI Assistant SPL generation (standard)
- Splunk AI Assistant SPL generation accuracy detection (standard)
- CTIBench SecBench cybersecurity LLM benchmark NeurIPS (standard)
- SOC analyst alert labels inconsistent noisy ground truth triage study (standard)
