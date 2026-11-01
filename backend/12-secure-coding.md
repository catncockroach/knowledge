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

## Câu hỏi và trả lời

**SQL injection là gì? Cách phòng?**
> - **Injection**: lớp lỗ hổng khi dữ liệu không tin cậy bị trình thông dịch (SQL, shell, HTML) hiểu thành *lệnh*.
> - **SQL injection**: injection vào câu SQL do ghép chuỗi input của người dùng.
>
> Ví dụ `"SELECT * FROM users WHERE email = '" + email + "'"` với input `' OR '1'='1` thành điều kiện luôn đúng, trả về mọi user; input khác có thể xóa bảng hay đọc dữ liệu bảng khác. Gốc rễ là *trộn mã và dữ liệu*, nên cách phòng chính là tách chúng: dùng parameterized query/placeholder (`WHERE email = $1`) để DB luôn coi input là dữ liệu. Những phần không dùng placeholder được (tên cột trong `ORDER BY`, `ASC/DESC`) thì đối chiếu với whitelist. Thêm lớp phòng thủ: tài khoản DB của app chỉ có quyền tối thiểu (least privilege), không hiện lỗi SQL thô cho người dùng.
>
> Ranh giới: escape thủ công dễ sót, không thay được placeholder. ORM an toàn khi dùng API bình thường nhưng vẫn bị injection nếu ghép chuỗi vào phần raw SQL. Cùng nguyên lý áp cho command injection (`exec.Command` với tham số tách riêng, không qua shell).

**XSS và CSRF khác nhau? Cách phòng?**
> - **XSS (Cross-Site Scripting)**: kẻ tấn công chèn được script vào trang web của bạn, script chạy trong trình duyệt nạn nhân với quyền của trang (đọc dữ liệu, gửi request thay người dùng).
> - **CSRF (Cross-Site Request Forgery)**: trang web *khác* khiến trình duyệt nạn nhân gửi request tới trang của bạn, trình duyệt tự kèm cookie nên request mang danh tính nạn nhân.
>
> Khác biệt cốt lõi: XSS là *trang bạn chạy mã của kẻ tấn công*; CSRF là *trang của kẻ tấn công mượn phiên đăng nhập* của nạn nhân trên trang bạn, mà không cần đọc được gì.
> - Phòng XSS: escape output theo đúng ngữ cảnh khi chèn vào HTML (`html/template` của Go tự làm), không chèn HTML thô từ người dùng, đặt Content-Security-Policy, cookie phiên `HttpOnly` để script không đọc được.
> - Phòng CSRF: cookie `SameSite=Lax/Strict`, CSRF token trong form, kiểm tra header `Origin`, không dùng GET cho thao tác thay đổi dữ liệu.
>
> Ranh giới: API xác thực bằng header `Authorization: Bearer` (không dùng cookie) không bị CSRF vì trình duyệt không tự gửi header đó, nhưng vẫn có thể bị XSS. Có XSS thì mọi biện pháp chống CSRF đều vô dụng, vì script chạy ngay trên trang đọc được token.

**Lưu mật khẩu thế nào? Salt là gì?**
> - **Hash**: hàm một chiều biến dữ liệu thành chuỗi cố định, không đảo ngược được.
> - **Salt**: chuỗi ngẫu nhiên riêng cho *từng* mật khẩu, trộn vào trước khi hash và lưu cùng hash.
> - **Password hashing function**: hàm hash được thiết kế *chậm có chủ đích* cho mật khẩu: bcrypt, scrypt, Argon2.
>
> Quy tắc: không lưu mật khẩu dạng gốc hay mã hóa được (giải mã được thì lộ khóa là lộ hết), chỉ lưu hash có salt bằng hàm hash chậm. Khi đăng nhập, hash mật khẩu nhập vào với cùng salt rồi so sánh. Salt làm hai người cùng mật khẩu có hash khác nhau, vô hiệu hóa bảng tra sẵn (rainbow table); hàm chậm (có tham số cost) làm mỗi lần đoán tốn thời gian, nên brute force hàng tỷ mật khẩu trở nên quá đắt.
>
> Ranh giới: SHA-256 hay MD5 *không* dùng cho mật khẩu dù có salt, vì quá nhanh (GPU thử hàng tỷ lần mỗi giây). Trong Go dùng `golang.org/x/crypto/bcrypt` hoặc `argon2`; bcrypt tự sinh và lưu salt trong chuỗi kết quả. Salt không cần bí mật; "pepper" là khóa bí mật thêm vào, lưu ngoài DB.

**Hash, encryption, encoding khác nhau?**
> - **Encoding**: đổi dữ liệu sang định dạng khác để *truyền hoặc lưu* được (Base64, URL encoding, UTF-8). Không có khóa, ai cũng đảo ngược được.
> - **Encryption**: biến dữ liệu thành dạng không đọc được để *giữ bí mật*; chỉ ai có khóa mới giải mã được (AES, RSA).
> - **Hash**: biến dữ liệu thành chuỗi độ dài cố định, *một chiều*, dùng để *kiểm tra toàn vẹn hay so khớp* (SHA-256, bcrypt).
>
> Tiêu chí phân biệt: có đảo ngược được không, và cần gì để đảo ngược. Encoding: đảo được, không cần khóa, nên *không bảo mật gì*. Encryption: đảo được khi có khóa. Hash: không đảo được, chỉ so được bằng cách hash lại đầu vào. Chọn theo mục đích: cần đọc lại dữ liệu gốc (số thẻ, token gọi API bên thứ ba) thì mã hóa; chỉ cần kiểm tra khớp (mật khẩu) hoặc phát hiện thay đổi (checksum file) thì hash.
>
> Ranh giới: Base64 hay gặp trong JWT, header Basic Auth, nên hay bị nhầm là mã hóa; nó chỉ là encoding. HMAC là hash có khóa, dùng để chứng minh dữ liệu không bị sửa và do người giữ khóa tạo ra.

**Mã hóa đối xứng và bất đối xứng? HTTPS dùng loại nào?**
> - **Mã hóa đối xứng**: một khóa dùng cho cả mã hóa và giải mã (AES, ChaCha20). Nhanh, nhưng hai bên phải có chung khóa bí mật.
> - **Mã hóa bất đối xứng**: cặp khóa public/private; dữ liệu mã hóa bằng khóa này chỉ giải được bằng khóa kia (RSA, elliptic curve). Chậm hơn nhiều, nhưng khóa public công khai được.
>
> Hai loại giải hai bài toán khác nhau: đối xứng giải bài toán *mã hóa khối lượng lớn nhanh*; bất đối xứng giải bài toán *trao đổi khóa và xác thực* giữa hai bên chưa từng gặp (chữ ký số, certificate). HTTPS (TLS) dùng *cả hai*: trong lúc bắt tay, dùng bất đối xứng để xác thực server (certificate có chữ ký) và thỏa thuận một khóa phiên (trao đổi khóa Diffie-Hellman trên elliptic curve, ECDHE); sau đó toàn bộ dữ liệu được mã hóa bằng khóa phiên đối xứng (AES-GCM hoặc ChaCha20-Poly1305).
>
> Ranh giới: TLS 1.3 không còn dùng RSA để *mã hóa* khóa phiên mà chỉ dùng trao đổi khóa (EC)DHE, nhờ đó có forward secrecy: lộ private key sau này không giải mã được phiên cũ. RSA/ECDSA vẫn dùng để *ký*. Chi tiết TLS ở domain [internet](../internet/README.md).

**Authentication vs authorization? 401 vs 403?**
> - **Authentication (xác thực)**: xác định *bạn là ai* (mật khẩu, token, OTP, certificate).
> - **Authorization (phân quyền)**: xác định *bạn được làm gì* với tài nguyên nào (role, quyền sở hữu, policy).
>
> Authentication luôn đi trước: phải biết là ai rồi mới quyết định quyền. Mã HTTP tương ứng: **401 Unauthorized** nghĩa là *chưa xác thực* hoặc xác thực sai (thiếu token, token hết hạn), client nên đăng nhập lại; **403 Forbidden** nghĩa là *đã biết bạn là ai nhưng bạn không có quyền*, đăng nhập lại cũng không thay đổi gì. Ví dụ user thường gọi API admin nhận 403; gọi khi token hết hạn nhận 401.
>
> Ranh giới: tên "401 Unauthorized" là cách đặt tên nhầm lịch sử của chuẩn HTTP, thực chất nghĩa là unauthenticated. Khi không muốn lộ việc tài nguyên tồn tại (vd đơn hàng của người khác), nhiều API trả 404 thay vì 403.

**JWT gồm những phần nào? Ưu nhược điểm so với session?**
> - **JWT (JSON Web Token)**: token tự chứa thông tin, gồm ba phần Base64URL nối bằng dấu chấm: **header** (thuật toán ký), **payload** (các claim: `sub`, `exp`, role...), **signature** (chữ ký trên header + payload).
> - **Session**: server lưu trạng thái đăng nhập (trong RAM, Redis, DB), client chỉ giữ session ID ngẫu nhiên trong cookie.
>
> Khác biệt gốc là *trạng thái nằm ở đâu*. JWT stateless: server chỉ cần kiểm chữ ký và hạn, không tra cứu kho nào, nên scale ngang và dùng giữa nhiều service dễ. Đổi lại: khó thu hồi trước khi hết hạn (đăng xuất, khóa tài khoản), vì không có chỗ nào để xóa; payload chỉ được *ký*, không mã hóa, ai cũng đọc được nên không chứa bí mật; token to hơn session ID. Session thu hồi tức thì (xóa ở server) nhưng mỗi request phải tra kho session.
>
> Ranh giới: cách thường dùng là access token JWT sống ngắn (vài phút) kèm refresh token lưu ở server để thu hồi được. Luôn kiểm tra thuật toán ký (không chấp nhận `alg: none`) và `exp`.

**IDOR là gì?**
> - **IDOR (Insecure Direct Object Reference)**: lỗ hổng phân quyền khi API cho truy cập object chỉ dựa trên ID người dùng gửi lên, mà không kiểm tra người gọi có quyền với object đó.
>
> Ví dụ user A gọi `GET /orders/1001` thấy đơn của mình, đổi thành `/orders/1002` thì thấy đơn của user B. Gốc rễ: server tin rằng "đã đăng nhập" là đủ, quên bước authorization *trên từng object*. Cách phòng: mọi truy cập object kiểm tra quyền sở hữu hoặc quyền ở server, tốt nhất là đưa vào ngay câu truy vấn: `WHERE id = $1 AND user_id = $2` với `user_id` lấy từ token, không lấy từ request.
>
> Ranh giới: dùng UUID thay ID tăng dần làm khó đoán ID nhưng *không* sửa được IDOR, vì ID vẫn có thể lộ qua link, log. IDOR là dạng phổ biến nhất của "Broken Access Control", hạng đầu OWASP Top 10.

**Quản lý secret trong ứng dụng thế nào?**
> - **Secret**: thông tin cho quyền truy cập: mật khẩu DB, API key, private key, khóa ký JWT.
> - **Secret manager**: hệ thống chuyên lưu, phân quyền, ghi log truy cập và xoay vòng secret (Vault, AWS Secrets Manager, Kubernetes Secret).
>
> Quy tắc: secret *không bao giờ* nằm trong source code hay git, vì lịch sử git giữ mãi và nhiều người truy cập được. App nhận secret lúc chạy qua biến môi trường hoặc file được mount, có nguồn gốc từ secret manager. Mỗi môi trường (dev, staging, prod) có secret riêng; mỗi service chỉ được cấp secret nó cần; secret được xoay vòng định kỳ và ngay khi nghi lộ.
>
> Ranh giới: không log secret (cẩn thận khi log cả config hay request header). Lỡ commit secret thì xóa khỏi git là chưa đủ: phải coi như đã lộ và thu hồi, tạo secret mới. File `.env` dùng cho máy dev, phải nằm trong `.gitignore`; công cụ quét như gitleaks phát hiện secret trước khi commit.

## Liên quan
- [02-backend-architecture.md](02-backend-architecture.md): HTTP, middleware xác thực.
- [10-databases.md](10-databases.md): parameterized query.
- [../internet/10-network-security.md](../internet/10-network-security.md): TLS, firewall, mã hóa trên mạng.
