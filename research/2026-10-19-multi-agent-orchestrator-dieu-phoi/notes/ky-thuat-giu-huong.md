# Kỹ thuật giữ orchestrator bám mục tiêu gốc qua nhiều lượt gọi (thực hành & case study)

Ghi chú chung về truy cập nguồn: trong phiên này proxy chặn các domain arxiv.org, manus.im, cognition.ai, blog.langchain.com, developers.openai.com, rlancemartin.github.io, research.trychroma.com, venturebeat.com, marktechpost.com. Các nguồn đọc trực tiếp được: anthropic.com/engineering, claude.com/blog, code.claude.com/docs, bản PDF Magentic-One trên microsoft.com. Phát hiện nào chỉ dựa vào snippet search hoặc trí nhớ của model được đánh dấu rõ, cần verifier kiểm tra lại.

## 4a. Giữ task gốc và plan "trước mắt" model: todo list, recitation, system reminder

### Kết luận ngắn
Model stateless nên cách giữ hướng cơ bản nhất là harness chèn lại (hoặc bắt model tự viết lại) mục tiêu/plan vào context ở mỗi lượt, đặt gần cuối context nơi attention mạnh. Claude Code làm việc này bằng todo tool + system reminder + tái chèn file từ đĩa sau compaction; Manus bằng `todo.md` "recitation". Mức chắc chắn: **cao** về cơ chế (docs chính thức), **trung bình–thấp** về hiệu quả định lượng (không có benchmark công bố; chính Anthropic và Manus đều đã giảm dùng todo list với model mới).

### Phát hiện có nguồn
- Trong Claude Code, khi có task-tracking tools, "Claude keeps a written todo list, updating each item's status as it works"; vòng đời `pending` → `in_progress` → `completed` (hoặc `deleted`); Claude tạo todo cho "Complex multi-step tasks requiring three or more distinct actions", danh sách người dùng đưa, thao tác dài, hoặc khi được yêu cầu; bỏ qua với yêu cầu ngắn/một bước — [Track todos (Agent SDK)](https://code.claude.com/docs/en/agent-sdk/todo-tracking) (bậc 1, truy cập 2026-10).
- Cùng trang: các tool `TodoWrite`/`TaskCreate`/`TaskUpdate`/... chỉ bật mặc định trên "Claude Opus 4.7, Claude Sonnet 4.6, Claude Haiku 4.5, and earlier models"; "Newer models track multi-step work without a written todo list" (áp dụng từ Claude Code v2.1.268) — [Track todos](https://code.claude.com/docs/en/agent-sdk/todo-tracking) (bậc 1, 2026-10). → Bằng chứng nhà cung cấp coi todo list là "giàn giáo" cho model cũ, không còn cần với model mới.
- System reminder = "A message that Claude Code, as the harness, adds to the conversation to give Claude context… inserts them as a session runs, for example when the session starts, when a hook returns text, or when a file changes on disk"; CLAUDE.md, output style, text hook trả về qua `additionalContext` đều đến Claude dưới dạng system reminder — [Claude Code Glossary](https://code.claude.com/docs/en/glossary) (bậc 1, truy cập 2026-10).
- Claude Code tự thêm vào hội thoại: CLAUDE.md, output style, "A note when a file Claude read earlier changes on disk", dòng attribution commit/PR — [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works) (bậc 1, truy cập 2026-10).
- Docs thừa nhận rủi ro trôi: "Claude compacts automatically, but instructions from early in the conversation can get lost. Put persistent rules in CLAUDE.md" — [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works) (bậc 1).
- Sau compaction, Claude Code **tái chèn từ đĩa**: system prompt vẫn áp dụng; project-root CLAUDE.md và rules không scope "Re-injected from disk"; auto memory re-inject; "The plan Claude wrote in plan mode | Re-injected from disk"; đọc lại tối đa 5 file sửa gần nhất; skill đã gọi re-inject (≤5.000 token/skill, ≤25.000 tổng); nhắc Claude các background subagent/command còn chạy "so it doesn't start a duplicate"; SessionStart hook với source `compact` được chạy lại — [Explore the context window – What survives compaction](https://code.claude.com/docs/en/context-window) (bậc 1, truy cập 2026-10).
- Manus (bài gốc của Yichao "Peak" Ji, 07/2025): agent liên tục viết lại `todo.md`; "reciting its objectives into the end of the context" đẩy plan toàn cục vào vùng attention gần, tránh "lost-in-the-middle" và giảm goal misalignment; một task Manus trung bình ~50 tool call — [Context Engineering for AI Agents: Lessons from Building Manus](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) (bậc 1, 2025-07). **Lưu ý:** không mở được trang gốc (proxy chặn); nội dung xác nhận qua snippet search của các bài tóm tắt (tianpan.co 2026-03, marktechpost 2025-07-22) và trí nhớ của model → verifier nên kiểm tra trích dẫn.
- Manus sau đó bỏ cách này: theo snippet search, "roughly one-third of all actions were spent updating the todo list", nên chuyển sang một planner agent riêng gọi executor sub-agent — nguồn gốc được cho là webinar Lance Martin × Peak Ji, [Context Engineering in Manus](https://rlancemartin.github.io/2025/10/15/manus/) (bậc 2, 2025-10-15). **Không mở được trang**, chỉ thấy qua snippet → độ tin thấp–trung bình.

### Nhận định
- **Nhận định:** cơ chế chung là "đặt lại mục tiêu vào recency zone". Có ba cách: (1) model tự recite (todo tool, `todo.md`) — tốn tool call/token; (2) harness tự chèn (system reminder, re-inject CLAUDE.md/plan sau compaction) — không tốn lượt của model; (3) đưa plan ra một agent/file riêng (planner agent của Manus, plan file của plan mode).
- **Nhận định:** xu hướng 2025→2026 là chuyển gánh "nhớ plan" từ model sang harness/file, vì model mới tự giữ được multi-step tốt hơn và recitation tốn kém (Manus: ~1/3 action).

### Khoảng trống
- Không tìm được benchmark công khai đo trực tiếp "có todo/recitation vs không" cho orchestrator.
- Nội dung gốc Manus và tỉ lệ "1/3 action" chưa đọc trực tiếp được.

## 4b. Task ledger + progress ledger, phát hiện đình trệ và replan (Magentic-One)

### Kết luận ngắn
Magentic-One là case study rõ nhất có ablation: Orchestrator giữ hai "ledger" (sổ cái) dạng text, cập nhật mỗi vòng; bỏ ledger thì hiệu năng GAIA giảm 31%. Mức chắc chắn: **cao** (paper gốc, đọc trực tiếp PDF).

### Phát hiện có nguồn
- Hai vòng lặp: "the outer loop maintains the task ledger, which contains the overall plan, while the inner loop maintains the progress ledger, which directs and evaluates the individual steps" — [Magentic-One: A Generalist Multi-Agent System for Solving Complex Tasks (PDF)](https://www.microsoft.com/en-us/research/wp-content/uploads/2024/11/MagenticOne.pdf) (bậc 1, Microsoft Research, 2024-11; arXiv 2411.04468).
- Task ledger là "short-term memory for the duration of the task", gồm: "given or verified facts, facts to look up (e.g., via web search), facts to derive (e.g., programmatically, or via reasoning), and educated guesses", sau đó mới lập plan từng bước gán cho agent dựa trên mô tả từng thành viên; plan "serves more as a hint… neither the Orchestrator nor the other agents are required to follow it exactly" — [Magentic-One PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2024/11/MagenticOne.pdf) (bậc 1, 2024-11).
- Mỗi lần cập nhật plan, "we force all agents to clear their contexts and reset their states" — cùng nguồn.
- Progress ledger: mỗi vòng inner loop Orchestrator trả lời 5 câu: "Is the request fully satisfied (i.e., task complete)? / Is the team looping or repeating itself? / Is forward progress being made? / Which agent should speak next? / What instruction or question should be asked of this team member?", xét cả task ledger và context hội thoại hiện tại — cùng nguồn.
- Stall counter: tăng khi phát hiện loop hoặc không tiến triển; ngưỡng "≤ 2 in our experiments"; vượt ngưỡng thì thoát inner loop, làm bước "reflection and self-refinement" (cái gì sai, học được gì mới, làm gì khác), cập nhật task ledger, sửa plan, bắt đầu inner loop mới. Kết thúc khi task xong hoặc chạm điều kiện cấu hình (số lần thử tối đa, thời gian tối đa); cuối cùng "reviews the full transcript, along with the ledger, and reports either a final answer, or its best educated guess" — cùng nguồn.
- Ablation trên GAIA validation (GPT-4o): thay Orchestrator bằng GroupChat-style chỉ chọn người nói kế tiếp ("eliminating both ledgers, planning, progress tracking, loop detection, and explicit instructions") → "without the full ledgers, performance drops by 31%"; bỏ từng worker giảm 21% (Coder, Executor) đến 39% (FileSurfer) — cùng nguồn.
- Kết quả tổng: 38% GAIA, 32.8% WebArena, 27.7% AssistantBench (test set), "statistically competitive" với SOTA — cùng nguồn.

### Nhận định
- **Nhận định:** ledger là cách "ngoại hoá trạng thái" thành văn bản có cấu trúc mà orchestrator đọc lại mỗi lượt; câu hỏi "task đã xong chưa / có đang lặp không / có tiến triển không" chính là completion check + loop detection được ép thành bước bắt buộc mỗi vòng, không để model tự nhớ.
- **Nhận định:** reset context của worker sau mỗi replan là một dạng cô lập context (xem 4e) để plan cũ không "kéo" hành vi.

### Khoảng trống
- Paper không tách riêng đóng góp của progress ledger vs task ledger vs stall counter (ablation gộp "full ledgers").

## 4c. Lưu plan / ghi chú ra bộ nhớ ngoài (external memory, note-taking, scratchpad file)

### Kết luận ngắn
Các hệ chạy dài đều ghi plan/tiến độ ra ngoài context (memory, file, git) để sống sót qua truncation/compaction/reset; Anthropic có số liệu nội bộ cho memory tool + context editing. Mức chắc chắn: **cao** về thực hành, **trung bình** về số liệu (eval nội bộ của nhà cung cấp).

### Phát hiện có nguồn
- Anthropic Research: LeadResearcher lưu plan vào Memory vì "if the context window exceeds 200,000 tokens it will be truncated and it is important to retain the plan" — [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (bậc 1, 2025-06).
- Cùng bài: agent "summarize completed work phases and store essential information in external memory before proceeding to new tasks"; khi gần giới hạn context có thể "spawn fresh subagents with clean contexts while maintaining continuity through careful handoffs" — (bậc 1, 2025-06).
- Structured note-taking: "the agent regularly writes notes persisted to memory outside of the context window", ví dụ file `NOTES.md`; Claude chơi Pokémon giữ ghi chú kiểu "for the last 1,234 steps I've been training my Pokémon in Route 1, Pikachu has gained 8 levels toward the target of 10", sau context reset đọc lại notes và tiếp tục — [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (bậc 1, 2025-09-29).
- Memory tool: "store and consult information outside the context window through a file-based system"; eval agentic search nội bộ: memory tool + context editing "improved performance by 39% over baseline", context editing riêng "29%"; trong eval web search 100 lượt, context editing giúp hoàn thành workflow lẽ ra thất bại và "reducing token consumption by 84%" — [Managing context on the Claude Developer Platform](https://claude.com/blog/context-management) (bậc 1, 2025-09-29; số liệu nội bộ của Anthropic).
- Manus coi file system là "ultimate context": nén "restorable" (bỏ nội dung trang web nhưng giữ URL, bỏ nội dung file nhưng giữ path) — [Manus blog](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) (bậc 1, 2025-07). **Không mở được trang gốc**; theo trí nhớ model + snippet → cần kiểm tra.
- "Just-in-time context": agent giữ "lightweight identifiers (file paths, stored queries, web links, etc.)" và nạp dữ liệu khi cần — [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (bậc 1, 2025-09-29).

### Nhận định
- **Nhận định:** "giữ đúng mục tiêu" và "quản lý context" là một bài toán: plan và mục tiêu gốc phải nằm ở nơi không bị nén/cắt (system prompt, file re-inject, memory) chứ không chỉ trong message history.

### Khoảng trống
- Chưa có số liệu độc lập (ngoài nhà cung cấp) cho memory tool/note-taking.

## 4d. Compaction / summarization và rủi ro

### Kết luận ngắn
Compaction (tóm tắt lịch sử khi gần đầy context) là cơ chế mặc định của Claude Code/Agent SDK, nhưng tất cả nguồn chính thức đều cảnh báo nó làm mất chi tiết và chỉ dẫn sớm; biện pháp giảm rủi ro là xoá tool result trước, tóm tắt có hướng dẫn, và tái chèn các file quan trọng từ đĩa. Mức chắc chắn: **cao**.

### Phát hiện có nguồn
- Định nghĩa: compaction là "taking a conversation nearing the context window limit" và tóm tắt lại để khởi tạo context mới; Claude Code giữ "architectural decisions, unresolved bugs, and implementation details"; rủi ro: "overly aggressive compaction can result in the loss of subtle but critical context"; dạng nhẹ và an toàn nhất là "tool result clearing" — [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (bậc 1, 2025-09-29).
- Context rot: khi số token tăng, khả năng nhớ chính xác giảm; "Every new token introduced depletes this budget"; context là "finite resource with diminishing marginal returns" — cùng nguồn.
- Claude Code: "It clears older tool outputs first, then summarizes the conversation if needed. Your requests and key code snippets are preserved; detailed instructions from early in the conversation may be lost"; có thể điều khiển bằng mục "Compact Instructions" trong CLAUDE.md hoặc `/compact focus on ...`; nếu một output quá lớn khiến context đầy lại ngay, auto-compact dừng sau vài lần "instead of looping" — [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works) (bậc 1, truy cập 2026-10).
- Claude Code: path-scoped rules và nested CLAUDE.md nằm trong message history nên "compaction summarizes them away"; skill body bị cắt giữ phần đầu, nên "put the most important instructions near the top of SKILL.md" — [Explore the context window](https://code.claude.com/docs/en/context-window) (bậc 1).
- Agent SDK: compact "automatically summarizes previous messages when the context limit approaches" — [Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk) (bậc 1, 2025-09-29).
- Compaction vs context reset: với Sonnet 4.5, "context anxiety" (model kết thúc sớm khi tưởng sắp hết context) mạnh đến mức compaction không đủ, phải reset (agent mới + handoff có cấu trúc); Opus 4.5 gần như hết hiện tượng này nên bỏ reset — [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps) (bậc 1, 2026-03-24, Prithvi Rajasekaran).
- "Context collapse" (paper ACE, Stanford/SambaNova/UC Berkeley, arXiv 2510.04618, 10/2025): viết lại toàn bộ context mỗi bước làm nó co lại thành bản tóm tắt ngắn, mất chi tiết; "brevity bias" đẩy context về tóm tắt chung chung; ACE dùng cập nhật "delta" tăng dần (Generator–Reflector–Curator) — theo snippet search từ VentureBeat/altexsoft/Medium (bậc 2–3). **Không mở được paper**; con số cụ thể (vd context co từ ~18k xuống ~122 token) chưa xác minh → không dùng.
- OpenAI cookbook "Session memory" (Agents SDK): hai kỹ thuật trimming và summarization; theo snippet, tóm tắt giúp tránh để "stale earlier plans override the current request" và hạn chế "context poisoning" — [Session memory cookbook](https://developers.openai.com/cookbook/examples/agents_sdk/session_memory) (bậc 1). **Chỉ thấy snippet**, không đọc được trang.

### Nhận định
- **Nhận định:** rủi ro chính của compaction với bài toán "giữ mục tiêu" là chỉ dẫn sớm (chính là mục tiêu gốc và ràng buộc) bị tóm tắt mất → thực hành chuẩn là giữ mục tiêu ở chỗ không bị nén (system prompt, CLAUDE.md, plan file re-inject) và chỉ nén phần tool output.

### Khoảng trống
- Không có số liệu định lượng công khai về tỉ lệ mất thông tin do compaction trong orchestrator thật.

## 4e. Cô lập context ở subagent để context của lead sạch

### Kết luận ngắn
Subagent chạy trong context riêng và chỉ trả bản chắt lọc về lead; đây vừa là kỹ thuật tiết kiệm context vừa là cách giữ lead tập trung vào plan. Mức chắc chắn: **cao** về cơ chế; lợi ích hiệu năng có số liệu nội bộ Anthropic (90,2%) nhưng đi kèm chi phí token lớn.

### Phát hiện có nguồn
- Subagent "handle focused tasks with clean context windows" và trả về "only a condensed, distilled summary of its work (often 1,000-2,000 tokens)" — [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (bậc 1, 2025-09-29).
- Subagent dùng context riêng và "only send relevant information back to the orchestrator" — [Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk) (bậc 1, 2025-09-29).
- Claude Code: subagent bắt đầu sạch trừ khi là fork (bản sao hội thoại); "the subagent's tool calls stay out of your context, and Claude gets back a summary when the subagent finishes" — [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works) (bậc 1).
- Artifact pattern: "Subagents call tools to store their work in external systems, then pass lightweight references back to the coordinator", giảm mất thông tin và token khi copy — [Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (bậc 1, 2025-06).
- Hiệu năng/chi phí: Opus 4 lead + Sonnet 4 subagent "outperformed single-agent Claude Opus 4 by 90.2%" trên eval research nội bộ; token usage giải thích 80% phương sai BrowseComp; multi-agent dùng ~15× token so với chat — cùng nguồn (bậc 1, 2025-06).
- Quan điểm ngược (Cognition, "Don't Build Multi-Agents", Walden Yan, 06/2025): chia việc cho agent song song gây quyết định phân tán và context không chia sẻ đủ; khuyên agent đơn luồng — chỉ thấy qua snippet search; Cognition sau đó (X, 2026-04-22) nói "the landscape is different" và đã cài vài luồng multi-agent trong Devin. **Không mở được cognition.ai** → độ tin thấp; nhóm câu hỏi phụ 1/5 nên kiểm tra.

### Nhận định
- **Nhận định:** cô lập context giúp lead "nhìn thấy" mục tiêu gốc + plan + các bản tóm tắt ngắn thay vì hàng trăm nghìn token tool output — giảm context rot đúng ở agent cần bám mục tiêu nhất. Cái giá là subagent không thấy toàn cảnh, nên brief giao việc phải đủ (xem 4f).

### Khoảng trống
- Thiếu so sánh có kiểm soát độc lập giữa "lead giữ toàn bộ trace" và "lead chỉ nhận tóm tắt".

## 4f. Điều kiện dừng, kiểm tra hoàn thành, verifier/LLM-as-judge, quy tắc effort scaling

### Kết luận ngắn
Các hệ thật đặt quy tắc phân bổ effort ngay trong prompt, ép bước tự kiểm "đã xong chưa", và tách evaluator khỏi generator vì model tự chấm mình quá dễ dãi. Mức chắc chắn: **cao** về thực hành; bằng chứng định lượng có ở Magentic-One và think tool, còn phần evaluator chủ yếu định tính.

### Phát hiện có nguồn
- Effort scaling trong prompt của Anthropic Research: "Simple fact-finding requires just 1 agent with 3-10 tool calls, direct comparisons might need 2-4 subagents with 10-15 calls each, and complex research might use more than 10 subagents with clearly divided responsibilities" — [Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (bậc 1, 2025-06).
- Brief giao việc: "Each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries"; đặt "explicit guardrails to prevent the agents from spiraling out of control" — cùng nguồn.
- LLM-as-judge cho eval: chấm theo rubric (factual accuracy, citation accuracy, completeness, source quality, tool efficiency); "a single LLM call with a single prompt outputting scores from 0.0-1.0 and a pass-fail grade" nhất quán và khớp người chấm nhất — cùng nguồn.
- Vòng lặp agent: "gather context -> take action -> verify work -> repeat"; verify bằng rule (vd lint), visual feedback, LLM-as-judge — nhưng judge "generally not a very robust method, and can have heavy latency tradeoffs" — [Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk) (bậc 1, 2025-09-29).
- Tự chấm thất bại: agent tự đánh giá thì "confidently praising the work—even when… the quality is obviously mediocre"; tách evaluator và chỉnh nó hoài nghi dễ hơn bắt generator tự phê bình; QA mặc định của Claude "identified real issues, then talked itself into approving the work"; giải pháp: "sprint contract" (generator đề xuất làm gì + cách kiểm, evaluator duyệt), evaluator dùng Playwright MCP click thử app, fail sprint nếu tiêu chí dưới ngưỡng; calibrate bằng few-shot có điểm chi tiết — [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps) (bậc 1, 2026-03-24).
- Chi phí: solo Opus 4.5 20 phút/$9; full harness 6 giờ/$200; V2 (Opus 4.6) 3 giờ 50 phút/$124,70; với Opus 4.6 bỏ sprint, evaluator chỉ chạy một lần cuối; giữ planner vì thiếu planner thì generator làm hẹp phạm vi; evaluator "worth its cost only when a task sits beyond what the current model does reliably on its own" — cùng nguồn.
- Magentic-One: completion check + loop detection là 2/5 câu hỏi bắt buộc mỗi vòng; dừng theo số lần thử/thời gian tối đa (xem 4b) — [Magentic-One PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2024/11/MagenticOne.pdf) (bậc 1, 2024-11).
- Claude Agent SDK có giới hạn `maxTurns`; chạm giới hạn trả result subtype `error_max_turns` — [Track todos](https://code.claude.com/docs/en/agent-sdk/todo-tracking) (bậc 1).

### Nhận định
- **Nhận định:** điều kiện dừng có hai lớp: lớp "cứng" do harness (max turns, thời gian, ngân sách) và lớp "mềm" do model (completion check theo tiêu chí trong brief/ledger/feature list). Lớp mềm đáng tin hơn khi tiêu chí được viết ra trước và kiểm bởi một agent/cơ chế khác (test, evaluator) thay vì chính model tự kết luận.

### Khoảng trống
- Chưa có số liệu ablation công khai cho evaluator tách rời vs tự đánh giá (bài 2026-03 chỉ có so sánh định tính + chi phí).

## 4g. Harness cho agent chạy dài: initializer agent, progress file, feature list

### Kết luận ngắn
Anthropic (11/2025) mô tả harness hai pha: initializer agent dựng môi trường và "bộ nhớ" (progress file, feature list JSON, git), các coding agent sau đó mỗi phiên đọc lại các file này trước khi làm một feature. Mức chắc chắn: **cao** về cơ chế; **không có số liệu định lượng**.

### Phát hiện có nguồn
- Lỗi quan sát được: "one-shotting" (làm quá nhiều một lúc, hết context giữa chừng, để lại feature dở không tài liệu); "declaring victory early" (thấy có tiến độ rồi kết luận xong); đánh dấu xong khi chưa test end-to-end — [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) (bậc 1, 2025-11-26).
- Initializer agent tạo `init.sh`, `claude-progress.txt` (log việc đã làm), commit git đầu, và feature list mở rộng prompt người dùng (ví dụ clone claude.ai >200 feature, tất cả ban đầu "failing") — cùng nguồn.
- Feature list dạng JSON với trường `passes`; agent chỉ được đổi `passes`; prompt: "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality"; chọn JSON vì model ít sửa/ghi đè sai hơn Markdown — cùng nguồn.
- Đầu mỗi phiên: chạy `pwd`; đọc git log và progress file; đọc feature list, chọn feature ưu tiên cao nhất chưa xong; chạy dev server qua `init.sh` và test end-to-end cơ bản trước khi làm feature mới — cùng nguồn.
- Test như người dùng bằng Puppeteer MCP "dramatically improved performance"; hạn chế: không thấy alert modal native — cùng nguồn.

### Nhận định
- **Nhận định:** đây là phiên bản "ledger" cho coding: feature list = task ledger (cố định, khó sửa), progress file + git log = progress ledger; nghi thức "đọc lại trước khi làm" thay cho việc model phải nhớ mục tiêu qua các phiên.

### Khoảng trống
- Bài không công bố số liệu; còn bỏ ngỏ câu hỏi multi-agent (QA/test agent) có tốt hơn agent đơn không.

## 4h. Orchestrator tích hợp kết quả và quyết định bước kế: reflection, think tool, interleaved thinking

### Kết luận ngắn
Sau mỗi kết quả subagent, orchestrator dùng một bước suy luận (extended/interleaved thinking, trước đây là "think" tool) để đối chiếu với plan/brief, xác định khoảng trống và quyết định spawn thêm, đổi chiến lược hay dừng. Think tool có số liệu τ-bench; nhưng Anthropic từ 12/2025 khuyên dùng extended thinking thay thế. Mức chắc chắn: **cao** về cơ chế, **trung bình** về mức cải thiện (số liệu trong bài lệch nhau).

### Phát hiện có nguồn
- LeadResearcher "synthesizes these results and decides whether more research is needed—if so, it can create additional subagents or refine its strategy" — [Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (bậc 1, 2025-06).
- Extended thinking của lead là "controllable scratchpad"; subagent dùng interleaved thinking sau tool result để "evaluate quality, identify gaps, and refine their next query"; extended thinking "improved instruction-following, reasoning, and efficiency" — cùng nguồn.
- Think tool (2025-03-20): tool `think` với một tham số `thought`, không lấy thông tin mới, chỉ ghi lại suy nghĩ; khác extended thinking ở chỗ dùng giữa chừng sau khi nhận tool result. τ-bench airline (Claude 3.7 Sonnet) pass^1: think + prompt tối ưu 0,570 vs baseline 0,370 trong lời văn ("54% relative improvement"), nhưng bảng ghi 0,584 vs 0,332 — hai bộ số không khớp; retail: think 0,812 vs baseline 0,783; SWE-bench +1,6% trung bình. Dùng cho: phân tích tool output, môi trường nhiều policy, quyết định tuần tự tốn kém nếu sai. Cập nhật 2025-12-15: nay khuyên dùng extended thinking thay think tool trong đa số trường hợp — [The "think" tool](https://www.anthropic.com/engineering/claude-think-tool) (bậc 1, 2025-03-20, cập nhật 2025-12-15).
- Magentic-One: reflection khi stall — "identifies what may have gone wrong, what new information it learned along the way, and what it might do differently" rồi cập nhật ledger và plan — [Magentic-One PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2024/11/MagenticOne.pdf) (bậc 1, 2024-11).
- Harness 2026: evaluator đối chiếu kết quả với "sprint contract" (tiêu chí kiểm thử thống nhất trước) chứ không với ấn tượng chung — [Harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps) (bậc 1, 2026-03-24).

### Nhận định
- **Nhận định:** "đánh giá output subagent so với brief" hiệu quả nhất khi brief có tiêu chí kiểm được (output format, ranh giới, tiêu chí pass) — tức chất lượng bước tích hợp phụ thuộc chất lượng bước giao việc.

### Khoảng trống
- Chưa có số liệu công khai riêng cho interleaved thinking ở orchestrator đa agent.

## Truy vấn đã chạy
- Manus context engineering todo.md recitation attention (standard)
- Manus Peak Ji todo list one third of actions planner agent (standard)
- Anthropic context editing memory tool 39% 84% token reduction (standard)
- Anthropic engineering harness design long-running application planner generator evaluator (extended)
- Cognition "Don't Build Multi-Agents" Walden Yan share full agent traces (standard)
- Agentic Context Engineering context collapse brevity bias evolving playbooks (standard)
- OpenAI cookbook session memory trimming summarization context drift agents (standard)
- Fetch trực tiếp: anthropic.com/engineering (multi-agent-research-system, effective-harnesses-for-long-running-agents, effective-context-engineering-for-ai-agents, claude-think-tool, harness-design-long-running-apps), claude.com/blog (context-management, building-agents-with-the-claude-agent-sdk), code.claude.com/docs (agent-sdk/todo-tracking, context-window, how-claude-code-works, glossary), Magentic-One PDF trên microsoft.com.
- Fetch thất bại (proxy chặn): arxiv.org/html/2411.04468, manus.im, rlancemartin.github.io, cognition.ai, blog.langchain.com, developers.openai.com, alphaxiv.org, venturebeat.com, research.trychroma.com, marktechpost.com, tianpan.co.
