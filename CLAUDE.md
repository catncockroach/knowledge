# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Mục đích

Đây là kho kiến thức cá nhân ("bộ não thứ hai") của chủ repo, dùng để nghiên cứu và ghi chép kiến thức. Đây không phải dự án phần mềm: không có bước build, lint hay test.

Chủ repo viết bằng tiếng Việt. Mặc định trả lời và ghi chú bằng tiếng Việt, trừ khi được yêu cầu khác.

## Research

Khi được yêu cầu research một đề tài hay câu hỏi, dùng skill `research` của repo (`.claude/skills/research/`), không dùng `deep-research` builtin. Mỗi lần research nằm trong một thư mục `research/<YYYY-MM-DD>-<slug>/`, gồm `brief.md`, `notes/` và `report.md`. Trước khi research một chủ đề, xem `research/` để kế thừa các báo cáo cũ cùng chủ đề.

## Kiến thức nền tảng theo domain

Khi được yêu cầu viết kiến thức cơ sở, cốt lõi hay nền tảng của một ngành, dùng skill `writing-domain-foundations`. Mỗi domain là một thư mục ở gốc repo (tên tiếng Anh, vd `internet/`), gồm các file `NN-<topic>.md` tên tiếng Anh với nội dung tiếng Việt, và một `README.md` tổng quan có mục lục kèm ý nghĩa từng file.

## Commit

Mỗi khi tạo commit, dùng skill `commit`: subject `brief title: detail` viết thường toàn bộ (brief title tự do, vài từ), vài dòng `- ` mô tả, kết thúc bằng trailer `Co-Authored-By` của agent. Chỉ commit khi chủ repo yêu cầu, không tự push.

## Skill của repo

Mỗi skill nằm ở `.claude/skills/<name>/`. Field `description` phải mở đầu bằng `catncockroach - ` để phân biệt với skill builtin. Skill nào cần làm rõ yêu cầu với người dùng thì gọi skill `grill-me` ở chế độ Called, không tự viết lại cách hỏi. Tạo hoặc sửa skill bằng skill `skill-building` (không dùng `skill-creator` builtin, trừ khi cần chạy eval/benchmark). Kiểm tra mọi skill bằng lệnh:

```bash
python3 .claude/skills/skill-building/scripts/validate.py .claude/skills/*/
```

## Quy ước còn để ngỏ

Ngoài `research/`, chưa có quy ước về cấu trúc thư mục, định dạng ghi chú hay cách liên kết giữa các ghi chú. Hỏi chủ repo trước khi tự đặt ra cấu trúc mới.
