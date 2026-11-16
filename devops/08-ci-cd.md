# CI/CD

> CI/CD là chuỗi tự động hoá đưa một thay đổi code từ lúc commit đến lúc chạy trên production. CI (Continuous Integration) liên tục gộp code và kiểm tra tự động. CD (Continuous Delivery / Deployment) liên tục đưa bản đã kiểm tra tới trạng thái sẵn sàng deploy, hoặc deploy luôn.

## Tại sao cần biết
Nếu mỗi người làm trên nhánh riêng vài tuần rồi mới gộp lại, thì lúc gộp sẽ có hàng trăm conflict và lỗi tích hợp ("integration hell"). Build và deploy bằng tay thì chậm, dễ sai, phụ thuộc vào một người biết cách làm. CI/CD là hiện thực trực tiếp của nguyên tắc Flow và Feedback ([01-devops-culture.md](01-devops-culture.md)): mỗi thay đổi nhỏ được kiểm tra trong vài phút, và cách deploy đã được tự động hoá nên deploy được nhiều lần mỗi ngày. Các chỉ số change lead time và deployment frequency của DORA được quyết định chủ yếu ở đây.

## Khái niệm cốt lõi

### Continuous Integration (CI)
- **Là gì:** thực hành mọi người gộp code vào nhánh chính thường xuyên (ít nhất mỗi ngày), mỗi lần gộp đều chạy build và test tự động.
- **Dùng để:** phát hiện lỗi tích hợp khi thay đổi còn nhỏ và người viết còn nhớ. Nhánh chính luôn ở trạng thái build được.
- Đi kèm **trunk-based development**: nhánh ngắn, sống vài giờ tới vài ngày, merge vào `main`. Tính năng chưa xong thì giấu sau feature flag ([09-deployment-strategies.md](09-deployment-strategies.md)). Các mô hình branching ở [../backend/13-git-and-version-control.md](../backend/13-git-and-version-control.md).

### Continuous Delivery và Continuous Deployment
- **Continuous Delivery** — **Là gì:** mỗi thay đổi qua được pipeline đều *có thể* deploy lên production bất cứ lúc nào, bằng một thao tác. Bước cuối lên production vẫn do người quyết định. **Dùng để:** release là một quyết định kinh doanh (khi nào bật), không còn là một sự kiện kỹ thuật rủi ro.
- **Continuous Deployment** — **Là gì:** mỗi thay đổi qua được pipeline được *tự động* deploy lên production, không có người duyệt. **Dùng để:** đạt lead time ngắn nhất. Đòi hỏi test tự động và monitoring đủ tin cậy để thay người duyệt.

### Pipeline, stage, job, runner
- **Pipeline** — **Là gì:** chuỗi bước tự động chạy khi có sự kiện (push, mở pull request, tạo tag, theo lịch). Được khai báo bằng file trong repo (pipeline as code). **Dùng để:** mọi thay đổi đi qua đúng một quy trình, có version và review như code.
- **Stage / job / step** — **Là gì:** stage là nhóm job theo giai đoạn (build, test, deploy). Job là một đơn vị chạy trên một máy. Step là một lệnh trong job. **Dùng để:** chạy song song những gì độc lập, và dừng sớm khi một bước fail.
- **Runner / agent** — **Là gì:** máy (hoặc container) thực thi job. **Dùng để:** tách nơi điều phối khỏi nơi chạy. Runner có thể do dịch vụ cung cấp hoặc tự host trong mạng nội bộ.
- Công cụ tiêu biểu: GitHub Actions, GitLab CI, Jenkins, CircleCI, Azure Pipelines. Mọi công cụ đều có cùng các khái niệm trên.

### Các stage điển hình
| Stage | Việc | Vì sao đặt ở đây |
|---|---|---|
| **Lint / static analysis** | Kiểm tra format, lỗi tĩnh, quét bảo mật code (SAST) | Rẻ và nhanh nhất, nên chặn sớm nhất |
| **Unit test** | Test từng đơn vị, không cần dịch vụ ngoài | Nhanh, phủ nhiều logic |
| **Build** | Compile, đóng gói thành artifact (binary, image) | Tạo ra đúng *một* artifact dùng cho mọi bước sau |
| **Integration / e2e test** | Chạy artifact với database, dịch vụ thật hoặc giả lập | Chậm hơn, bắt lỗi giữa các thành phần |
| **Security scan** | Quét dependency, image, IaC ([13-devsecops.md](13-devsecops.md)) | Chặn lỗ hổng đã biết trước khi lên môi trường |
| **Publish** | Đẩy artifact lên registry kèm version | Có nguồn duy nhất để deploy |
| **Deploy staging → production** | Đưa artifact lên từng môi trường, có thể có bước duyệt | Kiểm tra lần cuối ở môi trường gần giống thật |

### Artifact
- **Là gì:** sản phẩm của bước build, có version, bất biến: container image, binary, gói `.jar`/`.whl`, Helm chart.
- **Dùng để:** nguyên tắc **build once, deploy many**. Build một lần, rồi *cùng một artifact* được đưa qua staging và production, chỉ khác config. Build lại cho từng môi trường thì thứ đã test ở staging không còn là thứ chạy ở production.
- **Artifact repository / registry** — **Là gì:** nơi lưu artifact (container registry, Nexus, Artifactory, GitHub Packages).

### Build tái lập được (reproducible build)
- **Là gì:** cùng source code và cùng input thì build ra cùng một kết quả.
- **Dùng để:** tin được rằng artifact đúng là sinh ra từ commit đó. Muốn vậy phải ghim version dependency (lockfile như `go.sum`, `package-lock.json`), ghim base image, không tải "bản mới nhất" lúc build.

### Secret trong pipeline
- Pipeline cần credential để đẩy image hay deploy. Credential được lưu trong kho secret của công cụ CI và đưa vào job dưới dạng biến môi trường, tự che đi trong log.
- Cách tốt hơn là **OIDC federation**: công cụ CI phát một token ngắn hạn chứng minh "đây là job X của repo Y", cloud đổi token đó lấy credential tạm thời của một IAM role ([06-cloud-fundamentals.md](06-cloud-fundamentals.md)). Không còn khoá dài hạn nào nằm trong CI.

### GitOps
- **Là gì:** cách vận hành trong đó trạng thái mong muốn của hệ thống (manifest Kubernetes, Helm values) nằm trong Git, và một agent chạy trong môi trường đích tự kéo trạng thái đó về và liên tục áp nó. Theo OpenGitOps, GitOps có bốn nguyên tắc:
  1. **Declarative**: trạng thái mong muốn được mô tả theo kiểu khai báo.
  2. **Versioned and immutable**: lưu ở nơi có version, bất biến, giữ toàn bộ lịch sử (thường là Git).
  3. **Pulled automatically**: agent tự *kéo* khai báo từ nguồn.
  4. **Continuously reconciled**: agent liên tục quan sát trạng thái thật và áp trạng thái mong muốn.
- **Dùng để:** Git trở thành nguồn sự thật duy nhất. Deploy là merge một PR, rollback là revert commit, kiểm toán là xem Git log. Pipeline CI không cần quyền vào cluster.
- Công cụ tiêu biểu: **Argo CD**, **Flux**.

## Cách hoạt động

### Push-based và pull-based deploy
```
 Push-based (CI deploy trực tiếp)
   git push ─► CI: test, build, push image ─► CI chạy kubectl/helm ─► cluster
                                              (CI giữ credential của cluster)

 Pull-based (GitOps)
   git push app ─► CI: test, build, push image ─► CI mở PR sửa tag image
                                                  trong repo config
                                                        │ merge
                                                        ▼
                                                  Git (repo config)
                                                        ▲ kéo, so sánh liên tục
                                          Argo CD/Flux chạy trong cluster ─► áp vào cluster
```

Khác biệt nằm ở *ai giữ quyền* và *ai nhận ra lệch*. Với push-based, CI có quyền vào cluster, và ai sửa tay trong cluster thì không ai biết. Với pull-based, chỉ agent trong cluster có quyền. Agent thấy cluster lệch với Git thì báo, hoặc tự sửa lại (self-heal).

### Một thay đổi đi qua pipeline
```
 commit → PR mở ─► CI: lint, unit test, build, scan ─► review + check xanh ─► merge main
                                                                                  │
   ┌──────────────────────────────────────────────────────────────────────────────┘
   ▼
 build image :git-3f9a1c2 ─► push registry ─► deploy staging ─► smoke test
                                                                    │
            Continuous Delivery: chờ người bấm ◄─────────────────────┤
            Continuous Deployment: tự đi tiếp ──────────────────────►│
                                                                    ▼
                                                    deploy production (canary → 100%)
```

## Ví dụ
Workflow GitHub Actions cho một service Go, chạy khi push lên `main`:

```yaml
name: ci
on:
  push: { branches: [main] }
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with: { go-version-file: go.mod }
      - run: go vet ./...
      - run: go test -race ./...

  build:
    needs: test                         # chỉ chạy khi job test pass
    if: github.ref == 'refs/heads/main' # PR thì chỉ test, không build/push
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
      - run: docker build -t ghcr.io/acme/api:${{ github.sha }} .
      - run: docker push ghcr.io/acme/api:${{ github.sha }}
```

Image được tag bằng commit SHA nên mỗi image truy ngược được về đúng một commit. Bước deploy (không có trong ví dụ) sẽ sửa tag này trong repo config để Argo CD kéo về.

## Câu hỏi

**CI là gì, và vì sao phải merge thường xuyên?**
> - **Continuous Integration**: gộp code vào nhánh chính thường xuyên, mỗi lần gộp đều build và test tự động.
> - **Integration hell**: tình trạng gộp nhánh sống lâu thì gặp hàng loạt conflict và lỗi giữa các phần.
>
> Chi phí tích hợp tăng nhanh hơn tuyến tính theo độ lệch giữa các nhánh. Hai nhánh lệch nhau một ngày thì gộp dễ, lệch nhau một tháng thì mỗi bên đã đổi những thứ bên kia dựa vào. CI giữ độ lệch nhỏ bằng cách merge thường xuyên, và dùng test tự động để mỗi lần merge không làm hỏng nhánh chính.
>
> Ranh giới: có công cụ CI mà mỗi người vẫn giữ nhánh vài tuần thì chỉ là "chạy test tự động", chưa phải CI theo đúng nghĩa. Pipeline đỏ trên `main` thì phải sửa trước mọi việc khác.

**Continuous Delivery khác Continuous Deployment thế nào?**
> - **Continuous Delivery**: mọi thay đổi qua pipeline đều *sẵn sàng* lên production, người bấm nút lên.
> - **Continuous Deployment**: mọi thay đổi qua pipeline *tự động* lên production.
>
> Khác nhau đúng ở một điểm: có hay không bước duyệt của người trước production. Delivery là điều kiện cần của Deployment. Chọn Deployment khi test tự động, monitoring và rollback đủ tin để thay người duyệt. Chọn Delivery khi release cần khớp với lịch kinh doanh, hoặc quy định bắt buộc phải có người duyệt.
>
> Ranh giới: tách *deploy* (đưa code lên máy) khỏi *release* (bật tính năng cho người dùng) bằng feature flag thì Continuous Deployment vẫn giữ được quyền quyết định của con người ở bước release ([09-deployment-strategies.md](09-deployment-strategies.md)).

**Một pipeline gồm những stage nào, theo thứ tự nào?**
> - **Stage**: nhóm bước theo giai đoạn của pipeline.
> - **Fail fast**: dừng ngay ở bước lỗi đầu tiên để phản hồi nhanh.
>
> Sắp stage theo nguyên tắc rẻ và nhanh trước, đắt và chậm sau: lint → unit test → build → integration test và scan → publish → deploy staging → deploy production. Lỗi bị bắt ở bước rẻ nhất có thể, người viết nhận phản hồi trong vài phút. Những bước độc lập (lint và unit test, các loại scan) chạy song song để rút ngắn thời gian.
>
> Ranh giới: pipeline chậm (hơn khoảng 10–15 phút) làm người ta gộp nhiều thay đổi rồi mới push, phá đi mục tiêu thay đổi nhỏ. Khi đó phải tối ưu: cache dependency, chia test chạy song song, chỉ chạy test liên quan.

**Artifact là gì, vì sao phải "build once, deploy many"?**
> - **Artifact**: sản phẩm có version, bất biến của bước build.
> - **Môi trường**: nơi chạy (dev, staging, production), khác nhau ở config.
>
> Thứ chạy ở production phải *chính là* thứ đã được test ở staging. Vì vậy build đúng một lần thành artifact bất biến, gắn version truy về commit, rồi đưa cùng artifact đó qua các môi trường. Thứ khác nhau giữa môi trường (URL database, số replica, secret) nằm ngoài artifact và được đưa vào lúc chạy (biến môi trường, ConfigMap).
>
> Ranh giới: config nhúng vào image lúc build (`ENV DB_URL=...` khác nhau cho từng môi trường) phá vỡ nguyên tắc này. Muốn khác config thì phải build lại, và artifact ở production thành thứ chưa từng được test.

**GitOps hoạt động ra sao, khác gì CI chạy `kubectl apply`?**
> - **GitOps**: Git giữ trạng thái mong muốn, agent trong môi trường đích tự kéo về và liên tục áp.
> - **Reconciliation**: vòng lặp so trạng thái thật với trạng thái mong muốn rồi sửa phần lệch ([05-kubernetes.md](05-kubernetes.md)).
>
> Khác biệt cốt lõi là chiều của luồng và tính liên tục: CI chạy `kubectl apply` là *đẩy* một lần lúc deploy, sau đó cluster lệch đi thì không ai biết. GitOps là agent *kéo* và so sánh liên tục, nên phát hiện và sửa được drift. Credential của cluster cũng chỉ nằm trong cluster, không nằm trong CI. Deploy và rollback trở thành thao tác Git: merge và revert.
>
> Ranh giới: GitOps không tự build image hay chạy test. Phần đó vẫn là việc của CI. Secret không được để dạng rõ trong Git, phải dùng Sealed Secrets, SOPS hoặc External Secrets ([13-devsecops.md](13-devsecops.md)).

## Hiểu nhầm thường gặp
- **"Có Jenkins là có CI/CD."** Công cụ chỉ chạy pipeline. CI/CD đòi hỏi merge thường xuyên, test tự động đáng tin, và nhánh chính luôn xanh.
- **"Test fail thì chạy lại cho xanh."** Test chập chờn (flaky test) làm mọi người mất niềm tin vào pipeline. Phải sửa hoặc cách ly để sửa, không được lờ đi.
- **"CD nghĩa là không ai duyệt."** Chỉ Continuous Deployment mới bỏ bước duyệt. Continuous Delivery vẫn có người quyết định lúc lên production.
- **"Pipeline chỉ dành cho code ứng dụng."** Hạ tầng cũng đi qua pipeline: `terraform plan` khi mở PR, `apply` khi merge ([07-terraform-and-iac.md](07-terraform-and-iac.md)).

## Liên quan
- [../backend/13-git-and-version-control.md](../backend/13-git-and-version-control.md): branch, merge request, mô hình branching.
- [../backend/11-unit-testing.md](../backend/11-unit-testing.md): test pyramid, nền của các stage test.
- [09-deployment-strategies.md](09-deployment-strategies.md): bước deploy cuối pipeline diễn ra thế nào.
- [13-devsecops.md](13-devsecops.md): đưa kiểm tra bảo mật vào pipeline.
