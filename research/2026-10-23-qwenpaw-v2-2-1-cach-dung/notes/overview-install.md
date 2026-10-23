# Tổng quan, phiên bản v2.2.1, cài đặt và dùng hằng ngày

Ghi chú chung về nguồn: site docs `qwenpaw.agentscope.io`, `help.aliyun.com`, `aibase.com`, `ithome.com` không resolve DNS từ môi trường research (lỗi `ENOTFOUND`), nên tài liệu chính thức được đọc trực tiếp từ file markdown trong repo (`website/public/docs/*.en.md`), ưu tiên **tag `v2.2.1`**; chỗ nào chỉ đọc được ở nhánh `main` (đang là v2.2.2.post1) thì ghi rõ.

## 1. QwenPaw là gì, quan hệ CoPaw/AgentScope, v2.2.1 và các thay đổi v2.x

### Kết luận ngắn
v2.2.1 có thật: bản stable phát hành 2026-09-11 trên PyPI (README ghi 2026-09-10), sau v2.2.0 (2026-09-03); hiện đã có bản mới hơn là v2.2.2 (2026-10-15) và v2.2.2.post1 (2026-10-22). QwenPaw là tên mới của CoPaw (đổi tên tháng 4/2026 ở bản 1.1.0), do team AgentScope làm, chạy trên AgentScope 2.x. Mức chắc chắn: **cao** (PyPI, GitHub releases, source code).

### Phát hiện có nguồn
- QwenPaw = "Qwen Personal Agent Workstation", trợ lý AI cá nhân chạy local hoặc cloud, có Skills, Plugins, nhiều channel nhắn tin; license Apache 2.0; do team AgentScope xây dựng, cùng hệ với AgentScope, AgentScope Runtime, ReMe — [README QwenPaw](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/README.md) (bậc 1, truy cập 2026-10-23)
- Docs intro (tag v2.2.1): "a personal assistant that runs in your own environment"; mỗi agent có "its own workspace, configuration, memory, skills, and conversation history"; skill pool là kho dùng chung, workspace skill là bản copy agent thực sự dùng; heartbeat gửi câu hỏi định sẵn theo chu kỳ — [intro.en.md @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/intro.en.md) (bậc 1, 2026-09)
- Đổi tên: CoPaw đổi thành QwenPaw khi phát hành 1.1.0, IT之家 đưa tin ngày 2026-04-12; "Qwen" chỉ việc gia nhập hệ sinh thái mã nguồn mở Tongyi Qianwen, "Paw" giữ định vị bạn đồng hành — [IT之家](https://www.ithome.com/0/938/334.htm), [AIbase](https://www.aibase.com/news/27047) (bậc 2, 2026-04; chỉ đọc được qua snippet tìm kiếm, không mở được trang). Alibaba Cloud Model Studio docs mô tả QwenPaw "formerly CoPaw" — [help.aliyun.com/en/model-studio/qwenpaw](https://help.aliyun.com/en/model-studio/qwenpaw) (bậc 1, chỉ qua snippet, không mở được)
- Dấu vết CoPaw trong code v2.2.1: nếu không đặt `QWENPAW_WORKING_DIR` mà `~/.copaw` tồn tại thì dùng luôn `~/.copaw` làm working dir ("legacy installation → use it as-is"); có `LEGACY_QA_AGENT_ID = "CoPaw_QA_Agent_0.1beta1"` bị tắt khi migration — [src/qwenpaw/constant.py @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/src/qwenpaw/constant.py) (bậc 1, 2026-09)
- FAQ: nâng cấp từ CoPaw không cần bước migration; config, memory, skills thời CoPaw vẫn dùng được — [faq.en.md @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/faq.en.md) (bậc 1, 2026-09)
- Lịch phát hành trên PyPI: 2.2.0b1 (2026-08-27) … 2.2.0 (2026-09-03); 2.2.1b1 (09-08), 2.2.1b2 (09-10), **2.2.1 (2026-09-11)**; 2.2.2b1 (09-17) … 2.2.2 (10-15), 2.2.2.post1 (10-22, bản hiện tại). Requires-Python `<3.14, >=3.11`, maintainer "agentscope" — [PyPI qwenpaw](https://pypi.org/project/qwenpaw/#history) (bậc 1, truy cập 2026-10-23); README ghi v2.2.1 là 2026-09-10 — [README](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/README.md) (bậc 1). Lệch 1 ngày, có thể do múi giờ (UTC vs UTC+8).
- Issue release-duty #7692 mở 2026-09-11 để kiểm tra cài v2.2.1 trên PyPI (`pip install qwenpaw==2.2.1`), Docker, macOS desktop, Windows desktop; đóng cùng ngày nhưng checklist không ghi kết quả — [Issue #7692](https://github.com/agentscope-ai/QwenPaw/issues/7692) (bậc 1, 2026-09-11)
- **Changelog v2.2.1** (so với v2.2.0) — [Releases](https://github.com/agentscope-ai/QwenPaw/releases), [Release v2.2.1](https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.2.1) (bậc 1, 2026-09-11):
  - Added: per-Agent model routing ("Configure model routing separately for each Agent, including provider preferences and fallback behavior"); Auto Fin (tự review memory) và nâng cấp ReMe (beta.1 ghi ReMe 0.4.1.11); PowerContext làm memory backend tùy chọn; guardrail mạnh hơn cho agent builtin; Creator 1.2.0 (blueprint workbench, deploy Docker); quản lý biến môi trường hợp nhất; phát hiện cập nhật plugin và PawApp; thiết kế lại Console (sidebar, Settings, điều hướng tùy biến); Skill preloading, nâng cấp Make Skill, hiển thị version skill; timeout MCP HTTP/SSE cấu hình được.
  - Changed: các memory backend tự động dùng chung một lifecycle/action interface; chuẩn hóa màu Console; Agent selector tốt hơn trên màn nhỏ.
  - Fixed: race condition khi streaming và gửi xếp hàng; "Require approval for critical security findings unless policy explicitly denies the action"; enforce allowlist tool MCP ở runtime; xử lý PDF cho model chỉ text; context folding cho thinking đã dùng; tương thích MCP 401 cũ; gửi media base64 qua channel.
  - beta.2 thêm: kiểm tra version và dependency của skill, fallback khi memory plugin không có.
- **v2.2.0 (2026-09-03)**: QwenPaw Hub (self-host nhiều người dùng, runtime local-process hoặc Docker, phân quyền workspace, quản lý credential, reverse proxy); QwenPaw Data (PawApp native, workspace phân tích lâu dài); QwenPaw Mail (theo dõi mail, tìm kiếm, hành động theo thread, allow/deny người gửi, cần người duyệt khi gửi tới người lạ; Mail MCP đi kèm desktop app); provider mới Volcengine Agent Plan, MiMo V2.5; routing theo năng lực model, fallback policy, điều khiển thinking; nhóm hội thoại subagent trong Console; marketplace hợp nhất app/plugin/skill và đổi tên "Marketplace" thành "Extensions"; bật/tắt skill hàng loạt; AnySearch làm web search provider; đổi embedding model thì fallback về BM25 tới khi reindex xong; AgentScope lên 2.0.7.post1 — [Release v2.2.0](https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.2.0) (bậc 1, 2026-09-03)
- Hub: cài `pip install -U "qwenpaw[hub]"`, chạy `qwenpaw hub --host 127.0.0.1 --port 8000`, tài khoản đăng ký đầu tiên là admin; runtime Local cần `bwrap` (Linux) / `sandbox-exec` (macOS); Docker mặc định 2 CPU, 4096 MiB RAM; docs nói Hub 2.2.0 chỉ dành cho team tin nhau, không chạy làm dịch vụ public multi-tenant — [hub.en.md @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/hub.en.md) (bậc 1, 2026-09)
- Mốc v2.x khác theo README: v2.0.1 (2026-07-24) PawApp, Agent Modes, plugin Oh-My-Paw; v2.1.0 (2026-08-13) OS Shell, Files workspace, Creator, tích hợp Codex/Qoder, Browser-use, Computer-use, checkpoint workspace — [README](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/README.md) (bậc 1)
- v2.0.0 (2026-07-10): kernel refactor trên AgentScope 2.0; memory thay bằng ReMe v0.4.0; history SQLite có full-text search, giữ 30 ngày mặc định; desktop chuyển Electron → Tauri; TUI `qwenpaw tui`; policy engine allow/deny/ask và sandbox (Windows AppContainer, Linux bubblewrap); `preserve_thinking` đổi tên `relay_reasoning`; bỏ Plan Mode (`plan_mode`) — [Release v2.0.0](https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.0.0) (bậc 1, 2026-07-10)
- Sau v2.2.1: v2.2.2 (2026-10-15) thêm theme Console, terminal nhiều tab trong Chat, Hub model gateway với token budget theo thành viên, PawPort (import hội thoại, memory, skills, plugins, MCP từ Codex/Qoder), tool `view_audio`; `/reme <action> key=value` thay `/dream`, `/memorize`, `/reme_status`. v2.2.2.post1 (2026-10-22): vá CA trust, Node.js 22.23.4 — [Releases](https://github.com/agentscope-ai/QwenPaw/releases) (bậc 1)

### Nhận định
- **Nhận định:** v2.2.1 là bản "nhỏ" so với v2.2.0: phần lớn là per-agent model routing, memory (Auto Fin, PowerContext) và Console; các tính năng lớn Hub/Mail/Data đã có từ v2.2.0. Người cài mới hôm nay sẽ mặc định nhận 2.2.2.post1, muốn đúng v2.2.1 phải pin `qwenpaw==2.2.1` (hoặc `--version 2.2.1` với script, tag Docker tương ứng nếu có).
- **Nhận định:** Ai đã dùng CoPaw thì QwenPaw sẽ tự dùng tiếp `~/.copaw` nếu thư mục đó còn, nên tài liệu "~/.qwenpaw" có thể không đúng với máy đó.

### Khoảng trống
- Không mở được trang IT之家/AIbase/help.aliyun (DNS), nên ngày đổi tên chỉ có từ snippet (bậc 2).
- Không xác nhận được tag Docker `agentscope/qwenpaw:2.2.1` có tồn tại (chưa kiểm Docker Hub).

## 2. Cài đặt và chạy

### Kết luận ngắn
Cài qua pip (Python 3.11–3.13), script một dòng (tự lo uv/venv), Docker (`agentscope/qwenpaw`), desktop app Tauri (Windows 10+/macOS 14+), hoặc dùng không cài trên AgentScope Platform/ModelScope Studio/Alibaba ECS. Chạy `qwenpaw init --defaults` rồi `qwenpaw app`, Console ở `http://127.0.0.1:8088/`; dữ liệu ở `~/.qwenpaw` và secret ở `~/.qwenpaw.secret`. Mức chắc chắn: **cao** (docs ở tag v2.2.1 + source).

### Phát hiện có nguồn
- **pip**: `pip install qwenpaw` (Python ≥3.11, <3.14, nên dùng venv) — [quickstart.en.md](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/website/public/docs/quickstart.en.md) (bậc 1, nhánh main, 2026-10)
- **Script**: `curl -fsSL https://qwenpaw.agentscope.io/install.sh | bash` (macOS/Linux), rồi mở terminal mới hoặc `source ~/.zshrc`/`~/.bashrc`; Windows `irm https://qwenpaw.agentscope.io/install.ps1 | iex` hoặc bản `.bat`; chọn version `... | bash -s -- --version <x>`, `--from-source` cho dev; nâng cấp = chạy lại script; gỡ: `qwenpaw uninstall` (giữ config/data) hoặc `qwenpaw uninstall --purge` — [quickstart.en.md](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/website/public/docs/quickstart.en.md), [README](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/README.md) (bậc 1)
- **Docker**: tag `latest` (stable), `pre` (pre-release), có mirror ACR Alibaba cho người ở Trung Quốc:
  ```bash
  docker run -p 127.0.0.1:8088:8088 \
    -v qwenpaw-data:/app/working \
    -v qwenpaw-secrets:/app/working.secret \
    -v qwenpaw-backups:/app/working.backups \
    agentscope/qwenpaw:latest
  ```
  API key qua `-e DASHSCOPE_API_KEY=xxx` hoặc `--env-file .env`; nâng cấp = pull image mới và restart — [quickstart.en.md](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/website/public/docs/quickstart.en.md), [faq.en.md @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/faq.en.md) (bậc 1)
- **Desktop (Beta)**: file `QwenPaw-Tauri-<version>-Windows-setup.exe` / `QwenPaw-Tauri-<version>-macOS.zip` trên GitHub Releases; macOS lần đầu chuột phải → Open; khởi động lần đầu 10–60 giây; có updater tích hợp — [quickstart.en.md](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/website/public/docs/quickstart.en.md), [faq @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/faq.en.md) (bậc 1)
- Không cần cài: AgentScope Platform (platform.agentscope.io), ModelScope Studio (cảnh báo phải để Studio non-public "Otherwise, others may be able to control your QwenPaw"), Alibaba Cloud ECS qua Compute Nest — [quickstart.en.md](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/website/public/docs/quickstart.en.md) (bậc 1)
- Nâng cấp pip: `qwenpaw update`; từ source: `git pull`, build console (`npm ci && npm run build`), copy vào `src/qwenpaw/console/`, `pip install -e .` — [faq @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/faq.en.md) (bậc 1)
- **Chạy lần đầu**: `qwenpaw init --defaults` (hoặc `qwenpaw init` tương tác, `--force` ghi đè) → `qwenpaw app` (mặc định 127.0.0.1:8088) → mở Console → **bắt buộc** cấu hình model ở Settings → Models và đặt Default LLM → thử Chat. Kiểm tra API:
  `curl -N -X POST "http://localhost:8088/api/console/chat" -H "Content-Type: application/json" -d '{"input":[{"role":"user","content":[{"type":"text","text":"Hello"}]}],"session_id":"session123"}'` — [quickstart.en.md](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/website/public/docs/quickstart.en.md) (bậc 1)
- **Giao diện**: `qwenpaw app` (web Console), `qwenpaw` / `qwenpaw tui` (TUI toàn màn hình, `--agent <id>`, `--resume <id>`), `qwenpaw .` (TUI Coding Mode trong repo hiện tại) — [README](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/README.md), [cli.en.md](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/website/public/docs/cli.en.md) (bậc 1, nhánh main)
- **Lệnh CLI chính** (docs nhánh main) — [cli.en.md](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/website/public/docs/cli.en.md) (bậc 1, 2026-10):
  - Option chung `--host` (mặc định `127.0.0.1`), `--port` (mặc định `8088`).
  - `qwenpaw app --host --port --reload --log-level`; `qwenpaw desktop`, `shutdown`, `update`, `uninstall`.
  - `qwenpaw doctor [--deep]` và `doctor fix [--dry-run]`; `qwenpaw daemon status|restart|reload-config|version|logs [-n N]`.
  - `qwenpaw models list|config|config-key [provider]|set-llm|download <repo_id> [-s huggingface|modelscope]|local|remove-local`.
  - `qwenpaw env list|set KEY VALUE|delete KEY`.
  - `qwenpaw channels list|send|config|install|add|remove`.
  - `qwenpaw agents list|create (--name --template --skill --provider-id --model-id)|delete|chat (--to-agent --text --mode final|stream --background)`.
  - `qwenpaw chats ...`, `qwenpaw cron list|create|pause|resume|run ...`, `qwenpaw skills install <url> [--pool|--agent-id]|list|enable|disable|info|test`, `qwenpaw plugin install|list|...`, `qwenpaw clean [--dry-run]`, `qwenpaw auth reset-password`, `qwenpaw acp`.
- **Thư mục làm việc** (tag v2.2.1): working dir mặc định `~/.qwenpaw` (đổi bằng `QWENPAW_WORKING_DIR`); secret dir mặc định `<WORKING_DIR>.secret` tức `~/.qwenpaw.secret` (đổi bằng `QWENPAW_SECRET_DIR`; Docker `/app/working.secret`) — [config.en.md @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/config.en.md), [constant.py @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/src/qwenpaw/constant.py) (bậc 1)
- **Bố cục file** (config.en.md, đọc ở nhánh main; các biến môi trường đã đối chiếu với tag v2.2.1) — [config.en.md](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/website/public/docs/config.en.md) (bậc 1):
  - `~/.qwenpaw/config.json` (global: `agents.active_agent`, `agents.profiles`, `last_api.host/port`, `show_tool_details`, `user_timezone`), `workspaces/<agent_id>/`, `skill_pool/`.
  - `workspaces/<agent_id>/agent.json` (`channels`, `mcp`, `mail`, `heartbeat`, `running`, `active_model`, `language`, `system_prompt_files`, `tools`, `security`, `approval_level`), `chats.json`, `jobs.json`, `token_usage.json`, `AGENTS.md`, `SOUL.md`, `PROFILE.md`, `MEMORY.md`, `memory/`, `skills/`, `skill.json`, `.browser-profile/`.
  - `~/.qwenpaw.secret/providers.json` (provider và API key), `envs.json` (biến môi trường).
- **Biến môi trường** (tag v2.2.1): `QWENPAW_WORKING_DIR`, `QWENPAW_SECRET_DIR`, `QWENPAW_CONFIG_FILE`, `QWENPAW_LOG_LEVEL`, `QWENPAW_AUTH_ENABLED` (mặc định `false`) + `QWENPAW_AUTH_USERNAME`/`QWENPAW_AUTH_PASSWORD` (đăng nhập Console), `QWENPAW_TOOL_GUARD_ENABLED` (mặc định `true`), `QWENPAW_SKILL_SCAN_MODE` (mặc định `warn`), `QWENPAW_LLM_STREAM_FIRST_CONTENT_TIMEOUT`/`_IDLE_TIMEOUT` (mặc định 30), `QWENPAW_MEMORY_COMPACT_*`; không có biến `COPAW_*` — [config.en.md @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/config.en.md) (bậc 1)
- **Model provider** (tag v2.2.1) — [models.en.md @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/models.en.md) (bậc 1):
  - Local: QwenPaw Local (llama.cpp, còn thử nghiệm, chỉ chạy 1 model một lúc, file ở `~/.qwenpaw/local_models`), Ollama, LM Studio.
  - Cloud: ModelScope, DashScope, Aliyun Coding Plan, OpenRouter, OpenAI, Azure OpenAI, Anthropic, Google Gemini, DeepSeek, Kimi, MiniMax, Zhipu, SiliconFlow, OpenCode, Volcengine (+ Coding/Agent Plan), Xiaomi MiMo (+ Token Plan), GitHub Models, Kilo. Một số provider có base URL riêng cho Trung Quốc đại lục và quốc tế.
  - Provider OpenAI-compatible tự thêm: Settings → Models → Providers → Add Provider (chế độ `chat.completions`) → nhập Base URL + API Key → Add Model (Model ID) → Test Connection; ví dụ vLLM `http://localhost:8000/v1`.
  - Ollama: context length ≥ 32k; Docker gọi Ollama trên host thì thêm `--add-host=host.docker.internal:host-gateway` và dùng `http://host.docker.internal:11434`.
  - LM Studio: bật Local Server (`http://localhost:1234`, nhập kèm `/v1`), Default Context Length ≥ 32768, bật tách `reasoning_content` và `content` trong Experimental Settings.
  - DashScope có thể đặt `DASHSCOPE_API_KEY` trong shell hoặc `.env`; key tool như `TAVILY_API_KEY` đặt ở Settings → Environment variables — [README](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/README.md) (bậc 1)
  - Bản cài mới mặc định dùng router miễn phí `kilo-auto/free` của Kilo (maintainer trả lời trong issue) — [Issue #8218](https://github.com/agentscope-ai/QwenPaw/issues/8218) (bậc 1, 2026-10-15)
- **Channel** (tag v2.2.1): cấu hình ở Console → Control → Channels hoặc `workspaces/<agent_id>/agent.json` → `channels` — [channels.en.md @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/channels.en.md) (bậc 1):
  - DingTalk: Stream mode, `client_id`, `client_secret` (tùy chọn `robot_code`, `card_template_id`).
  - Feishu/Lark: WebSocket long connection, không cần IP public; `app_id`, `app_secret`, `domain` (`feishu`/`lark`); cần `lark-oapi`; phải chạy `qwenpaw app` trước khi cấu hình long connection.
  - WeChat (iLink cá nhân, beta giới hạn, phải xin quyền; gửi thực tế chỉ text), WeCom (`bot_id`, `secret`).
  - Discord (`bot_token`, bật Message Content Intent), Telegram (`bot_token` từ @BotFather); cả hai có `http_proxy`.
  - QQ bot chính thức (`app_id`, `client_secret`, cần whitelist IP), OneBot v11 (reverse WS, `ws_port` 6199, bắt buộc `access_token` nếu không bind loopback).
  - iMessage: "macOS only", cần `imsg` và Full Disk Access.
  - Matrix, Slack (Socket Mode, `xoxb-`/`xapp-`), Mattermost, Yuanbao, XiaoYi, MQTT.
  - Voice Twilio cần URL HTTPS public (tunnel về port 8088, callback `/api/voice/callback`); SIP; Azure Bot (plugin, cần endpoint public).

### Nhận định
- **Nhận định:** Với dùng cá nhân trên Linux/macOS, đường ngắn nhất là pip trong venv (hoặc script), `qwenpaw init --defaults`, `qwenpaw app`, rồi đổi ngay Default LLM khỏi router free mặc định sang provider mình kiểm soát. Các channel Feishu/DingTalk/Slack/Discord/Telegram không cần IP public, nên chạy được trên laptop.
- **Nhận định:** Console mặc định không có đăng nhập (`QWENPAW_AUTH_ENABLED=false`) và bind 127.0.0.1; nếu đổi `--host 0.0.0.0` thì nên bật auth.

### Khoảng trống
- Docs quickstart/cli ở tag v2.2.1 chưa được đối chiếu riêng (đọc ở nhánh main); một số lệnh như `qwenpaw .`, `doctor`, `models download` có thể mới thêm sau v2.2.1.
- Docs models @v2.2.1 không ghi base URL DashScope/Coding Plan và chưa mô tả per-agent model routing dù release note v2.2.1 có nói.

## 3. Hạn chế và lỗi thường gặp khi cài/chạy

### Kết luận ngắn
Không thấy lỗi cài đặt nghiêm trọng nào gắn nhãn `installation-bug` cho v2.2.x; lỗi hay gặp là xung đột port 8088 trên Windows, context quá nhỏ với model local, key/base URL sai, model free bị ngừng, timeout LLM không tự hồi phục (chưa tái hiện được), và vấn đề schema tool với một số provider. Mức chắc chắn: **trung bình** (chỉ xem trang đầu kết quả issues).

### Phát hiện có nguồn
- Nhãn `installation-bug` chỉ có 1 issue (release-duty v1.1.11.post1, đóng 2026-06-11) — [Issues label installation-bug](https://github.com/agentscope-ai/QwenPaw/issues?q=is%3Aissue+label%3Ainstallation-bug) (bậc 1, truy cập 2026-10-23)
- FAQ @v2.2.1: Hyper-V/WSL2 có thể giữ port 8088 ("Address already in use"); kiểm tra `netsh interface ipv4 show excludedportrange protocol=tcp`; đổi port `qwenpaw app --port 8090` hoặc `-p 127.0.0.1:8090:8088` — [faq @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/faq.en.md) (bậc 1)
- FAQ: Windows LTSC / Constrained Language Mode làm script không cập nhật PATH hoặc không tải được uv; thêm tay `%USERPROFILE%\.qwenpaw\bin` vào Path hoặc `python -m pip install -U uv` — cùng nguồn (bậc 1)
- FAQ: model local cần context ≥ 32K, thiếu thì mất instruction và tool call nhiều lượt bị hỏng; lỗi 401 "You didn't provide an API key" thì kiểm tra key ở Settings → Models, `base_url`, khoảng trắng thừa, tên model phân biệt hoa thường; WSL2 NAT bị `APITimeoutError` thì hạ MTU 1350 (`sudo ip link set eth0 mtu 1350`, hoặc `[boot] command = /sbin/ip link set eth0 mtu 1350` trong `/etc/wsl.conf`) — cùng nguồn (bậc 1)
- FAQ cron: dịch vụ phải đang chạy, task Enabled, Dispatch Channel đúng, Target User ID/Session ID khớp Control → Sessions; dùng "Execute Now" để thử — cùng nguồn (bậc 1)
- #7935 (mở 2026-09-22, v2.2.1, pip, Python 3.12, WSL2, provider OpenAI-compatible): sau lỗi mạng, `openai.APITimeoutError: Request timed out.` lặp hàng giờ, chỉ restart mới hết; Console chỉ báo `Request timeout after 30000ms`; maintainer gắn "Cannot Reproduce", xin traceback đầy đủ — [Issue #7935](https://github.com/agentscope-ai/QwenPaw/issues/7935) (bậc 1, 2026-09)
- #8218 (v2.2.1, đóng 2026-10-15): lỗi `MODEL_EXECUTION_ERROR` vì model free `mimo-v2.5-free` bị ngừng; cách xử lý: Settings → Models → Edit "Default LLM" → chọn model khác — [Issue #8218](https://github.com/agentscope-ai/QwenPaw/issues/8218) (bậc 1, 2026-10)
- Các bug khác có từ khóa 2.2.1 (trang 1/2): #8280 file content thiếu `file_id`/`file_data` bị provider OpenAI-compatible trả 400 (mở); #8265 hot-install plugin hỏng trên Python 3.11 do distro vá (mở); #7959 Moonshot kimi-k3 từ chối schema tool MCP có `anyOf` không type (mở); #8064 DeepSeek: `send_file_to_user` gửi PDF làm hỏng session vĩnh viễn (đã đóng); #7764 MCP client không active do `httpx.DecodingError` (đã đóng) — [Issues bug 2.2.1](https://github.com/agentscope-ai/QwenPaw/issues?q=is%3Aissue+label%3Abug+2.2.1) (bậc 1, truy cập 2026-10-23)
- Desktop 2.2.2 trên Windows: validator make-skill lỗi "No module named 'qwenpaw'" — [Issue #8320](https://github.com/agentscope-ai/QwenPaw/issues/8320) (bậc 1, 2026-10; bản 2.2.2, không phải 2.2.1)
- Hạn chế theo docs: QwenPaw Local (llama.cpp) còn thử nghiệm, GPU hạn chế, khuyên dùng Ollama/LM Studio — [models @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/models.en.md); WeChat iLink beta giới hạn, iMessage chỉ macOS — [channels @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/channels.en.md); Hub không có ranh giới cô lập mạnh, chỉ cho người dùng tin cậy — [hub @v2.2.1](https://raw.githubusercontent.com/agentscope-ai/QwenPaw/v2.2.1/website/public/docs/hub.en.md) (bậc 1)

### Nhận định
- **Nhận định:** Phần lớn sự cố của v2.2.1 nằm ở lớp tương thích provider (schema tool, file part, model free bị khai tử), không phải ở cài đặt. Nên chọn một provider ổn định, đặt `fallback_models`, và nếu gặp timeout kéo dài thì restart (`qwenpaw daemon restart` hoặc khởi động lại `qwenpaw app`).

### Khoảng trống
- Chỉ đọc trang 1/2 của danh sách bug "2.2.1"; chưa xem Discussions.
- Chưa có số liệu về tần suất lỗi; các issue là báo cáo đơn lẻ.

## Truy vấn đã chạy
- QwenPaw v2.2.1 release (extended)
- CoPaw renamed QwenPaw (standard)
- QwenPaw github issue install error qwenpaw app (extended)
- QwenPaw CoPaw 更名 ~/.copaw 迁移 (standard)
- WebFetch: GitHub releases, release v2.2.0, v2.0.0, README, docs `config/cli/quickstart/models/channels/faq/intro/hub` (tag v2.2.1 và main), `constant.py @v2.2.1`, PyPI history, issues #7692 #7935 #8218, danh sách issues theo nhãn
- Thất bại (DNS ENOTFOUND): qwenpaw.agentscope.io/docs/config, help.aliyun.com/en/model-studio/qwenpaw, aibase.com, ithome.com; `gh api` bị chặn (repo chưa được cấp quyền)
