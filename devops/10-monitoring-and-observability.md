# Monitoring and observability

> Monitoring là thu thập và theo dõi các chỉ số đã biết trước để phát hiện khi hệ thống hỏng. Observability là khả năng hiểu *vì sao* hệ thống đang hành xử như vậy, chỉ dựa vào dữ liệu nó phát ra (log, metric, trace), kể cả với những loại lỗi chưa từng gặp. Prometheus và Grafana là bộ công cụ phổ biến cho metric, OpenTelemetry là chuẩn chung để phát telemetry.

## Tại sao cần biết
Không đo thì không biết hệ thống đang chạy tốt hay tệ, chỉ biết khi người dùng phàn nàn. Mọi phần trước đều cần dữ liệu từ đây: canary cần metric để quyết định đi tiếp ([09-deployment-strategies.md](09-deployment-strategies.md)), autoscaling cần metric để biết khi nào thêm máy ([12-high-availability-and-dr.md](12-high-availability-and-dr.md)), SLO được tính từ metric ([11-sre-and-incident-management.md](11-sre-and-incident-management.md)), và lúc có sự cố thì log và trace là cách duy nhất để tìm nguyên nhân. Đây là phần Measurement của CALMS và vòng Feedback của Three Ways ([01-devops-culture.md](01-devops-culture.md)).

## Khái niệm cốt lõi

### Monitoring và observability
- **Monitoring** — **Là gì:** theo dõi một tập chỉ số định sẵn và cảnh báo khi chúng vượt ngưỡng. **Dùng để:** trả lời "hệ thống có đang hỏng không" với những kiểu hỏng *đã biết*.
- **Observability** — **Là gì:** tính chất của một hệ thống: từ dữ liệu bên ngoài (telemetry), người vận hành suy ra được trạng thái bên trong. **Dùng để:** trả lời những câu hỏi chưa nghĩ ra trước ("vì sao chỉ khách hàng ở Đức dùng app iOS bản 5.2 bị chậm"), tức những kiểu hỏng *chưa biết*.
- **White-box và black-box** — **White-box:** đo từ bên trong qua metric và log hệ thống tự phát ra. **Dùng để:** debug, thấy vấn đề sắp xảy ra. **Black-box:** đo từ bên ngoài giống người dùng (synthetic check gọi URL định kỳ). **Dùng để:** biết chắc người dùng đang thấy lỗi, hợp để gọi người trực.

### Ba loại telemetry
| | **Log** | **Metric** | **Trace** |
|---|---|---|---|
| Là gì | Bản ghi một sự kiện, có thời gian và nội dung | Giá trị số đo theo thời gian (time series), có label | Đường đi của một request qua nhiều service, gồm các span |
| Trả lời | "Chính xác chuyện gì đã xảy ra?" | "Có bao nhiêu, nhanh hay chậm, tăng hay giảm?" | "Thời gian của request này mất ở đâu?" |
| Chi phí | Cao, tăng theo lượng sự kiện | Thấp, tăng theo số time series | Trung bình, thường lấy mẫu (sampling) |
| Dùng để | Debug chi tiết, kiểm toán | Dashboard, alert, xu hướng | Tìm nút cổ chai, hiểu phụ thuộc giữa các service |

### Log
- **Structured log** — **Là gì:** log dạng có cấu trúc (thường là JSON) với các field cố định như `level`, `msg`, `trace_id`, `user_id`. **Dùng để:** máy lọc và tổng hợp được (`level=error AND service=payment`), thay vì `grep` chuỗi tự do.
- **Log aggregation** — **Là gì:** gom log từ mọi máy và container về một hệ thống tập trung để tìm kiếm. Tiêu biểu là bộ ELK/EFK (Elasticsearch + Logstash/Fluentd + Kibana) và Grafana Loki. **Dùng để:** đọc log khi container đã chết, tìm log của một request trên hàng chục service.
- **Log level**: `DEBUG` < `INFO` < `WARN` < `ERROR`. Production thường chỉ giữ từ `INFO` trở lên để tiết kiệm.

### Metric và Prometheus
- **Time series** — **Là gì:** chuỗi cặp (thời điểm, giá trị) được định danh bằng tên metric cộng bộ label, vd `http_requests_total{service="api", method="GET", status="200"}`.
- **Label** — **Là gì:** cặp key-value thêm chiều cho metric. **Dùng để:** lọc và gộp theo chiều đó (theo service, theo status code).
- **Cardinality** — **Là gì:** số tổ hợp label khác nhau, tức số time series. **Dùng để (cần hiểu):** mỗi tổ hợp là một time series riêng phải lưu. Đặt label là `user_id` hay `request_id` sẽ sinh hàng triệu series và làm sập hệ thống metric.
- **Prometheus** — **Là gì:** hệ thống thu và lưu metric theo mô hình **pull**: định kỳ (vd mỗi 15 giây) gọi HTTP tới endpoint `/metrics` của từng target để **scrape**, lưu vào cơ sở dữ liệu time series, truy vấn bằng **PromQL**. **Dùng để:** metric và alert cho hạ tầng và ứng dụng, đặc biệt trên Kubernetes, nơi Prometheus tự tìm target (service discovery).
- **Exporter** — **Là gì:** chương trình đọc số liệu của một hệ thống không tự phát metric theo định dạng Prometheus (Linux, PostgreSQL, Nginx) rồi phơi ra `/metrics`. Ví dụ: `node_exporter` cho máy Linux.
- **Bốn loại metric của Prometheus:**

| Loại | Là gì | Ví dụ |
|---|---|---|
| **Counter** | Chỉ tăng, về 0 khi process restart | Tổng số request, tổng số lỗi |
| **Gauge** | Lên xuống tự do | RAM đang dùng, số kết nối đang mở |
| **Histogram** | Đếm quan sát vào các bucket, kèm tổng và số lượng (`_bucket`, `_sum`, `_count`) | Phân bố latency, tính được percentile phía server |
| **Summary** | Tính sẵn quantile phía client trong một cửa sổ trượt | Latency p99 của một instance |

- **Grafana** — **Là gì:** công cụ vẽ dashboard và quản lý alert, đọc từ nhiều nguồn dữ liệu (Prometheus, Loki, Elasticsearch, cloud). **Dùng để:** nhìn trực quan và chia sẻ trạng thái hệ thống.

### Trace
- **Trace** — **Là gì:** toàn bộ hành trình của một request. **Span** — **Là gì:** một đoạn công việc trong trace (một lời gọi HTTP, một query database), có thời điểm bắt đầu, thời lượng và span cha.
- **Context propagation** — **Là gì:** truyền `trace_id` và `span_id` từ service này sang service khác qua header, chuẩn là header `traceparent` của W3C Trace Context. **Dùng để:** ghép các span ở nhiều service thành một trace.
- **Sampling** — **Là gì:** chỉ giữ một phần trace (vd 1%, hoặc giữ mọi trace có lỗi). **Dùng để:** giới hạn chi phí lưu trữ.
- Backend trace tiêu biểu: Jaeger, Grafana Tempo, Zipkin.

### OpenTelemetry
- **Là gì:** chuẩn mở và bộ SDK, agent (Collector) để phát và chuyển log, metric, trace theo một định dạng chung (OTLP), không phụ thuộc nơi lưu.
- **Dùng để:** instrument code một lần rồi gửi tới bất kỳ backend nào. Đổi nhà cung cấp monitoring thì không phải viết lại phần instrument.

### Các bộ chỉ số chuẩn
- **Four golden signals** (Google SRE) — dành cho service phục vụ người dùng:
  - **Latency**: thời gian phục vụ một request. Nên tách latency của request thành công khỏi request lỗi.
  - **Traffic**: mức nhu cầu (request/giây).
  - **Errors**: tỷ lệ request lỗi, gồm lỗi rõ (5xx) và lỗi ngầm (trả 200 nhưng sai nội dung).
  - **Saturation**: hệ thống "đầy" tới đâu, xét tài nguyên bị giới hạn nhất (CPU, RAM, độ dài hàng đợi).
- **RED** — dành cho mỗi service: **R**ate (request/giây), **E**rrors (lỗi/giây), **D**uration (phân bố latency). Là bản rút gọn của golden signals.
- **USE** — dành cho mỗi *tài nguyên* (CPU, disk, card mạng): **U**tilization (phần trăm thời gian bận), **S**aturation (lượng việc phải chờ), **E**rrors (số lỗi).

### Percentile
- **Là gì:** p99 = 300 ms nghĩa là 99% request nhanh hơn hoặc bằng 300 ms, còn 1% chậm hơn.
- **Dùng để:** mô tả trải nghiệm của nhóm người dùng tệ nhất, thứ mà giá trị trung bình che mất.

### Alerting
- **Alert rule** — **Là gì:** biểu thức trên metric kèm điều kiện thời gian (vd tỷ lệ lỗi > 5% liên tục 5 phút). **Dùng để:** báo cho người khi cần hành động.
- **Alertmanager** — **Là gì:** thành phần nhận alert từ Prometheus rồi gom nhóm (grouping), loại trùng, chặn alert phụ khi đã có alert gốc (inhibition), tạm tắt (silence), và gửi tới kênh phù hợp (pager, chat, email).
- Alert tốt bám theo **triệu chứng** (người dùng gặp lỗi, latency cao) chứ không bám theo **nguyên nhân** (CPU 90%). Nó phải hành động được (có việc cụ thể để làm) và khẩn cấp thật. Alert gọi người dậy lúc nửa đêm mà không cần làm gì gây ra **alert fatigue**: người trực quen bỏ qua, rồi bỏ qua cả alert thật.

## Cách hoạt động
Luồng telemetry trong một hệ thống trên Kubernetes:

```
   App (SDK OpenTelemetry)           node_exporter, kube-state-metrics
   │ log ra stdout                    │ /metrics
   │ /metrics                         │
   │ span qua OTLP                    │
   ▼                                  ▼
 ┌──────────────── thu thập ──────────────────────────────┐
 │ Fluent Bit (log) │ Prometheus (scrape) │ OTel Collector │
 └───────┬──────────┴─────────┬───────────┴───────┬────────┘
         ▼                    ▼                   ▼
       Loki              Prometheus TSDB        Tempo/Jaeger
         └───────────── Grafana (dashboard, explore) ─────────┘
                              │
                     alert rule ─► Alertmanager ─► pager / chat
```

Khi có sự cố, người trực đi theo một luồng: **alert** từ metric báo triệu chứng → **dashboard** khoanh service và thời điểm → **trace** chỉ ra span chậm hoặc lỗi → **log** có cùng `trace_id` cho biết chi tiết lỗi. Gắn `trace_id` vào mọi dòng log là thứ cho phép nhảy từ trace sang log.

## Ví dụ
Một API Go phơi counter và histogram. Truy vấn PromQL tương ứng:

```promql
# Traffic: số request/giây trong 5 phút gần nhất, theo service
sum by (service) (rate(http_requests_total[5m]))

# Errors: tỷ lệ request 5xx
sum(rate(http_requests_total{status=~"5.."}[5m]))
  / sum(rate(http_requests_total[5m]))

# Latency p99, tính từ histogram
histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))
```

`rate()` dùng cho counter: tính tốc độ tăng mỗi giây, tự xử lý trường hợp counter về 0 khi restart. Alert rule đi kèm:

```yaml
- alert: HighErrorRate
  expr: |
    sum(rate(http_requests_total{status=~"5.."}[5m]))
      / sum(rate(http_requests_total[5m])) > 0.05
  for: 5m                        # phải kéo dài 5 phút, tránh báo vì một đợt tăng ngắn
  labels: { severity: page }
  annotations:
    summary: "API trả >5% lỗi 5xx"
    runbook: "https://wiki.example.com/runbooks/api-5xx"
```

## Câu hỏi

**Monitoring khác observability thế nào?**
> - **Monitoring**: theo dõi chỉ số định sẵn và cảnh báo khi vượt ngưỡng.
> - **Observability**: khả năng suy ra trạng thái bên trong từ telemetry, kể cả với câu hỏi chưa có sẵn.
>
> Tiêu chí phân biệt là loại câu hỏi trả lời được: monitoring trả lời câu hỏi *đã biết* ("CPU có cao không"), observability trả lời câu hỏi *chưa biết* ("vì sao nhóm người dùng này chậm"). Monitoring là một hoạt động, observability là tính chất của hệ thống, có được nhờ telemetry giàu ngữ cảnh (label, trace, log có cấu trúc). Monitoring dựa trên nền observability.
>
> Ranh giới: có đủ ba loại log, metric, trace không có nghĩa là có observability. Thiếu ngữ cảnh để nối chúng (cùng `trace_id`, cùng label service và version) thì vẫn phải đoán.

**Log, metric và trace mỗi loại trả lời câu hỏi gì, khi nào dùng loại nào?**
> - **Log**: bản ghi sự kiện riêng lẻ.
> - **Metric**: số đo tổng hợp theo thời gian.
> - **Trace**: đường đi của một request qua các service.
>
> Chọn theo câu hỏi: "có bao nhiêu, xu hướng thế nào, có vượt ngưỡng không" thì dùng metric (rẻ, giữ được lâu, dùng làm alert). "Thời gian và lỗi của request này nằm ở service nào" thì dùng trace. "Chính xác chuyện gì xảy ra, với dữ liệu nào" thì dùng log. Một sự cố thường đi qua cả ba theo thứ tự: metric báo có vấn đề, trace khoanh vùng, log cho chi tiết.
>
> Ranh giới: đếm sự kiện bằng cách tìm trong log được nhưng đắt và chậm. Thứ cần đếm thường xuyên nên là metric. Ngược lại, đừng nhét chi tiết từng request (user_id) vào label của metric, vì cardinality sẽ bùng nổ.

**Prometheus thu metric như thế nào?**
> - **Pull / scrape**: Prometheus chủ động gọi HTTP tới `/metrics` của target theo chu kỳ.
> - **Target / service discovery**: danh sách endpoint cần scrape, tự cập nhật từ Kubernetes hay cloud.
> - **Exporter**: chương trình chuyển số liệu của hệ thống khác thành định dạng `/metrics`.
>
> Prometheus *kéo* về chứ không chờ ứng dụng đẩy lên. Ứng dụng chỉ giữ giá trị hiện tại của counter và gauge rồi phơi ra, Prometheus quyết định khi nào lấy và gắn thời điểm. Mô hình kéo cho Prometheus biết ngay khi target chết (scrape fail, metric `up` = 0), và ứng dụng không cần biết Prometheus ở đâu.
>
> Ranh giới: job chạy ngắn (batch vài giây) có thể kết thúc trước khi bị scrape. Khi đó job đẩy metric vào Pushgateway, hoặc gửi qua OpenTelemetry. Prometheus đơn lẻ không lưu dài hạn và không mở rộng ngang. Muốn vậy thì dùng thêm Thanos, Mimir hoặc dịch vụ managed.

**Golden signals, RED và USE khác nhau ở đâu?**
> - **Golden signals**: latency, traffic, errors, saturation.
> - **RED**: rate, errors, duration.
> - **USE**: utilization, saturation, errors.
>
> Khác nhau ở *đối tượng được đo*. RED và golden signals đo **service** từ góc request đi qua (người dùng có được phục vụ tốt không). USE đo **tài nguyên** (CPU, disk, mạng có quá tải không). RED là golden signals bỏ saturation. Hai góc bổ sung nhau: RED cho biết người dùng đang bị ảnh hưởng, USE giúp tìm tài nguyên nào là nguyên nhân.
>
> Ranh giới: với hệ thống xử lý hàng đợi hay batch (không có request trực tiếp), "latency" trở thành độ trễ xử lý và "traffic" trở thành lượng message vào. Khung vẫn dùng được, chỉ đổi cách đo.

**Vì sao đo latency bằng p99 mà không bằng trung bình?**
> - **Trung bình (mean)**: tổng chia số lượng.
> - **Percentile (pN)**: giá trị mà N% quan sát nhỏ hơn hoặc bằng.
>
> Phân bố latency luôn lệch, đa số nhanh và một đuôi rất chậm. Trung bình bị phần đông kéo xuống nên giấu mất đuôi chậm. Percentile cao (p95, p99) cho biết trải nghiệm của nhóm người dùng tệ nhất. Ví dụ 99 request mất 50 ms và 1 request mất 5 s: trung bình khoảng 100 ms, trông rất ổn, nhưng cứ 100 người thì một người phải chờ 5 giây. Một trang gọi 50 API thì xác suất gặp ít nhất một lời gọi chậm như vậy là 1 − 0,99^50, tức khoảng 40%.
>
> Ranh giới: không cộng hay lấy trung bình percentile của nhiều instance được (p99 của cả hệ thống không bằng trung bình p99 của từng máy). Muốn gộp đúng thì gộp bucket của histogram rồi mới tính quantile, đây là lý do dùng histogram thay cho summary.

**Thế nào là một alert tốt?**
> - **Triệu chứng**: điều người dùng cảm nhận (lỗi, chậm).
> - **Nguyên nhân**: điều bên trong có thể dẫn tới triệu chứng (CPU cao, disk gần đầy).
> - **Alert fatigue**: tình trạng nhận quá nhiều alert vô ích nên bỏ qua cả alert thật.
>
> Alert gọi người phải thoả cả ba điều: khẩn cấp, hành động được, và phản ánh tác động thật lên người dùng. Vì vậy alert gọi người nên bám vào triệu chứng (tỷ lệ lỗi, latency, tốt nhất là theo tốc độ tiêu error budget). Tín hiệu nguyên nhân chỉ để trên dashboard hoặc tạo ticket. Mỗi alert nên có runbook nói phải làm gì.
>
> Ranh giới: alert theo nguyên nhân vẫn đáng gọi người khi nó *chắc chắn và sắp xảy ra*, vd disk sẽ đầy trong 2 giờ tới theo tốc độ hiện tại. Còn "CPU 90%" mà người dùng không bị ảnh hưởng thì không đáng.

## Hiểu nhầm thường gặp
- **"Càng nhiều dashboard càng tốt."** Hàng trăm dashboard không ai xem thì vô ích. Vài dashboard theo golden signals cho mỗi service đáng giá hơn.
- **"Log mọi thứ cho chắc."** Log là loại telemetry đắt nhất. Log quá nhiều thì tốn tiền và làm chìm mất dòng log quan trọng. Thứ cần đếm thì làm metric.
- **"Health check xanh là service ổn."** Health check chỉ biết process còn trả lời. Service vẫn có thể trả kết quả sai hoặc chậm với người dùng thật. Hãy đo golden signals và chạy black-box check.
- **"Monitoring là việc của Ops."** Chỉ người viết code mới biết phải đo gì bên trong. Instrument là một phần của việc viết tính năng.

## Liên quan
- [../backend/14-debugging.md](../backend/14-debugging.md): log có cấu trúc, pprof, debug production.
- [11-sre-and-incident-management.md](11-sre-and-incident-management.md): SLI/SLO xây trên metric, xử lý incident dựa trên alert.
- [09-deployment-strategies.md](09-deployment-strategies.md): metric dùng cho canary analysis.
- [../enterprise-security/07-logging-and-telemetry.md](../enterprise-security/07-logging-and-telemetry.md): log nhìn từ góc bảo mật và phát hiện tấn công.
