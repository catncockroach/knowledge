# Git and version control

> Version control (quản lý phiên bản) lưu lại lịch sử mọi thay đổi của mã nguồn, cho phép nhiều người làm việc song song, quay lại phiên bản cũ và biết ai sửa gì, vì sao. Git là hệ thống phân tán phổ biến nhất; SVN là hệ thống tập trung đời trước.

## Tại sao cần biết
Ngày đầu đi làm, việc đầu tiên là clone repo, tạo branch, commit, push, tạo merge/pull request. Yêu cầu entry level: sử dụng Git/SVN ở mức cơ bản (commit, push, pull); mức thành thạo hơn là chia nhánh, merge theo quy trình của team. Interview hay hỏi: merge vs rebase, xử lý conflict, `git pull` làm gì, `reset` vs `revert`, quy trình branching.

## Khái niệm cốt lõi

### Tập trung và phân tán
| | Tập trung (SVN) | Phân tán (Git) |
|---|---|---|
| Kho lịch sử | Chỉ trên server | Mỗi máy có bản sao đầy đủ |
| Làm việc offline | Hạn chế (commit cần server) | Commit, xem log, tạo branch offline |
| Branch | Là bản copy thư mục, nặng | Chỉ là con trỏ, rất nhẹ |
| Lệnh tương ứng | `svn checkout`, `svn update`, `svn commit` (commit là gửi lên server luôn) | `git clone`, `git pull`, `git commit` + `git push` |

### Ba vùng của Git
```
Working directory ──git add──► Staging area (index) ──git commit──► Local repository ──git push──► Remote (origin)
        ▲                                                                   │
        └──────────────── git checkout / git restore ◄──────────────────────┘
                                         git fetch / git pull ◄── Remote
```
- **Working directory**: file bạn đang sửa.
- **Staging area**: những thay đổi đã chọn cho commit tiếp theo (cho phép commit một phần).
- **Repository** (`.git/`): lịch sử commit.
- **Remote**: kho trên server (GitHub, GitLab, Bitbucket), thường tên `origin`.

### Commit, branch, HEAD
- **Commit**: một ảnh chụp (snapshot) toàn bộ dự án, có mã hash SHA (vd `a1b2c3d`), tác giả, thời gian, message và con trỏ tới commit cha. Lịch sử là một đồ thị các commit.
- **Branch**: con trỏ di động trỏ tới một commit; commit mới thì con trỏ tiến lên. Tạo branch gần như không tốn gì.
- **HEAD**: con trỏ cho biết bạn đang đứng ở đâu (thường trỏ tới một branch). "Detached HEAD" là khi checkout thẳng một commit.
- **Tag**: nhãn cố định cho một commit, dùng đánh dấu phiên bản phát hành (`v1.2.0`).

### Lệnh cơ bản
```bash
git config --global user.name "Ten"; git config --global user.email "a@b.com"
git clone <url>                  # lấy repo về
git status                       # trạng thái file
git diff / git diff --staged     # xem thay đổi chưa stage / đã stage
git add file.go / git add -p     # stage file / chọn từng đoạn
git commit -m "feat: add login"  # tạo commit
git log --oneline --graph        # lịch sử
git push origin feature/login    # đẩy lên remote
git fetch                        # tải lịch sử mới về, KHÔNG đổi code đang làm
git pull                         # = fetch + merge (hoặc rebase nếu cấu hình)
```

### Branch và hợp nhất
```bash
git switch -c feature/login      # tạo và chuyển branch (cũ: git checkout -b)
git switch main
git merge feature/login          # hợp nhất vào main
git branch -d feature/login      # xóa branch đã merge
```

**Merge vs rebase**
```
Trước:            A───B───C  main
                       \
                        D───E  feature

git merge (đứng ở main):    A───B───C───────M  main      (M là merge commit có 2 cha)
                                 \         /
                                  D───E───┘

git rebase main (đứng ở feature):  A───B───C───D'───E'  feature   (D, E được "chép lại" lên đầu main)
```
| | Merge | Rebase |
|---|---|---|
| Lịch sử | Giữ nguyên, có merge commit | Thẳng, gọn |
| Viết lại lịch sử | Không | Có (tạo commit mới D', E') |
| An toàn trên branch chung | Có | **Không** rebase branch người khác đang dùng |

Quy tắc vàng: chỉ rebase những commit **chưa push** hoặc branch chỉ mình bạn dùng; với branch chung thì merge. **Fast-forward merge**: khi main không có commit mới, Git chỉ dịch con trỏ main tới đầu feature, không tạo merge commit. **Squash merge**: gộp mọi commit của branch thành một commit khi merge.

### Conflict
Xảy ra khi hai nhánh sửa **cùng vùng** của cùng file. Git đánh dấu:
```
<<<<<<< HEAD
timeout := 5 * time.Second
=======
timeout := 10 * time.Second
>>>>>>> feature/config
```
Cách xử lý: đọc hiểu cả hai thay đổi (hỏi người viết nếu cần), sửa file về kết quả đúng, xóa dấu đánh dấu, `git add`, rồi `git commit` (khi merge) hoặc `git rebase --continue`. Build và chạy test lại sau khi giải quyết. Hủy giữa chừng: `git merge --abort` / `git rebase --abort`. Giảm conflict bằng cách cập nhật từ main thường xuyên và giữ PR nhỏ.

### Hoàn tác
| Tình huống | Lệnh |
|---|---|
| Bỏ thay đổi chưa stage của một file | `git restore file.go` |
| Bỏ stage | `git restore --staged file.go` |
| Sửa commit cuối (chưa push) | `git commit --amend` |
| Bỏ commit cuối, giữ thay đổi trong working dir | `git reset --soft HEAD~1` (giữ ở staging) / `git reset HEAD~1` |
| Bỏ hẳn commit và thay đổi (nguy hiểm) | `git reset --hard HEAD~1` |
| Hoàn tác một commit **đã push** | `git revert <sha>`: tạo commit mới đảo ngược, không viết lại lịch sử |
| Cất tạm thay đổi để chuyển nhánh | `git stash` / `git stash pop` |
| Lấy một commit từ nhánh khác | `git cherry-pick <sha>` |
| Tìm lại commit "mất" | `git reflog` |

`reset` viết lại lịch sử (dùng cho commit local); `revert` an toàn cho lịch sử đã chia sẻ. Tránh `git push --force` lên branch chung; nếu bắt buộc thì dùng `--force-with-lease`.

### .gitignore
Liệt kê file không đưa vào Git: binary build, thư mục `vendor/` (tùy dự án), file IDE, `.env`, log, file chứa secret.
```
/bin/
*.log
.env
.idea/
.vscode/
coverage.out
```

## Cách hoạt động
Quy trình làm việc phổ biến trong team (feature branch + merge request/pull request):
1. Cập nhật main: `git switch main && git pull`.
2. Tạo branch theo quy ước: `feature/PROJ-123-login`, `bugfix/...`, `hotfix/...`.
3. Code, commit nhỏ và có ý nghĩa; message rõ ràng (nhiều team dùng **Conventional Commits**: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`).
4. Cập nhật từ main định kỳ (merge hoặc rebase tùy quy ước) để giảm conflict.
5. Push và tạo **Merge Request** (GitLab) / **Pull Request** (GitHub): mô tả thay đổi, liên kết ticket.
6. **CI** chạy build, lint, test; reviewer đọc và góp ý; sửa theo góp ý.
7. Được duyệt và CI xanh thì merge (merge commit, squash hoặc rebase theo quy ước), xóa branch.
8. CD triển khai lên môi trường dev/staging/production.

Các mô hình branching:
- **Git Flow**: `main` (bản phát hành), `develop` (tích hợp), `feature/*`, `release/*`, `hotfix/*`. Chặt chẽ, hợp với phát hành theo phiên bản định kỳ.
- **GitHub Flow**: chỉ `main` luôn deploy được + feature branch ngắn hạn + PR. Đơn giản, hợp deploy liên tục.
- **Trunk-based development**: mọi người tích hợp vào trunk (main) rất thường xuyên, branch sống rất ngắn, dùng feature flag để ẩn tính năng chưa xong.

## Ví dụ
Quên tạo branch và đã commit vào main local (chưa push):
```bash
git switch -c feature/fix-timeout    # tạo branch tại commit hiện tại, mang theo commit
git switch main
git reset --hard origin/main          # đưa main local về như remote
```

Commit lỡ chứa file `.env` (chưa push): `git rm --cached .env`, thêm vào `.gitignore`, `git commit --amend`. Nếu **đã push**: coi secret đã lộ, thu hồi và tạo secret mới ngay.

Tìm commit gây bug bằng tìm kiếm nhị phân:
```bash
git bisect start
git bisect bad              # commit hiện tại lỗi
git bisect good v1.4.0      # phiên bản này còn tốt
# Git checkout commit ở giữa; chạy test rồi báo git bisect good/bad cho tới khi tìm ra
git bisect reset
```

## Hiểu nhầm thường gặp
- **"`git pull` và `git fetch` như nhau"**: fetch chỉ tải về; pull còn hợp nhất vào branch hiện tại.
- **"Commit là đã lưu lên server"**: Git commit chỉ ở local; phải `push`.
- **"Rebase lúc nào cũng tốt vì lịch sử đẹp"**: rebase branch đã chia sẻ làm lệch lịch sử của người khác.
- **"Xóa file khỏi commit mới nhất là secret không còn"**: nó vẫn trong lịch sử và trong bản clone của người khác.

## Câu hỏi ôn tập
1. **Git khác SVN?** Phân tán vs tập trung.
2. **Ba vùng của Git? `git add` làm gì?**
3. **`git fetch` vs `git pull`?**
4. **Merge vs rebase? Khi nào không được rebase?**
5. **Xử lý conflict thế nào?**
6. **`reset` vs `revert`? `--soft`, `--mixed`, `--hard`?**
7. **Quy trình làm việc với Git trong team? Git Flow là gì?**
8. **`git stash`, `cherry-pick` dùng khi nào?**

## Liên quan
- [08-clean-code-and-solid.md](08-clean-code-and-solid.md): code review qua pull request.
- [15-sdlc-agile-scrum.md](15-sdlc-agile-scrum.md): Git trong quy trình phát triển và CI/CD.
