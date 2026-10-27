# Quy trình kiểm định chất lượng content SOAR của vendor

Ghi chú chung về nguồn: trong phiên này `WebFetch` không phân giải được phần lớn domain docs của vendor (xsoar.pan.dev, cortex-docs, learn.microsoft.com, docs.cloud.google.com, tines.com, kb.torq.io). Vì vậy phần XSOAR, Splunk SOAR, Sentinel, IBM, TheHive và Shuffle được đọc **trực tiếp từ mã nguồn hoặc file docs trên GitHub** (repo `demisto/content-docs`, `demisto/demisto-sdk`, `demisto/content`, `splunk-soar-connectors/.github`, `Azure/Azure-Sentinel`, `ibmresilient/resilient-python-api`, `TheHive-Project/Cortex-Analyzers`, `shuffle/shuffle-docs`), lấy nhánh master/main ngày 2026-10-27. Phần Google SecOps, Tines, Torq, Swimlane, FortiSOAR và trang Learn của Sentinel **chỉ dựa trên snippet của WebSearch, chưa mở được trang gốc**. Các phát hiện đó được đánh dấu "(snippet)".

## Câu hỏi phụ 1: Vendor kiểm định playbook/integration trước khi đưa lên marketplace hoặc giao khách thế nào?

### Kết luận ngắn
Các vendor lớn có content mở (Palo Alto XSOAR/XSIAM, Splunk SOAR, Microsoft Sentinel) đều dùng chung một khuôn: **PR lên repo GitHub công khai → CI tự động (schema/lint/static/security/unit test/coverage/backward-compat) → review thủ công của team content → (tùy mức hỗ trợ) test chức năng với sản phẩm thật và regression định kỳ → release notes và version bump bắt buộc**. Mức kiểm định **phân tầng theo mức hỗ trợ** (vendor-supported > partner > community). Độ chắc chắn **cao** cho XSOAR, Splunk và Sentinel (đọc thẳng từ source/docs trên GitHub). **Trung bình–thấp** cho Google, Tines, Torq, Swimlane và FortiSOAR (chỉ có snippet hoặc tài liệu mỏng).

### Phát hiện có nguồn

**Palo Alto Cortex XSOAR / XSIAM (repo `demisto/content`, công cụ `demisto-sdk`)**
- Content phân ba mức hỗ trợ. Pack "officially supported" (Palo Alto hoặc Technology Partner) có "a stricter quality-control process" và phải có email/website hỗ trợ. Pack community có "lesser strict quality-control process". — [Contributing XSOAR Content](https://github.com/demisto/content-docs/blob/master/docs/contributing/contributing.md) (bậc 1, không rõ ngày, đọc 2026-10)
- Quy trình gồm: thiết kế theo design guideline. Technology Partner phải được Alliances team duyệt design document và có Partner ID. Dựng cấu trúc bằng `demisto-sdk init`. Trước khi mở PR bắt buộc chạy `demisto-sdk validate -i Packs/<Pack>` và `demisto-sdk lint` (lint chạy luôn unit test). Kèm một video demo ngắn. Sau đó ký CLA, điền form đăng ký, được gán reviewer, và có thể bị yêu cầu demo trực tiếp trên instance XSOAR đã cấu hình pack. — [Contributing XSOAR Content](https://github.com/demisto/content-docs/blob/master/docs/contributing/contributing.md) (bậc 1)
- SLA review: reviewer phản hồi lần đầu trong **5 ngày làm việc**, mỗi vòng sửa phản hồi trong **3 ngày làm việc**. Contributor phải phản hồi trong **14 ngày**, quá hạn thì PR có thể bị đóng. Sau khi merge, một **internal PR** được mở trong vòng 1 giờ để "run our internal validity and security checks" và merge trong 3 ngày làm việc. Pack lên Marketplace trong 3 ngày làm việc sau đó. Đóng góp vào pack XSOAR-supported bắt buộc tuân theo code/doc standards, có **unit tests và test-playbook**. — [Contribution SLA](https://github.com/demisto/content-docs/blob/master/docs/contributing/sla.md) (bậc 1)
- Checklist file bắt buộc. Pack cần `pack_metadata.json`, README, và Release Notes (`ReleaseNotes/1_0_1.md`, bắt buộc khi cập nhật pack có sẵn). Integration cần code, YML, description, logo, README (phần lớn tự sinh), `command_examples`, unit test kèm `test_data/*.json`. Playbook cần YML (đã chạy `demisto-sdk format`), README và ảnh playbook. Với partner/XSOAR-supported thì README, ảnh playbook và unit test là bắt buộc. Checklist còn ghi: "we do **not** enforce a test to each and every function". — [Contribution Checklist](https://github.com/demisto/content-docs/blob/master/docs/contributing/checklist.md) (bậc 1)
- `demisto-sdk lint` chạy trên host các công cụ flake8, bandit (bảo mật), mypy, vulture (dead code), XSOAR linter. Trong docker image đúng runtime nó chạy pylint, pytest và coverage. — [Linting](https://github.com/demisto/content-docs/blob/master/docs/integrations/linting.md) (bậc 1)
- Pre-commit template của repo content gồm: check-json/yaml/ast, debug-statements, ruff, mypy, xsoar-lint, pylint/mypy/pytest trong docker, validate-content-paths, `format`, `secrets` và `coverage-pytest-analyze`. — [.pre-commit-config_template.yaml](https://github.com/demisto/content/blob/master/.pre-commit-config_template.yaml) (bậc 1, master 2026-10)
- Ngưỡng coverage của `demisto-sdk coverage-analyze`: **mặc định tối thiểu 70% cho file mới**, và file sửa đổi chỉ được giảm coverage tối đa **1.0%** so với báo cáo coverage trước (cơ chế ratchet). — [coverage-analyze README](https://github.com/demisto/demisto-sdk/blob/master/demisto_sdk/commands/coverage_analyze/README.md) (bậc 1, master 2026-10-22)
- `demisto-sdk validate`:
  - Mỗi lỗi có mã (ví dụ `[IN103]`). Validate chạy theo git diff (`-g`) hoặc theo đường dẫn (`-a/-i`), và có `--fix` tự sửa.
  - Tập luật cấu hình bằng TOML, chọn được theo **mức hỗ trợ** (`support_level.community` có thể bỏ qua một số luật).
  - Muốn bỏ qua lỗi cho từng file phải ghi vào `.pack-ignore` và chỉ áp dụng cho mã nằm trong danh sách `ignorable_errors`.
  - Bỏ qua luật ở cấp cả pack thì "strongly discouraged". Luật PA135 chặn việc này, không thể ignore, và cần "force-merge approved by a manager".
  — [validate README](https://github.com/demisto/demisto-sdk/blob/master/demisto_sdk/commands/validate/README.md) (bậc 1, 2026-10-22)
- Một số luật validate dành cho playbook (mã PB, trích từ source):
  - PB100: cấm `rolename`.
  - PB103: không có task bị bỏ rời (unconnected).
  - PB105: cấm `DeleteContext all=yes`.
  - PB106: không gán cứng integration instance, vì "not all the users have the same instance".
  - PB108/109: task ID phải là UUID.
  - PB114/115: quiet mode cho playbook chạy trên indicator.
  - PB116: mọi task phải **stop on error**. Lý do: tránh phát hành playbook "that can crash … instances if a playbook task does not stop on error, causing following tasks to rely on its output and fail".
  - PB118/PB119: mọi input khai báo phải được dùng, và mọi input được dùng phải được khai báo.
  - PB121: tham chiếu context phải đúng cú pháp `${path}`, không truyền nhầm dạng chuỗi.
  - PB122/123/124/125/126: **mọi nhánh condition phải được xử lý**, condition không được chỉ có nhánh default.
  - PB133: test được tham chiếu phải tồn tại.
  - PB135: playbook có AI task chỉ được hỗ trợ trên platform marketplace.
  — [PB_validators](https://github.com/demisto/demisto-sdk/tree/master/demisto_sdk/commands/validate/validators/PB_validators) (bậc 1, 2026-10-22)
- Luật backward-compatibility (mã BC):
  - BC101/102: không được xóa hoặc đổi đường dẫn context output.
  - BC103/104: không được đổi tên argument hoặc command.
  - BC105: không được đổi ID.
  - BC110/111: không được thêm argument **required** mới vào command hay script đang có.
  - BC112: không được xóa parameter của integration.
  - BC116: không phá output của "agentix action".
  Lý do được ghi: "Changing the paths may break dependent content items". — [BC_validators](https://github.com/demisto/demisto-sdk/tree/master/demisto_sdk/commands/validate/validators/BC_validators) (bậc 1)
- Luật trên graph phụ thuộc (mã GR):
  - GR103: không dùng content không tồn tại.
  - GR106: test playbook phải được liên kết với content item. Lý do: "unlinked test playbooks are not run in CI … Proper linkage of test playbooks ensures content quality".
  - GR107: content chưa deprecated không được dùng item đã deprecated.
  - GR108: phụ thuộc giữa các pack phải hợp lệ.
  - GR116: tổng token budget của định nghĩa agent và các action/skill. Lý do: "If the combined size is too large it displaces task data in the context window and degrades the agent's performance".
  — [GR_validators](https://github.com/demisto/demisto-sdk/tree/master/demisto_sdk/commands/validate/validators/GR_validators) (bậc 1)
- Test playbook là test end-to-end chạy trong CI "both as part of the build process and on a nightly basis". Khuyến nghị bắt đầu bằng `DeleteContext`, mỗi command một task, và dùng condition để kiểm tra kết quả. Có lệnh `demisto-sdk generate-test-playbook`. Mặc định test playbook không chạy trong CI cho pack không do XSOAR hỗ trợ. — [Test Playbooks](https://github.com/demisto/content-docs/blob/master/docs/integrations/test-playbooks.md) (bậc 1)
- Unit test dùng pytest và pytest-mock để mock cả object `demisto` lẫn API ngoài, dữ liệu mẫu đặt trong `test_data/`. — [Unit Testing](https://github.com/demisto/content-docs/blob/master/docs/integrations/unit-testing.md) (bậc 1)
- Versioning và release notes. Pack dùng MAJOR.MINOR.REVISION, bump bằng `demisto-sdk update-release-notes -u`:
  - major: viết lại hoặc thay đổi lớn;
  - minor: thêm chức năng như mirroring, fetch;
  - revision: thêm item hoặc vài command;
  - documentation: chỉ đổi tài liệu.
  Release notes phải nêu thay đổi, command mới, param/arg mới hoặc sửa, output đổi, và bug fix. Lý do: "A poorly written release note … can lead to a Customer Support ticket". — [Release Notes](https://github.com/demisto/content-docs/blob/master/docs/documentation/release-notes.md) (bậc 1)
- Deprecation: thêm `deprecated: true` vào YAML và ghi "Deprecated. Use {OTHER_INTEGRATION_NAME} instead." vào description. PB104 kiểm tra định dạng description của playbook deprecated. — [Deprecation process (xsoar.pan.dev, snippet)](https://xsoar.pan.dev/docs/reference/articles/deprecation-process-and-hidden-packs) (bậc 1, snippet); [PB104](https://github.com/demisto/demisto-sdk/blob/master/demisto_sdk/commands/validate/validators/PB_validators/PB104_deprecated_description.py) (bậc 1)

**Splunk SOAR (org GitHub `splunk-soar-connectors`)**
- Ma trận kiểm định theo mức hỗ trợ:
  - Mọi app (Community, Developer, Splunk-supported) đều qua Static Tests, Compile Tests, **Security Review** ("ensures no malicious code, libraries…"), Linting và Code Review.
  - **Content Review** áp dụng cho Developer và Splunk-supported.
  - Full Functionality Testing và Regular Regression Testing là bắt buộc với Splunk-supported, còn với Developer-supported thì "Developer Dependent".
  — [TYPES_OF_SUPPORT.md](https://github.com/splunk-soar-connectors/.github/blob/main/.github/TYPES_OF_SUPPORT.md) (bậc 1, không rõ ngày)
- Câu hỏi content review: "Would this update break existing user workflows?", "Is this update something that all users of the app can take advantage of?", "Does the update leverage an officially supported API on the partner product?", "Does this update expose functionality that is excessively difficult to use or understand?". Passive test gồm: app có action **"test connectivity"** bắt buộc không, và có "properly handle exceptions" không. — [TYPES_OF_SUPPORT.md](https://github.com/splunk-soar-connectors/.github/blob/main/.github/TYPES_OF_SUPPORT.md) (bậc 1)
- App do Splunk hỗ trợ: đội QA "tests every action exposed by the app against a working version of the product". Đội QA cũng viết **một SOAR playbook dùng làm regression test** cho từng app, và "Tests are added when fixing bugs to ensure they are not reintroduced". — [TYPES_OF_SUPPORT.md](https://github.com/splunk-soar-connectors/.github/blob/main/.github/TYPES_OF_SUPPORT.md) (bậc 1)
- CI cho mỗi PR:
  - Pre-commit: Conventional Commits, ruff, djlint, mdformat, **semgrep**, build docs, kiểm copyright, đóng gói dependency, **kiểm release notes**, static tests.
  - Pipeline thêm: detect-secrets, quét lỗ hổng dependency, **Test Coverage** ("will fail until support can help add tests"), compile, build.
  - **Sanity Tests trên nhiều môi trường**: phiên bản hiện tại, phiên bản kế tiếp, phiên bản trước, Cloud, RHEL.
  - Integration test.
  — [TESTING.md](https://github.com/splunk-soar-connectors/.github/blob/main/.github/TESTING.md) (bậc 1)
- Pre-commit phải pass thì PR mới được merge. Linter `soar-app-linter` (pylint 3.3.6 khớp với platform, thêm plugin riêng cho SOAR, validate `app.json`) kiểm tra tương thích Python 3.13, vì "apps not updated will fail to execute" ở bản platform đầu 2026. Mỗi PR chỉ được đụng một app hoặc một issue. — [CONTRIBUTING.md](https://github.com/splunk-soar-connectors/.github/blob/main/.github/CONTRIBUTING.md) (bậc 1, 2025–2026); [soar-app-linter README](https://github.com/phantomcyber/soar-app-linter) (bậc 1)
- Template PR yêu cầu liệt kê Features và Bug Fixes. Nó cũng bắt cập nhật `manual_readme_content.md` khi thay đổi REST handler, phương thức xác thực (đặc biệt OAuth), hoặc tương thích theo loại triển khai (ví dụ action không chạy được trên cloud hay automation broker). — [pull_request_template.md](https://github.com/splunk-soar-connectors/.github/blob/main/.github/pull_request_template.md) (bậc 1)
- Ví dụ pre-commit của một app thật (virustotalv3): conventional-pre-commit, check-json/yaml, ruff, djlint, soar-app-linter, mdformat, semgrep, detect-secrets, cùng các hook `build-docs`, `copyright`, `package-app-dependencies`, `notice-file`, `release-notes`, `static-tests`. — [virustotalv3 .pre-commit-config.yaml](https://github.com/splunk-soar-connectors/virustotalv3/blob/main/.pre-commit-config.yaml) (bậc 1)

**Microsoft Sentinel (repo `Azure/Azure-Sentinel`, Content Hub)**
- GitHub Actions chạy trên PR gồm: `playbook-validations`, `arm-ttk-validations`, `solution-validations`, `content-validations`, `json-syntax-validation`, `hyperlinkValidator`/`documents-link-validation`, `logo-validation`, `ScanSecrets`, `codeql-analysis`, `non-ascii-validations`, `kql-validations`, `detection-template-schema-validations`, cùng một workflow nhắc cập nhật version template. — [.github/workflows](https://github.com/Azure/Azure-Sentinel/tree/master/.github/workflows) (bậc 1, master 2026-10-26)
- `playbooksValidator.ts` chạy trên mọi `azuredeploy.json` được sửa trong `Playbooks/` hoặc `Solutions/`:
  - validate schema ARM deployment template;
  - metadata bắt buộc có `title`, `description`, `lastUpdateTime` (phải là timestamp hợp lệ), `support/tier`, `author/name`;
  - `entities` chỉ chứa loại entity được hỗ trợ;
  - bắt buộc có parameter tên playbook, và đúng một resource playbook lấy tên từ parameter đó;
  - location phải là location của resource group.
  — [playbooksValidator.ts](https://github.com/Azure/Azure-Sentinel/blob/master/.script/playbooksValidator.ts), [playbookCheckers](https://github.com/Azure/Azure-Sentinel/tree/master/.script/utils/playbookCheckers) (bậc 1)
- Template PR bắt buộc khai báo Change(s), Reason, Version Updated và Testing Completed. Code phải được test "in a Microsoft Sentinel environment that does not have any custom parsers, functions or tables". Contributor phải chạy validation cục bộ trước khi submit. — [pull_request_template.md](https://github.com/Azure/Azure-Sentinel/blob/master/.github/pull_request_template.md) (bậc 1)
- Quy trình Solution: PR → GitHub validation tự động → team Sentinel review, phản hồi lần đầu trong **5 ngày làm việc** → merge → publish qua Partner Center. Certification FAQ ghi các điểm sau:
  - "ARM-TTK must pass successfully. Any failures should result in rejection";
  - version phải khớp giữa Partner Center, Solution Metadata và mainTemplate.json;
  - gói nộp certification "must exactly match GitHub master repository files" (PR phải merge trước khi publish);
  - link hỏng là "grounds for rejection";
  - "Release notes must be present… Missing release notes will cause rejection";
  - thông tin support (name, email, tier, link) bắt buộc.
  — [Solutions/README.md](https://github.com/Azure/Azure-Sentinel/blob/master/Solutions/README.md) (bậc 1)
- Công cụ đóng gói V3 (`createSolutionV3.ps1`) tự bump semver (patch/minor/major) theo Catalog API hoặc chạy cục bộ. Sau khi tạo package, nó "automatically import and run validation … using the Azure Toolkit / TTK CLI tool". — [Create-Azure-Sentinel-Solution V3 README](https://github.com/Azure/Azure-Sentinel/blob/master/Tools/Create-Azure-Sentinel-Solution/V3/README.md) (bậc 1)
- Wiki Sentinel: contributor tự test chức năng trong Sentinel. Azure Pipelines chỉ chạy "basic syntactical checks", và team review trong vòng 7 ngày. — [Azure-Sentinel wiki Home](https://github.com/Azure/Azure-Sentinel/wiki) (bậc 1, không rõ ngày)
- (snippet) Trang Learn "Create Playbooks for Microsoft Sentinel Solutions" yêu cầu: cấu trúc thư mục cố định, file tên `azuredeploy.json`, Readme.md cho mọi custom connector và playbook, cập nhật phần metadata. Trang khuyến nghị **managed identity** (`ManagedServiceIdentity`) thay vì identity của user. — [Create Playbooks for Microsoft Sentinel Solutions](https://learn.microsoft.com/en-us/azure/sentinel/sentinel-playbook-creation) (bậc 1, snippet, không rõ ngày)

**Google SecOps (SOAR)** (snippet)
- Content Hub có bốn tầng: Google-maintained, Partner, Community và Custom. Community content được kiểm qua "automated quality and validation checks" của Google. Custom content là private và "not verified by Google SecOps". — [Content Hub overview](https://docs.cloud.google.com/chronicle/docs/secops/content_hub) (bậc 1, snippet)
- Để đạt tầng "Google Unified Security Recommended", partner cần ít nhất một Response Integration "published through our contribution workflow", có khả năng thực hiện hành động thay khách hàng, và ít nhất một **starter playbook** dùng integration đó. — [Google Unified Security Recommended](https://docs.cloud.google.com/chronicle/docs/reference/google-unified-security-recommended) (bậc 1, snippet, cập nhật khoảng 03/2026)
- Parser đã có quy trình PR trên GitHub với CI (syntax, cấu trúc thư mục, unit test) và CLA. Với response integration, tháng 06/2025 nhân viên Google chỉ nói đang làm việc này, chưa công bố. — [Community blog: GitHub support for parsers](https://security.googlecloudcommunity.com/community-blog-42/scaling-collective-defense-introducing-github-support-for-google-secops-parsers-7876) (bậc 2, snippet); [Community vs Google integration](https://security.googlecloudcommunity.com/google-security-operations-2/community-integration-vs-google-secops-integration-2017) (bậc 3, snippet)
- Có Playbook Simulator: ingest alert thành test case, và entity bị sửa trong test case không ảnh hưởng case thật. Nhưng chạy simulator trên playbook đang active vẫn ảnh hưởng mọi alert mới, và action như "Isolate Endpoint" vẫn gửi lệnh thật. — [Test playbooks with the simulator](https://docs.cloud.google.com/chronicle/docs/soar/respond/working-with-playbooks/working-with-playbook-simulator) (bậc 1, snippet); [Adoption Guide: Building Effective Playbooks](https://security.googlecloudcommunity.com/google-security-operations-66/adoption-guide-building-effective-playbooks-5856) (bậc 2, snippet)

**IBM QRadar SOAR (resilient-sdk)**
- `resilient-sdk validate` kiểm tra:
  - metadata trong setup.py không được để giá trị mặc định;
  - dependency phải pin version (`~=` hoặc `==`);
  - `selftest.py` (kiểm tra kết nối) bắt buộc có và phải pass;
  - Dockerfile khớp template và dùng đúng base image;
  - `apikey_permissions.txt` có đủ quyền cần thiết;
  - script global không được viết bằng Python 2;
  - playbook đóng gói kèm không được tham chiếu field nằm ngoài package;
  - README và logo phải có, LICENSE không được là file mặc định;
  - **tox tests** phải pass;
  - **Pylint score** đạt ngưỡng;
  - **Bandit scan** phải pass.
  App được phân phối qua IBM App Exchange. — [sdk_validate_configs.py](https://github.com/ibmresilient/resilient-python-api/blob/master/resilient-sdk/resilient_sdk/util/sdk_validate_configs.py) (bậc 1, 2026); [resilient-sdk README](https://github.com/ibmresilient/resilient-python-api/blob/master/resilient-sdk/README.md) (bậc 1)

**Fortinet FortiSOAR** (thấp)
- Connector tự viết tay hoặc dùng FortiSOAR Rapid Development Kit (RDK). Connector "uncertified" là connector do cộng đồng cung cấp. Muốn được certify thì phải qua account manager, PS hoặc TAC. Không tìm thấy checklist certification công khai. — [FortiSOAR Connectors Guide](https://docs.fortinet.com/document/fortisoar/7.6.5/connectors-guide) (bậc 1, snippet); [Community: connector certification](https://community.fortinet.com/fortisoar-community-217/cisco-ise-connector-certification-112484) (bậc 3, 2021)
- Mỗi connector có health check để validate cấu hình và kết nối (trạng thái Available/Disconnected). — [Configuring a connector](https://docs.fortinet.com/document/fortisoar/0.0.0/configuring-a-connector/1/configuring-a-connector) (bậc 1, snippet)

**Tines, Torq, Swimlane** (kiểm soát thay đổi ở phía khách hàng; snippet)
- Tines có Change Control. Khi bật, story live thành **read-only** và mọi thay đổi làm trên draft. Draft nhận được webhook test mà không đụng bản live. Builder mở "change request", team admin approve hoặc reject, rồi push live. Có webhook cho các sự kiện create/approved/rejected/cancelled/pushed. Chỉ admin hoặc người có quyền `change control: manage` mới tắt được change control. — [Tines Change Control](https://www.tines.com/docs/stories/change-control) (bậc 1, snippet, 2026); [Introducing approval flows](https://www.tines.com/whats-new/introducing-change-control-approval-flows/) (bậc 1, snippet)
- Torq:
  - Sửa workflow tạo ra draft, bản published vẫn chạy.
  - Có Test Run, chọn được trigger event cũ để replay.
  - **Mock outputs** thay cho các bước chậm, bị rate-limit, cần người, hoặc gây tác dụng phụ.
  - Phân vai: Creator chỉ sửa được và phải gửi review, Contributor được review và publish.
  - Có version history và export YAML.
  — [Torq: approval flow](https://kb.torq.io/en/articles/9140073-implement-a-workflow-approval-flow-effectively-control-production-changes) (bậc 1, snippet); [Torq: testing & production options](https://kb.torq.io/en/articles/9154312-execute-workflows-testing-and-production-options-in-torq) (bậc 1, snippet)
- Swimlane Turbine có Content Library (marketplace trong platform) và trang docs "Testing and Debugging"/"Test Console". Không tìm thấy thông tin về certification connector. — [Swimlane testing and debugging](https://docs.swimlane.com/testing-and-debugging) (bậc 1, snippet)

**Mã nguồn mở**
- TheHive Cortex Analyzers:
  - "Must" tăng major version khi thêm tính năng, đổi API, đổi output báo cáo hoặc template; tăng minor khi sửa bug.
  - Pin version dependency; git dependency phải tham chiếu commit SHA.
  - Khai báo `max_tlp`/`max_pap`/`check_tlp` để chặn chạy analyzer trên dữ liệu nhạy cảm.
  - Trước khi nộp: chạy thử với cấu hình đúng, và với cấu hình, dataType hoặc TLP thiếu thì analyzer "must generate an explicit error message".
  - Mỗi analyzer một PR vào nhánh develop.
  — [How to create an analyzer](https://github.com/TheHive-Project/Cortex-Analyzers/blob/master/docs/dev_guides/how-to-create-an-analyzer.md) (bậc 1)
- Shuffle: ưu tiên App Creator (OpenAPI) thay vì Python vì dễ bảo trì. Ít field bắt buộc thì tốt hơn. Thêm example response và link tài liệu gốc. **TEST** không chỉ riêng lẻ mà trong workflow kết hợp app khác, và giữ các use case này làm test example. README Markdown là bắt buộc. Team Shuffle validate rồi mới accept. — [Shuffle App Development](https://github.com/shuffle/shuffle-docs/blob/master/handbook/engineering/app_development.md) (bậc 1, không rõ ngày)

### Nhận định
- **Nhận định:** Có ba lớp lặp lại ở mọi vendor có content mở:
  1. **Gate tĩnh tự động**: schema, lint, SAST (bandit/semgrep), quét secret, kiểm backward compatibility, kiểm graph phụ thuộc, bắt buộc có docs và release notes.
  2. **Gate động**: unit test với mock và ngưỡng coverage; test playbook hoặc regression playbook chạy với sản phẩm thật, kể cả nightly; sanity test trên nhiều phiên bản platform.
  3. **Review con người**: code review, content review (UX, có phá workflow người dùng không), demo.

  Lớp 2 và 3 nặng dần theo mức hỗ trợ. Đây là khuôn có thể dùng ngay cho CI nội bộ.
- **Nhận định:** XSOAR là hình mẫu chi tiết nhất: luật validate có mã lỗi, lý do (rationale) và cơ chế ignore bị kiểm soát. Nhiều luật PB của nó thực chất là **tiêu chí chất lượng logic playbook** có thể kiểm tĩnh: không có task mồ côi, mọi nhánh condition được xử lý, input được dùng, không gán cứng instance, stop-on-error, không xóa toàn bộ context. Tất cả đều có thể chuyển thành linter nội bộ.
- **Nhận định:** Microsoft Sentinel chủ yếu validate **gói** (ARM schema, metadata, ARM-TTK, link, version, release notes) và gần như không kiểm logic Logic App. Chất lượng logic phụ thuộc vào review và test thủ công của contributor.
- **Nhận định:** Tines, Torq và Google không công bố gate cho marketplace. Thứ họ cung cấp là **công cụ kiểm soát thay đổi phía khách hàng**: draft vs live, approval, replay event, mock output, simulator. Phần này liên quan nhiều đến câu hỏi phụ 3.
- **Nhận định:** XSOAR đã có luật validate riêng cho AI agent: GR116 token budget, BC116 output của agentix action, PB135 AI task. Đây là dấu hiệu tiêu chí kiểm định đang mở rộng sang thành phần LLM (liên quan đến câu hỏi phụ 5).

## Tiêu chí chất lượng tường minh mà vendor nêu cho playbook/integration (đầu vào cho câu hỏi phụ 2)

### Kết luận ngắn
Vendor nêu khá rõ các tiêu chí về **xử lý lỗi, khả năng kiểm thử, hợp đồng input/output ổn định, bảo mật credential và log, hiệu năng, khả năng đọc/bảo trì, tính di động (không gán cứng môi trường)**. Họ hầu như **không** nêu tiêu chí về độ đúng nghiệp vụ hay an toàn của hành động response (approval cho hành động phá hủy), ngoại trừ cảnh báo trong tài liệu simulator. Độ chắc chắn **trung bình–cao**.

### Phát hiện có nguồn
- **Xử lý lỗi**
  - XSOAR: bọc command trong try/except, ở `main` dùng `return_error` để war room hiện thông báo dễ hiểu thay vì stack trace. — [Code Conventions](https://github.com/demisto/content-docs/blob/master/docs/integrations/code-conventions.md) (bậc 1)
  - XSOAR playbook: task phải stop on error (PB116). — [PB116](https://github.com/demisto/demisto-sdk/blob/master/demisto_sdk/commands/validate/validators/PB_validators/PB116_is_stopping_on_error.py) (bậc 1)
  - Splunk: "Does the app properly handle exceptions?" — [TYPES_OF_SUPPORT.md](https://github.com/splunk-soar-connectors/.github/blob/main/.github/TYPES_OF_SUPPORT.md) (bậc 1)
  - Cortex Analyzers: thiếu cấu hình thì phải báo lỗi tường minh. — [How to create an analyzer](https://github.com/TheHive-Project/Cortex-Analyzers/blob/master/docs/dev_guides/how-to-create-an-analyzer.md) (bậc 1)
- **Retry/timeout, hiệu năng**: XSOAR "do not allow using `sleep`" và yêu cầu dùng `retries`/`backoff_factor` của `BaseClient._http_request`. — [Code Conventions](https://github.com/demisto/content-docs/blob/master/docs/integrations/code-conventions.md) (bậc 1). Playbook cho indicator phải bật quiet mode vì có thể chạy trên hàng nghìn indicator (PB114). — [PB114](https://github.com/demisto/demisto-sdk/blob/master/demisto_sdk/commands/validate/validators/PB_validators/PB114_playbook_quiet_mode.py) (bậc 1)
- **Kiểm tra kết nối bắt buộc**: XSOAR `test-module` phải trả về "ok". Splunk bắt buộc action "test connectivity". IBM bắt buộc `selftest.py` và phải pass. FortiSOAR có health check. — [XSOAR Code Conventions](https://github.com/demisto/content-docs/blob/master/docs/integrations/code-conventions.md); [Splunk TYPES_OF_SUPPORT](https://github.com/splunk-soar-connectors/.github/blob/main/.github/TYPES_OF_SUPPORT.md); [IBM sdk_validate_configs.py](https://github.com/ibmresilient/resilient-python-api/blob/master/resilient-sdk/resilient_sdk/util/sdk_validate_configs.py) (bậc 1)
- **Khả năng kiểm thử**: XSOAR yêu cầu fetch-incidents "must be unit testable": nhận `last_run` làm tham số và trả `next_run`/`incidents` về `main`, thay vì gọi trực tiếp API của platform. — [Code Conventions](https://github.com/demisto/content-docs/blob/master/docs/integrations/code-conventions.md) (bậc 1)
- **Hợp đồng input/output ổn định**: XSOAR BC101–BC112 (không xóa hay đổi output context, không đổi tên argument hay command, không thêm argument required, không xóa parameter). Các tiêu chuẩn Context Standards và DBotScore chuẩn hóa output. — [BC_validators](https://github.com/demisto/demisto-sdk/tree/master/demisto_sdk/commands/validate/validators/BC_validators); [Contributing](https://github.com/demisto/content-docs/blob/master/docs/contributing/contributing.md) (bậc 1). Splunk: "Would this update break existing user workflows?" (bậc 1). Cortex Analyzers: đổi output báo cáo thì bắt buộc tăng major version (bậc 1).
- **Input playbook**: đặt giá trị mặc định khi cần, khử trùng lặp bằng transformer "Uniq", so sánh input không phân biệt hoa thường, hạn chế DT và ưu tiên selector/transformer. — [Playbook Conventions](https://github.com/demisto/content-docs/blob/master/docs/playbooks/playbook-conventions.md) (bậc 1). Input khai báo phải được dùng và ngược lại (PB118/119). Tham chiếu context phải đúng cú pháp (PB121). (bậc 1)
- **Tính đầy đủ của logic**: mọi nhánh condition hoặc reply option của ask-task phải được xử lý, condition không chỉ có default, không có task mồ côi (PB101–PB126). — [PB_validators](https://github.com/demisto/demisto-sdk/tree/master/demisto_sdk/commands/validate/validators/PB_validators) (bậc 1)
- **Tính di động (portability)**: không gán cứng integration instance (PB106), không đặt rolename (PB100) vì đây là thứ khách hàng tự tùy biến. — (bậc 1). Sentinel: tên playbook lấy từ parameter, location theo resource group, khuyến nghị managed identity. — [playbookCheckers](https://github.com/Azure/Azure-Sentinel/tree/master/.script/utils/playbookCheckers) (bậc 1); [Learn, snippet](https://learn.microsoft.com/en-us/azure/sentinel/sentinel-playbook-creation) (bậc 1, snippet)
- **An toàn side-effect trong test**: test playbook nên mở đầu bằng DeleteContext để "sterile". Còn trong playbook production thì cấm `DeleteContext all=yes` (PB105). — (bậc 1). Google: simulator vẫn gửi lệnh thật (ví dụ isolate). Khuyến nghị pin hoặc mock kết quả cho action containment và chạy trên endpoint không quan trọng. — [Google simulator docs](https://docs.cloud.google.com/chronicle/docs/soar/respond/working-with-playbooks/working-with-playbook-simulator) (bậc 1, snippet). Torq có mock outputs. (bậc 1, snippet)
- **Bảo mật credential và log**: XSOAR dùng parameter kiểu `credentials` (type 9) và "**ALWAYS** remove print statements" trước khi release ("Do Not Print Sensitive Data to the Log"). — [Code Conventions](https://github.com/demisto/content-docs/blob/master/docs/integrations/code-conventions.md) (bậc 1). Splunk và Sentinel chạy detect-secrets/ScanSecrets trong CI. Splunk Security Review chặn mã hoặc thư viện độc hại. (bậc 1). Cortex Analyzers dùng giới hạn TLP/PAP. (bậc 1)
- **Supply chain**: pin dependency (IBM, Cortex Analyzers), quét lỗ hổng dependency (Splunk), base image chuẩn (IBM). — (bậc 1)
- **Khả năng đọc và bảo trì**:
  - XSOAR có quy ước đặt tên (Title Case, động từ dạng "Save", condition kết thúc bằng "?"), mô tả task, tránh "programming terms". Thứ tự ưu tiên trình bày là "understanding of flow > readability of lines > aesthetics". — [Playbook Conventions](https://github.com/demisto/content-docs/blob/master/docs/playbooks/playbook-conventions.md) (bậc 1)
  - Splunk Lantern khuyến nghị playbook mô-đun, khoảng **15–20 block** mỗi playbook, vì nhỏ thì load nhanh, chạy xong sớm và dễ debug. — [Improving SOAR playbook design](https://lantern.splunk.com/Security_Use_Cases/Automation_and_Orchestration/Improving_SOAR_playbook_design) (bậc 1, snippet)
- **Documentation**: README cho mọi integration, script và playbook (phần lớn tự sinh), kèm ảnh playbook, `command_examples` và description cấu hình (XSOAR). Splunk yêu cầu `manual_readme_content.md` khi đổi auth, REST handler hoặc tương thích triển khai. Sentinel yêu cầu Readme, metadata (title, description, lastUpdateTime, support tier, author) và support info. — (bậc 1, các nguồn đã dẫn)
- **Thiết kế và giá trị cho người dùng**: content review của Splunk hỏi: có hữu ích cho mọi user không, có dùng API chính thức không, có quá khó dùng không. XSOAR yêu cầu partner theo "use case guidelines" và review design document. Shuffle: "less mandatory fields is always better". — (bậc 1)

### Nhận định
- **Nhận định:** Tiêu chí vendor thiên về **chất lượng kỹ thuật của artifact** (độ bền, hợp đồng, bảo mật, tài liệu), vì họ phát hành content dùng chung cho hàng nghìn khách hàng. Tiêu chí **độ đúng quyết định** (verdict đúng, auto-close an toàn) và **an toàn hành động** (approval cho block/isolate) gần như vắng mặt trong gate của vendor. Phần đó thuộc trách nhiệm của SOC/MSSP khi triển khai, nên cần lấy từ chuẩn (CACAO, NIST) và practitioner ở các câu hỏi phụ 2, 3 và 5.
- **Nhận định:** Có thể suy ra checklist nội bộ tối thiểu:
  - có test-connectivity;
  - có try/except kèm thông báo lỗi dễ đọc;
  - retry/backoff thay cho sleep;
  - không log secret, credential lưu trong vault/param;
  - không gán cứng instance hay môi trường;
  - mọi nhánh được xử lý, stop-on-error rõ ràng;
  - hợp đồng output không phá vỡ (hoặc bump major và ghi release notes);
  - unit test với mock, coverage ≥70% cho code mới và không giảm quá 1%;
  - test playbook hoặc regression playbook;
  - README, release notes, version bump.

### Khoảng trống
- Không mở được trang gốc của Google SecOps, Tines, Torq, Swimlane, FortiSOAR và Microsoft Learn (WebFetch không phân giải DNS, curl bị proxy chặn 403). Các phát hiện về các vendor này dựa trên snippet của WebSearch và cần verify nếu dùng làm trích dẫn quan trọng.
- Không tìm thấy checklist certification công khai cho: Google SecOps response integration (quy trình contribution chưa công bố), FortiSOAR connector, Swimlane connector, và Tines/Torq (không có marketplace mở cho bên thứ ba theo kiểu PR).
- Không xác nhận được ngưỡng Pylint cụ thể trong `resilient-sdk validate` (chỉ thấy thông báo "The Pylint score was {0:.2f}/10"). Cũng chưa xác nhận được ngưỡng coverage mà CI Splunk áp dụng.
- Ngày đăng của các trang docs trên `demisto/content-docs` không xác định được (đọc từ master ngày 2026-10-27). Một số đoạn có dấu hiệu viết từ thời XSOAR 5.x/6.x (2019–2021) nhưng vẫn là tài liệu hiện hành.
- Chưa có nguồn mô tả gate nội bộ của Palo Alto ở bước "internal PR … validity and security checks" ngoài câu trong SLA.

## Truy vấn đã chạy
- Splunk SOAR app certification requirements review (standard)
- Azure-Sentinel playbook contribution guidelines validation checks (standard)
- Google SecOps marketplace integration certification partner submission (standard)
- FortiSOAR connector development certification Fortinet review (standard)
- splunk-soar-connectors contributing pre-commit release notes app review (standard)
- resilient-sdk validate command QRadar SOAR app checks (standard)
- Google SecOps content hub contribute response integration github chronicle (standard)
- Tines story change control test environment best practices (standard)
- demisto-sdk validate deprecated content breaking changes backward compatibility (standard)
- Tines change control story drafts approval docs (standard)
- FortiSOAR connector development guidelines best practices health check (standard)
- Torq workflow version control testing best practices (standard)
- Sentinel playbook template contribution requirements metadata azuredeploy readme "Playbooks" guidance github (extended)
- Google SecOps SOAR IDE testing playbook simulator integration code best practices (extended)
- Splunk SOAR playbook development best practices error handling Lantern (standard)
- Swimlane Turbine playbook testing version control marketplace connectors certified (standard)
- Ngoài ra đọc trực tiếp từ GitHub (raw/sparse clone): demisto/content-docs, demisto/demisto-sdk (validators PB/BC/GR, validate và coverage-analyze README), demisto/content (.pre-commit-config_template.yaml), splunk-soar-connectors/.github, phantomcyber/soar-app-linter, Azure/Azure-Sentinel (.github/workflows, .script/playbooksValidator.ts, Solutions/README.md, Tools V3 README, wiki Home), ibmresilient/resilient-python-api (sdk_validate_configs.py), TheHive-Project/Cortex-Analyzers, shuffle/shuffle-docs.
