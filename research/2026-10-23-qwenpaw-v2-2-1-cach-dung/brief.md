# Brief: Dùng QwenPaw v2.2.1 thế nào, và cấu hình skills, subagent ra sao?

- **Ngày:** 2026-10-23
- **Câu hỏi chính:** Với QwenPaw v2.2.1 (agentscope-ai/QwenPaw), cài đặt, dùng hằng ngày và cấu hình skills, subagent (multi-agent) cùng các thành phần liên quan như thế nào?
- **Mục đích:** Chủ repo muốn hiểu đủ để tự cài, cấu hình và vận hành QwenPaw: biết file cấu hình nằm đâu, viết skill thế nào, tạo/điều phối subagent ra sao.
- **Câu hỏi phụ:**
  1. QwenPaw là gì (quan hệ với CoPaw, AgentScope), v2.2.1 có thật không, ra ngày nào, thay đổi gì so với v2.2.0 / v2.x trước đó?
  2. Cài đặt và chạy thế nào (pip/docker/desktop, lệnh CLI, console web, cấu hình model provider kể cả model local, channel như DingTalk/Feishu/Discord/Telegram…)?
  3. Skills: định dạng (SKILL.md?), thư mục đặt skill, cách bật/tắt, cài skill từ hub/marketplace, skill builtin có những gì, ví dụ một skill tự viết?
  4. Subagent / multi-agent: khái niệm agent workspace, tạo nhiều agent, giao việc giữa các agent, cấu hình (file nào, field nào), giới hạn?
  5. Các cấu hình liên quan khác: MCP, tools, memory, heartbeat/cron, bảo mật/sandbox; file cấu hình chính (config.json/agent.json…) và biến môi trường?
  6. Hạn chế, lỗi thường gặp, và mẹo thực tế từ cộng đồng (issues, discussions)?
- **Phạm vi:** Bản v2.2.1 (nếu không tồn tại thì bản gần nhất, ghi rõ). Ưu tiên tài liệu chính thức (GitHub repo, docs site, release notes, Alibaba Cloud Model Studio docs), rồi issues/discussions, bài blog. Giả định chủ repo chạy trên Linux/macOS, dùng cá nhân.
- **Ngoài phạm vi:** So sánh sâu với OpenClaw/các agent khác (chỉ nhắc ngắn nếu cần), phát triển core của QwenPaw, đánh giá benchmark.
- **Độ sâu:** sâu
- **Kế thừa:** không (research/2026-10-19-multi-agent-orchestrator-dieu-phoi là chủ đề gần nhưng khác)
