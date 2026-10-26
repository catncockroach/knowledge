# Structured output khi gọi QwenPaw qua API (bổ sung 2026-10-26)

Câu hỏi: khi gọi `POST /api/console/chat`, cấu hình structured output (JSON theo schema) thế nào?

Nguồn: repo `agentscope-ai/QwenPaw` tag `v2.2.1` và main (commit `95aa68f`, 2026-10-26); chạy thử `qwenpaw==2.2.1` với server model giả OpenAI-compatible (như `notes/api-chat.md`), lần này server giả ghi lại các key của request mà QwenPaw gửi tới model.

## 1. API chat không có tham số structured output

### Kết luận ngắn
Không có field kiểu `response_format`, `json_schema`, `output_schema` hay `structured_model` trong body của `/api/console/chat`, `/api/console/chat/task` hay `ctx.chat` của PawApp. Docs không có trang nào nói về structured output cho API. Mức chắc chắn: **cao** (grep source + docs ở cả v2.2.1 và main).

### Phát hiện có nguồn
- `AgentRequest` chỉ có `input`, `session_id`, `user_id`, `stream`, `metadata` (+ `extra="allow"`); handler chỉ đọc thêm `reconnect`, `request_context`, `model_slot_override` — [schemas.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/schemas.py), [console.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/app/routers/console.py) (bậc 1).
- grep `response_format|output_schema|structured_model|json_schema` trong `src/qwenpaw/app`, `src/qwenpaw/runtime`, `schemas.py` ở main: không có kết quả. `structured_model` chỉ xuất hiện ở `routing_chat_model.py` và `token_usage/model_wrapper.py`, nơi nó bị **`kwargs.pop("structured_model", None)`** (bỏ đi) với chú thích "agentscope 2.0 doesn't pass structured_model through __call__ (it goes via generate_structured_output)" — [routing_chat_model.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/routing_chat_model.py) (bậc 1).
- Agent ReAct của QwenPaw không gọi `generate_structured_output` ở đâu cả; docs context còn ghi Scroll "never invokes generate_structured_output, JSON mode, or a response schema" — [context.en.md @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/context.en.md) (bậc 1).
- `ctx.chat(message, skill=None, session_id=None, channel=None, user_id=None)` của PawApp cũng không có tham số schema — [pawapp/context.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/pawapp/context.py) (bậc 1).

## 2. Đường gián tiếp: `generate_kwargs` của model + `model_slot_override` theo request

### Phát hiện có nguồn
- Docs "Generation Parameters": Settings của provider → Advanced Configuration, nhập JSON tham số (ví dụ `temperature`, `top_p`, `max_tokens`), "QwenPaw will automatically include these parameters when generating with models from this provider" — [models.en.md @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/website/public/docs/models.en.md) (bậc 1). Docs không nói tới `response_format`.
- REST: `PUT /api/models/{provider_id}/models/{model_id}/config` với `{"generate_kwargs": {...}}` ("Per-model generation parameters ... override provider-level generate_kwargs"). Validator chỉ kiểm `max_tokens`, mọi key khác đi qua nguyên — [providers.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/app/routers/providers.py) (bậc 1).
- `model_slot_override` trong body chat chọn model cho **một request**: nhận dict `{"provider_id","model"}` hoặc chuỗi `"provider:model"`; sai định dạng thì chỉ log warning và dùng model mặc định — `_resolve_model_slot_override` trong [model_factory.py @v2.2.1](https://github.com/agentscope-ai/QwenPaw/blob/v2.2.1/src/qwenpaw/agents/model_factory.py), `ModelSlotConfig` trong config.py (bậc 1). Không có trong docs.

### Chạy thử (2026-10-26)
1. Tạo provider custom thứ hai `fakejson` trỏ cùng server, model `fake-model`, rồi `PUT /api/models/fakejson/models/fake-model/config` với `generate_kwargs.response_format = {"type":"json_schema","json_schema":{"name":"label","strict":true,"schema":{...label, score...}}}` → 200, `generate_kwargs` được lưu.
2. Chat với `"model_slot_override": {"provider_id":"fakejson","model":"fake-model"}`: request tới model có key `["model","response_format","stream","stream_options","tools"]`, `response_format` đúng nguyên văn, **kèm 26 tool**. Call sinh tiêu đề chat (không tool) vẫn dùng model mặc định, không có `response_format`.
3. Chat không override: key `["model","stream","stream_options","tools"]`, không có `response_format`.
4. Dạng chuỗi `"model_slot_override": "fakejson:fake-model"` cũng chạy. Request kế tiếp cùng `session_id` mà không override thì quay về model mặc định: override **chỉ áp cho request đó**.

### Nhận định (chưa kiểm với model thật)
- Vì `response_format` đi chung với danh sách tool, mọi lượt gọi model trong vòng ReAct của request đó đều bị ép schema. Với OpenAI, tool call vẫn được phép khi có `response_format` (schema chỉ ràng buộc nội dung text), nên thường ổn. Với vLLM/Ollama/LM Studio, guided decoding JSON có thể chặn model phát tool call hoặc bị backend từ chối khi đi cùng `tools`. Nên test trên backend thật.
- Backend phải hiểu `response_format` kiểu `json_schema` (OpenAI và vLLM có; Ollama dùng field `format` riêng ở API gốc, phần OpenAI-compatible tùy bản). Provider Anthropic dùng `messages`, không có `response_format`; key lạ có thể làm request lỗi.

## 3. Cách chắc chắn nhất: schema trong prompt (hoặc skill/persona) + kiểm ở client

- Nhét schema vào chính tin nhắn ("Chỉ trả về JSON đúng schema sau, không markdown: ..."), lấy text cuối như `notes/api-chat.md`, `json.loads`, validate (Pydantic/jsonschema), sai thì gửi lại trong **cùng `session_id`** kèm lỗi để agent tự sửa. Cách này không phụ thuộc backend.
- Muốn khỏi lặp schema mỗi lần: tạo agent riêng (ví dụ `labeler`) có persona/`AGENTS.md` ghi định dạng đầu ra, hoặc một skill mô tả format rồi gọi `ctx.chat(..., skill=...)` / nhắc tên skill trong tin. Đây là nhận định dựa trên cơ chế persona/skill đã mô tả trong report, chưa đo tỉ lệ tuân thủ.
- Nếu chỉ cần JSON mà không cần tool/memory của agent: gọi thẳng endpoint model (vLLM/Ollama/OpenAI) với `response_format`, như report đã khuyên cho pipeline gắn nhãn.
