# Secure coding

> Lập trình an toàn là viết code sao cho kẻ tấn công không thể lợi dụng để đọc trộm, sửa đổi dữ liệu hay làm gián đoạn dịch vụ. Phần lớn lỗ hổng không đến từ thuật toán mã hóa yếu mà từ những sai sót rất bình thường: tin input người dùng, nối chuỗi SQL, quên kiểm tra quyền, lộ secret.

## Tại sao cần biết
Backend là nơi giữ dữ liệu và quyền truy cập; một lỗi nhỏ có thể làm lộ dữ liệu của mọi khách hàng. Yêu cầu entry level: kiến thức cơ bản về lập trình an toàn; mức thành thạo hơn là áp dụng vào sản phẩm và hiểu mã hóa, toàn vẹn dữ liệu. Interview hay hỏi: SQL injection là gì và cách chống, XSS, CSRF, lưu mật khẩu thế nào, hash khác encryption, authentication vs authorization, JWT, HTTPS hoạt động ra sao.

## Khái niệm cốt lõi

### Mục tiêu bảo mật: CIA
- **Confidentiality** (bí mật): chỉ người được phép mới đọc được dữ liệu → mã hóa, phân quyền.
- **Integrity** (toàn vẹn): dữ liệu không bị sửa trái phép, hoặc nếu bị sửa thì phát hiện được → hash, MAC, chữ ký số.
- **Availability** (sẵn sàng): dịch vụ phục vụ được khi cần → chống DoS, rate limit, dự phòng.

### Nguyên tắc nền tảng
- **Không tin input**: mọi dữ liệu từ bên ngoài (body, query, header, cookie, file upload, thậm chí response từ service khác) đều có thể độc hại. Validate ở biên hệ thống.
- **Least privilege**: mỗi thành phần chỉ có quyền tối thiểu cần thiết (user DB của app không cần quyền `DROP`, container không chạy root).
- **Defense in depth**: nhiều lớp bảo vệ; một lớp thủng vẫn còn lớp khác.
- **Secure by default / fail securely**: mặc định từ chối; khi lỗi thì đóng cửa chứ không mở.
- **Không tự chế crypto**: dùng thư viện chuẩn đã được kiểm chứng.
- **Giảm bề mặt tấn công**: tắt endpoint debug, port, tính năng không dùng.

### Encoding, hashing, encryption
| | Mục đích | Đảo ngược? | Cần khóa? | Ví dụ |
|---|---|---|---|---|
| **Encoding** | Biểu diễn dữ liệu ở định dạng khác để truyền/lưu | Có, ai cũng làm được | Không | Base64, URL encoding, hex |
| **Hashing** | Tạo "dấu vân tay" cố định độ dài, kiểm tra toàn vẹn | Không (một chiều) | Không | SHA-256 |
| **Encryption** | Giữ bí mật | Có, với khóa đúng | Có | AES, RSA |

Base64 **không phải** mã hóa bảo mật.

**Hàm băm (hash)** tốt có tính chất: cùng input luôn cùng output; thay đổi một bit input làm output đổi hoàn toàn; không tìm được input từ output; khó tìm hai input cùng output (collision). MD5 và SHA-1 đã bị phá về collision, không dùng cho mục đích bảo mật; dùng họ SHA-2 (SHA-256) hoặc SHA-3.

**HMAC**: hash kết hợp khóa bí mật, chứng minh dữ liệu **không bị sửa** và **đến từ người có khóa** (ký webhook, ký JWT HS256).

**Mã hóa đối xứng** (symmetric): một khóa dùng cho cả mã hóa và giải mã. Nhanh, dùng cho dữ liệu lớn. Ví dụ AES (nên dùng chế độ có xác thực như AES-GCM). Vấn đề: làm sao trao khóa an toàn.

**Mã hóa bất đối xứng** (asymmetric): cặp **public key** (công khai) và **private key** (giữ bí mật). Mã hóa bằng public key thì chỉ private key giải được; **ký** bằng private key thì ai có public key cũng kiểm tra được (**chữ ký số**). Chậm hơn nhiều, dùng để trao đổi khóa và ký. Ví dụ RSA, ECDSA, Ed25519.

**TLS/HTTPS** kết hợp cả hai: bắt tay dùng bất đối xứng + chứng chỉ (certificate do CA ký) để xác thực server và thỏa thuận **khóa phiên**, sau đó dữ liệu được mã hóa đối xứng bằng khóa phiên. Đảm bảo bí mật, toàn vẹn và xác thực server. Chi tiết ở [../internet/10-network-security.md](../internet/10-network-security.md).

### Lưu mật khẩu
- **Không bao giờ** lưu plaintext, **không** mã hóa (vì giải được), **không** dùng hash nhanh như SHA-256/MD5 trần (GPU thử hàng tỷ lần mỗi giây).
- Dùng **hàm băm mật khẩu chậm, có salt**: **bcrypt**, **scrypt**, **Argon2id**, PBKDF2.
  - **Salt**: chuỗi ngẫu nhiên riêng cho từng user, ghép vào trước khi băm → hai user cùng mật khẩu có hash khác nhau, vô hiệu hóa rainbow table. bcrypt tự sinh và lưu salt trong chuỗi kết quả.
  - **Cost factor**: điều chỉnh độ chậm để tăng theo sức mạnh phần cứng.
```go
import "golang.org/x/crypto/bcrypt"

hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
// lưu hash vào DB

err = bcrypt.CompareHashAndPassword(hash, []byte(input)) // nil nghĩa là khớp
```

### Authentication và authorization
- **Authentication (AuthN)**: xác thực **bạn là ai** (mật khẩu, OTP, chứng chỉ, OAuth). Lỗi → 401.
- **Authorization (AuthZ)**: kiểm tra **bạn được làm gì** (RBAC: theo vai trò; ABAC: theo thuộc tính). Lỗi → 403.
- **Session**: server lưu phiên, client giữ session ID trong cookie (`HttpOnly`, `Secure`, `SameSite`).
- **JWT** (JSON Web Token): `header.payload.signature`, mã Base64URL. Payload **chỉ được ký, không được mã hóa**: ai cũng đọc được, nên không đặt dữ liệu nhạy cảm. Server kiểm tra chữ ký và hạn (`exp`) thay vì tra DB. Phải cố định thuật toán chấp nhận (chống tấn công `alg: none`), đặt thời hạn ngắn, dùng refresh token, có cách thu hồi khi cần.
- **OAuth 2.0 / OpenID Connect**: ủy quyền cho bên thứ ba và đăng nhập qua nhà cung cấp danh tính (đăng nhập bằng Google).
- Chống brute force: rate limit, khóa tạm, CAPTCHA, MFA. Thông báo lỗi chung chung ("email hoặc mật khẩu sai") để không lộ email nào tồn tại.

### Các lỗ hổng web phổ biến
Danh sách OWASP Top 10 (dự án cộng đồng về bảo mật ứng dụng web, cập nhật định kỳ) gom các nhóm rủi ro hay gặp nhất: kiểm soát truy cập hỏng, lỗi mật mã, injection, thiết kế không an toàn, cấu hình sai, thành phần lỗi thời, lỗi xác thực, lỗi toàn vẹn phần mềm, thiếu log/giám sát, SSRF… Các lỗ hổng cụ thể cần nắm:

**SQL injection**: dữ liệu người dùng được nối thẳng vào câu SQL và trở thành một phần của lệnh.
```go
// SAI: email = "' OR '1'='1" → lấy mọi user; "'; DROP TABLE users; --" → xóa bảng
q := "SELECT * FROM users WHERE email = '" + email + "'"

// ĐÚNG: parameterized query; driver gửi dữ liệu tách khỏi lệnh
db.QueryRowContext(ctx, "SELECT id FROM users WHERE email = $1", email)
```
Placeholder không dùng được cho tên bảng/cột; khi cần sắp xếp theo cột động thì so với **whitelist** cố định. Tương tự có **command injection** (`exec.Command("sh", "-c", "ping " + host)`): truyền tham số riêng, không qua shell.

**XSS (Cross-Site Scripting)**: kẻ tấn công chèn script vào trang mà người dùng khác xem (ví dụ comment chứa `<script>gửi cookie đi</script>`). Chống: **escape output** theo ngữ cảnh (`html/template` của Go tự escape; `text/template` thì không), Content-Security-Policy, cookie `HttpOnly`, trả JSON với `Content-Type` đúng.

**CSRF (Cross-Site Request Forgery)**: trang độc hại khiến trình duyệt của nạn nhân (đang đăng nhập, cookie tự gửi kèm) gửi request thay đổi dữ liệu. Chống: CSRF token, cookie `SameSite=Lax/Strict`, không dùng GET để thay đổi trạng thái. API dùng token trong header `Authorization` ít bị ảnh hưởng.

**Broken access control / IDOR**: `GET /orders/1002` trả đơn của người khác chỉ vì đổi ID. Luôn kiểm tra quyền sở hữu ở server: `WHERE id = $1 AND user_id = $2`. Đây là nhóm lỗi phổ biến nhất trong thực tế.

**Path traversal**: `GET /files?name=../../etc/passwd`. Chuẩn hóa đường dẫn và kiểm tra nằm trong thư mục cho phép (`filepath.Clean`, `os.Root` ở các bản Go mới), tốt nhất là không dùng tên file do người dùng cung cấp.

**SSRF (Server-Side Request Forgery)**: server tải URL do người dùng cung cấp, bị lừa gọi vào dịch vụ nội bộ (`http://169.254.169.254/` metadata cloud, `http://localhost:6379`). Chống: whitelist domain, chặn dải IP nội bộ.

**Deserialization / mass assignment**: bind thẳng JSON vào model có field `IsAdmin` → người dùng tự gửi `"is_admin": true`. Dùng struct request riêng chỉ chứa field được phép.

### Validate input
- Validate **kiểu, độ dài, định dạng, phạm vi** ở server (validate ở client chỉ để trải nghiệm người dùng, luôn bị bỏ qua được).
- Ưu tiên **whitelist** (cho phép những gì hợp lệ) hơn blacklist.
- Giới hạn kích thước body (`http.MaxBytesReader`), số phần tử, thời gian xử lý (timeout) để chống DoS.
- `json.Decoder.DisallowUnknownFields()` để từ chối field lạ khi cần chặt chẽ.

### Quản lý secret
- Không hard-code mật khẩu, API key, private key trong code; không commit file `.env`. Đã lỡ commit thì coi như lộ: **thu hồi và tạo mới**, xóa khỏi lịch sử Git chưa đủ.
- Đọc từ biến môi trường hoặc secret manager (Vault, Kubernetes Secret, dịch vụ cloud).
- Không ghi secret, mật khẩu, token, số thẻ vào log.

### Các thực hành khác
- **Error handling an toàn**: trả thông báo chung cho client, chi tiết (stack trace, câu SQL) chỉ ghi log nội bộ.
- **Logging và giám sát**: log sự kiện bảo mật (đăng nhập thất bại, đổi quyền) để phát hiện tấn công.
- **Dependency**: cập nhật thư viện, quét lỗ hổng (`govulncheck ./...` cho Go), dùng `go.sum` để đảm bảo toàn vẹn module.
- **Rate limiting** cho API, đặc biệt đăng nhập, gửi OTP.
- **Header bảo mật** (`Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`), cấu hình **CORS** chặt (không `*` kèm credentials).
- **TLS** cho mọi kết nối, kể cả nội bộ giữa service; không tắt kiểm tra chứng chỉ (`InsecureSkipVerify: true`) ở production.
- **Container**: image tối giản, không chạy root, quét lỗ hổng image.
- **Random an toàn**: token, mã OTP dùng `crypto/rand`, không dùng `math/rand`.
- **So sánh secret** bằng hàm thời gian hằng (`subtle.ConstantTimeCompare`, `hmac.Equal`) để chống timing attack.

## Cách hoạt động
Một request đi qua các lớp bảo vệ:
```
Client ─HTTPS─► WAF/Rate limit ─► Reverse proxy (TLS, header) ─► App
   App: parse + giới hạn kích thước → validate input → AuthN (token/session)
        → AuthZ (có quyền trên tài nguyên này không) → nghiệp vụ
        → truy vấn DB tham số hóa với user DB quyền tối thiểu
        → trả response đã lọc dữ liệu nhạy cảm, lỗi chung chung; log sự kiện
```

## Ví dụ
Ký và kiểm tra webhook bằng HMAC-SHA256:
```go
func sign(secret, body []byte) string {
    mac := hmac.New(sha256.New, secret)
    mac.Write(body)
    return hex.EncodeToString(mac.Sum(nil))
}

func verify(secret, body []byte, signatureHex string) bool {
    expected := sign(secret, body)
    return hmac.Equal([]byte(expected), []byte(signatureHex)) // so sánh thời gian hằng
}
```

Sinh token ngẫu nhiên an toàn:
```go
b := make([]byte, 32)
if _, err := rand.Read(b); err != nil { // crypto/rand
    return "", err
}
token := base64.RawURLEncoding.EncodeToString(b)
```

Chống IDOR khi lấy đơn hàng:
```go
func (r *OrderRepo) FindForUser(ctx context.Context, orderID, userID int64) (Order, error) {
    var o Order
    err := r.db.QueryRowContext(ctx,
        "SELECT id, total, status FROM orders WHERE id = $1 AND user_id = $2",
        orderID, userID).Scan(&o.ID, &o.Total, &o.Status)
    if errors.Is(err, sql.ErrNoRows) {
        return Order{}, ErrNotFound // trả 404, không tiết lộ đơn có tồn tại hay không
    }
    return o, err
}
```

## Hiểu nhầm thường gặp
- **"Base64 là mã hóa"**: chỉ là encoding, ai cũng giải được.
- **"Hash SHA-256 là đủ để lưu mật khẩu"**: quá nhanh; cần bcrypt/Argon2 có salt và cost.
- **"JWT được mã hóa nên an toàn để chứa dữ liệu"**: JWT thông thường chỉ được ký; payload đọc được.
- **"Đã validate ở frontend"**: kẻ tấn công gọi thẳng API, bỏ qua frontend.
- **"Dùng HTTPS là ứng dụng an toàn"**: HTTPS chỉ bảo vệ đường truyền; SQL injection, IDOR vẫn xảy ra.
- **"Escape input khi lưu"**: lưu dữ liệu nguyên gốc; escape khi **xuất** theo đúng ngữ cảnh (HTML, SQL qua placeholder, shell).

## Câu hỏi ôn tập
1. **SQL injection là gì? Cách phòng?** Parameterized query, whitelist cho tên cột, least privilege.
2. **XSS và CSRF khác nhau? Cách phòng?**
3. **Lưu mật khẩu thế nào? Salt là gì?**
4. **Hash, encryption, encoding khác nhau?**
5. **Mã hóa đối xứng và bất đối xứng? HTTPS dùng loại nào?** Cả hai.
6. **Authentication vs authorization? 401 vs 403?**
7. **JWT gồm những phần nào? Ưu nhược điểm so với session?** Stateless, scale dễ; khó thu hồi, payload đọc được.
8. **IDOR là gì?** Truy cập tài nguyên người khác bằng cách đổi ID; kiểm tra quyền sở hữu ở server.
9. **Quản lý secret trong ứng dụng thế nào?**

## Liên quan
- [02-backend-architecture.md](02-backend-architecture.md): HTTP, middleware xác thực.
- [10-databases.md](10-databases.md): parameterized query.
- [../internet/10-network-security.md](../internet/10-network-security.md): TLS, firewall, mã hóa trên mạng.
