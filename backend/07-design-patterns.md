# Design patterns

> Design pattern là lời giải đã được đặt tên cho những bài toán thiết kế lặp đi lặp lại. Nó không phải đoạn code copy được, mà là một ý tưởng tổ chức code giúp đội ngũ nói chung một ngôn ngữ ("chỗ này dùng Factory", "bọc bằng Adapter").

## Tại sao cần biết
Yêu cầu entry level: hiểu các pattern cơ bản nhóm Creational (Singleton, Factory) và Structural (Adapter). Thực tế dự án Go còn dùng rất nhiều Dependency Injection, Functional Options, Decorator (middleware), Strategy. Interviewer thường hỏi: "Singleton cài thế nào cho thread-safe?", "Factory giải quyết gì?", "cho ví dụ Adapter trong dự án", "DI là gì, lợi ích?".

## Khái niệm cốt lõi

### Ba nhóm pattern (theo sách "Design Patterns" của Gang of Four)
| Nhóm | Giải quyết | Ví dụ |
|---|---|---|
| **Creational** (khởi tạo) | Tạo object thế nào cho linh hoạt, ẩn chi tiết khởi tạo | Singleton, Factory Method, Abstract Factory, Builder, Prototype |
| **Structural** (cấu trúc) | Ghép các object/kiểu thành cấu trúc lớn hơn | Adapter, Decorator, Facade, Proxy, Composite, Bridge |
| **Behavioral** (hành vi) | Phân chia trách nhiệm và cách các object giao tiếp | Strategy, Observer, Command, Iterator, Template Method, Chain of Responsibility |

Trong Go, nhiều pattern trở nên rất gọn nhờ interface ngầm định, hàm là giá trị hạng nhất và closure.

### Singleton
**Vấn đề**: cần đúng **một** instance dùng chung cho cả ứng dụng (config, logger, connection pool) và một điểm truy cập toàn cục.

**Cài đặt thread-safe trong Go** bằng `sync.Once`: đảm bảo hàm khởi tạo chạy đúng một lần dù nhiều goroutine gọi cùng lúc.
```go
type Config struct{ DSN string }

var (
    cfg  *Config
    once sync.Once
)

func GetConfig() *Config {
    once.Do(func() {
        cfg = &Config{DSN: os.Getenv("DB_DSN")}
    })
    return cfg
}
```
Cách sai (race condition):
```go
func GetConfigBad() *Config {
    if cfg == nil {          // hai goroutine cùng thấy nil
        cfg = &Config{}      // → tạo hai instance, và là data race
    }
    return cfg
}
```
**Nhược điểm**: là trạng thái toàn cục ẩn, khó test (không thay bằng bản giả được), tạo phụ thuộc ngầm. Trong Go hiện đại, thường ưu tiên **tạo một lần ở `main` rồi truyền vào** (Dependency Injection) thay vì Singleton toàn cục. Biết Singleton để trả lời, nhưng nêu được nhược điểm sẽ ghi điểm.

### Factory
**Vấn đề**: code dùng object không nên biết chi tiết tạo object cụ thể nào; logic chọn loại nằm một chỗ.

**Simple factory / constructor** (phổ biến nhất trong Go): hàm `NewX` trả về object đã khởi tạo hợp lệ, kiểm tra tham số.
```go
func NewServer(addr string, timeout time.Duration) (*Server, error) {
    if addr == "" {
        return nil, errors.New("addr required")
    }
    return &Server{addr: addr, timeout: timeout}, nil
}
```

**Factory trả về interface**: chọn implementation theo tham số/cấu hình.
```go
type Storage interface {
    Save(ctx context.Context, key string, data []byte) error
}

type LocalStorage struct{ dir string }
type S3Storage struct{ bucket string }

func (l *LocalStorage) Save(ctx context.Context, key string, data []byte) error { return nil }
func (s *S3Storage) Save(ctx context.Context, key string, data []byte) error    { return nil }

func NewStorage(kind string) (Storage, error) {
    switch kind {
    case "local":
        return &LocalStorage{dir: "/data"}, nil
    case "s3":
        return &S3Storage{bucket: "my-bucket"}, nil
    default:
        return nil, fmt.Errorf("unknown storage %q", kind)
    }
}
```
Caller chỉ làm việc với `Storage`; thêm loại mới (GCS) chỉ sửa factory, không sửa nơi dùng.

**Factory Method / Abstract Factory** (dạng GoF): Factory Method để lớp con quyết định tạo object nào; Abstract Factory tạo cả một **họ** object liên quan (ví dụ bộ UI Windows vs macOS, hay bộ repository cho MySQL vs PostgreSQL).

### Builder và Functional Options
**Vấn đề**: object có nhiều tham số tùy chọn; constructor 10 tham số khó đọc, dễ truyền nhầm.

Go hay dùng **Functional Options**:
```go
type Server struct {
    addr         string
    readTimeout  time.Duration
    maxConns     int
}

type Option func(*Server)

func WithReadTimeout(d time.Duration) Option { return func(s *Server) { s.readTimeout = d } }
func WithMaxConns(n int) Option             { return func(s *Server) { s.maxConns = n } }

func NewServer(addr string, opts ...Option) *Server {
    s := &Server{addr: addr, readTimeout: 5 * time.Second, maxConns: 100} // giá trị mặc định
    for _, opt := range opts {
        opt(s)
    }
    return s
}

srv := NewServer(":8080", WithMaxConns(500))
```
Ưu điểm: có mặc định hợp lý, thêm option mới không phá API cũ, tên option tự giải thích.

### Adapter
**Vấn đề**: có một thành phần sẵn (thư viện bên thứ ba, hệ thống cũ) với interface **không khớp** với interface mà code của mình mong đợi. Adapter là lớp "chuyển đổi phích cắm" ở giữa.

```
Client ──► Target interface ──► Adapter ──► Adaptee (API có sẵn, khác chữ ký)
```

```go
// interface mà hệ thống của mình dùng
type PaymentGateway interface {
    Charge(ctx context.Context, userID string, amountVND int64) (txID string, err error)
}

// SDK bên thứ ba: chữ ký khác, đơn vị khác
type ThirdPartyClient struct{}
func (c *ThirdPartyClient) MakePayment(req ThirdPartyRequest) (*ThirdPartyResponse, error) { return nil, nil }

type ThirdPartyRequest struct {
    Customer string
    Amount   float64
    Currency string
}
type ThirdPartyResponse struct{ TransactionRef string }

// Adapter: implement PaymentGateway bằng cách gọi SDK
type ThirdPartyAdapter struct{ client *ThirdPartyClient }

func (a *ThirdPartyAdapter) Charge(ctx context.Context, userID string, amountVND int64) (string, error) {
    resp, err := a.client.MakePayment(ThirdPartyRequest{
        Customer: userID,
        Amount:   float64(amountVND),
        Currency: "VND",
    })
    if err != nil {
        return "", fmt.Errorf("third party charge: %w", err)
    }
    return resp.TransactionRef, nil
}
```
Lợi ích: nghiệp vụ không phụ thuộc SDK; đổi nhà cung cấp chỉ cần viết adapter mới. Ví dụ trong thư viện chuẩn: `http.HandlerFunc` biến một hàm thường thành `http.Handler`.

### Decorator (middleware)
**Vấn đề**: thêm hành vi (log, đo thời gian, xác thực, retry) vào một object mà không sửa nó, và có thể xếp chồng nhiều lớp.
```go
func Logging(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        next.ServeHTTP(w, r)
        slog.Info("request", "method", r.Method, "path", r.URL.Path, "dur", time.Since(start))
    })
}

handler := Logging(Auth(mux)) // xếp chồng: Logging → Auth → mux
```
Khác Adapter: Decorator **giữ nguyên** interface và thêm hành vi; Adapter **đổi** interface.

### Facade và Proxy (sơ lược)
- **Facade**: một interface đơn giản che một hệ thống con phức tạp (ví dụ `CheckoutService.Checkout()` gói các bước kiểm kho, thanh toán, tạo đơn, gửi email).
- **Proxy**: đối tượng đứng thay, cùng interface, kiểm soát truy cập tới đối tượng thật (cache proxy, lazy loading, kiểm tra quyền, gọi từ xa).

### Strategy
**Vấn đề**: nhiều cách thực hiện một việc, cần chọn lúc chạy mà không viết `if/else` dài.
```go
type DiscountStrategy interface{ Apply(total int64) int64 }

type NoDiscount struct{}
func (NoDiscount) Apply(t int64) int64 { return t }

type PercentDiscount struct{ Percent int64 }
func (p PercentDiscount) Apply(t int64) int64 { return t * (100 - p.Percent) / 100 }

func Checkout(total int64, s DiscountStrategy) int64 { return s.Apply(total) }
```
Trong Go, strategy đơn giản thường chỉ là một **hàm** truyền vào (`sort.Slice(x, less)`).

### Observer (publish/subscribe)
Một đối tượng phát sự kiện, nhiều đối tượng đăng ký nhận. Trong hệ thống phân tán, dạng lớn của nó là message queue / event bus (service A phát `OrderCreated`, service email và service kho cùng nhận).

### Dependency Injection (DI)
**Vấn đề**: nếu một struct tự tạo dependency bên trong (`repo := NewPostgresRepo()`), nó bị gắn chặt với implementation cụ thể, không test được bằng bản giả, không đổi được cấu hình.

**DI**: dependency được **truyền vào từ bên ngoài** (thường qua constructor), và kiểu của nó là interface.
```go
// Không DI: gắn chặt
type UserService struct{}
func (s *UserService) Get(id int64) (User, error) {
    repo := NewPostgresUserRepo("postgres://...") // không thay được
    return repo.Find(id)
}

// Có DI
type UserRepository interface{ Find(ctx context.Context, id int64) (User, error) }

type UserService struct{ repo UserRepository }
func NewUserService(repo UserRepository) *UserService { return &UserService{repo: repo} }

// main.go: "composition root", nơi duy nhất nối các thành phần
db := mustOpenDB()
svc := NewUserService(NewPostgresUserRepo(db))

// test: truyền bản giả
svc := NewUserService(&fakeUserRepo{users: map[int64]User{1: {ID: 1}}})
```
Lợi ích: dễ test, lỏng ràng buộc (loose coupling), đổi implementation không sửa code nghiệp vụ. DI là cách thực hiện nguyên tắc **Dependency Inversion** (chữ D trong SOLID). Go thường DI thủ công trong `main`; dự án lớn có thể dùng công cụ sinh code như Wire, hoặc framework như Fx.

### Repository
Gom toàn bộ truy cập dữ liệu của một thực thể sau một interface (`UserRepository` có `Find`, `Create`, `Update`), để tầng nghiệp vụ không chứa SQL. Đây là nền của layered architecture (xem [02-backend-architecture.md](02-backend-architecture.md)).

## Cách hoạt động
Cách chọn pattern khi thiết kế:
1. Nhận diện vấn đề trước, pattern sau. Đừng đưa pattern vào khi chưa có vấn đề nó giải quyết (over-engineering).
2. Đặt câu hỏi:
   - Khởi tạo phức tạp, nhiều biến thể? → Factory, Builder/Options.
   - Cần dùng thứ có interface không khớp? → Adapter.
   - Thêm hành vi xuyên suốt (log, auth, metrics)? → Decorator/middleware.
   - Nhiều thuật toán thay thế nhau? → Strategy.
   - Một sự kiện, nhiều nơi phản ứng? → Observer/pub-sub.
   - Cần test và đổi implementation? → Interface + DI.
3. Trong Go, ưu tiên dạng đơn giản nhất: một interface nhỏ, một hàm, một closure thường đủ.

## Ví dụ
Ghép nhiều pattern trong một luồng gửi thông báo:

```go
// Strategy/polymorphism: nhiều kênh cùng interface
type Sender interface{ Send(ctx context.Context, to, msg string) error }

// Factory: chọn kênh theo cấu hình
func NewSender(kind string) (Sender, error) { /* "email" | "sms" */ return nil, nil }

// Decorator: thêm retry mà không sửa Sender gốc
type retrySender struct {
    next     Sender
    attempts int
}

func (r *retrySender) Send(ctx context.Context, to, msg string) error {
    var err error
    for i := 0; i < r.attempts; i++ {
        if err = r.next.Send(ctx, to, msg); err == nil {
            return nil
        }
        time.Sleep(time.Duration(i+1) * 100 * time.Millisecond) // backoff
    }
    return fmt.Errorf("send after %d attempts: %w", r.attempts, err)
}

// DI: service nhận Sender từ ngoài
type AlertService struct{ sender Sender }

func main() {
    base, _ := NewSender("sms")
    svc := &AlertService{sender: &retrySender{next: base, attempts: 3}}
    _ = svc
}
```

## Hiểu nhầm thường gặp
- **"Dùng càng nhiều pattern càng tốt"**: pattern có chi phí (thêm lớp, thêm gián tiếp). Chỉ dùng khi giải quyết vấn đề có thật.
- **"Singleton là best practice"**: nó là trạng thái toàn cục; khó test và tạo phụ thuộc ẩn. DI thường tốt hơn.
- **"Adapter và Decorator giống nhau vì đều bọc object"**: Adapter đổi interface; Decorator giữ interface, thêm hành vi.
- **"DI cần framework"**: DI chỉ là truyền dependency qua tham số; framework là tùy chọn.

## Câu hỏi

**Ba nhóm design pattern? Mỗi nhóm cho 2 ví dụ.**
> - **Design pattern**: lời giải đã được đặt tên cho một vấn đề thiết kế lặp đi lặp lại; là ý tưởng, không phải đoạn code copy được.
>
> Sách của Gang of Four chia pattern theo *vấn đề chúng giải quyết*:
> - **Creational**: cách *tạo* object mà không để nơi dùng phụ thuộc vào cách tạo. Ví dụ Singleton, Factory Method, Builder.
> - **Structural**: cách *ghép* các object, kiểu với nhau thành cấu trúc lớn hơn. Ví dụ Adapter, Decorator, Facade, Proxy.
> - **Behavioral**: cách các object *phân chia trách nhiệm và giao tiếp*. Ví dụ Strategy, Observer, Chain of Responsibility.
>
> Ranh giới: Dependency Injection và Repository rất phổ biến trong backend nhưng không nằm trong 23 pattern gốc của GoF. Nhiều pattern sinh ra để bù cho hạn chế của ngôn ngữ hướng class; trong Go một số trở nên rất mỏng (Strategy chỉ là truyền một hàm hoặc interface).

**Cài Singleton thread-safe trong Go? Nhược điểm?**
> - **Singleton**: pattern đảm bảo một kiểu chỉ có *một* instance và có một điểm truy cập chung tới nó.
> - **Thread-safe**: chạy đúng khi nhiều goroutine cùng gọi đồng thời.
>
> Trong Go dùng `sync.Once`: hàm khởi tạo chỉ chạy đúng một lần dù nhiều goroutine gọi cùng lúc, các goroutine khác chờ tới khi nó xong.
>
> ```go
> var (
>     instance *Config
>     once     sync.Once
> )
>
> func GetConfig() *Config {
>     once.Do(func() { instance = loadConfig() })
>     return instance
> }
> ```
>
> Nhược điểm: singleton là *trạng thái toàn cục* trá hình: phụ thuộc bị giấu (hàm gọi `GetConfig()` bên trong, nhìn chữ ký không biết), khó thay bằng bản giả khi test, và các test ảnh hưởng nhau qua trạng thái chung. Cách thường tốt hơn là tạo object một lần trong `main` rồi truyền vào nơi cần (Dependency Injection). Kiểm tra `if instance == nil` không có khóa là sai vì race condition.

**Factory giải quyết vấn đề gì?**
> - **Factory**: hàm hoặc object chịu trách nhiệm *tạo* object, thay cho nơi dùng tự gọi constructor cụ thể.
>
> Factory tách *quyết định tạo cái gì và tạo thế nào* khỏi *nơi dùng*. Nơi dùng chỉ biết interface, factory chọn implementation dựa trên cấu hình hay tham số, vd `NewStorage(cfg)` trả về `S3Storage` hoặc `LocalStorage` dưới dạng interface `Storage`. Thêm loại storage mới chỉ sửa factory, không sửa mọi nơi dùng. Factory cũng gom logic khởi tạo phức tạp (validate, giá trị mặc định) vào một chỗ.
>
> Ranh giới: trong Go, constructor `NewXxx` chính là dạng factory đơn giản nhất. Một factory với `switch` theo loại thì mỗi khi thêm loại vẫn phải sửa `switch`; nếu loại thêm thường xuyên có thể dùng bảng đăng ký (registry) để thêm mà không sửa.

**Adapter dùng khi nào? Ví dụ?**
> - **Adapter**: lớp bọc chuyển interface của một thành phần có sẵn thành interface mà code của mình mong đợi, giống đầu chuyển phích cắm.
>
> Dùng khi phải tích hợp thứ mình *không sửa được* (thư viện ngoài, SDK, hệ thống cũ) mà interface không khớp với interface của mình. Ví dụ code định nghĩa `PaymentGateway` với `Charge(ctx, amount)`; SDK của nhà cung cấp A có `CreateTransaction(req)` với cấu trúc riêng. Viết `providerAAdapter` thỏa `PaymentGateway`, bên trong chuyển tham số và gọi SDK. Nghiệp vụ không biết SDK nào đang dùng; đổi nhà cung cấp chỉ cần adapter mới.
>
> Ranh giới: Adapter đổi *interface*; Decorator giữ nguyên interface và thêm hành vi; Facade đưa ra một interface đơn giản cho cả một hệ thống phức tạp. Adapter còn là nơi chuyển lỗi của SDK thành lỗi của miền nghiệp vụ.

**Dependency Injection là gì, lợi ích?**
> - **Dependency**: thứ một thành phần cần để làm việc (repository, client gửi email, đồng hồ).
> - **Dependency Injection (DI)**: thành phần *nhận* dependency từ bên ngoài (qua constructor, tham số) thay vì tự tạo bên trong.
>
> Quy tắc: thành phần khai báo nó cần *interface* gì, còn ai tạo và nối các phần với nhau là việc của tầng ngoài cùng (thường là `main`, gọi là composition root). Lợi ích: test dễ (truyền repository giả), lỏng ràng buộc (đổi implementation không sửa nơi dùng), phụ thuộc hiện rõ trong chữ ký constructor.
>
> ```go
> func NewOrderService(repo OrderRepository, n Notifier) *OrderService
> ```
>
> Ranh giới: DI là kỹ thuật, không bắt buộc framework; Go thường làm DI thủ công trong `main`, dự án lớn có thể dùng công cụ sinh code như Wire. Đây là cách hiện thực Dependency Inversion của SOLID, xem [08-clean-code-and-solid.md](08-clean-code-and-solid.md).

**Middleware trong HTTP server là pattern gì?**
> - **Middleware**: hàm bọc quanh một handler, chạy logic trước và/hoặc sau handler (log, xác thực, recover panic, đo thời gian).
> - **Decorator**: pattern bọc một object bằng object khác *cùng interface* để thêm hành vi mà không sửa object gốc.
> - **Chain of Responsibility**: pattern chuyển request qua một chuỗi bộ xử lý, mỗi bộ xử lý quyết định xử lý tiếp hay dừng.
>
> Middleware là Decorator: nhận `http.Handler`, trả `http.Handler`, nên bọc được nhiều lớp (`logging(auth(handler))`). Khi xếp thành chuỗi, nó cũng mang dáng Chain of Responsibility: middleware xác thực có thể trả 401 và không gọi handler kế tiếp.
>
> ```go
> func Logging(next http.Handler) http.Handler {
>     return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
>         start := time.Now()
>         next.ServeHTTP(w, r)
>         log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
>     })
> }
> ```
>
> Ranh giới: thứ tự bọc quyết định thứ tự chạy; recover nên nằm ngoài cùng, xác thực phải đứng trước handler.

**Functional options là gì?**
> - **Functional options**: cách cấu hình object trong Go bằng các hàm option truyền vào constructor dạng variadic: `NewServer(addr, WithTimeout(5*time.Second), WithTLS(cfg))`.
>
> Pattern giải bài toán: constructor có nhiều tham số tùy chọn mà Go không có tham số mặc định hay overloading. Mỗi option là một hàm sửa struct cấu hình; constructor đặt giá trị mặc định hợp lý trước rồi áp lần lượt các option. Thêm option mới không làm vỡ code đang gọi, gọi không option nào vẫn ra object dùng được, và tên option tự giải thích ý nghĩa.
>
> ```go
> type Option func(*Server)
>
> func WithTimeout(d time.Duration) Option {
>     return func(s *Server) { s.timeout = d }
> }
> ```
>
> Ranh giới: với vài tham số đơn giản, truyền một struct `Config` là đủ và dễ đọc hơn. Functional options là phiên bản Go của Builder, xem phần *Builder và Functional Options* của file này.

## Liên quan
- [04-oop-in-go.md](04-oop-in-go.md): interface và composition là nền của các pattern.
- [08-clean-code-and-solid.md](08-clean-code-and-solid.md): pattern là công cụ để đạt SOLID.
- [11-unit-testing.md](11-unit-testing.md): DI cho phép mock khi test.
