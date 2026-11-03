# Brief: Nên dùng những biểu đồ/graph nào để thể hiện trực quan thông tin khi quản lý một asset và khi quản lý toàn bộ asset inventory của một tenant SOC?

- **Ngày:** 2026-11-03
- **Câu hỏi chính:** Các vendor security dùng những biểu đồ, graph và widget trực quan nào ở trang một asset/user và ở dashboard toàn bộ inventory của một tenant (hoặc của MSSP nhiều tenant), mỗi biểu đồ trả lời câu hỏi vận hành gì, và nên chọn bộ biểu đồ nào cho sản phẩm quản lý tài sản SOC đa tenant trên dữ liệu OCSF v1.9.0?
- **Mục đích:** Chủ repo thiết kế phần trực quan hoá cho chức năng quản lý tài sản + asset profile của các tenant SOC: chọn biểu đồ cho trang asset profile và dashboard inventory tenant, biết dữ liệu OCSF nào nuôi từng biểu đồ, phục vụ vận hành, phân tích, phòng thủ và giảm nhiễu.
- **Câu hỏi phụ:**
  1. Ở cấp một asset/user: vendor dùng biểu đồ gì (risk score trend, đóng góp điểm theo nguồn, timeline/swim lane/heat map hoạt động, heatmap giờ trong tuần, prevalence graph, graph quan hệ host–user–IP–process, attack path, sparkline log volume theo nguồn/coverage, vulnerability/exposure breakdown, peer comparison)? Mỗi cái trả lời câu hỏi gì, có ảnh minh hoạ không?
  2. Ở cấp inventory một tenant: dashboard vendor gồm widget gì (tổng số asset và xu hướng, phân bố theo loại/OS/criticality/BU/site, managed vs unmanaged, coverage EDR/log theo nguồn, stale/new/silent assets, exposure/vuln theo severity, top risky assets/users, asset mới xuất hiện, data freshness, tỷ lệ tài sản chưa phân loại criticality, biểu đồ chất lượng dữ liệu inventory)? Loại biểu đồ (KPI tile, donut, bar, trend line, treemap, heatmap, Sankey/Venn coverage, map, graph) nào được dùng cho câu hỏi nào?
  3. Ở cấp MSSP đa tenant: view tổng hợp so sánh tenant (bảng/heatmap tenant × KPI, ranking) vendor làm thế nào?
  4. Nguyên tắc thiết kế: dashboard SOC/inventory nên chọn biểu đồ thế nào (actionability, drill-down từ widget sang danh sách asset được lọc, tránh vanity chart), và KPI chuẩn (CIS Controls 1/8, CISA) nên trực quan hoá thế nào?
  5. Mỗi biểu đồ khuyến nghị lấy dữ liệu từ class/field OCSF 1.9.0 nào (hoặc từ kho entity tự xây)?
- **Phạm vi:** Bối cảnh SOC/MSSP, quản lý log tập trung đa nguồn. Vendor: Microsoft Defender XDR/Exposure Management/Sentinel, Splunk ES (Exposure Analytics, Asset Investigator, entity analysis), Elastic (Entity Analytics dashboard, entity graph), Google SecOps, CrowdStrike Falcon Exposure Management, Cortex XSIAM, Trend Vision One, Axonius (dashboards/charts), runZero, Tenable, Armis, Wazuh, Exabeam, Sumo Logic, các công cụ khác nếu có. Ưu tiên docs chính thức và ảnh giao diện 2023–2026. Ảnh nhúng bằng URL gốc đã kiểm tra tải được.
- **Ngoài phạm vi:** Lý thuyết dataviz tổng quát không gắn với SOC; dashboard ITAM tài chính/license; giá.
- **Độ sâu:** sâu
- **Kế thừa:** research/2026-11-03-asset-profile-vendor-giao-dien-soc/report.md (đã có mô tả bố cục trang profile, 30 ảnh, ánh xạ OCSF; research mới chỉ đào sâu phần biểu đồ, không lặp lại phần đã có).
