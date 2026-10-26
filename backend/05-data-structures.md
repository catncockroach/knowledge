# Data structures

> Cấu trúc dữ liệu là cách tổ chức dữ liệu trong bộ nhớ để các thao tác cần thiết (tìm, thêm, xóa, duyệt) diễn ra hiệu quả. Chọn đúng cấu trúc dữ liệu thường quan trọng hơn tối ưu từng dòng code.

## Tại sao cần biết
Thuật toán luôn chạy trên một cấu trúc dữ liệu, và độ phức tạp của thuật toán phụ thuộc vào cấu trúc đó: tìm một phần tử trong slice chưa sắp xếp là O(n), trong map là O(1) trung bình, trong cây cân bằng là O(log n). Yêu cầu entry level: hiểu chi tiết kiểu dữ liệu cơ bản (integer, boolean…) và array, hiểu mối liên hệ giữa cấu trúc dữ liệu và giải thuật.

## Khái niệm cốt lõi

Ký hiệu O(...) trong file này đo số bước tăng theo kích thước dữ liệu n: O(1) là hằng số, O(n) tăng tuyến tính, O(log n) tăng rất chậm. Cách tính chi tiết ở [06-algorithms.md](06-algorithms.md).

### Kiểu dữ liệu cơ bản (primitive)
Máy tính chỉ lưu bit. Kiểu dữ liệu quy định **bao nhiêu bit** và **diễn giải chúng thế nào**.

**Integer**
| Kiểu Go | Kích thước | Phạm vi |
|---|---|---|
| `int8` | 1 byte | −128 … 127 |
| `uint8` / `byte` | 1 byte | 0 … 255 |
| `int16` | 2 byte | −32 768 … 32 767 |
| `int32` / `rune` | 4 byte | khoảng ±2,1 tỷ (−2³¹ … 2³¹−1) |
| `int64` | 8 byte | khoảng ±9,2×10¹⁸ (−2⁶³ … 2⁶³−1) |
| `int`, `uint` | 4 hoặc 8 byte tùy nền tảng | 8 byte trên máy 64-bit |

- Số âm lưu theo **bù hai** (two's complement): đảo bit rồi cộng 1. Vì vậy phạm vi có dạng −2ⁿ⁻¹ … 2ⁿ⁻¹−1.
- **Overflow**: vượt phạm vi thì "quay vòng" không báo lỗi: `var x int8 = 127; x++` → `-128`. Cẩn thận khi cộng số lớn, khi ép `int64` xuống `int32`.

**Số thực (float)**
- `float32` (~7 chữ số có nghĩa), `float64` (~15–16 chữ số), theo chuẩn IEEE 754: dấu + số mũ + phần định trị.
- Nhiều số thập phân không biểu diễn chính xác được: `0.1 + 0.2 == 0.3` là **false**. So sánh float dùng sai số (`math.Abs(a-b) < 1e-9`).
- **Tiền tệ không dùng float**: lưu số nguyên theo đơn vị nhỏ nhất (đồng, cent) bằng `int64`, hoặc dùng kiểu decimal.

**Boolean**: `true`/`false`, thường chiếm 1 byte. Go không cho dùng số thay bool (`if 1 {}` là lỗi).

**Ký tự và chuỗi**: ASCII dùng 1 byte/ký tự cho 128 ký tự cơ bản. Unicode gán mỗi ký tự một *code point*; **UTF-8** mã hóa code point bằng 1–4 byte. String Go là dãy byte UTF-8 bất biến; `rune` là một code point.

### Array
- Dãy phần tử cùng kiểu nằm **liên tiếp** trong bộ nhớ. Địa chỉ phần tử i = địa chỉ đầu + i × kích thước phần tử → truy cập theo chỉ số **O(1)**.
- Liên tiếp trong bộ nhớ nên thân thiện với CPU cache (duyệt rất nhanh).
- Chèn/xóa ở giữa phải dịch các phần tử sau → **O(n)**.
- Kích thước cố định. **Dynamic array** (slice của Go, `ArrayList` Java, `vector` C++) tự cấp phát mảng lớn hơn khi đầy và copy sang; vì mỗi lần tăng theo cấp số nhân nên `append` có chi phí **amortized O(1)**.

### Linked list
```
head → [3|•] → [7|•] → [9|nil]
```
- Mỗi node chứa dữ liệu + con trỏ tới node kế (singly) hoặc cả node trước (doubly).
- Chèn/xóa khi đã có con trỏ tới vị trí: O(1). Truy cập phần tử thứ i: O(n) (phải đi từ đầu).
- Các node rải rác trong bộ nhớ → không thân thiện cache. Thực tế slice thường nhanh hơn linked list cho hầu hết tác vụ; linked list hữu ích trong LRU cache, hàng đợi cần xóa ở giữa.
- Go có `container/list` (doubly linked list).

### Stack (ngăn xếp): LIFO
- Vào sau ra trước. Thao tác `push`, `pop`, `peek` đều O(1).
- Ứng dụng: call stack của chương trình, undo, kiểm tra ngoặc hợp lệ, DFS, tính biểu thức.
```go
stack := []int{}
stack = append(stack, 1, 2)       // push
top := stack[len(stack)-1]        // peek
stack = stack[:len(stack)-1]      // pop
```

### Queue (hàng đợi): FIFO
- Vào trước ra trước. `enqueue`, `dequeue` O(1) (với cài đặt đúng: linked list hoặc ring buffer).
- Ứng dụng: BFS, hàng đợi job, buffer giữa producer/consumer (channel có buffer của Go chính là một queue an toàn đồng thời), message queue.
- **Deque**: thêm/bớt ở cả hai đầu. **Priority queue**: lấy ra phần tử ưu tiên cao nhất, cài bằng heap.

### Hash table (map)
```
key "alice" ─hash()→ 7 ─(mod số bucket)→ bucket 3 → [("alice", 30)]
key "bob"   ─hash()→ 2 ─────────────────→ bucket 2 → [("bob", 25)]
```
- Hàm băm biến key thành số, xác định bucket chứa cặp key-value. Tìm/thêm/xóa **trung bình O(1)**.
- **Collision**: hai key khác nhau rơi cùng bucket. Giải quyết bằng chaining (mỗi bucket là danh sách) hoặc open addressing (tìm ô trống kế tiếp).
- **Load factor** = số phần tử / số bucket. Vượt ngưỡng thì **rehash** (tăng số bucket, phân bố lại).
- Trường hợp xấu (mọi key cùng bucket) là O(n). Không giữ thứ tự.
- Ứng dụng: đếm tần suất, cache, index, loại trùng (set: `map[T]struct{}`).

### Tree
- Cấu trúc phân cấp: root, node con, lá. **Binary tree**: mỗi node tối đa 2 con.
- **Binary Search Tree (BST)**: con trái < node < con phải. Tìm/thêm/xóa O(h) với h là chiều cao: O(log n) nếu cân bằng, O(n) nếu lệch (chèn dãy đã sắp xếp thì thành linked list).
- **Cây cân bằng** (AVL, Red-Black) tự xoay để giữ h = O(log n). `TreeMap` Java dùng Red-Black tree.
- **B-tree / B+ tree**: mỗi node có nhiều con, thấp và rộng, tối ưu cho đọc theo block trên đĩa. Đây là cấu trúc của **index trong database** (xem [10-databases.md](10-databases.md)).
- **Trie**: cây theo ký tự, dùng cho autocomplete, tìm theo tiền tố.
- Duyệt cây: pre-order, in-order (BST cho ra dãy tăng dần), post-order (đều là DFS), level-order (BFS).

### Heap
- Cây nhị phân hoàn chỉnh lưu trong array; **min-heap**: cha ≤ con, nên phần tử nhỏ nhất luôn ở gốc.
- Lấy min O(1), thêm/xóa O(log n). Dùng làm priority queue, heap sort, tìm top-K, lập lịch theo thời gian.
- Lưu trong array: con của i là 2i+1 và 2i+2, cha của i là (i−1)/2. Go có `container/heap`.

### Graph
- Tập đỉnh (vertex) và cạnh (edge); có hướng/vô hướng, có trọng số/không.
- Biểu diễn: **adjacency list** (`map[int][]int`, tiết kiệm cho đồ thị thưa) hoặc **adjacency matrix** (n×n, kiểm tra cạnh O(1) nhưng tốn O(n²) bộ nhớ).
- Ứng dụng: mạng xã hội, bản đồ đường đi, phụ thuộc giữa service/package, routing mạng.

### Bảng tổng hợp độ phức tạp
| Cấu trúc | Truy cập theo vị trí | Tìm kiếm | Thêm | Xóa | Ghi chú |
|---|---|---|---|---|---|
| Array/slice | O(1) | O(n) (O(log n) nếu đã sort) | O(1)* cuối, O(n) giữa | O(n) giữa | Cache tốt |
| Linked list | O(n) | O(n) | O(1) nếu có vị trí | O(1) nếu có vị trí | |
| Stack/Queue | — | O(n) | O(1) | O(1) | |
| Hash map | — | O(1) tb | O(1) tb | O(1) tb | Không thứ tự |
| BST cân bằng | — | O(log n) | O(log n) | O(log n) | Có thứ tự, range query |
| Heap | — | O(n) | O(log n) | O(log n) lấy min | Min/max O(1) |

\* amortized.

## Cách hoạt động
**Mối liên hệ giữa cấu trúc dữ liệu và giải thuật** (*"Algorithms + Data Structures = Programs"*):
1. Xác định thao tác nào xảy ra nhiều nhất: tìm theo key? lấy phần tử nhỏ nhất? duyệt theo thứ tự? thêm/xóa ở đầu?
2. Chọn cấu trúc làm thao tác đó rẻ nhất:
   - Tìm theo key → hash map.
   - Cần dữ liệu có thứ tự, truy vấn khoảng → cây cân bằng / slice đã sort + binary search.
   - Luôn lấy phần tử ưu tiên cao nhất → heap.
   - Xử lý theo thứ tự đến → queue. Quay lui, lồng nhau → stack.
3. Thuật toán được thiết kế dựa trên tính chất của cấu trúc: binary search cần array đã sắp xếp; BFS cần queue; DFS cần stack (hoặc đệ quy); Dijkstra cần priority queue.
4. Cân nhắc bộ nhớ và hằng số thực tế: O(1) của map có chi phí băm; với vài chục phần tử, duyệt slice có thể nhanh hơn.

## Ví dụ
**Bài toán Two Sum**: tìm hai chỉ số có tổng bằng target.

```go
// Cách 1: hai vòng lặp, O(n²) thời gian, O(1) bộ nhớ
func twoSumBrute(nums []int, target int) (int, int) {
    for i := 0; i < len(nums); i++ {
        for j := i + 1; j < len(nums); j++ {
            if nums[i]+nums[j] == target {
                return i, j
            }
        }
    }
    return -1, -1
}

// Cách 2: hash map, O(n) thời gian, O(n) bộ nhớ: đổi bộ nhớ lấy tốc độ
func twoSum(nums []int, target int) (int, int) {
    seen := make(map[int]int, len(nums)) // giá trị → chỉ số
    for i, v := range nums {
        if j, ok := seen[target-v]; ok {
            return j, i
        }
        seen[v] = i
    }
    return -1, -1
}
```
Với n = 100.000: cách 1 cần khoảng 5×10⁹ phép so sánh, cách 2 khoảng 10⁵ lần tra map.

**Kiểm tra ngoặc hợp lệ bằng stack:**
```go
func validBrackets(s string) bool {
    pair := map[rune]rune{')': '(', ']': '[', '}': '{'}
    var st []rune
    for _, c := range s {
        switch c {
        case '(', '[', '{':
            st = append(st, c)
        case ')', ']', '}':
            if len(st) == 0 || st[len(st)-1] != pair[c] {
                return false
            }
            st = st[:len(st)-1]
        }
    }
    return len(st) == 0
}
```

**Set trong Go:**
```go
set := map[string]struct{}{}  // struct{} chiếm 0 byte
set["go"] = struct{}{}
_, exists := set["go"]
```

## Hiểu nhầm thường gặp
- **"Hash map luôn O(1)"**: O(1) trung bình; trường hợp xấu O(n), có chi phí băm và rehash.
- **"Linked list chèn nhanh nên tốt hơn array"**: chỉ O(1) khi đã có con trỏ tới vị trí; tìm vị trí vẫn O(n), và cache miss làm nó chậm trong thực tế.
- **"float đủ chính xác cho tiền"**: sai số làm tròn tích lũy; dùng số nguyên đơn vị nhỏ nhất hoặc decimal.
- **"BST luôn O(log n)"**: chỉ khi cân bằng.

## Câu hỏi ôn tập
1. **Array khác linked list?** Liên tiếp vs rải rác; truy cập O(1) vs O(n); chèn giữa O(n) vs O(1) khi có vị trí.
2. **Hash table hoạt động thế nào? Xử lý collision?** Băm key → bucket; chaining hoặc open addressing; rehash khi load factor cao.
3. **Stack vs queue, ứng dụng?** LIFO (call stack, undo, DFS) vs FIFO (BFS, job queue).
4. **Vì sao index DB dùng B+ tree mà không dùng hash?** B+ tree giữ thứ tự, hỗ trợ range query và sort, ít lần đọc đĩa; hash chỉ tốt cho so sánh bằng.
5. **Heap dùng làm gì?** Priority queue, top-K, heap sort.
6. **int32 tràn thì sao? Vì sao 0.1 + 0.2 != 0.3?** Quay vòng theo bù hai; float nhị phân không biểu diễn chính xác 0.1.
7. **Amortized O(1) của append nghĩa là gì?** Thỉnh thoảng tốn O(n) để copy, nhưng chia đều trên nhiều lần thì trung bình O(1).

## Liên quan
- [03-go-basics.md](03-go-basics.md): slice, map, string trong Go.
- [06-algorithms.md](06-algorithms.md): thuật toán chạy trên các cấu trúc này, ký hiệu Big-O.
- [10-databases.md](10-databases.md): B+ tree trong index.
