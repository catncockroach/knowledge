# Brief: Trong hệ multi-agent, agent trung tâm (orchestrator) điều phối subtask, nhận kết quả, và giữ đúng mục tiêu ban đầu qua nhiều lượt gọi model như thế nào?

- **Ngày:** 2026-10-19
- **Câu hỏi chính:** Một orchestrator LLM chia việc cho các subagent, nhận kết quả về, và dù được gọi lại nhiều lần vẫn bám đúng mục tiêu ban đầu của task bằng cơ chế gì, và prompt gửi cho model ở mỗi lượt gồm những gì?
- **Mục đích:** Hiểu đủ sâu cơ chế bên trong để tự thiết kế (hoặc đánh giá) một hệ orchestrator–subagent: biết từng lượt gọi API chứa gì, kết quả subagent quay về dạng nào, và các kỹ thuật chống lạc hướng nào thực sự hiệu quả.
- **Câu hỏi phụ:**
  1. Các kiến trúc điều phối phổ biến là gì (orchestrator–worker/supervisor, handoff, hierarchical, agent-as-tool), và các hệ thống thật (Anthropic multi-agent Research, Claude Code subagents/Agent SDK, OpenAI Agents SDK, LangGraph, Microsoft Magentic-One/AutoGen, Google ADK) cài đặt chúng ra sao?
  2. Cơ chế giao việc và nhận kết quả cụ thể: subagent được gọi như một tool call? kết quả quay về dạng tool_result/tóm tắt/file/artifact? chạy song song hay tuần tự? orchestrator biết subagent đã xong bằng cách nào?
  3. Giải phẫu prompt mỗi lượt: messages gửi cho model orchestrator ở lượt thứ N gồm những phần nào (system prompt, tool definitions, lịch sử, tool_result của subagent, plan/state)? Prompt giao việc cho subagent nên chứa gì (mục tiêu, định dạng đầu ra, ranh giới, công cụ)? Có ví dụ prompt thật được công bố không?
  4. Model được gọi lặp lại là stateless: những kỹ thuật nào giữ nó đúng hướng mục tiêu ban đầu (giữ nguyên task gốc trong context, plan/todo list được "đọc lại", ledger/progress tracking, compaction/tóm tắt, memory ngoài, cô lập context subagent, kiểm tra hoàn thành/verifier)?
  5. Các lỗi thường gặp (goal drift, context rot, lặp vô hạn, subagent làm trùng/lệch, mất thông tin khi tóm tắt) và bằng chứng định lượng (benchmark, taxonomy lỗi, chi phí token) về khi nào multi-agent tốt hơn hay tệ hơn single-agent?
- **Phạm vi:** Hệ multi-agent dựa trên LLM (2023–10/2026), trọng tâm mô hình orchestrator–worker do một LLM trung tâm điều phối; tài liệu chính thức của các nhà cung cấp/framework, bài kỹ thuật engineering blog, paper học thuật. Giả định: người dùng quan tâm cơ chế ở mức API (messages, tool calls), không gắn với framework cụ thể.
- **Ngoài phạm vi:** Multi-agent reinforcement learning cổ điển; hệ agent không dùng LLM; so sánh giá/đánh giá thương mại các sản phẩm; hướng dẫn cài đặt từng framework chi tiết.
- **Độ sâu:** sâu
- **Kế thừa:** không
