# Databases

> Database là nơi lưu trữ dữ liệu bền vững và cho phép truy vấn hiệu quả, an toàn khi nhiều người cùng đọc ghi. Backend gần như luôn xoay quanh một database: SQL (quan hệ) cho dữ liệu có cấu trúc và cần nhất quán, NoSQL cho các nhu cầu riêng về quy mô, tốc độ hay mô hình dữ liệu.

## Tại sao cần biết
Phần lớn bug hiệu năng và bug dữ liệu của backend nằm ở tầng DB: thiếu index, truy vấn N+1, transaction sai, race condition khi cập nhật số dư. Yêu cầu entry level: kiến thức cơ bản về SQL và NoSQL. Interview hay hỏi: viết câu JOIN/GROUP BY, ACID, isolation level, index hoạt động thế nào, khi nào index không được dùng, SQL vs NoSQL, normalization.

## Khái niệm cốt lõi

### Mô hình quan hệ
- Dữ liệu tổ chức thành **bảng** (table/relation): **hàng** (row/record) là một thực thể, **cột** (column/field) là thuộc tính có kiểu.
- **Primary key (PK)**: định danh duy nhất mỗi hàng, không null. **Foreign key (FK)**: cột tham chiếu PK của bảng khác, đảm bảo **toàn vẹn tham chiếu** (không có đơn hàng trỏ tới user không tồn tại).
- **Constraint**: `NOT NULL`, `UNIQUE`, `CHECK (price >= 0)`, `DEFAULT`. Đặt ràng buộc ở DB là lớp bảo vệ cuối cùng cho dữ liệu đúng.
- Quan hệ: **1-1**, **1-n** (một user nhiều đơn: FK ở bảng đơn), **n-n** (sinh viên – môn học: cần bảng trung gian).
- Hệ quản trị phổ biến: PostgreSQL, MySQL/MariaDB, Oracle, SQL Server, SQLite.

```sql
CREATE TABLE users (
    id         BIGSERIAL PRIMARY KEY,
    email      VARCHAR(255) NOT NULL UNIQUE,
    name       VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES users(id),
    total      BIGINT NOT NULL CHECK (total >= 0),  -- tiền lưu số nguyên
    status     VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### SQL căn bản
| Nhóm | Lệnh |
|---|---|
| DDL (định nghĩa) | `CREATE`, `ALTER`, `DROP`, `TRUNCATE` |
| DML (thao tác) | `SELECT`, `INSERT`, `UPDATE`, `DELETE` |
| DCL (quyền) | `GRANT`, `REVOKE` |
| TCL (transaction) | `BEGIN`, `COMMIT`, `ROLLBACK`, `SAVEPOINT` |

```sql
-- Lọc, sắp xếp, phân trang
SELECT id, name FROM users WHERE created_at >= '2026-01-01' ORDER BY id LIMIT 20 OFFSET 40;

-- Gom nhóm: tổng chi tiêu mỗi user, chỉ lấy user chi trên 1 triệu
SELECT user_id, COUNT(*) AS orders, SUM(total) AS spent
FROM orders
WHERE status = 'paid'
GROUP BY user_id
HAVING SUM(total) > 1000000
ORDER BY spent DESC;
```
- `WHERE` lọc **hàng trước** khi gom nhóm; `HAVING` lọc **nhóm sau** khi gom.
- Thứ tự thực thi logic: `FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT`. Vì thế không dùng alias của `SELECT` trong `WHERE` được.
- Hàm tổng hợp: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`. `COUNT(*)` đếm mọi hàng, `COUNT(col)` bỏ qua NULL.
- `NULL` là "không biết": `NULL = NULL` không phải true; dùng `IS NULL`.

### JOIN
```
users                 orders
id | name             id | user_id | total
1  | An               10 | 1       | 500
2  | Bình             11 | 1       | 300
3  | Chi              12 | 9       | 100   (user 9 không tồn tại, nếu không có FK)
```
| Loại | Kết quả |
|---|---|
| `INNER JOIN` | Chỉ các cặp khớp ở cả hai bảng: An–10, An–11 |
| `LEFT JOIN` | Mọi hàng bảng trái + phần khớp bên phải (NULL nếu không khớp): An–10, An–11, Bình–NULL, Chi–NULL |
| `RIGHT JOIN` | Ngược lại: mọi hàng bảng phải |
| `FULL OUTER JOIN` | Mọi hàng cả hai bên |
| `CROSS JOIN` | Tích Descartes: mọi tổ hợp |
| Self join | Bảng join với chính nó (nhân viên – quản lý) |

```sql
-- User chưa từng đặt hàng
SELECT u.id, u.name
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE o.id IS NULL;
```
Subquery và CTE (`WITH ... AS`) giúp chia truy vấn phức tạp thành bước. **Window function** (`ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)`) tính toán theo nhóm mà không gộp hàng, ví dụ lấy đơn mới nhất của mỗi user.

### Normalization
Chuẩn hóa là tách bảng để **giảm dư thừa** và tránh **dị thường** khi cập nhật (sửa địa chỉ khách ở 100 dòng đơn hàng, quên một dòng).
- **1NF**: mỗi ô một giá trị nguyên tử (không lưu `"tag1,tag2"` trong một cột), không nhóm lặp.
- **2NF**: 1NF + mọi cột không khóa phụ thuộc **toàn bộ** khóa chính (quan trọng khi khóa gồm nhiều cột).
- **3NF**: 2NF + không có phụ thuộc **bắc cầu** (cột không khóa phụ thuộc cột không khóa khác; ví dụ lưu cả `zip_code` và `city` khi city suy ra từ zip).
- **Denormalization**: cố ý lặp dữ liệu để đọc nhanh (bớt JOIN), đánh đổi với độ phức tạp khi ghi. Hay gặp ở hệ thống báo cáo, đọc nhiều.

### Index
- Không có index, tìm `WHERE email = 'a@x.com'` phải quét toàn bảng (**full table scan**, O(n)).
- Index là cấu trúc dữ liệu phụ (thường **B+ tree**) lưu giá trị cột đã sắp xếp kèm con trỏ tới hàng → tìm O(log n), hỗ trợ cả `=`, `<`, `>`, `BETWEEN`, `ORDER BY`, tiền tố `LIKE 'abc%'`.
```
B+ tree index trên email
                 [ m ]
              /         \
       [ d | h ]        [ r | w ]
      /    |    \       /   |   \
   lá: a..c  d..g  h..l  m..q  r..v  w..z  → các lá nối nhau thành danh sách (quét khoảng nhanh)
```
- **Primary key** tự có index. Trong MySQL InnoDB, bảng được lưu sắp xếp theo PK (**clustered index**); index khác (**secondary**) lưu giá trị PK để tra ngược lại.
- **Composite index** `(user_id, created_at)`: dùng được cho `WHERE user_id = ?` và `WHERE user_id = ? AND created_at > ?`, **không** dùng hiệu quả cho chỉ `WHERE created_at > ?` (quy tắc **leftmost prefix**: như danh bạ sắp theo họ rồi tên, không tra nhanh theo tên được).
- **Covering index**: index chứa đủ mọi cột truy vấn cần → không phải đọc bảng.
- **Chi phí**: index tốn dung lượng và làm chậm `INSERT/UPDATE/DELETE` (phải cập nhật index). Chỉ index cột hay dùng để lọc/join/sort và có độ chọn lọc cao (cột giới tính 2 giá trị thì index ít tác dụng).
- **Index bị bỏ qua** khi: dùng hàm trên cột (`WHERE LOWER(email) = ...`, `WHERE DATE(created_at) = ...`), `LIKE '%abc'`, so sánh khác kiểu gây ép kiểu ngầm, không theo leftmost prefix, hoặc optimizer thấy quét bảng rẻ hơn.
- Xem kế hoạch thực thi bằng `EXPLAIN` / `EXPLAIN ANALYZE`: thấy "Seq Scan"/"type: ALL" trên bảng lớn là dấu hiệu thiếu index.

### Transaction và ACID
Transaction là nhóm thao tác được xử lý như **một đơn vị**: hoặc tất cả thành công, hoặc không gì cả.
| Tính chất | Ý nghĩa | Ví dụ chuyển tiền A → B |
|---|---|---|
| **Atomicity** | Tất cả hoặc không gì | Trừ A mà lỗi trước khi cộng B → rollback cả hai |
| **Consistency** | Đưa DB từ trạng thái hợp lệ sang trạng thái hợp lệ (thỏa constraint) | Số dư không âm; tổng tiền không đổi |
| **Isolation** | Các transaction đồng thời không thấy trạng thái dở dang của nhau | Người khác không thấy lúc A đã trừ mà B chưa cộng |
| **Durability** | Đã commit thì không mất, kể cả khi sập nguồn | Ghi WAL/redo log xuống đĩa trước khi báo commit |

### Isolation level và các hiện tượng
Hiện tượng khi các transaction chạy đồng thời:
- **Dirty read**: đọc dữ liệu transaction khác chưa commit (rồi nó rollback).
- **Non-repeatable read**: đọc cùng một hàng hai lần trong một transaction, ra giá trị khác vì transaction khác đã sửa và commit.
- **Phantom read**: chạy cùng một truy vấn khoảng hai lần, xuất hiện/mất hàng vì transaction khác đã chèn/xóa.
- **Lost update**: hai transaction cùng đọc rồi cùng ghi, một bản cập nhật bị đè.

| Isolation level | Dirty read | Non-repeatable read | Phantom read |
|---|---|---|---|
| Read Uncommitted | Có thể | Có thể | Có thể |
| Read Committed | Không | Có thể | Có thể |
| Repeatable Read | Không | Không | Có thể (theo chuẩn SQL) |
| Serializable | Không | Không | Không |

Level càng cao càng an toàn nhưng càng giảm khả năng chạy đồng thời. Mặc định: PostgreSQL là Read Committed, MySQL InnoDB là Repeatable Read. Các DB hiện đại dùng **MVCC** (multi-version concurrency control): giữ nhiều phiên bản của hàng để người đọc không chặn người ghi.

### Lock: pessimistic và optimistic
Bài toán: hai request cùng trừ tồn kho/số dư.
- **Pessimistic locking**: khóa hàng trước khi sửa, người khác phải chờ.
```sql
BEGIN;
SELECT balance FROM accounts WHERE id = 1 FOR UPDATE; -- khóa hàng
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;
```
- **Optimistic locking**: không khóa; thêm cột `version`, chỉ cập nhật nếu version chưa đổi, nếu 0 hàng bị ảnh hưởng thì có người sửa trước → đọc lại và thử lại.
```sql
UPDATE products SET stock = stock - 1, version = version + 1
WHERE id = 42 AND version = 7;
```
- Cách đơn giản và nguyên tử nhất khi được: `UPDATE products SET stock = stock - 1 WHERE id = 42 AND stock > 0;` rồi kiểm tra số hàng bị ảnh hưởng.
- Pessimistic hợp khi xung đột thường xuyên; optimistic hợp khi xung đột hiếm.

### NoSQL
"Not only SQL": các DB không theo mô hình bảng quan hệ, thường đánh đổi một phần tính nhất quán/khả năng JOIN để lấy khả năng mở rộng ngang, tốc độ hoặc schema linh hoạt.
| Loại | Mô hình | Ví dụ | Hợp cho |
|---|---|---|---|
| Key-value | key → value | Redis, Memcached, DynamoDB | Cache, session, counter, rate limit |
| Document | Tài liệu JSON/BSON lồng nhau | MongoDB, Couchbase | Dữ liệu schema linh hoạt, đọc cả object một lần |
| Wide-column | Hàng có cột động, phân tán theo partition key | Cassandra, HBase, ScyllaDB | Ghi rất nhiều, time-series, log |
| Graph | Đỉnh và cạnh | Neo4j | Quan hệ phức tạp: mạng xã hội, gợi ý |
| Search | Inverted index | Elasticsearch, OpenSearch | Tìm kiếm full-text, log |

**SQL vs NoSQL**
| | SQL | NoSQL |
|---|---|---|
| Schema | Cố định, định nghĩa trước | Linh hoạt |
| Quan hệ | JOIN mạnh, FK | Thường nhúng dữ liệu, hạn chế JOIN |
| Nhất quán | ACID mạnh | Nhiều hệ chọn eventual consistency (BASE), một số hỗ trợ transaction |
| Mở rộng | Chủ yếu dọc; ngang cần replication/sharding | Thiết kế để mở rộng ngang |
| Truy vấn | SQL chuẩn | API/ngôn ngữ riêng |
| Chọn khi | Dữ liệu có quan hệ, cần nhất quán (tài chính, đơn hàng) | Quy mô lớn, schema thay đổi, truy cập theo key đơn giản |

**CAP theorem**: trong hệ phân tán, khi xảy ra **phân mảnh mạng** (Partition), phải chọn giữa **Consistency** (mọi node trả dữ liệu mới nhất) và **Availability** (mọi request đều được trả lời). Hệ CP từ chối phục vụ để giữ nhất quán; hệ AP vẫn phục vụ nhưng có thể trả dữ liệu cũ. **Eventual consistency**: nếu ngừng ghi, các bản sao cuối cùng sẽ giống nhau.

### Mở rộng database (sơ lược)
- **Replication**: một primary nhận ghi, nhiều replica nhận bản sao để đọc. Chú ý **replication lag**: vừa ghi xong đọc từ replica có thể chưa thấy.
- **Sharding/partitioning**: chia dữ liệu theo khóa (user_id) sang nhiều máy/phân vùng.
- **Cache** trước DB (Redis), pattern **cache-aside**: đọc cache → miss thì đọc DB rồi ghi cache; khi cập nhật DB thì xóa cache.

## Cách hoạt động
Luồng một câu truy vấn trong DB quan hệ:
1. **Parse**: kiểm tra cú pháp, tạo cây truy vấn.
2. **Optimize**: optimizer ước lượng chi phí các cách thực thi (dùng index nào, thứ tự JOIN, nested loop hay hash join) dựa trên thống kê dữ liệu, chọn kế hoạch rẻ nhất.
3. **Execute**: đọc page dữ liệu từ buffer pool (RAM) hoặc đĩa, áp dụng lọc, join, sort.
4. Với lệnh ghi: ghi thay đổi vào **WAL** (write-ahead log) và `fsync` trước khi báo commit (durability), dữ liệu bảng được ghi xuống đĩa sau.

Dùng DB trong Go với `database/sql`:
```go
// Truy vấn một hàng: luôn dùng placeholder, không nối chuỗi
var u User
err := db.QueryRowContext(ctx,
    "SELECT id, email, name FROM users WHERE id = $1", id).
    Scan(&u.ID, &u.Email, &u.Name)
if errors.Is(err, sql.ErrNoRows) {
    return User{}, ErrNotFound
}

// Nhiều hàng: nhớ Close và kiểm tra rows.Err()
rows, err := db.QueryContext(ctx, "SELECT id, total FROM orders WHERE user_id = $1", userID)
if err != nil {
    return nil, err
}
defer rows.Close()
for rows.Next() {
    var o Order
    if err := rows.Scan(&o.ID, &o.Total); err != nil {
        return nil, err
    }
    list = append(list, o)
}
return list, rows.Err()
```

Transaction:
```go
func Transfer(ctx context.Context, db *sql.DB, from, to, amount int64) error {
    tx, err := db.BeginTx(ctx, nil)
    if err != nil {
        return err
    }
    defer tx.Rollback() // không có tác dụng nếu đã Commit

    res, err := tx.ExecContext(ctx,
        "UPDATE accounts SET balance = balance - $1 WHERE id = $2 AND balance >= $1", amount, from)
    if err != nil {
        return err
    }
    if n, _ := res.RowsAffected(); n == 0 {
        return errors.New("insufficient balance")
    }
    if _, err := tx.ExecContext(ctx,
        "UPDATE accounts SET balance = balance + $1 WHERE id = $2", amount, to); err != nil {
        return err
    }
    return tx.Commit()
}
```
Placeholder là `$1` với PostgreSQL, `?` với MySQL. Thư viện hay dùng thêm: `sqlx`, `pgx`, `sqlc` (sinh code Go từ SQL), ORM `GORM`. Thay đổi schema quản lý bằng **migration** có version (golang-migrate, goose), chạy tự động khi deploy.

## Ví dụ
**Vấn đề N+1 query**:
```go
orders := getOrders()            // 1 query
for _, o := range orders {       // N query
    o.User = getUser(o.UserID)
}
```
100 đơn hàng = 101 lần round-trip tới DB. Sửa: một câu JOIN, hoặc gom ID rồi `WHERE id IN (...)` / `= ANY($1)`.

**Phân trang**: `OFFSET 100000 LIMIT 20` buộc DB đọc và bỏ 100.000 hàng. **Keyset pagination** nhanh hơn: `WHERE id > :last_seen_id ORDER BY id LIMIT 20` (dùng index trên id).

**Chọn index cho truy vấn**: `SELECT * FROM orders WHERE user_id = ? AND status = 'paid' ORDER BY created_at DESC LIMIT 10` → index `(user_id, status, created_at)` cho phép tìm đúng nhóm và lấy sẵn theo thứ tự, không cần sort.

## Hiểu nhầm thường gặp
- **"Thêm index là luôn nhanh hơn"**: index làm chậm ghi, tốn bộ nhớ, và không được dùng nếu truy vấn không phù hợp (hàm trên cột, sai thứ tự cột composite).
- **"NoSQL nhanh hơn SQL"**: nhanh hơn cho mô hình truy cập nó được thiết kế; truy vấn quan hệ phức tạp thì SQL tốt hơn. Chọn theo bài toán.
- **"Transaction là xong mọi race condition"**: ở Read Committed vẫn có lost update nếu đọc rồi ghi ở hai câu riêng; cần `FOR UPDATE`, optimistic locking hoặc update nguyên tử.
- **"`DELETE` và `TRUNCATE` như nhau"**: `TRUNCATE` xóa toàn bộ nhanh, không chạy từng hàng, thường không lọc được bằng `WHERE` và có hành vi khác về trigger/rollback tùy DB.

## Câu hỏi

**ACID là gì? Cho ví dụ.**
> - **Transaction**: nhóm thao tác DB được xử lý như *một đơn vị*: hoặc tất cả thành công, hoặc như chưa có gì xảy ra.
> - **ACID**: bốn đảm bảo của transaction: Atomicity, Consistency, Isolation, Durability.
>
> Ví dụ chuyển 100k từ tài khoản A sang B (trừ A, cộng B):
> - **Atomicity (nguyên tử)**: cả hai lệnh cùng thành công hoặc cùng bị hủy; không có chuyện trừ A mà không cộng B.
> - **Consistency (nhất quán)**: transaction đưa DB từ trạng thái hợp lệ sang trạng thái hợp lệ, mọi ràng buộc (`CHECK balance >= 0`, khóa ngoại) đều giữ.
> - **Isolation (cô lập)**: transaction chạy đồng thời không thấy trạng thái dở dang của nhau; mức độ cô lập điều chỉnh bằng isolation level.
> - **Durability (bền vững)**: đã commit thì dữ liệu còn kể cả khi mất điện ngay sau đó, nhờ ghi write-ahead log xuống đĩa trước khi báo commit.
>
> Ranh giới: Consistency một phần do DB đảm bảo (ràng buộc), phần còn lại do logic ứng dụng. Isolation thực tế thường không tuyệt đối vì mặc định không phải Serializable. Nhiều NoSQL đánh đổi một phần ACID lấy khả năng mở rộng.

**Các isolation level và hiện tượng tương ứng? Mặc định của PostgreSQL/MySQL?**
> - **Isolation level**: mức độ một transaction bị cô lập khỏi thay đổi của các transaction chạy đồng thời.
> - **Dirty read**: đọc dữ liệu chưa commit. **Non-repeatable read**: đọc lại một hàng ra giá trị khác. **Phantom read**: chạy lại truy vấn khoảng thấy hàng mới xuất hiện hoặc biến mất.
>
> Quy tắc: level càng cao chặn càng nhiều hiện tượng nhưng càng giảm khả năng chạy đồng thời. Read Uncommitted chặn không gì; Read Committed chặn dirty read; Repeatable Read chặn thêm non-repeatable read; Serializable chặn tất cả, kết quả như các transaction chạy lần lượt. Bảng đầy đủ ở phần *Isolation level và các hiện tượng*. Mặc định: PostgreSQL là **Read Committed**, MySQL InnoDB là **Repeatable Read**.
>
> Ranh giới: chuẩn SQL chỉ quy định hiện tượng *tối thiểu* phải chặn, DB thực tế có thể chặn nhiều hơn: Repeatable Read của PostgreSQL (snapshot isolation) không có phantom read, InnoDB giảm phantom bằng gap lock. Lost update không nằm trong bảng chuẩn nhưng là lỗi hay gặp nhất ở Read Committed, phải xử lý bằng lock (xem câu về locking).

**Index hoạt động thế nào? Khi nào không dùng được? Composite index và leftmost prefix?**
> - **Index**: cấu trúc dữ liệu phụ (thường là B+ tree) lưu giá trị cột đã sắp xếp kèm vị trí hàng, giúp DB tìm hàng mà không quét cả bảng.
> - **Composite index**: index trên nhiều cột theo thứ tự, vd `(user_id, created_at)`.
> - **Leftmost prefix**: composite index chỉ dùng được khi truy vấn lọc theo các cột *từ trái sang*.
>
> Index biến tìm kiếm O(n) thành O(log n) nhờ dữ liệu đã sắp xếp, xem [05-data-structures.md](05-data-structures.md). Composite index sắp theo cột đầu, trong cùng giá trị cột đầu mới sắp theo cột hai, giống danh bạ sắp theo họ rồi tên. Vì vậy index `(user_id, created_at)` phục vụ `WHERE user_id = ?` và `WHERE user_id = ? AND created_at > ?`, nhưng không phục vụ `WHERE created_at > ?` một mình.
>
> Index không được dùng khi: áp hàm hay phép tính lên cột (`WHERE LOWER(email) = ?`, `WHERE YEAR(created_at) = 2026`); `LIKE '%abc'` bắt đầu bằng wildcard; so sánh khác kiểu gây ép kiểu ngầm; bỏ qua cột đầu của composite index; hoặc optimizer ước tính truy vấn trả về phần lớn bảng nên quét cả bảng rẻ hơn. Kiểm tra bằng `EXPLAIN`. Ranh giới: index tăng tốc đọc nhưng làm chậm ghi và tốn dung lượng, vì mỗi `INSERT`/`UPDATE` phải cập nhật mọi index liên quan.

**INNER JOIN vs LEFT JOIN? WHERE vs HAVING?**
> - **JOIN**: ghép hàng của hai bảng theo điều kiện, vd `orders.user_id = users.id`.
> - **WHERE / HAVING**: hai mệnh đề lọc ở hai thời điểm khác nhau của truy vấn.
>
> JOIN khác nhau ở *hàng không khớp*: `INNER JOIN` chỉ giữ hàng khớp ở cả hai bảng; `LEFT JOIN` giữ mọi hàng của bảng trái, phía phải không khớp thì điền `NULL`. Ví dụ liệt kê *mọi* user kèm số đơn, kể cả user chưa có đơn, phải dùng LEFT JOIN.
>
> WHERE và HAVING khác nhau ở *thời điểm lọc*: thứ tự logic là `FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT`. `WHERE` lọc *từng hàng trước* khi gom nhóm, nên không dùng được hàm tổng hợp; `HAVING` lọc *nhóm sau* khi gom, nên dùng được `SUM`, `COUNT`. Lọc được ở WHERE thì nên đặt ở WHERE để giảm số hàng phải gom.
>
> Ranh giới: với LEFT JOIN, điều kiện lên bảng bên phải mà đặt trong `WHERE` sẽ loại các hàng `NULL` và biến nó thành INNER JOIN; muốn giữ thì đặt điều kiện vào `ON`.

**Normalization là gì? 1NF, 2NF, 3NF? Khi nào denormalize?**
> - **Normalization**: cách tổ chức bảng để mỗi sự thật chỉ lưu *một chỗ*, tránh dư thừa và bất thường khi cập nhật (sửa chỗ này quên chỗ kia).
> - **Khóa chính**: cột (hoặc nhóm cột) xác định duy nhất một hàng.
>
> Các dạng chuẩn xây chồng lên nhau:
> - **1NF**: mỗi ô chứa một giá trị nguyên tử, không có danh sách hay nhóm lặp (không lưu `"tag1,tag2"` trong một cột).
> - **2NF**: đạt 1NF và mọi cột không khóa phụ thuộc vào *toàn bộ* khóa chính, không chỉ một phần của khóa ghép.
> - **3NF**: đạt 2NF và cột không khóa không phụ thuộc vào cột không khóa khác (không phụ thuộc bắc cầu). Ví dụ `orders` không lưu `user_email`, vì email phụ thuộc `user_id` chứ không phụ thuộc đơn hàng.
>
> Denormalize là cố ý lưu trùng để *đọc nhanh hơn*, chấp nhận ghi phức tạp hơn: khi truy vấn đọc chiếm đa số và JOIN quá tốn, vd lưu sẵn `order_count` trong `users`, hoặc bảng báo cáo tổng hợp. Ranh giới: dữ liệu lịch sử như *giá lúc mua* lưu trong `order_items` không phải denormalize, vì đó là một sự thật khác với giá hiện tại của sản phẩm.

**SQL vs NoSQL, khi nào chọn cái nào? CAP theorem?**
> - **SQL (relational)**: dữ liệu theo bảng có schema cố định, quan hệ bằng khóa ngoại, truy vấn bằng SQL, transaction ACID.
> - **NoSQL**: nhóm DB không theo mô hình bảng: document (MongoDB), key-value (Redis), wide-column (Cassandra), graph (Neo4j).
> - **CAP theorem**: hệ thống phân tán khi xảy ra *phân mảnh mạng* (Partition) chỉ giữ được một trong hai: **Consistency** (mọi node trả dữ liệu mới nhất) hoặc **Availability** (mọi request đều được trả lời).
>
> Tiêu chí chọn là *hình dạng dữ liệu và kiểu truy cập*. Dữ liệu có quan hệ chặt, cần JOIN, cần transaction nhiều bảng (đơn hàng, thanh toán, kho) thì SQL. Dữ liệu schema thay đổi linh hoạt, truy cập theo một khóa, lượng ghi rất lớn cần mở rộng ngang dễ (session, cache, log, feed) thì NoSQL hợp hơn. Nhiều hệ thống dùng cả hai: PostgreSQL làm nguồn sự thật, Redis làm cache.
>
> Ranh giới của CAP: vì phân mảnh mạng là không tránh được, lựa chọn thực tế là khi mạng đứt thì ưu tiên C (từ chối phục vụ, CP) hay A (trả dữ liệu có thể cũ, AP). Khi mạng bình thường, đánh đổi là giữa độ trễ và tính nhất quán (PACELC). CAP chỉ nói về hệ thống phân tán; một PostgreSQL đơn lẻ không phải bài toán CAP.

**Pessimistic vs optimistic locking?**
> - **Pessimistic locking**: khóa dữ liệu *trước* khi sửa, giả định xung đột sẽ xảy ra; transaction khác phải chờ. Trong SQL: `SELECT ... FOR UPDATE`.
> - **Optimistic locking**: không khóa, giả định xung đột hiếm; khi ghi mới kiểm tra dữ liệu có bị ai sửa từ lúc đọc không, thường bằng cột `version`.
>
> Cả hai cùng chống *lost update* (hai bên cùng đọc rồi cùng ghi, một bản bị đè). Tiêu chí chọn là *tần suất xung đột*: xung đột thường xuyên và retry tốn kém (trừ tồn kho hàng hot, trừ số dư) thì pessimistic; xung đột hiếm, thao tác đọc lâu (người dùng sửa form vài phút) thì optimistic.
>
> ```sql
> UPDATE products SET stock = stock - 1, version = version + 1
> WHERE id = 42 AND version = 7;   -- 0 hàng bị sửa nghĩa là có người sửa trước, đọc lại và thử lại
> ```
>
> Ranh giới: pessimistic giữ khóa lâu làm giảm đồng thời và có thể deadlock; optimistic với xung đột cao gây retry liên tục. Với cập nhật đơn giản, câu lệnh nguyên tử có điều kiện (`SET stock = stock - 1 WHERE stock > 0`) tránh được cả hai.

**N+1 query là gì, sửa thế nào?**
> - **N+1 query**: lỗi hiệu năng khi lấy một danh sách N bản ghi bằng 1 query, rồi với *mỗi* bản ghi lại chạy thêm 1 query để lấy dữ liệu liên quan, tổng cộng N+1 query.
>
> Ví dụ lấy 100 đơn hàng rồi trong vòng lặp gọi `getUser(order.UserID)`: 101 lần đi về DB, mỗi lần tốn độ trễ mạng. Lỗi thường ẩn trong ORM (lazy loading) hoặc trong hàm gọi DB nằm trong vòng lặp. Sửa bằng cách lấy dữ liệu liên quan *theo lô*: dùng `JOIN` lấy luôn trong một query, hoặc chạy query thứ hai `WHERE user_id IN (...)`/`= ANY($1)` cho cả danh sách rồi ghép trong code (tổng 2 query); với ORM, dùng eager loading (`Preload`, `include`).
>
> Ranh giới: phát hiện bằng log query hoặc tracing (thấy hàng trăm query giống nhau trong một request). Dạng tương tự xảy ra với gọi API: gọi một service khác trong vòng lặp, sửa bằng endpoint batch.

**Viết truy vấn: top 3 khách hàng chi nhiều nhất tháng này; user chưa có đơn hàng.**
> - **Aggregation**: gom các hàng theo nhóm rồi tính tổng, đếm (`GROUP BY` + `SUM`, `COUNT`).
> - **Anti-join**: lấy hàng của bảng này *không có* hàng tương ứng ở bảng kia.
>
> Dùng bảng `users` và `orders` ở đầu file. Top 3 khách chi nhiều nhất tháng này: lọc đơn đã thanh toán trong tháng, gom theo user, sắp giảm dần, lấy 3.
>
> ```sql
> SELECT u.id, u.name, SUM(o.total) AS spent
> FROM orders o
> JOIN users u ON u.id = o.user_id
> WHERE o.status = 'paid'
>   AND o.created_at >= date_trunc('month', now())
> GROUP BY u.id, u.name
> ORDER BY spent DESC
> LIMIT 3;
> ```
>
> User chưa có đơn hàng: anti-join, viết bằng `NOT EXISTS` hoặc `LEFT JOIN ... IS NULL`.
>
> ```sql
> SELECT u.id, u.email
> FROM users u
> WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
> ```
>
> Ranh giới: lọc thời gian bằng khoảng (`>=` đầu tháng) để dùng được index trên `created_at`, không bọc cột trong hàm. Tránh `NOT IN (SELECT user_id ...)`: nếu subquery có một giá trị `NULL` thì kết quả rỗng. Nếu hai khách bằng tiền nhau ở vị trí thứ 3, `LIMIT 3` cắt ngẫu nhiên; cần xử lý hòa thì dùng window function `RANK()`. `date_trunc` là cú pháp PostgreSQL, MySQL viết khác.

**Vì sao phải dùng prepared statement / placeholder?**
> - **SQL injection**: lỗ hổng khi dữ liệu người dùng được ghép thẳng vào chuỗi SQL, khiến dữ liệu bị hiểu thành lệnh.
> - **Placeholder / prepared statement**: viết câu SQL với chỗ trống (`$1`, `?`) và gửi giá trị *riêng* khỏi câu lệnh.
>
> Quy tắc: khi câu lệnh và dữ liệu đi tách nhau, DB parse câu lệnh trước và luôn coi giá trị là *dữ liệu*, không bao giờ là cú pháp SQL, nên input như `' OR '1'='1` chỉ là một chuỗi bình thường. `db.QueryContext(ctx, "SELECT ... WHERE email = $1", email)` an toàn; `fmt.Sprintf("... WHERE email = '%s'", email)` thì không. Prepared statement còn cho DB tái sử dụng kế hoạch thực thi khi chạy nhiều lần.
>
> Ranh giới: placeholder chỉ thay được *giá trị*, không thay được tên bảng, tên cột hay `ASC/DESC`; những chỗ đó phải đối chiếu với danh sách cho phép (whitelist). Chi tiết ở [12-secure-coding.md](12-secure-coding.md).

## Liên quan
- [05-data-structures.md](05-data-structures.md): B+ tree, hash table.
- [09-concurrency.md](09-concurrency.md): connection pool, race condition.
- [12-secure-coding.md](12-secure-coding.md): SQL injection.
