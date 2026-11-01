# Debugging

> Debug là quá trình tìm ra nguyên nhân gốc của một hành vi sai và sửa nó. Kỹ năng debug không nằm ở việc biết bấm nút nào trong IDE, mà ở phương pháp: tái hiện, thu hẹp, đặt giả thuyết, kiểm chứng.

## Tại sao cần biết
Lập trình viên dành phần lớn thời gian để đọc code và tìm lỗi. Yêu cầu entry level: debug code trong IDE; thành thạo hơn là dùng công cụ phục vụ debug lỗi (log, profiler, công cụ hệ thống). Interview hay hỏi: "khi gặp bug trên production bạn làm gì", "breakpoint, step over, step into là gì", "debug Go bằng gì", hoặc kể một bug khó bạn từng gặp.

## Khái niệm cốt lõi

### Quy trình debug có phương pháp
1. **Tái hiện (reproduce)**: tìm các bước, input, môi trường làm lỗi xuất hiện ổn định. Không tái hiện được thì không chắc đã sửa.
2. **Đọc kỹ thông báo lỗi và stack trace**: dòng nào, hàm nào, giá trị gì. Phần lớn đáp án nằm ngay đó.
3. **Thu hẹp phạm vi**: lỗi ở tầng nào (client, handler, service, DB)? Chia đôi luồng xử lý, kiểm tra dữ liệu ở giữa. Với lỗi xuất hiện sau một lần thay đổi, dùng `git bisect` tìm commit gây lỗi.
4. **Đặt giả thuyết và kiểm chứng**: "nếu nguyên nhân là X thì khi làm Y sẽ thấy Z". Thay đổi **một** thứ mỗi lần.
5. **Tìm nguyên nhân gốc (root cause)**, không chỉ triệu chứng. Kỹ thuật **5 Whys**: hỏi "vì sao" liên tiếp.
6. **Sửa và viết test tái hiện bug** (fail trước khi sửa, pass sau khi sửa) để bug không quay lại.
7. **Rút kinh nghiệm**: chỗ khác có lỗi tương tự không? Có cần thêm log, alert, validate không?

### Công cụ trong IDE (debugger)
- **Breakpoint**: dừng chương trình tại một dòng. **Conditional breakpoint**: chỉ dừng khi điều kiện đúng (`userID == 42`), hữu ích trong vòng lặp lớn. **Logpoint**: in giá trị mà không dừng.
- **Step over** (F10 trong VS Code): chạy hết dòng hiện tại, không đi vào hàm được gọi.
- **Step into** (F11): đi vào bên trong hàm được gọi.
- **Step out** (Shift+F11): chạy hết hàm hiện tại, quay về nơi gọi.
- **Continue** (F5): chạy tới breakpoint tiếp theo.
- **Variables / Watch**: xem và theo dõi giá trị biến, biểu thức.
- **Call stack**: chuỗi lời gọi hàm dẫn tới điểm hiện tại; mỗi goroutine có call stack riêng.
- Phím tắt khác nhau giữa IDE (GoLand dùng F8/F7…); nắm khái niệm là chính.

### Debug Go
- **Delve** (`dlv`) là debugger chuẩn cho Go; VS Code (extension Go) và GoLand dùng Delve bên dưới.
```bash
go install github.com/go-delve/delve/cmd/dlv@latest
dlv debug ./cmd/server -- --port 8080   # build và debug
(dlv) break internal/service/order.go:42
(dlv) continue
(dlv) print order
(dlv) next      # step over
(dlv) step      # step into
(dlv) stack     # call stack
(dlv) goroutines
```
- Cấu hình VS Code `launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug server",
      "type": "go",
      "request": "launch",
      "mode": "debug",
      "program": "${workspaceFolder}/cmd/server",
      "env": { "DB_DSN": "postgres://localhost/dev" },
      "args": ["--port", "8080"]
    }
  ]
}
```
- Debug một test: đặt breakpoint trong file `_test.go`, bấm "debug test" phía trên hàm test.
- Có thể **attach** vào process đang chạy (`dlv attach <pid>`) hoặc debug từ xa (container) qua `dlv --headless`.
- Build tối ưu có thể làm biến "biến mất" khi debug; Delve tự build với `-gcflags="all=-N -l"` (tắt tối ưu, tắt inline).

### Đọc panic và stack trace Go
```
panic: runtime error: invalid memory address or nil pointer dereference
[signal SIGSEGV: segmentation violation code=0x1 addr=0x0 pc=0x...]

goroutine 1 [running]:
main.(*OrderService).Total(0x0)
        /app/internal/service/order.go:27 +0x1d
main.main()
        /app/cmd/server/main.go:15 +0x25
```
Đọc từ trên xuống: loại lỗi (nil pointer), goroutine nào, hàm nào ở dòng nào (`order.go:27`), receiver `0x0` là nil → ai đó gọi method trên `*OrderService` chưa khởi tạo. Đi tiếp xuống để thấy ai gọi (`main.go:15`).

Panic hay gặp: nil pointer dereference, index out of range, ghi vào map nil, type assertion sai kiểu không dùng dạng `v, ok`, gửi vào channel đã đóng, `concurrent map writes`.

### Log
Ở môi trường server không gắn debugger được, **log là công cụ chính**.
- Dùng **log có cấu trúc** (`log/slog`), có level (DEBUG, INFO, WARN, ERROR), kèm ngữ cảnh: request ID, user ID, tham số quan trọng.
```go
logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
logger.Error("charge failed", "order_id", orderID, "amount", amount, "err", err)
// {"time":"...","level":"ERROR","msg":"charge failed","order_id":1001,"amount":50000,"err":"timeout"}
```
- **Request ID / trace ID** đi xuyên qua mọi log và service để ghép lại toàn bộ hành trình của một request.
- Không log secret, mật khẩu, dữ liệu cá nhân nhạy cảm.
- Wrap lỗi với ngữ cảnh (`fmt.Errorf("load user %d: %w", id, err)`) để thông điệp lỗi cuối cùng tự kể câu chuyện.

### Công cụ khác
| Công cụ | Dùng để |
|---|---|
| `go vet`, `staticcheck` | Bắt lỗi khả nghi trước khi chạy |
| `go test -race` | Phát hiện data race |
| `pprof` (`net/http/pprof`, `go tool pprof`) | Profile CPU, bộ nhớ, goroutine, tìm chỗ chậm hay rò rỉ |
| `go tool trace` | Xem lập lịch goroutine, độ trễ GC |
| `curl -v`, Postman | Gửi request, xem header/response |
| `tcpdump`, Wireshark | Bắt gói tin mạng |
| `ss`, `lsof`, `top`, `strace` | Kết nối, file đang mở, tài nguyên, system call |
| `EXPLAIN ANALYZE` | Truy vấn DB chậm |
| Log tập trung (ELK, Loki), metrics (Prometheus/Grafana), tracing (Jaeger, OpenTelemetry) | Debug hệ thống phân tán trên production |
| `kubectl logs/describe/exec`, `docker logs` | Debug trong container |

## Cách hoạt động
Xử lý bug trên production theo thứ tự ưu tiên:
1. **Đánh giá ảnh hưởng**: bao nhiêu người dùng, tính năng nào, dữ liệu có bị sai không.
2. **Giảm thiệt hại trước**: rollback phiên bản vừa deploy, tắt feature flag, scale thêm; sửa tận gốc sau.
3. **Thu thập dữ liệu**: log quanh thời điểm lỗi (lọc theo request ID), metrics (error rate, latency, CPU, memory, số kết nối DB), thay đổi gần đây (deploy, config, dữ liệu).
4. **Tái hiện ở môi trường dev/staging** với dữ liệu tương tự.
5. Sửa, viết test, review, deploy; theo dõi metrics sau deploy.
6. **Postmortem**: nguyên nhân, dòng thời gian, cách phòng tránh (không đổ lỗi cá nhân).

## Ví dụ
Bug: API `/orders` thỉnh thoảng treo rồi timeout sau vài giờ chạy.
1. Metrics: số kết nối DB đang dùng tăng dần tới `MaxOpenConns` rồi đứng yên; request chờ kết nối.
2. Giả thuyết: kết nối không được trả về pool.
3. `pprof` goroutine dump: hàng trăm goroutine kẹt ở `database/sql.(*DB).conn`.
4. Đọc code truy vấn:
```go
rows, err := db.QueryContext(ctx, q, userID)
if err != nil { return nil, err }
for rows.Next() {
    if err := rows.Scan(&o.ID); err != nil {
        return nil, err   // return sớm mà không Close → rò kết nối
    }
}
```
5. Sửa: thêm `defer rows.Close()` ngay sau khi kiểm tra err; viết test với số lần gọi lớn hơn `MaxOpenConns` để tái hiện.
6. Rút kinh nghiệm: bật linter `sqlclosecheck`/`rowserrcheck`; thêm alert khi pool gần cạn.

Bug: tổng tiền sai lệch vài đồng. Breakpoint ở hàm tính tổng, watch biến → thấy dùng `float64`; `0.1 + 0.2` không chính xác. Root cause: kiểu dữ liệu sai cho tiền. Sửa: dùng `int64` đơn vị đồng (xem [05-data-structures.md](05-data-structures.md)).

## Hiểu nhầm thường gặp
- **"Debug là thêm `fmt.Println` khắp nơi"**: print vẫn hữu ích, nhưng debugger, log có cấu trúc và profiler hiệu quả hơn nhiều; nhớ xóa print tạm trước khi commit.
- **"Sửa được triệu chứng là xong"**: bắt `nil` để khỏi panic mà không hỏi vì sao nó nil thì bug sẽ hiện ra chỗ khác.
- **"Lỗi chập chờn là do máy/mạng"**: lỗi không ổn định thường là race condition, timeout, phụ thuộc thứ tự hay dữ liệu cụ thể. Chạy `-race`, log nhiều ngữ cảnh hơn.
- **"Thay nhiều thứ cùng lúc cho nhanh"**: khi hết lỗi bạn không biết thay đổi nào có tác dụng.

## Câu hỏi và trả lời

**Quy trình debug của bạn?**
> - **Bug**: chênh lệch giữa hành vi mong đợi và hành vi thực tế của chương trình.
> - **Root cause (nguyên nhân gốc)**: điểm sai đầu tiên trong chuỗi nhân quả dẫn tới bug, khác với *triệu chứng* nơi lỗi lộ ra.
>
> Debug là áp dụng phương pháp khoa học: thu hẹp khoảng tìm kiếm bằng giả thuyết có kiểm chứng, không phải đoán mò. Các bước:
> 1. **Tái hiện** được lỗi một cách ổn định, càng nhỏ càng tốt.
> 2. **Đọc kỹ** thông báo lỗi, stack trace, log quanh thời điểm lỗi.
> 3. **Thu hẹp** vùng nghi ngờ: chia đôi code hay dữ liệu, `git bisect` tìm commit gây lỗi.
> 4. **Đặt giả thuyết** cụ thể ("biến X nil vì cache trả về rỗng").
> 5. **Kiểm chứng** bằng debugger, log, hoặc test, mỗi lần đổi một thứ.
> 6. **Sửa nguyên nhân gốc**, không chỉ chặn triệu chứng.
> 7. **Viết test** tái hiện lỗi để nó không quay lại, và kiểm tra chỗ khác có cùng lỗi không.
>
> Ranh giới: bị kẹt quá lâu thì giải thích vấn đề cho người khác (hoặc "con vịt cao su"), thường tự thấy chỗ giả định sai. Chi tiết ở phần *Quy trình debug có phương pháp* của file này.

**Step over, step into, step out khác nhau?**
> - **Debugger**: công cụ cho dừng chương trình tại một điểm, xem biến và chạy tiếp từng bước (trong Go là Delve, tích hợp vào IDE).
> - **Breakpoint**: điểm trong code mà debugger dừng chương trình lại.
>
> Ba lệnh khác nhau ở cách xử lý *lời gọi hàm* trên dòng hiện tại:
> - **Step over**: chạy hết dòng hiện tại, coi lời gọi hàm là một bước, dừng ở dòng kế tiếp của hàm đang đứng.
> - **Step into**: đi *vào bên trong* hàm được gọi ở dòng hiện tại, dừng ở dòng đầu của hàm đó.
> - **Step out**: chạy nốt hàm hiện tại, dừng ở chỗ ngay sau nơi đã gọi nó.
>
> Cách dùng: step over khi tin hàm được gọi đúng, step into khi nghi ngờ nó, step out khi lỡ vào một hàm không liên quan. **Continue** chạy tới breakpoint tiếp theo. Ranh giới: step into vào hàm thư viện chuẩn thường lạc vào code không cần quan tâm; đặt breakpoint ở nơi nghi ngờ rồi continue thường nhanh hơn step từng dòng.

**Conditional breakpoint dùng khi nào?**
> - **Conditional breakpoint**: breakpoint chỉ dừng khi một biểu thức điều kiện đúng, vd `userID == 42` hay `i > 9990`.
>
> Dùng khi đoạn code chạy *rất nhiều lần* mà lỗi chỉ xảy ra ở một lần cụ thể: một phần tử trong vòng lặp hàng nghìn lần, một user cụ thể trong hàng loạt request, một giá trị bất thường (`amount < 0`). Breakpoint thường sẽ dừng ở mọi lần, phải bấm continue hàng trăm lần.
>
> Ranh giới: debugger phải đánh giá điều kiện mỗi lần đi qua nên làm chương trình chậm đi đáng kể ở vòng lặp nóng. Biến thể liên quan: *hit count* (dừng ở lần thứ N) và *logpoint* (in giá trị mà không dừng). Nếu điều kiện phức tạp, thêm tạm một `if` trong code rồi đặt breakpoint thường bên trong cũng được.

**Debug Go bằng công cụ gì?**
> - **Delve (`dlv`)**: debugger chuẩn cho Go, hiểu goroutine, interface, slice; IDE (VS Code, GoLand) dùng nó bên dưới.
> - **pprof**: profiler tích hợp của Go, đo CPU, bộ nhớ, goroutine, lock.
> - **Race detector**: chế độ build `-race` phát hiện data race lúc chạy.
>
> Chọn công cụ theo *loại vấn đề*:
> - Logic sai: test + Delve (breakpoint, xem biến, xem stack từng goroutine).
> - Lỗi đồng thời: `go test -race`, xem trạng thái goroutine bằng pprof `goroutine` hoặc `kill -QUIT` để in mọi stack.
> - Chậm, tốn CPU, tốn RAM: pprof (`net/http/pprof` cho service đang chạy, `go test -cpuprofile`), `go tool trace` cho độ trễ và scheduler.
> - Lỗi trên production: log có cấu trúc, metrics, tracing; không gắn debugger vào production.
> - Bắt lỗi trước khi chạy: `go vet`, staticcheck.
>
> Ranh giới: Delve trên binary build tối ưu có thể thấy biến "optimized away"; build với `-gcflags="all=-N -l"` khi cần debug chi tiết.

**Gặp lỗi trên production nhưng local không bị, làm gì?**
> - **Môi trường**: mọi thứ quanh code ảnh hưởng hành vi: cấu hình, phiên bản phụ thuộc, dữ liệu, tải, mạng, quyền, múi giờ.
> - **Observability**: khả năng hiểu hệ thống từ bên ngoài qua log, metrics, trace.
>
> Quy tắc: code giống nhau mà kết quả khác nhau thì *môi trường khác nhau*; việc cần làm là tìm điểm khác biệt. Kiểm tra lần lượt: phiên bản đang chạy có đúng commit nghĩ không; cấu hình và biến môi trường; dữ liệu (production có giá trị null, ký tự lạ, khối lượng lớn mà local không có); tải và đồng thời (race condition, cạn connection pool, timeout chỉ lộ khi đông); phụ thuộc ngoài (service khác, DB version, mạng chậm); múi giờ, locale. Dùng log, metrics, trace quanh thời điểm lỗi để khoanh vùng, rồi tái hiện ở local hoặc staging với điều kiện tương tự.
>
> Ranh giới: không debug bằng cách sửa thử thẳng trên production. Nếu lỗi đang ảnh hưởng người dùng, ưu tiên khôi phục (rollback, tắt tính năng) trước rồi mới tìm nguyên nhân. Thiếu log để trả lời câu hỏi thì việc đầu tiên sau sự cố là bổ sung log hay metric đó.

**Đọc stack trace panic thế nào?**
> - **Panic**: lỗi runtime làm goroutine dừng; nếu không được recover thì chương trình in thông báo và stack trace rồi thoát.
> - **Stack trace**: danh sách các lời gọi hàm đang dở tại thời điểm lỗi, hàm gần nhất ở trên cùng.
>
> Cách đọc: dòng đầu là *loại lỗi* (`panic: runtime error: invalid memory address or nil pointer dereference`, `index out of range [5] with length 3`). Tiếp theo là `goroutine N [running]:` và các cặp dòng: tên hàm, rồi `đường/dẫn/file.go:dòng`. Đọc từ trên xuống, tìm *frame đầu tiên thuộc code của mình* (bỏ qua frame trong `runtime/` và thư viện), đó là chỗ lỗi lộ ra; các frame bên dưới cho biết đường đi dẫn tới đó.
>
> Ranh giới: chỗ panic là triệu chứng; nguyên nhân thường ở nơi tạo ra giá trị sai (biến nil được trả về từ đâu đó trước đó). Khi chương trình in nhiều goroutine (deadlock, `kill -QUIT`), tìm goroutine ở trạng thái `[running]` hoặc các goroutine cùng chờ một thứ. Ví dụ đọc mẫu ở phần *Đọc panic và stack trace Go* của file này.

**Service bị chậm dần/tốn RAM dần, nghi ngờ gì?**
> - **Memory leak**: bộ nhớ không còn cần dùng nhưng không được giải phóng. Trong Go có GC, nên "leak" là bộ nhớ *vẫn còn được tham chiếu* ngoài ý muốn.
> - **Resource leak**: tài nguyên (goroutine, kết nối, file descriptor) được mở mà không bao giờ đóng.
>
> Quy tắc: thứ gì *tăng theo thời gian chạy* mà không giảm là thứ đang được tạo mà không được giải phóng. Nghi phạm thường gặp: goroutine bị chặn mãi (chờ channel không ai gửi, không có timeout/context); `rows.Close()` hay response body không đóng làm rò kết nối; cache hoặc map toàn cục lớn dần không giới hạn; slice nhỏ cắt từ mảng lớn giữ cả mảng; `time.After` trong vòng lặp dài (giữ timer); `defer` trong vòng lặp. Chậm dần thường đi kèm: GC chạy nhiều hơn vì heap lớn, pool cạn nên request phải chờ.
>
> Cách xác nhận: theo dõi metric số goroutine, heap, số kết nối, file descriptor theo thời gian; so sánh hai lần chụp heap profile và goroutine profile bằng pprof (`go tool pprof -base`) để thấy thứ gì tăng. Ranh giới: RAM của process tăng rồi đứng yên ở một mức có thể là bình thường (runtime giữ bộ nhớ để dùng lại); chỉ đáng lo khi tăng không dừng.

## Liên quan
- [01-operating-systems.md](01-operating-systems.md): lệnh Linux xem process, tài nguyên.
- [09-concurrency.md](09-concurrency.md): race, deadlock, goroutine leak.
- [11-unit-testing.md](11-unit-testing.md): viết test tái hiện bug.
- [13-git-and-version-control.md](13-git-and-version-control.md): `git bisect`.
