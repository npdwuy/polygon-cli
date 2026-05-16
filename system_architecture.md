# DWUY POLYGON TOOL - System Architecture (v1.0.0)

Hệ thống Local Management Tool tự động hóa quy trình tạo và quản lý bài tập lập trình thi đấu thông qua Polygon API, giúp thu hẹp khoảng cách giữa phát triển local và hệ thống quản lý bài tập chuyên nghiệp.

---

## 1. Cấu trúc thư mục (Local Workspace)

Hệ thống quản lý dữ liệu dưới dạng thư mục tĩnh, hỗ trợ tối đa cho việc kiểm soát phiên bản (Git).

```text
Polygon-tool/
│
├── .env                       # Lưu API Key, Secret (Bảo mật tuyệt đối)
├── problem.json               # Registry: Single Source of Truth của toàn bộ bài tập
├── contest.json               # Registry: Quản lý danh sách bài theo kỳ thi
├── downloads/                 # Lưu trữ các file ZIP bài tập tải từ Polygon
└── problems/                  # Thư mục gốc chứa source code
    └── [slug]/
        ├── generator.cpp      # Code sinh test (sử dụng testlib.h)
        ├── main.cpp           # Lời giải chuẩn (Model Answer - MA)
        ├── statement.tex      # Đề bài định dạng LaTeX (Tiếng Việt mặc định)
        └── tests/             # Dữ liệu test sau khi Extract (In/Out)
```

---

## 2. Mô hình Dữ liệu (State Management)

### 2.1. problem.json (Core Registry)
Lưu trữ toàn bộ cấu hình bài tập. Điểm đặc biệt là cơ chế **Dynamic Test Distribution** (chia đều điểm hoặc theo subtask).

```json
{
  "local_id": "mult2019",
  "polygon_id": 542238,
  "name": "Multiple of 2019",
  "settings": {
    "time_limit": 1000,
    "memory_limit": 1024,
    "checker": "std::lcmp.cpp"
  },
  "test_config": {
    "total_tests": 20,
    "subtasks": [
      { "id": 1, "percent": 30, "args": "small" },
      { "id": 2, "percent": 70, "args": "large" }
    ]
  },
  "pipeline_status": { "SETUP": true, "TESTS": true, "BUILD": "READY" }
}
```

---

## 3. Automation Pipeline (Quy trình 6 bước)

Pipeline được thiết kế để đảm bảo tính nhất quán (Atomicity) giữa Local và Remote.

### Bước 1: SETUP (Initialization)
- Kiểm tra `polygon_id`, nếu chưa có sẽ gọi `problem.create`.
- Cấu hình metadata: `updateInfo`, `setChecker`.
- Upload `statement.tex` qua `saveStatement` (Mặc định: `vietnamese`).

### Bước 2: SOLUTIONS & GEN (Asset Sync)
- Duyệt và upload tất cả solution trong `paths.solutions`.
- Upload `generator.cpp` dưới dạng `source` file. Hệ thống tự động nhận diện tên file làm tên command sinh test.

### Bước 3: TESTS (Dynamic Scripting)
- **Engine**: Tự động tính toán số lượng testcase dựa trên tỷ lệ phần trăm.
- **Scripting**: Tạo chuỗi lệnh command-line trực tiếp (ví dụ: `gen 1 1 small > 1`) và đẩy lên Polygon qua `saveScript`.
- **Scoring**: Tự động kích hoạt chấm điểm và chia điểm đều cho các testcase.

### Bước 4: COMMIT (Remote Save)
- Mọi thay đổi được chốt lại bằng lệnh `commitChanges` để đảm bảo Polygon lưu trữ phiên bản mới nhất trước khi Build.

### Bước 5: BUILD & DOWNLOAD (Package Management)
- **Trigger**: Gọi `buildPackage` với flag `verify=true` để Polygon kiểm tra tính hợp lệ của bài tập.
- **Polling**: Kiểm tra trạng thái package mỗi 5 giây cho đến khi `READY`.
- **Stream**: Tải tệp ZIP dưới dạng `arraybuffer` để tránh hỏng dữ liệu nhị phân.

### Bước 6: EXTRACT (Local Deployment)
- **Unzip**: Sử dụng PowerShell `Expand-Archive` để giải nén vào thư mục tạm.
- **Generation**: Chạy `doall.bat` (CMD) để thực thi generator và tạo file `.in/.out` chính thức.
- **Sync**: Di chuyển thư mục `tests/` đã sinh vào đúng vị trí trong `problems/[slug]/` và dọn dẹp.

---

## 4. API Core & Fault Tolerance (Tầng mạng)

- **Signature Security**: Áp dụng thuật toán SHA-512 theo đúng chuẩn Polygon: `rand/method?params#secret`.
- **Rate Limiting**: Sử dụng **Exponential Backoff** (thử lại tối đa 5 lần) khi gặp lỗi HTTP 429.
- **Binary Handling**: Tích hợp `axios` với `responseType: 'arraybuffer'` để xử lý các gói bài tập lớn mà không làm tràn bộ nhớ.

---

## 5. Hướng dẫn Vận hành (CLI Commands)

1.  `polygon config <key> <secret>`: Thiết lập thông tin xác thực.
2.  `polygon add <slug> -n <name>`: Khởi tạo cấu trúc bài tập mới từ template.
3.  `polygon sync <slug>`: Đẩy toàn bộ dữ liệu lên Polygon (Bước 1-4).
4.  `polygon download <slug>`: Build và tải ZIP (Bước 5).
5.  `polygon extract <slug>`: Giải nén và tạo test local (Bước 6).
6.  `polygon status`: Kiểm tra tổng quan tiến độ của các bài tập.

---

## 6. Lưu ý kỹ thuật quan trọng

> [!CAUTION]
> **Hệ điều hành**: Hiện tại công cụ yêu cầu **Windows** để thực thi `doall.bat` và lệnh PowerShell.
> **testlib.h**: Generator phải tương thích với `testlib.h` và nhận seed từ `argv[1]`. Tham số subtask nên bắt đầu từ `argv[2]`.
