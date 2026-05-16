# Hướng dẫn sử dụng Polygon Tool 🚀

Công cụ hỗ trợ tự động hóa quy trình quản lý bài tập trên Codeforces Polygon.

## 1. Cài đặt môi trường

Công cụ này chạy trên nền tảng **Node.js**. Nếu máy bạn chưa có, hãy làm theo các bước sau:

### Cài đặt Node.js & npm:
1.  Truy cập trang chủ [nodejs.org](https://nodejs.org/).
2.  Tải bản **LTS** (khuyên dùng vì tính ổn định).
3.  Chạy file cài đặt và nhấn `Next` cho đến khi hoàn tất.
4.  Mở Terminal (hoặc CMD) và kiểm tra bằng lệnh:
    ```bash
    node -v
    npm -v
    ```
    (Nếu hiện ra phiên bản số là bạn đã cài đặt thành công).

### Cài đặt Tool:
```bash
# Clone dự án từ GitHub
git clone https://github.com/your-username/polygon-tool.git
cd polygon-tool

# Cài đặt các thư viện cần thiết
npm install
```

## 2. Cấu hình API

Để công cụ có thể kết nối với Polygon, bạn cần cung cấp **API Key** và **Secret**.

### Cách lấy API Key trên Polygon:
1.  Đăng nhập vào [Polygon](https://polygon.codeforces.com/).
2.  Nhấp vào mục **Settings** ở góc trên bên phải màn hình.
3.  Chọn tab **API Keys**.
4.  Nhấp vào nút **Add API Key**.
5.  Nhập mật khẩu tài khoản của bạn để xác nhận.
6.  Hệ thống sẽ cung cấp cho bạn một cặp **API Key** và **Secret**. Hãy lưu chúng lại cẩn thận.

### Thiết lập cho Tool:
Sử dụng lệnh sau để lưu thông tin vào dự án:
```bash
npm run polygon config <YOUR_API_KEY> <YOUR_API_SECRET>
```
Lệnh này sẽ tạo file `.env` lưu trữ thông tin của bạn một cách an toàn (file này đã được đưa vào `.gitignore`).

## 3. Quy trình làm việc cơ bản

### Bước 1: Khởi tạo Workspace
Nếu bạn mới bắt đầu trong một thư mục mới:
```bash
npm run polygon init
```

### Bước 2: Thêm bài tập mới
Tạo một bài tập mới với mã định danh (slug) và tên hiển thị:
```bash
npm run polygon add mult2019 --name "Multiple of 2019"
```
Hệ thống sẽ tạo thư mục `problems/mult2019` kèm theo các file mẫu: `main.cpp`, `generator.cpp`, `statement.tex`.

### Bước 3: Phát triển nội dung
*   Viết code giải trong `main.cpp`.
*   Viết logic sinh test trong `generator.cpp`.
*   Viết đề bài trong `statement.tex` (LaTeX).
*   Chỉnh sửa file `problem.json` để cấu hình subtasks và số lượng testcase.

### Bước 4: Đồng bộ lên Polygon
Đẩy toàn bộ dữ liệu (code, đề bài, script sinh test) lên hệ thống Polygon:
```bash
npm run polygon sync mult2019
```

### Bước 5: Kiểm tra và tải bộ test
Tải gói bài tập về, giải nén và sinh testcase cục bộ để kiểm tra:
```bash
npm run polygon extract mult2019
```
Bộ test sau khi sinh sẽ nằm trong thư mục `problems/mult2019/tests/`.

## 4. Các lệnh khác

*   `npm run polygon status`: Kiểm tra trạng thái đồng bộ của tất cả các bài tập.
*   `npm run polygon download <slug>`: Chỉ build và tải gói bài tập (.zip) về thư mục `downloads/`.

## 5. Lưu ý cho người dùng
*   **An toàn dữ liệu**: Đừng bao giờ commit file `.env` lên GitHub.
*   **Generator**: Khi sử dụng `testlib.h`, hãy nhớ đọc tham số từ `argv[2]` trở đi vì Polygon truyền thêm các tham số hệ thống ở đầu.
*   **Subtasks**: Bạn có thể chia phần trăm điểm và truyền tham số riêng cho generator thông qua mục `test_config` trong `problem.json`.

---
*Cập nhật lần cuối: 17:48 - 16/05/2026*
*Phát triển bởi DWUY - Chúc bạn tạo được những bài tập chất lượng!*
