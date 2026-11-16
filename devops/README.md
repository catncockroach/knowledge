# DevOps

DevOps là cách tổ chức công việc phần mềm để đội phát triển và đội vận hành cùng chịu trách nhiệm đưa thay đổi lên production nhanh, thường xuyên và an toàn. Nó là nền của mọi hệ thống phần mềm chạy thật: code chỉ có giá trị khi được build, deploy, vận hành và theo dõi một cách tin cậy. Bộ ghi chú này đi từ văn hoá và nền máy (Linux, mạng), qua đóng gói và hạ tầng (container, Kubernetes, cloud, Terraform), tới luồng giao phần mềm (CI/CD, chiến lược deploy) và vận hành (monitoring, SRE, HA/DR, bảo mật).

## Phạm vi
- **Có:** kiến thức level **entry**, dùng được cả khi đi làm lẫn khi ôn phỏng vấn: văn hoá DevOps và DORA metrics, Linux cơ sở cho vận hành, mạng từ góc ops, container và Docker, Kubernetes, khái niệm cloud (giảng chung, ví dụ bằng AWS), Terraform/IaC và Ansible, CI/CD và GitOps, chiến lược deploy, monitoring và observability (Prometheus, Grafana, OpenTelemetry), SRE và xử lý sự cố, high availability và disaster recovery, DevSecOps. Mỗi file giảng khái niệm trước, rồi lấy công cụ phổ biến nhất làm ví dụ, có lệnh minh hoạ ngắn khi lệnh giúp hiểu khái niệm. Cuối mỗi file có mục **Câu hỏi**.
- **Không:** Linux chi tiết (sẽ có domain Linux riêng, file 02 chỉ ở mức cơ sở), Git (đã có ở [../backend/13-git-and-version-control.md](../backend/13-git-and-version-control.md)), giao thức mạng (đã có ở [../internet/](../internet/README.md)), bảo mật doanh nghiệp chuyên sâu (đã có ở [../enterprise-security/](../enterprise-security/README.md)), vận hành Kubernetes nâng cao (tự dựng control plane, CNI, service mesh), hướng dẫn từng bước cho một cloud hay một công cụ cụ thể.
- **Đối tượng:** người mới bắt đầu học DevOps, đã biết lập trình và có nền backend cơ bản.

## Bản đồ tư duy
```
                    ┌──────────────────────────────────────────────┐
  Vì sao            │ 01 Văn hoá DevOps (CALMS, Three Ways, DORA)  │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────────┐
  Nền máy           │ 02 Linux  ──►  03 Mạng cho ops                │──► ../internet
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────────┐
  Đóng gói & hạ tầng│ 04 Container/Docker ─► 05 Kubernetes          │
                    │ 06 Cloud ─► 07 Terraform/IaC                  │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────────┐
  Giao phần mềm     │ 08 CI/CD (GitOps) ─► 09 Chiến lược deploy     │
                    └──────────────────────┬───────────────────────┘
                                           │  feedback
                    ┌──────────────────────▼───────────────────────┐
  Vận hành          │ 10 Monitoring ─► 11 SRE/incident ─► 12 HA/DR  │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────────┐
  Xuyên suốt        │ 13 DevSecOps                                  │──► ../enterprise-security
                    └──────────────────────────────────────────────┘
```

## Các file
Đọc theo thứ tự:

| File | Nội dung |
|---|---|
| [01-devops-culture.md](01-devops-culture.md) | DevOps giải quyết mâu thuẫn gì giữa Dev và Ops, CALMS, Three Ways, năm chỉ số DORA, vì sao deploy mẻ nhỏ an toàn hơn, so sánh DevOps, SRE và Platform Engineering |
| [02-linux-for-ops.md](02-linux-for-ops.md) | Linux cơ sở cho người vận hành: cây thư mục, user và permission `rwx`, systemd và journalctl, log, disk và inode, package, SSH, shell script và `set -euo pipefail` |
| [03-networking-for-ops.md](03-networking-for-ops.md) | Mạng từ góc vận hành: tính CIDR, private IP và NAT, firewall stateful/stateless, reverse proxy, load balancer L4 và L7, health check, TTL của DNS khi đổi hạ tầng |
| [04-containers-and-docker.md](04-containers-and-docker.md) | Container khác VM ở đâu, namespace và cgroup, image layer và build cache, OCI và container runtime, Dockerfile multi-stage, tag và digest, volume |
| [05-kubernetes.md](05-kubernetes.md) | Kubernetes: control plane và node, reconciliation loop, Pod/ReplicaSet/Deployment, StatefulSet, Service và Ingress, ConfigMap/Secret, requests/limits, probe, PV/PVC, HPA, Helm |
| [06-cloud-fundamentals.md](06-cloud-fundamentals.md) | IaaS/PaaS/SaaS, region và AZ, shared responsibility, compute, block/file/object storage, VPC và subnet public/private, security group, IAM user/role/policy, chi phí |
| [07-terraform-and-iac.md](07-terraform-and-iac.md) | Infrastructure as Code, declarative và imperative, idempotency, immutable infrastructure, Terraform (provider, resource, module, state, plan/apply, drift), Ansible |
| [08-ci-cd.md](08-ci-cd.md) | CI, Continuous Delivery và Continuous Deployment, stage của pipeline, artifact và "build once, deploy many", secret trong CI, GitOps (Argo CD, Flux) push và pull |
| [09-deployment-strategies.md](09-deployment-strategies.md) | Recreate, rolling, blue-green, canary, shadow, feature flag, tách deploy khỏi release, rollback và roll forward, migration database theo expand and contract |
| [10-monitoring-and-observability.md](10-monitoring-and-observability.md) | Monitoring và observability, log/metric/trace, Prometheus và PromQL, Grafana, OpenTelemetry, golden signals, RED, USE, percentile, alert tốt và Alertmanager |
| [11-sre-and-incident-management.md](11-sre-and-incident-management.md) | SLI, SLO, SLA, error budget và burn rate, toil, on-call và runbook, vòng đời và vai trò khi xử lý incident, postmortem blameless, bảng quy đổi số 9 |
| [12-high-availability-and-dr.md](12-high-availability-and-dr.md) | SPOF, redundancy và failover, availability của chuỗi phụ thuộc, scale ngang và autoscaling, timeout/retry/circuit breaker, replication, backup 3-2-1, RPO/RTO, chiến lược DR |
| [13-devsecops.md](13-devsecops.md) | Shift-left, SAST/SCA/DAST và quét IaC, image (Trivy), quản lý secret (Vault, dynamic secret), least privilege ở mọi tầng, supply chain (SBOM, ký image, provenance), policy as code |

## Thuật ngữ nền
- **Production**: môi trường thật phục vụ người dùng.
- **Artifact**: sản phẩm có version, bất biến của bước build (container image, binary).
- **Declarative**: khai báo trạng thái mong muốn, để công cụ tự tính các bước để đạt được nó.
- **Reconciliation loop**: vòng lặp so trạng thái thật với trạng thái mong muốn rồi sửa phần lệch. Là cơ chế chung của Kubernetes, Terraform và GitOps.
- **Idempotent**: chạy một lần hay nhiều lần đều cho cùng kết quả.
- **Stateless**: instance không giữ trạng thái riêng, nên thay thế và nhân bản được tự do.
- **Blast radius**: phạm vi bị ảnh hưởng khi một thứ hỏng hoặc bị chiếm.
- **SLO / error budget**: mục tiêu độ tin cậy / lượng lỗi được phép trong mục tiêu đó.
