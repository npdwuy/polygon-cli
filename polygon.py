# ==========================================
# CẤU HÌNH CHẠY SCRIPT
# ==========================================
COMMAND = ""  # Các lệnh: "pipeline", "automate-mashup", "package-contest"

# 0. Cấu hình BÀI TẬP MỤC TIÊU (Dùng chung cho pipeline và automate-mashup)
TARGET_SLUGS = [""]  # Danh sách slug cụ thể. Để rỗng [] nếu dùng CONTEST_NAME_TO_SYNC
CONTEST_NAME_TO_SYNC = ""  # Nếu có tên, sẽ chạy các problem của contest đó trong contest.json

# 1. Cấu hình cho lệnh 'pipeline'
PIPELINE_FLAGS = {
    "init": True,
    "resources": True,
    "solutions": True,
    "tests": True,
    "build": True,
    "download": True
}

# 2. Cấu hình cho lệnh 'automate-mashup'
MASHUP_NAME = ""        # Tên Mashup muốn tạo mới trên Codeforces. Nếu rỗng, sẽ không tạo mới.
MASHUP_GYM_ID = ""      # ID của Gym nếu đã có (Dùng khi MASHUP_NAME rỗng).
MASHUP_CONTEST_REF = "" # Tên contest trong contest.json để lưu lại Gym ID sau khi tạo (Tùy chọn)
GRANT_CODEFORCES_ACCESS = False # Bật/tắt việc cấp quyền cho user codeforces trên Polygon

# 3. Cấu hình cho lệnh 'package-contest'
PACKAGE_CONTEST_NAME = ""  # Nếu rỗng thì không trigger việc đóng gói contest


# ==========================================
# HẰNG SỐ ĐƯỜNG DẪN HỆ THỐNG
# ==========================================
PROBLEM_JSON_PATH = "problem.json"
CONTEST_JSON_PATH = "contest.json"
AUTOMATION_REPORT_PATH = "automation_report.md"
CONTESTS_OUTPUT_DIR = "contests"


if __name__ == '__main__':
    from Tools.Pipeline import main
    main()
