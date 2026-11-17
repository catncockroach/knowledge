# Linux for ops

> Gần như mọi server, container và node Kubernetes đều chạy Linux. File này gom những kiến thức Linux cơ sở mà người vận hành dùng hằng ngày: cấu trúc thư mục, user và permission, service với systemd, log, disk, package, SSH và shell script để tự động hoá.

## Tại sao cần biết
Khi một service chết lúc 2 giờ sáng, bạn SSH vào máy và phải trả lời được: process còn chạy không, log nói gì, disk có đầy không, file config có đúng quyền không. Container và Kubernetes cũng chỉ là các tính năng của Linux kernel được đóng gói lại ([04-containers-and-docker.md](04-containers-and-docker.md)). Không vững Linux thì gỡ lỗi container rất khó.

Phần khái niệm hệ điều hành (kernel, system call, process, thread, virtual memory, signal) đã có ở [../backend/01-operating-systems.md](../backend/01-operating-systems.md). File này đứng ở góc người quản trị máy. Chi tiết sâu hơn sẽ nằm ở một domain Linux riêng.

## Khái niệm cốt lõi

### Cấu trúc thư mục (FHS)
Linux có một cây thư mục duy nhất bắt đầu từ `/`. Ổ đĩa khác được gắn (mount) vào một nhánh của cây. Các thư mục ops hay dùng:

| Thư mục | Là gì | Dùng để |
|---|---|---|
| `/etc` | File cấu hình hệ thống | Sửa config service (`/etc/nginx/nginx.conf`, `/etc/ssh/sshd_config`) |
| `/var/log` | Log dạng file | Đọc log của các service ghi ra file |
| `/var/lib` | Dữ liệu trạng thái của service | Nơi database, Docker lưu dữ liệu (`/var/lib/docker`) |
| `/home`, `/root` | Thư mục của user, của root | File cá nhân, khoá SSH (`~/.ssh`) |
| `/usr/bin`, `/usr/local/bin` | Chương trình | Binary của hệ thống, của phần mềm tự cài |
| `/tmp` | File tạm | Có thể bị xoá khi reboot |
| `/proc`, `/sys` | File system ảo do kernel tạo | Đọc thông tin process, phần cứng (`/proc/cpuinfo`, `/proc/<pid>/`) |

### User, group và sudo
- **User** — **Là gì:** danh tính mà mọi process chạy dưới đó, có số UID. **Dùng để:** xác định process được đọc/ghi file nào. `root` (UID 0) có mọi quyền.
- **Group** — **Là gì:** nhóm user, có GID. **Dùng để:** cấp quyền cho nhiều user cùng lúc.
- **sudo** — **Là gì:** lệnh chạy một lệnh khác với quyền root (hoặc user khác) nếu được cho phép trong `/etc/sudoers`. **Dùng để:** đăng nhập bằng tài khoản thường, chỉ nâng quyền khi cần và có ghi log.
- **Service account** — **Là gì:** user không đăng nhập được, dành riêng cho một service (vd `nginx`, `postgres`). **Dùng để:** nếu service bị chiếm thì kẻ tấn công chỉ có quyền của user đó, không có quyền root.

### Permission
Mỗi file có một chủ sở hữu (owner), một group, và ba bộ quyền `rwx` cho owner, group và những người khác (others):

```
-rwxr-x---  1 deploy  app  1024  Jan 1 10:00  run.sh
│└┬┘└┬┘└┬┘     │       │
│ │  │  │      owner   group
│ │  │  └ others: --- (không có quyền gì)
│ │  └ group:  r-x (đọc, chạy)
│ └ owner:     rwx (đọc, ghi, chạy)
└ loại: - file, d thư mục, l symlink
```

| Ký hiệu | Số | Với file | Với thư mục |
|---|---|---|---|
| `r` | 4 | Đọc nội dung | Liệt kê tên file bên trong |
| `w` | 2 | Sửa nội dung | Tạo, xoá, đổi tên file bên trong |
| `x` | 1 | Chạy như chương trình | Đi vào (`cd`) và truy cập file bên trong |

Viết dạng số bằng cách cộng từng bộ: `rwxr-x---` = 7 5 0 = `750`. Lệnh: `chmod 750 run.sh`, `chown deploy:app run.sh`.

### Process và tài nguyên
- `ps aux`, `top`/`htop`: xem process, CPU, RAM.
- `kill <pid>` gửi `SIGTERM` (xin dừng, process được dọn dẹp). `kill -9 <pid>` gửi `SIGKILL` (kernel giết ngay, không dọn dẹp được).
- `free -h`: RAM. `uptime`: load average, tức số process đang chạy hoặc chờ CPU, trung bình trong 1, 5 và 15 phút.
- `ss -tlnp`: các port đang lắng nghe và process nào giữ port đó.

### systemd và service
- **systemd** — **Là gì:** chương trình init (PID 1) trên hầu hết bản phân phối Linux hiện đại. Nó khởi động hệ thống và quản lý service. **Dùng để:** chạy service lúc boot, tự restart khi service chết, quản lý thứ tự phụ thuộc giữa các service, gom log.
- **Unit** — **Là gì:** file khai báo một đối tượng systemd quản lý. Loại hay gặp là `.service` (một process chạy nền), ngoài ra có `.timer` (chạy theo lịch), `.socket`, `.mount`. **Dùng để:** mô tả cách chạy service theo kiểu khai báo (declarative), thay cho script khởi động tự viết.

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Go API
After=network-online.target

[Service]
User=myapp
ExecStart=/usr/local/bin/myapp --port 8080
Restart=on-failure
Environment=APP_ENV=production

[Install]
WantedBy=multi-user.target
```

| Lệnh | Ý nghĩa |
|---|---|
| `systemctl start/stop/restart myapp` | Chạy, dừng, khởi động lại ngay |
| `systemctl enable myapp` | Cho chạy tự động khi boot (khác với `start`) |
| `systemctl status myapp` | Trạng thái, PID, vài dòng log gần nhất |
| `systemctl daemon-reload` | Đọc lại file unit sau khi sửa |
| `journalctl -u myapp -f` | Xem log của service, `-f` để theo dõi log mới |

### Log
Có hai nơi log hay nằm: **journald** (log của systemd, đọc bằng `journalctl`) và file trong **`/var/log`** (vd `/var/log/nginx/error.log`). Đọc log bằng `tail -f`, `less`, lọc bằng `grep`. **logrotate** — **Là gì:** công cụ xoay vòng log theo lịch. **Dùng để:** nén file log cũ, xoá file quá hạn, để log không làm đầy disk.

### Disk
- `df -h`: dung lượng còn trống trên từng file system. `du -sh /var/log/*`: thư mục nào chiếm nhiều dung lượng.
- `df -i`: số **inode** còn lại. Inode là cấu trúc kernel dùng để mô tả mỗi file. Hết inode (do quá nhiều file nhỏ) thì không tạo được file mới, dù `df -h` vẫn báo còn chỗ.
- `lsblk`, `mount`: xem ổ đĩa và nơi chúng được gắn vào cây thư mục.

### Package manager
- **Là gì:** công cụ cài, gỡ và cập nhật phần mềm từ kho (repository) của bản phân phối: `apt` (Debian/Ubuntu), `dnf`/`yum` (RHEL/Fedora), `apk` (Alpine, hay dùng làm base image của container).
- **Dùng để:** cài phần mềm cùng các thư viện phụ thuộc, kiểm tra chữ ký gói, cập nhật bản vá bảo mật.

### SSH
- **Là gì:** giao thức đăng nhập và chạy lệnh từ xa qua kênh mã hoá (cổng mặc định 22).
- **Dùng để:** quản trị server từ xa, copy file (`scp`, `rsync`), làm kênh cho công cụ như Ansible ([07-terraform-and-iac.md](07-terraform-and-iac.md)).
- Đăng nhập bằng **cặp khoá** (key pair): private key giữ ở máy mình, public key đặt vào `~/.ssh/authorized_keys` trên server. Thường tắt đăng nhập bằng mật khẩu và tắt đăng nhập trực tiếp bằng root.

### Shell script
- **Là gì:** file chứa chuỗi lệnh shell (thường là Bash), chạy như một chương trình.
- **Dùng để:** tự động hoá việc lặp lại: backup, dọn log, kiểm tra sức khoẻ service, các bước trong pipeline CI.

Các khái niệm nền:
- **Shebang** `#!/usr/bin/env bash` ở dòng đầu: chọn chương trình thông dịch file.
- **Exit code**: mỗi lệnh trả về một số, `0` là thành công, khác `0` là lỗi. `$?` chứa exit code của lệnh vừa chạy. CI/CD dựa vào exit code để biết một bước pass hay fail.
- **Pipe** `|` nối stdout của lệnh trước vào stdin của lệnh sau. **Redirect**: `>` ghi đè vào file, `>>` ghi thêm, `2>&1` gộp stderr vào stdout.
- **`set -euo pipefail`**: dừng ngay khi một lệnh lỗi (`-e`), báo lỗi khi dùng biến chưa gán (`-u`), coi cả pipe là lỗi nếu một lệnh giữa pipe lỗi (`pipefail`). Bash mặc định *không* dừng khi một lệnh lỗi.
- **cron** — **Là gì:** dịch vụ chạy lệnh theo lịch. Lịch viết bằng 5 trường: phút, giờ, ngày trong tháng, tháng, thứ. `0 2 * * *` nghĩa là 2:00 mỗi ngày.

## Cách hoạt động
Luồng gỡ lỗi khi "service không chạy", đi từ ngoài vào trong:

```
1. Service có đang chạy không?      systemctl status myapp
2. Nếu chết, vì sao?                journalctl -u myapp -n 100
3. Có lắng nghe đúng port không?    ss -tlnp | grep 8080
4. Tài nguyên có cạn không?         df -h ; df -i ; free -h ; uptime
5. Quyền file config có đúng không? ls -l /etc/myapp/ ; id myapp
6. Mạng từ ngoài vào có thông không? curl -v localhost:8080/health
```

Mỗi bước loại bớt một nhóm nguyên nhân. Đây là cách debug có phương pháp ở [../backend/14-debugging.md](../backend/14-debugging.md), áp vào máy chủ.

## Ví dụ
Một script dọn log cũ, chạy hằng đêm bằng cron:

```bash
#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="/var/log/myapp"
DAYS=7

# Xoá file .log cũ hơn 7 ngày và in ra tên file đã xoá
find "$LOG_DIR" -name '*.log' -mtime +"$DAYS" -print -delete
echo "cleanup done at $(date -Is)"
```

Dòng crontab tương ứng: `30 3 * * * /usr/local/bin/cleanup-logs.sh >> /var/log/cleanup.log 2>&1`, tức chạy lúc 3:30 mỗi ngày và ghi cả stdout lẫn stderr vào file. Nếu `LOG_DIR` không tồn tại, `find` lỗi, `set -e` làm script dừng với exit code khác 0 và không in "cleanup done".

## Câu hỏi

**Quyền `755` hay `644` nghĩa là gì, và chọn quyền cho một file thế nào?**
> - **Permission bits**: ba bộ `rwx` cho owner, group, others. Mỗi bộ là một chữ số bằng tổng r=4, w=2, x=1.
> - **Owner/group**: user và group sở hữu file, đổi bằng `chown`.
>
> Mỗi chữ số là tổng các quyền của một nhóm: `755` = owner `rwx` (7), group và others `r-x` (5). `644` = owner `rw-`, còn lại `r--`. Quy tắc chọn là cấp ít nhất có thể (least privilege): file chương trình cần `x`, file config chứa bí mật chỉ owner được đọc (`600`), thư mục cần `x` để vào được.
>
> Ranh giới: `root` bỏ qua permission thông thường. Quyền của thư mục quyết định việc xoá file: có `w` trên thư mục là xoá được file bên trong, kể cả file mình không có quyền ghi.

**`systemctl start` khác `systemctl enable` thế nào?**
> - **systemd**: trình quản lý service (PID 1).
> - **start**: chạy service ngay bây giờ.
> - **enable**: tạo liên kết để service tự chạy ở những lần boot sau.
>
> `start`/`stop` thay đổi trạng thái hiện tại, còn `enable`/`disable` thay đổi hành vi lúc boot. Hai việc độc lập nhau: một service có thể đang chạy mà chưa enable (reboot là mất), hoặc đã enable mà đang dừng. Muốn làm cả hai một lúc: `systemctl enable --now myapp`.
>
> Ranh giới: sửa file unit xong phải chạy `systemctl daemon-reload` thì systemd mới đọc file mới. Chỉ `restart` thì vẫn chạy theo định nghĩa cũ.

**Log của một service nằm ở đâu?**
> - **journald**: thành phần của systemd, thu stdout/stderr của mọi service do systemd chạy.
> - **File log**: file service tự ghi, thường nằm trong `/var/log/<service>/`.
> - **Log của container**: stdout/stderr của container, do container runtime thu lại.
>
> Log nằm ở nơi process ghi ra. Service ghi ra stdout/stderr và chạy bằng systemd thì đọc bằng `journalctl -u <service>`. Service tự mở file thì xem config của nó (vd `error_log` của Nginx). Service chạy trong container thì đọc bằng `docker logs` hay `kubectl logs`. Trên hệ thống lớn, log từ mọi máy được gom về một nơi tập trung ([10-monitoring-and-observability.md](10-monitoring-and-observability.md)).
>
> Ranh giới: log trong container ghi vào file bên trong container sẽ mất khi container bị xoá, và `kubectl logs` không thấy. Đó là lý do ứng dụng trong container nên log ra stdout.

**Disk báo đầy dù đã xoá file log lớn, vì sao?**
> - **Inode và tên file**: tên file chỉ là một liên kết tới inode. Dữ liệu chỉ được giải phóng khi không còn tên nào *và* không còn process nào mở file.
> - **File descriptor**: số hiệu process dùng để giữ một file đang mở.
>
> Kernel chỉ giải phóng dung lượng khi file không còn tên trỏ tới và không còn process nào giữ nó mở. `rm` một file log mà service vẫn đang ghi thì chỉ xoá tên, dung lượng vẫn bị chiếm. Tìm bằng `lsof +L1`. Sửa bằng cách restart service, hoặc ngay từ đầu dùng `truncate -s 0 file.log` thay vì `rm`.
>
> Ranh giới: nếu `df -h` còn chỗ mà vẫn không tạo được file thì nguyên nhân có thể là hết inode (`df -i`), không phải hết dung lượng.

**Vì sao script bash nên có `set -euo pipefail`?**
> - **Exit code**: số mỗi lệnh trả về, 0 là thành công.
> - **`-e`, `-u`, `pipefail`**: dừng khi có lệnh lỗi, coi biến chưa gán là lỗi, và coi pipe là lỗi nếu một lệnh bất kỳ trong pipe lỗi.
>
> Bash mặc định chạy tiếp khi một lệnh lỗi, nên lỗi ở bước 2 có thể làm bước 5 phá hỏng dữ liệu. Các cờ này biến script thành "fail fast": dừng ở lỗi đầu tiên và trả exit code khác 0, để cron hay CI biết là đã hỏng. Ví dụ kinh điển: `rm -rf "$DIR/"*` với `DIR` chưa gán sẽ thành `rm -rf /*`. Có `-u` thì script dừng trước khi chạy dòng đó.
>
> Ranh giới: lệnh trong điều kiện `if`, hoặc lệnh đi với `||`, không kích hoạt `-e`. Lệnh được phép lỗi thì viết rõ, vd `cmd || true`.

## Hiểu nhầm thường gặp
- **"`kill -9` là cách dừng chuẩn."** `SIGKILL` không cho process đóng kết nối hay ghi nốt dữ liệu. Gửi `SIGTERM` trước, chỉ dùng `-9` khi process không phản hồi.
- **"Chạy service bằng root cho đỡ lỗi quyền."** Lỗi quyền là dấu hiệu cần cấp đúng quyền, không phải lý do để cấp mọi quyền. Service chạy bằng root bị chiếm thì cả máy bị chiếm.
- **"Load average 4 nghĩa là CPU quá tải."** Load average phải so với số CPU core. Load 4 trên máy 8 core là bình thường, trên máy 1 core là quá tải.

## Liên quan
- [../backend/01-operating-systems.md](../backend/01-operating-systems.md): kernel, process, thread, virtual memory, signal.
- [04-containers-and-docker.md](04-containers-and-docker.md): container dựa trên namespace và cgroup của Linux kernel.
- [03-networking-for-ops.md](03-networking-for-ops.md): mạng của máy Linux nhìn từ góc vận hành.
