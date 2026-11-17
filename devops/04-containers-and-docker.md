# Containers and Docker

> Container là một process (hoặc nhóm process) chạy trên kernel của máy host nhưng bị cô lập về tầm nhìn và giới hạn về tài nguyên, kèm theo toàn bộ file system nó cần. Docker là bộ công cụ phổ biến nhất để build image và chạy container. Nhờ container, "chạy được trên máy tôi" trở thành "chạy được ở mọi nơi".

## Tại sao cần biết
Trước container, deploy một app nghĩa là cài đúng phiên bản runtime, thư viện và config lên từng server. Mỗi server lệch nhau một chút, và lỗi "máy dev chạy được, production không chạy" là chuyện thường ngày. Máy ảo (VM) giải quyết bằng cách đóng gói cả hệ điều hành, nhưng mỗi VM nặng hàng GB và mất hàng chục giây mới khởi động. Container đóng gói đúng phần ứng dụng cần, khởi động trong khoảng một giây, và là đơn vị deploy của Kubernetes ([05-kubernetes.md](05-kubernetes.md)) cũng như của hầu hết pipeline CI/CD ([08-ci-cd.md](08-ci-cd.md)).

## Khái niệm cốt lõi

### Máy ảo (VM) và hypervisor
- **Hypervisor** — **Là gì:** phần mềm tạo và chạy máy ảo, giả lập phần cứng cho từng VM (KVM, Hyper-V, VMware ESXi). **Dùng để:** chia một máy vật lý thành nhiều máy độc lập, mỗi máy có kernel riêng.
- **VM** — **Là gì:** một máy tính giả lập có CPU, RAM, disk ảo và một hệ điều hành khách (guest OS) đầy đủ. **Dùng để:** cô lập mạnh ở mức kernel, chạy được hệ điều hành khác với host (Windows trên host Linux).

### Container
- **Là gì:** process thường của Linux, được kernel đặt vào các **namespace** riêng (nên chỉ thấy phần hệ thống của mình) và các **cgroup** riêng (nên chỉ dùng được phần tài nguyên được cấp). File system của container là một image. Container không có kernel riêng mà dùng chung kernel của host.
- **Dùng để:** đóng gói ứng dụng cùng mọi thứ nó phụ thuộc, chạy nhất quán ở mọi máy có container runtime, mật độ cao (nhiều container trên một máy), khởi động nhanh.

```
        Máy ảo                                  Container
 ┌──────┐ ┌──────┐ ┌──────┐            ┌──────┐ ┌──────┐ ┌──────┐
 │ App  │ │ App  │ │ App  │            │ App  │ │ App  │ │ App  │
 │ Libs │ │ Libs │ │ Libs │            │ Libs │ │ Libs │ │ Libs │
 │GuestOS│ │GuestOS│ │GuestOS│           └──┬───┘ └──┬───┘ └──┬───┘
 └──┬───┘ └──┬───┘ └──┬───┘               └───────┼────────┘
 ┌──┴────────┴────────┴──┐              ┌──────────┴──────────┐
 │      Hypervisor       │              │ Container runtime   │
 ├───────────────────────┤              ├─────────────────────┤
 │   Host OS / phần cứng │              │ Host OS (1 kernel)  │
 └───────────────────────┘              └─────────────────────┘
```

### Namespace
- **Là gì:** tính năng của Linux kernel cho một nhóm process một "góc nhìn" riêng về một loại tài nguyên hệ thống.
- **Dùng để:** làm process trong container tưởng như nó đang chạy một mình trên một máy.

| Namespace | Cô lập |
|---|---|
| PID | Số hiệu process: process đầu tiên trong container thấy mình là PID 1 |
| Network | Card mạng, IP, bảng định tuyến, port: mỗi container có port 80 của riêng nó |
| Mount | Các điểm mount: container thấy cây thư mục riêng |
| UTS | Hostname |
| IPC | Hàng đợi message, shared memory giữa process |
| User | UID/GID: root trong container có thể là user thường ở host |
| Cgroup | Gốc của cây cgroup mà container nhìn thấy |
| Time | Đồng hồ boot và monotonic |

### cgroup (control group)
- **Là gì:** tính năng kernel gom process thành nhóm, rồi giới hạn và đo tài nguyên của cả nhóm: CPU, RAM, I/O disk, số process.
- **Dùng để:** một container không ăn hết tài nguyên của máy. Vượt giới hạn RAM thì kernel giết process (OOM kill). Vượt giới hạn CPU thì process bị bóp (throttle), không bị giết.

### Image
- **Là gì:** gói chỉ đọc gồm nhiều **layer** (lớp file system) xếp chồng, cùng metadata: lệnh chạy mặc định, biến môi trường, port. Mỗi layer là tập thay đổi file so với layer bên dưới và không bao giờ bị sửa sau khi tạo.
- **Dùng để:** làm khuôn để tạo container. Một image tạo được nhiều container.
- Khi chạy container, runtime xếp các layer thành một file system thống nhất (union file system, vd OverlayFS) và thêm một **layer ghi** (writable layer) riêng cho container đó. Mọi thay đổi container tạo ra nằm ở layer ghi. Xoá container là mất layer ghi, image thì vẫn nguyên.
- Image dùng chung layer: mười image cùng base `python` chỉ cần lưu và tải layer base một lần.

### OCI
- **Là gì:** Open Container Initiative, tổ chức giữ các chuẩn mở cho container: **image spec** (định dạng image), **runtime spec** (cách chạy một container), **distribution spec** (cách đẩy/kéo image qua registry).
- **Dùng để:** image build bằng Docker chạy được trên containerd, CRI-O, Podman hay Kubernetes, không bị khoá vào một công cụ.

### Container runtime
- **Là gì:** phần mềm thực sự tạo và chạy container. Có hai tầng: **low-level runtime** (vd `runc`) gọi kernel để tạo namespace và cgroup rồi chạy process; **high-level runtime** (vd `containerd`) quản lý image, kéo image từ registry, quản lý vòng đời container và gọi `runc`.
- **Dùng để:** tách trách nhiệm. Docker CLI và Kubernetes đều không tự tạo container mà nói chuyện với runtime.

### Dockerfile
- **Là gì:** file khai báo từng bước build image. Mỗi lệnh thay đổi file system (`RUN`, `COPY`, `ADD`) tạo ra một layer mới.
- **Dùng để:** build image lặp lại được, có version trong Git.

| Lệnh | Ý nghĩa |
|---|---|
| `FROM` | Image gốc (base image) |
| `WORKDIR` | Thư mục làm việc cho các lệnh sau |
| `COPY` | Copy file từ build context vào image |
| `RUN` | Chạy lệnh lúc build (cài package, compile) |
| `ENV` | Biến môi trường |
| `EXPOSE` | Ghi chú port app lắng nghe (chỉ là metadata, không mở port) |
| `USER` | User chạy process |
| `ENTRYPOINT` / `CMD` | Lệnh chạy khi container khởi động |

- **Build cache**: khi build lại, Docker dùng lại layer cũ nếu lệnh và input của nó không đổi. Một layer đổi thì mọi layer phía sau phải build lại.
- **Multi-stage build**: dùng một stage có đủ công cụ để build, rồi chỉ copy kết quả sang một stage gọn để chạy. Image cuối nhỏ và ít lỗ hổng hơn.

### Registry, repository, tag, digest
- **Registry** — **Là gì:** server lưu và phân phối image (Docker Hub, GitHub Container Registry, Amazon ECR, Harbor). **Dùng để:** CI đẩy image lên, server và Kubernetes kéo image về.
- **Repository**: tập các phiên bản của một image, vd `ghcr.io/acme/api`.
- **Tag** — **Là gì:** nhãn dễ đọc trỏ tới một image, vd `:1.4.2`, `:latest`. Tag **gán lại được** cho image khác.
- **Digest** — **Là gì:** hash SHA-256 của nội dung image, vd `@sha256:3f9a...`. **Dùng để:** chỉ định chính xác một image bất biến. Cùng digest thì chắc chắn cùng nội dung.

### Volume và port mapping
- **Volume** — **Là gì:** vùng lưu trữ nằm ngoài layer ghi của container, do runtime quản lý (named volume) hoặc là một thư mục của host (bind mount). **Dùng để:** giữ dữ liệu sống lâu hơn container (database, file upload).
- **Port mapping** (`-p 8080:80`) — **Là gì:** luật NAT chuyển port 8080 của host vào port 80 trong network namespace của container. **Dùng để:** cho traffic từ ngoài vào được container.

## Cách hoạt động
Chuyện gì xảy ra khi chạy `docker run -p 8080:80 -m 256m nginx:1.27`:

```
docker CLI ──API──► dockerd ──► containerd
                                   │ 1. Chưa có image? Kéo từ registry: manifest → từng layer (theo digest)
                                   │ 2. Xếp layer thành rootfs (OverlayFS) + thêm layer ghi
                                   ▼
                                 runc
                                   │ 3. Tạo namespace: pid, net, mnt, uts, ipc...
                                   │ 4. Tạo cgroup: memory.max = 256 MiB
                                   │ 5. Chạy ENTRYPOINT/CMD làm PID 1 trong container
                                   ▼
                     process nginx (trên kernel của host)
           6. dockerd thêm luật NAT: host:8080 → container:80
```

Trên host, `ps aux` vẫn thấy process nginx. Container không phải máy riêng mà là process được kernel cô lập.

## Ví dụ
Dockerfile multi-stage cho một service Go:

```dockerfile
# Stage 1: build (có đầy đủ Go toolchain, khá nặng)
FROM golang:1.23 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download            # layer này chỉ build lại khi go.mod/go.sum đổi
COPY . .
RUN CGO_ENABLED=0 go build -o /out/api ./cmd/api

# Stage 2: runtime (chỉ chứa binary)
FROM gcr.io/distroless/static-debian12
COPY --from=build /out/api /api
USER nonroot
EXPOSE 8080
ENTRYPOINT ["/api"]
```

`go.mod` được copy và tải dependency *trước* khi copy code, vì code đổi thường xuyên còn dependency hiếm khi đổi. Khi chỉ sửa code, layer `go mod download` được lấy từ cache. Image cuối chỉ chứa binary và vài file tối thiểu, không có shell hay Go toolchain, nên nhỏ hơn image build nhiều lần.

## Câu hỏi

**Container khác máy ảo ở chỗ nào?**
> - **Máy ảo**: máy giả lập có kernel riêng, chạy trên hypervisor.
> - **Container**: process được kernel cô lập bằng namespace và giới hạn bằng cgroup, dùng chung kernel của host.
>
> Ranh giới cô lập là khác biệt gốc, mọi khác biệt khác suy ra từ đó: VM cô lập ở mức phần cứng ảo (mỗi VM một kernel), container cô lập ở mức kernel (mọi container chung một kernel). Vì không phải boot một kernel, container nhẹ (MB thay vì GB) và khởi động nhanh. Vì chung kernel, cô lập yếu hơn: lỗ hổng kernel có thể cho container thoát ra host, và không chạy được hệ điều hành có kernel khác.
>
> Ranh giới: Docker Desktop trên macOS hay Windows thật ra chạy một VM Linux nhỏ, container chạy trong VM đó. Môi trường cần cô lập mạnh có thể dùng sandbox như gVisor hay microVM như Firecracker, đứng giữa VM và container.

**Image khác container thế nào? Một image chạy được bao nhiêu container?**
> - **Image**: khuôn chỉ đọc gồm các layer cộng metadata.
> - **Container**: một thực thể đang chạy (hoặc đã dừng) tạo từ image, có thêm layer ghi và process riêng.
>
> Image và container giống class và object: một image tạo được nhiều container (1–n), mỗi container có layer ghi riêng nên không ảnh hưởng nhau và không ảnh hưởng image. Sửa file trong container đang chạy không làm đổi image. Muốn đổi image thì sửa Dockerfile và build lại.
>
> Ranh giới: `docker commit` tạo được image từ một container, nhưng kết quả không lặp lại được và không ai biết bên trong có gì. Image chuẩn nên build từ Dockerfile.

**Vì sao thứ tự lệnh trong Dockerfile ảnh hưởng tốc độ build?**
> - **Layer**: kết quả của một lệnh thay đổi file system.
> - **Build cache**: các layer đã build, được dùng lại nếu lệnh và input của nó không đổi.
>
> Cache bị vô hiệu theo chuỗi: một layer đổi thì mọi layer phía sau phải build lại. Vì vậy đặt thứ ít thay đổi lên trước (base image, cài package hệ thống, tải dependency) và thứ hay thay đổi xuống sau (copy source code). Copy cả source trước khi tải dependency thì mỗi lần sửa một dòng code là tải lại toàn bộ dependency.
>
> Ranh giới: `RUN apt-get update` được cache theo *nội dung lệnh*, không theo thời gian. Layer cũ có thể chứa danh sách package đã lỗi thời. Build có chủ đích để lấy bản vá thì dùng `--no-cache` hoặc gộp `update` và `install` vào cùng một lệnh `RUN`.

**Tag và digest khác nhau thế nào, vì sao không nên deploy `:latest`?**
> - **Tag**: tên đọc được, trỏ tới một image và gán lại được.
> - **Digest**: hash của nội dung image, bất biến.
>
> Tag là con trỏ có thể dời đi, digest là chính nội dung. `:latest` chỉ là một tag tên "latest", không có nghĩa là bản mới nhất, và có thể trỏ tới image khác giữa hai lần kéo. Deploy bằng `:latest` thì hai node có thể chạy hai phiên bản khác nhau, và khi rollback không biết quay về bản nào. Muốn deploy lặp lại được thì dùng tag cố định gắn với version hoặc commit (`:1.4.2`, `:git-3f9a1c2`), hoặc ghim theo digest.
>
> Ranh giới: tag version vẫn có thể bị ghi đè nếu registry cho phép. Registry có tính năng tag immutable để chặn việc này. Digest là cách duy nhất đảm bảo tuyệt đối.

**Dữ liệu trong container đi đâu khi container bị xoá?**
> - **Writable layer**: lớp ghi riêng của mỗi container, nằm trên các layer chỉ đọc của image.
> - **Volume / bind mount**: lưu trữ nằm ngoài vòng đời container.
>
> Mọi thứ ghi vào file system của container nằm ở layer ghi và mất cùng container. Dữ liệu cần giữ (database, file upload) phải ghi vào volume. Đây là lý do container được coi là "dùng xong bỏ" (ephemeral): có thể xoá và tạo lại bất cứ lúc nào mà không mất gì quan trọng.
>
> Ranh giới: `docker stop` chỉ dừng container, layer ghi vẫn còn và `docker start` lại sẽ thấy dữ liệu cũ. Dữ liệu chỉ mất khi container bị xoá (`docker rm`). Trong Kubernetes, Pod bị tạo lại là một container mới, nên phải dùng volume ([05-kubernetes.md](05-kubernetes.md)).

## Hiểu nhầm thường gặp
- **"Container là VM nhẹ."** Container không có kernel hay init riêng. Nó là process. PID 1 trong container phải tự xử lý signal: không xử lý `SIGTERM` thì container chờ hết thời gian rồi bị `SIGKILL`.
- **"Root trong container thì vô hại."** Nếu không dùng user namespace, root trong container chính là UID 0 trên host. Thoát được ra ngoài là có root trên host. Chạy bằng user thường (`USER`).
- **"`EXPOSE` mở port."** `EXPOSE` chỉ là ghi chú. Port chỉ vào được khi có `-p` hoặc khi có Service trong Kubernetes.
- **"Docker là container."** Docker chỉ là một bộ công cụ. Kubernetes hiện chạy container qua containerd hoặc CRI-O, không cần Docker, mà vẫn chạy được image build bằng Docker nhờ chuẩn OCI.

## Liên quan
- [02-linux-for-ops.md](02-linux-for-ops.md): process, user, file system, những thứ container dựa vào.
- [05-kubernetes.md](05-kubernetes.md): chạy và điều phối container trên nhiều máy.
- [13-devsecops.md](13-devsecops.md): quét image, base image tối thiểu, supply chain.
