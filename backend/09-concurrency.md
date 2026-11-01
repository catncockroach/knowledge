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

## Câu hỏi

**Concurrency khác parallelism?**
> - **Concurrency (đồng thời)**: cách *cấu trúc* chương trình thành nhiều việc độc lập, tiến triển xen kẽ nhau.
> - **Parallelism (song song)**: nhiều việc *thực sự chạy cùng một thời điểm* trên nhiều lõi CPU.
>
> Concurrency là thuộc tính của *thiết kế*, parallelism là thuộc tính của *lúc chạy*. Một CPU một lõi vẫn chạy được chương trình concurrent bằng cách chuyển qua lại giữa các việc (vd server xử lý request khác trong lúc chờ DB). Có nhiều lõi thì chương trình concurrent *có thể* chạy song song. Câu của Rob Pike: "Concurrency is about dealing with lots of things at once. Parallelism is about doing lots of things at once."
>
> Ranh giới: việc chủ yếu chờ I/O được lợi từ concurrency kể cả một lõi; việc nặng CPU chỉ nhanh lên khi có parallelism. Trong Go, `GOMAXPROCS` (mặc định bằng số lõi) quyết định tối đa bao nhiêu goroutine chạy song song.

**Vòng đời của thread?**
> - **Thread**: luồng thực thi được OS lập lịch, xem [01-operating-systems.md](01-operating-systems.md).
> - **Scheduler**: thành phần quyết định thread nào chạy trên CPU.
>
> Thread đi qua các trạng thái: **New** (đã tạo, chưa chạy) → **Runnable** (sẵn sàng, chờ CPU) → **Running** (đang chạy) → khi chờ I/O, chờ lock, sleep thì sang **Blocked/Waiting** và quay về Runnable khi điều kiện xong; hết time slice thì từ Running về Runnable → **Terminated** khi hàm của thread kết thúc. Chỉ thread Runnable mới được scheduler chọn chạy.
>
> Ranh giới: tên và số trạng thái khác nhau theo OS và ngôn ngữ (Java có thêm `TIMED_WAITING`). Goroutine có vòng đời tương tự (runnable, running, waiting) nhưng do runtime Go quản lý, không phải OS.

**Goroutine khác OS thread? Mô hình GMP?**
> - **Goroutine**: hàm chạy đồng thời do runtime Go quản lý, tạo bằng `go f()`.
> - **GMP**: mô hình scheduler của Go: **G** là goroutine, **M** (machine) là OS thread, **P** (processor) là tài nguyên lập lịch logic giữ hàng đợi goroutine; số P bằng `GOMAXPROCS`.
>
> Goroutine rẻ hơn OS thread nhiều bậc: stack khởi đầu chỉ vài KB và tự giãn (thread thường cố định cỡ MB), tạo và chuyển đổi diễn ra ở user space không cần vào kernel. Nhờ vậy một chương trình chạy được hàng trăm nghìn goroutine. Runtime ghép M:N: nhiều G chạy trên ít M; mỗi M phải giữ một P mới chạy được G; P lấy G từ hàng đợi riêng, hết thì "đánh cắp" (work stealing) từ P khác. Khi G gọi system call chặn, M bị giữ lại và P được trao cho M khác để các G còn lại vẫn chạy.
>
> Ranh giới: goroutine rẻ nhưng không miễn phí; goroutine bị chặn vĩnh viễn (chờ channel không ai gửi) là rò rỉ bộ nhớ. Goroutine không có ID hay cách giết từ bên ngoài; dừng nó bằng context hoặc channel.

**Buffered và unbuffered channel khác nhau? Điều gì xảy ra khi gửi vào channel đã đóng?**
> - **Channel**: ống truyền dữ liệu có kiểu giữa các goroutine, vừa truyền dữ liệu vừa đồng bộ.
> - **Unbuffered channel** (`make(chan T)`): không có chỗ chứa. **Buffered channel** (`make(chan T, n)`): chứa được tối đa n phần tử.
>
> Quy tắc: gửi chặn khi channel *không còn chỗ*, nhận chặn khi channel *không có gì*. Với unbuffered, không bao giờ có chỗ, nên gửi chặn tới khi có người nhận: hai bên gặp nhau, là điểm đồng bộ. Với buffered, gửi không chặn khi buffer chưa đầy, nên hai bên tách rời về thời gian, dùng làm hàng đợi hoặc giới hạn số việc đồng thời.
>
> Hành vi với channel đã đóng: *gửi* thì panic; *nhận* thì lấy nốt dữ liệu còn trong buffer, sau đó trả zero value ngay lập tức với `ok == false` (`v, ok := <-ch`), và `for range ch` kết thúc. Đóng channel đã đóng cũng panic. Vì vậy chỉ *bên gửi* được đóng channel, và chỉ khi không còn ai gửi nữa. Channel nil thì gửi và nhận đều chặn mãi mãi.

**Race condition là gì? Phát hiện và xử lý?**
> - **Data race**: hai goroutine truy cập cùng một biến đồng thời, ít nhất một bên ghi, và không có đồng bộ.
> - **Race condition**: kết quả chương trình phụ thuộc vào thứ tự chạy không kiểm soát được của các goroutine.
>
> Ví dụ: hai goroutine cùng `counter++`. Lệnh này là ba bước (đọc, cộng, ghi), hai goroutine cùng đọc 5 rồi cùng ghi 6, mất một lần tăng. Phát hiện bằng race detector: `go test -race`, `go run -race`, nó báo chính xác hai chỗ truy cập xung đột. Xử lý theo một trong ba cách: bảo vệ bằng `sync.Mutex`, dùng thao tác nguyên tử `sync/atomic` cho biến đơn, hoặc không chia sẻ biến mà truyền dữ liệu qua channel ("Don't communicate by sharing memory; share memory by communicating").
>
> Ranh giới: race detector chỉ thấy race *xảy ra* trong lần chạy đó, nên cần test có tải đồng thời thực. Không có data race vẫn có thể có race condition ở mức logic, vd kiểm tra rồi mới hành động (check-then-act) giữa hai thao tác đều có khóa riêng; database cũng có dạng này, xem [10-databases.md](10-databases.md).

**Deadlock là gì, bốn điều kiện, cách tránh?**
> - **Deadlock**: một nhóm goroutine/thread chờ nhau vĩnh viễn, mỗi bên giữ tài nguyên bên kia cần.
>
> Bốn điều kiện Coffman, deadlock chỉ xảy ra khi có *đủ cả bốn*:
> 1. **Mutual exclusion**: tài nguyên chỉ một bên dùng tại một thời điểm.
> 2. **Hold and wait**: đang giữ tài nguyên này vẫn chờ tài nguyên khác.
> 3. **No preemption**: không thể cưỡng đoạt tài nguyên đang bị giữ.
> 4. **Circular wait**: tồn tại vòng chờ A chờ B, B chờ A.
>
> Tránh bằng cách phá một điều kiện: lấy khóa theo *cùng một thứ tự* ở mọi nơi (phá circular wait, cách phổ biến nhất); lấy mọi khóa cần thiết một lần hoặc dùng try-lock với timeout (phá hold and wait); giữ khóa trong thời gian ngắn nhất và không gọi hàm lạ khi đang giữ khóa.
>
> Ranh giới trong Go: khi *mọi* goroutine đều bị chặn, runtime báo `fatal error: all goroutines are asleep - deadlock!`; nhưng nếu còn goroutine khác chạy (vd HTTP server) thì deadlock cục bộ không bị phát hiện, chỉ thấy request treo. Lỗi Go hay gặp: gửi vào unbuffered channel mà không ai nhận, quên `Unlock`, `Lock` hai lần cùng một mutex (mutex Go không reentrant).

**Mutex vs RWMutex?**
> - **Mutex** (`sync.Mutex`): khóa loại trừ: tại một thời điểm chỉ một goroutine giữ được, dù đọc hay ghi.
> - **RWMutex** (`sync.RWMutex`): khóa hai chế độ: nhiều goroutine cùng giữ khóa *đọc* (`RLock`), hoặc một goroutine giữ khóa *ghi* (`Lock`) độc quyền.
>
> Tiêu chí chọn là *tỷ lệ đọc/ghi và thời gian giữ khóa*. Đọc rất nhiều, ghi hiếm, và phần đọc đủ lâu (vd cache cấu hình) thì RWMutex cho các reader chạy song song. Còn lại dùng Mutex: đơn giản hơn và chi phí mỗi lần lấy khóa thấp hơn; với vùng găng ngắn, RWMutex có thể chậm hơn Mutex.
>
> Ranh giới: không nâng cấp từ khóa đọc lên khóa ghi được (giữ `RLock` rồi gọi `Lock` là deadlock). Mutex không được copy sau khi dùng, nên struct chứa mutex phải truyền bằng pointer; `go vet` cảnh báo trường hợp này. Với map đọc nhiều có `sync.Map` cho vài trường hợp đặc thù.

**WaitGroup dùng thế nào? Lỗi hay gặp?**
> - **WaitGroup** (`sync.WaitGroup`): bộ đếm để một goroutine chờ một nhóm goroutine khác làm xong.
>
> Ba thao tác: `Add(n)` tăng bộ đếm số việc, `Done()` giảm một khi một việc xong, `Wait()` chặn tới khi bộ đếm về 0.
>
> ```go
> var wg sync.WaitGroup
> for _, u := range urls {
>     wg.Add(1)            // trước khi chạy goroutine
>     go func() {
>         defer wg.Done()  // chạy kể cả khi panic hay return sớm
>         fetch(u)
>     }()
> }
> wg.Wait()
> ```
>
> Lỗi hay gặp: gọi `Add` *bên trong* goroutine (có thể `Wait` chạy trước khi `Add` kịp chạy, chờ thiếu); quên `Done` ở một nhánh return (treo mãi), nên luôn `defer wg.Done()`; truyền WaitGroup theo value (copy, `Done` giảm bản copy). Ranh giới: WaitGroup chỉ chờ, không thu lỗi; cần lỗi đầu tiên và hủy các việc còn lại thì dùng `errgroup` (`golang.org/x/sync/errgroup`). Từ Go 1.25 có thêm `wg.Go(func)` gộp `Add` và `Done`.

**Context dùng để làm gì?**
> - **Context** (`context.Context`): giá trị truyền dọc theo chuỗi lời gọi của *một request*, mang tín hiệu hủy, deadline và một ít dữ liệu theo request.
>
> Context giải bài toán: khi request bị hủy (client ngắt kết nối, quá thời gian) thì mọi việc nó sinh ra (query DB, gọi API khác, goroutine con) phải dừng theo, không chạy phí. Tạo context con bằng `context.WithCancel`, `WithTimeout`, `WithDeadline`; hủy cha thì mọi con bị hủy. Hàm nhận context theo dõi `ctx.Done()` và trả `ctx.Err()`; thư viện như `database/sql`, `net/http` đã hỗ trợ sẵn.
>
> Quy ước: `ctx` là tham số đầu tiên, không lưu trong struct; luôn `defer cancel()` để giải phóng timer. Ranh giới: `context.WithValue` chỉ dành cho dữ liệu theo request như request ID, trace ID, không dùng để truyền tham số tùy chọn hay dependency. Context không tự dừng goroutine; goroutine phải chủ động kiểm tra nó.

**Connection pool là gì? Cấu hình trong Go?**
> - **Connection pool**: tập kết nối (DB, HTTP) được mở sẵn và cho mượn lại, thay vì mở kết nối mới cho mỗi request.
>
> Lý do: mở kết nối tốn kém (bắt tay TCP, TLS, xác thực), còn DB chỉ chịu được số kết nối có hạn. Pool tái sử dụng kết nối và giới hạn tổng số; request phải chờ khi pool cạn. Trong Go, `*sql.DB` *chính là* pool, an toàn khi dùng đồng thời, nên tạo một lần và dùng chung. Cấu hình bằng `SetMaxOpenConns` (tối đa kết nối đồng thời), `SetMaxIdleConns` (số kết nối rảnh giữ lại), `SetConnMaxLifetime` và `SetConnMaxIdleTime` (làm mới kết nối định kỳ); code ở phần *Connection pool* của file này.
>
> Hậu quả khi quên `rows.Close()` hoặc không commit/rollback transaction: kết nối không được trả về pool; sau vài trăm request pool cạn, mọi request mới treo chờ kết nối dù DB vẫn rảnh. Ranh giới: tổng `MaxOpenConns` của mọi instance service cộng lại phải nhỏ hơn giới hạn kết nối của DB. `http.Client` cũng có pool riêng, cần đọc hết và `Close()` body response để kết nối được tái sử dụng.

**Sync vs async? Go xử lý async thế nào?**
> - **Synchronous (đồng bộ)**: bên gọi chờ thao tác xong mới làm tiếp.
> - **Asynchronous (bất đồng bộ)**: bên gọi khởi động thao tác rồi làm việc khác, nhận kết quả sau (qua callback, promise/future, channel).
> - **Blocking / non-blocking**: thao tác có chặn luồng đang chạy hay không.
>
> Nhiều ngôn ngữ (JavaScript, C#, Python) dùng `async/await` để một luồng phục vụ nhiều việc mà không bị chặn khi chờ I/O. Go chọn cách khác: code viết *đồng bộ, blocking* bình thường, chạy trong goroutine; khi goroutine chờ I/O, runtime tự chuyển sang goroutine khác (dùng epoll/kqueue bên dưới). Muốn chạy song song thì `go f()`, nhận kết quả qua channel, chờ nhóm việc bằng `WaitGroup` hoặc `errgroup`.
>
> Ranh giới: vì vậy Go không có "function coloring" (hàm async và hàm thường không gọi lẫn nhau được). Ở mức kiến trúc, "async" còn có nghĩa là xử lý qua message queue: API trả 202 Accepted ngay, worker xử lý sau.

## Liên quan
- [01-operating-systems.md](01-operating-systems.md): process, thread, scheduler.
- [03-go-basics.md](03-go-basics.md): map không an toàn đồng thời.
- [10-databases.md](10-databases.md): transaction và connection pool phía DB.
- [11-unit-testing.md](11-unit-testing.md): `go test -race`.
