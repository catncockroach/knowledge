# DevSecOps

> DevSecOps là đưa bảo mật vào ngay trong luồng DevOps: kiểm tra bảo mật tự động ở mọi bước của pipeline, quản lý secret và quyền theo nguyên tắc tối thiểu, và bảo vệ chuỗi cung ứng phần mềm từ source code tới image đang chạy. Bảo mật trở thành trách nhiệm chung, không còn là một cửa kiểm duyệt ở cuối.

## Tại sao cần biết
Khi deploy nhiều lần mỗi ngày ([08-ci-cd.md](08-ci-cd.md)), không thể chờ một đội bảo mật review tay từng release. Hoặc bảo mật thành nút cổ chai, hoặc bị bỏ qua. Hạ tầng hiện đại cũng mở ra những bề mặt tấn công mới: secret rải trong biến CI và manifest, image kéo từ registry công cộng, hàng trăm dependency mã nguồn mở, IAM role có quyền quá rộng. DevSecOps tự động hoá phần kiểm tra lặp lại được, để người làm bảo mật tập trung vào phần cần phán đoán. Các khái niệm bảo mật nền (CIA, mã hoá, AuthN/AuthZ, các lỗ hổng web) đã có ở [../backend/12-secure-coding.md](../backend/12-secure-coding.md) và [../enterprise-security/](../enterprise-security/README.md).

## Khái niệm cốt lõi

### Shift-left
- **Là gì:** dời kiểm tra bảo mật về phía *trái* của vòng đời (lúc viết code, lúc mở PR, lúc build), thay vì chỉ kiểm tra ở bên *phải* (trước release hay trên production).
- **Dùng để:** sửa lỗi khi còn rẻ. Lỗ hổng phát hiện lúc mở PR thì người viết sửa trong vài phút, phát hiện trên production thì có thể đã bị khai thác.
- Shift-left không thay thế lớp bảo vệ bên phải. Vẫn cần giám sát lúc chạy (runtime), vì có lỗ hổng chỉ được công bố *sau khi* code đã deploy.

### Các loại kiểm tra tự động
| Loại | Là gì | Bắt được gì | Chạy ở |
|---|---|---|---|
| **SAST** (Static Application Security Testing) | Phân tích source code mà không chạy nó | SQL injection, dùng hàm nguy hiểm, mã hoá yếu | PR, CI |
| **SCA** (Software Composition Analysis) | Đối chiếu dependency với cơ sở dữ liệu lỗ hổng đã công bố | Thư viện có CVE, license không phù hợp | PR, CI, định kỳ |
| **Secret scanning** | Tìm chuỗi giống credential trong code và lịch sử Git | API key, mật khẩu, private key bị commit | Pre-commit, PR |
| **IaC scanning** | Kiểm tra file Terraform, manifest Kubernetes | Bucket public, security group mở `0.0.0.0/0`, container chạy privileged | PR |
| **Image scanning** | Quét package của OS và thư viện trong container image | CVE trong base image và dependency | CI, registry, định kỳ |
| **DAST** (Dynamic Application Security Testing) | Tấn công thử ứng dụng đang chạy từ bên ngoài | Lỗi cấu hình, lỗ hổng chỉ lộ ra lúc chạy | Staging |

- **CVE** — **Là gì:** mã định danh công khai cho một lỗ hổng đã biết (vd `CVE-2021-44228`, Log4Shell). **CVSS** — **Là gì:** thang điểm 0–10 đo mức nghiêm trọng. **Dùng để:** đặt ngưỡng chặn pipeline (vd fail khi có lỗ hổng `CRITICAL` mà đã có bản vá).
- **Trivy** — **Là gì:** công cụ mã nguồn mở quét một lúc nhiều loại: image, file system, repo, IaC, Kubernetes. Tìm CVE, cấu hình sai, secret, và sinh SBOM. Các công cụ cùng nhóm: Grype, Snyk, Docker Scout.

### Quản lý secret
- **Secret** — **Là gì:** thông tin cho phép truy cập: mật khẩu database, API key, token, private key, certificate.
- Nguyên tắc: secret không nằm trong source code, không nằm trong image, không nằm trong Git ở dạng rõ, và không in ra log. Secret được cấp lúc chạy, đúng cho thứ cần nó, có thể xoay vòng (rotate) và thu hồi.
- **Secret manager** (HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager) — **Là gì:** dịch vụ lưu secret đã mã hoá, cấp phát theo danh tính và chính sách, ghi log mọi lần truy cập. **Dùng để:** có một nơi duy nhất để quản lý, kiểm toán và xoay vòng secret.
- **Static secret và dynamic secret** — **Static:** một giá trị lưu sẵn, dùng tới khi có người đổi. **Dynamic:** Vault *tạo mới* credential theo yêu cầu (vd một user database riêng cho mỗi Pod), có thời hạn (lease), hết hạn thì tự thu hồi. **Dùng để:** credential bị lộ chỉ dùng được trong thời gian ngắn, và biết chính xác ai dùng credential nào.
- Đưa secret vào Kubernetes: Secret được mã hoá trong etcd và RBAC chặt ([05-kubernetes.md](05-kubernetes.md)). Với GitOps thì dùng Sealed Secrets hoặc SOPS (lưu dạng đã mã hoá trong Git), hoặc External Secrets Operator (đồng bộ từ secret manager).

### Least privilege
- **Là gì:** mỗi danh tính (người, service, pipeline) chỉ có đúng những quyền cần cho việc của nó, trong thời gian cần, không hơn.
- **Dùng để:** giới hạn thiệt hại khi một danh tính bị chiếm (blast radius).
- Áp dụng ở mọi tầng:
  - **Cloud IAM**: role riêng cho mỗi service, policy theo action và resource cụ thể, không dùng `*:*` ([06-cloud-fundamentals.md](06-cloud-fundamentals.md)).
  - **Kubernetes RBAC**: Role/ClusterRole định nghĩa quyền trên loại object. RoleBinding gắn quyền cho user hoặc ServiceAccount. Mỗi app một ServiceAccount riêng.
  - **CI/CD**: dùng OIDC để nhận credential ngắn hạn thay cho key dài hạn, tách quyền deploy production khỏi quyền chạy test.
  - **Container**: chạy bằng user thường, file system chỉ đọc, bỏ bớt Linux capabilities, không chạy `privileged`.
  - **Mạng**: NetworkPolicy chỉ cho phép đúng những đường gọi cần thiết giữa các Pod (zero trust thay vì tin mọi thứ bên trong cluster).

### Supply chain security
- **Software supply chain** — **Là gì:** mọi thứ góp vào artifact cuối: source code, dependency, base image, công cụ build, runner CI, registry.
- **Supply chain attack** — **Là gì:** tấn công vào một mắt xích phía trên để đi xuống mọi người dùng nó: chèn mã độc vào một thư viện phổ biến, đặt tên package gần giống tên thật (typosquatting), đặt package nội bộ trùng tên lên registry công cộng (dependency confusion), chiếm hệ thống build để sửa artifact.
- **SBOM (Software Bill of Materials)** — **Là gì:** danh sách đầy đủ các thành phần và phiên bản có trong một artifact (định dạng SPDX hoặc CycloneDX). **Dùng để:** khi một CVE mới được công bố, trả lời ngay "artifact nào của mình đang dùng thư viện đó".
- **Ký artifact** (Sigstore/cosign) — **Là gì:** gắn chữ ký số vào image. **Dùng để:** lúc deploy kiểm chứng được image đúng là do pipeline của mình build và không bị sửa.
- **Provenance** — **Là gì:** thông tin kiểm chứng được về *cách* một artifact được tạo ra: từ commit nào, bằng hệ thống build nào, với những input nào. **SLSA** là bộ hướng dẫn chia theo level cho việc sinh và kiểm chứng provenance.

### Policy as code và admission control
- **Là gì:** viết luật bảo mật thành code (OPA/Gatekeeper, Kyverno) và áp chúng tự động. Trong Kubernetes, **admission controller** chặn object vi phạm ngay lúc gửi lên API server.
- **Dùng để:** đảm bảo luật được áp nhất quán. Ví dụ: chặn Pod chạy bằng root, chặn image không có chữ ký hoặc kéo từ registry lạ, bắt buộc có resource limit.

## Cách hoạt động
Kiểm tra bảo mật trải dọc vòng đời, mỗi tầng bắt một loại lỗi:

```
 viết code ──► PR ───────────► build ─────────────► registry ──────► deploy ─────────► runtime
  │            │                │                     │                │                  │
 pre-commit:  SAST, SCA,       image scan,           quét lại định kỳ  admission:       giám sát hành vi,
 secret scan  secret scan,     sinh SBOM,            (CVE mới công     chữ ký đúng?     audit log,
              IaC scan,        ký image,             bố sau khi build) không root?      phát hiện bất thường
              review           provenance                              có limit?
 ◄──────────────────────── shift-left: rẻ, nhanh ───────────────────────────────────────────┤
                                                                     lớp bảo vệ khi chạy ───►
```

Không có tầng nào đủ một mình. Image sạch lúc build vẫn có thể dính CVE được công bố một tuần sau, nên phải quét lại định kỳ trong registry và trên cluster.

## Ví dụ
Thêm bước quét image vào pipeline, fail khi có lỗ hổng nghiêm trọng mà đã có bản vá:

```bash
trivy image --severity CRITICAL,HIGH --ignore-unfixed --exit-code 1 ghcr.io/acme/api:git-3f9a1c2
```

```
ghcr.io/acme/api:git-3f9a1c2 (debian 12)
Total: 1 (HIGH: 1, CRITICAL: 0)

│ Library  │ Vulnerability  │ Severity │ Installed │ Fixed   │
│ libexample │ CVE-XXXX-YYYY │ HIGH     │ 1.2.3     │ 1.2.4   │
```

`--exit-code 1` làm job trả exit code khác 0 khi có kết quả, nên pipeline dừng ([02-linux-for-ops.md](02-linux-for-ops.md)). `--ignore-unfixed` bỏ qua lỗ hổng chưa có bản vá để pipeline không bị chặn bởi thứ đội không sửa được. Cách sửa thường là cập nhật base image rồi build lại. Đây là lý do dùng base image tối thiểu như distroless ([04-containers-and-docker.md](04-containers-and-docker.md)): ít package thì ít CVE.

## Câu hỏi

**Shift-left là gì, có phải chỉ cần kiểm tra sớm là đủ?**
> - **Shift-left**: dời kiểm tra bảo mật về các bước sớm (code, PR, build).
> - **Runtime protection**: giám sát và chặn khi hệ thống đang chạy.
>
> Chi phí sửa một lỗ hổng tăng theo độ muộn phát hiện ra nó. Vì vậy mọi kiểm tra tự động hoá được nên chạy càng sớm càng tốt, ngay trong luồng làm việc của developer (PR comment, pipeline fail), với kết quả đủ chính xác để không bị bỏ qua. Nhưng shift-left chỉ bắt được lỗ hổng *đã biết lúc build*. CVE công bố sau đó, credential bị đánh cắp, hành vi bất thường lúc chạy thì cần lớp bảo vệ bên phải.
>
> Ranh giới: công cụ báo quá nhiều kết quả sai (false positive) làm developer quen tay bỏ qua, giống alert fatigue ([10-monitoring-and-observability.md](10-monitoring-and-observability.md)). Hãy bắt đầu với ngưỡng chặn hẹp (critical, có bản vá) rồi mở rộng dần.

**Secret nên lưu ở đâu, và vì sao không để trong code hay biến môi trường cố định?**
> - **Secret**: thông tin cho phép truy cập (mật khẩu, key, token).
> - **Secret manager**: dịch vụ lưu mã hoá, cấp phát theo danh tính, ghi log truy cập, hỗ trợ xoay vòng.
> - **Dynamic secret**: credential được tạo mới theo yêu cầu, có thời hạn và tự thu hồi.
>
> Secret phải sống ở *một* nơi được kiểm soát và chỉ được cấp lúc chạy cho đúng danh tính cần nó. Trong code hay trong image, nó bị nhân bản tới mọi nơi có bản sao (máy dev, Git, registry, cache CI) và không thu hồi được. Credential do chính hạ tầng cấp (IAM role, OIDC, dynamic secret của Vault) còn tốt hơn nữa, vì không có giá trị dài hạn nào để lộ.
>
> Ranh giới: biến môi trường là cách *đưa* secret vào process rất phổ biến và chấp nhận được, miễn là giá trị đến từ secret manager lúc chạy chứ không cố định trong manifest. Nhưng biến môi trường có thể lộ qua crash dump, qua `/proc`, hay qua log in ra mọi biến môi trường. Gắn secret dạng file có quyền hẹp thì an toàn hơn một chút.

**Lỡ commit một API key lên Git thì phải làm gì?**
> - **Lịch sử Git**: mọi commit được giữ lại. Xoá file ở commit sau không xoá được nó khỏi commit trước.
> - **Rotate / revoke**: thu hồi credential cũ và cấp credential mới.
>
> Coi secret đã lộ là đã bị lộ, kể cả khi repo là private và mới đẩy lên vài giây (có bot quét repo công khai liên tục). Thứ tự xử lý: **thu hồi và xoay vòng credential ngay**, kiểm tra log truy cập xem nó đã bị dùng chưa, *sau đó* mới dọn lịch sử Git nếu cần. Chỉ xoá commit mà không thu hồi thì không giải quyết được gì, vì bản sao đã nằm ở máy khác, ở fork, ở cache.
>
> Ranh giới: cách phòng là secret scanning ở pre-commit và ở server Git (chặn push), cộng với dùng credential ngắn hạn để thứ bị lộ tự hết hạn.

**Least privilege áp dụng thế nào trong hạ tầng?**
> - **Least privilege**: mỗi danh tính chỉ có quyền tối thiểu cần cho việc của nó.
> - **Blast radius**: phạm vi thiệt hại khi một danh tính bị chiếm.
>
> Ở mỗi tầng, hỏi "nếu danh tính này bị chiếm thì kẻ tấn công làm được gì", rồi thu hẹp quyền tới khi câu trả lời chấp nhận được. Thực tế là mỗi service một danh tính riêng (IAM role, Kubernetes ServiceAccount) với quyền theo đúng action và resource nó dùng, credential ngắn hạn, quyền production tách khỏi quyền của môi trường khác, và mạng chỉ mở đúng đường cần thiết.
>
> Ranh giới: quyền quá hẹp làm mọi người tìm đường vòng (dùng chung một tài khoản admin). Cần có quy trình xin quyền tạm thời nhanh (just-in-time access) và rà soát định kỳ để thu hồi quyền không còn dùng.

**Supply chain attack là gì, phòng thế nào?**
> - **Software supply chain**: dependency, base image, công cụ build, CI, registry, tức mọi thứ góp vào artifact.
> - **SBOM**: danh sách thành phần của artifact.
> - **Ký và provenance**: bằng chứng artifact do đâu, từ đâu mà ra.
>
> Kẻ tấn công nhắm vào mắt xích phía trên vì một lần chiếm được thì đi xuống mọi người dùng. Phòng theo ba hướng: **kiểm soát cái đưa vào** (ghim version bằng lockfile, kiểm tra hash, dùng registry nội bộ hoặc proxy, quét SCA), **bảo vệ quá trình build** (runner tách biệt, quyền tối thiểu, build tái lập được, sinh provenance), và **kiểm chứng cái đưa ra** (ký image, admission controller chỉ cho chạy image có chữ ký đúng). SBOM giúp phản ứng nhanh khi một thành phần bị phát hiện có vấn đề.
>
> Ranh giới: ký image chỉ chứng minh image do pipeline của bạn tạo ra, không chứng minh bên trong không có mã độc. Nếu dependency đã độc từ trước, pipeline vẫn ký nó một cách "hợp lệ".

**Trivy quét image để tìm những gì?**
> - **Image scanning**: phân tích các layer của image để liệt kê package và thư viện bên trong.
> - **CVE / CVSS**: mã định danh lỗ hổng đã công bố / điểm mức nghiêm trọng.
>
> Image scanner liệt kê mọi thành phần trong image (package của OS như `apt`/`apk`, thư viện ngôn ngữ như Go module, npm, pip) rồi đối chiếu với cơ sở dữ liệu lỗ hổng. Kết quả là danh sách CVE kèm phiên bản đã có bản vá. Trivy còn tìm được cấu hình sai (Dockerfile chạy root), secret bị bỏ quên trong layer, và sinh được SBOM.
>
> Ranh giới: scanner chỉ tìm được lỗ hổng *đã công bố* trong thành phần *nhận diện được*. Lỗ hổng trong code của chính bạn là việc của SAST và review. Binary copy tay vào image không có metadata thì scanner có thể bỏ sót.

## Hiểu nhầm thường gặp
- **"Repo private nên để secret trong đó cũng được."** Repo private vẫn được clone về hàng chục máy, vào cache CI, vào fork. Một lần cấu hình sai là thành public.
- **"Base64 là mã hoá."** Base64 chỉ là cách biểu diễn, ai cũng giải được. Secret của Kubernetes mặc định chỉ là base64.
- **"Quét image một lần lúc build là đủ."** CVE mới được công bố hằng ngày. Image hôm qua sạch thì hôm nay có thể đã có lỗ hổng.
- **"DevSecOps là mua công cụ quét."** Công cụ tạo ra kết quả. Cần có quy trình phân loại và sửa, người chịu trách nhiệm, và ngưỡng chặn rõ ràng, nếu không thì kết quả chỉ chất đống.

## Liên quan
- [../backend/12-secure-coding.md](../backend/12-secure-coding.md): mã hoá, AuthN/AuthZ, lỗ hổng web, quản lý secret ở góc code.
- [../enterprise-security/06-vulnerability-management.md](../enterprise-security/06-vulnerability-management.md): quy trình quản lý lỗ hổng ở cấp tổ chức.
- [../enterprise-security/04-identity-and-access.md](../enterprise-security/04-identity-and-access.md): danh tính và kiểm soát truy cập.
- [08-ci-cd.md](08-ci-cd.md): nơi các bước kiểm tra bảo mật được gắn vào.
