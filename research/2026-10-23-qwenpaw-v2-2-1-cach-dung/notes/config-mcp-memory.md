# Cấu hình: file cấu hình, MCP, tools, memory, heartbeat/cron, bảo mật

Ghi chú về phiên bản: tag `v2.2.1` có thật trên GitHub, commit `cae5773` ngày 2026-09-11 ("chore: add release notes for v2.2.1 (#7691)"). Mọi đường dẫn docs/source dưới đây đã đọc trực tiếp từ bản clone `--branch v2.2.1`, nên khớp đúng v2.2.1. Docs gốc nằm trong repo ở `website/public/docs/*.en.md` (site hiển thị tại `https://qwenpaw.agentscope.io/docs/<tên>`).

Viết tắt nguồn:
- DOC-config = [Config & Working Directory, v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/config.en.md)
- DOC-mcp = [MCP & Built-in Tools, v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/mcp.en.md)
- DOC-security = [Security, v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/security.en.md)
- DOC-memory = [Long-Term Memory, v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/memory.en.md)
- DOC-persona = [Agent Persona, v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/persona.en.md)
- DOC-heartbeat = [Heartbeat, v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/heartbeat.en.md)
- DOC-cron = [Scheduled Tasks, v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/cron.en.md)
- DOC-faq = [FAQ, v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/faq.en.md)
- SRC-config = [src/qwenpaw/config/config.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/config/config.py)
- SRC-const = [src/qwenpaw/constant.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/constant.py)
- RN-2.2.1 = [Release notes v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v2.2.1.md)

Tất cả là bậc 1 (docs chính thức/source code), ngày 2026-09-11 (ngày tag), trừ khi ghi khác.

## 1. File cấu hình chính, vị trí, field quan trọng, biến môi trường

### Kết luận ngắn
Cấu hình chia hai lớp: `~/.qwenpaw/config.json` (toàn cục: danh sách agent, browser, security toàn cục, timezone) và `~/.qwenpaw/workspaces/<agent_id>/agent.json` (mỗi agent: channels, MCP, heartbeat, tools, running/memory, security, approval_level). Provider/API key và biến môi trường để riêng trong `~/.qwenpaw.secret/` (`providers.json`, `envs.json`). Có thêm `.env` được tự nạp. Cấu hình tự hot-reload (poll 2 giây). Độ chắc chắn: cao (docs + source cùng bản).

### Phát hiện có nguồn
- Thư mục làm việc mặc định `~/.qwenpaw`; cây gồm `config.json`, `workspaces/<agent_id>/` (chứa `agent.json`, `chats.json`, `jobs.json`, `token_usage.json`, `AGENTS.md`, `SOUL.md`, `PROFILE.md`, `BOOTSTRAP.md`, `MEMORY.md`, `skills/`, `skill.json`, `memory/`, `credentials.yaml`, `drivers/mcp/*.yaml`, `.browser-profile/`…) và `skill_pool/`. Thư mục bí mật `~/.qwenpaw.secret/` chứa `providers.json` (provider + API key) và `envs.json` (biến môi trường) — DOC-config.
- Ưu tiên chọn WORKING_DIR trong source: (1) `QWENPAW_WORKING_DIR` nếu đặt; (2) nếu `~/.copaw` (bản cài CoPaw cũ) tồn tại thì **dùng luôn `~/.copaw`**; (3) mặc định `~/.qwenpaw`. `SECRET_DIR` mặc định là `<WORKING_DIR>.secret` — SRC-const (dòng ~80–110). Docs không nhắc điểm (2).
- `.env`: source nạp `.env` ở gốc repo (khi chạy từ source) rồi `~/.qwenpaw/.env` (bản ở gốc repo được ưu tiên vì `override=False`) — SRC-const (dòng 5–10, 96–101).
- `config.json` toàn cục: `agents.active_agent`, `agents.profiles.<id>` (`id`, `name`, `description`, `enabled`, `workspace_dir`), `last_api.host/port` (mặc định cổng 8088), `show_tool_details`, `user_timezone`, `browser` (`experimental`, `backend`, `identity`, `headless`). Vẫn chấp nhận `channels`, `mcp`, `tools`, `security` để tương thích ngược, nhưng **`agent.json` thắng khi trùng field** — DOC-config.
- `agent.json`: `channels`, `mcp`, `heartbeat`, `mail`, `running`, `active_model` (`provider_id`, `model`; `null` = dùng model mặc định toàn cục), `language`, `system_prompt_files`, `tools.builtin_tools`, `security`, `approval_level` — DOC-config.
- Mặc định trong source: `running.max_iters = 100` (ví dụ JSON trong docs ghi 50, bảng ghi 100), `language = "zh"` (ví dụ ghi "en"), `approval_level = "AUTO"` — SRC-config (dòng 1707, 2311, 2315).
- Field `running` đáng chú ý: `shell_command_timeout` 60s, `shell_command_executable`, `auto_continue_on_text_only`, `llm_max_retries` 3, `llm_max_concurrent` 10 (chung mọi agent), `llm_max_qpm` 600, `max_input_length` 131072 token, `context_manager_backend` "light", `memory_manager_backend` "remelight"; nén context khi đạt `compact_threshold_ratio` 0.8 của `max_input_length` — DOC-config.
- Hot reload: "The system automatically detects `agent.json` changes every 2 seconds". Ghi cấu hình được khoá trong một tiến trình và từ chối bản lưu dựa trên snapshot cũ (HTTP 409); editor ngoài không tham gia khoá này — DOC-config.
- Provider dựng sẵn (ID): `qwenpaw-local`, `ollama` (localhost:11434), `lmstudio` (localhost:1234/v1), `openrouter`, `modelscope`, `dashscope`, `aliyun-codingplan`/`-intl`, `openai`, `azure-openai`, `anthropic`, `gemini`, `deepseek`, `kimi-cn/intl`, `minimax(-cn)`, `zhipu-*`, `opencode`, `siliconflow-cn/intl`, `custom`. Cấu hình bằng `qwenpaw init`, Console (Settings → Models) hoặc API `PUT /providers/{id}`, `PUT /providers/active_llm` — DOC-config.
- Biến môi trường được docs liệt kê: `QWENPAW_WORKING_DIR`, `QWENPAW_SECRET_DIR`, `QWENPAW_KEYRING_ACCOUNT` (tên tài khoản trong keychain hệ điều hành giữ master key), `QWENPAW_CONFIG_FILE`, `QWENPAW_HEARTBEAT_FILE`, `QWENPAW_JOBS_FILE`, `QWENPAW_CHATS_FILE`, `QWENPAW_TOKEN_USAGE_FILE`, `QWENPAW_LOG_LEVEL` (info), `QWENPAW_LOG_MAX_SIZE` (5MiB), `QWENPAW_LOG_MAX_BACKUPS` (3), `QWENPAW_MEMORY_COMPACT_THRESHOLD/KEEP_RECENT/RATIO`, `QWENPAW_REMOTE_IMAGE_DOWNLOAD_MAX_MB`, `QWENPAW_MAX_IMAGE_PIXELS`, `QWENPAW_CONSOLE_STATIC_DIR`, `QWENPAW_LLM_STREAM_FIRST_CONTENT_TIMEOUT` (30), `QWENPAW_LLM_STREAM_IDLE_TIMEOUT` (30), `QWENPAW_AUTH_ENABLED` (false), `QWENPAW_AUTH_USERNAME/PASSWORD`, `QWENPAW_TOOL_GUARD_ENABLED` (true), `QWENPAW_SKILL_SCAN_MODE` (warn). Đọc lúc khởi động, đổi xong phải restart — DOC-config.
- Biến môi trường có trong source nhưng docs config không liệt kê: `QWENPAW_ENABLED_CHANNELS` / `QWENPAW_DISABLED_CHANNELS` (danh sách channel bật/tắt, phân cách bằng dấu phẩy; ENABLED thắng), `QWENPAW_CORS_ORIGINS`, `QWENPAW_UPLOAD_MAX_SIZE_MB`, `QWENPAW_OPENAPI_DOCS` (bật /docs, /redoc), `QWENPAW_BACKUP_DIR` (mặc định `<WORKING_DIR>.backups`), `QWENPAW_TOOL_GUARD_APPROVAL_TIMEOUT_SECONDS` (mặc định 300), `QWENPAW_SHELL_MAX_OUTPUT_BYTES` (10 MiB), `QWENPAW_RUNNING_IN_CONTAINER`, `QWENPAW_DESKTOP_PORT`, `QWENPAW_LLM_MAX_RETRIES`/`_MAX_QPM`/`_MAX_CONCURRENT`…, `QWENPAW_TOOL_GUARD_DENIED_TOOLS`, `QWENPAW_TOOL_GUARD_TOOLS` — SRC-const (dòng 240–410); [config/utils.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/config/utils.py) (dòng ~400–425); [agents/tools/shell.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/tools/shell.py) (dòng 48–50).
- Biến môi trường cho tool/MCP (vd `TAVILY_API_KEY`) quản lý qua `qwenpaw init`, Console hoặc API `GET/PUT/DELETE /envs`, được nạp vào `os.environ` lúc khởi động — DOC-config. v2.2.1 thêm trang Settings quản lý biến môi trường thống nhất cho Agent, MCP, tools và local model (#7538) — RN-2.2.1.
- Một số file runtime không phải cấu hình: `state/last_dispatch.json` (kênh/user cuối, dùng cho heartbeat `target=last`) — DOC-config.

### Nhận định
- **Nhận định:** người dùng cá nhân nên coi `agent.json` là nơi cấu hình chính, `config.json` chỉ cho agent list/browser/sandbox, và không bao giờ đưa `~/.qwenpaw.secret/` hay `credentials.yaml` vào git/backup chia sẻ.
- **Nhận định:** ai từng cài CoPaw cần để ý: nếu còn `~/.copaw`, QwenPaw sẽ dùng thư mục đó, nên sửa `~/.qwenpaw/...` sẽ không có tác dụng. Đặt `QWENPAW_WORKING_DIR` cho rõ ràng.
- **Nhận định:** docs có vài chỗ lệch với source (max_iters 50/100, language en/zh, heartbeat 30m/6h, xem mục 3). Khi nghi ngờ, tin source/Console.

### Khoảng trống
- Chưa đọc schema chi tiết của `providers.json`/`envs.json` (có mã hoá bằng master key trong keychain hay không). Docs chỉ nói `QWENPAW_KEYRING_ACCOUNT` gắn với "master key"; RN-2.2.1 có nhắc "restored secrets and master keys" (#7658).
- Per-agent model routing/fallback mới ở v2.2.1 (#7501) chưa tra field cụ thể. Issue #7749 (2026-09-14, đang mở) hỏi "model failover cấu hình ở đâu", cho thấy docs chưa nói rõ.

## 2. MCP, tools builtin, bật/tắt tool, tool guard / approval / sandbox, bảo mật

### Kết luận ngắn
MCP thêm qua Console (Agent → MCP, dán JSON `mcpServers`), hỗ trợ stdio / streamable_http / sse. Từ v2.0, mỗi MCP client được lưu thành một "driver card" YAML (`workspaces/<id>/drivers/mcp/<name>.yaml`) có access policy riêng (allow/deny/ask, **mặc định ask**). Bảo mật gồm 5 lớp: governance/tool guard, file guard, sandbox (mặc định TẮT), skill scanner, access policy, cộng thêm đăng nhập web tuỳ chọn. Độ chắc chắn: cao.

### Phát hiện có nguồn
- Ba định dạng JSON được nhận khi import MCP: chuẩn `{"mcpServers": {...}}` (khuyên dùng), key-value bỏ wrapper, và một client đơn có `key`. Field: `name`, `description`, `enabled`, `transport` (`stdio`|`streamable_http`|`sse`, tự đoán: có `command` thì là stdio, có `url` thì là http), `url`, `headers`, `command`, `args`, `env`, `cwd`. MCP local cần Node.js 18+ — DOC-mcp.
- Model `MCPClientConfig` trong source còn có các field docs chưa ghi: `http_timeout` (giây, cho HTTP/SSE; mặc định client 30s/300s), `tools` (whitelist tên tool; `None` = nạp hết) và `oauth` — SRC-config (dòng 2456–2483). v2.2.1 thêm timeout kết nối cho MCP HTTP/SSE (#7649), bắt buộc tuân whitelist tool của từng MCP server trên đường runtime (#7504), và khôi phục tương thích với server MCP trả HTTP 401 ở bước discovery (#7627) — RN-2.2.1.
- Ví dụ remote: `{"transport":"streamable_http","url":"https://api.example.com/mcp","headers":{"Authorization":"Bearer ..."}}` — DOC-mcp.
- Chuyển cấu hình cũ: lần khởi động đầu, `mcp.clients` trong `agent.json` được chuyển một lần (one-shot) sang DriverCard; mốc đánh dấu là `mcp.migration_version` (hiện = 2) ghi lại vào `agent.json`. Bước v2 chuyển literal `${VAR}` thành tham chiếu credential `env:`. Đã chuyển rồi thì xoá client sẽ không bị "hồi sinh" lúc khởi động (#6130) — [drivers/adapters/mcp_legacy_config.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/drivers/adapters/mcp_legacy_config.py) (dòng 44–140).
- Ví dụ driver card: `drivers/mcp/hello-mcp.yaml` gồm `name`, `protocol: mcp`, `endpoint{transport, command, args, env}`, trong đó env có thể tham chiếu credential (`source: credential`), cùng `enabled` và `policy{default_effect: ask, rules:[{subject:"*", effect: deny, target:{kind: tool, name: get_secret_status}}]}`. Quản lý trong Console: Agent → MCP → "Tools & Access" — DOC-security.
- Client MCP mặc định trong source: `anysearch` (streamable_http `https://api.anysearch.com/mcp`, header `Bearer ${ANYSEARCH_API_KEY}`, **enabled=False**) — SRC-config (dòng 2550–2570). Mâu thuẫn: DOC-mcp ghi "a `tavily_search` client is automatically created at system startup… auto-enables when `TAVILY_API_KEY` is set". Trong source v2.2.1, Tavily là provider của tool builtin `web_search` (mặc định `tavily`, còn lựa chọn khác là `anysearch`, chọn qua `tools.builtin_tools.web_search.config.provider`) — [agents/tools/websearch/factory.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/tools/websearch/factory.py).
- Tools builtin theo DOC-mcp: `read_file`, `write_file`, `edit_file`, `append_file`, `grep_search`, `glob_search`, `execute_shell_command` (hỗ trợ async, kèm `list_background_tasks`/`get_task_output`/`cancel_task`), `delegate_external_agent` (ACP: claude_code, codex, qwen_code, opencode; mặc định tắt), `browser`, `desktop_screenshot`, `view_image`, `send_file_to_user`, `memory_search`, `get_current_time`, `set_user_timezone`, `get_token_usage`.
- Source v2.2.1 (`@tool_descriptor`) có thêm các tool docs chưa liệt kê: `web_search`, `web_fetch`, `view_video`, `ast_search` (chỉ ở mode coding), `run_tool_batch`, các tool agent (`list_agents`, `chat_with_agent`, `submit_to_agent`, `check_agent_task`, `spawn_subagent`) và `activate_f1_exploration_mode` (mail). Tool `enabled_by_default=False`: `delegate_external_agent`, `append_file` — [src/qwenpaw/agents/tools/ @v2.2.1](https://github.com/agentscope-ai/QwenPaw/tree/v2.2.1/src/qwenpaw/agents/tools).
- Bật/tắt tool: Console Agent → Tools (công tắc từng card, có Enable All/Disable All) hoặc `agent.json` → `tools.builtin_tools.<tên>` với các field `enabled`, `display_to_user`, `async_execution` (chỉ shell), `config` (vd provider của web_search). Mỗi agent có bộ tool riêng. Hot-reload, trừ việc đổi track Browser stable/experimental thì phải restart — DOC-mcp; SRC-config (dòng 2579–2604).
- `approval_level` (trong `agent.json`): STRICT (mọi tool call cần duyệt), SMART (rủi ro thấp tự cho qua, rủi ro cao cần duyệt), AUTO (mặc định; chỉ call bị rule bắt mới cần duyệt), OFF — DOC-security. Source mô tả chi tiết hơn: khi không có finding thì STRICT→ASK, SMART/AUTO/OFF→ALLOW; khi có finding thì STRICT→ASK, SMART: INFO/LOW→ALLOW còn MEDIUM+→ASK, **AUTO/OFF→ASK**. Nghĩa là ở OFF, finding vẫn đòi duyệt, khác câu "all tool calls execute directly" trong docs — [governance/policy.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/governance/policy.py) (dòng 695–725, 985–1005). Khớp với RN-2.2.1: "Require approval for critical security findings unless policy explicitly denies the action" (#7525).
- Tool Guard: rule YAML regex cộng `ShellEvasionGuardian`, chủ yếu cho `execute_shell_command`. Field: `enabled`, `guarded_tools` (null = mọi tool), `denied_tools`, `custom_rules` (id, tools, params, category, severity, patterns, exclude_patterns…), `disabled_rules` (chỉ áp cho `TOOL_CMD_*`), `shell_evasion_checks` (7 check, **mặc định đều false**). Rule builtin gồm `TOOL_CMD_DANGEROUS_RM`, `TOOL_CMD_PIPE_TO_SHELL` (CRITICAL), `TOOL_CMD_PRIVILEGE_ESCALATION` (sudo; CRITICAL), `TOOL_CMD_SYSTEM_TAMPERING` (crontab, authorized_keys)… CRITICAL/HIGH vào luồng chờ duyệt trong Console. Ở ngữ cảnh không tương tác, finding chỉ được ghi log, nên muốn chặn hẳn thì dùng `denied_tools` — DOC-security.
- Timeout chờ duyệt mặc định 300 giây (`QWENPAW_TOOL_GUARD_APPROVAL_TIMEOUT_SECONDS`), hết hạn thì từ chối — SRC-const (dòng 395–407); DOC-security ("If no response within the timeout period, the invocation is rejected").
- File Guard: chạy trên mọi tool call kể cả khi tool guard tắt, chặn theo `sensitive_files` (đường dẫn kết thúc `/` nghĩa là chặn đệ quy). Mặc định bảo vệ `~/.qwenpaw.secret/` — DOC-security.
- Sandbox: macOS dùng Seatbelt; Linux dùng bubblewrap (ưu tiên), rồi Landlock (kernel 5.13+), rồi none; Windows dùng AppContainer/Restricted_token. Mô hình whitelist: workspace ghi được, `deny_paths` mặc định gồm `~/.ssh`, `~/.aws`…, `allow_read_all=true`, mạng mặc định mở `["*"]`. Mount không sửa tay mà sinh ra từ rule trong `policy.yaml` (vd `user_rules: - match: Write(~/.cache/uv/**) action: allow`). `uv`/`pip`/`npm` sẽ lỗi trong sandbox nếu chưa cấp quyền thư mục cache, và đường dẫn phải tồn tại trước khi sandbox khởi động. Trong Docker thường rơi về `mode=none`, tức không cô lập gì. Kiểm tra bằng log `qwenpaw.log`, tìm dòng `governance decision: ... sandbox=bubblewrap` — DOC-security.
- Sandbox **mặc định tắt**: `security.sandbox_enabled: bool = False` trong `config.json` toàn cục ("When False, such calls run directly without the sandbox"). Đọc lỗi config thì fail-safe sang bật — SRC-config (dòng 2942–2960); [governance/resource_governor.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/governance/resource_governor.py) (dòng 130–155).
- `policy.yaml` nằm ngoài workspace để agent không sửa được: `~/.qwenpaw/governance/<tên-workspace>_<sha256[:12]>/policy.yaml` — resource_governor.py (dòng 92–107).
- Skill Scanner: chế độ `block`/`warn` (mặc định)/`off`, timeout 30s, whitelist theo SHA-256 nội dung. Thứ tự ưu tiên: env `QWENPAW_SKILL_SCAN_MODE` > Console > `config.json` — DOC-security.
- Web auth: tắt mặc định; bật bằng `QWENPAW_AUTH_ENABLED=true`, chạy một admin duy nhất, token HMAC hạn 7 ngày, `auth.json` quyền 0600. Request từ localhost (`allow_no_auth_hosts`: 127.0.0.1, ::1) bỏ qua xác thực. Có `trusted_proxies` cho reverse proxy — DOC-security; SRC-config (dòng 2961–2975).
- Chỗ lệch trong docs: DOC-security nói cấu hình security nằm trong `config.json`, còn DOC-config đặt `security` trong `agent.json`. Source có `security` ở cả `Config` lẫn `AgentProfileConfig` (SRC-config dòng 2333). Riêng `sandbox_enabled` được đọc từ `config.json` toàn cục.

### Nhận định
- **Nhận định:** với một máy cá nhân trên Linux, cấu hình hợp lý là giữ AUTO, bật `security.sandbox_enabled=true` (cài `bwrap`), cấp `Write(~/.cache/...)` trong `policy.yaml` cho các package manager, thêm `denied_tools` cho tool không cần, và đặt access policy MCP tin cậy là `allow` để khỏi phải duyệt liên tục (docs gợi ý đúng như vậy cho dùng cá nhân).
- **Nhận định:** sau khi lên v2.x, sửa `mcp.clients` trong `agent.json` có thể không còn tác dụng vì nguồn sự thật đã chuyển sang `drivers/mcp/*.yaml`. Nên quản lý MCP qua Console. Điểm này suy ra từ logic migration one-shot, chưa test.
- **Nhận định:** không nên expose cổng 8088 ra mạng khi chưa bật `QWENPAW_AUTH_ENABLED`, và không thêm IP ngoài vào `allow_no_auth_hosts`.

### Khoảng trống
- Chưa xác minh được việc sửa trực tiếp `mcp.clients` trong `agent.json` sau migration có còn được runtime đọc hay không (chưa đọc hết DriverManager).
- Chưa có schema đầy đủ của `policy.yaml` (`builtin_rules`/`user_rules`, cú pháp `Read()`/`Write()`/`Bash()`). Docs chỉ có một ví dụ.

## 3. Memory, persona files, heartbeat, cron

### Kết luận ngắn
Memory mặc định dùng backend `remelight` (ReMe, chạy trong tiến trình), lưu dạng file Markdown trong workspace: `MEMORY.md` (lõi, do người dùng/agent tự viết, không nạp vào system prompt), `memory/YYYY-MM-DD/*.md` (Auto-Memory, mặc định sau mỗi 5 lượt user) và `digest/` (Auto-Dream, cron 23:00). Persona là `AGENTS.md`/`SOUL.md`/`PROFILE.md` (+ `BOOTSTRAP.md` chỉ dùng lần đầu), chọn bằng `system_prompt_files`. Heartbeat đọc `HEARTBEAT.md` theo chu kỳ. Cron lưu trong `jobs.json`, quản lý bằng Console/CLI/chat. Độ chắc chắn: cao.

### Phát hiện có nguồn
- Persona: `AGENTS.md` (quy trình, quy tắc, cách dùng memory/tool/heartbeat), `SOUL.md` (giá trị, giọng điệu, ranh giới), `PROFILE.md` (danh tính agent và hồ sơ người dùng). `BOOTSTRAP.md` tạo lúc `qwenpaw init`, dẫn cuộc trò chuyện làm quen đầu tiên rồi tự xoá. Mặc định `system_prompt_files: ["AGENTS.md","SOUL.md","PROFILE.md"]`, thứ tự trong mảng là thứ tự ghép vào prompt; mảng rỗng thì rơi về "You are a helpful assistant". Có thể thêm bất kỳ file .md nào và bật trong Console Agent → Workspace (kéo thả để đổi thứ tự). Hot-reload — DOC-persona.
- Cảnh báo: đổi `language` của agent trong Console (Agent → Runtime Config) sẽ **ghi đè** AGENTS/SOUL/PROFILE bằng template ngôn ngữ mới. Ngôn ngữ template: `zh`/`en`/`ru`; `qwenpaw init --defaults` dùng `zh` — DOC-persona.
- System prompt gồm: Agent Identity (agent id), nội dung persona, rồi context runtime (giờ/timezone, workspace, danh sách tool, danh sách skill kèm name+description) — DOC-persona.
- QA Agent dựng sẵn (ID `QwenPaw_QA_Agent_0.2`), skill `guidance` + `QA_source_index`, chỉ bật tool lõi. Xoá đi thì `qwenpaw init` tạo lại — DOC-persona.
- `MEMORY.md` "not loaded into the system prompt by default"; agent đọc nó bằng `memory_search` hoặc `read_file` — DOC-persona. Auto-Memory và Auto-Dream không ghi đè `MEMORY.md` — DOC-memory.
- Cấu trúc memory của ReMe: `memory/YYYY-MM-DD.md` (trang index tự sinh, khối `<!-- notes:auto -->`), `memory/YYYY-MM-DD/<name>.md` (mỗi session một note), `digest/{personal,procedure,wiki}/` (tri thức bền, có Wikilink `[[...]]`), `mem_session/` (hội thoại nguồn dạng JSONL), `resource/` (PDF…), `mem_metadata/` (index, có thể dựng lại). "Markdown files are the source of truth" — DOC-memory.
- Field `running.reme_light_memory_config`: `auto_memory_interval` 5, `dream_cron_enabled` true / `dream_cron` "0 23 * * *" (trễ ngẫu nhiên 0–60s), `daily_paper_cron_enabled` false ("0 9 * * *"), `auto_fin_cron_enabled` false ("0 18 * * *"), `memory_search_enabled` true, `auto_memory_search_config.enabled` **false** (max_results 2), `*_inbox_push_enabled` true — DOC-memory; DOC-config.
- Embedding (`embedding_model_config`): backend `openai`/`dashscope`/`dashscope_multimodal`/`gemini`/`ollama`, `dimensions` 1024, `use_dimensions` false. Vector search chỉ bật khi đủ `model_name`+`api_key` (riêng Ollama chỉ cần `model_name`); thiếu thì vẫn còn BM25 và đồ thị wikilink. Đổi backend/model/dimensions sẽ đặt `needs_reindex=true`, phải rebuild bằng Console hoặc `POST /api/agents/{agentId}/memory/reindex?scope=all|bm25|embedding`, hoàn tác bằng `.../reindex/undo` — DOC-config; DOC-memory.
- Lệnh chat liên quan memory: `/memorize`, `/new`, `/compact`, `/auto_memory_status` — DOC-memory; `/compact`, `/system_prompt` — [Release notes v2.0.0](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v2.0.0.md).
- Backend khác: `powercontext` (plugin, phải tự chạy PowerContext Server, mặc định `http://127.0.0.1:8000`, cấu hình trong `running.memory_backend_configs.powercontext`), ADBPG (plugin), `none` (tắt hẳn memory, từ v2.0) — DOC-memory; RN-2.2.1 (#7080, #7561); release notes v2.0.0 (#5732).
- Heartbeat: file `workspaces/<agent_id>/HEARTBEAT.md` (đổi tên bằng `QWENPAW_HEARTBEAT_FILE`); cả nội dung file được gửi như một tin nhắn user. Cấu hình `agent.json` → `heartbeat`: `enabled` (mặc định false), `every` (chuỗi khoảng `30m`/`1h`/`2h30m`/`90s` **hoặc cron 5 trường**), `target` (`main` = không gửi đi đâu; `last` = gửi về kênh/session nói chuyện gần nhất; `inbox`), `timeoutSeconds` 300 (1–3600), `activeHours {start,end}`. Console: Control → Heartbeat — DOC-heartbeat.
- Mặc định `every` trong source là `"6h"` (`HEARTBEAT_DEFAULT_EVERY = "6h"`) — SRC-const (dòng 218); SRC-config (dòng 678–696). DOC-heartbeat cũng ghi "about 6 hours", còn ví dụ/bảng trong DOC-config ghi `"30m"`.
- Cron: hai kiểu, recurring (cron 5 trường, không có giây) và calendar (`--run-at`, lặp theo ngày, kết thúc theo `count`/`until`/`never`). Loại nội dung `text` (gửi text cố định) hoặc `agent` (hỏi agent rồi gửi câu trả lời). Mỗi job có channel, target user, target session; có tuỳ chọn shared session, Inbox, `--silent` (chỉ cho agent job), max concurrency/timeout/grace. CLI: `qwenpaw cron list|create|state|run|pause|resume|delete`. Có thể tạo bằng cách nhắn chat ("tạo task nhắc uống nước mỗi 5 phút") hoặc từ template. Sửa/xoá job thì phải disable trước. Timezone mặc định theo `user_timezone` — DOC-cron; DOC-config.
- Mỗi cron job có cờ riêng để yêu cầu hoặc bỏ qua duyệt tool (#5847) — [Release notes v2.0.0](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v2.0.0.md).
- Heartbeat và cron khác nhau ở chỗ: heartbeat chỉ có một file và một chu kỳ, gửi tới kênh cuối hoặc không gửi; cron có nhiều job, mỗi job lịch và đích riêng — DOC-heartbeat.

### Nhận định
- **Nhận định:** muốn agent "nhớ" chủ động thì bật `auto_memory_search_config.enabled` (đang mặc định tắt) và cấu hình embedding (mặc định không có vector). Không làm hai việc này thì chỉ có BM25 và memory_search thủ công.
- **Nhận định:** Auto-Memory, Auto-Dream, Daily Paper đều gọi model của agent, nên tốn token nền. Với model trả phí, nên cân nhắc tăng `auto_memory_interval` hoặc tắt các cron phụ.
- **Nhận định:** trước khi đổi language, tải workspace về (ZIP) để khỏi mất persona tự viết.

### Khoảng trống
- Chưa kiểm chứng format `jobs.json` hay field `heartbeat.target="inbox"` trong source (docs heartbeat có nhắc, bảng trong docs config thì không).
- Chưa rõ khi nào persona hoặc `MEMORY.md` được agent tự cập nhật (phụ thuộc chỉ dẫn trong AGENTS.md).

## 4. Mẹo vận hành, lỗi cấu hình thường gặp (issues)

### Kết luận ngắn
Các lỗi hay gặp: model local có context quá nhỏ, MCP mất session sau khi idle (đã sửa ở v2.1), popup duyệt vẫn hiện ở OFF với MCP (đã sửa ở v2.0), model chọn bị mất (v2.2.1, đang mở), output cron bị gập trong UI, context vượt giới hạn provider khi turn dài nhiều tool (đang mở). Độ chắc chắn: trung bình. Các issue là nguồn bậc 1 về hiện tượng nhưng nhiều cái chưa có kết luận.

### Phát hiện có nguồn
- Model local qua Ollama/LM Studio: phải đặt context length **≥ 32K**, nếu không agent quên lệnh, gãy multi-turn hay gọi tool sai — DOC-faq.
- Lỗi 401 "You didn't provide an API key": thường do chưa nhập key, hoặc sai `base_url`, key bị dư khoảng trắng, tên model sai hoa thường. Console có in đường dẫn file chi tiết lỗi (`qwenpaw_query_error_*.json`) để đính kèm khi báo issue — DOC-faq.
- Cron không chạy: kiểm tra service đang chạy, job ở trạng thái Enabled, Dispatch Channel đúng, User ID/Session ID khớp với Control → Sessions, biểu thức cron đúng, rồi thử "Execute Now" — DOC-faq.
- [#6732 MCP tools fail intermittently](https://github.com/agentscope-ai/QwenPaw/issues/6732) (bậc 1, mở 2026-08-06, đóng 2026-08-11): trên v2.0.1, session MCP bị server cắt sau khi idle (`McpError: Session terminated`, chỉ hiện ở log DEBUG), tool "biến mất". PR #6894 thêm tự kết nối lại (có từ v2.1.0). Workaround cũ: restart, hoặc tắt server lỗi. Mẹo: đặt `QWENPAW_LOG_LEVEL=debug` khi điều tra lỗi MCP.
- [#5846 approval popup in OFF mode](https://github.com/agentscope-ai/QwenPaw/issues/5846) (bậc 1, 2026-07-08, v2.0.0b3): OFF là thiết lập theo session; popup vẫn hiện khi dùng MCP là bug, đã sửa qua PR #5864. Liên quan: release notes v2.0.0 có "Session-level tool approval: Override global tool policy per session" (#5685).
- [#7708 configured LLM lost](https://github.com/agentscope-ai/QwenPaw/issues/7708) (bậc 1, mở 2026-09-11, v2.2.1 desktop Windows, đang mở): model chọn ở dropdown trang Chat bị mất. Collaborator khuyên đặt provider/model mặc định ở trang Models (2026-09-14).
- [#7709 cron tasks often produce no output](https://github.com/agentscope-ai/QwenPaw/issues/7709) (bậc 1, mở 2026-09-11, v2.2.1 pip/WSL, đang mở): maintainer giải thích UI chỉ giữ tin nhắn text cuối, phần còn lại gập vào "execution steps". Chỉnh trong Personalization (expand all / chỉ hiện kết quả cuối).
- [#7628 context compaction can exceed provider budget](https://github.com/agentscope-ai/QwenPaw/issues/7628) (bậc 1, mở 2026-09-08, đang mở tới ít nhất 2026-09-25): compaction chỉ tính phần hội thoại, không tính system prompt và schema tool, nên turn dài nhiều tool lỗi `CONTEXT_UNFIT` (vd 313,235 token so với giới hạn 267,904). Người góp ý quan sát thấy reasoning chiếm khoảng 81% request quá cỡ. Lỗi vẫn còn trên v2.2.1–v2.2.2b3.
- [#7749 model failover config location](https://github.com/agentscope-ai/QwenPaw/issues/7749) (bậc 1, mở 2026-09-14): người dùng không tìm thấy chỗ cấu hình failover (thông tin từ danh sách issue, chưa mở chi tiết).
- Sandbox: `uv`/`pip`/`npm` lỗi vì không ghi được cache ngoài workspace, phải thêm rule `Write(~/.cache/...)` và tạo sẵn thư mục. Trong Docker, user namespace bị tắt nên bwrap không chạy, rơi về Landlock hoặc none — DOC-security.
- MCP Tavily qua `npx -y tavily-mcp@latest` hoặc MCP local nói chung cần Node 18+ — DOC-mcp.
- Bật ít tool thôi để giảm context ("enable only the tools you need to reduce context overhead") — DOC-mcp.
- v2.2.1 sửa "Preserve Unix permission bits for restored secrets and master keys" (#7658): backup/restore ở bản cũ hơn có thể làm hỏng quyền file bí mật — RN-2.2.1.

### Nhận định
- **Nhận định:** checklist vận hành: (1) đặt model mặc định ở Settings → Models, đừng chỉ chọn ở dropdown Chat; (2) với model local, context ≥ 32K; (3) giảm số tool/MCP bật để tiết kiệm context, tránh #7628; (4) gặp lỗi MCP thì bật log debug; (5) cron gửi về kênh nào thì đặt user/session ID đúng của kênh đó; (6) backup `~/.qwenpaw` + `~/.qwenpaw.secret` riêng và cất cho an toàn.

### Khoảng trống
- Không dùng được GitHub search API (proxy chặn GraphQL/search), chỉ duyệt được trang 1 danh sách issue qua WebFetch nên có thể sót issue liên quan heartbeat/sandbox/env.
- Chưa có nguồn cộng đồng bậc 2 (blog, bài hướng dẫn) về cấu hình. Web search không ra kết quả nào cho QwenPaw.

## Truy vấn đã chạy
- git clone --branch v2.2.1 agentscope-ai/QwenPaw; đọc docs/source (standard)
- gh search issues / gh api search/issues "MCP", "sandbox", "heartbeat", "memory", "config", "approval", "cron" (bị chặn 403)
- WebFetch github.com/agentscope-ai/QwenPaw/issues?q=is:issue MCP sort:comments-desc (standard)
- WebFetch issues?q=is:issue created:>2026-09-10 sort:comments-desc (standard)
- WebSearch "QwenPaw issue MCP sandbox approval config github" (standard; không có kết quả liên quan)
- WebFetch issues #6732, #7628, #7709, #7708, #5846
