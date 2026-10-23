---
title: Cách dùng QwenPaw v2.2.1 — cài đặt, cấu hình skills và subagent
date: 2026-10-23
question: Với QwenPaw v2.2.1 (agentscope-ai/QwenPaw), cài đặt, dùng hằng ngày và cấu hình skills, subagent (multi-agent) cùng các thành phần liên quan như thế nào?
tags: [qwenpaw, agentscope, ai-agent, skills, subagent, multi-agent]
---

# QwenPaw v2.2.1: hai lớp cấu hình, skill đi qua pool, subagent là phiên phụ tạm thời

> **Câu hỏi:** Cài, dùng hằng ngày và cấu hình skills, subagent/multi-agent của QwenPaw v2.2.1 thế nào? · **Ngày:** 2026-10-23 · **Phạm vi:** bản v2.2.1 (tag 2026-09-11), đối chiếu docs trong repo với source cùng tag; người dùng cá nhân trên Linux/macOS · **Kiểm chứng:** 62 khẳng định đã đối chiếu nguồn, 14 đã sửa

## Tóm tắt

Dùng QwenPaw v2.2.1 tối thiểu gồm ba bước: cài bằng `pip install qwenpaw==2.2.1` trong venv (Python 3.11–3.13), chạy `qwenpaw init --defaults` rồi `qwenpaw app`, sau đó vào Console ở `http://127.0.0.1:8088/` để đặt model mặc định [2]. Bản v2.2.1 có thật, phát hành ngày **2026-09-11**, nhưng **không còn là bản mới nhất**: v2.2.2 ra ngày 2026-10-15 và v2.2.2.post1 ngày 2026-10-22 [1]. Cấu hình chia hai lớp. `~/.qwenpaw/config.json` giữ danh sách agent và vài thiết lập toàn cục. `~/.qwenpaw/workspaces/<agent_id>/agent.json` giữ mọi thứ của từng agent: channel, MCP, tools, model, heartbeat, bảo mật. API key nằm riêng trong `~/.qwenpaw.secret/` [3]. Skill là một thư mục chứa `SKILL.md` theo kiểu Anthropic. Skill nằm trong pool dùng chung, được broadcast sang workspace của từng agent, rồi được bật bằng Console hoặc `qwenpaw skills enable` [4]. "Subagent" theo nghĩa của QwenPaw là phiên phụ tạm thời của *chính agent đó*, sinh ra bằng tool `spawn_subagent`. Muốn có "chuyên gia" với model và persona riêng thì phải tạo agent riêng, rồi giao việc qua `chat_with_agent` hoặc `submit_to_agent` [5][6]. Các điểm trên đều chắc chắn cao, vì đã đọc cả docs lẫn source ở tag v2.2.1. Tuy vậy, docs lệch với source ở khá nhiều chi tiết, và một số bản sửa quan trọng (timeout của `chat_with_agent`, kiểm tra tên skill) chỉ có ở v2.2.2.

**Điểm chính**
- v2.2.1 là bản nhỏ sau v2.2.0. Nó thêm model routing riêng cho từng agent, preload skill, Make Skill nâng cấp và kiểm tra dependency của skill. Hub, Mail và Data đã có từ v2.2.0 [7][8].
- Mọi file nằm dưới `~/.qwenpaw/`. Ngoại lệ: máy từng cài CoPaw mà còn `~/.copaw` thì QwenPaw dùng luôn thư mục đó [9].
- Skill tự viết chỉ cần `name` và `description` trong frontmatter. Skill đặt tay vào thư mục ở trạng thái **tắt** cho tới khi bật lên. Skill Scanner mặc định chỉ `warn` chứ không chặn [4][10].
- `spawn_subagent` chờ tối đa **600 giây** ở foreground. Batch chạy tối đa **10** task, cùng lúc **3** task. Timeout là tham số model truyền vào tool, không phải cấu hình toàn cục [6][11].
- Sandbox **mặc định tắt**, Console **không có đăng nhập** mặc định, và tool agent-to-agent được bật sẵn [12][10][13].

## v2.2.1 có thật, nhưng người cài mới hôm nay sẽ nhận v2.2.2

QwenPaw ("Qwen Personal Agent Workstation") là trợ lý AI cá nhân mã nguồn mở (Apache 2.0) của team AgentScope, chạy local hoặc trên cloud, có skills, plugins và nhiều channel nhắn tin [14]. Nó là tên mới của **CoPaw**, đổi tên ở bản 1.1.0 (PyPI ngày 2026-04-12) [1][54]. Code v2.2.1 vẫn còn dấu vết đổi tên này: nếu không đặt `QWENPAW_WORKING_DIR` mà `~/.copaw` tồn tại, QwenPaw dùng `~/.copaw` "as-is" [9]. FAQ khẳng định nâng cấp từ CoPaw không cần migration [15]. Từ v2.0.0 (2026-07-10), kernel chạy trên AgentScope 2.0. Bản v2.0.0 cũng thay memory bằng ReMe, chuyển desktop sang Tauri, thêm TUI và policy engine allow/deny/ask [16]. v2.2.1 ghim `agentscope==2.0.7.post1` [17].

| Bản | Ngày | Điểm đáng chú ý cho người dùng |
|---|---|---|
| v2.2.0 | 2026-09-03 | QwenPaw Hub (server nhiều người dùng), Mail, Data; marketplace hợp nhất "Extensions"; nhóm hội thoại subagent; field `subagent_model` [8][6] |
| **v2.2.1** | **2026-09-11** | Model routing/fallback riêng từng agent (#7501); preload skill (#7183); Make Skill nâng cấp (#7509); kiểm tra version và dependency skill (#7609); timeout MCP HTTP/SSE; enforce whitelist tool MCP lúc runtime [7] |
| v2.2.2 | 2026-10-15 | Giữ lý do cancel và cho vòng agent chạy tiếp khi tool bị dừng (#8183, fix của #7981); kiểm tra tên skill trước khi làm đường dẫn cài (#8065); phân phối skill từ pool sang workspace hàng loạt (#7852); PawPort import từ Codex/Qoder; `/reme` thay `/dream`, `/memorize` [18][19] |
| v2.2.2.post1 | 2026-10-22 | Vá CA trust, Node.js 22.23.4 [19] |

PyPI ghi v2.2.1 ngày 2026-09-11, còn README ghi 2026-09-10. **Nhận định:** độ lệch một ngày có thể do múi giờ [1][14]. Lệnh cài không pin version sẽ lấy 2.2.2.post1. Muốn đúng v2.2.1 thì phải pin `qwenpaw==2.2.1`. Có hai lý do thực tế để lên v2.2.2: fix #8183 cho người dùng `chat_with_agent` nhiều, và fix #8065 cho người hay cài skill bên thứ ba.

## Cài bằng pip hoặc Docker, chạy `init` rồi `app`, việc đầu tiên là đổi model mặc định

Có năm cách cài: pip (Python **≥3.11, <3.14**), script một dòng (tự lo uv/venv), Docker image `agentscope/qwenpaw`, desktop app Tauri (Windows 10+/macOS 14+, đang beta), hoặc chạy không cần cài trên AgentScope Platform/ModelScope Studio [2][1]. Với máy cá nhân, quy trình ngắn nhất như sau:

```bash
# pip trong venv (pin đúng v2.2.1)
python3 -m venv ~/.venvs/qwenpaw && source ~/.venvs/qwenpaw/bin/activate
pip install qwenpaw==2.2.1

# hoặc script: curl -fsSL https://qwenpaw.agentscope.io/install.sh | bash -s -- --version 2.2.1

qwenpaw init --defaults      # hoặc `qwenpaw init` để hỏi tương tác; --force để ghi đè
qwenpaw app                  # Console tại http://127.0.0.1:8088/  (--host, --port, --reload, --log-level)
qwenpaw tui                  # hoặc chỉ `qwenpaw`: giao diện terminal, --agent <id>, --resume <id>

# thử API
curl -N -X POST "http://localhost:8088/api/console/chat" -H "Content-Type: application/json" \
  -d '{"input":[{"role":"user","content":[{"type":"text","text":"Hello"}]}],"session_id":"session123"}'
```

Docker dùng ba volume cho data, secret và backup. API key truyền bằng `-e` hoặc `--env-file` [2][15]:

```bash
docker run -p 127.0.0.1:8088:8088 \
  -v qwenpaw-data:/app/working -v qwenpaw-secrets:/app/working.secret \
  -v qwenpaw-backups:/app/working.backups \
  -e DASHSCOPE_API_KEY=xxx agentscope/qwenpaw:latest
```

Nâng cấp bằng `qwenpaw update` (pip) hoặc chạy lại script. Gỡ bằng `qwenpaw uninstall`, thêm `--purge` nếu muốn xóa cả data [2][15]. Các nhóm lệnh CLI chính là `models`, `env`, `channels`, `agents`, `chats`, `cron`, `skills`, `plugin`, `daemon` và `doctor` [20]. Docs quickstart và CLI ở nhánh main (2026-10-22) giống hệt bản ở tag v2.2.1, và các lệnh `qwenpaw .`, `doctor`, `models download` đều có trong source CLI của v2.2.1 [2][20].

**Bắt buộc** phải đặt model: vào Settings → Models, cấu hình provider và chọn Default LLM [2]. Bản cài mới mặc định dùng router miễn phí `kilo-auto/free`. Issue #8218 cho thấy model free có thể bị khai tử (`mimo-v2.5-free`), làm agent báo `MODEL_EXECUTION_ERROR` [21]. Provider cloud có sẵn gồm DashScope, ModelScope, Aliyun Coding Plan, OpenAI, Azure OpenAI, Anthropic, Gemini, DeepSeek, Kimi, MiniMax, Zhipu, OpenRouter, SiliconFlow, Volcengine, MiMo, GitHub Models, Kilo [22]. Model local có ba lựa chọn. QwenPaw Local (llama.cpp) còn thử nghiệm và chỉ chạy một model một lúc. Ollama (`localhost:11434`) cần context **≥ 32k**; khi chạy QwenPaw trong Docker thì thêm `--add-host=host.docker.internal:host-gateway`. LM Studio (`http://localhost:1234/v1`) cần Default Context Length ≥ 32768 và bật tách `reasoning_content`. Server OpenAI-compatible tự dựng (ví dụ vLLM `http://localhost:8000/v1`) thêm qua Add Provider [22]. FAQ giải thích lý do: context dưới 32K làm agent quên chỉ dẫn và gãy tool call nhiều lượt [15].

Channel cấu hình ở Console → Control → Channels, hoặc trong `agent.json` → `channels`. Các channel chính trong brief đều chạy được từ laptop mà không cần IP public. DingTalk dùng Stream mode (`client_id`, `client_secret`). Feishu/Lark dùng WebSocket (`app_id`, `app_secret`, `domain`, cần `lark-oapi`, và phải chạy `qwenpaw app` trước). Discord cần `bot_token` và bật Message Content Intent. Telegram dùng `bot_token` từ @BotFather. Cả Discord và Telegram có `http_proxy`. Slack dùng Socket Mode. Ngược lại, voice Twilio cần URL HTTPS public, iMessage chỉ chạy trên macOS, và WeChat iLink là beta giới hạn [23].

## Cấu hình nằm ở hai lớp: `config.json` toàn cục và `agent.json` của từng agent

Cây thư mục mặc định gồm ba gốc [3][9]:

```text
~/.qwenpaw/                      # QWENPAW_WORKING_DIR (hoặc ~/.copaw nếu còn bản CoPaw cũ)
├── config.json                  # agents.active_agent, agents.profiles, last_api, user_timezone, browser, security.sandbox_enabled, skill_paths
├── .env                         # tự nạp lúc khởi động
├── skill_pool/                  # kho skill dùng chung + skill.json
├── governance/<ws>_<sha12>/policy.yaml   # rule sandbox, nằm ngoài workspace
└── workspaces/<agent_id>/
    ├── agent.json               # channels, mcp, heartbeat, tools, running, active_model, security, approval_level...
    ├── AGENTS.md  SOUL.md  PROFILE.md  MEMORY.md  HEARTBEAT.md
    ├── skills/  skill.json      # skill agent thật sự dùng + trạng thái bật/tắt
    ├── drivers/mcp/*.yaml       # MCP "driver card" (từ v2.0)
    ├── memory/  chats.json  jobs.json  token_usage.json
~/.qwenpaw.secret/               # QWENPAW_SECRET_DIR: providers.json (API key), envs.json
~/.qwenpaw.backups/              # QWENPAW_BACKUP_DIR
```

Khi một field có ở cả hai file, `agent.json` thắng `config.json`. Hệ thống kiểm tra thay đổi của `agent.json` **mỗi 2 giây** để hot reload. Việc ghi cấu hình có khóa: bản lưu dựa trên snapshot cũ bị từ chối với HTTP 409, nhưng editor ngoài không tham gia khóa này [3]. Theo source, `config.json` chỉ giữ tham chiếu `AgentProfileRef` gồm `id`, `workspace_dir`, `enabled`, `pinned`. Toàn bộ cấu hình agent (`name`, `description`, `active_model`, `fallback_models`, `subagent_model`, `llm_routing`, `tools`, `running`…) nằm trong `AgentProfileConfig` ở `agent.json` [12].

Biến môi trường đọc lúc khởi động, nên đổi xong phải restart. Những biến đáng nhớ: `QWENPAW_WORKING_DIR`, `QWENPAW_SECRET_DIR`, `QWENPAW_LOG_LEVEL` (đặt `debug` khi điều tra MCP), `QWENPAW_AUTH_ENABLED` (mặc định `false`) cùng `QWENPAW_AUTH_USERNAME`/`PASSWORD`, `QWENPAW_TOOL_GUARD_ENABLED` (mặc định `true`), `QWENPAW_SKILL_SCAN_MODE` (mặc định `warn`), `QWENPAW_LLM_STREAM_FIRST_CONTENT_TIMEOUT` và `_IDLE_TIMEOUT` (30 giây) [3]. Source còn có những biến docs không ghi, như `QWENPAW_ENABLED_CHANNELS`/`QWENPAW_DISABLED_CHANNELS`, `QWENPAW_TOOL_GUARD_APPROVAL_TIMEOUT_SECONDS` (mặc định 300) và `QWENPAW_TOOL_GUARD_DENIED_TOOLS` [9]. Key cho tool (ví dụ `TAVILY_API_KEY`, `GITHUB_TOKEN`) đặt ở Settings → Environment variables hoặc bằng `qwenpaw env set KEY VALUE` [3][20].

Vài field trong khối `running` của `agent.json` đáng biết vì chúng quyết định hành vi hằng ngày [3][12]:

| Field | Mặc định (source) | Ý nghĩa |
|---|---|---|
| `max_iters` | 100 (ví dụ docs ghi 50) | số vòng ReAct tối đa mỗi lượt |
| `max_input_length` | 131072 token | ngưỡng nén context ở `compact_threshold_ratio` 0.8 |
| `shell_command_timeout` | 60 s | timeout lệnh shell |
| `llm_max_retries` / `llm_max_concurrent` / `llm_max_qpm` | 3 / 10 / 600 | giới hạn gọi LLM (concurrent dùng chung mọi agent) |
| `memory_manager_backend` | `remelight` | backend memory |

**Nhận định:** coi `agent.json` là nơi cấu hình chính, đặt `QWENPAW_WORKING_DIR` tường minh nếu máy từng cài CoPaw, và không bao giờ đưa `~/.qwenpaw.secret/` hay `credentials.yaml` vào git.

## Skill là thư mục `SKILL.md`, đi từ pool sang workspace rồi mới được bật

**Định dạng.** Một skill là thư mục chứa `SKILL.md` với YAML frontmatter. Hai field bắt buộc là `name` và `description`; `metadata` là tùy chọn [4]. Khối `requires` khai báo binary, biến môi trường và MCP cần có. Đây là **tên**, không phải giá trị: viết `env: MY_KEY` dạng chuỗi là sai. Version đọc lần lượt từ `version`, `metadata.version`, rồi `metadata.builtin_skill_version`. `requires` được tìm theo thứ tự `metadata.openclaw.requires` → `metadata.qwenpaw.requires` → `metadata.clawdbot.requires` → `metadata.requires` → `requires`. Emoji lấy từ `metadata.qwenpaw.emoji` [4][24]. Ví dụ một skill tự viết, theo mẫu chính thức:

```markdown
---
name: my_skill
description: Tạo báo cáo tuần từ file CSV bán hàng
metadata:
  version: "1.0"
  requires:
    bins: [ffmpeg]
    env: [MY_API_KEY, BASE_URL]
    mcp: [my-mcp-server]
---
# Hướng dẫn cho agent ...
```

Giá trị thật được nhập ở Console, trong object `config` của skill, ví dụ `{"MY_API_KEY":"sk-demo","BASE_URL":"https://api.example.com","timeout":30}`. Trong suốt một lượt của agent, các key có trong `requires.env` thành env var riêng, còn toàn bộ JSON nằm ở `QWENPAW_SKILL_CONFIG_MY_SKILL`. Script đọc bằng `os.environ.get("MY_API_KEY")` hoặc `json.loads(os.environ["QWENPAW_SKILL_CONFIG_MY_SKILL"])`. Biến env sẵn có trên máy **không bao giờ bị ghi đè**: host env thắng workspace config, workspace config thắng pool config [4]. Skill có thể kèm `scripts/` và `references/` như các builtin `pdf`, `make-skill` [25].

**Hai lớp lưu trữ.** Skill Pool (`~/.qwenpaw/skill_pool/`) là kho dùng chung. Pool không có trạng thái bật/tắt, và skill trong pool "are **not executed directly**". Muốn dùng phải **broadcast** sang workspace, tức `~/.qwenpaw/workspaces/{agent_id}/skills/`. Trạng thái của skill trong workspace nằm ở `skill.json`, với các field `enabled`, `channels` (mặc định `["all"]`), `preload`, `source`, `installed_from` và `config` [4][24]. Có thể khai báo thư mục ngoài bằng `skill_paths` trong `config.json`, ví dụ `{"skill_paths": ["~/my-skills", "/opt/team/shared-skills"]}`. Skill ở đó được đọc tại chỗ, và khi trùng tên thì path đứng trước thắng. Cần cẩn thận: **xóa skill external từ UI sẽ xóa file thật**, còn path không tồn tại bị bỏ qua mà không báo lỗi [4][12].

**Ba cách tạo, ba cách bật.** Cách thứ nhất là Console → Workspace → Skills → Create; skill tạo qua "Add Skill" được bật sẵn. Cách thứ hai là viết tay vào `workspaces/{agent_id}/skills/<name>/SKILL.md`; skill sẽ được ghi vào `skill.json` ở trạng thái **disabled** trong lần reconcile kế tiếp. Cách thứ ba là gõ `/make-skill weekly sales report workflow` trong chat. Agent đề xuất kế hoạch kèm mức test (No test / Smoke test / Eval), chờ duyệt, rồi lưu skill ở trạng thái bật [4]. Các lệnh CLI, mặc định áp cho agent `default` nếu thiếu `--agent-id` [4][20]:

```bash
qwenpaw skills list --status all --agent-id default      # hoặc --pool
qwenpaw skills enable pdf docx --agent-id coder
qwenpaw skills disable pdf --agent-id coder
qwenpaw skills info my_skill
qwenpaw skills test my_skill --agent-id default          # exit code ≠ 0 nếu thiếu bin/env/MCP
qwenpaw skills install https://github.com/anthropics/skills/... --pool   # hoặc --agent-id <id> [--enable]
qwenpaw skills uninstall my_skill --agent-id coder
```

Trong chat có ba lệnh: `/skills` liệt kê skill dùng được ở channel hiện tại, `/<skill_name>` xem chi tiết, và `/<skill_name> <input>` ép agent dùng skill đó [26].

**Cách skill vào prompt.** Mặc định là progressive disclosure giống Anthropic Agent Skills. Prompt chỉ chứa khối `<agent-skills>` gồm `<name>`, `<description>`, `<dir>`. Agent phải gọi tool read-only `Skill` với input `{"skill": "<name>"}` để đọc nội dung [17][27]. Từ v2.2.1, đặt `preload: true` (Workspace → Skills → Edit) sẽ nhét toàn bộ nội dung skill vào khối `<preloaded-skills>` của system prompt. Docs khuyên chỉ preload skill "trusted core or frequently used" [28][4]. Cũng từ v2.2.1, skill khai báo thiếu bin/env/MCP bị **bỏ qua khi nạp**, kèm log ERROR, và không hiện trong `/skills`. Agent vẫn chạy bình thường [4][7].

**Market và builtin.** Skill Market (Add Skill → Browse Market) tìm song song trên bốn provider: QwenPaw, ClawHub, ModelScope, và Aliyun (Aliyun cần `ALIBABA_CLOUD_ACCESS_KEY_ID`/`_SECRET`). Import theo URL nhận link từ skills.sh, clawhub.ai, skillsmp.com, lobehub.com, github.com và modelscope.cn/skills. Bị rate-limit GitHub thì thêm `GITHUB_TOKEN` [4]. "QwenPaw Hub" (`qwenpaw hub`) không phải hub skill mà là server nhiều người dùng [29]. Package v2.2.1 có **16 skill builtin**, mỗi skill có bản `-en` và `-zh`: `QA_source_index`, `browser`, `channel_message`, `chat_with_agent`, `cron`, `dingtalk_channel`, `docx`, `file_reader`, `guidance`, `mailbox`, `make-skill`, `make_plan`, `multi_agent_collaboration`, `pdf`, `pptx`, `xlsx`. Bốn skill `docx`/`pdf`/`pptx`/`xlsx` lấy từ repo `anthropics/skills` [25][4].

**Bảo mật skill.** Skill Scanner quét bằng regex YAML trước khi kích hoạt skill. Nó có ba chế độ `block`/`warn`/`off`, **mặc định `warn`**, tức skill đáng ngờ vẫn được bật, chỉ kèm cảnh báo. Thứ tự ưu tiên cấu hình là env `QWENPAW_SKILL_SCAN_MODE` > Console > `config.json` (`security.skill_scanner`). Whitelist khóa theo SHA-256 nội dung skill [10][12]. **Nhận định:** nếu hay cài skill từ market, đặt `QWENPAW_SKILL_SCAN_MODE=block` rồi whitelist skill tự viết. Nên giữ skill tự viết trong một git repo, khai báo qua `skill_paths`, rồi broadcast sang các agent cần dùng.

## "Subagent" là phiên phụ tạm thời của cùng agent (session mới, không chép hội thoại); muốn chuyên gia thì tạo agent riêng

QwenPaw có ba khái niệm dễ lẫn. **Agent** là một persona độc lập. Mỗi agent có workspace, `agent.json`, lịch sử chat, cron, skill và channel riêng, và "remembers its own conversations (no cross-talk)". Provider và env thì dùng chung giữa các agent [5]. **Subagent** là phiên phụ tạm thời của chính agent đang chạy, sinh ra bằng `spawn_subagent`: cùng identity, cùng workspace, mặc định cùng toàn bộ tool và skill, và không resume được [6][5]. **External agent** là Claude Code, Codex, Qwen Code hay opencode, được gọi qua ACP bằng `delegate_external_agent` [30].

Tạo agent mới có ba đường: Console (Settings → Agent Management → Create Agent), CLI, hoặc REST `POST /api/agents`. Description rất quan trọng, vì agent khác đọc nó và `PROFILE.md` để chọn người cộng tác. Agent `default` không xóa được. Xóa một agent vẫn giữ lại thư mục workspace [5].

```bash
qwenpaw agents create --name "Code Reviewer" --agent-id code-reviewer \
  --description "Review Python/JS và refactor" --template local \
  --skill make_plan --provider-id ollama --model-id qwen3:8b
qwenpaw agents list
qwenpaw agents chat --from-agent default --to-agent code-reviewer --text "Review src/app.py" --timeout 1800
qwenpaw agents delete code-reviewer --remove-workspace --yes
```

Template builtin chỉ có ba loại: `default`, `local` và `qa`. Template `local` bật sẵn các tool agent và skill `make_plan`, dành cho model local nhỏ [31]. Model và subagent của từng agent cấu hình trong `agent.json`. Khối dưới đây suy ra từ schema và **chưa chạy thử**; provider và model chỉ để minh họa [12][6]:

```json
{
  "id": "code-reviewer",
  "name": "Code Reviewer",
  "description": "Specializes in Python/JS code review and refactoring",
  "active_model":   {"provider_id": "dashscope", "model": "qwen3-max"},
  "subagent_model": {"provider_id": "ollama",    "model": "qwen3:8b"},
  "approval_level": "AUTO",
  "running": {"max_iters": 100},
  "tools": {"builtin_tools": {"spawn_subagent": {"enabled": true}, "chat_with_agent": {"enabled": true}}}
}
```

`subagent_model` ("Optional cheaper model used by spawned subagents") có từ v2.2.0. Nếu model này load lỗi, exception bị bỏ qua và subagent chạy không có override, tức dùng model của agent cha [6]. Issue #7676 từng báo `subagent_model` không có tác dụng, rồi chính người báo rút lại: log `builder` in ra `active_model` của cha, còn model thật sự dùng phải xem ở token usage của session [32].

Các tool giao việc đều **bật sẵn**. Trong `tool_registry.py`, `enabled_by_default` mặc định là `True`; chỉ `delegate_external_agent` và `append_file` mặc định tắt [13]. Chọn tool theo nhu cầu như bảng dưới [6][5][9]:

| Tool | Chạy | Ngữ cảnh | Giới hạn mặc định | Dùng khi |
|---|---|---|---|---|
| `chat_with_agent(to_agent, text, session_id, timeout=300)` | đồng bộ | workspace agent đích, chỉ text | 300 s | hỏi một agent chuyên gia, nhiều lượt nhờ `session_id` |
| `submit_to_agent` + `check_agent_task(task_id)` | nền, poll | như trên | 3600 s | việc dài giao cho agent khác |
| `spawn_subagent(task, fork=False, background=False, timeout, allowed_tools, skills, batch)` | foreground hoặc nền | session trống, cùng project | 600 s foreground, 3600 s nền | việc con độc lập |
| `spawn_subagent(..., fork=True)` | như trên | toàn bộ lịch sử cha, git worktree | như trên | việc phụ cần ngữ cảnh, có sửa file |
| `delegate_external_agent(action, runner, ...)` | phiên ACP | runner ngoài | `max_runtime=300` | giao cho Claude Code/Codex; phải cấu hình ở Workspace → ACP và bật tool |

Batch chạy tối đa **10** task, trong đó **3** task chạy đồng thời. `allowed_tools=[]` cấm mọi tool, còn `skills` là whitelist skill [6]. Với `fork=True`, nếu có git thì worktree đặt ở `<project_dir>/.qwenpaw/worktrees/` (khi Coding Mode bật) hoặc `<workspace_dir>/.qwenpaw/worktrees/`. Nếu subagent có sửa file, tool trả `[FORK_BRANCH: fork/...]` để người dùng tự merge. Muốn chép file bị gitignore (ví dụ `.env`) vào worktree thì liệt kê trong `.worktreeinclude`. Không có git thì fork chạy tại chỗ, không cô lập file [6]. Approval của subagent được chuyển về phiên gốc theo `root_session_id`, và subagent kế thừa `approval_level` [33]. Subagent hiện trong Console thành nhóm chat "subagents" [8].

Việc lớn nhiều bước thì dùng Mission Mode: `/mission <task> --max-iterations 30 --verify "pytest tests/"`, kèm `/mission status` và `/mission list`. Pipeline là master → worker (`spawn_subagent fork=True`) → verifier (background). Docs cảnh báo worker và verifier "automatically bypass the security guard", nên chỉ dùng trong codebase hoàn toàn tin cậy [34][26].

Giới hạn cần biết. Ở v2.2.1 **không có callback** báo việc nền xong: agent cha phải tự poll `check_agent_task`, docstring dặn chờ 30 giây rồi poll mỗi 30–60 giây. PR đánh thức agent cha khi việc nền xong (#8063) vẫn còn mở tới 2026-10-23 [55]. Grep source không thấy giới hạn độ sâu lồng (chưa chạy thử). Kết quả `chat_with_agent` được miễn tỉa khỏi context, nên câu trả lời dài chiếm chỗ lâu [12]. **Nhận định:** vì timeout là tham số do model truyền vào tool, cách ổn định nhất là ghi vào `AGENTS.md` của agent một quy tắc như "với việc dài, gọi `spawn_subagent`/`chat_with_agent` với `timeout=1800` hoặc dùng `background=True`/`submit_to_agent`".

## Context của subagent: không copy hội thoại của cha, nhưng dùng chung file persona của workspace

**Subagent không nhận context hội thoại của cha.** Với `fork=False` (mặc định), subagent mở một session mới. Docstring ghi: "does NOT inherit the parent agent's dialogue history, accumulated state, or in-progress tool calls". Chỉ khi `fork=True` mới chép state đã lưu của phiên cha sang [6]. Thứ subagent thấy là:
- **Tin nhắn user:** `task` là tin nhắn duy nhất [6].
- **System prompt:** không phải bản chép từ phiên của cha. Nó được *dựng lại* từ cấu hình của chính agent mà subagent mang identity. `spawn_subagent` gửi request với `agent_id` của agent hiện tại và chỉ thêm metadata định tuyến approval (`root_session_id`, `parent_session_id`, cờ `_spawn_subagent`) [6]. Builder dựng prompt từ workspace của agent đó, không có nhánh riêng cho subagent [28]. Prompt gồm:
  - khối "protected execution contract", khoảng 3,5 KB, luôn có [56];
  - các file trong `system_prompt_files` (mặc định `AGENTS.md`, `SOUL.md`, `PROFILE.md`) [12][28];
  - các khối ngữ cảnh thư mục và môi trường;
  - danh sách skill [28][17].

  Hệ quả thực tế: sửa `AGENTS.md` của agent thì prompt của mọi subagent cũng đổi. `spawn_subagent` không có tham số nào cho system prompt.
- **Tools:** `allowed_tools` là whitelist lọc ở bước cuối, gồm cả tool memory. `[]` bỏ hết tool [17].
- **Skills:** `skills` là whitelist trong tập skill của agent. `[]` không nạp skill nào [17].
- **Model:** `subagent_model` chỉ đổi model, không đổi prompt [6].

**Ba cách gắn vai cho subagent:**
1. **Viết chỉ dẫn vai vào `task`.** Mission Mode làm đúng như vậy: master soạn `worker_prompt` hoặc `verifier_prompt` rồi gọi `spawn_subagent(task=..., fork=True, background=True)` [57].
2. **Đóng vai thành skill** rồi truyền `skills=[...]`. **Chưa kiểm chứng:** `preload` có áp dụng cho subagent hay không.
3. **Tạo agent riêng**, có `AGENTS.md` và `system_prompt_files` riêng. Đây là cách duy nhất có system prompt riêng thật sự [5][6].

### Gắn nhãn comment theo batch bằng subagent, ưu tiên tốc độ

Bài toán: có vài trăm đến vài nghìn comment ngôn ngữ tự nhiên. Cần gắn nhãn ý nghĩa cho **từng comment** để thay việc gắn tay, rồi đếm xem ý nào xuất hiện nhiều nhất. Mỗi subagent xử lý một batch khoảng 50–200 comment. Cách để LLM chỉ đọc cả batch rồi trả top 10–20 ý nhanh hơn, nhưng mất liên kết giữa nhãn và comment, nên chỉ dùng để khám phá. Report cũ trong repo đã kết luận cùng hướng: **codebook trước, gán từng bản ghi sau**, có nhãn "khác", đếm bằng code ([gom nghĩa văn bản tự do](../2026-10-21-gom-nghia-van-ban-tu-do-ky-thuat/report.md), [reductive content analysis](../2026-10-21-reductive-content-analysis-llm/report.md)).

**Pipeline đề xuất.** Đây là **nhận định**: suy từ source v2.2.1 và cơ chế sinh token, **chưa đo** trên QwenPaw.

1. **Chốt codebook một lần.** Một subagent (hoặc chính agent cha) đọc một mẫu vài trăm comment và đề xuất 15–30 mã. Mỗi mã có tên ngắn, định nghĩa một câu và ví dụ, cộng thêm mã `OTHER`. Người duyệt rồi khóa codebook. Đây là lượt duy nhất cho LLM tự do quy nạp.
2. **Ghi dữ liệu ra file, không nhét vào `task`.** `task` là tham số tool do LLM của cha *sinh ra*. Nhét 200 comment vào `task` buộc cha gõ lại toàn bộ comment thành token đầu ra, và đây là phần chậm nhất của một lượt LLM. Thay vào đó:
   - dùng script chia comment thành file `batches/b01.jsonl`, `b02.jsonl`…, mỗi dòng gồm `id` và `text`;
   - `task` chỉ ghi codebook (hoặc đường dẫn tới `codebook.md`) và đường dẫn file batch;
   - subagent được `allowed_tools=["read_file", "write_file"]`, `skills=[]` (tên tool lấy từ `agents/tools/file_io.py` [59]).
3. **Đầu ra tối giản**, vì tốc độ sinh token đầu ra quyết định độ trễ:
   - mỗi comment một dòng `id<TAB>mã[,mã]`, ví dụ `1042\tC07,C12`;
   - không lặp lại nội dung comment, không viết giải thích, tối đa 2 mã mỗi comment;
   - với 200 comment, đầu ra khoảng 1–2 nghìn token. Nếu mỗi dòng có JSON và lý do thì có thể gấp 5–10 lần.

   Subagent ghi kết quả ra `labels/b01.tsv` và chỉ trả về một dòng tóm tắt, để context của cha không phình.
4. **Chạy song song:**
   - gọi `spawn_subagent(task="", batch=[{task: "...b01...", allowed_tools: [...], skills: []}, ...])`, mỗi lần tối đa 10 batch, 3 batch chạy cùng lúc [6];
   - đặt `subagent_model` là model nhanh, `thinking_level: "off"` [12];
   - poll bằng `check_agent_task`, chờ 30 giây rồi cách 30–60 giây mỗi lần [6].
5. **Đếm bằng code, không bằng LLM.** Gộp các file `labels/*.tsv` rồi đếm tần suất mỗi mã, mẫu số là số comment. Theo dõi tỷ lệ `OTHER`. Tỷ lệ này cao thì quay lại bước 1 để mở rộng codebook.
6. **Kiểm chất lượng:** chạy lại một batch hai lần để đo độ ổn định, và để người gán tay khoảng 100 comment để so với LLM.

**Chọn cỡ batch.** Batch lớn giảm số lượt gọi và số lần lặp codebook. Batch nhỏ thì mỗi lượt xong sớm hơn, chia đều cho 3 luồng song song tốt hơn, và model ít bỏ sót hay lệch dòng ở cuối danh sách dài. **Nhận định:** 50–100 comment mỗi batch là điểm khởi đầu hợp lý. Kiểm bằng cách đếm số dòng đầu ra so với đầu vào và so `id`.

**Giới hạn khi chạy trong QwenPaw:**
- Mỗi subagent vẫn mang system prompt dựng từ workspace của agent (contract khoảng 3,5 KB, cộng `AGENTS.md`/`SOUL.md`/`PROFILE.md`) và mỗi lần còn tốn một lượt LLM của cha để điều phối.
- Muốn system prompt gọn chỉ còn codebook, có hai cách:
  - tạo agent `labeler` riêng: `system_prompt_files: ["AGENTS.md"]`, `AGENTS.md` chỉ chứa quy tắc gắn nhãn, không skill, không MCP, model nhanh, `thinking_level: "off"`;
  - cho chính agent `labeler` gọi `spawn_subagent`, để subagent kế thừa prompt gọn đó.
- Có thể gọi `labeler` thẳng từ script bằng `qwenpaw agents chat --to-agent labeler` [58]. Khối cấu hình này suy từ schema [12], **chưa chạy thử**.
- **Nhận định:** nếu ưu tiên tuyệt đối là tốc độ và độ song song, gọi thẳng API model (OpenAI-compatible) bằng script vẫn nhanh nhất:
  - không có lượt điều phối, không có contract;
  - system prompt cố định nên tận dụng được prompt cache;
  - độ song song không bị giới hạn 3 luồng của `spawn_subagent` batch.

  QwenPaw khi đó chỉ đóng vai kích hoạt, qua một skill chạy script.

## MCP, tool và bảo mật mặc định khá mở; memory và heartbeat cần bật thêm

**MCP.** Thêm MCP qua Console (Agent → MCP) bằng cách dán JSON `{"mcpServers": {...}}`. Hỗ trợ ba transport: `stdio` (có `command`), `streamable_http` và `sse` (có `url`). MCP local cần Node.js 18+ [35]. Từ v2.x, mỗi MCP client được lưu thành driver card `workspaces/<id>/drivers/mcp/<name>.yaml` với access policy riêng (allow/deny/ask, **mặc định ask**). Card quản lý ở Agent → MCP → "Tools & Access" [10]. Ở lần khởi động đầu, `mcp.clients` cũ trong `agent.json` được chuyển một lần sang card, rồi `mcp.migration_version` được đặt bằng 2 [36]. **Nhận định:** sau migration, sửa `mcp.clients` trong `agent.json` có thể không còn tác dụng, nên quản lý MCP qua Console. Điểm này chưa được test. Source còn có các field docs chưa ghi: `http_timeout`, `tools` (whitelist) và `oauth` [12].

```json
{"mcpServers": {
  "remote-api": {"transport": "streamable_http", "url": "https://api.example.com/mcp",
                 "headers": {"Authorization": "Bearer ..."}},
  "local-fs":   {"command": "npx", "args": ["-y", "some-mcp-server"]}
}}
```

**Tools.** Bật/tắt từng tool ở Console Agent → Tools, hoặc trong `agent.json` → `tools.builtin_tools.<tên>.{enabled, display_to_user, async_execution, config}`. Ví dụ, provider web search chọn qua `tools.builtin_tools.web_search.config.provider` (`tavily` hoặc `anysearch`) [35][37]. Docs khuyên "enable only the tools you need to reduce context overhead" [35].

**Bảo mật.** Có bốn núm chính. `approval_level` trong `agent.json` nhận STRICT/SMART/**AUTO** (mặc định)/OFF. Tool Guard dùng rule regex cho shell; finding CRITICAL/HIGH như `sudo` hay pipe-to-shell phải chờ duyệt, hết **300 giây** (mặc định của `QWENPAW_TOOL_GUARD_APPROVAL_TIMEOUT_SECONDS`) thì bị từ chối [9], còn ở ngữ cảnh không tương tác thì chỉ ghi log, nên muốn chặn hẳn phải dùng `denied_tools`. File Guard mặc định đưa `~/.qwenpaw.secret/` vào danh sách file nhạy cảm. Sandbox (bubblewrap/Landlock trên Linux, Seatbelt trên macOS) **mặc định tắt**: `security.sandbox_enabled=false` trong `config.json` [10][12]. Bật sandbox thì `uv`/`pip`/`npm` sẽ lỗi cho tới khi thêm rule kiểu `Write(~/.cache/uv/**)` vào `policy.yaml`. Trong Docker, sandbox thường rơi về `mode=none` [10][38]. Đăng nhập web tắt mặc định và chỉ bật bằng `QWENPAW_AUTH_ENABLED=true`. Ngay cả khi bật, request từ localhost vẫn bỏ qua xác thực [10]. **Nhận định:** với máy cá nhân trên Linux, giữ AUTO, cài `bwrap` và bật `sandbox_enabled`, đặt policy MCP tin cậy là `allow`, và bật auth trước khi bind `--host 0.0.0.0`.

**Persona và memory.** Persona gồm `AGENTS.md` (quy trình), `SOUL.md` (giọng điệu, ranh giới) và `PROFILE.md`, ghép vào prompt theo thứ tự `system_prompt_files`. Cảnh báo: **đổi `language` trong Console sẽ ghi đè cả ba file** bằng template mới, nên tải workspace về trước khi đổi [39]. Memory mặc định dùng ReMe (`remelight`), lưu dạng Markdown. Auto-Memory ghi `memory/YYYY-MM-DD/*.md` sau mỗi **5** lượt. Auto-Dream chạy cron `0 23 * * *` để tổng hợp vào `digest/`. `MEMORY.md` **không** nằm trong `system_prompt_files` mặc định và cũng không thuộc index của `memory_search`; agent đọc nó khi cần bằng tool đọc file [40][39]. Tự động tìm memory (`running.reme_light_memory_config.auto_memory_search_config.enabled`) **mặc định tắt**, và vector search chỉ hoạt động khi đã cấu hình embedding. Thiếu embedding thì chỉ còn BM25 [40][3].

**Heartbeat và cron.** Heartbeat gửi toàn bộ nội dung `HEARTBEAT.md` như một tin nhắn user theo chu kỳ. Cấu hình ở `agent.json` → `heartbeat`: `enabled` (mặc định false), `every` (`30m`, `2h30m` hoặc cron 5 trường; mặc định source là `6h`), `target` (`main`/`last`/`inbox`) và `activeHours` [41][9]. Cron cho phép nhiều job, mỗi job có lịch, channel và target riêng, lưu trong `jobs.json`. Quản lý bằng `qwenpaw cron list|create|state|run|pause|resume|delete` hoặc nhắn trong chat. Muốn sửa hay xóa job thì phải disable trước [42].

## Lỗi thường gặp tập trung ở timeout và tương thích provider, không phải ở cài đặt

Nhãn `installation-bug` không có issue nào cho v2.2.x. Các sự cố của v2.2.1 chủ yếu thuộc ba nhóm [43]. Nhóm thứ nhất là **timeout multi-agent**. Ở #7678, subtask của `spawn_subagent` không bao giờ xong; maintainer chỉ ra subagent bị ngắt sau khoảng 10 phút, khớp `timeout=600`, và khuyên bảo agent chính truyền `timeout` bằng 1800. Issue do người báo tự đóng, không có fix được xác nhận [11]. Ở #7981, khi `chat_with_agent` hết 300 giây, agent cha nhận "The tool call has been interrupted by the user" và lượt kết thúc không có câu trả lời. Fix #8183 **chỉ có trong v2.2.2** [44]. Phiên gọi giữa các agent còn có thể bị hủy âm thầm bằng `CancelledError` (#8252, đóng 2026-10-21 qua PR #8317, sau v2.2.2.post1 vốn chỉ có ba thay đổi về bảo mật và version) [45][19], và mỗi tin nhắn có thể tạo session mới nếu không truyền `session_id` (#6918, #8078) [45]. Nhóm thứ hai là **provider**: model free bị khai tử (#8218); schema tool có `anyOf` bị Kimi từ chối (#7959); file part thiếu `file_id` bị trả lỗi 400 (#8280); `APITimeoutError` lặp hàng giờ trên WSL2 tới khi restart (#7935, chưa tái hiện được) [21][43][46]. Nhóm thứ ba là **context và UI**. Turn dài nhiều tool có thể vượt giới hạn provider dù đã có compaction, ví dụ **289.259** và **313.235** token so với giới hạn **267.904** (#7628, còn mở). Người báo nghi phần đếm context bỏ sót system prompt và schema tool; một comment khác thấy khối reasoning chiếm khoảng 81% số byte của một request lỗi. Nguyên nhân chưa được maintainer xác nhận [47]. Model chọn ở dropdown Chat có thể bị mất (#7708) [48]. Output cron trông như trống vì UI gập các bước thực thi (#7709) [49].

**Nhận định:** checklist vận hành rút từ các issue trên: đặt model mặc định ở Settings → Models thay vì chỉ chọn ở dropdown Chat; với model local, đặt context ≥ 32K; bật ít tool và MCP để tránh #7628; khi lỗi MCP thì đặt `QWENPAW_LOG_LEVEL=debug` (MCP mất session khi idle đã được tự kết nối lại từ v2.1.0) [50]; với việc dài thì ưu tiên `submit_to_agent` hoặc background; backup `~/.qwenpaw` và `~/.qwenpaw.secret` riêng.

## Các nguồn bất đồng ở đâu

Docs trong repo ở tag v2.2.1 lệch với source cùng tag ở ít nhất mười điểm. Nguyên tắc chung: source là thứ thật sự chạy, nên tin source (hoặc giá trị hiển thị trong Console). Docs nhiều khả năng chưa được cập nhật theo code.

| Điểm | Docs nói | Source v2.2.1 | Hệ quả |
|---|---|---|---|
| `agents.profiles` trong `config.json` | có `name`, `description` | chỉ `id`, `workspace_dir`, `enabled`, `pinned` (bỏ qua field khác) [12] | đặt tên, mô tả trong `agent.json` |
| Template agent | ví dụ `--template coder` [20] | chỉ `default`, `local`, `qa` [31] | **Nhận định:** `coder` sẽ báo "Unsupported template" |
| Skill builtin | bảng 14 dòng, có `news` [4] | 16 skill, không có `news`, có thêm `chat_with_agent`, `make-skill`, `make_plan` [25] | kiểm bằng `qwenpaw skills list --pool` |
| Chữ ký Skill Scanner | có `resource_abuse` [10] | 8 file, không có `resource_abuse` [51] | lớp quét mỏng hơn docs mô tả |
| `running.max_iters` | ví dụ JSON ghi 50 | 100 [12] | |
| `language` mặc định | ví dụ ghi `en` | `zh`; `init --defaults` dùng `zh` [12][39] | persona sinh ra bằng tiếng Trung nếu không đổi |
| Heartbeat `every` | bảng config ghi `30m` [3] | `6h` (docs heartbeat cũng ghi khoảng 6 giờ) [9][41] | |
| MCP mặc định | tự tạo client `tavily_search` [35] | client mặc định là `anysearch` (tắt); Tavily là provider của tool `web_search` [12][37] | đặt `TAVILY_API_KEY` để có web search, không phải MCP |
| `approval_level: OFF` | "all tool calls execute directly" [10] | khi có security finding vẫn chuyển sang ASK [52] | OFF không tắt hẳn phê duyệt |
| Vị trí `security` | security docs: `config.json`; config docs: `agent.json` | có ở cả hai; `sandbox_enabled` chỉ đọc từ `config.json` [12] | |
| Cộng tác multi-agent | phải bật skill "Multi-Agent Collaboration" [5] | tool đã bật sẵn; skill chỉ dạy cách dùng [13] | kiểm cả Workspace → Tools lẫn Skills |

Ngoài ra, ngày phát hành v2.2.1 lệch một ngày giữa PyPI (2026-09-11) và README (2026-09-10) [1][14]. Field `heartbeat.target="inbox"` có trong docs heartbeat nhưng không có trong bảng của docs config [41][3].

## Kết luận và hàm ý

Điều quan trọng nhất cho người tự vận hành là mô hình tư duy. QwenPaw là nhiều **agent cấu hình sẵn**, mỗi agent một thư mục `workspaces/<id>/`, còn "subagent" chỉ là công cụ nhân bản tạm thời bên trong một agent. Vì vậy, muốn có một trợ lý chuyên review code với model rẻ, cách làm là tạo một agent riêng, đặt `description` rõ ràng, gán `active_model` riêng, rồi để agent chính gọi nó qua `chat_with_agent`. Với việc phụ trong cùng project thì chỉ cần `spawn_subagent`, kèm `subagent_model` để giảm phí. Skill cũng theo tư duy hai tầng tương tự: viết một lần (tốt nhất trong `skill_paths` có git), rồi broadcast và bật cho từng agent.

Hàm ý thực tế là nên cài v2.2.2.post1 thay vì pin v2.2.1, trừ khi cần đúng bản này. Hai lỗi đau nhất khi dùng multi-agent và skill bên thứ ba (#7981 và #8065) chỉ được sửa ở v2.2.2, trong khi docs quickstart, CLI và skills ở nhánh main hiện vẫn giống hệt tag v2.2.1 [2][20][4]. Dù chạy bản nào, nên chủ động siết các mặc định mở: bật sandbox, đặt scanner về `block`, bật auth nếu mở cổng. Khi docs và Console nói khác nhau, tin Console và source.

## Chưa kiểm chứng được

- Chưa chạy thử thực tế bất kỳ cấu hình nào. Khối `agent.json` mẫu suy ra từ schema `AgentProfileConfig`. Chưa kiểm hot reload `active_model` khi sửa tay `agent.json`.
- Chưa xác nhận tag Docker `agentscope/qwenpaw:2.2.1` có trên Docker Hub.
- Chưa tìm thấy field cụ thể cho per-agent model routing/fallback mới ở v2.2.1 (#7501) ngoài `fallback_models`/`llm_routing`. Issue #7749 cho thấy người dùng cũng không tìm ra [53].
- Chưa đọc schema đầy đủ của `policy.yaml`, `providers.json` (có mã hóa bằng master key hay không) và `jobs.json`.
- Chưa xác minh việc sửa `mcp.clients` sau migration có còn được runtime đọc hay không. Chưa xác minh giới hạn độ sâu lồng subagent bằng chạy thật (grep `depth`, `nested`, `MAX_DEPTH` không ra kết quả).
- Chưa đo độ trễ thực tế của pipeline gắn nhãn comment (subagent theo batch, agent `labeler` riêng, gọi thẳng API); các khuyến nghị về cỡ batch và định dạng đầu ra là nhận định từ source và cơ chế sinh token. Chưa kiểm giới hạn 3 luồng đồng thời có áp dụng khi gọi nhiều lần `spawn_subagent` batch song song hay không. Chưa xác nhận skill bật `preload` có được chèn vào prompt của subagent hay không, và chưa đo kích thước thật của các khối ngữ cảnh môi trường.
- Chưa thử chạy skill OpenClaw hay Claude Code thật. Các field frontmatter riêng của Claude Code (`allowed-tools`, `disable-model-invocation`) không thấy xử lý trong source, nhiều khả năng bị bỏ qua.
- Không mở được docs site `qwenpaw.agentscope.io`, help.aliyun.com, IT之家, AIbase (lỗi DNS). GitHub API và search bị chặn (403), nên chỉ duyệt trang đầu danh sách issue. Không tìm thấy blog hay hướng dẫn cộng đồng bậc 2 nào (truy vấn: "QwenPaw skills issue github SKILL.md", "QwenPaw issue MCP sandbox approval config github", "QwenPaw github issue install error qwenpaw app").

## Nguồn

[1] PyPI qwenpaw — Release history — agentscope, truy cập 2026-10-23 (bậc 1). https://pypi.org/project/qwenpaw/#history
[2] Quick Start (docs, nhánh main) — agentscope-ai, 2026-10 (bậc 1). https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/website/public/docs/quickstart.en.md
[3] Config & Working Directory (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/config.en.md
[4] Skills (docs, tag v2.2.1; giống hệt bản main 2026-10-22) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md
[5] Multi-Agent (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/multi-agent.en.md
[6] src/qwenpaw/agents/tools/agent_management.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/tools/agent_management.py
[7] Release v2.2.1 (kèm website/public/release-notes/v2.2.1.md) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.2.1
[8] Release v2.2.0 — agentscope-ai, 2026-09-03 (bậc 1). https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.2.0
[9] src/qwenpaw/constant.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/constant.py
[10] Security (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/security.en.md
[11] Issue #7678 "spawn subAgent" — GitHub agentscope-ai/QwenPaw, đóng 2026-10-10 (bậc 1 cho phần trả lời của maintainer). https://github.com/agentscope-ai/QwenPaw/issues/7678
[12] src/qwenpaw/config/config.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/config/config.py
[13] src/qwenpaw/runtime/tool_registry.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/runtime/tool_registry.py
[14] README QwenPaw (nhánh main) — agentscope-ai, truy cập 2026-10-23 (bậc 1). https://raw.githubusercontent.com/agentscope-ai/QwenPaw/main/README.md
[15] FAQ (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/faq.en.md
[16] Release v2.0.0 — agentscope-ai, 2026-07-10 (bậc 1). https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.0.0
[17] src/qwenpaw/runtime/builder.py và pyproject.toml (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/runtime/builder.py
[18] Release notes v2.2.2 — agentscope-ai, 2026-10-15 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/main/website/public/release-notes/v2.2.2.md
[19] GitHub Releases của QwenPaw (v2.2.2, v2.2.2.post1) — agentscope-ai, 2026-10-15 và 2026-10-22 (bậc 1). https://github.com/agentscope-ai/QwenPaw/releases
[20] CLI (docs, tag v2.2.1 và nhánh main) — agentscope-ai, 2026-09-11 / 2026-10 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/cli.en.md
[21] Issue #8218 (MODEL_EXECUTION_ERROR, model free bị ngừng) — GitHub agentscope-ai/QwenPaw, đóng 2026-10-15 (bậc 1). https://github.com/agentscope-ai/QwenPaw/issues/8218
[22] Models (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/models.en.md
[23] Channels (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/channels.en.md
[24] src/qwenpaw/agents/skill_system/ (store.py, workspace_service.py, registry.py; source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/skill_system/store.py
[25] Thư mục skill builtin src/qwenpaw/agents/skills (tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/tree/v2.2.1/src/qwenpaw/agents/skills
[26] Commands (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/commands.en.md
[27] agentscope 2.0.7.post1 (tool/_toolkit.py, tool/_builtin/_skill.py trong wheel) — PyPI/AgentScope (bậc 1). https://pypi.org/project/agentscope/2.0.7.post1/
[28] src/qwenpaw/runtime/prompt_contributors.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/runtime/prompt_contributors.py
[29] QwenPaw Hub (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/hub.en.md
[30] ACP Integration (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/acp-integration.en.md
[31] src/qwenpaw/agents/templates.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/templates.py
[32] Issue #7676 (subagent_model, người báo tự rút lại) — GitHub agentscope-ai/QwenPaw, 2026-09 (bậc 3, chỉ dùng kèm source [6]). https://github.com/agentscope-ai/QwenPaw/issues/7676
[33] GitHub Releases, lọc "subagent" — agentscope-ai, 2026 (bậc 1). https://github.com/agentscope-ai/QwenPaw/releases?q=subagent&expanded=true
[34] Loop Engineering / Mission Mode (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/loop-engineering.en.md
[35] MCP & Built-in Tools (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/mcp.en.md
[36] src/qwenpaw/drivers/adapters/mcp_legacy_config.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/drivers/adapters/mcp_legacy_config.py
[37] src/qwenpaw/agents/tools/websearch/factory.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/tools/websearch/factory.py
[38] src/qwenpaw/governance/resource_governor.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/governance/resource_governor.py
[39] Agent Persona (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/persona.en.md
[40] Long-Term Memory (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/memory.en.md
[41] Heartbeat (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/heartbeat.en.md
[42] Scheduled Tasks (docs, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/cron.en.md
[43] Danh sách issue nhãn bug có "2.2.1" và nhãn installation-bug — GitHub agentscope-ai/QwenPaw, truy cập 2026-10-23 (bậc 1). https://github.com/agentscope-ai/QwenPaw/issues?q=is%3Aissue+label%3Abug+2.2.1
[44] Issue #7981 (chat_with_agent timeout 300s) — GitHub agentscope-ai/QwenPaw, đóng 2026-10-13 qua PR #8183 (bậc 1). https://github.com/agentscope-ai/QwenPaw/issues/7981
[45] Issue search "chat_with_agent" (#8252, #6918, #8078) — GitHub agentscope-ai/QwenPaw, truy cập 2026-10-23 (bậc 1). https://github.com/agentscope-ai/QwenPaw/issues?q=chat_with_agent
[46] Issue #7935 (APITimeoutError lặp trên WSL2) — GitHub agentscope-ai/QwenPaw, mở 2026-09-22 (bậc 1). https://github.com/agentscope-ai/QwenPaw/issues/7935
[47] Issue #7628 (context compaction vượt ngân sách provider) — GitHub agentscope-ai/QwenPaw, mở 2026-09-08 (bậc 1). https://github.com/agentscope-ai/QwenPaw/issues/7628
[48] Issue #7708 (configured LLM lost) — GitHub agentscope-ai/QwenPaw, mở 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/issues/7708
[49] Issue #7709 (cron tasks often produce no output) — GitHub agentscope-ai/QwenPaw, mở 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/issues/7709
[50] Issue #6732 (MCP tools fail intermittently) — GitHub agentscope-ai/QwenPaw, 2026-08-06 → 2026-08-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/issues/6732
[51] Thư mục chữ ký Skill Scanner src/qwenpaw/security/skill_scanner/rules/signatures (tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/tree/v2.2.1/src/qwenpaw/security/skill_scanner/rules/signatures
[52] src/qwenpaw/governance/policy.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/governance/policy.py
[53] Issue #7749 (model failover config location) — GitHub agentscope-ai/QwenPaw, mở 2026-09-14 (bậc 1). https://github.com/agentscope-ai/QwenPaw/issues/7749
[54] Release notes v1.1.0 "CoPaw is Officially Rebranding to QwenPaw" — agentscope-ai, 2026-04 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/main/website/public/release-notes/v1.1.0.md
[55] PR #8063 "wake parent agent session when a background task finishes" — GitHub agentscope-ai/QwenPaw, mở 2026-09-30, còn mở 2026-10-23 (bậc 1). https://github.com/agentscope-ai/QwenPaw/pull/8063
[56] src/qwenpaw/runtime/protected_prompt.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/runtime/protected_prompt.py
[57] src/qwenpaw/modes/mission/prompts.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/modes/mission/prompts.py
[58] src/qwenpaw/cli/agents_cmd.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/cli/agents_cmd.py
[59] src/qwenpaw/agents/tools/file_io.py (source, tag v2.2.1) — agentscope-ai, 2026-09-11 (bậc 1). https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/tools/file_io.py
