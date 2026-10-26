# Backend

Backend là phần chạy phía server của một hệ thống phần mềm: nhận request qua mạng, xử lý nghiệp vụ, lưu trữ dữ liệu và trả kết quả. Bộ ghi chú này gom kiến thức nền tảng mà một lập trình viên backend cần nắm, viết để ôn tập phỏng vấn, với **Go** là ngôn ngữ chính cho mọi ví dụ code. Nội dung là kiến thức tổng quát, không gắn với công ty, dự án hay sản phẩm cụ thể nào.

## Phạm vi
- **Có:** kiến thức level **entry**: hệ điều hành, kiến trúc backend và cách đọc tài liệu giải pháp, Go cơ bản, OOP, cấu trúc dữ liệu, thuật toán, design pattern, clean code/SOLID/convention, lập trình đa luồng, database (SQL, NoSQL), unit test, lập trình an toàn, Git, debug, quy trình Agile/Scrum. Cuối mỗi file có mục **Câu hỏi ôn tập**.
- **Không (ở level này):** system design quy mô lớn, distributed systems chuyên sâu (consensus, distributed transaction), tối ưu hiệu năng Go chuyên sâu, Kubernetes vận hành chi tiết. Các phần này sẽ được bổ sung vào thư mục này khi lên level cao hơn. Kiến thức mạng (TCP/IP, DNS, HTTP, TLS) nằm ở domain [../internet/](../internet/README.md).
- **Đối tượng:** người đã biết lập trình cơ bản, chuẩn bị phỏng vấn hoặc ôn lại cho vị trí backend developer entry level.

## Bản đồ tư duy
```
                     ┌────────────────────────────────────┐
  Nền máy & hệ thống │ 01 OS  ──►  02 Kiến trúc backend    │──► ../internet (mạng)
                     └────────────────────────────────────┘
                                     │
                     ┌───────────────▼────────────────────┐
  Ngôn ngữ & tư duy  │ 03 Go ─► 04 OOP ─► 05 CTDL ─► 06 Thuật toán │
                     └───────────────┬────────────────────┘
                                     │
                     ┌───────────────▼────────────────────┐
  Thiết kế code      │ 07 Design pattern ─► 08 Clean code/SOLID │
                     └───────────────┬────────────────────┘
                                     │
                     ┌───────────────▼────────────────────┐
  Hệ thống chạy thật │ 09 Concurrency ─► 10 Database ─► 12 Security │
                     └───────────────┬────────────────────┘
                                     │
                     ┌───────────────▼────────────────────┐
  Làm việc hằng ngày │ 11 Unit test · 13 Git · 14 Debug · 15 Agile │
                     └────────────────────────────────────┘
```

## Các file
Đọc theo thứ tự:

| File | Nội dung |
|---|---|
| [01-operating-systems.md](01-operating-systems.md) | Các tầng của hệ thống máy tính, kernel và system call, Linux vs Windows, process vs thread, scheduling, virtual memory, stack/heap, file system, signal và lệnh Linux hay dùng khi vận hành service |
| [02-backend-architecture.md](02-backend-architecture.md) | Một request đi qua những tầng nào: client-server, HTTP và REST, load balancer, cache, queue, layered architecture, monolith vs microservices, Docker/k8s, và cách đọc tài liệu giải pháp hệ thống |
| [03-go-basics.md](03-go-basics.md) | Nền tảng Go: kiểu dữ liệu, zero value, slice (len/cap/append) và map, pointer, hàm, xử lý lỗi, defer/panic/recover, package/module, generics, các bẫy hay gặp |
| [04-oop-in-go.md](04-oop-in-go.md) | Bốn trụ cột OOP và cách Go hiện thực chúng: method, value vs pointer receiver, encapsulation theo package, embedding thay kế thừa, interface ngầm định và đa hình |
| [05-data-structures.md](05-data-structures.md) | Kiểu dữ liệu cơ bản (integer, float, overflow), array, linked list, stack, queue, hash table, tree, heap, graph, độ phức tạp từng thao tác và cách chọn cấu trúc cho bài toán |
| [06-algorithms.md](06-algorithms.md) | Big-O và cách tính độ phức tạp, cài đặt bằng Go các thuật toán sắp xếp (bubble, selection, insertion, merge, quick), binary search, BFS/DFS, các kỹ thuật giải bài |
| [07-design-patterns.md](07-design-patterns.md) | Ba nhóm pattern; Singleton (sync.Once), Factory, Functional Options, Adapter, Decorator, Strategy, Observer, Dependency Injection, Repository kèm code Go |
| [08-clean-code-and-solid.md](08-clean-code-and-solid.md) | Nguyên tắc code rõ ràng (đặt tên, hàm, early return, DRY/KISS/YAGNI), năm nguyên tắc SOLID với ví dụ Go, coding convention và công cụ lint của Go |
| [09-concurrency.md](09-concurrency.md) | Concurrency vs parallelism, vòng đời thread, sync/async, goroutine và mô hình GMP, channel, select, mutex, race condition, deadlock, context, worker pool, connection pool |
| [10-databases.md](10-databases.md) | Mô hình quan hệ, SQL và JOIN, normalization, index B+ tree, transaction ACID, isolation level, locking, NoSQL và CAP, dùng `database/sql` trong Go, N+1 query |
| [11-unit-testing.md](11-unit-testing.md) | Test pyramid, nguyên tắc FIRST và AAA, mock/stub/fake, thiết kế code dễ test, table-driven test, fake repository, httptest, coverage, TDD |
| [12-secure-coding.md](12-secure-coding.md) | CIA, hash vs encryption vs encoding, đối xứng/bất đối xứng, lưu mật khẩu, AuthN/AuthZ, JWT, SQL injection, XSS, CSRF, IDOR, SSRF, quản lý secret |
| [13-git-and-version-control.md](13-git-and-version-control.md) | Git vs SVN, ba vùng của Git, branch, merge vs rebase, xử lý conflict, reset vs revert, quy trình merge request và các mô hình branching |
| [14-debugging.md](14-debugging.md) | Quy trình debug có phương pháp, breakpoint/step trong IDE, Delve, đọc panic stack trace, log có cấu trúc, pprof và xử lý bug trên production |
| [15-sdlc-agile-scrum.md](15-sdlc-agile-scrum.md) | Các giai đoạn SDLC, Waterfall vs Agile, Agile Manifesto, Scrum (vai trò, sự kiện, artifact), user story, story point, Kanban, CI/CD |

## Thuật ngữ nền
- **Request / response**: yêu cầu client gửi và kết quả server trả về.
- **Latency / throughput**: thời gian xử lý một request / số request xử lý được mỗi giây.
- **Stateless**: instance không giữ trạng thái phiên riêng, request nào tới instance nào cũng được.
- **Goroutine**: luồng thực thi nhẹ do Go runtime quản lý.
- **Interface**: tập chữ ký method; nền của đa hình, DI và mock trong Go.
- **Big-O**: ký hiệu đo tốc độ tăng chi phí theo kích thước dữ liệu.
- **Transaction / ACID**: nhóm thao tác DB nguyên tử, nhất quán, cô lập, bền vững.
- **Idempotent**: gọi một hay nhiều lần cho cùng kết quả.
- **CI/CD**: tự động build, test và triển khai mỗi khi có thay đổi.

## Cách ôn tập gợi ý
1. Đọc theo thứ tự một lượt, tự gõ lại và chạy các đoạn code Go (`go run`, `go test`).
2. Trả lời to mục **Câu hỏi ôn tập** ở cuối mỗi file mà không nhìn đáp án; chỗ nào ấp úng thì đọc lại phần tương ứng.
3. Chuẩn bị 1–2 ví dụ thực tế của bản thân cho mỗi nhóm (một bug từng debug, một chỗ đã áp dụng design pattern, một lần xử lý conflict).
