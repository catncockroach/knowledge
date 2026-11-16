# Cloud fundamentals

> Cloud computing là thuê tài nguyên máy tính (máy chủ, lưu trữ, mạng, database...) qua API, dùng bao nhiêu trả bấy nhiêu, thay vì tự mua và vận hành phần cứng. File này giải thích các khái niệm chung của mọi nhà cung cấp cloud, kèm tên dịch vụ AWS tương ứng để dễ hình dung.

## Tại sao cần biết
Hầu hết hạ tầng mới được dựng trên cloud. Terraform ([07-terraform-and-iac.md](07-terraform-and-iac.md)) tạo tài nguyên cloud, Kubernetes managed (EKS, GKE) chạy trên VM cloud, pipeline CI/CD đẩy artifact lên registry của cloud. Các cloud đặt tên dịch vụ khác nhau nhưng cùng chung một bộ khối xây dựng: compute, storage, network, identity. Hiểu khối xây dựng thì chuyển từ cloud này sang cloud khác chỉ là học tên mới.

## Khái niệm cốt lõi

### Cloud là gì
Theo định nghĩa của NIST (SP 800-145), cloud có năm đặc điểm:
1. **On-demand self-service**: tự tạo tài nguyên khi cần, không phải chờ ai duyệt hay lắp máy.
2. **Broad network access**: truy cập qua mạng bằng giao thức chuẩn.
3. **Resource pooling**: tài nguyên vật lý được dùng chung cho nhiều khách hàng (multi-tenant).
4. **Rapid elasticity**: tăng giảm nhanh theo nhu cầu.
5. **Measured service**: đo và tính tiền theo mức dùng.

### Mô hình dịch vụ
| Mô hình | Bạn quản lý | Nhà cung cấp quản lý | Ví dụ AWS |
|---|---|---|---|
| **On-premises** | Tất cả, kể cả phần cứng và toà nhà | Không có | (tự có data center) |
| **IaaS** | OS, runtime, app, data | Phần cứng, ảo hoá, mạng vật lý | EC2 (máy ảo) |
| **PaaS** | App, data | Thêm OS, runtime, scaling | Elastic Beanstalk, RDS (database managed) |
| **SaaS** | Chỉ dữ liệu và cách dùng | Toàn bộ ứng dụng | Gmail, Slack (dùng ngay) |
| **Serverless / FaaS** | Chỉ code của hàm | Mọi thứ còn lại, kể cả chuyện có bao nhiêu máy | Lambda |

- **Dùng để:** chọn mức trừu tượng. Càng đi xuống bảng thì càng ít việc vận hành và càng ít quyền kiểm soát.
- **Managed service** — **Là gì:** dịch vụ mà nhà cung cấp vận hành hộ phần nền (cài đặt, vá, backup, failover), vd database managed, Kubernetes managed (EKS). **Dùng để:** giảm việc vận hành lặp lại để đội tập trung vào sản phẩm.

### Region, Availability Zone, edge
- **Region** — **Là gì:** một khu vực địa lý độc lập của cloud (vd `ap-southeast-1` ở Singapore), gồm nhiều AZ. **Dùng để:** đặt hệ thống gần người dùng (giảm latency), đáp ứng yêu cầu dữ liệu phải lưu trong một quốc gia, và chịu được sự cố cấp vùng khi chạy nhiều region.
- **Availability Zone (AZ)** — **Là gì:** một hoặc nhiều data center trong một region, có nguồn điện, làm mát và mạng riêng, cách nhau đủ xa để không cùng hỏng, nối với nhau bằng mạng latency thấp. **Dùng để:** chạy bản sao ở nhiều AZ để một data center mất điện thì hệ thống vẫn chạy ([12-high-availability-and-dr.md](12-high-availability-and-dr.md)).
- **Edge location** — **Là gì:** điểm hiện diện nhỏ đặt gần người dùng, chạy CDN và DNS (CloudFront, Route 53). **Dùng để:** cache nội dung tĩnh, giảm latency.

### Shared responsibility model
- **Là gì:** mô hình chia trách nhiệm bảo mật. Nhà cung cấp lo **security *of* the cloud** (phần cứng, data center, mạng vật lý, lớp ảo hoá). Khách hàng lo **security *in* the cloud** (cấu hình, dữ liệu, quyền truy cập, và mọi thứ chạy trên tài nguyên mình thuê).
- **Dùng để:** biết lỗ hổng nào là việc của mình. Ranh giới dịch chuyển theo mô hình dịch vụ: với EC2 thì khách hàng vá guest OS và cấu hình firewall; với S3 hay DynamoDB thì AWS lo OS và nền, khách hàng vẫn lo dữ liệu, mã hoá và quyền IAM.

### Compute
- **VM** (EC2) — **Là gì:** máy ảo thuê theo giờ hoặc giây, chọn loại (instance type) theo CPU và RAM. **Dùng để:** chạy bất cứ thứ gì, kiểm soát được tới OS.
- **Container service** (ECS, EKS, Fargate) — **Là gì:** dịch vụ chạy container, có hoặc không cần tự quản node. **Dùng để:** chạy image mà không lo dựng cluster từ đầu.
- **Function** (Lambda) — **Là gì:** chạy một đoạn code khi có sự kiện, tính tiền theo lần gọi và thời gian chạy. **Dùng để:** việc ngắn, chạy theo sự kiện, tải thất thường.
- **Autoscaling group** — **Là gì:** nhóm VM tự tăng giảm số máy theo metric. **Dùng để:** co giãn theo tải và tự thay máy hỏng.

### Storage
| Loại | Là gì | Dùng để | AWS |
|---|---|---|---|
| **Block** | Disk ảo gắn vào một VM, OS thấy như một ổ cứng | Disk hệ điều hành, database tự quản | EBS |
| **File** | File system chia sẻ qua mạng (NFS), nhiều máy cùng mount | Thư mục dùng chung giữa nhiều server | EFS |
| **Object** | Kho lưu object (file + metadata) theo key, truy cập qua HTTP API, gần như không giới hạn dung lượng | Backup, log, file tĩnh, data lake, artifact | S3 |

### Network
- **VPC (Virtual Private Cloud)** — **Là gì:** mạng riêng ảo của bạn trong cloud, có dải CIDR riêng ([03-networking-for-ops.md](03-networking-for-ops.md)). **Dùng để:** cô lập tài nguyên của mình khỏi khách hàng khác và tự thiết kế subnet, route, firewall.
- **Subnet** — **Là gì:** dải con của VPC, nằm trong *một* AZ.
  - **Public subnet**: route table có đường ra **Internet Gateway**. Máy có IP public thì Internet vào được.
  - **Private subnet**: không có đường ra Internet Gateway. Muốn gọi ra ngoài thì đi qua **NAT Gateway** đặt ở public subnet.
- **Route table** — **Là gì:** bảng quyết định gói tin đi từ subnet tới đích nào qua đâu.
- **Security group** — **Là gì:** firewall **stateful** gắn vào từng network interface (từng instance), chỉ có luật *cho phép*. **Network ACL** — **Là gì:** firewall **stateless** gắn vào subnet, có cả luật cho phép lẫn chặn, xét theo thứ tự. **Dùng để:** security group kiểm soát chi tiết từng máy, NACL làm lớp chặn thô ở biên subnet.
- **Load balancer managed** (ALB, NLB): load balancer L7/L4 do cloud vận hành.

### IAM (Identity and Access Management)
- **Là gì:** hệ thống quản lý *ai* (principal) được làm *gì* (action) trên *tài nguyên nào* (resource) trong cloud.
- **Dùng để:** kiểm soát mọi lời gọi API tới cloud. Mọi thao tác (tạo VM, đọc S3) đều là một lời gọi API được IAM xét.
- **User** — **Là gì:** danh tính lâu dài của một người hoặc ứng dụng, có credential dài hạn (mật khẩu, access key).
- **Role** — **Là gì:** danh tính không có credential cố định. Ai được phép thì *assume* role và nhận credential tạm thời, tự hết hạn. **Dùng để:** cấp quyền cho máy, service, pipeline CI, hoặc người từ tài khoản khác mà không phải phát khoá dài hạn.
- **Policy** — **Là gì:** tài liệu JSON liệt kê `Effect` (Allow/Deny), `Action`, `Resource`, `Condition`. Mặc định là từ chối hết. Một `Deny` tường minh luôn thắng mọi `Allow`.

### Chi phí
- **Pay-as-you-go**: trả theo mức dùng (giờ VM, GB lưu trữ, số request, GB truyền ra Internet).
- **Hình thức mua**: on-demand (giá chuẩn, không cam kết), reserved / savings plan (cam kết 1–3 năm để được giảm giá), spot (dùng công suất thừa với giá rẻ, có thể bị thu hồi bất cứ lúc nào).
- Chi phí hay bị bỏ quên: **data transfer ra ngoài** (egress) và giữa các AZ hay region, tài nguyên tạo xong quên xoá, NAT Gateway, log lưu không có hạn.
- **Tag** — **Là gì:** nhãn key-value gắn lên tài nguyên (`team=payments`, `env=prod`). **Dùng để:** phân bổ chi phí theo đội hoặc dự án, và tìm tài nguyên mồ côi.

## Cách hoạt động
Một kiến trúc web cơ bản chịu được mất một AZ:

```
                         Region ap-southeast-1
 ┌──────────────────────────────────────────────────────────────────┐
 │ VPC 10.0.0.0/16                         Internet Gateway          │
 │                                                │                  │
 │      AZ a                                      │         AZ b     │
 │ ┌─────────────────────┐   ┌────────────────────┴┐                 │
 │ │ public  10.0.1.0/24 │   │ public  10.0.2.0/24 │ ◄── ALB trải 2 AZ│
 │ │   NAT GW            │   │   NAT GW            │                 │
 │ ├─────────────────────┤   ├─────────────────────┤                 │
 │ │ private 10.0.11.0/24│   │ private 10.0.12.0/24│ ◄── Autoscaling  │
 │ │   app EC2 ×2        │   │   app EC2 ×2        │     group 2 AZ   │
 │ ├─────────────────────┤   ├─────────────────────┤                 │
 │ │ db      10.0.21.0/24│   │ db      10.0.22.0/24│                 │
 │ │   RDS primary ──────┼───┼──► RDS standby      │ ◄── Multi-AZ     │
 │ └─────────────────────┘   └─────────────────────┘                 │
 └──────────────────────────────────────────────────────────────────┘
   S3 (object storage) và IAM là dịch vụ cấp region/toàn cầu, không nằm trong subnet
```

Mỗi tầng có bản sao ở cả hai AZ. AZ a mất thì ALB chỉ gửi traffic sang AZ b, autoscaling group tạo thêm máy ở AZ b, và RDS chuyển standby lên làm primary.

## Ví dụ
Policy IAM cho một service chỉ được đọc và ghi đúng một prefix trong một bucket S3:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::acme-uploads/invoices/*"
    }
  ]
}
```

Gắn policy này vào một **role**, rồi cho EC2 hoặc Pod assume role đó. Service nhận credential tạm thời tự xoay vòng, không có access key nào nằm trong code hay biến môi trường. Gọi `s3:DeleteObject`, hoặc đọc prefix khác, đều bị từ chối vì mặc định là deny.

`"Version": "2012-10-17"` là phiên bản của ngôn ngữ policy, không phải ngày tạo policy.

## Câu hỏi

**IaaS, PaaS và SaaS khác nhau ở đâu?**
> - **IaaS**: thuê hạ tầng (VM, disk, mạng), tự lo từ OS trở lên.
> - **PaaS**: thuê nền tảng chạy app, chỉ lo code và dữ liệu.
> - **SaaS**: dùng phần mềm hoàn chỉnh qua mạng.
>
> Tiêu chí phân biệt là ranh giới "ai quản lý tầng nào" trong chồng phần cứng → ảo hoá → OS → runtime → app → data. Mỗi bậc từ IaaS lên SaaS giao thêm vài tầng cho nhà cung cấp. Đổi lại bạn bớt việc vận hành nhưng cũng bớt quyền kiểm soát và khả năng tuỳ biến.
>
> Ranh giới: nhiều dịch vụ không nằm gọn trong một ô. Kubernetes managed nằm giữa IaaS và PaaS, serverless thì gần PaaS hơn. Dù ở mô hình nào thì dữ liệu và quyền truy cập luôn là trách nhiệm của khách hàng.

**Region và Availability Zone khác nhau thế nào? Một hệ thống nên chạy bao nhiêu AZ?**
> - **Region**: khu vực địa lý độc lập, gồm nhiều AZ.
> - **AZ**: một hoặc nhiều data center tách biệt về điện và mạng, trong cùng một region.
>
> AZ là đơn vị chịu lỗi cho sự cố *cục bộ* (một data center mất điện), region là đơn vị chịu lỗi cho sự cố *cả vùng* và là đơn vị để đặt gần người dùng hay tuân thủ luật dữ liệu. Muốn chịu được mất một AZ thì mọi tầng (load balancer, app, database) phải có bản sao ở ít nhất hai AZ. Nhiều region chỉ cần khi yêu cầu sẵn sàng hoặc DR đòi hỏi, vì chi phí và độ phức tạp tăng mạnh (dữ liệu phải sao chép xa).
>
> Ranh giới: subnet nằm trong một AZ, còn VPC trải nhiều AZ của một region. Truyền dữ liệu giữa các AZ thường tốn phí, nên hệ thống chạy nhiều AZ phải tính thêm chi phí này.

**Theo shared responsibility, phần nào cloud lo, phần nào mình lo?**
> - **Security of the cloud**: phần cứng, data center, mạng vật lý, hypervisor. Phần này nhà cung cấp lo.
> - **Security in the cloud**: những gì bạn cấu hình và đưa lên. Phần này khách hàng lo.
>
> Bạn luôn chịu trách nhiệm về những gì mình *cấu hình*: dữ liệu, quyền IAM, firewall, mã hoá. Còn những tầng nằm dưới ranh giới của dịch vụ thì nhà cung cấp lo. Với VM bạn vá OS. Với database managed thì nhà cung cấp vá, bạn lo user, quyền và mạng. Với S3 thì bạn lo bucket có bị mở public hay không.
>
> Ranh giới: phần lớn sự cố bảo mật trên cloud đến từ cấu hình sai phía khách hàng (bucket public, key bị lộ, security group mở `0.0.0.0/0`), không phải từ lỗi của nhà cung cấp.

**Public subnet khác private subnet ở đâu?**
> - **Subnet**: dải IP con của VPC, nằm trong một AZ.
> - **Internet Gateway**: cổng nối VPC với Internet theo cả hai chiều.
> - **NAT Gateway**: cổng chỉ cho máy private gọi ra ngoài.
>
> Subnet "public" hay "private" được quyết định bởi **route table**, không phải bởi tên hay một cờ nào: có route `0.0.0.0/0` trỏ tới Internet Gateway là public, không có là private. Thứ cần nhận kết nối từ Internet (load balancer, bastion) đặt ở public. App và database đặt ở private, gọi ra ngoài qua NAT.
>
> Ranh giới: máy nằm trong public subnet mà không có IP public thì vẫn không ai từ Internet vào được. Ngược lại, máy có IP public vẫn bị security group chặn nếu luật không cho phép.

**Block, file và object storage khác nhau thế nào?**
> - **Block**: disk ảo, OS tự định dạng và quản lý file system.
> - **File**: file system chia sẻ qua mạng.
> - **Object**: kho lưu theo key qua HTTP API, không có file system.
>
> Tiêu chí là cách truy cập và ai được truy cập. Block cho một máy đọc ghi ngẫu nhiên từng khối, nhanh, hợp với database. File cho nhiều máy cùng mount và cùng sửa file. Object cho mọi nơi đọc ghi *nguyên object* qua HTTP, rẻ, bền, dung lượng gần như vô hạn, hợp với backup, log, ảnh và artifact.
>
> Ranh giới: object storage không sửa được một phần object như sửa file, muốn sửa là ghi lại cả object. Vì vậy không chạy database trực tiếp trên S3, kể cả khi có công cụ mount S3 như một thư mục.

**IAM user khác IAM role thế nào?**
> - **Principal**: thực thể gọi API (người, service).
> - **User**: danh tính lâu dài có credential dài hạn.
> - **Role**: danh tính được assume, cấp credential tạm thời.
>
> Khác biệt chính là vòng đời của credential: credential của user tồn tại tới khi bị thu hồi, credential của role hết hạn tự động. Máy, service và pipeline nên dùng role, để không có khoá dài hạn nào nằm trong code, image hay biến CI có thể bị lộ. Người dùng thường đăng nhập qua SSO rồi assume role, thay vì mỗi người một IAM user.
>
> Ranh giới: role chỉ an toàn khi trust policy (ai được assume) cũng chặt. Một role mà ai cũng assume được thì credential tạm thời cũng vô nghĩa.

## Hiểu nhầm thường gặp
- **"Lên cloud là tự động sẵn sàng cao."** Một VM ở một AZ vẫn chết khi AZ đó có sự cố. Sẵn sàng cao phải tự thiết kế: nhiều AZ, có load balancer, database có bản sao.
- **"Cloud luôn rẻ hơn."** Cloud rẻ khi tải thay đổi và khi tắt được thứ không dùng. Tải ổn định chạy 24/7 mà không tối ưu (reserved, đúng kích thước) có thể đắt hơn tự vận hành.
- **"Security group giống firewall truyền thống, cần luật cho cả chiều về."** Security group là stateful: cho phép chiều vào thì gói trả lời tự được đi ra.
- **"Xoá VM là hết tốn tiền."** Disk, snapshot, IP public, load balancer, NAT Gateway vẫn tính tiền nếu còn tồn tại.

## Liên quan
- [03-networking-for-ops.md](03-networking-for-ops.md): CIDR, NAT, firewall, load balancer, nền của VPC.
- [07-terraform-and-iac.md](07-terraform-and-iac.md): tạo tài nguyên cloud bằng code.
- [12-high-availability-and-dr.md](12-high-availability-and-dr.md): thiết kế nhiều AZ, nhiều region.
- [../enterprise-security/04-identity-and-access.md](../enterprise-security/04-identity-and-access.md): IAM và kiểm soát truy cập ở góc bảo mật.
