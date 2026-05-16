# DWUY Polygon Tool

**Polygon Automation Tool (DWUY Tool)** là một công cụ quản lý bài tập lập trình thi đấu (Competitive Programming) cục bộ mạnh mẽ, được thiết kế để tự động hóa hoàn toàn quy trình làm việc với hệ thống **Codeforces Polygon API**.

[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/npdwuy/polygon-cli)

---

## 🚀 Tính năng nổi bật

- **Tự động hóa Pipeline**: Quy trình 6 bước từ khởi tạo bài tập đến giải nén testcase local.
- **Dynamic Script Generation**: Tự động tính toán và sinh script testcase trên Polygon dựa trên cấu hình subtask.
- **Quản lý Package thông minh**: Tự động build, theo dõi trạng thái và tải gói bài tập về máy.
- **Hệ thống xác thực an toàn**: Sử dụng chữ ký HMAC SHA-512 và cơ chế retry (Exponential Backoff) cho API.
- **Local Synchronization**: Giải nén và thực thi `doall.bat` tự động để đồng bộ dữ liệu test cục bộ ngay lập tức.

---

## 🛠 Tech Stack

- **Ngôn ngữ**: TypeScript
- **Runtime**: Node.js
- **Libraries**: Axios (API), Commander (CLI), Fs-extra (File management), Zod (Validation), Dotenv.
- **Hệ điều hành hỗ trợ**: Windows (do phụ thuộc vào PowerShell và `doall.bat`).

---

## 📥 Cài đặt

1. **Clone dự án**:
   ```bash
   git clone https://github.com/npdwuy/polygon-cli.git
   cd polygon-cli
   ```

2. **Cài đặt dependencies**:
   ```bash
   npm install
   ```

3. **Cấu hình API**:
   Sử dụng lệnh CLI để thiết lập API Key và Secret:
   ```bash
   npx ts-node src/cli/index.ts config <YOUR_API_KEY> <YOUR_API_SECRET>
   ```

---

## 📖 Hướng dẫn sử dụng

Sử dụng lệnh `polygon` (thông qua `npm run polygon` hoặc `npx ts-node src/cli/index.ts`):

| Lệnh | Mô tả |
| :--- | :--- |
| `init` | Khởi tạo cấu trúc workspace |
| `add <slug> -n <name>` | Thêm bài tập mới từ template |
| `sync <slug>` | Đồng bộ code, generator, script lên Polygon |
| `download <slug>` | Build package và tải file ZIP về |
| `extract <slug>` | Tải và giải nén tests vào thư mục local |
| `status` | Kiểm tra trạng thái pipeline của các bài tập |

---

## 📂 Cấu trúc dự án

```text
Polygon-tool/
├── src/
│   ├── cli/          # Giao diện dòng lệnh (Commander.js)
│   ├── core/         # Logic xử lý API và Pipeline
│   └── desktop/      # (Đang phát triển) Giao diện Desktop
├── problems/         # Source code các bài tập local
├── downloads/        # Các gói package tải từ Polygon
├── problem.json      # Registry lưu trữ trạng thái bài tập
└── contest.json      # Quản lý danh sách bài tập theo contest
```

---

## 🤝 Đóng góp

Mọi đóng góp nhằm cải thiện công cụ hoặc bổ sung tính năng mới đều được chào đón. Vui lòng tạo **Issue** hoặc **Pull Request** trên GitHub.

---

## 📄 Giấy phép

Dự án được phát hành dưới giấy phép **ISC**.

---

**Developed with ❤️ by [DWUY](https://github.com/npdwuy)**
