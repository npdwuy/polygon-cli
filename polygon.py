import sys
import json
import traceback
import os

from Tools.Method import execute_pipeline, get_problems, create_contest, download_package
from Tools.Browser import automate_mashup

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


def _update_contest_gym_id(contest_name, gym_id):
    path = "contest.json"
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    updated = False
    for c in data.get("contests", []):
        if c.get("name") == contest_name:
            c["gym_id"] = gym_id
            updated = True
            break
            
    if updated:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Updated contest.json: Saved Gym ID {gym_id} to contest '{contest_name}'.")

def _get_targets():
    targets = []
    if CONTEST_NAME_TO_SYNC:
        try:
            with open("contest.json", "r", encoding="utf-8") as f:
                cdata = json.load(f)
            contest = next((c for c in cdata.get("contests", []) if c["name"] == CONTEST_NAME_TO_SYNC), None)
            if not contest:
                print(f"Contest '{CONTEST_NAME_TO_SYNC}' not found in contest.json.")
                sys.exit(1)
            targets = contest.get("slugs", [])
        except Exception as e:
            print(f"Error reading contest: {e}")
            sys.exit(1)
    else:
        targets = TARGET_SLUGS

    if not targets:
        print("No target slugs specified. Provide TARGET_SLUGS or CONTEST_NAME_TO_SYNC.")
        sys.exit(1)
    return targets

def main():
    if COMMAND == "pipeline":
        targets = _get_targets()
        print(f"Starting pipeline for {len(targets)} problems: {', '.join(targets)}")
        
        for slug in targets:
            print(f"\\n=================== Syncing: {slug} ===================")
            try:
                execute_pipeline(
                    slug,
                    init=PIPELINE_FLAGS["init"],
                    resources=PIPELINE_FLAGS["resources"],
                    solutions=PIPELINE_FLAGS["solutions"],
                    tests=PIPELINE_FLAGS["tests"],
                    build=PIPELINE_FLAGS["build"]
                )
                print(f"[SUCCESS] Finished pipeline for {slug}")
            except Exception as e:
                print(f"\\n[ERROR] Pipeline failed for {slug}: {e}")
                traceback.print_exc()
                
                ans = input("Do you want to continue with the next problem? (y/n): ")
                if ans.lower() != 'y':
                    print("Aborting.")
                    sys.exit(1)
                    
        if PIPELINE_FLAGS.get("download"):
            print("\\n=================== Downloading Packages ===================")
            for slug in targets:
                print(f"\\n=================== Downloading: {slug} ===================")
                try:
                    download_package(slug)
                    print(f"[SUCCESS] Downloaded {slug}")
                except Exception as e:
                    print(f"\\n[ERROR] Download failed for {slug}: {e}")
                    traceback.print_exc()

    elif COMMAND == "automate-mashup":
        targets = _get_targets()
        if not MASHUP_NAME and not MASHUP_GYM_ID:
            print("Skipping mashup creation (MASHUP_NAME and MASHUP_GYM_ID are both empty).")
            return
            
        print("Starting Codeforces Mashup Automation...")
        try:
            new_gym_id = automate_mashup(slugs=targets, gym_id=MASHUP_GYM_ID if MASHUP_GYM_ID else None, mashup_name=MASHUP_NAME, grant_access=GRANT_CODEFORCES_ACCESS)
            print("Mashup automation finished.")
            
            if new_gym_id and MASHUP_CONTEST_REF:
                _update_contest_gym_id(MASHUP_CONTEST_REF, new_gym_id)
                
        except Exception as e:
            print(f"Automation failed: {e}")
            traceback.print_exc()

    elif COMMAND == "package-contest":
        if not PACKAGE_CONTEST_NAME:
            print("Skipping package-contest (PACKAGE_CONTEST_NAME is empty).")
            return
            
        try:
            create_contest(PACKAGE_CONTEST_NAME)
        except Exception as e:
            print(f"Failed to package contest: {e}")
            
    else:
        print(f"Unknown command: {COMMAND}")

if __name__ == "__main__":
    main()
