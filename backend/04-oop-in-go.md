# OOP in Go

> Lập trình hướng đối tượng (OOP) tổ chức chương trình thành các đối tượng gồm dữ liệu và hành vi đi kèm. Go không có class hay kế thừa, nhưng vẫn đạt được bốn trụ cột OOP bằng struct, method, interface và composition.

## Tại sao cần biết
Yêu cầu entry level: làm việc với method, đóng gói dữ liệu (encapsulation), hiểu kế thừa (inheritance). Interviewer dùng Java/C++ sẽ hỏi bốn tính chất OOP; interviewer Go sẽ hỏi "Go có OOP không", "Go thay kế thừa bằng gì", "value receiver vs pointer receiver", "interface ngầm định là gì". Cần trả lời được cả hai góc nhìn.

## Khái niệm cốt lõi

### Bốn trụ cột của OOP
| Tính chất | Ý nghĩa | Java/C++ | Go |
|---|---|---|---|
| **Encapsulation** (đóng gói) | Gói dữ liệu và hành vi lại, giấu chi tiết bên trong, chỉ lộ những gì cần | `private`/`public`, getter/setter | Chữ hoa/chữ thường ở cấp **package**; constructor `NewX` |
| **Abstraction** (trừu tượng) | Chỉ quan tâm "làm được gì", không quan tâm "làm thế nào" | abstract class, interface | interface |
| **Inheritance** (kế thừa) | Lớp con nhận lại thuộc tính, hành vi của lớp cha, quan hệ "is-a" | `extends` | **Không có**; thay bằng **embedding** (composition, quan hệ "has-a") |
| **Polymorphism** (đa hình) | Cùng một lời gọi, hành vi khác nhau tùy đối tượng thực | override + virtual method, overloading | interface (dynamic dispatch); không có overloading |

### Class vs object (khái niệm chung)
- **Class**: bản thiết kế (kiểu dữ liệu). **Object**: một thể hiện cụ thể của class trong bộ nhớ.
- **Constructor**: hàm khởi tạo object. **Method**: hàm gắn với object. **Field/attribute**: dữ liệu của object.
- Trong Go: kiểu `struct` ≈ class (phần dữ liệu), method khai báo riêng, giá trị struct ≈ object, hàm `NewX(...)` ≈ constructor.

### Method trong Go
```go
type Rectangle struct{ W, H float64 }

// value receiver: làm việc trên bản copy
func (r Rectangle) Area() float64 { return r.W * r.H }

// pointer receiver: sửa được struct gốc
func (r *Rectangle) Scale(k float64) { r.W *= k; r.H *= k }

r := Rectangle{2, 3}
r.Scale(2)        // Go tự lấy &r
fmt.Println(r.Area()) // 24
```
Method chỉ là hàm có tham số đặc biệt (receiver). Có thể gắn method cho mọi kiểu tự định nghĩa trong cùng package, không chỉ struct: `type Celsius float64; func (c Celsius) ToF() float64`.

**Chọn value hay pointer receiver:**
- Pointer receiver khi method cần sửa dữ liệu, struct lớn, hoặc struct chứa thứ không được copy (`sync.Mutex`).
- Value receiver cho kiểu nhỏ, bất biến (như `time.Time`).
- Nhất quán: nếu một method dùng pointer receiver thì nên cho tất cả dùng pointer.
- **Method set**: kiểu `T` chỉ có các method value receiver; `*T` có cả hai. Vì vậy nếu `Scale` dùng pointer receiver thì chỉ `*Rectangle` (không phải `Rectangle`) thỏa interface có `Scale`.

### Encapsulation trong Go
```go
package account

type Account struct {
    owner   string
    balance int64 // unexported: package khác không sửa trực tiếp được
}

func New(owner string) *Account { return &Account{owner: owner} }

func (a *Account) Deposit(amount int64) error {
    if amount <= 0 {
        return errors.New("amount must be positive")
    }
    a.balance += amount
    return nil
}

func (a *Account) Balance() int64 { return a.balance } // getter, không có setter
```
Ý nghĩa: **bất biến (invariant)** "số dư không bị cộng số âm" được bảo vệ bởi method, không ai bên ngoài phá được. Encapsulation không phải là "viết getter/setter cho mọi field", mà là bảo vệ tính đúng đắn của trạng thái.

### Inheritance và vì sao Go chọn composition
Kế thừa kiểu Java:
```java
class Animal { String name; void eat() {...} }
class Dog extends Animal { void bark() {...} }   // Dog is-a Animal
```
Vấn đề của kế thừa sâu: lớp con phụ thuộc chặt vào chi tiết lớp cha (*fragile base class*), cây kế thừa cứng nhắc, khó tái sử dụng hành vi theo nhiều chiều. Nguyên tắc kinh điển: **"favor composition over inheritance"**.

Go dùng **embedding**: nhúng một kiểu vào struct, field và method của kiểu nhúng được **promote** lên struct ngoài.
```go
type Animal struct{ Name string }
func (a Animal) Eat() string { return a.Name + " is eating" }

type Dog struct {
    Animal        // embedding: Dog has-a Animal
    Breed string
}
func (d Dog) Bark() string { return "Woof" }

d := Dog{Animal: Animal{Name: "Milu"}, Breed: "Corgi"}
d.Eat()          // "Milu is eating": method được promote
d.Name           // truy cập field của Animal
```
Khác kế thừa ở chỗ: `Dog` **không phải** là `Animal` về mặt kiểu; không truyền `Dog` vào hàm nhận `Animal` được. Muốn đa hình thì dùng interface. Nếu `Dog` định nghĩa `Eat()` riêng, nó che (shadow) method của `Animal` chứ không phải override kiểu virtual: method của `Animal` gọi `Eat` bên trong vẫn gọi bản của `Animal`.

### Interface và polymorphism
```go
type Shape interface {
    Area() float64
    Perimeter() float64
}
```
- Interface là tập hợp chữ ký method. Một kiểu **tự động** thỏa interface nếu có đủ các method đó, **không cần khai báo `implements`** (implicit / structural typing, "duck typing" kiểm tra lúc biên dịch).
- Hệ quả: interface có thể được khai báo ở phía **người dùng** (consumer), không cần sửa kiểu gốc. Đây là lý do Go có câu "accept interfaces, return structs".
- Interface nên **nhỏ**: `io.Reader` chỉ có `Read`, `io.Writer` chỉ có `Write`, `fmt.Stringer` chỉ có `String`. Interface nhỏ dễ implement, dễ mock.
- `any` (= `interface{}`) chứa được mọi giá trị; lấy giá trị ra bằng **type assertion** `v, ok := x.(string)` hoặc **type switch**.

```go
type Circle struct{ R float64 }
func (c Circle) Area() float64      { return math.Pi * c.R * c.R }
func (c Circle) Perimeter() float64 { return 2 * math.Pi * c.R }

func (r Rectangle) Perimeter() float64 { return 2 * (r.W + r.H) }

func TotalArea(shapes []Shape) float64 {
    total := 0.0
    for _, s := range shapes {
        total += s.Area() // gọi đúng Area của Circle hay Rectangle lúc chạy
    }
    return total
}

TotalArea([]Shape{Circle{1}, Rectangle{2, 3}})
```

Kiểm tra lúc biên dịch rằng một kiểu thỏa interface:
```go
var _ Shape = Circle{}           // không thỏa thì lỗi biên dịch
var _ Shape = (*Rectangle)(nil)
```

### Interface embedding
```go
type Reader interface { Read(p []byte) (int, error) }
type Writer interface { Write(p []byte) (int, error) }
type ReadWriter interface { Reader; Writer } // ghép interface nhỏ thành lớn
```

## Cách hoạt động
- Một giá trị interface bên trong là cặp **(type, value)**: con trỏ tới bảng thông tin kiểu + bảng method (*itab*), và con trỏ tới dữ liệu thật.
- Gọi `s.Area()` trên interface: runtime tra itab để tìm hàm `Area` của kiểu cụ thể rồi gọi (**dynamic dispatch**), tương tự virtual table trong C++.
- Interface chỉ bằng `nil` khi **cả** type và value đều nil. Đây là nguồn gốc lỗi "interface chứa pointer nil khác nil" (xem [03-go-basics.md](03-go-basics.md)).
- Embedding chỉ là cú pháp: compiler tự sinh đường dẫn `d.Animal.Eat()` khi bạn viết `d.Eat()`.

```
var s Shape = Circle{R: 1}

 s ┌────────┐      ┌────────────────────┐
   │ itab ──┼─────►│ type: Circle       │
   │ data ──┼──┐   │ Area  → Circle.Area│
   └────────┘  │   │ Perim → Circle.Per │
               │   └────────────────────┘
               └──►┌──────────┐
                   │ R: 1     │
                   └──────────┘
```

## Ví dụ
Đa hình thực tế trong backend: gửi thông báo qua nhiều kênh.

```go
type Notifier interface {
    Notify(ctx context.Context, to, msg string) error
}

type EmailNotifier struct{ smtpHost string }
func (e *EmailNotifier) Notify(ctx context.Context, to, msg string) error { /* gửi email */ return nil }

type SMSNotifier struct{ apiKey string }
func (s *SMSNotifier) Notify(ctx context.Context, to, msg string) error { /* gọi API SMS */ return nil }

type OrderService struct {
    notifier Notifier // phụ thuộc vào abstraction, không phụ thuộc Email hay SMS
}

func (s *OrderService) Complete(ctx context.Context, orderID, phone string) error {
    // ... cập nhật đơn hàng
    return s.notifier.Notify(ctx, phone, "Đơn "+orderID+" đã hoàn tất")
}

// Lúc khởi tạo chọn implementation; lúc test truyền một fake Notifier.
svc := &OrderService{notifier: &SMSNotifier{apiKey: "..."}}
```

Composition để tái sử dụng hành vi chung:
```go
type BaseRepo struct{ db *sql.DB }
func (b *BaseRepo) WithTx(ctx context.Context, fn func(*sql.Tx) error) error { /* begin/commit/rollback */ return nil }

type UserRepo struct{ *BaseRepo }   // dùng lại WithTx
type OrderRepo struct{ *BaseRepo }
```

## Hiểu nhầm thường gặp
- **"Go không hỗ trợ OOP"**: Go hỗ trợ encapsulation, abstraction, polymorphism; chỉ bỏ kế thừa class. Câu trả lời chuẩn: "Go hướng đối tượng theo kiểu composition".
- **"Embedding là kế thừa"**: không có quan hệ is-a, không có override kiểu virtual. Struct ngoài không dùng thay cho kiểu nhúng được.
- **"Encapsulation = getter/setter cho mọi field"**: mục tiêu là bảo vệ invariant; setter tùy tiện phá vỡ chính điều đó.
- **"Khai báo interface lớn trước ở phía implement"**: trong Go nên khai báo interface nhỏ ở nơi dùng nó, khi thật sự cần thay thế được.

## Câu hỏi ôn tập
1. **Bốn tính chất của OOP là gì? Cho ví dụ.** Encapsulation, abstraction, inheritance, polymorphism; xem bảng đầu.
2. **Abstraction khác encapsulation?** Abstraction: lộ ra "cái gì" (interface); encapsulation: giấu "thế nào" và bảo vệ trạng thái.
3. **Overloading vs overriding?** Overloading: cùng tên, khác tham số, quyết định lúc biên dịch (Go không có). Overriding: lớp con định nghĩa lại method lớp cha, quyết định lúc chạy.
4. **Go thay kế thừa bằng gì? Vì sao?** Embedding + interface; tránh cây kế thừa cứng và ràng buộc chặt.
5. **Value receiver vs pointer receiver?** Xem phần method; nêu được ảnh hưởng tới method set.
6. **Interface trong Go khác Java thế nào?** Implicit, không cần `implements`; khai báo phía consumer; nên nhỏ.
7. **Composition over inheritance nghĩa là gì?** Ghép hành vi từ các thành phần nhỏ thay vì kế thừa sâu; linh hoạt và ít ràng buộc hơn.
8. **Abstract class khác interface (Java)?** Abstract class có thể có state và method cài sẵn, chỉ kế thừa được một; interface chỉ là hợp đồng (Java 8+ có default method), implement được nhiều.

## Liên quan
- [03-go-basics.md](03-go-basics.md): struct, pointer, package (cơ sở của encapsulation).
- [07-design-patterns.md](07-design-patterns.md): pattern xây trên interface và composition.
- [08-clean-code-and-solid.md](08-clean-code-and-solid.md): SOLID dựa trên các khái niệm OOP này.
- [11-unit-testing.md](11-unit-testing.md): interface giúp mock dependency.
