# Subagent và multi-agent trong QwenPaw v2.2.1

Phạm vi kiểm chứng: đọc source tại tag `v2.2.1` (commit `cae5773`, 2026-09-11) của repo `agentscope-ai/QwenPaw`, docs trong `website/public/docs/` cùng tag, release notes trên GitHub và các issue. Bản mới nhất lúc research là `v2.2.2` (2026-10-15). Viết tắt: `src/` = `src/qwenpaw/` tại tag v2.2.1; `docs/` = `website/public/docs/` tại tag v2.2.1.

Link gốc source: `https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/<path>`.

## 1. Agent, workspace và subagent; tạo nhiều agent với workspace, model, skills, channel riêng

### Kết luận ngắn
QwenPaw có ba lớp: (a) **agent** là một "persona" độc lập, mỗi agent một workspace `~/.qwenpaw/workspaces/{agent_id}/` với `agent.json` riêng (channel, MCP, tools, model, heartbeat...), lịch sử chat, cron, skill và persona riêng; (b) **subagent** là phiên phụ tạm thời của *chính agent đó*, sinh ra bằng tool `spawn_subagent`; (c) **external agent** qua ACP. Tạo agent bằng Console (Settings → Agent Management), CLI `qwenpaw agents create` hoặc REST `POST /api/agents`. Chắc chắn: **cao** (docs chính thức và source khớp nhau, trừ vài chỗ docs cũ ghi ở dưới).

### Phát hiện có nguồn
- Multi-agent có từ v0.1.0. Mỗi agent có persona, lịch sử hội thoại, skills và channel riêng: "Remembers its own conversations (no cross-talk)", "Uses different skills", "Connects to different channels". — [docs/multi-agent.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/multi-agent.en.md) (bậc 1, tag 2026-09-11)
- Dùng chung giữa các agent: cấu hình model provider (API key) và biến môi trường. Riêng từng agent: channel, bật/tắt skill, lịch sử chat, cron job, file persona. — cùng nguồn (mục "What can agents share?")
- Cấu trúc thư mục: `~/.qwenpaw/config.json` là cấu hình toàn cục (gồm `agents.profiles`), còn `~/.qwenpaw/workspaces/<id>/` chứa `agent.json`, `chats.json`, `jobs.json`, `token_usage.json`, `AGENTS.md`, `SOUL.md`, `PROFILE.md`, `MEMORY.md`, `skills/`... Trạng thái bật/tắt skill nằm ở `workspaces/{agent_id}/skill.json`. Provider nằm ở `~/.qwenpaw.secret/providers.json`, env ở `~/.qwenpaw.secret/envs.json`. — [docs/config.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/config.en.md) (bậc 1, 2026-09-11)
- Giá trị trong `agent.json` thắng `config.json` khi trùng field. `agent.json` được hot reload: hệ thống kiểm tra thay đổi mỗi 2 giây. — cùng nguồn
- Trong source, `config.json` chỉ giữ tham chiếu `AgentProfileRef` gồm `id`, `workspace_dir`, `enabled`, `pinned` (`extra="ignore"`). Cấu hình đầy đủ (`name`, `description`, `channels`, `mcp`, `heartbeat`, `active_model`, `fallback_models`, `subagent_model`, `thinking_level`, `language`, `approval_level`, `system_prompt_files`, `tools`, `security`, `acp`, `plan`, `coding_mode`, `mail`, `running`, `llm_routing`, `project_dir`, `backend`, `template_id`) nằm ở `AgentProfileConfig` trong `agent.json`. `AgentsConfig` có `active_agent` (mặc định `"default"`), `agent_order` và `profiles`. — [src/config/config.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/config/config.py) dòng ~1976–2400 (bậc 1, source)
  - Ví dụ `config.json` trong docs đặt `name` và `description` trong `agents.profiles`, trái với model trong source. **Nhận định:** docs chưa cập nhật; tên và mô tả thực sự đọc từ `agent.json`.
- Mỗi agent tự chọn model: `active_model` (provider_id + model), `fallback_models`, `fallback_policy`, `llm_routing` (route local/cloud). v2.2.1 thêm "Configure model routing separately for each Agent, including provider preferences and fallback behavior" (#7501). — source như trên; [Release v2.2.1](https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.2.1) (bậc 1, 2026-09-11)
- Tạo agent trên Console: Settings → Agent Management → Create Agent, điền Name, **Description** (quan trọng, vì agent khác đọc nó để chọn người cộng tác) và ID (bỏ trống để tự sinh). Agent Selector nằm ở góc trên bên trái. Sau khi chuyển agent, chỉnh riêng: Control → Channels, Workspace → Skills / Tools / Files (AGENTS.md, SOUL.md). Agent `default` không xóa được. Xóa agent vẫn giữ thư mục workspace, muốn xóa hẳn thì xóa tay `~/.qwenpaw/workspaces/{agent_id}`. — [docs/multi-agent.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/multi-agent.en.md) (bậc 1)
- CLI: `qwenpaw agents list|create|delete|chat` (alias `qwenpaw agent`). Option của `create` trong source: `--name`, `--agent-id`, `--description`, `--workspace-dir`, `--language`, `--template`, `--skill` (lặp được), `--provider-id`, `--model-id`. Lệnh `delete` có `--remove-workspace` và `--yes`. — [docs/cli.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/cli.en.md); [src/cli/agents_cmd.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/cli/agents_cmd.py) (bậc 1)
- Template builtin trong source chỉ có `default`, `local` và `qa`. `local` bật sẵn `list_agents`, `chat_with_agent`, `submit_to_agent`, `check_agent_task`, shell và các tool file, kèm skill `make_plan` (cho agent chạy model local nhỏ, cần "escalate" việc lập kế hoạch). `qa` chỉ bật shell, read/write/edit file và view_image. — [src/agents/templates.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/templates.py), `build_local_agent_tools_config` trong config.py (bậc 1)
  - Docs CLI có ví dụ `--template coder`, nhưng `coder` không có trong `SUPPORTED_AGENT_TEMPLATES`. **Nhận định:** lệnh đó sẽ báo lỗi "Unsupported template".
- Lệnh có `--agent-id` (mặc định `default`): `channels`, `cron`, `daemon`, `chats`, `skills`. Lệnh toàn cục: `init`, `providers`, `models`, `env`. — [docs/multi-agent.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/multi-agent.en.md)
- REST: `GET/POST /api/agents`, `GET/PUT/DELETE /api/agents/{agent_id}`, `POST /api/agents/{agent_id}/active`. Các API theo agent nhận header `X-Agent-Id` (`/api/chats`, `/api/cron`, `/api/config`, `/api/skills`, `/api/tools`, `/api/mcp`, `/api/agent`). — cùng nguồn
- Có thể chạy nhiều agent cùng lúc, mỗi agent trả lời trên channel của mình. Agent rảnh không gọi LLM nên không tốn phí. — cùng nguồn (FAQ)
- Docs khuyên dùng 3–5 agent và đặt ID có nghĩa (`code-reviewer`, không đặt `abc123`). — cùng nguồn (Best Practices)
- `PROFILE.md` được sinh tự động từ name, description, skills và persona. Agent khác đọc Description và PROFILE.md khi quyết định cộng tác. — cùng nguồn

### Nhận định
- "Agent" của QwenPaw gần với một *instance/persona* có cấu hình riêng hơn là một worker. "Subagent" (spawn_subagent) là bản sao tạm thời của cùng agent, không phải một agent cấu hình khác.

### Khoảng trống
- Docs chưa liệt kê đầy đủ field của `agent.json` cho `subagent_model` và `llm_routing`; mới xác nhận qua source.
- Chưa kiểm thử thực tế việc đổi `agent.json` tay có hot reload `active_model` hay không (docs chỉ nói về channel).

## 2. Giao việc giữa các agent: tool nào, chạy nền/song song, nhận kết quả; "subagent" chính thức ở v2.x?

### Kết luận ngắn
Có: v2.2.1 có bộ tool builtin chính thức gồm `list_agents`, `chat_with_agent` (đồng bộ), `submit_to_agent` + `check_agent_task` (chạy nền, poll), `spawn_subagent` (subagent tạm thời trong cùng workspace, có foreground, background, batch song song và `fork` với git worktree) và `delegate_external_agent` (gọi agent ngoài qua ACP, mặc định tắt). Có thêm skill `multi_agent_collaboration` / `chat_with_agent`, CLI `qwenpaw agents chat` và Mission Mode `/mission` (master → worker → verifier, dùng `spawn_subagent`). Chắc chắn: **cao** (đọc trực tiếp source).

### Phát hiện có nguồn
- Docs chia ba chế độ cộng tác:

  | Chế độ | Workspace | Lịch sử | Dùng khi |
  |---|---|---|---|
  | `chat_with_agent` | workspace của agent đích | không (chỉ text) | gọi agent chuyên gia |
  | `spawn_subagent(fork=False)` | cùng project với cha | không (session trống) | việc con độc lập |
  | `spawn_subagent(fork=True)` | tùy môi trường | toàn bộ lịch sử cha | việc phụ cần ngữ cảnh, có thể sửa file |

  — [docs/multi-agent.en.md, Part 3](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/multi-agent.en.md) (bậc 1)
- `spawn_subagent` có từ **v1.1.10** ("New `spawn_subagent` tool for ephemeral in-workspace sub-agent execution", #4806). Ở v2.0.0-beta.2 có "fix(runtime): restore spawn_subagent for Runtime 2.0" (#5660). — [GitHub Releases](https://github.com/agentscope-ai/QwenPaw/releases?q=subagent&expanded=true) (bậc 1)
- Chữ ký các tool trong source v2.2.1 (`src/agents/tools/agent_management.py`):
  - `list_agents()` trả về JSON gồm id, name, description và workspace của mọi agent.
  - `chat_with_agent(to_agent, text, session_id=None, timeout=300)` chờ agent đích trả lời xong, trả `[SESSION: ...]` kèm nội dung. Truyền lại `session_id` để hỏi tiếp trong cùng ngữ cảnh.
  - `submit_to_agent(to_agent, text, session_id=None, task_timeout=None)` trả ngay `[TASK_ID]` và `[SESSION]`. Bỏ `task_timeout` thì server dùng `DEFAULT_STREAM_TASK_TIMEOUT_SECONDS = 3600`.
  - `check_agent_task(task_id)` trả trạng thái submitted → pending → running → finished, rồi completed hoặc failed.
  - `spawn_subagent(task, fork=False, background=False, timeout=None, allowed_tools=None, skills=None, batch=None)`.

  — [src/agents/tools/agent_management.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/tools/agent_management.py) (bậc 1)
- Chi tiết `spawn_subagent` (docstring):
  - Subagent "starts a fresh conversation context", cùng identity, workspace và (mặc định) toàn bộ tools và skills của cha.
  - `allowed_tools` là whitelist tên tool (`[]` = cấm mọi tool). `skills` là whitelist tên skill.
  - Foreground chờ tối đa `DEFAULT_SPAWN_FOREGROUND_TIMEOUT_SECONDS = 600` giây. Background mặc định 3600 giây.
  - Với `background=True`, docstring dặn model "Wait at least 30 seconds before the first check_agent_task call, and use 30-60 second intervals".
  - `batch` là danh sách spec (`task`, `fork`, `timeout`, `allowed_tools`, `skills`). Mọi task trong batch chạy nền, tối đa `MAX_SPAWN_BATCH_SIZE = 10` task, đồng thời tối đa `MAX_SPAWN_BATCH_CONCURRENCY = 3`.

  — cùng file, dòng 38–39 và 1147–1345; [src/constant.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/constant.py) dòng 225–227 (bậc 1)
- Subagent là tạm thời ("Ephemeral: Subagents cannot be resumed"). Muốn hội thoại nhiều lượt thì dùng `chat_with_agent` kèm `session_id`. — [docs/multi-agent.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/multi-agent.en.md)
- Hành vi của `fork=True`:
  - Coding Mode bật và project_dir là git repo: tạo worktree ở `<project_dir>/.qwenpaw/worktrees/`.
  - Coding Mode tắt nhưng workspace là git repo: tạo worktree ở `<workspace_dir>/.qwenpaw/worktrees/`.
  - Không có git: fork tại chỗ, không cô lập file.
  - Nếu subagent có sửa file thì worktree được giữ lại và tool trả `[FORK_BRANCH: fork/...]` để merge tay. Không sửa gì thì worktree tự xóa. Chế độ background không tự dọn worktree.
  - File `.worktreeinclude` ở gốc project liệt kê file bị gitignore (vd `.env`) cần copy vào worktree.

  — cùng nguồn
- Subagent hiện trong Console thành nhóm chat riêng (`SUBAGENT_CHAT_GROUP_ID = "subagents"`, session source `subagent`, có `parent_session_id` và `root_session_id`). v2.2.0 thêm "Organize subagent conversations into groups and surface completion and unread status" (#7035, #7275). — [src/app/chats/models.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/app/chats/models.py); [src/app/routers/console.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/app/routers/console.py); [Release v2.2.0](https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.2.0) (bậc 1, 2026-09-03)
- Yêu cầu phê duyệt (approval) của subagent và của agent được gọi đi theo `root_session_id` về phiên gốc ("fix(subagent): route and resolve approvals from the root session", #6295, v2.0.1-beta.1). `spawn_subagent` kế thừa `approval_level` của phiên (#6508, v2.1.0-beta.1). — [Releases](https://github.com/agentscope-ai/QwenPaw/releases?q=subagent&expanded=true); source `chat_with_agent` lấy `get_current_root_session_id()` (bậc 1)
- Skill builtin `multi_agent_collaboration` (v1.4) dạy agent gọi qua CLI `qwenpaw agents chat --from-agent ... --to-agent ... --text ...`, dùng `--background` và `--task-id`, `--session-id`. Luật của skill: không tự gọi agent khác nếu tự làm được, không đoán ID mà phải `list` trước, "Do not call back the source agent". Skill `chat_with_agent` (v1.2) có quy tắc tương tự cho tool cùng tên. — [src/agents/skills/multi_agent_collaboration-en/SKILL.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/skills/multi_agent_collaboration-en/SKILL.md); [chat_with_agent-en/SKILL.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/skills/chat_with_agent-en/SKILL.md) (bậc 1)
- CLI `qwenpaw agents chat`:
  - Bắt buộc `--from-agent` (alias `--agent-id`), `--to-agent` và `--text`.
  - Tùy chọn `--session-id`, `--mode final|stream` (stream không dùng cùng `--background`), `--timeout` (mặc định 300), `--base-url`, `--json-output`.
  - Khác `qwenpaw channels send` ở chỗ hai chiều và có trả lời.

  — [docs/cli.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/cli.en.md) (bậc 1)
- Tool agent-to-agent mặc định bật: trong `tool_registry.py`, `enabled_by_default` mặc định là `True`. Chỉ `delegate_external_agent` (và một tool file) khai báo `enabled_by_default=False`. — [src/runtime/tool_registry.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/runtime/tool_registry.py) dòng 75; [delegate_external_agent.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/tools/delegate_external_agent.py) dòng 928 (bậc 1)
  - **Nhận định:** tool đã bật sẵn nhưng docs (Part 2) vẫn yêu cầu bật skill "Multi-Agent Collaboration". Skill chủ yếu dạy model *khi nào* và *cách* cộng tác. Nên kiểm tra cả trang Workspace → Tools lẫn Skills.
- `delegate_external_agent(action, runner, message, cwd, max_runtime=300)` với action `list/status/start/message/respond/close` gọi runner ACP ngoài (ví dụ builtin: `opencode`, `qwen_code`, `claude_code`, `codex`). Cần cấu hình runner ở Workspace → ACP rồi bật tool. Permission request phải hỏi người dùng rồi trả đúng option id. — [docs/acp-integration.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/acp-integration.en.md); source như trên (bậc 1)
- Mission Mode: `/mission <task> [--max-iterations 30] [--verify "pytest tests/"]`, `/mission status`, `/mission list`. Chia task thành user story, chạy pipeline master → worker → verifier với ngữ cảnh cô lập. Prompt master bắt buộc dùng `spawn_subagent(... fork=True ...)` cho worker và `background=True` cho verifier, theo dõi bằng `check_agent_task`. Cảnh báo: "Worker and verifier agents automatically bypass the security guard ... Use Mission Mode only in fully trusted codebases". Có từ v2.0.0 (Normal/Mission/Goal Mode, #5665, #5727). — [docs/loop-engineering.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/loop-engineering.en.md); [docs/commands.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/commands.en.md); [src/modes/mission/prompts.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/modes/mission/prompts.py) (bậc 1)
- Đội agent nhiều máy: docs "Agent Team Practice" dùng QwenPaw kèm AgentTeams/HiClaw (hiclaw.io) bên ngoài, gồm Leader và Workers, deploy bằng Docker hoặc Helm. Đây là giải pháp ngoài core. — [docs/practice-agent-team.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/practice-agent-team.en.md) (bậc 1)

### Nhận định
- Với người dùng cá nhân: chỉ cần chạy một việc phụ trên cùng project thì dùng `spawn_subagent`. Cần "chuyên gia" có persona, model hay tool riêng thì tạo agent riêng và dùng `chat_with_agent` hoặc `submit_to_agent`. Việc lớn tự động nhiều bước thì dùng `/mission`. Khi cần agent code ngoài (Claude Code, Codex...) thì dùng `delegate_external_agent`.
- Song song thật chỉ có ở background hoặc batch (tối đa 3 subagent chạy cùng lúc mỗi batch). Kết quả lấy về bằng cách poll `check_agent_task`. Ở v2.2.1 chưa có cơ chế tự đánh thức agent cha khi việc nền xong: PR #8063 "Wake parent agent session when background task finishes" còn mở (2026-09-30), issue #7056 xin callback/notification cũng còn mở.

### Khoảng trống
- Không thấy giới hạn **độ sâu lồng** trong source v2.2.1. Đã grep `depth`, `nested`, `MAX_DEPTH`, `subagent_depth` mà không có kết quả, và không thấy chỗ nào gỡ `spawn_subagent` khỏi tool set của subagent. **Nhận định:** về lý thuyết subagent có thể spawn tiếp, chỉ bị chặn bởi timeout, `max_iters` và whitelist `allowed_tools`. Chưa kiểm chứng bằng chạy thật.

## 3. File cấu hình, field liên quan, ví dụ; giới hạn (lồng, timeout, chi phí); lỗi thường gặp

### Kết luận ngắn
Cấu hình multi-agent nằm ở hai nơi: `config.json` (danh sách agent) và `workspaces/<id>/agent.json` (mọi thứ của từng agent, kể cả `subagent_model` và bật/tắt tool trong `tools.builtin_tools`). Giới hạn đã có số: `chat_with_agent` 300 giây, foreground `spawn_subagent` 600 giây, task nền 3600 giây, batch 10 task với 3 chạy đồng thời, `max_iters` mặc định 100, `check_agent_task` 30 giây. Lỗi hay gặp nhất là **timeout**. Chắc chắn: **cao** với các con số (lấy từ source), **trung bình** với phần lỗi (lấy từ issue).

### Phát hiện có nguồn
- Ví dụ `config.json` (đã chỉnh theo source, chỉ giữ field có thật trong `AgentProfileRef`):
  ```json
  {
    "agents": {
      "active_agent": "default",
      "agent_order": ["default", "coder"],
      "profiles": {
        "default": {"id": "default", "workspace_dir": "~/.qwenpaw/workspaces/default", "enabled": true},
        "coder":   {"id": "coder",   "workspace_dir": "~/.qwenpaw/workspaces/coder",   "enabled": true, "pinned": false}
      }
    }
  }
  ```
  — source `AgentProfileRef` và `AgentsConfig`, [src/config/config.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/config/config.py) (bậc 1). Ví dụ trong docs có thêm `name` và `description`, nhưng source bỏ qua chúng ở đây.
- Field quan trọng cho multi-agent trong `agent.json` (`AgentProfileConfig`):
  - `name`, `description`: dùng khi agent chọn nhau để cộng tác.
  - `active_model`, `fallback_models`, `llm_routing`: model riêng của agent.
  - `subagent_model` ("Optional cheaper model used by spawned subagents"), dạng `ModelSlotConfig` gồm `provider_id` và `model`. Có từ v2.2.0, không có ở v2.1.0 (đã kiểm bằng `git grep` theo tag).
  - `tools.builtin_tools.<tên>.enabled`: bật/tắt `chat_with_agent`, `spawn_subagent`...
  - `approval_level`: STRICT, SMART, AUTO (mặc định) hoặc OFF.
  - `running.max_iters`: mặc định 100 trong source; ví dụ trong docs ghi 50.
  - `coding_mode`, `project_dir`: ảnh hưởng tới nơi đặt worktree khi `fork=True`.
  - `acp`: cấu hình runner ngoài.

  — [src/config/config.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/config/config.py) dòng 1703–1714 và 2233–2353 (bậc 1)
- Ví dụ khối trong `agent.json` (suy ra từ schema, **chưa chạy thử**):
  ```json
  {
    "id": "coder",
    "name": "Code Reviewer",
    "description": "Specializes in Python/JS code review and refactoring",
    "active_model": {"provider_id": "dashscope", "model": "qwen3-max"},
    "subagent_model": {"provider_id": "ollama", "model": "qwen3:8b"},
    "tools": {"builtin_tools": {"spawn_subagent": {"enabled": true}, "chat_with_agent": {"enabled": true}}}
  }
  ```
  Provider ID và tên model trong ví dụ chỉ để minh họa.
- `spawn_subagent` đọc `agent_config.subagent_model` và đặt `model_slot_override` cho request của subagent. Nếu load lỗi thì bỏ qua và dùng model của cha. — `_build_subagent_request_context`, [agent_management.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/tools/agent_management.py) dòng 1111–1137 (bậc 1)
- Timeout cứng trong `ToolCoordinator`:
  - `chat_with_agent`: mặc định 300 giây.
  - `check_agent_task`: 30 giây.
  - `spawn_subagent` và `chat_with_agent` có trần nội bộ `COORDINATOR_OWNED_EXEC_TIMEOUT_SECS` (comment: "24h coordinator-owned ceiling").
  - HTTP client gọi API agent: `DEFAULT_AGENT_API_TIMEOUT = 30.0`.

  — [src/agents/react_agent.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/react_agent.py) dòng 1206–1232; agent_management.py dòng 36 (bậc 1)
- Kết quả của `chat_with_agent` mặc định được miễn tỉa tool result (`exempt_tool_names = ["chat_with_agent"]`), nên câu trả lời dài của agent khác chiếm context lâu hơn. — config.py dòng ~1137 (bậc 1)
- Chi phí: docs nói "Collaboration involves multiple agents, which may require more time and API calls". Cách giảm phí chính thức là `subagent_model` dùng model rẻ hơn. — [docs/multi-agent.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/multi-agent.en.md); config.py (bậc 1)
- Lỗi thường gặp (issues):
  - **#7678 "spawn subAgent"** (2.2.0/2.2.1, Windows): mọi subtask timeout ("Task timed out after 300s"). Maintainer giải thích subagent bị ngắt sau khoảng 10 phút, khớp `timeout=600` mặc định, và khuyên "ask the main agent to set `timeout` to `1800`". Người báo lỗi không tìm thấy setting timeout trong `config.json` (vì timeout là tham số của tool). Đóng ngày 2026-10-10, không có fix code. — [Issue #7678](https://github.com/agentscope-ai/QwenPaw/issues/7678) (bậc 3 → tin được phần trả lời của maintainer)
  - **#7981**: khi `chat_with_agent` hết 300 giây, cha nhận "The tool call has been interrupted by the user" và lượt cha kết thúc mà không có câu trả lời (Desktop 2.2.1). Workaround: truyền `timeout` lớn (1800), dùng `submit_to_agent` + `check_agent_task` cho việc dài, bảo agent được hỏi trả lời ngắn. Đã fix bằng PR #8183 (merged 2026-10-13). Đối chiếu `git diff v2.2.1 v2.2.2` cho thấy `_cooperative_cancel_response` mới được thêm, nên **fix nằm trong v2.2.2, không có trong v2.2.1**. — [Issue #7981](https://github.com/agentscope-ai/QwenPaw/issues/7981); [Issues search chat_with_agent](https://github.com/agentscope-ai/QwenPaw/issues?q=chat_with_agent) (bậc 1–3)
  - **#8252**: phiên gọi giữa các agent bị hủy âm thầm (CancelledError) mà không ghi lại ai hủy hay vì sao. Đóng 2026-10-21, đi kèm PR #8317 thêm tracing lý do hủy. — cùng trang search
  - **#7676**: tưởng `subagent_model` không có tác dụng (2.2.1-beta). Người báo tự rút lại vì đo sai: log `builder: built agent ... model=` in model của cha. Cách kiểm chứng đúng là xem usage ledger (Token Usage). `spawn_subagent` chưa có tham số `model` theo từng task (yêu cầu ở #4901, còn mở). PR #7796 "Diagnose dropped subagent model overrides" còn mở. — [Issue #7676](https://github.com/agentscope-ai/QwenPaw/issues/7676) (bậc 3)
  - **#6918** (mở): mỗi tin giữa các agent tạo một session mới. **#8078** (mở): `chat_with_agent` tạo chat riêng, làm một phiên bị tách thành nhiều trang trên UI. **Nhận định:** muốn giữ ngữ cảnh thì phải truyền `session_id` rõ ràng. — [Issues search](https://github.com/agentscope-ai/QwenPaw/issues?q=chat_with_agent) (bậc 3)
  - **#7210** (mở, v2.1.0 Docker): tool bật trong `agent.json` nhưng không có trong schema gửi model. Maintainer không tái hiện được. — [Issue #7210](https://github.com/agentscope-ai/QwenPaw/issues/7210) (bậc 3)
  - Feature request còn mở: cô lập giữa các sub-agent (#6509), cô lập agent hoàn toàn (#6461), giao tiếp agent giữa các instance hoặc máy khác nhau (#8080). — [Issues search](https://github.com/agentscope-ai/QwenPaw/issues?q=chat_with_agent)

### Nhận định
- Timeout là tham số mà *model* truyền vào tool, không phải cấu hình toàn cục. Muốn việc dài chạy ổn thì ghi vào AGENTS.md của agent một quy tắc kiểu "khi gọi spawn_subagent hay chat_with_agent cho việc dài, đặt timeout=1800 hoặc dùng background".
- Ai dùng `chat_with_agent` nhiều nên lên v2.2.2 để có fix #8183.

### Khoảng trống
- Không có field cấu hình toàn cục nào giới hạn số subagent hay độ sâu. Không có ước tính chi phí định lượng.
- Không rõ `COORDINATOR_OWNED_EXEC_TIMEOUT_SECS` có đúng 86400 không, vì chỉ đọc comment "24h".

## 4. Thay đổi multi-agent từ v2.x đến v2.2.1

### Kết luận ngắn
v2.2.1 có thật, tag ngày 2026-09-11. v2.2.0 ra ngày 2026-09-03. Các thay đổi multi-agent đáng kể trong v2.x: v2.0.0 đưa vào Mission/Goal Mode và quản lý MCP/A2A/ACP thống nhất; v2.0.1 và v2.1.0 sửa approval và batch cho subagent; v2.2.0 thêm nhóm hội thoại subagent và `subagent_model`; v2.2.1 thêm model routing theo từng agent. **Hub của v2.2.0 là multi-*user*, không phải multi-agent.** Chắc chắn: **cao**.

### Phát hiện có nguồn
- Ngày tag theo git: v2.0.0 là 2026-07-10, v2.1.0 là 2026-08-13, v2.2.0 là 2026-09-03, v2.2.1 là 2026-09-11, v2.2.2 là 2026-10-15. — `git log` trên các tag của [agentscope-ai/QwenPaw](https://github.com/agentscope-ai/QwenPaw) (bậc 1)
- **v2.0.0** (2026-07-10):
  - "Unified management of MCP/A2A/ACP connections, encrypted credential storage, and per-call approval policy" (#5067).
  - "three Loop templates: Normal Mode / Mission Mode / Goal Mode" (#5665, #5727).
  - Node.js runtime và các module ACP đóng gói sẵn trong bản desktop (#5814, #5794).

  — [Releases](https://github.com/agentscope-ai/QwenPaw/releases?q=subagent&expanded=true) (bậc 1)
- **v2.0.1-beta**:
  - "fix(subagent): route and resolve approvals from the root session" (#6295).
  - "feat(omp): integrate OMP workflow modes and extend spawn_subagent" (#5882).
  - "fix(tools): coerce LLM-stringified spawn_subagent batch/list args" (#6395).

  — cùng nguồn
- **v2.1.0-beta.1**: "fix(agents): inherit session approval_level in spawn_subagent" (#6508). Các hằng số batch `MAX_SPAWN_BATCH_SIZE` có từ v2.1.0, không có ở v2.0.0 (kiểm bằng `git grep` theo tag). — cùng nguồn; source (bậc 1)
- **v2.2.0** (2026-09-03):
  - "Organize subagent conversations into groups and surface completion and unread status" (#7035, #7275).
  - Token Usage chia theo từng Agent (#7207, #7219).
  - Console stop được truyền xuống tool đang chạy của Agent (#7349).
  - Ghi cấu hình Agent nhất quán khi ghi đồng thời (#6767).
  - Task nền có timeout mặc định mà không ghi đè giá trị truyền tay (#6869).
  - Project directory gắn theo session (#6976).
  - Field `subagent_model` xuất hiện từ tag này (source).

  — [Release v2.2.0](https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.2.0) (bậc 1)
- **Hub v2.2.0**: "lets a team use QwenPaw on a shared server ... each person gets their own QwenPaw with separate workspaces". Cài bằng `pip install -U "qwenpaw[hub]"`, lệnh `qwenpaw hub`, không có trong bản desktop. Docs ghi: "Hub 2.2.0 is an early release intended only for internal teams whose members trust one another". — [docs/hub.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/hub.en.md); [Release v2.2.0](https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.2.0) ("Self-host a multi-user QwenPaw Hub with local-process or Docker runtimes", #7112) (bậc 1)
- **v2.2.1** (2026-09-11): release notes không có mục subagent hay chat_with_agent. Mục liên quan agent:
  - Model routing riêng cho từng Agent (#7501).
  - Tăng cường hành vi agent builtin (#7526).
  - Trang env thống nhất (#7538).
  - Agent Kanban có i18n (#7482).
  - Agent selector trên màn hình nhỏ (#7623).
  - Áp allowlist tool của MCP trên đường runtime của Agent (#7504).
  - ACP Agent không còn treo khi khởi động workspace trên Windows (#7401).

  — [Release v2.2.1](https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.2.1) (bậc 1)
- **Sau v2.2.1**:
  - v2.2.2 (2026-10-15) sửa cách báo cancel/timeout của `chat_with_agent` và `spawn_subagent` (#8183). `agent_management.py` thay đổi +84/−21 dòng giữa hai tag.
  - Trên main có PR mở #8063 (đánh thức agent cha khi task nền xong) và Advisor Mode (#7569, merged 2026-10-19).

  — `git diff v2.2.1 v2.2.2`; [Issues search subagent](https://github.com/agentscope-ai/QwenPaw/issues?q=subagent) (bậc 1–3)

### Nhận định
- Từ v2.0 đến v2.2.1 không có thay đổi lớn về khái niệm multi-agent. Phần lớn là hoàn thiện `spawn_subagent` (approval, batch, nhóm hiển thị, model rẻ) và thêm Mission Mode. Ai cần một "đội agent" thật trên nhiều máy vẫn phải dùng giải pháp ngoài (AgentTeams/HiClaw) hoặc chờ #8080.

### Khoảng trống
- Release notes trên trang GitHub bị cắt với v2.0.0 và v1.1.10, nên có thể còn mục liên quan chưa thấy.
- Chưa xác định chính xác PR nào thêm `subagent_model`. Chỉ biết nó có ở tag v2.2.0 mà không có ở v2.1.0.

## Truy vấn đã chạy
- git clone agentscope-ai/QwenPaw, checkout tag v2.2.1, grep `chat_with_agent|subagent|multi.agent|delegate` (source)
- grep `subagent_model|depth|nested|MAX_DEPTH|enabled_by_default` trong `src/` (source)
- `git grep` theo các tag v2.0.0/v2.1.0/v2.2.0 cho subagent_model, MAX_SPAWN_BATCH_SIZE (source)
- `git diff v2.2.1 v2.2.2 -- agent_management.py` (source)
- WebFetch: releases/tag/v2.2.1, releases/tag/v2.2.0, releases?q=subagent (standard)
- WebFetch: issues?q=subagent, issues?q=chat_with_agent; issues #7676, #7981, #7678, #7210 (standard)
- gh api releases: bị chặn (403, repo chưa bật cho session), nên chuyển sang WebFetch
