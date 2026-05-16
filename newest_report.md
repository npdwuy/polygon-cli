# Báo cáo dự án: Polygon Automation Tool (DWUY Tool)

## 1. Tổng quan dự án
Dự án là một công cụ quản lý cục bộ (Local Management Tool) mạnh mẽ được thiết kế để tự động hóa quy trình làm việc với hệ thống **Codeforces Polygon API**. Phiên bản hiện tại (v1.0.0) đã hoàn thiện các tính năng cốt lõi cho phép Problem Setter quản lý bài tập từ xa một cách ổn định và chuyên nghiệp.

## 2. Kiến trúc hệ thống & Thành phần
Dự án được xây dựng trên nền tảng **TypeScript/Node.js**, tối ưu hóa cho môi trường dòng lệnh (CLI):

*   **Core Engine (`src/core/`):**
    *   **`polygon.ts`**: Wrapper API chuyên sâu. Xử lý xác thực phức tạp (HMAC SHA-512), tự động hóa chữ ký số cho từng request và có cơ chế **Exponential Backoff** để vượt qua giới hạn tần suất (Rate Limit 429).
    *   **`pipeline.ts`**: Điều phối luồng công việc tự động qua 6 bước chính:
        1.  **SETUP**: Khởi tạo bài tập, cấu hình giới hạn và Checker.
        2.  **SOLUTIONS**: Upload đồng loạt các giải pháp (MA, TL, WA...).
        3.  **GEN**: Upload mã nguồn sinh test (`generator.cpp`).
        4.  **TESTS**: Engine sinh Script tự động dựa trên cấu hình Subtask.
        5.  **BUILD & DOWNLOAD**: Kích hoạt build gói bài tập và tải về dưới dạng Binary Stream.
        6.  **EXTRACT**: Giải nén và chạy `doall.bat` để đồng bộ dữ liệu test cục bộ.
    *   **`workspace.ts`**: Quản lý Registry (`problem.json`) và cấu trúc thư mục làm việc.

*   **CLI UI (`src/cli/`):**
    *   Giao diện dòng lệnh `polygon` mạnh mẽ với các lệnh: `config`, `init`, `add`, `sync`, `download`, `extract`, `status`.

*   **Desktop UI (Tầm nhìn phát triển):**
    *   Cấu trúc thư mục `src/desktop` đã được chuẩn bị để tích hợp **Electron + Vite**. Hiện tại, logic lõi đang được ổn định hóa trên CLI trước khi chuyển đổi sang giao diện đồ họa.

## 3. Quản lý Dữ liệu (Source of Truth)
*   **`problem.json`**: Cơ sở dữ liệu local duy nhất. Lưu trữ metadata, cấu hình subtask, và trạng thái pipeline của từng bài tập.
*   **`contest.json`**: Cấu hình gom nhóm các bài tập theo kỳ thi.
*   **`.env`**: Lưu trữ an toàn API Key và Secret.

## 4. Trạng thái hiện tại (Snapshot)
*   **Phiên bản**: 1.0.0 (Stable CLI).
*   **Bài tập mẫu**: `Multiple of 2019` (`mult2019`) đã hoàn thiện.
    *   Đã đồng bộ thành công lên Polygon (ID: `542238`).
    *   Đã kiểm thử quy trình `sync -> download -> extract` trơn tru.
    *   Dữ liệu test đã được sinh và lưu tại `problems/mult2019/tests/`.

## 5. Đánh giá & Định hướng
*   **Ưu điểm**: 
    *   Tự động hóa hoàn toàn việc sinh Script trên Polygon (tránh lỗi tay).
    *   Xử lý file ZIP và chạy `doall.bat` tự động giúp tiết kiệm thời gian thiết lập local.
    *   Hệ thống xác thực và retry API cực kỳ bền bỉ.
*   **Hạn chế**: Hiện tại chỉ hỗ trợ Windows (do phụ thuộc vào `doall.bat` và PowerShell cho việc giải nén).
*   **Định hướng**: Phát triển giao diện Desktop để hỗ trợ cấu hình Subtask trực quan hơn và hỗ trợ đa nền tảng (Cross-platform extraction).
