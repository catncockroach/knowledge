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

## Câu hỏi và trả lời

**Giải thích từng chữ trong SOLID kèm ví dụ.**
> - **SOLID**: năm nguyên tắc thiết kế hướng đối tượng, cùng mục tiêu giữ code *dễ thay đổi*: một thay đổi chỉ chạm ít chỗ và không làm vỡ chỗ khác.
>
> - **S, Single Responsibility**: một module chỉ có một lý do để thay đổi. Ví dụ tách `ReportService` (tính số liệu) khỏi `PDFRenderer` (định dạng); đổi font không chạm logic tính.
> - **O, Open/Closed**: mở để mở rộng, đóng với sửa đổi. Ví dụ thêm phương thức thanh toán bằng một implementation mới của `PaymentMethod`, không sửa hàm xử lý chung.
> - **L, Liskov Substitution**: mọi implementation phải thay được cho nhau mà không làm sai hành vi bên gọi trông đợi. Ví dụ mọi `Storage` đều trả `ErrNotFound` khi không có key, không cái nào panic.
> - **I, Interface Segregation**: không bắt bên dùng phụ thuộc vào method nó không cần. Ví dụ hàm chỉ đọc nhận `Reader`, không nhận cả `ReadWriteCloser`.
> - **D, Dependency Inversion**: module cấp cao (nghiệp vụ) và cấp thấp (DB) cùng phụ thuộc vào abstraction. Ví dụ `OrderService` phụ thuộc interface `OrderRepository`, không phụ thuộc `*sql.DB`.
>
> Ranh giới: SOLID là hướng dẫn chứ không phải luật; áp máy móc sinh ra quá nhiều interface và tầng cho chương trình nhỏ. Code mẫu từng nguyên tắc ở phần *SOLID* của file này.

**Open/Closed áp dụng trong Go thế nào?**
> - **Open/Closed principle**: thêm hành vi mới bằng cách *thêm code mới*, không phải *sửa code cũ* đã chạy ổn.
>
> Trong Go, "điểm mở rộng" là interface. Thay vì một hàm `switch method { case "card": ... case "momo": ... }` phải sửa mỗi lần thêm phương thức, định nghĩa `type PaymentMethod interface { Pay(amount int64) error }`, mỗi phương thức một kiểu riêng; code xử lý chung chỉ gọi `m.Pay(amount)`. Thêm phương thức mới là thêm một kiểu, không đụng code cũ, không cần test lại nó.
>
> Ranh giới: vẫn cần *một* chỗ chọn implementation (factory, bảng đăng ký trong `main`); OCP dồn sự thay đổi về chỗ đó thay vì rải khắp nơi. Đừng tạo điểm mở rộng cho thứ chưa từng thay đổi (YAGNI); `switch` hai nhánh ổn định vẫn hợp lý.

**Liskov vi phạm khi nào?**
> - **Liskov Substitution Principle (LSP)**: kiểu con (hoặc implementation của interface) phải thay thế được kiểu cha mà chương trình vẫn đúng.
> - **Hợp đồng**: những gì bên gọi được phép trông đợi: điều kiện đầu vào, kết quả, lỗi, tác dụng phụ.
>
> LSP bị vi phạm khi implementation *thỏa chữ ký nhưng phá hợp đồng*: đòi đầu vào chặt hơn (từ chối giá trị mà interface cho phép), trả kết quả yếu hơn hoặc khác nghĩa, panic hay ném lỗi lạ ở chỗ hợp đồng không nói có lỗi, hoặc có tác dụng phụ bất ngờ. Ví dụ `ReadOnlyStore` implement `Store` nhưng `Save` panic: mọi code nhận `Store` có thể sập. Ví dụ kinh điển: `Square` kế thừa `Rectangle`, đặt chiều rộng làm đổi cả chiều cao, phá kỳ vọng của code dùng `Rectangle`.
>
> Ranh giới: compiler chỉ kiểm chữ ký, không kiểm hợp đồng; nên ghi hợp đồng trong comment của interface và viết một bộ test chung chạy cho mọi implementation.

**Vì sao interface Go nên nhỏ?**
> - **Interface Segregation Principle (ISP)**: không buộc bên dùng phụ thuộc vào method nó không dùng.
>
> Interface nhỏ (một vài method) dễ implement, dễ viết bản giả khi test, và *ghép* được: `io.ReadWriter` là `io.Reader` + `io.Writer`. Vì Go thỏa interface ngầm định, interface nên được khai báo ở phía người dùng với đúng method người đó cần, nên tự nhiên nhỏ. Câu của Rob Pike: "The bigger the interface, the weaker the abstraction".
>
> Ranh giới: nhỏ không có nghĩa là luôn một method; repository có thể có vài method liên quan chặt. Lỗi ngược lại là định nghĩa interface trước khi có ít nhất hai implementation hay nhu cầu test, chỉ để "cho đẹp".

**DRY, KISS, YAGNI là gì?**
> - **DRY (Don't Repeat Yourself)**: mỗi *tri thức* (quy tắc nghiệp vụ, hằng số, cách tính) chỉ có một chỗ định nghĩa. Dùng để khi quy tắc đổi chỉ phải sửa một chỗ.
> - **KISS (Keep It Simple, Stupid)**: chọn lời giải đơn giản nhất đủ đáp ứng yêu cầu. Dùng để code dễ đọc, ít lỗi.
> - **YAGNI (You Aren't Gonna Need It)**: không viết tính năng hay lớp trừu tượng cho nhu cầu tưởng tượng trong tương lai. Dùng để không trả giá bảo trì cho thứ chưa ai dùng.
>
> Cả ba cùng chống một thứ: độ phức tạp không cần thiết. DRY chống phức tạp do *trùng lặp*, KISS và YAGNI chống phức tạp do *thiết kế thừa*.
>
> Ranh giới: DRY nói về tri thức, không về chữ: hai đoạn code giống nhau nhưng thay đổi vì hai lý do khác nhau thì gộp lại là sai, gộp vội tạo abstraction sai còn tệ hơn lặp lại ("a little copying is better than a little dependency", Go proverb). Các nguyên tắc này đôi khi kéo nhau: DRY quá mức có thể phá KISS.

**Thế nào là code sạch? Bạn chú ý gì khi review code?**
> - **Clean code**: code mà người khác (hoặc chính mình sau sáu tháng) đọc hiểu nhanh và sửa an toàn.
> - **Code review**: một người khác đọc thay đổi trước khi merge để tìm lỗi và giữ chất lượng chung.
>
> Thước đo của code sạch là *chi phí để hiểu và thay đổi*, không phải độ ngắn hay độ "khéo". Khi review, đi từ quan trọng tới phụ:
> 1. **Đúng**: làm đúng yêu cầu, xử lý ca biên (rỗng, nil, lỗi mạng), không race condition.
> 2. **An toàn**: validate input, không SQL injection, không log secret, kiểm quyền.
> 3. **Lỗi**: lỗi được kiểm tra, wrap có ngữ cảnh, không nuốt lỗi.
> 4. **Test**: có test cho logic mới và ca biên.
> 5. **Dễ đọc**: tên nói đúng ý, hàm ngắn làm một việc, không lặp tri thức, không code chết.
> 6. **Hiệu năng hiển nhiên**: không N+1 query, không quên đóng tài nguyên (rows, body, file).
>
> Ranh giới: phần định dạng để công cụ lo (`gofmt`, linter), người review tập trung vào thiết kế và logic. Góp ý nhắm vào code, không vào người.

**Convention đặt tên trong Go?**
> - **Convention**: quy ước cả cộng đồng tuân theo để code của mọi người trông như nhau, đọc nhanh hơn.
>
> Quy tắc chung của Go: tên ngắn và rõ trong phạm vi nhỏ, rõ hơn khi phạm vi lớn; chữ hoa đầu là exported.
> - Dùng MixedCaps (`userID`, `HTTPServer`), không gạch dưới; viết tắt giữ nguyên hoa hoặc thường: `ID`, `URL`, `HTTP` (không `Id`, `Url`).
> - Package: một từ, chữ thường, không số nhiều (`order`, `http`); tên trong package không lặp tên package (`order.Service`, không `order.OrderService`).
> - Getter không có `Get` (`u.Name()`), setter là `SetName`.
> - Interface một method đặt theo động từ + `-er` (`Reader`, `Notifier`).
> - Biến cục bộ ngắn (`i`, `r`, `ctx`, `err`), receiver một hai chữ cái, thống nhất trong cả kiểu.
>
> Ranh giới: `gofmt` lo định dạng chứ không lo tên; tên do người viết và người review giữ. Nguồn chính thức: *Effective Go* và *Go Code Review Comments*.

## Liên quan
- [04-oop-in-go.md](04-oop-in-go.md): nền tảng OOP của SOLID.
- [07-design-patterns.md](07-design-patterns.md): DI, Strategy, Factory phục vụ SOLID.
- [11-unit-testing.md](11-unit-testing.md): test là lưới an toàn để refactor.
- [13-git-and-version-control.md](13-git-and-version-control.md): code review qua pull request.
