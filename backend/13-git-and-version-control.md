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

## Câu hỏi và trả lời

**Git khác SVN?**
> - **Version control (quản lý phiên bản)**: hệ thống ghi lại lịch sử thay đổi của code, cho nhiều người làm chung và quay lại phiên bản cũ.
> - **Tập trung (SVN)**: một server giữ lịch sử; máy mỗi người chỉ có bản làm việc. **Phân tán (Git)**: mỗi bản clone chứa *toàn bộ* lịch sử.
>
> Mọi khác biệt đến từ việc lịch sử nằm ở đâu. Với Git, commit, xem log, tạo branch, so sánh phiên bản đều chạy cục bộ, nhanh và không cần mạng; mất server vẫn khôi phục được từ bất kỳ bản clone nào. Branch của Git chỉ là con trỏ tới một commit nên tạo và merge rất rẻ, khuyến khích mỗi việc một branch. Với SVN, gần như mọi thao tác cần server, và branch là bản copy thư mục.
>
> Ranh giới: SVN vẫn có điểm mạnh với file nhị phân lớn và phân quyền theo thư mục; Git xử lý file lớn bằng Git LFS. Trong thực tế team Git vẫn có một remote trung tâm (GitHub, GitLab), nhưng đó là quy ước, không phải giới hạn kỹ thuật.

**Ba vùng của Git? `git add` làm gì?**
> - **Working directory**: các file trên đĩa mà bạn đang sửa.
> - **Staging area (index)**: vùng soạn sẵn nội dung cho commit tiếp theo.
> - **Repository (`.git`)**: kho các commit đã lưu.
>
> Mỗi thay đổi đi qua ba vùng theo thứ tự: sửa file trong working directory → `git add` *chép ảnh chụp nội dung hiện tại* của file vào staging → `git commit` lưu toàn bộ staging thành một commit vĩnh viễn trong repository. Staging cho phép chọn chính xác thay đổi nào vào commit nào (`git add -p` chọn từng đoạn), để một commit chỉ chứa một ý.
>
> Ranh giới: `git add` chụp nội dung *tại thời điểm add*; sửa tiếp file sau đó thì phần sửa mới chưa được stage. `git status` cho biết file nào ở vùng nào; `git diff` so working với staging, `git diff --staged` so staging với commit cuối. `git restore --staged` đưa file ra khỏi staging mà không mất thay đổi.

**`git fetch` vs `git pull`?**
> - **Remote**: bản repository ở nơi khác (thường là `origin` trên GitHub).
> - **Remote-tracking branch**: bản sao cục bộ trạng thái branch của remote, vd `origin/main`.
>
> `git fetch` chỉ *tải* commit mới từ remote và cập nhật `origin/main`, không đụng branch đang làm hay file của bạn, nên luôn an toàn. `git pull` = `git fetch` + *tích hợp* vào branch hiện tại (mặc định là merge, hoặc rebase nếu cấu hình `pull.rebase` hay dùng `--rebase`). Vì vậy fetch trước để xem có gì mới (`git log HEAD..origin/main`) rồi mới quyết định cách tích hợp.
>
> Ranh giới: `pull` có thể sinh merge commit không mong muốn hoặc conflict ngay giữa lúc đang làm. Đặt `git config pull.ff only` để pull chỉ chạy khi không cần merge, còn lại phải tự quyết.

**Merge vs rebase? Khi nào không được rebase?**
> - **Merge**: kết hợp hai nhánh bằng một *merge commit* có hai cha; lịch sử giữ nguyên như đã xảy ra.
> - **Rebase**: *viết lại* các commit của nhánh bạn lên đỉnh nhánh đích, tạo commit mới (hash mới) với cùng thay đổi; lịch sử thành một đường thẳng.
>
> Tiêu chí: merge giữ *sự thật lịch sử* và không đổi commit đã có; rebase cho lịch sử *gọn, dễ đọc*, dễ `git bisect`, nhưng đổi hash các commit. Cách dùng phổ biến: rebase nhánh cá nhân lên `main` mới nhất trước khi mở PR; tích hợp vào `main` bằng merge (hoặc squash merge).
>
> Quy tắc vàng: *không rebase commit đã push lên nhánh người khác đang dùng chung* (vd `main`, `develop`). Rebase tạo commit mới thay cho commit cũ, người khác đã dựa trên commit cũ sẽ bị lịch sử lệch, phải sửa thủ công. Với nhánh của riêng mình đã push, rebase được nhưng phải `git push --force-with-lease` (an toàn hơn `--force` vì từ chối nếu remote có commit mới bạn chưa thấy).

**Xử lý conflict thế nào?**
> - **Conflict**: khi merge hoặc rebase, hai nhánh sửa *cùng một vùng* của cùng file theo hai cách khác nhau, Git không tự chọn được.
>
> Git dừng lại và đánh dấu vùng xung đột trong file:
>
> ```text
> <<<<<<< HEAD
> phiên bản của nhánh hiện tại
> =======
> phiên bản của nhánh đang đưa vào
> >>>>>>> feature/x
> ```
>
> Các bước: `git status` xem file nào conflict → mở từng file, hiểu *ý định* của cả hai bên rồi viết phiên bản đúng (có thể giữ một bên, cả hai, hoặc viết lại), xóa các dấu đánh dấu → build và chạy test → `git add` file đã giải → `git commit` (merge) hoặc `git rebase --continue`. Muốn bỏ cuộc thì `git merge --abort` / `git rebase --abort` để về trạng thái trước.
>
> Ranh giới: giải conflict là quyết định *nghiệp vụ*, không phải chọn bừa một bên; không chắc thì hỏi người viết bên kia. Không có conflict cú pháp không có nghĩa là đúng: hai thay đổi ở hai chỗ khác nhau vẫn có thể phá logic của nhau, nên luôn chạy test sau merge. Giảm conflict bằng cách merge/rebase từ `main` thường xuyên và giữ PR nhỏ.

**`reset` vs `revert`? `--soft`, `--mixed`, `--hard`?**
> - **`git revert`**: tạo một commit *mới* đảo ngược thay đổi của commit cũ; lịch sử chỉ thêm, không mất gì.
> - **`git reset`**: di chuyển con trỏ branch về commit khác, *bỏ* các commit phía sau khỏi branch.
>
> Tiêu chí chọn: commit *đã push* lên nhánh dùng chung thì dùng `revert`, vì không viết lại lịch sử người khác đang dựa vào. Commit *chỉ ở máy mình* thì `reset` được. Ba chế độ của reset khác nhau ở chỗ có đụng tới staging và working directory không:
>
> | | Con trỏ branch | Staging | Working directory |
> |---|---|---|---|
> | `--soft` | Lùi lại | Giữ (thay đổi vẫn staged) | Giữ |
> | `--mixed` (mặc định) | Lùi lại | Bỏ stage | Giữ |
> | `--hard` | Lùi lại | Bỏ | *Xóa* thay đổi |
>
> Ví dụ: gộp 3 commit cuối thành một thì `git reset --soft HEAD~3` rồi commit lại. Ranh giới: `--hard` xóa thay đổi chưa commit không lấy lại được; commit đã bị reset vẫn cứu được trong một thời gian qua `git reflog`.

**Quy trình làm việc với Git trong team? Git Flow là gì?**
> - **Branching strategy**: quy ước team dùng branch thế nào: branch nào tồn tại lâu, nhánh tính năng tách từ đâu, merge về đâu.
> - **Pull request (PR)**: yêu cầu merge một branch, là nơi review code và chạy CI trước khi vào nhánh chính.
>
> Quy trình phổ biến (GitHub Flow / trunk-based): `main` luôn deploy được; mỗi việc tạo branch ngắn hạn từ `main` → commit nhỏ, rõ nghĩa → push và mở PR → CI chạy test, đồng nghiệp review → merge vào `main` → deploy. Branch sống càng ngắn càng ít conflict.
>
> **Git Flow** là mô hình nhiều nhánh hơn: `main` chỉ chứa bản đã phát hành (có tag); `develop` là nhánh tích hợp; `feature/*` tách từ và merge về `develop`; `release/*` để chuẩn bị phát hành; `hotfix/*` tách từ `main` để vá gấp rồi merge về cả `main` và `develop`. Nó hợp với sản phẩm phát hành theo phiên bản (app mobile, phần mềm cài đặt); với web service deploy liên tục, nó thường bị coi là nặng nề, team chọn GitHub Flow hoặc trunk-based.
>
> Ranh giới: quy trình nào cũng cần commit message rõ ràng, nhánh chính được bảo vệ (không push thẳng, bắt buộc review và CI xanh).

**`git stash`, `cherry-pick` dùng khi nào?**
> - **`git stash`**: cất tạm các thay đổi chưa commit vào một ngăn xếp riêng, đưa working directory về sạch; `git stash pop` lấy lại.
> - **`git cherry-pick <commit>`**: áp *thay đổi của một commit cụ thể* từ nhánh khác vào nhánh hiện tại, tạo commit mới.
>
> Stash dùng khi đang làm dở mà phải chuyển việc gấp: cần sang nhánh khác sửa bug, cần pull mà thay đổi cục bộ chặn. Cherry-pick dùng khi cần *đúng một vài* commit chứ không cần cả nhánh: đưa bản vá từ `main` vào nhánh release cũ, cứu một commit từ nhánh sắp bỏ.
>
> Ranh giới: stash dễ bị quên, chồng nhiều stash khó nhớ cái nào là gì; việc dở dài hơn vài phút thì commit tạm trên branch riêng an toàn hơn. Cherry-pick tạo commit trùng nội dung khác hash, sau này merge hai nhánh có thể gây conflict hoặc lịch sử khó đọc; không dùng nó thay cho merge thường xuyên.

## Liên quan
- [08-clean-code-and-solid.md](08-clean-code-and-solid.md): code review qua pull request.
- [15-sdlc-agile-scrum.md](15-sdlc-agile-scrum.md): Git trong quy trình phát triển và CI/CD.
