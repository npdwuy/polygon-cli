# ==========================================
# CẤU HÌNH CHẠY SCRIPT
# ==========================================
# COMMAND = "pipeline"
COMMAND = "grant-access"
# COMMAND = "automate-mashup"
# COMMAND = "package-contest"

# 0. Cấu hình BÀI TẬP MỤC TIÊU (Dùng chung cho pipeline và automate-mashup)
TARGET_SLUGS = [
    "all-pairs-shortest-path", "ancestor-descendant", "bai-toan-rot-nuoc", "basic-dijkstra", 
    "boiso", "co-so-doi-xung", "comdiv", "connected-components", "dem-chu-so-khong", 
    "dem-so-nguyen-to", "dem-uoc-giai-thua", "divsub", "dondep", "island-counting", 
    "kfusion", "khoang-cach-nguyen-to", "khoi-phuc-cap-so", "luy-thua-modulo", "mult2019", 
    "ndel", "network-path", "phan-tich-thua-so", "postal-knight", "powmod", "qlnv", 
    "rect", "sibling-check", "simple-cycle", "sort", "spanning-tree", "sqrnum", "square-maze", 
    "subtree-size-height", "terrain-path", "tim-gcd-lon-nhat", "tinh-to-hop-chap", 
    "tong-cap-so-nhan", "tong-so-luong-uoc", "tong-uoc-nho-nhat", "tong-uoc-theo-modulo", 
    "traffic-toll", "tree-diameter", "xauhople"
]  # Danh sách slug cụ thể. Để rỗng [] nếu dùng CONTEST_NAME_TO_SYNC

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
AUTOMATION_REPORT_PATH = "automation_report.md"
CONTESTS_OUTPUT_DIR = "contests"


if __name__ == '__main__':
    from Tools.Pipeline import main
    main()
