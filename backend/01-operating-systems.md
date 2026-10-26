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

## Câu hỏi ôn tập
1. **Process khác thread thế nào?** Process có không gian địa chỉ riêng, thread chia sẻ bộ nhớ của process nhưng có stack riêng; tạo thread rẻ hơn, giao tiếp dễ hơn nhưng phải đồng bộ.
2. **System call là gì, ví dụ?** Cơ chế để ứng dụng yêu cầu kernel làm việc đặc quyền: `open`, `read`, `write`, `fork`, `socket`.
3. **Virtual memory giải quyết gì?** Cô lập process, cho mỗi process không gian địa chỉ riêng, cho phép dùng swap và chia sẻ thư viện.
4. **Stack và heap khác nhau?** Stack tự quản lý theo lời gọi hàm, nhanh, kích thước giới hạn; heap cấp phát động, do GC hoặc lập trình viên giải phóng.
5. **Context switch là gì, vì sao tốn kém?** Lưu trạng thái luồng cũ và nạp luồng mới; tốn thời gian lưu/nạp thanh ghi, làm nguội cache CPU.
6. **SIGTERM khác SIGKILL?** SIGTERM bắt được để dọn dẹp; SIGKILL không bắt được, process chết ngay.
7. **Deadlock là gì?** Xem [09-concurrency.md](09-concurrency.md).

## Liên quan
- [02-backend-architecture.md](02-backend-architecture.md): service chạy trên OS giao tiếp qua mạng ra sao.
- [09-concurrency.md](09-concurrency.md): thread, goroutine, đồng bộ hóa.
- [../internet/README.md](../internet/README.md): nền tảng mạng (TCP/IP, DNS, HTTP).
