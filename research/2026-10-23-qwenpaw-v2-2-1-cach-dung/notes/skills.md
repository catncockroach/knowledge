# Hệ thống skills của QwenPaw v2.2.1

Ghi chú chung về nguồn: phần lớn phát hiện lấy từ mã nguồn và docs **tại tag `v2.2.1`** của repo `agentscope-ai/QwenPaw` (commit của tag ngày 2026-09-11; trang GitHub Release ghi "released 11 Sep"). Repo còn có tag mới hơn là **v2.2.2** (commit 2026-10-15) và các bản `v2.2.2-beta.*`, nên v2.2.1 **không còn là bản mới nhất** tính đến 2026-10-23. File docs `website/public/docs/skills.en.md` ở `main` (2026-10-22) giống hệt bản ở v2.2.1 (đã chạy diff, không có khác biệt).

Viết tắt URL gốc: `T = https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1`

## 1. Định dạng skill, thư mục, bật/tắt, nạp vào prompt

### Kết luận ngắn
Skill là một thư mục chứa `SKILL.md` có YAML frontmatter, bắt buộc `name` và `description`, tùy chọn `metadata` (version, requires.bins/env/mcp, qwenpaw.emoji). Skill nằm theo hai lớp: **skill pool** dùng chung (`~/.qwenpaw/skill_pool/`) và **bản chạy riêng của từng workspace/agent** (`~/.qwenpaw/workspaces/{agent_id}/skills/`), trạng thái lưu trong `skill.json`. Bật/tắt qua Console hoặc `qwenpaw skills enable/disable`. Mặc định skill nạp theo kiểu on-demand: prompt chỉ liệt kê tên, mô tả và thư mục, agent gọi tool `Skill` để đọc nội dung. Từ v2.2.1 có thể đặt `preload` để nhét toàn bộ nội dung vào system prompt. Mức chắc chắn: **cao**, vì đã đối chiếu docs với code tại tag v2.2.1.

### Phát hiện có nguồn
- **Hai lớp lưu trữ.** Skill Pool là kho cục bộ dùng chung tại `$QWENPAW_WORKING_DIR/skill_pool/`. Workspace Skills là "local runtime copy" tại `$QWENPAW_WORKING_DIR/workspaces/{agent_id}/skills/`. `QWENPAW_WORKING_DIR` mặc định là `~/.qwenpaw`. Cả pool lẫn workspace đều có manifest `skill.json`. Pool entries "are **not executed directly** by a workspace. To use one, you must broadcast it to a workspace first." — [skills.en.md @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md) (bậc 1, 2026-09)
- **Thao tác phía pool:** Broadcast (chép sang một hoặc nhiều workspace), Add Skill (Create, Upload via Zip, Upload via URL, Browse Market), edit/rename, conflict handling (trùng tên thì trả lỗi kèm gợi ý tên mới, không ghi đè), Auto Sync, Auto Update. Nếu sửa `SKILL.md` của một built-in, entry đó chuyển thành custom skill và các bản cập nhật đóng gói sau này sẽ không ghi đè nữa. — [skills.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md) (bậc 1, 2026-09)
- **External skill paths.** Field top-level `skill_paths` trong `~/.qwenpaw/config.json`, ví dụ `{"skill_paths": ["~/my-skills", "/opt/team/shared-skills"]}`. Skill trong các thư mục này được đọc tại chỗ, không chép vào pool. Thứ tự quét là pool chính trước, rồi đến từng path theo thứ tự; trùng tên thì "earlier one wins". Xóa một skill external sẽ **xóa file thật** trong thư mục đó. Upload/import luôn ghi vào pool chính. Path không tồn tại bị bỏ qua mà không báo lỗi. — [skills.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md) (bậc 1); field `skill_paths: List[str]` có trong [config/config.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/config/config.py) (bậc 1). Release note v1.1.11 có mục "Multi-Path Skill Pool (#4891)" — [v1.1.11.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v1.1.11.md) (bậc 1)
- **Frontmatter.** `name` và `description` **bắt buộc**, `metadata` tùy chọn. Ví dụ chính thức:
  ```yaml
  ---
  name: my_skill
  description: My custom capability
  metadata:
    version: "1.0"
    requires:
      bins: [ffmpeg]
      env: [MY_SKILL_API_KEY]
      mcp: [my-mcp-server]
  ---
  ```
  Version được đọc theo thứ tự `version` → `metadata.version` → `metadata.builtin_skill_version` (khớp với hàm `extract_version` trong [store.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/skill_system/store.py)). Version không bị ép theo SemVer. Khối `requires` được tìm theo thứ tự `metadata.openclaw.requires` → `metadata.qwenpaw.requires` → `metadata.clawdbot.requires` → `metadata.requires` → `requires`, khối tìm thấy đầu tiên được dùng. Emoji lấy từ `metadata.qwenpaw.emoji`. — [skills.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md), [store.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/skill_system/store.py) (bậc 1, 2026-09)
- **Kiểm tra dependency (mới ở v2.2.1, PR #7609).** Một skill đang bật mà khai báo sai hoặc thiếu bin/env/MCP sẽ bị **bỏ qua** khi nạp, kèm log ERROR, và cũng không hiện trong `/skills`, preload hay lời gọi trực tiếp. Agent vẫn chạy bình thường. Sửa xong thì skill tự có lại ở lần nạp sau. Kiểm tra MCP chỉ xác nhận cấu hình MCP hợp lệ và đang bật, không kiểm tra kết nối. Kiểm tra thủ công bằng `qwenpaw skills test my_skill --agent-id default`, lệnh trả exit code khác 0 khi thiếu, ví dụ `Environment variable not set: MY_SKILL_API_KEY`. — [skills.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md); [release notes v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v2.2.1.md) (bậc 1)
- **Entry trong `skill.json` của workspace** có các field `enabled`, `channels` (mặc định `["all"]`), `preload` (chỉ `true` mới bật), `source`, `installed_from`, `config`. Manifest workspace có `schema_version: "workspace-skill-manifest.v1"`. — [workspace_service.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/skill_system/workspace_service.py), [store.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/skill_system/store.py) (bậc 1)
- **Bật/tắt:**
  - Console: **Workspace → Skills**. Skill thêm qua "Add Skill" được bật sẵn. Skill đặt tay vào thư mục sẽ được ghi vào `skill.json` ở trạng thái **disabled** trong lần reconcile kế tiếp.
  - CLI: `qwenpaw skills enable pdf docx --agent-id abc123`, `qwenpaw skills disable pdf --agent-id abc123`, `qwenpaw skills list --status enabled|disabled|all [--agent-id ID | --pool]`, `qwenpaw skills info NAME [--pool]`, `qwenpaw skills config [--agent-id]` (cấu hình tương tác), `qwenpaw skills test SKILL|./dir`. Nếu không có `--agent-id` thì mặc định là agent `default`.
  - Pool không có trạng thái enabled, nên `config`, `enable` và `disable` chỉ áp dụng cho workspace.
  — [skills.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md), [cli.en.md §Skills](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/cli.en.md) (bậc 1)
- **Lệnh trong chat:** `/skills` liệt kê skill dùng được ở channel hiện tại. `/<skill_name>` xem chi tiết skill. `/<skill_name> <input>` ép agent dùng skill đó. Các lệnh này chỉ chạy với skill đang bật và được route tới channel đó. — [commands.en.md §Skill Chat Commands](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/commands.en.md) (bậc 1)
- **Channel routing:** mỗi skill có `channels`, mặc định `["all"]`. Khi chạy trên một channel, chỉ skill có channel đó (hoặc `all`) được nạp, ví dụ chỉ bật skill onboarding DingTalk cho channel DingTalk. — [skills.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md) (bậc 1)
- **Skill config → biến môi trường:** object `config` trong entry `skill.json` được inject vào env trong suốt một lượt (turn) của agent, rồi được khôi phục sau đó. Chỉ những key có trong `metadata.requires.env` thành env var riêng. Toàn bộ JSON luôn có trong `QWENPAW_SKILL_CONFIG_<SKILL_NAME>`. Biến env sẵn có của máy **không bao giờ bị ghi đè**. Thứ tự ưu tiên: host env > workspace config > pool config (pool config chỉ là giá trị khởi tạo khi tải skill về workspace). — [skills.en.md §Skill config](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md) (bậc 1)
- **Cách nạp vào prompt, mặc định là on-demand.** QwenPaw đưa skill vào `Toolkit(tools=..., skills_or_loaders=...)` của AgentScope. Từ đó AgentScope 2.0 chèn khối `<agent-skills>` vào prompt, chỉ gồm `<name>`, `<description>`, `<dir>` của từng skill, kèm câu: "Skills are NOT tools, and you cannot call a skill directly. To use a skill, you MUST use the `{{ skill_viewer }}` tool to read the skill's full instructions". Tool viewer tên `Skill`, nhận input `{"skill": "<name>"}` và là tool read-only. QwenPaw v2.2.1 ghim `agentscope[model-ollama]==2.0.7.post1`. — [runtime/builder.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/runtime/builder.py), [pyproject.toml](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/pyproject.toml) (bậc 1); `agentscope/tool/_toolkit.py` (`DEFAULT_SKILL_INSTRUCTION`) và `agentscope/tool/_builtin/_skill.py` (`SkillViewer`) trong wheel agentscope 2.0.7.post1 trên PyPI — [PyPI agentscope 2.0.7.post1](https://pypi.org/project/agentscope/2.0.7.post1/) (bậc 1, đã đọc mã trong wheel)
- **Preload (mới ở v2.2.1, PR #7183).** Bật trong **Workspace → Skills → Edit**, tương ứng `preload: true` trong `skill.json`. Skill được preload bị tách khỏi danh sách của viewer. `PreloadedSkillsContributor` (priority 95) chèn khối `<preloaded-skills>` chứa toàn bộ `skill.markdown` của từng skill vào system prompt, với chỉ dẫn "do not load them again with the Skill Viewer". Docs khuyên chỉ preload những skill "trusted core or frequently used". — [runtime/prompt_contributors.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/runtime/prompt_contributors.py), [agents/skill_system/registry.py `select_preload_skills`](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/skill_system/registry.py), [skills.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md) (bậc 1)
- **Auto Update / Auto Sync:** luồng là `packaged built-in --Auto Update--> Skill Pool --Auto Sync--> workspaces`. Cấu hình nằm trong object `automation` của từng skill trong `skill.json` của pool, ví dụ `{"automation":{"auto_update":{"enabled":true},"auto_sync":{"enabled":true,"targets":["default"]}}}`. Nếu không có `targets`, skill chỉ sync tới các workspace đã có nó. Việc kiểm tra chạy khi lưu, khi khởi động và khi refresh pool. — [skills.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md) (bậc 1)
- **Nâng cấp từ bản cũ:** các thư mục `active_skills/` và `customized_skills/` cũ được **chép** (không di chuyển) sang `skills/` của workspace ở lần khởi động đầu. `active_skills/` được chép sang trạng thái enabled. `customized_skills/` sang trạng thái disabled, trừ khi skill đó cũng có trong active với nội dung giống hệt. Trùng tên mà khác nội dung thì giữ cả hai, với hậu tố `-active` / `-customize`. Sau khi migrate, hai thư mục cũ **không còn được đọc**. — [skills.en.md §Upgrading](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md) (bậc 1). Kiến trúc hai lớp pool/workspace có từ v1.0.0, lúc dự án còn tên CoPaw ("Skill Pool Architecture" #2173…) — [v1.0.0.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v1.0.0.md) (bậc 1)

### Nhận định
- Cơ chế này về bản chất là progressive disclosure giống Anthropic Agent Skills: metadata nằm trong prompt, nội dung đọc khi cần qua tool `Skill`. Khác biệt là QwenPaw thêm một lớp quản lý (pool, workspace, manifest `skill.json`, channels, config, preload).
- Khi dùng hằng ngày, nên viết skill trong thư mục riêng (git repo), khai báo vào `skill_paths`, rồi broadcast sang các agent cần dùng. Cách này tránh mất bản sửa khi pool bị ghi đè. Cần lưu ý xóa từ UI sẽ xóa file thật trong thư mục đó.

### Khoảng trống
- Chưa xác minh quy tắc ký tự hợp lệ cho `name`. Release note v2.2.2 có mục "Validate Skill names before using them as installation paths" (#8065), cho thấy v2.2.1 chưa kiểm tra chặt.
- Chưa xác minh URL docs site hiện hành (pyproject ghi `https://qwenpaw.agentscope.io/docs/`, nên trang skills nhiều khả năng là `/docs/skills`), vì chưa fetch trang này.

## 2. Cài skill từ hub/marketplace, import URL/GitHub, skill builtin

### Kết luận ngắn
Có **Skill Market** nhúng trong Console, tìm kiếm song song trên 4 provider (QwenPaw, ClawHub, ModelScope, Aliyun). Ngoài ra có thể import theo URL từ skills.sh, clawhub.ai, skillsmp.com, lobehub.com, market.lobehub.com, github.com, modelscope.cn/skills, qua Console hoặc `qwenpaw skills install <url> --pool|--agent-id`. Có 16 skill builtin thực tế trong package (mỗi skill có bản `-en` và `-zh`). Bảng builtin trong docs lệch với code: docs có `news` mà code không có, và thiếu `chat_with_agent`, `make-skill`, `make_plan`. Mức chắc chắn: **cao**.

### Phát hiện có nguồn
- **Import URL, các nguồn được hỗ trợ:** `https://skills.sh/...`, `https://clawhub.ai/...`, `https://skillsmp.com/...`, `https://lobehub.com/...`, `https://market.lobehub.com/...`, `https://github.com/...` (trang chứa `SKILL.md`, ví dụ skill-creator trong repo anthropics/skills), `https://modelscope.cn/skills/...`. Skill import xong được **bật sẵn**. Trùng tên thì không ghi đè. Nếu bị GitHub rate-limit thì thêm `GITHUB_TOKEN` trong Console → Settings → Environments. — [skills.en.md §Import from URL](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md) (bậc 1)
- **CLI:** `qwenpaw skills install <url> --pool` hoặc `--agent-id <id>`. Hai cờ này loại trừ nhau. Nếu bỏ cả hai thì đích vẫn là Pool (giữ để tương thích). Có thêm `--enable/--no-enable`, chỉ dùng cho workspace. Gỡ bằng `qwenpaw skills uninstall <name> --pool|--agent-id`. — [cli.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/cli.en.md) (bậc 1)
- **Skill Market:** mở từ Add Skill → Browse Market trong Workspace → Skills hoặc Settings → Skill Pool. Có 4 provider: **QwenPaw**, **ClawHub**, **ModelScope** (công khai, luôn bật) và **Aliyun** (cần `ALIBABA_CLOUD_ACCESS_KEY_ID` / `ALIBABA_CLOUD_ACCESS_KEY_SECRET`). Có thể lọc theo provider, category và từ khóa. Một provider lỗi không chặn các provider khác. Nút Save cài vào nơi người dùng đi vào (workspace hoặc pool). Các lượt cài chạy theo hàng đợi, có retry. Field `installed_from` ghi nguồn gốc: `clawhub`, `modelscope`, `aliyun`, `skills-sh`, `lobehub`, `skillsmp`, `github`, `url`, `zip`. — [skills.en.md §Skill Market](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md) (bậc 1)
- v2.2.1 sửa lỗi "Restore Skill discovery through the current ClawHub endpoint" (#7640). — [Release v2.2.1](https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.2.1) (bậc 1, 2026-09-11)
- **Lưu ý tên gọi:** "QwenPaw Hub" (`qwenpaw hub`, có từ 2.2.0) là **server nhiều người dùng**, không phải hub skill. — [hub.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/hub.en.md) (bậc 1)
- **Builtin thực tế trong package v2.2.1** (thư mục `src/qwenpaw/agents/skills/`, mỗi skill có bản `-en` và `-zh`): `QA_source_index`, `browser`, `channel_message`, `chat_with_agent`, `cron`, `dingtalk_channel`, `docx`, `file_reader`, `guidance`, `mailbox`, `make-skill`, `make_plan`, `multi_agent_collaboration`, `pdf`, `pptx`, `xlsx`. Bản ngôn ngữ chọn theo ngôn ngữ UI (`BUILTIN_SKILL_LANGUAGES = ("en","zh")`). Từ v1.1.3 có thể chuyển ngôn ngữ trên trang Skill Pool. — [tree src/qwenpaw/agents/skills @v2.2.1](https://github.com/agentscope-ai/QwenPaw/tree/v2.2.1/src/qwenpaw/agents/skills), [registry.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/skill_system/registry.py), [v1.1.3.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v1.1.3.md) (bậc 1). Tổng cộng 16 skill. Bảng trong docs có 14 dòng, trong đó có **`news`**, mà thư mục `news` không có trong package v2.2.1. Docs cũng ghi `docx`/`pdf`/`pptx`/`xlsx` lấy nguồn từ `github.com/anthropics/skills`. — [skills.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md) (bậc 1). Docs và code mâu thuẫn nhau ở điểm này.
- **Version một số builtin** (đọc từ frontmatter): `cron` 1.7, `make-skill` 2.0, `pdf` 1.1, `multi_agent_collaboration` 1.4 (mô tả: "First list agents, then use qwenpaw agents chat for two-way communication"). — [cron-en/SKILL.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/skills/cron-en/SKILL.md), [make-skill-en/SKILL.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/skills/make-skill-en/SKILL.md), [multi_agent_collaboration-en/SKILL.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/skills/multi_agent_collaboration-en/SKILL.md) (bậc 1)

### Nhận định
- Sau lần cập nhật đầu, nên đối chiếu `qwenpaw skills list --pool` với docs, vì bảng builtin trong docs đã cũ.

### Khoảng trống
- Chưa kiểm tra chi tiết code `skill_system/hub.py` (định dạng URL cụ thể của từng provider, xử lý zip nhiều skill).
- Chưa rõ `news` bị gỡ khỏi package từ bản nào.

## 3. Ví dụ skill tự viết; tương thích Anthropic / OpenClaw; bảo mật

### Kết luận ngắn
Một skill tự viết chỉ cần thư mục với `SKILL.md` theo chuẩn Anthropic (`name`, `description`). Có thể thêm `scripts/` và `references/`, vì builtin `pdf`/`make-skill` cũng có cấu trúc này. QwenPaw **đọc được** metadata kiểu OpenClaw (`metadata.openclaw.requires`, `metadata.clawdbot.requires`), cài được từ ClawHub, và đóng gói lại 4 skill của Anthropic. Về bảo mật, có **Skill Scanner** dựa trên regex YAML với 3 chế độ, mặc định là `warn` (chỉ cảnh báo, không chặn). Mức chắc chắn: **cao** cho phần cơ chế, **trung bình** cho mức "tương thích", vì chưa thử chạy thật một skill OpenClaw hay Anthropic.

### Phát hiện có nguồn
- **Ví dụ skill có config/env, dạng chính thức:**
  ```markdown
  ---
  name: my_skill
  description: demo
  metadata:
    requires:
      env: [MY_API_KEY, BASE_URL]
  ---
  ```
  Config trong Console: `{"MY_API_KEY":"sk-demo","BASE_URL":"https://api.example.com","timeout":30}`. Script đọc giá trị bằng `os.environ.get("MY_API_KEY")`, còn `timeout` lấy qua `json.loads(os.environ["QWENPAW_SKILL_CONFIG_MY_SKILL"])`. Danh sách YAML khai báo **tên**, không khai báo giá trị (`env: MY_KEY` dạng chuỗi là sai). — [skills.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md) (bậc 1)
- **Ba cách tạo skill:**
  1. Console → Create Skill (có nút "AI Optimize", đang beta).
  2. Viết file tay vào `workspaces/{agent_id}/skills/<name>/SKILL.md`, rồi bật lên vì skill đặt tay mặc định ở trạng thái disabled.
  3. Chạy `/make-skill <focus>` trong chat (ví dụ `/make-skill weekly sales report workflow`). Agent đề xuất kế hoạch gồm tên, mục đích, các bước, file, tùy chọn **Batch** và một trong ba mức test (No test / Smoke test / Eval). Sau khi người dùng duyệt, skill được lưu vào workspace ở trạng thái bật sẵn. `make-skill` cũng là một builtin và phải đang bật thì mới gọi được.
  — [skills.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md) (bậc 1). v2.2.1 nâng cấp Make Skill với "guided drafting, validation, behavior tests, and publishing tools" (#7509) — [release notes v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v2.2.1.md) (bậc 1)
- **Tương thích:**
  - Parser `requires` ưu tiên `metadata.openclaw.requires`, sau đó mới tới `metadata.qwenpaw.requires`, `metadata.clawdbot.requires`, `metadata.requires`, `requires`.
  - 4 builtin `docx`/`pdf`/`pptx`/`xlsx` ghi nguồn từ `github.com/anthropics/skills`. Frontmatter của `pdf` giữ nguyên field `license: Proprietary. LICENSE.txt has complete terms` của Anthropic.
  — [skills.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/skills.en.md), [pdf-en/SKILL.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/skills/pdf-en/SKILL.md) (bậc 1)
  - Grep mã nguồn v2.2.1 **không tìm thấy** xử lý các field frontmatter riêng của Claude Code như `allowed-tools`, `disable-model-invocation`, `user-invocable`. Chuỗi "allowed_tools" chỉ xuất hiện ở whitelist tool của subagent (`subagent_allowed_tools`). Nhiều khả năng các field này bị bỏ qua. — [runtime/builder.py](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/runtime/builder.py) (bậc 1, suy từ việc grep không có kết quả)
- **Skill Scanner:**
  - Chạy trước khi kích hoạt skill: khi tạo mới, khi bật một skill đang tắt, khi import từ Skill Hub.
  - Dùng chữ ký regex YAML (PatternAnalyzer). Kết quả cache theo mtime. Timeout mặc định 30 giây (cho phép 5–300). Bỏ qua symlink, kiểm tra đường dẫn thật không ra ngoài thư mục skill, bỏ qua file nhị phân và file nén.
  - Chế độ: `block` / `warn` (**mặc định**) / `off`. Thứ tự ưu tiên cấu hình: env `QWENPAW_SKILL_SCAN_MODE` > Console > `config.json` (`security.skill_scanner.{mode,timeout,whitelist}`).
  - Whitelist khóa theo SHA-256 của toàn bộ file trong skill: file đổi thì hash đổi và skill bị quét lại. Gỡ khỏi whitelist thì skill tự bị tắt.
  - Console: Settings → Security → Skill Scanner, có hai tab Scan Alerts và Whitelist.
  — [security.en.md §Skill Scanner](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/security.en.md); default `mode="warn"`, `timeout=30` trong [config/config.py `SkillScannerConfig`](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/config/config.py) (bậc 1)
- **Các file chữ ký trong code v2.2.1:** `command_injection`, `data_exfiltration`, `hardcoded_secrets`, `obfuscation`, `prompt_injection`, `social_engineering`, `supply_chain`, `unauthorized_tool_use` (8 file). Docs liệt kê thêm `resource_abuse`, nhưng không có file tương ứng. Có thể tự viết policy riêng: `ScanPolicy.from_yaml(...)` truyền vào `SkillScanner(policy=...)`. — [rules/signatures @v2.2.1](https://github.com/agentscope-ai/QwenPaw/tree/v2.2.1/src/qwenpaw/security/skill_scanner/rules/signatures), [security.en.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/security.en.md) (bậc 1). Scanner có từ thời CoPaw; v1.0.0 bổ sung regex tiếng Trung cho prompt injection (#2381) — [v1.0.0.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v1.0.0.md) (bậc 1)

### Nhận định
- Vì mặc định là `warn`, skill độc hại từ market vẫn được bật, chỉ kèm cảnh báo. Khi dùng cá nhân mà cài skill bên thứ ba, nên đặt `QWENPAW_SKILL_SCAN_MODE=block` và whitelist các skill tự viết. Scanner chỉ dựa trên regex nên chỉ là lớp phòng thủ nông. Còn có các lớp khác (Tool Guard, Access Policy) do góc nghiên cứu "bảo mật" đảm nhận.
- Skill viết theo chuẩn Anthropic (chỉ `name` + `description` + markdown) gần như chắc chắn chạy được, vì QwenPaw tự đóng gói skill của Anthropic. Skill OpenClaw dùng `metadata.openclaw.requires` cũng được đọc phần dependency.

### Khoảng trống
- Chưa tìm thấy issue hay bài cộng đồng về lỗi tương thích skill. Truy vấn web không ra kết quả, và không truy cập được GitHub API (403 trong phiên này) để tìm issue.
- Chưa thử chạy thật một skill OpenClaw hay Anthropic trên v2.2.1.

## 4. Thay đổi về skills trong v2.x đến v2.2.1 (và v2.2.2)

### Kết luận ngắn
Trong v2.x, skills thay đổi chủ yếu ở trải nghiệm market và quản lý (v2.0–2.2.0). Riêng v2.2.1 thêm **preload**, **Make Skill nâng cấp**, **hiển thị version và kiểm tra dependency**, và sửa ClawHub. v2.2.2 (ra sau, 2026-10) thêm broadcast hàng loạt, gán skill cho custom channel, nguồn market dạng plugin, Make Skill 2.1. Mức chắc chắn: **cao**, vì lấy từ release notes chính thức trong repo.

### Phát hiện có nguồn
- **v2.0.0:** Skill market có star/download count, tách enabled/disabled, auto-sync từ CDN (#5521, #5706, #5639). Thêm hook `on_uninstall` và public skill-provider API cho plugin (#5008). Khôi phục việc inject skill vào system prompt (#5396, #5680). — [v2.0.0.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v2.0.0.md) (bậc 1)
- **v2.0.1:** Danh sách skill tự refresh sau khi cài từ market (#6296). Sửa lỗi cuộn trang (#5968). Sửa rò rỉ bộ nhớ liên quan skill-hub (#6208). — [v2.0.1.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v2.0.1.md) (bậc 1)
- **v2.1.0:** External Skills trong settings center (#6870). Agent chạy bằng Codex/Qoder có Skills/MCP riêng cho từng session (#6397). Slash-command hiển thị nội dung được inject, bỏ qua bản trùng, import trực tiếp link QwenPaw Skill (#6345, #6650, #6517). — [v2.1.0.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v2.1.0.md) (bậc 1)
- **v2.2.0:** Tìm kiếm và bật/tắt skill hàng loạt (#7140, #6990). Nạp file nhanh hơn và tự động cập nhật builtin (Auto Update) (#7097, #7232). Gộp apps, plugins và Skills vào một marketplace (#6880, #7017, #7235). — [v2.2.0.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v2.2.0.md) (bậc 1)
- **v2.2.1 (2026-09-11):** Preload skill (#7183). Make Skill nâng cấp (#7509). Hiển thị version và kiểm tra dependency khai báo trước khi dùng (#7609). Khôi phục discovery qua endpoint ClawHub hiện hành (#7640). — [Release v2.2.1](https://github.com/agentscope-ai/QwenPaw/releases/tag/v2.2.1), [v2.2.1.md](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/release-notes/v2.2.1.md) (bậc 1)
- **v2.2.2 (commit tag 2026-10-15, sau v2.2.1):**
  - PawPort import Skills (và nhiều thứ khác) từ Codex/Qoder (#6960).
  - Phân phối skill hàng loạt từ pool sang workspace (#7852).
  - Gán skill cho custom channel (#7782).
  - Cài/gỡ các nguồn Skill Market (QwenPaw, ClawHub, ModelScope, Aliyun) dưới dạng plugin (#8128).
  - Make Skill 2.1 (#7753).
  - Kiểm tra tên skill trước khi dùng làm đường dẫn cài đặt (#8065).
  - Chuyển việc tải skill từ pool ra khỏi request path (#8055).
  — [v2.2.2.md](https://github.com/agentscope-ai/QwenPaw/blob/main/website/public/release-notes/v2.2.2.md) (bậc 1)

### Nhận định
- Bản sửa #8065 ở v2.2.2 gợi ý v2.2.1 có thể có lỗ hổng path khi đặt tên skill. Nếu thường cài skill bên thứ ba, đây là một lý do để cân nhắc lên v2.2.2.

### Khoảng trống
- Không lấy được ngày publish chính xác của GitHub Release v2.2.2 qua API (403). Ngày ghi ở trên là ngày commit của tag.

## Truy vấn đã chạy
- git clone github.com/agentscope-ai/QwenPaw, checkout tag v2.2.1, đọc docs `skills`, `security`, `cli`, `commands`, `hub`, release notes v1.0.0–v2.2.2, và code `agents/skill_system`, `runtime/builder.py`, `runtime/prompt_contributors.py`, `config/config.py`, `security/skill_scanner` (standard)
- pip download agentscope==2.0.7.post1, đọc `tool/_toolkit.py`, `tool/_builtin/_skill.py` (standard)
- WebSearch "QwenPaw skills issue github SKILL.md" (standard): không ra issue liên quan
- WebFetch github.com/agentscope-ai/QwenPaw/releases/tag/v2.2.1 (standard)
- gh api releases: bị chặn 403 trong phiên này
