# Enterprise security

Kiến thức cơ sở cốt lõi về an ninh thông tin ở môi trường doanh nghiệp: từ khái niệm rủi ro, hành vi tấn công, các lớp phòng thủ, đến cách một tổ chức phát hiện và ứng phó sự cố qua SIEM, SOC, SOAR/XDR. Một số file tận dụng kết quả từ nghiên cứu [`research/2026-10-18-llm-tuning-rule-giam-false-positive`](../research/2026-10-18-llm-tuning-rule-giam-false-positive/report.md).

## Phạm vi
- **Có:** nền tảng an ninh, mô hình tấn công, framework và quản trị, danh tính, các lớp control, quản lý lỗ hổng, log, SIEM, detection engineering, threat intel, tổ chức SOC, incident response, SOAR/XDR, thuật ngữ giữa các vendor; chuyên đề dữ liệu: vì sao OCSF, cấu trúc và cách đọc event OCSF, map log SIEM/EDR sang OCSF, asset management và asset profile dựng từ log, enrichment, ứng dụng của dữ liệu đã chuẩn hóa.
- **Không:** hướng dẫn cấu hình sâu theo sản phẩm, pentest/exploit chi tiết, mật mã học hình thức, pháp lý theo từng quốc gia, nền tảng mạng (xem [`internet/`](../internet/README.md)).
- **Đối tượng:** người biết CNTT (dev, ops, data) mới vào mảng security.

## Bản đồ tư duy

```
Nền tảng        01 fundamentals · 02 threats · 03 frameworks
Phòng ngừa      04 identity · 05 defense controls · 06 vulnerability mgmt
Phát hiện       07 logging → 08 SIEM → 09 detection engineering ← 10 threat intel
Vận hành        11 SOC → 12 incident response → 13 SOAR/XDR
Tham chiếu      14 vendor terminology map
Dữ liệu         15 why OCSF → 16 schema → 17 đọc event → 18 mapping
Tài sản         19 asset profile → 20 profiling từ log → 21 enrichment → 22 ứng dụng
```

Vòng chính: **log → rule → alert → case → verdict → tuning rule**.

## Các file
Đọc theo thứ tự:

| File | Nội dung |
|---|---|
| [01-security-fundamentals.md](01-security-fundamentals.md) | CIA, asset/threat/vulnerability/risk/control, defense in depth, least privilege, Zero Trust. |
| [02-threats-and-attack-lifecycle.md](02-threats-and-attack-lifecycle.md) | Tác nhân đe dọa, Kill Chain, MITRE ATT&CK (tactic/technique/TTP), IoC vs IoA, Pyramid of Pain. |
| [03-frameworks-and-governance.md](03-frameworks-and-governance.md) | NIST CSF 2.0, ISO 27001, CIS Controls, quy định; governance, risk register, vai trò. |
| [04-identity-and-access.md](04-identity-and-access.md) | Xác thực/phân quyền, MFA, SSO, directory, PAM, tấn công vào danh tính. |
| [05-defense-controls.md](05-defense-controls.md) | Biện pháp theo lớp tài sản: endpoint (EDR), mạng (NDR, firewall), cloud/ứng dụng, dữ liệu. |
| [06-vulnerability-management.md](06-vulnerability-management.md) | CVE/CVSS/KEV/EPSS, vòng quản lý lỗ hổng, ưu tiên theo rủi ro thực. |
| [07-logging-and-telemetry.md](07-logging-and-telemetry.md) | Nguồn log, thu thập, parse, schema chuẩn hóa (OCSF, ECS, UDM, ASIM, CIM), retention, data lake. |
| [08-siem.md](08-siem.md) | SIEM làm gì, các loại rule, UEBA, risk-based alerting, từ alert đến case. |
| [09-detection-engineering.md](09-detection-engineering.md) | Vòng đời rule, Sigma, detection-as-code, TP/FP/BTP/FN, các kiểu tuning. |
| [10-threat-intelligence.md](10-threat-intelligence.md) | Các cấp CTI, TIP, STIX/TAXII, chất lượng IoC, threat hunting. |
| [11-soc-organization.md](11-soc-organization.md) | Tier L1/L2/L3, detection engineer, in-house/MSSP/MDR, multi-tenant, metric, alert fatigue. |
| [12-incident-response.md](12-incident-response.md) | Event/alert/incident, vòng đời IR theo NIST 800-61, playbook vs runbook, forensics. |
| [13-soar-xdr-and-automation.md](13-soar-xdr-and-automation.md) | SOAR, playbook, automation rule, EDR/NDR/XDR, sơ đồ luồng dữ liệu tổng thể. |
| [14-vendor-terminology-map.md](14-vendor-terminology-map.md) | Bảng dịch thuật ngữ giữa Splunk, Sentinel, Elastic, Google SecOps, QRadar. |
| [15-why-ocsf.md](15-why-ocsf.md) | Vì sao phải chuẩn hóa log (bài toán N × M) và vì sao chọn OCSF; lợi ích khi mọi nguồn đã về OCSF và cái giá phải trả. |
| [16-ocsf-schema.md](16-ocsf-schema.md) | Cấu trúc OCSF: category/class/activity, `type_uid`, object `device`/endpoint, profile, extension, `observables`, `enrichments`, `unmapped`. |
| [17-reading-an-ocsf-event.md](17-reading-an-ocsf-event.md) | Quy trình 8 câu hỏi để đọc hiểu mọi event OCSF, ghép câu mô tả, nối event thành chuỗi; ví dụ đọc một alert EDR. |
| [18-mapping-logs-to-ocsf.md](18-mapping-logs-to-ocsf.md) | Map log SIEM/EDR sang OCSF: chọn class theo mã event, phân biệt `device` với `src_endpoint`, chuẩn hóa enum và thời gian; ví dụ Windows 4625. |
| [19-asset-management-and-profile.md](19-asset-management-and-profile.md) | Asset, asset management (vòng discover → retire), inventory khác profile, ba lớp profile (khai báo, quan sát, hành vi), entity resolution, criticality. |
| [20-asset-profiling-from-ocsf-logs.md](20-asset-profiling-from-ocsf-logs.md) | Dựng asset profile từ chính log OCSF: sighting, class nào cho thuộc tính nào, gom theo thời gian, so với CMDB để tìm máy lạ, máy thiếu EDR. |
| [21-asset-enrichment-in-ocsf.md](21-asset-enrichment-in-ocsf.md) | Gắn asset profile ngược vào event: khóa tra cứu, ghi vào `device`/`enrichments`/`resources`, enrich lúc ingest/truy vấn/alert. |
| [22-asset-data-use-cases.md](22-asset-data-use-cases.md) | Ứng dụng của log OCSF sạch cộng asset profile cho phòng ngừa, phát hiện, ứng phó, đo lường; ví dụ xử lý một lỗ hổng mới từ đầu đến cuối. |

## Thuật ngữ nền
- **SIEM**: hệ thống tập trung log và chạy rule để sinh alert.
- **SOC**: đội ngũ vận hành giám sát và ứng phó an ninh.
- **EDR / NDR / XDR**: phát hiện và phản ứng ở endpoint / mạng / nhiều lớp hợp nhất.
- **SOAR**: tự động hóa quy trình xử lý alert.
- **IoC / IoA / TTP**: dấu vết tĩnh / chuỗi hành vi / cách thức tấn công.
- **OCSF**: schema mở, trung lập vendor để chuẩn hóa sự kiện bảo mật.
- **Asset profile / enrichment**: hồ sơ hợp nhất của một tài sản / việc gắn hồ sơ đó vào event.
- **TP / BTP / FP / FN**: true positive / benign true positive / false positive / false negative.
