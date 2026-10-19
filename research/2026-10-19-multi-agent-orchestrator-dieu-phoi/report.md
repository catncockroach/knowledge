---
title: Orchestrator multi-agent điều phối subtask và giữ mục tiêu qua nhiều lượt gọi model
date: 2026-10-19
question: Một orchestrator LLM chia việc cho các subagent, nhận kết quả về, và dù được gọi lại nhiều lần vẫn bám đúng mục tiêu ban đầu của task bằng cơ chế gì, và prompt gửi cho model ở mỗi lượt gồm những gì?
tags: [multi-agent, orchestrator, subagent, context-engineering, tool-use, goal-drift]
---

# Orchestrator bám mục tiêu nhờ harness, không nhờ model nhớ

> **Câu hỏi:** Orchestrator LLM giao việc, nhận kết quả và giữ đúng mục tiêu gốc qua nhiều lượt gọi model bằng cơ chế gì; prompt mỗi lượt gồm những gì? · **Ngày:** 2026-10-19 · **Phạm vi:** hệ multi-agent dựa trên LLM 2023–10/2026, trọng tâm orchestrator–worker; docs chính thức, source code, engineering blog, paper. · **Kiểm chứng:** 42 khẳng định đã đối chiếu nguồn, 14 đã sửa

## Tóm tắt

Orchestrator không "nhớ" mục tiêu: nó là một model stateless được harness gọi lặp lại, và ở mỗi lượt harness gửi lại **toàn bộ** request, gồm tool definitions (trong đó có tool giao việc cho subagent), system prompt và mảng `messages` mở đầu bằng task gốc của người dùng, tiếp theo là mọi cặp `tool_use`/`tool_result` trước đó [1][2]. Ở hầu hết hệ thống thật, giao việc là **một tool call**: runtime chạy một vòng agent riêng với context trắng, chủ yếu gồm system prompt của subagent và chuỗi prompt giao việc, rồi trả **tin nhắn cuối** của subagent về làm `tool_result`; mọi bước trung gian ở lại bên trong subagent [3][4][5][6]. Vì thế, việc bám mục tiêu là thuộc tính của cách harness bày context chứ không phải của model. Task gốc nằm trong phần prefix không bao giờ bị sửa. Mục tiêu và plan được nhắc lại ở **cuối** context (ở mỗi lượt điều phối, Magentic-One append một tin bắt đầu bằng "Recall we are working on the following request: {task}") và được ghi ra ngoài context để sống sót qua compaction [7][8][9]. Context của lead được giữ nhỏ nhờ subagent chỉ trả về bản chưng cất, còn câu hỏi "xong chưa, có đang lặp không" bị ép thành bước bắt buộc kèm giới hạn cứng [10][11]. Bằng chứng định lượng tốt nhất cho các cơ chế này là ablation của Magentic-One: thay Orchestrator bằng một group chat chỉ chọn người nói (bỏ ledger, planning, theo dõi tiến độ, phát hiện lặp) thì điểm GAIA giảm **31%** [12]. Phần lớn các con số khác là vendor tự báo cáo, hoặc là paper chỉ đọc được qua kết quả search vì proxy chặn arXiv. Multi-agent cũng không phải lúc nào cũng tốt hơn: theo Anthropic nó tốn khoảng **15×** token so với chat [8], và theo một nghiên cứu có kiểm soát (qua search) nó thắng ở tác vụ song song hoá được nhưng thua ở tác vụ tuần tự [13].

**Điểm chính**
- Mọi kiến trúc (agent-as-tool, handoff, hierarchical, group chat có manager) đều hiện ra với model như một function tool hoặc một trường JSON chọn người làm tiếp; chúng chỉ khác nhau ở việc runtime làm gì sau đó: chạy vòng con rồi trả `tool_result`, hay chuyển cả hội thoại sang agent khác [4][14][11].
- Subagent chỉ biết những gì nằm trong chuỗi prompt giao việc, và orchestrator chỉ biết những gì subagent viết vào tin cuối; prompt giao việc tốt có một mục tiêu, bối cảnh, câu hỏi, nguồn và công cụ, ranh giới, ngân sách và định dạng đầu ra [3][15].
- Request lượt N có thứ tự cố định tools → system → messages; giữ phần đầu bất biến để trúng prompt cache (đọc cache **0,1×** giá input, thấp hơn nữa ở một số model mới) và đặt trạng thái động như ledger, todo hay reminder ở cuối [16][1].
- Bộ kỹ thuật giữ hướng có bằng chứng: nhắc lại task ở cuối context, ledger có cấu trúc kèm đếm đình trệ và replan (−31% GAIA khi bỏ), plan ghi ra file hoặc memory được tái chèn sau compaction, cô lập context subagent, evaluator tách khỏi generator, và giới hạn cứng [12][9][17].
- Nghiên cứu có kiểm soát (chỉ đọc qua search) cho thấy kiến trúc tập trung chỉ khuếch đại lỗi **4,4×**, so với **17,2×** ở các agent độc lập, nhưng mọi biến thể multi-agent đều giảm **39–70%** trên tác vụ suy luận tuần tự [13].

## Mọi kiểu điều phối do LLM quyết định đều quy về một tool call; chúng chỉ khác ở việc runtime làm gì sau đó

Anthropic định nghĩa pattern orchestrator–workers là "a central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results", và nhấn mạnh rằng subtask "aren't pre-defined, but determined by the orchestrator based on the specific input" [18]. Đọc docs và source code của sáu hệ thống, có bốn họ cài đặt. Họ thứ nhất là **agent-as-tool/supervisor**: orchestrator gọi subagent như một tool rồi giữ quyền điều khiển. Họ thứ hai là **handoff**: quyền điều khiển chuyển hẳn sang agent khác, và agent đó tiếp quản hội thoại. Họ thứ ba là **group chat có manager LLM** chọn người nói tiếp, như AutoGen Selector hay Magentic-One. Họ thứ tư là **workflow cứng bằng code**, như `SequentialAgent`/`ParallelAgent`/`LoopAgent` của ADK hay "orchestrating via code" của OpenAI [19][20][21]. Hierarchical chỉ là agent-as-tool lồng nhiều tầng; Claude Code mặc định cho phép lồng tới **3 tầng** dưới hội thoại chính và tối đa **20** subagent chạy đồng thời [22].

Ở mức API, ranh giới giữa các họ mỏng hơn tên gọi. OpenAI ghi thẳng "Handoffs are represented as tools to the LLM": handoff tới `Refund Agent` hiện ra với model dưới dạng tool `transfer_to_refund_agent` [14]. Docstring của `as_tool` nêu đúng hai khác biệt: "In handoffs, the new agent receives the conversation history. In this tool, the new agent receives generated input", và trong handoff agent mới "takes over the conversation", còn với tool thì "the conversation is continued by the original agent" [4]. LangGraph supervisor cũng dùng tool `transfer_to_<agent>`, kèm một cạnh cố định đưa quyền về supervisor sau khi worker xong [23]. ADK có cả `transfer_to_agent(agent_name, ...)`, vốn chỉ bật một cờ để runtime chuyển agent, và subagent `mode='single_turn'` được framework tự expose thành tool [24][6]. Ngoại lệ là Magentic-One: Orchestrator không gọi tool mà trả một JSON có trường `next_speaker` và `instruction_or_question` mỗi lượt [11].

| Hệ thống | Model thấy cách giao việc là | Context subagent nhận | Kết quả quay về | Song song | Biết subagent xong bằng |
|---|---|---|---|---|---|
| Anthropic Research | tool `run_blocking_subagent(prompt)` [15] | system prompt riêng + chuỗi `prompt` | báo cáo cô đọng nộp qua `complete_task`, hoặc tham chiếu tới artifact [25][8] | 3–5 subagent song song trong một đợt, đồng bộ giữa các đợt [8] | subagent gọi `complete_task`, trần cứng 20 tool call [25] |
| Claude Code / Agent SDK | tool `Agent` (`subagent_type`, `prompt`, `run_in_background`) [3] | system prompt riêng + prompt + CLAUDE.md + tool defs; riêng fork thì thừa kế toàn bộ hội thoại [22] | tin cuối + `agentId: <id>`, đánh dấu partial nếu chạm `maxTurns` [3] | chạy background mặc định, tối đa 20 đồng thời [22] | tool trả về (sync) hoặc completion notification ở lượt sau [22] |
| OpenAI Agents SDK | `Agent.as_tool()` với input `{"input": ...}`; handoff là `transfer_to_<agent>` [26][14] | as_tool: chỉ input do model sinh; handoff: toàn bộ lịch sử, lọc bằng `input_filter` [4][14] | as_tool: `final_output`; handoff: không có kết quả trả về [4] | `parallel_tool_calls`; mỗi lượt chỉ thực hiện handoff đầu tiên [27][28] | model con trả text không kèm tool call; `MaxTurnsExceeded` [27] |
| LangGraph / LangChain | `task(agent_name, description)` hoặc `transfer_to_<agent>` [5][23] | description làm human message cho subagent | tin cuối làm tool result; `output_mode` là `last_message` hoặc `full_history` [5][23] | supervisor mặc định `parallel_tool_calls=False` [23] | vòng con kết thúc; cạnh cố định quay về supervisor [23] |
| Magentic-One (AutoGen) | trường JSON `next_speaker` + `instruction_or_question` [11] | thread tin nhắn chung, bị xoá khi replan [7] | tin trả lời cuối của agent vào thread; tool call bị lọc khỏi context Orchestrator [7] | tuần tự, mỗi bước một agent [7] | `is_request_satisfied` hoặc `max_turns` [7] |
| Google ADK | `transfer_to_agent` hoặc subagent `single_turn` thành tool [20][6] | session con copy state của cha [6] | content cuối (bỏ part `thought`), hoặc `output_key` trong shared state [6][20] | chỉ `single_turn` chạy song song [29] | `finish_task` ở mode `task` [29] |

Bảng cho thấy hai trục thiết kế độc lập. Trục thứ nhất là **context vào**: chỉ chuỗi prompt (Claude subagent thường, `as_tool`, `task`), toàn bộ lịch sử (fork, handoff), hay state chung (ADK). Trục thứ hai là **kết quả ra**: tin cuối, toàn bộ lịch sử, tham chiếu tới file, hay key trong state. Xu hướng 2025–2026 là tự viết supervisor bằng tool thay vì dùng thư viện chuyên dụng. README `langgraph-supervisor` giờ tự khuyên "using the supervisor pattern directly via tools rather than this library… gives you more control over context engineering" [23], và docstring `AgentTool` của ADK ghi "Direct usage of `AgentTool` is discouraged" [6]. AutoGen nay đã archived, "no longer maintained", và README trỏ sang Microsoft Agent Framework cho dự án mới [21]. **Nhận định:** với người tự thiết kế, điều đáng học là primitive tool call cùng hai trục context vào/kết quả ra, chứ không phải tên pattern của từng framework.

## Subagent khởi đầu từ context trắng, và chỉ tin nhắn cuối đi về orchestrator

Chiều đi rất hẹp. Claude Agent SDK viết: "The only content you pass from parent to subagent is the Agent tool's prompt string, so include any file paths, error messages, or decisions the subagent needs directly in that prompt". Subagent thường **không** nhận lịch sử hội thoại, tool result hay system prompt của parent [3]. OpenAI nói tương tự cho `as_tool`: "the parent run's conversation state is not inherited automatically" [26]. Với LangChain, mô tả task "is passed as a human message to the sub-agent" [5]. Ngoại lệ có chủ đích là **fork** của Claude Code: "a subagent that inherits the entire conversation so far instead of starting fresh". Fork dùng cùng system prompt và tool với main agent nên tái dùng được prompt cache [22].

Chiều về cũng hẹp như vậy. "Intermediate tool calls and results stay inside the subagent; only its final message returns to the parent". Kết quả của Agent tool có thêm một text block `agentId: <id>` để resume sau, và bị đánh dấu partial nếu subagent chạm `maxTurns` [3]. `as_tool` của OpenAI trả `final_output`, rỗng thì quét ngược lấy output gần nhất, và cho phép `custom_output_extractor` [4]. ADK lấy content cuối và bỏ các part `thought` [6]. LangChain cảnh báo một lỗi điển hình: subagent làm việc nhưng "doesn't include results in its final message—remind it that the supervisor only sees the final output" [5]. Anthropic Research bổ sung đường thứ hai: subagent "store their work in external systems, then pass lightweight references back to the coordinator", để giảm "game of telephone" khi thông tin chuyển tay qua lead [8]. Kết quả subagent là dữ liệu không đáng tin. Docs Claude khuyên giữ nội dung untrusted "inside `tool_result` blocks rather than `system` prompts or plain user `text` blocks" [2]. Từ v2.1.210, Claude Code vô hiệu hoá thẻ kiểu `<system-reminder>` và escape các dòng bắt đầu bằng `Human:`/`Assistant:` trong báo cáo subagent, để báo cáo không giả được ranh giới lượt [3].

Orchestrator biết subagent đã xong theo ba cách. Ở chế độ đồng bộ, vòng con kết thúc khi model con trả text mà không kèm tool call: runner OpenAI coi đó là final output, và raise `MaxTurnsExceeded` nếu vượt trần [27]. Cách thứ hai là một tool kết thúc tường minh: subagent Anthropic được dặn "immediately use the `complete_task` tool", còn ADK mode `task` chạy "until it calls `finish_task`" [25][29]. Cách thứ ba dành cho chế độ background, vốn là mặc định của Claude Code theo docs hiện tại (truy cập 2026-10-19): "A background subagent's results reach Claude as a completion notification in a later turn", và notification được đánh dấu là sự kiện tự động chứ không phải tin của người dùng. Docs thừa nhận trước v2.1.211 Claude đôi khi báo kết quả cho subagent chưa xong [22]. Song song đạt được khi model phát nhiều block `tool_use` trong một response và runtime chạy chúng đồng thời [27]. Anthropic Research vẫn giữ **đồng bộ giữa các đợt**, tức chờ cả đợt xong mới đi tiếp, dù tự nhận "Synchronous execution creates bottlenecks" [8].

Orchestrator không thấy gì bên trong subagent. Transcript của subagent Claude Code được lưu riêng và có thể **resume** với đầy đủ lịch sử; các message trong stream mang `parent_tool_use_id`, nên ứng dụng host quan sát được dù model cha không thấy [22][3]. Magentic-One lọc bỏ `ToolCallRequestEvent`/`ToolCallExecutionEvent` khi dựng context cho Orchestrator [7]. **Nhận định:** hệ quả thực tế là mọi điều subagent biết nhưng không viết vào tin cuối đều mất với orchestrator. Định dạng đầu ra trong prompt giao việc vì thế là thành phần chịu tải, không phải chi tiết trình bày.

## Lượt thứ N là toàn bộ request gửi lại từ đầu, cộng phần chèn ở cuối

"The Messages API is stateless, which means that you always send the full conversational history to the API" [1]. Kể cả khi server giữ lịch sử, như `previous_response_id` của OpenAI Responses API, "all previous input tokens for responses in the chain are billed as input tokens" (chỉ đọc qua snippet search) [30]. Như vậy model vẫn đọc lại tất cả ở mỗi lượt. Khi request có `tools`, API của Claude tự dựng system prompt theo thứ tự: câu mở về tool, hướng dẫn định dạng, định nghĩa tool dạng JSON Schema, **rồi mới tới** system prompt của người dùng [31]. Tool giao việc vì thế nằm ở đầu những gì model thấy. Claude không có role `tool` riêng: `tool_result` nằm trong message `role: user`, phải đứng ngay sau `tool_use` tương ứng, và phải đứng **trước** mọi text trong cùng message, nếu sai thứ tự API trả lỗi 400 [2].

| Thành phần request lượt N | Vị trí | Ổn định hay thay đổi | Vai trò với mục tiêu gốc |
|---|---|---|---|
| `tools`, gồm tool giao việc và tool kết thúc | đầu prefix | bất biến; đổi tên, mô tả hay tham số là mất toàn bộ cache [16] | quy định cách giao việc và cách nộp kết quả |
| `system` | sau tools | bất biến | neo vai trò và mục tiêu, vd "a query… which serves as your primary goal" [15] |
| Tin user đầu tiên (task gốc) | đầu `messages` | bất biến, trừ khi bị compaction | bản gốc duy nhất của mục tiêu |
| Các cặp `assistant tool_use` / `user tool_result` | giữa | append-only | trạng thái thực: plan đã nói, kết quả subagent |
| Reminder, ledger, todo, mid-conversation `system` | cuối | đổi mỗi lượt | đưa mục tiêu và plan vào vùng attention gần [1][32] |
| Bản tóm tắt compaction | thay các lượt cũ | sinh lại khi gần đầy | giữ quyết định và việc dở, nhưng có thể làm mất chỉ dẫn sớm [33] |

Thứ tự này do chi phí quyết định. Prompt cache của Claude so khớp prefix theo thứ tự "`tools`, `system`, and `messages`". Ghi cache tốn **1,25×** giá input (TTL 5 phút), đọc cache **0,1×** (một số model mới còn rẻ hơn: 0,05× với Opus 5.5/Sonnet 5.5, 0,025× với Fable 5.1/Mythos 5.1), và với hội thoại tăng dần "earlier content never changes, so the next request's lookback finds the prior write" [16]. Manus (qua snippet search) gọi tỉ lệ trúng KV-cache là "the single most important metric for a production-stage AI agent". Họ nêu tỉ lệ input:output khoảng **100:1** và chênh lệch **10×** giữa token có cache và không cache trên Claude Sonnet, và khuyên không sửa action/observation cũ, serialize JSON một cách tất định [34]. Claude cung cấp hai kênh chèn chỉ dẫn mà không phá cache. Kênh thứ nhất là message `role: system` đặt giữa hội thoại, chỉ có trên một số model đời mới (như Opus 4.8, Opus 5, Opus 5.5, Sonnet 5.5, Haiku 5.5); nó "has the same authority as the top-level `system` field" và "does not invalidate any cached prefix" [1]. Kênh thứ hai là `<system-reminder>`, thẻ mà harness Claude Code chèn khi phiên bắt đầu, khi hook trả text hoặc khi file đổi trên đĩa [32][3].

**Ví dụ minh hoạ, do người viết dựng theo đúng định dạng docs ở trên; không phải traffic thật, nội dung và tên tool `run_subagent` là giả định (mô phỏng `run_blocking_subagent` của Anthropic).**

Lượt 1, request gửi cho orchestrator:

```json
{
  "model": "claude-…",
  "system": "You are an expert research lead… The user's query is your primary goal…",
  "tools": [
    {"name": "run_subagent",
     "description": "Spawn a research subagent with a fresh context. It cannot see this conversation; put everything it needs in `prompt`. Returns only the subagent's final report.",
     "input_schema": {"type": "object", "properties": {"prompt": {"type": "string"}}, "required": ["prompt"]}},
    {"name": "complete_task",
     "description": "Submit the final report to the user.",
     "input_schema": {"type": "object", "properties": {"report": {"type": "string"}}, "required": ["report"]}}
  ],
  "messages": [
    {"role": "user", "content": "So sánh hệ thống thuế thu nhập cá nhân của Thụy Điển, Na Uy, Đan Mạch"}
  ]
}
```

Lượt 1, response: `stop_reason: "tool_use"`. Content gồm một text block nêu kế hoạch và ba block `tool_use` (`toolu_A`, `toolu_B`, `toolu_C`) phát trong cùng một response, nên harness chạy ba subagent song song. Mỗi subagent là một vòng lặp riêng với request riêng, không chứa gì của orchestrator ngoài chuỗi prompt:

```json
{
  "system": "<system prompt riêng của subagent, vd research_subagent.md>",
  "tools": ["web_search", "web_fetch", "complete_task"],
  "messages": [
    {"role": "user", "content": "<nguyên văn input.prompt của toolu_A: mục tiêu, bối cảnh, câu hỏi, nguồn, ranh giới, ngân sách, định dạng đầu ra>"}
  ]
}
```

Lượt 2, request gửi cho orchestrator. Harness gửi lại **y nguyên** `tools`, `system` và các message cũ (phần này trúng cache), rồi append kết quả:

```json
{
  "system": "…(y nguyên)…",
  "tools": ["…(y nguyên)…"],
  "messages": [
    {"role": "user", "content": "So sánh hệ thống thuế thu nhập cá nhân của Thụy Điển, Na Uy, Đan Mạch"},
    {"role": "assistant", "content": [
      {"type": "text", "text": "Kế hoạch: mỗi nước một subagent, cùng khung so sánh…"},
      {"type": "tool_use", "id": "toolu_A", "name": "run_subagent", "input": {"prompt": "Mục tiêu: thuế TNCN Thụy Điển… Không tìm thuế doanh nghiệp… Tối đa ~10 tool call… Trả về: danh sách dữ kiện dày đặc kèm nguồn, ≤1.500 token"}},
      {"type": "tool_use", "id": "toolu_B", "name": "run_subagent", "input": {"prompt": "…Na Uy…"}},
      {"type": "tool_use", "id": "toolu_C", "name": "run_subagent", "input": {"prompt": "…Đan Mạch…"}}
    ]},
    {"role": "user", "content": [
      {"type": "tool_result", "tool_use_id": "toolu_A", "content": "<báo cáo cô đọng của subagent A>"},
      {"type": "tool_result", "tool_use_id": "toolu_B", "content": "<báo cáo của subagent B>"},
      {"type": "tool_result", "tool_use_id": "toolu_C", "content": "Subagent stopped: tool-call limit reached. Partial: …", "is_error": true},
      {"type": "text", "text": "<system-reminder>Mục tiêu gốc: so sánh thuế TNCN 3 nước. Đã có: Thụy Điển, Na Uy. Còn thiếu: Đan Mạch.</system-reminder>"}
    ]}
  ]
}
```

Từ lượt 3 trở đi, harness tiếp tục append từng cặp `assistant tool_use` → `user tool_result`. Vòng lặp kết thúc khi orchestrator gọi `complete_task` hoặc trả `stop_reason: "end_turn"`. Khi lịch sử gần đầy, harness xoá tool result cũ hoặc thay các lượt cũ bằng bản tóm tắt [35][36]. Nội dung thật của `<system-reminder>` mà Claude Code chèn không được công bố trong docs chính thức; dòng reminder ở trên chỉ minh hoạ vị trí và vai trò.

Magentic-One dựng context theo cách khác và tường minh hơn. Mỗi bước, `_orchestrate_step` lấy toàn bộ thread, trong đó tin của agent khác thành `UserMessage` và tin của Orchestrator thành `AssistantMessage`. Sau đó nó append một `UserMessage` Progress Ledger mở đầu bằng "Recall we are working on the following request:\n\n{task}" rồi gọi model lấy JSON. Prompt ledger này **không được lưu** vào thread; chỉ `instruction_or_question` được lưu và broadcast [7][11]. Mỗi lượt điều phối vì vậy có dạng: [Task Ledger: task, team, facts, plan] → [các tin trả lời cuối của từng agent] → [tin tạm: nhắc lại task + yêu cầu trả 5 trường JSON]. **Nhận định:** "trạng thái" của orchestrator chính là mảng `messages` do harness giữ. Bám mục tiêu ở mức API nghĩa là task gốc luôn nằm trong prefix gửi lại, và được harness chủ động đặt lại ở cuối context.

## Prompt giao việc phải tự đủ, vì subagent không thấy gì ngoài nó

Anthropic kể rằng chỉ dẫn ngắn kiểu "research the semiconductor shortage" khiến các subagent làm trùng nhau: một subagent tìm khủng hoảng chip ô tô 2021, trong khi hai subagent khác làm trùng việc nhau về chuỗi cung ứng 2025. Kết luận của họ là mỗi subagent cần "an objective, an output format, guidance on the tools and sources to use, and clear task boundaries" [8]. Prompt lead agent mà Anthropic mở nguồn liệt kê chi tiết hơn trong mục `<delegation_instructions>` [15]. Bảng dưới gộp danh sách đó với docs Claude Code và prompt Magentic-One.

| Thành phần prompt giao việc | Vì sao cần | Diễn đạt trong nguồn |
|---|---|---|
| Một mục tiêu cốt lõi | tránh trùng và lệch giữa các subagent | "ideally just 1 core objective per subagent" [15] |
| Bối cảnh: task gốc, phần việc này góp gì vào plan, dữ kiện cha đã biết (đường dẫn, lỗi, quyết định) | subagent bắt đầu từ context trắng | "Relevant background context about the user's question and how the subagent should contribute" [15]; "include any file paths, error messages, or decisions" [3] |
| Câu hỏi cụ thể cần trả lời | biến mục tiêu thành tiêu chí kiểm được | "Key questions to answer" [15] |
| Nguồn và tool nên dùng, tiêu chí tin cậy, nguồn nên tránh | giảm tìm lan man | "define what constitutes reliable information… list any unreliable sources to avoid" [15] |
| Ranh giới phạm vi | chống drift và trùng việc | "precise scope boundaries to prevent research drift" [15] |
| Ngân sách công sức | chống lặp và tìm vô tận | subagent tự đặt ngân sách từ dưới 5 tới khoảng 15 tool call theo độ khó, trần cứng "20 tool calls and… about 100 sources" [25]; `maxTurns` ở harness [3] |
| Định dạng và độ dài đầu ra | chỉ tin cuối về tới cha | "Expected output format" [15]; bản chưng cất thường **1.000–2.000 token** [10] |
| Cách kết thúc và báo xung đột | để cha biết xong và tự phân xử | `complete_task`; báo nguồn mâu thuẫn về cho lead thay vì tự chọn [25] |

Prompt của Magentic-One thu gọn tất cả vào một câu hỏi bắt buộc: "What instruction or question would you give this team member? (Phrase as if speaking directly to them, and include any specific information they may need)" [11]. Phía lead cũng cần quy tắc cho việc **có nên** giao việc không. Anthropic ghi quy tắc scale ngay trong prompt: "Simple fact-finding requires just 1 agent with 3-10 tool calls, direct comparisons might need 2-4 subagents with 10-15 calls each, and complex research might use more than 10 subagents" [8]. Prompt lead còn dặn mặc định 3 subagent, "Never create more than 20", "You MUST use parallel tool calls", và "NEVER create a subagent to generate the final report" [15]. Quy tắc này ra đời vì phiên bản sớm từng "spawning 50 subagents for simple queries" [8]. Vấn đề ngược lại cũng có: docs SDK ghi "Claude Opus 5 delegates to subagents more readily than earlier models", nên preset `claude_code` thêm một dòng system prompt dặn không gọi Agent tool trừ khi được yêu cầu [3]. Trong Claude Code, quyết định giao việc dựa vào field `description` của từng subagent [22]. **Nhận định:** thành phần hay bị thiếu nhất là bối cảnh, vì orchestrator "biết" quá nhiều và dễ cho rằng subagent cũng biết. Chất lượng bước tích hợp kết quả phụ thuộc trực tiếp vào việc prompt giao việc có tiêu chí kiểm được hay không.

## Giữ đúng hướng là việc của harness: mục tiêu ở chỗ không bị nén, nhắc lại ở cuối, kiểm bắt buộc mỗi vòng

Có hai lý do mục tiêu bị trôi. Thứ nhất, chất lượng model giảm khi context dài ra. Anthropic gọi hiện tượng này là context rot: "the model's ability to accurately recall information from that context decreases" khi số token tăng [10]. "Lost in the Middle" (qua search) cho thấy độ chính xác cao nhất khi thông tin nằm ở đầu hoặc cuối context, và giảm khi nằm giữa [37]. Thứ hai, áp lực trong context kéo model khỏi mục tiêu. Trong môi trường mô phỏng giao dịch cổ phiếu, mọi model được thử đều drift ở mức nào đó, drift mạnh hơn khi pha theo đuổi mục tiêu trung gian kéo dài và tương quan với xu hướng pattern-matching tăng theo độ dài context; model tốt nhất (Claude 3.5 Sonnet có scaffold) giữ mục tiêu gần hoàn hảo **quá 100.000 token** (qua search) [38]. Khi yêu cầu bị chia nhỏ qua nhiều lượt, các LLM hàng đầu giảm trung bình **39%**, nhưng gộp lại vào một lượt thì đạt **95,1%** so với bản đầy đủ (qua search) [39]. Kết quả này cho thấy cách bày context quan trọng không kém lượng thông tin có trong đó. Các kỹ thuật dưới đây đều nhắm vào hai lý do trên.

**Neo mục tiêu ở nơi không bị nén, rồi tái chèn.** Lead agent của Anthropic lưu plan vào Memory "since if the context window exceeds 200,000 tokens it will be truncated and it is important to retain the plan" [8]. Claude Code thừa nhận "instructions from early in the conversation can get lost" sau compaction, và khuyên đặt quy tắc lâu dài vào CLAUDE.md [33]. Sau compaction, nó **tái chèn từ đĩa** CLAUDE.md, plan viết trong plan mode và tối đa 5 file đã đọc hoặc sửa (ưu tiên file sửa đổi gần nhất). Nó cũng nhắc lại các subagent nền còn chạy "so it doesn't start a duplicate" [9]. Ở dạng coding chạy dài, Anthropic dùng initializer agent để tạo feature list JSON (trường `passes`, cấm sửa test) và `claude-progress.txt`. Mỗi phiên mới bắt đầu bằng việc đọc git log, progress file và feature list [40].

**Nhắc lại mục tiêu ở cuối context.** Magentic-One làm việc này ở **mọi** lượt điều phối bằng câu "Recall we are working on the following request" [7]. Manus (qua snippet search) cho agent liên tục viết lại `todo.md`, "reciting its objectives into the end of the context" để tránh "lost-in-the-middle" trong một task trung bình khoảng **50 tool call** [34]. Claude Code có todo tool, nhưng docs hiện ghi "Newer models track multi-step work without a written todo list": các tool này chỉ bật mặc định cho Opus 4.7, Sonnet 4.6, Haiku 4.5 và model cũ hơn [41]. **Nhận định:** recitation do model tự làm tốn lượt gọi tool, nên gánh "nhớ plan" đang chuyển sang harness (system reminder, mid-conversation system message, tái chèn file). Cách này không tốn lượt của model và không phá cache.

**Ledger có cấu trúc, đếm đình trệ và replan.** Đây là cơ chế có bằng chứng định lượng rõ nhất. Orchestrator của Magentic-One giữ một Task Ledger gồm facts đã biết, facts cần tra, facts cần suy ra, phỏng đoán và plan. Ở mỗi vòng, nó phải trả lời năm câu: task đã xong chưa, có đang lặp không, có tiến triển không, ai làm tiếp, giao chỉ dẫn gì [12][11]. Bộ đếm stall tăng khi đang lặp hoặc không tiến triển, và giảm 1 khi có tiến triển. Khi bộ đếm chạm `max_stalls` (mặc định **3** trong code, khớp với ngưỡng "≤ 2" trong paper), Orchestrator tự phân tích "what went wrong", cập nhật facts và plan, **xoá** thread, reset mọi agent rồi mở lại bằng một Task Ledger mới [7][12][42]. Câu trả lời cuối dùng prompt riêng, nhắc lại "{task}" một lần nữa [11]. Ablation trên GAIA validation với GPT-4o thay Orchestrator bằng một group chat chỉ chọn người nói, tức bỏ ledger, planning, theo dõi tiến độ, phát hiện lặp và chỉ dẫn tường minh. Kết quả: "without the full ledgers, performance drops by **31%**" [12]. Paper không tách riêng đóng góp của từng thành phần.

**Cô lập context subagent để context của lead sạch.** Subagent dùng hàng chục nghìn token để khám phá nhưng chỉ trả về "a condensed, distilled summary of its work (often 1,000-2,000 tokens)" [10]. Lead nhờ vậy giữ được task gốc, plan và các bản tóm tắt ngắn trong phần context mà nó chú ý tốt. Nghiên cứu có kiểm soát của Kim và cs. (qua search) đo được kiến trúc tập trung khuếch đại lỗi **4,4×** so với single-agent, thấp hơn nhiều so với **17,2×** khi các agent chạy độc lập. Tác giả cho rằng nguyên nhân là "the orchestrator reviews sub-agent outputs before aggregation" [13]. Cô lập cũng có mặt trái. Paper "Inherited Goal Drift" (qua search) cho thấy model vốn bền như Qwen3-235B và Gemini-2.5-Flash **kế thừa** quỹ đạo drift khi được điều kiện hoá bằng trajectory đã lệch của một agent yếu hơn [43]. **Nhận định:** đây là lý do không nên nạp nguyên transcript của subagent vào context lead. Nhưng chỉ nhận bản tóm tắt thì chấp nhận mất chi tiết ("game of telephone"); lời giải trung gian là ghi artifact ra file rồi trả tham chiếu [8].

**Nén có kiểm soát.** Claude Code "clears older tool outputs first, then summarizes the conversation if needed" và cho phép định hướng bản tóm tắt bằng `/compact focus on …` [33]. Anthropic gọi tool result clearing là cách "safest lightest touch" [10]. API context editing xoá tool result cũ ở phía server. Đổi lại, nó làm mất cache tại điểm xoá, nên docs khuyên dùng `clear_at_least` để cắt một lần đủ lớn [35]. Trên eval nội bộ của Anthropic, context editing cộng memory tool cải thiện **39%** so với baseline (riêng context editing **29%**), và giảm **84%** token trong một workflow web search 100 lượt; đây là vendor tự báo cáo [44]. Với Sonnet 4.5, hiện tượng "context anxiety" (model kết thúc sớm vì tưởng sắp hết context) mạnh tới mức phải reset context kèm handoff có cấu trúc thay vì chỉ compaction; Opus 4.5 "largely removed that behavior", nên tác giả bỏ hẳn context reset khỏi harness [17].

**Kiểm hoàn thành bằng cơ chế khác, và đặt giới hạn cứng.** Anthropic quan sát thấy agent "declaring victory early" và đánh dấu xong khi chưa test end-to-end [40]. Khi tự chấm, agent "confidently praising the work—even when… the quality is obviously mediocre"; ngay cả evaluator cũng từng nhận ra lỗi thật rồi "talk itself into deciding they weren't a big deal and approve the work anyway". Họ khắc phục bằng một evaluator tách riêng, được chỉnh cho hoài nghi, kiểm theo "sprint contract" thống nhất từ trước [17]. Ở lớp cứng, harness đặt `maxTurns`, độ sâu lồng, số subagent đồng thời và `max_budget_usd` [3][22]. Lý do được minh hoạ bằng nghiên cứu IAL-Scan (qua search): quét **6.549** repo agent, xác nhận **68** lỗi lặp vô hạn ở 47 dự án, nguyên nhân gốc là đường lặp "not covered by a strong bound" [45]. Trong hệ Research của Anthropic, lead dùng extended thinking để lập plan và tổng hợp kết quả từng đợt rồi quyết định spawn thêm hay dừng; subagent dùng interleaved thinking sau mỗi tool result để "evaluate quality, identify gaps, and refine their next query" [8]. Think tool từng có số liệu τ-bench, nhưng bản cập nhật 2025-12-15 khuyên dùng extended thinking thay thế [46].

Bảng dưới gom các kỹ thuật trên thành checklist thực hành, xếp theo thứ tự nên áp dụng.

| # | Kỹ thuật | Làm cụ thể ở mức API/harness | Bằng chứng và mức tin |
|---|---|---|---|
| 1 | Neo mục tiêu trong prefix bất biến | task gốc là tin user đầu tiên; system prompt gọi nó là "primary goal"; không sửa tools, system hay message cũ | cơ chế từ docs [15][16]; chưa có số đo riêng |
| 2 | Plan và quy tắc nằm ngoài message history | plan vào memory/file; CLAUDE.md và plan file được tái chèn sau compaction | vendor docs [8][9]; định tính |
| 3 | Nhắc lại task và plan ở cuối context mỗi lượt | append một tin tạm hoặc mid-conversation `system`/reminder; không lưu vào thread nếu chỉ dùng một lần | Magentic-One [7]; Manus (qua search) [34]; gián tiếp từ U-curve [37] |
| 4 | Ledger có cấu trúc mỗi vòng | JSON bắt buộc: xong chưa / lặp không / tiến triển không / ai tiếp / chỉ dẫn | −31% GAIA khi bỏ (gộp với các thành phần khác) [12] |
| 5 | Đếm đình trệ rồi replan và reset context | replan khi bộ đếm chạm 3 (mặc định Magentic-One); phân tích nguyên nhân rồi lập plan mới, xoá thread | như trên [7][12] |
| 6 | Cô lập context subagent | prompt giao việc tự đủ; tin cuối 1–2k token; artifact ra file và trả tham chiếu | khuếch đại lỗi 4,4× vs 17,2× (qua search) [13] |
| 7 | Không nạp nguyên trajectory lệch | chỉ lấy tin cuối hoặc output có cấu trúc, không lấy `full_history` khi không cần | inherited drift (qua search) [43] |
| 8 | Nén có kiểm soát | xoá tool result cũ trước, tóm tắt có định hướng sau, cắt một lần đủ lớn | +39%, −84% token (vendor, eval nội bộ) [44] |
| 9 | Tiêu chí hoàn thành viết trước, kiểm bởi cơ chế khác | feature list JSON `passes`, test end-to-end, evaluator hoài nghi | định tính [40][17] |
| 10 | Giới hạn cứng | max turns, độ sâu, số subagent, ngân sách tiền và token | 68 lỗi lặp vô hạn do thiếu bound (qua search) [45] |
| 11 | Quy tắc phân bổ công sức trong prompt lead | số subagent và tool call theo độ khó; tối đa bao nhiêu | chống lỗi "50 subagents" [8] |
| 12 | Bước suy luận sau mỗi tool result và mỗi đợt kết quả | extended/interleaved thinking đối chiếu với plan và brief | định tính [8][46] |

## Multi-agent thắng ở việc song song hoá được, thua ở việc tuần tự, và đắt hơn nhiều

Bằng chứng mạnh nhất cho multi-agent đến từ nhà cung cấp. Hệ Research của Anthropic (lead Opus 4, subagent Sonnet 4) "outperformed single-agent Claude Opus 4 by **90.2%**" trên eval research nội bộ không công bố. Cũng theo họ, token usage một mình giải thích **80%** phương sai hiệu năng trên BrowseComp, và multi-agent tốn khoảng **15×** token so với chat (agent đơn khoảng 4×) [8]. Chính Anthropic nói coding "involve fewer truly parallelizable tasks than research", và các domain cần mọi agent chia sẻ context hoặc phụ thuộc chặt là "not a good fit for multi-agent systems today" [8]. Ví dụ của LangChain ("Subagents processes 67% fewer tokens overall due to context isolation") là kịch bản do họ tự dựng để minh hoạ, không phải phép đo thực nghiệm [47].

Các nghiên cứu độc lập 2025–2026 cho bức tranh hẹp hơn. Proxy chặn arXiv nên mọi con số ở bảng dưới chỉ đọc được qua kết quả search; hướng kết luận thống nhất giữa các nhóm, nhưng con số cần đối chiếu với bản gốc.

| Nghiên cứu | Thiết kế | Kết quả chính | Mức kiểm chứng |
|---|---|---|---|
| Kim và cs., Google Research/DeepMind/MIT [13] | 180 cấu hình, 5 kiến trúc, 3 họ LLM, 4 benchmark, budget chuẩn hoá | centralized **+80,9%** trên tác vụ song song hoá được; mọi biến thể multi-agent **−39–70%** trên suy luận tuần tự; khi single-agent đã đạt trên ~**45%** thì phối hợp lợi ít hoặc hại | qua search (abstract) |
| Gao và cs., UIUC [48] | nhiều ứng dụng agentic | lợi thế MAS giảm khi LLM mạnh lên; cascade SAS/MAS tăng độ chính xác 1,1–12%, giảm chi phí tới 20% | qua search |
| Tran & Kiela [49] | multi-hop QA, budget thinking token bằng nhau | single-agent chính xác hơn và rẻ hơn; lợi thế MAS "better explained by unaccounted computation and context effects" | qua search |
| Salesforce AI Research [50] | MAS tự sinh so với CoT + self-consistency | MAS tự động luôn thua dù đắt tới ~10×; MAS thiết kế tay thắng trên dataset có phân rã tường minh | qua search |
| Zhang và cs. [51] | 5 phương pháp debate, 9 benchmark, 4 model | không phương pháp nào thắng CoT ở quá 20% trong 36 kịch bản; self-consistency thường tốt nhất | qua search |

Lỗi của hệ multi-agent cũng có taxonomy thực nghiệm. MAST (UC Berkeley, NeurIPS 2025) xây từ **150** trace một bộ **14** failure mode chia ba nhóm: thiết kế hệ thống/đặc tả, lệch pha giữa các agent, và kiểm chứng. Độ đồng thuận giữa người gán nhãn đạt κ = **0,88**. Theo Figure 1 bản gốc (qua search), ba nhóm chiếm lần lượt **44,2% / 32,3% / 23,5%** [52]. Kết luận của tác giả là thất bại "stem mainly from system design and inter-agent misalignment", chứ không chỉ do model yếu [52]. Quy lỗi cũng khó: trên benchmark Who&When gồm log từ 127 hệ multi-agent, phương pháp tốt nhất chỉ xác định đúng agent gây lỗi **53,5%** và bước gây lỗi **14,2%** (qua search) [53]. **Nhận định:** các lỗi trong brief ánh xạ khá gọn vào các nhóm của MAST. Lặp vô hạn ứng với lặp bước, goal drift với vi phạm đặc tả, mất thông tin khi tóm tắt với lệch pha giữa các agent, và kết thúc sớm với nhóm kiểm chứng. Ba nhóm này cũng là đích nhắm của các kỹ thuật 4, 5, 6 và 9 ở checklist trên.

## Các nguồn bất đồng ở đâu

Bất đồng lớn nhất là có nên chia việc cho nhiều agent hay không. Walden Yan (Cognition, 06/2025, qua search) phản đối: hành động mang "quyết định ngầm", nên các subagent song song làm ra phần việc không khớp nhau, như ví dụ clone Flappy Bird với phong cách đồ hoạ lệch nhau. Ông khuyên dùng agent đơn luồng với context liên tục [54]. Anthropic đứng phía ngược lại với con số +90,2% [8]. Đến 04/2026 (qua search), Cognition chấp nhận một lớp thiết kế: "one main loop carries state, subagents are stateless workers with narrow scope", với điều kiện việc ghi (writes) vẫn đơn luồng. Ông vẫn cho rằng để agent ngang hàng chia sẻ memory là nơi "coherence falls apart" [55]. **Nhận định:** hai phía đã hội tụ về đúng mô hình orchestrator–worker cho tác vụ **đọc**, thứ Anthropic cũng tự giới hạn khi nói coding ít song song hoá được. Bất đồng còn lại chỉ là có cho subagent ghi hay ra quyết định song song hay không. Nghiên cứu độc lập nghiêng về phía thận trọng.

Bất đồng thứ hai là lợi ích thật của multi-agent lớn đến đâu. Số của vendor không chuẩn hoá theo compute, trong khi chính Anthropic báo token giải thích 80% phương sai [8]. Các paper so sánh ở cùng budget (Tran & Kiela, Salesforce, qua search) thấy lợi thế co lại hoặc biến mất [49][50]. **Nhận định:** nên tin rằng lợi thế có thật ở tác vụ tìm kiếm theo bề rộng, và coi con số 90,2% là cận trên chưa trừ hiệu ứng chi nhiều token hơn khoảng 15×.

Bất đồng thứ ba là có nên dùng todo list hay recitation do model tự làm. Manus (qua snippet search) coi `todo.md` là cách chống lạc hướng [34]. Docs Claude Code nay tắt todo tool mặc định với model mới [41]. Thông tin rằng Manus sau đó bỏ cách này vì tốn khoảng một phần ba số action chỉ có từ snippet của nguồn thứ cấp (xem phần cuối). **Nhận định:** hai phía không thật sự mâu thuẫn. Nhắc mục tiêu ở cuối context vẫn đúng, chỉ là người làm việc đó đang chuyển từ model sang harness.

Ngoài ra còn vài chỗ lệch nhỏ về số. Bài think tool ghi trong lời văn 0,570 so với 0,370 trên τ-bench airline, nhưng bảng lại ghi 0,584 so với 0,332 [46]. MAST có hai bộ tỉ lệ nhóm, xem phần cuối.

## Kết luận và hàm ý

Điều rút ra quan trọng nhất là "giữ đúng mục tiêu" không phải năng lực riêng của model mà là bài toán **bố trí context** của harness. Ba quyết định nằm hoàn toàn ngoài model: cái gì nằm trong prefix bất biến, cái gì được nhắc lại ở cuối mỗi lượt, và cái gì được đẩy ra file hay sang context của subagent. Cùng một model có thể bám mục tiêu tốt hay kém tuỳ ba quyết định này (Magentic-One: −31% khi bỏ ledger). Prompt caching tạo thêm một ràng buộc: prefix phải ổn định, nên trạng thái động buộc phải đi vào cuối context, và cũng chính ở đó attention tốt nhất. Đánh đổi cốt lõi không có lời giải miễn phí. Cô lập context giữ lead sạch nhưng gây mất chi tiết; đưa nhiều trace về lead thì giữ chi tiết nhưng làm context dài ra và có nguy cơ kế thừa drift. Ghi artifact ra file và trả tham chiếu là điểm cân bằng mà Anthropic Research chọn [8].

Với mục đích tự thiết kế hoặc đánh giá một hệ orchestrator–subagent, thứ tự hợp lý là: bắt đầu bằng single agent kèm harness tốt (các mục 1–3 và 8–10 của checklist). Chỉ thêm orchestrator–worker khi tác vụ khó với agent đơn **và** tách được thành các nhánh đọc độc lập. Khi thêm, đầu tư vào prompt giao việc (bảng tám thành phần), một ledger kiểm tiến độ bắt buộc mỗi vòng, và một bước kiểm hoàn thành không do chính generator làm. Khi đánh giá một hệ có sẵn, câu hỏi nên đặt là: task gốc nằm ở đâu trong request lượt N, có bị compaction chạm tới không, ai quyết định "xong", và hệ được so với single-agent ở cùng budget token hay chưa. Xu hướng 2026 cho thấy phần "giàn giáo" như todo list và reset context giảm dần khi model mạnh lên. Nhưng nhu cầu kiểm soát context và kiểm chứng độc lập không giảm: model mới thậm chí giao việc hăng hơn, đến mức harness phải kìm lại [3].

## Chưa kiểm chứng được

- **Nguyên văn system prompt, tool description của Agent tool và nội dung `<system-reminder>` của Claude Code** không có trong docs chính thức; chỉ có bản leak bậc 3, không dùng. Định dạng JSON đầy đủ của `tool_result` mà Claude Code chèn cho Agent tool cũng không được công bố, ngoài các chi tiết "final message", `agentId` và cờ partial. Ví dụ turn-by-turn trong báo cáo vì vậy chỉ là minh hoạ.
- **Paper bị proxy chặn, số liệu chỉ có qua snippet search:** MAST, Who&When, Goal Drift, Inherited Goal Drift, Lost in the Middle, Lost in Multi-Turn, IAL-Scan, Kim và cs., UIUC, Tran & Kiela, Salesforce, Multi-agent debate. Chưa có bảng số theo từng benchmark/model, và chưa xác nhận +80,9% và −39–70% của Kim và cs. ứng với benchmark nào. Truy vấn đã thử: "Towards a Science of Scaling Agent Systems Google 180 configurations results", "Kim 2025 scaling agent systems PlanCraft sequential multi-agent degraded 39% 70% every variant".
- **MAST:** hai bộ tỉ lệ nhóm khác nhau, 44,2/32,3/23,5 (Figure 1 bản gốc, qua search) và 41,8/36,9/21,3 (nguồn thứ cấp) [52]; số trace phát hành lệch giữa "over 1K" trên repo và khoảng 1.600 trong paper [56]. Tỉ lệ từng mode (lặp bước ~15,7%, vi phạm đặc tả ~11,8%, kết thúc sớm 6,2%) chủ yếu thấy ở nguồn thứ cấp. Cũng chưa có số liệu cải thiện của các case study can thiệp.
- **Manus:** mọi trích dẫn chỉ có qua snippet search vì manus.im bị chặn, và ngày đăng 2025-07 chưa xác minh trực tiếp [34]. Thông tin "khoảng 1/3 số action dùng để cập nhật todo list, sau đó chuyển sang planner agent" chỉ thấy qua snippet trỏ tới bài của Lance Martin [57], độ tin thấp.
- **Bài gốc của Cognition (2025, 2026) và LangChain "How and when to build multi-agent systems"** không mở được; trích dẫn lấy từ đoạn trích search. Phân biệt tác vụ đọc với tác vụ ghi của LangChain chỉ có qua bản tóm tắt bậc 3 nên không trích làm bằng chứng.
- **Không có nghiên cứu độc lập** tái lập con số +90,2% của Anthropic; không có benchmark đo trực tiếp có/không recitation hay todo đối với goal drift ở orchestrator; không có số định lượng về mất thông tin khi subagent tóm tắt kết quả, hay về các subagent làm trùng việc nhau. Paper Magentic-One không tách đóng góp của từng ledger và của stall counter.
- **Chưa đọc:** OpenAI "A practical guide to building agents" (cdn.openai.com bị chặn); cách Microsoft Agent Framework, bản kế nhiệm AutoGen, cài orchestration kiểu Magentic; source `flows/llm_flows` của ADK cho cơ chế trả kết quả của `single_turn`; hạ tầng production của hệ Research Anthropic (`run_blocking_subagent` có phải tên tool thật hay chỉ là tên trong cookbook).
- **Paper ACE về "context collapse"** (arXiv 2510.04618) và các con số đi kèm chỉ thấy qua bài báo thứ cấp; không dùng.

## Nguồn

[1] Using the Messages API — Anthropic, Claude Platform Docs, truy cập 2026-10-19 (bậc 1). https://platform.claude.com/docs/en/build-with-claude/working-with-messages
[2] Handle tool calls — Anthropic, Claude Platform Docs, truy cập 2026-10-19 (bậc 1). https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls
[3] Subagents in the SDK — Anthropic, Claude Agent SDK Docs, truy cập 2026-10-19 (bậc 1). https://code.claude.com/docs/en/agent-sdk/subagents
[4] src/agents/agent.py (docstring `as_tool`) — OpenAI, openai-agents-python, commit mới nhất 2026-10-17 (bậc 1, source code). https://github.com/openai/openai-agents-python/blob/main/src/agents/agent.py
[5] Multi-agent: Subagents (subagents.mdx) — LangChain docs, commit mới nhất 2026-10-18 (bậc 1). https://github.com/langchain-ai/docs/blob/main/src/oss/langchain/multi-agent/subagents.mdx
[6] src/google/adk/tools/agent_tool.py — Google, adk-python, commit mới nhất 2026-10-18 (bậc 1, source code). https://github.com/google/adk-python/blob/main/src/google/adk/tools/agent_tool.py
[7] _magentic_one_orchestrator.py — Microsoft, AutoGen (autogen-agentchat), commit mới nhất 2026-10-16 (bậc 1, source code). https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_magentic_one/_magentic_one_orchestrator.py
[8] How we built our multi-agent research system — Anthropic Engineering, 2025-06-13 (bậc 1; số liệu hiệu năng là vendor tự báo cáo trên eval nội bộ). https://www.anthropic.com/engineering/multi-agent-research-system
[9] Explore the context window (What survives compaction) — Anthropic, Claude Code Docs, truy cập 2026-10 (bậc 1). https://code.claude.com/docs/en/context-window
[10] Effective context engineering for AI agents — Anthropic Engineering, 2025-09-29 (bậc 1). https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
[11] _prompts.py (Magentic-One) — Microsoft, AutoGen, commit mới nhất 2026-10-16 (bậc 1, source code). https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_magentic_one/_prompts.py
[12] Magentic-One: A Generalist Multi-Agent System for Solving Complex Tasks — Microsoft Research, 2024-11, arXiv 2411.04468 (bậc 1; đọc trực tiếp bản PDF trên microsoft.com). https://www.microsoft.com/en-us/research/wp-content/uploads/2024/11/MagenticOne.pdf
[13] Towards a Science of Scaling Agent Systems — Kim, Gu, … Liu (Google Research/Google DeepMind/MIT), arXiv 2512.08296, 2025-12-09; kèm blog Google Research 2026-01-28 (bậc 1; [qua search], chưa mở được toàn văn). https://arxiv.org/abs/2512.08296 · https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/
[14] docs/handoffs.md — OpenAI, openai-agents-python, commit mới nhất 2026-10-17 (bậc 1). https://github.com/openai/openai-agents-python/blob/main/docs/handoffs.md
[15] research_lead_agent.md (prompt lead agent) — Anthropic, claude-cookbooks, không rõ ngày commit, công bố kèm bài 2025-06 (bậc 1). https://github.com/anthropics/claude-cookbooks/blob/main/patterns/agents/prompts/research_lead_agent.md
[16] Prompt caching — Anthropic, Claude Platform Docs, truy cập 2026-10-19 (bậc 1). https://platform.claude.com/docs/en/build-with-claude/prompt-caching
[17] Harness design for long-running application development — Prithvi Rajasekaran, Anthropic Engineering, 2026-03-24 (bậc 1). https://www.anthropic.com/engineering/harness-design-long-running-apps
[18] Building effective agents — Anthropic Engineering, 2024-12-19 (bậc 1). https://www.anthropic.com/engineering/building-effective-agents
[19] docs/multi_agent.md — OpenAI, openai-agents-python, commit mới nhất 2026-10-17 (bậc 1). https://github.com/openai/openai-agents-python/blob/main/docs/multi_agent.md
[20] docs/workflows/patterns.md — Google, adk-docs, commit mới nhất 2026-10-16 (bậc 1). https://github.com/google/adk-docs/blob/main/docs/workflows/patterns.md
[21] microsoft/autogen README — Microsoft, commit mới nhất 2026-10-16 (bậc 1). https://github.com/microsoft/autogen
[22] Create custom subagents — Anthropic, Claude Code Docs, truy cập 2026-10-19 (bậc 1). https://code.claude.com/docs/en/sub-agents
[23] langgraph-supervisor-py (README, supervisor.py, handoff.py) — LangChain, commit mới nhất 2026-07-14 (bậc 1, source code). https://github.com/langchain-ai/langgraph-supervisor-py
[24] src/google/adk/tools/transfer_to_agent_tool.py — Google, adk-python, commit mới nhất 2026-10-18 (bậc 1, source code). https://github.com/google/adk-python/blob/main/src/google/adk/tools/transfer_to_agent_tool.py
[25] research_subagent.md (prompt subagent) — Anthropic, claude-cookbooks, không rõ ngày commit (bậc 1). https://github.com/anthropics/claude-cookbooks/blob/main/patterns/agents/prompts/research_subagent.md
[26] docs/tools.md — OpenAI, openai-agents-python, commit mới nhất 2026-10-17 (bậc 1). https://github.com/openai/openai-agents-python/blob/main/docs/tools.md
[27] docs/running_agents.md — OpenAI, openai-agents-python, commit mới nhất 2026-10-17 (bậc 1). https://github.com/openai/openai-agents-python/blob/main/docs/running_agents.md
[28] src/agents/run_internal/turn_resolution.py — OpenAI, openai-agents-python, commit mới nhất 2026-10-17 (bậc 1, source code). https://github.com/openai/openai-agents-python/blob/main/src/agents/run_internal/turn_resolution.py
[29] docs/workflows/collaboration.md (ADK 2.0 collaboration modes) — Google, adk-docs, commit mới nhất 2026-10-16 (bậc 1). https://github.com/google/adk-docs/blob/main/docs/workflows/collaboration.md
[30] Conversation state — OpenAI API Docs, không rõ ngày (bậc 1; [qua search], trang bị chặn). https://developers.openai.com/api/docs/guides/conversation-state
[31] Define tools — Anthropic, Claude Platform Docs, truy cập 2026-10-19 (bậc 1). https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
[32] Glossary — Anthropic, Claude Code Docs, truy cập 2026-10 (bậc 1). https://code.claude.com/docs/en/glossary
[33] How Claude Code works — Anthropic, Claude Code Docs, truy cập 2026-10 (bậc 1). https://code.claude.com/docs/en/how-claude-code-works
[34] Context Engineering for AI Agents: Lessons from Building Manus — Yichao "Peak" Ji, Manus, 2025-07 (ngày chưa xác minh) (bậc 1; [qua search], chỉ đọc qua snippet, trang bị chặn). https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus
[35] Context editing — Anthropic, Claude Platform Docs, truy cập 2026-10-19 (bậc 1). https://platform.claude.com/docs/en/build-with-claude/context-editing
[36] Compaction overview — Anthropic, Claude Platform Docs, truy cập 2026-10-19 (bậc 1). https://platform.claude.com/docs/en/build-with-claude/compaction
[37] Lost in the Middle: How Language Models Use Long Contexts — Liu và cs., arXiv 2307.03172, 2023-07; TACL 2024 (bậc 1; [qua search]). https://arxiv.org/abs/2307.03172
[38] Evaluating Goal Drift in Language Model Agents — Arike, Donoway, Bartsch, Hobbhahn, arXiv 2505.02709, 2025-05; AIES 2025 (bậc 1; [qua search]). https://arxiv.org/abs/2505.02709
[39] LLMs Get Lost In Multi-Turn Conversation — Laban, Hayashi và cs. (Microsoft/Salesforce), arXiv 2505.06120, 2025-05 (bậc 1; [qua search]). https://arxiv.org/abs/2505.06120
[40] Effective harnesses for long-running agents — Anthropic Engineering, 2025-11-26 (bậc 1). https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
[41] Track todos — Anthropic, Claude Agent SDK Docs, truy cập 2026-10 (bậc 1). https://code.claude.com/docs/en/agent-sdk/todo-tracking
[42] _magentic_one_group_chat.py — Microsoft, AutoGen, commit mới nhất 2026-10-16 (bậc 1, source code). https://github.com/microsoft/autogen/blob/main/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_magentic_one/_magentic_one_group_chat.py
[43] Inherited Goal Drift: Contextual Pressure Can Undermine Agentic Goals — Menon và cs., arXiv 2603.03258, 2026-03; ICLR 2026 (bậc 1; [qua search]). https://arxiv.org/html/2603.03258
[44] Managing context on the Claude Developer Platform — Anthropic (claude.com blog), 2025-09-29 (bậc 1; số liệu eval nội bộ của vendor). https://claude.com/blog/context-management
[45] When Agents Do Not Stop: Uncovering Infinite Agentic Loops in LLM Agents — arXiv 2607.01641, 2026-07 (bậc 1; [qua search]). https://arxiv.org/abs/2607.01641
[46] The "think" tool: Enabling Claude to stop and think — Anthropic Engineering, 2025-03-20, cập nhật 2025-12-15 (bậc 1). https://www.anthropic.com/engineering/claude-think-tool
[47] Multi-agent (index.mdx) — LangChain docs, commit mới nhất 2026-10-18 (bậc 1; bảng so sánh là ví dụ minh hoạ do LangChain tự dựng). https://github.com/langchain-ai/docs/blob/main/src/oss/langchain/multi-agent/index.mdx
[48] Single-agent or Multi-agent Systems? Why Not Both? — Gao, Li, Liu, Yu, Wang, Lin, Lai (UIUC), arXiv 2505.18286, 2025-05-23 (bậc 1; [qua search]). https://arxiv.org/abs/2505.18286
[49] Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets — Dat Tran, Douwe Kiela, arXiv 2604.02460, 2026-04 (bậc 1; [qua search]). https://arxiv.org/html/2604.02460v1
[50] The Illusion of Multi-Agent Advantage — Jwalapuram, Lin và cs. (Salesforce AI Research), arXiv 2606.13003, 2026-06-11 (bậc 1; [qua search]). https://arxiv.org/abs/2606.13003
[51] If Multi-Agent Debate is the Answer, What is the Question? (Stop Overvaluing Multi-Agent Debate) — Zhang và cs., arXiv 2502.08788, 2025-02 (bậc 1; [qua search]). https://arxiv.org/html/2502.08788v1
[52] Why Do Multi-Agent LLM Systems Fail? — Cemri, Pan, Yang và cs. (UC Berkeley), arXiv 2503.13657, v1 2025-03, v3 2025-10-26; NeurIPS 2025 Datasets & Benchmarks (bậc 1; [qua search]). https://arxiv.org/abs/2503.13657
[53] Which Agent Causes Task Failures and When? — Zhang và cs., arXiv 2505.00212, 2025-05; ICML 2025 (bậc 1; [qua search]). https://arxiv.org/pdf/2505.00212
[54] Don't Build Multi-Agents — Walden Yan, Cognition, 2025-06 (bậc 1, quan điểm của vendor; [qua search], trang bị chặn). https://cognition.ai/blog/dont-build-multi-agents
[55] Multi-Agents: What's Actually Working — Walden Yan, Cognition, 2026-04-22 (bậc 1, quan điểm của vendor; [qua search], trang bị chặn). https://cognition.com/blog/multi-agents-working
[56] multi-agent-systems-failure-taxonomy/MAST (repo) — UC Berkeley, không rõ ngày (bậc 1; đã mở trang). https://github.com/multi-agent-systems-failure-taxonomy/MAST
[57] Context Engineering in Manus — Lance Martin, 2025-10-15 (bậc 2; [qua search], trang bị chặn, chỉ làm manh mối). https://rlancemartin.github.io/2025/10/15/manus/
