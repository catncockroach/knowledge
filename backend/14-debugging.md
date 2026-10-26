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

## Câu hỏi ôn tập
1. **Quy trình debug của bạn?** Tái hiện → đọc lỗi → thu hẹp → giả thuyết → kiểm chứng → sửa gốc → test.
2. **Step over, step into, step out khác nhau?**
3. **Conditional breakpoint dùng khi nào?**
4. **Debug Go bằng công cụ gì?** Delve, IDE, pprof, `-race`.
5. **Gặp lỗi trên production nhưng local không bị, làm gì?** So sánh môi trường, cấu hình, dữ liệu, tải; dựa vào log, metrics, trace.
6. **Đọc stack trace panic thế nào?**
7. **Service bị chậm dần/tốn RAM dần, nghi ngờ gì?** Rò rỉ goroutine, kết nối không đóng, cache không giới hạn; dùng pprof.

## Liên quan
- [01-operating-systems.md](01-operating-systems.md): lệnh Linux xem process, tài nguyên.
- [09-concurrency.md](09-concurrency.md): race, deadlock, goroutine leak.
- [11-unit-testing.md](11-unit-testing.md): viết test tái hiện bug.
- [13-git-and-version-control.md](13-git-and-version-control.md): `git bisect`.
