from polygon import PROBLEM_JSON_PATH, CONTEST_JSON_PATH, CONTESTS_OUTPUT_DIR
import os
import zipfile
import shutil
import time
import json
import random
import string
import hashlib
import requests

POLYGON_API_URL = "https://polygon.codeforces.com/api"

def load_env():
    """Loads environment variables from .env file securely."""
    env_vars = {}
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip()
    return env_vars

ENV = load_env()
API_KEY = ENV.get("POLYGON_API_KEY", "")
API_SECRET = ENV.get("POLYGON_API_SECRET", "")

def _generate_api_sig(method_name, params, secret):
    """Generates the SHA-512 apiSig required by Polygon API."""
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    
    # Sort parameters
    sorted_params = sorted(params.items())
    
    # Construct the string to hash
    query_string = "&".join(f"{k}={v}" for k, v in sorted_params)
    str_to_hash = f"{rand}/{method_name}?{query_string}#{secret}"
    
    hash_obj = hashlib.sha512(str_to_hash.encode('utf-8'))
    return f"{rand}{hash_obj.hexdigest()}"

def _api_request(method_name, **kwargs):
    """
    Executes an API request to Polygon.
    Implements exponential backoff for 429/Busy errors.
    """
    if not API_KEY or not API_SECRET:
        raise ValueError("API Key or Secret is missing in .env")

    params = {
        "apiKey": API_KEY,
        "time": str(int(time.time()))
    }
    
    # Add kwargs to params
    for k, v in kwargs.items():
        if v is not None:
            # Convert booleans to "true"/"false"
            if isinstance(v, bool):
                params[k] = "true" if v else "false"
            else:
                params[k] = str(v)

    api_sig = _generate_api_sig(method_name, params, API_SECRET)
    params["apiSig"] = api_sig

    url = f"{POLYGON_API_URL}/{method_name}"
    
    max_retries = 5
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, data=params)
            
            # Rate limit or server error
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.exceptions.RequestException(f"HTTP {response.status_code}")
                
            # Parse JSON (except for some endpoints that return plain text/binary)
            # We will handle problem.package, problem.script, etc., later if needed,
            # but usually these return bytes. Wait, problem.package returns binary zip.
            if method_name in ["problem.package", "problem.testInput", "problem.testAnswer"]:
                if response.status_code == 200:
                    return response.content
                else:
                    raise Exception(f"Failed to download: {response.text}")
                    
            try:
                res_json = response.json()
            except ValueError:
                return response.text
                
            if res_json.get("status") == "OK":
                return res_json.get("result", True)
            else:
                raise Exception(f"Polygon API Error ({method_name}): {res_json.get('comment')}")
                
        except (requests.exceptions.RequestException, Exception) as e:
            # Do not retry on definite API logic errors
            if "Polygon API Error" in str(e):
                raise e
                
            if attempt == max_retries - 1:
                raise Exception(f"API Request Failed after {max_retries} attempts: {e}")
            
            time.sleep(base_delay * (2 ** attempt))

# ==========================================
# Direct API Endpoint Wrappers
# ==========================================

def problems_list():
    return _api_request("problems.list")

def problem_create(name):
    return _api_request("problem.create", name=name)

def problem_update_info(problem_id, **kwargs):
    return _api_request("problem.updateInfo", problemId=problem_id, **kwargs)

def problem_save_statement(problem_id, lang="english", **kwargs):
    return _api_request("problem.saveStatement", problemId=problem_id, lang=lang, **kwargs)

def problem_set_checker(problem_id, checker):
    return _api_request("problem.setChecker", problemId=problem_id, checker=checker)

def problem_save_file(problem_id, file_type, name, file_content, **kwargs):
    return _api_request("problem.saveFile", problemId=problem_id, type=file_type, name=name, file=file_content, **kwargs)

def problem_save_solution(problem_id, name, file_content, tag=None, **kwargs):
    return _api_request("problem.saveSolution", problemId=problem_id, name=name, file=file_content, tag=tag, **kwargs)

def problem_save_script(problem_id, testset, source):
    return _api_request("problem.saveScript", problemId=problem_id, testset=testset, source=source)

def problem_build_package(problem_id, full=False, verify=False):
    return _api_request("problem.buildPackage", problemId=problem_id, full=full, verify=verify)

def problem_packages(problem_id):
    return _api_request("problem.packages", problemId=problem_id)

def problem_package(problem_id, package_id, type_str="standard"):
    return _api_request("problem.package", problemId=problem_id, packageId=package_id, type=type_str)

def problem_commit_changes(problem_id, message=""):
    return _api_request("problem.commitChanges", problemId=problem_id, message=message)


import zipfile
import shutil

def get_problems():
    path = PROBLEM_JSON_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    problems = data.get("problems", [])
    for p in problems:
        if "local_id" not in p:
            raise ValueError("Missing local_id in problem.json")
        if "settings" not in p or "total_points" not in p["settings"]:
            raise ValueError(f"Missing total_points in settings for {p.get('local_id')}")
    return problems

def get_problem(local_id):
    for p in get_problems():
        if p["local_id"] == local_id:
            return p
    raise ValueError(f"Problem {local_id} not found in problem.json")

def add_problem(local_id, name):
    path = PROBLEM_JSON_PATH
    data = {"problems": []}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
    for p in data.get("problems", []):
        if p.get("local_id") == local_id:
            raise ValueError(f"Problem {local_id} already exists")
            
    new_prob = {
      "local_id": local_id,
      "polygon_id": None,
      "name": name,
      "paths": {
        "generator": f"problems/{local_id}/generator.cpp",
        "statement": f"problems/{local_id}/statement.tex",
        "solutions": [
          {
            "path": f"problems/{local_id}/main.cpp",
            "tag": "MA"
          }
        ]
      },
      "settings": {
        "time_limit": 1000,
        "memory_limit": 256,
        "checker": "std::lcmp.cpp",
        "compiler": "cpp.gcc14-64-msys2-g++23",
        "total_points": 100,
        "points_policy": "EACH_TEST"
      },
      "test_config": {
        "total_tests": 20,
        "number_of_samples": 0,
        "subtasks": []
      },
      "pipeline_status": {
        "BUILD": "NOT_READY"
      },
      "last_synced_hash": {}
    }
    data.setdefault("problems", []).append(new_prob)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _update_polygon_id(local_id, polygon_id):
    path = PROBLEM_JSON_PATH
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for p in data.get("problems", []):
        if p.get("local_id") == local_id:
            p["polygon_id"] = polygon_id
            break
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def execute_pipeline(local_id, init=False, resources=False, solutions=False, tests=False, build=False):
    problem = get_problem(local_id)
    polygon_id = problem.get("polygon_id")
    
    report_lines = [f"## Execution Report for {local_id} at {time.ctime()}"]
    
    if init:
        if not polygon_id:
            res = problem_create(problem["name"])
            polygon_id = res.get("id")
            _update_polygon_id(local_id, polygon_id)
            problem["polygon_id"] = polygon_id
            report_lines.append(f"- [Init] Created problem on Polygon with ID {polygon_id}")
            
        settings = problem["settings"]
        problem_update_info(polygon_id, timeLimit=settings["time_limit"], memoryLimit=settings["memory_limit"])
        report_lines.append("- [Init] Updated problem info (timeLimit, memoryLimit)")
        problem_commit_changes(polygon_id, message="Init problem metadata")
        
    if not polygon_id:
        raise ValueError("Cannot proceed without polygon_id. Run init first.")
        
    if resources:
        paths = problem["paths"]
        
        # Checker
        checker_name = problem["settings"]["checker"]
        if checker_name and not checker_name.startswith('std::'):
            checker_path = os.path.join('problems', local_id, checker_name)
            if os.path.exists(checker_path):
                with open(checker_path, "r", encoding="utf-8") as f:
                    problem_save_file(polygon_id, "source", checker_name, f.read())
        problem_set_checker(polygon_id, checker_name)
        
        # Generator
        gen_path = paths.get("generator")
        if gen_path and os.path.exists(gen_path):
            with open(gen_path, "r", encoding="utf-8") as f:
                problem_save_file(polygon_id, "source", os.path.basename(gen_path), f.read())
                
        # Statement
        stmt_path = paths.get("statement")
        if stmt_path and os.path.exists(stmt_path):
            with open(stmt_path, "r", encoding="utf-8") as f:
                problem_save_statement(polygon_id, lang="english", name=problem["name"], legend=f.read())
                
        report_lines.append("- [Resources] Uploaded statement, generator, and checker")
        problem_commit_changes(polygon_id, message="Uploaded resources")

    if solutions:
        paths = problem["paths"]
        for sol in paths.get("solutions", []):
            sol_path = sol.get("path")
            if sol_path and os.path.exists(sol_path):
                with open(sol_path, "r", encoding="utf-8") as f:
                    problem_save_solution(polygon_id, os.path.basename(sol_path), f.read(), tag=sol.get("tag"))
        report_lines.append("- [Solutions] Uploaded solutions")
        problem_commit_changes(polygon_id, message="Uploaded solutions")

    if tests:
        script_lines = []
        current_test = 1
        gen_path = problem["paths"].get("generator", "")
        gen_name = os.path.splitext(os.path.basename(gen_path))[0] if gen_path else "generator"
        
        test_config = problem["test_config"]
        for subtask in test_config.get("subtasks", []):
            num_tests = int(subtask["proportion"] * test_config["total_tests"])
            for _ in range(num_tests):
                args = f" {subtask['args']}" if subtask.get('args') else ""
                script_lines.append(f"{gen_name} {current_test} {subtask['id']}{args} > {current_test}")
                current_test += 1
                
        script_content = "\\n".join(script_lines)
        
        script_path = os.path.join("problems", local_id, "script.txt")
        os.makedirs(os.path.dirname(script_path), exist_ok=True)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
            
        problem_save_script(polygon_id, "tests", script_content)
        report_lines.append("- [Tests] Generated and uploaded script.txt")
        problem_commit_changes(polygon_id, message="Uploaded test script")

    if build:
        try:
            problem_build_package(polygon_id, full=True, verify=True)
            report_lines.append(f"- [Build] Triggered package build successfully")
        except Exception as e:
            if 'already being built' not in str(e) and 'already non-failed' not in str(e):
                raise e
            else:
                report_lines.append(f"- [Build] Package build already triggered or completed")

    with open("automation_report.md", "a", encoding="utf-8") as f:
        f.write("\\n".join(report_lines) + "\\n\\n")

def download_package(local_id):
    problem = get_problem(local_id)
    polygon_id = problem.get("polygon_id")
    if not polygon_id:
        raise ValueError(f"Cannot download {local_id}: no polygon_id")
        
    print(f"Waiting for package of {local_id} to be READY...")
    while True:
        packages = problem_packages(polygon_id)
        if packages:
            packages.sort(key=lambda x: x['id'], reverse=True)
            latest = packages[0]
            if latest['state'] == 'READY':
                break
            elif latest['state'] == 'FAILED':
                raise Exception(f"Package build failed for {local_id}: {latest.get('comment')}")
        time.sleep(15)
        
    zip_data = problem_package(polygon_id, latest['id'])
    os.makedirs('downloads', exist_ok=True)
    zip_path = os.path.join('downloads', f"{local_id}.zip")
    with open(zip_path, 'wb') as f:
        f.write(zip_data)
        
    with open("automation_report.md", "a", encoding="utf-8") as f:
        f.write(f"## Download Report for {local_id} at {time.ctime()}\\n")
        f.write(f"- [Download] Downloaded package to {zip_path}\\n\\n")

def create_contest(contest_name):
    path = CONTEST_JSON_PATH
    if not os.path.exists(path):
        raise FileNotFoundError("contest.json not found")
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    contest = next((c for c in data.get("contests", []) if c["name"] == contest_name), None)
    if not contest:
        raise ValueError(f"Contest {contest_name} not found")
        
    slugs = contest.get("slugs", [])
    os.makedirs("contests", exist_ok=True)
    
    temp_dir = os.path.join("contests", f"temp_{contest_name}")
    os.makedirs(temp_dir, exist_ok=True)
    
    for slug in slugs:
        src = os.path.join("downloads", f"{slug}.zip")
        if not os.path.exists(src):
            print(f"Warning: Package for {slug} not found in downloads/")
            continue
        shutil.copy2(src, os.path.join(temp_dir, f"{slug}.zip"))
        
    zip_path = os.path.join("contests", f"{contest_name}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
                
    shutil.rmtree(temp_dir)
    contest["zip_path"] = zip_path.replace("\\", "/")
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Contest {contest_name} packaged to {zip_path}")
