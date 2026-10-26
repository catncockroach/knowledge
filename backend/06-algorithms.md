# Algorithms

> Thuật toán là dãy bước hữu hạn, xác định để giải một bài toán. Ở level entry cần biết đánh giá độ phức tạp (Big-O), hiểu và tự cài đặt được các thuật toán sắp xếp và tìm kiếm kinh điển.

## Tại sao cần biết
Backend xử lý dữ liệu lớn: một thuật toán O(n²) chạy tốt với 100 bản ghi có thể treo với 1 triệu bản ghi. Interview gần như chắc chắn có câu: "độ phức tạp của đoạn code này?", "cài đặt binary search / quick sort", "so sánh merge sort và quick sort". Hiểu thuật toán còn giúp hiểu vì sao DB cần index, vì sao nên sort trước khi tìm.

## Khái niệm cốt lõi

### Đánh giá thuật toán
Một thuật toán tốt phải **đúng** (cho kết quả đúng với mọi input hợp lệ, kể cả trường hợp biên) và **hiệu quả** (về thời gian và bộ nhớ).

- **Time complexity**: số bước cơ bản tăng thế nào khi kích thước input n tăng.
- **Space complexity**: bộ nhớ **phụ** cần thêm (không tính input).
- **Big-O** mô tả **cận trên** của tốc độ tăng, bỏ hằng số và số hạng bậc thấp: 3n² + 5n + 100 → O(n²). Lý do: khi n lớn, số hạng bậc cao áp đảo.
- Ba trường hợp: **best** (tốt nhất), **average** (trung bình), **worst** (xấu nhất). Khi nói "độ phức tạp" mà không nói rõ, thường hiểu là worst case. (Θ là cận chặt, Ω là cận dưới; ở interview entry thường chỉ dùng O.)

### Các bậc phổ biến
| Big-O | Tên | Ví dụ | n = 10⁶ (xấp xỉ số bước) |
|---|---|---|---|
| O(1) | Hằng số | Truy cập `a[i]`, tra map | 1 |
| O(log n) | Logarit | Binary search, thao tác cây cân bằng | 20 |
| O(n) | Tuyến tính | Duyệt mảng, linear search | 10⁶ |
| O(n log n) | | Merge sort, quick sort trung bình, heap sort | 2×10⁷ |
| O(n²) | Bình phương | Hai vòng lặp lồng nhau, bubble sort | 10¹² |
| O(2ⁿ) | Mũ | Duyệt mọi tập con | không khả thi |
| O(n!) | Giai thừa | Duyệt mọi hoán vị | không khả thi |

Quy tắc ước lượng: máy tính làm cỡ 10⁸ phép tính đơn giản mỗi giây. Với n = 10⁶, O(n log n) chạy trong tích tắc, O(n²) mất hàng giờ.

### Cách tính độ phức tạp
- Câu lệnh đơn: O(1).
- Vòng lặp chạy n lần, thân O(1): O(n). Hai vòng **lồng nhau** n×n: O(n²). Hai vòng **nối tiếp**: O(n) + O(n) = O(n).
- Vòng lặp mà biến chia đôi mỗi lần (`for i := n; i > 0; i /= 2`): O(log n).
- Đệ quy: viết công thức truy hồi. Merge sort: T(n) = 2T(n/2) + O(n) → O(n log n) (log n tầng, mỗi tầng tổng công việc O(n)).
- Chú ý chi phí ẩn: `strings.Contains` là O(n·m), `append` hết cap là O(n), `copy` slice là O(n), gọi DB trong vòng lặp là n lần round-trip mạng.

```go
func example(a []int) {
    n := len(a)
    for i := 0; i < n; i++ {        // O(n)
        fmt.Println(a[i])
    }
    for i := 0; i < n; i++ {        // O(n²)
        for j := i + 1; j < n; j++ {
            _ = a[i] + a[j]
        }
    }
}
// Tổng: O(n) + O(n²) = O(n²)
```

### Đệ quy
Hàm gọi chính nó, cần **điều kiện dừng** (base case) và mỗi lần gọi phải tiến gần base case. Mỗi lời gọi chiếm một khung trên call stack → đệ quy quá sâu gây stack overflow (Go tự nới stack goroutine nhưng vẫn có giới hạn). Đệ quy rõ ràng cho bài toán chia để trị, cây; vòng lặp tiết kiệm bộ nhớ hơn.

### Thuật toán sắp xếp
| Thuật toán | Best | Average | Worst | Bộ nhớ phụ | Stable | Ý tưởng |
|---|---|---|---|---|---|---|
| Bubble sort | O(n) (có cờ dừng) | O(n²) | O(n²) | O(1) | Có | Đổi chỗ cặp kề sai thứ tự, phần tử lớn "nổi" lên cuối |
| Selection sort | O(n²) | O(n²) | O(n²) | O(1) | Không | Mỗi vòng chọn phần tử nhỏ nhất đưa về đầu |
| Insertion sort | O(n) | O(n²) | O(n²) | O(1) | Có | Chèn từng phần tử vào đúng chỗ trong phần đã sort; nhanh với mảng nhỏ hoặc gần sort |
| Merge sort | O(n log n) | O(n log n) | O(n log n) | O(n) | Có | Chia đôi, sort từng nửa, trộn hai nửa đã sort |
| Quick sort | O(n log n) | O(n log n) | O(n²) | O(log n) (stack) | Không | Chọn pivot, chia thành nhóm < pivot và > pivot, đệ quy |
| Heap sort | O(n log n) | O(n log n) | O(n log n) | O(1) | Không | Dựng max-heap, lần lượt lấy max ra cuối |

- **Stable**: các phần tử bằng nhau giữ nguyên thứ tự ban đầu. Quan trọng khi sort nhiều lần theo nhiều tiêu chí (sort theo tên, rồi stable sort theo phòng ban → trong mỗi phòng vẫn theo tên).
- **In-place**: không cần mảng phụ đáng kể.
- **Quick sort worst case O(n²)** xảy ra khi pivot luôn là phần tử nhỏ/lớn nhất (ví dụ chọn phần tử đầu với mảng đã sort). Khắc phục: chọn pivot ngẫu nhiên hoặc median-of-three. Thực tế quick sort thường nhanh nhất nhờ hằng số nhỏ và thân thiện cache.
- **Merge sort** ổn định, worst case đảm bảo, hợp cho linked list và sắp xếp dữ liệu lớn hơn RAM (external sort), nhưng cần O(n) bộ nhớ phụ.
- Thư viện chuẩn thường dùng thuật toán lai: Go `sort.Sort`/`slices.Sort` dùng pattern-defeating quicksort (kết hợp quick sort, insertion sort cho đoạn nhỏ và heap sort khi phân hoạch xấu), **không stable**; cần stable thì dùng `sort.SliceStable`/`slices.SortStableFunc`.
- Sắp xếp dựa trên so sánh không thể nhanh hơn O(n log n) trong trường hợp xấu. Counting sort, radix sort đạt O(n + k) nhờ không so sánh, nhưng chỉ dùng được cho khóa số nguyên trong phạm vi nhỏ.

### Thuật toán tìm kiếm
| Thuật toán | Điều kiện | Độ phức tạp |
|---|---|---|
| Linear search | Không | O(n) |
| Binary search | Mảng **đã sắp xếp** | O(log n) |
| Hash lookup | Đã dựng hash table | O(1) trung bình |
| BFS / DFS | Đồ thị, cây | O(V + E) |

**Binary search**: so phần tử giữa với target, loại bỏ một nửa mỗi bước. 1 triệu phần tử chỉ cần tối đa khoảng 20 lần so sánh (2²⁰ ≈ 10⁶).

**BFS** (duyệt theo chiều rộng, dùng queue): thăm theo từng lớp, tìm được đường đi ngắn nhất theo số cạnh trên đồ thị không trọng số. **DFS** (theo chiều sâu, dùng stack/đệ quy): đi sâu hết một nhánh rồi quay lui; dùng để phát hiện chu trình, sắp xếp topo, duyệt mọi khả năng.

### Một số kỹ thuật hay gặp
- **Two pointers**: hai chỉ số chạy trên mảng (đã sort) để tránh vòng lặp lồng; ví dụ tìm cặp có tổng bằng k trong O(n).
- **Sliding window**: cửa sổ trượt cho bài toán dãy con liên tiếp.
- **Chia để trị**: chia nhỏ, giải, kết hợp (merge sort, quick sort, binary search).
- **Tham lam (greedy)**: chọn tối ưu cục bộ mỗi bước (chỉ đúng với một số bài toán).
- **Quy hoạch động (DP)**: lưu kết quả bài toán con chồng lấp để không tính lại (Fibonacci, balo).
- **Đánh đổi không gian và thời gian**: dùng thêm bộ nhớ (map, cache, bảng DP) để giảm thời gian.

## Cách hoạt động
Cài đặt bằng Go các thuật toán cốt lõi.

**Bubble sort**
```go
func bubbleSort(a []int) {
    n := len(a)
    for i := 0; i < n-1; i++ {
        swapped := false
        for j := 0; j < n-1-i; j++ { // sau mỗi vòng, phần tử lớn nhất về cuối
            if a[j] > a[j+1] {
                a[j], a[j+1] = a[j+1], a[j]
                swapped = true
            }
        }
        if !swapped { // không đổi chỗ lần nào: đã sort, best case O(n)
            return
        }
    }
}
```

**Selection sort**
```go
func selectionSort(a []int) {
    for i := 0; i < len(a)-1; i++ {
        minIdx := i
        for j := i + 1; j < len(a); j++ {
            if a[j] < a[minIdx] {
                minIdx = j
            }
        }
        a[i], a[minIdx] = a[minIdx], a[i]
    }
}
```

**Insertion sort**
```go
func insertionSort(a []int) {
    for i := 1; i < len(a); i++ {
        key := a[i]
        j := i - 1
        for j >= 0 && a[j] > key { // dịch các phần tử lớn hơn sang phải
            a[j+1] = a[j]
            j--
        }
        a[j+1] = key
    }
}
```

**Merge sort**
```go
func mergeSort(a []int) []int {
    if len(a) <= 1 {
        return a
    }
    mid := len(a) / 2
    left := mergeSort(a[:mid])
    right := mergeSort(a[mid:])
    return merge(left, right)
}

func merge(l, r []int) []int {
    out := make([]int, 0, len(l)+len(r))
    i, j := 0, 0
    for i < len(l) && j < len(r) {
        if l[i] <= r[j] { // <= giữ tính stable
            out = append(out, l[i]); i++
        } else {
            out = append(out, r[j]); j++
        }
    }
    out = append(out, l[i:]...)
    return append(out, r[j:]...)
}
```

**Quick sort** (phân hoạch Lomuto, pivot là phần tử cuối)
```go
func quickSort(a []int, lo, hi int) {
    if lo >= hi {
        return
    }
    p := partition(a, lo, hi)
    quickSort(a, lo, p-1)
    quickSort(a, p+1, hi)
}

func partition(a []int, lo, hi int) int {
    pivot := a[hi]
    i := lo
    for j := lo; j < hi; j++ {
        if a[j] < pivot {
            a[i], a[j] = a[j], a[i]
            i++
        }
    }
    a[i], a[hi] = a[hi], a[i] // đưa pivot về đúng vị trí cuối cùng
    return i
}
// gọi: quickSort(a, 0, len(a)-1)
```

**Binary search**
```go
func binarySearch(a []int, target int) int {
    lo, hi := 0, len(a)-1
    for lo <= hi {
        mid := lo + (hi-lo)/2 // tránh tràn số so với (lo+hi)/2
        switch {
        case a[mid] == target:
            return mid
        case a[mid] < target:
            lo = mid + 1
        default:
            hi = mid - 1
        }
    }
    return -1
}
// thư viện chuẩn: idx, found := slices.BinarySearch(a, target)
```

**BFS trên đồ thị**
```go
func bfs(graph map[int][]int, start int) []int {
    visited := map[int]bool{start: true}
    queue := []int{start}
    var order []int
    for len(queue) > 0 {
        v := queue[0]
        queue = queue[1:]
        order = append(order, v)
        for _, nb := range graph[v] {
            if !visited[nb] {
                visited[nb] = true
                queue = append(queue, nb)
            }
        }
    }
    return order
}
```

## Ví dụ
Chạy tay quick sort trên `[5, 2, 8, 1, 9, 3]`, pivot = 3 (phần tử cuối):
- Duyệt j: 5 (≥3, bỏ qua), 2 (<3, đổi với a[0] → `[2,5,8,1,9,3]`, i=1), 8 (bỏ qua), 1 (<3, đổi với a[1] → `[2,1,8,5,9,3]`, i=2), 9 (bỏ qua).
- Đổi pivot với a[2]: `[2,1,3,5,9,8]`. Pivot 3 đã đúng vị trí; đệ quy trên `[2,1]` và `[5,9,8]`.

Sắp xếp struct trong Go thực tế:
```go
type User struct{ Name string; Age int }
users := []User{{"An", 30}, {"Bình", 25}, {"Chi", 30}}

sort.SliceStable(users, func(i, j int) bool { return users[i].Age < users[j].Age })
// Bình 25, An 30, Chi 30  (An vẫn trước Chi vì stable)

slices.SortFunc(users, func(a, b User) int { return cmp.Compare(a.Name, b.Name) })
```

Ví dụ backend: lấy 10 sản phẩm bán chạy nhất trong 1 triệu bản ghi. Sort toàn bộ là O(n log n); dùng min-heap kích thước 10 là O(n log 10) ≈ O(n). Tốt hơn nữa: để DB làm (`ORDER BY sold DESC LIMIT 10` với index phù hợp).

## Hiểu nhầm thường gặp
- **"O(1) luôn nhanh hơn O(n)"**: Big-O bỏ hằng số; với n nhỏ, O(n) có hằng số nhỏ có thể nhanh hơn. Big-O nói về xu hướng khi n lớn.
- **"Quick sort luôn O(n log n)"**: worst case O(n²); thư viện chuẩn phòng tránh bằng cách chọn pivot tốt và chuyển sang heap sort.
- **"Binary search dùng cho mọi mảng"**: chỉ đúng trên mảng đã sắp xếp.
- **"Space complexity tính cả input"**: thường chỉ tính bộ nhớ phụ; đệ quy tốn bộ nhớ stack theo độ sâu.

## Câu hỏi ôn tập
1. **Big-O là gì? Vì sao bỏ hằng số?** Cận trên tốc độ tăng; khi n lớn, bậc cao nhất quyết định.
2. **Độ phức tạp của binary search? Điều kiện?** O(log n), mảng đã sort.
3. **So sánh merge sort và quick sort.** Cùng O(n log n) trung bình; merge stable, worst O(n log n), cần O(n) bộ nhớ; quick in-place, nhanh thực tế, worst O(n²), không stable.
4. **Stable sort là gì, khi nào cần?** Giữ thứ tự phần tử bằng nhau; khi sort nhiều tiêu chí.
5. **Bubble sort best case O(n) khi nào?** Mảng đã sort và có cờ dừng sớm.
6. **BFS khác DFS?** Queue vs stack; BFS tìm đường ngắn nhất theo số cạnh.
7. **Cài đặt binary search / một thuật toán sort trên bảng trắng.** Luyện lại các đoạn code trên, chú ý trường hợp biên: mảng rỗng, 1 phần tử, phần tử trùng.

## Liên quan
- [05-data-structures.md](05-data-structures.md): các cấu trúc mà thuật toán chạy trên đó.
- [10-databases.md](10-databases.md): index giúp truy vấn từ O(n) xuống O(log n).
