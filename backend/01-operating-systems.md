# Operating systems

> Hệ điều hành (OS) là lớp phần mềm đứng giữa phần cứng và ứng dụng: nó chia sẻ CPU, RAM, ổ đĩa, mạng cho nhiều chương trình một cách an toàn, và cho ứng dụng một giao diện chung (system call) để dùng tài nguyên đó.

## Tại sao cần biết
Mọi backend service rốt cuộc là một **process** chạy trên một OS (thường là Linux). Những câu hỏi "tại sao service chậm", "tại sao bị OOM kill", "tại sao hết file descriptor", "goroutine khác thread thế nào" đều quy về kiến thức OS. Interview entry level hay hỏi: process vs thread, user mode vs kernel mode, virtual memory, các lệnh Linux cơ bản.

## Khái niệm cốt lõi

### Các tầng của một hệ thống máy tính

```
┌──────────────────────────────────────────┐
│ Ứng dụng (Go service, trình duyệt, DB)   │  user space
├──────────────────────────────────────────┤
│ Thư viện hệ thống (libc, Go runtime)     │  user space
├────────────── system call ───────────────┤
│ Kernel: scheduler, memory manager,       │  kernel space
│ file system, network stack, drivers      │
├──────────────────────────────────────────┤
│ Phần cứng: CPU, RAM, disk, NIC           │
└──────────────────────────────────────────┘
```

- **Kernel**: phần lõi của OS, chạy ở chế độ đặc quyền (*kernel mode*), truy cập trực tiếp phần cứng.
- **User space**: nơi ứng dụng chạy (*user mode*), không được đụng thẳng vào phần cứng. Muốn đọc file, mở socket, cấp phát bộ nhớ lớn… phải nhờ kernel qua **system call** (`open`, `read`, `write`, `socket`, `mmap`, `fork`, `execve`…).
- **Vì sao tách hai mode**: nếu một ứng dụng lỗi có thể ghi bừa lên bộ nhớ của kernel hay của ứng dụng khác thì cả máy sập. Tách mode giúp cô lập lỗi và bảo mật.
- Chuyển từ user mode sang kernel mode (*context switch* vào kernel) tốn chi phí, nên ứng dụng hiệu năng cao tìm cách giảm số system call (ví dụ đọc/ghi theo buffer lớn thay vì từng byte).

### Kiến trúc kernel
| Kiểu | Ý tưởng | Ví dụ |
|---|---|---|
| Monolithic | Mọi dịch vụ OS (file system, driver, network) chạy chung trong kernel space | Linux (có thêm *loadable module*) |
| Microkernel | Kernel tối thiểu, các dịch vụ chạy như process riêng ở user space | MINIX, QNX |
| Hybrid | Kết hợp | Windows NT, macOS (XNU) |

Monolithic nhanh hơn (gọi hàm trực tiếp), microkernel ổn định hơn (driver lỗi không kéo sập kernel).

### Linux và Windows
| | Linux | Windows |
|---|---|---|
| Kernel | Monolithic, mã nguồn mở | Hybrid (NT), đóng |
| File system | ext4, xfs, btrfs; một cây thư mục gốc `/` | NTFS; ổ đĩa `C:\`, `D:\` |
| Phân cách đường dẫn | `/` | `\` |
| Xuống dòng | `\n` (LF) | `\r\n` (CRLF) |
| Quản lý dịch vụ | systemd (`systemctl`) | Services (`sc`, services.msc) |
| Vai trò backend | Chiếm đa số server, container | Thường gặp ở môi trường .NET, desktop |

Triết lý Linux/Unix: **"mọi thứ là file"**. File thường, thư mục, thiết bị (`/dev/sda`), socket, pipe đều được thao tác qua **file descriptor** (một số nguyên, 0 = stdin, 1 = stdout, 2 = stderr).

### Process và thread
- **Program**: file thực thi nằm trên đĩa (thụ động).
- **Process**: một chương trình đang chạy. Mỗi process có **không gian địa chỉ riêng** (code, data, heap, stack), bảng file descriptor riêng, PID riêng. Process này không đọc được bộ nhớ của process khác.
- **Thread**: luồng thực thi bên trong process. Các thread của cùng process **chia sẻ** heap, code, file descriptor, nhưng mỗi thread có **stack và thanh ghi riêng**.

```
Process A (PID 100)
┌─────────────────────────────────────┐
│ Code │ Data │ Heap (dùng chung)     │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│ │Thread 1 │ │Thread 2 │ │Thread 3 │ │
│ │ stack   │ │ stack   │ │ stack   │ │
│ └─────────┘ └─────────┘ └─────────┘ │
└─────────────────────────────────────┘
```

| | Process | Thread |
|---|---|---|
| Bộ nhớ | Riêng biệt | Chia sẻ trong process |
| Tạo mới | Tốn kém (copy page table, tài nguyên) | Rẻ hơn |
| Giao tiếp | IPC: pipe, socket, shared memory, message queue | Đọc/ghi biến chung (cần đồng bộ) |
| Lỗi | Một process chết không ảnh hưởng process khác | Một thread crash có thể kéo sập cả process |

Goroutine của Go còn nhẹ hơn thread: nhiều goroutine chạy trên một số ít OS thread, do Go runtime lập lịch (xem [09-concurrency.md](09-concurrency.md)).

### Vòng đời process
```
 new ──► ready ◄──────► running ──► terminated
           ▲   (scheduler)  │
           │                ▼
           └──────────── waiting (chờ I/O, sleep, lock)
```
- **Ready**: sẵn sàng, chờ được cấp CPU.
- **Running**: đang chạy trên một core.
- **Waiting/Blocked**: chờ sự kiện (đọc đĩa, nhận dữ liệu mạng).
- **Zombie** (Linux): process đã kết thúc nhưng process cha chưa đọc exit code (`wait`). **Orphan**: process cha chết trước, được `init`/`systemd` (PID 1) nhận làm con.

### CPU scheduling
Scheduler quyết định process/thread nào được chạy. Một core chỉ chạy một luồng tại một thời điểm; cảm giác "chạy song song" trên một core là nhờ chia **time slice** và **context switch** (lưu thanh ghi, con trỏ lệnh của luồng cũ, nạp của luồng mới).
- **Preemptive**: OS có thể ngắt luồng đang chạy khi hết time slice (Linux, Windows hiện đại).
- Thuật toán kinh điển: FCFS, Shortest Job First, Round Robin, Priority. Linux dùng scheduler dựa trên công bằng (mỗi task được chia CPU theo tỉ lệ).
- **CPU-bound** (tính toán nặng) vs **I/O-bound** (chủ yếu chờ mạng/đĩa). Backend web đa số là I/O-bound, nên mô hình nhiều luồng nhẹ + I/O không chặn rất hiệu quả.

### Quản lý bộ nhớ
- **Virtual memory**: mỗi process thấy một không gian địa chỉ ảo liên tục, riêng của mình. Phần cứng (MMU) cùng kernel dịch địa chỉ ảo → địa chỉ vật lý qua **page table**. Đơn vị là **page** (thường 4 KB).
- Lợi ích: cô lập process; cho phép dùng nhiều hơn RAM thật (đẩy page ít dùng ra **swap** trên đĩa); chia sẻ thư viện chung giữa các process.
- **Page fault**: truy cập một page chưa nằm trong RAM → kernel nạp nó vào. Quá nhiều page fault do thiếu RAM gây **thrashing** (máy gần như đứng).
- Bố cục bộ nhớ của process:
```
địa chỉ cao  ┌──────────────┐
             │ Stack  ↓     │  biến cục bộ, lời gọi hàm; mỗi thread một stack
             │              │
             │ Heap   ↑     │  cấp phát động (new, make, malloc)
             │ Data/BSS     │  biến toàn cục
địa chỉ thấp │ Text (code)  │
             └──────────────┘
```
- **Stack** cấp phát/thu hồi tự động theo lời gọi hàm, rất nhanh. **Heap** cấp phát động, cần giải phóng (C dùng `free`; Go, Java dùng **garbage collector**). Go compiler làm *escape analysis* để quyết định biến nằm stack hay heap.
- **OOM killer** (Linux): khi hết bộ nhớ, kernel chọn giết một process (thường process ăn nhiều RAM nhất). Container bị vượt giới hạn memory cũng bị kill (exit code 137).

### File system và I/O
- File system tổ chức dữ liệu trên đĩa thành file và thư mục. Linux lưu metadata file (quyền, chủ sở hữu, kích thước, vị trí block) trong **inode**; tên file chỉ là một mục trong thư mục trỏ tới inode.
- **Quyền file Linux**: `rwx` cho owner/group/others. `chmod 754 app` = owner `rwx` (7), group `r-x` (5), others `r--` (4).
- **Page cache**: kernel giữ dữ liệu file vừa đọc/ghi trong RAM; đọc lần hai nhanh hơn nhiều. `write` thường chỉ ghi vào cache, muốn chắc chắn xuống đĩa phải `fsync` (database làm việc này khi commit).
- **Mô hình I/O**: *blocking* (gọi `read` thì luồng đứng chờ), *non-blocking* (trả về ngay nếu chưa có dữ liệu), *I/O multiplexing* (`select`/`poll`/`epoll`: một luồng theo dõi hàng nghìn socket). Go runtime dùng `epoll` (Linux) ở bên dưới, nên code Go viết kiểu blocking đơn giản mà vẫn phục vụ được rất nhiều kết nối.

### Boot và các khái niệm khác
- Khởi động: firmware (BIOS/UEFI) → bootloader (GRUB) → nạp kernel → kernel chạy process đầu tiên PID 1 (`systemd`) → systemd khởi động các service.
- **Signal**: thông báo bất đồng bộ gửi tới process. `SIGINT` (Ctrl+C), `SIGTERM` (yêu cầu dừng lịch sự, có thể bắt để dọn dẹp), `SIGKILL` (giết ngay, không bắt được). Service tốt phải bắt `SIGTERM` để **graceful shutdown**.
- **Environment variable**: cặp key=value truyền cho process, hay dùng để cấu hình service (12-factor app).

## Cách hoạt động
Điều gì xảy ra khi Go service gọi `os.ReadFile("config.yaml")`:

1. Code Go gọi hàm thư viện, runtime thực hiện system call `openat` → CPU chuyển sang kernel mode.
2. Kernel tra đường dẫn, tìm inode, kiểm tra quyền, cấp một file descriptor (ví dụ 3) và trả về user mode.
3. Gọi `read(3, buf, n)`: kernel xem dữ liệu có trong page cache chưa; chưa có thì yêu cầu driver đọc đĩa, luồng chuyển sang trạng thái *waiting*.
4. Đĩa đọc xong, phát **interrupt**; kernel copy dữ liệu vào buffer của process, luồng về *ready* rồi *running*.
5. Gọi `close(3)` để trả file descriptor. Quên đóng file/socket sẽ gây lỗi `too many open files` khi vượt giới hạn (`ulimit -n`).

## Ví dụ

Các lệnh Linux hay dùng khi vận hành backend:

```bash
ps aux | grep myservice      # liệt kê process
top / htop                   # CPU, RAM theo process
free -h                      # RAM, swap
df -h                        # dung lượng đĩa
du -sh /var/log/*            # thư mục nào chiếm nhiều chỗ
ss -tlnp                     # port đang listen, process nào giữ
lsof -p 1234                 # các file/socket process 1234 đang mở
kill -TERM 1234              # gửi SIGTERM
journalctl -u myservice -f   # xem log service systemd
tail -f app.log | grep ERROR # theo dõi log
chmod +x run.sh; chown app:app run.sh
```

Bắt tín hiệu để graceful shutdown trong Go:

```go
ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
defer stop()

srv := &http.Server{Addr: ":8080", Handler: mux}
go srv.ListenAndServe()

<-ctx.Done() // chờ SIGINT/SIGTERM
shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()
srv.Shutdown(shutdownCtx) // ngừng nhận request mới, chờ request đang xử lý xong
```

## Hiểu nhầm thường gặp
- **"Nhiều thread thì luôn nhanh hơn"**: với tác vụ CPU-bound, số thread vượt số core chỉ thêm chi phí context switch. Với I/O-bound thì nhiều luồng mới có lợi.
- **"Process và thread giống nhau"**: khác nhau ở chỗ có chia sẻ không gian địa chỉ hay không; đó là gốc của mọi khác biệt về chi phí, an toàn và cách giao tiếp.
- **"`write` xong là dữ liệu đã nằm trên đĩa"**: nó mới ở page cache, mất điện có thể mất. Cần `fsync`.
- **"Concurrency = parallelism"**: concurrency là cấu trúc chương trình xử lý nhiều việc xen kẽ; parallelism là thật sự chạy cùng lúc trên nhiều core.

## Câu hỏi

**Process khác thread thế nào?**
> - **Process**: một chương trình đang chạy, được OS cấp tài nguyên riêng: không gian địa chỉ (virtual memory), file descriptor, biến môi trường. Dùng để cô lập các chương trình với nhau.
> - **Thread**: luồng thực thi bên trong một process, là đơn vị mà OS lập lịch chạy trên CPU. Dùng để một chương trình làm nhiều việc cùng lúc.
>
> Quy tắc: process là đơn vị *sở hữu tài nguyên*, thread là đơn vị *thực thi*. Mọi thread trong cùng process dùng chung heap, biến toàn cục và file descriptor, nhưng mỗi thread có stack và thanh ghi riêng. Vì vậy tạo thread rẻ hơn tạo process, các thread trao đổi dữ liệu trực tiếp qua bộ nhớ chung, nhưng phải đồng bộ (mutex, channel) để tránh race condition.
>
> Ranh giới: process cô lập nên một process crash không kéo theo process khác; một thread làm hỏng bộ nhớ chung có thể làm sập cả process. Goroutine của Go không phải OS thread mà được runtime ghép lên một số ít thread, xem [09-concurrency.md](09-concurrency.md).

**System call là gì, ví dụ?**
> - **Kernel mode / user mode**: hai mức đặc quyền của CPU. Kernel chạy ở kernel mode, được chạm phần cứng; ứng dụng chạy ở user mode, bị hạn chế.
> - **System call**: cổng duy nhất để chương trình ở user mode nhờ kernel làm một việc đặc quyền.
>
> Mọi thao tác chạm tài nguyên dùng chung (file, mạng, tiến trình, bộ nhớ) đều phải đi qua system call: CPU chuyển sang kernel mode, kernel kiểm tra quyền, làm việc rồi trả kết quả. Ví dụ: `open`, `read`, `write`, `close` cho file; `socket`, `accept`, `connect` cho mạng; `fork`, `execve`, `exit` cho tiến trình; `mmap` cho bộ nhớ.
>
> Ranh giới: lập trình viên ít khi gọi trực tiếp; hàm thư viện như `os.ReadFile` hay `fmt.Println` gọi hộ. Mỗi lần chuyển mode tốn chi phí, nên đọc/ghi theo khối lớn (buffer) nhanh hơn nhiều lần gọi nhỏ. `strace` cho xem process đang gọi những system call nào.

**Virtual memory giải quyết gì?**
> - **Địa chỉ ảo**: địa chỉ mà chương trình nhìn thấy, không phải vị trí thật trên RAM.
> - **Page table**: bảng của OS (được MMU của CPU tra) ánh xạ từng trang ảo sang trang vật lý.
>
> Virtual memory cho mỗi process ảo giác có một không gian địa chỉ liền mạch, riêng của nó. Nhờ lớp ánh xạ này: process không đọc được bộ nhớ của nhau (cô lập); tổng bộ nhớ các process có thể lớn hơn RAM vì trang ít dùng được đẩy ra swap; nhiều process dùng chung một bản thư viện trên RAM; trang chỉ được cấp khi chạm tới lần đầu (lazy allocation).
>
> Ranh giới: truy cập trang không nằm trên RAM gây page fault; quá nhiều page fault ra đĩa (thrashing) làm máy chậm hẳn. Khi RAM và swap đều cạn, Linux kích hoạt OOM killer giết process.

**Stack và heap khác nhau?**
> - **Stack**: vùng nhớ của mỗi thread, cấp và thu theo lời gọi hàm (mỗi lời gọi đẩy một frame chứa biến cục bộ, tham số, địa chỉ trả về).
> - **Heap**: vùng nhớ cấp phát động, sống độc lập với lời gọi hàm, dùng cho dữ liệu cần tồn tại lâu hơn hàm tạo ra nó.
>
> Tiêu chí phân biệt là *vòng đời*: dữ liệu chết khi hàm return thì đặt trên stack (cấp/thu chỉ là dịch con trỏ stack, rất nhanh, nhưng kích thước giới hạn); dữ liệu sống tiếp thì đặt trên heap (chậm hơn, cần GC hoặc lập trình viên giải phóng).
>
> Ranh giới: trong Go lập trình viên không chọn; compiler làm *escape analysis*: biến bị tham chiếu sau khi hàm return (trả về con trỏ, gán vào biến toàn cục) sẽ "escape" lên heap. Đệ quy quá sâu làm tràn stack (stack overflow); goroutine có stack nhỏ tự giãn nên ít gặp hơn thread.

**Context switch là gì, vì sao tốn kém?**
> - **Scheduler**: thành phần của kernel quyết định thread nào được chạy trên CPU, trong bao lâu.
> - **Context switch**: việc CPU dừng thread đang chạy, lưu trạng thái của nó (thanh ghi, con trỏ lệnh, con trỏ stack) và nạp trạng thái của thread khác.
>
> Chi phí gồm phần trực tiếp (vào kernel, lưu/nạp thanh ghi) và phần gián tiếp lớn hơn: cache CPU và TLB đang chứa dữ liệu của thread cũ, thread mới chạy với cache "nguội" nên nhiều lần phải đọc RAM. Switch giữa hai process còn phải đổi page table, đắt hơn switch giữa hai thread cùng process.
>
> Ranh giới: switch xảy ra khi hết time slice, khi thread bị block (chờ I/O, chờ lock) hoặc khi có interrupt. Tạo hàng nghìn thread làm việc lặt vặt sẽ tốn thời gian vào switch; goroutine được runtime Go chuyển ở user space nên rẻ hơn nhiều.

**SIGTERM khác SIGKILL?**
> - **Signal**: thông báo bất đồng bộ kernel gửi tới process (vd do `kill`, Ctrl+C, hoặc do lỗi).
> - **SIGTERM (15)**: yêu cầu process kết thúc một cách lịch sự. **SIGKILL (9)**: lệnh kernel giết process ngay.
>
> Khác biệt cốt lõi: SIGTERM *bắt được*, nên process có thể dọn dẹp (ngừng nhận request mới, xử lý nốt request đang chạy, đóng kết nối DB, flush log) rồi mới thoát; SIGKILL *không bắt, không bỏ qua được*, process chết ngay, không dọn dẹp gì. Vì vậy `kill` mặc định gửi SIGTERM, Docker và Kubernetes gửi SIGTERM trước, đợi một khoảng (mặc định 30 giây trên Kubernetes) rồi mới SIGKILL.
>
> Ranh giới: graceful shutdown của service Go dựa vào việc bắt SIGTERM (`signal.NotifyContext`) rồi gọi `server.Shutdown`. Process bị OOM killer giết cũng nhận SIGKILL, nên không kịp ghi log gì.

**Deadlock là gì?**
> - **Lock (khóa)**: cơ chế cho một thread độc quyền dùng một tài nguyên; thread khác muốn dùng phải chờ.
> - **Deadlock**: tình trạng một nhóm thread chờ nhau vĩnh viễn, mỗi thread giữ một tài nguyên mà thread khác đang cần.
>
> Ví dụ kinh điển: thread A giữ khóa X và chờ khóa Y, thread B giữ Y và chờ X; cả hai không bao giờ chạy tiếp. Deadlock chỉ xảy ra khi đủ bốn điều kiện cùng lúc (mutual exclusion, hold and wait, no preemption, circular wait), nên phá một điều kiện là tránh được, cách phổ biến nhất là luôn lấy khóa theo cùng một thứ tự.
>
> Chi tiết bốn điều kiện và cách phát hiện trong Go: [09-concurrency.md](09-concurrency.md). Database cũng có deadlock giữa các transaction; DB tự phát hiện và hủy một bên, xem [10-databases.md](10-databases.md).

## Liên quan
- [02-backend-architecture.md](02-backend-architecture.md): service chạy trên OS giao tiếp qua mạng ra sao.
- [09-concurrency.md](09-concurrency.md): thread, goroutine, đồng bộ hóa.
- [../internet/README.md](../internet/README.md): nền tảng mạng (TCP/IP, DNS, HTTP).
