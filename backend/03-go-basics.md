# Go basics

> Go là ngôn ngữ biên dịch, kiểu tĩnh, có garbage collector và hỗ trợ concurrency ngay trong ngôn ngữ (goroutine, channel). Thiết kế của Go ưu tiên sự đơn giản, đọc dễ, biên dịch nhanh, ra một file binary chạy độc lập: rất hợp cho backend và công cụ hạ tầng.

## Tại sao cần biết
Đây là ngôn ngữ chính. Interview entry level Go thường xoáy vào: slice vs array (len, cap, append), map, zero value, pointer, value vs pointer receiver, error handling, `defer`, interface, goroutine/channel. Phần lớn bug của người mới đến từ việc không hiểu slice dùng chung mảng nền, map không an toàn khi dùng đồng thời, và interface chứa nil.

## Khái niệm cốt lõi

### Đặc điểm của Go
- **Compiled + statically typed**: lỗi kiểu bị bắt lúc biên dịch; build ra binary native, không cần runtime cài sẵn như JVM.
- **Garbage collected**: không phải tự `free`, nhưng vẫn có con trỏ.
- **Không có class và kế thừa**: dùng struct + method + interface + composition (xem [04-oop-in-go.md](04-oop-in-go.md)).
- **Không có exception**: lỗi là giá trị trả về (`error`).
- **Concurrency**: `go f()` chạy f trong goroutine; giao tiếp qua channel.
- **Tooling chuẩn**: `go build`, `go run`, `go test`, `go fmt`, `go vet`, `go mod`.

### Biến, hằng, kiểu
```go
var a int          // khai báo, nhận zero value 0
var b = 10         // suy kiểu int
c := "hello"       // khai báo ngắn, chỉ dùng trong hàm
const Pi = 3.14

const (
    StatusPending = iota // 0
    StatusPaid           // 1
    StatusShipped        // 2
)
```

Kiểu cơ bản:
| Nhóm | Kiểu |
|---|---|
| Boolean | `bool` |
| Số nguyên | `int`, `int8/16/32/64`, `uint`, `uint8` (= `byte`), …, `uintptr` |
| Số thực | `float32`, `float64` |
| Số phức | `complex64`, `complex128` |
| Chuỗi | `string` (bất biến, chứa byte UTF-8), `rune` (= `int32`, một code point Unicode) |

Kiểu tổng hợp: array, slice, map, struct, pointer, function, interface, channel.

- **Zero value**: mọi biến đều được khởi tạo. Số = `0`, bool = `false`, string = `""`, pointer/slice/map/channel/func/interface = `nil`, struct = mọi field là zero value. Nhờ vậy không có biến "rác chưa khởi tạo".
- **Không ép kiểu ngầm**: `int` + `int64` là lỗi biên dịch; phải viết `int64(x)`.
- Biến khai báo mà không dùng, import không dùng → lỗi biên dịch.

### Array và slice
- **Array** có độ dài cố định, là một phần của kiểu: `[3]int` khác `[4]int`. Gán hoặc truyền array là **copy toàn bộ**.
- **Slice** là "cửa sổ" nhìn vào một array nền. Bên trong slice là một struct 3 trường:

```
slice header           array nền
┌─────────┐           ┌───┬───┬───┬───┬───┐
│ ptr ────┼──────────►│ 1 │ 2 │ 3 │ 0 │ 0 │
│ len = 3 │           └───┴───┴───┴───┴───┘
│ cap = 5 │
└─────────┘
```
- `len`: số phần tử đang dùng; `cap`: số phần tử tối đa trước khi phải cấp phát mảng mới.
- `append` nếu còn cap thì ghi vào mảng nền hiện có; hết cap thì cấp phát mảng mới lớn hơn, copy dữ liệu sang, và trả về slice trỏ tới mảng mới. **Luôn gán lại**: `s = append(s, x)`.
- Truyền slice vào hàm là copy header (rẻ), nhưng hai header cùng trỏ một mảng nền → sửa phần tử trong hàm thì bên ngoài thấy.

```go
a := []int{1, 2, 3, 4, 5}
b := a[1:3]        // b = [2 3], len 2, cap 4 (tính từ a[1] tới hết)
b[0] = 99          // a = [1 99 3 4 5]  ← chung mảng nền!
b = append(b, 100) // còn cap → ghi đè a[3]: a = [1 99 3 100 5]

c := make([]int, 0, 10) // len 0, cap 10: cấp phát trước khi biết kích thước
d := slices.Clone(a)    // copy độc lập (hoặc append([]int(nil), a...))
```

- `nil` slice (`var s []int`) và empty slice (`[]int{}`) đều có len 0, đều `append` được; khác nhau khi so sánh `s == nil` và khi encode JSON (`null` vs `[]`).

### Map
```go
m := map[string]int{"a": 1}
m["b"] = 2
v, ok := m["c"]   // v = 0, ok = false: phân biệt "không có" với "giá trị 0"
delete(m, "a")
for k, v := range m { ... } // thứ tự duyệt ngẫu nhiên, đừng dựa vào nó
```
- Map là hash table (xem [05-data-structures.md](05-data-structures.md)); tra cứu trung bình O(1).
- Map `nil` đọc được nhưng **ghi vào sẽ panic**: phải `make` trước.
- Map **không an toàn cho concurrency**: nhiều goroutine đọc ghi đồng thời gây lỗi `fatal error: concurrent map writes`. Dùng `sync.Mutex` hoặc `sync.Map`.
- Key phải so sánh được bằng `==` (không dùng slice, map, func làm key).

### String, byte, rune
```go
s := "Xin chào"
len(s)                  // 9: số BYTE, "à" chiếm 2 byte trong UTF-8
utf8.RuneCountInString(s) // 8: số ký tự
for i, r := range s {}  // duyệt theo rune, i là vị trí byte
b := []byte(s)          // copy sang slice byte có thể sửa
```
String bất biến; nối nhiều chuỗi trong vòng lặp nên dùng `strings.Builder` để tránh cấp phát lặp lại.

### Struct và pointer
```go
type User struct {
    ID    int64
    Name  string
    email string // chữ thường: chỉ thấy được trong package
}

u := User{ID: 1, Name: "An"}
p := &u          // p là *User
p.Name = "Bình"  // tự dereference, tương đương (*p).Name
u2 := u          // copy toàn bộ struct
```
- Go **luôn truyền theo giá trị** (pass by value). Truyền pointer là copy địa chỉ, nên hàm sửa được dữ liệu gốc.
- Dùng pointer khi: cần sửa dữ liệu gốc, struct lớn (tránh copy), hoặc cần biểu diễn "không có" (`nil`).
- Không có số học con trỏ (trừ gói `unsafe`). Trả về pointer tới biến cục bộ là an toàn: compiler tự đưa biến đó lên heap (escape analysis).
- Slice, map, channel bản chất chứa con trỏ bên trong, nên truyền giá trị của chúng vẫn thấy được thay đổi trên dữ liệu nền.

### Hàm
```go
func divide(a, b float64) (float64, error) {   // nhiều giá trị trả về
    if b == 0 {
        return 0, errors.New("divide by zero")
    }
    return a / b, nil
}

func sum(nums ...int) int { ... }              // variadic: sum(1, 2, 3) hoặc sum(s...)

counter := func() func() int {                 // closure: hàm "nhớ" biến bên ngoài
    n := 0
    return func() int { n++; return n }
}()
```
Hàm là giá trị hạng nhất: gán cho biến, truyền làm tham số, trả về từ hàm khác.

### Điều khiển luồng
- Chỉ có một vòng lặp `for` (dùng được như while, for vô hạn, `for range`).
- `if` và `switch` có thể kèm câu lệnh khởi tạo: `if err := f(); err != nil {}`.
- `switch` không tự rơi xuống case sau (không cần `break`); muốn rơi thì `fallthrough`.
- Từ Go 1.22, biến của vòng `for` được tạo mới cho mỗi vòng lặp, nên closure/goroutine trong vòng lặp không còn bắt nhầm biến dùng chung như các phiên bản cũ.

### Xử lý lỗi
```go
type error interface { Error() string }
```
- Quy ước: hàm có thể lỗi trả `error` ở vị trí cuối; caller kiểm tra ngay `if err != nil`.
- **Wrap lỗi** để thêm ngữ cảnh mà vẫn giữ lỗi gốc: `fmt.Errorf("load config: %w", err)`.
- Kiểm tra lỗi: `errors.Is(err, ErrNotFound)` (so với lỗi mẫu, đi xuyên qua các lớp wrap), `errors.As(err, &target)` (lấy ra lỗi có kiểu cụ thể).
- **Sentinel error**: biến lỗi khai báo sẵn, `var ErrNotFound = errors.New("not found")`.
- **Custom error type**: struct implement `Error() string`, mang thêm thông tin (mã lỗi, field).

### defer, panic, recover
- `defer f()` hoãn gọi f đến khi hàm bao ngoài return; nhiều defer chạy theo thứ tự **LIFO**. Tham số của f được tính **ngay lúc defer**, không phải lúc chạy. Dùng để đóng file, unlock mutex, rollback transaction.
- `panic`: lỗi không thể tiếp tục (bug lập trình: index ngoài phạm vi, nil pointer dereference). Panic chạy các defer rồi làm chết goroutine, và cả chương trình nếu không ai recover.
- `recover()` chỉ có tác dụng khi gọi trong hàm defer; dùng ở middleware HTTP để một request lỗi không làm sập cả server.
- Quy tắc: lỗi dự đoán được (input sai, mất mạng) → trả `error`; `panic` chỉ cho tình huống "không thể xảy ra".

```go
func safeHandler(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if rec := recover(); rec != nil {
                slog.Error("panic", "err", rec)
                http.Error(w, "internal error", http.StatusInternalServerError)
            }
        }()
        next.ServeHTTP(w, r)
    })
}
```

### Package và module
- Mỗi thư mục là một **package**. Tên bắt đầu bằng **chữ hoa** là exported (public), chữ thường là unexported (chỉ dùng trong package). Đây là cơ chế đóng gói duy nhất của Go.
- Thư mục `internal/`: chỉ code trong cây thư mục cha mới import được.
- **Module** (`go.mod`) là tập package có version. `go mod init`, `go get`, `go mod tidy`. `go.sum` lưu checksum dependency để đảm bảo tải đúng mã.
- Hàm `init()` chạy tự động khi package được nạp, trước `main()`. Nên hạn chế dùng vì khó test, khó theo dõi.

### Generics (cơ bản)
```go
func Map[T, U any](s []T, f func(T) U) []U {
    out := make([]U, 0, len(s))
    for _, v := range s {
        out = append(out, f(v))
    }
    return out
}

type Number interface{ ~int | ~int64 | ~float64 }
func Sum[T Number](s []T) T { var t T; for _, v := range s { t += v }; return t }
```
Dùng generics cho cấu trúc dữ liệu và hàm tiện ích dùng chung; với hành vi khác nhau theo kiểu thì interface vẫn là lựa chọn chính.

### Công cụ
```bash
go run ./cmd/server        # build + chạy
go build -o app ./cmd/server
go test ./...              # chạy test toàn bộ
go test -race ./...        # phát hiện data race
go vet ./...               # tìm lỗi khả nghi
gofmt -w . / go fmt ./...  # format chuẩn
go mod tidy                # dọn dependency
```

## Cách hoạt động
Từ mã nguồn đến chương trình chạy:
1. `go build` biên dịch các package (theo đồ thị import, có cache) thành mã máy, link tĩnh cùng **Go runtime** thành một binary.
2. Go runtime đi kèm trong binary lo: lập lịch goroutine, garbage collector, cấp phát bộ nhớ, network poller.
3. Khi chạy: runtime khởi tạo, chạy `init()` của các package theo thứ tự phụ thuộc, rồi `main.main()`. Chương trình kết thúc khi `main` return, **kể cả khi các goroutine khác chưa xong**.
4. Cross-compile dễ: `GOOS=linux GOARCH=amd64 go build`.

## Ví dụ
Bài tập điển hình hay bị hỏi: đoán kết quả.

```go
func modify(s []int) { s[0] = 100 }
func grow(s []int)   { s = append(s, 4) }

func main() {
    s := []int{1, 2, 3}
    modify(s)
    fmt.Println(s) // [100 2 3]  sửa qua mảng nền chung
    grow(s)
    fmt.Println(s) // [100 2 3]  append trên header copy, header bên ngoài không đổi len

    for i := 0; i < 3; i++ {
        defer fmt.Print(i, " ")
    }
    // in "2 1 0 " khi main return (LIFO)
}
```

Đọc file và xử lý lỗi đúng chuẩn:

```go
func countLines(path string) (int, error) {
    f, err := os.Open(path)
    if err != nil {
        return 0, fmt.Errorf("open %s: %w", path, err)
    }
    defer f.Close()

    sc := bufio.NewScanner(f)
    n := 0
    for sc.Scan() {
        n++
    }
    if err := sc.Err(); err != nil {
        return 0, fmt.Errorf("scan %s: %w", path, err)
    }
    return n, nil
}

// caller
n, err := countLines("data.txt")
if errors.Is(err, fs.ErrNotExist) {
    // xử lý riêng trường hợp file không tồn tại
}
```

## Hiểu nhầm thường gặp
- **"Slice là tham chiếu"**: slice là một struct nhỏ truyền theo giá trị, chứa con trỏ tới mảng nền. Sửa phần tử thì chia sẻ; `append` vượt cap hoặc gán lại slice trong hàm thì không.
- **"Interface chứa pointer nil là nil"**: biến interface gồm (kiểu, giá trị). `var p *MyErr = nil; var err error = p` thì `err != nil` vì phần kiểu đã có. Hàm trả `error` nên `return nil` trực tiếp, đừng trả một pointer nil có kiểu.
- **"Map duyệt theo thứ tự chèn"**: thứ tự ngẫu nhiên; cần thứ tự thì lấy key ra, sort rồi duyệt.
- **"`defer` trong vòng lặp đóng tài nguyên sau mỗi vòng"**: defer chỉ chạy khi hàm return; mở 10.000 file trong vòng lặp với defer sẽ giữ cả 10.000 file. Tách thân vòng lặp ra hàm riêng.

## Câu hỏi

**Array khác slice?**
> - **Array**: dãy phần tử có độ dài cố định, độ dài là một phần của kiểu (`[3]int` khác `[4]int`).
> - **Slice**: "cửa sổ" nhìn vào một array nền, gồm ba trường: con trỏ tới phần tử đầu, `len`, `cap`.
>
> Quy tắc: array là *giá trị*, slice là *header trỏ vào dữ liệu*. Gán hay truyền array là copy toàn bộ phần tử; gán hay truyền slice chỉ copy header, hai slice cùng trỏ một array nền nên sửa phần tử qua slice này thì slice kia thấy. Slice co giãn được bằng `append`, array thì không, nên code Go thực tế gần như chỉ dùng slice.
>
> Ranh giới: `b := a[1:3]` không copy dữ liệu, `b` dùng chung array nền với `a`; muốn tách hẳn thì dùng `copy` hoặc `slices.Clone`. Giữ một slice nhỏ cắt từ slice rất lớn sẽ giữ cả array lớn trong bộ nhớ.

**len và cap khác nhau? append hoạt động thế nào?**
> - **len**: số phần tử slice đang có, truy cập được bằng chỉ số.
> - **cap**: số phần tử array nền còn chứa được tính từ đầu slice, tức là chỗ để `append` mà không cấp phát lại.
>
> `append` kiểm tra chỗ trống: nếu `len < cap` thì ghi vào array nền hiện có và tăng `len`; nếu đầy thì cấp phát array mới lớn hơn (thường gấp khoảng 2 lần với slice nhỏ, tăng chậm dần với slice lớn), copy dữ liệu cũ sang rồi ghi thêm. Vì có thể trả về slice trỏ array mới, luôn phải gán lại: `s = append(s, x)`.
>
> Ranh giới: hai slice chung array nền, `append` vào một slice khi còn cap có thể ghi đè dữ liệu slice kia nhìn thấy. Biết trước số phần tử thì tạo `make([]T, 0, n)` để tránh cấp phát lại nhiều lần.

**Zero value là gì? Map nil ghi được không?**
> - **Zero value**: giá trị mặc định Go gán cho biến khai báo mà không khởi tạo: `0` cho số, `""` cho string, `false` cho bool, `nil` cho pointer, slice, map, channel, interface, func; struct thì mọi field nhận zero value.
> - **Map nil**: biến map khai báo `var m map[string]int` mà chưa `make`.
>
> Quy tắc: Go không có biến "chưa khởi tạo", và các kiểu được thiết kế để zero value dùng được ngay khi có thể. Slice nil `append` được, đọc map nil trả zero value, `sync.Mutex` zero value dùng được luôn. Riêng *ghi* vào map nil thì panic, vì chưa có bảng băm để ghi; phải tạo bằng `make(map[string]int)` hoặc literal `map[string]int{}`.
>
> Ranh giới: gửi hoặc nhận trên channel nil thì block mãi mãi; gọi method qua con trỏ nil chỉ panic khi method truy cập field. Thiết kế struct sao cho zero value có nghĩa là một convention tốt của Go.

**Go truyền tham số theo value hay reference?**
> - **Pass by value**: hàm nhận bản copy của đối số; sửa bản copy không ảnh hưởng biến gốc.
> - **Pass by reference**: hàm nhận chính biến gốc (bí danh), sửa là sửa gốc. Go không có cơ chế này.
>
> Quy tắc: Go *luôn* truyền theo value. Cái được copy là giá trị của biến: với `int` là con số, với struct là toàn bộ field, với pointer là địa chỉ, với slice là header (ptr, len, cap), với map và channel là con trỏ tới cấu trúc bên trong. Vì vậy hàm sửa được phần tử của slice hay key của map được truyền vào: bản copy vẫn trỏ cùng dữ liệu.
>
> Ranh giới: hàm `append` vào slice tham số hoặc gán lại tham số thì bên gọi không thấy, vì chỉ header bản copy thay đổi; cần trả slice mới về hoặc truyền `*[]T`.

**Khi nào dùng pointer?**
> - **Pointer**: biến chứa địa chỉ của một biến khác (`*T`); `&x` lấy địa chỉ, `*p` đọc giá trị tại địa chỉ.
>
> Dùng pointer khi cần một trong ba điều: (1) hàm hay method phải *sửa* dữ liệu gốc của bên gọi; (2) struct lớn, copy tốn kém; (3) cần phân biệt "không có giá trị" (`nil`) với zero value, vd field tùy chọn trong JSON. Ngoài ba trường hợp đó, truyền giá trị cho rõ ràng và an toàn hơn.
>
> Ranh giới: slice, map, channel đã chứa con trỏ bên trong nên hiếm khi cần `*[]T` hay `*map`. Pointer không phải lúc nào cũng nhanh hơn: biến bị lấy địa chỉ có thể escape lên heap và tạo việc cho GC. Một kiểu nên dùng thống nhất pointer receiver hoặc value receiver, xem [04-oop-in-go.md](04-oop-in-go.md).

**Go xử lý lỗi thế nào? `%w`, `errors.Is`, `errors.As`?**
> - **error**: interface có một method `Error() string`; hàm có thể lỗi trả `error` làm giá trị cuối.
> - **Wrap**: bọc một lỗi trong lỗi mới để thêm ngữ cảnh mà vẫn giữ lỗi gốc, bằng `fmt.Errorf("load user %d: %w", id, err)`.
> - **Sentinel error**: biến lỗi mẫu dùng để so sánh, vd `sql.ErrNoRows`.
>
> Quy tắc: lỗi trong Go là *giá trị*, được trả về và kiểm tra tường minh (`if err != nil`), không phải exception nhảy qua stack. Mỗi tầng wrap thêm ngữ cảnh bằng `%w`, tạo thành chuỗi lỗi. `errors.Is(err, target)` duyệt chuỗi đó xem có lỗi nào *bằng* lỗi mẫu không; `errors.As(err, &target)` duyệt chuỗi tìm lỗi *thuộc kiểu* cụ thể và gán vào `target` để đọc thêm field.
>
> Ranh giới: so sánh `err == sql.ErrNoRows` hỏng ngay khi lỗi bị wrap, nên luôn dùng `errors.Is`. `%v` thay vì `%w` chỉ chép chuỗi, làm đứt chuỗi lỗi. Mỗi lỗi chỉ nên xử lý một lần: hoặc log, hoặc trả lên, không làm cả hai.

**defer chạy khi nào, thứ tự gì?**
> - **defer**: lệnh hoãn một lời gọi hàm tới lúc hàm bao quanh kết thúc, dùng để dọn dẹp (đóng file, mở khóa, rollback).
>
> Quy tắc: lời gọi được defer chạy khi hàm bao quanh *kết thúc vì bất kỳ lý do gì*: return bình thường hoặc panic. Nhiều defer chạy theo thứ tự LIFO (defer sau chạy trước), giống ngăn xếp, nên tài nguyên mở sau được đóng trước. *Đối số* của lời gọi được tính ngay lúc gặp lệnh `defer`, không phải lúc chạy: `defer fmt.Println(i)` in giá trị `i` ở thời điểm defer.
>
> Ranh giới: defer gắn với *hàm*, không với khối lệnh, nên `defer f.Close()` trong vòng lặp chỉ chạy khi cả hàm kết thúc và giữ file mở suốt vòng lặp; tách thân vòng lặp thành hàm riêng. Defer có thể sửa named return value, đó là cách `recover` biến panic thành error. `os.Exit` thoát ngay, bỏ qua mọi defer.

**panic khác error?**
> - **error**: giá trị trả về báo lỗi dự đoán được, bên gọi phải xử lý (file không tồn tại, input sai, mạng lỗi).
> - **panic**: dừng luồng chạy bình thường, chạy các defer rồi làm sập chương trình, trừ khi có `recover` trong một defer bắt lại.
>
> Tiêu chí: lỗi có thể xảy ra trong vận hành bình thường thì trả `error`; panic dành cho lỗi *lập trình* hoặc trạng thái không thể tiếp tục (truy cập ngoài chỉ số, nil pointer, cấu hình bắt buộc thiếu lúc khởi động). Thư viện không nên panic để báo lỗi cho bên gọi.
>
> Ranh giới: `recover` chỉ có tác dụng khi gọi trực tiếp trong hàm defer của chính goroutine bị panic; panic trong goroutine khác không bắt được và làm sập cả process. HTTP server của Go recover panic trong từng handler để một request lỗi không làm chết server; middleware recovery của các framework làm điều tương tự.

**Exported/unexported xác định thế nào?**
> - **Exported**: tên (hàm, kiểu, biến, hằng, field, method) dùng được từ package khác.
> - **Unexported**: tên chỉ dùng được trong package khai báo nó.
>
> Quy tắc: Go không có từ khóa `public`/`private`; chữ cái đầu của tên quyết định: viết hoa (`User`, `Save`) là exported, viết thường (`user`, `save`) là unexported. Phạm vi là *package*, không phải struct hay file: mọi file trong cùng package thấy tên unexported của nhau.
>
> Ranh giới: field unexported không được `encoding/json` đọc hay ghi, lỗi thường gặp khi struct trả JSON rỗng. Một hàm exported có thể trả về kiểu unexported, nhưng bên ngoài khó dùng nên tránh. Đây là công cụ encapsulation của Go, xem [04-oop-in-go.md](04-oop-in-go.md).

## Liên quan
- [04-oop-in-go.md](04-oop-in-go.md): method, interface, composition.
- [05-data-structures.md](05-data-structures.md): slice, map dưới góc nhìn cấu trúc dữ liệu.
- [09-concurrency.md](09-concurrency.md): goroutine, channel.
- [11-unit-testing.md](11-unit-testing.md): `go test`.
