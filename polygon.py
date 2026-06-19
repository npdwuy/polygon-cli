# ==========================================
# CẤU HÌNH CHẠY SCRIPT
# ==========================================
COMMAND = "pipeline"

# 0. Cấu hình BÀI TẬP MỤC TIÊU (Dùng chung cho pipeline và automate-mashup)
TARGET_SLUGS = [
  "math-pascal-combination",
  "math-candy-distribution",
  "math-catalan-number",
  "math-divisible-inclusion",
  "math-colored-segments",
  "math-balanced-teams",
  "math-alice-gift-list",
  "math-median-subarrays",
  "math-median-subsets",
  "math-sliding-window-and-zero"
]
 # Danh sách slug cụ thể. Để rỗng [] nếu dùng CONTEST_NAME_TO_SYNC

CONTEST_NAME_TO_SYNC = ""  # Nếu có tên, sẽ chạy các problem của contest đó trong contest.json

# 1. Cấu hình cho lệnh 'pipeline'
PIPELINE_FLAGS = {
    "init": False,
    "resources": False,
    "solutions": False,
    "tests": False,
    "build": False,
    "download": False,
    "grant_access": False,
    "automate_mashup": True
}

# 2. Cấu hình cho lệnh 'automate-mashup'
MASHUP_NAME = ""        # Tên Mashup muốn tạo mới trên Codeforces. Nếu rỗng, sẽ không tạo mới.
MASHUP_GYM_ID = "697277"      # ID của Gym nếu đã có (Dùng khi MASHUP_NAME rỗng).
MASHUP_CONTEST_REF = "TSBS" # Tên contest trong contest.json để lưu lại Gym ID sau khi tạo (Tùy chọn)

# 3. Cấu hình cho lệnh 'package-contest'
PACKAGE_CONTEST_NAME = ""  # Nếu rỗng thì không trigger việc đóng gói contest

# 4. Cấu hình cho lệnh 'grant-access' (Mặc định tự động chạy khi dùng lệnh 'automate-mashup')
GRANT_USERS = {
    "codeforces": "Read" # Quyền có thể là "Read" hoặc "Write"
}


# ==========================================
# HẰNG SỐ ĐƯỜNG DẪN HỆ THỐNG
# ==========================================
PROBLEM_JSON_PATH = "problem.json"
CONTEST_JSON_PATH = "contest.json"
CONTESTS_OUTPUT_DIR = "contests"


if __name__ == '__main__':
    from Tools.Pipeline import main
    main()
