# Concurrency

> Lập trình đa luồng (concurrency) là tổ chức chương trình để xử lý nhiều việc xen kẽ hoặc cùng lúc. Backend phục vụ hàng nghìn request đồng thời nên concurrency là kỹ năng lõi; Go đưa nó vào ngay ngôn ngữ bằng goroutine và channel.

## Tại sao cần biết
Yêu cầu entry level: hiểu khái niệm và bản chất hoạt động của thread (vòng đời), sync/async, lock, có khả năng lập trình đa luồng; thành thạo hơn là multithreading và connection pool. Interview Go gần như luôn hỏi: goroutine khác thread thế nào, channel buffered/unbuffered, `select`, `sync.WaitGroup`, `Mutex`, race condition, deadlock, cách giới hạn số goroutine, `context`.

## Khái niệm cốt lõi

### Concurrency và parallelism
- **Concurrency**: *cấu trúc* chương trình thành nhiều tác vụ độc lập có thể tiến triển xen kẽ. Có thể chạy trên một core.
- **Parallelism**: *thực thi* nhiều tác vụ **cùng một thời điểm** trên nhiều core.
- "Concurrency is about dealing with lots of things at once; parallelism is about doing lots of things at once" (Rob Pike). Concurrency là điều kiện để có parallelism, nhưng không đồng nghĩa.

### Thread và vòng đời
Thread là đơn vị lập lịch của OS bên trong process, chia sẻ bộ nhớ với các thread khác cùng process (xem [01-operating-systems.md](01-operating-systems.md)). Vòng đời (theo cách mô tả phổ biến của Java):
```
NEW ──start()──► RUNNABLE ◄────────► RUNNING ──xong──► TERMINATED
                    ▲                   │
                    │                   ▼
                    └──── BLOCKED / WAITING / TIMED_WAITING
                          (chờ lock, chờ I/O, sleep, wait/join)
```
- **New**: đã tạo, chưa chạy. **Runnable**: sẵn sàng, chờ scheduler cấp CPU. **Running**: đang chạy.
- **Blocked/Waiting**: chờ lock, chờ I/O, chờ thread khác, sleep. **Terminated**: kết thúc.
- OS thread tốn tài nguyên: stack cỡ MB, tạo/hủy và context switch qua kernel. Vài nghìn thread đã nặng.

### Sync và async; blocking và non-blocking
- **Synchronous**: gọi một việc rồi **chờ** nó xong mới làm tiếp. **Asynchronous**: khởi động việc rồi làm tiếp, nhận kết quả sau (callback, future/promise, channel).
- **Blocking**: luồng gọi bị treo cho tới khi có kết quả. **Non-blocking**: trả về ngay.
- Node.js/JS, C#, Python dùng `async/await` trên event loop. Go chọn cách khác: viết code **đồng bộ, blocking** trong goroutine; runtime tự đậu goroutine đang chờ và chạy goroutine khác, nên đạt hiệu quả của async mà code vẫn tuần tự, dễ đọc. Muốn chạy bất đồng bộ thì `go f()` và nhận kết quả qua channel.

### Goroutine
- Hàm chạy đồng thời, do **Go runtime** lập lịch (không phải OS). Khởi đầu với stack nhỏ (vài KB) tự co giãn, nên chạy hàng trăm nghìn goroutine là bình thường.
- Mô hình **G-M-P**: G (goroutine), M (OS thread), P (processor logic, số lượng = `GOMAXPROCS`, mặc định bằng số core). Mỗi P có hàng đợi goroutine; M gắn với P để chạy G. Goroutine chờ mạng được đưa vào network poller (epoll) mà không chiếm thread; P rảnh có thể "trộm" việc từ P khác (*work stealing*).
- Chương trình kết thúc khi `main` return, **không chờ** goroutine khác. Phải đồng bộ bằng `WaitGroup` hoặc channel.

| | OS thread | Goroutine |
|---|---|---|
| Quản lý | Kernel | Go runtime |
| Stack | Cố định, cỡ MB | Bắt đầu vài KB, tự tăng |
| Chi phí tạo, chuyển | Đắt (system call) | Rẻ (trong user space) |
| Số lượng thực tế | Nghìn | Trăm nghìn – triệu |
| Định danh | Có thread ID | Không lộ ID (cố ý) |

### Channel
"Don't communicate by sharing memory; share memory by communicating." Channel là đường ống có kiểu để các goroutine truyền dữ liệu và đồng bộ với nhau.
```go
ch := make(chan int)      // unbuffered
bc := make(chan int, 10)  // buffered, sức chứa 10

ch <- 1      // gửi
v := <-ch    // nhận
v, ok := <-ch // ok = false nếu channel đã đóng và rỗng
close(ch)    // chỉ bên GỬI đóng; báo "không còn dữ liệu"
for v := range ch {} // nhận tới khi channel đóng
```
- **Unbuffered**: gửi bị chặn cho tới khi có người nhận (và ngược lại) → điểm hẹn đồng bộ.
- **Buffered**: gửi chỉ chặn khi buffer đầy; nhận chặn khi rỗng → hàng đợi, tách nhịp producer/consumer.
- Quy tắc: gửi vào channel đã đóng → panic; đóng hai lần → panic; gửi/nhận trên channel `nil` → chặn mãi mãi.
- Kiểu có hướng: `chan<- int` (chỉ gửi), `<-chan int` (chỉ nhận) để hàm nói rõ vai trò.

**select**: chờ nhiều thao tác channel, chạy nhánh nào sẵn sàng trước.
```go
select {
case msg := <-msgCh:
    handle(msg)
case <-time.After(2 * time.Second):
    log.Println("timeout")
case <-ctx.Done():
    return ctx.Err()
default:
    // không chặn: chạy ngay nếu không nhánh nào sẵn sàng
}
```

### Shared memory và các vấn đề
**Race condition**: kết quả phụ thuộc thứ tự chạy của các luồng. **Data race**: hai goroutine truy cập cùng biến, ít nhất một ghi, không đồng bộ.
```go
counter := 0
var wg sync.WaitGroup
for i := 0; i < 1000; i++ {
    wg.Add(1)
    go func() {
        defer wg.Done()
        counter++ // đọc-cộng-ghi: không nguyên tử → kết quả < 1000
    }()
}
wg.Wait()
```
`counter++` gồm 3 bước (đọc, cộng, ghi); hai goroutine cùng đọc giá trị 5 rồi cùng ghi 6 → mất một lần cộng. Phát hiện bằng `go test -race` / `go run -race`.

**Critical section**: đoạn code truy cập tài nguyên dùng chung, chỉ một luồng được vào tại một thời điểm.

### Công cụ đồng bộ trong gói `sync`
| Công cụ | Dùng khi |
|---|---|
| `sync.Mutex` | Khóa loại trừ: một goroutine trong critical section |
| `sync.RWMutex` | Nhiều reader cùng lúc, writer độc quyền; hợp khi đọc nhiều ghi ít |
| `sync.WaitGroup` | Chờ một nhóm goroutine kết thúc |
| `sync.Once` | Chạy đúng một lần (khởi tạo lazy, singleton) |
| `sync/atomic` | Thao tác nguyên tử trên số, con trỏ (counter, flag) không cần lock |
| `sync.Cond` | Chờ một điều kiện (ít dùng, channel thường thay được) |
| `sync.Map` | Map an toàn đồng thời cho trường hợp đặc thù (key ghi một lần đọc nhiều) |
| `sync.Pool` | Tái sử dụng object tạm, giảm áp lực GC |

```go
type SafeCounter struct {
    mu sync.Mutex
    m  map[string]int
}

func (c *SafeCounter) Inc(key string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.m[key]++
}

var hits atomic.Int64
hits.Add(1)
```

### Deadlock, starvation, livelock
- **Deadlock**: các luồng chờ nhau vĩnh viễn. Bốn điều kiện cần (Coffman): *mutual exclusion* (tài nguyên độc quyền), *hold and wait* (giữ cái này, chờ cái kia), *no preemption* (không bị cưỡng đoạt), *circular wait* (chờ vòng tròn). Phá một điều kiện là tránh được; cách thực tế nhất: **luôn lấy các lock theo cùng một thứ tự**, giữ lock ngắn, dùng timeout.
```go
// G1: lock A rồi B     G2: lock B rồi A   → mỗi bên giữ một, chờ cái còn lại
```
Go runtime báo `fatal error: all goroutines are asleep - deadlock!` khi **mọi** goroutine đều bị chặn (ví dụ gửi vào unbuffered channel mà không ai nhận trong `main`). Deadlock cục bộ (chỉ vài goroutine) thì không được báo, biểu hiện là treo hoặc **goroutine leak**.
- **Starvation**: một luồng mãi không được cấp tài nguyên vì luồng khác luôn chiếm.
- **Livelock**: các luồng vẫn chạy, liên tục nhường nhau, nhưng không ai tiến triển.

### Context: hủy và timeout
`context.Context` truyền tín hiệu hủy, deadline và giá trị theo phạm vi request xuyên qua các hàm và goroutine.
```go
ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
defer cancel() // luôn gọi để giải phóng tài nguyên

rows, err := db.QueryContext(ctx, "SELECT ...") // DB tự hủy truy vấn khi hết hạn
```
Khi client ngắt kết nối hoặc hết timeout, `ctx.Done()` đóng lại; mọi goroutine con lắng nghe nó nên dừng sớm, tránh làm việc vô ích và rò rỉ goroutine.

### Connection pool
- Mở kết nối DB/HTTP tốn kém (TCP handshake, TLS, xác thực). **Pool** giữ sẵn một tập kết nối và cho mượn: lấy ra, dùng, trả lại.
- Giới hạn số kết nối tối đa để không làm quá tải DB; request phải **chờ** khi pool cạn.
- `database/sql` của Go có sẵn pool bên trong `*sql.DB` (an toàn cho concurrency, nên tạo **một lần** và dùng chung):
```go
db, err := sql.Open("postgres", dsn) // chưa mở kết nối ngay
db.SetMaxOpenConns(25)               // tối đa kết nối đồng thời
db.SetMaxIdleConns(25)               // số kết nối rảnh giữ lại
db.SetConnMaxLifetime(5 * time.Minute) // làm mới kết nối định kỳ
db.SetConnMaxIdleTime(1 * time.Minute)
```
- Lỗi kinh điển: quên `rows.Close()` hoặc không commit/rollback transaction → kết nối không được trả về pool → pool cạn, mọi request treo.
- `http.Client` cũng có pool kết nối (qua `Transport`); tạo một client dùng chung, đừng tạo mới mỗi request; nhớ đọc hết và `Close()` body response.

## Cách hoạt động
Các pattern concurrency hay dùng trong Go:

**Worker pool**: giới hạn số goroutine xử lý song song.
```go
func workerPool(ctx context.Context, jobs []int, workers int) []int {
    jobCh := make(chan int)
    resCh := make(chan int)
    var wg sync.WaitGroup

    for w := 0; w < workers; w++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for j := range jobCh {
                select {
                case resCh <- j * j: // xử lý
                case <-ctx.Done():
                    return
                }
            }
        }()
    }

    go func() { // producer
        defer close(jobCh)
        for _, j := range jobs {
            select {
            case jobCh <- j:
            case <-ctx.Done():
                return
            }
        }
    }()

    go func() { wg.Wait(); close(resCh) }() // đóng kết quả khi mọi worker xong

    var results []int
    for r := range resCh {
        results = append(results, r)
    }
    return results
}
```

**Fan-out / fan-in và errgroup**: gọi nhiều nguồn song song, gom kết quả, dừng tất cả khi một nguồn lỗi.
```go
import "golang.org/x/sync/errgroup"

func loadDashboard(ctx context.Context, userID int64) (Dashboard, error) {
    g, ctx := errgroup.WithContext(ctx)
    var profile Profile
    var orders []Order

    g.Go(func() (err error) { profile, err = getProfile(ctx, userID); return })
    g.Go(func() (err error) { orders, err = getOrders(ctx, userID); return })

    if err := g.Wait(); err != nil { // lỗi đầu tiên; ctx bị hủy cho các goroutine còn lại
        return Dashboard{}, err
    }
    return Dashboard{Profile: profile, Orders: orders}, nil
}
```
Nếu `getProfile` mất 200 ms và `getOrders` mất 300 ms, chạy tuần tự hết 500 ms, chạy song song khoảng 300 ms.

**Semaphore bằng buffered channel**: giới hạn số việc chạy đồng thời.
```go
sem := make(chan struct{}, 10) // tối đa 10
for _, url := range urls {
    sem <- struct{}{}          // chiếm chỗ, chặn nếu đủ 10
    go func(u string) {
        defer func() { <-sem }() // trả chỗ
        fetch(u)
    }(url)
}
```

**Pipeline**: chuỗi stage nối nhau bằng channel (đọc → parse → lưu), mỗi stage là một hoặc nhiều goroutine.

## Ví dụ
Đoán kết quả, câu hỏi phỏng vấn kinh điển:
```go
func main() {
    ch := make(chan int)
    ch <- 1           // deadlock: unbuffered, không có goroutine nào nhận
    fmt.Println(<-ch)
}
```
Sửa: dùng `make(chan int, 1)` hoặc gửi trong goroutine khác.

**Goroutine leak**:
```go
func search(ctx context.Context) int {
    ch := make(chan int)          // unbuffered
    go func() { ch <- slowQuery() }()
    select {
    case v := <-ch:
        return v
    case <-ctx.Done():
        return -1 // goroutine trên bị kẹt mãi ở "ch <-" vì không còn ai nhận
    }
}
```
Sửa: `make(chan int, 1)` để goroutine gửi được rồi thoát, hoặc truyền ctx vào `slowQuery`.

## Hiểu nhầm thường gặp
- **"Goroutine là thread"**: goroutine được multiplex lên ít OS thread; rẻ hơn rất nhiều và do runtime lập lịch.
- **"Thêm goroutine là nhanh hơn"**: CPU-bound bị giới hạn bởi số core; việc nhỏ thì chi phí đồng bộ lớn hơn lợi ích. Không giới hạn goroutine khi gọi tài nguyên ngoài sẽ làm sập DB/API.
- **"Channel luôn tốt hơn mutex"**: channel hợp để truyền dữ liệu/điều phối; bảo vệ một biến đếm hay map thì mutex đơn giản và nhanh hơn.
- **"Đọc biến dùng chung thì không cần lock"**: đọc đồng thời với một lần ghi vẫn là data race.
- **"Bên nhận nên đóng channel"**: chỉ bên gửi biết khi nào hết dữ liệu; bên nhận đóng dễ gây panic ở bên gửi.

## Câu hỏi ôn tập
1. **Concurrency khác parallelism?**
2. **Vòng đời của thread?** New → Runnable → Running → Blocked/Waiting → Terminated.
3. **Goroutine khác OS thread? Mô hình GMP?**
4. **Buffered và unbuffered channel khác nhau? Điều gì xảy ra khi gửi vào channel đã đóng?** Panic.
5. **Race condition là gì? Phát hiện và xử lý?** `-race`; mutex, atomic, channel.
6. **Deadlock là gì, bốn điều kiện, cách tránh?**
7. **Mutex vs RWMutex?** RWMutex cho phép nhiều reader đồng thời.
8. **WaitGroup dùng thế nào? Lỗi hay gặp?** `Add` trước khi `go`, `Done` bằng defer, `Wait` để chờ.
9. **Context dùng để làm gì?** Hủy, timeout, deadline, giá trị theo request.
10. **Connection pool là gì? Cấu hình trong Go?** Xem phần trên; nêu được hậu quả khi quên `rows.Close()`.
11. **Sync vs async? Go xử lý async thế nào?** Goroutine + channel thay cho async/await.

## Liên quan
- [01-operating-systems.md](01-operating-systems.md): process, thread, scheduler.
- [03-go-basics.md](03-go-basics.md): map không an toàn đồng thời.
- [10-databases.md](10-databases.md): transaction và connection pool phía DB.
- [11-unit-testing.md](11-unit-testing.md): `go test -race`.
