# Hướng dẫn sử dụng DWUY Polygon Tool (v2)

Công cụ này giúp bạn tự động hóa hoàn toàn quy trình ra đề thi: từ việc upload mã nguồn, cấu hình giới hạn, tạo script test trên [Polygon](https://polygon.codeforces.com/) cho đến việc tự động kết nối và tạo Mashup Contest trên [Codeforces](https://codeforces.com/).

---

## 1. Chuẩn bị (Prerequisites)

1. Đảm bảo bạn đã cài đặt các thư viện cần thiết (Python requests, selenium, webdriver_manager).
2. Kiểm tra file `.env` đã có đầy đủ thông tin bí mật:
   ```env
   POLYGON_API_KEY=xxx
   POLYGON_API_SECRET=xxx
   POLYGON_USERNAME=xxx
   POLYGON_PASSWORD=xxx
   CODEFORCES_USERNAME=xxx
   CODEFORCES_PASSWORD=xxx
   ```
3. Cấu hình bài tập vào `problem.json` và khai báo tập hợp các bài thành một kỳ thi trong `contest.json`.

---

## 2. Cách sử dụng (Luồng Cấu Hình)

DWUY Polygon Tool sử dụng **cấu hình trực tiếp**. Bạn chỉ cần mở file `polygon.py` (file duy nhất bạn cần quan tâm), chỉnh sửa các biến cấu hình ngay ở phần đầu file, lưu lại và chạy lệnh:

```bash
python polygon.py
```

### Giải thích các `COMMAND`

Tại dòng `COMMAND = "..."`, bạn có thể chọn 1 trong 4 tính năng sau:

#### A. `COMMAND = "pipeline"`
Gửi và đồng bộ mã nguồn, cấu hình từ máy tính của bạn lên máy chủ Polygon.
- **`TARGET_SLUGS`**: Danh sách ID bài tập (local_id) bạn muốn đồng bộ. (VD: `["bai1", "bai2"]`).
- **`CONTEST_NAME_TO_SYNC`**: Nếu bạn điền tên Contest (VD: `"round-1"`), tool sẽ tự lấy danh sách bài từ `contest.json` để chạy (không cần điền `TARGET_SLUGS`).
- **`PIPELINE_FLAGS`**: Cấu hình các bước muốn làm (Để `True` để chạy, `False` để bỏ qua):
  - `init`: Tìm bài trên Polygon hoặc tự tạo mới, sau đó cập nhật Time/Memory Limit.
  - `resources`: Upload Generator, Checker và đề bài (Statement).
  - `solutions`: Upload mã nguồn giải (Solutions) kèm theo Tag (MA, WA, TLE...).
  - `tests`: Tạo file `script.txt` sinh test dựa vào `test_config` và upload.
  - `build`: Gửi tín hiệu để máy chủ Polygon bắt đầu đóng gói (Build Package).
  - `download`: Tự động ngồi chờ các bài tập build xong và tải toàn bộ file ZIP về thư mục `downloads/`.

#### B. `COMMAND = "automate-mashup"`
*(Yêu cầu bài tập đã chạy qua pipeline và đã có trên Polygon)*
Lệnh này kết hợp cả hai bước cấp quyền và tạo Mashup trong cùng một phiên duyệt web (Selenium):
1. **Trên Polygon**: Dựa vào tuỳ chọn `GRANT_CODEFORCES_ACCESS`, tool sẽ tự động vào trang thông tin bài tập, cào lấy **link chia sẻ Gym bí mật**, sau đó vào phần cài đặt quyền để cấp quyền **Read** cho tài khoản `codeforces`.
2. **Trên Codeforces**: Tự động tạo Mashup và nhúng các bài tập trên vào thông qua link vừa cào được.
- **`TARGET_SLUGS`** / **`CONTEST_NAME_TO_SYNC`**: Vẫn giữ nguyên cấu hình mục tiêu như lệnh pipeline để tool biết lấy các bài nào.
- **`MASHUP_NAME`**: Nếu có tên, tool sẽ tạo mới một Gym Mashup mang tên này.
- **`MASHUP_GYM_ID`**: Nếu bạn đã tạo Gym từ trước, hãy điền ID của Gym đó vào đây (khi dùng cái này thì để trống MASHUP_NAME).
- **`MASHUP_CONTEST_REF`**: (Tuỳ chọn) Tên contest local trong `contest.json`. Nếu bạn điền, sau khi Codeforces tạo xong Mashup, ID của nó sẽ được tự động lưu về `contest.json` cho bạn.
- **`GRANT_CODEFORCES_ACCESS`**: Đặt thành `True` để bot thay bạn thao tác cấp quyền Read cho tài khoản `codeforces` trên tất cả các bài tập mục tiêu.

#### C. `COMMAND = "package-contest"`
Sau khi đã `download` các bài tập thành công về máy, lệnh này giúp bạn lấy file ZIP của các bài gộp chung lại vào một file ZIP tổng của Contest (Rất tiện khi muốn gửi đề cho nền tảng khác chấm).
- **`PACKAGE_CONTEST_NAME`**: Tên contest có trong file `contest.json`. Kết quả sẽ lưu ra thư mục `contests/`.

---

## 3. Luồng Làm Việc Tiêu Chuẩn Đề Nghị

Để tiết kiệm thời gian nhất, hãy thao tác theo thứ tự sau khi ra đề:

1. Thêm cấu hình bài vào `problem.json` và khai báo nhóm bài vào `contest.json`.
2. Mở `polygon.py`, chọn `COMMAND = "pipeline"`, điền `CONTEST_NAME_TO_SYNC` và bật toàn bộ `PIPELINE_FLAGS = True`.
3. Chạy `python polygon.py`. Uống một tách cà phê chờ hệ thống đẩy code lên và chờ tải ZIP về.
4. Chọn `COMMAND = "automate-mashup"`, điền tên vào `MASHUP_NAME` và `MASHUP_CONTEST_REF`, sau đó chạy script để tool tự động lên Polygon lấy quyền, sau đó sang Codeforces tạo Contest.
5. Lấy link Gym vừa tạo chia sẻ cho thí sinh làm bài! Mọi logs và thao tác sẽ được lưu lại trong `automation_report.md`.
