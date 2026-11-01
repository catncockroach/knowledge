# Backend architecture

> Backend là phần chạy phía server: nhận request từ client qua mạng, thực thi nghiệp vụ, đọc/ghi dữ liệu và trả response. File này mô tả bức tranh tổng thể: một request đi qua những tầng nào, code backend được tổ chức ra sao, monolith và microservices khác gì, và cách đọc một tài liệu giải pháp hệ thống.

## Tại sao cần biết
Trước khi đi vào ngôn ngữ, thuật toán hay database, cần biết từng mảnh đó nằm ở đâu trong hệ thống. Interview thường mở đầu bằng "điều gì xảy ra khi gõ URL vào trình duyệt", "REST là gì", "monolith vs microservices", hoặc yêu cầu giải thích kiến trúc dự án bạn từng làm. Ở công việc hằng ngày, bạn phải đọc tài liệu giải pháp (solution document) để hiểu mình code phần nào.

## Khái niệm cốt lõi

### Mô hình client-server
- **Client** gửi yêu cầu (trình duyệt, app mobile, service khác). **Server** lắng nghe trên một địa chỉ IP + port, xử lý và trả kết quả.
- Giao tiếp qua mạng theo bộ giao thức TCP/IP. Backend cần nắm tối thiểu:
  - **IP + port** xác định một tiến trình trên mạng (vd `10.0.0.5:8080`).
  - **TCP**: tin cậy, có thứ tự, bắt tay 3 bước; nền của HTTP/1.1, HTTP/2, gRPC, kết nối DB. **UDP**: không kết nối, không đảm bảo, nhanh; dùng cho DNS, streaming, game, RADIUS.
  - **DNS** đổi tên miền thành IP. **HTTP/HTTPS** là giao thức ứng dụng phổ biến nhất của backend; HTTPS = HTTP chạy trên TLS.
  - Chi tiết ở [../internet/07-transport-layer.md](../internet/07-transport-layer.md), [../internet/08-dns-and-dhcp.md](../internet/08-dns-and-dhcp.md), [../internet/09-http-and-web.md](../internet/09-http-and-web.md).

### HTTP căn bản cho backend
Một HTTP request gồm method, path, header, body:

```http
POST /api/v1/orders HTTP/1.1
Host: shop.example.com
Content-Type: application/json
Authorization: Bearer eyJhbGciOi...

{"product_id": 42, "quantity": 2}
```

Response:

```http
HTTP/1.1 201 Created
Content-Type: application/json

{"id": 1001, "status": "pending"}
```

| Method | Ý nghĩa | Idempotent | Safe |
|---|---|---|---|
| GET | Đọc tài nguyên | Có | Có |
| POST | Tạo mới / hành động | Không | Không |
| PUT | Thay thế toàn bộ tài nguyên | Có | Không |
| PATCH | Sửa một phần | Không nhất thiết | Không |
| DELETE | Xóa | Có | Không |

- **Safe**: không thay đổi trạng thái server. **Idempotent**: gọi 1 lần hay N lần cho cùng kết quả trên server (quan trọng khi client retry).
- Nhóm status code: `2xx` thành công (200 OK, 201 Created, 204 No Content), `3xx` chuyển hướng, `4xx` lỗi phía client (400 Bad Request, 401 Unauthorized = chưa xác thực, 403 Forbidden = không có quyền, 404 Not Found, 409 Conflict, 422, 429 Too Many Requests), `5xx` lỗi phía server (500, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout).
- HTTP là **stateless**: mỗi request độc lập, server không tự nhớ request trước. Muốn "nhớ" người dùng thì dùng cookie/session hoặc token (JWT).

### REST API
REST là phong cách thiết kế API xoay quanh **tài nguyên** (resource) được định danh bằng URL và thao tác bằng HTTP method:

```
GET    /users          danh sách user
GET    /users/42       một user
POST   /users          tạo user
PUT    /users/42       thay thế user 42
PATCH  /users/42       sửa một phần
DELETE /users/42       xóa
GET    /users/42/orders  đơn hàng của user 42
```
Nguyên tắc: URL là danh từ (không phải `/getUser`), dùng đúng method và status code, stateless, có versioning (`/v1/`), phân trang (`?page=2&limit=20`) cho danh sách.

Các kiểu giao tiếp khác: **gRPC** (HTTP/2 + Protocol Buffers, nhanh, hợp cho service-to-service), **GraphQL** (client tự chọn trường cần lấy), **WebSocket** (kết nối hai chiều lâu dài), **message queue** (bất đồng bộ).

### Các thành phần hạ tầng thường gặp
```
Client ──► DNS ──► Load Balancer / Reverse Proxy (Nginx) ──► App servers (Go) ──► Cache (Redis)
                                                                   │              
                                                                   ├──► Database (PostgreSQL)
                                                                   └──► Message queue (Kafka/RabbitMQ) ──► Worker
```
- **Web server / reverse proxy** (Nginx, HAProxy, Envoy): nhận kết nối từ ngoài, kết thúc TLS, phục vụ file tĩnh, chuyển tiếp request vào app server, nén, giới hạn tốc độ. Trong Go, gói `net/http` đã là một HTTP server đầy đủ, nên app Go thường đứng sau reverse proxy chứ không cần Apache/Tomcat.
- **Load balancer**: chia tải cho nhiều instance (round robin, least connections, hash). Cho phép **scale ngang** (thêm máy) và chịu lỗi (một instance chết, chuyển sang instance khác qua health check).
- **Cache** (Redis, Memcached): lưu kết quả đọc nhiều trong RAM để giảm tải DB và giảm latency. Vấn đề khó: khi nào xóa cache (invalidation), TTL.
- **Database**: lưu trữ bền vững. Xem [10-databases.md](10-databases.md).
- **Message queue / broker**: service A đẩy message, service B xử lý sau. Tách rời các service, chịu tải đột biến, xử lý bất đồng bộ (gửi email, xử lý ảnh).
- **API gateway**: cửa ngõ duy nhất cho nhiều microservice: định tuyến, xác thực, rate limit.

### Scale và stateless
- **Scale dọc** (vertical): máy mạnh hơn; đơn giản nhưng có giới hạn. **Scale ngang** (horizontal): thêm máy; cần service **stateless**, tức không giữ trạng thái người dùng trong RAM của riêng instance (đưa session vào Redis/DB), để request nào rơi vào instance nào cũng được.

### Tổ chức code: layered architecture
Cách tổ chức phổ biến nhất cho một service:

```
┌──────────────────────────────┐
│ Transport / Handler          │  parse HTTP/gRPC, validate input, trả response
├──────────────────────────────┤
│ Service / Use case           │  logic nghiệp vụ, không biết HTTP hay SQL
├──────────────────────────────┤
│ Repository / Data access     │  đọc/ghi DB, cache, gọi API ngoài
└──────────────────────────────┘
          ▼ phụ thuộc đi xuống qua interface
```
- Mỗi tầng chỉ gọi tầng ngay dưới, qua **interface**. Nhờ vậy test được tầng service bằng repository giả (mock), đổi PostgreSQL sang MySQL không ảnh hưởng nghiệp vụ. Đây là ứng dụng trực tiếp của SOLID (D — Dependency Inversion) và Dependency Injection, xem [07-design-patterns.md](07-design-patterns.md), [08-clean-code-and-solid.md](08-clean-code-and-solid.md).
- Biến thể: Clean Architecture, Hexagonal (Ports & Adapters): cùng tinh thần "nghiệp vụ ở giữa, chi tiết kỹ thuật ở rìa".

Cấu trúc thư mục Go thường gặp:
```
myservice/
├── cmd/server/main.go        # điểm vào, wiring dependency
├── internal/
│   ├── handler/              # HTTP handlers
│   ├── service/              # nghiệp vụ
│   ├── repository/           # truy cập DB
│   └── model/                # struct dữ liệu
├── migrations/               # SQL migration
├── go.mod
└── Dockerfile
```

### Monolith và microservices
| | Monolith | Microservices |
|---|---|---|
| Định nghĩa | Một ứng dụng, một codebase, deploy một khối | Nhiều service nhỏ, mỗi service một nghiệp vụ, deploy độc lập |
| Giao tiếp nội bộ | Gọi hàm | Qua mạng (HTTP, gRPC, message queue) |
| Ưu điểm | Đơn giản, dễ debug, transaction dễ, nhanh lúc đầu | Scale riêng từng phần, team độc lập, lỗi cô lập, chọn công nghệ riêng |
| Nhược điểm | Codebase phình to, deploy cả khối, scale cả khối | Phức tạp vận hành, lỗi mạng, khó transaction phân tán, cần monitoring/tracing |
| Khi nào | Sản phẩm mới, team nhỏ | Hệ thống lớn, nhiều team, nghiệp vụ tách bạch rõ |

Microservices kéo theo: **service discovery**, **database per service**, **distributed tracing**, **circuit breaker**, **eventual consistency**, container (Docker) và orchestration (Kubernetes).

### Container và triển khai (sơ lược)
- **Docker image**: gói ứng dụng + thư viện + cấu hình chạy, build từ `Dockerfile`. **Container**: một image đang chạy, cô lập bằng tính năng kernel Linux (namespaces, cgroups), nhẹ hơn máy ảo vì dùng chung kernel host.
- **Kubernetes (k8s)**: điều phối nhiều container trên cụm máy: tự khởi động lại, scale, rolling update, service discovery. Đơn vị nhỏ nhất là **Pod**.
- **CI/CD**: mỗi lần push code, pipeline tự chạy build, test, lint (CI) rồi triển khai (CD).

```dockerfile
# multi-stage build cho Go: image cuối chỉ chứa binary
FROM golang:1.22 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /app ./cmd/server

FROM gcr.io/distroless/static
COPY --from=build /app /app
ENTRYPOINT ["/app"]
```

### Quan sát hệ thống (observability)
- **Log**: ghi sự kiện, nên dùng log có cấu trúc (JSON, `log/slog` trong Go) kèm request ID.
- **Metrics**: số đo theo thời gian (request/s, latency p95/p99, error rate), thường Prometheus + Grafana.
- **Tracing**: theo dấu một request đi qua nhiều service (OpenTelemetry).

## Cách hoạt động
Điều gì xảy ra khi người dùng gửi `GET https://shop.example.com/api/v1/products/42`:

1. Client hỏi DNS lấy IP của `shop.example.com`.
2. Mở kết nối TCP (bắt tay 3 bước) tới load balancer, bắt tay TLS để mã hóa.
3. Gửi HTTP request. Load balancer/reverse proxy chọn một instance app server khỏe và chuyển tiếp.
4. Trong app Go: router khớp path → **middleware** (log, xác thực token, recover panic, đo latency) → **handler** parse tham số `42`.
5. Handler gọi **service** `GetProduct(ctx, 42)`. Service hỏi **cache** trước; cache miss thì gọi **repository** truy vấn DB qua connection pool, rồi ghi lại cache.
6. Handler đóng gói kết quả thành JSON, đặt status 200, trả về. Nếu không có sản phẩm thì 404; DB lỗi thì 500 và log chi tiết (không lộ chi tiết ra client).
7. Response đi ngược lại qua proxy về client.

## Ví dụ
Một service tối giản đủ ba tầng bằng Go chuẩn (`net/http`, Go 1.22+ hỗ trợ method và path param trong pattern):

```go
// model
type Product struct {
    ID    int64  `json:"id"`
    Name  string `json:"name"`
    Price int64  `json:"price"`
}

var ErrNotFound = errors.New("not found")

// repository: interface để service không phụ thuộc DB cụ thể
type ProductRepository interface {
    FindByID(ctx context.Context, id int64) (Product, error)
}

// service
type ProductService struct{ repo ProductRepository }

func (s *ProductService) Get(ctx context.Context, id int64) (Product, error) {
    if id <= 0 {
        return Product{}, fmt.Errorf("invalid id %d", id)
    }
    return s.repo.FindByID(ctx, id)
}

// handler
type ProductHandler struct{ svc *ProductService }

func (h *ProductHandler) Get(w http.ResponseWriter, r *http.Request) {
    id, err := strconv.ParseInt(r.PathValue("id"), 10, 64)
    if err != nil {
        http.Error(w, "bad id", http.StatusBadRequest)
        return
    }
    p, err := h.svc.Get(r.Context(), id)
    switch {
    case errors.Is(err, ErrNotFound):
        http.Error(w, "not found", http.StatusNotFound)
        return
    case err != nil:
        slog.Error("get product", "id", id, "err", err)
        http.Error(w, "internal error", http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(p)
}

func main() {
    repo := NewPostgresProductRepo(db) // implement ProductRepository
    h := &ProductHandler{svc: &ProductService{repo: repo}}

    mux := http.NewServeMux()
    mux.HandleFunc("GET /api/v1/products/{id}", h.Get)
    log.Fatal(http.ListenAndServe(":8080", mux))
}
```

## Đọc tài liệu giải pháp hệ thống
Tài liệu giải pháp (solution/design document) mô tả hệ thống sẽ được xây thế nào. Cách đọc hiệu quả:

1. **Bối cảnh và mục tiêu**: bài toán gì, ai dùng, yêu cầu chức năng (functional) và phi chức năng (non-functional: hiệu năng, sẵn sàng, bảo mật, khả năng mở rộng).
2. **Sơ đồ kiến trúc tổng thể** (*component/context diagram*): có những thành phần nào, kết nối bằng giao thức gì, dữ liệu đi theo hướng nào, đâu là biên hệ thống (cái gì của mình, cái gì của bên ngoài).
3. **Sequence diagram**: thứ tự các bước giữa các thành phần cho một luồng nghiệp vụ. Đọc từ trên xuống, mũi tên liền là gọi, mũi tên nét đứt là trả về. Đặc biệt chú ý luồng lỗi (timeout, retry, rollback).
4. **Mô hình dữ liệu** (ERD): bảng, khóa, quan hệ 1-n, n-n.
5. **Đặc tả API** (OpenAPI/Swagger, file `.proto`): endpoint, request/response, mã lỗi.
6. **Các quyết định và đánh đổi**: vì sao chọn A thay vì B.

Khi đọc, tự trả lời được các câu: luồng chính đi qua những thành phần nào; phần mình code nhận input gì, trả output gì, gọi ai; nếu thành phần X chết thì sao; dữ liệu được lưu ở đâu, nhất quán thế nào. Chỗ nào tài liệu mâu thuẫn hoặc thiếu (luồng lỗi không được mô tả, trường dữ liệu không khớp giữa API và DB) thì ghi lại và hỏi; phát hiện lỗi logic trong tài liệu sớm rẻ hơn nhiều so với phát hiện khi đã code.

Ví dụ sequence diagram cho luồng đặt hàng:

```mermaid
sequenceDiagram
    participant C as Client
    participant O as Order Service
    participant I as Inventory Service
    participant DB as Order DB
    participant Q as Message Queue
    C->>O: POST /orders
    O->>I: Reserve(product, qty)
    I-->>O: OK
    O->>DB: INSERT order (pending)
    O->>Q: publish OrderCreated
    O-->>C: 201 Created
```

## Hiểu nhầm thường gặp
- **"Microservices luôn tốt hơn monolith"**: microservices đổi độ phức tạp code lấy độ phức tạp vận hành và mạng. Với team nhỏ, monolith tổ chức tốt thường là lựa chọn đúng.
- **"401 và 403 như nhau"**: 401 là chưa xác thực (không biết bạn là ai), 403 là đã biết nhưng không có quyền.
- **"PUT và POST thay nhau được"**: PUT idempotent và thay thế toàn bộ tài nguyên ở URL chỉ định; POST thì không idempotent.
- **"Stateless nghĩa là không có dữ liệu"**: stateless là instance không giữ trạng thái phiên trong RAM riêng; dữ liệu vẫn nằm ở DB/cache dùng chung.

## Câu hỏi

**Chuyện gì xảy ra khi gõ URL vào trình duyệt?**
> - **DNS**: hệ thống đổi tên miền (`shop.example.com`) thành địa chỉ IP.
> - **TCP / TLS**: TCP thiết lập kết nối tin cậy giữa hai máy; TLS mã hóa kết nối đó (HTTPS).
> - **Load balancer (LB)**: máy đứng trước nhiều server, chia request cho chúng.
>
> Quy tắc: request đi qua lần lượt các tầng, mỗi tầng giải một bài toán riêng: *tìm* máy (DNS), *nối* tới máy (TCP), *bảo mật* kênh (TLS), *nói chuyện* (HTTP), *phân phối* (LB), *xử lý* (app gọi cache/DB), rồi *hiển thị* (trình duyệt parse HTML, tải thêm CSS/JS/ảnh, render).
>
> Chuỗi cụ thể: trình duyệt tra cache DNS → hỏi DNS resolver → có IP → bắt tay TCP (3-way handshake) → bắt tay TLS, kiểm certificate → gửi `GET /` → LB chọn một instance app → handler → service → repository đọc cache hoặc DB → trả response kèm status code → trình duyệt render.
>
> Ranh giới: nhiều bước bị bỏ qua nhờ cache (DNS cache, kết nối keep-alive, CDN trả luôn file tĩnh). Câu hỏi này dùng để kiểm tra bạn nối được các tầng với nhau; trả lời theo thứ tự tầng là đủ, sau đó đào sâu tầng mình hiểu nhất.

**REST là gì? Thế nào là API RESTful tốt?**
> - **REST**: phong cách thiết kế API trên HTTP, coi mọi thứ là *tài nguyên* (resource) có URL, và thao tác lên tài nguyên bằng các HTTP method chuẩn.
> - **Stateless**: mỗi request tự mang đủ thông tin (vd token), server không nhớ trạng thái phiên giữa các request.
>
> API RESTful tốt dùng đúng ngữ nghĩa có sẵn của HTTP thay vì tự đặt quy ước riêng: URL là danh từ số nhiều (`/orders/42`, không phải `/getOrder?id=42`); method nói hành động (GET đọc, POST tạo, PUT thay toàn bộ, PATCH sửa một phần, DELETE xóa); status code nói kết quả (200, 201 Created, 400, 401, 403, 404, 409, 500); có versioning (`/v1/`), phân trang, lọc, sắp xếp cho danh sách; lỗi trả về theo một format thống nhất.
>
> Ranh giới: stateless giúp scale ngang dễ, vì bất kỳ instance nào cũng xử lý được request. Không phải hành động nào cũng là CRUD; thao tác như "hủy đơn" thường mô hình hóa thành sub-resource (`POST /orders/42/cancel`) hoặc đổi trạng thái (`PATCH status`). gRPC và GraphQL là các lựa chọn khác, không theo REST.

**Idempotent là gì, method nào idempotent?**
> - **Idempotent**: gọi một thao tác một lần hay nhiều lần thì *trạng thái server* sau cùng vẫn như nhau.
> - **Safe method**: method không làm thay đổi trạng thái server (chỉ đọc).
>
> Theo chuẩn HTTP: GET, HEAD, OPTIONS là safe nên idempotent; PUT và DELETE không safe nhưng idempotent (đặt tài nguyên thành giá trị X hai lần vẫn là X, xóa hai lần vẫn là đã xóa); POST và PATCH không đảm bảo idempotent (POST tạo đơn hai lần ra hai đơn). Ý nghĩa thực tế: client, proxy được phép tự *retry* method idempotent khi mạng lỗi mà không gây hậu quả.
>
> Ranh giới: idempotent nói về trạng thái, không về response: DELETE lần hai có thể trả 404 nhưng vẫn idempotent. Với thao tác không idempotent như thanh toán, API thường nhận `Idempotency-Key` từ client để server nhận ra request lặp và không xử lý hai lần.

**Monolith vs microservices?**
> - **Monolith**: toàn bộ ứng dụng là một codebase, build và deploy thành một khối.
> - **Microservices**: ứng dụng chia thành nhiều service nhỏ, mỗi service một nghiệp vụ, deploy độc lập, giao tiếp qua mạng (HTTP, gRPC, message queue), thường có DB riêng.
>
> Tiêu chí quyết định là *đánh đổi giữa độc lập và độ phức tạp*. Microservices cho từng team deploy, scale, chọn công nghệ độc lập, lỗi một service ít lan sang service khác; cái giá là gọi qua mạng (chậm, có thể lỗi), dữ liệu phân tán (khó transaction), cần hạ tầng vận hành (service discovery, tracing, CI/CD nhiều pipeline). Monolith đơn giản, gọi hàm trực tiếp, transaction dễ, phù hợp team nhỏ, sản phẩm mới.
>
> Ranh giới: microservices là lời giải cho vấn đề *tổ chức* (nhiều team dẫm chân nhau) nhiều hơn là vấn đề kỹ thuật. Chia sai ranh giới tạo "distributed monolith": nhiều service nhưng phải deploy cùng nhau. Nhiều hệ thống bắt đầu bằng modular monolith (một khối nhưng chia module rõ) rồi mới tách dần.

**Load balancer làm gì?**
> - **Load balancer**: thành phần nhận request rồi phân phối cho một nhóm server phía sau (backend pool).
> - **Health check**: LB định kỳ gọi thử từng server để biết server nào còn sống.
>
> LB cho phép *scale ngang* (thêm server để chịu thêm tải) và *chịu lỗi* (server chết bị loại khỏi pool, client không thấy). Nó chọn server theo thuật toán: round robin, least connections, hash theo IP hay key. LB tầng 4 chia theo kết nối TCP/UDP; LB tầng 7 hiểu HTTP nên định tuyến được theo path, header, và thường kiêm TLS termination.
>
> Ranh giới: muốn LB chia request tự do thì app phải stateless; nếu lưu session trong RAM của server thì phải dùng sticky session hoặc chuyển session ra Redis. Bản thân LB cũng có thể là điểm lỗi duy nhất, nên thường chạy theo cặp hoặc dùng dịch vụ LB của cloud.

**Vì sao chia handler / service / repository?**
> - **Handler**: tầng nhận HTTP request, parse và validate input, gọi service, trả response.
> - **Service**: tầng chứa logic nghiệp vụ (quy tắc, tính toán), không biết HTTP hay SQL.
> - **Repository**: tầng truy cập dữ liệu, che giấu DB cụ thể sau một interface.
>
> Quy tắc: mỗi tầng chỉ có *một lý do để thay đổi* và chỉ phụ thuộc vào tầng dưới qua interface. Nhờ vậy đổi PostgreSQL sang MySQL chỉ sửa repository; thêm gRPC bên cạnh HTTP chỉ thêm handler; logic nghiệp vụ test được bằng repository giả (mock/fake) mà không cần DB.
>
> Ranh giới: không có tầng nào được "nhảy cóc" (handler gọi thẳng SQL) hoặc rò chi tiết (service trả `sql.Rows`). Với chương trình rất nhỏ, ba tầng có thể là thừa; đây là áp dụng của Single Responsibility và Dependency Inversion, xem [08-clean-code-and-solid.md](08-clean-code-and-solid.md).

**TCP khác UDP?**
> - **TCP**: giao thức tầng transport có kết nối, đảm bảo dữ liệu tới đủ, đúng thứ tự, không trùng.
> - **UDP**: giao thức transport không kết nối, gửi từng gói độc lập, không đảm bảo gì.
>
> Tiêu chí chọn: cần *đúng và đủ* thì dùng TCP; cần *nhanh, độ trễ thấp* và chấp nhận mất một ít thì dùng UDP. TCP đạt độ tin cậy nhờ bắt tay 3 bước, số thứ tự, ACK và gửi lại, điều khiển luồng và tắc nghẽn, cái giá là độ trễ thêm. HTTP/1.1, HTTP/2, database, SSH dùng TCP; DNS, video call, game, streaming dùng UDP.
>
> Ranh giới: UDP không có nghĩa là ứng dụng không tin cậy; ứng dụng có thể tự làm tin cậy trên UDP, như QUIC (nền của HTTP/3) làm lại các tính năng của TCP trên UDP. Kiến thức mạng sâu hơn ở domain [internet](../internet/README.md).

**Docker khác máy ảo?**
> - **Máy ảo (VM)**: máy tính giả lập bởi hypervisor, có hệ điều hành khách và kernel riêng.
> - **Container**: process được cô lập (bằng namespace và cgroup của Linux), chạy chung kernel với máy host. **Docker** là công cụ phổ biến để build và chạy container.
>
> Khác biệt gốc là *ranh giới ảo hóa*: VM ảo hóa phần cứng, container ảo hóa hệ điều hành. Vì không cần boot kernel riêng, container khởi động trong khoảng giây, image chỉ vài chục MB, một máy chạy được nhiều container. Image đóng gói app cùng thư viện, nên "chạy được trên máy tôi" thì chạy được mọi nơi.
>
> Ranh giới: container cô lập yếu hơn VM (chung kernel, lỗ hổng kernel ảnh hưởng tất cả), và không chạy được hệ điều hành khác kernel host (container Linux trên Mac/Windows thực ra chạy trong một VM Linux nhỏ). Trên cloud, container thường chạy *bên trong* VM: hai thứ kết hợp chứ không loại trừ nhau.

## Liên quan
- [01-operating-systems.md](01-operating-systems.md): service là một process trên OS.
- [03-go-basics.md](03-go-basics.md): ngôn ngữ dùng để viết các tầng trên.
- [10-databases.md](10-databases.md): tầng lưu trữ.
- [12-secure-coding.md](12-secure-coding.md): xác thực, phân quyền, TLS.
