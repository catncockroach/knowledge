# Kubernetes

> Kubernetes (k8s) là hệ thống điều phối container (container orchestration). Bạn khai báo trạng thái mong muốn ("chạy 3 bản của image này, mở port 80 cho chúng"), Kubernetes liên tục so trạng thái thực tế với khai báo đó và tự sửa phần lệch: đặt container lên máy nào, restart khi chết, chuyển đi khi máy hỏng, chia traffic, rollout phiên bản mới.

## Tại sao cần biết
Docker chạy container trên *một* máy ([04-containers-and-docker.md](04-containers-and-docker.md)). Khi có hàng chục service, mỗi service vài bản, rải trên hàng chục máy, sẽ nảy ra những câu hỏi mà Docker không trả lời: đặt container lên máy nào cho vừa tài nguyên, máy chết thì ai chạy lại container, các service tìm nhau bằng địa chỉ nào khi IP container thay đổi liên tục, cập nhật phiên bản sao cho không downtime. Kubernetes là câu trả lời phổ biến nhất hiện nay, và là nền của GitOps ([08-ci-cd.md](08-ci-cd.md)) cũng như các chiến lược deploy ([09-deployment-strategies.md](09-deployment-strategies.md)).

## Khái niệm cốt lõi

### Cluster, control plane, node
- **Cluster** — **Là gì:** một tập máy chạy Kubernetes, gồm control plane và các worker node. **Dùng để:** gộp nhiều máy thành một khối tài nguyên chung.
- **Node** — **Là gì:** một máy (vật lý hoặc VM) chạy workload. **Dùng để:** cung cấp CPU, RAM, mạng để chạy Pod.

**Thành phần control plane** (bộ não, quản lý trạng thái của cả cluster):

| Thành phần | Là gì / Dùng để |
|---|---|
| `kube-apiserver` | Cửa vào duy nhất: mọi thao tác (kubectl, controller, kubelet) đều đi qua HTTP API này. Xác thực, phân quyền, validate rồi ghi vào etcd |
| `etcd` | Kho key-value nhất quán, có tính sẵn sàng cao, lưu toàn bộ trạng thái của cluster |
| `kube-scheduler` | Tìm Pod chưa được gán node và chọn node phù hợp (đủ tài nguyên, đúng ràng buộc) |
| `kube-controller-manager` | Chạy các controller: mỗi controller theo dõi một loại object và kéo thực tế về đúng khai báo |
| `cloud-controller-manager` (tuỳ chọn) | Nối với API của cloud: tạo load balancer, gắn disk, nhận biết node bị xoá |

**Thành phần trên mỗi node:**

| Thành phần | Là gì / Dùng để |
|---|---|
| `kubelet` | Agent đảm bảo các Pod được gán cho node này đang chạy đúng, gọi container runtime, chạy probe, báo trạng thái về API server |
| `kube-proxy` (tuỳ chọn) | Duy trì luật mạng trên node để hiện thực Service (chuyển traffic từ IP của Service tới các Pod) |
| Container runtime | containerd hoặc CRI-O, thực sự chạy container |

### Object và manifest
- **Object** — **Là gì:** một bản ghi trong API của Kubernetes mô tả một thứ cần tồn tại. Mỗi object có `spec` (trạng thái mong muốn, do bạn viết) và `status` (trạng thái thực tế, do Kubernetes ghi). **Dùng để:** quản lý mọi thứ theo kiểu khai báo.
- **Manifest** — **Là gì:** file YAML mô tả object. Bốn trường luôn có: `apiVersion`, `kind`, `metadata` (tên, namespace, label), `spec`.
- **Namespace** — **Là gì:** phân vùng logic trong cluster. **Dùng để:** tách object theo đội hoặc môi trường, đặt quota, phân quyền theo namespace.
- **Label và selector** — **Là gì:** label là cặp key-value gắn lên object (`app: api`), selector là điều kiện lọc theo label. **Dùng để:** nối các object với nhau một cách lỏng lẻo: Deployment quản lý Pod nào, Service chuyển traffic tới Pod nào, đều xác định bằng selector chứ không bằng tên.

### Workload
- **Pod** — **Là gì:** đơn vị nhỏ nhất Kubernetes triển khai, gồm một hoặc vài container chạy cùng nhau trên một node, dùng chung network namespace (gọi nhau qua `localhost`, chung một IP) và có thể dùng chung volume. **Dùng để:** gói những container phải sống cùng nhau, vd app và sidecar thu log. Pod là thứ dùng xong bỏ: chết thì được thay bằng Pod mới có tên và IP mới.
- **ReplicaSet** — **Là gì:** controller giữ đúng N Pod khớp với selector. **Dùng để:** tự tạo Pod mới khi có Pod chết. Thường không tạo trực tiếp mà để Deployment quản lý.
- **Deployment** — **Là gì:** object quản lý ReplicaSet để chạy ứng dụng **stateless** và cập nhật dần (rolling update). Mỗi lần đổi template của Pod (vd đổi image) thì tạo ReplicaSet mới, tăng dần Pod mới, giảm dần Pod cũ. **Dùng để:** deploy, scale và rollback app.
- **StatefulSet** — **Là gì:** giống Deployment nhưng mỗi Pod có danh tính ổn định (tên `db-0`, `db-1`, volume riêng gắn chặt theo tên), tạo và xoá theo thứ tự. **Dùng để:** database, Kafka, những hệ thống mà mỗi bản sao không thay thế được cho nhau.
- **DaemonSet** — **Là gì:** chạy đúng một Pod trên mỗi node (hoặc mỗi node khớp điều kiện). **Dùng để:** agent thu log, agent monitoring, plugin mạng.
- **Job / CronJob** — **Là gì:** Job chạy Pod tới khi hoàn thành, CronJob tạo Job theo lịch. **Dùng để:** migration, batch, backup định kỳ.

### Mạng
- **Service** — **Là gì:** một địa chỉ ổn định (IP ảo và tên DNS như `api.prod.svc.cluster.local`) đứng trước một nhóm Pod chọn bằng selector. Controller liên tục cập nhật danh sách IP của các Pod khớp vào **EndpointSlice**. **Dùng để:** service khác gọi tới mà không cần biết IP của Pod, vốn đổi liên tục, và để chia tải giữa các Pod.

| Loại Service | Tiếp cận từ |
|---|---|
| `ClusterIP` (mặc định) | Chỉ bên trong cluster |
| `NodePort` | Ngoài cluster qua `<IP node>:<port cố định>` trên mọi node |
| `LoadBalancer` | Ngoài cluster qua load balancer do cloud tạo |
| `ExternalName` | Không proxy. Chỉ trả về một bản ghi CNAME tới tên DNS bên ngoài |

- **Ingress** — **Là gì:** luật route HTTP/HTTPS từ ngoài vào Service theo host và path, do một **ingress controller** (vd Nginx, Traefik) thực thi. **Dùng để:** dùng một load balancer L7 cho nhiều service thay vì mỗi service một load balancer. **Gateway API** là API thế hệ mới có cùng mục đích, biểu đạt được nhiều hơn Ingress.

### Cấu hình
- **ConfigMap** — **Là gì:** object chứa cấu hình không bí mật dạng key-value. **Dùng để:** tách config ra khỏi image. Cùng một image chạy được ở dev và prod với config khác nhau. Đưa vào Pod qua biến môi trường hoặc file.
- **Secret** — **Là gì:** object chứa dữ liệu nhạy cảm (mật khẩu, token, certificate). **Dùng để:** đưa bí mật vào Pod mà không ghi vào image hay vào manifest của ConfigMap. Mặc định Secret chỉ được mã hoá **base64** và lưu **không mã hoá** trong etcd. Muốn an toàn phải bật mã hoá etcd (encryption at rest), phân quyền RBAC chặt, hoặc dùng kho secret bên ngoài ([13-devsecops.md](13-devsecops.md)).

### Tài nguyên và sức khoẻ
- **Requests** — **Là gì:** lượng CPU/RAM container *xin đặt chỗ*. **Dùng để:** scheduler chỉ đặt Pod lên node còn đủ phần chưa ai đặt.
- **Limits** — **Là gì:** mức tối đa container được dùng, thực thi bằng cgroup. **Dùng để:** chặn một container ăn hết tài nguyên của node. Vượt limit RAM thì container bị giết (`OOMKilled`). Vượt limit CPU thì bị bóp CPU (throttle).
- **Probe** — **Là gì:** kiểm tra định kỳ do kubelet chạy (HTTP, TCP hoặc chạy lệnh):

| Probe | Khi fail |
|---|---|
| **Startup** | Container bị giết và restart. Liveness và readiness chỉ chạy sau khi startup pass. Dành cho app khởi động lâu |
| **Liveness** | Container bị restart. Dùng để thoát trạng thái treo (deadlock) |
| **Readiness** | Không restart. Pod bị rút khỏi EndpointSlice của Service nên không nhận traffic, pass lại thì nhận lại |

### Lưu trữ
- **PersistentVolume (PV)** — **Là gì:** một vùng lưu trữ thật (disk cloud, NFS) được đăng ký vào cluster. **PersistentVolumeClaim (PVC)** — **Là gì:** yêu cầu lưu trữ của một Pod ("cần 10 GiB, đọc ghi bởi một node"). **StorageClass** — **Là gì:** mô tả loại lưu trữ và cách tự tạo PV khi có PVC (dynamic provisioning). **Dùng để:** tách *nhu cầu* (PVC, do app khai báo) khỏi *cách cung cấp* (PV/StorageClass, do người vận hành cluster lo).

### Autoscaling và đóng gói
- **HorizontalPodAutoscaler (HPA)** — **Là gì:** controller tự đổi số replica theo metric (CPU, RAM hoặc metric tuỳ chỉnh). **Dùng để:** tăng Pod khi tải cao, giảm khi tải thấp ([12-high-availability-and-dr.md](12-high-availability-and-dr.md)).
- **Helm** — **Là gì:** trình quản lý package cho Kubernetes. Một **chart** là bộ template manifest cộng file `values.yaml`. Mỗi lần cài là một **release** có version. **Dùng để:** đóng gói một ứng dụng gồm nhiều manifest, tham số hoá theo môi trường, nâng cấp và rollback cả bộ.
- **kubectl** — **Là gì:** CLI nói chuyện với API server. Lệnh hay dùng: `get`, `describe`, `apply -f`, `logs`, `exec`, `rollout status/undo`.

## Cách hoạt động

### Reconciliation loop
Mọi controller chạy cùng một vòng lặp:

```
        ┌──────────────────────────────────────┐
        ▼                                      │
   Quan sát trạng thái thực tế (status)        │
        │                                      │
   So với trạng thái mong muốn (spec)          │
        │                                      │
   Lệch? ── có ──► hành động để giảm lệch ─────┘
        │
       không ──► chờ sự kiện tiếp theo ─────────┘
```

Vì không ai ra lệnh "tạo Pod" mà chỉ khai báo "cần 3 Pod", nên hệ thống tự lành (self-healing): Pod chết, node mất, hay ai đó xoá nhầm Pod thì controller đều thấy lệch và sửa.

### Chuyện gì xảy ra khi `kubectl apply -f deployment.yaml`

```
kubectl ──► kube-apiserver ──► etcd            1. Xác thực, phân quyền, validate, lưu Deployment
                 │
  Deployment controller thấy Deployment mới    2. Tạo ReplicaSet (replicas: 3)
  ReplicaSet controller thấy thiếu 3 Pod       3. Tạo 3 object Pod (chưa có node)
  kube-scheduler thấy Pod chưa có node         4. Chọn node theo requests, affinity... ghi nodeName
  kubelet trên node đó thấy Pod gán cho mình   5. Gọi containerd kéo image, chạy container, chạy probe
  kubelet báo status Ready                     6. EndpointSlice controller thêm IP Pod vào Service
  kube-proxy trên mọi node cập nhật luật       7. Traffic tới Service bắt đầu đi vào Pod mới
```

Các thành phần không gọi trực tiếp nhau. Mỗi thành phần chỉ *theo dõi* (watch) API server và phản ứng với thay đổi của object.

## Ví dụ
Deployment và Service cho một API:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: prod
spec:
  replicas: 3
  selector:
    matchLabels: { app: api }        # quản lý các Pod có label app=api
  template:                          # khuôn để tạo Pod
    metadata:
      labels: { app: api }
    spec:
      containers:
        - name: api
          image: ghcr.io/acme/api:1.4.2
          ports: [{ containerPort: 8080 }]
          resources:
            requests: { cpu: 250m, memory: 256Mi }   # 250m = 0.25 core
            limits:   { memory: 512Mi }
          readinessProbe:
            httpGet: { path: /ready, port: 8080 }
          livenessProbe:
            httpGet: { path: /healthz, port: 8080 }
---
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: prod
spec:
  selector: { app: api }             # chuyển traffic tới mọi Pod có label app=api
  ports: [{ port: 80, targetPort: 8080 }]
```

Service khác trong cluster gọi `http://api.prod` (hoặc `http://api` nếu cùng namespace). Đổi image thành `1.4.3` rồi `apply` lại là một rolling update. Mặc định có tối đa 25% Pod vượt số replica (`maxSurge`) và tối đa 25% Pod không sẵn sàng (`maxUnavailable`) trong lúc cập nhật. `kubectl rollout undo deployment/api -n prod` quay về ReplicaSet trước. Mặc định Deployment giữ lại 10 ReplicaSet cũ.

## Câu hỏi

**Đã có Docker rồi, vì sao còn cần Kubernetes?**
> - **Container runtime / Docker**: chạy container trên một máy.
> - **Orchestration**: quyết định và duy trì việc chạy nhiều container trên nhiều máy.
>
> Docker trả lời "chạy container này thế nào", Kubernetes trả lời "giữ cho cả hệ thống luôn ở trạng thái mong muốn thế nào" trên một cụm máy: xếp chỗ (scheduling), tự lành, service discovery, chia tải, rolling update, autoscaling, quản lý config và secret. Với một app chạy một máy, Docker (hoặc Docker Compose) là đủ. Khi có nhiều máy, nhiều service và yêu cầu không downtime thì bắt đầu cần orchestration.
>
> Ranh giới: Kubernetes rất phức tạp để tự vận hành. Nhiều đội dùng bản managed (EKS, GKE, AKS) hoặc nền tảng đơn giản hơn (ECS, Cloud Run, PaaS). Chọn theo quy mô và năng lực đội, không phải vì Kubernetes đang thịnh.

**Pod, ReplicaSet và Deployment khác nhau thế nào, cái nào quản lý cái nào?**
> - **Pod**: một hoặc vài container chạy cùng nhau, đơn vị nhỏ nhất.
> - **ReplicaSet**: giữ đúng N Pod khớp selector.
> - **Deployment**: quản lý các ReplicaSet theo từng phiên bản template để rollout và rollback.
>
> Quan hệ là sở hữu theo tầng: 1 Deployment → n ReplicaSet (mỗi phiên bản template một cái, chỉ cái mới nhất có replica > 0 khi không đang rollout) → n Pod. Mỗi tầng giải một bài toán: Pod để chạy, ReplicaSet để đủ số lượng, Deployment để đổi phiên bản. Bạn thường chỉ viết Deployment, hai tầng dưới do controller tạo.
>
> Ranh giới: tạo Pod trực tiếp (không qua controller) thì Pod chết là mất, không ai tạo lại. App cần danh tính ổn định dùng StatefulSet, agent chạy trên mỗi node dùng DaemonSet, việc chạy tới khi xong dùng Job. Các loại này thay Deployment chứ không đi qua Deployment.

**Một request từ ngoài đi tới Pod như thế nào?**
> - **Ingress / Gateway**: luật route HTTP theo host và path, do ingress controller thực thi.
> - **Service**: IP ảo và tên DNS ổn định đứng trước một nhóm Pod.
> - **EndpointSlice**: danh sách IP của các Pod đang Ready khớp với selector của Service.
>
> Traffic đi qua các lớp gián tiếp, từ ổn định tới thay đổi liên tục: load balancer của cloud → ingress controller (chọn Service theo host/path) → Service (IP ổn định) → một Pod trong EndpointSlice (IP đổi liên tục). Lớp gián tiếp tồn tại vì Pod là thứ dùng xong bỏ, IP của Pod không dùng làm địa chỉ được. Bên trong cluster thì bỏ hai lớp đầu: gọi thẳng tên DNS của Service.
>
> Ranh giới: Service chỉ gửi traffic tới Pod có readiness pass. Pod Running mà không Ready thì không nhận traffic. Đây là lỗi hay gặp khi "Service không chạy" mà Pod vẫn đang Running.

**Requests khác limits thế nào?**
> - **Requests**: phần tài nguyên đặt chỗ, dùng khi *xếp lịch*.
> - **Limits**: mức trần, dùng khi *chạy*, thực thi bằng cgroup.
>
> Requests quyết định Pod được đặt lên đâu, limits quyết định Pod bị chặn ở đâu. Scheduler cộng requests của các Pod trên mỗi node, không nhìn mức dùng thực tế, nên requests quá thấp làm node bị nhồi quá tải. Khi chạy, vượt limit RAM thì bị giết (`OOMKilled`), vượt limit CPU thì chỉ bị bóp vì CPU chia lại được còn RAM thì không thu hồi được.
>
> Ranh giới: thiếu requests làm scheduler xếp mù, và Pod là ứng viên bị đuổi (evict) đầu tiên khi node thiếu tài nguyên. Limits CPU quá chặt làm tăng latency do throttle, kể cả khi node còn CPU trống.

**Liveness probe khác readiness probe thế nào?**
> - **Probe**: kiểm tra định kỳ kubelet chạy vào container.
> - **Liveness**: "container còn sống không".
> - **Readiness**: "container có sẵn sàng nhận traffic không".
>
> Hai probe khác nhau ở hành động khi fail: liveness fail thì *restart* container, readiness fail thì *rút khỏi traffic* nhưng để container chạy tiếp. Lỗi tự khỏi hoặc tạm thời (đang khởi động, database tạm chậm, đang quá tải) thuộc về readiness. Chỉ trạng thái không tự thoát được (deadlock) mới thuộc về liveness.
>
> Ranh giới: liveness probe kiểm tra cả dependency (database) là bẫy kinh điển. Database chậm làm mọi Pod bị restart cùng lúc, biến sự cố nhỏ thành sập toàn bộ. App khởi động lâu thì dùng startup probe để liveness không giết app trước khi nó kịp lên.

**Secret của Kubernetes có thật sự bí mật không?**
> - **Secret**: object chứa dữ liệu nhạy cảm, đưa vào Pod qua biến môi trường hoặc file.
> - **base64**: cách mã hoá để biểu diễn dữ liệu nhị phân thành chữ, không phải mã hoá bảo mật.
>
> Secret được tách riêng để kiểm soát truy cập, không phải để mã hoá: mặc định nó chỉ được base64 và lưu nguyên văn trong etcd. Ai đọc được etcd, có quyền `get secret`, hoặc tạo được Pod trong namespace đó là đọc được Secret. Muốn an toàn cần mã hoá etcd, RBAC chặt và không commit Secret vào Git.
>
> Ranh giới: muốn lưu Secret trong Git theo kiểu GitOps thì dùng công cụ mã hoá như Sealed Secrets hoặc SOPS, hoặc đồng bộ từ kho secret bên ngoài bằng External Secrets ([13-devsecops.md](13-devsecops.md)).

## Hiểu nhầm thường gặp
- **"Pod là container."** Pod là vỏ bọc của một hoặc vài container dùng chung mạng và volume. Restart container không tạo Pod mới, còn xoá Pod thì có.
- **"`kubectl edit` để sửa production."** Sửa tay thì lệch khỏi manifest trong Git. Lần apply hoặc sync tiếp theo sẽ ghi đè, hoặc tệ hơn là không ai biết đã sửa gì.
- **"Kubernetes tự làm app chịu lỗi."** Kubernetes restart và rải Pod, nhưng app phải stateless, xử lý `SIGTERM` để dừng gọn, và có probe đúng thì mới không mất request khi Pod bị thay.
- **"Namespace là ranh giới bảo mật."** Namespace chỉ là phân vùng logic. Mặc định Pod ở namespace khác nhau vẫn gọi được nhau, muốn chặn phải dùng NetworkPolicy và RBAC.

## Liên quan
- [04-containers-and-docker.md](04-containers-and-docker.md): container, image, runtime mà Kubernetes điều phối.
- [03-networking-for-ops.md](03-networking-for-ops.md): load balancer và reverse proxy, nền của Service và Ingress.
- [08-ci-cd.md](08-ci-cd.md): GitOps đồng bộ manifest từ Git vào cluster.
- [09-deployment-strategies.md](09-deployment-strategies.md): rolling update, blue-green, canary trên Kubernetes.
