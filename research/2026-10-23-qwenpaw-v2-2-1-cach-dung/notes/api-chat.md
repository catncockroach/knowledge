# Gọi API chat vào QwenPaw local để lấy output (bổ sung 2026-10-26)

Câu hỏi: QwenPaw chạy local thì gọi API chat thế nào để lấy output, docs có mô tả theo chuẩn nào không (OpenAI-compatible hay chuẩn riêng)?

Nguồn chính: repo `agentscope-ai/QwenPaw`, clone ngày 2026-10-26 (nhánh main, commit `95aa68f`) và tag `v2.2.1`. File docs `website/public/docs/api-tutorial.en.md` ở tag v2.2.1 **giống hệt** bản main (đã `diff`).

## 1. Docs có, và chuẩn là của AgentScope Runtime, không phải OpenAI

### Kết luận ngắn
Có docs chính thức riêng: trang **RESTful API** (`api-tutorial.en.md` / `.zh.md`). Endpoint chính là `POST /api/console/chat`, trả **SSE**. Docs ghi rõ API "is based on an extension of the AgentScope Runtime protocol" và trỏ sang https://runtime.agentscope.io/en/protocol.html. Định dạng request chỉ "similar to OpenAI's message format", không phải OpenAI-compatible. Mức chắc chắn: **cao** (docs + source cùng tag).

### Phát hiện có nguồn
- Docs: "QwenPaw's API is based on an extension of the AgentScope Runtime protocol"; endpoint `POST /api/console/chat`, mọi API nằm dưới prefix `/api`; header `X-Agent-Id` chọn agent (mặc định `default`) — [api-tutorial.en.md @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/api-tutorial.en.md) (bậc 1)
- Body: `input` (mảng message, mỗi message có `role` và `content` là mảng `{type:"text", text}`), `session_id`, `user_id`, `channel` (khuyên `"console"`) — cùng nguồn.
- Response: SSE, mỗi dòng `data: {json}`; field `sequence_number`, `object` ("response"), `status` (`created`/`in_progress`/`completed`/`failed`), `output`, `error`, `session_id`, `usage` — cùng nguồn.
- Đa lượt: **không** gửi lại lịch sử trong `input`; giữ cùng `session_id` (và `user_id`) thì server tự nạp lịch sử — cùng nguồn.
- Request từ `127.0.0.1`/`::1` tự bỏ qua auth kể cả khi bật `QWENPAW_AUTH_ENABLED`; gọi từ máy khác cần `Authorization: Bearer <token>` lấy từ `POST /api/auth/login` (`expires_in` giây, `0` = vĩnh viễn) — cùng nguồn.
- Kiểm tra server sống: `GET /api/version` — cùng nguồn.
- Lỗi thường gặp theo docs: 405 (sai method/thiếu `/api`), 400 (body sai), 404 "Agent not found" (sai `X-Agent-Id`), 503 "Channel Console not found" — cùng nguồn.
- Router: `APIRouter(prefix="/console")`, route `POST /chat` có description "Agent API Request Format. See runtime.agentscope.io. Use body.reconnect=true to attach to a running stream." — [src/qwenpaw/app/routers/console.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/app/routers/console.py) (bậc 1)
- Không có endpoint OpenAI-compatible phía vào: grep `chat/completions`, `/v1/`, `compatible-mode` trong `src/` chỉ ra code **gọi ra** provider (DashScope, OpenAI...), không có route nào nhận request kiểu OpenAI — source v2.2.1 và main (bậc 1, tự grep).

## 2. Chi tiết từ source mà docs không nói

- Schema `AgentRequest` (`src/qwenpaw/schemas.py`): `input: List[Message]`, `session_id`, `user_id`, `stream: bool = True`, `metadata`, `extra="allow"`. Docstring: "The original surface mirrored OpenAI's chat-completion request ... We keep extra=allow". Handler luôn trả `StreamingResponse` (`text/event-stream`) và không đọc `stream`, nên **`"stream": false` không có tác dụng** — [schemas.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/schemas.py), console.py (bậc 1). Nhận định từ đọc code.
- `_extract_session_and_payload`: thiếu `session_id` thì dùng `"default"`, thiếu `user_id` thì `"default"`, thiếu `channel` thì `"console"`. Hệ quả (nhận định): gọi nhiều lần không truyền `session_id` sẽ dồn vào **một** phiên `default`, lịch sử dính nhau. Khớp với issue #6918/#8078 trong report gốc ở chiều ngược lại.
- Gửi nhiều message trong `input` kiểu OpenAI: code có hai nhánh (`AgentRequest` lấy `input[0].content`, nhánh dict gộp content của mọi message). Chạy thử thấy server **gộp** hai message thành một lượt user có hai đoạn text. Tức là `input` không phải lịch sử hội thoại; muốn có lịch sử thì dùng `session_id`.
- Field thêm: `reconnect: true` để nối lại stream đang chạy; `request_context`; `model_slot_override` — console.py.
- Run tiếp tục chạy nền khi client ngắt; dừng bằng `POST /api/console/chat/stop?chat_id=<chat_id hoặc session_id>` — console.py.
- SSE thực tế có ba loại object theo AgentScope Runtime: `response`, `message`, `content` (delta). Channel console còn đẩy event `type: "turn_usage"` cuối stream — [channels/console/channel.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/app/channels/console/channel.py), [agent_management.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/tools/agent_management.py) (bậc 1).
- Cách chính QwenPaw lấy output khi agent gọi agent (`collect_final_agent_chat_response`): đọc hết SSE, giữ **payload cuối cùng không phải `turn_usage`**, rồi `extract_agent_text_content` lấy `output[-1].content[*]` có `type == "text"`, nối bằng `\n` — agent_management.py. Đây là công thức nên sao chép.
- `MessageType` có `message`, `reasoning`, `function_call`, `function_call_output`, `mcp_tool_call`, `plugin_call`, `progress`, `result`...; nên lọc `type == "message"` và `role == "assistant"` nếu không muốn lẫn tool call — schemas.py.

## 3. Chế độ không stream: task nền + poll

- `POST /api/console/chat/task`: body như `/chat` thêm `timeout` (giây, mặc định `DEFAULT_STREAM_TASK_TIMEOUT_SECONDS = 3600`); trả ngay `{"task_id": "task-xxxxxxxxxxxx", "timeout": 3600}` — console.py, constant.py @v2.2.1.
- `GET /api/console/chat/task/{task_id}`: `{"status":"running","started_at":...}` hoặc `{"status":"finished","result":{"status":"completed","session_id":...,"output":[...], ...}}`; lỗi/timeout thì `result.status = "failed"`, `result.error.message` — console.py.
- Task lưu **trong bộ nhớ** (`_bg_tasks` dict), restart server là mất (nhận định từ code).
- Endpoint này không có trong api-tutorial; được dùng bởi tool `submit_to_agent` và CLI `qwenpaw agents chat --background` — agent_management.py, cli/agents_cmd.py.

## 4. Các đường gọi khác

- CLI: `qwenpaw agents chat --from-agent <id> --to-agent <id> --text "..." [--session-id] [--mode] [--background] [--task-id] [--timeout 300]` — gọi chính API trên — [cli/agents_cmd.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/cli/agents_cmd.py) (bậc 1).
- ACP server: `qwenpaw acp [--agent <id>] [--workspace <path>]` biến QwenPaw thành agent theo Agent Client Protocol (JSON-RPC qua stdio), cho Zed/editor ACP — [acp-integration.en.md @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/acp-integration.en.md) (bậc 1). Đây là chuẩn mở duy nhất QwenPaw expose, nhưng là stdio, không phải HTTP.
- PawApp/plugin: có thể tự đăng ký route HTTP riêng (`@app.route`, `ctx.chat(...)`), ví dụ route `/chat` nhận `{"message", "session_id", "skill"}` trả JSON — [src/qwenpaw/pawapp/app.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/pawapp/app.py) (bậc 1). Là đường tự viết nếu cần endpoint JSON gọn hoặc OpenAI-compatible.

## 5. Kết quả chạy thử (2026-10-26, sandbox Linux, Python 3.13)

Cách dựng: `pip install qwenpaw==2.2.1` trong venv (`qwenpaw --version` → `2.2.1`); `QWENPAW_WORKING_DIR`/`QWENPAW_SECRET_DIR` trỏ vào thư mục tạm; `qwenpaw app --port 8088`. Model là một server giả OpenAI-compatible tự viết ở `127.0.0.1:9999/v1` (trả "PONG-from-fake-llm"), gắn vào QwenPaw bằng REST: `POST /api/models/custom-providers`, `PUT /api/models/fakellm/config` (api_key, base_url), `PUT /api/models/active` (`scope: "global"`). Không có model thật nên không đo chất lượng hay độ trễ.

- `GET /api/version` → `{"version":"2.2.1"}`. Ghi chú: `qwenpaw init --defaults` không chạy được khi stdin không phải terminal ("Aborted!"), nhưng `qwenpaw app` vẫn tự khởi tạo và chạy.
- `POST /api/console/chat` (đúng ví dụ docs) trả 9 event SSE, theo thứ tự: `response` created → `response` in_progress → `message` in_progress (assistant, content rỗng) → hai `content` có `delta: true` ("PONG-", "from-fake-llm") → một `content` `delta: false` chứa cả câu → `message` completed → `response` completed (có `output`, `usage: {input_tokens, output_tokens}`, `session_id`, `completed_at`) → `{"type":"turn_usage", ...}` (provider, model, token, cache).
- `"stream": false` vẫn trả `content-type: text/event-stream`. Xác nhận nhận định ở mục 2.
- `POST /v1/chat/completions`, `/api/v1/chat/completions`, `/api/chat/completions` → **405** (chỉ có SPA của Console bắt GET các đường này, trả HTML). `/api/openapi.json`, `/docs`, `/api/docs` → 404: không có Swagger để tra.
- `POST /api/console/chat/task` (`timeout: 120`) → `{"task_id":"task-82a0ae4e62f7","timeout":120}`; poll ngay → `{"status":"running",...}`; sau 3 giây → `status: "finished"`, `result.status: "completed"`, `result.output[0].content[0].text = "PONG-from-fake-llm"`, `result` có thêm `usage`.
- Đa lượt cùng `session_id`: lượt 2 server gửi cho model 4 message (system, user A, assistant, user B). Lượt đầu của mỗi phiên mới, model bị gọi **hai lần**: một lần trả lời, một lần sinh tiêu đề chat (`generate_and_update_title`), tốn thêm token.
- Không truyền `session_id`: hai request liên tiếp **dùng chung phiên** (lượt 2 thấy "NOSESS-1" trong lịch sử). Luôn đặt `session_id` riêng nếu muốn mỗi lần gọi độc lập.
- `X-Agent-Id: nope` → 404 `{"detail":"Agent 'nope' not found"}`.
- Hàm Python mẫu (lọc event `object=="response"` có `status` completed/failed, lấy text của message assistant) trả `('PONG-from-fake-llm', {'input_tokens': 10, 'output_tokens': 3}, 'api-682aeac5')`.

## 6. Chưa kiểm chứng

- Chưa chạy với model thật, chưa thử tool call nhiều bước (output khi đó có thêm message `function_call`... nên mới cần lọc `type == "message"`).
- Chưa thử gọi từ máy khác có bật auth (`Authorization: Bearer`), chưa thử `reconnect: true` và `/chat/stop`.
- Chưa đọc trang protocol của AgentScope Runtime (runtime.agentscope.io) trực tiếp; định dạng event ở trên lấy từ chạy thật.
