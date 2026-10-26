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

## Câu hỏi ôn tập
1. **ACID là gì? Cho ví dụ.**
2. **Các isolation level và hiện tượng tương ứng? Mặc định của PostgreSQL/MySQL?**
3. **Index hoạt động thế nào? Khi nào không dùng được? Composite index và leftmost prefix?**
4. **INNER JOIN vs LEFT JOIN? WHERE vs HAVING?**
5. **Normalization là gì? 1NF, 2NF, 3NF? Khi nào denormalize?**
6. **SQL vs NoSQL, khi nào chọn cái nào? CAP theorem?**
7. **Pessimistic vs optimistic locking?**
8. **N+1 query là gì, sửa thế nào?**
9. **Viết truy vấn: top 3 khách hàng chi nhiều nhất tháng này; user chưa có đơn hàng.**
10. **Vì sao phải dùng prepared statement / placeholder?** Chống SQL injection, xem [12-secure-coding.md](12-secure-coding.md).

## Liên quan
- [05-data-structures.md](05-data-structures.md): B+ tree, hash table.
- [09-concurrency.md](09-concurrency.md): connection pool, race condition.
- [12-secure-coding.md](12-secure-coding.md): SQL injection.
