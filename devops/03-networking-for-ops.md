# Networking for ops

> File này nhìn mạng từ góc người vận hành, tức người phải đưa traffic từ người dùng tới đúng service: chia dải IP (CIDR), mạng private và NAT, firewall, reverse proxy, load balancer L4/L7, và vai trò của DNS khi deploy.

## Tại sao cần biết
Domain [../internet/](../internet/README.md) giải thích các giao thức chạy thế nào: IP, TCP, DNS, HTTP, TLS. Người làm ops còn phải *thiết kế và gỡ lỗi* đường đi của traffic: dải IP của VPC có đủ cho số máy dự kiến không, vì sao service A không gọi được service B, load balancer nên chia tải ở tầng nào. Phần lớn sự cố "service không truy cập được" là lỗi mạng: sai firewall, sai DNS, health check fail.

## Khái niệm cốt lõi

### CIDR và subnet
- **CIDR** — **Là gì:** cách viết một dải IP dưới dạng `địa_chỉ/số_bit_mạng`. `10.0.0.0/16` nghĩa là 16 bit đầu cố định, 16 bit sau dành cho host, tức 2^16 = 65.536 địa chỉ. **Dùng để:** cấp phát và chia dải IP linh hoạt, không bị bó vào các lớp A/B/C cũ.
- **Subnet** — **Là gì:** một dải con cắt ra từ dải lớn hơn. **Dùng để:** nhóm máy theo vai trò (public, private, database) để áp luật định tuyến và firewall khác nhau cho từng nhóm.
- Quy tắc tính: một `/n` có 2^(32−n) địa chỉ. `/24` = 256, `/25` = 128, `/28` = 16. Mỗi lần tăng `n` thêm 1 thì dải chia đôi.
- Không phải địa chỉ nào cũng cấp được cho máy. Trong mạng truyền thống, địa chỉ đầu (network) và địa chỉ cuối (broadcast) bị giữ lại. Trên AWS, mỗi subnet bị giữ 5 địa chỉ (4 địa chỉ đầu và 1 địa chỉ cuối), nên một `/24` chỉ còn 251 địa chỉ dùng được.
- Chi tiết bit và mask ở [../internet/05-ip-addressing.md](../internet/05-ip-addressing.md).

### Mạng private và NAT
- **Private IP** — **Là gì:** ba dải dành cho mạng nội bộ theo RFC 1918: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`. Router trên Internet không định tuyến các địa chỉ này. **Dùng để:** đặt địa chỉ cho máy bên trong mà không tốn IP public, và để máy không bị truy cập trực tiếp từ Internet.
- **NAT (Network Address Translation)** — **Là gì:** thiết bị đổi địa chỉ IP (và port) trong gói tin khi gói đi qua nó.
  - **SNAT / NAT ra ngoài**: đổi IP nguồn private thành IP public. **Dùng để:** cho máy private *gọi ra* Internet (tải package, gọi API bên ngoài), trong khi bên ngoài vẫn không tự mở kết nối vào được. Trên cloud, đây là việc của NAT gateway.
  - **DNAT / port forwarding**: đổi IP đích public thành IP private. **Dùng để:** đưa traffic từ ngoài vào một máy bên trong.

### Port
- **Là gì:** số 16 bit (0–65535) xác định một tiến trình trên một máy. Cặp IP + port + giao thức xác định một điểm nhận kết nối.
- **Dùng để:** nhiều service cùng chạy trên một máy. Port ops hay gặp: 22 (SSH), 53 (DNS), 80 (HTTP), 443 (HTTPS), 5432 (PostgreSQL), 6379 (Redis).

### Firewall
- **Là gì:** bộ luật cho phép hoặc chặn traffic dựa trên IP nguồn/đích, port, giao thức và chiều đi.
- **Dùng để:** chỉ mở đúng những đường cần thiết. Ví dụ database chỉ nhận kết nối port 5432 từ subnet của app, không nhận từ Internet.
- **Stateful** — **Là gì:** firewall nhớ trạng thái kết nối. Đã cho phép chiều đi thì tự cho phép gói trả lời quay về. **Stateless** — **Là gì:** xét từng gói độc lập, nên phải viết luật cho cả hai chiều. Trên AWS, security group là stateful, network ACL là stateless ([06-cloud-fundamentals.md](06-cloud-fundamentals.md)).
- Trên một máy Linux, firewall nằm trong kernel (netfilter) và được cấu hình qua `iptables`/`nftables`, hoặc các công cụ dễ dùng hơn như `ufw`, `firewalld`.

### Proxy và reverse proxy
- **Forward proxy** — **Là gì:** đứng phía client, thay client gửi request ra ngoài. **Dùng để:** kiểm soát và lọc traffic đi ra của một công ty, cache nội dung.
- **Reverse proxy** — **Là gì:** đứng phía server, nhận request thay cho các server phía sau rồi chuyển tiếp vào trong (Nginx, HAProxy, Envoy, Traefik). **Dùng để:**
  - **TLS termination**: giải mã HTTPS tại một chỗ, để app phía sau không phải quản lý certificate.
  - **Routing**: chia request theo host hoặc path (`/api` → service A, `/` → frontend).
  - Nén, cache, giới hạn tốc độ (rate limit), giấu cấu trúc nội bộ.

### Load balancer
- **Là gì:** thành phần chia request hoặc kết nối cho nhiều instance phía sau (backend pool / target group).
- **Dùng để:** scale ngang (thêm instance để tăng tải chịu được) và chịu lỗi (instance chết thì không gửi traffic tới nữa).

| | **L4 load balancer** | **L7 load balancer** |
|---|---|---|
| Nhìn thấy gì | IP, port, giao thức TCP/UDP | Nội dung HTTP: host, path, header, cookie |
| Quyết định theo | Kết nối | Từng request |
| Làm được | Chia kết nối, rất nhanh, giao thức nào cũng được | Route theo path, sửa header, TLS termination, retry |
| Ví dụ trên AWS | Network Load Balancer (NLB) | Application Load Balancer (ALB) |

Thuật toán chia tải phổ biến: **round robin** (lần lượt), **least connections** (gửi cho instance đang ít kết nối nhất), **hash** theo IP hoặc key (cùng client luôn tới cùng instance).

- **Health check** — **Là gì:** load balancer định kỳ gọi tới từng instance (vd `GET /health`) và loại instance không trả lời đúng. **Dùng để:** tự động ngừng gửi traffic tới instance hỏng.
- **Sticky session** — **Là gì:** giữ một client luôn gắn với một instance. **Dùng để:** đỡ cho ứng dụng giữ session trong RAM. Cái giá phải trả là tải chia không đều và mất session khi instance chết. Ứng dụng stateless thì không cần cơ chế này.

### DNS khi vận hành
- Record hay dùng: **A/AAAA** (tên → IPv4/IPv6), **CNAME** (tên → tên khác, vd `api.example.com` → tên của load balancer).
- **TTL** — **Là gì:** thời gian (giây) resolver được phép cache một record. **Dùng để:** cân bằng giữa tải lên DNS server và tốc độ lan truyền thay đổi. TTL dài thì đổi IP xong phải chờ lâu mới hết người dùng IP cũ.
- Cơ chế DNS chi tiết ở [../internet/08-dns-and-dhcp.md](../internet/08-dns-and-dhcp.md).

## Cách hoạt động
Đường đi của một request HTTPS vào một hệ thống điển hình trên cloud:

```
 Người dùng
    │  1. DNS: api.example.com → IP public của load balancer
    ▼
 ┌─────────────────── VPC 10.0.0.0/16 ───────────────────────────┐
 │  Public subnet 10.0.1.0/24                                    │
 │   ┌──────────────────────┐                                    │
 │   │ L7 Load Balancer     │ 2. TLS termination, route /api     │
 │   └─────────┬────────────┘                                    │
 │             │ 3. firewall: chỉ LB được gọi app port 8080      │
 │  Private subnet 10.0.2.0/24                                   │
 │   ┌─────────▼──┐ ┌────────────┐                               │
 │   │ app #1     │ │ app #2     │ 4. health check /health       │
 │   └─────┬──────┘ └────────────┘                               │
 │         │ 5. firewall: chỉ subnet app được gọi port 5432      │
 │  DB subnet 10.0.3.0/24                                        │
 │   ┌─────▼──────┐                                              │
 │   │ PostgreSQL │       NAT gateway ◄── app gọi ra Internet    │
 │   └────────────┘                                              │
 └───────────────────────────────────────────────────────────────┘
```

Mỗi tầng có một lớp firewall chỉ mở cho tầng ngay trước nó. App và database không có IP public. Muốn ra Internet thì đi qua NAT.

## Ví dụ
Gỡ lỗi "app không kết nối được database" bằng cách kiểm tra từng tầng từ thấp lên cao:

```bash
dig +short db.internal.example.com   # 1. DNS có phân giải ra IP không? → 10.0.3.15
nc -zv 10.0.3.15 5432                # 2. Có mở được kết nối TCP tới port không?
#   "Connection timed out"  → gói bị chặn ở đâu đó (firewall, route): xem luật mạng
#   "Connection refused"    → tới được máy nhưng không có gì lắng nghe port: xem service
ss -tlnp | grep 5432                 # 3. (trên máy DB) Postgres có lắng nghe đúng địa chỉ không?
#   127.0.0.1:5432 → chỉ nhận kết nối local, phải đổi listen_addresses
```

Phân biệt **timeout** với **refused** giúp khoanh vùng nhanh: timeout thường do mạng hoặc firewall, refused do service.

## Câu hỏi

**CIDR `/24` nghĩa là gì, và một dải chứa được bao nhiêu máy?**
> - **CIDR**: cách viết dải IP `địa_chỉ/n`, trong đó `n` bit đầu là phần mạng.
> - **Host bits**: `32 − n` bit còn lại, dùng để đánh số máy trong dải.
>
> Một dải `/n` có 2^(32−n) địa chỉ, nhưng số máy dùng được luôn ít hơn vì một số địa chỉ bị giữ lại. `/24` có 256 địa chỉ. Mạng truyền thống mất 2 (network, broadcast) nên còn 254. AWS giữ 5 nên còn 251.
>
> Ranh giới: khi thiết kế VPC hay mạng cho Kubernetes, nên chừa dải rộng ngay từ đầu. Mỗi Pod cũng có thể tiêu một IP, nên dải hết rất nhanh, mà đổi CIDR khi hệ thống đã chạy thì rất khó.

**NAT dùng để làm gì, và vì sao máy trong private subnet ra được Internet mà Internet không vào được?**
> - **Private IP**: địa chỉ thuộc RFC 1918, không định tuyến được trên Internet.
> - **NAT**: thiết bị đổi IP/port trong gói tin và nhớ bảng ánh xạ.
>
> NAT ra ngoài chỉ có ánh xạ cho những kết nối do máy bên trong *mở trước*. Gói trả lời khớp với ánh xạ nên được chuyển ngược vào. Gói lạ từ ngoài vào không khớp ánh xạ nào nên bị bỏ. Vì vậy máy private tải được package nhưng không ai từ ngoài mở kết nối vào nó được.
>
> Ranh giới: muốn nhận traffic từ ngoài thì cần DNAT hoặc load balancer có IP public. NAT không phải firewall: nó chặn kết nối vào chỉ như một hệ quả, nên vẫn cần luật firewall rõ ràng.

**Load balancer L4 khác L7 thế nào, khi nào dùng loại nào?**
> - **L4**: tầng transport (TCP/UDP). Load balancer chỉ thấy IP và port.
> - **L7**: tầng application (HTTP). Load balancer đọc được nội dung request.
>
> Tiêu chí phân biệt là quyết định chia tải có cần nội dung request hay không. Cần route theo path/host, sửa header, TLS termination hay retry theo từng request thì phải dùng L7. Chỉ cần chia kết nối thật nhanh cho giao thức bất kỳ (database, gRPC đi xuyên qua, game UDP) thì L4 là đủ và rẻ hơn.
>
> Ranh giới: L4 chia theo *kết nối*. Với kết nối giữ lâu như HTTP/2 hay gRPC, nhiều request đi trên cùng một kết nối nên dồn vào một instance. Muốn chia đều từng request thì cần L7.

**Reverse proxy khác load balancer ở đâu?**
> - **Reverse proxy**: thành phần nhận request thay cho server và chuyển tiếp vào trong.
> - **Load balancer**: thành phần chia tải cho nhiều instance.
>
> Đây là hai *vai trò*, không phải hai loại phần mềm khác nhau: reverse proxy mô tả vị trí (đứng trước server, nói chuyện với client thay server), load balancer mô tả chức năng (chia tải). Một L7 load balancer luôn là một reverse proxy. Một reverse proxy như Nginx có thể chỉ chuyển tiếp tới một server (để làm TLS termination, cache) mà không chia tải gì.
>
> Ranh giới: API gateway cũng là reverse proxy, có thêm chức năng của tầng ứng dụng như xác thực, rate limit theo người dùng, gom nhiều API.

**Đổi IP của service xong mà người dùng vẫn vào IP cũ, vì sao?**
> - **DNS cache**: resolver và client giữ kết quả phân giải trong một khoảng thời gian.
> - **TTL**: thời gian tối đa được phép cache một record.
>
> Thay đổi DNS chỉ có hiệu lực với một client khi bản cache của nó hết hạn, tức tối đa bằng TTL cũ. Nếu record có TTL 1 ngày thì có thể phải chờ tới 1 ngày. Cách làm khi cần đổi: hạ TTL xuống thấp (vd 60 giây) trước khi đổi, ít nhất một khoảng bằng TTL cũ, đổi xong thì nâng TTL lên lại.
>
> Ranh giới: một số client, runtime hay thư viện tự cache DNS lâu hơn TTL. Vì vậy khi chuyển IP, giữ máy cũ chạy thêm một thời gian. Trỏ người dùng tới tên của load balancer (CNAME) thay vì IP cụ thể giúp tránh phải đổi DNS khi đổi máy.

## Hiểu nhầm thường gặp
- **"Private subnet là an toàn, không cần firewall."** Kẻ tấn công đã vào được một máy trong VPC thì đi ngang (lateral movement) sang các máy khác. Mỗi tầng vẫn cần luật riêng.
- **"Ping không được là máy chết."** Nhiều mạng chặn ICMP. Kiểm tra đúng port của service bằng `nc` hoặc `curl`.
- **"Load balancer tự làm app chịu lỗi."** Load balancer chỉ loại instance khi health check fail. Health check chỉ trả `200` mà không kiểm tra gì thì instance hỏng vẫn nhận traffic.

## Liên quan
- [../internet/05-ip-addressing.md](../internet/05-ip-addressing.md), [../internet/08-dns-and-dhcp.md](../internet/08-dns-and-dhcp.md), [../internet/10-network-security.md](../internet/10-network-security.md): giao thức nền.
- [05-kubernetes.md](05-kubernetes.md): Service và Ingress là load balancer và reverse proxy bên trong cluster.
- [06-cloud-fundamentals.md](06-cloud-fundamentals.md): VPC, subnet, security group trên cloud.
