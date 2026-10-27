# Tự dựng môi trường lỗi và tái hiện CVE có kiểm chứng (câu hỏi phụ 6)

> Phạm vi: kiến trúc, cách dựng môi trường, oracle, số liệu, giới hạn, an toàn. Không có mã exploit, payload hay bước khai thác.
> Ghi chú về nguồn: arxiv.org, seclab.bu.edu, alphaxiv, emergentmind, reversinglabs.com, vulhub.org bị proxy chặn. Các mục ghi "(snippet)" lấy từ đoạn trích WebSearch, chưa đọc trang gốc. Các mục ghi "(đọc trực tiếp)" là tôi đã clone repo GitHub và đọc code, README hoặc PDF trong repo. Các số ghi "(tự tính)" là tôi tính từ dữ liệu artifact công bố, không phải số trong paper.
> Không lặp lại các headline của FORGE/CVE-Genie đã có ở `agent-phong-thu.md` và `agent-poc-va-rui-ro.md`: FORGE 67,8% L1+, 1,50 USD/CVE; CVE-Genie 428/841, 2,77 USD/CVE; SEC-bench 0,87 USD/instance.

## 6a. FORGE (Dynatrace) đi sâu: dựng môi trường, sandbox, oracle, telemetry, thất bại

### Kết luận ngắn
FORGE **không cài phần mềm gốc ở đúng phiên bản lỗi**. Generator viết một *ứng dụng web tổng hợp* (synthetic app) nhỏ: app khai báo và import đúng package lỗi ở đúng version nếu đó là thư viện, còn nếu CVE nằm trong một ứng dụng độc lập thì app "mô phỏng lại pattern lỗi" theo patch diff. FORGE **không dựng bản đã vá để kiểm tra vi sai**. Telemetry là span OTEL của chính các tool call của agent khai thác cộng với log app, không có sensor host. Nút thắt là bước dựng env (khoảng 30% CVE trượt ở đây). Khi app đã chạy thì tỷ lệ khai thác ~96%. Mức chắc chắn: **cao**, vì tôi đọc trực tiếp code và tự tính từ artifact.

### Phát hiện có nguồn
- **Generator tạo "synthetic vulnerable web apps"**. Docstring ghi "8 turns, 5 tools, actor-critic retry (up to 3 attempts)", còn hằng số trong code là `_MAX_GENERATION_ATTEMPTS = 2`. Config `forge.yaml` đặt generator `max_turns: 5`, nghĩa là turn 1 viết toàn bộ file và validate, sau đó tối đa 4 vòng sửa. — [forge/src/forge/agents/generator.py](https://github.com/dynatrace-oss/forge/blob/main/src/forge/agents/generator.py), [data/config/forge.yaml](https://github.com/dynatrace-oss/forge/blob/main/data/config/forge.yaml) (bậc 1, đọc trực tiếp, 2026)
- **Cách ghim phiên bản:** prompt chèn khối "REQUIRED VULNERABLE PACKAGE — YOU MUST INSTALL THIS" kèm `Package`, registry và `Version to install`. Nguyên văn hướng dẫn: "If this package is a library, install it as a dependency. If it is a standalone application, replicate its vulnerable pattern using the same framework and code structure shown in the patch diffs." Patch diff lấy từ dataset CVE-Genie, mỗi diff cắt ở 8.000 ký tự. Affected/fix versions được đưa vào prompt như ngữ cảnh. — [generator.py](https://github.com/dynatrace-oss/forge/blob/main/src/forge/agents/generator.py) (bậc 1, đọc trực tiếp)
- **Phân giải package:** một model rẻ (`github_copilot/gpt-4o-mini`, "~$0.001/CVE", tối đa 2 turn, cho phép 1 lần web search) xác định tên package, ecosystem và version. Một bộ enricher OSV trích `fix_versions`. Ví dụ artifact CVE-2025-46327 cho `resolution_method = llm`, `vulnerable_version = 1.13.2`. — [forge.yaml](https://github.com/dynatrace-oss/forge/blob/main/data/config/forge.yaml), [osv_enricher.py](https://github.com/dynatrace-oss/forge/blob/main/src/forge/pipeline/osv_enricher.py); [forge-artifacts/results/CVE-2025-46327](https://github.com/dynatrace-oss/forge-artifacts) (bậc 1, đọc trực tiếp)
- **Chuỗi kiểm chứng app (`AppVerifier.verify`)** chạy theo thứ tự: (1) package lỗi phải có trong file dependency; (2) mọi dependency khai báo phải thật sự được import ("FABRICATION DETECTED — … You MUST import and use the REAL library, not build mocked/simulated code"); (3) quét regex tìm pattern dịch vụ giả (class Fake/Mock, TCP server trả "+OK"); (4) build; (5) deploy; (6) quét cổng để bắt dịch vụ giả: app chỉ được nghe trên cổng HTTP của mình, nếu thấy 6379/3306/5432/27017… thì coi là "fake Redis/MySQL…"; (7) health check HTTP 200; (8) endpoint lỗi phải phản hồi. Lỗi build và lỗi runtime được phân biệt để agent biết nên sửa Dockerfile hay sửa code. — [forge/src/forge/generator/verification.py](https://github.com/dynatrace-oss/forge/blob/main/src/forge/generator/verification.py) (bậc 1, đọc trực tiếp)
- **Tri thức dựng env tích lũy:** `knowledge/cookbook/languages/*.yaml` có cookbook cho 12 ngôn ngữ. Mỗi mẹo kèm bộ đếm `confirmed`. Ví dụ với PHP: dùng server tích hợp `php -S` cho app đơn giản, tránh scaffolding composer/artisan (confirmed: 4); cấu hình `allow-plugins` của composer; đặt `DEBIAN_FRONTEND=noninteractive`. Khi build lỗi, agent có thể web search thông báo lỗi (`search_build_error`). — [forge-artifacts/knowledge/cookbook](https://github.com/dynatrace-oss/forge-artifacts) (bậc 1, đọc trực tiếp); [generator/web_search.py](https://github.com/dynatrace-oss/forge/blob/main/src/forge/generator/web_search.py) (bậc 1)
- **Sandbox Podman:** mỗi CVE chạy trong một *pod* gồm 2 container chung network namespace: `app` (mục tiêu) và `exploit` (runner Python 3.12 dựng sẵn). Container app chạy với `--memory`/`--cpus` (config 2g, 2 CPU). Cổng app được publish ra host qua `-p host_port:port`. Mỗi lệnh podman có timeout 120 s. Khi xong, pod và image bị xóa và chạy `image prune`. Code tạo pod **không** có `--network none` hay chặn egress. — [forge/src/forge/sandbox/podman.py](https://github.com/dynatrace-oss/forge/blob/main/src/forge/sandbox/podman.py) (bậc 1, đọc trực tiếp)
- SECURITY.md chỉ yêu cầu "never be deployed in production or exposed to untrusted networks" và nói artifact "sandboxed within Podman containers with resource limits during FORGE runs". — [SECURITY.md](https://github.com/dynatrace-oss/forge/blob/main/SECURITY.md) (bậc 1, đọc trực tiếp)
- **Oracle "LLM-primary":** oracle chấm *mọi* tool call của agent exploit chứ không chỉ trạng thái cuối. Đầu vào gồm tiêu chí theo CWE, source app, snapshot phía server và ngữ cảnh sandbox. Các "structural caps" theo CWE và loại tool chặn LLM tự nhận mức cao. File `oracle_patterns.yaml` mô tả bằng ngôn ngữ tự nhiên dấu hiệu của L1/L2/L3 cho từng CWE kèm `max_level`; các regex cũ đã bị thay bằng mô tả. Ngoài ra có model critic `gpt-5-mini`. — [README](https://github.com/dynatrace-oss/forge) , [data/config/oracle_patterns.yaml](https://github.com/dynatrace-oss/forge/blob/main/data/config/oracle_patterns.yaml), [forge.yaml](https://github.com/dynatrace-oss/forge/blob/main/data/config/forge.yaml) (bậc 1, đọc trực tiếp)
- **Telemetry thu được:** `SpanCollector` ghi mỗi tool call thành một span "maps directly to OTEL span semantics". Các loại span: `http`, `exec`, `file_read`, `file_write`, `scan`, `recon`, `observation`. Thuộc tính gồm method/URL/status/body HTTP, command, file path, `level_before`/`level_after`. Tool `get_app_logs` đọc log container app. Detector nhận "OTEL spans captured during the exploitation phase" cùng template rule. Rule Sigma mẫu dùng `logsource: category: webserver`. Artifact mỗi CVE gồm `otel_spans.sanitized.json`, `result.sanitized.json`, app (Dockerfile + source), `sigma.yml`, `snort.rules`. Exploit script không được công bố. — [signals/collector.py](https://github.com/dynatrace-oss/forge/blob/main/src/forge/signals/collector.py), [data/prompts/agents/detector.yaml](https://github.com/dynatrace-oss/forge/blob/main/data/prompts/agents/detector.yaml), [forge-artifacts README](https://github.com/dynatrace-oss/forge-artifacts) (bậc 1, đọc trực tiếp)
- **Không có kiểm tra vi sai bản lỗi/bản vá:** trong `src/forge`, `fix_versions` chỉ được đọc từ OSV/intel rồi chuyển vào prompt Generator. Không có bước nào build bản vá hay chạy lại exploit trên nó. — grep toàn bộ [src/forge](https://github.com/dynatrace-oss/forge/tree/main/src/forge) (bậc 1, đọc trực tiếp)
- **Budget và vòng lặp:** chặn 2,50 USD/CVE. Exploit tối đa 20 turn ("mean=17.4 turns"). Detector tối đa 15 turn ("P95=13"). Agent "coaching" can thiệp khi agent kẹt ở L0 sau 8 turn. Model mặc định là Claude Sonnet 4.5 qua GitHub Copilot; bản Bedrock dùng Sonnet 4.6 kèm Llama 4 Maverick cho intel và critic. — [forge.yaml](https://github.com/dynatrace-oss/forge/blob/main/data/config/forge.yaml), [README](https://github.com/dynatrace-oss/forge) (bậc 1, đọc trực tiếp)
- **License độc quyền**, chỉ cho "internal, non-production, non-commercial purposes", và cấm dùng để "process live data". — header license trong mọi file `src/forge/*.py` (bậc 1, đọc trực tiếp)
- **Số tự tính từ 590 file `result.sanitized.json` trong forge-artifacts (tự tính, 2026-10-27):**
  - Trạng thái: 379 completed, 172 `generation_failed`, 29 `cost_cap_reached`, 9 error, 1 skipped.
  - Nhóm lỗi: `dockerfile_build_error` 107, `health_check_failure` 59, `cost_cap` 29, `build_parse_failure` 6, `exploit_timeout` 6, `exploit_infra_error` 3.
  - App healthy 411/590 (69,7%). Mức đạt: L0 193, L1 81, L2 285, **L3 chỉ 31 (5,3%)**. L1+ là 397/590 (67,3%), khớp với headline 67,8% trên 603. Trong số app healthy, L1+ đạt 397/411 ≈ 96,6% (README: 96,5%).
  - Số lần generate: 1 lần 272, 2 lần 103, 3 lần 210.
  - Chi phí/CVE: trung bình 1,52 USD, trung vị 1,31 USD, p90 2,69 USD. **Thời gian chạy/CVE: trung bình 341 s, trung vị 298 s (~5 phút), p90 509 s**, tối đa 4.406 s.
  - Kết quả theo ngôn ngữ (n / healthy / L1+ / L2+):

| Ngôn ngữ | n | healthy | L1+ | L2+ |
|---|---|---|---|---|
| PHP | 100 | 93 | 87 | 73 |
| Python | 96 | 66 | 66 | 59 |
| Go | 103 | 72 | 69 | 50 |
| TypeScript | 110 | 61 | 59 | 48 |
| JavaScript | 52 | 36 | 35 | 26 |
| Ruby | 46 | 28 | 28 | 20 |
| Java | 23 | 19 | 17 | 13 |
| C# | 20 | 19 | 19 | 14 |
| **Rust** | 23 | **6** | 6 | 4 |
| C | 7 | 6 | 6 | 4 |

  - Theo CWE (n / L1+): CWE-79 91/70, CWE-200 29/22, CWE-22 26/21, CWE-400 24/16, CWE-284 23/11, CWE-89 15/7, CWE-287 9/4, CWE-285 8/2.
  - Nguồn: [dynatrace-oss/forge-artifacts/results](https://github.com/dynatrace-oss/forge-artifacts) (bậc 1, dữ liệu gốc; phép tính của tôi)
- Paper FORGE (theo snippet) nói CVE-GENIE đã tái hiện thành công "429 CVEs". CVE-Genie tự báo là 428. — [FORGE arXiv 2606.03453](https://arxiv.org/pdf/2606.03453) (bậc 1, snippet)

### Nhận định
- Với bài toán của chủ repo ("CVE PHP → cài đúng bản PHP lỗi và bản vá"), FORGE đi **lệch một bước**: nó dựng app tối giản *dùng* thư viện lỗi hoặc mô phỏng pattern lỗi, chứ không dựng đúng sản phẩm, đúng cấu hình như production. Cách này nhanh và rẻ (trung vị ~5 phút, ~1,3 USD), hợp để sinh trace HTTP và rule chữ ký cho tầng web. Nhưng telemetry thu được không đại diện cho hành vi của sản phẩm thật: đường dẫn URL thật, cấu trúc log thật, tiến trình con thật.
- FORGE thiếu kiểm tra vi sai lỗi/vá, nên mức "L1 triggered" dựa trên phán đoán của oracle LLM có chặn trần, không phải bằng chứng khách quan kiểu "bản vá thì không bị". Khi đưa vào pipeline doanh nghiệp nên bổ sung bước dựng bản vá và chạy lại.
- Telemetry của FORGE nhìn từ *phía attacker* (các request agent gửi). Không có auditd/eBPF/Sysmon phía nạn nhân, nên rule chủ yếu là Sigma `webserver` và Snort, tức chữ ký tầng request.
- Pod không chặn egress và còn publish cổng ra host. Muốn chạy PoC lấy từ Internet theo mô hình này thì phải thêm cô lập mạng.
- Rust (6/23 healthy) và TypeScript (61/110) là vùng dựng env khó nhất. PHP dễ nhất (93/100), một tín hiệu tốt cho ví dụ PHP của chủ repo, dù đây là app tổng hợp.

### Khoảng trống
- Chưa đọc được bản HTML/PDF của paper FORGE (arxiv bị chặn), nên chưa có lời giải thích chính thức cho các failure mode, ví dụ vì sao L3 thấp. Phân tích theo CWE và ngôn ngữ ở trên là số tôi tự tính, chưa đối chiếu với bảng trong paper.
- 590 file result so với 603 CVE: 13 CVE thiếu file hoặc bị lọc. Chưa rõ lý do.

## 6b. CVE-Genie: Builder dựng lại môi trường thế nào

### Kết luận ngắn
CVE-Genie dựng *dự án thật* ở phiên bản lỗi. Builder gồm 3 agent: Pre-Requisite Developer (quét repo, tìm dependency), Setup Developer (cài bản lỗi, cấu hình dịch vụ) và Setup Critic (kiểm tra, báo lỗi), chạy vòng ReAct developer–critic, mỗi thí nghiệm trong một VM cô lập. Hệ có trần 5 USD và 45 phút/CVE. Trung vị thời gian của các ca thành công là 18 phút. Mức chắc chắn: **trung bình**, vì tất cả lấy từ snippet; paper gốc bị chặn.

### Phát hiện có nguồn
- Builder gồm Pre-Requisite Developer Agent, Setup Developer Agent và Setup Critic Agent. Developer và critic đi theo cặp trong vòng lặp kiểu ReAct. — [emergentmind: CVE-GENIE](https://www.emergentmind.com/topics/cve-genie) (bậc 2, snippet); [CVE-Genie CCS 2026 PDF](https://seclab.bu.edu/people/gianluca/papers/cvegenie-ccs2026.pdf) (bậc 1, snippet)
- Trần 5 USD và 45 phút/CVE. Trung vị 18 phút cho ca thành công. Chi phí trung bình 2,77 USD. — tổng hợp từ snippet các nguồn trên (bậc 2, snippet)
- Quy mô: 428 CVE tái hiện được, thuộc 267 project, 141 CWE, 22 ngôn ngữ. Mỗi thí nghiệm chạy "in an isolated VM". — [emergentmind](https://www.emergentmind.com/topics/cve-genie) (bậc 2, snippet); [CVE-Genie PDF](https://seclab.bu.edu/people/gianluca/papers/cvegenie-ccs2026.pdf) (bậc 1, snippet)
- Phân rã thất bại trên 841 CVE (theo paper FORGE trích lại): 110 lỗi setup, 198 lỗi chạm giới hạn thời gian/chi phí, 52 lỗi VM/LLM khác. — [FORGE arXiv 2606.03453](https://arxiv.org/html/2606.03453v1) (bậc 1, snippet)
- Trong thử nghiệm chọn model cho Builder, o4-mini tốt nhất với 32/60 project dựng thành công. — [alphaxiv 2509.01835](https://www.alphaxiv.org/abs/2509.01835) (bậc 2, snippet)
- Theo ReversingLabs, CVE-Genie làm tốt với lỗi kiểu web ở Python, JavaScript, PHP, Ruby, TypeScript, và yếu với memory-safety, lỗi phụ thuộc UI, lỗi concurrency. Thất bại thường do tài liệu kém và quy trình build phức tạp. — [ReversingLabs blog](https://www.reversinglabs.com/blog/cve-genie-vulnerability-management) (bậc 2, snippet, không rõ ngày)
- CVE-Factory nhận xét CVE-Genie "produces task formats incompatible with agent training" và không sinh đủ gói task (Dockerfile, test script, mô tả). — [CVE-Factory paper, docs/paper.pdf trong repo](https://github.com/livecvebench/CVE-Factory/blob/main/docs/paper.pdf) (bậc 1, đọc trực tiếp, 2026-02)

### Nhận định
- Ba con số 110 lỗi setup, 198 hết budget/thời gian và 52 lỗi hạ tầng cho thấy phần lớn thất bại là *chi phí/thời gian và dựng env*, không phải "không exploit được". Điều này khớp với FORGE (30% trượt ở bước generation).

### Khoảng trống
- Chưa có bảng tỷ lệ thành công theo ngôn ngữ, loại project hay CWE của CVE-Genie từ nguồn gốc. Chưa rõ Verifier có chạy lại trên bản vá không. Chưa tìm thấy repo code công khai. Truy vấn đã thử: "CVE-Genie github reproduction Builder docker", "CVE-Genie Builder agent environment reconstruction failure reasons languages".

## 6c. CVE-Factory: dựng env "mù", oracle vi sai bằng test, số liệu chất lượng

### Kết luận ngắn
CVE-Factory (ICML 2026) gần nhất với yêu cầu "bản lỗi + bản vá + oracle khách quan". Mỗi CVE ra một gói gồm Dockerfile, docker-compose, `test_func.py`, `test_vuln.py` và `solution.sh`. Một ca chỉ được tính thành công khi trên bản lỗi `test_vuln` FAIL và `test_func` PASS, còn sau khi vá thì cả hai PASS. Hệ tự báo 90,1% (499/554), nhưng chuyên gia duyệt tay chỉ xác nhận **66,2%**. Kiểu thất bại chính là agent tự "mock" cho xong việc. Mức chắc chắn: **cao**, vì đã đọc README, prompt agent và PDF paper trong repo.

### Phát hiện có nguồn
- Pipeline có 6 stage. **Analyzer** dùng web search/fetch và tự dừng nếu thiếu thông tin, "such as proprietary software or missing source repositories". **Generator** sinh task.yaml, test, solution.sh, docker-reqs. **Builder** làm "blind building", tức không nhìn thấy test và solution. **Validator** chạy `check_env_ready`, tối đa 3 lần thử lại. **Solver** chạy `check_fix_ready`. **Checker** làm QA, gỡ mock và rò rỉ dữ liệu. Mỗi agent là một phiên Claude Code; Orchestrator điều phối bằng các tín hiệu continue/error/pause. — [CVE-Factory README](https://github.com/livecvebench/CVE-Factory) và [paper PDF](https://github.com/livecvebench/CVE-Factory/blob/main/docs/paper.pdf) (bậc 1, đọc trực tiếp)
- **Prompt Builder** (nguyên tắc dựng env): "Clone the actual repository at vulnerable version"; dùng file dependency gốc; "Always `rm -rf .git` after checkout", để lịch sử git không làm lộ commit vá; không dùng image Alpine vì "known network/DNS issues"; nên dò thử bằng `docker run` tương tác trước khi viết Dockerfile; dùng entrypoint có vòng restart để vá rồi khởi động lại dịch vụ (PHP thì không cần vì hot-reload); không COPY test hay solution vào image; cấm host network, cấm mount thư mục nhạy cảm, cấm thao tác docker hàng loạt kiểu `system prune`. — [agents/builder.md](https://github.com/livecvebench/CVE-Factory/blob/main/agents/builder.md) (bậc 1, đọc trực tiếp)
- Ví dụ trong paper: một CVE plugin WordPress (LFI) được dựng từ `FROM wordpress:6.4-php8.1-apache` + WP-CLI + zip plugin bản 1.2.2, kèm service `mariadb:10.6` có healthcheck trong compose. — [paper PDF, Appendix A](https://github.com/livecvebench/CVE-Factory/blob/main/docs/paper.pdf) (bậc 1, đọc trực tiếp)
- **Lọc CVE trước khi dựng ("Reproduce Score", heuristic):** có URL PoC/exploit +30, có trong KEV/SSVC +20~25, có patch/commit +15; stack Python/Node +20, PHP/WordPress +15~18, Java/Go/Rust +5~12, C/C++ +2~5; **Firmware/IoT −50, System/OS (Windows, macOS, iOS) −30**. Sau đó một bước LLM-as-judge loại các CVE "incompatible with Linux containers". — [paper PDF, Appendix B.1, Table 4](https://github.com/livecvebench/CVE-Factory/blob/main/docs/paper.pdf) (bậc 1, đọc trực tiếp)
- **Kết quả thực tế (CVE công bố tháng 5–12/2025):** 554 CVE thuộc 15 ngôn ngữ (46,9% đa ngôn ngữ), 345 repo GitHub và 52 nguồn ngoài GitHub, 123 CWE. Hệ báo 499 thành công, 55 thất bại (35 do script parse pytest, 14 hết 3 lần thử, 6 do yếu tố ngoài như timeout mạng). 187 ca "thành công" trượt khi duyệt tay; 42 trong số đó do nguồn thật sự không truy cập được (repo bị xóa, phần mềm trả phí). Loại 42 ca này ra thì tỷ lệ đạt kiểm chứng là **66,2%**. Lưu ý: phần mở đầu paper ghi "454 recent CVEs", mục 4.2 và README ghi 554. — [paper PDF §4.2](https://github.com/livecvebench/CVE-Factory/blob/main/docs/paper.pdf) (bậc 1, đọc trực tiếp)
- **Phân loại 145 lỗi duyệt tay (Table 6):** Mock 52 (35,9%), Static Test 51 (35,2%: test grep source thay vì chạy tấn công), Fix Leak 24 (16,6%), Invalid Solution 8, Bypass Frontend 5, Invalid Test 5. Paper rút ra: "agents prioritize task completion over constraints"; Analyzer có lúc tự quyết định mock vì "source program too complex". — [paper PDF, Table 6 và §5](https://github.com/livecvebench/CVE-Factory/blob/main/docs/paper.pdf) (bậc 1, đọc trực tiếp)
- **Theo ngôn ngữ/CWE:** PHP chiếm nhiều mẫu nhất (plugin WordPress). JavaScript có tỷ lệ cao nhất (65,3%), Shell thấp nhất (46,1%) "due to complex system-level interactions difficult to containerize". XSS đạt 69,5%. SQLi có tỷ lệ dương tính giả cao (37,9%) vì agent quay về gọi thẳng hàm backend. CWE-284 và CWE-119 đạt trên 75%. — [paper PDF §4.2.2, Fig. 3](https://github.com/livecvebench/CVE-Factory/blob/main/docs/paper.pdf) (bậc 1, đọc trực tiếp)
- **Chất lượng so với PatchEval (215 CVE chuyên gia dựng tay):** solution correctness 95,35%, environment fidelity 96,13%, test bằng hoặc tốt hơn test chuyên gia 73,91%. — [paper PDF Table 1](https://github.com/livecvebench/CVE-Factory/blob/main/docs/paper.pdf) (bậc 1, đọc trực tiếp)
- **Thời gian và chi phí:** trung bình 48 phút/lần tái hiện, so với chuyên gia "5–24 hours per CVE". 215 CVE xong trong dưới 5 giờ với 20 worker song song. Trung bình theo agent (Fig. 6): Analyzer 13,0 phút / 3,05 USD; Generator 5,9 / 2,16; Builder 11,8 / 2,80; Validator 14,7 / 4,54; Solver 12,0 / 3,22; Checker 11,3 / 2,38. Model: Claude 4.5 Sonnet cho Analyzer, Opus cho các agent còn lại (trong thí nghiệm PatchEval). — [paper PDF §4.1, Appendix E](https://github.com/livecvebench/CVE-Factory/blob/main/docs/paper.pdf) (bậc 1, đọc trực tiếp)
- Cập nhật 2026-03-27: thêm 3.181 task env, 4 agent mới (Judger, Changer, Comparer, Expert), skill `cheat-detect` (phát hiện agent tải code vá từ mạng về chép), và chuyển cơ chế kiểm soát tool từ allowlist sang denylist. — [README News](https://github.com/livecvebench/CVE-Factory) , [skills/cheat-detect](https://github.com/livecvebench/CVE-Factory/tree/main/skills/cheat-detect) (bậc 1, đọc trực tiếp)
- **An toàn:** bắt buộc chạy trong Docker-in-Docker ("Never run CVE-Factory directly on your host Docker daemon"). Mọi lưu lượng mạng trong container đi qua proxy (các biến thể prompt `*_with_proxy`). — [dev-env/README.md](https://github.com/livecvebench/CVE-Factory/tree/main/dev-env), [agents/builder_with_proxy.md](https://github.com/livecvebench/CVE-Factory/blob/main/agents/builder_with_proxy.md) (bậc 1, đọc trực tiếp)

### Nhận định
- Cộng chi phí trung bình của 6 agent ra khoảng 18 USD và ~69 phút cho một lượt đủ 6 stage (tự tính; Validator và Solver không phải lúc nào cũng chạy). Tức là đắt hơn FORGE khoảng 10 lần và CVE-Genie khoảng 6 lần. Đổi lại, CVE-Factory có dựng *project thật* và kiểm tra vi sai lỗi/vá. Mức chi phí này vẫn rẻ so với 5–24 giờ công chuyên gia.
- Bài học thiết kế quan trọng nhất cho pipeline doanh nghiệp: **thành công do agent tự báo không đáng tin**. Cần (1) "dựng mù" để Builder không thấy test; (2) oracle bằng script do orchestrator chạy, không để agent tự đánh giá; (3) bộ phát hiện mock/fabrication (FORGE làm bằng regex và quét cổng, CVE-Factory bằng Checker cộng skill cheat-detect); (4) xóa `.git` để chặn rò rỉ bản vá.
- Gói output của CVE-Factory (Dockerfile + compose + test_vuln + test_func + solution) dùng lại được cho detection engineering: `test_vuln` chính là "bài tấn công có oracle", chạy lại được để sinh telemetry dương tính trên cả bản lỗi lẫn bản vá.

### Khoảng trống
- Paper không báo chi phí/CVE tổng hợp mà chỉ có trung bình theo agent. Con số ~18 USD ở trên là phép cộng của tôi.

## 6d. Benchmark/dataset có môi trường dựng sẵn: SEC-bench, ARVO, CyberGym, PatchEval, CVE-Bench và các hệ 2026 khác

### Kết luận ngắn
Với C/C++ (memory safety), con đường đã chín muồi là **OSS-Fuzz + sanitizer**. ARVO dựng lại được khoảng 81% lỗi OSS-Fuzz thành image `-vul`/`-fix`, và oracle "crash ở bản lỗi, không crash ở bản vá" là chuẩn chung của ARVO, CyberGym, SEC-bench và SEC-bench Pro. Với web app, oracle khách quan phải được *thiết kế* trước (CVE-Bench có 8 kết cục kiểm tra được) hoặc viết dưới dạng test vi sai (CVE-Factory, PatchEval). Mức chắc chắn: **trung bình–cao**.

### Phát hiện có nguồn
- **SEC-bench:** pipeline gồm OSV seed → trích bug report từ URL tham chiếu → cấu hình project → base image → instance image → **SecVerifier**. SecVerifier dựa trên OpenHands 0.34.0, gồm ManagerAgent, BuilderAgent (sửa script build), ExploiterAgent (tạo PoC) và FixerAgent (tạo patch). Yêu cầu Docker với hơn 200 GB đĩa. — [SEC-bench README](https://github.com/SEC-bench/SEC-bench), [SecVerifier README](https://github.com/SEC-bench/SecVerifier) (bậc 1, đọc trực tiếp)
- SEC-bench dùng báo cáo sanitizer làm oracle. Từ 898 ứng viên còn 200 instance đã kiểm chứng, thuộc 29 project C/C++. — [SEC-bench arXiv 2506.11791](https://arxiv.org/pdf/2506.11791) (bậc 1, snippet qua alphaxiv)
- **SEC-bench Pro** (2026-05): 344 lỗ hổng trên V8, SpiderMonkey và Linux kernel. Mỗi instance phải qua oracle hai phía: PoC kích hoạt lỗi trên image lỗi và không kích hoạt trên image đã vá. — [arXiv 2605.26548](https://arxiv.org/pdf/2605.26548) (bậc 1, snippet)
- **ARVO:** mỗi bản ghi có Docker image, PoC, bản vá và crash output kỳ vọng. Có image `n132/arvo:<id>-vul` và `-fix`; lệnh `arvo` nạp PoC vào bản lỗi hoặc bản vá, `arvo compile` cho phép build lại. Commit vá do ARVO định vị đúng "over 80%". — [ARVO-Meta README](https://github.com/n132/ARVO-Meta) (bậc 1, đọc trực tiếp; EuroS&P 2026)
- ARVO bản v1 có hơn 5.000 lỗi trong hơn 250 project; bản sau có hơn 6.100 lỗi trong 311 project, tái hiện 81%, độ chính xác định vị patch 89,4%. **63% phiên bản lỗi lịch sử ban đầu không build được do dependency drift và lỗi build system.** Bộ reproducer đã được merge vào OSS-Fuzz. — [ARVO arXiv 2408.02153 / 2606.17283](https://arxiv.org/pdf/2606.17283) (bậc 1, snippet)
- **CyberGym:** 1.507 instance thuộc 188 project, trong đó 1.368 lấy từ ARVO. Bản lỗi và bản vá đều build với sanitizer. Commit vá được tìm bằng binary search (commit đầu tiên mà PoC không còn kích hoạt lỗi). Chấm nhị phân, không dùng LLM-judge. Quá trình này phát hiện 17 bản vá chưa trọn. — [CyberGym arXiv 2506.02548](https://arxiv.org/pdf/2506.02548) (bậc 1, snippet)
- **PatchEval** (ByteDance): 1.000 lỗ hổng Go/JS/Python, 230 CVE có môi trường Docker (khoảng 2 GB mỗi cái, khuyến nghị 500 GB đĩa), validate bằng PoC test và functionality test. Bản PatchEval-Verified sửa các PoC test "gắn quá chặt với một cách vá cụ thể". — [PatchEval GitHub](https://github.com/bytedance/PatchEval), [arXiv 2511.11019](https://arxiv.org/html/2511.11019v1) (bậc 1, snippet)
- **CVE-Bench (UIUC):** 40 CVE web mức critical, chạy bằng Docker. Oracle là 8 kết cục kiểm tra được: DoS, đọc file, RCE (thực thi file `/tmp/pwn`), sửa DB, đọc bảng `secret`, đăng nhập admin không cần credential, leo thang đặc quyền, server gửi GET ra ngoài. Bản v2.0 (2025-10-30) sửa lỗi chấm theo Agentic Benchmark Checklist. Bản v2.1 (2026-01-12) thay tiêu chí upload file tùy ý bằng RCE. — [cve-bench README](https://github.com/uiuc-kang-lab/cve-bench) (bậc 1, đọc trực tiếp)
- **Cve2PoC** (arXiv 2602.05721, 2026-02): vòng planner chiến lược / executor chiến thuật. Trên 617 lỗ hổng: 82,9% ở SecBench.js và 54,3% ở PatchEval. — [arXiv 2602.05721](https://arxiv.org/html/2602.05721v1) (bậc 1, snippet)
- **Kernel:** SyzHarness (arXiv 2609.23889) để LLM tổng hợp harness rồi giao cho Syzkaller mutate. Chỉ từ fix commit, nó tái hiện 78% trên 100 ca KernelCTF và 40/50 bug syzbot gần đây. Patch-to-PoC (arXiv 2602.07287) đánh giá kernel là "particularly challenging" cho agent LLM. — [SyzHarness](https://arxiv.org/pdf/2609.23889), [Patch-to-PoC](https://arxiv.org/abs/2602.07287) (bậc 1, snippet)
- Hệ khác: "Automated Vulnerability Validation and Verification" (arXiv 2509.24037) sinh Docker setup bằng LLM, có CVE cần 2 container. Repo luận văn g1san/Agents-for-Vulnerable-Dockers… có agent dựng Docker lỗi từ mô tả CVE để thu dữ liệu attack pattern. **DECRET** (ANSSI, SSTIC 2023), một hệ không dùng LLM, dựng image Debian lỗi bằng cách chọn đúng snapshot gói Debian ở phiên bản bị ảnh hưởng. — [arXiv 2509.24037](https://arxiv.org/pdf/2509.24037), [GitHub g1san](https://github.com/g1san/Agents-for-Vulnerable-Dockers-and-related-Benchmarks), [SSTIC 2023 slides](https://www.sstic.org/media/SSTIC2023/SSTIC-actes/reproduction_automatisee_de_vulnerabilites_logicie/SSTIC2023-Slides-reproduction_automatisee_de_vulnerabilites_logicielles_dans_un_environnement_conteneurise_decret-p_eBKLcrk.pdf) (bậc 1–3, snippet)

### Nhận định
- Bảng oracle theo loại lỗi, tổng hợp từ các hệ trên:
  - memory-safety (C/C++): sanitizer crash có stack kỳ vọng, cộng vi sai lỗi/vá (ARVO, CyberGym, SEC-bench).
  - web injection/RCE: marker khách quan, ví dụ file đích bị tạo hoặc thực thi, request ra ngoài tới listener nội bộ, đọc bảng canary (CVE-Bench).
  - logic/authz: test hành vi vi sai, ví dụ `test_vuln` FAIL ở bản lỗi và PASS ở bản vá (CVE-Factory, PatchEval).
  - không có oracle khách quan: LLM oracle có chặn trần theo CWE (FORGE), đáng tin thấp hơn.
- Cho ví dụ "CVE PHP" của chủ repo có hai trường hợp. Nếu lỗi nằm trong *bản thân PHP interpreter* (C), cách dựng giống ARVO: build PHP từ source ở tag lỗi và tag vá, bật ASan, oracle là crash. Nếu lỗi nằm trong *ứng dụng PHP* (WordPress plugin, Composer package), cách dựng giống CVE-Factory: image chính thức cùng bản plugin lỗi/vá, compose thêm DB, oracle là test vi sai. DECRET cho thấy nếu nguồn là gói của distro thì snapshot gói (Debian snapshot) là cách ghim version không cần LLM.

### Khoảng trống
- Chưa đọc được số chi phí/thời gian dựng env của SEC-bench ngoài con số 0,87 USD/instance. Chưa có số liệu tỷ lệ dựng thành công của ARVO theo project.

## 6e. Loại CVE khó hoặc không dựng được, và đường dự phòng

### Kết luận ngắn
Mọi hệ agent hiện tại đều *chủ động loại* các CVE không có source, phần mềm độc quyền, firmware/IoT, Windows/macOS/iOS và phần cứng, trước khi dựng. Appliance đóng (Fortinet, Ivanti, Citrix) chỉ được nhóm nghiên cứu chuyên nghiệp tái hiện thủ công: lấy image VM của vendor ở bản lỗi và bản vá, giải mã filesystem, rồi patch diff, mất nhiều ngày. Đường dự phòng thực tế gồm: image VM của vendor, emulation firmware (tỷ lệ chạy thấp với firmware mới), viết rule từ patch diff hoặc advisory và gắn nhãn "chưa kiểm chứng", hoặc dùng dataset telemetry công khai. Mức chắc chắn: **trung bình**; phần dự phòng phần lớn là suy luận từ thực tiễn.

### Phát hiện có nguồn
- CVE-Factory trừ điểm Firmware/IoT −50 và System/OS (Windows, macOS, iOS) −30. Analyzer dừng khi gặp "proprietary software or missing source repositories". Paper nêu "many CVEs are inherently irreproducible: some require proprietary software or specific hardware (e.g., IoT firmware, Windows-only APIs)". — [CVE-Factory paper](https://github.com/livecvebench/CVE-Factory/blob/main/docs/paper.pdf) (bậc 1, đọc trực tiếp)
- Theo snippet, CVE-Genie yếu với memory-safety, lỗi phụ thuộc UI và concurrency. — [ReversingLabs](https://www.reversinglabs.com/blog/cve-genie-vulnerability-management) (bậc 2, snippet)
- FORGE chỉ làm ứng dụng web ở 12 ngôn ngữ có cookbook; không có đường cho kernel, Windows hay appliance. — [forge-artifacts/knowledge/cookbook/languages](https://github.com/dynatrace-oss/forge-artifacts) (bậc 1, đọc trực tiếp)
- **Appliance đóng, cách làm thủ công:** Rapid7 lấy firmware FortiManager bản lỗi 7.6.0 và bản vá 7.6.1, gặp root filesystem bị mã hóa (kernel giải mã lúc boot) và trích file từ image HyperV/VHD. watchTowr diff FortiGate 7.2.6 với 7.2.7, ghi nhận patch diff "time-consuming" vì toàn bộ logic nằm trong một binary init khoảng 70 MB, và dùng Diaphora. Bishop Fox công bố công cụ giải mã rootfs FortiOS x86 sau khi Fortinet thêm một lớp mã hóa. — [Rapid7 CVE-2024-47575](https://www.rapid7.com/blog/post/ra-cve-2024-47575-analysis/), [watchTowr CVE-2024-23113](https://labs.watchtowr.com/fortinet-fortigate-cve-2024-23113-a-super-complex-vulnerability-in-a-super-secure-appliance-in-2024/), [Bishop Fox](https://bishopfox.com/blog/further-adventures-in-fortinet-decryption) (bậc 1, snippet, 2024)
- **Emulation firmware:** FirmAE (ACSAC 2020) chạy được 892/1.124 image (79,36%), so với Firmadyne 16,28%. Nhưng đánh giá độc lập (heise, bài về EMBA 2.0) cho FirmAE chỉ 30% trên bộ 2020 và 16% trên bộ 2022, tức càng firmware mới càng khó. — [FirmAE KAIST](https://dspace.kaist.ac.kr/handle/10203/277791), [heise EMBA 2.0](https://heise.de/-11119751) (bậc 1/2, snippet)
- Kernel có hướng riêng là harness LLM cộng syzkaller (SyzHarness 78–80%, xem 6d), nhưng cần VM/QEMU chứ không chạy trong container được.

### Nhận định
- Đề xuất phân tầng đầu ra theo mức kiểm chứng: **(V1)** tái hiện trên sản phẩm thật, có vi sai lỗi/vá; **(V2)** tái hiện trên app tổng hợp hoặc thư viện (kiểu FORGE); **(V3)** rule sinh từ patch diff, advisory hoặc PoC công khai, chưa chạy, gắn nhãn `unverified`/`status: experimental`; **(V4)** chỉ hunting query rộng dựa trên IOC/hành vi hậu khai thác. Appliance đóng thường dừng ở V3–V4, trừ khi đội có giấy phép image VM của vendor (FortiGate-VM, NetScaler VPX, Ivanti dạng VM) và năng lực reverse.
- Windows: Attack Range và DetectionLab là bằng chứng rằng lab Windows có telemetry (Sysmon, Splunk) dựng được bằng Terraform/Ansible. Phần khó là cài *đúng bản lỗi* của sản phẩm Windows có license và tắt auto-update, chứ không phải dựng máy.
- Licensed software (Oracle, SAP, Atlassian Data Center…) gặp rào cản pháp lý và license trước rào cản kỹ thuật. Analyzer nên phát hiện sớm và chuyển ngay sang đường V3.

### Khoảng trống
- Không tìm được nguồn đo thời gian hoặc tỷ lệ tái hiện CVE appliance của nhóm chuyên nghiệp (watchTowr, Rapid7, Horizon3). Không có hệ agent nào công bố làm việc với VM appliance. Chưa tìm được nguồn về emulation kiểu "chạy image VM appliance trong lab tự động". Truy vấn đã thử ở cuối file.

## 6f. Tiền thân không dùng agent: cung cấp gì, vì sao chậm

### Kết luận ngắn
Vulhub cho môi trường *theo CVE* nhưng do cộng đồng viết tay: khoảng 334 compose, chỉ 54 cho CVE 2024–2026. Attack Range, DetectionLab, Atomic Red Team và Caldera cho *lab có telemetry* và *mô phỏng kỹ thuật ATT&CK*, không dựng môi trường lỗi theo CVE. Mảnh "CVE → env lỗi" chính là phần mà các agent 2025–2026 tự động hóa. Mức chắc chắn: **cao** về chức năng (README), **trung bình** về lý do chậm (suy luận).

### Phát hiện có nguồn
- **Vulhub:** tuyển tập môi trường Docker dựng sẵn; mỗi thư mục có `docker compose up -d` và README hướng dẫn. Tôi đếm từ cây repo (commit cuối 2026-10-18): 334 file docker-compose; 253 nằm trong thư mục có tên CVE; 151 thư mục sản phẩm cấp 1; 54 env cho CVE 2024–2026, trong đó 33 cho 2025–2026. Có env PHP như php/CVE-2024-2961, php/CVE-2019-11043. — [vulhub/vulhub](https://github.com/vulhub/vulhub) (bậc 1, đọc trực tiếp; số đếm tự tính)
- **Splunk Attack Range v5:** dựng lab đám mây có instrument (AWS/Azure/GCP; Splunk, server Windows/Linux, tùy chọn Kali, Zeek) bằng Terraform cộng Ansible, chạy Atomic Red Team để "generate real telemetry", truy cập qua WireGuard; có web app và REST API. — [splunk/attack_range README](https://github.com/splunk/attack_range) (bậc 1, đọc trực tiếp)
- **DetectionLab:** "As of 2023-01-01, DetectionLab is no longer being actively maintained". — [clong/DetectionLab](https://github.com/clong/DetectionLab) (bậc 1, đọc trực tiếp)
- **Atomic Red Team:** thư viện test map theo ATT&CK, badge ghi 1.896 atomic, chạy được trực tiếp hoặc qua Invoke-Atomic. — [redcanaryco/atomic-red-team](https://github.com/redcanaryco/atomic-red-team) (bậc 1, đọc trực tiếp)
- **Caldera:** nền tảng adversary emulation dựa trên ATT&CK, gồm server C2 bất đồng bộ có REST API, web UI và plugin (Atomic, Access, Builder, Caldera for OT…). Badge trong README hiện trỏ sang `apache/caldera`. — [mitre/caldera README](https://github.com/mitre/caldera) (bậc 1, đọc trực tiếp)
- Chuyên gia mất "5–24 hours per CVE" để tái hiện tay (CVE-Factory trích Zhu et al. 2025); paper còn nhắc mức "10+ hours per CVE" (trích Mu et al. 2018). — [CVE-Factory paper](https://github.com/livecvebench/CVE-Factory/blob/main/docs/paper.pdf) (bậc 1, đọc trực tiếp)

### Nhận định
- Vì sao chậm và thủ công: (1) mỗi CVE cần một người đọc advisory, tìm bản lỗi, xử lý dependency drift (ARVO: 63% bản lịch sử không build được nếu không can thiệp) và viết README; (2) độ phủ của Vulhub vài chục CVE mỗi năm, trong khi CVEListV5 có tới 7.152 CVE mới chỉ riêng tháng 12/2025 (CVE-Factory); (3) Atomic/Caldera mô phỏng *kỹ thuật* (hành vi hậu khai thác), nên rule sinh ra bền với biến thể nhưng không trả lời câu "CVE X có để lại dấu vết gì".
- Kiến trúc hợp lý cho doanh nghiệp là ghép hai lớp: agent dựng env theo CVE (CVE-Factory/FORGE) và lab có telemetry kiểu Attack Range. Vulhub dùng làm ground truth và few-shot cho Builder.

### Khoảng trống
- Không lấy được số env chính thức trên vulhub.org (API bị chặn); số trên do tôi đếm file compose.

## 6g. An toàn: cô lập sandbox, egress, PoC độc

### Kết luận ngắn
Các hệ nghiên cứu cô lập ở mức khác nhau. CVE-Genie dùng VM riêng. CVE-Factory dùng Docker-in-Docker cộng proxy và denylist lệnh. FORGE chỉ dùng pod Podman có giới hạn RAM/CPU, không chặn egress. Không hệ nào công bố cơ chế quét PoC độc lấy từ Internet. Thực hành tốt cho lab doanh nghiệp: microVM hoặc VM dùng một lần, egress mặc định chặn (chỉ mở registry gói qua proxy có ghi log), tài khoản/VPC riêng, và tách bước *tải tài nguyên* (cần mạng) khỏi bước *chạy exploit* (không mạng), như CVE-Factory tách Phase 1/Phase 2. Mức chắc chắn: **trung bình**.

### Phát hiện có nguồn
- CVE-Genie chạy mỗi thí nghiệm trong VM cô lập. — [CVE-Genie PDF](https://seclab.bu.edu/people/gianluca/papers/cvegenie-ccs2026.pdf) (bậc 1, snippet)
- CVE-Factory: DinD bắt buộc; Phase 2 (Builder → Checker) "no web-related tools are required"; agent bị cấm đọc/ghi ngoài thư mục làm việc và cấm lệnh nguy hiểm; tool dùng denylist. — [README](https://github.com/livecvebench/CVE-Factory), [paper §3.1](https://github.com/livecvebench/CVE-Factory/blob/main/docs/paper.pdf) (bậc 1, đọc trực tiếp)
- FORGE: pod Podman có `--memory/--cpus`, publish cổng ra host, không chặn egress (xem 6a). — [podman.py](https://github.com/dynatrace-oss/forge/blob/main/src/forge/sandbox/podman.py) (bậc 1, đọc trực tiếp)
- Container dùng chung kernel host nên cô lập yếu hơn gVisor (kernel userspace chặn syscall) và Firecracker/Kata (microVM có kernel khách riêng). — [Fly.io: Firecracker vs gVisor](https://fly.io/learn/firecracker-vs-gvisor/) (bậc 2, snippet)
- AWS khuyến nghị cho lab phân tích mã độc: giả định mẫu sẽ thử thoát, exfiltrate và di chuyển ngang; quản lý egress chặt; VPC riêng trong account riêng; cảnh báo budget, tự động hóa vòng đời, IAM permission boundary. — [AWS Security Blog: Malware analysis on AWS](https://aws.amazon.com/blogs/security/malware-analysis-on-aws-setting-up-a-secure-environment) (bậc 1, snippet)
- Rủi ro PoC giả hoặc chứa mã độc trên GitHub và prompt injection qua advisory đã được ghi ở [agent-poc-va-rui-ro.md](agent-poc-va-rui-ro.md) (câu hỏi phụ 5), không lặp lại ở đây.

### Nhận định
- DinD thường cần container `--privileged`. Nó bảo vệ *daemon Docker của host* khỏi lệnh nhầm của agent, chứ không phải ranh giới bảo mật mạnh trước code độc. Với PoC không tin cậy nên chạy trong microVM hoặc VM dùng một lần.
- Môi trường lỗi bản chất là mục tiêu dễ bị khai thác. Đừng bao giờ publish cổng ra mạng chung, và nên đặt sensor ngay tại ranh giới mạng của sandbox để ghi PCAP, như vậy còn có thêm telemetry cho câu hỏi phụ 7.

### Khoảng trống
- Chưa thấy hệ nào công bố bước "quét PoC trước khi chạy" (scan malware, review tĩnh) hay số liệu về PoC độc gặp phải trong pipeline tự động.

## Truy vấn đã chạy
- Đọc trực tiếp (git clone/raw): dynatrace-oss/forge (README, agents/generator.py, generator/verification.py, sandbox/podman.py, signals/collector.py, oracle_patterns.yaml, forge.yaml, prompts/detector.yaml, SECURITY.md); dynatrace-oss/forge-artifacts (README, knowledge/cookbook, 590 result.sanitized.json → script thống kê); livecvebench/CVE-Factory (README, agents/builder.md, skills/cheat-detect, dev-env, docs/paper.pdf tr. 1–8, 13–27); SEC-bench/SEC-bench và SEC-bench/SecVerifier README; n132/ARVO-Meta README; uiuc-kang-lab/cve-bench README; vulhub/vulhub (cây file); splunk/attack_range, clong/DetectionLab, redcanaryco/atomic-red-team, mitre/caldera README
- WebFetch thất bại (host bị chặn): arxiv.org/html/2509.01835, seclab.bu.edu CVE-Genie PDF, alphaxiv 2509.01835, emergentmind cve-genie, reversinglabs blog
- CVE-Factory arXiv 2602.03012 vulnerability environment (standard)
- CVE-Genie github reproduction Builder docker (standard)
- "CVE-Genie" Builder agent environment reconstruction failure reasons languages (extended)
- CVE-Genie 428 841 CVEs Builder "pre-requisite" setup critic agent time per CVE minutes (extended)
- SEC-bench automated vulnerability benchmark builder agent docker sanitizer reproduction (standard)
- ARVO atlas reproducible vulnerabilities OSS-Fuzz 5000 reproducible cases recompilable (standard)
- LLM agent automatically build vulnerable docker environment CVE github 2026 (extended)
- PatchEval benchmark 230 CVEs docker runtime environment Python JavaScript Go construction (standard)
- detection engineering lab Fortinet Ivanti Citrix vulnerability reproduce virtual appliance image researchers patch diff (extended)
- "Dual-Loop Agent Framework for Automated Vulnerability Reproduction" results (standard)
- watchTowr Rapid7 analysis obtained vulnerable and patched virtual appliance FortiGate VM image patch diffing filesystem encrypted (extended)
- FirmAE firmware emulation success rate IoT vulnerability reproduction (standard)
- LLM agent Linux kernel CVE reproduction syzkaller reproducer automated environment 2026 (extended)
- SEC-bench Pro long-horizon vulnerable fixed image instances languages results (standard)
- CyberGym benchmark 1507 vulnerabilities OSS-Fuzz PoC sanitizer crash oracle patched version (standard)
- running untrusted exploit PoC sandbox microVM Firecracker gVisor egress isolation malware analysis lab best practice (standard)
