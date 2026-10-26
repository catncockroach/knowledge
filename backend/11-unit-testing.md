# Unit testing

> Unit test là đoạn code tự động kiểm tra một đơn vị nhỏ (hàm, method) cho ra kết quả đúng với từng input, chạy nhanh và độc lập với DB, mạng. Nó là lưới an toàn cho phép sửa và refactor code mà không sợ phá vỡ thứ đang chạy.

## Tại sao cần biết
Yêu cầu entry level: hiểu khái niệm unit test và viết unit test theo hướng dẫn; thành thạo hơn là thiết kế code để test được. Interview hay hỏi: unit test vs integration test, mock là gì, table-driven test trong Go, coverage bao nhiêu là đủ, test một hàm gọi DB thế nào.

## Khái niệm cốt lõi

### Các loại test (test pyramid)
```
          /\        E2E / UI test: ít, chậm, giả lập người dùng thật
         /  \
        /────\      Integration test: kiểm tra nhiều thành phần thật nối với nhau (code + DB thật)
       /      \
      /────────\    Unit test: nhiều, nhanh, cô lập từng hàm
```
| | Unit | Integration | End-to-end |
|---|---|---|---|
| Phạm vi | Một hàm/struct | Nhiều module + hạ tầng thật (DB, queue) | Toàn hệ thống qua API/UI |
| Tốc độ | Mili giây | Giây | Phút |
| Phụ thuộc ngoài | Thay bằng test double | Thật (thường chạy trong container) | Thật |
| Khi hỏng | Chỉ ra chính xác chỗ lỗi | Lỗi ở chỗ ghép nối | Biết là hỏng, khó biết vì sao |

Ngoài ra: **regression test** (bảo đảm bug cũ không quay lại), **smoke test**, **load/performance test**, **acceptance test** (UAT).

### Unit test tốt (FIRST)
- **Fast**: chạy nhanh để chạy thường xuyên.
- **Independent**: không phụ thuộc thứ tự, không chia sẻ trạng thái giữa các test.
- **Repeatable**: chạy bao nhiêu lần, ở máy nào cũng cùng kết quả (không phụ thuộc giờ hệ thống, mạng, dữ liệu ngẫu nhiên không kiểm soát).
- **Self-validating**: tự báo pass/fail, không cần người đọc log.
- **Timely**: viết cùng lúc với code (hoặc trước, theo TDD).

Cấu trúc mỗi test theo **AAA**: **Arrange** (chuẩn bị dữ liệu, dependency) → **Act** (gọi hàm cần test) → **Assert** (kiểm tra kết quả). Hoặc Given–When–Then.

Nên test: luồng đúng (happy path), **trường hợp biên** (rỗng, 0, âm, giá trị lớn nhất, nil, chuỗi Unicode), luồng lỗi (dependency trả lỗi, input sai).

### Test double
Khi hàm cần test phụ thuộc DB, API ngoài, thời gian, ta thay dependency bằng bản giả:
| Loại | Ý nghĩa |
|---|---|
| **Dummy** | Truyền cho đủ tham số, không dùng tới |
| **Stub** | Trả về dữ liệu cố định đã định sẵn |
| **Fake** | Cài đặt đơn giản nhưng chạy được (repository lưu trong map thay vì DB) |
| **Spy** | Stub có ghi lại cách nó được gọi (bao nhiêu lần, tham số gì) |
| **Mock** | Đặt kỳ vọng trước về lời gọi và tự kiểm tra kỳ vọng đó |
Trong giao tiếp hằng ngày, mọi loại thường được gọi chung là "mock".

### Thiết kế code để test được
Code khó test thường là code:
- Tự tạo dependency bên trong (`sql.Open` trong hàm nghiệp vụ), dùng biến toàn cục/singleton.
- Gọi trực tiếp `time.Now()`, `rand`, `os.Getenv` giữa logic.
- Trộn I/O với tính toán trong một hàm dài.

Cách sửa: phụ thuộc vào **interface nhỏ**, nhận dependency qua constructor (**Dependency Injection**, xem [07-design-patterns.md](07-design-patterns.md)), tách logic thuần (pure function: cùng input luôn cùng output, không side effect) khỏi phần I/O, truyền thời gian vào như một dependency (`now func() time.Time`).

### Test trong Go
- File test đặt cạnh code, tên kết thúc `_test.go`; hàm test có dạng `func TestXxx(t *testing.T)`.
- `t.Errorf` báo lỗi và chạy tiếp; `t.Fatalf` báo lỗi và dừng test hiện tại. `t.Run` tạo subtest. `t.Helper()` đánh dấu hàm hỗ trợ để báo đúng dòng. `t.Cleanup` dọn dẹp. `t.Parallel()` chạy song song.
- Package test: cùng package (`package user`, test được hàm unexported) hoặc `package user_test` (chỉ test API public, như người dùng thật).
- Thư viện hay dùng: `testify` (`assert`, `require`, `mock`), `gomock`/`mockery` (sinh mock từ interface), `httptest` (chuẩn: giả lập HTTP server/request), `testcontainers-go` (DB thật trong Docker cho integration test).

```bash
go test ./...                    # mọi package
go test -v -run TestAdd ./calc   # chạy test khớp tên, in chi tiết
go test -race ./...              # phát hiện data race
go test -cover ./...             # % coverage
go test -coverprofile=c.out ./... && go tool cover -html=c.out
go test -bench=. -benchmem       # benchmark
```

## Cách hoạt động
`go test` biên dịch package cùng các file `_test.go` thành một binary test tạm, chạy mọi hàm `TestXxx`, tổng hợp kết quả; exit code khác 0 nếu có test fail. Trong CI, bước này chặn merge khi test hỏng. Kết quả test của package không đổi được cache; thêm `-count=1` để buộc chạy lại.

## Ví dụ

### Table-driven test (phong cách chuẩn của Go)
```go
// calc.go
func Discount(total int64, isVIP bool) int64 {
    switch {
    case total <= 0:
        return 0
    case isVIP && total >= 1_000_000:
        return total * 10 / 100
    case total >= 1_000_000:
        return total * 5 / 100
    default:
        return 0
    }
}

// calc_test.go
func TestDiscount(t *testing.T) {
    tests := []struct {
        name  string
        total int64
        vip   bool
        want  int64
    }{
        {"zero total", 0, false, 0},
        {"negative total", -100, true, 0},
        {"below threshold", 999_999, true, 0},
        {"normal at threshold", 1_000_000, false, 50_000},
        {"vip at threshold", 1_000_000, true, 100_000},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Discount(tt.total, tt.vip)
            if got != tt.want {
                t.Errorf("Discount(%d, %v) = %d, want %d", tt.total, tt.vip, got, tt.want)
            }
        })
    }
}
```
Thêm một trường hợp chỉ cần thêm một dòng; tên subtest giúp biết ngay ca nào hỏng. Chú ý các ca biên quanh ngưỡng `999_999` và `1_000_000`.

### Test service với fake repository
```go
// service.go
type UserRepository interface {
    FindByEmail(ctx context.Context, email string) (User, error)
    Create(ctx context.Context, u User) error
}

var ErrEmailTaken = errors.New("email taken")

type UserService struct{ repo UserRepository }

func (s *UserService) Register(ctx context.Context, email string) error {
    _, err := s.repo.FindByEmail(ctx, email)
    if err == nil {
        return ErrEmailTaken
    }
    if !errors.Is(err, ErrNotFound) {
        return fmt.Errorf("find: %w", err)
    }
    return s.repo.Create(ctx, User{Email: email})
}

// service_test.go
type fakeRepo struct {
    users   map[string]User
    findErr error // để giả lập lỗi DB
}

func (f *fakeRepo) FindByEmail(_ context.Context, email string) (User, error) {
    if f.findErr != nil {
        return User{}, f.findErr
    }
    u, ok := f.users[email]
    if !ok {
        return User{}, ErrNotFound
    }
    return u, nil
}

func (f *fakeRepo) Create(_ context.Context, u User) error {
    f.users[u.Email] = u
    return nil
}

func TestRegister(t *testing.T) {
    ctx := context.Background()

    t.Run("new email is created", func(t *testing.T) {
        repo := &fakeRepo{users: map[string]User{}}
        svc := &UserService{repo: repo}

        if err := svc.Register(ctx, "a@x.com"); err != nil {
            t.Fatalf("unexpected error: %v", err)
        }
        if _, ok := repo.users["a@x.com"]; !ok {
            t.Error("user was not saved")
        }
    })

    t.Run("duplicate email is rejected", func(t *testing.T) {
        repo := &fakeRepo{users: map[string]User{"a@x.com": {Email: "a@x.com"}}}
        svc := &UserService{repo: repo}

        err := svc.Register(ctx, "a@x.com")
        if !errors.Is(err, ErrEmailTaken) {
            t.Fatalf("got %v, want ErrEmailTaken", err)
        }
    })

    t.Run("db error is propagated", func(t *testing.T) {
        dbErr := errors.New("connection refused")
        svc := &UserService{repo: &fakeRepo{findErr: dbErr}}

        if err := svc.Register(ctx, "a@x.com"); !errors.Is(err, dbErr) {
            t.Fatalf("got %v, want wrapped dbErr", err)
        }
    })
}
```

### Test HTTP handler với httptest
```go
func TestHealthHandler(t *testing.T) {
    req := httptest.NewRequest(http.MethodGet, "/health", nil)
    rec := httptest.NewRecorder()

    HealthHandler(rec, req)

    if rec.Code != http.StatusOK {
        t.Fatalf("status = %d, want 200", rec.Code)
    }
    if got := rec.Body.String(); got != `{"status":"ok"}` {
        t.Errorf("body = %s", got)
    }
}
```

### Benchmark
```go
func BenchmarkDiscount(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Discount(1_500_000, true)
    }
}
```

## TDD (Test-Driven Development)
Chu trình **Red → Green → Refactor**: viết test thất bại trước (red), viết code tối thiểu cho pass (green), rồi dọn code với test bảo vệ (refactor). Lợi ích: buộc nghĩ về hành vi và giao diện trước, code sinh ra tự nhiên dễ test.

## Hiểu nhầm thường gặp
- **"Coverage 100% là code không có bug"**: coverage chỉ đo dòng nào được chạy, không đo assert có đúng không. Coverage cao vẫn có thể thiếu ca biên. Dùng coverage để tìm chỗ chưa test, không phải làm mục tiêu tuyệt đối.
- **"Unit test gọi DB thật"**: đó là integration test. Unit test thay DB bằng fake/mock; integration test riêng để kiểm tra SQL thật.
- **"Mock càng nhiều càng tốt"**: mock quá chi tiết (kiểm tra từng lời gọi nội bộ) làm test gãy mỗi lần refactor dù hành vi không đổi. Test hành vi đầu ra, không test cách cài đặt.
- **"Test chỉ cần happy path"**: bug thường nằm ở ca biên và luồng lỗi.

## Câu hỏi ôn tập
1. **Unit test là gì? Khác integration test, E2E?** Xem test pyramid.
2. **Mock, stub, fake khác nhau?**
3. **Viết code thế nào để dễ unit test?** Interface, DI, pure function, không gọi trực tiếp thời gian/DB trong logic.
4. **Table-driven test là gì? Vì sao Go chuộng nó?**
5. **Coverage là gì? Bao nhiêu là đủ?** Không có con số tuyệt đối; ưu tiên phủ logic nghiệp vụ quan trọng và ca biên.
6. **TDD là gì?**
7. **Test hàm gọi DB/API ngoài thế nào?** Tách sau interface, dùng fake/mock cho unit test; integration test với DB thật trong container.

## Liên quan
- [07-design-patterns.md](07-design-patterns.md): Dependency Injection.
- [08-clean-code-and-solid.md](08-clean-code-and-solid.md): test là lưới an toàn khi refactor.
- [09-concurrency.md](09-concurrency.md): `-race`.
- [14-debugging.md](14-debugging.md): viết test tái hiện bug trước khi sửa.
