# Terraform and Infrastructure as Code

> Infrastructure as Code (IaC) là quản lý hạ tầng (mạng, máy, database, DNS, quyền truy cập) bằng file văn bản có version, thay vì bấm tay trên giao diện web. Terraform là công cụ IaC phổ biến nhất để *tạo* tài nguyên. Ansible là công cụ phổ biến để *cấu hình* bên trong máy.

## Tại sao cần biết
Hạ tầng dựng bằng tay thì không ai nhớ chính xác đã bấm những gì. Dựng lại môi trường thứ hai (staging giống production) mất vài ngày và thế nào cũng lệch. Một thay đổi sai không có ai review và không có lịch sử để quay lại. IaC đưa hạ tầng vào cùng quy trình với code: viết trong Git, review qua pull request, chạy qua pipeline ([08-ci-cd.md](08-ci-cd.md)), và tạo lại được bất cứ lúc nào. Đây là phần Automation của CALMS ([01-devops-culture.md](01-devops-culture.md)) áp vào hạ tầng.

## Khái niệm cốt lõi

### Infrastructure as Code
- **Là gì:** mô tả hạ tầng bằng file (HCL, YAML, hoặc ngôn ngữ lập trình), rồi để công cụ tạo và cập nhật hạ tầng thật theo file đó.
- **Dùng để:** lặp lại được (cùng code ra cùng hạ tầng), review được, có lịch sử và rollback qua Git, tài liệu hoá chính xác ("hạ tầng là những gì code nói"), tạo môi trường mới nhanh.

### Declarative và imperative
- **Imperative** — **Là gì:** viết *các bước* để đi tới kết quả ("tạo VM, rồi gắn disk, rồi mở port"). **Dùng để:** kiểm soát chi tiết thứ tự, hợp với việc một lần. Script bash gọi CLI là imperative.
- **Declarative** — **Là gì:** viết *kết quả mong muốn* ("cần 1 VM loại t3.small có disk 20 GB"), công cụ tự tính cần làm gì từ trạng thái hiện tại. **Dùng để:** chạy lại bao nhiêu lần cũng được, công cụ chỉ làm phần còn thiếu. Terraform và Kubernetes đều declarative.

### Idempotency
- **Là gì:** tính chất một thao tác chạy một lần hay nhiều lần đều cho cùng kết quả.
- **Dùng để:** chạy lại an toàn sau khi lỗi giữa chừng, và chạy định kỳ để kéo hạ tầng về đúng khai báo. Script "tạo VM" chạy hai lần ra hai VM, không idempotent. `terraform apply` chạy hai lần thì lần hai không làm gì, idempotent.

### Provisioning và configuration management
| | **Provisioning** | **Configuration management** |
|---|---|---|
| Là gì | Tạo, sửa, xoá tài nguyên hạ tầng qua API (VPC, VM, database, DNS, IAM) | Cấu hình *bên trong* máy đã có (cài package, sửa file config, quản lý service, user) |
| Công cụ tiêu biểu | Terraform / OpenTofu, CloudFormation, Pulumi | Ansible, Chef, Puppet, Salt |
| Nói chuyện với | API của cloud hay của dịch vụ | OS của máy (qua SSH hoặc agent) |

### Mutable và immutable infrastructure
- **Mutable** — **Là gì:** giữ nguyên máy và sửa dần bên trong (cập nhật package, đổi config). **Dùng để:** đỡ tạo máy mới. Cái giá phải trả là máy dần lệch nhau (configuration drift), mỗi máy thành một "bông tuyết" không ai tái tạo được.
- **Immutable** — **Là gì:** không bao giờ sửa máy đang chạy. Muốn đổi thì build image mới (VM image bằng Packer, hoặc container image) rồi thay máy cũ bằng máy mới. **Dùng để:** mọi máy giống hệt image của nó, rollback bằng cách quay về image cũ. Container và Kubernetes đẩy hướng này thành mặc định.
- Câu nói hay dùng: đối xử với server như **cattle, not pets** (gia súc, không phải thú cưng). Một con hỏng thì thay, không chăm chữa từng con.

### Thành phần của Terraform
| Thành phần | Là gì | Dùng để |
|---|---|---|
| **Provider** | Plugin nói chuyện với API của một nền tảng (AWS, GCP, Kubernetes, Cloudflare, GitHub...) | Cho Terraform quản lý mọi thứ có API, không riêng cloud |
| **Resource** | Khối khai báo một đối tượng Terraform tạo và quản lý (`aws_instance`, `aws_s3_bucket`) | Mô tả hạ tầng mong muốn |
| **Data source** | Khối *đọc* thông tin của thứ đã có mà Terraform không quản lý | Lấy ID của AMI, VPC có sẵn để dùng |
| **Variable / output** | Tham số đầu vào / giá trị xuất ra | Tái sử dụng code giữa môi trường, truyền giá trị giữa các phần |
| **Module** | Thư mục chứa nhóm resource, gọi được như một hàm | Đóng gói mẫu hạ tầng dùng lại (vd module "service chuẩn": ALB + ASG + IAM) |
| **State** | File JSON ghi ánh xạ giữa resource trong code và đối tượng thật (vd `aws_instance.web` ↔ `i-0abc123`), cùng thuộc tính của chúng | Biết cái gì đã tồn tại, để tính chênh lệch |
| **Backend** | Nơi lưu state (file local, S3, Terraform Cloud...) | Cả đội dùng chung một state, có khoá (locking) để hai người không apply cùng lúc |

### Vòng đời lệnh của Terraform
| Lệnh | Việc làm |
|---|---|
| `terraform init` | Tải provider, module, cấu hình backend |
| `terraform plan` | Đọc code + state + trạng thái thật, in ra những gì *sẽ* tạo (`+`), sửa (`~`), xoá (`-`), thay (`-/+`). Không đổi gì |
| `terraform apply` | Thực hiện plan, cập nhật state |
| `terraform destroy` | Xoá mọi resource trong state |
| `terraform import` / khối `import` | Đưa một tài nguyên tạo tay sẵn vào state để Terraform quản lý |

### Drift
- **Là gì:** chênh lệch giữa hạ tầng thật và khai báo trong code, thường do ai đó sửa tay trên console.
- **Dùng để (phát hiện):** `terraform plan` sẽ hiện drift như một thay đổi cần làm để kéo về đúng code. Nhiều đội chạy `plan` định kỳ để phát hiện drift sớm.

### Ansible
- **Là gì:** công cụ configuration management **agentless**: máy đích không cần cài agent, Ansible kết nối qua SSH (hoặc WinRM với Windows) rồi chạy các module.
- **Inventory**: danh sách máy và nhóm máy. **Playbook**: file YAML liệt kê các **play** (nhóm máy nào, chạy những **task** nào). **Module**: đơn vị công việc idempotent (`apt`, `copy`, `template`, `service`). **Role**: gói task, template, biến để dùng lại.
- **Dùng để:** cấu hình hàng loạt máy giống nhau, vá OS, triển khai ứng dụng lên VM, chạy việc vận hành lặp lại.

## Cách hoạt động
Terraform tính thay đổi bằng cách so ba thứ:

```
   Code (.tf)              State (terraform.tfstate)          Hạ tầng thật (API)
 "muốn có gì"         "lần trước đã tạo gì, ID là gì"        "hiện đang có gì"
       │                          │                                  │
       └──────────────┬───────────┴───────────── refresh ────────────┘
                      ▼
               terraform plan  ── chênh lệch ──►  + tạo   ~ sửa tại chỗ
                      │                           - xoá   -/+ xoá rồi tạo lại
                      ▼
               terraform apply ── gọi API theo thứ tự phụ thuộc ──► cập nhật state
```

- Terraform tự dựng **đồ thị phụ thuộc** từ tham chiếu trong code: subnet tham chiếu `aws_vpc.main.id` thì VPC phải được tạo trước. Những resource không phụ thuộc nhau được tạo song song.
- Có thuộc tính đổi được tại chỗ (`~`, vd đổi tag). Có thuộc tính buộc phải xoá rồi tạo lại (`-/+`, vd đổi AZ của subnet). Đọc kỹ `plan` là bước an toàn quan trọng nhất, vì `-/+` trên một database nghĩa là mất dữ liệu.

## Ví dụ
Code Terraform tạo một bucket S3 có bật versioning:

```hcl
terraform {
  backend "s3" {                       # state lưu chung trên S3, có khoá
    bucket       = "acme-tf-state"
    key          = "prod/storage.tfstate"
    region       = "ap-southeast-1"
    use_lockfile = true
  }
}

provider "aws" {
  region = "ap-southeast-1"
}

variable "env" {
  type    = string
  default = "prod"
}

resource "aws_s3_bucket" "uploads" {
  bucket = "acme-uploads-${var.env}"
  tags   = { team = "payments", env = var.env }
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id    # tham chiếu → tạo sau bucket
  versioning_configuration { status = "Enabled" }
}

output "bucket_arn" {
  value = aws_s3_bucket.uploads.arn
}
```

Lần đầu `plan` báo `2 to add`. Chạy `apply` lần hai báo `No changes`: đó là idempotency. Nếu có người tắt versioning trên console, lần `plan` sau báo `1 to change`: đó là drift.

Playbook Ansible tương ứng ở tầng bên trong máy:

```yaml
- hosts: web
  become: true                 # dùng sudo
  tasks:
    - name: Nginx được cài
      ansible.builtin.apt: { name: nginx, state: present }
    - name: Nginx đang chạy và bật khi boot
      ansible.builtin.service: { name: nginx, state: started, enabled: true }
```

Mỗi task mô tả *trạng thái* (`present`, `started`), không mô tả lệnh. Chạy lại thì task đã đúng báo `ok`, chỉ task phải làm gì đó mới báo `changed`.

## Câu hỏi

**IaC giải quyết vấn đề gì so với dựng hạ tầng bằng tay?**
> - **Infrastructure as Code**: mô tả hạ tầng bằng file có version, để công cụ tạo theo file đó.
> - **ClickOps**: cách gọi vui việc dựng hạ tầng bằng cách bấm trên console.
>
> IaC biến hạ tầng thành thứ *lặp lại được, review được và có lịch sử*, như code ứng dụng. Từ đó có các hệ quả: dựng môi trường mới bằng cách chạy lại code, mọi thay đổi đi qua pull request, sự cố thì xem Git log để biết ai đổi gì, khôi phục thảm hoạ bằng cách apply lại ở region khác.
>
> Ranh giới: IaC chỉ hiệu quả khi *mọi* thay đổi đi qua code. Còn sửa tay song song thì code và thực tế lệch nhau (drift), và lần apply sau có thể ghi đè chính bản sửa khẩn cấp đó.

**Declarative khác imperative thế nào?**
> - **Imperative**: viết các bước cần làm.
> - **Declarative**: viết trạng thái đích, công cụ tự suy ra các bước.
>
> Tiêu chí phân biệt là ai giữ logic "từ đây đến đó": imperative thì người viết phải xử lý mọi trạng thái xuất phát (đã có chưa, có nửa chừng không), declarative thì công cụ so trạng thái thật với đích rồi chỉ làm phần chênh. Vì vậy declarative idempotent một cách tự nhiên và chạy lại an toàn. Imperative muốn idempotent thì phải tự viết kiểm tra.
>
> Ranh giới: declarative không biểu đạt tốt những việc vốn là chuỗi bước một lần như migration dữ liệu, rotate khoá theo thứ tự. Những việc đó vẫn cần script hoặc job imperative, chạy bên cạnh IaC.

**Terraform state dùng để làm gì, vì sao không commit vào Git?**
> - **State**: file ánh xạ resource trong code với đối tượng thật, kèm thuộc tính và phụ thuộc.
> - **Backend / locking**: nơi lưu state dùng chung, có khoá chống apply đồng thời.
>
> State là trí nhớ của Terraform: nhờ nó mới biết `aws_instance.web` là máy `i-0abc123` nào, cái gì cần xoá khi bạn xoá một khối code (code không còn khối đó, chỉ state còn nhớ), và theo thứ tự nào. Không commit vào Git vì ba lý do: state có thể chứa bí mật ở dạng rõ (mật khẩu database, key), Git không có khoá nên hai người apply cùng lúc sẽ ghi đè state của nhau, và người làm dễ apply với state cũ. Dùng remote backend có mã hoá và locking.
>
> Ranh giới: mất state không làm mất hạ tầng, nhưng Terraform sẽ "quên" mọi thứ và định tạo lại từ đầu. Khi đó phải `import` từng tài nguyên. Vì vậy backend của state cần versioning và backup.

**Drift là gì, xử lý thế nào?**
> - **Drift**: hạ tầng thật khác với code do có thay đổi đi ngoài IaC.
>
> Code là nguồn sự thật (source of truth). Drift được giải theo một trong hai hướng: thay đổi tay là sai thì `apply` để kéo thực tế về code; thay đổi tay là đúng (vd sửa khẩn cấp lúc có sự cố) thì cập nhật code cho khớp rồi `plan` phải sạch. Cách phòng là hạn chế quyền sửa tay trên production và chạy `plan` định kỳ để phát hiện.
>
> Ranh giới: có thuộc tính được thay đổi hợp lệ bởi hệ thống khác (vd số máy do autoscaling đổi). Khai báo bỏ qua thuộc tính đó (`ignore_changes`) để Terraform không giành quyền với autoscaler.

**Terraform khác Ansible ở đâu, có dùng chung được không?**
> - **Terraform**: công cụ provisioning, declarative, có state, gọi API.
> - **Ansible**: công cụ configuration management, dạng task idempotent, không có state, chạy qua SSH.
>
> Tiêu chí là đối tượng quản lý: Terraform quản lý *sự tồn tại* của tài nguyên (VPC, VM, DNS), Ansible quản lý *trạng thái bên trong* máy (package, file, service). Hai thứ hay dùng chung: Terraform tạo VM, Ansible cấu hình VM đó. Với hướng immutable thì bước "cấu hình" dời sang lúc build image (Dockerfile, Packer), và vai trò của Ansible trên server thu hẹp lại.
>
> Ranh giới: Ansible cũng có module gọi API cloud, Terraform cũng chạy được script lúc tạo máy (provisioner). Dùng được nhưng là dùng lệch thế mạnh. Ansible không có state nên không biết xoá thứ đã bỏ khỏi playbook.

**Đổi tên một resource trong code thì chuyện gì xảy ra?**
> - **Resource address**: định danh của resource trong state, vd `aws_s3_bucket.uploads`.
>
> Terraform nhận diện resource theo *địa chỉ trong code*, không theo tên tài nguyên thật. Đổi `aws_s3_bucket.uploads` thành `aws_s3_bucket.files` bị hiểu là xoá cái cũ và tạo cái mới. Với bucket hay database, điều đó có thể mất dữ liệu. Khai báo khối `moved { from = ..., to = ... }` (hoặc chạy `terraform state mv`) để báo đây chỉ là đổi địa chỉ, tài nguyên thật giữ nguyên.
>
> Ranh giới: chuyển resource vào trong một module cũng làm đổi địa chỉ (`module.storage.aws_s3_bucket.uploads`), nên cũng cần `moved`. Luôn đọc `plan` trước khi apply một lần refactor.

## Hiểu nhầm thường gặp
- **"`terraform plan` sạch nghĩa là hạ tầng đúng."** Plan chỉ so với những gì Terraform quản lý. Tài nguyên tạo tay ngoài Terraform hoàn toàn vô hình với nó.
- **"Terraform chỉ dành cho cloud."** Provider tồn tại cho bất cứ thứ gì có API: DNS, GitHub, Kubernetes, monitoring.
- **"Ansible là declarative giống Terraform."** Từng module là idempotent và mô tả trạng thái, nhưng playbook chạy tuần tự từ trên xuống và không có state. Xoá một task không làm Ansible gỡ thứ task đó đã cài.
- **"IaC là viết script tự động."** Script tự động là imperative và thường không idempotent. IaC đúng nghĩa là khai báo, có version và có review.

## Liên quan
- [06-cloud-fundamentals.md](06-cloud-fundamentals.md): những tài nguyên Terraform tạo ra.
- [08-ci-cd.md](08-ci-cd.md): chạy `plan` khi mở PR, `apply` khi merge.
- [05-kubernetes.md](05-kubernetes.md): Kubernetes cũng là hệ thống declarative có reconciliation loop.
- [13-devsecops.md](13-devsecops.md): quét IaC tìm cấu hình sai, quản lý secret trong state.
