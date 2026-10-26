# Clean code and SOLID

> Clean code là code mà người khác (và chính bạn sáu tháng sau) đọc hiểu, sửa và mở rộng được với ít rủi ro nhất. SOLID là năm nguyên tắc thiết kế giúp code ít ràng buộc, dễ thay đổi. Coding convention là bộ quy ước chung để cả team viết code đồng nhất.

## Tại sao cần biết
Code được đọc nhiều hơn được viết rất nhiều lần. Yêu cầu entry level: code rõ ràng trong sáng, nắm nguyên tắc SOLID, áp dụng và tuân thủ coding convention. Interview hay hỏi: "giải thích SOLID kèm ví dụ", "thế nào là code sạch", "review đoạn code này có vấn đề gì". Trong công việc, code review sẽ soi đúng những điểm này.

## Khái niệm cốt lõi

### Nguyên tắc clean code
**Đặt tên**
- Tên nói lên ý định: `elapsedDays` thay vì `d`, `isExpired` thay vì `flag`.
- Hàm là động từ (`CalculateTotal`, `SendEmail`), kiểu là danh từ (`Invoice`, `OrderRepository`), bool là câu hỏi (`isValid`, `hasPermission`).
- Phạm vi càng nhỏ, tên càng ngắn được: `i` trong vòng lặp 3 dòng là ổn; biến package-level cần tên đầy đủ.
- Tránh tên mơ hồ: `data`, `info`, `manager`, `util`, `helper`.

**Hàm**
- Ngắn, làm **một việc** và làm tốt việc đó. Nếu phải dùng chữ "và" để mô tả hàm, có lẽ nên tách.
- Ít tham số (≤ 3–4); nhiều hơn thì gom thành struct.
- Một mức trừu tượng trong một hàm: không trộn logic nghiệp vụ cấp cao với chi tiết parse byte.
- Tránh side effect bất ngờ: hàm tên `GetUser` không nên ghi DB.

**Luồng điều khiển**
- **Early return / guard clause** thay vì `if` lồng sâu:
```go
// Khó đọc
func process(o *Order) error {
    if o != nil {
        if o.Paid {
            if len(o.Items) > 0 {
                return ship(o)
            }
        }
    }
    return errors.New("cannot ship")
}

// Dễ đọc
func process(o *Order) error {
    if o == nil {
        return errors.New("nil order")
    }
    if !o.Paid {
        return errors.New("order not paid")
    }
    if len(o.Items) == 0 {
        return errors.New("empty order")
    }
    return ship(o)
}
```
- Thay "magic number" bằng hằng số có tên: `const maxRetries = 3`.

**Comment**
- Code nên tự giải thích **cái gì**; comment giải thích **vì sao** (ràng buộc nghiệp vụ, lý do chọn cách làm lạ).
- Comment sai còn tệ hơn không có comment. Xóa code chết thay vì comment nó lại (đã có Git).
- Go: mọi định danh exported nên có **doc comment** bắt đầu bằng chính tên đó: `// NewServer creates ...`.

**Các nguyên tắc ngắn**
- **DRY** (Don't Repeat Yourself): mỗi tri thức có một nơi duy nhất. Nhưng đừng gộp hai đoạn code chỉ *trông* giống nhau mà mang ý nghĩa khác nhau.
- **KISS** (Keep It Simple, Stupid): chọn lời giải đơn giản nhất đủ dùng.
- **YAGNI** (You Aren't Gonna Need It): đừng xây cho nhu cầu tưởng tượng.
- **Boy Scout rule**: để code sạch hơn lúc bạn đến.
- **Separation of concerns**: mỗi phần lo một mối quan tâm (handler lo HTTP, service lo nghiệp vụ, repository lo dữ liệu).
- **Fail fast**: kiểm tra input sớm, báo lỗi rõ ràng.

### SOLID
| Chữ | Nguyên tắc | Ý chính |
|---|---|---|
| **S** | Single Responsibility | Một module chỉ có **một lý do để thay đổi** |
| **O** | Open/Closed | **Mở để mở rộng, đóng để sửa đổi**: thêm tính năng bằng code mới, không sửa code cũ đã chạy ổn |
| **L** | Liskov Substitution | Kiểu con phải **thay thế được** kiểu cha mà không làm sai chương trình |
| **I** | Interface Segregation | Nhiều interface nhỏ, chuyên biệt tốt hơn một interface lớn; client không bị buộc phụ thuộc method nó không dùng |
| **D** | Dependency Inversion | Module cấp cao và cấp thấp đều **phụ thuộc vào abstraction**, không phụ thuộc nhau trực tiếp |

**S: Single Responsibility**
```go
// Vi phạm: một struct vừa tính toán, vừa format, vừa ghi file
type Report struct{}
func (r *Report) Calculate() {}
func (r *Report) ToPDF() []byte { return nil }
func (r *Report) SaveToDisk(path string) error { return nil }

// Tách: thay đổi định dạng PDF không đụng tới logic tính toán
type ReportCalculator struct{}
type PDFRenderer struct{}
type FileStore struct{}
```
"Một lý do để thay đổi" nghĩa là một nhóm người/yêu cầu nghiệp vụ có thể đòi sửa nó (kế toán đổi công thức vs bộ phận thiết kế đổi mẫu PDF).

**O: Open/Closed**
```go
// Vi phạm: thêm phương thức thanh toán mới phải sửa hàm này
func Pay(method string, amount int64) error {
    switch method {
    case "card":   // ...
    case "wallet": // ...
    }
    return nil
}

// Tuân thủ: thêm loại mới = thêm một kiểu implement interface
type PaymentMethod interface{ Pay(ctx context.Context, amount int64) error }
type Card struct{}
type Wallet struct{}
type BankTransfer struct{} // mở rộng, không sửa code cũ

func Checkout(ctx context.Context, m PaymentMethod, amount int64) error { return m.Pay(ctx, amount) }
```

**L: Liskov Substitution**
- Ví dụ kinh điển: `Square` kế thừa `Rectangle`; đặt chiều rộng của hình vuông thì chiều cao đổi theo, nên code giả định "đặt rộng không ảnh hưởng cao" bị sai → vi phạm LSP.
- Trong Go: mọi implementation của một interface phải giữ đúng **hợp đồng** của nó. Một `Storage.Save` mà implementation "read-only" lại panic thay vì trả lỗi là vi phạm; caller không thể thay thế an toàn. `io.Reader` có hợp đồng rõ: trả `io.EOF` khi hết dữ liệu; implementation nào làm khác sẽ phá các hàm như `io.ReadAll`.

**I: Interface Segregation**
```go
// Vi phạm: interface "béo", ai implement cũng phải viết đủ 6 method
type Repository interface {
    Create(); Update(); Delete(); FindByID(); Search(); ExportCSV()
}

// Tuân thủ: tách nhỏ, ghép khi cần
type UserReader interface { FindByID(ctx context.Context, id int64) (User, error) }
type UserWriter interface { Create(ctx context.Context, u User) error }
type UserReadWriter interface { UserReader; UserWriter }

// Service chỉ đọc thì chỉ phụ thuộc UserReader → mock dễ hơn nhiều
type ProfileService struct{ users UserReader }
```
Go rất hợp ISP: thư viện chuẩn đầy interface một method (`io.Reader`, `io.Writer`, `io.Closer`, `fmt.Stringer`). "The bigger the interface, the weaker the abstraction."

**D: Dependency Inversion**
```
Không DIP:  OrderService ───────────────► MySQLOrderRepo
Có DIP:     OrderService ──► OrderRepository (interface) ◄── MySQLOrderRepo
```
Nghiệp vụ (cấp cao) định nghĩa interface nó cần; hạ tầng (cấp thấp) implement interface đó. Thực hiện bằng Dependency Injection (xem [07-design-patterns.md](07-design-patterns.md)).

### Coding convention trong Go
Go có lợi thế lớn: phần lớn convention được **công cụ áp đặt**.
- **gofmt / goimports**: format chuẩn duy nhất (tab để thụt lề, vị trí dấu ngoặc). Không tranh cãi về style; chạy tự động khi lưu file.
- **Đặt tên**:
  - `MixedCaps` / `mixedCaps`, không dùng `snake_case` cho định danh.
  - Viết tắt giữ nguyên hoa/thường: `userID`, `HTTPServer`, `parseURL` (không phải `userId`, `HttpServer`).
  - Tên package ngắn, chữ thường, không gạch dưới, số ít: `user`, `http`, `strconv`. Tránh lặp tên: `user.User` chấp nhận được, nhưng `user.UserService` lặp; dùng `user.Service`.
  - Getter không có tiền tố `Get`: `u.Name()`, setter là `u.SetName()`.
  - Interface một method thường có hậu tố `-er`: `Reader`, `Stringer`, `Notifier`.
  - Receiver ngắn, nhất quán: `func (s *Server)`, không dùng `this`/`self`.
- **Lỗi**: chuỗi lỗi viết thường, không dấu chấm cuối (`"open config: file not found"`), vì chúng hay được nối với nhau. Không bỏ qua lỗi bằng `_` trừ khi có lý do rõ ràng. Xử lý lỗi một lần: hoặc log, hoặc trả về, không làm cả hai.
- **Context**: `ctx context.Context` là tham số đầu tiên; không lưu context trong struct.
- **Package**: tránh package `util`/`common` chứa đủ thứ; tổ chức theo chức năng.
- **Công cụ kiểm tra**: `go vet` (lỗi khả nghi), `staticcheck`, `golangci-lint` (gộp nhiều linter), chạy trong CI để chặn code vi phạm trước khi merge.
- Tài liệu tham chiếu: *Effective Go*, *Go Code Review Comments* (wiki của dự án Go), các style guide công khai của những công ty lớn.

## Cách hoạt động
Quy trình giữ code sạch trong team:
1. **Viết**: đặt tên tốt, hàm nhỏ, xử lý lỗi đầy đủ.
2. **Tự kiểm tra**: `gofmt`, `go vet`, linter, test chạy pass, tự đọc lại diff trước khi tạo PR.
3. **Code review**: người khác đọc, góp ý tính đúng đắn, khả năng đọc, thiết kế, test, bảo mật.
4. **CI**: pipeline tự động chạy lint + test, chặn merge nếu lỗi.
5. **Refactor** thường xuyên với test làm lưới an toàn: đổi cấu trúc bên trong mà không đổi hành vi bên ngoài.

**Code smell** (dấu hiệu cần refactor): hàm quá dài, class/struct "biết tuốt" (God object), tham số quá nhiều, code lặp, `switch` theo kiểu lặp lại khắp nơi, comment giải thích code khó hiểu, biến toàn cục, bool flag làm hàm chạy hai kiểu khác nhau.

## Ví dụ
Refactor một hàm "làm mọi thứ":

```go
// Trước
func Handle(w http.ResponseWriter, r *http.Request) {
    var req struct{ Email string; Pass string }
    json.NewDecoder(r.Body).Decode(&req)
    db, _ := sql.Open("postgres", "postgres://...")
    row := db.QueryRow("SELECT id, hash FROM users WHERE email='" + req.Email + "'")
    var id int; var hash string
    row.Scan(&id, &hash)
    if bcrypt.CompareHashAndPassword([]byte(hash), []byte(req.Pass)) == nil {
        w.Write([]byte("ok"))
    } else {
        w.Write([]byte("fail"))
    }
}
```
Vấn đề: bỏ qua lỗi, mở DB mỗi request, SQL injection, trộn HTTP + SQL + nghiệp vụ, status code sai, khó test.

```go
// Sau
type AuthService struct{ users UserReader }

var ErrInvalidCredentials = errors.New("invalid credentials")

func (s *AuthService) Login(ctx context.Context, email, password string) (int64, error) {
    u, err := s.users.FindByEmail(ctx, email) // repository dùng query tham số hóa
    if errors.Is(err, ErrNotFound) {
        return 0, ErrInvalidCredentials
    }
    if err != nil {
        return 0, fmt.Errorf("find user: %w", err)
    }
    if bcrypt.CompareHashAndPassword(u.PasswordHash, []byte(password)) != nil {
        return 0, ErrInvalidCredentials
    }
    return u.ID, nil
}

type AuthHandler struct{ auth *AuthService }

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
    var req struct {
        Email    string `json:"email"`
        Password string `json:"password"`
    }
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "invalid body", http.StatusBadRequest)
        return
    }
    id, err := h.auth.Login(r.Context(), req.Email, req.Password)
    switch {
    case errors.Is(err, ErrInvalidCredentials):
        http.Error(w, "invalid credentials", http.StatusUnauthorized)
    case err != nil:
        slog.Error("login", "err", err)
        http.Error(w, "internal error", http.StatusInternalServerError)
    default:
        writeJSON(w, http.StatusOK, map[string]int64{"user_id": id})
    }
}
```

## Hiểu nhầm thường gặp
- **"Clean code = ngắn nhất"**: code ngắn mà khó hiểu không sạch. Mục tiêu là dễ đọc, dễ sửa.
- **"DRY tuyệt đối"**: gộp những đoạn trùng lặp ngẫu nhiên tạo ra ràng buộc sai; đôi khi lặp lại một chút tốt hơn abstraction sai.
- **"SOLID chỉ dành cho OOP có class"**: SOLID áp dụng tốt cho Go qua package, struct và interface.
- **"Convention là chuyện thẩm mỹ"**: convention giúp đọc nhanh, review nhanh, giảm bug; trong Go nó được công cụ kiểm tra tự động.

## Câu hỏi ôn tập
1. **Giải thích từng chữ trong SOLID kèm ví dụ.** Xem bảng và code mẫu.
2. **Open/Closed áp dụng trong Go thế nào?** Thêm implementation mới cho interface thay vì sửa `switch`.
3. **Liskov vi phạm khi nào?** Implementation không giữ hợp đồng của interface (ném panic, đổi ý nghĩa giá trị trả về).
4. **Vì sao interface Go nên nhỏ?** ISP; dễ implement, dễ mock, dễ ghép.
5. **DRY, KISS, YAGNI là gì?**
6. **Thế nào là code sạch? Bạn chú ý gì khi review code?** Đặt tên, hàm nhỏ, xử lý lỗi, test, không lặp, bảo mật, hiệu năng rõ ràng.
7. **Convention đặt tên trong Go?** MixedCaps, viết tắt giữ hoa, package ngắn, getter không có `Get`, interface `-er`.

## Liên quan
- [04-oop-in-go.md](04-oop-in-go.md): nền tảng OOP của SOLID.
- [07-design-patterns.md](07-design-patterns.md): DI, Strategy, Factory phục vụ SOLID.
- [11-unit-testing.md](11-unit-testing.md): test là lưới an toàn để refactor.
- [13-git-and-version-control.md](13-git-and-version-control.md): code review qua pull request.
